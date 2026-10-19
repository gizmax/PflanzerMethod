# Perspektiva: Zadavatel / Business owner

## Kdo jsem
Director / VP Product v B2B SaaS, 15+ let — prošel jsem od enterprise sales přes PO po dnešní VP roli. Vlastním P&L produktové linie ~30 M EUR ARR, reportuju CPO, peers VP Sales a VP Eng. Předchozí projekt mi sežral 9 měsíců v pinkacím cyklu mezi produktem, devem a security — od té doby kupuju každý postup, který tu smyčku zkrátí. Do exec committee chodím s ROI číslem a metric narrative, ne s deckem o „alignmentu".

## 1. Posouzení metody z mé role

**Co mi pomáhá**
- Cross-functional v jedné místnosti od minuty 0 — řeší přesně ten valley of death, který mě stál 9 měsíců (security/eng vetovali řešení, do kterého produkt napumpoval kvartál).
- Funkční mockup, ne Figma fasáda — můžu ho ukázat CPO/board jako důkaz, že to není „další design sprint".
- Score závaznosti per oddělení — konečně přemosťuje „líbí se mi" vs „commitnu to". Tohle je to, co si vezmu do PI Planningu.
- AI-mediovaná syntéza v Session 2 — odstraňuje politickou interpretaci „co řeklo Eng".

**Co mi chybí**
- **Žádný explicit ROI / business case artefakt** v přípravě ani výstupu. Bez něj mi exec nepodepíše budget na druhou iteraci.
- Není definován **success kriteriální threshold** — kdy je výstup „dobrý dost" pro handoff? Bez gate hrozí třetí, čtvrtá session a metoda začne sama být pinkací smyčka.
- Chybí **kill-switch / no-go protokol** — co když Session 1 ukáže, že problém vůbec neřešíme správně?
- **Reinforcement (R z ADKAR)** — co se děje 30/60/90 dní po handoffu? Bez toho metoda zhasne po 2 pilotech.

**Co mě v ní ohrožuje**
- **Security veto v Session 1** mi může před celým týmem zabít preferovanou variantu — politické riziko, který mě stojí kapitál u CPO. Potřebuju veto-handling proces, ne jen „má veto právo".
- **Eng manager s kapacitním vetem** mi může utopit projekt v „nemáme lidi do Q3". Potřebuju předem alternativu (champion z jiného týmu, externí kapacita).
- Pokud session vede AI a já nemám clear decider authority, **rozplývá se moje accountability** — exec mi neuvěří, že jsem rozhodl, když to „rozhodla skupina".

## 2. Must-have vstupy do Session 1 (z mé role)

1. **One-pager business case** — problém, target segment, expected ARR impact, success metric (1 leading, 1 lagging), týden přípravy.
2. **XYZ hypotéza á la Savoia** — „alespoň X % z Y udělá Z" jako falsifikovatelný marker pro mockup. Bez ní je „líbí/nelíbí" theatre.
3. **Constraint sheet** — budget cap, timeline cap (typicky end-of-PI), no-go zóny (kterých systémů se nedotýkáme), regulatorní rails (DORA/NIS2/GDPR triggery předem flagnuté).
4. **Konkurenční snapshot** — 3 referenční řešení (screenshot + 1 řádek diferenciátoru). Brání skupině znovuvynalézat vyřešené.
5. **Top 3 customer quotes / support tickety** — ukotví problém v reálu, zkrátí debate o personě o 40 minut.
6. **Capacity pre-check od Eng managera** — „máme 2 sprinty v Q3" potvrzeno písemně PŘED session, ne objeveno v session.
7. **Security pre-classification** — synthetic / anonym / live data. Definuje, jestli session vůbec smí proběhnout v sandboxu.
8. **Decider mandate** — písemně od CPO: „Tom rozhoduje o variant X v session 1, sign-off do 48 h". Bez toho je session konzultativní theatre.

## 3. Must-have výstupy ze Session 1 a 2

**Session 1 (do 24 h od konce):**
- 1–3 funkční mockupy s public preview URL (stakeholderům bez accountu).
- Preferovaná varianta + 3-řádkový rationale (proč ta a ne ostatní).
- Risk register: top 5 rizik s ownerem a mitigation deadline.
- Capacity & cost estimate (T-shirt size od Eng + odhad infra/license).
- Veto log: kdo co flagoval, jaký score závaznosti, jak se to řeší.

