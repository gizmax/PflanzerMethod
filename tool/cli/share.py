"""`pflanzer share` — jeden příkaz pro sdílení Buildu s kolegy.

Spustí preview variant (`preview up`) a hub (jako `pflanzer hub`, se stejným heslem) a vypíše
JEDNU zprávu pro kolegy: jednu adresu (hub, z něhož vedou odkazy na varianty), jedno heslo
(zvlášť) a termín.

Usage:
    pflanzer share --slug S [--tunnel auto|cloudflared|none] [--password P]
                   [--deadline "pátek 17:00"] [--json]
    pflanzer share down --slug S      # zastaví preview i hub (jen naše PID, nikdy pkill)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.cli import apprun, hub, preview  # noqa: E402
from tool.cli.ux import CzechArgumentParser, die, emit  # noqa: E402

HUB_BASE_PORT = 8701
RESERVED_PORTS = {8000, 8001, 7877, 7890, 8765}


def state_path(slug: str) -> Path:
    return preview.preview_dir() / f"{slug}.share.json"


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


def pick_hub_port(host: str, start: int = HUB_BASE_PORT) -> int:
    port = start
    for _i in range(200):
        if port not in RESERVED_PORTS and hub.port_free(host, port):
            return port
        port += 1
    raise RuntimeError("Nenašel jsem volný port pro hub. Zkuste to znovu později.")


def start_hub(port: int, host: str, password: str, tunnel: str, log: Path
              ) -> tuple[subprocess.Popen[bytes], str]:
    """Spustí `hub.py` odpojeně (vlastní skupina procesů). Vrátí (proces, čas startu)."""
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(Path(hub.__file__).resolve()), "--port", str(port),
           "--host", host, "--password", password, "--tunnel", tunnel]
    with open(log, "ab") as fh:
        proc = subprocess.Popen(cmd, stdout=fh, stderr=fh, stdin=subprocess.DEVNULL,
                                start_new_session=True, env=dict(os.environ))
    return proc, apprun.proc_started(proc.pid)


def wait_public_url(timeout: float = 45.0) -> str | None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        url = preview.hub_data().get("public_url")
        if url:
            return str(url)
        time.sleep(0.5)
    return None


def share_text(hub_url: str, deadline: str | None) -> str:
    """Zpráva pro kolegy bez hesla (heslo jde zvlášť). Žádné příkazy CLI."""
    until = deadline or "[doplňte termín]"
    return ("Dobrý den, připravili jsme varianty k rozhodnutí. Není to hotový produkt, "
            "zajímá nás váš dojem.\n"
            f"Adresa: {hub_url}\n"
            "Co udělat: otevřete adresu, projděte všechny varianty a u každé napište, "
            "co fungovalo a co ne.\n"
            f"Do kdy: {until}.")


def up(slug: str, *, tunnel: str = "auto", password: str | None = None,
       deadline: str | None = None) -> dict[str, Any]:
    if password is not None and not password.strip():
        raise ValueError("Heslo nesmí být prázdné — vynechte --password a vygeneruje se.")
    old = load_state(slug)
    if old and old.get("hub_pid") and preview._alive(int(old["hub_pid"]),
                                                     old.get("hub_started", "")):
        raise ValueError(f"Sdílení projektu ‚{slug}‘ už běží. Zastavíte ho "
                         f"`pflanzer share down --slug {slug}`.")
    use_tunnel = hub.resolve_tunnel(tunnel)
    password = password or preview._gen_password()
    host = "127.0.0.1" if use_tunnel else "0.0.0.0"  # bez tunelu musí být dostupné v síti
    res = preview.up(slug, password=password, tunnel=tunnel, host=host, deadline=deadline)
    port = pick_hub_port(host)
    log = preview.preview_dir() / f"{slug}-hub.log"
    proc, started = start_hub(port, host, password, "cloudflared" if use_tunnel else "none", log)
    warnings = list(res.get("warnings") or [])
    state = {"slug": slug, "hub_pid": proc.pid, "hub_started": started, "hub_port": port,
             "host": host, "password": password, "deadline": deadline}
    save_state(slug, state)
    if not hub.wait_listening(port, proc, timeout=float(os.environ.get(
            "PFLANZER_SHARE_HUB_TIMEOUT", "120"))):
        _stop_hub(state)
        preview.down(slug)
        raise RuntimeError(f"Hub se nespustil (log: {log}). Preview jsem zastavil.")
    public = wait_public_url() if use_tunnel else None
    if use_tunnel and not public:
        warnings.append("Tunel hubu se nepodařilo spustit — adresa funguje jen na tomto počítači.")
    data = preview.hub_data()
    if public:
        hub_url = public
    elif host == "0.0.0.0":
        hub_url = str(data.get("lan_url") or f"http://{preview._lan_ip()}:{port}/method/")
    else:
        hub_url = f"http://127.0.0.1:{port}/method/"
    body = share_text(hub_url, deadline)
    return {"slug": slug, "hub_url": hub_url, "password": password, "user": res["user"],
            "deadline": deadline, "message": body, "hub_port": port,
            "variants": res["variants"], "warnings": warnings, "tunnel": bool(use_tunnel)}


def _stop_hub(state: dict[str, Any]) -> bool:
    pid = state.get("hub_pid")
    if pid and preview._alive(int(pid), state.get("hub_started", "")):
        apprun.kill_group(int(pid))
        return True
    return False


def down(slug: str) -> dict[str, Any]:
    state = load_state(slug)
    hub_stopped = _stop_hub(state) if state else False
    pv = preview.down(slug)
    try:
        state_path(slug).unlink()
    except OSError:
        pass
    return {"slug": slug, "hub_stopped": hub_stopped, "preview_stopped": pv["stopped"],
            "was_running": bool(hub_stopped or pv["was_running"])}


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    action = "up"
    if argv and argv[0] == "down":
        action = "down"
        argv = argv[1:]
    p = CzechArgumentParser(prog="pflanzer share" + (" down" if action == "down" else ""),
                            description=(__doc__ or "").split("\n")[0])
    p.add_argument("--slug", required=True)
    if action == "up":
        p.add_argument("--tunnel", choices=["auto", "cloudflared", "none"], default="auto",
                       help="auto = cloudflared, když je v PATH; none = jen síť / tento počítač")
        p.add_argument("--password", default=None, help="Heslo (jinak se vygeneruje)")
        p.add_argument("--deadline", default=None, help="Termín, např. „pátek 17:00“")
    p.add_argument("--json", action="store_true", help="Strojový JSON výstup")
    args = p.parse_args(argv)
    try:
        if action == "down":
            res = down(args.slug)
            emit(res, title="Sdílení zastaveno" if res["was_running"] else "Nic nebylo spuštěno",
                 lines=[f"Hub: {'zastaven' if res['hub_stopped'] else 'neběžel'}",
                        f"Varianty: {', '.join(res['preview_stopped']) or 'neběžely'}"],
                 as_json=args.json)
            return
        res = up(args.slug, tunnel=args.tunnel, password=args.password, deadline=args.deadline)
    except (ValueError, RuntimeError) as exc:
        die(str(exc))
        return
    quoted = "\n".join(f"> {ln}" for ln in res["message"].splitlines())
    lines = ["Zpráva pro kolegy (přeposlat):", "", quoted, "",
             f"Heslo (uživatelské jméno je libovolné): {res['password']}",
             "Heslo pošlete jiným kanálem než adresu (jiný chat, SMS, telefon).", ""]
    if not res["tunnel"]:
        lines.append("Adresa funguje jen ve stejné síti; pro kolegy mimo síť nainstalujte "
                     "cloudflared a spusťte sdílení znovu.")
    emit(res, title="Sdílení běží", lines=lines,
         next_step=f"po Asyncu `pflanzer share down --slug {res['slug']}`, "
                   f"pak `/pm feedback {res['slug']}`",
         warnings=res["warnings"], as_json=args.json)


if __name__ == "__main__":
    main()
