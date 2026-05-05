"""Audit logging helpers for web hub.

Mirrors tool/cli/db.py audit() but inside SQLModel context.
DORA 7-letá retence (devil's advocate Útok 8).
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from sqlmodel import Session as DBSession

from .models import AuditLog

DORA_RETENTION = timedelta(days=365 * 7 + 2)


def write_audit(
    db: DBSession,
    *,
    actor: str,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append an audit_log row."""
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload_json=json.dumps(payload, ensure_ascii=False) if payload else None,
            retention_until=(date.today() + DORA_RETENTION).isoformat(),
        )
    )
