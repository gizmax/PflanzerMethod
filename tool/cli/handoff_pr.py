"""Handoff — SHIP.md + podklady pro `gh pr create` (v0.5).

SHIP.md je primární handoff artefakt: 1 stránka s tím, co se mění, kdo to merguje,
skóre quality gates vítěze ("X/100, práh Y"), kill kritériem, měřením a copy-paste
příkazem pro PR. Osm souborů per role (`handoff.py`) je doplněk pro audit.

Pravidla výstupu:
- první řádek je brand line,
- žádné absolutní lokální cesty v textu určeném do PR (jen větev, SHA, název),
- výstupy do `<DATA_ROOT>/handoffs/<slug>/`.

Ship (audit N5 + N11 + N16):
- vítěz = vítěz z Rozhodnutí; bez něj varianta s nejvyšším gate skóre (tie-break skóre z Buildu),
- triage tvrdá brána: pilot/production s nedokončeným triage = blok "BLOKOVÁNO", nikdy
  "splňuje práh" (leda s override Decidera z `session_3 --override-triage`); totéž při
  méně než 4 reálně spuštěných bránách nebo bez build/tests,
- skóre pod prahem + `session_3 --override-threshold` = SHIP.md i PR body mají sekci
  „Výjimka z prahu“ (důvod, Decider) a PR je draft,
- AI code provenance (07-handoff-do-vyvoje.md § AI code provenance): trailery
  `Pflanzer-Variant` / `Pflanzer-Session: ship` / `AI-Assisted`, PR labely `ai-generated`
  + `pflanzer:<slug>`, sekce „Původ kódu a podíl AI“ v PR body a read-only kontrola
  `base..pflanzer/<slug>-<W>` (historie se nepřepisuje; autor commitu je vždy člověk),
- sekce "AI náklady (viditelnost)" z transcriptů Claude Code (`ai_usage.py`); jen viditelnost,
  nikdy brána,
- sekce "Změř po 30 dnech" odkazuje na `/pm retro` (outcomes T+7/30/60/90).

Nevyplněné údaje (metriky, kill kritéria, jména) se v PR ani v SHIP.md neukazují jako
placeholdery: sekce bez dat se vynechá. Shadow PdM = shadow_pm, jinak zástupce kroku Produkt.

Rozhraní:
    pflanzer handoff_pr --slug S [--print] [--pr-body] [--json]
"""
from __future__ import annotations

import argparse
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
from tool.cli._compat import ai_stand_in_line, count, tips  # noqa: E402
from tool.cli.db import audit, transaction  # noqa: E402
from tool.cli.extract import (  # noqa: E402
    BRAND,
    DATA_ROOT,
    WORKTREE_METHODS,
    base_gates_adapter,
    code_without_tests,
    find_worktree,
    public_repo_ref,
    table_has_col,
    tilde,
)
from tool.cli.quality_gates import (  # noqa: E402
    GATE_TYPES,
    aggregate_score,
    gates_summary_line,
    parse_test_failures,
    skip_reasons,
)
from tool.cli.session_2 import (  # noqa: E402
    describe_critical,
    get_winner,
    open_criticals,
    resolved_criticals,
)
from tool.cli.session_3 import decider_genitive, gates_sufficiency  # noqa: E402
from tool.cli.triage import (  # noqa: E402
    human_triage_blockers,
    latest_threshold_override,
    path_owners,
    ship_triage_gate,
)
from tool.cli.ux import die, emit  # noqa: E402

SHIP_DIR = DATA_ROOT / "handoffs"
TEMPLATES_DIR = REPO_ROOT / "tool" / "templates" / "handoff"
BRAND_LINE = BRAND

_FALLBACK_MEASURE_30D = """## Změř po 30 dnech

Termín: 30 dní po merge. Změř: (1) kolik kódu vítěze (`{branch}` @ `{head_sha_short}`)
přežilo v `main`, (2) incidenty způsobené změnou, (3) metriku úspěchu vs. cíl
({metric_primary}). Kill kritérium: {kill}
Měření a připomínky vede `/pm retro {slug}` (`pflanzer retro measure --slug {slug}`).
"""

_PLACEHOLDER_RE = re.compile(r"doplnit|doplň|nezadán|nezadáno|^tbd|^\W*$|\btodo\b", re.IGNORECASE)


