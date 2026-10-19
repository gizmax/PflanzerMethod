Pflanzer Method | pflanzer.cz/method

# Role card #5 — Backend / API lead

> Držíš data a API — bez tebe varianty stojí na mockovaném backendu, který v produkci neexistuje.

Status v catalogu: **doporučená** · Kdy se zve: Mění se data nebo API?

## Přines do Session 1
- Backend Context Pack: OpenAPI stávajícího API, ERD, NFR baseline
- Event taxonomy a RFC 7807 konvence chyb
- ADR archiv za posledních 12 měsíců
- Seznam consumer ownerů pro breaking-change check

## Podepisuješ
- OpenAPI 3.1 final + procházející contract test (Pact / Schemathesis)
- Migration plan a 3–5 ADR commitů

## Kdy jsi v místnosti
- Quick (60–90 min) — **celá session**: pokud projekt má backend (dev pár u klávesnice)
- Lean (3 h) — **celá session**: builder backendové části
- Full (5–6 h) — **celá session**: vedeš BE feasibility (breaking-change check)

## Hlasuješ o
Skóruješ všechny 4 dimenze; u effort a risk rozhoduje tvůj feasibility check.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **effort**, **risk**. K tomu commitment level 0–3 pro mezi-session práci.

## Okamžitě hlas
- Breaking change v API bez informovaného consumer ownera
- Změna datového modelu bez migration planu
- Reálná osobní data v promptu nebo v sandboxu

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ Jen pro velmi greenfield části; brownfield vyžaduje lidského BE leada. Sub-agent: `.claude/agents/be-api-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 5 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
