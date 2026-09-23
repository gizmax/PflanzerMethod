"""Slice 6 — Feedback intake & audit (pre-Session 2 prep).

Web hub a CC sdílí stejnou SQLite (`data/pflanzer.db`), takže "pull" není
data-mover, ale **feedback summary + audit trigger**:

1. List veškerého feedbacku per project z web hubu.
2. Aggregate by department / severity / variant.
3. Identifikuj **Critical flags** (severity='critical') → eskalační log.
4. Připrav summary MD pro Session 2 (`docs/methodology/06-session-2.md`
   § Aggregate feedback by department).
5. Volitelně spustit discovery-debt-detector audit (přes Claude Agent;
   tento modul jen připraví vstupní data).

AI-only deflation byla již aplikována v `tool/web/backend/api/feedback.py`
při submit (devil's advocate Útok 6 — heuristic, ne measurement). Tady už
pracujeme s deflated scores.
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

from tool.cli.db import audit, transaction  # noqa: E402

FEEDBACK_DIR = REPO_ROOT / "data" / "feedback"


def aggregate(slug: str) -> dict[str, Any]:
    """Aggregate feedback for a project. Returns structured summary."""
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, name, status FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, name, status = int(proj[0]), proj[1], proj[2]

        if status not in ("session_1", "session_2", "handoff"):
            # Soft warn — feedback before Session 1 exists is OK pro early bird,
            # ale obvykle to znamená že tým spustil pull předčasně.
            pass

        # Pull all feedback for variants in this project's session 1
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
            WHERE s.project_id = ? AND s.type = 1
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
    """Render feedback summary MD pro Session 2 prep."""
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
            f"> Per `04-session-1.md` § Konfliktní situace: Critical flag = session "
            f"pivotuje na alt. variantu (Security/Legal veto pattern).\n"
        )

    ai_warn = ""
    if agg["ai_only_ratio"] > 0.5:
        ai_warn = (
            f"\n> ⚠ **AI-only ratio = {agg['ai_only_ratio']:.0%}** — víc než polovina "
            f"feedbacku je AI persona, ne reální lidé. Discovery debt risk "
            f"(per role catalog #14). Před Session 2 doporučeno: real user interview.\n"
        )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""# Feedback summary — {agg['project_name']}

> Slug: `{agg['slug']}` · Pulled: {today} · Project status: `{agg['project_status']}`
> Per `docs/methodology/05-mezi-sessions.md` + `06-session-2.md`.

## Přehled

- **Feedback rows celkem**: {agg['feedback_count']}
- **AI-only ratio**: {agg['ai_only_ratio']:.0%} (deflated max 0.5 per Útok 6)
{ai_warn}
## Severity rozložení

| Severity | Count |
|----------|-------|
{sev_table}

## Per-variant scoring

| Variant | Feedback rows | Avg score | Critical flags |
|---------|---------------|-----------|----------------|
{var_rows}

## Per-department avg score

| Department | Avg score |
|------------|-----------|
{dept_rows}
{crit_section}
## Co dál

1. Spusť **discovery-debt-detector** sub-agent na tento summary
   (vrátí skóre 0-10; > 2 = warning, > 5 = block Session 2).
2. Pokud Critical flags > 0 → Decider review **před** Session 2 (eskalační
   protokol per ADR-0001).
3. Spusť `/pflanzer-session-2 {agg['slug']}` (Slice 7) pro decisional session.
"""


def write_summary(slug: str) -> Path:
    agg = aggregate(slug)
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    out = FEEDBACK_DIR / f"{slug}-summary.md"
    out.write_text(render_summary_md(agg), encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--json", action="store_true",
                   help="Print full aggregate JSON (default: render MD summary)")
    args = p.parse_args()

    if args.json:
        print(json.dumps(aggregate(args.slug), ensure_ascii=False, indent=2, default=str))
    else:
        agg = aggregate(args.slug)
        path = write_summary(args.slug)
        print(json.dumps({
            "slug": args.slug,
            "summary_path": str(path),
            "feedback_count": agg["feedback_count"],
            "critical_flags": len(agg["critical_flags"]),
            "ai_only_ratio": agg["ai_only_ratio"],
            "next_step": (
                "Discovery debt audit + /pflanzer-session-2 <slug>"
                if agg["feedback_count"] > 0
                else "Žádný feedback yet — počkej 5-7 dní mezi-session okno."
            ),
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
