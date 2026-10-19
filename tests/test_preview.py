"""preview.py (auth proxy, štítek, tunel, down) + brána smoke (apprun)."""
from __future__ import annotations

import base64
import http.client
import json
import os
import random
import stat
import subprocess
import sys
import textwrap
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tool.cli import apprun, preview
from tool.cli import quality_gates as qg
from tool.cli.db import transaction

APP = textwrap.dedent('''
    import sys
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, ctype, body, extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self._send(200, "text/html; charset=utf-8",
                           "<html><body class='x'><h1>Ahoj</h1></body></html>".encode())
            elif self.path == "/own":
                self._send(200, "text/html", b"<body><p>Varianta Z k rozhodnuti</p></body>")
            elif self.path == "/t.txt":
                self._send(200, "text/plain", b"<body>plain</body>")
            elif self.path == "/r":
                self._send(302, "text/plain", b"",
                           {"Location": "http://127.0.0.1:%d/t.txt" % PORT})
            else:
                self._send(404, "text/plain", b"nope")

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            self._send(200, "text/plain", b"echo:" + self.rfile.read(n))

    PORT = int(sys.argv[1])
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
''')

NOT_FOUND_APP = textwrap.dedent('''
    import sys
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            ok = self.path == "/ok"
            self.send_response(200 if ok else 404)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"hi")

    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
''')


def _base_port() -> int:
    for _ in range(200):
        b = random.randint(20000, 40000)
        ports = [b + i for i in (0, 1, 10, 11, 20, 21)]
        if all(apprun.port_free(p) for p in ports):
            return b
    raise AssertionError("žádné volné porty")


def _make_app(root: Path, source: str, *, command: str | None = None,
              smoke_paths: list[str] | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "app.py").write_text(source, encoding="utf-8")
    if command is None:
        command = f'{sys.executable} app.py {{port}}'
    toml = f"[preview]\ncommand = {json.dumps(command)}\n"
    if smoke_paths is not None:
        toml += f"smoke_paths = {json.dumps(smoke_paths)}\n"
    (root / ".pflanzer").mkdir(exist_ok=True)
    (root / ".pflanzer" / "project.toml").write_text(toml, encoding="utf-8")
    return root


