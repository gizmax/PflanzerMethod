"""Registrace kódu varianty pro Ship (v0.5) + sdílené helpery Build/Ship.

Cíl: po Buildu a Rozhodnutí mít skutečný kód (ne jen preview URL), aby Ship
mohl projet quality gates a tým ho mohl opravdu použít.

**Výchozí metoda (v0.5) = `in_repo_branch`:** pokud existuje git worktree
varianty (`~/.pflanzer/targets/<slug>-<A|B|C>`, větev `pflanzer/<slug>-<X>`),
kód se jen zaregistruje (větev, HEAD SHA, velikost diffu proti základní větvi).
Skeleton se nikdy nespouští, pokud worktree existuje.

Sdílené helpery pro ostatní moduly Buildu/Shipu: `BRAND`, `DATA_ROOT`,
`table_has_col`, `locate_worktree`, `git_info`, `diff_stats`, `tilde`.

Strategie podle builderu (jen když worktree neexistuje):
- **bolt / lovable / v0**: většinou exportují přes „Push to GitHub"
  → user vloží GitHub URL (https://github.com/<user>/<repo>) a my git clone.
- **cursor**: code už je v lokálním repu (in-place edits) → extract = git fetch
  + checkpoint commit hash.
- **stitch / figma-make**: jen UI mockup, **žádný export** → fallback skeleton.
- **manual**: assume už v repu, jen zaregistrovat.

Pokud user nemá GitHub URL (ještě nepushl), můžeme:
1. Scaffoldovat **Vite + React + TS skeleton** s production-grade defaults
   (ESLint, Prettier, Vitest, Tailwind, axe-core). User pak ručně
   překopíruje komponenty z preview.
2. Vrátit `extraction_method='manual_paste'` se skeleton.

Po extractu: zaregistrovat row do `extracted_code` a vrátit local_path
+ files_count + total_loc pro `quality_gates.py`.

Ship (audit N3) — method selection order:
1. explicit `method_override`,
2. `worktree` — the variant's worktree from `worktree.py setup` exists
   (`~/.pflanzer/targets/<slug>-<variant>/`, branch `pflanzer/<slug>-<variant>`);
   pre-flight checks `origin == projects.target_repo_url`, gates run in place
   (no copy),
3. `git_clone` — hosted builder GitHub URL (`--prefer-hosted` projects),
4. `skeleton` — only for risk profile `throwaway`; pilot/production fail loud.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import ProjectNotFound  # noqa: E402
from tool.cli.db import audit, current_actor, display_path, transaction  # noqa: E402
from tool.cli.triage import load_risk_profile  # noqa: E402
from tool.cli.worktree import TARGETS_CACHE, verify_cwd_in_target  # noqa: E402

try:  # DATA_ROOT dodává tool.cli.db (výstupy mimo repo metody); fallback = <repo>/data
    from tool.cli.db import DATA_ROOT  # type: ignore[attr-defined]  # noqa: E402
except ImportError:  # pragma: no cover
    DATA_ROOT = REPO_ROOT / "data"

BRAND = "**Pflanzer Method | pflanzer.cz/method**"

EXTRACTED_DIR = DATA_ROOT / "extracted"
SUPPORTED_BUILDERS = {"claude-code", "codex-cli", "v0", "bolt", "lovable",
                      "cursor", "manual", "stitch", "figma-make"}
HOSTED_BUILDERS = {"v0", "bolt", "lovable"}
EXTRACTION_METHODS = ("worktree", "in_repo_branch", "git_clone", "skeleton",
                      "manual_paste", "builder_api")
# Methods that register the variant's worktree in place (no copy).
WORKTREE_METHODS = {"worktree", "in_repo_branch"}
# Methods that scaffold greenfield code — allowed only for throwaway.
SKELETON_METHODS = {"skeleton", "manual_paste"}


class ExtractionError(RuntimeError):
    """Fail-loud extraction problem with an actionable (Czech) message."""


# --------------------------------------------------------------------------
# Sdílené helpery (Build / Ship)
# --------------------------------------------------------------------------


def table_has_col(conn: Any, table: str, col: str) -> bool:
    """True, pokud tabulka má sloupec (DB bez nejnovější additive migrace nespadne)."""
    return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})").fetchall())


def tilde(path: Path | str) -> str:
    """Absolutní cestu pod $HOME zkrátí na ~/… (do generovaných textů nepatří lokální cesty)."""
    s = str(path)
    home = str(Path.home())
    return "~" + s[len(home):] if s == home or s.startswith(home + "/") else s


def clean_text(value: Any, placeholder: str = "doplnit") -> str:
    """Prázdná hodnota nebo placeholder `TBD…` z Kickoffu -> srozumitelné "doplnit"."""
    text = (str(value).strip() if value is not None else "")
    if not text or text.upper().startswith("TBD"):
        return placeholder
    return text


def public_repo_ref(url: str | None) -> str:
    """URL repa do textu; lokální cesta (file/bare origin) se zkrátí na název složky."""
    if not url:
        return "(target_repo_url nezadán v Kickoffu)"
    return Path(url).name if url.startswith("/") else url


def _targets_cache() -> Path:
    return Path(TARGETS_CACHE)


def locate_worktree(slug: str, variant: str, target_repo_url: str | None = None) -> Path | None:
    """Najdi git worktree varianty (`<slug>-<X>` i `<repo>-<X>` v cache targetů)."""
    cache = _targets_cache()
    names = [f"{slug}-{variant}"]
    if target_repo_url:
        try:
            from tool.cli.worktree import _slugify_repo
            names.append(f"{_slugify_repo(target_repo_url)}-{variant}")
        except Exception:
            pass
    for n in names:
        cand = cache / n
        if (cand / ".git").exists():
            return cand
    legacy = REPO_ROOT.parent / f"proto-{slug}-{variant}"
    return legacy if (legacy / ".git").exists() else None


def _git(wt: Path, *args: str, timeout: int = 30) -> tuple[int, str]:
    try:
        res = subprocess.run(["git", "-C", str(wt), *args], capture_output=True,
                             text=True, timeout=timeout)
        return res.returncode, res.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


def git_info(wt: Path) -> dict[str, Any]:
    """Větev + HEAD SHA + dirty flag worktree (prázdné hodnoty, pokud git selže)."""
    rc_b, branch = _git(wt, "rev-parse", "--abbrev-ref", "HEAD")
    rc_h, sha = _git(wt, "rev-parse", "HEAD")
    rc_s, status = _git(wt, "status", "--porcelain")
    return {
        "branch": branch if rc_b == 0 else None,
        "head_sha": sha if rc_h == 0 else None,
        "dirty": bool(status) if rc_s == 0 else None,
    }


def diff_stats(wt: Path, base_branch: str = "main") -> dict[str, int | None]:
    """Přidané/odebrané řádky a počet souborů vítězné větve proti základní větvi."""
    base = None
    for ref in (f"origin/{base_branch}", base_branch):
        rc, mb = _git(wt, "merge-base", "HEAD", ref)
        if rc == 0 and mb:
            base = mb
            break
    if not base:
        return {"added": None, "removed": None, "files": None}
    rc, out = _git(wt, "diff", "--numstat", base, "HEAD", timeout=60)
    if rc != 0:
        return {"added": None, "removed": None, "files": None}
    added = removed = files = 0
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        files += 1
        if parts[0].isdigit():
            added += int(parts[0])
        if parts[1].isdigit():
            removed += int(parts[1])
    return {"added": added, "removed": removed, "files": files}


_CODE_SUFFIXES = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
                  ".go", ".java", ".kt", ".cs", ".rb", ".php", ".rs", ".swift")
_TEST_NAME_RE = re.compile(r"(\.|_)(test|spec)\.[a-z]+$|^test_.*\.py$|_test\.(py|go)$")
_TEST_DIRS = {"test", "tests", "__tests__", "spec", "e2e"}


def _is_test_path(rel: str) -> bool:
    parts = rel.split("/")
    return bool(_TEST_NAME_RE.search(parts[-1])) or any(d in _TEST_DIRS for d in parts[:-1])


def code_without_tests(wt: Path, base_branch: str = "main") -> dict[str, Any] | None:
    """Přidal vítěz nové zdrojové soubory bez jediného nového/změněného testu?

    Porovnává pracovní strom s merge-base proti base větvi (commity i necommitnuté změny,
    včetně nových souborů). None = nejde zjistit (bez gitu / bez base větve).
    """
    base = None
    for ref in (f"origin/{base_branch}", base_branch):
        rc, mb = _git(wt, "merge-base", "HEAD", ref)
        if rc == 0 and mb:
            base = mb
            break
    if not base:
        return None
    rc, out = _git(wt, "diff", "--name-status", "--no-renames", base, timeout=60)
    if rc != 0:
        return None
    changed: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changed[parts[-1]] = parts[0][:1]
    rc, untracked = _git(wt, "ls-files", "--others", "--exclude-standard")
    for rel in untracked.splitlines() if rc == 0 else []:
        changed.setdefault(rel, "A")
    new_src = [f for f, st in changed.items()
               if st == "A" and f.lower().endswith(_CODE_SUFFIXES) and not _is_test_path(f)]
    tests = [f for f, st in changed.items() if st in ("A", "M") and _is_test_path(f)]
    return {"new_source_files": len(new_src), "test_files_changed": len(tests),
            "examples": new_src[:3], "missing_tests": bool(new_src) and not tests}


# --------------------------------------------------------------------------
# Skeleton — minimální production-grade Vite + React + TS projekt
# (zero deps; ready to `npm install` a ihned passing lint/type/test)
# --------------------------------------------------------------------------


SKELETON_FILES: dict[str, str] = {
    "package.json": """{
  "name": "{slug}-{variant}",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "engines": {
    "node": ">=20.11"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write \\"src/**/*.{ts,tsx,css}\\"",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:acceptance": "playwright test tests/acceptance",
    "preview": "vite preview",
    "prepare": "lefthook install || true"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@axe-core/playwright": "^4.10.0",
    "@faker-js/faker": "^9.0.0",
    "@playwright/test": "^1.48.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^14.2.0",
    "@testing-library/user-event": "^14.5.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@vitest/coverage-v8": "^1.4.0",
    "eslint": "^8.57.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "jest-axe": "^9.0.0",
    "jsdom": "^24.0.0",
    "lefthook": "^1.7.0",
    "msw": "^2.4.0",
    "prettier": "^3.2.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "vitest": "^1.4.0"
  }
}
""",
    "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src"]
}
""",
    "vite.config.ts": """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
});
""",
    ".eslintrc.cjs": """module.exports = {
  root: true,
  env: { browser: true, es2020: true, node: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
  },
};
""",
    ".prettierrc": """{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100
}
""",
    ".gitignore": """node_modules/
dist/
.env
.env.local
*.log
.DS_Store
coverage/
""",
    "index.html": """<!doctype html>
<html lang="cs">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="robots" content="noindex,nofollow" />
    <title>{slug} — {variant}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
    "src/main.tsx": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
""",
    "src/App.tsx": """/**
 * Pflanzer prototype skeleton — variant {variant}.
 *
 * REPLACE THIS with components from your vibe-coding tool preview.
 * Keep TypeScript strict mode + WCAG 2.2 AA semantics + design tokens.
 */
export default function App() {
  return (
    <main role="main" aria-label="Prototype">
      <header>
        <h1>{slug} — varianta {variant}</h1>
      </header>
      <section aria-labelledby="cta-heading">
        <h2 id="cta-heading">Onboarding krok 1</h2>
        <button type="button" onClick={() => alert('TODO: replace with extracted handler')}>
          Začít
        </button>
      </section>
    </main>
  );
}
""",
    "src/App.test.tsx": """import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from './test/render';
import App from './App';

describe('App skeleton', () => {
  it('renders heading', () => {
    render(<App />);
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });

  it('renders accessible CTA', () => {
    render(<App />);
    expect(screen.getByRole('button', { name: /začít/i })).toBeInTheDocument();
  });

  // Negative path — POVINNÉ per qa-test-architect perspektiva
  it('handles missing data gracefully (negative path)', () => {
    render(<App />);
    // Skeleton: button click neházet error
    expect(() => {
      const btn = screen.getByRole('button', { name: /začít/i });
      btn.click();
    }).not.toThrow();
  });
});
""",
    "src/test/render.tsx": """/**
 * Sdílený render helper. Tým rozšiřuje o providers (router, query client,
 * theme, auth context) podle target repa INTEGRATION_GUIDE.md.
 */
import { render as rtlRender, RenderOptions } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReactElement } from 'react';

export function render(ui: ReactElement, options?: RenderOptions) {
  return {
    user: userEvent.setup(),
    ...rtlRender(ui, options),
  };
}

export * from '@testing-library/react';
""",
    "src/test/factories.ts": """/**
 * Test data factories — používej `faker` místo hardcoded fixtures
 * (perspektiva 04 anti-pattern: hardcoded test@test.com regex bounce).
 */
import { faker } from '@faker-js/faker';

export const userFactory = (overrides: Partial<User> = {}): User => ({
  id: faker.string.uuid(),
  email: faker.internet.email(),
  name: faker.person.fullName(),
  createdAt: faker.date.past().toISOString(),
  ...overrides,
});

export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}
""",
    "src/test/server.ts": """/**
 * MSW server pro testy — místo Pact (perspektiva 04 conflict resolution).
 * Sdílí handlers napříč unit + integration tests.
 */
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
""",
    "src/test/handlers.ts": """import { http, HttpResponse } from 'msw';
import { userFactory } from './factories';

export const handlers = [
  http.get('/api/me', () => HttpResponse.json(userFactory())),
  // Tým doplní endpoints per INTEGRATION_GUIDE.md API client patterns.
];
""",
    "src/test/setup.ts": """import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { server } from './server';

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
""",
    "tests/acceptance/example.feature": """# Acceptance kritéria pro {slug} variant {variant}.
# Tento soubor zapisuje Decider při Kickoffu PŘED Buildem.
# AI variants implementují TENTO spec, ne vlastní výmysl.
# Per autoresearch synthesis T2 + ADR-0010 (acceptance gate).

Feature: {slug} core flow

  Scenario: Happy path — uživatel projde primary flow
    Given valid input z persona
    When uživatel projde flow
    Then primary lagging metric event je zaznamenán

  Scenario: Negative path — invalid input
    Given invalid input
    When uživatel zkusí submit
    Then UI vrátí actionable error (B1/B2 plain language)
    And žádná data nejsou persisted

  Scenario: Edge case — pomalé BE
    Given valid input
    When BE response > 5s
    Then UI ukáže loading state, pak fallback graceful
""",
    "tests/acceptance/example.spec.ts": """/**
 * Playwright runner pro acceptance scénáře.
 * `quality_gates.py gate_acceptance` čte JSON output odsud.
 *
 * Pro reálnou implementaci nahradit hard-coded scénáře parserem .feature
 * souboru přes @cucumber/cucumber. MVP: 1 spec = 1 feature scenario.
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('{slug} core flow', () => {
  test('Happy path — primary flow accessible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByRole('button', { name: /začít/i })).toBeVisible();
  });

  test('A11y — no critical violations on landing', async ({ page }) => {
    await page.goto('/');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
      .analyze();
    const critical = results.violations.filter(v => v.impact === 'critical');
    expect(critical).toEqual([]);
  });
});
""",
    "playwright.config.ts": """import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['json', { outputFile: 'playwright-report.json' }]],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
""",
    "lefthook.yml": """# Pre-commit gates per worktree.
# Per autoresearch perspektiva 03 (devex) #2 — broken commits never reach git.
# Per perspektiva 04 — fail-fast pro tým u stolu, ne post-hoc CI surprise.
pre-commit:
  parallel: true
  commands:
    lint:
      glob: "*.{ts,tsx,js,jsx}"
      run: npx eslint --max-warnings 0 {staged_files}
    types:
      glob: "*.{ts,tsx}"
      run: npx tsc --noEmit
    tests:
      glob: "*.{ts,tsx}"
      run: npm test -- --changed --reporter=dot
""",
    ".nvmrc": """20.11
""",
    ".npmrc": """save-exact=true
engine-strict=true
""",
    "README.md": """# {slug} — varianta {variant}

Prototype scaffold from `/pflanzer` workflow. Replace `src/App.tsx` with
components from your Bolt/v0/Lovable preview.

## Setup

```bash
npm install
npm run dev
```

## Quality gates (run by `tool/cli/quality_gates.py`)

```bash
npm run lint     # ESLint zero warnings
npm run build    # TypeScript strict mode passes
npm test         # Vitest suite passes
```

## A11y

- WCAG 2.2 AA target
- Default semantic HTML in skeleton; preserve when extending
- axe-core spuštěn v gates (volitelně)

## Deploy

- Sandbox only (per Pflanzer Charter throwaway/evolve directive).
- Production: pouze po `/pm ship` + handoff package.
""",
}


