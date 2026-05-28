# Marketing audit — Output cyklu: „hotový produkt" vs „prototyp"

> **Datum:** 2026-05-28
> **Auditor:** senior B2B marketing editor (sub-agent)
> **Trigger:** uživatelská korekce May 2026 — *„Pflanzer metoda by ti měla dát již reálný běžící produkt … Výstup z Pflanzer metody je hotový produkt."*
> **Scope:** website/index.html (2552 ř.), website/1-pager.html (636 ř.), README.md, docs/methodology/00-tldr.md, docs/methodology/00-lean-pflanzer.md, docs/case-studies/eshop-2026.md.

---

## TLDR (5 řádků)

- Napočítáno **34 zmínek o outputu** napříč 6 soubory: **9 Strong**, **11 Mid**, **14 Weak**.
- **Nejtoxičtější vzorec:** copy konzistentně používá *„prototyp / klikací prototyp / 3 prototypes"* jako primární popis výstupu Session 1, a teprve sekundárně dodává *„většina kódu jde do produkce"*. To buyera nutí myslet *„prototyp = papír pro vývojáře"* místo *„kód, který shippuje"*.
- Slovo *„většina kódu"* (anglicky *„most of the code"*) je **6× použito** napříč materiály — implicitně signalizuje, že část se zahodí. Per user claim by mělo být *„kód jde do produkce"*, tečka.
- *„Handoff package"* (4× v indexu, 1× v 1-pageru, 1× v README) zní jako *„papírová specka pro vývojáře, kteří to teprve napíšou"* — přesně to, čeho se Pflanzer **odlišuje od SDD**, a přesto to máme v každé sekci.
- Top 5 P0 fixes níže (§ Recommendations P0). Sekce 02b *„Past spec-drivenu"*, kterou jsme **právě commitovali** (3f46410), obsahuje **dvě weak fráze** (*„Funkční klikací prototyp od hodiny 1"*, *„klikatelný web s API skeletonem"*) — náš vlastní recent commit je underselling.

---

## 1. Klasifikační rámec

| Kategorie | Definice | Příklady z corpusu |
|-----------|----------|---------------------|
| **STRONG** | Match s user claim — output = běžící produkt / kód v produkci | *„Kód v produkci"*, *„code in production"*, *„most of the code ships straight to production"*, *„PR-ready commit. Deploy."*, *„not three Cursor prototypes — three things real customers use"* |
| **MID** | Ambiguous — technicky popisuje výstup, ale buyer si může představit *„prototype which engineers will harden later"* | *„3 funkční weby"*, *„Quality gates ≥ 80/100"*, *„Per-role handoff s odkazy na soubory"*, *„most of the code"* (slovo *„most"* implikuje výhybku) |
| **WEAK** | Underselling / contradicts user claim — buyer čte *„throw-away prototype"* | *„Funkční prototyp"*, *„klikací prototyp"*, *„prototyp"* v Output buňce tabulky, *„3 prototyp · prod kód"*, *„Throw-away je default v charteru"*, *„handoff package"* (bez „PR-ready" kontextu), *„klikatelný web s API skeletonem"* |

**Klíčová asymetrie pro buyera:**

- *Persona A (bank CTO, regulated)* už má v hlavě model *„nic neshippuje bez 6 audit colos"*. Když čte *„prototyp"*, čte *„OK, takže ten kód mi pak vývojáři napíšou znovu standardním SDLC, jen mám dříve cross-fn alignment"*. To je underselling — ztrácíme USP *„kód jde rovnou, ne re-implementace"*.
- *Persona B (eshop VP Eng, digital-native)* už zažil Bolt/v0/Lovable a ví, že *„prototyp"* tam často = throw-away. Když čte *„3 prototypes"*, default očekávání je *„cool demo, dev tým to pak napíše v Next.js znovu"*. Ztrácíme **hlavní 10× speedup claim**.

Obě persony jsou **citlivé na to samé slovo z opačné strany**: bank CTO si přeje slyšet *„production-grade"* (kvůli compliance), eshop VP Eng *„ships to prod"* (kvůli speedu). Slovo *„prototyp"* fragmentuje obě obě persony.

---

## 2. Per-file scan

### 2.1 `website/index.html`

#### Hero (ř. 1130–1190)

| Řádek | Element | Text | Klasifikace |
|-------|---------|------|-------------|
| 1140–1141 | Hero stat block, label „Výstup" | *„Kód v produkci / Code in production"* | **STRONG** |
| 1145 | Hero stat block, „Délka cyklu" | *„~14 dní calendar"* | Neutral |
| 1164–1165 | Hero tagline CS | *„Sázíme AI do korporátu. 6 lidí, 2 sezení, kód v produkci za 14 dní — místo 9 měsíců sériového handoffu."* | **STRONG** |
| 1167–1169 | Hero tagline EN | *„… code in production in 14 days — instead of 9 months of serial handoff."* | **STRONG** |

**Hero verdict:** STRONG. Žádný fix.

**Note k uživatelské otázce *„Co znamená 14 dní?"*:** Hero stat block staví do kontrastu *„~6–9 měsíců sériového handoffu"* (ř. 1289) vs *„~14 dní Pflanzer default profil"* (ř. 1293). Ve spojení s *„zrychlení cyklu od nápadu k prod kódu"* (ř. 1297) je interpretace **jednoznačná: 14 dní = idea → prod code**. Žádná ambiguita typu *„14 dní = prototype ready for hardening"*. Hero drží claim. ✅

