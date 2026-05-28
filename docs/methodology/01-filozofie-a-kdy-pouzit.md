# Filozofie a kdy Pflanzerovu metodu použít

> Cílový čtenář: praktikant (PM, EM, Tech Lead, facilitátor), který zvažuje
> konkrétní zadání a potřebuje fit/no-fit rozhodnutí dřív, než svolá místnost.

## Filozofie

Pflanzerova metoda je **alignment-driven discovery na funkčním artefaktu**.
Vychází z pozorování, že v korporátním prostředí 80 % zpoždění feature není
v psaní kódu, ale v sériové synchronizaci mezi odděleními: business → produkt
→ inženýring → security → legal → DevOps. Každé předání generuje
re-interpretation lag, politickou interpretaci „co řeklo X oddělení" a
late-stage veto. Klasické workshop metodiky to řeší tím, že lidi posadí do
místnosti — ale výstup je dokument (Lean Inception MVP Canvas), Figma fasáda
(Design Sprint) nebo seznam akcí bez ownerství (LDJ). „Alignment na
PowerPointu" se v týdnu 6 implementace ukáže jako alignment na představách,
které si každý z účastníků nakreslil v hlavě jinak [baseline 01].

Pflanzer dotáhne princip „stejní lidé v jedné místnosti" o krok dál:
**rozhodnutí se dělá nad běžícím kódem, ne nad mockupem**. AI vibe-coding je
demokratizační páka — non-designéři vidí, jak nápad vypadá, a non-developeři
vidí, co znamená pro contract. Přínos není rychlost generování UI (to je
hodinový output); přínos je **kompresí sériového handoffu do paralelní
deliberace** a vznik funkčního artefaktu, ke kterému se každá role vyjadřuje
ze své perspektivy s atribuovaným score závaznosti [synthesis 02 — bod 5].

Vztah k existujícím metodám je **kompilační, ne soutěživý**: Pflanzer přebírá
time-boxing a Decider z Design Sprintu, dot voting a silent ideation z LDJ,
MVP-thinking a Sequencer z Lean Inception, mapování pain points napříč
rolemi z Event Stormingu, XYZ hypotézu z Pretotypingu, 1-2-4-All a TRIZ
pre-mortem z Liberating Structures. Diferenciátor jsou tři novinky:
real-time AI vibe-coding, scored department feedback a AI-mediovaná syntéza
[baseline 01 — sekce Syntéza]. Výsledek je **AI-augmented alignment
workshop**, ne nová filozofie produktového vývoje.

Why now: AI generátory (Claude, Cursor, Bolt, v0) v roce 2025–2026 zvládají
end-to-end mockup v sub-hodinovém cyklu. Současně EAA platí od 28. 6. 2025
(A11y povinná pro public-facing + B2B nad 250 zaměstnanců), AI Act zavádí
risk-tier classification, DORA zavádí ICT third-party register a 7letý audit
log. Přesně v okně, kdy AI dovolí kompresi cyklu, regulace zpřísňuje
požadavky na atribuci rozhodnutí. Pflanzer je metodika, která tyto dvě síly
**spojuje, ne staví proti sobě** [synthesis 02 — bod 4].

## Kdy použít — fit kritéria

Pflanzer dává smysl, pokud **současně** platí ≥5 z následujících:

1. **Cross-functional alignment problem.** Rozhodnutí blokují ≥3 oddělení
   (typicky business + produkt + inženýring + security/legal); sériový
   handoff selhává nebo už selhal v podobném zadání.
2. **Funkční prototyp je requirement, ne nice-to-have.** Stakeholdeři
   nedokážou rozhodnout nad mockupem nebo PRD; je potřeba klikací artefakt
   pro „a-ha moment".
3. **Discovery je hotový nebo dohledatelný.** Persona freshness ≤6 měsíců
   (5+ rozhovorů), JTBD podepsaný PM, OST v0 existuje, success metric je
   měřitelná. Pokud chybí, předřaď 2-week Discovery Sprint [synthesis 01 — E].
4. **Scope vejde do kapacitního footprintu.** ~8–10 person-days/cyklus,
   max 2–3 cykly per PI. Default mounting: SAFe IP iteration. Mimo SAFe:
   Atlassian Play / GV Sprint slot [synthesis 03 — krok 13].
5. **Stakeholdeři mají mandát rozhodnout.** Decider je v místnosti nebo má
   asynchronní tie-breaker. Zadavatel má písemný decider mandate od CPO.
   Účastníci nejsou „delegáti delegátů".
6. **Pre-flight triage prošel.** Data Classification ≤L3, AI Act tier
   ≤Limited (nebo High-risk s předem dodanou DPIA), Approved AI Tool list
   s DPA/SCC, Sandbox spec schválený DevOps, Capacity sign-off EM
   [synthesis 01 — B].
