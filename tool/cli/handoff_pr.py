"""Handoff — SHIP.md + podklady pro `gh pr create` (v0.5).

SHIP.md je primární handoff artefakt: 1 stránka s tím, co se mění, kdo to merguje,
skóre quality gates vítěze ("X/100, práh Y"), kill kritériem, měřením a copy-paste
příkazem pro PR. Osm souborů per role (`handoff.py`) je doplněk pro audit.

Pravidla výstupu:
- první řádek je brand line,
- žádné absolutní lokální cesty v textu určeném do PR (jen větev, SHA, název),
- výstupy do `<DATA_ROOT>/handoffs/<slug>/`.

Ship gate (audit N5 + N11 + N16):
- vítěz = vítěz z Rozhodnutí; bez něj varianta s nejvyšším gate skóre (tie-break skóre z Buildu),
- triage tvrdá brána: pilot/production s nedokončeným triage = blok "BLOKOVÁNO", nikdy
  "splňuje práh" (leda s override Decidera z `session_3 --override-triage`); totéž při
  méně než 4 reálně spuštěných bránách nebo bez build/tests,
- AI code provenance (07-handoff-do-vyvoje.md § AI code provenance): trailery
  `Pflanzer-Variant` / `Pflanzer-Session: ship` / `AI-Assisted`, PR labely `ai-generated`
  + `pflanzer:<slug>`, sekce "AI provenance" v PR body a read-only kontrola
  `base..pflanzer/<slug>-<W>` (historie se nepřepisuje; autor commitu je vždy člověk),
- sekce "AI náklady (viditelnost)" z transcriptů Claude Code (`ai_usage.py`); jen viditelnost,
  nikdy brána,
- sekce "Změř po 30 dnech" odkazuje na `/pm retro` (outcomes T+7/30/60/90).

Rozhraní:
    pflanzer handoff_pr --slug S [--print] [--pr-body]
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli import ai_usage  # noqa: E402
from tool.cli.db import audit, transaction  # noqa: E402
from tool.cli.extract import (  # noqa: E402
    BRAND,
    DATA_ROOT,
    WORKTREE_METHODS,
    base_gates_adapter,
    clean_text,
    find_worktree,
    public_repo_ref,
    table_has_col,
    tilde,
)
from tool.cli.quality_gates import GATE_TYPES, aggregate_score  # noqa: E402
from tool.cli.session_2 import get_winner  # noqa: E402
from tool.cli.session_3 import gates_sufficiency  # noqa: E402
from tool.cli.triage import ship_triage_gate  # noqa: E402

SHIP_DIR = DATA_ROOT / "handoffs"
TEMPLATES_DIR = REPO_ROOT / "tool" / "templates" / "handoff"
BRAND_LINE = BRAND

_FALLBACK_MEASURE_30D = """## Změř po 30 dnech

