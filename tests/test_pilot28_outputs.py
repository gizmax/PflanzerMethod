"""Pilot 28: skóre nezavádí (částečné skóre v hlavní větě), PR pro recenzenta, retro z terminálu."""
from __future__ import annotations

from typing import Any, Callable

import pytest

from tool.cli import handoff_pr, report, retro, session_3
from tool.cli import quality_gates as qg


@pytest.fixture
def shipped(worktree_project: dict[str, Any], vote: Callable[..., Any]) -> dict[str, Any]:
    slug = worktree_project["slug"]
    vote(slug, status="handoff")
    session_3.hardening_run(slug=slug)
    return worktree_project


def test_partial_score_says_so_in_main_sentence() -> None:
    s = qg.score_sentence(100, 80, 6, ["pokrytí testy (nástroj na měření chybí)", "a", "b"],
                          "splňuje práh")
    assert s.startswith("**Skóre 100 ze 100 ze 6 automatických kontrol — 3 kontroly neproběhly, "
                        "skóre je proto jen částečné.**")
    assert "Splňuje práh 80." in s and "Neověřeno: " in s


def test_partial_score_czech_forms_and_open_remarks() -> None:
    one = qg.score_sentence(90, 80, 8, ["x"], "splňuje práh", open_on_winner=1)
    assert "1 kontrola neproběhla" in one and one.split("**")[1].endswith(
        "; na vítězi zůstává 1 otevřená připomínka.")
    five = qg.score_sentence(90, 80, 8, list("abcde"), "splňuje práh", open_on_winner=2)
    assert "5 kontrol neproběhlo" in five
    assert "; na vítězi zůstávají 2 otevřené připomínky.**" in five
    full = qg.score_sentence(95, 80, 8, [], "splňuje práh", open_on_winner=5)
    assert full.startswith("**Skóre 95 ze 100 — splňuje práh 80; na vítězi zůstává 5 otevřených "
                           "připomínek.**")
    assert "částečné" not in full


def test_unverified_text_has_no_jargon_outside_detail() -> None:
    cov = {"gate": "coverage", "reason": "chybí coverage nástroj"}
    a11y = {"gate": "a11y", "reason": "SPA"}
    assert qg.unverified_human(cov) == "pokrytí testy (nástroj na měření chybí)"
    assert "c8" in qg.unverified_human(cov, technical=True)
    t = qg.unverified_human(a11y)
    assert "zdravotním postižením" in t and "WCAG" not in t and "c8" not in t
    assert "jednostránková aplikace" in t and "ověřte ručně" in t and "SPA" not in t
    assert "WCAG" in qg.unverified_human(a11y, technical=True)


def test_gates_summary_line_partial_without_jargon() -> None:
    rows = [{"gate": g, "status": "pass", "details": ""} for g in ("build", "tests", "lint")]
    rows += [{"gate": "coverage", "status": "skipped",
              "details": "NEOVĚŘENO: chybí coverage nástroj — c8"},
             {"gate": "a11y", "status": "skipped",
              "details": "NEOVĚŘENO: SPA — bez headless prohlížeče nelze ověřit"}]
    line = qg.gates_summary_line(100, rows, target=80, verdict="splňuje práh", open_on_winner=2)
    assert "2 kontroly neproběhly, skóre je proto jen částečné; na vítězi zůstávají 2" in line
    assert "WCAG" not in line and "pytest-cov" not in line and "SPA" not in line


def test_pr_body_labels_for_reviewer(shipped: dict[str, Any]) -> None:
    pr = handoff_pr.build_pr(shipped["slug"])
    body = pr["body"]
    assert "Hlasování jádra" not in body and "- Brány:" not in body
    assert "- Automatické kontroly: " in body and " ze 100" in body
    if "Hodnocení jádra" in body:
        line = next(x for x in body.splitlines() if x.startswith("- Hodnocení jádra"))
        assert " z 1 (vyšší = lepší)" in line and "." not in line.split(":", 1)[1]


def test_ship_md_stays_short_and_plain(shipped: dict[str, Any]) -> None:
    md = handoff_pr.render_ship_md(shipped["slug"])
    assert len(md.splitlines()) <= 60
    assert "WCAG" not in md and "pytest-cov" not in md


def test_retro_report_footer_has_terminal_variant(shipped: dict[str, Any]) -> None:
    md = retro.render_report_md(shipped["slug"])
    assert f"pflanzer retro measure --slug {shipped['slug']} --pr-url" in md
    assert "--merge-commit" in md and "pflanzer retro record" in md


def test_report_next_step_has_terminal_measure(project: dict[str, Any]) -> None:
    md = report.render_summary_md(report.collect(project["slug"]))
    assert "pflanzer retro measure --slug" in md
