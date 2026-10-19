---
description: Handoff (/pm handoff) — balíček per role (PR-ready) + metriky pilotu (čas Kickoff→merge, gate score, Iterate kola, přežití kódu).
---

# Handoff (`/pm handoff`)

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

> **Argumenty:** `<slug>` = **první slovo** z `$ARGUMENTS` (zbytek je kontext od uživatele —
> rozhodnutí, jména, poznámky). Bez slugu: `pflanzer status`. Do příkazů dosazuj jen `<slug>`.
> **Zápisy dělá výhradně tool** (`pflanzer …`) — decision log, checkpointy ani DB nikdy needituj ručně.


Předpoklad: Rozhodnutí = Go a proběhl `/pm ship`. Jinak řekni, který krok chybí.

Ukaž lidský výstup toolu a předej jeho **Doporučení**; `--json` jen pro čtení polí.

## Krok 1 — Generování

```bash
pflanzer handoff --slug <slug>       # balíček per role do výstupní složky
pflanzer handoff_pr --slug <slug>    # PR-ready podklady + metriky pilotu
pflanzer data                            # kde výstupy leží (~/.pflanzer)
```

## Krok 2 — Rozeslání

Pro každý krok cesty vezmi jméno z Kickoffu a dej mu jeho soubor
(vývoj, QA, provoz, bezpečnost & právo, rozhodnutí). Placeholdery TODO
jsou záměr — doplní tým podle kontextu.

## Krok 3 — Metriky pilotu

Ukaž, co tool sesbíral — slouží k vylepšení metody:

- čas Kickoff → merge
- gate score vítěze
- počet kol Iterate
- kolik kódu vítěze přežije 30 dní v `main` (doměř po 30 dnech)

## Krok 4 — Další krok

> Další krok: po merge vítěze `/pm retro <slug>` — změří % LOC vítěze
> v produkci a days-to-prod, hned nastaví připomínky T+7/30/60/90.

Reinforcement podle zadání z Kickoffu (T+7/30/90) drží Decider. Retro je
pod povrchem: hlavní cesta končí Shipem a Handoffem.

## Co NEDĚLAT

- Negeneruj bez Go.
- Nezapisuj osobní údaje do balíčku.
- Nezapomeň na metriky — bez dat se metoda nezlepší.

## Reference

- `docs/methodology/07-handoff-do-vyvoje.md`
- `.claude/commands/pflanzer-retro.md` (`/pm retro`)
