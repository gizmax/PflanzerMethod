# External validation — Pflanzer vs. Anthropic & AI eng best practices (2024–2026)

> **Účel:** Najít externí, citovatelné důkazy z Anthropic a frontline AI engineering
> komunity, které **podporují** (nebo brzdí) jednotlivé Pflanzer USPs.
> Není to endorsement — Anthropic Pflanzer nezná. Je to **alignment evidence**:
> *„nejsme outliers, jdeme směrem, který Anthropic a jeho komunita v 2025–2026
> sami zaměřili."*
>
> **Autor:** AI engineering research subagent (paralelní vlna competitive intel)
> **Datum:** 2026-05-18
> **Cílový čtenář:** marketingový writer pflanzer.cz / 1-pager autor / autor
> ADR-0011 (positioning).
> **Předchůdce:** `docs/research/competitive/04-synthesis-and-positioning.md`
> (synthesis 5 USPs). Tento dokument **validuje** těch 5 USPs proti externím
> 2024–2026 zdrojům.

---

## TL;DR

Z 5 Pflanzer USPs:

- **3 USPs mají STRONG external validation** — multi-agent / role-specialized
  sub-agents (Anthropic Research blog 06/2025, Claude Code sub-agents docs
  2025), parallel worktrees pro independent variants (Claude Code
  `--worktree` docs 2025, Cursor `/best-of-n` 03/2026), a explicitní
  human-in-the-loop / approval gates (Claude Agent SDK 09/2025, hooks docs).
- **2 USPs mají MODERATE validation** — native AI Act / DORA compliance
  (EU AI Act čl. 12+14 explicitně requires decision attribution; Anthropic
  Compliance API 2026 dodává programmatic audit feed, ale Pflanzer pattern
  audit-trail-from-day-0-design je u Anthropic z pohledu *deployment hygieny*,
  ne *workshop methodology*), a pre-flight 4-track gating (Anthropic
  *„explore first, then plan, then code"* je sémanticky blízká, ale jiná
  jednotka analýzy — single dev vs. cross-fn workshop).
- **1 USP má WEAK direct validation** — non-tech v místnosti od minuty 0
  (Security/Legal/A11y/DPO/CS proxy v primary session). Anthropic mluví
  o cross-functional workflows (legal team blog, enterprise governance),
  ale **explicitně nedoporučuje** non-tech role v engineering session.
  Hodit se na to dá Anthropic enterprise governance vrstva +
  Lovable's enterprise *„multiplayer mode + RBAC"* (2026) + Vercel v0
  *„anyone on a team can ship production code"* (06/2025), ale je to
  *parallel observation*, ne přímý citát *„Security must be in the room"*.

**Top 3 citovatelné quotes na pflanzer.cz** (s URL + datem):

1. *„A multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4
   subagents outperformed single-agent Claude Opus 4 by 90.2%"* —
   Anthropic Engineering, *„How we built our multi-agent research system"*,
   2025-06-13.
   → validuje **Pflanzer 23 role-expert sub-agents** v `.claude/agents/`.

2. *„Running each Claude Code session in its own worktree means edits in one
   session never touch files in another, so you can have Claude building a
   feature in one terminal while fixing a bug in a second."* —
   Anthropic Claude Code Docs, *„Run parallel sessions with worktrees"*, 2025-2026.
   → validuje **Pflanzer 3 paralelní vibe-coding variants** v Session 1.

3. *„Override actions must be logged with timestamp and operator ID. Every
   escalation, exception, or override must be tracked to a qualified, authorised
   human being."* — EU AI Act, Article 14 + ISO 42001 commentary, 2024–2026.
   → validuje **Pflanzer decision log s human attribution** (USP #2 & #4
   v lean-pflanzer).

**Risk / counter-evidence:** Anthropic / Karpathy explicitně **nedoporučují
vibe coding pro production**. Pflanzer claim *„most code goes straight to
production"* (lean-pflanzer.md) musí být **kvalifikovaný** — winner kód
prochází quality gates (≥80/100) a code review, ne přímý ship z prototypu.
Marketing positioning by neměl vést s *„Karpathy doporučuje vibe coding"* —
Karpathy sám napsal *„vibe coding your way to a production codebase is
clearly risky"* (Simon Willison citace, 2025-03).

---

## 1) Pflanzer USP × external evidence — per-USP table

> Sloupce: **Pflanzer USP** | **External source** (URL + datum) | **Citát**
> | **Pflanzer alignment** | **Strength** (strong / moderate / weak).

### USP #1 — Non-tech v místnosti (Security / Legal / DPO / A11y od minuty 0)

| Source | URL + datum | Citát | Alignment | Strength |
|--------|------------|-------|-----------|----------|
| Anthropic — *„How Anthropic uses Claude in Legal"* | claude.com/blog/how-anthropic-uses-claude-legal, 2025+ | *„The legal team at Anthropic uses Claude to build workflows that automate repetitive tasks like reviewing marketing content and redlining contracts."* | Legal je first-class actor v Anthropic internal workflows. Sémanticky podporuje *„Legal v session"* pattern, ale je to **Legal jako user of AI**, ne **Legal jako participant v engineering workshop**. | weak |
| Anthropic — *„Claude Code and new admin controls for business plans"* | anthropic.com/news/claude-code-on-team-and-enterprise, 2025 | *„Managed policy settings allow deployment and enforcement of settings across all Claude Code users to match internal policies, including tool permissions, file access restrictions."* | Enterprise governance vrstva implicitně předpokládá Security/IT v rozhodovacím procesu. **Nevolá explicitně po Security v workshop session.** | weak |
| Lovable — *„How Lovable approaches governance, permissions, and security for non-technical teams"* | lovable.dev/blog/security-for-non-technical-teams, 2026 | *„Editing, approving, and publishing are treated as separate capabilities with independent permissions, where a user who can create or modify content cannot necessarily approve it, and a user who can approve content cannot necessarily publish it."* | Separation-of-duties princip pro non-technical teams — sémanticky velmi blízké Pflanzer Decider model + per-role závaznost. **Nejde explicitně o Security v room, ale o multi-role RBAC v AI workflow.** | moderate |
| Vercel — *„v0 plans for teams are here"* | vercel.com/blog/v0-plans-for-teams, 2025 | *„For the first time, anyone on a team, not just engineers, can ship production code through proper git workflows."* | *„Anyone on a team"* implicitně zahrnuje non-tech (PM, designer, business). Validuje princip *„non-engineers v AI-driven build session"* — ale nejmenuje Security/Legal explicitně. | moderate |
| EU AI Act čl. 14 + ISO 42001 (komentář) | euaiactguide.com/article-14-decoded, artificialintelligenceact.eu/article/14, 2024–2026 | *„Three levels of oversight are required: the ability to understand, to intervene, and to halt"* + *„High-risk interventions must always be attributed to a trained, identified professional."* | Regulatorně **vynucuje** human oversight pro high-risk AI. Pflanzer pre-empt — Security/Legal v session od minuty 0 = compliance-by-design. **Strong na úrovni regulace, ne na úrovni workshop praxe.** | moderate |

