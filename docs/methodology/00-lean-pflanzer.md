# Lean Pflanzer — default profil (1-pager, v0.5)

**Pflanzer Method | pflanzer.cz/method**

> **Tohle čti první**, pokud chceš metodu **použít**, ne studovat.
> Kanonický zdroj průběhu a terminologie: ADR-0021; stupně a okna: ADR-0017. Pro regulované
> prostředí (banky, DORA, AI Act High-risk) viz `docs/governance/`.

## Co Pflanzer Method je

**Malá skupina, ve které je zastoupena celá cesta** od nápadu do produkce,
postaví s AI co-pilotem 3 funkční varianty, rozhodne nad běžícím kódem
a vítěz jde rovnou do produkce. Žádné sériové předávání zadavatel →
produkt → vývoj → security → provoz; každý krok cesty je u toho, ale jen
tak dlouho, jak je potřeba.

Šéfovi stačí [`../pro-decidera.md`](../pro-decidera.md), kolik to stojí je
v [`../zacni.md`](../zacni.md#kolik-to-stojí).

Jediný vstup: `/pm` (`/pm status` ukáže fázi a další krok). Tři pravidla:

1. **Celá cesta je zastoupena.** Každý ze 6 kroků cesty má jednoho
   pojmenovaného zástupce s mandátem. Krok bez jména = nesvolávat.
2. **Malé jádro, ostatní na okna.** 3–4 lidé jsou u toho celou dobu,
   ostatní přijdou na krátké okno nad konkrétním artefaktem.
   Nikdy víc než 5 lidí naráz.
3. **Automat místo lidí v místnosti.** Sandbox a quality gates pokryjí,
   co jde zkontrolovat strojem; lidé řeší zbytek.

## Kdo — 6 kroků cesty

| Krok cesty | Zástupce (typicky) | Účast |
|------------|--------------------|-------|
| Byznys | Zadavatel / sponzor = **Decider** | okna: Kickoff 15 min + Rozhodnutí |
| Produkt | PdM (často i facilitátor) | **jádro** |
| Design | UX / Designer | **jádro** (u interního toolu může krýt PdM) |
| Vývoj | 1–2 vývojáři (FE / BE) = buildeři | **jádro** |
| Bezpečnost & právo | Security nebo Legal / DPO (jeden stačí) | okno: checkpoint 20 min |
| Provoz | DevOps / Platform nebo EM | okno: checkpoint 20 min u Ship |

Jeden člověk smí krýt víc kroků (vývojář = vývoj + provoz je běžné).
Chybí-li člověk, smí některé kroky v omezené míře zastoupit AI (design,
předkontrola bezpečnosti & práva a provozu) — podepisuje ale vždy člověk
(design PdM přes `checkpoint … design`; bezpečnost v pořadí: člověk
s mandátem z firmy → Decider vědomě přebírá riziko přes `--override-triage`
→ autor kódu jen jako poslední možnost u pilotu bez osobních dat),
Decidera a vývoj AI nenahradí nikdy (ADR-0023,
[`02-role-catalog.md` § AI náhrada](02-role-catalog.md#ai-náhrada-chybějícího-zástupce)).
Kdo přesně může krok zastoupit, říká `02-role-catalog.md` — catalog
je **knihovna zástupců**, ne seznam pozvánek. Každému zástupci pošli jen
jeho **role card** (1 strana: co do svého okna přinést, co podepisuje, kdy
být v místnosti, na co hlasuje) — [`role-cards/README.md`](role-cards/README.md),
pro konkrétní projekt se jmény a stupněm `pflanzer roles cards --slug <slug>`.

## Tři stupně jedné metody

> **Autoritativní definice** (ADR-0017). Délka Buildu, rozsah kontroly
> bezpečnosti & práva a délka Async okna jsou definované **jen v této
> tabulce**. README, `00-tldr.md`, `04-session-1.md`, `/pm` i `/pm live` sem
> odkazují. Na povrchu je jedna metoda s pěti kroky; stupeň jen říká, kolik
> rituálů se kolem nich pustí. Tool ho drží v `projects.tier`
> (`pflanzer status`).

| Stupeň | Build | Bezpečnost & právo | Async okno | Kdy použít | Command |
|--------|-------|--------------------|------------|------------|---------|
| **Quick** | Kickoff + Build v jednom, 60–90 min, 1 kolo × 30 min stavby → silent vote → shortlist | checkpoint odložený (před pilotem se doběhne `/pm triage`) | 3 pracovní dny | Rychlé ověření směru, první kontakt týmu s metodou; **jen risk profil `throwaway` / `pilot`** (pro `production` upgrade na Lean) | `/pm live` |
| **Lean** (**v0.5 default**) | 3 h, jádro; stavba s průběžnými kontrolami a mid-checkpointem → diff walkthrough → silent vote | checkpoint 20 min + lehký 1-pager checklist | 3–5 pracovních dní | Default — interní tool, SaaS feature, non-regulated projekt s vývojářem v jádru | `/pm start` → `/pm build` |
| **Full** (governance / regulované) | 5–6 h, kompletní agenda `04-session-1.md` (VoC, pre-mortem, Crazy 8s, shadow agenti, A11y quickscan) | 4 triage tracky povinné (Discovery + Security + Legal + Platform) | 5–7 pracovních dní | AI Act High-risk, DORA, public sector, rollout metody napříč organizací (viz § Kdy default NEstačí) | `/pm roles` → `/pm triage` → `/pm build` |

Všechny tři stupně mají **stejné jádro**: vývojář u klávesnice od minuty 0,
3 paralelní varianty, anti-HiPPO (silent vote, Decider hlasuje poslední)
a Decider s mandátem — liší se jen množstvím rituálů kolem. **Rozhodnutí je
ve všech stupních stejné** (`/pm decide`, 60–90 min; Full smí využít 3h
rozšířenou agendu). **Po Rozhodnutí následuje Ship, ne další setkání:**
pipeline (gates na vítěze + `SHIP.md`), kterou po Go pouští vývojáři
(`/pm ship` + `/pm handoff`). Délku okna per stupeň a pravidla pro mlčení po
deadline určuje [ADR-0017](../decisions/0017-mezi-session-okno-per-stupen.md).

## Průběh (~8 dní, ~6–8 PD)

```
Před     pflanzer doctor — repo připravené? (testy, CI, preview, CONSTITUTION)

Den 0    KICKOFF        15 min     Decider + jádro
         → zadání na 1 stránku: problém (1 věta), metrika úspěchu,
           kill kritérium, jména zástupců všech 6 kroků, zabookovaná okna
         /pm start   (nebo rovnou /pm live)

Den 1–5  BUILD          3 h        jádro
         → AI staví 3 varianty paralelně (Claude Code ve 3 worktrees
           target repa); jádro sedí u jedné obrazovky a směruje
         → v posledních 30 min: CHECKPOINT bezpečnost & právo (20 min)
           nad datovým tokem, data classification, egress limitem, stropem
           tokenů/nákladů a rizikem prompt injection (worktree není izolace)
         /pm live  nebo  /pm build

         ASYNC          3–5 dní    všichni zástupci
         → klikají na preview URL (štítek „k rozhodnutí, ne produkt"),
           komentují; builder zapracovává
         /pm feedback

Den ~7   ROZHODNUTÍ     60–90 min  Decider + jádro
         → 10 min demo, agregovaný feedback, top 3 spory,
           silent voting, Decider hlasuje POSLEDNÍ → Go / Iterate / Kill
         /pm decide

Den ~8   SHIP           1–2 dny    vývojáři + provoz
         → quality gates jen na vítěze, práh pilot 80 / production 85,
           CHECKPOINT provozu (20 min), PR do
           target repa, deploy, monitoring
         /pm ship  →  /pm handoff
```

Pod povrchem platí tato pravidla (rozšířená reference v 04–07):

- **Build:** před hlasováním **diff walkthrough** — vývojářský pár na
  každé variantě ukáže `git diff --stat` a řekne reuse / nové / mock;
  u klávesnice sedí vývojář, ne facilitátor (N10). Preview per varianta:
  draft PR s preview URL nebo Playwright záznam (`docs/postup.md`
  § Kde varianty fyzicky jsou).
- **Async:** technické role (vývoj, QA, provoz) projdou PR diff a ke každému
  souboru napíšou **keep / fix / kill**; ostatní hodnotí preview. Mlčení
  nevetovací role po deadline = „no objection“ v decision logu, mlčení
  vetovací role souhlas není (ADR-0017). Připomínka 48 h a 24 h před deadline.
- **Ship:** příkazy gates bere adaptér `pflanzer.gates.yml` z base branche
  target repa (varianta ho nepřepíše); verdikt potřebuje aspoň build
  a testy. Commity nesou trailery `Pflanzer-Variant` / `AI-Assisted`
  a PR labely `pflanzer` / `ai-generated` (**AI provenance**, N11); SHIP.md
  ukazuje i **AI náklady** (tokeny per varianta a za cyklus).
- **Retro:** po merge vítěze `/pm retro` změří % LOC vítěze v produkci
  a days-to-prod a nastaví readouty T+7/30/60/90 — viz `docs/zacni.md`
  § Co měřit.
- **Iterate** = jedno další Build kolo (max 1×), pak Go nebo Kill.
  Třetí kolo = problém je špatně zadaný, vrať se ke Kickoffu.
- „Session 1 / Session 2" ve starších dokumentech = Build / Rozhodnutí.
  „Session 3" = Ship (pipeline, ne setkání).

## Co tým dostane

- **3 funkční varianty** (ne mockupy) na sandbox URL, každý zástupce
  je vidí ve svém prohlížeči.
- **Kód vítěze** s gate score ≥ 80 (pilot) / 85 (production) jako PR do target repa.
- **Decision log** v target repu (`.pflanzer/decisions/<slug>.md`) — kdo co
  rozhodl a proč, včetně checkpointů.
- **Měření outcome** (`/pm retro`): kolik kódu vítěze žije v produkci a co
  se s ním stalo za 7 / 30 / 60 / 90 dní.

## Proč malá skupina

- Nad ~4 lidi u jedné obrazovky klesá zapojení; zbytek se stává diváky.
- AI přesunula úzké hrdlo z psaní kódu na rozhodování — to potřebuje
  mandát, ne počet lidí.
- Zástupce kroku v 20min okně nad konkrétním artefaktem přinese víc než
  stejný člověk 3 hodiny v místnosti, kde se ho nic netýká.

Evidence a její limity: ADR-0021 § Evidence.

## Kdy default NEstačí

Přidej vrstvu z `docs/governance/`, pokud platí **kterékoli**:

1. **AI Act High-risk** (čl. 6 + Annex III).
2. **DORA scope** (banky, pojišťovny EU).
3. **Public sector / zvláštní kategorie osobních dat** (DPIA).
4. **Rollout metody napříč organizací** (3+ pilotů).

**PSD2 SCA / platební flow** → standardní SDLC, Pflanzer se nehraje.

Vývojáři nejsou k dispozici → nejdřív je získej. Track S (spec místo
produktu) je nouzová cesta, viz `docs/governance/`.

## Anti-patterny

- **Krok cesty bez jména.** Typicky bezpečnost nebo provoz — pak se
  „rychlý" kód zasekne před produkcí. Nesvolávat.
- **Víc než 5 lidí naráz.** Zúžit scope nebo rozdělit.
- **Zástupce bez mandátu.** Kdo nemůže v okně rozhodnout, není zástupce.
- **Decider hlasuje první** nebo přijde „jen se podívat" do Buildu.
- **Okna se domlouvají ad hoc.** Bookují se na Kickoffu.
- **Vývojář není v jádru.** Pak to není Pflanzer, ale workshop s mockupy.

## Vztah k ostatním dokumentům

- `01-filozofie-a-kdy-pouzit.md` — fit / no-fit.
- `02-role-catalog.md` — kdo může zastoupit který krok.
- `04-session-1.md`, `05-mezi-sessions.md`, `06-session-2.md`,
  `07-handoff-do-vyvoje.md` — rozšířené referenční detaily (playbooky
  konfliktů, agendy pro větší/regulované projekty). Kde se liší od
  tohoto 1-pageru, platí tento 1-pager a ADR-0021.
- `docs/governance/` — audit-grade vrstva.
