# ADR-0009 — Worktree musí být v target repu (P0 fix code-reusability)

> Status: Accepted · 2026-05-14
> Autor: research/code-reusability autoresearch (5 perspektiv) → synthesis
> Související ADR: 0005 (Throw-away vs evolve), 0008 (Tool form-factor Hybrid)

## Kontext

Před touto změnou Pflanzer slash command `/pflanzer` doporučoval:

```bash
git worktree add ../proto-${SLUG}-A -b feat/${SLUG}-A
cd ../proto-${SLUG}-A && claude
```

Problém: `git worktree add` se spouští z **PflanzerMethod meta-repu**
(z `~/Documents/PflanzerMethod/`), takže worktree je sourozenec meta-toolu,
ne target zákazníkova projektu. Když Claude Code v této worktree spustí,
vidí jako contextual repository **PflanzerMethod**, ne target. Generuje code,
který fits PflanzerMethod conventions, ne target conventions.

**Důsledek pro autoresearch metric "% LOC merged without modification":**
v podstatě 0 % — žádný kód z těchto worktreeí nepoputuje do target main bez
kompletního rewrite, protože:
- Importuje neexistující `tool/cli/...` moduly
- Píše Python místo target stacku (TS/Go/whatever)
- Ignoruje target ESLint, design tokens, komponenty
- Je v branchi `feat/<slug>-A` v meta-repu, ne v target repu

Bez fixu jsou všechny ostatní quality gates / templates / prompty placebo.

## Rozhodnutí

1. **Nový tool**: `tool/cli/worktree.py` s `setup --slug X` příkazem.
2. **Cache target repos** v `~/.pflanzer/targets/<repo-slug>/` — full clone
   (ne shallow, AI potřebuje history pro pochopení patterns).
3. **3 worktrees** A/B/C jako siblings cached clonu, branche
   `pflanzer/<slug>-A` (Pflanzer-namespaced, aby nekolidovaly s běžnými feat/).
4. **Auto-detect package manager** z `packageManager` field v target
   `package.json`, pak install per worktree (`pnpm i --frozen-lockfile` /
   `yarn install --frozen-lockfile` / `npm ci`).
5. **Pre-flight check** v `extract.py`: `git remote get-url origin` v worktree
   musí matchovat `projects.target_repo_url`. Jinak fail-loud s actionable
   message "spusť `tool/cli/worktree.py setup` first".
6. **Mandatory `target_repo_url`** v Charteru pro `risk_profile in (pilot, production)`.
   `quick_session.bootstrap()` raises ValueError jinak.
7. **Update `/pflanzer` slash command** — KROK setup volá `worktree.py setup`,
   ne raw `git worktree add`.

## Konsekvence

### Pozitivní
- AI vidí target repo conventions od commit 0 → reuse skok ~0 % → ~75 % per
  perspektiva 05 (brownfield-integration).
- Pre-flight check chytá "tým spustil session bez worktree setup" před
  ztrátou času.
- Cached clone = druhá session na stejném repu start time klesne z ~3 min na
  ~30 s (jen `git fetch`).
- `pflanzer/<slug>-X` branch namespace = jasný origin, nesměšuje se s
  team's normal feature branches.

### Negativní / cost
- Vyžaduje `target_repo_url` v Charteru — pro úplně greenfield projekty
  (žádný existující repo) zatím není elegantní fallback. Workaround: tým
  vytvoří prázdný GitHub repo před session.
- Cached clones zaberou disk space (`~/.pflanzer/targets/`) — pro ~50
  repos cca 1-5 GB. Acceptable.
- Pokud target repo má multi-package structure (monorepo), worktree je na
  root úrovni — variant musí pracovat v `apps/<app>/` cestě. To je OK pro
  většinu projektů, ale Nx/Turborepo orgs možná chtějí budoucí
  `--workspace=` flag.

### Riziko: tým zapomene spustit worktree.py
Mitigace: pre-flight check v `extract.py` je hard fail. `quick_session.bootstrap()`
hlásí požadavek do handoff zprávy. README + slash command instrukce.

## Alternativy zvážené

1. **Klonovat target každou session jako fresh** — odmítnut, plýtvá time
   + disk; cache je správný kompromis.
2. **Použít `git submodule` místo worktree** — odmítnut, submodule mají
   horší DX, AI je často mate.
3. **Ponechat worktree v meta-repu, jen lépe instruovat AI** — odmítnut,
   prompt engineering nikdy nepřebije fyzikální location kódu. AI nemůže
   importovat z `target_repo_url` magic, musí mít files lokálně.

## Související

- Autoresearch synthesis: `docs/research/code-reusability/synthesis.md` § Sprint 1
- Perspektiva 01 (CC-coding) C1: "Skeleton must be a clone of target repo"
- Perspektiva 05 (Brownfield-integration) C1: "P0 catastrophic" finding
- Issue trackable jako: tato ADR
