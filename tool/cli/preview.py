"""Preview variant pro Async — `pflanzer preview up|down|status --slug S`.

Spustí aplikaci z worktree každé varianty (A/B/C), před každou postaví malý
reverse proxy s heslem (HTTP Basic, uživatel `pflanzer`) a štítkem „Varianta X
k rozhodnutí — není to hotový produkt“ vloženým do HTML. Volitelně přidá
Cloudflare quick tunnel, aby zástupci klikli odkudkoli bez Vercelu a bez
pushnutí kódu mimo firmu.

    pflanzer preview up --slug S [--password P] [--tunnel auto|cloudflared|none]
                        [--host 127.0.0.1|0.0.0.0] [--base-port 8601] [--deadline TEXT]
    pflanzer preview status --slug S
    pflanzer preview down --slug S

Příkaz aplikace: `.pflanzer/project.toml` `[preview] command = "… {port}"`, jinak
autodetekce (viz `tool/cli/apprun.py`). Port aplikace = base-port + i*10, proxy = +1.
Stav (PID, porty, heslo) je v `<datová složka>/preview/<slug>.json`, logy vedle.

Jen stdlib. Procesy běží na pozadí (vlastní process group) i po skončení příkazu.
"""
from __future__ import annotations

import argparse
import base64
import hmac
import http.client
import http.server
import json
import os
import re
import secrets
import shutil
import socket
import socketserver
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli import apprun  # noqa: E402
from tool.cli.ux import CzechArgumentParser, die, emit, tips_for_project  # noqa: E402

USER = "pflanzer"
DEFAULT_BASE_PORT = 8601
LABEL_MARK = "data-pflanzer-label"
TUNNEL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te",
              "trailers", "transfer-encoding", "upgrade"}
HUB_URL = "http://localhost:8000/method/"


# --------------------------------------------------------------------------
# Auth reverse proxy (běží jako samostatný proces: `preview.py _proxy …`)
# --------------------------------------------------------------------------


def label_html(variant: str) -> bytes:
    name = f"Varianta {variant}" if variant in ("A", "B", "C") else "Varianta"
    text = f"{name} k rozhodnutí — není to hotový produkt"
    return (f'<div {LABEL_MARK} style="position:sticky;top:0;z-index:2147483647;'
            "background:#fff3cd;color:#664d03;font:14px/1.4 system-ui,sans-serif;"
            "padding:6px 12px;text-align:center;border-bottom:1px solid #e0c97a\">"
            f"{text}</div>").encode("utf-8")


_BODY_RE = re.compile(rb"<body\b[^>]*>", re.IGNORECASE)
_LABEL_PRESENT_RE = re.compile(rb"k rozhodnut|data-pflanzer-label", re.IGNORECASE)


def inject_label(html: bytes, variant: str) -> bytes:
    """Vloží štítek hned za `<body …>`; má-li stránka podobný štítek, nechá ji být."""
    if _LABEL_PRESENT_RE.search(html):
        return html
    m = _BODY_RE.search(html)
    if not m:
        return html
    return html[:m.end()] + label_html(variant) + html[m.end():]


