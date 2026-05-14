"""`/pflanzer` quick wizard backend — single-entry orchestrator.

Cíl: tým v zasedačce projde celou metodou v jedné session bez 4 separátních
slash commandů. Sofistikovanost (Charter, role catalog, triage gates,
preference matrix, AI-only deflation, audit log) je zachovaná **uvnitř** —
zvenku jsou to 5 otázek + 1-page handoff.

Mapování na existující slices:
- bootstrap()   → wraps charter.persist_charter + roles.persist_roles
                 + sets triage='deferred' for all 4 tracks (in-room session
                 nemá 48h pre-read window).
- builder_prompts() → wraps builder_decision.recommend; vrátí copy-paste
                 prompts pro 2-3 builders (každý s krátkým variant briefem).
- record_voting() → wraps session.persist (variants + role_preferences).
- render_handoff() → 1-page MD: kdo / co / do kdy / kill criteria.

Defaults pro Charter pole, která se v in-room session neptáme (kapacita,
reinforcement track, sponzor jména) jsou založeny na risk_profile selektu
(throwaway / pilot / production). Decider je explicit (sociální akt).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.builder_decision import recommend_for_slug  # noqa: E402
from tool.cli.charter import CharterInput, persist_charter, render_charter_md  # noqa: E402
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.roles import RoleAnswers, resolve_roles, persist_roles  # noqa: E402
from tool.cli.session import persist as persist_session  # noqa: E402

QUICK_DIR = REPO_ROOT / "data" / "quick"

# Risk profile presets — drive Charter defaults for fields a tým v zasedačce
# neumí zformulovat za 60 minut bez Legal/EM in the room. All fields can be
# overridden later via /pflanzer-charter (full wizard) or DB edit.
RISK_PROFILES: dict[str, dict[str, Any]] = {
    "throwaway": {
        "label": "Throwaway prototyp (interní demo, ne produkce)",
        "ai_act_tier": "minimal",
        "data_class": "L2",
        "throwaway_or_evolve": "throwaway",
        "capacity_profile": "default",
        "capacity_person_days": 5,
        "kill_criteria": "demo není přesvědčivý → kill po 1 týdnu",
        "needs_security_triage": False,
        "needs_legal_triage": False,
        "production_readiness_target": 0,  # Throwaway = nejde do prod
    },
    "pilot": {
        "label": "Pilot s 5-20 reálnými uživateli",
        "ai_act_tier": "limited",
        "data_class": "L2",
        "throwaway_or_evolve": "evolve",  # Pilot kód má jít dál
        "capacity_profile": "default",
        "capacity_person_days": 10,
        "kill_criteria": "po 4 týdnech pilotu žádný měřitelný lift v leading metric",
        "needs_security_triage": True,
        "needs_legal_triage": False,
        "production_readiness_target": 70,  # Pilot tolerantnější
    },
    "production": {
        "label": "Production launch (ošetřená data, regulated)",
        "ai_act_tier": "limited",
        "data_class": "L3",
        "throwaway_or_evolve": "evolve",
        "capacity_profile": "regulated",
        "capacity_person_days": 14,
        "kill_criteria": "guardrail metric breach po 2 sprintech post-launch",
        "needs_security_triage": True,
        "needs_legal_triage": True,
        "production_readiness_target": 85,  # Strict
    },
}

# 5-role default mix per `02-role-catalog.md` § Decision tree
# (always-on 1+2+3, plus FE+UX pro UI fíčuru — covers 80 % corporate cases).
DEFAULT_ROOM = [1, 2, 3, 4, 6]


# --------------------------------------------------------------------------
# Bootstrap (Charter + Roles + Triage shortcut)
# --------------------------------------------------------------------------


def slugify(s: str, max_len: int = 40) -> str:
    """Convert hook into URL-safe slug."""
    s = s.lower().strip()
    # Czech diacritics quick map
    table = str.maketrans("áčďéěíňóřšťúůýž", "acdeeinorstuuyz")
    s = s.translate(table)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len] or f"session-{date.today().isoformat()}"


def _set_triage_deferred(project_id: int, profile: dict[str, Any]) -> None:
    """In-room session skips 48h pre-read triage — mark deferred with note.

    Per `04-session-1.md` failure modes: skipping triage entirely =
    Captured-by-tool risk. So we set status='deferred' (not skipped) with
    explicit follow-up TODO. Decider must address before production.
    """
    note = (
        "**Deferred** — in-room session via `/pflanzer` quick wizard. "
        "Re-run via `/pflanzer-triage <slug>` před production launch.\n"
    )
    with transaction() as conn:
        for track in ("discovery", "security", "legal", "platform"):
            # Skip security if profile flags it as required (= must run real triage)
            status = "deferred"
            if track == "security" and profile.get("needs_security_triage"):
                # Still defer — but flag prominently in handoff. Real triage
                # must run before pilot launch (NOT before in-room exploration).
                pass
            conn.execute(
                """
                INSERT INTO triage (project_id, track, status, artefact_md, signed_by, signed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, track) DO NOTHING
                """,
                (project_id, track, status, note, current_actor()),
            )

        # Move project status forward so session.persist accepts it.
        conn.execute(
            "UPDATE projects SET status = 'triage', updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            (project_id,),
        )


def bootstrap(
    *, hook: str, decider_name: str, room_role_idx: list[int],
    risk_profile: str, slug: str | None = None,
    role_owners: dict[int, str] | None = None,
    target_repo_url: str | None = None,
) -> dict[str, Any]:
    """Create project + Charter + roles + deferred triage in one step.

    Args:
        hook: 1-věta problem statement (mapuje na xyz_hypothesis + name).
        decider_name: jméno člověka s mandátem říct Go/Iterate/Kill.
        room_role_idx: catalog_idx 1..18 rolí, které mají hlas v session.
        risk_profile: 'throwaway' | 'pilot' | 'production'.
        slug: explicit slug; default = slugify(hook).
        role_owners: catalog_idx → human name (kdo z týmu tu roli zastává).

    Returns dict s project_id, slug, roles_count, defer_note.
    """
    profile = RISK_PROFILES[risk_profile]
    slug = slug or slugify(hook)

    # 1. Charter — minimal but valid per ADR-0004 schema
    name = hook[:80] if len(hook) <= 80 else hook[:77] + "…"
    xyz = (
        f"Tým má hypotézu, že **{hook}**. Ověříme tuto hypotézu in-room "
        f"vibe-coding session a 1-3 mockupy. Risk profil: {profile['label']}."
    )

    charter = CharterInput(
        slug=slug,
        name=name,
        xyz_hypothesis=xyz,
        decider_name=decider_name,
        decider_mandate_from="in-room session (to-be-formalized post-decision)",
        cpo_escalation_contact=f"{decider_name} (self-attested for quick session)",
        sponsor_name=decider_name,
        primary_lagging_metric="TBD — fix v Session 2 / handoff",
        leading_metric="TBD — fix v Session 2 / handoff",
        guardrail_metric="TBD — fix v Session 2 / handoff",
        kill_criteria=profile["kill_criteria"],
        capacity_profile=profile["capacity_profile"],
        capacity_person_days=profile["capacity_person_days"],
        ai_act_tier=profile["ai_act_tier"],
        data_class=profile["data_class"],
        throwaway_or_evolve=profile["throwaway_or_evolve"],
        reinforcement_t7="tým retro 7 dní po decision",
        reinforcement_t30="metric review (po fixaci v handoff)",
        reinforcement_t60="—",
        reinforcement_t90="—",
        reinforcement_budget_pd=2.0,
    )
    charter_md = render_charter_md(charter)
    project_id = persist_charter(charter, charter_md)

    # 2. Roles — quick mix from explicit user selection (skip decision tree)
    selected = _resolve_quick_roles(room_role_idx, role_owners or {})
    persist_roles(slug, profile["capacity_profile"], selected)

    # 3. Triage — deferred (with follow-up flag)
    _set_triage_deferred(project_id, profile)

    # 4. Production-path fields
    with transaction() as conn:
        conn.execute(
            "UPDATE projects SET target_repo_url = ?, "
            "production_readiness_target = ? "
            "WHERE id = ?",
            (target_repo_url, profile.get("production_readiness_target", 0), project_id),
        )
        audit(
            conn,
            action="quick.bootstrap",
            target_type="project",
            target_id=project_id,
            payload={
                "slug": slug, "decider": decider_name,
                "risk_profile": risk_profile, "roles": room_role_idx,
                "target_repo_url": target_repo_url,
                "production_readiness_target": profile.get("production_readiness_target", 0),
            },
        )

    return {
        "project_id": project_id,
        "slug": slug,
        "name": name,
        "risk_profile": risk_profile,
        "roles_count": len(selected),
        "production_readiness_target": profile.get("production_readiness_target", 0),
        "target_repo_url": target_repo_url,
        "defer_note": (
            "Triage deferred (in-room mode). Před pilotem/production spusť "
            f"`/pflanzer-triage {slug}`."
        ),
    }


def _resolve_quick_roles(
    room_role_idx: list[int],
    owners: dict[int, str],
) -> list[dict[str, Any]]:
    """Bypass decision tree — explicit role selection from in-room user."""
    catalog_path = REPO_ROOT / "tool" / "data" / "role_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    # Always include 1, 2, 3
    needed = set(room_role_idx) | {1, 2, 3}
    selected: list[dict[str, Any]] = []

    for role in catalog["roles"]:
        if role["idx"] not in needed:
            continue
        # Status: trigger=always → mandatory; ostatní → recommended
        status = "mandatory" if role["trigger"] == "always" else "recommended"
        selected.append({
            "catalog_idx": role["idx"],
            "catalog_label": role["label"],
            "status": status,
            "ai_proxy_mode": role["ai_proxy_mode"],
            "human_owner": owners.get(role["idx"], owners.get(str(role["idx"]), "")),
            "expert_agent_path": f".claude/agents/{role['expert_agent']}.md",
            "rationale": (
                "Quick wizard: explicit selection in-room"
                if role["idx"] not in {1, 2, 3} else "Always-on (Pflanzer core)"
            ),
        })
    return selected


# --------------------------------------------------------------------------
# Builder prompts — copy-paste-able pro 2-3 vibe-coding tools
# --------------------------------------------------------------------------


@dataclass
class VariantPrompt:
    name: str           # A / B / C
    builder: str        # v0 / bolt / cursor / …
    builder_url: str    # https://v0.app, https://bolt.new, …
    angle: str          # 1-věta diferenciace ("single-screen wizard", "multi-step")
    prompt_text: str    # copy-paste do builder
    placeholder_url: str  # předgenerovaný placeholder pro session.py


BUILDER_LANDINGS = {
    "claude-code": "lokální terminál — `claude` v git worktree",
    "codex-cli": "lokální terminál — `codex` v git worktree",
    "cursor": "https://cursor.com (lokální app, otevři repo)",
    "v0": "https://v0.app",
    "bolt": "https://bolt.new",
    "lovable": "https://lovable.dev",
    "stitch": "https://stitch.withgoogle.com",
    "figma-make": "https://www.figma.com/make",
    "manual": "n/a — pair-program in repo",
}


VARIANT_ANGLES = [
    ("A", "happy-path minimum", "Postav nejjednodušší možný flow — 1 obrazovka, 1 CTA, žádné optional pole"),
    ("B", "guided multi-step", "Postav guided flow s progress barem, 2-3 kroky, validace per krok"),
    ("C", "smart defaults", "Postav variantu, která hádá inputy z kontextu (recent activity / role) a uživatel jen potvrdí"),
]


def builder_prompts(slug: str, hook: str, n_variants: int = 3) -> dict[str, Any]:
    """Generate 2-3 copy-paste prompts pro vibe-coding tools.

    Strategie:
    - Vyber n_variants top builderů z builder_decision.recommend.
    - Pro každý builder dosaď VARIANT_ANGLES[i] jako diferenciaci.
    - Prompt template = ČJ-friendly brief + role-aware hint.
    """
    if not 1 <= n_variants <= 3:
        raise ValueError("n_variants must be 1..3")

    rec = recommend_for_slug(slug)
    if rec["blocked"]:
        return {"blocked": True, "reason": rec["blocked_reason"], "prompts": []}

    shortlist = rec["shortlist"][:n_variants]
    if len(shortlist) < n_variants:
        # Pad with manual fallback (always allowed unless project blocked)
        shortlist += [{"builder": "manual", "score": 0.0}] * (n_variants - len(shortlist))

    # Load Charter context for richer prompts
    with transaction() as conn:
        proj = conn.execute(
            "SELECT data_class, ai_act_tier, throwaway_or_evolve, name "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()

    constraints = []
    if proj:
        if proj[0] == "L3":
            constraints.append("⚠ NESMÍŠ použít reálná data — jen synthetic / pseudonymized")
        if proj[1] in ("limited", "high"):
            constraints.append("⚠ Pokud používáš AI v UI (chat / generation), přidej watermark + human-in-the-loop")
        if proj[2] == "throwaway":
            constraints.append("Throw-away prototyp — nepřemýšlej o testech / produkčním kódu")
        else:
            constraints.append("Evolve target — drž se design system tokenů, žádné inline styly")
    constraints.append("Žádné credentials v kódu, žádné .env. WCAG 2.2 AA.")

    prompts: list[VariantPrompt] = []
    for i, (item, (name, angle, brief)) in enumerate(zip(shortlist, VARIANT_ANGLES[:n_variants])):
        builder = item["builder"]
        prompt_text = _render_builder_prompt(hook, brief, constraints, builder,
                                             slug=slug, variant=name)
        # Pro CC/Codex placeholder URL = local branch, ne sandbox
        if builder in ("claude-code", "codex-cli"):
            placeholder_url = f"local://feat/{slug}-{name} (npm run dev)"
        else:
            placeholder_url = f"https://sandbox.invalid/{slug}/{name}"
        prompts.append(VariantPrompt(
            name=name, builder=builder,
            builder_url=BUILDER_LANDINGS.get(builder, "n/a"),
            angle=angle, prompt_text=prompt_text,
            placeholder_url=placeholder_url,
        ))

    return {
        "blocked": False,
        "slug": slug,
        "diversity_hint": rec.get("diversity_hint", ""),
        "prompts": [
            {
                "name": p.name, "builder": p.builder, "builder_url": p.builder_url,
                "angle": p.angle, "prompt_text": p.prompt_text,
                "placeholder_url": p.placeholder_url,
            }
            for p in prompts
        ],
    }


def _render_builder_prompt(
    hook: str, brief: str, constraints: list[str], builder: str,
    slug: str | None = None, variant: str | None = None,
) -> str:
    """Render a copy-paste prompt block per builder type."""
    constraint_lines = "\n".join(f"- {c}" for c in constraints)
    slug = slug or "<slug>"
    variant = variant or "X"

    # In-repo CLI builders (Claude Code, Codex CLI) → git worktree protocol
    if builder == "claude-code":
        return f"""**Otevři terminál v git worktree pro variant {variant}** (žádný browser tab):

