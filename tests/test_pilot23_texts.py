"""Pilot 23: texty reportu, úklid po Kill, mob + Kritické, názvy příkazů v nápovědě."""
from __future__ import annotations

import subprocess
from pathlib import Path

from tool.cli import report, status

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN = REPO_ROOT / "tool" / "bin" / "pflanzer"


def test_sentence_keeps_ordinals_and_abbreviations() -> None:
    t = "Po 2. kole web sám nenaplní metriku, např. konverzi. Druhá věta."
    assert report._sentence(t, 200) == "Po 2. kole web sám nenaplní metriku, např. konverzi."
    assert report._sentence("Hotovo, tj. vše. Další.", 200) == "Hotovo, tj. vše."


def test_shorten_cuts_on_word_boundary() -> None:
    out = report._shorten("slovo " * 60, 50)
    assert out.endswith("…") and len(out) <= 50 and not out[:-1].endswith("slov")


def test_decision_reason_not_cut_at_ordinal(project) -> None:
    from tool.cli.db import transaction
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects").fetchone()[0]
        conn.execute("INSERT INTO decisions (project_id, type, body_md, atribuce_user, "
                     "atribuce_ts) "
                     "VALUES (?, 'kill', ?, 'Tom', '2026-01-01T00:00:00')",
                     (pid, "### Důvod\nPo 2. kole web sám nenaplní metriku. Konec.\n"))
        assert report._decision_reason(conn, pid) == "Po 2. kole web sám nenaplní metriku. Konec."


def test_prompts_variants_deduplicated() -> None:
    src = (REPO_ROOT / "tool" / "cli" / "quick_session.py").read_text("utf-8")
    assert 'dict.fromkeys(out["variants_in_play"])' in src


def test_help_uses_public_command_names() -> None:
    for args, prog in ((["record", "--help"], "pflanzer record"),
                       (["decide", "--help"], "pflanzer decide")):
        res = subprocess.run([str(BIN), *args], capture_output=True, text=True, timeout=60)
        assert f"usage: {prog}" in res.stdout, res.stdout + res.stderr
        assert "quick_session" not in res.stdout and "session_2" not in res.stdout


def test_decide_resolve_and_prep_alias_parse() -> None:
    res = subprocess.run([str(BIN), "decide", "resolve", "--help"], capture_output=True,
                         text=True, timeout=60)
    assert "usage: pflanzer decide resolve" in res.stdout, res.stdout + res.stderr


def test_cleanup_prefers_share_down(monkeypatch, tmp_path: Path) -> None:
    import os

    from tool.cli import preview, share
    monkeypatch.setattr(share, "load_state",
                        lambda slug: {"hub_pid": os.getpid(), "hub_started": ""})
    monkeypatch.setattr(preview, "_alive", lambda pid, started: True)
    pdir = tmp_path / "data" / "preview"
    pdir.mkdir(parents=True)
    import json

    from tool.cli import db
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path / "data")
    (pdir / "s.json").write_text(json.dumps({"variants": {"A": {"app_pid": os.getpid()}}}))
    steps = status.cleanup_steps("s")
    assert any("pflanzer share down --slug s" in x for x in steps)
