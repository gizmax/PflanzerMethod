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

from tool.cli import apprun  # noqa: E402
from tool.cli import worktree as _worktree_mod  # noqa: E402
from tool.cli.builder_decision import recommend_for_slug  # noqa: E402
from tool.cli.charter import (  # noqa: E402
    BRAND_LINE,
    PATH_STEPS,
    THROWAWAY_USE_CASES,
    CharterInput,
    is_ai_owner,
    owner_display,
    people_check,
    persist_charter,
    render_charter_md,
    split_owner_signer,
    validate_ai_stand_ins,
)
from tool.cli.db import (  # noqa: E402
    DATA_ROOT,
    audit,
    current_actor,
    display_path,
    load_project_toml,
    resolve_local_repo_url,
    transaction,
)
from tool.cli.roles import persist_roles  # noqa: E402
from tool.cli.session import persist as persist_session  # noqa: E402
from tool.cli.session import rp_range_errors  # noqa: E402
from tool.cli.tier import (  # noqa: E402
    MOB_ITERATIONS,
    QUICK_BUILD_MINUTES,
    TIER_LABELS,
    project_tier,
    validate_tier,
)
from tool.cli.ux import (  # noqa: E402
    CzechArgumentParser,
    async_days,
    did_you_mean,
    die,
    emit,
    project_not_found_message,
    read_spec,
    tips_for_project,
)
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
        "label": "Ostré nasazení pro všechny uživatele (přísnější brány)",
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

# Výchozí stupeň podle risk profilu (spec `tier` ho přebíjí; `/pm live` posílá quick výslovně).
DEFAULT_TIER_BY_RISK = {"throwaway": "quick", "pilot": "lean", "production": "lean"}

# 5-role default mix per `02-role-catalog.md` § Výběr zástupců — rychlý strom
# (always-on 1+2+3, plus FE+UX pro UI fíčuru — covers 80 % corporate cases).
DEFAULT_ROOM = [1, 2, 3, 4, 6]


# --------------------------------------------------------------------------
# Bootstrap (Charter + Roles + Triage shortcut)
# --------------------------------------------------------------------------


def _cut_at_word(text: str, max_len: int, sep: str) -> str:
    """Cut `text` to `max_len` on a word boundary (`sep`), never mid-word."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    if text[max_len] == sep:      # the cut already falls exactly between two words
        return cut.rstrip(sep)
    head, found, _ = cut.rpartition(sep)
    return (head if found and head else cut).rstrip(sep)


SLUG_MAX_WORDS = 5


def slugify(s: str, max_len: int = 40, max_words: int = SLUG_MAX_WORDS) -> str:
    """Convert hook into URL-safe slug: max ~5 words, cut on a word boundary."""
    s = _strip_diacritics(s.lower().strip())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    words = s.split("-")
    if len(words) > max_words:
        s = "-".join(words[:max_words])
    s = _cut_at_word(s, max_len, "-")
    return s or f"session-{date.today().isoformat()}"


TITLE_MAX = 50


def short_title(hook: str, max_len: int = TITLE_MAX) -> str:
    """Krátký název projektu z hooku: první věta/klauzule (před čárkou, pomlčkou, dvojtečkou)."""
    hook = " ".join(hook.split())
    clause = re.split(r"\s[-–—]\s|[,;:.!?](?:\s|$)|\s\(", hook, maxsplit=1)[0].strip()
    if len(clause) < 8:        # příliš krátký úlomek = nic neříká, vezmi celý hook
        clause = hook
    return short_name(clause, max_len)


def short_name(hook: str, max_len: int = 80) -> str:
    """Project name from the hook: whole sentence, else whole words up to `max_len`.

    The ellipsis appears only when something was cut; never mid-word.
    """
    hook = " ".join(hook.split())
    if len(hook) <= max_len:
        return hook
    # Prefer the longest run of whole sentences that fits (no ellipsis needed).
    ends = [m.end() for m in re.finditer(r"[.!?](?=\s)", hook) if m.end() <= max_len]
    if ends and ends[-1] >= 12:
        return hook[:ends[-1]].rstrip(".!? ")
    return _cut_at_word(hook, max_len - 1, " ").rstrip(" ,.;:-") + "…"


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


MISSING_STEP_HINTS = {
    "byznys": "Bez Decidera (člověka s mandátem říct Go nebo Kill) se Kickoff nesvolává. "
              "Napiš jeho jméno — AI byznys zastoupit nesmí (ADR-0023).",
    "produkt": "Může ho krýt Decider nebo PdM (napiš jméno). V Quick nebo u throwaway smí "
               "produkt zastoupit `AI`.",
    "design": "V malém interním nástroji ho může krýt PdM (napiš jeho jméno), nebo dej `AI` — "
              "design smí zastoupit AI (ADR-0023).",
    "vyvoj": "U klávesnice sedí vývojář — napiš jeho jméno. AI vývoj nezastoupí (ADR-0023).",
    "bezpecnost": "Napiš jméno (stačí 20min okno), nebo `AI` jako pre-check — pilot "
                  "a production ho pak musí podepsat člověk do 48 h (ADR-0023).",
    "provoz": "Napiš jméno z provozu (stačí 20min okno), nebo `AI` jako pre-check — u pilotu "
              "smí podepsat i vývojář z jádra (ADR-0023).",
}


def _normalize_path_owners(raw: dict[str, str] | None) -> dict[str, str] | None:
    """Validate the 6 steps of the path; every step needs a name or `AI` (ADR-0021/0023).

    Accepts keys with/without diacritics ("bezpečnost", "vývoj"). Returns
    canonical dict in step order, or None when `raw` was not provided.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("path_owners musí být objekt se 6 kroky: "
                         '{"byznys": "Dana", "produkt": "Petr", "design": "AI", '
                         '"vyvoj": "Tomáš", "bezpecnost": "Jana", "provoz": "Karel"}.')
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
    for step, label in PATH_STEPS.items():
        if not given.get(step):
            raise ValueError(f"Chybí jméno u kroku {label}. {MISSING_STEP_HINTS[step]}")
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
        "# Kostra — builder doplní konkrétní scénáře své varianty.",
        f"Požadavek: {hook}",
        "",
    ]
    if criteria_md and re.search(r"(?mi)^\s*(Sc[eé]n[aá]ř|Scenario)", criteria_md):
        lines.append(criteria_md.strip())
    else:
        crits = [c.strip(" -*\t") for c in (criteria_md or "").splitlines() if c.strip()]
        for i, crit in enumerate(crits, 1):
            lines += [f"  Scénář: Kritérium {i}", f"    Pak {crit}", ""]
        if not crits:
            # Kostra chování — builder ji doplní pro svou variantu (testovatelné kroky).
            lines += [
                "  Scénář: Uživatel vyřeší problém hlavním tokem",
                "    Pokud jsem uživatel v situaci ze zadání",
                "    Když použiji novou funkci",
                "    Pak se problém ze zadání vyřeší bez obcházení a bez chyby",
                "",
            ]
        if metric:
            # Metrika se měří po nasazení (/pm retro), ne testem — proto jen komentář.
            lines += [f"  # Metrika úspěchu (měří se po nasazení, ne testem): {metric}", ""]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return str(out)


def _normalize_ai_signers(raw: dict[str, str] | None,
                          shorthand: dict[str, str]) -> dict[str, str] | None:
    """Merge `ai_signers` from the spec with signers from `AI:agent / Jméno` shorthand."""
    if raw is not None and not isinstance(raw, dict):
        raise ValueError('ai_signers musí být objekt {"bezpecnost": "Pavel Šnek"}.')
    out: dict[str, str] = dict(shorthand)
    for k, v in (raw or {}).items():
        key = _strip_diacritics(str(k)).lower().strip().replace(" ", "_")
        key = {"bezpecnost_a_pravo": "bezpecnost", "bezpecnost_pravo": "bezpecnost"}.get(key, key)
        out[key] = v.strip() if isinstance(v, str) else ""
    return out or None


def _split_shorthand_owners(raw: dict[str, str] | None) -> tuple[Any, dict[str, str]]:
    """`"bezpecnost": "AI:security-expert / Pavel Šnek"` -> owners bez jména + signers."""
    if not isinstance(raw, dict):
        return raw, {}
    clean: dict[str, str] = {}
    signers: dict[str, str] = {}
    for k, v in raw.items():
        owner, signer = split_owner_signer(v) if isinstance(v, str) else (v, None)
        clean[k] = owner
        if signer:
            key = _strip_diacritics(str(k)).lower().strip().replace(" ", "_")
            signers[{"bezpecnost_a_pravo": "bezpecnost",
                     "bezpecnost_pravo": "bezpecnost"}.get(key, key)] = signer
    return clean, signers


_CONSTITUTION_NO_DATA_RE = re.compile(
    r"(?i)(nesm[ií]\s+sb[ií]rat|nesb[ií]r|bez\s+osobn|žádn[ée]\s+osobn|zadn[ée]\s+osobn"
    r"|žádn[ée]\s+formul[aá]ř|zadn[ée]\s+formul[aá]r|\bL1\b(?!\s*[–-]\s*L4)|no\s+personal)")
# Pravidlo o datech jen pro VÝVOJ („ve vývoji jen syntetická data“, L1 pro dev) není rozpor
# s produkčním sběrem — rozpor je, jen když se zakazuje sběr / ukládání v produkci / aplikaci.
_CONSTITUTION_DEV_SCOPE_RE = re.compile(
    r"(?i)(vývoj|vyvoj|development|\bdev\b|testov|\btest\b|syntetick|synthetic|mock|fixtur|seed"
    r"|lokáln|lokaln|staging)")
_CONSTITUTION_PROD_SCOPE_RE = re.compile(
    r"(?i)(produkc|production|\bprod\b|aplikac|uživatel|uzivatel|zákazn|zakazn|návštěv|navstev"
    r"|\bweb|formul)")
_BRIEF_PERSONAL_RE = re.compile(
    r"(?i)(telefon|jm[eé]n[oa]|e-?mail|objedn[aá]v|rezervac|rezervov|formul[aá]ř|formular"
    r"|kontakt|adres[ay])")


def constitution_conflicts(hook: str, metric: str | None = None,
                           criteria: str | None = None,
                           cwd: Path | None = None) -> list[str]:
    """⚠ když CONSTITUTION zakazuje sběr osobních údajů / formulářů a zadání je chce."""
    path = (cwd or Path.cwd()) / ".pflanzer" / "CONSTITUTION.md"
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    rules = [ln.strip() for ln in text.splitlines()
             if _CONSTITUTION_NO_DATA_RE.search(ln) and not ln.lstrip().startswith("#")
             and "<doplň>" not in ln
             and not (_CONSTITUTION_DEV_SCOPE_RE.search(ln)
                      and not _CONSTITUTION_PROD_SCOPE_RE.search(ln))]
    brief = " ".join(x for x in (hook, metric, criteria) if x)
    wanted = sorted({m.group(1).lower() for m in _BRIEF_PERSONAL_RE.finditer(brief)})
    if not rules or not wanted:
        return []
    return [
        "CONSTITUTION (.pflanzer/CONSTITUTION.md) zřejmě odporuje zadání: pravidlo „"
        + rules[0][:90] + "“, ale zadání zmiňuje " + ", ".join(wanted[:4]) + ". "
        "Builderi se řídí zadáním z Kickoffu, ale upravte CONSTITUTION (výjimka pro tuto funkci, "
        "třída dat) a commitněte ji před Buildem, ať se s ní nehádají."]


