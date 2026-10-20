"""Pilot 21 (nováček): demo Ship bez podpisů, SHIP.md hned po Shipu, Co to je, počet bran."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import bootstrap_project, file_url, git

from tool.cli import handoff_pr, report, session_3, worktree


def _commit(wt: Path) -> None:
    (wt / "checkout.js").write_text("export const f = () => true;\n", encoding="utf-8")
    git(wt, "add", "checkout.js")
    git(wt, "commit", "-q", "-m", "feat: fast checkout")


@pytest.fixture
def demo(tmp_db: Path, bare_repo: Path, tmp_targets: Path,
         vote: Callable[..., Any]) -> dict[str, Any]:
    out = bootstrap_project(slug="demo", risk_profile="throwaway",
                            target_repo_url=file_url(bare_repo))
    slug = out["slug"]
    worktree.setup(slug, install_deps=False, run_guard=False)
    wt = tmp_targets / f"{slug}-A"
    (wt / "node_modules").mkdir(exist_ok=True)
    _commit(wt)
    vote(slug, status="handoff")
    return {"slug": slug, "wt": wt}


def test_throwaway_ship_does_not_require_window_signatures(demo: dict[str, Any]) -> None:
    out = session_3.hardening_run(slug=demo["slug"])
    assert out["risk_profile"] == "throwaway"
    assert out["blocked_by"] == []
    assert out["triage"]["human_blockers"] == []
    assert out["production_ready"] is False
    reason = out["production_ready_reason"]
    assert "demo" in reason and "podpis" in reason
    title, lines, _warns, nxt, ctx = session_3._human_ship(out, demo["slug"])
    text = "\n".join([title, *lines, nxt])
    assert "blokováno podpisy" not in text
    assert "jméno chybí" not in text
    assert "informativní, neblokuje" in text
    assert "nový Kickoff s risk profilem pilot" in text
    assert ctx["missing_signatures"] is False


def test_throwaway_report_has_no_blocking_banner(demo: dict[str, Any]) -> None:
    out = session_3.hardening_run(slug=demo["slug"])
    md = session_3.REPORTS_DIR.joinpath("demo-readiness.md").read_text(encoding="utf-8")
    assert out["slug"] == "demo"
    assert "BLOKOVÁNO" not in md and "chybí podpisy" not in md


def test_ship_main_writes_ship_md_and_prints_pr_step(
        demo: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/gh" if name == "gh" else None)
    monkeypatch.setattr("sys.argv", ["session_3", "--slug", demo["slug"]])
    session_3.main()
    cap = capsys.readouterr()
    assert cap.out.splitlines()[0].startswith("**Pflanzer Method")
    assert "[ship gate]" not in cap.err
    ship = handoff_pr.SHIP_DIR / demo["slug"] / "SHIP.md"
    assert ship.is_file()
    assert "SHIP.md (text PR)" in cap.out
    assert "gh pr create" in cap.out and "--title" in cap.out


def test_ship_main_without_gh_says_open_manually(
        demo: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr("sys.argv", ["session_3", "--slug", demo["slug"]])
    session_3.main()
    out = capsys.readouterr().out
    assert "otevřete PR ručně" in out and "SHIP.md" in out


def test_ship_json_has_ship_path_and_command(
        demo: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    import json
    monkeypatch.setattr("sys.argv", ["session_3", "--slug", demo["slug"], "--json"])
    session_3.main()
    data = json.loads(capsys.readouterr().out)
    assert data["ship_path"].endswith("SHIP.md")
    assert "gh pr create" in data["pr_command"]


def test_blocked_pilot_gate_notice_not_before_brand_line(
        worktree_project: dict[str, Any], vote: Callable[..., Any],
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    slug = worktree_project["slug"]
    _commit(worktree_project["worktrees"]["A"])
    vote(slug, status="handoff")
    monkeypatch.setattr("sys.argv", ["session_3", "--slug", slug])
    session_3.main()
    cap = capsys.readouterr()
    assert cap.err == ""
    assert cap.out.splitlines()[0].startswith("**Pflanzer Method")
    assert "podpis" in cap.out.lower() or "ještě nepodepsal" in cap.out


def test_pr_hook_cleaned_from_xyz_template() -> None:
    xyz = ("Problém k vyřešení: **Předobjednávky chleba pro Pekárnu Kvásek Brno**. Ověříme ho "
           "na třech funkčních variantách, mezi kterými se rozhodne nad běžícím kódem.")
    lead = handoff_pr._pr_lead(
        hook=xyz, winner="A", open_crit=0, open_remarks=0, open_conditions=0, failures=0,
        override=None, overridden=False, unverified=[], blocked_by=[],
        metric="80 % objednávek bez telefonátu")
    assert lead[0] == ("**Co to je:** Předobjednávky chleba pro Pekárnu Kvásek Brno "
                       "(varianta A); metrika úspěchu: 80 % objednávek bez telefonátu")
    assert "Ověříme" not in lead[0]


def test_failed_gates_counted_by_gate_not_finding() -> None:
    failures = [("a11y", "x"), ("a11y", "y"), ("a11y", "z")]
    lead = handoff_pr._pr_lead(
        hook="Hook", winner=None, open_crit=0, open_remarks=0, open_conditions=0, failures=3,
        failed_gates=handoff_pr._failed_gates(failures), override=None, overridden=False,
        unverified=[], blocked_by=[], metric=None)
    assert "1 brána selhala: přístupnost (3 nálezy)" in lead[1]
    assert "3 selhaných" not in lead[1]
    two = handoff_pr._failed_gates_text([("build", 1), ("web:a11y", 2)])
    assert two.startswith("2 brány selhaly: ") and "v repu web" in two


def test_report_risks_include_failed_gate() -> None:
    info = report._gate_info(
        [{"gate": "build", "status": "pass", "details": ""},
         {"gate": "a11y", "status": "fail", "details": "3 stránek"}], 80)
    assert info["failed"] == ["přístupnost"]


def test_human_ship_md_has_no_double_bullet(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = {
        "state": {"blocked_by": [], "score": 90, "target": 80, "verdict": "v"},
        "ctx": {"project": [None] * 9, "triage": {"blocked_by": [], "windows": []}},
        "gates_summary": "ok", "gate_score": 90, "target": 80, "failures": [],
        "critical_lines": ["- Informativně, poražená varianta: něco"], "warnings": [],
        "repos": [], "remarks": [],
    }
    monkeypatch.setattr(handoff_pr, "build_pr", lambda slug: fake)
    view = handoff_pr._human_ship_md("x", Path("/tmp/SHIP.md"))
    assert "Informativně, poražená varianta: něco" in view["lines"]
