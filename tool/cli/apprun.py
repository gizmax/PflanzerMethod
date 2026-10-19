"""Spuštění aplikace z worktree varianty — sdílí `preview` a brána `smoke`.

Pořadí zjištění příkazu:
1. `.pflanzer/project.toml` → `[preview] command = "… {port} …"` (shell, env PORT)
2. Node: `npm run dev` / `npm start` (env PORT; u Vite se přidá `--port`)
3. Python: Makefile cíl `run` (env PORT), `python -m uvicorn modul:app`, nebo
   `python -m <balíček>` s `__main__.py` (env PORT).
Interpreter: `PFLANZER_PYTHON` > `.venv/bin/python` / `venv/bin/python` > `python3`.

Jen stdlib. Žádný příkaz nenašel = `detect_run` vrací None (volající řekne lidsky,
že chybí `[preview] command`).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

APP_HOST = "127.0.0.1"


@dataclass
class RunSpec:
    command: str                    # lidsky čitelný příkaz (s dosazeným portem)
    argv: list[str] | str           # str = shell
    env: dict[str, str] = field(default_factory=dict)
    cwd: Path = field(default_factory=Path)
    source: str = ""                # odkud se příkaz vzal (project.toml / package.json / …)

    @property
    def shell(self) -> bool:
        return isinstance(self.argv, str)


PREVIEW_ENV = {"PFLANZER_PREVIEW": "1", "FEATURE_FLAGS": "all"}


def read_preview_config(wt: Path, role: str | None = None) -> dict[str, Any]:
    """Sekce `[preview]` z `.pflanzer/project.toml` (prázdná, když chybí / nejde přečíst).

    S `role` vrací per-repo blok `[preview.<role>]` (multi-repo projekt)."""
    path = Path(wt) / ".pflanzer" / "project.toml"
    if not path.is_file():
        return {}
    try:
        import tomllib
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — chybný TOML nesmí shodit preview, jen se ignoruje
        return {}
    sec = data.get("preview")
    if not isinstance(sec, dict):
        return {}
    if role:
        sub = sec.get(role)
        return sub if isinstance(sub, dict) else {}
    return sec


def python_for(wt: Path) -> str:
    env = os.environ.get("PFLANZER_PYTHON")
    if env:
        return env
    for d in (".venv", "venv"):
        cand = Path(wt) / d / "bin" / "python"
        if cand.is_file():
            return str(cand)
    return "python3"


def _has_make_target(wt: Path, target: str) -> bool:
    pat = re.compile(rf"^{re.escape(target)}\s*:(?!=)", re.MULTILINE)
    for name in ("Makefile", "makefile", "GNUmakefile"):
        f = wt / name
        if f.is_file():
            try:
                return bool(pat.search(f.read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                return False
    return False


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def workspace_packages(wt: Path) -> list[Path]:
    """Adresáře workspace balíčků (npm/yarn `workspaces`: pole nebo `{packages: […]}`).

    Podporuje globy (`apps/*`, `packages/**` se bere jako `packages/*`); bere jen adresáře
    s `package.json`, negace (`!x`) vynechá. Bez workspaces = []."""
    try:
        data = json.loads((Path(wt) / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    ws = data.get("workspaces") if isinstance(data, dict) else None
    if isinstance(ws, dict):
        ws = ws.get("packages")
    if not isinstance(ws, list):
        return []
    def norm(x: str) -> str:
        return x.strip().rstrip("/").replace("/**", "/*")

    excluded = {d for pat in ws if isinstance(pat, str) and pat.startswith("!")
                for d in Path(wt).glob(norm(pat[1:])) if not norm(pat[1:]).startswith(("/", ".."))}
    out: list[Path] = []
    for pat in ws:
        if not isinstance(pat, str) or pat.startswith("!"):
            continue
        pat = norm(pat)
        if not pat or pat.startswith(("/", "..")):
            continue
        for d in sorted(Path(wt).glob(pat)):
            if d in excluded:
                continue
            if d.is_dir() and (d / "package.json").is_file() and "node_modules" not in d.parts \
                    and d not in out:
                out.append(d)
    return out


def api_port_for(port: int, idx: int = 1) -> int:
    """Port API části (placeholder `{api_port}`): port + 1000 + idx — stejné schéma jako
    sekundární repa multi-repo preview, takže varianty (porty po 10) nikdy nesdílí API port."""
    p = port + 1000 + idx
    return p if p <= 65535 else max(1024, port - 1000 - idx)


def _detect_node(wt: Path, port: int) -> RunSpec | None:
    pkg = wt / "package.json"
    if not pkg.is_file():
        return None
    try:
        scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts") or {}
    except (OSError, ValueError):
        return None
    for name, argv in (("dev", ["npm", "run", "dev"]), ("start", ["npm", "start"])):
        if name not in scripts:
            continue
        argv = list(argv)
        if re.search(r"\bvite\b", str(scripts[name])):
            argv += ["--", "--port", str(port), "--strictPort", "--host", APP_HOST]
        env = {"PORT": str(port), "HOST": APP_HOST}
        if workspace_packages(wt):  # monorepo: dev skript (concurrently / -w) dostane i API port
            env["API_PORT"] = env["PFLANZER_API_PORT"] = str(api_port_for(port))
        return RunSpec(" ".join(argv), argv, env, wt, f"package.json ({name})")
    return None


def _detect_python(wt: Path, port: int) -> RunSpec | None:
    env = {"PORT": str(port)}
    if _has_make_target(wt, "run") and shutil.which("make"):
        return RunSpec("make run", ["make", "run"], env, wt, "Makefile (run)")
    declared = " ".join(_read(wt / f) for f in ("pyproject.toml", "requirements.txt"))
    py = python_for(wt)
    if "uvicorn" in declared:
        for mod, rel in (("main", "main.py"), ("app", "app.py"), ("app.main", "app/main.py"),
                         ("src.main", "src/main.py")):
            if re.search(r"^app\s*=", _read(wt / rel), re.MULTILINE):
                argv = [py, "-m", "uvicorn", f"{mod}:app", "--host", APP_HOST,
                        "--port", str(port)]
                return RunSpec(" ".join(argv), argv, env, wt, f"uvicorn {mod}:app")
    pkg_dirs = [p for p in [*wt.glob("*/"), *wt.glob("src/*/")]
                if (p / "__main__.py").is_file() and not p.name.startswith((".", "_", "test"))]
    if pkg_dirs:
        pkg = sorted(pkg_dirs)[0]
        argv = [py, "-m", pkg.name]
        e = dict(env)
        if pkg.parent.name == "src":
            e["PYTHONPATH"] = str(wt / "src")
        return RunSpec(" ".join(argv), argv, e, wt, f"python -m {pkg.name}")
    return None


def detect_run(wt: Path, port: int, role: str | None = None,
               config_wt: Path | None = None, api_port: int | None = None) -> RunSpec | None:
    """Příkaz ke spuštění aplikace ve worktree na daném portu; None = nenašel se.

    `role` (multi-repo, sekundární repo): hledá se `[preview.<role>] command` v project.toml
    primárního repa (`config_wt`) a pak v samotném repu (`[preview.<role>]`, `[preview]`);
    jinak autodetekce podle obsahu repa (Node / Python).

    V `command` se `{port}` nahradí portem aplikace a `{api_port}` portem API části monorepa
    (`api_port`, jinak port+1001); oba jdou i do env (`PORT`, `API_PORT`)."""
    wt = Path(wt)
    aport = api_port or api_port_for(port)
    cands: list[tuple[dict[str, Any], str]] = []
    if role:
        if config_wt is not None:
            cands.append((read_preview_config(config_wt, role),
                          f".pflanzer/project.toml [preview.{role}]"))
        cands.append((read_preview_config(wt, role), f".pflanzer/project.toml [preview.{role}]"))
    cands.append((read_preview_config(wt), ".pflanzer/project.toml [preview]"))
    for cfg, src in cands:
        cmd = cfg.get("command")
        if isinstance(cmd, str) and cmd.strip():
            full = cmd.replace("{port}", str(port)).replace("{api_port}", str(aport))
            env = {"PORT": str(port)}
            if "{api_port}" in cmd:
                env["API_PORT"] = env["PFLANZER_API_PORT"] = str(aport)
            return RunSpec(full, full, env, wt, src)
    return _detect_node(wt, port) or _detect_python(wt, port)


# --------------------------------------------------------------------------
# Procesy a HTTP
# --------------------------------------------------------------------------


def port_free(port: int, host: str = APP_HOST) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except OSError:
            return False
    return True


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((APP_HOST, 0))
        return int(s.getsockname()[1])


def start_app(spec: RunSpec, log_path: Path) -> subprocess.Popen:
    """Spustí aplikaci na pozadí (vlastní process group, výstup do logu)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # Vlajky jsou v preview / Buildu vždy zapnuté (viz INTEGRATION_GUIDE), jinak varianta
    # ukáže stránku bez nové funkce. spec.env (např. PORT) má přednost.
    env = {**os.environ, **PREVIEW_ENV, **spec.env}
    with open(log_path, "ab") as log:
        return subprocess.Popen(
            spec.argv, shell=spec.shell, cwd=str(spec.cwd), env=env,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True)


