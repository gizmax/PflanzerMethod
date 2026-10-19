"""Pilot 7 (Ledovka, React+Vite+TS SPA): počet testů vitestu, acceptance s vitestem,
detekce SPA a ehrlich smoke / a11y nad SPA (render přes Playwright, jinak NEOVĚŘENO)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from tool.cli import quality_gates as qg
from tool.cli import render

SIM_PW = Path("/private/tmp/claude-501/-Users-tom-AI-projekty-PflanzerMethod/"
              "84c43169-edba-4d42-8c1d-abce3e2877a7/scratchpad/sim4")

VITEST_OUT = """
 Test Files  2 passed (2)
      Tests  8 passed (8)
   Duration  1.2s
"""


def test_count_tests_vitest_prefers_tests_line():
    assert qg._count_tests(VITEST_OUT) == 8
    assert qg._count_tests(" Test Files  1 failed | 1 passed (2)\n"
                           "      Tests  2 failed | 6 passed (8)\n") == 6


def test_count_tests_jest():
    assert qg._count_tests("Test Suites: 1 passed, 1 total\nTests:       8 passed, 8 total\n") == 8


def _node_project(root: Path, deps: dict, tests: dict[str, str]) -> qg.Ctx:
    root.mkdir(parents=True)
    (root / "package.json").write_text(json.dumps({"devDependencies": deps}), encoding="utf-8")
    (root / "node_modules").mkdir()
    acc = root / "tests" / "acceptance"
    acc.mkdir(parents=True)
    for name, body in tests.items():
        (acc / name).write_text(body, encoding="utf-8")
    return qg.Ctx(root, qg.detect_stack_info(root), True, "")


def test_acceptance_vitest_tsx(tmp_path, monkeypatch):
    ctx = _node_project(tmp_path / "p", {"vitest": "^1"}, {"a.test.tsx": "x"})
    calls = []

    def fake_run(cmd, cwd, timeout=120):
        calls.append(cmd)
        return 0, VITEST_OUT, ""

    monkeypatch.setattr(qg, "_run", fake_run)
    res = qg.gate_acceptance(ctx)
    assert calls[0][:4] == ["npx", "--no-install", "vitest", "run"]
    assert calls[0][-1] == "tests/acceptance"
    assert res.status == "pass" and res.details.startswith("8/8")


def test_acceptance_vitest_failure(tmp_path, monkeypatch):
    ctx = _node_project(tmp_path / "p", {"vitest": "^1"}, {"a.test.ts": "x"})
    monkeypatch.setattr(qg, "_run", lambda *a, **k: (
        1, " Test Files  1 failed (1)\n      Tests  6 failed | 2 passed (8)\n", ""))
    res = qg.gate_acceptance(ctx)
    assert res.status == "fail" and res.details.startswith("2/8")


def test_acceptance_jest(tmp_path, monkeypatch):
    ctx = _node_project(tmp_path / "p", {"jest": "^29"}, {"a.test.tsx": "x"})
    calls = []
    monkeypatch.setattr(qg, "_run", lambda cmd, *a, **k: (
        calls.append(cmd) or (0, "Tests:       4 passed, 4 total\n", "")))
    res = qg.gate_acceptance(ctx)
    assert calls[0][2] == "jest" and res.status == "pass"


def test_acceptance_ts_without_runner_is_unverified(tmp_path):
    ctx = _node_project(tmp_path / "p", {"typescript": "^5"}, {"a.test.tsx": "x"})
    res = qg.gate_acceptance(ctx)
    assert res.status == "skipped" and res.details.startswith(qg.UNVERIFIED_PREFIX)


def test_acceptance_node_test_js_still_works(tmp_path, monkeypatch):
    ctx = _node_project(tmp_path / "p", {}, {"a.test.js": "x"})
    ctx.stack.deps = {}
    seen = []
    monkeypatch.setattr(qg, "_run", lambda cmd, *a, **k: (
        seen.append(cmd) or (0, "# pass 3\n# fail 0\n", "")))
    res = qg.gate_acceptance(ctx)
    assert seen[0][1] == "--test" and res.status == "pass"


# ---------------------------------------------------------------- SPA


SKELETON = ('<!doctype html><html lang="cs"><head><meta charset="utf-8"><title>Ledovka</title>'
            '<meta name="viewport" content="width=device-width"></head><body>'
            '<div id="root"></div><script type="module" src="/src/main.js"></script>'
            '</body></html>')
RENDER_JS = ("document.getElementById('root').innerHTML = '<main><h1>Ledovka</h1>"
             "<img src=\"x.png\"><button>Objednat</button></main>';")
BROKEN_JS = "throw new Error('boom');"

APP = '''
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

SKELETON = """__SKELETON__"""
JS = """__JS__"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/src/main.js":
            body, ctype = JS.encode(), "text/javascript"
        elif self.path == "/":
            body, ctype = SKELETON.encode(), "text/html; charset=utf-8"
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)


HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''


def _spa_app(root: Path, js: str = RENDER_JS) -> Path:
    root.mkdir(parents=True)
    (root / "app.py").write_text(
        APP.replace("__SKELETON__", SKELETON).replace("__JS__", js), encoding="utf-8")
    (root / ".pflanzer").mkdir()
    cmd = f"{sys.executable} app.py {{port}}"
    (root / ".pflanzer" / "project.toml").write_text(
        f"[preview]\ncommand = {json.dumps(cmd)}\n", encoding="utf-8")
    return root


