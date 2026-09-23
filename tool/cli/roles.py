"""Slice 2 — Role selection wizard backend.

Decision tree per `02-role-catalog.md` § Decision tree (15 kroků). Resolves
which roles from the 18-position catalog apply to a given project, and
persists role rows to the database.

The wizard's interactive flow lives in `.claude/commands/pflanzer-roles.md`;
this module handles the deterministic resolution logic + DB persistence.

It also renders one-page role cards (audit N15) from the `card` section of
the catalog: `roles.py cards --all` (static set in docs) or
`roles.py cards --slug S` (per-project cards with names, Decider, tier).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, transaction  # noqa: E402

CATALOG_PATH = REPO_ROOT / "tool" / "data" / "role_catalog.json"
SUMMARY_DIR = REPO_ROOT / "data" / "charters"
CARDS_DIR = REPO_ROOT / "data" / "role-cards"
STATIC_CARDS_DIR = REPO_ROOT / "docs" / "methodology" / "role-cards"

BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"
TIERS = ("quick", "lean", "full")


@dataclass
class RoleAnswers:
    """User answers to decision-tree questions."""

    slug: str
    profile: str  # default | regulated | audit-grade
    ui_changes: bool
    data_or_api: bool
    new_flow: bool
    data_auth_integration: bool
    release_intent: bool
    scope_2plus_sprints: bool
    personal_data_marketing_ai_act: bool
    customer_facing_or_b2b_250: bool
    release_intent_or_metrics: bool
    customer_base_1000: bool
    customer_facing_or_new_segment: bool
    infra_changes: bool
    user_facing_copy: bool
    second_plus_pilot: bool
    multi_team_or_complex_domain: bool
    # Opt-out flags (require justification)
    a11y_optout: bool = False
    a11y_optout_reason: str = ""
    user_research_optout: bool = False
    user_research_optout_reason: str = ""
    # Owner mapping (catalog_idx -> human name); facilitator may be co-facilitator
    owners: dict[int, str] | None = None


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def resolve_roles(answers: RoleAnswers) -> list[dict[str, Any]]:
    """Apply decision tree → list of selected roles with status."""
    catalog = load_catalog()
    selected: list[dict[str, Any]] = []

    triggers = {
        "ui_changes": answers.ui_changes,
        "data_or_api": answers.data_or_api,
        "new_flow": answers.new_flow,
        "data_auth_integration": answers.data_auth_integration,
        "release_intent": answers.release_intent,
        "scope_2plus_sprints": answers.scope_2plus_sprints,
        "personal_data_marketing_ai_act": answers.personal_data_marketing_ai_act,
        "customer_facing_or_b2b_250": answers.customer_facing_or_b2b_250,
        "release_intent_or_metrics": answers.release_intent_or_metrics,
        "customer_base_1000": answers.customer_base_1000,
        "customer_facing_or_new_segment": answers.customer_facing_or_new_segment,
        "infra_changes": answers.infra_changes,
        "user_facing_copy": answers.user_facing_copy,
        "second_plus_pilot": answers.second_plus_pilot,
        "multi_team_or_complex_domain": answers.multi_team_or_complex_domain,
    }

    for role in catalog["roles"]:
        idx = role["idx"]
        trigger = role["trigger"]
        is_default_on = role.get("default_on", False)

        # Always-on: roles 1, 2, 3
        if trigger == "always":
            status = "mandatory"
            include = True
        # Mandatory-when-triggered: 7, 8
        elif role.get("mandatory_if_triggered"):
            include = bool(triggers.get(trigger, False))
            status = "mandatory" if include else "excluded"
        # Default-on: 11, 14
        elif is_default_on:
            triggered = bool(triggers.get(trigger, False))
            optout = (
                (idx == 11 and answers.a11y_optout)
                or (idx == 14 and answers.user_research_optout)
            )
            include = triggered and not optout
            status = "recommended" if include else "excluded"
        # Other recommended: 4, 5, 6, 9, 10, 12, 13, 15
        elif role["default_status"] == "recommended":
            include = bool(triggers.get(trigger, False))
            status = "recommended" if include else "excluded"
        # Optional: 16, 17, 18
        else:
            include = bool(triggers.get(trigger, False))
            status = "optional" if include else "excluded"

        if include:
            owners = answers.owners or {}
            owner = owners.get(idx, owners.get(str(idx), ""))
            selected.append(
                {
                    "catalog_idx": idx,
                    "catalog_label": role["label"],
                    "status": status,
                    "ai_proxy_mode": role["ai_proxy_mode"],
                    "human_owner": owner,
                    "expert_agent_path": f".claude/agents/{role['expert_agent']}.md",
                    "rationale": _rationale(role, triggers, answers),
                }
            )

    return selected


def _rationale(role: dict[str, Any], triggers: dict[str, bool], answers: RoleAnswers) -> str:
    if role["trigger"] == "always":
        return "Always-on (povinná v každém Pflanzer cyklu)."
    if role.get("mandatory_if_triggered") and triggers.get(role["trigger"]):
        return f"Mandatory triggered: {role.get('trigger_question', role['trigger'])}"
    if role.get("default_on"):
        return "Default-on profile (opt-out vyžaduje justifikaci)."
    return f"Triggered by: {role.get('trigger_question', role['trigger'])}"


def sanity_check(selected: list[dict[str, Any]], profile: str) -> list[str]:
    """Return list of warnings."""
    warnings: list[str] = []
    if len(selected) > 10:
        warnings.append(
            f"⚠ {len(selected)} rolí v místnosti — přesahuje sanity check 10. "
            "Návrh: zúžit scope nebo federovaný model (per docs/methodology/"
            "08-edge-cases-a-rizika.md edge case 7)."
        )
    if profile == "audit-grade":
        warnings.append(
            "⚠ Audit-grade profil — co-facilitator SHOULD (devil's advocate "
            "Útok 10). Single facilitator závislý na sponzoringu = paper authority."
        )
    return warnings


def render_summary_md(slug: str, project_id: int, profile: str, selected: list[dict[str, Any]], warnings: list[str]) -> str:
    rows = "\n".join(
        f"| #{r['catalog_idx']} | {r['catalog_label']} | {r['status']} | "
        f"{r['ai_proxy_mode']} | {r['human_owner'] or '—'} | {r['rationale']} |"
        for r in selected
    )
    warn_block = (
        "\n## Sanity warnings\n\n" + "\n".join(f"- {w}" for w in warnings) + "\n"
        if warnings else ""
    )
    return f"""# Role selection — {slug}

