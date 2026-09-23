---
description: Live in-room session pro tým — společný vibe-coding od problému k handoff za 60-90 min, bez koleček iterací mezi sessions.
---

# /pflanzer — In-room session (single entry point)

**Argumenty (volitelné)**: `$ARGUMENTS` = problem statement (1 věta).
Pokud chybí, zeptáš se v kroku 1.

## Pro koho

Tým 4-6 lidí v zasedačce, jeden notebook připojený k velkému TV.
Cíl: do 60-90 min mít **shortlist + akční handoff** (kdo / co / do kdy),
bez čekání na pre-sessions a 4 separátních wizardů.
Toto je **Quick stupeň** (viz `00-lean-pflanzer.md` § Tři stupně).

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

**B) Kdo z těchto rolí je v místnosti?** [multiSelect, default: PM, FE, UX]
- Zadavatel / Business owner (#1) — vždy zahrnuto
- PM (#2) — vždy zahrnuto
- Facilitátor (#3) — vždy zahrnuto (může to být ty / Claude)
- Frontend (#4) ✅ default
- Backend (#5)
- UX / Designer (#6) ✅ default
- Security (#7) — pokud osobní data / auth
- QA (#8) — pokud "produkce / pilot"
- Engineering manager (#9)
- Legal / GDPR (#10)
- Accessibility (#11)
- Data / Analytics (#12)
- Customer support (#13)
- User research (#14)
- DevOps (#15)
- UX writer (#16)

Volitelně (jen pokud je tým > 6 lidí, jinak skipni): **Kdo zastává jakou roli?**
(text per role, jméno).

### KROK 2.5 — MODE SELECT (paralelní vs mob, per ADR-0011)

Před risk profile zeptej se týmu na working mode. Auto-recommend signál
získáš z `recommend_mode()` v `tool/cli/quick_session.py` (volá se po
KROK 2 kdy už víme room_size).

```
AskUserQuestion: "Jak budete dnes pracovat?"
description: "Auto-recommend: <{recommended_mode}>. Důvod: {rationale}"
options:
  - "Paralelně (3 dvojice, 3 worktrees, A/B/C angles)" — default majority cases
  - "Mob (1 obrazovka, sequential iterations, ≤ 5 lidí)" — opt-in pro
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
1. "Target repo(s): FE / BE / monorepo workspace?" [text]
   Formát: `role=url[#branch][:workspace]`, víc repozitářů odděl čárkou.
   - jednoduchý případ (jako dřív) = jedna URL: `https://github.com/<org>/<repo>`
   - FE + BE: `fe=https://github.com/org/web, be=https://github.com/org/api#develop`
   - monorepo workspace: `app=https://github.com/org/mono#main:apps/web`
   → jedna URL = `target_repo_url` ve spec JSON; jinak celý text jako
     `target_repos` (bootstrap ho naparsuje a validuje; primární FE/app repo
     jde i do projects.target_repo_url). POVINNÉ pro pilot/production — bez
     něj bootstrap raise ValueError per ADR-0009.
   → BE repo (role `be`/`api`) dostane v promptech angle „contract-first:
     nejdřív OpenAPI diff, pak implementace"; `workspace` = hint „pracuj v
     `apps/web`" v promptu i v INTEGRATION_GUIDE.
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
  "role_owners": {"1": "Honza", "2": "Petra", ...},
  "target_repo_url": "https://github.com/<org>/<repo>",
  "target_branch_owner": "@petra",
  "shadow_pm": "<jméno>"
}
```

Více repozitářů / monorepo: místo `target_repo_url` dej `"target_repos"` —
buď text z otázky 1 (`"fe=https://…/web, be=https://…/api#develop"`), nebo
pole `[{"role": "fe", "url": "…", "branch": "main", "workspace": "apps/web"},
{"role": "be", "url": "…"}]`.

Spusť:

```bash
python3 tool/cli/quick_session.py bootstrap --spec /tmp/quick-bootstrap-<slug>.json
```

→ vrátí `slug`, `project_id`, `defer_note`. Slug ukaž týmu (link
do web hubu: `http://localhost:8000/<slug>`).

### KROK 4 — BUILDER PROMPTS (paralelní vibe-coding)

> ⛔ **HARD RULE: U klávesnice sedí dev (#4/#5). Facilitátor nekóduje.**
> Pokud v místnosti není žádný dev, zastav a řekni týmu, že Track P nelze —
> nabídni odložení (per ADR-0020 decision tree, Q1 = NE). Facilitátor ani
> Claude jako „AI proxy" za dev tým není náhradní builder
> (per `04-session-1.md` § Hard rule: Builder = dev pár).

**Dev check (před generováním prompts):** pokud v KROK 2B není vybraný
Frontend (#4) ani Backend (#5):

```
AskUserQuestion: "⚠ V místnosti není žádný dev (#4/#5). Track P vyžaduje
dev v driver-seat (ADR-0020). Co dál?"
options:
  - "Dev dorazí / přidat" — doplň #4 a/nebo #5 do room_role_idx
    (+ jméno do role_owners), pak pokračuj KROK 4
  - "Pokračovat jako throwaway demo (ne Track P)" — risk_profile přepni
    na throwaway, v handoffu explicitně „NE Track P, kód nejde do prod";
    pro pilot/production navrhni odložení session
```

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
# Pro každý target repo (FE / BE / monorepo): cached clone v
# ~/.pflanzer/targets/<repo-slug>/ + worktrees A/B/C (branch pflanzer/<slug>-X
# ve všech repech) + git config & prepare-commit-msg hook (trailery
# Pflanzer-Variant / Pflanzer-Session / AI-Assisted) + data leakage guard
# + CLAUDE.md „Pflanzer session rules" + pnpm/yarn/npm install (non-JS skip)
python tool/cli/worktree.py setup --slug <your-slug>          # --mode mob, --no-install, --strict
```

Výstup ukaž týmu na TV — tabulka **repo × varianta × path**, např.:

```
| Repo          | Varianta | Branch            | Path                              | Workspace | Install | CLAUDE.md |
|---------------|----------|-------------------|-----------------------------------|-----------|---------|-----------|
| fe (primary)  | A        | pflanzer/<slug>-A | ~/.pflanzer/targets/<slug>-A      | apps/web  | ok      | created   |
| be            | A        | pflanzer/<slug>-A | ~/.pflanzer/targets/<slug>-A-be   | —         | skipped | created   |
```

Pod ní je stav hooku (`installed` / `chain-needed` + návod pro husky/lefthook)
a tabulka **data leakage guard** (secrets, `.env*` trackované / ignorované,
prod dumpy). `FAIL` v guardu = **stop před klávesnicí**: vyřeš (odstraň
secret, `git rm --cached .env`) a spusť `python tool/cli/worktree.py guard
--slug <slug>` znovu. Pokud setup připomene `init-pr`, spusť
`python tool/cli/worktree.py init-pr --slug <slug>` — první PR pilotu
(`docs/INTEGRATION_GUIDE.md` + `CLAUDE.md`) do target repa.

> ⚠ **KRITICKÉ (ADR-0009 P0 fix)**: Tento command spawne worktree v
> **target zákazníkově repu**, ne v PflanzerMethod meta-repu. Jinak by
> CC kódoval do tohoto toolu a reuse by byl 0 %.
>
> Vyžaduje `projects.target_repo_url` / `target_repos` (KROK 3 pro pilot/production).
>
> Po Session 1 (mezi sessions): `python tool/cli/worktree.py preview --slug <slug>`
> vytiskne draft PR per varianta (preview URL z Vercel/Netlify v PR checks,
> `--run` je opravdu založí a uloží URL do `variants.prototype_url`);
> `--mode playwright` nahraje průchod acceptance scénáři (video + trace).
> Session 2: `python tool/cli/worktree.py set-session --slug <slug> --session 2`.

**Tým rozdělí po dvojicích, každá:**
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

Facilitátor (ty) hlídá čas — **30 min cap**, pak diff walkthrough (KROK 4.5)
a voting bez ohledu na hotovost.

**Žádná AskUserQuestion za URL** — pro CC mode je branch deterministický
(`pflanzer/<slug>-A`, per `tool/cli/worktree.py`). Voting v kroku 5
dostává branch path.

### KROK 4.5 — DIFF WALKTHROUGH (dev vysvětlí, co AI napsalo)

> **Hard rule:** bez diff walkthroughu se voting (KROK 5) nekoná.
> AI kód bez lidského výkladu = stakeholdeři hlasují o UI, ne o kódu
> (per `04-session-1.md` § Detailní agenda + Failure modes).

**5 min per varianta**, facilitátor hlídá čas. Pro každou variantu (A, B, C):

1. Facilitátor vyzve dev pár dané varianty (jméno z KROK 2B owners).
2. V jejich worktree spusť (base = `projects.target_branch`, default `main`):

   ```bash
   cd ~/.pflanzer/targets/<your-slug>-X      # X = A / B / C
   git diff --stat <base>...HEAD
   git log --oneline <base>..HEAD
   ```

   Výstup vyhoď na TV.
3. Dev pár řekne **3 věci** (každá 1 věta):
   - **Reuse** — které existující komponenty/soubory použil nebo upravil,
   - **Nové** — co přibylo (nové soubory, endpointy, komponenty),
   - **Mock** — co je mock/stub/hardcoded a v prod by chybělo.
   Volitelně: které scénáře z `tests/acceptance/<slug>.feature` projely.

Výsledek ulož per varianta do pole `diff_summary` ve vote JSON specu
(KROK 6), např.:

```json
"diff_summary": {
  "stat": "<výstup git diff --stat, poslední řádek stačí>",
  "touched_existing": ["src/components/Form.tsx", "..."],
  "reuse": "<1 věta>", "new": "<1 věta>", "mock": "<1 věta>",
  "acceptance_pass": "3/4"
}
```

> Dokud `record_voting()` v `quick_session.py` pole `diff_summary`
> nepersistuje, **připoj 3 věty i na konec `description`** dané varianty
> (jinak se ztratí).

Dimenze `effort` a `risk` v KROK 5 se skórují **až po** tomto kroku —
podložené diffem, ne pocitem z UI.

### KROK 5 — VOTING (silent dot voting)

Voting začíná **až po dokončení KROK 4.5** (diff walkthrough všech variant).

Pro každého člena u stolu (jméno z kroku 2B/owners) projdi tento mini-loop:

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

> ⚠ **Speed mode**: pokud je týmu > 4, použij Liberating Structures **1-2-4-All**:
> 1 min sami, 2 min ve dvojici, 4 min v čtveřici, pak All. Hlasy SILENT,
> Decider hlasuje **poslední** (per `04-session-1.md` § HiPPO push).

Sestav `votes` array per variant:

```json
[
  {
    "name": "A", "builder": "v0", "description": "happy-path minimum",
    "diff_summary": {"stat": "...", "reuse": "...", "new": "...", "mock": "..."},
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
- **Kdo / Owner / Commitment 0-3 / Rationale** (table)
- Kill criteria
- ⚠ Pre-production TODO (triage deferred — re-run před pilotem)
- Co dál (5 akčních bodů)

### KROK 8 — Production path hint (pokud risk_profile != throwaway)

Pokud tým chce **kód reálně použít**:

```
> 🚀 Production path:
> 1. Sběr feedbacku (5-7 dní) přes web hub: /pflanzer-feedback-pull <slug>
> 2. Decisional session: /pflanzer-session-2 <slug>  (Decider Go/Iterate/Kill)
> 3. Production hardening: /pflanzer-session-3 <slug>
>    → extract code z buildru → 7 quality gates → score 0-100
>    → pokud >= 80, většina kódu je ready k mergi
> 4. Handoff: /pflanzer-handoff <slug>
>    → per-role package s odkazy na soubory + open-PR commands
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
- `docs/methodology/04-session-1.md` (canonical Session 1 — co tento command zkracuje)
- `docs/decisions/0008-tool-form-factor.md` § Hybrid (CC + web hub)
- Plný flow (4 sessions): `/pflanzer-charter` → `/pflanzer-roles` →
  `/pflanzer-triage` → `/pflanzer-session-1` → mezi-session → `/pflanzer-session-2`
- Quick flow (1 session): `/pflanzer` → handoff → (optional) plný flow později.
