# ADR-0020 — Dual-track model (Track P preferred, Track S fallback)

**Status:** Accepted (v0.4)
**Date:** 2026-05-28
**Context source:** User clarification 2026-05-28 + autoresearch `docs/research/dual-track-design/`

## Kontext

Pflanzerova metoda v0.3 definuje *„single track"*: 2-session cross-functional
workshop s dev #4 a #5 v room, output = produkt. User clarification 2026-05-28
explicitně potvrdil tuto pozici jako **preferred**, ale dodal **fallback**:

> *„V ideálním případě chci aby výstupem Pflanzer metody byl hotový produkt,
> proto je tam na začátku developer. Pokud tam ale nebude, bude možné mít
> jako výstup precizní speccu a ta se dá na vývoj. Ale není to preferovaná
> cesta."*

Bez explicit dual-track architektury Pflanzer riskuje:

1. **Adoption gravity** — organizace bez dev availability převede Pflanzer
   na *„yet another spec-driven workshop"*, čímž ztrácí všech 5 USPs
   (per `docs/research/dual-track-design/02-industry-comparative.md`).
2. **Inconsistent positioning** — marketing slibuje produkt, methodology
   v audit-grade scenarios produkuje spec. Buyer confusion.
3. **Spotify precedent** — *„aspirational, never fully implemented"*. Bez
   strukturální obrany Track P degraduje na Track S over time.
4. **Convergence k SDD** — fallback bez differentiation = Spec Kit / Kiro
   rebranding.

## Rozhodnutí

Pflanzer v0.4 zavádí **dual-track model**:

### Track P (Preferred, default ~80 % cases)

**Dev #4 + #5 v room od minuty 0** celý Session 1 (3-6h).

**Pre-flight requirements:**
- Charter potvrzuje track = P (default, zero-friction)
- EM podepisuje dev availability commitment (full Session 1 attendance)
- Builder lead = dev v driver-seat AI co-pilot session (NE facilitátor s AI proxy)

