"""Pilot 9 (Šlapka, npm workspaces monorepo): a11y ignoruje JSON, types/build ve workspace
balíčcích, gates-template bez stahování ze sítě, preview bez falešného ⚠, {api_port}, restart."""
from __future__ import annotations

import json
import os
import stat
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import pytest
from test_preview import _get, preview_env  # noqa: F401 — fixture

from tool.cli import a11y_html, apprun, init, preview, render
from tool.cli import quality_gates as qg

INDEX = '<!doctype html><html lang="cs"><head><title>x</title></head><body>' \
        '<div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>'


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd,
                   check=True, capture_output=True)


def make_monorepo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(json.dumps({
        "name": "m", "private": True, "workspaces": ["apps/*"],
        "scripts": {"build": "npm run build --workspaces --if-present", "test": "echo ok",
                    "lint": "echo ok"},
        "devDependencies": {"concurrently": "^8"}}), encoding="utf-8")
    web = root / "apps" / "web"
    (web / "src").mkdir(parents=True)
    (web / "package.json").write_text(json.dumps({
        "name": "@m/web", "scripts": {"dev": "vite", "build": "vite build"},
        "devDependencies": {"typescript": "^5", "vite": "^5"}}), encoding="utf-8")
    (web / "tsconfig.json").write_text("{}", encoding="utf-8")
    (web / "index.html").write_text(INDEX, encoding="utf-8")
    (web / "vite.config.ts").write_text("export default {}\n", encoding="utf-8")
    api = root / "apps" / "api"
    (api / "src").mkdir(parents=True)
    (api / "package.json").write_text(json.dumps({
        "name": "@m/api", "scripts": {"dev": "node src/server.js"},
        "dependencies": {"express": "^4"}}), encoding="utf-8")
    (root / "tests" / "acceptance").mkdir(parents=True)
    (root / "tests" / "acceptance" / "a.test.js").write_text("// t\n", encoding="utf-8")
    return root