> Project ID: {project_id} · Profil: `{profile}` · Rolí v místnosti: **{len(selected)}**
> Per `docs/methodology/02-role-catalog.md` v0.2 + `synthesis/03-role-catalog-updates.md`.

| # | Role | Status | AI proxy mode | Human owner | Rationale |
|---|------|--------|---------------|-------------|-----------|
{rows}
{warn_block}
## Next step

`/pflanzer-triage {slug}` — pre-flight Discovery + Security/Legal/Platform triage.
"""


def persist_roles(slug: str, profile: str, selected: list[dict[str, Any]]) -> dict[str, Any]:
    """Insert selected roles for a project; replaces existing rows."""
    with transaction() as conn:
        row = conn.execute("SELECT id, status FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not row:
            raise ValueError(f"Project '{slug}' not found. Run /pflanzer-charter first.")
        project_id = int(row[0])

        conn.execute("DELETE FROM roles WHERE project_id = ?", (project_id,))

        for r in selected:
            conn.execute(
                """
                INSERT INTO roles (project_id, catalog_idx, catalog_label, status,
                                   ai_proxy_mode, human_owner, expert_agent_path, rationale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id, r["catalog_idx"], r["catalog_label"], r["status"],
                    r["ai_proxy_mode"], r["human_owner"] or None,
                    r["expert_agent_path"], r["rationale"],
                ),
            )

        conn.execute(
            "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,),
        )
        audit(
            conn,
            action="roles.select",
            target_type="project",
            target_id=project_id,
            payload={"profile": profile, "count": len(selected)},
        )

    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = SUMMARY_DIR / f"{slug}-roles.md"
    warnings = sanity_check(selected, profile)
    summary_path.write_text(
        render_summary_md(slug, project_id, profile, selected, warnings),
        encoding="utf-8",
    )

    return {
        "project_id": project_id,
        "slug": slug,
        "roles_count": len(selected),
        "summary_path": str(summary_path),
        "warnings": warnings,
    }


def run_from_json(path: Path) -> dict[str, Any]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    answers = RoleAnswers(**spec)
    selected = resolve_roles(answers)
    return persist_roles(answers.slug, answers.profile, selected)


# --------------------------------------------------------------------------
# Role cards (audit N15) — one page per role, rendered from catalog `card`
# --------------------------------------------------------------------------

