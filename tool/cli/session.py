"""Build — persistence vrstva (v0.5; DB `sessions.type = 1`).

Orchestrátor Buildu (`/pm build`, `/pm live`) volá tento modul s JSON specem
(facilitátor + hlasy zástupců kroků cesty). Modul:

1. Validate project status (must be 'triage' = pre-flight passed; 'session_2' = Iterate).
2. Open / reuse session row (type=1).
3. Persist 1-3 variants (+ větev a HEAD SHA z worktree, pokud existuje) + per-role preference matrix.
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

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import ProjectNotFound, exit_if_project_missing, tips  # noqa: E402
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.extract import BRAND, DATA_ROOT, git_info, locate_worktree, table_has_col  # noqa: E402
from tool.cli.ux import CzechArgumentParser, die, emit, read_spec  # noqa: E402

SESSIONS_DIR = DATA_ROOT / "sessions"
ALLOWED_BUILDERS = {"claude-code", "codex-cli", "v0", "bolt", "lovable",
                    "stitch", "cursor", "figma-make", "manual"}
PREFERENCE_DIMS = ("user_value", "effort", "risk", "strategic_fit")

# AI-only deflation cap per role-catalog v0.2 (#14) + synthesis 02:
# AI-only persona feedback score deflated max 0.5.
AI_ONLY_CAP = 0.5


# --------------------------------------------------------------------------
# Aggregation helpers
# --------------------------------------------------------------------------



def _is_placeholder_url(url: str | None) -> bool:
    """Sandbox placeholder emitted by the facilitator / quick_session before a real preview exists."""
    return not url or "sandbox.invalid" in url


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


DIFF_SUMMARY_LABELS = {
    "stat": "Diff stat",
    "touched_existing": "Upravené existující soubory",
    "reuse": "Reuse",
    "new": "Nové",
    "mock": "Mock / stub",
    "acceptance_pass": "Acceptance pass",
}


def diff_summary_to_md(diff_summary: Any) -> str | None:
    """Diff walkthrough (pflanzer.md KROK 4.5) → markdown bullet list.

    Accepts the dict from the vote spec (known keys first, unknown keys kept),
    a plain string (stored as-is) or None.
    """
    if not diff_summary:
        return None
    if isinstance(diff_summary, str):
        return diff_summary.strip() or None
    if not isinstance(diff_summary, dict):
        return json.dumps(diff_summary, ensure_ascii=False)
    keys = [k for k in DIFF_SUMMARY_LABELS if k in diff_summary]
    keys += [k for k in diff_summary if k not in DIFF_SUMMARY_LABELS]
    lines = []
    for k in keys:
        val = diff_summary[k]
        if val in (None, "", []):
            continue
        if isinstance(val, (list, tuple)):
            val = ", ".join(f"`{x}`" for x in val)
        lines.append(f"- **{DIFF_SUMMARY_LABELS.get(k, k)}**: {val}")
    return "\n".join(lines) or None


SPEC_EXAMPLE = """  {
    "slug": "moje-appka",
    "facilitator": "Fanda",
    "decider_call": {"shortlist": ["A", "B"], "rationale": "A je nejrychlejší"},
    "variants": [
      {"name": "A", "builder": "claude-code", "prototype_url": "https://…",
       "description_md": "Co varianta dělá",
       "role_preferences": [{"role_idx": 1, "user_value": 0.8, "effort": 0.3, "risk": 0.2,
                             "strategic_fit": 0.9, "commitment_level": 3,
                             "rationale": "Proč to tak vidím (1–2 věty)"}]}
    ]
  }"""


def _validate_spec(spec: dict[str, Any]) -> None:
    if "slug" not in spec:
        raise ValueError("Ve specu chybí `slug` (jméno projektu z Kickoffu).")
    variants = spec.get("variants") or []
    if not (1 <= len(variants) <= 3):
        raise ValueError(f"Build musí mít 1–3 varianty, ve specu jich je {len(variants)}.")
    seen_names: set[str] = set()
    for i, v in enumerate(variants, 1):
        label = f"Varianta {v.get('name') or '#' + str(i)}"
        for k, why in (("name", "písmeno A, B nebo C"),
                       ("builder", "čím se stavěla, např. claude-code")):
            if not v.get(k):
                raise ValueError(f"{label}: chybí `{k}` ({why}).")
        if v["builder"] not in ALLOWED_BUILDERS:
            raise ValueError(f"{label}: neznámý builder „{v['builder']}“. "
                             f"Povolené: {', '.join(sorted(ALLOWED_BUILDERS))}.")
        if v["name"] in seen_names:
            raise ValueError(f"Varianta {v['name']} je ve specu dvakrát.")
        seen_names.add(v["name"])
        for rp in v.get("role_preferences", []):
            if not rp.get("rationale"):
                raise ValueError(
                    f"{label}: u hlasu role {rp.get('role_idx', '?')} chybí `rationale` "
                    "(1–2 věty, proč to zástupce vidí tak, jak hlasoval)."
                )
            for dim in PREFERENCE_DIMS:
                val = rp.get(dim)
                if val is None:
                    continue
                if isinstance(val, bool) or not isinstance(val, (int, float)) or not 0 <= val <= 1:
                    raise ValueError(
                        f"{label}: hlas role {rp.get('role_idx', '?')} má `{dim}` = {val!r}; "
                        "hodnocení je číslo 0–1 (např. 0.8, vyšší = lepší; u effort a risk "
                        "nižší = lepší). Opravte spec a zapište Build znovu."
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
              "diff_summary": {"stat": "...", "reuse": "...", "new": "...",
                               "mock": "...", "acceptance_pass": "3/4"},
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
    warnings: list[str] = []
    facilitator = spec.get("facilitator") or current_actor()
    decider_call = spec.get("decider_call", {})

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = SESSIONS_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, target_repo_url FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        project_id, status, target_repo_url = int(proj[0]), proj[1], proj[2]
        # session_2 = Iterate → další Build kolo (ADR-0021)
        if status not in ("triage", "session_1", "session_2"):
            raise ValueError(
                f"Project status='{status}'. Build vyžaduje 'triage' "
                f"(spusť `/pm start` / triage pro {slug} nejdřív) nebo Iterate po Rozhodnutí."
            )

        # Role lookup: catalog_idx → role row metadata
        role_rows = conn.execute(
            "SELECT id, catalog_idx, catalog_label, status, ai_proxy_mode "
            "FROM roles WHERE project_id = ?",
            (project_id,),
        ).fetchall()
        if not role_rows:
            raise ValueError(
                "Žádné role v DB. Dokonči Kickoff (`/pm start`) nejdřív."
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
        iterate_round = status == "session_2"  # Iterate = další Build kolo (max 1×)
        existing_variants: dict[str, int] = {}
        if sess:
            session_id = int(sess[0])
            existing_variants = {
                r[0]: int(r[1]) for r in conn.execute(
                    "SELECT name, id FROM variants WHERE session_id = ?", (session_id,),
                ).fetchall()
            }
            # Keep real preview URLs (e.g. stored by `worktree.py preview --run` or
            # `set-url`) when a re-vote only carries the sandbox placeholder.
            kept_urls = {
                r[0]: r[1] for r in conn.execute(
                    "SELECT name, prototype_url FROM variants WHERE session_id = ?",
                    (session_id,),
                ).fetchall()
                if r[1] and not _is_placeholder_url(r[1])
            }
            # Opakovaný zápis NEmaže feedback ani extracted_code: varianty se upsertují
            # podle jména. Nepřítomné varianty se mažou jen mimo Iterate kolo.
            if not iterate_round:
                for name, vid in existing_variants.items():
                    if name not in {v["name"] for v in spec["variants"]}:
                        conn.execute("DELETE FROM variants WHERE id = ?", (vid,))
        else:
            kept_urls = {}
            cur = conn.execute(
                "INSERT INTO sessions (project_id, type, starts_at, decision) "
                "VALUES (?, 1, ?, 'pending')",
                (project_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            session_id = cur.lastrowid

        # Persist variants + role_preferences
        # diff_summary_md is an additive column (audit N10) — older DBs
        # without `migrate.py` run simply skip it.
        has_diff_col = any(
            r[1] == "diff_summary_md"
            for r in conn.execute("PRAGMA table_info(variants)").fetchall()
        )
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

            given_url = v.get("prototype_url")
            proto_url = (
                kept_urls.get(v["name"], given_url or "")
                if _is_placeholder_url(given_url) else given_url
            )
            if _is_placeholder_url(proto_url):
                warnings.append(
                    f"Varianta {v['name']} nemá preview URL — zástupci v Asyncu nemají na co klikat. "
                    f"Doplň: `pflanzer worktree set-url --slug {slug} --variant {v['name']} "
                    f"--url https://…`")
                proto_url = proto_url or ""  # sandbox.invalid zůstává (NOT NULL), None -> ""
            if v["name"] in existing_variants:
                variant_id = existing_variants[v["name"]]
                conn.execute(
                    "UPDATE variants SET builder = ?, prototype_url = ?, "
                    "description_md = ?, preference_score = ? WHERE id = ?",
                    (v["builder"], proto_url, v.get("description_md"),
                     agg_score, variant_id),
                )
                conn.execute("DELETE FROM role_preferences WHERE variant_id = ?", (variant_id,))
            else:
                cur = conn.execute(
                    """
                    INSERT INTO variants (
                        session_id, name, builder, prototype_url,
                        description_md, preference_score
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id, v["name"], v["builder"], proto_url,
                        v.get("description_md"), agg_score,
                    ),
                )
                variant_id = cur.lastrowid

            # Větev + HEAD SHA z worktree (pokud existuje)
            branch = head_sha = None
            wt = locate_worktree(slug, v["name"], target_repo_url)
            if wt is not None:
                gi = git_info(wt)
                branch, head_sha = gi["branch"], gi["head_sha"]
                if table_has_col(conn, "variants", "head_sha"):
                    conn.execute("UPDATE variants SET branch = ?, head_sha = ? WHERE id = ?",
                                 (branch, head_sha, variant_id))
            diff_md = diff_summary_to_md(v.get("diff_summary"))
            if diff_md and has_diff_col:
                conn.execute(
                    "UPDATE variants SET diff_summary_md = ? WHERE id = ?",
                    (diff_md, variant_id),
                )

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
                "prototype_url": None if _is_placeholder_url(proto_url) else proto_url,
                "preference_score": agg_score,
                "branch": branch, "head_sha": head_sha,
                "description_md": v.get("description_md"),
                "diff_summary_md": diff_md,
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
                "iterate_round": iterate_round,
                "branches": {v["name"]: v["branch"] for v in persisted_variants if v["branch"]},
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
        "warnings": warnings,
        "next_step": (
            "Async: sdílej preview"
            + (" URL variant (" + ", ".join(f"{v['name']} {v['prototype_url']}"
                                          for v in persisted_variants if v["prototype_url"]) + ")"
               if any(v["prototype_url"] for v in persisted_variants) else "")
            + f" zástupcům kroků cesty (3–5 dní). Feedback sbírej přes `/pm feedback {slug}`, "
            f"pak `/pm decide {slug}`."
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
        f"{'shortlist' if v['name'] in shortlist else '—'} | "
        f"{'[preview](' + v['prototype_url'] + ')' if v['prototype_url'] else '— (bez URL)'} |"
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

    return f"""{BRAND}

# Build — {slug}

> Project ID: {project_id} · Session ID: {session_id}
> Facilitátor: {spec.get('facilitator', '—')}
> Viz `docs/methodology/04-session-1.md`.

## Varianty

| Varianta | Builder | Skóre (agg) | Shortlist | Preview |
|----------|---------|-------------|-----------|---------|
{var_table}

> Score = unweighted mean (user_value, 1-effort, 1-risk, strategic_fit) per role,
> weighted (mandatory ×1.5, recommended ×1.0, optional ×0.5),
> AI-only persona deflated max {AI_ONLY_CAP} (synthesis 02).

## Decider's call

- **Shortlist**: {', '.join(shortlist) if shortlist else '— (Decider call missing)'}
- **Rationale**: {decider_call.get('rationale', '—')}
{veto_section}{parking_section}
{chr(10).join(matrix_blocks)}

## Další krok

1. Sdílej preview URL variant zástupcům kroků cesty (Async, 3–5 dní).
2. `/pm feedback {slug}` — stáhne a agreguje feedback do DB.
3. `/pm decide {slug}` — Rozhodnutí (Go / Iterate max 1× / Kill, Decider hlasuje poslední).
"""


def render_decision_md(
    spec: dict[str, Any], variants: list[dict[str, Any]],
    idx_to_role: dict[int, dict[str, Any]],
) -> str:
    decider_call = spec.get("decider_call", {})
    shortlist = decider_call.get("shortlist", [])
    return f"""## Build — shortlist Deciderem

- Shortlist (1-3 variant): **{', '.join(shortlist) or '—'}**
- Rationale: {decider_call.get('rationale', '—')}
- Veto registr: {len(decider_call.get('veto_register') or [])} items
- Parking lot: {len(decider_call.get('parking_lot') or [])} items

### Agregované skóre variant

{chr(10).join(f"- **{v['name']}** (`{v['builder']}`) → {v['preference_score']:.2f}" for v in variants)}

Atribuce: {current_actor()} · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""


def _fmt(x: float | None) -> str:
    return f"{x:.2f}" if x is not None else "—"


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def run_from_json(path: Path | str) -> dict[str, Any]:
    return persist(read_spec(path, example=SPEC_EXAMPLE))


def _owners_for(slug: str) -> dict[str, str]:
    from tool.cli.triage import path_owners
    with transaction() as conn:
        row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        return path_owners(conn, int(row[0])) if row else {}


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer session", description=__doc__.split("\n")[0])
    p.add_argument("--spec", required=True,
                   help="JSON spec (slug + variants + role_preferences): soubor, nebo `-` pro stdin")
    p.add_argument("--json", action="store_true", help="Výstup jako JSON (pro skripty)")
    args = p.parse_args()
    try:
        out = run_from_json(args.spec)
    except ValueError as e:
        exit_if_project_missing(e)
        die(str(e), "pflanzer session --spec spec.json   (nebo: … | pflanzer session --spec -)\n"
            "Formát specu:\n" + SPEC_EXAMPLE)
    ranked = sorted(out["variants"], key=lambda v: -v["preference_score"])
    lines = ["Hlasování jádra (0–1, vyšší = lepší): "
             + ", ".join(f"{v['name']} {v['preference_score']:.2f}" for v in ranked)]
    lines.append("Varianty: " + ", ".join(
        f"{v['name']} ({v['builder']})" for v in out["variants"]))
    owners = _owners_for(out["slug"])
    sec = owners.get("bezpecnost")
    nxt = (f"{sec or 'zástupce bezpečnosti'} podepíše okno do 48 h: `pflanzer checkpoint --slug "
           f"{out['slug']} bezpecnost --by {sec or 'JMÉNO'} --note …`; zástupci zatím píšou feedback "
           f"(`/pm feedback {out['slug']}`)")
    emit(out, title=f"Build zapsán: {out['slug']}", lines=lines, warnings=out["warnings"],
         next_step=nxt, tips=tips(out["slug"], "build", {}), as_json=args.json)


if __name__ == "__main__":
    main()
