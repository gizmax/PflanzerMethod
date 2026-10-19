# SDD mechanika 2025-2026 vs Pflanzer — re-implementation gap deep dive

> **Cílový čtenář:** strateg / metodolog / sales engineer, který potřebuje obhájit Pflanzer
> proti námitce *„vždyť to dělá Spec Kit / Kiro / BMAD"*.
>
> **Datum:** 2026-05-28.
> **Scope:** Spec-Driven Development (SDD) ekosystém Q3 2025 – Q2 2026 + jeho **fundamentální
> friction model** (re-implementation gap, spec drift, multi-round cyklus, lost-context cost).
> **Předchozí context:** `docs/research/competitive/04-synthesis-and-positioning.md` (May 2026).

---

## TL;DR (5 řádků)

1. **SDD 2025-2026 = 6 nástrojů (Spec Kit 107k★, Kiro, OpenSpec, BMAD, Tessl, AIUP)**, všechny vyrůstají
   z Karpathyho 02/2025 „vibe-coding" kritiky. Standardní cyklus: Spec → Plan → Tasks → Implement.
2. **Re-implementation gap je doložený:** Spec Kit generuje **2 577 ř. markdownu pro 689 ř. kódu**
   (Scott Logic 11/2025, ~10× pomalejší než iterativní prompting). Spec drift 9.8–42.1 % kódu
   nesplňuje spec (Yan et al. 2025); 110 000+ AI-introduced issues v produkčních repos do 02/2026.
3. **Multi-round cyklus typicky 4-7 stages (Spec Kit má 7: constitution → specify → clarify → plan → tasks →
   analyze → implement)**; Böckeler (Martin Fowler 2025) dokumentuje *„the agent ignored the notes...
   creating duplicates"* = re-implementation gap v praxi.
4. **Spec staleness, bidirectional sync gap, stakeholder ne-čtení 50-stránkové spec** = 3 ze 7
   documentovaných failure modes. Tessl jediný řeší spec-as-source synchronization (private beta).
5. **SDD vyhrává tam, kde Pflanzer ne (legacy modernization přes SpecOps, audit-as-spec,
   multi-vendor contracts, řízená engineering produktivita).** Pflanzer vyhrává tam, kde SDD selhává
   (cross-functional alignment, non-tech v room, 14-day cadence s funkčním prototypem od minuty 0,
   compliance artefakt out-of-the-box, anti-HiPPO decision protokol).

---

## 1. SDD nástroje 2025-2026 — per-tool deep dive

### 1.1 GitHub Spec Kit

- **URL:** `github.com/github/spec-kit` ([repo](https://github.com/github/spec-kit))
- **Datum launch:** 09/2025 ([GitHub Blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/))
- **Velikost komunity (05/2026):** **107 000 ★**, 9 400 forks, 268 open issues, 154 open PRs, 151 releases (latest v0.8.16 z 27/5/2026)
- **Cílovka:** Developer s AI assistant (Copilot, Claude Code, Cursor, Gemini, +30 dalších agentů)

**Workflow (7 stages, oficiální):**

```
1. /speckit.constitution     — Establish project principles (rulebook)
2. /speckit.specify          — Describe product requirements (PRD)
3. /speckit.clarify          — Fill ambiguity (optional but recommended)
4. /speckit.plan             — Generate technical plan
5. (manual review)           — Validate plan
6. /speckit.tasks            — Break into atomic tasks
7. /speckit.implement        — Execute implementation
+  /speckit.analyze          — Cross-artifact validation (drift check)
+  /speckit.checklist        — Quality gates
+  /speckit.taskstoissues    — GitHub issue integration
```

**Claimed benefit:** Replace „big bang" coding with decomposition pipeline (Feature → User Stories
→ Tasks → 1-2 file scoped implementation). „A useful constitution typically captures project scope,
domain context, technology versions, coding standards and repository structure" (Thoughtworks
Tech Radar Vol 33, 11/2025).

**Reálné painpointy (zdroj — Scott Logic, Putting Spec Kit Through Its Paces, 26/11/2025):**

| Metrika | Spec Kit | Tradiční iterativní prompting |
|---|---|---|
| Agent execution (Feature 1) | 33m30s | 8 min |
| Code review | 3.5 h | 15 min |
| Functional testing | included | 9 min |
| Markdown vygenerován | **2 577 řádků** | — |
| Kód vygenerován | **689 řádků** | — |
| Ratio markdown : kód | **3.74 : 1** | — |
| Speed differential | — | **~10× rychlejší** |

> *„For now, the fastest path is still iterative prompting and review, not industrialised
> specification pipelines."* — Scott Logic (11/2025)
>
> *„Drags you right back into the past."* — autor o návratu k waterfall

**Konfirmace z Thoughtworks Tech Radar (Vol 33, 11/2025, Ring: Assess):**

- *„Workflows remain elaborate and opinionated."*
- *„Highly variable behavior depending on task size and type."*
- *„Some generate lengthy specification files that prove hard to review."*
- *„Unclear intended audiences when producing PRDs or user stories."*
- Invokuje Rich Sutton *„bitter lesson"*: *„handcrafting detailed rules for AI ultimately doesn't
  scale."*

### 1.2 Amazon Kiro

