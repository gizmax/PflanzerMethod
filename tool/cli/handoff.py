"""Handoff — balíček per role + metriky pilotu (v0.5; `/pm handoff`).

Po Go v Rozhodnutí (status='handoff') vygeneruje do výstupní složky
(`<DATA_ROOT>/handoffs/<slug>/`, viz `pflanzer data`) doplňkové soubory per role:
1. `decision.md`      — shrnutí Kickoffu (ne kopie charteru) + decision log + ADR drafty
2. `be.md`            — OpenAPI 3.1 stub, ERD placeholder, breaking-change registr
3. `fe.md`            — component manifest delta, design tokens diff
4. `qa.md`            — Gherkin scénáře + contract test skeleton + P2P checklist
5. `platform.md`      — sandbox spec + paved-road template + SLO archetyp
6. `data.md`          — event taxonomy delta + plán měření
7. `support.md`       — ticket prediction worksheet + deadline podkladů pro support
8. `compliance.md`    — audit trail + RoPA + AI Act register

Primární artefakt je `SHIP.md` (`handoff_pr.py`, 1 stránka + PR příkaz + sekce
"Změř po 30 dnech"). Každý soubor začíná brand line.

Plus `method-metrics.json` (`<DATA_ROOT>/method-metrics.json`): metriky pilotu
napříč projekty — čas Kickoff -> Rozhodnutí -> Ship, počet lidí v jádru, feedback
dle severity, gate skóre vítěze, počet Iterate kol a LOC vítěze. Na trhu AI-asistovaného
vývoje nikdo takováto data nemá; bez nich se metoda nedá zlepšovat.

Jinja2 se nepoužívá — string šablony v Pythonu jsou čitelnější a bez závislostí.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import ProjectNotFound, count, exit_if_project_missing, tips  # noqa: E402
from tool.cli.db import audit, transaction  # noqa: E402
from tool.cli.extract import (  # noqa: E402
    BRAND,
    DATA_ROOT,
    clean_text,
    repo_blocks,
    table_has_col,
    tilde,
)
from tool.cli.quality_gates import load_repo_gates  # noqa: E402
from tool.cli.session_2 import get_winner  # noqa: E402
from tool.cli.ux import CzechArgumentParser, die, emit  # noqa: E402

HANDOFF_DIR = DATA_ROOT / "handoffs"
METRICS_PATH = DATA_ROOT / "method-metrics.json"


# --------------------------------------------------------------------------
# Data fetcher
# --------------------------------------------------------------------------


class KilledProject(ValueError):
    """Zabitý projekt se nepředává — poučení místo balíčku."""

    def __init__(self, slug: str) -> None:
        super().__init__(f"Projekt {slug} skončil Kill — handoff se nedělá.")
        self.slug = slug


def _fetch_project_context(slug: str) -> dict[str, Any]:
    """Pull all context needed for handoff generation."""
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, name, slug, status, charter_md, xyz_hypothesis, "
            "decider_name, sponsor_name, ai_act_tier, data_class, "
            "throwaway_or_evolve, capacity_profile, capacity_person_days, "
            "primary_lagging_metric, leading_metric, guardrail_metric, "
            "kill_criteria, created_at, updated_at "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        if proj[3] == "killed":
            raise KilledProject(slug)
        if proj[3] != "handoff":
            raise ValueError(
                f"Project status='{proj[3]}'. Handoff vyžaduje status='handoff' "
                f"(= Go v Rozhodnutí). Spusť `/pm decide {slug}` nejdřív."
            )
        project_id = int(proj[0])

        roles = list(conn.execute(
            "SELECT catalog_idx, catalog_label, status, ai_proxy_mode, "
            "human_owner, rationale FROM roles WHERE project_id = ? "
            "ORDER BY catalog_idx",
            (project_id,),
        ).fetchall())

        triage = list(conn.execute(
            "SELECT track, status, artefact_md, signed_by FROM triage "
            "WHERE project_id = ?", (project_id,),
        ).fetchall())

        sessions = list(conn.execute(
            "SELECT id, type, decision, decision_atribuce, decision_ts, "
            "starts_at, ends_at FROM sessions WHERE project_id = ? "
            "ORDER BY type",
            (project_id,),
        ).fetchall())

        winner_name = get_winner(conn, project_id)
        variants = list(conn.execute(
            """
            SELECT v.name, v.builder, v.prototype_url, v.preference_score,
                   v.description_md
            FROM variants v
            JOIN sessions s ON s.id = v.session_id
            WHERE s.project_id = ? AND s.type = 1
            ORDER BY (v.name = ?) DESC, v.preference_score DESC
            """,
            (project_id, winner_name or ""),
        ).fetchall())
        branch_by_variant = {}
        if table_has_col(conn, "variants", "head_sha"):
            branch_by_variant = {
                r[0]: (r[1], r[2]) for r in conn.execute(
                    "SELECT v.name, v.branch, v.head_sha FROM variants v "
                    "JOIN sessions s ON s.id = v.session_id WHERE s.project_id = ? AND s.type = 1",
                    (project_id,)).fetchall()
            }

        decisions = list(conn.execute(
            "SELECT type, body_md, atribuce_user, atribuce_ts FROM decisions "
            "WHERE project_id = ? ORDER BY id",
            (project_id,),
        ).fetchall())

        feedback_summary = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) AS criticals,
                   SUM(CASE WHEN is_ai_only THEN 1 ELSE 0 END) AS ai_only
            FROM feedback f
            JOIN variants v ON v.id = f.variant_id
            JOIN sessions s ON s.id = v.session_id
            WHERE s.project_id = ? AND s.type = 1
            """,
            (project_id,),
        ).fetchone()

        # Time-to-handoff: created_at → first decision.atribuce_ts where type='handoff'
        handoff_decision = conn.execute(
            "SELECT atribuce_ts FROM decisions WHERE project_id = ? AND type = 'handoff' "
            "ORDER BY id LIMIT 1",
            (project_id,),
        ).fetchone()

        # Extracted code per variant
        diff_cols = ("e.diff_loc_added" if table_has_col(conn, "extracted_code", "diff_loc_added")
                     else "NULL")
        extracted_rows = list(conn.execute(
            f"""
            SELECT v.name, e.id, e.local_path, e.extraction_method,
                   e.files_count, e.total_loc, e.source_url, e.source_repo_url,
                   {diff_cols}
            FROM extracted_code e
            JOIN variants v ON v.id = e.variant_id
            JOIN sessions s ON s.id = v.session_id
            WHERE s.project_id = ? AND s.type = 1
            """,
            (project_id,),
        ).fetchall())
        extracted_by_variant = {
            row[0]: {
                "extracted_id": row[1], "local_path": row[2],
                "method": row[3], "files_count": row[4], "total_loc": row[5],
                "source_url": row[6], "source_repo_url": row[7], "diff_loc_added": row[8],
                "branch": branch_by_variant.get(row[0], (None, None))[0],
                "head_sha": branch_by_variant.get(row[0], (None, None))[1],
            } for row in extracted_rows
        }

        path_owners: dict[str, str] = {}
        try:
            orow = conn.execute("SELECT path_owners_json FROM projects WHERE id = ?",
                                (project_id,)).fetchone()
            path_owners = json.loads(orow[0]) if orow and orow[0] else {}
        except Exception:  # noqa: BLE001 — starší DB bez sloupce
            path_owners = {}
        try:
            from tool.cli.triage import load_risk_profile
            risk_profile = load_risk_profile(conn, project_id)
        except Exception:  # noqa: BLE001
            risk_profile = None

        # Latest gate score
        gate_score = conn.execute(
            "SELECT gate_score_latest, production_readiness_target "
            "FROM projects WHERE id = ?", (project_id,),
        ).fetchone()

    top_name = winner_name or (variants[0][0] if variants else None)
    repos = repo_blocks(slug, top_name) if top_name else []
    repo_gates = load_repo_gates(slug, top_name) if repos and top_name else []
    return {
        "repos": repos, "repo_gates": repo_gates,
        "project": dict(proj) if hasattr(proj, "keys") else None,
        "project_tuple": proj,
        "project_id": project_id,
        "roles": [dict(r) for r in roles] if roles and hasattr(roles[0], "keys") else [
            {"catalog_idx": r[0], "catalog_label": r[1], "status": r[2],
             "ai_proxy_mode": r[3], "human_owner": r[4], "rationale": r[5]}
            for r in roles
        ],
        "triage": [{"track": t[0], "status": t[1], "artefact_md": t[2], "signed_by": t[3]}
                   for t in triage],
        "sessions": [{"id": s[0], "type": s[1], "decision": s[2],
                      "decision_atribuce": s[3], "decision_ts": s[4],
                      "starts_at": s[5], "ends_at": s[6]} for s in sessions],
        "variants": [{"name": v[0], "builder": v[1], "prototype_url": v[2],
                      "preference_score": v[3], "description_md": v[4]}
                     for v in variants],
        "decisions": [{"type": d[0], "body_md": d[1], "atribuce_user": d[2],
                       "atribuce_ts": d[3]} for d in decisions],
        "feedback_summary": {
            "total": feedback_summary[0] or 0,
            "criticals": feedback_summary[1] or 0,
            "ai_only": feedback_summary[2] or 0,
        },
        "handoff_decision_ts": handoff_decision[0] if handoff_decision else None,
        "extracted_by_variant": extracted_by_variant,
        "winner": winner_name,
        "path_owners": path_owners, "risk_profile": risk_profile,
        "gate_score": int(gate_score[0]) if gate_score and gate_score[0] is not None else 0,
        "production_readiness_target": int(gate_score[1]) if gate_score and gate_score[1] else 80,
    }


