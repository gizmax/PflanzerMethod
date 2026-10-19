"""`pflanzer checkpoint` — zapíše výsledek okna zástupce kroku cesty (ADR-0021).

v0.5 nahrazuje plný 48h triage krátkými okny. Každé okno podepisuje příslušné
triage tracky, takže Ship (odložený triage blokuje production_ready)
projde bez paralelní byrokracie:

    zadani      → discovery          (Kickoff: problém, metrika, kill kritérium)
    bezpecnost  → security + legal   (20 min, konec Buildu nebo do 48 h)
    provoz      → platform           (20 min, před Ship)

Usage:
    pflanzer checkpoint --slug S bezpecnost --by "Lucie" --note "syntetická data, egress jen API X"
    pflanzer checkpoint --slug S provoz --by "Karel" --blocked --note "chybí monitoring"
    pflanzer checkpoint --slug S bezpecnost --ai [--agent security-expert] --note "AI pre-check"
    pflanzer checkpoint --slug S --list

AI náhrada (ADR-0023): `--ai` zapíše DRAFT. U throwaway je okno hned ok, u pilotu
a production zůstane „čeká na podpis člověka“ (Ship blokuje) a potvrdí ho až
`--by <jméno>`. U okna provoz pilotu smí podepsat i vývojář z jádra.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.cli.charter import ai_agent, is_ai_owner, owner_display  # noqa: E402
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.ux import die, emit, tips_for  # noqa: E402

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

WINDOWS: dict[str, dict[str, Any]] = {
    "zadani": {"label": "Zadání (Kickoff)", "tracks": ("discovery",)},
    "bezpecnost": {"label": "Bezpečnost & právo", "tracks": ("security", "legal")},
    "provoz": {"label": "Provoz", "tracks": ("platform",)},
}
ALIASES = {"kickoff": "zadani", "discovery": "zadani", "security": "bezpecnost",
           "legal": "bezpecnost", "pravo": "bezpecnost", "platform": "provoz",
           "ops": "provoz"}


# Okno -> krok cesty, jehož zástupce ho podepisuje.
WINDOW_STEP = {"zadani": "byznys", "bezpecnost": "bezpecnost", "provoz": "provoz"}
AI_DRAFT_MARK = "AI draft — čeká na podpis člověka"
USAGE = ('  pflanzer checkpoint --slug <slug> bezpecnost --by "Jana" --note "co se ověřilo"\n'
         '  pflanzer checkpoint --slug <slug> provoz --ai --note "AI pre-check"')


def _window(name: str) -> str:
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in WINDOWS:
        raise ValueError(f"Neznámé okno '{name}' (zadani | bezpecnost | provoz).")
    return key


def _same_person(a: str | None, b: str | None) -> bool:
    ta = set((a or "").casefold().split())
    tb = set((b or "").casefold().split())
    return bool(ta and tb and (ta <= tb or tb <= ta))


def _load_owners(conn: Any, pid: int) -> dict[str, str]:
    row = conn.execute("SELECT path_owners_json FROM projects WHERE id = ?", (pid,)).fetchone()
    return json.loads(row[0]) if row and row[0] else {}


def sign(slug: str, window: str, *, by: str = "", note: str, blocked: bool = False,
         ai: bool = False, agent: str | None = None) -> dict[str, Any]:
    """Sign (or block) the triage tracks covered by a checkpoint window.

    `ai=True` writes an AI draft (ADR-0023): ok for throwaway, otherwise
    `pending` until a human countersigns with `by=`.
    """
    from tool.cli.triage import load_risk_profile

    window = _window(window)
    if not ai and not by.strip():
        raise ValueError("--by je povinné: kdo za krok cesty podepisuje "
                         "(nebo --ai pro AI draft).\nPříklad:\n" + USAGE)
    if not note.strip():
        raise ValueError("--note je povinné: co se v okně ověřilo / co chybí.\nPříklad:\n" + USAGE)
    if ai and window == "zadani":
        raise ValueError("Zadání (Kickoff) AI nepodepíše — podepisuje Decider. Použij --by <jméno>.")
    label = WINDOWS[window]["label"]
    step = WINDOW_STEP[window]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    warnings: list[str] = []
    countersigned = False
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(f"Projekt '{slug}' neexistuje (zkus `pflanzer status`).")
        pid = int(proj[0])
        owners = _load_owners(conn, pid)
        owner = owners.get(step)
        risk = load_risk_profile(conn, pid)
        prior = conn.execute(
            "SELECT status, signed_by FROM triage WHERE project_id = ? AND track = ?",
            (pid, WINDOWS[window]["tracks"][0])).fetchone()

        if ai:
            who = f"AI ({agent or ai_agent(owner, step)})"
            status = "blocked" if blocked else ("ok" if risk == "throwaway" else "pending")
            head = ("BLOKOVÁNO" if blocked else
                    "AI pre-check" if status == "ok" else AI_DRAFT_MARK)
            if status == "pending":
                warnings.append(f"{label}: AI draft není podpis — Ship dál blokuje, dokud ho "
                                "nepotvrdí člověk (`--by <jméno>`).")
        else:
            who = by.strip()
            status = "blocked" if blocked else "ok"
            head = "BLOKOVÁNO" if blocked else "OK"
            countersigned = bool(prior and prior[0] == "pending"
                                 and str(prior[1] or "").startswith("AI")) and not blocked
            owner_human = owner and not is_ai_owner(owner)
            allowed = bool(owner_human and _same_person(who, owner))
            if (window == "provoz" and risk == "pilot"
                    and _same_person(who, owners.get("vyvoj"))):
                allowed = True
            if owner_human and not allowed:
                warnings.append(
                    f"{who} není zástupce kroku {label} ({owner}) — podpis zapsán jako zástup.")
        artefact = f"**Checkpoint {label}** — {head} · {who} · {now}\n\n{note.strip()}\n"
        if countersigned:
            artefact += f"\n_Potvrzuje AI draft ({prior[1]})._\n"
        for track in WINDOWS[window]["tracks"]:
            conn.execute(
                """
                INSERT INTO triage (project_id, track, status, artefact_md, signed_by, signed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, track) DO UPDATE SET
                  status = excluded.status, artefact_md = excluded.artefact_md,
                  signed_by = excluded.signed_by, signed_at = excluded.signed_at
                """,
                (pid, track, status, artefact, who),
            )
        audit(conn, action=f"checkpoint.{window}", target_type="project", target_id=pid,
              actor=current_actor(),
              payload={"slug": slug, "by": who, "status": status, "note": note, "ai": ai,
                       "countersigned_ai_draft": countersigned,
                       "tracks": list(WINDOWS[window]["tracks"])})
    log = _append_decision_log(slug, label, who, status, note, now)
    next_step = _next_step(slug, window, status, owner, owners, risk, by=who)
    return {"slug": slug, "window": window, "label": label, "status": status,
            "tracks": list(WINDOWS[window]["tracks"]), "signed_by": who,
            "ai_draft": status == "pending", "ai": ai,
            "countersigned_ai_draft": countersigned,
            "decision_log_repo": log, "warnings": warnings, "next_step": next_step}


def _signer_for(window: str, owner: str | None, owners: dict[str, str], risk: str) -> str:
    if owner and not is_ai_owner(owner):
        return owner
    if window == "provoz" and risk == "pilot" and owners.get("vyvoj"):
        return owners["vyvoj"]
    decider = owners.get("byznys")      # krok bez člověka: určí Decider
    return decider if decider and not is_ai_owner(decider) else "<jméno člověka>"


def _next_step(slug: str, window: str, status: str, owner: str | None,
               owners: dict[str, str], risk: str, by: str = "") -> str:
    signer = _signer_for(window, owner, owners, risk)
    label = WINDOWS[window]["label"]
    if status == "blocked":
        return (f"{label} je zablokované — odblokuje {signer}. Až bude opraveno: "
                f'`pflanzer checkpoint --slug {slug} {window} --by "{signer}" --note "co je opraveno"`')
    if status == "pending":
        return (f"AI draft {label} musí potvrdit člověk — {signer}: "
                f'`pflanzer checkpoint --slug {slug} {window} --by "{signer}" --note "co jsem ověřil"`')
    from tool.cli.status import project_detail
    return str(project_detail(slug)["next_step"])


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


STATE_LABELS = {"ok": "podepsáno", "blocked": "BLOKOVÁNO",
                "pending": "AI draft čeká na podpis člověka", "čeká": "čeká"}


def list_checkpoints(slug: str) -> list[dict[str, Any]]:
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(f"Projekt '{slug}' neexistuje (zkus `pflanzer status`).")
        pid = int(proj[0])
        owners = _load_owners(conn, pid)
        rows = {r[0]: r for r in conn.execute(
            "SELECT track, status, signed_by, signed_at FROM triage WHERE project_id = ?",
            (pid,)).fetchall()}
    out = []
    for key, w in WINDOWS.items():
        tracks = [rows.get(t) for t in w["tracks"]]
        statuses = {r[1] if r else "missing" for r in tracks}
        state = ("ok" if statuses == {"ok"} else
                 "blocked" if "blocked" in statuses else
                 "pending" if "pending" in statuses else "čeká")
        signer = next((r[2] for r in tracks if r and r[1] in ("ok", "blocked", "pending")), None)
        owner = owners.get(WINDOW_STEP[key])
        out.append({"window": key, "label": w["label"], "state": state, "signed_by": signer,
                    "owner": owner_display(owner, WINDOW_STEP[key]) or None})
    return out


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="pflanzer checkpoint", description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("window", nargs="?", help="zadani | bezpecnost | provoz")
    p.add_argument("--by", default="", help="Kdo za krok cesty podepisuje (jméno z Kickoffu)")
    p.add_argument("--note", default="", help="Co se ověřilo / co chybí (povinné)")
    p.add_argument("--blocked", action="store_true", help="Okno neprošlo — blokuje Ship")
    p.add_argument("--ai", action="store_true",
                   help="AI draft (ADR-0023): pilot/production čeká na podpis člověka")
    p.add_argument("--agent", default=None, help="S --ai: který agent (např. security-expert)")
    p.add_argument("--list", action="store_true", help="Stav všech oken")
    p.add_argument("--json", action="store_true", help="Strojový výstup")
    args = p.parse_args(argv)
    try:
        if args.list or not args.window:
            rows = list_checkpoints(args.slug)
            lines = []
            for r in rows:
                who = f" · {r['signed_by']}" if r["signed_by"] else ""
                owner = f" (zástupce: {r['owner']})" if r["owner"] else ""
                lines.append(f"{r['label']}: **{STATE_LABELS[r['state']]}**{who}{owner}")
            open_ = next((r for r in rows if r["state"] != "ok" and r["window"] != "zadani"), None)
            nxt = (f'`pflanzer checkpoint --slug {args.slug} {open_["window"]} '
                   f'--by "{open_["owner"] or "<jméno>"}" --note "…"`' if open_
                   else f"Všechna okna jsou podepsaná — `/pm ship {args.slug}`")
            emit(rows, title=f"Checkpointy — {args.slug}", lines=lines, next_step=nxt,
                 tips=tips_for("checkpoint_provoz") if open_ and open_["window"] == "provoz"
                 else tips_for("checkpoint_bezpecnost"), as_json=args.json)
            return
        out = sign(args.slug, args.window, by=args.by, note=args.note, blocked=args.blocked,
                   ai=args.ai, agent=args.agent)
    except ValueError as e:
        die(str(e))
        return
    state = {"ok": "podepsáno", "blocked": "BLOKOVÁNO",
             "pending": AI_DRAFT_MARK}[out["status"]]
    lines = [f"{out['label']}: **{state}** · {out['signed_by']}"]
    if out["countersigned_ai_draft"]:
        lines.append("Člověk potvrdil AI draft — okno je podepsané.")
    if out["decision_log_repo"]:
        lines.append(f"Zapsáno do `{out['decision_log_repo']}`.")
    phase = ("checkpoint_provoz" if out["window"] == "provoz" else "checkpoint_bezpecnost")
    ctx = {"blocked": out["status"] == "blocked"}
    tips = (tips_for("ai_stand_in") if out["ai"] else tips_for(phase, ctx))
    emit(out, title=f"Checkpoint {out['label']} zapsán", lines=lines,
         next_step=out["next_step"], tips=tips, warnings=out["warnings"], as_json=args.json)


if __name__ == "__main__":
    main()
