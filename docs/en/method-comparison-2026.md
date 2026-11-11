**Pflanzer Method | pflanzer.cz/method**

> English version of [srovnani-metod-2026.md](../research/srovnani-metod-2026.md). The Czech original is authoritative.

# Comparison: AI-assisted development methods in companies (2025–2026)

> Research of 2026-10-19, three parallel research agents (vendors /
> consultants / practitioners). Only what was found in the sources is stated.
> Where an agent saw only a summary or a paywall, this is marked. Context:
> Pflanzer v0.5 (ADR-0021).

## Summary

- **Nobody found a method that combines the whole Pflanzer cycle:** a small
  cross-functional group → 3 competing variants of the same brief in parallel
  on a real repo → async feedback on a preview URL → a formal decision
  (Decider last, Go/Iterate/Kill) → the winner goes to production as a PR
  through scored gates.
- The others address **one piece**: specification and agent control (AWS AI-DLC,
  Spec Kit, Kiro, BMAD), adoption and prototyping (Shopify, Atlassian, Uber),
  an individual working with agents (Willison, Conductor), governance (Gartner).
- **The path from prototype to production is every method's weak spot.** Uber
  itself calls it an open question. This is where Pflanzer is strongest.
- **The evidence is weak for all of them**, Pflanzer included. Only DORA, Bain
  (a survey) and Atlassian (internal, one team) have data. The rest is a
  description of a method, an opinion or marketing.

## Comparison table

| Method | Who, year | Team | Variants | Decision-making | To production | Evidence |
|--------|----------|-----|----------|-------------|-------------|--------|
| **Pflanzer v0.5** | 2026 | core group of 3–4 + windows for representatives of the 6 steps | **3 in parallel** (worktrees) | silent voting, Decider last, Go/Iterate/Kill | PR through gates ≥ 80 | 1 pilot, qualitative |
| AWS AI-DLC | AWS, 2025 | "the whole team" (size not stated), mob elaboration/construction | 1 path | a person approves every gate, audit log | IaC + deploy under supervision | no metrics |
| GitHub Spec Kit | GitHub, 2025–26 | unspecified (developer) | 1 path | constitution + optional gates; "idea assessment" extension → go / kill | not addressed | no data; Fowler critical |
| AWS Kiro | AWS, 2025 | developer | 1 path | spec → design → tasks, hooks | not addressed | product description |
| BMAD Method | open source, 2025–26 | 1 person + AI agents in roles | 1 path | a person chooses the depth of planning | "build & verify" | popularity, not data |
| Atlassian AI mob | Atlassian, 2025 | 2–4 developers, the driver rotates | 1 path | mob + AI reviewer | PR, merge in 1–2 days | ~10 features, agreement with the AI draft <50 % → ~80 % |
| Atlassian AI Builders Week | Atlassian, 2025–26 | small teams of designers/product managers + a product engineer | many builds | not stated | 1 PR into the monorepo | 85 % adoption, 240 builds (self-evaluation) |
| Crisp / Scania AI mob | 2025 | ~4 people daily, stakeholders through an open calendar slot | 1 path | mob | not stated | qualitative |
| Uber prototype-first | Uber, 2026 | product manager, design, engineers, operations | 6 concepts / 20 min | informal | **open question** | anecdotes |
| Shopify AI memo | Shopify, 2025 | company-wide culture | — | — | — | a policy, not a process |
| AI design sprint | Sherwen and others, 2025 | facilitated workshop | concepts | dot voting | wireframes, not code | testimonial |
| McKinsey agentic pods | McKinsey, 2025–26 | 8–12 → 4–6 people + agents | — | "what to build" is the bottleneck | — | a mix of data and marketing (text from the summary only) |
| Gartner governance | Gartner, 2026 | citizen developers | — | triage of citizen vs. engineering | 2 layers of checks | a prediction (paywall, summary only) |
| AI-Native SAFe | Scaled Agile, 2026 | SAFe | — | "agentic compliance gates" (unconfirmed) | — | none |

## What this confirms for Pflanzer

- **A small group:** Atlassian (2–4), Scania (~4), McKinsey (4–6 instead of
  8–10) and the practical ceiling of 3–5 parallel agents all fit a core group
  of 3–4 and 3 variants.
- **Windows instead of permanent participation:** Scania gets stakeholders
  through an open calendar slot, which is the same principle.
- **Decision-making is the bottleneck** (McKinsey, Bain: code is only 25–35 % of the
  time from idea to launch) → investing in the Decision makes sense.
- **A prototype as code in the target repo:** the only method that handles this
  end to end. The others either stay at wireframes (design sprint) or do not
  address production (Uber, LogRocket, Spec Kit).