Termín: 30 dní po merge. Změř: (1) kolik kódu vítěze (`{branch}` @ `{head_sha_short}`)
přežilo v `main`, (2) incidenty způsobené změnou, (3) metriku úspěchu vs. cíl
({metric_primary}). Kill kritérium: {kill}
Měření a připomínky vede `/pm retro {slug}`.
"""


def load_template(name: str, fallback: str = "") -> str:
    path = TEMPLATES_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return fallback


def render_measure_30d(values: dict[str, Any]) -> str:
    tpl = load_template("measure-30d.md.template", _FALLBACK_MEASURE_30D)
    safe = {k: ("—" if v in (None, "") else v) for k, v in values.items()}
    for key, val in safe.items():
        tpl = tpl.replace("{" + key + "}", str(val))
    return tpl


# Builder -> model family for the PR "AI provenance" section (no versions).
MODEL_FAMILY = {
    "claude-code": "Claude (Anthropic)",
    "codex-cli": "GPT / Codex (OpenAI)",
    "cursor": "dle nastavení Cursoru (doplň: Claude / GPT / …)",
    "v0": "v0 (Vercel) — model dle platformy",
    "bolt": "Bolt (StackBlitz) — model dle platformy",
    "lovable": "Lovable — model dle platformy",
    "stitch": "Gemini (Google Stitch)",
    "figma-make": "Figma Make — model dle platformy",
    "manual": "— (bez AI builderu)",
}
# Author / Co-Authored-By identities that must never appear on commits
# (07-handoff-do-vyvoje.md, pravidlo 1: AI is never author or co-author).
AI_IDENTITY_RE = re.compile(
    r"claude|anthropic|openai|chatgpt|codex|copilot|cursor\s*agent|cursoragent|"
    r"gemini|devin|lovable|\[bot\]",
    re.IGNORECASE,
)
_FS, _RS = "\x1f", "\x1e"


# --------------------------------------------------------------------------
# AI code provenance (N11)
# --------------------------------------------------------------------------


def _winner_worktree(slug: str, variant: str, extracted: Any) -> Path | None:
    """Worktree of the winner: the extracted path for worktree methods, else autodetect."""
    if extracted and extracted[2] in WORKTREE_METHODS:
        path = Path(extracted[1])
        path = path if path.is_absolute() else REPO_ROOT / path
        if path.is_dir():
            return path
    return find_worktree(slug, variant)


def _git(cwd: Path, *args: str) -> tuple[int, str]:
    try:
        res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return res.returncode, res.stdout


def check_provenance(
    *, slug: str, variant: str, builder: str, target_branch: str, worktree: Path | None,
) -> dict[str, Any]:
    """Read-only trailer/author check of `base..pflanzer/<slug>-<variant>`.

    Never rewrites history; problems are returned as warnings for SHIP.md.
    """
    branch = f"pflanzer/{slug}-{variant}"
    expected_variant = f"{slug}-{variant}"
    out: dict[str, Any] = {"branch": branch, "base": None, "commits": 0,
                           "authors": [], "warnings": [], "checked": False}
    if worktree is None:
        out["warnings"].append(
            f"Worktree varianty {variant} nenalezen — trailery na `{branch}` nelze ověřit."
        )
        return out

    base = None
    for candidate in (f"origin/{target_branch}", target_branch):
        rc, _ = _git(worktree, "rev-parse", "--verify", "--quiet", candidate)
        if rc == 0:
            base = candidate
            break
    if base is None:
        out["warnings"].append(
            f"Base `{target_branch}` nenalezena ve {worktree} — trailery nelze ověřit."
        )
        return out
    out["base"] = base

    fmt = _FS.join([
        "%h", "%an", "%ae",
        "%(trailers:key=Pflanzer-Variant,valueonly,separator=%x2C)",
        "%(trailers:key=AI-Assisted,valueonly,separator=%x2C)",
        "%(trailers:key=Co-authored-by,valueonly,separator=%x3B)",
    ]) + _RS
    rc, log = _git(worktree, "log", f"--format={fmt}", f"{base}..{branch}")
    if rc != 0:
        out["warnings"].append(f"`git log {base}..{branch}` selhal — trailery nelze ověřit.")
        return out
    out["checked"] = True

    missing_variant: list[str] = []
    wrong_variant: list[str] = []
    missing_ai: list[str] = []
    ai_coauthors: list[str] = []
    bot_authors: list[str] = []
    authors: list[str] = []
    for rec in filter(None, (r.strip("\n") for r in log.split(_RS))):
        parts = (rec.split(_FS) + [""] * 6)[:6]
        sha, name, email, pv, ai, coauth = (x.strip() for x in parts)
        out["commits"] += 1
        if AI_IDENTITY_RE.search(f"{name} <{email}>"):
            bot_authors.append(f"{sha} ({name} <{email}>)")
        elif name and name not in authors:
            authors.append(name)
        if not pv:
            missing_variant.append(sha)
        elif expected_variant not in [v.strip() for v in pv.split(",")]:
            wrong_variant.append(f"{sha} ({pv})")
        if builder != "manual" and not ai:
            missing_ai.append(sha)
        for co in filter(None, (c.strip() for c in coauth.split(";"))):
            if AI_IDENTITY_RE.search(co):
                ai_coauthors.append(f"{sha}: {co}")
    out["authors"] = authors

    def _few(items: list[str]) -> str:
        return ", ".join(items[:5]) + (f" (+{len(items) - 5})" if len(items) > 5 else "")

    w = out["warnings"]
    if out["commits"] == 0:
        w.append(f"`{base}..{branch}` nemá žádné commity — není co shipnout?")
    if missing_variant:
        w.append(f"{len(missing_variant)} commit(ů) bez traileru `Pflanzer-Variant`: {_few(missing_variant)}")
    if wrong_variant:
        w.append(f"Trailer `Pflanzer-Variant` ≠ `{expected_variant}`: {_few(wrong_variant)}")
    if missing_ai:
        w.append(f"{len(missing_ai)} commit(ů) bez traileru `AI-Assisted`: {_few(missing_ai)}")
    if ai_coauthors:
        w.append(
            "`Co-Authored-By` s AI identitou (AI nesmí být spoluautor — vypni atribuci "
            f"v builderu; historii tool nepřepisuje): {_few(ai_coauthors)}"
        )
    if bot_authors:
        w.append(
            "Autor commitu je AI / bot účet (autor musí být dev u klávesnice): "
            f"{_few(bot_authors)}"
        )
    return out


def _switch_worktree_session(worktree: Path | None) -> bool:
    """Best-effort: flip the worktree's trailer hook config to session 'ship'.

    Only when `worktree.py` enabled per-worktree config (extensions.worktreeConfig);
    returns True when the value was written.
    """
    if worktree is None:
        return False
    rc, val = _git(worktree, "config", "--get", "extensions.worktreeConfig")
    if rc != 0 or val.strip().lower() != "true":
        return False
    rc, _ = _git(worktree, "config", "--worktree", "pflanzer.session", "ship")
    return rc == 0


def _fetch_ship_context(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        proj = conn.execute(
            """
            SELECT id, name, slug, status, xyz_hypothesis, decider_name,
                   target_repo_url, target_branch, target_branch_owner,
                   shadow_pm, kill_criteria, throwaway_or_evolve,
                   ai_act_tier, data_class, gate_score_latest,
                   production_readiness_target, acceptance_criteria_md,
                   primary_lagging_metric, leading_metric, guardrail_metric
            FROM projects WHERE slug = ?
            """, (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id = int(proj[0])

        sess1 = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1", (project_id,),
        ).fetchone()
        decided = get_winner(conn, project_id)
        has_branch = table_has_col(conn, "variants", "head_sha")
        has_diff = table_has_col(conn, "extracted_code", "diff_loc_added")
        cols = ("v.name, v.builder, v.prototype_url, v.preference_score, v.description_md, v.id"
                + (", v.branch, v.head_sha" if has_branch else ", NULL, NULL"))
        winner = None
        winner_ext_id: int | None = None
        winner_basis: dict[str, Any] = {"mode": "none"}
        variant_names: list[str] = []
        if sess1:
            variant_rows = conn.execute(
                f"SELECT {cols} FROM variants v WHERE v.session_id = ? "
                "ORDER BY v.preference_score DESC, v.name", (sess1[0],),
            ).fetchall()
            variant_names = sorted(v[0] for v in variant_rows)
            scored: list[tuple[int, float, Any, int]] = []
            ext_ids: dict[str, int] = {}
            for v in variant_rows:
                ext = conn.execute(
                    "SELECT e.id FROM extracted_code e WHERE e.variant_id = ? "
                    "AND EXISTS (SELECT 1 FROM quality_gates qg WHERE qg.extracted_id = e.id) "
                    "ORDER BY e.id DESC LIMIT 1", (v[5],),
                ).fetchone()
                if not ext:
                    continue
                rows = conn.execute(
                    "SELECT gate_type, status FROM quality_gates WHERE extracted_id = ?",
                    (ext[0],),
                ).fetchall()
                score = aggregate_score(
                    [SimpleNamespace(gate_type=r[0], status=r[1]) for r in rows]  # type: ignore[misc]
                )["gate_score"]
                scored.append((score, float(v[3] or 0), v, int(ext[0])))
                ext_ids[v[0]] = int(ext[0])
            by_name = {v[0]: v for v in variant_rows}
            if decided and decided in by_name:
                winner = by_name[decided]
                winner_ext_id = ext_ids.get(decided)
                winner_basis = {"mode": "decision", "winner": decided}
                if scored:
                    winner_basis["compared"] = {x[2][0]: x[0] for x in scored}
            elif scored:
                best = max(scored, key=lambda x: (x[0], x[1]))
                winner, winner_ext_id = best[2], best[3]
                winner_basis = {"mode": "ship_gate", "compared": {x[2][0]: x[0] for x in scored}}
            elif variant_rows:
                winner = conn.execute(
                    f"SELECT {cols} FROM variants v JOIN extracted_code e ON e.variant_id = v.id "
                    "WHERE v.session_id = ? ORDER BY e.id DESC LIMIT 1", (sess1[0],),
                ).fetchone() or variant_rows[0]
                winner_basis = {"mode": "preference"}

        ext = None
        gate_rows: list = []
        if winner:
            ext = conn.execute(
                "SELECT e.id, e.local_path, e.extraction_method, e.files_count, e.total_loc"
                + (", e.diff_loc_added, e.diff_loc_removed, e.diff_files" if has_diff
                   else ", NULL, NULL, NULL")
                + " FROM extracted_code e WHERE e.variant_id = ? AND (? IS NULL OR e.id = ?) "
                "ORDER BY e.id DESC LIMIT 1",
                (winner[5], winner_ext_id, winner_ext_id),
            ).fetchone()
            if ext:
                gate_rows = list(conn.execute(
                    "SELECT gate_type, status, metric_value, details_md "
                    "FROM quality_gates WHERE extracted_id = ? ORDER BY id", (ext[0],),
                ).fetchall())

        decision = conn.execute(
            "SELECT body_md, atribuce_user, atribuce_ts FROM decisions "
            "WHERE project_id = ? AND type = 'handoff' ORDER BY id DESC LIMIT 1", (project_id,),
        ).fetchone()
        triage_gate = ship_triage_gate(conn, project_id)
        dev_owners = [
            r[0] for r in conn.execute(
                "SELECT human_owner FROM roles WHERE project_id = ? "
                "AND catalog_idx IN (4, 5) AND COALESCE(human_owner, '') != '' "
                "ORDER BY catalog_idx", (project_id,),
            ).fetchall()
        ]

    return {"project": proj, "winner": winner, "decided": decided, "extracted": ext,
            "gates": gate_rows, "decision": decision, "triage": triage_gate,
            "variant_names": variant_names, "dev_owners": dev_owners,
            "winner_basis": winner_basis}


def _render_triage_block(triage: dict[str, Any], slug: str) -> tuple[str, str]:
    """Vrátí (horní blok, sekce) markdownu se stavem triage."""
    labels = {"ok": "OK", "deferred": "ODLOŽENO", "failed": "SELHALO", "pending": "ČEKÁ",
              "missing": "—"}
    rows = "\n".join(
        f"| {t['track']} | {labels.get(t['display'], t['display'])} | {t['signed_by'] or '—'} |"
        for t in triage["tracks"]
    )
    note = (
        f"Risk profil `{triage['risk_profile']}` - triage je tvrdá brána pro production."
        if triage["gated"] else
        f"Risk profil `{triage['risk_profile']}` - triage brána se neuplatňuje."
    )
    if triage["override"]:
        o = triage["override"]
        note += (f"\n\n**Override Decidera** (rozhodnutí #{o['decision_id']}, {o['by']}, "
                 f"{o['at']}): {o['rationale']}")
    section = f"""## Triage stav

