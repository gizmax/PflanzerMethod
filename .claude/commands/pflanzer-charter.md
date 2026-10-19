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

Ukaž lidský výstup a jeho Doporučení. Pokud „připraveno ke Kickoffu: ne" →
vypiš, co chybí (origin, vyplněný `INTEGRATION_GUIDE` — vývojář v Claude Code
napíše „vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“ a zkontroluje,
`CONSTITUTION`, test/lint/build, CI, preview deploy, pushnutý init:
`git add -A docs .pflanzer tests .gitignore && git commit -m "chore(pflanzer): init" && git push`), a zeptej se přes AskUserQuestion:
*Opravit teď / Pokračovat vědomě (uveď riziko) / Zastavit.* Bez preview
deploye Build proběhne, ale Async nemá na co klikat — řekni to nahlas.

## Krok 1 — Sběr (AskUserQuestion, max 3 bloky)

1. **Zadání:** problém v 1 větě · jedna metrika úspěchu (číslo + termín,
   např. „10 z 15 obchodníků otevře přehled 3× týdně do 30 dnů“, ne „budou
   to používat“) · kill kritérium („kdy to zabalíme“; ve specu `metric`,
   `kill_criteria`).
2. **Lidé:** Decider (jméno + mandát říct Go i Kill) · **ke každému ze
   6 kroků cesty** — byznys, produkt, design, vývoj, bezpečnost & právo,
   provoz — jedna otázka přes AskUserQuestion s možnostmi:
   - **[jméno]** (volný text),
   - **[stejný člověk jako X]** (nabídni konkrétní jména z už zadaných kroků),
   - **[AI náhrada]** — **jen tam, kde ADR-0023 dovolí** (viz tabulka níže).
   Pak které z lidí je **jádro** (3–4, celou dobu) a které **okno**.
3. **Rámec:** risk profile `throwaway | pilot | production` · **stupeň**
   `quick | lean | full` (default **Lean**: Build 3 h, Async 3–5 dní;
   Quick = `/pm live`; Full = regulované, okno 5–7 dní — tabulka v
   `docs/methodology/00-lean-pflanzer.md` § Tři stupně) · zabookovaná okna
   (Build 3 h, checkpoint B&P 20 min, Rozhodnutí 60–90 min, checkpoint
   provozu 20 min).

**AI náhrada (ADR-0023) — nabízej jen podle tabulky:**

| Krok | Nabídka [AI náhrada] | Kdo podepíše místo chybějícího |
|------|---------------------|--------------------------------|
| byznys | **nikdy** | bez Decidera se Kickoff nesvolává |
| vývoj | **nikdy** | u klávesnice sedí vývojář |
| produkt | jen `quick` / `throwaway` | Decider (zadání) |
| design | ano (`AI:ux-expert`) | PdM; u zákaznického produktu v produkci člověk |
| bezpečnost & právo | jen předkontrola (`AI:security-expert`) | throwaway: stačí AI; pilot/production: člověk do 48 h, jinak Ship blokuje |
| provoz | jen předkontrola (`AI:devops-platform-expert`) | throwaway: AI; pilot: vývojář z jádra; production: člověk z provozu |

U kroku s AI náhradou se zeptej **hned i na člověka, který to podepíše**,
a řekni, že AI náhrada platí jen pro tento projekt (příště sehnat člověka).

Pravidla (vynucuj):
- **Krok bez jména a bez povolené AI náhrady → STOP.** Nabídni, kdo ho může
  zastoupit (jeden člověk smí krýt víc kroků; kdo — viz
  `docs/methodology/02-role-catalog.md`). Bez toho projekt nezakládej.
- **Jádro > 5** (nebo kdokoli naráz > 5) → navrhni zúžit scope nebo přesunout
  někoho na okno.
- Zástupce bez mandátu rozhodnout v okně není zástupce.
- `pilot`/`production`: repo musí mít origin (`doctor`); `target_repo_url`
  se čte z `.pflanzer/project.toml`, neptej se na něj znovu.
