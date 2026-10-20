# ADR-0024 — Prahy Ship skóre (80 / 85) a závaznosti (60 %): výchozí hypotéza

**Pflanzer Method | pflanzer.cz/method**

**Status:** Accepted · 2026-10-20
**Související:** ADR-0001 (Decider), ADR-0021 (malá skupina, celá cesta),
ADR-0023 (AI náhrada chybějícího zástupce: AI nikdy není podpis),
`tool/cli/quality_gates.py` (`GATE_WEIGHTS`, `PRODUCTION_TARGET`, `MIN_GATES_RUN`),
`tool/cli/session_2.py` (`COMMITMENT_THRESHOLD`)

## Kontext

Metoda používá tři čísla, která nikde nemají zdůvodnění: práh Ship skóre
**pilot 80 / production 85**, **váhy bran** a **60% práh závaznosti** (od
kdy Rozhodnutí doporučí Go). Pro komisi nebo vedení jsou to „magická čísla“:
nevědí, odkud jsou, kdo je smí změnit a jak se dozví, že jsou špatně.

## Jak se skóre počítá (podle kódu)

`aggregate_score` v `quality_gates.py`:

1. Každá brána dá stav: `pass` = 1,0, `warn` = 0,5, `fail` = 0,0.
   `skipped` (SKIP, včetně „NEOVĚŘENO“) a `unsupported` **nemají hodnotu a
   vypadnou i ze jmenovatele**; nezhorší skóre, ale ani ho nezvednou.
2. Skóre = `round(100 × Σ(hodnota × váha) / Σ váha)` jen přes brány, které
   reálně běžely, oříznuté na 0–100.
3. Váhy (`GATE_WEIGHTS`): acceptance 2,5; tests 2,0; security 2,0; build 1,5;
   types 1,5; smoke 1,5; lint 1,0; coverage 1,0; a11y 1,0; observability 0,5.
   Pořadí vychází z toho, co nejvíc vypovídá o tom, že kód funguje a dělá,
   co Decider chtěl (acceptance scénáře jsou ground truth, tests a security
   jsou síť proti regresi a blockerům), a co jen doplňuje (lint, observability).
4. **Minimum důkazů** (`gates_sufficiency`): práh lze potvrdit jen při aspoň
   `MIN_GATES_RUN` = 4 spuštěných branách, mezi nimi `build` a `tests`. Pod
   `MIN_SOLID_GATES` = 5 je skóre jen „orientační“. Při nedostatku důkazů
   report nepíše „splňuje práh“, ale „práh nelze potvrdit“.

Z toho plyne hlavní sdělení: **důležitější než samotné číslo je, nad kolika
branami vzniklo.** Skóre 100 nad třemi branami neříká nic; skóre 82 nad osmi
ano. Proto věta v reportu (`pflanzer ship`, `pflanzer report summary`) vždy zní
„Skóre X ze 100 — … Spočteno nad N branami“ a doplní, co zůstalo neověřeno.
Číslo se nikdy nezveřejňuje bez N.

## Varianty

| Varianta | Pro | Proti |
|----------|-----|-------|
| **A. Pevné výchozí číslo (80 / 85), přebitelné Deciderem** | Srozumitelné, srovnatelné napříč projekty, nulová konfigurace | Může být pro konkrétní tým příliš přísné či volné |
| B. Práh per tým / per projekt od začátku | Přesné | Bez dat je to jen jiné odhadnuté číslo; tým si ho nastaví tak, aby prošel |
| C. Bez prahu, jen skóre | Nikdo nesoudí podle jednoho čísla | Ship pak nemá jasnou hranici; „rychlý kód, který nikdo nepodepsal“ |
| D. Jen blokující brány (build, tests, security), bez skóre | Jednoduché, tvrdé | Ztrácí se gradace (warn, pokrytí, a11y) a vedení nevidí trend |

## Rozhodnutí

Varianta **A**, doplněná o minimum důkazů z bodu 4 (z varianty D přebíráme
tvrdost: bez `build` a `tests` se práh nepotvrdí).

1. **Výchozí hodnoty: pilot 80, production 85, throwaway informativní (0).**
   Production je přísnější, protože chyba jde k zákazníkům; rozdíl 5 bodů
   odpovídá zhruba jedné vynechané či warnující střední bráně. **Jsou to
   hypotézy, ne zjištění.** V `session_3.py` je pilot výchozí 80, v
   `quality_gates.py` je `PRODUCTION_TARGET` = 85.
2. **Práh závaznosti 60 %.** `commitment_index` = součet `commitment_level`
   (0–3) zástupců u vedoucí varianty Buildu / (3 × počet hodnocení), tedy
   průměrná úroveň aspoň 1,8 ze 3. Smysl: tým se za vítěze „aspoň převážně
   postaví“, ne jen mu nevadí. `pflanzer decide` pod 60 % nedoporučí Go.
   Konstanta je jedna pro všechny projekty; původní TODO na pole v Charteru
   se **ruší**: per-projektová hodnota by byla varianta B bez dat.
3. **Kdo smí práh měnit nebo přebít: jen Decider, vědomě, s důvodem.**
   - Skóre pod prahem: `pflanzer ship --slug S --override-threshold
     --rationale "…"`; jméno a důvod jdou do decision logu, SHIP.md a PR.
   - Go pod prahem závaznosti: `pflanzer decide --slug S go --winner X
     --force --rationale "…"`.
   - **Nikdy AI** (ADR-0023): AI práh nepřebíjí, nesnižuje ani nepotvrzuje
     za člověka.
   - **Throwaway** má skóre informativní; Ship neblokuje, nepřebíjí se.
   - Změna výchozích hodnot v kódu = nový ADR s daty z retra.

## Kalibrace (jak se hypotéza ověří)

`pflanzer retro` sbírá outcome po Shipu: % LOC vítěze, které přežilo v
produkci, days-to-prod a incidenty, na T+30 a T+90. Pro každý projekt se k
tomu uloží skóre, N bran, závaznost a zda šlo o přebití. Vyhodnocení:

- Projekty **nad prahem** s incidenty nebo nízkým přežitím LOC → práh je
  příliš volný (nebo chybí brána); zvážit zvýšení či jinou váhu.
- Projekty **přebité pod prahem**, které dopadly dobře → práh je příliš
  přísný, nebo váha brány neodpovídá riziku.
- Závaznost: koreluje-li ≥ 60 % s přežitím LOC a days-to-prod, ponechat;
  jinak posunout.
- **Přehodnocení po 5 pilotech** s daty T+30 (pak znovu po T+90). Do té doby
  se hodnoty nemění „podle pocitu“.

## Důsledky

- Komise dostane odpověď na „odkud je 80“: výchozí hypotéza, kterou ověřuje
  retro, s pojmenovaným místem a termínem revize.
- Vedení čte skóre vždy s počtem bran (`pflanzer report summary`), takže
  vysoké číslo nad málem bran nepůsobí jako jistota.
- Riziko: tým bude přebíjení používat rutinně. Mitigace: každé přebití je
  jmenovité, s důvodem, viditelné v reportu a počítané v retru (podíl
  přebitých projektů).
- Riziko: skóre se dá „vylepšit“ vypnutím bran. Mitigace: SKIP/NEOVĚŘENO se
  v reportu vypisuje a minimum 4 bran včetně build a tests brání potvrzení
  prahu.
