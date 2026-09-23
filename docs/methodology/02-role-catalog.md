# Role catalog — knihovna perspektiv pro Pflanzerovu metodu

> **Status:** v0.2 (po expertním panelu, syntéze a applikaci diff `synthesis/03-role-catalog-updates.md`).
> Změny vůči v0.1 jsou v ADR `decisions/0003-role-catalog-promotions.md`.

## Proč role catalog

Klasické workshop metodiky (Design Sprint, LDJ, …) předpokládají fixní okruh
účastníků. Pflanzerova metoda jde dál: **každý projekt má jiný relevantní mix
rolí**. Role catalog řeší dvě věci:

1. **Pre-flight check** — než svolám session, vím, koho potřebuji v místnosti
   a koho ne. Nezvu zbytečně, ani nezapomínám.
2. **AI panel mapping** — pro každou vybranou roli umí tool spustit
   odpovídajícího sub-agenta, který se k materiálům vyjadřuje *z té perspektivy*.

## Jak číst tabulku

- **Povinná** = bez této role session 1 nemá smysl spouštět.
- **Doporučená** = standardně přidat, pokud nemáš dobrý důvod nepřidat.
- **Doporučená default-on** = standard ZAPNUTO, vypínáš opt-outem s důvodem.
- **Volitelná (trigger)** = přidat, **jen když** platí trigger.
- **AI proxy:** ✅ = AI zvládne samostatně, ⚠️ = AI s lidským sign-off,
  ❌ = nelze AI nahradit, vždy člověk.

---

## Katalog (18 rolí)

### 1. Zadavatel / Business owner — POVINNÁ
- **Vlastní nápad a budget.** Bez něj projekt nestartuje.
- **Vstup:** business case one-pager (ARR/efficiency impact), XYZ hypotéza,
  decider mandate od CPO písemně, capacity pre-check.
- **Výstup ze session:** Go / Iterate / Kill rozhodnutí s commitment index
  threshold, reinforcement track 30 / 60 / 90.
- **AI proxy:** ❌ Nelze. Bez něj sessionu 1 odložit.

### 2. Produkt manažer — POVINNÁ
- **Překlad business → produktové požadavky**, prioritizace, OKR alignment.
- **Vstup:** JTBD formát, OST v0 (≥60 % vyplněná), success metric (leading +
  lagging), persona doc, OKR alignment, XYZ hypotéza.
- **Výstup:** preference matrix per role, PRD-lite, updated OST.
- **AI proxy:** ⚠️ Krátkodobě s předem připraveným briefem, finální slovo PM.

### 3. Facilitátor (lidský + AI) — POVINNÁ
- **Vede session**, hlídá agendu a energy curve, deeskaluje konflikty,
  orchestrouje AI co-pilot.
- **Vstup:** energy curve plán (Session 1 = 3–6 h podle stupně (Quick 60–90 min / Lean 3 h / Full 5–6 h, viz `00-lean-pflanzer.md` § Tři stupně),
  mezi-session = 3–7 dní podle stupně, Session 2 = 3 h rozhodovací), tří-režimová AI-human matice
  (viz níže).
- **Výstup:** facilitační notes, conflict log, decision log s lidskou atribucí.
- **AI proxy:** ❌ Lidský facilitátor nutný — AI samotná konflikt mezi
  rolemi neureší.
