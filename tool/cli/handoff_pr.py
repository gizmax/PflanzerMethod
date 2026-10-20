"""Handoff — SHIP.md + podklady pro `gh pr create` (v0.5).

SHIP.md je primární handoff artefakt: 1 stránka (≤ ~60 řádků) s vítězem a popisem, tím, co se
mění, skóre quality gates ("X/100, práh Y" jednou větou), podpisy a AI náhradou, copy-paste
příkazem pro PR a tím, co měřit za 30 dní (`pflanzer retro …`, jednou). Detaily (brány, původ
kódu a podíl AI, AI náklady, critical poražených, Co selhalo, triage) jsou v `SHIP-detail.md`.
Osm souborů per role (`handoff.py`) je doplněk pro audit.

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
from tool.cli._compat import (  # noqa: E402
    ProjectNotFound,
    ai_stand_in_line,
    conditions_checklist,
    count,
    exit_if_project_missing,
    local_date,
    signatures_line,
    tips,
)
from tool.cli.charter import reviewer_hint  # noqa: E402
from tool.cli.db import audit, transaction  # noqa: E402
from tool.cli.extract import (  # noqa: E402
    BRAND,
    DATA_ROOT,
    WORKTREE_METHODS,
    base_gates_adapter,
    code_without_tests,
    find_worktree,
    public_repo_ref,
    repo_blocks,
    table_has_col,
    tilde,
)
from tool.cli.quality_gates import (  # noqa: E402
    GATE_TYPES,
    PRODUCTION_TARGET,
    UNVERIFIED_PREFIX,
    a11y_reasons,
    acceptance_unverified,
    aggregate_repos,
    aggregate_score,
    gates_summary_line,
    load_repo_gates,
    parse_test_failures,
    repo_key,
    repos_summary_line,
    skip_reasons,
    unverified_gates,
)
from tool.cli.session_2 import (  # noqa: E402
    describe_critical,
    get_winner,
    open_criticals,
    overridden_critical_md,
    overridden_criticals,
    resolved_criticals,
    strip_reason,
)
from tool.cli.session_3 import decider_genitive, gates_sufficiency  # noqa: E402
from tool.cli.triage import (  # noqa: E402
    human_triage_blockers,
    latest_threshold_override,
    path_owners,
    ship_triage_gate,
)
from tool.cli.ux import CzechArgumentParser, die, emit  # noqa: E402

SHIP_DIR = DATA_ROOT / "handoffs"
TEMPLATES_DIR = REPO_ROOT / "tool" / "templates" / "handoff"
BRAND_LINE = BRAND

_FALLBACK_MEASURE_30D = """## Změř po 30 dnech

Termín: 30 dní po merge. Změř: (1) kolik kódu vítěze (`{branch}` @ `{head_sha_short}`)
přežilo v `main`, (2) incidenty způsobené změnou, (3) metriku úspěchu vs. cíl
({metric_primary}). Kill kritérium: {kill}
Měření a připomínky: viz `SHIP.md`, sekce „Co měřit za 30 dní“.
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
    if not found and (details or "").lstrip().startswith("a11y:"):
        reasons = a11y_reasons(details, limit=limit)
        if reasons:
            return reasons
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


def origin_branch_state(wt: Path | None, branch: str) -> str:
    """Stav větve na originu podle LOKÁLNÍCH referencí (bez sítě); nikdy netvrdí víc, než ví."""
    if wt is None or not Path(wt).is_dir():
        return "stav na originu neověřen (worktree není k dispozici)"
    rc, out = _git(Path(wt), "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}")
    if rc == 0 and out.strip():
        return "větev má na originu referenci (podle lokální kopie; `git ls-remote` ověří živě)"
    return "větev zatím není na originu (podle lokální kopie) — pushne ji krok níže"


def decision_log_lines(slug: str) -> str:
    """Příkaz commit + push decision logu (+ podpisů oken); tool sám nepushuje."""
    return (f"git add .pflanzer/decisions/{slug}.md && git commit -m "
            f"\"docs({slug}): decision log a podpisy oken\" && git push -u origin HEAD"
            "   # 0. z repa, kde běželo Rozhodnutí; jinak se log do originu nedostane\n")


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
            raise ProjectNotFound(slug)
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
        overridden = [c for c in overridden_criticals(conn, project_id)
                      if winner and c["variant"] == winner[0]]
        owners = path_owners(conn, project_id)
        dev_owners = [
            r[0] for r in conn.execute(
                "SELECT human_owner FROM roles WHERE project_id = ? "
                "AND catalog_idx IN (4, 5) AND COALESCE(human_owner, '') != '' "
                "ORDER BY catalog_idx", (project_id,),
            ).fetchall()
        ]

    repo_gates = load_repo_gates(slug, winner[0]) if winner else []
    repos = repo_blocks(slug, winner[0]) if winner else []
    return {"project": proj, "winner": winner, "decided": decided, "extracted": ext,
            "repo_gates": repo_gates, "repos": repos,
            "gates": gate_rows, "decision": decision, "triage": triage_gate,
            "threshold_override": threshold_override,
            "variant_names": variant_names, "dev_owners": dev_owners,
            "winner_basis": winner_basis, "open_critical": criticals,
            "resolved_critical": resolved, "overridden_critical": overridden,
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
                 f"rozhodnutí #{o['decision_id']}, {o['at']}): {strip_reason(o['rationale'])}")
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

    def badge(g: Any) -> str:
        if g[1] in ("skipped", "unsupported") and str(g[3] or "").startswith(UNVERIFIED_PREFIX):
            return "NEOVĚŘENO"
        return label.get(g[1], "?")

    line = " · ".join(f"{badge(g)} {g[0]}" for g in gates)
    applicable = sum(1 for g in gates if g[1] in ("pass", "warn", "fail"))
    return line, applicable, len(gates)


