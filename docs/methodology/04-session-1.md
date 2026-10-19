# 04 — Build

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: jak se vede Build (`/pm build`) — facilitace,
> úhly A/B/C, průběžné kontroly, checkpoint bezpečnost & právo, diff
> walkthrough a hlasování. Délky podle stupně jsou jen v kanonické tabulce
> [`00-lean-pflanzer.md`](00-lean-pflanzer.md) § Tři stupně; tady je
> Lean (default) a na konci odchylky Quick a Full. Příkazy a pořadí kroků:
> `.claude/commands/pflanzer-session-1.md`.

## Cíl

Za jedno sezení jádra vzniknou **3 běžící varianty** téhož zadání
(ve 3 worktrees target repa, ADR-0009), každá s kontrolami lint/typy/
testy/build, na preview URL se štítkem „Varianta X — k rozhodnutí, ne
produkt". Hlasuje se až po diff walkthrough. Build nerozhoduje; shortlist
a zápis jdou do Async a Rozhodnutí.

## Kdo

- **Jádro 3–4 lidé celou dobu:** PdM (často i facilitátor), 1–2 vývojáři
  jako buildeři, designér. **Max 5 lidí naráz.**
- **Decider u Buildu není** (anti-HiPPO: nemůže tlačit variantu během
  vzniku). Vidí je v Async a na demu v Rozhodnutí.
- **Bezpečnost & právo** přijde na checkpoint 20 min.
- **Hard rule: u klávesnice sedí vývojář.** Facilitátor nemá otevřené IDE
  a nepromptuje za dev tým (failure mode „captured by tool"). Není-li
  v jádru vývojář, Build nezačínej — Track P není možný (ADR-0020).
- Perspektivy nepřítomných rolí dodají **AI expert sub-agenti** jako vstup
  (ne hlas), ve vlnách po 3–4, nikdy všichni naráz.

## Průběh (Lean, 3 h, orientační)

| Čas | Blok | Poznámka |
|-----|------|----------|
| 0:00–0:15 | Start | zadání z Kickoffu nahlas, JTBD/metrika, rozdělení variant, kontrola `doctor` a worktrees (`pflanzer worktree setup`) |
| 0:15–2:30 | **Stavba** 3× Claude Code paralelně | vývojář řídí všechny tři (nebo 2+1), zbytek jádra u jedné obrazovky směruje; kontroly průběžně; tvrdý strop 2 h 30 min na stavbu |
| posledních 30 min | **Checkpoint bezpečnost & právo** 20 min | nad běžícími variantami a diffem; nebo nejpozději do 48 h |
| 2:30–2:45 | **Diff walkthrough** | 3 × ~5 min; bez něj se nehlasuje |
| 2:45–3:00 | Silent vote, zápis, push, preview | odkazy všem zástupcům |

### Úhly variant A/B/C

Prompty (`pflanzer quick_session prompts`) dávají každé variantě jiný úhel,
aby se nesoutěžilo o drobnosti:

- **A — minimum:** nejmenší změna, která řeší problém.
- **B — vedený multi-step:** průvodce/wizard, víc kroků, víc vedení.
- **C — chytré defaulty:** předvyplnění, automatika, nejméně zásahů uživatele.

Každý prompt čte `.pflanzer/CONSTITUTION.md` a `docs/INTEGRATION_GUIDE.md`
a ukládá AI **pouštět lint/typy/testy/build průběžně**.

### Kontroly průběžně

Po každé větší změně lint + typy + testy + build (+ secret scan, má-li ho
repo). **Červená varianta se neposouvá dál, dokud není zelená.** Zelené
kontroly jsou podmínka preview, ne ozdoba. Pro vícerepové zadání (FE + BE)
nese BE repo prompt „contract-first" (nejdřív OpenAPI diff, pak
implementace). Data leakage guard (`pflanzer worktree guard`) hlásí secrets,
trackované `.env*` a prod dumpy; `FAIL` = stop před klávesnicí.

### AI vs člověk

