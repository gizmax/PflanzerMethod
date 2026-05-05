# Pflanzerova metoda — TL;DR pro management

> 1-pager pro VP+. Kdo nemá 3 minuty, nepotřebuje rozhodovat.

## Co Pflanzer řeší

Korporátní handoff hell. Zadavatel dostane nápad, pošle ho produktu, pinká se to,
vznikne zadání, pinká se to s programátory, security to vetuje na konci, a za
chvíli je rok pryč bez funkčního výstupu. Pflanzerova metoda nahrazuje sériový
pinkání paralelním vajbeňím — všechny rozhodovací role (zadavatel, PM,
programátoři, security, legal, UX, …) jsou v jedné místnosti od minuty 0 a AI
slouží jako vibe-coding páka, která z verbálního inputu týmu generuje funkční
mockupy v reálném čase. Cílem není rychlejší výroba mockupů; cílem je
**cross-functional alignment na funkčním artefaktu, ne na PowerPointu**
[synthesis 02 — takeaway 3].

## Jak to funguje

1. **Krok 0 — Pre-flight gating** (48 h před S1, async): Discovery Readiness
   Gate (persona ≤6 měsíců, JTBD, OST), Security & Data triage (L1–L4
   classification, AI Act tier, DPIA), Platform Triage (sandbox spec, runtime),
   Capacity pre-sign-off od EM. Bez podpisů S1 nestartuje [synthesis 01 — B].
2. **Session 1** (5–6 h, end v 16:00): všichni v místnosti, AI generuje 1–3
   mockupy, BE shadow agent paralelně generuje OpenAPI 3.1, A11y quickscan,
   token compliance check, ticket prediction. Výstup = anotované varianty +
   risk register + score závaznosti per role [synthesis 02 — sekce 3].
3. **Mezi-session** (5–7 dní): klikací prototyp v sandbox VPC s 24 h TTL a
   watermark. Sbírá se strukturované hodnocení per oddělení (1–5 Likert +
   rationale; AI-only feedback deflated max 0.5).
4. **Session 2** (3 h, rozhodovací): AI moderuje výklad připomínek per role,
   zadavatel hlasuje **poslední** (anti-HiPPO), Decider má tie-breaker.
   Výstup = go / iterate / kill s explicit kritériem.
5. **Handoff + reinforcement track** (T+7 / T+30 / T+60 / T+90): ticket check
   vs prediction, leading metric readout, retro, lagging metric vs success
   criterion [synthesis 02 — sekce 1, bod 11].

## Co dostaneš (artefakty)

- **Business Charter** (ROI hypotéza, success metric, XYZ falsifikace,
  decider mandate, throw-away/evolve flag).
- **1–3 anotované klikací prototypy** v izolovaném sandboxu s OST/JTBD tagem.
- **Draft OpenAPI 3.1 per varianta** + breaking-change registr + 3–5 ADR.
- **Decision package**: preference matrix, score závaznosti per role, veto
  registr, decision log s lidskou atribucí (DORA, AI Act čl. 14, GDPR čl. 22).
- **Handoff package**: scoped epic, akceptační kritéria (Gherkin, ≥1 negative
  scenario per varianta), dependency map, P2P (Prototype-to-Prod) checklist.
- **Compliance pakety** (jen pokud relevantní): DPIA artefakt, AI Act Annex IV
  tech doc skeleton, Privacy Notice draft, SBOM, secret scan, A11y axe-core
  report, SLO baseline + runbook stub.

## Kdy ano

- Cross-functional **alignment problem** (3+ oddělení blokují rozhodnutí)
  s funkčním prototypem jako requirement.
- Nový view / nová feature s **fresh discovery** (persona ≤6 mo, JTBD lock).
- Scope vejde do **IP iterace SAFe** (~8–10 person-days/cyklus) nebo do okna
  Atlassian Play / GV Sprint slotu.

## Kdy ne

- **Legacy migrace s fixním scope** — alignment už je, problém je execution.
- **Regulovaný projekt s vyčerpaným risk budget** — DPIA / AI Act high-risk
  bez podpisů; metoda neslouží jako zkratka kolem governance.
- **Single-team scope < 1 sprint quick win** — overhead > přínos; udělej LDJ.

## Kapacita a cena

Z perspektivy Engineering Managera ~**8–10 person-days per cyklus** (pre-flight
+ S1 + mezi-session + S2 + handoff). Default kadence: **max 2–3 cykly per PI**,
defaultně mounted do **IP iterace** SAFe; mid-PI jen pokud sponzor uvolní
commit features ekvivalentní 8–10 person-days. EM má **veto na workshop**,
pokud PI je >80 % committed [synthesis 03 — decision tree krok 13].

## Risk & guardrails

Pflanzer **není zkratka kolem governance**. Sandbox je produkt, ne výmluva
[synthesis 02 — takeaway 1]: pre-approved Terraform modul s vlastní VPC,
network default-deny, syntetický data seeder, 24 h TTL, audit logging, cost
cap. Throw-away je **default v charteru**; „evolve" status vyžaduje současně
podpisy FE+EM (token compliance, A11y), Security (threat model, SBOM, secret
scan), DPO (DPIA, AI Act tier), DevOps (footprint, SLO, runbook), QA (P2P
checklist) [synthesis 01 — A]. Bez kompletního paketu prototyp neopustí
sandbox. Tím se odzbrojí politický tlak „management override" a metoda
splňuje DORA / AI Act / GDPR požadavky na atribuci rozhodnutí.
