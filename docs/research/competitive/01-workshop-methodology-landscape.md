# Competitive landscape — workshop methodology 2024–2026

> **Role:** Senior workshop methodology consultant (15+ let v poli).
> **Scope:** GV Design Sprint, AJ&Smart, Liberating Structures, Lean
> Inception, Lightning Decision Jam, Event Storming, Design Thinking,
> a vše, co se v 2024–2026 publikovalo jako „AI-native" varianta.
> **Filter:** *Co je v 2026 reálně dostupné, co se vyvinulo, co je nová
> kombinace?*
> **Audit target:** Pflanzer v0.3 USPs — jsou v 2026 ještě unikátní?

---

## TL;DR — verdikt pro USP audit

**Pflanzer v0.3 má dva ze tří USPs zranitelné v 2026.**

- **USP 1 (real-time AI vibe-coding viditelný stakeholderům)** — částečně
  unikátní. AJ&Smart, Design Sprint Academy a praktici GV Sprint začali
  v 2025 integrovat Lovable, Bolt, Figma Make, Galileo AI do prototypovací
  fáze. **Liší se ale šíř:** většina to dělá jako *substituci Figma fáze*
  (rychlejší fasáda), nikdo nepublikoval framework, ve kterém **BE shadow
  agent paralelně generuje OpenAPI 3.1 contract** a kde se výstup pouští
  rovnou jako production handoff. Thoughtworks AI/works + 3-3-3 metodika
  (PR 2026-Q1) je nejblíž — viz dedikovaná sekce dole. **Verdikt: adjacent,
  ne direct competitor**, ale **gap se rychle zavírá**.

- **USP 2 (score závaznosti per oddělení s váhami)** — **stále unikátní**.
  Stakeholder commitment scales existují od ~2010 (insideproduct.co, APQC,
  4-level „Enthusiastic / Help-it / Compliant / Hesitant"). Weighted scoring
  modely jsou v Product Management mainstream. **Ale kombinace** (1) per-role
  Likert s rationale field + (2) hierarchie Critical/Yellow/Score + (3)
  AI-deflated weight 0.5/1.0 + (4) anti-HiPPO „decider hlasuje poslední"
  protokol + (5) score uložené pro retrospective T+30/60/90 = **nikde jinde
  jako celistvý protokol nepublikováno**. Direct competitor neexistuje;
  nejbližší adjacent je APQC stakeholder commitment scale (kvalitativní,
  ne quantitative scoring per-variant) a Design Sprint Decider model
  (binární, ne weighted nuance).

- **USP 3 (AI-mediovaná syntéza feedbacku mezi sessions)** — **rapidly
  commoditizing**. SessionLab Custom AI Guidelines (2025), Miro Assist,
  FigJam AI populate, AJ&Smart workshopper AI features všechny v 2025-2026
  publikovaly variantu „AI clusters feedback / summarizes per role / suggests
  next action". **Pflanzerův differentiator je už jen v jednom místě:**
  „lidský facilitátor zůstává jako architect of accountability — rozhoduje,
  kdy AI mluví a kdy se konflikt eskaluje". Tří-režimová AI-human matice
  (vlastnické / konzultativní / execution-heavy role × kdo má veto) je
  publikačně unikátní, ale **operationally se konverguje k podobnému
  patternu napříč nástroji**. Pflanzer má 12-měsíční náskok v tom, že to
  má pojmenováno; **direct competitor v 2026: SessionLab AI Assistant pro
  Liberating Structures + Mural facilitation AI** (oba dělají per-role
  syntézu, oba mají human-in-the-loop, neformalizují ale tří-režimovou
  matici jako Pflanzer).

**Klíčový gap, kterému Pflanzer čelí v 2026:**

V kombinaci *„cross-functional 6-10 lidí v místnosti + AI generuje
produkční kód v session + handoff PR-ready balík"* je **přímý competitor
od dubna 2026 Thoughtworks AI/works s 3-3-3 metodikou** (3 měsíce idea→MVP,
2-day BMAD workshop produkuje PRD + architecture + UX spec rovnou pro
agent execution). Pflanzer má proti tomu:
- výhodu **lighter footprint** (2 sessions × 3 h vs. 90 dní program),
- výhodu **single-pilot vs. enterprise modernization** orientace,
- **nevýhodu**, že nemá publikovaný case study s ROI numbers,
- **nevýhodu**, že nemá enterprise sales motion (Thoughtworks ano).

Pflanzer není „nahrazen" — je v jiné kategorii. Ale obrana proti otázce
*„proč ne AI/works?"* musí explicitně říct: **„Pflanzer řeší alignment
problém PŘED tím, než se objedná AI/works engagement."** Foundation Sprint
od Knappa/Zeratskyho (2025) zaujímá v podstatě stejnou pre-AI/works pozici
ze strategy-first úhlu. **Pflanzer by se měl explicitně positionovat jako
„Foundation Sprint + Design Sprint + handoff stlačený do 2 sessions s AI
produkujícím kód, ne Figmu" — což je formulace, která dosud v repu chybí.**

---

## Aktualizace existujících entries (z `09-srovnani-existujici-metody.md`)

### Design Sprint (GV) — 2024-2026 update

**Status v repu:** *„5 dní (Knapp 2016), 4 dny (Sprint 2.0), 1 den (mikro)"*
+ *„Figma fasáda + valley of death"* kritika.

**Co je outdated:**

1. **Sprint 2.0 (AJ&Smart 2018) je etabolaný standard**, ne „semi-oficiální
   alternativa". AJ&Smart's Masterclass je jediný kurz osobně schválený
   Jakem Knappem. To by Pflanzer měl uznat jako de-facto current state.
2. **Foundation Sprint (Knapp/Zeratsky 2025)** — nová **2-day metodologie**
   uvedená v knize *Click* (Character Capital). Předřazuje se Design Sprintu
   a řeší *„what problem to sprint on"* (customer, problem, differentiation,
   Magic Lenses framework, testovatelná hypotéza). EU workshops květen 2025,
   US červen 2025. **V repu 09 chybí úplně.**
