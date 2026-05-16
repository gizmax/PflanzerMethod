# ADR-0012 — Method Steward operational scope

**Status:** Accepted (v0.3)
**Date:** 2026-05-16
**Context source:** Autoresearch round „method-falsifiability" — perspektivy 01 (Method Steward), 03 (Skeptický VP Útok 3), 04 (Akademik Gap 8)
**Supersedes (partial):** ADR-0007 § *„Role specific to method-level Charter"* (Steward = *„10 % FTE, may be EM with interest"*).

## Kontext

ADR-0007 definuje Method Stewarda jako *„~10 % FTE, může být EM se zájmem
o process improvement, žádná nová headcount."* Autoresearch round na method
falsifiability identifikoval **3 fatální problémy** s touto formulací:

1. **Budget vapor** (Skeptický VP Útok 3). *„10 % FTE bez headcount"* znamená,
   že role je financována *„z volného času EM"*. V realitě EM má 100 %+
   committed capacity (capacity check je pre-flight gate, viz `02-role-catalog.md`
   #9). Steward role po 6 měsících mrtvá; T+6 report se nepíše.

2. **Conflict of interest** (Akademik Gap 8). Steward je *advocate* metody
   (drives adoption, publishes reports, defends Charter) **a zároveň** *measurer*
   úspěšnosti. Akademická literatura (Charmaz 2014, Cook & Campbell 1979)
   standardně vyžaduje **separation of advocate and rater**.

3. **Operational scope undefined** (Method Steward perspective bod #4 a #6).
   Charter nespecifikuje, co Steward MUSÍ dělat (vs nice-to-have), jakou kadenci,
   jaké selekční kritérium pro osobu. V reálu role attractuje *„someone who has
   time"*, ne *„someone who has accountability and skills"*.

## Rozhodnutí

### Method Steward profile (v0.3)

**Method Steward** = **dedikovaný 0.5-0.7 FTE Senior Product Manager** (nebo
Principal Engineer) s **≥ 5 lety v process improvement / engineering productivity**.
Hired do **Engineering Excellence CoE** (nebo equivalent: Process Portfolio
Office, Eng Effectiveness team).

**Fully-loaded annual cost:** **€100-150k** (band M3/M4 EU base, fully loaded
včetně benefits / overhead). V US kontextu odpovídá $130-200k fully loaded.

**Budget line:** Engineering Excellence OPEX → *„Process Portfolio Stewardship
→ Pflanzer Method"*. Sign-off pro budget: Method Decider (viz ADR-0011) jako
Accountable owner.

### Operating model (capacity allocation)

| Aktivita | % capacity | Cadence |
|----------|-----------|---------|
| Pilot facilitation + Champion coaching | 40 % | per pilot (~2 PD support per pilot) |
| Metric aggregation + T+6 / T+12 / quarterly readouts | 30 % | quarterly + 2 readouts/yr |
| Method Charter maintenance + ADR shepherding | 15 % | ongoing |
| Cross-org learning (peer conferences, external red team coordination) | 10 % | quarterly |
| Charter compliance audits (per pilot ex-post) | 5 % | per pilot completion |

**Steward role survival rule:** Pokud Steward role je **neobsazená > 90 kalendářních
dní** (z jakéhokoliv důvodu: turnover, hiring freeze, re-org), Method Charter
**automatically enters sunset mode** po dobu trvání vacancy. Nové piloty se
nestartují. Re-activation = nový hire + Method Decider memo *„Charter reactivated"*.

### Selekční kritéria pro Method Steward osobu

1. **Pilot experience required:** alumnus ≥ 1 Pflanzer pilotu jako Champion (#17)
   nebo Decider (#1). Steward bez first-hand pilot experience = filter fail.
2. **Conflict-of-interest disclosure (signed):** žádný osobní finanční / kariérní
   stake na Pflanzer adoption (Steward nezíská promotion / bonus na základě
   N pilots run; jen na kvalitě reporting).
3. **Cross-BU mandate:** Steward NESMÍ být v BU, kde aktuálně běží > 30 % pilotů
   v poolu (avoid hometown bias).

### Separation of advocate and measurer

Steward **NEPOČÍTÁ acceptance score** (současný Charter sliboval EM dev týmu;
v0.3 redefinováno):

- **EM dev týmu T+30**: operational acceptance signal (fast, biased — Champion
  pressure → +bias).
- **Blind external EM panel T+30** (3 EMs z jiných BU, average): bias guardrail.
  Detail v ADR-0014 (composite metric).
- **Steward** agreguje obě měření, **interpretuje** a **flag-uje
  rozpory** > 20 % delta.

Tato three-layer struktura odděluje:
- *Operational reality* (EM přijímá / nepřijímá artefakty),
- *Independent assessment* (external EMs hodnotí blind),
- *Method-level synthesis* (Steward interpretuje vs metoda XYZ).

### Direct line k Method Decider

Steward má **direct reporting line k Method Decider** (viz ADR-0011), ne přes
Champion-of-Champions ani CoE manažera. Důvod:
- Champion má adoption incentive (žije z metody) — Steward integrity může být
  v konfliktu.
- Direct line zaručuje, že early-kill veto (ADR-0011) může Steward eskalovat
  bez politického blokátoru.

## Důsledky

**Pozitivní:**
- **Role exists for real** (CFO-readable cost line). Není to *budget vapor*.
- **Conflict of interest mitigated** přes selekční kritéria + acceptance
  delegation na external EM panel.
- **Operational scope explicit** — Steward ví, co MUSÍ dělat, a Decider ví,
  co od něj očekávat.
- **Role survival rule** zabraňuje *„Steward nenastoupil, ale Charter
  v platnosti"* zombifikaci.

**Negativní:**
- **Cost line €100-150k/rok** musí být schválen v rozpočtovém procesu
  organizace **PŘED prvním pilotem**. Bez Engineering Excellence CoE / OPEX
  budget = Pflanzer pilot se nestartuje. To je intentional gate.
- **Recruitment latency**: dedikovaný hire trvá 3-6 měsíců. Pflanzer adoption
  tedy nemůže být *„let's start next month"* iniciativa. Bootstrap budget
  (ADR-0011 a budoucí baseline collection playbook) explicit overlap.

**Mitigace:**
- **Acting Method Steward** delegace: pokud hire trvá > 90 dní, jednorázová
  delegace na **senior interim** (externí konzultant nebo interní senior PM
  s ad-hoc 0.3 FTE) pro max **6 měsíců**, schválená Method Decider memo.
- Po 6 měsících interim → Charter sunset trigger (per role survival rule).

## Update existující dokumentace

- `ADR-0007` — addendum: *„Steward operational scope a profile specifikovan v ADR-0012."*
- `method-charter.md` — sekce *„Status"* → Steward profile updated; nová sekce
  *„Method Steward operational scope"*.
- `02-role-catalog.md` — Champion role (#17) sekce *„Vztah k Method Stewardovi"*
  updated: direct line is Steward → Decider, Champion is informed.

## Reference

- Devil's Advocate review Útok 3 (10 % FTE = budget vapor).
- Autoresearch perspektiva 01 (Method Steward) — bod #6 selekční kritéria.
- Autoresearch perspektiva 03 (Skeptický VP) — Útok 3, Změna #2.
- Autoresearch perspektiva 04 (Akademik) — Gap 8 Reflexivity / positionality.
- Charmaz, K. (2014). *Constructing Grounded Theory* — researcher positionality standard.
- Cook, T. & Campbell, D. (1979). *Quasi-Experimentation* — separation of evaluator and advocate.