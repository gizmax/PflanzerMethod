# Devil's Advocate Review — Pflanzerova metoda v0.2

## Kdo to říká

Senior Corporate Architect / Director of Engineering, 20+ let v EU/CEE
bankách a telcech, viděl jsem přijít a odejít přibližně 30 metodik —
RUP, Scrum, SAFe 1.0–6.0, Design Sprint, Lean UX, dual-track agile,
Spotify model (RIP), holacracy, OKR-driven everything, a teď
„AI-augmented alignment". Moje skepse není ideologická; je to
pattern recognition. Všechny ty metodiky odešly, protože **nepřežily
kontakt s rozpočtovým cyklem, audit committee a juniorním backfillem
v Q3**. Pflanzer si nárokuje, že je jiný, protože „kompiluje" osvědčené
prvky a přidává AI. To je přesně ten příběh, který jsem slyšel u SAFe
4.0, Design Sprint 2.0 a každém „canvas" frameworku za posledních 15 let.
Moje práce v týhle review je najít místa, kde se to v prvním pilotu
rozpadne — ne aby autor cítil bolest, ale aby ji cítil **teď, ne na
T+90 readoutu před CIO**.

## TLDR — Verdikt

Pflanzer je **dobře zdokumentovaná**, **regulatorně gramotná**, a
**nepředstírá, že je discovery framework**. To je víc, než dokáže
většina workshop metod. Zároveň má **fatal flaw v ekonomice** (8–10
person-days × 7 rolí × pre-flight × reinforcement = realisticky 12–18
person-days, ne 8) a v **kruhové závislosti na Championovi**
(metoda potřebuje Championa pro adopci, ale Champion vzniká až
z proběhlých pilotů — chicken-and-egg, který metoda nepojmenovává).
Pilot bych **doporučil jen na neauditovaný, single-BU, low-stakes
projekt** s explicit instrumentací nákladů a Champion-buddy modelem
od minuty 0; **nikoli na regulovaný projekt s DPIA** — tam metoda
slibuje víc, než reálně audit committee přesvědčí. Před pilotem
požaduji 5 oprav (sekce na konci).

## Útok 1 — „8–10 person-days per cyklus" je marketingový claim, ne realistický odhad

V `00-tldr.md` a `01-filozofie-a-kdy-pouzit.md` se opakuje budget
„8–10 person-days/cyklus", v ADR-0002 a `03-pre-session-priprava.md`
se počítá s 48–72 h pre-read pro tři triage tracks a Discovery
Readiness Gate. Pojďme spočítat. Pre-flight: PM 4 h Charter,
Security 4–6 h triage, Legal/DPO 4–8 h (DPIA lite není 30-min
cvičení), Platform 4 h sandbox, EM 2 h capacity sign-off, UX 4–6 h
Discovery, Champion 2 h. Session 1: 5–6 h × 7 lidí = **4.5–5.5
person-days**. Mezi-session: prototype deploy 1–2 dny FE/BE, scoring
1–2 h × 7 = 1–2 dny, AI syntéza 4 h, triage updates 4–6 h. Session 2:
3 h × 7 = 2.5–3 person-days. Handoff: 1–2 dny. Reinforcement
pomineme. Sečteno: **realisticky 12–18 person-days, peak 22 pro
audit-grade**, ne 8–10. Metoda buďto nepřiznává náklad (a EM workshop
zaveto na třetím pilotu), nebo počítá jen Session 1+2 (intelektuálně
nepoctivé). V `06-session-2.md` chybí „True Cost Worksheet". Bez ní
je každý ROI argument do exec committee fikce a první EM, který
udělá vlastní time tracking, metodu zabije.

## Útok 2 — Champion model je kruhová závislost, kterou metoda nepojmenovává

