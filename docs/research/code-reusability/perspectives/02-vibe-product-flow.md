# Perspektiva 02 — Vibe-Product-Expert (ex-Bolt PdM, ex-v0 power-user)

> Autor: Senior PdM, 8 let B2B SaaS, 3 roky daily user Bolt/v0/Lovable v product
> discovery. Viděl 40+ týmů použít vibe-coding tool — z toho ~ 8 týmů shipnulo
> do 2 týdnů, zbytek shnil. Tato perspektiva je o **product-flow defaults**
> (wizard / agenda / artefakty), ne o technické architektuře.

## TL;DR — 3 největší páky pro 80%+ reusability

1. **Variant C nesmí být "build from scratch" — musí být "evolve existing component".**
   Současné `VARIANT_ANGLES` (A happy-path / B multi-step / C smart defaults) jsou
   3 různé UX patterns nad **stejným prázdným plátnem**. To je optimální pro
   discovery, **katastrofa pro reuse**. Změnit jeden ze tří angles na
   "extend nejbližší existující komponentu z target_repo" donutí AI číst kód,
   ne ho vyrábět.

2. **Decider musí hlasovat 2× — preference (líbí) a merge-vote (PR-ready).**
   Aktuálně Decider's call je sociální akt o směru. Reuse vyžaduje druhý akt:
   *"Pokud bych to dostal jako PR zítra ráno, mergnul bych?"* Když odpoví ne,
   prototyp je discovery artefakt, ne ship-ready kód — a tým to musí vědět
   **před** odchodem z místnosti, aby reset očekávání nepřekvapil sponsora.

3. **Pre-session "Component scout" ritual je povinný pro `evolve` projekty.**
   Před `/pflanzer` musí jeden FE člověk strávit 30 min produkcí
   `data/preflight/<slug>/component-map.md` — 5-10 nejbližších komponent +
   tokens + design system rules. Bez tohoto AI **vždy** vyrobí nový Button,
   nový Modal, nový Form. Vidíme to v každé Bolt session, kde nikdo nemá repo
   loadnuté.

## Diagnose — kde aktuální Pflanzer flow sabotuje reuse

### 1. Wizard má 5 otázek, ale žádnou o existujícím kódu

`pflanzer.md` KROK 1-3 se ptá na **problém, lidi, risk profile**. Nikde se
neptá: *"Existuje v repu komponenta, která řeší 60 % tohoto problému?"* Nebo:
*"Která stránka v produktu je nejblíž tomu, co děláme?"* Bez této otázky AI
v KROK 4 dostane prázdný brief a vyrobí greenfield variantu i v evolve módu.
Charter má `throwaway_or_evolve`, ale prompt generátor (`_render_builder_prompt`)
ho zužitkuje jen na 1 řádek constraintu *"drž se design system tokenů"* —
to je **prosba, ne instrukce**.

### 2. Tři varianty × 30 min cap = race-to-paint, ne race-to-merge

30 min je dost na hezkou obrazovku, **málo** na pochopení existujícího kódu.
Bolt power-users to znají: první session je „postav něco co se hýbe", druhá
session je „udělej to správně". Pflanzer končí po první. Tým odejde s 3
mockupy, které všechny vypadají jako Bolt template. **Nejjasnější signál,
že kód je throw-away: žádná z variant nereferencuje cestu z `target_repo`.**

### 3. "Mezi-session 5-7 dní async feedback" je v reálu sabotáž

