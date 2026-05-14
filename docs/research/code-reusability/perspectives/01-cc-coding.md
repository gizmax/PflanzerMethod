# Perspective 01 — CC-coding-expert (Senior eng / AI-pair-programming)

> Wave 1 · 2026-05-14 · branch `research/code-reusability`
> Author persona: 10+ let production eng, 2+ roky daily Claude Code / Codex CLI, ~100 PRs kde AI psala většinu kódu.

## TL;DR — 3 největší páky pro 80 % reusability

1. **Skeleton musí být klon target repa, ne čistý Vite scaffold.** Současný `SKELETON_FILES` v `extract.py:50` generuje generický Vite + React, který má 0 % shody s tím, kam kód poputuje. Páka: nahradit „skeleton" za `git clone --depth=1 --filter=blob:none $TARGET_REPO_URL` + checkpoint commit. CC pak píše do existující struktury, používá existující komponenty, dodržuje existující ESLint config. To je rozdíl 30 % → 85 % reusability sám o sobě.
2. **Builder prompt v `_render_builder_prompt()` neříká CC, kde najít „existing patterns".** Krok 1 řekne „Read existing src/ structure", ale neukazuje **co konkrétně** přečíst (CLAUDE.md, ADR, `src/components/ui/*`, design tokens). CC pak vyhledává nahodile a ujede mu 30-40 % token rozpočtu na exploration, který už mohl být explicitní. Páka: prompt template emituje **explicit read list** odvozený z `target_repo_url` (10-15 souborů, max 50 k tokenů cache hit).
3. **Quality gates měří „funguje to", ne „integruje se to".** `gate_lint`, `gate_types`, `gate_tests` všechny běží proti vygenerovanému Vite skeletonu — ne proti merge target. Chybí gate „diff-against-target" (kolik LOC z `feat/<slug>-<variant>` bude konfliktovat při `git merge main` nebo bude duplikovat existující funkci). To je proxy pro reusability metric a teprve to ji odemkne.

## Diagnose — kde současný flow leak-uje reusability

| Místo | Problém | Důsledek |
|---|---|---|
| `extract.py:50-247` `SKELETON_FILES` | Generický Vite scaffold; není-li `target_repo_url`, kód se generuje do prázdna | Tým to po session přepisuje na míru target stacku — typický rewrite ratio 60-70 % |
| `extract.py:376-378` `builder in ("claude-code", "codex-cli")` → `method = "in_repo_branch"` | Předpokládá worktree existuje; ale `pflanzer.md:121-125` vytváří worktree ze **současného repa metody**, ne z target repa | CC kóduje v PflanzerMethod repu místo v target produkčním repu = 0 % reuse |
| `quick_session.py:395-425` CC prompt | „Read existing src/ structure, tsconfig.json, .eslintrc, design tokens" — bez konkrétních cest | CC dělá `Glob` + `Grep` rampage, spotřebuje 20-30 k tokenů na exploration | 
| `quality_gates.py:41-49` GATE_WEIGHTS | `tests=2.0`, `security=2.0`, ale `lint=1.0` a chybí `integration_diff` | Variant může mít 90 score a přitom neimportuje žádnou existující komponentu |
| `quality_gates.py:95-119` `gate_lint` | Spouští `npm run lint` z extracted dir s vlastním `.eslintrc.cjs` (řádek 122 v extract.py) | Lint passes proti vlastním pravidlům, ne target repo pravidlům — false positive na „mergeable" |
| `quality_gates.py:142-159` `gate_tests` | Vyžaduje passing testy; `App.test.tsx` v skeletonu testuje jen samotný skeleton | „Tests pass" znamená nic relevantního pro merge |
| Chybí gate | Žádný `gate_imports_existing_modules`, žádný `gate_diff_loc_vs_target` | Metric `% LOC merged without modification` nelze měřit ani aproximovat |
| Worktree v `pflanzer.md:121-125` | `git worktree add ../proto-${SLUG}-A -b feat/${SLUG}-A` — z PflanzerMethod repa | Branch v špatném repu; CC nemá kontext target codebase |
| Commit message convention | Prompt říká `feat(<slug>): variant X` ale neříká scope/Conventional Commits | PR review vyžaduje rewrite history před merge |

## Concrete changes — 8 specific fixes (ranked by effect)

