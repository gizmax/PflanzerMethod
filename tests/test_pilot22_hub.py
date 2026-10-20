"""Hub (pilot 22): skloňování jmen, úloha podle role, potvrzení hlasu, Iterate s variantami."""
from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from tool.web.backend import main as hub  # noqa: E402
from tool.web.backend.models import Project, Variant  # noqa: E402
from tool.web.backend.models import Session as PSession  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tool" / "web" / "frontend" / "src"

VOCATIVE = {"Petr": "Petře", "Jana": "Jano", "Tomáš": "Tomáši", "Karel": "Karle", "Eva": "Evo",
            "Pavel": "Pavle", "Marek": "Marku", "Lucie": "Lucie", "Jiří": "Jiří", "Petra": "Petro"}
DATIVE = {"Petr": "Petrovi", "Jana": "Janě", "Tomáš": "Tomášovi", "Karel": "Karlovi", "Eva": "Evě",
          "Pavel": "Pavlovi", "Marek": "Markovi", "Lucie": "Lucii", "Petra": "Petře",
          "Lenka": "Lence", "Honza": "Honzovi"}


def test_czech_declension_pure_function() -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node není k dispozici")
    script = (
        "import {vocative, dative, vocativeName} from '"
        + (SRC / "lib" / "czech.ts").as_posix() + "';"
        "const v=" + json.dumps(VOCATIVE, ensure_ascii=False) + ";"
        "const d=" + json.dumps(DATIVE, ensure_ascii=False) + ";"
        "const out={v:{},d:{},unk:[vocative('Xyz'),dative('Xo'),vocativeName('')]};"
        "for(const k in v) out.v[k]=vocative(k+' Novák');"
        "for(const k in d) out.d[k]=dative(k+' Novák');"
        "console.log(JSON.stringify(out));"
    )
    r = subprocess.run([node, "--experimental-strip-types", "--no-warnings", "--input-type=module",
                        "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip(f"node nezvládl TS: {r.stderr[:200]}")
    out = json.loads(r.stdout)
    assert out["v"] == VOCATIVE
    assert out["d"] == DATIVE
    assert out["unk"][1] is None and out["unk"][2] is None


def test_task_source_uses_role_specific_lead_and_neutral_fallback() -> None:
    task = (SRC / "lib" / "task.ts").read_text(encoding="utf-8")
    assert "z pohledu ${view}" in task and '"designu"' in task
    assert "Dejte vědět: ${detail.pm_name}" in task
    # builder zůstává u „sbírejte a opravujte“, Design už ne
    core = task.split('case "core":')[1]
    assert "Sbírejte feedback a opravujte." in core.split("default:")[0]
    assert 'k === "design" || k === "produkt"' in task


def test_silent_vote_component_confirms_and_offers_iterate_variants() -> None:
    src = (SRC / "components" / "SilentVote.tsx").read_text(encoding="utf-8")
    assert "Váš hlas je uložený:" in src and "Ostatní ho uvidí po odkrytí" in src
    assert "iterate_variants" in src and 'type="checkbox"' in src


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
    owners = {"byznys": "Tereza Dvořák", "produkt": "Jana Nováková", "design": "Karel Kuba",
              "vyvoj": "Petr Provozní", "bezpecnost": "Pavel Šnek", "provoz": "Eva Provozní"}
    with Session(engine) as s:
        p = Project(slug="demo", name="Demo", status="session_1", decider_name="Tereza Dvořák")
        s.add(p)
        s.commit()
        s.refresh(p)
        s.execute(text("UPDATE projects SET path_owners_json=:o WHERE id=:i"),
                  {"o": json.dumps(owners), "i": p.id})
        sess = PSession(project_id=p.id, type=1)
        s.add(sess)
        s.commit()
        s.refresh(sess)
        s.add(Variant(session_id=sess.id, name="A", builder="x", prototype_url="http://x"))
        s.commit()

    def mem_session() -> Iterator[Session]:
        with Session(engine) as s:
            yield s

    saved = dict(hub.app.dependency_overrides)
    for router in (hub.projects_router, hub.variants_router, hub.feedback_router,
                   hub.expert_router):
        hub.app.dependency_overrides[router.get_session] = mem_session
    hub.app.dependency_overrides[hub.get_session] = mem_session
    try:
        yield {"client": TestClient(hub.app), "engine": engine}
    finally:
        hub.app.dependency_overrides.clear()
        hub.app.dependency_overrides.update(saved)


def who(name: str) -> dict[str, str]:
    return {"X-User": quote(name)}


def test_iterate_vote_stores_variants_and_command_includes_them(env: dict) -> None:
    c = env["client"]
    url = "/api/projects/demo/votes"
    r = c.post(url, headers=who("Karel Kuba"),
               json={"choice": "iterate", "iterate_variants": ["A", "B", "A"], "comment": "ladit"})
    assert r.status_code == 201
    assert r.json()["mine"]["iterate_variants"] == ["A", "B"]
    # zpětná kompatibilita: hlas bez pole funguje, Go varianty ignoruje
    go = {"choice": "go", "winner": "A", "iterate_variants": ["B"]}
    assert c.post(url, headers=who("Petr Provozní"), json=go).status_code == 201
    assert c.post(url + "/reveal", headers=who("Tereza Dvořák")).status_code == 200
    assert c.post(url, headers=who("Tereza Dvořák"),
                  json={"choice": "iterate", "iterate_variants": ["A", "C"],
                        "comment": "dolaďte"}).status_code == 201
    st = c.get(url, headers=who("Karel Kuba")).json()
    assert st["command"] == ('pflanzer decide --slug demo iterate --variants A,C '
                             '--rationale "dolaďte"')
    by = {v["voter"]: v for v in st["votes"]}
    assert by["Petr Provozní"]["iterate_variants"] == []


def test_iterate_variants_column_in_schema_and_migration() -> None:
    assert "iterate_variants TEXT" in (REPO / "tool" / "db" / "schema.sql").read_text("utf-8")
    assert '"iterate_variants"' in (REPO / "tool" / "db" / "migrate.py").read_text("utf-8")
