# Srovnání: metody AI-asistovaného vývoje ve firmách (2025–2026)

**Pflanzer Method | pflanzer.cz/method**

> Rešerše 2026-10-19, 3 paralelní rešeršní agenti (vendoři / konzultanti /
> praktici). Uvedeno jen to, co bylo ve zdrojích nalezeno; kde agent viděl
> jen shrnutí nebo paywall, je to označeno. Kontext: Pflanzer v0.5
> (ADR-0021).

## Shrnutí

- **Nikdo nenašel metodu, která spojuje celý Pflanzer cyklus:** malá
  cross-functional skupina → 3 soutěžní varianty stejného zadání paralelně
  na reálném repu → async feedback na preview URL → formální rozhodnutí
  (Decider poslední, Go/Iterate/Kill) → vítěz přes skórované gates jako PR
  do produkce.
- Ostatní řeší **jeden kus**: specifikaci a řízení agenta (AWS AI-DLC,
  Spec Kit, Kiro, BMAD), adopci a prototypování (Shopify, Atlassian, Uber),
  práci jednotlivce s agenty (Willison, Conductor), governance (Gartner).
- **Cesta prototyp → produkce je slabina všech** — Uber ji sám označuje
  za otevřenou otázku. Tady je Pflanzer nejsilnější.
- **Důkazy jsou u všech slabé**, Pflanzer nevyjímaje. Data mají jen DORA,
  Bain (přehledová) a Atlassian (interní, jeden tým). Zbytek je popis
  metody, názor nebo marketing.

## Srovnávací tabulka

| Metoda | Kdo, rok | Tým | Varianty | Rozhodování | Do produkce | Důkazy |
|--------|----------|-----|----------|-------------|-------------|--------|
| **Pflanzer v0.5** | 2026 | jádro 3–4 + okna zástupců 6 kroků | **3 paralelně** (worktrees) | silent voting, Decider poslední, Go/Iterate/Kill | PR přes gates ≥ 80 | 1 pilot, kvalitativně |
| AWS AI-DLC | AWS, 2025 | „celý tým" (velikost neuvedena), mob elaboration/construction | 1 cesta | člověk schvaluje každý gate, audit log | IaC + deploy pod dohledem | bez metrik |
| GitHub Spec Kit | GitHub, 2025–26 | neurčeno (vývojář) | 1 cesta | constitution + volitelné gates; rozšíření „idea assessment" → go / kill | neřeší | bez dat; Fowler kritický |
| AWS Kiro | AWS, 2025 | vývojář | 1 cesta | spec → design → tasks, hooks | neřeší | produktový popis |
| BMAD Method | open-source, 2025–26 | 1 člověk + AI agenti v rolích | 1 cesta | člověk volí hloubku plánování | „build & verify" | popularita, ne data |
| Atlassian AI mob | Atlassian, 2025 | 2–4 vývojáři, řidič rotuje | 1 cesta | mob + AI reviewer | PR, merge 1–2 dny | ~10 featur, shoda AI draftu <50 % → ~80 % |
| Atlassian AI Builders Week | Atlassian, 2025–26 | malé týmy designérů/PM + product engineer | mnoho buildů | neuvedeno | 1 PR do monorepa | 85 % adopce, 240 buildů (samoevaluace) |
| Crisp / Scania AI mob | 2025 | ~4 lidé denně, stakeholdeři přes otevřený slot v kalendáři | 1 cesta | mob | neuvedeno | kvalitativní |
| Uber prototype-first | Uber, 2026 | PdM, design, inženýři, provoz | 6 konceptů / 20 min | neformální | **otevřená otázka** | anekdoty |
| Shopify AI memo | Shopify, 2025 | kultura celé firmy | — | — | — | politika, ne proces |
| AI design sprint | Sherwen aj., 2025 | facilitovaný workshop | koncepty | dot voting | wireframy, ne kód | testimonial |
| McKinsey agentic pods | McKinsey, 2025–26 | 8–12 → 4–6 lidí + agenti | — | „co stavět" = úzké hrdlo | — | mix dat a marketingu (text jen ze shrnutí) |
| Gartner governance | Gartner, 2026 | citizen developeři | — | triage citizen vs. engineering | 2 vrstvy kontrol | predikce (paywall, jen shrnutí) |
| AI-Native SAFe | Scaled Agile, 2026 | SAFe | — | „agentic compliance gates" (nepotvrzeno) | — | žádné |

## Co tím Pflanzer potvrzuje

- **Malá skupina:** Atlassian (2–4), Scania (~4), McKinsey (4–6 místo
  8–10) i praktický strop 3–5 paralelních agentů sedí na jádro 3–4
  a 3 varianty.
