"""`pflanzer status [--slug S]` — kde projekt stojí a co je další krok.

Bez slugu: seznam projektů (slug, název, fáze slovy, další krok jako `/pm …`).
Se slugem: detail — fáze, jména 6 kroků cesty, varianty a větve, počet
feedbacků (otevřené critical), rozhodnutí, gate score a JEDEN doporučený krok.

Mapování `projects.status` (DB) na fáze v0.5 (ADR-0021):

| status            | fáze                          | další krok                    |
|-------------------|-------------------------------|-------------------------------|
| draft / charter   | Kickoff rozpracovaný          | /pm start                     |
| triage            | Kickoff hotový / Build běží   | /pm build                     |
| session_1         | Build hotový (Async běží)     | /pm feedback  (pak /pm decide)|
| session_2         | Iterate -> další Build kolo   | /pm build                     |
| handoff (před Ship)| Rozhodnutí: Go               | checkpoint … / /pm ship       |
| handoff (po Ship) | Ship hotový                   | /pm handoff  (PR)             |
| handoff (SHIP.md) | Handoff hotový                | /pm retro  (T+7)              |
| killed            | Ukončeno (Kill) — <datum>     | retro lesson (pak —)          |

Po Kill status nezobrazuje blokace, critical ani čekající podpisy (projekt je ukončený);
další krok je `pflanzer retro lesson --slug S --text "…"`, po zapsání poučení „—“.

Blokace mají přednost před fází: blokovaný checkpoint (kdo ho odblokuje),
otevřené critical (počet, varianta, kdo je nahlásil), AI draft čekající na
podpis člověka a chybějící podpisy před Ship. Fáze se řídí `projects.status`;
checkpointy ji jen doplňují (podpis provozu v Buildu nepřeskočí na Ship).
Po Go se blokující critical počítají jen na vítězi; critical na poražených jsou informace
bez ⚠. Další krok je vždy konkrétní příkaz se slugem. Po Ship `/pm handoff <slug>` (PR),
po handoffu / SHIP.md `/pm retro <slug>` (T+7). „Ship hotový“ se pozná podle auditu Ship
(`session_3.hardening`), ne podle skóre bran — to se plní už v Buildu.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.charter import is_ai_owner, owner_display  # noqa: E402
from tool.cli.db import transaction  # noqa: E402
from tool.cli.tier import TIER_LABELS, window_label  # noqa: E402
from tool.cli.ux import (  # noqa: E402
    CzechArgumentParser,
    die,
    emit,
    project_not_found_message,
    severity_label,
    tips_for_project,
)

PATH_STEPS = [
    ("byznys", "Byznys"), ("produkt", "Produkt"), ("design", "Design"),
    ("vyvoj", "Vývoj"), ("bezpecnost", "Bezpečnost & právo"), ("provoz", "Provoz"),
]


_DEADLINE_RE = re.compile(
    r"(?i)\bdo\s+((?:\d{1,2}\.\s?\d{1,2}\.(?:\s?\d{2,4})?)|(?:\d{4}-\d{2}-\d{2})"
    r"|(?:konce\s+\w+(?:\s+\w+)?)|(?:\d+\s+(?:dn[ůí]|týdn\w+|měsíc\w*)))")


def _override_deadline(reason: str) -> str | None:
    """Termín z důvodu přebití („do 15. 11.“, „do konce týdne“); None, když tam není."""
    m = _DEADLINE_RE.search(reason or "")
    return m.group(1).strip(" ,;") if m else None


def _phase(status: str, ship: str, feedback_count: int, critical: int,
           build_running: bool = False) -> tuple[str, str]:
    """Return (phase in words, next step). `ship` = none | failed | done | handed_off."""
    if status in ("draft", "charter"):
        return "Kickoff rozpracovaný", "/pm start"
    if status == "triage":
        return ("Build běží", "/pm build") if build_running else ("Kickoff hotový", "/pm build")
    if status == "session_1":
        if feedback_count == 0:
            return "Build hotový — čeká se na Async", "/pm feedback"
        if critical:
            return f"Async — {critical}× kritické otevřené", "/pm feedback"
        return "Async — feedback je", "/pm decide"
    if status == "session_2":
        return "Rozhodnutí: Iterate — další Build kolo", "/pm build"
    if status == "handoff":
        if ship == "handed_off":
            return "Handoff hotový", "/pm retro"
        if ship == "done":
            return "Ship hotový", "/pm handoff"
        if ship == "failed":
            return "Ship neprošel branami", "/pm ship"
        return "Rozhodnutí: Go", "/pm ship"
    if status == "killed":
        return "Kill — konec", "—"
    return status, "/pm"


def _last_build(slug: str) -> dict[str, Any]:
    """Audit posledního zápisu Buildu (`session_1.persist`) projektu; {} když žádný."""
    try:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM audit_log WHERE action = 'session_1.persist' "
                "ORDER BY id DESC").fetchall()
        return next((d for d in (json.loads(r[0]) for r in rows if r[0])
                     if d.get("slug") == slug), {})
    except Exception:  # noqa: BLE001 — advisory only
        return {}


def iterate_plan(slug: str) -> dict[str, Any] | None:
    """Po Rozhodnutí Iterate, před druhým Buildem: které varianty jdou do druhého kola a proč.

    `variants` = shortlist z Buildu (jinak všechny varianty projektu), `focus` = text z Iterate.
    None, když projekt není ve stavu „Iterate“ (status session_2).
    """
    try:
        with transaction() as conn:
            p = conn.execute("SELECT id, status FROM projects WHERE slug = ?", (slug,)).fetchone()
            if not p or p[1] != "session_2":
                return None
            names = [r[0] for r in conn.execute(
                "SELECT v.name FROM variants v JOIN sessions s ON s.id = v.session_id "
                "WHERE s.project_id = ? AND s.type = 1 ORDER BY v.name", (p[0],)).fetchall()]
            row = conn.execute(
                "SELECT notes_md FROM sessions WHERE project_id = ? AND type = 3 "
                "ORDER BY id DESC LIMIT 1", (p[0],)).fetchone()
    except Exception:  # noqa: BLE001 — advisory only
        return None
    shortlist = [n for n in _last_build(slug).get("shortlist", []) or [] if n in names]
    focus = (row[0] or "").strip() if row else ""
    return {"variants": sorted(dict.fromkeys(shortlist)) or names, "focus": focus or None}


def _variants_in_play(slug: str) -> list[str]:
    """Po Iterate: varianty druhého kola (ostatní skončily). Jinak []."""
    plan = iterate_plan(slug)
    if plan is not None:           # Iterate rozhodnuto, druhý Build ještě neběžel
        return plan["variants"]
    data = _last_build(slug)
    return [str(v) for v in data.get("variants", [])] if data.get("iterate_round") else []


def _blocked_triage(slug: str) -> list[str]:
    """Tracky plného triage ve stavu blocked (prázdné = nic neblokuje)."""
    try:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT t.track FROM triage t JOIN projects p ON p.id = t.project_id "
                "WHERE p.slug = ? AND t.status = 'blocked' ORDER BY t.track", (slug,)).fetchall()
    except Exception:  # noqa: BLE001 — advisory only
        return []
    return [r[0] for r in rows]


def _with_slug(step: str, slug: str) -> str:
    return f"{step} {slug}" if step.startswith("/pm ") and step != "/pm start" else step


def _audit_state(conn: Any, pid: int) -> dict[str, Any]:
    """Evidence z audit logu: běží worktrees? proběhl Ship (a prošel)? je hotový handoff?"""
    def latest(action: str) -> dict[str, Any] | None:
        r = conn.execute("SELECT payload_json FROM audit_log WHERE action = ? AND "
                         "target_type = 'project' AND target_id = ? ORDER BY id DESC LIMIT 1",
                         (action, pid)).fetchone()
        if not r:
            return None
        try:
            return json.loads(r[0] or "{}")
        except (ValueError, TypeError):
            return {}

    hardening = latest("session_3.hardening")
    ship = "none"
    if hardening is not None and not hardening.get("informational"):
        ok = (not hardening.get("blocked_by")
              and (hardening.get("meets_threshold") or hardening.get("threshold_override")))
        ship = "done" if ok else "failed"
    if ship == "done" and (latest("handoff.generate") is not None
                           or latest("ship.render") is not None):
        ship = "handed_off"
    lessons: list[str] = []
    for (raw,) in conn.execute(
            "SELECT payload_json FROM audit_log WHERE action = 'retro.lesson' AND "
            "target_type = 'project' AND target_id = ? ORDER BY id", (pid,)).fetchall():
        try:
            lessons.append(str(json.loads(raw or "{}").get("text") or "").strip())
        except (ValueError, TypeError, AttributeError):
            continue
    return {"build_running": latest("worktree.setup") is not None, "ship": ship,
            "triage_run": latest("triage.aggregate") is not None,
            "lesson": latest("retro.lesson") is not None,
            "retro_done": latest("retro.measure") is not None,
            "lessons": [x for x in lessons if x]}


def project_detail(slug: str) -> dict[str, Any]:
    from tool.cli.checkpoint import guidance_core, list_checkpoints
    from tool.cli.triage import load_risk_profile

    with transaction() as conn:
        p = conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not p:
            raise ValueError(project_not_found_message(slug))
        pid = int(p["id"])
        cols = p.keys()
        risk = load_risk_profile(conn, pid)
        evidence = _audit_state(conn, pid)

        sessions = conn.execute(
            "SELECT id, type, decision, decision_ts FROM sessions WHERE project_id = ? ORDER BY id",
            (pid,),
        ).fetchall()
        scols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
        winner = None
        override_reason = None
        if "winner_variant" in scols:
            wrow = conn.execute(
                "SELECT winner_variant" + (", override_critical_reason"
                                           if "override_critical_reason" in scols else ", NULL")
                + " FROM sessions WHERE project_id = ? AND type = 2 AND decision = 'go' "
                "ORDER BY id DESC LIMIT 1", (pid,)).fetchone()
            if wrow:
                winner, override_reason = wrow[0], wrow[1]
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
    try:
        ai_signers = json.loads(p["ai_signers_json"]) if (
            "ai_signers_json" in cols and p["ai_signers_json"]) else {}
    except (ValueError, TypeError):
        ai_signers = {}
    core = json.loads(p["core_json"]) if "core_json" in cols and p["core_json"] else []
    try:
        windows = json.loads(p["windows_json"]) if "windows_json" in cols and p["windows_json"] else []
    except (ValueError, TypeError):
        windows = []
    session_mode = (p["session_mode"] if "session_mode" in cols else None) or "parallel"
    tier = p["tier"] if "tier" in cols and p["tier"] else None

    decision_row = next((s for s in reversed(sessions) if s["type"] == 2), None)
    decision = decision_row["decision"] if decision_row else None
    iterate_rounds = sum(1 for s in sessions if s["type"] == 3)
    fcount = sum(sev.values())
    gate = int(p["gate_score_latest"] or 0)
    target = p["production_readiness_target"]

    # --- critical: před Go blokují všechny; po Go jen na vítězi (poražení = informace) ---
    crit_by_variant: dict[str, list[str]] = {}
    for r in crit_rows:
        crit_by_variant.setdefault(r["variant"], []).append(r["who"])
    after_go = p["status"] == "handoff"
    in_play = _variants_in_play(slug)  # po Iterate jen varianty posledního Build kola
    if after_go and winner:
        blocking_variants = [] if override_reason else [winner]
    elif in_play:
        blocking_variants = [v for v in crit_by_variant if v in in_play]
    else:
        blocking_variants = list(crit_by_variant)
    critical_total = sum(len(v) for v in crit_by_variant.values())
    critical = sum(len(crit_by_variant.get(v, [])) for v in blocking_variants)
    critical_info = {v: w for v, w in crit_by_variant.items() if v not in blocking_variants}

    phase, nxt = _phase(p["status"], evidence["ship"], fcount, critical,
                        build_running=evidence["build_running"])
    nxt = _with_slug(nxt, slug)
    if (tier == "full" and p["status"] in ("draft", "charter", "triage")
            and not evidence["build_running"] and not evidence.get("triage_run")):
        # Full stupeň jde přes roles + plný triage; rovnou Build by je přeskočil.
        phase = "Kickoff hotový — Full: čeká plný triage"
        nxt = f"/pm triage {slug}"
    if p["status"] in ("draft", "charter"):
        blocked_tracks = _blocked_triage(slug)
        if blocked_tracks:
            # Kickoff je hotový, ale plný triage (stupeň Full) blokuje Build.
            phase = "Kickoff hotový — triage blokuje: " + ", ".join(blocked_tracks)
            nxt = (f"odblokujte {', '.join(blocked_tracks)} (např. discovery: persona, JTBD, OST "
                   f"— nebo písemný opt-out Decidera) a znovu `/pm triage {slug}`")
    killed = p["status"] == "killed"
    killed_at = None
    if killed:
        kill_ts = next((d["atribuce_ts"] for d in reversed(decisions) if d["type"] == "kill"), None) \
            or next((s["decision_ts"] for s in reversed(sessions)
                     if s["decision"] == "kill" and s["decision_ts"]), None) \
            or (p["updated_at"] if "updated_at" in cols else None)
        killed_at = str(kill_ts)[:10] if kill_ts else None
        phase = "Ukončeno (Kill)" + (f" — {killed_at}" if killed_at else "")
        nxt = "—" if evidence["lesson"] else f'pflanzer retro lesson --slug {slug} --text "…"'
        crit_by_variant, critical, critical_total, blocking_variants = {}, 0, 0, []
        critical_info = {}

    # dedup variant names (po Iterate nový řádek přebíjí starý)
    seen: dict[str, dict[str, Any]] = {}
    for v in variants:
        seen[v["name"]] = {
            "name": v["name"], "builder": v["builder"],
            "score": v["preference_score"],
            "branch": v["branch"] or f"pflanzer/{slug}-{v['name']}",
        }

    # --- blokace: checkpointy, critical, AI drafty, chybějící podpisy ---------------
    cps = [] if killed else list_checkpoints(slug)
    late = p["status"] == "handoff"  # po Go, před/při Ship — dřív je to plán, ne blokace
    blockers: list[dict[str, str]] = []
    info: list[str] = []
    for c in cps:
        if c["window"] == "zadani":
            continue
        signer = c["designated"]
        cmd = (f'pflanzer checkpoint --slug {slug} {c["window"]} '
               f'--by "{signer or "<jméno>"}" --note "…"')
        if c["window"] == "design":
            if c["state"] == "blocked":
                blockers.append({
                    "kind": "blocked", "window": "design", "command": cmd,
                    "text": f"Design je BLOKOVÁNO ({c['signed_by'] or '—'})"
                            + (f": {c['note']}" if c.get("note") else "")
                            + f" — odblokuje {signer or 'PdM'}."})
            elif c["state"] == "pending":
                text = (f"Design: {c['owner']} — potvrďte před Rozhodnutím, potvrdí "
                        f"{signer or 'PdM'} (`pflanzer checkpoint … design`)")
                if risk == "production" and late:
                    blockers.append({
                        "kind": "missing_signature", "window": "design", "command": cmd,
                        "text": text + " — u production blokuje Ship."})
                else:
                    info.append(text + ("; u pilotu Ship neblokuje, u production ano."
                                        if risk != "production" else ""))
            continue
        if c["state"] == "blocked":
            reason = f": {c['note']}" if c.get("note") else ""
            blockers.append({
                "kind": "blocked", "window": c["window"], "command": cmd,
                "text": f"Checkpoint {c['label']} je BLOKOVÁNO ({c['signed_by'] or '—'})"
                        f"{reason} — odblokuje {signer or 'zástupce kroku'}: "
                        "oprav, co blokuje, a podepiš znovu."})
        elif c["state"] == "pending":
            who_signs = (f"podepíše {signer}" if signer else
                         "nikdo zatím není určen — " + guidance_core(
                             c["window"], path_owners, risk))
            blockers.append({
                "kind": "ai_draft", "window": c["window"], "command": cmd,
                "text": f"Checkpoint {c['label']}: AI draft čeká na podpis člověka — {who_signs}."})
        elif c["state"] != "ok" and late and risk != "throwaway":
            blockers.append({
                "kind": "missing_signature", "window": c["window"], "command": cmd,
                "text": f"Chybí podpis okna {c['label']}"
                        f"{' (' + signer + ')' if signer else ''} — bez něj Ship nepůjde."})
    for variant in blocking_variants:
        whos = crit_by_variant.get(variant, [])
        if not whos:
            continue
        uniq = ", ".join(dict.fromkeys(whos))
        blockers.append({
            "kind": "critical", "variant": variant, "command": f"/pm feedback {slug}",
            "text": f"{len(whos)}× {severity_label('critical').lower()} na variantě "
                    f"{variant} (nahlásil: {uniq}) — oprav, nebo Decider vědomě přebije."})
    for variant, whos in critical_info.items():
        uniq = ", ".join(dict.fromkeys(whos))
        if after_go and winner and variant == winner and override_reason:
            due = _override_deadline(override_reason)
            info.append(f"Kritické na vítězi {variant} přebil Decider (důvod: "
                        f"{_short(str(override_reason), 80)}; {len(whos)}×, nahlásil: {uniq})"
                        + (f" — dořešte do {due}." if due else " — dořešte po nasazení."))
            continue
        where = (f"poražené variantě {variant}" if after_go
                 else f"variantě {variant}, která po Iterate skončila")
        info.append(f"Kritické na {where} ({len(whos)}×, nahlásil: {uniq}) "
                    "neblokuje — zapište do parking lotu nebo vědomě zavřete.")

    def _pending_sig() -> dict[str, str] | None:
        return next((b for b in blockers if b["kind"] in ("ai_draft", "missing_signature")), None)

    if not killed:
        first = next((b for b in blockers if b["kind"] == "blocked"), None)
        crit_b = next((b for b in blockers if b["kind"] == "critical"), None)
        if first:
            nxt = first["command"].replace("…", "co je opraveno")
        elif crit_b and p["status"] != "session_2":  # při Iterate critical opraví Build kolo
            nxt = crit_b["command"]
        elif p["status"] == "handoff" and evidence["ship"] in ("none", "failed"):
            pend = _pending_sig()
            if pend:
                nxt = pend["command"].replace("…", "co jsem ověřil")

    return {
        "slug": slug, "name": p["name"], "status": p["status"], "phase": phase,
        "tier": tier, "risk_profile": risk,
        "next_step": nxt, "decider": p["decider_name"],
        "path_owners": {k: path_owners.get(k) for k, _ in PATH_STEPS},
        "ai_stand_ins": [k for k, _ in PATH_STEPS if is_ai_owner(path_owners.get(k))],
        "ai_signers": {k: ai_signers[k] for k, _ in PATH_STEPS
                       if is_ai_owner(path_owners.get(k)) and ai_signers.get(k)},
        "core": core, "windows": windows, "session_mode": session_mode,
        "variants": list(seen.values()),
        "winner": winner,
        "feedback": {"total": fcount, "critical": critical, "critical_total": critical_total,
                     "critical_informational": {v: len(w) for v, w in critical_info.items()},
                     "by_severity": sev},
        "checkpoints": cps, "blockers": blockers, "info": info,
        "ship_state": evidence["ship"], "killed_at": killed_at,
        "lesson_recorded": evidence["lesson"], "retro_done": evidence["retro_done"],
        "lessons": evidence["lessons"],
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


def _short(name: str, max_len: int = 50) -> str:
    """Projektový název na hranici slova (ne uprostřed)."""
    if len(name) <= max_len:
        return name
    cut = name[:max_len].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return (cut or name[:max_len]) + "…"


def tier_label(tier: str | None) -> str:
    if not tier:
        return "—"
    return f"{TIER_LABELS[tier]} (okno {window_label(tier)})" if tier in TIER_LABELS else tier


def _tip_plan(d: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Which tip phases fit the project right now (ordered, most specific first)."""
    kinds = {b["kind"] for b in d["blockers"]}
    ctx = {"blocked": "blocked" in kinds, "ai_pending": "ai_draft" in kinds,
           "open_critical": "critical" in kinds,
           "missing_signatures": "missing_signature" in kinds or "ai_draft" in kinds,
           "ai_design": "design" in d["ai_stand_ins"]}
    status, ship = d["status"], d["ship_state"]
    if status == "killed":
        return [("after_kill", ctx)]
    plan: list[tuple[str, dict[str, Any]]] = [("status", ctx)]
    if status == "handoff":
        plan.append(("after_ship" if ship in ("done", "handed_off") else "after_go", ctx))
        plan.append(("handoff" if ship == "handed_off" else "ship", ctx))
    elif status == "session_1" and "critical" in kinds:
        plan.append(("after_critical", ctx))
    else:
        key = {"charter": "kickoff", "draft": "kickoff", "triage": "build",
               "session_1": "async", "session_2": "iterate"}.get(status)
        if key:
            plan.append((key, ctx))
    return plan


