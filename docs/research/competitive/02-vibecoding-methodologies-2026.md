# Vibe-coding tools & methodologies — competitive landscape 2026

> Perspective: Senior AI tooling analyst, role „what bundles end-to-end from
> problem to production code, AI in loop, dnes, May 2026?"
> Sister-dokument k `baseline/02-vibecoding-tools-2026.md` (tam tools, tady
> *metodologie a playbooks kolem nich*).

## Verdikt (TL;DR)

**Existuje právě jeden přímý ideologický konkurent Pflanzeru — AWS AI-DLC
(Raja SP, červenec 2025, re:Invent 2025), jehož „Mob Elaboration" ceremonie
sdílí ~70 % DNA s Pflanzer Session 1.** Liší se v třech bodech, které jsou
zároveň Pflanzer USPs: (1) AI-DLC nemá **multi-stakeholder cross-functional
alignment napříč non-tech rolemi** (mob = engineering team: BA/PM, eng, QA,
ops — žádný Security/Legal/A11y/UX writer/CS proxy v místnosti); (2) AI-DLC
nemá **score závaznosti** (cohesive mob = konsensuální dohoda, ne weighted
sign-off s lidskou atribucí); (3) AI-DLC nemá **mezi-session stakeholder
feedback loop** s rolovou agregací (jede „bolts" lineárně, ne dva sessions
s týdenním asyncem).

Druhý semi-konkurent je **BMAD-METHOD** (open source, MIT, GitHub
bmad-code-org), který má **AI personas pro 12+ rolí včetně PM/Architect/QA/SM**
— ale je to **agent orchestration framework, ne workshop methodology**.
Žádní lidé v místnosti, jen agenti hrající role. Komplement, ne competitor.

Třetí kategorie — **spec-driven development** (GitHub Spec Kit v0.8.7, Amazon
Kiro, OpenSpec) — řeší jiný problém: *„AI píše kód podle formálního spec, ne
freeform prompt"*. To je upstream artifact, který Pflanzer mohl konzumovat
(Charter → spec.md → AI agent generuje), ne competitor.

Mainstream **„vibe coding"** se v 2026 ustálil na Karpathyho definici =
*„LLM píše kód z natural language, ty review-uješ output, neviděj diff"* —
**žádný workshop/session aspekt v mainstream definici není.** Pflanzer
používá termín *„společně provibe-koduje"* ve významu *„skupina v místnosti
diriguje AI generátor side-by-side"*, což je **divergence od mainstream
významu**. Pro positioning to znamená: buď Pflanzer udělá clean break
(„toto NENÍ vibe coding") nebo claim („vibe coding 2.0 = cross-functional").
Doporučení v sekci dole.

**Protected Pflanzer USPs k May 2026:**
1. Cross-functional non-tech alignment (Security/Legal/A11y v místnosti) —
   protected; nikdo jiný to neclaimuje.
2. Score závaznosti per role s lidskou atribucí + audit log DORA-grade —
   protected; AI-DLC ani BMAD ani spec-tools nemají.
3. Pre-flight triage 4 paralelní tracks + Charter wizard ex-ante — protected.
4. AI-only feedback deflation (-0.5/1.0) — protected; nobody else even
   thought about this.

**Kopírovatelné v ~6 měsících:**
5. Multi-version A/B/C ze stejného briefu — Cursor Composer 2 už má
   `/best-of-n` (Oct 2025), Replit Agent 3 plánuje. Diferenciátor zmizí
   během 12 měsíců.
6. Mob session formát — AWS to už claimuje pod „Mob Elaboration".
7. Funkční klikací prototyp v session — Bolt v2 (Oct 2025), v0 (Feb 2026
   Git+DB), Lovable 2.0 multiplayer to vše dělají. Pflanzerova hodnota tady
   = *facilitátorský proces*, ne tool.

---

## Per tool / methodology mapping

### 1. AWS AI-DLC (přímý competitor)

