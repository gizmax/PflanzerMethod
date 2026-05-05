# ADR-0001 — Decider model á la GV Sprint

**Status:** Accepted
**Date:** 2026-05-05
**Context source:** perspektiva 01 (Zadavatel), 03 (Facilitátor meta), synthesis 01 (conflict matrix Top 5)

## Kontext

Pflanzerova metoda v0 nedefinuje, kdo má v session 1 a 2 **finální slovo** při
volbě varianty / Go-Iterate-Kill rozhodnutí. AI-led syntéza v session 2
přirozeně rozmělňuje accountability („panel doporučil…") a zadavatel může
své rozhodnutí později popřít. Bez explicitního Decideru končí Pflanzer jako
„hezký den" bez závazného output.

## Varianty

1. **Konsensus celé skupiny** (LDJ-style). Riziko: nejnižší společný jmenovatel,
   politické pinkání po session 2.
2. **AI panel jako rozhodující** (AI-mediated Go/Kill). Riziko: rozporné s GDPR
   čl. 22 a AI Act čl. 14 (lidský dohled), žádná korporátní accountability.
3. **Single accountable Decider á la GV Sprint** (Knapp). Jeden člověk
   s mandátem, panel je advisory.
4. **Dual decider** (PM + zadavatel společně). Riziko: deadlock.

## Rozhodnutí

**Variant 3.** Pflanzer adoptuje **Decider model** podle GV Design Sprintu:

- **Decider je vždy 1 člověk** s předem doloženým mandátem od CPO/sponsora.
- Defaultně Decider = Zadavatel (#1). Pro corporate IT iniciativy lze delegovat
  na CTO-side sponzora.
- Decider vlastní **Go / Iterate / Kill** rozhodnutí na konci Session 2.
- Pokud Decider chybí v Session 2, **Session 2 se odkládá**, nepokračuje se
  bez něj.
- AI panel je **advisory** — generuje preference matrix, syntézu feedbacku,
  identifikuje konflikty. Decider rozhoduje.

## Důsledky

**Pozitivní:**
- Žádná účetní rozmělněnost — vždy víme, kdo schválil co.
- Soulad s AI Act čl. 14 (lidský dohled) a GDPR čl. 22 (ADM).
- Decision log atribuuje rozhodnutí na lidskou identitu (DORA 7-letá retence).

**Negativní:**
- Decider model nesedí korporátům s konsensuální kulturou — tam je nutný
  „social override" (Decider má veto, ale rozhoduje na základě vyjádřené vůle
  panelu). Adresováno v `01-filozofie-a-kdy-pouzit.md` jako anti-pattern fit.
- Pokud Decider nemá písemný mandát, session se nemusí konat (governance check).

**Mitigace:**
- Charter (ADR-0004) povinně obsahuje sekci „Decider + mandát od X, datum Y, podpis Z".
- Eskalační protokol: pokud Decider „neumí rozhodnout" v session 2, kill timer
  48 h, jinak default = Iterate (max 1×, pak Kill).

## Reference

- Knapp, J. *Sprint* (2016) — Decider definition.
- EU AI Act, čl. 14 — lidský dohled.
- GDPR čl. 22 — automated decision-making.
- DORA — audit log retention.