### C1. Skeleton = real target repo clone (HIGH effect)
**Co**: V `extract.py:284 _scaffold_skeleton()` před fallback na `SKELETON_FILES` zkus `git clone --depth=1 --filter=blob:none $target_repo_url $dest && cd $dest && git checkout -b feat/$slug-$variant`. Pouze pokud `target_repo_url` chybí (pure throwaway), spadni na současný generic skeleton.
**Proč**: CC pak vidí real `package.json`, real `eslint.config.js`, real `tsconfig.json`, real komponenty. Generuje kód, který importuje `@/components/ui/Button` místo `<button>`. Reusability skok ~30 % → ~75 %.
**Měření**: Nový gate `gate_uses_existing_modules` (viz C5) — počet importů z `@/` nebo relative paths mimo `src/<variant_slug>/`. Target ≥ 5.
**Síla**: HIGH

### C2. Worktree v target repu, ne v PflanzerMethod repu (HIGH effect)
**Co**: V `.claude/commands/pflanzer.md:121-125` change setup block na:
```bash
SLUG=<slug>
TARGET_REPO=$(python3 tool/cli/quick_session.py target-repo --slug $SLUG)
cd $TARGET_REPO
git worktree add ../proto-${SLUG}-A -b feat/${SLUG}-A
```
A přidat sub-command `target-repo` do `quick_session.py main()` který vrátí `projects.target_repo_url` resp. lokální cestu.
**Proč**: CC kóduje uvnitř target repa = automatically respektuje jeho conventions. Bez tohoto je celý ostatní flow placebo.
**Měření**: Nový pre-flight check v `extract.py` — `dest.parent.name == basename(target_repo_url)`. Pokud false → fail.
**Síla**: HIGH (gating fix pro C1)

### C3. Prompt template emituje explicit read list (HIGH effect)
**Co**: V `quick_session.py:395-425` (claude-code prompt) nahradit krok 1 za auto-vygenerovaný read list:
```
1. PŘED PSANÍM přečti tyto soubory (one tool call, prompt cache hit):
   - CLAUDE.md (project-level conventions)
   - .cursor/rules/*.md nebo .claude/rules/*.md (pokud existují)
   - package.json, tsconfig.json, eslint.config.js
   - src/components/ui/index.ts (design system entry)
   - src/lib/api/client.ts (API client convention)
   - 2-3 nejnovější PR diffs (`gh pr list --limit 3 --json files`)
   - docs/decisions/ (ADR pokud existuje)
```
Generovat dynamicky: `extract.py` před promptem detekuje které z těchto cest reálně existují v target repu a vloží jen existující.
**Proč**: CC ušetří 20-30 k tokenů exploration, dostane stable prompt cache hit (Anthropic prompt caching), a kóduje s real conventions od prvního tokenu.
**Měření**: Sleduj `cache_read_input_tokens` v session telemetrii (CC ji loguje). Target ≥ 60 % všech input tokens.
**Síla**: HIGH

### C4. Strict commit hygiene v promptu (MED effect)
**Co**: V `_render_builder_prompt()` `quick_session.py:418` rozšířit krok 5:
```
5. Commit conventions:
   - Conventional Commits: `feat(<scope>): <imperative summary>` 
   - Atomic: 1 commit = 1 logical change. Multiple commits OK.
   - Body: WHY, ne WHAT (diff to mluví sám).
   - Trailers: `Variant: <X>`, `Pflanzer-session: <slug>`.
   - Žádný `WIP`, `fix typo`, `address comments` — squash předem.
```
**Proč**: PR review je gatekeeper merge. Atomic conventional commits umožní `git rebase -i` cherry-pick winning subsetu, místo merge všeho-nebo-ničeho.
**Měření**: Post-handoff metric `commit_atomicity` = avg LOC per commit (target ≤ 150). Logovat v `method-metrics.json`.
**Síla**: MED

