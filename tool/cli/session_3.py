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
   Příkazy bran jdou z adaptéru `pflanzer.gates.yml` v **base branchi** target repa
   (ne z větve varianty), jinak z autodetekce stacku.
4. Hard gates: odložený/nepodepsaný triage blokuje `production_ready` pro pilot/production
   (override jen `--override-triage --rationale "…"` do decision logu) a verdikt vyžaduje
   aspoň 4 reálně spuštěné brány včetně build a tests.
5. Zapíše report `<DATA_ROOT>/production_reports/<slug>-readiness.md` a (je-li cwd
   target repo s `.pflanzer/`) sekci Ship do decision logu.

Rozhraní:
    pflanzer session_3 --slug S [--variants A[,B]] [--checkpoint "Provoz: ok (Karel, on-call)"]...
                       [--repo-urls JSON] [--method-overrides JSON]
                       [--override-triage --rationale "…"]
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

from tool.cli.db import audit, display_path, transaction  # noqa: E402
from tool.cli.extract import (  # noqa: E402
    BRAND,
    DATA_ROOT,
    WORKTREE_METHODS,
    ExtractionError,
    base_gates_adapter,
    extract,
    plan_extraction,
)
from tool.cli.quality_gates import (  # noqa: E402
    GATE_TYPES,
    MIN_GATES_RUN,
    RAN_STATUSES,
    REQUIRED_GATES,
    verdict_label,
)
from tool.cli.quality_gates import gates_sufficiency as _gates_sufficiency  # noqa: E402
from tool.cli.quality_gates import run_all as run_gates  # noqa: E402
from tool.cli.session_2 import get_shortlist, get_winner, write_repo_decision_log  # noqa: E402
from tool.cli.triage import record_triage_override, ship_triage_gate  # noqa: E402

REPORTS_DIR = DATA_ROOT / "production_reports"
BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"
__all__ = ["MIN_GATES_RUN", "RAN_STATUSES", "REQUIRED_GATES", "ExtractionError",
           "gates_sufficiency", "hardening_run"]


