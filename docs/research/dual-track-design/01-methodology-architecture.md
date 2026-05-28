# Dual-Track Architecture — Track P (Product) vs Track S (Spec)

> Strukturální návrh dual-track modelu Pflanzerovy metody po user
> clarification z 2026-05-28 (*„V ideálním případě chci aby výstupem
> Pflanzer metody byl hotový produkt, proto je tam na začátku developer.
> Pokud tam ale nebude, bude možné mít jako výstup precizní speccu a ta
> se dá na vývoj. Ale není to preferovaná cesta."*).
>
> **Cíl dokumentu:** dvě tracky strukturálně definovat tak, aby Track P
> (Product) byl jednoznačně **preferovaná default cesta** a Track S (Spec)
> existoval jako **dokumentovaný fallback** — ne escape hatch, ne SDD-lite
> rebranding.
>
> Status: draft v0.1 (research). Po sign-off Tom → ADR-0005 rewrite +
> ADR-0020 new + sweep across 11 docs.

---

## TLDR (5 řádků)

Pflanzer ode dneška má dvě tracky: **Track P** (Product, default, 80 % cases)
kde dev tým je v room od minuty 0 a output Session 2 je běžící produkt v target
prod repo; a **Track S** (Spec, fallback, 20 % cases) kde dev tým není dostupný
in-room a output Session 2 je *precision spec* (winner varianta + Gherkin
acceptance + OpenAPI 3.1 + ADR set + commitment-signed handoff). Track S je
dokumentovaný fallback, **ne preferovaná cesta**: aktivuje se jen pokud projekt
splní 1 ze 4 hard triggerů (distributed dev ≥3 TZ, regulatorní gate vyžadující
separate impl, AI Act High-risk certified prod, sponsor mandate spec-as-deliverable).
Bez triggeru → Track P, nebo metoda neproběhne. Decider's voice: *„Track S je
kompromis, ne volba."*

---

## 1. Track P — Preferred (Dev-in-room → Product)

### 1.1 Definice (single sentence)

**Track P je default Pflanzer profile, kde dev tým (#4 FE/Vibe-coding lead +
#5 BE/API lead z `02-role-catalog.md`) je fyzicky/synchronně v room po celou
Session 1 (3–6 h), staví spolu s AI co-pilotem 1–3 paralelní produkční-ready
varianty, a winner z Session 2 jde D11-D14 přímo do production deployu — bez
re-implementace.**

Output cyklu: **běžící produkt na production URL** + sign-off package
(audit trail, ne re-impl spec).

### 1.2 Pre-flight requirements (hard MUST)

Před Session 1 svoláním musí být splněno **VŠECHNO** z následujícího:

| Požadavek | Vlastník | Validace |
|-----------|----------|----------|
| Discovery Readiness Gate ✅ (persona ≤6 mo, JTBD signed, OST v0 ≥60 %) | PM | `03-pre-session-priprava.md` Krok 0 |
| Triage tracks (Security + Legal + Platform) ✅ | Security + DPO + DevOps | `03-pre-session-priprava.md` Krok 0a |
| Charter signed (per ADR-0004) **s flagem `track: P`** | Decider + Sponsor | viz § 7.1 Charter section sample |
| **Dev tým committed v plné kapacitě po celý Session 1**: #4 FE + #5 BE (pokud projekt má BE) — jmenovitě, jeden senior + jeden mid OK, ne junior delegate | EM | EM signs off in Charter Capacity commit table |
| **EM kapacita podepsána** pro D11-14 production hardening (max 2 PD per dev lead) | EM | Charter Capacity commit |
| Sandbox spec ✅ — pre-approved Terraform module + Approved AI tool list | DevOps | Platform Triage |
| Decider mandate writeable + Sponzor commit time-box (60 min Day 0 + 3 h Session 1 + 3 h Session 2) | CPO/Sponsor | Charter signature |

**Bez kteréhokoli MUST → Track P nestartuje.** Eskalace na: dev unavailable →
viz § 2.2 Track S triggers; ostatní → odložit projekt.

### 1.3 Session 1 mechanika (3 h in-room)

Per `04-session-1.md`, **s explicit Track-P modifikací**:

- **Builder lead = dev v room** (ne external vibe-coder, ne AI samostatně).
  Dev lead přebírá AI co-pilot driver-seat: 70 % keystrokes = dev's, 30 % =
  AI suggestion accept. Tím vzniká **production-grade familiarity by minute 1**.
- **BE shadow agent** generuje OpenAPI 3.1 paralelně, ale **#5 BE lead validuje
  v real-time** — žádný „BE byl AI proxy". OpenAPI v Session 1 je production
  contract draft, ne speculation.
- **Stack v Session 1 = stack v production target repu**. Vibe-coding tool
  selection per Charter (Bolt, v0, Lovable, Claude Code) **musí mapovat na**
  existing target stack (např. e-shop Next.js → v0; greenfield internal tool →
  Bolt; React Native → Cursor). Bez stack-match Track P se pozastaví, jdi
  Track S.
- **Code review v real-time**: během silent voting bloku (15:30–14:00) dev
  lead provede 30-min self-review winner candidate kódu; flaguje fundamental
  issues PŘED Session 2.
- **Sandbox URL = staging-grade prostředí**, ne "pure prototype". Sandbox
  guardrails (24h TTL, watermark, network default-deny) zůstávají, ale kvalita
  kódu už v sandboxu = production-grade (ESLint pass, Vitest defaults, type
  safety).

### 1.4 Session 2 output (winner → production)

Per `06-session-2.md`, **s Track-P specifikací**:

- **Decider's call**: Go / Iterate / Kill nad **konkrétní winner variantou** —
  ne nad spec. Vidí běžící produkt v sandbox URL na velkém screenu, navigates
  flow live.
- **Winner branch merge plan** (committed v Session 2 closing 5 min): dev lead
  + EM podepisují merge target branch v production repu + first-pass PR title.
- **D11-14 plan** (committed v Session 2 closing 5 min): production hardening
  scope (observability hookup, monitoring dashboards, edge case bug fix,
  CI/CD pipeline integration). **Není re-implementation** — je to polish.
- **Quality gates ≥ 80/100** = production prerequisite, ne *prototype hardening
  checklist*. Per `07-handoff-do-vyvoje.md` Promote-to-prod gate aplikováno
  immediately, ne *„later when we productize"*.

### 1.5 Sign-off package (audit trail, ne re-impl spec)

Per glossary.md `sign-off package` definici. V Track P obsahuje:

- Decision log s human attribution (DORA / AI Act čl. 14 / GDPR čl. 22)
- Preference matrix + score závaznosti per role + veto registr
- ADR set (3–5 ks: API versioning, idempotency, transactional boundaries,
  error model, sync vs events)
- Gherkin acceptance criteria (per varianta + winner)
- AI Act Fáze C final classification (signed DPO)
- Compliance pakety (audit-grade jen): DPIA, Annex IV skeleton, Privacy Notice
- **`#prod` git tag**: commit hash on production branch, deploy timestamp

**Sign-off package NENÍ re-implementation spec.** Dev tým si podle něj
nestaví produkt — ten je už deployed. Sign-off package slouží audit +
post-launch reinforcement (T+7/30/60/90 material).

### 1.6 Reinforcement T+7/30/60/90 = production monitoring

Per `07-handoff-do-vyvoje.md` § Champion model. Track-P specifika:

| Milník | Owner | Deliverable | Track-P interpretation |
|--------|-------|-------------|------------------------|
| T+7 | CS + Champion | Ticket check vs prediction | **Real production tickets**, ne sandbox simulace |
| T+30 | Data + Champion | Leading metric readout, retro | **Real user behavior**, A/B winner cohort |
| T+60 | Champion + EM | Capacity actual vs estimate | **Real DORA stats** (deploy frequency, lead time) |
| T+90 | Decider + PM + EM + Champion | Lagging metric vs success criterion | **Go/Iterate/Kill** formal v ADR per ADR-0001 |

### 1.7 Kdy volit Track P (fit criteria)

Track P **je default**. Volíš ho, pokud platí **VŠECHNY** následující:

1. Dev tým (#4 + #5) je v BU dostupný a EM committu kapacitu na 3 h Session 1
   + 3 h Session 2 + max 5 PD D11-14 hardening.
2. Stack v Session 1 mapuje na production target stack (žádný v0.dev pro
   production Next.js, žádný Bolt pro production Java).
3. Žádný hard trigger pro Track S (viz § 2.2).
4. Projekt fit criteria z `01-filozofie-a-kdy-pouzit.md` ≥ 5 z 7 ano.

**Track P je „happy path"** — žádný explicit signature potřebný (defaultně
aktivní v Charter template).

### 1.8 Throw-away v Track P (explicit opt-in, 3 výjimky)

Per `glossary.md` throw-away definici:

- **Track P + evolve** (default lean, 80 %): produkt jde do prod, D11-14
  hardening, T+7 production monitoring.
- **Track P + throw-away** (discovery-only pilot): produkt funguje, ale
  zahodíme — žádný production deploy. Vzácný case, typicky pro:
  - XYZ falsifikace pilot bez business commit
  - „Bake-off" mezi 2 fundamentally different architecturami
  - Internal training case study

Throw-away v Track P **NENÍ default** — flag v Charter explicit opt-in.

---

## 2. Track S — Fallback (No-dev-in-room → Precision Spec)

### 2.1 Definice (single sentence)

**Track S je fallback Pflanzer profile, kde dev tým (#4 + #5) není dostupný
in-room a Session 1 mechanika vyrábí 1–3 paralelní varianty s explicit
intent dodat *precision spec* — ne deployable code — pro budoucí dev tým,
který implementuje v separate track (typicky 2–8 týdnů po Session 2).**

Output cyklu: **winner spec + sign-off package** (acceptance criteria,
OpenAPI 3.1, ADR set, Gherkin scenarios, ADR-grade compliance artefakty).
Žádný production deploy v rámci Pflanzer cyklu.

### 2.2 Pre-flight requirements (hard MUST)

| Požadavek | Vlastník | Validace |
|-----------|----------|----------|
| Discovery Readiness Gate ✅ | PM | identické s Track P |
| Triage tracks ✅ | Security + DPO + DevOps | identické s Track P |
| Charter signed **s flagem `track: S`** | Decider + Sponsor | viz § 7.1 Charter section sample |
| **Track S justification signed**: 1 ze 4 hard triggers below | EM + Sponsor | Charter § Track S justification (mandatory) |
| **Escalation plan**: kdy a jak (pokud) recover na Track P | Decider | Charter § Track S recovery |
| **Implementation team named**: jméno + ETA (nesmí být *„dev team TBD"*) | EM | Charter Capacity |
| Decider mandate writeable + Sponzor commit time-box (60 min Day 0 + 3 h Session 1 + 3 h Session 2) | CPO/Sponsor | Charter signature |

#### Track S hard triggers (musí platit ≥1)

1. **Dev tým distributed (≥3 time zones)** — Pflanzer's 6-person-room axiom
   selhává. Per `01-filozofie-a-kdy-pouzit.md` anti-pattern *„single-team scope"*,
   ale s rozšířením: pokud projekt **vyžaduje** distributed dev (např. follow-
   the-sun ops, near-shore vendor), Track S je correct route.

2. **AI Act High-risk + certified production** — některé high-risk use cases
   (HR systems, biometrics, critical infrastructure) vyžadují *certified
   production deploy* s separate impl track (Annex IV technical documentation,
   conformity assessment per čl. 43, EU declaration of conformity). Track P
   produkt může být *staging-grade*, ale certification path je separate. Tady
   Track S vyrábí spec, který certification body může assess.

3. **FDA / IEC 62304 / DO-178C / PSD2 SCA** (regulatorní) — production = certified
   production. Medical device class III, avionics SW, banking payment SCA flows.
   Pflanzer artefakt **nemůže být** v target prod repu (separate certification
   track). Track S vyrábí *certified-grade spec*.

4. **Sponsor mandates spec-as-deliverable** (commercial / contractual) —
   typicky:
   - Multi-vendor integration kontrakt (spec = exhibit in commercial agreement)
   - Legacy modernization s novým dev týmem (knowledge transfer artifact)
   - Acquisition due diligence (spec = asset valuation evidence)

**Pokud žádný z 4 triggers neplatí, ale dev tým „není dostupný":**
**odložit Pflanzer**, vyřešit dev availability s EM. Není Track S volba —
je to deferral.

### 2.3 Session 1 mechanika (3 h in-room)

Per `04-session-1.md`, **s explicit Track-S modifikací**:

- **Builder lead = facilitator + AI** (žádný dev in room). AI co-pilot
  generuje varianty s **spec-first orientation**: každá UI komponenta má
  inline JSDoc komentář s expected props, každý API endpoint má OpenAPI
  schema entry, každý state transition má Gherkin scenario draft.
- **BE shadow agent** generuje OpenAPI 3.1 v *contract-first mode* —
  agresivnější schema validation, RFC 7807 errors explicit, idempotency
  conventions documented. Output je „dev-team-ready contract", ne working code.
- **Stack v Session 1 = REFERENCE STACK**, ne target production stack. Vibe-
  coding tool je *visualization aid*; kód v sandboxu **se neexpektuje** sloužit
  jako production starting point. Disclaimers explicit (watermark + „REFERENCE
  IMPLEMENTATION — DO NOT DEPLOY").
- **Spec-first review v real-time**: během silent voting bloku, facilitator
  vede 30-min review of **OpenAPI + Gherkin + ADR drafts** (ne kódu).
  Reviewuje s pomocí prxy „dev voice" (AI roleplay #4 a #5 reactions).
- **Sandbox URL** = preview-only (watermark, no-deploy-allowed). 24h TTL
  agresivnější (žádné prodloužení do Session 2 — pre-Session-2 export do
  static artifact + screen recording).

### 2.4 Session 2 output (winner spec + sign-off package)

Per `06-session-2.md`, **s Track-S specifikací**:

- **Decider's call**: Go / Iterate / Kill nad **konkrétní winner spec** —
  ne nad běžícím produktem (ten je reference jen). Vidí spec dokumenty +
  reference UI (screen recording / static screenshots) na velkém screenu.
- **Implementation team handoff plan** (committed v Session 2 closing 10 min):
  - Implementation team named (musí existovat per pre-flight, ne TBD).
  - Handoff meeting datum (max T+5 days post Session 2).
  - Spec versioning protocol (spec v1.0 frozen at Session 2 closure;
    amendments require explicit re-Charter per ADR-0013 § Amendments).
- **Quality gates pro spec ≥ 80/100** (různé od Track P, viz § 2.6).

### 2.5 Handoff to dev team (kdy, kdo, jak)

**Kdy:** T+5 days post Session 2 — handoff meeting (90 min slot,
implementation team + Champion + PM + Decider attend).

**Kdo:** Implementation team (named in Charter pre-flight) + #17 Champion
(z Session 1+2, signed Decision log; vlastní Coaching Kata loop pro
implementation phase).

**Jak:**
- **Spec walkthrough** (30 min): Champion prezentuje sign-off package.
- **Live Q&A** (30 min): implementation team has reading time T-2 days
  before; comes with prepared questions.
- **Commitment ceremony** (15 min): implementation team lead signs
  „Spec received, ETA Y/N pro X weeks". Pokud ETA nesouhlasí s Charter
  expectation → re-Charter (escalation na sponsor).
- **Reinforcement track activation** (15 min): T+7 ticket review proxy
  → in Track S replaced with *„T+7 spec questions check"* (kolik clarifications
  implementation team request); T+30 / T+60 / T+90 = implementation progress
  checkpoints.

**Spec versioning during implementation:**
- Spec v1.0 frozen at Session 2.
- Implementation team požádá clarifications via formal protocol (spec issue
  tracker, není ad-hoc Slack).
- Clarifications resolved Champion + original Decider; resolution committed
  as „Spec v1.0-clar-N" amendments.
- **Spec drift detection**: pokud implementation deviates > 20 % from spec
  (LOC ratio in covered files vs original spec coverage), Method Steward
  flag → re-Charter required.

### 2.6 Quality gates pro spec (≥80/100)

Different od Track P quality gates (které jsou *production code gates*).
Track S má **spec-grade gates**:

| Gate | Threshold | Validation method |
|------|-----------|-------------------|
| OpenAPI 3.1 lintovaný | Spectral clean (0 errors, ≤3 warnings) | Automated |
| Gherkin acceptance | ≥3 scenarios per accepted variant + ≥1 negative path | Manual review by QA #8 |
| ADR set | ≥3 ADRs (API versioning, idempotency, error model min) | Manual review by Solution arch #18 |
| Token compliance (if UI in spec) | ≥90 % token-mapped components | Style Dictionary audit |
| A11y baseline (if UI in spec) | WCAG 2.2 AA mapping per component | Axe-core static + manual review |
| Compliance artefakty (audit-grade jen) | DPIA + Annex IV + Privacy Notice + SBOM + secret scan | DPO sign-off |
| Decision log human attribution | 100 % decisions attributed (DORA / AI Act / GDPR) | Method Steward audit |
| Test coverage seed | Gherkin → test framework mapping documented | QA review |

**Aggregate score ≥ 80/100** = spec is „dev-team-ready". Below = iterate
Session 2 (limit 1 iterate per ADR-0001 Scenario C).

### 2.7 Reinforcement T+7/30/60/90 = spec implementation monitoring

| Milník | Owner | Track-S deliverable | Sankce |
|--------|-------|---------------------|--------|
| T+7 | Champion + Implementation lead | **Spec clarification rate**: <5 clarifications/week = OK; >10 = spec quality flag | Method Steward warning |
| T+30 | Champion + Data | **Implementation progress vs Spec milestones**: % completed vs Charter expectation | Re-Charter trigger if <50 % expected |
| T+60 | Champion + EM | **Spec drift detection**: LOC ratio in covered files vs original spec coverage | >20 % drift = Method Steward flag |
| T+90 | Decider + PM + EM + Champion + Implementation lead | **Production deploy** (first prod commit s `#prod` tag, OR justified delay with new ETA) | Go / Iterate / Kill ADR |

**Klíčový rozdíl od Track P:** v Track S **first production deploy je
T+90 outcome**, ne T+0. Pflanzer cyklus dodá *spec*, dev tým dodá *prod*.

### 2.8 Kdy volit Track S (fit criteria)

Track S **je fallback**, ne první volba. Volíš ho, pokud platí **VŠECHNO**
z následujícího:

1. **Splňuje aspoň 1 ze 4 hard triggers** (§ 2.2).
2. **Sponzor je informován** že Track S = 2-3× delší time-to-prod vs Track P
   (T+90 vs T+14), 2× vyšší effort total (Pflanzer 10 PD + Implementation
   N × PD vs Pflanzer 10 PD inclusive).
3. **Implementation team je named** (ne TBD).
4. **Recovery plan dokumentovaný** — kdy/jak (pokud) recover na Track P.

**Track S vyžaduje explicit sponsor signature** v Charter § Track S
justification. Není default.

### 2.9 Throw-away v Track S (vzácný case)

Per `glossary.md` throw-away definition + Track S context:

- **Track S + spec-as-deliverable** (default Track S, 95 %): spec se implementuje
  a deploy ✓ (T+90 outcome).
- **Track S + throw-away** (rare, ~5 %): spec se zahodí — typicky:
  - Spec slouží jako *due diligence artefakt* (acquisition decision = no-go,
    spec se neimplementuje).
  - „Bake-off" mezi 2 fundamentally different specifikacemi pro budoucí
    rozhodnutí (winner z Pflanzer = input do exec committee, ne to-be-built
    feature).
  - Audit-grade evidence collection separate od prod (compliance show-case).

Throw-away v Track S **NENÍ default** — flag v Charter explicit opt-in.

---

## 3. Decision tree — kdy P vs S

```
START — Discovery Readiness Gate ✅
  │
  ▼
Q1: Splňuje projekt 1 ze 4 hard Track S triggers?
  ├─ Distributed dev (≥3 TZ)?
  ├─ AI Act High-risk + certified production?
  ├─ FDA / IEC 62304 / DO-178C / PSD2 SCA?
  └─ Sponsor mandates spec-as-deliverable (multi-vendor / legacy modernization
     s novým týmem / acquisition due diligence)?
  │
  ├─ ANO (alespoň jeden) → Q2 (Track S preparation)
  └─ NE → Q3 (Track P preparation)
  │
  ▼ (Q2 — Track S preparation)
Q2a: Implementation team named v Charter pre-flight?
  ├─ NE → Charter not signable; resolve before Pflanzer kick-off
  └─ ANO → Q2b
Q2b: Recovery plan dokumentovaný (kdy/jak recover na Track P)?
  ├─ NE → Charter not signable; nepovoluje long-term Track S lock-in
  └─ ANO → **TRACK S start** (Charter signed s `track: S` + justification)
  │
  ▼ (Q3 — Track P preparation)
Q3a: Dev tým (#4 FE + #5 BE pokud projekt má BE) committed v plné kapacitě
     po celý Session 1 (3-6 h) + Session 2 (3 h) + D11-14 hardening (max 5 PD)?
  ├─ NE → Q3b
  └─ ANO → Q3c
Q3b: Proč není dev tým committed? (escalation diagnosis)
  ├─ EM capacity > 80 % committed PI → odložit do dalšího PI
  ├─ Dev tým na PTO / re-org → odložit do availability window
  ├─ Sponsor odmítá uvolnit commit features → eskalace na CPO
  └─ Pokud Q3b resolution > 4 týdny → consider Track S (re-route přes Q1)
                                       BUT only if 1 ze 4 triggers also triggers
  │
  ▼
Q3c: Stack v Session 1 mapuje na production target stack?
  ├─ NE → Track P pozastaven; resolve stack mismatch (vibe-coding tool selection)
  │        nebo odložit Pflanzer
  └─ ANO → **TRACK P start** (Charter signed s `track: P`, default)
```

**Pravidlo:** Track S **nesmí být easy escape hatch** pro „dev tým nemá čas".
Bez 1 ze 4 hard triggers je *„dev tým nemá čas"* = **odložit projekt**, ne
přepnout na Track S. Tím se chrání preferovanost Track P.

---

## 4. Honest tension audit

### 4.1 Riziko #1 — Track S konverguje s SDD

**Pojmenování:** Pokud Track S fallback = *„spec-driven precision spec for
later impl"*, v čem je Pflanzer Track S jiný než Spec Kit / Kiro / OpenSpec /
Tessl?

**Analýza:**

| Dimenze | SDD (Kiro / Spec Kit) | Pflanzer Track S |
|---------|----------------------|------------------|
| Generovací cyklus | Sequential: Vision → PRD → Architecture → Tasks → Impl | Single-pass: pre-flight → Session 1 (3 h) → mezi-session → Session 2 (3 h) → handoff |
| Stakeholder model | PM proxy (sponsor delegate; sequential review queues) | All cross-functional roles **fyzicky v room**: Session 1 + Session 2 |
| Decision attribution | Implicit (spec is consensus document; no Decider) | **Explicit anti-HiPPO Decider model** (per ADR-0001) — Decider hlasuje poslední |
| Conflict resolution | Async via PR comments; queue delays | In-room conflict resolution playbook (`06-session-2.md` § Top 3 sporné body) |
| Pre-flight gates | Často skipnuté (PRD je Round 0) | Discovery Readiness Gate + Triage tracks (Security + Legal + Platform) mandatory |
| AI co-pilot role | Spec generator (one-shot) | Variant generator (paralelně 1-3) + shadow agents (OpenAPI, A11y, ticket prediction) |
| Reinforcement loop | Žádný v defaultu | T+7/30/60/90 mandatory per Charter (ADR-0004) |
| Audit-grade compliance | Optional; bolted on per project | Built-in: AI Act Fáze A/B/C protocol, DORA 7y retention, AI Act Annex IV, DPIA |

**Unikátní diferenciátory Track S vs SDD:**

1. **Anti-HiPPO Decider model** — SDD nemá ekvivalent. Pflanzer Track S
   garantuje Decider hlasuje poslední, decision log atribuuje človĕka.
   Lu, Yuan & McLeod (2012) 41 % bias reduction.

2. **Functional variants jako reference** — Track S **stále staví 1-3
   varianty v Session 1** (jen ne production-grade); SDD obvykle dělá
   spec-of-one. Decider má visual artifact pro decision, ne abstract spec.

3. **Cross-functional in-room synthesis** — Track S si zachovává Pflanzer
   core: Security + Legal + UX + QA + DevOps + Data + CS proxy v jedné
   místnosti. SDD má každou roli v separate review queue.

4. **Discovery + Triage pre-flight gates** — Track S blokuje Session 1
   bez signed gates. SDD obvykle skip-uje.

5. **Reinforcement loop** — Track S T+7/30/60/90 mandatory. SDD nemá.

**Verdikt:** Track S **není SDD-lite rebranding**. Track S je *„Pflanzer
process s spec output místo code output"*. Process integrity (cross-fn in-room
+ anti-HiPPO + pre-flight + reinforcement) je nezměněna.

**Mitigace risk:** Track S documentation explicit framing: *„Track S vyrábí
spec stejnou cross-fn process disciplinou jako Track P vyrábí kód. Track S
spec **JE** Pflanzer artifact (kvalita spec ↑ kvůli session disciplině),
ne **bypass** Pflanzer process."*

### 4.2 Riziko #2 — Adoption gravity (fallback se stane defaultem)

**Pojmenování:** Pokud Track S fallback existuje, organizace s low PD
commit (typický enterprise pattern) ho **začne používat jako default**,
nikdy se ke Track P nedostane. Po 18 měsících metoda *„adapted to our
context"* = pouze Track S, Track P zmizí.

**Struktura risk:**

- **EM gravity**: EM je incentivized to minimize friction; *„dev nemá čas
  na Session 1"* je nejjednodušší cesta. Bez gating Track S se stane default.
- **Sponsor gravity**: sponsor často nechce committi 3 h v room; *„napíšete
  mi spec, já to schválím"* je preferovaný workflow.
- **Org culture gravity**: matrix orgs s strong PM function gravity vždy
  k spec-as-deliverable.

**Struktural mitigace (4 vrstvy):**

1. **Charter signature gate** (per § 7.1):
   - Track S volba vyžaduje **2 separate signatures**: EM + Sponsor.
   - **Track S justification** must reference 1 ze 4 hard triggers explicit.
   - Charter template má Track S fields blanket (vyplnit nebo blokovat sign).

2. **Compliance Score penalty** (per ADR-0013):
   - Pflanzer Compliance Score 12-element checklist přidá element #13:
     *„Track designation v Charter explicit + justification signed pro
     Track S"*. Track S bez justification = score deflation.
   - Method Steward audits ratio Track S / Track P per BU per quarter;
     pokud BU > 50 % Track S, **automatic Method Decider review**
     (intervention: dev availability constraint, fundamental org fit issue,
     nebo Track S misuse).

3. **PflanzerIndex formula penalty** (per ADR-0014):
   - PflanzerIndex Time Ratio component v Track S = computed against
     **T+90 production deploy timestamp**, ne T+14. Tj. Track S projects
     have inherently lower Time Ratio scores → method-level success rate
     reflects realistic delay cost.
   - Acceptance Blind Panel score: Track S spec quality is judged separately
     by external implementation EM (not by Track S sponsor) → no fake
     acceptance theater.

4. **Method Steward quarterly review**:
   - Per ADR-0012 § Operating model, Method Steward 15 % capacity =
     Charter maintenance + ADR shepherding.
   - **New responsibility**: quarterly review of Track S / Track P ratio
     per BU + Method Decider memo if anomaly. Per ADR-0011 emergency review
     trigger upgrade: *„Track S ratio > 50 % per BU"* = leading indicator
     for early-kill review.

**Verdikt:** 4-layer mitigation je strukturální, ne dependent na facilitator
discipline. Adoption gravity by se měla v T+18 sunset checkpoint manifestovat
jako kill signal (BU adopted Track S as default → org doesn't fit Pflanzer →
sunset is correct outcome).

### 4.3 Riziko #3 — ADR-0005 throw-away/evolve dichotomy

**Pojmenování:** ADR-0005 (current) říká throw-away vs evolve binary choice
per project. Po dual-track introduction, jak se mapuje?

**Analýza 4 kombinace:**

| Kombinace | Status | Frequency | Příklad |
|-----------|--------|-----------|---------|
| Track P + evolve | **Default lean** | ~75 % | e-shop eshop, internal dashboard, CRM feature |
| Track P + throw-away | Explicit opt-in (per ADR-0005 throw-away condition #1: discovery pilot) | ~5 % | XYZ falsifikace pilot, internal bake-off |
| Track S + spec-as-deliverable | Track S default | ~18 % | Multi-vendor integration, legacy modernization, FDA/IEC class III |
| Track S + throw-away | Rare | ~2 % | Acquisition due diligence (no-go decision), spec bake-off pro exec |

**Verdikt:** Throw-away/evolve a P/S **jsou ortogonální dimenze** — 4
kombinace jsou validní, každá s vlastním use case. Není nested.

**Důsledek pro ADR-0005 rewrite:** nový ADR-0005 musí pojmenovat všechny 4
kombinace + flag matrix v Charter template (track: P/S × output: evolve/
throw-away).

---

## 5. ADR-0005 rewrite proposal (full new text)

```markdown
# ADR-0005 — Track output mode: evolve vs throw-away (v0.3.1 invert)

**Status:** Superseded by v0.3.1 (this revision)
**Date:** 2026-05-28
**Supersedes:** ADR-0005 v0.1 (default = throw-away, 2026-05-05)
**Context source:** User clarification 2026-05-28; output consistency audit
(`docs/research/output-consistency/03-synthesis.md`); dual-track methodology
architecture (`docs/research/dual-track-design/01-methodology-architecture.md`).

## Kontext (revize)

ADR-0005 v0.1 definoval *„default = throw-away, produkce se píše znovu jako
specs-driven re-implementation"*. Po user clarification 2026-05-28
(*„výstupem Pflanzer metody je hotový produkt, programátor je v room od minuty 0"*)
a output consistency auditem (12 P0 míst protiřečí marketing claim *„kód
v produkci za 14 dní"*) byla původní decisional logic **invertována**.

Současně byl strukturálně zaveden **dual-track model** (Track P + Track S,
viz ADR-0020). Output mode (evolve / throw-away) a track designation
(P / S) jsou **ortogonální dimenze** s 4 validními kombinacemi.

## Rozhodnutí

### Track designation × output mode = 2 × 2 matrix

| Track × Output | Status | Frequency | Charter requirement |
|----------------|--------|-----------|---------------------|
| **Track P + evolve** | **Default lean** (v0.3.1 default) | ~75 % | žádný explicit flag; Charter `track: P, output: evolve` |
| **Track P + throw-away** | Explicit opt-in | ~5 % | Charter `output: throw-away` + reason 1 ze 3 (discovery pilot / audit evidence / cert prod separate) |
| **Track S + spec-as-deliverable** | Track S default | ~18 % | Charter `track: S` + Track S justification 1 ze 4 hard triggers (per ADR-0020) |
| **Track S + throw-away** | Rare | ~2 % | Charter `track: S, output: throw-away` + Track S triggers AND output throw-away reason |

### Track P + evolve (default)

- Winner varianta z Session 2 jde **přímo do produkce**.
- D11-14 production hardening (observability, monitoring, edge cases) —
  ne re-implementace.
- Quality gates ≥ 80/100 = production prerequisite, ne *prototype hardening*.
- `#prod` git tag = audit-trail v sign-off package.

### Track P + throw-away (discovery pilot)

3 výjimky kde produkt funguje, ale zahodíme:
1. **Discovery-only pilot** — XYZ falsifikace, žádný production commit.
2. **Audit-grade evidence collection** separate od prod (compliance show-case).
3. **Bake-off** mezi 2 fundamentally different architecturami.

Charter flag: `output: throw-away`. Sandbox TTL extension povolen pro
evidence preservation; žádný production deploy.

### Track S + spec-as-deliverable (Track S default)

- Winner spec z Session 2 jde k implementation teamu (T+5 handoff meeting).
- Spec v1.0 frozen at Session 2; amendments per spec issue tracker.
- Reinforcement T+7/30/60/90 = implementation progress monitoring.
- T+90 outcome = first production commit `#prod` tag.

### Track S + throw-away (rare)

Spec se zahodí — typicky:
1. **Acquisition due diligence** (M&A decision = no-go, spec se neimplementuje).
2. **Spec bake-off pro exec committee** (winner = input pro feature decision,
   ne to-be-built feature).
3. **Audit-grade evidence collection** separate od prod (compliance show-case).

Charter flag: `output: throw-away` + Track S justification.

## Důsledky

**Pozitivní:**
- **Removes contradiction**: marketing claim *„kód v produkci za 14 dní"*
  a methodology jsou konzistentní. Default cycle = Track P + evolve = produkt
  v prod.
- **Honest about fallback**: Track S + spec-as-deliverable je dokumentovaný
  fallback, ne hidden anti-pattern.
- **Throw-away preserved** pro 3 (Track P) + 3 (Track S) legitimate exceptions.
- **Charter explicit**: každý pilot musí declare track + output mode upfront,
  no ambiguity.

**Negativní:**
- **Charter complexity**: dva flags místo jednoho (track + output).
- **Compliance Score upgrade**: ADR-0013 12-element checklist potřebuje
  upgrade na 13 elementy (track designation + justification).
- **Method-level metrics complication**: Track S projects mají inherent
  T+90 timeline vs Track P T+14; PflanzerIndex aggregation per ADR-0014
  musí akumulovat per-track separately.

**Mitigace:**
- **Charter template default**: `track: P, output: evolve` (no explicit signature
  required). Jen non-default kombinace require explicit justification.
- **Tool support (Slice 2)**: `/pflanzer-charter` wizard prompts for track
  selection at minute 0, refuses to proceed without explicit declaration.
- **ADR-0013 upgrade**: Compliance Score element #13 = *„Track designation
  v Charter + justification (Track S only)"*; element #11 (handoff package)
  bifurcated by track (Track P = production code + sign-off package;
  Track S = spec + sign-off package).

## Update existující dokumentace

- `glossary.md` § evolve, throw-away — upgraded with Track × Output matrix.
- `00-tldr.md` — explicit *„default = Track P + evolve, alternativy
  dokumentovány v ADR-0005 + ADR-0020"*.
- `00-lean-pflanzer.md` — Track P + evolve baseline; Track S poznámka jako
  *„viz ADR-0020 pro fallback scenario"*.
- `01-filozofie-a-kdy-pouzit.md` decision tree — Track S triggers integrated.
- `03-pre-session-priprava.md` Charter template — track + output fields.
- `07-handoff-do-vyvoje.md` — bifurcated Track P sign-off + Track S handoff.
- `method-charter.md` — XYZ metric per track (`time-to-production-deploy`
  Track P vs `time-to-spec-completion` Track S, both lead to T+90 prod commit
  measurement).

## Reference

- ADR-0001 — Decider model (preserved unchanged).
- ADR-0004 — Charter mandatory input (Charter template upgrade triggered).
- ADR-0011 — Method Decider profile (no change).
- ADR-0012 — Method Steward (new quarterly review responsibility).
- ADR-0013 — Pre-registration + Compliance Score (element #13 added).
- ADR-0014 — PflanzerIndex formula (per-track aggregation noted).
- **ADR-0020** — Dual-track model (new, see separate ADR).
- User clarification 2026-05-28: *„Výstup z Pflanzer metody je hotový produkt."*
- Output consistency audit: `docs/research/output-consistency/03-synthesis.md`.
- Savoia, A. *The Right It* — pretotyping vs prototyping (still relevant for
  Track P + throw-away discovery pilots).
```

---

## 6. ADR-0020 proposal (full new text)

```markdown
# ADR-0020 — Dual-track model: Product (P) vs Precision Spec (S)

**Status:** Proposed (v0.3.1 P0)
**Date:** 2026-05-28
**Context source:** User clarification 2026-05-28 (Track P preferred,
Track S fallback). Synthesizes output consistency audit
(`docs/research/output-consistency/03-synthesis.md`), spec-driven friction
quantification (`docs/research/spec-driven-vs-pflanzer/02-friction-quantification.md`),
methodology architecture (`docs/research/dual-track-design/01-methodology-architecture.md`).

## Kontext

Pflanzer v0.3 mlčí o scénáři, kdy dev tým (#4 FE + #5 BE) není dostupný in-room
po celý Session 1. Output consistency audit identifikoval 12 míst napříč
dokumentací, kde se říká *„handoff package pro dev team re-implementaci"* —
což je v rozporu s user claim *„výstup je hotový produkt, programátor je v room
od minuty 0"*.

User clarification (2026-05-28):
> *„V ideálním případě chci aby výstupem Pflanzer metody byl hotový produkt,
> proto je tam na začátku developer. Pokud tam ale nebude, bude možné mít
> jako výstup precizní speccu a ta se dá na vývoj. Ale není to preferovaná
> cesta."*

Bez explicit dual-track model:
- **Marketing claim** *„kód v prod za 14 dní"* je v rozporu s methodology
  v 7 z 11 souborů.
- **Adoption gravity** vede k slow degradation: BUs s low dev availability
  začnou používat *„Pflanzer pro spec"* default, methodology drift.
- **No clear fallback** pro projekty, které mají legitimate Track S triggers
  (distributed dev, certified production, audit-as-artifact).

## Rozhodnutí

Pflanzer v0.3.1 zavádí **dual-track model**:

### Track P (Product) — Preferred (default)

**Definice:** Dev tým (#4 + #5) je in-room po celý Session 1; winner varianta
z Session 2 jde D11-14 do production target repu jako evolve (per ADR-0005).
Output = běžící produkt + sign-off package (audit trail).

**Fit (default):** všechny standard Pflanzer projects bez Track S triggers.
~80 % use cases per `00-lean-pflanzer.md` declared scope.

**Pre-flight requirements:**
- Discovery Readiness Gate ✅
- Triage tracks ✅
- Charter signed s flagem `track: P`
- **Dev tým committed** (EM signs off Capacity table)
- Stack v Session 1 = production target stack

**Session 1 mechanika:** dev lead = AI co-pilot driver-seat (70 % keystrokes
dev's, 30 % AI suggestion accept). BE shadow agent generuje OpenAPI 3.1
paralelně, BE lead validates real-time.

**Session 2 output:** Winner branch merge plan + D11-14 plan committed at
session closure. Quality gates ≥ 80/100 = production prerequisite.

**Reinforcement:** T+7/30/60/90 = real production monitoring (tickets,
metrics, DORA stats, lagging metric).

### Track S (Spec) — Fallback (explicit opt-in)

**Definice:** Dev tým není dostupný in-room; Session 1 vyrábí 1-3 reference
variants s explicit intent dodat *precision spec* pro budoucí implementation
team (T+5 handoff meeting). Output = winner spec + sign-off package.

**Fit:** ~20 % use cases. Hard triggers (musí platit ≥1):
1. Dev tým distributed (≥3 time zones).
2. AI Act High-risk + certified production (separate impl track required).
3. FDA / IEC 62304 / DO-178C / PSD2 SCA (regulatorní gate).
4. Sponsor mandates spec-as-deliverable (multi-vendor / legacy modernization
   / acquisition due diligence).

**Pre-flight requirements:**
- Discovery Readiness Gate ✅
- Triage tracks ✅
- Charter signed s flagem `track: S` + **Track S justification (1 ze 4
  hard triggers)** + **Implementation team named** + **Recovery plan
  documented** (kdy/jak (pokud) recover na Track P)
- 2 separate signatures: EM + Sponsor (anti-adoption-gravity guardrail)

**Session 1 mechanika:** facilitator + AI = builder lead. Vibe-coding tool
= visualization aid (REFERENCE IMPLEMENTATION watermark). Sandbox preview-only,
no-deploy-allowed.

**Session 2 output:** Winner spec + implementation team handoff plan
(T+5 meeting datum). Quality gates ≥ 80/100 spec-grade (OpenAPI lintovaný +
Gherkin scenarios + ADR set + token compliance + A11y baseline + Compliance
artefakty + Decision log human attribution).

**Reinforcement:** T+7/30/60/90 = implementation progress monitoring.
T+90 outcome = first production commit `#prod` tag (or justified delay).

## Decision tree

Per `docs/research/dual-track-design/01-methodology-architecture.md` § 3.

**Klíčové pravidlo:** Track S **není easy escape hatch** pro *„dev tým
nemá čas"*. Bez 1 ze 4 hard triggers je *„dev tým nemá čas"* = **odložit
projekt**, ne přepnout na Track S.

## Důsledky

**Pozitivní:**
- **Marketing-methodology coherence**: claim *„kód v prod za 14 dní"*
  konzistentní s Track P (default).
- **Honest fallback**: Track S triggers explicit, justification mandatory,
  no methodology drift.
- **Adoption gravity mitigated**: 4-layer mitigation (Charter signature
  gate + Compliance Score #13 + PflanzerIndex per-track penalty + Method
  Steward quarterly review).
- **SDD differentiation explicit**: Track S vyrábí spec stejnou cross-fn
  process disciplinou (anti-HiPPO Decider + Triage gates + reinforcement),
  ne SDD-lite.
- **Compatible s existing ADRs**: 0001 (Decider) / 0011 (Method Decider) /
  0012 (Method Steward) / 0013 (Pre-registration) / 0014 (PflanzerIndex)
  preserved s small upgrades.

**Negativní:**
- **Documentation overhead**: 11 dokumentů needs sweep (per § 7 implications
  table).
- **Charter complexity**: track + output flags + Track S justification + recovery
  plan. ~30 min Charter prep navíc pro Track S projects.
- **Compliance Score upgrade**: ADR-0013 element #13 + element #11 bifurcation.
- **PflanzerIndex aggregation**: per-track separation needed; method-level
  metrics report 2 series (Track P time-to-prod T+14, Track S time-to-prod T+90).
- **Tooling implication**: Slice 2 (`/pflanzer-charter`) wizard needs track
  decision tree front-loaded; cannot be afterthought.

**Mitigace:**
- **Default = Track P + evolve**: no explicit signature required, friction
  preserved for ~75 % cases.
- **Track S justification template**: pre-filled forms with 4 trigger options;
  pick + sign = ~10 min effort.
- **Method Steward quarterly review** automated: dashboard alert if BU > 50 %
  Track S ratio.
- **Tool wizard** front-loads track decision tree; user cannot bypass.

## Update existující dokumentace

Per `docs/research/dual-track-design/01-methodology-architecture.md` § 7.

## Reference

- User clarification 2026-05-28.
- Output consistency audit: `docs/research/output-consistency/03-synthesis.md`.
- Friction quantification SDD vs Pflanzer:
  `docs/research/spec-driven-vs-pflanzer/02-friction-quantification.md`.
- ADR-0001, 0004, 0005, 0011-0014 (preserved + upgrades).
- `docs/research/dual-track-design/01-methodology-architecture.md` (this work).
```

---

## 7. Charter section sample (track designation)

### 7.1 Track designation section (mandatory v0.3.1)

V Charter template (`docs/methodology/03-pre-session-priprava.md` § Krok 1
Business Charter, or ADR-0004 template) přidat sekci:

```markdown
## Track designation (mandatory, v0.3.1 per ADR-0020)

**Track:** [P] preferred default | [S] fallback (1 ze 4 triggers below)
**Output mode:** [evolve] default | [throw-away] explicit opt-in (per ADR-0005)

### If Track P (preferred):

**Dev tým commitment (EM sign-off mandatory):**

| Role | Jméno | Seniority | Session 1 commit (3-6 h) | Session 2 commit (3 h) | D11-14 hardening commit (max 5 PD) |
|------|-------|-----------|--------------------------|------------------------|-------------------------------------|
| #4 FE / Vibe-coding lead | <jméno> | Senior / Mid | ✅ | ✅ | ✅ (PD: __) |
| #5 BE / API lead (if projekt má BE) | <jméno> | Senior / Mid | ✅ | ✅ | ✅ (PD: __) |

**Stack matching:**
- Vibe-coding tool: <Bolt / v0 / Lovable / Claude Code / other>
- Target production stack: <Next.js / React Native / Java / Python / other>
- Stack mapping verified by FE lead: ✅ (signed: <jméno, datum>)

**EM signature (Capacity commit + Dev availability):**
- EM: <jméno>, datum: <YYYY-MM-DD>, signature.
- Capacity: <X PD per cycle including D11-14 hardening>.
- PI commit status: <% committed v current PI>, buffer 25 % ✅/❌.

### If Track S (fallback):

**Track S justification (mandatory, 1 ze 4 triggers):**

- [ ] Trigger 1 — Distributed dev (≥3 time zones).
      Detail: <BU name, team locations, why in-room nemožné>
- [ ] Trigger 2 — AI Act High-risk + certified production (čl. 6 + Annex III).
      Detail: <use case, AI Act tier from Fáze A, why certified prod separate>
- [ ] Trigger 3 — FDA / IEC 62304 / DO-178C / PSD2 SCA (regulatorní gate).
      Detail: <regulator, framework, certified production requirement>
- [ ] Trigger 4 — Sponsor mandates spec-as-deliverable.
      Detail: <multi-vendor contract / legacy modernization / acquisition DD>

**Implementation team named (mandatory):**

- Implementation team lead: <jméno>, BU: <BU>, ETA: <YYYY-MM-DD>.
- Implementation team capacity: <X PD>, span: <weeks>.
- Handoff meeting date (T+5 post Session 2): <YYYY-MM-DD>.

**Escalation plan / recovery to Track P (mandatory):**

Recovery trigger condition: <např. *„pokud distributed dev získá co-location
v IP iteration N+2"*; *„pokud regulatorní compliance achieved by Q3 2027"*>.
Recovery decision authority: <Decider name>.
Recovery checkpoint: <T+30 / T+60 / T+90 / nikdy (permanent Track S)>.

**Why NOT Track P (honest):**

Free-text 2-3 věty: *„Pokus o Track P selhal protože ___. Track S je
explicit kompromis, ne preference. Recovery plan v § Recovery."*

**EM + Sponsor double signature (anti-adoption-gravity guardrail):**

- EM: <jméno>, datum, signature: __
- Sponsor: <jméno>, datum, signature: __
```

---

## 8. Cross-doc implications table

Per dokument, what changes after ADR-0005 v0.3.1 + ADR-0020 v0.3.1:

| # | Soubor | Changes required | Effort |
|---|--------|------------------|--------|
| 1 | `00-tldr.md` | Primary/fallback framing v intro; "default = Track P + evolve" explicit; 5 weak frází sweep (per output consistency audit) | 30 min |
| 2 | `00-lean-pflanzer.md` | Track P jako default lean explicit; Track S poznámka *„viz ADR-0020 pro fallback"*; recipe Day 5 *„Session 1 · vibe"* check OK (Track P implicit) | 20 min |
| 3 | `01-filozofie-a-kdy-pouzit.md` | Decision tree update (Q1: 4 Track S triggers added before fit criteria); anti-patterns Section *„Sponzor odmítá uvolnit commit features"* mapped to Track S re-route Q3b | 40 min |
| 4 | `02-role-catalog.md` | #4 + #5 become harder MUST for Track P (currently DOPORUČENÁ pro UI/BE změny); add v0.3.1 note *„Track P: #4 + #5 MUST be in-room. Track S: #4 + #5 optional (facilitator + AI substitute)"* | 30 min |
| 5 | `03-pre-session-priprava.md` | Charter template (Krok 1) přidává track designation section (§ 7.1); Charter signature lifecycle updated (track flag immutable post Session 1 start unless re-Charter); True Cost Worksheet updated per track (Track P 10 PD per default; Track S 10 PD Pflanzer + N PD implementation separate) | 90 min |
| 6 | `04-session-1.md` | Sekce *„Účastníci"* bifurcated by track; *„Builder lead = dev v room"* (Track P) vs *„Builder lead = facilitator + AI"* (Track S); *„Stack v Session 1 = stack v production"* (Track P) vs *„Stack = REFERENCE STACK, watermark"* (Track S); *„Throw-away vs evolve flag explicit per varianta"* changes to *„Track × output flag per Charter"* | 90 min |
| 7 | `05-mezi-sessions.md` | Prototype hub spec bifurcated by track: Track P = staging-grade preview; Track S = REFERENCE IMPL preview-only watermark; scoring focus per track (Track P = code quality; Track S = spec completeness) | 60 min |
| 8 | `06-session-2.md` | Decider's call options unchanged (Go/Iterate/Kill); handoff package bifurcated by track (per `07`); quality gates bifurcated (production gates Track P vs spec gates Track S); resolution patterns *„Prototyp do prod"* changed to *„Track × output combination per Charter"* | 60 min |
| 9 | `07-handoff-do-vyvoje.md` | **Major rewrite**: file becomes `07-handoff-and-deploy.md`; Track P sections: sign-off package + D11-14 production deploy plan; Track S sections: spec handoff to implementation team (T+5 meeting) + reinforcement = impl progress monitoring; existing Promote-to-prod gate preserved (used in both tracks at slightly different timing) | 150 min |
| 10 | `08-edge-cases-a-rizika.md` | New edge cases: *„Dev tým unavailable mid-Session 1"* (Track P → halt or Track S re-route); *„Implementation team disappears mid-Track-S"* (re-Charter or Kill); *„Track S spec drift > 20 % during implementation"* (Method Steward flag → re-Charter); *„Track P forcing without proper dev commitment leads to spec-driven late-stage rework"* | 60 min |
| 11 | `09-srovnani-existujici-metody.md` | Track S vs SDD diferenciátory explicit (per § 4.1 of this doc); table column *„Pflanzer"* split na *„Pflanzer Track P"* + *„Pflanzer Track S"*; *„Track S != SDD-lite"* explicit framing | 90 min |
| 12 | `glossary.md` | Add: *„Track P"*, *„Track S"*, *„Track designation"*, *„Implementation team handoff"* (Track S only); evolve / throw-away upgraded with 2×2 matrix | 30 min |
| 13 | `method-charter.md` | XYZ hypothesis bifurcated by track (`time-to-production-deploy` T+14 Track P vs `time-to-spec-completion` T+5 Track S leading to T+90 prod); Compliance Score upgrade (element #13 track designation; element #11 bifurcated) | 60 min |
| 14 | `ADR-0004` | Charter template embedded in ADR — track designation section added | 30 min |
| 15 | `ADR-0005` | Full rewrite per § 5 of this doc | 30 min |
| 16 | `ADR-0013` | Compliance Score 12-element → 13-element (element #13: track designation + justification); element #11 bifurcated by track | 20 min |
| 17 | `ADR-0014` | PflanzerIndex per-track aggregation note; method-level report 2 series (Track P vs Track S) | 20 min |
| 18 | `ADR-0020` (new) | Full text per § 6 of this doc | created |
| 19 | `tool/templates/pre-registration.yaml.template` (P2 tool) | Add `track: P/S` field; add `track_s_justification` (nullable if Track P); add `implementation_team_named` (Track S mandatory) | 15 min (template) |
| 20 | `website/index.html` + `1-pager.html` | Sweep per output consistency audit (5 P0 marketing fixes); add *„Track P + evolve = default"* tooltip + *„Track S fallback dokumentován pro distributed teams"* footnote | 60 min |

**Total sweep effort estimate:** ~16 hours (~2 PD), spread across 1 week
after ADR sign-off.

---

## 9. Open questions pro Tom

### 9.1 Strategické otázky

1. **Naming.** Track P / Track S je technicky neutrální. Alternatives:
   - *„Product mode"* / *„Spec mode"* — explicit value claim
   - *„Default profile"* / *„Distributed profile"* — focus on org context
   - *„In-room"* / *„Distributed"* — focus on geographic reality

   Preferenc?

2. **Track S adoption gravity tolerance.** Method Steward quarterly review
   threshold *„BU > 50 % Track S = automatic Method Decider review"*. Je
   50 % správný threshold? Alternatives: 30 % (agresivnější), 70 % (lenientější).

3. **Track S → Track P recovery default.** Charter Recovery checkpoint =
   T+30 / T+60 / T+90 / never. Default? Návrh: T+60 (give 2 months for
   org constraints to resolve, then re-evaluate).

4. **Method-level XYZ hypothesis aggregation.** Per ADR-0014 PflanzerIndex
   formula. Aggregation rules po dual-track:
   - **Option A**: Pflanzer success = mean(Track P PflanzerIndex). Track S
     reported separately. ← preferred per Track P preferenc
   - **Option B**: Pflanzer success = weighted mean(0.8 × Track P + 0.2 ×
     Track S) — reflects observed ratio.
   - **Option C**: Pflanzer success = mean(both tracks pooled). ← masks
     track differences

5. **Track S in `00-lean-pflanzer.md` mention.** Současné lean-pflanzer.md
   říká *„audit-grade = upgrade"*. Po dual-track:
   - **Option A**: lean-pflanzer.md = Track P + evolve only; Track S = full
     `method-charter.md` reference. ← preserves lean simplicity
   - **Option B**: lean-pflanzer.md = mentions Track S existence + ADR-0020
     reference, no Track S detail. ← honest about fallback existence

### 9.2 Tactical otázky

6. **Charter sign-off blocking for Track S.** § 7.1 says *„EM + Sponsor
   double signature"*. Is this too friction-heavy? Alternative: EM signs
   solo + Method Steward audits ex-post (lower friction, but adoption
   gravity guardrail weaker).

7. **Sandbox guardrails per track.** Track S has watermark *„REFERENCE
   IMPLEMENTATION — DO NOT DEPLOY"*. Strong enough? Or also
   technical block (e.g., sandbox auto-revoke on `deploy` keyword in commit
   message)?

8. **Track S Session 1 length.** Same as Track P (5-6 h)? Or shorter
   (3-4 h) reflecting *„no dev hands-on"* nature?

9. **Slice 2 (tool) decision tree implementation.** `/pflanzer-charter` wizard
   per CLAUDE.md fáze 2. Wizard flow:
   - **Option A**: Track decision first (Q1-Q3), then Charter fields
   - **Option B**: Charter fields first, derive track at end
   - **Option A is preferred** per anti-adoption-gravity (user must explicitly
     navigate track decision tree, can't accidentally end up in Track S).

10. **Track P throw-away vs Track S throw-away distinction.** Both exist
    (per ADR-0005 rewrite § 5). Risk: user confusion. Resolution:
    - **Track P + throw-away** = product built but discarded (discovery
      pilot)
    - **Track S + throw-away** = spec built but discarded (DD artifact /
      bake-off)
    
    Clear enough? Or rename Track P throw-away to *„discovery"* and Track S
    throw-away to *„artifact-only"*?

### 9.3 Compatibility otázky

11. **ADR-0001 Decider eskalační protokol (Scenario A/B/C).** Změna?
    - Scenario A (Decider missing in Session 2): protokol unchanged across
      tracks.
    - Scenario B (Decider can't decide): same.
    - Scenario C (Iterate exhausted): pro Track S potřebuje *„Iterate"*
      definition adaptation (Track S iterate = spec revision, not new build).
    - **Verdict:** ADR-0001 zůstává. Minor addendum: *„Iterate per track:
      Track P = code iteration, Track S = spec revision."*

12. **ADR-0007 Method-level Charter sunset criteria.** Per ADR-0011
    default sunset T+18. Po dual-track:
    - **Per track sunset?** Track P + Track S evaluated separately.
    - **Combined sunset?** Methodology as whole.
    - **Preferred:** Combined sunset, but Method Steward T+12 review reports
      per-track success rates separately (transparency).

13. **ADR-0011 emergency review trigger.** Currently: 2+ leading indicators
    breach threshold > 60 days, OR ≥ 25 % piloty handoff collapse. Add:
    - **New trigger**: *„BU > 50 % Track S ratio for > 90 days"* (anti-
      adoption-gravity safety).

14. **ADR-0013 Compliance Score element bifurcation.** Element #11 (handoff
    package) needs upgrade:
    - **Track P element #11**: *„Sign-off package + #prod git tag exists"*.
    - **Track S element #11**: *„Spec sign-off package + T+5 handoff
      meeting executed + Implementation team commitment signed"*.
    - New **element #13**: *„Track designation v Charter explicit;
      Track S justification valid (1 ze 4 triggers + EM+Sponsor signatures)"*.

15. **Backward compat existing pilots.** Pilots started before v0.3.1:
    - **Option A**: Re-classify (forensic Track P / Track S labeling based on
      observed dev availability). ← retroactive complexity
    - **Option B**: Pre-v0.3.1 piloty marked *„unfgrandfathered"*, excluded
      from method-level success rate post-v0.3.1. ← clean cutoff
    - **Preferred:** Option B (clean cutoff). Method Steward T+12 review
      separates pre/post v0.3.1 cohorts.

---

## 10. Reference

### Documents informing this architecture

- `docs/methodology/00-lean-pflanzer.md` (default lean, 14 dní)
- `docs/methodology/01-filozofie-a-kdy-pouzit.md` (fit criteria + anti-patterns)
- `docs/methodology/02-role-catalog.md` (18 rolí; #4 + #5)
- `docs/methodology/03-pre-session-priprava.md` (Charter template; pre-flight gates)
- `docs/methodology/04-session-1.md` (Session 1 mechanika)
- `docs/methodology/05-mezi-sessions.md` (scoring window)
- `docs/methodology/06-session-2.md` (Session 2 decision)
- `docs/methodology/07-handoff-do-vyvoje.md` (sign-off + deploy)
- `docs/methodology/glossary.md` (just-created definice)
- `docs/methodology/method-charter.md` (audit-grade overhead)
- `docs/decisions/0001-decider-model.md` (Decider escalation protocol)
- `docs/decisions/0004-charter-as-mandatory-input.md` (Charter template)
- `docs/decisions/0005-throwaway-vs-evolve-prototype.md` (current; targeted for rewrite)
- `docs/decisions/0011-method-decider-profile-and-sunset-default.md` (Method Decider profile)
- `docs/decisions/0012-method-steward-operational-scope.md` (Method Steward 0.5-0.7 FTE)
- `docs/decisions/0013-pre-registration-and-compliance-score.md` (12-element checklist)
- `docs/decisions/0014-composite-pflanzerindex-formula.md` (PflanzerIndex)

### Research underpinning

- `docs/research/output-consistency/03-synthesis.md` (audit 12 P0 fixes,
  user clarification 2026-05-28)
- `docs/research/spec-driven-vs-pflanzer/02-friction-quantification.md`
  (SDD multi-round friction vs Pflanzer single-pass; § 4 *„Where SDD legitimately
  wins"* informs Track S triggers; § 5 *„Where Pflanzer dominates"* informs
  Track P preferenc)
- `docs/research/external-validation/04-synthesis.md` (industry benchmarks
  AWS 7×, Stripe 12×, MIT 95 %, Boehm 1×→100×)
- `docs/research/competitive/` (positioning vs SDD ecosystem, ADR-0015)

### External primary literature

- Boehm 1981, Boehm-Papaccio 1988 (defect cost amplification)
- UXPin 2024 (62 % devs redo design due to handoff)
- Demi 2021 IET Software (traceability decay)
- Knapp 2016 *Sprint* (Decider model — preserved in both tracks)
- Lu, Yuan & McLeod 2012 (anti-HiPPO 41 % bias reduction — preserved)
- Teasley 2002 (co-location *„half calendar time"* — Track P core claim)
- Peng et al. 2023 (AI co-pilot +56 % greenfield — both tracks)
- METR 2025 (AI co-pilot -19 % brownfield legacy — caveat)
- MIT NANDA Q3/2025 (95 % pilot zero ROI — Pflanzer aims to be the 5 %)

---

*Document length: ~1050 lines. Generated: 2026-05-28. Author: senior
methodology architect sub-agent in PflanzerMethod project. Status: draft
v0.1 (research), pending Tom sign-off → trigger ADR-0005 rewrite + ADR-0020
creation + 11-doc sweep.*
