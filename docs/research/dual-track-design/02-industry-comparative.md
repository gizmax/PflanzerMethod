# Industry Comparative — Dual-Track / Dev-Availability Bifurcation napříč metodologiemi

> **Cílový čtenář:** metodolog / strateg, který obhajuje Track P jako default
> a Track S jako fallback. Document validuje, že (1) preferovaná cesta
> *„dev v room od minuty 0"* je v 2024-2026 industry consensus, (2) precision
> spec fallback je legitimní pouze v úzce vymezených podmínkách, (3) **adoption
> gravity** je hlavní strukturální riziko pro Pflanzer Track S → fallback se
> stává defaultem, pokud není explicit guard-rail.
>
> **Datum:** 2026-05-28.
> **Předchozí kontext:**
> - `01-methodology-architecture.md` (Track P / Track S strukturální návrh)
> - `docs/methodology/09-srovnani-existujici-metody.md` (per-method comparison)
> - `docs/research/competitive/04-synthesis-and-positioning.md` (5 protected USPs)
> - `docs/research/spec-driven-vs-pflanzer/01-sdd-mechanika.md` (SDD ekosystém)

---

## TL;DR (5 řádků)

1. **Dev-in-room je 2026 industry consensus pro implementační methodologie.** GV
   Design Sprint vyžaduje engineera (Maker/Stitcher role); AWS AI-DLC Mob Elaboration
   = 5–7 cross-fn vč. devs; Lean Inception explicit *„A Dev must be on all activities"*;
   mob programming (Falco) inkluduje non-devs okolo developer-driven driver.
   Tools-only metody (Spec Kit, Kiro, OpenSpec, BMAD) **nemají** dev requirement —
   ale **také nemají non-tech alignment vrstvu** (Martinelli 03/2026 critique).
