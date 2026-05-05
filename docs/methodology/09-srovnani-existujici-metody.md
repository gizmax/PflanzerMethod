# Pflanzer vs adjacent metody — srovnání

> Cílový čtenář: analytik / metodolog, který potřebuje obhájit volbu metody
> proti alternativě. Každý argument je v tabulce, rozhodovacím stromu a
> seznamu diferenciátorů.

## Tabulka srovnání

| Atribut | Pflanzer | Design Sprint (GV) | Lightning Decision Jam | Lean Inception | Event Storming (Big Picture) | Pretotyping |
|---|---|---|---|---|---|---|
| **Cíl** | Cross-functional alignment na funkčním klikacím prototypu + handoff package | Validace strategické otázky přes high-fidelity prototyp testovaný s 5 uživateli | Z problémů prioritizovaný seznam akcí + ownery | Alignment na MVP přes vyplněný MVP Canvas | Mapování domény (events, bounded contexts, pain points) | Test tržní hypotézy XYZ přes nejmenší možný experiment |
| **Délka** | 2 sessions (5–6 h + 3 h) + 5–7 dní mezi-session + pre-flight 48 h + reinforcement T+7/30/60/90 | 5 dní (Knapp 2016), 4 dny (Sprint 2.0), 1 den (mikro) | 30–60 min | 5 dní (full), 2 dny (zkrácená) | 2–8 h až 2 dny | Hodiny až týdny dle pretotype typu |
| **Lidé** | 4–7 v místnosti default, 8–10 max; MoSCoW gradace; vždy core 3 (zadavatel, PM, facilitátor) + role z decision tree | 7 + Decider | 4–10 | PO + tech lead + UX + business (typicky 5–8) | Doménoví experti + dev (5–15) | 1–3 (autor hypotézy + MVP buddy) |
| **Hlavní výstup** | 1–3 anotované klikací prototypy, draft OpenAPI 3.1, score závaznosti per role, decision package s lidskou atribucí, P2P checklist | Figma fasáda + go/no-go/pivot z 5 user testů | Akční seznam s impact/effort + ownery | MVP Canvas (segment, hypotézy, metriky, features, journey, schedule) | Stěna post-itů s eventy, aktéry, pain points; 50+ painpointů bez prioritizace | Validovaná/falsifikovaná XYZ hypotéza („alespoň X % z Y udělá Z") |
| **Kde selhává v korp** | Pokud chybí discovery / persona / decider mandate, vyrobí „nejhladší feature factory" [synthesis 02 — takeaway 3] | 5 dní seniorů nereálných; Figma fasáda + valley of death; security/dev nejsou v místnosti od minuty 0 [baseline 01] | Mělká hloubka; HiPPO přebíjí silent voting; akce nikdo nerozjede | Týden non-stop blocker; Canvas končí v Confluence; alignment verbální, ne vizuální | Vyžaduje DDD-literate facilitátora; mapuje, neřeší — exec ztrácí trpělivost; zeď post-itů obtížně přenositelná | Fake Door reputačně rizikový pro compliance; B2B sample <100 statisticky neprůkazný; interní IT nemá „trh" |
| **Kde excels** | Cross-functional alignment problem na nové feature s funkčním prototypem; SAFe IP iteration mounting; regulovaný projekt s předem dodanou DPIA | Novel problem space pro consumer-facing s persona výzkumem v sprintu | Quick prioritizace problémů v existujícím týmu (<1 hod) | Greenfield startup MVP s diskovaným segmentem | Mapování existující komplexní domény před refaktoringem / DDD | Test poptávky před investicí do dev (B2C, externí trh) |

## Rozhodovací strom

Použij kaskádově — první ano = doporučená metoda.

1. **Máš < 1 hodinu a potřebuješ jen prioritizovat problémy s ownery?**
   → **LDJ.** Mělčí, ale rychlejší než cokoli jiného.
2. **Mapuješ existující komplexní doménu (3+ bounded contexts, legacy, DDD
   refaktor)?** → **Event Storming Big Picture.** Pflanzer to nepřevezme;
   může ho použít jako pre-step [baseline 01].
3. **Testuješ tržní hypotézu před investicí do dev na externím trhu?**
   → **Pretotyping s XYZ.** Pflanzer XYZ přebírá pro interní stakeholder
   alignment, ne pro market test [baseline 01].
4. **Máš novel problem space bez fresh persony, consumer-facing, a
   capacity na 5 dní seniorů?** → **GV Sprint** s předřazeným continuous
   discovery týdnem.
5. **Greenfield MVP s diskovaným segmentem, potřebuješ canvas-based
   alignment, není to korporát s 80 % PI committed?** → **Lean Inception.**
6. **Cross-functional alignment problem v korporátu (3+ oddělení blokují
   rozhodnutí), funkční prototyp je requirement, máš fresh discovery,
   capacity ~8–10 person-days, mandát rozhodnout, pre-flight triage
   prošel?** → **Pflanzer.**
7. **Žádné z výše uvedených, single-team quick win?** → Backlog +
   sprint, žádný workshop nepotřebuješ.

## Co Pflanzer převzal

- **Z Design Sprintu:** Decider model s tie-breakerem (anti-paralýza
  v hierarchii), time-boxing per fáze, princip „together alone" (silent
  ideation před skupinou), tangible outputy místo diskuse, prototyp
  v jeden den jako alignment device [baseline 01 — DS].
