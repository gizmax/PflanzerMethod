"""Slice 3 — Pre-flight triage aggregator.

The 4 triage sub-agents (discovery-readiness, security-triage, legal-triage,
platform-triage) run in parallel via Claude Code Agent calls. Each returns
a JSON with a `track` field + `status` + artefact_md. This module:

1. Persists the 4 triage rows in DB.
2. Computes overall pre-flight gate status (all 4 must be 'ok' or 'deferred').
3. Updates project status to 'triage' (if all clear) or keeps 'charter'
   (if any 'blocked').
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

TRIAGE_DIR = REPO_ROOT / "data" / "triage"
EXPECTED_TRACKS = ("discovery", "security", "legal", "platform")


def aggregate(slug: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """Persist 4 triage outputs + gate decision.

    Args:
        slug: project slug.
        results: list of 4 dicts (1 per track) with keys:
            track, status (ok|blocked|deferred), artefact_md, signed_by, ...

    Returns:
        dict with overall_status, blockers, warnings, summary_path.
    """
    seen_tracks = {r["track"] for r in results}
    missing = set(EXPECTED_TRACKS) - seen_tracks
    if missing:
        raise ValueError(f"Missing triage tracks: {missing}")

    # Aggregate
    blockers: list[str] = []
    warnings: list[str] = []
    for r in results:
        if r["status"] == "blocked":
            blockers.append(f"[{r['track']}] {r.get('rationale', 'no rationale')}")
        if r.get("warnings"):
            warnings.extend(f"[{r['track']}] {w}" for w in r["warnings"])

    overall = "blocked" if blockers else "ok"

    # Persist
    TRIAGE_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = TRIAGE_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    with transaction() as conn:
        row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not row:
            raise ValueError(f"Project '{slug}' not found.")
        project_id = int(row[0])

        for r in results:
            track = r["track"]
            artefact_md = r.get("artefact_md", "")
            (project_dir / f"{track}.md").write_text(artefact_md, encoding="utf-8")

            conn.execute(
                """
                INSERT INTO triage (project_id, track, status, artefact_md, signed_by, signed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, track) DO UPDATE SET
                    status = excluded.status,
                    artefact_md = excluded.artefact_md,
                    signed_by = excluded.signed_by,
                    signed_at = CURRENT_TIMESTAMP
                """,
                (project_id, track, r["status"], artefact_md, r.get("signed_by", current_actor())),
            )

        # Gate decision: update project status if all clear
        new_status = "triage" if overall == "ok" else "charter"
        conn.execute(
            "UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, project_id),
        )

        audit(
            conn,
            action="triage.aggregate",
            target_type="project",
            target_id=project_id,
            payload={"overall": overall, "blockers": blockers, "warnings": warnings},
        )

    summary_md = render_summary_md(slug, project_id, overall, results, blockers, warnings)
    summary_path = project_dir / "_summary.md"
    summary_path.write_text(summary_md, encoding="utf-8")

    return {
        "project_id": project_id,
        "slug": slug,
        "overall_status": overall,
        "blockers": blockers,
        "warnings": warnings,
        "summary_path": str(summary_path),
        "tracks": {r["track"]: r["status"] for r in results},
    }


def render_summary_md(
    slug: str, project_id: int, overall: str, results: list[dict[str, Any]],
    blockers: list[str], warnings: list[str],
) -> str:
    rows = "\n".join(
        f"| {r['track']} | {r['status']} | {r.get('signed_by', '—')} | {r.get('rationale', '—')} |"
        for r in results
    )
    block_section = ""
    if blockers:
        block_section = "\n## Blockers\n\n" + "\n".join(f"- {b}" for b in blockers) + "\n"
    warn_section = ""
    if warnings:
        warn_section = "\n## Warnings\n\n" + "\n".join(f"- {w}" for w in warnings) + "\n"

    next_step = (
        "`/pflanzer-session-1 " + slug + "` — Session 1 orchestrator." if overall == "ok"
        else "**Session 1 odložena.** Vyřešte blockers a spusťte `/pflanzer-triage " + slug + "` znovu."
    )

    return f"""# Pre-flight Triage — {slug}

> Project ID: {project_id} · Overall: **{overall.upper()}**
> Per ADR-0002 (Pre-flight triage tracks).

| Track | Status | Signed by | Rationale |
|-------|--------|-----------|-----------|
{rows}
{block_section}{warn_section}
## Next step