3. **AI-augmented Sprint** se v 2024-2025 stal mainstream praxí (ne novou
   metodologií). Nacho Marugán „Redesigning the Design Sprint for the Age
   of AI" (Medium 2025), Innovation Training „Design Sprints with AI" guide,
   praktici používají Lovable / Figma Make / Galileo AI / Uizard pro
   prototyping. **Knapp ani GV oficiální „Sprint 3.0" nevyhlásili**
   (k květnu 2026), ale Knapp+Zeratsky v lednu 2025 publikovali YouTube
   livestream *„Is the Design Sprint still relevant in 2025?"* — odpovídají
   ano, ale s AI co-pilotem pro synthesis a prototyping.
4. **Figma fasáda kritika je v 2026 méně silná** — nástroje Lovable / v0 /
   Bolt produkují živé URL, ne mockupy. Pflanzer to ve své kritice DS-2.0
   musí přiznat: „Sprint 2.0 + Lovable v praxi 2026 už není Figma fasáda."

**Co aktualizovat v `09`:**

- Přidat řádek „Sprint 2.0 + AI-augmented" jako samostatný sloupec nebo
  poznámku.
- Přidat Foundation Sprint jako samostatnou metodu (jiný cíl: strategy
  alignment před design execution).
- Kritika „Figma fasáda" → kvalifikovat na „GV původní 2016 verze; 2025+
  praxe používá Lovable/Bolt, ale stále chybí BE contract".

### Lightning Decision Jam (LDJ) — 2024-2026 update

**Status v repu:** Plně relevantní; není outdated.

**Co dodat:**
- AJ&Smart Workshopper.com v 2024 vyškolil 35,000+ facilitátorů; LDJ je
  jejich nejpopulárnější template.
- AI integrace LDJ není formálně publikována, ale praktici používají Miro
  Assist / ChatGPT pro post-LDJ akční clustering. Žádný formal „LDJ 2.0
  s AI" framework v 2026 neexistuje.
- LDJ zůstává komplementární k Pflanzeru (může být pre-step pro
  problem-framing před S1).

### Lean Inception — 2024-2026 update

**Status v repu:** Outdated v jedné dimenzi.

**Co je nového v 2024-2026:**

1. Paulo Caroli publikoval **State of Lean Inception Report 2024** s
   industry-wide adoption metrics.
2. Caroli.org spustil **ChatMVP.ai** — AI tool, který během MVP Canvas
   diskusí review-uje hypotézy, navrhuje improvements, prompt-uje
   doplňující otázky. Současně **FeatureCraft** — Lean Inception Feature
   Refiner pro konkretizaci feature ideas.
3. **Lean Inception for AI Agents** (Caroli, 2025) — top-5-ways article
   o použití metodiky pro alignment týmů, které integrují AI agents do
   MVP. Top mistake: *„putting 'Artificial Intelligence' as the MVP
   proposal"* — týmy mají focusovat na specifický value proposition.

**Co aktualizovat v `09`:**

- Lean Inception **má AI extension** (ChatMVP) — kritika *„Canvas končí
  v Confluence"* je v 2026 částečně oslabená, protože AI canvas tracker
  drží Canvas živý.
- Lean Inception **přebrala Pflanzerovu logiku** *„MVP = jedna jasná
  hypotéza, ne 'použijeme AI'"*. Pflanzerův MoSCoW + XYZ Hypothesis
  pattern je s ChatMVP konvergentní.

### Event Storming — 2024-2026 update

**Status v repu:** Outdated v AI dimenzi.

**Co je nového:**

1. **Qlerify** — AI-powered Event Storming tool (2024-2025), který
   automaticky identifikuje domain events z transkriptu, deduplicates
   eventy, navrhuje bounded contexts. Mění Event Storming z *„zeď
   post-itů"* na *„digitální artifact s reasoning trace"*.
2. **Event Storming pro Multi-Agent AI Systems** (DZone 2025) — DDD
   + ES jako framework pro design AI agent boundaries. Tania Storm
   *„Event Storming + AI = Turbocharged DDD"* (Medium 2025).
3. Open Group standardizoval Event Storming Workshop v O-AA standardu
   (publikováno 2024-2025).

**Co aktualizovat v `09`:**

- Kritika *„zeď post-itů obtížně přenositelná"* je s Qlerify částečně
  obsolete.
- Pflanzer by měl explicitně říct: pre-step Event Storming s Qlerify =
  ideální pre-flight pro Pflanzer S1, pokud cílový projekt má 3+ bounded
  contexts.

### Liberating Structures — 2024-2026 update

**Status v repu:** Outdated v AI dimenzi.

**Co je nového:**

1. **SessionLab Custom AI Guidelines** (2025) — workspace setting, kde
   facilitátor pre-konfiguruje LS framework jako default; AI Assistant
   pak navrhuje strukturu sezení per LS template.
2. **Copenhagen Symposium on Human-Centered AI SE** (2025) — celý
   research event navržen kolem LS, demonstruje aplikaci v AI engineering
   prostředí.
3. **ACM CACM 2025 article** *„From Passive to Participatory: How LS
   Can Revolutionize Our Conferences"* — institucionální adopce LS
   v akademii.
4. **1-2-4-All** + **TRIZ** zůstávají Pflanzerovými klíčovými importy.
   AI extensions Liberating Structures nepřinesly formální verzování,
   ale tools (SessionLab, Mural) přidaly *„suggest next LS"* AI feature.

