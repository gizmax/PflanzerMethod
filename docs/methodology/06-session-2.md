# 06 — Session 2

> Status: v1.0. **Rozhodovací session, ne generativní** [perspektiva 03].
> 3 hodiny. Cíl: go / iterate / kill rozhodnutí s explicitním kritériem,
> handoff package do vývoje, nebo re-charter / kill log.

## Cíl Session 2

Vyhodnotit feedback ze scoring windowu, vyřešit top 3 sporné body podle
conflict-resolution playbooku, dát Decider's call (go / iterate / kill)
a předat handoff package. **Nepokračuje v generaci variant** — pokud panel
chce další varianty, signál je: re-charter, ne třetí session [perspektiva 01].

**Hard rule z Charteru**: max 2 sessions, pak buď go/kill, nebo escalation
k CPO. Třetí session = metoda selhala, learning loop, ne pokračování.

## Délka a energy

**3 hodiny**, ne 6 [perspektiva 03]. Druhá session je rozhodovací; pokud
trvá 6 h, tým nerozhodl, jen unavil. Doporučený slot: **9:00–12:00**
(decision-making peak). Bez oběda. Konec → handoff package distribuce
do 48 h.

## Účastníci

- **Stejní jako Session 1** (kontinuita interpretace; bez toho AI syntéza
  ztrácí kontext).
- **Decider povinně přítomen** [perspektiva 01]. Bez Decidera Session 2
  **neprobíhá** — viz **kanonický Decider eskalační protokol v ADR-0001**
  (Scenario A: posun max 5 pracovních dní, dál eskalace na CPO).
- **Security on-call** + **Legal on-call** ve volných slotech (ne celé 3 h),
  triggered pokud Critical flag eskaluje. Pre-read jejich triage update
  z mezi-sessions povinný.