| AI vede (execution-heavy) | Člověk vede (context-heavy, odpovědnost) |
|---------------------------|-------------------------------------------|
| generování variant, OpenAPI shadow, axe-core, SBOM/secret scan, clustering feedbacku, agregace skóre, první draft pre-mortem rizik | rámování problému (PdM + UX), konflikty mezi rolemi, **diff walkthrough**, interpretace hlasování, veto, rozhodnutí a jeho podpis, správa energie |

Pravidlo: AI vede, když je úkol rychlý a bez kontextu; člověk, když nese
odpovědnost. Decision log píše AI, podepisuje člověk.

## Checkpoint bezpečnost & právo (20 min)

Zástupce kroku (jeden člověk, Security nebo Legal/DPO) projde nad
běžícími variantami a diffem:

- [ ] **Datový tok** — odkud kam data tečou, co opouští firmu
- [ ] **Data classification** — L1–L4; žádná produkční data v preview
- [ ] **Egress limit** — co smí agent a preview volat ven (default: nic
  mimo allowlist)
- [ ] **Strop tokenů / nákladů** — limit na sezení a na den, kdo ho hlídá
- [ ] **Riziko prompt injection** — agent čte cizí text (issues, weby,
  vstup uživatele)? Co když v něm bude instrukce?
- [ ] **Worktree není bezpečnostní izolace** — sdílí soubory, secrets i
  síť stroje; secrets mimo worktree, agent s minimem práv
- [ ] **Právo** — osobní údaje, licence závislostí, tvrzení v UI

Podpis (bez podpisu Ship pilotu/production neprojde):
`pflanzer checkpoint --slug <slug> bezpecnost --by "<jméno>" --note "…"`;
veto přidá `--blocked`. **Veto je veto, ne hlas:** varianta nejde na preview,
dokud ji Decider výslovně nepřebije s odůvodněním do decision logu. Kdo dá
critical bez důkazu (STRIDE, a11y, právní tvrzení), je facilitátorem
downgradován na varování. `doctor` a gates kontrolu doplňují, nenahrazují.

## Diff walkthrough (před hlasováním)

Bez výkladu kódu hlasují zástupci o UI, ne o kódu. U každé varianty
vývojářský pár ukáže `git diff --stat <base>...HEAD` a
`git log --oneline <base>..HEAD` a řekne tři věty: **reuse** (co existující
použil nebo upravil), **nové** (co přibylo), **mock** (co je stub a v produkci
by chybělo); volitelně kolik scénářů z `tests/acceptance/<slug>.feature`
projelo. Výsledek jde do `diff_summary` zápisu. Dimenze effort a risk se
skórují až po walkthrough.

## Silent voting a zápis

- Hlasy jsou **tiché**, výsledek se zveřejní až po hlasování (1-2-4-All).
  Hlasují přítomní; nepřítomní přes Async. **Decider hlasuje vždy poslední,
  a to až v Rozhodnutí.**
- Dimenze: hodnota pro uživatele, effort, risk, strategická vazba; u každého
  hlasu rationale (1 věta) a commitment 0–3 pro Async.
- Zápis: `pflanzer quick_session vote --spec …` (nebo plný `pflanzer
  session --spec …`): varianty (branch, preview URL), preference, výsledek
  checkpointu, veto registr, parking lot.
- Push a preview: větve `pflanzer/<slug>-A|B|C` do target repa, preview URL
  z CI (nebo draft PR / Playwright záznam — [`postup.md`](../postup.md)
  § Kde varianty fyzicky jsou). Žádná placeholder URL.

## Konfliktní situace — playbook

Konflikt pojmenuj v 5. minutě výskytu, ne na konci.

- **Veto bezpečnosti vs tlak zadavatele:** critical = pivot na jinou
  variantu, ne pokračování v zablokované. Reálná PII v promptu = okamžité
  přerušení, incident playbook, 72h GDPR hodiny. Detail
  [`08`](08-edge-cases-a-rizika.md) § 2.
- **HiPPO:** silent voting, Decider poslední; override výsledku jen veřejně
  s rationale v decision logu.
