# 07 — Sign-off + deploy do produkce (dual-track)

> Závěrečný krok Pflanzerovy metody. **Output závisí na Track designation**
> v Charteru (per ADR-0020 dual-track model):
>
> - **Track P (preferred, default ~80 %):** Output = běžící produkt na URL
>   (winner varianta) + sign-off package. Dev v room → žádný handoff.
> - **Track S (fallback ~20 %, 4 hard triggers):** Output = precision spec
>   ≥ 80/100 + 5-stage handoff ritual. Re-impl gap target ≤ 15 %.

## Track P — produkt do produkce (default)

### Filozofie

**Default = Track P + evolve.** Programátor byl v room od minuty 0
specifically proto, aby kód šel rovnou do prod — bez re-impl, bez paper
handoff, bez *„dev team picks up the prototype"* loop. Quality gates
v Session 2 (token compliance > 90 %, a11y Critical/Serious clean, SBOM +
secret scan clean, DPIA pokrytí, IaC v platform monorepu) jsou
**production prerequisite**, ne *„prototype hardening checklist"*
[perspektivy 04, 15; synthesis 01 osa A].

**Throw-away pro Track P** je explicit opt-in flag pro discovery-only piloty
(per ADR-0005 v0.4 — Track P + throw-away = ~5 % cases). Sponzor explicit
v Charteru s rationale. Throw-away **NENÍ default**.

Bez kompletního sign-off paketu sandbox technicky neuvolní deploy do prod
sítě (24h TTL, noindex, watermark, network default-deny) [perspektiva 15].
Sandbox je guardrail proti governance bypass.

### Track P sign-off package (Session 2 deliverable)

Track P sign-off = **audit trail**, ne re-impl spec:

- Decision log s human attribution per AI Act čl. 14
- Preference matrix + score závaznosti per role + veto registr
- DORA 7y audit log entry
- Acceptance kritéria (Gherkin) — verifikační, ne implementační (winner kód už existuje)
- AI Act Fáze C signed
- Compliance pakety (audit-grade jen): DPIA, Annex IV, Privacy Notice, SBOM,
  secret scan, axe-core, SLO baseline + runbook

### Track P D11-14: production hardening

Dev tým (same people kteří byli v Session 1 + 2):
- Polish + observability hookup
- Edge case handling
- Monitoring + alerting setup
- Production deploy

**Žádná re-implementace.** Winner kód z Session 2 → polish → prod.

## Track S — precision spec do vývoje (fallback)

### Když Track S

Dev #4 + #5 NENÍ v room. **4 hard triggers** (per ADR-0020) — bez triggeru
projekt odložit, ne přepnout:

1. Distributed dev tým ≥ 3 časové pásma
2. AI Act High-risk + certified production (Annex IV separate impl)
3. FDA / IEC 62304 / DO-178C / PSD2 SCA (regulated certified prod)
4. Sponsor mandate spec-as-deliverable (multi-vendor, legacy modernization, acquisition DD)

Method Decider (per ADR-0011) má autoritu hard-gate. EM + Sponzor
dual-signature v Charteru. Method Steward audituje trigger validation
v 5. pre-flight tracku.

### Track S sign-off package (Session 2 deliverable)

Track S sign-off = **spec navigation + audit trail**:

- **Precision spec ≥ 80/100 quality gate** (12 dimensions, per
  `tool/templates/precision-spec-track-s.md.template`):
  - A. Functional: INVEST-RA user stories, Mermaid diagrams, executable
    Gherkin BDD, edge cases enumeration, out-of-scope explicit
  - B. Technical: OpenAPI 3.1 + Spectral lint, ERD + JSON schemas + sample
    payloads, tech stack MUST/MAY/MUST NOT, NFRs
  - C. Quality: STRIDE one-pager, WCAG 2.2 AA checklist, AI Act/DPIA/DORA,
    BDD scenarios + unit prerequisites + E2E
  - D. Implementation: file structure, naming, pinned libs, anti-patterns,
    PR checklist
  - E. Sign-off: 12-role matrix s veto rights, parallel approval
- **Reference prototype z Session 1** = combined SoT s spec (anti-drift weapon)
- Decision log + AI Act Fáze C + DORA 7y log
- Spec quality gate score (publikováno transparentně)

### Track S 5-stage handoff ritual

**Critical:** žádný „throw spec over the wall". 5 stages:

1. **90-min walkthrough** (PM + dev tým lead + spec authors)
   - Spec authors present each section (A-E)
   - Reference prototype demonstrated
   - Q&A inline
2. **5-day Q&A window** (dev tým ↔ spec authors async)
   - Dev klade clarification questions
   - Spec authors odpovídají + update spec amendments inline
   - SLA: 24h response time
3. **Amendment protocol**
   - Dev requests changes (form: rationale + impact assessment)
   - Sponzor approves / rejects within 5 dní
   - Approved amendments → spec version bump (SemVer)
4. **First milestone review** (T+14-30 v dev sprint)
   - Dev demos first implementation slice (typicky 20-30 % spec scope)
   - Spec authors verify alignment vs reference prototype + Gherkin BDD
   - Drift assessment: ≤ 5 % = OK, > 5 % = root cause analysis
5. **T+30 embedded spec author shadowing**
   - 1 spec author shadows dev sprint po dobu 1 týdne
   - Detects drift early, answers questions inline
   - Reports back to Method Steward (drift metrics)

### Track S anti-drift mechanismy

Per `docs/research/dual-track-design/03-precision-spec-engineering.md`:

