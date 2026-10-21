# Glossary — Pflanzer terminologie

> **v0.6 (ADR-0021):** Default průběh a sestavu definuje `00-lean-pflanzer.md` — malá skupina (jádro 3–4 + okna pro zástupce kroků cesty, max 5 naráz). Terminologie v0.6: Kickoff → Build → Sběr feedbacku (Async) → Rozhodnutí → Ship; „Session 1/2“ = synonyma Build/Rozhodnutí. Glossary je rozšířená reference; kde se liší, platí 1-pager.

> Definice termínů, kde panovala nejednoznačnost. **v0.4, 2026-05-28; pojmy v0.6 doplněny 2026-10-21.**
> Updated po dual-track design (`docs/research/dual-track-design/`)
> a output consistency audit (`docs/research/output-consistency/`).

## Závazné termíny ve výstupech

Tyto termíny se ve výstupech toolu (CLI, hub, PR, SHIP.md, decision log) používají vždy stejně.

| Termín | Význam |
|---|---|
| **brána** | Jedna automatická kontrola kvality (např. testy, lint, bezpečnost). |
| **skóre bran** | Souhrn všech bran jako číslo 0–100, ve výstupech jako věta „Skóre X ze 100 z N automatických kontrol“. Neměří splnění zadání. |
| **částečné skóre** | Skóre, když část kontrol neproběhla (chybí nástroj, typová kontrola, pokrytí). Věta to řekne hned („Skóre 100 ze 100, ale neproběhlo N kontrol“) a práh se nepotvrdí, dokud nejsou aspoň build a testy. ADR-0024. |
| **práh** | Minimální skóre bran, od kterého Ship projde (pilot 80, production 85). |
| **podpis okna** | Okno = krátká kontrola jedné role (příkaz `checkpoint`); podpis okna říká, že role výsledek viděla a souhlasí. |
| **zástupce kroku** | Člověk, který zastupuje jeden krok cesty (Produkt, Design, Vývoj, Bezpečnost & právo, Provoz). |
| **Rozhodnutí** | Setkání Decidera: **Go** (jde se do Shipu), **Iterate** (jedno další kolo), **Kill** (konec). |
| **závaznost** | Jak moc se tým za variantu postaví, stupnice 0–3 (v datech `commitment_level`); na Go stačí 60 %. |
| **Sběr feedbacku** | Fáze Async (3–5 dní): zástupci píší připomínky k variantám (hub nebo offline `feedback add --by`); souhrn a kdo mlčí dá `feedback_pull`. |
| **record** | `pflanzer record` (dřív `vote`): zápis hodnocení Buildu (varianty, preference, rozhodnutí o shortlistu). Bez něj hub varianty neukáže. |
| **share** | `pflanzer share`: jedním příkazem pustí preview variant i hub na jedné adrese, heslo se pošle zvlášť, vypíše zprávu kolegům s termínem (`--deadline`). `share down` vše ukončí. |
| **report** | `pflanzer report summary --slug S` (stránka pro vedení: rozhodnutí, náklad, kvalita, rizika) a `report portfolio` (tabulka přes projekty, `--csv`). |
| **sloučené okno** | Okno **Bezpečnost a provoz** (`checkpoint … bezpecnost-provoz`): u pilotu bez osobních dat nahrazuje zvlášť Bezpečnost & právo a Provoz. S osobními daty zůstávají okna zvlášť; Právo (DPIA) samostatně jen u Full, když triage DPIA odložil. |
| **Jak vážné to je?** | Jediná otázka Kickoffu (demo / pilot / ostré + osobní údaje); odvodí stupeň Quick / Lean / Full, okna a prahy. `personal_data: true` = třída dat aspoň L3. |
| **závažnost** | Tři úrovně: **Kritické** (blokuje nasazení), **Důležité**, **Drobné**. |

Mapování závažnosti: CLI vstup `critical` = Kritické; `major` / `high` = Důležité; `minor` / `medium` / `low` = Drobné.
V databázi zůstávají hodnoty `critical`, `high`, `medium`, `low`; hub formulář nabízí `critical`, `high`, `low`.

## Track terms (v0.4)

### Track P (Preferred)

**Default Pflanzer track (~80 % cases).** Dev #4 (FE/vibe-coding lead) +
#5 (BE/API lead) jsou v room od minuty 0 celý Session 1. Output cyklu =
**běžící produkt na URL**, deployment D11-14. Žádný handoff k re-implementaci
— dev tým byl v room.