- **Scope creep („když už tu jsme…"):** facilitátor nebo PdM řekne „parking
  lot" a vrátí se k JTBD; nová věc = kandidát na další zadání.
- **Kapacita (EM) vs termín:** T-shirt odhad, ne story pointy; větší než L
  = 2denní spike mimo sezení; přetrvávající spor se eskaluje mimo
  místnost.
- **FE rychlost vs BE kontrakt:** contract-first, OpenAPI diff paralelně,
  breaking-change registr s vlastníkem.
- **Pivot gate v polovině:** pokud víc než polovina přítomných říká, že
  řešíme špatný problém, zastav stavbu a vrať se ke Kickoffu — lepší než
  3 varianty ke špatnému zadání.

## Výstupy Buildu

- 3 větve a preview URL se štítkem; stav kontrol per varianta.
- `diff_summary`, preference s rationale, veto registr, parking lot.
- Podepsaný checkpoint bezpečnost & právo.
- Další krok: `/pm feedback <slug>` ([`05`](05-mezi-sessions.md)).

## Failure modes

- **Captured by tool** (půlka času debugováním builderu) → AI v sub-roli,
  záložní builder předem.
- **Captured by HiPPO** → silent voting, Decider mimo Build.
- **Energy blindness** → pauza každých 90 min, pulz 1–5 prstů; konec dřív
  než v 16:00.
- **AI as authority** → každý AI insight má lidský override; decision log
  atribuuje člověka.
- **Voting o UI, ne o kódu** → diff walkthrough povinný.
- **Charter creep** → nové vstupy mimo zadání na 1 stránku se odmítají.

## Odchylky podle stupně

- **Quick** (`/pm live`): Kickoff + Build v jednom, 1 kolo stavby × ~30 min
  → silent vote → shortlist. Checkpoint bezpečnost & právo se odkládá,
  před pilotem se doběhne (`/pm triage`). Jen risk profil
  `throwaway`/`pilot`; Decider je jen na prvních 15 min.
- **Full** (regulované, governance): kompletní agenda 5–6 h (viz níže),
  4 triage tracky předem ([`03`](03-pre-session-priprava.md)), víc
  zástupců včetně senior delegátů vetovacích rolí a AI Act tier.

### Full — rozšířená agenda (5–6 h, konec do 16:00)

| Čas | Blok | Poznámka |
|-----|------|----------|
| 09:00–09:30 | **Voice of Customer** | 5 doslovných citací z ticketů, jedna nahrávka, historka „nejhorší týden support" (CS proxy) |
| 09:30–10:00 | Zadání + JTBD warm-up | re-read zadání, JTBD lock, OST review |
| 10:00–10:15 | Pre-mortem (TRIZ) | „za 6 měsíců funkce selhala — proč?" (facilitátor + AI) |
| 10:15–10:45 | Crazy 8s / silent ideation | individuálně, bez diskuse |
| 11:00–12:15 | **Stavba 3 variant** | AI vede, lidé směrují; shadow agenti paralelně (OpenAPI, token compliance, axe) |
| 12:15–12:30 | **Diff walkthrough** | povinný před hlasováním |
| 13:00–13:30 | A11y quickscan + feasibility | 8–10 položek WCAG 2.2 AA, breaking-change check |
| 13:30–15:00 | Silent vote, score závaznosti, shortlist | viz níže |
| 15:00–16:00 | Wrap-up, commitment 0–3, buffer | konec nejpozději v 16:00 |

#### Score závaznosti

Každá role skóruje variantu 1–5 (Likert) s **povinným rationale**; skóre
se zveřejní až po hlasování. **AI-only feedback má váhu max 0,5** z 1,0.
Hierarchie: **critical = blocker** (STRIDE Critical, AI Act High-risk bez
DPIA, WCAG Critical/Serious na veřejném rozhraní, breaking change bez
konzumentů) · **varování bez veta** (UX dluh, testovatelnost, zátěž
podpory) · **skóre** = váha pro zbytek. Chronicky nízké skóre bez důkazu
facilitátor ukáže jako samostatný bod Rozhodnutí.