def _tips(d: dict[str, Any], limit: int = 3) -> list[str]:
    """Human tips, never repeating one already shown for this project."""
    out: list[str] = []
    for phase, ctx in _tip_plan(d):
        if len(out) >= limit:
            break
        out += tips_for_project(d["slug"], phase, ctx, limit=min(2, limit - len(out)))
    return out[:limit]


def detail_lines(d: dict[str, Any]) -> list[str]:
    owners = d["path_owners"]
    lines = [f"Fáze: **{d['phase']}** · stupeň {tier_label(d['tier'])}",
             f"Decider: {d['decider'] or '—'}" + (f" · jádro: {', '.join(d['core'])}" if d["core"] else "")]
    signers = d.get("ai_signers") or {}
    steps = [f"{label} {owner_display(owners.get(key), key) or '— BEZ JMÉNA —'}"
             + (f" — AI draft, podepíše {signers[key]}" if signers.get(key) else "")
             for key, label in PATH_STEPS]
    lines.append("Kroky cesty: " + " · ".join(steps))
    if d.get("windows"):
        lines.append("Okna: " + " · ".join(
            f"{w['okno']}" + (f" {w['kdy']}" if w.get("kdy") else "") for w in d["windows"]))
    if d["variants"]:
        mob = d.get("session_mode") == "mob" or [v["name"] for v in d["variants"]] == ["mob"]
        lines.append(("Varianta (mob mode, jedna společná): " if mob else "Varianty: ")
                     + ", ".join(
            f"{v['name']}" + (f" ({v['score']:.2f})" if v["score"] is not None else "")
            for v in d["variants"]))
    elif d.get("session_mode") == "mob":
        lines.append("Režim: mob (jedna společná varianta)")
    fb = d["feedback"]
    dec = f" · rozhodnutí: **{d['decision']}**" if d["decision"] else ""
    win = f" · vítěz: **{d['winner']}**" if d.get("winner") else ""
    if d["status"] == "killed":
        lines.append(f"Feedback: {fb['total']}{dec}")
        lessons = d.get("lessons") or []
        if lessons:
            lines.append(f"Poučení ({len(lessons)}): {_short(lessons[0], 80)}")
        else:
            lines.append("Poučení: " + ("zapsáno" if d.get("lesson_recorded") else "zatím nezapsáno"))
        return lines
    lines.append(f"Feedback: {fb['total']} (kritické otevřené: {fb['critical']}){dec}{win}")
    cps = [c for c in d["checkpoints"] if c["window"] != "zadani"]
    lines.append("Podpisy: " + " · ".join(f"{c['label']} — {c['state_text']}" for c in cps))
    lines += d.get("info", [])
    if d["gate_score"] is not None:
        tgt = f" / práh {d['gate_target']}" if d["gate_target"] is not None else ""
        lines.append(f"Ship skóre: **{d['gate_score']}/100**{tgt}")
    return lines