def _gate(path: Path, name: str) -> qg.GateResult:
    return qg.GATE_RUNNERS[name](qg._make_ctx(path)[0])


def test_is_spa():
    assert render.is_spa(SKELETON)
    assert render.is_spa('<div id="app">\n</div><script src="/b.js"></script>')
    assert not render.is_spa('<div id="root"><h1>SSR</h1></div><script src="/b.js"></script>')
    assert not render.is_spa('<div id="root"></div>')  # bez skriptu to není SPA
    assert not render.is_spa("<html><body><h1>Statika</h1></body></html>")


def test_spa_without_playwright(tmp_path, monkeypatch):
    monkeypatch.delenv("PFLANZER_PLAYWRIGHT_DIR", raising=False)
    root = _spa_app(tmp_path / "spa")
    ctx = qg._make_ctx(root)[0]
    smoke = qg.GATE_RUNNERS["smoke"](ctx)
    a11y = qg.GATE_RUNNERS["a11y"](ctx)
    assert smoke.status == "pass"
    assert "render neověřen" in smoke.details and "bundle" in smoke.details
    assert a11y.status == "skipped"
    assert a11y.details.startswith(qg.UNVERIFIED_PREFIX) and "SPA" in a11y.details
    assert "playwright install chromium" in a11y.details
    line = qg.spa_line([smoke, a11y])
    assert "render neověřen" in line and "NEOVĚŘENO" in line


def test_spa_missing_bundle_fails_smoke(tmp_path, monkeypatch):
    monkeypatch.delenv("PFLANZER_PLAYWRIGHT_DIR", raising=False)
    root = _spa_app(tmp_path / "spa")
    app = (root / "app.py").read_text(encoding="utf-8")
    app = app.replace('src="/src/main.js"', 'src="/jina.js"')
    (root / "app.py").write_text(app, encoding="utf-8")
    smoke = _gate(root, "smoke")
    assert smoke.status == "fail" and "bundle" in smoke.details


def test_non_spa_unchanged(tmp_path):
    root = _spa_app(tmp_path / "ssr")
    app = (root / "app.py").read_text(encoding="utf-8").replace(
        '<div id="root"></div>', '<div id="root"><h1>Ahoj</h1></div>')
    (root / "app.py").write_text(app, encoding="utf-8")
    smoke = _gate(root, "smoke")
    assert smoke.status == "pass" and "SPA" not in smoke.details
    assert qg.spa_line([smoke]) == ""


needs_pw = pytest.mark.skipif(not (SIM_PW / "node_modules" / "playwright").is_dir(),
                              reason="Playwright (sim4) není k dispozici")


def _browser_ok(monkeypatch) -> bool:
    monkeypatch.setenv("PFLANZER_PLAYWRIGHT_DIR", str(SIM_PW))
    import pwd  # testy běží s izolovaným HOME; prohlížeče jsou v cache skutečného uživatele
    cache = Path(pwd.getpwuid(os.getuid()).pw_dir) / "Library" / "Caches" / "ms-playwright"
    if cache.is_dir() and "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
        monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(cache))
    return True


@needs_pw
def test_spa_render_with_playwright(tmp_path, monkeypatch):
    _browser_ok(monkeypatch)
    root = _spa_app(tmp_path / "spa")
    ctx = qg._make_ctx(root)[0]
    run = qg._app_run(ctx)
    if run.render is None and "prohlížeč" in run.render_why:
        pytest.skip(run.render_why)
    smoke = qg.GATE_RUNNERS["smoke"](ctx)
    a11y = qg.GATE_RUNNERS["a11y"](ctx)
    assert smoke.status == "pass" and "vyrenderována" in smoke.details
    # a11y běží nad vyrenderovaným DOM: <img> bez alt z JS je nález, ne prázdná kostra
    assert a11y.status in ("warn", "fail") and "alt" in a11y.details
    assert "ověřeno renderem" in qg.spa_line([smoke, a11y])


@needs_pw
def test_spa_render_uncaught_error_fails_smoke(tmp_path, monkeypatch):
    _browser_ok(monkeypatch)
    root = _spa_app(tmp_path / "spa", BROKEN_JS)
    ctx = qg._make_ctx(root)[0]
    run = qg._app_run(ctx)
    if run.render is None and "prohlížeč" in run.render_why:
        pytest.skip(run.render_why)
    smoke = qg.GATE_RUNNERS["smoke"](ctx)
    assert smoke.status == "fail" and "boom" in smoke.details


def test_find_playwright_env(tmp_path, monkeypatch):
    (tmp_path / "node_modules" / "playwright").mkdir(parents=True)
    monkeypatch.setenv("PFLANZER_PLAYWRIGHT_DIR", str(tmp_path))
    assert render.find_playwright(tmp_path / "jiny") == tmp_path
    monkeypatch.delenv("PFLANZER_PLAYWRIGHT_DIR")
    assert render.find_playwright(tmp_path / "jiny") is None
    assert os.environ.get("PFLANZER_PLAYWRIGHT_DIR") is None
