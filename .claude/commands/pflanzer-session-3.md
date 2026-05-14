---
description: Session 3 — Production hardening. Extract code z buildru, projet 7 quality gates, vrátit production-ready verdikt + winner. Gate score >= target = většina kódu použitelná.
---

# /pflanzer-session-3 — Production hardening

Argumenty: `$ARGUMENTS` = projekt slug.

Předpoklad: `projects.status = 'handoff'` (= Decider's Go ze Session 2).

## Co tento command dělá

Nový **3-session production path** (vs. původní 2-session exploration):
- Session 1 (in-room) = explore — generujeme 2-3 funkční varianty.
- Session 2 (decisional) = decide — Decider Go/Iterate/Kill.
- **Session 3 (hardening) = ship** — extract → gate → produktion-ready verdict.

Pod kapotou:
1. Pro každou shortlist variantu: **extract** code z Bolt/v0/Lovable
   (přes GitHub URL) nebo skeleton scaffold.
2. **Run 7 quality gates** na každém extracted projektu:
   lint / types / tests / security / a11y / build / observability.
3. Aggregate **gate_score 0-100**, porovnat s `production_readiness_target`
   z Charteru (default 80).
4. Vyber **winner** (highest gate_score; tie-break = Session 1 preference_score).
5. Pokud winner.score >= target → **production-ready**. Většina kódu použitelná.
6. Pokud ne → konkrétní list, co dofixovat (per gate fail).

## Jak postupuj

### Krok 1 — Validace + GitHub URL prompt

Zjisti aktuální shortlist (z Session 1 variants TOP-N).

Pro každou variantu se zeptej Decidera:

```
AskUserQuestion: "Variant A — máš GitHub URL z Boltu/v0/Lovable?"
options:
  - "Ano, vlož URL" [text input → https://github.com/user/repo]
  - "Ne, použij skeleton (tým doplní ručně)"
  - "Cursor — code už v lokálním repu (manual paste)"
```

### Krok 2 — Spusť hardening run

Sestav JSON spec:

```json
{
  "repo_urls": {
    "A": "https://github.com/team/onboarding-fast-a",
    "C": "https://github.com/team/onboarding-smart-c"
  },
  "method_overrides": {
    "B": "skeleton"
  }
}
```

Spusť:

```bash
python3 tool/cli/session_3.py --slug $ARGUMENTS \
  --repo-urls "$(cat /tmp/<slug>-repos.json | jq -c .repo_urls)" \
  --method-overrides "$(cat /tmp/<slug>-repos.json | jq -c .method_overrides)"
```

### Krok 3 — Vyhodnocení & Decider call

Stdout obsahuje:
- `winner` s `gate_score`, `production_ready` flag, `local_path`, `next_step`
- `per_variant[]` s každou variantou + score + status

Ukaž týmu na velký TV:

```
Variant A (v0)      → gate score 85/100  🚀 ready
Variant C (lovable) → gate score 72/100  ⚠ pilot-only
```

Pokud `production_ready=true`:
```
✅ Winner: Variant A. Většina kódu v extracted/{slug}/A/ je použitelná.
   Next: /pflanzer-handoff $ARGUMENTS → per-role package s odkazy na soubory.
```

Pokud `production_ready=false`:
- Ukaž failed gates (security/tests = blocker, lint/observability = warn).
- Zeptej se Decider:

```
AskUserQuestion: "Score {N}/{target} pod targetem. Co teď?"
options:
  - "Pilot s 5 uživateli, paralelně fix gates" (žádný production launch)
  - "Pause — tým 1-2 sprinty harduje, pak re-run /pflanzer-session-3"
  - "Ship anyway (Decider override + rationale do decision logu)"
```

### Krok 4 — Handoff + deploy

Po session 3 (a Decider OK):
```bash
/pflanzer-handoff $ARGUMENTS
```

Handoff package teď bude obsahovat:
- **Skutečné soubory** v `extracted/$ARGUMENTS/<winner>/`, ne TBD placeholders.
- Gate score per file v `data/handoffs/$ARGUMENTS/quality-<variant>.md`.
- Open-PR-ready commit message + reference na Charter target_repo_url.

## Co NEDĚLAT

- **Nepřeskakuj quality gates** kvůli rychlosti — gate fail = production
  bug. Decider override musí mít rationale do logu (DORA / AI Act).
- **Nepřebíj winner** ručně — score je deterministicky weighted (security
  + tests = 2× váha). Pokud Decider nesouhlasí, řešit přes preference_score
  v Session 1, ne tady.
- **Nezapomeň na node_modules** — gates `skipped` pokud `npm install`
  v extracted dir nikdy neběžel. Tým musí ručně pustit `cd extracted/X &&
  npm install` před session 3, nebo se gates skipnou (= score klesne).

## Reference

- `tool/cli/extract.py` (code extractor: git clone / skeleton / manual paste)
- `tool/cli/quality_gates.py` (7 gates + scoring)
- `tool/cli/session_3.py` (orchestrator)
- `data/production_reports/<slug>-readiness.md` (output)
