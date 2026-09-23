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
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.extract import (  # noqa: E402
    WORKTREE_METHODS, ExtractionError, base_gates_adapter, extract, plan_extraction,
)
from tool.cli.quality_gates import GATE_TYPES  # noqa: E402
from tool.cli.quality_gates import run_all as run_gates  # noqa: E402
from tool.cli.triage import record_triage_override, ship_triage_gate  # noqa: E402

REPORTS_DIR = REPO_ROOT / "data" / "production_reports"
BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"
# Minimum evidence for a production verdict: at least MIN_GATES_RUN gates
# actually executed (pass/warn/fail) and build + tests among them.
MIN_GATES_RUN = 4
REQUIRED_GATES = ("build", "tests")
RAN_STATUSES = ("pass", "warn", "fail")


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
            "SELECT id, status, production_readiness_target, name, target_repo_url, "
            "target_branch FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status, target, name, _target_repo = (
            int(proj[0]), proj[1], int(proj[2] if proj[2] is not None else 80), proj[3], proj[4],
        )
        target_branch = proj[5] or "main"
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

        # Adapter integrity: gate commands come from the BASE branch, never
        # from the variant branch the agent could have edited.
        adapter: dict[str, Any] = {"adapter_path": None, "tmp_dir": None, "warnings": []}
        if extract_result["method"] in WORKTREE_METHODS:
            adapter = base_gates_adapter(Path(extract_result["absolute_path"]), target_branch)
        try:
            # Run gates (in place for worktrees)
            gate_result = _run_gates(extract_result, target, adapter)
        finally:
            if adapter.get("tmp_dir"):
                shutil.rmtree(adapter["tmp_dir"], ignore_errors=True)

        per_variant_results.append({
            "variant": v_name,
            "builder": builder,
            "preference_score": pref,
            "extraction": extract_result,
            "gates": gate_result,
            "sufficiency": gates_sufficiency(gate_result),
            "adapter": {
                "source": (f"{adapter.get('base_ref')}:{adapter.get('name')}"
                           if adapter.get("adapter_path") else "autodetect"),
                "warnings": adapter["warnings"],
            },
        })

    # Pick winner
    winner = max(per_variant_results, key=lambda r: (
        r["gates"]["gate_score"], r["preference_score"],
    ))
    gate_ready = winner["gates"]["gate_score"] >= target
    blocked_by = list(triage_gate["blocked_by"])
    if not winner["sufficiency"]["sufficient"]:
        blocked_by.append(winner["sufficiency"]["blocker"])
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
                "gates_run": {r["variant"]: r["sufficiency"]["gates_run"] for r in per_variant_results},
                "adapter": {r["variant"]: r["adapter"] for r in per_variant_results},
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
                "gates_run": r["sufficiency"]["gates_run"],
                "gates_sufficient": r["sufficiency"]["sufficient"],
                "adapter": r["adapter"],
                "local_path": r["extraction"]["local_path"],
                "files": r["extraction"]["files_count"],
                "loc": r["extraction"]["total_loc"],
                "method": r["extraction"]["method"],
            }
            for r in per_variant_results
        ],
        "report_path": str(report_path.relative_to(REPO_ROOT)),
    }


def gates_sufficiency(gate_result: dict[str, Any]) -> dict[str, Any]:
    """Minimum evidence for a production verdict.

    Needs >= MIN_GATES_RUN executed gates (pass/warn/fail) and build + tests
    among them; skipped/unsupported gates do not count. Uses `gates_run` from
    quality_gates when present, otherwise derives it from `results`.
    """
    ran = [g["gate"] for g in gate_result.get("results", []) if g["status"] in RAN_STATUSES]
    gates_run = gate_result.get("gates_run")
    if isinstance(gates_run, (list, tuple, set)):
        ran = list(gates_run)
        gates_run = len(ran)
    elif not isinstance(gates_run, int):
        gates_run = len(ran)
    missing = [g for g in REQUIRED_GATES if g not in ran]
    sufficient = gates_run >= MIN_GATES_RUN and not missing
    detail = f"{gates_run}/{len(GATE_TYPES)} run"
    if missing:
        detail += f", missing: {', '.join(missing)}"
    elif gates_run < MIN_GATES_RUN:
        detail += f", min {MIN_GATES_RUN}"
    return {
        "gates_run": gates_run,
        "missing": missing,
        "sufficient": sufficient,
        "blocker": None if sufficient else f"gates:insufficient ({detail})",
    }


