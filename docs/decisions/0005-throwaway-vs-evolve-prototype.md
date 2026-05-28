# ADR-0005 — Track × Output matrix (v0.4 rewrite)

**Status:** Accepted (v0.4) — **supersedes v0.2 „default = throw-away"**
**Date:** 2026-05-05 (original); **2026-05-28 (v0.4 rewrite)**
**Context source:** User clarification 2026-05-28 + autoresearch
`docs/research/output-consistency/` + `docs/research/dual-track-design/`

## v0.4 supersession addendum

Původní ADR-0005 řekl: *„Default = throw-away. Produkce se píše znovu jako
specs-driven re-implementation."* User clarification 2026-05-28 řekl:
*„Výstup z Pflanzer metody je hotový produkt. Pokud dev není v room,
fallback je precision spec — ne preferovaná cesta."*

Tyto dvě věty se vylučují. v0.4 ADR-0005 rewrite reflektuje user pozici:
**default = evolve s programátorem v room od minuty 0**. Throw-away je
explicit opt-in pro 3 use cases (discovery pilot, audit-grade evidence,
regulated certified production). **Track × Output je 2×2 ortogonální
matice**, ne nested rozhodnutí.

## Kontext

Pflanzerova metoda od v0.4 zavádí **dual-track model** (ADR-0020):

- **Track P (preferred ~80 %)** — dev #4 + #5 v room od minuty 0; output = produkt
- **Track S (fallback ~20 %)** — dev není v room (4 hard triggers gate-keeping);
  output = precision spec ≥ 80/100

A historickou **throw-away vs evolve** dichotomy (kdy prototyp jde do prod
vs se zahodí). v0.4 udržuje obě dimenze, ale **ortogonálně** — tj. 4
kombinace, ne 2 (throw-away = always discard) nebo nested
(throw-away = sub-case evolve).

## Rozhodnutí

### 2×2 Track × Output matrix

```
                    EVOLVE                          THROW-AWAY
                    (deliverable goes to prod)      (deliverable discarded)
TRACK P             ┌─────────────────────────────┬─────────────────────────────┐
(dev in room,       │ Track P + evolve            │ Track P + throw-away        │
 output = product)  │ ≈ 75 % cases (default lean) │ ≈ 5 % cases (discovery only)│
                    │                             │                             │
                    │ Winner varianta → prod.     │ Functional artifact slouží  │
                    │ Dev byl v room, žádná       │ k falsifikaci XYZ.          │
                    │ re-implementace.            │ Po Session 2 zahozen.       │
                    │                             │ Sponzor explicit Charter    │
                    │ Quality gates ≥ 80/100      │ flag „discovery-only".      │
                    │ jako production prerequisite│                             │
                    ├─────────────────────────────┼─────────────────────────────┤
TRACK S             │ Track S + spec-as-deliverable│ Track S + throw-away       │
(dev NOT in room,   │ ≈ 18 % cases (Track S      │ ≈ 2 % cases (DD artifact,   │
 output = spec)     │  default)                  │  acquisition)               │
                    │                             │                             │
                    │ Spec ≥ 80/100 → dev tým.   │ Spec produkována pro        │
                    │ 5-stage handoff ritual      │ alignment / DD evidence,    │
                    │ + reference prototype.      │ ne implementaci.            │
                    │                             │ Sponzor explicit flag.      │
                    └─────────────────────────────┴─────────────────────────────┘
```

### Default volba

**Default = Track P + evolve** (75 % case rate). Charter sponzor:
- Označí Track P (default) NEBO Track S (s justification per 4 triggers — viz ADR-0020).
- Označí evolve (default) NEBO throw-away (s use case rationale).

Žádná default = throw-away (v0.2 protiklad odstraněn).

### Throw-away explicit opt-in — 3 valid use cases

1. **Discovery-only pilot** — XYZ falsifikace, žádný produkční záměr.
   Charter má success metric = *„team alignment + go/no-go decision"*,
   ne *„production deploy"*.

2. **Audit-grade evidence collection separate od prod** — pilot vyrobí
   artifact pro compliance / regulatorní show-case (např. AI Act Annex IV
   demonstrability), ale prod implementation běží separate track v normálním
   SDLC.

