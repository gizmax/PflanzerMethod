Pflanzer Method | pflanzer.cz/method

# Role card #11 — Accessibility expert

> Hlídáš WCAG 2.2 AA — Critical / Serious nález blokuje finální rozhodnutí jako Security veto.

Status v catalogu: **doporučená (default-on)** · Kdy se zve: Customer-facing nebo B2B nad 250 zaměstnanců?

## Přines do Session 1
- WCAG 2.2 AA filtr na komponenty
- Persona disability set (low vision, motor, cognitive)
- Tooling: axe DevTools / Pa11y CI / Lighthouse

## Podepisuješ
- A11y quickscan (8–10 položek) per varianta
- Blocker na „final“ při WCAG Critical / Serious
- Pre-launch human review (screen reader, focus, cognitive load)

## Kdy jsi v místnosti
- Quick (60–90 min) — **async**: AI udělá axe-core scan, tvůj review v mezi-session okně
- Lean (3 h) — **async**: AI proxy draft + tvůj sign-off do 24–48 h
- Full (5–6 h) — **celá session**: před votingem vedeš A11y quickscan

## Hlasuješ o
Skóruješ všechny 4 dimenze; WCAG Critical / Serious řešíš blockerem, ne nízkým skóre.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **user_value**, **risk**. K tomu commitment level 0–3 pro mezi-session práci.

## Okamžitě hlas
- Varianta nejde ovládat klávesnicí nebo ztrácí focus
- Nízký kontrast nebo chybějící labely formulářů
- Opt-out z role bez podepsané justifikace

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ AI zvládne static audit, axe-core a kontrast; pre-launch review je nedelegovatelný. Sub-agent: `.claude/agents/a11y-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 11 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
