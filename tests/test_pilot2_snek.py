"""Nálezy z pilotu „Šnek Servis": Iterate, podpis AI kroku, příprava Rozhodnutí."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from tool.cli import checkpoint, session_2, status
from tool.cli.db import transaction


@pytest.fixture
def voted(project: dict[str, Any], vote: Callable[..., Any]) -> dict[str, Any]:
    vote(project["slug"])
    return project


def _add_critical(slug: str, variant: str) -> int:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = ?",
            (slug, variant),
        ).fetchone()[0]
        return int(conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, "
            "rationale, submitted_by) VALUES (?, 'critical', 'security', 'gdpr', 0.1, "
            "'Kontakt bez souhlasu', 'Pavel')", (vid,),
        ).lastrowid)


def test_after_iterate_dropped_variants_do_not_block(voted: dict[str, Any],
                                                     vote: Callable[..., Any]) -> None:
    slug = voted["slug"]
    _add_critical(slug, "A")
    _add_critical(slug, "C")
    session_2.record_decision(slug=slug, decision="iterate", rationale="Jen C",
                              iterate_focus="souhlas")
    # Iterate: critical neblokuje další krok — Build kolo ho má opravit.
    assert status.project_detail(slug)["next_step"].startswith("/pm build")
    vote(slug, names=("C",))          # druhé Build kolo jen s C
    st = status.project_detail(slug)
    kinds = [(b["kind"], b.get("variant")) for b in st["blockers"]]
    assert ("critical", "C") in kinds
    assert ("critical", "A") not in kinds   # A skončila
    assert any("skončila" in i for i in st["info"])


def test_prep_offers_iterate_for_critical(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    _add_critical(slug, "A")   # A je na shortlistu (A, B)
    out = session_2.prep(slug)
    view = session_2._prep_view(out)
    text = str(view or out)
    assert "iterate" in text.lower()


def test_decider_confirming_ai_draft_is_zastupce() -> None:
    owners = {"byznys": "Pavel Šnek", "produkt": "Lenka", "vyvoj": "Marek",
              "bezpecnost": "AI:security-expert"}
    kind = checkpoint._signer_kind("bezpecnost", "Pavel Šnek", owners["bezpecnost"],
                                   owners, [], ai=False)
    assert kind == "zástupce"
    kind_other = checkpoint._signer_kind("bezpecnost", "Někdo Cizí", owners["bezpecnost"],
                                         owners, [], ai=False)
    assert kind_other == "zástup"
