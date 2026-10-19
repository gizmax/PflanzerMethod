---
description: Kickoff (/pm start, 15 min) — zadání na 1 stránku + jména zástupců 6 kroků cesty. Jediná cesta založení projektu.
---

# Kickoff (`/pm start`) — 15 minut

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`
> (funguje z libovolného adresáře).

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

Argumenty: `$ARGUMENTS` = volitelně problém v 1 větě. Kickoff vede Decider
+ jádro (ADR-0021). Cíl: **zadání na 1 stránku + jména pro všech 6 kroků
cesty + zabookovaná okna**. Žádný dlouhý wizard.

## Krok 0 — Readiness

```bash
pflanzer doctor
```

Pokud „připraveno ke Kickoffu: ne" → vypiš, co chybí (origin, vyplněný
`INTEGRATION_GUIDE`, `CONSTITUTION`, test/lint/build, CI, preview deploy,
pushnutý init), a zeptej se přes AskUserQuestion:
*Opravit teď / Pokračovat vědomě (uveď riziko) / Zastavit.* Bez preview
deploye Build proběhne, ale Async nemá na co klikat — řekni to nahlas.

## Krok 1 — Sběr (AskUserQuestion, max 3 bloky)

1. **Zadání:** problém v 1 větě · jedna metrika úspěchu · kill kritérium
   („kdy to zabalíme"; volitelně `metric`, `kill_criteria` ve specu).
2. **Lidé:** Decider (jméno + mandát říct Go i Kill) · **jméno ke každému ze
   6 kroků cesty** — byznys, produkt, design, vývoj, bezpečnost & právo,
   provoz · které z nich je **jádro** (3–4 lidé, celou dobu) a které **okno**.
3. **Rámec:** risk profile `throwaway | pilot | production` · **stupeň**
   `quick | lean | full` (default **Lean**: Build 3 h, Async 3–5 dní;
   Quick = `/pm live`; Full = governance / regulované, audit-grade, okno
   5–7 dní — autoritativní tabulka v `docs/methodology/00-lean-pflanzer.md`
   § Tři stupně, ADR-0017) · zabookovaná okna (Build 3 h, checkpoint B&P
   20 min, Rozhodnutí 60–90 min, checkpoint provozu 20 min).

Pravidla (vynucuj):
- **Krok bez jména → STOP.** Nabídni, kdo ho může zastoupit (jeden člověk
  smí krýt víc kroků; kdo — viz `docs/methodology/02-role-catalog.md`).
  Bez jmen projekt nezakládej.
- **Jádro > 5** (nebo kdokoli naráz > 5) → navrhni zúžit scope nebo přesunout
  někoho na okno.
- Zástupce bez mandátu rozhodnout v okně není zástupce.
- `pilot`/`production`: repo musí mít origin (`doctor`); `target_repo_url`
  se čte z `.pflanzer/project.toml`, neptej se na něj znovu.
- `quick` nejde s audit-grade (ten je vždy Full).
- `throwaway` (kód se po Rozhodnutí zahodí) = explicitní opt-in s důvodem:
  discovery-only pilot · důkaz oddělený od produkce (audit) · certifikovaná
  regulovaná produkce (ADR-0005). Jinak platí, že vítěz jde do produkce.
- Zákaz pokračovat při datech L4 nebo AI Act „unacceptable" — zapiš
  do decision logu a zastav. Regulované projekty: `docs/governance/`.

## Krok 2 — Založení (jediná cesta)

Sestav spec (např. `/tmp/<slug>-kickoff.json`):

```json
{
  "hook": "<problém v 1 větě>",
  "decider_name": "<jméno>",
  "room_role_idx": [1, 2, 6, 4, 7, 15],
  "risk_profile": "pilot",
  "tier": "lean",
  "role_owners": {"1": "Honza", "2": "Petra"},
  "metric": "<metrika>",
  "kill_criteria": "<kdy zabalit>",
  "path_owners": {"byznys": "", "produkt": "", "design": "", "vyvoj": "", "bezpecnost": "", "provoz": ""},
  "core": ["Petra", "Jan", "Eva"]
}
```

```bash
pflanzer quick_session bootstrap --spec /tmp/<slug>-kickoff.json
```

Víc repozitářů (FE + BE, monorepo): místo `target_repo_url` dej
`"target_repos"` — text `fe=https://…/web, be=https://…/api#develop` nebo
pole `[{"role": "fe", "url": "…", "branch": "main", "workspace": "apps/web"}]`.
Chyba „krok bez jména" nebo warning „jádro > 5" → vrať se ke Kroku 1, nic
neobcházej. Výstup obsahuje `slug`.

## Krok 3 — Výstup

Ukaž (s brand line):

- **Zadání na 1 stránku:** problém · metrika · kill kritérium · Decider.
- Tabulka: krok cesty → jméno → jádro/okno → termín okna.
- Rizika z `doctor` (pokud jsme pokračovali vědomě).

Na konci **jeden** další krok:

> Další krok: `/pm build <slug>` — jádro, 3 h (Decider u stavby není).

## Co NEDĚLAT

- Neptej se na víc než výše — detail (triage, roles, plný Charter) je
  volitelný a patří do regulovaných projektů (`/pm roles`, `/pm triage`).
- Nezaváděj Sessions, Slices ani jiné výrazy; terminologie: Kickoff, Build,
  Async, Rozhodnutí, Ship.
- Nezakládej projekt mimo `pflanzer quick_session bootstrap`.

## Reference

- `docs/decisions/0021-mala-skupina-cela-cesta.md`
- `docs/decisions/0022-inspirace-z-trhu.md`
- `docs/zacni.md` § Je repo připravené?
