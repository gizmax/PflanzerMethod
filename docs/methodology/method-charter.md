# Pflanzer Method-Level Charter

> Trvalý dokument. Pflanzer si nárokuje vlastní disciplínu — XYZ hypotézu,
> falsifying criterion, kill criteria. Bez toho je *methodology that exempts
> itself from its own discipline* (devil's advocate Útok 12, ADR-0007).
>
> **v0.3 update (2026-05-16):** structural rewrite po autoresearch round
> „method-falsifiability" (4 perspektivy: Method Steward, Data analyst,
> Skeptický VP, Akademik). Změny supersedují části ADR-0007 — viz ADR-0011
> (Decider profile + Sunset), ADR-0012 (Steward operational scope), ADR-0013
> (Pre-registration + Compliance Score). Detail v `docs/research/method-falsifiability/`.

## Status

- **Verze metody:** v0.3 (post-autoresearch falsifiability round)
- **Datum charteru:** 2026-05-16
- **Method Decider:** **VP Engineering Effectiveness** (nebo equivalent: Head of
  Engineering Excellence, Head of Process Portfolio), pozice 2 úrovně pod
  CTO/CIO, tenure profile 3+ roky, JD explicitně zahrnuje sunset authority.
  **NESMÍ být CPO** (per ADR-0011 rationale).
- **Method Steward:** **0.5-0.7 FTE dedikovaný Senior PM** v Engineering Excellence
  CoE, €100-150k OPEX/rok. Selekční kritéria + conflict-of-interest disclosure
  per ADR-0012. Direct reporting line k Method Decider.

## Practitioner vs Academic track (v0.3)

Charter explicitně rozlišuje **dvě perspektivy validace**:

| Track | Timeline | Sample | Authority | Charter scope |
|-------|----------|--------|-----------|--------------|
| **Practitioner** (business decision) | T+18 mo default Sunset checkpoint | N=12 pilots NEBO T+18 mo whichever first | Method Decider + Process Portfolio Review | **Primary scope** — všechna pravidla níže pokud není označeno „Academic" |
| **Academic** (publication-grade validation) | 3-5 let, ~12-20 pilots napříč 3+ organizace / 2+ industries | Multi-org replication, ablation pilots, mediation analysis | External academic partner, peer-review process | Opt-in side track. Pokud org má akademického partnera (univerzita, výzkumný institut), spustí se paralelně. |

**Audit dotaz mapping:**
- *„Funguje Pflanzer v naší organizaci?"* → Practitioner track odpovídá po T+18 mo.
- *„Je Pflanzer empirically validated method?"* → Academic track odpovídá po
  ~3-5 letech (per Akademik roadmap v `docs/research/method-falsifiability/04-akademik.md`).

Charter níže primárně definuje Practitioner track. Academic track má vlastní
research roadmap (out of scope tohoto dokumentu, viz Akademik perspektiva).

## XYZ hypotéza (metoda)

> Věříme, že Pflanzerova metoda **zkrátí čas od „nápad" k „handoff package"
> o ≥ 50 %** (z baseline ~6–9 měsíců sériového handoffu na ~6–9 týdnů
> 2-session cyklu) pro projekty splňující fit criteria
> z `01-filozofie-a-kdy-pouzit.md`,
>
> s kvalitou handoff package **srovnatelnou nebo vyšší** než current state
> (měřeno re-work % v T+90 a cross-functional NPS).
>
> **Practitioner-level falsification:** hypotéza je odmítnuta, pokud
> median(composite PflanzerIndex) ≤ 1.0 across N=12 piloty s
> `compliance_score ≥ 10/12` (per ADR-0013).

## Success threshold

