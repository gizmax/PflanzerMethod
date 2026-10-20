"""Jednotné názvy závažnosti (Kritické / Důležité / Drobné) a čitelné decision logy."""
from __future__ import annotations

from tool.cli import feedback_pull, session_2
from tool.cli.ux import group_severity_counts, normalize_severity, severity_label


def test_three_level_labels() -> None:
    assert [severity_label(k) for k in ("critical", "high", "medium", "low")] == [
        "Kritické", "Důležité", "Drobné", "Drobné"]


def test_cli_inputs_and_db_values_unchanged() -> None:
    given = ("critical", "major", "high", "medium", "minor", "low")
    assert [normalize_severity(x) for x in given] == [
        "critical", "high", "high", "medium", "low", "low"]


def test_medium_and_low_merge_in_counts() -> None:
    assert group_severity_counts({"critical": 1, "high": 2, "medium": 1, "low": 3}) == {
        "critical": 1, "high": 2, "low": 4}
    assert feedback_pull.severity_text({"high": 1, "medium": 1, "low": 1}) == "Důležité 1, Drobné 2"


def test_remarks_checklist_uses_czech_labels() -> None:
    items = [{"severity": "high", "level": "major", "submitted_by": "Petr", "rationale": "Chybí X"},
             {"severity": "medium", "level": "minor", "submitted_by": None, "rationale": "Y"}]
    assert session_2.remarks_checklist(items) == [
        "- [ ] (Důležité, Petr) Chybí X", "- [ ] (Drobné, autor neznámý) Y"]


def test_decision_md_has_no_duplicate_decision_line() -> None:
    md = session_2.render_decision_md("demo", "go", "Důvod", "Tom", None, winner="A")
    assert "- **Rozhodnutí**:" not in md
    assert "## Rozhodnutí — " in md and "**GO**" not in md
