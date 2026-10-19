"""Kickoff + Build backend — jediná vstupní cesta (`/pm start`, `/pm live`).

v0.5 (ADR-0021): malé jádro (3–4 lidé, max 5 naráz) + zástupci všech 6 kroků
cesty (byznys, produkt, design, vývoj, bezpečnost & právo, provoz). Sofistikovanost
(Charter, role catalog, triage brány, preference matrix, audit log) je uvnitř —
zvenku je to zadání na 1 stránku + jména + 3 varianty.

- bootstrap()       → JEDINÝ způsob založení projektu: Charter + role + jména
                      kroků cesty + jádro + odložený triage.
- builder_prompts() → copy-paste prompty pro 3 buildery (3 worktrees A/B/C).
- record_voting()   → session.persist (varianty + role_preferences).
- render_handoff()  → 1-page MD: kdo / co / do kdy / kill kritéria.

Defaults pro pole Charteru, na která se při Kickoffu neptáme, jsou dané
risk_profile (throwaway / pilot / production).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.builder_decision import recommend_for_slug  # noqa: E402
from tool.cli.charter import (  # noqa: E402
    BRAND_LINE,
    PATH_STEPS,
    THROWAWAY_USE_CASES,
    CharterInput,
    persist_charter,
    render_charter_md,
)
from tool.cli.db import (  # noqa: E402
    DATA_ROOT,
    audit,
    current_actor,
    display_path,
    load_project_toml,
    transaction,
)
from tool.cli.roles import persist_roles  # noqa: E402
from tool.cli.session import persist as persist_session  # noqa: E402
from tool.cli.tier import default_tier  # noqa: E402
from tool.cli.worktree import (  # noqa: E402
    TargetRepo,
    load_target_repos,
    normalize_target_repos,
    pick_primary,
    validate_repo_url,
    variant_worktrees,
)

QUICK_DIR = DATA_ROOT / "quick"
MAX_PEOPLE = 5  # ADR-0021: nikdy víc než 5 lidí naráz

# Krok cesty -> catalog_idx role, která ho typicky zastupuje (02-role-catalog.md)
PATH_STEP_ROLE = {"byznys": 1, "produkt": 2, "design": 6, "vyvoj": 4, "bezpecnost": 7, "provoz": 15}

# Risk profile presets — drive Charter defaults for fields a tým v zasedačce
# neumí zformulovat za 60 minut bez Legal/EM in the room. All fields can be
# overridden later via spec (metric, kill_criteria, ...) or DB edit.
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
        "capacity_person_days": 8,  # v0.5 default ≈ 6–8 PD
        "kill_criteria": "po 4 týdnech pilotu žádný měřitelný lift v leading metric",
        "needs_security_triage": True,
        "needs_legal_triage": False,
        "production_readiness_target": 80,  # dokumentace: Ship brány ≥ 80/100
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
    """Kickoff nemá 48h pre-read — triage se označí jako deferred.

    Úplné vynechání triage = Captured-by-tool risk, proto status='deferred'
    (ne skipped) s TODO: Checkpoint Bezpečnost & právo (20 min) do 48 h po
    Buildu, před Ship.
    """
    note = (
        "**Deferred** — Kickoff přes `/pm start`. Checkpoint Bezpečnost & právo "
        "(20 min) proběhne do 48 h po Buildu, před Ship.\n"
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


def _strip_diacritics(text: str) -> str:
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def _normalize_path_owners(raw: dict[str, str] | None) -> dict[str, str] | None:
    """Validate the 6 steps of the path; every step needs a name (ADR-0021).

    Accepts keys with/without diacritics ("bezpečnost", "vývoj"). Returns
    canonical dict in step order, or None when `raw` was not provided.
    """
    if raw is None:
        return None
    aliases = {"bezpecnost_a_pravo": "bezpecnost", "bezpecnost&pravo": "bezpecnost",
               "bezpecnost_pravo": "bezpecnost"}
    given: dict[str, str] = {}
    for k, v in raw.items():
        key = _strip_diacritics(str(k)).lower().strip().replace(" ", "_")
        key = aliases.get(key, key)
        given[key] = v.strip() if isinstance(v, str) else ""
    unknown = [k for k in given if k not in PATH_STEPS]
    if unknown:
        raise ValueError(
            f"Neznámý krok cesty: {', '.join(unknown)}. Platné: {', '.join(PATH_STEPS)}."
        )
    for step in PATH_STEPS:
        if not given.get(step):
            raise ValueError(
                f"Krok cesty '{step}' nemá jméno — Kickoff nesvolávat (ADR-0021)"
            )
    return {step: given[step] for step in PATH_STEPS}


def _unique_people(names: list[str]) -> set[str]:
    return {n.strip().casefold() for n in names if n and n.strip()}


def _write_acceptance_feature(
    slug: str, hook: str, metric: str | None, criteria_md: str | None,
) -> str | None:
    """Write tests/acceptance/<slug>.feature into the target repo (cwd with .pflanzer/).

    Only when metric or acceptance criteria were given. Never overwrites.
    """
    cwd = Path.cwd()
    if not (metric or criteria_md) or not (cwd / ".pflanzer").is_dir():
        return None
    out = cwd / "tests" / "acceptance" / f"{slug}.feature"
    if out.exists():
        return str(out)
    lines = [
        "# language: cs",
        "# Pflanzer Method | pflanzer.cz/method",
        "# Vygenerováno při Kickoffu — doplň konkrétní kroky; Builder se jimi řídí.",
        f"Požadavek: {hook}",
        "",
    ]
    if criteria_md and re.search(r"(?mi)^\s*(Sc[eé]n[aá]ř|Scenario)", criteria_md):
        lines.append(criteria_md.strip())
    else:
        crits = [c.strip(" -*\t") for c in (criteria_md or "").splitlines() if c.strip()]
        for i, crit in enumerate(crits, 1):
            lines += [f"  Scénář: Kritérium {i}", f"    Pak {crit}", ""]
        if metric:
            lines += [
                "  Scénář: Metrika úspěchu",
                "    Pokud je varianta nasazená pro cílové uživatele",
                f"    Pak se měří: {metric}",
                "",
            ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return str(out)


def bootstrap(
    *, hook: str, decider_name: str, room_role_idx: list[int],
    risk_profile: str, slug: str | None = None,
    role_owners: dict[int, str] | None = None,
    target_repo_url: str | None = None,
    acceptance_criteria_md: str | None = None,
    target_branch_owner: str | None = None,
    shadow_pm: str | None = None,
    metric: str | None = None,
    kill_criteria: str | None = None,
    path_owners: dict[str, str] | None = None,
    core: list[str] | None = None,
    target_repos: list[dict[str, Any]] | str | None = None,
    target_branch: str | None = None,
    throwaway_rationale: str | None = None,
    tier: str | None = None,
) -> dict[str, Any]:
    """Založí projekt: Charter + role + jména kroků cesty + odložený triage.

    JEDINÁ vstupní cesta (Kickoff i /pm live).

    Args:
        hook: 1-věta problem statement (xyz_hypothesis + name).
        decider_name: člověk s mandátem říct Go/Iterate/Kill.
        room_role_idx: catalog_idx 1..18 rolí v jádru/okně.
        risk_profile: 'throwaway' | 'pilot' | 'production'.
        slug: explicit slug; default = slugify(hook).
        role_owners: catalog_idx → jméno (kdo z týmu tu roli zastává).
        metric: metrika úspěchu (→ primary_lagging_metric + acceptance .feature).
        kill_criteria: přepíše default z risk profilu.
        path_owners: {"byznys","produkt","design","vyvoj","bezpecnost","provoz"} → jména.
            Pokud zadáno a některý krok chybí → ValueError (ADR-0021).
        core: jména jádra (3–4 lidé; > 5 unikátních = warning).
        target_repos: volitelně více repozitářů (audit N8) — list
            `[{"role": "fe", "url": ..., "branch": "main", "workspace": "apps/web"}]`
            nebo wizard text `fe=<url>[#branch][:workspace], be=<url>`.
            Primární repo (FE / app) se zapíše i do `target_repo_url`.
        target_branch: base branch pro jednorepo případ (default 'main').
        throwaway_rationale: jen pro risk_profile='throwaway' (ADR-0005 v0.4);
            default = use case „discovery-only pilot“ (interní demo).
        tier: 'quick' | 'lean' | 'full' (ADR-0017). Default: Quick (`/pm live`),
            jen risk_profile='production' dostane Lean (tabulka stupňů).

    Returns dict: project_id, slug, roles_count, warnings, ...
    """
    profile = RISK_PROFILES[risk_profile]
    slug = slug or slugify(hook)
    owners_by_step = _normalize_path_owners(path_owners)  # fail fast, before any write

    defaults = load_project_toml()
    target_repo_url = target_repo_url or defaults.get("target_repo_url")
    target_branch_owner = target_branch_owner or defaults.get("target_branch_owner")
    shadow_pm = shadow_pm or defaults.get("shadow_pm")

    repos, target_repo_url = _resolve_target_repos(
        target_repos=target_repos, target_repo_url=target_repo_url,
        target_branch=target_branch,
    )

    # Mandatory target_repo_url pro pilot/production
    if risk_profile in ("pilot", "production") and not target_repo_url:
        raise ValueError(
            f"target_repo_url je povinný pro risk_profile='{risk_profile}'. "
            "Bez něj Build vyrobí worktree v meta-repu = reuse 0 %. "
            "Spusť `pflanzer init` v target repu (vyplní .pflanzer/project.toml) "
            "nebo zadej target_repo_url='https://github.com/yourorg/yourapp' "
            "či target_repos='fe=https://github.com/org/web, be=https://github.com/org/api'."
        )

    warnings: list[str] = []
    if len(_unique_people(core or [])) > MAX_PEOPLE or len(set(room_role_idx)) > MAX_PEOPLE:
        warnings.append(
            "víc než 5 lidí naráz — zúž scope nebo přesuň zástupce na okna"
        )

    # 1. Charter
    name = hook[:80] if len(hook) <= 80 else hook[:77] + "…"
    xyz = (
        f"Problém k vyřešení: **{hook}**. Ověříme ho při Buildu "
        f"(3 varianty v 3 worktrees). Risk profil: {profile['label']}."
    )
    tbd = "doplň při Rozhodnutí"
    charter = CharterInput(
        slug=slug,
        name=name,
        xyz_hypothesis=xyz,
        decider_name=decider_name,
        decider_mandate_from="Kickoff (formalizuje se po Rozhodnutí)",
        cpo_escalation_contact=f"{decider_name} (self-attested při Kickoffu)",
        sponsor_name=decider_name,
        primary_lagging_metric=metric or tbd,
        leading_metric=tbd,
        guardrail_metric=tbd,
        kill_criteria=kill_criteria or profile["kill_criteria"],
        capacity_profile=profile["capacity_profile"],
        capacity_person_days=profile["capacity_person_days"],
        ai_act_tier=profile["ai_act_tier"],
        data_class=profile["data_class"],
        throwaway_or_evolve=profile["throwaway_or_evolve"],
        # ADR-0005 v0.4: throwaway needs a rationale naming one of the use cases.
        throwaway_rationale=(
            (throwaway_rationale or f"{THROWAWAY_USE_CASES[0]} — quick wizard, "
                                    "risk profil 'throwaway' (interní demo)")
            if profile["throwaway_or_evolve"] == "throwaway" else None
        ),
        reinforcement_t7="tým retro 7 dní po Rozhodnutí",
        reinforcement_t30="review metriky (po zafixování při Rozhodnutí)",
        reinforcement_t60="—",
        reinforcement_t90="—",
        reinforcement_budget_pd=2.0,
        tier=tier or default_tier(profile["capacity_profile"], quick_bootstrap=True,
                                  risk_profile=risk_profile),
        target_repo_url=target_repo_url,
        path_owners=owners_by_step,
        core=list(core) if core else None,
    )
    charter_md = render_charter_md(charter)
    project_id = persist_charter(charter, charter_md)

    # 2. Roles — explicit selection; owners of the 6 path steps flow into roles
    owners: dict[int, str] = {int(k): v for k, v in (role_owners or {}).items()}
    idx_set = set(room_role_idx)
    if owners_by_step:
        for step, idx in PATH_STEP_ROLE.items():
            owners.setdefault(idx, owners_by_step[step])
            idx_set.add(idx)
        # Facilitátor není krok cesty: default = PdM (ADR-0021), pokud není dedikovaný
        owners.setdefault(3, owners_by_step["produkt"])
    selected = _resolve_quick_roles(sorted(idx_set), owners)
    role_result = persist_roles(slug, profile["capacity_profile"], selected)
    for w in role_result.get("warnings", []):
        # Počet lidí v jádru hlídáme výše (okna smí mít další jména); zbytek přebereme.
        if "víc než 5 lidí" not in w:
            warnings.append(w.lstrip("⚠ ").strip())

    # 3. Triage — deferred; okna ho podepisují (`pflanzer checkpoint`).
    _set_triage_deferred(project_id, profile)
    if metric and (kill_criteria or profile.get("kill_criteria")) and owners_by_step:
        # Zadání z Kickoffu (problém + metrika + kill + jména 6 kroků) = discovery checkpoint.
        from tool.cli.checkpoint import sign as sign_checkpoint
        sign_checkpoint(slug, "zadani", by=decider_name,
                        note=f"Kickoff: {hook} · metrika: {metric} · kill: "
                             f"{kill_criteria or profile.get('kill_criteria')}")

    # 4. Production-path fields
    primary_branch = repos[0].branch if repos else (target_branch or None)
    repos_json = (
        json.dumps([r.to_dict() for r in repos], ensure_ascii=False)
        if repos and (len(repos) > 1 or repos[0].workspace or target_repos) else None
    )
    with transaction() as conn:
        conn.execute(
            "UPDATE projects SET target_repo_url = ?, "
            "target_branch = COALESCE(?, target_branch), "
            "production_readiness_target = ?, "
            "acceptance_criteria_md = COALESCE(?, acceptance_criteria_md), "
            "target_branch_owner = COALESCE(?, target_branch_owner), "
            "shadow_pm = COALESCE(?, shadow_pm), "
            "path_owners_json = COALESCE(?, path_owners_json), "
            "core_json = COALESCE(?, core_json) "
            "WHERE id = ?",
            (target_repo_url, primary_branch, profile.get("production_readiness_target", 0),
             acceptance_criteria_md, target_branch_owner, shadow_pm,
             json.dumps(owners_by_step, ensure_ascii=False) if owners_by_step else None,
             json.dumps(core, ensure_ascii=False) if core else None,
             project_id),
        )
        if repos_json:
            if not _has_column(conn, "projects", "target_repos"):
                raise ValueError(
                    "DB nemá sloupec projects.target_repos — spusť `python3 tool/db/migrate.py`."
                )
            conn.execute("UPDATE projects SET target_repos = ? WHERE id = ?",
                         (repos_json, project_id))
        audit(
            conn,
            action="quick.bootstrap",
            target_type="project",
            target_id=project_id,
            payload={
                "slug": slug, "decider": decider_name,
                "risk_profile": risk_profile, "roles": room_role_idx,
                "target_repo_url": target_repo_url,
                "target_repos": [r.to_dict() for r in repos],
                "production_readiness_target": profile.get("production_readiness_target", 0),
                "path_owners": owners_by_step, "core": core, "metric": metric,
                "warnings": warnings,
            },
        )

    feature_path = _write_acceptance_feature(slug, hook, metric, acceptance_criteria_md)

    return {
        "project_id": project_id,
        "slug": slug,
        "name": name,
        "risk_profile": risk_profile,
        "roles_count": len(selected),
        "production_readiness_target": profile.get("production_readiness_target", 0),
        "target_repo_url": target_repo_url,
        "path_owners": owners_by_step,
        "core": core,
        "target_repos": [r.to_dict() for r in repos],
        "charter_path": str(DATA_ROOT / "charters" / f"{slug}.md"),
        "acceptance_feature_path": feature_path,
        "warnings": warnings,
        "defer_note": (
            "Triage odložený (Kickoff nemá 48h pre-read). Checkpoint Bezpečnost & "
            "právo proběhne do 48 h po Buildu, před Ship."
        ),
        "next_step": "/pm build",
    }


def _has_column(conn: Any, table: str, column: str) -> bool:
    return any(r[1] == column for r in conn.execute(f"PRAGMA table_info({table})").fetchall())


def _resolve_target_repos(
    *, target_repos: Any, target_repo_url: str | None, target_branch: str | None,
) -> tuple[list[TargetRepo], str | None]:
    """Validate target repo input (N8). Returns (repos primary-first, primary URL).

    - `target_repos` (list / JSON / wizard text) wins; primary = FE/app repo
      unless `target_repo_url` names one of them explicitly.
    - Only `target_repo_url`: a plain URL → single repo; wizard-style text
      (`role=url#branch:workspace, ...`) is accepted there too.
    """
    if not target_repos and target_repo_url and re.search(r"[,=#\s]", target_repo_url.strip()):
        target_repos, target_repo_url = target_repo_url, None
    if target_repos:
        repos = normalize_target_repos(target_repos, fallback_branch=target_branch or "main")
        if not repos:
            raise ValueError("target_repos je prázdné.")
        if target_repo_url and not validate_repo_url(target_repo_url):
            raise ValueError(f"target_repo_url '{target_repo_url}' není platná git URL.")
        idx = pick_primary(repos, target_repo_url)
        repos = [repos[idx]] + [r for i, r in enumerate(repos) if i != idx]
        return repos, repos[0].url
    if target_repo_url:
        if not validate_repo_url(target_repo_url):
            raise ValueError(
                f"target_repo_url '{target_repo_url}' není platná git URL "
                "(očekávám https://<host>/<org>/<repo> nebo git@<host>:<org>/<repo>.git)."
            )
        return (normalize_target_repos(None, fallback_url=target_repo_url.strip(),
                                       fallback_branch=target_branch or "main"),
                target_repo_url.strip())
    return [], None


def _resolve_quick_roles(
    room_role_idx: list[int],
    owners: dict[int, str],
) -> list[dict[str, Any]]:
    """Bypass decision tree — explicit role selection from Kickoff."""
    catalog_path = REPO_ROOT / "tool" / "data" / "role_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    # Always include 1, 2, 3 — and never silently drop a role that has an owner
    needed = set(room_role_idx) | {1, 2, 3} | {int(i) for i, n in owners.items() if n}
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
                "Kickoff: explicitní výběr"
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
    placeholder_url: str  # předgenerovaný placeholder pro zápis do toolu


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

# Mob mode (per ADR-0016): sequential iterations, ne paralelní angles.
# Synthesis konsenzus: 1 deep + 1 refinement default; 3rd iteration opt-in.
MOB_ITERATION_ANGLES = [
    ("iter1", "deep first stab",
     "Postav nejdůležitější část flow. Mob driver/navigator rotation 8 min. "
     "Tým všichni vidí každý keystroke."),
    ("iter2", "refine or pivot",
     "Z iterace 1: co fungovalo (drž), co ne (přepiš). Po obsahu druhé "
     "iteraci voting nebo pokud jeste zbývá čas — opt-in iter3."),
    ("iter3", "ambitious 3rd (opt-in, warning: degraded quality)",
     "Pouze pokud iter1+2 hotové < 60 min. Risk: rushed, low quality."),
]


def recommend_mode(
    *, production_target: int, risk_profile: str, room_size: int,
    has_veto_role: bool = False, new_team: bool = False,
    onboarding_member: bool = False, single_high_stakes: bool = False,
) -> tuple[str, str]:
    """Return (mode, rationale_for_decider) per ADR-0016 decision tree.

    Default = parallel. Mob = explicit opt-in for narrow class.
    """
    # Hard blocks (production)
    if production_target >= 70:
        return "parallel", (
            f"Production target {production_target} ≥ 70 — paralelní pro "
            "% LOC reuse a per-variant audit trail. Mob = sunk-cost commitment."
        )
    if risk_profile == "production":
        return "parallel", (
            "Risk profile 'production' — 3 varianty dají Decideri real choice; "
            "mob produces 1 artefact = no fallback."
        )
    # Hard blocks (room geometry per cognitive-load perspektiva)
    if room_size > 5:
        return "parallel", (
            f"Tým má {room_size} lidí > 5 (Hunter Industries cap). "
            "Mob breaks at 6+ — observer fatigue + 70/30 air-time inequity. "
            "Paralelní škáluje přidáním dvojic; mob ne."
        )
    if has_veto_role and risk_profile != "throwaway":
        return "parallel", (
            "Veto role v týmu (Security/Legal/A11y) — paralelní umožňuje "
            "veto registr per variant. V mobu jen 1 artefakt = veto = kill all."
        )

    # Mob-positive signals
    if new_team or onboarding_member:
        return "mob", (
            "Nový tým / onboarding — mob's biggest win = shared mental "
            "model + skill transfer (Hattie d≈0.55 peer learning effect)."
        )
    if single_high_stakes:
        return "mob", (
            "Single high-stakes decision — mob přinese cross-functional "
            "alignment v 1 commit history (audit-grade trace)."
        )

    # Default
    return "parallel", (
        "Default paralelní — 3 angles dají Decideri exploration breadth. "
        "Mob opt-in pro narrow case (új tým, single-stake decision, ≤ 5 lidí)."
    )


def builder_prompts(slug: str, hook: str, n_variants: int = 3,
                    prefer_hosted: bool = False,
                    mode: str = "parallel") -> dict[str, Any]:
    """Generate copy-paste prompts pro buildery (Build, v0.5).

    Modes:
    - **parallel** (default): 3× claude-code s VARIANT_ANGLES (A/B/C paralelně
      v 3 worktrees, branch pflanzer/<slug>-X). Diversity skrz prompty.
    - **mob**: 2-3× claude-code s MOB_ITERATION_ANGLES (sequential iterations
      v 1 worktree, max 5 lidí u monitoru). Per ADR-0016.

    prefer_hosted (paralelní only): mix s Bolt/v0/Lovable.
    """
    if mode not in ("parallel", "mob"):
        raise ValueError(f"mode must be 'parallel' or 'mob', got '{mode}'")
    if not 1 <= n_variants <= 3:
        raise ValueError("n_variants must be 1..3")

    rec = recommend_for_slug(slug, prefer_hosted_preview=prefer_hosted)
    if rec["blocked"]:
        return {"blocked": True, "reason": rec["blocked_reason"], "prompts": []}

    if not prefer_hosted:
        # In-repo default: 3× claude-code (or codex-cli if user prefers).
        # Diversity je v promptu (angle), ne v builderu.
        top_builder = rec["shortlist"][0]["builder"] if rec["shortlist"] else "claude-code"
        shortlist = [{"builder": top_builder}] * n_variants
    else:
        shortlist = rec["shortlist"][:n_variants]
        if len(shortlist) < n_variants:
            shortlist += [{"builder": "manual"}] * (n_variants - len(shortlist))

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
    has_feature = _feature_exists(slug)

    # Audit N8: FE + BE + monorepo workspace — every variant gets all repos.
    try:
        repos = load_target_repos(slug)
    except ValueError:
        repos = []

    angles = VARIANT_ANGLES if mode == "parallel" else MOB_ITERATION_ANGLES

    prompts: list[VariantPrompt] = []
    for i, (item, (name, angle, brief)) in enumerate(zip(shortlist, angles[:n_variants])):
        builder = item["builder"]
        if mode == "mob" and builder == "claude-code":
            prompt_text = _render_mob_iteration_prompt(
                hook, brief, constraints, slug=slug, iteration=name,
                iteration_idx=i, total_iterations=n_variants, repos=repos,
                has_feature=has_feature,
            )
            placeholder_url = f"local://pflanzer/{slug}-mob (npm run dev)"
        else:
            prompt_text = _render_builder_prompt(hook, brief, constraints, builder,
                                                 slug=slug, variant=name, repos=repos,
                                                 has_feature=has_feature)
            if builder in ("claude-code", "codex-cli"):
                placeholder_url = f"local://pflanzer/{slug}-{name} (npm run dev)"
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
        "mode": mode,
        "diversity_hint": rec.get("diversity_hint", ""),
        "acceptance_feature": f"tests/acceptance/{slug}.feature" if has_feature else None,
        "push_hint": (
            f"Commitni a pushni tests/acceptance/{slug}.feature — worktrees se klonují z originu "
            "a jinak ho neuvidí."
        ) if has_feature else None,
        "target_repos": [r.to_dict() for r in repos],
        "prompts": [
            {
                "name": p.name, "builder": p.builder, "builder_url": p.builder_url,
                "angle": p.angle, "prompt_text": p.prompt_text,
                "placeholder_url": p.placeholder_url,
            }
            for p in prompts
        ],
    }


def _feature_exists(slug: str) -> bool:
    """Acceptance .feature je v prompt jen pokud skutečně existuje (cwd = target repo)."""
    return (Path.cwd() / "tests" / "acceptance" / f"{slug}.feature").is_file()


def _builder_rules(slug: str, hook: str, variant: str, has_feature: bool,
                   *, mob: bool = False) -> str:
    """Společná pravidla pro AI buildera (v0.5): constitution, kontroly v Buildu, štítek."""
    feature_line = (
        f"3. Přečti `tests/acceptance/{slug}.feature` (Deciderovo zadání) — "
        "implementace musí projít všemi scénáři.\n"
        if has_feature else ""
    )
    n = 4 if has_feature else 3
    label = f"Varianta {variant} k rozhodnutí — není to hotový produkt"
    return f"""POVINNÝ POSTUP (NEKÓDUJ, DOKUD KROKY 1–{n} NEJSOU HOTOVÉ):
