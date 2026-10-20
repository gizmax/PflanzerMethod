"""Ship (v0.5; příkaz `pflanzer ship`) — quality gates na vítěze po Go.

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
    pflanzer ship --slug S [--variants A[,B]] [--checkpoint "Provoz: ok (Karel, on-call)"]...
                       [--repo-urls JSON] [--method-overrides JSON]
                       [--override-triage --rationale "…"]
                       [--override-threshold --rationale "…"]   # Ship i pod prahem, na odpovědnost Decidera
                       [--json]                                  # strojový výstup (default: lidský)
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import ProjectNotFound, count, exit_if_project_missing, tips  # noqa: E402
from tool.cli.charter import reviewer_hint  # noqa: E402
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
    repo_blocks,
    tilde,
)
from tool.cli.quality_gates import (  # noqa: E402
    GATE_TYPES,
    MIN_GATES_RUN,
    PRODUCTION_TARGET,
    RAN_STATUSES,
    REQUIRED_GATES,
    a11y_reasons,
    acceptance_unverified,
    aggregate_repos,
    gates_summary_line,
    parse_test_failures,
    repo_key,
    repos_summary_line,
    run_repo_gates,
    save_repo_gates,
    score_sentence,
    skip_reason,
    spa_line,
    unverified_gates,
    verdict_label,
)
from tool.cli.quality_gates import gates_sufficiency as _gates_sufficiency  # noqa: E402
from tool.cli.quality_gates import run_all as run_gates  # noqa: E402
from tool.cli.session_2 import (  # noqa: E402
    get_shortlist,
    get_winner,
    open_remarks,
    overridden_critical_md,
    overridden_criticals,
    remarks_checklist,
    remarks_line,
    strip_reason,
    write_repo_decision_log,
)
from tool.cli.triage import (  # noqa: E402
    checkpoint_command,
    decider_label,
    human_triage_blockers,
    record_threshold_override,
    record_triage_override,
    ship_triage_gate,
)
from tool.cli.ux import CzechArgumentParser, die, emit  # noqa: E402

REPORTS_DIR = DATA_ROOT / "production_reports"
BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"
__all__ = ["MIN_GATES_RUN", "RAN_STATUSES", "REQUIRED_GATES", "ExtractionError",
           "gates_sufficiency", "hardening_run"]


def gates_sufficiency(gate_result: dict[str, Any]) -> dict[str, Any]:
    """Minimum důkazů pro verdikt (>= 4 spuštěné brány včetně build a tests).

    Bere výsledek `quality_gates.run_all` (klíč `results`); SKIP / unsupported se nepočítají.
    """
    return _gates_sufficiency(gate_result.get("results", []))


_GENITIVE_EXC = {"karel": "Karla", "pavel": "Pavla", "marcel": "Marcela", "havel": "Havla",
                 "ondra": "Ondry", "tom": "Toma", "jan": "Jana", "petr": "Petra"}


def decider_genitive(name: str) -> str:
    """„Ship na odpovědnost Pavly“: 2. pád jednoslovného křestního jména; jinak „Decidera (Jméno)“."""
    n = (name or "").strip()
    if not n or n == "Decider":
        return "Decidera"
    if " " in n:
        return f"Decidera ({n})"
    low = n.lower()
    if low in _GENITIVE_EXC:
        return _GENITIVE_EXC[low]
    if low.endswith("a"):
        return n[:-1] + "y"
    if low.endswith(("e", "i", "o", "u", "y")):
        return n
    if low.endswith("ek"):
        return n[:-2] + "ka"
    if low.endswith("ec"):
        return n[:-2] + "ce"
    return n + "a"


def _security_unsigned_by_human(triage_gate: dict[str, Any]) -> bool:
    """True, když Decider override přebil chybějící lidský podpis bezpečnosti (security / legal)."""
    ov = triage_gate.get("override")
    if not ov:
        return False
    return any(b.startswith(("triage:security", "triage:legal")) for b in ov.get("blocked_by", []))


def _provoz_done(windows: list[dict[str, Any]], checkpoints: list[str]) -> bool:
    """Okno provozu je podepsané (nebo ho tento běh dostal přes --checkpoint)."""
    if any(w["window"] in ("provoz", "bezpecnost-provoz") and w["state"] == "ok" for w in windows):
        return True
    return any(re.match(r"\s*provoz\b", c, re.I) for c in checkpoints)


def _clip_words(text: str, limit: int) -> str:
    """Zkrátí na hranici slova (bez useknuté závorky); text do limitu vrací celý."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-–—(")
    return cut + " …"


def _multi_repo_gates(
    slug: str, variant: str, ext: dict[str, Any], gates: dict[str, Any], target_branch: str,
) -> list[dict[str, Any]] | None:
    """Multi-repo projekt (`target_repos`): brány vítěze v KAŽDÉM repu, ne jen v primárním.

    None = jednorepo (původní chování). Chybějící worktree jiného repa je chyba (Ship nesmí
    tiše ověřit půlku kódu): `pflanzer worktree setup --slug …` ho vytvoří.
    """
    blocks = repo_blocks(slug, variant)
    if not blocks:
        return None
    primary = blocks[0]
    entries: list[dict[str, Any]] = [{
        "role": primary["role"], "path": ext["absolute_path"], "base": target_branch,
        "branch": ext.get("branch"), "head_sha": ext.get("head_sha"),
        "stack": gates.get("stack"), "gate_score": gates["gate_score"],
        "applicable_gates": gates["applicable_gates"], "total_gates": gates["total_gates"],
        "gates_run": gates["gates_run"], "sufficient": gates["sufficient"],
        "sufficiency_blocker": gates.get("sufficiency_blocker"),
        "adapter_warnings": [],
        "diff": {"added": ext.get("diff_loc_added"), "removed": ext.get("diff_loc_removed"),
                 "files": ext.get("diff_files")},
        "results": gates["results"],
    }]
    for b in blocks[1:]:
        if b["path"] is None:
            raise ValueError(
                f"Ship zatím nejde: chybí pracovní kopie repa {b['role']} pro variantu {variant} "
                f"({tilde(b['expected_path'])}), bez ní nejde ověřit celý kód. "
                f"Vytvoř ji: `pflanzer worktree setup --slug {slug}`.")
        entries.append(run_repo_gates(b["path"], b["role"], b["base"]))
    return entries


