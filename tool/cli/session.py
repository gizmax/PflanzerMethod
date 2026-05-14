"""Slice 5 — Session 1 persistence layer.

The Claude Code orchestrator (`/pflanzer-session-1`) calls this module with a
JSON spec built from facilitator + role-expert sub-agent outputs. We:

1. Validate project status (must be 'triage' = pre-flight passed).
2. Open / reuse session row (type=1).
3. Persist 1-3 variants + per-role preference matrix.
4. Compute aggregate variant.preference_score with AI-only deflation
   (max 0.5 per `04-session-1.md` § Score závaznosti, synthesis 02).
5. Append decision row (type='preference') with Decider attribution.
6. Render `_summary.md` with shortlist + commitment levels per role.
7. Move project status to 'session_1'.

Web hub push (POST /api/projects/{slug}/variants) is done by the slash command
after this module persists locally — keeps DB the source of truth, web hub
is a read replica per ADR-0008 (Hybrid form-factor).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

SESSIONS_DIR = REPO_ROOT / "data" / "sessions"
ALLOWED_BUILDERS = {"claude-code", "codex-cli", "v0", "bolt", "lovable",
                    "stitch", "cursor", "figma-make", "manual"}
PREFERENCE_DIMS = ("user_value", "effort", "risk", "strategic_fit")

# AI-only deflation cap per role-catalog v0.2 (#14) + synthesis 02:
# AI-only persona feedback score deflated max 0.5.
AI_ONLY_CAP = 0.5


# --------------------------------------------------------------------------
# Aggregation helpers
# --------------------------------------------------------------------------


def _normalize(value: float | None) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def _aggregate_variant_score(
    role_prefs: list[dict[str, Any]],
    role_meta: dict[int, dict[str, Any]],
) -> float:
    """Compute variant aggregate preference 0..1.

    Per 04-session-1.md § Score závaznosti:
    - 4 dimenze (user_value, effort_inv, risk_inv, strategic_fit) → unweighted mean.
    - effort and risk are inverted (lower = better).
    - mandatory roles weight = 1.5, recommended = 1.0, optional = 0.5.
    - is_ai_only or role.ai_proxy_mode='mode_3' (AI-only fallback) → cap 0.5.
    """
    if not role_prefs:
        return 0.0

    total_weighted = 0.0
    total_weight = 0.0
    for rp in role_prefs:
        role = role_meta.get(rp["role_id"], {})
        status = role.get("status", "recommended")
        weight = {"mandatory": 1.5, "recommended": 1.0, "optional": 0.5}.get(status, 1.0)

        dims = []
        if (uv := _normalize(rp.get("user_value"))) is not None:
            dims.append(uv)
        if (ef := _normalize(rp.get("effort"))) is not None:
            dims.append(1.0 - ef)
        if (rk := _normalize(rp.get("risk"))) is not None:
            dims.append(1.0 - rk)
        if (sf := _normalize(rp.get("strategic_fit"))) is not None:
            dims.append(sf)

        if not dims:
            continue
        score = sum(dims) / len(dims)

        ai_only = bool(rp.get("is_ai_only")) or role.get("ai_proxy_mode") == "mode_3"
        if ai_only:
            score = min(score, AI_ONLY_CAP)

        total_weighted += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0
    return round(total_weighted / total_weight, 4)


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------


def _validate_spec(spec: dict[str, Any]) -> None:
    if "slug" not in spec:
        raise ValueError("spec missing 'slug'")
    variants = spec.get("variants") or []
    if not (1 <= len(variants) <= 3):
        raise ValueError(f"Session 1 musí mít 1-3 varianty, got {len(variants)}")
    seen_names: set[str] = set()
    for v in variants:
        for k in ("name", "builder", "prototype_url"):
            if not v.get(k):
                raise ValueError(f"variant missing '{k}': {v}")
        if v["builder"] not in ALLOWED_BUILDERS:
            raise ValueError(f"unknown builder '{v['builder']}' (variant {v['name']})")
        if v["name"] in seen_names:
            raise ValueError(f"duplicate variant name '{v['name']}'")
        seen_names.add(v["name"])
        for rp in v.get("role_preferences", []):
            if not rp.get("rationale"):
                raise ValueError(
                    f"role_preferences row for variant '{v['name']}' missing rationale "
                    "(POVINNÉ per 04-session-1.md § Score závaznosti)"
                )


def persist(spec: dict[str, Any]) -> dict[str, Any]:
    """Persist Session 1 outputs.

    Spec format:
        {
          "slug": "demo-widget",
          "facilitator": "Jan Novák",
          "decider_call": {
            "shortlist": ["A", "B"],
            "rationale": "...",
            "veto_register": ["..."],
            "parking_lot": ["..."]
          },
          "variants": [
            {
              "name": "A",
              "builder": "v0",
              "prototype_url": "https://v0.app/.../preview",
              "description_md": "...",
              "ost_node": "...",
              "throwaway_or_evolve": "throwaway",
              "role_preferences": [
                {
                  "role_idx": 1,            # catalog_idx 1..18
                  "user_value": 0.8,
                  "effort": 0.3,
                  "risk": 0.2,
                  "strategic_fit": 0.9,
                  "commitment_level": 3,
                  "rationale": "POVINNÉ — 1-2 věty proč",
                  "is_ai_only": false
                }
              ]
            }
          ]
        }
    """
    _validate_spec(spec)

    slug = spec["slug"]
    facilitator = spec.get("facilitator") or current_actor()
    decider_call = spec.get("decider_call", {})

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = SESSIONS_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status = int(proj[0]), proj[1]
        if status not in ("triage", "session_1"):
            raise ValueError(
                f"Project status='{status}'. Session 1 vyžaduje 'triage' "
                "(spusť `/pflanzer-triage {slug}` nejdřív)."
            )

        # Role lookup: catalog_idx → role row metadata
        role_rows = conn.execute(
            "SELECT id, catalog_idx, catalog_label, status, ai_proxy_mode "
            "FROM roles WHERE project_id = ?",
            (project_id,),
        ).fetchall()
        if not role_rows:
            raise ValueError(
                "Žádné role v DB. Spusť `/pflanzer-roles {slug}` nejdřív."
            )
        idx_to_role: dict[int, dict[str, Any]] = {
            r[1]: {"id": r[0], "label": r[2], "status": r[3], "ai_proxy_mode": r[4]}
            for r in role_rows
        }

        # Find or create Session 1 row
        sess = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1",
            (project_id,),
        ).fetchone()
        if sess:
            session_id = int(sess[0])
            # Reset variants for re-run idempotency
            conn.execute(
                "DELETE FROM variants WHERE session_id = ?", (session_id,),
            )
        else:
            cur = conn.execute(
                "INSERT INTO sessions (project_id, type, starts_at, decision) "
                "VALUES (?, 1, ?, 'pending')",
                (project_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            session_id = cur.lastrowid

        # Persist variants + role_preferences
        persisted_variants: list[dict[str, Any]] = []
        for v in spec["variants"]:
            role_prefs_raw = v.get("role_preferences", [])
            # resolve role_idx → role_id; warn on missing
            resolved: list[dict[str, Any]] = []
            for rp in role_prefs_raw:
                role = idx_to_role.get(int(rp["role_idx"]))
                if not role:
                    # Role not in this project's mix → skip (with note)
                    continue
                resolved.append({
                    "role_id": role["id"],
                    "user_value": _normalize(rp.get("user_value")),
                    "effort": _normalize(rp.get("effort")),
                    "risk": _normalize(rp.get("risk")),
                    "strategic_fit": _normalize(rp.get("strategic_fit")),
                    "commitment_level": rp.get("commitment_level"),
                    "rationale": rp["rationale"],
                    "is_ai_only": 1 if rp.get("is_ai_only") else 0,
                })

            # Aggregate score with AI-only deflation
            role_meta_by_id = {r["id"]: r for r in idx_to_role.values()}
            agg_score = _aggregate_variant_score(resolved, role_meta_by_id)

            cur = conn.execute(
                """
                INSERT INTO variants (
                    session_id, name, builder, prototype_url,
                    description_md, preference_score
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id, v["name"], v["builder"], v["prototype_url"],
                    v.get("description_md"), agg_score,
                ),
            )
            variant_id = cur.lastrowid

            for rp in resolved:
                conn.execute(
                    """
                    INSERT INTO role_preferences (
                        variant_id, role_id,
                        user_value, effort, risk, strategic_fit,
                        commitment_level, rationale, is_ai_only
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        variant_id, rp["role_id"],
                        rp["user_value"], rp["effort"], rp["risk"], rp["strategic_fit"],
                        rp["commitment_level"], rp["rationale"], rp["is_ai_only"],
                    ),
                )

            persisted_variants.append({
                "id": variant_id, "name": v["name"], "builder": v["builder"],
                "prototype_url": v["prototype_url"],
                "preference_score": agg_score,
                "description_md": v.get("description_md"),
                "role_preferences": resolved,
            })

        # Decision row — Decider's call shortlist
        if decider_call:
            decision_md = render_decision_md(spec, persisted_variants, idx_to_role)
            conn.execute(
                """
                INSERT INTO decisions (
                    project_id, type, body_md, atribuce_user, atribuce_ts
                ) VALUES (?, 'preference', ?, ?, CURRENT_TIMESTAMP)
                """,
                (project_id, decision_md, current_actor()),
            )

        # Move project status forward
        conn.execute(
            "UPDATE projects SET status = 'session_1', updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            (project_id,),
        )

        audit(
            conn,
            action="session_1.persist",
            target_type="session",
            target_id=session_id,
            payload={
                "slug": slug,
                "variants": [v["name"] for v in persisted_variants],
                "facilitator": facilitator,
                "shortlist": decider_call.get("shortlist", []),
            },
        )

    summary_md = render_summary_md(slug, project_id, session_id, spec, persisted_variants, idx_to_role)
    summary_path = project_dir / "_summary.md"
    summary_path.write_text(summary_md, encoding="utf-8")

    return {
        "project_id": project_id,
        "session_id": session_id,
        "slug": slug,
        "variants": persisted_variants,
        "summary_path": str(summary_path),
        "next_step": (
            f"Push variants do web hubu: `POST /api/projects/{slug}/variants` per variant. "
            f"Pak: `/pflanzer-feedback-pull {slug}` (Slice 6) po sebrání feedbacku."
        ),
    }


# --------------------------------------------------------------------------
# Renderers
# --------------------------------------------------------------------------


def render_summary_md(
    slug: str, project_id: int, session_id: int,
    spec: dict[str, Any], variants: list[dict[str, Any]],
    idx_to_role: dict[int, dict[str, Any]],
) -> str:
    decider_call = spec.get("decider_call", {})
    shortlist = decider_call.get("shortlist", [])

    var_table = "\n".join(
        f"| {v['name']} | `{v['builder']}` | {v['preference_score']:.2f} | "
        f"{'✅ shortlist' if v['name'] in shortlist else '—'} | "
        f"[preview]({v['prototype_url']}) |"
        for v in variants
    )

    # Per-variant role matrix
    matrix_blocks = []
    role_id_to_label = {r["id"]: r["label"] for r in idx_to_role.values()}
    for v in variants:
        rows = []
        for rp in v["role_preferences"]:
            label = role_id_to_label.get(rp["role_id"], f"role_id={rp['role_id']}")
            ai_flag = " (AI-only, capped 0.5)" if rp["is_ai_only"] else ""
            rows.append(
                f"| {label}{ai_flag} | "
                f"{_fmt(rp['user_value'])} | {_fmt(rp['effort'])} | "
                f"{_fmt(rp['risk'])} | {_fmt(rp['strategic_fit'])} | "
                f"{rp['commitment_level'] if rp['commitment_level'] is not None else '—'} | "
                f"{rp['rationale']} |"
            )
        matrix_blocks.append(
            f"### Variant {v['name']} — preference matrix\n\n"
            f"| Role | UV | Effort | Risk | StratFit | Commit | Rationale |\n"
            f"|------|----|--------|------|----------|--------|-----------|\n"
            + "\n".join(rows)
        )

    veto_section = ""
    if decider_call.get("veto_register"):
        veto_section = (
            "\n## Veto registr\n\n"
            + "\n".join(f"- {x}" for x in decider_call["veto_register"]) + "\n"
        )

    parking = decider_call.get("parking_lot") or []
    parking_section = ""
    if parking:
        parking_section = (
            "\n## Parking lot\n\n"
            + "\n".join(f"- {x}" for x in parking) + "\n"
        )

    return f"""# Session 1 — {slug}

> Project ID: {project_id} · Session ID: {session_id}
> Facilitator: {spec.get('facilitator', '—')}
> Per `docs/methodology/04-session-1.md`.

## Varianty

| Variant | Builder | Score (agg) | Shortlist | Preview |
|---------|---------|-------------|-----------|---------|
{var_table}

> Score = unweighted mean (user_value, 1-effort, 1-risk, strategic_fit) per role,
> weighted (mandatory ×1.5, recommended ×1.0, optional ×0.5),
> AI-only persona deflated max {AI_ONLY_CAP} (synthesis 02).

## Decider's call

- **Shortlist**: {', '.join(shortlist) if shortlist else '— (Decider call missing)'}
- **Rationale**: {decider_call.get('rationale', '—')}
{veto_section}{parking_section}
{chr(10).join(matrix_blocks)}

## Next step

1. Push variants do web hubu (`POST /api/projects/{slug}/variants` per variant).
2. Sběr feedbacku v scoring window (5-7 pracovních dní).
3. `/pflanzer-feedback-pull {slug}` (Slice 6) → pull feedbacku do DB.
4. `/pflanzer-session-2 {slug}` (Slice 7) → decisional session.
"""


def render_decision_md(
    spec: dict[str, Any], variants: list[dict[str, Any]],
    idx_to_role: dict[int, dict[str, Any]],
) -> str:
    decider_call = spec.get("decider_call", {})
    shortlist = decider_call.get("shortlist", [])
    return f"""## Session 1 — Decider's preference call

- Shortlist (1-3 variant): **{', '.join(shortlist) or '—'}**
- Rationale: {decider_call.get('rationale', '—')}
- Veto registr: {len(decider_call.get('veto_register') or [])} items
- Parking lot: {len(decider_call.get('parking_lot') or [])} items

### Per-variant aggregate score

{chr(10).join(f"- **{v['name']}** (`{v['builder']}`) → {v['preference_score']:.2f}" for v in variants)}

Atribuce: {current_actor()} · {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z
"""


def _fmt(x: float | None) -> str:
    return f"{x:.2f}" if x is not None else "—"


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def run_from_json(path: Path) -> dict[str, Any]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    return persist(spec)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--spec", type=Path, required=True,
                   help="JSON spec with slug + variants + role_preferences")
    args = p.parse_args()
    print(json.dumps(run_from_json(args.spec), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
