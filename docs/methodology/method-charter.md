# Pflanzer Method-Level Charter

> Trvalý dokument. Pflanzer si nárokuje vlastní disciplínu — XYZ hypotézu,
> falsifying criterion, kill criteria. Bez toho je *methodology that exempts
> itself from its own discipline* (devil's advocate Útok 12, ADR-0007).

## Status

- **Verze metody:** v0.2 (post-devil's advocate v0.2.1 patches)
- **Datum charteru:** 2026-05-05
- **Method Steward:** *(přiřazení po 1. pilotu v cílové organizaci)*
- **Method Decider (CPO / Director of Engineering):** *(přiřazení v dané org)*

## XYZ hypotéza (metoda)

> Věříme, že Pflanzerova metoda **zkrátí čas od „nápad" k „handoff package"
> o ≥ 50 %** (z baseline ~6–9 měsíců sériového handoffu na ~6–9 týdnů
> 2-session cyklu) pro projekty splňující fit criteria
> z `01-filozofie-a-kdy-pouzit.md`,
>
> s kvalitou handoff package **srovnatelnou nebo vyšší** než current state
> (měřeno re-work % v T+90 a cross-functional NPS).

## Success threshold

| Metric | Cíl | Měřeno | Vlastník |
|--------|-----|--------|----------|
| Primary lagging — Time-to-handoff | ≤ 50 % baseline | per pilot, agregováno T+6 mo | Method Steward |
| Leading — Handoff acceptance | ≥ 80 % artefaktů použito v T+30 | per pilot | EM dev týmu |
| Guardrail — Re-work % T+90 | ≤ baseline current state | per pilot, agregace | Data #12 |
| Stakeholder NPS | ≥ +20 | post-pilot survey | Champion #17 |

## Kill criteria

| Po N pilotech | Kill trigger |
|---------------|--------------|
| 3 | > 50 % pilotů zhasne (Decider+CPO silence triggered Iterate→Kill, viz ADR-0001 Scenario B) |
| 6 | Average „nápad → handoff" ≥ baseline × 0.75 (< 25 % zlepšení) |
| 10 | < 3 self-sustaining BU (žádný organic Champion pipeline, ADR-0006) |

Po **6 pilotech** povinná **method-level review**: keep / iterate / sunset.

## Comparison baseline

Měříme proti **current state v dané organizaci**: sériový handoff
(zadavatel → produkt → vývoj → test → security → deploy). Baseline metric
collection **3 měsíce před prvním pilotem** (light: 5–10 reprezentativních
projektů, manuální estimace nebo project tracker analysis).

**Co tvoří baseline:**
- Time-to-handoff (median + p90 dnů)
- Re-work % T+90 (per project)
- Late-stage veto count (security/legal po > 50 % effortu)
- Stakeholder NPS (post-launch survey nebo pulse)

## Reinforcement track (method-level)

- **T+30 per pilot:** per-pilot retro (ADR-0004 reinforcement budget).
  Owner: Champion #17.
- **T+6 měsíců method-level:** agregace metrik napříč 3+ piloty.
  Method Steward publikuje report do CoP / Confluence.
- **T+12 měsíců method-level:** review — keep / iterate / sunset rozhodnutí.
  Owner: Method Decider (CPO/DoE).

## Validační loop & sunset

- Method Steward má pravomoc **navrhnout method-level Kill / sunset**.
- Pokud Method Decider potvrdí Kill → projekty v progress doběhnou,
  nové se nestartují, role catalog se freeze-uje.
- Sunset není failure — je to *methodology hygiene*. Lepší než nekonečný drift.

## Audit-committee odpověď

> Otázka: *„Kolik pilotů prošlo Pflanzerem, jaký je success rate, jak ho měříte?"*

> Odpověď: *„X pilotů prošlo. Time-to-handoff baseline je Y dní, Pflanzer
> průměrně Z dní (= W % zlepšení). Detail per pilot v Method Steward reportu
> T+6 mo (link). Falsifying criteria definovaná v Method Charteru, kill
> review po 6 pilotech, T+12 sunset gate."*

To je odpověď, kterou v0.2 metody **nemá**. v0.2.1 (po ADR-0007) má.

## Reference

- ADR-0007 (kontext rozhodnutí o vzniku tohoto Charteru).
- Savoia, A. *The Right It*.
- Devil's advocate review Útok 12.
- Charter projektový (ADR-0004) — vzor disciplíny.
