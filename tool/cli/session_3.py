"""Session 3 — Production hardening (post-Decider's Go).

Cíl: po Session 2 (status='handoff') projet kód shortlistovaných variant
přes quality gates. Pokud score >= production_readiness_target → produkt
je připravený k deployu. Pokud ne → wizard navrhne, co dohardit.

Flow:
1. Load shortlist z Session 2 decision.
2. Pro každou shortlist variantu: extract code (pokud ještě ne) → run gates.
3. Aggregate scores. Vyber **winner** = highest score (tie-break = original
   preference_score z Session 1).
4. Pokud winner.score >= target → production_ready=true.
5. Pokud ne → vrátí actionable list co dofixovat (per gate).

Output: production_readiness_report.md + status update na 'handoff' (zůstává;
to že kod je ready neznamená, že je deployed — handoff package + actual deploy
je responsibility devops).
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
from tool.cli.extract import extract  # noqa: E402
from tool.cli.quality_gates import run_all as run_gates  # noqa: E402

REPORTS_DIR = REPO_ROOT / "data" / "production_reports"


def hardening_run(
    *, slug: str, variant_repo_urls: dict[str, str] | None = None,
    extract_method_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run hardening pipeline for a project's shortlist variants.

    Args:
        slug: project slug.
        variant_repo_urls: variant_name → GitHub URL (z buildru).
                          Pokud chybí, fallback skeleton.
        extract_method_overrides: variant_name → method ('skeleton'|'git_clone'|'manual_paste').
    """
    variant_repo_urls = variant_repo_urls or {}
    extract_method_overrides = extract_method_overrides or {}

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, production_readiness_target, name, target_repo_url "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status, target, name, _target_repo = (
            int(proj[0]), proj[1], int(proj[2] or 80), proj[3], proj[4],
        )
        if status != "handoff":
            raise ValueError(
                f"Project status='{status}'. Session 3 vyžaduje 'handoff' "
                f"(spusť `/pflanzer-session-2 {slug}` nejdřív + Decider Go)."
            )

        # Load shortlist from latest Session 2 decision (heuristic: parse from body_md)
        # Pokud chybí, use top variants by preference_score
        sess1 = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1",
            (project_id,),
        ).fetchone()
        if not sess1:
            raise ValueError(f"No Session 1 for {slug}")
        variants = conn.execute(
            "SELECT id, name, builder, prototype_url, preference_score "
            "FROM variants WHERE session_id = ? ORDER BY preference_score DESC",
            (sess1[0],),
        ).fetchall()
        if not variants:
            raise ValueError(f"No variants for {slug}")

    # MVP: hardenuj všechny varianty (Decider's shortlist v0 — TODO parse z decision body_md)
    per_variant_results: list[dict[str, Any]] = []
    for v in variants:
        v_id, v_name, builder, prev_url, pref = (
            int(v[0]), v[1], v[2], v[3], float(v[4] or 0),
        )

        # Extract (idempotent — extract.py handles re-run)
        extract_result = extract(
            slug=slug, variant_name=v_name,
            source_url=prev_url, repo_url=variant_repo_urls.get(v_name),
            method_override=extract_method_overrides.get(v_name),
        )

        # Run gates
        gate_result = run_gates(extract_result["extracted_id"])

        per_variant_results.append({
            "variant": v_name,
            "builder": builder,
            "preference_score": pref,
            "extraction": extract_result,
            "gates": gate_result,
        })

    # Pick winner
    winner = max(per_variant_results, key=lambda r: (
        r["gates"]["gate_score"], r["preference_score"],
    ))
    production_ready = winner["gates"]["gate_score"] >= target

    # Persist + audit. Re-write gate_score_latest s WINNER score (quality_gates
    # ho přepisuje per variant, takže poslední run by jinak byl B nebo C).
    with transaction() as conn:
        conn.execute(
            "UPDATE projects SET gate_score_latest = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            (winner["gates"]["gate_score"], project_id),
        )
        audit(
            conn, action="session_3.hardening",
            target_type="project", target_id=project_id,
            payload={
                "slug": slug,
                "variants_tested": [r["variant"] for r in per_variant_results],
                "winner": winner["variant"],
                "winner_score": winner["gates"]["gate_score"],
                "target": target,
                "production_ready": production_ready,
            },
        )

    # Render report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{slug}-readiness.md"
    report_path.write_text(
        _render_report(slug, name, target, per_variant_results, winner, production_ready),
        encoding="utf-8",
    )

    return {
        "slug": slug,
        "production_readiness_target": target,
        "winner": {
            "variant": winner["variant"],
            "builder": winner["builder"],
            "gate_score": winner["gates"]["gate_score"],
            "production_ready": production_ready,
            "local_path": winner["extraction"]["local_path"],
            "next_step": _next_step(winner, production_ready, slug),
        },
        "per_variant": [
            {
                "variant": r["variant"],
                "builder": r["builder"],
                "preference_score": r["preference_score"],
                "gate_score": r["gates"]["gate_score"],
                "production_ready": r["gates"]["gate_score"] >= target,
                "local_path": r["extraction"]["local_path"],
                "files": r["extraction"]["files_count"],
                "loc": r["extraction"]["total_loc"],
                "method": r["extraction"]["method"],
            }
            for r in per_variant_results
        ],
        "report_path": str(report_path.relative_to(REPO_ROOT)),
    }


