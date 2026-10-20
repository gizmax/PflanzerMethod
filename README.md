# Pflanzer Method

**Pflanzer Method | [pflanzer.cz/method](https://pflanzer.cz/method)**

> Pro koho: pro Decidera, buildera i zástupce kroků cesty, kteří chtějí metodu vyzkoušet.

## Co to je

Malá skupina lidí, ve které je zastoupena **celá cesta od nápadu do produkce**
(byznys, produkt, design, vývoj, bezpečnost & právo, provoz), postaví s AI
asistentem **tři funkční varianty** na reálném repu. Šéf (Decider) rozhodne
nad běžícím kódem: jdeme, upravíme jednou, nebo končíme. Vítěz jde rovnou
jako pull request, nic se nepřepisuje.

Jádro 3–4 lidí je u toho celou dobu, ostatní přijdou na 20minutová okna.
Nikdy víc než 5 lidí naráz. Když v rámci firmy někdo z kroků chybí, může
ho v omezené míře zastoupit AI, ale podepisuje vždy člověk.

## Komu to pomůže

- **Firmě, kde nápad putuje měsíce** od zadání přes produkt a vývoj až
  k bezpečnosti a provozu a každé předání ztrácí kontext.
- **Sponzorovi**, který chce rozhodovat podle věci, která běží, ne podle
  slajdů: [`docs/pro-decidera.md`](docs/pro-decidera.md) (1 stránka a hotový e-mail).
- **PdM a vývojářům**, kteří chtějí vyzkoušet pilot za ~8 dní a ~6–8
  člověkodnů celkem, bez nové licence kromě Claude Code.

**Nehodí se** pro platby (PSD2), regulované banky a pojišťovny, nativní
mobilní appky ani projekty bez člověka, který smí říct Go i Kill.
Test 30 sekund je na začátku [`docs/zacni.md`](docs/zacni.md).

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/gizmax/PflanzerMethod/main/install.sh | bash   # jednou na stroj
cd /cesta/k/vasemu/repu && pflanzer init     # jednou na repo (vyplňte docs/INTEGRATION_GUIDE.md)
git add -A docs .pflanzer tests .gitignore .claude/settings.json && git commit -m "chore(pflanzer): init" && git push
pflanzer doctor          # je repo připravené? řekne i co opravit
/pm start                # v Claude Code: Kickoff, 15 min (bez Claude Code: pflanzer start --spec kickoff.json)
```

Nebo v Claude Code rovnou `/pm` — v čerstvém repu provede `init` i `doctor`
samo. **Jediný příkaz, který si musíte pamatovat, je `/pm`**; řekne, kde
projekt je, a doporučí jeden další krok (nenajdete-li ho, zkuste `/pflanzer:pm`).
Celá cesta jedním příkazem na krok (`start` → `build` → `share` → `record` →
sběr feedbacku → `decide` → `ship` → `retro`) je na jedné stránce v
[`docs/zacni.md`](docs/zacni.md); výjimky ve [`docs/faq.md`](docs/faq.md).

```
Kickoff            /pm start     15 min, Decider + jádro     zadání na 1 stránku + jména 6 kroků
Build              /pm build     3 h, jádro                  3 varianty paralelně, kontroly průběžně,
                                                             20min checkpoint bezpečnost & právo
Sběr feedbacku     /pm feedback  3–5 dní, všichni            klikání na preview URL (Async)
Rozhodnutí         /pm decide    60–90 min, Decider + jádro  Go / Iterate (max 1×) / Kill
Ship               /pm ship      1–2 dny, vývojáři + provoz  kontroly jen na vítěze, PR do main
```

Tři pravidla: každý krok cesty má jméno · max 5 lidí naráz · co umí automat,
nepotřebuje člověka v místnosti.

Stupně: výchozí je **Lean** (Build 3 h). **Quick** (`/pm live`) spojí Kickoff
a Build do 60–90 min, **Full** je pro regulované prostředí
([tabulka stupňů](docs/methodology/00-lean-pflanzer.md)).

## Kam dál

- [`docs/zacni.md`](docs/zacni.md) — první pilot na jedné stránce: checklist, instalace, cesta krok za krokem
- [`docs/faq.md`](docs/faq.md) — výjimky: co když nemáme designéra či security, víc repozitářů, tunel, měření
- [`docs/pro-decidera.md`](docs/pro-decidera.md) — stránka pro šéfa a hotový e-mail
- [`docs/postup.md`](docs/postup.md) — postup v 5 krocích a diagramy
- [`docs/methodology/00-lean-pflanzer.md`](docs/methodology/00-lean-pflanzer.md) — 1-pager metody
- [`docs/governance/`](docs/governance/README.md) — vrstva pro regulované prostředí (běžný projekt ji nepotřebuje)
- [`docs/research/srovnani-metod-2026.md`](docs/research/srovnani-metod-2026.md) — srovnání s AI-DLC, Spec Kit, Kiro a dalšími
- [`docs/dev.md`](docs/dev.md) — pro vývojáře toolu: builder, instalace, dev setup, hub, testy, struktura repa

## Stav

Metoda a tool v0.5 jsou hotové end-to-end: Kickoff, Build, Async, Rozhodnutí,
Ship, měření po nasazení (`/pm retro`), AI náklady a AI náhrada chybějícího
zástupce. Čísla z reálných pilotů zatím chybí; tool je sbírá (čas Kickoff → merge,
skóre kontrol, přežití kódu). Podrobný stav a historie:
[`docs/dev.md`](docs/dev.md#stav-implementace), [`CHANGELOG.md`](CHANGELOG.md).
