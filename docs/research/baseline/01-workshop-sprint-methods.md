# Adjacent Workshop & Sprint Methods — Baseline Research

Mapování metod, ze kterých Pflanzerova metoda (PM) vychází. Cíl: ukázat panelu, kde je PM kompilací best practice a kde přidává novinku.

---

## Google Ventures Design Sprint (Jake Knapp)

**Cíl / výstup:** validace strategické otázky přes high-fidelity prototyp testovaný s 5 uživateli. Výstup = go / no-go / pivot.

**Délka, lidé:** 5denní (Knapp 2016), 4denní Sprint 2.0 (AJ&Smart 2018), 1denní mikro. 7 lidí + Decider s vetem.

**Selhává v korporátu:**
- Cena chybné sázky v enterprise = lost credibility napříč odděleními, ne jen wasted dev (UX Booth).
- 5 dní plné disponibility seniorů je logisticky nereálné.
- Prototyp je Figma fasáda; po sprintu "valley of death" — 80 % rozhodnutí padá na security/dev/compliance, které ve sprintu nebyly v místnosti.
- Decider model v hierarchických firmách buď duplikuje rozhodovací řetězec, nebo tvoří politické napětí.
- 5 testovacích uživatelů = pro B2B / regulované obory nedostatečné.

**Co PM přebírá:** time-boxing, "together alone", tangible outputy místo diskuse.

**Liší se:** místo Figma fasády vzniká funkční mockup (AI vibe-coding); security/dev jsou v místnosti od minuty 0 (řeší valley of death); rozhodnutí není binární, ale gradient závaznosti per oddělení.

---

## Lightning Decision Jam — AJ&Smart (Jonathan Courtney)

**Cíl / výstup:** z problémů prioritizovaný seznam akcí + ownery.

**Délka, lidé:** 30–60 min, 4–10 lidí. Problémy (7 min silent) → prezentace → HMW reframe → ideace → impact/effort → akce.

**Selhává v korporátu:** mělká hloubka (symptomy, ne strukturální problémy); HiPPO efekt přebíjí silent voting; akce po LDJ nikdo nezačne řešit, chybí závaznost.

**Co PM přebírá:** silent ideation, dot voting, anti-discussion default, impact/effort thinking pro feedback.

**Liší se:** LDJ = 1 sezení, meta-problém. PM = 2 sezení + funkční prototyp mezi nimi, konkrétní feature.

---

## IDEO Design Thinking (5 fází)

**Cíl / výstup:** human-centered koncept připravený k implementaci. Empathize → Define → Ideate → Prototype → Test (Stanford d.school).

**Délka, lidé:** týdny až měsíce; multidisciplinární tým.

**Selhává v korporátu:** Empathize (terénní výzkum) v B2B nereálná — NDA, interní uživatelé. "Iterativní, non-linear" = žádný clear gate → frustrace sponsora. "Design theatre" — končí concept deckem bez ownerství implementace.

**Co PM přebírá:** human-centered princip, prototype-as-thinking-tool.

**Liší se:** PM je time-boxed na 2 sezení a vědomě přeskakuje Empathize tím, že stakeholdery má rovnou v místnosti. Není DT pro koncového uživatele, je alignment-driven discovery pro interní rozhodovatele.

---

## Lean Inception (Paulo Caroli, ThoughtWorks)

**Cíl / výstup:** alignment na MVP, vyplněný MVP Canvas (segment, hypotézy, metriky, features, journey, schedule).

**Délka, lidé:** 5 dní (1 týden), zkrácená 2denní. PO + tech lead + UX + business. Aktivity: Kickoff → Product Vision → Is/Is Not → Personas → Journeys → Feature Brainstorming → Sequencer → MVP Canvas → Showcase.

**Selhává v korporátu:** týden non-stop = logistický blocker. MVP Canvas je dokument, ne prototyp — alignment verbální, ne vizuální (lidé říkají "ano" na features, které si představují jinak). Showcase končí v Confluence.

**Co PM přebírá:** alignment cross-functional týmu, Sequencer (priorita featur), MVP-thinking.

**Liší se:** místo Canvasu vzniká klikací mockup. "Everyone clicks the same screen" místo "everyone agrees on the doc". Feedback mezi sezeními má score závaznosti — Lean Inception nic takového nemá.

---

## Event Storming (Alberto Brandolini)

**Cíl / výstup:** mapování domény. 3 úrovně: Big Picture (bounded contexts), Process Modeling, Software Design (aggregates pro DDD/CQRS).

**Délka, lidé:** 2–8 h až 2 dny; doménoví experti + dev. Oranžové post-ity = events, fialové = pain points, žluté = aktéři.

**Selhává v korporátu:** DDD-literate facilitátor je rare; bez něj sklouzne do flowchart cvičení. Big Picture odhalí 50+ painpointů bez prioritizace. Zeď post-itů je obtížně přenositelná. Mapuje, neřeší — exec ztrácí trpělivost.

**Co PM přebírá:** "stejní lidé v jedné místnosti", mapování pain points napříč rolemi.

**Liší se:** ES je discovery (mapuje existující), PM je generativní (vyrábí nové). PM může ES použít jako pre-step pro komplexní domény.

---

## Pretotyping (Alberto Savoia)

