# ADR-0014 — Composite PflanzerIndex formula

**Status:** Accepted (v0.3 P1)
**Date:** 2026-05-17
**Context source:** Autoresearch round „method-falsifiability" — perspektiva 02 (Data analyst M1 composite metric); follow-up P1-1 z `docs/research/method-falsifiability/07-recommendations.md`. Referencováno z `method-charter.md` § Success threshold a `tool/templates/pre-registration.yaml.template` jako TBD.

## Kontext

Method Charter v0.3 (`method-charter.md`) definuje 4 primary metriky pro pilot
hodnocení: time-to-handoff, handoff acceptance (operational + blind), re-work %,
stakeholder NPS. Pre-registration template referencuje **composite PflanzerIndex**
jako primary metric pro Mann-Whitney U test, ale **formula váhy a normalization
zůstaly TBD**.

Bez finalized composite metric:
- **Forking paths:** každý pilot může post-hoc zvolit „best metric" pro reporting.
- **Trade-off invisibility:** projekt s rychlým handoffem ale vysokým re-workem
  vypadá stejně jako projekt se slow handoffem ale low re-work.
- **Mann-Whitney U test** (preregistered) nelze spustit bez single continuous
  PflanzerIndex hodnoty per pilot.
- **Comparison s baseline** je apples-to-oranges, protože baseline má jiné
  metric availability (např. baseline nemá blind acceptance panel).

Tato ADR finalizuje formula, normalization, missing data handling, a edge cases.

## Rozhodnutí

### Formula (PflanzerIndex)

```
PflanzerIndex = 0.40 × TimeRatio_norm
              + 0.30 × Acceptance_blind_norm
              + 0.20 × (1 - ReworkRate_norm)
              + 0.10 × NPS_norm
```

Kde:
- **TimeRatio_norm** ∈ [0, 2] — viz § Normalization níže.
- **Acceptance_blind_norm** ∈ [0, 1] — blind external EM panel score / 100.
- **ReworkRate_norm** ∈ [0, 1] — clamped re-work %; inverze (1-x), protože
  nižší re-work = lepší.
- **NPS_norm** ∈ [0, 1] — NPS shifted from [-100, +100] do [0, 1].

**Interpretace:** PflanzerIndex > 1.0 = pilot performed lépe než propensity-matched
baseline. Pre-registered H1 testuje median(PflanzerIndex) > 1.0 napříč N=12 piloty.

**Váhy rationale:**
- **0.40 time** — primary lagging metric (XYZ hypotéza je o čase) + objektivní
  (git timestamps, low gaming). Highest weight.
- **0.30 acceptance** — kvalita handoffu; blind panel anti-Goodhart.
- **0.20 re-work** — guardrail; nesmí být primární (Pflanzer by mohl pomalu
  produkovat dokonalý handoff a vypadat dobře). Nižší než acceptance, protože
  re-work má T+90 latency a vyšší noise.
- **0.10 NPS** — sentiment proxy; survey bias risk. Lowest weight, ale present
  jako tie-breaker.

Váhy jsou **pre-registered v ADR-0013 protokolu**; změna váh je amendment
vyžadující Method Decider sign-off + signed rationale.

### Normalization (per metric)

#### TimeRatio_norm

```
TimeRatio_raw = baseline_class_median_time / pilot_time
TimeRatio_norm = clamp(TimeRatio_raw, 0.5, 2.0)
```

- **Baseline_class_median_time** = median time-to-handoff napříč propensity-matched
  baseline projekty stejné Project Class (A/B/C/D, viz future P1-5 doc).
- **Pilot_time** = od signed Charter timestamp do first commit s `#handoff` tag.
- **Clamp [0.5, 2.0]** zabraňuje outlier kontaminaci — extreme pilot (např.
  10× rychlejší) má teoreticky možnou hodnotu 10.0, ale flagujeme jako anomálii
  a clamp na 2.0. Symmetric pro 10× pomalejší.
- Hodnota **1.0 = baseline parity**, **2.0 = 50% reduction (XYZ target met)**,
  **0.5 = 50% slowdown**.

#### Acceptance_blind_norm

```
Acceptance_blind_norm = mean(blind_panel_scores) / 100
```

- 3 EMs z jiných BU hodnotí stripped artefakty Likertem 0-100 (per ADR-0012
  § Separation of advocate and measurer).
- Mean across 3 raters; pokud std > 25, flagujeme „high disagreement" a
  Method Steward kvalitativně reviewuje.
- Hodnota **1.0 = unanimous full acceptance**, **0.6 = threshold per pre-registration**.

#### ReworkRate_norm

```
ReworkRate_raw = code_churn_t90 / loc_initially_committed
ReworkRate_norm = clamp(ReworkRate_raw, 0, 1)
formula_input = 1 - ReworkRate_norm
```

- **Code_churn_t90** = LOC changed in feature files T+0..T+90 (`git log --numstat`,
  filter `git log --since=handoff --author!=bot --pretty=format:'' --name-only`).
- **LOC_initially_committed** = LOC v handoff commit.
- Clamp [0, 1] — re-work > 100 % původního commitu = clamp na 1.0 (= total
  rewrite, worst case).
