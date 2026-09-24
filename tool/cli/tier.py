"""Pflanzer Method stupeň (tier): Quick / Lean / Full.

Single source for the tier values and for deriving a tier when none was given
explicitly. The tier drives Session 1 length, triage depth and the
between-session window (docs/methodology/00-lean-pflanzer.md § Tři stupně,
ADR-0021).
"""
from __future__ import annotations

from typing import Any

TIERS: tuple[str, ...] = ("quick", "lean", "full")
TIER_LABELS = {"quick": "Quick", "lean": "Lean", "full": "Full"}
# ADR-0021: working days between Session 1 and Session 2.
WINDOW_DAYS = {"quick": "3", "lean": "3–5", "full": "5–7"}


def validate_tier(tier: str, capacity_profile: str | None = None) -> str:
    """Return the normalised tier or raise ValueError."""
    t = (tier or "").strip().lower()
    if t not in TIERS:
        raise ValueError(f"tier must be one of {TIERS}, got '{tier}'.")
    if t == "quick" and capacity_profile == "audit-grade":
        raise ValueError(
            "tier='quick' nejde s capacity_profile='audit-grade' — audit-grade "
            "projekt potřebuje Full stupeň (4 triage tracks, okno 5–7 dní, ADR-0021)."
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
