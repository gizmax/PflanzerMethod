# Method Falsifiability — perspektiva 03: Skeptický VP Engineering / VP Product

> Velká korporace, 5000+ FTE, regulated industry (banka / telco / pojišťovna).
> 10 let, 6 transformation methodologies viděno zemřít. SAFe 4.0, Spotify model,
> OKR cascade napříč 14 tribes, Design Sprint as a service, FAST agile pilot
> v retail BU, Holacracy attempt 2019 (přežilo 5 měsíců). Tahle review není
> akademická. Je to **pattern matching**.

---

## Verdikt

Method Charter (v0.2.1, ADR-0007) je správný směr a intelektuálně poctivý
krok. **Ale v současné podobě je naivní.** Předpokládá hráče, instituce
a rozhodovací kulturu, které ve velkých korporacích neexistují. Konkrétně:
předpokládá CPO ochotného podepsat sunset metody, do které jeho předchůdce
investoval politický kapitál; Method Stewarda placeného z neexistujícího
rozpočtu; NPS sběr v survey-fatigue prostředí; baseline „6–9 měsíců",
kterou nikdo nedefinoval per project class; a předpokládá, že po 30 měsících
review pamatuje někdo, co Pflanzer vlastně byl. Charter v současné podobě
přežije ne víc než **18 měsíců** v reálné bance — protože všech 6 metodologií,
které jsem pohřbil, mělo lepší papírovou disciplínu a horší organizační
realitu. Pflanzer má šanci, pokud Charter explicitně rozpočtuje **byrokratické
náklady svého vlastního přežití**, ne jen výzkumné metriky. Aktuálně to nedělá.
Bez třech nepříjemných změn níže Pflanzer zhasne v Q3 svého druhého roku —
ne proto, že by nefungoval, ale proto, že **nikdo nebude mít pravomoc to
oficiálně potvrdit, takže se metoda zombifikuje** a stane se další položkou
v CoE katalogu, kterou si nikdo nevybírá.

---

## Útok 1 — „CPO/DoE jako Method Decider" je institucionálně neproveditelné

**Současný stav:** Method Charter, sekce Validační loop & sunset:
*„Pokud Method Decider potvrdí Kill → projekty v progress doběhnou,
nové se nestartují, role catalog se freeze-uje."* ADR-0007 definuje
Method Decidera jako *„CPO nebo Director of Engineering s mandátem od
exec committee."*

**Proč selže:** V bance s 5000+ FTE je CPO **politicky exponovaný hráč**
s mediánovou tenure 2.3 roku (zdroj: Russell Reynolds 2024, EU banking CPO
turnover study). Sunset metody = veřejné přiznání, že 3 čtvrtletí
investovaného rozpočtu (Method Steward, baseline collection, 3–10 pilotů,
T+6 reporting) byly mismanagement. Tři problémy najednou:

1. **Sunk cost fallacy organizační úrovně.** CPO, který Pflanzer schválil
   v Q1 Y1, ho v Q3 Y2 nezabije. Buď ho zabije jeho nástupce (a má motivaci,
   protože „uklízí po předchůdci" je default new-CPO play), nebo se metoda
   **degraduje na opt-in tool** v CoE katalogu, kterou si nikdo nevybírá,
   ale formálně žije.

2. **Reputational risk asymmetry.** Když CPO řekne „pokračujeme" a Pflanzer
   za rok zhasne organicky, ztratí 10 % reputation. Když CPO podepíše Kill
   a za rok bývalý Champion ukáže case study, kde to fungovalo, ztratí 60 %
   reputation. **Risk-adjusted return na sunset rozhodnutí je negativní.**
   Optimální VP strategie = nechat to zhasnout organicky, beze stopy v emailu.

3. **Mandát od exec committee.** Charter to chce. Exec committee v bance se
   schází 4× ročně a má agendu **30+ položek per session**. „Sunset Pflanzer
   methodology" je položka, kterou CEO 2× odloží (priority: M&A integration,
   regulatorní reporting, capital adequacy). Třetí pokus se sloučí s
   „transformation portfolio review" a tam Pflanzer zmizí mezi 18 dalšími
   iniciativami bez explicitního rozhodnutí. **Žádný papír, žádný kill log.**

**Realistický fix:**
- **Method Decider NESMÍ být CPO.** Musí to být **VP Engineering Effectiveness**
  (nebo ekvivalent: Head of Engineering Productivity, Head of Eng Excellence),
  který sedí 2 levely pod CTO a jehož **job description explicitně zahrnuje
  process portfolio management včetně sunsetů**. V bance to bývá osoba s
  tenurou 4–7 let, politicky méně exponovaná, s mandátem říct „tahle metoda
  patří do graveyardu".
- **Sunset rozhodnutí je default delegated, ne escalated.** Charter musí říct:
  *„Pokud po T+12 review Method Decider explicitně nepotvrdí Keep písemně,
  default = Sunset."* Tím se obrátí burden of proof. Současný Charter má
  opačnou logiku (default = pokračujeme, sunset vyžaduje aktivní podpis).
- **Kill rozhodnutí je v Charter Decision Rights matici, ne v exec committee
  agendě.** Method Decider má RACI = Accountable, exec committee = Informed
  (1× ročně summary). Bez tohohle se sunset nestane nikdy.

---

## Útok 2 — „Kill po 3 / 6 / 10 pilotech" je v korp realitě T+30 měsíců, a do té doby je metoda dávno zombie

