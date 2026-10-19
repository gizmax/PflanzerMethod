"""Ship (v0.5; příkaz `pflanzer session_3`) — quality gates na vítěze po Go.

Ship není session, je to práce vývojářů s automatickými branami + 20min
checkpoint provozu (ADR-0021). Tento modul:

1. Zjistí, co hardenovat: **jen vítěze z Rozhodnutí** (`session_2 decide go --winner X`).
   Fallback: shortlist z Buildu, pak varianta s nejvyšším skóre. `--variants A,B` je
   explicitní override (např. porovnání dvou kandidátů).
2. Zaregistruje kód varianty (výchozí metoda `in_repo_branch` = existující větev ve
   worktree; skeleton se nespouští, pokud worktree existuje).
3. Pustí stack-aware quality gates (`quality_gates.py`) a porovná skóre s prahem projektu
   (`projects.production_readiness_target`: pilot 80 / production 85 / throwaway 0).
4. Zapíše report `<DATA_ROOT>/production_reports/<slug>-readiness.md` a (je-li cwd
   target repo s `.pflanzer/`) sekci Ship do decision logu.

Rozhraní:
    pflanzer session_3 --slug S [--variants A[,B]] [--checkpoint "Provoz: ok (Karel, on-call)"]...
                       [--repo-urls JSON] [--method-overrides JSON]
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

from tool.cli.db import audit, display_path, transaction  # noqa: E402
from tool.cli.extract import BRAND, DATA_ROOT, extract  # noqa: E402
from tool.cli.quality_gates import run_all as run_gates, verdict_label  # noqa: E402
from tool.cli.session_2 import get_shortlist, get_winner, write_repo_decision_log  # noqa: E402

REPORTS_DIR = DATA_ROOT / "production_reports"


def _select_variants(
    conn: Any, project_id: int, explicit: list[str] | None,
) -> tuple[list[tuple[int, str, str, float]], str, str | None]:
    """Vrátí (varianty k hardeningu, zdroj výběru, vítěz z rozhodnutí)."""
    sess1 = conn.execute(
        "SELECT id FROM sessions WHERE project_id = ? AND type = 1", (project_id,),
    ).fetchone()
    if not sess1:
        raise ValueError("Projekt nemá žádný Build (varianty). Spusť `/pm build` nejdřív.")
    rows = conn.execute(
        "SELECT id, name, builder, preference_score FROM variants "
        "WHERE session_id = ? ORDER BY preference_score DESC", (sess1[0],),
    ).fetchall()
    if not rows:
        raise ValueError("Build nemá žádné varianty.")
    by_name = {r[1]: (int(r[0]), r[1], r[2], float(r[3] or 0)) for r in rows}
    decided = get_winner(conn, project_id)

    if explicit:
        names, source = explicit, "explicit (--variants)"
    elif decided and decided in by_name:
        names, source = [decided], "vítěz z Rozhodnutí"
    elif (sl := [n for n in get_shortlist(conn, project_id) if n in by_name]):
        names, source = sl, "shortlist z Buildu (Rozhodnutí vítěze nezapsalo)"
    else:
        names, source = [rows[0][1]], "nejvyšší skóre z Buildu (bez vítěze a shortlistu)"
    missing = [n for n in names if n not in by_name]
    if missing:
        raise ValueError(f"Varianta {', '.join(missing)} v Buildu neexistuje "
                         f"(jsou: {', '.join(sorted(by_name))}).")
    return [by_name[n] for n in names], source, decided


def hardening_run(
    *, slug: str, variants: list[str] | None = None,
    variant_repo_urls: dict[str, str] | None = None,
    extract_method_overrides: dict[str, str] | None = None,
    checkpoints: list[str] | None = None,
) -> dict[str, Any]:
    """Pusť Ship pro vítěze (nebo explicitně zadané varianty)."""
    variant_repo_urls = variant_repo_urls or {}
    extract_method_overrides = extract_method_overrides or {}
    checkpoints = [c.strip() for c in (checkpoints or []) if c and c.strip()]

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, production_readiness_target, name "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status, name = int(proj[0]), proj[1], proj[3]
        target = int(proj[2]) if proj[2] is not None else 80
        if status != "handoff":
            raise ValueError(
                f"Project status='{status}'. Ship vyžaduje Go v Rozhodnutí "
                f"(`pflanzer session_2 decide --slug {slug} go --winner A --rationale \"…\"`)."
            )
        selected, source, decided = _select_variants(conn, project_id, variants)

    per_variant: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for v_id, v_name, builder, pref in selected:
        try:
            ext = extract(
                slug=slug, variant_name=v_name,
                repo_url=variant_repo_urls.get(v_name),
                method_override=extract_method_overrides.get(v_name),
            )
            gates = run_gates(ext["extracted_id"])
        except (ValueError, RuntimeError, NotImplementedError) as e:
            errors.append({"variant": v_name, "error": str(e)})
            continue
        per_variant.append({"variant": v_name, "builder": builder,
                            "preference_score": pref, "extraction": ext, "gates": gates})

    if not per_variant:
        raise ValueError("Ship se nepodařil: " + "; ".join(
            f"{e['variant']}: {e['error']}" for e in errors))

    # Vítěz = vítěz z Rozhodnutí (pokud byl hardenován), jinak nejlepší skóre
    winner = next((r for r in per_variant if r["variant"] == decided), None) or max(
        per_variant, key=lambda r: (r["gates"]["gate_score"], r["preference_score"]))
    w_score = winner["gates"]["gate_score"]
    low_conf = bool(winner["gates"].get("low_confidence"))
    meets = w_score >= target and not low_conf
    verdict = verdict_label(w_score, target, low_conf)

    with transaction() as conn:
        # run_gates přepisuje gate_score_latest po každé variantě; finální = vítěz
        conn.execute(
            "UPDATE projects SET gate_score_latest = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (w_score, project_id),
        )
        audit(
            conn, action="session_3.hardening",
            target_type="project", target_id=project_id,
            payload={
                "slug": slug, "selection": source,
                "variants_tested": [r["variant"] for r in per_variant],
                "winner": winner["variant"], "winner_score": w_score,
                "target": target, "meets_threshold": meets,
                "errors": errors, "checkpoints": checkpoints,
            },
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{slug}-readiness.md"
    report_md = _render_report(slug, name, target, per_variant, winner, meets,
                               source, errors, checkpoints)
    report_path.write_text(report_md, encoding="utf-8")

    repo_log = write_repo_decision_log(
        slug, _render_log_section(winner, target, verdict, checkpoints), label="Ship")

    out: dict[str, Any] = {
        "slug": slug,
        "selection": source,
        "production_readiness_target": target,
        "winner": {
            "variant": winner["variant"],
            "builder": winner["builder"],
            "branch": winner["extraction"].get("branch"),
            "head_sha": winner["extraction"].get("head_sha"),
            "gate_score": w_score,
            "score_display": f"{w_score}/100 (práh {target})",
            "verdict": verdict,
            "meets_threshold": meets,
            "stack": winner["gates"].get("stack"),
            "applicable_gates": winner["gates"].get("applicable_gates"),
            "total_gates": winner["gates"].get("total_gates"),
            "local_path": winner["extraction"]["local_path"],
            "next_step": _next_step(winner, meets, target, slug),
        },
        "per_variant": [
            {
                "variant": r["variant"],
                "builder": r["builder"],
                "preference_score": r["preference_score"],
                "gate_score": r["gates"]["gate_score"],
                "score_display": f"{r['gates']['gate_score']}/100 (práh {target})",
                "method": r["extraction"]["method"],
                "branch": r["extraction"].get("branch"),
                "files": r["extraction"]["files_count"],
                "diff_loc_added": r["extraction"].get("diff_loc_added"),
            }
            for r in per_variant
        ],
        "errors": errors,
        "report_path": display_path(report_path),
        "decision_log_repo": repo_log,
    }
    return out


def _failing(winner: dict[str, Any]) -> tuple[list[str], list[str]]:
    res = winner["gates"]["results"]
    return ([g["gate"] for g in res if g["status"] == "fail"],
            [g["gate"] for g in res if g["status"] == "warn"])


def _next_step(winner: dict[str, Any], meets: bool, target: int, slug: str) -> str:
    score = winner["gates"]["gate_score"]
    if meets:
        return (f"Skóre {score}/100 (práh {target}). Checkpoint provozu (20 min), pak PR vítěze: "
                f"`pflanzer handoff_pr --slug {slug}` a `/pm handoff {slug}`.")
    fails, warns = _failing(winner)
    return (f"Skóre {score}/100 je pod prahem {target}. Dopravit: "
            f"{', '.join(fails) or 'viz report'}"
            + (f" (varování: {', '.join(warns)})" if warns else "")
            + f". Pak znovu `/pm ship {slug}`, nebo pilot s malou skupinou na Decidera.")


def _render_log_section(winner: dict[str, Any], target: int, verdict: str,
                        checkpoints: list[str]) -> str:
    ext = winner["extraction"]
    lines = [
        "## Ship — quality gates",
        "",
        f"- **Vítěz**: **{winner['variant']}** (větev `{ext.get('branch') or '—'}` "
        f"@ `{(ext.get('head_sha') or '—')[:10]}`)",
        f"- **Skóre**: **{winner['gates']['gate_score']}/100** (práh {target}) — {verdict}",
        f"- **Brány**: {winner['gates'].get('applicable_gates')} z {winner['gates'].get('total_gates')} "
        f"aplikovatelných, stack `{winner['gates'].get('stack')}`",
    ]
    if checkpoints:
        lines += ["", "### Checkpointy", ""] + [f"- {c}" for c in checkpoints]
    return "\n".join(lines) + "\n"


def _render_report(
    slug: str, name: str, target: int,
    per_variant: list[dict[str, Any]], winner: dict[str, Any],
    meets: bool, source: str, errors: list[dict[str, str]], checkpoints: list[str],
) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    w = winner
    w_score = w["gates"]["gate_score"]
    ext = w["extraction"]

    def status_label(score: int) -> str:
        if target <= 0:
            return "informativně"
        return "splňuje práh" if score >= target else "pod prahem"

    var_table = "\n".join(
        f"| {r['variant']} | `{r['builder']}` | {r['preference_score']:.2f} | "
        f"**{r['gates']['gate_score']}/100** | {status_label(r['gates']['gate_score'])} | "
        f"`{r['extraction']['method']}` | {r['extraction'].get('branch') or '—'} |"
        for r in per_variant
    )
    gate_lines = "\n".join(
        f"- `{ {'skipped': 'SKIP', 'unsupported': 'SKIP'}.get(g['status'], g['status'].upper()) }` **{g['gate']}**: {g['details'][:160].replace(chr(10), ' ')}"
        for g in w["gates"]["results"]
    )
    fails, warns = _failing(w)
    if meets and target > 0:
        verdict_block = (
            f"## Verdikt: splňuje práh\n\n"
            f"Vítěz **{w['variant']}** má **{w_score}/100** (práh {target}). Kód je ve větvi "
            f"`{ext.get('branch') or '—'}` @ `{(ext.get('head_sha') or '—')[:10]}`.\n\n"
            f"### Další krok\n"
            f"1. Checkpoint provozu (20 min): deploy plán, monitoring, on-call, rollback.\n"
            f"2. PR vítěze do `{slug}` target repa: `pflanzer handoff_pr --slug {slug}`.\n"
            f"3. `/pm handoff {slug}` — balíček per role a metriky pilotu.\n"
        )
    elif target <= 0:
        verdict_block = (
            f"## Verdikt: informativně (throwaway, práh 0)\n\n"
            f"Skóre **{w_score}/100** nic neblokuje; kód nejde do produkce.\n"
        )
    else:
        verdict_block = (
            f"## Verdikt: pod prahem\n\n"
            f"Vítěz **{w['variant']}** má **{w_score}/100**, práh je {target}. "
            f"Blokující: {', '.join(fails) or '—'}; varování: {', '.join(warns) or '—'}.\n\n"
            f"Možnosti: (a) dopravit a znovu `/pm ship {slug}`, (b) pilot s malou skupinou "
            f"a paralelní oprava, (c) Ship i přesto jen s override Decidera a důvodem v decision logu.\n"
        )
    err_block = ""
    if errors:
        err_block = "\n## Chyby\n\n" + "\n".join(f"- varianta {e['variant']}: {e['error']}" for e in errors) + "\n"
    cp_block = ""
    if checkpoints:
        cp_block = "\n## Checkpointy\n\n" + "\n".join(f"- {c}" for c in checkpoints) + "\n"
    low = ""
    if w["gates"].get("low_confidence"):
        low = (f"\n> Pozor: skóre vychází jen z {w['gates'].get('applicable_gates')} "
               "aplikovatelných bran - malá vypovídací hodnota.\n")

    return f"""{BRAND}