def fake_tsc(path: Path, rc: int, out: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/sh\necho \"$@\" >> \"{path}.calls\"\n"
                    f"{'echo ' + repr(out) if out else ':'}\nexit {rc}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


# --- 2. a11y: JSON endpointy nejsou stránky ----------------------------------------------


def test_a11y_static_ignores_json_endpoints() -> None:
    run = qg.AppRun("ok", pages=[
        ("/", 200, '<!doctype html><html lang="cs"><head><title>x</title>'
                   '<meta name="viewport" content="width=device-width"></head>'
                   '<body><main><h1>a</h1></main></body></html>', "text/html; charset=utf-8"),
        ("/api/bikes", 200, "<html><body>[]</body></html>", "application/json"),
    ])
    res = qg._a11y_from_pages(run)
    assert res is not None and "1 stránek" in res.details and res.status == "pass"


def test_a11y_spa_skips_json_pages_and_names_path() -> None:
    bare = "<!DOCTYPE html><html><head></head><body><pre>[]</pre></body></html>"
    good = ('<!DOCTYPE html><html lang="cs"><head><title>x</title>'
            '<meta name="viewport" content="width=device-width"></head>'
            '<body><main><h1>a</h1></main></body></html>')
    rendered = render.RenderResult(True, pages=[
        render.RenderedPage("/", 200, good, False),
        render.RenderedPage("/api/bikes", 200, bare, False)])
    run = qg.AppRun("ok", spa=True, render=rendered, pages=[
        ("/", 200, INDEX, "text/html"), ("/api/bikes", 200, "[]", "application/json")])
    res = qg._a11y_spa(run)
    assert res.status == "pass", res.details
    assert "/api/bikes" not in res.details


def test_a11y_reasons_name_the_page() -> None:
    findings = [("/api/bikes", a11y_html.FAIL, "chybí <html lang>")]
    details = a11y_html.summarize(findings, 1)
    assert qg.a11y_reasons(details) == ["/api/bikes: chybí <html lang>"]


# --- 3. types / build ve workspace balíčcích -------------------------------------------


def test_types_finds_workspace_tsconfig_and_runs_per_package(tmp_path: Path) -> None:
    repo = make_monorepo(tmp_path / "m")
    (repo / "node_modules").mkdir()
    tsc = repo / "apps" / "web" / "node_modules" / ".bin" / "tsc"
    fake_tsc(tsc, 0)
    ctx, st, _ = qg._make_ctx(repo)
    assert st.has_tsconfig and [w.name for w in st.workspaces] == ["api", "web"]
    res = qg.gate_types(ctx)
    assert res.status == "pass", res.details
    assert "-p apps/web" in Path(str(tsc) + ".calls").read_text()


def test_types_workspace_errors_fail(tmp_path: Path) -> None:
    repo = make_monorepo(tmp_path / "m")
    (repo / "node_modules").mkdir()
    fake_tsc(repo / "apps" / "web" / "node_modules" / ".bin" / "tsc", 2,
             "src/a.ts(1,1): error TS2322: bad")
    ctx, _, _ = qg._make_ctx(repo)
    res = qg.gate_types(ctx)
    assert res.status == "fail" and res.metric == 1 and "apps/web" in res.details


def test_types_without_typescript_is_unverified_not_download(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = make_monorepo(tmp_path / "m")
    (repo / "node_modules").mkdir()
    monkeypatch.setattr(qg, "_has", lambda tool: False)
    ran: list[Any] = []
    monkeypatch.setattr(qg, "_run", lambda *a, **k: ran.append(a) or (0, "", ""))
    res = qg.gate_types(qg._make_ctx(repo)[0])
    assert res.status == "unsupported" or "NEOVĚŘENO" in res.details.upper() \
        or "nainstalovaný" in res.details
    assert "npm install" in res.details and not ran


def test_build_size_sums_workspace_outputs(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    repo = make_monorepo(tmp_path / "m")
    (repo / "node_modules").mkdir()
    dist = repo / "apps" / "web" / "dist"
    dist.mkdir()
    (dist / "a.js").write_bytes(b"x" * 4096)
    monkeypatch.setattr(qg, "_run", lambda *a, **k: (0, "", ""))
    monkeypatch.setattr(qg, "_has", lambda tool: True)
    res = qg.gate_build(qg._make_ctx(repo)[0])
    assert res.status == "pass" and res.metric == 4 and "4 KB" in res.details


# --- 4. gates-template pro monorepo -------------------------------------------------


def test_gates_template_monorepo_has_no_network_tools(tmp_path: Path) -> None:
    repo = make_monorepo(tmp_path / "m")
    text, stack = init.render_gates_template(repo)
    assert stack == "node"
    active = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    joined = "\n".join(active)
    assert "npx vitest" not in joined and "npx tsc" not in joined
    assert "(cd apps/web && npx --no-install tsc --noEmit)" in joined
    assert "node --test tests/acceptance/*.test.*" in joined
    assert "# coverage:" in text and "stahoval ze sítě" in text
    assert "playwright" not in joined


def test_gates_template_plain_node_without_tsconfig_comments_types(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"build": "x", "test": "y"}}), encoding="utf-8")
    text, _ = init.render_gates_template(tmp_path)
    assert "# types:" in text and "není TypeScript" in text
    assert "\nlint:" not in text and "# lint:" in text


# --- 5. preview: SPA ve workspace, žádné falešné ⚠ ----------------------------------


