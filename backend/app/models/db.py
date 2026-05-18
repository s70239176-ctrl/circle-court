import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ContractStatus(str, enum.Enum):
    draft = "draft"
    funded = "funded"
    active = "active"
    disputed = "disputed"
    resolved = "resolved"
    cancelled = "cancelled"


class DisputeStatus(str, enum.Enum):
    raised = "raised"
    deliberating = "deliberating"
    decided = "decided"
    appealed = "appealed"
    executed = "executed"


class VerdictKind(str, enum.Enum):
    full_release = "full_release"
    partial_release = "partial_release"
    refund = "refund"
    needs_more_evidence = "needs_more_evidence"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(180), index=True)
    description: Mapped[str] = mapped_column(Text)
    buyer_address: Mapped[str] = mapped_column(String(128))
    seller_address: Mapped[str] = mapped_column(String(128))
    arbiter_agent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    success_criteria: Mapped[list[str]] = mapped_column(JSON, default=list)
    subjective_clauses: Mapped[list[str]] = mapped_column(JSON, default=list)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount_usdc: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.draft)
    circle_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    circle_escrow_wallet_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    chain_escrow_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    disputes: Mapped[list["Dispute"]] = relationship(back_populates="contract", cascade="all, delete-orphan")


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    raised_by: Mapped[str] = mapped_column(String(128))
    claim: Mapped[str] = mapped_column(Text)
    requested_outcome: Mapped[str] = mapped_column(String(64))
    evidence: Mapped[list[dict]] = mapped_column(JSON, default=list)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus), default=DisputeStatus.raised)
    appeal_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contract: Mapped[Contract] = relationship(back_populates="disputes")
    verdicts: Mapped[list["Verdict"]] = relationship(back_populates="dispute", cascade="all, delete-orphan")


class Verdict(Base):
    __tablename__ = "verdicts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dispute_id: Mapped[str] = mapped_column(ForeignKey("disputes.id"), index=True)
    kind: Mapped[VerdictKind] = mapped_column(Enum(VerdictKind))
    release_to_seller_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    rationale: Mapped[str] = mapped_column(Text)
    leader: Mapped[dict] = mapped_column(JSON, default=dict)
    validators: Mapped[list[dict]] = mapped_column(JSON, default=list)
    semantic_agreement: Mapped[dict] = mapped_column(JSON, default=dict)
    payout_tx_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dispute: Mapped[Dispute] = relationship(back_populates="verdicts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor: Mapped[str] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    subject_type: Mapped[str] = mapped_column(String(80))
    subject_id: Mapped[str] = mapped_column(String(120), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
