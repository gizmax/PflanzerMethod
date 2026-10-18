# Začni — první pilot Pflanzer Method

**Pflanzer Method | pflanzer.cz/method**

> Pro toho, kdo chce metodu **vyzkoušet** ve své firmě. Jedna stránka:
> co zařídit s lidmi, co nainstalovat, co se pak děje den po dni.
> Průběh v obrázku: [`postup.md`](postup.md).

Potřebuješ **~1 týden přípravy** (hlavně kalendáře) a **~8 dní** na pilot.

---

## A. Lidi a domluvy (sponzor nebo PM, týden předem)

### 1. Vyber problém

Dobrý první pilot:

- **jedna věc, jedna metrika** — „zrychlit checkout", „self-service vrácení zboží", ne „nový e-shop";
- vlastní **existující repo**, do kterého má kód jít;
- nepotřebuje produkční data k vývoji (stačí syntetická).

Nehodí se: platební flow (PSD2 SCA), AI Act High-risk, banky v DORA scope
bez [`governance/`](governance/README.md). Na první pilot vyber něco jiného.

### 2. Sežeň jména — 6 kroků cesty

| Krok cesty | Kdo | Kolik času |
|------------|-----|-----------|
| Byznys | sponzor s mandátem říct Go/Kill (= **Decider**) | 15 min + 90 min |
| Produkt | PM | celý pilot (jádro) |
| Design | designér (u interního toolu může krýt PM) | celý pilot (jádro) |
| Vývoj | 1–2 vývojáři, kteří budou stavět | celý pilot (jádro) + Ship |
| Bezpečnost & právo | security nebo DPO, stačí jeden | 20 min |
| Provoz | DevOps / platforma, nebo EM | 20 min + domluva preview |

Jeden člověk smí krýt víc kroků. **Krok bez jména = pilot nezačínej.**
Bez vývojáře v jádru to není Pflanzer, ale workshop s obrázky.

### 3. Domluv s provozem, kde poběží varianty

Potřebuješ **preview prostředí pro 3 branche** — to, co už máte:
Vercel / Netlify preview, review apps v GitLabu, preview namespace
v Kubernetes. Bez produkčních dat a bez přístupu do produkční sítě.
Detail: [`postup.md` § Kde varianty fyzicky jsou](postup.md#kde-varianty-fyzicky-jsou).

### 4. Zabookuj okna (všechna najednou, ne ad hoc)

| Termín | Co | Kdo |
|--------|-----|-----|
| Den 0 | Kickoff 15 min | Decider + jádro |
| Den 1–5 | Build 3 h (+ 20 min checkpoint na konci) | jádro (+ bezpečnost & právo) |
| Den 1–6 | Async 3–5 dní, ~15 min denně klikání | všichni |
| Den ~7 | Rozhodnutí 60–90 min | Decider + jádro |
| Den ~8 | Ship 1–2 dny (+ 20 min checkpoint) | vývojáři + provoz |

---

## B. Technika (vývojář, ~30 min, před Kickoffem)

**Předpoklady:** `git`, `python3 ≥ 3.10`, `node ≥ 20.11`,
[Claude Code](https://claude.com/claude-code) (`claude` v PATH, přihlášený).

```bash
# 1. Instalace (jednou na stroj) — plugin /pm + CLI pflanzer + lokální DB
curl -fsSL https://raw.githubusercontent.com/gizmax/PflanzerMethod/main/install.sh | bash

# 2. V repu produktu (jednou na repo)
cd /cesta/k/vasemu/repu
pflanzer init

# 3. Vyplň docs/INTEGRATION_GUIDE.md (~30 min): auth, API klient, state,
#    logger, feature flags, struktura složek, test runner — AI se podle
#    toho drží vašich konvencí. Pak commit:
git add docs/INTEGRATION_GUIDE.md .pflanzer/ tests/acceptance/
git commit -m "chore(pflanzer): init project"
```

Pak **restartuj Claude Code v tom repu** a zkontroluj, že `/pm` existuje
(napiš `/pm` — bez argumentu ukáže stav a nabídne další krok).

> Instaluj přes `install.sh`, ne jen `/plugin install` v Claude Code —
> slash commandy potřebují i CLI `pflanzer`, které instaluje skript.

---

## C. Den po dni

| Kdy | Co se děje | Příkaz |
|-----|-----------|--------|
| Kickoff | zadání na 1 stránku: problém, metrika, kill kritérium, jména 6 kroků | `/pm start` |
| Build | AI staví 3 varianty ve 3 worktrees vašeho repa; jádro u jedné obrazovky směruje | `/pm live` nebo `/pm build` |
| po Buildu | builder pushne 3 branche → preview URL → pošle odkazy všem | — |
| Async | zástupci klikají a komentují, builder zapracovává | `/pm feedback` |
| Rozhodnutí | demo, top 3 spory, tiché hlasování, Decider poslední → Go / Iterate / Kill | `/pm decide` |
| Ship | quality gates ≥ 80/100, checkpoint provozu, PR do `main` | `/pm ship` → `/pm handoff` |

**Spěcháte?** `/pm live "co řešíme"` spojí Kickoff a Build do jednoho
sezení — vhodné pro malý interní tool.

---

## Checklist — připraveno ke Kickoffu

- [ ] Problém v 1 větě + 1 metrika + kill kritérium
- [ ] Jméno u všech 6 kroků cesty
- [ ] Decider má mandát říct Go i Kill
- [ ] Preview prostředí pro 3 branche domluvené s provozem
- [ ] Všechna okna v kalendáři
- [ ] `pflanzer init` v repu + vyplněný `INTEGRATION_GUIDE.md` commitnutý
- [ ] `/pm` v Claude Code funguje

---

## Když se něco zasekne

| Problém | Řešení |
|---------|--------|
| `/pm` v Claude Code není | restartuj Claude Code; `claude plugin list` musí ukázat `pflanzer@pflanzer-method` |
| `pflanzer: command not found` | přidej do `~/.zshrc`: `export PATH="$HOME/.local/bin:$PATH"` |
| nemáme preview prostředí | Build jede lokálně (3 dev servery); na Async nejde — bez URL nemají zástupci na co klikat. Zařiď preview, nebo pilot posuň |
| bezpečnost nechce syntetická data | nezačínej; vyber problém, který produkční data nepotřebuje |
| přišlo 8 lidí | max 5 naráz — ostatní na svá okna, nebo rozděl scope |
| Iterate podruhé | ne — problém je špatně zadaný, zpět na Kickoff |

Aktualizace: `pflanzer update`. Odinstalace: viz konec výpisu `install.sh`.