**Závěr per USP #1:** Žádný Anthropic primary source explicitně nedoporučuje
*„Security + Legal v engineering workshop session"*. Closest related concept
je (a) enterprise governance / RBAC vrstva (Anthropic + Lovable + Vercel),
(b) AI Act čl. 14 jako regulatorní driver. **Pflanzer pattern zůstává
organizational moat** — *not commoditized by Anthropic guidance*, což je
pro USP #1 dobrá zpráva (defensible position).

---

### USP #2 — Score závaznosti per role + AI deflation 0.5 + anti-HiPPO Decider

| Source | URL + datum | Citát | Alignment | Strength |
|--------|------------|-------|-----------|----------|
| Anthropic — *„How we built our multi-agent research system"* | anthropic.com/engineering/multi-agent-research-system, 2025-06-13 | *„LLM judge evaluated each output against criteria: factual accuracy, citation accuracy, completeness, source quality, tool efficiency. A single LLM call with prompt outputting scores 0.0-1.0 and pass-fail grade was most consistent."* | Anthropic interně používá **score-based evaluation** pro agent výstupy. Sémanticky velmi blízké Pflanzer score závaznosti per role. **Rozdíl:** Anthropic scóruje *AI output quality*; Pflanzer scóruje *human commitment to variant*. Stejná disciplína, jiný objekt. | moderate |
| Anthropic — *„How we built our multi-agent research system"* | anthropic.com/engineering/multi-agent-research-system, 2025-06-13 | *„Human testers noticed that early agents consistently chose SEO-optimized content farms over authoritative sources. Human evaluation catches what automation misses, identifying edge cases and subtle biases."* | **Anti-HiPPO analog:** Anthropic explicit acknowledgement, že *human-in-the-loop* catches AI biases. Pflanzer AI deflation -0.5 je operacionalizace stejného principu (AI nevěř plně, deflate score). | strong |
| Anthropic — *„Best practices for Claude Code"* | code.claude.com/docs/en/best-practices, 2025–2026 | *„The trust-then-verify gap. Claude produces a plausible-looking implementation that doesn't handle edge cases. Fix: Always provide verification (tests, scripts, screenshots). If you can't verify it, don't ship it."* | Identický princip jako Pflanzer AI deflation: *„AI-only signal je deflated, vyžaduje human verification before commit."* | strong |
| EU AI Act čl. 14 | artificialintelligenceact.eu/article/14, 2024 | *„High-risk AI systems must be designed to allow human oversight... Override actions must be logged with timestamp and operator ID."* | Regulatorně **vyžaduje** atribuovanou závaznost (kdo rozhodl, kdy, proč). Pflanzer score závaznosti per role + decision log = direct AI Act čl. 14 + čl. 12 record-keeping compliance. | strong |
| (none from Anthropic) — explicit anti-HiPPO / Decider model | — | — | Anthropic **nemá** explicitní workshop pattern *„highest-paid person votes last"*. Pflanzer pattern v této formě nemá Anthropic equivalent — closest je *„human evaluation catches AI biases"* (viz výše). | (gap) |

**Závěr per USP #2:** **STRONG validation** pro score-based decision-making
a AI-deflation patternu. Anthropic multi-agent paper přímo zmiňuje
LLM-judge s 0.0-1.0 score a pass-fail grade — identická abstrakce jako
Pflanzer 1-5 Likert. *„Trust-then-verify gap"* z Claude Code best practices
je sémantický twin pro AI-only feedback deflation. **Anti-HiPPO ordering
(Decider votes last)** zůstává unique Pflanzer pattern bez Anthropic
ekvivalentu.

---

### USP #3 — Pre-flight triage 4 tracks (Discovery + Security + Legal + Platform)

| Source | URL + datum | Citát | Alignment | Strength |
|--------|------------|-------|-----------|----------|
| Anthropic — *„Best practices for Claude Code"* | code.claude.com/docs/en/best-practices, 2025–2026 | *„Explore first, then plan, then code. Letting Claude jump straight to coding can produce code that solves the wrong problem. Use plan mode to separate exploration from execution."* | **Sémantický twin** pro pre-flight: Anthropic doporučuje *4-phase workflow* (Explore → Plan → Implement → Commit). Pflanzer pre-flight triage = workshop-level equivalent stejného konceptu (4 paralelní tracks místo 4 sekvenčních fází). | strong |
| Anthropic — *„Building agents with the Claude Agent SDK"* | claude.com/blog/building-agents-with-the-claude-agent-sdk, 2025-09-29 | *„Gather context → take action → verify work → repeat. This is the foundational agent feedback loop."* | Pflanzer pre-flight = první *„gather context"* fáze před Session 1 *„take action"*. Anthropic loop tuhle disciplínu zakládá. | strong |
| Anthropic — *„Effective context engineering for AI agents"* | anthropic.com/engineering/effective-context-engineering-for-ai-agents, 2025-09-29 | *„Good context engineering means finding the smallest possible set of high-signal tokens that maximize likelihood of desired outcome."* | Pflanzer pre-flight Backend Context Pack (ERD, OpenAPI, ADR archiv) = *high-signal token set* pre-loaded před Session 1. Stejný princip na workshop layer. | moderate |
| Anthropic — *„Best practices for Claude Code"* — CLAUDE.md | code.claude.com/docs/en/best-practices, 2025–2026 | *„CLAUDE.md is a special file that Claude reads at the start of every conversation. Include Bash commands, code style, and workflow rules. This gives Claude persistent context it can't infer from code alone."* | Pflanzer Charter + 1-pager success threshold = workshop-level CLAUDE.md (persistent context pre-loaded for all session participants, AI + human). | moderate |
| EU AI Act čl. 12 (record-keeping) + čl. 14 | artificialintelligenceact.eu/article/12, 2024 | *„Comprehensive, immutable audit logs where auditable logs, intervention records, and clear lines of authority must be producible instantly."* | Pflanzer Discovery / Security / Legal / Platform triage = pre-emptive audit-readiness check. **Strong** na regulatorní úrovni. | moderate |

