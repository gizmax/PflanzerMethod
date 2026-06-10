# CLAUDE.md — Pflanzerova metoda (projektový kontext)

Tento soubor doplňuje globální `~/.claude/CLAUDE.md` o projekt-specifický kontext.

## O čem projekt je

Generalizace a operacionalizace **Pflanzerovy metody** — frameworku pro
zrychlení agentního vývoje v korporátu skrz dvě intenzivní cross-functional
sessions s AI co-pilotem.

Cíl: dodat (1) doladěnou metodiku v dokumentaci, (2) tool, který tým metodou
provede end-to-end.

## Současná fáze

**Fáze 1 — autoresearch & dokumentace metodiky.**
Plán: `~/.claude/plans/recursive-cuddling-sonnet.md`.

Fáze 2 (návrh & implementace toolu) startuje **až po explicitním schválení**
fáze 1 uživatelem.

## Konvence specifické pro tento projekt

### Branding (povinné)
Oficiální brand lockup je **`Pflanzer Method | pflanzer.cz/method`**.
- Každý user-facing výstup toolu (slash commandy, web hub, reporty, handoff
  package, generované dokumenty) začíná tímto brand line.
- V marketingu a na webu vždy „Pflanzer Method" (EN wordmark, i v českém
  textu) + doména `pflanzer.cz/method` ve frame/footer.
- Zkratka „PM" se používá **jen** v názvech commandů (`/pm`), nikdy v textu.

### Jazyk
- Veškerá **dokumentace metodiky** (`docs/methodology/`, `docs/research/`,
  `docs/decisions/`): **čeština**.
- **Code, code-comments, identifikátory v toolu** (fáze 2): EN.
- README a tento CLAUDE.md: čeština.

### Role catalog je první-class koncept
Metoda nemá fixní sadu rolí. Kdykoliv se mluví o „expertech" / „stakeholderech",
referuj na `docs/methodology/02-role-catalog.md` a respektuj decision tree pro
výběr rolí pro konkrétní projekt.

### Expert panel = paralelní sub-agents
Každá role v autoresearchi i v toolu = samostatný `general-purpose` sub-agent
s rolovým promptem. Spouštět **ve vlnách po 3–4 paralelně**, ne všechny najednou
(context window).

### ADR pro každé sporné rozhodnutí
Pokud se v syntéze neshodnou dvě role, výsledek nezprůměrovat — udělat ADR
v `docs/decisions/NNNN-<slug>.md` (kontext / varianty / rozhodnutí / důsledky).

### Git workflow
- `main` chráněný, nikdy commit napřímo (kromě úvodního bootstrap commitu).
- Branch naming: `feat/...`, `fix/...`, `chore/...`, `docs/...`, `research/...`.
- PR přes `gh pr create` po dokončení každého logického celku.

### Tool stack (fáze 2, předběžně)
Per globální CLAUDE.md: Python + FastAPI + SQLite (BE), React + Tailwind (FE),
anthropic SDK, model `claude-sonnet-4-20250514`. Form-factor (CC plugin / web /
hybrid) se rozhodne ADR `0001-tool-form-factor.md` na začátku fáze 2.

## Co tady NEPATŘÍ

- ❌ Generování kódu produktu (např. InvestmentBot, Cardigo) — to do svých repos.
- ❌ Generic vibe-coding playground — projekt je specificky o **metodě a jejím toolu**.
- ❌ Sample mockupy z reálných sessions — ty patří do testovacích projektů, ne sem.
