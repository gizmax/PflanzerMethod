# ADR-0010 — SHIP.md jako primární výstup Ship + význam „/pm handoff"

**Pflanzer Method | pflanzer.cz/method**

**Status:** Accepted · 2026-10-19 (zpětně sepsáno; na „ADR-0010" se odkazovalo
od 2026-05, soubor chyběl)
**Související:** ADR-0005 (evolve default), ADR-0009 (worktree v target repu),
ADR-0016 (mob mode), ADR-0021 (malá skupina, celá cesta)

## Kontext

1. Ship vytváří víc souborů: per-role balíček (8 souborů), quality reporty,
   metriky pilotu. Tým potřebuje **jednu stránku**, ze které otevře PR.
2. Glossary zakazuje slovo *„handoff package"* (implikuje „hodíme to přes zeď
   vývoji"), ale uživatelský příkaz se jmenuje `/pm handoff`. Rozpor.
3. Na „ADR-0010" se v repu odkazovalo třemi různými významy (SHIP.md,
   co-facilitator, post-mortem disclosure), soubor neexistoval.

## Rozhodnutí

- **`SHIP.md` je primární výstup Ship** (1 stránka): vítěz (větev + SHA),
  gate skóre X/100 vs. práh, odpovědnosti (Decider, branch owner),
  příkaz `gh pr create`, checkpoint provozu, sekce „Změř po 30 dnech".
  Per-role soubory jsou doplněk pro audit (= *sign-off package* v glossary).
- **`/pm handoff` zůstává jako název příkazu** (stabilní rozhraní), ale
  znamená **předání vítězné větve do běžného vývojového procesu přes PR**,
  ne re-implementaci. V textech dál „sign-off package", ne „handoff package".
- Zbylé dva odkazy na „ADR-0010" (co-facilitator, post-mortem disclosure)
  nikdy nebyly sepsány → nahrazeny odkazem na role catalog #3, resp.
  „plánované ADR".
- Mob mode ADR (dříve druhé „0011") přečíslováno na **ADR-0016**.

## Důsledky

- Jedna stránka pro PR; audit zůstává dostupný, ale nepřekáží.
- Číslování ADR je jednoznačné (0011 = Method Decider, 0016 = mob mode,
  0010 = tento záznam).