def gates_sufficiency(gate_result: dict[str, Any]) -> dict[str, Any]:
    """Minimum důkazů pro verdikt (>= 4 spuštěné brány včetně build a tests).

    Bere výsledek `quality_gates.run_all` (klíč `results`); SKIP / unsupported se nepočítají.
    """
    return _gates_sufficiency(gate_result.get("results", []))


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
    override_triage: bool = False, override_rationale: str | None = None,
) -> dict[str, Any]:
    """Pusť Ship pro vítěze (nebo explicitně zadané varianty)."""
    variant_repo_urls = variant_repo_urls or {}
    extract_method_overrides = extract_method_overrides or {}
    checkpoints = [c.strip() for c in (checkpoints or []) if c and c.strip()]
    if override_triage and not (override_rationale or "").strip():
        raise ValueError(
            "--override-triage vyžaduje --rationale \"…\" (zapisuje se do decision logu)."
        )

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, production_readiness_target, name, target_branch "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status, name = int(proj[0]), proj[1], proj[3]
        target = int(proj[2]) if proj[2] is not None else 80
        target_branch = proj[4] or "main"
        if status != "handoff":
            raise ValueError(
                f"Project status='{status}'. Ship vyžaduje Go v Rozhodnutí "
                f"(`pflanzer session_2 decide --slug {slug} go --winner A --rationale \"…\"`)."
            )
        selected, source, decided = _select_variants(conn, project_id, variants)
        triage_gate = ship_triage_gate(conn, project_id)

    risk_profile = triage_gate["risk_profile"]

    # Fail loud dřív, než poběží jakákoli brána: každá hardenovaná varianta potřebuje použitelný
    # zdroj kódu (worktree > hosted URL > skeleton jen pro throwaway), viz extract.plan_extraction.
    for _v_id, v_name, v_builder, _pref in selected:
        plan_extraction(
            slug=slug, variant_name=v_name, builder=v_builder, risk_profile=risk_profile,
            repo_url=variant_repo_urls.get(v_name),
            method_override=extract_method_overrides.get(v_name),
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
                f"[ship gate] Blokováno triage ({', '.join(triage_gate['blocked_by'])}) - "
                f"production_ready bude false. Spusť `/pm triage {slug}`.",
                file=sys.stderr,
            )

    per_variant: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for v_id, v_name, builder, pref in selected:
        try:
            ext = extract(
                slug=slug, variant_name=v_name,
                repo_url=variant_repo_urls.get(v_name),
                method_override=extract_method_overrides.get(v_name),
            )
            # Integrita adaptéru: příkazy bran z BASE branche, ne z větve, kterou agent mohl upravit.
            adapter: dict[str, Any] = {"adapter_path": None, "tmp_dir": None, "warnings": []}
            if ext["method"] in WORKTREE_METHODS:
                adapter = base_gates_adapter(Path(ext["absolute_path"]), target_branch)
            try:
                gates = run_gates(ext["extracted_id"], adapter_path=adapter.get("adapter_path"))
            finally:
                if adapter.get("tmp_dir"):
                    shutil.rmtree(adapter["tmp_dir"], ignore_errors=True)
        except (ValueError, RuntimeError, NotImplementedError) as e:
            errors.append({"variant": v_name, "error": str(e)})
            continue
        per_variant.append({
            "variant": v_name, "builder": builder, "preference_score": pref,
            "extraction": ext, "gates": gates, "sufficiency": gates_sufficiency(gates),
            "adapter": {
                "source": (f"{adapter.get('base_ref')}:{adapter.get('name')}"
                           if adapter.get("adapter_path") else "autodetect"),
                "warnings": adapter["warnings"],
            },
        })

    if not per_variant:
        raise ValueError("Ship se nepodařil: " + "; ".join(
            f"{e['variant']}: {e['error']}" for e in errors))

    # Vítěz = vítěz z Rozhodnutí (pokud byl hardenován), jinak nejlepší skóre
    winner = next((r for r in per_variant if r["variant"] == decided), None) or max(
        per_variant, key=lambda r: (r["gates"]["gate_score"], r["preference_score"]))
    w_score = winner["gates"]["gate_score"]
    suff = winner["sufficiency"]
    low_conf = not suff["sufficient"]
    blocked_by = list(triage_gate["blocked_by"])
    if target > 0 and low_conf:
        blocked_by.append(suff["blocker"])
    gate_ready = w_score >= target
    meets = gate_ready and not blocked_by
    production_ready = meets and target > 0
    verdict = verdict_label(w_score, target, low_conf)
    if triage_gate["blocked_by"]:
        verdict = f"blokováno triage - {verdict}"

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
                "gate_ready": gate_ready, "production_ready": production_ready,
                "risk_profile": risk_profile, "blocked_by": blocked_by,
                "triage_override_decision_id": (
                    triage_gate["override"]["decision_id"] if triage_gate["override"] else None
                ),
                "methods": {r["variant"]: r["extraction"]["method"] for r in per_variant},
                "gates_run": {r["variant"]: r["sufficiency"]["gates_run"] for r in per_variant},
                "adapter": {r["variant"]: r["adapter"] for r in per_variant},
                "errors": errors, "checkpoints": checkpoints,
            },
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{slug}-readiness.md"
    report_md = _render_report(slug, name, target, per_variant, winner, meets,
                               source, errors, checkpoints, triage_gate, blocked_by)
    report_path.write_text(report_md, encoding="utf-8")

    repo_log = write_repo_decision_log(
        slug, _render_log_section(winner, target, verdict, checkpoints, blocked_by),
        label="Ship")

    out: dict[str, Any] = {
        "slug": slug,
        "selection": source,
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
            "branch": winner["extraction"].get("branch"),
            "head_sha": winner["extraction"].get("head_sha"),
            "gate_score": w_score,
            "score_display": f"{w_score}/100 (práh {target})",
            "verdict": verdict,
            "meets_threshold": meets,
            "gate_ready": gate_ready,
            "production_ready": production_ready,
            "blocked_by": blocked_by,
            "stack": winner["gates"].get("stack"),
            "applicable_gates": winner["gates"].get("applicable_gates"),
            "total_gates": winner["gates"].get("total_gates"),
            "local_path": winner["extraction"]["local_path"],
            "next_step": _next_step(winner, meets, target, slug, blocked_by),
        },
        "per_variant": [
            {
                "variant": r["variant"],
                "builder": r["builder"],
                "preference_score": r["preference_score"],
                "gate_score": r["gates"]["gate_score"],
                "score_display": f"{r['gates']['gate_score']}/100 (práh {target})",
                "gate_ready": r["gates"]["gate_score"] >= target,
                "gates_run": r["sufficiency"]["gates_run"],
                "gates_sufficient": r["sufficiency"]["sufficient"],
                "adapter": r["adapter"],
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


def _render_triage_md(triage_gate: dict[str, Any], slug: str) -> tuple[str, str]:
    """Vrátí (horní blok, sekce Triage stav) pro report."""
    icons = {"ok": "OK", "deferred": "ODLOŽENO", "failed": "SELHALO", "pending": "ČEKÁ", "missing": "—"}
    rows = "\n".join(
        f"| {t['track']} | {icons.get(t['display'], t['display'])} | {t['signed_by'] or '—'} |"
        for t in triage_gate["tracks"]
    )
    note = (
        f"Rizikový profil `{triage_gate['risk_profile']}` - triage je tvrdá brána pro production_ready."
        if triage_gate["gated"]
        else f"Rizikový profil `{triage_gate['risk_profile']}` - triage brána se neuplatňuje."
    )
    override_note = ""
    if triage_gate["override"]:
        o_ = triage_gate["override"]
        override_note = (
            f"\n**Override Decidera** (rozhodnutí #{o_['decision_id']}, {o_['by']}): "
            f"{o_['rationale']}\n"
        )
    section = f"""## Triage stav

{note}

| Track | Stav | Podepsal |
|-------|------|----------|
{rows}
{override_note}"""
    top = ""
    if triage_gate["blocked_by"]:
        top = f"""> ## BLOKOVÁNO: chybí podepsané checkpointy (`pflanzer checkpoint --slug {slug} --list`)
>
> production_ready = **false** bez ohledu na skóre.
> Důvod: {', '.join(f'`{b}`' for b in triage_gate['blocked_by'])}.
> Override Decidera jen s důvodem do decision logu:
> `pflanzer session_3 --slug {slug} --override-triage --rationale "…"`
"""
    return top, section


def _failing(winner: dict[str, Any]) -> tuple[list[str], list[str]]:
    res = winner["gates"]["results"]
    return ([g["gate"] for g in res if g["status"] == "fail"],
            [g["gate"] for g in res if g["status"] == "warn"])


def _next_step(winner: dict[str, Any], meets: bool, target: int, slug: str,
               blocked_by: list[str] | None = None) -> str:
    score = winner["gates"]["gate_score"]
    if blocked_by and target > 0:
        parts: list[str] = []
        triage_b = [b for b in blocked_by if b.startswith("triage:")]
        gates_b = [b for b in blocked_by if b.startswith("gates:")]
        if triage_b:
            parts.append(
                f"Blokováno: spusť `/pm triage {slug}` ({', '.join(triage_b)}). Override Decidera "
                f"jen s důvodem: `pflanzer session_3 --slug {slug} --override-triage "
                f"--rationale \"…\"`."
            )
        if gates_b:
            parts.append(
                f"{', '.join(gates_b)} - doplň `pflanzer.gates.yml` v base branchi target repa "
                "(viz tool/templates/README-gates.md) a spusť Ship znovu."
            )
        parts.append(f"Skóre {score}/100 (práh {target}).")
        return " ".join(parts)
    if meets:
        return (f"Skóre {score}/100 (práh {target}). Checkpoint provozu (20 min), pak PR vítěze: "
                f"`pflanzer handoff_pr --slug {slug}` a `/pm handoff {slug}`.")
    fails, warns = _failing(winner)
    return (f"Skóre {score}/100 je pod prahem {target}. Dopravit: "
            f"{', '.join(fails) or 'viz report'}"
            + (f" (varování: {', '.join(warns)})" if warns else "")
            + f". Pak znovu `/pm ship {slug}`, nebo pilot s malou skupinou na Decidera.")


def _render_log_section(winner: dict[str, Any], target: int, verdict: str,
                        checkpoints: list[str], blocked_by: list[str] | None = None) -> str:
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
    if blocked_by and target > 0:
        lines += ["", "### Blokace", ""] + [f"- `{b}`" for b in blocked_by]
    if checkpoints:
        lines += ["", "### Checkpointy", ""] + [f"- {c}" for c in checkpoints]
    return "\n".join(lines) + "\n"


def _render_report(
    slug: str, name: str, target: int,
    per_variant: list[dict[str, Any]], winner: dict[str, Any],
    meets: bool, source: str, errors: list[dict[str, str]], checkpoints: list[str],
    triage_gate: dict[str, Any], blocked_by: list[str],
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
        f"{r['sufficiency']['gates_run']}/{len(GATE_TYPES)}"
        f"{'' if r['sufficiency']['sufficient'] else ' (málo)'} | "
        f"`{r['extraction']['method']}` | {r['extraction'].get('branch') or '—'} | "
        f"{r['adapter']['source']} |"
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
    elif w_score >= target:
        # Skóre stačí, ale blokuje něco jiného (triage / málo spuštěných gates) —
        # nehlásit „pod prahem", jen odkázat na skutečný blokátor.
        verdict_block = (
            f"## Skóre splňuje práh ({w_score}/100 ≥ {target})\n\n"
            f"Ship blokuje: {', '.join(blocked_by) or 'málo spuštěných gates (min. 4 vč. build + tests)'}. "
            f"Okna podepiš přes `pflanzer checkpoint --slug {slug} bezpecnost|provoz …` "
            f"(viz blok výše), pak znovu `/pm ship {slug}`.\n"
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
    suff = w["sufficiency"]
    if not suff["sufficient"]:
        low = (f"\n> Pozor: skóre vychází jen z {w['gates'].get('applicable_gates')} "
               f"aplikovatelných bran - `{suff['blocker']}`. Verdikt vyžaduje aspoň "
               f"{MIN_GATES_RUN} reálně spuštěné brány včetně build a tests (SKIP / unsupported "
               "se nepočítají); doplň příkazy do `pflanzer.gates.yml` v base branchi "
               "(viz tool/templates/README-gates.md).\n")
    triage_top, triage_section = _render_triage_md(triage_gate, slug)
    adapter_warnings = "\n".join(
        f"- **{r['variant']}**: {x}" for r in per_variant for x in r["adapter"]["warnings"]
    )
    adapter_section = (
        f"\n## Gate adaptér - integrita\n\n{adapter_warnings}\n" if adapter_warnings else ""
    )
    if triage_gate["blocked_by"] and target > 0:
        verdict_block = (
            f"## Verdikt: BLOKOVÁNO triage\n\n"
            f"Vítěz **{w['variant']}** má **{w_score}/100** (práh {target}), ale risk profil "
            f"`{triage_gate['risk_profile']}` vyžaduje podepsaný triage ve všech 4 trackách. "
            f"Podepiš okna: `pflanzer checkpoint --slug {slug} bezpecnost --by … --note …` a `… provoz …` (zadání podepisuje Kickoff), pak Ship znovu. Plný triage (`/pm triage`) jen pro regulované projekty.\n"
        ) + ("\n" + verdict_block if not meets else "")

    return f"""{BRAND}

# Ship — {name}

> Projekt: `{slug}` · Vygenerováno: {today} · Práh: {target}/100 · Risk profil: `{triage_gate['risk_profile']}`
> Hardenováno: {source}
{low}
{triage_top}
## Varianty

| Varianta | Builder | Skóre z Buildu | Gate skóre | Stav | Spuštěné brány | Metoda | Větev | Adaptér |
|----------|---------|----------------|------------|------|----------------|--------|-------|---------|
{var_table}

{verdict_block}
## Brány vítěze ({w['variant']}, stack `{w['gates'].get('stack')}`, {w['gates'].get('applicable_gates')} z {w['gates'].get('total_gates')} aplikovatelných)

{gate_lines}
{adapter_section}{err_block}{cp_block}
{triage_section}
## Metodika

Skóre = body z aplikovatelných bran / max aplikovatelných × 100. Brána, která pro stack
nedává smysl (např. typy bez tsconfig.json), je SKIP a nepočítá se. Žádné testy = FAIL.
Verdikt "splňuje práh" vyžaduje aspoň 4 reálně spuštěné brány včetně build a tests.
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
    p.add_argument("--override-triage", action="store_true",
                   help="Override Decidera: triage tvrdá brána (vyžaduje --rationale)")
    p.add_argument("--rationale", default=None,
                   help="Zdůvodnění override do decision logu (povinné s --override-triage)")
    p.add_argument("--repo-urls", default=None, help="JSON dict variant→GitHub URL")
    p.add_argument("--method-overrides", default=None, help="JSON dict variant→metoda")
    args = p.parse_args()

    if args.override_triage and not (args.rationale or "").strip():
        p.error("--override-triage vyžaduje --rationale \"…\"")

    variants = [v.strip().upper() for v in args.variants.split(",") if v.strip()] if args.variants else None
    try:
        out = hardening_run(
            slug=args.slug, variants=variants,
            variant_repo_urls=json.loads(args.repo_urls) if args.repo_urls else None,
            extract_method_overrides=json.loads(args.method_overrides) if args.method_overrides else None,
            checkpoints=args.checkpoint,
            override_triage=args.override_triage, override_rationale=args.rationale,
        )
    except (ExtractionError, ValueError) as e:
        print(f"{BRAND_LINE}\n\n" + json.dumps({"error": str(e)}, ensure_ascii=False, indent=2),
              file=sys.stderr)
        sys.exit(2)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
