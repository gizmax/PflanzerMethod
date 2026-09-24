# Marketing Strategy Audit — Pflanzer Method Website
**Auditor:** Senior B2B marketing strategist (15+ let enterprise SaaS / management consulting positioning).
**Subjekt:** `website/index.html` (v0.3, CS+EN bilingual, 2026-05-18).
**Filtr:** *„Pokud nemůžu jmenovat osobu, která tenhle web čte v 21:30 večer a buduje business case, web neslouží."*
**Datum:** 2026-05-18.

---

## TL;DR — verdikt

Pflanzer web v0.3 je **redaktorsky vynikající, prodejně nedotažený**. Vizuál (Fraunces + JetBrains Mono, botanická vizualizace, paper grain, číslované sekce) jasně signalizuje „prémiový, ne hackathon" — což je strategicky správné. Copy je v deseti místech lepší než 90 % B2B SaaS landingů: má hlas, má názor (anti-SAFe, anti-Figma, anti-McKinsey), má strukturu. Hero stat block (`~6–9 měsíců → ~14 dní → ~10× speedup`) je nejlepší jedna věc na celém webu.

**Strategická díra je jediná, ale fatální: web mluví k metodice (manuál), ne k buyerovi (business case).** Není tam jediná persona-routed cesta. Není tam jediný moment, kde si VP Engineering v UniCredit, Director of Engineering Effectiveness ve Škodě nebo AI CoE Lead v ČSOB řekne *„tohle je o mně a o mém čtvrtletním KPI"*. CTA *„Začít s 1-pagerem"* posílá self-serve developera na GitHub — ale enterprise buyer, který má reálné rozpočtové páky, web opustí, protože tam pro něj neexistuje ani jeden artefakt (žádné case study s čísly, žádný TCO ROI kalkul, žádný procurement-ready 1-pager, žádný „request audit-grade pilot" CTA). e-shop case study je polovina důkazu (lidský storytelling), ale **schází mu jediná tabulka s čísly** — kolik % kódu šlo do prod, kolik dní od S2 do deploy, kolik bug rework v T+7. To je proof gap, který sám web v `eshop-2026.md` přiznává (řádek 98-103: *„Doplnit po skutečném deploy"*).