# --------------------------------------------------------------------------
# Builder-specific extraction
# --------------------------------------------------------------------------


def _validate_github_url(url: str) -> bool:
    pattern = r"^https?://github\.com/[\w.-]+/[\w.-]+(?:\.git)?/?$"
    return bool(re.match(pattern, url))


def _git_clone(repo_url: str, dest: Path, force: bool = False) -> tuple[int, int]:
    """Clone repo. Returns (files_count, total_loc).

    Idempotent: pokud dest existuje, skip clone (assume tým už pracuje s tímto kódem).
    Force=True = clean re-clone.
    """
    if dest.exists() and not force:
        return _count_files(dest)
    if dest.exists() and force:
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(dest)],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"git clone selhal: {res.stderr.strip()}")
    # Remove .git so it doesn't conflict with parent repo
    git_dir = dest / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
    return _count_files(dest)


def _scaffold_skeleton(slug: str, variant: str, dest: Path,
                       force: bool = False) -> tuple[int, int]:
    """Write production-grade Vite/React/TS skeleton.

    Idempotent: pokud dest/package.json už existuje, skip overwrite (tým
    už pracuje s extracted code; nechci smazat node_modules nebo edits).
    Force=True = clean re-scaffold.
    """
    if (dest / "package.json").exists() and not force:
        return _count_files(dest)

    if dest.exists() and force:
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for rel_path, template in SKELETON_FILES.items():
        target = dest / rel_path
        if target.exists() and not force:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            template.replace("{slug}", slug).replace("{variant}", variant),
            encoding="utf-8",
        )
    return _count_files(dest)


