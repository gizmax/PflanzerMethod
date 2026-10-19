"""Pilot 9 (Šlapka) A — mob mode end-to-end, druhé kolo po Iterate, PR title, české chyby."""
from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url, git

from tool.cli import handoff_pr, quick_session, retro, session_2, status, worktree
from tool.cli.db import transaction
from tool.cli.quick_session import record_voting
from tool.cli.ux import ASYNC_AFTER_ITERATE, ASYNC_FULL, async_days, read_spec

HOOK = "Rychlejší checkout pro B2B zákazníky"


def _pref(value: float = 0.8) -> dict[str, Any]:
    return {"role_idx": 1, "user_value": value, "effort": 0.4, "risk": 0.2,
            "strategic_fit": 0.7, "commitment_level": 2, "rationale": "nejrychlejší cesta"}


def _vote_mob(slug: str) -> dict[str, Any]:
    return record_voting(
        slug=slug, facilitator="Fanda", decider_call={"shortlist": ["mob"], "rationale": "jediná"},
        votes=[{"name": "mob", "builder": "claude-code", "description": "Rezervace kola na den",
                "role_preferences": [_pref()]}])


@pytest.fixture
def mob_project(tmp_db: Path, bare_repo: Path) -> dict[str, Any]:
    out = bootstrap_project(slug="slapka", target_repo_url=file_url(bare_repo),
                            session_mode="mob",
                            windows={"Build": "st 21.10. 9:00-12:00",
                                     "Rozhodnutí": "pá 30.10. 10:00"})
    out["bare_repo"] = bare_repo
    return out


# --- mob end-to-end ---------------------------------------------------------


def test_bootstrap_stores_mode_windows_and_recommendation(mob_project: dict[str, Any]) -> None:
    assert mob_project["session_mode"] == "mob"
    assert mob_project["mode_recommendation"]["mode"] in ("parallel", "mob")
    note = mob_project["mode_note"]
    assert "doporučení" in note or mob_project["mode_recommendation"]["mode"] == "mob"
    assert "jedné společně postavené variantě" in _xyz("slapka")
    d = status.project_detail("slapka")
    assert d["session_mode"] == "mob"
    assert [w["okno"] for w in d["windows"]] == ["Build", "Rozhodnutí"]
    text = "\n".join(status.detail_lines(d))
    assert "Okna: Build st 21.10. 9:00-12:00" in text and "Rozhodnutí pá 30.10. 10:00" in text


def _xyz(slug: str) -> str:
    with transaction() as conn:
        return conn.execute("SELECT xyz_hypothesis FROM projects WHERE slug = ?",
                            (slug,)).fetchone()[0]


def test_invalid_mode_and_windows_are_czech_errors(tmp_db: Path, bare_repo: Path) -> None:
    with pytest.raises(ValueError, match="Neznámý session_mode"):
        bootstrap_project(session_mode="trio", target_repo_url=file_url(bare_repo))
    with pytest.raises(ValueError, match="windows"):
        bootstrap_project(slug="x2", windows=42, target_repo_url=file_url(bare_repo))


def test_mob_flow_worktree_prompts_vote_decide_status(
        mob_project: dict[str, Any], tmp_targets: Path) -> None:
    slug = "slapka"
    # worktree setup bez --mode -> jeden worktree `slapka-mob`, větev pflanzer/slapka-mob
    res = worktree.setup(slug, install_deps=False, run_guard=False)
    assert res.mode == "mob"
    assert [p.name for p in res.worktrees] == ["slapka-mob"]
    assert git(res.worktrees[0], "rev-parse", "--abbrev-ref", "HEAD") == "pflanzer/slapka-mob"
    assert git(res.worktrees[0], "config", "--worktree", "pflanzer.variant") == "slapka-mob"
    assert not (tmp_targets / "slapka-mob-mob").exists()

    # prompts bez --mode -> mob, jedno jméno varianty
    out = quick_session.builder_prompts(slug, HOOK)
    assert out["mode"] == "mob"
    assert {p["name"] for p in out["prompts"]} == {"mob"}
    assert len(out["prompts"]) == 2
    assert all("slapka-mob-mob" not in p["prompt_text"] for p in out["prompts"])

    # vote -> prep řekne lidsky, že není co porovnávat -> Go s vítězem mob
    voted = _vote_mob(slug)
    assert "varianty" not in voted["next_step"].split(")")[0] or "variantu" in voted["next_step"]
    prep = session_2.prep(slug)
    assert prep["session_mode"] == "mob"
    _t, lines, _w, nxt, _c = session_2._prep_view(prep)
    assert any("Mob mode" in ln and "není co porovnávat" in ln for ln in lines)
    assert "--winner mob" in nxt or "kritické" in nxt
    done = session_2.record_decision(slug=slug, decision="go", winner="MOB", rationale="Jdeme")
    assert done["winner"] == "mob"
    assert done["new_status"] == "handoff"

    d = status.project_detail(slug)
    assert d["winner"] == "mob"
    text = "\n".join(status.detail_lines(d))
    assert "Varianta (mob mode, jedna společná)" in text
    assert "jedna společná varianta" in handoff_pr._variants_line(["mob"])


