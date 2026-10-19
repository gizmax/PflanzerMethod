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
    # v0.5 brand line is bold (`**Pflanzer Method | pflanzer.cz/method**`).
    assert md.startswith("**Pflanzer Method | pflanzer.cz/method**")
    assert f"Pflanzer-Variant: {slug}-A" in md
    assert "Pflanzer-Session: ship" in md
    assert "AI-Assisted: claude-code" in md
    assert '--label "ai-generated"' in md
    assert f'--label "pflanzer:{slug}"' in md
    assert "## Původ kódu a podíl AI" in md
    assert "## AI náklady (viditelnost)" in md  # N16: always present, never fails
    assert "**Vybrán podle**: Ship -" in md
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


# --- PR / SHIP.md bez placeholderů ------------------------------------------------------

PLACEHOLDERS = ("doplň", "doplnit", "nezadán", "nezadáno", "YOUR-GH-HANDLE",
                "Instrumentace hotová", "sandbox.invalid")


def test_pr_body_and_ship_have_no_placeholders(shipped: dict[str, Any]) -> None:
    slug = shipped["slug"]
    pr = handoff_pr.build_pr(slug)
    md = handoff_pr.render_ship_md(slug)
    for text in (pr["body"], md):
        for ph in PLACEHOLDERS:
            assert ph not in text, f"placeholder {ph!r} v textu určeném lidem"
    assert "Brány:" in pr["body"] and "/100" in pr["body"]
    # 2 běžící brány -> poctivá jedna věta, ne tučně
    assert pr["gates_summary"] == "100/100 jen ze 2 bran — orientační"
    assert "**100/100" not in pr["body"]


def test_shadow_pdm_falls_back_to_path_owner(shipped: dict[str, Any]) -> None:
    from tool.cli.db import transaction

    slug = shipped["slug"]
    with transaction() as conn:
        conn.execute("UPDATE projects SET shadow_pm = NULL, path_owners_json = ? WHERE slug = ?",
                     ('{"produkt": "Eva Produktová"}', slug))
    md = handoff_pr.render_ship_md(slug)
    assert "Shadow PdM" in md and "Eva Produktová" in md


def test_open_critical_on_losing_variant_is_informative(shipped: dict[str, Any]) -> None:
    from tool.cli.db import transaction

    slug = shipped["slug"]
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = 'B'",
            (slug,)).fetchone()[0]
        conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, rationale, "
            "submitted_by) VALUES (?, 'critical', 'Bezpečnost & právo', 'auth', 0.1, "
            "'B posílá hesla v URL', 'Lucie')", (vid,))
    body = handoff_pr.build_pr(slug)["body"]
    assert "Informativně, poražená varianta" in body and "Lucie" in body


def test_trim_words_and_failure_line() -> None:
    long = "Rychlejší objednávkový proces pro firemní zákazníky s mnoha pobočkami a schvalováním"
    cut = handoff_pr.trim_words(long, 40)
    assert len(cut) <= 40 and long.startswith(cut) and not cut.endswith(" ")
    assert cut.split()[-1] in long.split()  # nekončí uprostřed slova
    out = ("tests/test_x.py:12: in test_total\n    assert total() == 5\n"
           "E   assert 4 == 5\nE    +  where 4 = total()\n")
    assert handoff_pr.failure_line(out) == "assert 4 == 5"
