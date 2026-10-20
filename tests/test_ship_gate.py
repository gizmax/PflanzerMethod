"""Ship gate (session_3): triage hard gate, min gates, override, skeleton policy."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import bootstrap_project, set_status

from tool.cli import extract, session_3
from tool.cli.db import transaction
from tool.cli.extract import ExtractionError


@pytest.fixture
def handoff_project(worktree_project: dict[str, Any], vote: Callable[..., Any]) -> dict[str, Any]:
    vote(worktree_project["slug"], status="handoff")
    return worktree_project


def test_deferred_triage_and_few_gates_block(handoff_project: dict[str, Any]) -> None:
    out = session_3.hardening_run(slug=handoff_project["slug"])
    assert out["risk_profile"] == "pilot"
    assert out["production_ready"] is False
    blocked = out["blocked_by"]
    assert any(b.startswith("triage:") for b in blocked)
    assert any(b.startswith("gates:insufficient") for b in blocked)
    # Gates ran in place in the worktrees with the base-branch adapter.
    assert {v["method"] for v in out["per_variant"]} == {"worktree"}
    assert all(v["gates_run"] == 2 for v in out["per_variant"])
    assert out["winner"]["variant"] == "A"  # tie on score -> preference_score
    assert out["winner"]["gate_score"] == 100
    assert Path(out["report_path"]).is_file()
    with transaction() as conn:
        methods = {r[0] for r in conn.execute("SELECT extraction_method FROM extracted_code")}
    assert methods == {"worktree"}  # stored as-is, no in_repo_branch fallback


def test_override_requires_rationale(handoff_project: dict[str, Any],
                                     monkeypatch: pytest.MonkeyPatch) -> None:
    slug = handoff_project["slug"]
    with pytest.raises(ValueError, match="rationale"):
        session_3.hardening_run(slug=slug, override_triage=True, override_rationale="  ")
    monkeypatch.setattr(sys, "argv", ["session_3.py", "--slug", slug, "--override-triage"])
    with pytest.raises(SystemExit) as exc:
        session_3.main()
    assert exc.value.code == 2
    with transaction() as conn:
        n = conn.execute("SELECT COUNT(*) FROM decisions WHERE type = 'triage'").fetchone()[0]
    assert n == 0


def test_override_with_rationale_writes_decision(handoff_project: dict[str, Any]) -> None:
    slug = handoff_project["slug"]
    out = session_3.hardening_run(
        slug=slug, override_triage=True,
        override_rationale="Pilot pro 5 interních uživatelů, Security review naplánováno na T+3",
    )
    assert not any(b.startswith("triage:") for b in out["blocked_by"])
    assert out["triage"]["override"] is not None
    # Gates are still insufficient -> still not production-ready.
    assert any(b.startswith("gates:insufficient") for b in out["blocked_by"])
    assert out["production_ready"] is False
    with transaction() as conn:
        rows = conn.execute(
            "SELECT body_md, atribuce_user FROM decisions WHERE type = 'triage'"
        ).fetchall()
        audit = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'ship_gate.triage_override'"
        ).fetchone()[0]
    assert len(rows) == 1
    assert "pflanzer:triage-override" in rows[0][0]
    assert "Security review naplánováno" in rows[0][0]
    assert audit == 1


def test_skeleton_refused_for_pilot(handoff_project: dict[str, Any]) -> None:
    with pytest.raises(ExtractionError, match="throwaway"):
        session_3.hardening_run(slug=handoff_project["slug"],
                                extract_method_overrides={"A": "skeleton"})


def test_pilot_without_worktree_fails_loud(project: dict[str, Any],
                                           vote: Callable[..., Any]) -> None:
    vote(project["slug"], status="handoff")
    with pytest.raises(ExtractionError, match="worktree"):
        session_3.hardening_run(slug=project["slug"])


def test_skeleton_allowed_for_throwaway(tmp_db: Path, vote: Callable[..., Any]) -> None:
    info = bootstrap_project(risk_profile="throwaway", slug="demo-throwaway")
    vote(info["slug"], names=("A",))
    set_status(info["slug"], "handoff")
    method, wt = extract.plan_extraction(
        slug=info["slug"], variant_name="A", builder="claude-code", risk_profile="throwaway",
    )
    assert (method, wt) == ("skeleton", None)
    res = extract.extract(slug=info["slug"], variant_name="A")
    assert res["method"] == "skeleton"
    assert res["risk_profile"] == "throwaway"
    assert (Path(res["absolute_path"]) / "package.json").is_file()


# --- Ship pod prahem: override Decidera (--override-threshold) -------------------------

LOW_SCORE_ADAPTER = (
    "# 4 gates ran, `types` fails -> score 75 < 80 (pilot threshold), gates sufficient\n"
    "build: {cmd: \"true\"}\n"
    "tests: {cmd: \"true\"}\n"
    "lint: {cmd: \"true\"}\n"
    "types: {cmd: \"false\"}\n"
)


@pytest.fixture
def below_threshold_project(project: dict[str, Any], tmp_targets: Path,
                            vote: Callable[..., Any]) -> dict[str, Any]:
    from conftest import push_files, worktree_path

    from tool.cli import checkpoint, worktree

    push_files(project["bare_repo"], {"pflanzer.gates.yml": LOW_SCORE_ADAPTER},
               "ci: add pflanzer gate adapter")
    worktree.setup(project["slug"], install_deps=False, run_guard=False)
    for v in ("A", "B", "C"):
        (worktree_path(tmp_targets, project["slug"], v) / "node_modules").mkdir(exist_ok=True)
    vote(project["slug"], status="handoff")
    for window, who in (("zadani", "Dana"), ("bezpecnost", "Lucie"), ("provoz", "Karel")):
        checkpoint.sign(project["slug"], window, by=who, note="ok")
    return project


def test_threshold_override_requires_rationale(below_threshold_project: dict[str, Any],
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    slug = below_threshold_project["slug"]
    with pytest.raises(ValueError, match="rationale"):
        session_3.hardening_run(slug=slug, override_threshold=True, override_rationale=" ")
    monkeypatch.setattr(sys, "argv", ["session_3.py", "--slug", slug, "--override-threshold"])
    with pytest.raises(SystemExit) as exc:
        session_3.main()
    assert exc.value.code == 2
    with transaction() as conn:
        n = conn.execute("SELECT COUNT(*) FROM decisions WHERE type = 'escalation'").fetchone()[0]
    assert n == 0


def test_below_threshold_without_override_is_not_ready(
        below_threshold_project: dict[str, Any]) -> None:
    out = session_3.hardening_run(slug=below_threshold_project["slug"])
    assert out["winner"]["gate_score"] < out["production_readiness_target"]
    assert out["production_ready"] is False
    assert out["blocked_by"] == []
    assert "--override-threshold" in out["winner"]["next_step"]


def test_threshold_override_records_and_marks_ready(
        below_threshold_project: dict[str, Any], tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    from tool.cli import handoff_pr

    slug = below_threshold_project["slug"]
    repo = tmp_path / "target-repo"
    (repo / ".pflanzer").mkdir(parents=True)
    monkeypatch.chdir(repo)
    why = "Pilot pro 5 interních uživatelů, types opravíme do T+3"
    out = session_3.hardening_run(slug=slug, override_threshold=True, override_rationale=why)

    assert out["production_ready"] is True
    assert out["winner"]["production_ready"] is True
    assert out["winner"]["threshold_override"] is True
    assert out["threshold_override"]["decider"] == "Dana Deciderová"
    assert out["winner"]["verdict"] == (
        "pod prahem — Ship na odpovědnost Decidera (Dana Deciderová)")
    assert out["blocked_by"] == []

    with transaction() as conn:
        rows = conn.execute(
            "SELECT body_md FROM decisions WHERE type = 'escalation'").fetchall()
        audits = conn.execute(
            "SELECT payload_json FROM audit_log WHERE action = 'ship_gate.threshold_override'"
        ).fetchall()
        ship = conn.execute(
            "SELECT payload_json FROM audit_log WHERE action = 'session_3.hardening'").fetchone()
    assert len(rows) == 1 and why in rows[0][0] and "pflanzer:threshold-override" in rows[0][0]
    assert len(audits) == 1 and "Dana Deciderová" in audits[0][0]
    assert '"threshold_override": {' in ship[0] and '"production_ready": true' in ship[0]

    log = (repo / ".pflanzer" / "decisions" / f"{slug}.md").read_text(encoding="utf-8")
    assert "Výjimka z prahu" in log and why in log
    report = Path(out["report_path"]).read_text(encoding="utf-8")
    assert "Výjimka z prahu" in report and "Ship na odpovědnost Decidera" in report

    ship_md = handoff_pr.render_ship_md(slug)
    assert "## Výjimka z prahu" in ship_md
    assert why in ship_md and "Dana Deciderová" in ship_md
    assert "--draft" in ship_md
    assert "BLOKOVÁNO" not in ship_md
    body = handoff_pr.build_pr(slug)["body"]
    assert "<summary>Výjimka z prahu</summary>" in body and why in body


def test_threshold_override_refused_when_score_meets_threshold(
        worktree_project: dict[str, Any], vote: Callable[..., Any]) -> None:
    # Score 100 >= threshold: nothing to override.
    vote(worktree_project["slug"], status="handoff")
    with pytest.raises(ValueError, match="Výjimku z prahu nepotřebuješ"):
        session_3.hardening_run(slug=worktree_project["slug"],
                                override_threshold=True, override_rationale="zbytečné")