def _verdict(score: int, target: int, unverified: list[dict[str, str]] | None = None) -> str:
    if target <= 0:
        return "informativně (throwaway)"
    if score < target:
        return "pod prahem"
    if unverified:
        return "splňuje práh ⚠ ale neověřeno: " + ", ".join(u["gate"] for u in unverified)
    return "splňuje práh"


def _ship_state(ctx: dict[str, Any]) -> dict[str, Any]:
    """Skóre vítěze (X/100), práh a blokace (triage, nedostatek bran)."""
    p, gates = ctx["project"], ctx["gates"]
    target = int(p[15]) if p[15] is not None else 80
    rg = ctx.get("repo_gates") or []
    if gates and rg:
        score = aggregate_repos(rg)["gate_score"]
    elif gates:
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
    if gates and rg:
        agg = aggregate_repos(rg)
        suff = dict(suff, sufficient=agg["sufficient"], blocker=agg["blocker"])
    if gates and target > 0 and not suff["sufficient"]:
        blocked_by.append(suff["blocker"])
    if gates and rg:
        unverified = [dict(u, reason=f"{e['role']}: {u['reason']}")
                      for e in rg for u in unverified_gates(e["results"])]
    else:
        unverified = unverified_gates([{"gate": g[0], "status": g[1], "details": g[3] or ""}
                                       for g in gates])
    unv_blocks = bool(gates and target >= PRODUCTION_TARGET and acceptance_unverified(unverified))
    if unv_blocks:
        blocked_by.append("gates:acceptance-neověřeno")
    # Výjimka z prahu (Decider, `session_3 --override-threshold`): jen pod prahem a bez jiné blokace.
    override = ctx.get("threshold_override")
    if gates and rg:
        hard = [repo_key(e["role"], r["gate"]) for e in rg for r in e["results"]
                if r["status"] == "fail" and r["gate"] in ("build", "tests", "smoke")]
    else:
        hard = [g[0] for g in gates if g[1] == "fail" and g[0] in ("build", "tests", "smoke")]
    below = score < target or bool(hard)
    if not (gates and target > 0 and below and not blocked_by):
        override = None
    if ctx["triage"]["blocked_by"]:
        verdict = "BLOKOVÁNO (triage)"
    elif unv_blocks and blocked_by == ["gates:acceptance-neověřeno"]:
        reason = next(u["reason"] for u in unverified if u["gate"] == "acceptance")
        verdict = f"nesplňuje práh: acceptance je neověřená ({reason})"
    elif blocked_by:
        verdict = "BLOKOVÁNO (nedostatek gates)"
    elif override:
        verdict = (("neprošlo brány" if hard and score >= target else "pod prahem")
                   + f" — Ship na odpovědnost Decidera ({override['decider']})")
    elif hard and target > 0 and score >= target:
        verdict = f"neprošlo — padá brána {', '.join(hard)} (skóre {score}/100 to nezachrání)"
    else:
        verdict = _verdict(score, target, unverified)
    return {"score": score, "target": target, "blocked_by": blocked_by, "verdict": verdict,
            "suff": suff, "unverified": unverified, "threshold_override": override,
            "ready": bool(gates) and target > 0 and not blocked_by
            and ((score >= target and not hard) or override is not None)}