CARD_FIELDS = ("why", "bring", "sign_off", "when_in_room", "vote_on", "red_flags", "ai_proxy")

CATALOG_DOC = "docs/methodology/02-role-catalog.md"
TIERS_DOC = "docs/methodology/00-lean-pflanzer.md"

STATUS_LABELS = {
    "mandatory": "povinná",
    "mandatory_when_triggered": "povinná při triggeru",
    "recommended": "doporučená",
    "recommended_default_on": "doporučená (default-on)",
    "optional": "volitelná (trigger)",
    "excluded": "vyřazená",
}
TIER_LABELS = {"quick": "Quick (60–90 min)", "lean": "Lean (3 h)", "full": "Full (5–6 h)"}
TIER_SOURCES = {"arg": "zadáno přes `--tier`", "db": "odvozeno z DB, přepiš přes `--tier`"}


@dataclass
class CardProject:
    """Project context injected into per-project role cards."""

    slug: str
    name: str
    decider: str | None
    tier: str | None
    tier_source: str | None  # "arg" | "db" | None
    session_1: str | None
    session_2: str | None
    assignments: dict[int, dict[str, Any]]  # catalog_idx -> {status, human_owner}


def role_slug(label: str) -> str:
    """ASCII slug of a catalog label ("Produkt manažer" -> "produkt-manazer")."""
    text = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def card_filename(role: dict[str, Any]) -> str:
    return f"{int(role['idx']):02d}-{role_slug(role['label'])}.md"


def missing_card_fields(role: dict[str, Any]) -> list[str]:
    """Card fields that are absent or empty for a catalog role."""
    card = role.get("card") or {}
    missing = [f for f in CARD_FIELDS if not card.get(f)]
    when = card.get("when_in_room") or {}
    missing += [f"when_in_room.{t}" for t in TIERS
                if not (when.get(t) or {}).get("presence") or not (when.get(t) or {}).get("note")]
    if not (card.get("vote_on") or {}).get("note"):
        missing.append("vote_on.note")
    return missing


def _infer_tier(conn: Any, project_id: int, capacity_profile: str | None) -> str | None:
    """Best-effort tier from DB (the tier itself is not a DB column).

    audit-grade capacity profile -> Full; project bootstrapped by the in-room
    `/pm live` wizard with the default profile -> Quick; any other known
    profile -> Lean (the Track P default).
    """
    if capacity_profile == "audit-grade":
        return "full"
    quick = conn.execute(
        "SELECT 1 FROM audit_log WHERE action = 'quick.bootstrap' "
        "AND target_type = 'project' AND target_id = ? LIMIT 1",
        (project_id,),
    ).fetchone()
    if quick and capacity_profile in (None, "default"):
        return "quick"
    if capacity_profile in ("default", "regulated"):
        return "lean"
    return None


def load_card_project(slug: str, tier: str | None = None) -> CardProject:
    with transaction() as conn:
        row = conn.execute(
            "SELECT id, name, decider_name, capacity_profile FROM projects WHERE slug = ?",
            (slug,),
        ).fetchone()
        if not row:
            raise ValueError(f"Project '{slug}' not found. Run /pflanzer-charter first.")
        project_id = int(row["id"])
        roles = conn.execute(
            "SELECT catalog_idx, status, human_owner FROM roles "
            "WHERE project_id = ? AND status != 'excluded' ORDER BY catalog_idx",
            (project_id,),
        ).fetchall()
        sessions = {
            int(r[0]): r[1] for r in conn.execute(
                "SELECT type, MIN(starts_at) FROM sessions WHERE project_id = ? "
                "AND type IN (1, 2) GROUP BY type",
                (project_id,),
            ).fetchall()
        }
        inferred = _infer_tier(conn, project_id, row["capacity_profile"])
    if not roles:
        raise ValueError(f"Project '{slug}' has no selected roles. Run /pflanzer-roles first.")
    tier_source = "arg" if tier else ("db" if inferred else None)
    return CardProject(
        slug=slug,
        name=row["name"],
        decider=row["decider_name"],
        tier=tier or inferred,
        tier_source=tier_source,
        session_1=(sessions.get(1) or "")[:10] or None,
        session_2=(sessions.get(2) or "")[:10] or None,
        assignments={
            int(r["catalog_idx"]): {"status": r["status"], "human_owner": r["human_owner"]}
            for r in roles
        },
    )


