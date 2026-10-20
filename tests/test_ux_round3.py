"""3. kolo UX: Kill není slepá ulička, poctivé skóre, feedback_pull = prep, české chyby."""
from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tool.cli import checkpoint, feedback_pull, handoff_pr, quality_gates, retro, session_2
from tool.cli.db import transaction
from tool.cli.quality_gates import GateResult


def _critical(slug: str, variant: str, text: str = "Chybí kontrola oprávnění") -> int:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = ?",
            (slug, variant)).fetchone()[0]
        return int(conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, "
            "rationale, submitted_by) VALUES (?, 'critical', 'Bezpečnost', 'auth', 0.1, ?, "
            "'Lucie')",
            (vid, text)).lastrowid)


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


def _run(monkeypatch: pytest.MonkeyPatch, module: Any, *argv: str) -> None:
    monkeypatch.setattr(sys, "argv", [module.__name__, *argv])
    module.main()


# --- 1. Kill není slepá ulička --------------------------------------------------------------


def test_kill_log_has_lessons_and_all_criticals_and_human_next_step(
        voted: dict[str, Any], repo_cwd: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    for v in ("A", "B", "C"):
        _critical(slug, v, f"Problém na variantě {v}")
    _run(monkeypatch, session_2, "decide", "--slug", slug, "kill",
         "--rationale", "Uživatelé problém nemají")
    out = capsys.readouterr().out
    assert f"pflanzer retro lesson --slug {slug} --text" in out
    assert "10min demo" not in out and "Tiché hlasování" not in out
    assert "Kill je dobrý výsledek" in out  # tipy after_kill
    log = (repo_cwd / ".pflanzer" / "decisions" / f"{slug}.md").read_text(encoding="utf-8")
    assert "### Poučení" not in log     # prázdná šablona pryč; poučení dopíše `retro lesson`
    for v in ("A", "B", "C"):
        assert f"na variantě {v}" in log
    assert "Critical všech variant" in log
    with transaction() as conn:
        body = conn.execute("SELECT body_md FROM decisions WHERE type = 'kill'").fetchone()[0]
    assert "- \n" not in body


def test_retro_lesson_writes_db_and_decision_log(
        voted: dict[str, Any], repo_cwd: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    session_2.record_decision(slug=slug, decision="kill", rationale="Nikdo to nechce")
    capsys.readouterr()
    _run(monkeypatch, retro, "lesson", "--slug", slug, "--text", "Problém trápí jen vedení",
         "--by", "Dana")
    out = capsys.readouterr().out
    assert "Zapsáno poučení #1" in out
    _run(monkeypatch, retro, "lesson", "--slug", slug, "--text", "Zadání bylo příliš široké")
    assert "Zapsáno poučení #2" in capsys.readouterr().out
    with transaction() as conn:
        n = conn.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'retro.lesson'"
                         ).fetchone()[0]
    assert n == 2
    log = (repo_cwd / ".pflanzer" / "decisions" / f"{slug}.md").read_text(encoding="utf-8")
    assert "Problém trápí jen vedení" in log and "Zadání bylo příliš široké" in log
    assert [x["text"] for x in retro.lessons(slug)] == [
        "Problém trápí jen vedení", "Zadání bylo příliš široké"]


def test_retro_lesson_requires_text(voted: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="--text"):
        retro.lesson(slug=voted["slug"], text="  ")


def test_retro_report_for_killed_project_has_no_reminders(
        voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    session_2.record_decision(slug=slug, decision="kill", rationale="Nikdo to nechce")
    retro.lesson(slug=slug, text="Problém je jinde")
    capsys.readouterr()
    _run(monkeypatch, retro, "report", "--slug", slug)
    out = capsys.readouterr().out
    assert "Poučení #1: Problém je jinde" in out
    assert "T+7" not in out and "ics" not in out and "reminders" not in out
    md = (retro.RETRO_DIR / f"{slug}-retro.md").read_text(encoding="utf-8")
    assert "## Poučení" in md and "## Metriky Buildu" in md
    assert "T+7" not in md and "T+30" not in md
    assert "reminders" not in md
    with pytest.raises(ValueError, match="skončil Kill"):
        retro.render_reminders(slug, "ics")


# --- 2. Poctivé skóre --------------------------------------------------------------------------


def _gates(*, acceptance: str = "unverified", types: str = "skip") -> list[GateResult]:
    res = [GateResult(g, "pass", "ok") for g in ("build", "lint", "tests", "security",
                                                 "observability")]
    if acceptance == "unverified":
        res.append(GateResult("acceptance", "skipped",
                              "NEOVĚŘENO: chybí @playwright/test — scénáře se nespustily"))
    if types == "skip":
        res.append(GateResult("types", "skipped",
                              "SKIP: bez tsconfig.json - projekt není TypeScript"))
    return res


def test_summary_line_separates_unverified_from_not_applicable() -> None:
    line = quality_gates.gates_summary_line(100, _gates(types="none"))
    assert line == ("Skóre 100 ze 100. Spočteno z 5 automatických kontrol. "
                    "Neověřeno: akceptační testy — neměřeno, chybí @playwright/test.")
    both = quality_gates.gates_summary_line(100, _gates())
    assert both.startswith("Skóre 100 ze 100. Spočteno z 5 automatických kontrol. Neověřeno: "
                           "akceptační testy — neměřeno, chybí @playwright/test; typová kontrola")
    plain = quality_gates.gates_summary_line(100, _gates(acceptance="none", types="skip"))
    assert "Neověřeno: akceptační" not in plain and "typová kontrola" in plain


def test_verdict_has_warning_when_unverified_and_production_fails() -> None:
    unv = quality_gates.unverified_gates(_gates())
    assert unv == [{"gate": "acceptance", "reason": "chybí @playwright/test",
                    "detail": "scénáře se nespustily"}]
    pilot = quality_gates.verdict_label(100, 80, False, unv)
    assert pilot.startswith("splňuje práh (100/100 ≥ 80)") and "⚠" in pilot
    prod = quality_gates.verdict_label(100, 85, False, unv)
    assert prod.startswith("nesplňuje práh") and "acceptance" in prod
    assert "⚠" not in quality_gates.verdict_label(100, 80, False, [])


def test_acceptance_without_playwright_is_unverified_not_skip(tmp_path: Path) -> None:
    proj = tmp_path / "app"
    (proj / "tests" / "acceptance").mkdir(parents=True)
    (proj / "tests" / "acceptance" / "a.spec.ts").write_text("// scenario\n", encoding="utf-8")
    (proj / "package.json").write_text(json.dumps({"name": "app", "scripts": {}}),
                                       encoding="utf-8")
    res = {r.gate_type: r for r in quality_gates.run_gates_on_path(proj)}
    assert res["acceptance"].status == "skipped"
    assert res["acceptance"].details.startswith("NEOVĚŘENO: chybí akceptační testy")
    assert res["types"].details.startswith("SKIP:")  # typy bez TS = nedává smysl
    # a11y bez UI souborů a bez možnosti spustit app = NEOVĚŘENO (ne SKIP)
    assert res["a11y"].details.startswith("NEOVĚŘENO:")


def _ship_ctx(target: int) -> dict[str, Any]:
    p = [None] * 20
    p[2], p[14], p[15] = "x", 100, target
    gates = [(g.gate_type, g.status, None, g.details) for g in _gates(types="none")]
    return {"project": tuple(p), "gates": gates, "threshold_override": None,
            "triage": {"blocked_by": []}}


def test_ship_state_production_unverified_acceptance_does_not_pass_pilot_warns() -> None:
    prod = handoff_pr._ship_state(_ship_ctx(85))
    assert "gates:acceptance-neověřeno" in prod["blocked_by"] and not prod["ready"]
    assert prod["verdict"].startswith("nesplňuje práh")
    pilot = handoff_pr._ship_state(_ship_ctx(80))
    assert pilot["ready"] and "⚠" in pilot["verdict"] and "akceptační testy" in pilot["verdict"]


# --- 3. SHIP.md na jednu stránku + zástup ---------------------------------------------------


def test_signatures_mark_foreign_signer_as_zastup(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    with transaction() as conn:   # osobní data = okna bezpečnost a provoz zvlášť
        conn.execute("UPDATE projects SET data_class = 'L3' WHERE slug = ?", (slug,))
    checkpoint.sign(slug, "provoz", by="Kdokoli Cizí", note="rollback a on-call prošli")
    assert "Provoz: Kdokoli Cizí (zástup)" in (handoff_pr.signatures_line(slug) or "")
    pr = handoff_pr.build_pr(slug)
    assert "<summary>Podpisy oken</summary>" in pr["body"] and "(zástup)" in pr["body"]


# --- 4. feedback_pull vs prep ------------------------------------------------------------------


def test_feedback_pull_and_prep_list_same_criticals(
        voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    slug = voted["slug"]
    ids = [_critical(slug, "A"), _critical(slug, "B")]
    agg = feedback_pull.aggregate(slug)
    prep = session_2.prep(slug)
    assert [c["id"] for c in agg["critical_flags"]] == ids
    assert [c["id"] for c in prep["open_critical"]] == ids
    roles = {c["variant"]: c["role"] for c in agg["critical_flags"]}
    assert roles["B"] in ("shortlist", "ostatní") and roles["A"] in ("shortlist", "vítěz")
    pull_lines = feedback_pull._human(agg, None)[1]
    prep_lines = session_2._prep_view(prep)[1]
    for text in (pull_lines, prep_lines):
        joined = "\n".join(text)
        assert "Otevřené kritické: 2" in joined
        assert f"#{ids[0]}" in joined and f"#{ids[1]}" in joined


def test_critical_on_all_variants_says_kill_is_legitimate(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    _critical(slug, "A")
    assert not feedback_pull.aggregate(slug)["critical_on_all_variants"]
    _critical(slug, "B")
    _critical(slug, "C")
    agg = feedback_pull.aggregate(slug)
    assert agg["critical_on_all_variants"]
    assert feedback_pull.ALL_VARIANTS_CRITICAL_LINE in feedback_pull._human(agg, None)[1]
    assert feedback_pull.ALL_VARIANTS_CRITICAL_LINE in session_2._prep_view(session_2.prep(slug))[1]
    assert "Kill je legitimní výsledek" in feedback_pull.ALL_VARIANTS_CRITICAL_LINE


def test_prep_commitment_is_human_not_percent_of_zero(voted: dict[str, Any]) -> None:
    view = session_2._prep_view(session_2.prep(voted["slug"]))
    text = "\n".join(view[1]) + view[3]
    assert "závaznost 0 %" not in text and "cíl 60 %" not in text


# --- 5. Česky všude ----------------------------------------------------------------------------


def test_unknown_project_is_czech_with_existing_slugs(
        voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    for module, argv in ((feedback_pull, ["--slug", "chekout"]),
                         (session_2, ["prep", "--slug", "chekout"]),
                         (retro, ["report", "--slug", "chekout"]),
                         (handoff_pr, ["--slug", "chekout"])):
        with pytest.raises(SystemExit) as exc:
            _run(monkeypatch, module, *argv)
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert "Projekt „chekout“ neexistuje" in err and "Myslel jste „checkout“" in err
        assert "not found" not in err


def test_invalid_decision_is_czech_with_did_you_mean(
        voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        _run(monkeypatch, session_2, "decide", "--slug", voted["slug"], "maybe",
             "--rationale", "x")
    err = capsys.readouterr().err
    assert "Neznámé rozhodnutí „maybe“" in err and "go, iterate, kill" in err
    assert "invalid choice" not in err
    with pytest.raises(SystemExit):
        _run(monkeypatch, session_2, "decide", "--slug", voted["slug"], "kil",
             "--rationale", "x")
    assert "Myslel jste „kill“" in capsys.readouterr().err


def test_argparse_errors_are_czech(monkeypatch: pytest.MonkeyPatch,
                                   capsys: pytest.CaptureFixture[str]) -> None:
    from tool.cli import feedback, session_3

    for module, argv in ((session_3, []), (feedback_pull, []), (feedback, ["add"]),
                         (handoff_pr, [])):
        with pytest.raises(SystemExit) as exc:
            _run(monkeypatch, module, *argv)
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert "Chybí povinný parametr" in err
        assert "required" not in err and "usage:" not in err


def test_feedback_add_never_repeats_tips(voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    shown: list[str] = []
    for i in range(3):
        _run(monkeypatch, __import__("tool.cli.feedback", fromlist=["main"]), "add", "--slug",
             slug, "--variant", "A", "--role", "Design", "--severity", "minor",
             "--text", f"drobnost {i}")
        out = capsys.readouterr().out
        tips = [ln[2:] for ln in out.split("**Doporučení:**")[-1].splitlines()
                if ln.startswith("- ")] if "**Doporučení:**" in out else []
        assert not set(tips) & set(shown)
        shown += tips
