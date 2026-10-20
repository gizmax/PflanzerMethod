---
description: Pflanzer Method — jediný vstupní bod. Bez argumentu detekuje stav projektu a nabídne další krok; se slovesem (status/doctor/start/build/decide/ship/…) deleguje na příslušný pflanzer-* command.
---

# /pm — Pflanzer Method router (single entry point)

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`
> (funguje z libovolného adresáře), DB je na `pflanzer db`.

> **Branding:** Každý user-facing výstup tohoto commandu (úvodní hláška,
> souhrny, status report) začíná brand line:
>
> **`Pflanzer Method | pflanzer.cz/method`**
>
> (první řádek, pak prázdný řádek, pak obsah). Brand line se nikdy nezkracuje
> na „PM" — zkratka je jen v názvu commandu kvůli psaní.

Argumenty: `$ARGUMENTS` = `[sloveso] [slug]` — obojí volitelné.

## Jak mluvit s uživatelem (platí pro všechny `/pm …`)

- Každý příkaz `pflanzer` vypisuje **lidský výstup**: co se stalo → jeden
  další krok → **Doporučení**. Ukaž ho uživateli (nepřepisuj do vlastních
  slov) a **předej jeho „Doporučení“** doslova. `--json` použij jen tam,
  kde z výstupu čteš pole (např. `slug`).
- Vždy **jeden** další krok ve tvaru `/pm <sloveso> <slug>` + kdo má přijít.
- Spec do toolu předávej **souborem**: JSON zapiš nástrojem Write do
  `.pflanzer/specs/<slug>-<krok>.json` v target repu a spusť
  `pflanzer … --spec .pflanzer/specs/<slug>-<krok>.json`. Specy se
  necommitují (`.pflanzer/specs/` je v `.gitignore` z `init`). Heredoc
  `--spec - <<'EOF'` je jen záložní varianta — v omezených oprávněních ho
  blokuje bezpečnostní heuristika Bashe, proto nikdy nedoporučuj heredoc, vždy
  `--spec soubor.json` (Write).
- Režim stavby (`parallel` | `mob`) je uložený v projektu z Kickoffu: `worktree
  setup`, `quick_session prompts` i `/pm build` ho berou odtud, `--mode` nepiš.
- Žargon při **prvním** použití v odpovědi vysvětli jednou větou, pak už ne:
  Async (3–5 dní, po Iterate 1–2 dny, kdy zástupci sami proklikají preview a napíšou feedback) ·
  Decider (člověk s mandátem říct Go i Kill) · checkpoint (20min okno
  s podpisem) · stupeň Lean (výchozí průběh: Build 3 h, Async 3–5 dní) ·
  worktree (oddělená kopie repa) · quality gate (automatická kontrola).
- Po Kickoffu neopakuj „připraveno ke Kickoffu“ z `doctor`; zmiň jen
  otevřené výhrady, jednou větou.
- **Jeden další krok, nikdy dvě otázky najednou.** Chybí-li po Kickoffu jméno
  podepisujícího (např. u AI náhrady bezpečnosti) nebo nejsou zabookovaná
  okna, je dalším krokem právě to (konkrétní akce a člověk), ne
  `/pm build`. Chybí-li preview URL, navrhni konkrétního člověka (zástupce
  provozu z projektu) a termín, ne „domluvte s provozem“.
- Používej **skutečná jména z projektu** (`pflanzer status`), ne generické
  „PdM, vývojář, designér“.
- Nenajde-li uživatel `/pm`, zkus `/pflanzer:pm`. **„Restartuj Claude Code“
  říkej jen hned po instalaci / `init`** (dřív `/pm` neexistuje); jinak ne.
- **Každá odpověď končí jednou otázkou nebo jednou výzvou** — ne dvěma,
  ne žádnou.
- Na **volnou otázku** vždy nejdřív `pflanzer status` (pro aktivní projekt
  `--slug S`) a odpověz se **jmény z projektu**, ne obecně.

## Proč tento command existuje

Uživatel si pamatuje jen `/pm`. Router zjistí, kde projekt je (`pflanzer
status`), a řekne **jeden** další krok. Detail (DB, gates, hub) je schovaný
v toolu `pflanzer`; `pflanzer-*` commandy jsou interní implementace kroků.

## Sloveso (tabulka je záměrně krátká)

| Sloveso | Deleguje na | Kdy |
|---------|-------------|-----|
| *(žádné)* | — (`pflanzer status`) | stav + jeden další krok |
| `status` | — | totéž, výslovně |
| `doctor` | — (`pflanzer doctor`) | je repo připravené ke Kickoffu? |
| `start` | `pflanzer-charter` | **Kickoff** 15 min — zadání + jména 6 kroků |
| `build` | `pflanzer-session-1` | **Build** 3 h (Lean) — 3 varianty paralelně |
| `live` | `pflanzer` | Kickoff + Build v jednom (**Quick**, 60–90 min; malý interní tool) |
| `feedback` | `pflanzer-feedback-pull` | **Async** 3–5 dní (po Iterate 1–2 dny) — feedback zástupců |
| `decide` | `pflanzer-session-2` | **Rozhodnutí** 60–90 min — Go / Iterate / Kill |
| `ship` | `pflanzer-session-3` | **Ship** — gates jen na vítěze, checkpoint provozu, SHIP.md |
| `handoff` | `pflanzer-handoff` | balíček per role + metriky pilotu |
| `retro` | `pflanzer-retro` | **Retro** — měření outcome: % LOC vítěze v produkci, days-to-prod, T+7/30/60/90 |

Pokročilé (mimo hlavní cestu, jen regulované/větší projekty — stupeň Full):
`roles` (`pflanzer-roles`; vedle výběru rolí rozešle role cards), `triage`
(`pflanzer-triage`).

**Delegace = přečti `.claude/commands/<cíl>.md` přes Read a postupuj přesně
podle něj** (s `$ARGUMENTS` = slug). Nikdy nereimplementuj logiku cílového
commandu po svém.

## Model účasti (ADR-0021) — připomínej ho v každém kroku

- **6 kroků cesty**, každý s pojmenovaným zástupcem: byznys (Decider),
  produkt, design, vývoj, bezpečnost & právo, provoz. Krok bez jména →
  upozorni a nabídni doplnění, než pustíš `build`. Místo jména smí stát
  **AI náhrada** jen tam, kde to dovoluje ADR-0023 (design; předkontrola
  bezpečnosti & práva a provozu; produkt jen Quick / throwaway) — **nikdy**
  byznys a vývoj. Podepisuje vždy člověk.
- **Jádro 3–4 lidé** (PdM, 1–2 vývojáři, designér) celou dobu; ostatní
  na **okna**: Decider na Kickoff (15 min) + Rozhodnutí; bezpečnost & právo
  checkpoint 20 min během/po Buildu; provoz checkpoint 20 min u Ship.
- **3 pravidla:** každý krok má jméno · max 5 lidí naráz · co umí automat,
  nepotřebuje člověka v místnosti.
- **Max 5 lidí naráz.** Víc → navrhni zúžit scope nebo rozdělit.
- V hlášení dalšího kroku uváděj, **kdo má přijít** (např. „Další krok:
  `/pm decide demo-widget` — přizvi Decidera, 60–90 min").

## Jak postupuj

### 1. Parsuj `$ARGUMENTS`

- První token = sloveso (pokud odpovídá tabulce výše), zbytek = slug.
- **Argument není sloveso, ale věta nebo otázka** (např. „může Decider na
  Build?“, „co když nemáme security?“): nejdřív `pflanzer status` (pro
  aktivní projekt `--slug S`), pak odpověz **podle metody** — přečti
  příslušnou pasáž (`docs/methodology/00-lean-pflanzer.md`, FAQ
  v `docs/zacni.md`, ADR-0021 / ADR-0023), ne jen z obsahu repa. Odpověď
  max ~8 řádků, se jmény z projektu, a **jeden** další krok. Speciální
  případy viz sekce „Typické otázky“ níže.
- Neznámé sloveso → ukaž tabulku sloves a zeptej se přes AskUserQuestion.
- Sloveso bez slugu, ale `pflanzer status` hlásí víc projektů → AskUserQuestion, který projekt.

### 2. Bez argumentů (nebo `status`)

```bash
pflanzer status            # všechny projekty (vč. stupně Quick / Lean / Full)
pflanzer status --slug S   # jeden projekt
```

Výstup = fáze projektu + **jeden doporučený další krok** (`/pm …`) +
Doporučení. Ukaž ho doslova, doplň, **kdo má přijít** (okno), a zeptej se
přes AskUserQuestion, jestli krok spustit. Víc projektů → tabulka (slug /
fáze / další krok) a výběr.

**Žádný projekt:** nic se neptej na možnosti. Rovnou spusť `pflanzer doctor`
a podle výsledku doporuč **jediný** krok:

- „připraveno ke Kickoffu: ano“ → „Další krok: `/pm start` — Decider + jádro,
  15 min.“ (Pro malý interní tool v jednom sezení zmiň `/pm live` jednou
  větou, ne jako rovnocennou volbu.)
- „ne“ → vypiš, co chybí a jak to opravit (doctor to říká), a krok „oprav a
  spusť znovu `/pm`“.

Jsou-li u projektu kroky s AI náhradou (`pflanzer status` je uvádí), připomeň,
kdo je podepíše.

Neodvozuj stav sám z DB (žádné ruční `sqlite3`) — jediný zdroj pravdy je
`pflanzer status`.

Mapování stavu na další krok (pro orientaci; rozhoduje `pflanzer status`):
`draft` → `start` · `charter` → `build` (Full: nejdřív `roles` + `triage`) ·
`session_1` → `feedback`, po zápisu feedbacku `decide` · `session_2` (Iterate)
→ `decide` · `handoff` → `ship`, pak `handoff`. Existuje-li
`data/handoffs/<slug>/SHIP.md`, nabídni vedle `handoff` i `retro`
(po merge vítěze `measure`, hned `reminders`, pak T+7/30/60/90 readouty).
`killed` → jen oznám; nový projekt = `start`.

**Dva stavy, které router nesmí splést (pilot Ponk):**

- **Quick projekt (`/pm live`) s blokovaným Kickoffem** (CONSTITUTION vs. zadání,
  nezabookovaná okna, chybějící podpis): po odblokování doporuč **tentýž mód**
  — `/pm live <slug>` (pokračuje od Buildu, Kickoff se neopakuje) —, ne
  `/pm build`. Stupeň Quick poznáš v `pflanzer status --slug S` („stupeň
  Quick“); `/pm build` je pro Lean/Full. Tool u Quick po Kickoffu někdy vypíše
  `/pm build`; ber to jako synonymum a řekni uživateli `/pm live <slug>`.
- **Build už proběhl, chybí jen zápis** (v target repu worktrees s commity
  `pflanzer/<slug>-…`, preview případně běží, `pflanzer status` hlásí „Build
  běží“ / další krok `pflanzer vote`): nikdy neříkej „stavba neproběhla“ a
  nenabízej restart Buildu. Nabídni **zápis hlasování** — šablona je v
  `.pflanzer/specs/<slug>-vote.json` (vytvořil ji `worktree setup`) — a jako
  další krok `pflanzer vote --spec .pflanzer/specs/<slug>-vote.json`.

### 2a. Typické otázky (volný text v `/pm`)

**„Security nám nepodepíše, co teď?“**
1. Vyžádej si jejich **písemný důvod** a rozlišuj: *chybí podklady*
   (data, síť, strop nákladů — doplníme) vs. *reálné riziko* (osobní data,
   produkční přístup — upravíme rozsah nebo zastavíme).
2. Pošli jim **3věté shrnutí**: co aplikace čte, kam píše, jestli vidí
   reálná data. Nabídni **AI pre-check** (`security-expert`) jako podklad,
   ne jako podpis.
3. Bez odpovědi do **48 h** eskaluj na Decidera: rozhodne a zapíše to —
   buď převezme riziko (`pflanzer session_3 --slug S --override-triage
   --rationale "…"`, v decision logu je jeho jméno; jen pilot bez osobních
   dat), nebo projekt zastaví.

**Podpis bezpečnosti, když security není** — pořadí (nikdy nezačínej
autorem kódu): (a) někdo z firmy s mandátem — DPO, IT security, compliance,
stačí 20 min; (b) Decider vědomě převezme riziko (`--override-triage`),
u pilotu bez osobních dat; (c) autor kódu jen jako poslední možnost,
u interního nástroje bez osobních dat — nástroj to označí varováním a právo
tím pokryté není.

**„Decider chce být na Buildu.“** Ne (anti-HiPPO, ADR-0021: jeho přítomnost
táhne hlasování k jeho názoru). Nabídni místo toho: **10min screencast**
z Buildu (nahraje <jméno PdM>) a pozvánku na **Rozhodnutí s živým demem**
(<jméno Decidera>, 60–90 min). Jména vezmi z `pflanzer status`.

**„Můžeme Build dělat online?“** — Ano: vývojář sdílí **jednu obrazovku** (jeho Claude Code + běžící varianty), jádro naviguje hlasem; max 5 lidí; checkpoint bezpečnosti online 20 min. **Ne** 3 paralelní breakout místnosti — rozhoduje se nad stejnou obrazovkou. Hlasování tiše najednou přes chat nebo formulář. Jména (kdo sdílí, kdo
naviguje, kdo podepisuje bezpečnost) vezmi z `pflanzer status`. Detail:
`docs/methodology/04-session-1.md` § Build online.

**Po Kill** — poděkuj týmu nahlas (zastavit včas je výsledek metody, ne
selhání) a veď k 1–3 poučením:
`pflanzer retro lesson --slug S --text "<co jsme se naučili>"`. Poučení
napiš s týmem jednou větou každé; další krok je právě tento příkaz.

### 2b. `doctor`

```bash
pflanzer doctor            # v aktuálním repu; volitelně --target DIR, --json
```

Ukaž checklist a „připraveno ke Kickoffu: ano/ne" a Doporučení z výstupu.
Při „ne" vypiš, co chybí a jak to opravit (viz `docs/zacni.md` § Je repo
připravené?; INTEGRATION_GUIDE vývojář nechá vyplnit v Claude Code a
zkontroluje, 5 min). Další krok: při „ano“ `/pm start`, jinak oprava a znovu
`/pm doctor`. Commit všeho najednou, když chybí push:
`git add -A docs .pflanzer tests .gitignore .claude/settings.json && git commit -m "chore(pflanzer): init" && git push -u origin HEAD`.

### 3. Deleguj

Přečti cílový command file a proveď ho. Po dokončení ukaž **jeden** další
krok ve tvaru `/pm <sloveso> <slug>` (nikdy ne `/pflanzer-*`) a kdo má
přijít — např. „Další krok: `/pm build demo-widget` — jádro, 3 h".

## Co NEDĚLAT

- Nepřeskakuj prerekvizity cílových commandů (statusy, triage gate) —
  router zjednodušuje UX, ne metodu.
- Nevynalézej vlastní wizardy — vše dělají cílové commandy.
- Nezapomeň brand line `Pflanzer Method | pflanzer.cz/method` na začátku
  každého výstupu.

## Reference

- `.claude/commands/pflanzer*.md` — implementace kroků (interní)
- `docs/methodology/00-lean-pflanzer.md` — default profil průběhu
- `docs/decisions/0021-mala-skupina-cela-cesta.md` — model účasti
- `docs/decisions/0022-inspirace-z-trhu.md` — constitution, doctor, kontroly, měření
- `docs/decisions/0017-mezi-session-okno-per-stupen.md` — stupně Quick / Lean / Full
- `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody — autoritativní tabulka stupňů (default **Lean**)
- `README.md` § Quick start