{note}

| Track | Stav | Podepsal |
|-------|------|----------|
{rows}
"""
    top = ""
    if triage["blocked_by"]:
        top = f"""> ## BLOKOVÁNO: spusť `/pm triage {slug}`
>
> Produkční nasazení není povoleno - {', '.join(f'`{b}`' for b in triage['blocked_by'])}.
> Override Decidera jen s důvodem do decision logu:
> `pflanzer session_3 --slug {slug} --override-triage --rationale "…"`
"""
    return top, section


def render_ai_usage_section(slug: str) -> str:
    """N16 cost visibility: live measurement, fallback to the last DB snapshot.

    Never raises — a missing/corrupt transcript dir or DB must not break SHIP.md.
    """
    usage: dict[str, Any] = {}
    origin = "live"
    try:
        usage = ai_usage.usage_for_project(slug)
    except Exception:  # noqa: BLE001 — visibility only, never fail the render
        usage = {}
    if not usage:
        try:
            usage = ai_usage.load_snapshot(slug)
            origin = "snapshot"
        except Exception:  # noqa: BLE001
            usage = {}
    try:
        return ai_usage.render_markdown(usage, origin=origin)
    except Exception:  # noqa: BLE001
        return ai_usage.render_markdown({})


def _render_gate_badges(gates: list) -> tuple[str, int, int]:
    """Řádek `PASS build · WARN a11y · SKIP types …` + (aplikovatelné, celkem)."""
    if not gates:
        return "(quality gates ještě neběžely - `/pm ship`)", 0, 0
    label = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skipped": "SKIP", "unsupported": "SKIP"}
    line = " · ".join(f"{label.get(g[1], '?')} {g[0]}" for g in gates)
    applicable = sum(1 for g in gates if g[1] in ("pass", "warn", "fail"))
    return line, applicable, len(gates)


def _verdict(score: int, target: int) -> str:
    if target <= 0:
        return "informativně (throwaway)"
    return "splňuje práh" if score >= target else "pod prahem"


def _ship_state(ctx: dict[str, Any]) -> dict[str, Any]:
    """Skóre vítěze (X/100), práh a blokace (triage, nedostatek bran)."""
    p, gates = ctx["project"], ctx["gates"]
    target = int(p[15]) if p[15] is not None else 80
    if gates:
        score = aggregate_score(
            [SimpleNamespace(gate_type=g[0], status=g[1]) for g in gates]  # type: ignore[misc]
        )["gate_score"]
    else:
        score = int(p[14] or 0)
    blocked_by = list(ctx["triage"]["blocked_by"])
    suff = gates_sufficiency({"results": [{"gate": g[0], "status": g[1]} for g in gates]})
    if gates and target > 0 and not suff["sufficient"]:
        blocked_by.append(suff["blocker"])
    if ctx["triage"]["blocked_by"]:
        verdict = "BLOKOVÁNO (triage)"
    elif blocked_by:
        verdict = "BLOKOVÁNO (nedostatek gates)"
    else:
        verdict = _verdict(score, target)
    return {"score": score, "target": target, "blocked_by": blocked_by, "verdict": verdict,
            "suff": suff, "ready": bool(gates) and target > 0 and score >= target and not blocked_by}


def _winner_basis_md(basis: dict[str, Any]) -> str:
    cmp_ = ", ".join(f"{k}={v}" for k, v in sorted((basis.get("compared") or {}).items()))
    if basis["mode"] == "decision":
        return (f"Rozhodnutí (Go s vítězem {basis['winner']})"
                + (f"; gate skóre: {cmp_}" if cmp_ else ""))
    if basis["mode"] == "ship_gate":
        return f"Ship gate - nejvyšší gate skóre (tie-break skóre z Buildu); porovnáno: {cmp_}"
    if basis["mode"] == "preference":
        return "fallback - nejvyšší skóre z Buildu (Ship ještě neběžel, žádné quality_gates)"
    return "—"


def build_pr(slug: str) -> dict[str, Any]:
    """Sestaví titulek, tělo PR (bez absolutních cest) a metadata."""
    ctx = _fetch_ship_context(slug)
    p, w, e, gates = ctx["project"], ctx["winner"], ctx["extracted"], ctx["gates"]
    name, decider = p[1], p[5]
    state = _ship_state(ctx)
    metric_primary = clean_text(p[17], "doplnit při Rozhodnutí")
    metric_leading = clean_text(p[18], "doplnit při Rozhodnutí")
    metric_guardrail = clean_text(p[19], "doplnit při Rozhodnutí")
    gate_score, target = state["score"], state["target"]
    kill = p[10] or "(nezadáno v Kickoffu)"
    badges, applicable, total = _render_gate_badges(gates)
    dec_user = ctx["decision"][1] if ctx["decision"] else None
    dec_ts = str(ctx["decision"][2])[:10] if ctx["decision"] else None

    branch = w[6] if w and w[6] else (f"pflanzer/{slug}-{w[0]}" if w else None)
    head_sha = w[7] if w else None
    builder = w[1] if w else "manual"
    loc_added = e[5] if e else None
    loc_removed = e[6] if e else None
    diff_files = e[7] if e else None
    acceptance = next((f"{int(g[2])} %" for g in gates
                       if g[0] == "acceptance" and g[1] != "skipped" and g[2] is not None), "N/A")

    decider_line = decider or dec_user or "(Decider nezadán)"
    if dec_user and decider and dec_user.strip() != decider.strip():
        decider_line += f" (zapsal {dec_user})"
    if dec_ts:
        decider_line += f", rozhodnutí Go {dec_ts}"

    size_line = ""
    if loc_added is not None:
        size_line = f"+{loc_added}" + (f" / -{loc_removed}" if loc_removed is not None else "") + " řádků"
        if diff_files is not None:
            size_line += f" v {diff_files} souborech"

    wt = _winner_worktree(slug, w[0], e) if (w and e) else None
    prov = check_provenance(
        slug=slug, variant=w[0], builder=builder, target_branch=p[7] or "main", worktree=wt,
    ) if w else None
    keyboard = ((prov["authors"] if prov else None) or ctx["dev_owners"]
                or ["(doplň - dev u klávesnice)"])
    variants = ctx["variant_names"] or ([w[0]] if w else [])

    pr_title = f"feat({slug}): {name[:60]}"
    body_lines = [
        BRAND, "",
        "## Co se mění", p[4] or name, "",
        "## Výstup Pflanzer Method",
        f"- Varianta: `{w[0] if w else '—'}` (`{builder}`), větev `{branch or '—'}`"
        + (f" @ `{head_sha[:10]}`" if head_sha else ""),
        f"- Skóre z Buildu: {float(w[3] or 0):.2f}" if w else "- Skóre z Buildu: —",
        f"- Gate skóre: **{gate_score}/100 (práh {target})** - {state['verdict']}",
        f"- Acceptance: {acceptance}",
        f"- Rozsah: {size_line or '—'}", "",
        f"## Quality gates ({applicable} z {total} aplikovatelných)", badges, "",
        "## Decider", decider_line, "",
        "## Kill kritéria", kill, "",
        "## Měření",
        f"- Primary (lagging): {metric_primary}",
        f"- Leading: {metric_leading}",
        f"- Guardrail: {metric_guardrail}", "",
        "## AI provenance",
        f"- Builder: {builder}",
        f"- Model family: {MODEL_FAMILY.get(builder, 'doplň')}",
        f"- Varianty: {len(variants)} postaveny ({'/'.join(variants)}), do PR jde vítěz {w[0] if w else '—'}",
        f"- U klávesnice: {', '.join(keyboard)} (git author commitů)", "",
        "---", "*Vygenerováno Pflanzer Method (`/pm handoff`).*",
    ]
    return {
        "ctx": ctx, "state": state, "title": pr_title, "body": "\n".join(body_lines),
        "branch": branch, "head_sha": head_sha, "loc_added": loc_added,
        "gate_score": gate_score, "target": target, "badges": badges,
        "metrics": (metric_primary, metric_leading, metric_guardrail),
        "applicable": applicable, "total": total, "kill": kill,
        "builder": builder, "worktree": wt, "provenance": prov,
        "keyboard": keyboard, "variants": variants,
    }


def render_ship_md(slug: str) -> str:
    pr = build_pr(slug)
    ctx, state = pr["ctx"], pr["state"]
    p, w, e = ctx["project"], ctx["winner"], ctx["extracted"]
    name, decider = p[1], p[5]
    target_repo = public_repo_ref(p[6])
    target_branch = p[7] or "main"
    branch_owner = p[8] or "(target_branch_owner nezadán)"
    shadow_pm = p[9] or "(shadow_pm nezadán)"
    score, target, verdict = pr["gate_score"], pr["target"], state["verdict"]
    blocked_by = state["blocked_by"]
    triage = ctx["triage"]
    triage_top, triage_section = _render_triage_block(triage, slug)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    winner_info = pr_command = ""
    if w and e:
        builder, wt, prov = pr["builder"], pr["worktree"], pr["provenance"]
        adapter_warnings: list[str] = []
        if wt is not None:
            adapter = base_gates_adapter(wt, target_branch)
            if adapter.get("tmp_dir"):
                shutil.rmtree(adapter["tmp_dir"], ignore_errors=True)
            adapter_warnings = adapter["warnings"]
        feat_branch = f"pflanzer/{slug}-{w[0]}"
        reviewer = (branch_owner if (" " not in branch_owner and not branch_owner.startswith("("))
                    else "YOUR-GH-HANDLE")
        trailers = [f"Pflanzer-Variant: {slug}-{w[0]}", "Pflanzer-Session: ship"]
        if builder != "manual":
            trailers.append(f"AI-Assisted: {builder}")
        labels = ["pflanzer", f"pflanzer:{slug}"]
        if builder != "manual":
            labels.insert(1, "ai-generated")
        label_flags = " ".join(f'--label "{lbl}"' for lbl in labels)
        label_create = "\n".join(
            f'gh label create "{lbl}" --force --color {"D93F0B" if lbl == "ai-generated" else "5319E7"}'
            for lbl in labels
        )
        commit_msg = f"{pr['title']}\n\n" + "\n".join(trailers)
        prov_warn = "\n".join(f"  - {x}" for x in prov["warnings"]) or (
            f"  - {prov['commits']} commit(ů) na `{prov['base']}..{feat_branch}` "
            "má trailery, autor = člověk, bez AI `Co-Authored-By`."
        )
        adapter_md = "\n".join(f"- {x}" for x in adapter_warnings) or (
            "- gates běžely s adaptérem z base branche (nebo autodetekcí); worktree ho nemění."
        )
        suff = state["suff"]
        gates_md = (
            f"{suff['gates_run']}/{len(GATE_TYPES)} spuštěno"
            + ("" if suff["sufficient"] else f" - `{suff['blocker']}` (viz tool/templates/README-gates.md)")
        ) if ctx["gates"] else "(Ship ještě neběžel)"
        draft_flag = " \\\n  --draft" if blocked_by else ""
        work_dir = tilde(wt) if wt else e[1]
        winner_info = f"""## Vítěz