---

## Nové competitor entries (chybí v `09`)

### 1. Foundation Sprint (Knapp + Zeratsky, 2025)

- **Co:** 2-day workshop, předchází Design Sprintu. Den 1: customer
  + problem + competitors + differentiation. Den 2: Magic Lenses
  framework pro evaluation, výběr testable hypothesis.
- **Kdo:** Jake Knapp & John Zeratsky (Character Capital).
- **Publikováno:** Začátek 2025 (Q1), kniha *Click: How to Make What
  People Want* (Character Capital).
- **Claim:** *„Don't run in the wrong direction. Foundation Sprint
  defines WHAT problem to sprint on before you commit 4-5 days."*
- **Vztah k Pflanzerovi:** **Doplňkový, ne competitor.** Foundation
  Sprint řeší strategy-alignment před design execution. Pflanzer S1
  předpokládá, že strategy už víceméně víš (sponzor + 1-věty success
  threshold). **Doporučení:** Pflanzer by měl v `01-filozofie-a-kdy-pouzit.md`
  explicitně říct: *„Pokud nemáš jasné customer / problem framing,
  spusť Foundation Sprint před Pflanzerem. Bez toho generuje krásné
  weby pro špatný problém."*

### 2. AI Design Sprint (Design Sprint Academy, 2020-2025, „5 let")

- **Co:** 4-day cross-functional sprint specificky pro AI opportunity
  identification. Discovery Pod (Days 1-2) = cross-functional team
  7-9 lidí + external AI expert. Den 3-4: prototype + test s real users.
  AI coach validates feasibility během prototyping.
- **Kdo:** Design Sprint Academy (designsprint.academy, Polsko/EU).
- **Publikováno:** První verze 2020, v 2025 publikován *„Design Sprint
  3.0 with Problem Framing"* + *„AI Sprint Bootcamp"* program.
- **Claim:** *„From AI ambition to execution. Cross-functional team
  identifies AI opportunity, prototypes a solution, tests it before
  development."*
- **Vztah k Pflanzerovi:** **Direct adjacent — overlap ~40 %.**
  - Společné: cross-functional team 7-9, prototype-first, anti-mockup
    bias.
  - Rozdíl: Design Sprint Academy je **discovery-led** (Days 1-2
    Problem Framing), Pflanzer je **execution-led** (S1 už staví
    prototyp na sponzorem zadaný problém).
  - Rozdíl: Design Sprint Academy nedělá **production handoff**
    (test → recommendation), Pflanzer dělá PR-ready balík.
  - Rozdíl: Design Sprint Academy nemá **score závaznosti** —
    výstupem je doporučení, ne commitment per-role.
- **Riziko pro Pflanzer:** Konfuze v marketingu. Klient slyší „AI
  Design Sprint" a předpokládá, že je to Design Sprint Academy.
  **Doporučení:** Pflanzer nikdy nepoužít termín „AI Design Sprint"
  pro vlastní metodu (je to brand DSAA). Použít *„AI-augmented
  alignment workshop"* nebo *„Pflanzer method"*.

### 3. Thoughtworks AI/works + 3-3-3 metodika (2026)

- **Co:** Enterprise modernization platform + delivery methodology.
  90 dní idea → MVP in production. **3 fáze:** (1) product concept
  → stakeholder alignment, (2) prototype → desirability/viability/feasibility,
  (3) MVP in production → ship & continuous evolution. Agentic platform
  unifikuje legacy understanding, requirements enhancement, dynamic
  spec generation, agent code generation.
- **Kdo:** Thoughtworks (firma, co vymyslela Agile).
- **Publikováno:** AI/works platform launch **Q1 2026** (PRNewswire,
  itbrief.com), workshop offerings průběžně 2024-2026.
- **Claim:** *„From idea to production in 90 days. Industrial-grade
  systems that grow up instead of grow old."*
- **Vztah k Pflanzerovi:** **Largest direct competitor v 2026** pro
  enterprise modernization use case. Overlap ~60 %.
  - Společné: cross-functional 6-10 lidí, AI generuje kód, production
    handoff je cíl, ne mockup.
  - Rozdíl: Thoughtworks 3-3-3 je **90 days**, Pflanzer je **2 sessions
    × 3 h + 5-7 dní mezi**. Pflanzer je 30-50× kratší.
  - Rozdíl: Thoughtworks vyžaduje **enterprise sales engagement**
    (senior director sponsorship, 6-10 dedicated participants).
    Pflanzer je **self-service single-pilot** kompatibilní.
  - Rozdíl: Thoughtworks **vlastní platformu** (AI/works je SaaS),
    Pflanzer používá **off-the-shelf** (Claude, Cursor, Bolt, Lovable).
  - Rozdíl: Thoughtworks dělá **legacy modernization primary**;
    Pflanzer dělá **greenfield feature alignment primary**.
- **Riziko pro Pflanzer:** Enterprise buyer s budget €500k+ pravděpodobně
  zvolí Thoughtworks (jméno, audit-grade governance, IBM Bob alternativa).
  Pflanzer musí mít **ROI argument na 80 % výsledku za 5 % nákladů**.
- **Doporučení:** V `00-tldr.md` přidat řádek *„Konkurence: Thoughtworks
  AI/works (90 days, enterprise) vs. Pflanzer (2 weeks, pilot)."*

### 4. BMAD Method (Breakthrough Method for Agile AI-Driven Development)

- **Co:** Open-source agentic framework. **Specializované AI agents**
  s rolemi: Analyst, PM, Architect, UX Designer, Scrum Master, PO,
  Dev, QA. **Two-phase design:** Agentic Planning (PRD, architecture,
  UX spec generated by AI) → Context-Engineered Development (Dev
  agent implements stories). **2-day workshop** Improving.com učí
  týmy konfigurovat codebase pro BMAD spec-driven flow.
