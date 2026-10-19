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

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import DATA_ROOT, audit, current_actor, display_path, transaction  # noqa: E402

FEEDBACK_DIR = DATA_ROOT / "feedback"
BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"
NO_FEEDBACK_MSG = (
    "Žádný feedback — sbírej přes hub nebo `pflanzer feedback add` "
    "(např. pflanzer feedback add --slug {slug} --variant A --role \"Bezpečnost\" "
    "--severity major --text \"...\")."
)

def aggregate(slug: str) -> dict[str, Any]:
    """Aggregate feedback for a project. Returns structured summary."""
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, name, status FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, name, status = int(proj[0]), proj[1], proj[2]

        # Feedback ke všem variantám projektu (i po Iterate)
        rows = conn.execute(
            """
            SELECT f.id, f.variant_id, v.name AS variant_name, v.builder,
                   f.role_id, r.catalog_label AS role_label,
                   f.severity, f.department, f.category,
                   f.score, f.rationale, f.ai_act_dimension, f.wcag_level,
                   f.is_ai_only, f.submitted_by, f.submitted_at
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
            if fb["severity"] == "critical":
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
                                    if fb["variant_name"] == v and fb["severity"] == "critical")
            del data["scores"]  # don't dump raw

        ai_only_ratio = (
            ai_only_ratio_data["ai_only"] / ai_only_ratio_data["total"]
            if ai_only_ratio_data["total"] else 0.0
        )

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
        "ai_only_ratio": round(ai_only_ratio, 3),
        "raw_feedback": feedback,
    }


def render_summary_md(agg: dict[str, Any]) -> str:
    """Souhrn feedbacku pro Rozhodnutí (v0.5)."""
    sev_table = "\n".join(
        f"| {s} | {agg['by_severity'].get(s, 0)} |"
        for s in ("critical", "high", "medium", "low")
    )
    dept_rows = "\n".join(
        f"| {d} | {avg:.2f} |"
        for d, avg in sorted(agg["by_department"].items(), key=lambda x: -x[1])
    ) or "| — | — |"
    var_rows = "\n".join(
        f"| {v} | {data['count']} | {data['avg_score']:.2f} | {data['criticals']} |"
        for v, data in sorted(agg["by_variant"].items(), key=lambda x: -x[1]["avg_score"])
    ) or "| — | — | — | — |"

    crit_section = ""
    if agg["critical_flags"]:
        crit_rows = "\n".join(
            f"- **[{c['variant']} / {c['department']}]** — {c['rationale']}"
            f" *(by {c['submitted_by']}, {c['submitted_at']})*"
            for c in agg["critical_flags"]
        )
        crit_section = (
            f"\n## ⚠ Critical flags ({len(agg['critical_flags'])})\n\n"
            f"{crit_rows}\n\n"
            f"> Critical flag = varianta se nedá vybrat, dokud se nevyřeší nebo "
            f"Decider výslovně nepřijme riziko (ADR-0001, veto Bezpečnost & právo).\n"
        )

    ai_warn = ""
    if agg["ai_only_ratio"] > 0.5:
        ai_warn = (
            f"\n> ⚠ **AI-only ratio = {agg['ai_only_ratio']:.0%}** — víc než polovina "
            f"feedbacku je AI persona, ne reální lidé. Riziko discovery debtu. "
            f"Před Rozhodnutím doporučen rozhovor se skutečným uživatelem.\n"
        )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""{BRAND_LINE}

# Souhrn feedbacku — {agg['project_name']}

> Slug: `{agg['slug']}` · Staženo: {today} · Stav projektu: `{agg['project_status']}`
> Async (3–5 dní) → vstup pro Rozhodnutí (Go / Iterate / Kill).

## Přehled

- **Řádků feedbacku celkem**: {agg['feedback_count']}
- **AI-only ratio**: {agg['ai_only_ratio']:.0%} (skóre AI-only max 0.5)
{ai_warn}
## Rozložení podle severity

| Severity | Počet |
|----------|-------|
{sev_table}

## Skóre podle varianty

| Varianta | Řádků feedbacku | Průměrné skóre | Critical flags |
|----------|-----------------|----------------|----------------|
{var_rows}

## Průměrné skóre podle oddělení

| Oddělení | Průměrné skóre |
|----------|----------------|
{dept_rows}
{crit_section}
## Co dál

1. Spusť **discovery-debt-detector** na tento souhrn (skóre 0–10;
   > 2 = varování, > 5 = blokuje Rozhodnutí).
2. Pokud jsou otevřené Critical flags → Decider je řeší **před** Rozhodnutím
   (eskalační protokol ADR-0001).
3. Spusť `/pm decide` pro Rozhodnutí.
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


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--json", action="store_true",
                   help="Vypíše celý agregát jako JSON (default: zapíše souhrn MD)")
    args = p.parse_args()

    try:
        agg = aggregate(args.slug)
    except ValueError as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(agg, ensure_ascii=False, indent=2, default=str))
        return

    if agg["feedback_count"] == 0:
        print(json.dumps({
            "slug": args.slug,
            "feedback_count": 0,
            "summary_path": None,
            "message": NO_FEEDBACK_MSG.format(slug=args.slug),
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    path = write_summary(args.slug, agg)
    print(json.dumps({
        "slug": args.slug,
        "summary_path": display_path(path),
        "feedback_count": agg["feedback_count"],
        "critical_flags": len(agg["critical_flags"]),
        "ai_only_ratio": agg["ai_only_ratio"],
        "next_step": (
            "Nejdřív vyřeš otevřené critical flags, pak /pm decide"
            if agg["critical_flags"] else "Discovery debt audit, pak /pm decide"
        ),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