def ai_notes(d: dict[str, Any]) -> list[str]:
    """Jedna věta za každý krok s AI náhradou, který potřebuje člověka (bez opakování blokací)."""
    from tool.cli.checkpoint import WINDOWS, guidance_core

    if d["status"] == "killed":
        return []
    owners = d["path_owners"]
    by_window = {c["window"]: c for c in d["checkpoints"]}
    notes: list[str] = []
    for key, label in PATH_STEPS:
        if not is_ai_owner(owners.get(key)) or key == "design":
            continue      # design řeší řádek „Design: AI … potvrdí …“ ve výpisu
        win = key if key in WINDOWS else None
        who = owner_display(owners.get(key), key)
        cp = by_window.get(win or "")
        if cp and cp["state"] == "ok":
            continue
        if key == "produkt":
            notes.append(f"{label}: {who} — scope drží Decider ({d['decider'] or 'Decider'}).")
        elif cp and cp["state"] == "čeká" and d["risk_profile"] == "throwaway":
            notes.append(f"{label}: {who} — u throwaway stačí AI pre-check "
                         f"(`pflanzer checkpoint --slug {d['slug']} {win} --ai --note \"…\"`).")
        elif cp and cp["state"] == "čeká":
            signer = cp["designated"]
            notes.append(f"{label}: {who} — čeká na podpis: "
                         + (signer if signer else
                            "určete kdo (" + guidance_core(win or key, owners, d["risk_profile"]) + ")"))
    return notes