```bash
# První session 1× per repo:
git worktree add ../proto-{slug}-{variant} -b feat/{slug}-{variant}
cd ../proto-{slug}-{variant}
claude     # spustí Claude Code v této worktree
```

Pak v Claude Code vlož:

```
Cíl týmu: {hook}

Postav v tomto repu: {brief}.

Postup:
1. Read existing src/ structure, tsconfig.json, .eslintrc, design tokens.
2. Postav variant {variant} jako feature branch — žádné new app, ale extension repa.
3. Constraints:
{constraint_lines}
4. Po dokončení: `npm test && npm run lint && npm run build` musí passing.
5. Commit jako `feat({slug}): variant {variant} — <jednověté shrnutí>`.

Output:
- Branch: feat/{slug}-{variant}
- Preview: `npm run dev` na localhost (sdílím přes ngrok / port-forward na velký TV)
- ČJ texty v UI, EN identifikátory v kódu
```
"""

    if builder == "codex-cli":
        return f"""**Otevři terminál v git worktree pro variant {variant}**:

```bash
git worktree add ../proto-{slug}-{variant} -b feat/{slug}-{variant}
cd ../proto-{slug}-{variant}
codex      # spustí OpenAI Codex CLI
```

Pak v Codex CLI vlož:

```
Cíl týmu: {hook}

Postav v tomto repu: {brief}.

Postup:
1. Pochop existující src/ + design system + test setup.
2. Postav variant {variant} jako feature branch.
3. Constraints:
{constraint_lines}
4. Po dokončení: `npm test && npm run lint && npm run build` musí passing.
5. Commit jako `feat({slug}): variant {variant}`.

Output:
- Branch: feat/{slug}-{variant}
- Preview: `npm run dev` na localhost
- ČJ texty v UI, EN identifikátory v kódu
```
"""

    # Hosted SaaS builders (Bolt/v0/Lovable) — original flow
    if builder == "manual":
        intro = "Pair-program v repu (žádný online builder potřeba):"
    elif builder == "cursor":
        intro = (
            f"Otevři **Cursor** ({BUILDER_LANDINGS[builder]}) a v repu vytvoř "
            f"branch `feat/{slug}-{variant}`, pak vlož prompt:"
        )
    else:
        intro = f"Otevři **{builder}** ({BUILDER_LANDINGS[builder]}) a vlož tento prompt:"
    return f"""{intro}

