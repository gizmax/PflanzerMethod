# DevEx perspective — co dělat aby skeleton + worktree workflow nezvyšoval merge friction

> Autor: Staff DevEx / Eng Productivity (12+ y, monorepo lead 50–500 eng)
> Branch: `research/code-reusability` · Wave 1

## TL;DR (3 největší páky)

1. **Pinout všechno na lockfile + Node 20.11 LTS, jeden formatter (Biome), jedny pre-commit hooks (lefthook).** Tři paralelní worktree teď generují tři různá ESLint/Prettier nastavení a tři různé peer-dep grafy. Merge konflikt na `package.json` zabíjí 80 % reusability dřív, než se tým pohne.
2. **Hooky musí běžet PŘED commitem v každém worktree** — `quality_gates.py` jako post-mortem je pozdě. Když AI commitne broken kód do `feat/<slug>-A`, je to v gitu navždy a Decider to čte v Session 2.
3. **Skeleton musí mít `@/` path alias + `tsconfig.base.json` extend pattern**, jinak po extractu do brownfield monorepa selže každý import. Tohle je nejčastější důvod proč „prototype kód" musí být přepsán: liší se import paths, ne logika.

## Diagnose — co Pflanzer flow dělá špatně z DevEx pohledu

`extract.py:SKELETON_FILES` (řádky 50–247) je solidní startér, ale má `^` ranges v `package.json` → tři worktree volané v různý čas dostanou tři různé minor verze React/Vite. Po 2 týdnech `npm install` v hlavním repu vrátí jiný `vite@5.4.x` než ten, na kterém Decider viděl winning variant.

`quality_gates.py:40` má pořadí `lint → types → tests → security → a11y → build → observability`. Build je až šestý. V CI běhu trvá npm install + build 60–90 s. Když build selže (typo v JSX, missing default export), tým čeká na lint+types+tests timeout (možná 4 min total) jen aby se dozvěděl, že nic nezbuildí. **Fail fast = build first, pak types, pak zbytek.**

`quality_gates.py:99` skipne lint pokud chybí `node_modules`. To znamená že CI běhne na čerstvém runneru nikdy nedoběhne `lint` automaticky — vždy "skipped". Chybí `npm ci` step before gates.

Skeleton nemá `.editorconfig`, `.nvmrc`, `engines` field v `package.json`. Tři vývojáři v in-room session mají tři různé Node verze → tři různé `package-lock.json`. `git diff` je pak 200 řádků lockfile noise místo 20 řádků product kódu.

`gh pr create` template chybí. PR z handoffu je textový dump — reviewer netuší, který gate failed a kde. Tohle je single největší blocker pro „PR merged within 7 days" metriku.

Worktree pattern (`git worktree add ../proto-<slug>-<variant>`) je v korporátu **nový pro 70 % týmu**. Vidím to v každé migraci. Lidi pak commitují do špatného worktree, push odmítne, panika. Treba to wraping + safety net.

## Concrete changes

### 1. Switch ESLint+Prettier → **Biome 1.9.x** (med-high effect)
**Co:** V `extract.py:SKELETON_FILES` smaž `.eslintrc.cjs`, `.prettierrc` a všech 5 `@typescript-eslint/*` + `eslint-plugin-*` deps. Přidej:
```json
"@biomejs/biome": "1.9.4"
```
A `biome.json`:
```json
{ "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true },
  "linter": { "enabled": true, "rules": { "recommended": true, "a11y": { "recommended": true } } },
  "formatter": { "enabled": true, "indentStyle": "space", "indentWidth": 2, "lineWidth": 100 },
  "javascript": { "formatter": { "quoteStyle": "single", "trailingCommas": "all", "semicolons": "always" } } }
```
**Proč:** Jeden tool, jeden config, ~25× rychlejší než ESLint+Prettier (lint v <500 ms i pro 50k LOC), built-in a11y rules nahradí gate_a11y warm-start. V `package.json:scripts` zmenšíš z 2 scriptů na 1: `"check": "biome check --write ."`.
**Měření:** `quality_gates.py` lint gate čas < 5 s; `npm install` size shrink ~80 MB → ~12 MB. Síla: **high** (každá session ušetří 3–5 min × 3 worktree).

