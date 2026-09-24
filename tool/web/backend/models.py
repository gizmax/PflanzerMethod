"""SQLModel mirror of tool/db/schema.sql.

Read-mostly for projects/roles/triage; write for variants/feedback/audit/decisions.
The CC side (tool/cli/*.py) writes most rows; the web hub adds variants
(via /api/projects/{slug}/variants) and feedback (via /api/feedback).
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from sqlmodel import Field, SQLModel, create_engine

REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_db_path() -> Path:
    """Resolve the DB exactly like tool/cli/db.py so the hub and the CLI share one DB.

    Order: PFLANZER_DB env > ~/.pflanzer/pflanzer.db (installed plugin, file must
    exist) > <repo>/data/pflanzer.db (dev mode). Kept in sync with
    tool/cli/db.py::_resolve_db_path (covered by tests/test_db_path.py).
    """
    if env := os.environ.get("PFLANZER_DB"):
        return Path(env).expanduser()
    user_db = Path.home() / ".pflanzer" / "pflanzer.db"
    if user_db.is_file():
        return user_db
    return REPO_ROOT / "data" / "pflanzer.db"


DB_PATH = _resolve_db_path()


class Project(SQLModel, table=True):
    __tablename__ = "projects"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    charter_md: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "draft"
    decider_name: str | None = None
    decider_mandate_from: str | None = None
    cpo_escalation_contact: str | None = None
    sponsor_name: str | None = None
    ai_act_tier: str | None = None
    data_class: str | None = None
    throwaway_or_evolve: str | None = None
    capacity_profile: str | None = None
    tier: str | None = None  # quick | lean | full (ADR-0021)
    capacity_person_days: int | None = None
    xyz_hypothesis: str | None = None
    primary_lagging_metric: str | None = None
    leading_metric: str | None = None
    guardrail_metric: str | None = None
    kill_criteria: str | None = None
    reinforcement_t7: str | None = None
    reinforcement_t30: str | None = None
    reinforcement_t60: str | None = None
    reinforcement_t90: str | None = None
    reinforcement_budget_pd: float | None = None


class Role(SQLModel, table=True):
    __tablename__ = "roles"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    catalog_idx: int
    catalog_label: str
    status: str
    ai_proxy_mode: str
    human_owner: str | None = None
    expert_agent_path: str | None = None
    rationale: str | None = None


class Triage(SQLModel, table=True):
    __tablename__ = "triage"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    track: str
    status: str
    artefact_md: str
    signed_by: str | None = None
    signed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(SQLModel, table=True):
    __tablename__ = "sessions"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    type: int
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    decision: str | None = None
    decision_atribuce: str | None = None
    decision_ts: datetime | None = None
    notes_md: str | None = None


class Variant(SQLModel, table=True):
    __tablename__ = "variants"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    name: str
    builder: str
    prototype_url: str
    description_md: str | None = None
    preference_score: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Feedback(SQLModel, table=True):
    __tablename__ = "feedback"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    variant_id: int = Field(foreign_key="variants.id")
    role_id: int | None = Field(default=None, foreign_key="roles.id")
    severity: str
    department: str
    category: str
    score: float
    rationale: str
    ai_act_dimension: str | None = None
    wcag_level: str | None = None
    is_ai_only: bool = False
    submitted_by: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.utcnow)
    actor: str
    action: str
    target_type: str | None = None
    target_id: int | None = None
    payload_json: str | None = None
    retention_until: str | None = None  # ISO date string


def get_engine() -> object:
    return create_engine(
        f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False}
    )
