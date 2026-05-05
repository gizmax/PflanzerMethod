"""GET /api/projects, GET /api/projects/{slug}."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..models import Project, Role, Triage

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_session() -> Session:  # pragma: no cover — overridden in main
    raise NotImplementedError


@router.get("", response_model=list[Project])
def list_projects(db: Session = Depends(get_session)) -> list[Project]:
    return list(db.exec(select(Project).order_by(Project.created_at.desc())).all())


@router.get("/{slug}")
def get_project(slug: str, db: Session = Depends(get_session)) -> dict:
    project = db.exec(select(Project).where(Project.slug == slug)).first()
    if not project:
        raise HTTPException(404, f"Project '{slug}' not found")

    roles = list(db.exec(select(Role).where(Role.project_id == project.id)).all())
    triage = list(db.exec(select(Triage).where(Triage.project_id == project.id)).all())

    return {
        "project": project,
        "roles": roles,
        "triage": triage,
    }
