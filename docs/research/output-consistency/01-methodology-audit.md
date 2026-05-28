# Methodology Audit — output consistency (prototype vs production-ready product)

> **Auditor:** senior methodology editor (sub-agent run)
> **Datum:** 2026-05-28
> **Scope:** 13 souborů v `docs/methodology/` + ADR-0005 (throw-away vs evolve)
> **Korekce uživatele (May 2026):** *„Pflanzer metoda by ti měla dát již reálný
> běžící produkt, proto je tam od startu programátor, aby to šlo rovnou nasadit.
> Žádná specka se pak už programátorům nedává. Výstup z Pflanzer metody je
> hotový produkt."*

---

## TL;DR

Positioning **NENÍ konzistentní**. Repo má **dvě paralelní vrstvy** výstupu, které
si protiřečí:

1. **„Lean Pflanzer" vrstva** (`00-lean-pflanzer.md`) říká *„většina kódu jde
   rovnou do produkce"*, *„3 funkční weby, ne mockupy"*, *„Ship to prod 1-2 dny
   vývojářů"*. Tento layer **respektuje** uživatelskou korekci.
2. **„Audit-grade" vrstva** (`04-session-1`, `05-mezi-sessions`, `06-session-2`,
   `07-handoff-do-vyvoje`, `00-tldr`, `01-filozofie`) **systematicky** používá
   slovník *„prototyp / klikací prototyp / mockup / handoff package / re-implementace"*.
   Slovo *„prototyp"* se v 7 souborech objevuje **80+ krát**. ADR-0005 explicitně
   říká *„Default = throw-away, kód lze copy-paste-adapt, ne git-merge"* —
   to je **přímý protiklad** *„hotový produkt"*.

**Počet P0 míst k opravě:** ~22 (top-10 níže s recommendation). **Risk:** buyer
čte TL;DR `00-tldr.md` → vidí *„klikací prototyp + handoff package"* → mentální
model = *„dostaneme spec, naši dev to potom postaví"*. To je **falešná
prodejní pozice** versus tvůj reálný claim.

