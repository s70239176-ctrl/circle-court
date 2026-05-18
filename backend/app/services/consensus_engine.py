import asyncio
import json
from collections import Counter
from decimal import Decimal
from typing import Any

from litellm import acompletion
from pydantic import ValidationError

from app.core.config import get_settings
from app.models.db import Contract, Dispute, VerdictKind
from app.models.schemas import ConsensusResult, JuryVote
from app.services.embeddings import EmbeddingService


SYSTEM_PROMPT = """You are a careful decentralized escrow juror.
Return only JSON with keys verdict, release_to_seller_pct, confidence, rationale.
verdict must be one of full_release, partial_release, refund, needs_more_evidence.
Judge the contract criteria, subjective clauses, deadline, dispute claim, and evidence.
Be concise, impartial, and favor needs_more_evidence when the proof is materially incomplete."""


class ConsensusEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.embeddings = EmbeddingService()

    async def deliberate(self, contract: Contract, dispute: Dispute, appeal: bool = False) -> ConsensusResult:
        leader_model = self.settings.llm_model_leader
        validators = self._panel(appeal=appeal)
        prompt = self._build_prompt(contract, dispute, appeal=appeal)

        leader = await self._ask_model(leader_model, prompt, role="leader")
        validator_votes = await asyncio.gather(
            *(self._ask_model(model, prompt, role="validator", leader_hint=leader) for model in validators)
        )
        all_votes = [leader, *validator_votes]
        semantic = await self.embeddings.semantic_matrix([vote.rationale for vote in all_votes])
        result = self._aggregate(leader, validator_votes, semantic)
        return result

    def _panel(self, appeal: bool) -> list[str]:
        base = self.settings.validator_model_list
        if appeal:
            expanded = base + ["gpt-4o", "claude-3-5-haiku-20241022", "ollama/llama3.1"]
            return expanded[:9]
        return (base * 3)[:5]

    def _build_prompt(self, contract: Contract, dispute: Dispute, appeal: bool) -> str:
        return json.dumps(
            {
                "appeal": appeal,
                "contract": {
                    "title": contract.title,
                    "description": contract.description,
                    "success_criteria": contract.success_criteria,
                    "subjective_clauses": contract.subjective_clauses,
                    "deadline": contract.deadline.isoformat(),
                    "amount_usdc": str(contract.amount_usdc),
                    "buyer_address": contract.buyer_address,
                    "seller_address": contract.seller_address,
                },
                "dispute": {
                    "claim": dispute.claim,
                    "requested_outcome": dispute.requested_outcome,
                    "raised_by": dispute.raised_by,
                    "evidence": dispute.evidence,
                    "appeal_count": dispute.appeal_count,
                },
            },
            indent=2,
        )

    async def _ask_model(self, model: str, prompt: str, role: str, leader_hint: JuryVote | None = None) -> JuryVote:
        hint = f"\nLeader provisional verdict: {leader_hint.model_dump_json()}" if leader_hint else ""
        try:
            response = await acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt + hint},
                ],
                temperature=0.2 if role == "leader" else 0.35,
                timeout=45,
            )
            raw = response.choices[0].message.content
            payload = json.loads(raw)
            return self._vote_from_payload(model, role, payload)
        except Exception:
            return self._deterministic_fallback(model, role, prompt)

    def _vote_from_payload(self, model: str, role: str, payload: dict[str, Any]) -> JuryVote:
        try:
            return JuryVote(
                model=model,
                role=role,
                verdict=VerdictKind(payload["verdict"]),
                release_to_seller_pct=Decimal(str(payload["release_to_seller_pct"])),
                confidence=Decimal(str(payload["confidence"])),
                rationale=str(payload["rationale"])[:4000],
            )
        except (KeyError, ValidationError, ValueError):
            return JuryVote(
                model=model,
                role=role,
                verdict=VerdictKind.needs_more_evidence,
                release_to_seller_pct=Decimal("0"),
                confidence=Decimal("0.4"),
                rationale="The model returned malformed output, so this juror abstains toward more evidence.",
            )

    def _deterministic_fallback(self, model: str, role: str, prompt: str) -> JuryVote:
        text = prompt.lower()
        positive = sum(word in text for word in ["delivered", "accepted", "complete", "approved", "merged"])
        negative = sum(word in text for word in ["missing", "late", "plagiarized", "broken", "failed", "refund"])
        if positive > negative:
            verdict, pct, confidence = VerdictKind.full_release, Decimal("100"), Decimal("0.66")
        elif negative > positive:
            verdict, pct, confidence = VerdictKind.refund, Decimal("0"), Decimal("0.64")
        else:
            verdict, pct, confidence = VerdictKind.partial_release, Decimal("50"), Decimal("0.55")
        return JuryVote(
            model=f"{model}:fallback",
            role=role,  # type: ignore[arg-type]
            verdict=verdict,
            release_to_seller_pct=pct,
            confidence=confidence,
            rationale="Fallback juror used deterministic contract/evidence keyword scoring because live LLM credentials were unavailable.",
        )

    def _aggregate(self, leader: JuryVote, validators: list[JuryVote], semantic: dict[str, Any]) -> ConsensusResult:
        votes = [leader, *validators]
        weighted: Counter[VerdictKind] = Counter()
        for vote in votes:
            weight = float(vote.confidence) * (1.2 if vote.role == "leader" else 1.0)
            weighted[vote.verdict] += weight
        winner = weighted.most_common(1)[0][0]
        winning_votes = [vote for vote in votes if vote.verdict == winner]
        release_pct = sum(vote.release_to_seller_pct for vote in winning_votes) / Decimal(len(winning_votes))
        confidence = min(
            Decimal("0.99"),
            (sum(vote.confidence for vote in winning_votes) / Decimal(len(winning_votes)))
            * Decimal(str(max(semantic.get("average_pairwise_similarity", 0.75), 0.5))),
        )
        rationale = self._compose_rationale(winner, winning_votes, semantic)
        return ConsensusResult(
            kind=winner,
            release_to_seller_pct=release_pct.quantize(Decimal("0.01")),
            confidence=confidence.quantize(Decimal("0.0001")),
            rationale=rationale,
            leader=leader,
            validators=validators,
            semantic_agreement=semantic | {"weighted_votes": {key.value: value for key, value in weighted.items()}},
        )

    def _compose_rationale(self, winner: VerdictKind, votes: list[JuryVote], semantic: dict[str, Any]) -> str:
        reasons = " ".join(vote.rationale for vote in votes[:3])
        return (
            f"Optimistic Democracy reached {winner.value} with {len(votes)} aligned jurors. "
            f"Average semantic agreement was {semantic.get('average_pairwise_similarity')}. {reasons}"
        )[:4000]
