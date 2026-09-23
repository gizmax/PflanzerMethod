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
