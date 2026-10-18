---
description: Kickoff + Build v jednom (/pm live) — malé jádro se zástupci všech kroků cesty postaví 3 varianty a odejde se shortlistem a jmény pro okna.
---

# /pflanzer — In-room session (single entry point)

**Argumenty (volitelné)**: `$ARGUMENTS` = problem statement (1 věta).
Pokud chybí, zeptáš se v kroku 1.

## Pro koho

**Malá skupina (ADR-0021):** jádro 3–4 lidí (PM, 1–2 vývojáři, designér)
u jedné obrazovky připojené k TV; Decider přijde na Kickoff (prvních
15 min) a na závěrečný shortlist; bezpečnost & právo na 20min checkpoint.
**Nikdy víc než 5 lidí naráz.**
Cíl: za ~3 h mít **3 běžící varianty, shortlist a jména zástupců všech
6 kroků cesty se zabookovanými okny**, bez 4 separátních wizardů.

Pod kapotou tento command volá Charter + Roles + Triage (deferred) +
Builder Decision + Session 1 persistenci. Sofistikovanost zachována,
UX zjednodušeno.

## Workflow (5 kroků = 5 AskUserQuestion bloků + 1 generativní)

### KROK 1 — HOOK (co dnes řešíte)

Pokud `$ARGUMENTS` chybí, zeptej se přes `AskUserQuestion`:

> **Co konkrétně chcete dnes vyřešit?** (1-2 věty, akční formulace)

Zachovej odpověď jako `hook` (ne validovat moc — krátké je fajn).

### KROK 2 — DECIDER + ROOM (kdo má hlas)

Zeptej se 2 otázkami v jedné AskUserQuestion zprávě (paralelně):

**A) Kdo má dnes finální slovo (Decider)?** [text input]
- Default: nejstarší v místnosti / line manager / sponsor.

**B) Zástupci 6 kroků cesty** [text per krok: jméno + role z catalogu + `jádro` / `okno`]

