Pflanzer Method | pflanzer.cz/method

# Role card #1 — Zadavatel / Business owner

> Za 15 minut na Kickoffu potvrdíš zadání a že smíš říct Go i Kill; za 60–90 minut na Rozhodnutí rozhodneš nad běžícími variantami. Vlastníš nápad i budget a jsi Decider.

**Krok cesty:** Byznys · **Kde jsi:** okno — Decider: Kickoff 15 min + Rozhodnutí 60–90 min

Status v catalogu: **povinná** · Kdy se zve: vždy (core role)

## Přines do svého okna
- Zadání na 1 stránku: problém v jedné větě, jedno číslo úspěchu, kdy to zabalíme
- Písemný mandát, že smíš říct Go / Iterate / Kill
- Jméno zástupce za každý z 6 kroků cesty a zabookovaná okna
- Kdo v týmu má kapacitu komentovat a zapracovávat v Asyncu

## Podepisuješ
- Zadání z Kickoffu (`/pm start`)
- Go / Iterate / Kill v Rozhodnutí (`/pm decide`) — hlasuješ poslední
- Při Shipu pod prahem skóre: výjimku z prahu na vlastní odpovědnost (`--override-threshold`)

## Kdy jsi u toho
- Quick (60–90 min) — **celý běh**: Kickoff i Rozhodnutí; bez tebe se nic nekoná
- Lean (3 h) — **celý běh**: Kickoff 15 min a Rozhodnutí 60–90 min; Build běží bez tebe
- Full (5–6 h) — **celý běh**: Kickoff, Rozhodnutí i závěrečné commitmenty

## Hlasuješ o
Hlasuješ **poslední** (anti-HiPPO) a svou preferenci neříkáš před silent vote. Override výsledku jen veřejně s rationale do decision logu.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **strategic_fit**, **user_value**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Chybí písemný mandát nebo budget — řekni to před Kickoffem, ne po něm
- Kdokoli (i ty) prozradí preferovanou variantu před silent vote
- Scope creep „když už tu jsme…“ — patří do parking lotu

## AI proxy
**Režim 1 — Vlastnické a vetovací (vždy člověk).** Může tě nahradit AI? **Ne, nikdy** (ADR-0023). Bez Decidera se Kickoff ani Rozhodnutí nekoná. Sub-agent: `.claude/agents/zadavatel-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 1 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
