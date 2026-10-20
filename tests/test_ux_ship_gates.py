"""Ship UX: Python brány, --variants bez rationale, jmenovité blokace oken, feedback výstup."""
from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import git

from tool.cli import extract, feedback, feedback_pull, quality_gates, session_2, session_3
from tool.cli.db import transaction

# --- Python brány -------------------------------------------------------------------------


@pytest.fixture
def py_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("PFLANZER_PYTHON", sys.executable)
    root = tmp_path / "pyapp"
    (root / "tests").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname = 'pyapp'\nversion = '0'\n",
                                         encoding="utf-8")
    (root / "app.py").write_text("def total():\n    return 5\n", encoding="utf-8")
    (root / "tests" / "test_app.py").write_text(
        "from app import total\n\ndef test_total():\n    assert total() == 5\n", encoding="utf-8")
    (root / "conftest.py").write_text("", encoding="utf-8")
    return root


def _by_gate(path: Path) -> dict[str, quality_gates.GateResult]:
    return {r.gate_type: r for r in quality_gates.run_gates_on_path(path)}


def test_python_tests_gate_uses_python_m_pytest(py_project: Path) -> None:
    gates = _by_gate(py_project)
    assert gates["tests"].status == "pass"
    assert "1 testů prošlo" in gates["tests"].details


def test_python_failing_test_shows_assertion_line(py_project: Path) -> None:
    (py_project / "tests" / "test_app.py").write_text(
        "from app import total\n\ndef test_total():\n    assert total() == 4\n", encoding="utf-8")
    res = _by_gate(py_project)["tests"]
    assert res.status == "fail"
    assert "assert 5 == 4" in res.details


def test_python_build_uses_make_build_when_target_exists(py_project: Path) -> None:
    if not quality_gates._has("make"):
        pytest.skip("make není k dispozici")
    (py_project / "Makefile").write_text("build:\n\t@echo built\n", encoding="utf-8")
    res = _by_gate(py_project)["build"]
    assert res.status == "pass" and "make build" in res.details


def test_python_build_falls_back_to_compileall(py_project: Path) -> None:
    res = _by_gate(py_project)["build"]
    assert res.status == "pass" and "compileall" in res.details
    (py_project / "broken.py").write_text("def x(:\n", encoding="utf-8")
    assert _by_gate(py_project)["build"].status == "fail"


def test_python_gate_texts_have_no_node_wording(py_project: Path) -> None:
    gates = _by_gate(py_project)
    text = " ".join(r.details for r in gates.values()).lower()
    for word in ("vitest", "playwright", "npm audit", "npx"):
        assert word not in text