`01-filozofie-a-kdy-pouzit.md` v Kdy použít, bod 7: „Champion existuje.
Někdo v BU se chce stát facilitator-in-training a vést druhý+ cyklus;
bez toho je metoda one-shot demo, ne adopce." `07-handoff-do-vyvoje.md`
v sekci Champion model: „Bez čtyř readoutů adopce zhasne." ADR-0003
povyšuje #17 Champion na samostatnou roli. **Otázka, kterou nikdo
neadresuje:** kde se Champion vezme **pro první pilot**? Champion
je definován jako „byl v Session 1+2, podepsal Decision log" —
to znamená, že Champion může **existovat až po proběhlém pilotu**.
První pilot tedy z definice **nemá Championa**. Druhý pilot v té
samé BU může Championa převzít, ale druhý pilot v **jiné BU** je
zase první pilot v té BU — bez Championa. Metoda tedy škáluje
**lineárně per BU**, nikoli organicky. Banka s 8 BU potřebuje 8
„prvních pilotů" bez Championa, což je 8 případů, kdy metoda
„zhasne po druhém pilotu" podle vlastní definice. Edge case 10
(Champion odejde) tento problém **rozšiřuje, ale neřeší**: Champion
buddy musí být *„druhý senior z téže BU jako záloha"*, ale buddy
**také musí být v Session 1+2** — což znamená, že každý první pilot
v nové BU vyžaduje **dva senior committed lidi předem**, což je
v korp realitě ~10 % šance. Metoda potřebuje **bootstrap mechanismus**
(externí coach? rotace Championů z první BU?) a v `01` ani v
ADR-0003 není.

## Útok 3 — „48h kill timer" v ADR-0001 vs. „posune se o 1–3 dny" v 06-session-2 vs. „eskalace na CPO" v 08

Vnitřní rozpor ve třech dokumentech, který v reálném pilotu způsobí
chaos. ADR-0001, sekce Mitigace: *„Eskalační protokol: pokud Decider
'neumí rozhodnout' v session 2, kill timer 48 h, jinak default =
Iterate (max 1×, pak Kill)."* V `06-session-2.md` v Účastníci:
*„Bez Decidera Session 2 neprobíhá. Pokud nemůže, posunout o 1–3
dny."* — to je **odložení**, ne kill timer. V `08-edge-cases-a-rizika.md`
edge case 12 zavádí třetí variantu: *„Decider má 48 h; pak CPO; pak
iterate default."* — to už je **48h timer + eskalace + iterate
default**, tedy hybrid. Které platí? V reálném pilotu: zadavatel
v 11:50 řekne „dejte mi týden". Facilitátor otevře tři dokumenty
a najde tři odpovědi. Decision log nemá kanonický postup, takže
facilitátor improvizuje. Sponsor (CPO) o 48h timeru neví, protože
v Charteru (ADR-0004) sekce „Decider eskalace" **vůbec není**.
Charter má jen *„Decider + mandát od X, datum Y, podpis Z"* — bez
toho, co se stane, **když Decider mlčí**. Oprava: jeden kanonický
protokol, prokopírovaný do `06`, `08` i Charter template. Aktuálně
je to **písemný recept na 'silent project death'** — přesně to,
co edge case 12 deklaruje, že chrání.

## Útok 4 — „AI Act risk-tier classification" jako vstup do Charteru je over-promise

ADR-0002 a `03-pre-session-priprava.md` požadují **AI Act risk-tier
classification před Session 1**, podepsanou DPO. To zní rozumně —
ale v reálu **DPO nedokáže klasifikovat AI Act tier z 1-pager
Charteru**. AI Act Annex III definuje high-risk use cases velmi
specificky (employment, education, critical infrastructure, law
enforcement, …); klasifikace vyžaduje znát **konkrétní data flow,
modelový output, a downstream rozhodnutí**, což je přesně to, co
session má teprve vyrobit. Metoda žádá od DPO podpis **na
něco, co ještě neexistuje**. V praxi DPO buď podepíše „Limited"
default (bez evidence — což je **falešný compliance signal**),
nebo žádá pre-Session 1 design review, čímž celý pre-flight prodlužuje
o další 1–2 týdny. `08-edge-cases-a-rizika.md` tento case **nemá**.
Reálný protokol: AI Act tier je **sliding** — initial assessment
v Charteru s explicit *„provisional, re-assessed in Session 2"*
flagem, finální klasifikace v handoff package po Session 2.
Aktuální dokumenty to formulují jako binary gate, což je
audit-grade compliance theatre. Audit committee (ten, kdo skutečně
DORA compliance vyhodnocuje) tento footwork pozná na pět minut.

