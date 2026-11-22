# Zlepšení metody podle výzkumu z roku 2026

**Pflanzer Method | pflanzer.cz/method**

> Rešerše 2026-11-22. Navazuje na [`srovnani-metod-2026.md`](srovnani-metod-2026.md)
> (srovnání s jinými metodami); tady jde o empirické studie o vývoji s AI
> agenty a o to, co z nich plyne pro metodu v0.6.
> U každého zdroje je uvedeno, **co bylo přečteno**: primární text,
> jen abstrakt, nebo jen sekundární shrnutí. Čísla ze sekundárních zdrojů
> jsou označená a neměla by se citovat dál bez ověření.

## Shrnutí

- Úzké hrdlo se podle dat z roku 2026 přesunulo z psaní kódu na **review
  a merge**. Metoda dnes končí větou „PR otevře vlastník repa“ a review
  nechává na běžném procesu firmy. To je největší mezera.
- AI umí **naklonit rozhodnutí odborníků**, aniž si toho všimnou. Metoda
  staví na Rozhodnutí lidí, ale AI do něj dodává souhrn feedbacku a ve
  stupni Full první draft konvergence.
- **Porozumění kódu** s AI klesá a týmy ho vědomě odkládají. Metoda má
  diff walkthrough, ale neověřuje, že vítězi někdo rozumí.
- AI zvyšuje propustnost **i nestabilitu** dodávek a vlastní dojem ze
  zrychlení je nespolehlivý. Metoda měří dny a přežití kódu, neměří
  nestabilitu a nemá základnu ke srovnání.
- Z toho čtyři návrhy ADR (0025–0028, stav Proposed) a čtyři menší úpravy
  bez ADR.

Limit celé rešerše: jde o studie jiných týmů na jiných procesech. Žádná
netestuje Pflanzer Method. Návrhy jsou hypotézy, které má ověřit retro.

## 1. Review a merge jsou nové úzké hrdlo → ADR-0025

**Co říkají zdroje**

- Chen a Stratton (Harvard, data Jellyfish, 718 firem, zhruba 700 tisíc
  pracovníků, leden 2021 až březen 2026). Po nasazení agentů +30 % řádků
  kódu, +20 % commitů, +23 % PR; vyřešených issues jen +12 %. Průměrná
  doba review PR +49 %, komentářů na PR +53 %, podíl PR s požadavkem na
  změny se zdvojnásobil, podíl pracovníků dělajících review +14 %.
  *Přečteno: jen sekundárně (InfoQ, 22. 10. 2026). Primární PDF nečteno.*
- He a kol., arXiv 2607.01904 (jedna firma, 802 vývojářů, 196 212 PR,
  leden 2024 až duben 2026, mandát „2×“). Cíle firma dosáhla až v desátém
  měsíci; **zátěž na reviewera se zdvojnásobila**; automatické review do
  několika měsíců pokrylo víc PR než lidské. Autoři uvádějí, že propustnost
  je jen zástupná metrika a přiřazení nebylo náhodné.
  *Přečteno: abstrakt.*
- Duma a kol., arXiv 2605.02273 (dataset AIDev, EASE 2026). Většina PR od
  agentů nedostane žádné review; když ano, dělají ho převážně jiní agenti.
  Autoři varují, že metriky review pak neříkají nic o lidském dohledu.
  *Přečteno: abstrakt.*

**Co má metoda dnes:** v Asyncu technické role píšou keep / fix / kill nad
diffem; Ship končí otevřením PR; review je „stejná jako lidského kódu“,
approve dává člověk mimo autora ([`07`](../methodology/07-handoff-do-vyvoje.md)).
Retro měří dny od Go do merge jako jedno číslo.

**Návrh:** review vítěze je pojmenovaný a zabookovaný krok cesty, PR má
strop velikosti a retro měří čekání na review zvlášť. Detail v ADR-0025.

## 2. AI naklání úsudek odborníků → ADR-0026

**Co říkají zdroje**