def test_lint_missing_module_is_skip_not_fail(py_project: Path,
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    real_has, real_run = quality_gates._has, quality_gates._run
    monkeypatch.setattr(quality_gates, "_has", lambda t: False if t == "ruff" else real_has(t))

    def fake_run(cmd: Any, cwd: Path, timeout: int = 120) -> tuple[int, str, str]:
        if isinstance(cmd, list) and "ruff" in cmd:
            return 1, "", "/usr/bin/python3: No module named ruff"
        return real_run(cmd, cwd, timeout)

    monkeypatch.setattr(quality_gates, "_run", fake_run)
    res = _by_gate(py_project)["lint"]
    assert res.status == "skipped" and "ruff" in res.details


def test_json_adapter_and_missing_pyyaml_message(py_project: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    (py_project / "pflanzer.gates.json").write_text('{"build": {"cmd": "true"}}', encoding="utf-8")
    gates = _by_gate(py_project)
    assert gates["build"].status == "pass" and gates["tests"].status == "unsupported"
    (py_project / "pflanzer.gates.json").unlink()
    (py_project / "pflanzer.gates.yml").write_text("build: 'true'\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "yaml", None)  # import yaml -> ImportError
    with pytest.raises(quality_gates.AdapterError, match="(?i)pyyaml.*pflanzer.gates.json"):
        quality_gates.run_gates_on_path(py_project)


def test_summary_line_names_missing_gates() -> None:
    results = [
        quality_gates.GateResult("build", "pass"),
        quality_gates.GateResult("tests", "pass"),
        quality_gates.GateResult("types", "skipped", "SKIP: mypy není nakonfigurovaný"),
    ]
    # méně než 5 běžících bran: poctivě „orientační“
    line2 = quality_gates.gates_summary_line(100, results)
    assert line2 == ("Skóre 100 ze 100. Spočteno jen ze 2 automatických kontrol — orientační. "
                     "Neověřeno: typová kontrola.")
    many = [quality_gates.GateResult(g, "pass")
            for g in ("build", "tests", "lint", "security", "a11y")]
    many += [quality_gates.GateResult("coverage", "skipped",
                                      "SKIP: coverage se nespouští (definuj příkaz)"),
             quality_gates.GateResult("types", "skipped", "SKIP: mypy není nakonfigurovaný")]
    line = quality_gates.gates_summary_line(76, many)
    assert line == ("Skóre 76 ze 100. Spočteno z 5 automatických kontrol. "
                    "Neověřeno: pokrytí testy, typová kontrola.")
    full = quality_gates.skip_reasons(many)
    assert full == ["coverage — coverage se nespouští (definuj příkaz)",
                    "types — mypy není nakonfigurovaný"]


# --- nový kód bez testů -------------------------------------------------------------------


def test_code_without_tests_detects_missing_tests(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    git(repo, "checkout", "-q", "-b", "feat")
    (repo / "service.py").write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "feat")
    res = extract.code_without_tests(repo, "main")
    assert res and res["missing_tests"] and res["new_source_files"] == 1
    (repo / "tests").mkdir()
    (repo / "tests" / "test_service.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    res = extract.code_without_tests(repo, "main")
    assert res and not res["missing_tests"] and res["test_files_changed"] == 1


# --- Ship: --variants a okna --------------------------------------------------------------


def test_variants_other_than_winner_requires_rationale(worktree_project: dict[str, Any],
                                                       vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="A vede")
    with pytest.raises(ValueError, match=r"Vítěz z Rozhodnutí je A\. Jinou variantu ověříš"):
        session_3.hardening_run(slug=slug, variants=["B"])
    out = session_3.hardening_run(slug=slug, variants=["B"],
                                  override_rationale="Chci vidět skóre B")
    assert out["informational"] is True
    assert out["decided_winner"] == "A"
    assert out["production_ready"] is False
    report = Path(out["report_path"]).read_text(encoding="utf-8")
    assert "jen informativní porovnání" in report
    assert "Vítěz z Rozhodnutí je **A**" in report
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        assert session_2.get_winner(conn, pid) == "A"


def test_ship_blocked_message_names_people_and_windows(worktree_project: dict[str, Any],
                                                       vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    with transaction() as conn:   # osobní data = okna bezpečnost a provoz zvlášť
        conn.execute("UPDATE projects SET data_class = 'L3' WHERE slug = ?", (slug,))
    with transaction() as conn:
        conn.execute("UPDATE projects SET path_owners_json = ? WHERE slug = ?",
                     ('{"bezpecnost": "Jana", "provoz": "Ondra"}', slug))
    vote(slug, status="handoff")
    out = session_3.hardening_run(slug=slug)
    human = out["triage"]["human_blockers"]
    assert any(h.startswith("Provoz (Ondra) ještě nepodepsal") and
               f"pflanzer checkpoint --slug {slug} provoz --by Ondra" in h for h in human)
    assert not any("/pm triage" in h or "platform" in h for h in human)
    assert "/pm triage" not in out["winner"]["next_step"]
    assert out["winner"]["summary_line"].count(" ze 100") == 1


def test_pending_ai_draft_waits_for_named_signature(worktree_project: dict[str, Any],
                                                    vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    with transaction() as conn:
        conn.execute("UPDATE projects SET path_owners_json = ? WHERE slug = ?",
                     ('{"bezpecnost": "Jana"}', slug))
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        for track in ("security", "legal"):
            conn.execute(
                "INSERT INTO triage (project_id, track, status, artefact_md, signed_by) "
                "VALUES (?, ?, 'pending', 'AI draft', 'AI') "
                "ON CONFLICT(project_id, track) DO UPDATE SET status='pending', signed_by='AI'",
                (pid, track))
    vote(slug, status="handoff")
    out = session_3.hardening_run(slug=slug)
    blockers = out["triage"]["human_blockers"]
    assert any(h.startswith("AI draft čeká na podpis: Jana") for h in blockers)


# --- feedback -----------------------------------------------------------------------------


def test_feedback_pull_reports_silent_reps_and_severity_counts(
        worktree_project: dict[str, Any], vote: Callable[..., Any],
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    slug = worktree_project["slug"]
    vote(slug)
    with transaction() as conn:
        conn.execute("UPDATE projects SET path_owners_json = ? WHERE slug = ?",
                     ('{"bezpecnost": "Lucie Nováková", "design": "Eva", "provoz": "Ondra"}', slug))
    feedback.add_feedback(slug=slug, variant="A", role="Bezpečnost", severity="critical",
                          text="Heslo v URL", author="Lucie")
    feedback.add_feedback(slug=slug, variant="A", role="Design", severity="minor",
                          text="Malé písmo", author="Eva")
    agg = feedback_pull.aggregate(slug)
    assert [r["step"] for r in agg["silent_reps"]] == ["provoz"]
    monkeypatch.setattr(sys, "argv", ["feedback_pull.py", "--slug", slug])
    feedback_pull.main()
    out = capsys.readouterr().out
    assert "Kritické 1" in out and "Drobné 1" in out
    assert "Ještě bez feedbacku: Provoz (Ondra)" in out
    assert "Lucie" in out and not out.lstrip().startswith("{")
    assert "skóre" not in out.lower()


def test_feedback_accepts_major_minor_and_rejects_nonsense() -> None:
    from tool.cli.ux import normalize_severity
    assert normalize_severity("major") == "high" and normalize_severity("minor") == "low"
    with pytest.raises(ValueError, match="critical, major nebo minor"):
        normalize_severity("blocker")


def test_spec_from_stdin_and_human_error(tmp_db: Path, monkeypatch: pytest.MonkeyPatch,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    import io

    from tool.cli import session
    monkeypatch.setattr(sys, "stdin", io.StringIO("{ nejde to"))
    monkeypatch.setattr(sys, "argv", ["session.py", "--spec", "-"])
    with pytest.raises(SystemExit) as exc:
        session.main()
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "není platný JSON" in err and '"variants"' in err and "Traceback" not in err


def test_variant_without_prototype_url_warns(project: dict[str, Any]) -> None:
    from tool.cli import session
    out = session.persist({
        "slug": project["slug"], "facilitator": "F",
        "variants": [{"name": "A", "builder": "claude-code", "prototype_url": None,
                      "role_preferences": [{"role_idx": 1, "user_value": 0.5, "effort": 0.5,
                                            "risk": 0.5, "strategic_fit": 0.5,
                                            "rationale": "test"}]}],
    })
    assert out["variants"][0]["prototype_url"] is None
    assert any("nemá preview URL" in w and "set-url" in w for w in out["warnings"])
    assert "sandbox.invalid" not in out["next_step"]


def test_subprocess_cli_has_no_traceback(tmp_db: Path) -> None:
    res = subprocess.run([sys.executable, "tool/cli/session_2.py", "resolve", "--slug", "nope",
                          "--feedback-id", "1"], capture_output=True, text=True,
                         cwd=Path(__file__).resolve().parents[1],
                         env={"PFLANZER_DB": str(tmp_db), "PATH": "/usr/bin:/bin",
                              "HOME": str(tmp_db.parent)})
    assert res.returncode == 2 and "Traceback" not in res.stderr and "--by" in res.stderr
