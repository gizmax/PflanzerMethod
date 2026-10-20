"""Pilot 8 (Autoservis Píst) — multi-repo preview, validace hlasu, prompty per repo, aliasy."""
from __future__ import annotations

import http.server
import json
import random
import subprocess
import sys
import textwrap
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from tool.cli import apprun, preview, quick_session, session_2
from tool.cli.quick_session import record_voting
from tool.cli.worktree import TargetRepo

REPO_ROOT = Path(__file__).resolve().parents[1]

API_APP = textwrap.dedent('''
    import sys
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            body = b"pong-from-api"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
''')

WEB_APP = textwrap.dedent('''
    import os, sys, urllib.request
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            api = os.environ.get("API_URL", "")
            same = os.environ.get("PFLANZER_API_URL", "") == api
            try:
                got = urllib.request.urlopen(api + "/ping", timeout=5).read().decode()
                code = 200
            except Exception as exc:
                got, code = "ERR %r" % (exc,), 502
            body = ("<html><body>web:%s:%s</body></html>" % (got, same)).encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
''')


def _base_port() -> int:
    for _ in range(200):
        b = random.randint(20000, 38000)
        if all(apprun.port_free(p) for p in (b, b + 1, b + 1001, b + 1002)):
            return b
    raise AssertionError("žádné volné porty")


@pytest.fixture
def multi_env(tmp_path: Path, tmp_db: Path,
              monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    from tool.cli import db
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(preview, "hub_running", lambda: False)
    monkeypatch.setattr(preview.shutil, "which", lambda name, *a, **k: None
                        if name == "cloudflared" else __import__("shutil").which(name))
    web = tmp_path / "wt" / "web-A"
    api = tmp_path / "wt" / "web-A-api"
    for d, src in ((web, WEB_APP), (api, API_APP)):
        d.mkdir(parents=True)
        (d / "app.py").write_text(src, encoding="utf-8")
    (web / ".pflanzer").mkdir()
    py = json.dumps(f"{sys.executable} app.py {{port}}")
    # příkaz sekundárního repa je v project.toml primárního: [preview.api]
    (web / ".pflanzer" / "project.toml").write_text(
        f"[preview]\ncommand = {py}\n\n[preview.api]\ncommand = {py}\n", encoding="utf-8")
    monkeypatch.setattr(preview, "_primary_dirs", lambda slug: {"A": web})
    monkeypatch.setattr(preview, "_secondary_dirs", lambda slug: {"api": {"A": api}})
    env = {"slug": "pist", "base": _base_port()}
    yield env
    state = preview.load_state("pist")
    pids = []
    if state:
        for v in state["variants"].values():
            pids += [pid for pid, _ in preview._pids(v).values()]
    preview.down("pist")
    for pid in pids:
        if apprun.proc_alive(pid):
            apprun.kill_group(pid)


def test_multi_repo_preview_primary_calls_secondary_via_env(multi_env: dict[str, Any]) -> None:
    res = preview.up("pist", password="tajne", tunnel="none", base_port=multi_env["base"],
                     timeout=30)
    v = res["variants"]["A"]
    assert v["repos"]["api"]["port"] == multi_env["base"] + 1001
    code, body = _fetch(v["proxy_port"])
    assert code == 200, body
    assert "pong-from-api" in body and ":True" in body   # API_URL == PFLANZER_API_URL

    st = preview.status("pist")
    assert st["running"] is True
    assert st["variants"]["A"]["repos"]["api"]["alive"] is True
    state = preview.load_state("pist")
    pids = list(preview._pids(state["variants"]["A"]).items())
    assert {"app", "proxy", "api"} <= {k for k, _ in pids}

    out = preview.down("pist")
    assert out["was_running"] is True
    for _k, (pid, _s) in pids:
        assert not apprun.proc_alive(pid)


def _fetch(port: int) -> tuple[int, str]:
    import base64
    import http.client
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", "/", headers={"Authorization": "Basic "
                                      + base64.b64encode(b"pflanzer:tajne").decode()})
    r = conn.getresponse()
    return r.status, r.read().decode()


