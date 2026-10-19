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


# --- UX: dev auto-mode, sdílené heslo, odvozené score ---------------------------------

from tool.cli import hub as hub_cli  # noqa: E402
from tool.web.backend.models import Project, Variant  # noqa: E402
from tool.web.backend.models import Session as PSession  # noqa: E402


def test_plan_auth_localhost_defaults_to_dev() -> None:
    env, notes = hub_cli.plan_auth("127.0.0.1", None, {})
    assert env == {"PFLANZER_HUB_AUTH_MODE": "dev"}
    assert notes == []


def test_plan_auth_public_host_generates_password() -> None:
    env, notes = hub_cli.plan_auth("0.0.0.0", None, {})
    assert env["PFLANZER_HUB_AUTH_MODE"] == "dev"
    assert len(env["PFLANZER_HUB_PASSWORD"]) >= 8
    assert any("POZOR" in n for n in notes)
    assert any(env["PFLANZER_HUB_PASSWORD"] in n for n in notes)


def test_plan_auth_explicit_password_and_oidc_untouched() -> None:
    env, _ = hub_cli.plan_auth("0.0.0.0", "tajne", {})
    assert env["PFLANZER_HUB_PASSWORD"] == "tajne"
    assert hub_cli.plan_auth("0.0.0.0", None, {"PFLANZER_HUB_AUTH_MODE": "oidc"}) == ({}, [])


def test_shared_password_basic_auth(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "dev")
    monkeypatch.setenv(hub.PASSWORD_ENV, "tajne")
    assert client.get("/api/health").status_code == 200
    r = client.get("/api/projects")
    assert r.status_code == 401 and "Basic" in r.headers["www-authenticate"]
    assert client.get("/api/projects", auth=("x", "spatne")).status_code == 401
    assert client.get("/api/projects", auth=("x", "tajne")).status_code == 200


def _seed_variant(client: TestClient) -> int:
    override = hub.app.dependency_overrides[hub.get_session]
    s = next(override())
    p = Project(slug="demo", name="Demo")
    s.add(p)
    s.commit()
    s.refresh(p)
    ps = PSession(project_id=p.id, type=1)
    s.add(ps)
    s.commit()
    s.refresh(ps)
    v = Variant(session_id=ps.id, name="A", builder="claude-code", prototype_url="")
    s.add(v)
    s.commit()
    s.refresh(v)
    return v.id


@pytest.mark.parametrize(("severity", "score"),
                         [("critical", 0.1), ("high", 0.3), ("medium", 0.5), ("low", 0.7)])
def test_feedback_score_derived_from_severity(client: TestClient, monkeypatch: pytest.MonkeyPatch,
                                              severity: str, score: float) -> None:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "dev")
    vid = _seed_variant(client)
    r = client.post("/api/feedback", headers={"X-User": "Eva%20Hor%C3%A1kov%C3%A1"},
                    json={"variant_id": vid, "severity": severity,
                          "department": "Bezpečnost & právo", "rationale": "x"})
    assert r.status_code == 201
    body = r.json()
    assert body["score"] == score and body["category"] == "general"
    assert body["submitted_by"] == "Eva Horáková"  # X-User je percent-encoded
    # explicitní score se respektuje
    r = client.post("/api/feedback", json={"variant_id": vid, "severity": "low", "score": 0.9,
                                           "department": "d", "rationale": "x"})
    assert r.json()["score"] == 0.9


def test_variants_feedback_counts_and_project_extras(client: TestClient,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "dev")
    vid = _seed_variant(client)
    client.post("/api/feedback", headers={"X-User": "eva"},
                json={"variant_id": vid, "severity": "low", "department": "d", "rationale": "x"})
    mine = client.get("/api/projects/demo/variants", headers={"X-User": "eva"}).json()[0]
    other = client.get("/api/projects/demo/variants", headers={"X-User": "jan"}).json()[0]
    assert (mine["feedback_count"], mine["my_feedback"], other["my_feedback"]) == (1, True, False)
    detail = client.get("/api/projects/demo").json()
    assert detail["path_owners"] == {}
    assert detail["shortlist"] == []
    assert detail["async_deadline"] is None
