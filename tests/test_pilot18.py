"""Pilot 18 (Kvásek & syn, Lean, Express + EJS): texty feedbacku, otevřené připomínky k vítězi,
AI náhrada podle skutečného `--ai` podpisu, kosmetika."""
from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import (
    _compat,
    checkpoint,
    feedback,
    feedback_pull,
    handoff_pr,
    quick_session,
    retro,
    session,
    session_2,
    session_3,
    worktree,
)
from tool.cli.db import transaction

OWNERS = {"byznys": "Marie Kváskova", "produkt": "Eva Nováková", "design": "Petr Svoboda",
          "vyvoj": "Tomáš Dvořák", "bezpecnost": "Jana Černá", "provoz": "Karel Horák"}
LONG = ("Přehled objednávek je veřejný bez přihlášení a jméno a telefon jdou do cookie bez "
        "možnosti smazat. Doporučuji heslo na přehled a odkaz Zapomenout moje údaje.")


def _add(slug: str, variant: str, severity: str, text: str, dept: str = "Design",
         by: str = "Petr") -> int:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = ?",
            (slug, variant)).fetchone()[0]
        return int(conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, "
            "rationale, submitted_by) VALUES (?, ?, ?, 'general', 0.3, ?, ?)",
            (vid, severity, dept, text, by)).lastrowid)


@pytest.fixture
def voted(project: dict[str, Any], vote: Callable[..., Any]) -> dict[str, Any]:
    vote(project["slug"])
    return project


@pytest.fixture
def repo_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "target-repo"
    (repo / ".pflanzer").mkdir(parents=True)
    monkeypatch.chdir(repo)
    return repo


# --- 1. texty feedbacku -----------------------------------------------------------------------