def real(value: Any) -> str | None:
    """Skutečně vyplněná hodnota, nebo None (prázdné, `TBD…`, „doplň…“, „nezadán“)."""
    text = str(value).strip() if value is not None else ""
    return None if not text or _PLACEHOLDER_RE.search(text) else text


def trim_words(text: str, limit: int) -> str:
    """Zkrať na hranici slova (bez useknutého slova a bez visících interpunkčních znaků)."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0] if " " in text[:limit + 1] else text[:limit]
    return cut.rstrip(" ,;:-–—(") or text[:limit]


_ASSERT_RE = re.compile(r"^E\s|AssertionError|\bassert\b|Expected|expected|FAILED|✗|×|Error:", re.M)


def failure_lines(details: str, limit: int = 3, root: Path | None = None) -> list[str]:
    """Řádky „Co selhalo“: u testů (Node TAP, jest, vitest, pytest) `název — co se čekalo`.

    Cesty jsou relativní k repu (`root`); ostatní brány dostanou jeden užitečný řádek.
    """
    if root is not None:
        for r in {str(root), str(root.resolve())}:
            details = (details or "").replace(r + "/", "")
    found = parse_test_failures(details)
    if not found:
        return [failure_line(details)]
    out = [trim_words(f"{name} — {detail}" if detail else name, 160) for name, detail in found[:limit]]
    if len(found) > limit:
        out.append(f"…a {count(len(found) - limit, 'další test', 'další testy', 'dalších testů')}")
    return out


def failure_line(details: str) -> str:
    """Užitečný řádek z výstupu selhané brány: assertion, ne konec stack trace."""
    found = parse_test_failures(details)
    if found:
        name, detail = found[0]
        line = f"{name} — {detail}" if detail else name
        if len(found) > 1:
            line = f"{count(len(found), 'test', 'testy', 'testů')} selhalo, např. {line}"
        return trim_words(line, 160)
    lines = [ln.strip() for ln in (details or "").splitlines() if ln.strip()]
    for ln in lines:  # pytest: řádky `E   assert 4 == 5` nesou vyhodnocenou chybu
        if re.match(r"^E\s+\S", ln):
            return trim_words(ln[1:].strip(), 160)
    for ln in lines:
        if _ASSERT_RE.search(ln) and not ln.startswith("Traceback"):
            return trim_words(ln, 160)
    return trim_words(lines[0], 160) if lines else "(bez detailu)"


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


# Builder -> rodina modelu pro sekci „Původ kódu“ v PR (bez verzí).
MODEL_FAMILY = {
    "claude-code": "Claude (Anthropic)",
    "codex-cli": "GPT / Codex (OpenAI)",
    "cursor": "dle nastavení Cursoru",
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
        threshold_override = None
        if winner and gate_rows and proj[15] is not None:
            _score = aggregate_score(
                [SimpleNamespace(gate_type=g[0], status=g[1]) for g in gate_rows]  # type: ignore[misc]
            )["gate_score"]
            threshold_override = latest_threshold_override(
                conn, project_id, score=_score, target=int(proj[15]))
        criticals = open_criticals(conn, project_id)
        resolved = resolved_criticals(conn, project_id)
        owners = path_owners(conn, project_id)
        dev_owners = [
            r[0] for r in conn.execute(
                "SELECT human_owner FROM roles WHERE project_id = ? "
                "AND catalog_idx IN (4, 5) AND COALESCE(human_owner, '') != '' "
                "ORDER BY catalog_idx", (project_id,),
            ).fetchall()
        ]

    return {"project": proj, "winner": winner, "decided": decided, "extracted": ext,
            "gates": gate_rows, "decision": decision, "triage": triage_gate,
            "threshold_override": threshold_override,
            "variant_names": variant_names, "dev_owners": dev_owners,
            "winner_basis": winner_basis, "open_critical": criticals,
            "resolved_critical": resolved,
            "path_owners": owners}


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
        note += (f"\n\n**Výjimku schválil:** {o.get('decider') or 'Decider'} (Decider; "
                 f"rozhodnutí #{o['decision_id']}, {o['at']}): {o['rationale']}")
    section = f"""## Triage stav

{note}

