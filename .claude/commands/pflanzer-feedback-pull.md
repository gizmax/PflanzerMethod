---
description: Async (/pm feedback, 3–5 dní) — sběr a agregace feedbacku zástupců (hub nebo offline), audit discovery debtu, blokace při otevřeném critical.
---

# Async (`/pm feedback`) — feedback zástupců

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

Argumenty: `$ARGUMENTS` = projekt slug (jinak `pflanzer status`).

Kdo: všichni zástupci 6 kroků, ~15 min denně na preview URL variant.
Builder zapracovává připomínky.

## Krok 1 — Kde se feedback sbírá

**Web hub** (jedním příkazem, sdílí DB s CLI):

```bash
pflanzer hub                    # http://localhost:8000/method/
pflanzer hub --host 0.0.0.0     # dostupné kolegům ve firemní síti
```

Zástupci tam u každé varianty kliknou na preview a zapíšou feedback.

**Bez hubu (offline)** — hub není povinný. Kdo klikal na preview a feedback nezadal v hubu,
zapíše ho přímo (ty to můžeš udělat za něj podle jeho slov):

```bash
pflanzer feedback add --slug $ARGUMENTS --variant A --role <krok/role> \
  --severity critical|major|minor --text "<co a proč>"
pflanzer feedback list --slug $ARGUMENTS
```

`critical` = brání nasazení (bezpečnost, právo, data, rozbitý hlavní tok).
Nezneužívat; kdo dává critical, píše proč.

## Krok 2 — Agregace

```bash
pflanzer feedback_pull --slug $ARGUMENTS
```

Vrací `summary_path`, `feedback_count`, `critical_flags`. Při
`feedback_count == 0` zastav a připomeň preview URL a termín; nepouštěj
audit na prázdná data. Chybí hlasy zástupců některých kroků? Jmenuj je.

## Krok 3 — Audit discovery debtu

Pokud `feedback_count > 0`, spusť sub-agenta `discovery-debt-detector`
(read-only) nad summary a Kickoff zadáním; výstup ulož do
`feedback/<slug>-debt.json` ve výstupní složce (`pflanzer data`).

## Krok 4 — Otevřené critical

Otevřený `critical` na vítězné variantě **blokuje Go** na Rozhodnutí (Iterate ho může opravit).
Ukaž ho s autorem a zeptej se přes AskUserQuestion: opravit teď (builder),
varianta ven ze shortlistu, nebo nechat na Decidera (override vyžaduje
rationale v decision logu).

## Krok 5 — Výstup a další krok

Tabulka: feedback podle kroku cesty a závažnosti, top 3 spory, critical,
verdikt debtu. Na konci **jeden** krok:

> Další krok: `/pm decide <slug>` — přizvi Decidera, 60–90 min.

(Při critical bez řešení: nejdřív oprava a znovu `/pm feedback <slug>`.)

## Co NEDĚLAT

- Nezakrývej critical v průměrech.
- Nepouštěj audit na 0 feedbacku.
- Nepřebíjej audit — je to vstup pro Decidera, ne verdikt.

## Reference

- `docs/methodology/05-mezi-sessions.md` (rozšířená reference)
- `.claude/agents/discovery-debt-detector.md`
