"""`pflanzer hub` — spustí web hub (feedback zástupců) jedním příkazem.

Při prvním spuštění připraví venv (~/.pflanzer/hub-venv) a sestaví frontend
(pokud je k dispozici npm). Hub sdílí DB s CLI (`pflanzer db`).

Usage:
    pflanzer hub [--port 8000] [--host 127.0.0.1] [--password HESLO] [--rebuild]
                 [--tunnel auto|cloudflared|none|off]

Auth: na localhostu běží dev režim bez přihlášení (zástupce si vybere jméno v UI).
Při `--host 0.0.0.0` hub zapne sdílené heslo (HTTP Basic) — zadané `--password`,
nebo vygenerované a vypsané. `--tunnel` (stejný quick tunnel jako `preview up`) hub vystaví
i mimo síť; heslo je pak povinné. Firemní nasazení s OIDC: PFLANZER_HUB_AUTH_MODE=oidc.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.cli.db import DATA_ROOT, DB_PATH, REPO_ROOT  # noqa: E402

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"
DEPS = ["fastapi>=0.115", "uvicorn>=0.30", "sqlmodel>=0.0.22", "pydantic>=2.8"]
FRONTEND = REPO_ROOT / "tool" / "web" / "frontend"


LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


def plan_auth(host: str, password: str | None, environ: dict[str, str],
              shared: bool = False) -> tuple[dict[str, str], list[str]]:
    """Vrátí (env pro backend, varování česky). Čistá funkce kvůli testům.

    - explicitní PFLANZER_HUB_AUTH_MODE=oidc se nikdy nepřepisuje,
    - localhost bez nastavení -> dev režim (jinak by hub vracel 401),
    - jiný host (0.0.0.0) nebo `shared` (tunel) bez OIDC -> dev režim + sdílené heslo
      (zadané nebo vygenerované).
    """
    env: dict[str, str] = {}
    notes: list[str] = []
    mode = environ.get("PFLANZER_HUB_AUTH_MODE", "").strip().lower()
    password = password or environ.get("PFLANZER_HUB_PASSWORD") or None
    if mode == "oidc":
        return env, notes
    env["PFLANZER_HUB_AUTH_MODE"] = "dev"
    if host not in LOCAL_HOSTS or shared:
        generated = False
        if not password:
            password = secrets.token_urlsafe(9)
            generated = True
        notes.append(
            "POZOR: hub je dostupný ostatním v síti a nemá firemní přihlášení (OIDC). "
            "Chrání ho jen sdílené heslo — sdílejte ho jen s lidmi z týmu a jen ve firemní síti."
        )
        notes.append(("Vygenerované heslo: " if generated else "Heslo: ") + password
                     + "  (uživatelské jméno je libovolné)")
    if password:
        env["PFLANZER_HUB_PASSWORD"] = password
    return env, notes


def port_free(host: str, port: int) -> bool:
    """Dá se na host:port poslouchat? (uvicorn jinak končí syrovou chybou)"""
    bind = "127.0.0.1" if host in ("localhost",) else host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((bind, port))
        return True
    except OSError:
        return False


def find_free_port(host: str, start: int, tries: int = 50) -> int | None:
    return next((p for p in range(start + 1, start + 1 + tries) if port_free(host, p)), None)


def hub_json_path() -> Path:
    return DATA_ROOT / "hub.json"


def lan_ip() -> str:
    from tool.cli.preview import _lan_ip  # reuse z preview, žádná kopie
    return _lan_ip()


def hub_json_data(port: int, host: str = "127.0.0.1", public_url: str | None = None,
                  lan: str | None = None) -> dict[str, object]:
    """Obsah hub.json (bez hesla!): `url` = lokální, `lan_url` (host 0.0.0.0), `public_url`
    (tunel). Preview z toho vybere odkaz, který kolegové opravdu otevřou."""
    data: dict[str, object] = {"port": port, "url": f"http://127.0.0.1:{port}/method/"}
    if host not in LOCAL_HOSTS:
        data["lan_url"] = f"http://{lan or lan_ip()}:{port}/method/"
    if public_url:
        data["public_url"] = public_url.rstrip("/") + "/method/"
    return data


def write_hub_json(port: int, host: str = "127.0.0.1", public_url: str | None = None,
                   lan: str | None = None) -> None:
    try:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        hub_json_path().write_text(json.dumps(hub_json_data(port, host, public_url, lan)),
                                   encoding="utf-8")
    except OSError:
        pass


def resolve_tunnel(mode: str) -> bool:
    """auto = cloudflared, je-li v PATH; cloudflared = povinně (ValueError, chybí-li); none = ne.
    Stejná logika jako `preview up`."""
    if mode not in ("auto", "cloudflared", "none"):
        raise ValueError("--tunnel je auto, cloudflared nebo none.")
    have = shutil.which("cloudflared") is not None
    if mode == "cloudflared" and not have:
        raise ValueError("Chybí `cloudflared` v PATH. Nainstalujte ho (např. "
                         "`brew install cloudflared`), nebo použijte --tunnel none.")
    return mode == "cloudflared" or (mode == "auto" and have)


def wait_listening(port: int, proc: subprocess.Popen, timeout: float = 60.0) -> bool:
    import time
    end = time.monotonic() + timeout
    while time.monotonic() < end and proc.poll() is None:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def _venv() -> Path:
    venv = DATA_ROOT / "hub-venv"
    py = venv / "bin" / "python"
    probe = [str(py), "-c", "import fastapi, sqlmodel, uvicorn"]
    if py.exists() and subprocess.run(probe, capture_output=True).returncode == 0:
        return py
    print("[hub] připravuji venv (jednou, první spuštění stáhne závislosti)…", file=sys.stderr)
    try:
        subprocess.run([sys.executable, "-m", "venv", "--clear", str(venv)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", "--timeout", "60",
                        "--retries", "2", *DEPS], check=True)
    except (subprocess.CalledProcessError, OSError):
        shutil.rmtree(venv, ignore_errors=True)  # napůl vytvořený venv by další pokus zmátl
        print("[hub] instalace závislostí selhala (typicky síť/proxy) — napůl vytvořené "
              "prostředí jsem smazal, zkuste to znovu.", file=sys.stderr)
        raise
    return py


def _frontend(rebuild: bool) -> bool:
    dist = FRONTEND / "dist" / "index.html"
    if dist.exists() and not rebuild:
        return True
    npm = shutil.which("npm")
    if not npm:
        print("[hub] npm není v PATH — běží jen API (/api/docs).", file=sys.stderr)
        return False
    print("[hub] sestavuji frontend (jednou)…", file=sys.stderr)
    if not (FRONTEND / "node_modules").is_dir():
        subprocess.run([npm, "install", "--no-audit", "--no-fund", "--loglevel=error"],
                       cwd=FRONTEND, check=True)
    subprocess.run([npm, "run", "build"], cwd=FRONTEND, check=True)
    return dist.exists()


def main() -> None:
    p = argparse.ArgumentParser(prog="pflanzer hub", description=__doc__.split("\n")[0])
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="127.0.0.1",
                   help="0.0.0.0 = dostupné i ostatním v síti (sdílej jen ve firemní síti)")
    p.add_argument("--password", default=None,
                   help="sdílené heslo (HTTP Basic); u --host 0.0.0.0 se bez něj vygeneruje")
    p.add_argument("--rebuild", action="store_true", help="znovu sestavit frontend")
    p.add_argument("--tunnel", choices=["auto", "cloudflared", "none"], default="none",
                   type=lambda v: "none" if v == "off" else v,  # `off` = alias jako u preview
                   help="cloudflared quick tunnel (jako preview up); auto = když je v PATH; "
                        "vyžaduje heslo (vygeneruje se)")
    args = p.parse_args()
    # Výstup do roury (agent, log) je jinak bufferovaný a URL by se nevypsala včas.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    try:
        use_tunnel = resolve_tunnel(args.tunnel)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    if not port_free(args.host, args.port):
        alt = find_free_port(args.host, args.port)
        print(f"Port {args.port} je obsazený (nejspíš už běží jiný hub nebo jiná aplikace).",
              file=sys.stderr)
        if alt:
            print(f"Zkuste jiný port: `pflanzer hub --port {alt}`", file=sys.stderr)
        else:
            print("Zadejte jiný port přes `--port N`.", file=sys.stderr)
        sys.exit(2)
    py = _venv()
    has_ui = _frontend(args.rebuild)
    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}"
    print(BRAND_LINE)
    print()
    print(f"Hub: {url}/method/" if has_ui else f"API: {url}/api/docs", flush=True)
    print(f"DB:  {DB_PATH}  (sdílená s CLI)")
    print("Zástupci tu klikají na varianty a píšou feedback; pak `/pm feedback <slug>`.")
    auth_env, notes = plan_auth(args.host, args.password, dict(os.environ),
                                shared=use_tunnel)
    for note in notes:
        print(note)
    if notes:
        print()
    print("Ctrl+C ukončí.\n")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT), "PFLANZER_DB": str(DB_PATH),
           "PFLANZER_DATA": str(DATA_ROOT), "PFLANZER_HUB_BIND_HOST": args.host, **auth_env}
    # --log-level warning: uvicorn jinak vypíše holé http://127.0.0.1:PORT bez /method/ (plná
    # adresa hubu je ve výpisu výše); varování a chyby zůstanou.
    cmd = [str(py), "-m", "uvicorn", "tool.web.backend.main:app",
           "--host", args.host, "--port", str(args.port), "--log-level", "warning"]
    # hub.json: ostatní příkazy (preview) z něj poznají URL; po ukončení se smaže.
    write_hub_json(args.port, args.host)
    proc = subprocess.Popen(cmd, env=env)
    tunnel_pid: int | None = None
    if args.host not in LOCAL_HOSTS:
        print(f"Hub v síti: http://{lan_ip()}:{args.port}/method/")
    if use_tunnel:
        from tool.cli import preview
        if wait_listening(args.port, proc):
            res = preview.start_tunnel(args.port, DATA_ROOT / "preview" / "hub-tunnel.log")
            if res:
                tunnel_pid, _started, public = res
                write_hub_json(args.port, args.host, public)
                print(f"Hub přes tunel: {public}/method/  (provoz jde přes Cloudflare)")
            else:
                print("Tunel se nepodařilo spustit — hub běží jen lokálně / v síti.",
                      file=sys.stderr)

    def _stop(*_a: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _stop)
    try:
        sys.exit(proc.wait())
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    finally:
        if tunnel_pid:
            from tool.cli import apprun
            apprun.kill_group(tunnel_pid)
        try:
            hub_json_path().unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