**Současný stav:** Kill triggery v Charter tabulce — po 3 pilotech (>50 %
zhaslo), po 6 pilotech (<25 % zlepšení), po 10 pilotech (<3 self-sustaining BU).

**Proč selže:** Spočtěme realistický throughput pilotů ve velké bance.
Pflanzer cyklus = 6–9 týdnů aktivních + T+90 reinforcement = ~5 měsíců
end-to-end. Tři piloty **paralelně** = 5 měsíců. Tři piloty **sekvenčně
v jedné BU** = 15 měsíců. **Realistický mix:** 2 paralelní piloty v Q1,
další 2 v Q2 (po prvním retro), … přibližně 4–6 pilotů ročně v celé
organizaci, pokud se nebude závodit. **10 pilotů = T+24 až T+30 měsíců.**

V tom okně:

1. **3× se změní CPO.** Mediánová tenure CPO = 2.3 roku. Mediánová tenure
   VP Engineering = 2.7 roku. Z dnešního exec committee bude za 30 měsíců
   sedět ~40 % stejných lidí. **Nikdo z původního Decider gremiumu už nebude
   v roli.** Method Steward píše report do prázdné posluchárny.

2. **2× se přeorganizuje BU strukturu.** Co byla v Y1 „Retail Banking BU",
   je v Y2 sloučená do „Customer Solutions Tribe", a v Y3 rozdělená na
   „Daily Banking" a „Wealth". Pilot z roku 1 nemá majitele, jeho výsledky
   se nepřičítají k žádné aktuální BU. **Aggregace metrik přes 10 pilotů
   napříč 30 měsíci** vyžaduje organizační kontinuitu, kterou v korpu nemáš.

3. **Method Charter v0.2.1 je v T+18 měsíců dávno upraven.** Někdo někde
   tweakl thresholdy, někdo přidal výjimky pro „audit-grade" projekty,
   někdo to slil s SAFe IP iteration. Po 30 měsících žádný „Pflanzer v0.2.1"
   neexistuje. Existuje *„Pflanzer-inspired session model adapted to our
   context"*, což je code-name pro **defanged methodology** (viz Útok 6
   methodology drift trap).

