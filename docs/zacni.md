# Začni — první pilot Pflanzer Method

**Pflanzer Method | pflanzer.cz/method**

> Pro toho, kdo chce metodu **vyzkoušet** ve své firmě. Jedna stránka:
> co zařídit s lidmi, co nainstalovat, co se pak děje den po dni.
> Průběh v obrázku: [`postup.md`](postup.md). Šéfovi pošli
> [`pro-decidera.md`](pro-decidera.md) — je to jedna stránka a hotový e-mail.

Potřebuješ **~1 týden přípravy** (hlavně kalendáře) a **~8 dní** na pilot.

---

## Test 30 sekund — hodí se to pro vás?

Metodu **nepoužívejte** (jděte standardním vývojovým procesem), když platí
cokoli z toho:

- **compliance-citlivá věc** — AI Act High-risk, banky v rozsahu DORA
  (bez vrstvy [`governance/`](governance/README.md));
- **platby a platební flow** (PSD2 SCA);
- **silné externí závislosti** (partner, legacy systém, schvalovaný kontrakt),
  které nejdou nasimulovat;
- **nativní mobilní aplikace** s release cyklem přes store;
- **nejasná strategie a nikdo, kdo smí říct Go i Kill** — bez takového
  člověka (Decidera) nezačínejte.

Nic z toho neplatí? Pokračujte. Na první pilot vyberte něco menšího,
než si myslíte.

---

## Kolik to stojí

| Kdo | Kolik času |
|-----|-----------|
| Celkem lidé | **~6–8 člověkodnů** za celý pilot (~8 dní kalendářně) |
| Decider (sponzor) | **15 min** Kickoff + **90 min** Rozhodnutí |
| Bezpečnost & právo | **20 min** (checkpoint nad běžícími variantami) |
| Provoz | **20 min** checkpoint + domluva preview a Ship s vývojáři |
| Jádro (produkt, design, 1–2 vývojáři) | celý Build (3 h), ~15 min denně v Asyncu, Ship |

**Peníze:** žádná licence navíc kromě Claude Code, který už vývojáři
používají. Spotřebu AI tool měří sám — v `SHIP.md` je sekce *AI náklady*
(tokeny za variantu a za celý cyklus), takže šéfovi řeknete reálné číslo,
ne odhad.

**Co říct šéfovi:** „Za týden budeme mít tři běžící varianty na reálném repu,
vy rozhodnete nad nimi (15 + 90 min) a vítěz půjde jako PR přes naše
kontroly. Nic neskončí ve slajdu." Připravený text:
[`pro-decidera.md`](pro-decidera.md).

---

## A. Lidé a domluvy (sponzor nebo PdM, týden předem)

### 1. Vyberte problém

Dobrý první pilot:

- **jedna věc, jedna metrika** — „zrychlit checkout", „self-service vrácení
  zboží", ne „nový e-shop";
- vlastní **existující repo**, do kterého má kód jít;
- nepotřebuje produkční data k vývoji (stačí syntetická).

### 2. Sežeňte jména — 6 kroků cesty

| Krok cesty | Kdo | Kolik času | Nemáte? |
|------------|-----|-----------|---------|
| Byznys | sponzor, který smí říct Go i Kill (= **Decider**) | 15 min + 90 min | nezačínejte |
| Produkt | PdM | celý pilot (jádro) | jen pro rychlý Quick může zastoupit AI, podepisuje Decider |
| Design | designér (u interního toolu může krýt PdM) | celý pilot (jádro) | AI náhrada (UX expert + kontrola přístupnosti), podepisuje PdM |
| Vývoj | 1–2 vývojáři, kteří budou stavět | celý pilot (jádro) + Ship | nezačínejte |
| Bezpečnost & právo | security nebo DPO, stačí jeden | 20 min | AI předkontrola, člověk podepíše |
| Provoz | DevOps / platforma, nebo EM | 20 min + domluva preview | AI předkontrola, u pilotu podepíše vývojář z jádra |

