"""Sprint 3 — SHIP.md + auto `gh pr create` command.

Per autoresearch synthesis ADR-0010 + perspektiva 02 vibe-product:
> "Handoff package: 8 files → 1-page SHIP.md + auto-rendered `gh pr create`
>  command within 30s of Session 3. The 8 per-role MDs are compliance theater
>  nobody reads."

Tento modul:
1. Render `data/handoffs/<slug>/SHIP.md` — 1 stránka markdown s:
   - Co se mění (variant, branch, files touched)
   - Kdo to merguje (target_branch_owner z Charteru)
   - Quality gate score badges
   - Acceptance criteria pass rate
   - Kill criteria + rollback plán
   - Copy-paste `gh pr create` command (s pre-filled title + body)
2. Output je primary handoff artefakt; 8 per-role files (handoff.py)
   degraduje na supplementary.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

SHIP_DIR = REPO_ROOT / "data" / "handoffs"


def _fetch_ship_context(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        proj = conn.execute(
            """
            SELECT id, name, slug, status, xyz_hypothesis, decider_name,
                   target_repo_url, target_branch, target_branch_owner,
                   shadow_pm, kill_criteria, throwaway_or_evolve,
                   ai_act_tier, data_class, gate_score_latest,
                   production_readiness_target, acceptance_criteria_md,
                   primary_lagging_metric, leading_metric, guardrail_metric
            FROM projects WHERE slug = ?
            """, (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")

        # Winner = variant s gate_score blízko aktuálnímu projects.gate_score_latest.
        # Pokud žádná extracted/gates row (Session 3 ještě neběžela), fallback
        # na preference_score winner.
        sess1 = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1",
            (proj[0],),
        ).fetchone()
        winner = None
        if sess1:
            # First try: variant with extracted code AND highest gate score
            row = conn.execute(
                """
                SELECT v.name, v.builder, v.prototype_url, v.preference_score,
                       v.description_md, v.id,
                       COALESCE(MAX(qg.metric_value), 0) AS avg_gate
                FROM variants v
                LEFT JOIN extracted_code e ON e.variant_id = v.id
                LEFT JOIN quality_gates qg ON qg.extracted_id = e.id
                WHERE v.session_id = ? AND e.id IS NOT NULL
                GROUP BY v.id
                ORDER BY v.preference_score DESC, avg_gate DESC LIMIT 1
                """, (sess1[0],),
            ).fetchone()
            if row:
                winner = row
            else:
                # Fallback: highest preference, no extracted code yet
                winner = conn.execute(
                    """
                    SELECT v.name, v.builder, v.prototype_url, v.preference_score,
                           v.description_md, v.id
                    FROM variants v
                    WHERE v.session_id = ?
                    ORDER BY v.preference_score DESC LIMIT 1
                    """, (sess1[0],),
                ).fetchone()

        # Extracted code path + gate scores per variant
        ext_rows = []
        if winner:
            ext_rows = list(conn.execute(
                """
                SELECT e.id, e.local_path, e.extraction_method, e.files_count,
                       e.total_loc
                FROM extracted_code e
                WHERE e.variant_id = ?
                ORDER BY e.id DESC LIMIT 1
                """, (winner[5],),
            ).fetchall())

        # Per-gate detail
        gate_rows = []
        if ext_rows:
            gate_rows = list(conn.execute(
                "SELECT gate_type, status, metric_value, details_md "
                "FROM quality_gates WHERE extracted_id = ? ORDER BY id",
                (ext_rows[0][0],),
            ).fetchall())

        # Decision rationale
        decision = conn.execute(
            "SELECT body_md, atribuce_user FROM decisions "
            "WHERE project_id = ? AND type = 'handoff' "
            "ORDER BY id DESC LIMIT 1", (proj[0],),
        ).fetchone()

    return {
        "project": proj,
        "winner": winner,
        "extracted": ext_rows[0] if ext_rows else None,
        "gates": gate_rows,
        "decision": decision,
    }


def _render_gate_badges(gates: list) -> str:
    icons = {"pass": "✅", "warn": "⚠️", "fail": "❌",
             "skipped": "⏭️", "unsupported": "—"}
    return " ".join(f"{icons.get(g[1], '?')} {g[0]}" for g in gates) or "(no gates run yet)"


def render_ship_md(slug: str) -> str:
    ctx = _fetch_ship_context(slug)
    p = ctx["project"]
    w = ctx["winner"]
    e = ctx["extracted"]
    gates = ctx["gates"]

    name, decider = p[1], p[5]
    target_repo = p[6] or "(target_repo_url unset — set in Charter)"
    target_branch = p[7] or "main"
    branch_owner = p[8] or "(target_branch_owner unset)"
    shadow_pm = p[9] or "(shadow_pm unset — per perspektiva 02 needed)"
    kill = p[10] or "TBD"
    gate_score = int(p[14] or 0)
    target = int(p[15] or 80)
    throwaway = p[11]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ready = gate_score >= target
    verdict = "🚀 **PRODUCTION-READY**" if ready else "⚠ **PILOT-ONLY**"

    winner_info = ""
    pr_command = ""
    if w and e:
        feat_branch = f"pflanzer/{slug}-{w[0]}"
        pr_title = f"feat({slug}): {name[:60]}"
        pr_body_lines = [
            f"## Co se mění",
            f"{p[4]}",  # xyz_hypothesis
            "",
            f"## Pflanzer session output",
            f"- **Variant**: `{w[0]}` (`{w[1]}`)",
            f"- **Preference score**: {w[3]:.2f}",
            f"- **Gate score**: **{gate_score}/{target}** ({verdict})",
            f"- **Acceptance pass rate**: " +
            next((f"{int(g[2])} %" for g in gates if g[0] == "acceptance" and g[2] is not None), "N/A"),
            f"- **Files**: {e[3]} ({e[4]} LOC)",
            f"- **Local path**: `{e[1]}`",
            "",
            f"## Quality gates",
            f"{_render_gate_badges(gates)}",
            "",
            f"## Decider",
            f"{decider} — {ctx['decision'][1] if ctx['decision'] else current_actor()}",
            "",
            f"## Kill criteria",
            f"{kill}",
            "",
            f"## Measurement plan",
            f"- Primary lagging: {p[17] or 'TBD'}",
            f"- Leading: {p[18] or 'TBD'}",
            f"- Guardrail: {p[19] or 'TBD'}",
            "",
            f"---",
            f"*Generated by Pflanzer `/pflanzer-handoff` per ADR-0010.*",
        ]
        pr_body = "\n".join(pr_body_lines)

        winner_info = f"""## 🏆 Winner

