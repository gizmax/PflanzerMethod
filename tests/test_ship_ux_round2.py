"""2. kolo: Ship výjimka, další krok, selhání testů, AI náhrada, Rozhodnutí, Retro."""
from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from test_ship_gate import below_threshold_project  # noqa: F401 (fixture)

from tool.cli import (
    feedback,
    handoff_pr,
    quality_gates,
    retro,
    session,
    session_2,
    session_3,
)
from tool.cli.db import transaction

# --- Ship: výjimka Decidera ---------------------------------------------------------------


def test_threshold_override_title_and_decider_name(
        below_threshold_project: dict[str, Any]) -> None:  # noqa: F811
    slug = below_threshold_project["slug"]
    out = session_3.hardening_run(slug=slug, override_threshold=True,
                                  override_rationale="Pilot pro interní uživatele")
    title, lines, _warns, nxt, _ctx = session_3._human_ship(out, slug)
    score = out["winner"]["gate_score"]
    assert title == (f"Ship {slug}: připraveno jako draft — výjimka Decidera "
                     f"(Dana Deciderová, {score} < 80)")
    # Provoz je podepsaný (fixture) -> žádný zbytečný checkpoint, rovnou PR a handoff
    assert "Checkpoint provozu" not in nxt
    assert f"pflanzer handoff_pr --slug {slug}" in nxt and f"/pm handoff {slug}" in nxt
    assert lines[-1].startswith("Detail: ")
    # jméno Decidera z DB, ne git user (Test Dev)
    with transaction() as conn:
        body = conn.execute("SELECT body_md FROM decisions WHERE type = 'escalation'"
                            ).fetchone()[0]
    assert "Dana Deciderová" in body
    ship_md = handoff_pr.render_ship_md(slug)
    assert "**Výjimka schválil:** Dana Deciderová (Decider)" in ship_md
    report = Path(out["report_path"]).read_text(encoding="utf-8")
    assert "Výjimku schválil: Dana Deciderová (Decider)" in report


def test_threshold_override_without_decider_name_says_decider_not_git_user(
        below_threshold_project: dict[str, Any]) -> None:  # noqa: F811
    slug = below_threshold_project["slug"]
    with transaction() as conn:
        conn.execute("UPDATE projects SET decider_name = NULL WHERE slug = ?", (slug,))
    out = session_3.hardening_run(slug=slug, override_threshold=True,
                                  override_rationale="důvod")
    assert out["threshold_override"]["decider"] == "Decider"
    with transaction() as conn:
        body = conn.execute("SELECT body_md FROM decisions WHERE type = 'escalation'"
                            ).fetchone()[0]
    assert "(Decider)" in body.split("**Verdikt:**")[1].splitlines()[0]


def test_next_step_skips_checkpoint_when_provoz_signed() -> None:
    winner = {"gates": {"gate_score": 90, "results": []}}
    with_cp = session_3._next_step(winner, True, 80, "x", provoz_done=False)
    assert with_cp.startswith("Skóre 90/100 (práh 80). Checkpoint provozu (20 min), pak PR")
    done = session_3._next_step(winner, True, 80, "x", provoz_done=True)
    assert "Checkpoint" not in done and "pflanzer handoff_pr --slug x" in done
    assert session_3._provoz_done([{"window": "provoz", "state": "ok"}], [])
    assert session_3._provoz_done([], ["Provoz: ok (Karel, on-call)"])
    assert not session_3._provoz_done([{"window": "provoz", "state": "pending"}], [])


def test_override_triage_names_security_gap(worktree_project: dict[str, Any],
                                            vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug, status="handoff")
    out = session_3.hardening_run(slug=slug, override_triage=True,
                                  override_rationale="Pilot, review do T+3")
    assert any("bezpečnost nepodepsal člověk" in w and w.startswith("Ship na odpovědnost")
               for w in out["warnings"])
    with transaction() as conn:
        body = conn.execute("SELECT body_md FROM decisions WHERE type = 'triage'").fetchone()[0]
    assert "výjimku schválil: Dana Deciderová" in body
    assert "bezpečnost nepodepsal člověk" in handoff_pr.render_ship_md(slug)


@pytest.mark.parametrize(("name", "expected"), [
    ("Pavla", "Pavly"), ("Petr", "Petra"), ("Karel", "Karla"), ("Lucie", "Lucie"),
    ("Marek", "Marka"), ("Decider", "Decidera"),
    ("Dana Deciderová", "Decidera (Dana Deciderová)"),
])
def test_decider_genitive(name: str, expected: str) -> None:
    assert session_3.decider_genitive(name) == expected


# --- Skóre krátce a poctivě ---------------------------------------------------------------


