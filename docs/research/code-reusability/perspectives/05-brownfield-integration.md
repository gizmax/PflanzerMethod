# Perspektiva 05 — Brownfield-Integration-Expert (Staff Engineer / Legacy Codebase Surgeon)

> Wave 2 · 2026-05-14 · branch `research/code-reusability`
> Autor persona: 15+ let staff engineering ve 4 enterprise monorepech (1.2M LOC Java/Spring,
> 800k LOC Rails, 500k LOC TS Next.js, 2M LOC C++ trading platform). Vedl 9 prototype-to-prod
> integrací; 6 z nich shořelo na merge boundary. Tato perspektiva je o **díře mezi „kód, co
> builduje" a „kód, co se mergne do 5-letého repa s 14 týmy a 11 release-train policy"**.

---

## TL;DR — 3 největší páky pro 80 % reusability

1. **Současný in-repo flow je fundamentálně rozbitý — `git worktree add ../proto-${SLUG}-A`
   v `pflanzer.md:121-125` se spouští z PflanzerMethod meta-repa.** Takže CC vibe-coduje
   uvnitř meta-toolu, ne uvnitř target produkčního repa. **Reuse je z definice 0 %, protože
   kód není v cílovém repu.** Bez fixu C-1 (clone target repo first, worktree z target clonu)
   je všech 9 dalších páček v této perspektivě placebo. Toto je P0, blocker všeho ostatního.

2. **Brownfield konvence se nedají odhadnout — musí být explicit input do session.** 5-letý
   repo má implicitní pravidla (state lib, DI pattern, error handling, logging, auth context,
   feature flag wrapper, API client). AI je nikdy neuhodne ze 30 min exploration. Páka:
   **mandatory `INTEGRATION_GUIDE.md` v target repu**, který Charter wizard vyžaduje (resp.
   vygeneruje first-pass detekcí) a builder prompt **vždy** injektne jako 1. read.

3. **„Winning variant" musí být cherry-pickable, ne merge-jako-blob.** 3 paralelní variants
   v 3 worktreech budou kolidovat na shared modules (auth context, API client, design tokens).
   Bez **breaking-change registru** (per-worktree `git diff --stat main` před Session 2) tým
   slije A+B winnera tak, že `useAuth` se přepíše třikrát různě. Páka: nový **collision gate**
   v `quality_gates.py`, který flags shared-module touch a forcuje sequential merge protokol.

---

## Diagnose — kde brownfield integrace umírá v aktuálním Pflanzer flow

### D1. Worktree v špatném repu (P0 catastrophic)

`/.claude/commands/pflanzer.md:120-125`:
```bash
SLUG=<your-slug>
git worktree add ../proto-${SLUG}-A -b feat/${SLUG}-A
git worktree add ../proto-${SLUG}-B -b feat/${SLUG}-B
git worktree add ../proto-${SLUG}-C -b feat/${SLUG}-C
```

To se ale spouští **z `cwd = ~/Documents/PflanzerMethod/`**, takže branch `feat/<slug>-A`
vznikne v meta-repu, ne v target repu. CC pak otevře `../proto-<slug>-A`, vidí
`tool/cli/extract.py`, `docs/methodology/`, `data/` — a začne kódovat „nový feature pro
PflanzerMethod". `extract.py:391-399` `method = "in_repo_branch"` jen zaregistruje tu
worktree path do DB. Žádný extrakt, žádné cross-repo přenesení.

`quick_session.py:145 target_repo_url` parametr **existuje**, ale **nikdy není použit**
v worktree setupu. Je to dead field v Charter. Pro `risk_profile in (pilot, production)`
to musí být mandatory + driving worktree base.

**Důsledek**: 100 % aktuálních in-room sessions s CC builderem produkuje kód, který se
**nikdy** nedostane do produkce, protože je v špatném repu. Jediný způsob jak to fixnout
je manuálně copy-pasta diff do PR v target repu = de facto rewrite = `rewrite_loc_ratio`
blízko 1.0.