- **Variant**: `{w[0]}` (`{w[1]}`)
- **Branch**: `{feat_branch}` v `{target_repo}`
- **Code**: `{e[1]}` ({e[3]} files / {e[4]} LOC)
- **Gate score**: **{gate_score}/{target}** {verdict}

### Quality gates

{_render_gate_badges(gates)}
"""
        pr_command = f"""## 📤 Open PR (copy-paste)

```bash
cd {e[1]}
git push -u origin {feat_branch}

gh pr create \\
  --title "{pr_title}" \\
  --body "$(cat <<'PRBODY'
{pr_body}
PRBODY
)" \\
  --base {target_branch} \\
  --reviewer {branch_owner if branch_owner != '(target_branch_owner unset)' else 'YOUR-GH-HANDLE'} \\
  --label pflanzer
```
"""

    return f"""# SHIP — {name}

> Slug: `{p[2]}` · Generated: {today} · {verdict}
> Per ADR-0010 (1-page SHIP.md místo 8-file compliance theater).

## Co se mění

{p[4]}

## Ownership

| Role | Person |
|------|--------|
| **Decider** | {decider} |
| **Branch owner / merger** | {branch_owner} |
| **Shadow PM** (mezi-session babysitter) | {shadow_pm} |

{winner_info}

## Risk profile

- **AI Act tier**: `{p[12]}` · **Data class**: `{p[13]}` · **Profile**: `{throwaway}`

## Kill criteria

{kill}

## Measurement plan

- **Primary lagging**: {p[17] or 'TBD — set v Session 2 / handoff'}
- **Leading**: {p[18] or 'TBD'}
- **Guardrail**: {p[19] or 'TBD'}
- **Instrumentation deadline**: ship-date − 2 dny (per role catalog #12)

{pr_command}

## Co dál (T+0 → T+90)

- **Today**: PR otevřený, branch_owner reviews
- **T+1d**: PR merged → deploy preview link sdílen v Slack/Discord
- **T+7d**: feature flag rollout 10 % users; Decider checks instrumentation
- **T+14d**: rollout 50 % users; first metrics review (hit primary lagging?)
- **T+30d**: full rollout OR rollback dle kill criteria
- **T+60-90d**: retrospektiva, contribution do `data/method-metrics.json`

## Compliance audit trail

- DORA: audit_log v `data/pflanzer.db` audit_log table (7-letá retence)
- Decision atribuce: `data/handoffs/{p[2]}/decision.md` (per-role package)
- AI Act: pokud `tier=high`, generate Annex IV tech doc před production launch
- GDPR: pokud `data_class=L3+`, RoPA update + DPIA (per Legal triage)

---

*Tento SHIP.md je primary handoff artefakt. 8 per-role files
(`data/handoffs/{p[2]}/{{decision,be,fe,qa,platform,data,support,compliance}}.md`)
jsou supplementary pro audit + per-role deep dive — nikdo je nečte u stolu.
Per perspektiva 02 vibe-product C7 (anti-theater).*
"""


def write_ship(slug: str) -> Path:
    SHIP_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = SHIP_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    out = project_dir / "SHIP.md"
    out.write_text(render_ship_md(slug), encoding="utf-8")

    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if proj:
            audit(
                conn, action="ship.render",
                target_type="project", target_id=int(proj[0]),
                payload={"slug": slug, "path": str(out.relative_to(REPO_ROOT))},
            )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--print", action="store_true",
                   help="Print SHIP.md to stdout (default: write to file)")
    args = p.parse_args()

    if args.print:
        print(render_ship_md(args.slug))
    else:
        path = write_ship(args.slug)
        print(json.dumps({
            "slug": args.slug,
            "ship_path": str(path.relative_to(REPO_ROOT)),
            "next_step": (
                f"Vyhoď {path} týmu na velký TV. Decider nebo branch_owner "
                f"copy-paste `gh pr create` command z konce SHIP.md."
            ),
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