#### Sekce 00 Manifesto (ř. 1192–1309)

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 1210–1213 | *„V korporátu trvá cesta od nápadu k funkční fíčuře 6 až 9 měsíců. … Rozhodnutí se dělají na PowerPointu — ne na funkčním artefaktu."* | Mid |
| 1217–1218 | *„Vibe-coding tooly dnes umí v reálném čase vytáhnout z verbálního inputu týmu **funkční prototyp** — ne wireframe v Figmě, ne mockup v Sketch, ale klikatelný web s API skeletonem."* | **WEAK** (a) *„funkční prototyp"* zavádí slovo „prototyp" do hero copy; (b) *„klikatelný web s API skeletonem"* zní jako *„demo, ne produkt"* — *„skeleton"* = unfinished |
| 1228–1229 | *„… 3 funkční weby, ke kterým se mohou vyjádřit. Po jednom týdnu ladění a druhém 3hodinovém setkání jde **většina kódu** rovnou do produkce."* | Mid (slovo *„většina"* underselling — viz § 3) |
| 1234–1235 | *„Nejde o rychlejší výrobu mockupů. Jde o cross-funkční alignment **na funkčním artefaktu**, ne na slidu."* | Mid (slovo *„artefakt"* je polysemic — viz § Glossary) |
| 1247–1255 | EN mirror — *„a working prototype"*, *„a clickable web app with an API skeleton"* | **WEAK** (stejné jako 1217) |
| 1266–1267 | *„… 3 working web apps to respond to. After a week of refinement and a second 3-hour session, most of the code ships straight to production."* | Mid → STRONG (slovo *„ships straight to production"* je STRONG, ale „most" underselling) |

**Sekce 00 verdict:** Mixed. 2 weak fráze v EN+CS verzi (ř. 1217 + 1254) jsou nejtoxičtější místa. Hero je STRONG, sekce 00 to redukuje.

#### Sekce 01 Botanical flow (ř. 1376–1610)

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 1573–1576 | SVG label „Den 14 / Day 14 — Kód v produkci / Code in production" | **STRONG** |
| 1589–1590 | Den 5 Session 1: *„In-room vibe-coding. 3 paralelní weby v Bolt / v0 / Lovable / Claude Code. Silent voting, Decider shortlist."* | Mid (*„3 paralelní weby"* je dobré — ne *„prototypy"*) |
| 1604–1605 | Den 11–14 Ship to prod: *„Quality gates score ≥ 80/100. Per-role **handoff** s odkazy na soubory. PR-ready commit. Deploy."* | Mid (*„Quality gates"* + *„PR-ready commit. Deploy."* je STRONG; ale *„handoff"* tam zní starkly) |

**Per user otázka k 1604–1605:** *„„handoff" tam zní starkly. Replace?"* — **ANO**. *„Per-role handoff s odkazy na soubory"* implicitně říká *„papír pro vývojáře"*. Doporučení v § 4. Stejný pattern v 1-pageru (ř. 472) a v EN verzi.

#### Sekce 02 USPs (ř. 1614–1903)

USP #01 *„Non-tech v místnosti"* (ř. 1643–1675) — používá slovo *„artefakt"* v 1652/1664: *„od minuty 0 ve stejné místnosti, na stejném artefaktu / on the same artifact"*. **MID** — polysemic, viz § Glossary.

USP #02 *„Native AI Act compliance"* — neutrální vůči output claim.

USP #03–05 — neutrální.

#### Sekce 02b Spec-driven trap (ř. 1911–2142) — **NÁŠ RECENT COMMIT 3f46410**

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 1932 | *„Pflanzer dělá opačnou věc — **artefakt** v místnosti od minuty 0, specka padá ven jako vedlejší produkt."* | Mid (*„artefakt"* polysemic) |
| 1940 | EN mirror: *„the artifact is in the room from minute zero, the spec falls out as a by-product."* | Mid |
| 1988 | SVG label: *„Day 0 → Day 14 · single artifact"* | Mid |
| 2023 | SVG label D14: *„prod"* | **STRONG** |
| 2073–2075 | *„Pflanzer · artifact-first / Jeden artefakt. Šest hlav. Stejná místnost."* | Mid |
| 2077 | *„**Funkční klikací prototyp** od hodiny 1. Security, Legal, DPO čtou ten samý URL, ne PDF se speckou."* | **WEAK** ← **JUST COMMITTED** |
| 2082 | EN mirror: *„A working clickable prototype from hour 1."* | **WEAK** ← **JUST COMMITTED** |
| 2087–2089 | tag-list: *„same room · alignment roste · D14 → prod"* | **STRONG** |
| 2120–2122 | Punchline: *„Specka je nájemné. Artefakt je vlastnictví. Pflanzer staví artefakty."* | Mid (viz § Punchline audit) |
| 2124–2126 | EN: *„A spec is rent. An artifact is equity. Pflanzer builds artifacts."* | Mid |
| 2133 | *„Artefakt > spec dokument."* | Mid |
| 2138 | EN: *„Artifact > spec document."* | Mid |

