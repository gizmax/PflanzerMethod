# Pflanzer Method — Marketing Site Copy Audit (perspektiva senior B2B SaaS copywritera)

> **Auditor:** Senior B2B SaaS copywriter, 12+ let praxe (CS/EN tech & consulting).
> **Filter:** „Vyhodil bych to z landing page, kdybych pro to platil?"
> **Předmět:** `website/index.html` (Pflanzer Method v0.3, bilingual CS/EN).
> **Reader persona pro každý úsudek:** *45-letý VP Engineering v evropské bance,
> kterému CEO řekla „dostaňte AI do firmy do Q1 2027". Má 12 minut a tři další
> taby otevřené.*

---

## TL;DR verdikt

**CS skóre: 6/10. EN skóre: 5/10.**

Stránka má **vážné řemeslo na typografii a struktuře** (Fraunces + JetBrains Mono,
botanical SVG, receipty v e-shop sekci — to jsou copywriter-friendly building
blocks). Ale **copy samotná osciluje mezi dvěma extrémy**: hero a manifesto
mají osobnost a tah, zatímco USPs (sekce 02) je **technical landing page pro
AI Center of Excellence governance lead** přilepená na webu, který se v hero
prezentuje jako řemeslný manuál. Tonalitní whiplash je největší issue.

**Biggest issue:** sekce 02 (USPs) zní jako vstupní stránka B2B SaaS pro
governance tooling — `Organizační moat`, `Regulatorní moat`, `Decision moat`,
`Governance moat`, `Operational moat` jsou interní competitive-research kategorie,
ne reader-facing benefity. **Pět "moatů" za sebou je copy smell.** Reader,
který sem dorazil z LinkedInu, neví co je „LDJ dot voting", „AI Act čl. 14",
„BMAD", „Discovery Debt Detector" — a metoda mu to nevysvětluje, předpokládá,
že to ví. Současně chybí jediný reader-benefit gradient: *„za 14 dní místo
9 měsíců"* je v hero, ale od sekce 02 dolů metoda mluví **o sobě**, ne **k
čtenáři**.

**Druhý největší issue:** EN verze čte na 70 % jako přímý překlad CS. Idiomy
jako *„vajbili"*, *„pinkat"*, *„rozhýbat"* mají v CS náboj (a brand voice).
EN ekvivalenty (*vibing*, *pings*) buď nefungují, nebo zní jako technologičtí
22-letí (≠ cílová persona). EN copy potřebuje **standalone přepis**, ne lokalizaci.

**Třetí největší issue:** 3 CTAs (1-pager / GitHub / Mluvit s autorem)
směřují **všechny do otevřeného loopu**. Žádný z nich není committal s
nízkou friction. Chybí *„Stáhnout PDF case study (e-shop)"* — což je
classic 45-letý-VP-Eng download path.

---

## Per-section deep dive

### A. Frame top + bottom (mikrokopy)

**Co tam je:**
- Top: `Pflanzer Method · v0.3` | `Manuál pro sázení AI do rigidních procesů` /
  `Manual for planting AI in rigid processes` | `Est. 2026` + lang switch
- Bottom: `↳ Pflanzer Method` | `Manuál · ne manifesto` / `Manual · not manifesto` |
  `↑ nahoru` / `↑ top`

**1. Clarity & Friction:** `Manuál · ne manifesto` je **chytrá self-aware
mikrokopie**, která drží brand tone. Funguje v CS i EN. ✅

**2. Tone consistency:** `Est. 2026` je tongue-in-cheek (jako kdyby šlo o
craft-beer destilerii) — to **sedí** k Fraunces typografii a paper-grain
texture. ✅

**3. Benefit visibility:** N/A na frame mikrokopiích.

**4. Conversion mechanics:** Lang switch je v top-frame — ✅ dobré umístění,
ale `CS · EN` separator je drobný, na mobilu se ztratí (frame se zmenšuje na
9px font-size). Doporučení: na mobile zviditelnit lang toggle.

**Verdikt:** Lze nechat. Bottom „Manuál · ne manifesto" je actually jeden z
nejsilnějších taglinů na celé stránce.

**Návrh: alternativa pro EN frame-top** (current zní jako uvozující věta
v abstract akademického paperu):

```diff
- Manual for planting AI in rigid processes
+ A manual for planting AI inside rigid orgs
```

(rigid processes → rigid orgs: korporát čte líp, „processes" zní jako PRINCE2
dokument)

---

### B. Hero — wordmark, meta grid, punchmark tagline, 2 CTAs, scroll-cue

**Co tam je:**
- Meta grid: `Subjekt: Korporát 5–5000+ FTE` | `Vstup: Nápad bez plánu` |
  `Výstup: Kód v produkci` | `Délka cyklu: ~14 dní calendar`
- Wordmark: `Pflanzer / Method.`
- H-sub tagline (CS): *„Sázíme AI do korporátních procesů, kde sériový handoff
  zabíjí měsíce. 6 lidí, 2 sezení, většina kódu jde rovnou do produkce."*
- H-sub tagline (EN): *„We plant AI into corporate processes where serial
  handoff kills months. 6 people, 2 sessions, most code ships straight to
  production."*
- 2 CTAs: `Začít s 1-pagerem ↗` | `GitHub ↗`
- Scroll-cue: `Čti dál ↓ — 00 — 04`

#### 1. Clarity & Friction

Meta grid (Subjekt/Vstup/Výstup/Délka cyklu) je **strong opening move** —
v 5 vteřinách reader ví o co jde. ✅

ALE: `~14 dní calendar` je **CS-isms vůči EN reading**. „calendar days"
v hlavě engineering managera evokuje sprint-vs-business-day disclaimer.
Lepší: `2 sessions + 1 týden async` (informativnější a netřeba disclaimer).

#### 2. Tone consistency

CS „Sázíme AI" — chytré, drží brand metafora. ✅
EN „We plant AI" — funguje, ale `serial handoff kills months` zní jako
direct překlad. Native by řekl *„drags on for months"* nebo *„burns months
in handoffs"*. „kills months" je doslovný překlad ze CS, kde má sloveso
„zabíjí" jiný idiom-range.

#### 3. Benefit visibility

**6 lidí · 2 sezení · kód do produkce** — tohle je copy zlato. Tři čísla,
tři benefity, žádný buzzword. ✅✅

#### 4. Conversion mechanics

CTAs problém: **dvě CTAs ve stejné vizuální váze (`btn` + `btn.ghost`),
oba vedoucí na GitHub-grade artefakt**. Pro VP Eng je primární CTA
*„Začít s 1-pagerem"* moc kommitmentové, jelikož reader ještě neví, co je
metoda. „Get the 1-pager" + „Read the method" by dávalo dva různé intent
gradienty.

**Důležitější chyba:** primární CTA vede na `#zacni` — to je in-page anchor,
ne download. Reader si bude chtít stáhnout PDF, ne scrollovat dolů. To je
**falešné CTA**.