- **Co-facilitator / externí Facilitátor — SHOULD pro audit-grade profil
  a high-stakes session** (devil's advocate Útok 10): single-facilitator
  závislý na sponzoringu = paper authority při anti-HiPPO. Audit-grade
  profil (regulated SDLC, AI Act high-risk) **vyžaduje** druhého
  facilitátora — buď z jiné BU (neutrální vůči sponzor řetězci), nebo
  externího coache (viz ADR-0006 bootstrap forma 1).

### 4. Frontend / Vibe-coding lead — POVINNÁ pro Track P · doporučená pro Track S
- **Trigger pro povinnost:** projekt má UI komponent — Track P MUSÍ mít
  FE leada v room od minuty 0; Track S (fallback, viz ADR-0020) může bez
  FE leada, ale spec authors musí přebrat jeho zodpovědnost za tech stack
  rozhodnutí.
- **Vstup:** design tokens manifest, component manifest + Storybook URL,
  tech stack contract (framework, ESLint/Prettier), a11y baseline,
  anti-pattern list, Track + evolve/throw-away directive z Charteru.
- **Výstup (Track P):** **běžící produkční-ready varianty** (3 paralelní)
  s real kódem v target repo, komponentový mapping, token compliance > 90 %,
  PR-ready commit pro winner.
- **Výstup (Track S):** Reference prototype z Session 1 (1-3 lightweight) +
  technical sekce precision specu (per `tool/templates/precision-spec-track-s.md.template`),
  tech stack MUST/MAY/MUST NOT.
- **AI proxy:** ⚠️ Pro greenfield části jde, brownfield vyžaduje human review.

### 5. Backend / API lead — POVINNÁ pro Track P · doporučená pro Track S
- **Trigger:** nové API, změny datového modelu, integrace. Pro Track P MUSÍ
  být v room od minuty 0; pro Track S (fallback) spec authors přebírají
  zodpovědnost za contract-first sekce.
- **Vstup:** **Backend Context Pack** = OpenAPI URL stávajícího API, ERD,
  NFR baseline, ADR archiv 12 mo, event taxonomy, RFC 7807 conventions.
- **Výstup (Track P):** **OpenAPI 3.1 final** + contract test passing
  (Pact / Schemathesis), implementační kód v target repo, 3-5 ADR commits,
  migration plan executed.
- **Výstup (Track S):** Draft OpenAPI 3.1 final v precision spec, ERD +
  JSON schemas + sample payloads, contract test skeleton, migration plan
  for receiving dev team.
- **AI proxy:** ⚠️ Jen pro velmi greenfield části, brownfield vyžaduje
  lidského BE leada.

> **Track P / Track S note:** Per ADR-0020 dual-track model je dev #4 + #5
> v room **mandatory pro Track P** (preferred default ~80 % cases). Track S
> fallback (~20 %) vyžaduje 1 ze 4 hard triggers (distributed dev ≥ 3 TZ,
> AI Act High-risk, FDA/IEC/DO-178C/PSD2 SCA, sponsor mandate spec-as-deliverable).
> Bez triggeru = projekt odložit, ne přepnout. Viz `glossary.md`.

### 6. UX / Designer — DOPORUČENÁ pro nové flow
- **Trigger pro povinnost:** nový user flow, přepracování core experience.
- **Vstup:** persona doc + JTBD + a11y needs, journey map, design tokens,
  component inventory, JTBD card, brand voice & tone.
- **Výstup:** anotované mockupy mapované na JTBD + OST node, flow diagram,
  DS deviation list s ownerem, dual-track Figma↔kód mapping
  (Figma node ID ↔ commit hash).
- **AI proxy:** ✅ Možný pro design system audit, ⚠️ pro flow integrity.

### 7. Security / Compliance — POVINNÁ pro projekty s daty / integracemi / auth
- **Trigger pro povinnost:** auth, osobní data, externí integrace, payment,
  novel AI use case.
- **Vstup:** Data Classification L1–L4, STRIDE one-pager, Approved AI Tool list,
  Sandbox spec (24h TTL Terraform), SSO + MFA pravidla, DORA 3rd-party
  checklist, Legal pre-read 48 h.
- **Výstup:** **veto právo na varianty s critical risk**, audit log s SSO
  atribucí (DORA 7 let), SBOM (`cyclonedx`/`syft`) + license + CVE scan,
  secret scan (gitleaks/trufflehog), veto registr, sandbox-to-prod gate.
- **AI proxy:** ❌ Veto musí podepsat člověk; AI připraví STRIDE draft
  a SBOM/CVE scan.

### 8. QA / Test lead — POVINNÁ pro release intent
- **Trigger pro povinnost:** **jakákoli zmínka „produkce" nebo „pilot"**
  ve výstupu (i pokud je do produkce ≥1 měsíc).
- **Vstup:** test strategy, regression inventory, contract test framework
  (Pact), automation framework, kritické flows.
- **Výstup:** **3–5 BDD/Gherkin scénářů s ≥1 negative path per varianta**,
  test pyramide split s vlastníky, contract test skeleton, exploratory charter
  (90 min template), **P2P (prototype-to-prod) checklist (9 položek)**.
- **AI proxy:** ⚠️ Test generation OK, ale **lidský review každého scénáře
  povinný před CI** (LLM testuje implementaci, ne chování).

### 9. Engineering manager — DOPORUČENÁ pro scope > 2 sprinty
- **Trigger pro povinnost:** odhad práce > 2 sprinty / 1 PI.
- **Vstup:** kapacita + roadmap, dependencies (platform / identity / data),
  PI commit %, IP iteration availability, T-shirt rubric.
- **Výstup:** **Dependency Map** (feature → team → typ → required by → owner),
  **T-shirt v session + 2-day capped spike → story-point**, capacity buffer
  25 % pro Pflanzer-driven features, eskalační protokol.
- **AI proxy:** ❌ Kapacita & roadmap citlivé. **EM má veto na workshop**
  pokud PI > 80 % committed.

### 10. Legal / GDPR — DOPORUČENÁ
- **Trigger pro povinnost:** osobní data, marketing, novel AI use case
  (EU AI Act high-risk), regulovaný produkt (PSD2/MiFID).
- **Vstup:** RoPA, DPIA checklist (GDPR čl. 35/3 + EDPB), AI Act risk-tier
  klasifikace, DPA + SCC per vendor, marketing compliance brief, IP klauzule.
- **Výstup:** DPIA artefakt podepsaný DPO, AI Act tech doc Annex IV pro
  high-risk, Privacy Notice draft, Legal basis per feature, vendor risk
  register, decision log s lidskou atribucí.
- **AI proxy:** ⚠️ OK pro L1/L2 data, minimal/limited risk, internal use,
  syntetická data. **Lidský DPO** pro high-risk AI Act, GDPR čl. 9 special
  categories, profiling, ADM, marketing claims, novel vendor, cross-border
  non-adequacy.

### 11. Accessibility expert — DOPORUČENÁ default-on
- **Trigger pro opt-out:** pure internal admin tool < 250 zaměstnanců, žádný
  WCAG závazek (zdokumentovaný, podepsaný).
- **Vstup:** WCAG 2.2 AA filtr na komponenty, persona disability set
  (low vision + motor + cognitive), tools stack (axe DevTools / Pa11y CI /
  Lighthouse / CCA).
- **Výstup:** **A11y quickscan 8–10 položek** (sémantika, keyboard, focus,
  labels, errors, contrast, headings, alt, target size, cognitive),
  axe-core run, **WCAG Critical/Serious = blocker pro „final" rozhodnutí
  (váha jako Security veto)**.
- **AI proxy:** ⚠️ OK pro static mockup audit, axe, contrast, semantic lint.
  **Pre-launch human review povinný** — screen reader UX, cognitive load,
  dynamic focus, switch/voice. EAA (28. 6. 2025) nelze atestovat AI.

### 12. Data / Analytics — DOPORUČENÁ
- **Trigger pro povinnost:** release intent (= measurement plan +
  instrumentation deadline), nové metriky, A/B test, change v existujících
  events.
- **Vstup:** event taxonomy + naming convention, baseline metriky,
  XYZ measurable, power analysis, privacy classification, KPI strom.
- **Výstup:** **Measurement plan v1** (primary lagging + 2–3 leading +
  guardrail), event schema `object_action`, A/B test design + kill criteria,
  **instrumentation deadline = ship-date − 2 dny (merge-blokující)**,
  learning agenda T+30 / 60 / 90.
- **AI proxy:** ✅ AI navrhne event schema, ⚠️ člověk schválí measurement plan.

### 13. Customer support proxy — DOPORUČENÁ
- **Trigger pro povinnost:** customer base > 1 000 active users + user-facing
  change.
- **Vstup:** top-10 ticket kategorií 90d, 20 verbatim citací, frikční místa
  v current flow, churn radar, capacity baseline, KB článek baseline.
- **Výstup:** **Ticket prediction worksheet** per varianta (volume / TTR /
  deflectable / VoC match), **support docs deadline D-7 KB → D-2 makra/training
  → D+30 retro**, post-launch loop T+7 / T+30 / T+90.
- **AI proxy:** ⚠️ Pokud má AI přístup k ticket history.

### 14. End-user proxy / User research — DOPORUČENÁ default-on
- **Trigger pro opt-out:** fresh persona ≤ 3 měsíce + JTBD signed by PM
  (zdokumentovaný důvod).
- **Vstup:** persona freshness ≤ 6 mo (≥ 5 rozhovorů), JTBD card, OST v0,
  alternativy NDA (shadowing / ticket review / sales call analysis).
- **Výstup:** **Discovery Debt Detector skóre 0–10**, persona expiry compliance
  (B2C 6 mo / B2B 9 mo / internal 12 mo), **JTBD/OST node tag per varianta**,
  AI-only score deflation max 0.5 / 1.0.
- **AI proxy:** ⚠️ Vstup do session, **ne výstup**. Zvládne archetype check,
  JTBD reality check, hypothesis generation. Nezvládne novel insight, edge
  cases, cultural specifics, say-do gap, emotional arc.

### 15. DevOps / Platform — DOPORUČENÁ
- **Trigger pro povinnost:** session má sandbox (téměř vždy), nový deploy
  footprint, change v infra, významný datový tok.
- **Vstup:** **Sandbox spec Terraform modul** (24h TTL), Approved runtime list,
  footprint estimate template, observability contract (OTel + structured logs +
  tracing), secret policy (Vault + OIDC).
- **Výstup:** Deploy footprint TCO sheet per varianta, Sandbox URL + IaC
  commit, 4 golden signals dashboard, **SLO baseline** (availability / p95 /
  error budget) podle archetypu (5 archetypů: internal tool / customer portal /
  batch job / real-time API / mobile BE), runbook stub, **Promote-to-prod
  gate checklist**.
- **AI proxy:** ⚠️ Jen pro typické vzory, custom infra ne.

### 16. UX writer / Content designer — VOLITELNÁ (trigger)
- **Trigger:** user-facing copy, error / empty states, marketing claims,
  legal microcopy, B1/B2 plain language požadavek.
- **Vstup:** brand guidelines, voice & tone, B1/B2 plain language pravidla,
  ePrivacy / UCPD pravidla pro marketing claims.
- **Výstup:** microcopy per state (success / error / empty / loading / blocked),
  error message strategy, marketing claim review.
- **AI proxy:** ⚠️ Compliance sub-agent draft + lidský review.

### 17. Champion / Pilot lead — VOLITELNÁ (trigger)
- **Trigger:** druhý+ pilot v BU, scaling Pflanzeru ve společnosti.
- **Vstup:** retros předchozích pilotů, target / obstacle / next krok
  (Coaching Kata), security buddy.
- **Výstup:** retrospective, contribution do role catalogu, internal CoP
  health, T+30/60/90 reporting.
- **AI proxy:** ❌ Social capital v BU nelze nahradit.

### 18. Solution / Domain architect — VOLITELNÁ (trigger)
- **Trigger:** multi-team scope (3+ týmy), komplexní doména (vyžaduje
  Event Storming), regulovaný SDLC.
- **Vstup:** bounded contexts, ADR archiv, domain model, integration map
  cross-team.
- **Výstup:** domain delta, breaking-change registr, dependency map per
  bounded context, ADR drafts.
- **AI proxy:** ⚠️ Jen typické vzory.

---

## Decision tree — koho pozvat?

> Použij kaskádově. Každá otázka přidá další roli, pokud je odpověď ano.

### Fáze pre-flight (PŘED Session 1)

**Krok 0 — Discovery Readiness Gate.**
- Persona ≤ 6 měsíců? + JTBD podepsaný PM? + OST v0 ≥ 60 %?
- ❌ Pokud cokoli chybí → **2-week Discovery Sprint**, Session 1 odložena.

**Krok 0a — Triage tracks (paralelně, async, 48–72 h pre-read).**
- **Security & Data Triage:** Data Classification L1–L4, threat model lite,
  Approved AI Tool list, Sandbox spec.
- **Legal & Privacy Triage:** AI Act risk-tier, DPIA trigger checklist (≥ 2
  triggery = session odložena), DPA + SCC per vendor.
- **Platform Triage:** Sandbox provisioning, footprint estimate, runtime approval.
- ❌ Bez podpisů triage tracks → Session 1 nestartuje.

### Fáze role selection (kdo do místnosti)

1. **Vždy:** Zadavatel (1) + PM (2) + Facilitátor (3) → core 3.
2. **Mění se UI / přidává se view?** → +Frontend (4) + UX (6).
3. **Mění se data / API?** → +Backend (5).
4. **Pracujeme s daty uživatelů, auth, integracemi, platbami?** → +Security (7) [POVINNĚ].
5. **Jakákoli zmínka „produkce" / „pilot"?** → +QA (8) [POVINNĚ].
6. **Bude to déle než 2 sprinty / je to PI priority?** → +Eng manager (9).
7. **Osobní data, marketing, AI use case (≥ Limited)?** → +Legal/GDPR (10).
8. **Customer-facing nebo B2B > 250 zam.?** → +Accessibility (11) [default-on].
9. **Release intent (= ship plánován)?** → +Data (12).
10. **Customer base > 1 000 active users + user-facing change?** → +Customer support (13).
11. **Customer-facing flow nebo nový segment?** → +User research (14) [default-on].
12. **Změny v infra / deploy / runtime / sandbox?** → +DevOps (15).
13. **User-facing copy / marketing claims / error microcopy?** → +UX writer (16).
14. **Druhý+ pilot v BU, scaling?** → +Champion (17).
15. **Multi-team scope (≥ 3 týmy) nebo komplexní doména?** → +Solution architect (18).

**Sanity check:** Pokud je v místnosti **> 10 lidí**, je něco špatně —
buď zúžit scope, nebo udělat dvě paralelní sessions po menších buňkách.
Pokud > 3 týmy v scope → federovaný model nebo +Solution architect (18).

### MoSCoW gradace vstupů

Vstupních artefaktů napříč rolemi je 30+. Aby se Session 1 nestala fronta na
Charter, vstupy se gradují:

- **Default profil (greenfield, low-risk):** MUST only.
- **Regulated profil (data, integrace, AI Act limited):** MUST + SHOULD.
- **Audit-grade profil (high-risk AI Act, regulated SDLC):** vše (MUST + SHOULD + COULD).

Detail v `03-pre-session-priprava.md`.

### IP iteration mounting (SAFe)

- **Default:** Pflanzer cyklus do **IP iterace** (1 cyklus / IP iteration).
- **Pre-PI:** Nejcennější — výstup = realistický estimate pro PI commitment.
- **Mid-PI:** Jen pokud sponzor uvolní commit features ekvivalentní 8–10 person-days.
- **Mimo SAFe:** Atlassian Inception Play / GV Sprint variant.

---

## „AI proxy vs lidský zástupce" — 3 režimy

### Režim 1 — Vlastnické a vetovací (vždy člověk)

Tyto role **nelze** nahradit AI:
- #1 Zadavatel (final)
- #2 PM (final)
- #3 Facilitátor
- #7 Security (final veto)
- #9 EM (kapacita)
- #10 Legal (final, high-risk AI Act, special categories)
- #11 A11y (pre-launch review)
- #14 End-user (novel insight)
- #17 Champion

### Režim 2 — Konzultativní (AI proxy + human sign-off 24–48 h)

AI připraví draft, člověk podepisuje:
- #6 UX (design system audit)
- #8 QA (test generation)
- #10 Legal (L1/L2 data, minimal/limited risk, syntetická data)
- #12 Data (event schema návrh)
- #13 Customer support (ticket prediction)
- #14 End-user (archetype check, JTBD reality check)
- #16 UX writer (marketing draft)

### Režim 3 — Execution-heavy / context-light (AI vede)

AI provádí samostatně, výstupy zaznamenávané do decision logu:
- Mockup generation (vibe-coding tool dle stacku)
- Transcript summary
- Clustering feedbacku
- Score aggregation
- OpenAPI shadow agent (z perspektivy 05)
- SBOM / CVE scan
- axe-core auditing
- STRIDE draft
- Discovery Debt Detector
- Footprint kalkulačka
- Marketing compliance draft

### Pravidla cross-cutting

- **Score deflation AI-only:** max 0.5 / 1.0 (z perspektivy 14).
  **Pozor (devil's advocate Útok 6):** 0.5 je **heuristika, ne kalibrovaný
  parametr**. Stejně tak default `commitment threshold = 70/100` v Charteru.
  Pro v0.2 jsou advisory; v0.3+ má method-level Charter (ADR-0007) plánovat
  evidence-based kalibraci přes T+90 readout.
- **Decision log atribuuje vždy člověka** (DORA, AI Act čl. 14, GDPR čl. 22).
- **Pre-launch human review je nedelegovatelný** pro #11 (A11y).

---

## Změny vůči v0.1

Detailní diff: `decisions/0003-role-catalog-promotions.md`. Hlavní:

- **7 rolí povýšeno** (#8 → POVINNÁ, #10/11/12/13/14/15 → DOPORUČENÁ / DOPORUČENÁ default-on).
- **4 AI proxy degradovány** (#8/10/11/14 z ✅ na ⚠️).
- **3 nové role**: #16 UX writer, #17 Champion, #18 Solution architect.
- **Decision tree přidává Krok 0 + 0a** (Discovery + Triage gates).
- **3-režimová AI-human matice** (vlastnické / konzultativní / execution-heavy).
- **MoSCoW gradace vstupů** (default / regulated / audit-grade profil).
