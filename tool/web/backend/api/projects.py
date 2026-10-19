"""GET /api/projects, GET /api/projects/{slug}."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlmodel import Session, select

from ..models import AuditLog, Project, Role, Triage
from ..models import Session as PSession

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_session() -> Session:  # pragma: no cover — overridden in main
    raise NotImplementedError


@router.get("", response_model=list[Project])
def list_projects(db: Session = Depends(get_session)) -> list[Project]:
    return list(db.exec(select(Project).order_by(Project.created_at.desc())).all())


def _extra_columns(db: Session, project_id: int) -> dict[str, Any]:
    """Sloupce přidané migrací (path_owners_json, core_json, async_deadline).

    Čteme je surovým SQL, aby hub fungoval i se starší DB, kde sloupce nejsou.
    """
    cols = {r[1] for r in db.connection().execute(text("PRAGMA table_info(projects)")).fetchall()}
    wanted = [c for c in ("path_owners_json", "core_json", "async_deadline") if c in cols]
    if not wanted:
        return {}
    row = db.connection().execute(
        text(f"SELECT {', '.join(wanted)} FROM projects WHERE id = :i"), {"i": project_id}
    ).fetchone()
    return dict(zip(wanted, row, strict=True)) if row else {}


def _json_or(value: Any, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _shortlist(db: Session, project_id: int) -> list[str]:
    sids = [s.id for s in db.exec(
        select(PSession).where(PSession.project_id == project_id, PSession.type == 1)).all()]
    if not sids:
        return []
    row = db.exec(
        select(AuditLog).where(AuditLog.action == "session_1.persist",
                               AuditLog.target_id.in_(sids)).order_by(AuditLog.id.desc())
    ).first()
    data = _json_or(row.payload_json if row else None, {})
    return [str(x) for x in data.get("shortlist", []) or []] if isinstance(data, dict) else []


@router.get("/{slug}")
def get_project(slug: str, db: Session = Depends(get_session)) -> dict:
    project = db.exec(select(Project).where(Project.slug == slug)).first()
    if not project:
        raise HTTPException(404, f"Project '{slug}' not found")

    roles = list(db.exec(select(Role).where(Role.project_id == project.id)).all())
    triage = list(db.exec(select(Triage).where(Triage.project_id == project.id)).all())

    extra = _extra_columns(db, project.id)
    owners = _json_or(extra.get("path_owners_json"), {})
    return {
        "project": project,
        "roles": roles,
        "triage": triage,
        "path_owners": owners if isinstance(owners, dict) else {},
        "core": _json_or(extra.get("core_json"), []),
        "shortlist": _shortlist(db, project.id),
        "async_deadline": extra.get("async_deadline"),
    }
