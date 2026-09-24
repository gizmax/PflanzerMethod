# ADR-0013 — Pre-registration discipline + Pflanzer Compliance Score

**Status:** Accepted (v0.3)
**Date:** 2026-05-16
**Context source:** Autoresearch round „method-falsifiability" — perspektivy 02 Data analyst (Flaw 8 forking paths + M4 preregistration), 03 Skeptický VP (Útok 6 drift / fork), 04 Akademik (Gap 1 ad-hoc rescue + Gap 5 selection bias)

## Kontext

Současný Method Charter (v0.2.1, ADR-0007) definuje XYZ hypotézu, success
threshold, kill criteria — ale **bez ex-ante registrace**:

- **Fit criteria** (`01-filozofie-a-kdy-pouzit.md`) lze post-hoc redefinovat
  tak, aby každý neúspěšný pilot byl *„out of scope"* (Akademik Gap 1
  immunizing stratagem á la Popper-Lakatos).
- **Statistický test pro kill rozhodnutí** (α, power, MDE) není pre-specified
  → forking paths (Gelman & Loken 2014) → libovolný výsledek je publishable
  s post-hoc rationalizací.
- **„Pflanzer pilot"** není operacionálně rozlišen od *„Pflanzer-inspired"*
  variantu → drift / fork (Skeptický VP Útok 6 / Spotify pattern) je
  nedetekovatelný.
- **Charter version** není pinned per pilot → po 18 měsících metoda *„adapted
  to our context"* je success-attributována originální metodě.

Bez pre-registration discipline má Method Charter audit-grade vocabulary
**bez audit-grade evidence chain**.

## Rozhodnutí

Pflanzer v0.3 zavádí **dvě komplementární disciplíny**:

### A) Pre-registration protocol (per pilot, signed pre-Session 1)

**Pre-registration document** (artefakt v `pre-registrations/<pilot-id>.yaml`
v projektovém repu) podepsaný **PŘED** Session 1 obsahuje:

```yaml
pilot_id: P-NNNN
project_slug: <slug>
charter_version_pinned: v0.3.2  # method-charter.md SHA, ne semantic verze
signed_at: <YYYY-MM-DD>
signed_by:
  - Champion (#17)
  - Method Steward
  - Method Decider

fit_criteria:                   # registrace ex-ante kvalifikace
  applies_pflanzer:             # 7 criteria z 01-filozofie-a-kdy-pouzit.md
    - validated_problem: yes/no
    - cross_functional_decision_needed: yes/no
    - corporate_org_context: yes/no
    - ai_vibe_coding_tools_available: yes/no
    - non_throwaway_safety_floor: yes/no  # NE pro mission-critical
    - sponsor_exists: yes/no
    - champion_exists: yes/no
  anti_patterns_checked:        # 5 anti-patternů z 01.md
    - rotten_persona: pass/fail
    - single_team_scope: pass/fail
    - stakeholders_without_mandate: pass/fail
    - regulated_no_sandbox_path: pass/fail
    - vendor_outage_dependency: pass/fail
  qualification: PILOT / EXCLUDED  # binary, signed

statistical_test_preregistered:
  primary_hypothesis:
    H0: median(PflanzerIndex) ≤ 1.0
    H1: median(PflanzerIndex) > 1.0
  test: one-sided Mann-Whitney U vs propensity-matched baseline
  alpha: 0.10
  power_target: 0.80
  minimum_detectable_effect: 0.5 shift in PflanzerIndex
  sample_size_target: N=12 pilots minimum across method (not per pilot)
  multiplicity_correction: Bonferroni for secondary endpoints (×3)

primary_metric:
  composite_pflanzerindex_formula: # viz ADR-0014 (TBD)
    - time_ratio_weight: 0.40
    - acceptance_weight: 0.30
    - rework_weight: 0.20
    - nps_weight: 0.10

secondary_endpoints_preregistered:
  - blind_acceptance_external_panel
  - rework_percent_t90
  - npsl_stakeholder

protocol_deviations: []          # vyplňováno až po pilot completion
amendments: []                   # signed amendments mid-pilot (pokud nutné)
```

**Pravidla:**
- Pre-registration je **immutable** po podpisu (kromě signed amendments
  s rationale).
- Pokud pilot fail-uje fit_criteria po podpisu (např. zjištění mid-pilot),
  pilot **NESMÍ být re-classified jako EXCLUDED**. Místo toho je dokončen
  s flagem *„continued despite fit criteria deviation"* a sample je
  excluded z primary analysis (ne z secondary descriptives).
- **Method Steward udržuje OSF-style registry** pre-registrations
  (Open Science Framework template). Charter version diff mezi pre-reg a
  current method-charter.md je vždy auditovatelný.

### B) Pflanzer Compliance Score (per pilot, ex-post Method Steward audit)

**Compliance Score** = míra fidelity konkrétního pilotu vůči Pflanzer methodology.
Měřena **ex-post** Method Stewardem (audit pilot artefaktů + decision logs).

