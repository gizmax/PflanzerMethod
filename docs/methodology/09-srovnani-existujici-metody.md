# Pflanzer vs adjacent metody — srovnání

> Cílový čtenář: analytik / metodolog, který potřebuje obhájit volbu metody
> proti alternativě. Každý argument je v tabulce, rozhodovacím stromu a
> seznamu diferenciátorů.
>
> **v0.3 update (2026-05-18):** competitive research s 3 experty (workshop methodology,
> AI vibe-coding, enterprise transformation) identifikoval 4 nově nebo updatované
> konkurenty: **AWS AI-DLC** (direct competitor, ~60-70 % DNA overlap), **Thoughtworks
> AI/works + „3-3-3"** (enterprise direct competitor), **Foundation Sprint** (Knapp 2025,
> komplement pre-step), **McKinsey QuantumBlack / BCG GAMMA / Accenture AABG**
> (enterprise consulting layer). Detail v `docs/research/competitive/04-synthesis-and-positioning.md`.
>
> **Brand collision warning:** „AI Design Sprint" je Design Sprint Academy (DSA)
> brand — Pflanzer dokumentace a marketing **NESMÍ** tento termín používat.

## Tabulka srovnání — workshop methodology family

| Atribut | Pflanzer | Design Sprint (GV) | Lightning Decision Jam | Lean Inception | Event Storming (Big Picture) | Pretotyping |
|---|---|---|---|---|---|---|
| **Cíl** | Cross-functional alignment na funkčním klikacím prototypu + handoff package | Validace strategické otázky přes high-fidelity prototyp testovaný s 5 uživateli | Z problémů prioritizovaný seznam akcí + ownery | Alignment na MVP přes vyplněný MVP Canvas | Mapování domény (events, bounded contexts, pain points) | Test tržní hypotézy XYZ přes nejmenší možný experiment |
| **Délka** | 2 sessions (5–6 h + 3 h) + 5–7 dní mezi-session + pre-flight 48 h + reinforcement T+7/30/60/90 | 5 dní (Knapp 2016), 4 dny (Sprint 2.0), 1 den (mikro) | 30–60 min | 5 dní (full), 2 dny (zkrácená) | 2–8 h až 2 dny | Hodiny až týdny dle pretotype typu |
| **Lidé** | 4–7 v místnosti default, 8–10 max; MoSCoW gradace; vždy core 3 (zadavatel, PM, facilitátor) + role z decision tree | 7 + Decider | 4–10 | PO + tech lead + UX + business (typicky 5–8) | Doménoví experti + dev (5–15) | 1–3 (autor hypotézy + MVP buddy) |
| **Hlavní výstup** | 1–3 anotované klikací prototypy, draft OpenAPI 3.1, score závaznosti per role, decision package s lidskou atribucí, P2P checklist | High-fidelity prototyp (v 2026 Lovable / Bolt místo Figmy) + go/no-go/pivot z 5 user testů | Akční seznam s impact/effort + ownery | MVP Canvas (segment, hypotézy, metriky, features, journey, schedule) | Stěna post-itů s eventy, aktéry, pain points; 50+ painpointů bez prioritizace | Validovaná/falsifikovaná XYZ hypotéza („alespoň X % z Y udělá Z") |
| **Kde selhává v korp** | Pokud chybí discovery / persona / decider mandate, vyrobí „nejhladší feature factory" | 5 dní seniorů nereálných; security/legal/non-tech nejsou v místnosti od minuty 0 (v 2026 už ne Figma fasáda — Lovable produkuje live URL, ale **stakeholder alignment vrstva chybí**) | Mělká hloubka; HiPPO přebíjí silent voting; akce nikdo nerozjede | Týden non-stop blocker; Canvas končí v Confluence; alignment verbální, ne vizuální | Vyžaduje DDD-literate facilitátora; mapuje, neřeší — exec ztrácí trpělivost; zeď post-itů obtížně přenositelná | Fake Door reputačně rizikový pro compliance; B2B sample <100 statisticky neprůkazný; interní IT nemá „trh" |
| **Kde excels** | Cross-functional alignment problem na nové feature s funkčním prototypem v regulovaném prostředí; AI Act / DORA compliance gates; SAFe IP iteration mounting | Novel problem space pro consumer-facing s persona výzkumem v sprintu | Quick prioritizace problémů v existujícím týmu (<1 hod) | Greenfield startup MVP s diskovaným segmentem | Mapování existující komplexní domény před refaktoringem / DDD | Test poptávky před investicí do dev (B2C, externí trh) |

## Tabulka srovnání — AI workflow / pilot family (v0.3 add)

> **Tato sekce je nová v v0.3** (po competitive research May 2026). Zachycuje
> 2024-2026 emergence kategorie *„AI workflow methodology"*, kde Pflanzer
> sedí jako jeden z přibližně 4-5 hlavních hráčů.

| Atribut | Pflanzer | **AWS AI-DLC** | **Thoughtworks AI/works + „3-3-3"** | **Foundation Sprint** (Knapp 2025) | **BMAD-METHOD** | **Spec Kit / Kiro / OpenSpec** |
|---|---|---|---|---|---|---|
| **Kategorie** | AI pilot fixture (cross-fn, 14d, prod handoff) | AI development lifecycle methodology (mob, continuous bolts) | Enterprise AI delivery (90-day idea→MVP) | Pre-implementation strategic foundation (2h) | AI agent orchestration framework (12+ rolí jako AI personas) | Spec-driven development (specification discipline) |
| **Origin** | Pflanzer (Tom, v0.3 2026) | AWS / Raja SP (DevOps blog 07/2025, re:Invent DVT214 12/2025) | Thoughtworks consulting (Q1 2026) | Jake Knapp + John Zeratsky (kniha *Click*, 2025) | OSS community (MIT, `bmad-code-org`) | GitHub Spec Kit (93k stars), Amazon Kiro, OpenSpec |
| **Cíl** | Cross-functional alignment + production code z 2 sessions | Engineering velocity přes AI-led mob (BA/PM/eng/QA/ops) | 90-day production AI MVP s enterprise governance | Strategic problem framing před implementací | AI agent personas pro 12+ rolí | Specification-first development discipline |
| **Délka** | 2 sessions (3-6h + 3h) + 5-7d async + reinforcement T+7/30/60/90 (~14d default) | Continuous „bolts" (3-4h Mob Elaboration) | 90 dní idea → MVP | 2h foundation phase | Continuous (agent-based) | Variable (specification iteration) |
| **Lidé** | 4-7 cross-fn (vč. Security/Legal/A11y/UX-writer/CS-proxy v audit-grade) | Engineering tým + AI navigator (jen tech role) | Consulting team + client stakeholders | 3-5 leadership stakeholders | Solo + AI agents (no humans in „room") | Variable (developer-centric) |
| **AI role** | Co-pilot v session (Bolt/v0/Lovable/Claude Code) + AI-mediated synthesis v S2 | AI navrhuje → mob validuje (continuous loop) | AI augmented delivery (multi-tool stack) | (Žádná explicit AI role) | AI = primary actor (orchestrated agents) | AI generuje code from spec |
| **Compliance / audit** | **Native AI Act čl. 14 decision log + DORA-grade audit + dvoufázový AI Act protokol (Fáze A/B/C)** | Žádný explicit audit trail | Enterprise governance vrstva (consulting-grade) | (Out of scope) | Žádný | Žádný |
| **Score / decision protocol** | Score závaznosti per role + AI deflation 0.5 + anti-HiPPO Decider | Žádný | Standardní consulting decision frameworks | (Out of scope) | Žádný | Žádný |
| **Pricing / packaging** | Free (open) / self-serve | Free (open source, AWS partner channel) | Consulting engagement ($1M-$10M+) | Kniha + workshop (Knapp consulting) | OSS free | OSS free |
| **Direct competitor pro Pflanzer?** | — | **ANO** (60-70 % DNA overlap, Session 1 Mob Elaboration) | **ANO** (enterprise direct, ale 90d vs 14d) | NE (komplement, pre-step) | NE (komplement, agent orchestration target) | NE (komplement, handoff export target) |

## Tabulka srovnání — enterprise consulting layer (v0.3 add)

| Atribut | Pflanzer | **McKinsey QuantumBlack** | **BCG GAMMA + BCG X** | **Accenture AABG** | **Deloitte Enterprise AI Navigator** | **Capgemini Resonance** |
|---|---|---|---|---|---|---|
| **Kategorie** | AI pilot fixture (pilot-level) | AI Operating Model (top-down transformation) | DRI framework (Deploy/Reshape/Invent) | AI workflow redesign (channel partner ekosystém) | AI maturity toolkit (licensed framework) | AI consulting framework (RAISE gallery) |
| **Origin** | Tom (Pflanzer v0.3, 2026) | McKinsey QuantumBlack 2024+; Google Transformation Group 04/2026 | BCG GAMMA + BCG X | Accenture + Anthropic Business Group (12/2025) + Microsoft Accenture Digital Core (Q1 2026) | Deloitte 02/2026 toolkit launch | Capgemini 07/2025 |
| **Pricing** | Free / DIY | Strategy case $500k-$1.25M (8-12 týdnů); transformation $10M-$100M+ | $300k-$800k Envision phase; full multi-month | $200k-$600k diagnostika; partner-led delivery | License $50k-$250k/year + implementation | Lowest of big-5 (cca $150k-$400k) |
| **Typický deliverable** | 1-3 prototyp + handoff package + 14d cycle | AI strategy + operating model + capability roadmap | DRI assessment + portfolio + executive roadmap | Workflow redesign + 30 000 trained Claude Code lidí | Maturity assessment + use case catalog | Use case selection + delivery framework |
| **Compliance / audit** | Native AI Act čl. 14 + DORA | Variable (consulting deliverable) | Variable | Variable | Variable | Variable |
| **Time-to-value** | 14 dní default profil; 4-6 týdnů audit-grade | 8-12 týdnů strategy, 6-18 měsíců transformation | 4-8 týdnů Envision; multi-month delivery | 4-8 týdnů diagnostic; 3-12 měsíců delivery | Variable | Variable |
| **Direct competitor pro Pflanzer?** | — | **NE** (strategy layer, ne pilot fixture) | **NE** (portfolio layer) | **NE** (delivery layer — potenciální channel partner) | **NE** (assessment layer) | **NE** (delivery layer) |

**Bottom line per enterprise expert:** Pflanzer **sedí v mezeře** mezi $1M+ McKinsey transformations a $0 hackathon frameworks. Tu mezeru zatím nikdo nezaplnil. Doporučená pozice: *„AI pilot fixture pro AI CoE pilot portfolio"* — opakovatelná, certifikovaná, procurement-ready fixture na úrovni *operating cadence*, ne strategy a ne delivery.

## Rozhodovací strom

Použij kaskádově — první ano = doporučená metoda.

1. **Máš < 1 hodinu a potřebuješ jen prioritizovat problémy s ownery?**
   → **LDJ.** Mělčí, ale rychlejší než cokoli jiného.
2. **Mapuješ existující komplexní doménu (3+ bounded contexts, legacy, DDD
   refaktor)?** → **Event Storming Big Picture.** Pflanzer to nepřevezme;
   může ho použít jako pre-step.
3. **Testuješ tržní hypotézu před investicí do dev na externím trhu?**
   → **Pretotyping s XYZ.** Pflanzer XYZ přebírá pro interní stakeholder
   alignment, ne pro market test.
4. **Strategická foundation phase (problem framing, audience, USP) před implementací?**
   → **Foundation Sprint** (Knapp/Zeratsky 2025). Pflanzer ho nereplikuje;
   je komplementární pre-step (2h před Pflanzer Charterem).
5. **Máš novel problem space bez fresh persony, consumer-facing, a
   capacity na 5 dní seniorů?** → **GV Sprint** (v 2026 s Lovable/Bolt místo Figmy)
   s předřazeným continuous discovery týdnem.
6. **Greenfield MVP s diskovaným segmentem, potřebuješ canvas-based
   alignment, není to korporát s 80 % PI committed?** → **Lean Inception.**
7. **Continuous engineering loop s AI navigator (jen tech mob, žádný non-tech
   stakeholder requirement, no enterprise compliance)?** → **AWS AI-DLC**
   (open source, integrace s AWS stack zdarma).
8. **90-day enterprise AI MVP delivery s consulting engagement modelem
   ($300k-$1M budget)?** → **Thoughtworks AI/works + „3-3-3"**.
9. **Strategic AI transformation, top-down ($1M-$10M+ budget, 12+ týdnů)?**
   → **McKinsey QuantumBlack / BCG GAMMA / Accenture AABG.**
10. **Cross-functional alignment problem v korporátu (3+ oddělení blokují
    rozhodnutí), funkční prototyp je requirement, máš fresh discovery,
    capacity ~10 person-days, mandát rozhodnout, pre-flight triage prošel,
    AI Act / DORA compliance je MUST?** → **Pflanzer.**
11. **Žádné z výše uvedených, single-team quick win?** → Backlog +
    sprint, žádný workshop nepotřebuješ.

## Co Pflanzer převzal

- **Z Design Sprintu:** Decider model s tie-breakerem (anti-paralýza
  v hierarchii), time-boxing per fáze, princip „together alone" (silent
  ideation před skupinou), tangible outputy místo diskuse, prototyp
  v jeden den jako alignment device.
- **Z LDJ:** dot voting, silent ideation default, anti-discussion default
  jako protokol pro feedback fáze, impact/effort thinking pro score
  závaznosti.
- **Z Lean Inception:** alignment cross-functional týmu jako primární
  cíl (ne user testing), Sequencer pro priority featur, MVP-thinking
  jako rámec pro scope rozhodnutí.
- **Z Event Stormingu:** „stejní lidé v jedné místnosti" princip,
  mapování pain points napříč rolemi, doménový jazyk jako sdílený
  kontext (pre-flight Backend Context Pack obsahuje ERD, OpenAPI, ADR
  archiv).
- **Z Pretotypingu:** XYZ hypotéza („alespoň X % z Y udělá Z") jako
  formát success kritéria mockupu mezi sezeními a falsifikovatelný
  marker v Business Charteru.
- **Z Crazy 8s:** force-divergence princip, time-box, individuální před
  skupinovou — ale s **AI generujícím varianty** místo sketchingu, který
  seniorní účastníci odmítají („nejsem designér").
- **Z Liberating Structures:** 1-2-4-All jako default protokol feedback
  fáze (silent first → obejde HiPPO; zadavatel hlasuje poslední), TRIZ
  jako pre-mortem ve 30. minutě S1.
- **Z Design Thinking (IDEO):** prototype-as-thinking-tool, human-centered
  princip — ale **přeskočení Empathize fáze** přesunutím stakeholderů
  do místnosti (B2B / interní uživatelé jsou v Pflanzeru účastníci, ne
  subjekty výzkumu).
- **Z AWS AI-DLC** (v0.3 add): princip „AI navrhuje → mob validuje" jako
  Session 1 vibe-coding mechanika. Pflanzer rozšiřuje na non-tech roles
  a 2-session formát.
- **Z BMAD-METHOD** (v0.3 add): AI personas pro role z catalogu jako
  pre-session prep + during-session shadow agents (BE shadow generuje
  OpenAPI 3.1 paralelně s UI).

## Co Pflanzer přidává (5 protected diferenciátorů — v0.3 update)

> v0.2 mluvila o **3 diferenciátorech**. Competitive research May 2026
> identifikoval, že 2 z původních 3 jsou nyní commoditizované (real-time
> AI vibe-coding, AI-mediated synthesis rapidly commoditizing přes SessionLab/Miro).
> Reálná protected USPs v 2026 jsou **5 pilířů**, které **dohromady** v 2026
> nikdo jiný nedělá.

### 1. Non-tech role v primary session (organizational moat)

**Co:** Security + Legal/DPO + A11y + UX writer + CS proxy **v místnosti
od minuty 0**, ne v eskalačním řetězci na konci.

**Proč to není v adjacentech:** AWS AI-DLC „mob" je homogenní engineering
(BA/PM, eng, QA, ops). Thoughtworks AI/works je consulting team. McKinsey
to dělá v multi-week engagement, ne v single-session fixture. Design Sprint
historicky neměl Security/Legal v primary room.

**Co to umožňuje:** Late-stage veto eliminované — security/legal flag
risk surface na minutě 240, ne v sprintu 4. Audit-grade profil přidává
co-facilitator (ADR-0010) a Method Steward (ADR-0012) pro multi-pilot
governance.

### 2. Score závaznosti per role + AI deflation (decision moat)

**Co:** 1–5 Likert s rationale field per role per varianta, hierarchie
závaznosti **Critical (blocker) / Yellow (warning) / Score**. AI-only
feedback **deflated max 0.5/1.0**. Zadavatel hlasuje **poslední** (anti-HiPPO).

**Proč to není v adjacentech:** Workshop methodology expert independent
confirmation (May 2026): žádný direct competitor v 2026. AWS AI-DLC,
Sprint 2.0, IDEO, Liberating Structures, AJ&Smart Sprint 2.0 — žádná
metoda neřeší propast mezi *„líbí se mi"* (LDJ dot voting) a *„tohle
commitnu"* (DS Decider binary). 12-měsíční náskok.

**Co to umožňuje:** Eliminace late-stage veta, atribuovaná závaznost
(decision log s lidskou atribucí splňuje DORA, AI Act čl. 14, GDPR čl. 22),
učící smyčka (score uloženo do DB pro retrospective T+30/60/90 vs reálný
outcome — kalibrace AI deflation parametru per Method Charter v0.3).

### 3. Pre-flight triage 4 tracks (governance moat)

**Co:** Discovery Readiness Gate + Security & Data Triage + Legal & Privacy
Triage + Platform Triage — 4 paralelní async pre-read tracky 48-72h před
Session 1. Bez 4 podpisů Session 1 neodstartuje.

**Proč to není v adjacentech:** Žádná konkurenční metoda nemá 48-72h async
pre-read jako MUST gate. Design Sprint, AI-DLC, Lean Inception startují
bez explicit pre-flight discipline. Enterprise consulting frameworks mají
diagnostické fáze, ale ne formalizované gating.

**Co to umožňuje:** Discovery Debt Detector skóre, Sandbox spec ready
před Session 1, Approved AI Tool list (DPA/SCC), AI Act risk tier Fáze A.

### 4. Native AI Act / DORA compliance (regulatorní moat)

**Co:** Decision log s human attribution per AI Act čl. 14 + dvoufázový
AI Act protokol (Fáze A pre-Session 1, Fáze B interim review v mezi-session,
Fáze C final v Session 2 / handoff). DORA-grade 7-letá retence audit logů.

**Proč to není v adjacentech:** AWS AI-DLC nemá explicit audit trail.
McKinsey / BCG / Accenture compliance je custom deliverable per engagement,
ne out-of-the-box. Anti-Pflanzer external validation — Martinelli, *„Why
Spec-Driven Development Tools Fail in the Enterprise"* (2026), kritizuje
Spec Kit/BMAD/Kiro za chybějící stakeholder alignment + audit trail.
Tyto critique pointy jsou **doslova Pflanzer USPs**.

**Co to umožňuje:** Procurement-ready pro CRO/DPO. Hardest defensible
moat proti commoditization. Enterprise expert: out-of-the-box compliance
artefakt, který velcí poradci nemají.

### 5. 2-session formát s týdenním asyncem + reinforcement track (operational moat)

**Co:** Session 1 (vibe, 3-6h) → 5-7 dní async iterace → Session 2 (rozhodnutí,
3h) → handoff → reinforcement T+7/30/60/90. Default profil ~14 dní calendar,
~10 PD effort.

**Proč to není v adjacentech:** AWS AI-DLC běží continuous „bolts" (žádný
2-session formát). Thoughtworks „3-3-3" je 90 dní. Design Sprint je 5 dní
non-stop (corporate stakeholder unavail). Foundation Sprint je 2h foundation
(žádná implementation phase). 14-day production cycle = unique cadence.

**Co to umožňuje:** Corporate stakeholder availability (async window),
context retention (5-7 dní < window of forgetting), reinforcement loop
(T+7/30/60/90 kalibrace).

### Bývalé USPs (v0.2), nyní commoditizované

| Bývalý claim | Status May 2026 | Důvod |
|--------------|-----------------|-------|
| „Real-time AI vibe-coding viditelný stakeholderům" | ❌ Commoditizováno | Sprint 2.0 + Lovable/Bolt/v0/Cursor = 2025 mainstream. Cursor `/best-of-n` (10/2025) produkuje multi-variant. Wow-faktor se ztratil. |
| „AI-mediovaná syntéza feedbacku v Session 2" | ⚠️ Rapidly commoditizing | SessionLab Custom AI Guidelines + Miro AI + Mural konvergují k podobnému patternu. 12-18 měsíců window. |
| „Funkční kód místo Figmy" | ❌ Commoditizováno | Stejný důvod jako vibe-coding. Lovable produkuje live URL. |

**Důsledek pro positioning v0.4:** Marketing musí pivot z vibe-coding framing
na 5-pilíř kombinaci. Vibe-coding zůstává jako *enabler*, ne jako *primary USP*.

## Pflanzer pozice v 2026 enterprise stacku

| Layer | Příklady | Pflanzer role |
|-------|----------|---------------|
| **Strategy** | McKinsey QuantumBlack, BCG GAMMA | Pflanzer ne (pilot-level, ne strategy-level) |
| **Portfolio governance** | SAFe AI Coach, Disciplined Agile, BCG DRI portfolio | Pflanzer = jeden z pilots v portfolio |
| **AI CoE / operating cadence** | (mezera — Pflanzer's place) | **Pflanzer = AI pilot fixture, opakovatelná unit pro AI CoE pilot portfolio** |
| **Pilot delivery** | Thoughtworks AI/works, Accenture AABG, internal Champion-led | Pflanzer = opakovatelná methodology pro to, co dnes Champion dělá ad-hoc |
| **Engineering loop** | AWS AI-DLC, Cursor team mode, Claude Code workflows | Pflanzer Session 1 vibe-coding používá tyto tooly, ale s explicit non-tech alignment vrstvou |
| **Foundation** | Foundation Sprint (Knapp 2025) | Pflanzer pre-step (volitelný), Pflanzer Charter ho přejímá jako vstup |
| **Spec / handoff** | Spec Kit, Amazon Kiro, BMAD, OpenSpec | Pflanzer handoff target (v0.4 P1: spec-kit-compatible export) |

**Klíčová insight:** Pflanzer **není** „yet another workshop methodology" — to je hřbitov, ze kterého většina metod nevyšla. Pflanzer je **„operating-cadence layer pro AI Center of Excellence"** v mezeře mezi strategy ($1M+ consulting) a engineering loop (free OSS tools). Tu mezeru zatím nikdo nezaplnil.