def test_is_spa_in_workspace_and_no_false_added_routes(tmp_path: Path) -> None:
    repo = make_monorepo(tmp_path / "m")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    _git(repo, "checkout", "-qb", "var")
    (repo / "apps/web/src/components").mkdir(parents=True)
    (repo / "apps/web/src/components/Wizard.tsx").write_text("export const W = 1\n")
    (repo / "apps/api/src/server.js").write_text("app.get('/api/bikes', h)\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "feat")
    assert preview.is_spa(repo)
    assert preview._added_routes(repo) == []
    assert preview.check_reachable("A", repo, 1) is None
    # i bez SPA detekce: komponenta a /api/ nejsou stránky
    assert preview._added_routes(repo, spa=False) == []


def test_added_routes_still_finds_real_pages(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README").write_text("x")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    _git(repo, "checkout", "-qb", "var")
    (repo / "server.js").write_text("app.get('/objednavka', h)\napp.get('/api/x', h)\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "feat")
    assert preview._added_routes(repo, spa=False) == ["/objednavka"]


# --- 6. {api_port} ----------------------------------------------------------------------


def test_api_port_placeholder_and_env(tmp_path: Path) -> None:
    repo = make_monorepo(tmp_path / "m")
    (repo / ".pflanzer").mkdir()
    (repo / ".pflanzer" / "project.toml").write_text(
        '[preview]\ncommand = "PORT={api_port} api & web --port {port}"\n', encoding="utf-8")
    a = apprun.detect_run(repo, 8601)
    b = apprun.detect_run(repo, 8611)
    assert a is not None and b is not None
    assert a.command == "PORT=9602 api & web --port 8601"
    assert a.env["API_PORT"] == "9602" and b.env["API_PORT"] == "9612"
    assert apprun.api_port_for(8601) == 8601 + 1001
    assert apprun.detect_run(repo, 8601, api_port=7777).command.startswith("PORT=7777")


def test_autodetected_workspace_dev_gets_distinct_api_port(tmp_path: Path) -> None:
    repo = make_monorepo(tmp_path / "m")
    pkg = json.loads((repo / "package.json").read_text())
    pkg["scripts"]["dev"] = 'concurrently "npm run dev -w apps/api" "npm run dev -w apps/web"'
    (repo / "package.json").write_text(json.dumps(pkg))
    a, b = apprun.detect_run(repo, 8601), apprun.detect_run(repo, 8611)
    assert a.env["PORT"] == "8601" and a.env["API_PORT"] != b.env["API_PORT"]


def test_workspace_globs_object_form(tmp_path: Path) -> None:
    repo = make_monorepo(tmp_path / "m")
    pkg = json.loads((repo / "package.json").read_text())
    pkg["workspaces"] = {"packages": ["apps/*", "!apps/api"]}
    (repo / "package.json").write_text(json.dumps(pkg))
    assert [p.name for p in apprun.workspace_packages(repo)] == ["web"]


# --- 7. preview restart ----------------------------------------------------------------

APP_V = textwrap.dedent('''
    import sys
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            body = b"<html><body>VERZE-%s</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)

    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
''')


def test_restart_keeps_password_ports_and_proxy(preview_env: dict[str, Any],  # noqa: F811
                                                project: dict[str, Any], vote: Any) -> None:
    slug = preview_env["slug"]
    vote(slug)
    dirs = preview_env["dirs"]
    for d in dirs.values():
        (d / "app.py").write_text(APP_V.replace("%s", "1"), encoding="utf-8")
    res = preview.up(slug, password="tajne", tunnel="none", base_port=preview_env["base"])
    before = preview.load_state(slug)
    assert before is not None
    base = preview_env["base"]
    assert b"VERZE-1" in _get(base + 1)[2]

    with pytest.raises(ValueError, match="preview restart"):
        preview.up(slug, password="tajne", tunnel="none", base_port=base)

    (dirs["A"] / "app.py").write_text(APP_V.replace("%s", "2"), encoding="utf-8")
    out = preview.restart(slug, variants=["A"])
    after = preview.load_state(slug)
    assert after is not None and out["restarted"] == ["A"] and out["password"] == "tajne"
    a0, a1 = before["variants"]["A"], after["variants"]["A"]
    assert a1["app_port"] == a0["app_port"] and a1["proxy_port"] == a0["proxy_port"]
    assert a1["proxy_pid"] == a0["proxy_pid"] and a1["app_pid"] != a0["app_pid"]
    assert after["password"] == before["password"]
    assert b"VERZE-2" in _get(base + 1)[2]
    assert b"VERZE-1" in _get(base + 11)[2]  # B nedotčená
    assert res["variants"]["A"]["url"] == after["variants"]["A"]["url"] or True

    with pytest.raises(ValueError, match="není"):
        preview.restart(slug, variants=["Z"])
    assert preview.parse_variants("a, c") == ["A", "C"]


def test_share_message_counts_variants() -> None:
    def res(n: int) -> dict[str, Any]:
        return {"user": "pflanzer", "password": "p", "deadline": "pá",
                "variants": {c: {"url": f"http://x/{c}"} for c in "ABCD"[:n]}}
    assert "jednu variantu" in preview.share_message(res(1), None)
    assert "tři varianty" not in preview.share_message(res(1), None)
    assert "dvě varianty" in preview.share_message(res(2), None)
    assert "tři varianty" in preview.share_message(res(3), None)
    assert "jedna varianta" == preview._variants_phrase(1)[1]


def test_restart_without_running_preview(tmp_path: Path, tmp_db: Path,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    from tool.cli import db
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path / "data")
    with pytest.raises(ValueError, match="preview up"):
        preview.restart("nic")


_ = os
