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

- **AI Act risk-tier classification — dvoufázový protokol v0.3** (Útok 4):
  - **Fáze A — Initial provisional (pre-Session 1).** DPO klasifikuje
    *na základě Charteru* (intended use, target user group, data
    sensitivity). Output: provisional tier (Unacceptable / High-risk /
    Limited / Minimal) **s explicit flagem `provisional, evidence-light`**.
    Bez konkrétního data flow je to *educated guess*, ne audit-grade
    statement. Slouží **pouze** jako pre-flight gate (high-risk +
    no DPIA capacity = STOP).
  - **Fáze B — Interim review (mezi-sessions).** Po Session 1 existují
    konkrétní variant artefakty (UI, API skeleton, data shape, downstream
    decision flow). DPO **přehodnotí** tier proti reálnému variantu, ne
    proti Charteru. Output: ratified tier + delta vs Fáze A (pokud
    upgrade Limited→High-risk, Session 2 dostává mandatory Conflict bod).
  - **Fáze C — Final classification (Session 2 → handoff).** DPO podepisuje
    finální tier s plnou evidence chain: data flow diagram, model card,
    intended use statement, human-oversight design (per čl. 14), Annex IV
    skeleton. **Toto je audit-grade artefakt.** Provisional flag z Fáze A
    zde **nemá místo** — buď je final, nebo handoff není kompletní.
  - **Audit dotaz:** *„Která fáze byla podepsána a kdy?"* — Method
    Steward eviduje per pilot. Pokud Fáze C chybí v handoff package,
    pilot nemůže být započítán do success rate (ADR-0007).
  - **High-risk default**: povinný human oversight per čl. 14 + Annex IV
    technická dokumentace musí být v handoff package, ne jen Fáze A klasifikace.
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

### Track-S Trigger Validation (Method Steward, jen Track S)

> **5. pre-flight track per ADR-0020 — aktivuje se POUZE pokud Charter
> označuje Track S (fallback).** Track P (preferred default ~80 %) tento
> krok přeskakuje.

