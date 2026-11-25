# ADR-0027 — Porozumění vítězi se ověřuje před Shipem

**Pflanzer Method | pflanzer.cz/method**

**Status:** Accepted · 2026-11-25 (navrženo 2026-11-22)
**Související:** ADR-0005 (default evolve: vítěz jde do produkce),
ADR-0010 (SHIP.md), ADR-0025 (review vítěze),
[`../research/vylepseni-2026-11.md`](../research/vylepseni-2026-11.md) § 3

## Kontext

Vítěz je kód, který z velké části napsala AI a který jde do produkce
(ADR-0005). Diff walkthrough dnes dělá pár, který variantu stavěl, třemi
větami (reuse / nové / mock). Nikdo neověřuje, že kódu rozumí i ten, kdo ho
bude udržovat, a nikde se nezapisuje, proč je navržený právě takhle.

Zdroje: randomizovaný pokus Shen a Tamkin (52 účastníků, o 17 % horší
výsledek v testu porozumění u skupiny s AI, nejvíc v ladění); Storey
(kognitivní dluh v lidech, intent dluh v zapsaných znalostech); Lyu a kol.
(týmy přijímají kód dřív, než ho umějí vysvětlit, a vracení údržby AI dluh
jen obchází). Všechny tři mají úzký záběr, viz rešerše.

## Varianty

| Varianta | Pro | Proti |
|----------|-----|-------|
| A. Stav dnes (walkthrough autorů) | Rychlé | Ověřuje, že autoři umějí kód popsat, ne že mu rozumí tým |
| **B. Vysvětlení a malá změna od vývojáře, který vítěze nestavěl, plus věty „proč“ v SHIP.md** | Levné (zhruba 30 min), ověřuje přesně to, co bude potřeba při prvním incidentu | Potřebuje druhého vývojáře; u jednoho vývojáře v jádru nejde |
| C. Formální test porozumění nebo povinná dokumentace | Měřitelné | Režie; jde proti „co NEpřebírat“ (těžká specifikace) |

## Rozhodnutí

Varianta **B**, zaváděná ve dvou krocích: věty „proč“ (bod 3) hned, vysvětlení zpět a malá změna (body 1 a 2) jako doporučený krok, který Ship neblokuje.

1. **Vysvětlení zpět.** Před `pflanzer ship` vítěze projde vývojář, který
   u jeho klávesnice neseděl (typicky reviewer z ADR-0025), a vlastními
   slovy popíše datový tok a tři místa, kde by hledal chybu.
2. **Jedna malá změna bez AI.** Tentýž člověk udělá ve vítězi jednu
   drobnou úpravu ručně (například změnu validace nebo textu chyby)
   a pustí testy. Když to nejde v rozumném čase, je to nález závažnosti
   Důležité a důvod zvážit Iterate.
3. **Věty „proč“ v SHIP.md.** Ke každému většímu návrhovému rozhodnutí
   vítěze (nová závislost, nový datový model, obejití existující
   komponenty) jedna věta zdůvodnění. První draft smí napsat AI, potvrzuje
   ho autor.
4. **Jeden vývojář v jádru:** bod 1 a 2 udělá zástupce Provozu nebo
   reviewer mimo jádro; když není nikdo, zapíše se to do SHIP.md jako
   otevřené riziko, které Decider vědomě přebírá.
5. Není to brána se skóre a Ship to neblokuje. Výsledek je zápis v decision
   logu (kdo, kdy, co změnil, jak dlouho to trvalo); když krok neproběhl,
   SHIP.md to uvede jako otevřené riziko.
6. **Přehodnocení po 5 pilotech:** podle údaje z retra (kdo opravoval první
   chybu a jestli to zvládl bez autora) se rozhodne, zda z bodů 1 a 2
   udělat povinný krok, nebo je zrušit.

## Důsledky

- Ship je o zhruba 30 minut delší; šablona SHIP.md má novou sekci.
- `07-handoff-do-vyvoje.md` § checklist a tři otázky reviewera se doplní.
- Retro má na T+7 a T+30 nový údaj: kdo opravoval první chybu ve vítězi
  a jestli to zvládl bez autora. To je ověření, že pravidlo k něčemu je.
