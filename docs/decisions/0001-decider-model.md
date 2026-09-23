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
- **Kanonický Decider eskalační protokol** (viz níže) — jediný autoritativní zdroj;
  všechny ostatní dokumenty (`06-session-2.md`, `08-edge-cases-a-rizika.md`,
  Charter template) na něj odkazují, neduplikují text.

## Kanonický Decider eskalační protokol

> **Tento protokol je jediný autoritativní text.** Adresuje devil's advocate
> Útok 3 (vnitřní rozpor mezi `06`, `08` a ADR-0001 v0.2). Předtím existovaly
> tři odlišné varianty — způsobovalo by to silent project death.

### Scenario A — Decider chybí v Session 2

1. Session 2 **neprobíhá**. Facilitátor logguje stav.
2. Session 2 se odkládá **max 5 pracovních dní**.
3. Pokud Decider nemůže dorazit ani do 5 pracovních dní → eskalace na **CPO/sponzora**.
   CPO má 5 pracovních dní k jedné z:
   - Schválit nového Decideru s mandátem (Session 2 svolána s novým Deciderem).
   - **Kill projektu** (sponsor explicit, do decision logu).
4. Pokud CPO mlčí 5+5 = 10 pracovních dní → projekt **automaticky Kill**
   (silent CPO = silent kill; chrání kapacitu týmu).

### Scenario B — Decider přítomen v Session 2, ale „neumí rozhodnout"

> Decider říká *„potřebuji víc času"* na konci Session 2.

1. **T+0** (konec Session 2): Facilitátor logguje *„Decision pending: <Decider>
   by <T+48h date>"* do decision logu. Session 2 **nekončí v limbu** — formálně
   uzavřena s *„decision pending"* statusem.
2. **T+0 → T+48 h**: Decider má 48 h doručit rozhodnutí **písemně do decision
   logu** (Go / Iterate / Kill). E-mail nestačí — musí být v decision logu
   se SSO atribucí.
3. **T+48 h → T+72 h**: Pokud Decider mlčí, automatická eskalace na
   **CPO/sponzora**. CPO má 24 h.
4. **T+72 h**: Pokud CPO mlčí → projekt defaultuje na **Iterate (Session 2b)**
   s explicit write-up *„Decider+CPO silence triggered iterate default"*.
   Sponzor musí **aktivně Kill**, ne pasivně.

**Důvod „Iterate default" místo „Kill default"**: chrání před tichým úmrtím
projektu, do kterého už týmy investovaly — Decider/CPO mají druhou šanci se
ozvat v Session 2b.

### Scenario C — Iterate exhausted

1. **Iterate má hard cap: max 1 další iterace** (Session 2b — iterační rozhodovací
   session, 3 h, stejný formát jako Session 2; dříve nazývaná „Session 3“,
   přejmenováno v0.4, aby se nepletla se Ship gate).
2. Session 2b musí skončit Go nebo Kill rozhodnutím.
3. Pokud Session 2b končí znovu *„decision pending"* → automatický **Kill**
   (žádný další iterate default).

### Eskalační kontaktní řetězec

Charter (ADR-0004) povinně obsahuje:
- Decider + datum + podpis.
- **CPO/sponzor** (eskalační kontakt) + datum + podpis.
- **Backup Decider** (volitelné — pokud Decider PTO, automatická delegace).

### Kde tento protokol najít

- **Autoritativní zdroj:** tento ADR (0001), sekce „Kanonický Decider
  eskalační protokol".
- **Reference (bez duplikace textu):** `06-session-2.md` § Účastníci,
  `08-edge-cases-a-rizika.md` edge case 12, ADR-0004 Charter template.

## Reference

- Knapp, J. *Sprint* (2016) — Decider definition.
- EU AI Act, čl. 14 — lidský dohled.
- GDPR čl. 22 — automated decision-making.
- DORA — audit log retention.
