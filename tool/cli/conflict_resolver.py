"""Slice 7 — Conflict resolver pro Session 2.

Detekuje konflikty v posbíraném feedbacku a páruje je s navrhovanými
resolutions z `docs/research/synthesis/01-conflict-matrix.md`. Heuristic-based
(žádný LLM) — vstup je deterministický, output je transparent pro Decider.

Algoritmus:
1. Načti všechny feedback rows per project (přes feedback_pull.aggregate).
2. Group by (variant, role/department) → score divergence per variant.
3. Pokud 2 role mají score divergence > THRESHOLD na stejnou variantu →
   pravděpodobný konflikt.
4. Pro každý konflikt vyhledej v conflict_matrix odpovídající dvojici a vrať
   suggested resolution + ADR reference.

Pokud nenajde match v matrix → flagne jako "unmapped conflict" pro lidský
review (může to být novel kombinace, kterou stojí za to přidat do role catalogu).
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
from tool.cli.feedback_pull import aggregate as pull_aggregate  # noqa: E402

# Score divergence threshold pro označení konfliktu
DIVERGENCE_THRESHOLD = 0.3

# Conflict matrix subset — top dvojice z synthesis/01-conflict-matrix.md
# Klíč: frozenset((role_idx_A, role_idx_B)). Value: rozhodnutí + ADR.
CONFLICT_RESOLUTIONS: dict[frozenset, dict[str, str]] = {
    frozenset({1, 7}): {
        "axis": "Datová třída sandboxu (live integrace vs synthetic-only)",
        "resolution": "Pre-charter Data Classification Statement podepsaný DPO před session 1; L4 = session se nekoná.",
        "adr": "ADR-0002 (Pre-flight triage tracks)",
    },
    frozenset({1, 9}): {
        "axis": "Kapacita Q3 vs business urgency",
        "resolution": "Capacity pre-sign-off jako vstup; pokud kapacita zmizí, aktivuje se champion v jiné BU.",
        "adr": "ADR-0006 (Champion provisioning)",
    },
    frozenset({1, 4}): {
        "axis": "Prototyp do prod (throw-away vs evolve)",
        "resolution": "Evolve default v Charteru (ADR-0005 v0.4); prod deploy až po Ship gate (quality gates >= 80/100) + sign-off FE + EM + Security + DPO + DevOps + QA P2P. Throw-away jen jako explicit opt-in s rationale.",
        "adr": "ADR-0005 v0.4 (Track x Output: evolve default)",
    },
    frozenset({1, 5}): {
        "axis": "Vibe-coding speed vs migrace timeline",
        "resolution": "Score závaznosti BE = schválím contract, ne líbí se mi UI; T-shirt v session, story-point až po 2-day spiku.",
        "adr": None,
    },
    frozenset({1, 6}): {
        "axis": "Speed vs research rigor",
        "resolution": "XYZ hypotéza jako falsifikovatelný marker; persona ownership shared (PM + UX podpisují před session).",
        "adr": "ADR-0004 (Business Charter)",
    },
    frozenset({1, 13}): {
        "axis": "Ticket impact a support cost",
        "resolution": "Support cost line item v business case; D-2 readiness checklist jako merge-blocker.",
        "adr": None,
    },
    frozenset({1, 12}): {
        "axis": "Dashboard vs measurement plan",
        "resolution": "Measurement plan jako součást DoD; bez něj není ship. Consent + power analysis pre-read.",
        "adr": None,
    },
    frozenset({2, 6}): {
        "axis": "Persona ownership (prioritization vs flow)",
        "resolution": "Shared artefakt; PM tie-breaker na scope, UX na flow. Persona doc podepsaný oběma před session.",
        "adr": None,
    },
    frozenset({2, 7}): {
        "axis": "Veto-late vs feature scope",
        "resolution": "Pre-charter triage 80 % pokrývá; on-call slot v session; eskalace pro 20 %.",
        "adr": "ADR-0002",
    },
    frozenset({2, 5}): {
        "axis": "Pole navíc v UI vs schema migration",
        "resolution": "Breaking-change registr s explicit ownership; každá UI změna kontrola proti consumer ownerům.",
        "adr": None,
    },
    frozenset({2, 13}): {
        "axis": "Interpretace pain (PM vs CS)",
        "resolution": "VoC ritual prvních 30 min Session 1; ticket data jako vstup, ne názor jako rozhodnutí.",
        "adr": None,
    },
    frozenset({2, 12}): {
        "axis": "Outcome vs output",
        "resolution": "Measurement v DoD; PM + Analytics interlock — PM definuje outcome, Analytics měřitelný proxy.",
        "adr": None,
    },
    frozenset({2, 14}): {
        "axis": "Discovery vs delivery",
        "resolution": "Discovery Readiness Gate povinný; persona < 6 měsíců, 5+ rozhovorů, OST v0 ≥ 60 %.",
        "adr": "ADR-0002 (Krok 0)",
    },
    frozenset({4, 5}): {
        "axis": "Rychlost vs contract",
        "resolution": "Contract-first: BE shadow agent generuje OpenAPI paralelně s UI generátorem (side-by-side).",
        "adr": None,
    },
    frozenset({4, 6}): {
        "axis": "Komponentní rozhodování (DS deviations)",
        "resolution": "DS steward s veto na nové komponenty; tokens jako MCP context do builderu, every deviation logována.",
        "adr": None,
    },
    frozenset({4, 11}): {
        "axis": "A11y stav generovaného kódu",
        "resolution": "A11y quickscan + axe-core jako Session 1 gate; expert v místnosti od minuty 0, ne post-hoc.",
        "adr": None,
    },
    frozenset({5, 15}): {
        "axis": "SLO/SLA ownership",
        "resolution": "SLO Quick-Set library a sdílený footprint estimate; SLO = sdílený artefakt, ne overlap.",
        "adr": None,
    },
    frozenset({7, 10}): {
        "axis": "AI Act high-risk interpretation",
        "resolution": "Společný triage protokol (Krok 0a — Security & Legal Triage) s pre-approved templates; oba podepisují charter.",
        "adr": "ADR-0002",
    },
    frozenset({7, 15}): {
        "axis": "Sandbox deploy hranice",
        "resolution": "Sandbox spec jako sdílený Terraform modul (Security guardrails + Platform lifecycle).",
        "adr": "ADR-0002",
    },
    frozenset({9, 6}): {
        "axis": "Kapacita vs UX kvalita",
        "resolution": "UX dostává viditelný warning v rozhodovací matici (ne veto, ale signal vs rychlejší = lepší).",
        "adr": None,
    },
    frozenset({9, 5}): {
        "axis": "Effort estimate v rapid contextu",
        "resolution": "Dvoufázový estimate: T-shirt v session, story-point až po 2-day capped spike.",
        "adr": None,
    },
    frozenset({13, 6}): {
        "axis": "Happy path vs unhappy path",
        "resolution": "Top-3 predikované tickety = P1 v acceptance criteria; error states povinné v každé variantě.",
        "adr": None,
    },
    frozenset({12, 7}): {
        "axis": "PII v event taxonomy",
        "resolution": "Privacy classification dat jako vstup; PII NIKDY v event name/property; server-side pro essential.",
        "adr": None,
    },
    frozenset({12, 10}): {
        "axis": "PII v event taxonomy",
        "resolution": "Privacy classification dat jako vstup; PII NIKDY v event name/property; server-side pro essential.",
        "adr": None,
    },
    frozenset({14, 1}): {
        "axis": "AI persona jako náhrada research",
        "resolution": "Score deflation: AI-only persona feedback max 0.5 z 1.0; AI persona = vstup do session, ne výstup.",
        "adr": None,
    },
    frozenset({14, 2}): {
        "axis": "AI persona jako náhrada research",
        "resolution": "Score deflation: AI-only persona feedback max 0.5 z 1.0; AI persona = vstup do session, ne výstup.",
        "adr": None,
    },
}


@dataclass
class Conflict:
    variant: str
    role_a_idx: int | None
    role_a_label: str
    role_b_idx: int | None
    role_b_label: str
    score_a: float
    score_b: float
    divergence: float
    resolution: dict[str, str] | None  # None = unmapped


def _role_idx_from_label(label: str, role_map: dict[str, int]) -> int | None:
    """Best-effort lookup catalog_idx z department label."""
    label_norm = (label or "").strip().lower()
    for k, v in role_map.items():
        if k.lower() == label_norm:
            return v
    # fuzzy: substring match
    for k, v in role_map.items():
        if label_norm and label_norm in k.lower():
            return v
    return None


def detect_conflicts(slug: str) -> dict[str, Any]:
    """Detect role-vs-role conflicts ve feedbacku."""
    agg = pull_aggregate(slug)

    # Build role label → catalog_idx lookup
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        rows = conn.execute(
            "SELECT catalog_idx, catalog_label FROM roles WHERE project_id = ?",
            (proj[0],),
        ).fetchall()
    role_map: dict[str, int] = {r[1]: int(r[0]) for r in rows}

    # Group feedback rows by variant, then by department
    by_variant: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for fb in agg["raw_feedback"]:
        v = fb["variant_name"]
        d = fb["department"]
        by_variant.setdefault(v, {}).setdefault(d, []).append(fb)

    # For each variant, look at all department pairs. If avg score diverges > threshold,
    # it's a candidate conflict.
    conflicts: list[Conflict] = []
    for variant, depts in by_variant.items():
        dept_avg = {
            d: sum(f["score"] for f in fbs) / len(fbs)
            for d, fbs in depts.items()
        }
        labels = list(dept_avg.keys())
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                la, lb = labels[i], labels[j]
                divergence = abs(dept_avg[la] - dept_avg[lb])
                if divergence < DIVERGENCE_THRESHOLD:
                    continue
                idx_a = _role_idx_from_label(la, role_map)
                idx_b = _role_idx_from_label(lb, role_map)
                resolution = None
                if idx_a is not None and idx_b is not None:
                    resolution = CONFLICT_RESOLUTIONS.get(frozenset({idx_a, idx_b}))
                conflicts.append(Conflict(
                    variant=variant,
                    role_a_idx=idx_a, role_a_label=la,
                    role_b_idx=idx_b, role_b_label=lb,
                    score_a=round(dept_avg[la], 3),
                    score_b=round(dept_avg[lb], 3),
                    divergence=round(divergence, 3),
                    resolution=resolution,
                ))

    # Sort by divergence DESC (largest disagreement first)
    conflicts.sort(key=lambda c: -c.divergence)

    return {
        "slug": slug,
        "feedback_count": agg["feedback_count"],
        "conflicts_detected": len(conflicts),
        "top_conflicts": [_conflict_to_dict(c) for c in conflicts[:10]],
        "unmapped_count": sum(1 for c in conflicts if c.resolution is None),
        "critical_flags_passthrough": agg["critical_flags"],
    }


def _conflict_to_dict(c: Conflict) -> dict[str, Any]:
    return {
        "variant": c.variant,
        "role_a": {"idx": c.role_a_idx, "label": c.role_a_label, "score": c.score_a},
        "role_b": {"idx": c.role_b_idx, "label": c.role_b_label, "score": c.score_b},
        "divergence": c.divergence,
        "resolution": c.resolution,  # None = unmapped, requires human review
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    args = p.parse_args()
    print(json.dumps(detect_conflicts(args.slug), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
