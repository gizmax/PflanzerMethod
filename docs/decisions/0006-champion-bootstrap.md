# ADR-0006 — Champion bootstrap mechanismus (první pilot v BU)

**Status:** Accepted
**Date:** 2026-05-05
**Context source:** devil's advocate review Útok 2 (kruhová závislost), perspektiva 17 (Champion), baseline 03 (Innersource champion)

## Kontext

Devil's advocate Útok 2 odhalil **kruhovou závislost**: ADR-0003 a `02-role-catalog.md`
povyšují Champion (#17) na samostatnou roli, přičemž definice Championa zní
*„byl v Session 1+2 předchozího pilotu, podepsal Decision log"*. Důsledek:

- **První pilot v BU z definice nemá Championa** (žádný předchozí pilot neexistoval).
- **Druhý pilot v jiné BU = znovu první pilot** v té BU bez Championa.
- Banka s 8 BU potřebuje **8 prvních pilotů bez Championa**.

`01-filozofie-a-kdy-pouzit.md` přitom říká *„bez Championa je metoda one-shot
demo, ne adopce"*. To je writing-into-corner — metoda si vlastní podmínky
nedokáže splnit při startu.

## Rozhodnutí

Pflanzer rozlišuje **dva režimy Championa** podle fáze pilotu v BU:

### Režim 1 — Bootstrap Champion (první pilot v BU)

**Definice:** lidský coach s expertízou v Pflanzer metodě, **dočasně přidělený**
do BU pro první pilot.

**Tři přípustné formy:**

1. **Externí coach** — konzultant nebo trenér s vlastní zkušeností Pflanzer pilotů
   (např. původní autor metody, certifikovaný facilitátor z partnerské firmy).
   Cost: ~5–10 person-days externí kapacity per pilot.
2. **Rotace Championa z první BU** — pokud organizace už má proběhlý pilot
   v jiné BU, Champion z té BU je dočasně secondee na první pilot v nové BU
   (4–6 týdnů zapůjčení s explicit time commit).
3. **Tandem Champion-in-training + Bootstrap coach** — kombinace 1+2: junior
   Champion z BU + senior coach (externí nebo z první BU) jako pár.
   Cost: ~3 person-days senior + 5 person-days junior.

**Výběr formy:** rozhodnutí v Charteru (ADR-0004), sekce „Champion provisioning".

### Režim 2 — Organic Champion (druhý+ pilot v BU)

Definice nezměněna: byl v Session 1+2 předchozího pilotu v BU, podepsal Decision
log, accepted role pro pokračování. Žádné externí náklady.

### Kdy Pflanzer **nesmí** startovat bez Championa

- Žádná z forem 1–3 není dostupná → pilot odložen.
- Důvod: anti-pattern „Pflanzer pro Pflanzer" — bez plánu, jak metoda v BU
  přežije, je první pilot drahá demo.

### Champion buddy (Útok 2 sekundární adresování)

- Ve **všech** režimech (bootstrap i organic) **musí existovat Champion buddy**
  — druhá osoba se znalostí Pflanzeru, která může zaskočit pokud Champion
  odejde / je PTO / opustí firmu.
- Buddy nemusí být v Session 1+2; stačí onboarding do Pflanzer artefaktů
  + accepted role.
- V malých BU (< 30 lidí) může buddy být napříč BU.

## Důsledky

**Pozitivní:**
- Metoda škáluje napříč BU bez kruhové závislosti.
- Externí coach jako legitimní route — uznává realitu, že interní expertíza
  vzniká postupně.
- Cost-aware — bootstrap náklad je explicitní a v Charteru.

**Negativní:**
- Externí coach = dependency na vendor / consulting market. Mitigace:
  Champion-in-training tandem snižuje vendor lock-in.
- Rotace Championa zatěžuje původní BU. Mitigace: jasný time commit
  s end date.

**Mitigace ekonomiky:**
- První pilot v organizaci je **vždy** drahý (bootstrap externí coach 5–10 PD).
- Druhý+ pilot v BU = organic, tedy levný (žádný extra Champion cost).
- Druhý+ BU = záleží na rotaci nebo externí coach (mid cost).
- Po **3+ proběhlých pilotech v 2+ BU** se metoda stává **self-sustaining**
  (interní champion pool ≥ 3 lidé).

## Update Charter (ADR-0004)

Charter musí mít sekci **„Champion provisioning"** s povinnou volbou:

```
## Champion provisioning
- Režim: Bootstrap (forma 1/2/3) | Organic
- Champion: <jméno>, time commit <X PD per pilot>
- Champion buddy: <jméno>, time commit <Y PD>
- (Bootstrap only) Coach: <jméno / firma>, kontrakt do <date>, cost <Z>
- Validation post-pilot: Champion accepted continuation? <ano/ne>
```

## Update Role catalog (ADR-0003)

`02-role-catalog.md` role #17 dostane addendum:
*„První pilot v BU = Champion v režimu Bootstrap (viz ADR-0006).
Druhý+ pilot = Organic. Buddy povinný v obou režimech."*

## Reference

- Devil's advocate Útok 2.
- Innersource Commons — champion model.
- Toyota Improvement + Coaching Kata.
- Spotify model retrospective (2024) — proč adopce bez interní expertízy
  nefunguje long-term.
