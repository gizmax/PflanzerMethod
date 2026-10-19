"""Async — sběr a agregace feedbacku (`/pm feedback`).

Web hub i CLI (`pflanzer feedback add`) píšou do stejné SQLite, takže
"pull" není přenos dat, ale **souhrn feedbacku + audit**:

1. Načte feedback ke všem variantám projektu (hub i offline zápisy).
2. Agreguje podle oddělení / severity / varianty.
3. Vyznačí **critical flags** (severity='critical').
4. Připraví souhrn MD pro Rozhodnutí.
5. Když feedback chybí, řekne to jasně a NEVYTVÁŘÍ prázdný souhrn.

AI-only deflace (max 0.5) se aplikuje už při zápisu (hub i `feedback add`).
"""
from __future__ import annotations

import json
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import ProjectNotFound, count, exit_if_project_missing, tips  # noqa: E402
from tool.cli.db import DATA_ROOT, audit, display_path, transaction  # noqa: E402
from tool.cli.ux import CzechArgumentParser, die, emit, severity_label  # noqa: E402

FEEDBACK_DIR = DATA_ROOT / "feedback"
BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"
NO_FEEDBACK_MSG = (
    "Zatím žádný feedback. Zástupci ho píšou v hubu, nebo ho zapiš za ně: "
    "pflanzer feedback add --slug {slug} --variant A --role \"Bezpečnost\" "
    "--severity major --text \"co je špatně\"."
)
SEVERITY_ORDER = ("critical", "high", "medium", "low")
# Kroky cesty (klíč v path_owners_json) -> zobrazený název a texty, kterými se píše oddělení.
STEP_LABELS = {"produkt": "Produkt", "design": "Design", "vyvoj": "Vývoj",
               "bezpecnost": "Bezpečnost & právo", "provoz": "Provoz"}


def _norm(text: str | None) -> str:
    text = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in text if unicodedata.category(c) != "Mn").casefold().strip()


