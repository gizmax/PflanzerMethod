Pflanzer Method | pflanzer.cz/method

# Role card #5 — Backend / API lead

> Za 15 minut před Buildem potvrdíš, co varianty smí měnit na API a datech, aby nestály na mocku, který v produkci neexistuje.

**Krok cesty:** Vývoj (backend) · **Kde jsi:** jádro — Build (backendová část) a Ship

Status v catalogu: **doporučená** · Kdy se zve: Mění se data nebo API?

## Přines do svého okna
- Popis stávajícího API a datového modelu (OpenAPI, schéma)
- Seznam týmů, kterým by změna API rozbila klienta
- Plán migrace dat, pokud varianta mění model
- Pro hlubší kontrolu (stupeň Full): ERD, NFR baseline, event taxonomy, RFC 7807 konvence chyb, ADR archiv za 12 měsíců

## Podepisuješ
- OpenAPI 3.1 final + procházející contract test (Pact / Schemathesis)
- Migration plan a 3–5 ADR commitů

## Kdy jsi u toho
- Quick (60–90 min) — **celý běh**: pokud projekt má backend (dev pár u klávesnice)
- Lean (3 h) — **celý běh**: builder backendové části; po Go připravuješ Ship
- Full (5–6 h) — **celý běh**: vedeš BE feasibility (breaking-change check)

## Hlasuješ o
Skóruješ všechny 4 dimenze; u effort a risk rozhoduje tvůj feasibility check.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **effort**, **risk**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Breaking change v API bez informovaného consumer ownera
- Změna datového modelu bez migration planu
- Reálná osobní data v promptu nebo v sandboxu

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Ne, nikdy** (ADR-0023). Vývoj podepisuje člověk; AI jen pomáhá s částmi bez napojení na stávající systém. Sub-agent: `.claude/agents/be-api-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 5 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
