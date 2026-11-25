# ADR-0025 — Review vítěze je plánovaný krok, ne ocas Shipu

**Pflanzer Method | pflanzer.cz/method**

**Status:** Accepted · 2026-11-25 (navrženo 2026-11-22)
**Související:** ADR-0010 (SHIP.md jako primární handoff), ADR-0017 (Async
okno), ADR-0021 (malá skupina, celá cesta), ADR-0024 (prahy),
[`../research/vylepseni-2026-11.md`](../research/vylepseni-2026-11.md) § 1

## Kontext

Metoda slibuje cestu do produkce, ale její poslední krok je „PR otevře
vlastník repa“ a review nechává na běžném procesu firmy. Data z roku 2026
ukazují, že právě tam se práce s agenty zasekává: po nasazení agentů
přibylo kódu o 30 %, ale doba review PR vzrostla o 49 % (Chen a Stratton,
jen ze sekundárního zdroje) a zátěž na reviewera se v jedné sledované firmě
zdvojnásobila (He a kol., abstrakt). Retro dnes měří dny od Go do merge
jedním číslem, takže není vidět, kolik z nich je čekání na review.

Metoda přitom má výhodu, kterou nevyužívá: technické role už v Asyncu
prošly diff a napsaly keep / fix / kill.

## Varianty

| Varianta | Pro | Proti |
|----------|-----|-------|
| A. Nechat review na firmě (stav dnes) | Žádná změna, respektuje CODEOWNERS | Nejpomalejší část cesty je mimo metodu a neměří se |
| **B. Pojmenovaný reviewer a okno v Kickoffu, Async jako předreview, strop velikosti PR, měření čekání** | Review má jméno a termín jako ostatní okna; reviewer zná kód před Shipem | Další jméno v Kickoffu; strop může vynutit rozřezání PR |
| C. Automatické AI review místo lidského | Rychlé | Review agentů agenty neříká nic o lidském dohledu (Duma a kol.); odporuje ADR-0023 |

## Rozhodnutí

Varianta **B**. Strop velikosti PR je zatím jen doporučení (bod 3).

1. **Reviewer vítěze má jméno v Kickoffu.** Je to člověk s právem approve
   v target repu, který není autorem (typicky druhý vývojář nebo vlastník
   kódu podle CODEOWNERS). Okno review se bookuje spolu s ostatními okny.
   Bez jména platí pravidlo „krok cesty bez jména = nesvolávat“.
2. **Async je předreview.** Reviewer píše keep / fix / kill nad diffem
   vítězné varianty už v Asyncu. V Shipu čte jen rozdíl od stavu, který
   viděl, a výsledek gates.
3. **Velikost PR vítěze jako doporučení, ne brána.** SHIP.md uvádí velikost
   diffu vítěze a nad orientační hranicí doporučí rozřezat PR na navazující
   části. Ship to neblokuje. Tvrdý strop zavede až nový ADR s daty z retra
   (velikost PR proti době review).
4. **Retro měří tři úseky místo jednoho:** Go → PR otevřen, PR otevřen →
   první review, první review → merge.
5. **AI review je povolené jako doplněk**, nikdy jako approve (ADR-0023).

## Důsledky

- Kickoff zadání má o jedno jméno víc; role card pro reviewera.
- `pflanzer retro measure` potřebuje časy z PR (přes `gh`), ne jen merge.
- Dokumenty k úpravě: `00-lean-pflanzer.md` (průběh), `05`, `07`,
  `zacni.md` § Co měřit.
- Ověření: po 5 pilotech porovnat úsek „PR otevřen → první review“
  s mediánem target repa před pilotem (ADR-0028).
