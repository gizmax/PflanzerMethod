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
| handoff (gate>0)  | Ship hotový                   | /pm handoff                   |
| killed            | Kill — konec                  | —                             |
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import transaction  # noqa: E402

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

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
            return "Ship hotový", "/pm handoff"
        return "Rozhodnutí: Go", "/pm ship"
    if status == "killed":
        return "Kill — konec", "—"
    return status, "/pm"


def project_detail(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        p = conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not p:
            raise ValueError(f"Projekt '{slug}' neexistuje (zkus `pflanzer status`).")
        pid = int(p["id"])
        cols = p.keys()

        sessions = conn.execute(
            "SELECT id, type, decision, decision_ts FROM sessions WHERE project_id = ? ORDER BY id",
            (pid,),
        ).fetchall()
        sess_ids = [int(s["id"]) for s in sessions]
        vcols = {r[1] for r in conn.execute("PRAGMA table_info(variants)").fetchall()}
        branch_sel = "v.branch" if "branch" in vcols else "NULL"
        variants = conn.execute(
            f"SELECT v.id, v.name, v.builder, v.preference_score, {branch_sel} AS branch "
            "FROM variants v JOIN sessions s ON s.id = v.session_id "
            "WHERE s.project_id = ? ORDER BY v.name, v.id", (pid,),
        ).fetchall()
        fcols = {r[1] for r in conn.execute("PRAGMA table_info(feedback)").fetchall()}
        # critical je "otevřené", dokud není označené jako vyřešené (sloupec je additivní)
        open_only = " AND f.resolved_at IS NULL" if "resolved_at" in fcols else ""
        fb = conn.execute(
            "SELECT f.severity, COUNT(*) AS n FROM feedback f "
            "JOIN variants v ON v.id = f.variant_id JOIN sessions s ON s.id = v.session_id "
            "WHERE s.project_id = ?" + open_only.replace("f.resolved_at IS NULL",
            "(f.severity != 'critical' OR f.resolved_at IS NULL)") + " GROUP BY f.severity", (pid,),
        ).fetchall()
        sev = {r["severity"]: int(r["n"]) for r in fb}
        decisions = conn.execute(
            "SELECT type, atribuce_user, atribuce_ts FROM decisions WHERE project_id = ? "
            "AND type IN ('kill','handoff','preference','conflict','escalation') ORDER BY id",
            (pid,),
        ).fetchall()

    path_owners: dict[str, str] = {}
    if "path_owners_json" in cols and p["path_owners_json"]:
        path_owners = json.loads(p["path_owners_json"])
    core = json.loads(p["core_json"]) if "core_json" in cols and p["core_json"] else []

    decision_row = next((s for s in reversed(sessions) if s["type"] == 2), None)
    decision = decision_row["decision"] if decision_row else None
    iterate_rounds = sum(1 for s in sessions if s["type"] == 3)
    fcount = sum(sev.values())
    critical = sev.get("critical", 0)
    gate = int(p["gate_score_latest"] or 0)
    target = p["production_readiness_target"]
    phase, nxt = _phase(p["status"], gate, decision, fcount, critical)

    # dedup variant names (po Iterate nový řádek přebíjí starý)
    seen: dict[str, dict[str, Any]] = {}
    for v in variants:
        seen[v["name"]] = {
            "name": v["name"], "builder": v["builder"],
            "score": v["preference_score"],
            "branch": v["branch"] or f"pflanzer/{slug}-{v['name']}",
        }

    return {
        "slug": slug, "name": p["name"], "status": p["status"], "phase": phase,
        "next_step": nxt, "decider": p["decider_name"],
        "path_owners": {k: path_owners.get(k) for k, _ in PATH_STEPS},
        "core": core,
        "variants": list(seen.values()),
        "feedback": {"total": fcount, "critical": critical, "by_severity": sev},
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


def render_list(rows: list[dict[str, Any]]) -> str:
    out = [BRAND_LINE, ""]
    if not rows:
        out.append("Zatím žádný projekt. Začni Kickoffem: `/pm start`")
        return "\n".join(out)
    out += ["| Slug | Název | Fáze | Další krok |", "|------|-------|------|------------|"]
    for r in rows:
        name = r["name"] if len(r["name"]) <= 40 else r["name"][:37] + "…"
        out.append(f"| `{r['slug']}` | {name} | {r['phase']} | `{r['next_step']}` |")
    out += ["", "Detail: `pflanzer status --slug <slug>`"]
    return "\n".join(out)


def render_detail(d: dict[str, Any]) -> str:
    out = [BRAND_LINE, "", f"# {d['name']}  (`{d['slug']}`)", "",
           f"- **Fáze**: {d['phase']}  (DB status `{d['status']}`)",
           f"- **Decider**: {d['decider'] or '—'}"]
    if d["core"]:
        out.append(f"- **Jádro**: {', '.join(d['core'])}")
    if d["target_repo_url"]:
        out.append(f"- **Target repo**: {d['target_repo_url']}")
    out += ["", "## Kroky cesty", ""]
    missing = 0
    for key, label in PATH_STEPS:
        name = d["path_owners"].get(key)
        if not name:
            missing += 1
        out.append(f"- {label}: {name or '**— BEZ JMÉNA —**'}")
    if missing:
        out.append(f"\n⚠ {missing} kroků bez jména (ADR-0021: žádný krok bez zástupce).")
    out += ["", "## Varianty", ""]
    if d["variants"]:
        for v in d["variants"]:
            sc = f", skóre {v['score']:.2f}" if v["score"] is not None else ""
            out.append(f"- {v['name']} — `{v['branch']}` ({v['builder']}{sc})")
    else:
        out.append("- zatím nezapsané (po Buildu: `/pm build`)")
    fb = d["feedback"]
    out += ["", "## Feedback a rozhodnutí", "",
            f"- Feedback: {fb['total']} (critical: {fb['critical']})"]
    if d["decision"]:
        it = f", Iterate kol: {d['iterate_rounds']}" if d["iterate_rounds"] else ""
        out.append(f"- Rozhodnutí: **{d['decision']}**{it}")
    else:
        out.append("- Rozhodnutí: zatím ne")
    if d["gate_score"] is not None:
        tgt = f" / práh {d['gate_target']}" if d["gate_target"] is not None else ""
        out.append(f"- Gate score: **{d['gate_score']}/100**{tgt}")
    else:
        out.append("- Gate score: zatím ne (počítá se při Ship)")
    out += ["", f"**Další krok: `{d['next_step']}`**"]
    return "\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(prog="pflanzer status", description=__doc__.split("\n")[0])
    p.add_argument("--slug", help="Detail jednoho projektu (default: seznam všech)")
    p.add_argument("--json", action="store_true", help="Strojový výstup")
    args = p.parse_args()
    try:
        data: Any = project_detail(args.slug) if args.slug else list_projects()
    except ValueError as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:  # DB nemigrovaná apod.
        if "no such table" in str(e):
            print("CHYBA: databáze není inicializovaná — spusť `pflanzer update` "
                  "(migrace) nebo `python3 tool/db/migrate.py`.", file=sys.stderr)
            sys.exit(2)
        raise
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    elif args.slug:
        print(render_detail(data))
    else:
        print(render_list(data))


if __name__ == "__main__":
    main()