**Sekce 02b verdict:** Sekce, kterou jsme **právě přidali** (commit 3f46410), obsahuje **2 WEAK fráze v CS + EN verzi** (ř. 2077, 2082). To je P0 fix.

**Per user otázka *„Slovo „prototyp" je v té sekci — měl by být „produkt"?"*:** ANO. Sekce 02b celé bojuje proti SDD pomocí argumentu *„artefakt > spec"*, ale potom sama říká *„funkční klikací prototyp od hodiny 1"*. To je **logická díra** — buyer si přečte: *„OK, takže máte prototype, ne hotový produkt. Tak v čem se lišíte od Boltu?"*. Per user claim **má být *„běžící produkt od hodiny 1"*** nebo *„kód, který shippuje od hodiny 1"*.

#### Comparison matrix (ř. 2167–2173) — Pflanzer řádek output

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 2173 | CS: *„3 prototyp · prod kód"* / EN: *„3 prototypes · prod code"* | **WEAK** |

**Per user otázka:** Replace na *„3 funkční prod-ready kódu (winner shippuje)"*? — ANO. *„3 prototyp"* v output buňce, kde okolní metody mají *„MVP delivery"*, *„Operating model + roadmap"*, *„High-fidelity prototyp"* — Pflanzer vychází vedle Design Sprintu jako varianta téhož. To je explicit underselling claim: *„běží stejně daleko jak Design Sprint"*. Per user claim: Pflanzer **jediný** v tabulce má prod kód jako output.

#### Sekce 03 Field Notes e-shop (ř. 2228–2305)

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 2249–2252 | Pullquote CS: *„… Měli jsme tři funkční weby. Při dalším setkání jsme dva doladili. Na konci jde **většina kódu** rovnou do produkce."* | Mid |
| 2254–2257 | EN pullquote: *„… We had three working web apps. … **Most of the code** shipped straight to production."* | Mid |
| 2263–2264 | *„… cesta od první alignment session k produktivnímu kódu trvala týdny, ne měsíce"* | **STRONG** |
| 2268–2269 | *„Pflanzer cyklus skončí s **kódem, který lead developer mergne za 1–2 dny**."* | **STRONG** |
| 2293 | Receipt: Varianty — *„3 prototyp / 3 prototypes"* | **WEAK** |

**Per user otázka *„„většina" underselling. Co s tím?"*** — ANO. Slovo *„většina"* v 6 výskytech napříč materiály (1229, 1267, 2252, 2257, README ř. 22, 00-lean ř. 14, eshop ř. 21) je systematický underselling. Buyer čte: *„OK takže část se zahazuje. Kolik? 60 %? 95 %? 5 %?"*. Hard claim by byl: *„kód jde do produkce"* (bez kvalifikátoru), s podpůrnou metrikou *„≥80/100 quality gate score"*. Případně *„≥80 % kódu shippuje"* je tvrdý a měřitelný — *„most"* je vague.

#### Pricing (ř. 2309–2378), Sekce 04 CTA (ř. 2383–2485)

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 2340 | Pricing list: *„Handoff package + T+30 retro"* | Mid |
| 2460–2462 | *„V Q1 2027 ti CEO bude chtít vidět tři AI fíčury v produkci. Ne tři piloty v Cursor, ne tři PowerPointy z Innovation Day — tři věci, které používají reální zákazníci."* | **STRONG** ← per user identification |
| 2472–2474 | EN mirror | **STRONG** |

Sekce 04 je **nejsilnější část celého webu** vůči user claim. Drží linii: *„kód v prod, ne prototyp, ne deck"*.

---

### 2.2 `website/1-pager.html`

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 422 | Tagline CS: *„Sázíme AI do korporátu. 6 lidí, 2 sezení, kód v produkci za 14 dní."* | **STRONG** |
| 425 | Tagline EN: *„… code in production in 14 days."* | **STRONG** |
| 432–433 | Lede CS: *„… **Většina kódu** jde rovnou do produkce."* | Mid |
| 440–441 | Lede EN: *„… **Most of the code** ships straight to production."* | Mid |
| 457 | Recipe Day 5 Session 1: *„In-room vibe-coding. **3 paralelní weby**. Silent voting, shortlist."* | Mid (lepší než „3 prototypes" — vědomě používá „weby") |
| 472 | Recipe Day 11–14: *„Quality gates ≥ 80/100. PR-ready commit. Deploy."* | **STRONG** (slovo „handoff" tady **chybí**, sehrálo se to lépe než v indexu!) |
| 573–576 | Field notes e-shop: *„… 3 funkční weby. Druhé setkání = doladění, **většina kódu** rovnou do produkce."* | Mid |
| 578–580 | EN mirror | Mid |

**1-pager verdict:** Lepší než index. Den 11–14 cell **úmyslně vynechává *„handoff"* slovo** (ř. 472) — výsledek je STRONG. Index měl by replikovat. Slabost: 4× *„většina kódu / most of the code"*.

---

