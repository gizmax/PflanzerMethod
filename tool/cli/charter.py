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

import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import DATA_ROOT, audit, current_actor, load_project_toml, transaction  # noqa: E402
from tool.cli.tier import TIER_LABELS, default_tier, validate_tier, window_label  # noqa: E402
from tool.cli.ux import CzechArgumentParser, plural  # noqa: E402

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

# ADR-0005 v0.4: default output mode is `evolve` (Track P + evolve).
# `throwaway` is an explicit opt-in allowed only for these use cases and
# must carry a `throwaway_rationale`.
OUTPUT_MODES = ("evolve", "throwaway")
THROWAWAY_USE_CASES = (
    "discovery-only pilot (XYZ falsification, no production intent)",
    "audit-grade evidence collection separate from production",
    "regulated certified production (separate verified implementation)",
)


# --------------------------------------------------------------------------
# AI náhrada chybějícího zástupce kroku (ADR-0023)
# --------------------------------------------------------------------------

# Výchozí AI agent per krok (.claude/agents/<agent>.md).
STEP_AGENTS = {"produkt": "pm-expert", "design": "ux-expert",
               "bezpecnost": "security-expert", "provoz": "devops-platform-expert"}
# Kroky, které AI nikdy nezastoupí, a proč.
AI_FORBIDDEN = {
    "byznys": "Byznys (Decider) nemůže zastoupit AI — bez člověka s mandátem říct Go/Kill "
              "se Kickoff nesvolává. Napiš jméno Decidera.",
    "vyvoj": "Vývoj nemůže zastoupit AI — u klávesnice sedí vývojář (Track P). "
             "Napiš jméno vývojáře.",
}


def is_ai_owner(value: str | None) -> bool:
    """True for `AI` and `AI:<agent>` (case-insensitive)."""
    v = (value or "").strip().lower()
    return v == "ai" or v.startswith("ai:")


def ai_agent(value: str | None, step: str) -> str:
    """Agent behind an AI owner value (default per step)."""
    v = (value or "").strip()
    if ":" in v and v.split(":", 1)[1].strip():
        return v.split(":", 1)[1].strip()
    return STEP_AGENTS.get(step, "claude")


def owner_display(value: str | None, step: str = "") -> str:
    """Human display of a path owner: `AI (ux-expert)` for AI stand-ins."""
    if not value:
        return ""
    if is_ai_owner(value):
        return f"AI ({ai_agent(value, step)})"
    return value


def _norm_owner(value: str | None) -> str:
    return "AI" if is_ai_owner(value) else (value or "").strip()


def _security_signers(path_owners: dict[str, str], risk_profile: str) -> str:
    """Kdo smí podepsat bezpečnost za AI (do 48 h): Decider / PdM, u production Decider / DPO."""
    decider, pdm = path_owners.get("byznys"), path_owners.get("produkt")
    d = f"Decider ({decider})" if decider and not is_ai_owner(decider) else "Decider"
    if risk_profile == "production":
        return f"{d} nebo DPO/právník do 48 h"
    p = f"PdM ({pdm})" if pdm and not is_ai_owner(pdm) else "PdM"
    return f"{d} nebo {p} do 48 h"