1. Přečti `.pflanzer/CONSTITUTION.md` a drž se jí (nepřekročitelná pravidla).
2. Přečti `docs/INTEGRATION_GUIDE.md` a drž se jeho konvencí (auth, API klient,
   state, logger, folder layout, test runner). Pokud chybí, zastav se a zeptej se týmu.
{feature_line}{n}. Přečti 3–5 existujících komponent podobného typu (glob) a použij stejné patterns.

PAK kóduj:
{n + 1}. Po KAŽDÉM logickém kroku spusť lint + test + build target repa (příkazy najdeš
   v package.json / Makefile / README) a commitni JEN zelené. Červené oprav před
   commitem — kontroly běží během Buildu, ne až v Ship.
{n + 2}. Žádné nové závislosti bez důvodu v commit message.
{n + 3}. Na první obrazovku (a do README varianty) dej viditelný štítek:
   „{label}“ + problem statement: „{hook}“.
{n + 4}. Commit v Conventional Commits: `feat({slug}): {'mob ' if mob else 'variant '}{variant} — <jednou větou co se mění>`
   Trailery Pflanzer-* doplní git hook; NIKDY nepřidávej `Co-Authored-By` za AI."""


BE_CONTRACT_FIRST = (
    "CONTRACT-FIRST: nejdřív OpenAPI diff (změna `openapi.yaml` / kontraktu, "
    "ukaž ji týmu a FE páru), pak implementace endpointu + testy. FE staví "
    "proti kontraktu (mock z OpenAPI), ne proti hotovému BE."
)


def _tilde(path: Path) -> str:
    home = str(Path.home())
    p = str(path)
    return "~" + p[len(home):] if p.startswith(home + "/") else p


def _repo_lines(slug: str, variant: str, repos: list[TargetRepo]) -> list[str]:
    """One line per repo worktree of a variant (N8): path, workspace, BE angle."""
    lines = []
    for idx, (repo, path) in enumerate(variant_worktrees(slug, repos, variant)):
        line = f"- `{repo.role}`{' (primární)' if idx == 0 else ''}: `{_tilde(path)}`"
        if repo.workspace:
            line += f" — pracuj v `{repo.workspace}/`"
        if repo.is_backend:
            line += f" — {BE_CONTRACT_FIRST}"
        lines.append(line)
    return lines


def _primary_path(slug: str, variant: str, repos: list[TargetRepo]) -> str:
    if repos:
        return _tilde(variant_worktrees(slug, repos, variant)[0][1])
    return f"~/.pflanzer/targets/{slug}-{variant}"


def _render_mob_iteration_prompt(
    hook: str, brief: str, constraints: list[str], *,
    slug: str, iteration: str, iteration_idx: int, total_iterations: int,
    repos: list[TargetRepo] | None = None,
    has_feature: bool = False,
) -> str:
    """Mob mode prompt — sequential iteration v 1 worktree (ADR-0016).

    1 deep + 1 refinement default, 8min driver rotation, observer-task
    assignment, single shared branch. Max 5 lidí u monitoru.
    """
    constraint_lines = "\n".join(f"- {c}" for c in constraints)
    feature_obs = (
        f"  - Voice of Acceptance — sleduje tests/acceptance/{slug}.feature\n"
        if has_feature else ""
    )
    repos = repos or []
    mob_path = _primary_path(slug, "mob", repos)
    mob_add_dirs = "".join(f" --add-dir {_tilde(pth)}"
                           for _, pth in variant_worktrees(slug, repos, "mob")[1:]) if repos else ""
    repo_block = ""
    if len(repos) > 1 or any(r.workspace for r in repos):
        repo_block = ("\nRepozitáře (všechny na branchi pflanzer/" + slug + "-mob):\n"
                      + "\n".join(_repo_lines(slug, "mob", repos)) + "\n")

    setup_block = ""
    if iteration_idx == 0:
        setup_block = f"""**SETUP (facilitátor, 1× per Build):**

