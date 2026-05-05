# ADR-0003 — Role catalog v0.1 → v0.2 (povýšení, AI proxy degradace, nové role)

**Status:** Accepted
**Date:** 2026-05-05
**Context source:** synthesis 03 (role catalog updates), perspektivy 08, 10, 11, 12, 13, 14, 15

## Kontext

Role catalog v0.1 (15 rolí) byl draft před expertním panelem. Panel jednomyslně
tlačil na řadu změn — přesun „volitelných" rolí do „doporučených",
degradaci AI proxy z ✅ na ⚠️ pro role s regulatorní accountability,
a doplnění 3 chybějících rolí.

## Rozhodnutí

### A) Povýšení statusu (7 rolí)

| Role | v0.1 | v0.2 | Důvod |
|------|------|------|-------|
| #8 QA | DOPORUČENÁ pro release-grade | **POVINNÁ pro release intent** | Testovatelnost se rozhoduje v S1, ne v handoffu (8) |
| #10 Legal | VOLITELNÁ | **DOPORUČENÁ** | Vibe-coding tool = GDPR čl. 28; AI Act trigger téměř vždy (10) |
| #11 A11y | VOLITELNÁ | **DOPORUČENÁ default-on** | EAA 28. 6. 2025; obrácený gradient (11) |
| #12 Data | VOLITELNÁ | **DOPORUČENÁ** | Release intent ⇒ measurement plan + instrumentation deadline (12) |
| #13 CS | VOLITELNÁ | **DOPORUČENÁ** | Customer base > 1 000 + user-facing change (13) |
| #14 End-user | VOLITELNÁ | **DOPORUČENÁ default-on** | Customer-facing nebo nový segment; volitelná jen při fresh persona ≤ 3 mo (14) |
| #15 DevOps | VOLITELNÁ | **DOPORUČENÁ** | Téměř vždy potřeba sandbox (15) |

### B) Degradace AI proxy (4 role z ✅ na ⚠️)

| Role | v0.1 | v0.2 | Hranice |
|------|------|------|---------|
| #10 Legal | ✅ | ⚠️ | Lidský DPO pro high-risk AI Act, special categories, profiling, ADM, marketing claims, novel vendor (10) |
| #11 A11y | ✅ | ⚠️ | Pre-launch human review povinný — screen reader UX, cognitive, dynamic focus. EAA nelze atestovat AI (11) |
| #14 End-user | ✅ | ⚠️ + score deflation 0.5 | AI persona je vstup, ne výstup. Nezvládne novel insight, edge cases, say-do gap (14) |
| #8 QA | ✅ | ⚠️ | Test generation OK, lidský review každého scénáře povinný před CI (8) |

### C) Nové role (3)

- **#16 UX writer / Content designer.** Trigger: user-facing copy, error/empty
  states, marketing claims (perspektiva 06).
- **#17 Champion / Pilot lead.** Trigger: druhý+ pilot v BU, scaling. Coaching
  Kata loop (baseline 03).
- **#18 Solution / Domain architect** *(volitelně)*. Trigger: multi-team (3+),
  komplexní doména, regulovaný SDLC (perspektiva 09).

### D) Decision tree změny

- **Krok 0 — Discovery Readiness Gate** (viz ADR-0002).
- **Krok 0a — Triage tracks** (viz ADR-0002).
- **Krok 5 (QA trigger) změněn** na „jakákoli zmínka produkce/pilotu".
- **Krok 8 (A11y trigger) default-on** pro customer-facing + B2B > 250 zam.
- **Krok 12a — Multi-team scope (> 3 týmy)** → federovaný model nebo
  +Solution architect (#18).
- **Krok 13 — IP iteration mounting (SAFe)** (viz ADR — předpokládáme implicit).

### E) 3-režimová AI-human matice (viz `02-role-catalog.md`)

1. **Vlastnické a vetovací** (vždy člověk).
2. **Konzultativní** (AI + human sign-off 24–48 h).
3. **Execution-heavy / context-light** (AI vede).

## Důsledky

**Pozitivní:**
- Role catalog reflektuje regulatorní realitu 2026 (EAA, AI Act, DORA).
- AI proxy hranice explicitně, ne implicitně — žádná „rapid prototyping eskapuje
  governance" past.
- Pflanzer fit pro multi-team scope (#18) a scaling (#17).

**Negativní:**
- Default počet rolí v session vzrostl z ~5 na ~7. Mitigace: MoSCoW gradace
  vstupů, on-call sloty pro Security/Legal místo plné účasti.

**Mitigace:**
- Sanity check „> 10 lidí v místnosti = něco špatně" platí.
- Async accountability pro Security/Legal/Platform (pre-read + on-call + sign-off).

## Reference

- EAA — European Accessibility Act, EU 2019/882, accountability 28. 6. 2025.
- AI Act, čl. 6, 14, 50.
- GDPR čl. 22, 28, 35.
- DORA — supply chain + audit.
- Torres, T. *Continuous Discovery Habits* (2021).