```
Cíl týmu: {hook}

Postav: {brief}.

Constraints:
{constraint_lines}

Output:
- Funkční preview URL (sdílíme na velkém TV)
- 1 obrazovka stačí
- ČJ texty v UI, EN identifikátory v kódu
- Po dokončení: **Push to GitHub** → vlož repo URL do session 3 (production hardening)
```
"""


# --------------------------------------------------------------------------
# Voting — collect dot vote × dimensions × role
# --------------------------------------------------------------------------


def record_voting(
    *, slug: str, facilitator: str, votes: list[dict[str, Any]],
    decider_call: dict[str, Any], real_urls: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Persist voting outputs via session.persist.

    Args:
        slug: project slug.
        facilitator: jméno fyzického facilitátora.
        votes: list[{ "variant": "A", "name": str, "builder": str,
                      "description": str, "role_preferences": [...] }].
        decider_call: { shortlist, rationale, veto_register, parking_lot }.
        real_urls: optional dict[variant_name → real preview URL]; pokud chybí,
                   použije se placeholder z builder_prompts step.
    """
    real_urls = real_urls or {}

    spec_variants = []
    for v in votes:
        url = real_urls.get(
            v["name"],
            v.get("prototype_url") or f"https://sandbox.invalid/{slug}/{v['name']}",
        )
        spec_variants.append({
            "name": v["name"],
            "builder": v["builder"],
            "prototype_url": url,
            "description_md": v.get("description", ""),
            "role_preferences": v["role_preferences"],
        })

    spec = {
        "slug": slug,
        "facilitator": facilitator,
        "decider_call": decider_call,
        "variants": spec_variants,
    }
    return persist_session(spec)