| Track | Stav | Podepsal |
|-------|------|----------|
{rows}
"""
    top = ""
    if triage["blocked_by"]:
        who = "\n".join(f"> - {m}" for m in human_triage_blockers(slug, triage["windows"]))
        top = f"""> ## BLOKOVÁNO: chybí podpisy oken
>
> Produkční nasazení není povoleno, dokud okna nepodepíšou lidé z kroků cesty:
{who}
>
> Decider může přebít jen s důvodem do decision logu:
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
        return "(automatické kontroly ještě neběžely - `/pm ship`)", 0, 0
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
    try:
        from tool.cli.checkpoint import design_gate
        if target > 0 and design_gate(p[2]).get("blocks_ship"):
            blocked_by.append("design:nepotvrzeno")
    except Exception:  # noqa: BLE001
        pass
    suff = gates_sufficiency({"results": [{"gate": g[0], "status": g[1]} for g in gates]})
    if gates and target > 0 and not suff["sufficient"]:
        blocked_by.append(suff["blocker"])
    # Výjimka z prahu (Decider, `session_3 --override-threshold`): jen pod prahem a bez jiné blokace.
    override = ctx.get("threshold_override")
    if not (gates and target > 0 and score < target and not blocked_by):
        override = None
    if ctx["triage"]["blocked_by"]:
        verdict = "BLOKOVÁNO (triage)"
    elif blocked_by:
        verdict = "BLOKOVÁNO (nedostatek gates)"
    elif override:
        verdict = f"pod prahem — Ship na odpovědnost Decidera ({override['decider']})"
    else:
        verdict = _verdict(score, target)
    return {"score": score, "target": target, "blocked_by": blocked_by, "verdict": verdict,
            "suff": suff, "threshold_override": override,
            "ready": bool(gates) and target > 0 and not blocked_by
            and (score >= target or override is not None)}


def _render_threshold_override(override: dict[str, Any], score: int, target: int) -> str:
    """Sekce „Výjimka z prahu“ pro SHIP.md i tělo PR."""
    return (
        "## Výjimka z prahu\n\n"
        f"Skóre {score}/100 je pod prahem {target}. Ship jde na odpovědnost Decidera; "
        "PR je proto draft.\n\n"
        f"**Výjimka schválil:** {override['decider']} (Decider), "
        f"rozhodnutí #{override['decision_id']}\n\n"
        f"**Důvod:** {override['rationale']}\n"
    )


def _winner_basis_md(basis: dict[str, Any]) -> str:
    cmp_ = ", ".join(f"{k}={v}" for k, v in sorted((basis.get("compared") or {}).items()))
    if basis["mode"] == "decision":
        return (f"Rozhodnutí (Go s vítězem {basis['winner']})"
                + (f"; gate skóre: {cmp_}" if cmp_ else ""))
    if basis["mode"] == "ship_gate":
        return f"Ship - nejvyšší gate skóre (tie-break skóre z Buildu); porovnáno: {cmp_}"
    if basis["mode"] == "preference":
        return "fallback - nejvyšší skóre z Buildu (Ship ještě neběžel, žádné quality_gates)"
    return "—"


def _gate_summary(gates: list) -> str:
    """„78/100 z 5/9 bran; neběžely: types (důvod)“ ze zapsaných quality_gates."""
    rows = [{"gate": g[0], "status": g[1], "details": g[3] or ""} for g in gates]
    score = aggregate_score(
        [SimpleNamespace(gate_type=g[0], status=g[1]) for g in gates]  # type: ignore[misc]
    )["gate_score"]
    return gates_summary_line(score, rows)


def _criticals_md(ctx: dict[str, Any], winner_name: str | None) -> list[str]:
    """Řádky o otevřených kritických: na vítězi (blokují Go), na poražených jen informativně."""
    crit = ctx.get("open_critical") or []
    on_win = [c for c in crit if winner_name and c["variant"] == winner_name]
    on_lost = [c for c in crit if not winner_name or c["variant"] != winner_name]
    lines: list[str] = []
    for c in on_win:
        lines.append(f"- Na vítězi: {describe_critical(c)}")
    for c in on_lost:
        lines.append(f"- Informativně, poražená varianta: {describe_critical(c)}")
    return lines


