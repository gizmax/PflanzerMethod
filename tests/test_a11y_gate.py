"""Brána a11y: statická kontrola HTML stránek běžící aplikace (server-rendered, bez .html)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tool.cli import a11y_html
from tool.cli import quality_gates as qg

APP_TMPL = '''
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE = """__PAGE__"""
CONTACT = """<!doctype html><html lang="cs"><head><title>Kontakt</title>
<meta name="viewport" content="width=device-width"></head><body><main><h1>Kontakt</h1>
<img src="x.png"></main></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = (CONTACT if self.path == "/kontakt" else PAGE).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)


HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''

HEAD = ('<!doctype html><html lang="cs"><head><title>Rezervace</title>'
        '<meta name="viewport" content="width=device-width"></head><body><main>'
        '<h1>Rezervace</h1><a href="/kontakt">Kontakt</a>')
BAD = HEAD + ('<form><input type="text" name="x"><button>Odeslat</button></form>'
              '</main></body></html>')
GOOD = HEAD + ('<form><label for="m">E-mail</label><input id="m" type="email" '
               'autocomplete="email"><button>Odeslat</button></form></main></body></html>')


def _app(root: Path, page: str, contact_alt: bool = False) -> Path:
    src = APP_TMPL.replace("__PAGE__", page)
    if contact_alt:
        src = src.replace('<img src="x.png">', '<img src="x.png" alt="">')
    root.mkdir(parents=True)
    (root / "app.py").write_text(src, encoding="utf-8")
    (root / ".pflanzer").mkdir()
    cmd = f"{sys.executable} app.py {{port}}"
    (root / ".pflanzer" / "project.toml").write_text(
        f"[preview]\ncommand = {json.dumps(cmd)}\n", encoding="utf-8")
    return root


def _a11y(path: Path) -> qg.GateResult:
    return qg.GATE_RUNNERS["a11y"](qg._make_ctx(path)[0])


def test_missing_label_fails_with_page_path(tmp_path: Path) -> None:
    res = _a11y(_app(tmp_path / "bad", BAD))
    assert res.status == "fail"
    assert "bez popisku" in res.details and "· /:" in res.details
    assert "/kontakt" in res.details  # odkaz z první stránky se taky zkontroloval


def test_fixed_app_passes_or_only_warns(tmp_path: Path) -> None:
    res = _a11y(_app(tmp_path / "ok", GOOD, contact_alt=True))
    assert res.status == "pass", res.details


def test_without_command_is_unverified_not_skip(tmp_path: Path) -> None:
    proj = tmp_path / "x"
    proj.mkdir()
    (proj / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    res = _a11y(proj)
    assert res.status == "skipped"
    assert res.details.startswith(qg.UNVERIFIED_PREFIX)


def test_smoke_and_a11y_share_one_app_run(tmp_path: Path) -> None:
    ctx = qg._make_ctx(_app(tmp_path / "s", GOOD, contact_alt=True))[0]
    assert qg.gate_smoke(ctx).status == "pass"
    first = ctx.app_run
    assert qg.gate_a11y(ctx).status == "pass"
    assert ctx.app_run is first


def test_analyzer_rules() -> None:
    html = ('<html><head></head><body><h1>a</h1><h1>b</h1><h4>c</h4><img src="a">'
            '<a href="/x"></a><button></button><input type="tel">'
            '<label>Jméno <input type="text" name="jmeno" autocomplete="name"></label>'
            '</body></html>')
    msgs = " | ".join(m for _s, m in a11y_html.analyze(html))
    for needle in ("<html lang>", "<title>", "viewport", "bez atributu alt", "bez popisku",
                   "odkaz bez přístupného textu", "tlačítko bez přístupného textu",
                   "jen jeden", "h1 → h4", "autocomplete"):
        assert needle in msgs, needle
