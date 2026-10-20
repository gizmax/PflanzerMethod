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
    wanted = [c for c in ("path_owners_json", "core_json", "async_deadline", "ai_signers_json")
              if c in cols]
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


PROXY_HEADERS = ("X-Forwarded-For", "X-Forwarded-Email", "X-Forwarded-User", "X-Forwarded-Host",
                 "Forwarded", "X-Real-Ip", "Cf-Connecting-Ip", "Cf-Ray", "Cf-Visitor",
                 "True-Client-Ip")


def _is_local(request: Request) -> bool:
    """Skutečně lokální požadavek: z loopbacku, bez hlaviček proxy/tunelu a s Host na localhost.

    Tunel (cloudflared) doručuje provoz z 127.0.0.1, takže IP klienta sama nestačí.
    """
    h = request.headers
    if any(h.get(k) for k in PROXY_HEADERS):
        return False
    host = (h.get("host") or "").rsplit(":", 1)[0].strip("[]").lower() if h.get("host") else ""
    if host and host not in ("127.0.0.1", "::1", "localhost", "testserver"):
        return False
    client = request.client.host if request.client else ""
    return client in ("127.0.0.1", "::1", "localhost", "testclient")


def _preview_login(slug: str, request: Request) -> dict[str, Any] | None:
    """Přihlášení k náhledu pro zástupce. Heslo se vrací jen z hubu za heslem (volající už
    prošel Basic auth) nebo na localhostu — na veřejném hubu bez hesla nikdy."""
    try:
        state = json.loads((_data_root() / "preview" / f"{slug}.json").read_text("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict) or not state.get("password"):
        return None
    # Heslo jen po ověření heslem hubu (middleware s heslem pustí jen autentizované požadavky);
    # bez hesla jen skutečně lokální požadavek. Loopback IP sama nestačí (tunel).
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


def _is_ai(name: Any) -> bool:
    return isinstance(name, str) and bool(re.match(r"(?i)^\s*AI(:|\s|$)", name))


def _human(name: Any) -> str | None:
    return name.strip() if isinstance(name, str) and name.strip() and not _is_ai(name) else None


def _same_person(a: str | None, b: str | None) -> bool:
    ta, tb = set((a or "").casefold().split()), set((b or "").casefold().split())
    return bool(ta and tb and (ta <= tb or tb <= ta))


def step_confirmers(owners: dict[str, Any], signers: dict[str, Any], decider: str | None,
                    risk: str) -> dict[str, str]:
    """Krok s AI náhradou -> člověk, který AI draft skutečně podepíše.

    Zrcadlí `tool/cli/checkpoint.py::_signer_for` (ADR-0023): 1) `ai_signers` z Kickoffu
    (u production ne autor kódu), 2) u pilotu provoz vývojář z jádra, 3) design PdM / Decider,
    4) jinak Decider (u kroku bez určeného člověka určí podepisujícího Decider).
    """
    out: dict[str, str] = {}
    dev = _human(owners.get("vyvoj"))
    fallback = _human(owners.get("byznys")) or _human(decider) or _human(owners.get("produkt"))
    for step, owner in owners.items():
        if not _is_ai(owner):
            continue
        who = _human(signers.get(step))
        if who and risk == "production" and step != "design" and dev and _same_person(who, dev):
            who = None
        if not who and step == "provoz" and risk == "pilot":
            who = dev
        if not who and step == "design":
            who = _human(owners.get("produkt")) or _human(owners.get("byznys"))
        who = who or fallback
        if who:
            out[step] = who
    return out


def _decision_info(db: Session, project: Project) -> dict[str, Any] | None:
    """Rozhodnutí (Go/Iterate/Kill): vítěz, důvod, kdo rozhodl. Jen čtení z DB."""
    if project.status not in ("handoff", "session_2", "killed"):
        return None
    payloads = _audit_payloads(db, "session_2.decision", project.id)
    last = payloads[0] if payloads else {}
    decision = last.get("decision")
    winner = last.get("winner")
    if not decision:
        return None
    reason = None
    try:
        row = db.execute(text(
            "SELECT body_md FROM decisions WHERE project_id = :i "
            "AND type IN ('handoff','preference','kill') ORDER BY id DESC LIMIT 1"),
            {"i": project.id}).fetchone()
    except Exception:  # noqa: BLE001 — hub nad DB bez tabulky decisions
        row = None
    if row and row[0]:
        m = re.search(r"### Důvod\s*\n+(.+?)(?:\n###|\Z)", row[0], re.S)
        reason = m.group(1).strip() if m else None
    return {"decision": decision, "winner": winner, "rationale": reason,
            "decider": last.get("decider"),
            "below_commitment": last.get("below_commitment")}


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
    signers_raw = _json_or(extra.get("ai_signers_json"), {})
    signers = ({str(k): str(v) for k, v in signers_raw.items()}
               if isinstance(signers_raw, dict) else {})
    risk = _risk_info(db, project)
    in_play = variants_in_play(db, project)
    return {
        "project": project,
        "roles": roles,
        "triage": triage,
        "path_owners": owners,
        "decider_name": project.decider_name or None,
        "pm_name": pm if isinstance(pm, str) and pm and not pm.upper().startswith("AI") else None,
        # kdo skutečně podepíše krok s AI náhradou (ne vždy PdM) + explicitně určení podepisující
        "confirmers": step_confirmers(owners, signers, project.decider_name, risk["risk_profile"]),
        "ai_signers": {k: v for k, v in signers.items()
                       if _human(v) and _is_ai(owners.get(k))},
        "decision": _decision_info(db, project),
        "core": _json_or(extra.get("core_json"), []),
        "shortlist": _shortlist(db, project.id),
        "async_deadline": extra.get("async_deadline"),
        "variants_in_play": in_play,
        "variants_dropped": [n for n in _all_variant_names(db, project.id)
                             if in_play and n not in in_play],
        "preview_login": _preview_login(slug, request),
        "kill": _kill_info(db, project),
        **risk,
    }
