"""`pflanzer hub` — spustí web hub (feedback zástupců) jedním příkazem.

Při prvním spuštění připraví venv (~/.pflanzer/hub-venv) a sestaví frontend
(pokud je k dispozici npm). Hub sdílí DB s CLI (`pflanzer db`).

Usage:
    pflanzer hub [--port 8000] [--host 127.0.0.1] [--password HESLO] [--rebuild]

Auth: na localhostu běží dev režim bez přihlášení (zástupce si vybere jméno v UI).
Při `--host 0.0.0.0` hub zapne sdílené heslo (HTTP Basic) — zadané `--password`,
nebo vygenerované a vypsané. Firemní nasazení s OIDC: PFLANZER_HUB_AUTH_MODE=oidc.
"""
from __future__ import annotations

import argparse
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.cli.db import DATA_ROOT, DB_PATH, REPO_ROOT  # noqa: E402

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"
DEPS = ["fastapi>=0.115", "uvicorn>=0.30", "sqlmodel>=0.0.22", "pydantic>=2.8"]
FRONTEND = REPO_ROOT / "tool" / "web" / "frontend"


LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


def plan_auth(host: str, password: str | None, environ: dict[str, str]
              ) -> tuple[dict[str, str], list[str]]:
    """Vrátí (env pro backend, varování česky). Čistá funkce kvůli testům.

    - explicitní PFLANZER_HUB_AUTH_MODE=oidc se nikdy nepřepisuje,
    - localhost bez nastavení -> dev režim (jinak by hub vracel 401),
    - jiný host (0.0.0.0) bez OIDC -> dev režim + sdílené heslo (zadané nebo vygenerované).
    """
    env: dict[str, str] = {}
    notes: list[str] = []
    mode = environ.get("PFLANZER_HUB_AUTH_MODE", "").strip().lower()
    password = password or environ.get("PFLANZER_HUB_PASSWORD") or None
    if mode == "oidc":
        return env, notes
    env["PFLANZER_HUB_AUTH_MODE"] = "dev"
    if host not in LOCAL_HOSTS:
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


def _venv() -> Path:
    venv = DATA_ROOT / "hub-venv"
    py = venv / "bin" / "python"
    probe = [str(py), "-c", "import fastapi, sqlmodel, uvicorn"]
    if py.exists() and subprocess.run(probe, capture_output=True).returncode == 0:
        return py
    print("[hub] připravuji venv (jednou, ~30 s)…", file=sys.stderr)
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    subprocess.run([str(py), "-m", "pip", "install", "-q", *DEPS], check=True)
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
    args = p.parse_args()

    py = _venv()
    has_ui = _frontend(args.rebuild)
    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}"
    print(BRAND_LINE)
    print()
    print(f"Hub: {url}/method/" if has_ui else f"API: {url}/api/docs")
    print(f"DB:  {DB_PATH}  (sdílená s CLI)")
    print("Zástupci tu klikají na varianty a píšou feedback; pak `/pm feedback <slug>`.")
    auth_env, notes = plan_auth(args.host, args.password, dict(os.environ))
    for note in notes:
        print(note)
    if notes:
        print()
    print("Ctrl+C ukončí.\n")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT), "PFLANZER_DB": str(DB_PATH), **auth_env}
    os.execve(str(py), [str(py), "-m", "uvicorn", "tool.web.backend.main:app",
                        "--host", args.host, "--port", str(args.port)], env)


if __name__ == "__main__":
    main()