```bash
pflanzer worktree setup --slug {slug} --mode mob
# → Naclonuje target_repo_url, vytvoří 1 worktree '<slug>-mob'
# → Branch: pflanzer/{slug}-mob (single shared)
```

**Tým u 1 monitoru** (max 5 lidí — víc = zúžit scope nebo přesunout zástupce na okna):

```bash
cd {mob_path}
claude{mob_add_dirs}
```

**Driver/navigator/observer rotation**:
- Driver (kbd): 6 min active + 2 min handoff = 8 min cycle
- Navigator: říká strategy nahlas (NE syntax)
- Observers (max 3): explicit task per role
  - Voice of Decider-zadání — připomíná XYZ hypotézu z Charteru
  - Voice of UX — flag a11y / clarity issues
{feature_obs}  - Voice of QA — flag missing test coverage
- **Decider mute kontrakt**: Decider u stavby není (anti-HiPPO); do Buildu
  nemluví, rozhoduje až při Rozhodnutí.
- **Hard break 25 min** (observer fatigue)
"""
    elif iteration_idx == 1:
        setup_block = f"""**ITERACE 2 — refine or pivot** (po cca 25–30 min na iter1):

Než začnete:
1. **5min pauza** — voda, krátká procházka
2. **Per-role rationale** (silent, 2 min): co fungovalo? co ne?
3. **Rychlý check**: „ponechat iter1, refine na iter2, nebo pivot?“

