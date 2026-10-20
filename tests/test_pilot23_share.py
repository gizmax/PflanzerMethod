"""Pilot 23: `share` hlásí průběh, při selhání hubu uklidí a umí převzít běžící preview."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tool.cli import hub, share


class _Proc:
    pid = 515151

    def __init__(self, dead: bool) -> None:
        self.dead = dead

    def poll(self) -> int | None:
        return 1 if self.dead else None


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    c: dict[str, Any] = {"down": [], "up": 0, "killed": [], "dead": False, "listen": True,
                         "pv_state": None}
    pdir = tmp_path / "preview"
    monkeypatch.setattr(share.preview, "preview_dir", lambda: pdir)

    def fake_up(slug: str, **kw: Any) -> dict[str, Any]:
        c["up"] += 1
        return {"slug": slug, "user": "pflanzer", "password": kw["password"], "warnings": [],
                "variants": {"A": {"url": "http://a"}}}

    monkeypatch.setattr(share.preview, "up", fake_up)
    monkeypatch.setattr(share.preview, "down",
                        lambda slug, variants=None: c["down"].append(slug) or
                        {"stopped": ["A"], "was_running": True})
    monkeypatch.setattr(share.preview, "load_state", lambda slug: c["pv_state"])
    monkeypatch.setattr(share.preview, "_variant_running", lambda v: {"app": True})
    monkeypatch.setattr(share.preview, "status", lambda slug, probe=True: {
        "password": "stare", "user": "pflanzer", "host": "0.0.0.0",
        "variants": {"A": {"url": "http://a", "local_url": "http://l", "tunnel_url": None}}})
    monkeypatch.setattr(share.preview, "_alive", lambda pid, started: False)
    monkeypatch.setattr(share.preview, "_lan_ip", lambda: "192.0.2.7")
    monkeypatch.setattr(share.preview, "hub_data", lambda: {})
    monkeypatch.setattr(share.hub, "resolve_tunnel", lambda mode: False)
    monkeypatch.setattr(share.hub, "port_free", lambda host, port: True)
    monkeypatch.setattr(share.hub, "wait_listening", lambda *a, **k: c["listen"])
    monkeypatch.setattr(share.apprun, "kill_group", lambda pid, *a, **k: c["killed"].append(pid))
    monkeypatch.setattr(share.apprun, "tail", lambda p, *a, **k: "ERROR: ResolutionImpossible")

    def fake_start(port: int, host: str, password: str, tunnel: str, log: Path) -> Any:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("ERROR: ResolutionImpossible\n", encoding="utf-8")
        return _Proc(c["dead"]), "started"

    monkeypatch.setattr(share, "start_hub", fake_start)
    return c


def test_progress_on_stderr_json_clean(env: dict[str, Any],
                                       capsys: pytest.CaptureFixture[str]) -> None:
    share.main(["--slug", "demo", "--tunnel", "none", "--password", "pw1", "--json"])
    cap = capsys.readouterr()
    assert "Spouštím varianty" in cap.err and "Připravuji hub" in cap.err
    assert "Hub běží" in cap.err
    assert json.loads(cap.out)["slug"] == "demo"


def test_hub_failure_stops_preview_and_explains(env: dict[str, Any]) -> None:
    env["listen"], env["dead"] = False, True
    with pytest.raises(RuntimeError) as ei:
        share.up("demo", password="pw1", tunnel="none")
    msg = str(ei.value)
    assert env["down"] == ["demo"]
    assert "ResolutionImpossible" in msg and "demo-hub.log" in msg
    assert "zkuste to znovu" in msg and "Offline" in msg
    assert share.load_state("demo") is None


def test_hub_failure_exit_code(env: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    env["listen"] = False
    with pytest.raises(SystemExit) as ei:
        share.main(["--slug", "demo", "--tunnel", "none"])
    assert ei.value.code != 0
    assert "Hub se nespustil" in capsys.readouterr().err


def test_second_share_takes_over_running_preview(env: dict[str, Any]) -> None:
    env["pv_state"] = {"password": "stare", "variants": {"A": {}}}
    res = share.up("demo", tunnel="none")
    assert env["up"] == 0 and res["password"] == "stare"
    assert res["variants"]["A"]["url"] == "http://a"


def test_takeover_failure_keeps_preview(env: dict[str, Any]) -> None:
    env["pv_state"] = {"password": "stare", "variants": {"A": {}}}
    env["listen"] = False
    with pytest.raises(RuntimeError, match="share down"):
        share.up("demo", tunnel="none")
    assert env["down"] == []


def test_venv_failure_removes_partial_venv(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hub, "DATA_ROOT", tmp_path)
    seen: list[list[str]] = []

    def fake_run(cmd: list[str], **kw: Any) -> Any:
        seen.append(cmd)
        if "venv" in cmd:
            (tmp_path / "hub-venv" / "bin").mkdir(parents=True)
            return subprocess.CompletedProcess(cmd, 0)
        if "pip" in cmd:
            raise subprocess.CalledProcessError(1, cmd)
        return subprocess.CompletedProcess(cmd, 1)  # probe selže

    monkeypatch.setattr(hub.subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError):
        hub._venv()
    pip = next(c for c in seen if "pip" in c)
    assert "--timeout" in pip and "--retries" in pip
    assert not (tmp_path / "hub-venv").exists()
