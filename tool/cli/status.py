"""`pflanzer status [--slug S]` — kde projekt stojí a co je další krok.

Bez slugu: seznam projektů (slug, název, fáze slovy, další krok jako `/pm …`).
Se slugem: detail — fáze, jména 6 kroků cesty, varianty a větve, počet
feedbacků (otevřené critical), rozhodnutí, gate score a JEDEN doporučený krok.

Mapování `projects.status` (DB) na fáze v0.5 (ADR-0021):

| status            | fáze                          | další krok                    |
|-------------------|-------------------------------|-------------------------------|
| draft / charter   | Kickoff rozpracovaný          | /pm start                     |
| triage            | Kickoff hotový                | /pm build                     |
| session_1         | Build hotový (Async běží)     | /pm feedback  (pak /pm decide)|
| session_2         | Iterate -> další Build kolo   | /pm build                     |
| handoff (gate=0)  | Rozhodnutí: Go                | /pm ship                      |
| handoff (gate>0)  | Ship hotový (handoff)         | /pm retro  (T+7)              |
| killed            | Kill — konec                  | —                             |

Blokace mají přednost před fází: blokovaný checkpoint (kdo ho odblokuje),
otevřené critical (počet, varianta, kdo je nahlásil), AI draft čekající na
podpis člověka a chybějící podpisy před Ship. Fáze se řídí `projects.status`;
checkpointy ji jen doplňují (podpis provozu v Buildu nepřeskočí na Ship).
Další krok je vždy konkrétní příkaz se slugem. Po Ship/handoffu: `/pm retro <slug>` (T+7).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.charter import is_ai_owner, owner_display  # noqa: E402
from tool.cli.db import transaction  # noqa: E402
from tool.cli.tier import TIER_LABELS, WINDOW_DAYS  # noqa: E402
from tool.cli.ux import die, emit, severity_label, tips_for  # noqa: E402

PATH_STEPS = [
    ("byznys", "Byznys"), ("produkt", "Produkt"), ("design", "Design"),
    ("vyvoj", "Vývoj"), ("bezpecnost", "Bezpečnost & právo"), ("provoz", "Provoz"),
]


def _phase(status: str, gate_score: int, decision: str | None,
           feedback_count: int, critical: int) -> tuple[str, str]:
    """Return (phase in words, next step)."""
    if status in ("draft", "charter"):
        return "Kickoff rozpracovaný", "/pm start"
    if status == "triage":
        return "Kickoff hotový", "/pm build"
    if status == "session_1":
        if feedback_count == 0:
            return "Build hotový — čeká se na Async", "/pm feedback"
        if critical:
            return f"Async — {critical}× critical otevřené", "/pm feedback"
        return "Async — feedback je", "/pm decide"
    if status == "session_2":
        return "Rozhodnutí: Iterate — další Build kolo", "/pm build"
    if status == "handoff":
        if gate_score and gate_score > 0:
            return "Ship hotový", "/pm retro"
        return "Rozhodnutí: Go", "/pm ship"
    if status == "killed":
        return "Kill — konec", "—"
    return status, "/pm"


def _with_slug(step: str, slug: str) -> str:
    return f"{step} {slug}" if step.startswith("/pm ") and step != "/pm start" else step


def project_detail(slug: str) -> dict[str, Any]:
    from tool.cli.checkpoint import list_checkpoints
    from tool.cli.triage import load_risk_profile

    with transaction() as conn:
        p = conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not p:
            raise ValueError(f"Projekt '{slug}' neexistuje (zkus `pflanzer status`).")
        pid = int(p["id"])
        cols = p.keys()
        risk = load_risk_profile(conn, pid)

        sessions = conn.execute(
            "SELECT id, type, decision, decision_ts FROM sessions WHERE project_id = ? ORDER BY id",
            (pid,),
        ).fetchall()
        vcols = {r[1] for r in conn.execute("PRAGMA table_info(variants)").fetchall()}
        branch_sel = "v.branch" if "branch" in vcols else "NULL"
        variants = conn.execute(
            f"SELECT v.id, v.name, v.builder, v.preference_score, {branch_sel} AS branch "
            "FROM variants v JOIN sessions s ON s.id = v.session_id "
            "WHERE s.project_id = ? ORDER BY v.name, v.id", (pid,),
        ).fetchall()
        fcols = {r[1] for r in conn.execute("PRAGMA table_info(feedback)").fetchall()}
        # critical je "otevřené", dokud není označené jako vyřešené (sloupec je additivní)
        resolved = "(f.severity != 'critical' OR f.resolved_at IS NULL)" if "resolved_at" in fcols else "1"
        fb = conn.execute(
            "SELECT f.severity, COUNT(*) AS n FROM feedback f "
            "JOIN variants v ON v.id = f.variant_id JOIN sessions s ON s.id = v.session_id "
            f"WHERE s.project_id = ? AND {resolved} GROUP BY f.severity", (pid,),
        ).fetchall()
        sev = {r["severity"]: int(r["n"]) for r in fb}
        crit_rows = conn.execute(
            "SELECT v.name AS variant, f.submitted_by AS who FROM feedback f "
            "JOIN variants v ON v.id = f.variant_id JOIN sessions s ON s.id = v.session_id "
            f"WHERE s.project_id = ? AND f.severity = 'critical' AND {resolved} "
            "ORDER BY v.name, f.id", (pid,),
        ).fetchall()
        decisions = conn.execute(
            "SELECT type, atribuce_user, atribuce_ts FROM decisions WHERE project_id = ? "
            "AND type IN ('kill','handoff','preference','conflict','escalation') ORDER BY id",
            (pid,),
        ).fetchall()

    path_owners: dict[str, str] = {}
    if "path_owners_json" in cols and p["path_owners_json"]:
        path_owners = json.loads(p["path_owners_json"])
    core = json.loads(p["core_json"]) if "core_json" in cols and p["core_json"] else []
    tier = p["tier"] if "tier" in cols and p["tier"] else None

    decision_row = next((s for s in reversed(sessions) if s["type"] == 2), None)
    decision = decision_row["decision"] if decision_row else None
    iterate_rounds = sum(1 for s in sessions if s["type"] == 3)
    fcount = sum(sev.values())
    critical = sev.get("critical", 0)
    gate = int(p["gate_score_latest"] or 0)
    target = p["production_readiness_target"]
    phase, nxt = _phase(p["status"], gate, decision, fcount, critical)
    nxt = _with_slug(nxt, slug)

    # dedup variant names (po Iterate nový řádek přebíjí starý)
    seen: dict[str, dict[str, Any]] = {}
    for v in variants:
        seen[v["name"]] = {
            "name": v["name"], "builder": v["builder"],
            "score": v["preference_score"],
            "branch": v["branch"] or f"pflanzer/{slug}-{v['name']}",
        }

    # --- blokace: checkpointy, critical, AI drafty, chybějící podpisy ---------------
    cps = list_checkpoints(slug)
    late = p["status"] in ("session_1", "session_2", "handoff")  # po Buildu, před/při Ship
    blockers: list[dict[str, str]] = []
    for c in cps:
        if c["window"] == "zadani":
            continue
        owner = c["owner"] if c["owner"] and not str(c["owner"]).startswith("AI") else None
        cmd = (f'pflanzer checkpoint --slug {slug} {c["window"]} '
               f'--by "{owner or "<jméno>"}" --note "…"')
        if c["state"] == "blocked":
            blockers.append({
                "kind": "blocked", "window": c["window"], "command": cmd,
                "text": f"Checkpoint {c['label']} je BLOKOVÁNO ({c['signed_by'] or '—'}) — "
                        f"odblokuje {owner or 'zástupce kroku'}: oprav, co blokuje, a podepiš znovu."})
        elif c["state"] == "pending":
            blockers.append({
                "kind": "ai_draft", "window": c["window"], "command": cmd,
                "text": f"Checkpoint {c['label']}: AI draft čeká na podpis člověka — "
                        f"podepíše {owner or 'člověk, kterého určí Decider'}."})
        elif c["state"] != "ok" and late and risk != "throwaway":
            blockers.append({
                "kind": "missing_signature", "window": c["window"], "command": cmd,
                "text": f"Chybí podpis okna {c['label']}"
                        f"{' (' + owner + ')' if owner else ''} — bez něj Ship nepůjde."})
    crit_by_variant: dict[str, list[str]] = {}
    for r in crit_rows:
        crit_by_variant.setdefault(r["variant"], []).append(r["who"])
    for variant, whos in crit_by_variant.items():
        uniq = ", ".join(dict.fromkeys(whos))
        blockers.append({
            "kind": "critical", "variant": variant, "command": f"/pm feedback {slug}",
            "text": f"{len(whos)}× {severity_label('critical').lower()} (critical) na variantě "
                    f"{variant} (nahlásil: {uniq}) — oprav, nebo Decider vědomě přebije."})

    if p["status"] != "killed":
        first = next((b for b in blockers if b["kind"] == "blocked"), None)
        if first:
            nxt = first["command"].replace("…", "co je opraveno")
        elif critical and (b := next((b for b in blockers if b["kind"] == "critical"), None)):
            nxt = b["command"]
        elif phase == "Rozhodnutí: Go":
            pend = next((b for b in blockers if b["kind"] in ("ai_draft", "missing_signature")), None)
            if pend:
                nxt = pend["command"].replace("…", "co jsem ověřil")

    return {
        "slug": slug, "name": p["name"], "status": p["status"], "phase": phase,
        "tier": tier, "risk_profile": risk,
        "next_step": nxt, "decider": p["decider_name"],
        "path_owners": {k: path_owners.get(k) for k, _ in PATH_STEPS},
        "ai_stand_ins": [k for k, _ in PATH_STEPS if is_ai_owner(path_owners.get(k))],
        "core": core,
        "variants": list(seen.values()),
        "feedback": {"total": fcount, "critical": critical, "by_severity": sev},
        "checkpoints": cps, "blockers": blockers,
        "decision": decision, "iterate_rounds": iterate_rounds,
        "decision_log": [dict(d) for d in decisions],
        "gate_score": gate if gate else None, "gate_target": target,
        "target_repo_url": p["target_repo_url"],
    }


def list_projects() -> list[dict[str, Any]]:
    with transaction() as conn:
        slugs = [r[0] for r in conn.execute(
            "SELECT slug FROM projects ORDER BY updated_at DESC, id DESC").fetchall()]
    return [project_detail(s) for s in slugs]


def tier_label(tier: str | None) -> str:
    if not tier:
        return "—"
    return f"{TIER_LABELS[tier]} (okno {WINDOW_DAYS[tier]} dny)" if tier in TIER_LABELS else tier


def _tips(d: dict[str, Any]) -> list[str]:
    kinds = {b["kind"] for b in d["blockers"]}
    ctx = {"blocked": "blocked" in kinds, "ai_pending": "ai_draft" in kinds,
           "open_critical": "critical" in kinds,
           "missing_signatures": "missing_signature" in kinds or "ai_draft" in kinds}
    phase_key = {"charter": "kickoff", "draft": "kickoff", "triage": "build",
                 "session_1": "async", "session_2": "iterate", "handoff": "ship"}.get(d["status"])
    tips = tips_for("status", ctx, limit=2)
    if phase_key and d["phase"] != "Ship hotový":
        tips += [t for t in tips_for(phase_key, ctx, limit=2) if t not in tips]
    elif d["phase"] == "Ship hotový":
        tips += tips_for("handoff", limit=1)
    return tips[:3]


def detail_lines(d: dict[str, Any]) -> list[str]:
    owners = d["path_owners"]
    lines = [f"Fáze: **{d['phase']}** · stupeň {tier_label(d['tier'])}",
             f"Decider: {d['decider'] or '—'}" + (f" · jádro: {', '.join(d['core'])}" if d["core"] else "")]
    steps = [f"{label} {owner_display(owners.get(key), key) or '— BEZ JMÉNA —'}"
             for key, label in PATH_STEPS]
    lines.append("Kroky cesty: " + " · ".join(steps))
    if d["variants"]:
        lines.append("Varianty: " + ", ".join(
            f"{v['name']}" + (f" ({v['score']:.2f})" if v["score"] is not None else "")
            for v in d["variants"]))
    fb = d["feedback"]
    dec = f" · rozhodnutí: **{d['decision']}**" if d["decision"] else ""
    lines.append(f"Feedback: {fb['total']} (critical otevřené: {fb['critical']}){dec}")
    cps = [c for c in d["checkpoints"] if c["window"] != "zadani"]
    from tool.cli.checkpoint import STATE_LABELS
    lines.append("Podpisy: " + " · ".join(f"{c['label']} — {STATE_LABELS[c['state']]}" for c in cps))
    if d["gate_score"] is not None:
        tgt = f" / práh {d['gate_target']}" if d["gate_target"] is not None else ""
        lines.append(f"Ship skóre: **{d['gate_score']}/100**{tgt}")
    return lines


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="pflanzer status", description=__doc__.split("\n")[0])
    p.add_argument("--slug", help="Detail jednoho projektu (default: seznam všech)")
    p.add_argument("--json", action="store_true", help="Strojový výstup")
    args = p.parse_args(argv)
    try:
        data: Any = project_detail(args.slug) if args.slug else list_projects()
    except ValueError as e:
        die(str(e))
        return
    except Exception as e:  # DB nemigrovaná apod.
        if "no such table" in str(e):
            die("databáze není inicializovaná — spusť `pflanzer update` "
                "(migrace) nebo `python3 tool/db/migrate.py`.")
            return
        raise
    if args.slug:
        d = data
        warnings = [b["text"] for b in d["blockers"]]
        if any(is_ai_owner(v) for v in d["path_owners"].values()):
            who = ", ".join(f"{label}: {owner_display(d['path_owners'][k], k)}"
                            for k, label in PATH_STEPS if is_ai_owner(d["path_owners"].get(k)))
            warnings.append(f"AI náhrada: {who} — podepisuje člověk (ADR-0023).")
        emit(d, title=f"{d['name']} (`{d['slug']}`)", lines=detail_lines(d),
             next_step=f"`{d['next_step']}`" if d["next_step"] != "—" else "projekt skončil Killem",
             tips=_tips(d), warnings=warnings, as_json=args.json)
        return
    lines = [f"`{r['slug']}` — {r['name'][:50]} · {r['phase']} → `{r['next_step']}`" for r in data]
    emit(data, title="Projekty" if data else "Zatím žádný projekt", lines=lines,
         next_step=(f"`pflanzer status --slug {data[0]['slug']}`" if data else "`/pm start`"),
         tips=[], as_json=args.json)


if __name__ == "__main__":
    main()
