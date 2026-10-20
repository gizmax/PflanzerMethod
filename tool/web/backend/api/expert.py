"""Expertní panel (pilot 20): kdo chybí, okna čekající na podpis, tiché hlasování.

Hub tu nic nepodepisuje ani nerozhoduje: jen čte stav z DB a skládá hotové příkazy pro CLI
(`pflanzer checkpoint …`, `pflanzer decide …`). Jediný zápis je názor v tichém hlasování
(`decision_votes`) a jeho odkrytí (audit_log).
"""
from __future__ import annotations

import sqlite3
import unicodedata
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, SQLModel, select

from ..audit import write_audit
from ..models import AuditLog, DecisionVote, Feedback, Project, Triage, Variant
from ..models import Session as PSession
from .projects import (
    _audit_payloads,
    _extra_columns,
    _human,
    _is_ai,
    _json_or,
    _risk_info,
    step_confirmers,
)

router = APIRouter(prefix="/api/projects", tags=["expert"])

STEP_LABELS = {"byznys": "Byznys", "produkt": "Produkt", "design": "Design",
               "vyvoj": "Vývoj", "bezpecnost": "Bezpečnost & právo", "provoz": "Provoz"}
WINDOW_STEP = {"bezpecnost": "bezpecnost", "provoz": "provoz", "design": "design"}
WINDOW_LABEL = {"bezpecnost": "Bezpečnost & právo", "provoz": "Provoz", "design": "Design (AI)"}
WINDOW_TRACKS = {"bezpecnost": ("security", "legal"), "provoz": ("platform",)}
CHOICES = ("go", "iterate", "kill")
COLLECTING = ("session_1",)
VOTING = ("session_1", "session_2")


def get_session() -> Session:  # pragma: no cover — overridden in main
    raise NotImplementedError


def get_actor() -> str:  # pragma: no cover — overridden in main
    raise NotImplementedError


def _norm(name: str | None) -> str:
    s = unicodedata.normalize("NFKD", (name or "").strip())
    s = "".join(c for c in s if not unicodedata.combining(c)).casefold()
    if "@" in s:                                   # SSO identita: jana.novakova@firma.cz
        s = s.split("@", 1)[0].replace(".", " ").replace("_", " ")
    return " ".join(s.split())


def same_person(a: str | None, b: str | None) -> bool:
    ta, tb = set(_norm(a).split()), set(_norm(b).split())
    return bool(ta and tb and (ta <= tb or tb <= ta))


def _project(db: Session, slug: str) -> Project:
    project = db.exec(select(Project).where(Project.slug == slug)).first()
    if not project:
        raise HTTPException(404, f"Project '{slug}' not found")
    return project


def _owners(db: Session, project: Project) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    extra = _extra_columns(db, project.id)
    owners = _json_or(extra.get("path_owners_json"), {})
    owners = owners if isinstance(owners, dict) else {}
    raw = _json_or(extra.get("ai_signers_json"), {})
    signers = {str(k): str(v) for k, v in raw.items()} if isinstance(raw, dict) else {}
    risk = _risk_info(db, project)["risk_profile"]
    confirmers = step_confirmers(owners, signers, project.decider_name, risk)
    return owners, confirmers, {"risk": risk}


def _submitters(db: Session, project_id: int) -> list[str]:
    sids = [s.id for s in db.exec(select(PSession).where(PSession.project_id == project_id)).all()]
    vids = [v.id for v in db.exec(select(Variant).where(Variant.session_id.in_(sids))).all()] \
        if sids else []
    if not vids:
        return []
    return [f.submitted_by for f in db.exec(
        select(Feedback).where(Feedback.variant_id.in_(vids))).all()]


def _first(name: str) -> str:
    return name.strip().split()[0] if name.strip() else name


def missing_people(db: Session, project: Project) -> list[dict[str, Any]]:
    """Zástupci kroků, kteří k projektu zatím nedali žádný feedback (Decider se nepočítá)."""
    owners, confirmers, _ = _owners(db, project)
    people: list[dict[str, Any]] = []
    for step in STEP_LABELS:
        who = _human(owners.get(step)) or confirmers.get(step)
        if not who or same_person(who, project.decider_name):
            continue
        row = next((p for p in people if same_person(p["name"], who)), None)
        if row is None:
            people.append({"name": who, "steps": [step]})
        elif step not in row["steps"]:
            row["steps"].append(step)
    given = _submitters(db, project.id)
    return [{"name": p["name"], "steps": p["steps"],
             "labels": [STEP_LABELS[s] for s in p["steps"]]}
            for p in people if not any(same_person(p["name"], g) for g in given)]


