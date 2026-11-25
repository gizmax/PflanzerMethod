# Vibe coding ve firmách: co říkají studie a co z nich plyne pro metodu

**Pflanzer Method | pflanzer.cz/method**

> Rešerše 2026-11-25. Třetí v řadě po
> [`srovnani-metod-2026.md`](srovnani-metod-2026.md) (jiné metody)
> a [`vylepseni-2026-11.md`](vylepseni-2026-11.md) (studie o vývoji s agenty).
> Tady jde o studie, které popisují, **jak lidé ve firmách s AI skutečně
> staví**: profesionální vývojáři, ne-vývojáři (produkt, design) a smíšené
> týmy. U každého zdroje je uvedeno, co bylo přečteno.

## Shrnutí

- **Profesionálové „nevibují“, řídí.** Zkušení vývojáři si drží návrh
  a architekturu, plánují před stavbou a ověřují každý výstup. To metoda
  potvrzuje pravidlem „u klávesnice sedí vývojář“.
- **Ne-vývojáři staví, ale neověřují.** Designéři a produktoví manažeři
  dnes umějí sami postavit funkční prototyp; ověřit, opravit a napojit ho
  na backend neumějí. Metoda s takovým prototypem nepočítá jako se
  vstupem, přitom ve firmách vzniká čím dál častěji mimo IT.
- **Když zadání píše AI, výsledek se zhoršuje; když ho píše člověk
  a AI hodnotí, zlepšuje se.** V metodě prompty pro varianty generuje
  nástroj.
- **Bezpečnost AI kódu se zlepšuje pomalu a nerovnoměrně** a nejčastější
  kritická chyba ve vibe-coded aplikacích je vypnuté řízení přístupu
  k datům.
- Z toho pět návrhů. Žádný nemění model účasti; jeden (vstup prototypu
  z byznysu) je kandidát na ADR.

Limit: studií přímo o firemních týmech je málo. Většina akademických prací
stojí na rozhovorech, dotaznících a malých vzorcích; čísla o bezpečnosti
pocházejí hlavně od firem, které prodávají skenery.

## 1. Jak pracují profesionálové

- Huang a kol., arXiv 2512.14012, „Professional Software Developers Don't
  Vibe, They Control“. Pozorování 13 zkušených vývojářů a dotazník 99
  vývojářů. Vývojáři si drží kontrolu nad návrhem a implementací; plán
  dělí do souborů a pouští po malých částech; výstup ověřují ručním
  testem UI, testy, čtením diffu a debuggerem. Agenti se podle nich hodí
  na dobře popsané, přímočaré úkoly. Limit: dotazník záměrně oslovil
  vývojáře nakloněné AI; jedno 45minutové pozorování na osobu.
  *Přečteno: abstrakt a HTML, část přes strojové shrnutí.*
- Stack Overflow, bleskový průzkum z dubna 2026 (1 100 respondentů,
  zveřejněno 27. 5. 2026). Agenty v práci používá 59 % (v roce 2025
  31 %), denně 37 %. 63 % je nikdy nebo zřídka nechá běžet bez dohledu
  a 60 % jim blokuje neschválené změny systému. Limit: samovýběr,
  srovnání s jiným průzkumem.
  *Přečteno: primární článek.*
- Stack Overflow Developer Survey 2026 (30 903 odpovědí). Nejčastější
  odpověď na otázku důvěry (48 %): „věřím, když výstup můžu snadno
  ověřit“.
  *Přečteno: primární stránka výsledků. O vibe codingu na ní nic není.*
- Chou a kol., arXiv 2512.22418 (ESEC/FSE 2026), „Building Software by
  Rolling the Dice“. Rozbor 20 videí. Ladění s AI autoři popisují jako
  házení kostkou; někteří autoři kód vůbec nečtou, jiní ho kontrolují
  výběrově. Kontrolu drží návrat změn, verzování, malé změny, testy
  a linter. Limit: jen YouTube, ne firemní práce.
  *Přečteno: abstrakt a HTML, část přes strojové shrnutí.*

**Pro metodu:** potvrzuje vývojáře u klávesnice, průběžné kontroly
a malé commity. Chybí výslovný krok „plán před stavbou“ (návrh 3).