def test_winner_validated_against_real_variants(project: dict[str, Any],
                                                vote: Callable[..., Any]) -> None:
    vote(project["slug"], names=("A", "B"))
    with pytest.raises(ValueError, match="neexistuje"):
        session_2.record_decision(slug=project["slug"], decision="go", winner="C", rationale="x")
    out = session_2.record_decision(slug=project["slug"], decision="go", winner="b", rationale="x")
    assert out["winner"] == "B"


# --- druhé kolo po Iterate ----------------------------------------------------


def test_iterate_prompts_only_in_play_with_focus_and_short_async(
        project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    first = quick_session.builder_prompts(slug, HOOK)
    assert [p["name"] for p in first["prompts"]] == ["A", "B", "C"]
    assert async_days(slug) == ASYNC_FULL
    vote(slug, names=("A", "B", "C"))              # shortlist = A, B
    session_2.record_decision(slug=slug, decision="iterate", rationale="C má critical",
                              iterate_focus="doplnit kontrolu dostupnosti kola na den")
    assert async_days(slug) == ASYNC_AFTER_ITERATE
    out = quick_session.builder_prompts(slug, HOOK)
    assert [p["name"] for p in out["prompts"]] == ["A", "B"]
    assert out["variants_in_play"] == ["A", "B"]
    assert out["iterate_focus"] == "doplnit kontrolu dostupnosti kola na den"
    for p in out["prompts"]:
        assert "Cíl tohoto kola: doplnit kontrolu dostupnosti kola na den" in p["ai_prompt"]
    assert status._variants_in_play(slug) == ["A", "B"]
    voted = record_voting(
        slug=slug, facilitator="Fanda", decider_call={"shortlist": ["A"], "rationale": "A"},
        real_urls={"A": "https://example.com/a", "B": "https://example.com/b"},
        votes=[{"name": n, "builder": "claude-code", "description": n,
                "role_preferences": [_pref()]} for n in ("A", "B")])
    assert ASYNC_AFTER_ITERATE in voted["next_step"]


# --- PR title ---------------------------------------------------------------


def test_pr_title_has_no_po_iterate_prefix(worktree_project: dict[str, Any]) -> None:
    slug = worktree_project["slug"]
    record_voting(
        slug=slug, facilitator="Fanda", decider_call={"shortlist": ["A"], "rationale": "A"},
        votes=[{"name": "A", "builder": "claude-code",
                "description": "A po Iterate: Rezervace kola na den s kontrolou dostupnosti",
                "role_preferences": [_pref()]}])
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme")
    title = handoff_pr.build_pr(slug)["title"]
    assert "po Iterate" not in title
    assert title.startswith(f"feat({slug}): Rezervace kola na den")


def test_po_iterate_prefix_regex() -> None:
    rx = handoff_pr._PO_ITERATE_PREFIX
    assert rx.sub("", "C po Iterate: Rezervace") == "Rezervace"
    assert rx.sub("", "B po iterate — Něco") == "Něco"
    assert rx.sub("", "Rezervace po Iterate stavu") == "Rezervace po Iterate stavu"


# --- české chyby a spec ---------------------------------------------------------


def test_prompts_unknown_slug_is_czech_error(tmp_db: Path, project: dict[str, Any],
                                             monkeypatch: pytest.MonkeyPatch,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(ValueError, match="Projekt „chekout“ neexistuje.*checkout"):
        quick_session.builder_prompts("chekout", HOOK)
    monkeypatch.setattr(sys, "argv", ["quick_session", "prompts", "--slug", "chekout",
                                      "--hook", HOOK])
    with pytest.raises(SystemExit) as exc:
        quick_session.main()
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "neexistuje" in err and "Traceback" not in err


def test_spec_errors_recommend_file_not_heredoc(tmp_path: Path) -> None:
    assert "<<'EOF'" not in quick_session.BOOTSTRAP_EXAMPLE
    assert "--spec .pflanzer/specs/" in quick_session.BOOTSTRAP_EXAMPLE
    with pytest.raises(ValueError) as exc:
        read_spec(tmp_path / "chybi.json")
    assert "<<'EOF'" not in str(exc.value) and "Write" in str(exc.value)
    with pytest.raises(ValueError) as exc2:
        quick_session._bootstrap_from_spec(
            {"hook": HOOK, "decider_name": "D", "risk_profile": "pilot", "neznamy": 1})
    assert "<<'EOF'" not in str(exc2.value) and "neznamy" in str(exc2.value)


# --- retro: metrika projektu v horizontu --------------------------------------


def test_retro_horizon_item_uses_project_metric(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="slapka2", target_repo_url=file_url(bare_repo),
                      metric="podíl online rezervací >= 40 % do 6 týdnů")
    _p, _start, _src, items = retro._reminder_items("slapka2", "2026-10-30")
    it = next(i for i in items if i["milestone"] == "t42")
    assert it["metrics"] == ["t42_project_metric"]
    assert "t60_rework_pct" not in it["record_cmd"]
    assert "--metric t42_project_metric" in it["record_cmd"]
    retro.record(slug="slapka2", milestone="t60", metric="t42_project_metric", value=44, unit="%")
    with transaction() as conn:
        latest = {(r[0], r[1]): {"value": r[2], "unit": r[3]} for r in conn.execute(
            "SELECT milestone, metric, value, unit FROM outcomes").fetchall()}
    reading = retro._primary_metric({"primary_lagging_metric": "x"}, latest)["reading"]
    assert reading and reading["metric"] == "t42_project_metric" and reading["value"] == 44