def silent_reps(conn: Any, project_id: int, feedback: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Zástupci kroků cesty (jména z Kickoffu), kteří ještě nedali žádný feedback.

    Krok počítáme jako „ozvaný“, když feedback nese oddělení tohoto kroku, nebo ho napsal
    člověk se stejným jménem (stačí křestní jméno). Byznys (Decider) a AI náhrady se nehlídají.
    """
    from tool.cli.triage import path_owners  # lazy: triage importuje ux, ne feedback_pull

    owners = path_owners(conn, project_id)
    authors = {_norm(f.get("submitted_by")) for f in feedback if f.get("submitted_by")}
    depts = {_norm(f.get("department")) for f in feedback if f.get("department")}
    out: list[dict[str, str]] = []
    for key, label in STEP_LABELS.items():
        name = owners.get(key, "").strip()
        if not name or name.upper().startswith("AI"):
            continue
        n = _norm(name)
        first = n.split()[0] if n.split() else n
        by_dept = any(d == _norm(label) or d.startswith(key) or _norm(label).startswith(d)
                      for d in depts if d)
        by_author = any(a == n or a == first or n in a or (first and a.split()[:1] == [first])
                        for a in authors)
        if not (by_dept or by_author):
            out.append({"step": key, "label": label, "name": name})
    return out

def aggregate(slug: str) -> dict[str, Any]:
    """Aggregate feedback for a project. Returns structured summary."""
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, name, status FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        project_id, name, status = int(proj[0]), proj[1], proj[2]

        # Feedback ke všem variantám projektu (i po Iterate)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(feedback)")}
        resolved = "f.resolved_at" if "resolved_at" in cols else "NULL"
        rows = conn.execute(
            f"""
            SELECT f.id, f.variant_id, v.name AS variant_name, v.builder,
                   f.role_id, r.catalog_label AS role_label,
                   f.severity, f.department, f.category,
                   f.score, f.rationale, f.ai_act_dimension, f.wcag_level,
                   f.is_ai_only, f.submitted_by, f.submitted_at,
                   {resolved} AS resolved_at
            FROM feedback f
            JOIN variants v ON v.id = f.variant_id
            JOIN sessions s ON s.id = v.session_id
            LEFT JOIN roles r ON r.id = f.role_id
            WHERE s.project_id = ?
            ORDER BY f.submitted_at DESC
            """,
            (project_id,),
        ).fetchall()

        feedback = [dict(r) for r in rows]

        # Aggregate
        by_severity: dict[str, int] = defaultdict(int)
        by_department: dict[str, list[float]] = defaultdict(list)
        by_variant: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "avg_score": 0.0, "scores": [], "criticals": []}
        )
        critical_flags: list[dict[str, Any]] = []
        ai_only_ratio_data = {"total": 0, "ai_only": 0}

        for fb in feedback:
            by_severity[fb["severity"]] += 1
            by_department[fb["department"]].append(fb["score"])
            v = fb["variant_name"]
            by_variant[v]["count"] += 1
            by_variant[v]["scores"].append(fb["score"])
            ai_only_ratio_data["total"] += 1
            if fb["is_ai_only"]:
                ai_only_ratio_data["ai_only"] += 1
            if fb["severity"] == "critical" and not fb["resolved_at"]:
                critical_flags.append({
                    "id": fb["id"],
                    "variant": v,
                    "department": fb["department"],
                    "rationale": fb["rationale"],
                    "submitted_by": fb["submitted_by"],
                    "submitted_at": fb["submitted_at"],
                    "wcag_level": fb["wcag_level"],
                    "ai_act_dimension": fb["ai_act_dimension"],
                })

        # Department averages
        dept_avg = {
            d: round(sum(scores) / len(scores), 3) if scores else 0.0
            for d, scores in by_department.items()
        }

        # Per-variant aggregates
        for v, data in by_variant.items():
            scores = data["scores"]
            data["avg_score"] = round(sum(scores) / len(scores), 3) if scores else 0.0
            data["criticals"] = sum(1 for fb in feedback
                                    if fb["variant_name"] == v and fb["severity"] == "critical"
                                    and not fb["resolved_at"])
            del data["scores"]  # don't dump raw

        ai_only_ratio = (
            ai_only_ratio_data["ai_only"] / ai_only_ratio_data["total"]
            if ai_only_ratio_data["total"] else 0.0
        )
        silent = silent_reps(conn, project_id, feedback)
        from tool.cli.session_2 import focus_variants, get_winner  # lazy: session_2 importuje nás

        winner = get_winner(conn, project_id)
        focus = focus_variants(conn, project_id)
        build_variants = sorted(r[0] for r in conn.execute(
            "SELECT v.name FROM variants v JOIN sessions s ON s.id = v.session_id "
            "WHERE s.project_id = ? AND s.type = 1", (project_id,)).fetchall())
        critical_flags.sort(key=lambda c: c["id"])
        for c in critical_flags:
            c["role"] = ("vítěz" if winner and c["variant"] == winner
                         else "shortlist" if c["variant"] in focus else "ostatní")
        crit_variants = {c["variant"] for c in critical_flags}
        by_variant_severity: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for fb in feedback:
            by_variant_severity[fb["variant_name"]][fb["severity"]] += 1

        # Audit: log the pull event (DORA — every read of audit-relevant data is itself logged)
        audit(
            conn,
            action="feedback.pull",
            target_type="project",
            target_id=project_id,
            payload={
                "slug": slug,
                "feedback_count": len(feedback),
                "critical_count": len(critical_flags),
                "ai_only_ratio": round(ai_only_ratio, 3),
            },
        )

    return {
        "slug": slug,
        "project_name": name,
        "project_status": status,
        "feedback_count": len(feedback),
        "by_severity": dict(by_severity),
        "by_department": dept_avg,
        "by_variant": dict(by_variant),
        "critical_flags": critical_flags,
        "winner": winner,
        "focus_variants": focus,
        "critical_on_all_variants": bool(build_variants) and set(build_variants) <= crit_variants,
        "by_variant_severity": {v: dict(c) for v, c in by_variant_severity.items()},
        "silent_reps": silent,
        "ai_only_ratio": round(ai_only_ratio, 3),
        "raw_feedback": feedback,
    }


def severity_text(counts: dict[str, int]) -> str:
    """„Kritické 1, Vysoké 2“ (jen nenulové), nebo „bez připomínek“."""
    parts = [f"{severity_label(k)} {counts[k]}" for k in SEVERITY_ORDER if counts.get(k)]
    return ", ".join(parts) or "bez připomínek"


def critical_line(c: dict[str, Any], limit: int = 90) -> str:
    text = (c.get("rationale") or "").strip().replace("\n", " ")
    if len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0] + "…"
    return (f"#{c['id']} {c.get('submitted_by') or 'autor neznámý'} "
            f"(krok {c['department']}) na variantě {c['variant']}"
            + (f": „{text}“" if text else ""))


ALL_VARIANTS_CRITICAL_LINE = ("Critical na všech variantách: Kill je legitimní výsledek — "
                              "nebo Iterate s jedním jasným zadáním.")


def critical_summary_lines(crits: list[dict[str, Any]], focus: list[str], winner: str | None,
                           all_variants: bool = False) -> list[str]:
    """Řádky o otevřených kritických — společné pro `feedback_pull` i `session_2 prep`.

    Všechny otevřené (stejná sada, stejná id, řazeno podle id); rozlišuje vítěze / shortlist /
    ostatní varianty. Critical na všech variantách dostane navíc větu o Kill / Iterate.
    """
    if not crits:
        return []
    on_focus = [c for c in crits if c["variant"] in focus]
    other = [c for c in crits if c["variant"] not in focus]
    who = "na vítězi" if winner else "na shortlistu"
    head = f"Otevřené kritické: {len(crits)}"
    if focus:
        head += f" — {len(on_focus)} {who} ({'/'.join(focus)}), {len(other)} na ostatních variantách"
    lines = [head]
    shown = (on_focus[:2] + other[:1]) if on_focus else other[:2]
    for c in shown:
        tag = ("vítěz" if winner and c["variant"] == winner
               else "shortlist" if c["variant"] in focus else "ostatní")
        lines.append(f"{tag}: {critical_line(c)}")
    hidden = len(crits) - len(shown)
    if hidden > 0:
        lines.append("…a " + count(hidden, "další otevřený kritický", "další otevřené kritické",
                                  "dalších otevřených kritických"))
    if all_variants:
        lines.append(ALL_VARIANTS_CRITICAL_LINE)
    return lines


def render_summary_md(agg: dict[str, Any]) -> str:
    """Souhrn feedbacku pro Rozhodnutí (v0.5)."""
    sev_table = "\n".join(
        f"| {severity_label(s)} | {agg['by_severity'].get(s, 0)} |" for s in SEVERITY_ORDER
    )
    var_rows = "\n".join(
        f"| {v} | {data['count']} | {severity_text(agg['by_variant_severity'].get(v, {}))} "
        f"| {data['criticals']} |"
        for v, data in sorted(agg["by_variant"].items())
    ) or "| — | — | — | — |"
    dept_rows = "\n".join(
        f"| {d} | {n} |" for d, n in sorted(
            ((d, sum(1 for f in agg["raw_feedback"] if f["department"] == d))
             for d in agg["by_department"]), key=lambda x: -x[1])
    ) or "| — | — |"

    crit_section = ""
    if agg["critical_flags"]:
        crit_rows = "\n".join(f"- {critical_line(c, 300)} *({c['submitted_at']})*"
                              for c in agg["critical_flags"])
        crit_section = (
            f"\n## Otevřené kritické ({len(agg['critical_flags'])})\n\n"
            f"{crit_rows}\n\n"
            f"> Kritická připomínka na vítězi blokuje Go, dokud se nevyřeší "
            f"(`pflanzer session_2 resolve`) nebo ji Decider výslovně nepřebije s důvodem.\n"
        )
    silent_section = ""
    if agg.get("silent_reps"):
        who = ", ".join(f"{r['label']} ({r['name']})" for r in agg["silent_reps"])
        silent_section = f"\n## Ještě bez feedbacku\n\n{who}\n"

    ai_warn = ""
    if agg["ai_only_ratio"] > 0.5:
        ai_warn = (
            f"\n> ⚠ **{agg['ai_only_ratio']:.0%} feedbacku píše AI persona**, ne reální lidé. "
            f"Před Rozhodnutím doporučujeme rozhovor se skutečným uživatelem.\n"
        )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""{BRAND_LINE}

# Souhrn feedbacku — {agg['project_name']}

> Slug: `{agg['slug']}` · Staženo: {today} · Stav projektu: `{agg['project_status']}`
> Async (3–5 dní) → vstup pro Rozhodnutí (Go / Iterate / Kill).

## Přehled

- **Připomínek celkem**: {agg['feedback_count']}
- **Podíl AI feedbacku**: {agg['ai_only_ratio']:.0%} (hodnocení AI má váhu max 0,5)
{ai_warn}
## Podle závažnosti

| Závažnost | Počet |
|-----------|-------|
{sev_table}

## Podle varianty

| Varianta | Připomínek | Rozpis | Otevřené kritické |
|----------|------------|--------|-------------------|
{var_rows}

## Podle kroku cesty (počet připomínek)

| Krok | Připomínek |
|------|-----------|
{dept_rows}
{crit_section}{silent_section}
## Co dál

1. Otevřené kritické řeší Decider **před** Rozhodnutím (oprava, nebo vědomé přebití s důvodem).
2. Kdo ještě nenapsal, dostane připomínku; mlčení nevetovací role po termínu = souhlas,
   u bezpečnosti ne.
3. `pflanzer session_2 prep --slug {agg['slug']}`, pak Rozhodnutí.
"""


def write_summary(slug: str, agg: dict[str, Any] | None = None) -> Path | None:
    """Zapíše souhrn; při 0 řádcích feedbacku nezapíše nic a vrátí None."""
    agg = agg or aggregate(slug)
    if agg["feedback_count"] == 0:
        return None
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    out = FEEDBACK_DIR / f"{slug}-summary.md"
    out.write_text(render_summary_md(agg), encoding="utf-8")
    return out


def _human(agg: dict[str, Any], summary_path: Any) -> tuple[str, list[str], list[str], str, dict[str, Any]]:
    slug = agg["slug"]
    crit = agg["critical_flags"]
    silent = agg["silent_reps"]
    lines = [f"Připomínek celkem: {agg['feedback_count']} ({severity_text(agg['by_severity'])})"]
    lines += critical_summary_lines(crit, agg["focus_variants"], agg["winner"],
                                    agg["critical_on_all_variants"])
    if not crit:
        for v in sorted(agg["by_variant"])[:3]:
            lines.append(f"Varianta {v}: {severity_text(agg['by_variant_severity'].get(v, {}))}")
    if silent:
        lines.append("Ještě bez feedbacku: " + ", ".join(f"{r['label']} ({r['name']})"
                                                        for r in silent))
    warns = []
    if agg["ai_only_ratio"] > 0.5:
        warns.append(f"{agg['ai_only_ratio']:.0%} feedbacku píše AI persona, ne lidé — "
                     "před Rozhodnutím zkus rozhovor se skutečným uživatelem.")
    if crit:
        first = next((c for c in crit if c["variant"] in agg["focus_variants"]), crit[0])
        nxt = (f"vyřeš kritické #{first['id']} s autorem ({first.get('submitted_by') or '?'}): "
               f"`pflanzer session_2 resolve --slug {slug} --feedback-id {first['id']} "
               f"--by JMÉNO --note \"…\"`")
    elif silent:
        r = silent[0]
        nxt = (f"ozvi se {r['name']} ({r['label']}); jeho připomínku zapíšeš: "
               f"`pflanzer feedback add --slug {slug} --variant A --role {r['step']} "
               f"--severity major --text \"…\" --author {r['name']}`")
    else:
        nxt = f"`pflanzer session_2 prep --slug {slug}`"
    if summary_path:
        lines.append(f"Souhrn: {display_path(summary_path)}")
    return (f"Feedback {slug}", lines[:8], warns, nxt,
            {"silent_reps": bool(silent), "open_critical": bool(crit)})


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer feedback_pull", description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--json", action="store_true",
                   help="Vypíše celý agregát jako JSON (default: lidský souhrn + zápis MD)")
    args = p.parse_args()

    try:
        agg = aggregate(args.slug)
    except ValueError as e:
        exit_if_project_missing(e)
        die(f"{e} Přehled projektů: `pflanzer status`.", "pflanzer feedback_pull --slug moje-appka")

    if args.json:
        print(json.dumps(agg, ensure_ascii=False, indent=2, default=str))
        return

    if agg["feedback_count"] == 0:
        emit({}, title=f"Feedback {args.slug}: zatím nic",
             lines=["Nikdo zatím nenapsal žádnou připomínku."],
             next_step=NO_FEEDBACK_MSG.format(slug=args.slug),
             tips=tips(args.slug, "async", {"silent_reps": bool(agg["silent_reps"])}))
        sys.exit(1)

    path = write_summary(args.slug, agg)
    title, lines, warns, nxt, ctx = _human(agg, path)
    emit(agg, title=title, lines=lines, warnings=warns, next_step=nxt,
         tips=tips(args.slug, "async", ctx))


if __name__ == "__main__":
    main()
