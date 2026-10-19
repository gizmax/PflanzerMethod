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

## Krok 2 — Vyhodnocení

- Skóre ≥ práh → připraveno; ukaž gates a co je warning.
- Skóre < práh → konkrétní seznam, co dopravit (security/tests = blocker,
  lint/observability = warning). AskUserQuestion Decideru: pilot s malou
  skupinou a paralelní oprava / pauza a znovu `/pm ship` / Ship i přesto
  (override + rationale do decision logu). Neuhýbej: gate fail = pozdější bug.

## Krok 3 — Checkpoint provozu (20 min)

Zástupce kroku Provoz potvrdí: deploy plán, monitoring, kdo drží on-call,
rollback, strop nákladů. Zapiš do decision logu v target repu (commit).

## Krok 4 — PR a další krok

PR vítěze do `main` target repa přes běžnou pipeline a review; poražené
větve smaž. **Jeden** další krok:

> Další krok: `/pm handoff <slug>` — balíček per role a metriky pilotu.

## Co NEDĚLAT

- Nehodnoť poražené varianty.
- Nepřebíjej skóre ručně; override jen přes Decidera s rationale.
- Nemerguj bez checkpointu provozu.

## Reference

- `docs/decisions/0021-mala-skupina-cela-cesta.md`
- `docs/methodology/07-handoff-do-vyvoje.md`
