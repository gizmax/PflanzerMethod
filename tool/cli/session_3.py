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

Ship gate (formerly "Session 3") is a pipeline, not a meeting (audit N3/N5):
- code is taken from the variant worktrees created by `worktree.py setup`
  (autodetected, gates run in place); hosted URLs / skeleton are fallbacks,
  see `extract.plan_extraction`,
- triage hard gate: for pilot/production risk profiles every triage track
  must be 'ok', otherwise production_ready=false with `blocked_by`; the
  Decider can override only via `--override-triage --rationale "..."`
  (decisions row + audit log).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.extract import ExtractionError, extract, plan_extraction  # noqa: E402
from tool.cli.quality_gates import aggregate_score  # noqa: E402
from tool.cli.quality_gates import run_all as run_gates  # noqa: E402
from tool.cli.triage import record_triage_override, ship_triage_gate  # noqa: E402

REPORTS_DIR = REPO_ROOT / "data" / "production_reports"
BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"


def hardening_run(
    *, slug: str, variant_repo_urls: dict[str, str] | None = None,
    extract_method_overrides: dict[str, str] | None = None,
    override_triage: bool = False, override_rationale: str | None = None,
) -> dict[str, Any]:
    """Run hardening pipeline for a project's shortlist variants.

    Args:
        slug: project slug.
        variant_repo_urls: variant_name → GitHub URL (z hosted buildru).
                          Použije se jen, když worktree varianty neexistuje.
        extract_method_overrides: variant_name → method
                          ('worktree'|'git_clone'|'skeleton'|'manual_paste').
        override_triage: Decider override triage hard gate (needs rationale).
        override_rationale: povinné zdůvodnění override do decision logu.
    """
    variant_repo_urls = variant_repo_urls or {}
    extract_method_overrides = extract_method_overrides or {}
    if override_triage and not (override_rationale or "").strip():
        raise ValueError(
            "--override-triage vyžaduje --rationale \"…\" (zapisuje se do decision logu)."
        )

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, production_readiness_target, name, target_repo_url "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status, target, name, _target_repo = (
            int(proj[0]), proj[1], int(proj[2] if proj[2] is not None else 80), proj[3], proj[4],
        )
        if status != "handoff":
            raise ValueError(
                f"Project status='{status}'. Ship gate vyžaduje 'handoff' "
                f"(spusť `/pm decide {slug}` nejdřív + Decider Go)."
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

        triage_gate = ship_triage_gate(conn, project_id)

    risk_profile = triage_gate["risk_profile"]

    # Fail loud before running any gate: every variant needs a usable source
    # (worktree > hosted URL > skeleton for throwaway). See extract.plan_extraction.
    for v in variants:
        plan_extraction(
            slug=slug, variant_name=v[1], builder=v[2], risk_profile=risk_profile,
            repo_url=variant_repo_urls.get(v[1]),
            method_override=extract_method_overrides.get(v[1]),
        )

    if triage_gate["blocked_by"]:
        if override_triage:
            with transaction() as conn:
                record_triage_override(
                    conn, project_id=project_id, slug=slug,
                    blocked_by=triage_gate["raw_blocked_by"],
                    rationale=override_rationale or "",
                )
                triage_gate = ship_triage_gate(conn, project_id)
        else:
            print(
                f"[ship gate] Blokováno triage ({', '.join(triage_gate['blocked_by'])}) — "
                f"production_ready bude false. Spusť `/pm triage {slug}`.",
                file=sys.stderr,
            )

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

        # Run gates (in place for worktrees)
        gate_result = _run_gates(extract_result, target)

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
    gate_ready = winner["gates"]["gate_score"] >= target
    blocked_by = list(triage_gate["blocked_by"])
    production_ready = gate_ready and not blocked_by

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
                "gate_ready": gate_ready,
                "production_ready": production_ready,
                "risk_profile": risk_profile,
                "blocked_by": blocked_by,
                "triage_override_decision_id": (
                    triage_gate["override"]["decision_id"] if triage_gate["override"] else None
                ),
                "methods": {r["variant"]: r["extraction"]["method"] for r in per_variant_results},
            },
        )

    # Render report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{slug}-readiness.md"
    report_path.write_text(
        _render_report(slug, name, target, per_variant_results, winner, production_ready,
                       triage_gate),
        encoding="utf-8",
    )

    return {
        "slug": slug,
        "risk_profile": risk_profile,
        "production_readiness_target": target,
        "production_ready": production_ready,
        "blocked_by": blocked_by,
        "triage": {
            "gated": triage_gate["gated"],
            "tracks": {t["track"]: t["display"] for t in triage_gate["tracks"]},
            "override": triage_gate["override"],
        },
        "winner": {
            "variant": winner["variant"],
            "builder": winner["builder"],
            "gate_score": winner["gates"]["gate_score"],
            "gate_ready": gate_ready,
            "production_ready": production_ready,
            "blocked_by": blocked_by,
            "local_path": winner["extraction"]["local_path"],
            "next_step": _next_step(winner, production_ready, slug, blocked_by),
        },
        "per_variant": [
            {
                "variant": r["variant"],
                "builder": r["builder"],
                "preference_score": r["preference_score"],
                "gate_score": r["gates"]["gate_score"],
                "gate_ready": r["gates"]["gate_score"] >= target,
                "local_path": r["extraction"]["local_path"],
                "files": r["extraction"]["files_count"],
                "loc": r["extraction"]["total_loc"],
                "method": r["extraction"]["method"],
            }
            for r in per_variant_results
        ],
        "report_path": str(report_path.relative_to(REPO_ROOT)),
    }


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _run_gates(extraction: dict[str, Any], target: int) -> dict[str, Any]:
    """Run quality gates for one extraction.

    Compatibility shim: `quality_gates.run_all` persists the gate rows and
    then reports `local_path` relative to the meta-repo, which raises for
    worktrees outside it (`~/.pflanzer/targets/...`). In that case rebuild
    the result from the persisted rows instead of aborting the Ship gate.
    Drop once run_all handles absolute paths.
    """
    extracted_id = extraction["extracted_id"]
    try:
        return run_gates(extracted_id)
    except ValueError:
        if _inside_repo(Path(extraction["absolute_path"])):
            raise
        with transaction() as conn:
            rows = conn.execute(
                "SELECT gate_type, status, details_md, metric_value "
                "FROM quality_gates WHERE extracted_id = ? ORDER BY id",
                (extracted_id,),
            ).fetchall()
        if not rows:
            raise
        results = [SimpleNamespace(gate_type=r[0], status=r[1]) for r in rows]
        score_info = aggregate_score(results)  # type: ignore[arg-type]
        return {
            "extracted_id": extracted_id,
            "variant": extraction["variant"],
            "local_path": extraction["local_path"],
            "gate_score": score_info["gate_score"],
            "target": target,
            "production_ready": score_info["gate_score"] >= target,
            "counts": score_info["counts"],
            "results": [
                {"gate": r[0], "status": r[1], "metric": r[3], "details": (r[2] or "")[:200]}
                for r in rows
            ],
        }