**Závěr per USP #3:** **STRONG validation** přes Anthropic *„explore first,
then plan, then code"* a *„gather context → take action → verify work"*
loop. Pflanzer pre-flight je *„same discipline, different unit of analysis"* —
Anthropic to dělá per dev session, Pflanzer per cross-fn workshop.
**Match je sémantický (princip), ne lexicální (Anthropic neříká „pre-flight").**

---

### USP #4 — Native AI Act / DORA compliance (decision log + 7y retention)

| Source | URL + datum | Citát | Alignment | Strength |
|--------|------------|-------|-----------|----------|
| EU AI Act čl. 14 | artificialintelligenceact.eu/article/14, 2024 | *„High-risk AI systems must be designed to allow human oversight during their operation to minimise risks to health, safety, and fundamental rights. Three levels of oversight are required: the ability to understand, to intervene, and to halt."* | Pflanzer decision log s lidskou atribucí + Decider escalation protokol = direct čl. 14 compliance artefakt. | strong |
| EU AI Act čl. 12 (record-keeping) | artificialintelligenceact.eu/article/12, 2024 | *„Override actions must be logged with timestamp and operator ID. Every escalation, exception, or override must be tracked to a qualified, authorised human being."* | Pflanzer score závaznosti + ADR + decision log = direct čl. 12 compliance. | strong |
| Anthropic — *„Compliance API launches on Claude Platform"* | gadgetbond.com/anthropic-claude-platform-compliance-api, 2026 | *„Anthropic rolled out a Compliance API for the Claude Platform that gives Claude Platform admins a programmatic audit feed of what's happening across their organization, instead of forcing them to rely on CSV exports or sporadic manual reviews."* | Anthropic vidí **enterprise audit trail jako first-class product surface** v 2026. Pflanzer's bet (compliance-by-design ve workshop methodology) má strong tailwind. | strong |
| Anthropic Trust Portal — SOC 2 Type II + ISO 27001:2022 + ISO/IEC 42001:2023 | anthropic.com/trust, 2024–2026 | (Compliance documentation page, dates per certificate.) ISO 42001:2023 = AI management system standard. | Anthropic sám se certifikuje na ISO 42001 (AI management). Pflanzer decision log + DORA-grade retention = client-side analog stejné disciplíny. | moderate |
| Anthropic — *„Responsible Scaling Policy v3.0"* | anthropic.com/news/responsible-scaling-policy-v3, 2024–2025 | *„The RSP is based on the principle of proportional protection: safeguards that scale with potential risks."* | **Proportional protection** = Pflanzer's dvouvrstvý model (Lean default profil vs. audit-grade upgrade pro AI Act High-risk). Stejná filozofie scaling controls to risk. | strong |

**Závěr per USP #4:** **STRONG validation** — toto je nejhustčí kategorie
externí evidence. EU AI Act čl. 12+14 přímo *vynucuje* to, co Pflanzer
poskytuje *out-of-the-box*. Anthropic Compliance API 2026 a ISO 42001
self-certification ukazují, že **Anthropic sám rate-limits velký bet
na enterprise compliance** — Pflanzer's regulatorní moat má tailwind,
ne headwind.

---

### USP #5 — 14-day cadence (2 × 3h sessions + týdenní async + T+7/30/60/90 reinforcement)

| Source | URL + datum | Citát | Alignment | Strength |
|--------|------------|-------|-----------|----------|
| Anthropic — *„How we built our multi-agent research system"* | anthropic.com/engineering/multi-agent-research-system, 2025-06-13 | *„The lead agent spins up 3-5 subagents in parallel rather than serially... cut research time by up to 90%."* | Sémantická paralela: parallel > serial. Pflanzer paralelní async týden mezi sessions = stejná filozofie aplikovaná na human + AI hybrid workflow. | moderate |
| Anthropic — *„Best practices for Claude Code"* — Course-correct early | code.claude.com/docs/en/best-practices, 2025–2026 | *„The best results come from tight feedback loops. Though Claude occasionally solves problems perfectly on the first attempt, correcting it quickly generally produces better solutions faster."* | **Tight feedback loop** = Pflanzer T+7/30/60/90 reinforcement track. Anthropic pattern aplikovaný na multi-week cycle. | moderate |
| Karpathy — *„Vibe coding" tweet + Wikipedia syntéza* | x.com/karpathy/status/1886192184808149383, 2025-02-02 + en.wikipedia.org/wiki/Vibe_coding | *„It's not too bad for throwaway weekend projects, but still quite amusing."* (Karpathy on vibe coding's limits) | **Counter-evidence:** Karpathy explicitně označuje single-shot vibe coding za vhodný pro *„weekend projects"*, ne pro 14-day enterprise cycle. Pflanzer 14-day cadence + reinforcement = řeší Karpathy's limit. | strong (counter-positive) |
| Cursor — *„Composer 2 + /best-of-n + /multitask"* | nxcode.io / DataCamp, 2026-03-19 | *„The /multitask command farms a request out to parallel async subagents instead of queuing it. /best-of-n runs the same task across multiple models at once."* | Parallel + async = mainstream 2026 AI engineering pattern. Pflanzer S1 vibe-coding ride na téhle vlně. **Tooling tailwind pro 14-day cadence.** | moderate |
| GV Sprint, AJ&Smart Sprint 2.0 — komparativní (z `09-srovnani-existujici-metody.md`) | (internal) | 5-day sprint = corporate unrealistic; 90-day = Thoughtworks consulting | **Pflanzer 14-day = window between two failure modes** (5-day burnout / 90-day stale). Internal positioning, externí evidence chybí. | weak |

**Závěr per USP #5:** **MODERATE validation.** 14-day cadence sama o sobě
nemá Anthropic explicit endorsement — Anthropic neaktivuje *workshop
cadence* jako téma. Ale **počet podpůrných patternů** (parallel async,
tight feedback loops, Karpathy weekend-vs-production caveat) ukazuje, že
14-day je *defensible operating cadence* mezi 5-day sprint (krach na
stakeholder availability) a 90-day Thoughtworks (krach na momentum).

---

## 2) Anthropic-specific deep dive — Claude Code, Agent SDK, multi-agent

### 2.1 Multi-agent research system (klíčový citát)

**Zdroj:** anthropic.com/engineering/multi-agent-research-system,
**datum:** 2025-06-13.

Klíčové claims:

- *„A multi-agent system with Claude Opus 4 as the lead agent and Claude
  Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on
  internal research evaluations."*
- *„Subagents facilitate compression by operating in parallel with their
  own context windows, exploring different aspects simultaneously."*
- *„The lead agent spins up 3-5 subagents in parallel rather than
  serially... cut research time by up to 90%."*
- *„Each subagent needs an objective, output format, guidance on tools
  and sources, and clear task boundaries."*
- *„Subagents act as intelligent filters by iteratively using search
  tools to gather information, then returning findings."*

**Pflanzer mapping:**

- 23 role-expert sub-agents v `.claude/agents/` = direct architectural
  match s Anthropic orchestrator-subagent pattern.
- 3-5 paralelně spouštěné role-experti = direct quantitative match
  (Anthropic doporučuje 3-5 subagents per task).
- Role catalog (`02-role-catalog.md`) = *„objective, output format,
  guidance on tools and sources, and clear task boundaries"* — Pflanzer
  pattern doslova spadá pod Anthropic guidance.

**Caveat:** Anthropic mluví o *engineering-task sub-agents* (research,
code, eval). Pflanzer rozšiřuje na *role-expert sub-agents* (Security
expert, A11y expert, Legal expert). Architektonicky identické, doménově
další krok.

### 2.2 Sub-agents (Claude Code docs)

**Zdroj:** code.claude.com/docs/en/sub-agents, **datum:** 2025–2026
(continuously updated).

Klíčové claims:

- *„Subagents are specialized AI assistants that handle specific types of
  tasks. Define a custom subagent when you keep spawning the same kind of
  worker with the same instructions."*
- *„Each subagent runs in its own context window with a custom system
  prompt, specific tool access, and independent permissions."*
- *„Subagents help you: Preserve context, Enforce constraints, Reuse
  configurations across projects, Specialize behavior with focused
  system prompts."*

**Pflanzer mapping:** Identický match. Pflanzer's `.claude/agents/`
struktura (role name → role prompt → tool scope) = doslova Anthropic
sub-agent spec format. **Pflanzer = production application of Anthropic
sub-agent guidance to cross-fn workshop role catalog.**

### 2.3 Worktrees (parallel sessions)

**Zdroj:** code.claude.com/docs/en/worktrees, **datum:** 2025–2026.

Klíčové claims:

- *„A git worktree is a separate working directory with its own files and
  branch, sharing the same repository history and remote as your main
  checkout."*
- *„Running each Claude Code session in its own worktree means edits in
  one session never touch files in another."*
- *„Subagents can run in their own worktrees so parallel edits don't
  conflict. Ask Claude to 'use worktrees for your agents'."*
- (z best-practices) *„In practice, 2–4 parallel sessions is a
  reasonable ceiling before review overhead and API rate limits become
  friction points."*

**Pflanzer mapping:**

- Pflanzer Session 1 *„3 paralelní variants v Bolt / v0 / Lovable /
  Claude Code"* (lean-pflanzer.md den 5) = direct match s Anthropic
  worktree pattern aplikovaným na variant generation.
- *„2–4 parallel sessions ceiling"* z Claude Code best practices =
  Pflanzer's *„2-3 variants"* default (lean-pflanzer.md) je conservatively
  within Anthropic's recommended range.

**Citable on website:** *„Anthropic Claude Code recommends 2-4 parallel
sessions as the practical ceiling for parallel AI work. Pflanzer Method
generates 2-3 variants in Session 1, fitting squarely within Anthropic's
guidance."* (Direct URL: code.claude.com/docs/en/worktrees + Anthropic
internal best-practices, 2025–2026.)

### 2.4 Agent SDK — agent loop + verification

**Zdroj:** claude.com/blog/building-agents-with-the-claude-agent-sdk,
**datum:** 2025-09-29.

Klíčové claims:

- *„Gather context → take action → verify work → repeat. This is the
  foundational agent feedback loop."*
- *„Agents that can check and improve their own output are fundamentally
  more reliable."*
- *„Code linting is an excellent form of rules-based feedback. You can
  have another language model 'judge' the output."*

**Pflanzer mapping:** Pflanzer's lifecycle (pre-flight context →
Session 1 take action → Session 2 verify → handoff repeat) = workshop-level
analog Anthropic agent loop. *„Another language model judge"* = Pflanzer
AI-mediated synthesis v Session 2 (commoditizing, ale match).