V Claude Code (stejná session, stejný worktree):
```
Stejný cíl: {hook}

Z iter1 ZACHOVAT: <doplň, co se týmu líbilo>
Z iter1 ZAHODIT / přepsat: <doplň, co tým označil jako nefungující>

Tato iterace = {brief}.

Postup:
1. Zachovej, co funguje (nepřepisuj working code).
2. Refaktoruj / přidej, co tým označil.
3. Lint + test + build musí projít jako u iter1; commituj jen zelené.
4. Commit: `feat({slug}): mob iter2 — <co se mění oproti iter1>`
```
"""
    else:
        setup_block = f"""**ITERACE 3 (opt-in, ⚠ riziko nižší kvality)**:

Pokud iter1+2 hotové < 60 min, zkuste ambiciózní 3. iteraci. Jinak SKIP —
jděte rovnou na zápis do toolu a Rozhodnutí.

```
Tato iterace = {brief}.
Riziko: rushed, low quality. Facilitátor se zeptá týmu: „máme čas, nebo končíme?“
```
"""

    return setup_block + f"""

**Vlož do Claude Code (po setup):**

```
Cíl týmu: {hook}

Tato iterace ({iteration}, {iteration_idx + 1}/{total_iterations}): {brief}
{repo_block}
{_builder_rules(slug, hook, 'mob', has_feature, mob=True)}

Constraints:
{constraint_lines}

Output:
- Branch: pflanzer/{slug}-mob (sdílený, sekvenční commity)
- Preview: `npm run dev` (na velký TV pro tým)
- České texty v UI, EN identifikátory v kódu
- Acceptance scénáře pass rate ≥ 80 %
```
"""


def _render_builder_prompt(
    hook: str, brief: str, constraints: list[str], builder: str,
    slug: str | None = None, variant: str | None = None,
    repos: list[TargetRepo] | None = None,
    has_feature: bool = False,
) -> str:
    """Render a copy-paste prompt block per builder type."""
    constraint_lines = "\n".join(f"- {c}" for c in constraints)
    slug = slug or "<slug>"
    variant = variant or "X"
    rules = _builder_rules(slug, hook, variant, has_feature)
    repos = repos or []
    multi = len(repos) > 1 or bool(repos and repos[0].workspace)
    repo_block = ""
    add_dirs = "".join(f" --add-dir {_tilde(pth)}"
                       for _, pth in variant_worktrees(slug, repos, variant)[1:]) if repos else ""
    if multi:
        repo_block = (f"\nRepozitáře varianty {variant} (všechny na branchi pflanzer/{slug}-{variant}):\n"
                      + "\n".join(_repo_lines(slug, variant, repos)) + "\n")

    # In-repo CLI builders (Claude Code, Codex CLI) → git worktree protocol
    if builder in ("claude-code", "codex-cli"):
        cli_cmd = "claude" if builder == "claude-code" else "codex"
        cd_block = f"cd {_primary_path(slug, variant, repos)}\n{cli_cmd}{add_dirs}"
        if add_dirs:
            cd_block += "   # --add-dir = BE / další repa varianty ve stejné CC session"
        elif builder == "codex-cli":
            cd_block += "      # OpenAI Codex CLI"
        return f"""**Setup worktree (1× per Build, dělá facilitátor):**

