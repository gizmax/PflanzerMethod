# ADR-0011 — Method Decider profile + Default Sunset

**Status:** Accepted (v0.3)
**Date:** 2026-05-16
**Context source:** Autoresearch round „method-falsifiability" — perspektiva 03 Skeptický VP (Útoky 1 a 2), perspektiva 01 Method Steward (otevřená otázka #2)
**Supersedes (partial):** ADR-0007 § *„Decider method-level"* — tato ADR redefinuje Decider profil a sunset logiku.

## Kontext

ADR-0007 definuje Method Decidera jako *„CPO nebo Director of Engineering
s mandátem od exec committee."* Autoresearch round na method falsifiability
(autumn 2026) identifikoval **3 institucionální patterny**, které tuhle
formulaci v korporátní realitě (5000+ FTE, regulated industry) likvidují:

1. **CPO/DoE tenure profile.** Mediánová tenure CPO = 2.3 roku (Russell
   Reynolds EU banking 2024). T+12 / T+18 / T+30 review milestones se
   nesetkávají s jedním Deciderem. 3× změna CPO za 30 měsíců = Method
   Steward píše report do prázdné posluchárny.

2. **Sunk-cost asymmetry.** CPO, který Pflanzer schválil v Q1 Y1, ho
   v Q3 Y2 nezabije — buď ho zabije jeho nástupce, nebo se metoda
   *zombifikuje* (formálně žije v CoE katalogu, nikdo si nevybírá).
   Reputational risk asymmetry: positive Keep = +10 reputation; positive
   Sunset = -60 reputation pokud později někdo ukáže success case study.

3. **Exec committee agenda saturation.** Exec committee se v bance schází
   4× ročně, 30+ položek per session. „Sunset Pflanzer methodology"
   je položka, kterou CEO 2× odloží, třetí pokus se konsoliduje do
   *„transformation portfolio review"* — Pflanzer zmizí mezi 18 dalšími
   iniciativami bez explicitního rozhodnutí. **Žádný papír, žádný kill log.**

Současná Charter formulace má **default = pokračujeme, sunset vyžaduje
aktivní podpis**. To je v korp organizaci self-perpetuating — sunset
se nestane nikdy.

## Rozhodnutí

### Method Decider profile (v0.3)

**Method Decider** = **VP Engineering Effectiveness** (nebo equivalent: Head of
Engineering Excellence, Head of Process Portfolio Management). Pozice
**2 úrovně pod CTO/CIO**, ne v exec committee.

Required tenure profile:
- Minimum 3 roky předpokládaná tenure v roli (pokud hire externí, preference
  kandidáti s 7+ let v engineering productivity / process management).
- Není politicky exponovaný hráč (NE M&A, NE quarterly earnings, NE board reporting).

Job description Method Decidera **musí explicitně obsahovat:**
- Process portfolio management včetně sunset rozhodnutí.
- Quarterly accountability do Process Portfolio Review meeting (nebo equivalent
  governance body, který má rozpočtovou pravomoc).
- RACI: **Accountable** pro Pflanzer keep / iterate / sunset rozhodnutí.

**Exec committee role:** **Informed** (1× ročně summary), ne Accountable a ne
Consulted per decision. Tato delegace ven z exec committee je primární funkcí
Method Decider role.

### Default Sunset logic

**Charter rule (zapsáno doslova do `method-charter.md`):**

> **T+18 měsíců od první pilot kick-off** je sunset checkpoint. Pokud Method
> Decider **explicitně nepotvrdí Keep písemně** (signed memo do Process
> Portfolio Review minutes nejpozději v měsíci T+18), **default state = Sunset**.
> Sunset = projekty v progress doběhnou, Charter freeze, role catalog archived
> to read-only Confluence space.
>
> Re-activation post-sunset vyžaduje **nový ADR** s explicit re-baselining
> + Process Portfolio Review endorsement (nemůže se to stát latentně /
> implicitně).

### Method Steward early-kill veto

Method Steward má pravomoc **kdykoli mezi T+0 a T+18 mo** svolat **emergency
method-level review** s Method Deciderem, pokud:
- 2+ leading indicators (viz `method-charter.md` § Leading indicators) porušují
  threshold po dobu > 60 dní, NEBO
