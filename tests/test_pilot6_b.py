"""Pilot 6 (Pekárna), část B: tvrdé brány, přebitý critical, acceptance, retro, prefix Důvod."""
from __future__ import annotations

from datetime import date
from typing import Any

from tool.cli import quality_gates, retro, session_2, session_3
from tool.cli.quality_gates import GateResult
from tool.cli.ux import plural


def _winner(score: int, results: list[dict[str, Any]]) -> dict[str, Any]:
    return {"gates": {"gate_score": score, "results": results}}


FAIL_TESTS = {
    "gate": "tests", "status": "fail",
    "details": "not ok 1 - vrací 404\n  ---\n  error: boom\n  ...\nnot ok 2 - cena\n  ---\n  ...\n"
               "# pass 5\n# fail 2\n",
}


def test_hard_fail_helpers() -> None:
    w = _winner(81, [FAIL_TESTS, {"gate": "lint", "status": "fail", "details": "x"},
                     {"gate": "acceptance", "status": "warn", "details": ""},
                     {"gate": "observability", "status": "warn", "details": ""}])
    assert session_3._hard_failed(w) == ["tests"]
    msg = session_3._hard_fail_message(w, ["tests"])
    assert msg.startswith("padají testy")
    lint = _winner(90, [{"gate": "lint", "status": "fail", "details": ""}])
    assert session_3._hard_failed(lint) == []


def test_next_step_separates_fail_and_warn() -> None:
    w = _winner(81, [FAIL_TESTS, {"gate": "acceptance", "status": "warn", "details": ""},
                     {"gate": "observability", "status": "warn", "details": ""}])
    text = session_3._next_step(w, False, 80, "pek")
    assert "Opravit: tests." in text
    assert "K zvážení: acceptance, observability" in text
    assert "padají testy" in text
    assert "varování" not in text


def test_strip_reason_and_deadline() -> None:
    assert session_2.strip_reason("Důvod: opravíme do 15. 11.") == "opravíme do 15. 11."
    assert session_2.strip_reason("důvod: Důvod - dvojí") == "dvojí"
    assert session_2.strip_reason("bez prefixu") == "bez prefixu"
    assert session_2.reason_deadline("opravíme do 15. 11. 2026") == "do 15. 11. 2026"
    assert session_2.reason_deadline("opravíme do 2 týdnů") == "do 2 týdnů"
    assert session_2.reason_deadline("někdy") is None


def test_overridden_critical_section() -> None:
    item = {"id": 3, "variant": "A", "department": "bezpecnost", "rationale": "XSS ve formuláři",
            "submitted_by": "Lucie", "reason": "pilot, opravíme do 15. 11.",
            "deadline": "do 15. 11.", "decider": "Tom", "at": "2026-10-19"}
    md = session_2.overridden_critical_md([item])
    assert "## Vědomě přebité riziko" in md
    assert "**Přebil:** Tom" in md
    assert "**Důvod:** pilot, opravíme do 15. 11." in md
    assert "**Termín:** do 15. 11." in md
    assert "**Autor nálezu:** Lucie" in md
    assert session_2.overridden_critical_md([]) == ""


def test_decision_md_no_double_reason_and_plural() -> None:
    md = session_2.render_decision_md("s", "go", "ok", "Tom", None, winner="A",
                                      override_critical="Důvod: pilot")
    assert "Důvod: pilot" in md and "Důvod: Důvod" not in md
    assert plural(1, "kritický", "kritické", "kritických") == "1 kritický"
    assert plural(2, "kritický", "kritické", "kritických") == "2 kritické"
    assert plural(5, "kritický", "kritické", "kritických") == "5 kritických"


def test_acceptance_text_when_rate_high_but_run_fails(tmp_path: Any, monkeypatch: Any) -> None:
    (tmp_path / "package.json").write_text('{"name": "x"}', encoding="utf-8")
    acc = tmp_path / "tests" / "acceptance"
    acc.mkdir(parents=True)
    (acc / "a.test.js").write_text("// x", encoding="utf-8")
    out = "# pass 5\n# fail 1\nnot ok 1 - Scénář: uživatel objedná\n"
    monkeypatch.setattr(quality_gates, "_run", lambda *a, **k: (1, out, ""))
    ctx = type("C", (), {})()
    ctx.path = tmp_path
    ctx.stack = type("S", (), {"node": True, "python": False, "other": None, "deps": {}})()
    res = quality_gates._native_acceptance(ctx, acc)  # type: ignore[arg-type]
    assert isinstance(res, GateResult)
    assert res.status == "warn"
    assert "5/6" in res.details and "1 test padá" in res.details
    assert "< cíl" not in res.details


def test_tail_starts_on_line_boundary() -> None:
    text = "Scénář: uživatel objedná chleba\n" + "x" * 30
    tail = quality_gates._tail(text, 40)
    assert not tail.startswith("uži") and tail == "x" * 30
    assert quality_gates._tail("krátké", 40) == "krátké"


def test_coverage_recommendation_is_stack_aware(tmp_path: Any, monkeypatch: Any) -> None:
    def ctx_for(node: bool, python: bool, deps: dict[str, str]) -> Any:
        c = type("C", (), {})()
        c.path = tmp_path
        c.stack = type("S", (), {"node": node, "python": python, "other": None, "deps": deps})()
        return c

    node = quality_gates.gate_coverage(ctx_for(True, False, {}))
    assert "node --test --experimental-test-coverage" in node.details and "c8" in node.details
    assert "vitest + coverage-v8" not in node.details
    py = quality_gates.gate_coverage(ctx_for(False, True, {}))
    assert "pytest --cov" in py.details


def test_retro_horizon_from_kickoff() -> None:
    assert retro.metric_horizon_days({"primary_lagging_metric": "tržby +10 % do 14 dnů"}) == \
        (14, "tržby +10 % do 14 dnů")
    assert retro.metric_horizon_days({"leading_metric": "konverze do 2 týdnů"})[0] == 14
    assert retro.metric_horizon_days({"primary_lagging_metric": "tržby"}) is None


def test_retro_reminders_add_horizon_without_duplicates(monkeypatch: Any) -> None:
    project = {"id": 1, "name": "P", "primary_lagging_metric": "tržby do 14 dnů",
               "leading_metric": "x do 30 dnů"}
    monkeypatch.setattr(retro, "_load_project", lambda conn, slug: project)
    monkeypatch.setattr(retro, "_go_date", lambda conn, pid: (None, "x"))
    monkeypatch.setattr(retro, "_owners",
                        lambda slug, p: {m: ("Karel", "t") for m in retro.MILESTONES})
    _p, _start, _src, items = retro._reminder_items("s", "2026-10-01")
    labels = [it["label"] for it in items]
    assert labels == ["T+7", "T+14", "T+30", "T+60", "T+90"]
    assert items[1]["due"] == date(2026, 10, 15)
    project["primary_lagging_metric"] = "tržby do 30 dnů"
    _p, _s, _src, items = retro._reminder_items("s", "2026-10-01")
    assert [it["label"] for it in items] == ["T+7", "T+30", "T+60", "T+90"]
