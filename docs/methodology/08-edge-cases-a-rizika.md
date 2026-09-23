# 08 — Edge cases a rizika

> Co dělat, když metoda narazí na realitu. Každý edge case má strukturu
> **Situace → Co dělat → Kdo rozhoduje → Mitigace**. Cílem není vyřešit
> všechny patologie, ale dát facilitátorovi konkrétní protokol pro 13
> nejčastějších scénářů.

## 1. Stakeholder z povinné role nepřijde

**Situace.** Dva dny před Session 1: Decider má kalendářní konflikt /
Security manager je nemocný / Legal counsel na PTO. Catalog [02-role-
catalog] označuje jejich role jako POVINNÉ.

**Co dělat per role:**

- **Decider / Zadavatel (#1)** — *„AI proxy ❌ Nelze. Bez něj sessionu
  1 odložit"* [02-role-catalog]. Session se **odkládá**, ne přesunuje
  na delegáta. Decider mandate je nedelegovatelný (perspektiva 03 §
  failure modes).
- **Security (#7)** — pokud existuje pre-charter Security & Data Triage
  s podpisem (krok 0a, [synthesis 03]), session může běžet **v
  generative módu**, ale veto-bearing rozhodnutí čekají na async sign-
  off do 48 h. Pokud triage chybí, session se odkládá.
- **Legal / DPO (#10)** — AI proxy ⚠️ *jen pro L1/L2, minimal/limited
  risk, internal* [synthesis 03]. Pro high-risk AI Act, special
  categories, profiling, novel vendor, marketing claims — **lidský DPO
  povinně**, session se odkládá.

**Kdo rozhoduje.** Facilitátor + PM. Facilitátor má *„právo zadavateli
podržte slovo"* [perspektiva 03], stejně tak právo session zrušit, když
není kvórum.

**Mitigace.** Pre-charter triage 48 h předem [synthesis 01 osa B]
zachytí 80 % případů ex-ante; kalendářní rezervace povinných rolí ≥10
pracovních dní předem; **deputy register** — každá povinná role má
předem nominovaného zástupce s mandátem.

## 2. Security veto v Session 1

**Situace.** Security označí variantu A jako *Critical risk* (STRIDE
Critical, např. *„token v URL parameru"*, *„PII v event property"*,
*„cross-tenant data leakage"*).

**Co dělat — protokol deeskalace:**

1. **Stop generative work na variantě A** — žádný další mockup, žádná
   iterace.
2. **Severity check 5 minut**: facilitátor + Security přečtou veto
   nahlas, ostatní role poslouchají bez reakce (silent listening,
   Liberating Structures).
3. **Mitigation brainstorm 15 minut**: existuje varianta A' s technickou
   mitigací (sandbox watermark, tokenizace, server-side tracking,
   pseudonymizace)?
4. Pokud A' existuje → pokračuje se na A'. Pokud ne → **session
   pivotuje na variantu B/C**, A se vyřazuje [synthesis 01 osa D].
5. Critical veto se loguje do **veto registru** s rationale a
   mitigation návrhy.

**Kdo rozhoduje.** Security final (lidský podpis), AI proxy nepřípustná
[02-role-catalog]. Facilitátor moderuje proces, ne rozhodnutí.

**Mitigace.** Pre-charter Threat model lite (STRIDE one-pager) [synthesis
02] zachytí typické vzory ex-ante; sandbox spec s pre-approved
guardrails redukuje veto-surface area; **hierarchie závaznosti**
(Critical = blocker / Yellow flag = warning / Score = vote) [synthesis
01 osa D] dává Security strukturovanou cestu, ne binární vetovací
hammer.

## 3. HiPPO přebije persony / score

**Situace.** Zadavatel po prezentaci AI syntézy v Session 2 řekne *„já
to cítím jinak, půjdeme s variantou A, i když má score 2.4 vs varianta
B se 4.1"* [perspektiva 02; synthesis 01 § A].

**Co dělat:**

1. **Silent voting před verbálním** [perspektiva 03; Liberating
   Structures 1-2-4-All]. Zadavatel hlasuje **poslední** — anti-HiPPO
   pattern [synthesis 02 bod 10].
2. **Score s rationale field** se zveřejňuje **až po hlasování**, ne
   předem. HiPPO nemůže manipulovat persony.
3. Pokud zadavatel přesto override-uje, **decision log atribuuje
   člověka** s rationale: *„Decider override: variant A despite lower
   score, reason: <textual rationale>"*. Žádné anonymní *„team
   decided"*.
4. Override se trackuje napříč projekty — pokud >30 % decisions je
   HiPPO override, role catalog se kalibruje (signal pro CoP).

**Kdo rozhoduje.** Decider má **informed dictatorship** [synthesis 02
bod 10] — finální slovo, ale s povinným rationale a transparentní
atribucí (DORA, AI Act čl. 14).

**Mitigace.** Decider mandate v Charteru explicitně vyhraňuje, kdy je
score advisory a kdy blocker. Critical risk od Security/Legal/A11y
**nelze override-ovat HiPPO**, jen technickou mitigací nebo pivotem.

## 4. Scope creep během Session 1

**Situace.** Ve 4. hodině Session 1 zadavatel řekne *„když už tu
všichni jsme, přidáme i export do PDF / SSO / multi-tenant"*.

**Co dělat:**

1. **Parking lot okamžitě** — facilitátor zapíše návrh do viditelného
   sloupce *„Parking lot — Session 2 review"*. Žádná diskuse v Session 1.
2. **PM vlastní parking lot review** — každý bod má owner + due date
   + decision (in-scope / next iteration / never).
3. Pokud se scope creep opakuje 3× v jedné session, facilitátor
   zastaví práci a explicitně připomene Charter scope. *„Tato session
   řeší X. Y a Z patří do separátní iterace"* [perspektiva 03 §
   conflict avoidance].

**Kdo rozhoduje.** PM + Facilitátor. PM má tie-breaker na scope, UX
na flow [synthesis 01 § PM × UX].

**Mitigace.** XYZ hypotéza v Charteru s explicit *„Out-of-scope"*
sekcí; facilitátor *„konflikt nadojmem v 5. minutě výskytu, ne ke
konci"* [perspektiva 03 § failure modes].

## 5. AI vygeneruje halucinaci

**Situace.** AI co-pilot navrhne UX pattern, který ergonomicky neexistuje
(*drag-drop tabs s nested modal*) [perspektiva 04]; nebo fabricated API
endpoint (*GET /api/v3/users/preferences/global*, který v
backend systémech není); nebo fabricated legal claim v marketing copy
(*„GDPR-certified"* — neexistující kategorie).

**Co dělat — lidský review checkpoint:**

| Halucinace typ | Detektor | Kdo zachytí |
|----------------|----------|-------------|
| UX pattern | Pattern allowlist v Vibe-brief | FE lead + UX |
| API endpoint | OpenAPI shadow agent diff vs registry | BE lead |
| Legal claim | Marketing template (firemní), nikdy AI-generated | Legal/UX writer |
| Component | Component manifest match | FE lead |
| A11y assumption | axe-core run + manual keyboard test | A11y expert |

**Pravidlo:** žádný AI output nejde do handoff package bez **lidského
podpisu příslušné role**. *„AI je nejlepší co-pilot v místnosti — ale
nikdo nepodepíše rozhodnutí, které udělala AI"* [perspektiva 03].

**Kdo rozhoduje.** Vždy člověk příslušné expertízy, nikdy AI.

**Mitigace.** Tří-režimová matice [synthesis 03]: AI vede jen
execution-heavy context-light tasky; konzultativní role mají AI proxy s
human sign-off 24–48 h; vlastnické a vetovací role vždy člověk. Score
deflation 0.5 pro AI-only feedback (zejména persona) [synthesis 03 #14].

## 6. Discovery debt detekován v Session 1

**Situace.** Ve 30. minutě Session 1 vyjde najevo, že persona je
PowerPoint z roku 2024, JTBD chybí, OST neexistuje. AI Discovery Debt
Detector [synthesis 02 § Discovery] vrací skóre ≥7 z 10 (= STOP).

**Co dělat:**

1. **Facilitátor zastaví session** — žádné další divergence. *„Pflanzer
   řeší alignment, ne discovery"* [perspektiva 02].
2. **Předřadit 2-week Discovery Sprint** [synthesis 01 osa E]: 15
   user rozhovorů, JTBD statement podepsaný PM, OST v0, persona
   freshness ≤6 měsíců (5+ rozhovorů).
3. Session 1 se reschedule po Discovery Sprintu, ne dříve.
4. Náklady na discovery (~10 person-days) jdou na účet projektu, ne
   metody.

**Kdo rozhoduje.** Facilitátor (právo session zastavit) + PM (vlastní
discovery deliverable) + UX (vlastní persona research).

**Mitigace.** Discovery Readiness Gate jako krok 0 [synthesis 03];
persona expiry policy (≤6 měsíců, ≤3 měsíce pro nové segmenty); Voice
of Customer ritual prvních 30 min Session 1 (5 verbatim, 1 audio
recording, 1 anekdota *„nejhorší týden support"*) [perspektiva 13].

## 7. Multi-team scope nezvládnutý

**Situace.** V místnosti je >10 lidí ze 3+ týmů; sanity check v
[02-role-catalog] selhal; každý tým má vlastní backend, vlastní design
system, vlastní release cadence.

**Co dělat — federovaný workshop model** [synthesis 03 krok 12a]:

1. **Per-team mini-session** (3–4 h každá): každý tým řeší svoji
   bounded context, vyrobí sub-mockup + sub-charter.
2. **Solution architect (#18)** [synthesis 03] vlastní integration map
   napříč týmy: bounded contexts, contract dependencies, ADR archiv.
3. **Společná final session** (3 h, max 2 zástupci per tým) — pouze
   integration + alignment, ne generative work.
4. Mezi mini-sessions a final: **shared OpenAPI registry update**, BE
   shadow agenti synchronizují contracty.

**Kdo rozhoduje.** EM + Solution architect společně. Bez Solution
architecta multi-team scope = chaos.

**Mitigace.** Pre-flight check: pokud projekt zasahuje >2 týmy → flag
„multi-team", aktivuje federovaný model; Dependency Map jako povinný
pre-flight artefakt (feature → team → typ → required by → owner)
[synthesis 03 #9 patch].

## 8. Prototyp shipnut do prod bez review

**Situace.** Charter je (default) Track P + evolve — winner varianta
*půjde* do produkce. Sponzor ale nečeká na Ship gate ani sign-off: vidí
sandbox URL varianty po Session 1 nebo 2, dá ji enterprise zákazníkovi
a zákazník ji začne používat „na ostro". Problém není, že by sponzor
obešel throw-away (ten je od ADR-0005 v0.4 jen explicit opt-in), ale že
**evolve zkrátil o Ship gate** — kód, který ještě neprošel quality gates
≥ 80/100 ani sign-off paketem, běží s reálnými uživateli
[perspektivy 04, 08, 15; synthesis 01 osa A; ADR-0005 v0.4].

**Co dělat:**

1. **Okamžité takedown sandbox URL** — Platform team má enforcement
   právo (sandbox modul má 24h TTL + cost cap, ale shadow-IT může
   obejít). Network default-deny + noindex + watermark redukují, ale
   neeliminují.
2. **Blame-free retro do 48 h** [perspektiva 03] — co failnulo:
   technický enforcement (sandbox spec), sociální enforcement
   (Charter / sign-off), nebo komunikace (sponzor nevěděl, že evolve
   ≠ „hned do prod")?
3. **Šance vrátit**: pokud zákazník variantu viděl, ale ještě nepoužívá
   v provozu, sponzor osobně volá s vysvětlením + timeline. U evolve
   je timeline krátká: stejný kód projde Ship gate (quality gates
   ≥ 80/100) + sign-off a nasadí se proper cestou — žádná
   re-implementace.
4. **Governance update**: Charter explicit uvádí, že evolve = „kód jde
   do prod **přes** Ship gate + sign-off", a sponzor podpisem potvrzuje,
   že sandbox URL před Ship gate se externě nesdílí a nepoužívá
   s reálnými daty. U throw-away Charteru (opt-in) platí totéž
   absolutně — artifact do prod nejde nikdy.

**Kdo rozhoduje.** Security + DevOps společně mají takedown autoritu;
EM + sponzor řeší zákaznickou komunikaci; o urychleném průchodu Ship
gate rozhoduje Decider s EM (gate se nesnižuje, jen priorizuje).

**Mitigace.** Sandbox jako **technická pojistka, ne důvěra** [perspektiva
15]: VPC, watermark, noindex, 24h TTL, žádný route do prod sítě.
Evolve je default v Charteru, ale prod deploy je podmíněn Ship gate
(quality gates ≥ 80/100) + kompletním sign-off paketem (FE + EM +
Security + Legal + Platform + QA) [ADR-0005 v0.4; synthesis 01 osa A].
Throw-away zůstává explicit opt-in pro 3 use-casy s rationale
v Charteru. *„Production by stealth"* je organizační bug, ne technický
[perspektiva 04].

## 9. Score se stane politickým nástrojem

**Situace.** Oddělení X dá variantě skóre 1 (=blocker), aby se zbavilo
implementační práce, ne kvůli reálnému riziku. Nebo: oddělení Y dá
nadhodnocené skóre 5, aby protlačilo svou agendu.

**Co dělat:**

1. **Rationale field povinné** [synthesis 02 bod 5] — score 1 nebo 5
   bez rationale = invalid, facilitátor odmítá v aggregate.
2. **Pattern detection napříč projekty** [perspektiva 12 § learning
   loop]: facilitátor sleduje, které role chronicky underscore-ují
   nebo overscore-ují. Po 5+ projektech kalibrace v CoP.
3. **Hierarchie závaznosti** [synthesis 01 osa D] odděluje
   *Critical (blocker)* od *Yellow flag (warning)* od *Score (vote)*.
   Kdo dá Critical bez STRIDE/A11y/Capacity/Legal evidence = facilitátor
   downgrade-uje na Yellow flag.
4. **Decision log atribuuje hlasy s rationale**, ne anonymně. Politický
   tlak vidí každý.

**Kdo rozhoduje.** Facilitátor má pravomoc downgrade scoru bez
rationale; CoP vlastní long-term kalibraci.

**Mitigace.** Standardizovaná škála 1–5 Likert [synthesis 02 bod 5]
uložená do interní DB; AI-only feedback weight max 0.5; transparency
napříč Decision logem.

## 10. Champion odejde

**Situace.** T+45 dní po handoffu Champion mění tým / firmu.
Reinforcement track (T+30/60/90) ohrožen [perspektivy 07, 13].

**Co dělat:**

1. **Champion buddy aktivuje** — předem nominovaný druhý senior z téže
   BU [methodology 07].
2. **Knowledge transfer protokol** (≤5 pracovních dní):
   - 30-min recap deck (achieved milestones, parking lot, open risks).
   - Async video walkthrough handoff package (≤20 min).
   - Decision log čtení s buddy (≤60 min).
   - CS proxy + Data + EM seznámeni s buddy jako novým point-of-contact.
3. **CoP notification** — odchod championa je signál o adopci/burnout,
   loguje se pro pattern detection.

**Kdo rozhoduje.** EM (alokace buddy) + PM (re-commit od přijímajícího
týmu).

**Mitigace.** Champion buddy povinný od začátku [methodology 07]; CoP
sleduje champion turnover jako signal o sustainability metody.

## 11. Mezi-session feedback windowless

**Situace.** Mezi Session 1 a 2 je 3–7 pracovních dní (podle stupně, ADR-0021), ale 3 z 8 stakeholderů jsou
na PTO / on-site visit / quarter close [perspektiva 03 § energy curve].

**Co dělat:**

1. **Asynchronní sběr default-on**: Miro board s prototypem variantami
   + scoring formulář + threaded comments. Stakeholder hlasuje
   asynchronně do deadline.
2. **Video recap** (≤10 min) prezentace prototypu — facilitátor
   nahraje, sdílí s PTO stakeholdery, ti hlasují async.
3. **Quorum rule**: pokud <60 % povinných rolí dosáhne deadline,
   Session 2 se posune o ≤5 dní. Pokud >60 % a missing role je
   nevetovací → Session 2 běží, async input se započítává; mlčení nevetovací role po
   deadline = „no objection“ zapsané do decision logu (ADR-0021).
4. Vetovací role (Security, Legal, EM kapacita) bez async sign-offu =
   Session 2 ne-decision-making, jen review.

**Kdo rozhoduje.** Facilitátor + PM. PM vlastní stakeholder kalendář.

**Mitigace.** Mezi-session podle stupně (Quick 3 / Lean 3–5 / Full 5–7
pracovních dní, ADR-0021), prototyp deployed do 48 h, připomínka 48 h
a 24 h před deadline [perspektiva 03]; PTO check při plánování Session 1
(≥10 dní předem). Pokud vetovací role okno nestihne, upgrade stupně nebo
odklad Session 2, ne prodlužování okna.

## 12. Session 2 končí bez rozhodnutí

**Situace.** Session 2 je 3 h rozhodovací [perspektiva 03], ale Decider
po 3 h řekne *„potřebuju to ještě promyslet, dejte mi týden"*.

**Co dělat.** Aplikuj **kanonický Decider eskalační protokol** v
**`docs/decisions/0001-decider-model.md`**. Stručně:

- **Decider chybí v Session 2** (Scenario A): posun max 5 pracovních dní,
  dál eskalace na CPO (5 dní), dál automatický Kill.
- **Decider říká „potřebuju víc času"** (Scenario B): T+48 h písemné
  rozhodnutí do decision logu, T+72 h eskalace na CPO, dál „Iterate default"
  (chrání před tichým úmrtím).
- **Iterate exhausted** (Scenario C): hard cap 1 další iterační rozhodovací
  session (Session 2b per ADR-0001; nezaměňovat se Ship gate), pak automatický Kill.

**Důležité:** **neduplikuj** zde text protokolu — autoritativní zdroj je
ADR-0001. Kopírování textu způsobuje rozcházení verzí (původní bug v0.2,
adresován devil's advocate Útok 3).

**Kdo rozhoduje.** ADR-0001 protokol — Decider → CPO → automatický default
podle scenario.

**Mitigace.** Decider mandate podepsaný CPO písemně před Session 1
[synthesis 03 #1 patch]; informed dictatorship explicitně v Charteru;
Session 2 jako rozhodovací, ne generativní (3 h struktura: 30 min
prezentace / 60 min debata / 30 min go-iterate-kill / 30 min handoff
podpis [perspektiva 03]).

## 13. Failure modes facilitátora

[perspektiva 03 § 5] — facilitátor je nejčastější bod selhání metody.
Šest patologií + protijed:

| Failure mode | Symptom | Protijed |
|--------------|---------|----------|
| **Captured by tool** | 40 % session debugováním Boltu | AI co-pilot v sub-roli, ne main UI; pre-tested fallback builder (Stitch + Cursor); facilitátor sleduje agendu, ne IDE |
| **Captured by HiPPO** | Sponzor mě platí, podvědomě nadržuju | Silent voting, Decider hlasuje poslední; *„právo zadavateli podržet slovo"* v Charteru; co-facilitator pro high-stakes sessions |
| **Conflict avoidance** | *„Vyřešíme potom"* | Konflikt nadojmem v 5. minutě výskytu, ne ke konci; facilitator playbook (sekce 2 výše) jako muscle memory |
| **Energy blindness** | Tlačím přes agendu, tým mrtvý | Break každých 90 min nediskutuju; pulsní check-in (1–5 prst) každé 2 h; konec Session 1 v 16:00, ne 17:30 |
| **AI as authority** | *„AI navrhla"* = autoritativní argument | Každý AI insight má human override; Decision log atribuuje **člověka** (AI Act čl. 14, GDPR čl. 22); AI = co-pilot, ne pilot |
| **Charter creep** | 12 perspektiv chce 30+ vstupů | MoSCoW na vstupy [synthesis 02 § 5]: Default = MUST only, regulated = MUST + SHOULD, audit-grade = vše; facilitátor má právo *„won't do this session"* |

**Kdo rozhoduje.** Facilitátor sám sebe nereviduje — **co-facilitator
nebo CoP buddy** [synthesis 03 #17 Champion role] dělá observation +
feedback po každé 3. session. Po 10 sessions kalibrace v CoP.

**Mitigace.** Facilitátor není moderátor, je **architect of accountability**
[perspektiva 03]: rozhoduje, kdy AI mluví, kdy člověk mlčí, kdy se
konflikt eskaluje. Bez té tří-cestné dělby je Pflanzer rychlejší way to
fail at scale.