def test_secondary_without_command_is_skipped_with_hint(
        multi_env: dict[str, Any], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    empty = tmp_path / "wt" / "lib"
    empty.mkdir(parents=True)
    monkeypatch.setattr(preview, "_secondary_dirs", lambda slug: {"lib": {"A": empty}})
    (tmp_path / "wt" / "web-A" / "app.py").write_text(API_APP, encoding="utf-8")  # vždy 200
    res = preview.up("pist", password="tajne", tunnel="none", base_port=multi_env["base"],
                     timeout=30)
    assert any("[preview.lib]" in w for w in res["warnings"])
    assert res["variants"]["A"]["repos"] == {}


def test_detect_run_role_block(tmp_path: Path) -> None:
    (tmp_path / ".pflanzer").mkdir()
    (tmp_path / ".pflanzer" / "project.toml").write_text(
        '[preview]\ncommand = "web {port}"\n[preview.api]\ncommand = "api --p {port}"\n',
        encoding="utf-8")
    other = tmp_path / "api"
    other.mkdir()
    assert apprun.detect_run(tmp_path, 7000).command == "web 7000"
    spec = apprun.detect_run(other, 8000, role="api", config_wt=tmp_path)
    assert spec is not None and spec.command == "api --p 8000"


# --------------------------------------------------------------------------
# hub / zpráva k přeposlání
# --------------------------------------------------------------------------


class _Hub(http.server.BaseHTTPRequestHandler):
    health = b'{"status": "ok"}'

    def log_message(self, *a: Any) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/api/health" and self.health:
            body, code = self.health, 200
        elif self.path == "/method/":
            body, code = b"<html>hub</html>", 200
        else:
            body, code = b"nope", 404
        self.send_response(code)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _serve(handler: type) -> tuple[http.server.HTTPServer, int]:
    srv = http.server.HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, int(srv.server_address[1])


def test_hub_running_requires_pflanzer_hub(monkeypatch: pytest.MonkeyPatch) -> None:
    srv, port = _serve(_Hub)
    try:
        monkeypatch.setattr(preview, "HUB_HEALTH_URL", f"http://127.0.0.1:{port}/api/health")
        monkeypatch.setattr(preview, "HUB_URL", f"http://127.0.0.1:{port}/method/")
        assert preview.hub_running() is True
    finally:
        srv.shutdown()
    other = type("Other", (_Hub,), {"health": b""})   # cizí server na :8000, health 404
    srv2, port2 = _serve(other)
    try:
        monkeypatch.setattr(preview, "HUB_HEALTH_URL", f"http://127.0.0.1:{port2}/api/health")
        monkeypatch.setattr(preview, "HUB_URL", f"http://127.0.0.1:{port2}/method/")
        assert preview.hub_running() is False
    finally:
        srv2.shutdown()


def test_share_message_without_hub_has_feedback_line() -> None:
    res = {"variants": {"A": {"url": "http://x/"}}, "password": "p", "user": "pflanzer"}
    msg = preview.share_message(res, None)
    assert "pflanzer " not in msg and "Feedback napište" in msg
    assert "localhost:8000" not in msg
    assert "localhost:8000" in preview.share_message(res, preview.HUB_URL)


# --------------------------------------------------------------------------
# vote
# --------------------------------------------------------------------------


def _votes(**rp: Any) -> list[dict[str, Any]]:
    pref = {"role_idx": 1, "user_value": 0.8, "effort": 0.3, "risk": 0.2, "strategic_fit": 0.7,
            "commitment_level": 2, "rationale": "proč"}
    pref.update(rp)
    return [{"name": "A", "builder": "claude-code", "description": "A",
             "role_preferences": [pref]}]


DECIDER = {"shortlist": ["A"], "rationale": "r", "veto_register": [], "parking_lot": []}


@pytest.mark.parametrize("bad,needle", [
    ({"commitment_level": 5}, "commitment_level"),
    ({"commitment_level": -1}, "commitment_level"),
    ({"commitment_level": 1.5}, "commitment_level"),
    ({"user_value": 1.4}, "user_value"),
    ({"role_idx": 40}, "role_idx"),
])
def test_vote_validates_ranges_before_write(project: dict[str, Any], bad: dict[str, Any],
                                            needle: str) -> None:
    with pytest.raises(ValueError, match=needle) as exc:
        record_voting(slug=project["slug"], facilitator="F", votes=_votes(**bad),
                      decider_call=DECIDER)
    assert "0" in str(exc.value)
    from tool.cli.db import transaction
    with transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM variants").fetchone()[0] == 0


def test_vote_warns_on_dead_localhost_url(project: dict[str, Any]) -> None:
    port = _base_port()
    out = record_voting(slug=project["slug"], facilitator="F", votes=_votes(),
                        decider_call=DECIDER, real_urls={"A": f"http://127.0.0.1:{port}/"})
    assert any(f"http://127.0.0.1:{port}/ neodpovídá" in w and "pflanzer share" in w
               for w in out["warnings"])
    srv, live = _serve(_Hub)
    try:
        out2 = record_voting(slug=project["slug"], facilitator="F", votes=_votes(),
                             decider_call=DECIDER, real_urls={"A": f"http://127.0.0.1:{live}/method/"})
    finally:
        srv.shutdown()
    assert not any("neodpovídá" in w for w in out2["warnings"])


# --------------------------------------------------------------------------
# prep --winner
# --------------------------------------------------------------------------


def test_prep_recommends_leading_variant(project: dict[str, Any]) -> None:
    votes = []
    for name, uv in (("A", 0.4), ("B", 0.9)):
        votes.append({"name": name, "builder": "claude-code", "description": name,
                      "role_preferences": [{"role_idx": 1, "user_value": uv, "effort": 0.3,
                                            "risk": 0.2, "strategic_fit": 0.7,
                                            "commitment_level": 3, "rationale": "proč"}]})
    record_voting(slug=project["slug"], facilitator="F", votes=votes,
                  decider_call={"shortlist": ["A", "B"], "rationale": "r",
                                "veto_register": [], "parking_lot": []})
    out = session_2.prep(project["slug"])
    assert out["recommended_winner"] == "B"
    title, lines, warns, nxt, _ctx = session_2._prep_view(out)
    assert "--winner B" in nxt or "feedback" in nxt   # Go návrh jen když je tým připraven
    out["ready_for_decision"] = True
    out["open_critical"] = []
    _t, _l, _w, nxt2, _c = session_2._prep_view(out)
    assert "--winner B" in nxt2


# --------------------------------------------------------------------------
# prompty per repo
# --------------------------------------------------------------------------


@pytest.fixture
def two_repo_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                  ) -> Callable[[bool], list[TargetRepo]]:
    from tool.cli import quick_session as qs
    from tool.cli import worktree as wtm
    targets = tmp_path / "targets"
    monkeypatch.setattr(wtm, "TARGETS_CACHE", targets)

    def make(openapi: bool) -> list[TargetRepo]:
        web = targets / "pist-A"
        api = targets / "pist-A-api"
        web.mkdir(parents=True, exist_ok=True)
        api.mkdir(parents=True, exist_ok=True)
        (web / "package.json").write_text(json.dumps(
            {"name": "w", "scripts": {"test": "node --test", "lint": "eslint ."}}),
            encoding="utf-8")
        (api / "Makefile").write_text("test:\n\tpytest\nlint:\n\truff .\n", encoding="utf-8")
        (api / "pyproject.toml").write_text("[project]\nname='a'\n", encoding="utf-8")
        if openapi:
            (api / "openapi.yaml").write_text("openapi: 3.0.0\n", encoding="utf-8")
        return [TargetRepo("web", "file:///x/web.git"), TargetRepo("api", "file:///x/api.git")]

    monkeypatch.setattr(qs, "variant_worktrees", wtm.variant_worktrees)
    return make


