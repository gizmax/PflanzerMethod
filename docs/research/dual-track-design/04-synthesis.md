# Dual-Track Design — Synthesis

> Synthesis 3 paralelních expertních perspectives (May 2026):
> - `01-methodology-architecture.md` (1073 ř.) — Track P/S structural spec
> - `02-industry-comparative.md` (533 ř.) — dev-in-room consensus + adoption gravity
> - `03-precision-spec-engineering.md` (1246 ř.) — Track S spec anatomy
>
> **User clarification:**
> *„V ideálním případě chci aby výstupem Pflanzer metody byl hotový produkt,
> proto je tam na začátku developer. Pokud tam nebude, bude možné mít jako
> výstup precizní speccu — ale není to preferovaná cesta."*

---

## TLDR (5 řádků)

Pflanzer v0.4 zavádí **dual-track model**: **Track P** (preferred ~80 %) =
dev v room od minuty 0, output = produkt v prod. **Track S** (fallback ~20 %)
= dev není v room (4 hard triggers požadovány), output = precision spec
≥ 80/100 quality gate. **Track S MUSÍ zachovat všech 5 Pflanzer USPs** —
jinak konverguje k SDD-lite. **Adoption gravity je #1 risk** (Spotify
precedent: aspirational → never fully implemented) — Pflanzer chrání
strukturálně přes 10 guards (4 hard triggers + 5. pre-flight track +
visible PD differential + pricing +30-50% + Decider canonical voice +
Method Steward audit + ADR enforcement). **ADR-0005 throw-away/evolve
zůstává — ale ortogonálně k Track P/S** (4 kombinace, ne nested).

---

## Track P vs Track S — at a glance