Tohle je sweet teorie a v praxi nejhorší část flow. Co se stane:
- Den 0: tým odejde nadšený.
- Den 1-2: 1-2 lidi zkusí klikat varianty, dají vágní feedback („líbí se mi B").
- Den 3-5: Slack-ticho. Sponsor zahltí jiné priority.
- Den 6-7: facilitátor panicky honí lidi, dostane povrchní feedback.
- Session 2: rozhoduje se na tenkém datasetu, často "B vyhrála, protože
  nikdo nehlasoval proti".

Pak Session 3 dostane "vítěze" se 2 hlasy a špatným kódem. **80% reuse je
nedosažitelné, protože nikdo neviděl kód kriticky.**

### 4. Handoff package = 8 souborů × 0 čtenářů

`handoff.py` generuje `decision.md`, `be.md`, `fe.md`, `qa.md`,
`platform.md`, `data.md`, `support.md`, `compliance.md`. Krásně strukturované.
**Kdo je čte?** V Bolt světě `RESULTS.md` čte přesně 1 člověk: ten, kdo má
zítra commit deadline. Per-role MD jsou compliance theatre — vypadá to
profesionálně v ADR, ale v reálu si BE přečte `be.md` jen pokud má kalendářový
slot „Pflanzer follow-up". Nemá.

### 5. Charter neukotvuje "ship contract"

`production_readiness_target = 85` je technical metric. Chybí **product
contract**: do jakého sprintu/release window kód musí být? Kdo dostane PR
review notifikaci? Kdo je Code Owner extracted slugu? Bez tohoto je
`target_repo_url` jen string v DB — nikdo neví, **kdy** PR vznikne.

## Concrete changes (5-10 specifických)

### C1. Přidat KROK 2.5 — "Component scout" do `pflanzer.md`

**Co**: Mezi KROK 2 (Decider+Room) a KROK 3 (Risk profile) vložit:

```
AskUserQuestion: "Existuje v target repu komponenta/stránka, která řeší
                  ≥ 50 % tohoto problému?"
options:
  - "Ano — vlož cestu(y) k souborům" [text → src/components/X.tsx, ...]
  - "Ne — greenfield (skip)"
  - "Nevím — pošlete FE lidem 30min úkol scoutovat"
```

Pokud "Ano" / "Nevím": volej `quick_session.py scout --slug <slug> --paths ...`
který načte soubory + jejich imports a vyrobí
`data/preflight/<slug>/component-map.md`. Tento soubor se **vždy** vloží
do builder promptu jako `## Existing components to extend`.

**Mechanism**: AI dostane konkrétní soubory k rozšíření, ne prázdné plátno.
**Měření**: `% promptů s neprázdným component-map.md` × `winner reuse %`.
Korelace by měla být > 0.6.
**Síla**: **High**.

### C2. Přepsat Variant C v `quick_session.py:298 VARIANT_ANGLES`

Změnit:
```python
("C", "smart defaults", "Postav variantu, která hádá inputy z kontextu...")
```
na:
```python
("C", "evolve existing", "Najdi v repu nejbližší existující komponentu/stránku, "
 "rozšiř ji o tento flow. Žádný nový soubor v src/components/ — jen edit + "
 "max 1 nový hook. Pokud nic vhodného nenajdeš, vrať 'NO_BASE_FOUND' a stop.")
```

Pro `risk_profile == "throwaway"` ponechat současné C (smart defaults) —
throwaway nepotřebuje reuse. Pro `pilot` / `production` automaticky swap.

**Mechanism**: 1 ze 3 variant je nuceně reuse-first. Když vyhraje, reuse je
99 %. Když nevyhraje, ostatní 2 musí vysvětlit Deciderovi proč ne.
**Měření**: `winner.angle == "evolve existing"` rate. Target ≥ 33 %.
**Síla**: **High**.

### C3. Přidat merge-vote do KROK 6 (`pflanzer.md`)

Po Decider's preference call (current KROK 6) přidat:

```
AskUserQuestion: "{Decider} — kdyby ti winner přišel zítra ráno jako PR
                 do {target_repo_url}, mergnul(a) bys ho dnes / tento týden /
                 nikdy bez přepsání?"
options:
  - "Merge dnes (rychlý fix typo OK)"
  - "Merge tento týden (potřebuje tests + 1 review)"
  - "Re-write — beru jako spec, ne jako kód"
  - "Throwaway — kód do koše, použijeme jen learnings"
```

Toto se uloží do `decisions` jako `type='merge_intent'` a je vstupem
pro Session 3 — pokud Decider odpověděl "Re-write", Session 3 hardening
**neběží** (šetří 30 min × 5 týmů = pět hodin/týden CI).

**Mechanism**: Sociální závazek nahoře v org → tým ví, že kód má být PR-ready,
ne demo-ready. Mění chování během 30 min sprintu.
**Měření**: `merge_intent in (today, this_week)` → reuse % delta vs
`re-write/throwaway`. Očekávám 2-3× lift.
**Síla**: **High**.

### C4. Přejmenovat "5-7 day feedback window" na "48h merge-readiness review"

V `pflanzer.md` KROK 8 + `04-session-1.md` § Délka — zkrátit:

> Mezi-session okno: **48-72 h**, ne 5-7 dní. Po 72h Session 2 běží tak jako
> tak, missing feedback = "no objection".

Plus změnit **úkol** mezi-session: ne "klikni a dej preference", ale **"otevři
PR diff winner branche, projdi files changed, napiš 1 komentář per soubor:
keep / fix / kill"**. Web hub musí zobrazit `git diff`, ne preview URL.

**Mechanism**: Krátké okno = nikdo nezapomene. Konkrétní úkol (diff review)
generuje actionable feedback místo „líbí se mi". 
**Měření**: `% reviewerů, kteří otevřeli ≥ 1 file diff` (Slice 6 tracking).
Target ≥ 60 %.
**Síla**: **High**.

### C5. Přidat 2 pole do Charter / `bootstrap()` v `quick_session.py:141`

```python
def bootstrap(
    *, hook, decider_name, room_role_idx, risk_profile, ...
    target_repo_url=None,
    target_branch_owner=None,    # NEW: GitHub handle Code Ownera
    ship_window_sprint=None,     # NEW: "S2026-21" nebo ISO week
)
```

Bez `target_branch_owner` u `risk_profile != throwaway` → wizard **bloknout**
otázkou *"Kdo merguje PR? (GitHub handle)"*. To je jediný způsob jak zajistit,
že někdo skutečně dostane notifikaci a má skin in the game.

`ship_window_sprint` se vyrenderuje do handoff banneru: *"Tento kód cílí
na S2026-21 (deadline 22. 5.). Pokud Session 3 score < target k 20. 5.,
re-prioritize."*

**Mechanism**: Ship contract = lidé + datum, ne číslo. Bez toho `production_readiness_target=85`
je hra na čísla.
**Měření**: `% projektů, kde se PR mergnul ≤ 7 dní po Session 3`. Současný
proxy je `handoff_pr_merged_within_7d`.
**Síla**: **Medium-High**.

### C6. Konsolidovat handoff package z 8 → 2 souborů + 1 PR draft

8 per-role MD nikdo nečte. Místo toho:

- `data/handoffs/<slug>/SHIP.md` — 1-page: co/kdo/kdy/jak otestovat/jak rollbacknout.
  Posílá se Slack DM Code Ownerovi + Deciderovi.
- `data/handoffs/<slug>/CONTEXT.md` — všechny ostatní detaily slepené (Charter
  + role notes + decision log + triage). Pro audit.
- **`gh pr create` command rendered out** s pre-filled title, body
  (z SHIP.md), labels (`pflanzer`, `risk:<profile>`), assignees
  (`target_branch_owner`), draft=true. Facilitátor copy-pastne, PR existuje
  do 30s po Session 3.

8 souborů zachovat na disku pro compliance, ale **default doporučení v wizardu
je "otevři PR teď"**.

**Mechanism**: Snížení friction PR → vznik = sekundy ne dny. Existující open
PR = magnet pro review.
**Měření**: `time_from_session_3_to_pr_open` (currently NULL, ~ days).
Target: < 30 minut.
**Síla**: **Medium-High**.

### C7. Pojmenovat post-session vlastníka — "Shadow PdM"

Po Session 1 jeden člověk (ne Decider, ne facilitátor) dostává roli
**Shadow PdM** = babysitter winneru přes 48-72h okno. Konkrétně:

- Den 0 18:00: pošle SHIP.md draft všem v room.
- Den 1: posbírá diff komentáře z web hubu, syntetizuje top 3 sporné body.
- Den 2 ráno: 15 min standup s Code Ownerem.
- Den 2 18:00: přepošle Sessionu 2 spec.

V `pflanzer.md` KROK 2 přidat:
```
AskUserQuestion: "Kdo bude Shadow PdM (babysitter winneru přes 48-72h)?"
[default: druhý nejstarší v místnosti, ne Decider]
```

Persistovat do `roles` jako pseudo-role `shadow_pm` (catalog_idx=99 nebo
nový sloupec `projects.shadow_pm`).

**Mechanism**: Bez konkrétního vlastníka mezi-session všechno padá. Shadow PdM
≠ PdM = jiný člověk → distribuce zátěže + nové eyes.
**Síla**: **High** (řeší root cause #3 v diagnose).

### C8. "No new files" guard pro evolve variants

V `_render_builder_prompt` (`quick_session.py:385`) pro evolve angles přidat:

```
HARD CONSTRAINT (proveď self-check před commitem):
- git diff --stat HEAD~ -- src/components/ | wc -l musí být 0
  (žádný nový soubor v components/, jen edit existing)
- max 1 nový soubor v src/hooks/ NEBO src/utils/
- pokud potřebuješ víc, zastav a napiš REUSE_BLOCKED.md s důvodem
```

**Mechanism**: AI má tendenci tvořit `NewFlowComponent.tsx` místo extend
existujícího. Hard constraint v promptu sníží tuto tendenci o ~ 50 %
(z mé zkušenosti s Cursor / Claude Code projects).
**Měření**: `new_files_in_components_count` per variant. Target = 0
pro evolve.
**Síla**: **Medium**.

### C9. Decider "merge clinic" rotation — ritualizovat ownership

Aktuálně extracted kód po Session 3 visí v `data/extracted/<slug>/` a
nikdo neví čí je. Zavést **týdenní 30 min "Merge Clinic"** (středa 16:00):
Decider + Code Owner + facilitátor projdou všechny otevřené PR z Pflanzer
sessions, rozhodnou: merge / kill / re-prioritize. Ritual ne tool.

V `04-session-1.md` § Reinforcement track přidat T+7: Merge Clinic.

**Mechanism**: Forcing function. Bez kalendářového slotu PR umírá.
**Síla**: **Medium**.

### C10. "Two-truth" rule pro Session 1 wrap-up

Před wrap-upem (KROK 7 v `pflanzer.md`) každý člověk u stolu odpoví:

```
AskUserQuestion: "1 věta — co bys jako první kritizoval(a) na winneru,
                  kdybys dostal(a) PR zítra ráno?"
```

Toto se uloží do `decisions` jako `type='self_critique'` a Shadow PdM dostane
to do briefu. Cíl: explicitně odhalit "tohle není ready" hlasy, které by
jinak zmizely v euforii konce sessiony.

**Mechanism**: Pre-mortem v miniformátu, ale na vítězi ne na rizicích.
Generuje konkrétní fix-list pro 48h okno.
**Síla**: **Medium**.

## Anti-patterns — co tým NIKDY nedělat

1. **"Vyhrála A — zahoďte B a C."** — Hrubá chyba reuse strategie. B/C často
   obsahují jeden komponent / hook, který je lepší než ve A. **Vždy** projet
   `git diff` mezi A↔B a A↔C, cherry-pick reusable kousky před extract.

2. **Decider říká "líbí se mi všechny tři" bez tax.** — Per ADR Decider's tax,
   max 2 varianty na shortlist. Pokud Decider ani po taxu nevybere, problém
   je v briefu (KROK 1 hook), ne v variantách.

3. **"Tým má capacity, vyrobíme paralelně Storybook + tests + docs."** —
   Bolt anti-pattern: capacity expansion ničí focus. Drž scope na 1 flow,
   1 testní cesta, žádné docs do v1 PR.

4. **"Web hub má pretty preview, lidé budou klikat."** — Falešný idol. Pretty
   preview generuje "líbí se mi", což je **nulový signál pro reuse**. Web hub
   musí defaultně otevřít diff view, ne sandbox iframe.

5. **"Sponsor není v room, posíláme handoff PDF."** — Z 8 sledovaných týmů,
   všechny 4 týmy bez sponsora-in-room shnily. Sponsor v Sessione 1 (alespoň
   posledních 30 min) je ne-vyjednávatelná podmínka pro `production` profile.

6. **"Variant builder je různý → diversita."** — Aktuálně default je 3× claude-code
   se 3 angles. To je správně. NEPŘIDÁVAT různé buildery pro diversity (Bolt vs v0
   vs Lovable) — zvyšuje to friction extractu a snižuje reuse, protože každý
   builder má jiný design system bias.

7. **"Mezi-session feedback necháme open-ended."** — Open-ended = "líbí". Vždy
   structured: keep/fix/kill per file, max 1 věta. Web hub musí enforced.

## Tool / process recommendations

### Wizard / orchestrator (konkrétní edits)

- `pflanzer.md` KROK 2.5 — Component scout (C1).
- `pflanzer.md` KROK 6 — merge-vote (C3).
- `pflanzer.md` KROK 7 — two-truth (C10).
- `quick_session.py:38 RISK_PROFILES` — přidat `pilot.requires_target_branch_owner=True`,
  `production.requires_ship_window=True`.
- `quick_session.py:87 DEFAULT_ROOM` — pro `evolve` profile přidat default
  Code Owner role (#5 BE nebo #4 FE) jako mandatory.
- `quick_session.py:298 VARIANT_ANGLES` — swap C podle profile (C2).
- `quick_session.py:385 _render_builder_prompt` — inject `component-map.md`
  + "no new files" guard pro evolve (C8).

### Web hub (Slice 6)

- Default route `<slug>/<variant>` = **diff view** (`git diff main...feat/<slug>-X`),
  nikoli preview iframe. Preview je secondary tab.
- Reviewer flow: per soubor → keep / fix / kill + 1 věta. Bez toho nelze
  submit feedback. Limit 1 minuta per soubor (subjektivní progress bar).
- Push notification 24h, 48h, 70h před Session 2 deadline (Shadow PdM jako recipient).

### Handoff (Slice 8)

- `handoff.py` — generovat `SHIP.md` (1 page) + `gh pr create` command jako
  primary output. 8 souborů zachovat jako `--full` flag (compliance).
- Auto-Slack post (webhook) `data/handoffs/<slug>/SHIP.md` Code Ownerovi.

### Reinforcement (T+7)

- Týdenní Merge Clinic v Decider's kalendáři. Tool nemůže forcovat, ale
  může generovat agenda PDF (`/pflanzer-clinic-agenda` slash command, 5 min).

### Charter fields, které chybí

- `target_branch_owner` (GitHub handle, mandatory pro non-throwaway).
- `ship_window_sprint` (volitelné, ale silně doporučené).
- `shadow_pm` (jméno, mandatory pro non-throwaway).
- `merge_intent` (post-Session-1, populated by Decider).
- `existing_component_paths` (list[str], populated by Component scout).

---

**Zkrácený fix-list pro synthesis** (priorita pro 80% reuse target):

1. C1 (Component scout) + C2 (evolve variant) — bez tohoto greenfield bias zůstává.
2. C3 (merge-vote) + C5 (Charter ship contract) — Decider committed na merge, ne na líbí.
3. C4 (48h diff review) + C7 (Shadow PdM) — mezi-session není sabotáž.
4. C6 (handoff → PR za 30s) — closes loop k mergnutí.

Zbylých C8/C9/C10 jsou amplifiery — implementace má hodnotu jen po C1-C7.