def _next_step(winner: dict[str, Any], ready: bool, slug: str,
               blocked_by: list[str] | None = None) -> str:
    if blocked_by:
        return (
            f"Blokováno: spusť `/pm triage {slug}` ({', '.join(blocked_by)}). "
            f"Gate score {winner['gates']['gate_score']}/{winner['gates']['target']}. "
            f"Decider override jen s rationale: `python3 tool/cli/session_3.py --slug {slug} "
            f"--override-triage --rationale \"…\"`."
        )
    if ready:
        return (
            f"`/pm handoff {slug}` — SHIP.md + gh pr create z worktree "
            f"{winner['extraction']['local_path']}. Většina kódu je ready."
        )
    fails = [g["gate"] for g in winner["gates"]["results"] if g["status"] == "fail"]
    return (
        f"Score {winner['gates']['gate_score']}/{winner['gates']['target']} — pilot-only. "
        f"Fix gates: {', '.join(fails) or 'see report'}. "
        f"Pak re-run: `python3 tool/cli/quality_gates.py --extracted-id {winner['extraction']['extracted_id']}`."
    )


def _render_triage_md(triage_gate: dict[str, Any], slug: str) -> tuple[str, str]:
    """Return (top_block, triage_section) markdown for the readiness report."""
    icons = {"ok": "✅", "deferred": "⏸", "failed": "❌", "pending": "⏳", "missing": "—"}
    rows = "\n".join(
        f"| {t['track']} | {icons.get(t['display'], '?')} {t['display']} | "
        f"{t['signed_by'] or '—'} |"
        for t in triage_gate["tracks"]
    )
    gated_note = (
        f"Risk profil `{triage_gate['risk_profile']}` — triage je hard gate pro production_ready."
        if triage_gate["gated"]
        else f"Risk profil `{triage_gate['risk_profile']}` — triage gate se neuplatňuje."
    )
    override_note = ""
    if triage_gate["override"]:
        o = triage_gate["override"]
        override_note = (
            f"\n**Decider override** (decision #{o['decision_id']}, {o['by']}): "
            f"{o['rationale']}\n"
        )
    section = f"""## Triage stav

{gated_note}

| Track | Stav | Signed by |
|-------|------|-----------|
{rows}
{override_note}"""
    top = ""
    if triage_gate["blocked_by"]:
        top = f"""> ## ⛔ Blokováno: spusť `/pm triage {slug}`
>
> production_ready = **false** bez ohledu na gate score.
> Důvod: {', '.join(f'`{b}`' for b in triage_gate['blocked_by'])}.
> Decider override jen s rationale do decision logu:
> `python3 tool/cli/session_3.py --slug {slug} --override-triage --rationale "…"`
"""
    return top, section


