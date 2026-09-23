"""Slice 2 — Role selection wizard backend.

Decision tree per `02-role-catalog.md` § Decision tree (15 kroků). Resolves
which roles from the 18-position catalog apply to a given project, and
persists role rows to the database.

The wizard's interactive flow lives in `.claude/commands/pflanzer-roles.md`;
this module handles the deterministic resolution logic + DB persistence.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, transaction  # noqa: E402

CATALOG_PATH = REPO_ROOT / "tool" / "data" / "role_catalog.json"
SUMMARY_DIR = REPO_ROOT / "data" / "charters"


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--spec", type=Path, required=True, help="JSON spec with role wizard answers")
    args = parser.parse_args()
    print(json.dumps(run_from_json(args.spec), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
