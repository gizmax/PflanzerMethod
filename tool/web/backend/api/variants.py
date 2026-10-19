"""POST /api/projects/{slug}/variants, GET /api/projects/{slug}/variants."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from ..audit import write_audit
from ..models import Feedback, Project, Variant, utcnow
from ..models import Session as PSession

router = APIRouter(prefix="/api/projects", tags=["variants"])


def get_session() -> Session:  # pragma: no cover
    raise NotImplementedError


def get_actor() -> str:  # pragma: no cover
    raise NotImplementedError


class VariantIn(BaseModel):
    name: str
    builder: str  # v0|bolt|lovable|stitch|cursor|figma-make|manual
    prototype_url: str
    description_md: str | None = None
    preference_score: float | None = Field(default=None, ge=0, le=1)


@router.get("/{slug}/variants")
def list_variants(
    slug: str,
    db: Session = Depends(get_session),
    actor: str = Depends(get_actor),
) -> list[dict]:
    """Varianty projektu + počet feedbacků a příznak, zda už feedback dal volající."""
    project = db.exec(select(Project).where(Project.slug == slug)).first()
    if not project:
        raise HTTPException(404, f"Project '{slug}' not found")

    session_ids = [
        s.id for s in db.exec(select(PSession).where(PSession.project_id == project.id)).all()
    ]
    if not session_ids:
        return []
    variants = list(
        db.exec(select(Variant).where(Variant.session_id.in_(session_ids)).order_by(Variant.id)).all()
    )
    from .projects import variants_in_play
    in_play = variants_in_play(db, project)
    if in_play:
        latest = {v.name: v for v in variants if v.name in in_play}   # nový řádek přebíjí starý
        variants = sorted(latest.values(), key=lambda v: v.id)
    out: list[dict] = []
    for v in variants:
        fbs = db.exec(select(Feedback).where(Feedback.variant_id == v.id)).all()
        row = v.model_dump(mode="json")
        row["feedback_count"] = len(fbs)
        row["my_feedback"] = any(f.submitted_by == actor for f in fbs)
        out.append(row)
    return out


@router.post("/{slug}/variants", status_code=201)
def create_variant(
    slug: str,
    payload: VariantIn,
    db: Session = Depends(get_session),
    actor: str = Depends(get_actor),
) -> dict:
    project = db.exec(select(Project).where(Project.slug == slug)).first()
    if not project:
        raise HTTPException(404, f"Project '{slug}' not found")

    # Find or create the Build (type=1) row
    session_row = db.exec(
        select(PSession).where(PSession.project_id == project.id, PSession.type == 1)
    ).first()
    if not session_row:
        session_row = PSession(project_id=project.id, type=1, starts_at=utcnow())
        db.add(session_row)
        db.commit()
        db.refresh(session_row)

    variant = Variant(
        session_id=session_row.id,
        name=payload.name,
        builder=payload.builder,
        prototype_url=payload.prototype_url,
        description_md=payload.description_md,
        preference_score=payload.preference_score,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)

    write_audit(
        db,
        actor=actor,
        action="variant.create",
        target_type="variant",
        target_id=variant.id,
        payload={"slug": slug, "builder": payload.builder, "name": payload.name},
    )
    db.commit()

    return {
        "id": variant.id,
        "session_id": variant.session_id,
        "name": variant.name,
        "builder": variant.builder,
        "prototype_url": variant.prototype_url,
        "description_md": variant.description_md,
        "preference_score": variant.preference_score,
        "created_at": variant.created_at.isoformat() if variant.created_at else None,
    }