```bash
pflanzer worktree setup --slug {slug}
# → Naclonuje target repo(s) do ~/.pflanzer/targets/<repo-slug>/
# → Vyrobí worktrees A/B/C per repo + hook s trailery + guard + install
```

**Tvoje dvojice (varianta {variant}):**

```bash
{cd_block}
```

Vlož do AI:

```
Cíl týmu: {hook}

Postav variantu {variant} v tomto repu: {brief}.
{repo_block}
{rules}

Constraints:
{constraint_lines}

Output:
- Branch: pflanzer/{slug}-{variant} (v target repu)
- Preview: `npm run dev` v target worktree (sdílíme přes port-forward na TV)
- České texty v UI, EN identifikátory v kódu, komentáře EN
- Acceptance scénáře z .feature souboru (pokud existuje) pass rate ≥ 80 %
```
"""

    # Hosted SaaS builders (Bolt/v0/Lovable) — original flow
    label = f"Varianta {variant} k rozhodnutí — není to hotový produkt"
    if builder == "manual":
        intro = "Pair-program v repu (žádný online builder potřeba):"
    elif builder == "cursor":
        intro = (
            f"Otevři **Cursor** ({BUILDER_LANDINGS[builder]}) a v repu vytvoř "
            f"branch `pflanzer/{slug}-{variant}`, pak vlož prompt:"
        )
    else:
        intro = f"Otevři **{builder}** ({BUILDER_LANDINGS[builder]}) a vlož tento prompt:"
    return f"""{intro}