**Session 2 (do 48 h od konce):**
- **Go / iterate / kill rozhodnutí** s explicitním kritériem (ne „pokračujeme").
- Updatovaný business case s aktualizovaným ROI po feedbacku.
- Handoff package pro Eng: scoped epic, akcept. kritéria, dependency map, tech debt flagy.
- Decision log podepsaný všemi rolemi (security/legal explicit), DORA-grade audit trail.
- **Exec one-pager** pro CPO/board: problém, řešení, investice, expected impact, next milestone.

## 4. Edge cases a rizika

1. **Security pošle juniora bez mandátu.** → Charter od začátku vyžaduje senior delegate s explicit veto/sign-off mandátem; junior bez mandátu = session se odkládá. Nepustím session bez tohoto písemně.
2. **Session 1 odhalí, že problém není ten, který jsem zadal.** → Built-in „pivot gate" v polovině Session 1 (90 min mark): pokud >50 % rolí indikuje misalignment problému, session přepíná z generative na re-framing a Session 1.5 se plánuje. Nepokračovat ve špatném zadání.
3. **Eng manager zablokuje na kapacitě.** → Pre-session capacity sign-off (viz vstup #6) toto eliminuje ex-ante. Pokud kapacita zmizí mezi sessions, automaticky aktivuju champion model — pilot v jiné BU s volnější kapacitou.
4. **Variant preference = political vote, ne merit.** → Silent ranking (1-2-4-All protokol) PŘED diskusí, AI agreguje. HiPPO efekt ven. Já jako zadavatel hlasuji POSLEDNÍ.
5. **Třetí session v dohledu.** → Hard rule v charteru: max 2 sessions, pak buď go/kill, nebo escalation k CPO. Třetí session = metoda selhala, learning loop, ne pokračování.

## 5. Konkrétní vylepšení metody

1. **Přidat „Business Charter" jako povinný vstup před Session 1.** Šablona: problém, segment, ARR impact, success metric, XYZ hypotéza, constraints, decider mandate. Sponzor podepisuje 5 dní předem, security a eng manager async pre-review do 48 h. Bez podepsaného charteru session neodstartuje. Řeší ROI gap a security gating najednou.

2. **Zavést Score-based Go/Kill gate na konci Session 2.** Gradient závaznosti per role agreguje AI do jediného „commitment indexu" (0–100). Threshold definovaný v charteru (např. 70). Pod threshold = automaticky kill nebo re-charter, ne třetí session. Brání metodu před self-pinkáním.

3. **Decider model á la GV Sprint, ale explicit.** Zadavatel = Decider s definovaným tie-breaker právem. Není to consensus, je to informed dictatorship. AI prezentuje, panel doporučuje, decider rozhoduje a podepisuje. Brání accountability dilution.

4. **Reinforcement track 30/60/90.** Po handoffu povinné check-iny: 30 dní (build progress vs estimate), 60 dní (early metric signal vs XYZ hypotéza), 90 dní (lagging metric vs success criterion). AI generuje dashboard z tooling Eng týmu. Bez tohoto metoda zhasne — ADKAR „R" se vždy podcení.

5. **IP iteration mounting.** V SAFe korporátech metodu pozicovat výhradně do IP iterace (bez nového procesu vedle). Mimo SAFe pozicovat jako Atlassian Play / GV Sprint variantu. Brand metody = známý referenční rámec, žádné nové buzzwordy směrem k exec.

## 6. Konflikty s ostatními rolemi

- **Security/Compliance (#7):** budu tlačit synthetic data + sandbox scope, oni budou tlačit live integraci pro „realistický test". Konflikt se vyhrocuje při Session 1 minutě 45 — řeším pre-charterem (data classification fixed před session).
- **Engineering manager (#9):** moje business urgency vs jeho roadmap commitment. Klasický fight o Q3 kapacitu. Řeším capacity pre-sign-off a champion alternativou.
- **PdM (#2):** můj scope ambition vs jeho prioritization framework. Pokud PdM má jiný OKR view, Session 1 se přetahuje o problem framing místo o řešení. Řeším explicit decider hierarchií v charteru.
- **UX/Designer (#6):** moje rychlost vs jejich research rigor. „Persona není dost prozkoumaná" vs „ship to learn". Řeším XYZ hypotézou — měřitelné, ne vibe.
- **Legal/GDPR (#10):** můj go-to-market timeline vs jejich risk-aversion default. Async pre-review + on-call slot to řeší v 80 % případů, zbytek je political escalation k CPO.

## Memorabilia
Bez Business Charteru, decider mandate a Go/Kill gate je Pflanzer „hezký den" — s nimi je to artefakt, který přežije pondělí a obhájí mi ho exec committee.