- Herdağdelen, Joren, Tamkin (Anthropic, 27. 10. 2026), „How AI agents
  shape experts' judgment calls“. 50 analytiků se zkušeností s kauzální
  inferencí, jeden úkol, agent měl v systémovém promptu skrytý sklon
  určený hodem mincí. Analytici šli za sklonem agenta v **86 %** voleb
  (bez vlivu by to bylo asi 50 %); 77 % použilo argumenty agenta, někdy
  doslova; **jen 15 %** agenta uvedlo jako jejich zdroj. Když už měli
  vybráno a agent nesouhlasil, změnili volbu v 60 % případů (38 případů).
  Autoři navrhují, aby agent uvedl nejlepší argument pro každou možnost
  nebo se nejdřív zeptal na názor odborníka, a aby instituce vědomě
  určily, která rozhodnutí vyžadují vlastní úsudek člověka.
  Limity podle autorů: sklon byl záměrně zesílený; jeden úkol, jeden obor,
  jeden model.
  *Přečteno: primární stránka Anthropic. PDF studie nečteno.*

**Co má metoda dnes:** tiché hlasování a Decider poslední chrání před
vlivem nejvýše postaveného člověka, ne před vlivem AI. `pflanzer decide
prep` dává AI souhrn feedbacku „neutrálně, bez interpretace“ **před**
hlasováním; ve stupni Full AI píše první draft konvergence; AI smí
v omezené míře zastoupit chybějící role (ADR-0023).

**Návrh:** lidé hlasují dřív, než AI souhrn uvidí; AI píše argumenty pro
každou variantu i proti ní a nikdy nedoporučuje vítěze; decision log
zapisuje, co AI navrhla. Detail v ADR-0026.

## 3. Porozumění kódu klesá → ADR-0027

**Co říkají zdroje**

- Shen a Tamkin, arXiv 2601.20245, „How AI Impacts Skill Formation“.
  Randomizovaný pokus, 52 účastníků, hodinový úkol s neznámou knihovnou.
  Skupina s AI měla v testu porozumění o 4,15 bodu z 27 méně (autoři
  uvádějí 17 %, Cohenovo d = 0,74, p = 0,010) a nebyla významně rychlejší.
  Největší rozdíl byl v otázkách na ladění. Učení zachovaly způsoby práce,
  kde se účastník AI ptal na vysvětlení a koncepty, ne kde jí úkol předal.
  Limit: jeden úkol, chatové rozhraní, jedna hodina.
  *Přečteno: HTML studie, část přes strojové shrnutí.*
- Storey, arXiv 2603.22106. Tři dluhy: technický v kódu, **kognitivní**
  v lidech („eroze sdíleného porozumění v týmu“) a **intent dluh**
  v zapsaných znalostech („chybějící zapsané zdůvodnění, které vývojáři
  i AI agenti potřebují k bezpečné práci s kódem“).
  *Přečteno: abstrakt.*
- Lyu a kol., arXiv 2607.10856 (20 rozhovorů z 12 organizací, 80 platných
  dotazníků). Kód se přijímá dřív, než ho vývojáři umějí vysvětlit
  a upravit; týmy o budoucím závazku vědí a nesou ho dál, dokud kód
  funguje. Praxe „vrátit údržbu AI“ dluh podle autorů obchází, nesplácí.
  Limit: vlastní výpovědi, 15 z 20 respondentů z velkých technologických
  firem.
  *Přečteno: HTML studie, část přes strojové shrnutí.*

**Co má metoda dnes:** diff walkthrough tří vět (reuse / nové / mock)
od vývojářského páru, který variantu stavěl; decision log s rationale
Rozhodnutí. Nikdo neověřuje, že vítězi rozumí i někdo jiný, a zdůvodnění
návrhových rozhodnutí v kódu se nezapisuje.

**Návrh:** před Shipem vítěze vysvětlí vývojář, který ho nestavěl, a udělá
v něm jednu malou změnu bez AI; SHIP.md nese ke každému většímu návrhovému
rozhodnutí větu „proč“. Detail v ADR-0027.

## 4. Nestabilita a nespolehlivý dojem ze zrychlení → ADR-0028