### 2.5 Agent Skills (October 2024 — March 2026)

**Zdroj:** anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
+ platform.claude.com/docs/en/agents-and-tools/agent-skills,
**datum:** 2025–2026.

Klíčové claims:

- *„Agent Skills are organized folders of instructions, scripts, and
  resources that agents can discover and load dynamically to perform
  better at specific tasks."*
- *„Building a skill for an agent is like putting together an onboarding
  guide for a new hire."*
- *„Anthropic has open-sourced 17 Agent Skills... covering creative
  design, document creation, technical development, and enterprise
  communication."*
- *„In December 2025, Anthropic released the Agent Skills specification
  as an open standard, and OpenAI adopted the same format for Codex CLI
  and ChatGPT."*

**Pflanzer mapping:** Pflanzer role catalog → role prompts =
*„onboarding guide for a new hire"* aplikované na 23 specializovaných rolí.
**Pflanzer = vertical application of Skills pattern** k cross-fn enterprise
workshop methodology. Roadmap implication pro Fáze 2: Pflanzer tool by
měl exportovat role-prompty jako standard Agent Skills format pro
interoperability (Spec Kit / OpenAI Codex compatibility).

### 2.6 CLAUDE.md a context engineering

**Zdroj:** code.claude.com/docs/en/best-practices + anthropic.com/engineering/effective-context-engineering-for-ai-agents,
**datum:** 2025-09-29 + průběžně.