### 2. Pinout versions + Node 20.11 LTS (high effect, low cost)
**Co:** V `SKELETON_FILES["package.json"]` smaž všechny `^`, přidej:
```json
"engines": { "node": "20.11.1", "npm": "10.2.4" },
"packageManager": "npm@10.2.4"
```
A nový soubor `.nvmrc`:
```
20.11.1
```
A `SKELETON_FILES[".npmrc"]`:
```
engine-strict=true
save-exact=true
```
**Proč:** Tři worktree dostanou bit-for-bit stejné `node_modules`. Gate score je porovnatelný. `engine-strict` zabrání nešťastníkovi s Node 18 install pokračovat.
**Měření:** `git diff package-lock.json` mezi worktree A/B/C = 0 lines (jen entry-point app code se liší). Síla: **high**.

### 3. Pre-commit gates přes **lefthook** (high effect)
**Co:** V `SKELETON_FILES` přidej `lefthook.yml`:
```yaml
pre-commit:
  parallel: true
  commands:
    biome:
      glob: "*.{ts,tsx,js,jsx,json,css}"
      run: npx biome check --write {staged_files} && git add {staged_files}
    types:
      glob: "*.{ts,tsx}"
      run: npx tsc --noEmit
    secrets:
      run: npx --yes secretlint "**/*"
commit-msg:
  commands:
    conventional:
      run: npx --yes @commitlint/cli --extends @commitlint/config-conventional --edit {1}
```
A přidej `"lefthook": "1.7.18"` + `"prepare": "lefthook install"` script.
**Proč:** AI v Codex CLI/CC nemůže commitnout broken kód. Když Session 1 končí 3 commity per worktree, všechny už mají passing types + lint + 0 secrets. `quality_gates.py` v Session 3 pak má jen ověřit, ne diagnostikovat. **Lefthook > Husky** — žádný shell wrapper, paralelní execution, Go binary (rychlejší startup než Husky).
**Měření:** `git log --grep "wip\|fix lint\|type fix" --since session_start` count = 0. Síla: **high**.

### 4. Reorder gates: **build → types → lint → tests → security → a11y → observability** (med effect, zero cost)
**Co:** V `quality_gates.py:40` změnit:
```python
GATE_TYPES = ("build", "types", "lint", "tests", "security", "a11y", "observability")
```
A v `run_all` (`quality_gates.py:374`) přidat early-exit option:
```python
for gate in GATE_TYPES:
    r = GATE_RUNNERS[gate](local_path)
    results.append(r)
    if gate in ("build", "types") and r.status == "fail" and fail_fast:
        # Zbytek označit skipped — nemá smysl běžet a11y na nebuildících app
        for g in GATE_TYPES[GATE_TYPES.index(gate)+1:]:
            results.append(GateResult(g, "skipped", f"Skipped — {gate} failed"))
        break
```
**Proč:** Build fail v 30 s, ne v 4 min. V `pflanzer-session-3` triage tým nečeká.
**Měření:** Median `time_to_gate_verdict` per variant (target < 90 s pro fail, < 4 min pro pass). Síla: **med**.

### 5. Auto-install + cache `node_modules` v gate runneru (med effect)
**Co:** `quality_gates.py:99` aktuálně skipne lint pokud chybí `node_modules`. Přidej `_ensure_install()`:
```python
def _ensure_install(path: Path) -> bool:
    if (path / "node_modules").exists():
        return True
    if not (path / "package-lock.json").exists():
        return False
    rc, _, _ = _run(["npm", "ci", "--prefer-offline", "--no-audit"], path, timeout=300)
    return rc == 0
```
Volat na začátku `run_all`. Cache přes `~/.npm` (npm dělá automaticky).
**Proč:** Session 3 v in-room runu nikdy ručně neinstalluje. Bez tohoto je 60 % gates `skipped`. Síla: **med-high**.

