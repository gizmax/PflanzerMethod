# 03 — Pre-session příprava

> Status: v1.0. Vstupy do Session 1, pre-flight gating, triage tracks,
> Business Charter a logistika. Bez splněných kroků 0 a 1 a bez kompletní
> MoSCoW MUST sady **Session 1 neodstartuje**.

## Krok 0 — Discovery Readiness Gate

Pflanzer řeší alignment, ne discovery. Pokud na vstupu chybí validovaný
problém, panel vyrobí „nejhladší feature factory v korporátu" [perspektiva 2].
Před svoláním Session 1 musí PM doložit tři artefakty [perspektiva 14]:

1. **Persona freshness ≤ 6 měsíců** (B2C 6 mo, B2B SaaS 9 mo, internal tooling
   12 mo s povinným re-shadowingem). Minimálně 5 nedávných rozhovorů
   s reprezentativními uživateli, transcripty existují, klíčové JTBD jsou
   pojmenované. Po pivotu / org change / market shift = auto-expire bez
   ohledu na věk.
2. **JTBD statement** ve formátu *„When [situation], I want to [job], so I
   can [outcome]"* podepsaný PM (a UX, pokud je v projektu).
3. **Opportunity Solution Tree v0** (Torres) — desired outcome → 2–3
   opportunities → uvažované solutions, vyplněný do 60 %.

**Pokud kterýkoli artefakt chybí**, předřazuje se **2-week Continuous Discovery
Sprint** (Torres rhythm: 3 zákaznické rozhovory týdně, 15 rozhovorů celkem,
OST update weekly) [synthesis 02]. Session 1 odložena. V interních /
regulovaných projektech bez přístupu k externím uživatelům: shadowing,
support ticket review, sales call recordings — **ne přeskočit**.

**Discovery Debt Detector** (AI co-pilot skill) audituje brief: kolik tvrzení
o uživateli má zdroj (research artefakt, citace transcriptu, ticket ID)
vs. assumption-stated-as-fact. Skóre 0–10. **≥7 = STOP**, předřaď discovery
sprint. **3–6 = WARNING**, závaznost session výstupů omezena na *exploratory*.
**≤2 = OK** [perspektiva 14].

## Krok 0a — Triage tracks (paralelně, async, 48–72 h pre-read)

Tři pre-read tracky probíhají souběžně, každý končí podpisem na Business
Charteru. Bez všech tří podpisů Session 1 neodstartuje [synthesis 01, blok B].

### Security & Data Triage (Security architect + DPO)

- **Data Classification Statement L1–L4** [perspektiva 07]:
  - **L1 Public** (marketing copy) — žádný gate.
  - **L2 Internal synthetic** (faker, GPT-generated) — light review.
  - **L3 Anonymizovaný snapshot** (k-anonymity ≥ 5, žádné quasi-identifiers)
    — DPIA lite + sandbox-only.
  - **L4 Real PII / payment / health** — **session se nekoná**, jde do
    plného SDLC s threat modelem.
- **Threat model lite (STRIDE one-pager)** — co chráníme, před kým, jaký
  blast radius prototypu.
- **Approved AI Tool list** s DPA / SCC (Claude Enterprise zero-retention,
  Cursor Business privacy mode, v0 Team SSO+DPA, Bolt Pro opt-out trainingu).
  **Neschválené**: free tiery, osobní účty, novel vendor bez DPA.
- **Identity & access**: SSO + MFA pro všechny účastníky, guest přístupy
  s 24h expirací.

### Legal & Privacy Triage (Legal / DPO)

- **AI Act risk tier** classification (Unacceptable / High-risk / Limited /
  Minimal). High-risk = povinný human oversight per čl. 14 + Annex IV
  technická dokumentace.
- **DPIA trigger checklist** (GDPR čl. 35/3 + EDPB guidelines): personal
  data, profiling, ADM, novel use case, special categories, large scale,
  systematic monitoring, vulnerable subjects, cross-border transfer.
- **RoPA entry** draft pokud osobní data.
- **Vendor risk register** check pro každý AI tool v session (DPA, SCC,
  exit clauses, sub-processors).
- **Marketing claim brief** pokud session generuje user-facing copy
  (UCPD + ePrivacy compliance).

### Platform Triage (DevOps / Platform engineering)

- **Sandbox spec** — pre-approved Terraform modul: isolated VPC, throwaway
  DB, syntetický seeder, audit logging do SIEM, **24h TTL**, watermark,
  noindex, žádný route do prod sítě, cost cap [synthesis 02, perspektiva 07].
- **Deploy footprint estimate v0** (TCO sheet) per uvažovaná varianta.
- **Approved runtime list** + observability contract (OTel + structured
  logs + tracing).
