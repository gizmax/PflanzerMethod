"""Nálezy z pilotu „Šlápni" (Flask, hlavní cesta): šablona hlasování, autor feedbacku."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from tool.cli import feedback, session_2, worktree


def test_vote_template_leaves_commitment_to_people() -> None:
    tpl = worktree.vote_template("x", worktree.PARALLEL_VARIANTS)
    rps = [rp for v in tpl["votes"] for rp in v["role_preferences"]]
    assert rps and all(rp["commitment_level"] is None for rp in rps)
    assert "commitment_level" in tpl["_napoveda"] and "60 %" in tpl["_napoveda"]


def test_go_below_commitment_points_to_vote_not_feedback(
        project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    from tool.cli.db import transaction
    vote(slug)
    with transaction() as conn:
        conn.execute("UPDATE role_preferences SET commitment_level = 0")
    with pytest.raises(ValueError) as exc:
        session_2.record_decision(slug=slug, decision="go", winner="A", rationale="A")
    msg = str(exc.value)
    assert "commitment_level" in msg and "vote --spec" in msg and "feedback_pull" not in msg


def test_feedback_without_author_is_refused(project: dict[str, Any], vote: Callable[..., Any],
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    vote(project["slug"])
    monkeypatch.setattr(feedback, "current_actor", lambda: "unknown")
    with pytest.raises(ValueError, match="--by"):
        feedback.add_feedback(slug=project["slug"], variant="A", role="Produkt", severity="major",
                     text="Tlačítko Zpět nic nedělá")