# --------------------------------------------------------------------------
# Handoff renderer — 1-page MD (kdo / co / do kdy / kill)
# --------------------------------------------------------------------------


def render_handoff(slug: str) -> str:
    """1-page handoff MD: actionable summary post-decision.

    Pulled fields:
    - Project (Charter): name, xyz, decider, kill_criteria, risk profile.
    - Latest Session 1 row: variants + scores + commitment per role.
    - Latest decisions row (type='preference'): shortlist + rationale.
    - Triage deferred → flagni TODO před pilot/production.
    """
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, name, slug, xyz_hypothesis, decider_name, "
            "kill_criteria, throwaway_or_evolve, ai_act_tier, data_class, "
            "capacity_person_days "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        pid = proj[0]

        sess = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1 "
            "ORDER BY id DESC LIMIT 1",
            (pid,),
        ).fetchone()
        variants = []
        if sess:
            variants = list(conn.execute(
                "SELECT name, builder, prototype_url, preference_score, description_md "
                "FROM variants WHERE session_id = ? ORDER BY preference_score DESC",
                (sess[0],),
            ).fetchall())

        decision = conn.execute(
            "SELECT body_md, atribuce_user, atribuce_ts FROM decisions "
            "WHERE project_id = ? AND type = 'preference' "
            "ORDER BY id DESC LIMIT 1",
            (pid,),
        ).fetchone()

        deferred = conn.execute(
            "SELECT track FROM triage WHERE project_id = ? AND status = 'deferred'",
            (pid,),
        ).fetchall()

        # Per-role commitment from role_preferences (best variant)
        commitments = []
        if variants:
            top_variant = conn.execute(
                "SELECT id, name FROM variants WHERE session_id = ? "
                "ORDER BY preference_score DESC LIMIT 1",
                (sess[0],),
            ).fetchone()
            if top_variant:
                commitments = list(conn.execute(
                    """
                    SELECT r.catalog_label, r.human_owner, rp.commitment_level, rp.rationale
                    FROM role_preferences rp
                    JOIN roles r ON r.id = rp.role_id
                    WHERE rp.variant_id = ?
                    ORDER BY rp.commitment_level DESC, r.catalog_idx
                    """,
                    (top_variant[0],),
                ).fetchall())

    # --- Render ---
    var_table = "\n".join(
        f"| {v[0]} | `{v[1]}` | {v[3]:.2f} | [preview]({v[2]}) |"
        for v in variants
    ) or "| — | — | — | — |"

    commit_rows = "\n".join(
        f"| {c[0]} | {c[1] or '—'} | **{c[2] or '—'}** | {c[3]} |"
        for c in commitments
    ) or "| — | — | — | — |"

    deferred_block = ""
    if deferred:
        tracks = ", ".join(t[0] for t in deferred)
        deferred_block = (
            f"\n## ⚠ Pre-production TODO\n\n"
            f"Triage deferred během in-room session pro tracks: **{tracks}**.\n"
            f"Před pilotem/production launch spusť:\n\n"
            f"```bash\n/pflanzer-triage {slug}\n```\n"
        )

    decision_block = "_(Rozhodnutí ještě nezaznamenáno — spusť `/pflanzer` voting krok.)_"
    if decision:
        decision_block = decision[0]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""# Handoff — {proj[1]}

