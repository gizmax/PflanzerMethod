# ADR-0028 — Retro měří proti základně a sleduje nestabilitu

**Pflanzer Method | pflanzer.cz/method**

**Status:** Proposed · 2026-11-22
**Související:** ADR-0013 (pre-registrace), ADR-0014 (PflanzerIndex),
ADR-0024 (prahy a kalibrace), ADR-0025 (úseky review),
[`../research/vylepseni-2026-11.md`](../research/vylepseni-2026-11.md) § 4

## Kontext

Metoda o sobě říká, že důkazy o její účinnosti zatím neexistují a že je
má dodat měření pilotů. Dnešní měření na to nestačí ze tří důvodů:

1. **Chybí základna.** „Dny od Go do merge“ nejde vyhodnotit bez údaje,
   jak dlouho totéž trvalo v témže repu před pilotem. Dojem týmu ji
   nenahradí: v pokusu METR vývojáři čekali zrychlení o 24 %, po pokusu
   věřili ve 20 %, naměřeno bylo zpomalení o 19 %.
2. **Neměří se nestabilita.** DORA spojuje vyšší adopci AI s vyšší
   propustností i s vyšší nestabilitou dodávek. Readout T+7 „bugy
   a hotfixy“ je ruční zápis.
3. **Cíl „≥ 80 % LOC vítěze beze změny“ má špatný směr.** Trestá správné
   opravy a odměňuje kód, na který nikdo nesáhl.

## Varianty

| Varianta | Pro | Proti |
|----------|-----|-------|
| A. Stav dnes | Žádná práce | Výsledky pilotů nepůjde obhájit |
| **B. Základna z target repa, nestabilita z gitu a PR, přežití kódu jako údaj bez cíle** | Počítá se strojově z dat, která repo má; srovnatelné napříč piloty | Základna z historie není kontrolní skupina; malá repa mají málo dat |
| C. Kontrolovaný pokus (stejné zadání s metodou a bez) | Nejsilnější důkaz | Pro pilotní tým nereálné; METR sám naráží na to, že vývojáři odmítají pracovat bez AI |

## Rozhodnutí

Navrhuje se varianta **B**.

1. **Základna před pilotem.** `pflanzer doctor` (nebo `retro baseline`)
   spočítá z target repa za posledních 6 měsíců medián doby od otevření
   PR do merge a medián doby do prvního review. Uloží se k projektu před
   Kickoffem, aby ji výsledek pilotu nemohl ovlivnit (ADR-0013).
   Když má repo málo dat, zapíše se „základna není“ a výsledek se
   neporovnává.
2. **Nestabilita jako tvrdá metrika.** Na T+7 a T+30 retro spočítá
   z target repa reverty a opravné commity nad soubory vítěze; incidenty
   zůstávají ručním zápisem. Sleduje se vedle dnů, ne místo nich.
3. **Přežití kódu bez cíle.** % LOC vítěze beze změny zůstává jako údaj,
   cíl ≥ 80 % a FLAG se ruší. K přepsaným řádkům se na T+60 zapisuje důvod:
   oprava chyby / změna požadavku / refaktoring.
4. **Očekávání u prvního pilotu.** Dokumenty pro Decidera uvedou, že první
   pilot týmu má režii učení a metoda se hodnotí od druhého až třetího
   pilotu. Odkaz na „J-křivku“ ze zprávy DORA o ROI se doplní, až bude
   ověřen z primárního textu.
5. Reporty nikdy neuvádějí zrychlení jako dojem týmu; jen naměřené úseky
   vedle základny.

## Důsledky

- Mění kalibraci v ADR-0024 (přežití LOC už není kritérium samo o sobě;
  nahrazuje ho nestabilita) a vstupy ADR-0014.
- `pflanzer retro measure` a `report summary` mění výstup; `zacni.md`
  § Co měřit a `07` § Retro se přepíší.
- Základna z historie repa má zkreslení (jiné úkoly, jiné období).
  Je to nejlevnější dostupné srovnání, ne důkaz účinnosti.
