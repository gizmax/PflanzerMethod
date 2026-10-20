"""UX vrstva v0.5: AI náhrada (ADR-0023), počítání lidí, status s blokacemi,
`--spec -`, vote bez preview URL, stack-aware prompty, doctor."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import bootstrap_project, file_url, git, set_status

from tool.cli import checkpoint, doctor, quick_session, status
from tool.cli.db import audit, current_actor, transaction
from tool.cli.triage import ship_triage_gate
from tool.cli.ux import normalize_severity, severity_label

OWNERS = {"byznys": "Dana", "produkt": "Petr", "design": "Eva", "vyvoj": "Tomáš",
          "bezpecnost": "Lucie", "provoz": "Karel"}


def _owners(**over: str) -> dict[str, str]:
    return {**OWNERS, **over}


def _gate(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        return ship_triage_gate(conn, int(pid))


def _run(monkeypatch: pytest.MonkeyPatch, module: Any, *argv: str, stdin: str | None = None) -> int:
    monkeypatch.setattr(sys, "argv", [module.__name__, *argv])
    if stdin is not None:
        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    try:
        module.main()
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


# ---------------------------------------------------------------- AI náhrada


def test_ai_design_allowed_and_stored(tmp_db: Path, bare_repo: Path) -> None:
    out = bootstrap_project(slug="ai-design", target_repo_url=file_url(bare_repo),
                            path_owners=_owners(design="AI:ux-expert"))
    assert [a["step"] for a in out["ai_stand_ins"]] == ["design"]
    assert out["ai_stand_ins"][0]["agent"] == "ux-expert"
    with transaction() as conn:
        raw = conn.execute(
            "SELECT path_owners_json FROM projects WHERE slug='ai-design'").fetchone()[0]
    assert json.loads(raw)["design"] == "AI:ux-expert"


def test_ai_design_production_warns_human_needed(tmp_db: Path, bare_repo: Path) -> None:
    out = bootstrap_project(risk_profile="production", slug="ai-prod",
                            target_repo_url=file_url(bare_repo), path_owners=_owners(design="AI"))
    assert any("potřeba člověk před Ship" in w for w in out["warnings"])


@pytest.mark.parametrize("step,needle", [("byznys", "Byznys"), ("vyvoj", "Vývoj")])
def test_ai_never_covers_business_or_dev(tmp_db: Path, bare_repo: Path,
                                         step: str, needle: str) -> None:
    with pytest.raises(ValueError, match=needle):
        bootstrap_project(slug="ai-no", target_repo_url=file_url(bare_repo),
                          path_owners=_owners(**{step: "AI"}))


def test_ai_product_only_quick_or_throwaway(tmp_db: Path, bare_repo: Path) -> None:
    ok = bootstrap_project(slug="ai-prod-quick", target_repo_url=file_url(bare_repo),
                           tier="quick", path_owners=_owners(produkt="AI"))   # /pm live = Quick
    assert ok["tier"] == "quick"
    with pytest.raises(ValueError, match="Produkt smí zastoupit AI jen"):   # pilot default = Lean
        bootstrap_project(slug="ai-prod-pilot", target_repo_url=file_url(bare_repo),
                          path_owners=_owners(produkt="AI"))
    with pytest.raises(ValueError, match="Produkt smí zastoupit AI jen"):
        bootstrap_project(risk_profile="production", slug="ai-prod-lean",
                          target_repo_url=file_url(bare_repo), path_owners=_owners(produkt="AI"))


def test_missing_step_error_is_human(tmp_db: Path, bare_repo: Path) -> None:
    owners = _owners()
    del owners["design"]
    with pytest.raises(ValueError, match=r"Chybí jméno u kroku Design\. V malém interním nástroji"):
        bootstrap_project(slug="miss", target_repo_url=file_url(bare_repo), path_owners=owners)


def test_checkpoint_ai_pending_for_pilot_then_countersigned(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(personal_data=True, slug="pil", target_repo_url=file_url(bare_repo),
                      metric="10 z 15 lidí do 30 dnů", path_owners=_owners(bezpecnost="AI"))
    res = checkpoint.sign("pil", "bezpecnost", ai=True, agent="security-expert",
                          note="AI pre-check: žádná reálná data")
    assert res["status"] == "pending" and res["ai_draft"]
    assert "AI (security-expert)" in res["signed_by"]
    assert any("security" in b and "pending" in b for b in _gate("pil")["blocked_by"])
    states = {r["window"]: r["state"] for r in checkpoint.list_checkpoints("pil")}
    assert states["bezpecnost"] == "pending"
    # krok bez člověka: určí Decider
    assert "Dana" in res["next_step"] and "--by" in res["next_step"]

    signed = checkpoint.sign("pil", "bezpecnost", by="Lucie", note="přečteno, data jsou syntetická")
    assert signed["status"] == "ok" and signed["countersigned_ai_draft"] is True
    assert not [b for b in _gate("pil")["blocked_by"] if "security" in b or "legal" in b]


def test_checkpoint_ai_throwaway_is_ok(tmp_db: Path) -> None:
    bootstrap_project(risk_profile="throwaway", slug="thr", path_owners=_owners(provoz="AI"))
    res = checkpoint.sign("thr", "provoz", ai=True, note="AI pre-check provozu")
    assert res["status"] == "ok" and not res["ai_draft"]


def test_checkpoint_ai_refused_for_kickoff_window(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="kick", target_repo_url=file_url(bare_repo))
    with pytest.raises(ValueError, match="Decider"):
        checkpoint.sign("kick", "zadani", ai=True, note="x")


def test_checkpoint_stand_in_warning_and_ops_developer(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="zast", target_repo_url=file_url(bare_repo), path_owners=_owners(),
                      personal_data=True)
    res = checkpoint.sign("zast", "bezpecnost", by="Karel", note="ok")
    assert any("Karel není zástupce kroku Bezpečnost & právo (Lucie)" in w and "zástup" in w
               for w in res["warnings"])
    assert checkpoint.sign("zast", "bezpecnost", by="Lucie", note="ok")["warnings"] == []
    # pilot: provoz smí podepsat i vývojář z jádra
    assert checkpoint.sign("zast", "provoz", by="Tomáš", note="rollback + flag")["warnings"] == []


def test_checkpoint_blocked_next_step_names_owner(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="blk", target_repo_url=file_url(bare_repo), path_owners=_owners(),
                      personal_data=True)
    res = checkpoint.sign("blk", "provoz", by="Karel", note="chybí rollback", blocked=True)
    assert res["status"] == "blocked"
    assert 'pflanzer checkpoint --slug blk provoz --by "Karel"' in res["next_step"]


def test_checkpoint_cli_human_and_json(tmp_db: Path, bare_repo: Path,
                                       monkeypatch: pytest.MonkeyPatch,
                                       capsys: pytest.CaptureFixture[str]) -> None:
    bootstrap_project(slug="cli", target_repo_url=file_url(bare_repo), path_owners=_owners())
    rc = _run(monkeypatch, checkpoint, "--slug", "cli", "bezpecnost", "--by", "Lucie",
              "--note", "ok")
    out = capsys.readouterr().out
    assert rc == 0 and "Další krok" in out and not out.lstrip().startswith("{")
    rc = _run(monkeypatch, checkpoint, "--slug", "cli", "provoz", "--ai", "--note", "AI draft",
              "--json")
    data = json.loads(capsys.readouterr().out)
    assert rc == 0 and data["status"] == "pending"
    rc = _run(monkeypatch, checkpoint, "--slug", "cli", "provoz", "--note", "chybí --by")
    assert rc == 2 and "CHYBA" in capsys.readouterr().err


# ---------------------------------------------------------------- lidé, ne role


def test_more_than_five_roles_is_not_more_than_five_people(tmp_db: Path, bare_repo: Path) -> None:
    out = bootstrap_project(slug="lide", target_repo_url=file_url(bare_repo),
                            path_owners=_owners(), core=["Petr", "Tomáš", "Eva"])
    assert out["roles_count"] > 5
    assert not [w for w in out["warnings"] if "naráz" in w or "Jádro" in w]


def test_core_over_five_warns(tmp_db: Path, bare_repo: Path) -> None:
    out = bootstrap_project(slug="jadro", target_repo_url=file_url(bare_repo),
                            path_owners=_owners(),
                            core=["A1", "A2", "A3", "A4", "A5", "A6"])
    assert any(w.startswith("Jádro má 6 lidí") for w in out["warnings"])


def test_window_over_five_names_who_should_come(tmp_db: Path, bare_repo: Path) -> None:
    out = bootstrap_project(slug="okno", target_repo_url=file_url(bare_repo), path_owners=_owners(),
                            core=["Petr", "Tomáš", "Eva", "X1", "X2"])
    msg = next(w for w in out["warnings"] if "V okně Rozhodnutí" in w)
    assert "Dana" in msg and "6 lidí" in msg
    assert not any(w.startswith("Jádro má") for w in out["warnings"])


# ---------------------------------------------------------------- status


def test_status_blocked_checkpoint_has_owner_and_command(tmp_db: Path, bare_repo: Path,
                                                         vote: Callable[..., Any]) -> None:
    bootstrap_project(slug="st", target_repo_url=file_url(bare_repo), path_owners=_owners(),
                      personal_data=True)
    vote("st")
    checkpoint.sign("st", "provoz", by="Karel", note="chybí monitoring", blocked=True)
    d = status.project_detail("st")
    assert "blocked" in [b["kind"] for b in d["blockers"]]
    assert 'pflanzer checkpoint --slug st provoz --by "Karel"' in d["next_step"]
    assert "Karel" in next(b for b in d["blockers"] if b["kind"] == "blocked")["text"]


def test_status_ai_draft_names_signer(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(personal_data=True, slug="aid", target_repo_url=file_url(bare_repo),
                      path_owners=_owners(bezpecnost="AI"))
    checkpoint.sign("aid", "bezpecnost", ai=True, note="AI pre-check")
    d = status.project_detail("aid")
    txt = next(b["text"] for b in d["blockers"] if b["kind"] == "ai_draft")
    # bezpečnost za AI a nikdo není určen -> status řekne, kdo smí podepsat
    assert "Decider (Dana)" in txt and "PdM (Petr)" in txt and "ne autor kódu (Tomáš)" in txt


def test_status_open_critical_variant_and_who(tmp_db: Path, bare_repo: Path,
                                              vote: Callable[..., Any]) -> None:
    bootstrap_project(slug="crit", target_repo_url=file_url(bare_repo), path_owners=_owners())
    vote("crit")
    with transaction() as conn:
        vid = conn.execute("SELECT id FROM variants WHERE name='A'").fetchone()[0]
        conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, rationale, "
            "submitted_by) VALUES (?, 'critical', 'legal', 'privacy', 0.1, 'osobní údaje', 'Jana')",
            (vid,))
    d = status.project_detail("crit")
    b = next(x for x in d["blockers"] if x["kind"] == "critical")
    assert "variantě A" in b["text"] and "Jana" in b["text"]
    assert d["next_step"] == "/pm feedback crit"


def test_provoz_checkpoint_in_build_does_not_jump_to_ship(tmp_db: Path, bare_repo: Path,
                                                          vote: Callable[..., Any]) -> None:
    bootstrap_project(slug="ph", target_repo_url=file_url(bare_repo), path_owners=_owners())
    vote("ph")
    checkpoint.sign("ph", "provoz", by="Karel", note="rollback, on-call, flag")
    assert "/pm ship" not in status.project_detail("ph")["next_step"]


def test_status_after_ship_recommends_retro_and_human_output(
        tmp_db: Path, bare_repo: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    bootstrap_project(slug="done", target_repo_url=file_url(bare_repo), path_owners=_owners())
    set_status("done", "handoff")
    checkpoint.sign("done", "bezpecnost", by="Lucie", note="syntetická data")
    checkpoint.sign("done", "provoz", by="Karel", note="rollback, on-call, flag")
    with transaction() as conn:
        conn.execute("UPDATE projects SET gate_score_latest = 90 WHERE slug = 'done'")
        pid = conn.execute("SELECT id FROM projects WHERE slug = 'done'").fetchone()[0]
        audit(conn, action="session_3.hardening", target_type="project", target_id=pid,
              payload={"informational": False, "meets_threshold": True, "blocked_by": []})
    d = status.project_detail("done")
    assert d["phase"] == "Ship hotový" and d["next_step"] == "/pm handoff done"   # PR, ne retro
    with transaction() as conn:
        audit(conn, action="ship.render", target_type="project", target_id=pid,
              payload={"slug": "done"})
    assert status.project_detail("done")["next_step"] == "/pm retro done"
    assert _run(monkeypatch, status, "--slug", "done") == 0
    out = capsys.readouterr().out
    assert "Další krok" in out and "DB status" not in out and "Lean" in out


def test_status_before_ship_lists_missing_signatures(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="go", target_repo_url=file_url(bare_repo), path_owners=_owners(),
                      personal_data=True)
    set_status("go", "handoff")  # Go, Ship zatím ne
    d = status.project_detail("go")
    assert {b["window"] for b in d["blockers"] if b["kind"] == "missing_signature"} == {
        "bezpecnost", "provoz"}
    assert d["next_step"].startswith("pflanzer checkpoint --slug go bezpecnost")


# ---------------------------------------------------------------- --spec -, vote, slug


KICKOFF = {"hook": "Rychlejší schvalování žádostí", "decider_name": "Dana",
           "risk_profile": "throwaway",
           "metric": "10 z 15 lidí otevře přehled 3× týdně do 30 dnů", "path_owners": OWNERS}


def test_bootstrap_spec_from_stdin(tmp_db: Path, monkeypatch: pytest.MonkeyPatch,
                                   capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run(monkeypatch, quick_session, "bootstrap", "--spec", "-", stdin=json.dumps(KICKOFF))
    out = capsys.readouterr().out
    assert rc == 0 and "Kickoff hotový" in out and "/pm build rychlejsi-schvalovani-zadosti" in out
    rc = _run(monkeypatch, quick_session, "bootstrap", "--spec", "-", "--json",
              stdin=json.dumps({**KICKOFF, "slug": "j2"}))
    assert json.loads(capsys.readouterr().out)["slug"] == "j2"


def test_bootstrap_bad_spec_is_human_error(tmp_db: Path, monkeypatch: pytest.MonkeyPatch,
                                           capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(monkeypatch, quick_session, "bootstrap", "--spec", "-", stdin="{nejde") == 2
    err = capsys.readouterr().err
    assert "není platný JSON" in err and "Traceback" not in err
    assert _run(monkeypatch, quick_session, "bootstrap", "--spec", "-",
                stdin=json.dumps({"hook": "x"})) == 2
    assert "decider_name" in capsys.readouterr().err


def test_bootstrap_metrics_not_filled_with_placeholders(tmp_db: Path) -> None:
    bootstrap_project(risk_profile="throwaway", slug="nomet")
    with transaction() as conn:
        row = conn.execute("SELECT primary_lagging_metric, leading_metric, guardrail_metric "
                           "FROM projects WHERE slug='nomet'").fetchone()
    assert tuple(row) == (None, None, None)


def test_vote_without_prototype_url_warns_and_stores_none(project: dict[str, Any]) -> None:
    out = quick_session.record_voting(
        slug=project["slug"], facilitator="Fanda",
        votes=[{"name": "A", "builder": "claude-code",
                "role_preferences": [{"role_idx": 1, "user_value": 0.8, "rationale": "rychlé"}]}],
        decider_call={"shortlist": ["A"], "rationale": "r"})
    assert out["variants"][0]["prototype_url"] is None
    assert any("varianta A nemá preview URL — zástupci v Asyncu ji neuvidí" in w
               for w in out["warnings"])


def test_vote_bad_spec_shows_example(tmp_db: Path, monkeypatch: pytest.MonkeyPatch,
                                     capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run(monkeypatch, quick_session, "vote", "--spec", "-",
              stdin=json.dumps({"slug": "x", "facilitator": "F", "votes": [{"name": "A"}],
                                "decider_call": {}}))
    err = capsys.readouterr().err
    assert rc == 2 and "role_preferences" in err and '"votes"' in err and "KeyError" not in err


def test_slug_and_name_cut_on_word_boundary() -> None:
    hook = "Rychlejší schvalování žádostí tak, aby šéf viděl co je nové každý den ráno"
    slug = quick_session.slugify(hook)
    assert slug == "rychlejsi-schvalovani-zadosti-tak-aby"
    long_hook = "Aplikace, ve které uvidí každý den přehled nákladů za měsíc"
    assert quick_session.slugify(long_hook) == "aplikace-ve-ktere-uvidi-kazdy"
    name = quick_session.short_name(hook * 2)
    assert name.endswith("…") and not name[:-1].endswith(" ")


def test_current_actor_prefers_cwd_repo_then_global(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.chdir(plain)                       # mimo repo -> globální config
    assert current_actor().startswith("Test Dev")
    repo = tmp_path / "target"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Local Dev")
    git(repo, "config", "user.email", "local@example.com")
    monkeypatch.chdir(repo)                        # target repo má přednost
    assert current_actor() == "Local Dev <local@example.com>"


# ---------------------------------------------------------------- stack-aware prompty, doctor


def test_prompts_python_stack_has_no_npm(project: dict[str, Any], tmp_path: Path,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    py = tmp_path / "pyapp"
    (py / "tests").mkdir(parents=True)
    (py / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (py / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
    monkeypatch.chdir(py)
    out = quick_session.builder_prompts(project["slug"], "Rychlejší checkout")
    assert out["stack"] == "python"
    for p in out["prompts"]:
        assert "make test" in p["ai_prompt"]
        assert "npm" not in p["prompt_text"] and "design system tokenů" not in p["prompt_text"]
        assert "Setup worktree" in p["facilitator_text"] and "Setup worktree" not in p["ai_prompt"]
        assert "pflanzer worktree setup" not in p["ai_prompt"]


def test_prompts_node_stack_uses_scripts(tmp_path: Path) -> None:
    node = tmp_path / "web"
    node.mkdir()
    (node / "package.json").write_text(json.dumps({
        "scripts": {"dev": "vite", "test": "vitest", "lint": "eslint ."},
        "dependencies": {"react": "18"}}), encoding="utf-8")
    prof = quick_session.stack_profile(node)
    assert prof.run_cmd == "npm run dev" and prof.js_frontend
    assert prof.commands == ["npm run lint", "npm test"]


def test_doctor_stack_specific_advice(tmp_path: Path) -> None:
    py = tmp_path / "py"
    py.mkdir()
    (py / "pyproject.toml").write_text("[project]\nname='x'\ndependencies=['requests']\n",
                                       encoding="utf-8")
    assert "npm" not in doctor.check_preview(py)["advice"]
    lock = doctor.check_package_manager(py)
    assert lock["status"] == doctor.WARN and "uv lock" in lock["advice"]
    assert "npm" not in lock["advice"]
    assert lock["impact"].startswith("pilot půjde, ale")
    node = tmp_path / "node"
    node.mkdir()
    (node / "package.json").write_text("{}", encoding="utf-8")
    assert "pflanzer preview up" in doctor.check_preview(node)["advice"]


def test_doctor_guide_needs_most_sections_filled(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    (repo / "docs").mkdir(parents=True)
    guide = repo / "docs" / "INTEGRATION_GUIDE.md"
    tmpl = doctor.GUIDE_TEMPLATE.read_text(encoding="utf-8")
    first_placeholder = next(ln for ln in tmpl.splitlines() if doctor.PLACEHOLDER_RE.search(ln))
    guide.write_text(tmpl.replace(first_placeholder, "- Provider: Auth0", 1), encoding="utf-8")
    assert doctor.check_guide(repo)["status"] == doctor.FAIL       # 1 řádek nestačí
    filled = doctor.PLACEHOLDER_RE.sub("hotovo", tmpl)
    guide.write_text(filled, encoding="utf-8")
    assert doctor.check_guide(repo)["status"] == doctor.OK


def test_severity_aliases_and_czech_labels() -> None:
    given = ("critical", "major", "minor", "high", "medium", "low")
    assert [normalize_severity(x) for x in given] == [
        "critical", "high", "low", "high", "medium", "low"]
    assert [severity_label(x) for x in ("critical", "high", "medium", "low")] == [
        "Kritické", "Důležité", "Drobné", "Drobné"]
    with pytest.raises(ValueError):
        normalize_severity("blocker")
