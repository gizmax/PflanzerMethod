"""Pflanzer Method stupeň (tier): Quick / Lean / Full.

Single source for the tier values and for deriving a tier when none was given
explicitly. The tier drives Build length, triage depth and the
between-session window (docs/methodology/00-lean-pflanzer.md § Tři stupně,
ADR-0017).
"""
from __future__ import annotations

import difflib
from typing import Any

TIERS: tuple[str, ...] = ("quick", "lean", "full")
TIER_LABELS = {"quick": "Quick", "lean": "Lean", "full": "Full"}
# ADR-0017: working days between Build and Rozhodnutí.
WINDOW_DAYS = {"quick": "3", "lean": "3–5", "full": "5–7"}


# Mob Build: počet iterací podle stupně. Quick = 1 kolo × 30 min stavby
# (docs/methodology/00-lean-pflanzer.md § Tři stupně); Lean/Full 2 iterace (ADR-0016).
# Jediný zdroj pravdy pro prompty, worktree i status.
MOB_ITERATIONS = {"quick": 1, "lean": 2, "full": 2}
QUICK_BUILD_MINUTES = 30


RISK_PROFILE_NAMES: tuple[str, ...] = ("throwaway", "pilot", "production")

# Jedna otázka „Jak vážné to je?“: česká slova z Kickoffu -> kanonický risk profil.
RISK_PROFILE_ALIASES = {
    "demo": "throwaway", "prototyp": "throwaway", "zahodit": "throwaway",
    "ostre": "production", "ostré": "production", "ostry": "production",
    "ostrý": "production", "ostra": "production", "produkce": "production",
}
SENSITIVE_DATA_CLASSES = ("L3", "L4")
PRODUCTION_MIN_LEAN = "Ostré nasazení = minimálně Lean"


def normalize_risk_profile(value: Any) -> str | None:
    """`throwaway|pilot|production` nebo česky `demo|pilot|ostre`; neznámé -> None."""
    v = str(value or "").strip().lower()
    v = RISK_PROFILE_ALIASES.get(v, v)
    return v if v in RISK_PROFILE_NAMES else None


def is_sensitive(*, personal_data: Any = None, data_class: str | None = None,
                 ai_act_tier: str | None = None) -> bool:
    """Osobní data / citlivá třída dat / AI Act high+ -> projekt potřebuje i právo (Full u ostrého)."""
    if personal_data in (True, 1) or str(personal_data).strip().lower() in ("true", "ano", "yes", "1"):
        return True
    if str(data_class or "").strip().upper() in SENSITIVE_DATA_CLASSES:
        return True
    return str(ai_act_tier or "").strip().lower() in ("high", "unacceptable")


def derive_tier(risk_profile: str, *, sensitive: bool = False) -> tuple[str, str]:
    """Stupeň z odpovědi „Jak vážné to je?“ a věta, proč (+ jak přebít).

    throwaway -> quick, pilot -> lean, production -> lean; production + osobní data /
    regulované -> full. Explicitní `tier` ve specu tohle přebíjí.
    """
    if risk_profile == "throwaway":
        t, why = "quick", "demo, které nejde k uživatelům"
    elif risk_profile == "pilot":
        t, why = "lean", "pilot s reálnými uživateli"
    elif sensitive:
        t, why = "full", "ostré nasazení s osobními daty / regulovaným obsahem"
    else:
        t, why = "lean", "ostré nasazení"
    return t, (f"Stupeň {TIER_LABELS[t]} jsem odvodil z odpovědi „jak vážné to je“: {why}. "
               "Chcete jiný? Přidejte `tier` (quick|lean|full).")


def window_label(tier: str) -> str:
    """Czech days wording of the between-session window: "3 dny" / "3–5 dní" / "5–7 dní"."""
    days = WINDOW_DAYS[tier]
    return f"{days} dny" if days == "3" else f"{days} dní"