> Slug: `{proj[2]}` · Vygenerováno: {today} · Risk: `{proj[6]}` / `{proj[7]}` / data `{proj[8]}`
> 1-page handoff z `/pflanzer` quick session. Per `04-session-1.md` § Výstupy.

## Co děláme

{proj[3]}

## Decider

**{proj[4]}** rozhodl(a):

{decision_block}

## Varianty (sorted by score)

| Variant | Builder | Score | Preview |
|---------|---------|-------|---------|
{var_table}

## Kdo / co / commitment

| Role | Owner | Commitment 0-3 | Rationale |
|------|-------|----------------|-----------|
{commit_rows}

> Commitment legenda: 0 = neúčastnit se mezi-session · 1 = read-only feedback ·
> 2 = active scoring · 3 = co-creation prototypu.

## Kill criteria

{proj[5]}

## Kapacita

{proj[9]} person-days commit (per Charter risk profile).
{deferred_block}
## Co dál

1. Owner každé role s commitment ≥ 2 začíná pracovat **dnes**.
2. Mezi-session okno: **5-7 pracovních dní** (per `04-session-1.md`).
3. Async feedback do web hubu: `tool/web/` (běží lokálně na :8000).
4. Decision session 2 (Go/Iterate/Kill): `/pflanzer-session-2 {proj[2]}` (Slice 7 — TBD).
5. Před production: re-run triage `/pflanzer-triage {proj[2]}`.