### C5. Nový gate: `integration_diff` (HIGH effect)
**Co**: Přidat 8. gate do `quality_gates.py:40` `GATE_TYPES`:
```python
def gate_integration_diff(path: Path) -> GateResult:
    """Měří, kolik LOC se reálně merguje vs duplikuje."""
    # 1. git diff --stat main...HEAD → total LOC changed
    # 2. Detect duplicates: jsinspect / jscpd proti main branch
    # 3. Detect orphan files (nová komponenta vs reuse z @/components/ui)
    # 4. Score = 1 - (duplicate_loc + orphan_loc) / total_loc
```
Použij `jscpd` (npm install --no-save) nebo simple AST hash. Weight = **2.5** (highest, primary metric).
**Proč**: Toto **je** proxy pro autoresearch metric (% LOC merged without modification). Bez tohoto gates měří „proto funguje", ne „proto se merguje".
**Měření**: Score sám o sobě je metric. Korelovat s `handoff_pr_merged_within_7d` v `method-metrics.json` po 5+ projektech.
**Síla**: HIGH (přímo gating pro autoresearch metric)

### C6. ESLint config inheritance, ne override (MED effect)
**Co**: V `extract.py:122-136` `.eslintrc.cjs` template změnit na:
```js
module.exports = {
  root: false,  // Inherit z parent repo
  extends: ['../../.eslintrc.cjs'],  // Pokud target_repo_url byl použit
  // jen variant-specific overrides
};
```
A vůbec negenerovat `.eslintrc.cjs` pokud root `eslint.config.js` existuje (nový flat config).
**Proč**: Lint passing v skeletonu ≠ lint passing v target. Inheritance = single source of truth.
**Měření**: `gate_lint` re-run po merge — pokud se počet warnings nezmění (Δ ≤ 5 %), inheritance funguje.
**Síla**: MED

### C7. „Read before write" enforcement v prompt (MED effect)
**Co**: V CC promptu `quick_session.py:407-424` přidat explicit guardrail:
```
PRAVIDLO: Před každým novým souborem MUSÍŠ:
1. `Glob` na podobné existující soubory (`src/components/**/*.tsx`).
2. `Read` minimálně 1 podobný soubor.
3. Vysvětlit (1 věta v commit body): „následuje pattern X z `src/...`".

Pokud obcházíš existující komponentu, MUSÍŠ to commitnout jako 
samostatný commit `refactor(<scope>): introduce <new>` s rationale.
```
**Proč**: CC default „píše nový kód" místo „rozšiřuje existující". Tento prompt invertuje default.
**Měření**: Manual code review post-session — počet new files vs modified files. Target ratio ≤ 0.5.
**Síla**: MED

### C8. Gate weights re-balance pro mergeability (LOW-MED effect)
**Co**: V `quality_gates.py:41-49` re-weight:
```python
GATE_WEIGHTS = {
    "integration_diff": 2.5,  # NEW — primary
    "tests": 2.0,
    "types": 1.5,
    "security": 2.0,
    "build": 1.5,
    "lint": 1.0,
    "a11y": 0.75,           # ↓ ze 1.0 — neblokuje merge, blokuje launch
    "observability": 0.25,  # ↓ ze 0.5 — řeší se v prod hardening, ne v session
}
```
**Proč**: Současné weights optimalizují „is it production-ready" (správné pro Session 3 verdict), ale autoresearch metric je „is it mergeable". Mergeable kód jde do PR, observability/a11y se doplní v normal sprint.
**Měření**: Re-skóre 3 historických runs s novými weights. Pokud se ranking variant změní u > 1/3, weights mají signal.
**Síla**: LOW (jen pokud C5 je in)

## Anti-patterns — co tým NIKDY nedělat

1. **„Skeleton stačí, target repo doplníme po session."** Ne — generic skeleton + retroaktivní integrace = 100 % rewrite. Target repo URL je **vstup do session, ne výstup**. Pokud chybí, downgrade na throwaway risk profile a explicitně řekni týmu „tohle se nemerguje, jen se učíme".
2. **„Vypneme strict TS pro speed."** Ne — `tsconfig.json:101 "strict": true` je v skeletonu správně. Strict TS je zdarma quality gate. Vypnutí = +50 % rewrite ratio při merge (typing musí dohnat reviewer).
3. **„CC si poradí, prompt je dostatečný."** Ne — CC bez explicit read listu (C3) průměrně spotřebuje 30 % session window na exploration. To je 27 minut z 90 minut session promarněno.
4. **„3 worktrees v PflanzerMethod repu."** Ne — to je současný bug v `pflanzer.md:121`. Worktree musí být v target repu.
5. **„Vibe-coding bez Conventional Commits."** Ne — bez atomic commits není možné cherry-pick winning subset. Ban `git commit -am "WIP"` v session.
6. **„Single big commit na konci session."** Ne — atomicita commitů (C4) je předpoklad reusability. Big-bang commit = big-bang review = big-bang reject.
7. **„Spustíme gates jednou na konci."** Ne — gates by měly běžet **per commit** v worktree (pre-commit hook). Hook v skeleton scaffold by měl být `husky` + `lint-staged`. Currently chybí v `SKELETON_FILES` úplně.

