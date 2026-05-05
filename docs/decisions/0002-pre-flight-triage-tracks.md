# ADR-0002 — Pre-flight triage tracks (Discovery + Security/Legal/Platform)

**Status:** Accepted
**Date:** 2026-05-05
**Context source:** perspektivy 02 (PM), 07 (Security), 10 (Legal), 14 (User research), 15 (DevOps), synthesis 02 (key themes)

## Kontext

Pflanzerova metoda v0 začíná Session 1 přímo, předpokládá „hlavní přípravy".
Panel ale jednomyslně tlačí na **explicitní pre-flight gate**:

- Bez ověřené persony / JTBD / OST je Session 1 řešením k neexistujícímu
  problému (perspektivy 02, 14).
- Bez data classification + AI Act tier + sandbox spec hrozí session vetovaná
  zpětně Security/Legal po vyhotovení prototypu (perspektivy 07, 10).
- Bez sandbox provisioningu vznikne shadow IT (perspektiva 15).

V0 implicitně předpokládá, že tým „si to nějak připraví". To v korporátu
nestačí — bez **tvrdého gate** se metoda spouští do mlhy.

## Varianty

1. **Žádný formální gate** (v0 stav). Riziko: session 1 se rozpadne
   v prvních 2 hodinách na governance debaty.
2. **Sériový gate** (jeden po druhém). Riziko: 2–3 týdny zdržení.
3. **Discovery gate + 3 paralelní async triage tracks** (48–72 h pre-read).
4. **Single „blanket triage" jeden person** (Champion-driven). Riziko: žádná
   reálná authority, jen formální razítko.

## Rozhodnutí

**Variant 3.** Pflanzer zavádí dva kroky před Session 1:

### Krok 0 — Discovery Readiness Gate

**Vlastník:** PM (#2) + User research (#14).
**Kritéria (všechna povinná):**
- Persona freshness ≤ 6 mo (B2C) / 9 mo (B2B) / 12 mo (internal).
- JTBD card podepsaná PM.
- OST v0 ≥ 60 % vyplněná.

**Pokud chybí:** předřadit **2-week Continuous Discovery sprint** (Torres
rhythm — 3 user interviews / týden), Session 1 odložena.

### Krok 0a — Triage tracks (paralelně, async, 48–72 h pre-read)

**Track A — Security & Data Triage**
- Vlastník: #7 Security.
- Artefakty: Data Classification L1–L4, STRIDE one-pager, Approved AI Tool
  list, Sandbox spec (Terraform 24h TTL), DORA 3rd-party checklist.
- Gate: pokud L4 (top-secret / regulated PII) → **session se nekoná**.

**Track B — Legal & Privacy Triage**
- Vlastník: #10 Legal/DPO.
- Artefakty: AI Act risk-tier klasifikace, DPIA trigger checklist, DPA + SCC
  per AI vendor, marketing compliance brief.
- Gate: AI Act *Unacceptable* → **session se nekoná**. DPIA trigger ≥ 2 →
  **session odložena** do dokončení DPIA.

**Track C — Platform Triage**
- Vlastník: #15 DevOps.
- Artefakty: Sandbox URL provisioned, footprint estimate template, runtime
  approval, observability contract (OTel).
- Gate: bez sandbox URL nemůže Session 1 startovat.

**Sjednocení:** všechny 3 tracky musí mít **podepsané OK** (lidskou atribucí)
před Session 1.

## Důsledky

**Pozitivní:**
- 80 % governance friction vyřešeno **ex-ante** namísto reaktivního veta
  (perspektiva 07).
- Session 1 startuje s pre-approved infrastrukturou — žádný shadow IT.
- Soulad s DORA, NIS2, GDPR čl. 35 a AI Act.

**Negativní:**
- 48–72 h prodleva před Session 1.
- Zvýšený nárok na Security/Legal/Platform kapacitu (mitigováno tím, že
  triage je async, ne meeting).

**Mitigace:**
- Triage probíhá **async** — pre-read 48 h, on-call slot 30–45 min uprostřed
  Session 1 pro re-validation, post-session sign-off (z baseline 03).
- Pre-approved sandbox jako **produkt CISO Office** (ne ad-hoc) — Terraform
  modul `pflanzer-sandbox` (perspektiva 07, 15).
- Pre-approved AI Tool list (Anthropic Enterprise, Cursor Business, v0 Team,
  Bolt Pro) — žádné free tiery, žádné ad-hoc DPA review per session.

## Reference

- DORA čl. 8, 12, 28 — third-party risk.
- NIS2 čl. 21 — supply chain.
- GDPR čl. 35 — DPIA.
- AI Act čl. 6, 14, 50 — risk tiers + lidský dohled.
- Torres, T. *Continuous Discovery Habits* (2021).