@router.get("/{slug}/missing")
def get_missing(slug: str, db: Session = Depends(get_session)) -> dict:
    project = _project(db, slug)
    collecting = project.status in COLLECTING
    missing = missing_people(db, project) if collecting else []
    text = ("Chybí: " + ", ".join(f"{_first(m['name'])} ({', '.join(m['labels'])})"
                                  for m in missing)) if missing else None
    return {"collecting": collecting, "missing": missing, "text": text}


def _track_state(rows: dict[str, Triage], tracks: tuple[str, ...]) -> str:
    statuses = {rows[t].status if t in rows else "missing" for t in tracks}
    return ("ok" if statuses == {"ok"} else "blocked" if "blocked" in statuses else
            "pending" if "pending" in statuses else "čeká")


def checkpoint_command(slug: str, window: str, who: str | None) -> str:
    return (f'pflanzer checkpoint --slug {slug} {window} --by "{who or "<jméno člověka>"}" '
            '--note "co jsem ověřil"')


def _merged_window(db: Session, project_id: int) -> bool:
    """Pilot bez osobních dat má jedno okno Bezpečnost a provoz (stejné pravidlo jako CLI)."""
    try:
        from tool.cli.checkpoint import merged_applies
    except Exception:  # noqa: BLE001 — hub bez CLI na PYTHONPATH: oddělená okna
        return False
    raw = db.connection().connection.dbapi_connection
    prev = raw.row_factory
    raw.row_factory = sqlite3.Row  # CLI dotazy čtou řádky podle jmen sloupců
    try:
        return bool(merged_applies(raw, project_id))
    except Exception:  # noqa: BLE001 — poradní rozhodnutí
        return False
    finally:
        raw.row_factory = prev


@router.get("/{slug}/windows")
def get_windows(slug: str, db: Session = Depends(get_session)) -> dict:
    """Nepodepsaná okna (Bezpečnost & právo, Provoz, Design-AI): kdo podepíše + hotový příkaz."""
    project = _project(db, slug)
    owners, confirmers, _ = _owners(db, project)
    rows = {t.track: t for t in db.exec(select(Triage).where(Triage.project_id == project.id))}
    out: list[dict[str, Any]] = []
    if project.status in ("killed", "draft"):
        return {"windows": out}
    merged = _merged_window(db, project.id)
    if merged:
        state = _track_state(rows, ("security", "legal", "platform"))
        if state != "ok":
            signer = (_human(owners.get("bezpecnost")) or confirmers.get("bezpecnost")
                      or _human(owners.get("provoz")) or confirmers.get("provoz"))
            out.append({"window": "bezpecnost-provoz", "label": "Bezpečnost a provoz",
                        "state": state, "signer": signer,
                        "command": checkpoint_command(slug, "bezpecnost-provoz", signer)})
    for window, step in WINDOW_STEP.items():
        if merged and window != "design":
            continue
        owner = owners.get(step)
        if window == "design":
            if not _is_ai(owner):
                continue
            last = next((p for p in _audit_payloads(db, "checkpoint.design", project.id)), {})
            state = last.get("status") if last.get("status") in ("ok", "blocked") else "pending"
        else:
            state = _track_state(rows, WINDOW_TRACKS[window])
        if state == "ok":
            continue
        signer = _human(owner) or confirmers.get(step)
        out.append({"window": window, "label": WINDOW_LABEL[window], "state": state,
                    "signer": signer, "command": checkpoint_command(slug, window, signer)})
    return {"windows": out}


# --- tiché hlasování --------------------------------------------------------------------------

class VoteIn(BaseModel):
    choice: str
    winner: str | None = Field(default=None, max_length=40)
    comment: str = Field(default="", max_length=500)

    @field_validator("choice")
    @classmethod
    def choice_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in CHOICES:
            raise ValueError(f"choice must be one of {CHOICES}")
        return v


def _ensure_table(db: Session) -> None:
    """Starší DB bez migrace: tabulku hlasů vytvoříme (idempotentně) při prvním použití."""
    SQLModel.metadata.create_all(db.get_bind(), tables=[DecisionVote.__table__])  # type: ignore[attr-defined]


def _reveal_row(db: Session, project_id: int) -> AuditLog | None:
    return db.exec(select(AuditLog).where(
        AuditLog.action == "vote.reveal", AuditLog.target_id == project_id)).first()


def _voters(db: Session, project: Project) -> list[str]:
    owners, confirmers, _ = _owners(db, project)
    names: list[str] = []
    for step in STEP_LABELS:
        who = _human(owners.get(step)) or confirmers.get(step)
        if who and not same_person(who, project.decider_name) \
                and not any(same_person(who, n) for n in names):
            names.append(who)
    return names


def _is_decider(project: Project, actor: str) -> bool:
    return bool(project.decider_name) and same_person(actor, project.decider_name)