Jeden člověk smí krýt víc kroků. **Krok bez jména a bez povolené AI náhrady =
pilot nezačínejte.** Bez vývojáře u klávesnice to není Pflanzer, ale workshop
s obrázky. Podrobně: [Co když nemáme…](#co-když-nemáme)

### 3. Domluvte s provozem, kde poběží varianty

Potřebujete **preview prostředí pro 3 branche** — to, co už máte:
Vercel / Netlify preview, review apps v GitLabu, preview namespace
v Kubernetes. Bez produkčních dat a bez přístupu do produkční sítě.
Detail: [`postup.md` § Kde varianty fyzicky jsou](postup.md#kde-varianty-fyzicky-jsou).

### 4. Zabookujte okna (všechna najednou, ne ad hoc)

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
# 1. Instalace (jednou na stroj) — plugin /pm + příkaz pflanzer + lokální databáze
curl -fsSL https://raw.githubusercontent.com/gizmax/PflanzerMethod/main/install.sh | bash

# 2. V repu produktu (jednou na repo)
cd /cesta/k/vasemu/repu
pflanzer init

# 3. INTEGRATION_GUIDE (5 min přes Claude Code, ručně ~30 min): v Claude Code napište
#    „vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“ a výsledek zkontrolujte
#    (auth, API klient, state, logger, feature flags, struktura složek, test runner).
#    Zkontrolujte i .pflanzer/CONSTITUTION.md (krátká nepřekročitelná pravidla pro AI).

# 4. Commit a push všeho najednou
git add -A docs .pflanzer tests .gitignore .claude/settings.json && git commit -m "chore(pflanzer): init" && git push -u origin HEAD

# 5. Je repo připravené?
pflanzer doctor
```

Pak **restartujte Claude Code v tom repu** a napište `/pm` — bez argumentu
zjistí stav a doporučí jeden další krok (v čerstvém repu spustí `doctor`
a navrhne `/pm start`).

### Instalace v korporátu: co přesně skript dělá

Skript nemusíte pouštět naslepo. Stáhněte si ho, přečtěte a pak spusťte:

```bash
curl -fsSL https://raw.githubusercontent.com/gizmax/PflanzerMethod/main/install.sh -o install.sh
less install.sh
bash install.sh
```

Mění jen tyto věci v domovském adresáři (nic mimo něj, žádné `sudo`):

| Co | Kde |
|----|-----|
| plugin (příkazy `/pm`, agenti, kód toolu, ~700 KB) | `~/.claude/plugins/pflanzer` |
| lokální data a databáze (zápisy projektů) | `~/.pflanzer` |
| příkaz `pflanzer` | `~/.local/bin/pflanzer` |
| registrace pluginu v Claude Code | `claude plugin marketplace add` + `claude plugin install pflanzer@pflanzer-method` |

Odinstalace: `claude plugin uninstall pflanzer@pflanzer-method` a
`rm -rf ~/.claude/plugins/pflanzer ~/.pflanzer ~/.local/bin/pflanzer`.

### Je repo připravené?

`pflanzer doctor` ukáže checklist a „připraveno ke Kickoffu: ano/ne".
Agent zvládne produkční kód jen v repu, které ho udrží na uzdě. Musí být:

- **testy** a spustitelný `test` skript;
- **lint** a **build** skripty;
- **CI**, které je pouští na každé větvi;
- **preview deploy** větví (bez produkčních dat) — jinak Async nemá na co klikat;
- vyplněný `docs/INTEGRATION_GUIDE.md` a `.pflanzer/CONSTITUTION.md`;
- `pflanzer init` **commitnutý a pushnutý** (kopie repa pro varianty se zakládají z originu).

Co chybí, `doctor` řekne i s radou. Nezačínejte Kickoff na „ne", pokud
chybějící věc vědomě nepřijmete jako riziko.

U **throwaway** dema je `docs/INTEGRATION_GUIDE.md` jen doporučení (⚠, Kickoff
neblokuje) a chybějící CI či lockfile je jen informace. Risk profil se bere z
projektu (`pflanzer doctor --slug <slug>`) nebo z `default_risk_profile` v
`.pflanzer/project.toml`.

---

## C. Den po dni

| Kdy | Co se děje | Příkaz |
|-----|-----------|--------|
| Kickoff | zadání na 1 stránku: problém, metrika, kill kritérium, jména 6 kroků | `/pm start` |
| Build | AI staví 3 varianty ve 3 oddělených kopiích vašeho repa (nebo jednu společnou variantu `mob`, pokud ji zvolíte v Kickoffu), průběžně lint/testy/build; jádro u jedné obrazovky směruje; checkpoint bezpečnost & právo | `/pm live` nebo `/pm build` |
| po Buildu | builder pushne 3 branche (z klonů `data/targets/<slug>-<X>`, ne z hlavního repa) → preview URL (se štítkem „k rozhodnutí, ne produkt") → pošle odkazy všem | — |
| Async | zástupci klikají a komentují (`pflanzer hub`), builder zapracovává | `/pm feedback` |
| Rozhodnutí | demo, top 3 spory, tiché hlasování, Decider poslední → Go / Iterate / Kill | `/pm decide` |
| Ship | automatické kontroly jen na vítěze: pilot ≥ 80 / production ≥ 85 ze 100 (throwaway: skóre informativně, Ship neblokuje), checkpoint provozu, PR do `main` | `/pm ship` → `/pm handoff` |

**Okna se podepisují** jedním příkazem — `pflanzer checkpoint --slug <slug>
bezpecnost|provoz --by "<jméno>" --note "…"`. Bez podpisu Ship pilotu
neprojde (zadání podepisuje Kickoff sám). Kde okno zastoupila AI, zapíše se
jako návrh (`--ai --agent <agent>`) a podepíše ho člověk.

**Kde jste?** `/pm` řekne fázi a jeden další krok. Rozhodnutí se zapisují
do repa: `.pflanzer/decisions/<slug>.md` — commitněte je.

**Spěcháte?** `/pm live "co řešíme"` spojí Kickoff a Build do jednoho
sezení — vhodné pro malý interní tool.

---

## Checklist — připraveno ke Kickoffu

- [ ] Problém v 1 větě + 1 metrika + kill kritérium
- [ ] Jméno (nebo povolená AI náhrada) u všech 6 kroků cesty
- [ ] Decider má mandát říct Go i Kill a ví, že mu to zabere 15 + 90 min
- [ ] Preview prostředí pro 3 branche domluvené s provozem
- [ ] Všechna okna v kalendáři
- [ ] `pflanzer doctor` hlásí „připraveno ke Kickoffu: ano"
- [ ] `/pm` v Claude Code funguje

---

## Co když nemáme…

### …designéra

Design může zastoupit **PdM** (u interního toolu) nebo **AI náhrada**
(UX expert + automatická kontrola přístupnosti). Podepisuje PdM; u produktu
pro zákazníky ve výsledku musí design potvrdit člověk.

### …security nebo DPO na plný úvazek

Stačí 20 minut: AI udělá **předkontrolu** (datový tok, data, síť, strop
nákladů, právní rizika) a člověk ji **podepíše do 48 hodin**. U throwaway
věci stačí AI; u pilotu a produkce bez podpisu člověka Ship neprojde.

Kdo podepíše, když security ve firmě opravdu není — v tomto pořadí:

1. **Někdo z firmy s mandátem** — DPO, IT security, compliance; stačí
   20 minut a tři věty (co aplikace čte, kam píše, jestli vidí reálná data).
2. **Decider vědomě převezme riziko** (`pflanzer session_3 --slug S
   --override-triage --rationale "…"`) — jeho jméno se zapíše do decision
   logu. Jen u pilotu bez osobních dat.
3. **Autor kódu** — jen poslední možnost, u interního nástroje bez osobních
   dat. Nástroj to označí varováním a právo tím pokryté není.

Autor kódu **není výchozí volba**: podepisoval by vlastní práci.

### …security, která nám nechce podepsat

Vyžádejte si písemný důvod a rozlište, jestli chybí podklady, nebo je riziko
skutečné. Pošlete jim tříveté shrnutí (co aplikace čte, kam píše, jestli
vidí reálná data) a nabídněte AI pre-check jako podklad. Bez odpovědi do
48 hodin to eskaluje na Decidera: buď převezme riziko a zapíše to pod svým
jménem, nebo projekt zastaví.

### …DevOps

U **pilotu** podepíše provoz vývojář z jádra (vývoj + provoz je běžná
kombinace), AI předkontrola mu připraví checklist. U produkce musí provoz
podepsat člověk z provozu.

### …Decidera s mandátem

**Nezačínejte.** Bez člověka, který smí říct Go i Kill, vznikne jen víc
variant k diskusi. Nejdřív sežeňte sponzora (stránka [`pro-decidera.md`](pro-decidera.md)).

### …CI

Pilot jde, ale bez CI nemá PR automatické kontroly. `doctor` to ohlásí;
stačí jednoduchý běh lint + test + build na každé větvi.

### …preview prostředí

Určete konkrétního člověka (zástupce provozu) a termín, kdy preview
zprovozní; „domluvíme s provozem“ nestačí.

Build jede lokálně (3 dev servery), ale Async tak nemá na co klikat. Nejrychlejší
je `pflanzer preview up --slug <slug>`: spustí varianty s heslem, přes
`cloudflared` i s veřejnou URL, a vypíše zprávu k přeposlání zástupcům (kód
neopouští firmu; provoz přes tunel jde přes Cloudflare — řekněte to
bezpečnosti). Vercel? Volitelné, ne default; interní GitHub se na něj často
napojit nedá. Další možnost: draft PR s preview nebo nahrávku průchodu (`pflanzer worktree preview`,
viz [`postup.md`](postup.md#kde-varianty-fyzicky-jsou)). Jinak pilot posuňte.

### …možnost sejít se (Build online)

Ano: vývojář sdílí **jednu obrazovku** (jeho Claude Code + běžící varianty), jádro naviguje hlasem; max 5 lidí; checkpoint bezpečnosti online 20 min. **Ne** 3 paralelní breakout místnosti — rozhoduje se nad stejnou obrazovkou. Hlasování tiše najednou přes chat nebo formulář.

### …jediného vývojáře

Jde. Build je delší (varianty staví po sobě, ne paralelně), ostatní z jádra
směrují. Provoz u pilotu pak podepisuje jiný člověk než ten, kdo staví.

### …licenci Claude Code

Pilot bez ní nejde — varianty staví Claude Code. Požádejte o jednu licenci
pro vývojáře; ostatní v týmu ji nepotřebují.

### Projekt přes víc repozitářů

Typicky web + API. Při `/pm start` uveďte repa i s rolemi:
`web=<url>,api=<url>` (první je primární — to, co uživatel vidí). Nic dalšího
nenastavujete:

- **Build:** `pflanzer worktree setup` vyrobí worktrees A/B/C pro **každé** repo
  a prompt ukáže, kde je které repo a že sekundární je připojené přes `--add-dir`.
  Měnit se smí jen repa projektu.
- **Příprava:** `pflanzer init` patří do **každého** repa projektu; `/pm start`
  (a ostatní `/pm` kroky) spouštějte z **primárního** (web) repa.
- **Preview:** `pflanzer preview up` spustí u každé varianty všechna repa. Adresu
  API nikdy nehardcodujte (ani port); aplikace ji bere z proměnné
  (obecně `<ROLE>_URL`):
  - **v prohlížeči** (kód UI): `import.meta.env.VITE_API_URL` (Vite),
    `process.env.NEXT_PUBLIC_API_URL` (Next), `process.env.REACT_APP_API_URL` (CRA),
    např. `fetch(`${import.meta.env.VITE_API_URL}/slots`)`;
  - **na serveru** (SSR, skripty): `API_URL` (absolutní adresa na tomto počítači).

  V preview je prohlížečová proměnná **relativní cesta** `/__pflanzer/api` za
  heslem preview: proxy ji přepošle na API stejné varianty, takže kolegové přes
  tunel nebo síť nesahají na svůj localhost a API je chráněné stejným heslem.
  Neumí-li se repo spustit samo, doplňte do `.pflanzer/project.toml`
  `[preview.api]` s `command = "… {port} …"`.
- **Ship:** quality gates jedou na vítěze, PR vznikne **v každém repu** a PR
  se navzájem odkazují.

### Co přesně smí zastoupit AI

| Krok cesty | AI náhrada? | Kdo podepíše |
|------------|-------------|--------------|
| Byznys (Decider) | **nikdy** | bez Decidera se Kickoff nesvolává |
| Vývoj | **nikdy** | u klávesnice sedí vývojář |
| Produkt | jen Quick / throwaway | Decider (zadání) |
| Design | ano (UX expert + kontrola přístupnosti) | PdM (`pflanzer checkpoint … design`); u zákaznického produktu člověk |
| Bezpečnost & právo | jen **předkontrola** | throwaway: stačí AI; pilot/production: člověk do 48 h (pořadí viz výše) |
| Provoz | jen **předkontrola** | throwaway: AI; pilot: vývojář z jádra; production: člověk z provozu |

AI náhrada je u všeho **vidět** (stav projektu, rozhodnutí, `SHIP.md`) a je
na chvíli — pro další projekt `pflanzer status` připomene sehnat člověka.

---

## Když se něco zasekne

| Problém | Řešení |
|---------|--------|
| `/pm` v Claude Code není | restartujte Claude Code; zkuste **`/pflanzer:pm`**; `claude plugin list` musí ukázat `pflanzer@pflanzer-method` |
| `pflanzer: command not found` | přidejte do `~/.zshrc`: `export PATH="$HOME/.local/bin:$PATH"` |
| nemáme preview prostředí | viz výše „…preview prostředí" |
| bezpečnost nechce syntetická data | nezačínejte; vyberte problém, který produkční data nepotřebuje |
| přišlo 8 lidí | max 5 naráz — ostatní na svá okna, nebo zúžte zadání |
| Iterate podruhé | ne — problém je špatně zadaný, zpět na Kickoff |

## Co měřit

Metoda zatím nemá vlastní data, tak je sbírejte. Tool je zapisuje do handoffu:

- čas Kickoff → merge,
- skóre kontrol vítěze,
- počet kol Iterate,
- kolik kódu vítěze přežije 30 dní v `main`,
- AI náklady (tokeny za variantu a za cyklus) — součást `SHIP.md`,
- podíl kroků cesty, které zastoupila AI.

Po merge vítěze **`/pm retro <slug>`** změří, kolik kódu vítěze žije
v produkci beze změny (cíl ≥ 80 %), za jak dlouho se dostal do produkce
(cíl ≤ 14 dní) a nastaví připomínky za 7, 30, 60 a 90 dní. Hlavní cesta
končí Shipem, ale bez těchto čísel se metoda nedá zlepšovat.

U **throwaway** dema se kód nepředává do produkce: handoff vyrobí jen `SHIP.md`
a `README.md` (co ukázat, jak spustit, co je fake) a retro nepočítá přežití
kódu ani T+30/60/90. Měří se jen metrika dema v jejím termínu (jedna připomínka).

Aktualizace: `pflanzer update`.

---

## Slovníček v 8 řádcích

| Pojem | Znamená |
|-------|---------|
| **Decider** | člověk s mandátem říct Go i Kill; rozhoduje nad běžícím kódem |
| **worktree** | oddělená kopie repa pro každou variantu (A, B, C) |
| **quality gate** | automatická kontrola (lint, testy, build, bezpečnost) |
| **checkpoint** | 20minutové okno s podpisem (bezpečnost & právo, provoz) |
| **Iterate** | ještě jedno kolo stavby, nejvýše jednou |
| **Go / Kill** | jdeme do produkce / končíme |
| **preview** | běžící varianta na URL, kterou si lidé otevřou v prohlížeči |
| **PdM** | produkt manažer |

Celý slovník: [`methodology/glossary.md`](methodology/glossary.md).