**Session 1 mechanika:**
- AI co-pilot generuje 3 paralelní **produkční-ready varianty** na sandbox URL
- Dev (#4 + #5) commits real code, ne pseudo-code
- Sandbox = staging-grade environment (network default-deny, audit logging,
  syntetický data, but full Vite/React/TS/ESLint/Vitest production setup)
- Quality gates running real-time: lint, types, tests, security (SBOM, secret scan),
  a11y (axe-core), build, observability hooks

**Session 2 output:**
- Winner varianta z 3 paralelních
- Sign-off package = audit trail (decision log, AI Act Fáze C, DORA 7y log,
  compliance evidence) — **NE re-impl spec**
- D11-14: dev tým (same people) polish + observability + monitoring +
  edge cases → production deploy

**Reinforcement T+7/30/60/90:**
- T+7: production deploy stability
- T+30: user adoption / feature usage metrics
- T+60: re-work % vs baseline
- T+90: PflanzerIndex composite vs propensity-matched baseline

**Quality gates ≥ 80/100 = production prerequisite**, ne *„prototype hardening
checklist"*.

### Track S (Fallback ~20 % cases)

**Dev #4 + #5 NOT v room.** 4 hard triggers gate-keeping:

1. **Distributed dev tým ≥ 3 časové pásma** — sync 3h Session 1 nemožný
2. **AI Act High-risk + certified production** — Annex IV traceability requires
   separate impl
3. **FDA / IEC 62304 / DO-178C / PSD2 SCA** — regulated certified production
4. **Sponsor mandate spec-as-deliverable** — multi-vendor, legacy modernization,
   acquisition DD

**Bez jednoho z 4 triggers Track S = projekt odložit**, ne přepnout. Method
Decider (per ADR-0011) má autoritu hard-gate.

**Pre-flight requirements:**
- Charter potvrzuje track = S + justification (který z 4 triggers + evidence)
- EM + Sponsor **dual-signature** (žádný single-signer override)
- 5. pre-flight track: Trigger Validation by Method Steward

**Session 1 mechanika:**
- Spec authors (PdM, UX, BE/API lead pokud available, Solution Architect) +
  facilitátor + AI co-pilot
- AI generuje **1-3 reference prototypy** (lightweight, ne production-ready)
  jako navigation aid pro spec
- Cross-fn alignment (Security, Legal, DPO, A11y) stejně jako Track P
- Anti-HiPPO Decider voting last

**Session 2 output:**
- Winner spec ≥ 80/100 quality gate (12 dimensions, viz expert 3 doc)
- Reference prototype z Session 1 = combined SoT s spec (anti-drift weapon)
- Sign-off package = spec navigation + audit trail
- AI Act Fáze C signed
- 5-stage handoff ritual triggered

**5-stage handoff ritual (Track S unique):**
1. 90-min walkthrough (PdM + dev lead + spec authors)
2. 5-day Q&A window (dev tým může klást otázky, spec authors odpovídají)
3. Amendment protocol (dev requests changes, sponsor approves)
4. First milestone review (dev demos first slice, spec authors verify alignment)
5. T+30 embedded reviewer (spec author shadows dev sprint, detect drift early)

**Reinforcement T+7/30/60/90:**
- T+7: handoff walkthrough completed, Q&A active
- T+30: dev first milestone demo, drift assessment
- T+60: implementation progress vs spec, spec amendments tally
- T+90: production deploy outcome, re-impl gap measurement (target ≤ 15 %)

**Quality gates ≥ 80/100 = spec ready-for-handoff prerequisite**.

### Decision tree

```
[Charter draft]
   ↓
[Pre-flight: Discovery Readiness Gate ✅]
   ↓
Q1: Můžeš mít dev #4 + #5 v room po celý Session 1 (3-6h)?
   ├─ ANO → Track P (preferred, default)
   │         Žádné explicit signature, zero-friction.
   │
   └─ NE → Q2: Splňuje projekt jeden z 4 Track S triggers?
            ├─ ANO → Track S (fallback, justified)
            │         EM + Sponsor dual-signature.
            │         5. pre-flight track: Trigger Validation.
            │
            └─ NE → ⛔ Odložit projekt. Vyřešit dev availability.
                   Track S NESMÍ být easy escape hatch.
```

### 10 strukturálních guards proti adoption gravity

1. 4 hard triggers pro Track S (above)
2. 5. pre-flight track: Trigger Validation (Method Steward audit)
3. Charter dual-signature gate (EM + Sponsor) for Track S
4. Compliance Score #13 element — track + justification audit (ADR-0013 upgrade)
5. PflanzerIndex per-track penalty — Track S measured at T+90 (full prod deploy
   cycle), Track P at T+14 (ADR-0014 upgrade)
6. Method Steward quarterly review — > 50 % Track S / BU triggers ADR-0011
   Method Decider emergency review
7. Track S effort visibly higher in Charter — 15-20 PD vs Track P 10 PD
8. Pricing differential — Track S +30-50 % premium nad Track P (Tom decision pending)
9. Decider canonical voice — *„Track S je kompromis, ne volba"* v methodology copy
10. Marketing NEVER sells Track S directly — FAQ-only, never hero/CTA

## Throw-away / evolve ortogonálně (per ADR-0005 v0.4 rewrite)

Track × Output = 2×2 matrix, ne nested:

| | Evolve | Throw-away |
|-|--------|-----------|
| **Track P** | 75 % (default lean, prod) | 5 % (discovery only) |
| **Track S** | 18 % (spec → impl) | 2 % (DD artifact) |

Sponzor explicit volba per Charter (track + output).

## Differentiation Track S vs SDD (Spec Kit / Kiro / OpenSpec / BMAD)

Track S MUSÍ zachovat všech 5 Pflanzer USPs, jinak konverguje k SDD-lite:

1. **Non-tech v room** — Security/Legal/DPO/A11y/UX writer/CS proxy v Session 1
2. **Score závaznosti + AI deflation** — 1-5 Likert + rationale per role
3. **Pre-flight triage 4+1 tracks** — Discovery + Security + Legal + Platform +
   **Trigger Validation** (5. track unique pro Track S)
4. **AI Act native compliance** — Fáze A/B/C signed, DORA 7y log
5. **Anti-HiPPO Decider** — sponsor hlasuje poslední

**Plus Track S unique anti-drift:**
- Reference prototype z Session 1 jako combined SoT s spec (žádný SDD má)
- Spec quality gate ≥ 80/100 / 12 dimensions
- 5-stage handoff ritual s explicit SLA
- 30-day spec expiry (forces refresh)
- T+30 embedded spec author shadowing

Track S re-impl gap target ≤ 15 % (vs SDD 9.8-42.1 % per Yan et al. 2025).

## Důsledky

**Pozitivní:**
- Honest positioning — preferred path + fallback s explicit gate-keeping
- Track P zachovává marketing claim („hotový produkt") konzistentně
- Track S addresses regulated reality bez compromise USPs
- 10 strukturálních guards chrání proti adoption gravity (Spotify precedent)
- Track S re-impl gap dramatically lepší než SDD (5-15 % vs 9.8-42.1 %)

**Negativní:**
- 2 tracks = vyšší cognitive load pro adopters
- Track S effort 50-100 % vyšší než Track P → vyšší cost
- Pricing differential vyžaduje sales process design
- 20 dokumentů needs sweep pro track-awareness (~16h effort)

**Mitigace:**
- Decision tree (above) je single-question gate (dev v room? Yes/No + 4 triggers)
- Track S effort přiznán v Charter — sponsor sees real cost upfront
- Method Steward quarterly review eviduje track ratio per BU — drift detection
- ADR-0005 rewrite + glossary update minimize confusion

## Update existing dokumentace

- ADR-0005 — full rewrite (v0.4, 2×2 matrix track × output)
- ADR-0011 — addendum emergency review trigger (> 50 % Track S ratio)
- ADR-0013 — upgrade Compliance Score 12 → 13 (element #13 = track + justification)
- ADR-0014 — upgrade PflanzerIndex per-track aggregation (T+14 Track P, T+90 Track S)
- `00-tldr.md`, `00-lean-pflanzer.md`, `01-filozofie`, `02-role-catalog`,
  `03-pre-session-priprava`, `04-session-1`, `05-mezi-sessions`, `06-session-2`,
  `07-handoff-do-vyvoje` — track-aware sweep
- `glossary.md` — Track P, Track S, dev-in-room definice
- `09-srovnani-existujici-metody.md` — Pflanzer Track P + Track S rows
- `tool/templates/precision-spec-track-s.md.template` — NEW (735 ř., per expert 3)
- `website/index.html` — sekce 02b track context, comparison matrix split
- `website/1-pager.html` — track designation field

## Open questions — RESOLVED (Tom decisions 2026-05-28)

All 5 strategic questions resolved with Recommended defaults:

1. ✅ **Pricing differential** — Track S = **Track P × 1.4 (+40 % premium)**.
   Track P €15-80k → Track S €40-112k (audit-grade floor €40k, top +40 %).
2. ✅ **Marketing strategy** — **Current state** (Track S in comparison matrix
   as chartreuse-dim row + sekce 02b moss-bordered footnote „kdyz dev v room
   nemůže"). Nikdy v hero/CTA.
3. ✅ **ADR-0013 Compliance Score upgrade** — **Accepted**. Element #13 added:
   *„Track designation + justification (if Track S, evidence of 1 of 4 hard
   triggers)"*. Compliance Score scale shifted 12 → 13. Tier thresholds:
   Pflanzer pilot 11-13/13, Pflanzer-inspired 8-10/13, disqualified < 8/13.
4. ✅ **ADR-0014 PflanzerIndex per-track** — **Accepted**. Per-track measurement
   windows (Track P T+11-14 final, Track S T+60-90 final), separate
   `median_P` and `median_S`, combined index for XYZ validation. Track S adds
   explicit `ReImplGap_S` metric (target ≤ 15 %, critical > 25 %).
5. ✅ **ADR-0011 Default Sunset trigger** — **> 50 % Track S/BU per quarter**
   triggers Method Decider emergency review within 14 days. Steward audituje
   quarterly Compliance Score #13.

All 5 decisions reflected in:
- ADR-0011 v0.4 addendum (Track S adoption emergency trigger)
- ADR-0013 v0.4 upgrade (12 → 13 elements)
- ADR-0014 v0.4 addendum (per-track aggregation + ReImplGap_S)
- `method-charter.md` § Success threshold (per-track PflanzerIndex note)
- `website/index.html` comparison matrix (Track S €40-112k +40 %)

## Reference

- `docs/research/dual-track-design/01-methodology-architecture.md` (1073 ř.)
- `docs/research/dual-track-design/02-industry-comparative.md` (533 ř.)
- `docs/research/dual-track-design/03-precision-spec-engineering.md` (1246 ř.)
- `docs/research/dual-track-design/04-synthesis.md`
- User clarification 2026-05-28
- ADR-0005 v0.4 (rewrite) — Track × Output 2×2 matrix
- ADR-0001 Decider eskalační protokol (compatible)
- ADR-0007 Method Charter (compatible)
- ADR-0011 Method Decider + Default Sunset (addendum needed)
- ADR-0012 Method Steward operational scope (compatible)
- ADR-0013 Pre-registration + Compliance Score (upgrade 12→13 needed)
- ADR-0014 PflanzerIndex (upgrade per-track needed)
- ADR-0015 Positioning vs AI-DLC (compatible)

**Industry data podporující Track P preference:**
- DORA 2024: handoff = 8 % throughput penalty
- Bain/Clarity 2026: 70 % enterprise projects fail (stakeholder alignment gap)
- Questworks: 30-40 % dev time lost na poor handoff
- Spec Kit (Scott Logic 11/2025): 2 577 ř. MD / 689 ř. kódu, 10× slower
- Yan et al. 2025: 9.8-42.1 % spec-impl mismatch (SDD)

**Adoption gravity precedents:**
- Spotify squads → component teams (aspirational, never fully implemented)
- SAFe XP pair programming 22 % → 3.5 % current (84 % drop-off)
- Agile/AgileFall: only 4 % real agility (Matt LeMay)
- Shadow IT 70 % companies → default architecture