# Ship — {name}

> Projekt: `{slug}` · Vygenerováno: {today} · Práh: {target}/100
> Hardenováno: {source}
{low}
## Varianty

| Varianta | Builder | Skóre z Buildu | Gate skóre | Stav | Metoda | Větev |
|----------|---------|----------------|------------|------|--------|-------|
{var_table}

{verdict_block}
## Brány vítěze ({w['variant']}, stack `{w['gates'].get('stack')}`, {w['gates'].get('applicable_gates')} z {w['gates'].get('total_gates')} aplikovatelných)

{gate_lines}
{err_block}{cp_block}
## Metodika

Skóre = body z aplikovatelných bran / max aplikovatelných × 100. Brána, která pro stack
nedává smysl (např. typy bez tsconfig.json), je SKIP a nepočítá se. Žádné testy = FAIL.
Váhy: acceptance 2,5 · testy 2,0 · security 2,0 · build 1,5 · typy 1,5 · ostatní 0,5–1,0.
Detail per brána: `quality-{w['variant']}.md` ve výstupní složce (`pflanzer data`).
"""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--variants", default=None,
                   help="override výběru, např. A nebo A,B (default: vítěz z Rozhodnutí)")
    p.add_argument("--checkpoint", action="append", default=[],
                   help="záznam checkpointu provozu (opakovatelné)")
    p.add_argument("--repo-urls", default=None, help="JSON dict variant→GitHub URL")
    p.add_argument("--method-overrides", default=None, help="JSON dict variant→metoda")
    args = p.parse_args()

    variants = [v.strip().upper() for v in args.variants.split(",") if v.strip()] if args.variants else None
    try:
        out = hardening_run(
            slug=args.slug, variants=variants,
            variant_repo_urls=json.loads(args.repo_urls) if args.repo_urls else None,
            extract_method_overrides=json.loads(args.method_overrides) if args.method_overrides else None,
            checkpoints=args.checkpoint,
        )
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(2)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