def _compose_repo_gates(gates: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Jeden výsledek bran za variantu: agregované skóre, výsledky označené `repo`."""
    agg = aggregate_repos(entries)
    out = dict(gates)
    out.update(
        gate_score=agg["gate_score"], applicable_gates=agg["applicable_gates"],
        total_gates=agg["total_gates"], sufficient=agg["sufficient"],
        sufficiency_blocker=agg["blocker"], low_confidence=not agg["sufficient"],
        stack="; ".join(f"{e['role']}: {e['stack']}" for e in entries),
        results=[dict(r, repo=e["role"]) for e in entries for r in e["results"]],
        repos=entries,
        summary_line=repos_summary_line(entries, agg["gate_score"]),
    )
    return out


def _repo_sufficiency(entries: list[dict[str, Any]]) -> dict[str, Any]:
    bad = next((e for e in entries if not e["sufficient"]), None)
    return {
        "gates_run": min(e["gates_run"] for e in entries), "missing": [],
        "sufficient": bad is None,
        "blocker": None if bad is None else
        f"gates:insufficient ({bad['role']}: {str(bad.get('sufficiency_blocker') or '').split('(', 1)[-1].rstrip(')')})",
    }


def _unverified_all(winner: dict[str, Any]) -> list[dict[str, str]]:
    """Neověřené brány; ve vícerepu s rolí repa v důvodu („api: chybí @playwright/test“)."""
    repos = winner["gates"].get("repos")
    if not repos:
        return unverified_gates(winner["gates"]["results"])
    return [dict(u, reason=f"{e['role']}: {u['reason']}")
            for e in repos for u in unverified_gates(e["results"])]


def _select_variants(
    conn: Any, project_id: int, explicit: list[str] | None, rationale: str | None = None,
) -> tuple[list[tuple[int, str, str, float]], str, str | None]:
    """Vrátí (varianty k hardeningu, zdroj výběru, vítěz z rozhodnutí)."""
    sess1 = conn.execute(
        "SELECT id FROM sessions WHERE project_id = ? AND type = 1", (project_id,),
    ).fetchone()
    if not sess1:
        raise ValueError("Ship zatím nejde: projekt nemá žádný Build (varianty). Začni `/pm build`.")
    rows = conn.execute(
        "SELECT id, name, builder, preference_score FROM variants "
        "WHERE session_id = ? ORDER BY preference_score DESC", (sess1[0],),
    ).fetchall()
    if not rows:
        raise ValueError("Ship zatím nejde: Build nevytvořil žádnou variantu. Spusť `/pm build` znovu.")
    by_name = {r[1]: (int(r[0]), r[1], r[2], float(r[3] or 0)) for r in rows}
    decided = get_winner(conn, project_id)

    if explicit:
        if decided and set(explicit) != {decided} and not (rationale or "").strip():
            raise ValueError(
                f"Vítěz z Rozhodnutí je {decided}. Jinou variantu ověříš jen s důvodem "
                "(`--rationale \"…\"`); pro samotné skóre použij `pflanzer quality_gates --path …`."
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
        raise ValueError(f"Varianta {', '.join(missing)} v Buildu není. "
                         f"Vyber z: {', '.join(sorted(by_name))}.")
    return [by_name[n] for n in names], source, decided


def _before_ship_step(status: str, slug: str) -> str:
    """Další krok, když projekt ještě není v Rozhodnutí s Go (bez interních názvů stavů)."""
    decide = f'`pflanzer decide --slug {slug} go --winner X --rationale "…"`'
    if status in ("session_2", "decide"):
        return f"Řekne ho v Rozhodnutí: {decide} (X = vítězná varianta)."
    if status in ("triage", "session_1"):
        return (f"Nejdřív doběhne Build (`pflanzer status --slug {slug}` ukáže další krok), "
                f"pak Rozhodnutí: {decide}.")
    return f"Zapiš ho: {decide} (X = vítězná varianta)."


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
    if override_rationale:
        override_rationale = strip_reason(override_rationale) or override_rationale
    checkpoints = [c.strip() for c in (checkpoints or []) if c and c.strip()]
    if override_triage and not (override_rationale or "").strip():
        raise ValueError(
            "Přebití chybějících podpisů potřebuje důvod (`--rationale \"…\"`), "
            "zapíše se do decision logu."
        )

    if override_threshold and not (override_rationale or "").strip():
        raise ValueError(
            "Ship pod prahem potřebuje důvod (`--rationale \"…\"`), "
            "zapíše se do decision logu."
        )

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, production_readiness_target, name, target_branch, decider_name "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        project_id, status, name = int(proj[0]), proj[1], proj[3]
        target = int(proj[2]) if proj[2] is not None else 80
        target_branch = proj[4] or "main"
        decider_name = proj[5]
        if status == "killed":
            raise ValueError(
                "Ship nejde: projekt skončil Killem. "
                f"Poučení: `pflanzer retro lesson --slug {slug} --text \"…\"`.")
        if status != "handoff":
            raise ValueError(
                "Ship zatím nejde: Decider ještě neřekl Go. "
                f"{_before_ship_step(status, slug)}"
            )
        selected, source, decided = _select_variants(conn, project_id, variants,
                                                     override_rationale)
        prev_score = conn.execute("SELECT gate_score_latest FROM projects WHERE id = ?",
                                  (project_id,)).fetchone()[0]
        triage_gate = ship_triage_gate(conn, project_id)

    risk_profile = triage_gate["risk_profile"]
    # Podpisy oken vyžaduje jen pilot/production; demo (throwaway) žádná okna nemá.
    human_blockers_all = (human_triage_blockers(slug, triage_gate["windows"])
                          if triage_gate["gated"] else [])
    human_blockers = human_blockers_all
    _pending_gate_msg = ""

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
                    rationale=override_rationale or "", decider=decider_name,
                )
                triage_gate = ship_triage_gate(conn, project_id)
        else:
            _pending_gate_msg = (
                "[ship gate] Ship je blokovaný podpisy oken, production_ready bude false:\n  "
                + "\n  ".join(human_blockers_all))

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
            repo_entries = (_multi_repo_gates(slug, v_name, ext, gates, target_branch)
                            if ext["method"] in WORKTREE_METHODS else None)
            if repo_entries:
                gates = _compose_repo_gates(gates, repo_entries)
                save_repo_gates(slug, v_name, repo_entries)
        except (ValueError, RuntimeError, NotImplementedError) as e:
            errors.append({"variant": v_name, "error": str(e)})
            continue
        tests_note = None
        if ext["method"] in WORKTREE_METHODS:
            tests_note = code_without_tests(Path(ext["absolute_path"]), target_branch)
        per_variant.append({
            "variant": v_name, "builder": builder, "preference_score": pref,
            "extraction": ext, "gates": gates,
            "sufficiency": (_repo_sufficiency(repo_entries) if repo_entries
                            else gates_sufficiency(gates)),
            "new_code_check": tests_note,
            "adapter": {
                "source": (f"{adapter.get('base_ref')}:{adapter.get('name')}"
                           if adapter.get("adapter_path") else "autodetect"),
                "warnings": adapter["warnings"] + [
                    f"{e['role']}: {w}" for e in (repo_entries or [])[1:]
                    for w in e.get("adapter_warnings", [])],
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
    unverified = _unverified_all(winner)
    unverified_blocks = bool(target >= PRODUCTION_TARGET and acceptance_unverified(unverified))
    if unverified_blocks:
        blocked_by.append("gates:acceptance-neověřeno")
    design_msg = ""
    try:
        from tool.cli.checkpoint import design_gate
        dg = design_gate(slug)
        if dg.get("blocks_ship") and target > 0:
            blocked_by.append("design:nepotvrzeno")
            design_msg = dg["message"]
    except Exception:  # noqa: BLE001 — okno design je volitelné
        pass
    if design_msg:
        warnings_pre = [design_msg]
    else:
        warnings_pre = []
    if informational:
        blocked_by.append(f"ship:neni-vitez (Rozhodnutí = {decided})")
    w_repos: list[dict[str, Any]] = winner["gates"].get("repos") or []
    spa_note = spa_line(winner["gates"]["results"])
    warnings: list[str] = list(warnings_pre)
    if target > 0:
        for e in w_repos:
            if e["gate_score"] < target <= w_score:
                warnings.append(
                    f"Repo {e['role']}: {e['gate_score']}/100 je pod prahem {target}; "
                    f"celkové skóre {w_score}/100 to zakrývá průměrem přes repa.")
    if unverified and target > 0:
        what = ", ".join(f"{u['gate']} ({u['reason']})" for u in unverified)
        warnings.append(
            f"Neověřeno: {what} — skóre o tom nic neříká."
            + (" U production to Ship blokuje: doplňte, co chybí (nástroj nebo akceptační "
               "testy v tests/acceptance/), a spusťte Ship znovu."
               if unverified_blocks else
               " Ship to neblokuje (blokuje jen neověřená acceptance u production)."))
    ncheck = winner.get("new_code_check")
    if ncheck and ncheck["missing_tests"]:
        warnings.append(
            f"Nový kód bez testů: {ncheck['new_source_files']} nových zdrojových souborů "
            "a žádný nový ani změněný test (skóre to nesnižuje, ale doplň testy)."
        )
    decider_disp = decider_label(decider_name)
    if _security_unsigned_by_human(triage_gate):
        warnings.append(f"Ship na odpovědnost {decider_genitive(decider_disp)}: "
                        "bezpečnost nepodepsal člověk.")
    hard_fail = _hard_failed(winner)
    gate_ready = w_score >= target and not (hard_fail and target > 0)
    meets = gate_ready and not blocked_by
    if hard_fail and target > 0:
        warnings.append(_hard_fail_message(winner, hard_fail))
    threshold_override: dict[str, Any] | None = None
    if override_threshold:
        if target <= 0 or gate_ready:
            raise ValueError(
                f"Výjimku z prahu nepotřebuješ: skóre {w_score} ze 100"
                + (" je informativní (throwaway)." if target <= 0
                   else f" splňuje práh {target} a žádná klíčová brána (sestavení, testy, "
                        "spuštění aplikace) nepadá. Pusť Ship bez `--override-threshold`.")
            )
        if blocked_by:
            warnings.append(
                f"Výjimku z prahu zatím nejde použít, protože Ship blokuje "
                f"{', '.join(blocked_by)}. Nejdřív to vyřeš (chybějící podpisy lze přebít "
                "přes `--override-triage --rationale \"…\"`).")
        else:
            with transaction() as conn:
                dec_id = record_threshold_override(
                    conn, project_id=project_id, slug=slug, decider=decider_name,
                    score=w_score, target=target, rationale=override_rationale or "")
            threshold_override = {
                "decision_id": dec_id, "score": w_score, "target": target,
                "decider": decider_disp,
                "rationale": (override_rationale or "").strip(),
            }
    production_ready = (meets or threshold_override is not None) and target > 0
    verdict = verdict_label(w_score, target, low_conf, unverified)
    if hard_fail and target > 0 and w_score >= target:
        verdict = (f"neprošlo — {_hard_fail_message(winner, hard_fail)} "
                   f"(skóre {w_score}/100 to nezachrání)")
    if triage_gate["blocked_by"]:
        verdict = f"blokováno triage - {verdict}"
    if threshold_override:
        verdict = (("neprošlo brány — " if hard_fail else "pod prahem — ")
                   + f"Ship na odpovědnost Decidera ({threshold_override['decider']})")
    if target <= 0 and not informational:
        verdict = (f"informativně (demo) — neblokuje; před pilotem nový Kickoff s risk "
                   f"profilem pilot, skóre {w_score}/100")
    if informational:
        verdict = (f"informativně — {winner['variant']} není vítěz z Rozhodnutí ({decided}); "
                   f"production_ready=false")
        production_ready = False

    summary_line = (
        score_sentence(w_score, target, None, [], verdict, extra="Po repech: " + " · ".join(
            f"{e['role']} {int(e['gate_score'])}/100" for e in w_repos) + ".")
        if w_repos else gates_summary_line(w_score, winner["gates"]["results"],
                                           target=target, verdict=verdict))
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
                "unverified": unverified,
                "threshold_override": threshold_override,
                "risk_profile": risk_profile, "blocked_by": blocked_by,
                "triage_override_decision_id": (
                    triage_gate["override"]["decision_id"] if triage_gate["override"] else None
                ),
                "methods": {r["variant"]: r["extraction"]["method"] for r in per_variant},
                "gates_run": {r["variant"]: r["sufficiency"]["gates_run"] for r in per_variant},
                "adapter": {r["variant"]: r["adapter"] for r in per_variant},
                "errors": errors, "checkpoints": checkpoints,
                "repos": [{"role": e["role"], "gate_score": e["gate_score"],
                           "branch": e.get("branch")} for e in w_repos] or None,
            },
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{slug}-readiness.md"
    report_md = _render_report(slug, name, target, per_variant, winner, meets,
                               source, errors, checkpoints, triage_gate, blocked_by,
                               threshold_override, summary_line=summary_line,
                               warnings=warnings, decided=decided if informational else None,
                               provoz_done=_provoz_done(triage_gate["windows"], checkpoints))
    report_path.write_text(report_md, encoding="utf-8")

    with transaction() as conn:
        ov_crit = [c for c in overridden_criticals(conn, project_id)
                   if c["variant"] == winner["variant"]]
        remarks = open_remarks(conn, project_id, winner["variant"])
    log_md = _render_log_section(winner, target, verdict, checkpoints, blocked_by,
                                 threshold_override, summary_line=summary_line,
                                 warnings=warnings, informational=informational)
    if ov_crit:
        log_md += "\n" + overridden_critical_md(ov_crit).replace("## ", "### ", 1)
    if remarks:
        log_md += ("\n### Otevřené připomínky k vítězi\n\n"
                   + "\n".join(remarks_checklist(remarks)) + "\n")
    repo_log = write_repo_decision_log(
        slug, log_md,
        label="Ship (informativní porovnání)" if informational else "Ship")

    out: dict[str, Any] = {
        "slug": slug,
        "selection": source,
        "risk_profile": risk_profile,
        "production_readiness_target": target,
        "production_ready": production_ready,
        "blocked_by": blocked_by,
        "gate_notice": _pending_gate_msg.replace("[ship gate] ", "") or None,
        "production_ready_reason": _production_reason(
            production_ready, target, risk_profile, informational, blocked_by,
            hard_fail, w_score, threshold_override),
        "informational": informational,
        "decided_winner": decided,
        "warnings": warnings,
        "threshold_override": threshold_override,
        "provoz_signed": _provoz_done(triage_gate["windows"], checkpoints),
        "open_remarks": remarks,
        "triage": {
            "gated": triage_gate["gated"],
            "windows": triage_gate["windows"],
            "human_blockers": human_blockers,
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
            "spa_line": spa_note,
            "unverified": unverified,
            "verdict": verdict,
            "meets_threshold": meets,
            "gate_ready": gate_ready,
            "production_ready": production_ready,
            "threshold_override": threshold_override is not None,
            "blocked_by": blocked_by,
            "stack": winner["gates"].get("stack"),
            "failures": _gate_failures(winner["gates"]["results"]),
            "repos": [{
                "role": e["role"], "branch": e.get("branch"), "base": e.get("base"),
                "head_sha": e.get("head_sha"), "gate_score": e["gate_score"],
                "summary_line": gates_summary_line(e["gate_score"], e["results"]),
                "stack": e.get("stack"), "applicable_gates": e["applicable_gates"],
                "sufficient": e["sufficient"], "diff": e.get("diff"),
                "failures": _gate_failures(e["results"]),
            } for e in w_repos],
            "applicable_gates": winner["gates"].get("applicable_gates"),
            "total_gates": winner["gates"].get("total_gates"),
            "local_path": winner["extraction"]["local_path"],
            "next_step": _next_step(winner, meets, target, slug, blocked_by,
                                    threshold_override, informational=informational,
                                    decided=decided,
                                    human=human_blockers,
                                    provoz_done=_provoz_done(triage_gate["windows"], checkpoints)),
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
        "report_nice_path": _nice_path(report_path),
        "decision_log_repo": repo_log,
    }
    return out


_BLOCK_LABELS = {
    "gates:acceptance-neověřeno": "akceptační testy neověřené (production vyžaduje)",
}


def _block_reasons(blocked_by: list[str]) -> str:
    return ", ".join(_BLOCK_LABELS.get(b, b) for b in blocked_by) \
        or "málo spuštěných gates (min. 4 vč. build + tests)"


def _production_reason(production_ready: bool, target: int, risk_profile: str,
                       informational: bool, blocked_by: list[str], hard_fail: list[str],
                       score: int, threshold_override: dict[str, Any] | None) -> str:
    """Jednou větou, proč je production_ready true/false (u dema ne kvůli podpisům)."""
    if production_ready:
        return ("splněn práh i brány" if not threshold_override
                else "Ship pod prahem na odpovědnost Decidera")
    if informational:
        return "běh je jen porovnání, vítěz z Rozhodnutí se nemění"
    if target <= 0:
        return (f"demo ({risk_profile}) není produkce; skóre je informativní, "
                "podpisy oken ani práh se nevyžadují")
    if blocked_by:
        return "Ship blokuje: " + _block_reasons(blocked_by)
    if hard_fail:
        return "padá klíčová brána (sestavení, testy nebo spuštění aplikace)"
    return f"skóre {score}/100 je pod prahem {target}"


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
> `pflanzer ship --slug {slug} --override-triage --rationale "…"`
"""
    return top, section


HARD_FAIL_GATES = ("build", "tests", "smoke")


def _hard_failed(winner: dict[str, Any]) -> list[str]:
    """Brány build / tests / smoke se statusem fail: Ship neprojde bez ohledu na skóre."""
    return [repo_key(g.get("repo"), g["gate"]) for g in winner["gates"]["results"]
            if g["status"] == "fail" and g["gate"] in HARD_FAIL_GATES]


def _hard_fail_message(winner: dict[str, Any], hard: list[str]) -> str:
    parts: list[str] = []
    for g in winner["gates"]["results"]:
        if repo_key(g.get("repo"), g["gate"]) not in hard or g["status"] != "fail":
            continue
        where = f" v repu {g['repo']}" if g.get("repo") else ""
        if g["gate"] == "tests":
            names = [n for n, _d in parse_test_failures(g.get("details") or "")]
            if names:
                parts.append(f"padají testy{where}: " + "; ".join(names[:5])
                             + (f" (+{len(names) - 5} dalších)" if len(names) > 5 else ""))
            else:
                parts.append(f"padají testy{where}")
        else:
            first = next((x.strip() for x in (g.get("details") or "").splitlines()
                          if x.strip()), "")
            parts.append(f"brána {g['gate']}{where} neprošla"
                         + (f": {_clip_words(first, 110)}" if first else ""))
    return "; ".join(parts)


def _failing(winner: dict[str, Any]) -> tuple[list[str], list[str]]:
    res = winner["gates"]["results"]
    return ([repo_key(g.get("repo"), g["gate"]) for g in res if g["status"] == "fail"],
            [repo_key(g.get("repo"), g["gate"]) for g in res if g["status"] == "warn"])


def _next_step(winner: dict[str, Any], meets: bool, target: int, slug: str,
               blocked_by: list[str] | None = None,
               threshold_override: dict[str, Any] | None = None, *,
               informational: bool = False, decided: str | None = None,
               human: list[str] | None = None, provoz_done: bool = False) -> str:
    score = winner["gates"]["gate_score"]
    pr_step = (f"`pflanzer handoff_pr --slug {slug}` vypíše příkazy k otevření PR (SHIP.md), "
               f"potom `/pm handoff {slug}`. {reviewer_hint(slug)}")
    ops = "" if provoz_done else "Checkpoint provozu (20 min), pak "
    if informational:
        return (f"Tohle bylo jen porovnání: vítěz z Rozhodnutí je {decided}. Pro Ship spusť "
                f"`pflanzer ship --slug {slug}` bez --variants.")
    if threshold_override and not blocked_by:
        return (f"Skóre {score}/100 je pod prahem {target}, Ship běží na odpovědnost Decidera "
                f"({threshold_override['decider']}). {ops}{'d' if ops else 'D'}raft PR: {pr_step}")
    if blocked_by and target > 0:
        parts: list[str] = []
        triage_b = [b for b in blocked_by if b.startswith("triage:")]
        gates_b = [b for b in blocked_by if b.startswith("gates:") and "neověřeno" not in b]
        unv_b = [b for b in blocked_by if "neověřeno" in b]
        if triage_b:
            parts.append(
                "Blokováno podpisy oken: " + " ".join(human or triage_b) + " Decider může přebít "
                f"jen s důvodem: `pflanzer ship --slug {slug} --override-triage "
                f"--rationale \"…\"`."
            )
        if gates_b:
            parts.append(
                f"Málo spuštěných bran ({', '.join(gates_b)}) - doplň `pflanzer.gates.json` "
                "(nebo .yml) v base branchi target repa (viz tool/templates/README-gates.md) "
                "a spusť Ship znovu."
            )
        if unv_b:
            parts.append("Ship blokuje: akceptační testy neověřené (production vyžaduje). "
                         "Doplň tests/acceptance/ a nástroj (např. @playwright/test, `go`) nebo "
                         "`acceptance` v pflanzer.gates.json a spusť Ship znovu.")
        parts.append(f"Skóre {score}/100 (práh {target}).")
        return " ".join(parts)
    if meets and target <= 0:
        return (f"Demo hotové — sdílejte SHIP.md / ukázku (skóre {score}/100 je informativní, "
                "Ship neblokuje); před pilotem nový Kickoff s risk profilem pilot. "
                f"PR do repa je volitelný (`gh pr create`, jen pokud chcete demo zachovat v repu).")
    if meets:
        return f"Skóre {score}/100 (práh {target}). {ops}PR vítěze: {pr_step}"
    fails, warns = _failing(winner)
    hard = _hard_failed(winner)
    head = (f"Skóre {score}/100 (práh {target}), ale {_hard_fail_message(winner, hard)} — "
            "Ship tím neprojde. " if hard and score >= target
            else f"Skóre {score}/100 je pod prahem {target}. ")
    return (head + f"Opravit: {', '.join(fails) or 'viz report'}"
            + (f". K zvážení: {', '.join(warns)}" if warns else "")
            + f". Pak znovu `/pm ship {slug}`, nebo Ship i přesto na odpovědnost Decidera: "
            f"`pflanzer ship --slug {slug} --override-threshold --rationale \"…\"`.")


def _render_log_section(winner: dict[str, Any], target: int, verdict: str,
                        checkpoints: list[str], blocked_by: list[str] | None = None,
                        threshold_override: dict[str, Any] | None = None, *,
                        summary_line: str = "", warnings: list[str] | None = None,
                        informational: bool = False) -> str:
    ext = winner["extraction"]
    role = "Ověřená varianta (jen porovnání, NE vítěz z Rozhodnutí)" if informational else "Vítěz"
    w_repos: list[dict[str, Any]] = winner["gates"].get("repos") or []
    lines = [
        "## Ship — quality gates",
        "",
        f"- **{role}**: **{winner['variant']}** (větev `{ext.get('branch') or '—'}` "
        f"@ `{(ext.get('head_sha') or '—')[:10]}`)",
        f"- {summary_line or score_sentence(winner['gates']['gate_score'], target, None, [], verdict)}",
        f"- **Brány**: {winner['gates'].get('applicable_gates')} z {winner['gates'].get('total_gates')} "
        f"aplikovatelných, stack `{winner['gates'].get('stack')}`",
    ]
    for e in w_repos:
        lines.append(f"- **Repo {e['role']}**: {e['gate_score']}/100, větev `{e.get('branch') or '—'}` "
                     f"@ `{(e.get('head_sha') or '—')[:10]}`, stack `{e.get('stack')}`")
    if threshold_override:
        lines += ["", "### Výjimka z prahu", "",
                  f"- Verdikt: pod prahem — Ship na odpovědnost Decidera "
                  f"({threshold_override['decider']})",
                  f"- Skóre {threshold_override['score']}/100, práh {threshold_override['target']}",
                  f"- Výjimku schválil: {threshold_override['decider']} (Decider)",
                  f"- Důvod: {strip_reason(threshold_override['rationale'])}"]
    if blocked_by and target > 0:
        lines += ["", "### Blokace", ""] + [f"- `{b}`" for b in blocked_by]
    if warnings:
        lines += ["", "### Varování", ""] + [f"- {w}" for w in warnings]
    if checkpoints:
        lines += ["", "### Checkpointy", ""] + [f"- {c}" for c in checkpoints]
    return "\n".join(lines) + "\n"


def _steps_md(slug: str, provoz_done: bool, *, draft: bool) -> str:
    steps: list[str] = []
    if not provoz_done:
        steps.append("Checkpoint provozu (20 min): deploy plán, monitoring, on-call, rollback.")
    steps.append(("**Draft** PR" if draft else "PR") + f" vítěze do `{slug}` target repa: "
                 f"`pflanzer handoff_pr --slug {slug}`.")
    steps.append(f"`/pm handoff {slug}` — balíček per role a metriky pilotu.")
    return "".join(f"{i}. {x}\n" for i, x in enumerate(steps, 1))


def _render_report(
    slug: str, name: str, target: int,
    per_variant: list[dict[str, Any]], winner: dict[str, Any],
    meets: bool, source: str, errors: list[dict[str, str]], checkpoints: list[str],
    triage_gate: dict[str, Any], blocked_by: list[str],
    threshold_override: dict[str, Any] | None = None, *,
    summary_line: str = "", warnings: list[str] | None = None, decided: str | None = None,
    provoz_done: bool = False,
) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    w = winner
    w_score = w["gates"]["gate_score"]
    ext = w["extraction"]

    def status_label(score: int, unv: list[dict[str, str]] | None = None) -> str:
        if target <= 0:
            return "informativně"
        if score < target:
            return "pod prahem"
        return "splňuje práh ⚠" if unv else "splňuje práh"

    def _gates_run_cell(r: dict[str, Any]) -> str:
        """Spuštěné brány: u jednoho repa `6/10`, u více repa celkem + per repo."""
        repos = r["gates"].get("repos") or []
        if len(repos) > 1:
            total = sum(e["gates_run"] for e in repos)
            cell = (f"{total}/{len(GATE_TYPES) * len(repos)} celkem ("
                    + ", ".join(f"{e['role']} {e['gates_run']}/{len(GATE_TYPES)}"
                                for e in repos) + ")")
        else:
            cell = f"{r['sufficiency']['gates_run']}/{len(GATE_TYPES)}"
        return cell + ("" if r["sufficiency"]["sufficient"] else " (málo)")

    var_table = "\n".join(
        f"| {r['variant']} | `{r['builder']}` | {r['preference_score']:.2f} | "
        f"**{r['gates']['gate_score']}/100** | {status_label(r['gates']['gate_score'], unverified_gates(r['gates']['results']))} | "
        f"{_gates_run_cell(r)} | "
        f"`{r['extraction']['method']}` | {r['extraction'].get('branch') or '—'} | "
        f"{r['adapter']['source']} |"
        for r in per_variant
    )
    def _gate_detail(g: dict[str, Any]) -> str:
        if g["status"] in ("skipped", "unsupported"):  # důvod SKIP celý, nikdy useknutý
            return skip_reason(g) or "neběžela"
        return _clip_words(" ".join(g["details"].split()), 200)

    unv_w = _unverified_all(w)
    w_repos: list[dict[str, Any]] = w["gates"].get("repos") or []

    def _badge(g: dict[str, Any], unv_gates: set[str]) -> str:
        if g["gate"] in unv_gates:
            return "NEOVĚŘENO"
        return {"skipped": "SKIP", "unsupported": "SKIP"}.get(g["status"], g["status"].upper())

    def _gate_block(results: list[dict[str, Any]]) -> str:
        unv = {u["gate"] for u in unverified_gates(results)}
        return "\n".join(f"- `{_badge(g, unv)}` **{g['gate']}**: {_gate_detail(g)}"
                         for g in results)

    if w_repos:
        gate_lines = "\n\n".join(
            f"### Repo {e['role']} — {e['gate_score']}/100 "
            f"(`{e.get('branch') or '—'}`, stack `{e.get('stack')}`, "
            f"{e['applicable_gates']} z {e['total_gates']} aplikovatelných)\n\n"
            + _gate_block(e["results"])
            for e in w_repos)
        repo_table = (
            "\n## Repa\n\n| Repo | Větev | Base | Gate skóre | Stack | Rozsah |\n"
            "|------|-------|------|------------|-------|--------|\n"
            + "\n".join(
                f"| {e['role']} | `{e.get('branch') or '—'}` | `{e.get('base')}` | "
                f"**{e['gate_score']}/100** | `{e.get('stack')}` | "
                + (f"+{e['diff']['added']} / -{e['diff']['removed']} v {e['diff']['files']} souborech"
                   if (e.get("diff") or {}).get("added") is not None else "—") + " |"
                for e in w_repos)
            + f"\n\nCelkem **{w_score}/100** = průměr skóre repo vážený počtem aplikovatelných "
              "bran; FAIL build / tests / smoke v kterémkoli repu = neprošlo.\n")
    else:
        gate_lines = _gate_block(w["gates"]["results"])
        repo_table = ''
    fails, warns = _failing(w)
    if threshold_override and not blocked_by:
        verdict_block = (
            f"## Verdikt: pod prahem — Ship na odpovědnost Decidera ({threshold_override['decider']})\n\n"
            f"Vítěz **{w['variant']}** má {w_score}/100, práh je {target}. "
            f"Blokující: {', '.join(fails) or '—'}; k zvážení: {', '.join(warns) or '—'}.\n\n"
            f"### Výjimka z prahu\n\n"
            f"- Výjimku schválil: {threshold_override['decider']} (Decider), "
            f"rozhodnutí #{threshold_override['decision_id']}\n"
            f"- Důvod: {strip_reason(threshold_override['rationale'])}\n\n"
            f"### Další krok\n"
            f"{_steps_md(slug, provoz_done, draft=True)}"
        )
    elif meets and target > 0:
        verdict_block = (
            f"## Verdikt: splňuje práh{' ⚠' if unv_w else ''}\n\n"
            f"Vítěz **{w['variant']}** má {w_score}/100 (práh {target})"
            + (f", ale neověřeno: {', '.join(u['gate'] + ' (' + u['reason'] + ')' for u in unv_w)}"
               if unv_w else "")
            + f". Kód je ve větvi "
            f"`{ext.get('branch') or '—'}` @ `{(ext.get('head_sha') or '—')[:10]}`.\n\n"
            f"### Další krok\n"
            f"{_steps_md(slug, provoz_done, draft=False)}"
        )
    elif target <= 0:
        verdict_block = (
            f"## Verdikt: informativně (throwaway, práh 0)\n\n"
            f"Skóre **{w_score}/100** nic neblokuje; kód nejde do produkce.\n\n"
            f"Je to demo: před pilotem založte nový Kickoff s risk profilem pilot "
            f"(`/pm start`), teprve tam naběhne triage, okno Bezpečnost a provoz a práh 80.\n"
        )
    elif w_score >= target and _hard_failed(w):
        verdict_block = (
            f"## Verdikt: neprošlo — {_hard_fail_message(w, _hard_failed(w))}\n\n"
            f"Vítěz **{w['variant']}** má {w_score}/100 (práh {target}), ale brány build / tests / "
            f"smoke přebíjejí skóre. Blokující: {', '.join(fails) or '—'}; "
            f"k zvážení: {', '.join(warns) or '—'}.\n\n"
            f"Možnosti: (a) opravit a znovu `/pm ship {slug}`, (b) Ship i přesto na odpovědnost "
            f"Decidera: `pflanzer ship --slug {slug} --override-threshold --rationale \"…\"`.\n"
        )
    elif w_score >= target:
        # Skóre stačí, ale blokuje něco jiného (triage / málo spuštěných gates) —
        # nehlásit „pod prahem", jen odkázat na skutečný blokátor.
        reasons = _block_reasons(blocked_by)
        has_sign = any(b.startswith("triage:") for b in blocked_by)
        advice = []
        if has_sign:
            advice.append(f"Okna podepiš přes `pflanzer checkpoint --slug {slug} bezpecnost|provoz …` "
                          "(viz blok výše)")
        if "gates:acceptance-neověřeno" in blocked_by:
            advice.append("Doplň akceptační testy do tests/acceptance/ (nebo `acceptance` v "
                          "pflanzer.gates.json) a ověř je lokálně")
        if not advice:
            advice.append("Odstraň uvedenou blokaci")
        verdict_block = (
            f"## Ship blokuje: {reasons}\n\n"
            f"Skóre splňuje práh ({w_score}/100 ≥ {target}), ale Ship blokuje: {reasons}. "
            f"{'; '.join(advice)}, pak znovu `/pm ship {slug}`.\n"
        )
    else:
        verdict_block = (
            f"## Verdikt: pod prahem\n\n"
            f"Vítěz **{w['variant']}** má {w_score}/100, práh je {target}. "
            f"Blokující: {', '.join(fails) or '—'}; k zvážení: {', '.join(warns) or '—'}.\n\n"
            f"Možnosti: (a) dopravit a znovu `/pm ship {slug}`, (b) pilot s malou skupinou "
            f"a paralelní oprava, (c) Ship i přesto na odpovědnost Decidera: "
            f"`pflanzer ship --slug {slug} --override-threshold --rationale \"…\"`.\n"
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
            f"**{w['variant']}** má {summary_line} To NEmění vítěze ani "
            f"production_ready. Ship vítěze: `pflanzer ship --slug {slug}`.\n"
        )
    elif summary_line:
        verdict_block += f"\n{summary_line}\n"
    if spa_line(w["gates"]["results"]):
        verdict_block += f"\n{spa_line(w['gates']['results'])}.\n"
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
            f"Vítěz **{w['variant']}** má {w_score}/100 (práh {target}), ale risk profil "
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
{repo_table}
{verdict_block}
## Brány {'varianty' if decided else 'vítěze'} ({w['variant']}, stack `{w['gates'].get('stack')}`, {w['gates'].get('applicable_gates')} z {w['gates'].get('total_gates')} aplikovatelných)

{gate_lines}
{adapter_section}{err_block}{cp_block}
{triage_section}
## Metodika

Skóre = body z aplikovatelných bran / max aplikovatelných × 100. Brána, která pro stack
nedává smysl (např. typy bez tsconfig.json), je SKIP a nepočítá se. Brána, která by dávala
smysl, ale chybí nástroj (např. acceptance bez @playwright/test), je NEOVĚŘENO: nepočítá se,
u production blokuje (acceptance), u pilotu je to varování. Žádné testy = FAIL.
Verdikt "splňuje práh" vyžaduje aspoň 4 reálně spuštěné brány včetně build a tests.
Váhy: acceptance 2,5 · testy 2,0 · security 2,0 · build 1,5 · typy 1,5 · ostatní 0,5–1,0.
Detail per brána: `quality-{w['variant']}.md` ve výstupní složce (`pflanzer data`).
"""


def _nice_path(path: Path) -> str:
    """Cesta k reportu: relativní k aktuální složce, jinak ~/… (ne absolutní s /Users/…)."""
    p = Path(path).resolve()
    try:
        return str(p.relative_to(Path.cwd().resolve()))
    except ValueError:
        return tilde(p)


def _gate_failures(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Selhané brány: {gate, tests: [názvy], detail: první řádek} (cesty relativní k repu)."""
    out: list[dict[str, Any]] = []
    for g in results:
        if g["status"] != "fail":
            continue
        details = g.get("details") or ""
        first = next((x.strip() for x in details.splitlines() if x.strip()), "")
        detail = _clip_words(first, 110)
        if g["gate"] == "a11y":  # první řádek je jen „N stránek zkontrolováno“ - chci důvody
            detail = _clip_words("; ".join(a11y_reasons(details)), 160) or detail
        out.append({"gate": g["gate"], "repo": g.get("repo"),
                    "tests": [n for n, _d in parse_test_failures(details)], "detail": detail})
    return out


def _failed_gate_lines(failures: list[dict[str, Any]]) -> list[str]:
    """Řádky o selhaných branách: u testů názvy selhaných testů, jinak první řádek detailu."""
    lines: list[str] = []
    for f in failures:
        names = f["tests"]
        if names:
            more = len(names) - 3
            tail = f" (+{more} dalších)" if more > 0 else ""
            where = f" v repu {f['repo']}" if f.get("repo") else ""
            lines.append(f"{'Selhaly' if len(names) > 1 else 'Selhal'} "
                         f"{count(len(names), 'test', 'testy', 'testů')}{where}: "
                         f"{'; '.join(names[:3])}{tail}")
        else:
            where = f" (repo {f['repo']})" if f.get("repo") else ""
            lines.append(f"Selhala brána {f['gate']}{where}: {f['detail']}")
    return lines


def _human_ship(out: dict[str, Any], slug: str) -> tuple[str, list[str], list[str], str, dict[str, Any]]:
    """(titulek, řádky, varování, další krok, ctx pro tipy) lidského výstupu Shipu."""
    w = out["winner"]
    target = out["production_readiness_target"]
    short = w["summary_line"].replace("**", "")  # v terminálu jen jména bran; důvody SKIP jsou celé v reportu
    human = out["triage"].get("human_blockers") or []
    below = w["gate_score"] < target and not out["production_ready"]
    ctx = {"below_threshold": below, "missing_signatures": bool(human)}
    ov = out.get("threshold_override")
    if out.get("informational"):
        title = f"Ship {slug}: jen porovnání (vítěz = {out['decided_winner']})"
        lines = [f"Varianta {w['variant']}: {short}",
                 f"Vítěz z Rozhodnutí je {out['decided_winner']}; tento běh ho nemění."]
    elif ov and out["production_ready"]:
        title = (f"Ship {slug}: připraveno jako draft — výjimka Decidera "
                 f"({ov['decider']}, {ov['score']} < {ov['target']})")
        lines = [f"Vítěz {w['variant']}: {short} (práh {target})"]
    elif out.get("risk_profile") == "throwaway":
        title = f"Ship {slug}: Throwaway: skóre je informativní, Ship neblokuje"
        lines = [f"Vítěz {w['variant']}: {short}",
                 "Demo - informativní, neblokuje; před pilotem nový Kickoff s risk profilem "
                 "pilot (podpisy oken zadání, bezpečnost a provoz se u dema nevyžadují).",
                 f"production_ready=false: {out.get('production_ready_reason') or 'demo není produkce'}."]
    elif out["production_ready"]:
        title = f"Ship {slug}: připraveno"
        lines = [f"Vítěz {w['variant']}: {short} (práh {target})"]
    elif human:
        title = f"Ship {slug}: blokováno podpisy"
        lines = [f"Vítěz {w['variant']}: {short} (práh {target})", *human[:3]]
        if len(human) > 3:
            n_more = len(human) - 3
            lines.append(f"…a další {count(n_more, 'okno', 'okna', 'oken')}")
    else:
        title = f"Ship {slug}: " + ("pod prahem" if below else "nelze potvrdit")
        lines = [f"Vítěz {w['variant']}: {short} (práh {target})"]
        if not below and out.get("blocked_by"):
            lines.insert(0, "Ship blokuje: " + _block_reasons(out["blocked_by"]))
    failed = _failed_gate_lines(w.get("failures") or [])
    if failed:
        lines = [lines[0], *failed[:2], *lines[1:]]
    if out.get("open_remarks") and not out.get("informational"):
        lines.insert(1, remarks_line(len(out["open_remarks"])))
    if w.get("spa_line"):
        lines.insert(1, w["spa_line"])
    lines = lines[:5]
    lines.append(f"Detail: {out['report_nice_path']}")
    nxt = w["next_step"]
    if human and not out["production_ready"] and not out.get("informational"):
        first = next(x for x in out["triage"]["windows"] if x["state"] != "ok")
        nxt = f"`{checkpoint_command(slug, first)}`"
    return title, lines, list(out.get("warnings") or []), nxt, ctx


def _attach_ship_md(out: dict[str, Any], slug: str) -> None:
    """Po Shipu rovnou vyrobí SHIP.md (text PR) a zapíše cestu a příkaz `gh pr create` do `out`.

    `handoff_pr` zůstává pro opakované vygenerování. Informativní porovnání SHIP.md nedělá.
    """
    out["ship_path"] = None
    out["pr_command"] = None
    if out.get("informational"):
        return
    try:
        from tool.cli.handoff_pr import pr_create_command, write_ship
        path = write_ship(slug)
        out["ship_path"] = tilde(path)
        out["pr_command"] = pr_create_command(path)
    except Exception as e:  # noqa: BLE001 — Ship samotný proběhl; SHIP.md jde vygenerovat znovu
        out["ship_error"] = str(e)


def _ship_md_lines(out: dict[str, Any], slug: str, nxt: str) -> tuple[list[str], str]:
    """(řádek o SHIP.md, další krok) — jeden krok: `gh pr create`, nebo PR ručně bez `gh`."""
    path = out.get("ship_path")
    if not path:
        if out.get("ship_error"):
            return [], (nxt + f" SHIP.md se nepodařilo vyrobit ({out['ship_error']}); "
                        f"zkus `pflanzer handoff_pr --slug {slug}`.")
        return [], nxt
    cmd = out.get("pr_command")
    w = out["winner"]
    if out.get("production_readiness_target", 0) <= 0 and out.get("risk_profile") == "throwaway":
        # Demo: podpisy ani PR se nevyžadují; `gh pr create` jen volitelně.
        if cmd and shutil.which("gh"):
            opt = f" Volitelně, pokud chcete demo zachovat v repu: `{cmd}`."
        else:
            opt = (f" PR je volitelný: pokud chcete demo zachovat v repu, otevřete PR ručně "
                   f"(text je v {path}).")
        return [f"SHIP.md (text PR): {path}"], (
            "Demo hotové — sdílejte SHIP.md / ukázku; před pilotem nový Kickoff s risk profilem "
            f"pilot.{opt}")
    if not out["production_ready"] and (
            out["triage"].get("human_blockers") or out.get("production_readiness_target", 0) > 0):
        return [f"SHIP.md (text PR): {path}"], nxt   # blokace/pod prahem: napřed ji odstranit, PR až potom
    if not cmd:
        return [f"SHIP.md (text PR): {path}"], nxt
    if shutil.which("gh"):
        where = f"ve složce vítěze (`cd {tilde(w['local_path'])}`) " if w.get("local_path") else ""
        return [f"SHIP.md (text PR): {path}"], (
            f"Otevři PR {where}příkazem `{cmd}` (celý postup je na konci {path}).")
    return [f"SHIP.md (text PR): {path}"], (
        f"`gh` není k dispozici: otevřete PR ručně, text je v {path}.")


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer ship", description=__doc__.split("\n")[0])
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

    ex = f'pflanzer ship --slug {args.slug} --{{flag}} --rationale "Důvod, proč přebíjíme"'
    if args.override_triage and not (args.rationale or "").strip():
        die("Přebití chybějících podpisů potřebuje důvod (`--rationale \"…\"`), "
            "zapíše se do decision logu.",
            ex.format(flag="override-triage"))
    if args.override_threshold and not (args.rationale or "").strip():
        die("Ship pod prahem potřebuje důvod (`--rationale \"…\"`), "
            "zapíše se do decision logu.",
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
        die("`--repo-urls` a `--method-overrides` musí být JSON objekt (varianta -> hodnota).",
            '--repo-urls \'{"A": "https://github.com/firma/repo"}\'')
    except (ExtractionError, ValueError) as e:
        exit_if_project_missing(e)
        die(str(e))
    _attach_ship_md(out, args.slug)
    title, lines, warns, nxt, ctx = _human_ship(out, args.slug)
    ctx["open_critical"] = False
    ship_lines, nxt = _ship_md_lines(out, args.slug, nxt)
    if ship_lines:
        lines = [*lines, *ship_lines]
    phase = "after_ship" if out["production_ready"] and not out.get("informational") else "ship"
    demo = out.get("risk_profile") == "throwaway" and not out.get("informational")
    emit(out, title=title, lines=lines, warnings=warns, next_step=nxt,
         tips=(["Demo nemá podpisy oken ani checkpoint provozu: ukažte ho týmu a řekněte nahlas, "
                "co je fake; do pilotu jde jen přes nový Kickoff."] if demo
               else tips(args.slug, phase, ctx, fallback="ship")), as_json=args.json)


if __name__ == "__main__":
    main()