| Atribut | AI-DLC | Pflanzer |
|---|---|---|
| **Publikováno** | 31. červenec 2025 (AWS DevOps blog), re:Invent 2025 DVT214 (8. prosinec 2025) | v0.2.1 May 2026 |
| **Author / owner** | Raja SP (Principal SA @ AWS), open-sourced jako `github.com/awslabs/aidlc-workflows` | Tomáš Pflanzer, MIT/CC-BY |
| **Forma** | 3-fázový SDLC + 3 ceremony types (Mob Elaboration, Mob Construction, Mob Testing) + bolts | 2-session workshop + production handoff + reinforcement T+7/30/60/90 |
| **Délka session** | Mob Elaboration ~2-4 h (half-day), Mob Construction continuous během „bolt" cyklu (hours-to-days) | Session 1 3-6 h, Session 2 3 h, total ~10 PD |
| **Kdo v místnosti** | Engineering team: BA/PO/PM, SA/SWE/DevOps, QA, domain specialists. „Taxi team 4-6 lidí" | 18-position role catalog, default 6-7 lidí, audit-grade do 10 + Security/Legal/A11y/UX writer/CS proxy |
| **AI role** | AI navrhuje plan → mob validuje → AI implementuje. „Plan-Execute-Validate" cyklus | AI co-pilot generuje 1-3 varianty v sub-hodinovém cyklu, BE shadow agent paralelně OpenAPI, AI mediuje feedback v Session 2 |
| **Output** | requirements + stories + architecture + code + tests (vše v repu) | 1-3 klikací prototypy + draft OpenAPI + decision package + per-role handoff |
| **Decider model** | „Ceremony leader" per fáze (BA leads Inception, Tech Lead leads Construction) | Decider s tie-breakerem, anti-HiPPO (hlasuje poslední), score závaznosti per role |
| **Mezi-session async** | Žádný — bolt-cycle je continuous mob | 5-7 dní async feedback collection + Discovery Debt Detector |
| **Open source** | Ano — github.com/awslabs/aidlc-workflows | Ano — github.com/pflanzer-method |

**Gap vs Pflanzer:**

1. **„Cohesive team mob = konsensus"** — AI-DLC explicitně staví na premise
   *„everybody offers insights and validation"*. Žádný formal mechanism pro
   *„nesouhlasím a jsem Security, mám veto"*. To je v korporátním kontextu
   killer issue.
2. **No non-tech stakeholders** — Mob v AI-DLC = engineering proxies pro
   business (BA = product management). Pflanzer předpokládá, že
   **zadavatel + 3 non-tech departments + 4 tech rolí** jsou v jedné
   místnosti.
3. **„Bolts" = continuous, ne 2 sessions s týdenním asyncem** — což znamená
   stakeholdeři musí být *full-time committed* na celou délku bolt cyklu.
   Pflanzer model 2 sessions je explicitně designovaný pro korporát, kde
   stakeholder dá ~10 h za dva týdny.
4. **No production code default** — AI-DLC mob construction produkuje kód,
   ale nemá quality gate score 0-100. Pflanzer Session 3 výslovně targetuje
   `gate_score >= 80/100`.
5. **No audit log / DORA / AI Act** — AI-DLC nezmiňuje regulatorní vrstvu.

**Positioning vs Pflanzer:**
*AI-DLC říká „enterprise engineering teams". Pflanzer říká „enterprise
cross-functional rooms (engineering + business + risk + design)".*

**Reference k pozornosti:** Začínají vznikat extensions — *TheBushido
Collective ai-dlc* fork přidává „hat-based workflows" (rolové prompty),
*method-aidlc.web.app* mapuje proti generic PDLC. Komunita pomalu doplňuje
to, co Pflanzer má out-of-the-box.

---

### 2. BMAD-METHOD (semi-competitor, komplement)