- Inverze (1-x) v formule, protože **nižší re-work = lepší**.

#### NPS_norm

```
NPS_norm = (NPS + 100) / 200
```

- NPS range [-100, +100] (Reichheld 2003), normalizováno na [0, 1].
- Hodnota **0.6 = +20 NPS** (threshold per pre-registration).
- Hodnota **0.5 = neutral (NPS=0)**, **1.0 = perfect (+100)**.
- Response rate < 50 % = NPS_norm = `null`, treated per § Missing data níže.

### Missing data handling

| Scenario | Action |
|----------|--------|
| 1 metrika missing (např. NPS response rate < 50 %) | **Re-weight** zbývající 3 metriky proporcionálně (0.4/0.3/0.2 → 0.44/0.33/0.22). Flag „1 metric imputed" v pilot report. |
| 2 metriky missing | Pilot **disqualified z primary analysis**, reportován v secondary descriptives. |
| Re-work data T+90 ještě neexistují (pilot < 90 dní starý) | PflanzerIndex_interim = pouze 3 metriky (re-weighted); finalní PflanzerIndex computed at T+90. Interim flag v dashboardu. |
| Baseline class median chybí (nedostatek matched baseline projects) | Pilot **excluded z primary analysis**; reportován jako case study. Method Steward flag pro Project Class Taxonomy revision. |
| Handoff collapse (≤ 20 % blind acceptance, ≤ 10 % artifact use) | Stopping-for-harm trigger; PflanzerIndex = 0; pilot reported separátně. |

### Edge cases

**1. Censored time observations.** Pilot cancelled mid-cycle, no `#handoff` tag
ever committed:
- Censored = include v primary analysis s **survival analysis treatment** (Kaplan-Meier).
- Pro PflanzerIndex computation: pilot_time = T+max(cycle_days), TimeRatio_norm
  = clamp([baseline/T_max], 0.5, 2.0).
- Flag „censored" v pilot report.

**2. Negative re-work.** Pilot s handoffem, který dev tým vůbec nezačal používat
(handoff acceptance = 0): no LOC changed = re-work = 0. Ale to není „dobrá"
hodnota.
- Defensive rule: pokud Acceptance_blind_norm < 0.2, ReworkRate_norm = `null` →
  fall back na 2-metric formula (re-weight zbývající 2 metriky 0.4/0.3 → 0.57/0.43).

**3. Baseline class < 5 matched projects.** Underpowered comparison:
- Použij broader class (např. A+B sloučené) nebo cross-class median jako fallback.
- Flag „underpowered baseline" v pilot report; cite v Method Steward T+6 review.

**4. Extreme PflanzerIndex (> 2.0 or < 0.3).** Sanity check trigger:
- Method Steward manual review do 7 dní po pilot completion.
- Možné příčiny: instrumentation bug, anomalous baseline match, cherry-pick
  bias. Document v audit report.

### Reporting

**Per-pilot report (Method Steward, T+90):**

```yaml
pilot_id: P-NNNN
pflanzerindex:
  composite: 1.42  # > 1.0 = pilot lepší než baseline
  components:
    time_ratio_norm: 1.85
    acceptance_blind_norm: 0.72
    rework_rate_norm: 0.18  # inverted as (1-x) = 0.82 in formula
    nps_norm: 0.65
  weights_applied:
    time: 0.40
    acceptance: 0.30
    rework: 0.20
    nps: 0.10
  missing_data: []
  flags: []
  baseline_class: B
  baseline_n_matched: 8
```

**Method-level report (Method Steward, T+6 mo aggregated):**

- Median PflanzerIndex (Pflanzer piloty s compliance score ≥ 10/12).
- 95% Wilson CI (using order statistics).
- One-sided Mann-Whitney U test vs pooled baseline distribution.
- Per-component decomposition (which metric driving the result).
- Subgroup analysis pre-registered: per Project Class (NOT per BU, per
  Champion, per quarter — to prevent forking).

### Pre-registration immutability

