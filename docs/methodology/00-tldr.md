# Pflanzerova metoda — TL;DR pro management

> 1-pager pro VP+. Kdo nemá 3 minuty, nepotřebuje rozhodovat.
>
> **Hledáš jak metodu používat, ne prodávat?** → `00-lean-pflanzer.md`
> (default profil, ~6 lidí, 2 sezení, prod kód). Tento dokument je pro
> management decision, ne pro praktika.

## Co Pflanzer řeší

Korporátní handoff hell. Zadavatel dostane nápad, pošle ho produktu, pinká se to,
vznikne zadání, pinká se to s programátory, security to vetuje na konci, a za
chvíli je rok pryč bez funkčního výstupu. Pflanzerova metoda nahrazuje sériový
pinkání paralelním vibe-codingem — všechny rozhodovací role (zadavatel, PM,
programátoři od minuty 0, security, legal, UX, …) jsou v jedné místnosti
a AI slouží jako páka, která z verbálního inputu týmu generuje **běžící
produkční-ready varianty** v reálném čase. **Výstup cyklu je hotový produkt,
ne handoff package k re-implementaci** — programátor byl v room právě proto,
aby kód šel rovnou do prod
[synthesis 02 — takeaway 3].

## Jak to funguje

1. **Krok 0 — Pre-flight gating** (48 h před S1, async): Discovery Readiness
   Gate (persona ≤6 měsíců, JTBD, OST), Security & Data triage (L1–L4
   classification, AI Act tier, DPIA), Platform Triage (sandbox spec, runtime),
   Capacity pre-sign-off od EM. Bez podpisů S1 nestartuje [synthesis 01 — B].
2. **Session 1** (3–6 h podle stupně, viz `00-lean-pflanzer.md` § Tři stupně): všichni v místnosti **včetně programátora
   od minuty 0**, AI generuje 1–3 **běžící produkční-ready varianty**, BE shadow
   agent paralelně generuje OpenAPI 3.1, A11y quickscan, token compliance check,
   ticket prediction. Výstup = anotované varianty + risk register + score
   závaznosti per role [synthesis 02 — sekce 3].
3. **Mezi-session** (3–7 pracovních dní podle stupně, per ADR-0021): běžící produkt na sandbox URL (24 h TTL,
   watermark). Sbírá se strukturované hodnocení per oddělení (1–5 Likert +
   rationale; AI-only feedback deflated max 0.5).
4. **Session 2** (3 h, rozhodovací): AI moderuje výklad připomínek per role,
   zadavatel hlasuje **poslední** (anti-HiPPO), Decider má tie-breaker.
   Výstup = winner varianta jde **přímo do produkce**, ne re-implementace.
5. **Reinforcement track** (T+7 / T+30 / T+60 / T+90): ticket check
   vs prediction, leading metric readout, retro, lagging metric vs success
   criterion [synthesis 02 — sekce 1, bod 11].

## Co dostaneš (deliverables)

- **Běžící produkt v target prod repo** — winner varianta z Session 2,
  PR-ready commit, quality gates ≥ 80/100. Žádná re-implementace dev týmem
  (programátor byl v room).
- **Business Charter** (ROI hypotéza, success metric, XYZ falsifikace,
  decider mandate, evolve/throw-away flag).
- **Sign-off package** (audit trail, **ne** re-impl spec): preference matrix,
  score závaznosti per role, veto registr, decision log s lidskou atribucí
  (DORA, AI Act čl. 14, GDPR čl. 22).
- **OpenAPI 3.1 final** + 3–5 ADR + Gherkin acceptance kritéria.
- **Compliance pakety** (audit-grade jen): DPIA artefakt, AI Act Annex IV
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

Pflanzer **není zkratka kolem governance**. Sandbox je produkt-grade prostředí,
ne výmluva [synthesis 02 — takeaway 1]: pre-approved Terraform modul s vlastní
VPC, network default-deny, syntetický data seeder, audit logging, cost cap.

V default profilu (~80 % use casů) jde winner varianta z Session 2 **přímo
do prod** s podpisy FE+EM (token compliance, A11y), Security (threat model,
SBOM, secret scan), DPO (DPIA, AI Act tier), DevOps (footprint, SLO, runbook),
QA (acceptance criteria pass).

**Throw-away** je explicit opt-in flag pro 3 výjimky: (1) discovery-only piloty
(žádný produkční záměr), (2) audit-grade evidence collection separate od prod,
(3) regulatorní gate kde production = certified production (FDA, IEC 62304,
DO-178C) a vyžaduje separátní implementační cestu. Bez kompletního paketu
produkt neopustí sandbox — to platí pro evolve i throw-away. Tím se odzbrojí
politický tlak „management override" a metoda splňuje DORA / AI Act / GDPR
požadavky na atribuci rozhodnutí.