- **Varianta**: `{w[0]}` (`{builder}`)
- **Vybrán podle**: {_winner_basis_md(ctx['winner_basis'])}
- **Větev**: `{pr['branch']}`{f" @ `{pr['head_sha'][:10]}`" if pr['head_sha'] else ''} v `{target_repo}`
- **Rozsah**: {pr['loc_added'] if pr['loc_added'] is not None else '—'} přidaných řádků
- **Gate skóre**: **{score}/100 (práh {target})** - {verdict}

### Quality gates ({pr['applicable']} z {pr['total']} aplikovatelných)

{pr['badges']}

- **Gates run**: {gates_md}

### Gate adaptér - integrita

{adapter_md}

## AI provenance

- **Builder**: `{builder}` · **Model family**: {MODEL_FAMILY.get(builder, 'doplň')}
- **Varianty**: {len(pr['variants'])} postaveny ({'/'.join(pr['variants'])}), do PR jde vítěz {w[0]}
- **U klávesnice**: {', '.join(pr['keyboard'])}
- **Kontrola `{feat_branch}`** (read-only, historie se nepřepisuje):
{prov_warn}
"""
        pr_command = f"""## Otevři PR (copy-paste)

Autor commitu = **dev u klávesnice** (`git config user.name` / `user.email` ve worktree).
AI nikdy jako author ani `Co-Authored-By` - AI asistenty značí jen trailery níže
(07-handoff-do-vyvoje.md § AI code provenance).