- **Secret policy** (Vault + OIDC, žádné hardcoded credentials).

## Krok 1 — Business Charter

Charter je primární gate artefakt. Sponzor podepisuje 5–7 dní před session,
Security/Legal/EM async pre-review do 48 h. Bez podepsaného charteru session
neodstartuje [perspektiva 01].

**Povinná pole:**

| Pole | Obsah |
|------|-------|
| Problém | Pojmenování v JTBD formátu, evidence z Discovery Readiness Gate |
| Target segment | Persona + secondary, kontext použití |
| Business hypotéza | XYZ á la Savoia: *„Alespoň X % z Y udělá Z"* — falsifikovatelný marker |
| Success metric | 1 lagging + 1 leading indicator, threshold pro „dobrý dost" |
| Kill criteria | Konkrétní podmínky pro no-go (např. *„NPS shift < 5 na pilotu = kill"*) |
| Capacity commit | Písemný sign-off od EM: počet sprintů, dependencies, IP iteration availability |
| Constraints | Budget cap, timeline cap, no-go zóny, regulatorní rails |
| Decider mandate | Písemně od CPO: *„Tom rozhoduje o variantě X v session 1, sign-off do 48 h"* |
| Throw-away vs evolve | **Throw-away je default** [synthesis 01, blok A]. Evolve vyžaduje současný podpis FE+EM+Security+Legal+Platform po code review |
| AI Act risk tier | Z Legal Triage |
| Data classification | L1–L4 z Security Triage |
| Sandbox spec ref | Odkaz na Terraform modul z Platform Triage |

**Decider model** [perspektiva 01, synthesis 02]: zadavatel = Decider
s tie-breaker právem (informed dictatorship á la GV Sprint). Není to
consensus. AI prezentuje, panel doporučuje, decider rozhoduje a podepisuje.
Zadavatel hlasuje **poslední** (anti-HiPPO).

## MoSCoW vstupy do Session 1

Default = MUST only; high-stakes / regulated = MUST + SHOULD;
audit-grade = vše [synthesis 02].

### MUST (bez nich session 1 neodstartuje)

- Business Charter (kompletní, podepsaný).
- Data Classification Statement + AI Act risk-tier (DPO + Security podpis).
- Approved AI Tool list (s DPA / SCC).
- Sandbox spec / runtime approval (Platform Triage).
- Discovery Readiness Gate ✅ (persona ≤ 6 mo, JTBD, OST v0).
- Capacity pre-sign-off od Eng managera.
- **Vibe-brief**: tech stack, design tokens, component manifest, code
  conventions (ESLint/Prettier), anti-pattern list, a11y baseline.
- **Backend Context Pack**: existující OpenAPI URL, ERD výřez, NFR baseline
  (latence, throughput), ADR archiv 12 mo, RFC 7807 error conventions.
- **Threat model lite** (STRIDE one-pager).
- **Reálná demo data** se správnou shape (synthetic L1/L2).

### SHOULD (regulated / customer-facing default-on)

- DPIA lite + RoPA entry (pokud personal data).
- Privacy Notice template + Legal basis statement per feature.
- WCAG 2.2 AA baseline + persona disability set (low vision, motor,
  cognitive — alespoň 2) [perspektiva 11].
- Event taxonomy + naming convention (`object_action`) + baseline metriky.
- Top-10 ticket kategorií + 20 verbatim citací (pokud existující customer
  base) [synthesis 02].
- Brand guidelines + voice & tone + microcopy do/don't.
- Konkurenční snapshot deck (5–8 screenshotů + 1 řádek diferenciátoru).
- Browser / device support matrix.
- JTBD karty per opportunity v OST.

### COULD (nice-to-have, audit-grade)

- Existing analytics events + dashboard / KPI strom.
- A/B test power analysis pre-read.
- Multilingual / i18n requirements (top-3 jazyky).
- Cross-border / TIA dokumenty (non-adequacy země).
- Schema registry export (Avo / Iteratively).
- IaC / GitOps repo structure conventions.

### WON'T (out-of-scope pro session 1)

- Live prod systém data (L4) → session se nekoná, jde do plného SDLC.
- Marketing copy s halucinovaným ToS / Privacy Notice — vždy z firemní
  template, ne generated.
- Production deployment artefakty — vyžadují samostatný architecture
  review gate po Session 2.
- Pen test report / TLPT (DORA čl. 24) — post-handoff.

## Volba builderu — mini-decision tree

Vibe-coding tool se volí **podle stacku, ne hype** [baseline 02]. Builder
musí být na Approved AI Tool list, jinak je session GDPR breach čekající
na kalendář [perspektiva 07].

```
Greenfield UI / marketing site?
  └─ React + shadcn defaults → v0 (Vercel)
  └─ Designově vyhraněný                → Bolt + Figma import
  └─ Jednoduchý marketing site          → Stitch nebo Lovable

Brownfield + existující design system?
  └─ Component reuse povinný   → Cursor + komponenty z monorepa
  └─ Storybook tokens          → v0 s MCP context do design tokens

Backend / API změna?
  └─ Always:                   → Cursor / Claude Code (BE shadow agent
                                  generuje OpenAPI 3.1 paralelně s UI)

Regulovaný (PSD2 SCA, MiFID, health)?
  └─ Vibe-coding NE            → standardní SDLC, Pflanzer se nehraje
```

**Sanity check**: builder musí mít zero-retention DPA, SSO/SAML, audit
log export, opt-out trainingu. Bez toho = neschváleno.

## Kalendář a logistika

- **Pre-read window**: 5–7 pracovních dní [perspektiva 03]. Kratší = role
  nezvládnou pre-read; delší = ztráta kontextu.
- **Triage tracks**: Security & Data + Legal & Privacy + Platform paralelně,
  48–72 h před session.
- **Role pozvánky**: per Decision tree z `02-role-catalog.md`. Sanity check
  > **10 lidí v místnosti = scope příliš široký**, zúžit nebo paralelní
  sessions po menších buňkách (federovaný model pro multi-team).
- **Sandbox provisioning**: Platform team objedná Terraform modul, sandbox
  ready do 24 h před session.
- **Capacity check**: EM má **veto na workshop**, pokud PI > 80 % committed
  [synthesis 02, perspektiva 09]. Bez kapacity = no session, ne „domluvíme
  to potom".
- **Délka Session 1**: 5–6 h, konec v 16:00 [perspektiva 03]. Ne 8 h.
- **Mezi-session**: 5–7 pracovních dní (ne 14).
- **Senior delegate**: každá vetovací role posílá senior s explicit
  veto/sign-off mandátem; junior bez mandátu = session se odkládá
  [perspektiva 01].

## Pre-flight checklist

Předseda projektu (PM) prochází checklist 48 h před session. **Cokoli ✗ =
session odložena**, ne začata s improvizací.

```
[ ] Business Charter podepsaný sponzorem + Decider mandate od CPO
[ ] Discovery Readiness Gate ✅ (persona ≤ 6 mo, JTBD, OST v0)
[ ] Discovery Debt Detector skóre ≤ 2 (≥ 7 = STOP)
[ ] Data Classification Statement L1/L2/L3 podepsaný DPO (L4 = no session)
[ ] AI Act risk-tier classification (provisional, re-assessed v Session 2 — viz devil's advocate Útok 4) + DPIA trigger checklist
[ ] Approved AI Tool list potvrzen pro session (s DPA / SCC)
[ ] Threat model lite (STRIDE) hotový
[ ] Sandbox provisioned (Terraform modul, VPC, 24h TTL, audit logging)
[ ] **Prompt audit pipeline** active (devil's advocate Útok 8): vendor zero-retention DPA + corporate-side prompt custody chain (SIEM ingest, 7-letá retence, search by user@SSO + project tag); BEZ toho session = DORA non-compliant
[ ] Capacity pre-sign-off od EM (písemně, **realistický odhad**: default ~10 PD, regulated ~14 PD, audit-grade ~18–22 PD — viz devil's advocate Útok 1; "8–10" je single-cycle baseline bez pre-flight, reinforcement a Champion bootstrap)
[ ] **True Cost Worksheet** vyplněný — per-role person-days + reinforcement track T+7/30/60/90 + (bootstrap) Champion coach cost
[ ] Vibe-brief: tech stack, tokens, component manifest, conventions
[ ] Backend Context Pack: OpenAPI, ERD, NFR baseline, ADR archiv
[ ] Demo data se správnou shape (synthetic L1/L2)
[ ] Roles invited per Decision tree (≤ 10 lidí), všichni s mandátem
[ ] SSO + MFA enrolment všech účastníků
[ ] WCAG 2.2 AA baseline a persona disability set (pokud customer-facing)
[ ] Event taxonomy + measurement plan draft (pokud release intent)
[ ] Top-10 ticket kategorií + 20 verbatim (pokud existující customer base)
[ ] Throw-away/evolve flag explicit (default = throw-away)
[ ] Pre-read materiál distribuován 5–7 prac. dní předem
[ ] Builder volba potvrzena per stack (decision tree výše)
```

Pokud kterákoli vetovací role (Security, Legal, EM kapacita) flagne pre-read,
session se odkládá — ne řeší se v 9:00 v místnosti.
