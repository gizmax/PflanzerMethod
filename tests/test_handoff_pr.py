"""SHIP.md (handoff_pr): trailers, labels, AI provenance, winner basis."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import git

from tool.cli import handoff_pr, session_3


@pytest.fixture
def shipped(worktree_project: dict[str, Any], vote: Callable[..., Any]) -> dict[str, Any]:
    slug = worktree_project["slug"]
    wt = worktree_project["worktrees"]["A"]
    (wt / "checkout.js").write_text("export const fastCheckout = () => true;\n",
                                    encoding="utf-8")
    git(wt, "add", "checkout.js")
    git(wt, "commit", "-q", "-m", "feat: fast checkout")
    vote(slug, status="handoff")
    session_3.hardening_run(slug=slug)
    return worktree_project


def test_ship_md_contents(shipped: dict[str, Any]) -> None:
    slug = shipped["slug"]
    md = handoff_pr.render_ship_md(slug)
    assert md.startswith("Pflanzer Method | pflanzer.cz/method")
    assert f"Pflanzer-Variant: {slug}-A" in md
    assert "Pflanzer-Session: ship" in md
    assert "AI-Assisted: claude-code" in md
    assert '--label "ai-generated"' in md
    assert f'--label "pflanzer:{slug}"' in md
    assert "## AI provenance" in md
    assert "**Vybrán podle**: Ship gate" in md
    assert "Co-Authored-By: Claude" not in md
    # Blocked (deferred triage + 2 gates) -> draft PR, blocked verdict.
    assert "BLOKOVÁNO" in md
    assert "--draft" in md
    # Clean provenance on the winner branch.
    assert "má trailery, autor = člověk" in md
    # Co dál: one T+1d row (deploy preview + retro).
    assert md.count("- **T+1d**") == 1


def test_write_ship_switches_session(shipped: dict[str, Any]) -> None:
    path = handoff_pr.write_ship(shipped["slug"])
    assert path.is_file()
    wt = shipped["worktrees"]["A"]
    assert git(wt, "config", "--worktree", "--get", "pflanzer.session") == "ship"


def test_check_provenance_warns_on_ai_coauthor(shipped: dict[str, Any]) -> None:
    slug = shipped["slug"]
    wt: Path = shipped["worktrees"]["A"]
    (wt / "more.js").write_text("export const more = 1;\n", encoding="utf-8")
    git(wt, "add", "more.js")
    git(wt, "commit", "-q", "-m",
        "feat: more\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    prov = handoff_pr.check_provenance(
        slug=slug, variant="A", builder="claude-code", target_branch="main", worktree=wt,
    )
    assert prov["checked"] is True
    assert prov["commits"] == 2
    assert prov["authors"] == ["Test Dev"]
    assert any("Co-Authored-By" in w for w in prov["warnings"])


def test_check_provenance_flags_missing_trailers(shipped: dict[str, Any]) -> None:
    slug = shipped["slug"]
    wt: Path = shipped["worktrees"]["A"]
    (wt / "raw.js").write_text("export const raw = 1;\n", encoding="utf-8")
    git(wt, "add", "raw.js")
    git(wt, "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "feat: no hook")
    prov = handoff_pr.check_provenance(
        slug=slug, variant="A", builder="claude-code", target_branch="main", worktree=wt,
    )
    assert any("Pflanzer-Variant" in w for w in prov["warnings"])
    assert any("AI-Assisted" in w for w in prov["warnings"])
