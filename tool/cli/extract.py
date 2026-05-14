"""Extract code z vibe-coding tools do `extracted/<slug>/<variant>/`.

Cíl: po Session 1/2 mít skutečný kód v repu (ne jen preview URL), aby
Session 3 mohla projet quality gates a tým ho mohl opravdu použít.

Strategie podle builderu:
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
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

EXTRACTED_DIR = REPO_ROOT / "extracted"
SUPPORTED_BUILDERS = {"claude-code", "codex-cli", "v0", "bolt", "lovable",
                      "cursor", "manual", "stitch", "figma-make"}


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
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write \\"src/**/*.{ts,tsx,css}\\"",
    "test": "vitest run",
    "test:watch": "vitest",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^14.2.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "eslint": "^8.57.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "jsdom": "^24.0.0",
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
    "src/test/setup.ts": """import '@testing-library/jest-dom';
""",
    "src/App.test.tsx": """import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
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
});
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
- Production: pouze po /pflanzer-session-3 + handoff package.
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
        raise RuntimeError(f"git clone failed: {res.stderr.strip()}")
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
    skip_dirs = {"node_modules", "dist", "build", ".next", "coverage", ".venv"}
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
# Main extract
# --------------------------------------------------------------------------


def extract(
    *, slug: str, variant_name: str,
    source_url: str | None = None, repo_url: str | None = None,
    method_override: str | None = None, force: bool = False,
) -> dict[str, Any]:
    """Extract one variant's code into extracted/<slug>/<variant>/.

    Args:
        slug: project slug.
        variant_name: A / B / C.
        source_url: prototype preview URL (for audit).
        repo_url: GitHub URL pokud user pushl z builder.
        method_override: force 'skeleton' / 'git_clone' / 'manual_paste'.

    Returns dict s extracted_id, local_path, files_count, total_loc, method.
    """
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, name FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id = int(proj[0])

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
            raise ValueError(f"Variant '{variant_name}' not found in Session 1 for {slug}.")
        variant_id, builder, prototype_url = int(variant[0]), variant[1], variant[2]

    source_url = source_url or prototype_url

    # Decide extraction method
    if method_override:
        method = method_override
    elif builder in ("claude-code", "codex-cli"):
        # Code už je v repu (worktree feat branch). Jen ho zaregistrujeme.
        method = "in_repo_branch"
    elif repo_url and _validate_github_url(repo_url):
        method = "git_clone"
    elif builder in ("stitch", "figma-make"):
        method = "skeleton"  # UI-only builders → fall back to skeleton
    elif builder == "cursor":
        method = "manual_paste"  # cursor edits are in-place; user assigns local path
    else:
        method = "skeleton"

    dest = EXTRACTED_DIR / slug / variant_name

    notes = []
    if method == "in_repo_branch":
        # Code is already in repo's feat branch (CC/Codex psali přímo).
        # Default branch convention: feat/<slug>-<variant>. User může override
        # přes repo_url (formát: 'branch:feat/...' nebo abs path).
        branch_name = repo_url.replace("branch:", "") if repo_url and repo_url.startswith("branch:") else f"feat/{slug}-{variant_name}"
        # Try git worktree at sibling path
        worktree = REPO_ROOT.parent / f"proto-{slug}-{variant_name}"
        if worktree.exists():
            dest = worktree  # Real on-disk path
            files, loc = _count_files(dest)
            notes.append(
                f"Registered in-repo branch `{branch_name}` at {dest} "
                "(worktree). Code napsali Claude Code / Codex CLI přímo."
            )
        else:
            # Fallback: branch v hlavním repu
            dest = REPO_ROOT
            files, loc = (0, 0)
            notes.append(
                f"Branch `{branch_name}` registrován jako in-repo. "
                f"Worktree {worktree} neexistuje — code je na branchi v hlavním repu. "
                "Quality gates poběží na celém repu (může mít hluk)."
            )
    elif method == "git_clone":
        files, loc = _git_clone(repo_url, dest, force=force)
        notes.append(f"Cloned from {repo_url}" if force or not dest.exists() else f"Reused existing {dest}")
    elif method == "skeleton":
        files, loc = _scaffold_skeleton(slug, variant_name, dest, force=force)
        notes.append(
            "Scaffolded production-grade skeleton (Vite + React + TS + Vitest + ESLint)."
            f" Tým musí překopírovat komponenty z {source_url}."
        )
    elif method == "manual_paste":
        files, loc = _scaffold_skeleton(slug, variant_name, dest, force=force)
        notes.append(
            "Skeleton ready. Tým paste-uje code z Cursoru / lokálního repa do dest."
        )
    elif method == "builder_api":
        raise NotImplementedError(
            "builder_api extraction není v MVP — zatím použij git_clone nebo manual_paste."
        )
    else:
        raise ValueError(f"Unknown extraction_method '{method}'")

    # Persist
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO extracted_code (
                variant_id, source_url, source_repo_url, local_path,
                extraction_method, files_count, total_loc, extracted_by, notes_md
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (variant_id, source_url, repo_url, str(dest.relative_to(REPO_ROOT)),
             method, files, loc, current_actor(), "\n".join(notes)),
        )
        extracted_id = cur.lastrowid

        audit(
            conn,
            action="extract.code",
            target_type="variant",
            target_id=variant_id,
            payload={
                "slug": slug, "variant": variant_name,
                "method": method, "files": files, "loc": loc,
            },
        )

    return {
        "extracted_id": extracted_id,
        "slug": slug,
        "variant": variant_name,
        "builder": builder,
        "method": method,
        "local_path": str(dest.relative_to(REPO_ROOT)),
        "absolute_path": str(dest),
        "files_count": files,
        "total_loc": loc,
        "notes": notes,
        "next_step": (
            f"cd extracted/{slug}/{variant_name} && npm install && npm run dev"
            if (dest / "package.json").exists()
            else f"Inspect {dest}/ a doplň missing parts ručně."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--variant", required=True, help="A / B / C")
    p.add_argument("--source-url", default=None,
                   help="Preview URL z buildru (default: read z DB)")
    p.add_argument("--repo-url", default=None,
                   help="GitHub URL pokud user pushl z buildru")
    p.add_argument("--method", default=None,
                   choices=["git_clone", "manual_paste", "builder_api", "skeleton"],
                   help="Force specific extraction method")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing extracted dir (DELETES node_modules + edits)")
    args = p.parse_args()

    out = extract(
        slug=args.slug, variant_name=args.variant,
        source_url=args.source_url, repo_url=args.repo_url,
        method_override=args.method, force=args.force,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
