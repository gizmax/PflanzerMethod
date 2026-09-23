---
description: Pflanzer Method — jediný vstupní bod. Bez argumentu detekuje stav projektu a nabídne další krok; se slovesem (start/build/review/decide/ship/…) deleguje na příslušný pflanzer-* command.
---

# /pm — Pflanzer Method router (single entry point)

> **Branding:** Každý user-facing výstup tohoto commandu (úvodní hláška,
> souhrny, status report) začíná brand line:
>
> **`Pflanzer Method | pflanzer.cz/method`**
>
> (první řádek, pak prázdný řádek, pak obsah). Brand line se nikdy nezkracuje
> na „PM" — zkratka je jen v názvu commandu kvůli psaní.

Argumenty: `$ARGUMENTS` = `[sloveso] [slug]` — obojí volitelné.

## Proč tento command existuje

`/pflanzer-*` commandy jsou implementace jednotlivých kroků; jejich názvy
jsou ale dlouhé a příjmení Pflanzer se špatně píše. `/pm` je tenký router:
uživatel si nemusí pamatovat nic než `/pm` — router pozná, kde v cyklu
projekt je, a nabídne další krok.

## Subcommandy (slovesa, ne čísla sessions)

| Sloveso | Deleguje na | Kdy |
|---------|-------------|-----|
| `start` | `/pflanzer-charter` | Nový projekt — Charter wizard (Den 0) |
| `roles` | `/pflanzer-roles` | Výběr rolí po Charteru |
| `triage` | `/pflanzer-triage` | Pre-flight gate před Session 1 |
| `build` | `/pflanzer-session-1` | Session 1 (Lean/Full stupeň) |
| `feedback` | `/pflanzer-feedback-pull` | Stažení mezi-session feedbacku z hubu |
| `decide` | `/pflanzer-session-2` | Rozhodovací session — Go/Iterate/Kill |
| `ship` | `/pflanzer-session-3` | Ship gate — quality gates + SHIP.md (po Session 2 GO) |
| `handoff` | `/pflanzer-handoff` | Per-role handoff package |
| `live` | `/pflanzer` | Quick stupeň, 60–90 min (vše v jednom) |
| `status` | — (řeší router sám) | Přehled stavu projektu/ů |

**Delegace = přečti `.claude/commands/pflanzer-<cíl>.md` přes Read a postupuj
přesně podle něj** (s `$ARGUMENTS` = slug). Nikdy nereimplementuj logiku
cílového commandu po svém.

## Jak postupuj

### 1. Parsuj `$ARGUMENTS`

- První token = sloveso (pokud odpovídá tabulce výše), zbytek = slug.
- Neznámé sloveso → ukaž tabulku subcommandů a zeptej se přes AskUserQuestion.
- Sloveso bez slugu, ale v DB je víc projektů → AskUserQuestion, který projekt.

### 2. Bez argumentů (nebo `status`): autodetekce stavu

Načti projekty:

```bash
sqlite3 data/pflanzer.db "SELECT slug, name, status FROM projects ORDER BY updated_at DESC"
```

- **Žádný projekt** → nabídni `start` (nový projekt) nebo `live`
  (in-room session bez příprav).
- **Jeden projekt** → urči další krok podle stavu (tabulka níže) a potvrď
  přes AskUserQuestion („Projekt X je ve stavu Y → další krok je Z. Spustit?").
- **Víc projektů** → vypiš tabulku (slug / název / stav / další krok)
  a nech uživatele vybrat.

| `projects.status` | Další krok | Poznámka |
|-------------------|-----------|----------|
| `draft` | `start` | Charter nedokončen |
| `charter` | `roles` (pokud `SELECT COUNT(*) FROM roles WHERE project_id=…` = 0), jinak `triage` | |
| `triage` | `build` | Pre-flight prošel |
| `session_1` | `feedback` (pokud `data/feedback/<slug>-summary.md` neexistuje), jinak `decide` | |
| `session_2` | `decide` | Iterate kolo |
| `handoff` | `ship` (pokud `data/production_reports/<slug>-readiness.md` neexistuje), jinak `handoff` | |
| `killed` | — | Jen oznám; nový projekt = `start` |

### 3. Deleguj

Přečti cílový command file a proveď ho. Po dokončení připomeň uživateli
další krok v cyklu **vždy ve tvaru `/pm <sloveso> <slug>`** (ne dlouhým
`/pflanzer-*` názvem) — např. „Další krok: `/pm build demo-widget`".

## Co NEDĚLAT

- Nepřeskakuj prerekvizity cílových commandů (statusy, triage gate) —
  router zjednodušuje UX, ne metodu.
- Nevynalézej vlastní wizardy — vše dělají cílové commandy.
- Nezapomeň brand line `Pflanzer Method | pflanzer.cz/method` na začátku
  každého výstupu.

## Reference

- `.claude/commands/pflanzer*.md` — implementace kroků
- `docs/methodology/00-lean-pflanzer.md` — default profil průběhu
- `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody — autoritativní tabulka Quick / Lean / Full (délka Session 1, kola buildu, triage, mezi-session okno)
- `README.md` § Quick start