Charter potvrzuje track = P (default, zero-friction). Definováno v ADR-0020.

### Track S (Fallback)

**Fallback Pflanzer track (~20 % cases).** Dev tým NENÍ v room — z 1 ze
4 hard triggers:

1. Distributed dev tým ≥ 3 časové pásma
2. AI Act High-risk + certified production
3. FDA / IEC 62304 / DO-178C / PSD2 SCA
4. Sponsor mandate spec-as-deliverable (multi-vendor, legacy modernization, acquisition DD)

Output cyklu = **precision spec ≥ 80/100 quality gate** + 5-stage handoff
ritual. Track S NESMÍ být easy escape hatch — bez triggeru = projekt odložit,
ne přepnout. Definováno v ADR-0020.

**Track S re-impl gap target ≤ 15 %** (vs SDD 9.8-42.1 %, vs Track P ~0 %).

### dev-in-room

Konkrétně **#4 FE / Vibe-coding lead + #5 BE / API lead** (z role catalogu)
fyzicky / virtuálně v session od minuty 0 celý Session 1. Builder lead =
dev v driver-seat AI co-pilot session (NE facilitátor s AI proxy).

Dev-in-room je **fit criterion pro Track P** (mandatory). Pokud nelze
zajistit, Track S nebo odložit projekt.

### precision spec

Output Track S Session 2. Markdown dokument ≥ 80/100 quality gate na
12 dimensions:
- Functional (INVEST-RA user stories, Gherkin BDD, edge cases)
- Technical (OpenAPI 3.1, ERD, tech stack constraints)
- Quality (STRIDE, WCAG, AI Act/DPIA/DORA)
- Implementation (file structure, naming, anti-patterns)
- Sign-off (12-role matrix s veto rights)

**Reference prototype z Session 1 = combined SoT s spec** (anti-drift weapon
unique pro Pflanzer vs SDD).

Template: `tool/templates/precision-spec-track-s.md.template`.

### 5-stage handoff ritual (Track S only)

Když dev tým není v room a spec jde k nim:

1. **90-min walkthrough** — PdM + dev lead + spec authors
2. **5-day Q&A window** — dev klade otázky, spec authors odpovídají
3. **Amendment protocol** — dev requests changes, sponzor approves
4. **First milestone review** — dev demos first slice, spec authors verify
5. **T+30 embedded reviewer** — spec author shadows dev sprint, detects drift early

Definováno v ADR-0020.

## Core deliverable terms

### produkt (product)

**Primary output Pflanzer cyklu.** Běžící, klikatelný, deploy-able,
auditovatelný kód v target prod repo. Po Session 2 už existuje na
production-grade URL; dev tým (který byl v room od minuty 0) ho během
D11-14 doladí (observability, monitoring, edge cases).

**Synonyms (allowed):** běžící produkt, running product, production-ready code.

**NOT synonyms (deprecated):** prototyp, mockup, handoff package, klikatelná
ukázka.

### artefakt (artifact)