## Útok 5 — Sandbox jako „technická pojistka, ne důvěra" má slabý threat model proti shadow IT

Edge case 8 (`08-edge-cases-a-rizika.md`) řeší „Prototyp shipnut
do prod bez review", ale mitigace stojí na *„VPC, watermark, noindex,
24h TTL"*. To zachytí naivního sponzora s copy-paste URL. **Nezachytí
motivovaného sponzora**, který: (1) nasdílí URL přes browser screen
recording, (2) použije v0/Bolt one-click deploy do zákazníkova VPC
— sandbox spec obejde, (3) sponzoring exec už zákazníkovi rollout
slíbil v investor call. Guardrails fungují proti **náhodné expozici**,
ne proti **záměrnému governance bypassu**. Metoda v
`07-handoff-do-vyvoje.md` píše *„Production by stealth je organizační
bug, ne technický"* — a tím se zbavuje odpovědnosti. Ale celá
„Promote-to-prod gate" sekce předpokládá happy path; když sponzor
obejde gate, Pflanzer odpovídá „blame-free retro do 48 h", což je
v korp prostředí **direct trigger pro CISO incident**, ne retro.
Doporučení: **legal-binding throw-away kontrakt** podepsaný sponzorem
před Session 1 (ne až v handoffu), explicit sankce = sponsor osobně
kompenzuje cleanup náklad. Aktuální throw-away flag v Charteru je
**bez sankce**, tedy bez deterring power.

## Útok 6 — „Score deflation 0.5 pro AI-only feedback" je arbitrární číslo bez evidence

`02-role-catalog.md`, `04-session-1.md` a `05-mezi-sessions.md`
opakují *„AI-only persona feedback deflated max 0.5 / 1.0"* jako
core mechanismus. Otázka: **proč 0.5 a ne 0.3 nebo 0.7?** Žádný
ze synthesis dokumentů, žádné ADR, žádný `09-srovnani-existujici-metody.md`
**neuvádí evidenci**. Je to konvence vyšlá z perspektivního panelu,
prezentovaná jako kalibrovaný parametr. To by stačilo pro v0.2,
**kdyby metoda nevytvářela weighted decision matrix**, kde 0.5
přímo ovlivňuje go/iterate/kill threshold. V Session 2 (Decision
gate, sekce Go-criteria): *„Commitment index ≥ threshold z Charteru
(default 70/100)."* Threshold 70 a deflation 0.5 jsou **dva
arbitrární parametry, které se násobí**. Na třetím pilotu jeden EM
ukáže, že variantu B by Pflanzer „schválil" s 71/100, kdyby AI
deflation byla 0.6, a „zamítl" s 69/100 při 0.4. Tím je metoda
**vystavena obvinění z parameter tuning to a desired outcome**.
Oprava: buďto evidence-based kalibrace (tracking AI feedback vs.
human feedback predictive value v T+90 readoutu, retroactive
adjustment), **nebo** explicit *„0.5 je heuristika, ne measurement;
threshold je advisory"*. Aktuálně metoda předstírá precision, kterou
nemá — což je horší než žádné číslo.

## Útok 7 — „> 10 lidí v místnosti = něco špatně" je sanity check, který v korpu vždy selže