def _make_handler(app_port: int, password: str, variant: str) -> type:
    expected = f"{USER}:{password}".encode()

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"
        server_version = "pflanzer-preview"

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write(f"{self.log_date_time_string()} {self.address_string()} "
                             f"{fmt % args}\n")
            sys.stderr.flush()

        def _authorized(self) -> bool:
            hdr = self.headers.get("Authorization", "")
            if not hdr.lower().startswith("basic "):
                return False
            try:
                given = base64.b64decode(hdr[6:].strip(), validate=True)
            except ValueError:
                return False
            return hmac.compare_digest(given, expected)

        def _reply(self, code: int, body: bytes, ctype: str = "text/plain; charset=utf-8",
                   extra: dict[str, str] | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _rewrite_location(self, loc: str) -> str:
            parts = urlsplit(loc)
            if parts.netloc in (f"127.0.0.1:{app_port}", f"localhost:{app_port}"):
                return (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
            return loc

        def _proxy(self) -> None:
            if not self._authorized():
                self._reply(401, "Přihlášení je potřeba (uživatel pflanzer a heslo od "
                                 "organizátora).\n".encode(),
                            extra={"WWW-Authenticate": 'Basic realm="Pflanzer preview", '
                                                       'charset="UTF-8"'})
                return
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else None
            headers = {k: v for k, v in self.headers.items()
                       if k.lower() not in HOP_BY_HOP | {"host", "authorization",
                                                         "accept-encoding", "content-length"}}
            headers["Host"] = f"127.0.0.1:{app_port}"
            headers["Accept-Encoding"] = "identity"
            if body is not None:
                headers["Content-Length"] = str(len(body))
            conn = http.client.HTTPConnection("127.0.0.1", app_port, timeout=60)
            try:
                conn.request(self.command, self.path, body=body, headers=headers)
                resp = conn.getresponse()
            except (OSError, http.client.HTTPException) as exc:
                self._reply(502, f"Aplikace varianty {variant} neodpovídá ({exc}).\n".encode())
                conn.close()
                return
            try:
                out = [(k, v) for k, v in resp.getheaders() if k.lower() not in HOP_BY_HOP]
                ctype = resp.getheader("Content-Type", "")
                inject = (ctype.lower().startswith("text/html") and self.command != "HEAD"
                          and not resp.getheader("Content-Encoding")
                          and resp.status not in (204, 304))
                data = resp.read() if inject else None
                if data is not None:
                    data = inject_label(data, variant)
                self.send_response(resp.status)
                for k, v in out:
                    kl = k.lower()
                    if kl == "location":
                        v = self._rewrite_location(v)
                    if data is not None and kl == "content-length":
                        continue
                    self.send_header(k, v)
                if data is not None:
                    self.send_header("Content-Length", str(len(data)))
                self.send_header("X-Robots-Tag", "noindex, nofollow")
                self.end_headers()
                if self.command == "HEAD":
                    return
                if data is not None:
                    self.wfile.write(data)
                else:
                    while chunk := resp.read(65536):
                        self.wfile.write(chunk)
            except (OSError, http.client.HTTPException):
                pass  # klient odešel / upstream spadl uprostřed odpovědi
            finally:
                conn.close()

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = _proxy

    return Handler


class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve_proxy(listen_host: str, listen_port: int, app_port: int, password: str,
                variant: str) -> None:
    srv = _Server((listen_host, listen_port), _make_handler(app_port, password, variant))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def _proxy_main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="preview.py _proxy")
    ap.add_argument("--listen-host", default="127.0.0.1")
    ap.add_argument("--listen-port", type=int, required=True)
    ap.add_argument("--app-port", type=int, required=True)
    ap.add_argument("--variant", required=True)
    a = ap.parse_args(argv)
    serve_proxy(a.listen_host, a.listen_port, a.app_port,
                os.environ.get("PFLANZER_PREVIEW_PASSWORD", ""), a.variant)


# --------------------------------------------------------------------------
# Stav na disku
# --------------------------------------------------------------------------


def preview_dir() -> Path:
    from tool.cli import db
    return Path(db.DATA_ROOT) / "preview"


def state_path(slug: str) -> Path:
    return preview_dir() / f"{slug}.json"


def load_state(slug: str) -> dict[str, Any] | None:
    try:
        return json.loads(state_path(slug).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_state(slug: str, state: dict[str, Any]) -> None:
    p = state_path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        p.chmod(0o600)  # je tam heslo
    except OSError:
        pass


def _pids(v: dict[str, Any]) -> dict[str, tuple[int, str]]:
    out = {}
    for key in ("app", "proxy", "tunnel"):
        pid = v.get(f"{key}_pid")
        if pid:
            out[key] = (int(pid), v.get(f"{key}_started", ""))
    return out


def _alive(pid: int, started: str) -> bool:
    """Žije *náš* proces (PID se stejným časem startu)?"""
    return apprun.proc_alive(pid) and (not started or apprun.proc_started(pid) == started)


def _lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))  # nic se neodešle, jen se zvolí rozhraní
            return str(s.getsockname()[0])
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"


def _gen_password() -> str:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(10))


# --------------------------------------------------------------------------
# Tunel
# --------------------------------------------------------------------------


