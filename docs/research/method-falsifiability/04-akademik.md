# Method Falsifiability — Perspektiva 04: Akademický recenzent

> Autor perspektivy: senior academic researcher v software engineering /
> management science. Publikuji v EMSE (Empirical Software Engineering),
> ICSE (International Conference on Software Engineering), MIS Quarterly
> a Information Systems Research. Reviewer pro JSS, IST a TSE. Můj filter:
> *peer-review standard*. Předkládám otázky, které by zaznamenala 1. kolo
> recenze v Q1 časopisu, ne ohlas na blogu nebo na konferenci typu
> Agile Alliance practitioner track.

---

## Verdikt (1 odstavec, peer-review style)

**Decision: Major Revision (revise-and-resubmit), borderline reject.**
Pflanzerova metoda v0.2.1 je dobře zdokumentovaný *artefakt designové
vědy* (Hevner et al. 2004) s upřímnou snahou o vědeckou disciplínu
v podobě Method-Level Charteru (`method-charter.md`, ADR-0007). Jako
*technical report* nebo *experience report* je publikovatelný v IEEE
Software, Agile Alliance proceedings nebo CSCW industry track.
Jako *empirický příspěvek* v EMSE / ICSE má ale **šest fatálních
metodologických mezer**: (1) XYZ hypotéza je formálně non-falsifiable
v Popperově smyslu, protože ad-hoc rescue mechanism není vyloučen;
(2) klíčové konstrukty („handoff package quality", „cross-functional
NPS", „re-work %") **nejsou operacionalizovány** ani validovány proti
existujícím instrumentům (např. Functional Size Measurement, Carstens
& Joost 2018 pro handoff quality, nebo SUS pro stakeholder satisfaction);
(3) chybí **theory of why** — mechanismus účinku — bez něj je každý
kill / iterate verdikt attribuovatelný confounderům (Hawthorne effect,
selection bias, regression to the mean); (4) **novelty claim** vůči
Design Sprint + Pretotyping + Decider trojici není demonstrován ablation
studiem; (5) **research design** pro validaci (single-case pilots) je
nedostatečný pro generalizační claimy v Method Charteru ("velké
korporace s AI vibe-coding"); (6) **comparison baseline** ("sériový
handoff 6–9 měsíců") je single-organization, manuálně estimovaná,
3-měsíční — což ve VRIO smyslu nesplňuje requirements pro
between-condition comparison. **Pokud autor doplní:** (a) explicitní
*theory of change* s causal diagram, (b) operacionalizovaný measurement
instrument s pilot reliability check (Cronbach α ≥ 0.7), (c) multiple
case study design s ≥ 6 piloty napříč ≥ 3 organizace v ≥ 2 industries,
(d) blind / independent rater pro coding handoff acceptance, (e)
sample size calculation pro power 0.80 — má potenciál na ESEM nebo
ICSE-SEIP track. **V current state je to dobře vedený interní
governance dokument, ne empirický příspěvek.**

---

## Methodological Gaps (6 položek s referenci na literature standard)

### Gap 1 — XYZ hypotéza není Popper-falsifiable; je vystavena ad-hoc rescue

**Co Charter říká:**
> *„Pflanzerova metoda zkrátí čas od nápad k handoff package o ≥ 50 %
> (z baseline 6–9 měsíců na 6–9 týdnů) pro projekty splňující fit criteria
> z `01-filozofie-a-kdy-pouzit.md`."*

**Akademický problém:** Klauzule *„pro projekty splňující fit criteria"*
je **immunizing stratagem** (Popper 1959, *The Logic of Scientific
Discovery*, sekce 19–20). Pokud pilot zhasne, evangelista metody může
říct: *„To nebyl projekt splňující fit criteria — viz `01.md` antipattern 3
(rotten persona), antipattern 4 (single-team scope), antipattern 5
(stakeholdeři bez mandátu)."* Tím se **každé negative observation
re-classifies jako out-of-scope**, místo aby disconfirmovala hypotézu.
Tento pattern Lakatos (1970, *Falsification and the Methodology of
Scientific Research Programmes*) označuje jako *degenerating research
programme* — když ad-hoc auxiliary hypotézy chrání core před vyvrácením
bez generování nových testovatelných predikcí.

**Konkrétní symptomy:**
- Fit criteria (`01-filozofie-a-kdy-pouzit.md`) obsahují **7 kritérií**;
  audit by mohl tvrdit „splnili jsme 6 z 7" pro úspěšný pilot a „nesplnili
  jste 7. (Champion exists)" pro neúspěšný — bez ex-ante operacionalizace
  je to retrospektivní racionalizace.
- Antipattern 5 *„stakeholdeři bez mandátu"* je **neoperacionalizovaný**;
  „mandát" lze post-hoc redefinovat tak, aby žádný neúspěšný pilot mandát
  neměl. Tím se metoda chrání **definicí**, ne evidencí.
- Kill criterion *„> 50 % pilotů zhasne po druhém cyklu"* je formálně
  testovatelný, ale **bez registrace fit criteria ex-ante** je metric
  manipulovatelný retrospektivním vyloučením „špatných" pilotů.

**Literature standard:**
- Popper (1959), Conjectures and Refutations (1963) — *bold conjectures
  s riskantními predikcemi*.
- Lakatos (1970) — *progressive vs. degenerating research programme*:
  metoda musí generovat **novel testable predictions**, ne jen
  re-explain existing data.
- Chalmers (1999), *What is this thing called Science?*, kap. 7 — moderní
  pragmatická falsification: hypotéza musí specifikovat **observation
  conditions, které by ji vyvrátily, ex-ante**, ne ex-post.

**Doporučená oprava:**

Charter musí obsahovat **pre-registered ex-ante checklist** (signed
před Session 1 prvního pilotu), který lze auditovat:

```
PILOT REGISTRATION FORM (ex-ante, signed before Session 1)
─────────────────────────────────────────────────────────
Pilot ID: P-2026-NN
Date of registration: YYYY-MM-DD

Fit criteria checklist (per 01-filozofie-a-kdy-pouzit.md, items 1–7):
  [ ] 1. Cross-functional alignment problem (3+ depts)
  [ ] 2. Funkční prototyp je requirement
  [ ] 3. Fresh discovery (< 6 měsíců)
  [ ] 4. Capacity 8–10 person-days available
  [ ] 5. Mandate to decide (Decider with signed mandate)
  [ ] 6. Pre-flight triage passed (Discovery + Security + Legal + Platform)
  [ ] 7. Champion exists (or buddy-of-Champion, per ADR-0006)

All 7 must be CHECKED YES at registration.
Signature: Method Steward ____________ Date ____________

POST-PILOT (no exclusions allowed):
  Outcome: [ ] success [ ] iterate [ ] kill
  Re-classification post-hoc: PROHIBITED.
  If a fit criterion was violated, pilot still counts toward kill metric
  but with annotation "fit violation type X discovered post-hoc."
```

Bez tohoto **pre-registration mechanismu** je XYZ hypotéza
non-falsifiable v Popper-Lakatos smyslu a žádný EMSE recenzent ji
neakceptuje. Analogie: pre-registration v clinical trials (CONSORT
2010) a v empirical SE (Ralph et al. 2021, *Empirical Standards for
Software Engineering Research*).

---

### Gap 2 — Konstrukty nejsou operacionalizovány; content / construct validity neexistuje

**Co Charter říká (úryvek):**

| Metric | Cíl |
|--------|-----|
| Primary — Time-to-handoff | ≤ 50 % baseline |
| Leading — Handoff acceptance | ≥ 80 % artefaktů použito v T+30 |
| Guardrail — Re-work % T+90 | ≤ baseline current state |
| Stakeholder NPS | ≥ +20 |

**Akademický problém:** Každý ze čtyř konstruktů má neoperacionalizovanou
měřící proceduru. To je *fatal flaw* v construct validity (Cook & Campbell
1979; Shadish, Cook & Campbell 2002, *Experimental and Quasi-Experimental
Designs*).

#### 2a) „Time-to-handoff"

- **Co je „nápad"?** Datum prvního prompt v Slack? První Charter draft?
  Sponzorská diskuze v lobby? Bez kanonické *anchor point definition* je
  baseline manipulovatelná.
- **Co je „handoff package"?** `07-handoff-do-vyvoje.md` definuje list
  artefaktů — ale „handoff" jako *time-bounded event* vs. *gradual
  process* není rozhodnuto. Empirically: handoff acceptance je
  rolling (T+7, T+30, T+90). Time-to-handoff jako single number je
  reductionist.
- **Doporučená operacionalizace:** převzít ICSE convention
  *„cycle time" = first commit s tagem #PFLANZER po Session 2 minus
  Charter sign-off date*. Audit-friendly, manipulation-resistant.

#### 2b) „Handoff acceptance ≥ 80 % artefaktů použito v T+30"

- **Co je „artefakt"?** OpenAPI spec, mockup, decision log, score
  sheet, ADR, risk register — všechny jsou v handoff package.
- **Co je „použito"?** Referenced v PR description? Quoted v code
  comment? Implemented as-is? S nějakou modification?
- **Co je „% použito"?** Numerator / denominator?
- **Problém:** *„≥ 80 %"* zní precizně, ale je to **denominator-free
  fraction**. To je v survey research equivalent „is the sky blue?"
  bez Likertu.
- **Doporučená operacionalizace:** **Artifact Utilization Coding
  Scheme** — list ~12 artefakt typů × ordinal scale {0 = ignored,
  1 = referenced only, 2 = adapted with major changes, 3 = adopted
  as-is}. Coded by **independent rater blind to pilot success
  classification** (per Pflanzer Decider). Inter-rater reliability
  Cohen's κ ≥ 0.6 required (Landis & Koch 1977).

#### 2c) „Re-work % T+90"

- **Re-work code count?** Cyclomatic complexity delta? File change
  density? Commits with tag #fix nebo #rework?
- **Empirical SE literature:** Mockus et al. (2002), Nagappan &
  Ball (2005), Bird et al. (2011) — *defect prediction & code
  churn measurement*. Pflanzer **žádný z těchto established metrics
  neoperacionalizuje**.
- **Doporučená operacionalizace:** *Code churn ratio T+90 = (LOC
  changed in files touched in handoff PR) / (LOC initially committed
  in handoff PR)*, computed via `git log --numstat` over T+90 window.
  Established metric, manipulation-resistant, baseline-comparable.

#### 2d) „Stakeholder NPS ≥ +20"

**Toto je nejproblematičtější.** NPS (Net Promoter Score, Reichheld
2003) má dobře dokumentovanou **validity controversy**:

- **Keiningham et al. (2007)** *„A Longitudinal Examination of Net
  Promoter and Firm Revenue Growth"* — NPS **nepřesahuje** alternativy
  (ACSI, top-2-box satisfaction) v predictive validity. Reichheldův
  původní claim *„NPS is the one number you need to grow"* byl
  empiricky vyvrácen.
- **Grisaffe (2007)** *„Questions about the ultimate question"* —
  NPS má **non-linear distribution issues** a 11-bodová škála není
  optimální.
- **Pro N < 30** (a Pflanzer pilot má ~7 účastníků) je NPS jako
  index *„% promoters - % detractors"* **statisticky nesmyslný** —
  binarizing continuous scale na 3 buckets {0–6 detractor, 7–8
  passive, 9–10 promoter} ztrácí ~80 % informace.

**Doporučená operacionalizace:**

Replace single NPS with **multi-construct stakeholder satisfaction
battery**:

1. **Adapted TAM (Technology Acceptance Model)** — Davis (1989),
   Venkatesh & Bala (2008): per-role measurement *perceived
   usefulness* + *perceived ease of use* (4 items each, 7-pt
   Likert, Cronbach α target ≥ 0.8).
2. **Process satisfaction** — adapted from Sambamurthy &
   Poole (1992) Group Process scale (8 items, 7-pt Likert).
3. **Decision quality perception** — Reinig (2003) decision
   quality framework (5 items).
4. **NPS retained as secondary** with explicit caveat *„single-item
   reference, not primary"*.

Triangulace: kvantitativní battery + **post-pilot semi-structured
interview** (15–30 min per participant), thematic coding podle Braun
& Clarke (2006), inter-rater reliability check.

**Literature standard:**
- Cook & Campbell (1979), Shadish et al. (2002) — construct validity
  in quasi-experiments.
- Boudreau, Gefen & Straub (2001) *„Validation in Information
  Systems Research: A State-of-the-Art Assessment"* MISQ — IS
  field's checklist for construct validity.
- Ralph et al. (2021) *Empirical Standards for Software Engineering
  Research* — ACM/IEEE checklist (Methods & Reporting Standards).

---

### Gap 3 — Chybí Theory of Why; bez mechanismu je každý outcome attribuovatelný confounderům

**Charter formuluje XYZ jako black-box claim:** *„aplikuj Pflanzer →
získáš 50 % zkrácení."* Není ale specifikováno **proč** to funguje.
Bez kauzálního mechanismu je metoda *recipe*, ne *theory*. To je
fatální omezení vůči EMSE / MIS Quarterly:

- **Whetten (1989)** *„What Constitutes a Theoretical Contribution?"* AMR
  — teorie musí mít elementy *What, How, **Why**, Who-Where-When*.
  „Why" je *„theoretical glue that welds the model together"*.
  Pflanzer má robustní *What* (artefakty, role) a slušné *How*
  (procesní kroky), ale *Why* chybí.
- **Sutton & Staw (1995)** *„What Theory is Not"* ASQ — teorie
  není seznam konstruktů, citace, ani diagramy. Je to **kauzální
  argument**, který explikuje mechanismus.
- **Gregor (2006)** *„The Nature of Theory in Information Systems"*
  MISQ — Type IV (Explanation) a Type V (Design and Action) theory.
  Pflanzer aspiruje na Type V (design theory pro intervence), ale
  Type V vyžaduje explicit *„kernel theories"* (psychologie, sociologie,
  ekonomie) jako základ. Pflanzer **žádné kernel teorie necituje**.