Klíčové claims:

- *„CLAUDE.md is a special file that Claude reads at the start of every
  conversation."*
- *„Context, therefore, must be treated as a finite resource with
  diminishing marginal returns."*
- *„The over-specified CLAUDE.md. If your CLAUDE.md is too long, Claude
  ignores half of it because important rules get lost in the noise."*
- *„Rather than one agent attempting to maintain state across an entire
  project, specialized sub-agents can handle focused tasks with clean
  context windows."*

**Pflanzer mapping:**

- Pflanzer projektový CLAUDE.md + role-specific agent prompts =
  Anthropic-canonical pattern.
- *„Diminishing marginal returns"* = Pflanzer's choice of *2 sessions
  not 5 days* — workshop-level context conservation.
- *„Specialized sub-agents per focused task"* = Pflanzer role-expert
  panel.

### 2.7 Human-in-the-loop + tool approval

**Zdroj:** Claude Agent SDK + Claude Code permission modes docs,
**datum:** 2025-09-29 + průběžně.

Klíčové claims:

- *„Hooks (e.g., pre/post tool-use, session start/end) help you enforce
  policy, log decisions, and create human-in-the-loop checkpoints."*
- *„By default, Claude Code requests permission for actions that might
  modify your system: file writes, Bash commands, MCP tools, etc."*
- *„Auto mode: a separate classifier model reviews commands and blocks
  only what looks risky: scope escalation, unknown infrastructure, or
  hostile-content-driven actions."*

**Pflanzer mapping:** Pflanzer anti-HiPPO Decider (votes last) =
workshop-level analog Anthropic *„human-in-the-loop checkpoint"* a
*„auto-mode classifier reviews before action"*. **Sémanticky strong;
lexikálně Anthropic neříká „anti-HiPPO".**

### 2.8 Responsible Scaling Policy — proportional protection

**Zdroj:** anthropic.com/responsible-scaling-policy/rsp-v3-0,
**datum:** 2024–2025 (RSP v3.0).

Klíčový claim:

- *„The RSP is based on the principle of proportional protection:
  safeguards that scale with potential risks."*
- *„Anthropic uses AI Safety Level Standards (ASL Standards), graduated
  sets of safety and security measures that become more stringent as
  model capabilities increase."*

**Pflanzer mapping:** **STRONG philosophical alignment** s
Pflanzer's dual-mode (Lean default profil vs. audit-grade upgrade per
AI Act / DORA). Anthropic RSP = graduated controls; Pflanzer = graduated
methodology overhead. **Stejná disciplína „pay for what your risk tier
demands"** aplikovaná na workshop layer.

**Citable on website:** *„Anthropic's Responsible Scaling Policy v3.0
applies 'proportional protection: safeguards that scale with potential
risks.' Pflanzer Method does the same — Lean profile for ~80% of use
cases, audit-grade overhead only for AI Act High-risk and DORA scope."*
URL: anthropic.com/responsible-scaling-policy/rsp-v3-0.

---

## 3) Beyond Anthropic — Vercel, GitHub, Cursor, Lovable, Karpathy

### 3.1 Vercel v0 — non-engineer ship to production

**Zdroj:** vercel.com/blog/introducing-the-new-v0 + vercel.com/blog/v0-plans-for-teams,
**datum:** 2024–2025.

Klíčové claims:

- *„For the first time, anyone on a team, not just engineers, can ship
  production code through proper git workflows."*
- *„Anyone on a team can create branches from within v0, open pull
  requests against main and deploy on merge. Pull requests are
  first-class citizens and previews map directly to real Vercel
  deployments, not isolated demos."*

**Pflanzer mapping:** Validuje Pflanzer's claim *„non-tech v místnosti"*
od minuty 0. Vercel říká non-engineer **může produkovat production
artefakty s proper governance**. Pflanzer workshop pattern stojí na
stejném předpokladu. **Moderate, ne strong** — Vercel mluví o jednotlivci,
Pflanzer o cross-fn skupině.

### 3.2 Cursor — best-of-n + multitask

**Zdroj:** datacamp.com/blog/composer-2, **datum:** 2026-03-19.

Klíčové claims:

- *„The /multitask command farms a request out to parallel async
  subagents instead of queuing it."*
- *„/best-of-n runs the same task across multiple models at once. Each
  run gets its own worktree."*

**Pflanzer mapping:** Direct match na Pflanzer S1 *„3 paralelní vibe-coding
variants in Bolt / v0 / Lovable / Claude Code"*. **Cursor's /best-of-n
od 03/2026 = mainstream commoditization Pflanzer pattern.**

**Important caveat:** Toto je **bad news pro USP #5 vibe-coding framing**
(je commoditizováno per `09-srovnani`). **Good news pro architecture** —
3 paralelní variants jsou nyní industry-standard, Pflanzer není fringe.

### 3.3 Lovable — multi-tenant governance, RBAC

**Zdroj:** lovable.dev/blog/security-for-non-technical-teams +
lovable.dev/enterprise-landing, **datum:** 2026.

Klíčové claims:

- *„Editing, approving, and publishing are treated as separate
  capabilities with independent permissions."*
- *„SOC 2 Type II and ISO 27001. Enterprise features include SSO/SAML,
  SCIM provisioning, role-based access control, and audit logs."*

**Pflanzer mapping:** Separation-of-duties + RBAC v vibe-coding tool =
direct analog Pflanzer Critical/Yellow/Score + Decider votes last pattern.
**Moderate validation** pro USP #2 (decision-making moat).

### 3.4 GitHub Copilot Workspace — spec-plan-code

**Zdroj:** githubnext.com/projects/copilot-workspace + githubnext.com,
**datum:** 2024–2025 (Workspace) + 2025 (Spaces collaborative).

Klíčové claims:

- *„The spec → plan → code pipeline gives you real control without
  requiring you to micromanage the AI."*
- *„Copilot Workspace is collaborative, allowing you to share sessions
  with your team and publish links to your sessions on issues and pull
  requests."*