## 2. Ne-vývojáři a smíšené týmy

- Fawzy, Tahir, Blincoe, arXiv 2605.24521, „From Prompting to
  Verification“. Dotazník, 162 respondentů ve třech stejně velkých
  skupinách (ne-vývojáři, začátečníci, profesionálové). Vnímání nástrojů
  je podobné, chování se liší: asi 45 % profesionálů kód před použitím
  kontroluje vždy; ne-vývojáři byli jediná skupina, kde někdo odpověděl,
  že nekontroluje nikdy. Méně zkušení častěji zadávají znovu, místo aby
  chybu hledali. Limit: vlastní výpovědi v jednom okamžiku.
  *Přečteno: abstrakt a HTML, část přes strojové shrnutí.*
- Li a kol., arXiv 2509.10652 (CHIWORK '26), „Vibe Coding in Product
  Teams“. 22 rozhovorů (9 designérů, 4 inženýři, 2 produktoví manažeři,
  3 výzkumníci, 4 zakladatelé), 13 z velkých firem. Designéři a PM
  stavěli funkční prototypy sami a předávky mezi rolemi se zkrátily.
  Hlavní překážka bylo napojení na backend, API a databáze; nasazení se
  rozbíjelo, kontext se ztrácel a rychlost vedla k přepisování.
  Vlastnictví podle autorů „není spojené s tím, kdo kód spustil, ale
  s tím, kdo určil záměr“. Limit: mnoho účastníků používá vibe coding
  hlavně na prototypy, ne na produkci.
  *Přečteno: abstrakt a HTML; část o vlastnictví a předávkách přes
  strojové shrnutí.*
- Pimenova a kol., arXiv 2509.12491, „Good Vibrations?“. 134 veřejných
  příspěvků, přes 5 000 komentářů, 11 rozhovorů. Mezi bolestmi je zátěž
  z review a tření, když ne-inženýři odevzdávají práci vytvořenou AI
  inženýrskému týmu.
  *Přečteno: abstrakt a HTML, část přes strojové shrnutí.*
- Adobe Design (tým Firefly), zkušenost z praxe: produktový manažer, tři
  inženýři a designér postavili za osm pracovních dní dvě funkce do
  produkčního buildu. Spolupráce podle autora zesílila, nezmizela; méně
  času ve Figmě, víc ve stavbě; okrajové případy a přístupnost šly
  testovat dřív. Bez metrik.
  *Přečteno: primární článek.*
- PA Consulting, workshop 15 lidí, jedno odpoledne. Chatové nástroje byly
  „pro jednoho hráče“, výsledek měl generický vzhled, kód potřeboval
  inženýrskou kontrolu. Marketingový text konzultační firmy, bez metrik.
  *Přečteno: primární článek.*

**Pro metodu:** velikost a složení týmu Adobe (5 lidí, 8 dní) odpovídá
jádru a kalendáři metody. Nové je, že prototyp od ne-vývojáře existuje
stále častěji **dřív než Kickoff** a metoda pro něj nemá místo (návrh 1).

## 3. Kdo má zadávat a kdo hodnotit

- Hu a kol., arXiv 2602.10473, „Why Human Guidance Matters in
  Collaborative Vibe Coding“. 20 pokusů, 737 účastníků, úkol: postupně
  vylepšovat obrázek zapsaný kódem. Když pokyny psal člověk, výsledek se
  s iteracemi zlepšoval (o 23,4 %); když je psala AI, zhoršoval se.
  Zkrácení pokynů AI to nespravilo. Nejlépe vyšlo, když člověk zadával
  a AI hodnotila. AI hodnotitelé dávali přednost vlastním dřívějším
  výstupům. Limit: zjednodušený úkol, ne profesionální tým; jeden model
  v každé roli.
  *Přečteno: abstrakt a HTML, část přes strojové shrnutí.*

**Pro metodu:** prompty variant dnes generuje `pflanzer quick_session
prompts` z pevných úhlů A/B/C. Jádro je směruje, ale první zadání píše
nástroj (návrh 2). S ADR-0026 se to nevylučuje: tam jde o Rozhodnutí,
které AI nesmí naklánět; tady o hodnocení výstupu proti předem danému
měřítku.

## 4. Bezpečnost a nehody

- Veracode, GenAI Code Security Report (28. 7. 2026) a podzimní
  aktualizace (29. 10. 2026). Průměrná úspěšnost v bezpečnostních testech
  56 % v červenci (55 % v první zprávě), 62 % v říjnu. Zranitelnost
  vnesla zhruba ve 44 %, resp. 38 % úloh. Nejslabší kategorie: XSS 15 %,
  resp. 18 %; vkládání do logů 12 %. Modely v testu nedostaly žádný
  bezpečnostní pokyn. Veracode prodává skenery a opravy kódu.
  *Přečteno: primární články; plná zpráva je za formulářem.*
- Securityscanner.dev, „State of Vibe-Coded Security Q2 2026“. Kritický
  nález mělo 7,1 % aplikací z Lovable (34 ze 476), 7,3 % z Bolt.host
  a 2,1 % z Replitu; 96 % kritických nálezů bylo vypnuté řízení přístupu
  k řádkům v databázi (Supabase RLS). Vzorek není náhodný a vydavatel
  prodává skener.
  *Přečteno: primární stránka.*
- AI Incident Database, incident 1152 (18. 7. 2025). Agent Replitu podle
  hlášení smazal produkční databázi během zmrazení kódu, přes opakované
  pokyny nic neměnit, a uvedl nepravdivé údaje o obnově. Škoda je
  vedená jako tvrzená, zdroj je jeden uživatel.
  *Přečteno: záznam v databázi.*
- Michels a kol., arXiv 2608.20446, přehled 123 zdrojů (nesystematický).
  Z průzkumu dodavatele, který přehled sám řadí k nejslabším důkazům:
  93 % organizací má formální review AI kódu, ale jen 56 % ho vždy
  vynucuje.
  *Přečteno: abstrakt a HTML, část přes strojové shrnutí.*

Tvrzení připisované Gartneru, že přístup „prompt-to-app“ u citizen
developerů zvýší do roku 2028 počet chyb o 2 500 %, jsme z Gartneru
neověřili (stránky nedostupné) a nepoužíváme ho.

**Pro metodu:** checkpoint Bezpečnost & právo už řeší klasifikaci dat,
egress, strop tokenů a prompt injection. Chybí dvě konkrétní věci:
řízení přístupu ověřené testem a produkční přístupy mimo dosah agenta
(návrhy 4 a 5).

## Návrhy pro metodu

Seřazeno podle přínosu. Všechno jsou hypotézy pro retro.

1. **Vstup „prototyp z byznysu“** (kandidát na ADR). Když zadavatel,
   PdM nebo designér přinese vlastní vibe-coded prototyp, metoda ho
   přijme jako **skicu k zadání**, ne jako variantu: ukáže se v Kickoffu,
   z jeho chování se sepíšou akceptační scénáře a pak se zahodí. Varianty
   se staví znovu v target repu s vývojářem u klávesnice. Důvody: (a)
   ne-vývojáři kód neověřují (Fawzy); (b) prototypy se lámou na napojení
   a nasazení (Li); (c) zákaz nefunguje, prototypy vznikají tak jako tak.
   Do „Kdy použít“ přibude čtvrtý typický spouštěč: „byznys už něco
   postavil a chce to do produkce“.
2. **Zadání variant píše jádro vlastními slovy.** Nástroj dál dodá
   kostru promptu (Constitution, kontroly, úhel), ale první odstavec
   „co má varianta dokázat“ napíše člověk, krátce. Při Iterate totéž.
   AI kontrola varianty má běžet jiným modelem než tím, který ji stavěl
   (Hu: hodnotitelé dávají přednost vlastním výstupům).
3. **Plán před stavbou.** Prvních 10 minut Buildu: pro každou variantu
   plán na jednu obrazovku (soubory, datový tok, co je mock), který
   jádro odsouhlasí, než AI začne psát. Odpovídá tomu, jak pracují
   zkušení vývojáři (Huang).
4. **Pravidlo dvou pokusů.** Když dvě nová zadání po sobě chybu
   neopraví, vývojář ji hledá ručně (čte kód, pouští debugger), místo
   třetího zadání. Opakované zadávání bez ladění je vzorec méně zkušených
   (Fawzy) a „házení kostkou“ (Chou).
5. **Bezpečnost: dvě konkrétní položky.**
   - Šablona `CONSTITUTION.md` dostane krátkou bezpečnostní část
     zaměřenou na nejslabší kategorie (kódování výstupu, zápis do logů,
     řízení přístupu). Modely v testech Veracode žádný pokyn neměly.
   - Checkpoint B&P: u dat s osobními údaji musí mezi akceptačními
     scénáři být aspoň jeden negativní na řízení přístupu („cizí uživatel
     záznam nepřečte“), ověřený testem, ne nastavením.
   - Checkpoint B&P a `worktree guard`: agent nemá produkční přístupy
     a oddělení vývoje od produkce vynucuje prostředí, ne pokyn agentovi
     (incident 1152).

## Co se potvrdilo a neměnit

- **Vývojář u klávesnice** a „bez vývojáře je to workshop s obrázky“.
- **Jádro 3–4 lidi a ~8 dní** (Adobe: 5 lidí, 8 pracovních dní).
- **Rozhodnutí nad běžícím kódem:** předávky mezi rolemi se nad funkčním
  prototypem zkracují (Li).
- **Jména u každého kroku:** vlastnictví jde za tím, kdo určil záměr,
  a formální review se bez jména nevynucuje (Li; Michels, slabý zdroj).

## Zdroje

| Zdroj | Přečteno |
|-------|----------|
| [Huang a kol., Professional Software Developers Don't Vibe, They Control](https://arxiv.org/abs/2512.14012) | abstrakt a HTML, část přes shrnutí |
| [Stack Overflow: Agents on a leash (27. 5. 2026)](https://stackoverflow.blog/2026/05/27/agents-on-a-leash-agentic-ai-remains-mostly-monitored-at-work) | primární článek |
| [Stack Overflow Developer Survey 2026](https://survey.stackoverflow.co/2026) | primární stránka |
| [Chou a kol., Building Software by Rolling the Dice](https://arxiv.org/abs/2512.22418) | abstrakt a HTML, část přes shrnutí |
| [Fawzy, Tahir, Blincoe: From Prompting to Verification](https://arxiv.org/abs/2605.24521) | abstrakt a HTML, část přes shrnutí |
| [Li a kol., Vibe Coding in Product Teams](https://arxiv.org/abs/2509.10652) | abstrakt a HTML, část přes shrnutí |
| [Pimenova a kol., Good Vibrations?](https://arxiv.org/abs/2509.12491) | abstrakt a HTML, část přes shrnutí |
| [Adobe Design: Unexpected lessons from an AI-assisted prototyping experiment](https://adobe.design/ideas/unexpected-lessons-from-an-ai-assisted-prototyping-experiment) | primární článek |
| [PA Consulting: Vibe coding](https://www.paconsulting.com/insights/vibe-coding-can-we-reimagine-software-delivery-with-ai-or-does-it-fall-short) | primární článek |
| [Hu a kol., Why Human Guidance Matters in Collaborative Vibe Coding](https://arxiv.org/abs/2602.10473) | abstrakt a HTML, část přes shrnutí |
| [Veracode: 2026 GenAI Code Security Report](https://www.veracode.com/blog/2026-genai-code-security-report-ai-risk) | primární článek |
| [Veracode: GenAI Code Security Fall 2026](https://www.veracode.com/blog/fall-2026-genai-code-security/) | primární článek |
| [Securityscanner.dev: State of Vibe-Coded Security Q2 2026](https://securityscanner.dev/reports/2026-q2) | primární stránka |
| [AI Incident Database, incident 1152](https://incidentdatabase.ai/cite/1152/) | záznam |
| [Michels a kol., Vibe Coding: A State-of-the-Art Review](https://arxiv.org/abs/2608.20446) | abstrakt a HTML, část přes shrnutí |