def main(argv: list[str] | None = None) -> None:
    p = CzechArgumentParser(prog="pflanzer status", description=__doc__.split("\n")[0])
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
    if not args.slug and not args.json and len(data) == 1:
        data = data[0]             # jediný projekt: rovnou detail
        args.slug = data["slug"]
    if args.slug:
        d = data
        notes = ai_notes(d)
        # U throwaway je AI pre-check platný — informace, ne varování (ADR-0023).
        info_notes = [n for n in notes if "u throwaway stačí" in n]
        warnings = [b["text"] for b in d["blockers"]] + [n for n in notes if n not in info_notes]
        if d["next_step"] != "—":
            ns = d["next_step"]
            nxt = f"`{ns}`" if ns.startswith(("/pm", "pflanzer ")) else ns
        elif d["status"] == "killed":
            nxt = "— (projekt skončil Killem, poučení je zapsáno)"
        else:
            nxt = "—"
        emit(d, title=f"{d['name']} (`{d['slug']}`)", lines=detail_lines(d) + info_notes,
             next_step=nxt,
             tips=[] if args.json else _tips(d), warnings=warnings, as_json=args.json)
        return
    lines = []
    open_proj = next((r for r in data if r["next_step"] != "—"
                      and r.get("status") != "killed" and not r.get("retro_done")), None)
    for r in data:
        blocked = next((b for b in r["blockers"] if b["kind"] == "blocked"), None)
        flag = f" · ⚠ {blocked['text'].split(' — ')[0]}" if blocked else ""
        step = f"`{r['next_step']}`" if r["next_step"] != "—" else "—"
        lines.append(f"`{r['slug']}` — {_short(r['name'])} · {r['phase']}{flag} → {step}")
    emit(data, title="Projekty" if data else "Zatím žádný projekt", lines=lines,
         next_step=(f"`{open_proj['next_step']}`" if open_proj else
                    "Žádný rozpracovaný projekt — nový přes /pm start"),
         tips=[], as_json=args.json)


if __name__ == "__main__":
    main()