def test_feedback_list_human_shows_text_sorted_and_resolved_apart(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    minor = _add(slug, "A", "low", "Drobnost v patičce")
    major = _add(slug, "B", "high", LONG, dept="Bezpečnost & právo", by="Jana Černá")
    crit = _add(slug, "C", "critical", "Platba padá")
    done = _add(slug, "A", "high", "Starý problém, už opravený")
    session_2.resolve_feedback(slug=slug, feedback_ids=[done], by="Tomáš", note="opraveno")
    rows = feedback.list_feedback(slug)
    title, lines, _nxt, _ctx = feedback._list_view(slug, rows)
    text = "\n".join(lines)
    assert "Platba padá" in text and "Drobnost v patičce" in text
    assert f"#{major} B · Bezpečnost & právo (Jana Černá) · Důležité · Přehled objednávek" in text
    # zkrácené na ~120 znaků, ne celé
    assert "Zapomenout moje údaje" not in text and "…" in text
    # pořadí critical -> major -> minor, vyřešené na konci
    pos = [text.index(f"#{i} ") for i in (crit, major, minor)]
    assert pos == sorted(pos)
    assert text.index(f"Vyřešeno #{done}") > text.index(f"#{minor} ")
    assert "opraveno" in text.split(f"Vyřešeno #{done}")[1]


def test_summary_md_has_full_texts_for_discovery_audit(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    _add(slug, "B", "high", LONG, dept="Bezpečnost & právo", by="Jana Černá")
    _add(slug, "A", "low", "Krátká poznámka")
    md = feedback_pull.render_summary_md(feedback_pull.aggregate(slug))
    assert "Připomínky podle varianty (plné texty)" in md
    assert LONG in md and "Krátká poznámka" in md      # plné znění, ne zkrácené
    assert "### Varianta A" in md and "### Varianta B" in md
    # lidský výstup feedback_pull ukazuje text také
    agg = feedback_pull.aggregate(slug)
    assert any("Přehled objednávek" in ln for ln in feedback_pull._human(agg, None)[1])


def test_prep_shows_top_three_disputes_with_text(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    _add(slug, "A", "low", "Nízká věc", dept="Provoz")
    _add(slug, "A", "high", "Tlačítko Zpět je u Další", dept="Design")
    _add(slug, "B", "high", "Druhá věc o designu", dept="Design")
    _add(slug, "B", "high", LONG, dept="Bezpečnost & právo")
    _add(slug, "C", "medium", "Střední věc", dept="Provoz")
    prep = session_2.prep(slug)
    disputes = prep["top_disputes"]
    assert len(disputes) == 3
    assert all(d["severity"] == "high" for d in disputes)
    # při shodě závažnosti vede nejčastější téma (Design ×2)
    assert [d["department"] for d in disputes][:2] == ["Design", "Design"]
    lines = session_2._prep_view(prep)[1]
    joined = "\n".join(lines)
    assert "Spor 1:" in joined and "Tlačítko Zpět je u Další" in joined


def test_discovery_detector_reads_summary_texts() -> None:
    doc = (Path(__file__).resolve().parents[1] / ".claude" / "agents"
           / "discovery-debt-detector.md").read_text(encoding="utf-8")
    cmd = (Path(__file__).resolve().parents[1] / ".claude" / "commands"
           / "pflanzer-feedback-pull.md").read_text(encoding="utf-8")
    assert "plné texty" in doc and "plné texty" in cmd


# --- 2. otevřené připomínky k vítězi ---------------------------------------------------------


def test_open_remarks_reach_decision_log_ship_md_and_pr(
        voted: dict[str, Any], repo_cwd: Path) -> None:
    slug = voted["slug"]
    major = _add(slug, "A", "high", "Formulář odmítne objednávku bez nápisu", by="Petr")
    _add(slug, "A", "low", "Drobnost v patičce", by="Eva")
    _add(slug, "B", "high", "Jen na poražené variantě", by="Jana")
    out = session_2.record_decision(slug=slug, decision="go", winner="A",
                                    rationale="A je nejrychlejší")
    assert [c["id"] for c in out["open_remarks"]][0] == major and len(out["open_remarks"]) == 2
    with transaction() as conn:
        body = conn.execute("SELECT body_md FROM decisions WHERE type = 'handoff'").fetchone()[0]
    assert "### Otevřené připomínky k vítězi" in body
    assert "(Důležité, Petr, krok Design)" in body and "Drobnost v patičce" in body
    assert "Jen na poražené variantě" not in body
    assert "otevřené připomínky k vítězi (neblokuje)" in "\n".join(session_2._decision_view(out)[1])

    pr = handoff_pr.build_pr(slug)
    assert "<summary>Otevřené připomínky k vítězi (neblokují merge)</summary>" in pr["body"]
    assert "- [ ] (Důležité, Petr) Formulář odmítne objednávku bez nápisu" in pr["body"]
    assert "- [ ] (Drobné, Eva) Drobnost v patičce" in pr["body"]
    assert "Jen na poražené variantě" not in pr["body"]
    ship = handoff_pr.render_ship_md(slug)
    assert "## Otevřené připomínky k vítězi" in ship
    assert "- [ ] (Důležité, Petr) Formulář odmítne objednávku bez nápisu" in ship
    # lidský výstup handoff_pr
    view = handoff_pr._human_ship_md(slug, repo_cwd / "SHIP.md")
    assert any("2 otevřené připomínky k vítězi (neblokuje)" in ln for ln in view["lines"])

    # resolve funguje i pro major/minor a připomínka zmizí ze SHIP.md i PR
    res = session_2.resolve_feedback(slug=slug, feedback_ids=[major], by="Tomáš", note="opraveno")
    assert res["resolved_severity"][major] == "high" and len(res["open_remarks_left"]) == 1
    pr2 = handoff_pr.build_pr(slug)
    assert "Formulář odmítne objednávku" not in pr2["body"]
    assert "(Drobné, Eva) Drobnost v patičce" in pr2["body"]


def test_resolve_cli_accepts_major_feedback_id(
        voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    fid = _add(slug, "A", "high", "Něco k opravě")
    monkeypatch.setattr(sys, "argv", ["session_2", "resolve", "--slug", slug, "--feedback-id",
                                      str(fid), "--by", "Tomáš", "--note", "opraveno v PR #1"])
    session_2.main()
    out = capsys.readouterr().out
    assert f"Vyřešeno: #{fid}" in out


def test_ship_output_line_for_open_remarks() -> None:
    out = {"winner": {"variant": "A", "summary_line": "ok", "gate_score": 90,
                      "failures": [], "next_step": "dál"},
           "production_readiness_target": 80, "triage": {}, "production_ready": True,
           "open_remarks": [{"id": 1}, {"id": 2}, {"id": 3}], "informational": False,
           "report_nice_path": "~/x"}
    _t, lines, *_ = session_3._human_ship(out, "x")
    assert any("3 otevřené připomínky k vítězi (neblokuje)" in ln for ln in lines)
    assert session_2.remarks_line(5) == "5 otevřených připomínek k vítězi (neblokuje)"


# --- 3. AI náhrada podle skutečného --ai ------------------------------------------------------


def _lean(bare: Path, slug: str = "kvasek", **kw: Any) -> dict[str, Any]:
    kw.setdefault("path_owners", dict(OWNERS))
    kw.setdefault("core", ["Eva Nováková", "Petr Svoboda", "Tomáš Dvořák"])
    return bootstrap_project(slug=slug, target_repo_url=file_url(bare), tier="lean", **kw)


def test_foreign_human_signature_is_not_ai_stand_in(tmp_db: Path, bare_repo: Path) -> None:
    """Pilot Kvásek: Provoz podepsal Tomáš (zástup za Karla), `--ai` nebylo -> žádná AI náhrada."""
    _lean(bare_repo)
    out = checkpoint.sign("kvasek", "provoz", by="Tomáš Dvořák", note="rollback = revert merge")
    assert out["signed_by_role"] == "zástup" and not out["ai"]
    assert _compat.ai_stand_in_line("kvasek") is None
    assert "Provoz: Tomáš Dvořák (zástup)" in (_compat.signatures_line("kvasek") or "")
    pr = handoff_pr.build_pr("kvasek")
    assert "AI náhradou" not in pr["body"] and not pr["ai_stand_in"]
    assert "AI náhradou" not in handoff_pr.render_ship_md("kvasek")
    project = _project_row("kvasek")
    assert retro.ai_stand_in_share(project)["ai_steps"] == []
    assert retro._ai_stand_in_text(retro.ai_stand_in_share(project)).startswith("0 z 6")


def _project_row(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        return dict(conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone())


def test_real_ai_signature_counts_in_ship_pr_and_retro(tmp_db: Path, bare_repo: Path) -> None:
    _lean(bare_repo)
    checkpoint.sign("kvasek", "provoz", ai=True, agent="devops-expert", note="AI pre-check")
    line = _compat.ai_stand_in_line("kvasek") or ""
    assert "Provoz: AI (devops-expert), čeká na podpis člověka" in line
    checkpoint.sign("kvasek", "provoz", by="Tomáš Dvořák", note="rollback ověřen")
    line = _compat.ai_stand_in_line("kvasek") or ""
    assert "Provoz: AI (devops-expert), potvrdil Tomáš Dvořák" in line
    pr = handoff_pr.build_pr("kvasek")
    assert line in pr["body"] and line in handoff_pr.render_ship_md("kvasek")
    share = retro.ai_stand_in_share(_project_row("kvasek"))
    assert share["ai_steps"] == ["provoz"] and share["total_steps"] == 6


def test_owner_ai_counts_even_when_human_signs_directly(tmp_db: Path, bare_repo: Path) -> None:
    _lean(bare_repo, path_owners={**OWNERS, "design": "AI:ux-expert"})
    assert "Design: AI (ux-expert)" in (_compat.ai_stand_in_line("kvasek") or "")
    share = retro.ai_stand_in_share(_project_row("kvasek"))
    assert share["ai_steps"] == ["design"] and share["pct"] == 17
    assert "Design: AI (ux-expert)" in handoff_pr.build_pr("kvasek")["body"]


# --- kosmetika --------------------------------------------------------------------------------


def test_builder_prompt_calls_feature_a_scenario_skeleton() -> None:
    src = Path(quick_session.__file__).read_text(encoding="utf-8")
    assert "Deciderovo zadání" not in src
    assert "kostra akceptačních scénářů — doplň konkrétní scénáře podle Charteru" in src


def test_vote_hint_and_errors_explain_role_idx_vs_steps() -> None:
    tpl = worktree.vote_template("x", ["A"])
    hint = tpl["_napoveda"]
    assert "02-role-catalog.md" in hint and "NE číslo kroku cesty 1–6" in hint
    assert "6 = UX" in hint
    err = session.rp_range_errors({"role_idx": 19})[0]
    assert "ne číslo kroku cesty 1–6" in err
    assert "NE číslo kroku cesty 1–6" in " ".join(quick_session.VOTE_EPILOG.split())


def test_retro_command_formats_match_reminders_cli() -> None:
    cmd = (Path(__file__).resolve().parents[1] / ".claude" / "commands"
           / "pflanzer-retro.md").read_text(encoding="utf-8")
    row = next(ln for ln in cmd.splitlines() if ln.startswith("| `reminders`"))
    assert "--format ics" in row and "--format md" in row and "--format gh-issues" in row
    assert "nebo checklist" not in row


def test_hub_protected_preview_has_text_and_button() -> None:
    src = (Path(__file__).resolve().parents[1] / "tool" / "web" / "frontend" / "src" / "pages"
           / "CompareVariants.tsx").read_text(encoding="utf-8")
    assert "Náhled je za heslem — klikněte na Otevřít náhled" in src
    assert "protectedPreview" in src