**Co by Charter měl artikulovat — návrh Theory of Why:**

Tři kandidátní mechanismy, které lze formalizovat:

#### Mechanism A — Co-presence reduces information asymmetry
*„Když jsou stakeholdeři současně v jedné místnosti s funkčním
prototypem, snižuje se informační asymetrie mezi rolemi (Akerlof
1970 *Market for Lemons* adapted to internal stakeholder market),
což redukuje multi-round handoff loops, které jsou primary cause
sériového delay."*

- **Kernel theory:** Akerlof's information asymmetry, Williamson's
  transaction cost economics (TCE).
- **Testable prediction:** počet round-trip otázek security ⇄ dev
  v T+90 by mělo být **významně nižší** v Pflanzer pilotu vs. baseline.
- **Mediator measurement:** *„Information asymmetry index"* —
  count Slack / Jira interactions s tagem *„clarification needed"*
  v T+90 vs. baseline.

#### Mechanism B — Tangible artefact reduces ambiguity-driven veto
*„Funkční klikací prototyp s běžícím OpenAPI contractem snižuje
sémantickou nejednoznačnost specifikace (Hsieh-Yee 1996; relevant
literature: requirement engineering ambiguity, Berry & Kamsties 2004),
což redukuje late-stage security/legal veto, které je primary cause
re-work."*