def bootstrap(
    *, hook: str, decider_name: str, risk_profile: str,
    room_role_idx: list[int] | None = None, slug: str | None = None,
    role_owners: dict[int, str] | None = None,
    target_repo_url: str | None = None,
    acceptance_criteria_md: str | None = None,
    target_branch_owner: str | None = None,
    shadow_pm: str | None = None,
    metric: str | None = None,
    kill_criteria: str | None = None,
    path_owners: dict[str, str] | None = None,
    ai_signers: dict[str, str] | None = None,
    core: list[str] | None = None,
    target_repos: list[dict[str, Any]] | str | None = None,
    target_branch: str | None = None,
    throwaway_rationale: str | None = None,
    tier: str | None = None,
    leading_metric: str | None = None,
    guardrail_metric: str | None = None,
    title: str | None = None,
    session_mode: str | None = None,
    windows: Any = None,
) -> dict[str, Any]:
    """Založí projekt: Charter + role + jména kroků cesty + odložený triage.

    JEDINÁ vstupní cesta (Kickoff i /pm live).

    Args:
        hook: 1-věta problem statement (xyz_hypothesis + name).
        decider_name: člověk s mandátem říct Go/Iterate/Kill.
        room_role_idx: catalog_idx 1..18 rolí v jádru/okně. Nepovinné — když chybí,
            odvodí se z path_owners (kroky cesty), jinak DEFAULT_ROOM.
        risk_profile: 'throwaway' | 'pilot' | 'production'.
        slug: explicit slug; default = slugify(hook).
        role_owners: catalog_idx → jméno (kdo z týmu tu roli zastává).
        metric: metrika úspěchu (→ primary_lagging_metric + acceptance .feature).
        kill_criteria: přepíše default z risk profilu.
        path_owners: {"byznys","produkt","design","vyvoj","bezpecnost","provoz"} → jména
            nebo `AI` / `AI:<agent>` (ADR-0023: jen produkt v Quick/throwaway, design,
            bezpečnost a provoz jako pre-check; NIKDY byznys a vývoj).
            Pokud zadáno a některý krok chybí → ValueError s lidskou větou (ADR-0021).
        ai_signers: {"bezpecnost": "Pavel Šnek"} — člověk, který podepíše AI náhradu kroku
            (bezpecnost | provoz | design | produkt). Zkráceně přímo v path_owners:
            `"AI:security-expert / Pavel Šnek"` (oddělovač ` / ` nebo `|`).
        core: jména jádra (3–4 lidé; > 5 unikátních = warning).
        title: krátký název projektu (≤ 50 znaků) pro status, reporty a PR title;
            bez něj se odvodí z hooku (první věta/klauzule).
        session_mode: 'parallel' (3 varianty A/B/C, výchozí) | 'mob' (jedna společná varianta,
            ADR-0016). Uloží se k projektu; `worktree setup`, `prompts` a `/pm build` ho pak
            použijí bez `--mode`. Doporučení (`recommend_mode`) se jen ukáže, nic nevynucuje.
        windows: okna z Kickoffu (kdy je Build, checkpointy, Rozhodnutí): objekt
            `{"Build": "st 21.10. 9:00-12:00"}`, nebo seznam textů / `{"okno", "kdy"}`.
            Uloží se k projektu a ukáže ve `status`.
        leading_metric / guardrail_metric: nepovinné; když chybí, uloží se None
            (do PR/SHIP se nic nedosazuje).
        target_repos: volitelně více repozitářů (audit N8) — list
            `[{"role": "fe", "url": ..., "branch": "main", "workspace": "apps/web"}]`
            nebo wizard text `fe=<url>[#branch][:workspace], be=<url>`.
            Primární repo (FE / app) se zapíše i do `target_repo_url`.
        target_branch: base branch pro jednorepo případ (default 'main').
        throwaway_rationale: jen pro risk_profile='throwaway' (ADR-0005 v0.4);
            default = use case „discovery-only pilot“ (interní demo).
        tier: 'quick' | 'lean' | 'full' (ADR-0017). Spec ho respektuje. Default podle
            risk profilu: throwaway -> Quick, pilot -> Lean, production -> Lean.
            `/pm live` posílá `tier: "quick"` výslovně.

    Returns dict: project_id, slug, roles_count, warnings, ...
    """
    if risk_profile not in RISK_PROFILES:
        near = did_you_mean(str(risk_profile), RISK_PROFILES)
        raise ValueError(f"Neznámý risk_profile „{risk_profile}“."
                         + (f" Myslel jste „{near}“?" if near else "") + " Použij: "
                         f"{', '.join(RISK_PROFILES)} (throwaway = demo, pilot = 5–20 uživatelů, "
                         "production = ostrý provoz).")
    profile = RISK_PROFILES[risk_profile]
    session_mode = _normalize_session_mode(session_mode)
    windows_list = _normalize_windows(windows)
    slug = slug or slugify(hook)
    path_owners, short_signers = _split_shorthand_owners(path_owners)
    owners_by_step = _normalize_path_owners(path_owners)  # fail fast, before any write
    signers_by_step = _normalize_ai_signers(ai_signers, short_signers)
    if signers_by_step and not owners_by_step:
        raise ValueError("ai_signers dává smysl jen spolu s path_owners (kroky s AI náhradou).")
    tier = (validate_tier(tier, profile["capacity_profile"]) if tier
            else DEFAULT_TIER_BY_RISK[risk_profile])
    ai_stand_ins: list[dict[str, str]] = []
    ai_warnings: list[str] = []
    if owners_by_step:
        ai_stand_ins, ai_warnings = validate_ai_stand_ins(
            owners_by_step, risk_profile=risk_profile, tier=tier, ai_signers=signers_by_step)
        if signers_by_step:   # ukládáme jen kroky, které AI opravdu zastupuje
            signers_by_step = {k: v for k, v in signers_by_step.items()
                               if is_ai_owner(owners_by_step.get(k))} or None
        if room_role_idx is None:
            room_role_idx = sorted(set(PATH_STEP_ROLE.values()))
    room_role_idx = list(room_role_idx) if room_role_idx is not None else list(DEFAULT_ROOM)

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

    # Pořadí varování je stálé: AI náhrady -> kdo smí podepsat -> lidé v místnosti -> role.
    warnings: list[str] = list(ai_warnings)
    if owners_by_step and is_ai_owner(owners_by_step.get("bezpecnost")) \
            and risk_profile != "throwaway" and not (signers_by_step or {}).get("bezpecnost"):
        from tool.cli.checkpoint import signer_guidance
        warnings.append(signer_guidance("bezpecnost", owners_by_step, risk_profile))
    warnings += people_check(core, owners_by_step)

    warnings += constitution_conflicts(hook, metric, acceptance_criteria_md)

    # 1. Charter
    if title is not None and not title.strip():
        title = None
    if title and len(title.strip()) > TITLE_MAX:
        raise ValueError(f"title je moc dlouhý ({len(title.strip())} znaků, max {TITLE_MAX}). "
                         "Krátký název projektu, např. „Online objednávka“.")
    name = title.strip() if title else short_title(hook)
    built = ("jedné společně postavené variantě (mob), o které se rozhodne"
             if session_mode == "mob" else
             "třech funkčních variantách, mezi kterými se rozhodne")
    xyz = (
        f"Problém k vyřešení: **{hook.rstrip('.')}**. Ověříme ho na {built} "
        f"nad běžícím kódem."
        + (f" Měřítko úspěchu: {metric.strip().rstrip('.')}." if (metric or "").strip() else "")
    )  # risk profil (profile["label"]) patří jen do metadat, ne do tvrzení o tom, co se mění
    charter = CharterInput(
        slug=slug,
        name=name,
        xyz_hypothesis=xyz,
        decider_name=decider_name,
        decider_mandate_from="Kickoff (formalizuje se po Rozhodnutí)",
        cpo_escalation_contact=f"{decider_name} (self-attested při Kickoffu)",
        sponsor_name=decider_name,
        primary_lagging_metric=(metric or "").strip() or None,
        leading_metric=(leading_metric or "").strip() or None,
        guardrail_metric=(guardrail_metric or "").strip() or None,
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
        tier=tier,
        target_repo_url=target_repo_url,
        path_owners=owners_by_step,
        ai_signers=signers_by_step,
        core=list(core) if core else None,
    )
    charter_md = render_charter_md(charter)
    project_id = persist_charter(charter, charter_md)

    # 2. Roles — explicit selection; owners of the 6 path steps flow into roles
    owners: dict[int, str] = {int(k): v for k, v in (role_owners or {}).items()}
    idx_set = set(room_role_idx)
    if owners_by_step:
        for step, idx in PATH_STEP_ROLE.items():
            owners.setdefault(idx, owner_display(owners_by_step[step], step))
            idx_set.add(idx)
        # Facilitátor není krok cesty: default = PdM (ADR-0021), pokud není dedikovaný
        owners.setdefault(3, owner_display(owners_by_step["produkt"], "produkt"))
    selected = _resolve_quick_roles(sorted(idx_set), owners)
    role_result = persist_roles(slug, profile["capacity_profile"], selected)
    for w in role_result.get("warnings", []):
        # Počet lidí hlídáme výše (okna smí mít další jména); zbytek přebereme.
        if "víc než 5 lidí" not in w and "nefunguje" not in w:
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
            "core_json = COALESCE(?, core_json), "
            "session_mode = ?, windows_json = COALESCE(?, windows_json) "
            "WHERE id = ?",
            (target_repo_url, primary_branch, profile.get("production_readiness_target", 0),
             acceptance_criteria_md, target_branch_owner, shadow_pm,
             json.dumps(owners_by_step, ensure_ascii=False) if owners_by_step else None,
             json.dumps(core, ensure_ascii=False) if core else None,
             session_mode,
             json.dumps(windows_list, ensure_ascii=False) if windows_list else None,
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
                "path_owners": owners_by_step, "ai_signers": signers_by_step,
                "core": core, "metric": metric, "session_mode": session_mode,
                "windows": windows_list,
                "ai_stand_ins": ai_stand_ins, "warnings": warnings,
            },
        )

    feature_path = _write_acceptance_feature(slug, hook, metric, acceptance_criteria_md)

    # Doporučení režimu se jen ukáže (rozhoduje člověk), nic nevynucuje.
    room = {n.strip().lower() for n in (core or []) if n and n.strip()} or {
        owner_display(v, k).lower() for k, v in (owners_by_step or {}).items()}
    rec_mode, rec_why = recommend_mode(
        production_target=int(profile.get("production_readiness_target", 0) or 0),
        risk_profile=risk_profile, room_size=len(room),
        has_veto_role=bool(owners_by_step) and not is_ai_owner(
            (owners_by_step or {}).get("bezpecnost")))
    if session_mode == rec_mode:
        mode_note = f"Režim {session_mode}: {rec_why}"
    else:
        mode_note = (f"Zvolený režim: {session_mode}. Doporučení metody je {rec_mode} "
                     f"({rec_why}) — je to jen doporučení, rozhodujete vy.")

    return {
        "project_id": project_id,
        "slug": slug,
        "name": name,
        "risk_profile": risk_profile,
        "roles_count": len(selected),
        "tier": tier,
        "decider": decider_name,
        "ai_stand_ins": ai_stand_ins,
        "production_readiness_target": profile.get("production_readiness_target", 0),
        "target_repo_url": target_repo_url,
        "path_owners": owners_by_step,
        "ai_signers": signers_by_step,
        "core": core,
        "session_mode": session_mode, "windows": windows_list,
        "mode_recommendation": {"mode": rec_mode, "rationale": rec_why},
        "mode_note": mode_note,
        "target_repos": [r.to_dict() for r in repos],
        "charter_path": str(DATA_ROOT / "charters" / f"{slug}.md"),
        "acceptance_feature_path": feature_path,
        "acceptance_commit_hint": (
            f"Commitněte a pushněte `tests/acceptance/{slug}.feature` — worktrees se klonují "
            "z originu a jinak ho Build neuvidí." if feature_path else None),
        "warnings": list(dict.fromkeys(warnings)),
        "defer_note": (
            "Triage odložený (Kickoff nemá 48h pre-read). Checkpoint Bezpečnost & "
            "právo proběhne do 48 h po Buildu, před Ship."
        ),
        "next_step": f"/pm triage {slug}" if tier == "full" else f"/pm build {slug}",
    }


