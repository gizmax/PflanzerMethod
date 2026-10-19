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

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, transaction  # noqa: E402
from tool.cli.extract import BRAND, DATA_ROOT, clean_text, table_has_col, tilde  # noqa: E402
from tool.cli.session_2 import get_winner  # noqa: E402

HANDOFF_DIR = DATA_ROOT / "handoffs"
METRICS_PATH = DATA_ROOT / "method-metrics.json"


# --------------------------------------------------------------------------
# Data fetcher
# --------------------------------------------------------------------------


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
            raise ValueError(f"Project '{slug}' not found.")
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
        extracted_rows = list(conn.execute(
            """
            SELECT v.name, e.id, e.local_path, e.extraction_method,
                   e.files_count, e.total_loc, e.source_url, e.source_repo_url
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
                "source_url": row[6], "source_repo_url": row[7],
                "branch": branch_by_variant.get(row[0], (None, None))[0],
                "head_sha": branch_by_variant.get(row[0], (None, None))[1],
            } for row in extracted_rows
        }

        # Latest gate score
        gate_score = conn.execute(
            "SELECT gate_score_latest, production_readiness_target "
            "FROM projects WHERE id = ?", (project_id,),
        ).fetchone()

    return {
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
                f"- Soubory: {ext['files_count']} · LOC: {ext['total_loc']}\n"
                f"- Gate skóre: **{ctx['gate_score']}/100 (práh {ctx['production_readiness_target']})**\n\n"
                f"BE kód hledej typicky v `server/` nebo `api/` dané větve. "
                f"Pokud chybí, backend se píše v páru, FE už je hotové.\n"
            )

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
  # TODO: BE expert v Buildu měl vygenerovat per varianta.
  # Přenes paths sem z prototype repo.
  /healthz:
    get:
      summary: Liveness probe
      responses:
        '200': {{ description: ok }}
```

## ERD placeholder

```
TODO: Z prototypu varianty {top_variant['name'] if top_variant else 'A'} extrahuj
schema migration plán. Použij dbml/erdantic.
```

## Breaking-change registr

| Endpoint | Change | Consumer ownership | Migration plan |
|----------|--------|--------------------|----|
| _(none yet)_ | _(none)_ | _(none)_ | _(none)_ |

## Contract test skeleton (Pact)

- Provider: {p[2]} BE
- Consumers: doplnit (podle výstupu BE experta z Buildu)
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
    if ext:
        extracted_section = f"""

## Kód vítěze

- **Větev**: `{ext.get('branch') or '—'}`{' @ `' + ext['head_sha'][:10] + '`' if ext.get('head_sha') else ''}
- **Metoda**: `{ext['method']}`
- **Soubory**: {ext['files_count']} ({ext['total_loc']} LOC)
- **Gate skóre**: **{ctx['gate_score']}/100 (práh {ctx['production_readiness_target']})**
  ({'splňuje práh' if ctx['gate_score'] >= ctx['production_readiness_target'] else 'pod prahem'})

### Co s tím dál

```bash
cd {tilde(ext['local_path'])}
npm install        # pokud ještě ne
npm run lint
npm run build
npm test
```

Detail per brána: `quality-{top['name']}.md` ve výstupní složce (`pflanzer data`).

### PR

Kód už je ve větvi vítěze v target repu - nic se nekopíruje. Otevři PR příkazem
ze `SHIP.md` (`pflanzer handoff_pr --slug {p[2]}`).
"""
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

```
TODO: Diff component inventory PRE vs POST tohoto sprintu.
- New components: doplnit (extract z prototypu)
- Modified components: doplnit
- Deprecated components: doplnit
```

## Design tokens diff

```
TODO: Token compliance % per varianta:
- A: doplnit% (target > 90 %)
- B: doplnit%
- C: doplnit%

DS deviation list (s ownerem) — viz souhrn Buildu (`_summary.md`).
```

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
- [ ] Decision log atributed (DORA), audit_log retention 7 let

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

## DORA 3rd-party review (z Security triage)

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


def render_support(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    return f"""# Customer Support handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 13 (Customer support proxy).

## Ticket prediction worksheet

| Predicted issue | Volume estimate | TTR target | Deflectable? | VoC match |
|-----------------|-----------------|------------|--------------|-----------|
| doplnit issue 1     | doplnit/week        | doplnit min    | doplnit          | doplnit       |
| doplnit issue 2     | doplnit/week        | doplnit min    | doplnit          | doplnit       |
| doplnit issue 3     | doplnit/week        | doplnit min    | doplnit          | doplnit       |

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

```
TODO: Customer support proxy doplní 5 verbatim citací k Voice of Customer
ritual (per `04-session-1.md` § 09:00–09:30 blok).
```

## Capacity baseline

- Predicted ticket volume increase: doplnit %
- Required additional agent capacity: doplnit person-hours / week
- Escalation path: tier 1 → tier 2 → product team
"""


def render_compliance(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    legal_triage = next((t for t in ctx["triage"] if t["track"] == "legal"), None)
    sec_triage = next((t for t in ctx["triage"] if t["track"] == "security"), None)
    audit_count_text = "doplnit (query audit_log)"

    decision_attrib = []
    for d in ctx["decisions"]:
        decision_attrib.append(
            f"- **{d['type']}** by {d['atribuce_user']} @ {d['atribuce_ts']}"
        )

    return f"""# Compliance handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 7 (Security) + § 10 (Legal/GDPR).

## Audit trail dump

**Decision log atribuce** (DORA / AI Act čl. 14 / GDPR čl. 22):

{chr(10).join(decision_attrib) or '_(žádná rozhodnutí)_'}

**Audit log entries**: {audit_count_text} (DORA 7-letá retence enforced).

## RoPA update (Records of Processing Activities)

- Processing activity name: {p[1]}
- Data class: **{p[9]}**
- AI Act tier: **{p[8]}**
- Lawful basis: doplnit (z Legal triage)
- Data subjects: doplnit
- Categories of data: doplnit (per Security triage Data Classification)
- Retention: per `data.md` § Privacy classification
- Recipients (3rd parties): doplnit (z DORA 3rd-party register)

## AI Act risk register entry

- Risk tier: **{p[8]}**
- Use case description: {p[5]}
- Annex IV technical doc required: {'YES' if p[8] in ('high', 'limited') else 'NO'}
- Human oversight mechanism: doplnit (per Legal triage)
- Logging requirements: structured logs s atribucí, 7-letá retence

## DPA flag list (3rd party AI vendors)

- doplnit: per Security triage Approved AI Tool list, ověř DPA na všech vendorech
- Penetration test review v posledních 12 mo: doplnit per vendor
- Incident response SLA ≤ 4 h: doplnit per vendor (DORA čl. 12)
- Provider concentration risk: doplnit (DORA čl. 28)

## Triage artefakty (full text)

### Security triage

{sec_triage['artefact_md'][:1500] if sec_triage and sec_triage['artefact_md'] else '_(deferred — spusť triage znovu)_'}

### Legal triage

{legal_triage['artefact_md'][:1500] if legal_triage and legal_triage['artefact_md'] else '_(deferred — spusť triage znovu)_'}

## Pre-production gate

- [ ] DPIA finalized (pokud ≥ 2 triggery)
- [ ] AI Act tech doc (Annex IV) drafted (pokud high-risk)
- [ ] Privacy Notice update merged
- [ ] DPA signed for all AI vendors
- [ ] Security SBOM + CVE scan clean
- [ ] Secret scan clean
- [ ] Audit log retention configured (7 let DORA)
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


def generate(slug: str) -> dict[str, Any]:
    ctx = _fetch_project_context(slug)
    out_dir = HANDOFF_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for name, fn in RENDERERS.items():
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
        "next_step": (
            "Otevři `SHIP.md` (PR příkaz + sekce 'Změř po 30 dnech'); promote-to-prod "
            "checklisty jsou v `qa.md` a `platform.md`."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    args = p.parse_args()
    try:
        out = generate(args.slug)
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(2)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