- **Kernel theory:** Requirements engineering — *„document-based
  vs. prototype-based specification"* (Sommerville 2011).
- **Testable prediction:** late-stage veto count (security/legal
  intervention po > 50 % effortu) by mělo být **významně nižší**.
- **Mediator measurement:** late-stage veto count z project tracker,
  podle pre-defined coding (Útok 5 / Devil's Advocate review).

#### Mechanism C — Anti-HiPPO procedural authority reduces decision dilution
*„Silent voting před verbálním + Decider hlasuje poslední redukuje
sponsorovo zkreslení (HiPPO — Highest Paid Person's Opinion,
Davenport 2006), což vede k decision quality (Reinig 2003), což
vede k handoff acceptance."*

- **Kernel theory:** Group decision support systems literature
  (DeSanctis & Gallupe 1987), nominal group technique (Delbecq
  et al. 1975).
- **Testable prediction:** decision reversal rate v T+30 by mělo
  být **významně nižší** v Pflanzer vs. ad-hoc meetings.
- **Caveat:** Útok 10 (Devil's Advocate) ukazuje, že tato authority
  je *paper authority* bez co-facilitator. Mechanism C je tedy
  **conditional on co-facilitator existence**.

**Doporučení:** Charter musí mít **sekci „Causal model"** s explicit
diagram (Pflanzer interventions → mediators → outcomes), kterou lze
testovat **mediation analysis** (Baron & Kenny 1986; modern: Hayes
2018 *Introduction to Mediation, Moderation, and Conditional Process
Analysis*).

---

### Gap 4 — Novelty claim není ablation-studied; recombination vs. invention je nedoložena

**Charter (`09-srovnani-existujici-metody.md`) tvrdí 3 diferenciátory:**
1. Real-time AI vibe-coding viditelný stakeholderům.
2. Score závaznosti per oddělení.
3. AI-mediovaná syntéza feedbacku v Session 2.

**Akademický problém:** *„Recombination of existing techniques"* je
**legitimní** příspěvek (cf. Hevner et al. 2004 design science research
— *„Improvement"* DSR type), ale **musí být ablation-studied**: které
komponenty individuálně přispívají k outcome, a které jsou *epiphenomena*.

Otázky, které EMSE recenzent položí:

- **Q1:** *„Co kdyby Pflanzer použil Figma místo AI vibe-coding (= GV
  Sprint baseline)? Předpokládáte, že outcome by byl horší — kvantifikujte
  ablation."*
- **Q2:** *„Score závaznosti per oddělení s deflation 0.5 pro AI-only
  feedback (Útok 6 Devil's Advocate) — je to *measurement* nebo
  *heuristika*? Pokud heuristika, jaký je její vliv vs. baseline
  decision rule (jednoduché majority voting)?"*
- **Q3:** *„AI-mediovaná syntéza vs. lidský facilitátor solo — co je
  *uniquely AI-enabled* a co by lidský senior facilitátor zvládl
  také?"*

**Standard literature:**
- Hevner et al. (2004), Peffers et al. (2007) — design science research
  methodology requires *evaluation* phase s explicit comparison vs.
  baseline.
- **Wieringa (2014)** *Design Science Methodology for Information
  Systems and Software Engineering*, kap. 12 — *„Technical research
  problem"* musí mít *„contribution argument"*.

**Doporučená oprava:**

Pflanzer evaluation roadmap musí obsahovat **ablation pilot** (~3 pilots):

| Pilot variant | AI vibe-coding | Score závaznosti | AI synthesis | Expected vs. full Pflanzer |
|---|---|---|---|---|
| Full Pflanzer | YES | YES | YES | baseline (reference) |
| Pflanzer − AI vibe (GV Sprint hybrid) | NO (Figma) | YES | YES | tests Differentiator 1 |
| Pflanzer − Score (DS Decider hybrid) | YES | NO (simple vote) | YES | tests Differentiator 2 |
| Pflanzer − AI synthesis (human-only) | YES | YES | NO | tests Differentiator 3 |

Bez ablation je novelty claim **non-falsifiable in scientific sense** —
nikdo nemůže vědět, zda 50 % time reduction přichází z AI nebo z
prostého „co-located people in one room" efektu (Allen 1977).

---

### Gap 5 — Research design pro validaci je nedostatečný pro generalization claims

**Charter implicitně předpokládá „pilot → pilot → pilot → metoda
validated"**, ale neformuluje **research design** explicitně.

**Standard pro empirical SE / IS research:**
- **Yin (2014)** *Case Study Research: Design and Methods* — single
  case study je *„revelatory"* nebo *„critical case"*, ne *„representative"*.
  Generalizace z 1 pilotu = **anekdotická evidence**.
- **Runeson & Höst (2009)** *„Guidelines for conducting and reporting
  case study research in software engineering"* EMSE — *„multiple
  case study with replication logic"*: 6–10 cases, theoretical
  saturation, cross-case synthesis.
- **Wohlin et al. (2012)** *Experimentation in Software Engineering*
  — quasi-experiment requires control group (current state) + treatment
  group (Pflanzer), random or matched assignment, pre-post measurement,
  power analysis.

**Konkrétní problémy:**

1. **Sample size calculation chybí.** Pro detekci *„50 % time reduction"*
   s α = 0.05, power = 0.80, baseline variance unknown — minimum N
   per group závisí na effect size, ale orientačně:
   - Cohen's d = 1.0 (large effect, plausible pro 50 % reduction) →
     N ≈ 17 per group (Cohen 1988).
   - Cohen's d = 0.5 (medium, conservative) → N ≈ 64 per group.
   - Charter žádá kill po 6 pilotech — **statistically underpowered**
     pro detekci čehokoli menšího než velmi velkého effect size.

2. **Selection bias.** První piloty si vybírá Champion — *„low-risk,
   single-BU, low-stakes"* (per Devil's Advocate). To je
   *cherry-picking* nejlepších kandidátů, což inflatuje success rate.
   Audit committee question: *„byl by Pflanzer úspěšný na *průměrném*
   projektu, ne jen na hand-picked?"*

3. **No control group.** Charter měří „proti current state" s baseline
   collected *„3 měsíce před prvním pilotem"*. To je **historical
   comparison**, ne kontrolovaná condition. Confounders:
   - Hawthorne effect (samotná pozornost zlepšuje outcome).
   - Maturation (tým se zlepšuje sám časem).
   - Regression to the mean.
   - Selection (Pflanzer projekty mají senior buy-in, baseline ne).

4. **No blinding.** Method Steward, který hodnotí success, je
   stejná osoba, která metodu propaguje. Conflict of interest = bias.

**Doporučené research design (sequential):**

| Phase | Design | N | Duration | Output |
|---|---|---|---|---|
| 1. Pilot exploratory | Single descriptive case | 1 | 3 mo | Operacionalizace, instrument calibration |
| 2. Construct validation | Multi-case + measurement validation | 3 | 6 mo | Reliability, validity instrument |
| 3. Comparative quasi-exp | Matched-pair (Pflanzer vs. status quo project per BU) | 8 pairs | 12 mo | Effect size, confidence interval |
| 4. External validity | Multi-org replication | 3+ orgs × 3+ pilots | 12 mo | Generalization boundary |

Bez phase 3 + 4 je *„≥ 50 % zkrácení"* claim **non-generalizable**
(Lee & Baskerville 2003 *„Generalizing Generalizability in
Information Systems Research"* ISR — generalize from observation
to theory, ne from sample to population, ale i ten první vyžaduje
multi-case).

---

### Gap 6 — External validity / generalizability je over-claimed

**Charter implies (`01-filozofie-a-kdy-pouzit.md`, `09-srovnani-...md`):**
*„Pflanzer cílí cross-functional alignment v korporátu" → implikuje
„funguje napříč velkými organizacemi s AI vibe-coding."*

**Akademický problém — Lee & Baskerville (2003) generalizability
taxonomy:**

- **Type EE generalization** (empirical to empirical): „Z 6 pilotů
  v 1 organizaci generalizuju na 100 budoucích pilotů v té samé
  organizaci." Toto je **legitimní s replication logic** (Yin 2014).
- **Type ET generalization** (empirical to theory): „Z 6 pilotů
  potvrzuju mechanism A/B/C theory." Toto by Charter měl
  cílit.
- **Type TE generalization** (theory to empirical) a **Type TT**
  jsou irelevantní zde.

**Problém je, že Charter implicitně cílí Type EE napříč organizacemi
bez explicit replication logic.**

Pro tvrzení *„Pflanzer funguje v BU jiné než kde byl piloten"*
vyžadujeme:

- **Different industries:** banka vs. telco vs. retail vs. public
  sector — minimum 3.
- **Different sizes:** 500–2k employees, 2k–10k, 10k+.
- **Different regulatory contexts:** EU (GDPR/DORA/AI Act),
  US (SOX/HIPAA), APAC.
- **Different AI tooling maturity:** organizace s 6+ mo experience
  s Cursor/Claude vs. greenfield adopter.

**Sample size pro defensible generalization claim:**
- **Conservative (Yin 2014):** 6–10 cases for replication.
- **Aggressive (Eisenhardt 1989) per theoretical saturation:** 4–10.
- **Multi-context (Recker 2013 *Scientific Research in Information
  Systems*):** minimum 2 cases per context dimension → 3 industries
  × 2 sizes × 2 regulatory = 12 cases minimum.

**Realistic claim authority po N pilotech:**

| N pilotů | Defensible claim |
|---|---|
| 1 | *„Single instance description — proof of concept."* |
| 3 (same org) | *„Pflanzer is replicable within one organizational context."* |
| 6 (same org) | *„Pflanzer has internal validity within one organizational context."* |
| 6 (3 orgs) | *„Pflanzer generalizes to a *class* of similar organizations (Type ET)."* |
| 10+ (5 orgs, 3 industries) | *„Pflanzer generalizes across industries — bounded by fit criteria."* |
| 20+ peer-reviewed pilots in literature | *„Pflanzer is an empirically validated method."* |

**Doporučení:** Charter musí mít sekci *„Scope of validity claims"*
explicit, navázanou na current pilot count. Bez toho je *„cílí korporát"*
**generalizing beyond data** — což je most common reviewer rejection
ground (Ralph et al. 2021).

---

### Gap 7 (bonus) — Hawthorne effect a self-selection bias jsou nediskutovány

**Stručně:** Devil's Advocate Útok 2 (Champion bootstrap) implicitně
naznačuje, že první piloti budou *„high-energy, senior-committed,
Champion-led"* — což znamená samostatný **selection bias**, který
inflatuje outcome. Toto je **threat to internal validity** v Cook &
Campbell taxonomy.

Charter neobsahuje **diskuzi limitations**, která je standard v
empirical SE papers (Section *„Threats to Validity"* per Wohlin et al.
2012 a Runeson & Höst 2009 mandatory). Bez explicit limitations
section recenzent rejekt.

---

### Gap 8 (bonus) — Reflexivity / Researcher Positionality není adresována

V kvalitativním paradigmatu (Charmaz 2014, Creswell & Poth 2018)
researcher positionality — *„kdo jsem, jaké mám vztahy k pole, jak
to ovlivňuje sběr a interpretaci dat"* — musí být explicit. Method
Steward je *„advocate of the method"* (per Charter); jeho pozice
jako primary data analyst je **conflict of interest** vyžadující
acknowledgement.

Doporučení: Method Steward neměří success solo; měření je
delegated na **external/independent rater** (Útok 10 Devil's
Advocate naznačuje co-facilitator z jiné BU — stejný princip).

---

## Návrh Theory of Why Pflanzer Works (k explicit artikulaci v Charteru)

**Současný stav:** Charter má XYZ hypothesis (input → output), ale
chybí **mechanism** (input → mediators → output).

**Návrh kauzálního modelu** (k validaci mediation analysis přes
multi-pilot dataset):

```
                ┌─────────────────────────────────┐
                │  PFLANZER INTERVENTIONS         │
                │  ─────────────────────────────  │
                │  1. Co-location of stakeholders │
                │  2. AI-generated tangible       │
                │     prototype in session        │
                │  3. Silent + scored decision    │
                │     protocol (anti-HiPPO)       │
                │  4. AI-mediated cross-dept      │
                │     synthesis                   │
                │  5. Pre-flight triage gates     │
                └────────────┬────────────────────┘
                             │
                ┌────────────▼────────────────────┐
                │  MEDIATING MECHANISMS           │
                │  ─────────────────────────────  │
                │  M1. ↓ Information asymmetry    │
                │      (Akerlof 1970; TCE)        │
                │  M2. ↓ Requirements ambiguity   │
                │      (Berry & Kamsties 2004)    │
                │  M3. ↓ HiPPO sponsor bias       │
                │      (Davenport 2006;           │
                │       Reinig 2003)              │
                │  M4. ↑ Cross-functional shared  │
                │      mental model               │
                │      (Cannon-Bowers et al.      │
                │       1993; Mathieu et al. 2000)│
                │  M5. ↑ Pre-flight risk surface  │
                │      (gate logic — RE / SE      │
                │       requirements traceability)│
                └────────────┬────────────────────┘
                             │
                ┌────────────▼────────────────────┐
                │  OUTCOMES                       │
                │  ─────────────────────────────  │
                │  O1. ↓ Time-to-handoff          │
                │  O2. ↑ Handoff acceptance       │
                │  O3. ↓ Re-work T+90             │
                │  O4. ↑ Stakeholder satisfaction │
                └─────────────────────────────────┘

       MODERATORS (when does mechanism work?):
       ──────────────────────────────────────────
       - Mandate strength (Decider authority)
       - AI tooling maturity (vendor reliability)
       - Champion presence (bootstrap edge — ADR-0006)
       - Regulatory load (DORA / AI Act / GDPR)
       - Organizational size & culture
```

**Co tento model umožňuje akademicky:**

1. **Testable predictions:** každá M → O šipka je testovatelná
   mediation hypothesis (Baron & Kenny 1986; Hayes 2018).
2. **Mechanism-level falsification:** pokud M1 (information asymmetry)
   neklesá v Pflanzer pilotech, ale O1 (time-to-handoff) klesá,
   pak mechanism A je vyvrácen — outcome je *via different
   mechanism* (např. Hawthorne, selection bias).
3. **Theoretical contribution claim:** Pflanzer není jen recipe,
   ale **design theory** (Gregor 2006 Type V), která integruje
   kernel theories (TCE, requirements engineering, group decision
   support, shared mental models).
4. **Publication strategy:** *„Pflanzer is a design theory grounded
   in TCE and group decision support literature; we validate
   mechanism-level claims via N pilots with mediation analysis."*
   To je EMSE / MISQ acceptable framing.

---

## Konstrukty vyžadující operacionalizaci (s návrhem instrumentu)

| Konstrukt | Současný stav | Doporučená operacionalizace | Reliability target |
|---|---|---|---|
| **Time-to-handoff** | Vague start/end | First Slack thread w/ #pflanzer tag → first commit w/ #handoff tag (auditable timestamps) | N/A (objective) |
| **Handoff acceptance** | „≥ 80 % artefaktů" bez denominator | Artifact Utilization Coding Scheme (12 artifact types × 0–3 ordinal), independent rater blind to outcome, κ ≥ 0.6 | Cohen's κ ≥ 0.6 |
| **Re-work %** | Undefined | Code churn ratio T+90 (LOC changed / LOC committed) via `git log --numstat` | N/A (objective) |
| **Stakeholder satisfaction** | NPS ≥ +20 | Multi-construct battery: TAM (PU + PEOU) + Sambamurthy & Poole group process + Reinig decision quality + secondary NPS | Cronbach α ≥ 0.8 per subscale |
| **Information asymmetry (mediator M1)** | Not measured | Count cross-dept clarification messages (Slack / Jira) T+90, normalized by team size | N/A (objective) |
| **Requirements ambiguity (mediator M2)** | Not measured | Late-stage veto count T+90 (security / legal intervention po > 50 % effort) | N/A (objective) |
| **HiPPO bias (mediator M3)** | Not measured | Decision reversal rate T+30 (decisions overridden by Decider post-session) | N/A (objective) |
| **Shared mental model (mediator M4)** | Not measured | Adapted Mathieu et al. (2000) team mental model similarity score (card-sorting task pre / post session) | Inter-team similarity > 0.7 |
| **Fit criteria** | Narrative checklist | Pre-registered ex-ante binary checklist (signed) | N/A (procedural) |
| **Method adoption** | „Self-sustaining BU" undefined | (a) Number of pilots initiated without Method Steward intervention; (b) Champion pipeline depth (= number of Champion-trained people per BU) | N/A (objective) |

**Pilot instrument validation** (před production use):
1. **Pilot N = 1:** drafting + pre-test (think-aloud s 5 participanty).
2. **Pilot N = 2–3:** reliability check (Cronbach α, κ).
3. **Pilot N ≥ 4:** production měření.

To je standard per Boudreau et al. (2001) MISQ a Recker (2013).

---

## Research Roadmap (3-letá perspektiva pro publication-grade validation)

### Year 1 — Foundation & Instrument Validation

**Q1–Q2:**
- Charter revision dle Gaps 1–8 (pre-registration, theory of why,
  limitations section).
- Instrument drafting (8 konstruktů per tabulka výše).
- Baseline collection v cílové organizaci (3 mo, ≥ 10 reprezentativních
  projektů, multi-rater).
- IRB / ethics review (pokud accademic affiliation).

**Q3–Q4:**
- Pilot 1 (single descriptive case, Yin 2014 *revelatory*).
- Instrument pilot test (think-aloud, item analysis, reliability check).
- Submit *experience report* na IEEE Software / ICSE-SEIP track
  (Year 1 milestone — establish presence in community).

**Output Year 1:**
- Validated measurement instrument.
- 1 experience report paper.
- Method Charter v0.3 (post-instrument calibration).

### Year 2 — Multi-Case Replication & Mechanism Testing

**Q1–Q2:**
- Pilots 2–4 (same organization, replication logic).
- Mediation measurement (M1–M5 instruments deployed).
- Ablation pilot (Pflanzer − AI vibe-coding variant).

**Q3–Q4:**
- Pilots 5–6 (multi-case within organization).
- Cross-case synthesis (Eisenhardt 1989 grounded theory of method).
- Submit *empirical paper* na EMSE / ESEM (Year 2 milestone — first
  empirical validation).

**Output Year 2:**
- Multi-case study paper (N = 6 within-org).
- Mediation analysis preliminary results.
- Method Charter v0.4 (post-mechanism evidence).

### Year 3 — External Validity & Generalization

**Q1–Q2:**
- Multi-organizational replication (pilots 7–12 across 3 organizations,
  2+ industries).
- Quasi-experimental comparison (Pflanzer vs. matched current-state
  baseline within organizations).
- Power analysis-justified sample size for effect size detection.

**Q3–Q4:**
- Generalization paper (Lee & Baskerville Type ET argument).
- Theory consolidation: Design Theory paper (Gregor & Jones 2007
  *„The Anatomy of a Design Theory"* JAIS) — submit na MISQ /
  ISR / JAIS.

**Output Year 3:**
- Multi-organizational empirical paper.
- Design theory paper (theoretical contribution).
- Open-access replication package (handbook + instruments).

### Year 4+ (post-roadmap)

- Replication by independent teams (Carver et al. 2014 *„Identifying
  barriers to the systematic literature review process"* — replication
  package as condition for theoretical claim).
- Meta-analysis once N papers ≥ 10.
- Practitioner adoption studies.

**Total publication-grade evidence:**

| Year | Pilots | Papers submitted | Confidence in claims |
|---|---|---|---|
| 1 | 1 | 1 experience report | Anecdotal |
| 2 | 6 | 1 empirical paper | Internal validity for 1 org |
| 3 | 12 | 1 generalization + 1 theory paper | Bounded external validity |
| 4+ | 20+ | independent replications | Validated method |

**Reálná akademická timeline pro „Pflanzer is empirically validated"
claim: ~4–5 let, ne ~12 měsíců.** To je intelektuálně poctivé
očekávání, které Charter musí absorbovat (současné kill criteria
po 6 / 10 pilotech jsou *practitioner timeline*, ne *academic timeline*).
Oba timelines mohou koexistovat — practitioner kill je pro internal
business decision, academic validation je pro publication credibility.
Charter by měl rozlišit obě perspektivy explicitně.

---

## Závěr (peer-review summary)

Pflanzerova metoda v0.2.1 je **dobře zdokumentovaný design artifact**
s vědomím vlastních hranic (čest za Devil's Advocate review, čest za
ADR-0007 Method Charter). V *academic-empirical* perspektivě má **8
methodologických mezer**, z nichž 6 je fatálních pro Q1 publikaci.

**Decision: Major revision, borderline reject.** Po dopracování
(theory of why, operacionalizovaných konstruktů, multi-case research
design, ablation, external validity bounds, threats-to-validity
section) má potenciál na **ESEM / ICSE-SEIP / EMSE** v 2–3 letém
horizontu. V současné podobě je publikovatelný jako **experience
report** v IEEE Software / Communications of the ACM (industry
track), což je legitimní vědecký příspěvek, ale **nikoli empirická
validace claim *„Pflanzer redukuje time-to-handoff o ≥ 50 %"***.

**Klíčové doporučení autorovi:**

1. **Rozlišuj „practitioner authority" vs. „academic authority"
   explicitně.** Charter má hybrid framing — částečně internal
   governance dokument, částečně quasi-scientific manifesto. Tyto
   dvě role vyžadují různé standardy. Vyberte si nebo rozdělte.
2. **Pre-register fit criteria a measurement instruments před
   first pilot.** Bez toho je každý positive result attribuovatelný
   p-hacking nebo cherry-picking.
3. **Doplňte Theory of Why.** Bez kauzálního mechanismu je metoda
   non-theoretical recipe — což je legitimní v Hevner DSR
   *„Improvement"* type, ale ne v Gregor Type V design theory.
4. **Investujte do measurement validation před scaling.** Lepší
   3 piloty s validovaným instrumentem než 30 pilotů s ad-hoc
   metrikami.
5. **Akceptujte, že *„empirically validated method"* claim vyžaduje
   3–5 let a 12–20 pilotů napříč organizace.** Charter kill
   criteria po 6 pilotech jsou byznysově obhájitelné, ne akademicky.

**Co Pflanzer dělá DOBŘE z academic perspective (chvála recenzenta):**

1. **Self-applied Charter discipline (ADR-0007).** *„Methodology that
   applies its own discipline to itself"* je vzácné v workshop
   methodologies. Toto je legitimní *„scientific attitude"* per
   Popper.
2. **Explicit fit criteria a anti-patterns.** Mnoho metod si nárokuje
   universal applicability; Pflanzer **explicit boundaries** —
   *„kdy nepoužít"*. To je epistemická poctivost.
3. **Robustní comparison table (`09-srovnani-...md`).** Většina
   workshop methodologies se nesrovnává s adjacent metodami;
   Pflanzer toto dělá. To je seriózní *related work* sekce.
4. **Devil's Advocate review v dokumentaci.** Internalizace kritiky
   před externí kritikou — *„intellectual due diligence"* na úrovni,
   kterou v Q1 venues vidíme zřídka.
5. **ADR governance.** ADR-0001 až ADR-0007 s decision history je
   *traceability artifact* — splňuje requirements engineering
   tracking, který sám o sobě je akademicky obhájitelný.

**Tyto silné stránky znamenají, že po revision má Pflanzer *higher
ceiling* než typický workshop methodology paper.** Není to dno
literatury; je to *promising design artifact requiring empirical
grounding*. Pokud autor investuje 2–3 roky do empirical track,
publikace v top venues je realistická.

---

*Konec akademické perspektivy. Pokud autor přečte a řekne
„rozumím — separuju practitioner track a academic track, pre-registruju
fit criteria, dopracuju theory of why, instrument validation
před scaling" — review splnila účel. Pokud autor řekne „akademik
nepochopil practitioner reality" — pak prosím re-čtěte Gap 1
(Popper falsification), Gap 3 (theory of why), Gap 5 (research
design). Tam jsou neobejítelné requirements pro empirický příspěvek.*

---

## Reference

**Methodology & Philosophy of Science:**
- Popper, K. (1959). *The Logic of Scientific Discovery.*
- Lakatos, I. (1970). *Falsification and the Methodology of
  Scientific Research Programmes.*
- Chalmers, A. (1999). *What is this thing called Science?* 3rd ed.

**Empirical Software Engineering:**
- Wohlin, C. et al. (2012). *Experimentation in Software Engineering.*
- Runeson, P. & Höst, M. (2009). „Guidelines for conducting and
  reporting case study research in software engineering." EMSE.
- Ralph, P. et al. (2021). *Empirical Standards for Software
  Engineering Research.* ACM/IEEE.
- Yin, R. (2014). *Case Study Research: Design and Methods.* 5th ed.

**Design Science Research:**
- Hevner, A. et al. (2004). „Design Science in Information Systems
  Research." MISQ.
- Peffers, K. et al. (2007). „A Design Science Research Methodology
  for Information Systems Research." JMIS.
- Gregor, S. (2006). „The Nature of Theory in Information Systems." MISQ.
- Gregor, S. & Jones, D. (2007). „The Anatomy of a Design Theory."
  JAIS.
- Wieringa, R. (2014). *Design Science Methodology for Information
  Systems and Software Engineering.*

**Construct Validity & Measurement:**
- Cook, T. & Campbell, D. (1979). *Quasi-Experimentation.*
- Shadish, W., Cook, T. & Campbell, D. (2002). *Experimental and
  Quasi-Experimental Designs for Generalized Causal Inference.*
- Boudreau, M., Gefen, D. & Straub, D. (2001). „Validation in
  Information Systems Research." MISQ.
- Davis, F. (1989). „Perceived Usefulness, Perceived Ease of Use,
  and User Acceptance of Information Technology." MISQ. (TAM)
- Venkatesh, V. & Bala, H. (2008). „Technology Acceptance Model 3
  and a Research Agenda on Interventions." Decision Sciences.
- Sambamurthy, V. & Poole, M. (1992). „The Effects of Variations
  in Capabilities of GDSS Designs on Management of Cognitive
  Conflict in Groups." ISR.
- Reinig, B. (2003). „Toward an Understanding of Satisfaction with
  the Process and Outcomes of Teamwork." JMIS.

**NPS Critique:**
- Reichheld, F. (2003). „The One Number You Need to Grow." HBR.
- Keiningham, T. et al. (2007). „A Longitudinal Examination of Net
  Promoter and Firm Revenue Growth." Journal of Marketing.
- Grisaffe, D. (2007). „Questions about the ultimate question:
  conceptual considerations in evaluating Reichheld's Net Promoter
  Score." Journal of Consumer Satisfaction.

**Theory Construction:**
- Whetten, D. (1989). „What Constitutes a Theoretical Contribution?"
  AMR.
- Sutton, R. & Staw, B. (1995). „What Theory is Not." ASQ.
- Eisenhardt, K. (1989). „Building Theories from Case Study
  Research." AMR.

**Mediation & Causal Analysis:**
- Baron, R. & Kenny, D. (1986). „The Moderator-Mediator Variable
  Distinction in Social Psychological Research." JPSP.
- Hayes, A. (2018). *Introduction to Mediation, Moderation, and
  Conditional Process Analysis.* 2nd ed.

**Generalizability:**
- Lee, A. & Baskerville, R. (2003). „Generalizing Generalizability
  in Information Systems Research." ISR.
- Recker, J. (2013). *Scientific Research in Information Systems.*

**Pretotyping (referenced):**
- Savoia, A. (2019). *The Right It: Why So Many Ideas Fail and How
  to Make Sure Yours Succeed.*

**Group Decision & Information Asymmetry (mechanism kernels):**
- Akerlof, G. (1970). „The Market for Lemons." QJE.
- Davenport, T. (2006). „Competing on Analytics." HBR. (HiPPO concept)
- DeSanctis, G. & Gallupe, R. (1987). „A Foundation for the Study
  of Group Decision Support Systems." Management Science.
- Delbecq, A. et al. (1975). *Group Techniques for Program Planning.*
- Cannon-Bowers, J., Salas, E. & Converse, S. (1993). „Shared mental
  models in expert team decision making."
- Mathieu, J. et al. (2000). „The influence of shared mental models
  on team process and performance." JAP.
- Berry, D. & Kamsties, E. (2004). „Ambiguity in requirements
  specification."
- Allen, T. (1977). *Managing the Flow of Technology.* (co-location effect)

**Qualitative Methods (positionality):**
- Braun, V. & Clarke, V. (2006). „Using thematic analysis in
  psychology." Qualitative Research in Psychology.
- Charmaz, K. (2014). *Constructing Grounded Theory.* 2nd ed.
- Creswell, J. & Poth, C. (2018). *Qualitative Inquiry and
  Research Design.* 4th ed.
- Landis, J. & Koch, G. (1977). „The measurement of observer
  agreement for categorical data." Biometrics. (κ benchmark)

**Software Engineering Defect & Churn Metrics:**
- Mockus, A. et al. (2002). „Two case studies of open source
  software development."
- Nagappan, N. & Ball, T. (2005). „Use of relative code churn
  measures to predict system defect density." ICSE.
- Bird, C. et al. (2011). „Don't touch my code! Examining the
  effects of ownership on software quality." ESEC/FSE.

**TCE (transaction cost economics):**
- Williamson, O. (1985). *The Economic Institutions of Capitalism.*