- **EM** povinně pro capacity / dependency rozhodnutí.
- **Champion** (#17) pokud běží Coaching Kata loop pro pilot v BU
  [synthesis 03].

> Sanity check: > 8 lidí v 3h decision sessionu = paralýza. Konzultativní
> role mohou dorazit jen pro svůj blok.

## Detailní agenda

| Čas | Blok | Aktivita | Vede |
|-----|------|----------|------|
| 09:00–09:30 | **Recap + feedback agregace** | AI prezentuje aggregate by department: heatmap score × varianta × role; severity distribution; Discovery Debt Detector skóre; veto registr stav. **AI mluví neutrálně, fakta, ne interpretace** [perspektiva 03] | **AI vede prvních 20 min**, pak Facilitátor |
| 09:30–10:15 | **Conflict-resolution playbook na top 3 sporné body** | Pre-identifikované z mezi-sessions. Každý bod: 5 min context → 5 min návrh resolution → 5 min hlasování → 5 min commit / eskalace | Facilitátor + AI |
| 10:15–10:30 | **Break** | Pulsní check-in (1–5 prst) | — |
| 10:30–11:15 | **AI návrhy zapracování + variant convergence** | AI prezentuje, **jak** zapracovat top feedback do preferované varianty: konkrétní změny v UI, OpenAPI, A11y mitigations, ticket prediction adjustments. Panel reaguje, ne re-designuje | AI první draft, Facilitátor + role validují |
| 11:15–11:45 | **Decider's call: go / iterate / kill** | Decider rozhoduje s commitment indexem (0–100) z scoring window. Threshold definován v Charteru | **Decider** |
| 11:45–12:00 | **Handoff package preview + AI Act Fáze C sign-off** | Recap artefaktů, sign-off check, P2P gate stav, eskalace items. **DPO podepisuje AI Act final classification** (Fáze C dvoufázového protokolu — viz `03-pre-session-priprava.md` § Legal & Privacy Triage) s data flow diagramem, Annex IV skeletonem a human-oversight designem (per čl. 14). Bez Fáze C podpisu handoff package **není kompletní**. | Facilitátor + AI + DPO |
| **12:00** | **Konec** | — | — |

## Conflict-resolution playbook (top 3 sporné body)

[synthesis 01]. Mezi-sessions identifikuje top 3 cross-cutting konflikty;
Session 2 je řeší strukturovaně podle resolution patterns.

### Hierarchie závaznosti — strukturovaná místo binárního veta

[synthesis 01, blok D]:

1. **Critical risk = blocker** — varianta se nepokračuje:
   - Security STRIDE Critical
   - Legal AI Act high-risk + bez DPIA
   - A11y WCAG Critical/Serious na public-facing
   - EM capacity overrun bez champion alternativy
   - BE breaking change bez consumer alignment
   → **Session pivotuje na alt. variantu** nebo iterate s mitigation deadlinem.
2. **Yellow flag = viditelný warning v decision matrici, bez veta**:
   - UX usability debt
   - QA testability concern
   - CS load increase
   → Decider rozhoduje s plnou viditelností warningu; warning jde do
   decision logu.
3. **Score závaznosti** (0–1 s rationale field) — váhy pro non-blocker
   feedback. AI-only persona feedback **score deflation max 0.5**
   [synthesis 02].

**Anti-HiPPO**: Decider hlasuje **poslední**. Pokud Decider override-uje
silent-vote výsledek, dělá to **veřejně s rationale do decision logu**
[perspektiva 03].

### Konkrétní resolution patterns

[synthesis 01]:

- **Prototyp do prod**: evolve je default v Charteru (Track P + evolve,
  ADR-0005 v0.4) — winner varianta jde do produkce bez re-implementace.
  Samotný prod deploy je ale podmíněn Ship gate (quality gates ≥ 80/100)
  + kompletním sign-off paketem (FE + EM + Security + Legal + Platform + QA
  P2P checklist); do té doby žije varianta jen v sandboxu. Throw-away je
  explicit opt-in s rationale z Charteru (discovery-only pilot, audit-grade
  evidence separate od prod, regulated certified production).
- **Security veto + zadavatel push**: Pre-charter triage zachytí 80 %.
  Critical = pivot. L4 data v promptu = okamžitý stop.
- **EM kapacita vs business timeline**: T-shirt v session, story points
  až po 2-day capped spike. Persistence konflikt = eskalace mimo místnost.
- **PM + UX persona ownership**: shared artefakt; PM tie-breaker na scope,
  UX na flow. Persona doc podepsaný oběma.
- **FE + BE contract**: contract-first, OpenAPI shadow paralelní.
  Breaking-change registr.

## Decision gate

[perspektiva 01]:

### Go-criteria

- **Commitment index ≥ threshold z Charteru** (default 70/100).
- **Zero Critical** v veto registru.
- **Discovery Debt Detector ≤ 6** (≥ 7 = STOP).
- **WCAG Critical/Serious mitigated** pro public-facing + B2B nad
  250 zaměstnanců.
- **Capacity sign-off od EM** finalizovaný (žádné „posune se to").
- **P2P gate checklist** kompletní pro evolve, nebo throw-away flag.
- **Decider podepisuje** explicit go.

### Iterate criteria

- Commitment index 50–70 + jasné mitigation items s ownery a deadlines.
- ≤ 3 Critical s jasným resolution path do 1 týdne.
- Discovery Debt 3–6 (exploratory mode).
- Iterate cycle definovaný **úzce** (1 week, scoped scope), ne otevřený.

### Kill criteria

- **Commitment index < 50** napříč rolemi.
- **Kill criteria z Charteru splněny** (XYZ hypotéza falsifikována, kapacita
  zmizela, market shift).
- **Discovery Debt ≥ 7** + Decider odmítá discovery sprint.
- **Persistent Critical bez mitigation path** (Security high-risk, Legal AI
  Act non-compliance, BE breaking change bez consumer ownerů).
- **L4 data incident** v scoring windowu.

### Escalation path

- Capacity konflikt → CPO + VP Eng [perspektiva 01].
- Security/Legal Critical bez resolution → CISO + DPO.
- Decider conflict mezi BU → exec committee.
- Charter creep / scope drift → re-charter, nikoli třetí session.

## Score-based commitment

Každá zúčastněná role potvrzuje commitment level **0–3** [synthesis 03]:

| Level | Význam | Závazek |
|-------|--------|---------|
| **0** | Nesouhlas | Eskalace nebo opt-out z handoff scope |
| **1** | Read-only | Bere na vědomí, neúčastní se delivery |
| **2** | Active scoring | Bude reviewovat handoff artefakty, on-call pro otázky |
| **3** | Co-creation | Aktivně se podílí na delivery, owns dependency |

**Critical role** (PM, EM, Security, Legal pokud relevantní) musí mít **≥ 2**;
pokud kterákoli má 0, automatické iterate / re-charter.

**AI-assisted commitment** se započítává deflated max 0.5 (AI proxy nemá
podpis, jen briefing) [synthesis 02].

## Sign-off package (do 48 h od Session 2)

> **Track-aware (v0.4, per ADR-0020):** Session 2 output a sign-off package
> se liší podle Charter track. **Track P** (preferred ~80 %) → **winner
> varianta = běžící produkt v target prod repo**, sign-off package = audit
> trail. **Track S** (fallback ~20 %) → **winner varianta = precision spec
> ≥ 80/100 quality gate**, sign-off package = spec navigation + audit trail
> + 5-stage handoff ritual triggered.

### Track P sign-off package (GO call, default)

Winner varianta JE produkt. Žádný re-impl handoff k dev týmu — dev byl v room.

- **Winner kód v target prod repo** (PR-ready commit, quality gates ≥ 80/100:
  lint, types, tests, security, a11y, build, observability)
- **Scoped epic** (PRD-lite, 1 stránka): JTBD, persona, success metric,
  scope in/out, otevřené otázky [perspektiva 02].
- **Akceptační kritéria** v Gherkin (verifikační, ne implementační — kód
  už existuje), ≥ 1 negative scenario per flow.
- **Akceptovaný OpenAPI 3.1** lintovaný (Spectral) + 3–5 ADR + contract
  test passing (Pact / Schemathesis).

### Track S sign-off package (GO call)

Winner = **precision spec ≥ 80/100** + reference prototype z Session 1 +
5-stage handoff ritual triggered. Per
`tool/templates/precision-spec-track-s.md.template`.

- **Precision spec** sekce A–E (Functional INVEST-RA / Technical OpenAPI
  + ERD / Quality STRIDE + WCAG + AI Act / Implementation / Sign-off
  12-role matrix) ≥ 80/100 quality gate
- **Reference prototype** z Session 1 = Combined SoT s spec (anti-drift)
- **5-stage handoff ritual scheduled**: 90-min walkthrough → 5-day Q&A
  window → amendment protocol → first milestone review → T+30 embedded
  reviewer (per `07-handoff-do-vyvoje.md` Track S section)
- **Akceptační kritéria** v executable Gherkin (BDD scenarios runnable,
  ne prose), ≥ 1 negative scenario per flow.
- **Akceptovaný OpenAPI 3.1** lintovaný (Spectral) + 3–5 ADR + contract
  test skeleton (Pact / Schemathesis), passing dle spec verifikace.

### Společné pro Track P a Track S
- **Dependency Map**: feature → team → typ → required by → owner.
- **Tech debt flagy** s ownerem a planned-pay-down sprintem.
- **Updated business case + exec one-pager** pro CPO/board (problém,
  řešení, investice, expected impact, next milestone) [perspektiva 01].
- **DPIA artefakt** podepsaný DPO + AI Act tech doc skeleton (Annex IV)
  pokud high-risk.
- **Privacy Notice draft** + Legal basis statement per feature.
- **Measurement plan v1**: primary lagging + 2–3 leading + guardrail
  metrics; A/B test design + kill criteria; instrumentation deadline
  ship-2d [synthesis 02].
- **Support readiness checklist**: KB článek D-7, makra D-2, training,
  escalation [synthesis 02].
- **SLO baseline** + runbook stub + on-call assignment.
- **P2P (Prototype-to-Prod) checklist**: SBOM, secret scan, IaC v monorepu,
  observability, SLO, runbook, change advisory, DPIA, A11y human review
  [synthesis 02].
- **Audit log** session 1 + 2 s lidskou atribucí (DORA 7 let pro regulované).
- **Veto registr finalizovaný** + decision atribuce.
- **Reinforcement track**: T+7 ticket category check vs prediction;
  T+30 build progress + leading metric readout; T+60 retro + verbatim
  sample; T+90 lagging metric vs success criterion + churn cohort
  + learning loop do role catalogu [perspektiva 01, synthesis 02].

Pokud Decider's call = **ITERATE**:

- Scoped iterate package: konkrétní mitigation items, ownery, deadlines,
  re-Session 2 datum (ne otevřené, max 1 týden iterate cycle).
- Stávající artefakty zůstávají v hub repo; sandbox TTL prodloužen.

Pokud Decider's call = **KILL**:

- Kill log s rationale (které kill criteria z Charteru se naplnily).
- Learning loop entry: co metoda zachytila, co ne, update do role catalogu.
- Sandbox teardown, audit log retention per regulační framework.
- Charter archivovaný, exec one-pager s kill rationale.
