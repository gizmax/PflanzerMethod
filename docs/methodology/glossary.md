# Glossary — Pflanzer terminologie

> Definice termínů, kde panovala nejednoznačnost. **v0.4, 2026-05-28.**
> Updated po dual-track design (`docs/research/dual-track-design/`)
> a output consistency audit (`docs/research/output-consistency/`).

## Track terms (v0.4)

### Track P (Preferred)

**Default Pflanzer track (~80 % cases).** Dev #4 (FE/vibe-coding lead) +
#5 (BE/API lead) jsou v room od minuty 0 celý Session 1. Output cyklu =
**běžící produkt na URL**, deployment D11-14. Žádný handoff k re-implementaci
— dev tým byl v room.

Charter potvrzuje track = P (default, zero-friction). Definováno v ADR-0020.

### Track S (Fallback)

**Fallback Pflanzer track (~20 % cases).** Dev tým NENÍ v room — z 1 ze
4 hard triggers:

1. Distributed dev tým ≥ 3 časové pásma
2. AI Act High-risk + certified production
3. FDA / IEC 62304 / DO-178C / PSD2 SCA
4. Sponsor mandate spec-as-deliverable (multi-vendor, legacy modernization, acquisition DD)

Output cyklu = **precision spec ≥ 80/100 quality gate** + 5-stage handoff
ritual. Track S NESMÍ být easy escape hatch — bez triggeru = projekt odložit,
ne přepnout. Definováno v ADR-0020.

**Track S re-impl gap target ≤ 15 %** (vs SDD 9.8-42.1 %, vs Track P ~0 %).

### dev-in-room

Konkrétně **#4 FE / Vibe-coding lead + #5 BE / API lead** (z role catalogu)
fyzicky / virtuálně v session od minuty 0 celý Session 1. Builder lead =
dev v driver-seat AI co-pilot session (NE facilitátor s AI proxy).

Dev-in-room je **fit criterion pro Track P** (mandatory). Pokud nelze
zajistit, Track S nebo odložit projekt.

### precision spec

Output Track S Session 2. Markdown dokument ≥ 80/100 quality gate na
12 dimensions:
- Functional (INVEST-RA user stories, Gherkin BDD, edge cases)
- Technical (OpenAPI 3.1, ERD, tech stack constraints)
- Quality (STRIDE, WCAG, AI Act/DPIA/DORA)
- Implementation (file structure, naming, anti-patterns)
- Sign-off (12-role matrix s veto rights)

**Reference prototype z Session 1 = combined SoT s spec** (anti-drift weapon
unique pro Pflanzer vs SDD).

Template: `tool/templates/precision-spec-track-s.md.template`.

### 5-stage handoff ritual (Track S only)

Když dev tým není v room a spec jde k nim:

1. **90-min walkthrough** — PM + dev lead + spec authors
2. **5-day Q&A window** — dev klade otázky, spec authors odpovídají
3. **Amendment protocol** — dev requests changes, sponzor approves
4. **First milestone review** — dev demos first slice, spec authors verify
5. **T+30 embedded reviewer** — spec author shadows dev sprint, detects drift early

Definováno v ADR-0020.

## Core deliverable terms

## Core deliverable terms

### produkt (product)

**Primary output Pflanzer cyklu.** Běžící, klikatelný, deploy-able,
auditovatelný kód v target prod repo. Po Session 2 už existuje na
production-grade URL; dev tým (který byl v room od minuty 0) ho během
D11-14 doladí (observability, monitoring, edge cases).

**Synonyms (allowed):** běžící produkt, running product, production-ready code.

**NOT synonyms (deprecated):** prototyp, mockup, handoff package, klikatelná
ukázka.

### artefakt (artifact)