- **Okna místo stálé účasti:** Scania má stakeholdery přes otevřený
  kalendářní slot, což je stejný princip.
- **Rozhodování je úzké hrdlo** (McKinsey, Bain: kód je jen 25–35 % času
  od nápadu po launch) → investice do Rozhodnutí dává smysl.
- **Prototyp jako kód v target repu:** jediný, kdo to řeší end-to-end;
  ostatní buď zůstávají u wireframů (design sprint), nebo produkci
  neřeší (Uber, LogRocket, Spec Kit).

## Co převzít (doporučení, seřazeno podle přínosu)

1. **Constitution v target repu** (Spec Kit, Thoughtworks, Microsoft
   Learn). Krátký soubor principů: bezpečnost, právo, standardy kódu.
   Čte ho AI v každém worktree a kontrolují se proti němu gates. Rozšířit
   `INTEGRATION_GUIDE.md` z `pflanzer init`, **krátce** (Fowler varuje
   před verbózními specy).
2. **Repo-readiness checklist před Kickoffem** (Willison): testy, CI,
   lint, **preview deploy**. Bez nich agent produkční kód nezvládne.
   Patří do `docs/zacni.md` § B.
3. **Kdy metodu NEpoužít** (Uber): compliance-citlivé věci, silné
   závislosti, mobil → PRD-first / standardní SDLC. Zpřesnit „Nehodí se"
   v `zacni.md`.
4. **Rozhodnutí a okna jako artefakty v repu** (AI-DLC): decision log
   (kdo, kdy, co schválil) commitnutý do target repa, ne jen v lokální DB.
5. **Kontroly už během Buildu, ne jen v Ship** (Gartner, Atlassian evals):
   lint/test/secret scan běží průběžně ve worktrees.
6. **Bezpečnost agentů:** worktree **není** bezpečnostní izolace
   (Conductor). Doplnit do checkpointu B&P: egress limit, strop tokenů,
   ochrana proti prompt injection (Gartner).
7. **Štítek prototypu na preview URL** (Uber): „varianta k rozhodnutí,
   ne produkt" + problem statement, aby se preview nezaměnilo za hotovou
   věc.
8. **Vlastní data** — nikdo je nemá. Měřit u každého pilotu: čas od
   Kickoffu po merge, shoda AI výstupu s očekáváním (Atlassian), gate
   score, podíl kódu vítěze, který přežije do produkce. Může to být
   hlavní diferenciace metody.

## Co NEpřebírat

- Těžkou specifikaci před každou změnou (Kiro rozdělil malý bug na 4 stories
  a 16 acceptance criteria — Fowler).
- Certifikace a role navíc (AI-Native SAFe).
- Kulturní mandát přes performance review (Shopify) — mimo scope metody.

## Zdroje

**Vendoři:**
- [AWS AI-DLC](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)
- [AI-DLC open-source workflows](https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/)
- [GitHub Spec Kit](https://github.com/github/spec-kit)
- [Fowler: SDD tools](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [Kiro (SD Times)](https://sdtimes.com/ai/amazon-launches-spec-driven-ai-ide-kiro/)
- [Shopify memo (BetaKit)](https://betakit.com/shopify-ceo-tobi-lutke-tells-employees-to-prove-ai-cant-do-the-job-before-asking-for-resources/)
- [Atlassian AI Builders](https://www.atlassian.com/blog/ai-at-work/a-design-technologists-take-on-ai-builders)
- [Anthropic teams](https://claude.com/blog/how-anthropic-teams-use-claude-code)
- [DORA 2025](https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf)

**Konzultanti:**
- [Thoughtworks Radar SDD](https://www.thoughtworks.com/radar/techniques/spec-driven-development)
- [Microsoft Learn Spec Kit enterprise](https://learn.microsoft.com/en-us/training/modules/spec-driven-development-github-spec-kit-enterprise-developers)
- [McKinsey agentic delivery](https://www.mckinsey.com/capabilities/mckinsey-technology/our-insights/rewiring-software-delivery-for-the-agentic-era)
- [Bain 2025](https://www.bain.com/insights/from-pilots-to-payoff-generative-ai-in-software-development-technology-report-2025/)
- [Gartner vibe coding governance](https://www.gartner.com/en/documents/8068765)
- [SAFe AI](https://framework.scaledagile.com/blog/thriving-in-the-age-of-ai-with-scaled-agile)
- [Sherwen AI sprint](https://www.sherwen.com/ai-design-sprint-workshop)

**Praktici:**
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
