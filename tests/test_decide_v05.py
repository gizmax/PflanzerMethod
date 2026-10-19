"""Rozhodnutí (session_2, v0.5): Go vyžaduje vítěze, critical na vítězi blokuje, Iterate max 1x."""
from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

import pytest

from tool.cli import session_2
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
            "rationale, submitted_by) VALUES (?, 'critical', 'security', 'auth', 0.1, "
            "'Chybí kontrola oprávnění', 'Test')", (vid,),
        ).lastrowid)


def _status(slug: str) -> str:
    with transaction() as conn:
        return conn.execute("SELECT status FROM projects WHERE slug = ?", (slug,)).fetchone()[0]


def test_go_without_winner_rejected(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    with pytest.raises(ValueError, match="--winner"):
        session_2.record_decision(slug=slug, decision="go", rationale="Jdeme do toho")
    assert _status(slug) != "handoff"


def test_go_with_winner_records_winner_and_status(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    out = session_2.record_decision(slug=slug, decision="go", winner="a",
                                    rationale="A je nejrychlejší")
    assert out["winner"] == "A"
    assert out["new_status"] == "handoff"
    assert _status(slug) == "handoff"
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        assert session_2.get_winner(conn, pid) == "A"


def test_go_with_unknown_winner_rejected(voted: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="--winner"):
        session_2.record_decision(slug=voted["slug"], decision="go", winner="Z",
                                  rationale="x")


def test_critical_on_winner_blocks_go(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    _add_critical(slug, "A")
    with pytest.raises(ValueError, match="critical"):
        session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    assert _status(slug) != "handoff"


def test_critical_on_other_variant_does_not_block_go(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    _add_critical(slug, "B")
    out = session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme s A")
    assert out["new_status"] == "handoff"
    assert out["open_critical_overridden"] == 0


def test_override_critical_with_reason_passes(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    fid = _add_critical(slug, "A")
    out = session_2.record_decision(
        slug=slug, decision="go", winner="A", rationale="Jdeme",
        override_critical="Oprava je v plánu na T+3, pilot jen interní",
    )
    assert out["new_status"] == "handoff"
    assert out["open_critical_overridden"] == 1
    with transaction() as conn:
        reason = conn.execute(
            "SELECT override_critical_reason FROM sessions WHERE type = 2"
        ).fetchone()[0]
        body = conn.execute(
            "SELECT body_md FROM decisions WHERE type = 'handoff'"
        ).fetchone()[0]
    assert "T+3" in reason
    assert f"#{fid}" in body


def test_resolved_critical_does_not_block(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    fid = _add_critical(slug, "A")
    res = session_2.resolve_feedback(slug=slug, feedback_ids=[fid], note="Opraveno v PR",
                                     by="Ondra")
    assert res["open_critical_left"] == 0
    out = session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    assert out["new_status"] == "handoff"


def test_iterate_allowed_once_with_critical_then_rejected(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    _add_critical(slug, "A")  # critical neblokuje Iterate - právě v něm se opravuje
    first = session_2.record_decision(slug=slug, decision="iterate",
                                      rationale="Opravit auth", iterate_focus="auth")
    assert first["new_status"] == "session_2"
    assert _status(slug) == "session_2"
    with pytest.raises(ValueError, match="max 1"):
        session_2.record_decision(slug=slug, decision="iterate", rationale="Ještě jednou")
    assert _status(slug) == "session_2"


def test_cli_go_without_winner_exits_2(voted: dict[str, Any],
                                       monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["session_2.py", "decide", "--slug", voted["slug"],
                                      "go", "--rationale", "Jdeme"])
    with pytest.raises(SystemExit) as exc:
        session_2.main()
    assert exc.value.code == 2


def test_ship_hardens_only_decided_winner(worktree_project: dict[str, Any],
                                          vote: Callable[..., Any]) -> None:
    from tool.cli import session_3

    slug = worktree_project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="go", winner="B", rationale="B je čistší")
    out = session_3.hardening_run(slug=slug)
    assert [v["variant"] for v in out["per_variant"]] == ["B"]
    assert out["winner"]["variant"] == "B"
    assert out["selection"] == "vítěz z Rozhodnutí"
    # Skóre je normalizované X/100 s prahem projektu (pilot = 80).
    assert out["winner"]["score_display"] == f"{out['winner']['gate_score']}/100 (práh 80)"
    explicit = session_3.hardening_run(slug=slug, variants=["A", "B"],
                                       override_rationale="porovnání kandidátů")
    assert {v["variant"] for v in explicit["per_variant"]} == {"A", "B"}


# --- UX v0.5.x: druhé decide, resolve, jmenovité blokace ---------------------------------


def test_second_decide_after_go_rejected_without_force(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    with pytest.raises(ValueError, match=r"Už je Go \(A\).*--force --rationale"):
        session_2.record_decision(slug=slug, decision="go", winner="B", rationale="Radši B")
    assert _status(slug) == "handoff"
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        assert session_2.get_winner(conn, pid) == "A"
    forced = session_2.record_decision(slug=slug, decision="go", winner="B",
                                       rationale="Nová informace od bezpečnosti", force=True)
    assert forced["winner"] == "B"


def test_resolve_requires_by_and_note_and_known_id(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    fid = _add_critical(slug, "A")
    with pytest.raises(ValueError, match="--by"):
        session_2.resolve_feedback(slug=slug, feedback_ids=[fid], note="Opraveno")
    with pytest.raises(ValueError, match="--note"):
        session_2.resolve_feedback(slug=slug, feedback_ids=[fid], by="Ondra")
    with pytest.raises(ValueError, match="#999"):
        session_2.resolve_feedback(slug=slug, feedback_ids=[999], by="Ondra", note="x")
    res = session_2.resolve_feedback(slug=slug, feedback_ids=[fid], by="Ondra", note="Opraveno")
    assert res["resolved"] == [fid]
    assert res["open_critical_left"] == 0


def test_critical_block_names_author_and_step(voted: dict[str, Any]) -> None:
    slug = voted["slug"]
    _add_critical(slug, "A")
    with pytest.raises(ValueError) as exc:
        session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    msg = str(exc.value)
    assert "Test" in msg and "krok security" in msg and "--by JMÉNO" in msg


def test_cli_resolve_without_by_exits_2(voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    fid = _add_critical(slug, "A")
    monkeypatch.setattr(sys, "argv", ["session_2.py", "resolve", "--slug", slug,
                                      "--feedback-id", str(fid), "--note", "Opraveno"])
    with pytest.raises(SystemExit) as exc:
        session_2.main()
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "--by" in err and "Traceback" not in err


def test_cli_resolve_human_output(voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
                                  capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    fid = _add_critical(slug, "A")
    monkeypatch.setattr(sys, "argv", ["session_2.py", "resolve", "--slug", slug,
                                      "--feedback-id", str(fid), "--by", "Ondra",
                                      "--note", "Opraveno v PR"])
    session_2.main()
    out = capsys.readouterr().out
    assert f"Vyřešeno: #{fid} (Ondra: Opraveno v PR)" in out
    assert not out.lstrip().startswith("{")
