"""Sprint 3 — SHIP.md + auto `gh pr create` command.

Per autoresearch synthesis ADR-0010 + perspektiva 02 vibe-product:
> "Handoff package: 8 files → 1-page SHIP.md + auto-rendered `gh pr create`
>  command within 30s of Session 3. The 8 per-role MDs are compliance theater
>  nobody reads."

Tento modul:
1. Render `data/handoffs/<slug>/SHIP.md` — 1 stránka markdown s:
   - Co se mění (variant, branch, files touched)
   - Kdo to merguje (target_branch_owner z Charteru)
   - Quality gate score badges
   - Acceptance criteria pass rate
   - Kill criteria + rollback plán
   - Copy-paste `gh pr create` command (s pre-filled title + body)
2. Output je primary handoff artefakt; 8 per-role files (handoff.py)
   degraduje na supplementary.

Audit N5 + N11 additions:
- triage hard gate: pilot/production with any triage track not 'ok' renders
  a prominent "Blokováno" block and never claims PRODUCTION-READY (unless a
  Decider override from `session_3.py --override-triage` covers it),
- AI code provenance (07-handoff-do-vyvoje.md § AI code provenance): commit
  trailers `Pflanzer-Variant` / `Pflanzer-Session: ship` / `AI-Assisted`,
  PR labels `ai-generated` + `pflanzer:<slug>`, PR body "AI provenance"
  section, and a read-only trailer/author check of `base..pflanzer/<slug>-<W>`
  (history is never rewritten; the commit author is always the human).

Audit N16: "AI náklady (viditelnost)" section — Claude Code token usage per
variant from the session transcripts on this machine (`ai_usage.py`), with a
fallback to the last `ai_usage` DB snapshot. Visibility only, never a gate.
"""
from __future__ import annotations

import argparse
import json
import re
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
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.extract import WORKTREE_METHODS, base_gates_adapter, find_worktree  # noqa: E402
from tool.cli.quality_gates import GATE_TYPES, _display_path, aggregate_score  # noqa: E402
from tool.cli.session_3 import gates_sufficiency  # noqa: E402
from tool.cli.triage import ship_triage_gate  # noqa: E402

SHIP_DIR = REPO_ROOT / "data" / "handoffs"
BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"

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

        # Winner = the Ship gate winner: highest gate_score over each variant's
        # latest gate run (tie-break preference_score), same rule as
        # session_3.py. Only without any gate rows fall back to preference_score.
        sess1 = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1",
            (proj[0],),
        ).fetchone()
        winner = None
        winner_ext_id: int | None = None
        winner_basis: dict[str, Any] = {"mode": "none"}
        if sess1:
            variant_rows = conn.execute(
                """
                SELECT v.name, v.builder, v.prototype_url, v.preference_score,
                       v.description_md, v.id
                FROM variants v
                WHERE v.session_id = ?
                ORDER BY v.preference_score DESC, v.name
                """, (sess1[0],),
            ).fetchall()
            scored: list[tuple[int, float, Any, int]] = []
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
            if scored:
                best = max(scored, key=lambda x: (x[0], x[1]))
                winner, winner_ext_id = best[2], best[3]
                winner_basis = {
                    "mode": "ship_gate", "gate_score": best[0],
                    "compared": {x[2][0]: x[0] for x in scored},
                }
            elif variant_rows:
                winner = variant_rows[0]
                winner_basis = {"mode": "preference"}

        # Extracted code path + gate scores per variant
        ext_rows = []
        if winner:
            ext_rows = list(conn.execute(
                """
                SELECT e.id, e.local_path, e.extraction_method, e.files_count,
                       e.total_loc
                FROM extracted_code e
                WHERE e.variant_id = ? AND (? IS NULL OR e.id = ?)
                ORDER BY e.id DESC LIMIT 1
                """, (winner[5], winner_ext_id, winner_ext_id),
            ).fetchall())

        # Per-gate detail
        gate_rows = []
        if ext_rows:
            gate_rows = list(conn.execute(
                "SELECT gate_type, status, metric_value, details_md "
                "FROM quality_gates WHERE extracted_id = ? ORDER BY id",
                (ext_rows[0][0],),
            ).fetchall())

        # Decision rationale
        decision = conn.execute(
            "SELECT body_md, atribuce_user FROM decisions "
            "WHERE project_id = ? AND type = 'handoff' "
            "ORDER BY id DESC LIMIT 1", (proj[0],),
        ).fetchone()

        # Triage hard gate (N5) + provenance context (N11)
        triage_gate = ship_triage_gate(conn, int(proj[0]))
        variant_names = [
            r[0] for r in conn.execute(
                "SELECT name FROM variants WHERE session_id = ? ORDER BY name",
                (sess1[0],),
            ).fetchall()
        ] if sess1 else []
        dev_owners = [
            r[0] for r in conn.execute(
                "SELECT human_owner FROM roles WHERE project_id = ? "
                "AND catalog_idx IN (4, 5) AND COALESCE(human_owner, '') != '' "
                "ORDER BY catalog_idx", (proj[0],),
            ).fetchall()
        ]

    return {
        "project": proj,
        "winner": winner,
        "extracted": ext_rows[0] if ext_rows else None,
        "gates": gate_rows,
        "decision": decision,
        "triage": triage_gate,
        "variant_names": variant_names,
        "dev_owners": dev_owners,
        "winner_basis": winner_basis,
    }


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


