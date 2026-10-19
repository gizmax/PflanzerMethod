# Autoresearch — Maximize Code Reusability After Pflanzer Sessions

> Status: research v1 · 2026-05-14 · branch `research/code-reusability`

## Goal

**Po 2-3 sezeních Pflanzer metody musí být **co nejvíce kódu** z winning
varianty použitelné v produkci** — bez re-implementace, jen s běžnými
production polish kroky (tests, security, observability).

## Mechanická metrika

Primary: `% LOC z winning variant branche, který doputuje do main bez
významné modifikace` (target: **≥ 80 %**).

Proxy metriky (sledované v `data/method-metrics.json`):
- `gate_score` per session_3 run (váha: tests + security + types = 1.5–2.0×)
- `time_to_handoff_days` (target: ≤ 14 dní wall-clock = 3 sezení v 2 týdnech)
- `handoff_pr_merged_within_7d` (binární success signal post-handoff)
- `rewrite_loc_ratio` (LOC změněné v PR review / total LOC merged)

Anti-metrika (no-go):
- Tým musí re-implement > 50 % kódu = sessions byly jen "alignment", ne shipping
- Critical security finding post-merge = gates byly příliš slabé
- Type errors v prod = TS strict mode nebyl enforced v session

## Scope

**V scope:**
- Vibe-coding session protocol (CC/Codex CLI in-room, 3 worktrees)
- Quality gates (lint/types/tests/security/a11y/build/observability)
- Skeleton scaffold defaults (Vite + React + TS, ESLint, Vitest)
- Charter risk_profile presets (target gate score, throwaway/evolve)
- Handoff package per role (FE/BE/QA/Platform/Data)

**Mimo scope:**
- Změny v Claude Code samotném (out of our control)
- Replace existing methodology dokumentace (jen evolve, ne redesign)
- Plný redesign role catalogu (zafixované, ADR-0003)

## Anti-patterns (z perspektivy 6 měsíců corporate adoption)

1. **"Vibe-coding = throw-away"** — tým generuje kód v Boltu, refactor 2 týdny po
2. **"Test po session"** — gates skipnuté, "doplníme později", nikdy
3. **"Strict TypeScript je překážka"** — vypnuté pro speed, později dluh
4. **"Sandbox secrets v repo"** — `.env` checked in, security incident
5. **"Žádný design system" v greenfield** — 3 varianty mají 3 button stylů
6. **"BE shadow agent" je fikce** — nikdo nepíše OpenAPI paralelně s UI
7. **"Decider override testing"** — "to je MVP, otestujeme post-launch"

## Expert panel (5 perspektiv, 2 vlny)

### Wave 1 (paralelně)
1. **CC-coding-expert** — senior eng, 10+ let s AI assistants, ví jak nastavit prompt aby AI vyrobila reusable code
2. **Vibe-product-expert** — ex-Bolt PdM, ex-v0 user, ví jak product flow přinutí team shippovat
3. **DevEx-expert** — engineering productivity, dotfiles, monorepo lead, ví jak nastavit defaults

### Wave 2 (paralelně po wave 1)
4. **QA-test-architect** — test pyramid, contract tests, mutation testing, ví jak gate signal je actionable
5. **Brownfield-integration-expert** — staff eng v 5+ legacy codebases, ví co prevents merge

## Output formát per expert

Každý expert vrátí markdown soubor v `docs/research/code-reusability/perspectives/<slug>.md`
s těmito sekcemi:

1. **TL;DR** (3 bullet) — 3 největší páky pro 80%+ reusability
2. **Diagnose** — co aktuální Pflanzer flow dělá špatně z této perspektivy
3. **Concrete changes** — 5-10 specifikých technických změn:
   - Co konkrétně změnit (file:line nebo nová concept)
   - Proč to zvýší metric (mechanism)
   - Jak měřit, že to funguje (gate / counter / dashboard)
   - Síla efektu (low / med / high)
4. **Anti-patterns** — co tým NIKDY nedělat (z war stories)
5. **Tool/process recommendations** — konkrétní libs / configs / rituals

## Synthesis output

Po obou wave: `docs/research/code-reusability/synthesis.md` — top 10 cross-cutting
themes seřazených podle:
- síla efektu na gate_score (high → low)
- náklad implementace (low → high)
- počet expertů, kteří doporučili (5 → 1)

Pak ADR `docs/decisions/0009-...` pro vybrané top 3-5 changes.
