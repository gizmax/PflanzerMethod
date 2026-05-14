"""Slice 7 — Session 2 (decisional) backend.

3-hodinová decisional session per `docs/methodology/06-session-2.md`. Cíl:
Decider's call **Go / Iterate / Kill** s commitment indexem vs threshold
z Charteru.

Vstupy:
- Feedback summary (`tool/cli/feedback_pull.py`).
- Conflict matrix (`tool/cli/conflict_resolver.py`).
- Discovery debt audit (volitelně z `discovery-debt-detector` agent).
- Charter XYZ + kill criteria.

Výstup:
- `sessions` row type=2 s decision (go|iterate|kill).
- Pokud iterate: max 1× další session (type=3) — guard against infinite loop.
- Pokud go: status='handoff' → triggers /pflanzer-handoff.
- Pokud kill: status='killed', kill row v decisions.
- Eskalační protokol per ADR-0001 pokud Decider neumí rozhodnout
  (commitment_index = 0 nebo split decision).
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

from tool.cli.conflict_resolver import detect_conflicts  # noqa: E402
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.feedback_pull import aggregate as pull_aggregate  # noqa: E402

SESSIONS_DIR = REPO_ROOT / "data" / "sessions"
VALID_DECISIONS = {"go", "iterate", "kill"}
COMMITMENT_THRESHOLD = 0.6  # Default; over-ridable per Charter (TODO: schema field)


def prep(slug: str) -> dict[str, Any]:
    """Pre-Session 2 prep: aggregate feedback + detect conflicts.

    Read-only. Stdout je vstupem pro slash command, který pak vede AI panel
    + Decider call.
    """
    agg = pull_aggregate(slug)
    conflicts = detect_conflicts(slug)

    # Compute commitment index ze sessions/variants
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, kill_criteria, xyz_hypothesis, decider_name "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status, kill, xyz, decider = (
            int(proj[0]), proj[1], proj[2], proj[3], proj[4],
        )

        # Aggregate commitment from role_preferences (best variant)
        sess1 = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1",
            (project_id,),
        ).fetchone()
        commitments: list[int] = []
        if sess1:
            top_variant = conn.execute(
                "SELECT id FROM variants WHERE session_id = ? "
                "ORDER BY preference_score DESC LIMIT 1", (sess1[0],),
            ).fetchone()
            if top_variant:
                commit_rows = conn.execute(
                    "SELECT commitment_level FROM role_preferences "
                    "WHERE variant_id = ? AND commitment_level IS NOT NULL",
                    (top_variant[0],),
                ).fetchall()
                commitments = [int(c[0]) for c in commit_rows]

    commitment_index = (
        sum(commitments) / (3 * len(commitments)) if commitments else 0.0
    )  # Normalized 0..1 (max 3 per role)

    return {
        "slug": slug,
        "project_status": status,
        "decider": decider,
        "xyz": xyz,
        "kill_criteria": kill,
        "commitment_index": round(commitment_index, 3),
        "commitment_threshold": COMMITMENT_THRESHOLD,
        "ready_for_decision": commitment_index >= COMMITMENT_THRESHOLD,
        "feedback_summary": {
            "count": agg["feedback_count"],
            "by_severity": agg["by_severity"],
            "ai_only_ratio": agg["ai_only_ratio"],
            "critical_flags": len(agg["critical_flags"]),
        },
        "conflicts": conflicts["top_conflicts"][:3],  # top 3
        "unmapped_conflicts": conflicts["unmapped_count"],
        "next_action": _suggest_next_action(commitment_index, agg, conflicts),
    }


def _suggest_next_action(
    commitment_index: float, agg: dict[str, Any], conflicts: dict[str, Any],
) -> str:
    if len(agg["critical_flags"]) > 0:
        return "RESOLVE_CRITICALS_FIRST"
    if commitment_index < COMMITMENT_THRESHOLD:
        return "GATHER_MORE_FEEDBACK"
    if conflicts["unmapped_count"] > 0:
        return "REVIEW_UNMAPPED_CONFLICTS"
    return "DECIDER_CALL_READY"


def record_decision(
    *, slug: str, decision: str, rationale: str,
    decider_attribution: str | None = None,
    iterate_focus: str | None = None,
) -> dict[str, Any]:
    """Persist Decider's call. Idempotent per (project, session_2)."""
    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision must be one of {VALID_DECISIONS}")
    if not rationale.strip():
        raise ValueError("rationale je POVINNÝ pro decision log (DORA / AI Act čl. 14).")

    decider_attribution = decider_attribution or current_actor()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, decider_name FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id = int(proj[0])

        # Find or create Session 2 row
        sess = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 2",
            (project_id,),
        ).fetchone()
        if sess:
            session_id = int(sess[0])
            conn.execute(
                "UPDATE sessions SET decision = ?, decision_atribuce = ?, "
                "decision_ts = CURRENT_TIMESTAMP, ends_at = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (decision, decider_attribution, session_id),
            )
        else:
            cur = conn.execute(
                "INSERT INTO sessions (project_id, type, starts_at, ends_at, "
                "decision, decision_atribuce, decision_ts) "
                "VALUES (?, 2, ?, ?, ?, ?, ?)",
                (project_id, now, now, decision, decider_attribution, now),
            )
            session_id = cur.lastrowid

        # Iterate guard — max 1 type=3 row
        if decision == "iterate":
            existing_iters = conn.execute(
                "SELECT COUNT(*) FROM sessions WHERE project_id = ? AND type = 3",
                (project_id,),
            ).fetchone()[0]
            if existing_iters >= 1:
                raise ValueError(
                    "Iterate already used (max 1×). Decision musí být Go nebo Kill. "
                    "Pokud opravdu chceš re-iter, manuálně reset DB a re-Charter."
                )
            iter_focus_md = iterate_focus or "Iterate focus: TBD"
            conn.execute(
                "INSERT INTO sessions (project_id, type, starts_at, decision, notes_md) "
                "VALUES (?, 3, ?, 'pending', ?)",
                (project_id, now, iter_focus_md),
            )

        # Decision row + status update
        decision_md = render_decision_md(
            slug, decision, rationale, decider_attribution, iterate_focus,
        )
        conn.execute(
            "INSERT INTO decisions (project_id, type, body_md, atribuce_user, atribuce_ts) "
            "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (project_id,
             "kill" if decision == "kill" else ("handoff" if decision == "go" else "preference"),
             decision_md, decider_attribution),
        )

        new_status = {
            "go": "handoff",
            "iterate": "session_2",  # stay in session_2 until iterate done
            "kill": "killed",
        }[decision]
        conn.execute(
            "UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, project_id),
        )

        audit(
            conn,
            action="session_2.decision",
            target_type="project",
            target_id=project_id,
            payload={
                "slug": slug, "decision": decision,
                "decider": decider_attribution,
                "iterate_focus": iterate_focus,
            },
        )

    summary_path = _write_summary(slug, project_id, session_id, decision, rationale,
                                  decider_attribution, iterate_focus)

    return {
        "project_id": project_id,
        "session_id": session_id,
        "slug": slug,
        "decision": decision,
        "decider": decider_attribution,
        "new_status": new_status,
        "summary_path": str(summary_path),
        "next_step": _next_step_label(decision, slug),
    }