Tabulka s **instrumentation** sloupci (per Method Steward perspective bod #1).

| Metric | Cíl | Definice (start → end) | Data source | Cadence | Vlastník |
|--------|-----|------------------------|-------------|---------|----------|
| Primary lagging — Time-to-handoff | ≤ 50 % baseline | Od **signed Charter timestamp** (ADR-0004 artefakt v projekt repo) do **first commit s `#handoff` tag** v target dev repo (auditable git timestamps) | Pflanzer tool DB (primary) + Git API (validation) | Per pilot completion | Method Steward |
| Leading — Handoff acceptance (operational) | ≥ 80 % artefaktů použito v T+30 | T+30 form survey s checklist 6 artifact types × {used / used with mods / not used} | EM dev týmu fills form; data v Pflanzer tool | T+30 per pilot | EM dev týmu |
| Leading — Handoff acceptance (**blind external**) | ≥ 60 % per 3-EM panel | Stripped metadata artefakty + Likert 0-100 estimate per 3 EMs z jiných BU | Blind panel form, Steward aggregates | T+30 per pilot | Method Steward (orchestrace) |
| Guardrail — Re-work % T+90 | ≤ baseline current state | Code churn ratio T+0..T+90 (LOC changed in feature files / LOC initially committed) via `git log --numstat` | Git API + Jira labels (`rework`, `defect_fix`) | T+90 per pilot | Method Steward (automated query) |
| Stakeholder NPS | ≥ +20 (aggregated, N≥30, response rate ≥ 50 %) | Post-pilot survey T+30, 11-point scale + open-ended | Survey tool (typeform / similar) | T+30 per pilot, aggregated quarterly | Method Steward |
| **Composite PflanzerIndex** (P1, ADR-0014 TBD) | > 1.0 (vs propensity-matched baseline) | Weighted: 0.4 × time_ratio + 0.3 × acceptance + 0.2 × (1-rework) + 0.1 × NPS_normalized | Computed by Method Steward dashboard | Per pilot completion | Method Steward |

**Note on PflanzerIndex:** P1 follow-up (ADR-0014). Současný Charter v0.3 udává
4 base metriky; composite formula bude finalized v ADR-0014 s váhami + edge
cases (missing data, censored observations).

## Kill criteria (Practitioner track)

**Time-bounded variants** (per Skeptický VP Útok 2 + Method Steward perspective bod #4):

| Trigger (whichever first) | Kill condition | Decision authority |
|---------------------------|----------------|---------------------|
| **N=3 piloty NEBO T+9 mo** | > 50 % pilotů zhasne po S2 + 2+ leading indicators porušují threshold > 60 dní | Method Steward **emergency review veto** → Method Decider |
| **N=8 piloty NEBO T+15 mo** | One-sided binomial test p > 0.10 NEBO median(PflanzerIndex) < 1.0 | Method Decider |
| **N=12 piloty NEBO T+18 mo** | **Default Sunset** triggers pokud Method Decider nepotvrdí Keep písemně (per ADR-0011) | Method Decider (active Keep) or default (Sunset) |
| **N=20 piloty (Practitioner cap)** | < 3 self-sustaining BU (Champion pipeline) | Method Decider |

**Stopping for harm rule** (Data analyst Flaw 4): **kill immediately** bez ohledu
na N, pokud ≥ 25 % pilotů má dokumentovaný handoff collapse (0 % artifact
utilization v T+30, blind external panel score < 20/100). Method Steward triggers
emergency review do 7 dní.

**Interim analysis at N=6** (Data analyst M4 preregistration): conditional power
check. CP < 0.20 → futility kill. CP ∈ [0.20, 0.80] → continue. CP > 0.80 →
optional early stop pro efficacy (Method Decider rozhoduje).

**Pravomoc:**
- Method Steward = **veto pravomoc na emergency review** (svolá review do 7 dní
  od triggering signal). Final kill decision však u Method Decider.
- Method Decider = **Accountable** pro kill / iterate / sunset rozhodnutí.
  Process Portfolio Review = **Informed**.

## Default Sunset checkpoint

Per ADR-0011: **T+18 měsíců od first pilot kick-off** je sunset checkpoint.

Pokud Method Decider **explicitně nepotvrdí Keep písemně** (signed memo do
Process Portfolio Review minutes nejpozději v měsíci T+18), **default state
= Sunset**:
- Projekty v progress doběhnou bez nového scope.
- Charter freeze (žádné nové revize).
- Role catalog archived to read-only Confluence space.
- Method dashboard přechází do read-only historical mode.

**Re-activation post-sunset** vyžaduje nový ADR + Process Portfolio Review
endorsement. Nemůže se to stát latentně.

## Pre-registration protocol

Per ADR-0013: každý pilot má **signed pre-registration document** (`pre-registrations/<pilot-id>.yaml`)
**PŘED Session 1**, obsahující:

- **Fit criteria binary checklist** (7 kritérií z `01-filozofie-a-kdy-pouzit.md`)
  + 5 anti-pattern checks. Signed: PILOT / EXCLUDED.
- **Charter version pinned** (specific SHA, ne semantic verze).
- **Statistical test pre-specified** (α=0.10, power=0.80, MDE=0.5 PflanzerIndex shift).
- **Primary metric specification** (composite formula váhy).
- **Secondary endpoints** (predefined, multiplicity correction Bonferroni × 3).

**Immutable** po podpisu (kromě signed amendments s rationale).

## Pflanzer Compliance Score

Per ADR-0013: Method Steward audituje **ex-post** (do 30 dní po handoff completion)
12 must-have prvků. Skóre interpretation:

| Score | Status pilot pro method-level metrics |
|-------|---------------------------------------|
| **10-12 / 12** | Pflanzer pilot. Započítává se do XYZ validation. |
| **7-9 / 12** | „Pflanzer-inspired". Reportovaný separátně. NEZAPOČÍTÁVÁ se do success / kill metrics. |
| **< 7 / 12** | Pilot disqualified. Deviations = fork candidate. |

**Audit dotaz po pilotu** (Method Steward T+6 method-level report):
> *„Z N pilotů v reportu prošlo M compliance score ≥ 10/12. Validní sample pro
> XYZ test = M, ne N. Pokud M/N < 0.7, method má **fidelity problem** —
> Charter formulation nebo Champion training nestačí."*

## Causal model (Theory of Why)

Per ADR-0007 addendum + Akademik Gap 3 (akademik perspektiva, kauzální diagram).

```
PFLANZER INTERVENTIONS (X)             MEDIATING MECHANISMS (M)            OUTCOMES (Y)

1. Co-location of stakeholders    →    M1. ↓ Information asymmetry    →   O1. ↓ Time-to-handoff
   (cross-functional session)          (Akerlof 1970; TCE)                O2. ↑ Handoff acceptance
                                                                          O3. ↓ Re-work T+90
2. AI-generated tangible           →    M2. ↓ Requirements ambiguity   →   O4. ↑ Stakeholder satisfaction
   prototype in session                (Berry & Kamsties 2004)

3. Silent + scored decision        →    M3. ↓ HiPPO sponsor bias       →
   protocol (anti-HiPPO)               (Davenport 2006; Reinig 2003)

4. AI-mediated cross-dept          →    M4. ↑ Cross-functional shared   →
   synthesis                           mental model
                                       (Cannon-Bowers et al. 1993)

5. Pre-flight triage gates         →    M5. ↑ Pre-flight risk surface  →
                                       (RE traceability)

MODERATORS (when does mechanism work?):
- Mandate strength (Decider authority) — per ADR-0001
- AI tooling maturity (vendor reliability)
- Champion presence (bootstrap edge — ADR-0006)
- Regulatory load (DORA / AI Act / GDPR)
- Organizational size & culture
```

**Implikace pro measurement:**
- Charter měří **interventions** (compliance score) + **outcomes** (4 metrics).
- Mediators (M1-M5) měřitelné v academic track (P1 follow-up + P3 academic track),
  ne mandatory v practitioner track.
- Pokud outcomes pozitivní, ale interventions nedeliver (compliance < 10/12)
  → nepřipisuj success Pflanzerovi (mohl být Hawthorne / selection).

## Comparison baseline

Měříme proti **current state v dané organizaci**: sériový handoff
(zadavatel → produkt → vývoj → test → security → deploy).

**v0.3 updates** (per Data analyst Flaw 2 + Skeptický VP Útok 5):

- **Full population mining** (NE 5-10 manual estimate): Jira/Azure DevOps za
  posledních 24 měsíců, all projects matching fit-criteria proxy. Typicky N=30-80
  v BU 200+ FTE.
- **Survival analysis** pro cancelled projects (censored = include, ne mean-of-completed).
- **Project Class Taxonomy A/B/C/D** (per Skeptický VP Útok 5) — baseline collected
  per class; comparison MUSÍ být class-matched. Definice tax. v P1 follow-up
  (`docs/methodology/baseline-collection-playbook.md`).
- **Propensity score matching** na 6 kovariátech (project size, team count,
  regulated, customer-facing, scope category, BU) → top-quartile propensity
  baseline projects = control set per Pflanzer pilot.
- **Bootstrap budget €40k + 3 měsíce pre-pilot Steward effort** pro baseline
  collection (P2 follow-up: ADR-0010 method post-mortem disclosure + budget
  spec).

## Reinforcement track (method-level + per-pilot)

> Útok 11 v0.3 resolution: reinforcement track má **explicit budget commit**
> v Charteru projektovém (ADR-0004) a v True Cost Worksheet
> (`03-pre-session-priprava.md` Krok 1a). Bez podepsaného rozpočtu T+7/30/60/90
> Session 1 neodstartuje. Tabulka níže je method-level agregát.

| Readout | Scope | Owner | Min. PD per pilot | Co se musí stát |
|---------|-------|-------|-------------------|------------------|
| T+7 | per pilot | Champion (#17) | 0.5 | Handoff přijatý dev týmem, SHIP.md aktualizovaný |
| T+30 | per pilot | PM + EM + Champion | 2.0 (souhrnně) | Leading metric check (handoff acceptance ≥ 80 %), retro 60 min + **blind external EM panel** trigger |
| T+60 | per pilot | PM + Champion | 1.0 | Scope creep audit, 1-page update do Method Steward inboxu |
| T+90 | per pilot | Decider + PM + EM + Champion | 2.5 | Guardrail metric (re-work %), Go/Iterate/Kill **v ADR** per ADR-0001 |
| **T+30 compliance audit** | **method-level** | Method Steward | 0.5 | 12-bodový compliance check, score publikován v dashboardu |
| T+6 mo | **method-level** | Method Steward | 2 PD/report + 0.25 PD/měsíc průběžně | Agregace metrik napříč 3+ piloty, **Process Portfolio Review** publikace (NE Confluence-only) |
| T+12 mo | **method-level** | Method Decider (VP Eng Effectiveness) | review session 4 h + prep | Keep / iterate / sunset rozhodnutí, **external red team observer** přítomen (P2 follow-up), ADR commit |
| **T+18 mo** | **method-level** | Method Decider | **Default Sunset checkpoint** | Bez explicit Keep memo → automatic Sunset (per ADR-0011) |

**Σ per-pilot reinforcement commit:** min 6.5 PD souhrnně (včetně compliance
audit; default profil). Sponzor a EM ho podepisují v Charteru. Bez podpisu
pilot neodstartuje.

**Method-level escalation:** pokud u 2+ za sebou jdoucích pilotů
M(skutečnost) / N(plán) < 0.7 reinforcement utilization → automatický
warning v Method Steward T+6 reportu + flag pro Method Decider, že
**method-level Kill criteria nemohou být obhájena** (success/failure
data jsou unreliable).

## Validační loop & sunset

- **Method Steward** má pravomoc:
  - **Navrhnout** method-level Kill / Sunset (per Charter section *„Kill criteria"*).
  - **Svolat emergency review** (early-kill veto, per ADR-0011) pokud 2+ leading
    indicators porušují threshold > 60 dní nebo stopping-for-harm rule triggers.
- **Method Decider** rozhoduje Keep / Iterate / Sunset.
- **Default Sunset po T+18 mo** bez explicit Keep memo.
- Sunset = projekty v progress doběhnou, nové se nestartují, role catalog freeze.
- **Re-activation** vyžaduje nový ADR + Process Portfolio Review endorsement.

Sunset není failure — je to *methodology hygiene*. Lepší než nekonečný drift.

## Audit-committee odpověď

**Success scenario:**
> Otázka: *„Kolik pilotů prošlo Pflanzerem, jaký je success rate, jak ho měříte?"*
>
> Odpověď: *„X pilotů prošlo, Y z nich má compliance score ≥ 10/12 (Pflanzer
> piloty). Median PflanzerIndex je Z (vs baseline 1.0). Pre-registered statistický
> test (α=0.10, power=0.80) odmítá H0 s p=W. Detail per pilot v Method Steward
> T+6 mo reportu (link). Falsifying criteria definovaná v Method Charteru ADR-0013,
> kill review po N=12 nebo T+18 mo whichever first, default Sunset gate."*

**Failure scenario** (per Method Steward perspective):
> Otázka: *„Metoda nefunguje, proč ji ještě používáte?"*
>
> Odpověď: *„X pilotů prošlo, median PflanzerIndex Z (pod threshold 1.0).
> T+12 mo Method Steward review (link) doporučuje [Iterate / Sunset]
> s konkrétními změnami v role catalog / fit criteria. Decision podepsaná
> Method Deciderem [datum]. Default Sunset triggered po T+18 mo bez explicit
> Keep memo."*

**To je odpověď, kterou v0.2 metody nemá. v0.3 (po ADR-0011, 0012, 0013) má.**

## Reference

- ADR-0007 (kontext rozhodnutí o vzniku tohoto Charteru) — rámec.
- **ADR-0011** (Decider profile + Default Sunset) — supersedes ADR-0007 § Decider.
- **ADR-0012** (Steward operational scope) — supersedes ADR-0007 § Steward role.
- **ADR-0013** (Pre-registration + Compliance Score) — addendum k ADR-0007.
- Savoia, A. *The Right It* — XYZ pretotyping.
- Devil's advocate review Útok 12 + autoresearch round `docs/research/method-falsifiability/`.
- Charter projektový (ADR-0004) — vzor disciplíny.
- Popper / Lakatos — falsifiability standard.
- Gelman & Loken (2014) — forking paths.
- Akademická literatura per `docs/research/method-falsifiability/04-akademik.md` § Reference.