```bash
cd {work_dir}

# Ship commit s provenance trailery (jen pokud je co commitnout)
git add -A
git diff --cached --quiet || git commit -F - <<'COMMITMSG'
{commit_msg}
COMMITMSG

git push -u origin {pr['branch']}

# Labely musí v target repu existovat (idempotentní)
{label_create}

gh pr create \\
  --title {shlex.quote(pr['title'])} \\
  --body "$(cat <<'PRBODY'
{pr['body']}
PRBODY
)" \\
  --base {target_branch} \\
  --reviewer {reviewer} \\
  {label_flags}{draft_flag}
```
"""

    measure = render_measure_30d({
        "slug": slug, "branch": pr["branch"], "head_sha_short": (pr["head_sha"] or "")[:10],
        "loc_added": pr["loc_added"], "metric_primary": pr["metrics"][0],
        "guardrail": pr["metrics"][2], "kill": pr["kill"],
    })

    return f"""{BRAND}

# SHIP — {name}

> Projekt: `{p[2]}` · Vygenerováno: {today} · {verdict}
> SHIP.md je primární handoff (1 stránka). Soubory per role jsou doplněk pro audit.

{triage_top}
## Co se mění

{p[4]}

## Odpovědnosti

| Role | Kdo |
|------|-----|
| **Decider** | {decider or '(nezadán)'} |
| **Branch owner / merger** | {branch_owner} |
| **Shadow PdM** (hlídá Async) | {shadow_pm} |

