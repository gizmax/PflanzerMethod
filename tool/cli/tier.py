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
             "bezpečnost se dohání před pilotem",
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
