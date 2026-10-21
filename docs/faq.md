# FAQ — výjimky, detaily a „co když…“

**Pflanzer Method | pflanzer.cz/method**

> Pro koho: pro buildera a zástupce, kterým se něco nehodí do základní cesty.
> Hlavní cesta na jedné stránce: [`zacni.md`](zacni.md).

Obsah: [Hodí se to pro nás?](#hodí-se-to-pro-nás) ·
[Kolik to stojí](#kolik-to-stojí) · [Co když nemáme…](#co-když-nemáme) ·
[Víc repozitářů](#projekt-přes-víc-repozitářů) · [Co smí zastoupit AI](#co-přesně-smí-zastoupit-ai) ·
[Instalace v korporátu](#instalace-v-korporátu-co-přesně-skript-dělá) ·
[Je repo připravené?](#je-repo-připravené) · [Tunel a LAN](#tunel-lan-a-preview) ·
[Výjimky a přebití prahu](#výjimky-a-přebití-prahu) ·
[Když se něco zasekne](#když-se-něco-zasekne) · [Co měřit](#co-měřit)

---

## Hodí se to pro nás?

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
| Celkem lidé | **~6–8 člověkodnů** za pilot Lean (~8 dní kalendářně); demo Quick ~5, ostré nasazení ~14 (plán z Kickoffu, `report summary` ho uvádí se zdrojem) |
| Decider (sponzor) | **15 min** Kickoff + **90 min** Rozhodnutí |
| Bezpečnost & právo | **20 min** (checkpoint nad běžícími variantami); u pilotu bez osobních dat jedno sloučené okno **Bezpečnost a provoz** |
| Provoz | **20 min** checkpoint + domluva preview a Ship s vývojáři |
| Jádro (produkt, design, 1–2 vývojáři) | celý Build (3 h), ~15 min denně ve sběru feedbacku, Ship |

**Peníze:** žádná licence navíc kromě Claude Code, který už vývojáři
používají. Spotřebu AI tool měří sám — v `SHIP.md` je sekce *AI náklady*
(tokeny za variantu a za celý cyklus), takže šéfovi řeknete reálné číslo,
ne odhad.

**Co říct šéfovi:** „Za týden budeme mít tři běžící varianty na reálném repu,
vy rozhodnete nad nimi (15 + 90 min) a vítěz půjde jako PR přes naše
kontroly. Nic neskončí ve slajdu." Připravený text:
[`pro-decidera.md`](pro-decidera.md).

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
2. **Decider vědomě převezme riziko** (`pflanzer ship --slug S
   --override-triage --rationale "…"`) — jeho jméno se zapíše do decision
   logu. Jen u pilotu bez osobních dat.
3. **Autor kódu** — jen poslední možnost, u interního nástroje bez osobních
   dat. Nástroj to označí varováním a právo tím pokryté není.

Autor kódu **není výchozí volba**: podepisoval by vlastní práci.

Podpis s výhradami (např. „CSRF, rate limit, informace dle čl. 13“) zapište
jako podmínky: `pflanzer checkpoint … --conditions "CSRF; rate limit; čl. 13"`.
Ship je neblokuje, ale uvidíte je v SHIP.md i v checklistu PR, aby se neztratily.

**Co přesně blokuje Ship (Lean):** plný triage (`/pm triage`) se u Lean
nespouští, jen u stupně Full. Tvrdá brána Shipu u pilotu a production ale
hlídá stav triage tracků, a ty u Lean plní podpisy oken (zadání → discovery,
bezpečnost & právo → security + legal, provoz → platform). Ship tedy blokuje
nepodepsané či zablokované okno a AI draft bez podpisu člověka; throwaway
neblokuje nic.

### Triage bez Claude Code

U stupně Full (ostré s osobními údaji) `pflanzer start` doporučí `/pm triage`. Bez
Claude Code zapište výsledky čtyř tracků do `triage.json` a spusťte
`pflanzer triage --spec triage.json` (stejné schéma ukáže `pflanzer triage --help`):

```json
{
  "slug": "moje-appka",
  "results": [
    {"track": "discovery", "status": "ok", "signed_by": "Dana Nováková",
     "rationale": "persona a JTBD ověřeny s 5 uživateli", "artefact_md": "# Discovery\n…"},
    {"track": "security", "status": "ok", "signed_by": "Jana Svobodová",
     "rationale": "datový tok a hrozby prošly",
     "conditions": [{"id": "K1", "text": "logy bez osobních údajů"}],
     "artefact_md": "# Security\n…"},
    {"track": "legal", "status": "deferred", "signed_by": "Marie Dvořáková (DPO)",
     "rationale": "DPIA se dokončuje",
     "conditions": [{"id": "D1", "text": "DPIA hotová před Shipem"}],
     "artefact_md": "# Legal\n…"},
    {"track": "platform", "status": "ok", "signed_by": "Karel Dvořák",
     "rationale": "sandbox a runtime schváleny", "artefact_md": "# Platform\n…"}
  ]
}
```

`status` je `ok`, `blocked` nebo `deferred`. `signed_by` je **podpis člověka**, který
track ověřil; prázdné znamená, že track čeká na podpis (`pending`). `conditions`
jsou volitelné podmínky, které převezme podpis okna (viz `pflanzer checkpoint
--help`). Po triage podepisují okna lidé (`pflanzer checkpoint … --by "<jméno>"`);
AI návrh (`--ai`) už podepsané okno nikdy nepřepíše. Právo (DPIA) je samostatné okno
`checkpoint … pravo` jen když triage legal odložil (`deferred`) a security je `ok`;
jinak ho podepíšete spolu s bezpečností. Podmínky z odloženého legal tracku
(např. DPIA) patří do okna Právo.

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

Build jede lokálně (3 dev servery), ale sběr feedbacku tak nemá na co klikat. Nejrychlejší
je `pflanzer share --slug <slug>` (po `pflanzer record`): spustí varianty s heslem, přes
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

---

### Projekt přes víc repozitářů

Typicky web + API. Při `/pm start` uveďte repa i s rolemi:
`web=<url>,api=<url>` (první je primární — to, co uživatel vidí). Nic dalšího
nenastavujete:

- **Build:** `pflanzer worktree setup` vyrobí worktrees A/B/C pro **každé** repo
  a prompt ukáže, kde je které repo a že sekundární je připojené přes `--add-dir`.
  Měnit se smí jen repa projektu.
- **Příprava:** `pflanzer init` patří do **každého** repa projektu; `/pm start`
  (a ostatní `/pm` kroky) spouštějte z **primárního** (web) repa.
- **Preview:** `pflanzer share` (pod ním `preview up`) spustí u každé varianty všechna repa. Adresu
  API nikdy nehardcodujte (ani port); aplikace ji bere z proměnné
  (obecně `<ROLE>_URL`):
  - **v prohlížeči** (kód UI): `import.meta.env.VITE_API_URL` (Vite),
    `process.env.NEXT_PUBLIC_API_URL` (Next), `process.env.REACT_APP_API_URL` (CRA),
    např. `fetch(`${import.meta.env.VITE_API_URL}/api/slots`)` (proxy odřízne jen
    `/__pflanzer/<role>`, cesta API `/api/slots` zůstává);
  - **na serveru** (SSR, skripty): `API_URL` (absolutní adresa na tomto počítači).

  V preview je prohlížečová proměnná **relativní cesta** `/__pflanzer/api` za
  heslem preview: proxy ji přepošle na API stejné varianty, takže kolegové přes
  tunel nebo síť nesahají na svůj localhost a API je chráněné stejným heslem.
  Neumí-li se repo spustit samo, doplňte do `.pflanzer/project.toml`
  `[preview.api]` s `command = "… {port} …"`.
- **Ship:** quality gates jedou na vítěze, PR vznikne **v každém repu** a PR
  se navzájem odkazují.

---

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

---

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
- **preview deploy** větví (bez produkčních dat) — jinak sběr feedbacku nemá na co klikat;
- vyplněný `docs/INTEGRATION_GUIDE.md` a `.pflanzer/CONSTITUTION.md`;
- `pflanzer init` **commitnutý a pushnutý** (kopie repa pro varianty se zakládají z originu).

Co chybí, `doctor` řekne i s radou. Nezačínejte Kickoff na „ne", pokud
chybějící věc vědomě nepřijmete jako riziko.

U **throwaway** dema je `docs/INTEGRATION_GUIDE.md` jen doporučení (⚠, Kickoff
neblokuje) a chybějící CI či lockfile je jen informace. Risk profil se bere z
projektu (`pflanzer doctor --slug <slug>`) nebo z `default_risk_profile` v
`.pflanzer/project.toml`.

---

## Tunel, LAN a preview

Nejrychlejší cesta, jak dát kolegům jednu adresu a heslo, je
`pflanzer share --slug <slug>` (až po zápisu Buildu `pflanzer record`, jinak hub
varianty neukáže): spustí preview variant i hub a vypíše jednu zprávu k přeposlání. Zastavení: `pflanzer share down --slug <slug>`.

Pod ním jsou dvě části, které můžete spouštět i zvlášť:

- **Preview variant:** `pflanzer preview up --slug <slug>` (nebo `status`,
  `down`). Před každou variantou postaví proxy s heslem (uživatel `pflanzer`)
  a štítkem „k rozhodnutí, ne produkt“. S `cloudflared` v PATH (`--tunnel auto`)
  dostane každá varianta veřejnou URL, jinak jen lokální / LAN
  (`--host 0.0.0.0`). Provoz přes tunel jde přes Cloudflare — zapište to na
  checkpointu bezpečnosti. Počítač buildera musí běžet po celý sběr feedbacku.
- **Hub:** `pflanzer hub` (lokálně bez přihlášení; pro kolegy
  `--host 0.0.0.0 --password …`) sbírá odkazy a feedback. Offline varianta:
  `pflanzer feedback add`.

Další možnosti: preview deploy firmy (Vercel / Netlify / review apps),
draft PR (`pflanzer worktree preview --slug <slug>`) nebo nahrávka průchodu
(`--mode playwright`). Podrobně: [`postup.md`](postup.md#kde-varianty-fyzicky-jsou).

## API hubu

Pro skripty a automatizaci (hub musí běžet, `pflanzer hub` / `pflanzer share`):

- `GET /api/projects/<slug>/missing` — co v projektu ještě chybí,
- `GET /api/projects/<slug>/windows` — stav oken k podpisu,
- `GET` / `POST /api/projects/<slug>/votes` — tiché hlasování jádra (informativní, rozhoduje Decider).

Hub sám ukazuje pohled podle role (co má kdo posoudit), kdo ještě chybí,
okna k podpisu s hotovým příkazem a termín feedbacku.

Cesty jsou pod `/api/projects/`, **ne** pod `/method/` (to je webové rozhraní).
Přihlášení heslem hubu přes HTTP Basic, jméno je libovolné (např.
`curl -u pflanzer:HESLO http://adresa/api/projects/<slug>/windows`).

---

## Výjimky a přebití prahu

- **Přebití prahu Shipu** (`pflanzer ship --slug S --override-threshold
  --rationale "…"`): Decider vědomě bere skóre pod práh (pilot 80 / production 85)
  na sebe, jeho jméno jde do decision logu. Odkud jsou čísla 80 / 85 a 60 %
  závaznosti a jak se kalibrují: [ADR-0024](decisions/0024-prahy-a-zavaznost.md).
  Go pod 60 % závaznosti jde jen přes `pflanzer decide … --force --rationale`.
- **Přebití triage / podpisu bezpečnosti** (`pflanzer ship --slug S
  --override-triage --rationale "…"`): jen pilot bez osobních dat, zapíše se
  jméno Decidera; právo to nepokrývá.
- **Throwaway:** skóre je informativní, Ship neblokuje.
- **Mob** (jedna společná varianta u jednoho monitoru, ADR-0016) je výjimka,
  ne otázka: Kickoff ji nenabízí, zvolí se jen na výslovné přání jádra.
- **Iterate podruhé** ne — problém je špatně zadaný, zpět na Kickoff.

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
| `pflanzer share` selhal nebo dlouho mlčel | viz odstavec níže |

**Sdílení / hub selhal.** `pflanzer share` průběžně píše, co dělá. Selže-li hub
(nejčastěji první stažení závislostí kvůli síti nebo proxy), varianty, které
sdílení spustilo, zastaví a vypíše poslední řádky logu s cestou
(`<data>/preview/<slug>-hub.log`). Zkuste `pflanzer share --slug S` znovu — napůl
vytvořené prostředí hubu se smazalo a běžící varianty se převezmou. Zůstane-li
něco viset, `pflanzer share down --slug S` uklidí varianty i hub a pak spusťte
sdílení znovu.

## Co měřit

Metoda zatím nemá vlastní data, tak je sbírejte. Tool je zapisuje do handoffu:

- dny od Go do merge,
- skóre kontrol vítěze,
- počet kol Iterate,
- kolik kódu vítěze přežije 30 dní v `main`,
- AI náklady (tokeny za variantu a za cyklus) — součást `SHIP.md`,
- podíl kroků cesty, které zastoupila AI.

Po merge vítěze **`/pm retro <slug>`** změří, kolik kódu vítěze žije
v produkci beze změny (cíl ≥ 80 %), za kolik dní od Go se dostal do merge
(cíl ≤ 14 dní) a nastaví připomínky za 7, 30, 60 a 90 dní. Hlavní cesta
končí Shipem, ale bez těchto čísel se metoda nedá zlepšovat.

U **throwaway** dema se kód nepředává do produkce: `pflanzer ship` vyrobí `SHIP.md`,
`pflanzer handoff --slug S` přidá `README.md` (co ukázat, jak spustit, co je fake) a retro nepočítá přežití
kódu ani T+30/60/90. Měří se jen metrika dema v jejím termínu (jedna připomínka).

Aktualizace: `pflanzer update`.

