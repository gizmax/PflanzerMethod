"""Hub (pilot 20): kdo chybí, okna k podpisu, tiché hlasování, kosmetika hubu."""
from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from tool.cli import hub as hub_cli  # noqa: E402
from tool.web.backend import main as hub  # noqa: E402
from tool.web.backend.models import Feedback, Project, Triage, Variant  # noqa: E402
from tool.web.backend.models import Session as PSession  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tool" / "web" / "frontend" / "src"

OWNERS = {"byznys": "Tereza Dvořák", "produkt": "Jana Nováková", "design": "AI",
          "vyvoj": "Karel Kuba", "bezpecnost": "AI", "provoz": "Petr Provozní"}
SIGNERS = {"bezpecnost": "Pavel Šnek", "design": "Jana Nováková"}


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict]:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "dev")
    monkeypatch.delenv(hub.PASSWORD_ENV, raising=False)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with engine.begin() as c:
        c.execute(text("ALTER TABLE projects ADD COLUMN path_owners_json TEXT"))
        c.execute(text("ALTER TABLE projects ADD COLUMN ai_signers_json TEXT"))
    with Session(engine) as s:
        p = Project(slug="demo", name="Demo", status="session_1", decider_name="Tereza Dvořák")
        s.add(p)
        s.commit()
        s.refresh(p)
        s.execute(text("UPDATE projects SET path_owners_json=:o, ai_signers_json=:g WHERE id=:i"),
                  {"o": json.dumps(OWNERS), "g": json.dumps(SIGNERS), "i": p.id})
        sess = PSession(project_id=p.id, type=1)
        s.add(sess)
        s.commit()
        s.refresh(sess)
        v = Variant(session_id=sess.id, name="A", builder="x", prototype_url="http://x")
        s.add(v)
        s.commit()
        s.refresh(v)
        ids = {"project": p.id, "variant": v.id}

    def mem_session() -> Iterator[Session]:
        with Session(engine) as s:
            yield s

    saved = dict(hub.app.dependency_overrides)
    for router in (hub.projects_router, hub.variants_router, hub.feedback_router,
                   hub.expert_router):
        hub.app.dependency_overrides[router.get_session] = mem_session
    hub.app.dependency_overrides[hub.get_session] = mem_session
    try:
        yield {"client": TestClient(hub.app), "engine": engine, **ids}
    finally:
        hub.app.dependency_overrides.clear()
        hub.app.dependency_overrides.update(saved)


def who(name: str) -> dict[str, str]:
    from urllib.parse import quote
    return {"X-User": quote(name)}


def test_missing_lists_people_without_feedback(env: dict) -> None:
    c = env["client"]
    r = c.get("/api/projects/demo/missing", headers=who("Jana Nováková")).json()
    names = {m["name"] for m in r["missing"]}
    assert r["collecting"] is True
    # Decider se nepočítá; AI kroky řeší jejich podepisující (Pavel Šnek, Jana)
    assert names == {"Jana Nováková", "Karel Kuba", "Petr Provozní", "Pavel Šnek"}
    jana = next(m for m in r["missing"] if m["name"] == "Jana Nováková")
    assert set(jana["labels"]) == {"Produkt", "Design"}
    assert r["text"].startswith("Chybí: ") and "Petr (Provoz)" in r["text"]
    with Session(env["engine"]) as s:
        s.add(Feedback(variant_id=env["variant"], severity="low", department="Provoz",
                       category="general", score=0.7, rationale="x",
                       submitted_by="Petr Provozní"))
        s.commit()
    r = c.get("/api/projects/demo/missing", headers=who("Jana Nováková")).json()
    assert "Petr Provozní" not in {m["name"] for m in r["missing"]}