7. **Champion existuje.** Někdo v BU se chce stát facilitator-in-training
   (#17 Champion / Pilot lead) a vést druhý+ cyklus; bez toho je metoda
   one-shot demo, ne adopce.

## Kdy NEpoužít — anti-patterns

Tady je řez ostrý. Pokud platí **alespoň jedno**, Pflanzer není správný
nástroj — najdi jiný (viz `09-srovnani-existujici-metody.md`).

1. **Legacy migrace s fixním scope.** Alignment už je, problém je
   execution: 200M řádků DB se nemigruje rychleji, protože UI vyrobíme
   v hodinách [synthesis 01 — Zadavatel × BE]. Použij Event Storming
   (Big Picture) pro mapování bounded contexts a klasický architecture
   review.
2. **Regulovaný projekt s vyčerpaným risk budget.** AI Act High-risk
   bez DPIA, L4 data, special categories bez DPO sign-off, novel vendor
   bez DPA. „Vibe-coding tool je processor v okamžiku, kdy do promptu
   vstoupí osobní data" [synthesis 02 — takeaway 7]. Session se nekoná;
   jde do plného SDLC s formální architecture review gate.
3. **Neexistující persona a discovery debt.** Persona je PowerPoint z
   roku 2024, JTBD chybí, AI-only persona dělá archetype check. Discovery
   Debt Detector skóre ≥7 = STOP [synthesis 01 — E]. Pflanzer **neřeší
   discovery**, pouze ho předpokládá; bez něj vyrobí kosmetickou fikci
   [synthesis 02 — takeaway 2].
4. **Single-team scope < 1 sprint quick win.** Overhead pre-flight (48 h)
   + 2 sessions + reinforcement track > samotná implementace. Použij LDJ
   (30–60 min) nebo Continuous Discovery rytmus.
5. **Stakeholdeři bez mandátu.** Účastníci nemohou commitnout (jsou
   delegáti, čekají na schválení vyšší úrovně, decider mandate chybí).
   Session vyrobí preference, ne rozhodnutí. Eskalace na sponzora **před**
   svoláním, ne po.
6. **Vyhořelá kapacita PI.** Engineering manager hlásí >80 % PI committed,
   nemá buffer 25 %, nemá IP iteraci k dispozici. EM má **veto na
   workshop** [synthesis 03 — sanity check]. Odlož na další PI.
7. **„Pflanzer pro pflanzer".** Sponzor chce metodu, protože je trendy,
   nikoli protože platí 1–6. Anti-pattern „solution looking for problem".
   Champion (#17) musí umět říct sponzorovi „tohle není pro nás" — adopce
   stojí na credibility, ne na demo statistice.

## Vztah k existujícím procesům

- **SAFe IP iteration** je default fit-window. Pflanzer cyklus = ~8–10
  person-days; do IP iterace se vejde 1–2 cykly bez kompromisu na
  innovation/exploration prostor. Mid-PI jen pokud sponzor uvolní commit
  features ekvivalentní kapacitě [synthesis 03 — krok 13]. Pre-PI okno
  je nejcennější (vstupy do PI Planningu).
- **Continuous Discovery (Teresa Torres)** je pre-requisite, ne
  konkurence. OST a JTBD karty z continuous discovery jsou vstup do
  pre-flight gate; Pflanzer cyklus je solution-space deliberace, která
  mapuje na konkrétní node OST. Bez continuous discovery se Pflanzer
  redukuje na alignment-on-feature-without-problem.
- **Innersource champion model** je adopční páka. Druhý+ pilot v nové BU
  vyžaduje #17 Champion / Pilot lead, který vlastní Coaching Kata loop
  (target / obstacle / next), retros do internal CoP, contribution do
  role catalogu [synthesis 03 — #17].
- **DORA / AI Act / GDPR** — Pflanzer se chová jako compliance enabler,
  ne bypass: decision log atribuuje člověka (AI Act čl. 14, GDPR čl. 22),
  audit log s SSO atribucí 7 let (DORA), sandbox = Approved AI Tool list
  s DPA/SCC, DPIA artefakt jako S2 výstup pokud high-risk
  [synthesis 02 — sekce 1, bod 12].

## Co Pflanzer NEdělá (anti-scope)

- **Nenahrazuje user research.** Continuous discovery / persona
  validation / JTBD jsou **vstup**, ne výstup. AI persona je archetype
  check (max 0.5/1.0 score), ne novel insight [synthesis 03 — #14].
- **Nenahrazuje DDD / Event Storming.** Pro komplexní doménu s bounded
  contexts předřaď Big Picture Event Storming; Pflanzer mapuje na
  existující doménový model, nereverse-enginnerá ho.
- **Nenahrazuje SDLC.** P2P (Prototype-to-Prod) checklist je gate, ne
  shortcut. SBOM, secret scan, IaC v monorepu, observability, SLO,
  runbook, change advisory, DPIA, A11y human review — vše musí být
  podepsáno, než prototyp opustí sandbox [synthesis 01 — A].
- **Nenahrazuje architecture review.** Multi-team scope (>3 týmy) nebo
  novel runtime vyžaduje +#18 Solution / Domain architect a paralelní
  ADR proces [synthesis 03 — #18].
- **Nenahrazuje pen test / TLPT** (DORA čl. 24). Post-handoff aktivita,
  out-of-scope pro session [synthesis 02 — sekce 5, WON'T].
- **Nenahrazuje go-to-market.** Marketing claims, copy, launch readiness
  — to je #16 UX writer / Content designer + samostatná launch
  strategie. Pflanzer končí **běžícím produktem v prod** + sign-off package,
  ne launch campaign-ready aktivitou.
- **Není one-shot demo metoda.** Bez reinforcement tracku (T+7/30/60/90)
  a Champion / CoP loopu metoda zhasne po 2 pilotech. Adopce stojí na
  Coaching Kata, ne na pre-launch nadšení [synthesis 02 — sekce 1,
  bod 11].