def _get(port: int, path: str = "/", *, pw: str | None = "tajne", method: str = "GET",
         body: bytes | None = None) -> tuple[int, dict[str, str], bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {}
    if pw is not None:
        headers["Authorization"] = "Basic " + base64.b64encode(f"pflanzer:{pw}".encode()).decode()
    conn.request(method, path, body=body, headers=headers)
    r = conn.getresponse()
    data = r.read()
    out = (r.status, {k.lower(): v for k, v in r.getheaders()}, data)
    conn.close()
    return out


@pytest.fixture
def preview_env(tmp_path: Path, tmp_db: Path, monkeypatch: pytest.MonkeyPatch,
                ) -> Iterator[dict[str, Any]]:
    from tool.cli import db
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(preview, "hub_running", lambda: False)
    monkeypatch.setattr(preview.shutil, "which", lambda name, *a, **k: None
                        if name == "cloudflared" else __import__("shutil").which(name))
    dirs = {v: _make_app(tmp_path / "wt" / f"x-{v}", APP) for v in "ABC"}
    monkeypatch.setattr(preview, "_primary_dirs", lambda slug: dict(dirs))
    env = {"slug": "checkout", "dirs": dirs, "base": _base_port()}
    yield env
    state = preview.load_state("checkout")
    pids = []
    if state:
        for v in state["variants"].values():
            pids += [pid for pid, _ in preview._pids(v).values()]
    preview.down("checkout")
    for pid in pids:  # pojistka: nic nesmí zůstat
        if apprun.proc_alive(pid):
            apprun.kill_group(pid)


def test_up_proxy_auth_label_url_and_down(preview_env: dict[str, Any], project: dict[str, Any],
                                          vote: Any) -> None:
    slug = preview_env["slug"]
    vote(slug)
    res = preview.up(slug, password="tajne", tunnel="none", base_port=preview_env["base"],
                     deadline="pátek 17:00")
    assert set(res["variants"]) == {"A", "B", "C"}
    base = preview_env["base"]
    a_proxy = base + 1
    assert res["variants"]["A"]["url"] == f"http://127.0.0.1:{a_proxy}/"
    assert res["variants"]["C"]["proxy_port"] == base + 21

    # heslo: bez něj / se špatným 401, se správným 200
    assert _get(a_proxy, pw=None)[0] == 401
    assert _get(a_proxy, pw="spatne")[0] == 401
    code, hdrs, body = _get(a_proxy)
    assert code == 200
    assert "noindex" in hdrs["x-robots-tag"]
    text = body.decode()
    assert "Varianta A k rozhodnutí — není to hotový produkt" in text
    assert text.index("<body class='x'>") < text.index("data-pflanzer-label") < text.index("<h1>")
    assert "Varianta B k rozhodnutí" in _get(base + 11)[2].decode()
    # štítek se nevkládá podruhé ani do jiných typů
    assert b"data-pflanzer-label" not in _get(a_proxy, "/own")[2]
    assert _get(a_proxy, "/t.txt")[2] == b"<body>plain</body>"
    # POST a hlavičky, redirect (Location bez interního portu)
    assert _get(a_proxy, "/x", method="POST", body=b"abc")[2] == b"echo:abc"
    code, hdrs, _ = _get(a_proxy, "/r")
    assert code == 302 and hdrs["location"] == "/t.txt"
    assert _get(a_proxy, "/nic")[0] == 404

    # prototype_url v DB + stav na disku
    with transaction() as conn:
        urls = dict(conn.execute(
            "SELECT v.name, v.prototype_url FROM variants v").fetchall())
    assert urls["A"] == f"http://127.0.0.1:{a_proxy}/"
    assert urls["C"] == res["variants"]["C"]["url"]
    state = json.loads(preview.state_path(slug).read_text(encoding="utf-8"))
    assert state["password"] == "tajne"
    pids = [pid for v in state["variants"].values() for pid, _ in preview._pids(v).values()]
    assert len(pids) == 6 and all(apprun.proc_alive(p) for p in pids)
    assert stat.S_IMODE(preview.state_path(slug).stat().st_mode) == 0o600

    st = preview.status(slug)
    assert st["running"] and all(v["ok"] for v in st["variants"].values())

    stopped = preview.down(slug)
    assert stopped["was_running"] and sorted(stopped["stopped"]) == ["A", "B", "C"]
    assert not any(apprun.proc_alive(p) for p in pids)
    assert not preview.state_path(slug).exists()
    assert preview.status(slug)["running"] is False
    assert apprun.http_get(f"http://127.0.0.1:{a_proxy}/", timeout=1) is None


def test_message_and_cli_json(preview_env: dict[str, Any], capsys: pytest.CaptureFixture[str],
                              project: dict[str, Any]) -> None:
    slug = preview_env["slug"]
    preview.main(["up", "--slug", slug, "--tunnel", "none", "--password", "abc123",
                  "--base-port", str(preview_env["base"]), "--deadline", "pátek 17:00",
                  "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["password"] == "abc123"
    assert "pátek 17:00" in out["message"] and "abc123" in out["message"]
    assert out["message"].count("http://127.0.0.1:") == 3
    # druhé up bez down = lidská chyba, nic se nerozbije
    with pytest.raises(SystemExit):
        preview.main(["up", "--slug", slug, "--tunnel", "none"])
    assert "už běží" in capsys.readouterr().err
    preview.main(["status", "--slug", slug])
    assert "Varianta A: běží" in capsys.readouterr().out
    preview.main(["down", "--slug", slug])
    assert "Preview zastaveno" in capsys.readouterr().out


def test_human_output(preview_env: dict[str, Any], capsys: pytest.CaptureFixture[str],
                      project: dict[str, Any]) -> None:
    preview.main(["up", "--slug", preview_env["slug"], "--tunnel", "none",
                  "--base-port", str(preview_env["base"])])
    out = capsys.readouterr().out
    assert out.startswith("**Pflanzer Method | pflanzer.cz/method**")
    assert "Zpráva k přeposlání" in out and "**Další krok:**" in out
    assert "Odkazy fungují jen na tomto počítači" in out
    preview.down(preview_env["slug"])


def test_tunnel_url_is_stored_and_killed(preview_env: dict[str, Any], project: dict[str, Any],
                                         vote: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    slug = preview_env["slug"]
    vote(slug)
    monkeypatch.setattr(preview.shutil, "which", lambda name, *a, **k: "/x/cloudflared")
    tunnels: list[int] = []

    def fake_tunnel(port: int, log: Path, timeout: float = 0) -> tuple[int, str, str]:
        p = subprocess.Popen(["sleep", "60"], start_new_session=True)
        tunnels.append(p.pid)
        return p.pid, apprun.proc_started(p.pid), f"https://t-{port}.trycloudflare.com"

    monkeypatch.setattr(preview, "start_tunnel", fake_tunnel)
    res = preview.up(slug, tunnel="auto", base_port=preview_env["base"])
    assert res["variants"]["A"]["url"] == f"https://t-{preview_env['base'] + 1}.trycloudflare.com"
    assert any("Cloudflare" in w for w in res["warnings"])
    with transaction() as conn:
        url = conn.execute("SELECT prototype_url FROM variants WHERE name = 'B'").fetchone()[0]
    assert url.startswith("https://t-") and url.endswith(".trycloudflare.com")
    assert len(tunnels) == 3 and all(apprun.proc_alive(p) for p in tunnels)
    preview.down(slug)
    assert not any(apprun.proc_alive(p) for p in tunnels)


def test_start_tunnel_parses_cloudflared_output(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    exe = tmp_path / "bin" / "cloudflared"
    exe.parent.mkdir()
    exe.write_text('#!/bin/sh\necho "INF |  https://foo-bar-1.trycloudflare.com  |" >&2\n'
                   "sleep 30\n", encoding="utf-8")
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", f"{exe.parent}{os.pathsep}{os.environ['PATH']}")
    res = preview.start_tunnel(8601, tmp_path / "t.log", timeout=10)
    assert res is not None
    try:
        assert res[2] == "https://foo-bar-1.trycloudflare.com"
    finally:
        apprun.kill_group(res[0])
    assert not apprun.proc_alive(res[0])


def test_variant_that_does_not_start_gives_log_tail_and_cleans_up(
        preview_env: dict[str, Any], project: dict[str, Any]) -> None:
    _make_app(preview_env["dirs"]["B"], APP, command=f"{sys.executable} -c "
              "\"print('boom: chybí modul'); raise SystemExit(3)\"")
    with pytest.raises(RuntimeError) as err:
        preview.up(preview_env["slug"], tunnel="none", base_port=preview_env["base"],
                   timeout=15)
    msg = str(err.value)
    assert "Varianta B nenaběhla" in msg and "boom: chybí modul" in msg
    assert not preview.state_path(preview_env["slug"]).exists()
    assert apprun.port_free(preview_env["base"]) and apprun.port_free(preview_env["base"] + 1)


def test_missing_command_and_empty_password(preview_env: dict[str, Any],
                                            project: dict[str, Any]) -> None:
    empty = preview_env["dirs"]["C"].parent / "empty"
    empty.mkdir()
    preview_env["dirs"]["C"] = empty
    with pytest.raises(ValueError, match=r"\[preview\]"):
        preview.up(preview_env["slug"], tunnel="none", base_port=preview_env["base"])
    with pytest.raises(ValueError, match="Heslo"):
        preview.up(preview_env["slug"], password=" ", tunnel="none")
    assert not preview.state_path(preview_env["slug"]).exists()


def test_lan_host_warns(preview_env: dict[str, Any], project: dict[str, Any]) -> None:
    res = preview.up(preview_env["slug"], tunnel="none", host="0.0.0.0",
                     base_port=preview_env["base"])
    assert any("bez šifrování" in w for w in res["warnings"])
    assert not res["variants"]["A"]["url"].startswith("http://0.0.0.0")
    preview.down(preview_env["slug"])


def test_inject_label_unit() -> None:
    assert b"data-pflanzer-label" in preview.inject_label(b"<HTML><BODY><p>x", "A")
    assert preview.inject_label(b"<p>bez body</p>", "A") == b"<p>bez body</p>"
    same = "<body>Varianta A — k rozhodnutí</body>".encode()
    assert preview.inject_label(same, "A") == same


def test_detect_run(tmp_path: Path) -> None:
    node = tmp_path / "n"
    node.mkdir()
    (node / "package.json").write_text(json.dumps({"scripts": {"start": "node s.js"}}))
    spec = apprun.detect_run(node, 8601)
    assert spec and spec.argv == ["npm", "start"] and spec.env["PORT"] == "8601"
    (node / "package.json").write_text(json.dumps({"scripts": {"dev": "vite", "start": "x"}}))
    spec = apprun.detect_run(node, 8611)
    assert spec and spec.argv[:3] == ["npm", "run", "dev"] and "8611" in spec.argv
    py = tmp_path / "p"
    (py / "svc").mkdir(parents=True)
    (py / "svc" / "__main__.py").write_text("print(1)")
    (py / ".venv" / "bin").mkdir(parents=True)
    (py / ".venv" / "bin" / "python").write_text("")
    spec = apprun.detect_run(py, 8601)
    assert spec and spec.argv == [str(py / ".venv/bin/python"), "-m", "svc"]
    mk = tmp_path / "m"
    mk.mkdir()
    (mk / "Makefile").write_text("run:\n\techo hi\n")
    spec = apprun.detect_run(mk, 8601)
    assert spec and spec.command == "make run" and spec.env["PORT"] == "8601"
    assert apprun.detect_run(tmp_path, 8601) is None


# --------------------------------------------------------------------------
# Brána smoke
# --------------------------------------------------------------------------


def _smoke(path: Path) -> qg.GateResult:
    return qg.GATE_RUNNERS["smoke"](qg._make_ctx(path)[0])


def test_smoke_pass(tmp_path: Path) -> None:
    app = _make_app(tmp_path / "ok", APP)
    res = _smoke(app)
    assert res.status == "pass" and "/ odpovídá 200" in res.details
    assert res.details.startswith("smoke:")


def test_smoke_fail_on_404_root(tmp_path: Path) -> None:
    app = _make_app(tmp_path / "nf", NOT_FOUND_APP)
    res = _smoke(app)
    assert res.status == "fail" and "/ odpovídá 404" in res.details


def test_smoke_paths_all_checked(tmp_path: Path) -> None:
    good = _make_app(tmp_path / "g", APP, smoke_paths=["/", "/t.txt"])
    assert _smoke(good).status == "pass"
    bad = _make_app(tmp_path / "b", APP, smoke_paths=["/", "/rezervace"])
    res = _smoke(bad)
    assert res.status == "fail" and "/rezervace odpovídá 404" in res.details


def test_smoke_without_command_is_unverified(tmp_path: Path) -> None:
    (tmp_path / "x").mkdir()
    res = _smoke(tmp_path / "x")
    assert res.status == "skipped" and res.details.startswith(qg.UNVERIFIED_PREFIX)
    assert qg.unverified_gates([res])[0]["reason"] == "chybí příkaz pro spuštění"
    assert qg.aggregate_score([res])["gates_run"] == 0


def test_smoke_app_that_crashes_fails_with_log(tmp_path: Path) -> None:
    app = _make_app(tmp_path / "c", APP, command=f"{sys.executable} -c "
                    "\"print('spadlo to'); raise SystemExit(1)\"")
    res = _smoke(app)
    assert res.status == "fail" and "spadlo to" in res.details


def test_smoke_in_gate_types_and_score(tmp_path: Path) -> None:
    assert "smoke" in qg.GATE_TYPES and len(qg.GATE_TYPES) == 10
    assert set(qg.GATE_TYPES) == set(qg.GATE_RUNNERS) == set(qg.GATE_WEIGHTS)
    app = _make_app(tmp_path / "s", APP)
    results = qg.run_gates_on_path(app)
    assert len(results) == 10
    assert {r.gate_type: r.status for r in results}["smoke"] == "pass"
