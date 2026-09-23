"""Pflanzer web hub — FastAPI entry point.

Run locally:
    cd tool/web/backend
    PFLANZER_HUB_AUTH_MODE=dev uvicorn main:app --reload --port 8000

Auth modes (env PFLANZER_HUB_AUTH_MODE, see tool/web/README-auth.md):
    oidc (default) — identity comes only from oauth2-proxy headers
                     (X-Forwarded-Email, then X-Forwarded-User); missing -> 401.
    dev            — additionally trusts the client-supplied X-User header.
"""
from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from .api import feedback as feedback_router
from .api import projects as projects_router
from .api import variants as variants_router
from .models import get_engine

ENGINE = get_engine()

log = logging.getLogger("pflanzer.web_hub")

AUTH_MODE_ENV = "PFLANZER_HUB_AUTH_MODE"
AUTH_MODE_DEV = "dev"
AUTH_MODE_OIDC = "oidc"
DEV_ANONYMOUS_ACTOR = "anonymous@web-hub"
MISSING_IDENTITY_DETAIL = (
    "identity header missing — hub must run behind oauth2-proxy "
    "(see tool/web/README-auth.md)"
)


def get_session() -> Iterator[Session]:
    with Session(ENGINE) as session:
        yield session


def get_auth_mode() -> str:
    """Return the configured auth mode. Anything other than 'dev' fails closed to 'oidc'."""
    mode = os.environ.get(AUTH_MODE_ENV, AUTH_MODE_OIDC).strip().lower()
    return AUTH_MODE_DEV if mode == AUTH_MODE_DEV else AUTH_MODE_OIDC


def get_actor(request: Request) -> str:
    """Resolve the auditable actor (feedback.submitted_by, audit_log.actor).

    Order: X-Forwarded-Email (oauth2-proxy) -> X-Forwarded-User -> X-User (dev mode only).
    In oidc mode a request without an SSO identity is rejected with 401.
    nginx (pflanzer.oidc.conf) overwrites these headers from the auth_request
    response, so clients cannot spoof them as long as the backend is reachable
    only through nginx.
    """
    for header in ("X-Forwarded-Email", "X-Forwarded-User"):
        value = request.headers.get(header, "").strip()
        if value:
            return value
    if get_auth_mode() == AUTH_MODE_DEV:
        return request.headers.get("X-User", "").strip() or DEV_ANONYMOUS_ACTOR
    raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if get_auth_mode() == AUTH_MODE_DEV:
        log.warning(
            "%s=dev: trusting client-supplied X-User header — never use in production",
            AUTH_MODE_ENV,
        )
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

# Every data endpoint requires an identity (reads included: feedback rationale is
# internal). /api/health, /api and /api/docs stay open.
REQUIRE_ACTOR = [Depends(get_actor)]
app.include_router(projects_router.router, dependencies=REQUIRE_ACTOR)
app.include_router(variants_router.router, dependencies=REQUIRE_ACTOR)
app.include_router(feedback_router.router, dependencies=REQUIRE_ACTOR)

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
