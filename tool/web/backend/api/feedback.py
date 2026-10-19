"""POST /api/feedback, GET /api/feedback?project=slug."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select

from ..audit import write_audit
from ..models import Feedback, Project, Variant
from ..models import Session as PSession

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


def get_session() -> Session:  # pragma: no cover
    raise NotImplementedError


def get_actor() -> str:  # pragma: no cover
    raise NotImplementedError


VALID_SEVERITY = {"critical", "high", "medium", "low"}
VALID_WCAG = {"A", "AA", "AAA", "N/A", None}


class FeedbackIn(BaseModel):
    variant_id: int
    role_id: int | None = None
    severity: str
    department: str
    category: str
    score: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1)
    ai_act_dimension: str | None = None
    wcag_level: str | None = None
    is_ai_only: bool = False

    @field_validator("severity")
    @classmethod
    def severity_valid(cls, v: str) -> str:
        if v not in VALID_SEVERITY:
            raise ValueError(f"severity must be one of {VALID_SEVERITY}")
        return v

    @field_validator("wcag_level")
    @classmethod
    def wcag_valid(cls, v: str | None) -> str | None:
        if v not in VALID_WCAG:
            raise ValueError(f"wcag_level must be one of {VALID_WCAG}")
        return v


@router.get("", response_model=list[Feedback])
def list_feedback(
    project: str = Query(..., description="Project slug"),
    db: Session = Depends(get_session),
) -> list[Feedback]:
    proj = db.exec(select(Project).where(Project.slug == project)).first()
    if not proj:
        raise HTTPException(404, f"Project '{project}' not found")

    session_ids = [
        s.id for s in db.exec(select(PSession).where(PSession.project_id == proj.id)).all()
    ]
    if not session_ids:
        return []
    variant_ids = [
        v.id for v in db.exec(select(Variant).where(Variant.session_id.in_(session_ids))).all()
    ]
    if not variant_ids:
        return []
    return list(
        db.exec(
            select(Feedback).where(Feedback.variant_id.in_(variant_ids)).order_by(Feedback.submitted_at.desc())
        ).all()
    )


@router.post("", status_code=201)
def submit_feedback(
    payload: FeedbackIn,
    db: Session = Depends(get_session),
    actor: str = Depends(get_actor),
) -> dict:
    variant = db.exec(select(Variant).where(Variant.id == payload.variant_id)).first()
    if not variant:
        raise HTTPException(404, f"Variant {payload.variant_id} not found")

    # AI-only score deflation max 0.5 (perspektiva 14, devil's advocate Útok 6 caveat)
    score = payload.score
    if payload.is_ai_only and score > 0.5:
        score = 0.5

    fb = Feedback(
        variant_id=payload.variant_id,
        role_id=payload.role_id,
        severity=payload.severity,
        department=payload.department,
        category=payload.category,
        score=score,
        rationale=payload.rationale,
        ai_act_dimension=payload.ai_act_dimension,
        wcag_level=payload.wcag_level,
        is_ai_only=payload.is_ai_only,
        submitted_by=actor,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)

    write_audit(
        db,
        actor=actor,
        action="feedback.create",
        target_type="feedback",
        target_id=fb.id,
        payload={
            "variant_id": payload.variant_id,
            "severity": payload.severity,
            "department": payload.department,
            "ai_only": payload.is_ai_only,
        },
    )
    db.commit()

    return {
        "id": fb.id,
        "variant_id": fb.variant_id,
        "role_id": fb.role_id,
        "severity": fb.severity,
        "department": fb.department,
        "category": fb.category,
        "score": fb.score,
        "rationale": fb.rationale,
        "ai_act_dimension": fb.ai_act_dimension,
        "wcag_level": fb.wcag_level,
        "is_ai_only": fb.is_ai_only,
        "submitted_by": fb.submitted_by,
        "submitted_at": fb.submitted_at.isoformat() if fb.submitted_at else None,
    }
