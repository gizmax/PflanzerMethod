Pflanzer Method | pflanzer.cz/method

# Role card #9 — Engineering manager

> Zastupuješ krok provoz: hlídáš kapacitu, závislosti a to, co s vítězem bude po nasazení — z varianty se stává závazek týmu.

**Krok cesty:** Provoz · **Kde jsi:** okno — checkpoint provozu 20 min u Shipu (stačí DevOps nebo EM)

Status v catalogu: **doporučená** · Kdy se zve: Bude scope déle než 2 sprinty / je to PI priority?

## Přines do svého okna
- Kapacitu týmu a roadmapu (PI commit %)
- Závislosti na platform / identity / data týmech
- T-shirt sizing rubriku

## Podepisuješ
- Checkpoint provozu: `pflanzer checkpoint --slug <slug> provoz --by JMÉNO --note …` (blokace: přidej `--blocked`)
- Dependency Map a T-shirt odhad (+ 2denní capped spike)
- Capacity buffer 25 % pro Pflanzer-driven features; veto, pokud je PI commit > 80 %

## Kdy jsi u toho
- Quick (60–90 min) — **async**: kapacitu potvrdíš po Rozhodnutí
- Lean (3 h) — **blok**: okno u Shipu: kapacita, monitoring, kdo to bude provozovat
- Full (5–6 h) — **celý běh**: senior delegát; blok tech feasibility + T-shirt v Buildu

## Hlasuješ o
Skóruješ všechny 4 dimenze; effort opíráš o T-shirt sizing, ne o dojem.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **effort**, **strategic_fit**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- PI commit > 80 % — řekni to před Kickoffem (veto)
- Varianta závisí na týmu, který o tom neví
- Odhad nad 2 sprinty bez spiku

## AI proxy
**Režim 1 — Vlastnické a vetovací (vždy člověk).** ❌ Kapacita a roadmapa jsou citlivé — vždy člověk. Sub-agent: `.claude/agents/em-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 9 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
