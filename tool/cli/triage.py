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