V Pflanzer kontextu **= produkt** (viz výše). Termín *„artefakt"* se používá
v anti-SDD argumentaci (*„artefakt > spec"*) jako protiklad k dokumentu.
**Pflanzer artefakt JE running production code**, ne Figma mockup, ne PDF
spec, ne PowerPoint slide.

Etymologie: latinské *arte factum* („udělaný řemeslem"). V SW inženýrství
obecný termín pro hmatatelný výstup (kód, build, dokumentace). V Pflanzer
copy = specificky *„běžící produkční artefakt"*.

### sign-off package (formerly „handoff package")

**Audit trail + compliance evidence**, který padá ven po Session 2:
- decision log s human attribution per AI Act čl. 14
- preference matrix + score závaznosti per role + veto registr
- DORA 7y audit log entry
- Acceptance kritéria (Gherkin)
- Compliance pakety (DPIA, AI Act Annex IV, Privacy Notice, SBOM,
  secret scan, A11y axe-core, SLO baseline) — audit-grade jen

**Sign-off package NENÍ re-implementation spec.** Dev tým si podle něj
nestaví produkt — ten je už v target repo. Sign-off package slouží **audit**
+ **post-launch reinforcement** (T+7/30/60/90 retro material).

**Deprecated:** *„handoff package"* — slovo *„handoff"* implies *„throw to
dev team"*, což protiřečí Pflanzer claimu *„dev was in room from minute 0"*.

> **`/pm handoff`** je jen název příkazu (stabilní rozhraní, ADR-0010):
> vytvoří `SHIP.md` + sign-off package a vítěz jde přes PR do běžného
> vývojového procesu. Není to předání k re-implementaci.

### AI code provenance

**Atribuce AI-asistovaného kódu** (doplněk k atribuci rozhodnutí v decision
logu). Autor commitu = dev, který seděl u klávesnice, a ručí za kód jako za
vlastní; AI nikdy není autor. AI asistence se značí commit trailery
(`Pflanzer-Variant`, `Pflanzer-Session`, `AI-Assisted`) a PR labely
(`ai-generated`, `pflanzer:<slug>`); review je stejná jako u lidského kódu.
Definováno v `07-handoff-do-vyvoje.md` § AI code provenance.

## Profile terms

### evolve (default)

**Default mode**. Winner varianta z Session 2 jde **přímo do produkce**.
Dev tým (#4 + #5 byli v room) ji doladí pro production hardening
(observability, monitoring, edge cases) během D11-14. Quality gates
(pilot ≥ 80 / production ≥ 85 ze 100) = production prerequisite, ne *„prototype hardening checklist"*.

### throw-away (explicit opt-in)

Flag v Charteru pro **3 výjimky**:
1. **Discovery-only piloty** — žádný produkční záměr, jen falsifikace XYZ.
2. **Audit-grade evidence collection** separate od prod (compliance artefakt
   k regulatorní show-case).
3. **Regulatorní gate kde production = certified production** (FDA, IEC 62304,
   DO-178C, některé AI Act High-risk uses), kde MUST existovat separate
   implementation track.

**Throw-away NENÍ default** (vyřešeno od v0.3.1; potvrzeno ADR-0005 a ADR-0021). Sponzor musí podepsat v Charteru
*„throw-away"* explicit a uvést který z 3 use casů aplikuje.

## Session terms

### Session 1 output

**3 paralelní produkční-ready varianty** na sandbox URL (default profile).
NE *„mockupy"*, NE *„klikací prototypy"* — vibe-coding tools (Bolt, v0, Lovable,
Claude Code) v 2026 produkují **production-grade kód** s ESLint pass + types +
Vitest defaults. Sandbox je guardrail (24h TTL, watermark, network default-deny),
ne *„prototype playground"*.

### Session 2 output

**Winner varianta selected for prod** + sign-off package.

### Session 3 (nepoužívá se)

**Session 3 se nepoužívá** (ADR-0021) — produkční hardening = **Ship**
(`/pm ship`, gates na vítěze + checkpoint provozu); **Iterate** =
další Build kolo (max 1×), ne třetí session.

**Alias (deprecated):** *„Session 3“* — starší název v toolu; command
`/pflanzer-session-3` zůstává jako implementace pod kapotou `/pm ship`.
Iterační rozhodovací session po Iterate (ADR-0001 Scenario B/C) se jmenuje
**Session 2b** (dříve také „Session 3“) — to není Ship.

### Stupeň (Quick / Lean / Full)

Míra rituálů kolem stejného jádra metody (vývojář u klávesnice, 3 paralelní
varianty, anti-HiPPO, Decider). **Quick** = `/pm live`, Kickoff + Build
v jednom, 60–90 min, okno 3 dny, jen `throwaway` / `pilot`. **Lean** =
**v0.6 default**, Build 3 h, Sběr feedbacku (Async) 3–5 dní. **Full** = governance /
regulované, rozšířená agenda 5–6 h (`04-session-1.md`), 4 triage tracky,
okno 5–7 dní. Rozhodnutí je ve všech stupních stejné. Autoritativní tabulka:
`00-lean-pflanzer.md` § Tři stupně jedné metody (ADR-0017). Tool ukládá
stupeň do `projects.tier`.

### Ship

**Pipeline, ne setkání.** Po Go v Rozhodnutí ji pouští vývojáři: quality
gates na vítěze (score 0–100, pilot 80 / production 85) + `SHIP.md` → PR
připravený k mergi (`/pm ship` + `/pm handoff`). Starší název „Ship gate“.

### Retro

`/pm retro` — měření outcome po Shipu: % LOC vítěze v produkci, days-to-prod
a readouty T+7/30/60/90. Pod povrchem, mimo pět kroků hlavní cesty.

### AI náhrada

Krok cesty, u kterého místo jména stojí `AI` (nebo `AI:<agent>`). AI **připraví**
(perspektivu, předkontrolu, návrh checkpointu), **podepisuje člověk**. Nikdy
u kroků byznys a vývoj; u produktu jen ve stupni Quick / throwaway; u designu
ano; u bezpečnosti & práva a provozu jen jako předkontrola. Viz ADR-0023
a `02-role-catalog.md` § AI náhrada chybějícího zástupce. Design potvrzuje
PdM (`pflanzer checkpoint --slug S design --by <PdM>`). Podpis bezpečnosti
autorem kódu je jen varování (pilot bez osobních dat), právo tím pokryté
není.

### Override triage

Vědomé převzetí rizika Deciderem, když bezpečnost & právo nikdo nepodepsal:
`pflanzer ship --slug S --override-triage --rationale "…"`. Do decision
logu se zapíše jeho jméno; u pilotu bez osobních dat.

### Checkpoint

20minutové okno nad konkrétním artefaktem (bezpečnost & právo u Buildu,
provoz u Shipu), které končí podpisem: `pflanzer checkpoint --slug <slug>
bezpecnost|provoz|bezpecnost-provoz --by <jméno> --note …`
(`bezpecnost-provoz` = sloučené okno u pilotu bez osobních dat; aliasy `bezpecnost`/`provoz` v něm fungují stejně). Zadání podepisuje Decider, při Kickoffu s metrikou a kill kritériem samo; AI návrh podpis člověka nikdy nepřepíše (ADR-0023). Checkpoint zapsaný AI (`--ai`) je
jen návrh, dokud ho nepodepíše člověk.

### Quality gate

Automatická kontrola (lint, typy, testy, bezpečnost, přístupnost, build)
puštěná jen na vítěze. Výsledkem je skóre ze 100 („Skóre X ze 100 z N automatických kontrol“); práh pilot 80 / production 85 (ADR-0024).

### Worktree

Oddělená kopie repa pro každou variantu (větve `pflanzer/<slug>-A|B|C`).
Není to bezpečnostní izolace — sdílí soubory a síť stroje.

## Zkratky

### PdM

**Produkt manažer** (role #2 v `02-role-catalog.md`). Zkratka „PdM" se
v češtině neskloňuje, takže sedí do vět beze změny tvaru.

### PM

**Pflanzer Method.** Používá se **jen** v názvu commandu `/pm`, nikdy v textu
(brand pravidlo v `CLAUDE.md`). Pro produkt manažera piš „PdM".

## Anti-patterns (deprecated language)

| ❌ Deprecated | ✅ Use instead | Why |
|--------------|---------------|-----|
| „prototype" | „produkt" / „varianta" | Underselling — Pflanzer output IS production code |
| „mockup" | „varianta" / „produkt" | Same as above |
| „klikatelný prototyp" | „běžící produkt na URL" | Stronger claim |
| „handoff package" | „sign-off package" | „Handoff" implies dev re-implementation; Pflanzer dev was in room |
| „dev team picks up the prototype" | „dev team byl v room, kód jde do prod" | Contradicts core claim |
| „Prototype-to-Prod (P2P) checklist" | „Production readiness checklist" | Naming |
| „extract code" (Ship) | „polish + observability" | „Extract" implies code wasn't prod-ready |
| „Session 3" / „3 sezení" | „Ship" / „Kickoff, Build, Sběr feedbacku (Async), Rozhodnutí, Ship" | Ship je pipeline, ne setkání |
| „re-implementation" | (don't mention; not part of cycle) | Antithesis Pflanzer |
| „PM" pro produkt manažera | „PdM" (nebo „produkt manažer") | „PM" je vyhrazeno pro Pflanzer Method a smí být jen v názvu commandu `/pm` |

## Reference

- ADR-0005 throw-away vs evolve prototype (v0.4: default = evolve, throw-away = explicit opt-in pro 3 use cases)
- `docs/research/output-consistency/03-synthesis.md` — audit findings + recommendations
- User clarification 2026-05-28: *„Výstup z Pflanzer metody je hotový produkt."*
