# Pflanzer Method

**Pflanzer Method | [pflanzer.cz/method](https://pflanzer.cz/method)**

> Univerzální corporate framework pro zrychlení agentního vývoje od nápadu po
> produkční deploy — všechny zainteresované role (**včetně programátora od minuty 0**)
> se sejdou v jedné místnosti s AI co-pilotem a společně provibe-kódují 1–3 funkční
> produkční-ready varianty. Default Track P (~80 % case-ů) → produkt rovnou do prod.
> Fallback Track S (~20 % s 4 hard triggers, ne preferovaný) → precision spec
> ≥ 80/100 + 5-stage handoff ritual. Viz ADR-0020.

## Začni tady (default profil — ~80 % use casů)

- **`docs/methodology/00-lean-pflanzer.md`** — 1-pager pro default profil (~6 lidí, 2 sezení, ~14 dní, ~10 PD). **Tohle čti, pokud chceš metodu použít, ne studovat.**
- **`docs/case-studies/eshop-2026.md`** — reálný průběh e-shop pilotu (3h vibe, 3 weby, ship to prod).
- Quick start níže (`/pflanzer ...` commands).

**Audit-grade overhead** (Method Steward, pre-registration, compliance score, AI Act Fáze A/B/C, DORA prompt audit pipeline) → relevantní jen pro regulated industries (banky, pojišťovny EU, AI Act High-risk). Viz `method-charter.md` + ADR-0011/0012/0013/0014. Běžný e-shop projekt tohle **nepotřebuje**.

## Co řeší

V korporátu typicky cesta od nápadu k funkční fíčuře trvá měsíce: zadavatel pinká
s produktem, produkt s vývojem, schvalovací kola, security audit, atd. Metoda to
zkracuje na **2 sezení + Ship gate** — tým se sejde, společně provibe-koduje 2–3 varianty,
rozhodne, kód projde production gates, ven jde **PR připravený k mergi**.

**Většina kódu z vibe-coding session je použitelná**, ne jen reference pro re-implementaci.

## Quick start (2 sezení + Ship gate = ship to production)

**Jediný command, který si musíš pamatovat: `/pm`** — bez argumentu pozná,
kde v cyklu projekt je, a nabídne další krok. (Dlouhé `/pflanzer-*` commandy
žijí dál jako implementace pod kapotou.)

Délka Session 1 závisí na zvoleném **stupni** (Quick 60–90 min / Lean 3 h /
Full 5–6 h) — jediná autoritativní tabulka je v
[`docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody](docs/methodology/00-lean-pflanzer.md#tři-stupně-jedné-metody).

```
Session 1: Explore (in-room, délka podle stupně Quick / Lean / Full)
  /pm live "chceme zlepšit onboarding"   # Quick, 60–90 min
  /pm build <slug>                       # Lean (default Track P) / Full
  → 3 paralelní varianty (3× Claude Code ve worktrees target repa)
  → silent voting + Decider's shortlist
  → 1-page handoff MD

Session 2: Decide (3 h)
  /pm feedback <slug>     # async feedback od stakeholderů
  /pm decide <slug>       # Decider's Go/Iterate/Kill

Ship gate (pipeline po Session 2 GO, pouští dev pár — není to setkání)
  /pm ship <slug>         # quality gates → score 0-100 + SHIP.md
  /pm handoff <slug>      # PR-ready package s odkazy na soubory
```

**Po Ship gate dostane tým**:
- Funkční kód v `extracted/<slug>/<winner>/` (Vite + React + TS, ESLint, Vitest)
- Quality gate score (lint + types + tests + security + a11y + build + observability)
- Per-role handoff balíčky s **odkazy na skutečné soubory** (ne TBD placeholders)
- Open-PR-ready commit message do `target_repo_url` z Charteru

Cílem je `gate_score >= 80/100` = většina kódu se dá použít v produkci.

Pod kapotou: Charter (ADR-0004) + 18-position role catalog + builder decision
optimalizovaná na exportable code + preference matrix s AI-only deflation +
audit log s DORA 7-letou retencí. **Sofistikovanost zachovaná, UX zjednodušeno.**

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

# 3. Po skončení: 3 feature branche v repu, gate-scored přes Ship gate (/pm ship)
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

## Plný flow (pokud potřebuješ celé)

Pro audit-grade projekty (regulated SDLC, AI Act high-risk, multi-team scope):

```
/pm start <slug>      # Plný Charter wizard (XYZ, kapacita, Decider mandate, …)
/pm roles <slug>      # Decision tree pro 18 rolí
/pm triage <slug>     # 4 paralelní triage tracks (Discovery + Security + Legal + Platform)
/pm build <slug>      # Session 1 orchestrator (délka podle stupně Quick/Lean/Full)
# … mezi-session 5–7 dní (web hub) …
/pm decide <slug>     # Session 2 (decisional, 3 h)
/pm handoff <slug>    # Handoff package (BE/FE/QA/Platform)
```

## Klíčový pilíř — role catalog

Místo fixní sady stakeholderů má metoda **knihovnu 18 rolí**. Před každým
projektem si tým vybere relevantní podmnožinu (decision tree). AI panel pak
v session zapojí právě tyhle role — žádný overhead, žádné chybějící vstupy.

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
  → kód po 2 sezeních + Ship gate ready k mergi (gate_score 0-100)

## Struktura repa

```
docs/
├── methodology/         # finální metoda v češtině (9 dokumentů)
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
└── agents/              # 23 sub-agentů (1 facilitator + 17 role experts + 5 triage)
```

## Install — co si tým musí stáhnout

### Pro tebe (one-time, ~30 sekund)

```bash
curl -fsSL https://raw.githubusercontent.com/gizmax/PflanzerMethod/main/install.sh | bash
```

Co se stane:
1. Naclonuje plugin do `~/.claude/plugins/pflanzer/` (slash commands + agents + tool/cli)
2. Vytvoří `~/.pflanzer/` runtime dir + sdílenou SQLite DB (audit log per všechny tvoje projekty)
3. Symlink `pflanzer` do `~/.local/bin/` (CLI wrapper pro `pflanzer init`, `pflanzer extract`, …)
4. Ověří: `git`, `python3.10+`, `node 20+`, `claude` v PATH

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

**Pak commit oba soubory** a tým je ready. V Claude Code:

```
/pm live "co dnes řešíme"
```

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
pflanzer update    # = git pull v ~/.claude/plugins/pflanzer/
rm -rf ~/.claude/plugins/pflanzer ~/.pflanzer ~/.local/bin/pflanzer
```

### Dev setup (pokud přispíváš do metody)

```bash
git clone https://github.com/gizmax/PflanzerMethod
cd PflanzerMethod
python3 tool/db/migrate.py    # použije ./data/pflanzer.db (dev mode)
# Web hub (volitelně, pro async feedback dev):
PFLANZER_HUB_AUTH_MODE=dev uvicorn backend.main:app --app-dir tool/web --reload --port 8000 &
cd tool/web/frontend && npm install && npm run dev
```

> DB lokace: pokud existuje soubor `~/.pflanzer/pflanzer.db` (vytvoří ho
> `install.sh`), použije se ten (installed plugin mode). Jinak
> `<repo>/data/pflanzer.db` (dev mode) — samotný adresář `~/.pflanzer/targets/`
> (cache target repozitářů z `worktree.py setup`) DB nepřepne.
> Override: `export PFLANZER_DB=/path/to/db.sqlite`.
> Web hub (`tool/web/backend`) používá stejné pořadí, takže CLI i hub čtou jednu DB.

**Deploy web hubu ve firmě.** Backend je defaultně v `oidc` módu (bez SSO identity
vrací 401); lokálně ho spouštěj s `PFLANZER_HUB_AUTH_MODE=dev` (to dělá
`tool/web/run-local.sh`) — identita je pak neověřená hlavička `X-User`. Ve firmě
musí hub stát za `oauth2-proxy` napojeným na firemní IdP (Entra ID / Okta /
Keycloak): `cp tool/web/.env.example tool/web/.env`, vyplnit a
`docker compose --profile oidc up`. Hodnotitel ve feedbacku je pak SSO e-mail
(auditovatelná atribuce, AI Act čl. 14 / DORA). Detail:
[`tool/web/README-auth.md`](tool/web/README-auth.md).

### Testy a CI

```bash
pip install pytest ruff pyyaml         # + fastapi sqlmodel httpx pro test web auth
python3 -m pytest -q                   # tests/ — hermetické: tmp DB, tmp HOME, lokální git repa
ruff check tool tests                  # konfigurace v pyproject.toml
python3 tool/cli/quality_gates.py --path tool/web/frontend --adapter tool/pflanzer.gates.yml
```

GitHub Actions (`.github/workflows/ci.yml`, push + PR): `tool` (ruff + pytest),
`web-backend` (auth testy), `web-frontend` (`tsc --noEmit` + build) a `dogfood`
(quality gates toolu na vlastním repu — jen report, na skóre nepadá).

## Plán fáze 2 (full)

Detailní plán: [`~/.claude/plans/recursive-cuddling-sonnet.md`](../../.claude/plans/recursive-cuddling-sonnet.md)

## Konvence

- Dokumentace metodiky: **čeština**
- Code, comments v toolu: EN, dle CLAUDE.md
- Git workflow: feature-branche + lokální merge `--no-ff` (NIKDY commit přímo na main)
- ADR formát: `docs/decisions/NNNN-short-slug.md`