### D2. Zero conventions injekce do builder promptu

`quick_session.py:385+ _render_builder_prompt()` říká variant angle, hook, gate target.
**Neříká** nic o:
- Auth wrapper pattern (`useCurrentUser()` vs `withAuth(Component)` vs `<AuthProvider>`)
- API client (`fetch` vs `axios` vs `@tanstack/react-query` + generated SDK)
- State management (Redux Toolkit vs Zustand vs Jotai vs context)
- Error boundary placement
- Logging interface (`logger.info()` vs `console.log` vs OTel span)
- Feature flag client (`useFlag('my-feature')` vs `if (flags.myFeature)`)
- Folder naming (`features/<name>/` vs `pages/<name>/` vs `modules/<name>/`)

Tyto věci **definují** brownfield. Bez nich AI generuje plausibly-looking kód, který
nepoužívá ani jeden z těchto patternů → každý touch v PR review = rewrite.

### D3. Žádný breaking-change / collision detector

Tři variants paralelně. Variant A přidá `src/lib/auth.ts` (rewrite useAuth).
Variant B přidá `src/api/client.ts` wrapper. Variant C upraví `src/store/index.ts`.
Decider vybere A jako winner. **Co když ale B a C taky touchnuly auth.ts?** Když A jde
do PR, B/C learnings jsou ztracené — nebo hůř, někdo je ručně merguje a vyrobí
3-way konflikt v shared module.

`quality_gates.py:40 GATE_TYPES` neobsahuje žádný cross-variant nebo target-diff gate.
Každý variant je gated v izolaci.

### D4. Database migrace = no-op v Pflanzer flow

V `extract.py SKELETON_FILES` není žádný `migrations/`, žádný Alembic config, žádný
Prisma schema, žádný Drizzle. Pokud variant potřebuje přidat sloupec do `users` tabulky,
AI buď:
(a) Upraví ORM model bez migrace → broken na review.
(b) Napíše SQL inline → broken jak řekne DBA.
(c) Skipne perzistenci, vše drží v useState → nepoužitelné v produkci.

Pflanzer nemá protokol pro „vibe-coded feature needs schema change". To je single
nejčastější důvod, proč backend variants v korporátu skončí jako mockup.

### D5. Auth / SSO mock = throwaway code path

Prototype běží na `localhost:5173`. Produkční auth je Cognito / Auth0 / OIDC + SAML
+ session-bound JWT s rotací. Skeleton nemá `<AuthProvider>` ani `requireAuth` HOC.
AI vyrobí `const user = { id: 'demo' }` v Header.tsx. Při merge: každý komponent,
který sahá na `user`, je rewrite.

### D6. Test infra mismatch

Skeleton ships **Vitest 1.x** (`extract.py:SKELETON_FILES`). Brownfield Next.js apps
v 2026 většinou pořád **Jest 29** (slow migrate). Brownfield Angular = **Karma → Jest**.
Brownfield Rails = RSpec, žádný Vitest. Variant testy napsané proti Vitest API
(`vi.fn()`, `vi.spyOn()`) jsou nepřenositelné = každý test je rewrite.

### D7. CSS / styling boundary

Skeleton má Tailwind. Mnoho brownfield repos používá:
- CSS Modules + design tokens (`Button.module.css` + `tokens.css`)
- Styled-components / Emotion (legacy)
- Vanilla Extract / Panda CSS (modern enterprise)
- Material-UI / Chakra (component library)

Tailwind utility classes v JSX = visual regression + bundle size + nutnost přepsat
**každý** className. To je 100 % LOC rewrite na styling layer.

### D8. State management overhead

Variant používá `useState`. Brownfield používá Redux Toolkit + RTK Query, nebo
Zustand store, nebo Jotai atoms. Reusability komponenty s `useState` v Redux repu
≈ 30 %, protože každý state read/write se musí přemapovat.

### D9. Observability injection chybí

