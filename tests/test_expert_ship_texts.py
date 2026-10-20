"""Expertní panel (UX writer + EM): lidské texty Shipu - skóre, BLOKOVÁNO, PR body, chyby."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

import pytest
from conftest import git

from tool.cli import handoff_pr, quality_gates, session_3


def _res(**status: str) -> list[Any]:
    return [SimpleNamespace(gate_type=g, status=s, details="" if s != "skipped" else "SKIP: n/a")
            for g, s in status.items()]


def test_score_sentence_below_threshold_names_unverified_in_czech() -> None:
    res = _res(build="pass", tests="pass", lint="pass", smoke="pass", security="pass",
               types="skipped", coverage="skipped", a11y="skipped")
    line = quality_gates.gates_summary_line(78, res, target=80)
    assert line.startswith("**Skóre 78 ze 100 — pod prahem 80.**")
    assert "Spočteno z 5 automatických kontrol." in line
    assert "Neověřeno: typová kontrola, pokrytí testy, přístupnost (WCAG)." in line


def test_score_sentence_meets_threshold_and_informational() -> None:
    res = _res(build="pass", tests="pass", lint="pass", smoke="pass", security="pass")
    assert quality_gates.gates_summary_line(89, res, target=85).startswith(
        "**Skóre 89 ze 100 — splňuje práh 85.** Spočteno z 5 automatických kontrol.")
    assert "Neověřeno" not in quality_gates.gates_summary_line(89, res, target=85)
    assert quality_gates.gates_summary_line(60, res, target=0).startswith(
        "**Skóre 60 ze 100 — informativní, neblokuje.**")


def test_score_sentence_is_honest_with_few_gates() -> None:
    line = quality_gates.gates_summary_line(100, _res(build="pass", tests="pass"), target=80)
    assert "Spočteno jen ze 2 automatických kontrol — orientační." in line
    assert "práh 80 nelze potvrdit" in line
    assert "jen ze 4 automatických kontrol — orientační" in quality_gates.gates_summary_line(
        100, _res(build="pass", tests="pass", lint="pass", smoke="pass"))


def test_gate_labels_cover_all_gate_types() -> None:
    assert set(quality_gates.GATE_TYPES) <= set(quality_gates.GATE_LABELS)
    assert quality_gates.gate_label("a11y") == "přístupnost"


def test_unsigned_windows_name_owner_and_command_on_own_line() -> None:
    wins = [{"window": "zadani", "label": "Zadání", "state": "missing", "owner": "Dana D.",
             "signed_by": None},
            {"window": "provoz", "label": "Provoz", "state": "pending", "owner": None,
             "signed_by": None}]
    lines = handoff_pr._unsigned_window_lines("kv", wins)
    assert "Dana D." in lines[0] and "`zadani`" in lines[0]
    assert "pflanzer checkpoint" not in lines[0]
    assert lines[1].strip().startswith("`pflanzer checkpoint --slug kv zadani")
    assert "jméno chybí v Kickoffu" in lines[2] and "AI draft" in lines[2]


def test_collapse_sections_wraps_in_details_and_keeps_footer() -> None:
    out = handoff_pr._collapse_sections(
        ["## Co selhalo", "- x", "", "## Decider", "Dana", "", "---", "*pata*"])
    text = "\n".join(out)
    assert "<details open><summary>Co selhalo</summary>" in text
    assert "<details><summary>Decider</summary>" in text
    assert text.count("</details>") == 2
    assert text.endswith("---\n*pata*")


def test_pr_lead_three_lines() -> None:
    lead = handoff_pr._pr_lead(
        hook="Rychlejší checkout", winner="A", open_crit=1, open_remarks=0, open_conditions=2,
        failures=0, override=None, overridden=False,
        unverified=[{"gate": "acceptance", "reason": "x"}], blocked_by=[], metric=None)
    assert lead[0] == "**Co to je:** Rychlejší checkout (varianta A)"
    assert lead[1].startswith("**Co ověřit:** 1 otevřená kritická připomínka na vítězi")
    assert "2 podmínky z podpisů oken" in lead[1]
    assert lead[2] == "**Rizika:** neověřeno: akceptační testy"


def test_ship_errors_are_human_and_have_next_step() -> None:
    msg = session_3._before_ship_step("session_2", "kv")
    assert "pflanzer decide --slug kv go --winner X" in msg
    assert "status=" not in msg and "session_2" not in msg
    with pytest.raises(ValueError, match="Přebití chybějících podpisů potřebuje důvod"):
        session_3.hardening_run(slug="kv", override_triage=True)
    with pytest.raises(ValueError, match="Ship pod prahem potřebuje důvod"):
        session_3.hardening_run(slug="kv", override_threshold=True)


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


def test_pr_body_starts_with_lead_and_collapses_sections(shipped: dict[str, Any]) -> None:
    body = handoff_pr.build_pr(shipped["slug"])["body"]
    lines = body.splitlines()
    assert lines[2].startswith("**Co to je:**")
    assert lines[3].startswith("**Co ověřit:**") and lines[4].startswith("**Rizika:**")
    assert "<details" in body and body.count("<details") == body.count("</details>")
    assert "**Skóre " in body and " ze 100" in body
    assert "Override critical" not in body
