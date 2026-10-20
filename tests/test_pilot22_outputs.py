"""Pilot 22: varování bran v Rizicích, kapacita, doctor, šablona Node backendu, `pflanzer start`."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import git

from tool.cli import doctor, handoff_pr, init, quick_session, report, session_3
from tool.cli.db import transaction
from tool.cli.quality_gates import gate_risk_notes, warned_gates

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def shipped(worktree_project: dict[str, Any], vote: Callable[..., Any]) -> dict[str, Any]:
    slug = worktree_project["slug"]
    wt = worktree_project["worktrees"]["A"]
    (wt / "checkout.js").write_text("export const f = () => true;\n", encoding="utf-8")
    git(wt, "add", "checkout.js")
    git(wt, "commit", "-q", "-m", "feat: fast checkout")
    vote(slug, status="handoff")
    session_3.hardening_run(slug=slug)
    return worktree_project


def _force_warn(slug: str, gates: tuple[str, ...]) -> None:
    """Všechny změřené varianty dostanou WARN u daných bran (vítěz je tak jistě zasažen)."""
    with transaction() as conn:
        for g in gates:
            conn.execute("UPDATE quality_gates SET status = 'warn', details_md = '' "
                         "WHERE gate_type = ?", (g,))


def test_warned_gates_use_human_labels() -> None:
    rows = [{"gate": "a11y", "status": "warn"}, {"gate": "build", "status": "pass"},
            {"gate": "observability", "status": "warn"}, {"gate": "a11y", "status": "warn"}]
    assert warned_gates(rows) == ["přístupnost", "observabilita"]


def test_risk_notes_personal_data_only_for_production() -> None:
    unv = [{"gate": "coverage", "reason": "x", "detail": ""}, {"gate": "lint", "reason": "x",
                                                                "detail": ""}]
    prod = gate_risk_notes(["přístupnost"], unv, "production", "L3")
    assert prod[0] == "Varování: přístupnost"
    assert "pokrytí testy" in prod[1] and "osobních dat" in prod[1] and "lint" not in prod[1]
    assert gate_risk_notes([], unv, "pilot", "L3") == []
    assert gate_risk_notes([], unv, "production", "L1") == []


def test_ship_md_and_pr_show_gate_warnings(shipped: dict[str, Any]) -> None:
    slug = shipped["slug"]
    _force_warn(slug, ("a11y", "observability"))
    md = handoff_pr.render_ship_md(slug)
    assert "Varování: přístupnost, observabilita" in md
    assert len(md.splitlines()) <= 60
    body = handoff_pr.build_pr(slug)["body"]
    rizika = next(x for x in body.splitlines() if x.startswith("**Rizika:**"))
    assert "Varování: přístupnost, observabilita" in rizika


def test_report_summary_lists_warnings_and_capacity_tier(
        shipped: dict[str, Any]) -> None:
    slug = shipped["slug"]
    _force_warn(slug, ("a11y", "observability"))
    with transaction() as conn:
        conn.execute("UPDATE projects SET capacity_person_days = 14, tier = 'full' WHERE slug = ?",
                     (slug,))
    data = report.collect(slug)
    assert "Varování: přístupnost, observabilita" in data["risks"]
    md = report.render_summary_md(data)
    assert "14 člověkodnů (plán z Kickoffu pro Full" in md


def test_doctor_next_step_mentions_terminal_start(tmp_path: Path) -> None:
    src = (REPO_ROOT / "tool" / "cli" / "doctor.py").read_text(encoding="utf-8")
    assert "pflanzer start --spec kickoff.json" in src and "pflanzer start --help" in src
    assert callable(doctor.main)


def test_node_backend_gets_backend_template(tmp_path: Path) -> None:
    pkg = {"dependencies": {"express": "^4"}, "devDependencies": {"typescript": "^5"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    assert init.guide_template_for(tmp_path) == init.NODE_BACKEND_TEMPLATE_PATH
    assert "Tailwind" not in init.NODE_BACKEND_TEMPLATE_PATH.read_text(encoding="utf-8")


def test_node_frontend_keeps_react_template(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(json.dumps(
        {"dependencies": {"express": "^4", "react": "^18"}}), encoding="utf-8")
    assert init.guide_template_for(tmp_path) == init.TEMPLATE_PATH
    other = tmp_path / "plain"
    other.mkdir()
    (other / "package.json").write_text("{}", encoding="utf-8")
    assert init.guide_template_for(other) == init.TEMPLATE_PATH


def test_git_add_includes_lockfile_and_ci(tmp_path: Path) -> None:
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    cmd = init.git_add_command(tmp_path)
    assert "package-lock.json" in cmd and ".github" in cmd
    assert "yarn.lock" not in cmd


def test_start_help_shows_pflanzer_start() -> None:
    res = subprocess.run([sys.executable, str(REPO_ROOT / "tool" / "cli" / "quick_session.py"),
                          "bootstrap", "--help"], capture_output=True, text=True,
                         env={"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"})
    assert res.stdout.startswith("usage: pflanzer start"), res.stdout[:200]
    assert quick_session is not None