```
Cíl týmu: {hook}

Postav: {brief}.

Na první obrazovku dej viditelný štítek „{label}“ + problem statement „{hook}“.

Constraints:
{constraint_lines}

Output:
- Funkční preview URL (sdílíme na velkém TV)
- 1 obrazovka stačí
- České texty v UI, EN identifikátory v kódu
- Po dokončení: **Push to GitHub** → vlož repo URL do Ship (production hardening)
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
                      "description": str, "diff_summary": {...} | str,
                      "role_preferences": [...] }].
                diff_summary (KROK 4.5 diff walkthrough) se persistuje do
                variants.diff_summary_md a vypíše v handoffu.
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
            "diff_summary": v.get("diff_summary"),
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
        diff_col = (", diff_summary_md" if _has_column(conn, "variants", "diff_summary_md")
                    else ", NULL")
        if sess:
            variants = list(conn.execute(
                "SELECT name, builder, prototype_url, preference_score, description_md"
                + diff_col + " FROM variants WHERE session_id = ? "
                "ORDER BY preference_score DESC",
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

    diff_block = ""
    diff_parts = [f"### Varianta {v[0]}\n\n{v[5]}\n" for v in variants if v[5]]
    if diff_parts:
        diff_block = (
            "\n## Diff walkthrough (per varianta)\n\n"
            "> Co AI napsalo podle dev páru (KROK 4.5): reuse / nové / mock.\n\n"
            + "\n".join(diff_parts)
        )

    commit_rows = "\n".join(
        f"| {c[0]} | {c[1] or '—'} | **{c[2] or '—'}** | {c[3]} |"
        for c in commitments
    ) or "| — | — | — | — |"

    deferred_block = ""
    if deferred:
        tracks = ", ".join(t[0] for t in deferred)
        deferred_block = (
            f"\n## ⚠ Před produkcí\n\n"
            f"Triage odložený při Kickoffu pro tracks: **{tracks}**.\n"
            f"Checkpoint Bezpečnost & právo (20 min) musí proběhnout před Ship.\n"
        )

    decision_block = "_(Rozhodnutí ještě nezaznamenáno — spusť `/pm decide`.)_"
    if decision:
        decision_block = decision[0]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""{BRAND_LINE}

# Handoff — {proj[1]}

> Slug: `{proj[2]}` · Vygenerováno: {today} · Risk: `{proj[6]}` / `{proj[7]}` / data `{proj[8]}`
> Jednostránkový souhrn po Buildu: kdo / co / do kdy / kill kritéria.

## Co děláme

{proj[3]}

## Decider

**{proj[4]}** rozhodl(a):

{decision_block}

## Varianty (podle skóre)

| Variant | Builder | Score | Preview |
|---------|---------|-------|---------|
{var_table}
{diff_block}
## Kdo / co / commitment

| Role | Owner | Commitment 0-3 | Rationale |
|------|-------|----------------|-----------|
{commit_rows}

> Commitment legenda: 0 = neúčastnit se Asyncu · 1 = read-only feedback ·
> 2 = active scoring · 3 = co-creation prototypu.

## Kill kritéria

{proj[5]}

## Kapacita

{proj[9]} person-days (dle risk profilu Charteru; default v0.5 ≈ 6–8 PD).
{deferred_block}
## Co dál

1. Owner každé role s commitment ≥ 2 začíná pracovat **dnes**.
2. Async: **3–5 pracovních dní** — zástupci klikají a komentují (hub nebo `pflanzer feedback add`).
3. Sběr feedbacku: `/pm feedback`.
4. Rozhodnutí (Go / Iterate / Kill): `/pm decide {proj[2]}`.
5. Před produkcí: Checkpoint Bezpečnost & právo a Checkpoint Provozu, pak `/pm ship`.

---

*Generováno z `/pm`. Plná auditovatelná stopa (Charter, role, triage): `{display_path(DATA_ROOT / "charters" / (proj[2] + ".md"))}`,
`{display_path(DATA_ROOT / "sessions" / proj[2] / "_summary.md")}`.*
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

    p_boot = sub.add_parser("bootstrap", help="Kickoff: Charter + role + jména kroků cesty + odložený triage")
    p_boot.add_argument("--spec", type=Path, required=True,
                        help="JSON: {hook, decider_name, room_role_idx, risk_profile, slug?, role_owners?, "
                             "metric?, kill_criteria?, path_owners?{byznys,produkt,design,vyvoj,bezpecnost,provoz}, core?[], "
                             "target_repo_url?, target_repos? (list nebo 'fe=url#branch:workspace, be=url'), tier?}")

    p_prompts = sub.add_parser("prompts", help="Prompty pro buildery (Build)")
    p_prompts.add_argument("--slug", required=True)
    p_prompts.add_argument("--hook", required=True)
    p_prompts.add_argument("--n", type=int, default=3)
    p_prompts.add_argument("--mode", choices=["parallel", "mob"], default="parallel",
                           help="parallel = 3 angles paralelně; mob = sequential iterations (per ADR-0016)")
    p_prompts.add_argument("--prefer-hosted", action="store_true",
                           help="Opt-in pro Bolt/v0/Lovable (parallel only). Default = claude-code 3×.")

    p_vote = sub.add_parser("vote", help="Record voting + Decider's call")
    p_vote.add_argument("--spec", type=Path, required=True)

    p_hand = sub.add_parser("handoff", help="Render 1-page handoff MD")
    p_hand.add_argument("--slug", required=True)

    args = p.parse_args()

    try:
        if args.cmd == "bootstrap":
            spec = json.loads(args.spec.read_text(encoding="utf-8"))
            out = bootstrap(**spec)
        elif args.cmd == "prompts":
            out = builder_prompts(args.slug, args.hook, args.n,
                                  prefer_hosted=args.prefer_hosted,
                                  mode=args.mode)
        elif args.cmd == "vote":
            spec = json.loads(args.spec.read_text(encoding="utf-8"))
            out = record_voting(**spec)
        elif args.cmd == "handoff":
            path = write_handoff(args.slug)
            out = {"handoff_path": str(path), "preview": render_handoff(args.slug)[:400] + "…"}
        else:
            p.error(f"unknown cmd: {args.cmd}")
    except ValueError as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(2)

    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