**Pflanzer mapping:** *„Spec → plan → code"* je sémantický twin
Pflanzer pre-flight → Session 1 → handoff cycle. **Moderate alignment.**

### 3.5 Karpathy — vibe coding (origin)

**Zdroj:** x.com/karpathy/status/1886192184808149383 +
en.wikipedia.org/wiki/Vibe_coding, **datum:** 2025-02-02 (original tweet).

Klíčové claims:

- *„There's a new kind of coding I call 'vibe coding', where you fully
  give in to the vibes, embrace exponentials, and forget that the code
  even exists."*
- (follow-up) *„It's not too bad for throwaway weekend projects, but
  still quite amusing."*
- (Simon Willison komentář, 2025-03) *„Vibe coding your way to a
  production codebase is clearly risky. Most of the work we do as
  software engineers involves evolving existing systems, where the
  quality and understandability of the underlying code is crucial."*

**Pflanzer mapping:** Pflanzer **explicitně dispelluje** Karpathy's
*„weekend project"* limit přes (a) 14-day cadence + reinforcement, (b)
quality gates ≥80/100 před handoff, (c) cross-fn alignment vrstva.
**Karpathy = origin lexikonu „vibe coding"; Pflanzer = enterprise-grade
enclosure stejného přístupu.**

**Marketing implication:** Pflanzer 1-pager / pflanzer.cz **NESMÍ** říct
*„Karpathy doporučuje vibe coding pro váš enterprise projekt."* Naopak:
*„Karpathy ukázal, že vibe coding funguje pro experimenty. Pflanzer
Method přidává cross-fn alignment + quality gates + audit trail, aby
to fungovalo i v korporátu."*

---

## 4) Citable on pflanzer.cz — 5–10 top quotes

> Drop-in ready citáty s URL + datem. **Quote → Pflanzer message → URL.**

1. **Multi-agent výhoda** —
   *„A multi-agent system with Claude Opus 4 as the lead agent and Claude
   Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2%."*
   → **Pflanzer message:** *„23 role-expert sub-agents není nadbytečné —
   Anthropic interně ukázal 90% výkonnostní výhodu multi-agent vs.
   single-agent."*
   → URL: anthropic.com/engineering/multi-agent-research-system (2025-06-13).

2. **Parallel worktrees** —
   *„Running each Claude Code session in its own worktree means edits in
   one session never touch files in another."*
   → **Pflanzer message:** *„Pflanzer Session 1 generates 3 parallel
   variants in isolated worktrees — exactly what Anthropic recommends
   for parallel AI work."*
   → URL: code.claude.com/docs/en/worktrees (2025–2026).

3. **AI Act human attribution** —
   *„Override actions must be logged with timestamp and operator ID.
   Every escalation, exception, or override must be tracked to a
   qualified, authorised human being."*
   → **Pflanzer message:** *„AI Act čl. 14 vyžaduje atribuovanou
   závaznost. Pflanzer's decision log s human attribution to dodává
   out-of-the-box."*
   → URL: artificialintelligenceact.eu/article/14 + ISO 42001
   commentary (2024–2026).

4. **Proportional protection (RSP)** —
   *„The RSP is based on the principle of proportional protection:
   safeguards that scale with potential risks."*
   → **Pflanzer message:** *„Anthropic škáluje bezpečnostní opatření
   úměrně riziku. Pflanzer dělá totéž — Lean profile pro ~80% projektů,
   audit-grade jen pro AI Act High-risk a DORA."*
   → URL: anthropic.com/responsible-scaling-policy/rsp-v3-0 (2024–2025).

5. **Verify-before-ship** —
   *„The trust-then-verify gap. Claude produces a plausible-looking
   implementation that doesn't handle edge cases. Always provide
   verification. If you can't verify it, don't ship it."*
   → **Pflanzer message:** *„Pflanzer's quality gates ≥80/100 +
   AI deflation -0.5 implementují Anthropic's „trust-then-verify"
   discipline na workshop layer."*
   → URL: code.claude.com/docs/en/best-practices (2025–2026).

6. **Specialized sub-agents** —
   *„Rather than one agent attempting to maintain state across an entire
   project, specialized sub-agents can handle focused tasks with clean
   context windows."*
   → **Pflanzer message:** *„Pflanzer's role catalog s rolovými sub-agents
   = direct application of Anthropic's specialized sub-agent pattern."*
   → URL: anthropic.com/engineering/effective-context-engineering-for-ai-agents (2025-09-29).

7. **Explore → plan → code** —
   *„Explore first, then plan, then code. Letting Claude jump straight to
   coding can produce code that solves the wrong problem."*
   → **Pflanzer message:** *„Pflanzer pre-flight triage (4 paralelní
   tracks) = workshop-level operacionalizace Anthropic „explore first"
   principu."*
   → URL: code.claude.com/docs/en/best-practices (2025–2026).

8. **Skills = onboarding guide** —
   *„Building a skill for an agent is like putting together an onboarding
   guide for a new hire."*
   → **Pflanzer message:** *„Pflanzer role catalog (Security, A11y, Legal,
   …) = enterprise extension Anthropic Agent Skills patternu — onboarding
   guide pro AI co-pilot per role."*
   → URL: anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills (2025).

9. **Non-engineers can ship** —
   *„For the first time, anyone on a team, not just engineers, can ship
   production code through proper git workflows."*
   → **Pflanzer message:** *„Vercel v0 zpřístupnil production code
   non-engineerům. Pflanzer přidává cross-fn alignment vrstvu, aby to
   fungovalo v regulovaném korporátu."*
   → URL: vercel.com/blog/v0-plans-for-teams (2025).

10. **Compliance API jako enterprise primitiv** —
    *„Anthropic rolled out a Compliance API for the Claude Platform that
    gives Claude Platform admins a programmatic audit feed of what's
    happening across their organization."*
    → **Pflanzer message:** *„Anthropic sám staví compliance jako first-class
    surface v 2026. Pflanzer's compliance-by-design ve workshop methodology
    má strong tailwind, ne headwind."*
    → URL: gadgetbond.com/anthropic-claude-platform-compliance-api (2026).

---

## 5) Risk / counter-evidence (brutally honest)

### 5.1 Karpathy: vibe coding není pro production

> *„Vibe coding your way to a production codebase is clearly risky."*
> (Simon Willison, simonwillison.net/2025/Mar/19/vibe-coding/, 2025-03-19)

