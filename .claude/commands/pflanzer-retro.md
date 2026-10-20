---
description: Retro (/pm retro) — měření outcome po Ship: % LOC vítěze v produkci, days-to-prod, T+7/30/60/90 readouty a připomínky.
---

# Retro (`/pm retro`) — měření outcome po Ship

> **Branding:** Každý user-facing výstup tohoto commandu začíná brand line
> **`Pflanzer Method | pflanzer.cz/method`** (první řádek, pak prázdný řádek).

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

> **Argumenty:** `<slug>` = **první slovo** z `$ARGUMENTS` (zbytek je kontext od uživatele —
> rozhodnutí, jména, poznámky). Bez slugu: `pflanzer status`. Do příkazů dosazuj jen `<slug>`.
> **Zápisy dělá výhradně tool** (`pflanzer …`) — decision log, checkpointy ani DB nikdy needituj ručně.

Výstup toolu je lidský (co se stalo → jeden další krok → Doporučení); ukaž ho
a předej Doporučení. `--json` jen pro čtení polí.

Argumenty: `$ARGUMENTS` = `<slug> [measure|record|report|reminders]` —
podpříkaz volitelný; bez něj command sám pozná, co chybí (viz Krok 1).

Předpoklad: `projects.status = 'handoff'` a existuje
`data/handoffs/<slug>/SHIP.md` (Ship proběhl, PR s větví vítěze
`pflanzer/<slug>-<X>` byl otevřen v target repu). Retro je poslední krok
cesty za Handoffem a **nepatří do jádra 5 kroků** — spouští ho ten, kdo
vlastní měření (zástupce kroku Produkt nebo Provoz), ne celá skupina.

## Co tento command dělá

Metoda tvrdí **„≥ 80 % LOC vítěze jde do produkce beze změny, prod deploy
do 14 dnů"**. Tento command to měří z target repa a ukládá do tabulky
`outcomes` (`data/pflanzer.db`), takže PflanzerIndex (ADR-0014) a sekce
„Co měřit" v `docs/zacni.md` stojí na datech, ne na dojmech. Tohle je
čtvrtá metrika vedle čtyř, které zapisuje Handoff (čas Kickoff → merge, gate
score vítěze, kola Iterate, přežití kódu 30 dní): **kolik kódu vítěze
opravdu žije v produkci a co se s ním stalo za 7 / 30 / 60 / 90 dní.**

| Podpříkaz | Co udělá | Milník |
|-----------|----------|--------|
| `measure` | Najde vítěze (stejné pravidlo jako SHIP.md), lokalizuje clone target repa (`$(pflanzer data)/targets/<repo>/`), `git fetch`, spočítá `loc_winner`, `loc_merged_unchanged`, `loc_reused_pct`, `days_to_prod`, `winner_commits` | `ship` |
| `record` | Ruční readout (bugy, leading/lagging metrika, rework, verdikt) | `t7` / `t30` / `t60` / `t90` |
| `report` | `data/retro/<slug>-retro.md` + porovnání s cíli (reuse ≥ 80 %, days-to-prod ≤ 14 → jinak FLAG) | — |
| `reminders` | T+7/30/60/90 od Go v Rozhodnutí s ownery z Charteru jako `.ics` (`--format ics`), Markdown checklist (`--format md`, default) nebo `gh issue create` příkazy (`--format gh-issues`) | — |

Doporučené názvy metrik pro `record`:

| Milník | Metrika | Co zapsat |
|--------|---------|-----------|
| T+7 | `t7_bugs` | Počet bugů na shipnutý kód (issues s labelem `pflanzer:<slug>`) |
| T+7 | `t7_hotfix_commits` | Hotfix commity do shipnutých cest |
| T+30 | `t30_leading_metric` | Readout leading metriky z Charteru |
| T+30 | `t30_handoff_acceptance_pct` | % acceptance criteria splněných v produkci / přijetí handoffu dev týmem |
| T+60 | `t60_rework_pct` | % shipnutých LOC přepsaných od merge |
| T+90 | `t90_lagging_metric` | Lagging metrika vs success criterion |
| T+90 | `t90_go_iterate_kill` | Verdikt readoutu: 1 = go, 0.5 = iterate, 0 = kill |

## Jak postupuj

### Krok 1 — Stav

```bash
pflanzer retro report --slug <slug>
```

JSON vrátí `checks` (reuse, days_to_prod: `ok` / `flag` / `missing`)
a `milestones` (`recorded` / `pending` / `overdue`). Podle toho:

- `loc_reused_pct` = `missing` → **Krok 2 (measure)**.
- Nějaký milník `overdue` → **Krok 3 (record)** pro ten milník.
- Připomínky ještě nevygenerované (typicky hned po Ship) → **Krok 4**.

### Krok 2 — Measure (po merge PR vítěze)

