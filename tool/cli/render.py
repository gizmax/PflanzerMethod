"""Render SPA v headless prohlížeči (Playwright) pro brány smoke a a11y.

SPA (React/Vite/…) vrací z `/` jen prázdnou kostru `<div id="root"></div>` + bundle; smoke
a statická a11y kontrola nad surovým HTML by pak „prošly“ bez toho, aby cokoli ověřily.
Tento modul SPA pozná a — když je k dispozici Playwright s nainstalovaným prohlížečem —
vyrenderuje stránky přes `render_pages.cjs` (networkidle) a vrátí DOM + chyby z konzole.

Playwright se hledá v `<projekt>/node_modules/{playwright,@playwright/test}` nebo v adresáři
z env `PFLANZER_PLAYWRIGHT_DIR` (adresář, který obsahuje `node_modules/playwright`).
Jen stdlib; Node z `PFLANZER_NODE` nebo `node`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlsplit

SCRIPT = Path(__file__).with_name("render_pages.cjs")
INSTALL_HINT = "`npm i -D playwright && npx playwright install chromium`"

_EMPTY_ROOT = re.compile(r"<div\s+[^>]*\bid=[\"'](?:root|app)[\"'][^>]*>\s*</div>", re.I)
_SCRIPT_SRC = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.I)
_PW_NAMES = (("playwright",), ("@playwright", "test"), ("playwright-core",))


@dataclass
class RenderedPage:
    path: str
    status: int | None
    html: str
    root_empty: bool
    errors: list[str] = field(default_factory=list)          # uncaught výjimky
    console_errors: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def broken(self) -> bool:
        return (self.status is None or self.status >= 400 or self.root_empty
                or bool(self.errors))


@dataclass
class RenderResult:
    ok: bool
    why: str = ""
    pages: list[RenderedPage] = field(default_factory=list)


def is_spa(html: str) -> bool:
    """Prázdný `<div id="root|app">` + aspoň jeden `<script src>` (typicky `type=module`)."""
    return bool(html and _EMPTY_ROOT.search(html) and _SCRIPT_SRC.search(html))


def script_urls(html: str, base_url: str, limit: int = 6) -> list[str]:
    """Absolutní URL skriptů ze stejného hostu (bundle SPA)."""
    host = urlsplit(base_url).netloc
    out: list[str] = []
    for src in _SCRIPT_SRC.findall(html):
        url = urljoin(base_url, src)
        if urlsplit(url).netloc == host and url not in out:
            out.append(url)
    return out[:limit]


def _has_pw(root: Path) -> bool:
    nm = root / "node_modules"
    return any(nm.joinpath(*parts).is_dir() for parts in _PW_NAMES)


def find_playwright(project: Path) -> Path | None:
    """Adresář s `node_modules/playwright`: projekt, jinak env PFLANZER_PLAYWRIGHT_DIR."""
    cands = [Path(project)]
    env = os.environ.get("PFLANZER_PLAYWRIGHT_DIR")
    if env:
        e = Path(env)
        cands += [e, e.parent] if e.name == "node_modules" else [e]
    for c in cands:
        if _has_pw(c):
            return c
    return None


def render_pages(base_url: str, paths: list[str], pw_dir: Path, timeout_s: int = 30,
                 ) -> RenderResult:
    node = os.environ.get("PFLANZER_NODE") or shutil.which("node")
    if not node:
        return RenderResult(False, "chybí Node.js")
    try:
        res = subprocess.run(
            [node, str(SCRIPT), str(pw_dir), base_url, json.dumps(paths), str(timeout_s * 1000)],
            capture_output=True, text=True, timeout=timeout_s * (len(paths) + 2) + 30)
    except subprocess.TimeoutExpired:
        return RenderResult(False, "render vypršel")
    except OSError as e:
        return RenderResult(False, str(e))
    line = next((ln for ln in reversed(res.stdout.splitlines()) if ln.startswith("{")), "")
    try:
        data = json.loads(line)
    except ValueError:
        tail = (res.stderr or res.stdout).strip().splitlines()[-1:] or ["bez výstupu"]
        return RenderResult(False, f"render selhal: {tail[0][:160]}")
    if not data.get("ok"):
        why = str(data.get("why") or "render selhal")
        if data.get("browser"):
            why = "prohlížeč Playwrightu nejde spustit (`npx playwright install chromium`): " \
                  + why[:120]
        return RenderResult(False, why)
    pages = [RenderedPage(p["path"], p.get("status"), p.get("html", ""),
                          bool(p.get("rootEmpty")), list(p.get("errors") or []),
                          list(p.get("consoleErrors") or []), p.get("note", ""))
             for p in data.get("pages", [])]
    return RenderResult(True, pages=pages)
