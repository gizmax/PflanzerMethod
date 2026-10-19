Pflanzer Method | pflanzer.cz/method

# Role card #14 — End-user proxy / User research

> Za 20 minut v Asyncu potvrdíš, že varianty vycházejí z toho, co uživatelé skutečně dělají, ne z názorů v místnosti.

**Krok cesty:** Produkt (evidence od uživatelů) · **Kde jsi:** okno — Async okno a Rozhodnutí (evidence)

Status v catalogu: **doporučená (default-on)** · Kdy se zve: Customer-facing flow nebo nový segment?

## Přines do svého okna
- Popis uživatele z aspoň 5 rozhovorů (ne starší než 6 měsíců)
- Co o problému víme z pozorování, ticketů nebo hovorů
- Pro hlubší kontrolu (stupeň Full): JTBD karta, OST v0, Discovery Debt skóre 0–10, expirace persony (B2C 6 / B2B 9 / interní 12 měsíců)

## Podepisuješ
- Discovery Debt Detector skóre 0–10
- JTBD / OST node tag per varianta
- Persona expiry compliance (B2C 6 / B2B 9 / interní 12 měsíců)

## Kdy jsi u toho
- Quick (60–90 min) — **async**: AI archetype check, tvůj review v Async okně
- Lean (3 h) — **async**: AI proxy draft + tvůj sign-off v Async okně (24–48 h)
- Full (5–6 h) — **celý běh**: hlídáš evidence u každé varianty

## Hlasuješ o
Skóruješ všechny 4 dimenze. AI-only persona hlas má deflaci max 0.5 / 1.0 — tvůj lidský hlas platí plně.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **user_value**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Persona po expiraci nebo bez rozhovorů
- „Uživatelé chtějí…“ bez evidence
- Varianta bez JTBD / OST node

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Není to krok cesty** (ADR-0023); AI feedback má váhu max 0,5 a nové poznatky nevymyslí. Sub-agent: `.claude/agents/user-research-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 14 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