def _next_step(winner: dict[str, Any], ready: bool, slug: str) -> str:
    if ready:
        return (
            f"`/pflanzer-handoff {slug}` — generate per-role handoff package "
            f"s odkazy na extracted/{winner['variant']}/. Většina kódu je ready."
        )
    fails = [g["gate"] for g in winner["gates"]["results"] if g["status"] == "fail"]
    return (
        f"Score {winner['gates']['gate_score']}/{winner['gates']['target']} — pilot-only. "
        f"Fix gates: {', '.join(fails) or 'see report'}. "
        f"Pak re-run: `python3 tool/cli/quality_gates.py --extracted-id {winner['extraction']['extracted_id']}`."
    )


def _render_report(
    slug: str, name: str, target: int,
    per_variant: list[dict[str, Any]], winner: dict[str, Any],
    ready: bool,
) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    var_table = "\n".join(
        f"| {r['variant']} | `{r['builder']}` | {r['preference_score']:.2f} | "
        f"**{r['gates']['gate_score']}** | "
        f"{'🚀 ready' if r['gates']['gate_score'] >= target else '⚠ pilot-only'} | "
        f"{r['extraction']['files_count']} files / {r['extraction']['total_loc']} LOC | "
        f"`{r['extraction']['method']}` |"
        for r in per_variant
    )

    winner_gates = "\n".join(
        f"- {g['status'].upper()} **{g['gate']}**: {g['details'][:100]}"
        for g in winner["gates"]["results"]
    )

    verdict_block = ""
    if ready:
        verdict_block = f"""## 🚀 Production-ready

Winner: **variant {winner['variant']}** (`{winner['builder']}`, score {winner['gates']['gate_score']}/100).

Code je v `{winner['extraction']['local_path']}/`. Většinu lze použít přímo.

### Next 24 h
1. `cd {winner['extraction']['local_path']} && npm install && npm run dev` — sanity check.
2. `/pflanzer-handoff {slug}` — vygeneruj per-role handoff package.
3. Open PR ze {winner['extraction']['local_path']}/ do `target_repo_url`
   (per Charter target_branch).
4. CI green → merge → deploy preview.
"""
    else:
        verdict_block = f"""## ⚠ Pilot-only — gates pod target

Winner: **variant {winner['variant']}** (`{winner['builder']}`, score {winner['gates']['gate_score']}/100; target {target}).

Před production launch dofix gates pod failed status. Po fixu:
```bash
python3 tool/cli/quality_gates.py --extracted-id {winner['extraction']['extracted_id']}
```

### Pilot scope
- Smí jít do **5-20 reálných uživatelů** v sandboxu (per Charter risk profile).
- Production launch BLOCKED pokud kterékoliv security gate = fail.
"""

    return f"""# Production readiness — {name}

> Slug: `{slug}` · Generated: {today} · Target: {target}/100

## Per-variant gates

| Variant | Builder | Pref score | Gate score | Status | Code | Method |
|---------|---------|------------|------------|--------|------|--------|
{var_table}

{verdict_block}

## Winner gate breakdown

{winner_gates}

## Methodology note

Per Charter `production_readiness_target = {target}/100`. Score = weighted
average across 7 gates (lint / types / tests / security / a11y / build /
observability). Security a tests mají nejvyšší váhu (2.0×) — gate fail v nich
je production blocker.

Detailní per-gate report: `data/handoffs/{slug}/quality-{winner['variant']}.md`.
"""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--repo-urls", default=None,
                   help="JSON dict variant_name→GitHub URL")
    p.add_argument("--method-overrides", default=None,
                   help="JSON dict variant_name→method")
    args = p.parse_args()

    repo_urls = json.loads(args.repo_urls) if args.repo_urls else None
    method_overrides = json.loads(args.method_overrides) if args.method_overrides else None

    out = hardening_run(slug=args.slug, variant_repo_urls=repo_urls,
                        extract_method_overrides=method_overrides)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