V Pflanzer kontextu **= produkt** (viz výše). Termín *„artefakt"* se používá
v anti-SDD argumentaci (*„artefakt > spec"*) jako protiklad k dokumentu.
**Pflanzer artefakt JE running production code**, ne Figma mockup, ne PDF
spec, ne PowerPoint slide.

Etymologie: latinské *arte factum* („udělaný řemeslem"). V SW inženýrství
obecný termín pro hmatatelný výstup (kód, build, dokumentace). V Pflanzer
copy = specificky *„běžící produkční artefakt"*.

### sign-off package (formerly „handoff package")

**Audit trail + compliance evidence**, který padá ven po Session 2:
- decision log s human attribution per AI Act čl. 14
- preference matrix + score závaznosti per role + veto registr
- DORA 7y audit log entry
- Acceptance kritéria (Gherkin)
- Compliance pakety (DPIA, AI Act Annex IV, Privacy Notice, SBOM,
  secret scan, A11y axe-core, SLO baseline) — audit-grade jen

**Sign-off package NENÍ re-implementation spec.** Dev tým si podle něj
nestaví produkt — ten je už v target repo. Sign-off package slouží **audit**
+ **post-launch reinforcement** (T+7/30/60/90 retro material).

**Deprecated:** *„handoff package"* — slovo *„handoff"* implies *„throw to
dev team"*, což protiřečí Pflanzer claimu *„dev was in room from minute 0"*.

### AI code provenance

**Atribuce AI-asistovaného kódu** (doplněk k atribuci rozhodnutí v decision
logu). Autor commitu = dev, který seděl u klávesnice, a ručí za kód jako za
vlastní; AI nikdy není autor. AI asistence se značí commit trailery
(`Pflanzer-Variant`, `Pflanzer-Session`, `AI-Assisted`) a PR labely
(`ai-generated`, `pflanzer:<slug>`); review je stejná jako u lidského kódu.
Definováno v `07-handoff-do-vyvoje.md` § AI code provenance.

## Profile terms

### evolve (default)

**Default mode**. Winner varianta z Session 2 jde **přímo do produkce**.
Dev tým (#4 + #5 byli v room) ji doladí pro production hardening
(observability, monitoring, edge cases) během D11-14. Quality gates
≥ 80/100 = production prerequisite, ne *„prototype hardening checklist"*.

### throw-away (explicit opt-in)

Flag v Charteru pro **3 výjimky**:
1. **Discovery-only piloty** — žádný produkční záměr, jen falsifikace XYZ.
2. **Audit-grade evidence collection** separate od prod (compliance artefakt
   k regulatorní show-case).
3. **Regulatorní gate kde production = certified production** (FDA, IEC 62304,
   DO-178C, některé AI Act High-risk uses), kde MUST existovat separate
   implementation track.

**Throw-away NENÍ default** (v0.3.1 change). Sponzor musí podepsat v Charteru
*„throw-away"* explicit a uvést který z 3 use casů aplikuje.

## Session terms

### Session 1 output

**3 paralelní produkční-ready varianty** na sandbox URL (default profile).
NE *„mockupy"*, NE *„klikací prototypy"* — vibe-coding tools (Bolt, v0, Lovable,
Claude Code) v 2026 produkují **production-grade kód** s ESLint pass + types +
Vitest defaults. Sandbox je guardrail (24h TTL, watermark, network default-deny),
ne *„prototype playground"*.

### Session 2 output

**Winner varianta selected for prod** + sign-off package.

### Stupeň (Quick / Lean / Full)

Míra rituálů kolem stejného jádra metody (dev v room, 3 paralelní varianty,
anti-HiPPO, Decider). **Quick** = 60–90 min in-room, 1 kolo buildu, triage
deferred, jen `throwaway` / `pilot` (`/pm live`). **Lean** = 3 h, 2 kola
buildu s mid-checkpointem, default pro Track P (`/pm build`). **Full** =
5–6 h, kompletní agenda `04-session-1.md`, 4 triage tracks povinné,
audit-grade / regulated. Session 2 je ve všech stupních 3 h. Autoritativní
tabulka: `00-lean-pflanzer.md` § Tři stupně jedné metody.

### Ship gate

**Pipeline, ne setkání.** Po Go rozhodnutí v Session 2 ji pouští dev pár:
quality gates (score 0–100) + `SHIP.md` → PR připravený k mergi
(`/pm ship` + `/pm handoff`). Pflanzer cyklus = **2 sezení + Ship gate**.

**Alias (deprecated):** *„Session 3"* — starší název v toolu; command
`/pflanzer-session-3` zůstává jako implementace pod kapotou `/pm ship`.
Iterační rozhodovací session po Iterate (ADR-0001 Scenario B/C) se jmenuje
**Session 2b** (dříve také „Session 3“) — to není Ship gate.

## Anti-patterns (deprecated language)

| ❌ Deprecated | ✅ Use instead | Why |
|--------------|---------------|-----|
| „prototype" | „produkt" / „varianta" | Underselling — Pflanzer output IS production code |
| „mockup" | „varianta" / „produkt" | Same as above |
| „klikatelný prototyp" | „běžící produkt na URL" | Stronger claim |
| „handoff package" | „sign-off package" | „Handoff" implies dev re-implementation; Pflanzer dev was in room |
| „dev team picks up the prototype" | „dev team byl v room, kód jde do prod" | Contradicts core claim |
| „Prototype-to-Prod (P2P) checklist" | „Production readiness checklist" | Naming |
| „extract code" (Ship gate) | „polish + observability" | „Extract" implies code wasn't prod-ready |
| „Session 3" / „3 sezení" | „Ship gate" / „2 sezení + Ship gate" | Ship gate je pipeline, ne setkání |
| „re-implementation" | (don't mention; not part of cycle) | Antithesis Pflanzer |

## Reference

- ADR-0005 throw-away vs evolve prototype (v0.4: default = evolve, throw-away = explicit opt-in pro 3 use cases)
- `docs/research/output-consistency/03-synthesis.md` — audit findings + recommendations
- User clarification 2026-05-28: *„Výstup z Pflanzer metody je hotový produkt."*