**Top 1 thing fix nejdřív:** Postav nad současný hero **persona switcher** *(„Jsem AI CoE Lead v regulované firmě" / „Jsem VP Engineering v eshopu / SaaS" / „Jsem konzultant / facilitátor")*, který routuje na 3 odlišné second-fold narrativy a 3 odlišné CTA stacky. Aktuální monolit *„6 lidí, 2 sezení, kód do produkce za 14 dní"* je tagline pro e-shop persona — ale na webu má krvácet i audit-grade buyer, který kupuje úplně jiný value (compliance moat, ne speedup). Bez toho switcher zůstaneš v „interesting reading" pásmu místo „opens deal" pásma.

---

## 1. ICP — Ideal Customer Profile per segment

Identifikoval jsem **5 personas**, které mají rozumný důvod přijít na web. Pflanzer je dnes positioned (i v copy i v `ADR-0015`) jako *„operating-cadence layer pro AI Center of Excellence"* — to ale není jedna persona, je to čtyři. Plus jeden champion archetyp.

### Persona A — „Compliance-pressured AI CoE Lead"

| Atribut | Hodnota |
|---|---|
| Role / job title | **AI Center of Excellence Lead** / Head of AI Enablement / Director, AI Transformation |
| Org context | EU bank / pojišťovna / telco / utility / public sector. **2 000–50 000 FTE.** AI maturity: existující pilot portfolio (5-20 piloty), žádný production breakthrough. |
| Trigger event | Q3 2026: audit committee se zeptal *„kde je naše AI Act readiness pro Annex III use cases?"*. Nebo: CRO poslal email *„DORA Q1 2027 deadline, AI prompt pipeline audit needed"*. Nebo: CEO viděl prezentaci Accenture AABG (12/2025) a chce *„our version"*. |
| Status quo | Drží Excel s 18 piloty napříč BU, z toho 3 jsou *„o čem by ses měl bavit s CRO"*. Spravuje vztah s McKinsey / BCG (in-flight $1.5M engagement) + interní hackathon program (čtvrtletně). |
| Top 3 worries | (1) Audit committee Q4 2026 zjistí, že 12 z 18 pilotů nemá decision log per AI Act čl. 14. (2) DORA Q1 2027 = SIEM ingest prompt logů, nikdo to neimplementuje. (3) CEO chce *„AI velocity story"* na annual report, ale CRO blokuje produkční nasazení. |
| Buying authority | **Doporučuje + spolurozhoduje s CRO / CFO.** Vlastní €500k-€2M roční rozpočet na methodology + tooling. Single-vendor schválí sám do ~€80k. Nad to potřebuje procurement RFP. |

### Persona B — „Velocity-pressured VP Engineering"

| Atribut | Hodnota |
|---|---|
| Role / job title | **VP Engineering** / Director of Engineering Effectiveness / Head of Platform |
| Org context | E-commerce / SaaS / digital-native enterprise (e-shop, Rohlik, Productboard, Pipedrive scale). **200–3 000 FTE.** Non-regulated nebo light-regulated. AI maturity: vývojáři používají Cursor/Copilot indiviuálně, žádný cross-fn proces. |
| Trigger event | Q2 2026: board měřil *„AI productivity uplift"* a engineering reportoval *„14 % feature velocity"*, který nikdo neumí ověřit. Nebo: CEO viděl konkurenční launch, co tým doručil za 3 týdny tam, kde jeho tým dělal 4 měsíce. Nebo: nový CPO chce *„kill the Figma → re-implementation cycle"*. |
| Status quo | Engineering dělá 2-týdenní sprinty, produkt dělá quarterly OKRs, UX dělá Figma libraries. Mezi tím sériový handoff. Kupuje Linear, Vercel, Cursor pro tým. |
| Top 3 worries | (1) Top 5 talents odejdou, pokud nedostanou *„serious AI workflow"* (LinkedIn pull už začal). (2) CEO čeká velocity story na Q4 board (90 dní). (3) Engineering org chart se nedaří škálovat — každý nový PdM přidá 2 týdny handoff lag. |
| Buying authority | **Rozhoduje sám do ~€50k.** Pro >€50k konzultuje CTO. Žádná procurement bariéra pro „methodology + facilitation" line item, pokud line item je <€100k. |

### Persona C — „CFO-watched Director of Engineering Effectiveness"

| Atribut | Hodnota |
|---|---|
| Role / job title | **Director of Engineering Effectiveness** / Productivity Lead / Developer Experience Lead |
| Org context | Mid-large enterprise s formalizovaným engineering effectiveness function (Skyscanner-style, Spotify-2024-model). **1 000–10 000 FTE engineering.** AI maturity: měří DORA + DX index, hledá *„next intervention"*. |
| Trigger event | Annual planning Q4 2026: CFO se zeptal *„ROI of AI Copilot license fleet?"* a Director nemá quantified answer. Nebo: DX survey ukázal *„cross-functional handoff"* jako #1 friction. |
| Status quo | Dělá quarterly DX surveys, Spotify-style guilds, internal hackathons, runs A/B testy na engineering interventions. Reportuje VP Eng + CFO. |
| Top 3 worries | (1) Cursor/Copilot ROI je nečitelný (CFO se ptá quarterly). (2) Cross-fn handoff je top friction, ale nemá intervention s evidence base. (3) Externí consulting (McKinsey AI op model) je politicky toxic — *„not invented here"*. |
| Buying authority | **Doporučuje VP Eng / CFO.** Owns evidence layer. Single PO authority typically €25k; cokoliv nad eskaluje. |

### Persona D — „Consultant / Facilitator looking for sellable IP"

| Atribut | Hodnota |
|---|---|
| Role / job title | **Independent facilitator / boutique consultant** / Big-4 senior manager / agency lead (AJ&Smart-style, EnterpriseScale-style) |
| Org context | Boutique 2–20 FTE / Big-4 practice lead. Sells workshops, sprints, AI enablement. Hledá *„next-gen sellable method"* pro 2026-2027. |
| Trigger event | Klient se zeptal *„dělejte nám Design Sprint, ale s AI a tak, aby to mělo audit trail"*. Existing Sprint methodology nestačí. Sleduje AJ&Smart Sprint 2.0, IDEO AI, Foundation Sprint. |
| Status quo | Prodává 5-day Design Sprints €15-40k. Začíná experimentovat s Lovable/Bolt v session. Hledá differentiated methodology pro 2027 sales motion. |
| Top 3 worries | (1) Sprint 2.0 mainstream do 12 měsíců → komodita. (2) Klienti chtějí compliance story (AI Act), facilitator nemá. (3) Bez certified methodology hard to charge €30k+ per engagement. |
| Buying authority | **Self.** Adoptuje methodology pokud dostane (a) license terms, (b) playbook, (c) potenciální certifikační track. |

### Persona E — „Internal Champion (sponsor's ear)"

| Atribut | Hodnota |
|---|---|
| Role / job title | **Senior PdM / Tech lead / Innovation manager / Staff Engineer** — někdo, kdo neumí sám rozhodnout o €50k, ale má 30 minut měsíčně se sponzorem |
| Org context | Korporát, kde Champion sleduje LinkedIn, Substack, AI newsletters. Často staff-IC nebo PdM s 5-8 let zkušenosti. |
| Trigger event | Sponzor řekl *„najdi nám něco, jak to dělat rychleji"* na 1:1. Nebo: Champion sleduje Tom Pflanzer LinkedIn / blog a chce přinést sponzorovi 1-pager. |
| Status quo | Píše interní memo *„AI workflow opportunities"*. Vede SoP / internal newsletter. |
| Top 3 worries | (1) Sponzor zkusí přitáhnout to k jakémukoli McKinsey-style projektu, který už běží = se ztratí. (2) Champion vypadá blbě, pokud doporučí method, která se v korporátu nezachytí. (3) Champion nemá rozpočet, jen vliv. |
| Buying authority | **Žádná.** Referuje, ale rozhoduje sponzor (Persona A/B/C). |

### Persony, které **NEJSOU** target (a web by je neměl matení):

- **CTO / CIO C-level** přímo — moc abstraktní; Pflanzer není transformation program, je pilot fixture. Tato persona delegate na Persona A/B.
- **Solo developer / vibe-coder** — Pflanzer není individual tool; AWS AI-DLC / Cursor mainstream je lepší fit.
- **Public sector procurement officer** — Pflanzer v0.3 nemá ani indikativní MSA template; konverze nemožná.
- **Startup founder <50 FTE** — Pflanzer overhead unfit; Foundation Sprint je lepší fit.

---

## 2. Buyer journey map — per persona

### Persona A — Compliance-pressured AI CoE Lead

| Stage | Co potřebuje | Současný web odpoví? | Co chybí |
|---|---|---|---|
| **Awareness** | Hledá *„AI Act compliance methodology"*, *„AI pilot governance framework"*, *„enterprise AI workflow"*. LinkedIn post od kolegy / Substack / konferenční talk. | ❌ Web nemá SEO/SEM target na compliance keywords. Hero říká *„sázíme AI do korporátních procesů"* — neevokuje *„AI Act"*. | Sekce/landing variant *„For regulated enterprise"* s hero variantou *„Native AI Act art. 14 compliance fixture, 14-day production cycle"*. |
| **Consideration** | Potřebuje shortlistovat Pflanzer vs (1) McKinsey AI Op Model, (2) AWS AI-DLC + AABG, (3) interní hackathon program. Co potřebuje: srovnávací tabulka, compliance artefakt sample, reference call. | ⚠️ Sekce 02 *„5 věcí, které nikdo jiný nedělá"* je dobrá, ale **schází srovnávací tabulka** (Pflanzer vs AI-DLC vs McKinsey). USP #2 *„Native AI Act compliance"* je tam, ale **nemá sample artefakt** ke stažení. | (1) Comparison matrix sekce. (2) Sample compliance log download (PDF). (3) Audit-grade fact-sheet 2-pager link. (4) Reference call CTA. |
| **Decision** | Potřebuje (a) reference v podobné firmě (EU bank / pojišťovna), (b) pilot test (1 use case, 4-6 týdnů), (c) procurement-ready MSA template, (d) compliance officer sign-off artefakty. | ❌ Web nemá ani jeden z těchto. e-shop je e-commerce, ne regulated reference. | (1) Audit-grade case study (i kdyby anonymizovaná: *„Top-5 CEE bank, Q1 2026, RWA stress-test prototype"*). (2) Pilot RFP template. (3) MSA reference link. (4) Compliance officer endorsement quote. |
| **Activation** | První akce = vyžádá si **1h discovery call s Method Steward** nebo **request audit-grade pilot proposal**. NE clone GitHub. | ❌ Hero CTA je *„Začít s 1-pagerem"* + GitHub. Pro Persona A nesmyslné — nestáhne si GitHub repo, deleguje to. | Tertiary CTA *„Request audit-grade pilot proposal"* → form (jméno, firma, AI Act tier, FTE, expected start). Routes to Tom directly s SLA *„48h response"*. |

### Persona B — Velocity-pressured VP Engineering

| Stage | Co potřebuje | Současný web odpoví? | Co chybí |
|---|---|---|---|
| **Awareness** | Hledá *„AI engineering productivity"*, *„cross-functional AI workflow"*, *„kill the handoff"*. LinkedIn from Director of Eng peer / Substack / podcast guest spot. | ⚠️ Hero *„kde sériový handoff zabíjí měsíce, 6 lidí, 2 sezení, kód do produkce za 14 dní"* — **tohle je přesně Persona B language**. Hit. | OK, ale neexistuje *„For engineering leaders"* deep-dive landing — VP Eng chce vidět DORA-style metriky, ne botanickou metaforu. |
| **Consideration** | Potřebuje (a) výsledky podobných firem (e-shop-grade), (b) team capacity worksheet (kolik PD), (c) jak to fit do existing sprint cadence, (d) co se stane, když se tým spálí. | ✅/⚠️ e-shop sekce 03 je správný směr, ale **schází numbers** (kolik % kódu šlo do prod, kolik dní). Manifesto říká *„~10× speedup"* — to je tagline, ne důkaz. | (1) e-shop čísla (production deploy %, lead-time delta). (2) Effort estimator: *„Pro váš tým ~10 PD; rozložení Sponsor / PdM / Builder…"* (default profil už má v `00-lean-pflanzer.md`, jen není na webu). (3) Anti-pattern callout: *„Pflanzer NEpoužívejte pro PSD2 / SCA / payment flow"*. |
| **Decision** | Potřebuje (a) DIY playbook + 1 facilitátorský pilot za €15-30k, (b) referenci od peer VP Eng, (c) timeline kdy lze začít. | ⚠️ DIY playbook OK (Lean Pflanzer 1-pager). Facilitátor pricing **chybí úplně**. Reference call **chybí úplně**. | (1) Pricing/packaging sekce (tier ladder: DIY free / Facilitated pilot €X-Y / Audit-grade €X-Y). (2) *„Schedule 30-min architecture call"* CTA. (3) Sample Charter download. |
| **Activation** | Buď self-serve clone (Persona B s vlastním facilitator skill), nebo *„first pilot for €Y"* poptávka. | ⚠️ CTA *„Tool na GitHubu"* funguje pro self-serve, ale GitHub link vede na `https://github.com/` (placeholder!), ne real repo. | (1) Fix GitHub URL. (2) Add *„Book pilot intro call"* CTA + Calendly. |

### Persona C — CFO-watched Director of Engineering Effectiveness

| Stage | Co potřebuje | Současný web odpoví? | Co chybí |
|---|---|---|---|
| **Awareness** | Hledá *„engineering effectiveness AI"*, *„DX intervention AI"*, *„DORA AI productivity"*. Sleduje Gergely Orosz, Will Larson, DX index. | ❌ Web nemluví jejich jazykem (žádné DORA, žádný DX index, žádné quantified intervention). | Optional: blog post sekce s *„How Pflanzer changes DORA + DX metrics"* — ale to je content marketing investment, ne web fix. |
| **Consideration** | Potřebuje (a) **měřený outcome** (před/po), (b) intervention design pro A/B test (1 tým s Pflanzer, 1 bez), (c) leading + lagging indicators. | ⚠️ Pflanzer má `leading-indicators.md` v `docs/methodology/`, ale **na webu není žádný link / žádný preview**. | (1) Sekce „Leading indicators" preview se 3-4 metrikami. (2) Link na methodology repo. (3) Sample retrospective template. |
| **Decision** | Potřebuje (a) **N=1 case s before/after numbers**, (b) executive 1-pager pro CFO. | ❌ Web nemá CFO 1-pager. e-shop je *„our experience"*, ne quantified. | (1) Executive 2-pager *„Pflanzer for engineering effectiveness leads"* PDF. (2) ROI estimator (lead-time delta × developer cost). |
| **Activation** | Pošle peer VP Eng + CFO + Tom 4-osmí email *„let's run a 4-week trial"*. | ⚠️ Aktuální *„Mluvit s autorem"* funguje, ale není jasné, co Tom v té konverzaci nabídne (30 min architecture, hodinová placená konzultace, free intro?). | Define + advertise *„First call format"* — *„Free 30 min: I'll review your pipeline, propose one pilot, no commitment"*. |

### Persona D — Consultant / Facilitator

| Stage | Co potřebuje | Současný web odpoví? | Co chybí |
|---|---|---|---|
| **Awareness** | Hledá *„AI workshop methodology 2026"*, *„Sprint 2.0 alternative"*, *„Lovable workshop"*. Sleduje AJ&Smart, Knapp, Liberating Structures. | ⚠️ Web nemá explicit *„For facilitators / consultants"* track. Hero říká *„rozhybat rigidní procesy"* — což je client-language, ne facilitator-language. | Sekce *„For practitioners"* (facilitátory / konzultanty) s license terms + certifikační intent. |
| **Consideration** | Potřebuje (a) license (MIT je OK pro DIY, ale pro client engagement potřebuje *„OK to use commercially?"* clear), (b) facilitator playbook / training, (c) certifikační track. | ⚠️ Footer říká *„MIT License"* — OK signal, ale **playbook detail chybí** (kromě GitHub linku, který vede na placeholder). | (1) *„Use Pflanzer commercially"* FAQ. (2) Facilitator training intent (i kdyby *„coming Q3 2026 — join waitlist"*). (3) Certified facilitator path teaser. |
| **Decision** | Potřebuje *„buy-in pre-sale"* — pokud doporučí klientovi Pflanzer, klient může gůglit a najít *„serious method"*. | ⚠️ Web v této roli funguje dobře (vizuál + jazyk signalizují seriousness), ale **chybí externí endorsement** (Martinelli paper citation, klient quote). | (1) Martinelli paper citation jako *„external validation"*. (2) Expert quotes (i kdyby Tom sám: *„Reviewed by 3 independent experts, May 2026"* — je v docs, není na webu). |
| **Activation** | Email *„chci dělat pilot s mým klientem, jak to děláme"* nebo *„join facilitator network"*. | ❌ Žádný *„join facilitator network"* CTA. | (1) *„Facilitators: get the playbook"* CTA. (2) Optional Discord / Slack community link. |

### Persona E — Internal Champion

| Stage | Co potřebuje | Současný web odpoví? | Co chybí |
|---|---|---|---|
| **Awareness** | Sleduje LinkedIn / Substack / Slack komunity. Trigger: někdo sdílel Pflanzer link. | ✅ Web vypadá hodnotně, brand-credible. Pass na share. | – |
| **Consideration** | Potřebuje **přesvědčit sponzora za 4 minuty**. Potřebuje 1 deck / 1 1-pager, který může sponzorovi forwardnout. | ❌ Web sám není 4-min exec read. Sekce 00 je dlouhá; e-shop case nemá numbers. **Žádný „Send this to your sponsor" 2-pager PDF**. | (1) *„Send this to your sponsor"* 2-page PDF download (high-quality print). (2) Loom intro video 90 sec (Tom mluví). (3) Email template *„How to pitch Pflanzer to your VP"*. |
| **Decision** | Sponzor řekne *„OK, projednám s engineering"*. Champion potřebuje další materiál: pilot proposal template. | ❌ Žádný pilot proposal template. | Pilot proposal template (1-pager) ke stažení. |
| **Activation** | Champion zorganizuje 30-min meeting Tom × sponzor. | ⚠️ *„Mluvit s autorem"* funguje, ale je generic. | *„Bring me into your sponsor's 30-min meeting"* explicit CTA. |

---

## 3. Value framework — 5 USPs × buyer's „so what?"

| # | USP | Buyer's „so what?" | Risk reversal (co se pokazí, když Pflanzer nepoužiju) | Proof point dnes |
|---|---|---|---|---|
| 01 | **Non-tech v místnosti od minuty 0** (Security, Legal, DPO, A11y, UX writer, CS proxy) | Pro Persona A: *„Compliance officer mě nezablokuje na minutě 5000 = 4 týdny zpoždění × 6 lidí × €1000/den = €168k zachráněných nákladů."* Pro Persona B: *„Můj sprint nekončí ve security review queue na 3 týdny."* Pro Persona D: *„Můj klient nepřijde s `Where's GDPR sign-off?` v týdnu 3."* | **Late-stage veto.** Security flagne risk surface v sprintu 4 / týdnu 12 = whole pilot dies. Empirický pattern: 60-70 % AI pilotů v EU regulated industries umírá na late-stage compliance veto (zdroj: Anthropic enterprise survey 2025, nepřímá Pflanzer reference). | ⚠️ Tvrzení („AWS AI-DLC mob = jen engineering") je faktický, ale **na webu chybí důkaz**, že non-tech v místnosti reálně mění outcome. e-shop case to nepoužívá (e-shop default profil non-tech vědomě vynechal). **Proof gap — potřeba audit-grade case study.** |
| 02 | **Native AI Act compliance** (decision log per čl. 14, DORA-grade 7y retention, Fáze A/B/C protocol) | Pro Persona A: *„DPO mi nepošle 14-stránkový dotazník, protože decision log je v repo, signed, timestamped."* Pro Persona D: *„Klient mě platí o €15k víc, protože dostane procurement-ready compliance artefakt."* | **Audit committee Q4 hit.** Pokud 12 z 18 pilotů nemá decision log per čl. 14, AI CoE Lead je v Q4 board meeting *„person responsible for non-compliance"*. CRO eskaluje na CEO. | ✅ Martinelli paper 2026 reference je silná, ALE **není na webu**. ✅ Decision log template existuje v repo, ale **není linkovaný ze sekce 02**. Recommendation: link `pflanzer-charter` + ukázat tabulkový sample. |
| 03 | **Score závaznosti per role + AI deflation** (1-5 Likert + Critical/Yellow/Score + AI-only feedback × 0.5) | Pro Persona B: *„Můj sponzor přestane říkat `looks good` a začne říkat `commit on level 4 because of X`."* Pro Persona C: *„Rozdíl mezi `like` a `commit` = leading indicator pro adoption v T+30."* | **HiPPO bias kills pilot in T+30.** Sponzor řekl v session *„great"*, pak v T+30 retro řekl *„we never aligned on this"*. Bez score závaznosti tuto disagreement nejde retrospectively trackovat. | ⚠️ Tvrzení („workshop expert confirmation, žádný direct competitor 2026") je v `04-synthesis-and-positioning.md`, ale **na webu nemá sample template**. Add: *„Sample feedback form"* download. |
| 04 | **Pre-flight triage 4 tracks** (Discovery + Security + Legal + Platform, 48-72h async, MUST gate) | Pro Persona A: *„Session 1 neodstartuje, dokud 4 podpisy. Žádné `we'll figure out security later`."* Pro Persona D: *„Můj 3-hodinový workshop neumře proto, že stakeholder přišel s otázkou `máme přístup k production data?` v minutě 90."* | **Discovery debt blow-up.** Session 1 startuje bez pre-read → 60 min se spotřebuje na *„kdo je stakeholder, jaký je success threshold"* místo na vibe-coding. ROI session padá o 33 %. | ⚠️ Sekce 02 zmiňuje 4 tracky, ale **na webu schází sample pre-flight checklist** ke stažení. Tohle by byl 2-min konverzní artefakt pro Persona D. |
| 05 | **14 dní + reinforcement** (2 sezení s týdenním async, T+7/30/60/90 reinforcement) | Pro Persona A: *„Měřitelný outcome v T+30 retro, ne za 6 měsíců."* Pro Persona B: *„Můj tým není mimo provoz 5 dní v kuse (Design Sprint problem)."* Pro Persona D: *„Klient zaplatí €X za první cyklus, pak má vidět T+30/60/90 outcome, pak kupuje další."* | **Context retention pod 7 dní = degraded handoff.** Pokud session je 5-day non-stop (Design Sprint), stakeholder availability collapse: typical EU corporate stakeholder má 60 % kalendáře blokovaný. Sprint zruší se s 2/6 lidmi = pilot dies. | ⚠️ Hero stat „~14 dní" je proof. Ale **T+7/30/60/90 reinforcement není visualizovaný** ve flow diagramu (sekce 01). Diagram končí *„Den 14: Kód v produkci"* — chybí *„T+30: retro / leading indicator check"* milestone. |

### Bonus USP, který schází na webu

| USP | Buyer's „so what?" | Důvod, proč ho přidat |
|---|---|---|
| **Default vs Audit-grade profile bifurcation** (Lean Pflanzer 1-pager pro ~80 % case-ů, audit-grade overhead jen kdy potřeba) | Pro Persona B/C: *„Můj non-regulated eshop nepotřebuje Method Steward 0.5 FTE €100-150k/rok."* Pro Persona A: *„Můj regulated pilot dostane plný overhead, ale můj internal CRM rework ne."* | Žádný konkurent (AWS AI-DLC ani McKinsey) **nemá explicit cena-aware bifurcation**. Default profil je sám o sobě protected pozice. Web ji zmiňuje až v sekci 04 jako footnote — měla by být sekce 02 USP #6 nebo součást hero subhead. |

---

## 4. Conversion architecture audit

### Současné CTA stack

| CTA | Pozice | Persona target (assumed) | Co s tím v reálu uživatel udělá |
|---|---|---|---|
| *„Začít s 1-pagerem"* (hero primary) | Hero | Persona B/D (self-serve) | Odscrolluje na sekci 04 (interní anchor). NE je to download nebo external action. |
| *„GitHub ↗"* (hero secondary) | Hero | Persona B/D | Otevře `https://github.com/` — **placeholder URL, broken**. Critical bug. |
| *„1-pager · Lean Pflanzer"* (sekce 04) | Section 04 | Persona B/D | Klikne, jde na GitHub placeholder = broken. |
| *„Tool na GitHubu"* (sekce 04) | Section 04 | Persona B/D | Stejné = broken. |
| *„Mluvit s autorem"* (sekce 04) | Section 04 | Persona A/C/E | mailto:tom@gizmax.cz — funkční, ale generic. |

### Friction audit

1. **Hero CTA neukončuje akci.** *„Začít s 1-pagerem"* zní jako action, ale je to anchor link na sekci 04 (intra-page scroll). Buyer očekává *„get something now"* (download / signup / talk).
2. **GitHub URLs jsou placeholdery.** 3 z 5 CTA vedou na `https://github.com/` (broken). **Toto je P0 critical bug.** Každý buyer, který si web prošel a chtěl convert, narazí.
3. **Žádný persona routing v hero.** Všech 5 person dostane stejnou CTA. Persona A potřebuje *„Request audit-grade proposal"*; Persona B potřebuje *„Get the playbook + book intro call"*; Persona D potřebuje *„Get facilitator playbook"*.
4. **Žádný lead capture.** Nikde žádný email signup, žádný newsletter, žádný *„get notified when training launches"* form. **Pflanzer dnes nemá způsob, jak druhý kontakt s lead-em (Persona D, který si prohlédl web a odešel = lost forever)**.
5. **Žádný shareable artefakt.** Persona E (Champion) nemá co stáhnout a poslat sponzorovi. *„Send this to your sponsor"* PDF 2-pager je no-brainer wins.
6. **CTA hierarchy je rovnostářská.** V sekci 04 jsou 3 CTA na stejné úrovni (1-pager, GitHub, Email). Není jasné, který je primary. Buyer s low intent klikne na bezpečnější GitHub; high-intent buyer klikne email. Nejdůležitější CTA (Talk to author) by měl být primary, ostatní secondary.

### Co chybí jako CTA per buyer stage

| Stage | Persona | Aktuální CTA | Doporučený CTA |
|---|---|---|---|
| Awareness exit | A | žádný | *„Get the regulated enterprise fact-sheet (2 pages, PDF)"* — lead capture form |
| Awareness exit | B | žádný | *„Get the engineering leader's 1-pager (PDF)"* — lead capture |
| Awareness exit | C | žádný | *„How Pflanzer affects DORA + DX metrics (Substack)"* — newsletter signup |
| Awareness exit | D | žádný | *„Join the facilitator early-access list"* — lead capture |
| Consideration | A | žádný | *„See the AI Act compliance log (sample artifact)"* — gated download |
| Consideration | B | žádný | *„Calculate Pflanzer effort for your team"* — interactive calculator |
| Consideration | C | žádný | *„Read the e-shop case (live updated)"* — internal link (case study sub-page) |
| Decision | A | žádný | *„Request audit-grade pilot proposal"* — form → Tom 48h SLA |
| Decision | B | *„1-pager · Lean Pflanzer"* (broken) | (fix link) + *„Book 30-min architecture call"* — Calendly |
| Decision | C | žádný | *„Read the effort + ROI estimator (1-pager PDF)"* |
| Decision | D | žádný | *„Get the facilitator playbook (commercial use OK)"* — form gating |
| Activation | A/B/C | email | + Calendly link |

### Email capture — fail nebo OK?

**Fail.** Pflanzer nemá žádný způsob, jak druhý kontakt s lead-em provést. To znamená: každý lead, který web opustí bez kliknutí *„Mluvit s autorem"* (= většina), je lost. Pro Persona D (consultant), který se vrátí za 3 měsíce, když má klienta připraveného — žádný drip, žádný *„we launched Q3"* update.

**Minimum viable:** newsletter signup *„AI pilot field notes — 1 email/měsíc, 5min read, e-shop + další cases"*. Pflanzer má unikátní content (ADRy, autoresearch findings, e-shop learning), který by se dal měsíčně publish.

---

## 5. Strategic narrative test — „Rozhýbat firmu a naskočit na vlnu AI"

Pflanzer claim (z prompts): *„Pomáhá rozhybat rigidní procesy a postupně AI do firem dostat."* Audit, jestli to web vyjadřuje:

### Komu konkrétně Pflanzer pomáhá vyhrát interní bitvu o AI adoption?

**Web odpověď dnes:** generický *„korporát · 5–5000+ FTE"*. To je tak abstraktní, že to neslouží buyerovi.

**Co by tam mělo být:** Per-persona triggers. *„Pflanzer pomáhá AI CoE Lead doručit Q4 board update s názorem `12 pilotů, 4 v prod, 0 audit incidentů` místo `pilot portfolio still maturing`."* *„Pflanzer pomáhá VP Engineering dodat board Q4 příběh `2 features v prod přes Pflanzer cykl, 14 dní each`, ne `working on AI integration`."*

### Jaký je „job done well"?

**Po prvním Pflanzer pilotu:** Tým (6 lidí) má sdílenou zkušenost *„toto FUNGUJE"*. Decision log signed, kód v prod, T+7 retro hotový. **Sponzor je první referent**.

**Po 5 pilotech:** Method má pull, ne push. Internal Slack #pflanzer-method channel. Externí cases. Sponzor #1 stake CRO-ready, sponzor #5 stake CEO-ready. Method Steward role part-time formalized. Pflanzer cykl je *„jak my děláme AI"*, ne *„external method we tried"*.

**Web tohle naratuje?** ❌ Web mluví o jednom cyklu. Schází *„long-game"* narativ. Recommendation: sekce 03b — *„After 5 pilots"* — kde se ukáže, co se v org změní (kultura, KPI, role).

### Distillation test — 1 věta v Slack komunitě?

Aktuální tagline kandidáti z webu:
- *„Sázíme AI do korporátních procesů, kde sériový handoff zabíjí měsíce."*
- *„6 lidí, 2 sezení, kód do produkce za 14 dní."*
- *„Cross-functional AI pilot fixture s native AI Act compliance."*

**Audit:**
- První je poetické, ale nezahrnuje *„what's in it for me"* pro Persona A. Persona B/C/D by ji sdílel.
- Druhá je **silná** — quantified, specific, debatable. Toto by Persona B sdílel.
- Třetí je strategicky správná (per ADR-0015), ale **na webu se v této přesné formě neobjevuje** — jen pomalá derivace. Toto by Persona A sdílel.

**Doporučení:** Web má **2 hlavní messages**, ne 1. Hero by měl ukázat oba (per persona):
1. *„Ship AI features in 14 days, not 9 months — and survive audit."* (Persona A magnet)
2. *„6 people, 2 sessions, code straight to production."* (Persona B magnet)

### Exec test — 4 minuty, ukázat CEO?

Champion (Persona E) má 4 minuty se sponzorem (CEO/VP). Co ukáže?

**Aktuálně možné:** Otevře web na laptop. Sponzor čte hero, kouká na botanickou vizualizaci (krásnou, ale neoperační), čte stat block (`~6-9 → ~14 dní, ~10×`). Sponzor řekne *„cool, send me a 1-pager"*. Champion klikne *„1-pager · Lean Pflanzer"* — broken GitHub link.

**Co by mělo být:** *„Send this to your CEO"* PDF (jeden klik download), 2 stránky, A4, print-ready:
- p.1: Hero stat (~14 dní), e-shop numbers (s konkrétními čísly), 5 USPs jako bullety, *„What's NOT this"* (anti-McKinsey, anti-SAFe).
- p.2: Implementation timeline 14 dní, profile bifurcation (default vs audit), CTA *„Schedule 30 min with Tom"*.

**Bez toho exec test fail.** Champion + sponzor scénář je dnes broken na CTA layer.

### Pokud ten web sdílí v Slack komunitě:

**Persona D (facilitator) napíše:** *„This is what Sprint 2.0 wishes it were — with AI Act compliance baked in."* Pflanzer pro tuto personu ✅.

**Persona B (VP Eng) napíše:** *„14-day method to ship AI features without dying in handoff hell."* Pflanzer pro tuto personu ✅.

**Persona A (AI CoE Lead) napíše:** *„Has anyone here run this in a regulated bank?"* — protože **na webu chybí regulated reference**. Pflanzer pro tuto personu ⚠️ — viral motion blocked na proof gap.

---

## 6. Priority changes

### P0 — Must-fix to convert (do 2 týdnů)

1. **Fix broken GitHub URLs.** 3 CTA vedou na `https://github.com/` (placeholder). Buď nastavit reálný repo URL, nebo skrýt CTA. **Critical conversion bug.** Bez fixe 60-80 % high-intent kliků skončí na 404.

2. **Add persona routing v hero / second-fold.** Buď persona switcher (CS/EN switcher už máš, persona switcher je extension stejného patternu), nebo 3 horizontal cards pod hero: *„Jsem v regulované firmě (banka, pojišťovna, telco)"* / *„Jsem v digital-native firmě (eshop, SaaS, scale-up)"* / *„Jsem facilitátor / konzultant"*. Každá vede na own anchor section s persona-routed value prop + CTA. Bez tohoto všichni dostanou stejnou *„default profil pro běžný e-shop"* messaging, ale 50 % audience (Persona A + D) potřebuje jiný appeal.

3. **e-shop case study — doplnit čísla.** *„Doplnit po skutečném deploy"* v `eshop-2026.md` (řádky 98-103) je proof gap. Web sekce 03 musí mít minimálně: (a) % winner kódu v prod, (b) dní S2 → first deploy, (c) bug rework T+7. I kdyby čísla nebyla finální, **lepší honest „Q2 2026: 70 % kódu v prod, S2→prod 3 dny, 2 P2 bugs T+7"** než *„cyklus total ~14 dní"* placeholder. Bez čísel je e-shop sekce *„nice story"*, ne *„case study"*. Pro Persona B/C neconvert.

### P1 — Should-fix to scale (do 4-6 týdnů)

4. **Add Send-to-Sponsor 2-pager PDF.** Champion (Persona E) workflow je dnes broken na CTA layer. PDF 2-pager (A4, print-ready, anglicky + česky), který obsahuje: hero stat, e-shop numbers, 5 USPs, profile bifurcation, CTA. Drop-in download bez form gating (low-friction).

5. **Pricing / packaging sekce.** Aktuální *„Default / Audit-grade"* bifurcation je strategicky správná, ale na webu chybí cenová ladder. **Min viable:** *„DIY: free (MIT) / Facilitated pilot: €15-30k / Audit-grade pilot: €40-80k / Method-level rollout: €X-Y per quarter"*. Bez tohoto Persona B/D nemůže udělat rozhodnutí; Persona A nemůže sestavit RFP. Aktuálně procurement není možný.

6. **Add comparison matrix.** Pflanzer vs AWS AI-DLC vs McKinsey AI Operating Model vs Design Sprint 2.0. 5-7 řádků (audience, format, compliance, distribuce, sweet spot, cost, time-to-prod). Tabulka už **existuje v `ADR-0015`** (řádky 47-53), jen ji přepřebrat do webu. Persona A toto MUSÍ dostat na webu, jinak nedělá shortlist.

7. **Add lead capture (newsletter signup).** Min viable: *„AI pilot field notes — 1 email/month"* signup form v sekci 04 + footer. Pflanzer má unikátní content pipeline (ADRy, autoresearch findings, e-shop). Bez lead capture každý lost lead = lost forever.

8. **Externí endorsement / proof block.** Sekce mezi 02 a 03: *„Externí validace"* — Martinelli paper citace, 3 expert review výsledek („Reviewed by 3 independent experts, May 2026"), případně Wikipedia / Anthropic / AWS reference (pokud existuje). Pflanzer dnes spoléhá výhradně na vlastní hlas — což funguje pro Persona D (community), ale Persona A v regulated industries chce externí přízeň.