def _render_report(
    slug: str, name: str, target: int,
    per_variant: list[dict[str, Any]], winner: dict[str, Any],
    ready: bool, triage_gate: dict[str, Any],
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

    triage_top, triage_section = _render_triage_md(triage_gate, slug)

    verdict_block = ""
    if triage_gate["blocked_by"]:
        verdict_block = f"""## ⛔ Blokováno triage

Winner: **variant {winner['variant']}** (`{winner['builder']}`, score {winner['gates']['gate_score']}/100; target {target}).

Gate score by {'stačil' if winner['gates']['gate_score'] >= target else 'nestačil'}, ale risk profil
`{triage_gate['risk_profile']}` vyžaduje podepsaný triage ve všech 4 trackách.
Spusť `/pm triage {slug}` a pak Ship gate znovu.
"""
    elif ready:
        verdict_block = f"""## 🚀 Production-ready

Winner: **variant {winner['variant']}** (`{winner['builder']}`, score {winner['gates']['gate_score']}/100).

Code je v `{winner['extraction']['local_path']}/`. Většinu lze použít přímo.

### Next 24 h
1. `cd {winner['extraction']['local_path']} && npm install && npm run dev` — sanity check.
2. `/pm handoff {slug}` — SHIP.md + `gh pr create` (trailery + AI provenance).
3. Open PR z branche `pflanzer/{slug}-{winner['variant']}` do `target_repo_url`
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

    return f"""{BRAND_LINE}

# Ship gate — production readiness — {name}

> Slug: `{slug}` · Generated: {today} · Target: {target}/100 · Risk profil: `{triage_gate['risk_profile']}`

{triage_top}
## Per-variant gates

| Variant | Builder | Pref score | Gate score | Status | Code | Method |
|---------|---------|------------|------------|--------|------|--------|
{var_table}

{verdict_block}

{triage_section}

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
    p = argparse.ArgumentParser(
        description="Ship gate (dříve Session 3) — quality gates ve worktrees + winner + triage hard gate.",
    )
    p.add_argument("--slug", required=True)
    p.add_argument("--repo-urls", default=None,
                   help="JSON dict variant_name→GitHub URL (jen hosted buildery bez worktree)")
    p.add_argument("--method-overrides", default=None,
                   help="JSON dict variant_name→method (worktree|git_clone|skeleton|manual_paste)")
    p.add_argument("--override-triage", action="store_true",
                   help="Decider override triage hard gate (vyžaduje --rationale)")
    p.add_argument("--rationale", default=None,
                   help="Zdůvodnění override do decision logu (povinné s --override-triage)")
    args = p.parse_args()

    if args.override_triage and not (args.rationale or "").strip():
        p.error("--override-triage vyžaduje --rationale \"…\"")

    try:
        repo_urls = json.loads(args.repo_urls) if args.repo_urls else None
        method_overrides = json.loads(args.method_overrides) if args.method_overrides else None
        out = hardening_run(slug=args.slug, variant_repo_urls=repo_urls,
                            extract_method_overrides=method_overrides,
                            override_triage=args.override_triage,
                            override_rationale=args.rationale)
    except (ExtractionError, ValueError) as exc:
        print(f"{BRAND_LINE}\n\n✖ Ship gate zastaven: {exc}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
