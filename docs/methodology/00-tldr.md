# TL;DR — rozcestník

**Pflanzer Method | pflanzer.cz/method**

> Pro koho: pro kohokoli (Decidera, buildera i zástupce), kdo má tři minuty.
> K čemu je tento dokument: jedna obrazovka.
> Říká, co metoda je, a posílá na dokument, který potřebuješ.

## Co to je

Malá skupina, ve které je zastoupena **celá cesta** od nápadu do produkce
(byznys, produkt, design, vývoj, bezpečnost & právo, provoz), postaví
s AI co-pilotem **3 funkční varianty** nad reálným repem, rozhodne nad
běžícím kódem a vítěz jde přes automatické brány jako PR do produkce.
Místo sériového předávání mezi odděleními rozhoduje najednou skupina,
která rozhodnutí umí i zrealizovat.

Povrch je jednoduchý: jeden vstup `/pm`, pět kroků
**Kickoff → Build → Sběr feedbacku (Async) → Rozhodnutí → Ship**, tři pravidla:

1. každý krok cesty má jméno,
2. nejvýš 5 lidí naráz (jádro 3–4 celou dobu, ostatní na krátká okna),
3. co umí zkontrolovat automat, nepotřebuje člověka v místnosti.

Složitost je pod povrchem: v toolu (`pflanzer`), v ADR a v referenčních
dokumentech níže. Effort ~6–8 PD, kalendářně ~8 dní.

## Kam dál

| Chci… | Čti |
|-------|-----|
| metodu **použít** (default profil, stupně, průběh) | [`00-lean-pflanzer.md`](00-lean-pflanzer.md) |
| **vyzkoušet první pilot** (jedna stránka: lidé, instalace, cesta krok za krokem) | [`../zacni.md`](../zacni.md) |
| výjimky a „co když nemáme…“ | [`../faq.md`](../faq.md) |
| průběh v **obrázku** (diagramy, kde varianty fyzicky jsou) | [`../postup.md`](../postup.md) |
| vědět, **kdy ji nepoužít** a proč funguje | [`01-filozofie-a-kdy-pouzit.md`](01-filozofie-a-kdy-pouzit.md) |
| vybrat **zástupce** kroků cesty | [`02-role-catalog.md`](02-role-catalog.md) |
| detail jednotlivých kroků | [`03`](03-pre-session-priprava.md) příprava · [`04`](04-session-1.md) Build · [`05`](05-mezi-sessions.md) Async · [`06`](06-session-2.md) Rozhodnutí · [`07`](07-handoff-do-vyvoje.md) Ship, handoff, retro |
| řešit **sporné situace** | [`08-edge-cases-a-rizika.md`](08-edge-cases-a-rizika.md) |
| srovnání s jinými metodami | [`09-srovnani-existujici-metody.md`](09-srovnani-existujici-metody.md) |
| regulované prostředí (AI Act High-risk, DORA, public sector) | [`../governance/README.md`](../governance/README.md) |
| pojmy | [`glossary.md`](glossary.md) |

## Kanon

Kde se dokumenty liší, platí v tomto pořadí: ADR-0021 (model účasti
a průběh) a ADR-0017 (stupně Quick / Lean / Full), pak `00-lean-pflanzer.md`,
pak ostatní. Terminologie: Kickoff, Build, Sběr feedbacku (Async), Rozhodnutí, Ship.
Starší označení „Session 1 / 2" znamenají Build / Rozhodnutí; „Session 3"
se nepoužívá — Ship je pipeline, ne setkání.