def _render_triage_block(triage: dict[str, Any], slug: str) -> tuple[str, str]:
    """Return (top_block, section) markdown for the triage state."""
    icons = {"ok": "✅", "deferred": "⏸", "failed": "❌", "pending": "⏳", "missing": "—"}
    rows = "\n".join(
        f"| {t['track']} | {icons.get(t['display'], '?')} {t['display']} | {t['signed_by'] or '—'} |"
        for t in triage["tracks"]
    )
    note = (
        f"Risk profil `{triage['risk_profile']}` — triage je hard gate pro production."
        if triage["gated"] else
        f"Risk profil `{triage['risk_profile']}` — triage gate se neuplatňuje."
    )
    if triage["override"]:
        o = triage["override"]
        note += (f"\n\n**Decider override** (decision #{o['decision_id']}, {o['by']}, {o['at']}): "
                 f"{o['rationale']}")
    section = f"""## Triage stav

{note}

| Track | Stav | Signed by |
|-------|------|-----------|
{rows}
"""
    top = ""
    if triage["blocked_by"]:
        top = f"""> ## ⛔ Blokováno: spusť `/pm triage {slug}`
>
> Production launch není povolen — {', '.join(f'`{b}`' for b in triage['blocked_by'])}.
> Decider override jen s rationale do decision logu:
> `python3 tool/cli/session_3.py --slug {slug} --override-triage --rationale "…"`
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


def _render_gate_badges(gates: list) -> str:
    icons = {"pass": "✅", "warn": "⚠️", "fail": "❌",
             "skipped": "⏭️", "unsupported": "—"}
    return " ".join(f"{icons.get(g[1], '?')} {g[0]}" for g in gates) or "(no gates run yet)"


def render_ship_md(slug: str) -> str:
    ctx = _fetch_ship_context(slug)
    p = ctx["project"]
    w = ctx["winner"]
    e = ctx["extracted"]
    gates = ctx["gates"]

    name, decider = p[1], p[5]
    target_repo = p[6] or "(target_repo_url unset — set in Charter)"
    target_branch = p[7] or "main"
    branch_owner = p[8] or "(target_branch_owner unset)"
    shadow_pm = p[9] or "(shadow_pm unset — per perspektiva 02 needed)"
    kill = p[10] or "TBD"
    basis = ctx["winner_basis"]
    gate_score = int(basis["gate_score"]) if basis["mode"] == "ship_gate" else int(p[14] or 0)
    target = int(p[15] if p[15] is not None else 80)
    throwaway = p[11]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    triage = ctx["triage"]
    blocked_by = list(triage["blocked_by"])
    suff = gates_sufficiency({"results": [{"gate": g[0], "status": g[1]} for g in gates]})
    if gates and not suff["sufficient"]:
        blocked_by.append(suff["blocker"])
    ready = bool(gates) and gate_score >= target and not blocked_by
    if triage["blocked_by"]:
        verdict = "⛔ **BLOKOVÁNO (triage)**"
    elif blocked_by:
        verdict = "⛔ **BLOKOVÁNO (nedostatek gates)**"
    else:
        verdict = "🚀 **PRODUCTION-READY**" if ready else "⚠ **PILOT-ONLY**"
    triage_top, triage_section = _render_triage_block(triage, slug)

    if basis["mode"] == "ship_gate":
        compared = ", ".join(f"{k}={v}" for k, v in sorted(basis["compared"].items()))
        winner_basis_md = (
            f"Ship gate — nejvyšší gate_score (tie-break preference_score); porovnáno: {compared}"
        )
    elif basis["mode"] == "preference":
        winner_basis_md = (
            "fallback — nejvyšší preference_score ze Session 1 (Ship gate ještě neběžel, "
            "žádné quality_gates rows)"
        )
    else:
        winner_basis_md = "—"

    winner_info = ""
    pr_command = ""
    provenance: dict[str, Any] | None = None
    if w and e:
        feat_branch = f"pflanzer/{slug}-{w[0]}"
        builder = w[1]
        wt = _winner_worktree(slug, w[0], e)
        adapter_warnings: list[str] = []
        if wt is not None:
            adapter = base_gates_adapter(wt, target_branch)
            if adapter.get("tmp_dir"):
                shutil.rmtree(adapter["tmp_dir"], ignore_errors=True)
            adapter_warnings = adapter["warnings"]
        provenance = check_provenance(
            slug=slug, variant=w[0], builder=builder,
            target_branch=target_branch, worktree=wt,
        )
        keyboard = provenance["authors"] or ctx["dev_owners"] or ["(doplň — dev u klávesnice)"]
        variants = ctx["variant_names"] or [w[0]]
        work_dir = str(wt) if wt else e[1]
        pr_title = f"feat({slug}): {name[:60]}"
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
        pr_body_lines = [
            "## Co se mění",
            f"{p[4]}",  # xyz_hypothesis
            "",
            "## Pflanzer session output",
            f"- **Variant**: `{w[0]}` (`{w[1]}`)",
            f"- **Preference score**: {w[3]:.2f}",
            f"- **Gate score**: **{gate_score}/{target}** ({verdict})",
            "- **Acceptance pass rate**: " +
            next((f"{int(g[2])} %" for g in gates if g[0] == "acceptance" and g[2] is not None), "N/A"),
            f"- **Files**: {e[3]} ({e[4]} LOC)",
            f"- **Local path**: `{e[1]}`",
            "",
            "## Quality gates",
            f"{_render_gate_badges(gates)}",
            "",
            "## Decider",
            f"{decider} — {ctx['decision'][1] if ctx['decision'] else current_actor()}",
            "",
            "## Kill criteria",
            f"{kill}",
            "",
            "## Measurement plan",
            f"- Primary lagging: {p[17] or 'TBD'}",
            f"- Leading: {p[18] or 'TBD'}",
            f"- Guardrail: {p[19] or 'TBD'}",
            "",
            "## AI provenance",
            f"- **Builder**: {builder}",
            f"- **Model family**: {MODEL_FAMILY.get(builder, 'doplň')}",
            f"- **Varianty**: {len(variants)} postaveny ({'/'.join(variants)}), do PR jde winner {w[0]}",
            f"- **U klávesnice**: {', '.join(keyboard)} (git author commitů)",
            f"- **Decision log**: `data/handoffs/{slug}/SHIP.md` + `decisions` v Pflanzer DB",
            "",
            "---",
            "*Generated by Pflanzer Method (pflanzer.cz/method) — `/pm handoff` per ADR-0010.*",
        ]
        pr_body = "\n".join(pr_body_lines)
        commit_msg = f"{pr_title}\n\n" + "\n".join(trailers)

        prov_warn = "\n".join(f"  - ⚠ {x}" for x in provenance["warnings"]) or (
            f"  - ✅ {provenance['commits']} commit(ů) na `{provenance['base']}..{feat_branch}` "
            "má trailery, autor = člověk, bez AI `Co-Authored-By`."
        )
        adapter_md = "\n".join(f"- ⚠ {x}" for x in adapter_warnings) or (
            "- ✅ gates běžely s adaptérem z base branche (nebo autodetekcí); worktree ho nemění."
        )
        gates_md = (
            f"{suff['gates_run']}/{len(GATE_TYPES)} spuštěno"
            + ("" if suff["sufficient"] else f" — ⛔ `{suff['blocker']}` (viz tool/templates/README-gates.md)")
        ) if gates else "(Ship gate ještě neběžel)"
        winner_info = f"""## 🏆 Winner