Váhy (0.40/0.30/0.20/0.10) jsou **pre-registered v ADR-0013 protokolu**. Změna
vyžaduje:
- Signed amendment Method Steward + Method Decider.
- Rationale s evidence (např. „posledních 6 pilots showed re-work T+90 measurement
  unreliability, lowering weight from 0.20 to 0.10").
- **Amendment se aplikuje pouze na future piloty**, ne retroactively. Historical
  data se přepočítají pro reporting transparency, ale primary test používá
  váhy platné při pre-registration každého konkrétního pilotu.

## Důsledky

**Pozitivní:**
- **Single continuous metric** umožňuje Mann-Whitney U test (per ADR-0013
  pre-registration spec).
- **Váhy reflect priority hierarchy** — time primary, acceptance kvalita,
  re-work guardrail, NPS sentiment.
- **Goodhart resistance** přes 4-way composite (žádná metrika sama nemůže
  drive PflanzerIndex k cíli).
- **Missing data handling** explicit — žádné silent re-weighting nebo
  imputation bez audit trail.
- **Edge case rules** zabraňují *„this pilot is special"* exceptions.

**Negativní:**
- **Composite váhy jsou subjective.** 0.40 vs 0.50 pro time je judgment call,
  ne odvozeno z first principles. Pre-registration to zachycuje, ale neeliminuje.
- **Re-work measurement** je nejméně reliable component (T+90 latency, git
  filtering complexity, definice „feature files"). Mitigace: 0.20 weight (low)
  + Jira labels jako secondary signal.
- **Baseline class taxonomy** musí existovat (P1-5 follow-up). Bez ní PflanzerIndex
  není computable.

**Mitigace:**
- **Sensitivity analysis** v Method Steward T+12 reportu: re-compute PflanzerIndex
  s alternative weights (0.5/0.3/0.1/0.1, 0.3/0.3/0.2/0.2) — pokud rank order
  pilotů zůstává stable, váhy nejsou outcome-driving.
- **Inter-rater reliability** (Cohen's κ ≥ 0.6) pro blind acceptance panel —
  pokud raters disagree, formula váhy nejsou primární problém.
- **Public formula** v `method-charter.md` + tato ADR — žádné hidden weighting.

## Implementation

- `tool/templates/pre-registration.yaml.template` — váhy already populated;
  ne další změna potřeba.
- `method-charter.md` § Success threshold — composite formula explicit
  (post-ADR-0014 commit, update tabulku to remove TBD note).
- `tool/cli/lib/` — future Python implementation `pflanzerindex.py` (P2 tool work).

## v0.4 addendum — Per-track aggregation (2026-05-28)

Per ADR-0020 dual-track model, PflanzerIndex gets **per-track measurement
windows** (Tom decision 2026-05-28, Recommended default):

### Track-specific measurement windows

| Track | TimeRatio measurement | Acceptance measurement | Re-work measurement | NPS measurement |
|-------|----------------------|------------------------|---------------------|-----------------|
| **Track P** (preferred) | Charter signed → **first prod deploy commit** (`#prod` tag) — typically T+11-14 | EM dev týmu T+30 + blind external EM panel T+30 | Code churn T+0..T+90 | Stakeholder survey T+30 |
| **Track S** (fallback) | Charter signed → **first prod deploy commit by receiving dev team** — typically T+60-90 | EM dev týmu T+60 + spec author embedded reviewer T+30 + blind external EM panel T+60 | Code churn measured against spec at T+90 | Stakeholder survey T+30 + receiving dev team survey T+60 |

### Per-track aggregation rule

Method Steward reports **two separate medians** per quarter:
- `median(PflanzerIndex_P)` — Track P pilots only
- `median(PflanzerIndex_S)` — Track S pilots only

**Combined PflanzerIndex** for method-level XYZ hypothesis validation
(per ADR-0007 method charter):

```
PflanzerIndex_combined = (count_P × median_P + count_S × median_S) / (count_P + count_S)
```

**Validation thresholds (per track):**
- Track P PflanzerIndex > 1.0 = method working (default expectation)
- Track S PflanzerIndex > 0.85 = method working (fallback accepts smaller delta)
- Combined PflanzerIndex > 1.0 = aggregate XYZ validated

### Track S re-impl gap explicit measurement

Track S has explicit **re-impl gap metric** added (not in Track P):

```
ReImplGap_S = (LOC changed by receiving dev team that differs from spec) / (LOC delivered in final prod)
```

**Target:** ≤ 15 % (per ADR-0020). **Critical threshold:** > 25 % triggers
Method Steward escalation (spec quality gate failed in retrospect).

Comparable baseline:
- Pflanzer Track P ~0 % (kód JE deliverable, no spec to drift from)
- Pflanzer Track S target ≤ 15 %
- SDD (Spec Kit, Kiro) 9.8-42.1 % (Yan et al. 2025)

### Per-track adoption tracking

Method Steward dashboard publishes monthly:
- `count_P` (Track P pilots completed this quarter)
- `count_S` (Track S pilots completed this quarter)
- `ratio_S = count_S / (count_P + count_S)`
- **Per-BU breakdown** of `ratio_S` — input to ADR-0011 v0.4 addendum
  emergency trigger (`> 50 % Track S/BU` triggers Method Decider review)

## Out of scope (deferred)

- **Project Class Taxonomy** (P1-5) — definice A/B/C/D class, prerequisita pro
  baseline_class_median_time computation. Tracked separately.
- **Propensity score matching algorithm** — implementation detail, deferred
  do baseline-collection-playbook.md (P1-3).
- **Alternative composite designs** (Bayesian, multi-criteria decision analysis) —
  P3 academic track explorace, ne practitioner-grade requirement.

## Reference

- Devil's Advocate Útok 12 + autoresearch perspektiva 02 (Data analyst) M1.
- Reichheld, F. (2003). NPS instrument.
- Kaplan, E. & Meier, P. (1958). Nonparametric estimation from incomplete observations.
- Saaty, T. (1980). *The Analytic Hierarchy Process* — composite metric weighting.
- ADR-0013 — Pre-registration protocol.
- `docs/research/method-falsifiability/02-data-analyst.md` § M1 composite PflanzerIndex.
- `docs/research/method-falsifiability/07-recommendations.md` P1-1.