`02-role-catalog.md` decision tree s 15 kroky **běžně produkuje
10–14 rolí** pro audit-grade projekt: Zadavatel, PM, Facilitátor,
FE, BE, UX, Security, QA, EM, Legal, A11y, Data, CS, End-user,
DevOps, UX writer, Champion, Solution architect. To je 18 rolí,
z nichž **pro regulovaný customer-facing projekt s integracemi
a multi-team scopem je v decision tree ano-ano-ano-ano** prakticky
na všechny. Pak metoda říká *„> 10 lidí = scope příliš široký,
zúžit nebo paralelní sessions"*. Federovaný workshop model v
edge case 7 je popsán jako *„per-team mini-session 3–4 h každá +
společná final session 3 h"* — to ale **multiplikuje cost**, ne
zužuje. Pro 4-team projekt: 4 × 4 h mini × 5 rolí + 3 h final
× 8 rolí = 80 + 24 = 104 person-hours = **13 person-days jen
v sessions**, plus celý pre-flight × 4. Sanity check říká „zúžit",
metoda dává postup, který „rozšiřuje". Reálný protokol pro korp
projekty je: **rotation model** (klíčové role po celou dobu, ostatní
v 30-min slotech podle agendy), který Pflanzer **nepojmenovává**,
ačkoli v `06-session-2.md` má v Účastníci poznámku *„Konzultativní
role mohou dorazit jen pro svůj blok"* — pro Session 2, ne pro
Session 1 (kde to je víc potřeba). Bez explicitního rotation
playbooku v `04-session-1.md` se tento sanity check stává
prázdnou frází.

## Útok 8 — DORA 7-letý audit log retention je technický nárok, který metoda neumí naplnit

`02-role-catalog.md`, `04-session-1.md`, `06-session-2.md`,
`07-handoff-do-vyvoje.md`, ADR-0001 — všechny opakují *„audit log
s SSO atribucí 7 let pro regulované projekty (DORA)"*. To zní
seriózně. **V realitě** to znamená:
1. Každý prompt do Claude/Cursor/v0/Bolt musí být archivován
   s atribucí na user@SSO, retention 7 let.
2. Každá AI odpověď, každý mockup commit, každý feedback comment
   v Miro / scoring formuláři.
3. Plus decision log, plus audit log session, plus SBOM, plus
   secret scan output, plus DPIA artefakt.

Pflanzer **nedefinuje, kde tento audit log žije**. Není to v
Charteru, není to v sandbox spec, není to v handoff package
checklistu. „Approved AI Tool list" (Claude Enterprise zero-retention,
Cursor Business …) ale **zero-retention znamená, že vendor neretencuje
prompty** — tedy korporátní audit log musí být **side-loaded**.
To je netriviální projekt sám o sobě (SIEM integration, prompt
proxy/MITM, kategorizace, search). `03-pre-session-priprava.md`
zmiňuje *„audit logging do SIEM"* pro sandbox, ale **nikoli pro
prompt content** to AI tools. V auditu DORA inspection bude
otázka: *„Show us the prompts that led to this decision in
project X, dated 18 měsíců zpátky."* Pflanzer odpoví:
*„Claude má zero-retention, takže prompty nemáme."* Auditor
odpoví: *„Tak jste DORA non-compliant."* Metoda potřebuje
**explicit prompt audit pipeline** jako MUST v `03`, ne abstract
„audit log" v každém druhém odstavci.

## Útok 9 — Pre-mortem TRIZ v 15 minutách v Session 1 generuje generická rizika, ne actionable

`04-session-1.md` agenda 10:00–10:15: *„Pre-mortem TRIZ — 'Je 6
měsíců po launchi, fíčura selhala, proč?' — kondenzát 15 min,
generuje rizika dřív, než tým zamiluje variantu."* 15 minut po
charter alignmentu, před Crazy 8s, **bez prototypu**. Co
realisticky vznikne: „security breach", „nikdo to nepoužívá",
„regulátor zakáže", „competitor předběhl", „technický dluh".
To jsou **generic risk archetypes**, ne project-specific scenarios.
Bez konkrétního artefaktu na který reagovat, pre-mortem produkuje
**katalog korporátních úzkostí**, ne actionable risk register.
TRIZ má smysl **po vzniku variant**, ne před nimi — ve 14:00
po vibe-coding kola 1, kdy panel má co kritizovat. Pflanzer zařadil
pre-mortem brzy, aby **„surface-oval rizika dřív, než tým zamiluje
variantu"** (per perspektiva 02), což je rozumný princip — ale
provedl ho **moc brzy**, kdy ještě není co kritizovat. Risk
register na konci Session 1 (top 5 rizik s ownerem a deadlinem)
podle dokumentu existuje; pochybuji, že je výrazně lepší než
ten, který by vznikl bez TRIZ kola. Mitigace: **dvoufázový
pre-mortem** — 5-min „what could break the project" before
Crazy 8s (charter-level), 20-min „what breaks variant X" after
vibe-coding (artifact-level). Aktuální 15-min single-shot je
**performative**, ne diagnostic.