#### Diff (CS):
```diff
- Sázíme AI do korporátních procesů, kde sériový handoff zabíjí měsíce.
- 6 lidí, 2 sezení, většina kódu jde rovnou do produkce.
+ Sázíme AI do korporátu. 6 lidí, 2 sezení, kód v produkci za 14 dní —
+ ne za 9 měsíců sériového handoffu.
```
(Pevnější rytmus: short → long → kontrastní longer. Benefit „14 dní vs.
9 měsíců" už v tagline, ne až v meta gridu nahoře.)

#### Diff (EN):
```diff
- We plant AI into corporate processes where serial handoff kills months.
- 6 people, 2 sessions, most code ships straight to production.
+ We plant AI inside the corporate. 6 people, 2 sessions, code in production
+ in 14 days — instead of 9 months of serial handoffs.
```

#### Diff (CTAs):
```diff
- [Začít s 1-pagerem →]   [GitHub ↗]
+ [Stáhnout 1-pager (PDF) ↓]   [Číst metodu ↓]   [github.com/... ↗]
```
(Tři tier: download = nízká friction commit, číst = engagement, GitHub =
expert track. Současné dvě tlačítka mají oba stejný intent gradient.)

**Verdikt hero:** silná struktura, slabší tagline EN, chybí PDF-grade
primární CTA. **6/10 CS · 5/10 EN.**

---

### C. 00 Manifesto

**Co tam je:**
- H2 (CS): *„Korporátní handoff hell. Tohle vznikla, aby ho prolomila."*
- H2 (EN): *„Corporate handoff hell. This was made to break it."*
- 5 paragrafů body
- Pull quote: *„Nejde o rychlejší výrobu mockupů. Jde o cross-funkční
  alignment na funkčním artefaktu, ne na slidu."*
- Etymology paragraf (`Pflanzer = německy „pěstitel, sazeč"`)
- 4 stat cards (6–9, 14, 10×, 6)

#### 1. Clarity & Friction

H2 (CS) má **gramatickou chybu**: *„Tohle vznikla"* — pokud je subjekt
„metoda/věc", má být „Tohle vzniklo" nebo „Ta vznikla". `Tohle` (neutrum) →
`vzniklo`. **P0 fix.**

H2 (EN) `This was made to break it` — funguje, je idiomatičtější než CS.

První paragraf má **vysokou kognitivní zátěž**: 5 entit (`Zadavatel`,
`produkt`, `vývoj`, `security`, `legal`, `deploy team`) v jedné větě
přes 5 sub-clausí. To je v 5. vteřině reader už scrolluje. Buď zkrátit
na 3 entity, nebo přepsat na bullet.

`Pinká` v EN přeloženo jako `pings`. To zní jako Slack notification, ne
jako frustrace. Native by řekl `bounces it to`, `kicks it over to`,
nebo přímo `hands it off to`. „Pings" je doslovný překlad bez idiom carry.

#### 2. Tone consistency

CS *„Zadavatel pinká s produktem"* — má **drive a frustration**. Native CS
reader to slyší v intonaci. EN ekvivalent ztratil 80 % toho náboje.

CS *„kontext se ztratí v emailech"* — strong.
EN *„context gets lost in emails"* — strong. ✅

CS *„rozhodnutí se dělají na PowerPointu, ne na funkčním artefaktu"* —
silná pointa, drží přes oba jazyky. ✅

CS *„dáme jim 3 hodiny společného vajbování s AI"* — „vajbování" je
přesně ten brand voice token (sebevědomý, mechanický, ale lidský). ✅
EN *„give them 3 hours of vibe-coding with AI"* — `vibe-coding` je technical
term v EN, OK, ale ztratil jsme tu „spojený" konotaci (`společného`).
Lepší: *„give them 3 hours together vibe-coding with AI"*.

#### 3. Benefit visibility

Manifesto **je o metodě**, ne o čtenáři. To je v 95 % případů OK pro
manifesto sekci, ALE: chybí jediná věta *„Co tě to ušetří"*. Reader si
musí benefity dopočítat ze stat-cards (10× zrychlení).

#### 4. Conversion mechanics

Stat-cards (sticky right column) jsou **chytré** — slouží jako always-visible
benefit reminder. ✅ Sticky position drží reader anchored on the numbers
when scrolling through paragraphs.

ALE: `~10× zrychlení v cyklu od nápadu k prod kódu` — claim s rizikem.
Bez asterisku / methodology disclaimeru je to **statistical-credibility
debt**. Reader z banky/auditovaného prostředí to bude muset later vyřvat.
Doporučení: přidat `*based on e-shop pilot, default profile` jako 9px
poznámku.

#### Diff H2 (CS):
```diff
- Korporátní handoff hell. Tohle vznikla, aby ho prolomila.
+ Korporátní handoff hell. Metoda, která ho prolomí.
```
(Opravuje gramatiku + dropuje pasivní „Tohle vznikla, aby" konstrukci, která
v 2026 zní starinkavě.)

#### Diff první paragraf (CS):
```diff
- V korporátu cesta od nápadu k funkční fíčuře typicky trvá 6 až 9 měsíců.
- Zadavatel pinká s produktem, produkt s vývojem, vývoj se security,
- security s legal, legal s deploy týmem. Mezitím nápad zestárne, kontext
- se ztratí v emailech a rozhodnutí se dělají na PowerPointu, ne na
- funkčním artefaktu.
+ V korporátu trvá cesta od nápadu k funkční fíčuře 6 až 9 měsíců. Nápad
+ pinká mezi produktem, vývojem, security a legal. Kontext se ztrácí v
+ emailech. Rozhodnutí se dělají na PowerPointu — ne na funkčním artefaktu.
```
(Zkráceno z 67 → 41 slov. Rytmus: long → short → short → punch line.
Stejné info, dvakrát víc tahu.)

#### Diff první paragraf (EN):
```diff
- In a corporate, the path from an idea to a working feature typically takes
- 6 to 9 months. The sponsor pings product, product pings engineering,
- engineering pings security, security pings legal, legal pings the deploy
- team. Meanwhile the idea ages, context gets lost in emails, and decisions
- are made on PowerPoint, not on a working artifact.
+ Inside a corporate, an idea takes 6 to 9 months to become a working feature.
+ It bounces between product, engineering, security, and legal. Context
+ dies in email threads. Decisions get made on PowerPoint slides — not on
+ working artifacts.
```
(`pings` × 5 raised it to comedy level; `bounces` carries the frustration.
`context dies` > `context gets lost`. `working artifact` → kept singular for
contrast with „PowerPoint slides".)

#### Diff etymology paragraf (EN):
```diff
- Pflanzer = German for „planter, one who sows". The method doesn't force AI
- into companies as a transformation. **It plants.** Pilot by pilot, team by
- team. What takes root, grows. What doesn't, everyone sees right away —
- not in a year.
+ Pflanzer is German for „planter". The method doesn't force AI into companies
+ as a transformation. **It plants it.** Pilot by pilot, team by team. What
+ takes root, grows. What doesn't, you see it that week — not next year.
```
(„one who sows" je over-translation; „planter" stačí. „you see it that week"
je punchier než „everyone sees right away" — specifický timeframe víc bije.)

**Verdikt manifesto:** koncepčně silné, ale 1. paragraf je tldr-bait, H2 má
gramatickou chybu, EN ztrácí osobnost. Po opravách → **7/10 CS · 6/10 EN.**

---

### D. 01 Botanical flow

**Co tam je:**
- H2 (CS): *„Jak metoda roste."* / EN: *„How the method grows."*
- Fig caption: `Fig. 01 — Pflanzer cyklus, default profil`
- 5 stage cards (Day 0–14, name, description)

#### 1. Clarity & Friction

Stage names — CS používá *„Sazba"* (Day 0). Pro non-Czech reader nebo
pro někoho, kdo není familiar s gardening metaphor, je to neuhodatelné.
EN přeloženo jako *„Sowing"* — drží metaphor.

`Den 0 · Sazba` — nejsilnější fáze copy-wise: *„Problém v jedné větě,
success threshold ve dvou."* — to je tagline-grade věta. ✅

`Den 5 · Session 1 · vibe` — vibe jako label name? Působí to **trochu
nedotaženě**. Pro VP Eng z banky „vibe" zní vibe-coder-22-year-old.
Lepší by bylo `Session 1 · prototyping` nebo `Session 1 · build`.

`Den 10 · Session 2 · rozhodnutí` (decision) — OK, jasné.

`Den 11–14 · Ship to prod` — ✅ silné, action-oriented.

**Friction issue:** Day 6–9 description: *„Stakeholdeři klikají, builder
lead aplikuje feedback. Cross-fn alignment roste, ne degraduje."* — věta
„Cross-fn alignment roste, ne degraduje" zní jako **post-meeting Slack
zpráva**. Není to copy, je to interní pozorování. Vyhodit.

#### 2. Tone consistency

CS používá *„Kávový meeting"* — milé, držící brand. EN *„Coffee meeting"*
funguje. ✅

`silent voting, Decider shortlist` — Decider zde poprvé poprvé použito
bez vysvětlení. Reader nezná Design Sprint terminologii → friction.

#### 3. Benefit visibility

**Stage flow říká „co se děje", ne „co tím získáš".** Každá stage by
mohla končit jedním slovem-benefit (např. `Sowing → alignment v 60 min`,
`Session 1 → 3 prototypy v 3h`).

#### 4. Conversion mechanics

Žádné CTA v této sekci → OK, je to expository.

#### Diff Day 5 stage (CS):
```diff
- Session 1 · vibe
- In-room vibe-coding. 3 paralelní weby v Bolt / v0 / Lovable / Claude Code.
- Silent voting, Decider shortlist.
+ Session 1 · build
+ 3 paralelní weby ve 3 hodinách. Bolt / v0 / Lovable / Claude Code.
+ Tichý voting, vyber 2.
```

#### Diff Day 6–9 (CS):
```diff
- Mezi-session
- Stakeholdeři klikají, builder lead aplikuje feedback. Cross-fn alignment
- roste, ne degraduje.
+ Async týden
+ Stakeholdeři klikají, builder lead aplikuje feedback. Aliment se v týdnu
+ nerozpadne — ostře proti tomu, co dělá Design Sprint.
```

#### Diff Day 6–9 (EN):
```diff
- Between sessions
- Stakeholders click, builder lead applies feedback. Cross-fn alignment
- grows, doesn't degrade.
+ Async week
+ Stakeholders click, builder lead applies feedback. Alignment holds — the
+ opposite of what happens to a Design Sprint after Friday.
```
(„the opposite of what happens to a Design Sprint after Friday" = competitive
swipe + specific. „Cross-fn alignment grows, doesn't degrade" = corporate
governance speak.)

**Verdikt flow:** SVG je crafty, copy je mid. Po opravách → **6/10 CS · 6/10 EN.**

---

### E. 02 USPs (5 pillars)

**Toto je nejvíc problematická sekce z celého webu.** Zaslouží si rozsáhlé
ošetření.

**Co tam je:**
- H2 (CS): *„Pět věcí, které nikdo jiný nedělá."* / EN: *„Five things no
  one else does."*
- Intro paragraph (statistical-rigor tón, jmenuje AWS AI-DLC / McKinsey
  QuantumBlack / AJ&Smart)
- 5 USP rows, každý: numbered tag, h-sub heading + italic sub-h-sub,
  2 body paragraphs, tag chips
- „Co Pflanzer NENÍ" / „What Pflanzer is NOT" closer block

#### 1. Clarity & Friction — **fatal**

V 5 USP řádcích metoda používá tyto termy bez jediného vysvětlení:
- `RTE` (none here, ale jinde) ✅
- `AABG` (none)
- `DORA` (#02)
- `AI Act čl. 14` (#02)
- `BMAD` (#02)
- `Spec Kit/BMAD/Kiro` (#02)
- `AI-DLC` (#01, #04, #05)
- `LDJ dot voting` (#03)
- `Decider` (#03)
- `Likert` (#03)
- `HiPPO` (#03 anti-HiPPO chip)
- `Discovery Debt Detector` (#04)
- `Sandbox spec` (#04)
- `AI Act tier Fáze A` (#04)
- `Approved AI Tool list` (#04)
- `Thoughtworks "3-3-3"` (#05)
- `T+7/30/60/90 reinforcement` (#05)
- `Method Charter v0.3 (ADR-0011 default Sunset T+18 mo)` (#05)
- `Method Steward` (#03, ale tady)
- `QuantumBlack` (intro)

Tohle je **20+ uncuratovaných expert termů**. Pro 45-letého VP Eng,
který CEO řekla „dostaňte AI do firmy", je tohle reading-stop. Nevolá
to po googleningu — volá to po `tab close`.

#### 2. Tone consistency

Intro paragraf začíná: *„Competitive research May 2026 (3 nezávislí experti)
potvrdil..."* — to není marketing copy. **To je executive summary
researchového dokumentu na landing page**. Reader nepřišel číst metodiku
research processu. Vyhodit, nebo přesunout do `/research`.

Pull-quote tón ve většině řádků zní jako recruiter LinkedIn post:
*„Pflanzer audit-grade profil dává Security, Legal/DPO, A11y, UX writer
a CS proxy do primary session"* — tohle je **vstupní text do RFP**, ne
marketing copy.

#### 3. Benefit visibility

**Zero reader benefit.** Pět „moatů" za sebou. „Moat" je investor termín
(Buffett). Reader z banky to nečte jako benefit pro sebe, čte to jako
self-aggrandizement pitch deck.

Co reader chce slyšet po headlinu „Five things no one else does":
*„Co z toho má?"*

Aktuální copy:
> Pflanzer audit-grade profil dává Security, Legal/DPO, A11y, UX writer
> a CS proxy do primary session.

Reader benefit verze:
> Security tě nezablokuje v týdnu 4. Sedí v místnosti od minuty 0.

#### 4. Conversion mechanics

Žádné CTA v této sekci. Po 5 USP textech v 2000+ slov má reader buď
spadnout do „CTA next" momentu, nebo opustit. Aktuální copy ho udrží
asi 30 sekund max.

#### „Co Pflanzer NENÍ" — analýza

*„Pflanzer není „yet another workshop methodology" — to je hřbitov, ze
kterého většina metod nevyšla. Pflanzer je operating-cadence layer pro
AI Center of Excellence: opakovatelná, certifikovatelná, procurement-ready
pilot fixture v mezeře mezi $1M+ McKinsey transformations a $0 hackathon
frameworks. Tu mezeru zatím nikdo nezaplnil."*

Tohle je actually **nejsilnější věta v sekci 02**. Comp v cenách
($1M+ vs. $0) je konkretní, „graveyard" metafora drží přes oba jazyky.
**Tahle věta měla být H2 sekce, ne closer block.**

`operating-cadence layer pro AI Center of Excellence` — termín
„AI Center of Excellence" je v evropském bankovním kontextu **přesně
to slovo, které VP Eng hledá**. Tahle 1 věta dělá víc práce než celá
intro paragraf.

#### Diff intro paragraf (CS):
```diff
- Competitive research May 2026 (3 nezávislí experti) potvrdil: vibe-coding
- samotný už není Pflanzer differentiator (Lovable + Bolt + Cursor = 2026
- mainstream). Reálná protected pozice je 5 pilířů, které dohromady nikdo
- jiný v 2026 nedělá — ani AWS AI-DLC, ani McKinsey QuantumBlack, ani
- AJ&Smart Sprint 2.0.
+ Vibe-coding samotný už není diferenciátor — v 2026 to umí každý.
+ Diferenciátor je, jak ho dostat do banky tak, aby ho podepsala security,
+ legal i procurement. Tady je pět věcí, které nikdo jiný v 2026 nedělá.
```

#### Diff intro paragraf (EN):
```diff
- Competitive research May 2026 (3 independent experts) confirmed: vibe-coding
- alone is no longer Pflanzer's differentiator (Lovable + Bolt + Cursor = 2026
- mainstream). The real protected position is 5 pillars that, together, no
- one else does in 2026 — not AWS AI-DLC, not McKinsey QuantumBlack, not
- AJ&Smart Sprint 2.0.
+ Vibe-coding itself is no longer the moat — in 2026 everyone can do it.
+ The moat is shipping it inside a bank so that security, legal, and
+ procurement all sign off. Here are five things no one else does.
```

#### Diff USP #01 — body (CS):
```diff
- AWS AI-DLC „mob" = jen engineering. Design Sprint = jen produktový tým.
- Pflanzer audit-grade profil dává Security, Legal/DPO, A11y, UX writer
- a CS proxy do primary session.
-
- Late-stage veto eliminované. Security flag risk surface na minutě 240,
- ne v sprintu 4.
+ V AWS „mob mode" sedí jen vývojáři. V Design Sprintu jen produktový tým.
+ U Pflanzera sedí Security, Legal, DPO, a11y a UX writer od minuty 0 —
+ ve stejné místnosti, na stejném artefaktu.
+
+ Co to znamená: na security audit narazíš v hodině 4, ne v sprintu 4.
+ Žádný „v poslední fázi nám compliance řeknou, že to neprojde."
```

#### Diff USP #02 — body (CS):
```diff
- McKinsey i BCG dělají AI Act compliance jako custom deliverable v $1M+
- engagementu. Pflanzer ho má native v Charter template: decision log s
- human attribution, dvoufázový AI Act protokol (Fáze A/B/C), DORA-grade
- 7-letá retence audit logů.
-
- Externí validace: Martinelli paper 2026 kritizuje Spec Kit/BMAD/Kiro za
- chybějící stakeholder alignment + audit trail. Jeho critique pointy jsou
- doslova Pflanzer USPs.
+ McKinsey ti AI Act compliance dodá jako custom deliverable v engagementu
+ za $1M+. Pflanzer ho má zadarmo přibalený: každé rozhodnutí má
+ atribuci k člověku, audit log běží 7 let (DORA-grade), AI Act ti
+ klasifikuje riziko ještě před první session.
+
+ Když si tě regulátor zavolá za 14 měsíců na audit, máš co ukázat.
```
(Vyhozen Martinelli reference — to je interní validation argument, ne reader
selling point. Doplněn reader-facing benefit „když si tě regulátor zavolá".)

#### Diff USP #03 — heading + body (CS):

Heading current:
> „Líbí se mi" vs „commitnu" — Pflanzer to měří.

Heading current EN:
> „Like it" vs „commit" — Pflanzer measures the gap.

CS heading je punchy. EN heading je slabší — `Pflanzer measures the gap`
zní academicky. Native: *„Pflanzer pins it down"*.

Body současně:
> LDJ dot voting řeší „líbí se mi". DS Decider řeší binární „go/no-go".
> Pflanzer řeší hranici mezi nimi — 1-5 Likert s rationale field,
> hierarchie závaznosti Critical / Yellow / Score, AI-only feedback
> deflated 0.5/1.0.

Problémové termíny: `LDJ`, `DS Decider`, `1-5 Likert`, `rationale field`,
`hierarchie závaznosti Critical / Yellow / Score`, `AI-only feedback
deflated 0.5/1.0`. Tohle je 6 jargon termů v 2 větách.

```diff
- LDJ dot voting řeší „líbí se mi". DS Decider řeší binární „go/no-go".
- Pflanzer řeší hranici mezi nimi — 1-5 Likert s rationale field,
- hierarchie závaznosti Critical / Yellow / Score, AI-only feedback
- deflated 0.5/1.0.
-
- Workshop methodology expert confirmation: žádný direct competitor v 2026.
- 12-měsíční náskok.
+ Většina workshop metod měří „líbí se mi" — palečky, samolepky, dot voting.
+ Decider v Design Sprintu udělá binární „go/no-go". A pak týden po sprintu
+ ti člověk z compliance řekne, že se mu to vlastně nelíbí. Proto má Pflanzer
+ 1-5 stupnici s povinným důvodem („proč jsi dal 3, ne 5?") + binární
+ veto-právo pro 4 role: Security, Legal, A11y, Decider.
+
+ Žádný direct competitor v 2026 to nedělá.
```

#### Diff USP #04 — body (CS):

```diff
- Discovery Readiness Gate + Security & Data + Legal & Privacy + Platform Triage.
- Bez 4 podpisů Session 1 neodstartuje. Discovery Debt Detector, Sandbox spec,
- AI Act tier Fáze A, Approved AI Tool list.
-
- Žádný direct competitor nemá 48-72h async pre-read jako MUST gate.
- AI-DLC, Sprint 2.0, AJ&Smart startují bez explicit pre-flight discipline.
+ 48 hodin před Session 1 dostane každá ze 4 rolí (Discovery, Security,
+ Legal, Platform) krátký async check-list. Bez 4 podpisů Session 1
+ neodstartuje. Důvod: žádné „my jsme to nevěděli" v hodině 3 — protože
+ tu informaci si přečetli den předtím v posteli.
+
+ AWS AI-DLC, AJ&Smart Sprint 2.0 ani Thoughtworks tohle nemají.
```

#### Diff USP #05 — body (CS):

```diff
- AWS AI-DLC = continuous bolts (no async window). Thoughtworks „3-3-3" = 90 dní.
- Design Sprint = 5 dní non-stop (corporate stakeholder unavailable).
- Pflanzer = 2 sezení s 5-7d asyncem + T+7/30/60/90 reinforcement.
-
- Corporate stakeholder availability. Context retention pod 7 dní. Reinforcement
- kalibrace per Method Charter v0.3 (ADR-0011 default Sunset T+18 mo).
+ AWS AI-DLC běží non-stop bez async pauzy. Thoughtworks „3-3-3" trvá 90 dní.
+ Design Sprint chce 5 dní v kuse — což stakeholder z compliance v korporátu
+ nikdy nedá. Pflanzer rozsekne to: 2 × 3 hodiny, mezi tím týden.
+
+ Bonus: po Session 2 jsou checkpointy v T+7, T+30, T+60, T+90 dní. Pilot
+ se nepředá do vakua. Když po 6 měsících metoda nevykazuje hodnotu, sunset.
```
(Vyhozen `ADR-0011 default Sunset T+18 mo` — interní artefakt referencing,
reader to nemůže ověřit.)

#### Diff „Co Pflanzer NENÍ" — header rework (CS):

```diff
- Co Pflanzer NENÍ
- Pflanzer není „yet another workshop methodology" — to je hřbitov, ze
- kterého většina metod nevyšla. Pflanzer je operating-cadence layer pro
- AI Center of Excellence: opakovatelná, certifikovatelná, procurement-ready
- pilot fixture v mezeře mezi $1M+ McKinsey transformations a $0 hackathon
- frameworks. Tu mezeru zatím nikdo nezaplnil.
+ Co Pflanzer NENÍ (a co je)
+ NENÍ to další workshop metoda. Hřbitov těch je plný — Sprint 2.0, Lean
+ Startup workshops, Innovation Days, Design Thinking, „AI Adoption
+ Frameworks" od poradenské firmy XY.
+
+ Pflanzer JE operating layer pro tvoje AI Center of Excellence —
+ opakovatelný, certifikovatelný, procurement-ready. Cenově sedí mezi
+ McKinsey transformací za $1M+ a hackathonem za $0. Tu mezeru zatím
+ nikdo nezaplnil.
```

**Verdikt USPs:** **3/10 CS · 3/10 EN aktuálně**. Po reworku potenciál
na 7/10. Současný stav je executive summary research dokumentu, ne sales
copy. Tato sekce je gating factor pro celý web.

---

### F. 03 Field Notes (e-shop)

**Co tam je:**
- H2 (CS): *„Z terénu. e-shop · 2026."* / EN: *„From the field. e-shop · 2026."*
- Stamp: `Field Notes · Pilot P-001` | `e-commerce · ~7M MAU · CZ/SK/PL`
- Pull quote: *„Dali jsme dohromady 6 lidí. Tři hodiny vajbili..."*
- 2 body paragraphs
- 10 receipt rows (Účastníci, Setkání, ..., AI Act tier: limited)

#### 1. Clarity & Friction

✅ **Tato sekce je nejlepší na celé stránce.** Receipt format je geniální —
strukturovaný proof v stylu fyzické paragony. `2 × 3h`, `5 dní async`,
`3 prototyp`, `~14 dní` — to jsou benefit-by-numbers, které VP Eng
nasaje za 5 sekund.

ALE: `Method Steward: —`, `Compliance score: —`, `AI Act tier: limited`
— tři em-dashe na řádek za sebou působí jako *„tohle jsme ještě nedělali"*.
Lepší: vyhodit ty, co jsou prázdné, nebo dát `n/a (default profile)`.

#### 2. Tone consistency

CS pull quote *„vajbili"* — perfektní brand tone. ✅
EN pull quote *„vibing"* — translates OK, ale lehčí náboj. Native by
možná napsal *„three hours of vibe-coding"* nebo prostě *„three hours
of just shipping"*. „vibing" v EN konotuje party.

Body text je dobře pevný v obou jazycích.

#### 3. Benefit visibility

Receipt format = celá benefit visibility. Funguje.

ALE chybí jedna kritická informace: **kdo jsou stakeholdeři / role
z těch 6**? Reader chce vědět: byl tam právník? Byl tam security?
Tohle by mělo být v receiptech: `Roles: Product, Eng, Security, Legal,
UX, Sponsor`.

#### 4. Conversion mechanics

Žádné CTA → měla by být. e-shop case study je perfektní opportunity
pro „Read full case (PDF)" download.

#### Diff stamp (CS):
```diff
- Field Notes · Pilot P-001 | e-commerce · ~7M MAU · CZ/SK/PL
+ Field Notes · Pilot P-001 — e-shop | e-commerce · ~7M MAU · CZ/SK/PL
```
(`e-shop` v headeru, ne až v body — reader skenuje pull-quotes a receipts,
neoči-přečte „e-shop" z H2.)

#### Diff body P1 (CS):
```diff
- E-commerce platforma. Klasický rigidní workflow: zadavatel → produkt → UX →
- vývoj, jeden cyklus měsíce. Cíl pilotu: nasadit vibe-coding tak, aby cesta
- od první alignment session k produktivnímu kódu trvala týdny, ne měsíce.
+ E-commerce platforma, ~7M MAU. Rigidní workflow: zadavatel → produkt → UX →
+ vývoj, jeden cyklus = měsíce. Cíl: cestu od první alignment session k
+ produkčnímu kódu zkrátit na týdny.
```

#### Diff receipts — přidat role row:
```diff
  Účastníci         6
+ Role v místnosti  Sponsor · Product · Eng · UX · Security · CS proxy
  Setkání           2 × 3h
  Mezi-session      5 dní async
  ...
```

#### Diff body P2 (EN):
```diff
- While a classic Design Sprint produces a Figma in the same time that someone
- then re-implements over 2 more months, the Pflanzer cycle ends with code
- the lead developer merges in 1–2 days.
+ A classic Design Sprint hands you a Figma — and then someone re-implements
+ it over the next 2 months. The Pflanzer cycle hands you code the lead
+ developer merges in 1–2 days.
```
(Kratší, pevnější rytmus. Active voice „hands you" × 2.)

#### Přidat CTA pod field-notes:
```html
<a href="/case/eshop.pdf" class="btn ghost">
  <span class="lang-cs">Stáhnout celý case (PDF, 8 str.) ↓</span>
  <span class="lang-en">Download full case (PDF, 8 pages) ↓</span>
</a>
```

**Verdikt field notes:** strongest section. **8/10 CS · 7/10 EN.** Drobné
úpravy + 1 CTA → 9/10.

---

### G. 04 CTA

**Co tam je:**
- H2 (CS): *„Začni sázet."* / EN: *„Start planting."*
- Body: dva profily (Default, Audit-grade)
- 3 CTAs: `1-pager · Lean Pflanzer` | `Tool na GitHubu` | `Mluvit s autorem`
- „Proč teď" / „Why now" — 2 paragraphs

#### 1. Clarity & Friction

`Default (e-shop-style, ~80 % korporátních case-ů) ti stačí jeden 1-pager.`
— „case-ů" je gramaticky špatně v CS (sg. „case" pl. „cases", ne „case-ů").
**P0 fix.** Lepší: `~80 % případů` nebo `~80 % korporátních situací`.

`Audit-grade (banky, AI Act High-risk, DORA)` — clear segment naming,
funguje pro reader z banky. ✅

#### 2. Tone consistency

H2 *„Začni sázet."* / EN *„Start planting."* — drží gardening metafora,
funguje, závěrečná. ✅

`Mluvit s autorem` (CS) → ✅ casual, brand-consistent
`Talk to the author` (EN) → OK, ale lehce stiff. *„Email me"* by bylo
casual-er, ale „author" drží mannerism.

#### 3. Benefit visibility

`Proč teď` paragraph: *„AI vibe-coding tooly v roce 2026 dosáhly bodu,
kdy verbální input týmu generuje funkční artefakt v reálném čase."*
— tohle je **zopakování manifesto**, ne nový benefit. Reader to už četl.

Lepší: *„V Q1 2027 ti CEO bude chtít vidět 3 AI fíčury v produkci.
Pflanzer je nejrychlejší cesta, jak je tam dostat — bez toho, abys
zatloukl 6 měsíců do Design Sprintu."*

#### 4. Conversion mechanics — **fatal**

**3 CTAs jdou všechny do stejného loop typu** (otevřený, low-commit,
asynchronní):
1. `1-pager · Lean Pflanzer` → GitHub link → reader nemá pojem, co se
   tam objeví (PDF? README? .md file?). **Falešný expectation.**
2. `Tool na GitHubu` → také GitHub. **Stejný target jako #1.**
3. `Mluvit s autorem` → mailto. Highest-commit, ale ze 3 CTAs nejmenší
   visual prominence.

**Currently href="https://github.com/" placeholder na 4 různých místech
(hero × 1, CTA × 2, footer × 1)**. Tohle musí být fixed před launchem.

**Co chybí:**
- `Stáhnout 1-pager (PDF)` — lowest-friction, materialnejší než link na repo
- `Naplánovat 30min call` — Calendly link, ne mailto
- `Zapsat se na čekací listinu / pilot waitlist` — pokud je metoda v early
  access
- `Číst e-shop case study` — pokud existuje PDF

#### Diff CTAs:
```diff
- [1-pager · Lean Pflanzer →]   [Tool na GitHubu ↗]   [Mluvit s autorem ↗]
+ [Stáhnout 1-pager (PDF) ↓]   [Zapsat se na pilot waitlist →]   [Email tom@gizmax.cz ↗]
```

Anebo pokud 1-pager je v repo:
```diff
+ [1-pager (PDF, GitHub) ↗]   [30min call s autorem (Cal.com) ↗]   [Naskočit do tool repo ↗]
```

#### Diff „Proč teď" (CS):
```diff
- AI vibe-coding tooly v roce 2026 dosáhly bodu, kdy verbální input týmu
- generuje funkční artefakt v reálném čase. To je pákový moment, který se
- v korporátu zatím využívá nesystematicky — jeden tým si v Cursor udělá
- prototyp, ostatní o tom neví, nebo to musí re-implementovat.
-
- Pflanzer dává tomu pákovému momentu operační rámec: jak ho použít cross-
- funkčně, jak handoffovat, jak rozhodnout, kdy přestat. Bez toho rámce
- zůstane AI v korporátu sólo aktivita několika ranních ptáčat.
+ V Q1 2027 ti CEO bude chtít vidět tři AI fíčury v produkci. Ne tři
+ piloty v Cursor, ne tři PowerPointy z innovation day, ale tři věci,
+ které používají reální zákazníci.
+
+ Pflanzer je rámec, kterým tam ty tři věci dostaneš za 6 týdnů místo
+ 6 měsíců. Bez něj zůstane AI v korporátu solo aktivita několika
+ ranních ptáčat — a CEO ti to v Q2 2027 spočítá.
```

#### Diff „Why now" (EN):
```diff
- By 2026, AI vibe-coding tools have reached the point where a team's verbal
- input generates a working artifact in real time. That's a leverage moment
- corporates use unsystematically — one team builds a prototype in Cursor,
- others don't know about it, or have to re-implement it.
-
- Pflanzer gives that leverage moment an operating frame: how to use it
- cross-functionally, how to hand off, how to decide, when to stop. Without
- that frame, AI in the corporate stays a solo activity of a few early birds.
+ In Q1 2027 your CEO will want three AI features in production. Not three
+ prototypes in Cursor, not three Innovation Day slide decks — three things
+ real customers use.
+
+ Pflanzer is the frame that gets you there in 6 weeks instead of 6 months.
+ Without it, AI inside the corporate stays a solo gig for a handful of early
+ birds — and your CEO will notice in Q2.
```

**Verdikt CTA:** copy OK, CTAs chybí materiální options. **6/10 CS · 5/10 EN
aktuálně**, po reworku 8/10.

---

### H. Footer

**Co tam je:**
- Wordmark: `Pflanzer / Method.`
- Meta: Source (github.com, tom@gizmax.cz), Verze (v0.3 · 2026, MIT, Czech &
  English)
- Foot tagline (CS): *„Pestujeme AI v korporátu od roku 2026."* /
  EN: *„Planting AI in corporate since 2026."*

#### 1. Clarity & Friction

`MIT License | Czech & English` — clear, technical.
`github.com` jako visible link text **bez konkretního path** je placeholder.

#### 2. Tone consistency

`Pestujeme AI v korporátu od roku 2026.` — strong tagline-grade, drží
brand. ✅✅
`Planting AI in corporate since 2026.` — drobně awkward EN. *„corporate"*
jako noun singular zní jako kontrakce. Native: *„inside the enterprise"*
nebo *„into companies"*. Nebo nechat „in corporates" (plural).

#### 3. Benefit visibility

Footer není o benefitech. OK.

#### 4. Conversion mechanics

Žádný explicit re-CTA. Klasický B2B SaaS footer by tu měl:
- `Subscribe to newsletter`
- `Follow on LinkedIn`
- `Email`

Aktuálně footer je jen wordmark + meta. **Missed opportunity** — last
section před tab close je drahá real estate.

#### Diff foot tagline (EN):
```diff
- Planting AI in corporate since 2026.
+ Planting AI inside corporates since 2026.
```
nebo
```diff
+ Planting AI inside the enterprise. Since 2026.
```

**Verdikt footer:** ok. 7/10 CS · 6/10 EN.

---

## Headline tier ranking (všech 5 h-section)

| # | Heading (CS) | Heading (EN) | Score CS | Score EN | Verdict |
|---|---|---|---|---|---|
| 00 | Korporátní handoff hell. *Tohle vznikla, aby ho prolomila.* | Corporate handoff hell. *This was made to break it.* | 2/5 (gramatická chyba „Tohle vznikla") | 4/5 | EN > CS. CS fix nutný. |
| 01 | Jak metoda *roste.* | How the method *grows.* | 4/5 | 4/5 | ✅ Drží brand metaphor. Krátké, dobrý rytmus. |
| 02 | Pět věcí, které *nikdo jiný nedělá.* | Five things *no one else does.* | 3/5 | 4/5 | EN > CS. CS „nikdo jiný nedělá" zní jako sales pitch z 2017. EN funguje. Alternativy níže. |
| 03 | Z terénu. *e-shop · 2026.* | From the field. *e-shop · 2026.* | 5/5 | 5/5 | ✅✅ Newspaper / dispatch tonalita. Strongest. |
| 04 | Začni *sázet.* | Start *planting.* | 5/5 | 5/5 | ✅✅ Action verb + brand metaphor. Strongest closer. |

### Pod 3 → alternativy

**00 H2 alternativy (CS):**
```
A) Korporátní handoff hell. Metoda, která ho prolomí.
B) Šest až devět měsíců. Metoda, která to zkrátí na čtrnáct dní.
C) Korporátní handoff hell. A jak z něj vypadnout za 14 dní.
```

**00 H2 alternativy (EN):**
```
A) Corporate handoff hell. Here's how to break out.
B) Six to nine months. The method that turns it into fourteen days.
C) Corporate handoff hell — broken in 14 days.
```

**02 H2 alternativy (CS):**
```
A) Pět věcí, které ti banka odsouhlasí.
B) Pět věcí, které tě liší od AWS, McKinsey, AJ&Smart.
C) Pět věcí, které jiné metody zapomněly.
D) Pět věcí, kvůli kterým security řekne ano.
```

**02 H2 alternativy (EN):**
```
A) Five things the bank's compliance will sign.
B) Five things AWS, McKinsey and AJ&Smart still don't do.
C) Five things every other workshop framework forgot.
D) Five things that get past security.
```

---

## 5 tagline kandidátů (must work in CS + EN)

Tagline kritéria: ≤ 8 slov, fits on merch/billboard, drží brand voice,
funguje samostatně bez kontextu.

### 1. „Sázíme AI do korporátu." / „We plant AI inside the enterprise."
✅ Brand metaphor. Active verb. Krátké. Funguje na hoodie i landing page.

### 2. „Manuál. Ne manifesto." / „A manual. Not a manifesto."
✅✅ Tohle už je v frame-bottom — povýšit na primary tagline kandidát.
Self-deprecating, anti-bullshit signal, perfectly captures brand pozici.

### 3. „6 lidí. 2 sezení. 14 dní." / „6 people. 2 sessions. 14 days."
✅ Naked čísla. Reader si dosadí benefit. Strong v obou jazycích.

### 4. „Hřbitov metod. A jak z něj vyjít." / „The graveyard of frameworks. And how to walk out."
✅ Provokativní. Bere risk. Vhodné jako social/LinkedIn quote, ne hero.

### 5. „AI v produkci do čtrnácti dní. Bez politiky." / „AI in production in 14 days. No politics."
✅ Benefit + emotion (politiky/politics jako shared enemy). Direct.

**Doporučená primární tagline:** kombinace #2 (positioning) + #3 (proof).
Hero copy by mohlo být reorganizováno tak, aby tagline pyramida byla:

```
SÁZÍME AI DO KORPORÁTU.                       (positioning)
6 lidí. 2 sezení. 14 dní.                     (proof numbers)
Manuál. Ne manifesto.                         (anti-bullshit signal)
```

---

## 3 top P0 changes (must-fix před launch)

### P0-1. Oprav gramatickou chybu v H2 sekce 00

> CS: *„Tohle vznikla, aby ho prolomila."*

Subjekt `Tohle` (neutrum) vyžaduje sloveso `vzniklo`. Nebo přepsat na
*„Metoda, která ho prolomí."* (varianta výše).

**Risk if not fixed:** první H2, kterou reader přečte, má gramatickou
chybu. Pro Czech reader z banky = signal *„autor není přesný"*. Smrtelná
chyba pro positioning *„metodický manuál pro auditované prostředí"*.

### P0-2. Odstraň placeholder GitHub linky

`href="https://github.com/"` na 4 místech vede na github.com homepage.
Pokud repo ještě není public, doplň `href="#"` + tooltip „Coming soon"
nebo `href="mailto:tom@gizmax.cz?subject=Pflanzer%20early%20access"`.

**Risk if not fixed:** primární CTA leadne na github.com — reader si
myslí, že je rozbitý web.

### P0-3. Přepsat USP sekci 02

Současný stav: 20+ neviswětlených expertních termů v jedné sekci, žádný
reader benefit, statistical-rigor tón víc patřící do executive summary
research dokumentu než na landing page.

**Minimum viable rework:**
1. Vyhodit `Competitive research May 2026 (3 nezávislí experti)...`
   intro paragraph.
2. Každý USP řádek otevřít reader-facing větou („Co z toho máš").
3. Vyhodit z body text: `LDJ dot voting`, `Martinelli paper 2026`,
   `Discovery Debt Detector`, `ADR-0011 default Sunset T+18 mo`. Tohle
   jsou interní artefakty.
4. Připustit, že 5 USPs = příliš mnoho. Konsolidovat na 3 USPs s clear
   reader benefit, ostatní 2 přesunout do separátního „Methodology
   details" expandable.

**Risk if not fixed:** Sekce 02 je tab-close zone. Reader 45-letý VP
Eng touto sekcí proletí očima a opustí web s pocitem *„zase nějaký
governance tool, ne řešení mého problému"*.

---

## 5 P1 changes (should-fix krátce po launch)

### P1-1. EN copy potřebuje native pass

`pings` × 5, `vibing`, `kills months`, `early birds`, `planting AI in
corporate` — to jsou direct překlady, které ztratili idiom carry. Doporučení:
najmout EN native copywritera na jeden pass přes celý web (4-6 hodin
práce). Bez něj EN verze zaostává za CS o 1 score point celkově.

### P1-2. CTA tier rework

Aktuální 3 CTAs (1-pager / GitHub / Mluvit s autorem) jsou ve stejné
commit tier. Reader nemá clear signal *„co je low-risk start, co je
high-risk start"*. Doporučená 3-tier struktura:

```
TIER 1 (low friction, materializovaný):  [Stáhnout 1-pager PDF ↓]
TIER 2 (medium friction, action):         [Naplánovat 30min call ↗]
TIER 3 (high friction, expert):           [GitHub repo ↗]
```

### P1-3. Doplnit role-breakdown do e-shop field notes

Reader se ptá: *„kdo z 6 lidí byl právník?"* Současně receipty říkají
jen `Účastníci: 6`. Přidat řádek `Role v místnosti: Sponsor · Product ·
Eng · UX · Security · CS proxy`. Tahle 1 informace dělá víc heavy lifting
než celý odstavec body textu nad ní.

### P1-4. Statistical claims potřebují disclaimer

`~10× zrychlení v cyklu od nápadu k prod kódu` (stat card 00) — bez
asterisku to v auditovaném prostředí (banka, AI Act compliance) bude
challenged. Přidat 9px font-size poznámku: `*based on e-shop pilot,
default profile, n=1`.

Anebo zmírnit na `2–10×` s `*pilot range`.

### P1-5. Stage 5 / Day 11–14 description

> Quality gates score ≥ 80/100. Per-role handoff s odkazy na soubory.
> PR-ready commit. Deploy.

`Quality gates score ≥ 80/100` bez kontextu nedává smysl. Co se měří?
Buď vysvětlit (`security · a11y · test coverage · code review`), nebo
vyhodit.

---

## CS-only formulace, které v EN ztratily náboj

| # | CS originál | EN current | EN nedostatek | EN návrh |
|---|---|---|---|---|
| 1 | Zadavatel **pinká** s produktem, produkt s vývojem... | The sponsor **pings** product, product pings engineering... | „pings" = Slack notification, ztratil frustraci | The idea **bounces** between product, engineering, security, and legal. |
| 2 | dáme jim 3 hodiny **společného vajbování** s AI | give them 3 hours of vibe-coding with AI | „společného" ztraceno | give them 3 hours **together vibe-coding** with AI |
| 3 | rozhodnutí se dělají **na PowerPointu**, ne na funkčním artefaktu | decisions are made **on PowerPoint** | OK, but flat | decisions get made **on PowerPoint slides** — not on working artifacts |
| 4 | Tři hodiny **vajbili** | Three hours of **vibing** | „vibing" = party, ne work | Three hours **vibe-coding** / Three hours of **just shipping** |
| 5 | Pflanzer = německy **„pěstitel, sazeč"** | Pflanzer = German for **„planter, one who sows"** | „one who sows" = over-translation | Pflanzer is German for **„planter"** |
| 6 | sólo aktivita několika **ranních ptáčat** | a solo activity of a few **early birds** | „early birds" OK, ale flat | stays a **solo gig** for a handful of **early movers** |
| 7 | **Sazba** (Day 0 stage name) | **Sowing** | OK | OK, ale stage name overlapping s farming idiom — možná **Plant** by bylo punchier |
| 8 | **hřbitov** metod | **graveyard** most methods never returned from | OK | **graveyard** of frameworks — most never made it out |

---

## EN-only awkwardness

| # | EN copy | Problém | Návrh |
|---|---|---|---|
| 1 | `Manual for planting AI in rigid processes` (frame top) | „in rigid processes" zní jako ITIL document | `inside rigid orgs` |
| 2 | `~14 calendar days` (hero meta grid) | „calendar days" je odpověď na otázku, kterou nikdo nepoložil | `~14 days end-to-end` |
| 3 | `serial handoff kills months` | direct CS překlad | `serial handoffs burn months` |
| 4 | `What takes root, grows. What doesn't, everyone sees right away — not in a year.` | „everyone sees right away" je trochu vague | `What takes root, grows. What doesn't, you see it that week — not next year.` |
| 5 | `Cross-fn alignment grows, doesn't degrade.` (Day 6–9) | „Cross-fn" abbrev v body copy = bad | `Alignment holds — it doesn't degrade across the week.` |
| 6 | `Pflanzer measures the gap` (USP #03 sub-h) | academic | `Pflanzer pins it down` |
| 7 | `5 pillars that, together, no one else does in 2026` | grammar awkward („no one does pillars") | `5 things that, together, no one else has in 2026` |
| 8 | `the line between` (USP #03 body) | grammatically dangling | `the line between „I like it" and „I'll sign for it"` |
| 9 | `No direct competitor has a 48-72h async pre-read as a MUST gate.` | „MUST gate" caps + jargon | `No competitor makes the async pre-read mandatory.` |
| 10 | `Planting AI in corporate since 2026.` (footer) | „in corporate" = nominal singular = awkward | `Planting AI inside the enterprise. Since 2026.` |
| 11 | `corporate stakeholder unavailable` (USP #05) | telegrafický | `because no corporate stakeholder can clear 5 days back-to-back` |

---

## Co bys vyhodil / drasticky zkrátil (≥ 3 konkrétní pasáže)

### 1. Intro paragraf sekce 02 (USP)

> *„Competitive research May 2026 (3 nezávislí experti) potvrdil: vibe-coding samotný už není Pflanzer differentiator..."*

**Verdikt:** Vyhodit. Toto je executive summary research dokumentu na
landing page. Reader nepřišel hodnotit research metodologii — přišel
zjistit, jestli mu to pomůže. Nahradit 2-větným reader-facing setupem.

### 2. ADR / Method Charter / Martinelli references v USPs

> *„Externí validace: Martinelli paper 2026 kritizuje Spec Kit/BMAD/Kiro za chybějící stakeholder alignment + audit trail. Jeho critique pointy jsou doslova Pflanzer USPs."*
>
> *„(ADR-0011 default Sunset T+18 mo)"*
>
> *„per Method Charter v0.3"*

**Verdikt:** Vyhodit z marketing copy. Tohle jsou důkazy pro reviewer
v RFP nebo recenze v Architecture Review Board. Reader na landing page
to nečte, akorát to vytváří kognitivní noise. Přesunout do `/docs` nebo
`/methodology` link.

### 3. „AI-only feedback deflated 0.5/1.0" (USP #03)

**Verdikt:** Vyhodit. Bez kontextu (co je AI-only feedback? co je deflated?)
to vypadá jako interní implementation detail, který se omylem dostal do
copy. Buď vysvětlit v 1 větě, nebo zcela vyhodit.

### Bonus 4. „Discovery Debt Detector, Sandbox spec, AI Act tier Fáze A, Approved AI Tool list."

**Verdikt:** Zkrátit. 4 jména artefaktů v jedné větě bez kontextu =
buzz-word salad. Vyber 1-2 nejdůležitější (Discovery Readiness Gate +
AI Act tier), zbytek vyhoď, nebo přesun do feature list níže.

### Bonus 5. „Workshop methodology expert confirmation: žádný direct competitor v 2026. 12-měsíční náskok." (USP #03)

**Verdikt:** Vyhodit první větu, ponechat druhou („12-month lead").
„Workshop methodology expert confirmation" zní jako citace z příspěvku
na conferenci, ne jako prodejní argument.

---

## Co chybí (≥ 3 sekce / fakta, bez kterých čtenář nepadne dolů)

### 1. Pricing / engagement model

**Currently:** Web mluví o „operating-cadence layer pro AI Center of
Excellence" a porovnává s „$1M+ McKinsey transformations vs. $0 hackathon
frameworks". Ale **nikde neříká, kolik Pflanzer stojí**.

VP Eng z banky musí v hlavě udělat budget odhad. Bez čísla nepokračuje
do sales conversation.

**Doporučení:** Přidat sekci `Pricing` nebo alespoň 1 stat card:
- *„Pilot: $25k-50k flat. License v0.3: MIT (free pro internal use)."*
- *„Method Steward (audit-grade): $1.5k/month."*

Nebo jasné *„Pricing on request — book a 30min call"*.

### 2. „Who is this for? Who is this NOT for?"

**Currently:** Hero říká `Korporát · 5–5000+ FTE` (široký rozsah).
USP #02 zmiňuje banks/AI Act/DORA. Manifesto mluví obecně o „korporátu".

**Reader friction:** *„Jsem v 200-people fintech, není to spíš pro
Citibank?"* nebo *„Jsem v 5000-FTE bance, je to pro mě dost robust?"*

**Doporučení:** Přidat krátkou sekci nebo blok:
- ✅ For: regulated industries (banks, insurance, healthcare), 100+ FTE
- ✅ For: orgs s existujícím AI Center of Excellence intent
- ❌ Not for: pure software startups, <50 FTE
- ❌ Not for: hackathon culture (use Lovable directly)

### 3. Track record / proof beyond e-shop

**Currently:** Field Notes = e-shop. 1 case study. *„e-shop-style ~80 %
korporátních case-ů"* implikuje, že existují další.

**Reader friction:** *„Jediný case je e-commerce. Funguje to v bance?"*

**Doporučení:** Buď zveřejnit 2-3 další case (i anonymizované —
`European retail bank, 12k FTE, AI Act high-risk pilot, 18 days end-to-end`)
nebo open o tom („v0.3, e-shop pilot complete, banking pilot in progress").
Transparency > omyl signalizace zralosti.

### 4. „How is this different from a Design Sprint?" sekce

**Currently:** Roztroušeno v USP #04 (Design Sprint nemá pre-flight),
#05 (Design Sprint = 5 dní), 03 e-shop (re-implementuje Figmu za 2 měsíce).

**Doporučení:** Sjednotit do 1 srovnávací tabulky (3 sloupce: Pflanzer
vs. Design Sprint vs. AWS AI-DLC). Comparative table = vysoká SEO i
reader hodnota.

### 5. Author credibility

**Currently:** *„© 2026 Tom Pflanzer · GiZMaX"* v footeru. To je all.

**Reader friction:** *„Kdo je Tom Pflanzer? Why should I trust this
method?"*

**Doporučení:** 2-3 řádkový author bio. *„Tom Pflanzer, 15 let v AI/ML
v evropských bankách (Erste, KBC). Author of Pflanzer Method. Based in
Praha."* Tahle 1 věta dělá víc credibility lifting než celá USP sekce.

---

## Specifická P0/P1 souhrnná tabulka

| Priority | Section | Issue | Fix effort |
|---|---|---|---|
| **P0** | 00 H2 | Gramatická chyba „Tohle vznikla" | 2 min |
| **P0** | Hero, footer, CTA | 4× placeholder `https://github.com/` | 10 min |
| **P0** | 02 USPs | Statistical-rigor tón, 20+ jargon termů, žádný reader benefit | 3-4 h rewrite |
| **P1** | EN celý | Native idiom pass | 4-6 h |
| **P1** | 04 CTA | 3 CTAs ve stejné commit tier | 1 h + design |
| **P1** | 03 Field notes | Role-breakdown missing v receiptech | 15 min |
| **P1** | 00 Stat cards | `~10×` claim potřebuje disclaimer | 5 min |
| **P1** | 01 Flow | Day 11–14 „Quality gates ≥ 80/100" bez kontextu | 15 min |
| P2 | Hero CTA | Chybí „Stáhnout PDF" low-friction CTA | 30 min |
| P2 | Footer | Chybí re-CTA / newsletter / LinkedIn | 30 min |
| P2 | Author bio | Chybí kdo je Tom Pflanzer | 20 min |
| P2 | Pricing section | Chybí | 1 h decision + 30 min copy |
| P2 | Who is this for | Chybí | 30 min |

---

## Závěr

Pflanzer Method website má **silnou typografickou identitu, dobré
strukturní rozhodnutí (botanical SVG, e-shop receipts) a místy
copywriting nad-průměr** (manifesto, field notes, „Manuál ne manifesto"
tagline, Day 14 „Ship to prod").

**Ale:**

1. **Sekce 02 (USPs) je tab-close zone.** V současné podobě sabotuje
   konverzi všech ostatních sekcí. Toto je #1 priorita.
2. **EN copy je 70% direct translation z CS** a ztrácí brand voice.
   Potřebuje native pass nebo rewrite.
3. **CTA struktura nemá tier gradient** a všechny 3 leadnou na placeholder
   GitHub link.
4. **Chybí 5 standardních B2B SaaS elementů:** pricing, ideal customer
   profile, author bio, srovnávací tabulka s konkurencí, secondary case
   studies.

Po opravách P0 + P1 odhaduji **realistický gain z 6/10 na 8/10 CS, z 5/10
na 7.5/10 EN**.

Aktuálně by **VP Eng v Erste / KBC / ČSOB** scroll-readingem skončil v
sekci 02, otevřel by si LinkedIn autora a poslal Calendly link kolegovi
*„podívej se, je to pro nás?"* — což je v B2B SaaS funnel **fatální
slow-walk**.

Po opravách by **stejný VP Eng** scrollnul až do e-shop field notes,
stáhnul PDF case study, a v 24h naplánoval call. To je **3-4× lepší
conversion velocity** za 8-10 hodin copy práce.

---

*Audit completed. Filter passed: „Vyhodil bych to z landing page,
kdybych pro to platil?" — Yes, ~30 % current copy by qualified. Po
reworku očekávané ~5 %.*