def start_tunnel(proxy_port: int, log_path: Path, timeout: float = 40.0
                 ) -> tuple[int, str, str] | None:
    """`cloudflared tunnel --url …`; vrací (pid, start, https URL) nebo None."""
    exe = shutil.which("cloudflared")
    if not exe:
        return None
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_bytes(b"")
    with open(log_path, "ab") as log:
        proc = subprocess.Popen(
            [exe, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{proxy_port}"],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True)
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        m = TUNNEL_RE.search(log_path.read_text(encoding="utf-8", errors="replace"))
        if m:
            return proc.pid, apprun.proc_started(proc.pid), m.group(0)
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    apprun.kill_group(proc.pid)
    return None


# --------------------------------------------------------------------------
# up / down / status
# --------------------------------------------------------------------------


def _primary_dirs(slug: str) -> dict[str, Path]:
    from tool.cli import worktree as wt
    repos = wt.load_target_repos(slug)
    if not repos:
        raise ValueError(f"Projekt ‚{slug}‘ nemá target repo. Spusťte `pflanzer worktree setup "
                         f"--slug {slug}`.")
    primary = repos[0]
    out: dict[str, Path] = {}
    for variant in wt.PARALLEL_VARIANTS + wt.MOB_VARIANTS:
        path = wt.worktree_dir(slug, variant, primary, True)
        if path.is_dir():
            if primary.workspace and (path / primary.workspace).is_dir():
                path = path / primary.workspace
            out[variant] = path
    if not out:
        raise ValueError(f"Worktrees varianty ještě neexistují. Spusťte nejdřív "
                         f"`pflanzer worktree setup --slug {slug}`.")
    return out


def _stop_variant(v: dict[str, Any]) -> None:
    for key in ("tunnel", "proxy", "app"):
        pid_started = _pids(v).get(key)
        if pid_started and _alive(*pid_started):
            apprun.kill_group(pid_started[0])


def down(slug: str) -> dict[str, Any]:
    state = load_state(slug)
    if not state:
        return {"slug": slug, "stopped": [], "was_running": False}
    stopped = []
    for name, v in state.get("variants", {}).items():
        running = [k for k, (pid, st) in _pids(v).items() if _alive(pid, st)]
        _stop_variant(v)
        if running:
            stopped.append(name)
    try:
        state_path(slug).unlink()
    except OSError:
        pass
    return {"slug": slug, "stopped": stopped, "was_running": bool(stopped)}


def _variant_running(v: dict[str, Any]) -> dict[str, bool]:
    return {k: _alive(pid, st) for k, (pid, st) in _pids(v).items()}


def status(slug: str, *, probe: bool = True) -> dict[str, Any]:
    state = load_state(slug)
    if not state:
        return {"slug": slug, "running": False, "variants": {}}
    out: dict[str, Any] = {}
    for name, v in state.get("variants", {}).items():
        alive = _variant_running(v)
        http_status = None
        if probe and alive.get("proxy") and alive.get("app", True):
            http_status = apprun.http_get(f"http://127.0.0.1:{v['proxy_port']}/",
                                          auth=(USER, state["password"]), timeout=3)
        out[name] = {"url": v["url"], "local_url": v["local_url"],
                     "tunnel_url": v.get("tunnel_url"), "alive": alive,
                     "ok": bool(alive) and all(alive.values()) and http_status is not None
                     and http_status < 500,
                     "http_status": http_status, "app_port": v["app_port"],
                     "proxy_port": v["proxy_port"], "command": v.get("command"),
                     "log": v.get("log")}
    return {"slug": slug, "running": any(x["ok"] for x in out.values()),
            "password": state["password"], "user": USER, "host": state.get("host"),
            "tunnel": state.get("tunnel"), "variants": out}


def _fail_text(name: str, v: dict[str, Any], why: str) -> str:
    log = apprun.tail(Path(v["log"]))
    return (f"Varianta {name} nenaběhla: {why}.\n  Příkaz: {v.get('command')}\n"
            f"  Posledních řádků logu ({v['log']}):\n"
            + "\n".join(f"    {ln}" for ln in (log or "(log je prázdný)").splitlines()))


def up(slug: str, *, password: str | None = None, tunnel: str = "auto",
       host: str = "127.0.0.1", base_port: int = DEFAULT_BASE_PORT,
       deadline: str | None = None, timeout: float | None = None) -> dict[str, Any]:
    if password is not None and not password.strip():
        raise ValueError("Heslo nesmí být prázdné — preview je vždy chráněné heslem "
                         "(vynechte --password a vygeneruje se).")
    if host not in ("127.0.0.1", "0.0.0.0"):
        raise ValueError("--host je 127.0.0.1 (jen tento počítač) nebo 0.0.0.0 (celá síť).")
    if tunnel not in ("auto", "cloudflared", "none"):
        raise ValueError("--tunnel je auto, cloudflared nebo none.")
    if timeout is None:
        timeout = float(os.environ.get("PFLANZER_PREVIEW_TIMEOUT", "90"))

    old = load_state(slug)
    if old and any(any(_variant_running(v).values()) for v in old.get("variants", {}).values()):
        raise ValueError(f"Preview projektu ‚{slug}‘ už běží. Zastavte ho "
                         f"`pflanzer preview down --slug {slug}`, nebo ukažte stav "
                         f"`pflanzer preview status --slug {slug}`.")
    dirs = _primary_dirs(slug)
    have_cf = shutil.which("cloudflared") is not None
    if tunnel == "cloudflared" and not have_cf:
        raise ValueError("Chybí `cloudflared` v PATH. Nainstalujte ho (např. "
                         "`brew install cloudflared`), nebo použijte --tunnel none.")
    use_tunnel = tunnel == "cloudflared" or (tunnel == "auto" and have_cf)

    plan = []
    for i, (name, path) in enumerate(dirs.items()):
        app_port = base_port + i * 10
        spec = apprun.detect_run(path, app_port)
        if spec is None:
            raise ValueError(
                f"Pro variantu {name} nevím, jak spustit aplikaci. Doplňte do "
                f".pflanzer/project.toml v target repu:\n  [preview]\n  "
                'command = "npm run dev -- --port {port}"\n(v příkazu `{port}` nahradí '
                "preview číslem portu).")
        for port in (app_port, app_port + 1):
            if not apprun.port_free(port, "127.0.0.1") or (
                    port == app_port + 1 and not apprun.port_free(port, host)):
                raise ValueError(f"Port {port} je obsazený. Zvolte jiný základ: "
                                 f"`--base-port {base_port + 100}`.")
        plan.append((name, path, spec, app_port))

    password = password or _gen_password()
    d = preview_dir()
    d.mkdir(parents=True, exist_ok=True)
    ip = _lan_ip() if host == "0.0.0.0" else "127.0.0.1"
    state: dict[str, Any] = {
        "slug": slug, "password": password, "user": USER, "host": host,
        "tunnel": "cloudflared" if use_tunnel else "none",
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "variants": {},
    }
    warnings: list[str] = []
    failures: list[str] = []
    procs: dict[str, subprocess.Popen] = {}
    try:
        for name, path, spec, app_port in plan:
            proxy_port = app_port + 1
            log = d / f"{slug}-{name}.log"
            log.write_bytes(b"")
            v: dict[str, Any] = {
                "worktree": str(path), "command": spec.command, "source": spec.source,
                "app_port": app_port, "proxy_port": proxy_port, "log": str(log),
                "local_url": f"http://{ip}:{proxy_port}/",
            }
            state["variants"][name] = v
            app = apprun.start_app(spec, log)
            procs[name] = app
            v["app_pid"], v["app_started"] = app.pid, apprun.proc_started(app.pid)
            env = {**os.environ, "PFLANZER_PREVIEW_PASSWORD": password,
                   "PYTHONPATH": str(REPO_ROOT)}
            with open(d / f"{slug}-{name}-proxy.log", "ab") as plog:
                proxy = subprocess.Popen(
                    [sys.executable, str(Path(__file__).resolve()), "_proxy",
                     "--listen-host", host, "--listen-port", str(proxy_port),
                     "--app-port", str(app_port), "--variant", name],
                    env=env, stdin=subprocess.DEVNULL, stdout=plog, stderr=subprocess.STDOUT,
                    start_new_session=True)
            v["proxy_pid"], v["proxy_started"] = proxy.pid, apprun.proc_started(proxy.pid)
            save_state(slug, state)
        for name, _path, _spec, _port in plan:
            v = state["variants"][name]
            ok, st = apprun.wait_http(f"http://127.0.0.1:{v['proxy_port']}/", timeout=timeout,
                                      proc=procs[name], auth=(USER, password))
            if not ok:
                alive = _variant_running(v)
                why = ("aplikace skončila" if not alive.get("app", True)
                       else f"do {int(timeout)} s neodpověděla"
                       + (f" (poslední status {st})" if st else ""))
                failures.append(_fail_text(name, v, why))
        if failures:
            raise RuntimeError("\n\n".join(failures))
        for name, path, _spec, app_port in plan:
            w = check_reachable(name, path, app_port)
            if w:
                warnings.append(w)
        if use_tunnel:
            for name, *_ in plan:
                v = state["variants"][name]
                res = start_tunnel(v["proxy_port"], d / f"{slug}-{name}-tunnel.log")
                if res is None:
                    warnings.append(f"Tunel pro variantu {name} se nepodařilo otevřít "
                                    f"(log {d / f'{slug}-{name}-tunnel.log'}); varianta je jen "
                                    "lokálně.")
                    continue
                v["tunnel_pid"], v["tunnel_started"], v["tunnel_url"] = res
        for v in state["variants"].values():
            v["url"] = v.get("tunnel_url") or v["local_url"]
        save_state(slug, state)
    except BaseException:
        for v in state["variants"].values():
            _stop_variant(v)
        try:
            state_path(slug).unlink()
        except OSError:
            pass
        raise

    from tool.cli import worktree as wt
    stored: dict[str, bool] = {}
    for name, v in state["variants"].items():
        try:
            stored[name] = wt.set_prototype_url(slug, name, v["url"])
        except Exception:  # noqa: BLE001 — zápis URL nesmí shodit běžící preview
            stored[name] = False
    if not all(stored.values()):
        warnings.append("URL se zatím nezapsala do DB u: "
                        + ", ".join(n for n, ok in stored.items() if not ok)
                        + " (Build ještě není zapsaný) — předejte je v `real_urls` při zápisu "
                          "Buildu.")
    if host == "0.0.0.0":
        warnings.append("Preview je dostupné v celé síti přes HTTP bez šifrování; chrání ho jen "
                        "heslo. Pro vzdálené zástupce použijte tunel.")
    if use_tunnel and any(v.get("tunnel_url") for v in state["variants"].values()):
        warnings.append("Tunel = provoz s preview jde přes Cloudflare (quick tunnel). Uveďte to "
                        "na checkpointu bezpečnosti.")
    if not use_tunnel and host == "127.0.0.1":
        warnings.append("Odkazy fungují jen na tomto počítači. Pro kolegy použijte "
                        "--host 0.0.0.0 (stejná síť) nebo cloudflared (odkudkoli).")
    return {"slug": slug, "user": USER, "password": password, "host": host,
            "tunnel": state["tunnel"], "deadline": deadline, "warnings": warnings,
            "variants": {n: {k: v.get(k) for k in ("url", "local_url", "tunnel_url", "app_port",
                                                   "proxy_port", "command", "source", "log")}
                         for n, v in state["variants"].items()},
            "prototype_url_stored": stored}


_ROUTE_RES = (
    re.compile(r"""\b(?:app|router|server|api)\.(?:get|post|put|all|use)\(\s*['"`](/[^'"`:*?]*)['"`]"""),
    re.compile(r"""@\w+\.(?:get|post|route|api_route)\(\s*['"](/[^'"{<:]*)['"]"""),
    re.compile(r"""\bpath\(\s*r?['"]([\w\-/]+)['"]"""),
)
_SKIP_PARTS = ("test", "spec", "docs/", "node_modules", ".pflanzer", "fixtures", "__tests__")


def _added_routes(wt: Path) -> list[str]:
    """Statické cesty, které varianta přidala proti mainu (z diffu: route definice + nové soubory)."""
    base = None
    for ref in ("origin/main", "origin/master", "main", "master"):
        rc = subprocess.run(["git", "rev-parse", "--verify", "-q", ref], cwd=wt,
                            capture_output=True, text=True)
        if rc.returncode == 0:
            base = ref
            break
    if not base:
        return []
    diff = subprocess.run(["git", "diff", "--unified=0", f"{base}...HEAD"], cwd=wt,
                          capture_output=True, text=True, timeout=30).stdout
    routes: list[str] = []
    for ln in diff.splitlines():
        if not ln.startswith("+") or ln.startswith("+++"):
            continue
        for rx in _ROUTE_RES:
            for m in rx.finditer(ln):
                r = m.group(1)
                if not r.startswith("/"):
                    r = "/" + r
                r = r.rstrip("/") or "/"
                if r != "/" and r not in routes:
                    routes.append(r)
    names = subprocess.run(["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"],
                           cwd=wt, capture_output=True, text=True, timeout=30).stdout.split()
    for n in names:
        low = n.lower()
        if any(p in low for p in _SKIP_PARTS) or not low.endswith(
                (".html", ".ejs", ".pug", ".hbs", ".njk", ".jinja", ".jinja2", ".tsx", ".jsx",
                 ".vue", ".svelte")):
            continue
        stem = Path(n).stem.lower()
        if stem not in ("index", "layout", "base", "app", "main", "_app", "page"):
            r = "/" + stem
            if r not in routes and not any(x.strip("/").endswith(stem) for x in routes):
                routes.append(r)
    return routes


def check_reachable(name: str, wt: Path, app_port: int) -> str | None:
    """⚠ text, když varianta přidala novou cestu, ale na `/` na ni nevede žádný odkaz.

    Heuristika: nové cesty z diffu proti mainu vs. href / action na `/` běžící varianty.
    Nic nenajde-li / nejde-li to zjistit, mlčí (None).
    """
    try:
        routes = _added_routes(wt)
        if not routes:
            return None
        st, body, _ct = apprun.http_fetch(f"http://127.0.0.1:{app_port}/", timeout=5.0)
        if st is None or st >= 400 or not body:
            return None
        hrefs = [h.split("#")[0].split("?")[0].rstrip("/") or "/"
                 for h in re.findall(r"""(?:href|action)\s*=\s*['"]([^'"]+)['"]""", body, re.I)]
        hrefs = [re.sub(r"^https?://[^/]+", "", h) for h in hrefs]
        linked = [r for r in routes
                  if any(h == r or h.endswith(r) or h == r.lstrip("/") for h in hrefs)]
        if linked:
            return None
        shown = ", ".join(routes[:3])
        return (f"varianta {name} na / nenabízí nic nového — je funkce za vypnutým přepínačem? "
                f"(přidala cestu {shown}, ale z / na ni nevede odkaz; builder má odkaz přidat "
                "a flag musí být v preview zapnutý).")
    except Exception:  # noqa: BLE001 — advisory only, nikdy neshodí preview
        return None


def hub_running() -> bool:
    return apprun.http_get(HUB_URL, timeout=0.5) is not None


def share_message(res: dict[str, Any], hub: str | None) -> str:
    rows = "\n".join(f"  Varianta {n}: {v['url']}" for n, v in res["variants"].items())
    until = res.get("deadline") or "[doplňte termín]"
    msg = ("Dobrý den, připravili jsme tři varianty k rozhodnutí. Není to hotový produkt, "
           "zajímá nás váš dojem.\n"
           f"{rows}\n"
           f"Přihlášení: uživatel {res['user']}, heslo {res['password']}\n"
           "Co udělat: projděte všechny tři varianty (zabere to asi 15 minut) a u každé "
           "napište, co fungovalo a co ne.\n"
           f"Do kdy: {until}.")
    if hub:
        msg += f"\nZpětnou vazbu zapište sem: {hub}"
    return msg


def _up_view(res: dict[str, Any]) -> tuple[list[str], str, str]:
    slug = res["slug"]
    lines = [f"Varianta {n}: {v['url']}" for n, v in res["variants"].items()]
    lines.append(f"Přihlášení: uživatel {res['user']}, heslo {res['password']}")
    hub = HUB_URL if hub_running() else None
    msg = share_message(res, hub)
    lines.append("Zpráva k přeposlání zástupcům:\n\n"
                 + "\n".join(f"> {ln}" for ln in msg.splitlines()) + "\n")
    lines.append(f"Stav a zastavení: `pflanzer preview status --slug {slug}`, "
                 f"`pflanzer preview down --slug {slug}`.")
    nxt = ("Pošlete zprávu zástupcům a nechte tento počítač zapnutý po dobu Asyncu; potom "
           f"`/pm feedback {slug}`.")
    return lines, nxt, msg


def _status_next(slug: str) -> str:
    """Další krok podle skutečné fáze projektu (preview se vypíná i po Shipu)."""
    try:
        from tool.cli.status import project_detail
        return f"`{project_detail(slug)['next_step']}`"
    except Exception:  # noqa: BLE001 — advisory only
        return f"`/pm status {slug}`"


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "_proxy":
        _proxy_main(argv[1:])
        return
    p = CzechArgumentParser(prog="pflanzer preview", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    js = {"action": "store_true", "help": "Strojový JSON výstup místo lidského"}

    pu = sub.add_parser("up", help="Spustí varianty s heslem (a tunelem) a zapíše URL")
    pu.add_argument("--slug", required=True)
    pu.add_argument("--password", default=None, help="Heslo (jinak se vygeneruje)")
    pu.add_argument("--tunnel", choices=["auto", "cloudflared", "none"], default="auto",
                    help="auto = cloudflared, když je v PATH; none = jen lokálně")
    pu.add_argument("--host", default="127.0.0.1",
                    help="127.0.0.1 (jen tento počítač) nebo 0.0.0.0 (celá síť)")
    pu.add_argument("--base-port", type=int, default=DEFAULT_BASE_PORT,
                    help="port aplikace varianty A; B = +10, C = +20; proxy = port aplikace + 1")
    pu.add_argument("--deadline", default=None, help="Termín pro zprávu zástupcům, např. „pátek 17:00“")
    pu.add_argument("--json", **js)
    ps = sub.add_parser("status", help="Co běží")
    ps.add_argument("--slug", required=True)
    ps.add_argument("--json", **js)
    pd = sub.add_parser("down", help="Ukončí varianty, proxy i tunely")
    pd.add_argument("--slug", required=True)
    pd.add_argument("--json", **js)
    args = p.parse_args(argv)

    try:
        _dispatch(args)
    except ValueError as exc:
        die(str(exc))
    except RuntimeError as exc:
        die(str(exc))


def _dispatch(args: argparse.Namespace) -> None:
    slug = args.slug
    if args.cmd == "up":
        res = up(slug, password=args.password, tunnel=args.tunnel, host=args.host,
                 base_port=args.base_port, deadline=args.deadline)
        lines, nxt, msg = _up_view(res)
        res["message"] = msg
        tips = tips_for_project(slug, "async", {})
        emit(res, title=f"Preview běží ({len(res['variants'])} varianty)", lines=lines,
             next_step=nxt, tips=tips, warnings=res["warnings"], as_json=args.json)
    elif args.cmd == "status":
        res = status(slug)
        if not res["variants"]:
            emit(res, title="Preview neběží", lines=["Pro tento projekt není nic spuštěno."],
                 next_step=f"`pflanzer preview up --slug {slug}`", as_json=args.json)
            return
        lines = []
        for n, v in res["variants"].items():
            dead = [k for k, a in v["alive"].items() if not a]
            if v["ok"]:
                state = "běží"
            elif dead:
                state = "NEBĚŽÍ (" + ", ".join(dead) + " spadl)"
            else:
                state = f"neodpovídá (status {v['http_status']})"
            lines.append(f"Varianta {n}: {state} — {v['url']}")
        lines.append(f"Přihlášení: uživatel {res['user']}, heslo {res['password']}")
        emit(res, title="Stav preview", lines=lines,
             next_step=(f"`pflanzer preview down --slug {slug}`" if res["running"]
                        else f"`pflanzer preview down --slug {slug}` a znovu `up`"),
             as_json=args.json)
    else:
        res = down(slug)
        emit(res, title="Preview zastaveno" if res["was_running"] else "Nic nebylo spuštěno",
             lines=[f"Ukončeno: {', '.join(res['stopped']) or 'nic'}"],
             next_step=_status_next(slug) if res["was_running"] else None,
             as_json=args.json)


if __name__ == "__main__":
    main()
