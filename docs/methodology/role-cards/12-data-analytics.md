Pflanzer Method | pflanzer.cz/method

# Role card #12 — Data / Analytics

> Za 20 minut v Asyncu potvrdíš, že jde změřit metriku z Kickoffu: co se bude sbírat, odkud a jaké je dnešní číslo.

**Krok cesty:** Produkt (měření) · **Kde jsi:** okno — Async a Ship (measurement plan)

Status v catalogu: **doporučená** · Kdy se zve: Release intent (= ship plánován) nebo nové metriky / A/B test?

## Přines do svého okna
- Dnešní hodnotu metriky z Kickoffu
- Události, které se musí sbírat, a zda obsahují osobní údaje
- Pro hlubší kontrolu (stupeň Full): event taxonomy, KPI strom, power analysis pro A/B test, instrumentation deadline = ship-date − 2 dny

## Podepisuješ
- Measurement plan v1 (lagging + 2–3 leading + guardrail)
- Instrumentation deadline = ship-date − 2 dny (merge-blokující)
- A/B test design a kill criteria

## Kdy jsi u toho
- Quick (60–90 min) — **async**: metriky jsou v Quick TBD — measurement plan doplníš v Async okně
- Lean (3 h) — **async**: AI navrhne event schema, measurement plan schválíš v Async okně (24–48 h)
- Full (5–6 h) — **celý běh**: měřitelnost variant proti XYZ hypotéze

## Hlasuješ o
Skóruješ všechny 4 dimenze; hlavně jestli jde varianta změřit proti XYZ hypotéze.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **strategic_fit**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Success metric bez baseline
- Event bez privacy klasifikace
- Ship bez instrumentace

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Není to krok cesty** (ADR-0023); AI navrhne schéma událostí, plán měření schvaluješ ty. Sub-agent: `.claude/agents/data-analytics-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 12 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
