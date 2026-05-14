"""Slice 8 — Handoff package generator.

Per-role handoff artefakty po Decider Go (status='handoff'). 8 souborů:
1. `decision.md`      — Charter + decisions table dump + ADR drafty
2. `be.md`            — OpenAPI 3.1 stub, ERD placeholder, breaking-change registr
3. `fe.md`            — Component manifest delta, design tokens diff
4. `qa.md`            — Gherkin scénáře + contract test skeleton + P2P checklist (9)
5. `platform.md`      — Sandbox spec + paved-road template + SLO archetype
6. `data.md`          — Event taxonomy delta + measurement plan
7. `support.md`       — Ticket prediction worksheet + support docs deadline
8. `compliance.md`    — Audit trail dump + RoPA update + AI Act register

Plus `method-metrics.json` — time-to-handoff agregát napříč projekty (post-mortem
trends, viz devil's advocate Útok 11 — reinforcement track).

Output dir: `data/handoffs/<slug>/`. Skip vrtění Jinja2 — string templates
v Pythonu jsou čitelnější + zero dependency.
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

HANDOFF_DIR = REPO_ROOT / "data" / "handoffs"
METRICS_PATH = REPO_ROOT / "data" / "method-metrics.json"


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
                f"Project status='{proj[3]}'. /pflanzer-handoff vyžaduje "
                f"status='handoff' (= Session 2 Decider's Go). "
                f"Spusť `/pflanzer-session-2 {slug}` nejdřív."
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

        variants = list(conn.execute(
            """
            SELECT v.name, v.builder, v.prototype_url, v.preference_score,
                   v.description_md
            FROM variants v
            JOIN sessions s ON s.id = v.session_id
            WHERE s.project_id = ? AND s.type = 1
            ORDER BY v.preference_score DESC
            """,
            (project_id,),
        ).fetchall())

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

        # Extracted code per variant (Slice production-path)
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
        "gate_score": int(gate_score[0]) if gate_score and gate_score[0] is not None else 0,
        "production_readiness_target": int(gate_score[1]) if gate_score and gate_score[1] else 80,
    }


# --------------------------------------------------------------------------
# Per-role renderers (8)
# --------------------------------------------------------------------------


def render_decision(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    decision_lines = "\n\n".join(d["body_md"] for d in ctx["decisions"])
    return f"""# Decision package — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()} · Status: `{p[3]}`

## Charter (snapshot)

{p[4] or '_(charter_md missing)_'}

## Decision log (all entries)

{decision_lines or '_(žádná rozhodnutí v log)_'}

## ADR drafts (suggestions)

Ze Session 2 conflict resolutions a triage outputs lze vyrobit:

- ADR: throw-away vs evolve (per ADR-0005, link to `docs/decisions/0005-...`)
- ADR: AI Act tier + DPIA outcome (per Legal triage artefakt)
- ADR: Sandbox lifecycle (per Platform triage)

Tým by měl review těchto bodů a vyrobit konkrétní ADR soubory v `docs/decisions/`.
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
                f"\n### 🚀 Extracted code\n\n"
                f"- Local path: `{ext['local_path']}`\n"
                f"- Method: `{ext['method']}`\n"
                f"- Files: {ext['files_count']} · LOC: {ext['total_loc']}\n"
                f"- Source repo: {ext['source_repo_url'] or '(none — skeleton/manual)'}\n"
                f"- Gate score: **{ctx['gate_score']}/{ctx['production_readiness_target']}**\n\n"
                f"BE folder (typicky): `{ext['local_path']}/server/` nebo `/api/`. "
                f"Pokud chybí — tým pair-programuje na backendu, FE už máme.\n"
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
  # TODO: BE shadow agent v Session 1 měl vygenerovat per varianta.
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
- Consumers: TBD (per Session 1 BE shadow agent output)
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

## 🚀 Extracted code (PRODUCTION-READY-ish)

- **Local path**: `{ext['local_path']}`
- **Method**: `{ext['method']}`
- **Files**: {ext['files_count']} ({ext['total_loc']} LOC)
- **Gate score**: **{ctx['gate_score']}/{ctx['production_readiness_target']}**
  ({'✅ ready' if ctx['gate_score'] >= ctx['production_readiness_target'] else '⚠ pilot-only'})

### Co s tím dál