**Co říkají zdroje**

- DORA. Vyšší adopce AI souvisí s vyšší propustností **i s vyšší
  nestabilitou** dodávek; jako protiopatření DORA uvádí práci v malých
  dávkách. Zjištění pochází ze zprávy DORA 2025; článek „Balancing AI
  tensions“ (10. 3. 2026) ho cituje.
  *Přečteno: článek DORA z března 2026. Zpráva o ROI z roku 2026 nečtena;
  tvrzení o „J-křivce“ a sedmi schopnostech jsou jen ze sekundárních
  shrnutí.*
- METR. Pokus z července 2025: 16 zkušených vývojářů, 246 úkolů; s AI
  trvaly úkoly o 19 % déle, vývojáři předem čekali zrychlení o 24 %
  a po pokusu stále věřili ve zrychlení o 20 %. Navazující sběr
  (24. 2. 2026; 57 vývojářů, 143 rep, přes 800 úkolů): odhad změny času
  u vracejících se vývojářů −18 % (interval −38 % až +9 %), u nových −4 %
  (−15 % až +9 %). METR to sám označuje za „jen velmi slabý důkaz“: 30 až
  50 % vývojářů některé úkoly neodevzdalo, protože je nechtěli dělat bez AI.
  *Přečteno: oba primární texty.*

**Co má metoda dnes:** retro měří % LOC vítěze beze změny (cíl ≥ 80 %),
dny od Go do merge (cíl ≤ 14) a readouty T+7 až T+90; T+7 „bugy
a hotfixy“ je ruční zápis. Chybí srovnání s tím, jak repo dodávalo před
pilotem, a cíl 80 % beze změny trestá i správné opravy.

**Návrh:** základna z target repa před pilotem, nestabilita jako tvrdá
metrika, přeformulovaný cíl přežití kódu. Detail v ADR-0028.

## Menší úpravy bez ADR

Jsou to návrhy do dokumentů a toolu; žádná nemění model účasti ani průběh.

1. **Úhly variant podle nejistoty zadání.** Dnes jsou pevné (A minimum,
   B vedený multi-step, C chytré defaulty) a sedí hlavně na UI. Wang
   a kol. (arXiv 2611.09798, *abstrakt a HTML*) uvádějí, že výběr nejlepšího
   z mnoha nezávislých pokusů se rychle nasytí a že výběr stojí na
   ověřovači, který umí každý pokus ohodnotit. Tři varianty, které se liší
   jen provedením, tedy přinesou málo. Návrh: v Kickoffu zapsat hlavní
   nejistotu zadání a dát každé variantě jinou hypotézu; pevné úhly A/B/C
   nechat jako výchozí pro zadání, kde je nejistota v UI.
2. **Akceptační scénáře před Buildem povinně.** Dnes jsou u walkthrough
   „volitelně“, přitom brána acceptance má v Ship skóre nejvyšší váhu
   (ADR-0024). Tufano a kol. (Google, arXiv 2608.17177, 90 produkčních
   chyb, *abstrakt a HTML*): agent, který nejdřív sepíše kontrakt kódu,
   našel o 9,8 procentního bodu víc chyb při zhruba 38 % tokenů navíc.
   Ariño de la Rubia a Pafka (arXiv 2609.33812, *abstrakt*): nejdřív
   vyřadit běhy, které porušily pravidla, pak vybrat nejlepší z několika.
   Návrh: 5–10 scénářů psaných lidmi v Kickoffu nebo na začátku Buildu,
   aspoň jeden negativní; všechny varianty se měří proti stejným.
3. **Bezpečnost agentů v `pflanzer doctor`.** Maloyan a Namiot (arXiv
   2601.17548, přehled 78 studií, *abstrakt*): úspěšnost adaptivních útoků
   proti současným obranám přes 85 %, většina obran zmírní méně než 50 %;
   autoři žádají obranu na úrovni architektury, ne filtry. Checkpoint
   B&P už řeší egress, strop tokenů a prompt injection. Návrh: `doctor`
   navíc vypíše soubory v target repu, které agent čte jako instrukce
   (pravidla, skills, README, konfigurace MCP), a SHIP.md uvede nové
   závislosti přidané ve vítězi k lidskému souhlasu. Seznam OWASP Top 10
   for Agentic Applications (9. 12. 2025) jsme z primárního textu
   nepřečetli, proto se na jeho jednotlivé body neodkazujeme.
