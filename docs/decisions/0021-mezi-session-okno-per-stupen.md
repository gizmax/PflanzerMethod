# ADR-0021 — Délka mezi-session okna podle stupně (Quick / Lean / Full)

> Status: Accepted · 2026-09-23
> Autor: audit `docs/research/review-2026-09/01-audit-a-navrhy-zlepseni.md` (nález N18)
> Související: ADR-0001 (Decider, Session 2b), ADR-0020 (Track P/S),
> `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody

## Kontext

Délka okna mezi Session 1 a Session 2 byla v metodice sporná a v dokumentaci
nekonzistentní:

- **Facilitátor** (`docs/research/perspectives/03-facilitator-meta.md`):
  *„5–7 dní, ne 14. Prototyp deployed do 48 h, scoring window 3 dny, syntéza
  1 den. Delší = ztráta kontextu, kratší = nikdo neoscoruje."* Argument stojí na
  async rolích s vetem (Legal, Security, EM), které potřebují pracovní dny.
- **Vibe-product flow** (`docs/research/code-reusability/perspectives/02-vibe-product-flow.md`
  C4, synthesis K2): *„48–72 h, ne 5–7 dní"* — delší okno znamená Slack-ticho,
  sponzor přepne na jiné priority a nikdo kód kriticky neviděl. Navrhuje změnit
  i úkol: místo „klikni a dej preference" projít PR diff a napsat keep / fix /
  kill per soubor.
- Lean recept (`00-lean-pflanzer.md`) mezitím počítal se 4 dny (Den 6–9),
  e-shop case study s ~5 dny a `05-mezi-sessions.md`, `04-session-1.md`,
  `00-tldr.md`, commandy a README s pevnými 5–7 dny.

Obě perspektivy mají pravdu pro jiný typ projektu. Podle `CLAUDE.md` se spor
nezprůměrovává, rozhoduje se ADR.

## Rozhodnutí

### 1. Délka okna se řídí stupněm, protože stupeň určuje, kdo musí dát feedback

| Stupeň | Okno | Proč | Kdo musí dát feedback |
|--------|------|------|------------------------|
| **Quick** | **3 pracovní dny** (~72 h) | Žádná vetovací role v okně (triage deferred; prod blokuje Ship gate triage gate). Rozhoduje momentum. | Lidé z místnosti + dev páry |
| **Lean** (default Track P) | **3–5 pracovních dní**, default **4** | Triage je lightweight checklist, vetovací role nejsou povinně v místnosti. Odpovídá receptu Den 6–9. | Lidé z místnosti + stakeholdeři dotčených oddělení |
| **Full** | **5–7 pracovních dní** | Async vetovací role (Security, Legal/DPO, EM), AI Act Fáze B a triage updates do Den 5 (`05-mezi-sessions.md`). Kratší okno by je vyřadilo. | Všechny role včetně async vetovacích |

Stupeň je zapsaný v Charteru / bootstrapu a uložený v `projects.tier`. Okno se **neprodlužuje nad horní
hranici stupně**; potřeba delšího okna je signál k upgradu stupně nebo
k odložení Session 2 podle eskalačních pravidel v `05-mezi-sessions.md`.

### 2. Úkol v okně: diff review pro technické role, preview + scoring pro ostatní

Přebíráme C4 z vibe-product perspektivy, ale jen pro role, které diff umí číst:

- **Dev páry, BE/FE lead, QA, Security:** projít PR diff varianty
  (`worktree.py preview --mode draft-pr`) a ke každému změněnému souboru napsat
  **keep / fix / kill** jako PR komentář.
- **Non-tech stakeholdeři:** preview (draft PR preview URL nebo Playwright
  záznam acceptance scénářů) + strukturovaný scoring formulář ve web hubu.

### 3. Ticho po deadline

- **Nevetovací role:** chybějící feedback po deadline = *„no objection"*,
  zapisuje se do decision logu s atribucí (kdo mlčel).
- **Vetovací role (Security, Legal/DPO, EM kapacita):** ticho **není**
  souhlas. Platí quorum pravidlo `08-edge-cases-a-rizika.md` § 11 — bez jejich
  async sign-offu je Session 2 jen review, ne rozhodnutí.

### 4. Připomínky

Facilitátor pošle připomínku **48 h a 24 h před deadline** okna. Ve Full stupni
navíc upozorní vetovací role na Den 3.

## Varianty zvážené

1. **48–72 h pro všechny stupně** — odmítnuto: ve Full stupni by async
   vetovací role nestihly triage update a AI Act Fázi B; metoda by je
   de facto vyřadila z rozhodnutí.
2. **5–7 dní pro všechny stupně** — odmítnuto: v Quick a Lean ztrácí momentum
   a winner kód zůstává dny nerevidovaný; případ, před kterým varuje C4.
3. **Kompromis 4 dny pro všechny** — odmítnuto: průměr nevyhovuje ani jedné
   straně a porušuje pravidlo „ADR místo zprůměrování".

## Důsledky

**Pozitivní**
- Jedno pravidlo místo tří protichůdných čísel v dokumentaci.
- Quick a Lean drží momentum; Full nechává prostor vetovacím rolím.
- Diff review dává feedback, který jde přímo do kódu, ne jen preference.

**Negativní / cost**
- Tým musí znát svůj stupeň už v Session 1 (Charter / bootstrap ho ukládá do
  `projects.tier`; starší projekty doplní odhadem `migrate.py`).
- Pravidlo „ticho = no objection" vyžaduje, aby decision log zapisoval
  i mlčení.

**Sladěné dokumenty:** `05-mezi-sessions.md`, `04-session-1.md`, `00-tldr.md`,
`08-edge-cases-a-rizika.md`, `09-srovnani-existujici-metody.md`, README,
`/pflanzer`, `/pflanzer-session-1`, `/pflanzer-feedback-pull`.