## Útok 10 — „Decider hlasuje poslední" anti-HiPPO pattern předpokládá hierarchicky disciplinovaného Decidera

`04-session-1.md`, `06-session-2.md`, `08-edge-cases-a-rizika.md`
edge case 3, ADR-0001 — všechny opakují *„Zadavatel hlasuje
poslední (anti-HiPPO)"* a *„silent voting před verbálním"*. To
je good intent. **V reálu sponzor v 14:00 v Session 1 přeruší
silent voting** větou *„Před hlasováním bych chtěl říct…"*. Co
udělá facilitátor? `04` říká *„Charter dává facilitátorovi právo
'zadavateli, podržte slovo'"*. Facilitátor je v 70 % případů
junior nebo mid-level zaměstnanec, který je **kariérně závislý
na sponzoringu** od toho samého Decidera. Pravomoc „podržte
slovo" je **paper authority**. `08` edge case 13 říká *„Captured
by HiPPO" — Sponzor mě platí, podvědomě nadržuju → Silent voting,
co-facilitator pro high-stakes sessions"*. Co-facilitator je
zmíněn jednou, **bez** definice, **bez** procesu povolávání,
**bez** rozpočtu. V `02-role-catalog.md` Facilitátor (#3) je
single role, ne pair. Pflanzer potřebuje **explicit
co-facilitator** v audit-grade profilu (MoSCoW SHOULD), nebo
**externí Facilitátor** (Champion z jiné BU, neutrální vůči
sponzoringovému řetězci). Aktuálně metoda závisí na **morální
disciplíně Decidera**, kterou žádná procedura nevynutí.
Anti-HiPPO claim je v `09-srovnani-existujici-metody.md` jeden
ze tří diferenciátorů; reálně je to **best practice, kterou
metoda neumí garantovat**.

## Útok 11 — Reinforcement track T+7/30/60/90 vyžaduje 4 readouty, ale rozpočet mizí po Session 2

`07-handoff-do-vyvoje.md` Reinforcement track: 4 readouty × 2–3
lidé × 30–60 min, plus prep. **Žádný není v Charteru kapacitně
commitnutý**. ADR-0004 sekce „Kapacitní commit" mluví o *„Eng
kapacita: Z person-days za PI"* — pro buildy, ne readouty.
CS a Data jsou v Pflanzer session-time committed, ale post-launch
T+7/30/60/90 je **asynchronní cost** bez story v sprint backlogu.
V praxi T+7 proběhne (čerstvé v paměti), T+30 napůl (Data má
quarterly close), T+60 vyrhán (Champion v jiném pilotu), T+90
neproběhne (sponzor už nepamatuje, že to byl Pflanzer projekt).
Tento pattern jsem viděl v 8 z 8 OKR-driven iniciativ s ritualizovanou
*„retrospective per quarter"* — fakticky ji dělalo 2 z 8 týmů.
`07` říká *„T+90 readout je vstup do další iterace metody samotné"*.
Bez explicit cost commit a owner v Charteru se metoda **neučí**,
jen tvrdí, že se učí. ADR-0004 musí mít sekci „Reinforcement budget
commit (X person-days T+7/30/60/90)" s konkrétním FTE %, ne volnou
zmínku v handoffu.

## Útok 12 — Měřitelnost Pflanzeru samotného: jak víme, že funguje?

`09-srovnani-existujici-metody.md` slibuje, že Pflanzer řeší
**cross-functional alignment problem v korporátu**. Otázka, kterou
si autor metody musí položit: **jak vypadá důkaz, že funguje
lépe než current state?** Současný proces (sériový handoff +
Confluence + 4 meetingy) má **měřitelný outcome**: time-to-launch,
re-work %, late-stage veto count. Pflanzer se měl porovnat **proti
těmto metrikám**, nikoli proti sobě. V dokumentech najdu *„T+90
lagging metric vs success criterion"* — ale to je per-feature
measurement, ne per-method measurement. Žádný z 9 methodology
souborů neobsahuje **method-level success criteria**. Po jakém
počtu pilotů je metoda „validated"? 3? 10? Co je
falsifying outcome? *„Pokud > 50 % pilotů zhasne po druhém cyklu,
metoda je broken"*? Žádné takové kritérium neexistuje. Metoda,
která je sama o sobě o falsifikaci hypotéz (XYZ z Pretotypingu),
**se nemá vlastní falsifying criterion**. To je intelektuálně
zarážející a v audit committee otázka první minuty: *„Kolik pilotů
prošlo, jaký je success rate, jak ho měříte?"* Aktuálně neexistuje
odpověď. Metoda potřebuje **vlastní Charter** (XYZ hypotéza
o sobě samé), s falsifying threshold a kill criteria po N pilotech.
Bez toho je Pflanzer **methodology that exempts itself from its own
discipline** — což je přesně typ kritiky, kterou kdyby Pflanzer
slyšel o jiné metodě, byl by první, kdo by ji formuloval.

## Co metoda dělá DOBŘE (chvála skeptika)

1. **Throw-away default v ADR-0005 je nepopulární a správné.**
   Většina „rapid prototyping" frameworků implicitně předpokládá
   evolve, čímž subsidizuje shadow IT. Pflanzer si v Charteru
   vynucuje vědomé rozhodnutí, a evolve gate má 6 podmínek.
   To je governance, kterou většina metod neměla odvahu napsat.
2. **Discovery Readiness Gate explicitně odmítá řešit discovery.**
   Metoda nepřebírá zodpovědnost za to, co neumí (`01`, anti-pattern 3).
   To je vzácná epistemická poctivost.
3. **Hierarchie závaznosti (Critical / Yellow / Score) namísto
   binárního veta** v `08` edge case 2 a `06` Decision gate.
   Většina workshop metod má binární veto (jednou veto = stop),
   čímž motivuje role k overuse. Strukturovaný downgrade je
   inženýrská odpověď na sociální problém.
4. **Pre-flight triage tracks místo „začneme a uvidíme".** ADR-0002.
   Korporátní governance je z 80 % o tom, co se vyřeší **před**
   meetingem. Pflanzer to chápe — žádná jiná „rapid" metoda nemá
   48–72 h pre-read jako MUST.
5. **Anti-pattern „Pflanzer pro Pflanzer"** (`01-filozofie-a-kdy-pouzit.md`
   bod 7). Metoda explicitně říká, že má říct „my nejsme pro vás"
   a Champion má credibility říct sponsorovi „tohle není pro nás".
   Tato větev rozumí, že adopce stojí na credibility, ne demo
   statistice. To je antithesis SAFe sales pitch a já oceňuji.

