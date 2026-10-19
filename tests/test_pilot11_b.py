"""Pilot 11 (Kvítek) B — Iterate s výběrem variant, úklid po Kill, hub (heslo, port), poučení."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tool.cli import db as cli_db
from tool.cli import handoff, hub, quick_session, retro, session_2, status, worktree
from tool.cli.db import transaction


def _iterate(slug: str, **kw: Any) -> dict[str, Any]:
    return session_2.record_decision(slug=slug, decision="iterate", rationale="zúžit", **kw)


# --- 3: Iterate --variants -------------------------------------------------------


def test_iterate_variants_explicit_overrides_shortlist(project: dict[str, Any],
                                                       vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)                                      # shortlist A, B
    out = _iterate(slug, iterate_variants="c, a", iterate_focus="doladit")
    assert out["iterate_variants"] == ["A", "C"]
    assert out["iterate_variants_dropped"] == ["B"]
    assert status.variants_in_play(slug) == ["A", "C"]
    plan = status.iterate_plan(slug)
    assert plan and plan["variants"] == ["A", "C"] and plan["explicit"] and plan["dropped"] == ["B"]
    d = status.project_detail(slug)
    assert [v["name"] for v in d["variants"]] == ["A", "C"]
    assert d["variants_dropped"] == ["B"]
    assert "Po Iterate vypadly: B" in "\n".join(status.detail_lines(d))
    # prompty druhého kola jdou jen pro vybrané varianty
    prompts = quick_session.builder_prompts(slug, "Rychlejší checkout")
    assert [p["name"] for p in prompts["prompts"]] == ["A", "C"]


def test_iterate_without_variants_falls_back_to_shortlist(project: dict[str, Any],
                                                          vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    _iterate(slug)
    assert status.variants_in_play(slug) == ["A", "B"]
    assert status.iterate_plan(slug)["explicit"] is False


def test_iterate_variants_validated(project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    with pytest.raises(ValueError, match="neexistuje"):
        _iterate(slug, iterate_variants="A,Z")
    with pytest.raises(ValueError, match="jen k Iterate"):
        session_2.record_decision(slug=slug, decision="go", winner="A", rationale="x",
                                  iterate_variants="A")


# --- 4: úklid po Kill ----------------------------------------------------------------


def test_kill_lists_cleanup_for_running_preview_and_worktrees(
        project: dict[str, Any], vote: Callable[..., Any], tmp_path: Path,
        tmp_targets: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    slug = project["slug"]
    vote(slug)
    data = tmp_path / "data"
    (data / "preview").mkdir(parents=True)
    monkeypatch.setattr(cli_db, "DATA_ROOT", data)
    (data / "preview" / f"{slug}.json").write_text(json.dumps(
        {"password": "x", "variants": {"A": {"app_pid": os.getpid()}}}))
    wt = tmp_targets / f"{slug}-A"
    wt.mkdir(parents=True)
    (wt / ".git").write_text("gitdir: /clone/.git/worktrees/checkout-A\n")
    assert worktree.TARGETS_CACHE == tmp_targets

    out = session_2.record_decision(slug=slug, decision="kill", rationale="nikdo to nechce")
    text = "\n".join(out["cleanup"])
    assert f"pflanzer preview down --slug {slug}" in text
    assert "git -C /clone worktree remove" in text and f"{slug}-A" in text
    _t, lines, _w, _n, _p = session_2._decision_view(out)
    assert any(ln.startswith("Úklid:") for ln in lines)
    assert "Úklid po Kill" in "\n".join(status.detail_lines(status.project_detail(slug)))


def test_cleanup_silent_when_nothing_runs(project: dict[str, Any], tmp_path: Path,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_db, "DATA_ROOT", tmp_path / "nic")
    assert status.cleanup_steps(project["slug"]) == []


# --- 8: poučení ---------------------------------------------------------------------


def test_kill_log_has_single_lesson_section_and_author(
        project: dict[str, Any], vote: Callable[..., Any], tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    slug = project["slug"]
    vote(slug)
    repo = tmp_path / "target"
    (repo / ".pflanzer").mkdir(parents=True)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli_db, "current_actor", lambda: "unknown")
    monkeypatch.setattr(retro, "current_actor", lambda: "unknown")
    session_2.record_decision(slug=slug, decision="kill", rationale="špatný problém")
    retro.lesson(slug=slug, text="lidé to nechtějí")
    retro.lesson(slug=slug, text="cena je moc vysoká", by="Barbora")
    log = (repo / ".pflanzer" / "decisions" / f"{slug}.md").read_text(encoding="utf-8")
    assert log.count("### Poučení") == 1
    assert "- - -" not in log and "- \n" not in log
    assert "unknown" not in log
    assert "— Dana Deciderová" in log and "— Barbora" in log


# --- 10: Kill ve výpisech -------------------------------------------------------------


def test_handoff_and_retro_after_kill_are_human(project: dict[str, Any], vote: Callable[..., Any],
                                                capsys: pytest.CaptureFixture[str],
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    slug = project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="kill", rationale="x")
    retro.lesson(slug=slug, text="trh není", by="Dana")
    monkeypatch.setattr(sys, "argv", ["pflanzer", "--slug", slug])
    handoff.main()
    out = capsys.readouterr().out
    assert "handoff se nedělá" in out and "trh není" in out and "/pm decide" not in out
    monkeypatch.setattr(sys, "argv", ["pflanzer", "reminders", "--slug", slug])
    retro.main()
    out = capsys.readouterr().out
    assert "připomínky" in out and "trh není" in out and "CHYBA" not in out.upper()
    monkeypatch.setattr(sys, "argv", ["pflanzer", "measure", "--slug", slug])
    retro.main()
    assert "není co měřit" in capsys.readouterr().out


# --- 9: nová DB ---------------------------------------------------------------------


def test_fresh_db_is_created_automatically(isolated_env: dict[str, Path]) -> None:
    assert not isolated_env["db"].exists()
    with transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0
    assert status.list_projects() == []


# --- 6: hub port --------------------------------------------------------------------


def test_hub_port_check_and_hub_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        assert not hub.port_free("127.0.0.1", port)
        alt = hub.find_free_port("127.0.0.1", port)
        assert alt and alt != port and hub.port_free("127.0.0.1", alt)
    monkeypatch.setattr(hub, "DATA_ROOT", tmp_path)
    hub.write_hub_json(8123)
    assert json.loads((tmp_path / "hub.json").read_text()) == {
        "port": 8123, "url": "http://127.0.0.1:8123/method/"}


def test_hub_busy_port_gives_czech_message(monkeypatch: pytest.MonkeyPatch,
                                           capsys: pytest.CaptureFixture[str]) -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        monkeypatch.setattr(sys, "argv", ["pflanzer hub", "--port", str(port)])
        with pytest.raises(SystemExit) as e:
            hub.main()
    err = capsys.readouterr().err
    assert e.value.code == 2 and "obsazený" in err and "--port" in err


# --- 5 + 3 + 10 + 11: backend hubu ----------------------------------------------------

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")


def _detail(slug: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, password: str | None,
            local: bool, state_pw: str | None = "tajne") -> dict[str, Any]:
    from sqlmodel import Session, create_engine
    from starlette.requests import Request

    from tool.web.backend.api import projects as api

    data = tmp_path / "hubdata"
    (data / "preview").mkdir(parents=True, exist_ok=True)
    (data / "preview" / f"{slug}.json").unlink(missing_ok=True)
    if state_pw:
        (data / "preview" / f"{slug}.json").write_text(
            json.dumps({"password": state_pw, "user": "pflanzer"}))
    monkeypatch.setenv("PFLANZER_DATA", str(data))
    if password:
        monkeypatch.setenv("PFLANZER_HUB_PASSWORD", password)
    else:
        monkeypatch.delenv("PFLANZER_HUB_PASSWORD", raising=False)
    headers = [] if local else [(b"x-forwarded-for", b"10.0.0.5")]
    req = Request({"type": "http", "headers": headers,
                   "client": ("127.0.0.1" if local else "10.0.0.5", 1)})
    engine = create_engine(f"sqlite:///{os.environ['PFLANZER_DB']}")
    with Session(engine) as db:
        return api.get_project(slug, req, db)


def test_hub_shows_preview_password_only_when_safe(
        project: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    slug = project["slug"]
    assert _detail(slug, tmp_path, monkeypatch, password=None, local=True)[
        "preview_login"] == {"user": "pflanzer", "password": "tajne"}
    assert _detail(slug, tmp_path, monkeypatch, password="hubpw", local=False)[
        "preview_login"]["password"] == "tajne"
    assert _detail(slug, tmp_path, monkeypatch, password=None, local=False)[
        "preview_login"] == {"user": "pflanzer", "password": None}
    assert _detail(slug, tmp_path, monkeypatch, password=None, local=True,
                   state_pw=None)["preview_login"] is None


def test_hub_backend_in_play_kill_and_profile(
        project: dict[str, Any], vote: Callable[..., Any], tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlmodel import Session, create_engine

    from tool.web.backend.api import variants as vapi

    slug = project["slug"]
    vote(slug)
    _iterate(slug, iterate_variants="A,C")
    d = _detail(slug, tmp_path, monkeypatch, password=None, local=True, state_pw=None)
    assert d["variants_in_play"] == ["A", "C"] and d["variants_dropped"] == ["B"]
    assert d["risk_profile"] == "pilot" and d["kill"] is None
    with Session(create_engine(f"sqlite:///{os.environ['PFLANZER_DB']}")) as db:
        names = [v["name"] for v in vapi.list_variants(slug, db, "x")]
    assert names == ["A", "C"]


def test_hub_backend_kill_card(project: dict[str, Any], vote: Callable[..., Any],
                               tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    slug = project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="kill", rationale="Trh to nechce.")
    retro.lesson(slug=slug, text="ptát se dřív", by="Dana")
    d = _detail(slug, tmp_path, monkeypatch, password=None, local=True, state_pw=None)
    assert d["kill"]["reason"] == "Trh to nechce."
    assert d["kill"]["lessons"] == [{"text": "ptát se dřív", "by": "Dana"}]


# --- 11: frontend texty --------------------------------------------------------------


def test_frontend_sources_have_human_labels() -> None:
    src = Path(__file__).resolve().parents[1] / "tool" / "web" / "frontend" / "src"
    form = (src / "pages" / "FeedbackForm.tsx").read_text(encoding="utf-8")
    assert "{r.ai_proxy_mode})" not in form and "mode_1" not in form
    assert "Dimenze AI Act" not in form and "Úroveň WCAG" not in form
    task = (src / "lib" / "task.ts").read_text(encoding="utf-8")
    assert "feedbackExample(step: string | undefined, variant" in task
    assert "U varianty B" not in task and "Varianta B" not in task


@pytest.mark.skipif(subprocess.run(["which", "node"], capture_output=True).returncode != 0,
                    reason="node není k dispozici")
def test_split_hypothesis_regex_matches_profile_sentences() -> None:
    import re
    pattern = r"\s*(?:Throwaway prototyp|Pilot s|Ostré nasazení)[^.]*\.?\s*$"
    for label in ("Pilot s 5-20 reálnými uživateli",
                  "Throwaway prototyp (interní demo, ne produkce)",
                  "Ostré nasazení pro všechny uživatele (přísnější brány)"):
        assert re.sub(pattern, "", f"Ověříme ho na třech variantách. {label}.", flags=re.I) \
            == "Ověříme ho na třech variantách."