| Atribut | BMAD-METHOD |
|---|---|
| **Publikováno** | 2025, aktivní vývoj, GitHub `bmad-code-org/BMAD-METHOD` |
| **License** | MIT |
| **Forma** | Multi-agent orchestration framework s rolovými AI persony („Agent-as-Code" markdown files) |
| **Personas** | 12-19+ specialized agents: Product Manager, Architect, Developer, Scrum Master, UX Designer, QA, Analyst, … |
| **Phases** | 4-phase cycle: Analysis → Planning → Solutioning → Implementation |
| **Source of truth** | Dokumentace (PRD, architecture, user stories), kód = downstream derivative |
| **Lidé** | **Nulová — celé je to agent-on-agent.** Operator = 1 dev orchestruje agenty. |

**Gap vs Pflanzer:**
*BMAD orchestruje role-playing AI agenty pro **single dev**. Pflanzer
orchestruje **lidi v jedné místnosti** s AI co-pilotem.* Opačná škála
spektra. **Pflanzer může BMAD interně použít** jako engine pro paralelní
expert panel agentů (a vlastně to už dělá — `.claude/agents/` má 17 role
expertů, což je v podstatě BMAD-style architektura).

**Positioning vs Pflanzer:** *Pflanzer = workshop. BMAD = engine.
Komplement, ne competitor.* Stojí za to v dokumentaci uvést jako reference
implementation („naše agent layer je BMAD-style multi-persona, viz BMAD pro
generic framework").

---

### 3. Spec-Driven Development family (GitHub Spec Kit / Kiro / OpenSpec)

| Tool | Owner | Forma | Workshop aspekt |
|---|---|---|---|
| GitHub Spec Kit v0.8.7 | GitHub, open source, 93k stars na May 7 2026 | Python CLI, 4 phases: Specify → Plan → Tasks → Implement | Žádný |
| Amazon Kiro | AWS, agentic IDE, build na Bedrock | 3-phase: Requirements → Design → Implementation, generuje requirements.md / design.md / tasks.md s EARS notation | Žádný |
| OpenSpec | open source | Lightweight spec process | Žádný |
| Tessl / Spec Kitty | komunita | Various | Žádný |

**Gap vs Pflanzer:**
*Spec-driven je **pre-code artifact discipline**, ne workshop.* Řeší
problém *„AI generuje šum z volného promptu"* tím, že injektuje formální
spec krok. **Pflanzer Charter wizard je v podstatě spec phase upstream**;
Pflanzer Session 1 prompt input = de-facto spec.

**Positioning vs Pflanzer:** *Komplement upstream.* Pflanzer Charter →
Spec Kit `specify` → Pflanzer Session 1 builders konzumují spec.
Doporučení: v Pflanzer roadmapě zvážit native Spec Kit export
(`/pflanzer-charter` produkuje `spec.md` ve Spec Kit formátu, builders ho
čtou).

**Critique source:** Martinelli, *„Why Spec-Driven Development Tools Fail
in the Enterprise"* (2026) — argumentuje, že Spec Kit/BMAD/Kiro **selhávají
v enterprise** protože **chybí stakeholder alignment vrstva** *před*
spec-fází. **To je literálně Pflanzer claim.** Tento blogpost je
external validation pro Pflanzer thesis.

---

### 4. Vercel v0

| Atribut | v0 |
|---|---|
| **Methodology publikace** | Nemá. Žádný „v0 Team Methodology" whitepaper. |
| **Team features (Feb 2026)** | Git integration, VS Code-style editor, DB connectivity, agentic workflows, Team Templates, Approval Processes, Credit Tracking |
| **Workflow positioning** | *„non-engineers can ship frontend changes through proper Git workflows"* — fokus na **PM/Marketing → PR** workflow, ne cross-functional session |
| **Pricing** | Team $30/seat, Business $100/seat |

**Gap vs Pflanzer:** v0 řeší *„non-tech človek šíruje vlastní změnu"*.
Pflanzer řeší *„non-tech človek souhlasí s tech změnou + commitne to
podpisem"*. Inverzní problém.

---

### 5. Bolt.new / StackBlitz

| Atribut | Bolt |
|---|---|
| **Methodology publikace** | Nemá. Bolt v2 (Oct 2025) je *„enterprise-grade vibe coding"* slogan, ne metoda. |
| **PM playbook** | Existuje *„The PM's Complete Guide to Bolt.new"* (Aakash Gupta, Product Growth), ale je to **tool tutorial**, ne methodology framework. |
| **Workshop posture** | StackBlitz nepořádá team workshop training. |

**Gap vs Pflanzer:** Bolt = tool. Pflanzer = proces. Tool může být builder
v Pflanzer Session 1 (per `02-vibecoding-tools-2026.md` doporučení).

---

### 6. Lovable.dev

| Atribut | Lovable 2.0 |
|---|---|
| **Team features** | Multiplayer (real-time co-edit), Workspaces, Roles (Admin/Member), GitHub branch-per-person workflow |
| **Methodology** | Nemá formal published methodology. Marketing claim: *„designers iterate on mockups while PMs add feedback annotations directly in interface, eliminating Figma→Notion→Slack chains"* |
| **Workshop posture** | Lovable Community má Discord eventy, ne formalized training. |
| **„Professional Vibe Coder" role** | Lazar Jovanovic (Lovable in-house) byl v Feb 2026 v Lenny's Podcast jako *full-time vibe coder*, ne facilitator/methodologist. |

**Gap vs Pflanzer:** Lovable řeší *„continuous async co-edit"*. Pflanzer
řeší *„in-room synchronní decision moment"*. Doplňující se.

---

### 7. Cursor Composer 2 (Oct 29, 2025)

| Atribut | Cursor 2.0 |
|---|---|
| **Multi-agent** | Až 8 agentů paralelně, sandboxed workspaces. `/best-of-n` spustí stejný task přes N modelů |
| **Methodology publikace** | Žádný formal Cursor playbook. Komunita má článek *„Pair Programming with Cursor"* (Colby Palmer, Aug 2025), 25 Cursor Tips (Zoer.ai 2025) — vše tactical, ne methodology |
| **Team posture** | Doporučení v komunitě: *„maintain a playbook of approved prompts (CRUD templates, test-first patterns)"* — tj. ad-hoc per-team |
| **Pair programming claim** | Cursor blog/docs **používá termín *„pair-programming with agents, not replacement of review"*** — closest to AI pair programming methodology v 2026, ale není to formalized doctrine |

**Gap vs Pflanzer:** `/best-of-n` je *engineer-pojetí* multi-version. Pflanzer
multi-version je *stakeholder-pojetí* (3 varianty = 3 různé business-logic
trade-offy, ne 3 různé implementations stejného taskem). Zásadní rozdíl
v sémantice, i když mechanika je podobná.

---

### 8. Claude Code / Anthropic Agent SDK

| Atribut | Claude Code / Agent SDK |
|---|---|
| **Internal Anthropic playbook** | Anthropic publikovala *„How Anthropic teams use Claude Code"* PDF (2026), de-facto methodology share. Klíčové claims: *„majority of code is now written by Claude Code, engineers focus on architecture and orchestration"* |
| **Claude Cowork** | Code with Claude 2026 conference (May 19-22, 2026) — anonsovaná feature umožní *„multiple developers share a single agentic Claude session within the same repository"*. **Toto je nejblíže Pflanzer in-room model.** Stable release status nejasný. |
| **Multi-agent pattern** | Lead agent + sub-agents fan-out pattern doporučovaný v Agent SDK docs |
| **Methodology publikace** | Anthropic PDF + 2026 Agentic Coding Trends Report. Není to step-by-step playbook, je to *„here's what we learned"* doc |

**Gap vs Pflanzer:** Anthropic playbook je *engineering-internal* (jak
Anthropic engineers používají Claude Code). Pflanzer je *cross-functional
corporate*. Claude Cowork by mohl být tool support pro Pflanzer Session 1
když vyjde (sledovat changelog).

---

### 9. GitHub Spark / Copilot Coding Agent

| Atribut | Spark / Coding Agent |
|---|---|
| **Spark** | Public preview Sept 2025 (Copilot Pro+ / Enterprise), full-stack apps z natural language, GitHub Models nativně |
| **Copilot Workspace** | Sunset May 2025, rebuilt jako *„Copilot Coding Agent"* (GA Sept 2025) — agentic, dělá multi-file PR |
| **Methodology** | Žádná formal team methodology. GitHub komunikuje *„AI-native developer experience"* jako kategorii, ne 7-step playbook |
| **Multi-stakeholder workshop** | Žádný — single dev → @mention agent → PR |

**Gap vs Pflanzer:** GitHub vision = *„each dev má AI sparring partnera"*.
Pflanzer vision = *„tým má AI co-pilot v společné místnosti"*. Levels of
collaboration jsou jiné.

---

### 10. Replit Agent 3 (Sept 2025)

| Atribut | Replit Agent 3 |
|---|---|
| **Methodology** | Žádná publikovaná. Marketing emphasis: *„Agent works autonomously for 200 minutes, tests itself, builds other agents"* |
| **Team features** | SCIM provisioning, viewer seats, Collaborative Workspaces s pooled credits, Plan Mode |
| **Workshop posture** | Replit blog *„2025 in Review"* — žádná zmínka o team workshop methodology |

**Gap vs Pflanzer:** Replit = solo agent pro non-dev. Pflanzer = tým + agenti.

---

### 11. Foundation Sprint (Knapp + Zeratsky, „Click" book, Apr 2025)

| Atribut | Foundation Sprint |
|---|---|
| **Author** | Jake Knapp + John Zeratsky, *Click: How to Make What People Want* (Simon & Schuster, 22. duben 2025) |
| **Forma** | 2-day workshop, **pre-Design Sprint** — definuje founding hypothesis |
| **Day 1** | Defining + Differentiating (customer, problem, competitors, what makes us different) |
| **Day 2** | Approaches + Magic Lenses + Founding Hypothesis |
| **AI role** | *„Differentiation remains human work: AI is excellent at prototyping, but only humans can define the radical differentiation"* — explicitně **anti-AI-in-the-room** posture |
| **Output** | Founding Hypothesis = testable statement (žádný kód, žádný prototyp) |

**Gap vs Pflanzer:** Foundation Sprint je *upstream of Pflanzer*. Pflanzer
předpokládá, že problem statement existuje (Charter); Foundation Sprint
generuje problem statement. **Potenciálně Pflanzer V2 — Foundation Sprint
jako pre-step ke Charteru.** ADR-worthy.

**Positioning vs Pflanzer:** Knapp explicitně říká *„AI mění mechaniku, ne
strategii"*. Pflanzer claim je opačný — *„AI mění proces, kdy se strategie
dělá"*. Filozofická opozice, ale ne soutěž (jiné body funnel).

---

### 12. AI Design Sprint (Design Sprint Academy)

| Atribut | AI Design Sprint |
|---|---|
| **Owner** | Design Sprint Academy (Dana Vetan a kol.), komerční training provider |
| **Délka** | 4-5 dní (4-day variant), 2-day variant |
| **Cíl** | Identifikovat AI opportunity → prototype → user test |
| **AI role v session** | *„One person uses AI tools to build a functional prototype end to end"* — single AI operator, ne celý tým |
| **Distinction** | DSA rozlišuje *„AI Design Sprint"* (cíl = AI produkt) vs *„AI-powered Design Sprint"* (DS rychlejší díky AI) |
| **Pricing** | Komerční workshop, ~$2-5k per účastník |

**Gap vs Pflanzer:** AI Design Sprint = klasický DS s AI prototypem.
Pflanzer = nová kategorie. Hlavní rozdíl: AI Design Sprint má **user test
s 5 lidmi v Day 5** (Knapp model), Pflanzer má **stakeholder sign-off
sběr napříč odděleními** (žádný external user test, protože interní
stakeholdery jsou stakeholdery, ne subjekty).

---

### 13. „Enterprise Vibe Coding" trend articles

V 2026 vznikla **kategorie blog content** s názvy jako *„Vibe Coding for
Enterprise"*, *„Red Zone / Green Zone Methodology"*, *„Vibe Coding vs
Spec-Driven Development"*. Examples:

- linesNcircles, *„Vibe Coding for Enterprise: The 2026 Strategy Guide"*
- BettyBlocks, *„Vibe Coding for Enterprises | Best Practices for Corporate IT Teams"*
- HCLTech, *„Vibe Coding: Silent Revolution Reshaping Enterprise Development 2025"*
- prommer.net, *„Vibe Coding vs Spec-Driven Development: Enterprise Guide"*
- enterprisevibecoding.com (samostatný domén)
- vibe-coding-framework.com / *„Vibe Coding Framework"* (Oracle case study)

**Posuzování:** Tohle jsou **marketing pieces od konzultantů/SI/vendor**,
ne publikované akademické nebo open-source metodologie. Žádný z těchto
materiálů nemá:
- Vyčíslený session count + duration
- Role catalog
- Score / sign-off mechanism
- Audit log
- Production gate score

**Jediný strukturovaný framework v té kategorii** je
`vibe-coding-framework.com` (Oracle Application Modernisation case study) —
ale ten není OSS, není veřejně atribuovaný autor, vypadá jako vendor
collateral. Nepředstavuje serious competitor.

**Red Zone / Green Zone** (kreditovaný různým konzultantům) je **užitečný
princip** (AI dělá UI, lidé dělají auth/payment/security logic), ale je to
**heuristika**, ne methodology. Pflanzer by mohl tento jazyk
přijmout v dokumentaci pro filozofickou sekci.

---

### 14. AI Pair Programming methodology (Beck/Fowler-style?)

**Status k May 2026:**

- **Žádná Beck/Fowler kniha o AI pair programming neexistuje.** Pragmatic
  Engineer udělal podcast *„Cycles of disruption in the tech industry"*
  s Beck + Fowler (2025), ale formal methodology kniha ne.
- Bitruvius Roman, *„VIBE CODING: AI Pair-Programming Done Right"* (Kindle
  ebook 2025) — self-published manifesto, žádný uptake v enterprise.
- SAP Press, *„AI-Assisted Coding"* (2025) — tool guide, ne methodology.
- arXiv 2506.04785 (Jun 2025), *„From Developer Pairs to AI Copilots"* —
  academic survey, ne prescriptive framework.

**Martin Fowler 2024 article *„On Pair Programming"*** zůstává jediný
„canonical text", ale **nebyla aktualizovaná pro AI éru**. Mezera v
literatuře.

**Implikace pro Pflanzer:** Můžeš si claim *„první formal cross-functional
AI-augmented workshop methodology s sign-off mechanismem"* obhájit. Není
existing dominant framework, který bys narušoval.

---

### 15. Lenny's Newsletter / Reforge / Maven

- **Lenny Rachitsky** — 2025-2026 publikoval guide *„AI prototyping for
  product managers"*, podcast s Lazar Jovanovic (professional vibe coder
  @ Lovable, Feb 2026), 1000+ respondentů survey *„what tool did you vibe
  code with"*. **Všechno individual-PM-fokusováno, žádný team workshop.**
