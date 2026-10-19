---
description: Rozhodnutí (/pm decide, 60–90 min, Decider + jádro) — demo, top 3 spory, Go / Iterate (max 1×) / Kill, decision log do target repa.
---

# Rozhodnutí (`/pm decide`) — 60–90 min

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

Argumenty: `$ARGUMENTS` = projekt slug (jinak `pflanzer status`).

Kdo: **Decider + jádro**, max 5 lidí. Decider u stavby nebyl — začni
10min demem běžících variant na preview. Decider hlasuje **poslední**.
Zástupce bezpečnosti/provozu přizvi jen při otevřeném critical v jeho kroku.

## Krok 1 — Příprava

```bash
pflanzer session_2 prep --slug $ARGUMENTS
```

Ukaž na TV: commitment index, top 3 spory (osa, hlasy per krok cesty,
návrh řešení), počet critical. Chybí feedback? Zpět na `/pm feedback`.

## Krok 2 — Critical

Každý otevřený `critical` projdi: opraveno / varianta ven / Decider
override (rationale povinné). **Dokud je critical na vítězi otevřený, Go
nejde zapsat** — tool to odmítne. Iterate je povolen (opraví ho).

## Krok 3 — Spory a hlasování

Top 3 spory: AI navrhuje řešení, nerozhoduje. Neznámý spor rozhodne
Decider s rationale. Silent voting jádra, Decider poslední.

## Krok 4 — Rozhodnutí

AskUserQuestion Decideru: **Go / Iterate / Kill** + rationale (1–2 věty,
povinné). Při Go vyber vítěze.

```bash
pflanzer session_2 decide --slug $ARGUMENTS go --winner A --rationale "<1–2 věty>"
pflanzer session_2 decide --slug $ARGUMENTS go --winner A --rationale "…" --override-critical "<důvod>"
pflanzer session_2 decide --slug $ARGUMENTS iterate --rationale "…" --iterate-focus "<co změnit>"   # max 1×
pflanzer session_2 decide --slug $ARGUMENTS kill --rationale "…"
# critical vyřešen jinak než overridem:
pflanzer session_2 resolve --slug $ARGUMENTS --feedback-id <id> --note "<jak>"
```

- **Iterate** = jedno další Build kolo (max 1×). Druhý Iterate tool
  odmítne — problém je špatně zadaný, zpět na Kickoff.
- Decider nemůže rozhodnout → eskalace dle ADR-0001.
- Tool zapíše **decision log do target repa** `.pflanzer/decisions/<slug>.md`
  — **commitni ho** (kdo, kdy, co, proč zůstane v gitu).

## Krok 5 — Výstup a další krok

Rozhodnutí + rationale, vítěz, počet critical, cesta k decision logu.
**Jeden** další krok:

- Go → `/pm ship <slug>` — vývojáři + provoz (checkpoint 20 min)
- Iterate → `/pm build <slug>` — jádro, jen to, co se mění
- Kill → hotovo; krátká retro do decision logu

## Co NEDĚLAT

- Nepřebíjej Decidera; nezapomeň rationale (audit).
- Nedovol druhý Iterate.
- Nezapomeň commitnout decision log.

## Reference

- `docs/methodology/06-session-2.md`, `docs/decisions/0001-decider-model.md`
