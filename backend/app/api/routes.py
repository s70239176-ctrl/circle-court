import hashlib
import os
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import ApiKeyDependency
from app.db.session import get_db
from app.models.db import Contract, ContractStatus, Dispute, DisputeStatus, Verdict
from app.models.schemas import (
    AgentCommand,
    AgentCommandResult,
    ContractCreate,
    ContractRead,
    DisputeCreate,
    DisputeRead,
    EvidenceItem,
    HealthRead,
    VerdictRead,
)
from app.services.audit import log_audit
from app.services.blockchain import EscrowChainClient
from app.services.circle import CircleClient
from app.services.consensus_engine import ConsensusEngine

router = APIRouter()


@router.get("/health", response_model=HealthRead)
async def health() -> HealthRead:
    settings = get_settings()
    return HealthRead(status="ok", service=settings.app_name, environment=settings.environment)


@router.post("/contracts", response_model=ContractRead, dependencies=[ApiKeyDependency])
async def create_contract(payload: ContractCreate, db: AsyncSession = Depends(get_db)) -> Contract:
    circle = CircleClient()
    chain = EscrowChainClient()
    contract = Contract(
        **payload.model_dump(),
        status=ContractStatus.funded,
    )
    db.add(contract)
    await db.flush()
    escrow = await circle.create_escrow(
        amount_usdc=payload.amount_usdc,
        contract_id=contract.id,
        buyer_address=payload.buyer_address,
    )
    chain_receipt = await chain.register_escrow(
        contract_id=contract.id,
        buyer=contract.buyer_address,
        seller=contract.seller_address,
        amount_usdc=contract.amount_usdc,
    )
    contract.circle_payment_id = escrow.get("payment_id")
    contract.circle_escrow_wallet_id = escrow.get("escrow_wallet_id")
    contract.chain_escrow_id = chain_receipt.get("chain_escrow_id")
    contract.metadata_json = contract.metadata_json | {"escrow": escrow, "chain": chain_receipt}
    await log_audit(db, actor=payload.buyer_address, action="contract.create", subject_type="contract", subject_id=contract.id, payload=payload.model_dump(mode="json"))
    await db.commit()
    await db.refresh(contract)
    return contract


@router.get("/contracts", response_model=list[ContractRead], dependencies=[ApiKeyDependency])
async def list_contracts(db: AsyncSession = Depends(get_db)) -> list[Contract]:
    result = await db.execute(select(Contract).order_by(desc(Contract.created_at)))
    return list(result.scalars().all())


@router.get("/contracts/{contract_id}", response_model=ContractRead, dependencies=[ApiKeyDependency])
async def get_contract(contract_id: str, db: AsyncSession = Depends(get_db)) -> Contract:
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.post("/evidence/upload", response_model=EvidenceItem, dependencies=[ApiKeyDependency])
async def upload_evidence(file: UploadFile = File(...)) -> EvidenceItem:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    contents = await file.read()
    digest = hashlib.sha256(contents).hexdigest()
    safe_name = f"{digest[:16]}-{Path(file.filename or 'evidence.bin').name}"
    target = upload_dir / safe_name
    target.write_bytes(contents)
    return EvidenceItem(
        filename=file.filename or safe_name,
        content_type=file.content_type,
        url=f"/uploads/{safe_name}",
        sha256=digest,
        size_bytes=len(contents),
    )


