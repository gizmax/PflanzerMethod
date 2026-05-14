"""Slice 5 — Builder decision (recommend vibe-coding tool per project).

Inputs come from Charter (data_class, ai_act_tier, throwaway_or_evolve) and
Platform Triage (sandbox URL + approved runtime list). Output is a ranked
shortlist of approved AI builders per `02-role-catalog.md` § Approved AI Tool
list and devil's advocate Útok 8 (sandbox + prompt audit).

Used by `/pflanzer-session-1` to seed the 1-3 paralelní variants. The
facilitator agent picks 1-3 from the shortlist (different builders =
different aesthetic / interaction biases per `04-session-1.md`).

Hard rules (veto):
- L4 data → no builder allowed (session blocked already by triage).
- AI Act `unacceptable` → blocked.
- Free tier vendors → excluded (Enterprise/Business only — Approved AI Tool list).
- `evolve` profil + brownfield → manual / cursor preferenced (AI builder
  jako prototyp je throw-away).
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

from tool.cli.db import transaction  # noqa: E402

# Approved builders — keep in sync with .claude/agents/security-triage.md
# § Approved AI Tool list and tool/db/schema.sql variants.builder CHECK.
APPROVED_BUILDERS: dict[str, dict[str, Any]] = {
    "v0": {
        "tier": "Team",
        "good_for": ["UI mockup", "marketing page", "design-system aware"],
        "weak_for": ["complex BE", "auth", "stateful flows"],
        "allows_export": True,
        "exportable_score": 0.85,  # GitHub export + copy-paste components
    },
    "bolt": {
        "tier": "Pro",
        "good_for": ["fullstack prototyp", "Node/Vite stacks", "rapid iteration"],
        "weak_for": ["regulated data", "complex SSO"],
        "allows_export": True,
        "exportable_score": 0.95,  # Full project download + GitHub push
    },
    "lovable": {
        "tier": "Team",
        "good_for": ["fullstack TS", "Supabase BE", "rapid"],
        "weak_for": ["custom infra", "no Supabase orgs"],
        "allows_export": True,
        "exportable_score": 0.90,  # GitHub sync built-in
    },
    "stitch": {
        "tier": "Pro",
        "good_for": ["mobile-first UI mockup", "design exploration"],
        "weak_for": ["functional logic", "BE"],
        "allows_export": False,
        "exportable_score": 0.20,  # Design only — žádný runnable kód
    },
    "cursor": {
        "tier": "Business",
        "good_for": ["brownfield", "evolve profil", "in-repo edits", "tests"],
        "weak_for": ["greenfield from scratch (slower)"],
        "allows_export": True,
        "exportable_score": 1.00,  # Code je už v repu — zero export friction
    },
    "figma-make": {
        "tier": "Enterprise",
        "good_for": ["design-tokens lock-in", "Figma-first orgs"],
        "weak_for": ["BE", "rapid pivots"],
        "allows_export": False,
        "exportable_score": 0.30,  # Design tokens, ne komponenty
    },
    "manual": {
        "tier": "n/a",
        "good_for": ["fallback when all builders excluded", "L3 data with veto"],
        "weak_for": ["speed"],
        "allows_export": True,
        "exportable_score": 0.70,  # Tým píše kód = vždy použitelný, ale pomalejší
    },
}


@dataclass(frozen=True)
class DecisionInput:
    slug: str
    data_class: str            # L1 | L2 | L3 | L4
    ai_act_tier: str           # minimal | limited | high | unacceptable
    throwaway_or_evolve: str   # throwaway | evolve
    has_sandbox: bool          # from platform triage
    stack_hint: str | None = None  # "react", "nextjs", "vue", "node-fastapi", ...
    customer_facing: bool = False
    production_target: int = 0  # 0..100; >0 = optimize pro reusable code (Slice production-path)


def _eligible(b: str, di: DecisionInput) -> tuple[bool, str | None]:
    """Hard veto rules. Returns (eligible, exclusion_reason_if_not)."""
    if di.data_class == "L4":
        return False, "L4 data — session blocked"
    if di.ai_act_tier == "unacceptable":
        return False, "AI Act unacceptable — session blocked"
    if not di.has_sandbox and b != "manual":
        return False, "No approved sandbox (devil's advocate Útok 8)"
    # evolve profil → AI builder výstup je stále throw-away,
    # ale cursor je přirozenější (in-repo). Builder se nezakazuje.
    return True, None


def _score(b: str, di: DecisionInput) -> float:
    """Simple suitability score 0..1."""
    meta = APPROVED_BUILDERS[b]
    score = 0.5

    if di.throwaway_or_evolve == "evolve":
        if b == "cursor":
            score += 0.35
        elif b in ("v0", "bolt", "lovable"):
            score += 0.10
        elif b == "manual":
            score += 0.20
    else:  # throwaway
        if b in ("v0", "bolt", "lovable"):
            score += 0.30
        elif b == "stitch" and di.customer_facing:
            score += 0.15
        elif b == "cursor":
            score += 0.10

    # stack-affinity hints (cheap heuristic)
    sh = (di.stack_hint or "").lower()
    if sh:
        if b == "lovable" and "supabase" in sh:
            score += 0.10
        if b == "v0" and ("nextjs" in sh or "next.js" in sh or "react" in sh):
            score += 0.10
        if b == "bolt" and ("vite" in sh or "node" in sh):
            score += 0.10
        if b == "figma-make" and ("figma" in sh or "tokens" in sh):
            score += 0.10

    # customer-facing → prefer builders s a11y-aware výstupem
    if di.customer_facing and b in ("v0", "lovable"):
        score += 0.05

    # Production-ready boost: pokud target > 0, weight exportable_score
    # ratio nepřímo úměrný targetu (target=100 → exportability je 30 % skóre).
    if di.production_target > 0:
        weight = min(0.30, di.production_target / 333)  # max 0.30 boost
        score += weight * meta["exportable_score"]

    return min(score, 1.0)


def recommend(di: DecisionInput, top_n: int = 3) -> dict[str, Any]:
    """Return ranked shortlist of approved builders.

    Output:
        {
          "blocked": bool,
          "blocked_reason": "..." | None,
          "shortlist": [{"builder": "v0", "score": 0.85, "rationale": "..."}, ...],
          "fallback": "manual"
        }
    """
    if di.data_class == "L4":
        return {
            "blocked": True,
            "blocked_reason": "L4 data classification — session se nekoná",
            "shortlist": [],
            "fallback": None,
        }
    if di.ai_act_tier == "unacceptable":
        return {
            "blocked": True,
            "blocked_reason": "AI Act unacceptable risk — session se nekoná",
            "shortlist": [],
            "fallback": None,
        }

    ranked: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for b in APPROVED_BUILDERS:
        ok, reason = _eligible(b, di)
        if not ok:
            excluded.append({"builder": b, "reason": reason})
            continue
        meta = APPROVED_BUILDERS[b]
        ranked.append({
            "builder": b,
            "score": round(_score(b, di), 3),
            "tier": meta["tier"],
            "good_for": meta["good_for"],
            "weak_for": meta["weak_for"],
            "allows_export": meta["allows_export"],
            "exportable_score": meta["exportable_score"],
        })

    ranked.sort(key=lambda r: r["score"], reverse=True)

    return {
        "blocked": False,
        "blocked_reason": None,
        "shortlist": ranked[:top_n],
        "excluded": excluded,
        "fallback": "manual",
        "diversity_hint": (
            "Vyber 1-3 builders s rozdílným stylem (např. v0 + bolt + cursor) "
            "aby varianty měly jiné aesthetic/interaction biasy "
            "(viz `docs/methodology/04-session-1.md` § AI vibe-coding kolo 1)."
        ),
    }


def recommend_for_slug(slug: str, stack_hint: str | None = None,
                       customer_facing: bool = False) -> dict[str, Any]:
    """Load Charter + platform triage from DB and recommend."""
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, data_class, ai_act_tier, throwaway_or_evolve, "
            "production_readiness_target "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        platform = conn.execute(
            "SELECT status FROM triage WHERE project_id = ? AND track = 'platform'",
            (proj[0],),
        ).fetchone()

    has_sandbox = bool(platform and platform[0] in ("ok", "deferred"))
    production_target = int(proj[4] or 0) if proj[3] == "evolve" else 0

    di = DecisionInput(
        slug=slug,
        data_class=proj[1] or "L2",
        ai_act_tier=proj[2] or "minimal",
        throwaway_or_evolve=proj[3] or "throwaway",
        has_sandbox=has_sandbox,
        stack_hint=stack_hint,
        customer_facing=customer_facing,
        production_target=production_target,
    )
    return recommend(di)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--stack-hint", default=None)
    p.add_argument("--customer-facing", action="store_true")
    args = p.parse_args()
    print(json.dumps(
        recommend_for_slug(args.slug, args.stack_hint, args.customer_facing),
        ensure_ascii=False, indent=2,
    ))


if __name__ == "__main__":
    main()
