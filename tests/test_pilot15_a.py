"""Pilot 15 (Ponk, Flask+htmx, Quick + mob + throwaway) A — builder prompt, mob texty,
Quick = 1 kolo, šablona vote specu, .venv v PATH."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import apprun, quality_gates, quick_session, worktree
from tool.cli.tier import MOB_ITERATIONS, project_tier
from tool.cli.ux import tips_for

ROOT = Path(__file__).resolve().parents[1]
HOOK = "Rychlejší checkout pro B2B zákazníky"


@pytest.fixture
def ponk(tmp_db: Path, bare_repo: Path) -> dict[str, Any]:
    return bootstrap_project(slug="ponk", risk_profile="throwaway", tier="quick",
                             session_mode="mob", target_repo_url=file_url(bare_repo))


# --- 1. throwaway: jedna instrukce k testům -------------------------------------------------

def test_throwaway_prompt_has_single_test_instruction(ponk: dict[str, Any]) -> None:
    out = quick_session.builder_prompts("ponk", HOOK)
    text = out["prompts"][0]["ai_prompt"]
    assert "nepřemýšlej o testech" not in text
    assert "1 smoke / akceptační test hlavního toku" in text
    assert "commitni JEN zelené (throw-away" in text


def test_pilot_prompt_keeps_full_test_rules(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="pil", risk_profile="pilot", session_mode="mob",
                      target_repo_url=file_url(bare_repo))
    text = quick_session.builder_prompts("pil", HOOK)["prompts"][0]["ai_prompt"]
    assert "throw-away" not in text and "commitni JEN zelené." in text


# --- 5. mob texty -----------------------------------------------------------------------------

def test_mob_commit_message_has_no_doubled_mob(ponk: dict[str, Any]) -> None:
    text = quick_session.builder_prompts("ponk", HOOK)["prompts"][0]["ai_prompt"]
    assert "feat(ponk): mob — " in text
    assert "mob mob" not in text


def test_parallel_commit_message_names_variant(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="par", target_repo_url=file_url(bare_repo))
    text = quick_session.builder_prompts("par", HOOK)["prompts"][0]["ai_prompt"]
    assert "feat(par): variant A — " in text


def test_setup_only_when_worktree_missing(ponk: dict[str, Any], tmp_targets: Path) -> None:
    before = quick_session.builder_prompts("ponk", HOOK)["prompts"][0]["facilitator_text"]
    assert "worktree setup --slug ponk --mode mob" in before
    worktree.setup("ponk", install_deps=False, run_guard=False)
    after = quick_session.builder_prompts("ponk", HOOK)["prompts"][0]["facilitator_text"]
    assert "SETUP" not in after and "worktree setup" not in after
    assert "už existuje" in after


def test_parallel_setup_text_only_when_worktrees_missing(
        tmp_db: Path, bare_repo: Path, tmp_targets: Path) -> None:
    bootstrap_project(slug="par", target_repo_url=file_url(bare_repo))
    assert "worktree setup --slug par" in quick_session.builder_prompts("par", HOOK)["setup_text"]
    worktree.setup("par", install_deps=False, run_guard=False)
    out = quick_session.builder_prompts("par", HOOK)
    assert out["setup_text"] == ""
    assert all("worktree setup" not in p["facilitator_text"] for p in out["prompts"])


def test_after_vote_tips_follow_variant_count() -> None:
    one = " ".join(tips_for("after_vote", {"single_variant": True}))
    many = " ".join(tips_for("after_vote", {"multi_variants": True}))
    assert "společnou variantu" in one and "3 odkazy" not in one
    assert "všechny varianty" in many and "3 odkazy" not in many


def test_vote_output_for_mob_does_not_say_three_links(ponk: dict[str, Any], capsys: Any) -> None:
    out = quick_session.record_voting(
        slug="ponk", facilitator="Fanda", decider_call={"shortlist": ["mob"], "rationale": "x"},
        votes=[{"name": "mob", "builder": "claude-code", "description": "d",
                "role_preferences": [{"role_idx": 1, "user_value": 0.8, "effort": 0.4, "risk": 0.2,
                                      "strategic_fit": 0.7, "commitment_level": 2,
                                      "rationale": "ok"}]}])
    quick_session._render_vote(out, False, "ponk")
    shown = capsys.readouterr().out
    assert "3 odkazy" not in shown and "společnou variantu" in shown


def test_build_help_names_real_variants() -> None:
    env = {**os.environ, "PFLANZER_PLUGIN_DIR": str(ROOT)}
    res = subprocess.run([str(ROOT / "tool" / "bin" / "pflanzer"), "build"], capture_output=True,
                         text=True, env=env, check=True)
    assert "mob" in res.stdout and "worktrees A/B/C" not in res.stdout


# --- 6. Quick = 1 iterace ---------------------------------------------------------------------

def test_quick_mob_is_single_iteration(ponk: dict[str, Any]) -> None:
    assert project_tier("ponk") == "quick" and MOB_ITERATIONS["quick"] == 1
    out = quick_session.builder_prompts("ponk", HOOK)
    assert len(out["prompts"]) == 1
    fac = out["prompts"][0]["facilitator_text"]
    assert "1 kolo × 30 min" in fac and "Hard break 25 min" not in fac
    assert "iterace 1/1" in out["prompts"][0]["angle"]


def test_lean_mob_keeps_two_iterations(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="lean", risk_profile="pilot", tier="lean", session_mode="mob",
                      target_repo_url=file_url(bare_repo))
    out = quick_session.builder_prompts("lean", HOOK)
    assert len(out["prompts"]) == 2
    assert "Hard break 25 min" in out["prompts"][0]["facilitator_text"]


def test_iteration_angle_typo_fixed() -> None:
    joined = " ".join(a[2] for a in quick_session.MOB_ITERATION_ANGLES)
    assert "Po obsahu" not in joined and "iteraci voting" not in joined


# --- 8. šablona vote specu --------------------------------------------------------------------

def test_vote_template_written_and_loadable(
        ponk: dict[str, Any], tmp_path: Path, tmp_targets: Path) -> None:
    base = tmp_path / "repo"
    base.mkdir()
    path = worktree.write_vote_template("ponk", "mob", base)
    assert path == base / ".pflanzer" / "specs" / "ponk-vote.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "_napoveda" in data and [v["name"] for v in data["votes"]] == ["mob"]
    assert data["real_urls"] == {"mob": ""}
    assert worktree.write_vote_template("ponk", "mob", base) is None      # nic nepřepisuje
    par = worktree.vote_template("x", worktree.PARALLEL_VARIANTS)
    assert [v["name"] for v in par["votes"]] == ["A", "B", "C"]


def test_vote_ignores_napoveda_key(ponk: dict[str, Any], tmp_path: Path) -> None:
    spec = {"_napoveda": "tohle vote ignoruje", "slug": "ponk", "facilitator": "Fanda",
            "votes": [{"name": "mob", "builder": "claude-code", "description": "d",
                       "role_preferences": [{"role_idx": 1, "user_value": 0.8, "effort": 0.4,
                                             "risk": 0.2, "strategic_fit": 0.7,
                                             "commitment_level": 2, "rationale": "ok"}]}],
            "real_urls": {"mob": ""},
            "decider_call": {"shortlist": ["mob"], "rationale": "x"}}
    f = tmp_path / "v.json"
    f.write_text(json.dumps(spec), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    res = subprocess.run(["python3", "-m", "tool.cli.quick_session", "vote", "--spec", str(f),
                          "--json"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert res.returncode == 0, res.stderr + res.stdout
    assert "_napoveda" not in res.stderr


# --- 9. .venv/bin v PATH ----------------------------------------------------------------------

def test_venv_env_prepends_venv_bin(tmp_path: Path) -> None:
    assert apprun.venv_env(tmp_path) == {}
    py = tmp_path / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\n")
    env = apprun.venv_env(tmp_path)
    assert env["PATH"].startswith(str(tmp_path / ".venv" / "bin") + os.pathsep)
    assert env["VIRTUAL_ENV"] == str(tmp_path / ".venv")


def test_quality_gate_commands_see_venv_python(tmp_path: Path) -> None:
    exe = tmp_path / ".venv" / "bin" / "python"
    exe.parent.mkdir(parents=True)
    exe.write_text("#!/bin/sh\necho venv-python\n")
    exe.chmod(0o755)
    rc, out, _ = quality_gates._run("python", tmp_path)
    assert rc == 0 and "venv-python" in out


def test_start_app_uses_venv_path(tmp_path: Path) -> None:
    exe = tmp_path / ".venv" / "bin" / "mytool"
    exe.parent.mkdir(parents=True)
    (exe.parent / "python").write_text("#!/bin/sh\n")
    exe.write_text("#!/bin/sh\necho from-venv\n")
    exe.chmod(0o755)
    spec = apprun.RunSpec("mytool", "mytool", {}, tmp_path)
    log = tmp_path / "app.log"
    proc = apprun.start_app(spec, log)
    proc.wait(timeout=10)
    assert "from-venv" in log.read_text()


def test_python_prompt_mentions_venv_path(tmp_db: Path, bare_repo: Path) -> None:
    stack = quick_session.StackProfile("python", ["make test"], None)
    rules = quick_session._builder_rules("s", "h", "A", False, stack=stack)
    assert ".venv/bin" in rules and "PATH" in rules
    node_stack = quick_session.StackProfile("node", ["npm test"], None)
    node = quick_session._builder_rules("s", "h", "A", False, stack=node_stack)
    assert ".venv/bin" not in node