def http_get(url: str, *, auth: tuple[str, str] | None = None,
             timeout: float = 3.0) -> int | None:
    """HTTP status GET `url` bez následování redirectů; None = nikdo neodpovídá."""
    import base64

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a: Any, **k: Any) -> None:  # noqa: D401
            return None

    req = urllib.request.Request(url)
    if auth:
        tok = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {tok}")
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as r:
            return int(r.status)
    except urllib.error.HTTPError as e:
        return int(e.code)
    except (urllib.error.URLError, OSError, ValueError):
        return None


def http_fetch(url: str, *, timeout: float = 10.0, max_bytes: int = 1_000_000,
               ) -> tuple[int | None, str, str]:
    """GET bez následování redirectů: (status, tělo jako text, content-type); None = nic."""
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a: Any, **k: Any) -> None:  # noqa: D401
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(urllib.request.Request(url), timeout=timeout) as r:
            return int(r.status), r.read(max_bytes).decode("utf-8", "replace"), \
                r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        try:
            body = e.read(max_bytes).decode("utf-8", "replace")
        except OSError:
            body = ""
        return int(e.code), body, e.headers.get("Content-Type", "") if e.headers else ""
    except (urllib.error.URLError, OSError, ValueError):
        return None, "", ""


def wait_http(url: str, *, timeout: float, proc: subprocess.Popen | None = None,
              auth: tuple[str, str] | None = None, ok: Any = lambda s: s < 500,
              ) -> tuple[bool, int | None]:
    """Čeká, až `url` odpoví a `ok(status)`; končí dřív, když proces `proc` umřel."""
    deadline = time.monotonic() + timeout
    status: int | None = None
    while time.monotonic() < deadline:
        status = http_get(url, auth=auth, timeout=2.0)
        if status is not None and ok(status):
            return True, status
        if proc is not None and proc.poll() is not None:
            return False, status
        time.sleep(0.3)
    return False, status


def kill_group(pid: int, grace: float = 3.0) -> None:
    """SIGTERM celé skupině procesu, po `grace` s SIGKILL; a sklidí zombie dítě."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pid, sig)
        except (ProcessLookupError, PermissionError):
            break
        end = time.monotonic() + (grace if sig == signal.SIGTERM else 1.0)
        while time.monotonic() < end:
            try:
                done, _ = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                done = 0
                if not proc_alive(pid):
                    return
            else:
                if done:
                    return
            if not proc_alive(pid):
                return
            time.sleep(0.1)


def proc_alive(pid: int) -> bool:
    """Žije proces (zombie se nepočítá)?"""
    try:
        res = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True,
                             text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    stat = res.stdout.strip()
    return bool(stat) and not stat.startswith("Z")


def proc_started(pid: int) -> str:
    """Čas startu procesu (ochrana proti recyklovanému PID); prázdné = neběží."""
    try:
        res = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True,
                             text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return res.stdout.strip()


def tail(path: Path, lines: int = 12) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(text.rstrip().splitlines()[-lines:])