**Hlavní napětí:** **ADR-0005 (throw-away default) doslova zakazuje produktový
output.** Pokud má být *„hotový produkt"* default — ADR-0005 musí být převrácen
na *„default = evolve s production-grade kvalitou"*, nebo musí být explicitně
re-framed („throw-away" jako *throw-away of 2 of 3 variants — winner ships*).

---

## Per-file scan (13 souborů)

### 1. `00-tldr.md` — **WEAK** (management 1-pager, kde to nejvíc bolí)

**Citáty:**

- L16-17: *„AI slouží jako vibe-coding páka, která z verbálního inputu týmu
  generuje **funkční mockupy** v reálném čase"*
- L18: *„cross-functional alignment **na funkčním artefaktu**, ne na PowerPointu"*
- L28: *„AI generuje **1–3 mockupy**"*
- L31: *„**klikací prototyp** v sandbox VPC s 24 h TTL a watermark"*
- L41: *„**Co dostaneš (artefakty)**"* — celá sekce mluví o *„anotovaných
  klikacích prototypech"*, *„handoff package: scoped epic, akceptační kritéria,
  P2P checklist"*
- L45: *„1–3 anotované **klikací prototypy** v izolovaném sandboxu"*
- L86-87: *„Bez kompletního paketu **prototyp neopustí sandbox**"*

**Diagnóza:** TLDR popisuje output jako (a) klikací prototyp (b) handoff package
(spec + checklisty). **Nikde** v `00-tldr.md` slovo *„produkční kód"*,
*„deploy do prod"*, *„nasazený produkt"*. Manažer který čte 1-pager dostává
**spec-driven mentální model**: *„AI workshop produkuje papírové artefakty,
naši inženýři to potom postaví"*.

**Severity:** P0. Tohle je první stránka, kterou buyer čte.

---

### 2. `00-lean-pflanzer.md` — **STRONG** (jediný konzistentní soubor)

**Citáty:**

- L14: *„většina **kódu jde rovnou do produkce**"*
- L45: *„**Den 11-14: Ship to prod (1-2 dny vývojářů)**"*
- L46: *„`/pflanzer-session-3 <slug>` # extract → quality gates score 0-100"*
  ⚠️ (drobnost: viz problém #4 níže)
- L47: *„`/pflanzer-handoff <slug>` # PR-ready package"*
- L48: *„Vývojáři **doladí edge-case bugy**, deploy, monitorování"*
- L53: *„**3 funkční weby (ne mockupy v Figmě)** — clickable, deployed
  v sandbox URL"*
- L54-55: *„**Winner kód (≥80/100 gate score)** — Vite + React + TS + ESLint +
  Vitest, **exportovatelný do target repu**"*
- L56: *„Per-role handoff s odkazy na konkrétní soubory (ne TBD placeholders)"*

**Diagnóza:** Toto je **jediný** soubor, který respektuje uživatelskou
korekci. Sděluje: tým postaví 3 funkční weby v session 1, winner se mergne, dev
týden 11-14 jen doladí edge-cases.

**Slabost:** Slovo *„prototyp"* se ani zde úplně neeliminuje — ve standardním
toku se mluví o *„prototyp"* (Den 6-9 *„stakeholdeři klikají"*). Anti-pattern
list L131 dokonce zní: *„Vývojářský tým nevidí Session 1 **prototyp**"*. Tj.
i lean profil interně mluví o prototypu — jen claim *„většina kódu jde do
produkce"* L14 a *„Ship to prod L45"* nese tu strong pozici.

**Severity:** P2 (drobné slovo *„prototyp"* zde-tam ale claim **je** o hotovém
produktu).

---

### 3. `01-filozofie-a-kdy-pouzit.md` — **MID**

**Citáty pro:**

- L8: *„**alignment-driven discovery na funkčním artefaktu**"*
- L20: *„**rozhodnutí se dělá nad běžícím kódem, ne nad mockupem**"* ← strong
- L24: *„vznik **funkčního artefaktu**, ke kterému se každá role vyjadřuje"*

**Citáty proti:**

- L51-53: *„**Funkční prototyp** je requirement, ne nice-to-have. Stakeholdeři
  nedokážou rozhodnout nad mockupem nebo PRD; je potřeba **klikací artefakt**"*
- L136-139: *„**Nenahrazuje SDLC.** P2P (Prototype-to-Prod) checklist je gate,
  ne shortcut. SBOM, secret scan, IaC v monorepu, observability, SLO,
  runbook, change advisory, DPIA, A11y human review — vše musí být
  podepsáno, **než prototyp opustí sandbox**"*
- L147: *„**Pflanzer končí handoff package, ne launchem**"* ← **DIRECT PROTIKLAD**
  uživatelské korekce

**Diagnóza:** Soubor má dva moduly. *„Filozofie"* (L7-42) říká *„běžící kód
místo mockupu"* — strong. *„Anti-scope"* (L128-151) explicitně tvrdí, že
metoda končí handoff packagem a ne launchem (= *„dev tým převezme"*). To je
**inkonzistence v rámci jednoho souboru**.

**Severity:** P0 (L147 fráze *„Pflanzer končí handoff package, ne launchem"*).

---

### 4. `02-role-catalog.md` — **MID**

**FE / Vibe-coding lead (#4) výstup, L66-68:**
> *„komponentový mapping, token compliance > 90 % per varianta, throw-away/evolve
> decision, repo + commit history s Figma↔kód lineage"*

→ *„repo + commit history"* je strong, ale *„throw-away/evolve decision"*
default = throw-away (per ADR-0005) = **prototyp není produkt**.

**BE / API lead (#5) výstup, L74-78:**
> *„Draft OpenAPI 3.1 per varianta (BE shadow agent generuje paralelně k UI
> mockupům), breaking-change registr, 3–5 ADR drafts, contract test skeleton
> (Pact / Schemathesis), **migration plan stub**"*

→ *„draft"*, *„skeleton"*, *„stub"* — **explicit prototype language**, ne
production code. BE lead **negeneruje production kód v session**, jen spec a
draft. Tohle je **přesně to**, co uživatelská korekce kritizuje (*„žádná specka
se pak už programátorům nedává"*).

**Mockup generation v sekci „Režim 3 — AI vede" L313:**
> *„Mockup generation (vibe-coding tool dle stacku)"*

→ AI vede *„mockup generation"*, ne *„production code generation"*. Slovní
volba říká: AI vyrábí mockups, ne production.

**Severity:** P0 — role catalog kodifikuje, že FE/BE leadi produkují drafts/
skeletons/stubs, ne running prod code. To je strukturální problém.

---

### 5. `03-pre-session-priprava.md` — **WEAK**

**Citát — kritický:**

L164 (True Cost Worksheet, FE / Vibe-coding lead PD breakdown):
> *„FE / Vibe-coding lead (#4) | 0.5 (vibe-brief, builder) | 0.75 | 1.0 (iterace)
> | 0.5 | **1.0 (extract / hardening, viz Sprint 2)** | …"*

→ **„extract / hardening"** je **přímé doznání**, že prototyp **NENÍ** prod-ready
po Session 2 — FE lead potřebuje 1 PD v handoff fázi pro *extract* z prototypu
a *hardening*. To je **production hardening po Session 2**, což přesně byla
fráze v zadání jako anti-pattern.

L177:
> *„hardening a reinforcement: **3× vyšší** [než 10 PD]"*

→ Total ~32 PD se 3× hardening overhead. *„Hotový produkt"* by NEMĚL potřebovat
hardening — pokud je to *built right the first time* per uživatelskou korekci.

L274:
> *„Production deployment artefakty — vyžadují **samostatný architecture
> review gate po Session 2**"*

→ MoSCoW *„WON'T"* sekce: production deployment je out-of-scope pro session
1. Tj. **production work se děje až po Session 2 v separátním procesu**.
Inkonzistentní s *„hotový produkt"*.

**Severity:** P0. True Cost Worksheet a MoSCoW WON'T sekce kodifikují
post-Session-2 hardening fázi.

---

### 6. `04-session-1.md` — **WEAK** (header říká *„funkční mockupy"*)

**Citáty:**

- L3-4 (status): *„Generativní session: cross-functional alignment, **1–3 funkční
  mockupy**, preference matrix, score závaznosti per role, Decider's go/no-go
  shortlist"*
- L9: *„Vyrobit **1–3 funkční mockupy** anotované na konkrétní node v OST"*
- L11: *„**Mockupy nejsou Figma fasáda — jsou runnable v sandboxu**"* ← strong
- L13-14: *„Session **neproduktivuje finální feature** — produkuje
  **alignovaný shortlist**, který poputuje do scoring window"*
- L24: *„AI nese execution-heavy zátěž (**mockup generation**, …)"*
- L57: *„AI vibe-coding kolo 1 — **3 paralelní varianty**. AI builder generuje
  3 varianty paralelně z merged Crazy 8s"*
- L72: *„Generování **mockupů** | **AI** | Lidi to neumí dost rychle, AI 3
  varianty / 20 min"*
- L137: *„Lepší zastavit po 90 minutách, než **vyrobit 3 mockupy** ke špatnému
  problému"*
- L145: *„**1–3 anotované mockupy** s embed link (public preview URL bez
  accountu)"*

**Diagnóza:** L13 — *„Session neproduktivuje finální feature"* — je **PŘÍMÝ
PROTIKLAD** uživatelské korekce. Pokud má být výstup *„hotový produkt"*,
Session 1 + Session 2 dohromady **mají** doručit feature připravený k nasazení.

**Severity:** P0. L13 je hard contradiction.

---

### 7. `05-mezi-sessions.md` — **WEAK**

**Citáty:**

- L1-3: *„Scoring window mezi Session 1 a Session 2: **prototype hub** s 1–3
  variantami"*
- L9: *„Zhmotnit Session 1 shortlist do **klikacího prototypu** v 1–3
  variantách"*
- L18: *„**Den 1–2**: **deploy prototypů do sandboxu** (max 48 h od konce
  Session 1)"*
- L26: *„**Prototype hub spec**"*
- L37: *„Throw-away/evolve flag (default = throw-away)"*
- L40-41: *„Sandbox URL s 24h TTL refreshovaným do konce scoring windowu;
  audit logging do SIEM, **žádný route do prod sítě**"*
- L60: *„Žádné prod credentials, **žádný route do prod sítě**"*

**Diagnóza:** Slovo *„prototyp"* + *„prototype hub"* dominuje. *„Žádný route do
prod sítě"* technicky zabraňuje produktu opustit sandbox. Jedná se o **klikací
prototyp s sandbox guardrails**, ne o running produkt. Pflanzer fáze *„mezi
sessions"* je **strukturálně prototype-only**.

**Severity:** P0 (název *„prototype hub"* + *„žádný route do prod sítě"* dvakrát).

---

### 8. `06-session-2.md` — **WEAK**

**Citáty:**

- L52: *„**Handoff package** preview + AI Act Fáze C sign-off"*
- L86-89: *„**Prototyp do prod**: throw-away je default v Charteru. „Evolve"
  jen po kompletním sign-off paketu"*
- L155-187: Celá sekce *„Handoff package (do 48 h od Session 2)"* — vyjmenovává
  18 artefaktů: *„scoped epic, PRD-lite, akceptační kritéria, OpenAPI,
  Dependency Map, P2P checklist, Audit log, …"*. **Nikde** *„production-ready
  PR-ready kód"*, *„merged main branch"*, *„deployed feature flag at 1%"*.

L188:
> *„Pokud Decider's call = **GO**:"* → následuje 18-bod list **specifikací**,
ne *„deploy probíhá v T+1 den po Session 2"*.

**Diagnóza:** Session 2 GO rozhodnutí produkuje **18 spec/policy/checklist
artefaktů**. To je **přesně handoff specka pro dev tým**, kterou uživatelská
korekce explicitně **zakazuje**.

**Severity:** P0 (toto je centrální dokument; sekce 155-187 je doslova
*„spec-handoff-for-dev"* pattern).

---

### 9. `07-handoff-do-vyvoje.md` — **WEAK** (název už říká „**do vývoje**")

**Sám název souboru:** *„07 - handoff **do vývoje**"* — tj. dev tým je
recipient, ne participant. To je **inkonzistentní** s claim *„dev je v room
od minuty 0"*.

**Citáty:**

- L3-5: *„Výstupem Session 2 není **„kód"**, ale **podepsaný handoff package**,
  který tým vývoje **může vzít a postavit z něj produkt** — nebo ho vědomě
  zahodit"* ← **TOHLE JE PŘÍMÝ PROTIKLAD** uživatelské korekce. *„Vzít a
  postavit"* znamená re-implementaci, ne hotový produkt.
- L9-11: *„**Prototyp není produkt.** Default kontrakt v Charteru je
  **throw-away pattern**: prototyp slouží k alignmentu a falsifikaci variant,
  po Session 2 se **zahazuje a produkční implementace startuje** na paved-road
  template"* ← **DRUHÝ přímý protiklad**. *„Produkční implementace startuje"*
  AŽ PO Session 2.
- L13-19: Evolve pattern je opt-in, vyžaduje *„token compliance >90 %, a11y
  Critical/Serious clean, SBOM + secret scan clean, DPIA pokrytí"* atd. — six
  podmínek. Default = throw-away.
- L107: *„**Bez 9/9 položek prototyp neopouští sandbox**"* (P2P checklist).
- L190-216: *„Promote-to-prod gate"* checklist (16 položek) **PŘED prvním
  produkčním deployem**. To znamená: produkční deploy se **NE-dělá v Pflanzeru**;
  děje se **AŽ POTOM** přes Promote-to-prod gate.
- L244-251: *„Co handoff NENÍ: ZIP soubor s prototypem hozený přes plot,
  Jira ticket „implement Figma", „Vibe-deployed" Bolt instance s prod
  credentials, …"* → toto popírá *„ne handoff přes plot"*, ale **nepopírá**
  základní handoff-as-handover pattern.

**Diagnóza:** Tento soubor je **epicentrum nekonzistence**. Filozofie souboru
L3-19 explicitně říká:
1. Output není kód, je spec-handoff.
2. Prototyp není produkt; prototyp se zahazuje.
3. Produkční implementace startuje **po** Session 2 (= dev tým převzme).

To jsou **3 hard contradictions** s uživatelskou korekcí v rámci 16 řádků.

**Severity:** P0 (highest priority pro fix).

---

### 10. `08-edge-cases-a-rizika.md` — **MID**

**Citát — důležitý:**

L199-228: *„**8. Prototyp shipnut do prod bez review**"*
> *„Situace. Sponzor vidí Bolt deploy URL, dá ji enterprise zákazníkovi,
> zákazník ji začne používat „na ostro". **Throw-away kontrakt v Charteru
> ignorován**"*

→ Toto je explicit edge-case: *„production by stealth"* je **failure mode**.
Tj. *„prototyp jde do prod"* je v současné metodě **bug**, ne feature. Ale
uživatelská korekce tvrdí, že *„hotový produkt"* JE výstup. **Strukturální
konflikt:** současný edge-case #8 je v lean profilu standardní happy path.

L223: *„**Production by stealth** je organizační bug, ne technický"* —
explicit framing.

**Severity:** P0 (edge case #8 musí být re-framed pro lean profil — buď
přesunut do audit-grade only, nebo přepsán: *„Production by stealth = lifting
without sign-off"*, ne *„prototyp v prod"* per se).

---

### 11. `09-srovnani-existujici-metody.md` — **STRONG** (jediná místa kde claim drží)

**Citáty:**

- L36 (AI workflow family table): *„Pflanzer | AI pilot fixture (cross-fn,
  14d, **prod handoff**) | …"*
- L38: *„**Cíl** | Cross-functional alignment + **production code z 2 sessions** | …"*
- L54 (enterprise consulting table): *„**Typický deliverable** | 1-3 prototyp
  + handoff package + 14d cycle"*

L38 *„production code z 2 sessions"* je **správný claim**. Ale je v rozporu
s rest of dokumentace, kde Session 2 produkuje *„spec + checklist + decision
package"*.

L54 mluví o *„1-3 prototyp + handoff package"* — kompromisní formulace,
nikoli *„hotový produkt"*.

**Severity:** P3 (jen drobné: deliverable na L54 by mělo říct *„1-3 funkčních
webů, winner shipped + handoff metadata"*, ne *„1-3 prototyp"*).

---

### 12. `method-charter.md` — **WEAK**

**Citát kritický:**

L42-44 (XYZ hypotéza):
> *„Věříme, že Pflanzerova metoda **zkrátí čas od „nápad" k „handoff package"**
> o ≥ 50 % (z baseline ~6–9 měsíců sériového handoffu na ~6–9 týdnů 2-session
> cyklu)"*

→ XYZ hypotéza optimalizuje **time-to-handoff-package**, **NE** time-to-prod-
deployed-feature. To je **strukturálně špatná metrika** vůči uživatelské korekci.
Pokud má být output *„hotový produkt"*, primary metric musí být
time-to-merged-PR / time-to-first-prod-deploy, **ne** time-to-handoff.

L62 (Success metric):
> *„Primary lagging — Time-to-handoff | ≤ 50 % baseline | Od signed Charter
> timestamp do **first commit s `#handoff` tag** v target dev repo"*

→ Měří *čas k tagu `#handoff`*, ne čas k *deploy* nebo *PR merged*. Závisí
na tom, **co `#handoff` znamená v real-world** — pokud znamená *„PR open
+ approved + ready to merge"*, je OK. Pokud znamená *„spec handed to dev
team"*, je v rozporu s uživatelskou korekcí.

L63: *„Leading — **Handoff acceptance** | ≥ 80 % artefaktů použito v T+30"*
→ Měřit *„kolik artefaktů z handoff package dev tým použil"* implicitně
předpokládá, že **dev tým artefakty přijme a začne implementovat**. To je
spec-handoff model, ne *„produkt už běží"* model.

**Severity:** P0 (XYZ hypotéza je load-bearing claim; metric design říká
*„zkrátíme handoff"*, ne *„dodáme produkt"*).

---

### 13. `leading-indicators.md` — **MID**

**Citát — important nuance:**

L144-176 (LI-5 Throwaway→Evolve slip rate):
> *„LI-5 = (# pilots s charter.flag = throwaway AND **post-handoff prototype
> routed to production/customer-facing** AND missing one or more required
> evolve sign-offs) / …"*

L168: *„Throwaway default deteriorating; Method Steward review of sponsor
education"*
L171: *„Charter sign-off discipline broken. … **Production-by-stealth risk**"*

→ Indicator **trestá** případy, kdy se *„prototyp dostane do prod"*. To je
**konzistentní s ADR-0005 throw-away default**, ale **NE-konzistentní** s
uživatelskou korekcí. Pokud má být *„hotový produkt"* default, LI-5 musí
být re-framed (např. *„Production deploy without quality gates"*), ne
*„throw-away slip"*.

**Severity:** P1 (přímo měříme metriku, která odměňuje *prototype-only* mindset).

---

### Příloha: ADR-0005 — KEY TENSION

**ADR-0005 explicit citáty:**

- L25: *„Variant 3 s **defaultem throw-away**"*
- L30-33: *„Prototyp je **discovery artefakt** s 24h TTL sandbox. Produkce
  se píše znovu na základě **Handoff package**"*
- L34: *„Code z prototypu **lze copy-paste-adapt, ne git-merge**"*
- L50: *„Throw-away → Handoff package = **specifikace + draft kódu jako
  reference**"*
- L57: *„Throw-away znamená **duplicitní práce** (prototyp + produkce)"*
- L67: *„AI co-pilot fáze 2 generuje Handoff package **přímo z prototypu**,
  takže rewrite není „od nuly" — je to **specs-driven re-implementation**"*

**Diagnóza:** ADR-0005 je v **absolutním** protikladu k uživatelské korekci.
L34 *„copy-paste-adapt, ne git-merge"* + L57 *„duplicitní práce
(prototyp + produkce)"* + L67 *„rewrite není od nuly — je to specs-driven
re-implementation"* — **toto všechno** říká: *„prototyp je throw-away,
production je re-write"*. Uživatelská korekce říká: *„hotový produkt, žádná
specka pro dev"*. **Nejde to oba**.

**Klíčová otázka pro tebe:**
> ADR-0005 default = throw-away je **zakotvený v sedmi souborech**. Pokud má
> být *„hotový produkt"* claim, **ADR-0005 musí být zrušený nebo přepsaný na
> default = evolve s production-grade quality gates from minute 0**.

**Možná „smířlivá" čtení (zda ADR-0005 lze zachovat):**

- **Option A (re-frame throw-away):** *„Throw-away = 2 z 3 variant se zahazují
  v Session 2. **Winner** se mergne přes Promote-to-prod gate a deploy."*
  Pak ADR-0005 je o **variant selection** (3 → 1), ne o *„prototype vs production"*
  dichotomy. To je **kompatibilní** s uživatelskou korekcí.
- **Option B (default switch):** *„Default = evolve s production-grade quality.
  Throw-away je opt-in pro discovery-only piloty (no release intent)."*
  Tohle by **vyžadovalo** přepsat ADR-0005 + všechny downstream reference (7
  souborů).
- **Option C (reálná dichotomie):** Pflanzer **má** dva profily:
  *„Discovery Pflanzer"* (throw-away default, 4 souborů) a *„Production Pflanzer"*
  (evolve default = *„hotový produkt"*). Současný stav repo je **mix obou**,
  což je důvod inkonzistence.

**Doporučuji Option A** jako rychlou path → minimální changes do ADR-0005,
re-frame *„throw-away"* na *„variant pruning"*, claim *„hotový produkt"* drží
přes evolve sign-off, který se v lean profilu zjednoduší.

---

## Top 10 problematic phrases (P0 fix recommendations)

| # | File:Line | Current text | Recommended replacement | Why it matters |
|---|-----------|--------------|-------------------------|----------------|
| 1 | `07-handoff-do-vyvoje.md:3-5` | *„Výstupem Session 2 není „kód", ale podepsaný handoff package, který tým vývoje může vzít a postavit z něj produkt — nebo ho vědomě zahodit."* | *„Výstupem Session 2 je **PR-ready kód winning varianty** v target repo + handoff metadata (decision log, ADR drafty, P2P sign-off pakety). Dev tým, který byl v session od minuty 0, doladí edge-case bugy a deploy v T+1-3 dny."* | Toto je **first thing reader sees** v handoff dokumentu. Současný text doslova říká *„prototype → spec → re-implement"*, což uživatel zakazuje. |
| 2 | `07-handoff-do-vyvoje.md:9-11` | *„**Prototyp není produkt.** Default kontrakt v Charteru je **throw-away pattern**: prototyp slouží k alignmentu a falsifikaci variant, po Session 2 se **zahazuje a produkční implementace startuje** na paved-road template"* | *„**Winner varianta = produkt.** Default kontrakt v Charteru je **variant pruning**: 3 varianty postavené v Session 1 jsou production-grade kód v sandboxu. Session 2 vybere winner; non-winning varianty se zahazují, winner pokračuje přes Promote-to-prod gate. **Žádná re-implementace, paved-road template byl použit od minuty 0**."* | Vysvětluje koherentně, proč je tam Promote-to-prod gate (winner) i throw-away (2 of 3 variants). |
| 3 | `01-filozofie-a-kdy-pouzit.md:147` | *„Pflanzer **končí handoff packagem, ne launchem**"* | *„Pflanzer **končí merged PR + deploy do staging/prod**, ne launch communications (marketing copy a launch readiness jsou samostatná aktivita)."* | Soft "Pflanzer ends at handoff" je classic spec-handoff framing. Reframe: Pflanzer **doručí kód**, ale neřeší marketing launch. |
| 4 | `04-session-1.md:13-14` | *„Session **neproduktivuje finální feature** — produkuje **alignovaný shortlist**"* | *„Session 1 produkuje **1-3 production-grade verze feature** v sandbox URL, plus alignovaný shortlist preference matrix. Final feature = winner po Session 2."* | L13 je hard "session = alignment, not feature" claim — přímo protiřečí *„hotový produkt"*. |
| 5 | `04-session-1.md:3-4,9` (status + cíl) | *„1–3 funkční **mockupy**"* | *„1–3 funkční **production-grade weby** (Vite + React + TS + ESLint, gate score ≥ 80/100), nasaditelné z prvního commitu"* | Slovo *„mockupy"* x 80 napříč repem signaluje throw-away. *„Web"* / *„aplikace"* / *„prod-grade build"* je rigorous. |
| 6 | `06-session-2.md:155-187` (Handoff package GO list) | 18-bod list spec/policy/checklist artefaktů (Scoped epic, PRD-lite, Gherkin, OpenAPI, Dependency Map, P2P, Privacy, Measurement plan, …) | Rozdělit na: **(a) Production deliverables**: merged PR with winning code, deployment manifest, feature flag config, SLO baseline live. **(b) Audit deliverables**: decision log, ADR drafts, DPIA, AI Act Fáze C, audit trail. **(a) je shippable, (b) je governance evidence.** | Současný list = 18 papírových artefaktů. Reader = *„kde je kód?"*. Reformulovat na *„shippable kód + audit evidence"* model. |
| 7 | `00-tldr.md:31, 45` | *„klikací prototyp v sandbox VPC"* / *„1–3 anotované klikací prototypy"* | *„1-3 production-grade weby deployované do sandbox VPC (winner mergne do target repo v Session 2)"* | TLDR je first impression. *„Klikací prototyp"* = spec-handoff mental model. *„Production-grade web"* = product mental model. |
| 8 | `method-charter.md:42-44, 62-63` (XYZ + Primary metric) | *„zkrátí čas od „nápad" k „**handoff package**" o ≥ 50 %"* + *„Time-to-handoff = od Charter timestamp do **first commit s `#handoff` tag**"* | *„zkrátí čas od „nápad" k **„merged PR v target repo + first prod deploy"** o ≥ 50 %"* + *„Time-to-shipped-feature = od Charter timestamp do **first commit on main branch v target repo, deployed at ≥1% rollout**"* | XYZ hypotéza je core method-level claim. Pokud merí time-to-handoff, optimalizuje spec velocity, ne product velocity. Misalignment s buyer expectation. |
| 9 | `03-pre-session-priprava.md:164` (True Cost Worksheet) | *„FE / Vibe-coding lead … Handoff: **1.0 (extract / hardening, viz Sprint 2)**"* | *„FE / Vibe-coding lead … Handoff: **0.5 (PR finalization, edge-case fix; production-grade kvalita byla zachována v Session 1 přes Vite + ESLint + Vitest gates)**"* | *„Extract / hardening / Sprint 2"* = explicit doznání, že prototyp NE-je prod-ready. To je load-bearing line v cost model. |
| 10 | `02-role-catalog.md:74-78` (BE / API lead output) | *„**Draft** OpenAPI 3.1 per varianta, breaking-change registr, 3–5 ADR **drafts**, contract test **skeleton** (Pact / Schemathesis), **migration plan stub**"* | *„**Finalizovaný** OpenAPI 3.1 winning varianty (Spectral clean, examples, RFC 7807 errors), implementovaný v target repo s contract tests passing (Pact), migration plan s rollback procedure"* | Slovní pole *„draft / skeleton / stub"* napříč BE lead outputs = role expect, že někdo jiný (jiný BE engineer post-handoff) to dotáhne. Uživatel říká: žádný post-handoff dev work na specifikaci. |

---

## Glossary recommendation

**KRITICKY CHYBÍ** napříč repem — termíny *„artefakt"*, *„prototyp"*, *„handoff
package"*, *„production-ready"*, *„funkční mockup"* nejsou nikde definované.
Každý dokument je používá s mírně jiným významem. Doporučuji vytvořit
`docs/methodology/glossary.md`:

### Navržený glossary (~12 termínů):

```
artefakt
  Cokoli, co Pflanzer cyklus produkuje. Spadají sem 3 kategorie:
  1. Shippable artifacts — kód, PR, deploy manifest, feature flag config.
  2. Audit artifacts — decision log, ADR, DPIA, AI Act tier classification.
  3. Process artifacts — preference matrix, score matrix, parking lot.
  Slovo „artefakt" SAMO nestačí — vždy specifikuj kategorii.

prototyp [DEPRECATED v0.4]
  V Pflanzer v0.3 byl tento termín použit pro *„throw-away klikatelný build
  v sandboxu"*. V v0.4 NAHRADIT termíny:
  - „varianta" = 1 z 3 souběžně postavených verzí (Session 1 output)
  - „winner" = varianta vybraná v Session 2 (default deploy target)
  - „discovery build" = pouze pokud Charter má `release_intent: false`

handoff package
  Sada audit artifacts (kategorie 2) doprovázející winner deploy. **NENÍ
  to spec pro dev tým.** Dev tým byl v session od minuty 0; handoff package
  slouží compliance / governance (DORA 7-letá retence, AI Act čl. 14 atd.),
  ne re-implementaci.

production-ready
  Kód v target repo, který prošel:
  - quality gate score ≥ 80/100 (per `/pflanzer-session-3` audit)
  - Vite + ESLint + Vitest CI passing
  - Promote-to-prod gate (16 položek per `07-handoff-do-vyvoje.md` L190+)
  - blind external EM panel acceptance ≥ 60/100
  Session 1 buildy jsou production-ready v dimenzi „kód kvalita", ale ne
  v dimenzi „governance sign-off" (ten se dotahuje v Session 2 / handoff).

shippable
  Production-ready AND signed off across all required dimensions
  (Security, Legal, EM, A11y). Možno deploy z `main` po feature flag rollout.

winner varianta
  Output Session 2 Decider's call. Default = mergne do target repo + deploy
  feature flag at 1%.

throw-away [REFRAMED v0.4]
  V v0.3 byl default kontrakt v Charteru. V v0.4 znamená:
  - „variant pruning": 2 ze 3 variant se zahazují v Session 2 (winner zůstává)
  - "no release intent": opt-in pro discovery-only pilots
  NE-znamená: „celý prototyp se zahodí a začne se znovu" (to byl v0.3 default,
  v0.4 deprecated)

evolve [REFRAMED v0.4]
  V v0.3 byl opt-in s 5-podpisovým gateway. V v0.4 = **default** pro
  pilots s `release_intent: true` v Charteru. Production-grade quality
  gates jsou aktivní od minuty 0 (paved-road template, Vite + ESLint,
  contract-first BE, A11y axe-core).

Promote-to-prod gate
  16-položkový checklist před prvním deployem winner varianty (per
  `07-handoff-do-vyvoje.md` L190+). Aktivuje se **v T+1-2 dny po Session 2**,
  ne v separátním post-Pflanzer SDLC.

Session 3 [v0.4 explicit]
  „Production hardening" session (`/pflanzer-session-3` slash command per
  `00-lean-pflanzer.md` L46). 1-2 dny dev work: extract winner kódu z
  sandboxu do target repo, projet 7 quality gates, vrátit production-ready
  verdikt. **POZOR:** existence Session 3 ukazuje, že Session 1+2 NE-jsou
  fully shippable per se. v0.4 musí jasně říct, jestli:
  (a) Session 3 je standard step (tj. „hotový produkt" = po Session 3, ne
      po Session 2);
  (b) Session 3 je optional gate jen pro audit-grade profile.

prototype hub
  V v0.3 byl deploy target Session 1 variant pro stakeholder feedback během
  mezi-sessions. V v0.4 doporučuji **přejmenovat na „variant hub"** nebo
  „candidate hub" — slovo „prototype" v názvu signalizuje throw-away.

handoff specifikace [TERM, KTERÝ V REPU NESMÍ EXISTOVAT]
  Anti-pattern. Pokud někde čteš tento termín, je to bug. Per uživatelská
  korekce: žádná spec se dev týmu nedává, dev byl v room od minuty 0.
```

---

## Risk audit — kde inconsistency → buyer confusion → conversion loss

Buyer journey simulace:

1. **Manažer čte `00-tldr.md`** (3 minuty, management 1-pager).
   → Vidí: *„AI generuje 1–3 mockupy"*, *„handoff package: scoped epic,
   akceptační kritéria, P2P checklist"*.
   → Mental model: *„Workshop produkuje spec, naši dev to potom implementují."*
   → Reakce: *„Zajímavé, ale nechci spec za $X, mám už specifikací plný
   Confluence."*
   → **Conversion lost**.

2. **PM/EM čte `07-handoff-do-vyvoje.md`** (15 minut).
   → Vidí explicit: *„Výstupem Session 2 není „kód", ale podepsaný handoff
   package, který tým vývoje může vzít a postavit z něj produkt"*.
   → Mental model: *„OK, tohle je předpřipravená specka. Velocity gain
   ~30 % ve fázi specifikace. Reálná velocity gain v fázi dev = 0."*
   → Reakce: *„Šetří mi week of specifikace, ale ne 4 měsíce dev. Pflanzer
   = $5k workshop, ne $100k value."*
   → **Pricing power lost**.

3. **CFO/buyer ekonomického modelu** čte `method-charter.md` XYZ hypotézu.
   → Vidí: *„zkrátí čas od „nápad" k „handoff package" o ≥ 50 %"*.
   → Mental model: *„Šetří mi spec time, ale ne implementation time. Total
   project time = spec (15 %) + implementation (85 %). 50 % saving v 15 %
   = 7.5 % project speed. Pro to nezaplatím."*
   → **Economic model collapses**.

4. **Developer reading `04-session-1.md`**:
   → Vidí: *„Session neproduktivuje finální feature"* + *„AI generuje mockupy"*.
   → Reakce: *„Takže já v sessionu jen review-uju mockup, a pak ho implementuju
   znova v sprintu? Proč tam mám sedět 6 hodin?"*
   → **Developer disengagement** v Session 1 → low quality alignment.

5. **Security/Legal čte `05-mezi-sessions.md`**:
   → Vidí: *„prototype hub, sandbox URL, 24h TTL, žádný route do prod sítě"*.
   → Reakce: *„OK, je to throw-away, nemusím to audituvat tak detailně."*
   → Quality of security review degraded **assuming throw-away**.

**Aggregate risk:**
- Manager: conversion loss
- PM/EM: pricing power loss (low willingness-to-pay)
- CFO: economic model rejection
- Developer: disengagement → low alignment
- Security/Legal: under-rigor (assuming throw-away)

**Net effect:** Pflanzer je **prodán** jako *„workshop methodology"* a **placen**
jako *„workshop methodology"* — i když uživatel **chtěl** prodat jako
*„AI development methodology"* / *„production code factory"*. To je **the gap**.

---

## Honest reading — kdy je throw-away SPRÁVNĚ?

Nutno říct fair: throw-away **má smysl** v některých kontextech, a to repo
tomu věnuje místo (ADR-0005, edge-case #8, LI-5). Konkrétně:

- **Discovery-only piloty** (no release intent, just *„chceme vidět, jestli
  to dává smysl"*). Buyer-research-style, kde cíl je learning, ne deployment.
- **Audit-grade profile s L3+ daty / AI Act High-risk**, kde prototype v sandbox
  s real prod-grade architektura review JE správné — *„promote-to-prod gate
  = formal review point"*, dokud není 100 % governance signed-off, kód
  technicky NEMÁ být v prod.

Pro tyto 2 use cases je current dokumentace **přesně správně**. Problém je,
že tyto use cases jsou **menšina** (~20 % per `00-lean-pflanzer.md` claim
*„80 % use casů = default profile"*), ale slovník celého repa je **dimenzovaný
na ně**. Resulting: 80 % uživatelů čte dokumentaci napsanou pro 20 % use case.

**Doporučení:** explicitně rozdělit slovník per profil.
- **Lean / Default profil dokumenty** (00-lean-pflanzer, 04-session-1-lean-variant,
  06-session-2-lean-variant, 07-handoff-lean-variant) — **product language**:
  *„production-grade weby"*, *„winner varianta mergne"*, *„T+1 deploy"*.
- **Audit-grade profil dokumenty** (current 04/05/06/07 zachovat) —
  **prototype language**: *„throw-away klikací prototyp"*, *„handoff package
  jako spec pro post-Pflanzer SDLC"*.

To je **honest** a **technicky správné** rozdělení. Lean profil pak může
upřímně tvrdit *„hotový produkt"* a audit-grade profil pak může upřímně
tvrdit *„prototype-driven alignment + downstream SDLC"*.

---

## Akční doporučení P0 (rank-ordered)

1. **`07-handoff-do-vyvoje.md`** complete rewrite — celá filozofie (L1-30)
   reframe na product-handoff, ne spec-handoff. Top single P0 item.
2. **`00-tldr.md`** — replace *„mockupy"* / *„klikací prototypy"* za
   *„production-grade weby"*. Manager 1-pager musí signalizovat product.
3. **`method-charter.md`** XYZ hypotéza — switch metric z `time-to-handoff-package`
   na `time-to-merged-PR + first prod deploy`. Strukturální fix metric design.
4. **ADR-0005 amendment** — explicit re-framing per Option A (throw-away =
   variant pruning, ne *„rewrite po session 2"*). Bez toho je všechno ostatní
   inkonzistentní s ADR.
5. **`04-session-1.md` L13** *„neproduktivuje finální feature"* — hard fix.
   Lean profil musí říct: Session 1 = 3 production-grade verze feature,
   ne 3 alignment mockupy.
6. **`02-role-catalog.md`** FE/BE leads sekce — `draft/skeleton/stub` slovník
   nahradit za *„finalizovaný / production-grade / implementovaný"*.
7. **Vytvořit `glossary.md`** per draft výše, link ze všech ostatních souborů
   na první výskyt klíčového termínu.
8. **`08-edge-cases-a-rizika.md` #8** *„Prototyp shipnut do prod"* — reframe
   na *„Winner deploy bez quality gate sign-off"*, ne *„prototype escape"*.
9. **`leading-indicators.md` LI-5** — refit na lean profile: *„Production deploy
   without Promote-to-prod gate completion"*, ne *„throwaway slip"*.
10. **`03-pre-session-priprava.md` True Cost Worksheet L164** — remove *„extract
    / hardening, viz Sprint 2"*, replace za *„PR finalization 0.5 PD; production-
    grade kvalita zachována v Session 1"*.

---

## Závěr

Pflanzer dokumentace má **systematický inconsistency mezi claim a slovníkem**.
Claim (`00-lean-pflanzer.md` + `09-srovnani` table): *„14d → production code"*.
Slovník (rest of repo): *„klikací prototyp → handoff package → re-implementace"*.

**Root cause:** ADR-0005 throw-away default je hlubinný axiom celé v0.3
dokumentace. **Bez jeho re-framingu** nelze unified product positioning.

**Recommended path:**

1. **Amend ADR-0005** (Option A re-framing) — `decisions/0005-throwaway-vs-evolve-prototype.md`
   reframe na *„variant pruning"*.
2. **Vytvořit `glossary.md`** — single source of truth pro vocabulary.
3. **Rewrite `07-handoff-do-vyvoje.md` first** — biggest single contradiction.
4. **Sweep ostatní 6 souborů** pro slovní pole *„prototyp / mockup / handoff
   package = spec"* → replace per glossary.
5. **`method-charter.md`** metric switch — strukturální zarovnání metrik
   k *„hotový produkt"* hypotéze.

Effort estimate: ~1.5-2 PD content editing + 0.5 PD glossary + 0.5 PD ADR-0005
amendment. **Total ~3 PD pro full positioning fix.** Bez tohoto fixu je
*„Pflanzerova metoda = hotový produkt"* prodej **mismatch** vůči reálné
dokumentaci, kterou buyer čte před nákupem.

---

*Konec auditu.*
