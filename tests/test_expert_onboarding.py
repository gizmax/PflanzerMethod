"""Onboarding experta bez Claude Code: alias `pflanzer start`, Python acceptance glob, hlášky."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from tool.cli import quick_session

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "tool" / "bin" / "pflanzer"


def _env(tmp_path: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(HOME=str(tmp_path / "home"), PFLANZER_DATA=str(tmp_path / "data"),
               PFLANZER_DB=str(tmp_path / "data" / "p.db"), TZ="UTC")
    (tmp_path / "home").mkdir(exist_ok=True)
    return env


def test_start_alias_in_help_and_cmds() -> None:
    src = BIN.read_text(encoding="utf-8")
    assert re.search(r"^  start\)", src, re.M)
    assert "help start ship" in src


def test_start_help_has_example(tmp_path: Path) -> None:
    res = subprocess.run([str(BIN), "start", "--help"], capture_output=True, text=True,
                         env=_env(tmp_path), cwd=tmp_path)
    assert res.returncode == 0
    assert "pflanzer start --spec" in res.stdout


def test_docs_example_json_passes(tmp_path: Path) -> None:
    md = (ROOT / "docs" / "zacni.md").read_text(encoding="utf-8")
    block = re.search(r"### Bez Claude Code.*?```json\n(.*?)```", md, re.S)
    assert block
    spec = json.loads(block.group(1))
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "kickoff.json").write_text(json.dumps(spec), encoding="utf-8")
    res = subprocess.run([str(BIN), "start", "--spec", "kickoff.json", "--json"],
                         capture_output=True, text=True, env=_env(tmp_path), cwd=repo)
    assert res.returncode == 0, res.stdout + res.stderr


def test_python_requirements_acceptance_glob(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("flask\n", encoding="utf-8")
    prof = quick_session.stack_profile(tmp_path)
    assert prof.stack == "python"
    rules = quick_session._builder_rules("s", "h", "A", True, stack=prof)
    assert "tests/acceptance/test_*.py" in rules
    assert ".test.js" not in rules


def test_bootstrap_example_uses_short_alias() -> None:
    assert quick_session.BOOTSTRAP_EXAMPLE.startswith("pflanzer start --spec")
