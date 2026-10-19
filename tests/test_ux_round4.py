"""4. kolo UX: Kill u Ship, přehled statusu, retro chyby, SHIP.md, business critical,
tier, PyYAML v doctoru, .gitignore v init, poučení ve statusu."""
from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import REPO_ROOT, git

from tool.cli import doctor, feedback, handoff_pr, init, retro, session_2, session_3, status, tier
from tool.cli.db import transaction


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


def _killed(slug: str, repo_cwd: Path) -> None:
    session_2.record_decision(slug=slug, decision="kill", rationale="Nikdo to nechce")


# 1 + 2 + 10 ---------------------------------------------------------------------------------


def test_ship_after_kill_says_ship_impossible(voted: dict[str, Any], repo_cwd: Path) -> None:
    slug = voted["slug"]
    _killed(slug, repo_cwd)
    with pytest.raises(ValueError) as exc:
        session_3.hardening_run(slug=slug)
    msg = str(exc.value)
    assert "Ship není možný" in msg and "retro lesson" in msg and "decide" not in msg


def test_status_overview_skips_killed_and_shows_lessons(
        voted: dict[str, Any], repo_cwd: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    _killed(slug, repo_cwd)
    capsys.readouterr()
    data = status.list_projects()
    assert data and all(r["status"] == "killed" for r in data)
    _run(monkeypatch, status)  # jediný projekt -> detail; vypnout přes dva projekty níže
    out = capsys.readouterr().out
    assert "Poučení: zatím nezapsáno" in out

    _run(monkeypatch, retro, "lesson", "--slug", slug, "--text", "Problém trápí jen vedení")
    out = capsys.readouterr().out
    assert "Problém trápí jen vedení" in out
    _run(monkeypatch, status, "--slug", slug)
    out = capsys.readouterr().out
    assert "Poučení (1): Problém trápí jen vedení" in out


def test_status_overview_without_open_project(
        voted: dict[str, Any], repo_cwd: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _killed(voted["slug"], repo_cwd)
    with transaction() as conn:   # druhý (zabitý) projekt, aby se nevypsal detail
        conn.execute("INSERT INTO projects (slug, name, status) SELECT 'druhy', 'Druhý', 'killed'")
    capsys.readouterr()
    _run(monkeypatch, status)
    out = capsys.readouterr().out
    assert "Žádný rozpracovaný projekt — nový přes /pm start" in out


# 3 ------------------------------------------------------------------------------------------


def test_retro_error_uses_placeholder_slug(monkeypatch: pytest.MonkeyPatch,
                                           capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["retro.py", "mereni"])
    with pytest.raises(SystemExit):
        retro.main()
    err = capsys.readouterr().err
    assert "--slug <slug>" in err and "--slug mereni" not in err
    assert len([ln for ln in err.split("Příklad správného použití:")[1].splitlines()
                if ln.strip()]) == 1


def test_wrapper_unknown_command_does_not_list_all() -> None:
    import os
    env = {**os.environ, "PFLANZER_PLUGIN_DIR": str(REPO_ROOT)}
    r = subprocess.run(["bash", str(REPO_ROOT / "tool" / "bin" / "pflanzer"), "statuss"],
                       capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 2 and "Přehled: pflanzer help" in r.stderr
    assert "Příkazy:" not in r.stderr


# 4 + 9 --------------------------------------------------------------------------------------


def test_ship_md_past_tense_and_no_empty_winner_heading(
        worktree_project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug, status="handoff")
    session_3.hardening_run(slug=slug)
    with transaction() as conn:
        conn.execute("UPDATE projects SET xyz_hypothesis = ? WHERE slug = ?",
                     ("Problém k vyřešení: **Checkout**. Ověříme ho na třech funkčních "
                      "variantách, mezi kterými se rozhodne nad běžícím kódem. Pilot.", slug))
    md = handoff_pr.render_ship_md(slug)
    assert "## Vítěz" not in md
    assert "Ověřili jsme na třech funkčních variantách; vyhrála A" in md
    assert "Ověříme ho" not in md
    assert md.index("## Co se mění") < md.index("Vítěz A")


def test_ship_warns_on_absurd_diff_size(worktree_project: dict[str, Any],
                                        vote: Callable[..., Any]) -> None:
    slug = worktree_project["slug"]
    vote(slug, status="handoff")
    session_3.hardening_run(slug=slug)
    with transaction() as conn:
        conn.execute("UPDATE extracted_code SET diff_loc_added = 25000")
    md = handoff_pr.render_ship_md(slug)
    assert "Rozsah vypadá nesmyslně" in md and "node_modules" in md


# 5 ------------------------------------------------------------------------------------------


def test_business_critical_suggests_kill_not_fix() -> None:
    assert feedback.is_business_critical("Byznys", "general")
    assert feedback.is_business_critical("Vývoj", "duplicita")
    assert not feedback.is_business_critical("Bezpečnost", "auth")


def test_feedback_cli_business_critical_next_step(
        voted: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    slug = voted["slug"]
    monkeypatch.setattr(sys, "argv", [
        "feedback.py", "add", "--slug", slug, "--variant", "A", "--role", "byznys",
        "--severity", "critical", "--text", "Problém už vyřešil jiný tým"])
    feedback.main()
    out = capsys.readouterr().out
    assert "Byznysový critical: zvažte Kill" in out and "--override-critical" in out
    assert "oprav to ve variantě" not in out


# 6 ------------------------------------------------------------------------------------------


def test_tier_overview_lists_tiers(capsys: pytest.CaptureFixture[str],
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["tier.py"])
    tier.main()
    out = capsys.readouterr().out
    for word in ("quick", "lean", "full", "3 dny", "3–5 dní", "5–7 dní"):
        assert word in out


# 7 ------------------------------------------------------------------------------------------


def test_doctor_warns_when_yaml_adapter_without_pyyaml(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    assert doctor.check_gates_yaml(repo) is None
    (repo / "pflanzer.gates.yml").write_text("lint: {}\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "yaml", None)   # import yaml -> ImportError
    row = doctor.check_gates_yaml(repo)
    assert row and row["status"] == doctor.WARN
    assert "pflanzer.gates.json" in row["advice"] and "pip install pyyaml" in row["advice"]


def test_install_sh_tries_pyyaml_nonblocking() -> None:
    text = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    assert "pip install --user --quiet pyyaml" in text and "import yaml" in text


# 8 ------------------------------------------------------------------------------------------


def test_no_dopravit_in_user_output() -> None:
    for path in (REPO_ROOT / "tool" / "cli").glob("*.py"):
        assert "Dopravit" not in path.read_text(encoding="utf-8"), path


# 9 ------------------------------------------------------------------------------------------


def _git_repo(path: Path, files: dict[str, str]) -> Path:
    path.mkdir()
    git(path, "init", "-q")
    for name, content in files.items():
        (path / name).write_text(content, encoding="utf-8")
    return path


def test_init_gitignore_node(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path / "n", {"package.json": json.dumps(
        {"name": "x", "scripts": {"build": "tsc"}})})
    init.init(repo)
    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "node_modules/" in lines and "dist/" in lines and "extracted/" in lines


def test_init_gitignore_node_without_build_has_no_dist(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path / "n2", {"package.json": json.dumps({"name": "x"}),
                                       ".gitignore": "node_modules/\n"})
    init.init(repo)
    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "dist/" not in lines and lines.count("node_modules/") == 1


def test_init_gitignore_python(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path / "p", {"pyproject.toml": "[project]\nname = 'x'\n"})
    init.init(repo)
    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".venv/" in lines and "__pycache__/" in lines