4. **AI Act v `docs/governance/`.** Podle stránky Evropské komise
   (aktualizace 19. 10. 2026) vstoupil AI Omnibus v platnost 27. 7. 2026.
   Povinnosti pro samostatné high-risk systémy podle přílohy III platí od
   2. 12. 2027, pro systémy zabudované ve výrobcích podle přílohy I od
   2. 8. 2028. Návrh: opravit data v governance vrstvě a ověřit je proti
   textu v Úředním věstníku.

## Co se potvrdilo a neměnit

- **Constitution v target repu.** Denisov-Blanch a kol. (arXiv 2608.25241,
  *abstrakt*): mezi repozitáři stavěnými hlavně agenty měly ty **bez**
  commitnuté konfigurace AI zhruba dvojnásobný nárůst kognitivní
  složitosti (+53 % proti +27 %) a 1,7× nárůst varování statické analýzy.
  Autoři to označují za hypotézu, ne kauzální důkaz. Podporuje to
  `.pflanzer/CONSTITUTION.md` a `INTEGRATION_GUIDE.md`.
- **Malé dávky.** Odpovídá scope ~6–8 PD a jednomu vítězi.
- **Rozhodnutí u lidí.** Studie o naklánění úsudku je důvod Rozhodnutí
  posílit (ADR-0026), ne ho předat AI.

## Zdroje

| Zdroj | Přečteno |
|-------|----------|
| [InfoQ: Jellyfish / Harvard (Chen, Stratton)](https://infoq.com/news/2026/10/jellyfish-ai-productivity) | sekundární článek |
| [He a kol., AI Writes Faster Than Humans Can Review](https://arxiv.org/abs/2607.01904) | abstrakt |
| [Duma a kol., How Humans Review AI-Generated Pull Requests](https://arxiv.org/abs/2605.02273) | abstrakt |
| [Anthropic: How AI agents shape experts' judgment calls](https://www.anthropic.com/research) (27. 10. 2026) | primární stránka |
| [Shen, Tamkin: How AI Impacts Skill Formation](https://arxiv.org/abs/2601.20245) | HTML, část přes shrnutí |
| [Storey: From Technical Debt to Cognitive and Intent Debt](https://arxiv.org/abs/2603.22106) | abstrakt |
| [Lyu a kol., How Do Practitioners Build SE Agents?](https://arxiv.org/abs/2607.10856) | HTML, část přes shrnutí |
| [DORA: Balancing AI tensions](https://dora.dev/insights/balancing-ai-tensions/) | primární článek |
| [DORA: ROI of AI-assisted Software Development](https://dora.dev/ai/roi/report) | nečteno (jen úvodní stránka) |
| [METR: studie z července 2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) | primární text |
| [METR: změna designu pokusu, 24. 2. 2026](https://metr.org/blog/2026-02-24-uplift-update/) | primární text |
| [Wang a kol., Test-Time Compute Scales Better with Parallel Agent Teams](https://arxiv.org/abs/2611.09798) | abstrakt a HTML |
| [Ariño de la Rubia, Pafka: Identical Runs, Different Results](https://arxiv.org/abs/2609.33812) | abstrakt |
| [Tufano a kol., Grounding AI Agents in Contracts](https://arxiv.org/abs/2608.17177) | abstrakt a HTML |
| [Denisov-Blanch a kol., A Few Pages of Markdown](https://arxiv.org/abs/2608.25241) | abstrakt |
| [Maloyan, Namiot: Prompt Injection Attacks on Agentic Coding Assistants](https://arxiv.org/abs/2601.17548) | abstrakt |
| [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | jen úvodní stránka |
| [Evropská komise: regulatory framework for AI](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) | primární stránka (stav 19. 10. 2026) |