- **Kdo:** bmad-code-org (GitHub) + Improving Consulting.
- **Publikováno:** 2025, většina aktivity Q4 2025 - Q1 2026.
  26 agents, 68 workflows, 655 souborů (vibesparking.com analysis
  2026-01).
- **Claim:** *„I ditched vibe coding for BMAD: structured AI agents
  turn vibe-coding chaos into production-ready software."*
- **Vztah k Pflanzerovi:** **Adjacent, ne direct.** Overlap ~30 %.
  - Společné: AI agents v rolích, spec-driven flow, production-ready
    output, anti-vibe-coding-chaos.
  - Rozdíl: BMAD je **post-workshop tooling** — vyžaduje, že už máš
    týmem ratified problem. Pflanzer je **workshop sám** + handoff
    na takovou tooling vrstvu.
  - Rozdíl: BMAD je **single-developer-friendly** (1 osoba + 8 agents),
    Pflanzer je **cross-functional 6-10 lidí** (lidé jsou co-creators,
    ne uživatelé tooling).
  - Komplementární: Pflanzer S2 handoff → BMAD pipeline = realistic
    flow. **Doporučení:** přidat BMAD jako jednu z post-Pflanzer
    handoff options vedle Cursor / Claude Code.

### 5. Spec-Driven Development (SDD, Thoughtworks Technology Radar Vol 33)

- **Co:** Vývojový paradigm. **/specify → /plan → /tasks** pipeline,
  kde well-crafted spec funguje jako prompt pro AI agents. GitHub
  spec-kit (open-source), Kiro (Amazon), Tessl, AI/works (Thoughtworks)
  jsou implementace.
- **Kdo:** Thoughtworks Technology Radar Vol 33 (2025) — řazení
  *„Assess"*. Související: Martin Fowler články.
- **Publikováno:** 2025.
- **Claim:** *„Stakeholder alignment in /specify phase: review and
  clarify stories, acceptance criteria, motivation. Spec serves as
  always-up-to-date documentation."*
- **Vztah k Pflanzerovi:** **Methodology backbone, ne competitor.**
  Pflanzer S2 → handoff package efektivně produkuje takovou spec
  (decision package, OpenAPI 3.1 contract, score per role). **Pflanzer
  se může pozicionovat jako *„first workshop methodology designed
  to output a Thoughtworks-grade spec for downstream AI execution"*.**
- **Varování:** Thoughtworks Radar warning: *„heavy up-front
  specification and big-bang releases"* je antipattern. Pflanzer musí
  argumentovat, že 2 sessions × 3 h **není heavy** (vs. 90-day
  spec-fest).

### 6. AI-Augmented Sprint Planning (Agile Leadership Day India, Mar 2026)

- **Co:** Scrum framework adaptation pro autonomous bots v týmech.
  Capacity, effort, backlog readiness — vše musí počítat s agents.
- **Kdo:** Agile Leadership Day India.
- **Publikováno:** Březen 2026.
- **Claim:** *„Major structural shift in how teams view capacity
  when integrating autonomous bots into Scrum teams."*
- **Vztah k Pflanzerovi:** **Tangenciální.** AI-augmented Scrum
  funguje na sprint-cadence úrovni (každé 2 týdny); Pflanzer je
  one-shot workshop methodology. Komplementární: Pflanzer kick-off
  → AI-augmented Scrum continuous delivery.

### 7. AI Design Sprint (course, AJ&Smart 2025)

- **Co:** AJ&Smart's official AI Design Sprint course (Q3 2025).
  4-day format with AI tooling integration (Galileo, Figma Make,
  Lovable) explicitly in prototyping phase.
- **Kdo:** AJ&Smart (Workshopper.com brand).
- **Claim:** *„Sprint with AI tools: prototype in minutes, not hours.
  Same Sprint 2.0 structure, AI accelerates synthesis and prototyping."*
- **Vztah k Pflanzerovi:** **Adjacent — overlap ~35 %.**
  - Společné: AI prototyping in-session, cross-functional small team.
  - Rozdíl: AJ&Smart si drží Sprint 2.0 strukturu (4 dní). Pflanzer
    zkracuje na 2 sessions × 3 h.
  - Rozdíl: AJ&Smart neřeší **score závaznosti** — Decider model
    zůstává binární.
  - Rozdíl: AJ&Smart neřeší **production handoff** (prototype = test,
    ne PR-ready).

---

## USP claim audit (detail per USP)

### USP 1 — Real-time AI vibe-coding viditelný stakeholderům

**Pflanzer claim (recapped z `09`):** *„Mockup vzniká v session, ne mezi
sessions. AI generátor (Claude, Cursor, Bolt, v0) v sub-hodinovém cyklu
produkuje 1-3 funkční varianty z verbálního inputu týmu. BE shadow agent
paralelně generuje draft OpenAPI 3.1 per varianta."*

**Direct competitors (2024-2026):**

| Metoda | Co dělá podobně | Co dělá jinak |
|---|---|---|
| **Thoughtworks AI/works + 3-3-3** | Generuje produkční kód, ne fasádu | 90 days, ne 1 session; potřebuje enterprise engagement |
| **BMAD Method** | Agentic planning → PRD + architecture + UX spec → code | Není workshop — je to post-workshop tooling pro 1-2 lidi |
| **Replit Agent 3 / Agent 4** (Q4 2025) | Live URL stakeholder access (SCIM viewer seats) | Není workshop methodology — je to platform |
| **Lovable + Cursor combo** (2025 prototyping stack) | Used in many Sprint 2.0 implementations | Není formalizovaná metodika; čistě tooling stack |

**Adjacent (dělá podobně, ale jinak):**

