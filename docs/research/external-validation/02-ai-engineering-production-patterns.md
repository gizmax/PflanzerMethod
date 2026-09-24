# External validation #02 — AI engineering production patterns (2024-2026)

> **Účel dokumentu:** intelektuálně poctivý audit veřejných důkazů, které
> podporují (nebo vyvracejí) klíčové claims Pflanzerovy metody. Zaznamenat
> verifikovatelné metriky z industry, ne anecdotal LinkedIn posts.
>
> **Cílový čtenář:** content team (1-pager / website), Method Steward,
> sales (defensible claims), Akademik (falsifiability layer).
>
> **Metodika:** WebSearch + WebFetch, květen 2026. Per finding: URL, datum
> publikace, citát/metrika, strength rating (strong / moderate / weak),
> Pflanzer aspekt potvrzen/vyvrácen.
>
> **Recenze:** v0 (2026-05-18) — initial draft. Doplnit při novém pilotu
> a po N=3 Pflanzer instances pro re-baseline.

---

## TL;DR

### Pět nejsilnějších findings (PRO Pflanzer)

1. **AWS AI-DLC (re:Invent 2025) — Amazon Bedrock case study: 18 měsíců → 76 dní
   se 6 inženýry místo 30.** [strong]
   - Source: AWS DVT214 / AWS DevOps blog, 11-12/2025.
   - „Mob Elaboration" jako Session 1 analog (tým validuje AI návrhy live).
   - Pflanzer claim *„6-9 měsíců → 14 dní, ~10× speedup"* je v té stejné
     řadové třídě (AWS = ~7×, Pflanzer = ~10×). Není to outlier.

2. **Allianz Project Nemo: 100 dní od start k operational deployment v agentic AI
   claims (regulovaná insurance).** [strong]
   - Source: allianz.com news, 11/2025.
   - 80 % reduction in claim processing time (eligible food spoilage <$327).
   - Validuje audit-grade variantu (insurance = AI Act + GDPR + regulační dohled),
     compliance-by-design lze dělat *„rychle a procedurálně"*.

3. **Stripe Minions: 1 300 PRs / týden z AI agenta v produkci,
   10 000-line Scala→Java migrace za 4 dny (odhad 10 engineer-weeks).** [strong]
   - Source: stripe.dev/blog 2025, lennysnewsletter.com 2026.
   - 10 engineer-weeks → 4 dny = **~12×** speed-up. Verifikovaný metrika
     vůči Pflanzer 10× claim.

4. **Spotify Honk + Claude Agent SDK: 650+ AI-merged PRs/month,
   až 90 % reduction v engineering time pro migrations.** [strong]
   - Source: claude.com/customers/spotify, TechCrunch 2/2026.
   - Pflanzer aspekt: *„most code straight to production"* — Spotify
     to v produkci dělá v měřítku.

5. **GitHub Octoverse 2025: 80 % nových developerů používá Copilot
   v prvním týdnu; 1.1M veřejných repo s LLM SDK (+178 % YoY).** [strong]
   - Source: github.blog/news-insights/octoverse 10/2025.
   - Validuje *baseline*: AI-native dev je nyní default, ne experiment.
     Pflanzer žije v zralém prostředí, ne v early-adopter bubble.

### Tři nejsilnější counter-evidence (PROTI Pflanzer claimům)

1. **MIT NANDA: 95 % enterprise GenAI pilotů má zero ROI.** [strong]
   - Source: Fortune 8/2025, MIT NANDA report.
   - $30-40B globální enterprise investice, vrátka zero pro 19 z 20 pilotů.
   - **Pflanzer dopad:** *„most code straight to production"* je v industry
     spíše výjimka než pravidlo. Pflanzer musí umět vysvětlit, proč je v 5 %,
     ne v 95 %.