SESSION_MODES = ("parallel", "mob")


def _normalize_session_mode(mode: str | None) -> str:
    """'parallel' | 'mob' (velikost písmen nerozhoduje); None -> parallel. Jinak česká chyba."""
    if mode is None or not str(mode).strip():
        return "parallel"
    m = str(mode).strip().lower()
    if m not in SESSION_MODES:
        near = did_you_mean(m, SESSION_MODES)
        raise ValueError(f"Neznámý session_mode „{mode}“." + (f" Myslel jste „{near}“?" if near else "")
                         + " Použij: parallel (3 varianty A/B/C, výchozí) nebo mob (jedna "
                           "společná varianta u jednoho monitoru, ADR-0016).")
    return m


def _normalize_windows(raw: Any) -> list[dict[str, str]]:
    """Okna z Kickoffu -> [{"okno": …, "kdy": …}]. Přijme objekt, seznam textů nebo objektů."""
    if raw in (None, "", [], {}):
        return []
    bad = ValueError("„windows“ ve specu: zadej objekt {\"Build\": \"st 21.10. 9:00-12:00\", "
                     "\"Rozhodnutí\": \"pá 30.10. 10:00\"}, nebo seznam textů "
                     "[\"Build st 21.10. 9:00-12:00\"].")
    out: list[dict[str, str]] = []
    if isinstance(raw, dict):
        items: list[Any] = [{"okno": k, "kdy": v} for k, v in raw.items()]
    elif isinstance(raw, list):
        items = raw
    else:
        raise bad
    for it in items:
        if isinstance(it, str) and it.strip():
            out.append({"okno": it.strip(), "kdy": ""})
        elif isinstance(it, dict):
            name = str(it.get("okno") or it.get("name") or it.get("window") or "").strip()
            when = str(it.get("kdy") or it.get("when") or it.get("termin") or "").strip()
            if not name:
                raise bad
            out.append({"okno": name, "kdy": when})
        else:
            raise bad
    return out


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
    target_repo_url = resolve_local_repo_url(target_repo_url) if target_repo_url else target_repo_url
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
    facilitator_text: str = ""  # jen pro lidi: setup, příkazy, rotace (NEvkládá se do AI)
    ai_prompt: str = ""         # jen tohle se vkládá do AI


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
    ("C", "smart defaults", "Postav variantu s chytrými výchozími hodnotami z kontextu, který aplikace opravdu má (předvyplnění, nejčastější volba) — uživatel jen potvrdí"),
]