4. **„Self-sustaining BU" definici nikdo nemá.** Charter ji zmiňuje
   v ADR-0007 (*„3+ self-sustaining BU, žádný organic Champion pipeline"*).
   Co je *self-sustaining*? BU, která dělá Pflanzer pilot bez asistence
   Method Stewarda? BU, která má Champion-of-Champions interně? BU,
   která má v rozpočtu Pflanzer line item? Bez operativní definice je to
   subjective call Method Stewarda — a Method Steward je v T+30 měsíců
   už třetí v pořadí (viz Útok 3).

**Realistický fix:**
- **Sklouznout kill triggery na T+6 mo / T+12 mo / T+18 mo absolute time**,
  ne per N pilotů. Čas je hard constraint, počet pilotů ne. Pokud za 6 měsíců
  proběhly jen 2 piloty místo plánovaných 3, **to samo o sobě je signal**
  (nezájem, low velocity, organizational friction) a Charter to musí
  interpretovat jako leading indicator, ne čekat na třetí pilot.
- **Quarterly Method Steward readout** (ne T+6 a T+12 jen), 1-pager do
  Process Portfolio Review meetingu (existuje v každé velké bance pod jiným
  jménem). Tím se kontinuita zajistí přes change of CPO — readout pamatuje
  papír, ne osoby.
- **„Self-sustaining BU" operacionalizovat:** *BU má Champion s tenurou ≥6 mo,
  spustila ≥2 piloty bez Method Steward přítomnosti, alespoň 1 pilot vedený
  internal facilitator-in-training, post-pilot NPS ≥+20.* Bez tohohle je
  metric meaningless.

---

## Útok 3 — Method Steward 10 % FTE = neexistujicí rozpočet, role po 6 měsících mrtvá

**Současný stav:** ADR-0007 Důsledky / Negativní: *„Vyžaduje role Method
Stewarda (~10 % FTE) v organizaci."* Mitigace: *„Method Steward = může být
Engineering Manager se zájmem o process improvement (žádná nová headcount)."*

**Proč selže:** Tohle je **nejnaivnější věta v celém Charteru**. Pojďme to
rozebrat z perspektivy někoho, kdo viděl 6 takových rolí umřít.

1. **„10 % FTE EM se zájmem o process improvement"** = v reálu *„EM
   s normální saturací 110 % capacity dostane sidekick odpovědnost na
   process work, který má prioritu HIGH dokud nepadne sprint, pak je to
   první věc, která jde ven."* Spotify model coaches, SAFe RTE part-time
   pilot, Lean Kata coach — všechny tyhle role byly „part-time EM se
   zájmem". Žádná nepřežila 12 měsíců funkčně.

2. **Z jakého rozpočtu?** Charter to neřeší. V reálu jsou tři možnosti,
   všechny mají problém:
   - **PMO budget** — PMO neuvolní headcount na něco, co konkuruje s PMO
     governance (a Pflanzer parciálně konkuruje, protože nahrazuje
     PMO-driven handoff sequence).
   - **CoE / Engineering Excellence budget** — tady to dává smysl, ale CoE
     budget je v bance typicky 0.5–1 % engineering OPEX, a v rámci toho
     soutěží Pflanzer s 15 jinými process iniciativami (Internal Developer
     Platform, DORA metrics dashboard, AI coding assistant rollout, …).
     Pflanzer dostane 0.2 FTE, ne 1 FTE Method Stewarda.
   - **BU operational budget** — žádný BU nezaplatí cross-BU process role.

3. **Žádná nová headcount = role je v JD jako P3 priorita.** *„Method
   Steward odpovědnosti přidány do existujícího role chart bez navýšení
   compensation."* První ranní stand-up, kdy EM má volit mezi Pflanzer
   T+6 reportem a outage post-mortemem, vyhraje outage. Vždycky. Po 6
   měsících je T+6 report 3 měsíce zpožděný a po 9 měsících se nikdo
   neptá.

4. **„Champion-of-Champions" v malé organizaci** (ADR-0007) je elegant idea
   pro startup, ne pro 5000 FTE banku. V bance jsou Champions per BU, ale
   *Champion-of-Champions* role je nová a nemá svého shepherd-a.

**Realistický fix:**
- **Method Steward je dedikovaný 0.5–1.0 FTE role v Engineering Excellence
  (nebo equivalent CoE) s explicit hiring profilem.** Senior PM nebo
  Principal Engineer s 5+ let v process improvement, ne EM se sidekick
  odpovědností.
- **Charter musí mít „Method Steward funding section"** s konkrétními čísly:
  *„Steward = 0.5 FTE Senior PM (band M3/M4), annual fully-loaded cost
  €120k–€180k, funded from Engineering Excellence OPEX, line item
  'Process Portfolio Stewardship', sign-off VP Engineering Effectiveness."*
  Bez tohohle čísla v Charteru se diskuse nikdy nedostane do budget cycle.
- **Quarterly readout do Process Portfolio Review** (ne CoP / Confluence) —
  to vytváří institucionální prostor pro role survival, protože Steward
  má co prezentovat 4× ročně do governance body, který má rozpočtovou pravomoc.
- **Charter musí mít „kill signal" pro Steward role samotnou:** *„Pokud
  Steward role je neobsazená > 90 dní, Method Charter automatically enters
  sunset mode."* Tím se vyřeší zombie state, kdy metoda formálně žije, ale
  role je mrtvá.

---

## Útok 4 — „Cross-functional NPS ≥ +20" je nezměřitelný v survey-fatigue prostředí

**Současný stav:** Charter tabulka, Stakeholder NPS ≥ +20, vlastník
Champion #17, měřeno *„post-pilot survey"*.

**Proč selže:** Pojďme to rozebrat operativně.

1. **Kdo to sbírá?** Champion #17 z BU. Champion není trénovaný UX researcher;
   nemá svolení rozesílat survey napříč 6–10 odděleními (compliance, security,
   legal, vývoj, produkt, design). V bance survey s 7+ recipients napříč BU
   typicky vyžaduje **People Analytics / HR sign-off** (kvůli engagement
   survey overlap a kvůli GDPR survey response retention rules). To je další
   2–3 týdny pre-flight, který Charter neuvádí.

2. **Do jakého survey nástroje?** Pokud korporace má Qualtrics / Glint /
   Workday Peakon (běžné v EU bankách), Champion **nemá admin access**
   a People Analytics nepustí survey, který neprošel jejich review (kvůli
   pulse survey schedule clash — banka má engagement survey 2× ročně a
   pulse měsíčně, další survey = response fatigue).

3. **Pulse survey fatigue = response rate <30 %.** Při 7 lidech v pilotu
   to znamená 2 odpovědi. NPS z N=2 je statistical noise. Charter
   neuvádí minimum N pro validitu — bez toho lze NPS *„změřit"* z 1
   odpovědi a vykázat +100 nebo -100.

4. **Response bias:** Kdo vyplní survey = enthusiast (positive bias) nebo
   resentful (negative bias). Default → enthusiast bias, protože resentful
   loga doceluje passive aggressive *„nevyplnit"*. Reportovaný NPS bude
   systematically inflated o 15–25 bodů.

5. **„Cross-functional NPS"** — co to znamená? *Jak byste doporučili
   Pflanzer kolegovi?* — to je NPS metody. *Jak byste doporučili tento pilot
   kolegovi?* — to je NPS projektu. To jsou dvě věci a Charter to nerozlišuje.
   Pilot může být úspěch a metoda špatně-vnímaná zároveň (typical SAFe
   pattern: *„dodali jsme PI, ale process je peklo"*).

**Realistický fix:**
- **NPS sbírá Method Steward, ne Champion.** Steward má institucionální
  legitimitu pro cross-BU survey.
- **Survey jde přes existující People Analytics pulse infrastructure**
  (mounted do quarterly engagement pulse, ne stand-alone). Tím se vyhne
  klesající response rate.
- **Otázka je rozdělena:** (a) *„Pflanzer process NPS — jak byste doporučil
  metodu kolegovi v jiném pilotu?"*, (b) *„Pilot outcome NPS — jak byste
  doporučil výsledek do production?"* Threshold ≥ +20 platí pro (a), ne (b).
- **Minimum N = 5 respondentů per pilot, jinak metric flagged ⟨insufficient⟩.**
  Bez tohohle se NPS reportuje z 1–2 odpovědí a je to bullshit metric.
- **Aggregate across pilots, not per-pilot reporting.** Per-pilot NPS s N=5
  má margin of error ±20. Aggregate přes 6+ pilotů (N>=30) je statisticky
  validní. Charter aktuálně reportuje per-pilot, což je noise.

---

## Útok 5 — „Sériový handoff baseline 6–9 měsíců" je incomparable, protože pro které projekty?

**Současný stav:** Charter, XYZ hypotéza: *„zkrátí čas od 'nápad' k 'handoff
package' o ≥ 50 % (z baseline ~6–9 měsíců sériového handoffu na ~6–9 týdnů)."*
Comparison baseline sekce: *„Baseline metric collection 3 měsíce před prvním
pilotem (light: 5–10 reprezentativních projektů, manuální estimace nebo
project tracker analysis)."*

**Proč selže:** Tahle XYZ hypotéza je **nepoctivá srovnávací matematika**
a v audit committee ji rozbiju do 4 minut.

1. **„6–9 měsíců sériového handoffu" — pro JAKÝ project?** V mé bance jsou
   minimálně 4 kategorie:
   - **Single-team bugfix / patch** (current state: 2–4 týdny, Pflanzer
     nepřichází v úvahu — anti-pattern 4).
   - **Cross-team feature, jeden BU, žádný DPIA** (current state: 4–8 týdnů
     handoff, Pflanzer cyklus 6–9 týdnů = **stejný čas nebo pomalejší**).
   - **Cross-BU feature, DPIA required** (current state: 4–7 měsíců včetně
     pre-discovery a security review, Pflanzer cyklus 6–9 týdnů + nezahrnuje
     full security review pokud throw-away = **comparable, ale Pflanzer je
     incomplete srovnání**).
   - **Strategic platform feature, multi-team, regulatorní change** (current
     state: 9–18 měsíců, Pflanzer claim 6–9 týdnů = **nesrovnatelné, protože
     Pflanzer pokrývá jen handoff package, ne celý SDLC**).

   Charter neuvádí, do které kategorie patří baseline „6–9 měsíců". Defaultně
   čtenář předpokládá kategorii 4, ale Pflanzer doručuje něco bližšího
   kategorii 2. **To je apples-to-oranges srovnání.**

2. **„Time-to-handoff" vs „time-to-production"** — Charter měří handoff
   package, ne deploy. Sériový handoff také pokrývá jen do handoffu, takže
   v tom je férové. Ale **v reálu management chce vidět time-to-production**,
   a tam Pflanzer nepokrývá zbytek SDLC. Audit committee otázka: *„Zkrátili
   jsme dobu k handoffu, ale zkrátili jsme dobu k production?"* Pflanzer
   odpovídá *„to není naše metoda"*. Audit committee si poznamenává.

3. **3-měsíční baseline collection s 5–10 projekty** = **N=5–10 retrospektivně
   odhadnutých dat**, kde každý odhad má margin of error ±30 % (project
   tracker data v bance jsou typicky špinavá, milestones se posouvají,
   re-baselining se nedokumentuje). Comparison Pflanzer-pilot-result vs
   noisy baseline = **statistical hand-waving**.

4. **Survivor bias v baseline.** *„5–10 reprezentativních projektů"* — kdo
   vybírá? Champion. Champion vybírá projekty, které **měly cross-functional
   alignment problem**, protože tam je Pflanzer fit. Ale to jsou
   **systematicky pomalejší projekty** než průměr (alignment problém ⇒
   delay). Baseline je tedy inflated, srovnání je zkreslené ve prospěch
   Pflanzeru. To audit committee chytí na druhý pohled.

**Realistický fix:**
- **Project class taxonomy v Charteru.** Baseline a target time per class:
  *„Class B (cross-team, jeden BU, žádný DPIA): baseline median 6 týdnů,
  target ≤4 týdny."* *„Class C (cross-BU, DPIA): baseline median 4 měsíce,
  target ≤6 týdnů + parallel DPIA track."* Pflanzer cíluje na class B+C
  explicitly, ne abstract „6–9 měsíců".
- **Baseline = N≥20 projektů per class** s data extraction z Jira / ADO
  pomocí scriptu (ne manuální estimace), audit trail v Confluence.
  Light baseline (N=5) je signal *„nepřipraveni měřit"*.
- **Selection criteria pro baseline projekty je publikované a externí**
  — ne Champion-selected. Default = *„všechny projekty class B/C
  closed-out za posledních 18 mo, vyloučeny pouze ty s incomplete data
  (>20 % missing fields)."*
- **Reportovat handoff-to-prod follow-up metric** (ne success criterion,
  ale informational): *„Pflanzer pilot 6 týdnů to handoff + 12 týdnů to
  prod = 18 týdnů total. Sériový handoff baseline class C = 16 týdnů to
  handoff + 8 týdnů to prod = 24 týdnů total."* Tím se argument o **end-to-end
  speed** dá obhájit, ne jen handoff segment.

---

## Útok 6 — Methodology drift / fork trap: po 18 měsících už to není Pflanzer

**Současný stav:** ADR-0007 Důsledky / Pozitivní: *„Eliminuje methodology drift
— bez method-level review se workshop metody stávají self-perpetuating bez
dohledu."* Charter validační loop = T+6 / T+12 review.

**Proč selže:** Method-level review **nezabraňuje driftu**; v lepším případě
ho zpomaluje. Pojďme se podívat, jak drift reálně vypadá.

1. **„Adaptace na náš kontext"** — bance s 2 pilots za rohem řekne facilitátor
   *„v naší situaci dáváme silent voting přes Mural místo papíru, protože
   všichni jsou na Mural"*. Drobnost. Třetí pilot už nemá silent voting
   vůbec, protože *„Mural session ate the timer, dáme jen verbal voting,
   ušetříme 20 minut"*. **Anti-HiPPO mechanism je tichý, nikdo to
   nezdokumentoval, Method Steward o tom neví.**

2. **Fork v BU.** Retail BU dělá *„Pflanzer Lite"* — jednu session místo dvou,
   *„naše projekty jsou menší"*. Wealth BU dělá *„Pflanzer Plus"* — tři
   sessions, *„naše projekty mají vyšší regulatorní zátěž"*. Po 12 měsících
   jsou tři varianty Pflanzeru a žádná z nich není v0.2.1.

3. **Charter v0.2.1 vs implementation v0.3.x.** Method Steward updatuje
   Charter v0.3, ale piloty v běhu používají v0.2.1 návyky. Confluence
   diverges od reality. Po 18 měsících je Charter document, který nikdo
   nečte.

4. **„Pflanzer-inspired"** = code-name pro defanged methodology. Tým
   konferenci v Q4 prezentuje *„our adapted approach inspired by Pflanzer"*,
   audit committee to zaznamenává jako *„Pflanzer success"*, ale fakticky
   to už není falsifiable hypothesis — je to vágní inspirace.

5. **Spotify model precedent.** Kniberg + Ivarsson 2012 → 2024 review:
   *„Spotify nikdy nepoužíval Spotify model, jak ho banky implementovaly."*
   Drift od originálu je **měřitelně 5–7 let**, ale ireverzibilní. Pflanzer
   má stejnou trajektorii bez fork-detection mechanismu.

**Realistický fix:**
- **„Pflanzer compliance score" per pilot** — Method Steward kontroluje
  ex-post checklist 12 must-have prvků (silent voting použito, throw-away
  default v Charteru, anti-HiPPO Decider vote last, pre-flight triage
  proběhly, atd.). Score < 9/12 = **pilot není Pflanzer pilot**, ale
  *„Pflanzer-inspired"*, a **nezapočítává se do success metrics**.
  Bez tohohle audit-trailu je drift nedetekovatelný.
- **Charter version pinning.** Každý pilot eviduje *„Pflanzer Charter
  version pinned: v0.2.1, deviations: [seznam]"*. Method-level review
  agreguje deviations a rozhoduje, zda jde o (a) bug fix v0.3, (b)
  legitimní variant fork, (c) drift to be reverted.
- **Fork governance.** ADR-0008 (nový): *„Variant fork povolen pouze
  s Method Decider sign-off, dokumentovaný v dedicated ADR, s vlastní
  XYZ hypotézou."* Bez ADR fork není fork, je to silent drift.
- **Public Pflanzer adherence dashboard** — Method Steward publikuje
  per-pilot compliance score. Drift se stane veřejně viditelný, čímž
  se vytváří social pressure proti tichému forku.

---

## Útok 7 — „T+6 / T+12 method-level review" v bance znamená „nikdy" bez tahových mechanismů

**Současný stav:** Charter Reinforcement track: *„T+6 měsíců method-level
agregace, Method Steward publikuje report do CoP / Confluence."* *„T+12 měsíců
review — keep / iterate / sunset, owner Method Decider."*

**Proč selže:** *„Publikuje do Confluence"* je v bance ekvivalent *„hodí to
do studny"*. Confluence read rates pro process documentation v EU bankách:
**3–8 % targeted audience views per quarter**. T+6 report přečtou 3 lidé —
Method Steward, autor (asi tentýž), a jeden ambitious junior PM, který
hledá topic na vnitřní prezentaci.

Pull mechanism (kdo chce, najde) nestačí pro institucionální rozhodnutí.
Bez **push mechanism** se T+12 review buď neuskuteční, nebo se konsoliduje
do existujícího process portfolio review v 10-min slotu, kde Method
Decider má 3 minuty na prezentaci a 2 minuty na otázky → default outcome
= *„keep + iterate"*, nikdy *„sunset"*.

**Realistický fix:**
- **T+6 report = mandatory agenda item v Process Portfolio Review meeting**
  (nebo equivalent governance body, který má rozpočtovou pravomoc). Ne
  Confluence. Method Steward má 15-min slot s pre-circulated 2-pager.
- **T+12 review je formal Decision meeting**, ne agenda item. Charter musí
  specifikovat: *„T+12 review = 60-min dedicated meeting, attendees = Method
  Decider + 3 BU Champions + Method Steward + 1 sceptical external observer
  (peer org Engineering Excellence lead). Pre-read = 5-pager. Decision
  log signed v meetingu."*
- **External observer / red team v T+12.** Bez externí skepse je review
  echo chamber. Default = Engineering Excellence lead z jiné dceřinné
  společnosti / peer bank (consortium model). Bez externí kritiky review
  vždy doporučí *„keep + iterate"*.

---

## Útok 8 — Charter mlčí o **rozpočtu na baseline collection** a tím odsouvá první pilot o 6 měsíců

**Současný stav:** *„Baseline metric collection 3 měsíce před prvním pilotem
(light: 5–10 reprezentativních projektů)."*

**Proč selže:** *„Manuální estimace nebo project tracker analysis"* = kdo
to dělá? Method Steward, který ještě neexistuje (přiřazení po 1. pilotu,
viz Charter sekce Status). Někdo musí udělat baseline **před** prvním
pilotem, ale Steward je definovaný **po** prvním pilotu. **Bootstrap
paradox.**

V reálu:
1. Champion v Q1 navrhne Pflanzer pilot.
2. CoE řekne: *„OK, ale potřebujeme baseline. Najmi si konzultanta nebo
   to udělej sám."*
3. Champion nemá 80 hodin volné kapacity na project tracker analysis.
4. Konzultant stojí €15k–€30k a Champion nemá CAPEX schválený.
5. Q1 končí, Q2 začíná, pilot se posouvá. Q3 — Champion mění roli.
   **První pilot se nestihne.**

Tohle jsem viděl s OKR rollout v 4 bankách. Pre-launch measurement
infrastructure trvala 6–9 měsíců, během té doby skončili 3 z 5 sponzorů.

**Realistický fix:**
- **„Baseline collection bootstrap"** v Charteru jako pre-condition: *„Method
  Steward role obsazena PŘED první pilot kick-off. Steward odpracovává
  3 měsíce baseline + Charter operationalization PŘED prvním pilotem."*
- **Konkrétní budget line:** *„Bootstrap budget = €40k (3 měsíce 0.5 FTE
  Steward + 2× konzultantský workshop pro project class taxonomy + Jira
  data extraction tooling)."*
- **Bootstrap kill criterion:** *„Pokud bootstrap netrvá max 4 měsíce
  end-to-end, Charter neaktivováno, sponzor revidovat scope."* Bez kill
  criterion na bootstrap se to zpožďuje donekonečna.

---

## Methodology graveyard checklist

Šest „transformation methodologies", které jsem viděl umřít, mělo
**deset společných patternů**. Pflanzer Method Charter dnes naplňuje
**7 z 10**. Zde checklist; každý bod je hřebík do rakve, který Charter
musí explicitně vytáhnout.

| # | Pattern | Příklad metody, která zemřela | Pflanzer (v0.2.1) status |
|---|---------|-------------------------------|--------------------------|
| 1 | Decider role je politicky exponovaná osoba s tenurou < 3 roky | SAFe RTE escalation to CIO, Spotify chapter lead model | **NAPLNĚN** — CPO/DoE je political role. Útok 1. |
| 2 | Sunset rozhodnutí vyžaduje aktivní podpis, default = pokračovat | OKR cascade, Holacracy attempt | **NAPLNĚN** — Charter má aktivní Kill, default keep. Útok 1. |
| 3 | Method Steward / coach role je part-time nebo „bez nové headcount" | Spotify Agile Coaches (po 2018), SAFe RTE part-time | **NAPLNĚN** — *„EM se zájmem o process improvement, žádná nová headcount"*. Útok 3. |
| 4 | Metriky závisí na voluntary survey response | Engagement-driven OKR, post-Sprint NPS | **NAPLNĚN** — Stakeholder NPS bez infrastruktury. Útok 4. |
| 5 | Baseline definovaný retrospektivně, malý N, Champion-selected | Většina transformace ROI cases | **NAPLNĚN** — N=5–10, manuální estimace. Útok 5 + Útok 8. |
| 6 | Žádný mechanism proti drift / fork; *„adapted to our context"* je vítaný | Spotify model, Lean Startup as-applied, holacracy variants | **ČÁSTEČNĚ NAPLNĚN** — review existuje, ale compliance score chybí. Útok 6. |
| 7 | Review do Confluence / wiki, ne governance body s rozpočtovou pravomocí | OKR retro, SAFe Inspect & Adapt aggregation | **NAPLNĚN** — *„publikuje do CoP / Confluence"*. Útok 7. |
| 8 | Bootstrap paradox: pre-launch infrastructure vyžaduje role, která vznikne až po launch | OKR coach hiring after first OKR cycle, SAFe LACE | **NAPLNĚN** — Steward přiřazen po 1. pilotu. Útok 8. |
| 9 | Žádný externí red team / skeptical observer v review | SAFe assessment by SAI itself, Spotify *„we did it because we did it"* | **NAPLNĚN** — review je internal-only. Útok 7. |
| 10 | Žádný explicit financial line item v rozpočtu organizace | Holacracy training budget, *„change initiative"* slush funds | **NAPLNĚN** — Charter nemá CFO-readable cost section. Útok 3 + Útok 8. |

**Skóre: Pflanzer naplňuje 9 z 10 patternů, 1 částečně. Pravděpodobnost
přežití 24 měsíců bez nepříjemných změn níže = 10–15 %.**

---

## Tři nepříjemné změny, které Method Charter musí přijmout

Tyhle jsou **non-negotiable**. Ne *„nice to have"*. Bez nich Pflanzer
neopustí pilotní fázi v žádné velké korporaci. Každá je nepříjemná, protože
přidává byrokratický overhead, který Pflanzer hodnotová proposice
*„rychlost a alignment"* nerada slyší. Ale to je point: **methodology
survival cost je byrokratický cost**, ne metodický cost.

### Změna #1 — Method Decider sedí 2 levely pod CTO, ne na CPO úrovni; sunset je default po T+18 mo bez aktivního Keep

**Současný Charter:** *„Method Decider = CPO nebo Director of Engineering
s mandátem od exec committee. Sunset vyžaduje Method Decider podpis."*

**Nový Charter (zapsat doslova):**

```
Method Decider = VP Engineering Effectiveness (nebo equivalent: Head of
Engineering Excellence, Head of Process Portfolio), pozice 2 úrovně pod
CTO/CIO. Tenure profile: minimum 3 roky v roli předpokládaná, hire
externí kandidát s 7+ let v eng productivity je preferován.

Job description Method Decidera explicitly obsahuje:
- Process portfolio management včetně sunset rozhodnutí.
- Quarterly accountability do Process Portfolio Review meeting.
- RACI = Accountable for Pflanzer keep/iterate/sunset decisions.

Sunset triggering rule:
T+18 měsíců od první pilot kick-off, pokud Method Decider explicitly
nepotvrdí Keep písemně (signed memo do Process Portfolio Review minutes),
default state = Sunset. Sunset = projekty v progress doběhnou, Charter
freeze, role catalog archived to read-only Confluence space.

Re-activation post-sunset vyžaduje nový ADR s explicit re-baselining
+ exec committee endorsement (= nemůže se to stát latentně).
```

**Proč nepříjemné:** Pflanzer autoři budou chtít CPO jako Decider kvůli
*„executive sponsorship signal"*. To je přesně to, co metodu zabije.
Méně senior, méně exposed, dlouho-tenured Decider má **vyšší pravděpodobnost
sunset rozhodnutí** = **vyšší pravděpodobnost vůbec přežít review cycle**,
protože default flip (active Keep, ne active Kill) eliminuje sunk-cost
freeze.

### Změna #2 — Method Steward je dedikovaný 0.7–1.0 FTE Senior PM s €150k–€200k annual budget, financován z Engineering Excellence CoE; quarterly readout do Process Portfolio Review

**Současný Charter:** *„~10 % FTE, může být EM se zájmem o process
improvement, žádná nová headcount."*

**Nový Charter:**

```
Method Steward = dedikovaný 0.7–1.0 FTE Senior Product Manager nebo
Principal Engineer s ≥5 lety v process improvement, hired do Engineering
Excellence CoE (nebo equivalent).

Annual fully-loaded cost: €150k–€200k (band M3/M4 EU base).
Budget line: Engineering Excellence OPEX → „Process Portfolio
Stewardship → Pflanzer Method".
Sign-off pro budget: VP Engineering Effectiveness (= Method Decider).

Method Steward operating model:
- 50 % capacity: Pflanzer pilot facilitation + Champion coaching.
- 30 % capacity: Metric aggregation, T+6 / T+12 / quarterly readouts.
- 10 % capacity: Method Charter maintenance + ADR shepherding.
- 10 % capacity: Cross-org learning (peer conferences, external red team).

Quarterly readout = mandatory 15-min agenda item v Process Portfolio
Review meeting (existující governance body s rozpočtovou pravomocí,
NE Confluence / CoP). Pre-read 2-pager 5 working days před meetingem.

Steward role survival rule:
Pokud Steward role je neobsazená > 90 kalendářních dní (z jakéhokoliv
důvodu: turnover, hiring freeze, re-org), Method Charter automatically
enters sunset mode po dobu trvání vacancy. Nové piloty se nestartují.
Re-activation = nový hire + Method Decider memo „Charter reactivated".
```

**Proč nepříjemné:** Tahle změna říká *„Pflanzer stojí €150k+ ročně jen
za role stewarda, plus pilots cost"*. Sponzorovi se to nebude líbit. Ale
**bez explicit cost line v CFO-readable formátu Charter nikdy nepasuje do
budget cycle a Steward role se nikdy nehiruje**. Současná formulace
*„10 % FTE EM bez headcount"* je *budget vapor* — vypadá levně, fakticky
neexistuje.

### Změna #3 — „Pflanzer compliance score" per pilot a externí red team v T+12 review; bez nich pilot není Pflanzer pilot

**Současný Charter:** Žádný compliance check; review je internal-only.

**Nový Charter:**

```
Pflanzer Compliance Score (per pilot, checked by Method Steward ex-post):

12 must-have prvků:
1. Pre-flight Discovery Readiness Gate sign-off existuje (datovaný).
2. Pre-flight Security & Data triage sign-off existuje (datovaný).
3. Pre-flight Platform Triage sign-off existuje (datovaný).
4. Charter (ADR-0004 template) podepsaný před Session 1.
5. Session 1 attendance ≥ 70 % Required roles podle role catalog.
6. Silent voting použit minimálně 1× v Session 1.
7. Decider hlasoval poslední (anti-HiPPO) v Session 2 — decision log
   evidence.
8. Hierarchie závaznosti (Critical/Yellow/Score) použita pro feedback
   v mezi-session.
9. Throw-away default flag v Charteru (nebo explicit evolve sign-off
   per ADR-0005).
10. Handoff package obsahuje všech 6 required artefaktů.
11. T+30 readout proběhl (post-pilot retro).
12. AI prompt audit log archived (per ADR-0008 retention spec).

Score ≥ 10/12 = Pflanzer pilot, započítává se do method-level metrics.
Score 7–9/12 = „Pflanzer-inspired", reportováno separátně, NE započítává
se do XYZ hypotézy validace.
Score < 7/12 = pilot disqualified, deviations logged jako fork candidate.

T+12 Method-level Review formát:

60-min dedicated meeting (NE agenda item v jiném meetingu).
Attendees:
- Method Decider (Accountable, signs off).
- Method Steward (presents).
- 3 BU Champions (peer perspective).
- 1 External Red Team observer = Engineering Excellence lead z peer
  organization (consortium model: 3 banky se vzájemně red-teamují
  process portfolios, quarterly rotation).

Pre-read 5-pager (Steward authors, External observer pre-reviews
1 week ahead with right to request additional data).

Decision options: Keep (with thresholds renewed) / Iterate (with
specific changes documented) / Sunset (with wind-down plan).

Default ve absence explicit decision = Sunset (= burden of proof
on continuation, ne sunset).
```

**Proč nepříjemné:** Compliance score je byrokratický overhead, který
*„rychlost a alignment"* hodnotová proposice odmítá. External red team
vyžaduje peer consortium, který v bance neexistuje a vyžaduje legal
agreements (NDA, data sharing). Default Sunset obrací organizační
inertia.

Ale **bez tohoto checkpoint sety Pflanzer driftí**, fork-uje se,
a po 24 měsících je *„Pflanzer-inspired adapted approach"* označen jako
úspěch metodologie, která už neexistuje. To je přesně Spotify pattern.

---

## Co bych jako VP potřeboval vidět v T+6 reportu

Ne pro Confluence read. Pro **15-min agenda slot v Process Portfolio
Review**, kde rozhoduji o Q-next budget pro Method Steward. Bez všech 8
položek default je *„iterate s rozpočtem -25 %"*, což je polite-cut, který
za další 6 měsíců znamená sunset.

1. **N pilots completed, breakdown per project class** (B / C / D).
   Bez project class taxonomy je celá metrika non-comparable. Pokud
   reportujete *„4 piloty proběhly"* bez class breakdown, **next question:
   'across which kind of projects'**. Bez odpovědi → meeting over.

2. **Compliance score distribution.** Histogram: kolik pilotů
   score 10–12, kolik 7–9, kolik <7. Pokud více než 30 % pilotů má
   score <10, **method není consistently practiced** a aggregate metrics
   jsou meaningless. To je první otázka, na kterou se ptám.

3. **Time-to-handoff median + p90 per class, vs baseline.** Ne průměr
   (outliers zkreslí). Median + p90, side-by-side s baseline class
   median + p90. Pokud baseline data nejsou class-segmented, **report
   nepřijatelný** — vraťte se s lepšími daty.

4. **Re-work % T+90 per pilot, vs baseline current state.** Tohle je
   guardrail metric a každý chce vidět, že to nevozí re-work do prod.
   Pokud chybí (T+90 ještě nenastoupil pro většinu pilotů), **report
   incomplete** — ale acceptable s explicit *„awaiting T+90 data, expected
   Q-next"*.

5. **NPS aggregated across pilots, N≥30, with response rate.** Per-pilot
   NPS je noise. Aggregate je signal. Response rate <50 % = response bias
   alert.

6. **Champion pipeline status.** Konkrétně: kolik BU má Champion, kolik
   těch Champions vedlo ≥1 pilot bez Steward přítomnosti, kolik
   Champion-of-Champions kandidátů existuje. Bez Champion organic growth
   metoda nepřežije Steward turnover.

7. **Method Steward time allocation actual vs target.** Pokud Steward
   říká *„60 % capacity Pflanzer"* a actual je 30 % (zbytek mu sežralo
   firefighting), Charter operating model je nereálný. Adjust nebo flag.

8. **External red team finding summary** (z peer-org observer). Minimum
   3 substantive critiques s response. Bez external skepse jsem skeptický,
   že review byla čestná.

**A jednu věc, kterou nechci v reportu vidět:** *„team enthusiasm high"*.
Enthusiasm je leading indicator pro Year 1 a zero predictive value pro
Year 3. Pokud v reportu vidím enthusiasm bez compliance score, beru to
jako warning sign, že Steward měří správnou věc.

---

## Závěr — co řeknu Pflanzer autorům do očí

Method Charter je intelektuálně poctivější než 5 ze 6 transformation
methodologies, které jsem za 10 let viděl. To **nestačí**, protože těch 5
také mělo papírové discipliny a zemřely v korp realitě. Pflanzer dnes
naplňuje 9 z 10 graveyard patternů, ne proto, že by autoři byli naivní,
ale proto, že **Charter byl psán z perspektivy methodology designerů,
ne z perspektivy organizational survival**.

Tři nepříjemné změny výše jsou hřebíkové. Pokud autoři řeknou *„to je
overhead, to ruší naši rychlost"*, řekl bych: ano. Methodology overhead
existuje proto, aby methodology survival nákladu **nestál víc než
methodology value**. Bez overhead methodology hodnotu ani nezjistíte,
protože do té doby zhasne.

Co bys ode mě dnes potřeboval slyšet, aby ses cítil líp: že Pflanzer
je dobrá metoda. Ano, je. Pro **jeden pilot v jedné BU s motivovaným
Championem a engaged sponzorem na 3 měsíce** je Pflanzer mezi top 20 %
metodologií, které znám. Pro **multi-BU rollout s 18-měsíčním validation
horizonem v 5000+ FTE bance** je Pflanzer ve své v0.2.1 formě **statisticky
mrtvý projekt**, který si toho zatím neuvědomil. Tři změny výše to mění,
ne na 80 % survival pravděpodobnost, ale na 40–50 %. To je nejlepší, co
**žádná methodology v korporátu nedostane**, a Pflanzer toho může
dosáhnout, pokud autoři přijmou, že **Method Charter musí rozpočtovat
nejen výzkumné metriky, ale i byrokratický cost vlastního přežití**.

Konec review.

---

*— Skeptický VP, který doufá, že se mýlí, ale 6× za 10 let se nemýlil.*