Pokud Charter sponzor označuje Track S (dev #4 + #5 nebude v room), Method
Steward **MUSÍ validovat justifikaci** — 1 ze 4 hard triggers musí být
prokázán evidencí. Bez validace Session 1 neodstartuje a Method Decider
(per ADR-0011) má autoritu vrátit projekt na Track P nebo odložit.

**4 hard triggers (Charter MUSÍ specifikovat který + evidence):**

1. **Distributed dev tým ≥ 3 časové pásma.** Evidence: org chart screenshot
   s timezone tagy, demonstrace nemožnosti synchronního 3h Session 1.
2. **AI Act High-risk + certified production.** Evidence: AI Act tier Fáze A
   classification (čl. 6 + Annex III), regulator requirement pro Annex IV
   separate impl track.
3. **FDA / IEC 62304 / DO-178C / PSD2 SCA.** Evidence: regulatory scope
   statement + change-of-record proces vyžadující spec-as-artifact.
4. **Sponsor mandate spec-as-deliverable.** Evidence: signed mandate
   s rationale (multi-vendor integration contract, legacy modernization
   s novým dev týmem, M&A acquisition due diligence).

**Bez 1 ze 4 triggerů → projekt odložit**, ne přepnout na Track S. Track S
NESMÍ být easy escape hatch (per ADR-0020 § 10 strukturálních guards).

**Charter dual-signature requirement (Track S):** EM + Sponzor podepisují
oba. Žádný single-signer override.

**Output Track-S Trigger Validation:** signed 1-pager memo s trigger
justification + evidence + Method Steward sign-off. Audit log entry per
ADR-0013 Compliance Score element #13.

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
| **Track designation (v0.4)** | **Track P (default)** = dev #4 + #5 v room od minuty 0, output = produkt v prod. **Track S** (fallback) = dev mimo room, output = precision spec ≥ 80/100 + 5-stage handoff ritual. Pokud Track S, MUSÍ specifikovat 1 ze 4 hard triggers + evidence (per Track-S Trigger Validation pre-flight track). Per ADR-0020. |
| Throw-away vs evolve (v0.4) | **Default = evolve** (per ADR-0005 v0.4 rewrite). Throw-away je explicit opt-in pro 3 use cases (discovery-only pilot, audit-grade evidence separate od prod, regulated certified prod). Track × Output je 2×2 ortogonální matice, ne nested. |
| AI Act risk tier | Z Legal Triage |
| Data classification | L1–L4 z Security Triage |
| Sandbox spec ref | Odkaz na Terraform modul z Platform Triage |

**Decider model** [perspektiva 01, synthesis 02]: zadavatel = Decider
s tie-breaker právem (informed dictatorship á la GV Sprint). Není to
consensus. AI prezentuje, panel doporučuje, decider rozhoduje a podepisuje.
Zadavatel hlasuje **poslední** (anti-HiPPO).

## Krok 1a — True Cost Worksheet (povinný v0.3)

> Útok 1 devil's advocate review označil „8–10 person-days per cyklus" jako
> marketingový claim. **True Cost Worksheet** je odpověď v0.3: explicitní
> rozpočet **per role × per fáze** + **reinforcement track**, podepsaný EM
> a sponzorem před Session 1. Bez vyplněné worksheet pre-flight checklist
> selhává.
>
> **Cíl:** nikdo si po Session 1 nemůže říct *„netušil jsem, že to bude
> stát 3× tolik"*. Reinforcement track má vlastní rozpočet, ne „udělá to
> Champion ve volném čase".

### Profil cyklu (volba před vyplněním)

| Profil | Total PD (orientačně) | Trigger |
|--------|----------------------|---------|
| **Default** | ~10 PD | Standardní B2B / interní tool, žádný regulatorní gate, throw-away default |
| **Regulated** | ~14 PD | Finance (mimo PSD2 SCA), telco, healthtech non-PII, AI Act Limited risk |
| **Audit-grade** | ~18–22 PD | DORA scope, AI Act High-risk, PSD2 SCA proximity, public sector |

Volbu profilu schvaluje EM + Legal v rámci Krok 0a (Legal & Security Triage).
Profil je **odhad**, ne strop — pokud reálný cost > profil × 1.3, **flag
do Session 2 retra** a method-level T+30 readoutu (viz `method-charter.md`).

### Worksheet — per-role × per-phase

Tabulka níže je **šablona**. Vyplň aktuální čísla per pilot.
PD = person-day á 8 h. Default profil ukazuje typický řád; regulated /
audit-grade přidává na řádcích označených `+R` / `+A`.

| Role (catalog #) | Pre-flight | Session 1 | Mezi-session | Session 2 | Handoff | Reinforcement (T+7/30/60/90) | Total PD |
|-----------------|-----------|-----------|--------------|-----------|---------|------------------------------|----------|
| Zadavatel (#1) | 0.5 | 0.75 (½ den) | 0.25 | 0.5 (3h) | 0.25 | 0.25 + 0.25 + 0 + 0.5 = 1.0 | **3.25** |
| PM (#2) | 1.0 (Charter, OST) | 0.75 | 0.5 | 0.5 | 0.5 | 0.25 + 0.5 + 0.25 + 0.5 = 1.5 | **4.75** |
| Facilitátor (#3) | 0.5 (agenda, pre-read review) | 0.75 | 0.25 | 0.5 | 0.25 | 0 + 0.25 + 0 + 0.25 = 0.5 | **2.75** |
| FE / Vibe-coding lead (#4) | 0.5 (vibe-brief, builder) | 0.75 | 1.0 (iterace) | 0.5 | 1.0 (extract / hardening, viz Sprint 2) | 0 + 0.5 + 0.5 + 0.5 = 1.5 | **5.25** |
| BE / API lead (#5) | 0.5 (Context Pack) | 0.75 | 1.0 (OpenAPI shadow) | 0.5 | 1.0 | 0 + 0.5 + 0.5 + 0.5 = 1.5 | **5.25** |
| UX / Designer (#6) | 0.5 (design tokens, persona) | 0.75 | 0.5 | 0.5 | 0.25 | 0 + 0.25 + 0 + 0.25 = 0.5 | **3.0** |
| Security (#7) `+R+A` | 0.75 (STRIDE, sandbox spec) | 0.5 | 0.25 | 0.5 | 0.5 | 0 + 0.5 + 0 + 0.5 = 1.0 | **3.5** |
| QA (#8) | 0.25 (test data shape) | 0.5 | 0.5 | 0.5 | 0.75 | 0 + 0.5 + 0.5 + 0.5 = 1.5 | **4.0** |
| EM (#9) | 0.5 (capacity sign-off, Worksheet) | 0.5 | 0.25 | 0.5 | 0.5 | 0.25 + 0.5 + 0.25 + 0.5 = 1.5 | **3.75** |
| Legal / DPO (#10) `+R+A` | 0.75 (AI Act, DPIA trigger) | 0.25 (on-call) | 0.25 | 0.5 | 0.5 | 0 + 0.25 + 0 + 0.25 = 0.5 | **2.75** |
| Champion (#17) | 0.5 (bootstrap, ADR-0006) | 0.5 (on-call) | 0.5 | 0.5 | 0.5 | 0.5 + 1.0 + 0.5 + 1.0 = 3.0 | **5.5** |
| **Method Steward (org-shared)** | 0.1 | 0 | 0 | 0.1 | 0.1 | 0 + 0.25 + 0.25 + 0.25 = 0.75 | **1.05** (amortizováno přes všechny piloty) |

**Subtotal (Default profil, povinné role + Champion):** ~32 person-days.
**Realistická interpretace:** „10 PD" v původní v0.2 byla **single-cycle session-only**
projekce. Reálný end-to-end PD-cost včetně pre-flight, mezi-session iterací,
hardening a reinforcement: **3× vyšší**.

#### Regulated profil — přírůstky `+R`
- Security (#7): pre-flight +0.5 PD (DPIA lite, threat model rev), handoff +0.5 PD.
- Legal / DPO (#10): pre-flight +0.5 PD (DPIA full, RoPA), Session 2 +0.25 PD.
- A11y expert (#11, default-on regulated): celkem ~2.5 PD.
- Solution architect (#13): celkem ~2.0 PD (architecture review po S1).

#### Audit-grade profil — přírůstky `+A` nad regulated
- Co-facilitator (ADR-0010 / role #3 sekce): +1.5 PD (povinný druhý facilitátor).
- Compliance auditor / external (mimo catalog, ad-hoc): +1.0 PD pre-flight + 0.5 PD post-Session 2.
- Security (#7) DORA TLPT prep: +1.0 PD post-handoff (ne v cyklu, ale rozpočet držet).
- Method Steward report contribution: +0.25 PD per audit dotaz.

### Reinforcement track — explicit budget commit

> Útok 11 devil's advocate review: *„T+7/30/60/90 readouty bez budget
> ownership = mizí po 2 týdnech."* Worksheet má dedikovaný řádek
> pro reinforcement.

| Readout | Owner | Minimální FTE % | Co se musí stát |
|---------|-------|-----------------|------------------|
| **T+7** (1 týden) | Champion (#17) | **0.5 PD** = ~6 % týdenního FTE | Sync s dev týmem: handoff package přijatý? Co rozbilo build? Co se nepoužilo? Update SHIP.md status řádku. |
| **T+30** | PM (#2) + EM (#9) + Champion | **2.0 PD souhrnně** | Leading metric check (handoff acceptance ≥ 80 %), re-work tracking start, retro 60 min. |
| **T+60** | PM + Champion | **1.0 PD** | Leading metric trend, scope creep audit, Method Steward update (1-page report). |
| **T+90** | Decider (#1) + PM + EM + Champion | **2.5 PD** | Guardrail metric vyhodnocení (re-work %), Go / Iterate / Kill **per pilot** rozhodnutí, ADR-0007 method-level data feed. |
| **Method-level T+6 mo** | Method Steward | **0.25 PD/měsíc průběžně + 2 PD na report** | Agregace metrik napříč 3+ piloty, CoP publikace. |

**Pravidlo:** Reinforcement budget commit je **prerequisite, ne nice-to-have**.
Bez podpisu „rozpočet T+7/30/60/90 = X PD souhrnně, owner = Y" v Charteru
**Session 1 neodstartuje**. Detail viz `method-charter.md` sekce
*„Reinforcement track method-level"* a Charter projektový (ADR-0004).

**Audit dotaz po pilotu** (Method Steward T+6 report):
> *„Z X plánovaných reinforcement PD bylo skutečně utraceno Y. Pokud
> Y/X < 0.7, T+90 Go-rozhodnutí má warning: reinforcement neproběhl,
> success claim není falsifikovatelný (rovnocenné silence-triggered
> Kill per ADR-0001 Scenario B)."*

### Worksheet sign-off

Před Session 1 podepisují:
- **EM (#9)** — capacity confirm (per-role PD reálně k dispozici, ne jen na papíře).
- **Sponzor (#1 Zadavatel)** — rozpočtové schválení (PD × interní hourly rate).
- **Method Steward** — formální check, že Worksheet odpovídá profilu (default / regulated / audit-grade).

Worksheet artefakt: `worksheets/true-cost-<project-slug>.md` v `tool/templates/`
nebo v project repu (Pflanzer init layout). Verzování v gitu.

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
[ ] AI Act risk-tier **Fáze A — Initial provisional** podepsaná DPO (dvoufázový protokol v0.3 — viz Legal & Privacy Triage výše; Fáze B v mezi-session, Fáze C v Session 2) + DPIA trigger checklist
[ ] Approved AI Tool list potvrzen pro session (s DPA / SCC)
[ ] Threat model lite (STRIDE) hotový
[ ] Sandbox provisioned (Terraform modul, VPC, 24h TTL, audit logging)
[ ] **Prompt audit pipeline** active (devil's advocate Útok 8): vendor zero-retention DPA + corporate-side prompt custody chain (SIEM ingest, 7-letá retence, search by user@SSO + project tag); BEZ toho session = DORA non-compliant
[ ] Capacity pre-sign-off od EM (písemně, **realistický odhad**: default ~10 PD, regulated ~14 PD, audit-grade ~18–22 PD — viz devil's advocate Útok 1; "8–10" je single-cycle baseline bez pre-flight, reinforcement a Champion bootstrap)
[ ] **True Cost Worksheet** vyplněný a podepsaný (EM + sponzor + Method Steward) — per-role person-days × phase + reinforcement track T+7/30/60/90 + (bootstrap) Champion coach cost. Šablona: Krok 1a výše.
[ ] **Pre-registration document** (per ADR-0013) podepsaný Champion + Method Steward + Method Decider PŘED Session 1 — fit criteria binary checklist + Charter version pinned + statistical test pre-specified. Šablona: `tool/templates/pre-registration.yaml.template`.
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