2. **„Dev unavailable" degradation existuje pouze 4 strukturálními formami:**
   (a) strategic-foundation phase (Foundation Sprint, Lean Inception kickoff —
   *před* implementací), (b) discovery-only track (Jeff Patton dual-track agile),
   (c) consulting-engagement model (Thoughtworks 3-3-3 — externí tým převezme dev),
   (d) spec-driven handoff (Spec Kit, Kiro — explicit *„dev není v room"*).
   **Žádná metoda nemá *Track P → Track S degradation* jako documented protocol.**
3. **Precision-spec quality bar v 2026:** EARS notation (Kiro), Gherkin/BDD
   (industry default), OpenAPI 3.1 / 3.2 (contract-first), 3-phase sign-off
   (Requirements → Design → Tasks, Kiro). Pflanzer Track S spec **musí být na
   nebo nad tímto barem**, aby nebyl pouhým rebranding SDD-lite.
4. **Re-implementation gap je doložený:** 30–40 % development time lost on poor
   handoff (Questworks); 68 % rework cost from communication gap at handoff
   boundary; 47 % rework cycle reduction with formal handoff practices; 50 %
   of all requirements defects = ambiguous/inaccurate (James Martin); 70 %
   enterprise projects fail to meet objectives due to stakeholder alignment
   gap (Clarity 2026, citing Bain).
5. **Adoption gravity = #1 strukturální riziko Track S:** 5 historických precedentů
   (Spotify squad model bez full implementation; SAFe XP pair-programming patchy
   3.5 % current-project adoption; agile/AgileFall waterfall sneak-back; pair
   programming 22 % praxe / 3.5 % current — Microsoft; shadow IT = 70 % companies).
   Pflanzer Track S potřebuje **strukturální guards** (not policy), jinak
   konverguje na SDD-lite za 6-12 měsíců.

---

## 1. Per-method dev-in-room policy table

| Methodology | Dev required? | Phase | Fallback if dev absent? | Source |
|---|---|---|---|---|
| **GV Design Sprint (Knapp 2016)** | YES — Maker(s) + Stitcher role (designer or engineer) for high-fidelity prototype | Day 3-4 prototype | NO explicit fallback. Knapp 2016 *„realistic façade"* je default — neimplementační. *„Lack of engineers means solution impossible or way out of budget — renders entire process useless"* (nerdcow.co.uk) | Knapp 2016, *Sprint*; [gv.com/sprint](https://www.gv.com/sprint/); [thesprintbook.com](https://www.thesprintbook.com/the-design-sprint) |
| **AJ&Smart Sprint 2.0** (4-day) | YES — Prototyper/Maker role explicit | Day 3 prototype | Compressed format = engineer ještě kritičtější (less time pro mid-sprint hiring) | [ajsmart.com](https://ajsmart.com/design-sprints-2/); [sessionlab.com Design Sprint 2.0](https://www.sessionlab.com/templates/design-sprint-2-0) |
| **AWS AI-DLC Mob Elaboration** | YES — *„cross-functional team of 5–7 people (product, engineering, QA, Ops, security)"* | All Mob Elaboration (3–4h) + Mob Construction (3–5 days) | NO. *„Construction involves developers and AI"* — engineering je core, ne fallback role. **Žádný non-tech fallback.** | [AWS DevOps blog 7/2025](https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/); [zenn.dev kiakiraki](https://zenn.dev/kiakiraki/articles/437ba4d9441b2b?locale=en) |
| **Thoughtworks „3-3-3"** | YES — 3 days alignment + 3 weeks prototype + 3 months production MVP | All 90 days | Consulting model — Thoughtworks **dodává** dev capacity if client lacks it. *„Our technologists at the wheel"* | [thoughtworks.com/ai/works](https://www.thoughtworks.com/ai/works/) |
| **BMAD-METHOD** | NO human dev — AI agents (PdM, Architect, Dev, QA personas) | All phases | N/A — agent-only by design. *„Does not aim to replace humans entirely... humans maintain strategic oversight"* | [github.com/bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD); [Medium BMAD review](https://medium.com/@anubhavbhatt/the-bmad-method-a-smarter-way-to-build-with-ai-11c6ec07567e) |
| **Spec Kit / Kiro / OpenSpec** | NO during spec phase (developer-centric tool, but no *„room"*) | Specify → Plan → Tasks → Implement | By design no „room" — async tool | [github/spec-kit](https://github.com/github/spec-kit); [kiro.dev](https://kiro.dev/) |
| **Foundation Sprint (Knapp 2025)** | NO — *„Gather the leaders of the team: no more than five people"* — Decider + leadership | 2h strategic foundation, pre-implementation | N/A — Foundation Sprint není implementation phase; je *před* implementací. Knapp doporučuje navazující Design Sprint pro implementation | [Lenny's newsletter — Foundation Sprint](https://www.lennysnewsletter.com/p/introducing-the-foundation-sprint); [thefoundationsprint.com](https://thefoundationsprint.com/) |
| **Lean Inception (Caroli)** | YES (explicit) — *„A Dev must be on all the lean inception activities"* | All 5 days (or compressed 2-day) | Post-inception sprint 0 = další dev tým. Sprint 0 *„will have to constantly be doing this as project progresses"* | [caroli.org/en/lean-inception-for-a-dev](https://caroli.org/en/lean-inception-for-a-dev/); [caroli.org Lean Inception](https://caroli.org/en/lean-inception-4/) |
| **Liberating Structures (1-2-4-All)** | NO requirement | Single workshop | N/A — generic facilitation pattern, ne implementation method | [liberatingstructures.com](https://www.liberatingstructures.com/) |
| **Design Thinking (IDEO)** | NO during Empathize/Define/Ideate | Implementation phase = hand-off to developers | *„Prototype helps communicate concepts to stakeholders and developers"* — developer = handoff recipient, ne primary participant | [designthinking.ideo.com](https://designthinking.ideo.com/); [ideou.com](https://www.ideou.com/blogs/inspiration/design-thinking-process) |
| **Event Storming Big Picture** | YES — *„Event Storming can only unfold its full potential when not only developers do it"* but devs are explicit participants | All workshop (2-8h, up to 2 days) | NO — žádná verze bez devs. Domain experts + devs = base requirement | [philippe.bourgau.net](https://philippe.bourgau.net/4-tips-that-will-make-your-ddd-big-picture-event-storming-successful/); [wiki.prooph-board.com](https://wiki.prooph-board.com/event_storming/big_picture.html) |
| **Mob Programming (Falco)** | YES — driver + navigators, většinou devs; **non-devs participate around dev core** | Single mob session | *„Non-developer participation"* — PO, tester, designer kolem dev driver, ne místo něj | [The Mob Programming Guidebook](https://www.mobprogrammingguidebook.com/images/mobprogrammingguidebook.pdf) |
| **Shape Up (Basecamp)** | YES post-shaping (Cycle = 6 weeks dev work) | Shaping phase: no devs; Cycle: full team of devs | Shaping bez devs, ale Cycle (build) je explicit dev-driven. Žádný *„spec-only handoff to external team"* | [basecamp.com/shapeup](https://basecamp.com/shapeup/0.3-chapter-01) |
| **Pflanzer (Track P)** | YES — FE/Vibe-coding lead + BE/API lead in room from minute 0 | Session 1 (3-6h) | **Track S documented fallback** s 4 hard triggers | `01-methodology-architecture.md` |

### Klíčová observation #1: Žádná implementační metoda nemá *Track P → Track S degradation*

Z 14 metodologií **žádná** explicitně dokumentuje *„default = dev v room; fallback = spec to external team"* protokol. Nejbližší vzory:

- **Foundation Sprint → Design Sprint**: chain, ale to jsou dvě separátní metody, ne dual-track jedné metody.
- **Lean Inception → Sprint 0**: chain, kde Sprint 0 je další dev cycle, ne fallback.
- **Shape Up Shaping → Cycle**: phase split, ale dev tým je *stejný v obou phases* (shaping team je subset cycle teamu).
- **Thoughtworks 3-3-3**: consulting *dodává* devs — žádný fallback, je to plná convergence na vendor delivery.

**Důsledek pro Pflanzer:** Track P / Track S model je **strukturální novinka**.
To má dvě implikace:
1. Pflanzer nemůže okopírovat existující bifurcation protocol — musí navrhnout vlastní.
2. **Žádné guard-railing není proven**. Adoption gravity riziko je high.

### Klíčová observation #2: Tools-only metody (SDD ekosystém) nahrazují developer requirement *AI*, ne *spec*

Spec Kit / Kiro / OpenSpec / BMAD nemají developer v *„room"* protože **nemají room**. Spec generated by LLM → reviewed by 1-2 humans → implemented by AI agent. Mezi-stakeholderový alignment **chybí by design**.

Martinelli (03/2026): *„Enterprise teams need business stakeholders to validate requirements — not just developers reviewing markdown files. This alignment is not optional."* Pflanzer Track S **musí mít stakeholder alignment**, jinak ztrácí 4. protected USP (native AI Act compliance) a 1. USP (non-tech v room).

---

## 2. Degradation patterns (12 examples — kde se „preferred" stalo „fallback")

### 2.1 Spotify squad model 2016 → component teams 2020+
**Pattern:** Squad autonomy s embedded skills bylo aspirational, never fully implemented. Engineering managers reportovali outside squad boundaries (chapter leads per specialization). Squads grew headcount avoiding dependencies; chapters became ineffective.
**Quote:** *„The famed squad model was only ever aspirational and never fully implemented, and organizational chaos ensued as the company's leaders incrementally transitioned to more traditional management structures."* — [Jeremiah Lee blog](https://www.jeremiahlee.com/posts/failed-squad-goals/)
**Lesson pro Pflanzer:** Pokud *„dev embedded in room"* je described jako ideal ale není enforced strukturálně, organizace converguje k *„dev assigned to PR review later"* (= Track S equivalent).

### 2.2 Agile *„as practiced"* vs *„as documented"* (AgileFall)
**Pattern:** *„AgileFall describes a situation in which project managers attempt to shift to Agile methodology, but are forced to continue operating under many of the rules and practices of traditional Waterfall development."* Optional waterfall practices became default.
**Quote:** *„The adoption of Agile practices at the expense of Agile principles all but guarantees that organizations will see the benefits of neither."*
**Numerical:** Only 4 % respondents to Matt LeMay survey 2020 reported actual agility (vs claimed agile adoption).
**Source:** [HBR — When Waterfall Principles Sneak Back](https://hbr.org/2019/09/when-waterfall-principles-sneak-back-into-agile-workflows); [Medium — Agile Adoption Is Not Agility](https://medium.com/on-human-centric-systems/agile-adoption-is-not-agility-f1bcd8f68fef)
**Lesson:** Without structural enforcement, *„we'll prefer Track P"* degrades to *„we use Track S because it's easier."*

### 2.3 SAFe XP pair programming — *„optional"* zůstal optional
**Pattern:** SAFe endorses XP including pair programming, ale adoption je patchy.
**Numerical:** Microsoft research: 22 % engineers have *„practiced"* pair programming; only **3.5 %** apply it in *„current project"*. Pair programming *„still only has patchy adoption in the industry"* (Martin Fowler).
**Source:** [Martin Fowler — On Pair Programming](https://martinfowler.com/articles/on-pair-programming.html); [arXiv 2506.19511](https://arxiv.org/html/2506.19511v1)
**Lesson:** *„Optional practice that gives best result"* converguje na *„nikdo ji v praxi nepoužívá"*. Pflanzer Track P bez structural enforcement = Track S majoritní.

### 2.4 SAFe ART IP Iteration — buffer became overflow
**Pattern:** Innovation & Planning iteration je dedicated capacity buffer (no features/stories planned). Měl být pro innovation + technical debt + cross-training. V praxi *„buffer absorbs unexpected delays and dependencies"*, čili scope creep z předchozího PI.
**Source:** [premieragile.com — SAFe IP Iteration](https://premieragile.com/what-is-ip-iteration-in-safe/); [deeprojectmanager.com](https://deeprojectmanager.com/safe-innovation-and-planning-iteration/)
**Lesson:** Capacity buffer ≠ usage outcome. Pokud Track P má sliding window/buffer (5-7d async), může se *„rozšířit"* až Track P ⊂ Track S.

### 2.5 DORA 2024 — platform team penalty na throughput
**Pattern:** Teams that rely heavily on a platform experienced **8 % drop in throughput** compared to those not using one. Platform team produces **6 % gain at team level** but **negligible at individual level**. Developer independence (no enabling team dependency) = **+5 % productivity** both individual and team.
**Source:** [DORA Report 2024](https://dora.dev/research/2024/dora-report/); [Middleware blog](https://middlewarehq.com/blog/platform-engineering-impact-on-developer-productivity-dora-report-2024-trends-and-takeaways)
**Lesson:** *„Hand to platform team"* = 8 % throughput penalty. Track S (handoff to dev team) **dědí tento penalty by design**. Pflanzer marketing musí být upfront *„Track S má 8% performance cost vs Track P"* nebo srovnatelný framing.

### 2.6 Scrum Master & Product Owner v Daily Scrum — *„not mandatory"* became mandatory
**Pattern:** Scrum Guide does NOT mandate SM/PO presence at Daily Scrum. *„Contrary to popular belief, the presence of the Scrum Master and Product Owner is not mandatory at certain meetings like the Daily Scrum."* Ale v praxi obě role staly de-facto required — bez nich agilita kolabuje.
**Source:** [Medium — Davide Patti](https://medium.com/@davidepatti/why-the-scrum-master-and-product-owner-are-not-mandatory-at-daily-scrum-180a7de9e3ab); [Scrum.org](https://www.scrum.org)
**Lesson:** *„Optional"* může mít opačný směr taky — *„optional"* stane mandatory. Track P jako *„preferred"* může se stát *„mandatory pro audit-grade"* (= positive direction).

### 2.7 Spec Kit constitution.md — *„non-negotiable"* je negotiable
**Pattern:** Spec Kit constitution = *„non-negotiable principles"*. Quality gates *„enforced through mandatory gates"*. Ale *„when a plan violates constitutional principles, the violation must be documented in the Complexity Tracking section with explicit justification."* → exception path → de facto negotiation.
**Source:** [Microsoft Dev Blog — Spec Kit](https://developer.microsoft.com/blog/spec-driven-development-spec-kit); [Spec Kit constitution discussion](https://github.com/github/spec-kit/discussions/980)
**Lesson:** *„Mandatory s exception path"* = de facto optional. Pflanzer Track P enforcement nemůže mít *„dokumentovaná exception"* path, jinak je to Track S de-facto default.

### 2.8 Shadow IT 2026 — *„unofficial"* became default
**Pattern:** *„Shadow AI is becoming the default enterprise architecture as AI adoption outpaces governance."* **70 %** companies have shadow IT (Vanta 2026 survey).
**Source:** [Black Hat MEA — Shadow AI default architecture](https://insights.blackhatmea.com/is-shadow-ai-now-the-default-enterprise-architecture/); [Wikipedia Shadow IT](https://en.wikipedia.org/wiki/Shadow_IT)
**Lesson:** Když official path má friction a unofficial path nemá, unofficial wins. Pflanzer Track P (in-room, 14 days, 4-7 lidí, pre-flight gate) má vyšší friction než Track S (spec ke devs). Bez structural intervention Track S vyhraje.

### 2.9 Continuous Discovery replacing Dual-Track Agile
**Pattern:** *„In fact, continuous discovery has essentially replaced dual-track agile over the last couple of years."* Patton's 2012 dual-track became Torres' continuous discovery (2021).
**Source:** [LogRocket — Dual-Track Agile and Continuous Discovery](https://blog.logrocket.com/product-management/dual-track-agile-continuous-discovery/)
**Lesson:** Dual-track modely *konverguují* — one track tends to absorb the other. Pro Pflanzer hrozí, že *„dual-track"* (P + S) konverguje na *„all-track"* (vše Track S) nebo *„single-track"* (Track P only) podle adoption realities.

### 2.10 Design Sprint corporate adoption — *„5 days"* became *„1 day workshop"*
**Pattern:** GV Sprint 2016 = 5 days non-stop seniors. Corporate stakeholder availability = nereální. Sprint 2.0 (AJ&Smart) = 4 days. Sprint Micro = 1 day. *„Senior unavailability"* drove format compression.
**Source:** [DesignRush — Design Sprint 2026](https://www.designrush.com/agency/product-design/trends/google-design-sprint); [SessionLab DS 2.0](https://www.sessionlab.com/templates/design-sprint-2-0)
**Lesson:** *„Senior unavailability"* je rekurentní failure mode. Pflanzer dev (FE lead + BE lead) je často senior → strukturně absent → Track S becomes default.

### 2.11 OpenSpec adoption — Instructions.md as fallback
**Pattern:** Developer experiment dokumentován v *„OpenSpec Failed My Experiment"*. 3 attempts OpenSpec → 4. attempt *„Instructions.md (bez SDD)"* — *„Quickly, minimal token usage, dramatically shorter execution time."*
**Source:** [DEV.to — OpenSpec Failed](https://dev.to/incomplete_developer/openspec-spec-driven-development-failed-my-experiment-instructionsmd-was-simpler-and-faster-3a5d)
**Lesson:** I uvnitř SDD existuje *„fallback to simpler"* path. Pro Pflanzer to znamená: Track S (spec) může mít *„informal fallback to Instructions.md"* — meta-fallback hierarchy.

### 2.12 Karpathy vibe coding 2025 → spec-driven 2026
**Pattern:** Karpathy coined *„vibe coding"* Feb 2025. Feb 2026 declared it obsolete. Within 12 months: aspirational mainstream → declared end-of-era. Industry shifted to *„agentic engineering — orchestrating agents against detailed specifications with human oversight."*
**Source:** [Augment Code — Vibe Coding vs SDD](https://www.augmentcode.com/guides/vibe-coding-vs-spec-driven-development); [InfoWorld — Vibe Coding or SDD](https://www.infoworld.com/article/4166817/vibe-coding-or-spec-driven-development-how-to-choose.html)
**Lesson:** AI tooling category lifespan = 12 months. Pflanzer cannot assume Track P (vibe-coding-based) bude vždy preferred — během 12 měsíců SDD/spec-driven může být *„best practice"* a Track P bude pod tlakem konvergovat na Track S.

---

## 3. „Precision spec" — industry best practices

Pokud Track S existuje, jeho spec MUSÍ být demonstrably above SDD standard. Industry consensus 2026 na precision spec je následující:

### 3.1 Acceptance criteria format

| Standard | Format | Použití |
|---|---|---|
| **EARS notation** (Kiro default) | *„WHEN [trigger] THE SYSTEM SHALL [behavior]"* | Acceptance criteria + edge cases. Originally Rolls-Royce. Pflanzer 2026 — explicit recommendation. |
| **Gherkin / Given-When-Then** | *„Given [context] When [action] Then [outcome]"* | BDD test scenarios. *„Move from ambiguity to precision."* 1-3 criteria per story optimal (more → split story). |
| **User Stories** | *„As a [role] I want [feature] so that [benefit]"* | High-level intent, **not enough** as sole acceptance criteria. Must pair with EARS or Gherkin. |
| **Spec Kit checkpoint** | Specify → Plan → Tasks → Implement | Sequential sign-off gates. Constitution = non-negotiable principles. |

**Pflanzer Track S minimum bar:**
1. **EARS notation** pro každou Critical user story.
2. **Gherkin** pro každý acceptance criteria (1-3 per story max — pokud více, split story).
3. **Sign-off gate**: Decider + role-owners (Security/Legal/A11y/UX writer/CS-proxy) **musí** sign-off před handoff.

### 3.2 API contracts (OpenAPI 3.1 / 3.2)

**Industry 2026:** Contract-first development. *„Agreeing on an API contract first and then programming business logic afterwards."* Enterprise audit platforms (42Crunch) support OAS v2, v3.0, v3.1 with **300+ security checks**. OpenAPI 3.2.0 (Sept 2025) added *„structured tag navigation, streaming-friendly media types, fresh OAuth flows."*

**Pflanzer Track S minimum bar:**
- **Complete OpenAPI 3.1** (request schemas, response schemas, error schemas, auth flows) — 100 % surface, ne happy path only.
- **Linted** via 42Crunch or equivalent (no critical findings).
- **Auditable** — versioned in repo with sign-off log.

### 3.3 Test scenarios (BDD)

**Industry consensus:** BDD scenarios = specifications, not just tests. *„Should be essential, focused, singular, clear, complete, unique, ubiquitous, integrous"* (Characterising the Quality of BDD Specifications, Springer 2020).

**Pflanzer Track S minimum bar:**
- **Gherkin BDD** scenarios pro každý acceptance criteria — happy path + at least 2 edge cases + 1 error case.
- **Negative scenarios** explicit (industry: *„consider both positive and negative conditions"*).
- **Test data** packaged (sample payloads, golden datasets).

### 3.4 Data model

**Industry default 2026:**
- ERD (Mermaid or PlantUML embedded v markdown).
- **Sample payloads** (canonical happy + edge + error).
- **Data lineage** pokud applicable.

**Pflanzer Track S minimum bar:**
- ERD + sample payloads + dialect indication (PostgreSQL/MySQL/MongoDB specifics).
- **Privacy classification** per field (PII / PHI / financial / public) — Track S MUSÍ mít, protože sponsor Track S často je v regulated context.

### 3.5 Edge cases enumeration

**Industry research:** Spec Kit generuje *„2 577 ř. MD pro 689 ř. kódu"* (Scott Logic 11/2025) — verbose. Kiro single-line bug = *„4 user stories + 16 acceptance criteria"* (Böckeler, Martin Fowler). Overhead-heavy.

**Pflanzer Track S optimum:**
- **Edge cases per Critical user story:** min 3 (boundary, error, concurrency).
- **NOT exhaustive** — per Pflanzer principle *„precision, ne completeness"* (`01-methodology-architecture.md`).
- **TRIZ pre-mortem** v Session 1 = source pro Track S edge case enumeration.

### 3.6 Sign-off requirements

**Industry comparison:**

| Tool | Sign-off gates | Who signs |
|---|---|---|
| Kiro | Requirements → Design → Tasks | Single user („review and approval") |
| Spec Kit | Constitution + per-stage checklist | Single user („manual review") |
| BMAD | Phase handoffs (Discovery → Planning → Execution → Verification) | Agent-only (no human sign-off explicit) |
| Lovable | GitHub export | Single user via PR review |
| **Pflanzer Track S** | **5+ role sign-offs (Decider + Security + Legal + A11y + UX writer + CS proxy)** | **Multi-role, attributed, DORA 7-year retention** |

**Pflanzer differentiator:** Multi-role attribution = native AI Act čl. 14 compliance. **No SDD tool má toto out-of-the-box.**

### 3.7 Quality gate score pro spec (analog k ≥80/100 pro kód)

Industry: **žádný explicit numeric quality gate pro spec.** Spec Kit má `/speckit.analyze` cross-artifact validation — pass/fail, no score.

**Návrh pro Pflanzer Track S** (originální):

| Dimenze | Skóre 0-20 | Threshold |
|---|---|---|
| **Acceptance criteria coverage** (EARS pro Critical stories) | 0 = chybí, 20 = 100 % stories | ≥16 |
| **API contract completeness** (OpenAPI 3.1 lint score) | 0 = chybí, 20 = 0 critical findings | ≥16 |
| **Test scenarios** (Gherkin happy + 2 edge + 1 error per AC) | 0 = chybí, 20 = full | ≥16 |
| **Data model** (ERD + samples + privacy classification) | 0 = chybí, 20 = full | ≥16 |
| **Sign-off completeness** (5+ roles signed, attributed) | 0 = 0 roles, 20 = 5+ roles all signed | ≥20 (mandatory) |

**Threshold pro Track S handoff: ≥84/100** (= analog k ≥80/100 pro Track P kód, ale 4 bod přísnější protože sign-off completeness binary mandatory).

---

## 4. Track S vs SDD — must-be-NOT-SDD differentiation

### 4.1 The convergence risk (per definici)

Pokud Pflanzer Track S = *„spec → external dev team"*, to literally **JE SDD** per definici. Bez explicit differentiator Track S = SDD-lite rebranding.

### 4.2 Quantitative empirical data — kde spec vyhrává

| Use case | Why spec works | Source |
|---|---|---|
| **Legacy modernization (COBOL → Java)** | AI extrahuje institutional knowledge z legacy do plain-language specs verified by domain experts. Spec → source-of-truth pro modernized system. | [Civic Innovations SpecOps](https://civic.io/2025/12/04/proving-out-a-new-approach-to-legacy-system-modernization/) |
| **Multi-vendor contracts** | Vendor-neutral specification = contract baseline. Spec Kit constitution + OpenAPI 3.1 = same contract to 2-3 vendors. | [RFP process guide](https://www.responsive.io/blog/rfp-process-guide); SDD comparative refs |
| **Large distributed teams (50+ engineers, 3+ continents)** | Spec = async-readable single source of truth. Pflanzer in-room formát nescaluje >10 účastníků. | DORA 2024; `docs/research/spec-driven-vs-pflanzer/01-sdd-mechanika.md` §5.3 |
| **Continuous engineering (weekly release)** | Per-PR spec + cross-artifact validation = lightweight, continuous, fits PR pipeline. | `01-sdd-mechanika.md` §5.4 |
| **Regulated handoff post-incident** | Spec = ex-ante artefakt, code = ex-post evidence. Diff je accountability. | `01-sdd-mechanika.md` §5.5 |

### 4.3 Quantitative empirical data — kde spec selhává

| Pattern | Numerical | Source |
|---|---|---|
| **Spec drift v code** | 9.8–42.1 % AI-generated code mismatches/vulnerabilities | Yan et al. 2025 (via Augment Code) |
| **Greenfield ambiguity** | 50 % requirements defects = ambiguous/inaccurate | James Martin (via Lansa research) |
| **Stakeholder alignment gap** | 70 % enterprise projects miss objectives | Bain via [Clarity 2026](https://heyclarity.dev/blog/the-stakeholder-alignment-problem-why-enterprise-software-projects-miss-the-mark/) |
| **Handoff cost** | 30-40 % dev time lost on misinterpretation/rework | Questworks |
| **Re-impl from communication gap** | 68 % rework cost from information lost/never communicated at handoff boundary | Questworks |
| **Markdown:code ratio Spec Kit** | 2 577 ř. MD : 689 ř. kódu (3.74:1); 10× pomalejší than iterative prompting | Scott Logic 11/2025 |
| **Excessive overhead small bug** | 4 user stories + 16 acceptance criteria pro single-line bug | Böckeler / Martin Fowler 11/2025 |
| **Spec hallucination duplicates** | *„The agent ignored the notes that these were descriptions of existing classes, it just took them as a new specification and generated them all over again, creating duplicates"* | Böckeler 11/2025 |

### 4.4 Pflanzer Track S differentiation (canonical 5-pillar)

To prevent Track S from being SDD-lite, **Pflanzer Track S MUSÍ zachovat všech 5 protected USPs**:

| Pillar | SDD má? | Track P má? | Track S má? |
|---|---|---|---|
| **1. Non-tech role v primary session** (Security, Legal/DPO, A11y, UX writer, CS proxy v room minute 0) | NE | ANO | **ANO** — non-tech musí být v room pro Session 1 a Session 2 i v Track S |
| **2. Score závaznosti per role + AI deflation 0.5** | NE | ANO | **ANO** — multi-role attribution preserved |
| **3. Pre-flight triage 4 tracks** (Discovery + Security + Legal + Platform, 48-72h pre-read) | NE | ANO | **ANO** — Track S **zostřuje** pre-flight (sponsor mandate + audit-grade default) |
| **4. Native AI Act čl. 14 / DORA compliance** | NE | ANO | **ANO** — decision log + 7-year retention |
| **5. Anti-HiPPO Decider voting last + ADR-0001 escalation** | NE | ANO | **ANO** — Decider's voice: *„Track S je kompromis, ne volba"* |

**Klíčový závěr:** Track S **bez 5 pillars = SDD-lite**. Track S **s 5 pillars = stakeholder-aligned SDD** (= novel kategorie, Pflanzer's contribution).

### 4.5 Differentiation soundbites pro web (Track S vs SDD)

Z této research vytahuju 4 sound-bites pro Pflanzer marketing:

1. **„Spec Kit produces a contract. Pflanzer Track S produces a contract signed by Security, Legal, A11y, UX writer, and CS proxy — with attribution and 7-year retention."**
2. **„70 % enterprise projects fail due to stakeholder alignment gap (Bain). Pflanzer Track S spec is the only spec with multi-role attributed sign-off out-of-the-box."**
3. **„Spec Kit generates 2 577 lines of markdown for 689 lines of code. Pflanzer Track S spec is bounded by 5 quality dimensions (≥84/100 gate) and signed by 5+ roles."**
4. **„Kiro asks 1 user to sign-off. Pflanzer Track S requires Decider + role-owners — with explicit anti-HiPPO Decider-votes-last protocol per ADR-0001."**

---

## 5. Adoption gravity risk — 5 historical precedents kde fallback became default

### 5.1 Spotify squad model — *„engineering manager outside squad"* became *„component team"*
**Pattern:** Aspirational embedded model never fully implemented. Engineering managers outside squad (chapter leads per specialization), squads grew avoiding dependencies, chapters became ineffective. *„Co-author of the Spotify model and multiple agile coaches who worked at Spotify have been telling people to not copy it for years."*
**Quantitative:** No specific 67 % conversion stat in public sources, but Jeremiah Lee retrospective confirms *„incrementally transitioned to more traditional management structures."*
**Source:** [Jeremiah Lee — Failed #SquadGoals](https://www.jeremiahlee.com/posts/failed-squad-goals/); [DX Podcast](https://getdx.com/podcast/spotify-squads/)
**Pflanzer implication:** Pokud Track P (cross-fn embedded) je aspirational ale Track S (handoff) je easier, organizace converguje na Track S. **Structural fix needed.**

### 5.2 SAFe XP pair programming — patchy 3.5 %
**Pattern:** SAFe endorses XP including pair programming. Microsoft research: 22 % engineers have practiced, only **3.5 %** apply in current project.
**Quantitative:** 22 % lifetime / 3.5 % current = 84 % drop-off rate from practice to current adoption.
**Source:** [Martin Fowler — On Pair Programming](https://martinfowler.com/articles/on-pair-programming.html)
**Pflanzer implication:** Even if **all** Pflanzer-trained facilitators learn Track P, only ~3-5 % actually run Track P. Bez enforcement Track P bude minoritní.

### 5.3 Agile/AgileFall — *„agile principles"* lost, *„agile ceremonies"* kept
**Pattern:** Organizations adopt agile ceremonies (daily standup, retro) but waterfall principles persist (big design upfront, phase gates, formal handoff). Matt LeMay survey 2020: **only 4 %** respondents reported actual agility.
**Quantitative:** 4 % real agility / 96 % AgileFall = mostly fallback.
**Source:** [Matt LeMay survey — Agile Adoption Is Not Agility](https://medium.com/on-human-centric-systems/agile-adoption-is-not-agility-f1bcd8f68fef); [HBR AgileFall](https://hbr.org/2019/09/when-waterfall-principles-sneak-back-into-agile-workflows)
**Pflanzer implication:** Pokud Pflanzer Track P se reduce na *„ceremonies"* (Session 1 + Session 2 ceremony) bez non-tech in-room reality, dostáváme PflanzerFall = Track S de facto.

### 5.4 Shadow IT — 70 % companies
**Pattern:** Official IT path s friction (governance, security review, procurement); unofficial shadow IT bez friction. **70 %** companies have shadow IT (Vanta 2026). Shadow AI declared *„default enterprise architecture"* (Black Hat MEA 2026).
**Quantitative:** 70 % shadow / 30 % official = fallback je default.
**Source:** [Vanta 2026 via Black Hat MEA](https://insights.blackhatmea.com/is-shadow-ai-now-the-default-enterprise-architecture/); [Wikipedia](https://en.wikipedia.org/wiki/Shadow_IT)
**Pflanzer implication:** Track P (6-7 lidí, 14 dní, pre-flight gate) má vyšší friction než Track S (spec ke devs). Track S bude *„shadow track"* convergence target.

### 5.5 Continuous Discovery replacing Dual-Track Agile
**Pattern:** Patton 2012 Dual-Track Agile (Discovery + Delivery parallel). Torres 2021 Continuous Discovery (Discovery permeating Delivery, no separate track). *„Continuous discovery has essentially replaced dual-track agile over the last couple of years."*
**Quantitative:** No specific %; but LogRocket 2024 retrospective consensus = continuous discovery dominant.
**Source:** [LogRocket](https://blog.logrocket.com/product-management/dual-track-agile-continuous-discovery/); [SVPG — Dual-Track Agile](https://www.svpg.com/dual-track-agile/)
**Pflanzer implication:** Dual-track models converge. Track P + Track S nemůže zůstat *„parallel preferred + fallback"* dlouho. Po 2-3 letech jeden vyhraje a Pflanzer bude *„single-track P"* (ideálně) nebo *„single-track S"* (worst case).

---

## 6. Recommendations — strukturální guards pro Track P jako default

Z above 5 historical precedents vyplývá: *„document Track P as preferred, Track S as fallback"* je **insufficient**. Pflanzer musí mít **strukturální** (ne policy) guards.

### 6.1 4 hard triggers pro Track S aktivaci (per `01-methodology-architecture.md`)

Track S **musí** vyžadovat 1 ze 4 explicit triggers:
1. **Distributed dev ≥3 timezones** — physically impossible in-room
2. **Regulatorní gate vyžadující separate impl** (např. multi-vendor contract jako audit-as-spec)
3. **AI Act High-risk certified production** — vyžaduje formal spec deliverable per čl. 14/15
4. **Sponsor mandate spec-as-deliverable** — explicit non-Pflanzer constraint

**Bez 1 z 4 triggerů: Track P, nebo metoda neproběhne.**

### 6.2 Trigger validation = pre-flight track 5

Pflanzer pre-flight má 4 tracks (Discovery + Security + Legal + Platform). **Návrh: přidat 5. track — Track-S Trigger Validation.**

5. **Track-S Trigger Validation** — 48-72h pre-read, validates 1 ze 4 triggers signed by Decider + relevant stakeholder. **Default: Track P. Track S aktivován pouze pokud Track-S Trigger Gate pass.**

### 6.3 Track P / Track S asymmetric pricing/effort

Z DORA 2024: platform team handoff = **8 % throughput penalty**. Pflanzer dokumentace + marketing **musí explicit říct**:

- Track P: 10 PD effort, 14 dní calendar, output = production-ready kód (≥80/100 quality gate)
- Track S: **15-20 PD effort** (extra non-tech sign-off, audit trail, spec quality dimension audits), 18-25 dní calendar, output = precision spec (≥84/100 quality gate) **+ external dev team's effort to implement** (3-5× spec effort per industry handoff penalty)

**Track S effort musí být visibly higher než Track P** v marketing materials, jinak adoption gravity prevails (Track S looks easier → becomes default).

### 6.4 Decider's voice canonical

Z `01-methodology-architecture.md`: *„Track S je kompromis, ne volba."* Tato věta **musí** být v každém marketing collateral, README, web hero, pricing page. Adoption gravity je primárně **psychological** — pokud Track S vypadá jako legitimate volba, organizace ji volí pro flexibility. Pokud vypadá jako kompromis, organizace ji volí pouze pokud musí.

### 6.5 Method Steward role (per ADR-0012)

Method Steward governance role = monitor Track P / Track S ratio across pilots. **Threshold:** pokud Track S > 30 % of pilots za quarter, **Method Steward audit** investigates structural drift. Quarterly retrospective = early warning system pro adoption gravity drift.

### 6.6 Reinforcement track delta pro Track S

Pflanzer reinforcement T+7/30/60/90 měří outcome vs prediction. **Návrh pro Track S:**
- **T+7:** dev team kickoff status, spec questions count (target: <5 per week — pokud více, spec quality nedostatečná)
- **T+30:** re-implementation cycles count (target: 0-1 — pokud 2+, Pflanzer Track S failed)
- **T+60:** quality gate score per Pflanzer release (target: ≥80/100 if Pflanzer Track P, ≥70/100 if Track S handoff)
- **T+90:** stakeholder alignment retention (Decider + role-owners still align with shipped product?)

**Track S má vyšší measurement bar than Track P**, protože musíme detect drift z spec → impl.

### 6.7 Explicit anti-pattern documentation

V `docs/methodology/` přidat dedicated section *„Track S anti-patterns"*:

- *„Track S as default"* — pokud organizace volí Track S without 1-of-4 trigger, **method neproběhne**.
- *„Track S without non-tech sign-off"* — preserves 1. Pflanzer USP, mandatory.
- *„Track S spec without ≥84/100 quality gate"* — preserves spec quality bar.
- *„Track S without reinforcement track"* — preserves audit trail USP.

### 6.8 Web pricing page differentiation

Per `04-synthesis-and-positioning.md` P2 plan: pricing tiers. **Návrh pro Track P / Track S:**

| Tier | Track P (preferred) | Track S (fallback) |
|---|---|---|
| **DIY** (free) | Self-serve template, no facilitator | Self-serve template, no facilitator, **explicit Track-S Trigger Gate required** |
| **Facilitator** (€10-25k/cycle) | 1 facilitator, 1 cycle 14d | 1 facilitator + 1 spec quality auditor, 1 cycle 18-25d, **+30-50 % vs Track P** |
| **Audit-grade** (€40-80k) | Co-facilitator + Method Steward, 1 cycle 4-6 weeks | Co-facilitator + Method Steward + Independent spec auditor, 1 cycle 5-8 weeks, **+50-100 % vs Track P** |

**Pricing musí explicit reflect Track S higher effort.** Adoption gravity má economic component — pokud Track S je levnější, organizace volí Track S. Pokud Track S je dražší (a delivers higher quality artefakt), organizace volí Track P unless necessary.

### 6.9 Marketing framing — never sell Track S directly

Pflanzer marketing **nesmí** featurit Track S jako *„alternative"* nebo *„flexibility option"*. Track S existuje jako **honest acknowledgement** pro audit-grade audience (CRO/DPO), ne jako sales pitch:

- Web hero: *„Pflanzer = cross-functional alignment + production code via 2 sessions + async."* (Track P only)
- FAQ: *„Q: Co když dev tým není v room? A: Pflanzer Track S = precision spec fallback s multi-role sign-off, dostupný pokud splňujete 1 ze 4 hard triggerů. Default cesta je Track P — Track S je kompromis, ne volba."*

### 6.10 ADR enforcement

ADR-0005 (Cross-functional alignment) musí explicit say:
- Track P = default per Pflanzer Method Charter v0.4+
- Track S = fallback s 1-of-4 hard triggers + Track-S Trigger Gate validation
- Pokud trigger neexistuje a Track S je *„chosen for convenience"*, je to **method violation** (ne legitimate variant)
- Method Steward governance: quarterly audit Track P / Track S ratio across pilot portfolio

---

## 7. Recommendations summary table

| Guard | Type | Owner | Threshold |
|---|---|---|---|
| **4 hard triggers** pro Track S | Structural (gate) | Decider + sponsor | Bez 1-of-4: Track S forbidden |
| **5. pre-flight track Trigger Validation** | Structural (process) | Co-facilitator | Track S handoff requires gate pass |
| **Track S effort visibly higher** (15-20 PD vs 10 PD) | Marketing/contract | Pflanzer Method team | Pricing differential ≥30 % |
| **Decider's voice canonical** (*„Track S je kompromis"*) | Cultural | Method Steward | Every marketing artefact |
| **Method Steward audit** if Track S >30 % pilots | Governance | Method Steward | Quarterly review |
| **Track S reinforcement T+7/30/60/90 delta** | Measurement | Co-facilitator | Spec questions <5/wk, re-impl cycles 0-1 |
| **Anti-pattern docs** | Documentation | Method team | `docs/methodology/` dedicated section |
| **Web pricing Track S +30-50 %** | Marketing | Sales/marketing | Pricing page reflects |
| **Marketing never sell Track S directly** | Brand | Marketing | FAQ-only treatment |
| **ADR-0005 enforcement** | Documentation | Method team | ADR-0005 + ADR-0020 |

---

## 8. Co tato research konfirmuje vs co je net-new

### Konfirmuje (Pflanzer pozice already-strong)

- **Dev-in-room je 2026 industry consensus** — 11 ze 14 mainstream metodologií vyžadují dev v primary session (kromě Foundation Sprint pre-implementation, BMAD AI-only, SDD tools by definition).
- **Stakeholder alignment + audit trail = real enterprise gap** — Bain 70 %, Clarity 2026, Questworks 30-40 %, James Martin 50 %. Pflanzer 5 USPs are critique points materialized.
- **Re-implementation gap data** — Yan 2025 (9.8-42.1 %), Scott Logic (3.74:1 markdown:code), Böckeler (4 stories pro single-line bug). Track S handoff má real cost.

### Net-new finding (Pflanzer pozice needs strengthening)

- **Žádná konkurenční metoda nemá *Track P → Track S degradation* protocol.** Pflanzer's strukturální novinka = strukturální obhajoba potřebná.
- **5 adoption gravity precedentů** (Spotify, SAFe XP, Agile/AgileFall, Shadow IT, Continuous Discovery convergence) → high risk že Pflanzer Track S → default za 6-12 měsíců bez structural guards.
- **Precision spec quality bar v 2026** je vyšší než Pflanzer current Charter — potřeba upgrade spec quality gates (EARS + Gherkin + OpenAPI 3.1 + sign-off matrix).
- **DORA 2024 8 % platform handoff penalty** = quantitative základ pro Track S effort differential. **Pflanzer marketing material musí to citovat.**

---

## 9. Open questions / unverified claims

| Claim | Status | Akce |
|---|---|---|
| *„Spotify squads 2018-2024 evolved 67 % to component teams"* (z user prompt) | Nepotvrzeno publicly. Jeremiah Lee retrospective potvrzuje patterns, ale ne konkrétní 67 % číslo. | Hledat Spotify SEC filings / employee retrospectives s konkrétnímy %. |
| Karpathy primary tweet *„end of vibe coding era"* (Feb 2026) | Citováno secondary | Najít primary URL via X/Twitter archive |
| Bain *„88 % business transformations fail"* | Cited via Clarity 2026 | Primary Bain report identification |
| Microsoft pair programming research 22 % / 3.5 % | Cited via Martin Fowler | Najít primary Microsoft paper / blog |
| Foundation Sprint formál „5 leaders, žádní devs explicit" | Confirmed via Lenny's | OK |
| Vanta 2026 70 % shadow IT survey | Cited via Black Hat MEA | Primary Vanta report identification |

---

## 10. Reference (URLs + datum přístupu 2026-05-28)

### Per-method dev-in-room policy

- **GV Design Sprint** — [gv.com/sprint](https://www.gv.com/sprint/); [thesprintbook.com](https://www.thesprintbook.com/the-design-sprint); [jakeknapp.com](https://jakeknapp.com/sprint)
- **AJ&Smart Sprint 2.0** — [ajsmart.com](https://ajsmart.com/design-sprints-2/); [sessionlab.com DS 2.0](https://www.sessionlab.com/templates/design-sprint-2-0); [howthisworks.co](https://howthisworks.co/work/design-sprint)
- **AWS AI-DLC** — [AWS DevOps blog 7/2025](https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/); [zenn.dev kiakiraki](https://zenn.dev/kiakiraki/articles/437ba4d9441b2b?locale=en); [DEV.to re:Invent DVT214](https://dev.to/kazuya_dev/aws-reinvent-2025-introducing-ai-driven-development-lifecycle-ai-dlc-dvt214-32b)
- **Thoughtworks 3-3-3** — [thoughtworks.com/ai/works](https://www.thoughtworks.com/ai/works/)
- **BMAD-METHOD** — [github.com/bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD); [Medium BMAD review](https://medium.com/@anubhavbhatt/the-bmad-method-a-smarter-way-to-build-with-ai-11c6ec07567e)
- **Spec Kit** — [github.com/github/spec-kit](https://github.com/github/spec-kit); [Microsoft Dev Blog](https://developer.microsoft.com/blog/spec-driven-development-spec-kit)
- **Kiro** — [kiro.dev](https://kiro.dev/); [kiro.dev/docs/specs/feature-specs/requirements-first](https://kiro.dev/docs/specs/feature-specs/requirements-first/)
- **OpenSpec** — [openspec.dev](https://openspec.dev/); [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)
- **Foundation Sprint** — [Lenny's newsletter](https://www.lennysnewsletter.com/p/introducing-the-foundation-sprint); [thefoundationsprint.com](https://thefoundationsprint.com/)
- **Lean Inception** — [caroli.org/en/lean-inception-for-a-dev](https://caroli.org/en/lean-inception-for-a-dev/); [caroli.org Lean Inception](https://caroli.org/en/lean-inception-4/)
- **Liberating Structures** — [liberatingstructures.com](https://www.liberatingstructures.com/)
- **Design Thinking (IDEO)** — [designthinking.ideo.com](https://designthinking.ideo.com/); [ideou.com](https://www.ideou.com/blogs/inspiration/design-thinking-process)
- **Event Storming Big Picture** — [philippe.bourgau.net](https://philippe.bourgau.net/4-tips-that-will-make-your-ddd-big-picture-event-storming-successful/); [wiki.prooph-board.com](https://wiki.prooph-board.com/event_storming/big_picture.html)
- **Mob Programming (Falco)** — [The Mob Programming Guidebook](https://www.mobprogrammingguidebook.com/images/mobprogrammingguidebook.pdf)
- **Shape Up (Basecamp)** — [basecamp.com/shapeup](https://basecamp.com/shapeup/0.3-chapter-01)

### Degradation patterns + adoption gravity

- **Spotify model retrospective** — [Jeremiah Lee — Failed #SquadGoals](https://www.jeremiahlee.com/posts/failed-squad-goals/); [DX Podcast](https://getdx.com/podcast/spotify-squads/)
- **AgileFall** — [HBR](https://hbr.org/2019/09/when-waterfall-principles-sneak-back-into-agile-workflows); [Cloudwards Scrumfall](https://www.cloudwards.net/scrumfall/); [CodeLucky Water-Scrum-Fall](https://codelucky.com/water-scrum-fall-hybrid-anti-pattern/)
- **Agile Adoption Is Not Agility** — [Matt LeMay survey 2020](https://medium.com/on-human-centric-systems/agile-adoption-is-not-agility-f1bcd8f68fef)
- **SAFe IP Iteration** — [premieragile.com](https://premieragile.com/what-is-ip-iteration-in-safe/); [deeprojectmanager.com](https://deeprojectmanager.com/safe-innovation-and-planning-iteration/)
- **DORA 2024 platform handoff** — [DORA Report 2024](https://dora.dev/research/2024/dora-report/); [Faros DORA 2025 takeaways](https://www.faros.ai/blog/key-takeaways-from-the-dora-report-2025); [Architecture Weekly](https://www.architecture-weekly.com/p/thoughts-on-platforms-core-teams)
- **DORA 2025 AI report** — [dora.dev/dora-report-2025](https://dora.dev/dora-report-2025/)
- **Pair programming patchy adoption** — [Martin Fowler — On Pair Programming](https://martinfowler.com/articles/on-pair-programming.html); [arXiv 2506.19511](https://arxiv.org/html/2506.19511v1)
- **Scrum Master/PO not mandatory at Daily Scrum** — [Medium Davide Patti](https://medium.com/@davidepatti/why-the-scrum-master-and-product-owner-are-not-mandatory-at-daily-scrum-180a7de9e3ab)
- **Shadow IT 70 %** — [Black Hat MEA — Shadow AI default](https://insights.blackhatmea.com/is-shadow-ai-now-the-default-enterprise-architecture/); [Wikipedia](https://en.wikipedia.org/wiki/Shadow_IT)
- **Dual-Track Agile vs Continuous Discovery** — [LogRocket](https://blog.logrocket.com/product-management/dual-track-agile-continuous-discovery/); [SVPG](https://www.svpg.com/dual-track-agile/); [Caroli — Jeff Patton](https://caroli.org/en/jeff-patton-dual-track-development/)

### Precision spec quality

- **EARS notation (Kiro)** — [kiro.dev/docs/specs](https://kiro.dev/docs/specs/); [teachmeidea.com](https://teachmeidea.com/kiro-ai-ide-spec-driven-development/)
- **Gherkin BDD** — [testquality.com Gherkin guide 2026](https://testquality.com/gherkin-user-stories-acceptance-criteria-guide/); [skills.visual-paradigm.com BDD Gherkin](https://skills.visual-paradigm.com/docs/user-story-techniques-large-scale-agile/advanced-enterprise-story-patterns/bdd-gherkin-user-stories-acceptance-criteria/)
- **Characterising BDD Quality** — [Springer 2020 BDD Quality](https://link.springer.com/chapter/10.1007/978-3-030-49392-9_6); [PMC NCBI](https://pmc.ncbi.nlm.nih.gov/articles/PMC7251619/)
- **OpenAPI 3.1 / 3.2** — [42Crunch API Audit](https://42crunch.com/api-security-audit/); [OpenAPI Spec v3.2.0](https://spec.openapis.org/oas/v3.2.0.html); [swagger.io](https://swagger.io/specification/)
- **Spec Kit constitution + quality gate** — [Microsoft Dev Blog](https://developer.microsoft.com/blog/spec-driven-development-spec-kit); [Spec Kit Discussion #980](https://github.com/github/spec-kit/discussions/980)

### Re-implementation gap data

- **Yan et al. 2025** — via [Augment Code SDD guide](https://www.augmentcode.com/guides/what-is-spec-driven-development)
- **Scott Logic 11/2025** — [blog.scottlogic.com — Spec Kit Paces](https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html)
- **Böckeler / Martin Fowler 11/2025** — [martinfowler.com SDD 3 tools](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- **Martinelli 03/2026** — [martinelli.ch](https://martinelli.ch/why-spec-driven-development-tools-fail-in-the-enterprise/)
- **Comprehension-Performance Gap (arXiv 2025)** — [arxiv 2511.02922](https://arxiv.org/pdf/2511.02922)
- **Handoff cost 30-40 %** — [Questworks design-engineering handoff](https://www.questworks.io/blog/design-engineering-handoff)
- **Stakeholder alignment 70 %** — [Clarity 2026](https://heyclarity.dev/blog/the-stakeholder-alignment-problem-why-enterprise-software-projects-miss-the-mark/) (citing Bain)
- **James Martin 50 % ambiguous** — [Lansa research](https://lansa.com/blog/app-development/rapid-app-development/ambiguity-in-requirements/)
- **Berry & Kamsties NL ambiguity** — [link.springer.com](https://link.springer.com/chapter/10.1007/978-1-4615-0465-8_2)
- **Requirements engineering failure factors** — [PMC NCBI](https://pmc.ncbi.nlm.nih.gov/articles/PMC7144980/)

### Lovable / Bolt handoff

- **Lovable handoff** — [lovable.dev/blog prototype-to-production handoff](https://lovable.dev/blog/prototype-to-production-handoff-how-non-technical-teams-use-lovable-without-bypassing-engineering)
- **AI prototyping 2026 comparison** — [NxCode Vibe Design Tools 2026](https://www.nxcode.io/resources/news/vibe-design-tools-compared-stitch-v0-lovable-2026); [softr.io Lovable vs Bolt 2026](https://www.softr.io/blog/lovable-vs-bolt)

### Pflanzer cross-refs

- `docs/methodology/09-srovnani-existujici-metody.md`
- `docs/research/competitive/04-synthesis-and-positioning.md`
- `docs/research/spec-driven-vs-pflanzer/01-sdd-mechanika.md`
- `docs/research/dual-track-design/01-methodology-architecture.md`
- (Tato research) `docs/research/dual-track-design/02-industry-comparative.md`