def vote_command(slug: str, choice: str, winner: str | None, rationale: str) -> str:
    rationale = (rationale or "důvod v jedné větě").replace('"', "'")
    win = f" --winner {winner}" if choice == "go" and winner else ""
    return f'pflanzer decide --slug {slug} {choice}{win} --rationale "{rationale}"'


def _state(db: Session, project: Project, actor: str) -> dict[str, Any]:
    _ensure_table(db)
    voters = _voters(db, project)
    votes = list(db.exec(select(DecisionVote).where(
        DecisionVote.project_id == project.id).order_by(DecisionVote.id)).all())
    decider_vote = next((v for v in votes if _is_decider(project, v.voter)), None)
    others = [v for v in votes if not _is_decider(project, v.voter)]
    all_in = bool(voters) and all(any(same_person(n, v.voter) for v in others) for n in voters)
    forced = _reveal_row(db, project.id) is not None
    revealed = all_in or forced
    mine = next((v for v in votes if same_person(v.voter, actor)), None)
    shown = votes if revealed else ([mine] if mine else [])
    tally = {c: 0 for c in CHOICES}
    if revealed:
        for v in votes:
            tally[v.choice] += 1
    lead = None
    if revealed and votes:
        lead = decider_vote or max(votes, key=lambda v: (tally[v.choice], -votes.index(v)))
    return {
        "enabled": project.status in VOTING,
        "revealed": revealed,
        "is_decider": _is_decider(project, actor),
        "decider": project.decider_name,
        "can_vote": project.status in VOTING and (
            revealed if _is_decider(project, actor) else not revealed),
        "can_reveal": project.status in VOTING and _is_decider(project, actor) and not revealed,
        "voters": [{"name": n, "voted": any(same_person(n, v.voter) for v in others)}
                   for n in voters],
        "decider_voted": decider_vote is not None and revealed,
        "mine": _vote_out(mine) if mine else None,
        "votes": [_vote_out(v) for v in shown],
        "tally": tally if revealed else None,
        "command": (vote_command(project.slug, lead.choice, lead.winner, lead.comment)
                    if lead is not None else None),
    }


def _vote_out(v: DecisionVote) -> dict[str, Any]:
    return {"voter": v.voter, "choice": v.choice, "winner": v.winner, "comment": v.comment}


@router.get("/{slug}/votes")
def get_votes(slug: str, db: Session = Depends(get_session),
              actor: str = Depends(get_actor)) -> dict:
    return _state(db, _project(db, slug), actor)


@router.post("/{slug}/votes", status_code=201)
def post_vote(slug: str, payload: VoteIn, db: Session = Depends(get_session),
              actor: str = Depends(get_actor)) -> dict:
    project = _project(db, slug)
    if project.status not in VOTING:
        raise HTTPException(409, "Hlasovat se dá jen před Rozhodnutím.")
    state = _state(db, project, actor)
    if _is_decider(project, actor) and not state["revealed"]:
        raise HTTPException(409, "Decider hlasuje poslední — nejdřív odkryjte hlasy ostatních.")
    if not _is_decider(project, actor) and state["revealed"]:
        raise HTTPException(409, "Hlasy už jsou odkryté, hlasování je uzavřené.")
    if payload.choice == "go" and not (payload.winner or "").strip():
        raise HTTPException(422, "U volby Go uveďte vítěznou variantu.")
    winner = (payload.winner or "").strip() or None
    mine = db.exec(select(DecisionVote).where(
        DecisionVote.project_id == project.id, DecisionVote.voter == actor)).first()
    if mine:
        mine.choice, mine.winner, mine.comment = payload.choice, winner, payload.comment.strip()
        db.add(mine)
    else:
        db.add(DecisionVote(project_id=project.id, voter=actor, choice=payload.choice,
                            winner=winner, comment=payload.comment.strip()))
    write_audit(db, actor=actor, action="vote.cast", target_type="project",
                target_id=project.id, payload={"choice": payload.choice})
    db.commit()
    return _state(db, project, actor)


@router.post("/{slug}/votes/reveal")
def reveal_votes(slug: str, db: Session = Depends(get_session),
                 actor: str = Depends(get_actor)) -> dict:
    project = _project(db, slug)
    if project.status not in VOTING:
        raise HTTPException(409, "Hlasovat se dá jen před Rozhodnutím.")
    if not _is_decider(project, actor):
        raise HTTPException(403, "Hlasy odkrývá jen Decider"
                            + (f" ({project.decider_name})." if project.decider_name else "."))
    if _reveal_row(db, project.id) is None:
        write_audit(db, actor=actor, action="vote.reveal", target_type="project",
                    target_id=project.id)
        db.commit()
    return _state(db, project, actor)
