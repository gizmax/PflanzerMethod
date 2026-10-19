---
description: Ship (/pm ship) — quality gates jen na vítěze, skóre X/100 (práh pilot 80 / production 85), checkpoint provozu, PR do target repa.
---

# Ship (`/pm ship`) — 1–2 dny

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

Argumenty: `$ARGUMENTS` = projekt slug (jinak `pflanzer status`).

Ship není session, je to práce vývojářů s automatickými branami + 20min
checkpoint provozu. Předpoklad: Rozhodnutí skončilo **Go** s vítězem.
Krok Provoz musí mít jméno; jinak se zeptej, kdo deploy převezme.
(`/pflanzer-session-3` a `tool/cli/session_3.py` jsou jen technické názvy
tohoto kroku.)

Kód vítěze je ve **worktree target repa** (`~/.pflanzer/targets/<slug>-<X>/`,
branch `pflanzer/<slug>-<X>`, ADR-0009) — Ship gate nic nekopíruje a na
GitHub URL se neptá. Ověř, že worktree existuje a patří do target repa:
`pflanzer worktree verify --slug <slug> --cwd <worktree>`. Chybí-li, řekni
týmu, ať spustí `pflanzer worktree setup --slug <slug>` a vítěze commitne.
URL buildru (Bolt / v0 / Lovable) je jen fallback u `--prefer-hosted`
projektů (`--repo-urls`); skeleton pro `pilot` / `production` nikdy.

## Krok 1 — Gates jen na vítěze

```bash
pflanzer session_3 --slug $ARGUMENTS
pflanzer session_3 --slug $ARGUMENTS --variants A    # výslovně vítěz
```

Poražené varianty se nehodnotí ani nehardenují. Tool pustí gates (lint,
typy, testy, security, a11y, build, observability) v branchi vítěze
a vrátí **skóre X/100**.

Práh: **pilot 80, production 85** (podle risk profilu z Kickoffu).
Security a testy mají dvojnásobnou váhu.

Pod povrchem:

- **Adaptér `pflanzer.gates.yml`** — příkazy gates se berou z adaptéru
  v **base branchi** target repa, ne z branche vítěze (agent ve worktree ho
  mohl „zjednodušit"; report varuje „adapter modified in variant branch —
  ignored"). Bez adaptéru autodetekce stacku; pro Java / .NET / Go
  `pflanzer init gates-template --path <repo>`
  (`tool/templates/README-gates.md`).
- **Minimum gates pro verdikt** — „připraveno" jen když běžely aspoň 4 gates
  včetně `build` a `tests`; jinak `blocked_by: gates:insufficient (…)`.
  Neoverriduje se: bez buildu a testů není co podepsat.
- **Triage hard gate** (`pilot` / `production`, vždy u stupně Full) —
  všechny triage tracky musí být `ok`, jinak `production_ready = false`
  a `blocked_by` odkáže na `/pm triage <slug>`. Override jen Decider přes
  `pflanzer session_3 --slug <slug> --override-triage --rationale "…"`
  (zápis do decision logu).

## Krok 2 — Vyhodnocení

- Skóre ≥ práh → připraveno; ukaž gates a co je warning.
- Skóre < práh → konkrétní seznam, co dopravit (security/tests = blocker,
  lint/observability = warning). AskUserQuestion Decideru: pilot s malou
  skupinou a paralelní oprava / pauza a znovu `/pm ship` / Ship i přesto
  (override + rationale do decision logu). Neuhýbej: gate fail = pozdější bug.

## Krok 3 — Checkpoint provozu (20 min)

Zástupce kroku Provoz potvrdí: deploy plán, monitoring, kdo drží on-call,
rollback, strop nákladů. Podepiš (zapíše se i do decision logu v target repu):

```bash
pflanzer checkpoint --slug $ARGUMENTS provoz --by "<jméno>" --note "<deploy, monitoring, rollback>"
pflanzer checkpoint --slug $ARGUMENTS --list    # stav všech oken
```

Ship pilotu/production blokuje, dokud nejsou podepsaná všechna okna
(zadání podepisuje Kickoff sám). Plný triage (`/pm triage`) jen regulované.

## Krok 4 — PR a další krok

PR vítěze do `main` target repa přes běžnou pipeline a review; poražené
větve smaž. AI asistenci značí jen trailery (`Pflanzer-Variant`,
`Pflanzer-Session: ship`, `AI-Assisted`) a PR labely `pflanzer`,
`ai-generated`, `pflanzer:<slug>` — autor commitu je vývojář u klávesnice,
nikdy AI (`Co-Authored-By` s AI ne); `/pm handoff` je vygeneruje do SHIP.md
spolu s read-only kontrolou trailerů (AI provenance, N11) a viditelností
AI nákladů (tokeny Claude Code per varianta a za cyklus; USD jen s ceníkem,
`tool/templates/README-ai-usage.md`). **Jeden** další krok:

> Další krok: `/pm handoff <slug>` — balíček per role a metriky pilotu;
> po merge vítěze `/pm retro <slug>` (měření outcome T+7/30/60/90).

## Co NEDĚLAT

- Nehodnoť poražené varianty.
- Nepřebíjej skóre ručně; override jen přes Decidera s rationale.
- Nemerguj bez checkpointu provozu.
- Neupravuj `pflanzer.gates.yml` v branchi vítěze — Ship gate ho ignoruje.
- Neobcházej triage gate ústním „security to ví" — jen `--override-triage`
  s rationale.

## Reference

- `docs/decisions/0021-mala-skupina-cela-cesta.md`
- `docs/methodology/07-handoff-do-vyvoje.md` § AI code provenance
- `docs/decisions/0009-worktree-in-target-repo.md`
- `tool/cli/session_3.py`, `tool/cli/quality_gates.py`, `tool/cli/handoff_pr.py`