def validate_tier(tier: str, capacity_profile: str | None = None) -> str:
    """Return the normalised tier or raise ValueError (Czech, human sentence)."""
    t = (tier or "").strip().lower()
    if t not in TIERS:
        if t in RISK_PROFILE_NAMES:
            raise ValueError(
                f"‚{t}‘ je risk profil (throwaway|pilot|production), ne stupeň. "
                "Stupeň: quick|lean|full (pilot má výchozí lean).")
        near = difflib.get_close_matches(t, TIERS, n=1, cutoff=0.6)
        hint = f" Myslel jste ‚{near[0]}‘?" if near else ""
        raise ValueError(f"Neznámý stupeň ‚{tier}‘.{hint} Stupeň: quick|lean|full "
                         "(risk profil throwaway|pilot|production se zadává zvlášť).")
    if t == "quick" and capacity_profile == "audit-grade":
        raise ValueError(
            "tier='quick' nejde s capacity_profile='audit-grade' — audit-grade "
            "projekt potřebuje Full stupeň (4 triage tracks, okno 5–7 dní, ADR-0017)."
        )
    return t


def default_tier(capacity_profile: str | None, *, quick_bootstrap: bool = False,
                 risk_profile: str | None = None) -> str:
    """Tier used when the caller did not choose one.

    audit-grade -> Full. The in-room `/pm live` wizard -> Quick, except the
    `production` risk profile, which the tier table upgrades to Lean.
    Everything else -> Lean (the Track P default).
    """
    if capacity_profile == "audit-grade":
        return "full"
    if quick_bootstrap and risk_profile != "production":
        return "quick"
    return "lean"


def infer_tier(conn: Any, project_id: int, capacity_profile: str | None) -> str:
    """Best-effort tier for projects created before `projects.tier` existed."""
    quick = conn.execute(
        "SELECT 1 FROM audit_log WHERE action = 'quick.bootstrap' "
        "AND target_type = 'project' AND target_id = ? LIMIT 1",
        (project_id,),
    ).fetchone()
    # Legacy quick bootstrap stored `production` as capacity_profile='regulated'.
    risk = "production" if capacity_profile == "regulated" else None
    return default_tier(capacity_profile, quick_bootstrap=bool(quick), risk_profile=risk)


def project_tier(slug: str) -> str:
    """Stupeň projektu z DB (`projects.tier`), jinak odvozený; neznámý projekt -> lean."""
    try:
        from tool.cli.db import transaction
        with transaction() as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()}
            sel = "id, capacity_profile" + (", tier" if "tier" in cols else "")
            row = conn.execute(f"SELECT {sel} FROM projects WHERE slug = ?", (slug,)).fetchone()
            if not row:
                return "lean"
            if len(row) > 2 and row[2] in TIERS:
                return str(row[2])
            return infer_tier(conn, int(row[0]), row[1])
    except Exception:  # noqa: BLE001 — poradní údaj, nikdy neshodí příkaz
        return "lean"


TIER_MEANING = {
    "quick": "rychlé ověření směru, Kickoff + Build v jednom (60–90 min), `/pm live`; "
             "bez triage a oken, před pilotem nový Kickoff",
    "lean": "výchozí: Build 3 h, checkpoint bezpečnosti 20 min, `/pm start` → `/pm build`",
    "full": "regulované / governance: Build 5–6 h, 4 triage tracky povinné, "
            "`/pm roles` → `/pm triage` → `/pm build`",
}


def overview() -> str:
    """Human overview of the three tiers (what `pflanzer tier` prints)."""
    rows = [f"- {TIER_LABELS[t]} (`{t}`) — okno {window_label(t)} mezi Buildem a Rozhodnutím; "
            f"{TIER_MEANING[t]}" for t in TIERS]
    return ("**Pflanzer Method | pflanzer.cz/method**\n\nStupně metody:\n\n" + "\n".join(rows)
            + "\n\nStupeň se volí při Kickoffu (`--tier quick|lean|full`); "
              "aktuální stupeň projektu ukáže `pflanzer status --slug <slug>`.")


def main() -> None:
    print(overview())


if __name__ == "__main__":
    main()