def validate_ai_stand_ins(path_owners: dict[str, str], *, risk_profile: str,
                          tier: str | None) -> tuple[list[dict[str, str]], list[str]]:
    """Check which steps a stand-in AI may cover (ADR-0023 table).

    Returns (ai_stand_ins, warnings); raises ValueError with a human sentence
    for forbidden steps.
    """
    stand_ins: list[dict[str, str]] = []
    warnings: list[str] = []
    for step, value in path_owners.items():
        if not is_ai_owner(value):
            continue
        if step in AI_FORBIDDEN:
            raise ValueError(AI_FORBIDDEN[step])
        label = PATH_STEPS[step]
        if step == "produkt" and not (tier == "quick" or risk_profile == "throwaway"):
            raise ValueError(
                "Produkt smí zastoupit AI jen ve stupni Quick nebo u throwaway prototypu. "
                "Tady napiš jméno PdM (nebo Decidera, který scope drží sám)."
            )
        agent = ai_agent(value, step)
        signer = {
            "produkt": path_owners.get("byznys", "Decider"),
            "design": (path_owners.get("produkt") if not is_ai_owner(path_owners.get("produkt"))
                       else path_owners.get("byznys")) or "PdM",
            "bezpecnost": ("AI pre-check stačí (throwaway)" if risk_profile == "throwaway"
                           else _security_signers(path_owners, risk_profile)),
            "provoz": ("AI pre-check stačí (throwaway)" if risk_profile == "throwaway"
                       else (path_owners.get("vyvoj") if risk_profile == "pilot"
                             else "člověk z provozu")),
        }[step]
        stand_ins.append({"step": step, "label": label, "agent": agent, "signer": str(signer)})
        if step == "design" and risk_profile == "production":
            warnings.append(
                "Design zastupuje AI u production projektu — pokud je aplikace pro "
                "zákazníky, potřeba člověk před Ship."
            )
        if step in ("bezpecnost", "provoz") and risk_profile != "throwaway":
            warnings.append(
                f"{label}: AI připraví jen draft; podpis člověka je nutný před Ship "
                f"({'do 48 h' if step == 'bezpecnost' else 'vývojář z jádra stačí u pilotu'})."
            )
    return stand_ins, warnings


# --------------------------------------------------------------------------
# Kolik lidí je naráz v místnosti (ADR-0021: max 5) — počítají se LIDÉ, ne role
# --------------------------------------------------------------------------

MAX_PEOPLE = 5
# Okno -> kroky cesty, jejichž zástupce do okna přichází navíc k jádru.
WINDOW_STEPS: dict[str, tuple[str, ...]] = {
    "Build": (),
    "Rozhodnutí": ("byznys",),
    "Checkpoint Bezpečnost & právo": ("bezpecnost",),
    "Checkpoint Provoz": ("provoz",),
}


def _people(names: list[str | None]) -> dict[str, str]:
    """casefolded key -> display name; AI and blanks are not people."""
    out: dict[str, str] = {}
    for n in names:
        if n and n.strip() and not is_ai_owner(n):
            out.setdefault(n.strip().casefold(), n.strip())
    return out


def people_check(core: list[str] | None, path_owners: dict[str, str] | None) -> list[str]:
    """Warnings for too many humans: core > 5, or one window > 5.

    Without an explicit core the builders (Vývoj, Produkt, Design) form it.
    """
    owners = path_owners or {}
    core_people = _people(list(core or []) or
                          [owners.get("vyvoj"), owners.get("produkt"), owners.get("design")])
    warnings: list[str] = []
    if len(core_people) > MAX_PEOPLE:
        warnings.append(
            f"Jádro má {plural(len(core_people), 'člověka', 'lidi', 'lidí')} "
            f"({', '.join(core_people.values())}) — víc než "
            f"{plural(MAX_PEOPLE, 'člověk', 'lidé', 'lidí')} naráz nefunguje. Nech stálou účast jen 3–4 lidem, ostatní zvi "
            "jen na jejich okno."
        )
    for window, steps in WINDOW_STEPS.items():
        guests = _people([owners.get(s) for s in steps])
        room = {**core_people, **guests}
        if len(room) > MAX_PEOPLE:
            who = ", ".join(v for k, v in guests.items() if k not in core_people) or "hosté"
            warnings.append(
                f"V okně {window} by bylo {plural(len(room), 'člověk', 'lidé', 'lidí')} — víc než "
                f"{plural(MAX_PEOPLE, 'člověk', 'lidé', 'lidí')} naráz. "
                f"Ať na okno přijde jen {who} a nikdo další ze stálé účasti."
            )
    return warnings


