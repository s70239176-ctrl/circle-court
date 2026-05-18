from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import AuditLog


async def log_audit(
    db: AsyncSession,
    *,
    actor: str,
    action: str,
    subject_type: str,
    subject_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            payload=payload or {},
        )
    )