- **Reforge** — kurzy *„AI for Product Builders"*, *„AI Product Strategy"*,
  *„AI Growth"* (Brian Balfour 4-week, 2025). Cohort learning, nikoli
  workshop methodology pro klient teams.
- **Marily Nika (Maven)** — *„AI PM Bootcamp"* certification. Education,
  ne in-org methodology delivery.
- **Productside / Product School** — *„AI Product Management Certification"*
  kurzy.

**Posuzování:** **Žádný z těchto educational vendors neprodává *team
workshop methodology***. Prodávají *individual upskilling*. To je
fundamentally jiný produkt než Pflanzer. **Komplement, ne competitor.**

---

## Direct competitor list

Po prozkoumání ~15 toolů/methodologií dnes (May 2026) je seznam direct
competitors **velmi krátký**:

| Competitor | Overlap | Threat level | Pflanzer differentiator |
|---|---|---|---|
| **AWS AI-DLC** (Mob Elaboration) | 60-70 % session DNA | **High** | Cross-fn non-tech, score závaznosti, async mezi-session, audit log |
| BMAD-METHOD | 20 % (agent personas overlap se sub-agent layer) | Low | BMAD = engine, Pflanzer = workshop wrapper |
| AI Design Sprint (DSA) | 30 % (cross-fn workshop + AI tools) | Low | DSA = user testing, Pflanzer = stakeholder sign-off; DSA = 4-5 dní, Pflanzer = 2 sessions s týdenním asyncem |
| GitHub Spec Kit | 10 % (Charter ≈ spec) | None | Komplement upstream |
| Vibe Coding Framework (vibe-coding-framework.com) | unclear (closed-source, vendor) | Low | Pflanzer veřejně atribuovaný, OSS, score mechanism |