- `quick` nejde s audit-grade (ten je vždy Full).
- `throwaway` (kód se po Rozhodnutí zahodí) = explicitní opt-in s důvodem:
  discovery-only pilot · důkaz oddělený od produkce (audit) · certifikovaná
  regulovaná produkce (ADR-0005). Jinak platí, že vítěz jde do produkce.
- Zákaz pokračovat při datech L4 nebo AI Act „unacceptable“ — zapiš
  do decision logu a zastav. Regulované projekty: `docs/governance/`.

## Krok 2 — Založení (jediná cesta)

Spec předej přes stdin (`--spec -`), žádný soubor:

```bash
pflanzer quick_session bootstrap --spec - <<'EOF'
{
  "hook": "<problém v 1 větě>",
  "decider_name": "<jméno>",
  "room_role_idx": [1, 2, 6, 4, 7, 15],
  "risk_profile": "pilot",
  "tier": "lean",
  "role_owners": {"1": "Honza", "2": "Petra"},
  "metric": "<metrika>",
  "kill_criteria": "<kdy zabalit>",
  "path_owners": {"byznys": "Honza", "produkt": "Petra", "design": "AI:ux-expert", "vyvoj": "Jan", "bezpecnost": "AI:security-expert", "provoz": "Jan"},
  "core": ["Petra", "Jan", "Eva"]
}
EOF
```

`path_owners`: jméno, `AI` nebo `AI:<agent>` (jen kde to tabulka dovolí).
Víc repozitářů (FE + BE, monorepo): místo `target_repo_url` dej
`"target_repos"` — text `fe=https://…/web, be=https://…/api#develop` nebo
pole `[{"role": "fe", "url": "…", "branch": "main", "workspace": "apps/web"}]`.
Chyba „krok bez jména“, nepovolená AI náhrada nebo warning „jádro > 5“ →
vrať se ke Kroku 1, nic neobcházej. Potřebuješ-li z výstupu pole `slug`,
přidej `--json`.

## Krok 3 — Výstup a Doporučení

Ukaž lidský výstup toolu (s brand line) a předej jeho **Doporučení**; doplň:

- **Zadání na 1 stránku:** problém · metrika · kill kritérium · Decider.
- Tabulka: krok cesty → jméno (nebo „AI (agent), podepisuje X“) → jádro/okno
  → termín okna.
- Rizika z `doctor` (pokud jsme pokračovali vědomě).

### Pozvánky pro okna (nabídni hned)

Zeptej se přes AskUserQuestion, jestli má command vygenerovat e-maily /
pozvánky pro zástupce oken. Pro každého zástupce (Decider, bezpečnost & právo,
provoz, případně člověk podepisující AI náhradu) napiš krátký text:

- **kdy** (termín okna) a **na jak dlouho** (Decider 15 + 90 min, bezpečnost
  & právo 20 min, provoz 20 min),
- **co přinést** — z jeho role card (`docs/methodology/role-cards/`,
  pro projekt `pflanzer roles cards --slug <slug>`): u bezpečnosti tři věty
  (jaká data AI vidí, kam smí síť, kolik smí AI stát), u provozu rollback,
  kdo je na telefonu a první hodina po nasazení,
- **co udělá na konci** (podpis `pflanzer checkpoint …` nebo Go/Kill).

Posílá je člověk; ty jen napíšeš text.

Na konci **jeden** další krok:

> Další krok: `/pm build <slug>` — jádro, 3 h (Decider u stavby není).

## Co NEDĚLAT

- Neptej se na víc než výše a nenabízej AI náhradu byznysu ani vývoji — detail (triage, roles, plný Charter) je
  volitelný a patří do regulovaných projektů (`/pm roles`, `/pm triage`).
- Nezaváděj Sessions, Slices ani jiné výrazy; terminologie: Kickoff, Build,
  Async, Rozhodnutí, Ship.
- Nezakládej projekt mimo `pflanzer quick_session bootstrap`.

## Reference

- `docs/decisions/0021-mala-skupina-cela-cesta.md`
- `docs/decisions/0022-inspirace-z-trhu.md`
- `docs/zacni.md` § Je repo připravené?