**13 must-have prvků (v0.4 upgrade — added #13):**

1. Pre-flight Discovery Readiness Gate sign-off existuje (datovaný, signed Champion + PdM).
2. Pre-flight Security & Data triage sign-off existuje (datovaný, signed Security + DPO).
3. Pre-flight Platform Triage sign-off existuje (datovaný, signed Platform Eng).
4. **Pre-registration document** (per § A) podepsaný před Session 1.
5. Charter (ADR-0004 template, projekt-level) podepsaný před Session 1.
6. Session 1 attendance ≥ 70 % Required roles podle role catalog (Track P: vč. dev #4 + #5 mandatory; Track S: dev optional).
7. Silent voting použit minimálně 1× v Session 1 (decision log evidence).
8. **Decider hlasoval poslední** (anti-HiPPO) v Session 2 — decision log evidence.
9. Hierarchie závaznosti (Critical / Yellow / Score) použita pro feedback v mezi-session.
10. **Evolve / throw-away flag** v Charteru podepsaný sponzorem (per ADR-0005 v0.4 — default = evolve, throw-away opt-in pro 3 use cases).
11. Sign-off package obsahuje **track-příslušné artefakty** (per `07-handoff-do-vyvoje.md`: Track P = audit trail; Track S = precision spec ≥ 80/100 + 5-stage handoff ritual).
12. **AI Act Fáze C final classification** podepsaná DPO (per Útok 4 v0.3 resolution).
13. **Track designation + justification (v0.4, per ADR-0020):** Charter má explicit Track P (default) nebo Track S declaration. Pokud Track S, MUSÍ být doložen 1 ze 4 hard triggers + evidence (distributed dev ≥ 3 TZ / AI Act High-risk / FDA-IEC-DO178C-PSD2 / sponsor mandate). Method Steward validuje v Track-S Trigger Validation pre-flight (per `03-pre-session-priprava.md`).

**Skóre interpretation (v0.4 — adjusted for 13 elements):**

| Score | Status pilot pro method-level metrics |
|-------|---------------------------------------|
| **11-13 / 13** | **Pflanzer pilot.** Započítává se do XYZ hypothesis validation. |
| **8-10 / 13** | **„Pflanzer-inspired".** Reportovaný separátně. **NEZAPOČÍTÁVÁ se** do success / kill metrics. Method Steward dokumentuje deviations. |
| **< 8 / 13** | **Pilot disqualified.** Deviations logged jako *fork candidate*. |

**Audit workflow:**
- Method Steward provede compliance audit do **30 dní po pilot handoff completion**.
- Audit report (1-pager) je součástí pilot artifact set.
- Compliance score je **transparent** — publikovaný v Method dashboardu
  (per Method Steward perspective bod #7).

**Charter version pinning:**
- Pre-registration pinned `charter_version: v0.3.X` (specific SHA).
- Compliance audit zaznamenává **delta vs pinned version** — pokud pilot
  použil novější Charter verzi (např. v0.4.0 mid-pilot), delta je logged.
- Method Steward agreguje deltas → input do T+12 review *„drift detection"*.

## Důsledky

**Pozitivní:**
- **Falsifiability restored** — fit criteria signed ex-ante eliminuje
  immunizing stratagem (Popper).
- **Forking paths uzavřeny** — statistický test, α, power, sample size target
  jsou pre-registered, ne post-hoc selected.
- **Drift / fork detekovatelný** přes Charter version pinning + compliance score.
- **Audit committee defensibility** — *„byl pilot Pflanzer pilot?"* má
  reproducible, audit-trail-backed odpověď.
- **Method-level metrics jsou clean** — *„Pflanzer-inspired"* piloty nezkreslují
  primary hypothesis validation.

**Negativní:**
- **Overhead per pilot**: pre-registration + compliance audit = ~3-4 hodiny
  Method Steward + ~1 hodina Champion pre-reg signoff. Realisticky **~0.5 PD
  per pilot navíc**, započítané v True Cost Worksheet (`03-pre-session-priprava.md`
  Krok 1a).
- **Některé piloty budou disqualified** (score < 10). To je **intentional** —
  bez disqualification rule je metoda nedefinovatelná. Disqualified piloty
  vedou k learning, ne k success claim.
- **Compliance score je politicky citlivý** — pilot, který Champion považoval
  za úspěch, ale score < 10 → Pflanzer adoption skeptik. Mitigace: Steward
  publikuje **both** signál (operational success per Champion + compliance per
  Method Steward).

**Mitigace:**
- **Amendments protocol** dovoluje mid-pilot adjustments s signed rationale —
  flexibilita bez fraud (akademický standard pre OSF amendments).
- **Compliance audit** je transparent: Champion má právo dispute findings
  na T+12 review (escalable na Method Decider).
- **„Pflanzer-inspired" tracking** je **non-pejorative** — některé adaptations
  jsou legitimní (Spotify model legitimization paradox). Fork governance
  ADR-0015 (P2 backlog) bude formálně rozlišovat *„adapted variant"* vs *„drift"*.

## Update existující dokumentace

- `ADR-0007` — addendum: *„Pre-registration a Compliance Score per ADR-0013."*
- `method-charter.md` — nové sekce *„Pre-registration protocol"* a *„Pflanzer
  Compliance Score"*.
- `03-pre-session-priprava.md` — pre-flight checklist přidává řádek *„Pre-registration
  document signed (per ADR-0013)"*.
- `tool/templates/` — nová šablona `pre-registration.yaml.template`.

## Out of scope (deferred to follow-up PRs)

- **ADR-0014** (TBD P1) — Composite PflanzerIndex formula detail (váhy,
  normalization, edge cases).
- **ADR-0015** (TBD P2) — Fork governance (variant fork povolen jen s Method
  Decider sign-off + dedicated ADR + vlastní XYZ).

## Reference

- Popper, K. (1959). *The Logic of Scientific Discovery* — falsifiability principle.
- Lakatos, I. (1970). *Falsification and the Methodology of Scientific Research
  Programmes* — degenerating research programmes.
- Gelman, A. & Loken, E. (2014). *The Statistical Crisis in Science: garden
  of forking paths*.
- Open Science Framework — pre-registration templates.
- ICH E9 — Statistical Principles for Clinical Trials (pre-registration discipline).
- Devil's Advocate review Útok 12.
- Autoresearch perspektivy 02 (Data analyst), 03 (Skeptický VP), 04 (Akademik).