- **AJ&Smart AI Design Sprint course** (Q3 2025) — AI prototyping ano,
  ale **bez paralelního BE contract** generation. Stakeholders vidí
  UI, ne contract.
- **Design Sprint Academy AI Design Sprint** — AI prototyping s AI
  coach feasibility check, ale **bez BE shadow OpenAPI** workflow.
- **Innovation Training „Design Sprints with AI" guide** (2025) — best
  practice doporučuje Lovable / Figma Make / Galileo AI v Sprint week 3,
  ale nemá protokol *„BE shadow agent paralelně"*.

**Kde je Pflanzer ještě skutečně unikátní:**

1. **BE shadow agent paralelně generuje OpenAPI 3.1 contract per
   variant.** Žádná publikovaná metoda v 2026 to nedělá v session.
   AI/works to dělá automatizovaně, ale **po** sezení, ne během.
2. **Sub-hodinový cyklus mezi verbálním inputem a klikací variantou,
   kde celý tým je v místnosti.** Sprint 2.0 + Lovable má často model
   *„designer/dev jde do Lovable, vrátí se za hodinu s prototypem"*.
   Pflanzer chce **týmovou klávesnici** (sponzor diktuje, dev/PM
   kontroluje prompt, AI generuje → tým komentuje).
3. **Instant accessibility quickscan + axe-core run** v S1 jako
   automatický kontrolní bod. Žádná competing methodology v 2026
   to nemá embedded.

**Verdikt USP 1:** **Adjacent, ne direct.** Pflanzer ztrácí čistou
exkluzivitu generování kódu v session (každý dnes umí), ale **drží
exkluzivitu specifické kombinace UI + BE contract + a11y check
v jednom session okamžiku**. Komunikační riziko: *„AI generuje kód
v session"* už není wow-factor; *„AI generuje UI + OpenAPI + a11y
report současně, vše ratifikováno cross-fn týmem"* ano.

### USP 2 — Score závaznosti per oddělení

**Pflanzer claim (recapped z `09`):** *„1-5 Likert s rationale field
per role per varianta, weight per role (Security/Legal/A11y high-risk
= blocker, ne weighted vote), hierarchie Critical / Yellow / Score.
AI-only feedback deflated max 0.5/1.0. Zadavatel hlasuje poslední."*

**Direct competitors:** **Žádný.** Po systematic search v 2024-2026:

- **APQC Stakeholder Commitment Scale** (2020+) — 4-level kvalitativní
  (Enthusiastic / Help-it-work / Compliant / Hesitant). **Žádné per-role
  weighting, žádné rationale field, žádné Likert.**
- **Weighted scoring models** (Product School standard) — 1-5 nebo 1-10
  per kritérium per varianta. **Žádné role-based weighting, žádný
  AI-deflated coefficient, žádný „Critical/Yellow/Score" hierarchy.**
- **Dot voting** (LDJ, Sprint, all of facilitation field) — equal-weight,
  silent, anonymous. **Nemá rationale, nemá role-based weight, nemá
  AI handling.**
- **Sprint Decider model** — 1 osoba s binary veto. **Nemá score
  per-role, nemá nuance, nemá audit trail.**

**Adjacent (podobné, ale jinak):**

- **Lovable.dev quasi-RACI matice pro AI agents** — kdo schvaluje co
  v multi-agent flow. **Není stakeholder-facing, je intra-AI.**
- **Mural facilitation Superpowers** — anonymous voting + private
  notes. **Nemá role weighting, nemá AI deflation.**
- **Liberating Structures 1-2-4-All** — silent first → group → all.
  **Nemá scoring, jen presence/absence of position.**

**Verdikt USP 2:** **Direct competitor neexistuje k květnu 2026.**
Pflanzer **drží 12-měsíční náskok** v tom, že tohle má pojmenováno
a operationalizováno. **Riziko:** kdokoliv s 1 facilitátorem a SessionLab
AI by tohle uměl reproduce za týden. **Defenzivní strategie:** Pflanzer
musí mít empirická data, že score závaznosti **predikuje post-launch
adoption rate** (T+30/60/90 retrospective). Bez dat je to elegantní
protocol, ale ne defensible USP.

### USP 3 — AI-mediovaná syntéza feedbacku v S2

**Pflanzer claim (recapped z `09`):** *„Mezi-session sběr feedbacku
per oddělení → AI v S2 vede výklad, jaké oddělení mělo jaké připomínky
a navrhuje, jak je zapracovat. Lidský facilitátor zůstává jako
architect of accountability — rozhoduje, kdy AI mluví, kdy člověk mlčí,
a kdy se konflikt eskaluje."*

**Direct competitors (2024-2026):**

| Metoda | Co dělá podobně | Co dělá jinak |
|---|---|---|
| **SessionLab AI Assistant + Custom Guidelines** (2025) | Per-role syntéza feedbacku, suggest LS structure pro follow-up | Nemá explicit *„architect of accountability"* protokol; AI suggestions jsou rovnocenné s human input |
| **Miro Assist** (2025) | Cluster sticky notes per téma, summarize content | Není workshop-cycle aware; jednorázová operace |
| **FigJam AI populate + summarize** (2025) | Template + summary generation | Není multi-session, není per-role |
| **Mural Facilitation Superpowers + AI** | Per-participant private notes + AI synthesis suggest | Nemá explicit human-veto matrix |
| **Lyssna Research Synthesis Report 2025** | AI-assisted synthesis je 21 % use; workshop synthesis je 21 % use | Není formalizovaná methodology, je to tooling survey |

**Adjacent:**

- **RAISE guidance framework** (Cochrane + Campbell + JBI + CEE, 2025)
  — AI-mediated evidence synthesis methodology, ale je to **systematic
  review tool**, ne **workshop tool**.
