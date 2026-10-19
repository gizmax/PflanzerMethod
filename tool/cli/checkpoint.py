"""`pflanzer checkpoint` — zapíše výsledek okna zástupce kroku cesty (ADR-0021).

v0.5 nahrazuje plný 48h triage krátkými okny. Každé okno podepisuje příslušné
triage tracky, takže Ship gate (odložený triage blokuje production_ready)
projde bez paralelní byrokracie:

    zadani      → discovery          (Kickoff: problém, metrika, kill kritérium)
    bezpecnost  → security + legal   (20 min, konec Buildu nebo do 48 h)
    provoz      → platform           (20 min, před Ship)

Usage:
    pflanzer checkpoint --slug S bezpecnost --by "Lucie" --note "syntetická data, egress jen API X"
    pflanzer checkpoint --slug S provoz --by "Karel" --blocked --note "chybí monitoring"
    pflanzer checkpoint --slug S --list
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

WINDOWS: dict[str, dict[str, Any]] = {
    "zadani": {"label": "Zadání (Kickoff)", "tracks": ("discovery",)},
    "bezpecnost": {"label": "Bezpečnost & právo", "tracks": ("security", "legal")},
    "provoz": {"label": "Provoz", "tracks": ("platform",)},
}
ALIASES = {"kickoff": "zadani", "discovery": "zadani", "security": "bezpecnost",
           "legal": "bezpecnost", "pravo": "bezpecnost", "platform": "provoz",
           "ops": "provoz"}


def _window(name: str) -> str:
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in WINDOWS:
        raise ValueError(f"Neznámé okno '{name}' (zadani | bezpecnost | provoz).")
    return key


def sign(slug: str, window: str, *, by: str, note: str, blocked: bool = False) -> dict[str, Any]:
    """Sign (or block) the triage tracks covered by a checkpoint window."""
    window = _window(window)
    if not by.strip():
        raise ValueError("--by je povinné: kdo za krok cesty podepisuje.")
    if not note.strip():
        raise ValueError("--note je povinné: co se v okně ověřilo / co chybí.")
    status = "blocked" if blocked else "ok"
    label = WINDOWS[window]["label"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    artefact = (f"**Checkpoint {label}** — {'BLOKOVÁNO' if blocked else 'OK'} · "
                f"{by} · {now}\n\n{note.strip()}\n")
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(f"Projekt '{slug}' neexistuje (zkus `pflanzer status`).")
        pid = int(proj[0])
        for track in WINDOWS[window]["tracks"]:
            conn.execute(
                """
                INSERT INTO triage (project_id, track, status, artefact_md, signed_by, signed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, track) DO UPDATE SET
                  status = excluded.status, artefact_md = excluded.artefact_md,
                  signed_by = excluded.signed_by, signed_at = excluded.signed_at
                """,
                (pid, track, status, artefact, by.strip()),
            )
        audit(conn, action=f"checkpoint.{window}", target_type="project", target_id=pid,
              actor=current_actor(),
              payload={"slug": slug, "by": by, "status": status, "note": note,
                       "tracks": list(WINDOWS[window]["tracks"])})
    log = _append_decision_log(slug, label, by, status, note, now)
    return {"slug": slug, "window": window, "status": status,
            "tracks": list(WINDOWS[window]["tracks"]), "signed_by": by,
            "decision_log_repo": log,
            "next_step": ("Oprav, co checkpoint blokuje, a podepiš znovu."
                          if blocked else _next_after(window, slug))}


def _next_after(window: str, slug: str) -> str:
    return {"zadani": f"/pm build {slug}",
            "bezpecnost": f"/pm feedback {slug} (Async)",
            "provoz": f"/pm ship {slug}"}[window]


def _append_decision_log(slug: str, label: str, by: str, status: str, note: str,
                         now: str) -> str | None:
    """Append to `.pflanzer/decisions/<slug>.md` in the target repo (cwd), if present."""
    base = Path.cwd() / ".pflanzer"
    if not base.is_dir():
        return None
    path = base / "decisions" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"{BRAND_LINE}\n\n# Decision log — {slug}\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## Checkpoint — {label}\n\n- **Stav**: {status.upper()}\n"
                f"- **Podepsal**: {by} · {now}\n- **Poznámka**: {note.strip()}\n")
    return str(path.relative_to(Path.cwd()))


def list_checkpoints(slug: str) -> list[dict[str, Any]]:
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(f"Projekt '{slug}' neexistuje (zkus `pflanzer status`).")
        rows = {r[0]: r for r in conn.execute(
            "SELECT track, status, signed_by, signed_at FROM triage WHERE project_id = ?",
            (int(proj[0]),)).fetchall()}
    out = []
    for key, w in WINDOWS.items():
        tracks = [rows.get(t) for t in w["tracks"]]
        statuses = {r[1] if r else "missing" for r in tracks}
        state = ("ok" if statuses == {"ok"} else
                 "blocked" if "blocked" in statuses else "čeká")
        signer = next((r[2] for r in tracks if r and r[1] in ("ok", "blocked")), None)
        out.append({"window": key, "label": w["label"], "state": state, "signed_by": signer})
    return out


def main() -> None:
    p = argparse.ArgumentParser(prog="pflanzer checkpoint", description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("window", nargs="?", help="zadani | bezpecnost | provoz")
    p.add_argument("--by", default="", help="Kdo za krok cesty podepisuje (jméno z Kickoffu)")
    p.add_argument("--note", default="", help="Co se ověřilo / co chybí (povinné)")
    p.add_argument("--blocked", action="store_true", help="Okno neprošlo — blokuje Ship")
    p.add_argument("--list", action="store_true", help="Stav všech oken")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    try:
        if args.list or not args.window:
            rows = list_checkpoints(args.slug)
            if args.json:
                print(json.dumps(rows, ensure_ascii=False, indent=2))
                return
            print(BRAND_LINE + "\n")
            print(f"Checkpointy — {args.slug}\n")
            print("| Okno | Stav | Podepsal |\n|------|------|----------|")
            for r in rows:
                print(f"| {r['label']} | {r['state']} | {r['signed_by'] or '—'} |")
            return
        out = sign(args.slug, args.window, by=args.by, note=args.note, blocked=args.blocked)
    except ValueError as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
