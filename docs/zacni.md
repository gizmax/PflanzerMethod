# Začni — první pilot Pflanzer Method

**Pflanzer Method | pflanzer.cz/method**

> Pro koho: pro **buildera** (PdM nebo vývojáře), který pilot rozjíždí.
> Šéfovi (Decideru) pošlete [`pro-decidera.md`](pro-decidera.md), průběh v obrázku
> je v [`postup.md`](postup.md), výjimky a „co když…“ ve [`faq.md`](faq.md).

Metoda: malá skupina se zástupci celé cesty od nápadu po provoz postaví s AI
tři běžící varianty na vašem reálném repu, Decider rozhodne nad nimi a vítěz
jde jako PR. Potřebujete **~1 týden přípravy** (hlavně kalendáře) a **~8 dní**
na pilot. Hodí se to na menší věc s jednou metrikou; **nehodí** na platby,
regulované banky, nativní mobilní appky ani projekt bez člověka, který smí
říct Go i Kill — [test 30 sekund](faq.md#hodí-se-to-pro-nás).

## Kolik to stojí

Plán z Kickoffu podle stupně a risk profilu: pilot Lean **~6–8 člověkodnů**,
demo Quick ~5, ostré nasazení ~14 (`report summary` uvádí číslo se zdrojem).
Žádná licence navíc kromě Claude Code. Decider dá **15 min + 90 min**, bezpečnost & právo a provoz po **20 min**.
Tabulka a text pro šéfa: [`faq.md`](faq.md#kolik-to-stojí).

## Checklist před startem

- [ ] Problém v 1 větě + 1 metrika + kill kritérium
- [ ] **Jméno u všech 6 kroků cesty**: byznys (Decider, smí říct Go i Kill),
      produkt, design, vývoj, bezpečnost & právo, provoz. Jeden člověk smí krýt
      víc kroků; kde nikdo není, viz [Co když nemáme…](faq.md#co-když-nemáme)
- [ ] Všechna okna v kalendáři (tabulka níže)
- [ ] Preview prostředí pro varianty domluvené s provozem (nebo
      [`pflanzer share`](faq.md#tunel-lan-a-preview))
- [ ] `pflanzer doctor` hlásí „připraveno ke Kickoffu: ano“

Max 5 lidí naráz. Krok bez jména a bez povolené AI náhrady = pilot nezačínejte.

## Instalace (vývojář, ~30 min)

Předpoklady: `git`, `python3 ≥ 3.10`, `node ≥ 20.11`,
[Claude Code](https://claude.com/claude-code). Co skript mění:
[`faq.md`](faq.md#instalace-v-korporátu-co-přesně-skript-dělá).

```bash
curl -fsSL https://raw.githubusercontent.com/gizmax/PflanzerMethod/main/install.sh | bash   # jednou na stroj
cd /cesta/k/vasemu/repu && pflanzer init     # jednou na repo
# INTEGRATION_GUIDE: 5 min přes Claude Code („vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“),
# ručně ~30 min; výsledek zkontroluj. Zkontroluj i .pflanzer/CONSTITUTION.md.
git add -A docs .pflanzer tests .gitignore .claude/settings.json && git commit -m "chore(pflanzer): init" && git push -u origin HEAD
pflanzer doctor                              # je repo připravené?
```

V Claude Code v tom repu pak stačí **`/pm`** — zjistí stav a řekne jeden další
krok. V čerstvém repu `/pm` provede i `init` a `doctor` za vás.

Víc repozitářů (web + API): `pflanzer init` patří do každého z nich, detaily
v [`faq.md`](faq.md#projekt-přes-víc-repozitářů).

## Cesta krok za krokem

Na každém kroku stačí jeden příkaz (v Claude Code `/pm <krok>`).

| # | Krok | Příkaz | Kdo, kolik |
|---|------|--------|-----------|
| 1 | Kickoff: zadání na 1 stránku, jména 6 kroků, otázka „Jak vážné to je? demo / pilot / ostré“ | `/pm start` (bez Claude Code: `pflanzer start --spec kickoff.json`) | Decider + jádro, 15 min |
| 2 | Build: AI staví 3 varianty, kontroly běží průběžně | `/pm build` (nápověda: `pflanzer build`; kód píšete ručně? `pflanzer worktree setup --slug S --builder manual`) | jádro, 3 h |
| 3 | Zápis hodnocení Buildu (hub bez něj varianty neukáže) | `pflanzer record --spec soubor.json` | builder |
| 4 | Sdílení: preview i hub, jedna adresa + heslo, hotová zpráva kolegům | `pflanzer share --slug S` | builder, 5 min |
| 5 | Sběr feedbacku (Async): zástupci proklikají a komentují | `/pm feedback` (terminál: `pflanzer feedback add --slug S --variant A --role Design --by "Jméno" --severity critical\|major\|minor --text "…"`, přehled `pflanzer feedback list --slug S`) | všichni, ~15 min denně, 3–5 dní |
| 6 | Rozhodnutí: demo, top 3 spory, Decider hlasuje poslední → Go / Iterate (max 1×) / Kill | `/pm decide` (`pflanzer decide`) | Decider + jádro, 60–90 min |
| 7 | Ship: kontroly jen na vítěze, nástroj vyrobí `SHIP.md` a text PR; PR otevře vlastník repa příkazem `gh pr create` z konce `SHIP.md` | `/pm ship` (`pflanzer ship --slug S`) | vývojáři + provoz, 1–2 dny |
| 8 | Retro: kolik kódu vítěze žije v produkci | `/pm retro S` (`pflanzer retro measure --slug S --pr-url URL`, bez gh `--merge-commit <sha>`) | builder, po merge |

Slug (krátký) vypíše Kickoff; lze ho zadat i ve specu (`"slug"`). Po sběru feedbacku
(po Rozhodnutí) zastavíte sdílení: `pflanzer share down --slug S`. Report pro vedení:
`pflanzer report summary --slug S`. Termín ve zprávě kolegům se spočítá z délky sběru
feedbacku; vlastní zadáte `pflanzer share --slug S --deadline "pátek 17:00"`.
Souhrn feedbacku: `/pm feedback` (terminál `pflanzer feedback_pull --slug S`).
**Kde jste?** `/pm` řekne fázi a jeden další krok. Rozhodnutí se zapisují do
repa (`.pflanzer/decisions/<slug>.md`) — commitněte je. Spěcháte? `/pm live
"co řešíme"` spojí Kickoff a Build (stupeň Quick, 60–90 min).

### Jak vážné to je?

Kickoff se ptá jen na tohle: **demo** (throwaway), **pilot**, nebo **ostré**
(production), plus jestli jsou v datech osobní údaje (`personal_data: true` znamená třídu dat aspoň L3 —
nižší `data_class` se přepíše na L3 s varováním, takže pilot s osobními daty nikdy nedostane sloučené okno). Stupeň Quick / Lean / Full,
okna, režim stavby a prahy se z toho odvodí; přebít je lze
([`faq.md`](faq.md#výjimky-a-přebití-prahu)). Práh Shipu: pilot ≥ 80, production
≥ 85 ze 100 (throwaway: skóre informativně, Ship neblokuje).

| Odpověď | Stupeň | Okna k podpisu |
|---|---|---|
| demo | Quick | žádná (triage se nespouští; před pilotem nový Kickoff) |
| pilot bez osobních dat | Lean | **Zadání** (samo při Kickoffu) + **Bezpečnost a provoz** (`checkpoint … bezpecnost-provoz`) |
| pilot s osobními daty | Lean | Zadání, Bezpečnost & právo, Provoz |
| ostré | Lean (s osobními daty Full) | Zadání, Bezpečnost & právo, Provoz (u Full Právo (DPIA) samostatně jen když triage DPIA odloží) |

### Okna a podpisy

| Termín | Co | Kdo |
|--------|-----|-----|
| Den 0 | Kickoff 15 min | Decider + jádro |
| Den 1–5 | Build 3 h + checkpoint bezpečnost & právo 20 min | jádro (+ bezpečnost & právo) |
| Den 1–6 | Sběr feedbacku 3–5 dní | všichni |
| Den ~7 | Rozhodnutí 60–90 min | Decider + jádro |
| Den ~8 | Ship 1–2 dny + checkpoint provozu 20 min | vývojáři + provoz |

Okno se podepisuje jedním příkazem: `pflanzer checkpoint --slug S
bezpecnost|provoz|bezpecnost-provoz --by "<jméno>" --note "…"`. **Zadání se
podepíše samo při Kickoffu** jménem Decidera (když je ve specu metrika, kill
kritérium a jména kroků); `pflanzer status` ho ukáže mezi podpisy. Ručně
(`checkpoint … zadani --by "<jméno Decidera>"`, jméno, ne slovo „Decider“) jen když
Kickoff šel bez metriky nebo kill kritéria. Bez podpisů Ship pilotu neprojde.
Kde okno zastoupila AI, zapíše se jako návrh (`--ai --agent <agent>`) a podepíše
ho člověk. **Design za AI** je zapsaný už v Kickoffu: člověk (PdM) jen potvrdí
`pflanzer checkpoint --slug S design --by "Jméno" --note "co jste zkontrolovali"`;
`--ai` použijte jen, když AI návrh vzniká až dodatečně. Kdo podepíše, když
security není: [`faq.md`](faq.md#security-nebo-dpo-na-plný-úvazek).

### Bez Claude Code

Kickoff jde i z terminálu: zapište spec do `kickoff.json` a spusťte
`pflanzer start --spec kickoff.json` (všechna pole: `pflanzer start --help`).

```json
{"hook": "Rychlejší schvalování žádostí", "decider_name": "Dana Nováková",
 "risk_profile": "pilot", "personal_data": false,
 "metric": "10 z 15 lidí otevře přehled 3× týdně do 30 dnů",
 "kill_criteria": "do 30 dnů přehled otevře méně než 5 lidí",
 "target_repo_url": "https://github.com/firma/appka",
 "path_owners": {"byznys": "Dana", "produkt": "Petr", "design": "AI", "vyvoj": "Tomáš",
                 "bezpecnost": "Jana", "provoz": "Karel"}}
```

Stupeň Full (ostré s osobními údaji) doporučí `/pm triage`; bez Claude Code zapište
4 výsledky (discovery, security, legal, platform) do `triage.json` a spusťte
`pflanzer triage --spec triage.json` (schéma a ukázka: `pflanzer triage --help`,
[`faq.md`](faq.md#triage-bez-claude-code)). `signed_by` v triage je podpis člověka;
prázdné = čeká na podpis.

Další kroky v terminálu: `pflanzer build` (nápověda k Buildu), `pflanzer prompts --slug S`,
`pflanzer record --spec soubor.json` (zápis Buildu), `pflanzer share --slug S` (sdílení
ke sběru feedbacku), `pflanzer decide`, `pflanzer ship`.

## Zasekli jste se?

`/pm` v Claude Code není → restartujte Claude Code, zkuste `/pflanzer:pm`.
`pflanzer: command not found` → `export PATH="$HOME/.local/bin:$PATH"`.
Ostatní: [`faq.md`](faq.md#když-se-něco-zasekne). Co měřit a slovníček:
[`faq.md`](faq.md#co-měřit), [`methodology/glossary.md`](methodology/glossary.md).