def render_card(
    role: dict[str, Any],
    catalog: dict[str, Any],
    *,
    tier: str | None = None,
    project: CardProject | None = None,
) -> str:
    """Render one role card (Czech, <= 1 page)."""
    card = role["card"]
    presence = catalog.get("card_presence", {})
    mode = catalog["ai_proxy_modes"][role["ai_proxy_mode"]]
    mode_no = role["ai_proxy_mode"].split("_")[-1]
    tier = project.tier if project else tier

    lines = [
        BRAND_LINE, "",
        f"# Role card #{role['idx']} — {role['label']}", "",
        f"> {card['why']}", "",
        f"Status v catalogu: **{STATUS_LABELS.get(role['default_status'], role['default_status'])}**"
        f" · Kdy se zve: {role.get('trigger_question', 'vždy (core role)')}",
        "",
    ]
    if project:
        mine = project.assignments.get(int(role["idx"]), {})
        sessions = (f"**Session 1:** {project.session_1 or 'termín v DB chybí'} · "
                    f"**Session 2:** {project.session_2 or 'termín v DB chybí'}")
        lines += [
            "## Tvůj projekt", "",
            f"- **Projekt:** {project.name} (`{project.slug}`) · "
            f"**Decider:** {project.decider or '—'}",
            f"- **Ty:** {mine.get('human_owner') or '— doplň jméno před Session 1'} · "
            f"status role: {STATUS_LABELS.get(mine.get('status', ''), mine.get('status', '—'))}",
            f"- {sessions}",
            "",
        ]

    lines += ["## Přines do Session 1", ""]
    lines += [f"- {item}" for item in card["bring"]]
    lines += ["", "## Podepisuješ", ""]
    lines += [f"- {item}" for item in card["sign_off"]]

    heading = "## Kdy jsi v místnosti"
    if tier:
        source = TIER_SOURCES.get(project.tier_source or "", "") if project else TIER_SOURCES["arg"]
        heading += f" (stupeň: **{TIER_LABELS[tier].split(' ')[0]}**, {source})"
    elif project:
        heading += " (stupeň projektu neznámý — doplň `--tier`)"
    lines += ["", heading, ""]
    for t in TIERS:
        slot = card["when_in_room"][t]
        text = (f"{TIER_LABELS[t]} — {presence.get(slot['presence'], slot['presence'])}: "
                f"{slot['note']}")
        lines.append(f"- **{text}** ← tvůj stupeň" if t == tier else f"- {text}")

    vote = card["vote_on"]
    lines += ["", "## Hlasuješ o", "", vote["note"]]
    if vote.get("dimensions"):
        dims = " · ".join(f"`{d}`" for d in vote["dimensions"])
        focus = ", ".join(f"**{f}**" for f in vote.get("focus", []))
        lines += ["", f"Preference matrix: {dims}" + (f"; tvoje váha: {focus}" if focus else "")
                  + ". K tomu commitment level 0–3 pro mezi-session práci."]

    lines += ["", "## Okamžitě hlas", ""]
    lines += [f"- {item}" for item in card["red_flags"]]
    lines += [
        "", "## AI proxy", "",
        f"**Režim {mode_no} — {mode['label']}.** {card['ai_proxy']} "
        f"Sub-agent: `.claude/agents/{role['expert_agent']}.md`.",
        "", "---", "",
        f"Detail: `{CATALOG_DOC}` § {role['idx']} · stupně: "
        f"`{TIERS_DOC}` § Tři stupně jedné metody",
    ]
    return "\n".join(lines) + "\n"


