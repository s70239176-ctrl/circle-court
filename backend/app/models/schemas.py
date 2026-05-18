from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.db import ContractStatus, DisputeStatus, VerdictKind


class EvidenceItem(BaseModel):
    filename: str
    content_type: str | None = None
    url: str
    sha256: str
    size_bytes: int


class ContractCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=20)
    buyer_address: str = Field(min_length=4)
    seller_address: str = Field(min_length=4)
    arbiter_agent: str | None = None
    success_criteria: list[str] = Field(min_length=1)
    subjective_clauses: list[str] = Field(default_factory=list)
    deadline: datetime
    amount_usdc: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("success_criteria", "subjective_clauses")
    @classmethod
    def trim_list(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


class ContractRead(BaseModel):
    id: str
    title: str
    description: str
    buyer_address: str
    seller_address: str
    arbiter_agent: str | None
    success_criteria: list[str]
    subjective_clauses: list[str]
    deadline: datetime
    amount_usdc: Decimal
    status: ContractStatus
    circle_payment_id: str | None
    circle_escrow_wallet_id: str | None
    chain_escrow_id: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DisputeCreate(BaseModel):
    contract_id: str
    raised_by: str = Field(min_length=3)
    claim: str = Field(min_length=20)
    requested_outcome: Literal["full_release", "partial_release", "refund", "needs_more_evidence"]
    evidence: list[EvidenceItem] = Field(default_factory=list)


class DisputeRead(BaseModel):
    id: str
    contract_id: str
    raised_by: str
    claim: str
    requested_outcome: str
    evidence: list[dict[str, Any]]
    status: DisputeStatus
    appeal_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JuryVote(BaseModel):
    model: str
    role: Literal["leader", "validator"]
    verdict: VerdictKind
    release_to_seller_pct: Decimal = Field(ge=0, le=100)
    confidence: Decimal = Field(ge=0, le=1)
    rationale: str
    embedding_label: str | None = None


class ConsensusResult(BaseModel):
    kind: VerdictKind
    release_to_seller_pct: Decimal = Field(ge=0, le=100)
    confidence: Decimal = Field(ge=0, le=1)
    rationale: str
    leader: JuryVote
    validators: list[JuryVote]
    semantic_agreement: dict[str, Any]


class VerdictRead(BaseModel):
    id: str
    dispute_id: str
    kind: VerdictKind
    release_to_seller_pct: Decimal
    confidence: Decimal
    rationale: str
    leader: dict[str, Any]
    validators: list[dict[str, Any]]
    semantic_agreement: dict[str, Any]
    payout_tx_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentCommand(BaseModel):
    actor: str = "agent"
    command: str = Field(min_length=3)
    dry_run: bool = False


class AgentCommandResult(BaseModel):
    action: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class HealthRead(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