**Žádný z těchto v plné šíři nesplňuje Pflanzer claim *„multi-person
session + AI generates working code + cross-fn sign-off + production
handoff"*.** AI-DLC je nejblíž, ale chybí mu cross-fn non-tech sloupec.

---

## „Vibe coding" jako kategorie — definice 2026 a kdo ji vlastní

### Stávající definice (May 2026)

- **Karpathy original (Feb 2025):** *„kind of coding where you fully give
  in to the vibes, embrace exponentials, and forget that the code even
  exists. Possible because LLMs are getting too good."* — individual,
  zero-workshop, anti-review posture.
- **Wikipedia (2026):** software dev practice assisted by AI where developer
  describes task in prompt → LLM generates source code automatically.
- **IBM, Daily.dev, Natively, Modern Age Coders:** *„describing what you
  want in plain English → AI writes code → you ship"*.
- **Collins Dictionary:** Word of the Year 2026 candidate, mainstream noun.
- **Mainstream media (TechTarget, IBM, Modern Age Coders):** verb,
  individual dev practice.

### Co v mainstream definici NENÍ

- Workshop / session aspekt
- Multi-person aspekt
- Stakeholder alignment
- Sign-off / score mechanism
- Production handoff

### Co Pflanzer dělá s termínem

README říká: *„společně provibekódují 1-3 funkční prototypy"*. Sémanticky
to **rozšiřuje** Karpathy definici z *„individual člověk + AI"* na
*„skupina lidí + AI"*. **To je divergence od mainstream významu.**

