"""GET /api/projects, GET /api/projects/{slug}."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlmodel import Session, select

from ..models import DB_PATH, AuditLog, Project, Role, Triage, Variant
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


def _audit_payloads(db: Session, action: str, project_id: int) -> list[dict[str, Any]]:
    rows = db.exec(select(AuditLog).where(
        AuditLog.action == action, AuditLog.target_id == project_id
    ).order_by(AuditLog.id.desc())).all()
    out = []
    for r in rows:
        d = _json_or(r.payload_json, {})
        if isinstance(d, dict):
            out.append(d)
    return out


def variants_in_play(db: Session, project: Project) -> list[str]:
    """Varianty ve hře po Iterate (explicitní `--variants`, jinak shortlist, jinak všechny).

    Mimo Iterate vrací [] = ve hře jsou všechny. Zrcadlí `tool/cli/status.py::variants_in_play`.
    """
    sids = [s.id for s in db.exec(
        select(PSession).where(PSession.project_id == project.id, PSession.type == 1)).all()]
    names = sorted({v.name for v in db.exec(
        select(Variant).where(Variant.session_id.in_(sids))).all()}) if sids else []
    if project.status == "session_2":
        decisions = _audit_payloads(db, "session_2.decision", project.id)
        chosen = []
        if decisions and decisions[0].get("decision") == "iterate":
            chosen = [str(x) for x in decisions[0].get("iterate_variants") or []]
        chosen = [n for n in chosen if n in names]
        short = [n for n in _shortlist(db, project.id) if n in names]
        return sorted(dict.fromkeys(chosen)) or sorted(dict.fromkeys(short)) or names
    if sids:
        row = db.exec(select(AuditLog).where(
            AuditLog.action == "session_1.persist", AuditLog.target_id.in_(sids)
        ).order_by(AuditLog.id.desc())).first()
        data = _json_or(row.payload_json if row else None, {})
        if isinstance(data, dict) and data.get("iterate_round"):
            return [str(x) for x in data.get("variants", []) or []]
    return []


def _all_variant_names(db: Session, project_id: int) -> list[str]:
    sids = [s.id for s in db.exec(select(PSession).where(PSession.project_id == project_id)).all()]
    if not sids:
        return []
    rows = db.exec(select(Variant).where(Variant.session_id.in_(sids))).all()
    return sorted({v.name for v in rows})


def _data_root() -> Path:
    if env := os.environ.get("PFLANZER_DATA"):
        return Path(env).expanduser()
    return Path(DB_PATH).parent


def _is_local(request: Request) -> bool:
    h = request.headers
    if any(h.get(k) for k in ("X-Forwarded-For", "X-Forwarded-Email", "X-Forwarded-User")):
        return False
    host = request.client.host if request.client else ""
    return host in ("127.0.0.1", "::1", "localhost", "testclient")


def _preview_login(slug: str, request: Request) -> dict[str, Any] | None:
    """Přihlášení k náhledu pro zástupce. Heslo se vrací jen z hubu za heslem (volající už
    prošel Basic auth) nebo na localhostu — na veřejném hubu bez hesla nikdy."""
    try:
        state = json.loads((_data_root() / "preview" / f"{slug}.json").read_text("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict) or not state.get("password"):
        return None
    safe = bool(os.environ.get("PFLANZER_HUB_PASSWORD")) or _is_local(request)
    return {"user": state.get("user") or "pflanzer",
            "password": state["password"] if safe else None}


def _kill_info(db: Session, project: Project) -> dict[str, Any] | None:
    if project.status != "killed":
        return None
    reason = None
    row = db.execute(text(
        "SELECT body_md FROM decisions WHERE project_id = :i AND type = 'kill' "
        "ORDER BY id DESC LIMIT 1"), {"i": project.id}).fetchone()
    if row and row[0]:
        m = re.search(r"### Důvod\s*\n+(.+?)(?:\n###|\Z)", row[0], re.S)
        reason = m.group(1).strip() if m else None
    lessons = []
    for d in reversed(_audit_payloads(db, "retro.lesson", project.id)):
        if d.get("text"):
            lessons.append({"text": str(d["text"]), "by": d.get("by")})
    return {"reason": reason, "lessons": lessons}


def _risk_info(db: Session, project: Project) -> dict[str, Any]:
    cols = {r[1] for r in db.connection().execute(text("PRAGMA table_info(projects)")).fetchall()}
    sel = [c for c in ("risk_profile", "production_readiness_target") if c in cols]
    row = db.connection().execute(
        text(f"SELECT {', '.join(sel)} FROM projects WHERE id = :i"), {"i": project.id}
    ).fetchone() if sel else None
    raw = dict(zip(sel, row, strict=True)) if row else {}
    profile = raw.get("risk_profile")
    if profile not in ("throwaway", "pilot", "production"):
        target = raw.get("production_readiness_target") or 0
        profile = ("production" if target >= 85 else "pilot" if target else
                   "throwaway" if project.throwaway_or_evolve == "throwaway" else "pilot")
    return {"risk_profile": profile}


@router.get("/{slug}")
def get_project(slug: str, request: Request, db: Session = Depends(get_session)) -> dict:
    project = db.exec(select(Project).where(Project.slug == slug)).first()
    if not project:
        raise HTTPException(404, f"Project '{slug}' not found")

    roles = list(db.exec(select(Role).where(Role.project_id == project.id)).all())
    triage = list(db.exec(select(Triage).where(Triage.project_id == project.id)).all())

    extra = _extra_columns(db, project.id)
    owners = _json_or(extra.get("path_owners_json"), {})
    owners = owners if isinstance(owners, dict) else {}
    pm = owners.get("produkt")
    in_play = variants_in_play(db, project)
    return {
        "project": project,
        "roles": roles,
        "triage": triage,
        "path_owners": owners,
        "decider_name": project.decider_name or None,
        "pm_name": pm if isinstance(pm, str) and pm and not pm.upper().startswith("AI") else None,
        "core": _json_or(extra.get("core_json"), []),
        "shortlist": _shortlist(db, project.id),
        "async_deadline": extra.get("async_deadline"),
        "variants_in_play": in_play,
        "variants_dropped": [n for n in _all_variant_names(db, project.id)
                             if in_play and n not in in_play],
        "preview_login": _preview_login(slug, request),
        "kill": _kill_info(db, project),
        **_risk_info(db, project),
    }
