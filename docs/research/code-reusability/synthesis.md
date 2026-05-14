# Synthesis — top changes for code reusability

> Wave 1+2 syntéza · 2026-05-14 · branch `research/code-reusability`
> Editor: Senior Tech Lead. Vstup: 5 expertních perspektiv (cc-coding,
> vibe-product-flow, devex, qa-test-architect, brownfield-integration).
> Cílová metrika: **% LOC merged without modification** ze winning variant
> branche → target ≥ 80 %.

---

## TL;DR (5 bullets) — top páky pro `% LOC merged without modification`

1. **P0 BUG: worktree se vytváří v meta-repu PflanzerMethod, ne v target repu.**
   `pflanzer.md:120-125` spouští `git worktree add` z `cwd = ~/Documents/PflanzerMethod/`.
   Důsledek: 100 % aktuálních in-room sessions produkuje kód v špatném repu →
   reuse z definice 0 %. Bez fixu je všech 9 dalších páček placebo.
   *(endorsed: 01, 05; cited as P0 catastrophic)*
2. **Skeleton musí být klon target repa, ne generický Vite scaffold** —
   `extract.py:50 SKELETON_FILES` generuje greenfield, kam kód nepoputuje.
   Klon target repa = AI vidí real `package.json`, real ESLint config, real
   komponenty → import `@/components/ui/Button` místo `<button>`. Sám o sobě
   skok ~30 % → ~75 % reuse. *(endorsed: 01, 03, 05)*
3. **Sdílený `src/test/` harness (render, factories, MSW server, axe) v skeletonu** —
   největší single intervence proti `rewrite_loc_ratio`. Brownfield už podobnou
   infrastrukturu má, drop-in funguje. Healthcare case study: zvedlo
   `tests merged unmodified` z 12 % → 78 %. *(endorsed: 03, 04)*
4. **Acceptance criteria (Gherkin) jako VSTUP do session, ne výstup z handoffu** —
   Decider píše scénáře v Charter wizardu, `extract.py` zapíše jako
   `tests/acceptance/<slug>.feature` do všech 3 worktree. AI píše implementaci
   *aby projela* spec, ne sám si test vymýšlí. Tím získáš apples-to-apples
   srovnání variant a vynucený negative-path coverage. *(endorsed: 02, 04)*
5. **Variant C = "evolve existing component", ne "smart defaults"** + mandatory
   "Component scout" pre-flight. AI dostane konkrétní soubory k rozšíření
   místo prázdného plátna. Když evolve vyhraje, reuse je 99 %; když
   nevyhraje, ostatní varianty musí Deciderovi vysvětlit proč ne.
   *(endorsed: 02, 01)*

---

## Top 10 cross-cutting témat

Seřazeno podle: effect strength DESC → cost ASC → # endorsements DESC.

### T1. Worktree musí být v target repu, ne v PflanzerMethod
- **Endorsed by**: 01, 05 (oba P0)
- **Effect strength**: **catastrophic** (gating fix; bez něj reuse = 0 %)
- **Cost**: S (1 helper script + 1 prompt edit)
- **Mechanism**: AI kóduje uvnitř target repa = automaticky respektuje jeho
  conventions, importy, ESLint, komponenty. Bez tohoto všechno ostatní je
  theatre.
- **Concrete first step**: vytvořit `tool/cli/worktree.py setup --slug X`
  který naclonuje target repo do `~/.pflanzer/targets/<repo-slug>/` a vytvoří
  3 worktree z target clonu. Přepsat `pflanzer.md:120-125` na volání tohoto
  helperu. Pre-flight check v `extract.py`: `cwd_remote_url == target_repo_url`,
  fail-loud jinak.

### T2. Acceptance criteria (Gherkin) jako vstup, ne výstup
- **Endorsed by**: 02 (jako "merge-vote / ship contract"), 04 (Q5, "architecturally most impactful change")
- **Effect strength**: **high**
- **Cost**: M (Charter wizard step + skeleton write + nový gate + Playwright dep)
- **Mechanism**: AI píše implementaci *aby projela* spec, ne aby napsala
  vlastní testy. Sdílený acceptance file napříč 3 worktree → Decider porovnává
  objektivně (kdo prošel kolik scénářů). Eliminuje "apples-to-oranges"
  Session 2 dilema.
- **Concrete first step**: do `tool/cli/charter.py` (Slice 1 wizard) přidat
  krok "Acceptance criteria" — 3-5 Gherkin scénářů (1 happy + 2 negative
  + 1 edge), persistnout do `projects.acceptance_criteria_md`. Pak
  `extract.py:_scaffold_skeleton()` zapíše jako `tests/acceptance/<slug>.feature`
  + `tests/acceptance/<slug>.spec.ts` Playwright skeleton. Builder prompt
  v `quick_session.py:385` přidá krok 0: "PŘED PSANÍM si přečti
  `tests/acceptance/<slug>.feature` — to JE specifikace."