```bash
cd {ext['local_path']}
npm install        # pokud ještě ne
npm run lint       # ESLint zero warnings (target)
npm run build      # TypeScript strict mode passes
npm test           # Vitest suite
```

Quality gate per-gate detail: `data/handoffs/{p[2]}/quality-{top['name']}.md`.

### Open PR

```bash
git checkout -b feat/{p[2]}
cp -r {ext['local_path']}/* path/to/your/target_repo/
cd path/to/your/target_repo
git add . && git commit -m "feat({p[2]}): import vibe-coding output (variant {top['name']})"
git push -u origin feat/{p[2]}
gh pr create --title "feat({p[2]}): {p[1]}" --body "Pflanzer session output, gate score {ctx['gate_score']}/100"
```
"""

    return f"""# Frontend handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 4 (Frontend / Vibe-coding lead).

## Throw-away vs evolve directive

**`{p[10]}`** (per Charter, ADR-0005)

{'⚠ EVOLVE: vyžaduje code review s podpisem FE + EM + Security před merge do prod repo.' if p[10] == 'evolve' else 'Throw-away: prototype zůstává v sandboxu, do prod repa NEPŘENÁŠET. Použij jako reference pro greenfield implementaci.'}
{extracted_section}

## Vítězná varianta

- Name: `{top['name'] if top else '—'}`
- Builder: `{top['builder'] if top else '—'}`
- Preview: {top['prototype_url'] if top else '—'}

## Component manifest delta

```
TODO: Diff component inventory PRE vs POST tohoto sprintu.
- New components: TBD (extract z prototypu)
- Modified components: TBD
- Deprecated components: TBD
```

## Design tokens diff

```
TODO: Token compliance % per varianta:
- A: TBD% (target > 90 %)
- B: TBD%
- C: TBD%

DS deviation list (s ownerem) — viz Session 1 _summary.
```

## Figma↔commit lineage placeholder

| Figma node ID | Commit hash | Date | Author |
|---------------|-------------|------|--------|
| _(populate post-implementation)_ | _(post-impl)_ | _(post-impl)_ | _(post-impl)_ |

## A11y baseline (z A11y triage)

- WCAG 2.2 AA target
- axe-core run report: TBD (run pre-merge)
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
    Then primary lagging metric ({p[13] or 'TBD'}) zaznamená event

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

- [ ] Acceptance criteria reviewed + signed by PM
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

**Vyber pro {p[2]}**: TBD (vyplň při first deploy).

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

{sec_triage['artefact_md'][:500] if sec_triage and sec_triage['artefact_md'] else '_(no security triage artefakt — re-run /pflanzer-triage před production)_'}
"""


def render_data(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    return f"""# Data / Analytics handoff — {p[1]}

> Slug: `{p[2]}` · Generated: {_now()}
> Per `02-role-catalog.md` § 12 (Data / Analytics).

## Measurement plan v1

| Metric type | Metric | Source | Cadence |
|-------------|--------|--------|---------|
| **Primary lagging** | {p[13] or 'TBD'} | TBD | weekly |
| **Leading** | {p[14] or 'TBD'} | TBD | daily |
| **Guardrail** | {p[15] or 'TBD'} | TBD | continuous |

> ⚠ **Instrumentation deadline = ship-date − 2 dny (merge-blokující).**
> Per role catalog #12 + perspektiva 12.

## Event taxonomy delta