- ≥ 25 % pilotů v poolu má dokumentovaný handoff collapse (0 % artifact
  utilization v T+30 — *„stopping for harm"* per Data analyst Flaw 4).

Emergency review následuje stejný formát jako T+12 review (60-min dedicated
meeting, 5-pager pre-read, decision log signed v meetingu, external observer
volitelný).

## Důsledky

**Pozitivní:**
- **Tenure align s milestones.** Method Decider 4-7 let překryje T+18 mo + reactivation cycles.
- **Default Sunset obrátí inertia** — burden of proof na pokračování, ne na sunset.
  Zombifikace patternu (Spotify) eliminována.
- **Exec committee odlehčeno** — 1× ročně summary, ne quarterly debata.
- **Steward early-kill veto** brání *„we need more pilots to know"* lock-in.

**Negativní:**
- **Method Decider role** musí existovat v cílové organizaci. Pokud org nemá VP
  Eng Effectiveness ani equivalent, Pflanzer pilot se **nestartuje** — to je
  early Sunset trigger sám o sobě (org nemá governance fit).
- **Default Sunset** generuje politický pressure: každý T+18 měsíc je decision
  point, který musí proběhnout. Pokud Method Decider je na PTO / role neobsazená,
  default Sunset triggers — to je intentional.

**Mitigace:**
- ADR-0012 (Method Steward operational scope) dovoluje **acting Method Decider**
  delegaci pokud role > 30 dní vacancy, ale pouze pro Keep memo s ≤ 30-day extension.
- Re-activation post-sunset má jasný proces (nový ADR + Process Portfolio Review
  endorsement) — sunset není permanent kill, je to *reset s explicit re-baselining*.

## v0.4 addendum — Track S adoption emergency trigger (2026-05-28)

Per ADR-0020 dual-track model, Method Decider gets **new emergency review
trigger** for Track S adoption drift (Tom decision 2026-05-28, Recommended
default):

> **> 50 % Track S/BU per quarter** triggers Method Decider emergency review
> within 14 days. Method Steward audituje quarterly Compliance Score #13
> (Charter track designation + justification, per ADR-0013 v0.4 addendum).
> If > 50 % pilots in given BU went Track S during quarter, Steward submits
> mandatory escalation report to Method Decider + BU AI CoE Lead.

**Rationale:** Pflanzer Track S adoption gravity je #1 strukturální risk
(Spotify precedent: 22 % SAFe XP pair programming → 3.5 %). Without
threshold trigger, BU drift detection happens late. 50 % is middle-ground:
catches drift bez over-policing valid Track S adoption v regulated
industries.

**Alternative thresholds considered:**
- 30 % (stricter): false positives v finance/healthcare BUs where Track S
  is legitimate majority
- 70 % (looser): drift catches late
- 3 consecutive Track S pilots (absolute): considered, but ratio captures
  systemic pattern better

**Emergency review options for Method Decider:**
- **Keep current adoption** — accept BU rationale (legitimate Track S use cases)
- **Iterate** — joint Method Steward + BU AI CoE Lead intervention to
  restore Track P preference (training, Charter coaching, dev availability fix)
- **Sunset Pflanzer for that BU** — if root cause is „cannot sustain Track P,"
  Pflanzer is wrong fit. Method Charter scope reduction.

## Update existující dokumentace

- `ADR-0007` — addendum: *„Decider profile a sunset default specifikováno v ADR-0011."*
- `method-charter.md` — sekce *„Status"* → Method Decider profile updated;
  nová sekce *„Default Sunset checkpoint"*; *„Validační loop & sunset"* sekce updated.
- `ADR-0020 v0.4` — references this addendum for Track S adoption emergency trigger.

## Reference

- Russell Reynolds Associates (2024). *EU banking CPO turnover study* (mediánová tenure 2.3 r).
- Knapp, J. *Sprint* — decider mandate concept.
- Devil's Advocate review Útok 12 + autoresearch perspektiva 03 (Skeptický VP).
- ADR-0001 § Decider eskalační protokol (komplementární, ne nahrazený).
- ADR-0007 — Method-Level Charter (rámec, ke kterému toto ADR je addendum).