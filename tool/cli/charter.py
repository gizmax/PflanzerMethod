"""Slice 1 — Charter wizard logic.

Generates a Pflanzer Business Charter (per ADR-0004 template) and persists
the project record. Called from `.claude/commands/pflanzer-charter.md`.

Input: dict of charter fields collected interactively by Claude Code.
Output: charter markdown file + projects DB row + audit log.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import REPO_ROOT as DB_REPO_ROOT  # noqa: E402
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.tier import TIER_LABELS, WINDOW_DAYS, default_tier, validate_tier  # noqa: E402

CHARTER_DIR = DB_REPO_ROOT / "data" / "charters"

# ADR-0005 v0.4: default output mode is `evolve` (Track P + evolve).
# `throwaway` is an explicit opt-in allowed only for these use cases and
# must carry a `throwaway_rationale`.
OUTPUT_MODES = ("evolve", "throwaway")
THROWAWAY_USE_CASES = (
    "discovery-only pilot (XYZ falsification, no production intent)",
    "audit-grade evidence collection separate from production",
    "regulated certified production (separate verified implementation)",
)


@dataclass
class CharterInput:
    """Charter wizard inputs — must mirror the Claude Code wizard fields."""

    slug: str
    name: str
    xyz_hypothesis: str
    decider_name: str
    decider_mandate_from: str
    cpo_escalation_contact: str
    sponsor_name: str
    primary_lagging_metric: str
    leading_metric: str
    guardrail_metric: str
    kill_criteria: str
    capacity_profile: str  # default | regulated | audit-grade
    capacity_person_days: int
    ai_act_tier: str  # minimal | limited | high | unacceptable
    data_class: str  # L1 | L2 | L3 | L4
    reinforcement_t7: str
    reinforcement_t30: str
    reinforcement_t60: str
    reinforcement_t90: str
    reinforcement_budget_pd: float
    backup_decider: str | None = None
    # ADR-0005 v0.4: default = evolve; throwaway requires a rationale that
    # names one of THROWAWAY_USE_CASES.
    throwaway_or_evolve: str = "evolve"  # evolve | throwaway
    throwaway_rationale: str | None = None
    # Stupeň Quick / Lean / Full (ADR-0021). None = derive from capacity_profile.
    tier: str | None = None
    # Deprecated (v0.2 "6 conditions for evolve" gate). Accepted so older
    # JSON specs still load, but ignored: production deploy is gated by
    # Ship gate quality gates >= 80/100 + sign-off, not by Charter.
    evolve_conditions_met: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tier = validate_tier(
            self.tier or default_tier(self.capacity_profile), self.capacity_profile
        )
        if self.throwaway_or_evolve not in OUTPUT_MODES:
            raise ValueError(
                f"throwaway_or_evolve must be one of {OUTPUT_MODES}, "
                f"got '{self.throwaway_or_evolve}'."
            )
        if self.throwaway_or_evolve == "throwaway" and not (
            self.throwaway_rationale and self.throwaway_rationale.strip()
        ):
            raise ValueError(
                "throwaway_or_evolve='throwaway' requires throwaway_rationale "
                "(ADR-0005 v0.4: default is 'evolve'; throwaway is an explicit "
                "opt-in for one of: " + "; ".join(THROWAWAY_USE_CASES) + ")."
            )


def render_charter_md(c: CharterInput) -> str:
    """Render Charter to markdown per ADR-0004 template."""
    today = date.today().isoformat()
    backup_line = f"- Backup Decider: {c.backup_decider}" if c.backup_decider else "- Backup Decider: —"
    if c.throwaway_or_evolve == "throwaway":
        output_block = (
            f"- **Throw-away rationale** (explicit opt-in, ADR-0005 v0.4): "
            f"{c.throwaway_rationale}\n"
        )
    else:
        output_block = (
            "- Evolve = default (ADR-0005 v0.4): winner varianta jde do produkce; "
            "prod deploy podmíněn Ship gate (quality gates ≥ 80/100) + sign-off.\n"
        )

    return f"""# Pflanzer Charter — {c.name}

> Slug: `{c.slug}` · Vytvořeno: {today} · Autor: {current_actor()}
> Per ADR-0004 (Business Charter) + ADR-0001 (Decider escalation).

## XYZ hypotéza
{c.xyz_hypothesis}

## Decider + eskalační řetězec (ADR-0001)
- Decider: **{c.decider_name}** · mandát od: {c.decider_mandate_from}
- CPO / sponzor (eskalační kontakt): **{c.cpo_escalation_contact}**
- Sponsor: {c.sponsor_name}
{backup_line}
- **Eskalační protokol**: aplikuje se kanonický Decider eskalační protokol
  z `docs/decisions/0001-decider-model.md` (Scenario A/B/C). Charter ho
  neduplikuje, jen odkazuje.

## Success threshold
- **Primary lagging metric**: {c.primary_lagging_metric}
- **Leading metric**: {c.leading_metric}
- **Guardrail metric**: {c.guardrail_metric}

## Kill criteria
{c.kill_criteria}

