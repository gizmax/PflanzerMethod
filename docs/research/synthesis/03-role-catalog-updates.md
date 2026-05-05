# 03 — Role catalog updates

> Diff-style úpravy `02-role-catalog.md` (v0.1 → v0.2) na základě 15
> perspektiv.

## Změny

### Povýšení / degradace statusu

| Role | v0.1 | v0.2 | Trigger / důvod |
|------|------|------|------------------|
| #8 QA | DOPORUČENÁ pro release-grade | **POVINNÁ pro release intent** | Jakákoli zmínka „produkce"/„pilot"; testovatelnost se rozhoduje v S1 (8) |
| #10 Legal | VOLITELNÁ | **DOPORUČENÁ** | Vibe-coding tool = GDPR čl. 28 processor; AI Act trigger téměř vždy (10) |
| #11 A11y | VOLITELNÁ | **DOPORUČENÁ default-on** | Public-facing + B2B nad 250 zam.; obrácený gradient (jen úzká výjimka). EAA 28. 6. 2025 (11) |
| #12 Data | VOLITELNÁ | **DOPORUČENÁ** | Release intent = measurement plan + instrumentation deadline (12) |
| #13 CS | VOLITELNÁ | **DOPORUČENÁ** | Customer base >1000 active + user-facing change (13) |
| #14 End-user | VOLITELNÁ | **DOPORUČENÁ default-on** | Customer-facing flow / nový segment; volitelná jen při fresh persona ≤3 mo (14) |
| #15 DevOps | VOLITELNÁ | **DOPORUČENÁ** | Session má sandbox (téměř vždy); bez paved-road = shadow-IT (15) |

### Degradace AI proxy

| Role | v0.1 | v0.2 | Hranice |
|------|------|------|---------|
| #10 Legal | ✅ | **⚠️** | OK pro L1/L2, min/limited risk, internal, syntetická data. **Lidský DPO** pro high-risk AI Act, special categories, profiling, ADM, marketing claims, novel vendor, cross-border non-adequacy (10) |
| #11 A11y | ✅ | **⚠️** | OK pro static mockup audit, axe, contrast, semantic lint. **Pre-launch human review povinný** — screen reader UX, cognitive load, dynamic focus, switch/voice. EAA nelze atestovat AI (11) |
| #14 End-user | ✅ | **⚠️ score deflation 0.5** | Vstup do session, ne výstup. Zvládne archetype check, JTBD reality check, hypothesis generation. Nezvládne novel insight, edge case, cultural specifics, say-do gap, emotional arc (14) |
| #8 QA | ✅ | **⚠️** | Test generation OK, ale lidský review každého scénáře povinný před CI (LLM testuje implementaci, ne chování) (8) |

### Nové role

- **#16 UX writer / Content designer.** Trigger: user-facing copy, error/
  empty states, marketing claims. Volitelná pro pure internal tooling.
  Vstup: brand guidelines, voice & tone, B1/B2 plain language, ePrivacy/
  UCPD pravidla. Výstup: microcopy, error message strategy, marketing
  claim review. AI proxy ⚠️ (compliance sub-agent draft + lidský review).
  *(Perspektiva 6.)*
- **#17 Champion / Pilot lead.** Trigger: druhý+ pilot v BU, scaling.
  Coaching Kata loop, internal CoP. Vstup: retros, target/obstacle/next,
  security buddy. Výstup: retrospective, contribution do role catalogu.
  AI proxy ❌ (social capital v BU). *(Implicitně 7, 9; baseline 03.)*
- **#18 Solution / Domain architect** *(volitelně)*. Trigger: multi-team
  (3+), komplexní doména (Event Storming), regulovaný SDLC. Vstup:
  bounded contexts, ADR archiv, domain model, integration map. Výstup:
  domain delta, breaking-change registr, dependency map, ADR drafts.
  AI proxy ⚠️ jen typické vzory. *(Otevřená v0; perspektiva 9.)*

### Decision tree změny