def _run_gates(extraction: dict[str, Any], target: int,
               adapter: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run quality gates for one extraction (in place for worktrees).

    `adapter["adapter_path"]` is the base-branch adapter (see
    `extract.base_gates_adapter`); None means autodetection.
    """
    adapter_path = (adapter or {}).get("adapter_path")
    return run_gates(extraction["extracted_id"], adapter_path=adapter_path)


def _next_step(winner: dict[str, Any], ready: bool, slug: str,
               blocked_by: list[str] | None = None) -> str:
    if blocked_by:
        parts: list[str] = []
        triage_b = [b for b in blocked_by if b.startswith("triage:")]
        gates_b = [b for b in blocked_by if b.startswith("gates:")]
        if triage_b:
            parts.append(
                f"Blokováno: spusť `/pm triage {slug}` ({', '.join(triage_b)}). "
                f"Decider override jen s rationale: `python3 tool/cli/session_3.py --slug {slug} "
                f"--override-triage --rationale \"…\"`."
            )
        if gates_b:
            parts.append(
                f"{', '.join(gates_b)} — doplň `pflanzer.gates.yml` v base branchi target repa "
                "(viz tool/templates/README-gates.md) a spusť Ship gate znovu."
            )
        parts.append(f"Gate score {winner['gates']['gate_score']}/{winner['gates']['target']}.")
        return " ".join(parts)
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
        f"{r['sufficiency']['gates_run']}/{len(GATE_TYPES)}"
        f"{'' if r['sufficiency']['sufficient'] else ' ⛔'} | "
        f"{r['extraction']['files_count']} files / {r['extraction']['total_loc']} LOC | "
        f"`{r['extraction']['method']}` | {r['adapter']['source']} |"
        for r in per_variant
    )
    adapter_warnings = "\n".join(
        f"- ⚠ **{r['variant']}**: {w}" for r in per_variant for w in r["adapter"]["warnings"]
    )
    adapter_section = (
        f"## Gate adaptér — integrita\n\n{adapter_warnings}\n" if adapter_warnings else ""
    )
    suff = winner["sufficiency"]
    gates_block = ""
    if not suff["sufficient"]:
        gates_block = f"""## ⛔ Nedostatek gates pro verdikt

`{suff['blocker']}` — production_ready vyžaduje ≥ {MIN_GATES_RUN} spuštěné gates
(pass/warn/fail) a mezi nimi `build` i `tests`. Skipped / unsupported gates
se nepočítají. Doplň příkazy do `pflanzer.gates.yml` v **base branchi** target
repa (`pflanzer init gates-template --path <repo>`, viz
`tool/templates/README-gates.md`) a spusť Ship gate znovu.
"""

    winner_gates = "\n".join(
        f"- {g['status'].upper()} **{g['gate']}**: {g['details'][:100]}"
        for g in winner["gates"]["results"]
    )

    triage_top, triage_section = _render_triage_md(triage_gate, slug)

    verdict_block = ""
    if triage_gate["blocked_by"] or not suff["sufficient"]:
        verdict_block = gates_block
    if triage_gate["blocked_by"]:
        verdict_block += f"""## ⛔ Blokováno triage

Winner: **variant {winner['variant']}** (`{winner['builder']}`, score {winner['gates']['gate_score']}/100; target {target}).

Gate score by {'stačil' if winner['gates']['gate_score'] >= target else 'nestačil'}, ale risk profil
`{triage_gate['risk_profile']}` vyžaduje podepsaný triage ve všech 4 trackách.
Spusť `/pm triage {slug}` a pak Ship gate znovu.
"""
    elif not suff["sufficient"]:
        pass  # gates_block already explains the blocker
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

| Variant | Builder | Pref score | Gate score | Status | Gates run | Code | Method | Adaptér |
|---------|---------|------------|------------|--------|-----------|------|--------|---------|
{var_table}

{verdict_block}

{adapter_section}
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