@router.post("/disputes", response_model=DisputeRead, dependencies=[ApiKeyDependency])
async def create_dispute(payload: DisputeCreate, db: AsyncSession = Depends(get_db)) -> Dispute:
    contract = await db.get(Contract, payload.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    dispute = Dispute(**payload.model_dump(mode="json"), status=DisputeStatus.raised)
    contract.status = ContractStatus.disputed
    db.add(dispute)
    await log_audit(db, actor=payload.raised_by, action="dispute.raise", subject_type="dispute", subject_id=dispute.id, payload=payload.model_dump(mode="json"))
    await db.commit()
    await db.refresh(dispute)
    return dispute


@router.get("/disputes", response_model=list[DisputeRead], dependencies=[ApiKeyDependency])
async def list_disputes(db: AsyncSession = Depends(get_db)) -> list[Dispute]:
    result = await db.execute(select(Dispute).order_by(desc(Dispute.created_at)))
    return list(result.scalars().all())


@router.get("/disputes/{dispute_id}", response_model=DisputeRead, dependencies=[ApiKeyDependency])
async def get_dispute(dispute_id: str, db: AsyncSession = Depends(get_db)) -> Dispute:
    dispute = await db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute


@router.post("/disputes/{dispute_id}/deliberate", response_model=VerdictRead, dependencies=[ApiKeyDependency])
async def deliberate(dispute_id: str, db: AsyncSession = Depends(get_db)) -> Verdict:
    dispute = await db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    contract = await db.get(Contract, dispute.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    dispute.status = DisputeStatus.deliberating
    result = await ConsensusEngine().deliberate(contract, dispute, appeal=dispute.appeal_count > 0)
    payout = await CircleClient().release(
        escrow_wallet_id=contract.circle_escrow_wallet_id,
        seller_address=contract.seller_address,
        buyer_address=contract.buyer_address,
        amount_usdc=contract.amount_usdc,
        release_to_seller_pct=result.release_to_seller_pct,
    )
    chain = await EscrowChainClient().execute_resolution(chain_escrow_id=contract.chain_escrow_id, release_to_seller_pct=result.release_to_seller_pct)
    verdict = Verdict(
        dispute_id=dispute.id,
        kind=result.kind,
        release_to_seller_pct=result.release_to_seller_pct,
        confidence=result.confidence,
        rationale=result.rationale,
        leader=result.leader.model_dump(mode="json"),
        validators=[vote.model_dump(mode="json") for vote in result.validators],
        semantic_agreement=result.semantic_agreement | {"circle_payout": payout, "chain_execution": chain},
        payout_tx_id=payout.get("tx_id") or chain.get("tx_hash"),
    )
    dispute.status = DisputeStatus.executed
    contract.status = ContractStatus.resolved
    db.add(verdict)
    await log_audit(db, actor="consensus-engine", action="verdict.execute", subject_type="dispute", subject_id=dispute.id, payload=result.model_dump(mode="json"))
    await db.commit()
    await db.refresh(verdict)
    return verdict


@router.post("/disputes/{dispute_id}/appeal", response_model=VerdictRead, dependencies=[ApiKeyDependency])
async def appeal(dispute_id: str, db: AsyncSession = Depends(get_db)) -> Verdict:
    dispute = await db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute.appeal_count += 1
    dispute.status = DisputeStatus.appealed
    await db.commit()
    return await deliberate(dispute_id, db)


@router.get("/disputes/{dispute_id}/verdict", response_model=VerdictRead | None, dependencies=[ApiKeyDependency])
async def get_verdict(dispute_id: str, db: AsyncSession = Depends(get_db)) -> Verdict | None:
    result = await db.execute(select(Verdict).where(Verdict.dispute_id == dispute_id).order_by(desc(Verdict.created_at)).limit(1))
    return result.scalar_one_or_none()


@router.post("/agent/command", response_model=AgentCommandResult, dependencies=[ApiKeyDependency])
async def agent_command(payload: AgentCommand, db: AsyncSession = Depends(get_db)) -> AgentCommandResult:
    command = payload.command.lower()
    if "list" in command and "contract" in command:
        result = await db.execute(select(Contract).order_by(desc(Contract.created_at)).limit(10))
        contracts = [ContractRead.model_validate(row).model_dump(mode="json") for row in result.scalars().all()]
        return AgentCommandResult(action="contracts.list", message=f"Found {len(contracts)} contracts.", data={"contracts": contracts})
    if "deliberate" in command or "resolve" in command:
        dispute_id = command.split()[-1]
        if payload.dry_run:
            return AgentCommandResult(action="dispute.deliberate", message="Dry run accepted.", data={"dispute_id": dispute_id})
        verdict = await deliberate(dispute_id, db)
        return AgentCommandResult(action="dispute.deliberate", message="Verdict executed.", data=VerdictRead.model_validate(verdict).model_dump(mode="json"))
    return AgentCommandResult(
        action="help",
        message="Try: 'list contracts' or 'deliberate <dispute_id>'. Contract and dispute creation are available through REST endpoints.",
    )


@router.get("/audit", dependencies=[ApiKeyDependency])
async def audit_log(db: AsyncSession = Depends(get_db)) -> list[dict]:
    from app.models.db import AuditLog

    result = await db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(100))
    return [
        {
            "id": row.id,
            "actor": row.actor,
            "action": row.action,
            "subject_type": row.subject_type,
            "subject_id": row.subject_id,
            "payload": row.payload,
            "created_at": row.created_at,
        }
        for row in result.scalars().all()
    ]