Zeptej se na PR a merge commit:

```
AskUserQuestion: "PR vítěze pro {slug} — je už mergnutý?"
options:
  - "Ano, vložím URL PR" [text input → https://github.com/<org>/<repo>/pull/<N>]
  - "Ano, vložím SHA merge commitu" [text input]
  - "Ještě ne" → připomeň, že measure se pouští až po merge; nabídni Krok 4
```

Pokud máš jen PR URL a `gh` na PATH není (nebo není přihlášený), zeptej se
dodatečně na SHA merge commitu (`git log --merges --oneline` v target repu).

```bash
pflanzer retro measure --slug <slug> \
  --pr-url <PR_URL> [--merge-commit <SHA>] [--repo-path <clone>]
```

- Squash merge funguje stejně. Rebase merge: `--merge-commit` = poslední
  commit rebasované série, `--base` = commit, ze kterého vítěz vznikl.
- Chyba „winner branch neexistuje" → branch byla po merge smazaná; obnov ji
  (`git fetch origin pull/<N>/head:pflanzer/<slug>-<X>`) a pusť znovu.
- `measure` je přepočitatelný — opakované spuštění nahradí `ship` rows.

Ukaž týmu `loc_reused_pct`, `days_to_prod` a `per_file` (které soubory
review nejvíc přepsal — to je materiál pro T+30 retro).

### Krok 3 — Record (T+7 / T+30 / T+60 / T+90)

```
AskUserQuestion: "Který readout zapisujeme?"
options:
  - "T+7 — bugy / hotfixy"
  - "T+30 — leading metrika / přijetí handoffu"
  - "T+60 — rework"
  - "T+90 — lagging metrika / verdikt"
```

Pro T+7 bugy spočítej issues (pokud je `gh` k dispozici):
`gh issue list --label pflanzer:<slug> --state all --json number --jq length`.

```bash
pflanzer retro record --slug <slug> --milestone t7 \
  --metric t7_bugs --value <N> --evidence <URL> --notes "<kontext>"
```

Kvalitativní reakce stakeholderů patří do `--notes` u
`t30_handoff_acceptance_pct` (případně `t90_go_iterate_kill`).

### Krok 4 — Reminders (hned po Ship)

```
AskUserQuestion: "Jak chcete připomínky T+7/30/60/90?"
options:
  - "Kalendář (.ics)" → data/retro/<slug>-reminders.ics
  - "Checklist (markdown)"
  - "GitHub issues (vypíšu gh příkazy, spustíte je sami)"
```

```bash
pflanzer retro reminders --slug <slug> --format ics \
  --out data/retro/<slug>-reminders.ics
```

Owneři se berou z Charteru (`reinforcement_t7…t90`); prázdný milník dostane
default ownera z `07-handoff-do-vyvoje.md` § Retro.

### Co měřit a proč (řekni to týmu jednou větou)

- **Přežití kódu** — kolik z kódu vítěze žije v produkci beze změny (cíl ≥ 80 %).
- **Rychlost** — dny od Kickoffu / Go do produkce (cíl ≤ 14).
- **Kvalita po nasazení** — bugy a hotfixy za 7 dní, rework za 60 dní.
- **Dopad** — metrika z Kickoffu za 30 a 90 dní proti číslu, které jsme si dali.
- **AI náklady** a **podíl kroků s AI náhradou** (kolik kroků cesty podepsal
  jen AI draft + člověk) — vstup pro příští pilot.

### Krok 5 — Report + next step

```bash
pflanzer retro report --slug <slug> --md
```

Ukaž report. Pokud je některý cíl `flag`, zapiš do T+30 retro příčinu
(review rework? scope změna? chybějící acceptance criteria?). Připomeň
další krok ve tvaru `/pm retro <slug>` s termínem nejbližšího milníku.

## Co NEDĚLAT

- **Nevymýšlet čísla.** Bez merge commitu `measure` nespouštěj a hodnoty
  neodhaduj — čísla se berou jen z `outcomes`.
- **Nespouštět `gh issue create` automaticky** — `reminders --format gh-issues`
  příkazy jen vypíše; spouští je tým.
- **Nepřepisovat FLAG na úspěch.** Reuse < 80 % nebo days-to-prod > 14 je
  kalibrační data pro metodu, ne selhání týmu — nezaokrouhlovat, nemazat.
- **Neměřit proti meta-repu.** `measure` čte target repo (worktree cache nebo
  `--repo-path`), nikdy PflanzerMethod.

## Reference

- `tool/cli/retro.py` (heuristika v docstringu `measure`)
- `tool/db/schema.sql` — tabulka `outcomes`
- `docs/methodology/07-handoff-do-vyvoje.md` § Retro
- `docs/research/review-2026-09/01-audit-a-navrhy-zlepseni.md` § N4
- `docs/zacni.md` § Co měřit