## 5 nejostřejších změn které bych vyžádal před pilotem

1. **True Cost Worksheet jako MUST v `03-pre-session-priprava.md`.**
   Realistické person-day budget per role per profil (default,
   regulated, audit-grade) včetně reinforcement T+7/30/60/90.
   ADR-0004 Charter musí mít sekci „Reinforcement budget commit"
   s konkrétním person-days. Aktuální „8–10" je marketingový claim,
   ne odhad — viz Útok 1.
2. **Kanonický Decider eskalační protokol v ADR-0001 +
   `06-session-2.md` + Charter template.** Jeden recept, prokopírovaný
   do tří míst. Aktuální tři verze (Útok 3) jsou písemný recept na
   silent project death.
3. **Bootstrap mechanismus pro Champion v ADR-0003 nebo nový ADR-0006.**
   Externí coach pro první pilot v BU? Rotace Championů z první BU?
   Bez toho metoda neumí škálovat napříč BU-jednotkami a vlastní
   anti-pattern „one-shot demo" se stane realitou v 80 % case-ů
   (Útok 2).
4. **Prompt audit pipeline jako MUST v `03-pre-session-priprava.md`
   pre-flight checklistu.** Ne „audit log do SIEM" abstract, ale
   konkrétní side-loaded prompt retention (vendor-side zero-retention
   ⇒ corporate-side custody chain). Bez toho je DORA 7-letá retence
   compliance theatre (Útok 8).
