# Pro vývojáře a správce toolu

**Pflanzer Method | pflanzer.cz/method**

> Technické podrobnosti, které nepatří na úvodní stránku. Kdo chce metodu
> jen použít, začne v [`zacni.md`](zacni.md). Tady je volba builderu,
> co tým stahuje, dev setup, nasazení hubu, testy a struktura repa.

## Volba builderu — Claude Code default, hosted SaaS opt-in

**Standardně používej Claude Code** (nebo Codex CLI, podle preference týmu).
3× CC v 3 git worktrees, paralelně. Bolt/v0/Lovable jen na **explicit
opt-in** (greenfield bez repa, throw-away demo).

### In-room protocol (default)

```bash
# 1. Facilitátor (1 minuta):
SLUG=<your-slug>
pflanzer worktree setup --slug ${SLUG}   # větve pflanzer/${SLUG}-A|B|C

# 2. Tým se rozdělí po dvojicích, každá v jednom worktree:
# (cesty worktrees vypíše setup; X = A/B/C)
claude
# Vloží prompt (z `pflanzer quick_session prompts`) → koduje, průběžně
# npm test && npm run lint && npm run build → commit

# 3. Po skončení: 3 větve v repu → preview URL; vítěz projde gates v /pm ship
```

Diversity skrz **3 různé prompty** (happy-path / multi-step / smart defaults),
ne skrz 3 různé builders. Tým má všechny konvence repa, žádný extract step,
žádná SaaS license navíc, žádný leak prompt history.

### Kdy opt-in pro hosted SaaS

```bash
pflanzer quick_session prompts --slug <slug> --hook "<hook>" --prefer-hosted
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
# … async: Lean 3–5 dní, Full 5–7 dní (pflanzer hub nebo pflanzer feedback add) …
/pm decide <slug>     # Rozhodnutí (Go / Iterate / Kill)
/pm ship <slug>       # Quality gates (pflanzer.gates.yml) na vítěze
/pm handoff <slug>    # Handoff package (BE/FE/QA/Platform)
/pm retro <slug>      # Měření outcome: % LOC v produkci, T+7/30/60/90
```


## Projekt přes víc repozitářů (target_repos)

`target_repos` je seznam `{role, url, branch, workspace?}` (wizard text:
`web=<url>#main,api=<url>`). Primární repo (to, co vidí uživatel; jinak podle
`target_repo_url`) je první a drží cesty `<slug>-<X>`; ostatní jsou
`<slug>-<X>-<role>`. Role `be` / `backend` / `api` je backend.

- **Build:** `worktree setup` založí worktrees A/B/C v každém repu na branchi
  `pflanzer/<slug>-<X>`. Prompt (`quick_session prompts`) vypíše repa varianty,
  kontroly **per repo** (npm u Node, make / `.venv` u Pythonu), pravidlo „měň jen
  tato repa“ a příkaz `claude --add-dir <sekundární repa>`. „CONTRACT-FIRST“
  (OpenAPI) se uvede jen u backendu, který má `openapi.*`. `acceptance_feature`
  v `--json` je nastaven, když `.feature` existuje v kterémkoli repu.
- **Preview:** `preview up` spustí pro každou variantu všechna repa. Sekundární
  běží na portu `app + 1000 + idx` (idx = pořadí repa, primární 0); primární dostane
  env `<ROLE>_URL` a `PFLANZER_<ROLE>_URL` (`API_URL=http://127.0.0.1:<port>`).
  Proxy s heslem je jen před primárním. Příkaz sekundárního repa:

  ```toml
  [preview]            # primární repo
  command = "npm run dev -- --port {port}"
  [preview.api]        # sekundární repo s rolí api
  command = ".venv/bin/python -m uvicorn app.main:app --port {port}"
  ```

  Bez `[preview.<role>]` se příkaz autodetekuje (Node / Python); repo bez příkazu
  se přeskočí s varováním. `preview status` ukáže stav po repech, `preview down`
  ukončí vše.
- **Push větví:** `pflanzer/<slug>-<X>` jsou ve worktrees v klonu pod
  `data/targets/<slug>-<X>` (cesta je ve výstupu `worktree setup`), ne v hlavním
  repu: `cd data/targets/<slug>-A && git push origin pflanzer/<slug>-A`.
- **Ship / PR:** gates jedou na vítěze, `handoff_pr` commitne a pushne větev a
  otevře PR do base toho repa **per repo**; PR se odkazují navzájem.

## Install — co si tým musí stáhnout

### Pro tebe (one-time, ~30 sekund)

Skript si můžeš předem prohlédnout: `curl -fsSL …/install.sh -o install.sh; less install.sh`. Mění jen `~/.claude/plugins/pflanzer`, `~/.pflanzer`, `~/.local/bin/pflanzer` a registraci pluginu v Claude Code (viz [`zacni.md`](zacni.md#instalace-v-korporátu-co-přesně-skript-dělá)).

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
1. Vyrobí `docs/INTEGRATION_GUIDE.md` (šablona — vývojář ji nechá vyplnit v Claude Code příkazem „vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“ a zkontroluje; auth pattern, API client, state lib, logger, feature flags, folder layout, test runner).
2. Vyrobí `.pflanzer/project.toml` (pre-populated `target_repo_url` z `git remote get-url origin`).
3. Vytvoří `tests/acceptance/` složku (Charter wizard tam píše `.feature` soubory per session).
4. Update `.gitignore` (`extracted/`, `.pflanzer/local/`).

**Pak commit všeho najednou** (`git add -A docs .pflanzer tests .gitignore .claude/settings.json && git commit -m "chore(pflanzer): init" && git push`), restartuj Claude Code v tom repu a spusť:

```
/pm start            # Kickoff (nebo /pm live "co dnes řešíme" = Kickoff + Build v jednom)
```

Průvodce prvním pilotem (lidi, okna, preview, checklist): [`zacni.md`](zacni.md).

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
# Web hub (async feedback) — venv + build frontendu se připraví samy:
tool/bin/pflanzer hub            # http://localhost:8000/method/ (localhost, bez přihlášení)
                                 # obsazený port: hub navrhne `--port N`; za běhu zapisuje <datová složka>/hub.json
tool/bin/pflanzer hub --host 0.0.0.0 --password …   # pro kolegy v síti
# vývoj frontendu s hot reloadem: cd tool/web/frontend && npm install && npm run dev
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
[`tool/web/README-auth.md`](../tool/web/README-auth.md).

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


## Stav implementace

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
- **Testy a CI** ✅ — `tests/` (pytest, hermetické), ruff, GitHub Actions
  (`.github/workflows/ci.yml`); viz „Testy a CI" níže
- **Měření** ✅ — `/pm retro` (outcome T+7/30/60/90), AI provenance v SHIP.md, AI náklady


## Struktura repa

```
docs/
├── methodology/         # metoda v češtině (start: 00-lean-pflanzer.md)
├── governance/          # audit-grade vrstva (jen regulované / multi-pilot)
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


## Plán fáze 2

Plán fáze 2 byl pracovní dokument mimo repo; rozhodnutí z něj jsou v ADR
(`docs/decisions/`), aktuální stav je v [Stav implementace](#stav-implementace)
a v `CHANGELOG.md`.

## Konvence

- Dokumentace metodiky: **čeština**
- Code, comments v toolu: EN, dle CLAUDE.md
- Git workflow: feature-branche + lokální merge `--no-ff` (NIKDY commit přímo na main)
- ADR formát: `docs/decisions/NNNN-short-slug.md`