**Cíl / výstup:** test tržní hypotézy před prototypem. "Build the right It before building It right." Nástroje: Fake Door, Pinocchio, Mechanical Turk.

**XYZ hypotéza:** "alespoň X % z Y udělá Z" — měřitelná, refutable. Hypozooming = nejmenší možný test.

**Selhává v korporátu:** Fake Door je reputačně rizikový (compliance odmítne inzerát na neexistující produkt). Interní IT projekty nemají externí "trh". B2B sample pod 100 = statisticky neprůkazné.

**Co PM přebírá:** XYZ hypotézu jako formát pro success kritéria mockupu mezi sezeními. Score závaznosti = pretotyping aplikovaný na interní stakeholdery místo trhu.

**Liší se:** PM testuje interní alignment, ne externí poptávku. Komplementární.

---

## Crazy 8s

**Cíl / výstup:** 8 nápadů za 8 minut, force divergence beyond first idea. Součást DS (Sketch fáze, den 2).

**Selhává v korporátu:** seniorní účastníci odmítají kreslit ("nejsem designér") → 2–3 nápady místo 8. Často 8 variant jednoho nápadu. Sketches jsou nečitelné po týdnu.

**Co PM přebírá:** force-divergence princip, time-box, individuální před skupinovou.

**Liší se:** PM nahrazuje sketching tím, že AI generuje 1–3 mockup varianty z verbálního inputu týmu. Demokratizuje vizualizaci pro non-designéry.

---

## Liberating Structures (Lipmanowicz & McCandless)

**1-2-4-All:** silent → pair → quad → group (12 min, engaguje 100 % účastníků). **TRIZ:** kreativní destrukce — "co bychom dělali, abychom zaručeně selhali", pak inverze.

**Selhává v korporátu:** vyžaduje facilitátora schopného prosadit nezvyklé protokoly proti C-level netrpělivosti.

**Co PM přebírá:** 1-2-4-All jako default protokol feedback fáze (silent first → obejde HiPPO). TRIZ jako "pre-mortem" pro security/compliance v sezení 1.

---

## Syntéza — pozice Pflanzerovy metody

PM je **kompilace** osvědčených prvků (silent ideation, time-box, prototype-as-alignment, dot voting, cross-functional in one room) **plus tři novinky:**

1. **AI co-pilot v reálném čase** — vibe-coding viditelný stakeholderům. Mockup vzniká v sezení, ne mezi sezeními.
2. **Score závaznosti per oddělení** — přemosťuje propast mezi "líbí se mi" (LDJ, DS) a "tohle commitnu" (žádná z metod to neřeší).
3. **AI-mediovaná syntéza feedbacku** v sezení 2 — odstraňuje politickou interpretaci "co řeklo X oddělení".

**Riziko překryvu:** PM bez těchto tří prvků = Design Sprint 2.0 + Lean Inception lite. S nimi = nová kategorie "AI-augmented alignment workshop". Panel by měl tlačit na ostrost těchto diferenciátorů.

---

## Zdroje

- [The Design Sprint — GV](https://www.gv.com/sprint/)
- [Sprint — Jake Knapp](https://jakeknapp.com/sprint)
- [Design Sprints in 2025: The Questions Enterprise Teams Are Really Asking — Design Sprint Academy](https://www.designsprint.academy/blog/design-sprints-in-2025-the-questions-enterprise-teams-are-really-asking)
- [What a Design Sprint CAN'T Do (for Enterprise Teams) — UX Booth](https://www.uxbooth.com/articles/what-a-design-sprint-cant-do-for-enterprise-teams/)
- [Lightning Decision Jam — AJ&Smart Workshopper](https://www.workshopper.com/lightning-decision-jam)
- [Lightning Decision Jam — SessionLab](https://www.sessionlab.com/methods/lightning-decision-jam-ldj)
- [The 5 Stages in the Design Thinking Process — IxDF](https://ixdf.org/literature/article/5-stages-in-the-design-thinking-process)
- [Stanford d.school Design Thinking Process Guide (PDF)](https://web.stanford.edu/~mshanks/MichaelShanks/files/509554.pdf)
- [Lean Inception — Caroli.org](https://caroli.org/en/lean-inception-4/)
- [Lean Inception — Martin Fowler](https://martinfowler.com/articles/lean-inception/)
- [The MVP Canvas — Caroli.org](https://caroli.org/en/the-mvp-canvas/)
- [EventStorming — Alberto Brandolini](https://www.eventstorming.com/)
- [Big Picture Event Storming — Qlerify](https://www.qlerify.com/event-storming-concepts/what-is-big-picture-event-storming)
- [Pretotyping Planning Canvas (XYZ) — Alberto Savoia](https://www.albertosavoia.com/uploads/1/4/0/9/14099067/pretotyping_planning_canvas_by_chris_callaghan.pdf)
- [Building the Right "It": Pretotyping & XYZ Hypothesis — Medium](https://medium.com/@aappalla/building-the-right-it-pretotyping-xyz-hypothesis-and-hypozooming-06971961be87)
- [Crazy 8's — Google Design Sprint Kit](https://designsprintkit.withgoogle.com/methodology/phase3-sketch/crazy-8s)
- [Liberating Structures — 1-2-4-All](https://www.liberatingstructures.com/1-1-2-4-all/)
- [Liberating Structures — TRIZ](https://www.liberatingstructures.com/6-making-space-with-triz/)