def render_cards_index(
    roles: list[dict[str, Any]], catalog: dict[str, Any], project: CardProject | None = None,
) -> str:
    """README.md index: role -> card."""
    modes = catalog["ai_proxy_modes"]
    if project:
        rows = "\n".join(
            f"| {r['idx']} | {r['label']} | "
            f"{project.assignments[int(r['idx'])].get('human_owner') or '— doplnit'} | "
            f"{STATUS_LABELS.get(project.assignments[int(r['idx'])]['status'], '—')} | "
            f"[{card_filename(r)}]({card_filename(r)}) |"
            for r in roles
        )
        tier = TIER_LABELS[project.tier] if project.tier else "neznámý (`--tier`)"
        return f"""{BRAND_LINE}

# Role cards — {project.name}

> Projekt `{project.slug}` · Decider: {project.decider or '—'} · stupeň: {tier}
> Vygenerováno: `python3 tool/cli/roles.py cards --slug {project.slug}`.

Každý člověk dostane **jen svou kartu** (1 strana) nejpozději s pozvánkou
na Session 1. Metodiku číst nemusí — karta říká, co přinést, co podepisuje,
kdy je v místnosti a na co hlasuje.

| # | Role | Člověk | Status | Karta |
|---|------|--------|--------|-------|
{rows}
"""
    rows = "\n".join(
        f"| {r['idx']} | {r['label']} | "
        f"{STATUS_LABELS.get(r['default_status'], r['default_status'])} | "
        f"Režim {r['ai_proxy_mode'].split('_')[-1]} ({modes[r['ai_proxy_mode']]['label']}) | "
        f"[{card_filename(r)}]({card_filename(r)}) |"
        for r in roles
    )
    return f"""{BRAND_LINE}

# Role cards — jedna strana na roli

> Generováno z `tool/data/role_catalog.json` (sekce `card`) příkazem
> `python3 tool/cli/roles.py cards --all`. **Needitovat ručně** — test
> `tests/test_role_cards.py` hlídá, že karty odpovídají generátoru.

Sponzor, Security ani UX nemusí číst celou metodiku: každá karta na jedné
straně říká, co do Session 1 přinést, co role podepisuje, kdy je v místnosti
(Quick / Lean / Full), na co hlasuje a co má okamžitě nahlásit. Detail role
je v `{CATALOG_DOC}`.

Pro konkrétní projekt vygeneruj karty se jmény, Deciderem, termíny a stupněm:
`python3 tool/cli/roles.py cards --slug <slug>` → `data/role-cards/<slug>/`.

| # | Role | Status v catalogu | AI proxy | Karta |
|---|------|-------------------|----------|-------|
{rows}
"""


def generate_cards(
    *, slug: str | None = None, out: Path | None = None, tier: str | None = None,
) -> dict[str, Any]:
    """Write role cards + README index. `slug=None` = all 18 catalog roles."""
    if tier is not None and tier not in TIERS:
        raise ValueError(f"Unknown tier '{tier}' (expected one of {', '.join(TIERS)}).")
    catalog = load_catalog()
    project = load_card_project(slug, tier) if slug else None
    roles = [r for r in catalog["roles"]
             if project is None or int(r["idx"]) in project.assignments]
    broken = {r["idx"]: missing_card_fields(r) for r in roles if missing_card_fields(r)}
    if broken:
        raise ValueError(f"role_catalog.json: incomplete `card` sections: {broken}")

    out_dir = Path(out) if out else (CARDS_DIR / slug if slug else STATIC_CARDS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Drop cards of roles no longer selected (exact catalog file names only).
    keep = {card_filename(r) for r in roles}
    for r in catalog["roles"]:
        stale = out_dir / card_filename(r)
        if card_filename(r) not in keep and stale.is_file():
            stale.unlink()

    written = []
    for r in roles:
        path = out_dir / card_filename(r)
        path.write_text(render_card(r, catalog, tier=tier, project=project), encoding="utf-8")
        written.append(str(path))
    index = out_dir / "README.md"
    index.write_text(render_cards_index(roles, catalog, project), encoding="utf-8")
    return {
        "slug": slug,
        "out_dir": str(out_dir),
        "tier": project.tier if project else tier,
        "cards_count": len(written),
        "cards": written,
        "index_path": str(index),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--spec", type=Path, help="JSON spec with role wizard answers")
    sub = parser.add_subparsers(dest="command")
    cards = sub.add_parser("cards", help="Render one-page role cards (audit N15)")
    target = cards.add_mutually_exclusive_group(required=True)
    target.add_argument("--slug", help="Project slug — cards for the roles selected in DB")
    target.add_argument("--all", action="store_true",
                        help=f"All catalog roles (default out: {STATIC_CARDS_DIR.relative_to(REPO_ROOT)})")
    cards.add_argument("--out", type=Path, help="Output directory")
    cards.add_argument("--tier", choices=TIERS, help="Highlight Quick / Lean / Full presence")
    args = parser.parse_args(argv)

    if args.command == "cards":
        try:
            result = generate_cards(slug=args.slug, out=args.out, tier=args.tier)
        except ValueError as exc:
            print(f"{BRAND_LINE}\n\n✖ {exc}", file=sys.stderr)
            sys.exit(2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.spec is None:
        parser.error("--spec is required (or use the `cards` subcommand)")
    print(json.dumps(run_from_json(args.spec), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