# Mob mode (per ADR-0016): sequential iterations, ne paralelní angles.
# Synthesis konsenzus: 1 deep + 1 refinement default; 3rd iteration opt-in.
MOB_ITERATION_ANGLES = [
    ("iter1", "deep first stab",
     "Postav nejdůležitější část flow. Mob driver/navigator rotation 8 min. "
     "Tým všichni vidí každý keystroke."),
    ("iter2", "refine or pivot",
     "Z iterace 1: co fungovalo (drž), co ne (přepiš). Po druhé "
     "iteraci následuje voting, nebo pokud ještě zbývá čas, opt-in iter3."),
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


def _hook_from_project(slug: str) -> str:
    """Hook projektu z DB (xyz_hypothesis „Problém k vyřešení: **…**“, jinak název)."""
    with transaction() as conn:
        row = conn.execute("SELECT xyz_hypothesis, name FROM projects WHERE slug = ?",
                           (slug,)).fetchone()
    if not row:
        raise ValueError(project_not_found_message(slug))
    m = re.search(r"\*\*(.+?)\*\*", row[0] or "", re.S)
    hook = (m.group(1) if m else row[1] or "").strip()
    if not hook:
        raise ValueError("Projekt nemá uložený hook — zadej ho: `--hook \"jedna věta\"`.")
    return hook


def project_session_mode(slug: str) -> str:
    """Uložený režim projektu (`projects.session_mode`), jinak parallel."""
    with transaction() as conn:
        row = conn.execute("SELECT session_mode FROM projects WHERE slug = ?", (slug,)).fetchone()
    return (row[0] if row and row[0] in SESSION_MODES else None) or "parallel"


def builder_prompts(slug: str, hook: str, n_variants: int | None = None,
                    prefer_hosted: bool = False,
                    mode: str | None = None) -> dict[str, Any]:
    """Generate copy-paste prompts pro buildery (Build, v0.5).

    Modes:
    - **parallel** (default): 3× claude-code s VARIANT_ANGLES (A/B/C paralelně
      v 3 worktrees, branch pflanzer/<slug>-X). Diversity skrz prompty.
    - **mob**: 2-3× claude-code s MOB_ITERATION_ANGLES (sequential iterations
      v 1 worktree, max 5 lidí u monitoru). Per ADR-0016.

    prefer_hosted (paralelní only): mix s Bolt/v0/Lovable.

    `mode=None` -> režim uložený v projektu (Kickoff `session_mode`). Po Iterate se staví
    jen varianty druhého kola (`status.iterate_plan`) a do promptů jde „Cíl tohoto kola“.
    V mob modu je jedna společná varianta `mob`; n_variants = počet iterací (default podle
    stupně: Quick 1 kolo × 30 min, jinak 2; `tier.MOB_ITERATIONS`).
    """
    from tool.cli.status import iterate_plan, split_iterate_focus, variant_findings

    with transaction() as conn:
        if not conn.execute("SELECT 1 FROM projects WHERE slug = ?", (slug,)).fetchone():
            raise ValueError(project_not_found_message(slug))
    mode = mode or project_session_mode(slug)
    if mode not in SESSION_MODES:
        raise ValueError(f"Neznámý režim „{mode}“. Použij parallel nebo mob.")
    if n_variants is not None and not 1 <= n_variants <= 3:
        raise ValueError("Počet variant (--n) musí být 1 až 3.")
    plan = iterate_plan(slug)
    focus = (plan or {}).get("focus")
    angles = VARIANT_ANGLES if mode == "parallel" else MOB_ITERATION_ANGLES
    if mode == "parallel" and plan:      # druhé kolo: jen varianty, které pokračují
        angles = [a for a in VARIANT_ANGLES if a[0] in plan["variants"]] or VARIANT_ANGLES
    if n_variants is None:
        n_variants = len(angles) if mode == "parallel" else MOB_ITERATIONS.get(
            project_tier(slug), 2)
    n_variants = min(n_variants, len(angles))
    revise: dict[str, str] = {}
    if focus and mode == "parallel" and plan:
        # Druhé kola: každá varianta dostane jen SVŮJ cíl (nebo společný), nic o cílech ostatních,
        # a její nálezy; staví se nad existující větví (ne od nuly).
        common, goals = split_iterate_focus(focus, plan["variants"])
        for nm, ang, _brief in angles:
            lines = []
            if nm in goals:
                lines.append(f"Cíl tohoto kola pro {nm}: {goals[nm].rstrip('.')}")
                if common:
                    lines.append(f"Společný cíl: {common.rstrip('.')}")
            elif common:
                lines.append(f"Cíl tohoto kola: {common.rstrip('.')}")
            else:
                lines.append(f"Cíl tohoto kola: {focus.rstrip('.')}" if not goals else
                             f"Cíl tohoto kola pro {nm}: drž se nálezů níže, zadání z Iterate "
                             "tuto variantu výslovně neuvádí")
            found = variant_findings(slug, nm)
            if found:
                lines.append(f"Nálezy k variantě {nm} (oprav před dalším kolem; critical nejdřív):")
                lines += [f"- {f}" for f in found]
            revise[nm] = f"Přístup varianty: {ang}.\n" + "\n".join(lines)
    elif focus:
        angles = [(nm, ang, f"{brief}.\nCíl tohoto kola: {focus.rstrip('.')}")
                  for nm, ang, brief in angles]

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
            "SELECT data_class, ai_act_tier, throwaway_or_evolve, name, target_branch "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()

    keyboard = keyboard_owner(slug)

    # Audit N8: FE + BE + monorepo workspace — every variant gets all repos.
    try:
        repos = load_target_repos(slug)
    except ValueError:
        repos = []
    stack = _detect_stack_for(slug, repos)

    throwaway = bool(proj and proj[2] == "throwaway")
    constraints = []
    if proj:
        if proj[0] == "L3":
            constraints.append("⚠ NESMÍŠ použít reálná data — jen synthetic / pseudonymized")
        if proj[1] in ("limited", "high") and re.search(
                r"(?i)\b(ai|llm|chat\w*|gener\w+|asistent\w*|umělá|umela)\b", hook):
            constraints.append("⚠ Pokud používáš AI v UI (chat / generation), přidej watermark + human-in-the-loop")
        if proj[2] == "throwaway":
            constraints.append(THROWAWAY_RULE)
        elif stack.js_frontend:
            constraints.append("Evolve target — drž se design system tokenů, žádné inline styly")
        else:
            constraints.append("Evolve target — drž se konvencí repa z INTEGRATION_GUIDE "
                               "(struktura, pojmenování, testy)")
    constraints.append("Žádné credentials v kódu, žádné .env."
                       + (" Pokud má varianta uživatelské rozhraní: WCAG 2.2 AA."
                          if stack.js_frontend or not stack.stack else ""))
    has_feature = _feature_exists(slug, repos)
    feature_repo = _feature_repo(slug, repos)

    prompts: list[VariantPrompt] = []
    heads: dict[str, str] = {}
    common_text = ""
    for i, (item, (name, angle, brief)) in enumerate(zip(shortlist, angles[:n_variants])):
        builder = item["builder"]
        run_hint = f" ({stack.run_cmd})" if stack.run_cmd else ""
        if mode == "mob" and builder == "claude-code":
            facilitator, ai_text = _render_mob_iteration_prompt(
                hook, brief, constraints, slug=slug, iteration=name,
                iteration_idx=i, total_iterations=n_variants, repos=repos,
                has_feature=has_feature, stack=stack, throwaway=throwaway,
            )
            placeholder_url = f"local://pflanzer/{slug}-mob{run_hint}"
            angle = f"iterace {i + 1}/{n_variants}: {angle}"
            name = "mob"                      # jedna společná varianta, jedno jméno
        else:
            facilitator, head, tail = _render_builder_prompt_parts(
                hook, brief, constraints, builder, slug=slug, variant=name, repos=repos,
                has_feature=has_feature, stack=stack, revise=revise.get(name),
                throwaway=throwaway)
            ai_text = f"{head}\n{tail}" if tail else head
            if tail and mode == "parallel":
                heads[name] = head
                if not common_text:       # pravidla se liší jen písmenem varianty -> X
                    common_text = (_render_builder_prompt_parts(
                        hook, brief, constraints, builder, slug=slug, variant="X",
                        repos=repos, has_feature=has_feature, stack=stack,
                        throwaway=throwaway)[2])
            if builder in ("claude-code", "codex-cli"):
                placeholder_url = f"local://pflanzer/{slug}-{name}{run_hint}"
            else:
                placeholder_url = f"https://sandbox.invalid/{slug}/{name}"
        prompts.append(VariantPrompt(
            name=name, builder=builder,
            builder_url=BUILDER_LANDINGS.get(builder, "n/a"),
            angle=angle, prompt_text=f"{facilitator}\n\n**Vlož do AI:**\n\n```\n{ai_text}\n```\n",
            placeholder_url=placeholder_url,
            facilitator_text=facilitator, ai_prompt=ai_text,
        ))

    return {
        "blocked": False,
        "slug": slug,
        "mode": mode,
        "iterate_focus": focus,
        "variants_in_play": [p.name for p in prompts] if plan else None,
        "diversity_hint": rec.get("diversity_hint", ""),
        "keyboard": keyboard,
        "stack": stack.stack, "stack_label": stack.label or None,
        "check_commands": stack.commands or [],
        "acceptance_feature": f"tests/acceptance/{slug}.feature" if has_feature else None,
        "acceptance_feature_repo": (
            feature_repo if feature_repo != "."
            else (repos[0].role if repos else None)),
        "check_commands_by_repo": {
            r.role: stack_profile(pth / r.workspace if r.workspace else pth).commands or []
            for r, pth in (variant_worktrees(slug, repos, "mob" if mode == "mob" else "A")
                           if repos else [])},
        "push_hint": (
            f"Commitni a pushni tests/acceptance/{slug}.feature — worktrees se klonují z originu "
            "a jinak ho neuvidí."
        ) if has_feature and not _feature_in_origin(
            slug, (repos[0].branch if repos else None) or (proj[4] if proj and len(proj) > 4 else None)
            or "main") else None,
        "setup_text": (_setup_block(slug) if heads and not all(
            _worktrees_ready(slug, repos, p.name) for p in prompts) else ""),
        "common_text": common_text,
        "variant_heads": heads,
        "target_repos": [r.to_dict() for r in repos],
        "prompts": [
            {
                "name": p.name, "builder": p.builder, "builder_url": p.builder_url,
                "angle": p.angle, "prompt_text": p.prompt_text,
                "facilitator_text": p.facilitator_text, "ai_prompt": p.ai_prompt,
                "placeholder_url": p.placeholder_url,
                "variant_head": heads.get(p.name),
            }
            for p in prompts
        ],
    }


THROWAWAY_RULE = ("Throw-away prototyp — žádný produkční kód ani pokrytí; testy: stačí 1 smoke / "
                  "akceptační test hlavního toku (kroky níže na to odkazují)")


def keyboard_owner(slug: str) -> str | None:
    """Kdo sedí u klávesnice = zástupce kroku Vývoj z Kickoffu (ne git user)."""
    try:
        with transaction() as conn:
            row = conn.execute("SELECT path_owners_json FROM projects WHERE slug = ?",
                               (slug,)).fetchone()
        owner = (json.loads(row[0]) if row and row[0] else {}).get("vyvoj")
    except Exception:  # noqa: BLE001 — jen informace pro lidi
        return None
    return owner if owner and not is_ai_owner(owner) else None


def _feature_in_origin(slug: str, branch: str) -> bool:
    """Je acceptance .feature už na `origin/<branch>`? (nelze zjistit -> False = hint se ukáže)."""
    import subprocess
    rel = f"tests/acceptance/{slug}.feature"
    try:
        res = subprocess.run(["git", "ls-tree", "-r", "--name-only", f"origin/{branch}"],
                             cwd=Path.cwd(), capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return False
    return res.returncode == 0 and rel in res.stdout.splitlines()


def _feature_repo(slug: str, repos: list[TargetRepo] | None = None) -> str | None:
    """Kde leží acceptance .feature: "." = cwd, jinak role repa (primární první).

    None = nikde. Multi-repo: hledá i ve worktrees varianty A každého repa."""
    rel = Path("tests") / "acceptance" / f"{slug}.feature"
    if (Path.cwd() / rel).is_file():
        return "."
    for repo, path in ([*variant_worktrees(slug, repos, "A"), *variant_worktrees(slug, repos, "mob")]
                       if repos else []):
        for base in ([path / repo.workspace] if repo.workspace else []) + [path]:
            if (base / rel).is_file():
                return repo.role
    return None


def _feature_exists(slug: str, repos: list[TargetRepo] | None = None) -> bool:
    """Acceptance .feature je v prompt jen pokud skutečně existuje (cwd nebo kterékoli repo)."""
    return _feature_repo(slug, repos) is not None


@dataclass
class StackProfile:
    """Co víme o stacku target repa — řídí příkazy v promptech (žádné `npm` u Pythonu)."""

    stack: str | None = None
    commands: list[str] | None = None   # kontroly po každém kroku (lint/test/build)
    run_cmd: str | None = None          # jak spustit náhled
    js_frontend: bool = False
    acceptance_glob: str | None = None  # např. tests/acceptance/*.test.ts(x)
    nextjs: bool = False

    @property
    def label(self) -> str:
        """Lidský popis stacku do promptů a výpisů („Next.js (App Router, TS)“, jinak `stack`)."""
        return self.detail or self.stack or ""
    detail: str | None = None

    @property
    def check_text(self) -> str:
        if self.commands:
            return " a ".join(f"`{c}`" for c in self.commands)
        return ("lint + test + build target repa (příkazy najdeš v package.json / Makefile / "
                "README)")

    @property
    def run_text(self) -> str:
        return f"`{self.run_cmd}`" if self.run_cmd else "podle README (příkaz napiš týmu do chatu)"


_JS_UI_DEPS = ("react", "vue", "svelte", "next", "nuxt", "@angular/core", "solid-js", "preact")


def _next_label(path: Path) -> str:
    ts = (path / "tsconfig.json").is_file()
    router = ("App Router" if any((path / d).is_dir() for d in ("app", "src/app"))
              else "Pages Router" if any((path / d).is_dir() for d in ("pages", "src/pages"))
              else "App Router")
    return f"Next.js ({router}, {'TS' if ts else 'JS'})"


def _node_acceptance_glob(path: Path, scripts: dict[str, Any], deps: dict[str, Any]) -> str:
    """Přípona akceptačních testů podle runneru: vitest/jest -> .test.ts(x) u TS, jinak .test.js
    (TS projekt s `node --test` -> .test.ts, Node >= 22.6 si poradí sám)."""
    runner = any(d in deps for d in ("vitest", "jest", "@jest/core", "ts-jest"))
    node_test = "node --test" in str(scripts.get("test", ""))
    if not runner and (path / "tsconfig.json").is_file() and (
            node_test or "typescript" in deps):
        return "tests/acceptance/*.test.ts"
    if runner or not node_test:
        ts = "typescript" in deps or (path / "tsconfig.json").is_file()
        if runner and ts:
            react = any(d in deps for d in ("react", "react-dom", "preact", "solid-js"))
            return "tests/acceptance/*.test.ts(x)" if react else "tests/acceptance/*.test.ts"
    return "tests/acceptance/*.test.js"


def _uses_ruff(path: Path) -> bool:
    """Má Python repo ruff (konfigurace nebo závislost)? Pak patří lint do kontrol."""
    if any((path / f).is_file() for f in ("ruff.toml", ".ruff.toml")):
        return True
    for f in ("pyproject.toml", "requirements.txt", "requirements-dev.txt"):
        try:
            if re.search(r"\bruff\b", (path / f).read_text(encoding="utf-8", errors="replace")):
                return True
        except OSError:
            continue
    return False


def stack_profile(path: Path | None) -> StackProfile:
    """Detect the stack of a repo/worktree from manifests (best effort, never raises)."""
    if path is None or not path.is_dir():
        return StackProfile()
    try:
        from tool.cli.quality_gates import detect_stack
        stack = detect_stack(path)
    except Exception:  # noqa: BLE001 — detection is advisory
        stack = None
    targets: set[str] = set()
    mk = path / "Makefile"
    if mk.is_file():
        targets = set(re.findall(r"^([A-Za-z0-9_.-]+)\s*:", mk.read_text(errors="replace"), re.M))
    if stack == "node":
        try:
            pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pkg = {}
        scripts = pkg.get("scripts") or {}
        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
        cmds = [c for key, c in (("lint", "npm run lint"), ("test", "npm test"),
                                 ("build", "npm run build")) if key in scripts]
        run = "npm run dev" if "dev" in scripts else ("npm start" if "start" in scripts else None)
        nextjs = apprun.is_nextjs(path)
        return StackProfile("node", cmds, run, js_frontend=any(d in deps for d in _JS_UI_DEPS),
                            acceptance_glob=_node_acceptance_glob(path, scripts, deps),
                            nextjs=nextjs, detail=_next_label(path) if nextjs else None)
    if stack == "python":
        vpy = ".venv/bin/python" if (path / ".venv" / "bin" / "python").exists() else "python3"
        cmds = ["make test" if "test" in targets else f"{vpy} -m pytest"]
        if "lint" in targets:
            cmds.append("make lint")
        elif _uses_ruff(path):
            cmds.append("ruff check .")
        run = "make run" if "run" in targets else None
        return StackProfile("python", cmds, run, acceptance_glob="tests/acceptance/test_*.py")
    if stack == "go":
        # Makefile: všechny existující kontrolní cíle (test, lint, vet, build) + run; bez něj plný řetěz
        make_cmds = [f"make {t}" for t in ("test", "lint", "vet", "build") if t in targets]
        if make_cmds:
            cmds = make_cmds if "test" in targets else [*make_cmds, "go test ./..."]
        else:
            cmds = ["go build ./... && go vet ./... && go test ./..."]
        run = "make run" if "run" in targets else "go run ."
        return StackProfile("go", cmds, run, acceptance_glob="tests/acceptance/*_test.go")
    simple = {"maven": (["mvn -q test"], None),
              "gradle": (["./gradlew test" if (path / "gradlew").exists() else "gradle test"], None),
              "dotnet": (["dotnet test --nologo"], None)}
    if stack in simple:
        cmds, run = simple[stack]
        if "test" in targets and stack not in ("maven", "gradle"):
            cmds = ["make test"]
        return StackProfile(stack, cmds, run)
    if targets & {"test", "check"}:
        cmds = [f"make {'test' if 'test' in targets else 'check'}"]
        if "lint" in targets:  # např. Python repo jen s requirements.txt: test i lint
            cmds.append("make lint")
        return StackProfile(None, cmds, "make run" if "run" in targets else None)
    return StackProfile()


def _detect_stack_for(slug: str, repos: list[TargetRepo]) -> StackProfile:
    """Stack of the primary repo: its variant A worktree if present, else cwd."""
    candidates: list[Path] = []
    for variant in ("A", "mob") if repos else ():
        wt = variant_worktrees(slug, repos, variant)[0][1]
        candidates.append(wt / repos[0].workspace if repos[0].workspace else wt)
    candidates.append(Path.cwd())
    for c in candidates:
        prof = stack_profile(c)
        if prof.stack or prof.commands:
            return prof
    return StackProfile()


def _builder_rules(slug: str, hook: str, variant: str, has_feature: bool,
                   *, mob: bool = False, stack: StackProfile | None = None,
                   multi_repo: bool = False, throwaway: bool = False) -> str:
    """Společná pravidla pro AI buildera (v0.5): constitution, kontroly v Buildu, štítek."""
    stack = stack or StackProfile()
    acc_file = (stack.acceptance_glob or
                ("tests/acceptance/test_*.py" if stack.stack == "python" else
                 "tests/acceptance/*_test.go" if stack.stack == "go" else
                 "tests/acceptance/" if stack.stack in ("maven", "gradle", "dotnet")
                 else "tests/acceptance/*.test.js"))
    acc_note = (" (package `acceptance`; Ship spustí `go test ./tests/acceptance/...`)"
                if stack.stack == "go" else "")
    scenarios = ("implementace musí pokrýt hlavní tok; u throw-away stačí 1 smoke / akceptační "
                 "test hlavního toku (ne všechny scénáře)" if throwaway
                 else "implementace musí projít všemi scénáři")
    feature_line = (
        f"3. Přečti `tests/acceptance/{slug}.feature` (Deciderovo zadání) — "
        f"{scenarios}. Akceptační test(y) k nim napiš do "
        f"`{acc_file}`{acc_note} (běžný test runner projektu"
        f"{'; v TS projektu .test.ts, ne .js' if acc_file.endswith('.ts') or acc_file.endswith('.ts(x)') else ''}"
        ") — Ship je spustí jako bránu acceptance.\n"
        if has_feature else ""
    )
    n = 4 if has_feature else 3
    green = ("commitni JEN zelené (throw-away: stačí, že prochází ten 1 smoke / akceptační test "
             f"hlavního toku v `{acc_file}`, víc testů nepiš)" if throwaway
             else "commitni JEN zelené")
    label = f"Varianta {variant} k rozhodnutí — není to hotový produkt"
    checks = (f"kontroly repa, ve kterém jsi měnil kód (příkazy jsou u každého repa v seznamu "
              f"repozitářů výše; primární repo: {stack.check_text})" if multi_repo
              else stack.check_text)
    next_rules = ""
    if stack.nextjs:
        next_rules = (
            f"\n{n + 7}. Stack: {stack.label}. `next build` (i `npm run build`) přepíše `.next` pod "
            "běžícím `next dev` a preview pak vrací 500: neběž ho, když preview této varianty "
            f"běží; pokud ho potřebuješ, hned po něm spusť `pflanzer preview restart --slug "
            f"{slug} --variants {'<VARIANTA>' if mob else variant}`. Dev odznak Next překrývá "
            "rohy UI (CTA): v `next.config` nastav `devIndicators: false`.")
    venv_rule = ""
    if stack.stack == "python" and not stack.nextjs:
        venv_rule = (f"\n{n + 7}. Python: `.venv/bin` je v PATH (Makefile volá `python` / `pytest` "
                     "z `.venv`); mimo `make` použij `.venv/bin/python`, ne systémový `python3`.")
    return f"""POVINNÝ POSTUP (NEKÓDUJ, DOKUD KROKY 1–{n} NEJSOU HOTOVÉ):
1. Přečti `.pflanzer/CONSTITUTION.md` a drž se jí (nepřekročitelná pravidla).
2. Přečti `docs/INTEGRATION_GUIDE.md` a drž se jeho konvencí (auth, API klient,
   state, logger, folder layout, test runner). Pokud chybí, zastav se a zeptej se týmu.
{feature_line}{n}. Přečti 3–5 existujících souborů podobného typu (glob) a použij stejné patterns.

PAK kóduj:
{n + 1}. Po KAŽDÉM logickém kroku spusť {checks} a {green}.
   Červené oprav před commitem — kontroly běží během Buildu, ne až v Ship.
{n + 2}. Žádné nové závislosti bez důvodu v commit message.
{n + 3}. Na první obrazovku (a do README varianty) dej viditelný štítek:
   „{label}“ + problem statement: „{hook}“. (Bez obrazovky: totéž do README a výpisu příkazu.)
{n + 4}. Commit v Conventional Commits: `feat({slug}): {'mob' if mob else 'variant ' + variant} — <jednou větou co se mění>`
   Trailery Pflanzer-* doplní git hook; NIKDY nepřidávej `Co-Authored-By` za AI.
{n + 5}. Nová funkce musí být dosažitelná odkazem z `/` a zapnutá v preview
   (preview běží s `PFLANZER_PREVIEW=1` a `FEATURE_FLAGS=all`; flag nesmí být default OFF).
{n + 6}. Při rozporu má přednost zadání z Kickoffu (Charter, .feature) před
   CONSTITUTION / INTEGRATION_GUIDE; rozpor napiš do commit message a nezastavuj se.{next_rules}{venv_rule}"""


BE_CONTRACT_FIRST = (
    "CONTRACT-FIRST: nejdřív OpenAPI diff (změna `openapi.yaml` / kontraktu, "
    "ukaž ji týmu a FE páru), pak implementace endpointu + testy. FE staví "
    "proti kontraktu (mock z OpenAPI), ne proti hotovému BE."
)


def _tilde(path: Path) -> str:
    home = str(Path.home())
    p = str(path)
    return "~" + p[len(home):] if p.startswith(home + "/") else p


def _has_openapi(path: Path) -> bool:
    """Obsahuje repo OpenAPI kontrakt (`openapi.*`, do hloubky 3, bez node_modules/.venv)?"""
    skip = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build"}
    try:
        stack = [(path, 0)]
        while stack:
            cur, depth = stack.pop()
            for ch in cur.iterdir():
                if ch.is_file() and ch.name.lower().startswith("openapi."):
                    return True
                if ch.is_dir() and depth < 3 and ch.name not in skip:
                    stack.append((ch, depth + 1))
    except OSError:
        return False
    return False


def _repo_lines(slug: str, variant: str, repos: list[TargetRepo]) -> list[str]:
    """One line per repo worktree of a variant (N8): path, workspace, BE angle, checks.

    Příkazy kontrol jdou per repo (Node npm vs Python make/.venv); CONTRACT-FIRST jen u
    backendu, který OpenAPI kontrakt opravdu má (worktree ještě není = nelze ověřit, platí
    pro backend)."""
    lines = []
    for idx, (repo, path) in enumerate(variant_worktrees(slug, repos, variant)):
        line = f"- `{repo.role}`{' (primární)' if idx == 0 else ''}: `{_tilde(path)}`"
        base = path / repo.workspace if repo.workspace else path
        if repo.workspace:
            line += f" — pracuj v `{repo.workspace}/`"
        prof = stack_profile(base)
        if len(repos) > 1 and prof.commands:
            line += " — kontroly: " + " a ".join(f"`{c}`" for c in prof.commands)
        if repo.is_backend and (not path.is_dir() or _has_openapi(base)):
            line += f" — {BE_CONTRACT_FIRST}"
        lines.append(line)
    return lines


def _multi_repo_rules(slug: str, variant: str, repos: list[TargetRepo]) -> str:
    """Kde je které repo a co se smí měnit (multi-repo projekt)."""
    wts = variant_worktrees(slug, repos, variant)
    names = ", ".join(f"`{r.role}`" for r, _ in wts)
    return (f"Měnit smíš jen repa varianty {variant}: {names} (cesty výše; sekundární jsou "
            "připojená přes `--add-dir`). Všude jinde jen čti. Změny dělej v tom repu, kam "
            "patří (UI v primárním, API v jeho repu), commituj per repo na branch "
            f"`pflanzer/{slug}-{variant}`. Preview spustí všechna repa; primární najde ostatní "
            "v env `<ROLE>_URL` — adresy ani porty nehardcoduj. Na API odkazuj takto: v prohlížeči "
            "(kód UI) čti `import.meta.env.VITE_API_URL` (Vite; Next `process.env.NEXT_PUBLIC_API_URL`, "
            "CRA `REACT_APP_API_URL`) a volej `${VITE_API_URL}/cesta`; na serveru (SSR, skripty, "
            "server-to-server) čti `API_URL`. V preview je prohlížečová proměnná relativní cesta "
            "`/__pflanzer/api` za heslem preview (proxy ji směruje na API stejné varianty), "
            "proto skládej URL jen z ní, bez `http://localhost:…`. Pro roli jiného jména "
            "nahraď `API` jejím názvem velkými písmeny.")


def _primary_path(slug: str, variant: str, repos: list[TargetRepo]) -> str:
    if repos:
        return _tilde(variant_worktrees(slug, repos, variant)[0][1])
    return _tilde(_worktree_mod.TARGETS_CACHE / f"{slug}-{variant}")


def _output_block(slug: str, branch: str, stack: StackProfile, has_feature: bool,
                  *, mob: bool = False) -> str:
    """Output sekce promptu — jen příkazy, které dávají smysl pro stack target repa."""
    lines = [f"- Branch: {branch} (v target repu{', sdílený, sekvenční commity' if mob else ''})",
             f"- Náhled / spuštění: {stack.run_text}"
             + (" (na velký TV pro tým)" if mob else " v target worktree"),
             "- České texty pro uživatele, EN identifikátory v kódu, komentáře EN"]
    if has_feature or mob:
        lines.append("- Acceptance scénáře z .feature souboru (pokud existuje) pass rate ≥ 80 %")
    return "\n".join(lines)


def _render_mob_iteration_prompt(
    hook: str, brief: str, constraints: list[str], *,
    slug: str, iteration: str, iteration_idx: int, total_iterations: int,
    repos: list[TargetRepo] | None = None,
    has_feature: bool = False, stack: StackProfile | None = None,
    throwaway: bool = False,
) -> tuple[str, str]:
    """Mob mode — sequential iteration v 1 worktree (ADR-0016).

    Vrací (text pro facilitátora, text k vložení do AI). 1 deep + 1 refinement
    default, 8min driver rotation, single shared branch, max 5 lidí u monitoru.
    """
    stack = stack or StackProfile()
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
        if len(repos) > 1:
            repo_block += "\n" + _multi_repo_rules(slug, "mob", repos) + "\n"

    if iteration_idx == 0:
        if _worktrees_ready(slug, repos, "mob"):
            setup_block = (f"**Worktree `{slug}-mob` už existuje** (větev pflanzer/{slug}-mob) — "
                           "setup se nespouští znovu.\n\n")
        else:
            setup_block = f"""**SETUP (facilitátor, 1× per Build):**

```bash
pflanzer worktree setup --slug {slug} --mode mob
# → Naclonuje target_repo_url, vytvoří 1 worktree '<slug>-mob'
# → Branch: pflanzer/{slug}-mob (single shared)
```

"""
        if total_iterations == 1:
            timing = (f"- **Stavba: 1 kolo × {QUICK_BUILD_MINUTES} min** (Quick). Druhá iterace není; "
                      "po ní rovnou zápis do toolu (`pflanzer vote`).")
        else:
            timing = "- **Hard break 25 min** (observer fatigue)"
        facilitator = f"""{setup_block}**Tým u 1 monitoru** (max 5 lidí — víc = zúžit scope nebo přesunout zástupce na okna):

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
{timing}

Do AI vlož text z bloku „Vlož do AI“ níže."""
        ai_head = f"Cíl týmu: {hook}\n\nTato iterace ({iteration}, 1/{total_iterations}): {brief}"
    elif iteration_idx == 1:
        facilitator = """**ITERACE 2 — refine or pivot** (po cca 25–30 min na iter1):

Než začnete:
1. **5min pauza** — voda, krátká procházka
2. **Per-role rationale** (silent, 2 min): co fungovalo? co ne?
3. **Rychlý check**: „ponechat iter1, refine na iter2, nebo pivot?“

Do stejné Claude Code session (stejný worktree) vlož text níže a v něm doplň,
co tým chce zachovat a co zahodit."""
        ai_head = (f"Stejný cíl: {hook}\n\nZ iter1 ZACHOVAT: <doplň, co se týmu líbilo>\n"
                   "Z iter1 ZAHODIT / přepsat: <doplň, co tým označil jako nefungující>\n\n"
                   f"Tato iterace = {brief}.\n\nPostup:\n1. Zachovej, co funguje (nepřepisuj working code).\n"
                   "2. Refaktoruj / přidej, co tým označil.\n"
                   f"3. {stack.check_text} musí projít jako u iter1; commituj jen zelené.\n"
                   f"4. Commit: `feat({slug}): mob iter2 — <co se mění oproti iter1>`")
    else:
        facilitator = """**ITERACE 3 (opt-in, ⚠ riziko nižší kvality)**:

Pokud iter1+2 hotové < 60 min, zkuste ambiciózní 3. iteraci. Jinak SKIP —
jděte rovnou na zápis do toolu a Rozhodnutí. Facilitátor se zeptá týmu:
„máme čas, nebo končíme?“"""
        ai_head = f"Tato iterace = {brief}.\nRiziko: rushed, low quality."

    ai = f"""{ai_head}
{repo_block}
{_builder_rules(slug, hook, 'mob', has_feature, mob=True, stack=stack,
                multi_repo=len(repos) > 1, throwaway=throwaway)}

Constraints:
{constraint_lines}

Output:
{_output_block(slug, f'pflanzer/{slug}-mob', stack, has_feature, mob=True)}"""
    return facilitator, ai


def _worktrees_ready(slug: str, repos: list[TargetRepo], variant: str) -> bool:
    """Worktree varianty (všech repo) už na disku existuje -> setup se v promptu nenabízí."""
    if not repos:
        return False
    try:
        return all(pth.exists() for _r, pth in variant_worktrees(slug, repos, variant))
    except Exception:  # noqa: BLE001 — poradní údaj
        return False


def _setup_block(slug: str, variants: str = "A/B/C") -> str:
    """Sdílený setup worktrees (jednou per Build) — společný všem variantám."""
    return f"""**Setup worktree (1× per Build, dělá facilitátor):**
`pflanzer worktree setup --slug {slug}` — naklonuje target repo(s) do `<data>/targets/`
(`PFLANZER_TARGETS_DIR` přepíše), vyrobí worktrees {variants} + hook s trailery + guard + install."""


def _render_builder_prompt(
    hook: str, brief: str, constraints: list[str], builder: str,
    slug: str | None = None, variant: str | None = None,
    repos: list[TargetRepo] | None = None,
    has_feature: bool = False, stack: StackProfile | None = None,
) -> tuple[str, str]:
    """Prompt per builder: (text pro facilitátora, text k vložení do AI)."""
    facilitator, head, tail = _render_builder_prompt_parts(
        hook, brief, constraints, builder, slug, variant, repos, has_feature, stack)
    return facilitator, (f"{head}\n{tail}" if tail else head)


def _render_builder_prompt_parts(
    hook: str, brief: str, constraints: list[str], builder: str,
    slug: str | None = None, variant: str | None = None,
    repos: list[TargetRepo] | None = None,
    has_feature: bool = False, stack: StackProfile | None = None,
    revise: str | None = None, throwaway: bool = False,
) -> tuple[str, str, str]:
    """(facilitátor, hlavička varianty, společná pravidla). Pro hosted buildery je tail prázdný.

    `revise` = druhé kolo po Iterate: text cíle a nálezů varianty; místo „Postav“ se upravuje
    existující varianta.
    """
    stack = stack or StackProfile()
    constraint_lines = "\n".join(f"- {c}" for c in constraints)
    slug = slug or "<slug>"
    variant = variant or "X"
    repos = repos or []
    multi = len(repos) > 1 or bool(repos and repos[0].workspace)
    rules = _builder_rules(slug, hook, variant, has_feature, stack=stack,
                           multi_repo=len(repos) > 1, throwaway=throwaway)
    repo_block = ""
    add_dirs = "".join(f" --add-dir {_tilde(pth)}"
                       for _, pth in variant_worktrees(slug, repos, variant)[1:]) if repos else ""
    if multi:
        repo_block = (f"\nRepozitáře varianty {variant} (všechny na branchi pflanzer/{slug}-{variant}):\n"
                      + "\n".join(_repo_lines(slug, variant, repos)) + "\n")
        if len(repos) > 1:
            repo_block += "\n" + _multi_repo_rules(slug, variant, repos) + "\n"

    # In-repo CLI builders (Claude Code, Codex CLI) → git worktree protocol
    if builder in ("claude-code", "codex-cli"):
        cli_cmd = "claude" if builder == "claude-code" else "codex"
        cd_block = f"cd {_primary_path(slug, variant, repos)}\n{cli_cmd}{add_dirs}"
        if add_dirs:
            cd_block += "   # --add-dir = BE / další repa varianty ve stejné CC session"
        elif builder == "codex-cli":
            cd_block += "      # OpenAI Codex CLI"
        setup = ("" if _worktrees_ready(slug, repos, variant)
                 else _setup_block(slug) + "\n\n")
        facilitator = f"""{setup}**Tvoje dvojice (varianta {variant}):**

```bash
{cd_block}
```

Do AI vlož text z bloku „Vlož do AI“ níže."""
        if revise:
            head = f"""Cíl týmu: {hook}

Uprav existující variantu {variant} podle nálezů v tomto repu (větev pflanzer/{slug}-{variant}
už existuje, nezačínej od nuly).
{revise}
{repo_block}"""
        else:
            head = f"""Cíl týmu: {hook}

Postav variantu {variant} v tomto repu: {brief}.
{repo_block}"""
        tail = f"""{rules}

Constraints:
{constraint_lines}

Output:
{_output_block(slug, f'pflanzer/{slug}-{variant}', stack, has_feature)}"""
        return facilitator, head, tail

    # Hosted SaaS builders (Bolt/v0/Lovable) — original flow
    label = f"Varianta {variant} k rozhodnutí — není to hotový produkt"
    if builder == "manual":
        facilitator = "Pair-program v repu (žádný online builder potřeba)."
    elif builder == "cursor":
        facilitator = (
            f"Otevři **Cursor** ({BUILDER_LANDINGS[builder]}) a v repu vytvoř "
            f"branch `pflanzer/{slug}-{variant}`, pak vlož prompt níže."
        )
    else:
        facilitator = f"Otevři **{builder}** ({BUILDER_LANDINGS[builder]}) a vlož prompt níže."
    ai = f"""Cíl týmu: {hook}

Postav: {brief}.

Na první obrazovku dej viditelný štítek „{label}“ + problem statement „{hook}“.

Constraints:
{constraint_lines}

Output:
- Funkční preview URL (sdílíme s týmem)
- 1 obrazovka stačí
- České texty v UI, EN identifikátory v kódu
- Po dokončení: **Push to GitHub** → vlož repo URL do Ship (production hardening)"""
    return facilitator, ai, ""


# --------------------------------------------------------------------------
# Voting — collect dot vote × dimensions × role
# --------------------------------------------------------------------------


VOTE_EXAMPLE = """{
  "slug": "moje-appka",
  "facilitator": "Jana Nováková",
  "votes": [
    {"name": "A", "builder": "claude-code", "description": "nejjednodušší flow",
     "prototype_url": "https://github.com/org/repo/pull/7",
     "role_preferences": [
       {"role_idx": 1, "user_value": 0.8, "effort": 0.3, "risk": 0.2, "strategic_fit": 0.9,
        "commitment_level": 2, "rationale": "nejrychlejší cesta k hodnotě"}]}
  ],
  "decider_call": {"shortlist": ["A"], "rationale": "A je nejrychlejší",
                   "veto_register": [], "parking_lot": []}
}"""


def _validate_votes(slug: str, facilitator: str, votes: Any, decider_call: Any) -> None:
    """Human errors with an example instead of KeyError/TypeError tracebacks."""
    def bad(msg: str) -> ValueError:
        return ValueError(f"{msg}\nSpec pro `vote` vypadá takto:\n{VOTE_EXAMPLE}")

    if not slug:
        raise bad("Ve specu chybí „slug“ (slug projektu).")
    if not facilitator:
        raise bad("Ve specu chybí „facilitator“ (jméno facilitátora).")
    if not isinstance(votes, list) or not votes:
        raise bad("Ve specu chybí seznam „votes“ (alespoň jedna varianta).")
    for i, v in enumerate(votes, 1):
        if not isinstance(v, dict):
            raise bad(f"Varianta č. {i} v „votes“ musí být objekt {{…}}.")
        label = v.get("name") or v.get("variant") or f"č. {i}"
        if not (v.get("name") or v.get("variant")):
            raise bad(f"Varianta č. {i} nemá „name“ (A, B nebo C).")
        prefs = v.get("role_preferences")
        if not isinstance(prefs, list) or not prefs:
            raise bad(f"Varianta {label} nemá „role_preferences“ (kdo ji jak ohodnotil).")
        for j, rp in enumerate(prefs, 1):
            if not isinstance(rp, dict):
                raise bad(f"Hodnocení č. {j} u varianty {label} musí být objekt {{…}}.")
            missing = [k for k in ("role_idx", "user_value", "rationale") if rp.get(k) in (None, "")]
            if missing:
                raise bad(f"Hodnocení č. {j} u varianty {label} nemá: {', '.join(missing)}. "
                          "Důvod (rationale) je povinný — jedna věta stačí.")
            for dim in ("user_value", "effort", "risk", "strategic_fit"):
                val = rp.get(dim)
                if val is None:
                    continue
                if isinstance(val, bool) or not isinstance(val, (int, float)) or not 0 <= val <= 1:
                    raise bad(f"Hodnocení č. {j} u varianty {label}: „{dim}“ musí být číslo "
                              f"od 0 do 1 (dostal jsem {val!r}). 0 = nejhorší, 1 = nejlepší.")
            for msg in rp_range_errors(rp):
                raise bad(f"Hodnocení č. {j} u varianty {label}: {msg}")
    if not isinstance(decider_call, dict) or not decider_call:
        raise bad("Ve specu chybí „decider_call“ (shortlist, rationale).")


def _is_no_url(url: str | None) -> bool:
    """Prázdný řetězec (nový zápis) i starý placeholder `sandbox.invalid` = „bez URL“."""
    return not url or "sandbox.invalid" in url


def _dead_local_url_warning(url: str, slug: str) -> str | None:
    """⚠ když URL míří na localhost / 127.0.0.1 a nikdo tam neodpovídá (preview neběží)."""
    if not url:
        return None
    from urllib.parse import urlsplit
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or host not in ("localhost", "127.0.0.1", "0.0.0.0"):
        return None
    if apprun.http_get(url, timeout=2.0) is not None:
        return None
    return f"URL {url} neodpovídá — preview neběží? `pflanzer preview up --slug {slug}`"


def record_voting(
    *, slug: str, facilitator: str, votes: list[dict[str, Any]],
    decider_call: dict[str, Any] | None = None, real_urls: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Persist voting outputs via session.persist.

    Args:
        slug: project slug.
        facilitator: jméno fyzického facilitátora.
        votes: list[{ "name": "A", "builder": str,
                      "description": str, "diff_summary": {...} | str,
                      "prototype_url": str | None,
                      "role_preferences": [...] }].
                diff_summary (KROK 4.5 diff walkthrough) se persistuje do
                variants.diff_summary_md a vypíše v handoffu.
        decider_call: { shortlist, rationale, veto_register, parking_lot }.
        real_urls: optional dict[variant_name → real preview URL]. Bez URL se
                   NEdosazuje vymyšlená adresa: výstup má `prototype_url: None`
                   a varování, že zástupci v Asyncu variantu neuvidí. (DB sloupec
                   je NOT NULL, proto se bez URL ukládá prázdný řetězec `''`;
                   starší řádky s `sandbox.invalid` se berou stejně.)

    Returns session.persist result + `warnings`.
    """
    _validate_votes(slug, facilitator, votes, decider_call)
    real_urls = real_urls or {}

    with transaction() as conn:
        if not conn.execute("SELECT 1 FROM projects WHERE slug = ?", (slug,)).fetchone():
            raise ValueError(f"Projekt „{slug}“ neexistuje. Zkontroluj slug — "
                             "seznam projektů ukáže `pflanzer status`.")
        existing = {r[0]: r[1] for r in conn.execute(
            "SELECT v.name, v.prototype_url FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ?", (slug,)).fetchall()}

    spec_variants = []
    warnings: list[str] = []
    missing_urls: list[str] = []
    for v in votes:
        name = v.get("name") or v["variant"]
        url = real_urls.get(name) or v.get("prototype_url")
        if not url:
            kept = existing.get(name)
            if not kept or _is_no_url(kept):
                missing_urls.append(name)
            url = ""  # „bez URL“: DB sloupec je NOT NULL, proto prázdný řetězec (ne vymyšlená adresa)
        spec_variants.append({
            "name": name,
            "builder": v.get("builder") or "claude-code",
            "prototype_url": url,
            "description_md": v.get("description", ""),
            "diff_summary": v.get("diff_summary"),
            "role_preferences": v["role_preferences"],
        })

    for sv in spec_variants:
        w = _dead_local_url_warning(sv["prototype_url"], slug)
        if w:
            warnings.append(w)
    if len(missing_urls) == 1:
        warnings.append(f"varianta {missing_urls[0]} nemá preview URL — zástupci v Asyncu ji "
                        f"neuvidí (spusťte `pflanzer preview up --slug {slug}`: odkazy + heslo)")
    elif missing_urls:
        warnings.append(f"varianty {', '.join(missing_urls)} zatím nemají preview URL — "
                        f"zástupci v Asyncu je neuvidí (spusťte `pflanzer preview up --slug "
                        f"{slug}`: odkazy + heslo)")
    spec = {
        "slug": slug,
        "facilitator": facilitator,
        "decider_call": decider_call,
        "variants": spec_variants,
    }
    result = persist_session(spec)
    for pv in result.get("variants", []):
        if _is_no_url(str(pv.get("prototype_url") or "")):
            pv["prototype_url"] = None
    result["warnings"] = warnings
    shown = [f"{v['name']} {v['prototype_url']}" for v in result.get("variants", [])
             if v.get("prototype_url")]
    result["next_step"] = (
        (f"Async: pošli zástupcům odkazy na {'variantu' if len(shown) == 1 else 'varianty'} "
         f"({', '.join(shown)}) a dej jim {async_days(slug)}. "
         if shown else "Async: nejdřív doplň preview URL variant (viz varování), jinak je zástupci "
                       "neuvidí. ")
        + f"Pak `/pm feedback {slug}` a `/pm decide {slug}`."
    )
    return result


# --------------------------------------------------------------------------
# Handoff renderer — 1-page MD (kdo / co / do kdy / kill)
# --------------------------------------------------------------------------


def render_handoff(slug: str) -> str:
    """1-page handoff MD: actionable summary post-decision.

    Pulled fields:
    - Project (Charter): name, xyz, decider, kill_criteria, risk profile.
    - Latest Build row: variants + scores + commitment per role.
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
            raise ValueError(project_not_found_message(slug))
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
2. Async: **{async_days(proj[2])}** — zástupci klikají a komentují (hub nebo `pflanzer feedback add`).
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


BOOTSTRAP_EXAMPLE = """pflanzer quick_session bootstrap --spec .pflanzer/specs/moje-appka-kickoff.json
(soubor zapiš nástrojem Write; obsah:)
{"hook": "Rychlejší schvalování žádostí", "decider_name": "Dana Nováková",
 "risk_profile": "pilot", "metric": "10 z 15 lidí otevře přehled 3× týdně do 30 dnů",
 "path_owners": {"byznys": "Dana", "produkt": "Petr", "design": "AI", "vyvoj": "Tomáš",
                 "bezpecnost": "Jana", "provoz": "Karel"},
 "core": ["Petr", "Tomáš"], "session_mode": "parallel",
 "windows": {"Build": "st 21.10. 9:00-12:00", "Rozhodnutí": "pá 30.10. 10:00"}}"""


BOOTSTRAP_EPILOG = """Pole specu (JSON):
  povinné:   hook, decider_name, risk_profile (throwaway | pilot | production)
  nepovinné: slug, title (krátký název ≤ 50 znaků), metric, kill_criteria, tier (quick | lean | full), core [jména],
             path_owners {byznys, produkt, design, vyvoj, bezpecnost, provoz}
             (hodnota = jméno, nebo AI / AI:agent; ne u byznys a vývoj),
             ai_signers {bezpecnost|provoz|design|produkt: "jméno člověka, který AI draft
             podepíše"} — nebo zkráceně v path_owners: "AI:security-expert / Pavel Šnek",
             target_repo_url, target_repos, target_branch,
             session_mode (parallel = 3 varianty A/B/C, výchozí | mob = jedna společná varianta),
             windows {"Build": "st 21.10. 9:00-12:00", …} — okna z Kickoffu (ukáže je `status`)

Příklad:
""" + BOOTSTRAP_EXAMPLE

VOTE_EPILOG = """Pole specu (JSON):
  slug, facilitator, votes [{name, builder, description, prototype_url?,
  role_preferences [{role_idx, user_value, effort, risk, strategic_fit,
  commitment_level, rationale}]}], decider_call {shortlist, rationale,
  veto_register, parking_lot}, real_urls? {varianta: url}

Příklad:
""" + VOTE_EXAMPLE


def _bootstrap_from_spec(spec: dict[str, Any]) -> dict[str, Any]:
    required = {"hook": "jednovětý popis problému",
                "decider_name": "jméno Decidera",
                "risk_profile": "throwaway | pilot | production"}
    missing = [f"{k} ({why})" for k, why in required.items() if not spec.get(k)]
    if missing:
        raise ValueError("Ve specu chybí: " + "; ".join(missing) + f".\nPříklad:\n{BOOTSTRAP_EXAMPLE}")
    try:
        return bootstrap(**spec)
    except TypeError as exc:
        unknown = re.findall(r"unexpected keyword argument '(\w+)'", str(exc))
        if unknown:
            raise ValueError(f"Neznámé pole ve specu: {', '.join(unknown)}.\nPříklad:\n"
                             f"{BOOTSTRAP_EXAMPLE}") from exc
        raise


def _render_bootstrap(out: dict[str, Any], as_json: bool, spec: dict[str, Any]) -> None:
    owners = out.get("path_owners") or {}
    lines = [
        f"Projekt „{out['name']}“ je založen (`{out['slug']}`), stupeň "
        f"{TIER_LABELS.get(out.get('tier') or '', out.get('tier'))}.",
        f"Decider: {out['decider']}",
    ]
    if owners:
        lines.append("Kroky cesty: " + " · ".join(
            f"{label} {owner_display(owners[k], k)}" for k, label in PATH_STEPS.items()))
    if out.get("core"):
        lines.append("Jádro: " + ", ".join(out["core"]))
    if out.get("ai_stand_ins"):
        lines.append("AI náhrada: " + ", ".join(
            f"{a['label']} (AI {a['agent']}, {a['signer']})" if a["signer"].startswith("AI pre-check")
            else f"{a['label']} (AI {a['agent']}, podepisuje {a['signer']})"
            for a in out["ai_stand_ins"]))
    if out.get("windows"):
        lines.append("Okna: " + " · ".join(
            w["okno"] + (f" {w['kdy']}" if w.get("kdy") else "") for w in out["windows"]))
    if out.get("mode_note"):
        lines.append(out["mode_note"])
    if out.get("acceptance_feature_path"):
        lines.append(f"Akceptační scénáře: `{out['acceptance_feature_path']}`")
    if out.get("acceptance_commit_hint"):
        lines.append(out["acceptance_commit_hint"])
    metric = (spec.get("metric") or "")
    kill = (spec.get("kill_criteria") or "")
    ctx = {"metric_weak": not (metric and re.search(r"\d", metric)),
           "kill_weak": bool(kill) and not re.search(r"\d", kill),
           "ai_design": any(a["step"] == "design" for a in out.get("ai_stand_ins", [])),
           "ai_stand_ins": bool(out.get("ai_stand_ins"))}
    emit(out, title="Kickoff hotový", lines=lines, next_step=f"`{out['next_step']}`",
         tips=([] if as_json else tips_for_project(out["slug"], "kickoff", ctx)),
         warnings=out.get("warnings"), as_json=as_json)


def _render_prompts(out: dict[str, Any], as_json: bool) -> None:
    if out.get("blocked"):
        emit(out, title="Prompty zatím nejde připravit", lines=[out.get("reason", "")],
             next_step="vyřeš důvod výše a spusť příkaz znovu", as_json=as_json)
        return
    if as_json:
        emit(out, title="", as_json=True)
        return
    compact = bool(out.get("variant_heads")) and bool(out.get("common_text"))
    lines = ([] if compact else
             [f"Varianta {p['name']} — {p['angle']} ({p['builder']})" for p in out["prompts"]])
    if out.get("iterate_focus"):
        lines.append(f"Druhé kolo po Iterate — cíl tohoto kola: {out['iterate_focus']}")
    if out.get("variants_in_play"):
        lines.append("Staví se jen: " + ", ".join(out["variants_in_play"])
                     + " (ostatní varianty skončily)")
    if out.get("mode") == "mob":
        lines.append("Mob mode: jedna společná varianta `mob`, jedna větev a jeden worktree")
    if out.get("keyboard"):
        lines.append(f"U klávesnice: {out['keyboard']} (zástupce kroku Vývoj)")
    if out.get("stack"):
        lines.append(f"Stack target repa: {out.get('stack_label') or out['stack']}; kontroly po každém kroku: "
                     f"{', '.join(out['check_commands']) or 'viz README'}")
    emit(out, title="Prompty pro buildery", lines=lines,
         next_step=(("setup worktrees (jednou), pak dvojice" if out.get("setup_text")
                     else "dvojice") + ": `cd` do své varianty a do AI "
                    "společná pravidla + blok varianty" if compact else
                    "vlož každému dvojici jen blok „Vlož do AI“ (tisk níže), zbytek je pro facilitátora"),
         tips=tips_for_project(out["slug"], "build"), as_json=False)
    if compact:
        heads = [[ln for ln in pr["variant_head"].splitlines() if ln.strip()]
                 for pr in out["prompts"]]
        goal = heads[0][0] if heads and heads[0] else ""        # „Cíl týmu: …“ je pro všechny stejný
        rules = "\n".join(ln for ln in out["common_text"].splitlines() if ln.strip())
        if out.get("setup_text"):
            print(f"\n{out['setup_text']}")
        print("\n**Společná pravidla (do AI jako úvod; X = písmeno tvé varianty):**\n"
              f"```\n{goal}\n{rules}\n```")
        for pr, head in zip(out["prompts"], heads):
            cd = re.search(r"```bash\n(.*?)\n```", pr["facilitator_text"].split(
                "**Tvoje dvojice", 1)[-1], re.S)
            cmd = " && ".join(ln.split("#", 1)[0].strip() for ln in cd.group(1).splitlines()
                              if ln.split("#", 1)[0].strip()) if cd else ""
            own = head[1:] if head and head[0].startswith("Cíl týmu") else head
            print(f"\n**Varianta {pr['name']} — {pr['angle']}**: `{cmd}`\n"
                  "Do AI po pravidlech: " + "\n> ".join(own))
        if out.get("push_hint"):
            print(f"\n{out['push_hint']}")
        return
    for pr in out["prompts"]:
        print(f"\n---\n### Varianta {pr['name']} — {pr['angle']}\n\n"
              f"**Pro facilitátora:**\n\n{pr['facilitator_text']}\n\n"
              f"**Vlož do AI:**\n\n```\n{pr['ai_prompt']}\n```")
    if out.get("push_hint"):
        print(f"\n{out['push_hint']}")


def _tie_lines(variants: list[dict[str, Any]]) -> list[str]:
    """Shoda na čele (rozdíl do 0,01): hlasování nerozhodlo, rozhodne diskuse / Decider."""
    scored = [(v["name"], float(v["preference_score"])) for v in variants
              if v.get("preference_score") is not None]
    if len(scored) < 2:
        return []
    top = max(sc for _n, sc in scored)
    names = sorted(n for n, sc in scored if top - sc <= 0.01)
    if len(names) < 2:
        return []
    joined = ", ".join(names[:-1]) + f" a {names[-1]}"
    return [f"{joined} mají stejné skóre — rozhodne diskuse/Decider."]


def _render_vote(out: dict[str, Any], as_json: bool, slug: str) -> None:
    lines = []
    for v in sorted(out["variants"], key=lambda x: -(x["preference_score"] or 0)):
        url = v.get("prototype_url") or "bez preview URL"
        lines.append(f"Varianta {v['name']}: skóre {v['preference_score']:.2f} — {url}")
    lines.extend(_tie_lines(out["variants"]))
    emit(out, title="Hlasování zapsáno", lines=lines, next_step=out["next_step"],
         tips=([] if as_json else tips_for_project(
             slug, "after_vote", {("single_variant" if len(out["variants"]) == 1
                                   else "multi_variants"): True}, limit=2)),
         warnings=out.get("warnings"), as_json=as_json)


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer quick_session", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    spec_help = "JSON soubor (zapiš nástrojem Write; `-` čte stdin)"
    raw = argparse.RawDescriptionHelpFormatter
    p_boot = sub.add_parser(
        "bootstrap", help="Kickoff: Charter + role + jména kroků cesty + odložený triage",
        formatter_class=raw, epilog=BOOTSTRAP_EPILOG)
    p_boot.add_argument("--spec", required=True,
                        help=spec_help + ". Pole: {hook, decider_name, risk_profile, slug?, role_owners?, "
                             "metric?, kill_criteria?, path_owners?{byznys,produkt,design,vyvoj,bezpecnost,provoz; "
                             "hodnota jméno nebo AI / AI:agent [/ podepisující]}, ai_signers?{krok: jméno}, core?[], "
                             "target_repo_url?, target_repos? (list nebo 'fe=url#branch:workspace, be=url'), tier?, "
                             "session_mode? (parallel|mob), windows? {okno: termín}}")
    p_boot.add_argument("--json", action="store_true", help="Strojový výstup")

    p_prompts = sub.add_parser("prompts", help="Prompty pro buildery (Build)")
    p_prompts.add_argument("--slug", required=True)
    p_prompts.add_argument("--hook", default=None,
                           help="Problem statement; bez něj se vezme z projektu (Kickoff)")
    p_prompts.add_argument("--n", type=int, default=None,
                           help="Počet variant (default: 3, po Iterate jen ty, co pokračují; mob: Quick 1 kolo, jinak 2 iterace)")
    p_prompts.add_argument("--mode", choices=["parallel", "mob"], default=None,
                           help="parallel = 3 varianty paralelně; mob = jedna společná varianta "
                                "(ADR-0016). Default: režim uložený v projektu")
    p_prompts.add_argument("--prefer-hosted", action="store_true",
                           help="Opt-in pro Bolt/v0/Lovable (parallel only). Default = claude-code 3×.")
    p_prompts.add_argument("--json", action="store_true", help="Strojový výstup")

    p_vote = sub.add_parser("vote", help="Hlasování po Buildu + volba Decidera",
                            formatter_class=raw, epilog=VOTE_EPILOG)
    p_vote.add_argument("--spec", required=True, help=spec_help)
    p_vote.add_argument("--json", action="store_true", help="Strojový výstup")

    p_hand = sub.add_parser("handoff", help="Render 1-page handoff MD")
    p_hand.add_argument("--slug", required=True)
    p_hand.add_argument("--json", action="store_true", help="Strojový výstup")

    args = p.parse_args()

    try:
        if args.cmd == "bootstrap":
            spec = read_spec(args.spec, example=BOOTSTRAP_EXAMPLE)
            out = _bootstrap_from_spec(spec)
            _render_bootstrap(out, args.json, spec)
        elif args.cmd == "prompts":
            hook = args.hook or _hook_from_project(args.slug)
            out = builder_prompts(args.slug, hook, args.n,
                                  prefer_hosted=args.prefer_hosted,
                                  mode=args.mode)
            _render_prompts(out, args.json)
        elif args.cmd == "vote":
            spec = read_spec(args.spec, example=VOTE_EXAMPLE)
            spec = {k: v for k, v in spec.items() if not str(k).startswith("_")}  # `_napoveda`
            if "variants" in spec and "votes" not in spec:   # spec ve formátu session.persist
                spec["votes"] = spec.pop("variants")
            try:
                out = record_voting(**spec)
            except TypeError as exc:
                raise ValueError(f"Spec pro `vote` nesedí ({exc}).\nPříklad:\n{VOTE_EXAMPLE}") from exc
            _render_vote(out, args.json, spec.get("slug", ""))
        elif args.cmd == "handoff":
            path = write_handoff(args.slug)
            out = {"handoff_path": str(path), "preview": render_handoff(args.slug)[:400] + "…",
                   "next_step": f"/pm feedback {args.slug}"}
            emit(out, title="Handoff po Buildu je hotový",
                 lines=[f"Jednostránkový souhrn: `{path}`",
                        "Obsahuje: co děláme, varianty, kdo co dělá, kill kritéria, co dál."],
                 next_step=f"`/pm feedback {args.slug}` (Async {async_days(args.slug)})",
                 tips=([] if args.json else tips_for_project(args.slug, "async", limit=2)),
                 as_json=args.json)
        else:
            p.error(f"unknown cmd: {args.cmd}")
    except ValueError as e:
        die(str(e))


if __name__ == "__main__":
    main()