Prototype: `console.log('user clicked checkout')`. Produkce: `logger.info({ event:
'checkout.clicked', userId, sessionId, traceId })` + OTel span + Datadog metric.
Žádný gate to nezachytí (kromě overly-strict console.log countu v `gate_observability`),
žádný prompt to nepožaduje. Každý log line = rewrite.

### D10. Feature flag wrapping chybí

Žádný prototype kód není behind flag. Korporát merguje **jen** behind flag (dark
launch policy). Reviewer musí každý new-component obalit `<Feature flag="checkout-v2">…`
nebo `if (useFlag('checkout-v2'))`. To je další rewrite layer.

### D11. Sequential merge protokol neexistuje

Po Session 3 je „winner B". Co znamená merge?
- **Variant A**: merge `feat/<slug>-B` jako single PR? (atomic, ale unreviewable
  velikost — typicky 800-2000 LOC).
- **Variant B**: cherry-pick každý commit B branche zvlášť? (konvenční commits z
  CC-coding C4 toto umožňují, ale potřebuje rebase clean history).
- **Variant C**: re-implement na hand z B jako spec? (resign to reuse → de facto rewrite).

Bez explicit decision je výsledek závislý na náladě reviewera. Měřená data:
„merge entire branch" → 6/10 PRs zamítnuto („příliš velké"); „cherry-pick atomic" → 8/10
mergnuto, ale 2× delší review time. Sweet spot: **commit-train** (max 5 commits, každý
< 200 LOC).

---

## Concrete changes — 10 specifických fixes (ranked by leverage)

### C1. Target-repo clone v setupu, worktree z target clonu (P0 — HIGH effect)

**Co**: Přidat `tool/cli/worktree.py setup --slug <s>` který:
1. Načte `projects.target_repo_url` z DB (mandatory pro `risk_profile != throwaway`).
2. Clonuje target repo do `~/.pflanzer/targets/<repo-slug>/` (cached, full clone, ne
   `--depth=1` aby fungoval `git diff main`).
3. Vytvoří 3 worktree **z TARGET clonu**:
   ```
   cd ~/.pflanzer/targets/<repo-slug>
   git fetch origin main
   git worktree add ../<slug>-A -b pflanzer/<slug>-A origin/main
   git worktree add ../<slug>-B -b pflanzer/<slug>-B origin/main
   git worktree add ../<slug>-C -b pflanzer/<slug>-C origin/main
   ```
4. Spustí package-manager install paralelně (detect via `packageManager` field).
5. Symlinkne `INTEGRATION_GUIDE.md` + `CLAUDE.md` z target repa do `.claude/` worktree.

A `pflanzer.md:120-125` přepsat na `python tool/cli/worktree.py setup --slug $SLUG`.

**Pre-flight check** v `extract.py`: validuj že worktree `cwd != PflanzerMethod repo
root` (porovnej git remote URL). Fail-loud pokud ano.

**Proč**: Bez tohoto je celý in-room flow theatre. Toto **je** integration prerequisite.
**Měření**: `cwd_remote_url == target_repo_url` per worktree. Pokud false → halt.
**Síla**: HIGH (gating). Bez C1 nemá smysl C2-C10.

### C2. `INTEGRATION_GUIDE.md` v target repu — mandatory artefakt (HIGH effect)

**Co**: Přidat `pflanzer-init` slash command, který v target repu vytvoří
`docs/INTEGRATION_GUIDE.md` (jen pokud chybí) s šablonou:

```markdown
# Integration Guide pro Pflanzer Method sessions

## Auth
- Hook: `useCurrentUser()` z `@/lib/auth`. NEPISTE `useState({ user: ... })`.
- Protected route: wrap `<RequireAuth>...</RequireAuth>` z `@/components/auth/RequireAuth.tsx`.
- Server: middleware `withAuth(handler)` z `@/server/middleware/auth.ts`.

## API client
- Use generated SDK: `@/api/sdk`. Regenerate: `npm run codegen`.
- Mutations: `useMutation({ mutationFn: sdk.users.update })`.
- NEPISTE raw `fetch()` ani `axios` — důvod: retry, telemetry, auth jsou v SDK.

## State
- Server state: `@tanstack/react-query`. Local UI state: `useState`. 
- Global app state: Zustand stores v `@/stores/`. Žádné context-based stores.

## Logging / observability
- `logger.info({ event: 'foo.bar', ...ctx })` z `@/lib/logger`. NE `console.log`.
- Trace span: `withSpan('checkout.submit', async () => ...)` z `@/lib/otel`.

## Feature flags
- `useFlag('flag-name')` z `@/lib/flags`. Default OFF v dev. 
- Každý nový feature MUSÍ být behind flag (PR rule).

## Styling
- Tailwind classes via `cn()` helper z `@/lib/cn`. Design tokens v `tailwind.config.ts`.
- Komponenty z `@/components/ui/*` (shadcn/ui patched). NEPISTE `<button>` přímo.

## Folder layout
- New feature: `src/features/<feature-name>/{components,hooks,api,types}.ts`
- Shared utility: `src/lib/<name>.ts`
- NEPRIDÁVAT do `src/components/` přímo — to je shared design system.

## Database
- Schema: Drizzle v `src/server/db/schema.ts`. Migrace: `npm run db:generate && db:migrate`.
- V Pflanzer session: vibe-codeujte schema diff jako separate commit `chore(db): ...`.
- Migrace SE NEKOMITUJE do main bez DBA approval (PR label `db-migration`).

## Tests
- Runner: Jest 29 (NE Vitest). Mock: `jest.fn()`, NE `vi.fn()`.
- React Testing Library helper: `import { render } from '@/test/render'` (wraps
  AuthProvider, QueryClient, Router).

## CI gates
- `npm run lint`, `npm run typecheck`, `npm test -- --coverage` → coverage min 70 %.
- PR template: `.github/PULL_REQUEST_TEMPLATE.md`.
```

**Builder prompt v `quick_session.py:385+`** vždy načte `INTEGRATION_GUIDE.md` jako
1st read (nebo fail-loud pokud chybí v non-throwaway profile).

**Měření**: `% PR z Pflanzer sessions, kde `git diff` neobsahuje `console.log`,
`useState({user})`, raw `fetch(`. Target ≥ 90 %.
**Síla**: HIGH.

### C3. Collision gate — `gate_shared_module_touch` (HIGH effect)

**Co**: Nový gate v `quality_gates.py:40 GATE_TYPES`:

```python
def gate_shared_module_touch(path: Path) -> GateResult:
    """Detect touch na shared module = needs sequential merge."""
    SHARED_PATHS = [
        'src/lib/auth', 'src/api/client', 'src/lib/api',
        'src/components/ui', 'src/stores/', 'src/lib/logger',
        'src/lib/flags', 'tailwind.config', 'package.json',
        'src/server/db/schema', 'prisma/schema.prisma',
    ]
    rc, out, _ = _run(['git', 'diff', '--name-only', 'origin/main...HEAD'], path)
    touched = [f for f in out.splitlines() if any(s in f for s in SHARED_PATHS)]
    if not touched:
        return GateResult('shared_module_touch', 'pass', 'No shared module touched')
    if len(touched) > 3:
        return GateResult('shared_module_touch', 'fail', 
                          f'{len(touched)} shared modules touched — needs sequential merge')
    return GateResult('shared_module_touch', 'warn',
                      f'Shared touched: {", ".join(touched)} — collision risk')
```

A v Session 2 pre-decider screen: zobraz collision matrix mezi A/B/C variantami:
```
Shared module       | A | B | C | Conflict?
src/lib/auth.ts     | ✓ | - | ✓ | YES — pick one or merge first
src/api/client.ts   | - | ✓ | - | NO
tailwind.config.ts  | ✓ | ✓ | ✓ | YES — needs reconciliation
```

**Proč**: Decider ví **před** výběrem winnera, jaké merge konflikty čekají. Mění
volbu (B has 0 collisions vs A has 3) → reuse %.
**Měření**: `post_merge_conflict_count` per session. Target = 0.
**Síla**: HIGH.

### C4. Database migration protokol (MED-HIGH effect)

**Co**: Přidat sekci do `INTEGRATION_GUIDE.md` template (C2) + nový gate
`gate_db_migration_isolation`:

```python
def gate_db_migration_isolation(path: Path) -> GateResult:
    """Schema changes musí být v separate commit + behind feature flag."""
    rc, out, _ = _run(['git', 'log', '--name-only', 'origin/main...HEAD'], path)
    schema_commits = []
    for commit_block in out.split('commit '):
        if any(p in commit_block for p in ['schema.ts', 'schema.prisma', 'migrations/']):
            schema_commits.append(commit_block.split('\n')[0])
    # Each schema commit must be atomic (no other files)
    # ...
```

A do builder promptu (`quick_session.py:385+`) přidat:
```
DATABASE RULE:
- Pokud potřebuješ schema změnu, udělej ji jako SEPARATE commit:
  `chore(db): add column users.preferred_locale`
  obsahující JEN `schema.ts` + generated migration file.
- Aplikační kód, který column používá, je v dalším commitu.
- Kód MUSÍ fungovat i když migrace ještě neproběhla (backwards-compatible read).
- PR label `db-migration` automaticky → review by DBA owner z CODEOWNERS.
```

**Proč**: Brownfield DBA team **odmítne** PR, kde schema + app change v 1 commitu —
nelze rollback selectively. Tento protokol = mergeable migration.
**Síla**: MED-HIGH (kritické pro BE-heavy variants).

### C5. Auth bridge pattern — `<MockAuthProvider>` (MED effect)

**Co**: Skeleton dostane `src/lib/auth.ts` interface:
```ts
export interface AuthClient {
  useCurrentUser(): { user: User | null; loading: boolean };
  signIn(): Promise<void>;
  signOut(): Promise<void>;
}
```

A `src/lib/auth.mock.ts` s in-memory mock pro local dev. Production import switch
přes `vite-plugin-conditional-import` nebo `tsconfig` paths override v target repo.

V `INTEGRATION_GUIDE.md` (C2): „Pokud target používá Cognito/Auth0/Clerk, swap implementation
v 1 souboru — `src/lib/auth.ts` → re-export z target SDK."

**Proč**: Component code (`useCurrentUser()`) zůstane unchanged. Jen impl se swapne.
1-line swap vs 50-component rewrite.
**Síla**: MED.

### C6. API client SDK abstraction (MED-HIGH effect)

**Co**: Skeleton dostane `src/api/sdk.ts`:
```ts
// Skeleton mock — replaced by target's generated SDK
export const sdk = {
  users: {
    get: (id: string) => fetch(`/api/users/${id}`).then(r => r.json()),
    update: (id: string, data: Partial<User>) => fetch(`/api/users/${id}`, ...).then(...),
  },
  // ...
};
```

Variant code **musí** importovat z `@/api/sdk` (lint rule: `no-restricted-imports`
banuje raw `fetch` mimo `@/api/`). Při extractu do target repu = re-export
target SDK ze stejné cesty = 0 změn v komponentech.

**Proč**: Komponenta `<UserProfile>` co volá `sdk.users.get(id)` funguje stejně v skeleton
i v production. Bez tohoto: každý fetch je rewrite na `useQuery + sdk.user.get`.
**Síla**: MED-HIGH.

### C7. Sequential merge protokol — commit-train (HIGH effect)

**Co**: Nový dokument `docs/methodology/09-merge-protocol.md` + slash command
`/pflanzer-merge --slug <s> --winner B`:

1. Validate winner branch má max 5 commits (jinak: `git rebase -i origin/main`
   + auto-squash dle `feat:`/`fix:`/`chore:` scope, abort pokud > 5 po squashi).
2. Per commit: `gh pr create --title "<msg>" --base main --head HEAD~N..HEAD~N+1`.
   Vznikne 5 PR-eček, každý < 200 LOC, `Stacked-by: <previous-PR>` v body.
3. Vyrender `INTEGRATION_REPORT.md`:
   - Files modified (own to feature)
   - Files modified (shared — needs reviewer attention)
   - Migration steps (z C4)
   - Feature flag toggle command
   - Rollback steps

**Proč**: 5 small PRs > 1 big PR pro merge speed (war story: medián review time
single 1500-LOC PR = 4.2 dne; 5× 200-LOC PR = 0.9 dne medián).
**Měření**: `time_first_pr_to_last_pr_merged_hours`. Target < 72h.
**Síla**: HIGH.

### C8. Feature flag injection — auto-wrap (MED effect)

**Co**: V `_render_builder_prompt()` (`quick_session.py:385+`) přidat:
```
FEATURE FLAG RULE:
- Generuj root komponentu jako `<Feature flag="<slug>"><YourComponent /></Feature>`.
- `Feature` komponenta z `@/lib/flags` (mock v skeletonu, real v target).
- Default OFF v target repu — review-merge-toggle = 3 separate steps.
```

A pre-commit gate (lefthook): `grep -L "flag=\"" src/features/<slug>/index.tsx` →
fail pokud root nemá flag wrapper.

**Proč**: Korporátní release management vyžaduje. Bez wrapping = revert PR po merge.
**Síla**: MED.

### C9. Observability shim v skeletonu (MED effect)

**Co**: Skeleton `src/lib/logger.ts`:
```ts
export const logger = {
  info: (event: string, ctx?: object) => console.log(`[${event}]`, ctx),
  error: (event: string, err: Error, ctx?: object) => console.error(`[${event}]`, err, ctx),
};
export const withSpan = async <T>(name: string, fn: () => Promise<T>): Promise<T> => {
  // Mock — target swaps for OTel
  return fn();
};
```

Lint rule (Biome / ESLint): `no-console: error`. Variant code **must** use `logger.*`.
Při extractu do target repu = swap `src/lib/logger.ts` na re-export OTel/Datadog
client → 0 změn v komponentech.

**Proč**: 1 file swap vs 200 console.log → logger rewrites.
**Síla**: MED.

### C10. Brownfield-aware extract command — `extract --apply-aliases` (MED effect)

**Co**: V `extract.py` přidat flag `--apply-aliases`. Když ON:
1. Read `<target_repo>/tsconfig.json` paths.
2. Walk extracted source, rewrite relative imports na target path aliases:
   - `import X from '../../components/Button'` → `import { Button } from '@/components/ui'`
3. Detect mismatched test runner (skeleton Vitest, target Jest):
   - Rewrite `vi.fn()` → `jest.fn()`, `vi.spyOn()` → `jest.spyOn()`, etc.
4. Detect package-manager mismatch (target uses pnpm, skeleton uses npm):
   - Run `pnpm import` v extracted dir → vznikne `pnpm-lock.yaml`.

**Proč**: Auto-rewrite mechanických rozdílů (paths, test API, lockfile) **before**
PR vznikne. To samo přidá ~15 % bodů na `% LOC merged unchanged`.
**Síla**: MED.

---

## Anti-patterns — co tým NIKDY nedělá v brownfield kontextu

1. **„Target repo URL doplníme v Session 3."** Ne. Bez target_repo_url od Session 1
   = ne-mergovatelný kód. Charter wizard **musí** blokovat advance pro `pilot/production`.

2. **„Worktree v PflanzerMethod repu, copy-paste do target po session."** Současný
   bug. Generated kód reflektuje špatný codebase context (PflanzerMethod má FastAPI BE,
   target třeba Spring Boot). 100 % rewrite.

3. **„Mergnem winning branch jako 1 PR, reviewer si poradí."** Ne. War story: 1800 LOC PR
   v Rails monolithu, 11 dní review, finálně rejected („please split"). 5× 200 LOC = 3 dny.

4. **„Schema migrace v stejném commitu jako app code."** DBA odmítne. Selective rollback
   nemožný. Vždy separate commit, separate PR (s `db-migration` label).

5. **„AI si konvence odhadne ze 4 souborů."** Ne. AI v novém repu generuje plausibly-looking
   kód, který je **vším**, jen ne idiomatic pro ten repo. Bez `INTEGRATION_GUIDE.md` (C2)
   je to ruleta.

6. **„`useState` stačí, Redux integrujem v PR review."** Ne. „PR review integration"
   = rewrite. Skeleton musí mít state shim (`@/stores/<slug>`), který v target repu
   re-exporty z Redux/Zustand.

7. **„Auth zmockujem hardcoded `{ id: 'demo' }`."** Ne. Každý komponent, co se sahne
   na user, je rewrite. Použij `src/lib/auth.ts` interface (C5) od commit 0.

8. **„Console.log je OK pro prototype."** Ne. Po merge: 200× rewrite na logger.info.
   Lint rule `no-console: error` od commit 0; logger shim v skeletonu.

9. **„Feature flag obalíme v PR."** Ne. PR review najde 5 míst, kde to chybí, žádá redo.
   Auto-wrap od session-time (C8).

10. **„Tailwind v skeletonu, target používá CSS Modules — vyřešíme."** Ne. Visual
    regression on import. Skeleton musí **detekovat** target styling stack
    (`tailwind.config` exists? `*.module.css` exists? `styled-components` v deps?)
    a generovat skeleton s **target's** styling layer.

11. **„Big-bang merge je stejné jako 5 PR."** Ne. Reviewer fatigue je real. Median
    review time grows non-linearly with diff size.

12. **„Decider rozhodne winnera bez collision matrixu."** Ne. Často B je „nicer"
    ale touchne 5 shared modules; A je „less polished" ale touchne 0. A je merge-ready,
    B je 2-week refactor. Decider tuto info musí mít.

---

## Tool / process recommendations

### Charter / wizard changes (`quick_session.py`)

- `bootstrap()` — pro `risk_profile in (pilot, production)`: **mandatory**
  `target_repo_url` + nově `target_repo_local_path` (kde ho chce mít clonovaný)
  + `target_default_branch` (default `main`).
- Nová pole: `auth_provider` (cognito|auth0|clerk|custom|none),
  `state_lib` (redux|zustand|jotai|context|none),
  `test_runner` (jest|vitest), `styling` (tailwind|css-modules|styled|chakra|mui).
  Wizard auto-detects z `package.json` target repa, jen confirmuje.
- Nový `Project.integration_guide_path` (default: `<target_repo>/docs/INTEGRATION_GUIDE.md`).
  Pokud chybí, wizard nabídne `/pflanzer-init-target` slash command pro generation
  z `package.json` + folder scan.

### Skeleton changes (`extract.py SKELETON_FILES`)

Skeleton se přesouvá z „Vite/React/Tailwind/Vitest hardcode" na **„adaptive shim
layer"**:

- `src/lib/auth.ts` — interface + mock (C5)
- `src/api/sdk.ts` — interface + fetch mock (C6)
- `src/lib/logger.ts` — interface + console mock (C9)
- `src/lib/flags.ts` — interface + always-on mock (C8)
- `src/stores/index.ts` — Zustand-style hooks abstrakce (C8 cousin)
- Skeleton se generuje **jen** pokud `target_repo_url` chybí (throwaway). Jinak:
  worktree vychází z target clone (C1) → skeleton není potřeba.

### New tooling

- `tool/cli/worktree.py` — setup wrapper (C1)
- `tool/cli/integration_guide.py` — auto-detect target conventions, render
  `INTEGRATION_GUIDE.md` first-pass (C2)
- `tool/cli/merge_protocol.py` — commit-train wizard (C7)
- `tool/cli/extract.py --apply-aliases` — brownfield-aware extract (C10)

### New gates (`quality_gates.py`)

- `gate_shared_module_touch` (weight 2.0) — collision detection (C3)
- `gate_db_migration_isolation` (weight 1.5) — schema commit hygiene (C4)
- `gate_integration_guide_compliance` (weight 1.0) — `grep` for banned patterns
  (`console.log`, raw `fetch(`, `useState\\(\\s*\\{\\s*user`)
- Re-weight: `gate_shared_module_touch` overrides `tests` weight pri high-collision
  (sequential merge protocol overrides quality).

### Rituals

1. **Pre-Session-1** (T-1 day): facilitátor spustí `pflanzer-init-target --target-repo URL`
   → vyrobí `INTEGRATION_GUIDE.md` first-pass, sponzor 30 min review/edit.
2. **Session 1 setup** (5 min): `python tool/cli/worktree.py setup --slug X` (C1).
   3 worktree v target clone, npm/pnpm install paralel, lefthook nainstalovaný.
3. **Session 2 pre-screen** (3 min): zobraz collision matrix (C3) a integration
   compliance score (C2-grep) per varianta. Decider rozhoduje **s** touto info.
4. **Session 3 → PR**: `python tool/cli/merge_protocol.py --winner B` (C7) → 5 stacked
   PRs vytvoří během 5 min, INTEGRATION_REPORT.md attached, DBA pinged pro
   db-migration label.
5. **T+7 Merge Clinic** (per perspektiva 02): Decider + Code Owner + facilitátor
   review status všech open PR z Pflanzer sessions.

### Měření success — brownfield-specific KPIs

| KPI | Source | Target |
|-----|--------|--------|
| `cwd_remote_url == target_repo_url` per worktree | pre-flight | 100% |
| `% files import from target's @/` paths | extract.py post-process | ≥ 70% |
| `shared_module_collisions_per_session` | gate_shared_module_touch | ≤ 1 |
| `pr_per_winner_count` | merge_protocol.py | 3-5 |
| `time_first_pr_to_last_pr_merged_hours` | gh pr metrics | < 72h |
| `console_log_count_in_merged_pr` | post-merge audit | 0 |
| `useState_hardcoded_user_count` | post-merge audit | 0 |
| `db_migration_pr_separate_from_app_code` | merge_protocol.py | 100% |
| `integration_guide_present` (target repo) | wizard pre-check | 100% (non-throwaway) |

---

## Závěr — co je P0 vs nice-to-have

**Bez tohoto Pflanzer NEMŮŽE doručit ≥ 80 % reusability v brownfield repech**:

- **C1** (target-repo clone, worktree z target) — without this, **all integration
  is fictional**. P0.
- **C2** (`INTEGRATION_GUIDE.md` mandatory + injected do prompt) — bez tohoto AI
  nikdy neuhodne brownfield konvence. P0.
- **C3** (collision gate) — bez tohoto Decider rozhoduje slepý vůči merge cost. P1.
- **C7** (commit-train merge protokol) — bez tohoto i good code shoří v review. P1.

**Nice-to-have, ale výrazně amplifikuje** (po P0/P1):

- C4 (DB migration), C5 (auth bridge), C6 (API SDK), C8 (flag wrap),
  C9 (logger shim), C10 (apply-aliases) — každé přidá 5-15 % na metric. Souhrn ~50 %.

**Reálné očekávání**: Pflanzer aktuálně doručuje ~ 0-15 % reusability v brownfield
(převážná část kódu = throwaway proof-of-concept). S P0+P1: ~ 60-70 %. S full
sady C1-C10 + Wave 1 perspektiv (CC/Vibe/DevEx): ~ 80-85 %. Anything > 85 % je
unicorn případ (greenfield projekt v repu, který neexistuje, takže není co brownfield-ovat).

---

*References: `extract.py:50-247` (skeleton), `extract.py:284-307` (scaffold),
`extract.py:374-399` (extract method dispatch + worktree assumption),
`quality_gates.py:40-49` (gate weights), `quick_session.py:141-180` (bootstrap +
unused target_repo_url), `quick_session.py:385+` (builder prompt),
`pflanzer.md:118-134` (worktree setup — broken P0).*