{winner_info}
{render_ai_usage_section(slug)}
## Rizikový profil

- **AI Act tier**: `{p[12]}` · **Data class**: `{p[13]}` · **Profil**: `{p[11]}` · **Risk profil**: `{triage['risk_profile']}`

{triage_section}
## Kill kritéria

{pr['kill']}

## Měření

- **Primary (lagging)**: {pr['metrics'][0]}
- **Leading**: {pr['metrics'][1]}
- **Guardrail**: {pr['metrics'][2]}
- **Instrumentace hotová**: 2 dny před nasazením

{pr_command}
## Co dál (T+0 → T+90)

- **Dnes**: PR otevřený, branch owner dělá review
- **T+1d**: PR merged, preview odkaz sdílen + `/pm retro {slug}` (`python3 tool/cli/retro.py measure --slug {slug} --pr-url <PR_URL>`) -> `loc_reused_pct` (cíl ≥ 80 %), `days_to_prod` (cíl ≤ 14)
- **Hned po merge**: připomínky T+7/30/60/90 -> `python3 tool/cli/retro.py reminders --slug {slug} --format ics --out data/retro/{slug}-reminders.ics`
- **T+7 dní**: feature flag 10 % uživatelů; kontrola instrumentace
- **T+14 dní**: 50 % uživatelů; první čtení metrik
- **T+30 dní**: plný rollout, nebo rollback podle kill kritérií; **změř, co z kódu přežilo** (níže)
- **T+7/30/60/90**: readouty přes `/pm retro {slug}` (tabulka `outcomes`, report `data/retro/{slug}-retro.md`)