### 6. `tsconfig.json` rozdělit + path aliases (high effect pro brownfield)
**Co:** V `SKELETON_FILES` přidej `tsconfig.base.json`:
```json
{ "compilerOptions": {
    "target": "ES2022", "module": "ESNext", "moduleResolution": "bundler",
    "strict": true, "noUncheckedIndexedAccess": true, "exactOptionalPropertyTypes": true,
    "baseUrl": ".", "paths": { "@/*": ["./src/*"], "@test/*": ["./src/test/*"] } } }
```
A `tsconfig.json`:
```json
{ "extends": "./tsconfig.base.json",
  "compilerOptions": { "jsx": "react-jsx", "lib": ["ES2022", "DOM"], "noEmit": true, "types": ["vitest/globals"] },
  "include": ["src"] }
```
A `vite.config.ts` rozšířit:
```ts
resolve: { alias: { '@': path.resolve(__dirname, './src') } }
```
**Proč:** Brownfield monorepa skoro vždy mají `@/` alias (Next.js default, většina shadcn/ui setupů). Když AI generuje `import Button from '../../../components/Button'`, brownfield import přepíše na `@/components/Button` = každý import je rewrite = `rewrite_loc_ratio` skočí 3×. **Toto je jediná největší páka pro "≥ 80 % LOC unchanged".** `noUncheckedIndexedAccess` přidá real type safety, kterou brownfield už má. Síla: **high**.

### 7. Přidej **`ts-reset`** do skeletonu (low cost, med effect)
**Co:** V `package.json` deps: `"@total-typescript/ts-reset": "0.6.1"`. Vytvoř `src/reset.d.ts`:
```ts
import '@total-typescript/ts-reset';
```
**Proč:** Vrátí `JSON.parse() → unknown` (ne `any`), `Array.filter(Boolean)` removes nullables. AI bez tohoto generuje `any`-laden kód → fail v brownfield strict repu. Síla: **med**.

### 8. **`coverage` gate v `quality_gates.py`** (med effect)
**Co:** Přidat 8th gate `coverage` (weight 1.0) běžící `npx vitest run --coverage --reporter=json`, parsovat statements ≥ 60 % = pass, 30-60 % = warn, < 30 % = fail. Coverage tool: `@vitest/coverage-v8` (přidat do deps).
**Proč:** Aktuální `tests` gate kontroluje jen že testy projdou — ne že existují. Variant s 1 trivial testem dostane stejný score jako variant s 40 testy. Pro 80 % reusability target potřebujeme min. coverage 60 %, jinak v brownfieldu hned padne při refactoru. Síla: **med**.

### 9. **PR template + gate badges v `gh pr create`** (high effect pro merge speed)
**Co:** Nový soubor `tool/cli/handoff_pr.py` který po `quality_gates.run` vygeneruje:
```markdown
## Pflanzer handoff — {slug} variant {winner}

| Gate | Status | Metric |
|------|--------|--------|
| build | ✅ pass | 142 KB |
| types | ✅ pass | 0 errors |
| tests | ✅ pass | 47 cases, 78% coverage |
...

**Gate score: 87/100 (target 80) → production-ready**

### Files most likely needing review
- `src/components/CheckoutForm.tsx` (78 LOC, complex state)
...

### Files safe to merge as-is
- `src/lib/validation.ts` (100% coverage, pure)
...
```
A automaticky `gh pr create --body-file <path>`.
**Proč:** Reviewer vidí gate evidence v PR description, ne musí klonovat a běžet. `handoff_pr_merged_within_7d` skočí o 30–50 % v zkušenosti z 3 podobných projektech. Síla: **high**.

### 10. **MSW + render helper v skeletonu** (med effect)
**Co:** `SKELETON_FILES["src/test/render.tsx"]`:
```tsx
import { render as rtlRender, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
// import { Providers } from '../providers';  // Decommentnout až existuje
export const render = (ui: ReactElement, opts?: RenderOptions) =>
  rtlRender(ui, { /* wrapper: Providers, */ ...opts });
export * from '@testing-library/react';
```
A `src/test/server.ts` s msw setup. Přidat `"msw": "2.4.x"` do deps.
**Proč:** AI píše ad-hoc test setup v každém variantu. Když brownfield má vlastní `render` wrapper s Theme/Router/Query providers, každý test v handoff je rewrite. Sdílený helper = drop-in replacement. Síla: **med**.

## Anti-patterns (war stories)