```
Naming convention: object_action (snake_case)

NEW EVENTS (this sprint):
- TBD_event_1
- TBD_event_2

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
- Primary metric: {p[13] or 'TBD'}
- Sample size: TBD (power analysis)
- Duration: TBD (typically 2 weeks)
- **Kill criteria**: {p[16] or 'TBD'}

## Learning agenda

- T+30: efficiency check (does primary lagging move?)
- T+60: deeper cohort analysis
- T+90: decision Go-bigger / Iterate / Sunset

## Privacy classification

- Data class: **{p[9]}** (z Charter)
- Consent strategy: TBD (per Legal triage)
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
| TBD issue 1     | TBD/week        | TBD min    | TBD          | TBD       |
| TBD issue 2     | TBD/week        | TBD min    | TBD          | TBD       |
| TBD issue 3     | TBD/week        | TBD min    | TBD          | TBD       |

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

- Predicted ticket volume increase: TBD %
- Required additional agent capacity: TBD person-hours / week
- Escalation path: tier 1 → tier 2 → product team
"""


def render_compliance(ctx: dict[str, Any]) -> str:
    p = ctx["project_tuple"]
    legal_triage = next((t for t in ctx["triage"] if t["track"] == "legal"), None)
    sec_triage = next((t for t in ctx["triage"] if t["track"] == "security"), None)
    audit_count_text = "TBD (query audit_log)"

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
- Lawful basis: TBD (z Legal triage)
- Data subjects: TBD
- Categories of data: TBD (per Security triage Data Classification)
- Retention: per `data.md` § Privacy classification
- Recipients (3rd parties): TBD (z DORA 3rd-party register)

## AI Act risk register entry

- Risk tier: **{p[8]}**
- Use case description: {p[5]}
- Annex IV technical doc required: {'YES' if p[8] in ('high', 'limited') else 'NO'}
- Human oversight mechanism: TBD (per Legal triage)
- Logging requirements: structured logs s atribucí, 7-letá retence

## DPA flag list (3rd party AI vendors)

- TBD: per Security triage Approved AI Tool list, ověř DPA na všech vendorech
- Penetration test review v posledních 12 mo: TBD per vendor
- Incident response SLA ≤ 4 h: TBD per vendor (DORA čl. 12)
- Provider concentration risk: TBD (DORA čl. 28)

## Triage artefakty (full text)

### Security triage

{sec_triage['artefact_md'][:1500] if sec_triage and sec_triage['artefact_md'] else '_(deferred — re-run /pflanzer-triage)_'}

### Legal triage

{legal_triage['artefact_md'][:1500] if legal_triage and legal_triage['artefact_md'] else '_(deferred — re-run /pflanzer-triage)_'}

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


def update_method_metrics(slug: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """Append project's time-to-handoff to method-metrics.json."""
    p = ctx["project_tuple"]

    # Compute time-to-handoff
    created = p[17]  # created_at
    handoff_ts = ctx["handoff_decision_ts"]
    days = None
    if created and handoff_ts:
        try:
            t0 = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(str(handoff_ts).replace("Z", "+00:00"))
            days = round((t1 - t0).total_seconds() / 86400, 2)
        except Exception:
            days = None

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, Any] = {"projects": []}
    if METRICS_PATH.exists():
        try:
            metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            metrics = {"projects": []}

    metrics.setdefault("projects", [])
    # Upsert by slug
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
        "handoff_at": str(handoff_ts) if handoff_ts else None,
        "metrics_recorded_at": _now(),
    }
    metrics["projects"].append(entry)

    # Aggregates
    days_all = [p["time_to_handoff_days"] for p in metrics["projects"]
                if p.get("time_to_handoff_days") is not None]
    metrics["aggregates"] = {
        "total_projects": len(metrics["projects"]),
        "avg_time_to_handoff_days": (
            round(sum(days_all) / len(days_all), 2) if days_all else None
        ),
        "min_time_to_handoff_days": min(days_all) if days_all else None,
        "max_time_to_handoff_days": max(days_all) if days_all else None,
    }

    METRICS_PATH.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
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
        path.write_text(fn(ctx), encoding="utf-8")
        written.append(str(path))

    # Sprint 3: primary artefakt = SHIP.md (per ADR-0010 + perspektiva 02 C7)
    from tool.cli.handoff_pr import write_ship  # local import to avoid cycle
    ship_path = write_ship(slug)
    written.insert(0, str(ship_path))  # SHIP.md first in list = primary

    metrics_entry = update_method_metrics(slug, ctx)

    with transaction() as conn:
        audit(
            conn,
            action="handoff.generate",
            target_type="project",
            target_id=ctx["project_id"],
            payload={
                "slug": slug,
                "files": [Path(w).name for w in written],
                "time_to_handoff_days": metrics_entry["time_to_handoff_days"],
            },
        )

    return {
        "slug": slug,
        "out_dir": str(out_dir),
        "files": written,
        "metrics": metrics_entry,
        "p2p_gate_checklist": (
            f"Promote-to-prod gate checklist v {out_dir}/qa.md "
            "+ {out_dir}/platform.md (9 + 7 položek)."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    args = p.parse_args()
    print(json.dumps(generate(args.slug), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