- **Variant**: `{w[0]}` (`{w[1]}`)
- **Vybrán podle**: {winner_basis_md}
- **Branch**: `{feat_branch}` v `{target_repo}`
- **Code**: `{e[1]}` ({e[3]} files / {e[4]} LOC)
- **Gate score**: **{gate_score}/{target}** {verdict}

### Quality gates

{_render_gate_badges(gates)}

- **Gates run**: {gates_md}

### Gate adaptér — integrita

{adapter_md}

## AI provenance

- **Builder**: `{builder}` · **Model family**: {MODEL_FAMILY.get(builder, 'doplň')}
- **Varianty**: {len(variants)} postaveny ({'/'.join(variants)}), do PR jde winner {w[0]}
- **U klávesnice**: {', '.join(keyboard)}
- **Kontrola `{feat_branch}`** (read-only, historie se nepřepisuje):
{prov_warn}
"""
        reviewer = branch_owner if branch_owner != '(target_branch_owner unset)' else 'YOUR-GH-HANDLE'
        draft_flag = " \\\n  --draft" if blocked_by else ""
        pr_command = f"""## 📤 Open PR (copy-paste)

Autor commitu = **dev u klávesnice** (`git config user.name` / `user.email`
ve worktree). AI nikdy jako author ani `Co-Authored-By` — AI asistenci
značí jen trailery níže (07-handoff-do-vyvoje.md § AI code provenance).

