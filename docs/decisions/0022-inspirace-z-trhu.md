# ADR-0022 — Inspirace z trhu: povrch jednoduchý, pod ním komplexní

**Status:** Accepted (v0.5)
**Date:** 2026-10-19
**Context source:** [`docs/research/srovnani-metod-2026.md`](../research/srovnani-metod-2026.md)
**Navazuje na:** ADR-0021 (malá skupina, celá cesta). Nemění ho.

## Kontext

Rešerše (2026-10-19, 3 paralelní agenti) srovnala Pflanzer s AI-DLC, Spec Kit,
Kiro, BMAD, Atlassian, Uber, Shopify, McKinsey, Gartner a dalšími. Závěr:
nikdo nespojuje celý cyklus (3 soutěžní varianty na reálném repu → async
→ rozhodnutí → PR přes gates); cesta prototyp → produkce je slabina všech.
Důkazy jsou slabé u všech, i u nás. Rešerše zároveň ukázala osm věcí, které
jinde fungují a nám chybí. Cíl uživatele: povrch zůstane `/pm` + 5 kroků
+ 3 pravidla; složitost patří do toolu a referencí.

## Varianty

| Varianta | Pro | Proti |
|----------|-----|-------|
| A — nic nepřebírat | nejmenší změna | zůstávají známé mezery (readiness, bezpečnost agentů, měření) |
| B — **přebrat jen, co jde automatizovat nebo se vejde do jednoho řádku** | povrch se nemění, tool nese složitost | více práce v toolu |
| C — přebrat vše (těžká spec, certifikace) | „úplné" | rozbije jednoduchost; Fowler varuje před verbózními specy |

## Rozhodnutí

**Varianta B.** Přebíráme:

1. **Constitution v target repu** (`.pflanzer/CONSTITUTION.md`, vytváří
   `pflanzer init`) — krátká nepřekročitelná pravidla pro AI. Čte ji AI ve
   všech worktrees, kontrolují se proti ní gates. Záměrně krátká.
2. **Repo-readiness: `pflanzer doctor`** před Kickoffem (testy, lint, build,
   CI, preview deploy, vyplněné průvodce, pushnutý init). Kickoff při „ne"
   nezačíná bez vědomého přijetí rizika.
3. **Kdy metodu NEpoužít** — compliance-citlivé věci, platby, silné externí
   závislosti, nativní mobilní release cyklus, nejednoznačná strategie bez
   Decidera. Zapsáno v `docs/zacni.md`.
4. **Decision log v repu** (`.pflanzer/decisions/<slug>.md`, commitnutý) —
   kdo, kdy, co, proč; ne jen lokální DB.
5. **Kontroly už během Buildu** — lint/typy/testy/build průběžně ve všech
   worktrees; prompty to AI ukládají.
6. **Rozšířený checkpoint bezpečnost & právo (stále 20 min):** datový tok,
   data classification, egress limit, strop tokenů/nákladů, riziko prompt
   injection, a výslovně: **worktree není bezpečnostní izolace**.
7. **Měření pilotů** — čas Kickoff → merge, gate score, počet kol Iterate,
   podíl kódu vítěze, který přežije 30 dní v `main`. Tool sbírá v handoffu.
   Může být hlavní diferenciace.
8. **Štítek prototypu na preview** — „Varianta X — k rozhodnutí, ne produkt"
   + problém v jedné větě.

Doplňky v duchu téhož: `pflanzer status` (jediný zdroj pravdy o fázi
+ jeden další krok), jedna cesta založení projektu (Kickoff →
`quick_session bootstrap`), gates jen na vítěze (práh pilot 80 / production
85), offline feedback, critical na vítězi blokuje Go.

**Nepřebíráme:** těžkou specifikaci před každou změnou (Kiro/Fowler),
certifikace a role navíc (SAFe), kulturní mandát přes performance review
(Shopify — mimo scope metody).

## Důsledky

**Pozitivní**
- Uživatel dál vidí jen `/pm`; readiness, constitution a měření jsou v toolu.
- Zavřená mezera „worktree = izolace" a „kdo hlídá náklady agentů".
- První vlastní data o metodě.

**Negativní / rizika**
- Víc práce před Kickoffem (CONSTITUTION, preview deploy). Mitigace:
  `doctor` řekne přesně co; zacni.md má seznam.
- Constitution může narůst do spec. Mitigace: držet na jedné obrazovce.
- Práh 85 pro production je odhad; doladit na pilotech.

**Otevřené**
- Skutečná shoda AI výstupu s očekáváním (Atlassian) zatím neměříme.
- Rozhraní toolu (`doctor`, `status`, `feedback add`, `--winner`) staví
  paralelní práce; commandy se na ně spoléhají.