- **AI Scientist v2 (Sakana 2025)** — workshop-level AI papers, ale
  je to **publication assist**, ne **stakeholder synthesis**.

**Kde je Pflanzer ještě skutečně unikátní:**

1. **Formalizovaná tří-režimová AI-human matice** (vlastnické / konzultativní
   / execution-heavy role × kdo má veto). Operationally se v SessionLab /
   Mural konverguje k podobnému patternu, ale **nikdo to nemá publikováno
   jako framework s explicit role list a veto map**.
2. **Mezi-session async cycle s 24h TTL sandbox** + AI agreguje a vede
   výklad v S2. SessionLab dělá per-session AI, ne **mezi-session
   continuous AI tracking**.
3. **Vazba na audit trail** — score uložen, decision attribuovaný
   člověku, DORA / AI Act čl. 14 / GDPR čl. 22 compliance. **Žádný
   facilitation tool v 2026 nemá audit-grade output by default.**

**Verdikt USP 3:** **Adjacent, ne direct.** Pflanzer drží náskok
v formalization + audit trail, **ale operational gap se v 2026-2027
zavře**. SessionLab roadmap explicitně směřuje k *„AI Assistant search
your workspace to find and apply patterns from sessions you've already
run"* — to je 80 % Pflanzer S2 AI synthesis. **12-18 měsíců window
pro Pflanzer zaplatit za formalization advantage publikací nebo
case-study.**

---

## Co Pflanzer ještě nemá z existujících metod (doporučení pro v0.4)

### 1. Foundation Sprint pre-step jako explicit option

**Z:** Knapp/Zeratsky 2025.
**Co převzít:** Magic Lenses framework (evaluation kritérií pro
shortlist variants); customer + problem + differentiation 1-pager
jako vstup do Pflanzer S1 pre-flight. **Když strategy není jasná,
Pflanzer S1 generuje krásné weby pro špatný problém** — Foundation
Sprint zaplní tento gap.

**Recommendation pro v0.4:** Přidat do `01-filozofie-a-kdy-pouzit.md`
sekci *„Když potřebuješ Foundation Sprint před Pflanzerem"*. Magic
Lenses framework integrovat do pre-flight checklist.

### 2. Sequencer prioritization (Lean Inception)

**Z:** Paulo Caroli, Lean Inception.
**Co převzít:** Po S2 winning variant identify, jaký je *„walking
skeleton" sequence* features pro production rollout. Sprint 1 = login
+ search. Sprint 2 = checkout. atd. Pflanzer **má MoSCoW**, ale
**nemá temporal sequence**.

**Recommendation pro v0.4:** Do `07-handoff-do-vyvoje.md` přidat
Sequencer výstup jako optional sekci (pro multi-sprint roadmap).

### 3. Qlerify-style domain event extraction (Event Storming + AI)

**Z:** Qlerify 2024-2025, Tania Storm 2025.
**Co převzít:** Pokud projekt má 3+ bounded contexts, S1 pre-flight
mock-step *„AI extracts domain events z transkriptu stakeholder
interviews → ratify with team"*. To je 30-min addition před S1, ale
zvyšuje shared mental model.

**Recommendation pro v0.4:** Přidat do `03-pre-session-priprava.md`
optional *„Domain Pre-Map"* step pro DDD-relevant projekty.

### 4. Spec-Driven Development output format

**Z:** Thoughtworks Tech Radar Vol 33, GitHub spec-kit, Kiro, Tessl.
**Co převzít:** Pflanzer S2 handoff package by měl být **spec-kit
compatible** — `/specify` (problem + acceptance criteria), `/plan`
(architecture), `/tasks` (stories). To umožní *„one-click handoff"*
do BMAD / AI/works / Claude Code / Cursor.

**Recommendation pro v0.4:** Do `07-handoff-do-vyvoje.md` přidat
spec-kit-compatible export. Pflanzer se může pozicionovat jako
*„first workshop methodology that outputs spec-kit-grade spec from
2 sessions × 3h"*.

### 5. SessionLab Custom AI Guidelines pattern

**Z:** SessionLab 2025 update.
**Co převzít:** Pre-konfigurovat AI agents Pflanzer-specific guidelines
(LS protokol pro S1, MoSCoW pro variant filtering, atd.) jako workspace
default, ne per-session prompt. **Tohle Pflanzer Tool fáze 2 dělat by měl.**

**Recommendation pro v0.4 / fáze 2:** Pflanzer Tool ukládá role
catalog + protokol templates do project workspace; AI agents pulling
from this workspace, ne re-prompting v každé session.

### 6. Replit Agent live URL stakeholder access pattern

**Z:** Replit Agent 3/4, 2025.
**Co převzít:** Mezi-session sandbox URL **bez login** pro stakeholders,
ale **s telemetry tracking** (kdo kdy klikal, kde se zasekl). Replit
to dělá přes „viewer seats". Pflanzer S2 pak ví, kteří stakeholdeři
fakt prototype prošli vs. kteří jen hlasovali.

**Recommendation pro v0.4:** Sandbox deployment per variant musí mít
basic analytics (page views, click depth, time on page) jako vstup
do S2 AI synthesis.

### 7. BMAD agent role embedding pro post-Pflanzer execution

**Z:** BMAD Method, 2025-2026.
**Co převzít:** Post-S2 handoff může include „BMAD config" — jak
nakonfigurovat BMAD agents pro execution winning variant. Pflanzer
neimplementuje BMAD, ale **vystavuje export** kompatibilní s BMAD
agentic flow.

**Recommendation pro v0.4:** Optional handoff target = BMAD pipeline,
vedle Cursor / Claude Code / Lovable production.

---

## Reference (URL list)

### Sprint family (Knapp/Zeratsky/AJ&Smart/DSA)