- **„Zapneme strict mode později."** Nikdy. Po 200 LOC máš 80 type errors a tým rezignuje. Strict OD COMMIT 0. (Skeleton to už má — chraňte to.)
- **Husky shell scripts.** Husky 9 stale install issues, slow on Windows worktree, fragile. Lefthook = 1 binary, parallel, fast.
- **`npm install` v in-room session.** Pomalé, neopakovatelné, audit warnings panic team. Vždy `npm ci`. Vždy committed lockfile. Cache `~/.npm` napříč worktree.
- **Tři ESLint configy v 3 worktree.** Garbage. Jeden centralizovaný (lépe Biome — jeden tool).
- **Worktree v `~/Desktop/proto-X/`.** Lidi tam pak nikdy nepushnou. Vždy v `../proto-<slug>-<variant>` sibling parent (viz README — to je správně, ale dokumentujte to v `pflanzer.md` JEŠTĚ explicitněji s `git worktree list` po setupu).
- **`gh pr create` bez body.** Reviewer žádá kontext. Auto-generovaný gate report = 80 % objections vyřešeno preemptivně.
- **Tailwind vs CSS modules debata v každém variant.** Bake Tailwind 3.4 do skeletonu (de-facto standard 2026, 95 % korporátních FE). Eliminuje 1 sporné rozhodnutí v Session 1.
- **Console.log gate jako fail.** Současná `gate_observability` (`quality_gates.py:298`) failuje na > 3 console.log. To je moc tvrdé v prototype fázi. Downgrade na warn always; přesun do **lint rule** (`no-console`) ať to chytne pre-commit hook, ne post-mortem gate.

## Tool / process recommendations

| Concern | Tool | Version | Place |
|--------|------|---------|-------|
| Lint + format | **Biome** | 1.9.4 | `biome.json` v skeletonu |
| Pre-commit | **lefthook** | 1.7.18 | `lefthook.yml` v skeletonu |
| Commit msg | **commitlint** + conventional | 19.x | lefthook commit-msg |
| Secret scan | **secretlint** | 9.x | lefthook + gate |
| Coverage | **@vitest/coverage-v8** | match vitest | dev dep |
| Mock service | **msw** | 2.4.x | `src/test/server.ts` |
| Type safety helper | **@total-typescript/ts-reset** | 0.6.1 | `src/reset.d.ts` |
| Path alias | tsconfig + vite alias | — | `tsconfig.base.json` + `vite.config.ts` |
| Node version pin | `.nvmrc` + `engines` + `engine-strict` | 20.11.1 | repo root |
| Editor consistency | `.editorconfig` | — | repo root |
| Worktree wrapper | `tool/cli/worktree.py` | new | `python tool/cli/worktree.py add A` → safer git worktree + npm ci |

**Rituals:**

1. **Před každou Session 1**: `python tool/cli/worktree.py setup <slug>` vytvoří 3 worktrees, spustí `npm ci` paralelně (3× `&`), instaluje lefthook. Tým otevře 3 Cursor/CC instance na 3 paths. Žádné ruční `git worktree add` confusion.
2. **Session 2 brief**: pretty-print `quality-A.md` + `quality-B.md` + `quality-C.md` side-by-side. Decider vidí gate score před tím, než řekne winner.
3. **Po Session 3**: `python tool/cli/handoff_pr.py --slug <s> --winner B` → auto PR s gate badges + per-file confidence list.
4. **Brownfield bridge**: nový flag `extract.py --target-repo /path/to/monorepo --apply-aliases` zkopíruje winning `src/` do `<target>/apps/<slug>/`, přepíše importy podle target `tsconfig.json` paths. Toto je práce na 1 sprint, ale eliminuje největší source of `rewrite_loc_ratio` bloat.

**Měřit success:** track `lockfile_diff_lines_between_worktrees` (target: 0), `gate_runtime_p50_seconds` (target: <120 s), `commits_with_lint_fix_keyword` (target: 0), `pr_first_review_to_merge_hours` (target: <72 h). Tyhle 4 metriky odpovědí jestli DevEx změny zvedly `rewrite_loc_ratio` pod 20 % = 80 % reusability cíl.
