"""Web hub auth (audit N12): oidc fails closed, dev mode trusts X-User."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")
pytest.importorskip("httpx")

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from tool.web.backend import main as hub  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def mem_session() -> Iterator[Session]:
        with Session(engine) as s:
            yield s

    saved = dict(hub.app.dependency_overrides)
    hub.app.dependency_overrides[hub.get_session] = mem_session
    for router in (hub.projects_router, hub.variants_router, hub.feedback_router):
        hub.app.dependency_overrides[router.get_session] = mem_session
    try:
        yield TestClient(hub.app)
    finally:
        hub.app.dependency_overrides.clear()
        hub.app.dependency_overrides.update(saved)


@pytest.fixture
def probe() -> TestClient:
    app = FastAPI()

    @app.get("/whoami")
    def whoami(actor: str = Depends(hub.get_actor)) -> dict[str, Any]:
        return {"actor": actor}

    return TestClient(app)


@pytest.mark.parametrize("mode", [None, "oidc", "OIDC", "garbage"])
def test_oidc_mode_requires_identity(client: TestClient, monkeypatch: pytest.MonkeyPatch,
                                     mode: str | None) -> None:
    if mode is None:
        monkeypatch.delenv(hub.AUTH_MODE_ENV, raising=False)
    else:
        monkeypatch.setenv(hub.AUTH_MODE_ENV, mode)
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/projects", headers={"X-User": "spoof@x"}).status_code == 401
    r = client.get("/api/projects", headers={"X-Forwarded-Email": "anna@corp.example"})
    assert r.status_code != 401
    assert r.status_code == 200


def test_oidc_actor_precedence(probe: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "oidc")
    r = probe.get("/whoami", headers={"X-Forwarded-Email": "anna@corp.example",
                                      "X-Forwarded-User": "u1", "X-User": "spoof@x"})
    assert r.json() == {"actor": "anna@corp.example"}
    assert probe.get("/whoami", headers={"X-Forwarded-User": "u1"}).json() == {"actor": "u1"}
    assert probe.get("/whoami", headers={"X-User": "spoof@x"}).status_code == 401


def test_dev_mode_accepts_x_user(client: TestClient, probe: TestClient,
                                 monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "dev")
    assert probe.get("/whoami", headers={"X-User": "dev@local"}).json() == {"actor": "dev@local"}
    assert probe.get("/whoami").json() == {"actor": hub.DEV_ANONYMOUS_ACTOR}
    assert client.get("/api/projects", headers={"X-User": "dev@local"}).status_code == 200