def test_missing_matches_sso_identity_and_hides_outside_collecting(env: dict) -> None:
    with Session(env["engine"]) as s:
        s.add(Feedback(variant_id=env["variant"], severity="low", department="Vývoj",
                       category="general", score=0.7, rationale="x",
                       submitted_by="karel.kuba@firma.cz"))
        s.commit()
    r = env["client"].get("/api/projects/demo/missing", headers=who("x")).json()
    assert "Karel Kuba" not in {m["name"] for m in r["missing"]}
    with Session(env["engine"]) as s:
        s.execute(text("UPDATE projects SET status='session_2'"))
        s.commit()
    r = env["client"].get("/api/projects/demo/missing", headers=who("x")).json()
    assert r == {"collecting": False, "missing": [], "text": None}


def test_windows_have_signer_and_ready_command(env: dict) -> None:
    c = env["client"]
    ws = {w["window"]: w for w in c.get("/api/projects/demo/windows",
                                         headers=who("x")).json()["windows"]}
    assert set(ws) == {"zadani", "bezpecnost", "provoz", "design"}
    assert ws["bezpecnost"]["signer"] == "Pavel Šnek"
    assert ws["bezpecnost"]["command"] == (
        'pflanzer checkpoint --slug demo bezpecnost --by "Pavel Šnek" --note "co jsem ověřil"')
    assert ws["provoz"]["signer"] == "Petr Provozní"
    with Session(env["engine"]) as s:
        s.add(Triage(project_id=env["project"], track="platform", status="ok",
                     artefact_md="x", signed_by="Petr Provozní"))
        s.commit()
    ws = {w["window"] for w in c.get("/api/projects/demo/windows",
                                      headers=who("x")).json()["windows"]}
    assert "provoz" not in ws


def vote(c: TestClient, who_: str, choice: str, **kw: object):
    return c.post("/api/projects/demo/votes", headers=who(who_),
                  json={"choice": choice, "comment": "proč", **kw})


def test_silent_vote_hides_until_everyone_voted(env: dict) -> None:
    c = env["client"]
    st = c.get("/api/projects/demo/votes", headers=who("Karel Kuba")).json()
    assert st["revealed"] is False and st["can_vote"] is True and st["tally"] is None
    assert vote(c, "Karel Kuba", "go").status_code == 422          # Go chce vítěze
    assert vote(c, "Karel Kuba", "go", winner="A").status_code == 201
    # ostatní hlas nevidí, vlastní ano
    other = c.get("/api/projects/demo/votes", headers=who("Jana Nováková")).json()
    assert other["votes"] == [] and other["revealed"] is False
    mine = c.get("/api/projects/demo/votes", headers=who("Karel Kuba")).json()
    assert [v["voter"] for v in mine["votes"]] == ["Karel Kuba"]
    # Decider nemůže hlasovat před odkrytím a hlas se nesmí prozradit
    assert vote(c, "Tereza Dvořák", "kill").status_code == 409
    # odkrýt smí jen Decider
    rv = "/api/projects/demo/votes/reveal"
    assert c.post(rv, headers=who("Karel Kuba")).status_code == 403
    st = c.post(rv, headers=who("Tereza Dvořák")).json()
    assert st["revealed"] is True and st["tally"]["go"] == 1
    # po odkrytí už ostatní nehlasují, Decider ano a jeho hlas určí příkaz
    assert vote(c, "Petr Provozní", "kill").status_code == 409
    assert vote(c, "Tereza Dvořák", "iterate").status_code == 201
    st = c.get("/api/projects/demo/votes", headers=who("Petr Provozní")).json()
    assert st["decider_voted"] is True and len(st["votes"]) == 2
    assert st["command"] == 'pflanzer decide --slug demo iterate --rationale "proč"'


def test_silent_vote_auto_reveals_when_all_voted(env: dict) -> None:
    c = env["client"]
    for name in ("Jana Nováková", "Karel Kuba", "Petr Provozní", "Pavel Šnek"):
        assert vote(c, name, "go", winner="A").status_code == 201
    st = c.get("/api/projects/demo/votes", headers=who("Karel Kuba")).json()
    assert st["revealed"] is True and st["tally"] == {"go": 4, "iterate": 0, "kill": 0}
    assert st["command"] == 'pflanzer decide --slug demo go --winner A --rationale "proč"'
    assert vote(c, "Tereza Dvořák", "go", winner="A").status_code == 201


