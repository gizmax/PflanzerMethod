# Glossary — Pflanzer terminologie

> Definice termínů, kde panovala nejednoznačnost. v0.3.1, 2026-05-28.
> Created after output consistency audit
> (`docs/research/output-consistency/`).

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

### Session 3 (optional)

Nice-to-have polish + observability + monitoring setup. **Není mandatory
production prerequisite** — quality gates již proběhly v Session 2.

## Anti-patterns (deprecated language)

| ❌ Deprecated | ✅ Use instead | Why |
|--------------|---------------|-----|
| „prototype" | „produkt" / „varianta" | Underselling — Pflanzer output IS production code |
| „mockup" | „varianta" / „produkt" | Same as above |
| „klikatelný prototyp" | „běžící produkt na URL" | Stronger claim |
| „handoff package" | „sign-off package" | „Handoff" implies dev re-implementation; Pflanzer dev was in room |
| „dev team picks up the prototype" | „dev team byl v room, kód jde do prod" | Contradicts core claim |
| „Prototype-to-Prod (P2P) checklist" | „Production readiness checklist" | Naming |
| „extract code" (Session 3) | „polish + observability" | „Extract" implies code wasn't prod-ready |
| „re-implementation" | (don't mention; not part of cycle) | Antithesis Pflanzer |

## Reference

- ADR-0005 throw-away vs evolve prototype (note: pending v0.3.1 invert per audit)
- `docs/research/output-consistency/03-synthesis.md` — audit findings + recommendations
- User clarification 2026-05-28: *„Výstup z Pflanzer metody je hotový produkt."*
