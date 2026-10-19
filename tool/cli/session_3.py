"""Ship (v0.5; příkaz `pflanzer session_3`) — quality gates na vítěze po Go.

Ship není session, je to práce vývojářů s automatickými branami + 20min
checkpoint provozu (ADR-0021). Tento modul:

1. Zjistí, co hardenovat: **jen vítěze z Rozhodnutí** (`session_2 decide go --winner X`).
   Fallback: shortlist z Buildu, pak varianta s nejvyšším skóre. `--variants` jiné než
   vítěz z Rozhodnutí jde jen s `--rationale` a je to informativní porovnání: vítěz
   v reportu ani v SHIP.md se tím nepřepíše (pro samotné skóre: `quality_gates --path`).
2. Zaregistruje kód varianty (výchozí metoda `in_repo_branch` = existující větev ve
   worktree; skeleton se nespouští, pokud worktree existuje).
3. Pustí stack-aware quality gates (`quality_gates.py`) a porovná skóre s prahem projektu
   (`projects.production_readiness_target`: pilot 80 / production 85 / throwaway 0).
   Příkazy bran jdou z adaptéru `pflanzer.gates.yml` v **base branchi** target repa
   (ne z větve varianty), jinak z autodetekce stacku.
4. Hard gates: odložený/nepodepsaný triage blokuje `production_ready` pro pilot/production
   (override jen `--override-triage --rationale "…"` do decision logu) a verdikt vyžaduje
   aspoň 4 reálně spuštěné brány včetně build a tests. Skóre pod prahem smí Decider
   přebít jen `--override-threshold --rationale "…"` (draft PR, sekce „Výjimka z prahu");
   triage ani minimum bran tím obejít nejde.
5. Zapíše report `<DATA_ROOT>/production_reports/<slug>-readiness.md` a (je-li cwd
   target repo s `.pflanzer/`) sekci Ship do decision logu.

Rozhraní:
    pflanzer session_3 --slug S [--variants A[,B]] [--checkpoint "Provoz: ok (Karel, on-call)"]...
                       [--repo-urls JSON] [--method-overrides JSON]
                       [--override-triage --rationale "…"]
                       [--override-threshold --rationale "…"]   # Ship i pod prahem, na odpovědnost Decidera
                       [--json]                                  # strojový výstup (default: lidský)
"""
from __future__ import annotations