# --------------------------------------------------------------------------
# Per-role renderers (8)
# --------------------------------------------------------------------------


def render_decision(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    # Charter se tu NEduplikuje (je v DB a v decision logu Kickoffu); jen shrnutí + odkaz.
    log_entries = [d for d in ctx["decisions"] if d["type"] != "charter"]
    decision_lines = "\n\n".join(d["body_md"] for d in log_entries)
    return f"""# Decision package — {p[1]}

> Projekt: `{p[2]}` · Vygenerováno: {_now()} · Stav: `{p[3]}`

## Shrnutí Kickoffu

- **Hypotéza**: {p[5] or 'doplnit'}
- **Decider**: {p[6] or 'doplnit'} · **Sponzor**: {p[7] or 'doplnit'}
- **Metriky**: primary {clean_text(p[13])} · leading {clean_text(p[14])} · guardrail {clean_text(p[15])}
- **Kill kritéria**: {p[16] or 'doplnit'}
- **Vítěz Rozhodnutí**: {ctx.get('winner') or '—'}

Celé zadání (charter) je v DB toolu (`pflanzer db`) a v decision logu v target repu.

## Decision log (bez charteru)

{decision_lines or '_(žádná rozhodnutí v logu)_'}

## ADR drafty (návrhy)

Z konfliktů řešených v Rozhodnutí a z triage lze vyrobit:

- ADR: throw-away vs evolve (viz `docs/decisions/0005-…`)
- ADR: AI Act tier + výsledek DPIA (z Legal triage)
- ADR: životní cyklus sandboxu (z Platform triage)

Tým by tyto body měl projít a založit konkrétní ADR soubory v `docs/decisions/` target repa.
"""


def _repo_stat_lines(ctx: dict[str, Any]) -> list[str]:
    """Statistika per repo (větev, base, rozsah diffu, gate skóre); [] pro jednorepo."""
    repos = ctx.get("repos") or []
    if len(repos) < 2:
        return []
    out = []
    for b in repos:
        g = next((x for x in ctx.get("repo_gates") or [] if x["role"] == b["role"]), None)
        size = (f"+{b['added']}" + (f" / -{b['removed']}" if b.get("removed") is not None else "")
                + f" řádků v {b['files']} souborech") if b.get("added") is not None else "rozsah neznámý"
        out.append(f"- **{b['role']}** (`{b['ref']}`): větev `{b['branch']}`"
                   + (f" @ `{b['head_sha'][:10]}`" if b.get("head_sha") else "")
                   + f", base `{b['base']}`, {size}"
                   + (f", gate skóre {g['gate_score']}/100" if g else ""))
    return out


_FIN_RE = re.compile(
    r"(?i)\bDORA\b|\bPSD2\b|MiFID|Solvency|\bbank\w*|pojišť\w*|pojistn\w*|finančn\w+|"
    r"platební|platebn\w+|fintech|úvěr\w*|hypotéč\w*|investičn\w+|broker\w*|obchodník s cennými")


def is_financial(ctx: dict[str, Any]) -> bool:
    """Spadá projekt do finančního sektoru (DORA)? Podle zadání, domény a triage artefaktů."""
    p = ctx["project_tuple"]
    parts = [str(x or "") for x in (p[1], p[4], p[5])]
    parts += [str(t.get("artefact_md") or "") for t in ctx.get("triage", [])
              if t.get("track") in ("legal", "security")]
    return bool(_FIN_RE.search(" ".join(parts)))


def regulation_text(ctx: dict[str, Any]) -> dict[str, str]:
    """Regulatorní formulace podle domény: DORA a 7letá retence jen u finančního sektoru."""
    if is_financial(ctx):
        return {"attrib": "DORA / AI Act čl. 14 / GDPR čl. 22",
                "attrib_short": "DORA",
                "retention": "audit_log retention 7 let (DORA)",
                "retention_note": "(DORA 7-letá retence enforced)",
                "third_party": "DORA 3rd-party review",
                "recipients": "z DORA 3rd-party register",
                "ir_sla": "Incident response SLA ≤ 4 h: doplnit per vendor (DORA čl. 12)",
                "concentration": "Provider concentration risk: doplnit (DORA čl. 28)",
                "logging": "structured logs s atribucí, 7-letá retence (DORA)"}
    return {"attrib": "AI Act čl. 14 / GDPR čl. 22",
            "attrib_short": "AI Act čl. 14",
            "retention": "audit_log retence dle Legal triage (nástroj ukládá 7 let; upřesnit)",
            "retention_note": "(retenci určí Legal triage; nástroj ukládá 7 let)",
            "third_party": "3rd-party review",
            "recipients": "z registru dodavatelů",
            "ir_sla": "Incident response SLA: doplnit per vendor (dle smlouvy)",
            "concentration": "Závislost na jednom dodavateli: doplnit",
            "logging": "structured logs s atribucí, retence dle Legal triage"}


def stack_commands(local_path: str | None) -> tuple[str, str]:
    """(stack, bash blok) podle souborů ve větvi vítěze: Go / Python / Rust / Node / Make."""
    root = Path(local_path).expanduser() if local_path else None

    def has(*names: str) -> bool:
        return bool(root and root.is_dir() and any((root / n).exists() for n in names))

    if has("go.mod"):
        return "go", "go mod download     # pokud ještě ne\ngo vet ./...\ngo build ./...\ngo test ./..."
    if has("package.json"):
        return "node", "npm install        # pokud ještě ne\nnpm run lint\nnpm run build\nnpm test"
    if has("pyproject.toml", "requirements.txt", "setup.py"):
        return "python", "python -m pip install -e .   # pokud ještě ne\nruff check .\npython -m pytest"
    if has("Cargo.toml"):
        return "rust", "cargo clippy\ncargo build\ncargo test"
    if has("Makefile"):
        return "make", "make lint\nmake build\nmake test"
    return "unknown", "# stack nerozpoznán — použij příkazy z README / Makefile projektu"


def _who(ctx: dict[str, Any], step: str, role: str) -> str:
    """„Role (jméno)“ podle zástupce kroku cesty z Kickoffu; bez jména jen role."""
    name = (ctx.get("path_owners") or {}).get(step)
    return f"{role} ({name})" if name else role


def _loc_text(ext: dict[str, Any]) -> str:
    """Rozsah kódu: celkem ve větvi + (když je známo) kolik z toho přibylo oproti base."""
    out = f"{ext['total_loc']} řádků celkem ve větvi"
    if ext.get("diff_loc_added") is not None:
        out += f", z toho +{ext['diff_loc_added']} přidáno oproti base (stejné číslo jako ve `SHIP.md`)"
    return out


def _winner_routes(ctx: dict[str, Any]) -> list[str]:
    """Trasy (stránky) přidané ve větvi vítěze; [] když kód nebo rozpoznání chybí."""
    top = ctx["variants"][0] if ctx["variants"] else None
    ext = ctx["extracted_by_variant"].get(top["name"]) if top else None
    if not ext or not ext.get("local_path"):
        return []
    try:
        from tool.cli import preview
        wt = Path(ext["local_path"]).expanduser()
        return preview._added_routes(wt) if wt.is_dir() else []
    except Exception:  # noqa: BLE001 — jen doplněk handoffu
        return []


_SCHEMA_HINT = re.compile(r"(?i)(^|/)(migrations?|models?|schema|prisma|db)(/|\.|$)")


def _schema_files(ctx: dict[str, Any]) -> list[str]:
    top = ctx["variants"][0] if ctx["variants"] else None
    ext = ctx["extracted_by_variant"].get(top["name"]) if top else None
    if not ext or not ext.get("local_path"):
        return []
    root = Path(ext["local_path"]).expanduser()
    if not root.is_dir():
        return []
    found: list[str] = []
    try:
        for f in sorted(root.rglob("*")):
            rel = f.relative_to(root).as_posix()
            if (f.is_file() and not any(x in rel for x in ("node_modules/", ".git/", ".venv/"))
                    and _SCHEMA_HINT.search(rel) and rel.endswith(
                        (".sql", ".prisma", ".py", ".js", ".ts", ".rb", ".go", ".dbml"))):
                found.append(rel)
            if len(found) >= 6:
                break
    except OSError:
        return found
    return found


def render_be(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    top_variant = ctx["variants"][0] if ctx["variants"] else None
    var_block = ""
    extracted_block = ""
    if top_variant:
        var_block = (
            f"### Top varianta\n\n"
            f"- Name: `{top_variant['name']}` · Builder: `{top_variant['builder']}`\n"
            f"- Preview: {top_variant['prototype_url']}\n"
            f"- Score: {top_variant['preference_score']:.2f}\n"
        )
        ext = ctx["extracted_by_variant"].get(top_variant["name"])
        if ext:
            extracted_block = (
                f"\n### Kód vítěze\n\n"
                f"- Větev: `{ext.get('branch') or '—'}`"
                f"{' @ `' + ext['head_sha'][:10] + '`' if ext.get('head_sha') else ''}\n"
                f"- Metoda: `{ext['method']}`\n"
                f"- Soubory: {ext['files_count']} · Rozsah: {_loc_text(ext)}\n"
                f"- Gate skóre: **{ctx['gate_score']}/100 (práh {ctx['production_readiness_target']})**\n\n"
                f"BE kód hledej typicky v `server/` nebo `api/` dané větve. "
                f"Pokud chybí, backend se píše v páru, FE už je hotové.\n"
            )
            stat = _repo_stat_lines(ctx)
            if stat:
                be_repos = [b for b in ctx["repos"] if b["backend"] and not b["primary"]]
                where = (f"BE kód je v samostatném repu `{be_repos[0]['role']}` "
                         f"(`{be_repos[0]['ref']}`), ne v podsložce FE repa: PR do něj má vlastní "
                         "větev a base."
                         if be_repos else
                         "Projekt má víc repozitářů; každý má vlastní větev, base a PR.")
                extracted_block = (
                    "\n### Kód vítěze (per repo)\n\n" + "\n".join(stat) + "\n"
                    f"- Gate skóre celkem: **{ctx['gate_score']}/100 "
                    f"(práh {ctx['production_readiness_target']})**\n\n{where}\n")

    be_owner = _who(ctx, "vyvoj", "Backend lead")
    routes = _winner_routes(ctx)
    if routes:
        be_paths_yaml = (f"  # Trasy nalezené v kódu vítěze (z diffu větve). Operace a schémata\n"
                         f"  # doplní {be_owner} při review PR.\n"
                         + "".join(f"  {r}:\n    get:\n      summary: trasa z kódu vítěze\n"
                                   "      responses:\n        '200': { description: ok }\n"
                                   for r in routes[:10]))
    else:
        be_paths_yaml = (f"  # V kódu vítěze nástroj nerozpoznal žádné přidané trasy. Paths doplní\n"
                         f"  # {be_owner} z kódu větve vítěze (nebo z OpenAPI repa, je-li).\n")
    schema = _schema_files(ctx)
    vname = top_variant["name"] if top_variant else "A"
    if schema:
        erd_md = (f"Soubory ve větvi vítěze ({vname}), které vypadají jako schéma dat / migrace:\n\n"
                  + "\n".join(f"- `{x}`" for x in schema)
                  + f"\n\nERD z nich nakreslí {be_owner} (dbml / erdantic) před merge do produkce.")
    else:
        erd_md = (f"Ve větvi vítěze ({vname}) nástroj nenašel migrace ani modely dat. Ověří "
                  f"{be_owner}: pokud varianta data neukládá, napíše to sem; jinak doplní plán "
                  "migrace (dbml / erdantic) před merge do produkce.")
    return f"""# Backend handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 5 (Backend / API lead).

{var_block}{extracted_block}

## OpenAPI 3.1 stub

```yaml
openapi: 3.1.0
info:
  title: {p[2]} API
  version: 0.1.0-handoff
servers:
  - url: https://api.{p[2]}.sandbox.example.com
paths:
{be_paths_yaml}  /healthz:
    get:
      summary: Liveness probe
      responses:
        '200': {{ description: ok }}
```

## ERD placeholder

{erd_md}

## Breaking-change registr

| Endpoint | Change | Consumer ownership | Migration plan |
|----------|--------|--------------------|----|
| _(none yet)_ | _(none)_ | _(none)_ | _(none)_ |

## Contract test skeleton (Pact)

- Provider: {p[2]} BE
- Consumers: seznam doplní {be_owner} (kdo volá API; z výstupu BE experta z Buildu)
- Test framework: Pact / Schemathesis
- CI gate: every PR runs contract tests against latest consumer pact

## ADR drafty (3-5)

1. Choice of HTTP framework (FastAPI default per CLAUDE.md)
2. Auth strategy (default: SSO + JWT, override per Charter)
3. Error format (RFC 7807 Problem Details)
4. Pagination strategy
5. Idempotency keys pro write endpoints
"""


def render_fe(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    top = ctx["variants"][0] if ctx["variants"] else None
    ext = ctx["extracted_by_variant"].get(top["name"]) if top else None
    extracted_section = ""
    stat = _repo_stat_lines(ctx)
    repo_md = ("\n### Repa\n\n" + "\n".join(stat) + "\n") if stat else ""
    if ext:
        extracted_section = f"""

## Kód vítěze

- **Větev**: `{ext.get('branch') or '—'}`{' @ `' + ext['head_sha'][:10] + '`' if ext.get('head_sha') else ''}
- **Metoda**: `{ext['method']}`
- **Soubory**: {ext['files_count']} · {_loc_text(ext)}
- **Gate skóre**: **{ctx['gate_score']}/100 (práh {ctx['production_readiness_target']})**
  ({'splňuje práh' if ctx['gate_score'] >= ctx['production_readiness_target'] else 'pod prahem'})

{repo_md}
### Co s tím dál

```bash
cd {tilde(ext['local_path'])}
{stack_commands(ext['local_path'])[1]}
```

Detail per brána: `quality-{top['name']}.md` ve výstupní složce (`pflanzer data`).

### PR

Kód už je ve větvi vítěze v target repu - nic se nekopíruje. Otevři PR příkazem
ze `SHIP.md` (`pflanzer handoff_pr --slug {p[2]}`).
"""
    fe_owner = _who(ctx, "vyvoj", "Frontend lead")
    design_owner = _who(ctx, "design", "Design")
    routes = _winner_routes(ctx)
    routes_line = (f"Přidané trasy / stránky ve větvi vítěze: {', '.join(f'`{x}`' for x in routes[:10])}."
                   if routes else "Přidané trasy / stránky nástroj ve větvi vítěze nerozpoznal.")
    var_names = [v["name"] for v in ctx["variants"]] or ["A"]
    tokens_md = "\n".join(f"- {n}: % doplní {design_owner} při review (cíl > 90 %)"
                          for n in var_names)
    return f"""# Frontend handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 4 (Frontend / Vibe-coding lead).

## Throw-away vs evolve directive

**`{p[10]}`** (per Charter, ADR-0005)

{'EVOLVE: vyžaduje code review (FE + EM + bezpečnost) před merge do produkčního repa.' if p[10] == 'evolve' else 'Throw-away: prototyp zůstává v sandboxu, do produkčního repa se NEPŘENÁŠÍ. Slouží jako reference pro čistou implementaci.'}
{extracted_section}

## Vítězná varianta

- Name: `{top['name'] if top else '—'}`
- Builder: `{top['builder'] if top else '—'}`
- Preview: {top['prototype_url'] if top else '—'}

## Component manifest delta

Nástroj komponenty nepočítá. {routes_line}
Seznam nových / změněných / zrušených komponent doplní {fe_owner} při review PR
(`git diff --stat` ze `SHIP.md` ukáže dotčené soubory).

## Design tokens diff

Podíl použitých design tokenů nástroj neměří. Per varianta ho doplní {design_owner}:

{tokens_md}

DS deviation list (s ownerem) — viz souhrn Buildu (`_summary.md`).

## Figma↔commit lineage placeholder

| Figma node ID | Commit hash | Date | Author |
|---------------|-------------|------|--------|
| _(populate post-implementation)_ | _(post-impl)_ | _(post-impl)_ | _(post-impl)_ |

## A11y baseline (z A11y triage)

- WCAG 2.2 AA target
- axe-core run report: doplnit (run pre-merge)
- Critical/Serious findings = blocker

## Tech stack contract

- Framework: per Charter / repo standard
- ESLint + Prettier: enforced v CI
- TypeScript strict mode: enabled
"""


def render_qa(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    top = ctx["variants"][0] if ctx["variants"] else None
    reg = regulation_text(ctx)
    return f"""# QA handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 8 (QA / Test lead).

## Acceptance criteria — BDD/Gherkin

**Vítězná varianta**: `{top['name'] if top else '—'}` (`{top['builder'] if top else '—'}`)

```gherkin
Feature: {p[1]}

  Scenario: Happy path
    Given valid input z persona
    When uživatel projde flow
    Then primary lagging metric ({clean_text(p[13])}) zaznamená event

  Scenario: Negative path — invalid input
    Given invalid input
    When uživatel zkusí submit
    Then UI vrátí actionable error message (B1/B2 plain language)
    And žádná data nejsou persisted

  Scenario: Negative path — backend timeout
    Given valid input
    When BE response > 5s
    Then UI ukáže loading state, pak fallback graceful
    And retry button je dostupný
```

> ⚠ Per role-catalog #8: **lidský review každého scénáře povinný před CI**
> (LLM testuje implementaci, ne chování).

## Contract test skeleton (Pact)

- Consumer: FE
- Provider: BE (per `be.md` handoff)
- Pact framework
- CI gate: every PR runs `pact-broker can-i-deploy`

## P2P (Prototype-to-Prod) checklist (9 položek)

- [ ] Acceptance criteria reviewed + signed by PdM
- [ ] Contract tests (Pact) zelené
- [ ] A11y axe-core run pass (žádné Critical / Serious)
- [ ] Security: SBOM (`cyclonedx`/`syft`) + CVE scan (Trivy/Snyk) clean
- [ ] Secret scan (gitleaks) clean
- [ ] Performance baseline meets SLO (z platform.md)
- [ ] Measurement plan instrumented (z data.md)
- [ ] Support docs ready D-7 (KB) → D-2 (makra) (z support.md)
- [ ] Decision log atributed ({reg['attrib_short']}), {reg['retention']}

## Exploratory test charter (90 min template)

- Mission: Explore variant {top['name'] if top else 'A'} pro edge cases
- Areas: error states, empty states, loading states, slow network
- Time-box: 90 min strict
- Tester: assigned QA in roles
- Output: bug log + risk areas pro regression suite
"""


def render_platform(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    plat_triage = next((t for t in ctx["triage"] if t["track"] == "platform"), None)
    sec_triage = next((t for t in ctx["triage"] if t["track"] == "security"), None)
    return f"""# Platform / DevOps handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 15 (DevOps / Platform).

## Sandbox spec (z Platform triage)

Status: **{plat_triage['status'] if plat_triage else 'unknown'}** · Signed by:
{plat_triage['signed_by'] if plat_triage else '—'}

```hcl
# Terraform module: iac/sandbox/{p[2]}.tf (placeholder)
# 24h TTL auto-destroy, VPC isolated, watermark + noindex.
# Synthetic / pseudonymized data only (data_class = {p[9]}).
```

## Paved-road template

- Approved runtime: per security triage approved AI tool list
- Container image: official base only (alpine / distroless)
- Observability: OpenTelemetry traces + structured JSON logs
- Secrets: Vault + OIDC, NIKDY .env do gitu

## SLO baseline (per archetype)

Vyber 1 z 5 archetypů:
- internal tool: 99.0 % availability, p95 < 2s
- customer portal: 99.5 % availability, p95 < 1s
- batch job: < 30 min latency tail
- real-time API: 99.9 %, p95 < 200ms
- mobile BE: 99.5 %, p95 < 500ms

**Vyber pro {p[2]}**: doplnit (vyplň při first deploy).

## 4 golden signals dashboard

- Latency (p50, p95, p99)
- Traffic (req/s)
- Errors (4xx, 5xx ratio)
- Saturation (CPU, memory, disk)

Tool: Grafana / DataDog (per company default).

## Promote-to-prod gate checklist

- [ ] Sandbox URL + IaC commit hash
- [ ] SLO baseline defined + approved by EM
- [ ] Runbook stub committed
- [ ] On-call rotation defined
- [ ] Disaster recovery plan (RTO/RPO)
- [ ] Cost estimate (TCO sheet) + budget approval
- [ ] Security sign-off (SBOM + CVE + secret scan clean)

## {regulation_text(ctx)['third_party']} (z Security triage)

{sec_triage['artefact_md'][:500] if sec_triage and sec_triage['artefact_md'] else '_(no security triage artefakt — spusť triage znovu před produkcí)_'}
"""


def render_data(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    return f"""# Data / Analytics handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 12 (Data / Analytics).

## Measurement plan v1

| Metric type | Metric | Source | Cadence |
|-------------|--------|--------|---------|
| **Primary lagging** | {clean_text(p[13])} | doplnit | weekly |
| **Leading** | {clean_text(p[14])} | doplnit | daily |
| **Guardrail** | {clean_text(p[15])} | doplnit | continuous |

> ⚠ **Instrumentation deadline = ship-date − 2 dny (merge-blokující).**
> Per role catalog #12 + perspektiva 12.

## Event taxonomy delta

```
Naming convention: object_action (snake_case)

NEW EVENTS (this sprint):
- nový_event_1
- nový_event_2

MODIFIED EVENTS:
- (none)

DEPRECATED EVENTS:
- (none)
```

> ⚠ **PII NIKDY v event name nebo property.** Hashing / pseudonymizace
> server-side per Security + Legal triage.

## A/B test design (pokud applicable)

- Hypothesis: per Charter XYZ
- Variants: control vs {ctx["variants"][0]["name"] if ctx["variants"] else 'A'}
- Primary metric: {clean_text(p[13])}
- Sample size: doplnit (power analysis)
- Duration: doplnit (typically 2 weeks)
- **Kill criteria**: {p[16] or 'doplnit'}

## Learning agenda

- T+30: efficiency check (does primary lagging move?)
- T+60: deeper cohort analysis
- T+90: decision Go-bigger / Iterate / Sunset

## Privacy classification

- Data class: **{p[9]}** (z Charter)
- Consent strategy: doplnit (per Legal triage)
- Retention: per data class default (L1: 5 let, L2: 3 roky, L3: 1 rok podle GDPR + use case)
"""


def _predicted_issues(ctx: dict[str, Any], limit: int = 3) -> list[str]:
    """Top problémy z feedbacku vítěze (critical → low) jako základ predikce ticketů."""
    winner = ctx.get("winner") or (ctx["variants"][0]["name"] if ctx["variants"] else None)
    if not winner:
        return []
    try:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT f.rationale FROM feedback f JOIN variants v ON v.id = f.variant_id "
                "JOIN sessions s ON s.id = v.session_id WHERE s.project_id = ? AND v.name = ? "
                "ORDER BY CASE f.severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 "
                "WHEN 'medium' THEN 2 ELSE 3 END, f.id", (ctx["project_id"], winner)).fetchall()
    except Exception:  # noqa: BLE001 — jen doplněk handoffu
        return []
    out: list[str] = []
    for (why,) in rows:
        t = " ".join(str(why or "").replace("|", "/").split())
        if t and t[:80] not in [x[:80] for x in out]:
            out.append(t[:140])
        if len(out) >= limit:
            break
    return out


def render_support(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    sup = _who(ctx, "provoz", "Customer support proxy")
    issues = _predicted_issues(ctx)
    rows = "\n".join(
        f"| {txt} | odhad doplní {sup} | cíl doplní {sup} | doplní {sup} | feedback Buildu |"
        for txt in issues) or (
        f"| top 3 problémy doplní {sup} z feedbacku Asyncu | — | — | — | — |")
    return f"""# Customer Support handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 13 (Customer support proxy).

## Ticket prediction worksheet

| Predicted issue | Volume estimate | TTR target | Deflectable? | VoC match |
|-----------------|-----------------|------------|--------------|-----------|
{rows}

> Per role catalog #13: top-3 predikované tickety = **P1 v acceptance
> criteria** (řešeno v `qa.md`).

## Support docs deadline

- **D-7**: KB článek draft hotov (link na release notes)
- **D-2**: Macros + agent training (15 min) hotové
- **D+30**: Retro tickets review, KB article update

## Churn signal radar

- Sledovat ticket spike v 7 dnech post-launch
- Sledovat NPS delta v 30 dnech
- Sledovat CSAT na ticketech reference {p[2]}

## Verbatim citace baseline (z předchozích 90 dní ticketů)

{sup} doplní 5 verbatim citací z ticketů posledních 90 dní k Voice of Customer
(per `04-session-1.md` § Full — rozšířená agenda) nejpozději do D-7 před spuštěním.

## Capacity baseline

- Predicted ticket volume increase: odhad doplní {sup}
- Required additional agent capacity: person-hours / week doplní {sup}
- Escalation path: tier 1 → tier 2 → product team
"""


def _excerpt(md: str, n: int = 1500) -> str:
    """Začátek + konec artefaktu: poznámky oken (checkpointy) jsou připojené na konci."""
    md = md.strip()
    if len(md) <= n:
        return md
    return md[: n // 3].rstrip() + "\n\n[…]\n\n" + md[-(n * 2 // 3):].lstrip()


def render_compliance(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    legal_triage = next((t for t in ctx["triage"] if t["track"] == "legal"), None)
    sec_triage = next((t for t in ctx["triage"] if t["track"] == "security"), None)
    audit_count_text = "doplnit (query audit_log)"
    slug = p[2]
    owners = ctx.get("path_owners") or {}
    step_names = {"byznys": "Byznys", "produkt": "Produkt", "design": "Design", "vyvoj": "Vývoj",
                  "bezpecnost": "Bezpečnost & právo", "provoz": "Provoz"}
    steps = "; ".join(f"{step_names[k]}: {owners[k]}" for k in step_names if owners.get(k))
    try:
        from tool.cli._compat import ai_stand_in_line
        ai_line = ai_stand_in_line(slug)
    except Exception:  # noqa: BLE001
        ai_line = None
    reg = regulation_text(ctx)
    hook_text = " ".join(str(x or "") for x in (p[5], p[4]))
    pii_hit = re.search(
        r"(?i)osobn\w*\s+(?:údaj|udaj|dat)\w*|e-?mail|telefon|jméno|jmeno|adres\w+|"
        r"přihlášk\w*|formulář\w*|registrac\w*|zákazn\w+|objednáv\w+|personal data|gdpr|"
        r"průkazk\w*|čísl\w*\s+průkaz\w*|občansk\w+\s+průkaz\w*|rodn\w+\s+čísl\w*|"
        r"datum\s+narození|narozen\w+|e-?mail\w*|telefon\w*|adres\w+|bydliště|čtenář\w*",
        hook_text)
    pii = (f"ano, podle zadání (zmínka: „{pii_hit.group(0)}“) — upřesnit kategorie"
           if pii_hit else "v zadání se osobní údaje nezmiňují — potvrdit")
    risk = ctx.get("risk_profile")
    legal_basis = ("doplnit (z Legal triage)" if legal_triage and legal_triage["artefact_md"]
                   else "doplnit; Legal triage zatím neběžela")

    decision_attrib = []
    for d in ctx["decisions"]:
        decision_attrib.append(
            f"- **{d['type']}** by {d['atribuce_user']} @ {d['atribuce_ts']}"
        )

    return f"""# Compliance handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 7 (Security) + § 10 (Legal/GDPR).

## Audit trail dump

**Decision log atribuce** ({reg['attrib']}):

{chr(10).join(decision_attrib) or '_(žádná rozhodnutí)_'}

**Audit log entries**: {audit_count_text} {reg['retention_note']}.

## RoPA update (Records of Processing Activities)

- Processing activity name: {p[1]}
- Data class: **{p[9] or 'neuvedeno'}**
- AI Act tier: **{p[8]}**
- Risk profil projektu: {risk or 'neuvedeno'}
- Decider: {p[6] or 'doplnit'} · Sponzor: {p[7] or 'doplnit'}
- Kroky cesty a zástupci: {steps or 'doplnit'}
- Kroky s AI náhradou: {ai_line or 'žádné'}
- Osobní údaje: {pii}
- Lawful basis: {legal_basis}
- Data subjects: doplnit
- Categories of data: doplnit (per Security triage Data Classification)
- Retention: per `data.md` § Privacy classification
- Recipients (3rd parties): doplnit ({reg['recipients']})

## AI Act risk register entry

- Risk tier: **{p[8]}**
- Use case description: {p[5]}
- Annex IV technical doc required: {'YES' if p[8] in ('high', 'limited') else 'NO'}
- Human oversight mechanism: doplnit (per Legal triage)
- Logging requirements: {reg['logging']}

## DPA flag list (3rd party AI vendors)

- doplnit: per Security triage Approved AI Tool list, ověř DPA na všech vendorech
- Penetration test review v posledních 12 mo: doplnit per vendor
- {reg['ir_sla']}
- {reg['concentration']}

## Triage artefakty (full text)

### Security triage

{_excerpt(sec_triage['artefact_md']) if sec_triage and sec_triage['artefact_md'] else '_(deferred — spusť triage znovu)_'}

### Legal triage

{_excerpt(legal_triage['artefact_md']) if legal_triage and legal_triage['artefact_md'] else '_(deferred — spusť triage znovu)_'}

## Pre-production gate

- [ ] DPIA finalized (pokud ≥ 2 triggery)
- [ ] AI Act tech doc (Annex IV) drafted (pokud high-risk)
- [ ] Privacy Notice update merged
- [ ] DPA signed for all AI vendors
- [ ] Security SBOM + CVE scan clean
- [ ] Secret scan clean
- [ ] Audit log retention configured ({reg['retention']})
"""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# --------------------------------------------------------------------------
# Method-level metrics
# --------------------------------------------------------------------------


def _parse_ts(value: Any) -> datetime | None:
    """ISO i SQLite CURRENT_TIMESTAMP ("YYYY-MM-DD HH:MM:SS", UTC) -> aware datetime."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _delta(a: datetime | None, b: datetime | None) -> dict[str, float | None]:
    if not a or not b:
        return {"hours": None, "days": None}
    secs = (b - a).total_seconds()
    return {"hours": round(secs / 3600, 2), "days": round(secs / 86400, 2)}


def _collect_pilot_metrics(project_id: int, ctx: dict[str, Any]) -> dict[str, Any]:
    """Metriky pilotu z DB a auditu (nic se nezadává ručně)."""
    p = ctx["project_tuple"]
    with transaction() as conn:
        sess = {r[0]: r for r in conn.execute(
            "SELECT type, starts_at, decision_ts FROM sessions WHERE project_id = ? "
            "ORDER BY id", (project_id,)).fetchall()}
        iterate_rounds = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE project_id = ? AND type = 3",
            (project_id,)).fetchone()[0]
        ship_row = conn.execute(
            "SELECT ts FROM audit_log WHERE action = 'session_3.hardening' AND target_id = ? "
            "ORDER BY id DESC LIMIT 1", (project_id,)).fetchone()
        dec_row = conn.execute(
            "SELECT ts, payload_json FROM audit_log WHERE action = 'session_2.decision' "
            "AND target_id = ? ORDER BY id DESC LIMIT 1", (project_id,)).fetchone()
        sev = {r[0]: r[1] for r in conn.execute(
            "SELECT f.severity, COUNT(*) FROM feedback f JOIN variants v ON v.id = f.variant_id "
            "JOIN sessions s ON s.id = v.session_id WHERE s.project_id = ? GROUP BY f.severity",
            (project_id,)).fetchall()}
        owners = [r[0] for r in conn.execute(
            "SELECT DISTINCT human_owner FROM roles WHERE project_id = ? "
            "AND human_owner IS NOT NULL AND TRIM(human_owner) <> ''", (project_id,)).fetchall()]
        core = None
        if table_has_col(conn, "projects", "core_json"):
            row = conn.execute("SELECT core_json FROM projects WHERE id = ?", (project_id,)).fetchone()
            if row and row[0]:
                try:
                    core = json.loads(row[0])
                except json.JSONDecodeError:
                    core = None
        winner = ctx.get("winner")
        diff = None
        if winner:
            has_diff = table_has_col(conn, "extracted_code", "diff_loc_added")
            diff = conn.execute(
                "SELECT e.total_loc, e.files_count"
                + (", e.diff_loc_added, e.diff_loc_removed, e.diff_files" if has_diff
                   else ", NULL, NULL, NULL")
                + " FROM extracted_code e JOIN variants v ON v.id = e.variant_id "
                "JOIN sessions s ON s.id = v.session_id WHERE s.project_id = ? AND s.type = 1 "
                "AND v.name = ? ORDER BY e.id DESC LIMIT 1", (project_id, winner)).fetchone()

    kickoff = _parse_ts(p[17])  # projects.created_at
    decision_at = _parse_ts(sess[2][2]) if 2 in sess else None
    ship_at = _parse_ts(ship_row[0]) if ship_row else None
    override = None
    if dec_row and dec_row[1]:
        try:
            override = json.loads(dec_row[1]).get("override_critical")
        except json.JSONDecodeError:
            override = None

    core_names = core if isinstance(core, list) else None
    if core_names is not None:
        core_size = len({(c.get("name") if isinstance(c, dict) else str(c)) for c in core_names})
    else:
        core_size = len(owners) or None

    return {
        "timeline": {
            "kickoff_at": str(p[17]) if p[17] else None,
            "build_started_at": str(sess[1][1]) if 1 in sess and sess[1][1] else None,
            "decision_at": decision_at.isoformat() if decision_at else None,
            "ship_at": ship_at.isoformat() if ship_at else None,
            "kickoff_to_decision": _delta(kickoff, decision_at),
            "decision_to_ship": _delta(decision_at, ship_at),
            "kickoff_to_ship": _delta(kickoff, ship_at),
        },
        "core_size": core_size,
        "feedback_by_severity": {k: int(sev.get(k, 0)) for k in ("critical", "high", "medium", "low")},
        "iterate_rounds": int(iterate_rounds),
        "critical_override": bool(override),
        "winner": winner,
        "winner_gate_score": ctx["gate_score"],
        "gate_target": ctx["production_readiness_target"],
        "winner_loc_added": diff[2] if diff and diff[2] is not None else None,
        "winner_loc_removed": diff[3] if diff and diff[3] is not None else None,
        "winner_files_changed": diff[4] if diff and diff[4] is not None else None,
        "winner_loc_total": diff[0] if diff else None,
    }


def update_method_metrics(slug: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """Upsert metrik pilotu do `method-metrics.json` (podle slug)."""
    p = ctx["project_tuple"]
    pilot = _collect_pilot_metrics(ctx["project_id"], ctx)

    created = _parse_ts(p[17])
    handoff_ts = _parse_ts(ctx["handoff_decision_ts"])
    days = _delta(created, handoff_ts)["days"]

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, Any] = {"projects": []}
    if METRICS_PATH.exists():
        try:
            metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            metrics = {"projects": []}

    metrics.setdefault("projects", [])
    previous = next((m for m in metrics["projects"] if m.get("slug") == slug), {})
    metrics["projects"] = [m for m in metrics["projects"] if m.get("slug") != slug]
    entry = {
        "slug": slug,
        "name": p[1],
        "ai_act_tier": p[8],
        "data_class": p[9],
        "throwaway_or_evolve": p[10],
        "capacity_person_days": p[12],
        "feedback_count": ctx["feedback_summary"]["total"],
        "feedback_critical": ctx["feedback_summary"]["criticals"],
        "feedback_ai_only": ctx["feedback_summary"]["ai_only"],
        "variants_count": len(ctx["variants"]),
        "time_to_handoff_days": days,
        "handoff_at": str(ctx["handoff_decision_ts"]) if ctx["handoff_decision_ts"] else None,
        "metrics_recorded_at": _now(),
        **pilot,
        # Vyplní se ručně po 30 dnech (viz SHIP.md, sekce "Změř po 30 dnech"); upsert ho nepřepíše.
        "after_30d": previous.get("after_30d") or {
            "code_survival_pct": None, "incidents": None, "success_metric_vs_target": None,
        },
    }
    metrics["projects"].append(entry)

    days_all = [m["time_to_handoff_days"] for m in metrics["projects"]
                if m.get("time_to_handoff_days") is not None]
    k2s = [m["timeline"]["kickoff_to_ship"]["days"] for m in metrics["projects"]
           if m.get("timeline", {}).get("kickoff_to_ship", {}).get("days") is not None]
    scores = [m["winner_gate_score"] for m in metrics["projects"]
              if m.get("winner_gate_score") is not None]
    metrics["aggregates"] = {
        "total_projects": len(metrics["projects"]),
        "avg_time_to_handoff_days": round(sum(days_all) / len(days_all), 2) if days_all else None,
        "min_time_to_handoff_days": min(days_all) if days_all else None,
        "max_time_to_handoff_days": max(days_all) if days_all else None,
        "avg_kickoff_to_ship_days": round(sum(k2s) / len(k2s), 2) if k2s else None,
        "avg_winner_gate_score": round(sum(scores) / len(scores), 1) if scores else None,
    }

    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


# --------------------------------------------------------------------------
# Generate full package
# --------------------------------------------------------------------------


RENDERERS: dict[str, Any] = {
    "decision": render_decision,
    "be": render_be,
    "fe": render_fe,
    "qa": render_qa,
    "platform": render_platform,
    "data": render_data,
    "support": render_support,
    "compliance": render_compliance,
}


def _winner_local_path(ctx: dict[str, Any]) -> str | None:
    ext = (ctx.get("extracted_by_variant") or {}).get(ctx.get("winner") or "") or {}
    return ext.get("local_path")


def render_demo_readme(ctx: dict[str, Any]) -> str:
    """Throwaway: jedna stránka místo osmi rolí — co ukázat, jak spustit, co je fake."""
    p = ctx["project_tuple"]
    stack, cmds = stack_commands(_winner_local_path(ctx))
    rationale = (ctx.get("project") or {}).get("throwaway_rationale") or ""
    measure = clean_text(p[13]) if p[13] else "metrika z Kickoffu"
    kill = p[16] or "kill kritérium z Kickoffu"
    return f"""# Demo — {p[1]}

> Projekt: `{p[2]}` · Vygenerováno: {_now()} · Throwaway (kód nejde do produkce)

## Co ukázat

- **Hypotéza**: {p[5] or 'doplnit'}
- **Vítěz Rozhodnutí**: {ctx.get('winner') or '—'}
- Projdi hlavní cestu uživatele z Kickoffu od začátku do konce; ukaž, co hypotézu potvrzuje.

## Jak spustit

Stack: {stack}. Příkazy ve větvi vítěze:

```bash
{cmds}
```

## Co je fake

- Data, uživatelé a integrace jsou ukázkové; nic tu není produkční
  (bez auth, bez zálohování, bez monitoringu).
{f'- Důvod throwaway: {rationale}' if rationale else '- Doplň sem, co přesně je v demu nasimulované.'}

## Co dál

- Metrika dema: {measure}
- Kill kritérium: {kill}
- Vyhodnocení v termínu: `pflanzer retro reminders --slug {p[2]}`
"""


def generate(slug: str) -> dict[str, Any]:
    ctx = _fetch_project_context(slug)
    out_dir = HANDOFF_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    throwaway = ctx.get("risk_profile") == "throwaway"
    if throwaway:
        path = out_dir / "README.md"
        path.write_text(f"{BRAND}\n\n{render_demo_readme(ctx)}", encoding="utf-8")
        written.append(path.name)
    for name, fn in ({} if throwaway else RENDERERS).items():
        path = out_dir / f"{name}.md"
        path.write_text(f"{BRAND}\n\n{fn(ctx)}", encoding="utf-8")
        written.append(path.name)

    # Primární artefakt = SHIP.md (1 stránka + PR příkaz + "Změř po 30 dnech")
    from tool.cli.handoff_pr import write_ship  # local import to avoid cycle
    ship_path = write_ship(slug)
    written.insert(0, ship_path.name)

    metrics_entry = update_method_metrics(slug, ctx)

    with transaction() as conn:
        audit(
            conn,
            action="handoff.generate",
            target_type="project",
            target_id=ctx["project_id"],
            payload={
                "slug": slug,
                "files": written,
                "time_to_handoff_days": metrics_entry["time_to_handoff_days"],
            },
        )

    return {
        "slug": slug,
        "out_dir": tilde(out_dir),
        "files": written,
        "metrics": metrics_entry,
        "metrics_file": tilde(METRICS_PATH),
        "throwaway": throwaway,
        "next_step": (
            "Throwaway: otevři `SHIP.md` a `README.md` (co ukázat, jak spustit, co je fake)."
            if throwaway else
            "Otevři `SHIP.md` (PR příkaz + sekce 'Změř po 30 dnech'); promote-to-prod "
            "checklisty jsou v `qa.md` a `platform.md`."
        ),
    }


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer handoff", description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--json", action="store_true", help="Výstup jako JSON (pro skripty)")
    args = p.parse_args()
    try:
        out = generate(args.slug)
    except KilledProject as e:
        from tool.cli.retro import killed_notice
        kn = killed_notice(e.slug, "handoff se nedělá")
        lines = ["Projekt ukončen (Kill) — handoff se nedělá."]
        ls = (kn or {}).get("lessons") or []
        lines += [f"Poučení: {x['text']} — {x['by']}" for x in ls] or [
            "Poučení zatím není zapsané."]
        emit({"slug": e.slug, "killed": True, "lessons": ls}, title=f"Handoff {e.slug}: Kill",
             lines=lines,
             next_step=(f"`pflanzer retro lesson --slug {e.slug} --text \"…\"`" if not ls
                        else "vezmi poučení do zadání dalšího Kickoffu (`/pm start`)"),
             tips=tips(e.slug, "after_kill", {}), as_json=args.json)
        return
    except ValueError as e:
        exit_if_project_missing(e)
        die(f"{e} Přehled projektů: `pflanzer status`.", "pflanzer handoff --slug moje-appka")
    m = out["metrics"]
    lines = [f"Hlavní dokument: {out['out_dir']}/SHIP.md (PR příkaz a měření na jedné stránce)",
             (f"Demo README (co ukázat, jak spustit, co je fake): {out['out_dir']}/README.md"
              if out.get("throwaway") else
              f"Doplňkové podklady pro role: "
              f"{count(len(out['files']) - 1, 'soubor', 'soubory', 'souborů')} v {out['out_dir']}")]
    days = m.get("time_to_handoff_days")
    if days is not None:
        lines.append(f"Od Kickoffu k předání: {count(int(days), 'den', 'dny', 'dní')}")
    if m.get("feedback_critical"):
        lines.append(f"Kritických připomínek v Asyncu bylo {m['feedback_critical']}.")
    emit(out, title=f"Předání hotové: {args.slug}", lines=lines,
         next_step=("otevři `SHIP.md` a `README.md`; throwaway jde jen jako demo"
                    if out.get("throwaway") else
                    "otevři `SHIP.md`, branch owner spustí `gh pr create` z jeho konce; "
                    "kontrolní seznamy před nasazením jsou v `qa.md` a `platform.md`"),
         tips=tips(args.slug, "handoff", {}), as_json=args.json)


if __name__ == "__main__":
    main()