def _count_files(root: Path) -> tuple[int, int]:
    """Count source files + total LOC (skip node_modules, dist, etc.)."""
    skip_dirs = {"node_modules", "dist", "build", ".next", "coverage", ".venv", ".git"}
    code_exts = {".ts", ".tsx", ".js", ".jsx", ".py", ".css", ".scss", ".html",
                 ".json", ".md", ".yml", ".yaml"}
    files = 0
    loc = 0
    for p in root.rglob("*"):
        if any(part in skip_dirs for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in code_exts:
            files += 1
            try:
                loc += sum(1 for _ in p.read_text(encoding="utf-8", errors="ignore").splitlines())
            except OSError:
                pass
    return files, loc


# --------------------------------------------------------------------------
# Worktree discovery + method selection (Ship, audit N3)
# --------------------------------------------------------------------------


def worktree_path(slug: str, variant: str) -> Path:
    """Expected worktree location for a variant.

    Mirrors `worktree._create_worktrees`: worktrees are siblings of the cached
    target clone (`TARGETS_CACHE/<repo-slug>/`), named `<project-slug>-<variant>`.
    """
    return TARGETS_CACHE / f"{slug}-{variant}"


def find_worktree(slug: str, variant: str, target_repo_url: str | None = None) -> Path | None:
    """Return the existing worktree for a variant, or None.

    Checks the `worktree.py setup` location(s) first (`<slug>-<X>`, `<repo>-<X>`),
    then the legacy `../proto-<slug>-<variant>` sibling of this repo.
    """
    found = locate_worktree(slug, variant, target_repo_url)
    if found is not None:
        return found
    for candidate in (worktree_path(slug, variant),
                      REPO_ROOT.parent / f"proto-{slug}-{variant}"):
        if candidate.is_dir():
            return candidate
    return None


def _setup_hint(slug: str) -> str:
    return f"pflanzer worktree setup --slug {slug}"


def plan_extraction(
    *, slug: str, variant_name: str, builder: str, risk_profile: str,
    repo_url: str | None = None, method_override: str | None = None,
    target_repo_url: str | None = None,
) -> tuple[str, Path | None]:
    """Pick the extraction method without side effects.

    Order: explicit override > existing worktree > hosted repo URL >
    skeleton (throwaway only). Raises ExtractionError when nothing usable
    exists, so Ship can fail loud before running any gate.

    Returns (method, worktree_path_or_None).
    """
    wt = find_worktree(slug, variant_name, target_repo_url)
    if method_override:
        method = method_override
        if method not in EXTRACTION_METHODS:
            raise ValueError(
                f"Unknown extraction_method '{method}' (varianta {variant_name}); "
                f"povolené: {', '.join(EXTRACTION_METHODS)}."
            )
        if method in WORKTREE_METHODS and wt is None:
            raise ExtractionError(
                f"Varianta {variant_name}: method '{method}' vyžaduje worktree "
                f"`{worktree_path(slug, variant_name)}`, který neexistuje. "
                f"Spusť `{_setup_hint(slug)}`."
            )
        if method == "git_clone" and not (repo_url and _validate_github_url(repo_url)):
            raise ExtractionError(
                f"Varianta {variant_name}: method 'git_clone' vyžaduje platnou GitHub URL "
                f"(dostal jsem: {repo_url or 'nic'})."
            )
    elif wt is not None:
        method = "worktree"
    elif repo_url:
        if not _validate_github_url(repo_url):
            raise ExtractionError(
                f"Varianta {variant_name}: '{repo_url}' není platná GitHub URL "
                "(očekávám https://github.com/<owner>/<repo>)."
            )
        method = "git_clone"
    elif risk_profile == "throwaway":
        method = "manual_paste" if builder == "cursor" else "skeleton"
    else:
        hosted_hint = (
            f" Varianta je z hosted builderu `{builder}` (--prefer-hosted): dodej "
            f"GitHub URL přes `--repo-urls '{{\"{variant_name}\": \"https://github.com/<org>/<repo>\"}}'`."
            if builder in HOSTED_BUILDERS else ""
        )
        raise ExtractionError(
            f"Varianta {variant_name}: worktree `{worktree_path(slug, variant_name)}` "
            f"neexistuje a pro risk profil '{risk_profile}' není skeleton povolený "
            f"(greenfield kód do target repa nepůjde, reuse ~0 %). "
            f"Spusť `{_setup_hint(slug)}` a postav variantu ve worktree.{hosted_hint}"
        )

    if method in SKELETON_METHODS and risk_profile != "throwaway":
        raise ExtractionError(
            f"Varianta {variant_name}: method '{method}' (skeleton) je povolená jen pro "
            f"risk profil 'throwaway', projekt má '{risk_profile}'. "
            f"Spusť `{_setup_hint(slug)}` a postav variantu ve worktree target repa."
        )
    return method, wt


def _git_out(path: Path, *args: str) -> tuple[int, bytes]:
    try:
        res = subprocess.run(["git", "-C", str(path), *args], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return 1, b""
    return res.returncode, res.stdout


def base_gates_adapter(worktree: Path, target_branch: str) -> dict[str, Any]:
    """Load the gate adapter (`pflanzer.gates.yml|yaml|json`) from the BASE branch.

    Integrity guard: the adapter lives in the same repo as the scored variant,
    so an agent in the worktree could "simplify" it. Ship therefore
    uses the base-branch version (`origin/<target_branch>`, fallback
    `<target_branch>`), written to a temp file, and only warns about the
    worktree copy. The caller removes `tmp_dir` when done.

    Returns {adapter_path, base_ref, name, tmp_dir, warnings}; adapter_path is
    None when the base branch has no adapter (autodetection).
    """
    from tool.cli.quality_gates import ADAPTER_FILENAMES  # lazy: quality_gates imports extract

    out: dict[str, Any] = {"adapter_path": None, "base_ref": None, "name": None,
                           "tmp_dir": None, "warnings": []}
    base_content: bytes | None = None
    # Best effort: čerstvá base branch (lokální origin/<branch> může být pozadu); bez sítě nevadí.
    try:
        subprocess.run(["git", "-C", str(worktree), "fetch", "--quiet", "origin", target_branch],
                       capture_output=True, timeout=20,
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except (OSError, subprocess.TimeoutExpired):
        pass
    for ref in (f"origin/{target_branch}", target_branch):
        rc, _ = _git_out(worktree, "rev-parse", "--verify", "--quiet", ref)
        if rc != 0:
            continue
        out["base_ref"] = ref
        for name in ADAPTER_FILENAMES:
            rc, blob = _git_out(worktree, "show", f"{ref}:{name}")
            if rc == 0:
                out["name"], base_content = name, blob
                break
        break  # base ref exists: do not fall back to another ref
    if out["base_ref"] is None:
        out["warnings"].append(
            f"Base `{target_branch}` nenalezena ve {worktree} — adaptér z base nelze načíst "
            "(autodetekce)."
        )

    if base_content is not None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="pflanzer-adapter-"))
        adapter = tmp_dir / out["name"]
        adapter.write_bytes(base_content)
        out["adapter_path"], out["tmp_dir"] = adapter, tmp_dir

    for name in ADAPTER_FILENAMES:
        local = worktree / name
        if not local.is_file():
            continue
        if base_content is None:
            out["warnings"].append(
                f"`{name}` přidán ve variant branchi (v base `{target_branch}` není) — "
                "reviewuj jako změnu CI configu."
            )
        elif name != out["name"] or local.read_bytes() != base_content:
            out["warnings"].append(
                f"adapter modified in variant branch — ignored (`{name}` ≠ "
                f"`{out['base_ref']}:{out['name']}`; gates běží s verzí z base)."
            )
    if base_content is not None and not (worktree / out["name"]).is_file():
        out["warnings"].append(
            f"adapter modified in variant branch — ignored (`{out['name']}` ve variant "
            "branchi smazán; gates běží s verzí z base)."
        )
    return out


def _current_branch(path: Path) -> str | None:
    res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                         cwd=path, capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else None


def _load_variant(slug: str, variant_name: str) -> dict[str, Any]:
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, name, target_repo_url, target_branch FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        project_id = int(proj[0])
        risk_profile = load_risk_profile(conn, project_id)

        variant = conn.execute(
            """
            SELECT v.id, v.builder, v.prototype_url
            FROM variants v
            JOIN sessions s ON s.id = v.session_id
            WHERE s.project_id = ? AND s.type = 1 AND v.name = ?
            """,
            (project_id, variant_name),
        ).fetchone()
        if not variant:
            raise ValueError(f"Varianta {variant_name} v Buildu projektu {slug} neexistuje. "
                             f"Zkontroluj název (A/B/C): `pflanzer status`.")
    return {
        "project_id": project_id,
        "target_repo_url": proj[2],
        "target_branch": proj[3] or "main",
        "risk_profile": risk_profile,
        "variant_id": int(variant[0]),
        "builder": variant[1],
        "prototype_url": variant[2],
    }


# --------------------------------------------------------------------------
# Main extract
# --------------------------------------------------------------------------


def extract(
    *, slug: str, variant_name: str,
    source_url: str | None = None, repo_url: str | None = None,
    method_override: str | None = None, force: bool = False,
) -> dict[str, Any]:
    """Zaregistruj kód jedné varianty (default: existující git worktree).

    Args:
        slug: project slug.
        variant_name: A / B / C.
        source_url: prototype preview URL (for audit).
        repo_url: GitHub URL pokud user pushl z builder (nebo `branch:<name>`).
        method_override: force 'worktree' / 'git_clone' / 'skeleton' / 'manual_paste'.

    Pro method 'worktree' se nic nekopíruje: local_path = worktree v target repu.

    Returns dict s extracted_id, local_path, files_count, total_loc, method, branch, head_sha.
    """
    info = _load_variant(slug, variant_name)
    variant_id, builder = info["variant_id"], info["builder"]
    target_url, risk_profile = info["target_repo_url"], info["risk_profile"]
    target_branch = info["target_branch"]
    source_url = source_url or info["prototype_url"]

    method, wt = plan_extraction(
        slug=slug, variant_name=variant_name, builder=builder,
        risk_profile=risk_profile, repo_url=repo_url, method_override=method_override,
        target_repo_url=target_url,
    )

    dest = EXTRACTED_DIR / slug / variant_name
    source_repo_url = repo_url
    notes: list[str] = []
    branch: str | None = None
    head_sha: str | None = None
    diff: dict[str, int | None] = {"added": None, "removed": None, "files": None}
    if method in WORKTREE_METHODS:
        assert wt is not None  # guaranteed by plan_extraction
        # Pre-flight (ADR-0009): the worktree must belong to target_repo_url,
        # otherwise gates would score code that never reaches the target repo.
        ok, msg = verify_cwd_in_target(slug, wt)
        if not ok:
            raise ExtractionError(
                f"Pre-flight selhal pro variantu {variant_name} ({tilde(wt)}): {msg}"
            )
        dest = wt
        source_repo_url = target_url
        expected_branch = (
            repo_url.replace("branch:", "") if repo_url and repo_url.startswith("branch:")
            else f"pflanzer/{slug}-{variant_name}"
        )
        gi = git_info(wt)
        branch, head_sha = gi["branch"], gi["head_sha"]
        diff = diff_stats(wt, target_branch)
        if branch != expected_branch:
            notes.append(
                f"Worktree {tilde(wt)} je na větvi `{branch}`, očekávám `{expected_branch}`."
            )
        files, loc = _count_files(dest)
        notes.append(
            f"Worktree `{tilde(wt)}` (větev `{branch}` @ {(head_sha or '?')[:10]}) - "
            "gates běží přímo v target repu, žádné kopírování."
        )
        if gi["dirty"]:
            notes.append("Worktree má necommitnuté změny - do PR půjde jen to, co je commitnuté.")
    elif method == "git_clone":
        existed = dest.exists()
        files, loc = _git_clone(repo_url, dest, force=force)
        notes.append(f"Reused existing {dest.name}" if existed and not force else f"Cloned from {repo_url}")
    elif method == "skeleton":
        files, loc = _scaffold_skeleton(slug, variant_name, dest, force=force)
        notes.append(
            "Scaffolded skeleton (Vite + React + TS + Vitest + ESLint) - throwaway only."
            " Tým musí překopírovat komponenty z preview."
        )
    elif method == "manual_paste":
        files, loc = _scaffold_skeleton(slug, variant_name, dest, force=force)
        notes.append(
            "Skeleton ready. Tým vloží kód z Cursoru / lokálního repa do cílové složky."
        )
    elif method == "builder_api":
        raise NotImplementedError(
            "builder_api extraction není v MVP — zatím použij git_clone nebo manual_paste."
        )
    else:
        raise ValueError(f"Neznámá metoda načtení kódu „{method}“.")

    # Persist
    with transaction() as conn:
        insert_sql = """
            INSERT INTO extracted_code (
                variant_id, source_url, source_repo_url, local_path,
                extraction_method, files_count, total_loc, extracted_by, notes_md
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

        # 'worktree' is part of the extraction_method CHECK since the
        # migrate.py rebuild of extracted_code — older DBs: run migrate.py.
        stored_method = method
        cur = conn.execute(
            insert_sql,
            (variant_id, source_url, source_repo_url, display_path(dest),
             stored_method, files, loc, current_actor(), "\n".join(notes)),
        )
        extracted_id = int(cur.lastrowid)
        if table_has_col(conn, "extracted_code", "diff_loc_added"):
            conn.execute(
                "UPDATE extracted_code SET diff_loc_added = ?, diff_loc_removed = ?, "
                "diff_files = ? WHERE id = ?",
                (diff["added"], diff["removed"], diff["files"], extracted_id),
            )
        if branch and table_has_col(conn, "variants", "head_sha"):
            conn.execute("UPDATE variants SET branch = ?, head_sha = ? WHERE id = ?",
                         (branch, head_sha, variant_id))

        audit(
            conn,
            action="extract.code",
            target_type="variant",
            target_id=variant_id,
            payload={
                "slug": slug, "variant": variant_name,
                "method": method, "stored_method": stored_method,
                "risk_profile": risk_profile,
                "branch": branch, "head_sha": head_sha, "diff_loc_added": diff["added"],
                "local_path": display_path(dest), "files": files, "loc": loc,
            },
        )

    return {
        "extracted_id": extracted_id,
        "slug": slug,
        "variant": variant_name,
        "builder": builder,
        "method": method,
        "stored_method": stored_method,
        "risk_profile": risk_profile,
        "local_path": display_path(dest),
        "absolute_path": str(dest),
        "branch": branch,
        "head_sha": head_sha,
        "files_count": files,
        "total_loc": loc,
        "diff_loc_added": diff["added"],
        "diff_loc_removed": diff["removed"],
        "diff_files": diff["files"],
        "notes": notes,
        "next_step": (
            f"Kód je ve větvi `{branch}`; další krok: quality gates (`pflanzer session_3 --slug {slug}`)."
            if method in WORKTREE_METHODS
            else f"Zkontroluj {tilde(dest)}/ a doplň chybějící části ručně."
        ),
    }


def main() -> None:
    from tool.cli.ux import CzechArgumentParser

    p = CzechArgumentParser(prog="pflanzer extract", description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--variant", required=True, help="A / B / C")
    p.add_argument("--source-url", default=None,
                   help="Preview URL z buildru (default: read z DB)")
    p.add_argument("--repo-url", default=None,
                   help="GitHub URL pokud user pushl z buildru")
    p.add_argument("--method", default=None, choices=list(EXTRACTION_METHODS),
                   help="Force specific extraction method (default: worktree autodetect)")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing extracted dir (DELETES node_modules + edits)")
    p.add_argument("--json", action="store_true", help="Výstup jako JSON (pro skripty)")
    args = p.parse_args()

    from tool.cli._compat import exit_if_project_missing
    from tool.cli.ux import die, emit  # lazy: ux nepatří k jádru extrakce
    try:
        out = extract(
            slug=args.slug, variant_name=args.variant,
            source_url=args.source_url, repo_url=args.repo_url,
            method_override=args.method, force=args.force,
        )
    except (ExtractionError, ValueError) as exc:
        exit_if_project_missing(exc)
        die(str(exc), f"pflanzer extract --slug {args.slug} --variant {args.variant}")
    lines = [f"Varianta {args.variant}: kód načten ({out.get('method')}), "
             f"{out.get('files_count', '?')} souborů"]
    if out.get("branch"):
        lines.append(f"Větev {out['branch']}")
    emit(out, title=f"Kód varianty {args.variant} načten: {args.slug}", lines=lines,
         next_step=f"`pflanzer quality_gates --slug {args.slug} --variant {args.variant}`",
         as_json=args.json)

if __name__ == "__main__":
    main()