def _what_changes(p: Any, w: Any, name: str, metric_primary: str | None) -> list[str]:
    """Sekce „Co se mění“: hook, metrika úspěchu a vítěz s popisem (ne boilerplate o metodě)."""
    lines = [real(p[4]) or name]
    if metric_primary:
        lines.append(f"Metrika úspěchu: {metric_primary}")
    if w:
        desc = real(w[4])
        if desc:
            first = next((x.strip() for x in desc.split("\n\n") if x.strip()), desc)
            first = " ".join(first.lstrip("# ").split())
            lines.append(f"Vítěz {w[0]}: {trim_words(first, 300)}")
        else:
            lines.append(f"Vítěz {w[0]}.")
    return lines


def _resolved_line(c: dict[str, Any]) -> str:
    """„#3 Lucie (krok Bezpečnost): „text“ — vyřešeno: Ondra: opraveno v PR“."""
    text = " ".join((c.get("rationale") or "").split())
    text = trim_words(text, 90) if text else ""
    who = c.get("submitted_by") or "neznámý autor"
    return (f"- #{c['id']} {who} (krok {c['department']})"
            + (f": „{text}“" if text else "")
            + (f" — vyřešeno: {c['resolved_note']}" if c.get("resolved_note") else " — vyřešeno"))


def build_pr(slug: str) -> dict[str, Any]:
    """Sestaví titulek, tělo PR (bez absolutních cest) a metadata."""
    ctx = _fetch_ship_context(slug)
    p, w, e, gates = ctx["project"], ctx["winner"], ctx["extracted"], ctx["gates"]
    name, decider = p[1], p[5]
    state = _ship_state(ctx)
    metric_primary, metric_leading, metric_guardrail = real(p[17]), real(p[18]), real(p[19])
    gate_score, target = state["score"], state["target"]
    kill = real(p[10])
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
                       if g[0] == "acceptance" and g[1] != "skipped" and g[2] is not None), None)

    decider_line = real(decider) or real(dec_user)
    if decider_line and dec_user and real(decider) and dec_user.strip() != decider.strip():
        decider_line += f" (zapsal {dec_user})"
    if decider_line and dec_ts:
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
    try:
        from tool.cli.quick_session import keyboard_owner
        kb_owner = keyboard_owner(slug)
    except Exception:  # noqa: BLE001
        kb_owner = None
    keyboard = [kb_owner] if kb_owner else ((prov["authors"] if prov else None)
                                            or ctx["dev_owners"] or [])
    variants = ctx["variant_names"] or ([w[0]] if w else [])
    notests = code_without_tests(wt, p[7] or "main") if wt else None
    warnings: list[str] = []
    if notests and notests["missing_tests"]:
        warnings.append(
            f"Nový kód bez testů: {notests['new_source_files']} nových zdrojových souborů, "
            "žádný nový ani změněný test.")
    failures = [(g[0], line) for g in gates if g[1] == "fail"
                for line in failure_lines(g[3] or "", root=wt)]
    crit_lines = _criticals_md(ctx, w[0] if w else None)
    model = MODEL_FAMILY.get(builder)

    pr_title = f"feat({slug}): {trim_words(name, 60)}"
    summary = _gate_summary(gates) if gates else None
    ai_line = ai_stand_in_line(slug)
    resolved_on_win = [c for c in ctx.get("resolved_critical", [])
                       if w and c["variant"] == w[0]]
    body_lines: list[str] = [BRAND, "", "## Co se mění", *_what_changes(p, w, name, metric_primary),
                             "", "## Výstup Pflanzer Method",
                             f"- Varianta: `{w[0] if w else '—'}` ({builder}), větev `{branch or '—'}`"
                             + (f" @ `{head_sha[:10]}`" if head_sha else "")]
    if w:
        body_lines.append(f"- Hlasování jádra v Buildu: {float(w[3] or 0):.2f} (0–1, vyšší = lepší)")
    body_lines.append(f"- Brány: {summary or str(gate_score) + '/100'} (práh {target}) - "
                      f"{state['verdict']}")
    if acceptance:
        body_lines.append(f"- Acceptance: {acceptance}")
    if size_line:
        body_lines.append(f"- Rozsah: {size_line}")
    body_lines += ["", f"## Automatické kontroly ({applicable} z {total} aplikovatelných)", badges, ""]
    if failures:
        body_lines += ["## Co selhalo"] + [f"- {g}: {line}" for g, line in failures] + [""]
    if warnings:
        body_lines += ["## Pozor"] + [f"- {x}" for x in warnings] + [""]
    if crit_lines:
        body_lines += ["## Otevřené kritické připomínky"] + crit_lines + [""]
    if resolved_on_win:
        body_lines += ["## Vyřešené kritické připomínky (vítěz)"] + [
            _resolved_line(c) for c in resolved_on_win] + [""]
    if decider_line:
        body_lines += ["## Decider", decider_line, ""]
    if kill:
        body_lines += ["## Kill kritéria", kill, ""]
    metrics = [("Hlavní metrika", metric_primary), ("Ranná metrika", metric_leading),
               ("Pojistka (guardrail)", metric_guardrail)]
    if any(v for _, v in metrics):
        body_lines += ["## Měření"] + [f"- {k}: {v}" for k, v in metrics if v] + [""]
    if ai_line:
        body_lines += ["## Kroky s AI náhradou (ADR-0023)", ai_line, ""]
    prov_lines = [f"- Nástroj (builder): {builder}"]
    if model:
        prov_lines.append(f"- Model: {model}")
    if variants:
        prov_lines.append(f"- Varianty: {len(variants)} postaveny ({'/'.join(variants)}), "
                          f"do PR jde vítěz {w[0] if w else '—'}")
    if keyboard:
        prov_lines.append(f"- U klávesnice: {', '.join(keyboard)}")
    body_lines += ["## Původ kódu a podíl AI", *prov_lines, "",
                   "---", "*Vygenerováno Pflanzer Method (`/pm handoff`).*"]
    if state["threshold_override"]:
        at = body_lines.index("## Decider") if "## Decider" in body_lines else len(body_lines) - 3
        body_lines[at:at] = _render_threshold_override(
            state["threshold_override"], gate_score, target).splitlines() + [""]
    return {
        "ctx": ctx, "state": state, "title": pr_title, "body": "\n".join(body_lines),
        "branch": branch, "head_sha": head_sha, "loc_added": loc_added,
        "gate_score": gate_score, "target": target, "badges": badges,
        "gates_summary": summary,
        "metrics": (metric_primary, metric_leading, metric_guardrail),
        "applicable": applicable, "total": total, "kill": kill,
        "builder": builder, "worktree": wt, "provenance": prov,
        "keyboard": keyboard, "variants": variants, "warnings": warnings,
        "failures": failures, "critical_lines": crit_lines, "model": model,
        "resolved_critical": resolved_on_win, "ai_stand_in": ai_line,
        "decider_line": decider_line,
    }