def _render_threshold_override(override: dict[str, Any], score: int, target: int) -> str:
    """Sekce „Výjimka z prahu“ pro SHIP.md i tělo PR."""
    return (
        "## Výjimka z prahu\n\n"
        f"Skóre {score}/100 je pod prahem {target}. Ship jde na odpovědnost Decidera; "
        "PR je proto draft.\n\n"
        f"**Výjimka schválil:** {override['decider']} (Decider), "
        f"rozhodnutí #{override['decision_id']}\n\n"
        f"**Důvod:** {strip_reason(override['rationale'])}\n"
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


def _gate_summary(gates: list, repo_gates: list[dict[str, Any]] | None = None) -> str:
    """„78/100 z 5/9 bran; neběžely: types (důvod)“ ze zapsaných quality_gates.

    Ve vícerepu „web: 89/100 · api: 100/100 (celkem 94/100)“.
    """
    if repo_gates:
        return repos_summary_line(repo_gates, aggregate_repos(repo_gates)["gate_score"])
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
    hook = real(p[4]) or name
    try:  # starší projekty mají v hypotéze připojený label risk profilu — to není zadání uživatele
        from tool.cli.quick_session import RISK_PROFILES
        for prof in RISK_PROFILES.values():
            hook = hook.replace(f" {prof['label']}.", "").replace(prof["label"], "")
        hook = hook.strip() or name
    except (ImportError, AttributeError, KeyError, TypeError):
        pass
    lines = [hook]
    if metric_primary:
        lines.append(f"Metrika úspěchu: {metric_primary}")
    if w:
        desc = real(w[4])
        if desc:
            first = next((x.strip() for x in desc.split("\n\n") if x.strip()), desc)
            first = " ".join(first.lstrip("# ").split())
            lines.append(f"Vítěz {w[0]} — {trim_words(first, 300)}")
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


def _related_md(repos: list[dict[str, Any]], rg: list[dict[str, Any]], current: str,
                related: dict[str, str] | None) -> list[str]:
    """Sekce „Repa a související PR“: u každého jiného repa řádek „Související PR v <role> repu“."""
    lines = ["## Repa a související PR", "",
             "Změna zasahuje víc repozitářů a PR se mergují společně:"]
    for b in repos:
        e = next((x for x in rg if x["role"] == b["role"]), None)
        score = f", brány {e['gate_score']}/100" if e else ""
        head = f" @ `{b['head_sha'][:10]}`" if b.get("head_sha") else ""
        where = f"větev `{b['branch']}`{head}, base `{b['base']}`{score}"
        if b["role"] == current:
            lines.append(f"- **{b['role']}** (tento PR): {where}")
        else:
            url = (related or {}).get(b["role"])
            lines.append(f"- Související PR v {b['role']} repu: "
                         f"{url or 'odkaz se doplní po otevření (viz SHIP.md)'} — {where}")
    return lines + [""]


def _repo_size(b: dict[str, Any]) -> str | None:
    if b.get("added") is None:
        return None
    text = f"+{b['added']}" + (f" / -{b['removed']}" if b.get("removed") is not None else "")
    return text + " řádků" + (f" v {b['files']} souborech" if b.get("files") is not None else "")


def build_pr(slug: str, repo: str | None = None,
             related: dict[str, str] | None = None) -> dict[str, Any]:
    """Sestaví titulek, tělo PR (bez absolutních cest) a metadata.

    Vícerepo: `repo` = role repa, pro které se skládá tělo (default primární); `related`
    = {role: url PR} už otevřených PR v jiných repech (odkaz „související PR“).
    """
    ctx = _fetch_ship_context(slug)
    p, w, e, gates = ctx["project"], ctx["winner"], ctx["extracted"], ctx["gates"]
    rg: list[dict[str, Any]] = ctx.get("repo_gates") or []
    repos: list[dict[str, Any]] = ctx.get("repos") or []
    multi = len(repos) > 1
    if repo and (not multi or repo not in [b["role"] for b in repos]):
        raise ValueError(f"Repo „{repo}“ v projektu není"
                         + (f" (jsou: {', '.join(b['role'] for b in repos)})." if multi
                            else " (projekt má jeden target repo)."))
    cur_role = repo or (repos[0]["role"] if multi else None)
    name, decider = p[1], p[5]
    state = _ship_state(ctx)
    metric_primary, metric_leading, metric_guardrail = real(p[17]), real(p[18]), real(p[19])
    gate_score, target = state["score"], state["target"]
    kill = real(p[10])
    badges, applicable, total = _render_gate_badges(gates)
    if rg:
        per = [(x["role"], *_render_gate_badges(
            [(r["gate"], r["status"], r.get("metric"), r.get("details")) for r in x["results"]]))
            for x in rg]
        badges = "\n".join(f"- **{role}**: {line}" for role, line, _a, _t in per)
        applicable, total = sum(a for _r, _l, a, _t in per), sum(t for _r, _l, _a, t in per)
    dec_user = ctx["decision"][1] if ctx["decision"] else None
    dec_day = local_date(ctx["decision"][2]) if ctx["decision"] else None  # jako decision log
    dec_ts = dec_day.isoformat() if dec_day else (
        str(ctx["decision"][2])[:10] if ctx["decision"] else None)

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
    if multi:  # statistika per repo; loc_added = součet přes repa
        sized = [(b["role"], _repo_size(b), b["added"]) for b in repos if b.get("added") is not None]
        size_line = "; ".join(f"{role}: {txt}" for role, txt, _a in sized)
        loc_added = sum(a for _r, _t, a in sized) if sized else loc_added

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
    for b in repos[1:]:
        nt = code_without_tests(b["path"], b["base"]) if b.get("path") else None
        if nt and nt["missing_tests"]:
            warnings.append(
                f"Repo {b['role']}: nový kód bez testů ({nt['new_source_files']} nových "
                "zdrojových souborů, žádný nový ani změněný test).")
    if loc_added is not None and loc_added > 20000:
        warnings.append(
            "⚠ Rozsah vypadá nesmyslně — nejsou v commitu node_modules/ nebo build výstup?")
    if state["unverified"] and target > 0 and "NEOVĚŘENO" not in (
            (_gate_summary(gates, rg) if gates else None) or ""):
        warnings.append(
            "Neověřeno: " + ", ".join(f"{u['gate']} ({u['reason']})" for u in state["unverified"])
            + " — skóre o tom nic neříká.")
    failures = [(g[0], line) for g in gates if g[1] == "fail"
                for line in failure_lines(g[3] or "", root=wt)]
    if rg:
        failures = [(repo_key(x["role"], r["gate"]), line)
                    for x in rg for r in x["results"] if r["status"] == "fail"
                    for line in failure_lines(
                        r.get("details") or "",
                        root=Path(x["path"]) if x.get("path") and Path(x["path"]).is_dir() else None)]
    crit_lines = _criticals_md(ctx, w[0] if w else None)
    model = MODEL_FAMILY.get(builder)

    # Název PR = co vítěz dělá (popis varianty), ne useknutá věta zadání.
    desc_title = _PO_ITERATE_PREFIX.sub("", (_winner_description(w) or "").strip()).strip().rstrip(".")
    # Název PR = první celá část popisu (před ; — :), ať se neuseká uprostřed věty.
    desc_title = re.split(r"\s*[;—]\s*|\s+-\s+", desc_title)[0].strip()
    title_src = " ".join((desc_title or name).split())
    title_txt = trim_words(title_src, 60)
    if len(title_txt) < len(title_src):
        title_txt += "…"      # uříznuto na hranici slova -> je to vidět
    pr_title = f"feat({slug}): {title_txt}"
    pr_title_base = pr_title
    if cur_role:
        pr_title += f" ({cur_role})"
    summary = _gate_summary(gates, rg) if gates else None
    ai_line = ai_stand_in_line(slug)
    sign_line = signatures_line(slug)
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
    if multi:
        body_lines += [""] + _related_md(repos, rg, cur_role or "", related)[:-1]
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
    ov_md = overridden_critical_md(ctx.get("overridden_critical") or [])
    if ov_md:
        body_lines += ov_md.rstrip("\n").splitlines() + [""]
    if decider_line:
        body_lines += ["## Decider", decider_line, ""]
    if kill:
        body_lines += ["## Kill kritéria", kill, ""]
    metrics = [("Hlavní metrika", metric_primary), ("Ranná metrika", metric_leading),
               ("Pojistka (guardrail)", metric_guardrail)]
    if any(v for _, v in metrics):
        body_lines += ["## Měření"] + [f"- {k}: {v}" for k, v in metrics if v] + [""]
    if sign_line:
        body_lines += ["## Podpisy oken", sign_line, ""]
    cond_lines = conditions_checklist(slug)
    if cond_lines:
        body_lines += ["## Podmínky z podpisů oken (musí splnit tento PR)", *cond_lines, ""]
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
    if multi and repo and repo != repos[0]["role"]:
        b = next(x for x in repos if x["role"] == repo)
        x = next((y for y in rg if y["role"] == repo), None)
        head = f" @ `{b['head_sha'][:10]}`" if b.get("head_sha") else ""
        own_fail = [(g, ln) for g, ln in failures if g.startswith(f"{repo}:")]
        sec = [BRAND, "", "## Co se mění", *_what_changes(p, w, name, metric_primary),
               f"Tento PR obsahuje část v repu {repo}.", "",
               "## Výstup Pflanzer Method",
               f"- Varianta: `{w[0] if w else '—'}` ({builder}), větev `{b['branch']}`{head}, "
               f"base `{b['base']}`",
               f"- Brány repa {repo}: "
               + (gates_summary_line(x["gate_score"], x["results"]) if x else "neběžely")
               + f"; celkem {gate_score}/100 (práh {target}) - {state['verdict']}"]
        if _repo_size(b):
            sec.append(f"- Rozsah: {_repo_size(b)}")
        if x:
            sec += ["", f"## Automatické kontroly ({repo})",
                    _render_gate_badges([(r["gate"], r["status"], r.get("metric"), r.get("details"))
                                         for r in x["results"]])[0], ""]
        else:
            sec.append("")
        if own_fail:
            sec += ["## Co selhalo"] + [f"- {g}: {ln}" for g, ln in own_fail] + [""]
        sec += _related_md(repos, rg, repo, related)
        if decider_line:
            sec += ["## Decider", decider_line, ""]
        if kill:
            sec += ["## Kill kritéria", kill, ""]
        sec += ["---", "*Vygenerováno Pflanzer Method (`/pm handoff`).*"]
        if state["threshold_override"]:
            sec[-2:-2] = _render_threshold_override(
                state["threshold_override"], gate_score, target).splitlines() + [""]
        body_lines = sec
    return {
        "repos": repos, "repo_gates": rg, "size_line": size_line, "repo_role": cur_role,
        "title_base": pr_title_base,
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
        "signatures": sign_line, "conditions": cond_lines,
        "decider_line": decider_line,
    }


def _ship_parts(slug: str) -> dict[str, Any]:
    """Společné podklady pro SHIP.md (1 stránka) i SHIP-detail.md (brány, provenance, náklady)."""
    pr = build_pr(slug)
    ctx, state = pr["ctx"], pr["state"]
    p, w, e = ctx["project"], ctx["winner"], ctx["extracted"]
    target_branch = p[7] or "main"
    parts: dict[str, Any] = {
        "pr": pr, "ctx": ctx, "state": state, "p": p, "w": w, "e": e,
        "target_repo": public_repo_ref(p[6]), "target_branch": target_branch,
        "branch_owner": real(p[8]),
        "shadow_pm": real(p[9]) or real(ctx["path_owners"].get("produkt")),
        "triage": ctx["triage"], "winner_block": None,
    }
    if not (w and e):
        return parts
    builder, wt, prov = pr["builder"], pr["worktree"], pr["provenance"]
    adapter_warnings: list[str] = []
    if wt is not None:
        adapter = base_gates_adapter(wt, target_branch)
        if adapter.get("tmp_dir"):
            shutil.rmtree(adapter["tmp_dir"], ignore_errors=True)
        adapter_warnings = adapter["warnings"]
    feat_branch = f"pflanzer/{slug}-{w[0]}"
    trailers = [f"Pflanzer-Variant: {slug}-{w[0]}", "Pflanzer-Session: ship"]
    if builder != "manual":
        trailers.append(f"AI-Assisted: {builder}")
    labels = ["pflanzer", f"pflanzer:{slug}"]
    if builder != "manual":
        labels.insert(1, "ai-generated")
    repos = pr.get("repos") or []
    other_prov: list[tuple[str, dict[str, Any]]] = []
    for b in repos[1:]:
        other_prov.append((b["role"], check_provenance(
            slug=slug, variant=w[0], builder=builder, target_branch=b["base"],
            worktree=b.get("path"))))
    parts["winner_block"] = {
        "other_prov": other_prov,
        "builder": builder, "wt": wt, "prov": prov, "adapter_warnings": adapter_warnings,
        "feat_branch": feat_branch, "trailers": trailers, "labels": labels,
        "work_dir": tilde(wt) if wt else e[1],
    }
    return parts


# „C po Iterate: …“ je poznámka k variantě, ne název změny — do titulku PR nepatří.
_PO_ITERATE_PREFIX = re.compile(r"^\S{1,12}\s+po\s+Iterate\s*[:—–-]\s*", re.I)


def _built_phrase(names: list[str]) -> str:
    """„3 funkčních variantách“ / „jedné společné variantě“ podle skutečného počtu variant."""
    n = len(names)
    if n <= 1:
        return "jedné společně postavené variantě (mob)" if names == ["mob"] else "jedné variantě"
    return {2: "dvou funkčních variantách", 3: "třech funkčních variantách"}.get(
        n, f"{n} funkčních variantách")


def _variants_line(names: list[str]) -> str:
    if len(names) <= 1:
        return "jedna společná varianta" + (f" ({names[0]})" if names else "")
    return f"{len(names)} " + ("postaveny" if len(names) < 5 else "postaveno") + f" ({'/'.join(names)})"


def _winner_description(w: Any) -> str | None:
    """První odstavec popisu vítěze (ne boilerplate), nebo None."""
    desc = real(w[4]) if w else None
    if not desc:
        return None
    first = next((x.strip() for x in desc.split("\n\n") if x.strip()), desc)
    return trim_words(" ".join(first.lstrip("# ").split()), 300)


def _pr_command_multi_md(slug: str, parts: dict[str, Any]) -> str:
    """Vícerepo: per repo blok (commit, push větve, PR do base toho repa), PR se vzájemně odkazují."""
    wb, pr, state = parts["winner_block"], parts["pr"], parts["state"]
    repos = pr["repos"]
    label_flags = " ".join(f'--label "{lbl}"' for lbl in wb["labels"])
    label_create = "\n".join(
        f'gh label create "{lbl}" --force --color {"D93F0B" if lbl == "ai-generated" else "5319E7"}'
        for lbl in wb["labels"])
    draft_flag = " \\\n    --draft" if (state["blocked_by"] or state["threshold_override"]) else ""
    commit_msg = "\n".join(wb["trailers"])
    blocks: list[str] = []
    prev: list[tuple[str, str]] = []  # (role, proměnná s URL už otevřeného PR)
    for i, b in enumerate(repos, 1):
        role = b["role"]
        var = f"PR_{re.sub(r'[^A-Za-z0-9]', '_', role).upper()}"
        wd = tilde(b["path"]) if b.get("path") else f"(worktree repa {role} chybí: `pflanzer worktree setup --slug {slug}`)"
        title = f"{pr['title_base']} ({role})"
        related = "".join(f' --related "{r}=${v}"' for r, v in prev)
        blocks.append(f"""### {i}. Repo `{role}` (base `{b['base']}`, větev `{b['branch']}`)

```bash
cd {wd}
git add -A -- . ':(exclude)*.egg-info/*'
git diff --cached --quiet || git commit -F - <<'COMMITMSG'
{title}

{commit_msg}
COMMITMSG
git push -u origin {b['branch']}
{label_create}
{var}=$(pflanzer handoff_pr --slug {slug} --pr-body --repo {role}{related} | gh pr create \\
    --title {shlex.quote(title)} --body-file - \\
    --base {b['base']} \\
    {label_flags}{draft_flag})
```
""")
        prev.append((role, var))
    first = repos[0]["role"]
    back = "\n".join(
        f'pflanzer handoff_pr --slug {slug} --pr-body --repo {b["role"]}'
        + "".join(f' --related "{r}=${v}"' for r, v in prev if r != b["role"])
        + f' | gh pr edit "${prev[i][1]}" --body-file -'
        for i, b in enumerate(repos[:-1]))
    return f"""## Otevři PR (každé repo zvlášť)

Projekt má {len(repos)} repa ({', '.join(b['role'] for b in repos)}); PR se otevírají v každém repu
a v těle se odkazují jako „Související PR v <repo> repu“. Autor commitu = dev u klávesnice;
AI nikdy jako author ani `Co-Authored-By` (jen trailery). Reviewera přidejte ručně
(`--reviewer <github-handle>`). {reviewer_hint(slug)} Mergujte společně.

### 0. Decision log

```bash
{decision_log_lines(slug)}```

{chr(10).join(blocks)}
### {len(repos) + 1}. Provázání

Do dřív otevřených PR doplň odkazy na pozdější (repo `{first}` ještě nevědělo o ostatních):

```bash
{back}
```
"""


def _pr_command_md(slug: str, parts: dict[str, Any]) -> str:
    """Krátký copy-paste blok: commit s trailery, push, labely, `gh pr create` (tělo z --pr-body)."""
    wb, pr, state = parts["winner_block"], parts["pr"], parts["state"]
    if len(pr.get("repos") or []) > 1:
        return _pr_command_multi_md(slug, parts)
    # Review dělá někdo, kdo u Buildu nebyl — ne branch owner/builder.
    reviewer = None
    label_flags = " ".join(f'--label "{lbl}"' for lbl in wb["labels"])
    label_create = "\n".join(
        f'gh label create "{lbl}" --force --color {"D93F0B" if lbl == "ai-generated" else "5319E7"}'
        for lbl in wb["labels"])
    commit_msg = f"{pr['title']}\n\n" + "\n".join(wb["trailers"])
    draft_flag = " \\\n  --draft" if (state["blocked_by"] or state["threshold_override"]) else ""
    reviewer_flag = f"  --reviewer {reviewer} \\\n" if reviewer else ""
    return f"""## Otevři PR

Autor commitu = dev u klávesnice; AI nikdy jako author ani `Co-Authored-By` (jen trailery).
Reviewera přidejte ručně (`--reviewer <github-handle>`). {reviewer_hint(slug)}

```bash
{decision_log_lines(slug)}cd {wb['work_dir']}
git add -A -- . ':(exclude)*.egg-info/*'
git diff --cached --quiet || git commit -F - <<'COMMITMSG'
{commit_msg}
COMMITMSG
git push -u origin {pr['branch']}
{label_create}
pflanzer handoff_pr --slug {slug} --pr-body | gh pr create \\
  --title {shlex.quote(pr['title'])} --body-file - \\
  --base {parts['target_branch']} \\
{reviewer_flag}  {label_flags}{draft_flag}
```
"""


def _measure_md(slug: str, pr: dict[str, Any]) -> str:
    """„Co měřit za 30 dní“ — jediné místo v SHIP.md, kde se mluví o retru."""
    if pr["target"] <= 0:   # throwaway: žádné přežití LOC ani T+30/60/90, jen metrika dema
        lines = []
        for k, v in (("Hlavní metrika dema", pr["metrics"][0]), ("Ranná metrika", pr["metrics"][1])):
            if v:
                lines.append(f"- {k}: {v}")
        if pr["kill"]:
            lines.append(f"- Kill kritérium: {pr['kill']}")
        lines.append("- Kód je throwaway a nejde do produkce, neměří se jeho přežití. Změř jen "
                     f"metriku dema v jejím termínu; připomínka: `pflanzer retro reminders "
                     f"--slug {slug} --format ics --out {slug}-pripominka.ics`")
        return "## Co měřit u dema\n\n" + "\n".join(lines) + "\n"
    lines = [
        "- Kolik kódu vítěze přežilo v `main` a za kolik dní se dostal do produkce (cíl ≥ 80 %, "
        "≤ 14 dní). Po merge, z worktree vítěze: "
        f"`pflanzer retro measure --slug {slug} --pr-url \"$(gh pr view --json url -q .url)\"`",
    ]
    for k, v in (("Hlavní metrika", pr["metrics"][0]), ("Ranná metrika", pr["metrics"][1]),
                 ("Pojistka (guardrail)", pr["metrics"][2])):
        if v:
            lines.append(f"- {k}: {v}")
    if pr["kill"]:
        lines.append(f"- Kill kritérium: {pr['kill']}")
    lines.append(f"- Čtení T+7/30/60/90: `pflanzer retro report --slug {slug}`; připomínky do "
                 f"kalendáře: `pflanzer retro reminders --slug {slug} --format ics "
                 f"--out {slug}-pripominky.ics`")
    return "## Co měřit za 30 dní\n\n" + "\n".join(lines) + "\n"


def _cond_word(n: int) -> str:
    return "podmínka" if n == 1 else "podmínky" if 2 <= n <= 4 else "podmínek"


def render_ship_md(slug: str, parts: dict[str, Any] | None = None) -> str:
    """SHIP.md — jedna stránka (≤ ~60 řádků). Detaily jsou v SHIP-detail.md."""
    parts = parts or _ship_parts(slug)
    pr, state, p, w = parts["pr"], parts["state"], parts["p"], parts["w"]
    name, decider = p[1], p[5]
    score, target, verdict = pr["gate_score"], pr["target"], state["verdict"]
    triage = parts["triage"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    triage_top = ""
    if triage["blocked_by"]:
        who = human_triage_blockers(slug, triage["windows"])
        triage_top = ("\n> ## BLOKOVÁNO: chybí podpisy oken\n"
                      + "".join(f"> - {m}\n" for m in who[:3])
                      + (f"> - …a další ({len(who) - 3})\n" if len(who) > 3 else "")
                      + f"> Decider může přebít: `pflanzer session_3 --slug {slug} "
                        "--override-triage --rationale \"…\"`\n")
    ovc_md = overridden_critical_md(parts["ctx"].get("overridden_critical") or [])
    threshold_md = (ovc_md + "\n" if ovc_md else "") + (
        _render_threshold_override(state["threshold_override"], score, target) + "\n"
        if state["threshold_override"] else "")
    ov = triage.get("override")
    sec_gap = ov and any(b.startswith(("triage:security", "triage:legal"))
                         for b in ov.get("blocked_by", []))
    gap_notes = ([f"Ship na odpovědnost {decider_genitive(ov.get('decider') or 'Decider')}: "
                  "bezpečnost nepodepsal člověk."] if sec_gap else [])
    cond_lines = pr.get("conditions") or []
    cond_notes = ([f"{len(cond_lines)} {_cond_word(len(cond_lines))} z podpisů oken musí splnit PR "
                   "(sekce Podmínky z podpisů oken)."] if cond_lines else [])
    verdict_notes = "".join(f"> Pozor: {x}\n" for x in [*gap_notes, *cond_notes, *pr["warnings"]])

    winner_md = "" if w else "## Vítěz\n\nVítěz zatím není vybraný (Rozhodnutí → Go).\n"
    first = real(p[4]) or name
    if w:
        verb = (f"Ověřili jsme na {_built_phrase(pr['variants'])}"
                + ("." if len(pr["variants"]) <= 1 else f"; vyhrála {w[0]}."))
        first = re.sub(r"Ověříme ho na (?:třech funkčních variantách|jedné společně postavené "
                       r"variantě)[^.]*\.", verb, first)
    changes = [first]
    if pr["metrics"][0]:
        changes.append(f"Metrika úspěchu: {pr['metrics'][0]}")
    if w:
        desc = _winner_description(w)
        changes.append(f"Vítěz {w[0]}" + (f" — {desc}" if desc else "."))
    changes_md = "## Co se mění\n\n" + "\n\n".join(changes) + "\n"

    score_line = (pr["gates_summary"] or f"{score}/100") + (
        " — Throwaway: skóre je informativní, Ship neblokuje" if target <= 0
        else f" (práh {target}) — {verdict}")
    if len(pr.get("repos") or []) > 1 and pr.get("size_line"):
        score_line += f". Rozsah: {pr['size_line']}"
    elif pr["loc_added"] is not None:
        score_line += f". Rozsah: +{pr['loc_added']} řádků"
    owner_rows = [("Decider", real(decider)), ("Branch owner / merger", parts["branch_owner"]),
                  ("Shadow PdM (hlídá Async)", parts["shadow_pm"])]
    people = [f"- {k}: {v}" for k, v in owner_rows if v]
    if pr.get("signatures"):
        people.append(f"- Podepsaná okna: {pr['signatures']}")
    if pr["ai_stand_in"]:
        people.append(f"- Kroky s AI náhradou (ADR-0023): {pr['ai_stand_in']}")
    people_md = ("## Podpisy a odpovědnosti\n\n" + "\n".join(people) + "\n\n") if people else ""
    if cond_lines:
        people_md += ("## Podmínky z podpisů oken\n\nPodepsáno s podmínkami; PR je musí splnit "
                      "(checklist je i v těle PR):\n\n" + "\n".join(cond_lines) + "\n\n")

    pr_command = _pr_command_md(slug, parts) if parts["winner_block"] else ""
    md = f"""{BRAND}

# SHIP — {name}

> Projekt: `{p[2]}` · {today} · {verdict}
> Detaily (brány, původ kódu, AI náklady, kritické na poražených): `SHIP-detail.md`
{verdict_notes}{triage_top}
{winner_md}
{changes_md}
## Skóre

{score_line}

{people_md}{threshold_md}{pr_command}
{_measure_md(slug, pr)}"""
    return re.sub(r"\n{3,}", "\n\n", md)


def render_ship_detail_md(slug: str, parts: dict[str, Any] | None = None) -> str:
    """SHIP-detail.md — brány, AI provenance, AI náklady, critical poražených, Co selhalo, triage."""
    parts = parts or _ship_parts(slug)
    pr, state, ctx, p, w = parts["pr"], parts["state"], parts["ctx"], parts["p"], parts["w"]
    score, target, verdict = pr["gate_score"], pr["target"], state["verdict"]
    triage = parts["triage"]
    _top, triage_section = _render_triage_block(triage, slug)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    wb = parts["winner_block"]

    winner_info = ""
    if wb:
        builder, prov = wb["builder"], wb["prov"]
        skipped = skip_reasons([{"gate": g[0], "status": g[1], "details": g[3] or ""}
                                for g in ctx["gates"]])
        skipped_md = ("\nNeběžely (důvod):\n" + "\n".join(f"- {x}" for x in skipped) + "\n"
                      if skipped else "")
        suff = state["suff"]
        gates_md = (
            f"{suff['gates_run']}/{len(GATE_TYPES)} spuštěno"
            + ("" if suff["sufficient"] else f" - `{suff['blocker']}` (viz tool/templates/README-gates.md)")
        ) if ctx["gates"] else "(Ship ještě neběžel)"
        adapter_md = "\n".join(f"- {x}" for x in wb["adapter_warnings"]) or (
            "- gates běžely s adaptérem z base branche (nebo autodetekcí); worktree ho nemění.")
        prov_warn = "\n".join(f"  - {x}" for x in prov["warnings"]) or (
            f"  - {prov['commits']} commit(ů) na `{prov['base']}..{wb['feat_branch']}` "
            "má trailery, autor = člověk, bez AI `Co-Authored-By`.")
        ai_md = (f"- **Kroky s AI náhradou (ADR-0023)**: {pr['ai_stand_in']}\n"
                 if pr["ai_stand_in"] else "")
        extra_parts: list[str] = []
        if len(pr.get("repos") or []) > 1:
            rows = []
            for b in pr["repos"]:
                x = next((y for y in pr["repo_gates"] if y["role"] == b["role"]), None)
                rows.append(
                    f"| {b['role']} | `{b['branch']}` | `{b['base']}` | "
                    + (f"**{x['gate_score']}/100**" if x else "—") + " | "
                    + (_repo_size(b) or "—") + " |")
            prov_others = "".join(
                f"- repo {role}: " + ("; ".join(pv["warnings"]) or
                                      f"{pv['commits']} commit(ů), trailery v pořádku") + "\n"
                for role, pv in wb.get("other_prov", []))
            extra_parts.append(
                "\n### Repa\n\n| Repo | Větev | Base | Gate skóre | Rozsah |\n"
                "|------|-------|------|------------|--------|\n" + "\n".join(rows) + "\n"
                + ("\nKontrola commitů v dalších repech:\n\n" + prov_others if prov_others else ""))
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
        winner_info = f"""## Vítěz

- **Varianta**: `{w[0]}` (`{builder}`)
- **Vybrán podle**: {_winner_basis_md(ctx['winner_basis'])}
- **Větev**: `{pr['branch']}`{f" @ `{pr['head_sha'][:10]}`" if pr['head_sha'] else ''} (target repo `{parts['target_repo']}`) — {origin_branch_state(wb['wt'], pr['branch'])}
{f"- **Rozsah**: {pr['loc_added']} přidaných řádků" + chr(10) if pr['loc_added'] is not None else ''}- **Brány**: {pr['gates_summary'] or str(score) + '/100'} (práh {target}) - {verdict}

### Automatické kontroly ({pr['applicable']} z {pr['total']} aplikovatelných)

{pr['badges']}
{skipped_md}
- **Spuštěno bran**: {gates_md}
{''.join(extra_parts)}
### Gate adaptér - integrita

{adapter_md}

## Původ kódu a podíl AI

{ai_md}- **Nástroj (builder)**: `{builder}`{f" · **Model**: {pr['model']}" if pr['model'] else ''}
- **Varianty**: {_variants_line(pr['variants'])}, do PR jde {'tato varianta' if len(pr['variants']) <= 1 else 'vítěz ' + w[0]}
{f"- **U klávesnice**: {', '.join(pr['keyboard'])}" + chr(10) if pr['keyboard'] else ''}
- **Kontrola `{wb['feat_branch']}`** (read-only, historie se nepřepisuje):
{prov_warn}
"""

    measure = render_measure_30d({
        "slug": slug, "branch": pr["branch"], "head_sha_short": (pr["head_sha"] or "")[:10],
        "loc_added": pr["loc_added"], "metric_primary": pr["metrics"][0] or "dle Kickoffu",
        "guardrail": pr["metrics"][2], "kill": pr["kill"] or "viz Kickoff",
    })
    return f"""{BRAND}

# SHIP — detail — {p[1]}

> Projekt: `{p[2]}` · {today} · {verdict}
> Hlavní stránka je `SHIP.md`; tady jsou podklady pro audit a review.

{winner_info}
{render_ai_usage_section(slug)}
## Rizikový profil

- **AI Act tier**: `{p[12]}` · **Data class**: `{p[13]}` · **Profil**: `{p[11]}` · **Risk profil**: `{triage['risk_profile']}`

{triage_section}
{measure}
## Záznam rozhodnutí

- Audit log a decision log jsou v DB toolu (retence 7 let nastavená v nástroji); cesta: `pflanzer db`.
- Decision log pro git: `.pflanzer/decisions/{p[2]}.md` v target repu (zapsaný při Rozhodnutí; do originu ho dostane krok 0 v sekci „Otevři PR“ v `SHIP.md`).
- AI Act: pokud `tier=high`, Annex IV technická dokumentace před produkcí.
- GDPR: pokud `data_class=L3+`, aktualizace RoPA a DPIA.

---

*Soubory per role: `decision, be, fe, qa, platform, data, support, compliance` (`.md`) ve
výstupní složce (`pflanzer data`) jsou doplněk pro audit.*
"""


def write_ship(slug: str) -> Path:
    project_dir = SHIP_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    out = project_dir / "SHIP.md"
    ctx = _fetch_ship_context(slug)
    wt = _winner_worktree(slug, ctx["winner"][0], ctx["extracted"]) if ctx["winner"] else None
    # Worktree trailer hook se přepne na `Pflanzer-Session: ship`.
    session_switched = _switch_worktree_session(wt)
    parts = _ship_parts(slug)
    out.write_text(render_ship_md(slug, parts), encoding="utf-8")
    (project_dir / "SHIP-detail.md").write_text(render_ship_detail_md(slug, parts), encoding="utf-8")

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
    multi = len(pr.get("repos") or []) > 1
    nxt = ("Ukaž SHIP.md týmu a " + (f"{owner} (branch owner) " if owner else "branch owner ")
           + "spustí `gh pr create` z konce SHIP.md ("
           + ("z worktree vítěze v každém repu: " + ", ".join(b["role"] for b in pr["repos"])
              if multi else "z worktree vítěze") + ").")
    return {"lines": lines[:6], "warnings": warnings, "next_step": nxt,
            "ctx": {"open_critical": bool(pr["critical_lines"]),
                    "below_threshold": state["score"] < state["target"]}}


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer handoff_pr", description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--print", action="store_true",
                   help="Vypiš SHIP.md na stdout (default: zapiš do výstupní složky)")
    p.add_argument("--pr-body", action="store_true",
                   help="Vypiš jen tělo PR (pro `gh pr create --body-file -`)")
    p.add_argument("--repo", default=None,
                   help="Vícerepo: role repa, pro které se skládá tělo PR (default primární)")
    p.add_argument("--related", action="append", default=[], metavar="ROLE=URL",
                   help="Vícerepo: už otevřený PR v jiném repu (odkaz „související PR“); opakovatelné")
    p.add_argument("--json", action="store_true", help="Výstup jako JSON (pro skripty)")
    args = p.parse_args()

    try:
        related: dict[str, str] = {}
        for item in args.related:
            role, sep, url = item.partition("=")
            if not sep or not role.strip() or not url.strip():
                die(f"--related čeká ROLE=URL, dostal jsem „{item}“.",
                    "--related web=https://github.com/firma/web/pull/12")
            related[role.strip()] = url.strip()
        if args.pr_body:
            print(build_pr(args.slug, repo=args.repo, related=related)["body"])
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
        exit_if_project_missing(e)
        die(f"{e} Přehled projektů: `pflanzer status`.", "pflanzer handoff_pr --slug moje-appka")


if __name__ == "__main__":
    main()
