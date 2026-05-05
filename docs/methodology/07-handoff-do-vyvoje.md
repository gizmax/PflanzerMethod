# 07 — Handoff do vývoje

> Závěrečný krok Pflanzerovy metody. Výstupem Session 2 není „kód", ale
> **podepsaný handoff package**, který tým vývoje může vzít a postavit z něj
> produkt — nebo ho vědomě zahodit.

## Filozofie handoffu

**Prototyp není produkt.** Default kontrakt v Charteru je **throw-away
pattern**: prototyp slouží k alignmentu a falsifikaci variant, po Session
2 se zahazuje a produkční implementace startuje na paved-road template
[perspektiva 04].

**Evolve pattern** je povolen výhradně tehdy, když Charter podepíše FE
lead + EM + Security a platí: token compliance >90 %, a11y Critical/
Serious clean, SBOM + secret scan clean, DPIA pokrytí, IaC v platform
monorepu [perspektivy 04, 15; synthesis 01 osa A]. Bez paketu sandbox
technicky neuvolní deploy do prod sítě (24h TTL, noindex, watermark,
network default-deny) [perspektiva 15].

**Champion model adopce** [synthesis 03 #17]. Každý handoff má
pojmenovaného championa — senior engineer z přijímajícího týmu, byl v
Session 1+2, podepsal Decision log. Vlastní delivery, vede T+30/60/90
readout, reportuje do CoP. Bez championa metoda zhasne po druhém pilotu.

## Definition of Done pro handoff package

Každá ze 7 sekcí níže musí mít před Session 2 closure stav **ano / ne /
N/A s důvodem**. „N/A" vyžaduje větu proč (např. *„#6 Data handoff: N/A —
internal tooling bez release intentu, instrumentation deferred"*). Bez
explicitních checkboxů se handoff nepodepisuje a Session 2 končí ve
stavu „iterate" [synthesis 02 bod 11].

## Handoff Package — 7 + 1 sekcí

### 1. Decision package (vlastní PM + Facilitátor)

- **Business Charter** finální verze: problém, segment, ARR impact,
  success metric (lagging + 1+ leading), XYZ hypotéza, decider mandate
  podepsaný CPO, throw-away/evolve flag [synthesis 02 § Business Charter].
- **Decision log** se **lidskou atribucí** každého rozhodnutí (DORA, AI
  Act čl. 14, GDPR čl. 22) [synthesis 01 osa C; perspektiva 03]. Formát:
  `<rozhodnutí> | <kdo navrhl> | <kdo schválil> | <datum> | <rationale>`.
- **ADR drafty** 3–5 kusů (API versioning, idempotency, transakční
  hranice, error model, sync vs eventy) [perspektiva 05].
- **Parking lot rezoluce** — každý odložený bod má owner + due date,
  jinak se vrací do Session 2 jako blocker.
- **Score závaznosti per role** (1–5 Likert + rationale field, AI-only
  feedback weight max 0.5) [synthesis 02 bod 5].

### 2. Backend handoff (vlastní BE lead) [perspektiva 05]

- **Lintovaný OpenAPI 3.1** finální varianty (Spectral clean, examples,
  RFC 7807 errors, idempotency-key konvence). Žádný YAML export z UI nebo
  PDF — raw spec v repu.
- **ERD diff** + breaking-change registr per consumer:

  ```
  | Field/Endpoint | Změna | Consumer | Owner | Migration window |
  |----------------|-------|----------|-------|------------------|
  | /v1/orders.id  | UUID→ULID | mobile-app, billing | @ne... | 2 sprinty |
  ```
- **Migration plan stub**: backfill strategy, dual-write window,
  rollback plán, feature flag, odhad času (po 2-day capped spiku, ne
  z místnosti) [synthesis 03, EM patch].
- **Contract test skeleton** (Pact / Schemathesis) — názvy testů per
  scénář, ne implementace.
- **Observability checklist**: jaké metriky/traces/logs vznikají, kdo
  vlastní dashboardy, alert thresholds, cardinality estimate (anti
  Prometheus blow-up).

### 3. Frontend handoff (vlastní FE lead) [perspektivy 04, 06]

- **Component manifest delta**: každá obrazovka označená `reused /
  new candidate / one-off`. Cíl pro evolve: >80 % reused, <10 % one-off.
- **Design tokens diff** proti Style Dictionary export. Token compliance
  report (% stylů z tokens vs hardcoded, cíl pro evolve >90 %).
- **A11y baseline** = axe-core run + manuální keyboard test top 3
  obrazovek. Critical/Serious = blocker pro „final" status [perspektiva
  11; synthesis 03 #11 patch].
- **Figma↔commit lineage**: každá Figma frame má git commit hash
  implementační branch; každá komponenta v repu má Figma node ID. Dual
  source of truth nepřijatelný — Figma vizuál, kód implementace, **oba
  mapují na stejné tokeny** [perspektiva 06].
- **Repo + git history** (ne ZIP). Code review startuje den 1 po Session 2.

### 4. QA handoff (vlastní QA lead) [perspektiva 08]

- **3–5 BDD/Gherkin scénářů per accepted varianta**, **min. 1 ne-happy
  path** per varianta:

  ```gherkin
  Feature: Plan upgrade
    Scenario: Payment timeout during upgrade
      Given user on Pro plan with valid card
      When upgrade request times out at gateway
      Then user sees retry CTA, not duplicate charge
      And idempotency-key prevents second charge on retry
  ```
- **Test pyramide split** (70/20/10) s vlastníkem per vrstva (dev = unit
  + integration; QA = E2E + exploratory).
- **Contract test skeleton** synced s BE Pactem.
- **Exploratory charter** pro post-handoff (90 min, mission + areas +
  out-of-scope + deliverable).
- **P2P (Prototype-to-Prod) checklist — 9 položek** [perspektiva 08]:
  1. Gherkin akceptace s ≥1 negative scenario per varianta.
  2. Test pyramide split + vlastník per vrstva.
  3. API contract + Pact testy zadané a passující.
  4. Regression impact analysis (jaké existující flows feature ovlivňuje).
  5. Observability v DoD (logs, metrics, traces instrumented).
  6. Synthetic data sada (žádné prod data v testech).
  7. Security sign-off (SBOM clean, secret scan clean).
  8. A11y baseline (Critical/Serious clean pro public-facing).
  9. DoD podepsaná QA + dev + PM.

  **Bez 9/9 položek prototyp neopouští sandbox.**

### 5. Platform handoff (vlastní DevOps / Platform) [perspektiva 15]

- **Sandbox spec** finální (Terraform modul `pflanzer-sandbox`: VPC,
  throwaway DB, syntetický seeder, audit logging, 24h TTL, cost cap).
  Sdílený artefakt se Security [synthesis 01 osa A].
- **Paved-road template volba** — který cookiecutter (`internal-tool`,
  `customer-portal`, `batch-job`, `realtime-api`, `mobile-be`). Vibe-coder
  generoval *do* templatu, ne na zelené louce.
- **SLO archetype** ze SLO Quick-Set library:
  ```
  Archetype: customer-portal
  Availability: 99.9% / 30d
  p95 latency: < 300ms (read), < 800ms (write)
  Error budget: 0.1% / 30d
  ```
- **Promote-to-prod gate checklist** (viz níže) — DevOps owner.
- **Runbook stub**: alert thresholds, on-call rotation, rollback
  procedura, dependencies graph.
- **Footprint TCO sheet** finální: services, compute, storage, third-
  party SaaS (DORA čl. 28 vendor registr), est. monthly cost.

### 6. Data handoff (vlastní Data / Analytics) [perspektiva 12]

- **Event taxonomy delta** — nové eventy v `object_action` snake_case,
  registered v schema registry (Avo / Snowplow Iglu). Schema diff blokuje
  merge.
- **Measurement plan** v1: 1 primary lagging metric, 2–3 leading
  indicators, 1+ guardrail (latency, error rate, churn proxy).
- **A/B test design**: control vs treatment, randomization unit, sample
  size kalkulace, expected runtime, **kill criteria** (např. *„Po 14
  dnech v 95% CI bez upliftu > MDE → treatment kill"*).
- **Instrumentation deadline = ship date − 2 dny** (tvrdé pravidlo,
  pre-commit hook na schema registry diff). Bez merge-blokujícího schema
  checku eventy nikdy nevzniknou včas [perspektiva 12 § 5.4].
- **Dashboard mockup link** (Looker/Amplitude drátěnka) — kde žije
  primary + leading metrics, kdo má access.

### 7. Support handoff (vlastní CS proxy) [perspektiva 13]

- **Ticket prediction worksheet** per accepted varianta (top-3 kategorie,
  volume tickets/week, median TTR, deflectable %, new macros, capacity
  impact, VoC match z 20 verbatim citací).
- **Support docs deadline plan**:
  ```
  D-7  KB draft v review
  D-5  Enablement deck pro agenty
  D-3  Peer review KB článku
  D-2  Training + makra live + escalation path
  D-0  Launch
  D+1  Hourly ticket dashboard
  D+30 Retro s verbatim sample, kalibrace worksheetu
  ```
  **D-2 readiness = merge-blocker.** Bez něj launch posunut.
- **Churn signal radar baseline**: cancellations citing flow N / 90d,
  1-CSAT M, reopened K, NPS detractor mentions L, trend ↑/↓/flat.
- **Post-launch monitoring**: ticket tag pro feature, alert thresholds
  (např. *>20 tiketů/h v category X = page on-call*), escalation path.

### 8. Compliance handoff (vlastní Legal / DPO + Security) [perspektiva 10; synthesis 02 § AI Act]

- **Audit trail** všech rozhodnutí (transcript + decision log + score
  závaznosti, retence 7 let dle DORA).
- **RoPA update** — Record of Processing Activities, nový/změněný
  záznam pro feature.
- **AI Act risk-tier classification entry** v risk registru
  (Unacceptable / High-risk / Limited / Minimal). Pro high-risk +
  Annex IV tech doc skeleton.
- **DPIA artefakt** (čl. 35 GDPR) podepsaný DPO, pokud feature spadá
  do triggerů (osobní data, profiling, ADM, special categories,
  novel AI use).
- **DPA flag pro vendor**: každý použitý vibe-coding tool / SaaS má
  podepsaný DPA + SCC (pokud cross-border non-adequacy země). TIA
  pro audit-grade [synthesis 02 § Could].
- **Privacy Notice draft** + **Legal basis statement** per feature,
  z firemní template (nikdy AI-generated marketing claims).

## Promote-to-prod gate

Explicitní checklist před **prvním produkčním deployem** features
postavené nad Pflanzer artefakty. Sjednocuje výstupy sekcí 4, 5, 7, 8.
Owner: **Platform engineer + QA lead společně**. Bez 100 % zelených
bodů merge nemožný.

```
[ ] OpenAPI lintovaný (Spectral) + Pact contract testy passující
[ ] P2P checklist 9/9 (sekce 4)
[ ] SBOM (cyclonedx/syft) clean, žádné Critical/High CVE
[ ] Secret scan (gitleaks/trufflehog) clean
[ ] IaC v platform monorepu, terraform plan + OPA policy check pass
[ ] OpenTelemetry instrumented (logs/metrics/traces), 4 golden signals
    dashboard live
[ ] SLO baseline definovaný + runbook v on-call wiki
[ ] On-call rotation assigned, alert thresholds nastaveny
[ ] Change advisory approval (per CAB process)
[ ] DPIA podepsán (pokud aplikabilní), AI Act tech doc skeleton hotový
[ ] A11y human review pre-launch (screen reader UX, focus management) —
    AI proxy NESTAČÍ pro EAA atestaci [perspektiva 11]
[ ] Support readiness D-2: KB live, makra live, training proběhlý
[ ] Instrumentation live (event schema deployed, dashboard nahozen)
[ ] Feature flag default OFF, gradual rollout plán (0 % → 1 % → 10 %
    → 50 % → 100 %)
[ ] Rollback procedura otestovaná v staging
```

## Champion model — adopce a reinforcement

[synthesis 02 bod 11; perspektivy 12, 13]

**Pojmenování championa:** poslední bod Session 2. Champion = senior
engineer z přijímajícího týmu, byl v Session 1+2, podepsal Decision log,
má kapacitní commit od EM (≥10 % FTE na 90 dní).

**Champion buddy** [edge cases, sekce 10]: druhý senior z téže BU jako
záloha. Knowledge transfer protokol pro případ odchodu (recap deck,
async video walkthrough handoff package, decision log čtení).

**Reinforcement track** — champion vlastní:

| Milník | Owner | Deliverable |
|--------|-------|-------------|
| **T+7**  | CS proxy + Champion | Ticket category check vs prediction worksheet |
| **T+30** | Data + Champion | Build progress vs estimate, leading metric readout, retro s verbatim sample [perspektiva 12 § learning agenda] |
| **T+60** | Champion + EM | Capacity actual vs estimate, dependency drift report |
| **T+90** | Data + CS + Champion | Lagging metric vs success criterion, churn cohort analysis, learnings → role catalog patch |

Bez čtyř readoutů adopce zhasne, role catalog se nekalibruje, score
závaznosti zůstává politickým nástrojem. T+90 readout je **vstup do
další iterace metody samotné** — Pflanzer se učí na svých výstupech
[synthesis 02 bod 11].

## Co handoff NENÍ

- ZIP soubor s prototypem hozený přes plot.
- Jira ticket „implement Figma".
- „Vibe-deployed" Bolt instance s prod credentials.
- Confluence stránka bez decision atribuce.
- Handoff bez P2P checklistu = **handoff bez metody**, jen
  dramatizace alignmentu.