@dataclass
class CharterInput:
    """Kickoff inputs — must mirror the `/pm start` fields."""

    slug: str
    name: str
    xyz_hypothesis: str
    decider_name: str
    decider_mandate_from: str
    cpo_escalation_contact: str
    sponsor_name: str
    primary_lagging_metric: str | None
    leading_metric: str | None
    guardrail_metric: str | None
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
    # Ship quality gates >= 80/100 + sign-off, not by Charter.
    evolve_conditions_met: list[str] = field(default_factory=list)
    # v0.5 (ADR-0021)
    target_repo_url: str | None = None
    path_owners: dict[str, str] | None = None  # krok cesty -> jméno
    core: list[str] | None = None              # jádro (3–4 lidé, max 5 naráz)

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
            "prod deploy podmíněn Shipem (quality gates ≥ 80/100) + sign-off.\n"
        )

    path_block = ""
    if c.path_owners:
        rows = "\n".join(
            f"| {label} | {owner_display(c.path_owners.get(key)) or '**— BEZ JMÉNA —**'} |"
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
            "\n## Jádro (celou dobu, max 5 lidí naráz)\n"
            + "\n".join(f"- {n}" for n in c.core) + "\n"
        )
    repo_line = f"\n- **Target repo**: {c.target_repo_url}" if c.target_repo_url else ""
    metrics = [(label, val) for label, val in (
        ("Primary lagging metric", c.primary_lagging_metric),
        ("Leading metric", c.leading_metric),
        ("Guardrail metric", c.guardrail_metric)) if val and str(val).strip()]
    metrics_block = ("\n".join(f"- **{label}**: {val}" for label, val in metrics) + "\n"
                     if metrics else "- _Metrika zatím není stanovená — zafixuje se při Rozhodnutí._\n")

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
{metrics_block}
## Kill kritéria
{c.kill_criteria}

## Kapacitní commit
- **Profil**: `{c.capacity_profile}` (default v0.5 ≈ 6–8 PD; regulated a
  audit-grade přidávají okna a brány, viz ADR-0021 + ADR-0008)
- **Person-days commit**: **{c.capacity_person_days}**{repo_line}
- **Stupeň**: **{TIER_LABELS[c.tier]}** · mezi-session okno {window_label(c.tier)} (pracovní dny, ADR-0017)

## Risk profile
- **AI Act risk-tier**: `{c.ai_act_tier}` *(předběžný, přehodnotí se při Rozhodnutí)*
- **Data classification**: `{c.data_class}`
- **Throw-away vs evolve** (ADR-0005 v0.4): **`{c.throwaway_or_evolve}`**
{output_block}
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
    parser = CzechArgumentParser(prog="pflanzer charter", description=__doc__.split("\n")[0])
    parser.add_argument("--spec", required=True,
                        help="JSON se vstupy Charteru, nebo `-` pro stdin (target_repo_url se doplní "
                             "z .pflanzer/project.toml). Doporučená cesta je /pm start "
                             "(quick_session bootstrap).")
    parser.add_argument("--json", action="store_true", help="Strojový výstup")
    args = parser.parse_args()
    from tool.cli.ux import die, emit, read_spec, tips_for_project
    try:
        spec = read_spec(args.spec)
        if not spec.get("target_repo_url"):
            spec["target_repo_url"] = load_project_toml().get("target_repo_url")
        inp = CharterInput(**spec)
        md = render_charter_md(inp)
        pid = persist_charter(inp, md)
    except TypeError as exc:
        die(f"Spec nesedí na Charter: {exc}. Doporučená cesta je `pflanzer quick_session "
            "bootstrap --spec -` (viz /pm start).")
        return
    except ValueError as exc:
        die(str(exc))
        return
    result = {"project_id": pid, "charter_path": str(CHARTER_DIR / f"{inp.slug}.md"),
              "slug": inp.slug}
    emit(result, title=f"Charter uložen — {inp.name}",
         lines=[f"Zadání je v `{result['charter_path']}`.", f"Decider: {inp.decider_name}"],
         next_step=f"/pm build {inp.slug}", tips=[] if args.json else tips_for_project(inp.slug, "kickoff"), as_json=args.json)


if __name__ == "__main__":
    main()