{measure}
## Audit trail

- Audit log a decision log jsou v DB toolu (7letá retence, DORA); cesta: `pflanzer db`.
- Decision log pro git: `.pflanzer/decisions/{p[2]}.md` v target repu (commitnutý při Rozhodnutí).
- AI Act: pokud `tier=high`, Annex IV technická dokumentace před produkcí.
- GDPR: pokud `data_class=L3+`, aktualizace RoPA a DPIA.

---

*Soubory per role: `decision, be, fe, qa, platform, data, support, compliance` (`.md`) ve
výstupní složce (`pflanzer data`) slouží pro audit a hlubší pohled; u stolu je nikdo nečte.*
"""


def write_ship(slug: str) -> Path:
    project_dir = SHIP_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    out = project_dir / "SHIP.md"
    ctx = _fetch_ship_context(slug)
    wt = _winner_worktree(slug, ctx["winner"][0], ctx["extracted"]) if ctx["winner"] else None
    # Worktree trailer hook se přepne na `Pflanzer-Session: ship`.
    session_switched = _switch_worktree_session(wt)
    out.write_text(render_ship_md(slug), encoding="utf-8")

    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if proj:
            audit(
                conn, action="ship.render",
                target_type="project", target_id=int(proj[0]),
                payload={
                    "slug": slug, "file": out.name,
                    "blocked_by": ctx["triage"]["blocked_by"],
                    "worktree_session_ship": session_switched,
                },
            )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--print", action="store_true",
                   help="Vypiš SHIP.md na stdout (default: zapiš do výstupní složky)")
    p.add_argument("--pr-body", action="store_true",
                   help="Vypiš jen tělo PR (pro `gh pr create --body-file -`)")
    args = p.parse_args()

    if args.pr_body:
        print(build_pr(args.slug)["body"])
    elif args.print:
        print(render_ship_md(args.slug))
    else:
        path = write_ship(args.slug)
        print(json.dumps({
            "slug": args.slug,
            "ship_path": tilde(path),
            "next_step": (
                "Ukaž SHIP.md týmu. Decider nebo branch owner spustí `gh pr create` příkaz "
                "z konce SHIP.md (z worktree vítěze)."
            ),
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