- **URL:** `kiro.dev` ([Kiro](https://kiro.dev/))
- **Launch:** mid-2025; re:Invent 2025 DVT209 (12/2025)
- **Pricing:** Free tier 50 interactions/měsíc, Pro $19/měsíc
- **Engine:** Claude Sonnet + Amazon Nova (přes Bedrock)
- **Form-factor:** **Standalone IDE** (vendor lock-in)

**Workflow (3 phases, EARS notation):**

```
Phase 1: Requirements          — Natural language → user stories + acceptance criteria (EARS)
Phase 2: Design                — Technical design (diagrams, schemas)
Phase 3: Tasks                 — Sequence of trackable implementation tasks
Phase X: Hooks                 — Event-driven background automations (save/create/delete file)
```

**Claimed benefit:** *„Bring engineering rigor to agentic development."* Direct response na vibe-coding
loop: *„the vibe coding loop is a symptom of skipping the requirements phase, not a feature"*
([InfoQ 08/2025](https://www.infoq.com/news/2025/08/aws-kiro-spec-driven-agent/)).

**Reálné painpointy:**

| Painpoint | Zdroj | Detail |
|---|---|---|
| Vendor lock-in | OpenAlternative.co, Augment Code 2026 | AWS account + Claude-only models; *„Most plugin ecosystems (JetBrains-native and Neovim) cannot be fully reused inside Kiro's IDE."* |
| Greenfield bias | Martinelli 03/2026 | *„The core assumption remains: you are building something new... A single-line bug fix in a legacy system should not trigger a full spec generation pipeline."* |
| Context limity | Martinelli 03/2026 | *„When existing applications are large, it becomes impractical for LLMs to create specifications without exceeding context limits."* |
| Pricing glitch 12/2025 | InfoWorld | AWS přiznal *„bug"* — tasky inaccurately consumed multiple requests, vyčerpaly dev limity bez varování. |
| Internal mandate 02/2026 | AI CERTs News | 1 500 Amazon inženýrů podepsalo internal forum post žádající přístup k Claude Code (external models *„outperformed Kiro in edge cases like multi-language refactoring"*). |
| Workflow rigidita | Augment Code 2026 | *„Kiro proved the concept but introduced model lock-in, workflow rigidity, and context limitations that undermine the approach at scale."* |
| Excessive overhead na malé úkoly | Böckeler (martinfowler.com) | *„Small bug fix in Kiro generated 4 user stories with 16 acceptance criteria."* |

### 1.3 OpenSpec

- **URL:** `openspec.dev` / `github.com/Fission-AI/OpenSpec` ([repo](https://github.com/Fission-AI/OpenSpec))
- **Licence:** Open source, MIT-like
- **USP vs Spec Kit:** *„Universal, no API keys, no MCP."* Lightweight & portable.

**Workflow (3 stages):**

```
1. Propose    — Describe change → AI produces proposal + specs + design + tasks
2. Apply      — AI implements step-by-step podle task checklistu
3. Archive    — Archive completed changes (audit record)
```

**Claimed benefit:** Each change v separate folder (proposal/specs/design/tasks); *„no rigid phase
gates"* — můžeš updatovat libovolný artefakt anytime.

**Reálné painpointy (zdroj — Incomplete Developer, DEV.to, *„OpenSpec Failed My Experiment"*, 2026):**

| Attempt | Setup | Výsledek |
|---|---|---|
| 1 | OpenSpec + GPT-5.3 Codex | ~2 hodiny + *„lot of tokens"*; UI redesign FAIL, new front-end *„looked almost identical to the original"* |
| 2 | OpenSpec + Copilot + Claude Haiku | *„Still disappointing. More time reviewing tasks. More agent execution cycles."* |
| 3 | Instructions.md (bez SDD) | *„Quickly, minimal token usage, dramatically shorter execution time"* |

> *„The structured Spec-Driven Development workflow introduced a lot of overhead without delivering
> better results."* — autor

### 1.4 BMAD-METHOD

- **URL:** `github.com/bmad-code-org/BMAD-METHOD` ([repo](https://github.com/bmad-code-org/BMAD-METHOD))
- **Licence:** MIT
- **Status (05/2026):** v6 Alpha *„still recommended for new projects"* (Martinelli)

**Workflow (multi-agent, žádní lidé v *„room"*):**

```
Phase 1: Discovery       — Briefs, market research
Phase 2: Planning        — PRDs, architecture (PdM agent + Architect agent)
Phase 3: Execution       — Stories, sprints (Scrum Master + Dev agents)
Phase 4: Verification    — QA, docs (QA + Technical Writer agents)
```

12+ specialized personas (PdM, Architect, Developer, UX, Scrum Master, QA, Technical Writer, …).
*„Party Mode"* = multi-agent v jedné session.

**Claimed benefit:** *„Strict role boundaries... file-based context passing... discrete handoff protocols.
Your project context and quality gates live in the repo, not in someone's chat history."*

**Reálné painpointy (Martinelli 03/2026):**

- *„Steep learning curve, and the agent orchestration adds significant overhead."*
- *„Immature product"* — v6 Alpha v 05/2026 stále *„recommended for new projects"*, ne brownfield.
- *„Limited real-world brownfield evidence despite enterprise claims."*

### 1.5 Tessl Framework

- **Status (09/2025):** Private beta ([Thoughtworks Tech Radar Vol 33](https://www.thoughtworks.com/radar/techniques/spec-driven-development))
- **USP:** *„The specification itself becomes the maintained artifact, rather than the code"* —
  jediný SDD nástroj, který explicitně řeší **bidirectional sync gap** (spec-as-source-of-truth).
- **Riziko:** Pokud se ujme, dělá z kódu derivační artefakt — extrémní forma SDD.

### 1.6 AI Unified Process (AIUP) — Martinelli alternativa

- **URL:** `martinelli.ch/why-spec-driven-development-tools-fail-in-the-enterprise/`
- **Datum:** 29/3/2026
- **Origin:** Pavel Martinelli, enterprise consultant

**Principy:**

```
- Requirements at center (ne direct code generation)
- Agile phases (ne linear pipelines)
- Technology-specific plugins (ne generic templates)
- Explicit brownfield-ready (feature-level adoption, ne whole codebase retrofit)
- Comprehensive testing = primary safety net for AI code generation
```

**Důležitý kontext pro Pflanzer:** Martinelli paper je external validation Pflanzer pozice
(stakeholder alignment, audit trail, cross-fn discipline). AIUP je sourozenec, ne competitor.

### 1.7 SpecOps (DevOps-style spec-driven legacy modernization)

- **Zdroj:** [Civic Innovations](https://civic.io/2025/12/04/proving-out-a-new-approach-to-legacy-system-modernization/), 04/12/2025
- **Princip:** *„Flips the typical approach. Instead of using AI tools to convert code (COBOL → Java),
  SpecOps uses AI to extract institutional knowledge from legacy code into plain-language specs
  that domain experts can verify."*
- **Audit trail:** *„Version-controlled specifications govern all implementations, creating an audit
  trail and enabling proper oversight."*
- **Multi-vendor:** *„Worked across different AI vendors, demonstrating the portability of the methodology."*

**Tohle je use case, kde SDD legitimně vyhrává a Pflanzer NEDĚLÁ.** Detail v § 6.

---

## 2. Typický SDD multi-round cyklus s odhady času

### Konsolidovaná timeline na typické feature (zdroj: Spec Kit metriky Scott Logic, Böckeler, OpenSpec painpointy)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TYPICKÝ SDD CYKLUS                              │
├──────┬──────────────────────────────────┬──────────┬───────────────────┤
│ Kolo │ Fáze                             │ Čas      │ Output            │
├──────┼──────────────────────────────────┼──────────┼───────────────────┤
│  1   │ Constitution / rulebook          │ 30-60m   │ ~300-500 ř. MD    │
│  2   │ Specify (PRD)                    │ 30-90m   │ ~500-800 ř. MD    │
│  3   │ Clarify (resolve ambiguity)      │ 20-60m   │ ~200-400 ř. MD    │
│  4   │ Plan (technical design)          │ 30-90m   │ ~600-1000 ř. MD   │
│  5   │ Manual review + sign-off         │ 30-180m  │ Decision          │
│  6   │ Tasks (decomposition)            │ 15-45m   │ ~300-500 ř. MD    │
│  7   │ Implement (agent execution)      │ 20-45m   │ ~300-700 ř. code  │
│  8   │ Code review (human)              │ 2-4h     │ Feedback          │
│  9   │ Spec ↔ code reconciliation       │ 30-90m   │ Spec updates      │
│ 10+  │ Re-implement po stakeholder change│ Kolo 1-9 znovu             │
└──────┴──────────────────────────────────┴──────────┴───────────────────┘

CELKEM jednorázový průchod: 6-12 h
CELKEM s 1 re-implementation kolem: 10-22 h
CELKEM s 3 re-implementation koly: 24-48 h
```

### Empirické referenční body

| Source | Feature | Total time | Markdown : code ratio |
|---|---|---|---|
| Scott Logic Feature 1 (Circuit Mgmt, 11/2025) | mid-complexity | 33m30s exec + 3.5h review = **~4h pro 689 ř. kódu** | **3.74 : 1** |
| Scott Logic Feature 2 (GPS Geolocation, 11/2025) | low-complexity | 23m30s exec + ~2h review = **~2.5h pro ~300 ř. kódu** | **7.54 : 1** |
| Böckeler Kiro bug fix | single-line bug | 4 user stories + 16 acceptance criteria | extreme overhead |
| OpenSpec Attempt 1 | UI redesign | 2h + many tokens | **failed** (output identický s before) |

### Lost-context cost per round (literature-grounded estimate)

| Kolo | Spec ↔ kód gap (cumulative) | Cohn-style cost multiplier vs Round 1 |
|---|---|---|
| Round 1 | 0-15 % | 1× |
| Round 2 | 10-30 % | 1.5-2× |
| Round 3 | 25-45 % | 2-3× |
| Round 4+ | 35-60 % | 3-5× |

> ⚠ **Disclaimer:** Číselné mapování *„cumulative spec drift × cost multiplier"* je extrapolace
> z Cohn 2005 *Agile Estimating and Planning* (cost-of-change kurva) + Berry & Kamsties 2004
> (ambiguity in NL requirements) + Yan et al. 2025 (9.8-42.1 % code mismatch). Žádná SDD-specifická
> longitudinální studie tuto matici **nevalidovala** k 05/2026. Číslo používej jako **odhad orders
> of magnitude**, ne přesnou metriku.

---

## 3. Re-implementation gap — validace user claim

### User claim (verbatim):
> *„Konkurent tlačí spec-driven: vyrobí app → popíše do specky → pošle do vývoje → tam podle specky
> znovu vznikne produkt, který se bude lišit a znovu pinkat mezi zadavatelem, produktem a vývojem.
> Cyklus se prodlouží."*

### Konkrétní case studies / blog posts dokumentující claim

#### 3.1 Böckeler / Martin Fowler 11/2025 — hallucination re-implementation
**Source:** [martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
> *„The agent ignored the notes that these were descriptions of existing classes, it just took them
> as a new specification and generated them all over again, creating duplicates."*

To je **doslova** user claim — *„podle specky znovu vznikne produkt, který se bude lišit"*. Agent
si přečetl deskripce existing classes jako new spec a vytvořil duplikáty.

#### 3.2 OpenSpec re-redesign failure (incomplete_developer, DEV.to 2026)
2 hodiny + many tokens → *„new front-end looked almost identical to the original"* — re-implementation
se NELIŠÍ od original, ale spotřebovala čas i tokeny. Inverzní variant claim: někdy re-impl je
identical (zbytečná práce), jindy se liší (kontextový drift).

#### 3.3 Scott Logic 11/2025 — bug se objevil v re-implementaci, ne ve spec
> *„A single 'small and very obvious bug' emerged during implementation: a variable (circuitsData)
> wasn't being populated from the datastore in the session form. This required manual chat-based
> correction rather than specification refinement."*

Spec passed review, kód měl bug. **Specifikace nezachytila integration gap.** Human musel spec
obejít přímým chatem (= návrat k vibe-codingu).

#### 3.4 Spec Kit Discussion #152 — *„Evolving specs"*
GitHub discussion komunita systematicky řeší *„jak udržet spec aktuální, když dev udělá ad-hoc
změnu?"* Otevřená diskuse od Q4 2025, k 05/2026 **neuzavřeno**. To je bidirectional sync gap
v praxi.

### Typický počet kol re-implementace

| Source | Min | Typical | Max |
|---|---|---|---|
| Karpathy original (vibe-coding kritika, 02/2025) | 3 | 5-10 | 15 |
| Spec Kit ideal (oficiální dokumentace) | 1 | 1 + clarification | 2 |
| Spec Kit real (Scott Logic 11/2025) | 1 | 2-3 (spec + impl + bug fix) | 4 |
| OpenSpec (Incomplete Developer 2026) | 1 | 2-3 attempts before fallback to Instructions.md | 3 |
| Böckeler Kiro experience | 1 | 2-4 (kvůli non-compliance s instrukcemi) | 5+ |

> *„I frequently saw the agent ultimately not follow all the instructions"* — Böckeler

### Spec staleness window

Z dostupných zdrojů:

- **Augment Code (2026):** *„Static specs face four documented failure modes: they are expensive to maintain,
  cannot capture all implicit context, drift over time as implementations evolve, and do not account
  for software development's iterative nature."*
- **Augment Code (2026):** *„Most spec-driven tools produce static documents that drift from
  implementation within hours."*
- **Thoughtworks Tech Radar Vol 33:** *„Some generate lengthy specification files that prove hard
  to review."* + bitter lesson o nescalování handcraftu pravidel.
- **Kinde 2026:** Spec drift definováno jako *„gaps in the specification widen with direct code
  changes and keep resurfacing because AI generation is non-deterministic."*

**Konkrétní quantification spec drift do production (citováno multiple sources):**

- **9.8 % – 42.1 %** AI-generated code v benchmarks contains vulnerabilities/mismatches (Yan et al. 2025)
- **~40 %** programs generated in security-sensitive contexts contain vulnerabilities (Pearce et al.,
  IEEE S&P 2023)
- **43 CWEs** identified across 3 AI code-gen tools (Fu et al., ACM TOSEM 2025)
- **70 %+** detected vulnerabilities rated BLOCKER severity (Llama 3.2 90B); ~2/3 GPT-4o /
  OpenCoder-8B rated BLOCKER/CRITICAL (SonarQube arXiv 08/2025)
- **110 000+ surviving AI-introduced issues** in production repos do 02/2026 (arXiv 2026 study —
  precise citation lacks identifier v augmentcode source, **flag jako neověřené**)

⚠ **Caveat:** Tato čísla jsou *„AI-generated code"* obecně, ne striktně SDD output. Ale SDD systémy
generují kód přes stejné LLM (Claude/GPT/Gemini), takže rate spec-drift dědí.

---

## 4. SDD failure modes (7 patterns)

### 4.1 Spec staleness
Spec napsaná jednou, nikdy neaktualizovaná. *„If the spec drifts from reality, it becomes worse
than no spec at all — it becomes misleading context."* (Augment Code 2026, BCMS 2026).

**Empirický důkaz:** GitHub Spec Kit Discussion #152 *„Evolving specs"* — komunita systematicky řeší,
k 05/2026 neuzavřeno.

### 4.2 Bidirectional sync gap
Dev udělá ad-hoc change v kódu → spec to nereflektuje. Pouze **Tessl** (private beta) tohle explicitně
řeší přes spec-as-source-of-truth. Spec Kit/Kiro/OpenSpec/BMAD/AIUP mají one-way flow (spec → kód),
ne opak.

> *„Implementation changes flow back into the specification and prevent spec drift"* — Augment Code
> popisuje **living specs** jako řešení, ale to není v žádném z 5 mainstream tools out-of-the-box.

### 4.3 Stakeholder ne-čtení 50-stránkové specky
Spec Kit generuje 2 577 řádků MD pro jedno feature (Scott Logic 11/2025). Žádný non-tech stakeholder
(security, legal, exec) tohle čísti nebude. **Pflanzer's Lufthansa-style insight:** clickable
prototype = shared reference point, kde stakeholdeři **vidí**, ne čtou.

> *„Generating more markdown files to review than it would take to build the feature itself"* — Martinelli

> *„I'd rather review code than all these markdown files"* — Böckeler 11/2025

### 4.4 AI hallucinations v spec → AI hallucinations v impl (compound)
Spec se generuje LLMkem. Pokud LLM hallucinuje v spec, hallucinuje i v impl (oba kroky stejný engine).
Böckeler: agent vzal *„notes describing existing classes"* jako new spec a vytvořil duplikáty —
hallucination v spec → duplicitní impl. 9.8-42.1 % mismatch rate (Yan et al. 2025) **se compoundne
přes dvě LLM volání**.

### 4.5 Re-implementation cost (data-grounded)
- **2 577 ř. MD / 689 ř. kódu** (Scott Logic Feature 1, 11/2025) = 3.74× markdown overhead
- **10× pomalejší** než iterativní prompting (tamtéž)
- **2 hodiny + many tokens** s nulovou změnou (OpenSpec UI redesign attempt)
- **4 user stories + 16 acceptance criteria** pro single-line bug (Böckeler Kiro)

### 4.6 Workflow rigidity vs context limity (large-codebase fail)
Martinelli 03/2026: *„When existing applications are large, it becomes impractical for LLMs to
create specifications without exceeding context limits."*

To je **systematic limitation SDD pro brownfield**. Greenfield ano, legacy ne. Pflanzer to neřeší
o nic líp pro legacy, ale **Pflanzer pro brownfield ani necílí** (default profil = nový feature
v existing produktu, ne refaktoring legacy).

### 4.7 Vendor lock-in / model lock-in
- Kiro = AWS account + Claude-only via Bedrock + standalone IDE
- Spec Kit = Python setup (barrier pro JS-focused teams)
- BMAD = v6 Alpha (immature)
- Tessl = private beta

> *„Kiro proved the concept but introduced model lock-in, workflow rigidity, and context limitations
> that undermine the approach at scale."* — Augment Code 2026

> Internal Amazon situace 02/2026: **1 500 inženýrů** podepsalo internal forum post žádající přístup
> k Claude Code místo Kiro mandate. *„External models outperformed Kiro in edge cases like
> multi-language refactoring."*

---

## 5. Kde SDD legitimně vyhrává nad Pflanzer (poctivost)

Nepokoušej se prodávat Pflanzer pro tyhle use casy — ztratíš důvěryhodnost.

### 5.1 Legacy modernization (COBOL → Java) přes SpecOps
- **Use case:** Mainframe COBOL → cloud Java/Python, 100k+ ř. legacy bez původních devs.
- **Proč SDD vyhrává:** AI extrahuje institutional knowledge z kódu do plain-language specs, které
  domain experts verifikují. Spec se stane source-of-truth pro modernized system.
- **Proč Pflanzer ne:** Pflanzer cílí na **nový feature / nový produkt / nový workflow**, ne na
  reverse-engineering existujícího kódu. 6-7 lidí v room nepřečte 100k ř. COBOL za 3h.
- **Doporučení:** Recommend SpecOps + AIUP. Pflanzer není fit.

### 5.2 Multi-vendor contracts (audit-as-spec)
- **Use case:** Korporát objednává implementaci u 2-3 vendorů paralelně (např. mobile + web + BE),
  potřebuje **vendor-neutral specifikaci** jako kontraktní baseline.
- **Proč SDD vyhrává:** Spec Kit *„constitution" + OpenAPI 3.1 + machine-readable PRD* = stejný
  kontrakt všem vendorům. Audit trail per Tessl.
- **Proč Pflanzer ne:** Pflanzer's *„Decider's call"* je single-org decision. Multi-vendor contract
  vyžaduje externí legally-binding artefakt, ne in-room verbal commitment.
- **Doporučení:** Pflanzer pro **internal alignment phase** (pre-RFP), pak SDD output jako
  contract anchor pro vendory.

### 5.3 Large distributed teams (50+ engineers, geographically distributed)
- **Use case:** Multi-team feature, 5+ pods na 3 kontinentech, async-first culture.
- **Proč SDD vyhrává:** Spec = single source of truth, async-readable, version-controlled, parallel
  team execution bez in-room blocker.
- **Proč Pflanzer ne:** Pflanzer 2-session formát vyžaduje **stejné lidi v room** (i kdyby remote).
  6-7 lidí ≠ 50+. Default profil neškáluje nad ~10 účastníků.
- **Doporučení:** SDD primary, Pflanzer jen pro per-pod alignment (3-5 lidí) jako sub-workflow.

### 5.4 Continuous engineering (mature product, weekly releases)
- **Use case:** Mature SaaS, weekly release cadence, feature stream, žádný cross-fn blocker.
- **Proč SDD vyhrává:** Per-PR spec + Spec Kit `/analyze` cross-artifact validation = lightweight,
  continuous, fits do PR pipeline.
- **Proč Pflanzer ne:** 14-day cadence je overhead pro weekly release rytmus. Pflanzer's value je
  v *„unblock cross-fn rozhodnutí"*, ne v *„guide každý PR"*.

### 5.5 Regulated handoff k externímu auditorovi (post-incident reconstruction)
- **Use case:** Po security incident potřebuješ rekonstruovat *„co měl systém dělat"* vs *„co dělal"*.
- **Proč SDD vyhrává:** Spec = ex-ante artefakt, code = ex-post evidence. Diff je accountability.
- **Proč Pflanzer ne:** Pflanzer Decision Log je in-process, ne ex-post forensic tool. Pflanzer's
  AI Act čl. 14 decision log doplňuje SDD spec, nenahrazuje ho.
- **Doporučení:** Both. Pflanzer Decision Log + SDD spec = complete audit trail.

---

## 6. Kde Pflanzer vyhrává nad SDD

### 6.1 Cross-functional alignment od minuty 0
- **SDD assumption:** Developer + AI agent = primary actor. Stakeholdeři (security, legal, exec,
  CS, UX writer) v eskalačním řetězci.
- **Pflanzer:** Non-tech v room od minuty 0 (P1 protected USP — viz `09-srovnani-existujici-metody.md`
  § *„5 protected diferenciátorů"*).
- **Důsledek:** Pflanzer eliminuje late-stage veto. SDD ho **vyrábí**: security flag v review fázi
  po 4. kole = back to clarify/plan stages = další 2-4h re-impl cycle.

### 6.2 Funkční prototyp od minuty 1 vs 2 577 řádků markdownu
- **SDD output:** 2 577 ř. MD pro 689 ř. kódu (Spec Kit Scott Logic 11/2025). Stakeholder čte spec,
  představuje si výsledek, signs off, dev to implementuje, výsledek se liší od stakeholder mental
  model → další kolo.
- **Pflanzer:** 3 paralelní funkční weby z Session 1 (3h). Stakeholder kliká na real URL, ne čte
  PRD. Lufthansa-style insight: *„clickable vision rather than describe it makes a concrete difference."*
- **Důsledek:** Pflanzer obejde Berry & Kamsties (2004) NL-requirements ambiguity tím, že **specifikace
  neexistuje jako čtený text** — existuje jako klikací artefakt + Decision Log s atribucí.

### 6.3 14-day cadence vs SDD's open-ended cycle
- **SDD:** *„Just iterate the spec."* Bez time-box. Scott Logic dokumentuje 10× pomalejší než
  iterativní prompting; Böckeler dokumentuje 5+ kol non-compliance.
- **Pflanzer:** 2 sessions + 5-7 dní async + reinforcement T+7/30/60. **Hard 14-day default cap.**
- **Důsledec:** Pflanzer's *„corporate stakeholder availability"* (async window) řeší realistic
  capacity. SDD's *„continuous spec iteration"* nereflektuje, že exec má 30 min týdně, ne 30h.

### 6.4 Anti-HiPPO Decider protocol vs SDD's silent escalation
- **SDD:** Pokud spec passes review a dev má pocit, že je špatně, eskalace ad-hoc. Žádný formalizovaný
  protokol.
- **Pflanzer:** Decider votes last. Score závaznosti per role. ADR-0001 Scenario A/B/C eskalační
  protokol. *„Hardest defensible moat"* per workshop methodology expert (May 2026).

### 6.5 Native AI Act čl. 14 / DORA compliance
- **SDD:** Žádný nemá explicit audit trail per AI Act čl. 14. Spec Kit constitution **není** decision
  log s human attribution; je to rulebook.
- **Pflanzer:** Decision Log s human attribution per AI Act čl. 14 + dvoufázový AI Act protokol
  (Fáze A/B/C, ADR-0013) + DORA 7-letá retence.
- **Důsledek:** Martinelli external validation — *„SDD tools fail in the enterprise because they
  miss stakeholder alignment + audit trail."* Tyto critique pointy = Pflanzer's P1+P4 USPs.

### 6.6 Re-implementation gap = neutralized
- **SDD generuje re-impl gap as feature**: app → spec → dev re-impl. Tři instance produktu (mental
  model stakeholder ↔ spec text ↔ implemented code), tři příležitosti k driftu.
- **Pflanzer eliminuje:** Stakeholder vidí prototype → hlasuje → winner code se extrahuje, NE
  re-implementuje. *„Production-ready code, ne handoff dokument."* Per `00-lean-pflanzer.md`:
  *„Winner kód (≥80/100 gate score), exportovatelný do target repu... Vývojáři doladí edge-case
  bugy, deploy."* — žádné kolo *„podle specky znovu vznikne produkt"*.

### 6.7 Pre-flight triage 4 tracks
- **SDD:** No-op. Spec Kit constitution stage je rulebook, ne security/legal/discovery gate.
- **Pflanzer:** 4 paralelní pre-flight tracks (Discovery + Security + Legal + Platform), 48-72h
  pre-read jako MUST gate. Bez 4 podpisů Session 1 neodstartuje.
- **Důsledek:** Pflanzer eliminuje známé SDD failure mode *„security flag v review fázi po 4. kole"*
  tím, že security flagy padají na Pre-flight, ne v review.

---

## 7. Sum tabulka — SDD nástroje vs Pflanzer

| Atribut | Spec Kit | Kiro | OpenSpec | BMAD | Tessl | AIUP | **Pflanzer** |
|---|---|---|---|---|---|---|---|
| Stars / status | 107k★ | proprietary | OSS | OSS | private beta | concept | OSS + Method Charter |
| Workflow stages | 7 + 3 helpery | 3 phases | 3 phases | 4 phases (multi-agent) | 1 (spec-as-source) | agile phases | **2 sessions + async + reinforcement** |
| Cross-fn role v primary session | ❌ | ❌ | ❌ | ❌ (jen AI personas) | ❌ | partial | **✅ 4-7 lidí** |
| Funkční prototyp výstup | ❌ (code from spec) | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 3 weby v 3h** |
| Re-implementation kola typically | 2-4 | 2-5 | 2-3 | unclear | 1 (deterministic claim) | 1-2 | **0 (winner code extracted)** |
| Markdown : code ratio | **3.74-7.54 : 1** | excessive (4 stories/16 ACs pro single line) | high | high | unclear | medium | low (decision log, ne PRD) |
| Audit trail / AI Act čl. 14 | ❌ | ❌ | ❌ | ❌ | partial | ❌ | **✅ native** |
| Anti-HiPPO Decider protokol | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ ADR-0001** |
| Score závaznosti per role | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ unique** |
| Time-to-shippable code (feature) | **10× pomalejší než vibe** | unclear | failed v 2h | unclear | unclear | unclear | **~14 dní default** |
| Brownfield support | weak | weak | medium | weak | unclear | strong | medium |
| Stakeholder ne-tech reading load | **2 577 ř. MD** | excessive | high | high | medium | medium | **prototype-driven (čte UI, ne MD)** |
| Vendor lock-in | open (Python) | **AWS + Claude** | open | open | unclear | open | open |

---

## 8. Strategické důsledky pro Pflanzer marketing v0.4

### 8.1 Anti-SDD framing — co psát na web

Z této research vytahuju 3 sound-bite které lze citovat na website (ověřené):

> **„Spec Kit generuje 2 577 řádků markdownu pro 689 řádků kódu — Pflanzer generuje 3 funkční
> klikací weby v 3 hodinách."** (Scott Logic 11/2025)

> **„AI agent ignoroval poznámky o existujících třídách a vygeneroval je znovu jako nové, vytvořil
> duplikáty."** — Birgitta Böckeler, ThoughtWorks / Martin Fowler 11/2025
>
> **Pflanzer:** Žádné re-implementation kolo. Winner code z Session 1 se **extrahuje**, ne re-impl.

> **„9.8-42.1 % AI-generated code obsahuje vulnerabilities/mismatches"** (Yan et al. 2025).
> **Pflanzer:** Quality gates 0-100 score + production-grade extract per Session 3.

### 8.2 Honest both ways pozicování

**NEpoužívat formulaci:** *„Pflanzer je lepší než Spec Kit."*

**Použít:**

> *„Spec Kit / Kiro / BMAD řeší ‚AI vyrobí lepší kód z lepší speciky'. Pflanzer řeší ‚6 lidí
> z různých oddělení se shodne na funkčním prototypu za 14 dní'. To jsou různé problémy.*
>
> *Pokud máš 50+ distributed devs, brownfield legacy, multi-vendor contract nebo continuous release
> stream — jdeš SDD. Pokud máš cross-fn blokér v korporátu, non-tech stakeholdery, regulatorní
> tlak (AI Act/DORA) a 6-7 lidí, kteří se musí shodnout — jdeš Pflanzer. Často potřebuješ oboje
> v různých fázích."*

### 8.3 Spec-Kit-compatible handoff (P1 z v0.3 synthesis)

Per `04-synthesis-and-positioning.md` § *„P1 — v0.4 SHOULD"*:

> *„4. diferenciátor: Spec-kit-compatible handoff (BMAD-feedable, Kiro-feedable export). Charter
> `tool/templates/` přidat `handoff-spec-kit.md.template`."*

**Tato research validuje, že to dává smysl:** Pflanzer Session 2 + winner code + decision log →
exportovat do Spec Kit constitution + spec format. Pflanzer výstup tak může sloužit jako **vstup**
pro SDD-organized engineering pipeline. Komplement, ne competitor.

### 8.4 P0 action items pro v0.4 z této research

1. **Doplnit `09-srovnani-existujici-metody.md`** o Spec Kit / Kiro / OpenSpec / BMAD entries
   s konkrétními čísly (2 577 ř. MD, 10× pomalejší, 9.8-42.1 % drift).
2. **Website pricing/comparison sekce** — přidat *„vs Spec-driven tools"* tab s 3 sound-bites z § 8.1.
3. **ADR-0019** — *„Vztah k SDD ekosystému + Spec Kit handoff export"* (formalizovat komplementární
   pozici, ne competitive).
4. **Martinelli citation** — paper *„Why Spec-Driven Development Tools Fail in the Enterprise"*
   (29/3/2026) jako *„independent validation of Pflanzer's stakeholder alignment + audit trail USPs."*

---

## 9. Open questions / unverified claims (flag pro další research)

| Claim | Status | Akce |
|---|---|---|
| arXiv 2026 study *„110 000 AI-introduced issues"* | Citováno bez DOI/arXiv ID v augmentcode source | Doohlédnout přes arXiv search 06/2026 |
| Spec drift *„9.8-42.1 %"* range (Yan et al. 2025) | Citováno přes secondary source | Najít primary paper |
| Pearce et al. *„~40 % vulnerabilities"* (IEEE S&P 2023) | Citováno přes secondary | Primary IEEE access |
| Martinelli paper (29/3/2026) | First-hand fetched, OK | — |
| Scott Logic 11/2025 metriky (2 577 / 689) | First-hand fetched, OK | — |
| Böckeler quote (martinfowler.com) | First-hand fetched, OK | — |
| Internal Amazon Kiro mandate (1 500 engineers) | AI CERTs News secondary | Validate via Amazon internal / Bloomberg sources |
| Karpathy 2025 → 2026 *„end of vibe coding era"* admission | Quoted secondary | Najít primary tweet / talk |

---

## 10. Reference (URLs + datum přístupu 2026-05-28)

### Primary SDD tools

- **GitHub Spec Kit** — [github.com/github/spec-kit](https://github.com/github/spec-kit) — 107k★, v0.8.16 (27/5/2026)
- **GitHub Spec Kit docs** — [github.github.com/spec-kit](https://github.github.com/spec-kit/)
- **GitHub Blog launch** — [spec-driven-development-with-ai-get-started](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/) (09/2025)
- **Spec Kit Discussion #152 *„Evolving specs"*** — [github/spec-kit/discussions/152](https://github.com/github/spec-kit/discussions/152) (Q4 2025-otevřeno k 05/2026)
- **Amazon Kiro** — [kiro.dev](https://kiro.dev/) + [kiro.dev/blog/introducing-kiro](https://kiro.dev/blog/introducing-kiro/)
- **AWS re:Invent DVT209 (12/2025)** — [dev.to/kazuya_dev/aws-reinvent-2025-kiro](https://dev.to/kazuya_dev/aws-reinvent-2025-kiro-your-agentic-ide-for-spec-driven-development-dvt209-12gd)
- **OpenSpec** — [openspec.dev](https://openspec.dev/) + [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)
- **BMAD-METHOD** — [github.com/bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)
- **Tessl Framework** — private beta (per Thoughtworks Tech Radar Vol 33)

### Tool critiques / failure mode docs

- **Scott Logic, *„Putting Spec Kit Through Its Paces"* (26/11/2025)** — [blog.scottlogic.com](https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html) — 2 577 ř. MD / 689 ř. kódu, 10× pomalejší
- **Martin Fowler / Birgitta Böckeler, *„Understanding SDD: Kiro, spec-kit, Tessl"*** — [martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) (11/2025) — hallucination duplikáty
- **Martinelli, *„Why SDD Tools Fail in the Enterprise"* (29/3/2026)** — [martinelli.ch](https://martinelli.ch/why-spec-driven-development-tools-fail-in-the-enterprise/) — Kiro/Spec Kit/BMAD enterprise critique + AIUP alternativa
- **Incomplete Developer, *„OpenSpec Failed My Experiment"* (2026)** — [dev.to/incomplete_developer](https://dev.to/incomplete_developer/openspec-spec-driven-development-failed-my-experiment-instructionsmd-was-simpler-and-faster-3a5d) — 2h + many tokens + zero change
- **InfoQ, *„Beyond Vibe Coding: Amazon Introduces Kiro"* (08/2025)** — [infoq.com](https://www.infoq.com/news/2025/08/aws-kiro-spec-driven-agent/)
- **InfoWorld, *„AWS blames bug for Kiro pricing glitch"* (12/2025)** — [infoworld.com](https://www.infoworld.com/article/4042912/aws-blames-bug-for-kiro-pricing-glitch-that-drained-developer-limits.html)
- **AI CERTs News, *„Inside Amazon's Kiro Mandate"* (02/2026)** — [aicerts.ai](https://www.aicerts.ai/news/inside-amazons-kiro-mandate-and-the-future-of-ai-coding/) — 1 500 engineers internal forum post

### Thoughtworks coverage

- **Tech Radar Vol 33 *„Spec-driven development"* (Assess, 05/11/2025)** — [thoughtworks.com/radar/techniques/spec-driven-development](https://www.thoughtworks.com/radar/techniques/spec-driven-development)
- **Tech Radar Vol 33 PDF (11/2025)** — [thoughtworks.com/content/dam/.../tr_technology_radar_vol_33_en.pdf](https://www.thoughtworks.com/content/dam/thoughtworks/documents/radar/2025/11/tr_technology_radar_vol_33_en.pdf)
- **Thoughtworks, *„From vibe coding to context engineering"* (2025 retrospective)** — [thoughtworks.com/en-us/insights/blog/machine-learning-and-ai/vibe-coding-context-engineering-2025-software-development](https://www.thoughtworks.com/en-us/insights/blog/machine-learning-and-ai/vibe-coding-context-engineering-2025-software-development)
- **Thoughtworks Medium, *„Spec-driven development"*** — [thoughtworks.medium.com/spec-driven-development-d85995a81387](https://thoughtworks.medium.com/spec-driven-development-d85995a81387)

### Spec drift / hallucination / re-impl data

- **Augment Code, *„What Is SDD?"*** — [augmentcode.com/guides/what-is-spec-driven-development](https://www.augmentcode.com/guides/what-is-spec-driven-development) — Yan et al. 2025 (9.8-42.1 %), Pearce et al. 2023 (~40 %), Fu et al. ACM TOSEM 2025 (43 CWEs), arXiv 2026 (110 000+ issues)
- **Augment Code, *„Living Specs"*** — [augmentcode.com/guides/living-specs-for-ai-agent-development](https://www.augmentcode.com/guides/living-specs-for-ai-agent-development)
- **Kinde, *„Spec Drift: The Hidden Problem"*** — [kinde.com/learn/.../spec-drift-the-hidden-problem-ai-can-help-fix](https://www.kinde.com/learn/ai-for-software-engineering/ai-devops/spec-drift-the-hidden-problem-ai-can-help-fix/)
- **BCMS, *„Spec-Driven Development: Definitive 2026 Guide"*** — [thebcms.com/blog/spec-driven-development](https://thebcms.com/blog/spec-driven-development)
- **Rushi's blog, *„SDD Technical Deep Dive"*** — [rushis.com](https://www.rushis.com/spec-driven-development-sdd-a-technical-deep-dive-into-the-methodologies-reshaping-ai-assisted-engineering/)

### Legacy modernization / SpecOps

- **Civic Innovations, *„Proving Out New Approach to Legacy"* (04/12/2025)** — [civic.io](https://civic.io/2025/12/04/proving-out-a-new-approach-to-legacy-system-modernization/)

### Comparison tables

- **Augment Code, *„6 Best SDD Tools 2026"*** — [augmentcode.com/tools/best-spec-driven-development-tools](https://www.augmentcode.com/tools/best-spec-driven-development-tools)
- **Augment Code, *„6 Best Kiro Alternatives"*** — [augmentcode.com/tools/best-kiro-alternatives](https://www.augmentcode.com/tools/best-kiro-alternatives)
- **OpenSpec.pro Comparison (Spec Kit vs BMAD vs OpenSpec vs Kiro)** — [openspec.pro/comparison](https://openspec.pro/comparison/)
- **azanello.com, *„GSD vs Spec Kit vs OpenSpec"*** — [azanello.com](https://azanello.com/blog/spec-driven-development-tools-compared)

### Foundational refs (older but relevant)

- **Berry, D.M. & Kamsties, E. (2004), *„Ambiguity in Requirements Specification"*** — [link.springer.com](https://link.springer.com/chapter/10.1007/978-1-4615-0465-8_2)
- **Cohn, M. (2005), *„Agile Estimating and Planning"*** — Robert C. Martin Series, ISBN 0131479415
- **Karpathy, A. (02/2025), original *„vibe coding"* tweet** — známé, primary URL nedohledán via WebSearch k 05/2026

### Pflanzer internal cross-refs

- `docs/methodology/00-lean-pflanzer.md` (default profil 14d / 10 PD)
- `docs/methodology/09-srovnani-existujici-metody.md` (vč. Spec Kit/Kiro/BMAD/OpenSpec entries v workshop comparison)
- `docs/research/competitive/04-synthesis-and-positioning.md` (Martinelli reference, 5 protected USPs)
- `docs/research/competitive/02-vibecoding-methodologies-2026.md` (full AI vibe-coding expert pohled)
- *(Tato research)* `docs/research/spec-driven-vs-pflanzer/01-sdd-mechanika.md`
