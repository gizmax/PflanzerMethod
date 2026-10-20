"""Pilot 16 (Úsměv, production + AI náhrada bezpečnosti), část B: podmínky z podpisů oken,
kdo skutečně podepisuje v hubu, hub po Go, Go pod prahem commitmentu, kosmetika."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import checkpoint, feedback, handoff, handoff_pr, session_2, status, ux
from tool.cli._compat import conditions_checklist
from tool.cli.db import transaction
from tool.cli.quick_session import record_voting

REPO = Path(__file__).resolve().parents[1]


def _vote(slug: str, commitment: int = 2, description: str = "Varianta A") -> None:
    pref = {"role_idx": 1, "user_value": 0.9, "effort": 0.4, "risk": 0.2,
            "strategic_fit": 0.7, "commitment_level": commitment, "rationale": "A je nejrychlejší"}
    record_voting(
        slug=slug, facilitator="Fanda",
        decider_call={"shortlist": ["A"], "rationale": "A"},
        votes=[{"name": "A", "builder": "claude-code", "description": description,
                "role_preferences": [pref]}])


# --- 4. podmínky z podpisů oken -------------------------------------------------------------


def test_parse_conditions_semicolon_repeat_and_dedup() -> None:
    assert checkpoint.parse_conditions(["CSRF; rate limit", "DPA", "CSRF"]) == [
        "CSRF", "rate limit", "DPA"]
    assert checkpoint.parse_conditions("- čl. 13\nretence") == ["čl. 13", "retence"]
    assert checkpoint.parse_conditions(None) == []


def test_conditions_stored_survive_resign_and_block(tmp_db: Path, bare_repo: Path) -> None:
    slug = "usmev"
    bootstrap_project(slug=slug, target_repo_url=file_url(bare_repo))
    out = checkpoint.sign(slug, "bezpecnost", by="Lucie", note="OK s podmínkami",
                          conditions=["CSRF; rate limit", "DPA"])
    assert out["conditions"] == ["CSRF", "rate limit", "DPA"]
    row = next(r for r in checkpoint.checkpoint_summary(slug) if r["window"] == "bezpecnost")
    assert row["conditions"] == ["CSRF", "rate limit", "DPA"]
    # podpis bez --conditions je nemaže, zablokovaný zápis je nemění
    checkpoint.sign(slug, "bezpecnost", by="Lucie", note="znovu")
    checkpoint.sign(slug, "bezpecnost", by="Lucie", note="veto", blocked=True,
                    conditions=["jiné"])
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        assert checkpoint.conditions_by_window(conn, pid)["bezpecnost"] == [
            "CSRF", "rate limit", "DPA"]
    checkpoint.sign(slug, "bezpecnost", by="Lucie", note="odblokováno")
    assert [c["text"] for c in checkpoint.signature_conditions(slug)] == [
        "CSRF", "rate limit", "DPA"]
    assert conditions_checklist(slug)[0] == "- [ ] CSRF (Bezpečnost, Lucie)"


def test_checkpoint_cli_has_conditions_flag(tmp_db: Path, bare_repo: Path,
                                            monkeypatch: pytest.MonkeyPatch,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    bootstrap_project(slug="cli", target_repo_url=file_url(bare_repo))
    monkeypatch.setattr(sys, "argv", [
        "checkpoint", "--slug", "cli", "bezpecnost", "--by", "Lucie", "--note", "ok",
        "--conditions", "CSRF; rate limit", "--conditions", "DPA"])
    checkpoint.main()
    assert "Podmínky podpisu (3)" in capsys.readouterr().out


def test_conditions_in_pr_body_ship_md_and_compliance(
        worktree_project: dict[str, Any]) -> None:
    slug = worktree_project["slug"]
    checkpoint.sign(slug, "bezpecnost", by="Lucie", note="OK s podmínkami",
                    conditions="CSRF; rate limit; čl. 13")
    _vote(slug)
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    pr = handoff_pr.build_pr(slug)
    assert "## Podmínky z podpisů oken" in pr["body"]
    assert "- [ ] CSRF (Bezpečnost, Lucie)" in pr["body"]
    assert "- [ ] čl. 13 (Bezpečnost, Lucie)" in pr["body"]
    md = handoff_pr.render_ship_md(slug)
    assert "3 podmínky z podpisů oken musí splnit PR" in md
    assert "- [ ] rate limit (Bezpečnost, Lucie)" in md
    p = (1, "Úsměv", slug, "handoff", "h", "h", "Dana", None, "minimal", "L3",
         "evolve", None, None, "m", "l", "g", "k", None, None)
    comp = handoff.render_compliance({
        "project_tuple": p, "triage": [], "decisions": [], "risk_profile": "production",
        "path_owners": {}})
    assert "Podmínky z podpisů oken" in comp and "- [ ] CSRF (Bezpečnost, Lucie)" in comp


# --- 7. Go pod prahem commitmentu -----------------------------------------------------------


def test_go_below_commitment_needs_force_with_reason(tmp_db: Path, bare_repo: Path) -> None:
    slug = "nizky"
    bootstrap_project(slug=slug, target_repo_url=file_url(bare_repo))
    _vote(slug, commitment=1)                       # 1/3 = 33 %
    with pytest.raises(ValueError, match=r"33 %|33%") as exc:
        session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    assert "60" in str(exc.value) and "--force" in str(exc.value)
    out = session_2.record_decision(slug=slug, decision="go", winner="A", force=True,
                                    rationale="Zákazník čeká, rizika znám")
    assert out["below_commitment"] == pytest.approx(0.333, abs=0.001)
    with transaction() as conn:
        body = conn.execute("SELECT body_md FROM decisions WHERE type = 'handoff' "
                            "ORDER BY id DESC LIMIT 1").fetchone()[0]
    assert "Go pod prahem commitmentu" in body and "Zákazník čeká" in body


def test_go_at_or_above_threshold_does_not_need_force(tmp_db: Path, bare_repo: Path) -> None:
    slug = "ok"
    bootstrap_project(slug=slug, target_repo_url=file_url(bare_repo))
    _vote(slug, commitment=2)                       # 67 %
    out = session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    assert out["below_commitment"] is None


# --- kosmetika ------------------------------------------------------------------------------


def test_pr_title_cut_at_word_boundary_with_ellipsis(worktree_project: dict[str, Any]) -> None:
    slug = worktree_project["slug"]
    _vote(slug, description="Rezervace kola na den s kontrolou dostupnosti a upozorněním "
                            "zákazníka na změnu termínu vyzvednutí")
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    title = handoff_pr.build_pr(slug)["title"]
    assert title.endswith("…")
    body = title.split(": ", 1)[1].rstrip("…")
    assert body.split()[-1] in "Rezervace kola na den s kontrolou dostupnosti a upozorněním "\
        "zákazníka na změnu termínu vyzvednutí".split()


def test_feedback_add_by_overrides_git_author(tmp_db: Path, bare_repo: Path,
                                              monkeypatch: pytest.MonkeyPatch,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    slug = "fb"
    bootstrap_project(slug=slug, target_repo_url=file_url(bare_repo))
    _vote(slug)
    base = ["feedback", "add", "--slug", slug, "--variant", "A", "--role", "Bezpečnost",
            "--severity", "major", "--text", "chybí CSRF"]
    monkeypatch.setattr(sys, "argv", [*base, "--by", "Lucie"])
    feedback.main()
    out = capsys.readouterr().out
    assert "autor Lucie" in out and "git user" not in out
    monkeypatch.setattr(sys, "argv", base)
    feedback.main()
    assert "Autor je git user" in capsys.readouterr().out
    assert [r["submitted_by"] for r in feedback.list_feedback(slug)][0] == "Lucie"


def test_security_tip_disappears_after_signature(tmp_db: Path, bare_repo: Path) -> None:
    slug = "tip"
    bootstrap_project(slug=slug, target_repo_url=file_url(bare_repo))
    assert any("3 vět" in t for t in ux.tips_for("checkpoint_bezpecnost", {}, limit=5))
    assert not any("3 vět" in t for t in ux.tips_for(
        "checkpoint_bezpecnost", {"security_signed": True}, limit=5))
    checkpoint.sign(slug, "bezpecnost", by="Lucie", note="ok")
    for phase in ("build", "checkpoint_bezpecnost"):
        assert not any("3 vět" in t for t in ux.tips_for_project(slug, phase, limit=5))


def test_status_after_go_with_open_critical_points_to_resolve(
        worktree_project: dict[str, Any]) -> None:
    slug = worktree_project["slug"]
    _vote(slug)
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    res = feedback.add_feedback(slug=slug, variant="A", role="Bezpečnost", severity="critical",
                                text="chybí CSRF", author="Lucie")
    d = status.project_detail(slug)
    crit = next(b for b in d["blockers"] if b["kind"] == "critical")
    assert crit["command"].startswith("pflanzer session_2 resolve")
    assert f"--feedback-id {res['id']}" in crit["command"]
    assert "/pm feedback" not in crit["command"]


def test_feedback_example_is_generic() -> None:
    text = (REPO / "tool/web/frontend/src/lib/task.ts").read_text(encoding="utf-8")
    assert "e-mail zákazníka" not in text and "Objednat" not in text


# --- 2 + 6. hub -----------------------------------------------------------------------------

try:
    import json

    from fastapi.testclient import TestClient
    from sqlalchemy.pool import StaticPool
    from sqlmodel import Session, SQLModel, create_engine

    from tool.web.backend import main as hub
    from tool.web.backend.api.projects import step_confirmers
    from tool.web.backend.audit import write_audit
    from tool.web.backend.models import Project, Variant
    from tool.web.backend.models import Session as PSession
    HAVE_HUB = True
except ImportError:      # fastapi / sqlmodel nejsou v prostředí: testy hubu se přeskočí
    HAVE_HUB = False

web = pytest.mark.skipif(not HAVE_HUB, reason="fastapi / sqlmodel nejsou nainstalované")

OWNERS = {"byznys": "Dana Nováková", "produkt": "Petra Svobodová", "design": "AI:ux-expert",
          "vyvoj": "Tomáš Dvořák", "bezpecnost": "AI:security-expert", "provoz": "Karel Malý"}


@web
def test_step_confirmers_prefers_ai_signers_then_decider() -> None:
    got = step_confirmers(OWNERS, {"bezpecnost": "Lucie Králová"}, "Dana Nováková", "production")
    assert got["bezpecnost"] == "Lucie Králová"          # ne PdM
    assert got["design"] == "Petra Svobodová"            # design potvrzuje PdM
    assert "provoz" not in got                           # člověk, ne AI
    # bez ai_signers: Decider (stejně jako checkpoint._signer_for)
    assert step_confirmers(OWNERS, {}, "Dana Nováková", "pilot")["bezpecnost"] == "Dana Nováková"
    # production: autor kódu AI náhradu nepotvrzuje
    assert step_confirmers(OWNERS, {"bezpecnost": "Tomáš Dvořák"}, "Dana Nováková",
                           "production")["bezpecnost"] == "Dana Nováková"


@pytest.fixture
def client() -> Any:
    if not HAVE_HUB:
        pytest.skip("fastapi / sqlmodel nejsou nainstalované")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def mem_session() -> Any:
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


def _seed(client: Any, *, status_: str, winner: str | None) -> dict[str, int]:
    s = next(hub.app.dependency_overrides[hub.get_session]())
    for col in ("path_owners_json", "ai_signers_json"):
        s.connection().exec_driver_sql(f"ALTER TABLE projects ADD COLUMN {col} TEXT")
    p = Project(slug="usmev", name="Úsměv", status=status_, decider_name="Dana Nováková")
    s.add(p)
    s.commit()
    s.refresh(p)
    s.connection().exec_driver_sql(
        "UPDATE projects SET path_owners_json = ?, ai_signers_json = ? WHERE id = ?",
        (json.dumps(OWNERS), json.dumps({"bezpecnost": "Lucie Králová"}), p.id))
    ps = PSession(project_id=p.id, type=1)
    s.add(ps)
    s.commit()
    s.refresh(ps)
    ids = {}
    for name in ("A", "B"):
        v = Variant(session_id=ps.id, name=name, builder="claude-code", prototype_url="")
        s.add(v)
        s.commit()
        s.refresh(v)
        ids[name] = v.id
    if winner:
        write_audit(s, actor="cli", action="session_2.decision", target_type="project",
                    target_id=p.id, payload={"decision": "go", "winner": winner,
                                             "decider": "Dana Nováková"})
        s.commit()
    s.commit()
    return ids


@web
def test_hub_detail_reports_real_confirmer_and_signer(
        client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "dev")
    _seed(client, status_="session_1", winner=None)
    d = client.get("/api/projects/usmev", headers={"X-User": "x"}).json()
    assert d["confirmers"]["bezpecnost"] == "Lucie Králová"
    assert d["ai_signers"] == {"bezpecnost": "Lucie Králová"}
    assert d["pm_name"] == "Petra Svobodová"             # PdM zůstává, ale nepotvrzuje bezpečnost


@web
def test_hub_after_go_shows_winner_and_blocks_feedback_on_losers(
        client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "dev")
    ids = _seed(client, status_="handoff", winner="A")
    d = client.get("/api/projects/usmev", headers={"X-User": "x"}).json()
    assert d["decision"]["winner"] == "A" and d["decision"]["decision"] == "go"
    body = {"severity": "low", "department": "d", "rationale": "x"}
    ok = client.post("/api/feedback", json={**body, "variant_id": ids["A"]},
                     headers={"X-User": "x"})
    assert ok.status_code == 201
    lost = client.post("/api/feedback", json={**body, "variant_id": ids["B"]},
                       headers={"X-User": "x"})
    assert lost.status_code == 409 and "vítězí varianta A" in lost.text


@web
def test_hub_cannot_write_decisions_or_signatures() -> None:
    """Hub smí zapisovat jen feedback (a varianty); žádné rozhodnutí ani podpis okna."""
    writes = {(m.upper(), path) for path, ops in hub.app.openapi()["paths"].items()
              for m in ops if m.upper() in ("POST", "PUT", "PATCH", "DELETE")}
    assert writes == {("POST", "/api/feedback"), ("POST", "/api/projects/{slug}/variants")}


def test_identity_note_in_hub_ui() -> None:
    picker = (REPO / "tool/web/frontend/src/components/IdentityPicker.tsx").read_text("utf-8")
    assert "Identita je jen deklarovaná" in picker and "výhradně přes CLI" in picker


# --- tunel (cloudflared): loopback IP není důvěra ---------------------------------------------


def _req(headers: dict[str, str], client: str = "127.0.0.1") -> Any:
    from starlette.requests import Request
    return Request({"type": "http", "client": (client, 1),
                    "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()]})


@web
@pytest.mark.parametrize("headers", [
    {"Cf-Connecting-Ip": "203.0.113.9"}, {"X-Forwarded-For": "203.0.113.9"},
    {"Cf-Ray": "abc"}, {"Forwarded": "for=203.0.113.9"},
    {"Host": "abc.trycloudflare.com"}])
def test_tunnel_requests_are_not_local(headers: dict[str, str]) -> None:
    from tool.web.backend.api.projects import _is_local
    assert _is_local(_req(headers)) is False
    assert _is_local(_req({"Host": "localhost:8000"})) is True


@web
def test_preview_password_hidden_from_tunnel_without_hub_password(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tool.web.backend.api.projects import _preview_login
    (tmp_path / "preview").mkdir()
    (tmp_path / "preview" / "s.json").write_text(json.dumps({"password": "tajne"}))
    monkeypatch.setenv("PFLANZER_DATA", str(tmp_path))
    monkeypatch.delenv("PFLANZER_HUB_PASSWORD", raising=False)
    tunnel = _req({"Cf-Connecting-Ip": "203.0.113.9", "Host": "x.trycloudflare.com"})
    assert _preview_login("s", tunnel)["password"] is None
    assert _preview_login("s", _req({"Host": "127.0.0.1:8000"}))["password"] == "tajne"


@web
def test_hub_password_required_even_from_loopback(
        client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(hub.AUTH_MODE_ENV, "dev")
    monkeypatch.setenv(hub.PASSWORD_ENV, "hubpw")
    # TestClient přichází z loopbacku ("testclient"); heslo se přesto vyžaduje
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/projects", headers={"Cf-Connecting-Ip": "1.2.3.4"}).status_code == 401
    assert client.get("/api/projects", auth=("x", "hubpw")).status_code == 200
