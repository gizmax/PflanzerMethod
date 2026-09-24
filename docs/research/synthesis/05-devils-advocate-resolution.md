# Devil's Advocate Resolution — odpověď na 12 útoků

> Mapuje, **co bylo opraveno v0.2 → v0.2.1** vs **co je akceptovaná známá
> limitace** vs **co odložené do v0.3**. Auditní stopa pro ujištění, že žádný
> útok zůstal bez explicitní odpovědi.

## Stav metody po resolution

- **v0.2** = stav po expertním panelu + syntéze + 5 ADR.
- **v0.2.1** = v0.2 + 3 nové ADR (0006 Champion bootstrap, 0007 Method-level
  Charter) + Method Charter (`docs/methodology/method-charter.md`) + 4 inline
  patche (Útoky 3, 6, 8, 10).
- **v0.3 backlog** = Útoky 4, 5, 7, 9, 11 — adresovány textuální revizí
  v dalším kole, nebo plánováno do toolu fáze 2.

## Resolution per útok

| # | Útok | Action | Kde |
|---|------|--------|-----|
| 1 | „8–10 PD" je marketing | **FULL FIX v0.3** | `03-pre-session-priprava.md` Krok 1a — kompletní **True Cost Worksheet** s per-role × per-phase tabulkou (3 profily: default ~32 PD souhrnně, regulated, audit-grade), reinforcement track T+7/30/60/90 a worksheet sign-off sekcí. Šablona pro vyplnění: `tool/templates/worksheets/true-cost-worksheet.md.template`. Pre-flight checklist vyžaduje podpis EM + sponzor + Method Steward. |
| 2 | Champion bootstrap paradox | **FIX v0.2.1** | **ADR-0006** — bootstrap režim (externí coach / rotace / tandem), Charter sekce „Champion provisioning", buddy povinný. |
| 3 | Decider escalation 3 verze | **FIX v0.2.1 (kritický bug)** | **ADR-0001 obsahuje kanonický protokol** (Scenario A/B/C). `06-session-2.md` a `08-edge-cases-a-rizika.md` na něj odkazují bez duplikace. Charter (ADR-0004) dostal sekci „Decider + eskalační řetězec" s odkazem na ADR-0001. |
| 4 | AI Act tier jako binary gate = audit theatre | **FULL FIX v0.3** | **Dvoufázový protokol** v `03-pre-session-priprava.md` § Legal & Privacy Triage: Fáze A (initial provisional pre-Session 1, `evidence-light` flag), Fáze B (interim review v mezi-session proti konkrétnímu variantu, viz `05-mezi-sessions.md`), Fáze C (final s data flow + Annex IV + human-oversight design v Session 2 / handoff, viz `06-session-2.md` + `07-handoff-do-vyvoje.md`). Pokud Fáze C chybí, pilot není kompletní (ADR-0007). |
| 5 | Sandbox guardrails slabé proti motivovanému sponzorovi | **DEFERRED v0.3** | Útok je správný, ale řešení (legal-binding throw-away kontrakt s cleanup-cost sankcí) je **org policy artefakt**, ne text metodiky. Plánováno: Charter (ADR-0004) v0.3 dostane sekci „Production by stealth sankce" s template smluvního ujednání. Zatím akceptováno jako známá slabina pro pilot. |
| 6 | Score deflation 0.5 = arbitrární | **FIX v0.2.1** | `02-role-catalog.md` sekce „Pravidla cross-cutting" obsahuje explicit *„0.5 je heuristika, ne kalibrovaný parametr; v0.3+ má method-level Charter ADR-0007 plánovat evidence-based kalibraci přes T+90 readout"*. Default threshold 70/100 v Charteru má stejný status. |
| 7 | „> 10 lidí" sanity check vs decision tree | **DEFERRED v0.3** | Útok přesný — chybí explicit rotation playbook v `04-session-1.md`. v0.3 přidá sekci *„Role rotation v Session 1: konzultativní role v 30-min slotech"* (analogicky k tomu, co `06` má pro Session 2). Zatím akceptováno jako známé omezení pro audit-grade profil. |
| 8 | DORA prompt audit pipeline chybí | **FIX v0.2.1** | `03-pre-session-priprava.md` pre-flight checklist přidává řádek *„Prompt audit pipeline active: vendor zero-retention DPA + corporate-side prompt custody chain (SIEM ingest, 7-letá retence, search by user@SSO + project tag); BEZ toho session = DORA non-compliant"*. Implementace pipeline (technická) = úkol pro fáze 2 (tool). |
| 9 | Pre-mortem TRIZ moc brzy | **DEFERRED v0.3** | Útok přesný — `04-session-1.md` má 15-min pre-mortem v 10:00 před vznikem variant. v0.3 plánuje **dvoufázový pre-mortem**: 5-min charter-level před Crazy 8s + 20-min variant-level po vibe-coding kola 1. Zatím akceptováno; facilitátor může v praxi odložit pre-mortem k 14:00 podle uvážení. |
| 10 | Anti-HiPPO bez external co-facilitator = paper authority | **FIX v0.2.1** | `02-role-catalog.md` role #3 Facilitátor dostal sekci *„Co-facilitator / externí Facilitátor — SHOULD pro audit-grade profil a high-stakes session; single-facilitator závislý na sponzoringu = paper authority"*. Audit-grade profil **vyžaduje** druhého facilitátora (z jiné BU nebo externí coach). |
| 11 | Reinforcement track bez budget commit | **FULL FIX v0.3** | ADR-0004 Charter sekce **„Reinforcement track — explicit budget commit"** s tabulkou per-readout (T+7/30/60/90: vlastník, min PD, akceptační kritérium, sankce za vynechání), Σ min 6 PD souhrnně default profil. Zrcadlově v `method-charter.md` § Reinforcement track (method-level + per-pilot). Audit-dotaz: M/N < 0.7 utilization → pilot „incomplete reinforcement", nezapočítaný do success rate per ADR-0007. |
| 12 | Method-level falsifying criterion | **FULL FIX v0.3** (povýšeno z v0.2.1 FIX po autoresearch round) | **ADR-0007** + `docs/methodology/method-charter.md` v0.3 (structural rewrite) + 3 nové ADR-y: **ADR-0011** (Decider profile = VP Eng Effectiveness, NE CPO; Default Sunset po T+18 mo bez explicit Keep memo), **ADR-0012** (Steward = 0.5-0.7 FTE dedikovaný Senior PdM, €100-150k OPEX; blind acceptance delegated na external EM panel; advocate-vs-measurer separation), **ADR-0013** (Pre-registration discipline ex-ante: fit criteria signed, statistical test α=0.10/power=0.80/MDE=0.5 pre-specified, Charter version pinned; Pflanzer Compliance Score 12 elementů ex-post; pilot < 10/12 = „Pflanzer-inspired", nezapočítává se do success metrics). Practitioner vs Academic track explicitně rozlišeny. Time-bounded kill criteria (N + T+X mo whichever first). Stopping-for-harm rule (≥ 25 % handoff collapse = kill immediately). Causal model (Theory of Why) explicitně artikulovaný. Detail v `docs/research/method-falsifiability/`. |

## Souhrn

- **5 FIX v0.2.1** (kritické, zůstávají v0.2.1 fixed): 2, 3, 6, 8, 10.
- **4 FULL FIX v0.3** (povýšeno z v0.2.1 status): 1, 4, 11 (z PARTIAL FIX), 12 (z FIX → structural rewrite).
- **3 DEFERRED v0.3** (akceptované známé limitace): 5, 7, 9.
- **0 REJECTED** — žádný útok jsme neodmítli jako nerelevantní.

### v0.3 changelog (Útoky 1, 4, 11)

- **Útok 1 → FULL FIX:** `docs/methodology/03-pre-session-priprava.md` Krok 1a
  + `tool/templates/worksheets/true-cost-worksheet.md.template`.
- **Útok 4 → FULL FIX:** `docs/methodology/03-pre-session-priprava.md`
  § Legal & Privacy Triage (Fáze A) + `05-mezi-sessions.md` (Fáze B)
  + `06-session-2.md` agenda + `07-handoff-do-vyvoje.md` § 8 Compliance handoff (Fáze C).
- **Útok 11 → FULL FIX:** `docs/decisions/0004-charter-as-mandatory-input.md`
  § Reinforcement track + `docs/methodology/method-charter.md`
  § Reinforcement track (method-level + per-pilot).

### v0.3 — autoresearch round resolution (Útok 12 → FULL FIX)

Devil's advocate Útok 12 měl status FIX v0.2.1 (ADR-0007 + method-charter).
Autoresearch round s 4 perspectives v `docs/research/method-falsifiability/`
(01 Method Steward, 02 Data analyst, 03 Skeptický VP, 04 Akademik)
identifikoval **3 fatální slabiny** původní v0.2.1 formulace:

1. **Decider profile** (CPO/DoE) — politicky exponovaný, tenure 2.3y, sunk-cost
   asymmetry → metoda zombifikuje.
2. **Steward role** (10 % FTE, EM bez headcount) — budget vapor, conflict
   of interest (advocate-as-measurer).
3. **Falsifiability** — fit criteria post-hoc redefinovatelné, statistický
   test nepre-registered, drift nedetekovatelný.

**v0.3 changes** (povýšení Útok 12 na FULL FIX):

- **ADR-0011** — Method Decider = VP Eng Effectiveness (2 levely pod CTO),
  tenure 3+ let; **Default Sunset po T+18 mo** bez explicit Keep memo;
  Method Steward early-kill veto; stopping-for-harm rule.
- **ADR-0012** — Method Steward = 0.5-0.7 FTE dedikovaný Senior PdM,
  €100-150k OPEX/rok, Engineering Excellence CoE; **separation of advocate
  and measurer** (blind external EM panel pro acceptance); selekční kritéria
  + conflict-of-interest disclosure.
- **ADR-0013** — **Pre-registration protocol** (fit criteria + statistical
  test signed pre-Session 1, Charter version pinned) + **Pflanzer Compliance
  Score** (12 elementů, ex-post Steward audit; < 10/12 = pilot není Pflanzer
  pilot).
- **`method-charter.md` v0.3 structural rewrite:**
  - Practitioner vs Academic track explicitně rozlišeny.
  - Time-bounded kill criteria (N=3/T+9 mo, N=8/T+15 mo, N=12/T+18 mo default Sunset).
  - Causal model (5 interventions → 5 mediators → 4 outcomes) explicitně
    artikulovaný.
  - Success threshold tabulka s instrumentation columns (start/end events,
    data source, cadence).
  - Comparison baseline: full population mining + survival analysis +
    propensity matching + Project Class Taxonomy.
- **Synthesis docs** v `docs/research/method-falsifiability/`:
  - `05-conflict-matrix.md` — top 7 konfliktů mezi perspectives + resolutions.
  - `06-key-themes.md` — 8 cross-cutting themes.
  - `07-recommendations.md` — P0-P3 priority backlog (24 action items).
- **Template:** `tool/templates/pre-registration.yaml.template` (OSF-style).

**Out-of-scope tohoto PR (P1-P3 follow-ups):**
- ADR-0014 (Composite PflanzerIndex finalized formula).
- ADR-0015 (Fork governance).
- ADR-0010 (Method post-mortem disclosure).
- `docs/methodology/baseline-collection-playbook.md`, `per-pilot-instrumentation.md`,
  `leading-indicators.md`, `method-dashboard-template.md`, `method-steward-raci.md`,
  `acceptance-review-protocol.md`.
- Academic track instrument validation, IRB review, multi-org replication.

## Co devil's advocate hodnotil POZITIVNĚ

Skeptik sám pojmenoval 5 silných stránek metody:
1. **Throw-away default v ADR-0005** — *„governance, kterou většina metod
   neměla odvahu napsat"*.
2. **Discovery Readiness Gate explicit refusal** — *„vzácná epistemická
   poctivost"*.
3. **Hierarchie závaznosti místo binárního veta** — *„inženýrská odpověď
   na sociální problém"*.
4. **Pre-flight triage tracks** — *„žádná jiná 'rapid' metoda nemá 48–72 h
   pre-read jako MUST"*.
5. **Anti-pattern „Pflanzer pro Pflanzer"** — *„antithesis SAFe sales pitch"*.

## Co se nedá opravit (akceptované limitations)

Skeptik sám pojmenoval 5, s nimiž souhlasíme jako s **core design tradeoffs**:

1. Pflanzer nemůže urychlit governance deeper than pre-flight (DPIA 3 týdny zůstanou 3 týdny).
2. Pflanzer závisí na maturity AI vibe-coding tools (jejich outage = metoda nefunguje).
3. Pflanzer je drahý pro single-team scope (pod tu hranici → LDJ, ne Pflanzer).
4. Pflanzer netvoří user research; jen ho vyžaduje na vstupu.
5. Pflanzer nemůže vyhrát political battle, kde sponzor chce, aby metoda prohrála.

Tyto akceptujeme — jsou v souladu s `01-filozofie-a-kdy-pouzit.md` anti-patterns
a s **Method Charterem** (ADR-0007) jako kill triggery.

## Method-level acknowledgement

> *„Metoda, která je sama o sobě o falsifikaci hypotéz (XYZ z Pretotypingu),
> se nemá vlastní falsifying criterion."* — devil's advocate Útok 12.

Akceptováno a opraveno v ADR-0007 + `method-charter.md`. Pflanzer si nyní
nárokuje vlastní disciplínu se sunset gate po 6 / 10 pilotech a Method
Steward rolí. Audit committee má odpověď.
