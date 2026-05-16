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

## Reinforcement track (method-level + per-pilot)

> Útok 11 v0.3 resolution: reinforcement track má **explicit budget commit**
> v Charteru projektovém (ADR-0004) a v True Cost Worksheet
> (`03-pre-session-priprava.md` Krok 1a). Bez podepsaného rozpočtu T+7/30/60/90
> Session 1 neodstartuje. Tabulka níže je method-level agregát.

| Readout | Scope | Owner | Min. PD per pilot | Co se musí stát |
|---------|-------|-------|-------------------|------------------|
| T+7 | per pilot | Champion (#17) | 0.5 | Handoff přijatý dev týmem, SHIP.md aktualizovaný |
| T+30 | per pilot | PM + EM + Champion | 2.0 (souhrnně) | Leading metric check (handoff acceptance ≥ 80 %), retro 60 min |
| T+60 | per pilot | PM + Champion | 1.0 | Scope creep audit, 1-page update do Method Steward inboxu |
| T+90 | per pilot | Decider + PM + EM + Champion | 2.5 | Guardrail metric (re-work %), Go/Iterate/Kill **v ADR** per ADR-0001 |
| T+6 mo | **method-level** | Method Steward | 2 PD/report + 0.25 PD/měsíc průběžně | Agregace metrik napříč 3+ piloty, CoP publikace |
| T+12 mo | **method-level** | Method Decider (CPO/DoE) | review session 4 h + prep | Keep / iterate / sunset rozhodnutí, ADR commit |

**Σ per-pilot reinforcement commit:** min 6 PD souhrnně (default profil).
Sponzor a EM ho podepisují v Charteru. Bez podpisu pilot neodstartuje.

**Method-level escalation:** pokud u 2+ za sebou jdoucích pilotů
M(skutečnost) / N(plán) < 0.7 reinforcement utilization → automatický
warning v Method Steward T+6 reportu + flag pro Method Decider, že
**method-level Kill criteria nemohou být obhájena** (success/failure
data jsou unreliable).

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
