import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.db.session import AsyncSessionLocal, engine
from app.models.db import Base, Contract, ContractStatus, Dispute, DisputeStatus


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        code_contract = Contract(
            title="AI Code Review Escrow",
            description="Seller will deliver a secure FastAPI endpoint and tests for an agent wallet webhook.",
            buyer_address="agent-buyer-code",
            seller_address="agent-dev-0x42",
            success_criteria=["Endpoint validates signed webhook payloads", "Unit tests cover valid and invalid signatures", "README documents local run"],
            subjective_clauses=["Code should be maintainable and production-minded"],
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
            amount_usdc=Decimal("250.00"),
            status=ContractStatus.disputed,
            circle_payment_id="seed-pay-code",
            circle_escrow_wallet_id="seed-wallet-code",
            chain_escrow_id="seed-chain-code",
        )
        art_contract = Contract(
            title="Creative Poster Escrow",
            description="Seller will create a cyberpunk conference poster with editable source files and two revision passes.",
            buyer_address="agent-buyer-creative",
            seller_address="artist-wallet-demo",
            success_criteria=["Final PNG delivered at 4K", "Editable source file included", "Two revision passes completed"],
            subjective_clauses=["Visual direction should feel premium, legible, and not stock-like"],
            deadline=datetime.now(timezone.utc) + timedelta(days=5),
            amount_usdc=Decimal("180.00"),
            status=ContractStatus.disputed,
            circle_payment_id="seed-pay-creative",
            circle_escrow_wallet_id="seed-wallet-creative",
            chain_escrow_id="seed-chain-creative",
        )
        db.add_all([code_contract, art_contract])
        await db.flush()
        db.add_all(
            [
                Dispute(
                    contract_id=code_contract.id,
                    raised_by="agent-buyer-code",
                    claim="The endpoint was delivered and merged, but the invalid signature test is missing. Request a partial release until tests are complete.",
                    requested_outcome="partial_release",
                    evidence=[{"filename": "pull-request.txt", "url": "/examples/code-pr.txt", "sha256": "seed", "size_bytes": 128}],
                    status=DisputeStatus.raised,
                ),
                Dispute(
                    contract_id=art_contract.id,
                    raised_by="artist-wallet-demo",
                    claim="All poster files were delivered before the deadline and the buyer approved the second revision in chat. Request full release.",
                    requested_outcome="full_release",
                    evidence=[{"filename": "revision-approval.png", "url": "/examples/revision-approval.png", "sha256": "seed", "size_bytes": 256}],
                    status=DisputeStatus.raised,
                ),
            ]
        )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
