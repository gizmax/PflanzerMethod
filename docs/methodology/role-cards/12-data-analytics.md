Pflanzer Method | pflanzer.cz/method

# Role card #12 — Data / Analytics

> Zajišťuješ, že winner jde změřit — bez measurement planu nevíme, jestli fíčura funguje.

Status v catalogu: **doporučená** · Kdy se zve: Release intent (= ship plánován) nebo nové metriky / A/B test?

## Přines do Session 1
- Event taxonomy a naming convention
- Baseline metriky a KPI strom
- Power analysis pro případný A/B test
- Privacy klasifikaci eventů

## Podepisuješ
- Measurement plan v1 (lagging + 2–3 leading + guardrail)
- Instrumentation deadline = ship-date − 2 dny (merge-blokující)
- A/B test design a kill criteria

## Kdy jsi v místnosti
- Quick (60–90 min) — **async**: metriky jsou v Quick TBD — measurement plan doplníš mezi sessions
- Lean (3 h) — **async**: AI navrhne event schema, measurement plan schválíš do 24–48 h
- Full (5–6 h) — **celá session**: měřitelnost variant proti XYZ hypotéze

## Hlasuješ o
Skóruješ všechny 4 dimenze; hlavně jestli jde varianta změřit proti XYZ hypotéze.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **strategic_fit**. K tomu commitment level 0–3 pro mezi-session práci.

## Okamžitě hlas
- Success metric bez baseline
- Event bez privacy klasifikace
- Ship bez instrumentace

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ✅ AI navrhne event schema, ⚠️ measurement plan schvaluješ ty. Sub-agent: `.claude/agents/data-analytics-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 12 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
