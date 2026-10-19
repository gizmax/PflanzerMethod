"""DB path priority: PFLANZER_DB > existing ~/.pflanzer/pflanzer.db > data/pflanzer.db."""
from __future__ import annotations

from pathlib import Path

import pytest

from tool.cli.db import REPO_ROOT, _resolve_db_path


def test_env_override_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = Path.home()
    (home / ".pflanzer").mkdir()
    (home / ".pflanzer" / "pflanzer.db").touch()
    explicit = tmp_path / "explicit.db"
    monkeypatch.setenv("PFLANZER_DB", str(explicit))
    assert _resolve_db_path() == explicit


def test_installed_db_file_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PFLANZER_DB")
    user_db = Path.home() / ".pflanzer" / "pflanzer.db"
    user_db.parent.mkdir()
    user_db.touch()
    assert _resolve_db_path() == user_db


def test_dev_mode_falls_back_to_repo_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PFLANZER_DB")
    assert _resolve_db_path() == REPO_ROOT / "data" / "pflanzer.db"


def test_targets_cache_dir_alone_does_not_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    """`worktree.py setup` creates ~/.pflanzer/targets — that must not move the DB."""
    monkeypatch.delenv("PFLANZER_DB")
    (Path.home() / ".pflanzer" / "targets").mkdir(parents=True)
    assert _resolve_db_path() == REPO_ROOT / "data" / "pflanzer.db"


def test_web_hub_resolves_same_db_as_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The hub (tool/web/backend/models.py) must read the same DB as the CLI."""
    import ast

    src = (REPO_ROOT / "tool" / "web" / "backend" / "models.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.parse(src).body
              if isinstance(n, ast.FunctionDef) and n.name == "_resolve_db_path")
    ns: dict[str, object] = {"Path": Path, "os": __import__("os"), "REPO_ROOT": REPO_ROOT}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "models.py", "exec"), ns)
    hub_resolve = ns["_resolve_db_path"]

    monkeypatch.setenv("PFLANZER_DB", str(tmp_path / "x.db"))
    assert hub_resolve() == _resolve_db_path() == tmp_path / "x.db"  # type: ignore[operator]
    monkeypatch.delenv("PFLANZER_DB")
    assert hub_resolve() == _resolve_db_path() == REPO_ROOT / "data" / "pflanzer.db"  # type: ignore[operator]
    user_db = Path.home() / ".pflanzer" / "pflanzer.db"
    user_db.parent.mkdir(parents=True, exist_ok=True)
    user_db.touch()
    assert hub_resolve() == _resolve_db_path() == user_db  # type: ignore[operator]