| Dimension | Track P (Preferred) | Track S (Fallback) |
|-----------|---------------------|---------------------|
| **Dev (#4 + #5) v room** | Required, full Session 1 | Not in room (4 triggers required) |
| **Session 1 output** | 3 paralelní produkční-ready varianty na URL | 1-3 reference prototypy + precision spec draft |
| **Session 2 output** | Winner varianta → prod deploy D11-14 | Winner spec ≥ 80/100 + sign-off package |
| **Sign-off package role** | Audit trail (compliance evidence) | Spec navigation + audit trail |
| **Reinforcement T+7/30/60/90** | Production monitoring | Spec implementation monitoring |
| **Calendar time** | ~14 dní default | ~21-28 dní (incl. handoff ritual) |
| **Person-days effort** | ~10 PD | ~15-20 PD (50-100 % more) |
| **Pricing tier** | Same as default | Audit-grade tier (+30-50 % premium) |
| **Re-impl gap risk** | ~0 % | 5-15 % (vs SDD 9.8-42.1 %) |
| **Default v Charter?** | YES (zero-friction) | NO (explicit opt-in s 4-trigger justification) |

---

## 4 hard triggers pro Track S (gate-keeping)

Track S **NESMÍ** být easy escape hatch. 4 fixed triggers, žádný else clause:

1. **Distributed dev tým ≥ 3 časové pásma** — synchronní 3h Session 1 nemožný.
2. **AI Act High-risk certified production** — regulatorně MUSÍ existovat
   separate impl track (Annex IV traceability).
3. **FDA / IEC 62304 / DO-178C / PSD2 SCA** — certified production environments
   kde change-of-record proces vyžaduje spec-as-artifact.
4. **Sponsor mandate spec-as-deliverable** — multi-vendor contract, legacy
   modernization s novým dev týmem, acquisition due diligence.

**Bez jednoho z 4 triggers Track S = projekt odložit**, ne přepnout. Method
Decider má autoritu hard-gate.

---

## Track S ≠ SDD-lite — differentiation (per Expert 2)

Pflanzer Track S **MUSÍ zachovat všech 5 USPs**, jinak je to jen rebranding
Spec Kit / Kiro:

| USP | Track P implementation | Track S implementation |
|-----|------------------------|------------------------|
| Non-tech v room | Security/Legal/DPO/A11y/UX writer/CS proxy v primary session | Same — spec dělají stejně cross-functionally |
| Score závaznosti + AI deflation | 1-5 Likert + rationale field per role | Same — bodují i spec varianty |
| Pre-flight triage 4+1 tracks | Discovery + Security + Legal + Platform | **Plus 5. track: Track-S Trigger Validation** |
| AI Act native compliance | Decision log s human attribution | Spec dostává AI Act Fáze C signed |
| Anti-HiPPO Decider | Sponsor hlasuje poslední | Same — Decider rozhoduje spec winner |

**Plus Track S unique:** Reference prototype z Session 1 = anti-drift weapon
(žádný SDD framework toto nemá).

---

## 10 strukturálních guards proti adoption gravity (per Expert 2)

Adoption gravity precedents:
- Spotify squads → component teams („aspirational, never fully implemented")
- SAFe XP pair programming: 22 % lifetime / **3.5 %** current (84 % drop-off)
- Agile/AgileFall: only **4 %** real agility per Matt LeMay
- Shadow IT: **70 %** companies → „default architecture"
- Dual-Track Agile → konvergovalo na Continuous Discovery

Pflanzer obrana (10 guards):

1. **4 hard triggers** (above) — Track S NESMÍ být volba bez triggeru
2. **5. pre-flight track: Trigger Validation** — Method Steward audituje
3. **Charter dual-signature gate** (EM + Sponsor) pro Track S
4. **Compliance Score #13 element** — track + justification audit
5. **PflanzerIndex per-track penalty** — Track S = T+90 measurement vs Track P T+14
6. **Method Steward quarterly review** — > 50 % Track S/BU triggers
   ADR-0011 Method Decider review (emergency)
7. **Track S effort visibly higher** — 15-20 PD vs Track P 10 PD (transparent v Charter)
8. **Pricing differential** — Track S = +30-50 % premium nad Track P
9. **Decider canonical voice** — *„Track S je kompromis, ne volba"*
   v methodology copy + Tom hand-off rituals
10. **Marketing NEVER sells Track S directly** — FAQ-only, never hero/CTA

---

## ADR mapping & conflicts (per Expert 1)

| ADR | Status | Change |
|-----|--------|--------|
| ADR-0001 Decider model | Compatible | None |
| ADR-0004 Charter | Compatible | Add track designation field |
| ADR-0005 throw-away/evolve | **REWRITE** | 2×2 matrix track × output (4 combinations) |
| ADR-0006 Champion bootstrap | Compatible | None |
| ADR-0007 Method Charter | Compatible | None (covered v ADR-0020) |
| ADR-0011 Method Decider + Sunset | Compatible | Add emergency trigger: > 50 % Track S/BU |
| ADR-0012 Method Steward scope | Compatible | Add quarterly Track S audit |
| ADR-0013 Compliance Score | **UPGRADE 12 → 13** | Add element #13 (track + justification) |
| ADR-0014 PflanzerIndex | **UPGRADE** | Per-track aggregation (T+14 vs T+90) |
| ADR-0015 positioning vs AI-DLC | Compatible | Track S complementarity message added |
| ADR-0020 Dual-track model | **NEW** | Full spec |

---

## Throw-away / evolve = orthogonal to P/S

ADR-0005 byla *„default = throw-away"* — to byl protiklad user claim *„hotový
produkt"*. v0.4 udržuje throw-away jako koncept, ale **ortogonálně** k P/S:

| Combination | % use | Description |
|-------------|-------|-------------|
| **Track P + evolve** | 75 % | Default lean. Produkt jde do prod. |
| **Track P + throw-away** | 5 % | Discovery pilot, prod nezáměrný. Žádné re-impl. |
| **Track S + spec-as-deliverable** | 18 % | Track S default. Spec implementována. |
| **Track S + throw-away** | 2 % | DD artifact, acquisition. Spec není implementována. |

Žádné nested („throw-away requires evolve"). Sponsor explicit volba per Charter.

---

## Empirical data supporting Track P preference (per Expert 2)

- **DORA 2024:** Platform team handoff = 8 % throughput penalty. Developer
  independence = +5 % productivity.
- **Bain/Clarity 2026:** 70 % enterprise projects fail kvůli stakeholder
  alignment gap; 88 % transformations miss original ambitions.
- **Questworks:** 30-40 % dev time lost na poor handoff; 68 % rework cost
  from communication gap.
- **Spec Kit (Scott Logic 11/2025):** 2 577 ř. MD pro 689 ř. kódu (3.74:1),
  10× pomalejší než iterative prompting.
- **James Martin:** 50 % req defects = ambiguous/inaccurate.
- **Yan et al. 2025:** 9.8-42.1 % spec-impl mismatch rate (SDD).

Industry data **podporuje Pflanzer pozici Track P jako preferred** — handoff
penalty je quantitatively měřitelná, mezi-functional handoff drift kompoundní.

---

## Precision spec anatomy (per Expert 3)

Track S spec **MUSÍ být dramatically lepší než SDD** by-design. 5 sekcí:

- **A. Functional** — INVEST-RA user stories (Pflanzer-unique extension:
  Referenced + Attributed), Mermaid diagrams, executable Gherkin BDD,
  edge cases, out-of-scope
- **B. Technical** — OpenAPI 3.1 + Spectral/Schemathesis/Pact CI, ERD +
  JSON schemas + sample payloads, tech stack MUST/MAY/MUST NOT, NFRs
- **C. Quality** — STRIDE one-pager, WCAG 2.2 AA checklist, AI Act/DPIA/DORA,
  test scenarios (BDD + unit prerequisites + E2E)
- **D. Implementation** — file structure, naming conventions, pinned libs,
  anti-patterns, PR checklist
- **E. Sign-off** — 12-role matrix s veto rights, parallel approval, quality
  gate ≥ 80/100 pro spec samotnou

**Combined SoT pattern:** Spec + Reference Prototype (z Session 1) + Decision
Log + Executable Tests = 4 anchory proti drift (Yan et al. 2025 compound
drift mitigation).

**Anti-drift mechanismy (7):**
1. SemVer + MADR ADR cross-link
2. Amendment protocol s sponsor approval
3. Reference prototype as combined SoT
4. Executable Gherkin (BDD, ne prose)
5. CI sync monitoring (linter flags drift)
6. 30-day spec expiry (forces refresh)
7. T+30 embedded spec author shadowing

**5-stage handoff ritual:**
1. 90-min walkthrough (PM + dev lead + spec authors)
2. 5-day Q&A window
3. Amendment protocol (dev requests, sponsor approves)
4. First milestone review (dev demos, spec authors verify)
5. T+30 embedded reviewer (drift detection early)

**Honest re-impl gap:**
- Track P: ~0 % (kód JE deliverable)
- Track S Pflanzer: 5-15 %
- SDD Spec Kit / Kiro: 9.8-42.1 %

Track S je dramatically lepší než SDD, ale ne tak dobré jako Track P.

---

## P0 implementation plan

### Batch 1 — Core ADRs + Glossary (must-have pro consistency)

1. ✅ **ADR-0005 rewrite** — full new text (per Expert 1 § 5)
2. ✅ **ADR-0020 new** — dual-track model (per Expert 1 § 6)
3. ✅ **Glossary update** — Track P, Track S definice + handoff ritual term
4. ✅ **`tool/templates/precision-spec-track-s.md.template`** — z Expert 3 output (735 ř., 22 KB)

### Batch 2 — Methodology rewrite (critical files)

5. ✅ **07-handoff-do-vyvoje.md** — dual-track sections (Track P sign-off only,
   Track S full handoff ritual)
6. ✅ **00-tldr.md** — Track P/S framing v intro
7. ✅ **01-filozofie-a-kdy-pouzit.md** — decision tree update
8. ✅ **03-pre-session-priprava.md** — 5. pre-flight track (Trigger Validation)
9. ✅ **method-charter.md** — per-track XYZ + PflanzerIndex

### Batch 3 — Web (visibility)

10. **Sekce 02b** — track context: *„Pflanzer Track P = produkt; SDD = forced
    do Track S-like loop"*. Glossary inline mini.
11. **Comparison matrix** — split Pflanzer řádek na P + S (Track P preferred row + Track S fallback row)
12. **Pricing tiers** — explicit Track S +30-50 % differential annotation
13. **Persona routing** — Persona A (regulated) likely Track S; Persona B (digital-native) Track P

### Batch 4 — 1-pager + comparison matrix in docs

14. **1-pager** — track designation field
15. **09-srovnani-existujici-metody.md** — Pflanzer Track P vs Track S rows

---

## Open questions for Tom (per Expert 1, condensed to 5)

1. **Pricing differential Track S vs Track P** — accept +30-50 % premium?
2. **Marketing strategy** — Track S FAQ-only (never hero)? OK?
3. **Compliance Score upgrade 12→13** — accept? (ADR-0013 patch needed)
4. **PflanzerIndex per-track aggregation** — accept? (ADR-0014 patch needed)
5. **„Default Sunset" trigger** — > 50 % Track S/BU triggers Decider emergency review (ADR-0011 addendum)? Accept threshold or different?

---

## Reference

- `01-methodology-architecture.md` — full Track P/S spec
- `02-industry-comparative.md` — adoption gravity precedents + industry data
- `03-precision-spec-engineering.md` — spec anatomy + handoff ritual
- ADR-0005 (pending rewrite, Expert 1 § 5)
- ADR-0020 (pending new, Expert 1 § 6)
- User clarification 2026-05-28