| Krok cesty | Default role (catalog #) | Default účast |
|------------|--------------------------|---------------|
| Byznys | Zadavatel / Decider (#1) | okno (Kickoff + Rozhodnutí) |
| Produkt | PM (#2), často i facilitátor (#3) | jádro |
| Design | UX / Designer (#6) | jádro |
| Vývoj | FE (#4) a/nebo BE (#5) | jádro |
| Bezpečnost & právo | Security (#7) nebo Legal / DPO (#10) | okno (checkpoint 20 min) |
| Provoz | DevOps (#15) nebo EM (#9) | okno (checkpoint u Ship) |

Pravidla (vynucuj):
- **Krok bez jména → STOP.** Zeptej se, kdo ho zastoupí; jeden člověk
  smí krýt víc kroků (např. vývojář = vývoj + provoz).
- **Jádro > 4 nebo kdokoli naráz > 5** → navrhni přesunout někoho na okno
  nebo zúžit scope.
- Další role z catalogu (QA #8, A11y #11, Data #12, CS #13, User research
  #14, UX writer #16, …) přidej jen jako zástupce existujícího kroku nebo
  jako AI expert perspektivu — ne jako další osobu u stolu.

`room_role_idx` = role catalog čísla všech zástupců (jádro i okna);
`role_owners` = jména. Do handoff MD zapiš ke každému `jádro` / `okno`
+ datum/čas okna.

### KROK 2.5 — MODE SELECT (paralelní vs mob, per ADR-0011)

Před risk profile zeptej se týmu na working mode. Auto-recommend signál
získáš z `recommend_mode()` v `tool/cli/quick_session.py` (volá se po
KROK 2 kdy už víme room_size).

```
AskUserQuestion: "Jak budete dnes pracovat?"
description: "Auto-recommend: <{recommended_mode}>. Důvod: {rationale}"
options:
  - "Jedna obrazovka, AI staví A/B/C paralelně (3 worktrees)" — default
    pro jádro 3–4 (session_mode = 'parallel'); vývojář řídí 3 CC sessions,
    ostatní navigují
  - "Mob (1 obrazovka, 1 varianta, sequential iterations)" — opt-in pro
    nový tým / onboarding / single high-stakes decision
  - "Hybrid (mob → split → review)" — disabled, v3 coming
```

**Hard-block guards** (force re-confirm s warning pokud user vybere mob):
- `production_readiness_target ≥ 70` → "Production target — paralelní dá Decideri 3 fallback options. Mob = sunk-cost commitment. Pokračovat s mobem? rationale POVINNÝ."
- `room_size > 5` → "Tým má > 5 lidí. Mob breaks at 6+ (cognitive load + air-time inequity). Doporučuji paralelní nebo split team."
- veto role povinná (Security/Legal) → "Veto role v týmu. Mob = jediný artefakt = veto = kill all. Paralelní lépe."

Result se persistuje jako `projects.session_mode = 'parallel' | 'mob'`
(volitelný field, default 'parallel').

### KROK 3 — RISK PROFILE + PRODUCTION TARGET (rozsah dopadu)

```
AskUserQuestion: "Co je dnešní cíl tohoto prototypu?"
options:
  - "Throwaway proto" — interní demo, žádná produkce, žádná real data
  - "Pilot s 5-20 reálnými uživateli" — limited AI Act, L2 data
  - "Production launch" — limited AI Act, L3 data, regulated profile, kód → repo
```

→ mapuje se na `RISK_PROFILES` v `tool/cli/quick_session.py`.

**Pokud Pilot nebo Production**: zeptej se navíc (3 otázky v jednom AskUserQuestion):

```
AskUserQuestion (3 otázky):
1. "Target git repo URL?" [text → https://github.com/<org>/<repo>]
   → projects.target_repo_url (POVINNÝ pro pilot/production — bez něj
     bootstrap raise ValueError per ADR-0009)
2. "Branch owner / kdo merguje PR?" [text → GitHub handle, např. @petra]
   → projects.target_branch_owner (auto-fills `gh pr create --reviewer`
     v SHIP.md per ADR-0010)
3. "Shadow PM (kdo babysittuje code mezi-session)?" [text → jméno]
   → projects.shadow_pm (per perspektiva 02 vibe-product C5 — bez named
     ownera mezi-session work dies)
```

Pokud risk_profile = throwaway, tyto 3 otázky se přeskočí.

**Acceptance criteria** (per ADR-0010 = nejvyšší leverage gate):
```
AskUserQuestion: "Acceptance kritéria pro winning variantu (3-5 Gherkin scénářů)?"
  - Decider napíše 1 happy + 2 negative + 1 edge case
  - Persistne do projects.acceptance_criteria_md
  - Per worktree zapíše tests/acceptance/<slug>.feature (AI implementuje aby projela)
```

**Bootstrap call** (po krocích 1-3):

Vyrob JSON spec do `/tmp/quick-bootstrap-<slug>.json`:

```json
{
  "hook": "<z kroku 1>",
  "decider_name": "<z kroku 2A>",
  "room_role_idx": [1, 2, 3, 4, 6],
  "risk_profile": "throwaway|pilot|production",
  "role_owners": {"1": "Honza", "2": "Petra", ...}
}
```

Spusť:

```bash
python3 tool/cli/quick_session.py bootstrap --spec /tmp/quick-bootstrap-<slug>.json
```

→ vrátí `slug`, `project_id`, `defer_note`. Slug ukaž týmu (link
do web hubu: `http://localhost:8000/<slug>`).

### KROK 4 — BUILDER PROMPTS (paralelní vibe-coding)

**Default = 3× Claude Code v 3 git worktrees** (žádný browser tab, žádný extract).

```bash
python3 tool/cli/quick_session.py prompts --slug <slug> --hook "<hook>" --n 3
```

→ JSON s 3 prompts, všechny pro `claude-code`, **každý s jiným angle**:
- A — happy-path minimum (1 obrazovka, 1 CTA)
- B — guided multi-step (progress bar, validace per krok)
- C — smart defaults (AI hádá inputy z kontextu)

**Setup (facilitátor, 1× per session, ~1-3 minuty):**

```bash
# 1. Pflanzer naclonuje target repo do ~/.pflanzer/targets/<repo-slug>/
#    a vyrobí 3 worktree A/B/C jako siblings + spustí pnpm/yarn/npm install
python tool/cli/worktree.py setup --slug <your-slug>
```

> ⚠ **KRITICKÉ (ADR-0009 P0 fix)**: Tento command spawne worktree v
> **target zákazníkově repu**, ne v PflanzerMethod meta-repu. Jinak by
> CC kódoval do tohoto toolu a reuse by byl 0 %.
>
> Vyžaduje `projects.target_repo_url` (settnut v Charteru pro pilot/production).

**Vývojář(i) v jádru řídí worktrees (1 vývojář = všechny 3, 2 vývojáři = 2+1); ostatní v jádru navigují u TV. Per worktree:**
```bash
cd ~/.pflanzer/targets/<your-slug>-X     # X = A / B / C
claude                                    # otevře CC session v target worktree
# 1. Read INTEGRATION_GUIDE.md + tests/acceptance/<slug>.feature (POVINNÉ)
# 2. Vlož prompt z `quick_session.py prompts` output
# 3. Kóduje 30 min, drží se conventions target repa
# 4. Pre-commit hook spustí lint+types+tests
# 5. Commit jako `feat(<slug>): variant X — <shrnutí>`
```

> **Hosted SaaS opt-in** (jen pokud nemáš CC license / chceš UX showcase
> pro non-tech sponsora / greenfield bez repa):
>
> ```bash
> python3 tool/cli/quick_session.py prompts --slug <slug> --hook "<hook>" --n 3 --prefer-hosted
> ```
>
> → mix `claude-code + codex-cli + v0` s instrukcemi pro Push to GitHub.

Facilitátor (ty) hlídá čas — **30 min cap**, pak voting bez ohledu na hotovost.

**Žádná AskUserQuestion za URL** — pro CC mode je branch deterministický
(`feat/<slug>-A`). Voting v kroku 5 dostává branch path.

### KROK 5 — VOTING (silent dot voting)

Pro každého **přítomného** zástupce (jádro + Decider, pokud je v okně) projdi tento mini-loop. Zástupce v oknech, kteří nejsou přítomni, hlasují async přes web hub (`/pm feedback`):

```
For role v selected_roles:
  pro každou variantu (A, B, C):
    AskUserQuestion: "{role_label} ({owner}) — Variant {X}"
    options:
      - "Líbí se mi" (user_value=0.8, strategic_fit=0.7)
      - "Spíš ne" (user_value=0.4, strategic_fit=0.5)
      - "Veto / blocker" (risk=0.9, rationale povinný)
      - "Pass" (skip)
    + zeptej se 1× na rationale (povinný 1 věta).
    + zeptej se 1× na commitment level 0-3 PER PERSONA (ne per varianta).
```

> ⚠ **Speed mode**: pokud je přítomno > 4, použij Liberating Structures **1-2-4-All**:
> 1 min sami, 2 min ve dvojici, 4 min v čtveřici, pak All. Hlasy SILENT,
> Decider hlasuje **poslední** (per `04-session-1.md` § HiPPO push).

Sestav `votes` array per variant:

```json
[
  {
    "name": "A", "builder": "v0", "description": "happy-path minimum",
    "role_preferences": [
      {"role_idx": 1, "user_value": 0.8, "effort": 0.3, "risk": 0.2,
       "strategic_fit": 0.85, "commitment_level": 3,
       "rationale": "matches XYZ", "is_ai_only": false},
      ...
    ]
  }
]
```

### KROK 6 — DECIDER'S CALL (sociální akt)

Decider přichází na **okno posledních ~15 min** (nebyl u stavby — anti-HiPPO).
Pokud nemůže, jádro připraví shortlist návrh a Decider ho potvrdí async
do 24 h; do decision logu zapiš, že call byl async.

```
AskUserQuestion: "{Decider} — která varianta jde do mezi-session prototype hubu?"
options: ["A", "B", "C", "A+B", "A+C", "B+C", "A+B+C", "Žádná → re-frame problému"]
```

```
AskUserQuestion: "Decider rationale (1-2 věty, do decision logu):" [text]
```

Pokud někdo dal "Veto / blocker" v kroku 5 → uveď do `veto_register` array
+ spec`AskUserQuestion: "Decider — override veto?"` (pokud ano, rationale
povinný do decision logu).

Vyrob spec a persistuj:

```json
{
  "slug": "<slug>",
  "facilitator": "<your name z kroku 2A or 2B owners>",
  "decider_call": {
    "shortlist": ["A", "B"],
    "rationale": "<z předchozího>",
    "veto_register": [...],
    "parking_lot": []
  },
  "votes": [...]
}
```

```bash
python3 tool/cli/quick_session.py vote --spec /tmp/quick-vote-<slug>.json
```

### KROK 7 — HANDOFF (1-page MD)

```bash
python3 tool/cli/quick_session.py handoff --slug <slug>
```

→ zapíše `data/quick/<slug>-handoff.md`. **Vyhoď týmu na TV** v plném textu
(je 1 stránka, vejde se).

Klíčové sekce:
- Co děláme (XYZ)
- Decider + decision rationale
- Varianty + scores
- **Zástupci 6 kroků cesty**: jméno / role / jádro vs okno / datum okna
- **Kdo / Owner / Commitment 0-3 / Rationale** (table)
- Kill criteria
- ⚠ Pre-production TODO (triage deferred — re-run před pilotem)
- Co dál (5 akčních bodů)

### KROK 8 — Production path hint (pokud risk_profile != throwaway)

Pokud tým chce **kód reálně použít**:

```
> 🚀 Production path:
> 0. Checkpoint bezpečnost & právo (20 min, do 48 h) — zástupce z kroku 2B
>    projde datový tok + data classification nad winner kandidátem
> 1. Async feedback (3–5 dní) přes web hub: /pm feedback <slug>
> 2. Rozhodnutí (60–90 min, Decider + jádro): /pm decide <slug>
> 3. Ship: /pm ship <slug>  + checkpoint provozu (20 min)
>    → 7 quality gates → score 0-100; pokud >= 80, kód je ready k mergi
> 4. Handoff: /pm handoff <slug>
>    → package s odkazy na soubory + open-PR commands
```

Tento blok **vyhoď do handoff MD** — tým má roadmap k production.

## Co tento command NEDĚLÁ

- **Negeneruje moc otázek** — 5-6 AskUserQuestion bloků MAX. Pokud potřebuješ
  všechny pole z plného Charter wizardu, použij `/pflanzer-charter`.
- **Nespouští reálnou triage** — všechny 4 tracky deferred (in-room mode
  nemá 48h pre-read). Pre-pilot/production MUSÍ tým pustit `/pflanzer-triage`.
- **Nespouští 17 expert sub-agentů** — voting je manuální od lidí v místnosti
  (commitment je sociální akt). AI běží jen na builder prompts + agregaci.
- **Nepushuje varianty do web hubu** — to je krok 7 (handoff). Web hub je
  pro async mezi-session feedback (Slice 6).

## Anti-patterns (block immediately)

- **HiPPO override silent vote bez rationale** → block. Decider override
  vyžaduje veřejný rationale do decision logu.
- **Žádná negative variant** (A+B+C all positive) → flagni "groupthink risk",
  navrhni Pre-mortem TRIZ ("za 6 měsíců to selhalo, proč?").
- **Decider zvolí > 3 varianty** → Decider's tax (synthesis 02). Force
  re-pick s max 3.
- **Žádné L3+ data v promptech** — pokud Charter má `data_class=L3`, prompt
  generator už zahrnul varování; opakuj ho ústně před vibe-codingem.

## Reference

- `tool/cli/quick_session.py` (single-entry orchestrator)
- `docs/decisions/0021-mala-skupina-cela-cesta.md` (model účasti: jádro + okna)
- `docs/methodology/00-lean-pflanzer.md` (kanonický průběh)
- `docs/methodology/04-session-1.md` (rozšířená reference Buildu)
- `docs/decisions/0008-tool-form-factor.md` § Hybrid (CC + web hub)
- Plný flow: `/pm start` → `/pm roles` → `/pm triage` → `/pm build` → async → `/pm decide` → `/pm ship`
- Quick flow: `/pm live` → async → `/pm decide` → `/pm ship`.
