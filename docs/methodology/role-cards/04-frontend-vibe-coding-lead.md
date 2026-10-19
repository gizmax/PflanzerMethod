Pflanzer Method | pflanzer.cz/method

# Role card #4 — Frontend / Vibe-coding lead

> Za 15 minut před Buildem potvrdíš, že v repu jde pustit build a testy; pak sedíš u klávesnice a stavíš varianty, které půjdou rovnou do produkce.

**Krok cesty:** Vývoj · **Kde jsi:** jádro — celý Build a Ship

Status v catalogu: **doporučená** · Kdy se zve: Mění se UI nebo přidává se nový view?

## Přines do svého okna
- Přístup do repa produktu a funkční lokální build i testy
- Design tokeny a existující komponenty, které mají varianty použít
- Diff walkthrough své varianty: co je znovupoužité, nové a mock
- Pro hlubší kontrolu (stupeň Full): tech stack contract (ESLint / Prettier, a11y baseline), component manifest (Storybook), anti-pattern list

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
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Ne, nikdy** (ADR-0023). U klávesnice sedí vývojář; AI je jeho asistent, ne zástupce. Sub-agent: `.claude/agents/fe-vibe-coding-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 4 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
