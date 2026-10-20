"""Pilot 21: docs pro nováčka (okno Zadání, terminálová cesta, help)."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "tool" / "bin" / "pflanzer"


def _zacni() -> str:
    return (ROOT / "docs" / "zacni.md").read_text(encoding="utf-8")


def test_window_table_mentions_zadani() -> None:
    md = _zacni()
    table = md.split("Okna k podpisu")[1].split("###")[0]
    assert "Zadání" in table and "Bezpečnost a provoz" in table


def test_terminal_commands_present() -> None:
    md = _zacni()
    for cmd in ("feedback add", "retro measure", "report summary", "pflanzer ship --slug S"):
        assert cmd in md
    assert "PR do `main`" not in md


def test_help_lists_retro_and_merged_window() -> None:
    out = subprocess.run([str(BIN), "help"], capture_output=True, text=True).stdout
    assert "retro" in out and "bezpecnost-provoz" in out and "feedback add" in out