---

*Generated by `/pflanzer` quick wizard. Pro plnou auditovatelnou stopu (Charter
ADR-0004, role catalog, triage tracks): `data/charters/{proj[2]}.md`,
`data/sessions/{proj[2]}/_summary.md`.*
"""


def write_handoff(slug: str) -> Path:
    QUICK_DIR.mkdir(parents=True, exist_ok=True)
    out = QUICK_DIR / f"{slug}-handoff.md"
    out.write_text(render_handoff(slug), encoding="utf-8")
    return out


# --------------------------------------------------------------------------
# CLI dispatcher
# --------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    p_boot = sub.add_parser("bootstrap", help="Create project + Charter + roles + deferred triage")
    p_boot.add_argument("--spec", type=Path, required=True,
                        help="JSON: {hook, decider_name, room_role_idx, risk_profile, slug?, role_owners?}")

    p_prompts = sub.add_parser("prompts", help="Generate 2-3 builder prompts")
    p_prompts.add_argument("--slug", required=True)
    p_prompts.add_argument("--hook", required=True)
    p_prompts.add_argument("--n", type=int, default=3)

    p_vote = sub.add_parser("vote", help="Record voting + Decider's call")
    p_vote.add_argument("--spec", type=Path, required=True)

    p_hand = sub.add_parser("handoff", help="Render 1-page handoff MD")
    p_hand.add_argument("--slug", required=True)

    args = p.parse_args()

    if args.cmd == "bootstrap":
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        out = bootstrap(**spec)
    elif args.cmd == "prompts":
        out = builder_prompts(args.slug, args.hook, args.n)
    elif args.cmd == "vote":
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        out = record_voting(**spec)
    elif args.cmd == "handoff":
        path = write_handoff(args.slug)
        out = {"handoff_path": str(path), "preview": render_handoff(args.slug)[:400] + "…"}
    else:
        p.error(f"unknown cmd: {args.cmd}")

    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
