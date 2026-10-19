# Pro sponzora: co po vás chceme

**Pflanzer Method | pflanzer.cz/method**

> Jedna stránka pro člověka, který bude rozhodovat (Decider). Čtení: 3 minuty.

## Problém

Cesta od nápadu k funkční věci trvá měsíce: zadání putuje od byznysu
k produktu, k vývoji, k bezpečnosti a k provozu a každé předání ztrácí kontext.
Rozhodujete podle slajdů a specifikací, ne podle věci, kterou si můžete
vyzkoušet.

## Co dostanete

Za zhruba týden:

- **tři běžící varianty** řešení na našem reálném repu — otevřete je
  v prohlížeči, nejsou to mockupy;
- **rozhodnutí nad kódem**: Go, Kill, nebo jedno kolo úprav (Iterate);
- **vítěze jako pull request**, který prošel automatickými kontrolami
  a podpisy bezpečnosti a provozu, nic se nepřepisuje;
- **zápis rozhodnutí v gitu**: kdo co rozhodl, proč, kdo podepsal.

## Co potřebujeme od vás

1. **Mandát říct Go i Kill.** Když nemůžete zastavit, nejste Decider.
2. **15 minut na začátku** (Kickoff): odsouhlasíte problém v jedné větě,
   jedno číslo úspěchu a kdy to zabalíme.
3. **90 minut na konci** (Rozhodnutí): uvidíte varianty běžet, vyslechnete
   tři největší spory a rozhodnete. Hlasujete **poslední**, aby tým
   neříkal to, co chcete slyšet.
4. **Jména**: koho pověřujete za produkt, design, vývoj, bezpečnost & právo
   a provoz.

Nic víc. Na stavbě nemusíte být. Peníze navíc nejsou potřeba, kromě licence
Claude Code, kterou vývojáři už mají; spotřeba AI se měří a uvidíte ji
v závěrečném zápisu.

## Riziko a jak je řízené

| Obava | Co ji hlídá |
|-------|-------------|
| „AI napíše nebezpečný kód" | 20minutový **checkpoint** bezpečnosti & práva nad běžícími variantami; bez podpisu se nic nenasadí |
| „Nikdo za to neručí" | rozhodnutí a podpisy s **jmény** v `.pflanzer/decisions/` (git) |
| „Kód nebude dost dobrý" | **automatické kontroly** (lint, testy, build, bezpečnost) jen na vítěze; pod skóre 80 (pilot) / 85 (produkce) nejde dál bez vaší výslovné výjimky |
| „Utratíme víc, než čekáme" | strop nákladů na AI se potvrzuje v checkpointu a spotřeba je v zápisu |
| „Bude to nekonečné" | Iterate jen jednou; potom Go nebo Kill |
| „Chybí nám specialista" | AI připraví předkontrolu, ale u pilotu a produkce **podepisuje vždy člověk**; vás (Decidera) a vývoj AI nenahrazuje nikdy |
| „Security nám nepodepíše" | rozhodnete vy: u pilotu bez osobních dat můžete riziko vědomě převzít (`--override-triage`, zapíše se vaše jméno); právo to nepokrývá |
| „Chci být na Buildu" | ne, ať váš názor netáhne hlasování; dostanete 10min screencast z Buildu a na Rozhodnutí uvidíte varianty živě |

## Hotový e-mail

**Předmět:** Pilot Pflanzer Method: potřebuju vás na 15 min + 90 min

> Dobrý den,
>
> chceme vyzkoušet postup, kde za zhruba týden máme tři běžící varianty
> řešení [problém v jedné větě] na našem reálném repu a vy nad nimi
> rozhodnete. Vítěz půjde jako pull request přes naše běžné kontroly.
>
> Potřebuji od vás:
> 1. Mandát říct Go i Kill.
> 2. 15 minut na Kickoff: [datum, čas] (problém, číslo úspěchu, kdy končíme).
> 3. 90 minut na Rozhodnutí: [datum, čas] (uvidíte varianty běžet a rozhodnete).
>
> Na stavbě být nemusíte. Přehled na jedné stránce:
> https://pflanzer.cz/method
>
> Děkuji,
> [jméno]

Další krok pro vás: pošlete e-mail a zablokujte si oba termíny. Zbytek
zařídí PdM podle [`zacni.md`](zacni.md).
