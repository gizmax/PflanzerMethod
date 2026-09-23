"""quick_session: bootstrap (multi-repo), builder prompts, voting persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import bootstrap_project

from tool.cli import quick_session
from tool.cli.db import transaction


def _project_row(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        return dict(conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone())


def test_bootstrap_multi_repo_text(tmp_db: Path, tmp_path: Path) -> None:
    fe = f"file://{tmp_path}/origin/web.git"
    be = f"file://{tmp_path}/origin/api.git"
    out = bootstrap_project(slug="multi", target_repos=f"fe={fe}#main:apps/web,be={be}")
    assert out["target_repo_url"] == fe
    assert [r["role"] for r in out["target_repos"]] == ["fe", "be"]

    row = _project_row("multi")
    assert row["target_repo_url"] == fe
    assert row["status"] == "triage"
    repos = json.loads(row["target_repos"])
    assert repos == [
        {"role": "fe", "url": fe, "branch": "main", "workspace": "apps/web"},
        {"role": "be", "url": be, "branch": "main"},
    ]
    with transaction() as conn:
        tracks = dict(conn.execute(
            "SELECT track, status FROM triage WHERE project_id = ?", (row["id"],),
        ).fetchall())
    assert tracks == {t: "deferred" for t in ("discovery", "security", "legal", "platform")}


def test_bootstrap_rejects_invalid_url(tmp_db: Path) -> None:
    with pytest.raises(ValueError, match="není platná git URL"):
        bootstrap_project(slug="bad-url", target_repo_url="ftp//not-a-repo")


def test_bootstrap_pilot_requires_target_repo(tmp_db: Path) -> None:
    with pytest.raises(ValueError, match="target_repo_url je povinný"):
        bootstrap_project(slug="no-repo", target_repo_url=None)


def test_bootstrap_throwaway_gets_rationale(tmp_db: Path) -> None:
    bootstrap_project(risk_profile="throwaway", slug="demo")
    row = _project_row("demo")
    assert row["throwaway_or_evolve"] == "throwaway"
    assert row["throwaway_rationale"].startswith("discovery-only pilot")


def test_builder_prompts_angles_and_be_hint(tmp_db: Path, tmp_path: Path) -> None:
    fe = f"file://{tmp_path}/origin/web.git"
    be = f"file://{tmp_path}/origin/api.git"
    bootstrap_project(slug="prompts", target_repos=f"fe={fe},be={be}")
    out = quick_session.builder_prompts("prompts", "Rychlejší checkout")
    assert out["blocked"] is False
    prompts = out["prompts"]
    assert [p["name"] for p in prompts] == ["A", "B", "C"]
    assert len({p["angle"] for p in prompts}) == 3
    assert len({p["prompt_text"] for p in prompts}) == 3
    for p in prompts:
        assert quick_session.BE_CONTRACT_FIRST in p["prompt_text"]
        assert f"prompts-{p['name']}-be" in p["prompt_text"]


def test_builder_prompts_single_repo_has_no_be_hint(project: dict[str, Any]) -> None:
    out = quick_session.builder_prompts(project["slug"], "Rychlejší checkout", n_variants=2)
    assert len(out["prompts"]) == 2
    assert all(quick_session.BE_CONTRACT_FIRST not in p["prompt_text"] for p in out["prompts"])


def test_record_voting_persists_diff_summary(project: dict[str, Any],
                                             vote: Callable[..., Any]) -> None:
    diff = {"stat": "3 files changed, 120 insertions(+)", "touched_existing": ["src/Form.tsx"],
            "reuse": "Form komponenta", "new": "Wizard krok", "mock": "platba je stub",
            "acceptance_pass": "3/4"}
    out = vote(project["slug"], diff_summary=diff)
    a = next(v for v in out["variants"] if v["name"] == "A")
    assert "src/Form.tsx" in a["diff_summary_md"]
    with transaction() as conn:
        rows = dict(conn.execute("SELECT name, diff_summary_md FROM variants").fetchall())
        status = conn.execute("SELECT status FROM projects WHERE slug = ?",
                              (project["slug"],)).fetchone()[0]
    assert "**Mock / stub**: platba je stub" in rows["A"]
    assert "**Acceptance pass**: 3/4" in rows["A"]
    assert rows["B"] is None
    assert status == "session_1"
    # A had the highest user_value -> highest preference score.
    scores = {v["name"]: v["preference_score"] for v in out["variants"]}
    assert scores["A"] > scores["B"] > scores["C"]