- *Is the Design Sprint still RELEVANT in 2025?* (YouTube, Knapp/Zeratsky,
  leden 2025): https://www.youtube.com/watch?v=8-Syxs3SQ7s
- AJ&Smart Design Sprint 2.0: https://ajsmart.com/design-sprint-2-0/
- AJ&Smart Workshopper LDJ: https://www.workshopper.com/lightning-decision-jam
- *Redesigning the Design Sprint for the Age of AI* (Nacho Marugán,
  Medium 2025): https://medium.com/design-bootcamp/redesigning-the-design-sprint-for-the-age-of-ai-568654a06152
- *Faster. Smarter. Sharper. The New AI-Driven Design Sprint* (Suresh
  John Senegarapu, Medium 2025): https://medium.com/design-bootcamp/faster-smarter-sharper-the-new-ai-driven-design-sprint-a70fc5999579
- *Design Sprints with AI* (Innovation Training, 2025): https://www.innovationtraining.org/design-sprints-with-ai/
- The Foundation Sprint: https://thefoundationsprint.com/
- *Foundation Sprint introduction* (Lenny's Newsletter, 2025): https://www.lennysnewsletter.com/p/introducing-the-foundation-sprint
- *Click* (Character Capital, Knapp/Zeratsky 2025): https://www.character.vc/click
- Design Sprint Academy AI Design Sprint: https://www.designsprint.academy/workshops/ai-design-sprints
- *AI Design Sprints vs. AI-powered Design Sprints* (DSA blog): https://www.designsprint.academy/blog/ai-design-sprints-and-ai-powered-design-sprints
- *Design Sprints in 2025: Enterprise Questions* (DSA blog): https://www.designsprint.academy/blog/design-sprints-in-2025-the-questions-enterprise-teams-are-really-asking

### Lean Inception / Caroli

- Lean Inception for AI Agents (Caroli, 2025): https://caroli.org/en/lean-inception-for-ai-agents/
- ChatMVP.ai: https://chatmvp.ai (via caroli.org)
- FeatureCraft Lean Inception Feature Refiner (via Caroli ecosystem)

### Event Storming + AI

- *Event Storming + AI = Turbocharged DDD* (Tania Storm, Medium 2025):
  https://medium.com/@tanstorm/event-storming-ia-ddd-turbo-d8f720fccfb0
- Qlerify Event Storming Tool: https://www.qlerify.com/event-storming-with-qlerify
- *Multi-Agent AI + DDD + Event Storming* (DZone 2025): https://dzone.com/articles/multi-agent-ai-ddd-event-storming
- Open Group O-AA Event Storming Workshop: https://pubs.opengroup.org/architecture/o-aa-standard/event-storming-workshop.html

### Liberating Structures + AI

- SessionLab 2025 recap: https://www.sessionlab.com/blog/sessionlab-2025-recap/
- *From Passive to Participatory* (CACM, 2025): https://cacm.acm.org/opinion/from-passive-to-participatory-how-liberating-structures-can-revolutionize-our-conferences/
- Copenhagen Symposium (Daniel Russo, 2025): https://www.danielrusso.org/copenhagen-symposium-human-centered-ai-software-engineering/

### Thoughtworks (3-3-3, AI/works, SDD)

- Thoughtworks 3-3-3 + AI/works platform: https://www.thoughtworks.com/ai/works/
- AI/works launch announcement (PRNewswire, Q1 2026): https://www.prnewswire.com/news-releases/aiworks-heralds-a-new-era-of-agile-and-next-generation-software-development-302664456.html
- *Thoughtworks unveils AI/works for legacy modernisation* (itbrief): https://itbrief.com.au/story/thoughtworks-unveils-ai-works-for-legacy-modernisation
- Spec-Driven Development (Thoughtworks blog, 2025): https://www.thoughtworks.com/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices
- Spec-Driven Development Tech Radar Vol 33: https://www.thoughtworks.com/radar/techniques/spec-driven-development
- *Understanding SDD: Kiro, spec-kit, Tessl* (Martin Fowler, 2025): https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- *Beyond the prototype: Generative AI products* (Thoughtworks Canada): https://www.thoughtworks.com/en-ca/insights/blog/product-innovation/beyond-prototype-reality-delivering-generative-ai-products
- *Can vibe coding produce production-grade software?* (Thoughtworks): https://www.thoughtworks.com/insights/blog/generative-ai/can-vibe-coding-produce-production-grade-software

### BMAD Method

- BMAD Method GitHub: https://github.com/bmad-code-org/BMAD-METHOD
- BMAD docs: https://docs.bmad-method.org/
- *What Is BMAD?* (Reenbit, 2025-2026): https://reenbit.com/the-bmad-method-how-structured-ai-agents-turn-vibe-coding-into-production-ready-software/
- BMAD Architecture Deep Dive (Vibe Sparking AI, 2026-01): https://www.vibesparking.com/en/blog/ai/bmad/2026-01-15-bmad-agents-workflows-tasks-files-architecture/
- Agentic Development Workshop (Improving): https://www.improving.com/services/training/ai/agentic-development-workshop/

### Vibe coding research & frameworks

- VibeX 2026 workshop (EASE 2026): https://conf.researchr.org/home/ease-2026/vibex-2026
- *Vibe Coding for Product Design* (arXiv 2509.10652): https://arxiv.org/pdf/2509.10652
- *Vibe Coding Needs Vibe Reasoning* (arXiv 2511.00202): https://arxiv.org/html/2511.00202
- *Good Vibrations? Co-Creation, Communication, Flow, Trust* (arXiv 2509.12491): https://arxiv.org/html/2509.12491v1
- IBM: *What is Vibe Coding?*: https://www.ibm.com/think/topics/vibe-coding

### AI prototyping stack (Bolt / Lovable / v0 / Cursor / Replit)

- *Choosing your AI prototyping stack* (Anna Arteeva, Medium 2025):
  https://annaarteeva.medium.com/choosing-your-ai-prototyping-stack-lovable-v0-bolt-replit-cursor-magic-patterns-compared-9a5194f163e9
- *Lovable + Cursor: Best of Both Worlds* (Anna Arteeva, Medium):
  https://annaarteeva.medium.com/lovable-cursor-best-of-both-worlds-for-ai-prototyping-b760aced392d
- Replit Agent 3 (InfoQ, 2025): https://www.infoq.com/news/2025/09/replit-agent-3/
- Replit 2025 in Review: https://blog.replit.com/2025-replit-in-review
- *Lovable & Bolt.new vs. Cursor & Claude Code* (Breathbase): https://www.breathbase.io/en/blog/lovable-bolt-vs-cursor-claude

### Facilitation tools + AI

- *Redesigning the workshop: AI-powered facilitation in Miro, FigJam, Mural*
  (UX.raspberry, Medium): https://medium.com/@uxraspberry/redesigning-the-workshop-ai-powered-facilitation-in-miro-figjam-and-mural-84d8b3deab62
- Miro AI Prototype Generator: https://miro.com/ai/prototype-ai/
- Generative AI Workshop Template (Miroverse): https://miro.com/miroverse/generative-ai-workshop/
- NN/G dot voting article: https://www.nngroup.com/articles/dot-voting/
- *AI for Design Workflows* (NN/G course): https://www.nngroup.com/courses/ai-for-design/

### McKinsey / BCG / consulting AI methodologies

- BCG *How Companies Can Prepare for AI-First Future* (2025): https://www.bcg.com/publications/2025/how-companies-can-prepare-for-ai-first-future
- BCG *AI at Work 2025*: https://web-assets.bcg.com/fd/0d/bcc5dfae4cbaa08c718b95b16cf5/ai-at-work-2025-slideshow-june-2025-edit-02.pdf
- BCG *Agents Accelerate Next Wave of AI Value Creation* (2025): https://www.bcg.com/publications/2025/agents-accelerate-next-wave-of-ai-value-creation
- *How AI is Redefining Strategy Consulting: McKinsey, BCG, Bain* (Takafumi Endo, Medium): https://medium.com/@takafumi.endo/how-ai-is-redefining-strategy-consulting-insights-from-mckinsey-bcg-and-bain-69d6d82f1bab
- McKinsey *Agentic Organization* (2025): https://www.brianheger.com/the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era-mckinsey/

### Stakeholder commitment & weighted voting

- APQC Stakeholder Commitment Scale: https://www.apqc.org/resource-library/resource-listing/identify-stakeholders-and-their-levels-commitment
- Inside Product Commitment Scale: https://insideproduct.co/commitment-scale/
- Product School Weighted Scoring Guide: https://productschool.com/blog/product-fundamentals/weighted-scoring-model

### AI workshop / enterprise frameworks (other)

- *AI Workforce Implementation Roadmap 2026* (Knowlee): https://www.knowlee.ai/blog/ai-workforce-implementation-roadmap-2026
- IBM Bob AI Development Partner (PR, 2026-04): https://newsroom.ibm.com/2026-04-28-introducing-ibm-bob-ai-development-partner-that-takes-enterprises-from-ai-assisted-coding-to-production-ready-software
- AI-Augmented Sprint Planning (Agile Leadership Day India, Mar 2026):
  https://agileleadershipdayindia.org/blogs/ai-augmented-scrum-framework/ai-augmented-sprint-planning.html
- *The Death of the Mockup: How AI Is Collapsing the Design-to-Code Handoff* (MindStudio):
  https://www.mindstudio.ai/blog/death-of-the-mockup-ai-design-to-code

---

## Změny v `09-srovnani-existujici-metody.md` (actionable list)

1. **Add row:** Foundation Sprint (2025, Knapp/Zeratsky) — 2-day strategy
   alignment pre-Design-Sprint. Komplementární, ne competitor.
2. **Add row:** Thoughtworks AI/works + 3-3-3 (2026 Q1) — 90-day idea→MVP,
   enterprise. **Largest direct competitor pro enterprise budget.**
3. **Add row:** AI Design Sprint (Design Sprint Academy, 2020-2025) — 4-day
   cross-fn s AI coach. Adjacent overlap ~40 %.
4. **Add row:** BMAD Method (2025-2026) — post-workshop agentic execution.
   Komplementární handoff target, ne competitor.
5. **Add row:** Spec-Driven Development (Thoughtworks Radar Vol 33, 2025) —
   methodology backbone, ne workshop. Pflanzer S2 handoff → SDD-compatible.
6. **Update Design Sprint row:** kritika *„Figma fasáda"* kvalifikovat na
   *„Sprint 2.0 + Lovable v 2026 už není Figma fasáda; gap je v BE contract"*.
7. **Update Lean Inception row:** přidat *„ChatMVP.ai + FeatureCraft (2025)
   = AI extensions, Canvas-in-Confluence kritika oslabena"*.
8. **Update Event Storming row:** přidat *„Qlerify AI extraction (2024-2025)
   = post-it wall obsolete; O-AA standardization (2024-2025)"*.
9. **Update Liberating Structures row:** přidat *„SessionLab Custom AI
   Guidelines (2025), Copenhagen Symposium (2025) = LS-as-default
   institutional adoption"*.
10. **Add Diferenciátor #4 (proposal):** *„Pflanzer handoff je
    spec-kit-compatible / BMAD-feedable"* — nový diferenciátor přidávající
    explicit handoff into emerging spec-driven AI execution tooling.

---

*Konec dokumentu. Stav: květen 2026, ~ 580 řádků.*
