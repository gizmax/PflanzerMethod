"""Pilot 27: poctivé skóre, otevřené připomínky napříč projektem, lidské názvy kontrol, čeština."""
from __future__ import annotations

from typing import Any, Callable

from tool.cli import handoff_pr, report, session_2
from tool.cli import quality_gates as qg
from tool.cli.db import transaction


def _fb(slug: str, variant: str, severity: str, text: str, by: str = "Petra") -> None:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = ?",
            (slug, variant)).fetchone()[0]
        conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, rationale, "
            "submitted_by) VALUES (?, ?, 'ux', 'form', 0.5, ?, ?)", (vid, severity, text, by))


# --- helpery ---------------------------------------------------------------------------


def test_gate_human_and_unverified_text() -> None:
    assert qg.gate_human("observability") == "observabilita (logy a metriky pro provoz)"
    assert qg.gate_human("a11y") == "přístupnost (WCAG)"
    assert qg.gate_human("smoke") == "spuštění aplikace"
    assert qg.gate_human("lint") == "lint"
    text = qg.unverified_human({"gate": "coverage", "reason": "chybí coverage nástroj"})
    assert text == "pokrytí testy — neměřeno, chybí nástroj (c8 / pytest-cov)"


def test_score_sentence_has_no_jargon() -> None:
    s = qg.score_sentence(98, 80, 8, ["typová kontrola"], "splňuje práh")
    assert "Spočteno z 8 automatických kontrol." in s and "branami" not in s
    assert "ze 4 automatických kontrol" in qg.score_sentence(90, 80, 4)
    assert "z 1 automatické kontroly" in qg.score_sentence(90, 80, 1)


def test_warned_gates_are_human() -> None:
    got = qg.warned_gates([{"gate": "observability", "status": "warn"},
                           {"gate": "a11y", "status": "warn"}])
    assert got == ["observabilita (logy a metriky pro provoz)", "přístupnost (WCAG)"]


def test_czech_counts() -> None:
    assert handoff_pr._lines_added(1) == "+1 řádek"
    assert handoff_pr._lines_added(2) == "+2 řádky"
    assert handoff_pr._lines_added(5) == "+5 řádků"
    one = handoff_pr.open_feedback_lines(
        {"total": 1, "winner": [{"severity": "high", "variant": "A", "rationale": "x",
                                 "submitted_by": "P", "id": 1}], "others": [], "has_winner": True},
        "s")
    assert one[0].startswith("1 otevřená připomínka:")


def test_pr_title_never_cut_mid_word_nor_ellipsis() -> None:
    t = handoff_pr._short_pr_title(
        "Předvyplněná nejčastější kytice a zítřejší datum, uživatel jen potvrdí objednávku", 60)
    assert t == "Předvyplněná nejčastější kytice a zítřejší datum"
    long = handoff_pr._short_pr_title("slovo " * 30, 60)
    assert "…" not in long and len(long) <= 60 and not long.endswith("slov")


def test_digest_orders_by_severity_and_splits_winner() -> None:
    crit = [{"id": 9, "variant": "B", "rationale": "kritické", "submitted_by": "K"}]
    def r(i: int, v: str, sev: str, text: str) -> dict[str, Any]:
        return {"id": i, "variant": v, "severity": sev, "rationale": text, "submitted_by": "P"}

    rem = [r(1, "A", "low", "drobnost"), r(2, "A", "high", "adresa"), r(3, "C", "high", "jiné")]
    d = handoff_pr.open_feedback_digest(crit, rem, "A")
    assert d["total"] == 4
    assert [c["id"] for c in d["winner"]] == [2, 1]
    assert [c["id"] for c in d["others"]] == [9, 3]
    text = "\n".join(handoff_pr.open_feedback_lines(d, "s"))
    assert "4 otevřené připomínky: 2 na vítězi (k vyřešení), 2 na ostatních variantách" in text
    assert "Zkontrolujte, jestli se netýkají i vítěze" in text
    others = text.split("Zkontrolujte, jestli se netýkají i vítěze:")[1]
    assert others.index("Kritické") < others.index("Důležité")


# --- SHIP.md a PR ----------------------------------------------------------------------


def test_ship_md_disclaimer_feedback_and_tense(worktree_project: dict[str, Any],
                                               vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug, status="handoff")
    _fb(slug, "A", "high", "Chybí pole pro adresu doručení")
    _fb(slug, "B", "high", "Adresa se neukládá")
    md = handoff_pr.render_ship_md(slug)
    assert handoff_pr.SCORE_DISCLAIMER in md
    assert "ne to, jestli varianta splní zadání" in md
    assert "## Otevřené připomínky" in md
    assert "2 otevřené připomínky: 1 na vítězi (k vyřešení), 1 na ostatních variantách" in md
    assert "Chybí pole pro adresu doručení" in md and "Adresa se neukládá" in md
    assert "Spočteno nad" not in md and "branami" not in md
    assert "Ověřili jsme" not in md and "Ověříme" not in md
    assert len(md.splitlines()) <= 60
    assert "…" not in handoff_pr.build_pr(slug)["title"]


def test_ship_md_without_remarks_says_so(worktree_project: dict[str, Any],
                                         vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug, status="handoff")
    md = handoff_pr.render_ship_md(slug)
    assert "Otevřené připomínky: žádné." in md
    assert len(md.splitlines()) <= 60


def test_pr_body_uses_same_tense_and_plurals(worktree_project: dict[str, Any],
                                             vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug, status="handoff")
    _fb(slug, "A", "low", "Drobnost")
    body = handoff_pr.build_pr(slug)["body"]
    assert "Ověříme" not in body
    assert "1 otevřená připomínka (neblokují merge)" in body


# --- report ----------------------------------------------------------------------------


def test_report_has_disclaimer_feedback_and_full_reason(worktree_project: dict[str, Any],
                                                        vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug)
    _fb(slug, "A", "high", "Chybí pole pro adresu doručení")
    _fb(slug, "C", "high", "Jiná varianta má stejný problém")
    reason = ("A vede o dost, ale riziko: platební brána je zatím jen v testovacím režimu "
              "a doručení do zahraničí není ošetřené, což musíme vyřešit před spuštěním")
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale=reason)
    md = report.render_summary_md(report.collect(slug))
    assert "## Otevřené připomínky" in md
    assert "Chybí pole pro adresu doručení" in md and "Jiná varianta má stejný problém" in md
    assert "doručení do zahraničí není ošetřené" in md and "…" not in md.split("## Rizika")[0]
    assert "Zkontrolujte, jestli se netýkají i vítěze" in md