def test_summary_line_one_short_sentence() -> None:
    res = [quality_gates.GateResult(g, "pass") for g in
           ("build", "tests", "lint", "security", "types")]
    res += [quality_gates.GateResult("coverage", "skipped", "SKIP: x (neusekni)"),
            quality_gates.GateResult("acceptance", "unsupported", "nic"),
            quality_gates.GateResult("a11y", "skipped", "SKIP: y")]
    assert quality_gates.gates_summary_line(76, res) == (
        "Skóre 76 ze 100. Spočteno nad 5 branami. "
        "Neověřeno: pokrytí testy, akceptační testy, přístupnost.")
    assert "pokrytí testy: x (neusekni)" in quality_gates.gates_summary_line(76, res, reasons=True)
    assert "Spočteno jen ze 4 bran — orientační." in quality_gates.gates_summary_line(100, res[:4])


# --- Python gates -------------------------------------------------------------------------


def test_python_gates_use_project_venv_and_make_lint(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PFLANZER_PYTHON", raising=False)
    root = tmp_path / "app"
    root.mkdir()
    assert quality_gates._python_cmd(root) == "python3"
    (root / ".venv" / "bin").mkdir(parents=True)
    py = root / ".venv" / "bin" / "python"
    py.write_text("#!/bin/sh\n", encoding="utf-8")
    assert quality_gates._python_cmd(root) == str(py)
    monkeypatch.setenv("PFLANZER_PYTHON", "/opt/py")
    assert quality_gates._python_cmd(root) == "/opt/py"
    monkeypatch.delenv("PFLANZER_PYTHON")
    (root / "pyproject.toml").write_text("[project]\nname='a'\nversion='0'\n", encoding="utf-8")
    (root / "Makefile").write_text("lint:\n\t@echo linted\n", encoding="utf-8")
    if quality_gates._has("make"):
        res = quality_gates.gate_lint(quality_gates.Ctx(
            root, quality_gates.detect_stack_info(root), True, ""))
        assert res.status == "pass" and "make lint" in res.details


def test_missing_python_is_human_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "app"
    (root / "tests").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='a'\nversion='0'\n", encoding="utf-8")
    monkeypatch.setenv("PFLANZER_PYTHON", "/nonexistent/python")
    res = {r.gate_type: r for r in quality_gates.run_gates_on_path(root)}
    for gate in ("tests", "build"):
        assert res[gate].status == "skipped"
        assert "Python v projektu nenašel" in res[gate].details
        assert "pflanzer.gates.json" in res[gate].details and '"cmd"' in res[gate].details


# --- Co selhalo: Node TAP, jest, vitest, pytest --------------------------------------------

TAP = """TAP version 13
# Subtest: sums
not ok 1 - sums
  ---
  duration_ms: 0.8
  failureType: 'testCodeFailure'
  error: 'Expected values to be strictly equal:'
  code: 'ERR_ASSERTION'
  expected: 5
  actual: 4
  ...
ok 2 - other
1..2
# fail 1
"""

JEST = """FAIL src/sum.test.js
  ● sum › adds numbers

    expect(received).toBe(expected)

    Expected: 5
    Received: 4
"""

VITEST = """ FAIL  src/sum.test.ts > sum > adds
AssertionError: expected 4 to be 5
"""


def test_failure_line_node_tap_jest_vitest_pytest() -> None:
    line = handoff_pr.failure_line(TAP)
    assert line.startswith("sums — Expected values to be strictly equal:")
    assert "očekáváno 5, bylo 4" in line
    assert handoff_pr.failure_line(JEST) == "sum › adds numbers — očekáváno 5, bylo 4"
    assert handoff_pr.failure_line(VITEST) == \
        "src/sum.test.ts > sum > adds — AssertionError: expected 4 to be 5"
    py = "FAILED tests/test_x.py::test_total - assert 4 == 5\n1 failed"
    assert handoff_pr.failure_line(py) == "tests/test_x.py::test_total — assert 4 == 5"
    assert handoff_pr.failure_line("E   assert 4 == 5\n") == "assert 4 == 5"


def test_failure_lines_relative_to_repo_and_multiple(tmp_path: Path) -> None:
    out = (f"FAILED {tmp_path}/tests/test_a.py::test_a - x\n"
           f"FAILED {tmp_path}/tests/test_b.py::test_b\n")
    lines = handoff_pr.failure_lines(out, limit=1, root=tmp_path)
    assert lines[0] == "tests/test_a.py::test_a — x"
    assert lines[1].startswith("…a 1 další test")


def test_node_tap_failure_summary_names_tests(tmp_path: Path) -> None:
    summary = quality_gates.summarize_test_failures(TAP.replace("sums", f"{tmp_path}/sums"),
                                                    tmp_path)
    assert summary.startswith("✗ sums — Expected values")
    assert str(tmp_path) not in summary
    assert [n for n, _ in quality_gates.parse_test_failures(summary)] == ["sums"]


def test_human_ship_lists_failed_tests_and_detail_path() -> None:
    out = {
        "production_readiness_target": 80, "production_ready": False, "informational": False,
        "decided_winner": "A", "warnings": [], "threshold_override": None,
        "report_nice_path": "data/production_reports/x-readiness.md",
        "triage": {"human_blockers": [], "windows": []},
        "winner": {"variant": "A", "summary_line": "40/100 jen ze 4 bran — orientační",
                   "gate_score": 40, "next_step": "oprav", "failures": [
                       {"gate": "tests", "tests": ["sums", "diff"], "detail": "x"}]},
    }
    title, lines, _w, _n, _c = session_3._human_ship(out, "x")
    assert title == "Ship x: pod prahem"
    assert "Selhaly 2 testy: sums; diff" in lines
    assert lines[-1] == "Detail: data/production_reports/x-readiness.md"


# --- SHIP.md / PR body --------------------------------------------------------------------


def test_ship_md_ai_stand_in_section_and_czech_labels(worktree_project: dict[str, Any],
                                                      vote: Callable[..., Any]) -> None:
    from tool.cli import checkpoint

    slug = worktree_project["slug"]
    with transaction() as conn:   # osobní data = okna bezpečnost a provoz zvlášť
        conn.execute("UPDATE projects SET data_class = 'L3' WHERE slug = ?", (slug,))
    with transaction() as conn:
        conn.execute("UPDATE projects SET path_owners_json = ? WHERE slug = ?",
                     (json.dumps({"bezpecnost": "AI", "provoz": "Karel", "byznys": "Dana",
                                  "produkt": "Pavla"}), slug))
    vote(slug, status="handoff")
    checkpoint.sign(slug, "bezpecnost", ai=True, agent="security-expert", note="pre-check")
    checkpoint.sign(slug, "bezpecnost", by="Petr", note="přečteno")
    session_3.hardening_run(slug=slug)
    md = handoff_pr.render_ship_md(slug)
    body = handoff_pr.build_pr(slug)["body"]
    for text in (md, body):
        assert "Bezpečnost: AI (security-expert), potvrdil Petr" in text
        for old in ("Gates run", "Quality gates", "Audit trail", "Model family",
                    "<URL_PR>", "<PR_URL>"):
            assert old not in text
    assert "<summary>Co se mění</summary>" in body
    assert "Rychlejší checkout pro B2B zákazníky" in body.split("<summary>Výstup")[0]
    assert "Vítěz A — Varianta A" in body.split("<summary>Výstup")[0]
    assert "gh pr view --json url" in md


def test_ship_md_lists_resolved_critical_on_winner(worktree_project: dict[str, Any],
                                                   vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug, status="handoff")
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = 'A'",
            (slug,)).fetchone()[0]
        fid = conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, rationale, "
            "submitted_by) VALUES (?, 'critical', 'Bezpečnost', 'auth', 0.1, "
            "'Chybí kontrola oprávnění', 'Lucie')", (vid,)).lastrowid
    session_2.resolve_feedback(slug=slug, feedback_ids=[fid], by="Ondra",
                               note="opraveno v PR 12")
    body = handoff_pr.build_pr(slug)["body"]
    assert "Vyřešené kritické připomínky (vítěz)" in body
    assert "Lucie" in body and "vyřešeno: Ondra: opraveno v PR 12" in body


