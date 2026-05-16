# Method Falsifiability — perspektiva Data / Analytics

> Autor: senior data analyst / measurement scientist sub-agent (role catalog #12).
> Kontext: autoresearch round na **method-level falsifiability** Pflanzerovy metody.
> Předmět review: `docs/methodology/method-charter.md` v0.2.1 + ADR-0007.
> Lens: statistická rigor — power, sample size, confounders, baseline validity,
> Goodhart, comparison fairness.

---

## Verdikt (1 odstavec)

**Current Method-Level Charter má kosmetickou falsifying power, ne reálnou.**
Vypadá to disciplinovaně (XYZ + threshold + kill criteria + baseline), ale když
projedu thresholdy přes power analýzu, sample size kalkulaci a confounder
inventory, *žádné* z definovaných tvrzení nelze po N=3 pilotech statisticky
obhájit. Kill criterion „> 50 % z 3 pilotů zhasne" je v noise floor binomického
rozdělení (95% CI po N=3 je ±56 %); audit committee, který umí přečíst tabulku,
to rozseká za 4 minuty. Baseline je definovaný light a vágně (5–10 projektů,
manuální estimace) — to je *convenience sample*, ne baseline, a obsahuje minimálně
4 zjevné biasy (selection, survivorship, recall, Hawthorne). Comparison je
strukturálně unfair, protože Pflanzer projekty jsou cherry-picked přes fit
criteria, ale baseline projekty fit criteria neprošly. Primary metric (time-to-
handoff) je definovaná bez termínu „handoff" a bez composite, takže ji lze
trivially gamovat zkrácením scope nebo přesunem práce do reinforcement track.
Goodhart-loop na „handoff acceptance ≥ 80 %" je open-by-design — interní
self-report, žádný blind reviewer. Charter v současné podobě **neumí
zfalsifikovat sám sebe**; je to *vanity science with audit-grade vocabulary*.
Doporučení dole: zvednout minimum N na 8 (skeptický pilot scenario) / 12
(decision-grade), přejít na composite primary metric, zavést synthetic control
nebo difference-in-differences design a externí blind reviewer na acceptance
score. Bez těchto úprav je ADR-0007 audit committee odpověď, ne measurement
plan.

---

## Methodological flaws

### Flaw 1 — Sample size N=3 je v binomické noise floor; threshold „> 50 %" není decision-grade

**Současný stav.** Kill criterion: *„Po 3 pilotech: > 50 % pilotů zhasne →
trigger Iterate→Kill."*

**Problém.** Binomická distribuce s N=3 a true p = 0.50 (null = „method
indifferent vs baseline") vrátí ≥ 2/3 selhání s pravděpodobností 50 % — to
znamená, že **pokud metoda v populaci funguje na 50/50 coinflip úrovni
(= worthless), Pflanzer ji zkilluje s 50% šancí**, ale taky s 50% šancí
ponechá. Type-I error (kill funkční metody) ≈ 50 % při true p = 0.5; type-II
(keep broken metody) ≈ 50 %. To je *coin flip masquerading as governance*.

Konkrétní spočet (binomial CDF, p=0.5, N=3):
- P(≥2 fails | p=0.5) = 0.500
- P(≥2 fails | p=0.3) = 0.216  (= metoda *lepší* než coin flip jde do kill v 22 % případů)
- P(≥2 fails | p=0.7) = 0.784  (= broken metoda projde v 22 % případů)

**Wilson 95% CI** pro pozorovaný success rate 1/3 (≈ 33 %): **[6 %, 79 %]**.
To znamená: po 3 pilotech s 1 úspěchem nelze odmítnout ani hypotézu „method
fails 94 % of the time" ani „method works 79 % of the time". Charter
prohlašující na základě N=3 cokoliv = strawman.

**Scenario, kde Charter selže.** Pflanzer odběhne 3 piloty: jeden úspěšný
(handoff per Charter), dva zhaslé (Decider silence + Champion odešel).
Method Steward podle current rules trigger Iterate→Kill. Audit committee
otázka: *„Jaký je 95% CI na success rate?"* — odpověď: *„33 % bodový odhad,
CI [6 %, 79 %]."* Audit: *„Tak jste killnuli metodu, která může mít true
success rate 79 %."* Charter má **zero evidentiary defensibility**.

### Flaw 2 — Baseline validity: 5–10 projektů „manuální estimace" je convenience sample

**Současný stav.** ADR-0007: *„Baseline collection může být light (5–10
reprezentativních projektů s manuálním estimace) namísto plné instrumentace."*

**Problém.** 5–10 projektů ručně vybraných „as representative" je learning-book
příklad **convenience sample**. Konkrétně obsahuje **čtyři zjevné biasy**:

1. **Selection bias.** Kdo vybírá „reprezentativní"? Champion #17. Champion má
   incentive vybrat projekty, kde sériový handoff bolel — protože to ospravedlňuje
   Pflanzer. *Confirmation bias by design.*
2. **Survivorship bias.** „Time-to-handoff baseline" lze měřit jen na projektech,
   které **doběhly do handoffu**. Cancellované / restartované / silently-died
   projekty (kterých je v korpu typicky 30–50 % portfolio) z baseline mizí.
   Baseline tedy systematicky **podceňuje** skutečnou délku — což hraje v favor
   Pflanzeru (jeho zlepšení vypadá menší než reálně může být), ALE současně
   maskuje fakt, že significant chunk projektů by ani v baseline nikdy nedošel
   do měřitelného stavu.
3. **Recall bias.** „Manuální estimace" znamená, že někdo retroaktivně řekne
   *„tohle trvalo asi 7 měsíců"*. Recall pro project duration je notoricky
   neaccurate — meta-analýzy v project management literature (PMI) ukazují
   recall error ±25 % pro projekty starší než 6 měsíců.
4. **Hawthorne effect na pilot side.** Pilot projekty *vědí*, že jsou měřené.
   Baseline projekty to nevěděly. Comparison je tedy *measured-and-observed vs
   measured-but-unobserved* — well-documented confound v industrial measurement.

**Scenario, kde Charter selže.** Champion #17 vybere 8 baseline projektů, kde
median time-to-handoff je 7 měsíců. První Pflanzer pilot dosáhne 8 týdnů. Cílem
ADR-0007 je „≤ 50 % baseline = ≤ 3.5 měsíce". Pilot vypadá jako huge win (-72 %).
Auditor: *„Ukaz mi distribuci všech baseline projektů, nejen těch 8."* Pokud
median napříč all 80 projektů je 4 měsíce (protože převzal jen velké, viditelné),
Pflanzer pilot najednou je -50 % místo -72 %, na hraně threshold. Pokud auditor
požádá o **median time-to-cancellation** nebo **median time-to-handoff including
silently-died = censored at observation date**, čísla se rozsypou úplně.

### Flaw 3 — Fit criteria filtering = comparison je strukturálně unfair

**Současný stav.** `01-filozofie-a-kdy-pouzit.md` definuje 7 fit kritérií;
metoda se použije, jen pokud platí ≥5. Baseline projekty fit criteria neprošly
(nemohly — neexistovala).

**Problém.** To je **klasický selection-on-treatment confound**. Pflanzer
projekty jsou ex-ante filtrované na *„cross-functional alignment problem +
discovery hotový + stakeholdeři mají mandát + Champion existuje + scope vejde
+ pre-flight prošel"*. Tato kritéria sama o sobě **predikují kratší
time-to-handoff** independent of method. Projekt, kde stakeholdeři mají mandát
a Champion exists a discovery je hotový, doběhne rychleji **i v sériovém
handoffu** než projekt, kde nic z toho neplatí.

Lze formálně: nechť `T = α + β·Method + γ·FitCriteria + ε`, kde
`FitCriteria` jsou strongly correlated s `Method` (Pflanzer projekty mají
FitCriteria=1, baseline FitCriteria je distribuovaný). Naive ATT
(average treatment on treated) estimate `β̂` bude **upward-biased** o
velikost `γ·E[FitCriteria | Method=1] − γ·E[FitCriteria | Method=0]`. V Pflanzer
case-u je rozdíl v fit criteria veliký (Pflanzer = 5+/7, baseline pravděpodobně
2–3/7), takže `β̂` je dominantly **fit criteria effect, nikoli method effect**.

**Scenario, kde Charter selže.** Po 6 pilotech average time-to-handoff = 9 týdnů
(vs baseline median 28 týdnů). Charter declares 68 % improvement. Skeptický
auditor (Director of Engineering z Útok 12 přesně) říká: *„Ukažte mi 6 srovnatelných
projektů z baseline, kde stakeholdeři měli decider mandate, discovery byl hotový,
Champion existoval — a porovnejte time-to-handoff."* Pokud takových projektů
v baseline pool je 3 s median 12 týdnů, **improvement clesne na 25 %**, pod
threshold (≥ 50 %). Charter dosud nezadal *matched-pair design*, takže tahle
otázka rozseká celý success claim.

### Flaw 4 — Primary metric „time-to-handoff" je underspecified a gameable

**Současný stav.** Method Charter: *„Time-to-handoff ≤ 50 % baseline, per pilot,
agregováno T+6 mo."* Bez definice „handoff start" a „handoff end".

**Problém.** Co je `t_0`? První kontakt sponzora se zadáním? Charter sign-off?
Pre-flight kickoff? Session 1 start? Žádné z toho není explicit. Co je `t_1`?
Handoff package akceptován dev týmem? Production deploy? T+30 acceptance
review (≥ 80 % artefaktů použito)?

Gameabilita:
- **t_0 manipulation:** definovat t_0 = Session 1 start. Tím schováš celý
  pre-flight (typicky 2–4 týdny per ADR-0002). Time-to-handoff se zkracuje
  arbitrarily.
- **t_1 manipulation:** definovat t_1 = handoff package signed. Tím vyhneš
  veškerý post-handoff re-work, který může být masivní (Útok 11: T+30/60/90
  readouts faktem dělá 2 z 8 týmů).
- **Scope manipulation:** uměle zúžit Pflanzer scope na *„MVP slice"* a
  výsledek porovnat s baseline projekty, které měly full scope. Time
  ratio vypadá skvěle; tým pak dělá 4 měsíce *„fast-follow"* mimo Pflanzer
  cyklus.

**Composite metric absence.** Charter má guardrail re-work % v T+90, ale
re-work a time-to-handoff **nejsou ve společné decision rule**. Audit
committee otázka: *„Co když pilot má time-to-handoff -60 %, ale re-work
+100 %?"* — žádná rule. Aktuální Charter dává Method Stewardovi diskreci,
což je opět paper authority pod sponzorským tlakem.

**Scenario, kde Charter selže.** Pilot A: t_0 = Session 1 (Charter
artificially zúžil), pre-flight schoval do *„preparation"*. t_1 = handoff
signed (po-handoff re-work schoval do *„operational hand-off"*). Time
ratio: 6 týdnů vs 28 týdnů = -78 %. Re-work %: 60 % (massive). Method
Steward report říká *„success, primary lagging met"*. Engineering 4 měsíce
po-handoff opravuje. Konec: Pflanzer „funguje" v reportech, baseline má
horší metriku, ale total project cost je stejný nebo vyšší.

### Flaw 5 — Confounders: Champion quality, AI tool maturity, top-mgmt sponsorship

**Současný stav.** Charter nedefinuje confounders. ADR-0007 mluví o *„Method
Steward sleduje metrics"*, ne o causal identification.

**Problém.** Pflanzer success záleží minimálně na:
1. **Champion quality** (#17 — viz Útok 2). Champion je v každém pilotu jiný
   člověk. Variance v Champion skills (facilitation, political capital, AI
   tooling fluency) je obrovská a jde kompletně do `ε` residualu.
2. **AI tool maturity.** Pilot v Q1 2026 (Claude 4.7, v0/Bolt zralé) vs pilot
   v Q3 2026 (hypothetical Claude 5, lepší codegen). Method effect je
   nemožné oddělit od tool effect.
3. **Top-mgmt sponsorship.** Sponzor s exec air-cover = decisions stick.
   Sponzor mid-level = decisions reverted. To je dominant predictor.
4. **Project complexity.** Pflanzer scope se mění per pilot — od jednoduchého
   customer-facing přes integration-heavy po multi-team. Cross-pilot
   comparison je apples-to-oranges.

**RCT je nemožné** (nelze randomizovat metodu na pilot úrovni — proti vůli
stakeholderů). Second-best options:

- **Synthetic control (Abadie).** Pro každý Pflanzer pilot zkonstruuj
  weighted combination historických baseline projektů, který matchuje na
  pre-treatment covariates (project size, team count, regulated y/n, scope).
  Difference between actual Pflanzer outcome a synthetic counterfactual =
  treatment effect. Vyžaduje N≥10 baseline projektů s instrumentací.
- **Difference-in-differences.** Pokud má organizace 2+ BU a Pflanzer se
  rolluje sequence, BU bez Pflanzeru v daném quarteru je control. Identifying
  assumption: parallel trends. Vyžaduje N≥4 BU, longitudinal data, minimum
  6 quarter window.
- **Propensity score matching.** Definuj propensity to be Pflanzer-eligible
  na základě fit criteria; matchuj Pflanzer pilots s baseline projekty
  v top quartile of propensity. Eliminates Flaw 3.

Charter žádné z toho nezmiňuje. Charter spoléhá na **naive before/after
comparison**, což je weakest possible causal identification.

### Flaw 6 — Goodhart's law na „Handoff acceptance ≥ 80 %"

**Současný stav.** *„Leading metric: handoff package akceptován dev týmem
≥ 80 % artefaktů použito v T+30. Owner: EM dev týmu."*

**Problém.** *Owner: EM dev týmu* = ten samý EM, který byl v Session 1,
podepsal capacity sign-off, je politicky exposed k pilotnímu success. Self-
report metric s **strong incentive to confirm**. Konkrétní gaming patterns:

- **„Artefakt použit"** je vague. Pokud EM vyplní *„yes"* protože dev tým
  *„referenčně se na Charter podíval"*, threshold se trivially naplní.
- **80 % cutoff** je politicky positioning — EM nepíše 75 % protože by to
  spustilo escalation; nepíše 85 % protože by to ukázalo, že měl rezervu;
  napíše 80 ± 2.
- **T+30 timing** — měřeno přesně tehdy, kdy je pilot ještě „project of
  the moment". Re-work attribution v T+90 je už mimo radar.

**Audit grade:** Žádný metric s **kombinací**: (a) self-reported, (b) by-party-
with-skin-in-the-game, (c) without blind reviewer, (d) without ground truth
artefact, **není defensible**. To je standard ve Cochrane review methodology.
Pflanzer Charter selže v jakémkoli quality audit.

**Scenario.** Method Steward agregátní report: *„Across 6 pilots, handoff
acceptance averaged 84 %."* Skeptik (audit): *„Pull random sample of 20
artifacts from handoff packages and have an independent EM rate them. What
do you predict?"* Pokud nestrukturovaný retro by ukazal 50–60 % skutečné
acceptance, Charter je *Theranos-grade reporting*.

### Flaw 7 — Threshold velikosti efektu (-50 %) je arbitrary, nepodepřená a likely overstated

**Současný stav.** *„XYZ: Pflanzer zkrátí čas od nápad → handoff o ≥ 50 %
(z baseline ~6–9 měsíců na ~6–9 týdnů)."*

**Problém.** Kde se vzal 50 %? V dokumentaci žádný reference. Charter uvádí
specific numerical claim *6 měsíců → 6 týdnů* — to je **-83 % reduction**,
nikoli -50 %. Internal inconsistency. Plus:

- Žádná literature review effect sizes podobných metod (Design Sprint,
  Lean Inception) jako referenční benchmark.
- Effect sizes v workshop methodology research jsou typicky Cohen's d
  ∈ [0.2, 0.5] (small to medium). -50 % time reduction by odpovídalo
  d > 1.0 (huge), což je v interventional research **suspiciously large**.
- *„Too good to be true"* heuristika: any single intervention claiming
  -50 % to -83 % time reduction without confirmatory replication je red
  flag for publication bias / methodological artifact.

### Flaw 8 — N=3 vs N=6 vs N=10 thresholdy nejsou pre-registered, jsou ad-hoc

**Současný stav.** Charter má 3 kill triggers (po N=3, N=6, N=10), každý
s jiným threshold (> 50 %, ≥ baseline × 0.75, < 3 self-sustaining BU).

**Problém.** Tři thresholdy = **forking paths problem** (Gelman). Při třech
independent decision points s α ≈ 0.5 na každém (viz Flaw 1) je probability
type-I error někde across the path > 80 %. Method Steward bude muset
*„rozhodnout v duchu Charteru"* na ad-hoc základě, což je **researcher
degrees of freedom** = p-hacking by another name.

**Mitigace.** Pre-register exact decision rule: e.g., *„After exactly N=8
pilots, Method Steward runs single pre-specified test of H0: median
time-to-handoff ≥ 0.75 × baseline median. α = 0.10 (one-sided), power 0.80.
If reject → keep. If fail to reject → kill."* Pre-registration eliminuje
forking paths.

---

## Konkrétní navrhované metric úpravy

### M1 — Primary lagging: composite Pflanzer Index místo samostatné time metriky

Definice:

```
PflanzerIndex_i = (BaselineTime_matched / PflanzerTime_i)
                  × (1 − ReworkRate_T+90_i)
                  × HandoffAcceptance_blind_i

kde:
- PflanzerTime_i = t_handoff_signed − t_charter_signed
                   + 0.5 × t_pre_flight_duration  (penalizace za pre-flight)
- BaselineTime_matched = median time-to-handoff of propensity-matched
                          baseline projects
- ReworkRate_T+90 = (engineering hours T+0..T+90 on rework /
                     total engineering hours T+0..T+90)
- HandoffAcceptance_blind = % artifacts rated „used as primary input"
                             by independent EM blind to which pilot
                             produced them
```

Threshold: `PflanzerIndex ≥ 1.5` (50 % composite improvement, harder to
game než single metric).

### M2 — Time metric: definovat `t_0` a `t_1` precisely

- `t_0` = datum **signed Charter** (ADR-0004 artefakt).
- `t_1` = datum **handoff package merge to main branch of dev repo**
  (technical artifact, git timestamp = ground truth, ne self-report).
- Pre-flight duration logována separately, ne zahrnována do t_0.
- Post-handoff rework počítán separately T+30, T+90.

### M3 — Baseline: full population, ne convenience sample

Místo *„5–10 reprezentativních projektů manuální estimace"* požadovat:

- Mining project tracker (Jira/Azure DevOps) za posledních 24 měsíců, **all
  projects matching fit criteria proxy**: ≥ 3 teams involved, ≥ 1 regulated
  function (security/legal/compliance), customer-facing or B2B. Typicky
  N=30–80 projektů v BU velikosti 200+ FTE.
- Měřit time-to-handoff jako `t_first_ticket_created` → `t_first_production_deploy`.
  Pokud projekt cancelovaný, **include as censored observation** (survival
  analysis, Kaplan-Meier, ne mean-of-completed).
- Sample baseline distribution: median, p25, p75, p90, % censored.

### M4 — Pre-registered decision rule

```yaml
preregistration:
  primary_hypothesis:
    H0: median(PflanzerIndex) ≤ 1.0  # no improvement vs matched baseline
    H1: median(PflanzerIndex) > 1.0
  test: one-sided Mann-Whitney U
  alpha: 0.10
  power_target: 0.80
  minimum_detectable_effect: PflanzerIndex shift of 0.5
  sample_size_required: 8 pilots minimum, 12 preferred
  stopping_rule:
    interim_at: N=6
    interim_action: futility check (conditional power); if < 0.20, kill
    final_at: N=12
    final_action: pre-specified test
  multiple_comparisons:
    no_subgroup_analysis_without_pre_registration: true
```

### M5 — Blind acceptance review

Handoff acceptance metric musí být *blind*:

- Po T+30 každého pilotu nakopíruj `handoff_package/` artifacts.
- Strip metadata identifying pilot (project name, dates, role names).
- Pošli **3 independent EMs z jiných BU** (nezúčastněných v daném pilotu).
- Každý hodnotí: *„Kdyby tento package přišel k vám, kolik % byste reálně
  použili?"* Likert + numerický odhad.
- Average across 3 reviewers = `HandoffAcceptance_blind`.
- Cost: ~4 h × 3 EM = 12 hours per pilot, fully external.

### M6 — Guardrails proti Goodhart

- **Re-work shadow ledger.** Engineering hours T+0..T+90 split into
  `feature_dev`, `defect_fix`, `requirement_change`, `arch_rework`. Last
  three jsou „re-work". Logged in Jira labels, audited quarterly.
- **External replication.** Po N=6 pilotech externí auditor (jiná konzultace
  / akademický partner) replikuje 2 piloty z dat. Discrepancy > 20 %
  = re-instrument.
- **Pilot blinding kde možné.** Champion nesmí být měřič. Method Steward
  nesmí být ve stejné BU jako pilot. Decider nesmí podepsat handoff
  acceptance.

---

## Sample-size table — co lze statisticky obhájit po N pilotech

Předpoklady: dichotomické success/fail observation per pilot (zjednodušení;
pro composite PflanzerIndex platí podobně, viz poznámka pod tabulkou).
Null hypotéza H0: true success rate p₀ = 0.50 (Pflanzer indifferent vs
baseline). Test: exact binomial, one-sided, α = 0.10.

| N pilotů | Observed succ. | Wilson 95 % CI | Lze obhájit závěr „p > 0.50"? | Lze obhájit „p > 0.75"? | Method Steward defensible claim |
|----------|----------------|----------------|-------------------------------|-------------------------|---------------------------------|
| 3        | 2/3 (67 %)     | [21 %, 94 %]   | NE                            | NE                      | „Nepoznáme noise od signal."   |
| 3        | 3/3 (100 %)    | [44 %, 100 %]  | NE (p=0.125)                  | NE                      | „Suggestive only; need more."  |
| 5        | 4/5 (80 %)     | [38 %, 96 %]   | NE (p=0.188)                  | NE                      | „Trending positive."           |
| 6        | 5/6 (83 %)     | [44 %, 97 %]   | NE (p=0.109)                  | NE                      | „Suggestive, marginal."        |
| 8        | 7/8 (88 %)     | [53 %, 98 %]   | **ANO** (p=0.035)             | NE (p=0.367)            | „Method probably better than coin flip; magnitude unclear." |
| 10       | 8/10 (80 %)    | [49 %, 94 %]   | **ANO** (p=0.055)             | NE                      | „Method outperforms 50 % threshold."                        |
| 12       | 10/12 (83 %)   | [55 %, 95 %]   | **ANO** (p=0.019)             | Marginal (p=0.158)      | „Method robustly outperforms 50 %; 75 % threshold unclear."   |
| 16       | 13/16 (81 %)   | [57 %, 93 %]   | **ANO** (p=0.011)             | **ANO** (p=0.093)       | „Method outperforms baseline; effect size moderate-to-large." |
| 20       | 16/20 (80 %)   | [58 %, 92 %]   | **ANO** (p=0.006)             | **ANO** (p=0.087)       | „Robust evidence at both thresholds."                       |

Pro **kill decision** (one-sided, „prove broken"):

| N pilotů | Observed fail. | Wilson 95 % CI fail rate | Lze obhájit „method broken (fail > 50 %)"? |
|----------|----------------|--------------------------|---------------------------------------------|
| 3        | 2/3 (67 %)     | [21 %, 94 %]             | NE — CI zahrnuje 0.30 i 0.94                |
| 3        | 3/3 (100 %)    | [44 %, 100 %]            | Suggestive, ne decision-grade (p = 0.125)   |
| 6        | 4/6 (67 %)     | [30 %, 90 %]             | NE                                          |
| 8        | 6/8 (75 %)     | [41 %, 93 %]             | Marginal (p = 0.145)                        |
| 10       | 7/10 (70 %)    | [40 %, 89 %]             | Marginal (p = 0.172)                        |
| 12       | 9/12 (75 %)    | [47 %, 91 %]             | **ANO** (p = 0.073)                         |

**Bottom line.**
- **N=3 nestačí na NIC.** Ani success ani kill rozhodnutí nelze obhájit.
  CI jsou tak široké, že zahrnují každý rozumný null.
- **N=8 je floor pro „lepší než coin flip"** závěr (jednostranně, α=0.10).
- **N=12 je floor pro „lepší než 50 % baseline reduction" claim,** a
  current Charter to claimuje. Tj. Charter nepřímo požaduje N=12,
  ale defines kill decision při N=3. Internal contradiction.
- **N=16–20 je decision-grade** pro multi-threshold claims (composite
  metric + magnitude).

**Poznámka k composite metric.** Pokud PflanzerIndex je kontinuální
(ne dichotomický), Mann-Whitney U test má vyšší power than exact binomial.
Pro detekci shift in median by ~30 % s α=0.10, power=0.80 a expected
effect size d≈0.5 → **N≈26 per group (Pflanzer + matched baseline)**.
S synthetic control design lze pravděpodobně dostat dolů na N≈12 Pflanzer
pilots + 30+ baseline projects v poolu.

---

## Návrh „falsifiability acid test" — co by metodu skutečně vyvrátilo

Nazvu **Pflanzer Falsifying Trial v1**. Spec:

### Design

- **Sample.** N=12 Pflanzer pilots + matched control pool 30+ baseline
  projektů (mined z project trackeru posledních 24 měsíců). Matching:
  propensity score na 6 kovariátech (project size, team count, regulated,
  customer-facing, scope category, BU). Top-quartile propensity baseline
  projects = control set.
- **Primary endpoint.** Median PflanzerIndex (M1 definice).
- **Pre-registered decision rule.**
  - H0: median PflanzerIndex ≤ 1.0 (žádné composite zlepšení)
  - H1: median PflanzerIndex > 1.0
  - Test: Mann-Whitney U, one-sided, α = 0.10
  - Minimum detectable effect: shift of 0.5 (odpovídá ~50 % composite improvement)
- **Secondary endpoints.** Time ratio alone; re-work %; blind acceptance.
  Reported, ne decision-driving (avoid forking paths).
- **Interim analysis at N=6.** Conditional power. If CP < 0.20, kill for
  futility. If CP ∈ [0.20, 0.80], continue. If CP > 0.80, early stop for
  efficacy (optional).
- **Stopping for harm.** Pokud > 25 % pilotů má dokumentovaný **handoff
  collapse** (= 0 % artifacts used T+30), kill immediately bez ohledu
  na N. (Etical analog: stopping for safety.)

### Falsifying outcomes

Pflanzer **byl by vyvrácen**, pokud:

1. **Statistical futility at N=12** (primary test failed to reject H0).
2. **Effect size below MDE** (median PflanzerIndex < 1.5 i při
   significant test).
3. **Time-only improvement bez quality match** (time ratio > 1.5 ALE
   blind acceptance < 60 % AND re-work > 30 %) — = surface speed bez
   substance.
4. **Replication failure.** External auditor replikuje 2 random pilots
   a najde discrepancy > 20 % v primary metric → re-instrument; pokud
   replication fail two times v sequenci, kill.
5. **Self-sustaining failure.** Po N=12 pilotech (~ 18 měsíců real time)
   < 30 % BU má actively running second-or-later cycle bez vendor coach
   intervence. (Tj. metoda nemá legs.)
6. **Cost overrun.** Realized person-day cost per cycle > 1.5× claimed
   (Útok 1 effect): pokud average pilot stojí > 18 person-days proti
   claimed 8–10, business case je broken even pokud metoda funguje.

### Falsifying NULL conditions

Pflanzer **nelze adekvátně testovat**, pokud (= postpone, nekill):

- Méně než 8 pilotů má kompletní data (rozumný floor).
- Baseline pool < 20 projektů (matched control nemožný).
- Pivotal organizační změna mid-trial (CPO odchod, reorg) — confounds
  result. Document, continue, asterisk in final report.
- AI tool landscape posun > 1 major generation mid-trial.

### Co Charter v1 (current) musí přidat, aby získal falsifying power

1. **N raised from 3 → 12 pro kill decision.** Threshold po N=3 je
   informational (warning lights), ne kill trigger.
2. **Composite PflanzerIndex** místo single time metric.
3. **Propensity-matched comparison** explicitly required v baseline
   collection spec.
4. **Blind acceptance review** (externí EM z jiné BU).
5. **Pre-registration document** signed by Method Decider PŘED N=1 pilot
   start. (= OSF-style preregistration, ne ex-post Charter update.)
6. **Survival analysis** pro baseline (censored = include).
7. **Interim analysis rules** specified up front.
8. **External replication** povinný po N=6 nebo N=8 pilots.

Bez těchto úprav Charter zůstává *audit-grade vocabulary on top of
naive before/after numerology*, což je přesně to, co Pflanzer kritizuje
u Design Sprint 2.0, SAFe success stories, atd. Method that exempts
itself from rigorous measurement reproduces the failure mode it claims
to fix.

---

## Statistical-rigor scorecard (current Charter v0.2.1)

| Kritérium                                  | Skóre 0–5 | Komentář                                                                 |
|--------------------------------------------|-----------|--------------------------------------------------------------------------|
| Pre-registration                           | 1         | XYZ + threshold v Charter, ale bez α, power, exact test                  |
| Sample size adequacy                       | 0         | N=3 kill rule = noise floor                                              |
| Baseline validity                          | 1         | 5–10 manual estimation = convenience sample                              |
| Comparison fairness                        | 0         | Žádný matching, žádný synthetic control                                  |
| Confounder control                         | 0         | Žádný inventory, žádný adjustment                                        |
| Primary metric specification               | 1         | Time „handoff" undefined, no composite                                   |
| Goodhart resistance                        | 1         | Self-reported acceptance, žádný blind reviewer                           |
| Stopping rules                             | 2         | 3 thresholds defined, ale forking paths                                  |
| Replication / external audit               | 0         | Nezmíněno                                                                |
| Effect-size benchmarking                   | 1         | -50 % claim bez literature anchor                                        |
| **Total**                                  | **7/50**  | **Audit-grade fail. Charter potřebuje structural redesign, ne polish.**  |

---

## Pokud autor řekne „to je moc rigorózní pro internal method"

Standardní pushback. Odpovědi:

1. **Charter sám slibuje audit-committee defensibility.** ADR-0007: *„Audit
   committee má odpověď na 'jak víte, že to funguje'."* Když tu odpověď
   nemá statistical defensibility, slib je nesplněný.
2. **Cost of rigorous design je 1 statistician × 0.2 FTE × 12 měsíců = ~50
   person-days.** Cost of *not* doing it = jedno audit committee blowup
   moment, kde Method Steward přiznává *„CI je [6 %, 79 %]"*, čímž zabije
   metodu skrz **její vlastní governance discipline**. Cheaper to invest now.
3. **Methodologie která se sama nedokáže zfalsifikovat = self-sealing belief
   system.** Pflanzer's intellectual claim je antithesis tomuto patternu.
   Bez rigorous test framework je Charter v0.2.1 *intellectually equivalent
   to SAFe success-story marketing*, což je přesně to, co Útok 12 atakoval.
4. **Není potřeba mít všechno v Phase 1.** OK přiznat: *„v0.3 Charter má
   informational metrics po N=3, decision-grade test po N=12."* Honest
   limitation > false precision.

---

## Doporučené priority pro v0.3 Charter update

V order of impact:

| Priorita | Úprava                                                                                            | Effort       |
|----------|---------------------------------------------------------------------------------------------------|--------------|
| P0       | Raise N for kill decision: 3 → 12; N=3 = informational only                                       | Editorial    |
| P0       | Pre-register exact test + α + power + MDE                                                        | 4 h          |
| P0       | Define `t_0`, `t_1` precisely; composite PflanzerIndex jako primary                                | 8 h          |
| P1       | Baseline: full population mining + survival analysis (censored)                                   | ~5 person-days |
| P1       | Propensity score matching design                                                                  | ~3 person-days |
| P1       | Blind acceptance review process (external EM panel)                                              | ~2 days setup + 12 h/pilot |
| P2       | Synthetic control / DiD secondary design                                                          | ~5 person-days |
| P2       | External replication after N=6                                                                    | Budget item  |
| P2       | Confounder inventory + adjustment plan                                                            | ~2 days     |
| P3       | Stopping for harm rule (handoff collapse)                                                         | Editorial   |
| P3       | Effect-size literature anchoring                                                                  | ~1 day desk research |

Total Phase 1 effort to make Charter actually falsifiable: **~20 person-days
+ ongoing 12 h/pilot blind review**. To je < 5 % of one pilot cycle cost.
Bez toho je ADR-0007 *Potemkin governance*.

---

## Reference

- Abadie, A. (2021). Using Synthetic Controls: Feasibility, Data Requirements,
  and Methodological Aspects. *Journal of Economic Literature*.
- Gelman, A. & Loken, E. (2014). The Statistical Crisis in Science: garden
  of forking paths.
- Cochrane Handbook for Systematic Reviews, Ch. 8: Assessing risk of bias.
- ICH E9: Statistical Principles for Clinical Trials (pre-registration,
  interim analysis, multiplicity).
- Open Science Framework: pre-registration templates.
- Devil's advocate review Útok 12 (`docs/research/synthesis/04-devils-advocate-review.md`).
- Method Charter v0.2.1 (`docs/methodology/method-charter.md`).
- ADR-0007 (`docs/decisions/0007-method-level-charter.md`).
- Fit criteria (`docs/methodology/01-filozofie-a-kdy-pouzit.md`).
