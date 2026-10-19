# 03 — Facilitator (META): Pflanzerova metoda jako workshop architecture

## Kdo jsem

Senior Workshop Facilitator / Workshop Architect, 15+ let. 200+ Design Sprintů, LDJ, Lean Inceptions, Event Stormingů, plus 18 měsíců AI-augmented sessionů s Miro Sidekicks, Otter, Claude Code v live místnosti. Žiju z toho, že **stakeholdery přečtu rychleji než agendu** — vidím, kdy security mlčí proto, že nesouhlasí, kdy zadavatel "kýve" proto, že nechce ztratit minutu, kdy je tým ve flow vs. v sebepřesvědčování. Denní bolesti: stakeholdeři přijdou, nevyřeší se nic; silní přebíjejí tiché; AI tool zpomaluje místo zrychluje; sessiony končí bez akceptačních kritérií. Tahle perspektiva není o mé roli — je **o metodě jako architecture**.

## 1. Posouzení metody META

**Co Pflanzer dělá strukturálně dobře.** Dvě sessiony s prototypem mezi nimi řeší dvě Achillovky korporátu: Design Sprint je 5denní logistický blocker, LDJ je 60min mělčina. Pflanzer trefí střed — den+den s týdenní mezerou na rozmysl. Cross-functional od minuty 0 řeší valley of death. AI-mediovaná syntéza v Session 2 odstraňuje politickou interpretaci "co řeklo Eng".

**Co metoda strukturálně neřeší.** (a) **Žádný explicit decider model** — předpokládá konsensus, ale konsensus 8 lidí = paralýza nebo HiPPO maska. (b) **Energy curve chybí v designu** — 6 h "intenzivního vibekódování" ignoruje, že po 3 h kreativita kolabuje. (c) **Konflikt-resolution playbook chybí** — Security veto + zadavatel push = co dělám? (d) **AI-human dělba** je nedefinovaná: "AI vede výklad" buď znamená všechno nebo nic. (e) **Failure modes facilitátora** nejsou pojmenovány — přitom já jsem nejčastější bod selhání.

**Co mě ohrožuje.** Pokud "AI vede session 2", stávám se moderátor toolu. Druhé riziko: 12 perspektiv chce 30+ povinných vstupů (Charter, Threat model, OpenAPI, Design tokens, Event taxonomy, DPIA, SLO baseline...) — facilitátor s tímto checklistem **nikdy session nezačne**. Architektura musí degradovat gracefully.

## 2. Energy curve — proč 2 sessiony, ne 1 dlouhá

Kreativní špička je **45–90 minut**, druhá vlna po obědě **max 60 minut**, pak je tým mentálně v Slacku.

**Session 1 (5–6 h, ne 8):** 0–30 min warm-up + JTBD lock; 30–90 min divergence, AI generuje 3 varianty paralelně (peak energy, AI nese execution, lidé direction); 90–105 break + silent walk (fyzický reset, ne networking); 105–180 convergence + dot voting silent first (1-2-4-All); 180–240 oběd + parking lot review; 240–300 deepening + pre-mortem (TRIZ 15 min) — energy klesá, AI nese instrumentaci; 300–360 handoff brief + akceptační kritéria. **Konec v 16:00, ne 17:30** — tým musí mít rezervu.

**Mezi-session: 5–7 dní, ne 14.** Prototyp deployed do 48 h, scoring window 3 dny, syntéza 1 den. Delší = ztráta kontextu, kratší = nikdo neoscoruje.

**Session 2 (3 h, ne 6):** AI prezentuje feedback aggregate (30 min) → diskuse blokerů (60 min) → go/iterate/kill (30 min) → handoff podpis (30 min). Druhá session je **rozhodovací, ne generativní**. Pokud trvá 6 h, tým nerozhodl, jen unavil.

**Anti-pattern:** "uděláme to celé na 1 den". Den bez prototypu mezi = rozhodli o vibe, ne o realitě.

## 3. AI-human dělba práce — kdy AI vede a kdy člověk

Pflanzer "AI vede výklad v Session 2" je nedostatečně specifikované. Reálné rozdělení podle 200 sessionů:

| Aktivita | Vede | Proč |
|---|---|---|
| Generování mockupů | **AI** | Lidi to neumí dost rychle, AI 3 varianty / 20 min |
| Sumarizace transcriptu | **AI** | Otter/Read v real-time, facilitátor je v místnosti |
| Clustering sticky notes / feedback | **AI** | Miro Sidekick šetří 30 min |
| Generování pre-mortem rizik | **AI první**, člověk valid. | AI nemá context blindness |
| **JTBD framing & persona lock** | **Člověk** | AI nepozná, že persona drift začal |
| **Konflikt mezi rolemi** | **Člověk** | AI nemá political authority |
| **Dot voting interpretation** | **Člověk** | "8 hlasů pro A" může být HiPPO efekt — facilitátor čte místnost |
| **Veto handling** (Security/Legal) | **Člověk** | AI nemá podpis, nemá accountability |
| **Commitment moment** | **Člověk** | Závaznost je sociální akt, ne syntéza |
| **Energy management** (break, refocus) | **Člověk** | AI nepozná unavený tým |
| Score agregace + rationale extrakce | **AI** | Dataset, ne názor |
| Decision log s atribucí | **Oba** | AI píše, člověk podepisuje |
| Prezentace feedback v S2 | **AI první 20 min**, pak **člověk** | AI dá fakta neutrálně, člověk nese rozhodnutí |

**Pravidlo:** AI vede, když je úkol **execution-heavy a context-light**. Člověk vede, když je **context-heavy a accountability-bearing**. Mezi tím **shared mode** — AI navrhuje, člověk valid.

## 4. Konflikt-resolution playbook (cross-cutting napříč 12 perspektivami)

Z 12 perspektiv jsem vyextrahoval **6 opakujících se konfliktních os**:

1. **Security veto vs. zadavatel push** (#7 × #1). Pre-charter triage zachytí 80 %. V místnosti: silent ranking blockerů → AI agreguje severity → Critical = **session pivotuje na alt. variantu**, nepokračuje v zablokované. Veto je veto, ne hlas mezi hlasy.
2. **Eng kapacita vs. business timeline** (#9 × #1, #2). T-shirt sizing, **nikoli story pointy** (SP deformuje sociální tlak). T-shirt > L → 2-day capped spike mimo workshop. Přetrvávající konflikt = eskalace mimo místnost.
3. **PdM výstup vs. UX research** (#2 × #6). JTBD lock v prvních 30 min, persona owner = PdM + UX společně (oba podepíší). Disagreement po 30 min → **Session 1 se odkládá**, předřazení Continuous Discovery.
4. **FE rychlost vs. BE contract** (#4 × #5). **Contract-first** — BE shadow agent generuje OpenAPI paralelně s UI generátorem, side-by-side. Konflikt se nestává, protože vznikají současně.
5. **Hlasitý vs. tichý hlas** (cross-cutting). **Liberating Structures default** — 1-2-4-All před diskusí, dot voting silent před verbálním. Score se zveřejní **po hlasování**. Zadavatel hlasuje **poslední** (anti-HiPPO).
6. **Prototyp do prod** (Sponzor × FE/BE/Security/DevOps). **Throw-away charter** — defaultně throw-away, "evolve" jen s FE+EM+Security podpisem po code review. Sandbox má noindex, watermark, 24h TTL. Technická pojistka, ne důvěra.

## 5. Failure modes facilitátora (co můžu pokazit já sám)

1. **Captured by tool.** Trávím 40 % session debugováním Boltu. Mitigace: AI co-pilot v sub-roli, ne v main session UI; fallback builder (Stitch + Cursor) předem.
2. **Captured by HiPPO.** Zadavatel mě platí, podvědomě mu nadržuju. Mitigace: silent voting, decider hlasuje poslední, právo "zadavateli, podržte slovo" v charteru.
3. **Conflict avoidance.** Odkládám na "vyřešíme potom". Pflanzer "potom" nemá. Mitigace: konflikt nadojmem v 5. minutě výskytu, ne ke konci.
4. **Energy blindness.** Tlačím přes agendu, tým mrtvý. Mitigace: break každých 90 min nediskutuju, pulsní check-in (1–5 prst) každé 2 h.
5. **AI as authority.** "AI navrhla" se v korporátu stává autoritativním argumentem. Mitigace: každý AI insight má human override, decision log atribuuje **člověka**. AI Act čl. 14 to vyžaduje.
6. **Charter creep.** 12 perspektiv chce 30+ vstupů. Mitigace: **MoSCoW na vstupy** — Must (Charter, JTBD, Decider, Data classification, Tech stack), Should (zbytek), Could (audit-grade pro regulované). Default = Must only, regulated = Must + Should.

## 6. Memorabilia

> **"AI je nejlepší co-pilot v místnosti — ale nikdo nepodepíše rozhodnutí, které udělala AI. Facilitátor v Pflanzerovi není moderátor, je architect of accountability: rozhoduje, kdy AI mluví, kdy člověk mlčí, a kdy se konflikt nevyřeší v místnosti, ale eskaluje. Bez té tří-cestné dělby je Pflanzer rychlejší way to fail at scale."**