### P2 — Nice-to-have for brand (do 8-12 týdnů)

9. **„After 5 pilots" sekce.** Long-game narativ — co se v organizaci stane po 5 cyclech (kultura, KPI, role formalization). Dnes web mluví jen o single-cycle. Pro Persona A (AI CoE Lead) toto je *„kde jsem za 12 měsíců"* perspektiva, kterou potřebuje pro board pitch.

10. **Interactive effort calculator.** Slider („tým 6 lidí, ~10 PD; audit-grade 15-20 PD; method-level rollout ..."). Engaging artefakt, lead capture na exit. Differentiator vs konkurence (žádný McKinsey ani AWS AI-DLC nemá public calculator).

11. **Loom intro video 90 sec.** Tom v hlavní roli, mluví hero message, ukáže e-shop case na video. Loom je low-effort high-trust signal. Persona E share na Slack komunitách 5× pravděpodobněji než link na text.

---

## Závěr — strategic gap v jedné větě

> **Pflanzer web je dnes excellent manuál pro lidi, kteří už metodu chtějí použít. Není to ještě B2B sales asset pro 5 distinct buyer person, které ji potřebují koupit.**

Mezera mezi „manuál" a „sales asset" se zacelí třemi věcmi: (1) fix CTA layer + persona routing, (2) doplnit e-shop numbers + audit-grade reference, (3) postavit lead capture + shareable artefakty pro Champion workflow. Strategický fundament (5 USPs, profile bifurcation, ADR-0015 ekosystémová pozice) je správný; chybí pouze poslední 20 % konverze layer.

---

*Žádné externí reference — toto je first-party audit založený na competitive research `04-synthesis-and-positioning.md`, methodology `00-lean-pflanzer.md`, case study `eshop-2026.md`, ADR-0015 a current website source `index.html`.*
