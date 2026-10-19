Pflanzer Method | pflanzer.cz/method

# Role card #4 — Frontend / Vibe-coding lead

> Jsi builder: u klávesnice stavíš varianty s Claude Code přímo v target repu, takže vítěz jde do produkce bez re-implementace.

**Krok cesty:** Vývoj · **Kde jsi:** jádro — celý Build a Ship

Status v catalogu: **doporučená** · Kdy se zve: Mění se UI nebo přidává se nový view?

## Přines do svého okna
- Design tokens a component manifest (Storybook URL)
- Tech stack contract: framework, ESLint / Prettier, a11y baseline
- Přístup do target repa a funkční lokální build
- Anti-pattern list komponent

## Podepisuješ
- PR-ready commit vítězné varianty (token compliance > 90 %)
- Diff walkthrough a komponentový mapping své varianty

## Kdy jsi u toho
- Quick (60–90 min) — **celý běh**: builder, 1 kolo × 30 min
- Lean (3 h) — **celý běh**: builder, 2 kola × 30 min + diff walkthrough; po Go pouštíš Ship
- Full (5–6 h) — **celý běh**: od minuty 0 do Shipu

## Hlasuješ o
Hlasuješ silent jako ostatní; před hlasováním máš 5 min diff walkthrough (`git diff --stat`, co je mock / stub).

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **effort**, **risk**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Varianta obchází design system nebo existující komponenty
- Mock / stub vypadá jako hotová funkce — řekni to v diff walkthrough
- V target repu nejde build nebo testy — winner by nešel do produkce

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ Pro greenfield části jde, brownfield vyžaduje tvůj review. Sub-agent: `.claude/agents/fe-vibe-coding-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 4 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