## Tool / process recommendations — concrete configs

### Skeleton additions (do `SKELETON_FILES` v `extract.py:50`)

- **`.husky/pre-commit`**: `npx lint-staged && npm run -s typecheck`
- **`.lintstagedrc.json`**: `{"*.{ts,tsx}": ["eslint --fix", "prettier --write"]}`
- **`commitlint.config.cjs`**: `{extends: ['@commitlint/config-conventional']}`
- **`.husky/commit-msg`**: `npx --no -- commitlint --edit ${1}`
- **`.editorconfig`**: 4-space py, 2-space ts, LF endings, final newline
- **`.nvmrc`**: pin node version (e.g., `20.11.0`) — eliminuje „works on my machine"
- **`CLAUDE.md`** (per worktree): krátký variant-specific kontext (variant angle, kill criteria, „read these files first" list z C3)
- **`.github/PULL_REQUEST_TEMPLATE.md`**: pre-filled checkboxy (gates passed, ADR linked, screenshots)

### Prompt cache strategy

- Use Anthropic prompt caching: skeleton prompt + read list = 1st turn, mark `cache_control: ephemeral`. Each subsequent turn re-uses cache → ~85 % cost reduction + faster TTFT.
- V `_render_builder_prompt()` výstup strukturovat tak, aby first ~5k tokenů (system + read list + Charter context) byly stable across all 3 variants. Diff jen v posledním ~500-token blocku (variant brief).

### Libraries to add (skeleton devDependencies)

- `husky` ^9 — git hooks
- `lint-staged` ^15 — staged linting
- `@commitlint/cli` + `@commitlint/config-conventional` — commit message validation
- `jscpd` ^4 (devDep, ne runtime) — duplicate detection pro `gate_integration_diff`
- `vitest-mock-extended` — better mocks bez boilerplate
- Pokud target repo používá `pnpm` / `bun`, **detect a use it** (read `packageManager` field z target `package.json`); current skeleton hard-codes `npm`.

### Quality gate enforcement order (re-order in `quality_gates.py:374-377`)

Run in this order, **fail-fast**:
1. `integration_diff` (cheap, gating)
2. `types` (fast, deterministic)
3. `lint` (fast)
4. `tests` (medium)
5. `build` (slow)
6. `security` (slow, async OK)
7. `a11y` (info-only)
8. `observability` (info-only)

Currently `quality_gates.py:374-377` runs in `GATE_TYPES` order which is alphabetical-ish, ne by-cost. Fail-fast saves 60-90 s per failed run × 3 variants × N iterations.

### Worktree friction reduction

- Add helper `tool/cli/worktree.py` s `setup --slug X --target-repo URL` který vyrobí všechny 3 worktrees + checkout + spustí `npm install` paralelně. Současný manuální `git worktree add` × 3 + `cd` × 3 + `claude` × 3 je 6+ příkazů × 3 lidi = friction nad „opening Bolt tabu". Sniž na 1 příkaz.
- Worktree má vlastní `.claude/` s pre-loaded variant prompt (no copy-paste from JSON output) — CC při startupu rovnou vidí context.

### Token economy v 90-min session

| Spotřebič | Současně | Po C1+C3 | Úspora |
|---|---|---|---|
| Glob/Grep exploration | 25 k | 5 k | 20 k |
| Read files (no cache) | 40 k | 15 k (cached) | 25 k |
| Code generation | 30 k | 30 k | 0 |
| Re-explanation/recovery | 15 k | 5 k | 10 k |
| **Total** | **~110 k** | **~55 k** | **50 % rozpočtu** |

Free 50 % rozpočtu = více iterace per variant = vyšší kvalita = vyšší reusability.

---

*References: `extract.py:50-247` (skeleton), `extract.py:284-307` (scaffold), `quality_gates.py:40-49` (gate weights), `quality_gates.py:374-377` (gate order), `quick_session.py:385-456` (builder prompt), `pflanzer.md:121-134` (worktree setup).*