### T3. INTEGRATION_GUIDE.md mandatory v target repu, vždy první read v promptu
- **Endorsed by**: 05 (C2, P0), 01 (C3 explicit read list)
- **Effect strength**: **high**
- **Cost**: S (template + 1 wizard prompt)
- **Mechanism**: 5-letý repo má implicitní pravidla (auth wrapper, API client,
  state lib, logger, feature flag, folder layout). AI je nikdy neuhodne ze
  30 min exploration. Mandatory guide = AI píše idiomatic kód od commit 0.
- **Concrete first step**: nový slash command `/pflanzer-init-target` který
  scanne target `package.json`, folder structure a vyrobí first-pass
  `docs/INTEGRATION_GUIDE.md` (auth, API, state, logger, flags, styling,
  folder layout, DB, tests, CI). Sponzor 30 min review. V `_render_builder_prompt()`
  enforce: "1. read INTEGRATION_GUIDE.md (fail-loud pokud chybí pro
  non-throwaway profile)".

### T4. Sdílený `src/test/` infrastruktura v skeletonu
- **Endorsed by**: 04 (Q4, HIGH), 03 (DevEx #10), 01 (implicit)
- **Effect strength**: **high**
- **Cost**: S (5 souborů + 5 devDeps)
- **Mechanism**: Brownfield reposy už tuto infrastrukturu mají v podobné
  formě. Sdílený `render.tsx` + `factories.ts` + `server.ts` (MSW) +
  `axe.ts` = drop-in při merge. Bez něj ad-hoc setup per variant = 100 %
  test rewrite.
- **Concrete first step**: do `extract.py:50 SKELETON_FILES` přidat
  `src/test/{render.tsx,factories.ts,server.ts,handlers.ts,axe.ts}`. devDeps:
  `msw@^2.4`, `@faker-js/faker@^9`, `jest-axe@^9`, `@axe-core/playwright@^4.10`,
  `@testing-library/user-event@^14`. Reference: konkrétní obsah souborů
  v perspektivě 04 § Q4.

### T5. Skeleton = klon target repa (s fallback na generic pro throwaway)
- **Endorsed by**: 01 (C1, HIGH), 05 (C1, P0), 03 (implicit přes `--target-repo`)
- **Effect strength**: **high**
- **Cost**: M (clone caching, package-manager auto-detect, skeleton fallback path)
- **Mechanism**: AI vidí real conventions od prvního tokenu. Reuse skok
  ~30 % → ~75 %.
- **Concrete first step**: v `extract.py:284 _scaffold_skeleton()` přidat
  větev: pokud `target_repo_url` set, `git clone --depth=1 --filter=blob:none
  $url $dest && git checkout -b feat/$slug-$variant`. Detect package manager
  z `packageManager` field. Generický `SKELETON_FILES` jen jako fallback pro
  `throwaway`.

### T6. Quality gates — composite `tests` + nový `acceptance` + (evolve) `mutation`
- **Endorsed by**: 04 (Q1, Q2, Q5; HIGH), 03 (#8 coverage gate), 01 (C5 integration_diff)
- **Effect strength**: **high**
- **Cost**: M (přepis `gate_tests`, +Playwright, +Stryker pro evolve)
- **Mechanism**: Současný `gate_tests` je placebo (1 trivial test = pass).
  Composite (pass/fail + coverage + negative-path + test:code ratio) +
  acceptance scenarios pass rate + mutation score (jen evolve) = real signal,
  ne vanity. Banking case study: 100 % coverage suite, mutation score 18 %.
- **Concrete first step**: přepsat `quality_gates.py:142-159 gate_tests` na
  composite (kód v perspektivě 04 § Q1). Přidat nový `gate_acceptance`
  (weight 2.5, gating). Přidat `gate_mutation` (weight 1.0, jen pro
  `evolve`). Re-balance weights dle perspektivy 04 § Q9.

### T7. Pre-commit gates per worktree (lefthook + Biome)
- **Endorsed by**: 03 (#1, #3; HIGH), 01 (#7 anti-pattern: "spustit gates jednou na konci")
- **Effect strength**: **high**
- **Cost**: S (lefthook.yml + biome.json + 2 devDeps)
- **Mechanism**: AI nemůže commitnout broken kód. Session 1 končí 3× variant
  s passing types + lint + 0 secrets per commit. `quality_gates.py`
  v Session 3 jen ověřuje, ne diagnostikuje. Lefthook > Husky (Go binary,
  paralelní, žádný shell wrapper). Biome > ESLint+Prettier (~25× rychlejší,
  jeden config).
- **Concrete first step**: do `SKELETON_FILES` přidat `lefthook.yml` +
  `biome.json` (kód v perspektivě 03 § 1+3). Smaž `.eslintrc.cjs` a
  `.prettierrc`. devDeps: `@biomejs/biome@1.9.4`, `lefthook@1.7.18`,
  `@commitlint/cli@19.x`, `secretlint@9.x`. Přidej `"prepare":
  "lefthook install"` script.

### T8. Adaptive shim layer v skeletonu (auth/api/logger/flags)
- **Endorsed by**: 05 (C5, C6, C8, C9; MED-HIGH), 03 (implicit přes path aliases)
- **Effect strength**: **high**
- **Cost**: M (5 interface souborů + lint rules + apply-aliases logic)
- **Mechanism**: Komponenta `useCurrentUser()` / `sdk.users.get()` /
  `logger.info()` zůstane unchanged při merge. Při extractu se swapne jen
  implementace v 1 souboru. 1-line swap vs 50-component rewrite.
- **Concrete first step**: do `SKELETON_FILES` přidat `src/lib/auth.ts`
  (interface + mock), `src/api/sdk.ts` (interface + fetch mock),
  `src/lib/logger.ts` (interface + console mock), `src/lib/flags.ts`
  (interface + always-on mock), `src/stores/index.ts` (Zustand-style
  abstrakce). Lint rule (Biome): `no-restricted-imports` banuje raw `fetch`
  mimo `@/api/`, `no-console: error`.

### T9. Path aliases (`@/`) + `tsconfig.base.json` + `noUncheckedIndexedAccess`
- **Endorsed by**: 03 (#6, "single největší páka pro ≥ 80 %"), 05 (C10 implicit)
- **Effect strength**: **high**
- **Cost**: S (2 tsconfig souborů + 3 řádky vite.config.ts)
- **Mechanism**: Brownfield monorepa skoro vždy mají `@/` alias (Next.js,
  shadcn/ui standard). AI generující `import X from '../../../components/Button'`
  → brownfield přepíše na `@/components/Button` = každý import je rewrite.
  `noUncheckedIndexedAccess` přidá real type safety, kterou brownfield už má.
- **Concrete first step**: rozdělit skeleton `tsconfig.json` na `tsconfig.base.json`
  (paths, strict, noUncheckedIndexedAccess) + `tsconfig.json` (extends). Přidat
  `resolve.alias` v `vite.config.ts`. Kód v perspektivě 03 § 6.

### T10. Component scout pre-flight + Variant C jako "evolve existing"
- **Endorsed by**: 02 (C1+C2, HIGH), 01 (implicit "read existing patterns")
- **Effect strength**: **high**
- **Cost**: M (wizard krok + scout helper + variant angle swap)
- **Mechanism**: 1 ze 3 variant je nuceně reuse-first. AI dostane konkrétní
  soubory k rozšíření, ne prázdné plátno. Hard constraint "no new files in
  src/components/" pro evolve angle sníží AI tendenci tvořit
  `NewFlowComponent.tsx` o ~50 %.
- **Concrete first step**: v `pflanzer.md` mezi KROK 2 a 3 přidat KROK 2.5
  "Component scout" (otázka + path picker → `data/preflight/<slug>/component-map.md`).
  V `quick_session.py:298 VARIANT_ANGLES` swap C podle profilu: pro
  `pilot/production` → "evolve existing", pro `throwaway` ponechat "smart
  defaults". V `_render_builder_prompt()` pro evolve inject hard constraint
  + component-map.md jako "## Existing components to extend".

---

## Konflikty mezi perspektivami

### K1. Pact (contract testing) — 01 vs 04
- **01 (cc-coding)**: zmiňuje Pact implicitně v handoff context jako contract test.
- **04 (qa-test)**: explicitně **odmítá Pact pro MVP** (Q8, kontroverzní).
  Pact = tax pro single-team projekty, dává smysl jen pro nezávislé
  consumer/provider týmy.
- **Resolution**: **přijmout pozici 04**. Skeleton ship-uje sdílenou MSW
  handler library jako single source of truth FE/BE/E2E. Pact až jako P2P
  promotion path v `qa.md` handoff dokumentu pro `evolve` profil
  s multi-team consumer (MSW handlers → Pact convertable přes
  `mockServer.toPactJson()`). **Punt to evolve when 2+ consumer teams.**

### K2. 5-7 day mezi-session okno vs 48-72 h
- **Současná metodika**: 5-7 dní async feedback window.
- **02 (vibe-product)**: 48-72 h max (C4). 5-7 dní = "Slack-ticho, sponsor
  zahltí jiné priority, nikdo neviděl kód kriticky".
- **Resolution**: **zkrátit na 48-72 h** + změnit *úkol* mezi-session
  z "klikni a dej preference" na "otevři PR diff, napiš keep/fix/kill per
  soubor". Web hub default route = diff view, ne preview iframe. Push
  notification 24h/48h/70h před Session 2 deadline.

### K3. Strict TypeScript jako test substitute
- **Implicitní v některých discussions**: TS strict chytá bugy, méně testů
  potřeba.
- **04 (qa-test)** anti-pattern #6: TS chytá ~30 % bugů (překlepy), ne
  runtime invariants (auth, money math, datetime, async race conditions).
  Healthcare incident: TS strict, 0 runtime test, off-by-one v insulin dose →
  3 patient overdose.
- **Resolution**: **TS strict je table stakes (skeleton to už má), NE
  substitute za runtime testy.** Mandatory `gate_acceptance` (Playwright)
  pro runtime invariants.

### K4. Console.log jako fail vs warn
- **Současný `gate_observability` (`quality_gates.py:298`)**: fail na > 3 console.log.
- **03 (devex)**: too strict v prototype fáze; downgrade na warn, přesunout
  do lint rule (`no-console`) v pre-commit hook.
- **04 (qa-test)** anti-pattern #7: souhlasí s downgrade na warn.
- **05 (brownfield)** C9: `no-console: error` lint rule + logger shim
  v skeletonu.
- **Resolution**: **lint-time fail (Biome `no-console: error`) v skeletonu +
  logger shim** (T8). Post-mortem `gate_observability` downgrade na warn-only
  s weight 0.25. Kombinace = best of both: pre-commit zachytí, post-mortem
  jen reportuje.

### K5. Big skeleton vs minimal adaptive shim
- **01 (cc-coding)**: skeleton bohatě vybavit (husky, lint-staged, commitlint,
  CLAUDE.md per worktree, PR template).
- **05 (brownfield)**: skeleton je **jen pro throwaway**. Pro pilot/production
  worktree vychází z target clone → skeleton není potřeba.
- **Resolution**: **dvouvrstvý approach**. Pro `target_repo_url` set = clone
  target (T5). Skeleton pak existuje *jen* jako adaptive shim layer (T8 — auth,
  api, logger, flags, sdílený test harness T4) injektnutý do clone, ne jako
  full Vite scaffold. Pro `throwaway` = full generic skeleton zůstává.

### K6. ESLint vs Biome
- **01 (cc-coding)**: zachovat ESLint + Prettier (žádný explicitní call).
- **03 (devex) #1**: switch na Biome (~25× rychlejší, jeden tool).
- **Resolution**: **přijmout 03 (Biome)**. ESLint je legacy v 2026,
  Biome 1.9.x má a11y rules + format + lint v jednom binary. Lint v <500 ms
  i pro 50k LOC = pre-commit nezpomaluje session iteration.

---

## Recommended ADR-0009 scope

Top 5 změn, které mění tool architekturu (ne jen config tweaks):

### ADR candidate 1: "Worktree v target repu (P0 fix)"
- **Context**: Současný `pflanzer.md:120-125` vytváří worktree v meta-repu.
  Reuse z definice 0 %.
- **Decision**: Nový `tool/cli/worktree.py setup --slug X` který clonuje
  target repo do `~/.pflanzer/targets/` a vytvoří 3 worktree z clonu.
  Pre-flight check v `extract.py` validuje `cwd_remote_url`.
- **Consequence**: `target_repo_url` se stává mandatory pro
  `risk_profile in (pilot, production)`. Charter wizard musí blokovat
  advance bez něj. `~/.pflanzer/targets/` cache directory přibývá.

### ADR candidate 2: "Acceptance criteria jako Charter input + acceptance gate"
- **Context**: AI generuje testy after-the-fact, každá varianta testuje
  něco jiného. Decider rozhoduje na vibe.
- **Decision**: Charter wizard vyžaduje 3-5 Gherkin scénářů. `extract.py`
  je zapíše jako `tests/acceptance/<slug>.feature` + Playwright skeleton.
  Nový `gate_acceptance` (weight 2.5, gating). Decider's Go vyžaduje
  ≥ 80 % scenarios passed.
- **Consequence**: Session 2 brief = `playwright report --json` per varianta
  (apples-to-apples). Charter bez acceptance criteria = `CharterError`
  refuse to proceed. +1 dependency: `@playwright/test`.

### ADR candidate 3: "Adaptive shim layer namísto full skeleton (auth/api/logger/flags)"
- **Context**: Generic Vite skeleton produkuje kód, který v brownfield repu
  vyžaduje 100 % rewrite na auth/API/logger/flags layer.
- **Decision**: Skeleton ship-uje 5 interface souborů (`src/lib/auth.ts`,
  `src/api/sdk.ts`, `src/lib/logger.ts`, `src/lib/flags.ts`,
  `src/stores/index.ts`) s mock implementací. Lint rules banují raw `fetch`,
  `console.log`, hardcoded user. Při merge se swapne jen impl.
- **Consequence**: Variant code je portable. Brownfield reviewer mění 5
  souborů, ne 200. Vyžaduje per-target swap config (deferred do Sprint 4+).

### ADR candidate 4: "Quality gates re-architecture (composite tests + acceptance + mutation + collision)"
- **Context**: Současné gates měří "funguje to", ne "merguje se to".
  `gate_tests` je placebo (1 trivial test = pass).
- **Decision**: Přepsat `gate_tests` na composite (Q1). Přidat `gate_acceptance`
  (Q5, weight 2.5, gating), `gate_mutation` (Q2, weight 1.0, jen evolve),
  `gate_shared_module_touch` (collision, weight 2.0). Re-balance weights:
  acceptance > tests > security > types > build > lint > a11y > visual >
  observability.
- **Consequence**: Variant s passing gates = skutečně mergeable. Stryker
  jen pro `evolve` (~3-5 min runtime). Playwright dependency. Existing
  `gate_observability` downgrade na warn-only.

### ADR candidate 5: "Mezi-session feedback window 48-72h + diff-first web hub"
- **Context**: 5-7 day async feedback = sabotáž (Slack-ticho, povrchní
  feedback, Session 2 rozhoduje na tenkém datasetu).
- **Decision**: Zkrátit na 48-72 h (po 72h Session 2 běží, missing feedback
  = "no objection"). Web hub default route = `git diff main...feat/<slug>-X`,
  ne preview iframe. Reviewer flow: per soubor → keep/fix/kill + 1 věta.
  Push notification 24h/48h/70h před deadline.
- **Consequence**: Slice 6 (web hub) potřebuje diff view UI + structured
  comment form + notification scheduler. Methodology dokumentace `04-session-1.md`
  § "Délka" update. Nový "Shadow PM" role v `pflanzer.md` KROK 2.

---

## Punt list (good ideas, defer)

Ne v top 10, ale na backlogu:

- **Pact contract tests** — odložit do "evolve + 2+ consumer teams" scenario
  (per K1 resolution).
- **Visual regression (Playwright pixel diff)** — Q7, MED effect, opt-in jen
  pro `evolve` profil. Implementovat až po T6.
- **Stryker mutation testing** — viz ADR 4, ale jen pro `evolve`. Cost MED
  (~3-5 min runtime), implementovat ve Sprint 4+.
- **Merge-vote (2nd Decider call)** — perspektiva 02 C3, MED-HIGH. Sociální
  ritual, hodnotný ale ne blocker. Přidat do Slice 5 backlog.
- **Shadow PM role** — perspektiva 02 C7. Closely-related k mezi-session 48h
  okno (ADR 5), ale samotná role-definition může počkat.
- **Two-truth wrap-up question** — perspektiva 02 C10, MED. Nice ritual,
  nemění tooling.
- **Merge Clinic týdenní ritual** — perspektiva 02 C9, MED. Org behavior,
  ne tool change.
- **Database migration protokol** — perspektiva 05 C4, MED-HIGH. Kritické
  pro BE-heavy varianty, ale frontend-first MVP může počkat.
- **Feature flag auto-wrap** — perspektiva 05 C8, MED. Závisí na enterprise
  flag client (Cognito/LaunchDarkly/internal); odložit do per-target setup.
- **`extract --apply-aliases` brownfield rewriter** — perspektiva 05 C10,
  MED. Hodnota až po stabilním T9 (path aliases skeleton baseline).
- **Sequential merge protokol (commit-train)** — perspektiva 05 C7, HIGH ale
  cost L (nový CLI command + git rebase logic + multi-PR orchestration).
  Implementovat až po T1+T5+T6 stabilizaci.
- **Strict commit hygiene (Conventional Commits enforcement)** — perspektiva 01
  C4, MED. Enforced přes T7 (lefthook + commitlint), no separate ADR potřeba.
- **`ts-reset`** — perspektiva 03 #7, MED. Jednorázový dependency add,
  trivial.
- **Coverage gate (60 % branches threshold)** — perspektiva 03 #8 + 04 Q1.
  Subsumed by ADR 4 (composite `gate_tests` includes coverage).

---

## Implementation order (sprint plan)

### Sprint 1 (this week) — fix the P0 bug

**Cíl**: Worktree v target repu. Bez tohoto je vše ostatní placebo.

**Commits**:
1. `feat(worktree): add tool/cli/worktree.py setup command`
   - Nový soubor `tool/cli/worktree.py` s `setup --slug X` příkazem
   - Načte `projects.target_repo_url` z DB (mandatory pro non-throwaway)
   - Clone target do `~/.pflanzer/targets/<repo-slug>/` (cached, full clone)
   - Vytvoří 3 worktree `git worktree add ../<slug>-{A,B,C} -b pflanzer/<slug>-{A,B,C} origin/main`
   - Spustí package-manager install paralelně (detect via `packageManager` field)

2. `feat(charter): mandatory target_repo_url for pilot/production profiles`
   - V `quick_session.py:141 bootstrap()` validate `target_repo_url is not None`
     pro `risk_profile in ("pilot", "production")`
   - `tool/cli/charter.py` wizard blokne advance bez URL

3. `fix(worktree): pre-flight check in extract.py — cwd remote URL must match target`
   - V `extract.py:284` před scaffoldem: `git remote get-url origin` v `dest`
     musí matchovat `projects.target_repo_url`. Jinak fail-loud.

4. `docs(commands): rewrite pflanzer.md KROK setup to call worktree.py`
   - `pflanzer.md:120-125` nahradit za `python tool/cli/worktree.py setup --slug $SLUG`
   - Přidat assert: pokud `target_repo_url` chybí pro non-throwaway, halt

**PR title**: `fix(P0): worktree spawned in target repo, not meta-repo`
**Acceptance**: New session pro test target repo (např. claude.gizmax.cz/cardigo)
vytvoří 3 worktree v target clonu, `git remote -v` v každém worktree ukazuje
target URL, ne PflanzerMethod URL.

---

### Sprint 2 (next week) — quality gates upgrade

**Cíl**: Gates měří "mergeable", ne "funguje to".

**Changes to `quality_gates.py`**:
1. **Přepsat `gate_tests` (line 142-159) na composite** (per perspektiva 04 Q1):
   pass/fail + branch coverage + negative-path heuristic + test:code ratio.
   Vrátit `metric=branches_coverage` pro tracking.

2. **Přidat `gate_acceptance` (NEW, weight 2.5, gating)**:
   ```python
   def gate_acceptance(path: Path) -> GateResult:
       # Spustí npx playwright test tests/acceptance/
       # Parse % scenarios passed
       # @deferred = warn, missing oproti charter spec = fail
   ```

3. **Přidat `gate_shared_module_touch` (NEW, weight 2.0)** (per perspektiva 05 C3):
   detekuje touch shared modulů (`src/lib/auth`, `src/api/client`, `src/components/ui`,
   `src/stores/`, `tailwind.config`, atd.). > 3 = fail; 1-3 = warn s collision matrix.

4. **Přidat `gate_mutation` (NEW, weight 1.0, jen `evolve`)** (per Q2):
   Stryker incremental, scope `src/{lib,utils,hooks}/**`. Score ≥ 70 = pass,
   ≥ 50 = warn, < 50 = fail. **NIKDY** v Session 1 (runtime kill).

5. **Re-balance `GATE_WEIGHTS` (line 41-49)**:
   ```python
   GATE_WEIGHTS = {
       "acceptance": 2.5, "tests": 2.0, "security": 2.0,
       "shared_module_touch": 2.0, "types": 1.5, "build": 1.5,
       "mutation": 1.0, "lint": 1.0, "a11y": 1.0,
       "visual": 0.5, "observability": 0.25,
   }
   ```

6. **Reorder gates v `run_all` (line 374-377) na fail-fast**:
   build → types → lint → tests → acceptance → security → shared_module_touch
   → mutation → a11y → visual → observability. Build/types fail = skip rest.

7. **`_ensure_install()` helper** — `npm ci` pokud chybí `node_modules`
   (per perspektiva 03 #5).

**Changes to `extract.py:SKELETON_FILES` (line 50-247)**:
1. **Přidat sdílený test harness** (T4):
   - `src/test/render.tsx` (provider wrapper)
   - `src/test/factories.ts` (Faker factories)
   - `src/test/server.ts` + `handlers.ts` (MSW v2)
   - `src/test/axe.ts` (jest-axe re-export)
2. **Přepsat `App.test.tsx` na 5-test reference suite** (per Q3): demonstrate
   happy + 2 negative + a11y + factory edge case patterns.
3. **Adaptive shim layer** (T8):
   - `src/lib/auth.ts`, `src/api/sdk.ts`, `src/lib/logger.ts`,
     `src/lib/flags.ts`, `src/stores/index.ts`
4. **Path aliases** (T9):
   - `tsconfig.base.json` (paths, strict, noUncheckedIndexedAccess)
   - `vite.config.ts` resolve.alias
5. **Pre-commit gates** (T7):
   - `lefthook.yml` + `biome.json`
   - Smaž `.eslintrc.cjs`, `.prettierrc`
6. **Pin versions** (per perspektiva 03 #2):
   - `engines.node = "20.11.1"`, `packageManager = "npm@10.2.4"`
   - `.nvmrc`, `.npmrc` (engine-strict, save-exact)
7. **Skeleton fallback path**: pokud `target_repo_url` set → skip generic
   `SKELETON_FILES`, jen overlay shim layer (`src/lib/`, `src/test/`)
   na clone.

**PR titles**:
- `feat(gates): composite tests gate + acceptance + shared_module_touch + mutation`
- `feat(skeleton): shared test harness + adaptive shim layer + path aliases`
- `chore(skeleton): switch ESLint+Prettier to Biome, Husky to lefthook`

**Acceptance**: Re-skóre 3 historických session runs (cardigo, investment-bot,
test slug) s novými gates. Variant ranking se změní u ≥ 1 z 3 = signal funguje.

---

### Sprint 3 — product flow + handoff

**Cíl**: Wizard vyžaduje acceptance criteria, handoff = PR za 30s, mezi-session
okno = 48-72h s diff-first web hub.

**Changes to `pflanzer.md` wizard**:
1. **KROK 2.5 — Component scout** (T10):
   `AskUserQuestion: Existuje v target repu komponenta řešící ≥ 50 % problému?`
   Volá `quick_session.py scout --slug X --paths ...` →
   `data/preflight/<slug>/component-map.md`.

2. **KROK 3.5 — Acceptance criteria** (ADR 2):
   `AskUserQuestion: 3-5 Gherkin scénářů (1 happy + 2 negative + 1 edge)`.
   Persistnout do `projects.acceptance_criteria_md`.

3. **KROK 6 — Merge-vote po Decider's preference** (perspektiva 02 C3):
   `AskUserQuestion: kdyby winner přišel zítra ráno jako PR, mergnul bys?`
   Options: today / this week / re-write / throwaway. Persist jako
   `decisions.type='merge_intent'`.

4. **KROK 7 — Two-truth pre-mortem** (perspektiva 02 C10):
   Každý u stolu odpoví: "1 věta — co bys jako první kritizoval(a)?".

**Changes to `quick_session.py`**:
1. **`bootstrap()` (line 141)** — nová pole: `target_branch_owner` (mandatory
   non-throwaway), `ship_window_sprint`, `shadow_pm`. Wizard blokne bez nich.
2. **`VARIANT_ANGLES` (line 298)** — swap C podle profile (T10):
   - `throwaway` → "smart defaults" (current)
   - `pilot/production` → "evolve existing" + hard constraint "no new files
     in src/components/"
3. **`_render_builder_prompt()` (line 385)** — inject:
   - `INTEGRATION_GUIDE.md` jako 1st read (fail-loud pokud chybí)
   - `tests/acceptance/<slug>.feature` jako 2nd read (krok 0: "to JE specifikace")
   - `component-map.md` jako "## Existing components to extend" (pokud existuje)
   - Explicit read list (CLAUDE.md, package.json, tsconfig.json, eslint config,
     `src/components/ui/index.ts`, `src/lib/api/client.ts`, recent PR diffs)
   - Pro evolve angle: hard constraint block (no new files, max 1 nový hook)
   - Conventional Commits prompt (Variant: X, Pflanzer-session: slug trailers)

**Changes to `handoff.py`** (perspektiva 02 C6):
1. **Konsolidovat 8 souborů na 2 + 1 PR draft**:
   - `data/handoffs/<slug>/SHIP.md` — 1-page (co/kdo/kdy/jak otestovat/jak rollbacknout)
   - `data/handoffs/<slug>/CONTEXT.md` — slepený zbytek (Charter + role notes
     + decisions + triage), pro audit
   - **Render `gh pr create` command** s pre-filled title, body (z SHIP.md),
     labels (`pflanzer`, `risk:<profile>`), assignees (`target_branch_owner`),
     `--draft`. Facilitátor copy-pastne, PR existuje do 30s.
   - 8 původních souborů zachovat za `--full` flag (compliance theatre).
2. **`render_qa()`** — nahradit Pact section za "MSW handlers — single source
   of truth FE/BE/E2E" s odkazem na `extracted/<slug>/<variant>/src/test/handlers.ts`.
   Pact jen jako P2P promotion path note (per K1 resolution).

**Changes to Charter (`tool/cli/charter.py` + DB schema)**:
1. **Schema additions** (`tool/db.py` migration):
   - `projects.target_branch_owner TEXT`
   - `projects.ship_window_sprint TEXT`
   - `projects.shadow_pm TEXT`
   - `projects.acceptance_criteria_md TEXT NOT NULL` (pro non-throwaway)
   - `projects.integration_guide_path TEXT`
   - `projects.existing_component_paths TEXT` (JSON list)
   - `decisions.type` extend o `'merge_intent'`, `'self_critique'`
2. **Wizard kroky** — viz `pflanzer.md` updates výše.

**PR titles**:
- `feat(charter): mandatory acceptance criteria + ship contract fields`
- `feat(wizard): component scout + merge-vote + two-truth steps`
- `feat(handoff): SHIP.md + auto gh pr create command (handoff_pr.py)`
- `feat(prompt): integration guide + acceptance file as builder input`

**Acceptance**: End-to-end test session na test slug. PR existuje do 30 min
po Session 3 (track `time_from_session_3_to_pr_open`). Acceptance file
shared napříč 3 worktrees, `playwright report --json` per varianta v Session 2
brief.

---

## Metric instrumentation

Každá metrika z briefu + jak ji reálně zachytit:

| Metric | Source | Capture mechanism |
|---|---|---|
| **`% LOC merged without modification`** (primary, ≥ 80%) | post-merge audit | Post-PR webhook (`tool/cli/handoff_pr.py` registers `gh pr view --json mergedAt`). Po merge: `git diff <pflanzer-branch-tip>...<merge-commit>` → `additions+deletions` divided by total LOC v winning branch. Persist do `data/method-metrics.json` jako `reusability_pct` per slug. **Manual fallback**: facilitátor zadá ručně do CLI po 7 dnech (`pflanzer metric --slug X --reusability 82`). |
| **`gate_score` per session_3 run** | `quality_gates.py` already returns this | Persist do `gate_runs` table (Slice 3+ schema). Add `composite_score`, `acceptance_passed_pct`, `mutation_score` columns (per ADR 4). Track P50/P10 across sessions. |
| **`time_to_handoff_days`** (≤ 14 wall-clock) | DB calculation | `(handoffs.created_at - projects.created_at).days`. Already trackable z existing schema, jen surface v `data/method-metrics.json`. |
| **`handoff_pr_merged_within_7d`** (binary) | gh API poll | Po `handoff_pr.py` vytvoří PR, register cron/webhook. T+7 days: `gh pr view <num> --json mergedAt,state`. Bool result do `handoffs.pr_merged_within_7d` column. |
| **`rewrite_loc_ratio`** | post-merge audit | Same as primary metric: `loc_modified_in_review / loc_merged_total`. Capture: `git log --since=<pr-open> --until=<pr-merged> -p <pr-files>` count change vs initial diff. Persist do `data/method-metrics.json`. |

**New metrics z perspektiv (worth capturing)**:

| New metric | Source | Why |
|---|---|---|
| `cwd_remote_url == target_repo_url` per worktree | pre-flight check (Sprint 1) | P0 sanity; binary fail-loud |
| `cache_read_input_tokens / total_input_tokens` ratio | CC session telemetry | T3 effectiveness; target ≥ 60 % |
| `lockfile_diff_lines_between_worktrees` | post-Session-1 audit | T7 effectiveness; target = 0 |
| `gate_runtime_p50_seconds` | `quality_gates.py` timestamps | T6+T7 effectiveness; target < 120 s |
| `commits_with_lint_fix_keyword` | `git log --grep "fix lint\|wip"` count | T7 effectiveness; target = 0 |
| `pr_first_review_to_merge_hours` | gh API | ADR 5 + sequential merge; target < 72h |
| `acceptance_scenarios_passed_pct` per variant | `gate_acceptance.metric` | ADR 2 effectiveness; gates ≥ 80 % |
| `mutation_score` (evolve only) | `gate_mutation.metric` | ADR 4 effectiveness; banking ≥ 70 %, internal ≥ 50 % |
| `shared_module_collisions_per_session` | `gate_shared_module_touch.metric` | ADR 4 + perspektiva 05 C3; target ≤ 1 |
| `time_from_session_3_to_pr_open` | `handoffs.created_at` vs `pr_opened_at` | T2/Sprint 3 effectiveness; target < 30 min |
| `test_files_imported_from_shared_harness` | post-merge `grep "from '@/test/'"` | T4 effectiveness; target ≥ 80 % |
| `console_log_count_in_merged_pr` | post-merge audit | T8 effectiveness; target = 0 |
| `winner.angle == "evolve existing"` rate | `decisions` table | T10 effectiveness; target ≥ 33 % |
| `merge_intent in (today, this_week)` | `decisions` table | ADR 5 / perspektiva 02 C3; correlate with reusability |

**DB schema additions** (`tool/db.py` migration):
```sql
ALTER TABLE handoffs ADD COLUMN pr_url TEXT;
ALTER TABLE handoffs ADD COLUMN pr_opened_at TIMESTAMP;
ALTER TABLE handoffs ADD COLUMN pr_merged_at TIMESTAMP;
ALTER TABLE handoffs ADD COLUMN pr_merged_within_7d BOOLEAN;
ALTER TABLE handoffs ADD COLUMN reusability_pct INTEGER;
ALTER TABLE handoffs ADD COLUMN rewrite_loc_ratio REAL;

ALTER TABLE gate_runs ADD COLUMN acceptance_passed_pct REAL;
ALTER TABLE gate_runs ADD COLUMN mutation_score REAL;
ALTER TABLE gate_runs ADD COLUMN shared_module_collisions INTEGER;
ALTER TABLE gate_runs ADD COLUMN composite_score REAL;
ALTER TABLE gate_runs ADD COLUMN runtime_seconds REAL;

ALTER TABLE projects ADD COLUMN target_branch_owner TEXT;
ALTER TABLE projects ADD COLUMN ship_window_sprint TEXT;
ALTER TABLE projects ADD COLUMN shadow_pm TEXT;
ALTER TABLE projects ADD COLUMN acceptance_criteria_md TEXT;
ALTER TABLE projects ADD COLUMN integration_guide_path TEXT;
ALTER TABLE projects ADD COLUMN existing_component_paths TEXT;
```

**Aggregation**: `tool/cli/method_metrics.py aggregate` cron weekly → píše
`data/method-metrics.json` souhrn (P50/P90 per metric, trend last 4 weeks).
Tento JSON je input pro budoucí dashboard / ADR retrospektivu po N projektech.

---

*References (top-cited files): `extract.py:50-247` (skeleton), `extract.py:284-307`
(scaffold), `extract.py:374-399` (extract dispatch), `quality_gates.py:40-49`
(gate weights + types), `quality_gates.py:142-159` (`gate_tests`),
`quality_gates.py:374-377` (run_all order), `quick_session.py:141-180`
(bootstrap + unused `target_repo_url`), `quick_session.py:298 VARIANT_ANGLES`,
`quick_session.py:385+` (`_render_builder_prompt`), `pflanzer.md:118-134`
(worktree setup — broken P0), `handoff.py:render_qa()` + 8-files generation.*