## What to adopt (recommendations, ordered by benefit)

1. **A constitution in the target repo** (Spec Kit, Thoughtworks, Microsoft
   Learn). A short file of principles: security, legal, code standards.
   AI reads it in every worktree and the gates check against it. Extend
   `INTEGRATION_GUIDE.md` from `pflanzer init`, **briefly** (Fowler warns
   against verbose specs).
2. **A repo-readiness checklist before Kickoff** (Willison): tests, CI,
   lint, **preview deploy**. Without them an agent cannot handle production code.
   It belongs in `docs/zacni.md` § B.
3. **When NOT to use the method** (Uber): compliance-sensitive work, strong
   dependencies, mobile → PRD-first / standard SDLC. Tighten the "Does not suit"
   section in `zacni.md`.
4. **Decisions and windows as artifacts in the repo** (AI-DLC): a decision log
   (who approved what, and when) committed to the target repo, not only in a local DB.
5. **Checks already during Build, not only in Ship** (Gartner, Atlassian evals):
   lint/test/secret scan run continuously in the worktrees.
6. **Agent security:** a worktree is **not** security isolation
   (Conductor). Add to the security & operations checkpoint: an egress limit, a token cap,
   protection against prompt injection (Gartner).
7. **A prototype label on the preview URL** (Uber): "variant for decision,
   not a product" + the problem statement, so that the preview is not mistaken
   for a finished thing.
8. **Our own data**, because nobody has any. Measure for every pilot: time from
   Kickoff to merge, agreement of the AI output with expectations (Atlassian), gate
   score, the share of the winner's code that survives into production. This may be
   the method's main differentiator.

## What NOT to adopt

- Heavy specification before every change (Kiro split a small bug into 4 stories
  and 16 acceptance criteria — Fowler).
- Certifications and extra roles (AI-Native SAFe).
- A cultural mandate through performance reviews (Shopify) — outside the scope of the method.

## Sources

**Vendors:**
- [AWS AI-DLC](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)
- [AI-DLC open-source workflows](https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/)
- [GitHub Spec Kit](https://github.com/github/spec-kit)
- [Fowler: SDD tools](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [Kiro (SD Times)](https://sdtimes.com/ai/amazon-launches-spec-driven-ai-ide-kiro/)
- [Shopify memo (BetaKit)](https://betakit.com/shopify-ceo-tobi-lutke-tells-employees-to-prove-ai-cant-do-the-job-before-asking-for-resources/)
- [Atlassian AI Builders](https://www.atlassian.com/blog/ai-at-work/a-design-technologists-take-on-ai-builders)
- [Anthropic teams](https://claude.com/blog/how-anthropic-teams-use-claude-code)
- [DORA 2025](https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf)

**Consultants:**
- [Thoughtworks Radar SDD](https://www.thoughtworks.com/radar/techniques/spec-driven-development)
- [Microsoft Learn Spec Kit enterprise](https://learn.microsoft.com/en-us/training/modules/spec-driven-development-github-spec-kit-enterprise-developers)
- [McKinsey agentic delivery](https://www.mckinsey.com/capabilities/mckinsey-technology/our-insights/rewiring-software-delivery-for-the-agentic-era)
- [Bain 2025](https://www.bain.com/insights/from-pilots-to-payoff-generative-ai-in-software-development-technology-report-2025/)
- [Gartner vibe coding governance](https://www.gartner.com/en/documents/8068765)
- [SAFe AI](https://framework.scaledagile.com/blog/thriving-in-the-age-of-ai-with-scaled-agile)
- [Sherwen AI sprint](https://www.sherwen.com/ai-design-sprint-workshop)

**Practitioners:**
- [BMAD](https://github.com/bmad-code-org/BMAD-METHOD)
- [Willison: vibe engineering](https://simonwillison.net/2025/Oct/7/vibe-engineering/)
- [Conductor worktrees](https://www.conductor.build/docs/concepts/git-worktrees)
- [Sculptor](https://imbue.com/sculptor)
- [Atlassian mobbing with AI](https://www.atlassian.com/blog/how-we-build/mobbing-with-ai)
- [Crisp/Scania](https://blog.crisp.se/2025/06/02/michaelgothe/mob-programming-with-ai-inside-a-high-performing-teams-journey)
- [Uber AI prototyping](https://www.uber.com/in/ta/blog/ai-prototyping/)
- [LogRocket](https://stories.logrocket.com/p/thought-leadership-how-we-replaced-prds-ai-prototypes)
- [Reforge/Balfour](https://blog.brianbalfour.com/p/ai-native-product-teams-how-they)
- [Vibe coding stop sign](https://cspanswick.substack.com/p/vibe-coding-has-a-stop-sign)