### 2.3 `README.md`

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 5 | *„… společně provibekódují 1–3 **funkční prototypy**."* | **WEAK** |
| 10 | *„… e-shop pilotu (3h vibe, 3 weby, **ship to prod**)."* | **STRONG** |
| 20 | *„… tým se sejde, společně provibe-koduje 2–3 varianty, rozhodne, kód projde production gates, ven jde **PR připravený k mergi**."* | **STRONG** |
| 22 | *„**Většina kódu** z vibe-coding session je použitelná, ne jen reference pro re-implementaci."* | Mid |
| 26–40 | Quick-start: *„(3 sezení = ship to production)"*, *„7 quality gates"*, *„PR-ready package"* | **STRONG** |
| 48 | *„Cílem je `gate_score >= 80/100` = **většina kódu se dá použít v produkci**."* | Mid |
| 91 | *„Throw-away interní demo (`production_readiness_target = 0`)"* — opt-in pro hosted SaaS | **WEAK** (per user *„throw-away = discard, contradicts hotový produkt"*) — viz § 3 |
| 107 | tabulka „Production code defaults" — *„✅ testy, strict types, lint"* | **STRONG** |

**README verdict:** Ř. 5 je hned na začátku — *„1–3 funkční prototypy"*. **První 5 řádků README jsou underselling.** Ř. 91 *„Throw-away interní demo"* je legit (opt-in pro hosted SaaS demo), ale prezentován jako *„one of the use cases"*, ne jako anti-pattern výjimka.

---

### 2.4 `docs/methodology/00-tldr.md`

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 17 | *„… AI slouží jako vibe-coding páka, která z verbálního inputu týmu generuje **funkční mockupy** v reálném čase."* | **WEAK** (*„mockupy"* = jasný vizuální layer, ne code) |
| 18 | *„… cross-functional alignment na funkčním artefaktu, ne na PowerPointu"* | Mid |
| 29 | *„… AI generuje 1–3 **mockupy**, BE shadow agent paralelně generuje OpenAPI 3.1"* | **WEAK** |
| 31 | *„Výstup = anotované **varianty** + risk register"* | Mid |
| 33 | *„… **klikací prototyp** v sandbox VPC s 24 h TTL a watermark"* | **WEAK** |
| 44 | *„1–3 anotované **klikací prototypy** v izolovaném sandboxu"* | **WEAK** |
| 50 | *„… P2P (Prototype-to-Prod) checklist"* | **WEAK** (slovo *„Prototype-to-Prod"* zafixuje *„prototype" jako mental anchor*) |
| 80 | *„Throw-away je **default v charteru**"* | **WEAK** (per user — viz § 3) |

**00-tldr verdict:** **Nejhorší dokument z corpusu.** 6× weak language napříč 88 řádků. Tento dokument je audit-grade variant (viz § disclaimer ř. 4), nicméně **uživatel si ho přečte první podle ordering** v `docs/methodology/`. Hned v sekci „Jak to funguje" čte *„AI generuje 1–3 mockupy"* a v sekci „Co dostaneš" *„1–3 anotované klikací prototypy"* + *„Prototype-to-Prod checklist"*. Pro audit-grade Persona A bank CTO je to **kontradiktorní s hero**: hero říká *„kód v produkci za 14 dní"*, 00-tldr říká *„dostaneš klikací prototyp v sandboxu"*.

---

### 2.5 `docs/methodology/00-lean-pflanzer.md`

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 14 | *„… 2 setkání, 1 týden mezi nimi, **většina kódu jde rovnou do produkce**."* | Mid → STRONG |
| 31 | Recept Den 5: *„… 2-3 paralelně postavené weby v Bolt / v0 / Lovable / Claude Code"* | Mid (*„weby"*, ne *„prototypy"* — dobré) |
| 53–54 | *„**3 funkční weby** (ne mockupy v Figmě) — clickable, deployed v sandbox URL"* | **STRONG** (explicit kontrast: ne-mockup) |
| 55 | *„**Winner kód** (≥80/100 gate score) — Vite + React + TS + ESLint + Vitest, exportovatelný do target repu."* | **STRONG** |
| 56 | *„Per-role **handoff** s odkazy na konkrétní soubory (ne TBD placeholders)."* | Mid (*„handoff"* polysemic — ale s „odkazy na konkrétní soubory" je to jasnější) |

**00-lean verdict:** Nejlepší dokument z corpusu vůči user claim. Drží linii. Stačí 1 cosmetic upgrade.

---

### 2.6 `docs/case-studies/eshop-2026.md`

| Řádek | Text | Klasifikace |
|-------|------|-------------|
| 22–23 | *„… aby **většina kódu z vibe-session šla přímo do produkce** — ne jako reference pro re-implementaci."* | STRONG (poslední half-věta *„ne jako reference pro re-implementaci"* zachraňuje claim) |
| 56 | *„Po cca 90 minutách: **3 funkční weby** (clickable, deployed)."* | Mid |
| 88 | *„**Winner kód** s definovaným scope."* | **STRONG** |
| 95 | *„Cíl: Většina kódu z vibe-coding session jde rovnou do produkce, ne jako reference pro re-implementaci."* | STRONG (jediná instance v corpusu, kde *„většina"* explicitně kvalifikováno *„ne re-impl"* — buyer pak ví, že *„většina ≠ throw-away rest"*) |
| 99 | *„Kolik % winner kódu zůstalo v prod commit?"* | (placeholder — TBD doplnit po retro) |

**e-shop verdict:** Drží claim. Slovo *„většina"* je 2× použito, ale 2× v páru s *„ne jako reference pro re-implementaci"* — to je **správný hedge**: říká *„část se ladí, ale neimplementuje se znovu"*. To je honest production reality (bug fixes při deployi). Tento pattern (*„většina kódu rovnou … ne re-impl"*) doporučuji **replikovat napříč materiály** místo *„většina kódu rovnou do prod."* samotného.

