"""Expertní panel (UX): zkrácený `help`, alias `record`, `pflanzer share`."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tool.cli import share

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN = REPO_ROOT / "tool" / "bin" / "pflanzer"


def _cli(*args: str, home: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HOME": str(home), "PFLANZER_DATA": str(home / "data"),
           "PFLANZER_DB": str(home / "data" / "t.db"), "TZ": "UTC"}
    return subprocess.run([str(BIN), *args], capture_output=True, text=True, timeout=60, env=env)


def test_help_default_is_path_only(tmp_path: Path) -> None:
    out = _cli("help", home=tmp_path).stdout
    assert "pflanzer.cz/method" in out
    for cmd in ("start", "build", "prompts", "share", "record", "feedback", "decide", "ship",
                "checkpoint", "status", "doctor"):
        assert f"pflanzer {cmd}" in out
    order = [out.index(f"pflanzer {c}") for c in ("start", "build", "prompts", "record", "share",
                                                  "feedback", "decide", "ship", "checkpoint")]
    assert order == sorted(order)
    assert "session_2" not in out and "a11y_html" not in out and "apprun" not in out
    assert "pflanzer vote" not in out
    assert "help --all" in out


def test_help_all_lists_modules(tmp_path: Path) -> None:
    out = _cli("help", "--all", home=tmp_path).stdout
    assert "pflanzer session_2" in out and "pflanzer share" in out


def test_record_and_hidden_vote_alias_same_target(tmp_path: Path) -> None:
    rec = _cli("record", "--help", home=tmp_path)
    vote = _cli("vote", "--help", home=tmp_path)
    assert rec.returncode == 0 and rec.stdout == vote.stdout and "--spec" in rec.stdout
    assert "pflanzer vote" not in _cli("build", home=tmp_path).stdout


def test_share_message_has_no_cli_and_password_separate() -> None:
    msg = share.share_text("https://x.trycloudflare.com/method/", "pátek 17:00")
    assert "https://x.trycloudflare.com/method/" in msg and "pátek 17:00" in msg
    assert "heslo" not in msg.lower() and "pflanzer" not in msg.lower()


@pytest.fixture
def fake_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    calls: dict[str, Any] = {"killed": [], "down": []}
    monkeypatch.setattr(share.preview, "preview_dir", lambda: tmp_path / "preview")

    def fake_up(slug: str, **kw: Any) -> dict[str, Any]:
        calls["up"] = kw
        return {"slug": slug, "user": "pflanzer", "password": kw["password"], "warnings": [],
                "variants": {"A": {"url": "http://a"}, "B": {"url": "http://b"}}}

    monkeypatch.setattr(share.preview, "up", fake_up)
    monkeypatch.setattr(share.preview, "down",
                        lambda slug, variants=None: calls["down"].append(slug) or
                        {"stopped": ["A", "B"], "was_running": True})
    monkeypatch.setattr(share.hub, "resolve_tunnel", lambda mode: False)
    monkeypatch.setattr(share.hub, "port_free", lambda host, port: True)
    monkeypatch.setattr(share.hub, "wait_listening", lambda *a, **k: True)
    monkeypatch.setattr(share.preview, "_lan_ip", lambda: "192.0.2.7")
    monkeypatch.setattr(share.preview, "hub_data", lambda: {"lan_url": "http://192.0.2.7:8701/method/"})

    class P:
        pid = 424242

    def fake_start(port: int, host: str, password: str, tunnel: str, log: Path) -> Any:
        calls["hub"] = (port, host, password, tunnel)
        return P(), "started"

    monkeypatch.setattr(share, "start_hub", fake_start)
    monkeypatch.setattr(share.preview, "_alive", lambda pid, started: True)
    monkeypatch.setattr(share.apprun, "kill_group",
                        lambda pid, *a, **k: calls["killed"].append(pid))
    return calls


def test_share_up_and_down(fake_env: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    share.main(["--slug", "demo", "--password", "tajne123", "--deadline", "pátek 17:00"])
    out = capsys.readouterr().out
    assert fake_env["up"]["password"] == "tajne123" and fake_env["up"]["host"] == "0.0.0.0"
    port, host, pw, tunnel = fake_env["hub"]
    assert port not in share.RESERVED_PORTS and pw == "tajne123" and tunnel == "none"
    assert "http://192.0.2.7:8701/method/" in out and "pátek 17:00" in out
    assert "jiným kanálem" in out and "tajne123" in out
    msg = [ln for ln in out.splitlines() if ln.startswith("> ")]
    assert not any("tajne123" in ln or "pflanzer" in ln.lower() for ln in msg)
    assert share.load_state("demo")["hub_pid"] == 424242

    share.main(["down", "--slug", "demo"])
    assert fake_env["killed"] == [424242] and fake_env["down"] == ["demo"]
    assert share.load_state("demo") is None


def test_share_rejects_second_run(fake_env: dict[str, Any]) -> None:
    share.up("demo", password="x1")
    with pytest.raises(ValueError, match="už běží"):
        share.up("demo")
    json.dumps(share.load_state("demo"))
    share.down("demo")