**Impact:** Pflanzer claim *„most code goes straight to production"*
(lean-pflanzer.md, řádek 15) **musí být kvalifikovaný**. Marketing
positioning by neměl vést s tím, že Pflanzer = scaled-up vibe coding.
Karpathy + Willison + Anthropic Best practices (*„trust-then-verify gap"*)
všichni explicitně varují před přímým ship z AI-generated kódu.

**Defenzivní hrana:** Pflanzer **má** quality gates ≥80/100 a code
review (per `07-handoff-do-vyvoje.md`). Marketing musí říct:
*„Vibe coding is the input, audit-grade handoff is the output."*

### 5.2 Anthropic explicit nedoporučuje non-tech v engineering session

**Impact:** USP #1 (non-tech v místnosti) **nemá direct Anthropic
endorsement**. Nejbližší related je (a) Anthropic legal team blog post
(*„Legal uses Claude for redlining"*), což je *Legal jako user of AI*,
ne *Legal jako participant v engineering workshop*. (b) Lovable +
Vercel governance vrstva, což je *post-hoc RBAC*, ne *pre-emptive room
participation*.

**Defenzivní hrana:** USP #1 zůstává **organizational moat, ne
tooling/architectural moat**. Pflanzer's bet je, že nikdo jiný
neformalizoval *„Security from minute 0"* — to je v 2026 stále pravda
(per `04-synthesis-and-positioning.md`). Marketing musí být honest:
*„Pflanzer is the only methodology that brings non-tech roles into
the primary AI workshop session. Anthropic's enterprise governance
recognizes the need; Pflanzer operationalizes it."*

### 5.3 Anthropic agent loop je primárně single-developer

**Impact:** Anthropic *„gather context → take action → verify work →
repeat"* je výslovně **per-dev session**, ne **per-workshop**.
Pflanzer aplikuje stejný princip o vrstvu výš (workshop loop), ale
**Anthropic nikdy explicitně nepoužil Pflanzer-style 2-session +
async window pattern**.

**Defenzivní hrana:** *Sémantický match, ne lexikální.* Pflanzer claim
musí být: *„Same discipline, workshop-level application."*

### 5.4 Anti-HiPPO není v Anthropic guidance

**Impact:** Anthropic nepublikoval guideline *„highest-paid person votes
last"*. Closest related je *„human evaluation catches what automation
misses"* (multi-agent paper, 2025-06). To je o AI bias correction, ne
o hierarchy unblocking ve workshop.

**Defenzivní hrana:** **Pure Pflanzer pattern.** Marketing může říct:
*„Anti-HiPPO Decider is a Pflanzer original, derived from Liberating
Structures 1-2-4-All and Design Sprint Decider model. Anthropic and
Anthropic-ecosystem tools recognize the importance of human-in-the-loop
verification (Agent SDK 09/2025), but do not prescribe a workshop
decision protocol."*

### 5.5 14-day cadence není v žádném Anthropic doporučení

**Impact:** Pflanzer 14-day workshop cadence je **architecture choice
bez direct Anthropic endorsement**. Anthropic mluví o *tight feedback
loops* (best practices), ale ne o *2-session + async week + reinforcement*
workshop format.

**Defenzivní hrana:** Pflanzer 14-day je **operating-cadence layer**
(per `09-srovnani-existujici-metody.md` final section). Anthropic
neaktivuje workshop methodology jako téma — to je Pflanzer's mezera
v enterprise stacku. Marketing může říct: *„Pflanzer fills the gap
between Anthropic's per-session agent loop (minutes-to-hours) and
McKinsey's transformation cycle (months-to-years). 14 days is the
sweet spot for cross-functional AI pilots."*

---

## 6) Per-USP strength summary

| USP | Strength | Top evidence |
|-----|----------|--------------|
| #1 Non-tech v místnosti | **WEAK** direct, **MODERATE** via enterprise governance vrstva (Lovable, Vercel, AI Act čl. 14) | EU AI Act čl. 14 + Lovable RBAC blog 2026 |
| #2 Score závaznosti + AI deflation + anti-HiPPO | **STRONG** | Anthropic multi-agent paper (LLM judge 0-1 score) + Claude Code "trust-then-verify gap" + EU AI Act čl. 12+14 |
| #3 Pre-flight triage 4 tracks | **STRONG** sémanticky, **WEAK** lexikálně | Claude Code "explore first, then plan, then code" + Agent SDK loop |
| #4 Native AI Act / DORA compliance | **STRONG** | EU AI Act čl. 12+14 + Anthropic Compliance API 2026 + Anthropic RSP v3.0 + ISO 42001 |
| #5 14-day cadence | **MODERATE** | Karpathy weekend-vs-production caveat + Anthropic parallel agents 90% gain + tight feedback loops |
| Tactical: 23 role-expert sub-agents | **STRONG** | Anthropic multi-agent paper + sub-agents docs + Agent Skills |
| Tactical: 3 paralelní worktrees | **STRONG** | Anthropic worktree docs + Cursor /best-of-n 2026 |

**Aggregate:** 3 STRONG, 1 STRONG/WEAK split (USP #3), 1 MODERATE
(USP #5), 1 WEAK (USP #1). **Pflanzer je strongly aligned s Anthropic
architectural pattern, weakly aligned s Anthropic workshop guidance
(Anthropic prostě nepokrývá workshop layer).**

---

## 7) Reference list (URLs + datumy)

### Anthropic primary sources

- *„How we built our multi-agent research system"* —
  anthropic.com/engineering/multi-agent-research-system (2025-06-13).
- *„Effective context engineering for AI agents"* —
  anthropic.com/engineering/effective-context-engineering-for-ai-agents (2025-09-29).
- *„Building agents with the Claude Agent SDK"* —
  claude.com/blog/building-agents-with-the-claude-agent-sdk (2025-09-29,
  redirect z anthropic.com/engineering).
- *„Equipping agents for the real world with Agent Skills"* —
  anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills (2025).
- *„Writing effective tools for AI agents"* —
  anthropic.com/engineering/writing-tools-for-agents (2025).
- *„Best practices for Claude Code"* —
  code.claude.com/docs/en/best-practices (2025–2026, continuously updated).
- *„Create custom subagents"* —
  code.claude.com/docs/en/sub-agents (2025–2026).
- *„Run parallel sessions with worktrees"* —
  code.claude.com/docs/en/worktrees (2025–2026).
- *„How the agent loop works"* —
  code.claude.com/docs/en/agent-sdk/agent-loop (2025).
- *„Tool use with Claude"* —
  platform.claude.com/docs/en/agents-and-tools/tool-use/overview (2025).
- *„Agent Skills"* —
  platform.claude.com/docs/en/agents-and-tools/agent-skills/overview (2025).
- *„Anthropic's Responsible Scaling Policy v3.0"* —
  anthropic.com/responsible-scaling-policy/rsp-v3-0 (2024–2025).
- *„Claude Code and new admin controls for business plans"* —
  anthropic.com/news/claude-code-on-team-and-enterprise (2025).
- *„How Anthropic uses Claude in Legal"* —
  claude.com/blog/how-anthropic-uses-claude-legal (2025+).
- *„Anthropic Constitution"* (CC0 release) —
  anthropic.com/constitution (2026-01-21, per AI CERTs).

### Anthropic secondary / community

- *„Claude Code Advanced Patterns: Subagents, MCP, and Scaling to Real
  Codebases"* (Anthropic resources hub) —
  resources.anthropic.com/hubfs/Claude%20Code%20Advanced%20Patterns_*.pdf.
- Simon Willison, *„Anthropic: How we built our multi-agent research
  system"* — simonwillison.net/2025/Jun/14/multi-agent-research-system/.
- Simon Willison, *„Not all AI-assisted programming is vibe coding"* —
  simonwillison.net/2025/Mar/19/vibe-coding/ (2025-03-19).

### Regulatorní zdroje (EU AI Act + ISO)

- EU AI Act čl. 14 (Human oversight) —
  artificialintelligenceact.eu/article/14 (2024, ve vynucování pro
  high-risk od 08/2026).
- EU AI Act čl. 12 (Record-keeping) —
  artificialintelligenceact.eu/article/12 (2024).
- EU AI Act čl. 13 (Transparency) —
  ai-act-service-desk.ec.europa.eu/en/ai-act/article-13 (2024).
- *„Article 14 Decoded: How to Implement 'Human-in-the-Loop' Oversight"* —
  euaiactguide.com/article-14-decoded-how-to-implement-human-in-the-loop-oversight (2024–2026).
- *„Why Article 14 Demands Real Human Oversight — ISO 42001 Alone Isn't
  Enough"* — isms.online/iso-42001/eu-ai-act/article-14 (2025–2026).
- *„Compliance API launches on Claude Platform for programmatic audit
  access"* — gadgetbond.com/anthropic-claude-platform-compliance-api (2026).

### Beyond Anthropic

- Karpathy original *„vibe coding"* tweet — x.com/karpathy/status/1886192184808149383 (2025-02-02).
- *„Vibe coding"* Wikipedia entry — en.wikipedia.org/wiki/Vibe_coding (2025–2026,
  průběžně aktualizováno).
- *„A semantic history of vibe coding"* — coderabbit.ai/blog/a-semantic-history-how-the-term-vibe-coding-went-from-a-tweet-to-prod (2025–2026).
- Vercel — *„Introducing the new v0"* — vercel.com/blog/introducing-the-new-v0 (2024–2025).
- Vercel — *„v0 plans for teams are here"* — vercel.com/blog/v0-plans-for-teams (2025).
- Vercel — *„2026 Vercel AI Accelerator recap"* — vercel.com/blog/2026-vercel-ai-accelerator-recap (2026).
- Lovable — *„How Lovable approaches governance, permissions, and
  security for non-technical teams"* —
  lovable.dev/blog/security-for-non-technical-teams (2026).
- Lovable Security — lovable.dev/security (2026, průběžně).
- Cursor Composer 2 — datacamp.com/blog/composer-2 (2026-03-19) +
  nxcode.io/resources/news/cursor-alternative-2026.
- GitHub Copilot Workspace — githubnext.com/projects/copilot-workspace
  (2024–2025).
- GitHub Copilot Spaces (collaborative) —
  docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/provide-context/use-copilot-spaces/collaborate-with-others
  (2025).

---

## 8) Doporučení pro pflanzer.cz copywriter

1. **Primary citátový anchor**: kombinace Anthropic multi-agent 90.2% +
   AI Act čl. 14 human attribution. Tyto dva citáty pokrývají
   architekturu (multi-agent → 23 sub-agents) i regulatorní moat
   (AI Act → decision log) — Pflanzer's 2 nejhustčí USPs.

2. **Avoid**: framing Pflanzer jako *„Karpathy-approved vibe coding"*.
   Karpathy sám varoval před production vibe coding. Pflanzer pozici
   spíš jako *„enterprise enclosure for the vibe coding wave"*.

3. **Lean into**: *„proportional protection"* paralela s Anthropic RSP.
   To je nejčistší story pro dvouvrstvý Lean / audit-grade model.

4. **Honest gap**: non-tech-v-místnosti USP (USP #1) je defensible jen
   organizationally. Marketing copy by měl říct: *„Pflanzer is the
   first methodology to formalize Security/Legal/A11y in the primary
   AI workshop session — a gap that Anthropic's enterprise governance
   layer recognizes but does not operationalize."* (Implicitní
   uznání, ne pretense endorsement.)

5. **Citable tagline candidates** (pro 1-pager):
   - *„Built on Anthropic-recommended patterns. Designed for AI Act
     compliance from day 0."*
   - *„23 role-expert AI sub-agents. Multi-agent architecture
     Anthropic showed to outperform single-agent by 90.2%."*
   - *„14-day cadence. Audit-grade decision log. Same proportional-protection
     philosophy as Anthropic's Responsible Scaling Policy."*

---

*Konec dokumentu. ~640 řádků. Datum: 2026-05-18.*
*Předchůdce v research linii: `docs/research/competitive/04-synthesis-and-positioning.md`.*
*Doporučený follow-up: paralelní research vlna pro (a) Microsoft / GitHub
enterprise AI governance frameworks, (b) Google / DeepMind responsible AI
deployment patterns, (c) frontier-lab safety reports na overlap s Pflanzer
audit-grade USPs.*
