"""Pilot 14 (Lázně Sůl, web Vite+React + api FastAPI): prohlížeč varianty dosáhne na API své
varianty přes proxy s heslem (`/__pflanzer/<role>`), retro měří per repo, Go->merge ve stejném
pásmu, kosmetika (readiness tabulka, fáze ve feedbacku, doctor, kontroly API repa, reviewer)."""
from __future__ import annotations

import base64
import http.client
import http.server
import json
import os
import subprocess
import threading
import time
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from conftest import git
from test_pilot8_b import _duo

from tool.cli import (
    _compat,
    charter,
    doctor,
    feedback_pull,
    handoff_pr,
    preview,
    quick_session,
    retro,
    session_3,
)
from tool.cli.db import transaction

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def tz(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str], None]]:
    """Přepne časové pásmo procesu (a vrátí ho)."""
    def _set(name: str) -> None:
        monkeypatch.setenv("TZ", name)
        time.tzset()
    yield _set
    monkeypatch.undo()
    time.tzset()


# --- 1. proxy směruje /__pflanzer/<role>/ na sekundární repo --------------------------------

def _server(handler: type) -> http.server.HTTPServer:
    srv = http.server.HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _req(port: int, method: str, path: str, *, auth: bool = True, body: bytes | None = None,
         headers: dict[str, str] | None = None) -> tuple[int, bytes, http.client.HTTPResponse]:
    hdrs = dict(headers or {})
    if auth:
        hdrs["Authorization"] = "Basic " + base64.b64encode(b"pflanzer:pw").decode()
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request(method, path, body=body, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, data, resp


@pytest.fixture
def stack() -> Iterator[dict[str, Any]]:
    seen: list[dict[str, Any]] = []

    class Web(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a: Any) -> None:
            pass

        def do_GET(self) -> None:  # noqa: N802
            body = f"web:{self.path}".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    class Api(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a: Any) -> None:
            pass

        def _answer(self) -> None:
            n = int(self.headers.get("Content-Length") or 0)
            seen.append({"method": self.command, "path": self.path,
                         "body": self.rfile.read(n) if n else b"",
                         "x": self.headers.get("X-Test"), "host": self.headers.get("Host"),
                         "auth": self.headers.get("Authorization")})
            if self.path.startswith("/redir"):
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{api.server_port}/slots")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            body = json.dumps({"api": self.command, "path": self.path}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = do_POST = do_PUT = do_DELETE = _answer  # noqa: N815

    web, api = _server(Web), _server(Api)
    proxy = preview._Server(("127.0.0.1", 0), preview._make_handler(
        web.server_port, "pw", "A", {"api": api.server_port}))
    threading.Thread(target=proxy.serve_forever, daemon=True).start()
    yield {"proxy": proxy.server_port, "api": api.server_port, "web": web.server_port,
           "seen": seen}
    for s in (web, api, proxy):
        s.shutdown()
        s.server_close()


def test_proxy_routes_browser_calls_to_secondary_repo(stack: dict[str, Any]) -> None:
    status, data, _ = _req(stack["proxy"], "GET", "/__pflanzer/api/x?a=1")
    assert status == 200
    assert json.loads(data) == {"api": "GET", "path": "/x?a=1"}  # prefix odříznut, query zůstala
    # primární aplikace pořád jde bez prefixu
    status, data, _ = _req(stack["proxy"], "GET", "/index")
    assert (status, data) == (200, b"web:/index")


def test_proxy_forwards_method_body_headers_and_hides_password(stack: dict[str, Any]) -> None:
    status, _data, _ = _req(stack["proxy"], "POST", "/__pflanzer/api/slots", body=b'{"d": 1}',
                            headers={"X-Test": "ano", "Content-Type": "application/json"})
    assert status == 200
    got = stack["seen"][-1]
    assert (got["method"], got["path"], got["body"], got["x"]) == (
        "POST", "/slots", b'{"d": 1}', "ano")
    assert got["host"] == f"127.0.0.1:{stack['api']}"
    assert got["auth"] is None  # heslo preview se do API nepředává
    assert _req(stack["proxy"], "DELETE", "/__pflanzer/api/slots/3")[0] == 200
    assert stack["seen"][-1]["method"] == "DELETE"


def test_proxy_route_requires_password(stack: dict[str, Any]) -> None:
    seen_before = len(stack["seen"])
    status, _d, resp = _req(stack["proxy"], "GET", "/__pflanzer/api/x", auth=False)
    assert status == 401 and "Basic" in (resp.getheader("WWW-Authenticate") or "")
    assert len(stack["seen"]) == seen_before  # API bez hesla nedostalo nic
    bad = {"Authorization": "Basic " + base64.b64encode(b"pflanzer:spatne").decode()}
    assert _req(stack["proxy"], "GET", "/__pflanzer/api/x", auth=False, headers=bad)[0] == 401


def test_proxy_unknown_role_and_redirect(stack: dict[str, Any]) -> None:
    assert _req(stack["proxy"], "GET", "/__pflanzer/nic/x")[0] == 404
    assert _req(stack["proxy"], "GET", "/__pflanzer/api")[1]  # bez lomítka -> `/`
    assert stack["seen"][-1]["path"] == "/"
    status, _d, resp = _req(stack["proxy"], "GET", "/__pflanzer/api/redir")
    assert status == 302
    assert resp.getheader("Location") == "/__pflanzer/api/slots"  # redirect zůstane za proxy


def test_split_route() -> None:
    routes = {"api": 1, "web-2": 2}
    assert preview.split_route("/a/b", routes) == (None, "/a/b")
    assert preview.split_route("/__pflanzer/api/x/y?z=1", routes) == ("api", "/x/y?z=1")
    assert preview.split_route("/__pflanzer/api?z=1", routes) == ("api", "/?z=1")
    assert preview.split_route("/__pflanzer/web-2/", routes) == ("web-2", "/")
    assert preview.split_route("/__pflanzer/nope/x", routes) == (None, None)


def test_browser_env_is_relative_for_every_framework() -> None:
    env = preview.browser_env(["api", "pdf-svc"])
    assert env["VITE_API_URL"] == "/__pflanzer/api"
    assert env["NEXT_PUBLIC_API_URL"] == "/__pflanzer/api"
    assert env["REACT_APP_API_URL"] == "/__pflanzer/api"
    assert env["VITE_PDF_SVC_URL"] == "/__pflanzer/pdf-svc"
    assert not any("127.0.0.1" in v for v in env.values())  # žádný port, žádný localhost


def test_up_passes_server_and_browser_env_and_routes(
        tmp_db: Path, tmp_path: Path, tmp_targets: Path, vote: Callable[..., Any],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """`preview up` dá primárnímu repu <ROLE>_URL (server) i VITE_/NEXT_PUBLIC_/REACT_APP_ a
    proxy dostane route na sekundární repo."""
    _duo(tmp_path, tmp_targets, vote)
    started: list[Any] = []
    spawned: list[tuple[Any, ...]] = []

    class FakeProc:
        pid = 0

    def fake_start(spec: Any, log: Path) -> FakeProc:
        started.append(spec)
        return FakeProc()

    def fake_spawn(*a: Any, **k: Any) -> FakeProc:
        spawned.append(a)
        return FakeProc()

    monkeypatch.setattr(
        preview.apprun, "detect_run",
        lambda path, port, **k: preview.apprun.RunSpec(
            command=f"app {port}", argv=["app", str(port)], cwd=path, source="test"))
    monkeypatch.setattr(preview.apprun, "start_app", fake_start)
    monkeypatch.setattr(preview, "_spawn_proxy", fake_spawn)
    monkeypatch.setattr(preview.apprun, "wait_http", lambda *a, **k: (True, 200))
    monkeypatch.setattr(preview, "check_reachable", lambda *a, **k: None)
    monkeypatch.setattr(preview.apprun, "proc_started", lambda pid: "x")
    monkeypatch.setattr(preview.apprun, "port_free", lambda *a, **k: True)
    monkeypatch.setattr(preview, "_primary_dirs",
                        lambda slug: {"A": tmp_targets / "duo-A"})
    monkeypatch.setattr(preview, "in_play", lambda slug: ["A"])
    monkeypatch.setattr(preview, "is_spa", lambda p: True)
    preview.up("duo", password="pw", tunnel="none", variants=["A"], timeout=1)
    primary_env = next(s.env for s in started if "VITE_API_URL" in s.env)
    assert primary_env["API_URL"].startswith("http://127.0.0.1:")  # server: absolutní
    assert primary_env["VITE_API_URL"] == "/__pflanzer/api"
    assert primary_env["NEXT_PUBLIC_API_URL"] == "/__pflanzer/api"
    assert primary_env["REACT_APP_API_URL"] == "/__pflanzer/api"
    port = primary_env["API_URL"].rsplit(":", 1)[1]
    assert spawned and spawned[0][-1] == {"api": int(port)}  # routes pro proxy
    api_env = next(s.env for s in started if "VITE_API_URL" not in s.env)
    assert not any(k.startswith(("VITE_", "NEXT_PUBLIC_")) for k in api_env)


# --- 2. retro měří per repo --------------------------------------------------------------------

def _merge_commit(wt: Path, branch: str) -> str:
    """Merge commit (rodiče base + větev) bez checkoutu: strom větve = nic se nepřepsalo."""
    base = git(wt, "rev-parse", f"{branch}~1")
    return git(wt, "commit-tree", f"{branch}^{{tree}}", "-p", base, "-p", branch,
               "-m", "Merge winner")


def _go(project_id: int, days_ago: int = 3) -> None:
    go = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(timespec="seconds")
    with transaction() as conn:
        conn.execute("INSERT INTO sessions (project_id, type, decision, decision_ts) "
                     "VALUES (?, 2, 'go', ?)", (project_id, go))


def test_retro_measure_reports_every_repo_and_total(
        tmp_db: Path, tmp_path: Path, tmp_targets: Path, vote: Callable[..., Any]) -> None:
    duo = _duo(tmp_path, tmp_targets, vote)
    _go(duo["project_id"])
    web_sha = _merge_commit(duo["wt_web"], "pflanzer/duo-A")
    api_sha = _merge_commit(duo["wt_api"], "pflanzer/duo-A")
    out = retro.measure(slug="duo", merge_commit=web_sha, winner="A", fetch=False,
                        repo_merges=[f"api={api_sha}"])
    assert out["measured_repos"] == ["web", "api"] and out["unmeasured_repos"] == []
    per = {r["role"]: r for r in out["per_repo"]}
    assert per["web"]["loc_winner"] == 1 and per["api"]["loc_winner"] == 2
    assert out["loc_winner"] == 3 == sum(r["loc_winner"] for r in per.values())
    assert out["loc_reused_pct"] == 100.0
    with transaction() as conn:
        rows = dict(conn.execute(
            "SELECT metric, value FROM outcomes WHERE milestone='ship'").fetchall())
        notes = conn.execute("SELECT notes FROM outcomes WHERE metric='loc_winner'").fetchone()[0]
    assert rows["loc_winner@api"] == 2 and rows["loc_winner@web"] == 1
    assert rows["loc_winner"] == 3
    assert "měřeno: web, api" in notes
    # znovu: přepíše, nezdvojí
    retro.measure(slug="duo", merge_commit=web_sha, winner="A", fetch=False,
                  repo_merges=[f"api={api_sha}"])
    with transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM outcomes WHERE metric='loc_winner@api'"
                            ).fetchone()[0] == 1


def test_retro_measure_says_when_only_primary_repo_is_measured(
        tmp_db: Path, tmp_path: Path, tmp_targets: Path, vote: Callable[..., Any]) -> None:
    duo = _duo(tmp_path, tmp_targets, vote)
    _go(duo["project_id"])
    web_sha = _merge_commit(duo["wt_web"], "pflanzer/duo-A")
    out = retro.measure(slug="duo", merge_commit=web_sha, winner="A", fetch=False)
    assert out["measured_repos"] == ["web"]
    assert [u["role"] for u in out["unmeasured_repos"]] == ["api"]
    assert "--repo-pr api=" in out["unmeasured_repos"][0]["reason"]
    with transaction() as conn:
        notes = conn.execute("SELECT notes FROM outcomes WHERE metric='loc_reused_pct'"
                             ).fetchone()[0]
        assert conn.execute("SELECT COUNT(*) FROM outcomes WHERE metric LIKE '%@api'"
                            ).fetchone()[0] == 0
    assert "měřeno: web; neměřeno: api" in notes
    with pytest.raises(ValueError, match="není"):
        retro.measure(slug="duo", merge_commit=web_sha, winner="A", fetch=False,
                      repo_prs=["db=https://x/pr/1"])


# --- 3. Go -> merge přes místní datum ---------------------------------------------------------

@pytest.mark.parametrize("zone,expected", [("UTC", "2026-10-19"), ("Europe/Prague", "2026-10-20")])
def test_local_date_follows_timezone(tz: Callable[[str], None], zone: str, expected: str) -> None:
    tz(zone)
    # SQLite CURRENT_TIMESTAMP (naivní = UTC) 23:30 UTC
    assert _compat.local_date("2026-10-19 23:30:00").isoformat() == expected
    assert _compat.local_date("2026-10-19T23:30:00Z").isoformat() == expected
    assert _compat.local_date("") is None


def test_days_to_prod_uses_one_timezone(
        tz: Callable[[str], None], tmp_db: Path, tmp_path: Path, tmp_targets: Path,
        vote: Callable[..., Any]) -> None:
    """Go 19.10. 23:30 UTC (= 20.10. 01:30 v Praze), merge 20.10. 10:00 +02:00: v Praze 0 dní
    (dřív UTC datum Go vs lokální datum merge -> 1)."""
    tz("Europe/Prague")
    duo = _duo(tmp_path, tmp_targets, vote)
    with transaction() as conn:
        conn.execute("INSERT INTO sessions (project_id, type, decision, decision_ts) "
                     "VALUES (?, 2, 'go', '2026-10-19T23:30:00+00:00')", (duo["project_id"],))
    env = {"GIT_COMMITTER_DATE": "2026-10-20T10:00:00+02:00"}
    # merge commit s pevným časem
    base = git(duo["wt_web"], "rev-parse", "pflanzer/duo-A~1")
    res = subprocess.run(
        ["git", "commit-tree", "pflanzer/duo-A^{tree}", "-p", base, "-p", "pflanzer/duo-A",
         "-m", "Merge"], cwd=duo["wt_web"], capture_output=True, text=True,
        env={**os.environ, **env}, check=True)
    sha = res.stdout.strip()
    out = retro.measure(slug="duo", merge_commit=sha, winner="A", fetch=False)
    assert out["days_to_prod"] == 0


def test_pr_body_decision_date_is_local(tz: Callable[[str], None]) -> None:
    tz("Europe/Prague")
    assert _compat.local_date("2026-10-19 23:30:00").isoformat() == "2026-10-20"
    src = (REPO / "tool" / "cli" / "handoff_pr.py").read_text(encoding="utf-8")
    assert "local_date(ctx[\"decision\"][2])" in src and handoff_pr.local_date is _compat.local_date


# --- kosmetika ---------------------------------------------------------------------------------

def test_readiness_table_shows_total_and_per_repo(
        tmp_db: Path, tmp_path: Path, tmp_targets: Path, vote: Callable[..., Any]) -> None:
    _duo(tmp_path, tmp_targets, vote)
    session_3.hardening_run(slug="duo")
    md = (session_3.REPORTS_DIR / "duo-readiness.md").read_text(encoding="utf-8")
    assert "celkem (web " in md and ", api " in md
    assert "Spuštěné brány" in md


def test_feedback_summary_shows_phase_in_words(project: dict[str, Any],
                                               vote: Callable[..., Any]) -> None:
    vote(project["slug"], status="session_1")
    md = feedback_pull.render_summary_md(feedback_pull.aggregate(project["slug"]))
    assert "session_1" not in md
    assert "Stav projektu: Build zapsaný" in md


def test_doctor_next_step_mentions_multi_repo_init_and_primary_start(tmp_path: Path) -> None:
    title, _lines, nxt, _w, _t = doctor._human(tmp_path, [
        {"check": "x", "status": doctor.OK, "detail": "", "advice": "", "impact": ""}])
    assert "každém repu" in nxt and "primárního" in nxt and "/pm start" in nxt
    faq = (REPO / "docs" / "faq.md").read_text(encoding="utf-8")
    assert "`pflanzer init` patří do **každého** repa" in faq
    assert "z **primárního** (web) repa" in faq


def test_doctor_lockfile_advice_for_python_is_concrete(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    row = doctor.check_package_manager(tmp_path)
    assert row["status"] == doctor.WARN
    assert "pip freeze > requirements.txt" in row["advice"] and "uv lock" in row["advice"]
    assert ".venv" in row["advice"]


def test_api_repo_checks_include_lint(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("fastapi\nruff\npytest\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text(
        "test: .venv\n\tpytest\n\nlint: .venv\n\truff check .\n\nrun:\n\tuvicorn app:app\n",
        encoding="utf-8")
    prof = quick_session.stack_profile(tmp_path)
    assert prof.commands == ["make test", "make lint"]
    # pyproject + ruff bez make lint
    py = tmp_path / "py"
    py.mkdir()
    (py / "pyproject.toml").write_text(
        "[project]\nname='x'\ndependencies=['fastapi']\n[tool.ruff]\nline-length=100\n",
        encoding="utf-8")
    (py / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
    assert quick_session.stack_profile(py).commands == ["make test", "ruff check ."]


def test_multi_repo_prompt_names_browser_and_server_variable(
        tmp_db: Path, tmp_path: Path, tmp_targets: Path, vote: Callable[..., Any]) -> None:
    _duo(tmp_path, tmp_targets, vote)
    from tool.cli.worktree import load_target_repos
    text = quick_session._multi_repo_rules("duo", "A", load_target_repos("duo"))
    for needle in ("VITE_API_URL", "NEXT_PUBLIC_API_URL", "REACT_APP_API_URL", "`API_URL`",
                   "/__pflanzer/api", "nehardcoduj"):
        assert needle in text, needle
    dev = (REPO / "docs" / "dev.md").read_text(encoding="utf-8")
    faq = (REPO / "docs" / "faq.md").read_text(encoding="utf-8")
    for doc in (dev, faq):
        assert "VITE_API_URL" in doc and "/__pflanzer/api" in doc


def _set_people(slug: str, core: list[str], owners: dict[str, str]) -> None:
    with transaction() as conn:
        conn.execute("UPDATE projects SET core_json = ?, path_owners_json = ? WHERE slug = ?",
                     (json.dumps(core, ensure_ascii=False),
                      json.dumps(owners, ensure_ascii=False), slug))


def test_reviewer_hint_only_names_people_outside_core(project: dict[str, Any]) -> None:
    slug = project["slug"]
    owners = {"vyvoj": "Jakub Král", "design": "Marie Nováková", "bezpecnost": "Hana Veselá",
              "provoz": "AI:devops-platform-expert", "byznys": "Eva Dvořáková"}
    _set_people(slug, ["Jakub Král (Vývoj)", "Marie Nováková (Design)"], owners)
    hint = charter.reviewer_hint(slug)
    assert "Hana Veselá" in hint and "Eva Dvořáková" in hint
    assert "Marie" not in hint and "Jakub" not in hint and "AI" not in hint
    _set_people(slug, ["Jakub Král", "Marie Nováková", "Hana Veselá", "Eva Dvořáková"], owners)
    assert charter.reviewer_hint(slug) == (
        "PR musí zkontrolovat někdo mimo jádro (kdo u Buildu nebyl).")


def test_ship_next_step_says_it_prints_pr_commands(project: dict[str, Any]) -> None:
    winner = {"gates": {"gate_score": 90}}
    txt = session_3._next_step(winner, True, 80, project["slug"], provoz_done=True)
    assert "vypíše příkazy k otevření PR (SHIP.md)" in txt
    assert "otevře PR" not in txt and ".." not in txt
    assert "mimo jádro" in txt
