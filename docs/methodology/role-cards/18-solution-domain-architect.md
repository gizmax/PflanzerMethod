Pflanzer Method | pflanzer.cz/method

# Role card #18 — Solution / Domain architect

> Hlídáš hranice domén a dopady napříč týmy, když scope přesahuje jeden tým.

Status v catalogu: **volitelná (trigger)** · Kdy se zve: Multi-team scope (≥ 3 týmy) nebo komplexní doména (vyžaduje Event Storming) nebo regulovaný SDLC?

## Přines do Session 1
- Bounded contexts a domain model
- Integration map napříč týmy
- ADR archiv

## Podepisuješ
- Breaking-change registr
- Domain delta a dependency map per bounded context
- ADR drafty

## Kdy jsi v místnosti
- Quick (60–90 min) — **nepřítomna**: multi-team scope se v Quick nedělá
- Lean (3 h) — **async**: review breaking changes v mezi-session okně
- Full (5–6 h) — **celá session**: při > 3 týmech federovaný model

## Hlasuješ o
Skóruješ všechny 4 dimenze; risk za tebe = dopad na ostatní bounded contexts.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **risk**, **strategic_fit**. K tomu commitment level 0–3 pro mezi-session práci.

## Okamžitě hlas
- Varianta sahá do bounded contextu jiného týmu bez jeho vědomí
- Víc než 3 týmy ve scope bez federovaného modelu
- Breaking change bez záznamu v registru

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ Jen typické vzory; doménový úsudek je tvůj. Sub-agent: `.claude/agents/solution-architect-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 18 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