def render_decision_md(
    slug: str, decision: str, rationale: str,
    decider: str, iterate_focus: str | None,
) -> str:
    body = f"""## Session 2 — Decider's Go/Iterate/Kill call

- **Decision**: **{decision.upper()}**
- **Slug**: `{slug}`
- **Atribuce**: {decider} · {datetime.now(timezone.utc).isoformat(timespec="seconds")}

### Rationale

{rationale}
"""
    if decision == "iterate" and iterate_focus:
        body += f"\n### Iterate focus (max 1×)\n\n{iterate_focus}\n"
    return body


def _next_step_label(decision: str, slug: str) -> str:
    if decision == "go":
        return f"`/pflanzer-handoff {slug}` — generate per-role handoff package."
    if decision == "iterate":
        return (
            f"Re-run jedné iterace: `/pflanzer-session-1 {slug}` (single new variant) → "
            f"feedback → `/pflanzer-session-2 {slug}` znovu. **Max 1× iterate**."
        )
    return f"Project killed. Optional retro: `data/sessions/{slug}/_kill-retro.md` (manuálně)."


def _write_summary(
    slug: str, project_id: int, session_id: int,
    decision: str, rationale: str, decider: str, iterate_focus: str | None,
) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = SESSIONS_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    md = f"""# Session 2 — {slug}

> Project ID: {project_id} · Session ID: {session_id}
> Decision: **{decision.upper()}** · Decider: {decider}
> Per `docs/methodology/06-session-2.md`.

## Rationale

{rationale}

{f'## Iterate focus{chr(10)}{chr(10)}{iterate_focus}{chr(10)}' if decision == 'iterate' and iterate_focus else ''}
## Next step

{_next_step_label(decision, slug)}
"""
    out = project_dir / "_session_2_summary.md"
    out.write_text(md, encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    p_prep = sub.add_parser("prep", help="Pre-Session 2 aggregate (read-only)")
    p_prep.add_argument("--slug", required=True)

    p_dec = sub.add_parser("decide", help="Record Decider's Go/Iterate/Kill call")
    p_dec.add_argument("--slug", required=True)
    p_dec.add_argument("--decision", required=True, choices=sorted(VALID_DECISIONS))
    p_dec.add_argument("--rationale", required=True)
    p_dec.add_argument("--iterate-focus", default=None)
    p_dec.add_argument("--decider", default=None)

    args = p.parse_args()

    if args.cmd == "prep":
        out = prep(args.slug)
    else:
        out = record_decision(
            slug=args.slug, decision=args.decision, rationale=args.rationale,
            iterate_focus=args.iterate_focus, decider_attribution=args.decider,
        )
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
