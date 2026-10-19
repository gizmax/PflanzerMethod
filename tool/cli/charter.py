"""Charter (zadání na 1 stránku) — logika Kickoffu.

Generuje Pflanzer Charter (ADR-0004, v0.5 terminologie) a ukládá projekt
do DB. Jediná doporučená vstupní cesta je `quick_session.bootstrap`
(`/pm start`, `/pm live`); tento modul zůstává kvůli zpětné kompatibilitě
jako CLI (`pflanzer charter --spec spec.json`) a jako knihovna.

Input: dict polí Charteru. Pokud chybí `target_repo_url`, doplní se z
`.pflanzer/project.toml` v cwd (vytvořeno `pflanzer init`).
Output: charter markdown (DATA_ROOT/charters) + řádek v projects + audit log.
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

from tool.cli.db import DATA_ROOT, audit, current_actor, load_project_toml, transaction  # noqa: E402

CHARTER_DIR = DATA_ROOT / "charters"

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

# Kroky cesty nápadu do produkce (ADR-0021) — každý musí mít jméno.
PATH_STEPS: dict[str, str] = {
    "byznys": "Byznys",
    "produkt": "Produkt",
    "design": "Design",
    "vyvoj": "Vývoj",
    "bezpecnost": "Bezpečnost & právo",
    "provoz": "Provoz",
}


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
    throwaway_or_evolve: str  # throwaway | evolve
    reinforcement_t7: str
    reinforcement_t30: str
    reinforcement_t60: str
    reinforcement_t90: str
    reinforcement_budget_pd: float
    backup_decider: str | None = None
    evolve_conditions_met: list[str] = field(default_factory=list)
    # v0.5 (ADR-0021)
    target_repo_url: str | None = None
    path_owners: dict[str, str] | None = None  # krok cesty -> jméno
    core: list[str] | None = None              # jádro (3–4 lidé, max 5 naráz)


def render_charter_md(c: CharterInput) -> str:
    """Render Charter to markdown per ADR-0004 template."""
    today = date.today().isoformat()
    backup_line = f"- Backup Decider: {c.backup_decider}" if c.backup_decider else "- Backup Decider: —"
    evolve_block = ""
    if c.throwaway_or_evolve == "evolve":
        cond = "\n".join(f"  - [x] {it}" for it in c.evolve_conditions_met)
        evolve_block = f"\n### Evolve podmínky splněné (ADR-0005)\n{cond}\n"

    path_block = ""
    if c.path_owners:
        rows = "\n".join(
            f"| {label} | {c.path_owners.get(key) or '**— BEZ JMÉNA —**'} |"
            for key, label in PATH_STEPS.items()
        )
        path_block = f"""
## Kroky cesty a jejich jména (ADR-0021)
Každý krok má právě jedno jméno; jeden člověk smí zastupovat víc kroků.

| Krok cesty | Zástupce |
|------------|----------|
{rows}
"""
    core_block = ""
    if c.core:
        core_block = (
            f"\n## Jádro (celou dobu, max 5 lidí naráz)\n"
            + "\n".join(f"- {n}" for n in c.core) + "\n"
        )
    repo_line = f"\n- **Target repo**: {c.target_repo_url}" if c.target_repo_url else ""

    return f"""{BRAND_LINE}

# Pflanzer Charter — {c.name}

> Slug: `{c.slug}` · Vytvořeno: {today} · Autor: {current_actor()}
> Per ADR-0004 (Business Charter) + ADR-0001 (Decider) + ADR-0021 (malá skupina, celá cesta).

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
{path_block}{core_block}
## Metrika úspěchu
- **Primary lagging metric**: {c.primary_lagging_metric}
- **Leading metric**: {c.leading_metric}
- **Guardrail metric**: {c.guardrail_metric}

## Kill kritéria
{c.kill_criteria}

## Kapacitní commit
- **Profil**: `{c.capacity_profile}` (default v0.5 ≈ 6–8 PD; regulated a
  audit-grade přidávají okna a brány, viz ADR-0021 + ADR-0008)
- **Person-days commit**: **{c.capacity_person_days}**{repo_line}

## Risk profile
- **AI Act risk-tier**: `{c.ai_act_tier}` *(předběžný, přehodnotí se při Rozhodnutí)*
- **Data classification**: `{c.data_class}`
- **Throw-away vs evolve** (ADR-0005): **`{c.throwaway_or_evolve}`**
{evolve_block}
## Reinforcement track (ADR-0004)
- **T+7**: {c.reinforcement_t7}
- **T+30**: {c.reinforcement_t30}
- **T+60**: {c.reinforcement_t60}
- **T+90**: {c.reinforcement_t90}
- **Reinforcement budget commit**: **{c.reinforcement_budget_pd} PD**

## Sign-off
- Decider podpis (datum + jméno): _PENDING — povinné před Buildem_
- Sponsor podpis: _PENDING_
- Checkpoint Bezpečnost & právo (do 48 h po Buildu): _PENDING_
- Checkpoint Provoz (před Ship): _PENDING_
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
                ai_act_tier, data_class, throwaway_or_evolve,
                capacity_profile, capacity_person_days,
                xyz_hypothesis, primary_lagging_metric, leading_metric, guardrail_metric,
                kill_criteria,
                reinforcement_t7, reinforcement_t30, reinforcement_t60, reinforcement_t90,
                reinforcement_budget_pd
            ) VALUES (?, ?, ?, 'charter',
                      ?, ?, ?, ?,
                      ?, ?, ?,
                      ?, ?,
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
                capacity_profile = excluded.capacity_profile,
                capacity_person_days = excluded.capacity_person_days,
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
                c.ai_act_tier, c.data_class, c.throwaway_or_evolve,
                c.capacity_profile, c.capacity_person_days,
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
            "UPDATE projects SET "
            "target_repo_url = COALESCE(?, target_repo_url), "
            "path_owners_json = COALESCE(?, path_owners_json), "
            "core_json = COALESCE(?, core_json) WHERE id = ?",
            (
                c.target_repo_url,
                json.dumps(c.path_owners, ensure_ascii=False) if c.path_owners else None,
                json.dumps(c.core, ensure_ascii=False) if c.core else None,
                project_id,
            ),
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
    if not spec.get("target_repo_url"):
        spec["target_repo_url"] = load_project_toml().get("target_repo_url")
    inp = CharterInput(**spec)
    md = render_charter_md(inp)
    pid = persist_charter(inp, md)
    out_path = CHARTER_DIR / f"{inp.slug}.md"
    return {"project_id": pid, "charter_path": str(out_path), "slug": inp.slug}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--spec", type=Path, required=True,
                        help="JSON se vstupy Charteru (target_repo_url se doplní z .pflanzer/project.toml). "
                             "Doporučená cesta je /pm start (quick_session bootstrap).")
    args = parser.parse_args()
    result = run_from_json(args.spec)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