def test_vote_changes_replace_and_closed_after_decision(env: dict) -> None:
    c = env["client"]
    vote(c, "Karel Kuba", "kill")
    vote(c, "Karel Kuba", "iterate")
    st = c.get("/api/projects/demo/votes", headers=who("Karel Kuba")).json()
    assert [v["choice"] for v in st["votes"]] == ["iterate"]
    with Session(env["engine"]) as s:
        s.execute(text("UPDATE projects SET status='handoff'"))
        s.commit()
    assert vote(c, "Karel Kuba", "go", winner="A").status_code == 409
    assert c.get("/api/projects/demo/votes", headers=who("x")).json()["enabled"] is False


def test_votes_table_in_schema_and_migration() -> None:
    schema = (REPO / "tool" / "db" / "schema.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS decision_votes" in schema
    from tool.db import migrate
    assert "decision_votes" in migrate.ADDITIVE_TABLES


def test_hub_tunnel_off_is_alias_and_url_always_flushed(monkeypatch: pytest.MonkeyPatch,
                                                         capsys: pytest.CaptureFixture) -> None:
    called: dict[str, str] = {}

    def fake_resolve(mode: str) -> bool:
        called["mode"] = mode
        raise ValueError("stop")

    monkeypatch.setattr(hub_cli, "resolve_tunnel", fake_resolve)
    monkeypatch.setattr(sys, "argv", ["pflanzer hub", "--tunnel", "off", "--port", "18999"])
    with pytest.raises(SystemExit):
        hub_cli.main()
    assert called["mode"] == "none"
    assert capsys.readouterr().err.strip() == "stop"
    src = (REPO / "tool" / "cli" / "hub.py").read_text(encoding="utf-8")
    assert "line_buffering=True" in src and "flush=True" in src


def test_frontend_texts() -> None:
    page = (SRC / "pages" / "ProjectPage.tsx").read_text(encoding="utf-8")
    assert "Pro Decidera a facilitátora" in page and "catalog_idx" not in page
    assert "SignWindows" in page and "SilentVote" in page and "MissingBanner" in page
    assert (SRC / "components" / "CopyButton.tsx").read_text(encoding="utf-8").count(
        "Zkopírovat příkaz") == 1
    form = (SRC / "pages" / "FeedbackForm.tsx").read_text(encoding="utf-8")
    assert form.index("Další podrobnosti") < form.index("Právní nebo etická oblast")
    assert form.index("Další podrobnosti") < form.index("Úroveň přístupnosti")
    cmp = (SRC / "pages" / "CompareVariants.tsx").read_text(encoding="utf-8")
    assert "!(desktop && protectedPreview)" in cmp


def test_task_does_not_tell_pm_to_tell_himself() -> None:
    task = (SRC / "lib" / "task.ts").read_text(encoding="utf-8")
    assert "iAmPm" in task and "sameName(identity.name, detail.pm_name)" in task


def test_windows_endpoint_shows_merged_window(env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pilot bez osobních dat: hub ukáže jedno okno Bezpečnost a provoz (jako CLI)."""
    from tool.web.backend.api import expert
    monkeypatch.setattr(expert, "_merged_window", lambda db, pid: True)
    ws = {w["window"]: w for w in env["client"].get(
        "/api/projects/demo/windows", headers=who("x")).json()["windows"]}
    assert set(ws) == {"zadani", "bezpecnost-provoz", "design"}
    assert ws["bezpecnost-provoz"]["label"] == "Bezpečnost a provoz"
    assert ws["bezpecnost-provoz"]["command"].startswith(
        'pflanzer checkpoint --slug demo bezpecnost-provoz --by "Pavel Šnek"')
