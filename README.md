# Pflanzer Method

**Pflanzer Method | [pflanzer.cz/method](https://pflanzer.cz/method)**

> **Malá skupina, ve které je zastoupena celá cesta** od nápadu do produkce
> (byznys → produkt → design → vývoj → bezpečnost & právo → provoz),
> postaví s AI co-pilotem 3 funkční varianty, rozhodne nad běžícím kódem
> a vítěz jde rovnou do produkce. Jádro 3–4 lidí je u toho celou dobu,
> ostatní zástupci přijdou na krátké okno. Nikdy víc než 5 lidí naráz.
> Viz ADR-0021.

## Začni tady

- **`docs/zacni.md`** — **chceš to vyzkoušet?** Co zařídit s lidmi, co nainstalovat, checklist ke Kickoffu.
- **`docs/postup.md`** — postup v 5 krocích + diagram průběhu (1 obrazovka).
- **`docs/methodology/00-lean-pflanzer.md`** — 1-pager: kdo, kdy, co (~8 dní, ~6–8 PD). **Tohle čti, pokud chceš metodu použít, ne studovat.**
- **`docs/decisions/0021-mala-skupina-cela-cesta.md`** — proč malá skupina + evidence.
- **`docs/case-studies/eshop-2026.md`** — reálný průběh pilotu.

**Regulované prostředí** (banky, pojišťovny EU, AI Act High-risk, rollout metody napříč organizací) → `docs/governance/`. Běžný projekt to **nepotřebuje**.

## Co řeší

V korporátu cesta od nápadu k funkční fíčuře trvá měsíce: zadavatel pinká
s produktem, produkt s vývojem, schvalovací kola, security audit… Každé
předání ztrácí kontext. Metoda dá zástupce každého kroku cesty k jednomu
artefaktu — běžícímu kódu — a rozhodne za ~týden. Ven jde **PR připravený
k mergi**, ne specifikace k re-implementaci.

## Quick start

**Jediný command, který si musíš pamatovat: `/pm`** — bez argumentu pozná,
kde v cyklu projekt je, a nabídne další krok.

```
Kickoff      (15 min, Decider + jádro)
  /pm start            # zadání na 1 stránku + jména zástupců 6 kroků cesty
                       # (nebo rovnou /pm live = kickoff + build v jednom)

Build        (3 h, jádro; checkpoint bezpečnost & právo 20 min)
  /pm live "chceme zlepšit onboarding"
  → 3 varianty paralelně (Claude Code ve 3 worktrees target repa)

Async        (3–5 dní, všichni zástupci)
  /pm feedback <slug>  # agregace komentářů ze sandbox URL

Rozhodnutí   (60–90 min, Decider + jádro)
  /pm decide <slug>    # Go / Iterate / Kill, Decider hlasuje poslední

Ship         (1–2 dny, vývojáři + checkpoint provozu 20 min)
  /pm ship <slug>      # 7 quality gates → score 0–100
  /pm handoff <slug>   # PR-ready package s odkazy na soubory
```

**Po Ship tým má**:
- Funkční kód jako feature branch v target repu (ESLint, typy, testy)
- Quality gate score (lint + types + tests + security + a11y + build + observability)
- Decision log včetně checkpointů bezpečnosti a provozu
- Open-PR-ready commit do `target_repo_url`

Cílem je `gate_score >= 80/100` = většina kódu se dá použít v produkci.

## Volba builderu — Claude Code default, hosted SaaS opt-in

**Standardně používej Claude Code** (nebo Codex CLI, podle preference týmu).
3× CC v 3 git worktrees, paralelně. Bolt/v0/Lovable jen na **explicit
opt-in** přes `--prefer-hosted`.

### In-room protocol (default)

```bash
# 1. Facilitátor (1 minuta):
SLUG=<your-slug>
git worktree add ../proto-${SLUG}-A -b feat/${SLUG}-A
git worktree add ../proto-${SLUG}-B -b feat/${SLUG}-B
git worktree add ../proto-${SLUG}-C -b feat/${SLUG}-C

# 2. Tým se rozdělí po dvojicích, každá v jednom worktree:
cd ../proto-${SLUG}-X && claude
# Vloží prompt (z `quick_session.py prompts` output) → 30 min koduje
# → npm test && npm run lint && npm run build → commit

# 3. Po skončení: 3 feature branche v repu, gate-scored přes /pm ship
```

Diversity skrz **3 různé prompty** (happy-path / multi-step / smart defaults),
ne skrz 3 různé builders. Tým má všechny konvence repa, žádný extract step,
žádná SaaS license navíc, žádný leak prompt history.

### Kdy opt-in pro hosted SaaS

```bash
python3 tool/cli/quick_session.py prompts --slug <slug> --hook "<hook>" --prefer-hosted
```

Použij **jen** v jednom z těchto případů:
- Greenfield: žádný existující repo, hackathon weekend
- Designer / non-tech sponsor u stolu (chce klikni-vidíš UX showcase)
- Marketing landing page (one-off, hosted preview = okamžitý sdílení)
- Throw-away interní demo (`production_readiness_target = 0`)

V opt-in módu dostane shortlist mix: `claude-code + codex-cli + v0`
(stále preferuje in-repo + 1 hosted pro showcase).

### Srovnávací tabulka

| Vlastnost | CC / Codex CLI (default) | Bolt / v0 / Lovable (opt-in) |
|-----------|---------------------------|-------------------------------|
| Kde vzniká kód | Tvůj repo, feat branch | SaaS sandbox |
| Extract step | Žádný — rovnou commit | `git clone` z buildru po Push to GitHub |
| Brownfield (existující repo) | Vidí ESLint, tokens, komponenty | Vyrobí "new app", ignoruje DS |
| Security / audit | Lokální, žádný leak | Prompt history u třetí strany |
| Cena | Žádná navíc | Per-seat license |
| Preview URL | `npm run dev` + ngrok | Hosted ✓ |
| Non-tech stakeholder UX showcase | ❌ vyžaduje terminál | ✅ klikni-vidíš |
| Production code defaults | ✅ testy, strict types, lint | ⚠ často chybí |

## Plný flow (regulované / větší projekty)

Pro audit-grade projekty (regulated SDLC, AI Act high-risk) — stejný model
malé skupiny, jen víc příprav a podpisů (viz `docs/governance/`):

```
/pm start <slug>      # Plný Charter wizard (XYZ, kapacita, Decider mandate, …)
/pm roles <slug>      # Kdo zastupuje který krok cesty (z 18 rolí catalogu)
/pm triage <slug>     # 4 paralelní triage tracks (Discovery + Security + Legal + Platform)
/pm build <slug>      # Build (orchestrator s AI expert sub-agenty)
# … async 3–5 dní (web hub) …
/pm decide <slug>     # Rozhodnutí (Go / Iterate / Kill)
/pm ship <slug>       # Quality gates
/pm handoff <slug>    # Handoff package (BE/FE/QA/Platform)
```

## Klíčový pilíř — 6 kroků cesty, každý se jménem

Každý projekt má zástupce pro **byznys, produkt, design, vývoj, bezpečnost
& právo a provoz**. Jeden člověk může krýt víc kroků; žádný krok nesmí
zůstat bez jména. Kdo může který krok zastoupit, říká **role catalog
(18 rolí)** — knihovna zástupců, ne seznam pozvánek. Perspektivy rolí,
které nejsou u stavby, může dodat AI expert sub-agent (jako vstup, ne hlas).

Detail: [`docs/methodology/02-role-catalog.md`](docs/methodology/02-role-catalog.md).

## Status

✅ **Fáze 1** — autoresearch & dokumentace metodiky (v0.2.1, ADR-0008 form-factor)
🚧 **Fáze 2** — implementace toolu (probíhá)
- Slice 1 ✅ Charter wizard
- Slice 2 ✅ Role selection
- Slice 3 ✅ Pre-flight triage (4 paralelní agents)
- Slice 4 ✅ Web hub MVP (FastAPI + React + Vite + nginx)
- Slice 5 ✅ Session 1 orchestrator (facilitator + 17 role experts)
- Slice 6 ✅ Mezi-session feedback collection + discovery-debt-detector
- Slice 7 ✅ Session 2 (decisional) + conflict resolver
- Slice 8 ✅ Handoff package generator (8 per-role artefakty)
- **`/pflanzer` quick wizard** ✅ — single-entry pro in-room session
- **Production path** ✅ — extract.py + quality_gates.py + /pflanzer-session-3
  → kód po Ship ready k mergi (gate_score 0-100)

## Struktura repa

```
docs/
├── methodology/         # metoda v češtině (start: 00-lean-pflanzer.md)
├── governance/          # audit-grade vrstva (jen regulované / multi-pilot)
├── case-studies/        # reálné piloty
├── research/
│   ├── baseline/        # adjacent metody, vibe-coding tools, change-mgmt
│   ├── perspectives/    # raw výstupy expertního panelu (1 .md / role)
│   └── synthesis/       # pracovní syntézy, conflict matrix, devil's advocate
└── decisions/           # ADR (Architecture Decision Records)

tool/
├── cli/                 # Python backend (charter, roles, triage, session, quick)
├── db/                  # SQLite schema + migrate
├── data/                # role_catalog.json
└── web/                 # FastAPI backend + React frontend (Hybrid form-factor)

.claude/
├── commands/            # slash commands (/pm router + /pflanzer-* implementace)
└── agents/              # 24 sub-agentů (facilitator, role experts, triage, helpers)
```

## Install — co si tým musí stáhnout

### Pro tebe (one-time, ~30 sekund)

```bash
curl -fsSL https://raw.githubusercontent.com/gizmax/PflanzerMethod/main/install.sh | bash
```

Co se stane:
1. Naclonuje metodu do `~/.claude/plugins/pflanzer/` (slash commands + agents + tool/cli)
2. Vytvoří `~/.pflanzer/` runtime dir + sdílenou SQLite DB (audit log per všechny tvoje projekty)
3. Symlink `pflanzer` do `~/.local/bin/` (CLI wrapper: `pflanzer init`, `pflanzer root`, `pflanzer db`, …)
4. Zaregistruje plugin v Claude Code (`claude plugin marketplace add` + `claude plugin install pflanzer@pflanzer-method`) → `/pm` je dostupné z **libovolného** repa
5. Ověří: `git`, `python3.10+`, `node 20+`, `claude` v PATH

> Jen `/plugin install` v Claude Code nestačí — slash commandy volají CLI
> `pflanzer`, které instaluje skript.

### Pro každý cílový repo (one-time, ~1 minuta)

```bash
cd /path/to/your/repo
pflanzer init
```

Co se stane:
1. Vyrobí `docs/INTEGRATION_GUIDE.md` (template — tým ručně vyplní auth pattern, API client, state lib, logger, feature flags, folder layout, test runner).
2. Vyrobí `.pflanzer/project.toml` (pre-populated `target_repo_url` z `git remote get-url origin`).
3. Vytvoří `tests/acceptance/` složku (Charter wizard tam píše `.feature` soubory per session).
4. Update `.gitignore` (`extracted/`, `.pflanzer/local/`).

**Pak commit oba soubory**, restartuj Claude Code v tom repu a spusť:

```
/pm start            # Kickoff (nebo /pm live "co dnes řešíme" = Kickoff + Build v jednom)
```

Průvodce prvním pilotem (lidi, okna, preview, checklist): `docs/zacni.md`.

### Co vlastně tým stahuje?

| Komponenta | Velikost | Kde |
|------------|----------|-----|
| Plugin (slash commands + agents + Python) | ~700 KB | `~/.claude/plugins/pflanzer/` |
| INTEGRATION_GUIDE.md template | ~3 KB | `docs/` v target repu |
| `.pflanzer/project.toml` | ~500 B | per target repo |
| Skeleton (per session) | ~30-50 MB | `~/.pflanzer/targets/<repo>/` (cached) |
| node_modules (per worktree) | ~150 MB × 3 | `~/.pflanzer/targets/<slug>-{A,B,C}/node_modules/` |

**Předpoklady na lokálu:**
- `git` (jakákoliv verze)
- `python3 ≥ 3.10`
- `node ≥ 20.11` (LTS)
- Claude Code (`claude` v PATH)

### Update / Uninstall

```bash
pflanzer update    # git pull + DB migrace + claude plugin update
claude plugin uninstall pflanzer@pflanzer-method
rm -rf ~/.claude/plugins/pflanzer ~/.pflanzer ~/.local/bin/pflanzer
```

### Dev setup (pokud přispíváš do metody)

```bash
git clone https://github.com/gizmax/PflanzerMethod
cd PflanzerMethod
python3 tool/db/migrate.py    # použije ./data/pflanzer.db (dev mode)
# Web hub (volitelně, pro async feedback dev):
cd tool/web/backend && uvicorn main:app --reload --port 8000 &
cd tool/web/frontend && npm install && npm run dev
```

> DB lokace: pokud `~/.pflanzer/` existuje, použije se `~/.pflanzer/pflanzer.db`
> (installed plugin mode). Jinak `<repo>/data/pflanzer.db` (dev mode).
> Override: `export PFLANZER_DB=/path/to/db.sqlite`.

## Plán fáze 2 (full)

Detailní plán: [`~/.claude/plans/recursive-cuddling-sonnet.md`](../../.claude/plans/recursive-cuddling-sonnet.md)

## Konvence

- Dokumentace metodiky: **čeština**
- Code, comments v toolu: EN, dle CLAUDE.md
- Git workflow: feature-branche + lokální merge `--no-ff` (NIKDY commit přímo na main)
- ADR formát: `docs/decisions/NNNN-short-slug.md`