- **Krok 0 — Discovery Readiness Gate.** Persona ≤6 mo + JTBD podepsaný
  PM + OST v0. Pokud chybí → 2-week Discovery Sprint, session odložena.
  *(2, 6, 14.)*
- **Krok 0a — Security & Data + Legal & Privacy + Platform Triage**
  (paralelně async, 48 h). Data Classification L1–L4 (DPO), AI Act
  risk-tier, DPIA + RoPA, Approved AI Tool list + DPA/SCC, Sandbox spec +
  runtime approval, STRIDE one-pager, Capacity pre-sign-off (EM). Bez
  podpisů S1 neodstartuje. *(1, 7, 10, 15.)*
- **Krok 4 (Security trigger) — doplnit:** „Prompty s reálnými /
  pseudonymizovanými daty do externích AI toolů?" → +Security + Legal
  POVINNĚ; L4 = session se nekoná. *(7, 10.)*
- **Krok 5 (QA trigger) — změnit:** „Jakékoli prohlášení o produkci nebo
  pilotu" → +QA POVINNĚ. *(8.)*
- **Krok 8 (A11y trigger) — default-on** pro customer-facing + B2B nad
  250 zaměstnanců. *(11.)*
- **Krok 12a — Multi-team scope (>3 týmy)** → federovaný model nebo
  +Solution architect (#18). *(9.)*
- **Krok 13 — IP iteration mounting (SAFe).** Default do IP iterace;
  mid-PI jen pokud sponzor uvolní commit features ekvivalentní 8–10
  person-days; pre-PI nejcennější. Mimo SAFe = Atlassian Play / GV Sprint
  varianta. *(1, 9.)*
- **Sanity check rozšíření.** MoSCoW na vstupy (Default = MUST only /
  regulated = MUST + SHOULD / audit-grade = vše). Kapacitní footprint
  ~8–10 person-days/cyklus; EM má **veto na workshop** pokud PI >80 %
  committed. *(3, 9.)*

### Per-role text patche

Tabulka doplňků (vstup / výstup); detail v perspektivách.

| # | Role | Doplnit vstup | Doplnit výstup |
|---|------|---------------|----------------|
| 1 | Zadavatel | One-pager business case (ARR impact), XYZ hypotéza, decider mandate od CPO písemně, capacity pre-check | Go/iterate/kill s commitment index threshold; reinforcement track 30/60/90 |
| 2 | PM | JTBD formát, OST 60 % vyplněná, success + leading metric, OKR alignment, XYZ | Preference matrix per role; PRD-lite; updated OST |
| 3 | Facilitátor | Block **Energy curve** (S1 5–6 h, end 16:00; mezi-session 5–7 d; S2 3 h rozhodovací) | Tří-režimová AI-human matice (viz níže) |
| 4 | FE lead | Design tokens, component manifest + Storybook, tech stack contract, ESLint/Prettier, a11y baseline, anti-pattern list | Komponentový mapping; token compliance >90 %; throw-away/evolve decision; repo + commit history |
| 5 | BE lead | Backend Context Pack (OpenAPI URL, ERD, NFR baseline, ADR archiv 12 mo, event taxonomy, RFC 7807 conventions) | Draft OpenAPI 3.1 per varianta (BE shadow agent); breaking-change registr; 3–5 ADR; contract test skeleton (Pact/Schemathesis); migration plan stub |
| 6 | UX | Persona doc + JTBD + a11y needs, journey map, design tokens, component inventory, JTBD card, brand voice | Anotované mockupy mapované na JTBD + OST; flow diagram; DS deviation list s ownerem; dual-track Figma↔kód mapping |
| 7 | Security | Data Classification L1–L4, STRIDE one-pager, Approved AI Tool list, Sandbox spec, SSO+MFA, DORA 3rd-party, legal pre-read 48 h | Audit log SSO atribucí (DORA 7 let); SBOM `cyclonedx`/`syft` + license + CVE scan; secret scan gitleaks/trufflehog; veto registr; sandbox-to-prod gate |
| 8 | QA | Test strategy, regression inventory, contract test framework (Pact) | BDD/Gherkin (≥1 negative per varianta); test pyramide split s vlastníky; contract test skeleton; exploratory charter; P2P checklist |
| 9 | EM | Kapacita + roadmap, dependencies (platform/identity/data), PI commit %, IP iteration availability, T-shirt rubric | Dependency Map (feature → team → typ → required by → owner); T-shirt + 2-day capped spike; capacity buffer 25 %; eskalační protokol |
| 10 | Legal | RoPA, DPIA checklist (čl. 35/3 + EDPB), AI Act risk-tier, DPA + SCC per vendor, marketing compliance brief, IP klauzule | DPIA artefakt podepsaný DPO; AI Act tech doc Annex IV (high-risk); Privacy Notice draft z template; Legal basis per feature; vendor risk register; decision log s lidskou atribucí |
| 11 | A11y | WCAG 2.2 AA filtr na komponenty, persona disability set (low vision + motor + cognitive), tools (axe/Pa11y/Lighthouse/CCA) | A11y quickscan 8–10 položek; axe-core run; Critical/Serious = blocker pro „final" |
| 12 | Data | Event taxonomy + naming, baseline metriky, XYZ measurable, power analysis, privacy classification, KPI strom | Measurement plan v1 (primary lagging + 2–3 leading + guardrail); event schema `object_action`; A/B test design + kill criteria; instrumentation deadline ship-2d; learning agenda T+30/60/90 |
| 13 | CS proxy | Top-10 ticket kategorií 90d, 20 verbatim, frikční místa, churn radar, capacity baseline, KB článek | Ticket prediction worksheet (volume/TTR/deflectable/VoC match); readiness D-7 KB → D-2 makra/training; post-launch T+7/T+30/T+90 |
| 14 | End-user | Persona freshness ≤6 mo (5+ rozhovorů), JTBD card, OST v0, NDA alternativy (shadowing/tickets/sales calls) | Discovery Debt Detector skóre 0–10; persona expiry compliance; JTBD/OST node tag per varianta; AI-only score deflation max 0.5 |
| 15 | DevOps | Sandbox spec Terraform modul, Approved runtime list, footprint estimate template, observability contract (OTel + structured logs + tracing), secret policy (Vault + OIDC) | Deploy footprint TCO sheet per varianta; Sandbox URL + IaC commit; 4 golden signals dashboard; SLO baseline (availability/p95/error budget); runbook stub; P2P gate checklist |

### „AI proxy vs lidský zástupce" — 3 režimy

1. **Vlastnické a vetovací (vždy člověk):** #1, #2 final, #7 final,
   #10 final, #9 kapacita, #11 pre-launch, #14 novel insight, #17.
2. **Konzultativní (AI proxy + human sign-off 24–48 h):** #6, #12, #8
   test gen, #13, #14 archetype check, #16 marketing draft.
3. **Execution-heavy / context-light (AI vede):** mockup generation,
   transcript summary, clustering, score aggregation, OpenAPI shadow,
   SBOM/CVE scan, axe-core, STRIDE draft, Discovery Debt Detector,
   BE shadow agent, footprint kalkulačka, marketing compliance draft.

**Score deflation** AI-only max 0.5/1.0 (#14). **Decision log atribuuje
člověka** (DORA, AI Act čl. 14, GDPR čl. 22).

### Otevřené otázky — uzavírané

- ✅ Chybí role → #16 UX writer, #17 Champion, volitelně #18 Solution
  architect.
- ✅ 15 rolí akorát s MoSCoW gradací; default 4–7 v místnosti.
- ✅ AI strategist není zvlášť, je to facilitator s AI-human dělbou (3).
- ✅ Konflikt security vs zadavatel: hierarchie závaznosti (Critical /
  Yellow / Score) + pre-charter triage 80 % ex-ante.
- ⚠️ Archetypy (B2B SaaS / internal / mobile) — otevřené, drafting fáze.