2. **METR RCT (7/2025): zkušení OSS developeři jsou s AI nástroji **19 % POMALEJŠÍ**,
   ale věří, že jsou o 20 % rychlejší.** [strong]
   - Source: metr.org/blog 7/2025; arxiv:2507.09089.
   - 16 developerů, 246 tasků, RCT design = brutally honest data.
   - **Pflanzer dopad:** stakeholder retrospective („cítili jsme se rychlejší")
     není evidence — Pflanzer pre-registration + lagging metrics
     (ADR-0013) je odpovědí na tento bias, ale industry baseline říká,
     že perception ≠ reality.

3. **GitClear (100M LOC analýza): code churn z 5.5 % na 7.9 % (+39 %),
   refactoring klesl z 25 % (2021) na <10 % (2024).** [strong]
   - Source: byteiota.com / leaddev.com 2025, GitClear analysis.
   - **Pflanzer dopad:** *„most code straight to production"* claim by měl
     **vždy** být doplněn o quality-gate metriku (Pflanzer má score 0-100,
     ale industry baseline ukazuje, že AI kód má 1.7× více issues per PR).

### Klíčové takeaway pro Pflanzer marketing

- **10× speedup claim je obhájitelný**, ale jen v kontextu *„správný typ úkolu × AI-mature org"*.
  Mimo ten context (METR study na zralých OSS projektech) je realita 0.8×, ne 10×.
- **„Most code straight to production" claim je risky bez quality-gate doplnění.**
  Lovable 10.3 % apps má kritické security holes — bez Security/Legal v room
  od minuty 0 je Pflanzer claim falešný marketing.
- **Cross-functional alignment claim je strongest moat.** Industry data
  (MIT, McKinsey) ukazuje, že 70 % failure mode = lidé/proces/kultura, ne technologie.
  Pflanzer řeší přesně toto, ale tu konkrétní hodnotu nikdo ostatní výslovně
  neslibuje (AWS AI-DLC je homogenní eng-only mob; Thoughtworks 3-3-3 je 90 dní).

---

## 1. Industry baseline — co dnes říkají velké reporty

### 1.1 McKinsey „The State of AI" (March + November 2025)

| Metrika | Hodnota | Zdroj |
|---------|---------|-------|
| % firem s AI v ≥1 funkci | 88 % | McKinsey 2025 |
| % firem se scaled enterprise AI | ~33 % | McKinsey 2025 |
| % firem v „pilot purgatory" | ~67 % | McKinsey 2025 |
| % firem attributujících EBIT impact AI | 39 % | McKinsey 2025 |
| % firem s >5 % EBIT z AI (high performers) | ~6 % | McKinsey 2025 |

**Klíčový citát:** *„The blockers to scaling include data quality and
architecture, workflow rigidity, operating model inertia, and measurement gaps."*
([McKinsey, Nov 2025](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai))

**Pflanzer alignment [strong]:** Pflanzer adresuje *„workflow rigidity"* a *„measurement gaps"*
(decision log s lidskou atribucí, score závaznosti per role). Pflanzer však
**neadresuje** *„data quality and architecture"* — to je delivery layer,
ne pilot fixture.

### 1.2 MIT NANDA „GenAI Divide" (8/2025)

| Metrika | Hodnota | Pflanzer dopad |
|---------|---------|----------------|
| % AI pilotů s zero ROI | 95 % | Counter-evidence k „most code to prod" claim |
| % pilotů s rapid revenue acceleration | 5 % | Pflanzer musí být v 5 %, ne v 95 % |
| Internal builds success rate | ~22 % | Pflanzer je hybrid (internal + AI tooling) |
| External vendor partnership success | ~67 % | Pflanzer = tooling partnership (Anthropic, Bolt, Lovable) |
| Globální enterprise GenAI investice 2025 | $30-40B | Velikost trhu pro Pflanzer-style metodologie |

**Klíčový citát:** *„The vast majority stall, delivering little to no measurable
impact on P&L."*
([Fortune, 8/2025](https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/))

**Pflanzer alignment [moderate]:** Pflanzer cross-fn alignment + procurement-ready
compliance artifacts (AI Act decision log, DORA prompt audit) snižují
„internal build" failure rate. Ale claim *„většina kódu rovnou do produkce"*
je v rozporu s 95 % failure mode — Pflanzer to musí vysvětlit lepším
gating, ne handwave-em.

### 1.3 DORA Report 2025 (Google Cloud)

| Metrika | Hodnota | Zdroj |
|---------|---------|-------|
| % respondentů používající AI v práci | 90 % | DORA 2025 |
| % cítí zvýšenou produktivitu | >80 % | DORA 2025 |
| % cítí pozitivní impact na code quality | 59 % | DORA 2025 |
| % s little/no trust v AI generated code | 30 % | DORA 2025 |
| Vztah AI ↔ delivery stability | **NEGATIVNÍ** | DORA 2025 |

**Klíčový citát:** *„AI accelerates software development, but that acceleration
can expose weaknesses downstream. Without robust control systems […], an increase
in change volume leads to instability."*
([Google Cloud, 10/2025](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report))

**Pflanzer alignment [strong]:** Validuje 5. USP (2-session formát + reinforcement
T+7/30/60/90) jako *„control system"* pro AI acceleration. DORA dvouřádkové
*„AI amplifies the quality of the engineering system it operates within"*
je doslovný argument proti Spec Kit / BMAD / vibe-coding-only stack a
**ve prospěch** Pflanzer cross-fn alignmentu.

### 1.4 Stack Overflow Developer Survey 2025

| Metrika | Hodnota | Zdroj |
|---------|---------|-------|
| % vývojářů používajících AI | 84 % (vs 76 % 2024) | SO Survey 2025 |
| % profesionálních devs s AI daily | 51 % | SO Survey 2025 |
| % distrust AI accuracy | 46 % | SO Survey 2025 |
| % trust AI accuracy | 33 % | SO Survey 2025 |
| % „highly trust" AI output | 3 % | SO Survey 2025 |
| % agent users seeing collab improvement | 17 % | SO Survey 2025 |

**Klíčový citát:** *„Only 17% of users agree that agents have improved
collaboration within their team, making it the lowest-rated impact by a
wide margin."*
([Stack Overflow Blog, 12/2025](https://stackoverflow.blog/2025/12/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here/))

**Pflanzer alignment [strong]:** Counter-narrative k AI-as-collaboration-driver
hype. Pflanzer **nedává AI rolí collaboration partnera** — dává jí roli
*„variant generator"*. Cross-fn alignment v Pflanzeru je human-to-human
mediated by AI artifacts, ne human-to-AI collaboration. To je defensible
narrative vůči 17 % číslu.

### 1.5 GitHub Octoverse 2025

| Metrika | Hodnota | Zdroj |
|---------|---------|-------|
| Noví developers na GH 2024-25 | 36M+ (180M total) | Octoverse 2025 |
| % new developers using Copilot v 1. týdnu | 80 % | Octoverse 2025 |
| Repo s LLM SDK | 1.1M | Octoverse 2025 |
| YoY růst LLM-SDK repos | +178 % | Octoverse 2025 |
| Top language 2025 | TypeScript (AI-driven shift) | Octoverse 2025 |

**Pflanzer alignment [strong]:** Validuje, že Pflanzer pluje v hlavním proudu,
ne v early-adopter eddy. Vibe-coding stack (Bolt, v0, Lovable, Claude Code)
nejsou hipster tools — jsou to default tools pro nové developery.

### 1.6 Pragmatic Engineer (Gergely Orosz, 2025-2026)

| Metrika | Hodnota |
|---------|---------|
| % survey respondentů s AI agents regularly | 55 % |
| % Staff+ engineers heavy agent users | 63.5 % |
| % engineers regularly using agents | 49.7 % |
| Claude Code adoption since 5/2025 | #1 tool (přebrala Copilot/Cursor) |

**Klíčový citát:** *„As more software engineers use AI agents daily, there's
also more sloppy software, outages, quality issues, and even a slowdown
in shipping velocity."*
([Pragmatic Engineer, 2026](https://newsletter.pragmaticengineer.com/p/ai-tooling-2026))

**Pflanzer alignment [strong]:** Validuje quality-gate vrstvu Pflanzeru
(score 0-100, pre-flight triage, Security/Legal v room). Industry data
říká, že velocity bez gates → outages.

---

## 2. Per-USP validation

### USP 1: Non-tech role v primary session (organizational moat)

**Pflanzer claim:** Security + Legal/DPO + A11y + UX writer + CS proxy
v místnosti od minuty 0.

**Industry evidence:**

| Source | Finding | Strength |
|--------|---------|----------|
| MIT NANDA | „70 % failure mode = people/process/culture" (BCG 10-20-70 rule cited) | strong |
| McKinsey | „Operating model inertia" je top scaling blocker | strong |
| Platform Engineering 2026 predictions | *„The 'shift left' era is ending; platforms inject controls at infrastructure layer"* | moderate (proti, ale s nuancí) |
| AWS AI-DLC | Mob je BA/PM/eng/QA/ops — **chybí Security/Legal v primary room** | strong (Pflanzer differentiator confirmed) |
| Thoughtworks AI/works | Consulting team + client stakeholders, 90 dní | moderate (delší, nezachycuje 14-day claim) |
| Allianz Project Nemo | „Strictly adheres to compliance and data privacy standards" během 100-day deployment | strong |

**Verdict:** **Confirmed differentiator.** Industry expressně **nemá** Security/Legal
v Session 1. Allianz Project Nemo to dělá compliance-by-design, ale není
to documented metodologie — je to internal consulting playbook.
Pflanzer to dělá **explicit a opakovatelně**.

**Counter-nuance:** Platform Engineering článek říká *„shift left era is ending —
platforms inject controls at infra layer"* (např. Policy-as-Code).
Pflanzer to **nezastupuje**; doplňuje to. Pre-flight triage + role v room =
detect → escalate; platform-injected controls = prevent.

### USP 2: Score závaznosti per role + AI deflation (decision moat)

**Pflanzer claim:** 1-5 Likert s rationale per role per varianta,
Critical/Yellow/Score hierarchie, AI deflation 0.5/1.0, sponzor hlasuje
poslední.

**Industry evidence:**

| Source | Finding | Strength |
|--------|---------|----------|
| Workshop methodology expert (internal research, 5/2026) | Žádný direct competitor v industry | strong |
| AWS AI-DLC | Žádný explicit decision protocol | strong (gap confirmed) |
| Foundation Sprint (Knapp 2025) | Strategic framing, ne implementation decision | moderate |
| Thoughtworks 3-3-3 | Standardní consulting decision frameworks | moderate |
| Stack Overflow 2025 | „46 % distrust AI accuracy" | strong (validuje AI deflation) |
| DORA 2025 | „30 % little/no trust in AI generated code" | strong (validuje AI deflation) |

**Verdict:** **Confirmed protected USP.** Industry trust v AI je nízká,
ale žádná workshop methodology to nepřevádí do quantified rozhodovacího
protokolu. To je 12-18 měsíční moat.

### USP 3: Pre-flight triage 4 tracks (governance moat)

**Pflanzer claim:** Discovery Readiness + Security & Data Triage + Legal & Privacy
Triage + Platform Triage, 48-72 h před S1, blocking gate.

**Industry evidence:**

| Source | Finding | Strength |
|--------|---------|----------|
| BCG „Widening AI Value Gap" 2025 | „Bolting AI onto fragmented architecture fails catastrophically" | strong |
| Banking AI failure analysis | 73 % banking AI initiatives nepřejde pilot stage; data v rozdělených systémech | strong |
| McKinsey 2025 | Workflow rigidity = blocker | strong |
| AWS AI-DLC | „Semantic context building for brownfield projects" — analog Backend Context Pack | moderate (komplement) |
| MIT NANDA | „Generic tools stall in enterprise" — kontextový gap | strong |

**Verdict:** **Confirmed differentiator.** Industry data drsně potvrzuje
need for pre-flight kontextu — žádný direct konkurent to však nemá jako
formalized blocking gate.

### USP 4: Native AI Act / DORA compliance (regulatorní moat)

**Pflanzer claim:** Decision log s human attribution per AI Act čl. 14,
dvoufázový AI Act protokol Fáze A/B/C, DORA-grade 7-letá retence.

**Industry evidence:**

| Source | Finding | Strength |
|--------|---------|----------|
| EU AI Act enforcement | High-risk obligations vstupují 8/2026 (Articles 9-17 provider, 26 deployer) | strong |
| CSA „EU AI Act High-Risk Compliance Deadline" 2025 | >50 % orgs nemá AI inventář; 70 % nemá ongoing monitoring | strong |
| Allianz Project Nemo | „Strictly adheres to compliance and data privacy standards" | strong (case study konkrétní implementation) |
| BCG „A Faster Path to Scaling GenAI in Banking Compliance" | Pre-AI compliance review 3 weeks → AI-assisted 3 days | strong |
| AWS AI-DLC | „No explicit audit trail" | strong (gap confirmed) |
| Thoughtworks AI/works | Enterprise governance vrstva, ale ne out-of-the-box | moderate |

**Verdict:** **Strongest defensible moat.** Industry deadline (8/2026) +
massive readiness gap (70 % no monitoring) + žádný konkurenční metodologie
nemá out-of-the-box compliance artifact = procurement-ready Pflanzer
audit-grade variant je defensible 24-36 měsíců.

### USP 5: 2-session formát + reinforcement (operational moat)

**Pflanzer claim:** S1 vibe (3-6h) → 5-7d async → S2 (3h) → handoff →
T+7/30/60/90.

**Industry evidence:**

| Source | Finding | Strength |
|--------|---------|----------|
| AWS AI-DLC | Continuous „bolts" 3-4h Mob Elaboration — **ne 2-session formát** | strong (gap confirmed) |
| Thoughtworks 3-3-3 | 3 dny concept / 3 týdny prototype / 3 měsíce MVP — 90-day cycle | strong (komplement, ne ekvivalent) |
| Design Sprint (Knapp) | 5 dní non-stop (korporát unavail) | strong (gap confirmed) |
| Foundation Sprint (Knapp 2025) | 2h foundation, ne implementation | strong (komplement) |
| Helium42 / accelerated frameworks | 6-8 týdnů production deployment | moderate (longer than Pflanzer claim) |
| Anthropic / Stripe / Spotify | „Weeks not quarters" production code | strong (validuje claim řádu) |

**Verdict:** **Unique cadence v industry.** 14-day claim je v souladu
s mainstream weeks-not-quarters trendem, ale specifický 2-session +
async + reinforcement format je unique.

---

## 3. Banking / regulated industry case studies (Persona A target)

### 3.1 Goldman Sachs (2025-2026)

- **GS AI Assistant** firmwide po 10 000-employee pilotu (mid-2025).
- **Devin (Cognition):** první major bank s autonomním coding agentem v 12k engineer workforce.
- **3-4× productivity gain** dle internal benchmarks.
- **40 % improvement v time-to-deliver** pro standard coding tasks.
- **15 % reduction post-release bug reports** v legacy modernization.

Source: [BankInfoSecurity](https://www.bankinfosecurity.com/how-goldman-sachs-jpmorgan-aig-are-actually-deploying-ai-a-31643),
[AIExpertNetwork](https://aiexpert.network/ai-at-jpmorgan/)

**Pflanzer dopad [strong]:** Goldman 3-4× je *delivery layer* — Pflanzer pilot layer
nadbíhá podobné metriky (10× pro greenfield feature, 3-5× pro brownfield).
Persona A „CIO velké banky" má Goldman jako external benchmark.

### 3.2 JPMorgan Chase

- **AI coding assistant:** 10-20 % developer efficiency gains.
- **400+ production AI use cases** na enterprise ML platformě.
- **LLM Suite:** 200 000+ employees jako research assistant.
- **40 % automation** investment-banker research tasks.
- **$10T daily transactions** processed s AI v loop.

Source: [Klover.ai](https://www.klover.ai/jpmorgan-uses-ai-agents-10-ways-to-use-ai-in-depth-analysis-2025/)

**Pflanzer dopad [moderate]:** Validuje, že banking-grade compliance + AI
v produkci je možné. Ale JPM má 400+ use cases — to je *portfolio governance*
layer (kde Pflanzer = jeden z mnoha pilots), ne single-feature replace.

### 3.3 Allianz Project Nemo (insurance + agentic AI)

- **100 dní** od start k operational deployment.
- **80 % reduction** v claim processing time pro eligible categories.
- **7-agent workflow** executes <5 minutes per claim.
- **„Strictly adheres to compliance and data privacy standards"** — quote.
- **900+ AI use cases** internally registered.
- **AllianzGPT:** 60 000+ employees.

Source: [Allianz news, 11/2025](https://www.allianz.com/en/mediacenter/news/articles/251103-when-the-storm-clears-so-should-the-claim-queue.html)

**Pflanzer dopad [strong]:** **Best regulated-industry case study analogie.**
Insurance (regulated, GDPR special category data, AI Act limited/high-risk dle
use case) + 100-day delivery + compliance-by-design = doslovný validation
template pro Pflanzer audit-grade profil.

### 3.4 HSBC, AIG (zmiňováno v Lucidate beyond-the-pilot)

Source: [Lucidate](https://www.lucidate.co.uk/post/beyond-the-pilot-how-jpmorgan-goldman-sachs-and-hsbc-are-scaling-ai-to-enterprise-production)

Méně detailních metrik, ale potvrzuje, že banking sector dělá enterprise-grade
AI production. **Pflanzer dopad [weak-moderate]:** referenční name-drop, ne hard metric.

### 3.5 Banking AI failure rates (counter-side)

- **73 %** banking AI initiatives nepřejde pilot ([Gartner cit. Backbase](https://www.backbase.com/blog/ai-native-banking-36-month-window))
- **92 % banks** je v riziku „AI-native fail" (36-month window)
- **Real-time data je problém** — fraud modely na včerejších transakcích = nepoužitelné

**Pflanzer dopad [strong]:** Validuje audit-grade profil potřebu.
Default profil **NESTAČÍ** pro banking — Pflanzer charter explicitně řekne *„audit-grade only pro DORA scope"*.

---

## 4. Digital-native case studies (Persona B target)

### 4.1 Stripe Minions

- **1 300 PRs/týden** merged z AI agentů (mid-2025 disclosed).
- **10 000-line Scala→Java migration ve 4 dnech**, odhad 10 engineer-weeks.
  - = **~12× speedup** verifikovaný metrikou.
- **Claude Code deployment** napříč 1 370 engineers (zero-config enterprise binary).
- **Slack-triggered async PR generation** s automated test gates.

Source: [Stripe.dev blog](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2),
[Lenny's Newsletter](https://www.lennysnewsletter.com/p/how-stripe-built-minionsai-coding),
[Anthropic Claude Code customer page](https://www.anthropic.com/product/claude-code)

**Pflanzer dopad [strong]:** Verifikované 10× speedup metriky existují v industry.
Stripe to dělá pro *brownfield migrations* (sub-task uvnitř velké organizace),
Pflanzer to dělá pro *greenfield feature* (cross-fn alignment + production code).
Ne identical use case, ale stejná order-of-magnitude.

### 4.2 Spotify Honk + Claude Agent SDK

- **650+ AI-merged PRs/month** v produkci.
- **Až 90 % reduction** v engineering time pro code migrations.
- **50+ features shipped 2025** přes AI agent system.
- *„Best developers haven't written a line of code since December"* (TechCrunch 2/2026).
- **Slack-based interface** + sandboxed containers + automated verification.

Source: [Anthropic Spotify case study](https://claude.com/customers/spotify),
[TechCrunch 2/2026](https://techcrunch.com/2026/02/12/spotify-says-its-best-developers-havent-written-a-line-of-code-since-december-thanks-to-ai/)

**Pflanzer dopad [strong]:** *„Most code straight to production"* claim
je v Spotify case study real. Ale **CAVEAT:** Spotify má massive engineering
platform (verification, sandboxes, fleet management); Pflanzer claim v korpu
bez té infrastruktury je nepodložen. Pflanzer musí přidat *„pokud máte
mature CI/CD a quality gates, jinak ne"*.

### 4.3 Vercel v0 customer stories

- **Swapped:** 48h od v0 draft k production, 43 % drop v ticket volume v 5 dnech, $1 400 saved.
- **SeekFast:** customer dashboard v <40 min (vs 2 devs + 1 designer × týden).
- **Vanta:** every PdM má v0 license; non-technical PMs staví prototypy přímo pro zákazníky.
- **Stripe Projects:** John Collison: *„Leading edge is now in vibe deploying"*.

Source: [Vercel blog ship-ai-2025-recap](https://vercel.com/blog/ship-ai-2025-recap),
[SaaStr v0 review](https://www.saastr.com/saastr-ai-app-of-the-week-v0-by-vercel-the-vibe-coding-tool-that-4-million-people-use-to-ship-real-software-not-just-demos/)

**Pflanzer dopad [strong]:** *„Funkční prototyp v session"* claim
(Pflanzer S1) má v industry direct analog. Vanta *„every PdM má v0 license"*
je intermediate pattern — ne workshop methodology, ale democratized prototyping.
Pflanzer differentiator = **cross-fn alignment**, ne demokratizace.

### 4.4 Anthropic interní

- **~90 % production code** Claude Code je written by/with Claude Code.
- **Daily deploys** internal; weekday releases external.
- **Continuous shipping** model.

Source: [Anthropic „How AI is transforming work at Anthropic"](https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic),
[Anthropic Claude Code product page](https://www.anthropic.com/product/claude-code)

**Pflanzer dopad [moderate]:** Self-referential (Anthropic používá svoji vlastní AI).
N=1, ale order-of-magnitude číslo (90 % code by/with AI) je dramatic
end-state ukazatel. Pflanzer claim *„most code straight to production"*
sedí v rozumné middle position mezi MIT 95 % failure a Anthropic 90 % AI-written.

---

## 5. AWS AI-DLC, Thoughtworks 3-3-3, AI workshop family (direct competitors)

### 5.1 AWS AI-DLC (re:Invent 2025, DVT214)

**Pflanzer-relevant claims:**
- **10-15× productivity gains** dle AWS.
- **40-60 % improvement** v development velocity.
- **40-60 % reduction** v defects.
- **300-500 % ROI within 12 months** (verified).
- **Amazon Bedrock case:** 18 měsíců / 30 developers → 76 dní / 6 inženýrů.
- **Wipro:** 4 distribuované moduly za 20 hodin.
- **Dun (fintech):** new application za 48h, launched následující týden.

Source: [AWS DevOps blog AI-DLC](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/),
[AWS re:Invent DVT214](https://www.antstack.com/talks/reinvent25/aws-reinvent-2025---introducing-ai-driven-development-lifecycle-ai-dlc-dvt214/),
[Open-sourcing adaptive workflows](https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/)

**Pflanzer dopad [strong, mixed]:**
- **Validates** order-of-magnitude (10-15× gain claim) — Pflanzer 10× není outlier.
- **Validates** „mob elaboration" jako Session 1 mechanika.
- **Competes:** AWS AI-DLC je direct competitor; Pflanzer differentiator = non-tech roles, 2-session formát, AI Act/DORA out-of-box, score závaznosti.

### 5.2 Thoughtworks AI/works + 3-3-3

**Pflanzer-relevant claims:**
- **3 dny concept / 3 týdny prototype / 3 měsíce MVP.**
- Idea → production v 90 dnech.
- Industrial-grade systems delivery.

Source: [Thoughtworks AI/works page](https://www.thoughtworks.com/ai/works/),
[Thoughtworks news 2026](https://www.thoughtworks.com/about-us/news/2026/ai-works-heralds-new-era-of-agile-and-next-generation-software-development)

**Pflanzer dopad [moderate]:**
- **Validates** weeks/months scale (3 týdny prototype ≈ Pflanzer 14 dny).
- **Differs:** Thoughtworks = consulting engagement model ($1M-$10M typical), Pflanzer = DIY methodology / tool.
- **Differs:** 90-day full cycle je 6× longer než Pflanzer default.

### 5.3 Foundation Sprint (Knapp 2025)

- 2-day workshop, strategic framing před implementation.
- Compresses *„months of work into 2 days"* per Knapp marketing.
- Komplement, ne competitor (per `09-srovnani-existujici-metody.md`).

Source: [Lenny's Newsletter podcast](https://www.lennysnewsletter.com/p/the-foundation-sprint-jake-knapp-and-john-zeratsky),
[thefoundationsprint.com](https://thefoundationsprint.com/),
*Click* book (April 2025).

**Pflanzer dopad [moderate]:** Foundation Sprint = pre-step. Pflanzer
Charter může explicitně přijmout Foundation Sprint výstup jako input.
Není to alternativa, je to komplement.

### 5.4 IBM Bob (Apr 2026)

- IBM-launched AI development partner.
- *„10× faster architecture analysis"*, 100 % accuracy v legacy JCL/PL/I documenting.
- Enterprise-focused.

Source: [IBM Bob announcement](https://newsroom.ibm.com/2026-04-28-introducing-ibm-bob-ai-development-partner-that-takes-enterprises-from-ai-assisted-coding-to-production-ready-software)

**Pflanzer dopad [moderate]:** Další 10× claim v industry — Pflanzer 10× není unicorn,
ale v industry context je řád dimension běžný.

---

## 6. Counter-evidence (intelektuálně poctivý audit)

### 6.1 METR RCT „19 % slowdown" (7/2025)

- **16 zkušených OSS developers**, **246 tasků**, RCT design.
- AI-allowed cohort **19 % POMALEJŠÍ** než AI-disallowed.
- Subjective belief: *„20 % faster"* — perception gap.
- Developers expected AI by speed up 24 %; reality -19 %.

Source: [METR blog 7/2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/),
[arxiv:2507.09089](https://arxiv.org/abs/2507.09089)

**Pflanzer counter-narrative [strong]:**
- Pflanzer claim *„10× speedup"* je pro **greenfield cross-fn problem
  v korporátu** (kde sériový handoff = baseline 6-9 měsíců).
- METR měřil **brownfield maintenance task** zkušených OSS contributors
  na **mature, well-understood codebases**.
- **Both findings can be true simultaneously** — Pflanzer není zpochybněno METRem,
  ale **NESMÍ** claim *„10× faster"* aplikovat na maintenance work.
- **Honest framing:** *„Pflanzer 10× faster pro cross-fn alignment + greenfield
  feature. Pro mature codebase maintenance může být AI dokonce slowdown
  (METR 2025). Pflanzer adresuje ten první context, ne ten druhý."*

### 6.2 GitClear „code churn +39 %" (2025)

- 100M LOC analysis, code churn z 5.5 % na 7.9 %.
- Refactoring decline 25 % (2021) → <10 % (2024).
- Copy-paste +48 %.

Source: [byteiota.com](https://byteiota.com/ai-technical-debt-30-41-increase-hits-developers/),
[LeadDev technical-direction](https://leaddev.com/technical-direction/how-ai-generated-code-accelerates-technical-debt)

**Pflanzer counter-narrative [strong]:**
- *„Most code straight to production"* claim je v korelaci s churn risk.
- Pflanzer **MUSÍ** explicit říct: *„Default profil = quality gate score
  ≥80/100; bez toho je claim falešný."*
- Audit-grade profil: review track T+7 redbug-fixing window addresses churn directly.

### 6.3 Lovable security vulnerabilities (10.3 % apps critical)

- 1 645 Lovable-generated apps skenováno.
- **170 (10.3 %) měly critical security vulnerabilities.**

Source: [VentureBeat „Vibe coding tools must fix"](https://venturebeat.com/ai/from-prototype-to-production-what-vibe-coding-tools-must-fix-for-enterprise),
[Retool blog „Risks of vibe coding"](https://retool.com/blog/vibe-coding-risks)

**Pflanzer counter-narrative [strong]:**
- Pflanzer S1 vibe-coding používá Bolt/v0/Lovable — to JE risk surface.
- **Mitigation v Pflanzer:** Security v room od minuty 0 (USP 1) + quality gate score (handoff) + audit-grade variantu pre-flight Security & Data Triage.
- **Honest framing:** *„Vibe-coding tools alone ≠ production. Pflanzer je tady přesně proto, že vibe-coding alone nefunguje."*

### 6.4 Klarna AI rollback (2024 → 2025-2026)

- 2/2024: AI assistant handling 2.3M chats, 67 % automation, work of 700 FTE, $40M projected savings.
- Resolution time 11 min → 2 min.
- 2025: hallucinations on ~5 % conversations, CSAT drops on complex/emotional tickets.
- Klarna quietly reintroduced human capacity.
- 2026: hybrid model, AI handles routine + human handles complex.

Source: [PromptLayer Klarna analysis](https://blog.promptlayer.com/klarna-customer-service-from-ai-first-to-human-hybrid-balance/),
[ChadBockius case study](https://chadbockius.com/case-studies/klarna/),
[CXToday](https://www.cxtoday.com/contact-center/klarnas-ai-merry-go-round-enough-to-put-anyones-head-in-a-spin/),
[Klarna press 2/2024](https://www.klarna.com/international/press/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month/)

**Pflanzer counter-narrative [strong]:**
- Klarna **NEPOUŽIL Pflanzer-style metodologii** — byla to top-down product
  rollout bez cross-fn pre-flight triage CSAT impact assessment.
- *„Most code straight to production"* claim **nevylučuje hybrid rollback** —
  Pflanzer reinforcement T+7/30/60/90 je explicit *„watch for degradation"* phase.
- **Honest framing:** *„Klarna je důvod, proč Pflanzer nedělá AI replacement —
  Pflanzer dělá AI augmentation s human-attributed decision log od minuty 0."*
- Klarna 2024 zpočátku vypadala jako *„AI win"*, ale 12-měsíční lagging metric ji vyvrátila.
  Pflanzer ADR-0013 pre-registration + T+90 lagging metric protocol je explicit
  odpověď na tento failure mode.

### 6.5 73 % banking AI nepřejde pilot

- Gartner cited via Backbase: 73 % banking AI initiatives nepřejde pilot stage.
- Data v rozdělených systémech = týdny práce jen na pochopení polí.

Source: [Backbase „AI-native banking 36-month window"](https://www.backbase.com/blog/ai-native-banking-36-month-window),
[Oradian](https://oradian.com/insights/public/why-your-banks-ai-pilot-failed-and-how-to-fix-it/)

**Pflanzer counter-narrative [strong]:**
- Banking pilot purgatory je **největší market opportunity** Pflanzer audit-grade.
- **Honest framing:** *„Pflanzer není silver bullet pro 73 % failure rate.
  Pflanzer je opakovatelná fixture pro AI CoE pilot portfolio — pomáhá to
  jen, pokud tato vrstva v organizaci existuje a má mandate."*

### 6.6 Spotify caveat — *„best devs haven't coded since December"*

- TechCrunch quote impressive, ale **CAVEAT**: jen *„best developers"*, ne celý team.
- Spotify investoval **roky** do Fleet Management infrastruktury, sandboxed containers, automated verification.

**Pflanzer counter-narrative [moderate]:**
- *„Most code straight to production"* claim platí **jen v org s zralou platform infrastrukturou**.
- Korporátní cílový zákazník Pflanzeru často **tu zralost nemá** — Pflanzer
  pre-flight Platform Triage to detect, ale nesupplánuje.
- **Honest framing:** *„Pflanzer assumes mature CI/CD a quality gates. Pokud
  je nemáte, Pflanzer doporučí předřazený Platform Triage před první sessions."*

---

## 7. „Citable on website / 1-pager" — quotes hotové k vložení

Vybraná z verifikovaných sources. **Vždy** doplnit URL.

### 7.1 Pro „weeks not quarters" claim

> *„Engineering teams are using Claude Code to ship production software for major
> companies in weeks, not quarters."*
> — Anthropic, *Claude Code customer page*, 2025-2026.

### 7.2 Pro 10× / order-of-magnitude

> *„18 months of work for 30 developers […] a team of 6 engineers delivered
> the project in 76 days."*
> — AWS, AI-DLC re:Invent DVT214, 12/2025 (Amazon Bedrock case).

> *„One team completed a 10,000-line Scala-to-Java migration in four days,
> work estimated at ten engineer-weeks."*
> — Stripe / Anthropic Claude Code case study, 2025.

### 7.3 Pro „most code straight to production"

> *„Spotify's agent generates more than 650 monthly pull requests merged
> into production, saving engineers up to 90% of the time they'd spend
> writing migrations manually."*
> — Anthropic, Spotify customer story, 2025.

> *„About 90% of the tool's production code is written by or with Claude Code."*
> — Anthropic, *How AI is transforming work at Anthropic*, 2025.

### 7.4 Pro cross-functional alignment (Pflanzer USP 1)

> *„The blockers to scaling include data quality and architecture, workflow
> rigidity, operating model inertia, and measurement gaps."*
> — McKinsey, *The State of AI 2025*, November 2025.

> *„Only 17% of [AI agent] users agree that agents have improved collaboration
> within their team, making it the lowest-rated impact by a wide margin."*
> — Stack Overflow, *Developer Survey 2025*, 12/2025.

### 7.5 Pro audit-grade compliance moat (Pflanzer USP 4)

> *„More than half of organizations have not established systematic inventories
> of the AI systems they operate — the minimum prerequisite for any compliance
> program. 47% of organizations have an AI risk management framework, yet 70%
> lack ongoing monitoring and controls."*
> — CSA, *EU AI Act High-Risk Compliance Deadline*, 2025.

> *„August 2, 2026 is the binding enforcement date for high-risk AI system
> obligations under the EU AI Act."*
> — Cooley, *EU AI Act Proposed Digital Omnibus*, 11/2025.

### 7.6 Pro counter-evidence honesty (přidat na *Limitations* sekci 1-pageru)

> *„95% of organisations report zero return on the [GenAI] initiatives."*
> — MIT NANDA, *The GenAI Divide: State of AI in Business 2025*, 8/2025.

> *„When developers are allowed to use AI tools, they take 19% longer to
> complete issues."*
> — METR, *Measuring the Impact of Early-2025 AI on Experienced OSS Developer
> Productivity*, 7/2025.

### 7.7 Pro „funkční prototyp" claim

> *„Vibe design tools let product managers generate visual prototypes in real
> time during meetings, turning 'What if the dashboard had a sidebar?' into
> a live demo in 30 seconds rather than a spec that needs to be designed and
> built over the next sprint."*
> — NxCode, *Vibe Design Tools 2026 comparison*, 2026.

---

## 8. Industry baseline metrics — jak dlouho trvá AI feature dnes?

Pflanzer claim *„6-9 měsíců → 14 dní (~10× speedup)"* potřebuje baseline.

| Org / Source | Baseline | After-AI | Ratio |
|--------------|----------|----------|-------|
| Amazon Bedrock (AWS AI-DLC) | 18 měsíců / 30 devs | 76 dní / 6 inženýrů | ~7× (time) / ~35× (engineer-months) |
| Stripe Scala→Java migration | ~10 engineer-weeks | 4 days | ~12× |
| BCG global bank risk-review | 3 weeks | 3 days | ~7× |
| Vodafone Ireland (ServiceNow) | „weeks" | „days" | ~5-10× |
| Vodafone-Zinkworks RIC | „months" | 3-4 weeks | ~3-6× |
| Allianz claims (Nemo) | „several days" | <1 day | ~5-10× |
| Helium42 accelerated framework | 20-24 weeks | 6-8 weeks | ~3-4× |
| Lyft customer service resolution | (baseline N/A) | -87 % time | ~7× |
| Klarna AI resolution time | 11 min | 2 min | ~5× |
| Goldman Sachs developer time-to-deliver | (baseline N/A) | -40 % | ~1.7× |
| JPMorgan code dev efficiency | (baseline N/A) | +10-20 % | ~1.1-1.2× |

**Aggregate trend:** Industry verified ratios range from **~1.2× (developer
efficiency)** přes **~5-10× (specific workflows)** k **~12× (Stripe Scala migration)**.
Pflanzer 10× claim je v této řadě **legitimate**, ale **na horním okraji**.
**Defensible framing:** *„Order of magnitude faster (5-12×), in line with AWS AI-DLC,
Stripe and Vodafone published benchmarks; specific multiple depends on context."*

---

## 9. Pflanzer-aligned patterns reported jinde (sběr signal)

Hledali jsme firmy publikované přesné Pflanzer-style claims. Findings:

### 9.1 *„Týden místo měsíců"* / *„dny místo týdnů"*

- **AWS AI-DLC Dun (fintech):** *„new application in 48 hours and launched the following week"* [strong]
- **AWS AI-DLC Wipro:** *„4 distributed modules across teams and time zones in just 20 hours"* [strong]
- **Vodafone Ireland (ServiceNow):** *„600 customers and 28 products in days rather than weeks"* [moderate]
- **BCG global bank compliance:** *„3 weeks to 3 days"* [strong]
- **Stripe Slack→PR:** *„An engineer sends a message in Slack, walks away, and comes back to a finished pull request"* [strong]

### 9.2 *„Cross-functional alignment v jedné místnosti"*

- **NEFOUND v direct citation.** Pflanzer USP 1 zůstává unique claim.
- Closest analog: AWS AI-DLC „mob elaboration" — ale jen pro eng-only mob.
- Closest analog: Allianz Nemo „compliance-by-design" — ale je to internal practice, ne published methodology.

### 9.3 *„AI Act compliance od začátku"*

- **NEFOUND v direct citation pro methodology level.**
- Allianz Project Nemo se přibližuje, ale je to point-solution, ne reusable fixture.
- Hogan Lovells ELTEMATE Regulatory Pilot — drafts technical documentation pro
  AI Act, ale jako standalone consultative tool, ne workshop methodology.

Source: [Hogan Lovells ELTEMATE](https://www.hoganlovells.com/en/case-studies/transforming-global-regulatory-compliance-with-eltemates-ai-powered-regulatory-pilot)

### 9.4 *„Design Sprint nás zklamal — funkční prototyp v session změnil výsledek"*

- **NEFOUND v exact citation.**
- Closest: Vanta *„Every PdM has v0 license […] non-technical PMs are building
  interactive prototypes and putting them in front of customers"* — demokratizace,
  ne Pflanzer style.
- Closest: NxCode review *„live demo in 30 seconds rather than a spec that needs
  to be designed and built over the next sprint"* — anti-Figma sentiment confirmed.

### 9.5 *„Security review od minuty 0, ne na konci sprintu"*

- **NEFOUND explicit citation.**
- Closest: Platform Engineering 2026 predictions *„the 'shift left' era is ending,
  platforms inject controls at infrastructure layer"* — different mechanism.
- Pflanzer claim **zůstává unique**: human-in-room ≠ platform-as-code.

---

## 10. Industry expert / conference signals

### 10.1 Anthropic Builder Summit (Paris 2/2025, London 10/2025)

- [Paris summit](https://www.anthropic.com/events/paris-builder-summit)
- [London summit](https://www.anthropic.com/events/london-builder-summit-2025)
- [Bengaluru](https://www.anthropic.com/events/builder-summit-bengaluru)

**Findings:** Specific Pflanzer-aligned talks **nenalezeny** v indexovaných veřejných materiálech.

### 10.2 Vercel Ship AI 2025

- [Recap](https://vercel.com/blog/ship-ai-2025-recap)
- John Collison (Stripe) keynote: *„The leading edge is now in vibe deploying."*

### 10.3 Anthropic 2026 Developer Conference („Code with Claude")

- [Every.to coverage](https://every.to/chain-of-thought/inside-anthropic-s-2026-developer-conference)
- [Dotzlaw analysis](https://www.dotzlaw.com/insights/anthropic-2026-code-with-claude/)

### 10.4 AWS re:Invent 2025 — DVT214 (Introducing AI-DLC)

- [DVT214 slides](https://www.antstack.com/talks/reinvent25/aws-reinvent-2025---introducing-ai-driven-development-lifecycle-ai-dlc-dvt214/)

### 10.5 InfoQ industry coverage

- [QConSF 2025 — Developing Claude Code at Anthropic at AI Speed](https://www.infoq.com/news/2025/11/claude-ai-speed/)
- [AI is Amplifying Software Engineering Performance, Says the 2025 DORA Report](https://www.infoq.com/news/2026/03/ai-dora-report/)
- [AI-Generated Code Creates New Wave of Technical Debt](https://www.infoq.com/news/2025/11/ai-code-technical-debt/)
- [From Prompts to Production: a Playbook for Agentic Development](https://www.infoq.com/articles/prompts-to-production-playbook-for-agentic-development/)

---

## 11. Verdikt per Pflanzer claim

| Pflanzer claim | Industry support | Verdict | Doporučená marketing formulace |
|----------------|------------------|---------|--------------------------------|
| **Time-to-prod 6-9 měsíců → 14 dní (~10× speedup)** | Strong (AWS, Stripe, BCG, Allianz, IBM Bob) | **Defensible**, ale jen v greenfield + AI-mature org | *„Order of magnitude faster — in line with AWS AI-DLC, Stripe and BCG benchmarks; specific multiple depends on context."* |
| **6 lidí cross-functional v 1 místnosti** | Moderate (Allianz interní, AWS eng-only mob) | **Confirmed differentiator** — non-tech v room je unique | *„Security a Legal v místnosti od minuty 0 — to v industry nikdo jiný explicitně nedělá."* |
| **AI vibe-coding 3 paralelní varianty** | Strong (NxCode, Vercel v0, Lovable, Cursor /best-of-n) | **Commoditized enabler**, ne USP | Demote z primary USP claim. |
| **80 % default / 20 % audit-grade** | Strong (AI Act enforcement 8/2026, CSA readiness gap, DORA, regulated industries) | **Confirmed market segmentation** | *„AI Act enforces high-risk obligations 8/2026; 70 % organizací nemá monitoring — Pflanzer audit-grade variant je out-of-the-box."* |
| **T+7/30/60/90 reinforcement** | Strong (Klarna lagging metric failure, METR perception gap, DORA delivery stability) | **Confirmed differentiator** | *„Reinforcement loop je odpovědí na Klarna-style 12-měsíční rollback risk."* |
| **Most code straight to production** | Mixed (Spotify, Anthropic interní YES; MIT 95 % failure, GitClear churn NO) | **Conditional claim** — nutno doplnit quality gate, jinak misleading | *„Pflanzer winner kód: score ≥80/100 quality gate, exportable to target repo. Bez gating je tento claim falešný."* |
| **Decider's call anti-HiPPO** | Moderate (Design Sprint precedent, Liberating Structures, no AI workshop competitor) | **Confirmed differentiator** v AI workshop family | *„Anti-HiPPO není novinka, ale v AI workshop family ji nikdo jiný nemá."* |

---

## 12. Doporučení pro 1-pager / website

### 12.1 Co změnit

1. **Demote vibe-coding USP claim.** Industry to commoditizovala. Pflanzer
   moat je non-tech in room + AI Act/DORA, ne vibe-coding.
2. **Přidat quality-gate disclaimer.** „Most code straight to production"
   bez score ≥80 je sales lying. Doplnit gate metriku.
3. **Přidat *„Inspired by / Compatible with"* sekci.** Referenced AWS AI-DLC,
   Foundation Sprint (komplement pre-step), Stripe Minions (handoff target).
4. **Přidat *„Honest Limitations"* box.**
   - METR study: 19 % slowdown pro maintenance work.
   - MIT NANDA: 95 % pilots fail.
   - GitClear: code churn +39 %.
   - „Pflanzer je v 5 % winning side **pokud** quality gates, cross-fn alignment,
     a pre-flight triage jsou respected. Bez nich Pflanzer **negarantuje** úspěch."

### 12.2 Co posílit

1. **„AI Act enforcement 8/2026" hook.** Procurement-ready audit-grade fixture
   je unique market position.
2. **„Klarna failure mode covered" hook.** T+90 reinforcement layer je
   explicit protection proti 12-měsíční rollback risk.
3. **„AWS AI-DLC compatible / extended" hook.** Pflanzer rozšiřuje
   eng-only mob na non-tech roles + 2-session formát + compliance.

### 12.3 Co odstranit

1. *„Most code straight to production"* bez quality-gate qualifier.
2. *„AI vibe-coding"* jako primary USP claim (commoditized).
3. *„Funkční kód místo Figmy"* jako primary USP (commoditized — Lovable / v0 dělají).

---

## 13. Open questions pro další research

- [ ] **e-shop veřejné publikace 2024-2026.** Hledali jsme engineering blog,
  konference talks, LinkedIn posts CTO/VP Engineering — **NEFOUND** v indexed
  search. Doporučujeme přímo kontaktovat e-shop lead / Tom Pflanzer
  pro internal artifact.
- [ ] **Rohlik Group, Productboard, Pricerunner.** Engineering blog signals
  o AI workflow — **NEFOUND** v základním sweep. Doporučujeme dedicated
  research pass pro CZ/CE digital-native.
- [ ] **Gartner / Forrester reports.** Většina je za paywall; abstract-level
  data covered via secondary sources. Pokud Pflanzer projde pilot N=3,
  paywall reports access for citable Gartner Magic Quadrant inclusion.
- [ ] **State of DevOps 2025 (Puppet/Forrester).** Hledali jsme,
  nepřinesly se konkrétní AI-workshop relevant metriky. Re-search pro v0.4.
- [ ] **GitLab benchmarks AI integrations.** Anthropic case study existuje,
  ale GitLab nemá specific „developer hours saved" metriku v public docs.
- [ ] **PwC + Anthropic partnership** ([news](https://www.anthropic.com/news/pwc-expanded-partnership)).
  Detail engagement model nezveřejněn — potenciální komplement Pflanzer
  pro Persona A (Big-4 channel partner).

---

## 14. Reference (full list)

### Industry baseline reports

- [McKinsey „The State of AI 2025"](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai)
- [McKinsey „State of AI" — Allianz Direct case study](https://www.mckinsey.com/capabilities/tech-and-ai/how-we-help-clients/rewired-in-action/allianz-direct-advancing-as-europes-leading-digital-insurer)
- [MIT NANDA „GenAI Divide" — Fortune coverage](https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/)
- [DORA 2025 Report — Google Cloud](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)
- [DORA dora.dev official](https://dora.dev/dora-report-2025/)
- [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/2025/ai)
- [Stack Overflow blog summary](https://stackoverflow.blog/2025/12/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here/)
- [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)
- [BCG „The Widening AI Value Gap" 2025](https://media-publications.bcg.com/The-Widening-AI-Value-Gap-October-2025.pdf)
- [BCG „A Faster Path to Scaling GenAI in Banking Compliance"](https://www.bcg.com/publications/2025/a-faster-path-to-scaling-genai-in-banking-compliance)
- [OpenAI „State of Enterprise AI 2025"](https://cdn.openai.com/pdf/7ef17d82-96bf-4dd1-9df2-228f7f377a29/the-state-of-enterprise-ai_2025-report.pdf)
- [Wharton AI Adoption Report 2025](https://ai.wharton.upenn.edu/wp-content/uploads/2025/10/2025-Wharton-GBK-AI-Adoption-Report_Full-Report.pdf)
- [Menlo Ventures „2025 State of Generative AI in the Enterprise"](https://menlovc.com/perspective/2025-the-state-of-generative-ai-in-the-enterprise/)

### Methodologies & competitors

- [AWS AI-DLC introduction (DevOps blog)](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)
- [AWS re:Invent DVT214 — AI-DLC announcement](https://dev.to/kazuya_dev/aws-reinvent-2025-introducing-ai-driven-development-lifecycle-ai-dlc-dvt214-32b)
- [AWS open-sourcing adaptive workflows for AI-DLC](https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/)
- [Thoughtworks AI/works platform + 3-3-3](https://www.thoughtworks.com/ai/works/)
- [Thoughtworks 2026 announcement](https://www.thoughtworks.com/about-us/news/2026/ai-works-heralds-new-era-of-agile-and-next-generation-software-development)
- [Thoughtworks „Beyond vibe coding — 5 building blocks"](https://www.thoughtworks.com/insights/blog/generative-ai/beyond-vibe-coding-the-five-building-blocks-of-aI-native-engineering)
- [Foundation Sprint — thefoundationsprint.com](https://thefoundationsprint.com/)
- [Lenny's Newsletter — Foundation Sprint interview](https://www.lennysnewsletter.com/p/the-foundation-sprint-jake-knapp-and-john-zeratsky)
- [IBM Bob announcement (4/2026)](https://newsroom.ibm.com/2026-04-28-introducing-ibm-bob-ai-development-partner-that-takes-enterprises-from-ai-assisted-coding-to-production-ready-software)

### Customer / case studies

- [Anthropic Spotify case study](https://claude.com/customers/spotify)
- [Anthropic Claude Code customer page](https://www.anthropic.com/product/claude-code)
- [Anthropic GitLab customer story](https://claude.com/customers/gitlab)
- [TechCrunch Spotify (2/2026)](https://techcrunch.com/2026/02/12/spotify-says-its-best-developers-havent-written-a-line-of-code-since-december-thanks-to-ai/)
- [InfoQ — Claude Code at AI Speed (QConSF 2025)](https://www.infoq.com/news/2025/11/claude-ai-speed/)
- [Lenny's Newsletter — Stripe Minions](https://www.lennysnewsletter.com/p/how-stripe-built-minionsai-coding)
- [Stripe.dev blog — Minions Part 2](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2)
- [MindStudio — AI Agent Harness analysis](https://www.mindstudio.ai/blog/what-is-ai-agent-harness-stripe-minions)
- [Vercel Ship AI 2025 recap](https://vercel.com/blog/ship-ai-2025-recap)
- [Vercel — introducing the new v0](https://vercel.com/blog/introducing-the-new-v0)
- [SaaStr v0 review](https://www.saastr.com/saastr-ai-app-of-the-week-v0-by-vercel-the-vibe-coding-tool-that-4-million-people-use-to-ship-real-software-not-just-demos/)
- [Allianz Project Nemo (11/2025)](https://www.allianz.com/en/mediacenter/news/articles/251103-when-the-storm-clears-so-should-the-claim-queue.html)
- [Allianz AI scaling (1/2025)](https://www.allianz.com/en/mediacenter/news/interviews/250129-ai-at-allianz-scaling-ai-to-transform-insurance.html)
- [Allianz AllianzGPT impact (2/2025)](https://www.allianz.com/en/mediacenter/news/articles/250218-ai-at-allianz-the-impact-of-allianzgpt.html)
- [JPMorgan AI deployment — AIX](https://aiexpert.network/ai-at-jpmorgan/)
- [Goldman Sachs / JPM / AIG AI deployment](https://www.bankinfosecurity.com/how-goldman-sachs-jpmorgan-aig-are-actually-deploying-ai-a-31643)
- [Lucidate — beyond the pilot (JPM/GS/HSBC)](https://www.lucidate.co.uk/post/beyond-the-pilot-how-jpmorgan-goldman-sachs-and-hsbc-are-scaling-ai-to-enterprise-production)
- [Lyft Anthropic partnership](https://www.lyft.com/blog/posts/lyft-and-anthropic-team-up-to-redefine-customer-obsessed-ai)
- [Lyft Anthropic case study (CX Dive)](https://www.customerexperiencedive.com/news/lyft-deploys-anthropic-generative-ai-customer-service/739486/)
- [Vodafone-Zinkworks Rapid RIC](https://www.vodafone.com/news/technology/vodafone-and-zinkworks-partner-to-create-ai-platform-to-simplify-and-accelerate-launch-of-new-mobile-network-apps-for-customers)
- [Vodafone-ServiceNow](https://www.vodafone.com/news/technology/vodafone-business-and-service-now-collaborate-to-enhance-the-customer-experience-with-ai-powered-service-automation)
- [Vodafone Microsoft Azure AI](https://www.microsoft.com/en/customers/story/1770174778560829849-vodafone-group-azure-telecommunications-en-united-kingdom)

### Klarna (counter-evidence)

- [Klarna press 2/2024 — initial launch](https://www.klarna.com/international/press/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month/)
- [PromptLayer — Klarna hybrid analysis](https://blog.promptlayer.com/klarna-customer-service-from-ai-first-to-human-hybrid-balance/)
- [Chad Bockius — Klarna case study](https://chadbockius.com/case-studies/klarna/)
- [CXToday — Klarna AI merry-go-round](https://www.cxtoday.com/contact-center/klarnas-ai-merry-go-round-enough-to-put-anyones-head-in-a-spin/)
- [Lasoft — Klarna walks back AI](https://lasoft.org/blog/klarna-walks-back-ai-overhaul-rehires-staff-after-customer-service-backlash/)
- [Digital Applied — Klarna reverses AI layoffs](https://www.digitalapplied.com/blog/klarna-reverses-ai-layoffs-replacing-700-workers-backfired)

### Counter-evidence (productivity, technical debt)

- [METR — 2025 RCT 19% slowdown](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)
- [METR — Updated experiment design (2/2026)](https://metr.org/blog/2026-02-24-uplift-update/)
- [arxiv:2507.09089 — METR paper](https://arxiv.org/abs/2507.09089)
- [Simon Willison — METR commentary](https://simonwillison.net/2025/Jul/12/ai-open-source-productivity/)
- [GitClear analysis — byteiota](https://byteiota.com/ai-technical-debt-30-41-increase-hits-developers/)
- [LeadDev — AI generated code accelerates tech debt](https://leaddev.com/technical-direction/how-ai-generated-code-accelerates-technical-debt)
- [InfoQ — AI-generated code creates new wave of tech debt](https://www.infoq.com/news/2025/11/ai-code-technical-debt/)
- [Tembo — AI technical debt](https://www.tembo.io/blog/ai-technical-debt)
- [Augment Code — AI tech debt compounds, spec-driven dev](https://www.augmentcode.com/guides/ai-technical-debt-compounds-spec-driven-development)

### Vibe coding (industry analysis)

- [VentureBeat — vibe coding tools must fix](https://venturebeat.com/ai/from-prototype-to-production-what-vibe-coding-tools-must-fix-for-enterprise)
- [Capgemini — vibe coding ready?](https://www.capgemini.com/insights/expert-perspectives/from-prototypes-to-production-is-vibe-coding-ready/)
- [Retool — risks of vibe coding](https://retool.com/blog/vibe-coding-risks)
- [ISACA — is vibe coding ready for prime time?](https://www.isaca.org/resources/news-and-trends/isaca-now-blog/2025/is-vibe-coding-ready-for-prime-time)
- [NxCode — vibe design tools 2026](https://www.nxcode.io/resources/news/vibe-design-tools-compared-stitch-v0-lovable-2026)
- [Wikipedia — vibe coding](https://en.wikipedia.org/wiki/Vibe_coding)

### Banking AI pilot failure

- [Backbase — AI-native banking 36-month window](https://www.backbase.com/blog/ai-native-banking-36-month-window)
- [Oradian — bank AI pilot failure](https://oradian.com/insights/public/why-your-banks-ai-pilot-failed-and-how-to-fix-it/)
- [Axe Finance — why AI projects stall in banks](https://www.axefinance.com/resources/news-blogs/why-ai-projects-stall-in-banks/)
- [Trullion — why 95% of GenAI projects fail](https://trullion.com/blog/why-95-of-ai-projects-fail-and-why-the-5-that-survive-matter/)
- [Banking Dive — why your AI pilot will fail](https://www.bankingdive.com/spons/why-your-ai-pilot-will-fail-in-production-and-how-to-fix-it/811780/)
- [Kendall AI — MIT 95% lessons](https://kendallai.org/blog/why-95-of-enterprise-ai-pilots-fail-lessons-from-mits-2025-report/)

### EU AI Act / regulatory

- [ScienceDirect — AI Act high-risk multiple case study](https://www.sciencedirect.com/science/article/pii/S095058492600056X)
- [CSA — EU AI Act high-risk compliance deadline](https://labs.cloudsecurityalliance.org/research/csa-research-note-eu-ai-act-high-risk-compliance-deadline-20/)
- [Cooley — EU AI Act Proposed Digital Omnibus](https://www.cooley.com/news/insight/2025/2025-11-24-eu-ai-act-proposed-digital-omnibus-on-ai-will-impact-businesses-ai-compliance-roadmaps)
- [Hogan Lovells — ELTEMATE Regulatory Pilot](https://www.hoganlovells.com/en/case-studies/transforming-global-regulatory-compliance-with-eltemates-ai-powered-regulatory-pilot)
- [Secure Privacy — AI risk compliance 2026](https://secureprivacy.ai/blog/ai-risk-compliance-2026)
- [Legal Nodes — EU AI Act 2026 updates](https://www.legalnodes.com/article/eu-ai-act-2026-updates-compliance-requirements-and-business-risks)

### Industry analysis newsletters / podcasts

- [Pragmatic Engineer — AI Tooling for SWEs 2026](https://newsletter.pragmaticengineer.com/p/ai-tooling-2026)
- [Pragmatic Engineer — 2025 retrospective](https://newsletter.pragmaticengineer.com/p/the-pragmatic-engineer-in-2025)
- [Lenny's Newsletter — Stripe Minions](https://www.lennysnewsletter.com/p/how-stripe-built-minionsai-coding)
- [Every.to — Anthropic 2026 dev conference](https://every.to/chain-of-thought/inside-anthropic-s-2026-developer-conference)
- [InfoQ — From Prompts to Production playbook](https://www.infoq.com/articles/prompts-to-production-playbook-for-agentic-development/)

### Anthropic events

- [Anthropic Paris Builder Summit](https://www.anthropic.com/events/paris-builder-summit)
- [Anthropic London Builder Summit 2025](https://www.anthropic.com/events/london-builder-summit-2025)
- [Anthropic Bengaluru Builder Summit](https://www.anthropic.com/events/builder-summit-bengaluru)
- [Anthropic PwC partnership](https://www.anthropic.com/news/pwc-expanded-partnership)
- [Anthropic „How AI is transforming work at Anthropic"](https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic)
- [Anthropic „How Anthropic teams use Claude Code" (PDF)](https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf)

### Other

- [Faros.ai — DORA 2025 key takeaways](https://www.faros.ai/blog/key-takeaways-from-the-dora-report-2025)
- [Thoughtworks — DORA 2025 perspective](https://www.thoughtworks.com/en-us/insights/articles/the-dora-report-2025--a-thoughtworks-perspective)
- [IT Revolution — AI's mirror effect DORA 2025](https://itrevolution.com/articles/ais-mirror-effect-how-the-2025-dora-report-reveals-your-organizations-true-capabilities/)
- [Google Blog — DORA 2025 inside](https://blog.google/innovation-and-ai/technology/developers-tools/dora-report-2025/)
- [Helium42 — AI implementation roadmap](https://helium42.com/blog/ai-implementation-roadmap)
- [Computer Weekly — agentic AI from innovation theatre to production](https://www.computerweekly.com/feature/Moving-agentic-AI-from-innovation-theatre-to-enterprise-production)
- [New Stack — production-ready AI checklist](https://thenewstack.io/production-ready-ai-platforms/)
- [Platform Engineering — 2026 predictions](https://platformengineering.org/blog/10-platform-engineering-predictions-for-2026)

---

## Recenze

- **v0 (2026-05-18) — initial draft**: 14 sekcí, ~700 řádků; ~80 verifikovaných URL;
  TLDR + per-USP validation + counter-evidence audit + 1-pager citable quotes.
- **Doporučená re-baseline cadence:** quarterly. Velké zdroje (DORA, Octoverse,
  SO Survey, Stack Overflow, MIT NANDA) mají roční cadence.
- **Linkable from:** `docs/methodology/00-lean-pflanzer.md`,
  `docs/methodology/09-srovnani-existujici-metody.md`,
  `docs/case-studies/eshop-2026.md` (po T+90),
  `website/1-pager.html` (Honest Limitations box).
