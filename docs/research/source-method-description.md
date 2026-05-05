# Pflanzerova metoda — zdrojový popis (verze 0)

> Originální popis od autora (Tom / GiZMaX), z kterého vychází autoresearch.
> **Tento dokument se nemění**; je to fixed input pro expertní panel
> a referenční bod pro syntézu.

## Cíl metody

Vytvořit **prostor pro společné vajbeni celého týmu** — místo, kde se v korporátu
prosadí zrychlení agentního vývoje tím, že se zástupci jednotlivých týmů na cestě
přivedou do jedné místnosti (prostoru).

## Proč

Normálně by si to mohl navibekódit jen zadavatel sám, ale pak narazí na problémy
s implementací a schválením dalších týmů. Bez všech stran u stolu vznikají
dlouhé pinkací smyčky:

> Zadavatel dostane nápad → pošle to produktu → dlouho se to pinká →
> vznikne zadání → pinká se s programátory → za chvilku je rok pryč.

## Princip Pflanzerovy metody

1. **Hlavní přípravy** se udělají před první session (vstupy, podklady).
2. **Session 1** — všechny strany v jedné místnosti (zadavatel, produkt,
   programátoři, security, …). Intenzivně se vibekóduje. **Výstup: 1–3 mockupy
   a jejich preference.**
3. **Mezi sessions** vznikne **klikací prototyp v několika verzích** s rozcestníkem
   a popisem rozdílů. Sbírá se **jednoduché hodnocení a feedback dle oddělení**.
4. **Session 2** — všichni se znovu sejdou. Představí se připomínky.
   **AI model vede výklad**, jaké oddělení mělo jaké připomínky, a navrhuje,
   **jak to zapracovat**. Připomínky mají **score závaznosti**.
5. Tým rozhodne: **další session** / **final → handoff do vývoje**.

## Vstupy do Session 1 (předem připravit)

- **Demo data** (poprvé vygenerovaná, pokud potřeba).
- **Grafická inspirace** (manuál nebo načtení z webu).
- **Vstup od programátorů**: jazyk (Node.js / jiný), jak má vypadat správně
  popsaný kód, jak má vypadat dokumentace, *(doplnit, co všechno tam programátor
  může chtít — toto je úkol pro expertní panel)*.
- *(Další vstupy doplňuje expertní panel ze svých rolí.)*

Všechny podklady jsou **vstupem pro Claude / jiný model** a **AI session provází**.

## Důležité atributy

- **Programátoři jsou u tvorby klikacího prototypu** → handoff do vývoje pak
  proběhne hladce, protože už metodu spoluvytvářeli.
- **AI model vede session 2** s návrhy, jak připomínky zapracovat, a sám dává
  feedback k jejich návrhům.
- **Připomínky jsou skórované** dle závaznosti.

## Co metoda explicitně neřeší v původní verzi

- Co když některé oddělení nepřijde / vetuje?
- Jak metoda škáluje na různé velikosti zadání?
- Jak interaguje s existujícími korporátními procesy (sprint, PI planning, …)?
- Jak se metoda vyrovnává s regulovanými projekty (compliance, audit trail)?
- Kdo a jak vybírá role, které do session zapojit?
- Co dělat, pokud expertní panel v session 2 mezi sebou silně nesouhlasí?

→ Tyto a další otevřené body jsou předmětem expertního autoresearche.

## Cíl autoresearche

1. **Doladit** každý krok metody pohledy z různých rolí.
2. **Generalizovat** ji do podoby reusable corporate frameworku.
3. **Pojmenovat edge cases** a navrhnout pro ně řešení.
4. **Porovnat** s adjacent metodami (Design Sprint, LDJ, Lean Inception, …)
   a říct, kdy je která lepší.