---

## 3. Top 10 problematic phrases — P0 fix recommendations

| # | File:line | Current text (CS) | Current text (EN) | Recommended replacement (CS) | Recommended replacement (EN) | Why matters |
|---|-----------|-------------------|-------------------|------------------------------|-------------------------------|-------------|
| 1 | `website/index.html:2077,2082` (sekce 02b, **náš recent commit**) | *„Funkční klikací prototyp od hodiny 1."* | *„A working clickable prototype from hour 1."* | *„Funkční běžící produkt od hodiny 1."* | *„A working, running product from hour 1."* | Sekce 02b je **anti-SDD argument**. Jestli mluvíme o *„prototypu"*, buyer si přečte *„OK, takže máte Bolt-style demo, lišíte se od SDD jen tím, že vynecháváte spec krok"* — ztrácíme USP *„kód jde rovnou"*. Persona A+B obojí. |
| 2 | `website/index.html:1217–1218,1254–1255` (sekce 00 manifesto) | *„… vytáhnout z verbálního inputu týmu funkční prototyp — ne wireframe v Figmě, ne mockup v Sketch, ale klikatelný web s API skeletonem."* | *„… pull a working prototype from a team's verbal input in real time — not a Figma wireframe, not a Sketch mockup, but a clickable web app with an API skeleton."* | *„… vytáhnout z verbálního inputu týmu **běžící aplikaci** — ne wireframe v Figmě, ne mockup v Sketch, ale **deployable kód s REST/GraphQL endpointy**."* | *„… pull a **running application** from a team's verbal input in real time — not a Figma wireframe, not a Sketch mockup, but **deployable code with REST/GraphQL endpoints**."* | *„API skeleton"* zní jako *„kostra, kterou backend tým doplní"*. Buyer A (bank CTO) si přečte *„prototype = ne-shipovatelná demo"*. |
| 3 | `website/index.html:2173` (Comparison matrix, Pflanzer řádek Output) | *„3 prototyp · prod kód"* | *„3 prototypes · prod code"* | *„3 funkční varianty → prod kód (winner shippuje)"* | *„3 working variants → prod code (winner ships)"* | V tabulce má Pflanzer řádek output, kde okolní metody mají *„MVP delivery"*, *„High-fidelity prototyp"*. Slovo *„prototyp"* v Pflanzer řádku okrádá differentiator. Persona A+B. |
| 4 | `website/index.html:1229,1267` + `1-pager.html:432,440` + `eshop-2026.md:22,95` + `00-lean-pflanzer.md:14` + `README.md:22,48` (6 výskytů *„většina kódu"*) | *„… většina kódu rovnou do produkce."* | *„… most of the code ships straight to production."* | Buď **A**: *„… kód jde rovnou do produkce."* (bez kvalifikátoru) — pokud věříme reálnému % ≥ 80. Nebo **B** (e-shop pattern, replikovat): *„… kód jde rovnou do produkce, ne jako reference pro re-implementaci."* (kvalifikuje *„většina"* jako *„fixes při deploy"*, ne *„re-write"*). | Same options EN: **A** *„… code ships straight to production."* / **B** *„… code ships straight to production, not as a reference for re-implementation."* | *„Most"* implikuje *„část se zahazuje"* — neurčité, jak velká. Buyer si dosadí worst case. Persona A+B. e-shop case 2× ukazuje správný pattern. |
| 5 | `README.md:5` (lead-in repo) | *„… společně provibekódují 1–3 funkční prototypy."* | (jen CS) | *„… společně provibekódují 1–3 funkční varianty produktu."* | (jen CS) | První 3 řádky README = první dojem otevírajícího repa. *„Prototypy"* hned v lead-inu fragmentuje. |
| 6 | `docs/methodology/00-tldr.md:17,29,33,44,50` (5× *„mockupy / klikací prototypy / Prototype-to-Prod"*) | *„AI generuje 1–3 mockupy"*, *„klikací prototyp v sandbox VPC"*, *„P2P (Prototype-to-Prod) checklist"* | (CS dokument) | Replace *„mockupy"* → *„kód"* / *„běžící aplikace"*. *„Klikací prototyp"* → *„běžící varianta v sandbox VPC"*. *„Prototype-to-Prod"* → *„Sandbox-to-Prod (S2P)"* checklist. | n/a | Audit-grade dokument pro Persona A. *„Mockupy"* a *„Prototype-to-Prod"* zafixuje mental model *„dva oddělené světy: prototype a prod"*, opak Pflanzer claim. |
| 7 | `docs/methodology/00-tldr.md:80` + `00-lean-pflanzer.md` (implicit) + `README.md:91` | *„Throw-away je default v charteru"* | *„throw-away/evolve flag"* (00-tldr ř. 44) | Redefinovat: *„Throw-away = NOT default. Default = ship-to-prod. Throw-away je explicit opt-in pouze pro: greenfield hackathon, marketing one-off, dev/internal demo. Pflanzer pilot = ship-to-prod target by default."* | n/a | **Per user claim explicit:** *„Žádná specka se pak už programátorům nedává. Výstup z Pflanzer metody je hotový produkt."* — pokud throw-away je default, pak hotový produkt **není** default. To je přímá kontradikce s user claim. Persona A+B (oba pochopí *„throw-away default" = nebezpečí*). |
| 8 | `website/index.html:1604–1605` (sekce 01 Botanical, Den 11–14) | *„Quality gates score ≥ 80/100. Per-role **handoff** s odkazy na soubory. PR-ready commit. Deploy."* | *„… Per-role **handoff** with file links. PR-ready commit. Deploy."* | *„Quality gates score ≥ 80/100. PR-ready commit s odkazy na soubory per role. Deploy."* | *„… PR-ready commit with per-role file pointers. Deploy."* | Per user otázka *„„handoff" tam zní starkly"*. ANO. *„Handoff package"* connotation = *„papír pro vývojáře, kteří to teprve napíšou"*. 1-pager ř. 472 sám vynechává slovo — funguje. Index by měl replikovat. |
| 9 | `website/index.html:2293` (Field Notes Receipty řádek „Varianty") | *„3 prototyp"* | *„3 prototypes"* | *„3 funkční varianty"* | *„3 working variants"* | Receipty = audit-style stamp. *„Prototyp"* v stamp formátu se podepíše jako fakt: *„e-shop dostalo 3 prototypy"*. |
| 10 | `README.md:91` | *„Throw-away interní demo (`production_readiness_target = 0`)"* | n/a | Reframe celý bullet: *„Throw-away demo (např. Innovation Day showcase, marketing landing one-off) — vědomý opt-out z ship-to-prod default. Konfigurace: `production_readiness_target = 0`. Pflanzer pilot default = `production_readiness_target ≥ 80`."* | n/a | Bullet aktuálně presents throw-away jako *„one of the use cases"* na úrovni s ship-to-prod. Per user: throw-away = explicit výjimka, ne ekvivalent. |

---

## 4. Glossary recommendation — termín *„artefakt" / „artifact"*

### Tension

Per user clarification: *„Výstup z Pflanzer metody je hotový produkt."* Pflanzer punchline (právě commitnutý 3f46410): *„Specka je nájemné, artefakt vlastnictví. Pflanzer staví artefakty."*

*„Artefakt"* je v komputer-science / software engineering kontextu **polysemic**:
- **Software artifact** (Wikipedia, IEEE): *„one of many kinds of tangible by-products produced during the development of software"* — zahrnuje spec dokumenty, design diagrams, **i source code**, **i deployable binaries**.
- **Casual reading** (mimo SE): *„nějaký výtvor, předmět"* — vágní.

Buyer si tedy *„artefakt"* může přečíst tak, že to znamená spec dokument (kontradikce s celou sekcí 02b), klikací prototyp, deployed running app, nebo *„prostě cokoliv hmotného"*.

### Options analyzed

| Option | Pro | Contra |
|--------|-----|--------|
| **A. Replace *„artefakt"* na *„produkt"* / *„kód v produkci"*** | Tvrdý, jednoznačný claim. Match s user. | Sekce 02b SVG ztrácí poetiku (*„single artifact"* je vizuálně lepší než *„single product"*). Punchline *„Pflanzer staví produkty"* zní generic — *„staví artefakty"* je distinctively positioned proti SDD. |
| **B. Re-define *„artefakt"* explicitly jako *„running production code"*** | Drží poetiku, ale buyer ví, co tím myslíme. | Vyžaduje glossary v každém dokumentu. Buyer co skanuje, glossary nečte. |
| **C. Keep + disambiguate inline** | Lze udělat *„artefakt = běžící kód, ne spec"* v každé sekci. Drží punchline. | Verbose. |

### Recommendation: **Hybrid A+C**

1. **Punchline keep** (ř. 2120–2126): *„Specka je nájemné. Artefakt je vlastnictví. Pflanzer staví artefakty."* — drží distinctive positioning vs SDD.

2. **Inline disambiguation v sekci 02b** (ř. 2077, 2082): replace *„funkční klikací prototyp"* → *„funkční běžící produkt (kód, ne spec)"*. Tím punchline *„artefakt = vlastnictví"* dostává konkrétní obsah: artefakt = produkční kód, ne PDF spec.

3. **Glossary card** v sekci 02b nebo v footer:
   > V Pflanzer terminologii: *artefakt* = běžící produkt (kód v produkci), **ne** spec dokument, **ne** Figma, **ne** wireframe. Pflanzer artefakt je to, co tým může commitnout a deploynout.

4. **Sekce 00 (manifesto) ř. 1234–1235**: *„cross-funkční alignment na funkčním artefaktu"* — replace na *„cross-funkční alignment na **běžícím produktu**"* (concrete, no ambiguity).

5. **Mantra:** *„artefakt = produkt"* je linka. Kdekoliv copy hovoří o output v abstraktu, slovo musí být *„produkt"* nebo *„kód v produkci"*. Slovo *„artefakt"* používáme **jen** v anti-SDD positioning (sekce 02b) — tam má distinctive value vs *„spec dokument"*.

---

## 5. Hero tagline audit

### Current (`website/index.html:1164,1167`)

CS: *„Sázíme AI do korporátu. 6 lidí, 2 sezení, kód v produkci za 14 dní — místo 9 měsíců sériového handoffu."*

EN: *„We plant AI inside the enterprise. 6 people, 2 sessions, code in production in 14 days — instead of 9 months of serial handoff."*

### Klasifikace: **STRONG**

Hero drží claim. Match s user. Žádný fix.

### Strongest possible (zvážit pro variant test)

CS: *„Sázíme AI do korporátu. 6 lidí, 2 sezení, **běžící produkt za 14 dní** — místo 9 měsíců spec ping-pongu."*

EN: *„We plant AI inside the enterprise. 6 people, 2 sessions, **a shipping product in 14 days** — instead of 9 months of spec ping-pong."*

**Rationale:**
- *„Kód v produkci"* je STRONG (drží technical accuracy), ale *„běžící produkt"* je o úroveň silnější marketing-wise: *„produkt"* connotes *„customer-facing thing they paid for"*, *„kód"* connotes *„technical artifact"*. Persona A bank CTO myslí *„kód v produkci = production deployment"*; Persona B eshop VP Eng myslí to samé. Žádná není underserved. Ale board-level reader (CFO, CEO) čte *„produkt"* lépe.
- *„sériového handoffu"* → *„spec ping-pongu"* připojuje sekci 02b (spec-driven trap) explicit do hero. Posiluje story arc.

**Verdict:** Current hero je solid (STRONG). Strongest variant nabízím jako A/B test option, **ne jako P0 fix**.

---

## 6. Punchline audit — *„Specka je nájemné, artefakt vlastnictví"*

### Current (`website/index.html:2120–2126`)

CS: *„Specka je **nájemné**. Artefakt je **vlastnictví**. Pflanzer staví artefakty."*

EN: *„A spec is **rent**. An artifact is **equity**. Pflanzer builds artifacts."*

### Verdict: **Drží claim, ale s caveatem**

**Drží claim, protože:**
- Metafora *„rent vs equity"* je silná pro buyer (finanční model: spec = recurring cost without ownership; artifact = one-time investment with ownership). Persona A (bank CTO) tohle čte přesně tak (CapEx mindset).
- Distinctively positioned vs SDD — žádná konkurence tuto metaforu nepoužívá.
- Memorable. Punchy.

**Caveat (underselling):**
- *„Artefakt"* sám o sobě je ambiguous (viz § Glossary). Buyer si bez kontextu může *„artefakt"* dosadit *„dokument, který si můžeme ponechat"* — to je weaker než *„běžící produkt, který obsluhuje zákazníky"*.
- Ve spojení s ř. 2077 *„funkční klikací prototyp od hodiny 1"* (recent commit weak fráze), buyer čte: *„OK, artefakt = klikací prototyp = vlastnictví. Ale je to running prod, nebo deck?"*

### Recommendation: **Keep + reinforce**

Punchline keep. **Ale fix sekce 02b body** (P0 #1 výše): replace *„klikací prototyp"* → *„běžící produkt"*. Pak punchline *„artefakt = vlastnictví"* dostává konkrétní backing: artefakt = běžící produkt = vlastnictví. Match s user claim.

**Alternative punchline (NOT recommend, just for comparison):**

CS: *„Specka je nájemné. Hotový produkt je vlastnictví. Pflanzer staví produkty."*
EN: *„A spec is rent. A shipped product is equity. Pflanzer ships products."*

Tahle varianta je STRONG, ale ztrácí poetic ambiguity *„artefakt"* (a duplicates *„product/produkt"* z hero). Doporučuji **NEbrat** — keep current punchline s reinforced kontextem v sekci 02b body.

---

## 7. Aggregate score & summary

| Soubor | Strong mentions | Mid mentions | Weak mentions | Net verdict |
|--------|-----------------|--------------|---------------|-------------|
| `website/index.html` (hero, sekce 00, 01, 02, 02b, 03, 04) | 6 | 6 | 5 | **MIXED** — hero a sekce 04 STRONG, sekce 00 a 02b drag down |
| `website/1-pager.html` | 3 | 3 | 0 | **STRONG** — žádný weak (best v corpusu) |
| `README.md` | 3 | 2 | 2 | **MIXED** — lead-in (ř. 5) weak, ostatní STRONG |
| `docs/methodology/00-tldr.md` | 0 | 1 | 6 | **WEAK** — worst v corpusu |
| `docs/methodology/00-lean-pflanzer.md` | 2 | 2 | 0 | **STRONG** |
| `docs/case-studies/eshop-2026.md` | 3 | 2 | 0 | **STRONG** (`*„většina kódu … ne re-impl"*` pattern model) |
| **TOTAL** | **17** | **16** | **13** | **MIXED, leaning WEAK na audit-grade audience** |

### Critical insight

**Buyer journey hypothesis:**

1. Persona A (bank CTO) přijde na index → čte hero STRONG → klikne *„Open the 1-pager"* → 1-pager STRONG → klikne do repa → README ř. 5 WEAK *„1–3 funkční prototypy"* → otevře `00-tldr.md` (management 1-pager) → WEAK *„AI generuje 1–3 mockupy"*, *„klikací prototyp v sandbox VPC"*, *„Throw-away je default"*.

   **Buyer dropoff point:** README ř. 5 nebo 00-tldr.md. Confidence loss.

2. Persona B (eshop VP Eng) přijde na index → čte hero STRONG → scrolluje na sekci 02b → čte *„funkční klikací prototyp od hodiny 1"* (náš recent commit) → mentální alignment s Bolt/v0 (prototype tools) → comparison matrix *„3 prototyp · prod kód"* → klasifikuje Pflanzer = *„cool but ne pro nás, my už máme Bolt"*.

   **Buyer dropoff point:** sekce 02b weak fráze + comparison matrix output cell.

### Top 5 P0 fixes (priority order)

1. **`website/index.html:2077,2082`** — replace *„funkční klikací prototyp od hodiny 1"* → *„běžící produkt od hodiny 1"*. (Persona B critical.) **Náš vlastní recent commit fix.**
2. **`docs/methodology/00-tldr.md` ř. 17, 29, 33, 44, 50** — replace *„mockupy"*, *„klikací prototypy"*, *„P2P (Prototype-to-Prod)"* napříč dokumentem. (Persona A critical — audit-grade dokument je 1. místo, kam Persona A jde po hero.)
3. **`website/index.html:2173`** + **`:2293`** — Comparison matrix output cell + Field Notes Receipty cell: replace *„3 prototyp"* → *„3 funkční varianty"* (output) / *„3 funkční varianty"* (receipty). Drop *„prototyp"* slovo z buyer-facing tabulek.
4. **`README.md:5` + 6 výskytů „většina kódu"** — replace *„1–3 funkční prototypy"* → *„1–3 funkční varianty produktu"*; replikovat e-shop pattern *„kód jde do produkce, ne jako reference pro re-implementaci"* místo holé *„většina kódu"*.
5. **`docs/methodology/00-tldr.md:80` + `README.md:91`** — Redefinovat *„throw-away default"*: throw-away NE-default, je to opt-in exception. Per user claim explicit.

---

## 8. Appendix — Glossary recommendations summary

| Term | Current usage | Recommendation |
|------|---------------|----------------|
| *prototyp / prototype* | 9× v corpusu, často jako synonymum pro *„output Session 1"* | **Drop slovo úplně z buyer-facing copy.** Use *„varianta"* / *„funkční produkt"* / *„běžící aplikace"*. *„Prototyp"* keep jen tam, kde dynamically srovnáváme s SDD/Design Sprint (*„our 3 working products vs their high-fidelity prototype"*) — tj. as differentiator, ne self-identifier. |
| *mockup / mock-up* | 4× v 00-tldr.md, 2× v sekci 00 manifesto (jen jako kontrast *„ne mockup v Sketch"*) | **Drop self-applications.** Keep jen jako negative contrast (*„ne mockupy v Figmě"*). |
| *artefakt / artifact* | 8× v corpusu | **Keep** s anchored meaning *„běžící produkt, ne spec"*. Inline glossary v sekci 02b. Hero & sekce 00 použít *„produkt"* místo *„artefakt"*. |
| *handoff* | 6× v corpusu | **Audit per occurrence.** *„Handoff package"* = OK kdy explicit *„PR-ready commit"* + *„odkazy na soubory"* hned vedle. Standalone *„handoff"* = drop, zní jako paper-spec. |
| *většina kódu / most of the code* | 6× v corpusu | **Replikovat e-shop pattern** (*„kód jde do prod, ne jako reference pro re-implementaci"*) — kvalifikuje *„většina"* jako *„fixes during deploy"*, ne *„throw-away rest"*. Nebo dropnout slovo *„většina"* úplně. |
| *throw-away* | 3× v corpusu (00-tldr ř. 80, README ř. 91, ADR-0009 implicit) | **Redefinovat NEdefault.** Throw-away = explicit opt-in pro 3 named výjimky (hackathon, marketing one-off, Innovation Day demo). Default = ship-to-prod. |
| *clickable / klikací* | 5× v corpusu | **Keep, ale always pair s *„deployed" / „running" / „shippuje k mergi"*.** *„Klikací prototyp"* sólo = weak. *„Klikatelná běžící aplikace v sandbox URL"* = OK. |
| *skeleton (API skeleton)* | 2× v sekci 00 manifesto | **Drop.** *„Skeleton"* connotes *„kostra, kterou někdo doplní"* — opak user claim. Replace *„API skeleton"* → *„API endpointy"* / *„REST/GraphQL endpointy"*. |

---

## 9. Final note — self-honest

Tento audit byl objednán **po** našem vlastním nedávném commitu 3f46410 (sekce 02b Past spec-drivenu + punchline + Anthropic Engineering quote). Při review **jsme do produkčního copy zavedli 2 nové weak fráze** (ř. 2077 + 2082, CS+EN = 4 strings):

> *„Funkční klikací prototyp od hodiny 1. Security, Legal, DPO čtou ten samý URL, ne PDF se speckou."*

Sekce, kterou jsme designovali jako **anti-SDD punch** (*„artefakt > spec"*), současně sama říká *„funkční klikací prototyp"*. To je logická díra. Per user claim by sekce 02b měla říkat:

> *„**Běžící produkt od hodiny 1.** Security, Legal, DPO čtou ten samý URL, ne PDF se speckou. Specka se generuje **po** sezení jako audit log, ne před."*

Tím sekce 02b match s user claim a zároveň punchline *„Pflanzer staví artefakty"* dostává konkrétní obsah: artefakt = běžící produkt = vlastnictví.

**P0 #1 (výše) je oprava našeho vlastního recent commitu.**

---

*Konec auditu. Pro implementaci doporučení viz P0 priority list § 7.*
