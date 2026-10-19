Pflanzer Method | pflanzer.cz/method

# Role card #6 — UX / Designer

> Za Build a Async potvrdíš, že varianty sedí na uživatele a úkol, který řeší, ne jen hezky vypadají. Držíš flow a design system.

**Krok cesty:** Design · **Kde jsi:** jádro — Build a Async (u interního toolu může krýt PdM)

Status v catalogu: **doporučená** · Kdy se zve: Vzniká nový user flow nebo přepracování core experience?

## Přines do svého okna
- Popis uživatele, jeho úkolu a potřeb přístupnosti
- Dnešní průchod uživatele (kde to bolí)
- Design tokeny a existující komponenty
- Pro hlubší kontrolu (stupeň Full): journey map, component inventory, brand voice & tone, seznam odchylek od design systému s ownerem

## Podepisuješ
- JTBD a persona lock (spolu s PdM)
- DS deviation list s ownerem a Figma ↔ kód mapping

## Kdy jsi u toho
- Quick (60–90 min) — **celý běh**: default sestava jádra
- Lean (3 h) — **celý běh**: hlídáš flow integrity v obou kolech Buildu a v Async komentářích
- Full (5–6 h) — **celý běh**: s PdM vedeš JTBD warm-up

## Hlasuješ o
Skóruješ všechny 4 dimenze; tvoje rationale váží hlavně u user value a flow integrity.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **user_value**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Varianta řeší jiný flow nebo personu, než je zamčená
- Odchylka od design systému bez ownera
- Persona drift — tým navrhuje pro sebe, ne pro uživatele

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Ano** (ADR-0023): UX expert + kontroly přístupnosti, nahrazení podepisuje PdM; u zákaznického produktu v produkci potvrdí design člověk. Sub-agent: `.claude/agents/ux-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 6 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