def test_repo_lines_per_repo_checks_and_openapi_only_when_present(
        two_repo_dirs: Callable[[bool], list[TargetRepo]]) -> None:
    repos = two_repo_dirs(False)
    lines = "\n".join(quick_session._repo_lines("pist", "A", repos))
    assert "`npm test`" in lines and "`make test`" in lines
    assert "CONTRACT-FIRST" not in lines
    repos = two_repo_dirs(True)
    assert "CONTRACT-FIRST" in "\n".join(quick_session._repo_lines("pist", "A", repos))
    rules = quick_session._multi_repo_rules("pist", "A", repos)
    assert "`web`" in rules and "`api`" in rules and "API_URL" in rules


def test_feature_found_in_any_repo(two_repo_dirs: Callable[[bool], list[TargetRepo]],
                                   tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tool.cli import worktree as wtm
    repos = two_repo_dirs(False)
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    assert quick_session._feature_exists("pist", repos) is False
    feat = wtm.TARGETS_CACHE / "pist-A-api" / "tests" / "acceptance"
    feat.mkdir(parents=True)
    (feat / "pist.feature").write_text("Feature: x\n", encoding="utf-8")
    assert quick_session._feature_repo("pist", repos) == "api"
    assert quick_session._feature_exists("pist", repos) is True


# --------------------------------------------------------------------------
# constitution, verify, aliasy
# --------------------------------------------------------------------------


def test_constitution_dev_only_synthetic_data_is_not_a_conflict(tmp_path: Path) -> None:
    (tmp_path / ".pflanzer").mkdir()
    c = tmp_path / ".pflanzer" / "CONSTITUTION.md"
    c.write_text("# Constitution\n- Ve vývoji jen syntetická data (L1), žádné osobní údaje.\n",
                 encoding="utf-8")
    brief = "Rezervační formulář: jméno, telefon, e-mail"
    assert quick_session.constitution_conflicts(brief, cwd=tmp_path) == []
    c.write_text("# Constitution\n- Aplikace nesmí sbírat osobní údaje uživatelů.\n",
                 encoding="utf-8")
    assert quick_session.constitution_conflicts(brief, cwd=tmp_path)
    c.write_text("- Ve vývoji jen syntetická data; v produkci nesbíráme osobní údaje.\n",
                 encoding="utf-8")
    assert quick_session.constitution_conflicts(brief, cwd=tmp_path)


def test_verify_next_step_follows_project_state(project: dict[str, Any]) -> None:
    from tests.conftest import set_status
    from tool.cli import worktree as wtm
    set_status(project["slug"], "handoff")
    nxt = wtm._verify_next_step(project["slug"])
    assert nxt and "pokračuj Buildem" not in nxt


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(REPO_ROOT / "tool" / "bin" / "pflanzer"), *args],
                          capture_output=True, text=True, timeout=60)


def test_aliases_ship_decide_build_and_did_you_mean() -> None:
    ship = _cli("ship", "--help")
    assert ship.returncode == 0 and "usage" in ship.stdout.lower()
    dec = _cli("decide", "--help")
    assert dec.returncode == 0 and "--winner" in dec.stdout
    build = _cli("build")
    assert build.returncode == 0 and "worktree setup" in build.stdout
    typo = _cli("shpi")
    assert typo.returncode == 2 and "ship" in typo.stderr
    helptext = _cli("help", "--all").stdout
    assert helptext.index("pflanzer ship") < helptext.index("pflanzer session_2")