- **Z LDJ:** dot voting, silent ideation default, anti-discussion default
  jako protokol pro feedback fáze, impact/effort thinking pro score
  závaznosti [baseline 01 — LDJ].
- **Z Lean Inception:** alignment cross-functional týmu jako primární
  cíl (ne user testing), Sequencer pro priority featur, MVP-thinking
  jako rámec pro scope rozhodnutí [baseline 01 — LI].
- **Z Event Stormingu:** „stejní lidé v jedné místnosti" princip,
  mapování pain points napříč rolemi, doménový jazyk jako sdílený
  kontext (pre-flight Backend Context Pack obsahuje ERD, OpenAPI, ADR
  archiv) [baseline 01 — ES; synthesis 03 — #5].
- **Z Pretotypingu:** XYZ hypotéza („alespoň X % z Y udělá Z") jako
  formát success kritéria mockupu mezi sezeními a falsifikovatelný
  marker v Business Charteru; score závaznosti = pretotyping aplikovaný
  na interní stakeholdery místo externího trhu [baseline 01 — Pretotyping].
- **Z Crazy 8s:** force-divergence princip, time-box, individuální před
  skupinovou — ale s **AI generujícím varianty** místo sketchingu, který
  seniorní účastníci odmítají („nejsem designér") [baseline 01 — Crazy 8s].
- **Z Liberating Structures:** 1-2-4-All jako default protokol feedback
  fáze (silent first → obejde HiPPO; zadavatel hlasuje poslední), TRIZ
  jako pre-mortem ve 30. minutě S1 („za 6 měsíců to selhalo, proč?")
  pro security/compliance/QA risk surfacing dřív, než tým zamiluje
  variantu [baseline 01 — LS; synthesis 01 — E].
- **Z Design Thinking (IDEO):** prototype-as-thinking-tool, human-centered
  princip — ale **přeskočení Empathize fáze** přesunutím stakeholderů
  do místnosti (B2B / interní uživatelé jsou v Pflanzeru účastníci, ne
  subjekty výzkumu) [baseline 01 — DT].

## Co Pflanzer přidává (3 diferenciátory)

Bez nich je Pflanzer „Design Sprint 2.0 + Lean Inception lite" [baseline 01
— Syntéza]. S nimi je nová kategorie „AI-augmented alignment workshop".

### 1. Real-time AI vibe-coding viditelný stakeholderům

**Co:** Mockup vzniká **v session, ne mezi sessions**. AI generátor
(Claude, Cursor, Bolt, v0) v sub-hodinovém cyklu produkuje 1–3 funkční
varianty z verbálního inputu týmu. **BE shadow agent paralelně** generuje
draft OpenAPI 3.1 per varianta, takže contract žije ve stejném okamžiku
jako UI [synthesis 02 — sekce 1, bod 7].

**Proč to není v adjacentech:** GV Sprint má Figma fasádu, Lean Inception
má MVP Canvas (dokument), LDJ má sticky notes, Event Storming má post-its
na zdi, Pretotyping má Fake Door (statickou stránku). Žádná z metod
neprodukuje v session funkční artefakt s běžícím kódem.

**Co to umožňuje:** Demokratizace vizualizace pro non-designéry (Crazy
8s problém „nejsem designér" odpadá — AI kreslí), instant feasibility
check pro non-developery (FE/BE lead vidí, co znamená contract bump,
ne jen wireframe), instant accessibility quickscan + axe-core run
v session 1 (EAA gate posunut z post-launch na minutu 240) [synthesis
01 — FE × A11y].

### 2. Score závaznosti per oddělení

**Co:** 1–5 Likert s rationale field per role per varianta, weight per
role (Security / Legal / A11y high-risk = blocker, ne weighted vote),
hierarchie závaznosti **Critical (blocker) / Yellow (warning) / Score**
[synthesis 01 — D]. AI-only feedback **deflated max 0.5/1.0**
[synthesis 03 — #14]. Zadavatel hlasuje **poslední** (anti-HiPPO).

**Proč to není v adjacentech:** LDJ řeší „líbí se mi" (impact/effort dot
voting bez závaznosti), DS řeší „rozhodne Decider" (binární s vetem bez
nuance), Lean Inception má konsensus na Canvas (verbální, neukotvený),
Event Storming nemá hlasování. **Žádná z metod neřeší přemostění
propasti mezi „líbí se mi" a „tohle commitnu"** [baseline 01 — Syntéza].

**Co to umožňuje:** Eliminace late-stage veta (pre-charter triage 80 %
ex-ante, score zveřejněn až po hlasování — anti-HiPPO), atribuovaná
závaznost (decision log s lidskou atribucí splňuje DORA, AI Act čl. 14,
GDPR čl. 22 [synthesis 02 — takeaway 4]), učící smyčka (score uloženo
do DB pro retrospective T+30/60/90 vs reálný outcome).

### 3. AI-mediovaná syntéza feedbacku v Session 2

**Co:** Mezi-session sběr feedbacku per oddělení (klikací prototyp v
sandbox VPC, 24 h TTL, watermark) → AI v Session 2 **vede výklad**, jaké
oddělení mělo jaké připomínky a navrhuje, jak je zapracovat. Lidský
facilitátor zůstává jako **architect of accountability** — rozhoduje,
kdy AI mluví, kdy člověk mlčí, a kdy se konflikt eskaluje [synthesis 02
— takeaway 4].

**Proč to není v adjacentech:** GV Sprint nechává interpretaci
feedbacku na Decideovi (politická interpretace „co řeklo X oddělení"),
Lean Inception nemá feedback fázi mezi sessions (linear flow), LDJ končí
po jedné session. **Žádná z metod neodstraňuje politickou interpretaci
připomínek napříč odděleními.**

**Co to umožňuje:** Tří-režimová AI-human matice [synthesis 03]:
(1) **vlastnické a vetovací role** vždy člověk (zadavatel, PM final,
Security/Legal final, EM kapacita, A11y pre-launch, end-user novel
insight); (2) **konzultativní role** AI proxy + human sign-off 24–48 h
(UX, Data, QA test gen, CS, marketing draft); (3) **execution-heavy /
context-light** AI vede (mockup gen, transcript summary, clustering,
score aggregation, OpenAPI shadow, SBOM scan, axe-core, STRIDE draft,
Discovery Debt Detector, footprint kalkulačka). Tím Pflanzer respektuje
hranici „AI je nejlepší co-pilot v místnosti — ale nikdo nepodepíše
rozhodnutí, které udělala AI" [synthesis 02 — takeaway 4].