```bash
cd {work_dir}

# Ship commit s provenance trailery (jen pokud je co commitnout)
git add -A
git diff --cached --quiet || git commit -F - <<'COMMITMSG'
{commit_msg}
COMMITMSG

git push -u origin {feat_branch}

# Labely musí v target repu existovat (idempotentní)
{label_create}

gh pr create \\
  --title "{pr_title}" \\
  --body "$(cat <<'PRBODY'
{pr_body}
PRBODY
)" \\
  --base {target_branch} \\
  --reviewer {reviewer} \\
  {label_flags}{draft_flag}
```
"""

    return f"""{BRAND_LINE}

# SHIP — {name}

> Slug: `{p[2]}` · Generated: {today} · {verdict}
> Per ADR-0010 (1-page SHIP.md místo 8-file compliance theater).

{triage_top}
## Co se mění

{p[4]}

## Ownership

| Role | Person |
|------|--------|
| **Decider** | {decider} |
| **Branch owner / merger** | {branch_owner} |
| **Shadow PdM** (mezi-session babysitter) | {shadow_pm} |

{winner_info}

{render_ai_usage_section(slug)}
## Risk profile

- **AI Act tier**: `{p[12]}` · **Data class**: `{p[13]}` · **Profile**: `{throwaway}` · **Risk profil**: `{triage['risk_profile']}`

{triage_section}

## Kill criteria

{kill}

## Measurement plan

- **Primary lagging**: {p[17] or 'TBD — set v Session 2 / handoff'}
- **Leading**: {p[18] or 'TBD'}
- **Guardrail**: {p[19] or 'TBD'}
- **Instrumentation deadline**: ship-date − 2 dny (per role catalog #12)

{pr_command}

## Co dál (T+0 → T+90)

- **Today**: PR otevřený, branch_owner reviews
- **T+1d**: PR merged → deploy preview link sdílen v Slack/Discord + `/pm retro {slug}` (`python3 tool/cli/retro.py measure --slug {slug} --pr-url <PR_URL>`) → `loc_reused_pct` (cíl ≥ 80 %), `days_to_prod` (cíl ≤ 14)
- **Hned po merge**: připomínky T+7/30/60/90 → `python3 tool/cli/retro.py reminders --slug {slug} --format ics --out data/retro/{slug}-reminders.ics`
- **T+7d**: feature flag rollout 10 % users; Decider checks instrumentation
- **T+14d**: rollout 50 % users; first metrics review (hit primary lagging?)
- **T+30d**: full rollout OR rollback dle kill criteria
- **T+7/30/60/90**: readouty přes `/pm retro {slug}` (tabulka `outcomes`, report `data/retro/{slug}-retro.md`)

## Compliance audit trail

- DORA: audit_log v `data/pflanzer.db` audit_log table (7-letá retence)
- Decision atribuce: `data/handoffs/{p[2]}/decision.md` (per-role package)
- AI Act: pokud `tier=high`, generate Annex IV tech doc před production launch
- GDPR: pokud `data_class=L3+`, RoPA update + DPIA (per Legal triage)

---

*Tento SHIP.md je primary handoff artefakt. 8 per-role files
(`data/handoffs/{p[2]}/{{decision,be,fe,qa,platform,data,support,compliance}}.md`)
jsou supplementary pro audit + per-role deep dive — nikdo je nečte u stolu.
Per perspektiva 02 vibe-product C7 (anti-theater).*
"""


def write_ship(slug: str) -> Path:
    SHIP_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = SHIP_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    out = project_dir / "SHIP.md"
    ctx = _fetch_ship_context(slug)
    wt = _winner_worktree(slug, ctx["winner"][0], ctx["extracted"]) if ctx["winner"] else None
    # Docs: handoff_pr flips the worktree trailer hook to Pflanzer-Session: ship.
    session_switched = _switch_worktree_session(wt)
    out.write_text(render_ship_md(slug), encoding="utf-8")

    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if proj:
            audit(
                conn, action="ship.render",
                target_type="project", target_id=int(proj[0]),
                payload={
                    "slug": slug, "path": _display_path(out),
                    "blocked_by": ctx["triage"]["blocked_by"],
                    "worktree": str(wt) if wt else None,
                    "worktree_session_ship": session_switched,
                },
            )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--print", action="store_true",
                   help="Print SHIP.md to stdout (default: write to file)")
    args = p.parse_args()

    if args.print:
        print(render_ship_md(args.slug))
    else:
        path = write_ship(args.slug)
        print(json.dumps({
            "slug": args.slug,
            "ship_path": _display_path(path),
            "next_step": (
                f"Vyhoď {path} týmu na velký TV. Decider nebo branch_owner "
                f"copy-paste `gh pr create` command z konce SHIP.md."
            ),
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