### Tři options pro positioning

**Option A — clean break:** *„Pflanzer není vibe coding. Vibe coding je
individual practice. Pflanzer je AI-augmented alignment workshop, kategorie
nová."* Risky: ztratí SEO outyt. Bezpečnější dlouhodobě.

**Option B — claim extension:** *„Pflanzer = vibe coding 2.0 / Enterprise
Vibe Coding / Cross-Functional Vibe Coding"*. Risky: hraje na hype, který
zítra splaskne (FINRA 2026, vibe coding security crisis = brand contamination).

**Option C — selective use:** Termín *„vibe-coding"* používej **interně v
session 1 builderském workflow** (akcept jsme, jde o ten okamžik
generování), ale **navenek positioning = „cross-functional alignment
workshop"** bez „vibe" v hlavičce. **Doporučení.**

### Kdo termín v 2026 vlastní

Nikdo formálně. Karpathy je creator (a tweetnul *„a lot of people quote
tweeted this as 1 year anniversary"*, distancuje se od ownership).
Komercialization: Lovable, Bolt, Cursor (každý si lepí *„vibe coding"*
label). Acta-Ngiri & Klover.ai claim *„first-mover"* status, ale nikdo to
nepřebral. **Otevřená kategorie, ale rychle se kommodifikuje.**

---

## Anti-Pflanzer critique source

**Martinelli (2026), *„Why Spec-Driven Development Tools Fail in the
Enterprise"*** — kritizuje Spec Kit / BMAD / Kiro za:

1. Předpokládají, že **stakeholder alignment už existuje** před spec fází.
2. Žádný mechanism pro **eskalaci konfliktu** mezi business / risk / dev.
3. Žádný **audit trail** kdo co rozhodl proč.
4. Production gate score chybí — kód se *„assumes works"*.

**Tyto critique pointy jsou literálně Pflanzer USPs.** Citovatelný zdroj
pro positioning.

**Trend Micro (March 2026), *„The Real Risk of Vibecoding"*** —
katalogizuje 35 CVEs z AI-vygenerovaných code v 1 měsíci, 86 % AI-generated
samples má XSS vuln (Georgetown CSET). **Vyjadřuje boundary problem: vibe
coding bez Security gate = breach.** Pflanzer Security-in-room + audit
log addresuje přesně toto.

**FINRA 2026 Annual Regulatory Oversight Report** — explicitně targetuje
gen AI code in financial services. Pflanzer audit-grade overhead
(ADR-0011/0012/0013/0014) addresuje compliance, ale **pouze tehdy, když je
ten overhead použit**. V default profilu ne. Citovat v management 1-pageru
jako *„regulatorní vítr fouká směrem k audit-grade overhead"*.

---

## USP differentiation — protected vs kopírovatelné

### Protected (May 2026)

| USP | Proč nikdo nemá |
|---|---|
| **Non-tech v místnosti** (Security, Legal/DPO, A11y, UX writer, CS proxy) | AI-DLC, BMAD, Cursor — vše tech-only. Není to feature, je to **organizační volba**, která vyžaduje sociální capital, ne tooling. Těžce kopírovatelné. |
| **Score závaznosti per role + AI deflation -0.5** | Žádný jiný framework to nemá. AI deflation je antifragile design, ne random number. Důkaz: published v `docs/methodology/04-session-1.md` + synthesis 03. |
| **Pre-flight triage 4 paralelní tracks** (Discovery + Security + Legal + Platform) | Žádný jiný framework. Hluboká integrace s ne-vibekódovacími disciplines. |
| **Audit log s DORA 7y retention + AI Act Fáze A/B/C protokol** | Spec Kit/Kiro/AI-DLC nemají regulatorní vrstvu. Pflanzer má ji zabalenou jako opt-in upgrade. |
| **Decider hlasuje poslední (anti-HiPPO)** | Knapp DS má Decider, ale hlasuje *kdykoli* a *binárně*. Pflanzer time-ordering hlasu je antifragile detail. |

### Kopírovatelné v 6-12 měsících

| USP | Kdo to zkopíruje |
|---|---|
| **Multi-version A/B/C ze stejného briefu** | Cursor `/best-of-n` už má. Replit, v0, Lovable budou mít do 6 měsíců. Komodita. |
| **Funkční klikací prototyp v session** | Bolt v2, v0 Feb 2026, Lovable 2.0 multiplayer to vše dělají. Komodita. |
| **AI mediated feedback synthesis v S2** | Anthropic Claude Cowork (anonsovaný, stable date nejistý) by mohl dělat real-time multi-stakeholder syntézu. ~12 měsíců. |
| **BE shadow agent generuje OpenAPI** | Spec Kit + Kiro to dělají z opačné strany. Konvergence do 6 měsíců. |
| **Mob session formát** | AI-DLC už claimuje. Etable AWS distribution channel. |

### Strategická implikace

**Pflanzer USP-1 (non-tech v místnosti)** a **USP-2 (score závaznosti
s AI deflation)** jsou **moaty**, ne tooling features. Stojí na
*organizational doctrine*, ne na *code*. Tyto USP jsou ochránitelné
**dokumentací, training, certifikací** — ne softwarovou implementací.

**Implikace pro fáze 2 (tool implementace):**
- Nestavět vlastní vibe-coding engine (komodita, AWS/Cursor/Bolt nás
  přejedou). README aktuálně tuto strategii správně volí (CC default,
  hosted SaaS opt-in).
- **Stavět na facilitator UX, score collection, audit log, ADR generator,
  per-role handoff** — tj. layer **nad** existující tooling, nikoli vedle.
- **Certifikační program** pro facilitátory (3-5 let dopředu) jako moat
  proti AWS AI-DLC commoditization. Knapp Design Sprint Academy je
  precedent — vybudovali $50M+/rok business na training/certification,
  zatímco samotná metodika je v knize za $20.

---

## Reference (URL list)

- AWS AI-DLC: https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/
- AWS AI-DLC adaptive workflows: https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle/
- AI-DLC open source: https://github.com/awslabs/aidlc-workflows
- AI-DLC team practices (Derick Chen): https://www.buildwithdc.co/posts/working-with-ai-dlc-team-structure-and-practices/
- AI-DLC Mob Elaboration skill: https://mcpmarket.com/tools/skills/ai-dlc-mob-elaboration
- AI-DLC critique (Tilsen): https://medium.com/data-science-collective/the-ai-driven-development-lifecycle-ai-dlc-a-critical-yet-hopeful-view-edc966173f2f
- AI-DLC essence (Zenn / Kiakiraki): https://zenn.dev/kiakiraki/articles/437ba4d9441b2b?locale=en
- BMAD-METHOD: https://github.com/bmad-code-org/BMAD-METHOD
- BMAD docs: https://docs.bmad-method.org/
- GitHub Spec Kit deep dive: https://www.morphllm.com/spec-driven-development
- Spec Kit vs Kiro vs BMAD comparison: https://medium.com/@visrow/comprehensive-guide-to-spec-driven-development-kiro-github-spec-kit-and-bmad-method-5d28ff61b9b1
- Why SDD tools fail in enterprise (Martinelli): https://martinelli.ch/why-spec-driven-development-tools-fail-in-the-enterprise/
- Amazon Kiro: https://github.com/kirodotdev/Kiro
- Karpathy original tweet: https://x.com/karpathy/status/1886192184808149383
- Karpathy 1-year retrospective: https://x.com/karpathy/status/2019137879310836075
- Vibe coding semantic history (CodeRabbit): https://www.coderabbit.ai/blog/a-semantic-history-how-the-term-vibe-coding-went-from-a-tweet-to-prod
- What is vibe coding 2026 (Natively): https://natively.dev/articles/what-is-vibe-coding
- Vibe Coding Wikipedia: https://en.wikipedia.org/wiki/Vibe_coding
- IBM on vibe coding: https://www.ibm.com/think/topics/vibe-coding
- Vibe coding security risks (Trend Micro): https://www.trendmicro.com/en_us/research/26/c/the-real-risk-of-vibecoding.html
- Vibe coding enterprise risks (Retool): https://retool.com/blog/vibe-coding-risks
- Vibe coding enterprise (linesNcircles): https://linesncircles.com/Blog/Enterprise/Vibe_Coding_for_Enterprise
- HCLTech enterprise vibe coding: https://www.hcltech.com/trends-and-insights/vibe-coding-silent-revolution-reshaping-enterprise-development-2025
- Vibe Coding Framework (vendor): https://docs.vibe-coding-framework.com/for-enterprises
- Vercel v0 teams: https://v0.app/docs/teams
- v0 team plans blog: https://vercel.com/blog/v0-plans-for-teams
- Bolt.new pricing/features: https://bolt.new/pricing
- Lovable 2.0 launch: https://lovable.dev/blog/lovable-2-0
- Lovable collaboration docs: https://docs.lovable.dev/features/collaboration
- Cursor 2.0 multi-agent (Artezio): https://www.artezio.com/pressroom/blog/revolutionizes-architecture-proprietary/
- Pair Programming with Cursor (Palmer): https://www.colbypalmer.com/blog/pair-programming-with-cursor-part-1
- Anthropic How teams use Claude Code (PDF): https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf
- 2026 Agentic Coding Trends Report (Anthropic): https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf
- Claude Code product: https://www.anthropic.com/product/claude-code
- Code with Claude 2026: https://claude.com/code-with-claude
- Inside Anthropic Dev Conf 2026 (Every): https://every.to/chain-of-thought/inside-anthropic-s-2026-developer-conference
- GitHub Spark: https://github.com/features/spark
- Replit 2025 in review: https://blog.replit.com/2025-replit-in-review
- Replit Agent docs: https://docs.replit.com/core-concepts/agent
- Foundation Sprint (Knapp/Zeratsky): https://thefoundationsprint.com/
- Foundation Sprint Lenny intro: https://www.lennysnewsletter.com/p/introducing-the-foundation-sprint
- Click book: https://www.simonandschuster.com/books/Click/Jake-Knapp/9781668072110
- Design Sprint Academy AI Design Sprint: https://www.designsprint.academy/blog/what-is-an-ai-design-sprint
- AI Design Sprints vs AI-powered: https://www.designsprint.academy/blog/ai-design-sprints-and-ai-powered-design-sprints
- AI Design Sprint Workshop: https://www.designsprint.academy/workshops/ai-design-sprints
- Mob Programming with AI (Crisp): https://blog.crisp.se/2025/06/02/michaelgothe/mob-programming-with-ai-inside-a-high-performing-teams-journey
- Atlassian mobbing with AI: https://www.atlassian.com/blog/atlassian-engineering/mobbing-with-ai
- Reforge courses: https://www.reforge.com/courses
- Lenny vibe coding survey: https://x.com/lennysan/status/1942614966064013723
- Professional Vibe Coder (Lenny x Jovanovic): https://www.lennysnewsletter.com/p/getting-paid-to-vibe-code
- Pragmatic Engineer Beck+Fowler (cycles of disruption): https://newsletter.pragmaticengineer.com/p/cycles-of-disruption-in-the-tech
- From Developer Pairs to AI Copilots (arXiv): https://arxiv.org/pdf/2506.04785

---

## Doporučení pro Pflanzer dokumentaci (akční bullet)

1. **Přidat sekci do `09-srovnani-existujici-metody.md`** s AI-DLC jako
   sloupec v tabulce. Aktuálně tam chybí — bug.
2. **Vytvořit ADR-XXXX *„Vztah k AWS AI-DLC"*** — pozice, kdy doporučit
   AI-DLC místo Pflanzeru (tech-only mob, žádný external stakeholder,
   continuous bolts → AI-DLC; cross-fn s sign-off → Pflanzer).
3. **Vytvořit ADR-XXXX *„Vibe coding terminologie"*** — rozhodnout Option
   A/B/C z výše. Doporučení = C (selective use).
4. **Spec Kit interop** — zvážit `/pflanzer-charter` export do
   `spec.md` formátu pro builder consumption. Roadmap item.
5. **Foundation Sprint jako pre-step** — ADR-worthy: kdy Pflanzer
   předpokládá hotový problem statement, kdy je Foundation Sprint pre-step.
6. **Certifikační program pro facilitátory** — long-term moat builder vs.
   AWS/AI-DLC commodity push. Roadmap 18-24 měsíců.
7. **Citation Martinelli + Trend Micro + FINRA** v management 1-pageru
   (`00-tldr.md`) jako external validation Pflanzer thesis.