{next_step}
"""


# --------------------------------------------------------------------------
# Ship gate — triage hard gate (audit N5)
# --------------------------------------------------------------------------

# Risk profiles where the Ship gate refuses production_ready without signed
# triage. Throwaway never ships, so it is not gated.
SHIP_GATED_PROFILES = ("pilot", "production")
TRIAGE_OVERRIDE_MARKER = "pflanzer:triage-override"
_OVERRIDE_RE = re.compile(r"<!-- " + re.escape(TRIAGE_OVERRIDE_MARKER) + r" (\{.*?\}) -->")

# DB status -> display status used in SHIP.md / readiness report.
_DISPLAY_STATUS = {"ok": "ok", "deferred": "deferred", "blocked": "failed",
                   "pending": "pending"}


def derive_risk_profile(
    *, throwaway_or_evolve: str | None, production_readiness_target: int | None,
    capacity_profile: str | None = None, explicit: str | None = None,
) -> str:
    """Return 'throwaway' | 'pilot' | 'production'.

    `projects` has no dedicated risk_profile column (quick_session maps the
    profile onto Charter fields), so it is reconstructed from them:
    throwaway = throwaway_or_evolve='throwaway' or readiness target 0;
    production = regulated/audit-grade capacity or target >= 85; else pilot.
    An explicit `risk_profile` column wins if a later migration adds one.
    """
    if explicit in ("throwaway", "pilot", "production"):
        return explicit
    target = production_readiness_target
    if throwaway_or_evolve == "throwaway" or (target is not None and int(target) == 0):
        return "throwaway"
    if capacity_profile in ("regulated", "audit-grade") or (target is not None and int(target) >= 85):
        return "production"
    return "pilot"


def load_risk_profile(conn: sqlite3.Connection, project_id: int) -> str:
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise ValueError(f"Project id={project_id} not found.")
    keys = row.keys()
    return derive_risk_profile(
        throwaway_or_evolve=row["throwaway_or_evolve"],
        production_readiness_target=row["production_readiness_target"],
        capacity_profile=row["capacity_profile"],
        explicit=row["risk_profile"] if "risk_profile" in keys else None,
    )


def triage_tracks(conn: sqlite3.Connection, project_id: int) -> list[dict[str, Any]]:
    """Per-track triage state; a missing row is reported as status 'missing'."""
    rows = {
        r[0]: r for r in conn.execute(
            "SELECT track, status, signed_by, signed_at FROM triage WHERE project_id = ?",
            (project_id,),
        ).fetchall()
    }
    out: list[dict[str, Any]] = []
    for track in EXPECTED_TRACKS:
        r = rows.get(track)
        status = r[1] if r else "missing"
        out.append({
            "track": track,
            "status": status,
            "display": _DISPLAY_STATUS.get(status, status),
            "signed_by": (r[2] if r else None),
            "signed_at": (r[3] if r else None),
        })
    return out


def _latest_override(conn: sqlite3.Connection, project_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, body_md, atribuce_user, atribuce_ts FROM decisions "
        "WHERE project_id = ? AND type = 'triage' AND body_md LIKE ? "
        "ORDER BY id DESC LIMIT 1",
        (project_id, f"%{TRIAGE_OVERRIDE_MARKER}%"),
    ).fetchone()
    if not row:
        return None
    m = _OVERRIDE_RE.search(row[1] or "")
    payload = json.loads(m.group(1)) if m else {}
    return {
        "decision_id": int(row[0]),
        "blocked_by": list(payload.get("blocked_by", [])),
        "rationale": payload.get("rationale", ""),
        "by": row[2],
        "at": row[3],
    }


def ship_triage_gate(conn: sqlite3.Connection, project_id: int) -> dict[str, Any]:
    """Evaluate the triage hard gate for the Ship gate.

    For pilot/production every track must be 'ok'; anything else (deferred,
    pending, blocked, missing row) blocks production_ready. A Decider
    override only counts if it covers every current blocker (a new blocker
    after the override re-blocks).
    """
    risk = load_risk_profile(conn, project_id)
    tracks = triage_tracks(conn, project_id)
    gated = risk in SHIP_GATED_PROFILES
    raw_blockers = (
        [f"triage:{t['track']} {t['display']}" for t in tracks if t["status"] != "ok"]
        if gated else []
    )
    override = _latest_override(conn, project_id) if raw_blockers else None
    covered = bool(override) and set(raw_blockers) <= set(override["blocked_by"])
    return {
        "risk_profile": risk,
        "gated": gated,
        "tracks": tracks,
        "raw_blocked_by": raw_blockers,
        "blocked_by": [] if covered else raw_blockers,
        "override": override if covered else None,
    }


def record_triage_override(
    conn: sqlite3.Connection, *, project_id: int, slug: str,
    blocked_by: list[str], rationale: str, actor: str | None = None,
) -> int:
    """Persist a Decider override of the triage gate (decisions + audit log)."""
    if not rationale or not rationale.strip():
        raise ValueError(
            "--override-triage vyžaduje --rationale \"…\" (DORA / AI Act čl. 14)."
        )
    actor = actor or current_actor()
    payload = {"blocked_by": blocked_by, "rationale": rationale.strip()}
    body = (
        f"# Triage override (Ship gate) — {slug}\n\n"
        f"<!-- {TRIAGE_OVERRIDE_MARKER} {json.dumps(payload, ensure_ascii=False)} -->\n\n"
        f"**Decider override:** production_ready povoleno i přes nedokončený triage.\n\n"
        f"**Blokace, které override pokrývá:** {', '.join(blocked_by)}\n\n"
        f"**Rationale:** {rationale.strip()}\n\n"
        f"**Atribuce:** {actor}\n"
    )
    cur = conn.execute(
        "INSERT INTO decisions (project_id, type, body_md, atribuce_user, atribuce_ts) "
        "VALUES (?, 'triage', ?, ?, CURRENT_TIMESTAMP)",
        (project_id, body, actor),
    )
    audit(
        conn, actor=actor, action="ship_gate.triage_override",
        target_type="project", target_id=project_id,
        payload={"slug": slug, **payload, "decision_id": cur.lastrowid},
    )
    return int(cur.lastrowid)


def run_from_json(path: Path) -> dict[str, Any]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    return aggregate(spec["slug"], spec["results"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--spec", type=Path, required=True, help="JSON spec with 4 triage results")
    args = parser.parse_args()
    print(json.dumps(run_from_json(args.spec), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
