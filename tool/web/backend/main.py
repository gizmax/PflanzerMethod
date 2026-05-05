"""Pflanzer web hub — FastAPI entry point.

Run locally:
    cd tool/web/backend
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from .api import feedback as feedback_router
from .api import projects as projects_router
from .api import variants as variants_router
from .models import get_engine

ENGINE = get_engine()


def get_session() -> Iterator[Session]:
    with Session(ENGINE) as session:
        yield session


def get_actor(request: Request) -> str:
    """Resolve actor from request header. v0: trust X-User header (dev only)."""
    return request.headers.get("X-User", "anonymous@web-hub")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="Pflanzer web hub",
    version="0.1.0",
    description="Prototype share + scored feedback (form-factor C — Hybrid).",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router.router)
app.include_router(variants_router.router)
app.include_router(feedback_router.router)

# Wire dependencies via FastAPI's dependency_overrides (Depends captures
# function refs at decoration time, so module-level reassignment doesn't work).
app.dependency_overrides[projects_router.get_session] = get_session
app.dependency_overrides[variants_router.get_session] = get_session
app.dependency_overrides[variants_router.get_actor] = get_actor
app.dependency_overrides[feedback_router.get_session] = get_session
app.dependency_overrides[feedback_router.get_actor] = get_actor


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api")
def api_root() -> dict[str, object]:
    return {
        "name": "pflanzer-web-hub",
        "version": "0.1.0",
        "docs": "/api/docs",
        "endpoints": [
            "GET  /api/projects",
            "GET  /api/projects/{slug}",
            "GET  /api/projects/{slug}/variants",
            "POST /api/projects/{slug}/variants",
            "GET  /api/feedback?project={slug}",
            "POST /api/feedback",
        ],
    }
