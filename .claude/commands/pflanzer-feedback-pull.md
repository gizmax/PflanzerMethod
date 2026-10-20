---
description: Sběr feedbacku (Async, /pm feedback, 3–5 dní) — sběr a agregace feedbacku zástupců (hub nebo offline), audit discovery debtu, blokace při otevřeném critical.
---

# Sběr feedbacku (`/pm feedback`) — feedback zástupců

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

> **Argumenty:** `<slug>` = **první slovo** z `$ARGUMENTS` (zbytek je kontext od uživatele —
> rozhodnutí, jména, poznámky). Bez slugu: `pflanzer status`. Do příkazů dosazuj jen `<slug>`.
> **Zápisy dělá výhradně tool** (`pflanzer …`) — decision log, checkpointy ani DB nikdy needituj ručně.


Kdo: všichni zástupci 6 kroků, ~15 min denně na preview URL variant.
Builder zapracovává připomínky.

## Krok 1 — Kde se feedback sbírá

**Web hub** (jedním příkazem, sdílí DB s CLI):

```bash
pflanzer hub                    # http://localhost:8000/method/
pflanzer hub --host 0.0.0.0 --password …   # kolegům ve firemní síti (heslo povinné)
```

Na `localhost` hub běží bez přihlášení.

Zástupci tam u každé varianty kliknou na preview a zapíšou feedback.

**Bez hubu (offline)** — hub není povinný. Kdo klikal na preview a feedback nezadal v hubu,
zapíše ho přímo (ty to můžeš udělat za něj podle jeho slov):

```bash
pflanzer feedback add --slug <slug> --variant A --role <krok/role> --by "<jméno autora>" \
  --severity critical|major|minor --text "<co a proč>"
pflanzer feedback list --slug <slug>
```

Závažnost: `critical` (Kritické) · `major` (Důležité) · `minor`
(Drobné). `critical` = brání nasazení (bezpečnost, právo, data,
rozbitý hlavní tok). Nezneužívat; kdo dává critical, píše proč.

Dobrý feedback: **co jsem zkoušel → co se stalo → co jsem čekal → co
navrhuji**; jeden feedback = jeden problém. Kdo z oken ještě nic nenapsal,
dostane připomínku; mlčení nevetovací role po termínu = souhlas, u
bezpečnosti ne.

## Krok 2 — Agregace

```bash
pflanzer feedback_pull --slug <slug>
```

Vrací `summary_path`, `feedback_count`, `critical_flags`. Souhrn (`<slug>-summary.md`)
obsahuje **plné texty připomínek** po variantách (critical → major → minor, vyřešené na
konci); stejné řádky (zkrácené na ~120 znaků) ukazuje `pflanzer feedback list`. Při
`feedback_count == 0` zastav a připomeň preview URL a termín; nepouštěj
audit na prázdná data. Chybí hlasy zástupců některých kroků? Jmenuj je.

## Krok 3 — Audit discovery debtu

Pokud `feedback_count > 0`, spusť sub-agenta `discovery-debt-detector`
(read-only) nad summary (musí obsahovat sekci „Připomínky podle varianty (plné
texty)“ — bez textů audit nemá z čeho posoudit, které tvrzení jsou holé) a Kickoff
zadáním; výstup ulož do
`feedback/<slug>-debt.json` ve výstupní složce (`pflanzer data`).

## Krok 4 — Otevřené critical

Otevřený `critical` na vítězné variantě **blokuje Go** na Rozhodnutí (Iterate ho může opravit).
Ukaž ho s autorem a zeptej se přes AskUserQuestion: opravit teď (builder),
varianta ven ze shortlistu, nebo nechat na Decidera (override vyžaduje
rationale v decision logu).

## Krok 5 — Výstup a další krok

Ukaž lidský výstup toolu a předej jeho **Doporučení**. Tabulka: feedback podle kroku cesty a závažnosti, top 3 spory, critical,
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