1. SemVer + MADR ADR cross-link pro spec changes
2. Amendment protocol s sponsor approval (above)
3. Reference prototype as combined SoT (Session 1 artifact)
4. Executable Gherkin (BDD scenarios runnable, ne prose)
5. CI sync monitoring (linter flags spec ≠ impl)
6. 30-day spec expiry — forces refresh, prevents staleness
7. T+30 embedded reviewer (above)

Track S re-impl gap target ≤ 15 % (vs SDD 9.8-42.1 % Yan et al. 2025).

## Champion model adopce (oba tracks)

[synthesis 03 #17]. Každý handoff má pojmenovaného championa — senior
engineer z přijímajícího týmu (Track P: byl v Session 1+2; Track S: dev
tým lead, attendovaný walkthrough), podepsal Decision log. Vlastní delivery,
vede T+30/60/90 readout, reportuje do CoP. Bez championa metoda zhasne po
druhém pilotu.

**Champion model adopce** [synthesis 03 #17]. Každý handoff má
pojmenovaného championa — senior engineer z přijímajícího týmu, byl v
Session 1+2, podepsal Decision log. Vlastní delivery, vede T+30/60/90
readout, reportuje do CoP. Bez championa metoda zhasne po druhém pilotu.

## Definition of Done pro handoff package

Každá ze sekcí níže musí mít před Session 2 closure stav **ano / ne /
N/A s důvodem**. „N/A" vyžaduje větu proč (např. *„Data handoff: N/A —
internal tooling bez release intentu"*). Bez explicitních checkboxů se
handoff nepodepisuje a Session 2 končí ve stavu „iterate".

## Handoff Package — 7 + 1 sekcí

### 1. Decision package (PM + Facilitátor)

- **Business Charter** finální: problém, segment, ARR impact, success
  metric (lagging + ≥1 leading), XYZ hypotéza, decider mandate podepsaný
  CPO, throw-away/evolve flag [synthesis 02].
- **Decision log** s lidskou atribucí každého rozhodnutí (DORA, AI Act
  čl. 14, GDPR čl. 22) [synthesis 01 osa C]. Formát: `<rozhodnutí> |
  <kdo navrhl> | <kdo schválil> | <datum> | <rationale>`.
- **ADR drafty** 3–5 kusů (API versioning, idempotency, transakční
  hranice, error model, sync vs eventy) [perspektiva 05].
- **Parking lot rezoluce** — každý odložený bod má owner + due date.
- **Score závaznosti per role** (1–5 Likert + rationale, AI-only weight
  max 0.5) [synthesis 02 bod 5].

### 2. Backend handoff (BE lead) [perspektiva 05]

- **Lintovaný OpenAPI 3.1** finální varianty (Spectral clean, examples,
  RFC 7807 errors, idempotency-key konvence). Raw spec v repu, ne PDF.
- **ERD diff** + breaking-change registr per consumer:

  ```
  | Field/Endpoint | Změna | Consumer | Owner | Migration window |
  |----------------|-------|----------|-------|------------------|
  | /v1/orders.id  | UUID→ULID | mobile-app, billing | @ne... | 2 sprinty |
  ```
- **Migration plan stub**: backfill, dual-write window, rollback,
  feature flag, odhad po 2-day capped spiku [synthesis 03 EM patch].
- **Contract test skeleton** (Pact / Schemathesis) — názvy testů.
- **Observability checklist**: metriky/traces/logs, owner dashboardů,
  alert thresholds, cardinality estimate.

### 3. Frontend handoff (FE lead) [perspektivy 04, 06]

- **Component manifest delta**: každá obrazovka označená `reused / new
  candidate / one-off`. Cíl pro evolve: >80 % reused, <10 % one-off.
- **Design tokens diff** proti Style Dictionary export + token
  compliance report (cíl pro evolve >90 %).
- **A11y baseline** = axe-core + manual keyboard test top 3 obrazovek.
  Critical/Serious = blocker pro „final" [perspektiva 11].
- **Figma↔commit lineage**: každá Figma frame má git commit hash;
  každá komponenta v repu má Figma node ID. Figma vizuál, kód
  implementace, oba mapují na stejné tokeny [perspektiva 06].
- **Repo + git history** (ne ZIP).

### 4. QA handoff (QA lead) [perspektiva 08]

- **3–5 BDD/Gherkin scénářů per accepted varianta**, min. 1 ne-happy
  path:

  ```gherkin
  Feature: Plan upgrade
    Scenario: Payment timeout during upgrade
      Given user on Pro plan with valid card
      When upgrade request times out at gateway
      Then user sees retry CTA, not duplicate charge
      And idempotency-key prevents second charge on retry
  ```
- **Test pyramide split** (70/20/10) s vlastníkem per vrstva.
- **Contract test skeleton** synced s BE Pactem.
- **Exploratory charter** (90 min: mission + areas + out-of-scope +
  deliverable).
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
- **AI Act risk-tier classification entry — Fáze C (final)** v risk registru
  (Unacceptable / High-risk / Limited / Minimal). Podepsáno DPO v Session 2
  per **dvoufázový protokol v0.3** (Útok 4 resolution; viz
  `03-pre-session-priprava.md` § Legal & Privacy Triage). Mandatory součásti
  Fáze C: data flow diagram, intended-use statement, human-oversight design
  (čl. 14), Annex IV technická dokumentace skeleton (high-risk). Provisional
  flag (Fáze A) **není validní** pro handoff package — pokud Fáze C chybí,
  pilot není kompletní a nezapočítává se do method-level success rate (ADR-0007).
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
[ ] DPIA podepsán (pokud aplikabilní), AI Act **Fáze C final classification** podepsaná DPO + Annex IV tech doc skeleton hotový
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