# --- Rozhodnutí ---------------------------------------------------------------------------


def _critical(slug: str, variant: str) -> int:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = ?",
            (slug, variant)).fetchone()[0]
        return int(conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, "
            "rationale, submitted_by) VALUES (?, 'critical', 'security', 'auth', 0.1, "
            "'Chybí kontrola', 'Test')", (vid,)).lastrowid)


def test_second_go_error_shows_force_example(project: dict[str, Any],
                                             vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="A vede")
    with pytest.raises(ValueError, match=r"--force.*--rationale") as exc:
        session_2.record_decision(slug=slug, decision="go", winner="B", rationale="B")
    assert f"pflanzer session_2 decide --slug {slug} go --winner B --force --rationale" in str(
        exc.value)


def test_resolve_points_to_go_on_winner(project: dict[str, Any], vote: Callable[..., Any],
                                        monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    slug = project["slug"]
    vote(slug)  # shortlist A, B
    on_a = _critical(slug, "A")
    on_c = _critical(slug, "C")  # poražená, mimo shortlist
    out = session_2.resolve_feedback(slug=slug, feedback_ids=[on_a], by="Petr", note="opraveno")
    assert out["focus_variants"] == ["A", "B"]
    assert out["open_critical_on_winner"] == [] and [c["id"] for c in out["open_critical_other"]] \
        == [on_c]
    monkeypatch.setattr(sys, "argv", ["session_2.py", "resolve", "--slug", slug,
                                      "--feedback-id", str(_critical(slug, "B")),
                                      "--by", "Petr", "--note", "ok"])
    session_2.main()
    text = capsys.readouterr().out
    assert "Na shortlistu A/B žádný kritický nezbývá" in text   # Rozhodnutí ještě nepadlo
    assert f"decide --slug {slug} go --winner A" in text
    assert "resolve --slug" not in text.split("Další krok")[1].split("Doporučení")[0]


def test_feedback_add_critical_next_step(project: dict[str, Any], vote: Callable[..., Any],
                                         monkeypatch: pytest.MonkeyPatch,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    slug = project["slug"]
    vote(slug)
    monkeypatch.setattr(sys, "argv", ["feedback.py", "add", "--slug", slug, "--variant", "A",
                                      "--role", "Bezpečnost", "--severity", "critical",
                                      "--text", "Hesla v URL", "--author", "Lucie"])
    feedback.main()
    text = capsys.readouterr().out
    assert "blokuje Go" in text and "session_2 resolve" in text
    assert "--override-critical" in text


# --- session.py ---------------------------------------------------------------------------


def test_user_value_out_of_range_is_human_error(project: dict[str, Any]) -> None:
    spec = {"slug": project["slug"], "variants": [{
        "name": "A", "builder": "claude-code",
        "role_preferences": [{"role_idx": 1, "user_value": 7, "effort": 0.3, "risk": 0.2,
                              "strategic_fit": 0.5, "rationale": "x"}]}]}
    with pytest.raises(ValueError, match=r"`user_value` = 7.*0–1"):
        session.persist(spec)


def test_session_unknown_slug_is_czech(tmp_db: Path) -> None:
    spec = {"slug": "neexistuje", "variants": [{"name": "A", "builder": "manual"}]}
    with pytest.raises(ValueError, match=r"Projekt „neexistuje“ neexistuje.*pflanzer status"):
        session.persist(spec)


# --- Retro --------------------------------------------------------------------------------


def test_retro_without_subcommand_is_czech_help(monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["retro.py", "moje-appka"])
    with pytest.raises(SystemExit) as exc:
        retro.main()
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "chybí, co se má udělat" in err
    assert "pflanzer retro report --slug <slug>" in err and "moje-appka --" not in err
    assert "usage:" not in err and "invalid choice" not in err


def test_retro_report_in_data_root_with_values_and_ai_share(
        project: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    slug = project["slug"]
    with transaction() as conn:
        conn.execute(
            "UPDATE projects SET path_owners_json = ?, primary_lagging_metric = ? WHERE slug = ?",
            (json.dumps({"byznys": "Dana", "produkt": "AI", "design": "AI:ux-expert",
                         "vyvoj": "Petr", "bezpecnost": "Lucie", "provoz": "Karel"}),
             "10 z 15 obchodníků otevře přehled do 30 dnů", slug))
    retro.record(slug=slug, milestone="t7", metric="t7_bugs", value=2)
    retro.record(slug=slug, milestone="t90", metric="t90_lagging_metric", value=62, unit="%")
    monkeypatch.setattr(sys, "argv", ["retro.py", "report", "--slug", slug])
    retro.main()
    out = capsys.readouterr().out
    assert "Metrika: 10 z 15 obchodníků otevře přehled do 30 dnů — změřeno: 62 % (T+90)" in out
    assert "Podíl kroků s AI náhradou: 33 % (2 z 6 kroků: Produkt, Design)" in out
    assert "T+7 t7_bugs: 2" in out
    path = retro.RETRO_DIR / f"{slug}-retro.md"
    assert path.is_file() and str(path) in out.replace("~", str(Path.home()))
    md = path.read_text(encoding="utf-8")
    assert "Podíl kroků s AI náhradou" in md and "Reinforcement" not in md
    reminders = retro.render_reminders(slug, "md", from_date="2026-09-01")
    assert "# Připomínky —" in reminders and "Reinforcement" not in reminders


def test_retro_plural_helpers() -> None:
    from tool.cli._compat import count

    assert [count(n, "den", "dny", "dní") for n in (1, 3, 5)] == ["1 den", "3 dny", "5 dní"]