def render_ship_md(slug: str) -> str:
    pr = build_pr(slug)
    ctx, state = pr["ctx"], pr["state"]
    p, w, e = ctx["project"], ctx["winner"], ctx["extracted"]
    name, decider = p[1], p[5]
    target_repo = public_repo_ref(p[6])
    target_branch = p[7] or "main"
    branch_owner = real(p[8])
    shadow_pm = real(p[9]) or real(ctx["path_owners"].get("produkt"))
    score, target, verdict = pr["gate_score"], pr["target"], state["verdict"]
    blocked_by = state["blocked_by"]
    triage = ctx["triage"]
    triage_top, triage_section = _render_triage_block(triage, slug)
    threshold_md = (_render_threshold_override(state["threshold_override"], score, target) + "\n"
                    if state["threshold_override"] else "")
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
        reviewer = branch_owner if (branch_owner and " " not in branch_owner) else None
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
        skipped = skip_reasons([{"gate": g[0], "status": g[1], "details": g[3] or ""}
                                for g in ctx["gates"]])
        skipped_md = ("\nNeběžely (důvod):\n" + "\n".join(f"- {x}" for x in skipped) + "\n"
                      if skipped else "")
        ai_line = ai_stand_in_line(slug)
        ai_md = f"- **Kroky s AI náhradou (ADR-0023)**: {ai_line}\n" if ai_line else ""
        suff = state["suff"]
        gates_md = (
            f"{suff['gates_run']}/{len(GATE_TYPES)} spuštěno"
            + ("" if suff["sufficient"] else f" - `{suff['blocker']}` (viz tool/templates/README-gates.md)")
        ) if ctx["gates"] else "(Ship ještě neběžel)"
        draft_flag = " \\\n  --draft" if (blocked_by or state["threshold_override"]) else ""
        reviewer_flag = f"  --reviewer {reviewer} \\\n" if reviewer else ""
        work_dir = tilde(wt) if wt else e[1]
        extra_parts: list[str] = []
        if pr["failures"]:
            extra_parts.append("\n### Co selhalo\n\n" + "\n".join(
                f"- {g}: {line}" for g, line in pr["failures"]) + "\n")
        if pr["warnings"]:
            extra_parts.append("\n### Pozor\n\n" + "\n".join(f"- {x}" for x in pr["warnings"]) + "\n")
        if pr["critical_lines"]:
            extra_parts.append("\n### Otevřené kritické připomínky\n\n"
                               + "\n".join(pr["critical_lines"]) + "\n")
        if pr["resolved_critical"]:
            extra_parts.append("\n### Vyřešené kritické připomínky (vítěz)\n\n"
                               + "\n".join(_resolved_line(c) for c in pr["resolved_critical"])
                               + "\n")
        extra_md = "".join(extra_parts)
        winner_info = f"""## Vítěz

- **Varianta**: `{w[0]}` (`{builder}`)
- **Vybrán podle**: {_winner_basis_md(ctx['winner_basis'])}
- **Větev**: `{pr['branch']}`{f" @ `{pr['head_sha'][:10]}`" if pr['head_sha'] else ''} v `{target_repo}`
{f"- **Rozsah**: {pr['loc_added']} přidaných řádků" + chr(10) if pr['loc_added'] is not None else ''}- **Brány**: {pr['gates_summary'] or str(score) + '/100'} (práh {target}) - {verdict}

### Automatické kontroly ({pr['applicable']} z {pr['total']} aplikovatelných)

{pr['badges']}
{skipped_md}
- **Spuštěno bran**: {gates_md}
{extra_md}
### Gate adaptér - integrita

{adapter_md}

## Původ kódu a podíl AI

{ai_md}- **Nástroj (builder)**: `{builder}`{f" · **Model**: {pr['model']}" if pr['model'] else ''}
- **Varianty**: {len(pr['variants'])} postaveny ({'/'.join(pr['variants'])}), do PR jde vítěz {w[0]}
{f"- **U klávesnice**: {', '.join(pr['keyboard'])}" + chr(10) if pr['keyboard'] else ''}
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
{reviewer_flag}  {label_flags}{draft_flag}
```
"""

    measure = render_measure_30d({
        "slug": slug, "branch": pr["branch"], "head_sha_short": (pr["head_sha"] or "")[:10],
        "loc_added": pr["loc_added"], "metric_primary": pr["metrics"][0] or "dle Kickoffu",
        "guardrail": pr["metrics"][2], "kill": pr["kill"] or "viz Kickoff",
    })
    owner_rows = [("Decider", real(decider)), ("Branch owner / merger", branch_owner),
                  ("Shadow PdM (hlídá Async)", shadow_pm)]
    owners_md = "\n".join(f"| **{k}** | {v} |" for k, v in owner_rows if v)
    owners_section = (f"## Odpovědnosti\n\n| Role | Kdo |\n|------|-----|\n{owners_md}\n"
                      if owners_md else "")
    metrics_rows = [("Hlavní metrika", pr["metrics"][0]), ("Ranná metrika", pr["metrics"][1]),
                    ("Pojistka (guardrail)", pr["metrics"][2])]
    measure_md = "\n".join(f"- **{k}**: {v}" for k, v in metrics_rows if v)
    measure_section = f"## Měření\n\n{measure_md}\n\n" if measure_md else ""
    kill_section = f"## Kill kritéria\n\n{pr['kill']}\n\n" if pr["kill"] else ""
    ov = triage.get("override")
    sec_gap = ov and any(b.startswith(("triage:security", "triage:legal"))
                         for b in ov.get("blocked_by", []))
    gap_notes = ([f"Ship na odpovědnost {decider_genitive(ov.get('decider') or 'Decider')}: "
                  "bezpečnost nepodepsal člověk."] if sec_gap else [])
    verdict_notes = "".join(f"> Pozor: {x}\n" for x in [*gap_notes, *pr["warnings"]])
    what_md = "\n\n".join(_what_changes(p, w, name, pr["metrics"][0]))

    return f"""{BRAND}

# SHIP — {name}

> Projekt: `{p[2]}` · Vygenerováno: {today} · {verdict}
> SHIP.md je primární handoff (1 stránka). Soubory per role jsou doplněk pro audit.
{verdict_notes}
{triage_top}{threshold_md}## Co se mění

{what_md}

{owners_section}
{winner_info}
{render_ai_usage_section(slug)}
## Rizikový profil

- **AI Act tier**: `{p[12]}` · **Data class**: `{p[13]}` · **Profil**: `{p[11]}` · **Risk profil**: `{triage['risk_profile']}`

{triage_section}
{kill_section}{measure_section}{pr_command}
## Co dál (T+0 → T+90)

- **Dnes**: PR otevřený, branch owner dělá review
- **T+1d**: PR merged, preview sdílen; `pflanzer retro measure --slug {slug} --pr-url "$(gh pr view --json url -q .url)"` (URL PR vypíše `gh pr create`) — kolik kódu vítěze přežilo a za kolik dní se dostal do produkce
- **Hned po merge**: připomínky do kalendáře: `pflanzer retro reminders --slug {slug} --format ics --out {slug}-pripominky.ics`
- **T+7 / 30 / 60 / 90 dní**: čtení metrik přes `/pm retro {slug}`
- **T+30 dní**: plný rollout, nebo rollback podle kill kritérií; **změř, co z kódu přežilo** (níže)

{measure}
## Záznam rozhodnutí

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
                    "threshold_override": bool(_ship_state(ctx)["threshold_override"]),
                    "worktree_session_ship": session_switched,
                },
            )
    return out


def _human_ship_md(slug: str, path: Path) -> dict[str, Any]:
    """Data pro lidský výstup po zápisu SHIP.md."""
    pr = build_pr(slug)
    state, ctx = pr["state"], pr["ctx"]
    owner = real(ctx["project"][8])
    lines = [f"SHIP.md: {tilde(path)}",
             f"Brány: {pr['gates_summary'] or str(pr['gate_score']) + '/100'} "
             f"(práh {pr['target']}) — {state['verdict']}"]
    human = human_triage_blockers(slug, ctx["triage"]["windows"]) if ctx["triage"]["blocked_by"] else []
    lines += human[:2]
    for x in pr["failures"][:1]:
        lines.append(f"Selhalo {x[0]}: {x[1]}")
    lines += pr["critical_lines"][:1]
    warnings = list(pr["warnings"])
    if state["blocked_by"] and not human:
        warnings.append("PR půjde jako draft: " + ", ".join(state["blocked_by"]))
    nxt = ("Ukaž SHIP.md týmu a " + (f"{owner} (branch owner) " if owner else "branch owner ")
           + "spustí `gh pr create` z konce SHIP.md (z worktree vítěze).")
    return {"lines": lines[:6], "warnings": warnings, "next_step": nxt,
            "ctx": {"open_critical": bool(pr["critical_lines"]),
                    "below_threshold": state["score"] < state["target"]}}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--print", action="store_true",
                   help="Vypiš SHIP.md na stdout (default: zapiš do výstupní složky)")
    p.add_argument("--pr-body", action="store_true",
                   help="Vypiš jen tělo PR (pro `gh pr create --body-file -`)")
    p.add_argument("--json", action="store_true", help="Výstup jako JSON (pro skripty)")
    args = p.parse_args()

    try:
        if args.pr_body:
            print(build_pr(args.slug)["body"])
        elif args.print:
            print(render_ship_md(args.slug))
        else:
            path = write_ship(args.slug)
            view = _human_ship_md(args.slug, path)
            emit({"slug": args.slug, "ship_path": tilde(path), "next_step": view["next_step"]},
                 title=f"SHIP.md hotový: {args.slug}", lines=view["lines"],
                 warnings=view["warnings"], next_step=view["next_step"],
                 tips=tips(args.slug, "handoff", view["ctx"]), as_json=args.json)
    except ValueError as e:
        die(f"{e} Přehled projektů: `pflanzer status`.", "pflanzer handoff_pr --slug moje-appka")


if __name__ == "__main__":
    main()