## Kapacitní commit
- **Profil**: `{c.capacity_profile}` (default ~10 PD / regulated ~14 PD /
  audit-grade ~18–22 PD per ADR-0008 + devil's advocate Útok 1)
- **Person-days commit**: **{c.capacity_person_days}**
- **Stupeň**: **{TIER_LABELS[c.tier]}** · mezi-session okno {WINDOW_DAYS[c.tier]} pracovních dní (ADR-0021)

## Risk profile
- **AI Act risk-tier**: `{c.ai_act_tier}` *(provisional, re-assessed v Session 2 —
  devil's advocate Útok 4)*
- **Data classification**: `{c.data_class}`
- **Throw-away vs evolve** (ADR-0005 v0.4): **`{c.throwaway_or_evolve}`**
{output_block}
## Reinforcement track (ADR-0004 + devil's advocate Útok 11)
- **T+7**: {c.reinforcement_t7}
- **T+30**: {c.reinforcement_t30}
- **T+60**: {c.reinforcement_t60}
- **T+90**: {c.reinforcement_t90}
- **Reinforcement budget commit**: **{c.reinforcement_budget_pd} PD**

## Champion provisioning (ADR-0006)
*(vyplní Slice 2 / Roles wizard. Zatím placeholder.)*
- Režim: TBD (Bootstrap forma 1/2/3 nebo Organic)
- Champion: TBD
- Champion buddy: TBD

## Sign-off
- Decider podpis (datum + jméno): _PENDING — povinné před Session 1_
- Sponsor podpis: _PENDING_
- Security pre-read (48 h): _PENDING_
- Legal pre-read (48 h): _PENDING_
- EM kapacitní sign-off: _PENDING_
"""


def persist_charter(c: CharterInput, charter_md: str) -> int:
    """Write charter file + persist project row. Returns project_id."""
    CHARTER_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CHARTER_DIR / f"{c.slug}.md"
    out_path.write_text(charter_md, encoding="utf-8")

    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects (
                slug, name, charter_md, status,
                decider_name, decider_mandate_from, cpo_escalation_contact, sponsor_name,
                ai_act_tier, data_class, throwaway_or_evolve, throwaway_rationale,
                capacity_profile, capacity_person_days, tier,
                xyz_hypothesis, primary_lagging_metric, leading_metric, guardrail_metric,
                kill_criteria,
                reinforcement_t7, reinforcement_t30, reinforcement_t60, reinforcement_t90,
                reinforcement_budget_pd
            ) VALUES (?, ?, ?, 'charter',
                      ?, ?, ?, ?,
                      ?, ?, ?, ?,
                      ?, ?, ?,
                      ?, ?, ?, ?,
                      ?,
                      ?, ?, ?, ?,
                      ?)
            ON CONFLICT(slug) DO UPDATE SET
                name = excluded.name,
                charter_md = excluded.charter_md,
                status = 'charter',
                decider_name = excluded.decider_name,
                decider_mandate_from = excluded.decider_mandate_from,
                cpo_escalation_contact = excluded.cpo_escalation_contact,
                sponsor_name = excluded.sponsor_name,
                ai_act_tier = excluded.ai_act_tier,
                data_class = excluded.data_class,
                throwaway_or_evolve = excluded.throwaway_or_evolve,
                throwaway_rationale = excluded.throwaway_rationale,
                capacity_profile = excluded.capacity_profile,
                capacity_person_days = excluded.capacity_person_days,
                tier = excluded.tier,
                xyz_hypothesis = excluded.xyz_hypothesis,
                primary_lagging_metric = excluded.primary_lagging_metric,
                leading_metric = excluded.leading_metric,
                guardrail_metric = excluded.guardrail_metric,
                kill_criteria = excluded.kill_criteria,
                reinforcement_t7 = excluded.reinforcement_t7,
                reinforcement_t30 = excluded.reinforcement_t30,
                reinforcement_t60 = excluded.reinforcement_t60,
                reinforcement_t90 = excluded.reinforcement_t90,
                reinforcement_budget_pd = excluded.reinforcement_budget_pd,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                c.slug, c.name, charter_md,
                c.decider_name, c.decider_mandate_from, c.cpo_escalation_contact, c.sponsor_name,
                c.ai_act_tier, c.data_class, c.throwaway_or_evolve, c.throwaway_rationale,
                c.capacity_profile, c.capacity_person_days, c.tier,
                c.xyz_hypothesis, c.primary_lagging_metric, c.leading_metric, c.guardrail_metric,
                c.kill_criteria,
                c.reinforcement_t7, c.reinforcement_t30, c.reinforcement_t60, c.reinforcement_t90,
                c.reinforcement_budget_pd,
            ),
        )
        project_id = (
            cur.lastrowid
            or conn.execute("SELECT id FROM projects WHERE slug = ?", (c.slug,)).fetchone()[0]
        )

        conn.execute(
            """
            INSERT INTO decisions (project_id, type, body_md, atribuce_user, atribuce_ts)
            VALUES (?, 'charter', ?, ?, CURRENT_TIMESTAMP)
            """,
            (project_id, charter_md, current_actor()),
        )

        audit(
            conn,
            action="charter.create",
            target_type="project",
            target_id=project_id,
            payload={"slug": c.slug, "path": str(out_path)},
        )

    return int(project_id)


def run_from_json(path: Path) -> dict[str, Any]:
    """Run charter generation from a JSON spec file (used by slash command)."""
    spec = json.loads(path.read_text(encoding="utf-8"))
    inp = CharterInput(**spec)
    md = render_charter_md(inp)
    pid = persist_charter(inp, md)
    out_path = CHARTER_DIR / f"{inp.slug}.md"
    return {"project_id": pid, "charter_path": str(out_path), "slug": inp.slug}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--spec", type=Path, required=True, help="JSON spec file with charter inputs")
    args = parser.parse_args()
    result = run_from_json(args.spec)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
