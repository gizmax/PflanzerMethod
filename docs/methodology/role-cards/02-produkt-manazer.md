Pflanzer Method | pflanzer.cz/method

# Role card #2 — Produkt manažer

> Za celý Build potvrdíš, že varianty řeší správný problém a míří na metriku z Kickoffu. Překládáš business do požadavků a držíš prioritu.

**Krok cesty:** Produkt · **Kde jsi:** jádro — celý Build, Async a Rozhodnutí

Status v catalogu: **povinná** · Kdy se zve: vždy (core role)

## Přines do svého okna
- Popis uživatele a úkolu, který řeší (JTBD karta, ne starší než 6 měsíců)
- Metriku úspěchu s dnešním výchozím číslem
- Zadání z Kickoffu rozepsané do kritérií, podle kterých se varianty posoudí
- Pro hlubší kontrolu (stupeň Full): OST v0 vyplněný aspoň na 60 %, podpis JTBD v Discovery Readiness Gate

## Podepisuješ
- JTBD podpis v Discovery Readiness Gate — bez něj se Build odkládá
- JTBD a persona lock na začátku Buildu (spolu s UX)
- PRD-lite a aktualizovaný OST po Rozhodnutí

## Kdy jsi u toho
- Quick (60–90 min) — **celý běh**: celý Quick běh; držíš JTBD a parking lot
- Lean (3 h) — **celý běh**: Kickoff, celý Build, Async i Rozhodnutí; držíš JTBD
- Full (5–6 h) — **celý běh**: s UX vedeš JTBD warm-up a sladění zadání

## Hlasuješ o
Skóruješ všechny 4 dimenze s povinným rationale. S facilitátorem máš právo poslat nový požadavek do parking lotu.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **user_value**, **strategic_fit**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Persona po expiraci nebo JTBD bez podpisu → Discovery Sprint, ne Build
- Varianta řeší jiný JTBD než ten zamčený
- Metrika úspěchu nejde změřit (chybí baseline)

## AI proxy
**Režim 1 — Vlastnické a vetovací (vždy člověk).** Může tě nahradit AI? **Jen ve stupni Quick / u throwaway** (ADR-0023); zadání pak podepisuje Decider. Jinak člověk, finální slovo máš ty. Sub-agent: `.claude/agents/pm-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 2 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
