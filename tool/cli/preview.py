"""Preview variant pro Async — `pflanzer preview up|down|status --slug S`.

Spustí aplikaci z worktree každé varianty (A/B/C), před každou postaví malý
reverse proxy s heslem (HTTP Basic, uživatel `pflanzer`) a štítkem „Varianta X
k rozhodnutí — není to hotový produkt“ vloženým do HTML. Volitelně přidá
Cloudflare quick tunnel, aby zástupci klikli odkudkoli bez Vercelu a bez
pushnutí kódu mimo firmu.

    pflanzer preview up --slug S [--password P] [--tunnel auto|cloudflared|none]
                        [--host 127.0.0.1|0.0.0.0] [--base-port 8601] [--deadline TEXT]
    pflanzer preview status --slug S
    pflanzer preview restart --slug S [--variants A,C]   (po Iterate; zachová heslo a tunel)
    pflanzer preview down --slug S

Příkaz aplikace: `.pflanzer/project.toml` `[preview] command = "… {port}"`, jinak
autodetekce (viz `tool/cli/apprun.py`). Port aplikace = base-port + i*10, proxy = +1.
Multi-repo projekt (`target_repos` s rolemi): pro každou variantu se spustí všechna repa;
sekundární běží na portu app+1000+idx (idx = pořadí repa, primární = 0) a primární dostane
env `<ROLE>_URL` a `PFLANZER_<ROLE>_URL` (např. `API_URL=http://127.0.0.1:9601`). Příkaz
sekundárního repa: `[preview.<role>] command = "… {port} …"`, jinak autodetekce. Proxy je jen
před primárním; `down` ukončí vše.
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
import select
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


# SPA (React/Vite…): štítek, který appka vykreslí sama až za běhu, v HTML kostře není vidět.
# Proxy proto vloží svůj štítek a malý skript ho skryje, jakmile je v DOM štítek jiný.
_LABEL_DEDUP_JS = (
    b"<script>(function(){var m=document.querySelector('[data-pflanzer-label]');"
    b"if(!m)return;var re=/k rozhodnut/i;function other(){"
    b"var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),n;"
    b"while((n=w.nextNode())){if(!m.contains(n)&&re.test(n.nodeValue))return true}"
    b"return false}function chk(){m.style.display=other()?'none':''}"
    b"chk();var o=new MutationObserver(chk);"
    b"o.observe(document.body,{childList:true,subtree:true,characterData:true});"
    b"setTimeout(function(){o.disconnect()},20000)})();</script>")


def label_html(variant: str) -> bytes:
    name = f"Varianta {variant}" if variant in ("A", "B", "C") else "Varianta"
    text = f"{name} k rozhodnutí — není to hotový produkt"
    return (f'<div {LABEL_MARK} style="position:sticky;top:0;z-index:2147483647;'
            "background:#fff3cd;color:#664d03;font:14px/1.4 system-ui,sans-serif;"
            "padding:6px 12px;text-align:center;border-bottom:1px solid #e0c97a\">"
            f"{text}</div>").encode("utf-8") + _LABEL_DEDUP_JS


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

        def _is_upgrade(self) -> bool:
            return ("upgrade" in self.headers.get("Connection", "").lower()
                    and bool(self.headers.get("Upgrade")))

        def _tunnel(self) -> None:
            """WebSocket (Vite HMR…): přepošli handshake na aplikaci a kopíruj bajty oběma směry."""
            try:
                up = socket.create_connection(("127.0.0.1", app_port), timeout=10)
            except OSError as exc:
                self._reply(502, f"Aplikace varianty {variant} neodpovídá ({exc}).\n".encode())
                return
            lines = [f"{self.command} {self.path} HTTP/1.1"]
            for k, v in self.headers.items():
                kl = k.lower()
                if kl == "authorization":
                    continue
                if kl == "host":
                    v = f"127.0.0.1:{app_port}"
                elif kl == "origin":
                    v = f"http://127.0.0.1:{app_port}"
                lines.append(f"{k}: {v}")
            up.sendall(("\r\n".join(lines) + "\r\n\r\n").encode("latin-1"))
            up.settimeout(None)
            client = self.connection
            socks = [client, up]
            try:
                while True:
                    readable, _, _ = select.select(socks, [], [], 60)
                    if not readable:
                        continue
                    for src in readable:
                        data = src.recv(65536)
                        if not data:
                            return
                        (up if src is client else client).sendall(data)
            except OSError:
                pass
            finally:
                up.close()
                self.close_connection = True

        def _proxy(self) -> None:
            if not self._authorized():
                self._reply(401, "Přihlášení je potřeba (uživatel pflanzer a heslo od "
                                 "organizátora).\n".encode(),
                            extra={"WWW-Authenticate": 'Basic realm="Pflanzer preview", '
                                                       'charset="UTF-8"'})
                return
            if self._is_upgrade():
                self._tunnel()
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
    for role, e in (v.get("extra") or {}).items():  # sekundární repa (multi-repo)
        if e.get("app_pid"):
            out[role] = (int(e["app_pid"]), e.get("app_started", ""))
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


def role_env_name(role: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", role.upper()).strip("_") or "REPO"


def _secondary_dirs(slug: str) -> dict[str, dict[str, Path]]:
    """Sekundární repa multi-repo projektu: role -> {varianta: worktree}. Jedno repo = {}."""
    try:
        from tool.cli import worktree as wt
        repos = wt.load_target_repos(slug)
    except Exception:  # noqa: BLE001 — bez DB / projektu zůstane jen primární repo
        return {}
    out: dict[str, dict[str, Path]] = {}
    for repo in repos[1:]:
        per: dict[str, Path] = {}
        for variant in wt.PARALLEL_VARIANTS + wt.MOB_VARIANTS:
            path = wt.worktree_dir(slug, variant, repo, False)
            if path.is_dir():
                if repo.workspace and (path / repo.workspace).is_dir():
                    path = path / repo.workspace
                per[variant] = path
        if per:
            out[repo.role] = per
    return out


def _stop_variant(v: dict[str, Any]) -> None:
    pids = _pids(v)
    order = ["tunnel", "proxy", "app"] + [k for k in pids if k not in ("tunnel", "proxy", "app")]
    for key in order:
        pid_started = pids.get(key)
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
        repos = {"primary": {"alive": alive.get("app"), "port": v["app_port"]}} \
            if v.get("extra") else {}
        for role, e in (v.get("extra") or {}).items():
            repos[role] = {"alive": alive.get(role), "port": e["app_port"],
                           "url": e.get("url"), "command": e.get("command")}
        out[name] = {"url": v["url"], "local_url": v["local_url"], "repos": repos,
                     "tunnel_url": v.get("tunnel_url"), "alive": alive,
                     "ok": bool(alive) and all(alive.values()) and http_status is not None
                     and http_status < 500,
                     "http_status": http_status, "app_port": v["app_port"],
                     "proxy_port": v["proxy_port"], "command": v.get("command"),
                     "log": v.get("log")}
    return {"slug": slug, "running": any(x["ok"] for x in out.values()),
            "password": state["password"], "user": USER, "host": state.get("host"),
            "tunnel": state.get("tunnel"), "variants": out}


def _spawn_proxy(log: Path, host: str, proxy_port: int, app_port: int, name: str,
                 password: str) -> subprocess.Popen:
    env = {**os.environ, "PFLANZER_PREVIEW_PASSWORD": password, "PYTHONPATH": str(REPO_ROOT)}
    with open(log, "ab") as plog:
        return subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "_proxy",
             "--listen-host", host, "--listen-port", str(proxy_port),
             "--app-port", str(app_port), "--variant", name],
            env=env, stdin=subprocess.DEVNULL, stdout=plog, stderr=subprocess.STDOUT,
            start_new_session=True)


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
        raise ValueError(f"Preview projektu ‚{slug}‘ už běží. Po Iterate (nový kód) ho "
                         f"restartujte `pflanzer preview restart --slug {slug}` — zachová "
                         "heslo, porty i odkazy (tunel). Úplné zastavení: "
                         f"`pflanzer preview down --slug {slug}`; stav: "
                         f"`pflanzer preview status --slug {slug}`.")
    dirs = _primary_dirs(slug)
    have_cf = shutil.which("cloudflared") is not None
    if tunnel == "cloudflared" and not have_cf:
        raise ValueError("Chybí `cloudflared` v PATH. Nainstalujte ho (např. "
                         "`brew install cloudflared`), nebo použijte --tunnel none.")
    use_tunnel = tunnel == "cloudflared" or (tunnel == "auto" and have_cf)

    secondary = _secondary_dirs(slug)
    skipped_repos: list[str] = []
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
        if "{api_port}" in (apprun.read_preview_config(path).get("command") or "") and \
                not apprun.port_free(apprun.api_port_for(app_port), "127.0.0.1"):
            raise ValueError(f"API port {apprun.api_port_for(app_port)} (`{{api_port}}`) je "
                             f"obsazený. Zvolte jiný základ: `--base-port {base_port + 100}`.")
        extras: list[tuple[str, Path, apprun.RunSpec, int]] = []
        for idx, (role, per) in enumerate(secondary.items(), start=1):
            if name not in per:
                continue
            port = app_port + 1000 + idx
            sspec = apprun.detect_run(per[name], port, role=role, config_wt=path)
            if sspec is None:
                skipped_repos.append(
                    f"Repo {role} (varianta {name}) se nespouští — nevím jak. Doplňte do "
                    f".pflanzer/project.toml:\n  [preview.{role}]\n  command = \"…{{port}}…\"")
                continue
            if not apprun.port_free(port, "127.0.0.1"):
                raise ValueError(f"Port {port} (repo {role}) je obsazený. Zvolte jiný základ: "
                                 f"`--base-port {base_port + 100}`.")
            extras.append((role, per[name], sspec, port))
        plan.append((name, path, spec, app_port, extras))

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
    notes: list[str] = []
    failures: list[str] = []
    procs: dict[str, subprocess.Popen] = {}
    try:
        for name, path, spec, app_port, extras in plan:
            proxy_port = app_port + 1
            log = d / f"{slug}-{name}.log"
            log.write_bytes(b"")
            v: dict[str, Any] = {
                "worktree": str(path), "command": spec.command, "source": spec.source,
                "app_port": app_port, "proxy_port": proxy_port, "log": str(log),
                "local_url": f"http://{ip}:{proxy_port}/",
            }
            state["variants"][name] = v
            # Sekundární repa jedou první; primární dostane jejich URL v env.
            urls = {role: f"http://127.0.0.1:{port}" for role, _w, _s, port in extras}

            def _links(roles: Any) -> dict[str, str]:
                out: dict[str, str] = {}
                for r in roles:
                    out[f"{role_env_name(r)}_URL"] = urls[r]
                    out[f"PFLANZER_{role_env_name(r)}_URL"] = urls[r]
                return out

            link_env = _links(urls)
            for role, swt, sspec, port in extras:
                elog = d / f"{slug}-{name}-{role}.log"
                elog.write_bytes(b"")
                sspec.env = {**_links(r for r in urls if r != role), **sspec.env}
                eproc = apprun.start_app(sspec, elog)
                procs[f"{name}:{role}"] = eproc
                v.setdefault("extra", {})[role] = {
                    "worktree": str(swt), "command": sspec.command, "source": sspec.source,
                    "app_port": port, "url": urls[role], "log": str(elog),
                    "app_pid": eproc.pid, "app_started": apprun.proc_started(eproc.pid)}
            spec.env = {**link_env, **spec.env}
            save_state(slug, state)
            app = apprun.start_app(spec, log)
            procs[name] = app
            v["app_pid"], v["app_started"] = app.pid, apprun.proc_started(app.pid)
            proxy = _spawn_proxy(d / f"{slug}-{name}-proxy.log", host, proxy_port, app_port,
                                 name, password)
            v["proxy_pid"], v["proxy_started"] = proxy.pid, apprun.proc_started(proxy.pid)
            save_state(slug, state)
        for name, _path, _spec, _port, _extras in plan:
            v = state["variants"][name]
            for role, e in (v.get("extra") or {}).items():
                eok, est = apprun.wait_http(f"http://127.0.0.1:{e['app_port']}/", timeout=timeout,
                                            proc=procs[f"{name}:{role}"], ok=lambda s: True)
                if not eok:
                    why = ("aplikace skončila" if not _alive(e["app_pid"], e["app_started"])
                           else f"do {int(timeout)} s neodpověděla")
                    failures.append(_fail_text(f"{name} (repo {role})", e, why))
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
        for name, path, _spec, app_port, _extras in plan:
            w = check_reachable(name, path, app_port)
            if w:
                warnings.append(w)
            elif is_spa(path):
                notes.append(f"Varianta {name} je SPA — kontrola „nabízí něco nového“ se "
                             "přeskakuje (odkazy vznikají až v prohlížeči).")
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
    warnings.extend(skipped_repos)
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
            "tunnel": state["tunnel"], "deadline": deadline, "warnings": warnings, "notes": notes,
            "variants": {n: {k: v.get(k) for k in ("url", "local_url", "tunnel_url", "app_port",
                                                   "proxy_port", "command", "source", "log")}
                            | {"repos": {r: {"port": e["app_port"], "url": e["url"],
                                             "command": e["command"]}
                                         for r, e in (v.get("extra") or {}).items()}}
                         for n, v in state["variants"].items()},
            "prototype_url_stored": stored}


def _wait_port_free(port: int, timeout: float = 8.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if apprun.port_free(port, "127.0.0.1"):
            return True
        time.sleep(0.2)
    return apprun.port_free(port, "127.0.0.1")


def parse_variants(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [x.strip().upper() for x in re.split(r"[,\s]+", raw) if x.strip()] or None


def restart(slug: str, *, variants: list[str] | None = None,
            timeout: float | None = None) -> dict[str, Any]:
    """Restartuje procesy aplikace variant (nový kód po Iterate); heslo, porty, proxy a tunel
    zůstávají, takže odkazy zástupců dál fungují."""
    state = load_state(slug)
    if not state or not state.get("variants"):
        raise ValueError(f"Preview projektu ‚{slug}‘ neběží. Spusťte ho "
                         f"`pflanzer preview up --slug {slug}`.")
    if timeout is None:
        timeout = float(os.environ.get("PFLANZER_PREVIEW_TIMEOUT", "90"))
    names = variants or list(state["variants"])
    unknown = [n for n in names if n not in state["variants"]]
    if unknown:
        raise ValueError(f"Varianta {', '.join(unknown)} v preview není "
                         f"(jsou: {', '.join(state['variants'])}).")
    d = preview_dir()
    password = state["password"]
    host = state.get("host", "127.0.0.1")
    restarted: list[str] = []
    warnings: list[str] = []
    procs: dict[str, subprocess.Popen] = {}
    for name in names:
        v = state["variants"][name]
        pids = _pids(v)
        for key, (pid, started) in pids.items():  # jen aplikace; proxy a tunel nechat být
            if key not in ("proxy", "tunnel") and _alive(pid, started):
                apprun.kill_group(pid)
        wt = Path(v["worktree"])
        ports = [v["app_port"]] + [e["app_port"] for e in (v.get("extra") or {}).values()]
        busy = [p for p in ports if not _wait_port_free(p)]
        if busy:
            raise ValueError(f"Port {busy[0]} varianty {name} po zastavení pořád drží jiný "
                             "proces; ukončete ho, nebo použijte `preview down` a `up`.")
        urls = {r: e["url"] for r, e in (v.get("extra") or {}).items()}

        def _links(roles: Any, urls: dict[str, str] = urls) -> dict[str, str]:
            out: dict[str, str] = {}
            for r in roles:
                out[f"{role_env_name(r)}_URL"] = urls[r]
                out[f"PFLANZER_{role_env_name(r)}_URL"] = urls[r]
            return out

        for role, e in (v.get("extra") or {}).items():
            sspec = apprun.detect_run(Path(e["worktree"]), e["app_port"], role=role,
                                      config_wt=wt)
            if sspec is None:
                warnings.append(f"Repo {role} (varianta {name}) se nespustilo — nevím jak.")
                continue
            sspec.env = {**_links(r for r in urls if r != role), **sspec.env}
            log = Path(e["log"])
            log.write_bytes(b"")
            ep = apprun.start_app(sspec, log)
            procs[f"{name}:{role}"] = ep
            e.update(command=sspec.command, app_pid=ep.pid, app_started=apprun.proc_started(ep.pid))
        spec = apprun.detect_run(wt, v["app_port"])
        if spec is None:
            raise ValueError(f"Pro variantu {name} nevím, jak spustit aplikaci "
                             "(viz `[preview] command` v .pflanzer/project.toml).")
        spec.env = {**_links(urls), **spec.env}
        log = Path(v["log"])
        log.write_bytes(b"")
        app = apprun.start_app(spec, log)
        procs[name] = app
        v.update(command=spec.command, app_pid=app.pid, app_started=apprun.proc_started(app.pid))
        if not _alive(v.get("proxy_pid") or 0, v.get("proxy_started", "")):
            if not apprun.port_free(v["proxy_port"], host):
                warnings.append(f"Proxy varianty {name} nežije a její port drží jiný proces.")
            else:
                px = _spawn_proxy(d / f"{slug}-{name}-proxy.log", host, v["proxy_port"],
                                  v["app_port"], name, password)
                v["proxy_pid"], v["proxy_started"] = px.pid, apprun.proc_started(px.pid)
        if v.get("tunnel_pid") and not _alive(v["tunnel_pid"], v.get("tunnel_started", "")):
            warnings.append(f"Tunel varianty {name} nežije — odkaz {v.get('tunnel_url')} "
                            "nefunguje; `preview down` a `up` otevře nový.")
        save_state(slug, state)
    failures: list[str] = []
    for name in names:
        v = state["variants"][name]
        ok, st = apprun.wait_http(f"http://127.0.0.1:{v['proxy_port']}/", timeout=timeout,
                                  proc=procs.get(name), auth=(USER, password))
        if ok:
            restarted.append(name)
        else:
            alive = _variant_running(v)
            why = ("aplikace skončila" if not alive.get("app", True)
                   else f"do {int(timeout)} s neodpověděla" + (f" (status {st})" if st else ""))
            failures.append(_fail_text(name, v, why))
    if failures:
        raise RuntimeError("\n\n".join(failures))
    return {"slug": slug, "restarted": restarted, "password": password, "user": USER,
            "warnings": warnings,
            "variants": {n: {"url": v.get("url"), "app_port": v["app_port"],
                             "proxy_port": v["proxy_port"]}
                         for n, v in state["variants"].items()}}


_ROUTE_RES = (
    re.compile(r"""\b(?:app|router|server|api)\.(?:get|post|put|all|use)\(\s*['"`](/[^'"`:*?]*)['"`]"""),
    re.compile(r"""@\w+\.(?:get|post|route|api_route)\(\s*['"](/[^'"{<:]*)['"]"""),
    re.compile(r"""\bpath\(\s*r?['"]([\w\-/]+)['"]"""),
)
_SPA_ROUTE_RES = (
    re.compile(r"""\bpath\s*:\s*['"`](/[\w\-/]*)['"`]"""),
    re.compile(r"""<Route\b[^>]*?\bpath\s*=\s*[{]?['"`](/?[\w\-/]*)['"`]"""),
)
_SPA_ROOT_RE = re.compile(r"""id\s*=\s*['"](?:root|app|__next)['"]""", re.I)
_SPA_DEPS = ("react-router", "react-router-dom", "vue-router", "@tanstack/react-router",
             "@sveltejs/kit", "vite", "react-scripts")


def is_spa(wt: Path) -> bool:
    """SPA = index.html s mount bodem (`<div id="root">`) + vite / router v package.json.

    Monorepo (npm workspaces): hledá se i v balíčcích (typicky `apps/web`)."""
    return any(_is_spa_dir(d) for d in [wt, *apprun.workspace_packages(wt)])


def _is_spa_dir(wt: Path) -> bool:
    try:
        for cand in (wt / "index.html", wt / "public" / "index.html"):
            if cand.is_file() and _SPA_ROOT_RE.search(cand.read_text(encoding="utf-8", errors="replace")):
                break
        else:
            return False
        if any((wt / f).is_file() for f in ("vite.config.ts", "vite.config.js", "vite.config.mjs")):
            return True
        pkg = json.loads((wt / "package.json").read_text(encoding="utf-8"))
        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
        return any(d in deps for d in _SPA_DEPS)
    except (OSError, ValueError, AttributeError):
        return False


_COMPONENT_DIRS = ("components", "component", "ui", "hooks", "lib", "utils", "shared",
                   "layouts")  # .tsx/.vue tady je komponenta, ne stránka
_COMPONENT_EXTS = (".tsx", ".jsx", ".vue", ".svelte")
_SKIP_PARTS = ("test", "spec", "docs/", "node_modules", ".pflanzer", "fixtures", "__tests__")


def _added_routes(wt: Path, spa: bool | None = None) -> list[str]:
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
    spa = is_spa(wt) if spa is None else spa
    for ln in diff.splitlines():
        if not ln.startswith("+") or ln.startswith("+++"):
            continue
        for rx in (_SPA_ROUTE_RES if spa else _ROUTE_RES):
            for m in rx.finditer(ln):
                r = m.group(1)
                if not r.startswith("/"):
                    r = "/" + r
                r = r.rstrip("/") or "/"
                if r == "/api" or r.startswith("/api/"):
                    continue  # API trasa není stránka, na kterou by vedl odkaz
                if r != "/" and r not in routes:
                    routes.append(r)
    if spa:  # nové .tsx/.jsx soubory jsou komponenty, ne cesty
        return routes
    names = subprocess.run(["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"],
                           cwd=wt, capture_output=True, text=True, timeout=30).stdout.split()
    for n in names:
        low = n.lower()
        if any(p in low for p in _SKIP_PARTS) or not low.endswith(
                (".html", ".ejs", ".pug", ".hbs", ".njk", ".jinja", ".jinja2", ".tsx", ".jsx",
                 ".vue", ".svelte")):
            continue
        if low.endswith(_COMPONENT_EXTS) and any(
                part in _COMPONENT_DIRS for part in Path(low).parts[:-1]):
            continue  # React/Vue komponenta (Wizard.tsx) mimo pages/routes není stránka
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
        if is_spa(wt):  # DOM vzniká až v prohlížeči, v HTML kostře odkazy nejsou
            return None
        routes = _added_routes(wt, spa=False)
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


HUB_HEALTH_URL = "http://localhost:8000/api/health"
FEEDBACK_FALLBACK = ("Feedback: `pflanzer feedback add` nebo spusťte `pflanzer hub` "
                     "a zapište ho tam.")


def hub_running() -> bool:
    """Běží na :8000 opravdu Pflanzer hub? (/api/health = {"status": "ok"} a /method/ odpovídá)"""
    st, body, _ct = apprun.http_fetch(HUB_HEALTH_URL, timeout=1.0, max_bytes=2000)
    if st != 200:
        return False
    try:
        if json.loads(body).get("status") != "ok":
            return False
    except (ValueError, AttributeError):
        return False
    return apprun.http_get(HUB_URL, timeout=1.0) in (200, 401)


def _variants_phrase(n: int) -> tuple[str, str]:
    """(„jednu variantu“ / „tři varianty“ …) pro 4. pád, („jedna varianta“ …) pro 1. pád."""
    words = {1: "jednu variantu", 2: "dvě varianty", 3: "tři varianty", 4: "čtyři varianty"}
    return words.get(n, f"{n} variant"), \
        {1: "jedna varianta"}.get(n, words.get(n, f"{n} variant"))


def share_message(res: dict[str, Any], hub: str | None) -> str:
    rows = "\n".join(f"  Varianta {n}: {v['url']}" for n, v in res["variants"].items())
    until = res.get("deadline") or "[doplňte termín]"
    count = len(res["variants"])
    acc, _nom = _variants_phrase(count)
    if count == 1:
        todo = ("projděte variantu (zabere to asi 5 minut) a napište, co fungovalo a co ne.")
    else:
        every = "obě varianty" if count == 2 else f"všechny {acc}" if count < 5 else \
            f"všech {count} variant"
        todo = (f"projděte {every} (zabere to asi {5 * count} minut) a u každé napište, "
                "co fungovalo a co ne.")
    msg = (f"Dobrý den, připravili jsme {acc} k rozhodnutí. Není to hotový produkt, "
           "zajímá nás váš dojem.\n"
           f"{rows}\n"
           f"Přihlášení: uživatel {res['user']}, heslo {res['password']}\n"
           f"Co udělat: {todo}\n"
           f"Do kdy: {until}.")
    if hub:
        msg += f"\nZpětnou vazbu zapište sem: {hub}"
    else:
        msg += f"\n{FEEDBACK_FALLBACK}"
    return msg


def _up_view(res: dict[str, Any]) -> tuple[list[str], str, str]:
    slug = res["slug"]
    lines = []
    for n, v in res["variants"].items():
        lines.append(f"Varianta {n}: {v['url']}")
        for role, r in (v.get("repos") or {}).items():
            lines.append(f"  + repo {role}: {r['url']} (interně, bez hesla)")
    lines.append(f"Přihlášení: uživatel {res['user']}, heslo {res['password']}")
    lines.extend(f"Info: {n}" for n in res.get("notes") or [])
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
    pr = sub.add_parser("restart", help="Restartuje aplikace variant (po Iterate); heslo, "
                                        "porty a tunel zůstanou")
    pr.add_argument("--slug", required=True)
    pr.add_argument("--variants", default=None, help="např. A,C (jinak všechny)")
    pr.add_argument("--json", **js)
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
        emit(res, title=f"Preview běží ({_variants_phrase(len(res['variants']))[1]})", lines=lines,
             next_step=nxt, tips=tips, warnings=res["warnings"], as_json=args.json)
    elif args.cmd == "restart":
        res = restart(slug, variants=parse_variants(args.variants))
        lines = [f"Varianta {n}: {v['url']}" for n, v in res["variants"].items()]
        lines.append(f"Heslo zůstává: uživatel {res['user']}, heslo {res['password']}")
        emit(res, title="Preview restartováno: " + ", ".join(res["restarted"]), lines=lines,
             next_step="Odkazy zástupců fungují dál; stav: "
                       f"`pflanzer preview status --slug {slug}`.",
             warnings=res["warnings"], as_json=args.json)
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
            for role, r in (v.get("repos") or {}).items():
                lines.append(f"  repo {role}: {'běží' if r['alive'] else 'NEBĚŽÍ'} "
                             f"(port {r['port']})")
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