5. **Co-facilitator nebo externí Facilitátor jako default pro
   regulated/audit-grade profil.** `02-role-catalog.md` Facilitátor (#3)
   musí mít MoSCoW SHOULD na *„independent or co-facilitator pro
   high-stakes sessions"*. Anti-HiPPO claim bez external authority
   je paper authority (Útok 10).

## Co se nedá opravit (a proč ti to nevadí)

1. **Pflanzer nemůže urychlit governance deeper than pre-flight.**
   Pokud DPIA legitimně vyžaduje 3 týdny (special categories,
   cross-border), metoda to nezkrátí. Pflanzer správně říká
   *„AI Act high-risk bez DPIA = session se nekoná"* (`01` anti-pattern
   2). To není flaw, je to limitation core designu — pokud chceš
   speed v regulovaném prostoru, **musíš do plného SDLC**, ne do
   Pflanzeru. Metoda je honest o tom, co neumí.
2. **Pflanzer závisí na maturity AI vibe-coding tools.** Pokud
   v0/Bolt/Cursor mají v session 1 outage nebo vendor zruší
   zero-retention DPA, metoda nefunguje. Žádná methodology
   guardrail tomu nezabrání. Pflanzer to **má rozumně mitigated**
   — pre-tested fallback builder, sanity check builderu per stack
   v `03`. Akceptuju to jako technologickou závislost, ne metodický
   flaw. Stejně jako Scrum závisí na tom, že lidi přijdou na
   stand-up.
3. **Pflanzer je drahý pro single-team scope.** Anti-pattern 4 to
   říká: *„Single-team scope < 1 sprint quick win → použij LDJ"*.
   Korektní self-awareness. Není to flaw, ale floor of viable use.
   Sponsor, který chce Pflanzer pro 2-day fíčuru, nepochopil
   metodu — a `01-filozofie-a-kdy-pouzit.md` to říká nahlas.
4. **Pflanzer netvoří user research; jen ho vyžaduje na vstupu.**
   Discovery Readiness Gate je explicit. Metoda neumí zachránit
   projekt s rotten persona. Akceptuju — kdyby se snažila řešit
   discovery i alignment, byla by to univerzální pacifická pilulka,
   která neřeší nic.
5. **Pflanzer nemůže vyhrát political battle, kde sponsor chce,
   aby metoda prohrála.** Pokud CPO chce protlačit svou agendu
   a sponsor je proti, žádná methodology nezachrání. Pflanzer má
   anti-HiPPO mechanismy (silent voting, Decider hlasuje poslední,
   decision log atribuce), ale tyto fungují **pouze, když exec
   committee ctí proces**. V dysfunkčních organizacích žádná
   metoda nepomůže. Tady je Pflanzer realistický — `01` anti-pattern
   5 (stakeholdeři bez mandátu) říká „eskalace na sponzora **před**
   svoláním, ne po". Jediná možná odpověď.

---

*Konec review. Pokud autor tento dokument přečte a řekne „tohle
jsme přehlédli" alespoň u 4 z 12 útoků, review splnila účel.
Pokud řekne „ten chlap nepochopil", přečtěte si Útoky 1, 3, 8 a 12
ještě jednou — tam je nejostřejší inženýrská kritika, ne metodická
preference.*