import argparse
import json
import re
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
    code_without_tests,
    extract,
    plan_extraction,
)
from tool.cli.quality_gates import (  # noqa: E402
    GATE_TYPES,
    MIN_GATES_RUN,
    RAN_STATUSES,
    REQUIRED_GATES,
    gates_summary_line,
    verdict_label,
)
from tool.cli.quality_gates import gates_sufficiency as _gates_sufficiency  # noqa: E402
from tool.cli.quality_gates import run_all as run_gates  # noqa: E402
from tool.cli.session_2 import get_shortlist, get_winner, write_repo_decision_log  # noqa: E402
from tool.cli.triage import (  # noqa: E402
    checkpoint_command,
    human_triage_blockers,
    record_threshold_override,
    record_triage_override,
    ship_triage_gate,
)
from tool.cli.ux import die, emit, tips_for  # noqa: E402

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
    conn: Any, project_id: int, explicit: list[str] | None, rationale: str | None = None,
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
        if decided and set(explicit) != {decided} and not (rationale or "").strip():
            raise ValueError(
                f"Rozhodnutí = {decided}. Jiná varianta jen s --rationale; pro samotné skóre "
                "použij `pflanzer quality_gates --path …`."
            )
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
    override_threshold: bool = False,
) -> dict[str, Any]:
    """Pusť Ship pro vítěze (nebo explicitně zadané varianty)."""
    variant_repo_urls = variant_repo_urls or {}
    extract_method_overrides = extract_method_overrides or {}
    checkpoints = [c.strip() for c in (checkpoints or []) if c and c.strip()]
    if override_triage and not (override_rationale or "").strip():
        raise ValueError(
            "--override-triage vyžaduje --rationale \"…\" (zapisuje se do decision logu)."
        )

    if override_threshold and not (override_rationale or "").strip():
        raise ValueError(
            "--override-threshold vyžaduje --rationale \"…\" (zapisuje se do decision logu)."
        )

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, production_readiness_target, name, target_branch, decider_name "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status, name = int(proj[0]), proj[1], proj[3]
        target = int(proj[2]) if proj[2] is not None else 80
        target_branch = proj[4] or "main"
        decider_name = proj[5]
        if status != "handoff":
            raise ValueError(
                f"Project status='{status}'. Ship vyžaduje Go v Rozhodnutí "
                f"(`pflanzer session_2 decide --slug {slug} go --winner A --rationale \"…\"`)."
            )
        selected, source, decided = _select_variants(conn, project_id, variants,
                                                     override_rationale)
        prev_score = conn.execute("SELECT gate_score_latest FROM projects WHERE id = ?",
                                  (project_id,)).fetchone()[0]
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
            print("[ship gate] Ship je blokovaný podpisy oken, production_ready bude false:\n  "
                  + "\n  ".join(human_triage_blockers(slug, triage_gate["windows"])),
                  file=sys.stderr)

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
        tests_note = None
        if ext["method"] in WORKTREE_METHODS:
            tests_note = code_without_tests(Path(ext["absolute_path"]), target_branch)
        per_variant.append({
            "variant": v_name, "builder": builder, "preference_score": pref,
            "extraction": ext, "gates": gates, "sufficiency": gates_sufficiency(gates),
            "new_code_check": tests_note,
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
    # Vítěz z Rozhodnutí se nikdy nepřepisuje: ověřovaná varianta jiná než vítěz je jen informativní.
    winner = next((r for r in per_variant if r["variant"] == decided), None)
    informational = bool(decided) and winner is None
    if winner is None:
        winner = max(per_variant, key=lambda r: (r["gates"]["gate_score"], r["preference_score"]))
    w_score = winner["gates"]["gate_score"]
    suff = winner["sufficiency"]
    low_conf = not suff["sufficient"]
    blocked_by = list(triage_gate["blocked_by"])
    if target > 0 and low_conf:
        blocked_by.append(suff["blocker"])
    if informational:
        blocked_by.append(f"ship:neni-vitez (Rozhodnutí = {decided})")
    summary_line = gates_summary_line(w_score, winner["gates"]["results"])
    warnings: list[str] = []
    ncheck = winner.get("new_code_check")
    if ncheck and ncheck["missing_tests"]:
        warnings.append(
            f"Nový kód bez testů: {ncheck['new_source_files']} nových zdrojových souborů "
            "a žádný nový ani změněný test (skóre to nesnižuje, ale doplň testy)."
        )
    gate_ready = w_score >= target
    meets = gate_ready and not blocked_by
    threshold_override: dict[str, Any] | None = None
    if override_threshold:
        if target <= 0 or gate_ready:
            raise ValueError(
                f"--override-threshold se použije jen pod prahem projektu (skóre {w_score}/100, "
                f"práh {target}); tady není co přebíjet."
            )
        if blocked_by:
            print(f"[ship gate] --override-threshold nelze použít, dokud blokuje "
                  f"{', '.join(blocked_by)} (triage má vlastní override, minimum bran ne).",
                  file=sys.stderr)
        else:
            with transaction() as conn:
                dec_id = record_threshold_override(
                    conn, project_id=project_id, slug=slug, decider=decider_name,
                    score=w_score, target=target, rationale=override_rationale or "")
            threshold_override = {
                "decision_id": dec_id, "score": w_score, "target": target,
                "decider": (decider_name or "").strip() or "Decider",
                "rationale": (override_rationale or "").strip(),
            }
    production_ready = (meets or threshold_override is not None) and target > 0
    verdict = verdict_label(w_score, target, low_conf)
    if triage_gate["blocked_by"]:
        verdict = f"blokováno triage - {verdict}"
    if threshold_override:
        verdict = (f"pod prahem — Ship na odpovědnost Decidera ({threshold_override['decider']})")
    if informational:
        verdict = (f"informativně — {winner['variant']} není vítěz z Rozhodnutí ({decided}); "
                   f"production_ready=false")
        production_ready = False

    with transaction() as conn:
        # run_gates přepisuje gate_score_latest po každé variantě; finální = vítěz
        # (u informativního porovnání se vrací původní hodnota).
        conn.execute(
            "UPDATE projects SET gate_score_latest = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (prev_score if informational else w_score, project_id),
        )
        audit(
            conn, action="session_3.hardening",
            target_type="project", target_id=project_id,
            payload={
                "slug": slug, "selection": source,
                "variants_tested": [r["variant"] for r in per_variant],
                "winner": winner["variant"], "winner_score": w_score,
                "target": target, "meets_threshold": meets,
                "informational": informational, "decided_winner": decided,
                "variants_rationale": (override_rationale or None) if variants else None,
                "summary_line": summary_line, "warnings": warnings,
                "gate_ready": gate_ready, "production_ready": production_ready,
                "threshold_override": threshold_override,
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
                               source, errors, checkpoints, triage_gate, blocked_by,
                               threshold_override, summary_line=summary_line,
                               warnings=warnings, decided=decided if informational else None)
    report_path.write_text(report_md, encoding="utf-8")

    repo_log = write_repo_decision_log(
        slug, _render_log_section(winner, target, verdict, checkpoints, blocked_by,
                            threshold_override, summary_line=summary_line, warnings=warnings,
                            informational=informational),
        label="Ship (informativní porovnání)" if informational else "Ship")

    out: dict[str, Any] = {
        "slug": slug,
        "selection": source,
        "risk_profile": risk_profile,
        "production_readiness_target": target,
        "production_ready": production_ready,
        "blocked_by": blocked_by,
        "informational": informational,
        "decided_winner": decided,
        "warnings": warnings,
        "threshold_override": threshold_override,
        "triage": {
            "gated": triage_gate["gated"],
            "windows": triage_gate["windows"],
            "human_blockers": human_triage_blockers(slug, triage_gate["windows"]),
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
            "summary_line": summary_line,
            "verdict": verdict,
            "meets_threshold": meets,
            "gate_ready": gate_ready,
            "production_ready": production_ready,
            "threshold_override": threshold_override is not None,
            "blocked_by": blocked_by,
            "stack": winner["gates"].get("stack"),
            "applicable_gates": winner["gates"].get("applicable_gates"),
            "total_gates": winner["gates"].get("total_gates"),
            "local_path": winner["extraction"]["local_path"],
            "next_step": _next_step(winner, meets, target, slug, blocked_by,
                                    threshold_override, informational=informational,
                                    decided=decided,
                                    human=human_triage_blockers(slug, triage_gate["windows"])),
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
        human = "\n".join(f"> - {m}" for m in human_triage_blockers(slug, triage_gate["windows"]))
        top = f"""> ## BLOKOVÁNO: chybí podpisy oken
>
> production_ready = **false** bez ohledu na skóre.
{human}
>
> Decider může přebít jen s důvodem do decision logu:
> `pflanzer session_3 --slug {slug} --override-triage --rationale "…"`
"""
    return top, section


def _failing(winner: dict[str, Any]) -> tuple[list[str], list[str]]:
    res = winner["gates"]["results"]
    return ([g["gate"] for g in res if g["status"] == "fail"],
            [g["gate"] for g in res if g["status"] == "warn"])


def _next_step(winner: dict[str, Any], meets: bool, target: int, slug: str,
               blocked_by: list[str] | None = None,
               threshold_override: dict[str, Any] | None = None, *,
               informational: bool = False, decided: str | None = None,
               human: list[str] | None = None) -> str:
    score = winner["gates"]["gate_score"]
    if informational:
        return (f"Tohle bylo jen porovnání: vítěz z Rozhodnutí je {decided}. Pro Ship spusť "
                f"`pflanzer session_3 --slug {slug}` bez --variants.")
    if threshold_override and not blocked_by:
        return (f"Skóre {score}/100 je pod prahem {target}, Ship běží na odpovědnost Decidera "
                f"({threshold_override['decider']}). Checkpoint provozu (20 min), pak draft PR: "
                f"`pflanzer handoff_pr --slug {slug}` a `/pm handoff {slug}`.")
    if blocked_by and target > 0:
        parts: list[str] = []
        triage_b = [b for b in blocked_by if b.startswith("triage:")]
        gates_b = [b for b in blocked_by if b.startswith("gates:")]
        if triage_b:
            parts.append(
                "Blokováno podpisy oken: " + " ".join(human or triage_b) + " Decider může přebít "
                f"jen s důvodem: `pflanzer session_3 --slug {slug} --override-triage "
                f"--rationale \"…\"`."
            )
        if gates_b:
            parts.append(
                f"Málo spuštěných bran ({', '.join(gates_b)}) - doplň `pflanzer.gates.json` "
                "(nebo .yml) v base branchi target repa (viz tool/templates/README-gates.md) "
                "a spusť Ship znovu."
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
            + f". Pak znovu `/pm ship {slug}`, nebo Ship i přesto na odpovědnost Decidera: "
            f"`pflanzer session_3 --slug {slug} --override-threshold --rationale \"…\"`.")


def _render_log_section(winner: dict[str, Any], target: int, verdict: str,
                        checkpoints: list[str], blocked_by: list[str] | None = None,
                        threshold_override: dict[str, Any] | None = None, *,
                        summary_line: str = "", warnings: list[str] | None = None,
                        informational: bool = False) -> str:
    ext = winner["extraction"]
    role = "Ověřená varianta (jen porovnání, NE vítěz z Rozhodnutí)" if informational else "Vítěz"
    lines = [
        "## Ship — quality gates",
        "",
        f"- **{role}**: **{winner['variant']}** (větev `{ext.get('branch') or '—'}` "
        f"@ `{(ext.get('head_sha') or '—')[:10]}`)",
        f"- **Skóre**: **{summary_line or str(winner['gates']['gate_score']) + '/100'}** "
        f"(práh {target}) — {verdict}",
        f"- **Brány**: {winner['gates'].get('applicable_gates')} z {winner['gates'].get('total_gates')} "
        f"aplikovatelných, stack `{winner['gates'].get('stack')}`",
    ]
    if threshold_override:
        lines += ["", "### Výjimka z prahu", "",
                  f"- Verdikt: pod prahem — Ship na odpovědnost Decidera "
                  f"({threshold_override['decider']})",
                  f"- Skóre {threshold_override['score']}/100, práh {threshold_override['target']}",
                  f"- Důvod: {threshold_override['rationale']}"]
    if blocked_by and target > 0:
        lines += ["", "### Blokace", ""] + [f"- `{b}`" for b in blocked_by]
    if warnings:
        lines += ["", "### Varování", ""] + [f"- {w}" for w in warnings]
    if checkpoints:
        lines += ["", "### Checkpointy", ""] + [f"- {c}" for c in checkpoints]
    return "\n".join(lines) + "\n"


def _render_report(
    slug: str, name: str, target: int,
    per_variant: list[dict[str, Any]], winner: dict[str, Any],
    meets: bool, source: str, errors: list[dict[str, str]], checkpoints: list[str],
    triage_gate: dict[str, Any], blocked_by: list[str],
    threshold_override: dict[str, Any] | None = None, *,
    summary_line: str = "", warnings: list[str] | None = None, decided: str | None = None,
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
    if threshold_override and not blocked_by:
        verdict_block = (
            f"## Verdikt: pod prahem — Ship na odpovědnost Decidera ({threshold_override['decider']})\n\n"
            f"Vítěz **{w['variant']}** má **{w_score}/100**, práh je {target}. "
            f"Blokující: {', '.join(fails) or '—'}; varování: {', '.join(warns) or '—'}.\n\n"
            f"### Výjimka z prahu\n\n"
            f"- Rozhodnutí #{threshold_override['decision_id']}, Decider: "
            f"{threshold_override['decider']}\n"
            f"- Důvod: {threshold_override['rationale']}\n\n"
            f"### Další krok\n"
            f"1. Checkpoint provozu (20 min): deploy plán, monitoring, on-call, rollback.\n"
            f"2. **Draft** PR vítěze do `{slug}` target repa: `pflanzer handoff_pr --slug {slug}`.\n"
            f"3. `/pm handoff {slug}` — balíček per role a metriky pilotu.\n"
        )
    elif meets and target > 0:
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
            f"a paralelní oprava, (c) Ship i přesto na odpovědnost Decidera: "
            f"`pflanzer session_3 --slug {slug} --override-threshold --rationale \"…\"`.\n"
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
               "se nepočítají); doplň příkazy do `pflanzer.gates.json` (nebo .yml) v base branchi "
               "(viz tool/templates/README-gates.md).\n")
    triage_top, triage_section = _render_triage_md(triage_gate, slug)
    if decided:
        verdict_block = (
            f"## Verdikt: jen informativní porovnání\n\n"
            f"Vítěz z Rozhodnutí je **{decided}** a tento běh ho nehodnotil. Varianta "
            f"**{w['variant']}** má **{summary_line}** (práh {target}); to NEmění vítěze ani "
            f"production_ready. Ship vítěze: `pflanzer session_3 --slug {slug}`.\n"
        )
    elif summary_line:
        verdict_block += f"\n**Brány:** {summary_line}.\n"
    if warnings:
        verdict_block += "\n" + "\n".join(f"> Varování: {x}" for x in warnings) + "\n"
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
            f"`{triage_gate['risk_profile']}` vyžaduje podepsaná všechna okna.\n\n"
            + "\n".join(f"- {m}" for m in human_triage_blockers(slug, triage_gate["windows"]))
            + "\n\nPak spusť Ship znovu.\n"
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
## Brány {'varianty' if decided else 'vítěze'} ({w['variant']}, stack `{w['gates'].get('stack')}`, {w['gates'].get('applicable_gates')} z {w['gates'].get('total_gates')} aplikovatelných)

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


def _human_ship(out: dict[str, Any], slug: str) -> tuple[str, list[str], list[str], str, dict[str, Any]]:
    """(titulek, řádky, varování, další krok, ctx pro tipy) lidského výstupu Shipu."""
    w = out["winner"]
    target = out["production_readiness_target"]
    # v terminálu jen jména neběžících bran; důvody jsou v reportu
    short = re.sub(r" \([^)]*\)(?=,|$)", "", w["summary_line"])
    human = out["triage"].get("human_blockers") or []
    below = w["gate_score"] < target and not out["production_ready"]
    ctx = {"below_threshold": below}
    if out.get("informational"):
        title = f"Ship {slug}: jen porovnání (vítěz = {out['decided_winner']})"
        lines = [f"Varianta {w['variant']}: {short}",
                 f"Vítěz z Rozhodnutí je {out['decided_winner']}; tento běh ho nemění."]
    elif out["production_ready"]:
        title = f"Ship {slug}: připraveno"
        lines = [f"Vítěz {w['variant']}: {short} (práh {target})"]
    elif human:
        title = f"Ship {slug}: blokováno podpisy"
        lines = [f"Vítěz {w['variant']}: {short} (práh {target})", *human[:3]]
        if len(human) > 3:
            lines.append(f"…a dalších {len(human) - 3} oken")
    else:
        title = f"Ship {slug}: " + ("pod prahem" if below else "nelze potvrdit")
        lines = [f"Vítěz {w['variant']}: {short} (práh {target})"]
    nxt = w["next_step"]
    if human and not out["production_ready"] and not out.get("informational"):
        first = next(x for x in out["triage"]["windows"] if x["state"] != "ok")
        nxt = f"`{checkpoint_command(slug, first)}`"
    return title, lines[:6], list(out.get("warnings") or []), nxt, ctx


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--variants", default=None,
                   help="jiné varianty než vítěz z Rozhodnutí (vyžaduje --rationale; jen porovnání)")
    p.add_argument("--checkpoint", action="append", default=[],
                   help="záznam checkpointu provozu (opakovatelné)")
    p.add_argument("--override-triage", action="store_true",
                   help="Override Decidera: chybějící podpisy oken (vyžaduje --rationale)")
    p.add_argument("--rationale", default=None,
                   help="Zdůvodnění override do decision logu (povinné s --override-triage, "
                        "--override-threshold a s --variants jinými než vítěz)")
    p.add_argument("--override-threshold", action="store_true",
                   help="Ship i pod prahem na odpovědnost Decidera (jen když skóre < práh; "
                        "vyžaduje --rationale; PR bude draft)")
    p.add_argument("--repo-urls", default=None, help="JSON dict variant→GitHub URL")
    p.add_argument("--method-overrides", default=None, help="JSON dict variant→metoda")
    p.add_argument("--json", action="store_true", help="Výstup jako JSON (pro skripty)")
    args = p.parse_args()

    ex = f'pflanzer session_3 --slug {args.slug} --{{flag}} --rationale "Důvod, proč přebíjíme"'
    if args.override_triage and not (args.rationale or "").strip():
        die("--override-triage vyžaduje --rationale s důvodem (zapisuje se do decision logu).",
            ex.format(flag="override-triage"))
    if args.override_threshold and not (args.rationale or "").strip():
        die("--override-threshold vyžaduje --rationale s důvodem (zapisuje se do decision logu).",
            ex.format(flag="override-threshold"))

    try:
        variants = ([v.strip().upper() for v in args.variants.split(",") if v.strip()]
                    if args.variants else None)
        out = hardening_run(
            slug=args.slug, variants=variants,
            variant_repo_urls=json.loads(args.repo_urls) if args.repo_urls else None,
            extract_method_overrides=json.loads(args.method_overrides) if args.method_overrides else None,
            checkpoints=args.checkpoint,
            override_triage=args.override_triage, override_rationale=args.rationale,
            override_threshold=args.override_threshold,
        )
    except json.JSONDecodeError:
        die("--repo-urls a --method-overrides čekají JSON objekt.",
            '--repo-urls \'{"A": "https://github.com/firma/repo"}\'')
    except (ExtractionError, ValueError) as e:
        die(str(e))
    title, lines, warns, nxt, ctx = _human_ship(out, args.slug)
    ctx["open_critical"] = False
    emit(out, title=title, lines=lines, warnings=warns, next_step=nxt,
         tips=tips_for("ship", ctx), as_json=args.json)


if __name__ == "__main__":
    main()
