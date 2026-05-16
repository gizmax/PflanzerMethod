# ADR-0007 — Method-level Charter (Pflanzer si nárokuje vlastní disciplínu)

**Status:** Accepted (v0.2.1) — **partially superseded v0.3** (viz ADR-0011, ADR-0012, ADR-0013 níže)
**Date:** 2026-05-05 (original); 2026-05-16 (v0.3 supersession addendum)
**Context source:** devil's advocate review Útok 12 (method bez vlastního falsifying criterion); autoresearch round „method-falsifiability" (`docs/research/method-falsifiability/`)

## v0.3 supersession addendum

Autoresearch round s 4 perspektivami (Method Steward, Data analyst, Skeptický VP,
Akademik) identifikoval **3 fatální problémy** s původní ADR-0007 formulací:

1. **Decider profile** (*„CPO/DoE"*) — politicky exponovaný, tenure 2.3y, sunk-cost
   asymmetry → metoda zombifikuje. → **Supersedes** ADR-0011 (Method Decider =
   VP Engineering Effectiveness, 2 levely pod CTO).
2. **Steward role** (*„10 % FTE, EM bez headcount"*) — budget vapor, conflict
   of interest (advocate-as-measurer). → **Supersedes** ADR-0012 (0.5-0.7 FTE
   dedikovaný Senior PM, €100-150k OPEX, blind acceptance review delegated
   na external EM panel).
3. **Falsifiability** — fit criteria post-hoc redefinovatelné, statistický
   test nepre-registered, drift / fork nedetekovatelný. → **Addendum**
   ADR-0013 (Pre-registration discipline + Pflanzer Compliance Score).

Method Charter (`docs/methodology/method-charter.md`) v0.3 reflektuje výše uvedené.
Structure of this ADR (Kontext, Rozhodnutí, Důsledky níže) zůstává jako historický
záznam original v0.2.1 myšlenky; superseded částí jsou označené v textu.

**Dodatečné v0.3 changes mimo supersession:**
- **Practitioner vs Academic track** explicitně rozlišeny (charter `method-charter.md`
  § Practitioner vs Academic track).
- **Causal model (Theory of Why)** — kauzální diagram interventions → mediators →
  outcomes (z Akademik perspective, Akademik Gap 3).
- **Time-bounded kill criteria** (N + T+X mo whichever first; default Sunset po T+18 mo).
- **Stopping for harm rule** (kill immediately pokud ≥ 25 % handoff collapse).

## Kontext

Devil's advocate Útok 12 zachytil **intelektuální nedůslednost**: Pflanzer
požaduje, aby každý projekt měl Charter (XYZ hypotéza, success threshold,
kill criteria), ale **sám sebe této disciplíně nepodřizuje**. V dokumentech
metody (00–09 + ADRy) chybí:

- XYZ hypotéza pro metodu samotnou.
- Falsifying criterion (po jakém počtu pilotů metoda buď „funguje" nebo se
  killuje).
- Success/failure metrics na method-level (vs per-feature metrics, které
  metoda pokrývá).
- Comparison baseline (vs current state — sériový handoff).

To je *methodology that exempts itself from its own discipline*. Audit
committee otázka první minuty: *„Kolik pilotů prošlo, jaký je success rate,
jak ho měříte?"* — žádná odpověď.

## Rozhodnutí

Vznik **Pflanzer Method-Level Charteru** jako trvalý dokument
v `docs/methodology/method-charter.md`. Podléhá stejné disciplíně jako Charter
projektový (ADR-0004) — má XYZ, threshold, kill criteria, reinforcement track.

### Struktura Method-Level Charteru

```
# Pflanzer Method-Level Charter

## XYZ hypotéza (metoda)
Věříme, že Pflanzerova metoda zkrátí čas
od „nápad" k „handoff package" o ≥ 50 %
(z baseline 6–9 měsíců na 6–9 týdnů)
pro projekty splňující fit criteria z `01-filozofie-a-kdy-pouzit.md`,
s kvalitou handoff package srovnatelnou nebo vyšší než current state
(měřeno re-work % v T+90 a stakeholder NPS).

## Success threshold
- **Primary lagging metric**: čas „nápad → handoff" ≤ baseline / 2
  (měřeno per pilot, agregováno po N pilotech).
- **Leading metric** (T+30): handoff package akceptován dev týmem
  bez re-work block (≥ 80 % artefaktů použito).
- **Guardrail metric**: re-work v T+90 ≤ baseline current state
  (handoff není povrchní).
- **Stakeholder NPS**: cross-functional NPS po pilotu ≥ +20.

## Kill criteria
- **Po 3 pilotech**: pokud > 50 % pilotů zhasne po druhém cyklu
  (Decider+CPO silence triggered iterate → Kill).
- **Po 6 pilotech**: pokud average „nápad → handoff" ≥ baseline × 0.75
  (méně než 25 % zlepšení = nezájem).
- **Po 10 pilotech**: pokud nedosaženo 3+ self-sustaining BU
  (žádný organic Champion pipeline → method nepřežije bez vendor coach).

## Comparison baseline
Měříme proti **current state**: sériový handoff
(zadavatel → produkt → vývoj → test → security review → deploy)
v dané organizaci. Baseline metric collection 3 měsíce před prvním pilotem.

## Reinforcement track method-level
- **T+30 per pilot**: per-pilot retro (ADR-0004 reinforcement).
- **T+6 měsíců method-level**: agregace metrik napříč piloty,
  publikace report do CoP.
- **T+12 měsíců**: method-level review — keep / iterate / sunset.

## Decider method-level
- **CPO** nebo **Director of Engineering** s mandátem od exec committee.
- Method-level kill rozhodnutí dělá CPO/DoE, ne Champion.

## Role specific to method-level Charter
- **Method Steward** (1 osoba ve firmě) — sleduje metrics across pilots,
  publikuje T+6/T+12 reporty, agreguje retros do role catalog updatů.
  V malé organizaci může to být Champion-of-Champions.
```

## Validační loop

- **Method Steward** (nová role, nikoli #17 Champion) — má pravomoc
  navrhnout method-level Kill / sunset.
- Pokud je method-level Kill → projekty v progress doběhnou; nové se nestartují.
- ADR-0007 sám o sobě má auto-review po **6 pilotech** — review buďto
  potvrdí, doladí thresholdy nebo rozhodne o sunset.

## Důsledky

**Pozitivní:**
- Pflanzer dostává vlastní falsifying criterion.
- Audit committee má odpověď na *„jak víte, že to funguje?"*.
- Eliminuje *methodology drift* — bez method-level review se workshop metody
  stávají self-perpetuating bez dohledu.

**Negativní:**
- Vyžaduje **role Method Stewarda** (~10 % FTE) v organizaci.
- Vyžaduje **3-měsíční baseline collection** před prvním pilotem.
  Pro některé organizace to znamená odložit start o čtvrtletí.

**Mitigace:**
- Method Steward = může být Engineering Manager se zájmem o process
  improvement (žádná nová headcount).
- Baseline collection může být **light** (5–10 reprezentativních projektů
  s manuálním estimace) namísto plné instrumentace.

## Update existující dokumentace

- `00-tldr.md` — přidat sekci „Jak víme, že to funguje" s referencí na
  method-level Charter.
- `09-srovnani-existujici-metody.md` — přidat sloupec „self-validating"
  do srovnávací tabulky (Pflanzer = ano, většina ostatních = ne).
- README — odkaz na `docs/methodology/method-charter.md`.

## Reference

- Savoia, A. *The Right It* — pretotyping XYZ.
- Devil's advocate Útok 12.
- Spotify model post-mortem 2024 — methodology drift.