3. **Regulated certified production** — FDA, IEC 62304, DO-178C, PSD2 SCA
   environments kde change-of-record proces vyžaduje separate verified
   implementation. Pflanzer pilot vyrobí spec / reference, certified impl
   běží paralel.

### Track P × Output × Quality gate

**Track P + evolve (default):**
- Quality gates ≥ 80/100 = **production prerequisite**, ne *„prototype hardening checklist"*
- 7 gates: lint, types, tests, security, a11y, build, observability
- Sandbox = production-grade prostředí (24h TTL → continuous deploy after Session 2 sign-off)
- Sign-off package = audit trail, **ne** re-impl spec
- Dev tým byl v room → žádná handoff fáze

**Track P + throw-away (discovery-only):**
- Quality gates ≥ 60/100 (lower threshold — artifact slouží alignmentu)
- Sandbox 24h TTL, žádný prod deploy
- Sign-off package = decision log only

### Track S × Output × Quality gate

**Track S + spec-as-deliverable (Track S default):**
- Spec quality gate ≥ 80/100 (12 dimensions per ADR-0020)
- Reference prototype z Session 1 = combined SoT s spec (anti-drift)
- 5-stage handoff ritual: 90-min walkthrough → 5-day Q&A → amendment protocol → first milestone review → T+30 embedded reviewer
- Dev tým implementuje per spec + reference prototype
- Reinforcement T+7/30/60/90 = spec implementation monitoring (drift detection)

**Track S + throw-away (DD only):**
- Spec quality gate ≥ 70/100
- Žádný handoff (spec is the artifact for stakeholder reference, ne impl)
- Charter flag „DD/acquisition" explicit

## Konsekvence

**Pozitivní:**
- Eliminuje protiklad mezi marketing claim („hotový produkt") a methodology
  (throw-away default).
- Throw-away zachován jako concept pro 3 valid use cases (~7 % total).
- 2×2 matrix je clear, dokumentovatelná, sponzor volí explicitně v Charteru.
- Compatible s ADR-0020 dual-track model.

**Negativní:**
- Existing pilots / documentation mají v0.2 wording (*„default throw-away"*).
  Sweep ~6 souborů needed.
- Sponzori, kteří Pflanzer adoptovali jako *„throw-away workshop"*, musí
  re-orientovat na Track P + evolve default.

**Mitigace:**
- v0.4 supersession addendum (above) je breadcrumb pro existing users.
- Glossary.md (`docs/methodology/glossary.md`) má anti-patterns deprecated
  language table — surface clear migration path.
- Method Steward T+6 review (per ADR-0011/ADR-0012) eviduje track/output
  combination — pokud > 50 % pilots stay v throw-away mode, emergency
  review trigger.

## Update existing dokumentace

- `00-tldr.md` — Track P/S framing v intro (v0.4)
- `00-lean-pflanzer.md` — Track P jako default lean (v0.4)
- `01-filozofie-a-kdy-pouzit.md` — decision tree update
- `03-pre-session-priprava.md` — Charter dual-signature gate (EM + Sponsor)
- `04-session-1.md` — Track P + Track S Session 1 mechanika
- `06-session-2.md` — output per track
- `07-handoff-do-vyvoje.md` — kompletní rewrite (Track P = no handoff,
  Track S = 5-stage ritual)
- `glossary.md` — Track P, Track S, evolve, throw-away definice
- ADR-0013 — upgrade Compliance Score 12 → 13 (element #13 = track + justification)
- ADR-0014 — upgrade PflanzerIndex per-track aggregation
- ADR-0020 — NEW (dual-track model full spec)

## Out of scope (deferred)

- **Pricing structure** pro Track P vs Track S — Tom decision pending (Expert
  recommendation: +30-50 % premium for Track S due to higher effort 15-20 PD)
- **Marketing copy strategy** — Track S FAQ-only vs explicit website mention
  (Tom decision pending)

## Reference

- ADR-0020 — Dual-track model (full spec)
- `docs/research/dual-track-design/04-synthesis.md` — synthesis
- `docs/research/output-consistency/03-synthesis.md` — audit findings
- User clarification 2026-05-28
- Savoia, A. *The Right It* — pretotyping (still relevant pro discovery-only).
- Cagan, M. — discovery vs delivery prototypes.
