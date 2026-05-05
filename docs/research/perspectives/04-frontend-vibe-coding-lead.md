# Perspektiva: Frontend / Vibe-coding lead

## Kdo jsem
Staff FE engineer s 12+ lety v Reactu, žiju mezi `tsconfig.strict`, design tokeny a tickety typu „v0 nám vygeneroval krásné tlačítko, ale ignoruje náš Button". Vibe-coding mě nadchnul jako discovery nástroj a děsí jako delivery nástroj — vidím, jak rapid prototyping zkracuje pinkací smyčky, a zároveň jak generated code propašuje druhý design system zadními vrátky. Moje denní starost: aby z workshopového prototypu nevznikl shadow frontend, který někdo za půl roku „jen dotáhne do produkce".

## 1. Posouzení metody z mé role

**Co mi pomáhá**
- Konečně mě někdo posadí do místnosti **před** tím, než zadání ztuhne. Discovery sessions bez FE jsou důvod, proč pak v produkci řešíme nemožné interakce a a11y dluh.
- „Programátoři jsou u tvorby klikacího prototypu" — to je klíč k tomu, aby handoff nebyl `throw-over-the-wall`. Můžu hned říct „toto v naší knihovně je, toto ne".
- Score závaznosti per oddělení dává FE leadovi nástroj, jak označit „toto je hezké, ale s naším design systémem nekompatibilní" jako blocker, ne jen názor.

**Co mi chybí**
- Nikde není definováno, **jaký je vztah prototypu k produkčnímu kódu**. Throw-away? Evolve? Reference? Bez tohoto rozhodnutí v charteru vznikne pseudo-MVP, který nejde ani vyhodit, ani shipnout.
- Chybí **design system / token contract** jako povinný vstup. Bez něj AI vyrobí třetí variantu Buttonu, čtvrtou variantu spacingu a vlastní paletu.
- Chybí **a11y baseline** jako acceptance kritérium prototypu. Vibe-coding tools (Bolt, Lovable, v0) mají demonstrovaně slabý kontrast, chybějící focus states a `<div onClick>` všude.

**Co mě ohrožuje**
- **Sponzor uvidí klikací mockup a řekne „to je hotové, jen to nasaďte".** Tohle je nejčastější scénář v korporátu a metoda proti němu nemá vakcínu.
- **AI model „vede výklad" v session 2** — pokud nemá kontext našeho design systému, dá doporučení optimalizovat věc, která se stejně bude předělávat.
- Můj tým bude trávit Q3 refaktorováním vibe-prototypu do `@company/ui` místo aby psal nové fíčury.

## 2. Must-have vstupy do Session 1

1. **Design tokens export** (JSON / Style Dictionary) — barvy, spacing, typografie, radii, shadows. Nakrmit do system promptu builderu.
2. **Komponentová knihovna manifest** — seznam existujících komponent (`Button`, `DataTable`, `Modal`, ...) s props signaturama. Ideálně Storybook URL + MCP server (Builder.io Fusion vzor).
3. **Tech stack contract** — framework (Next.js App Router 15? Vite + React 19?), state mgmt, data fetching pattern, form library, i18n. Konkrétně, ne „React".
4. **Code conventions** — ESLint + Prettier config, file structure, naming, commit konvence. AI agent musí tyto pravidla dostat předem.
5. **A11y baseline** — WCAG 2.2 AA jako minimum, kontrast tokeny, keyboard-nav checklist, screen reader smoke test. Pro public-facing EAA-required.
6. **Browser/device support matrix** — co testujeme, co ignorujeme. Brání AI vyrobit Safari-broken `:has()` chain.
7. **Reálná demo data se správnou shape** — ne `{ name: "John" }`, ale produkčně podobný JSON včetně edge cases (prázdný stav, dlouhé stringy, RTL, error states).
8. **Anti-pattern list** — „nepoužívat: tabs jako navigation, modals nad modals, infinite scroll bez fallback, custom dropdowns". Konkrétní gardrails pro generátor.

## 3. Must-have výstupy ze Session 1 a 2

- **Komponentový mapping**: každá obrazovka prototypu označená — co je reused z `@company/ui`, co je nový kandidát na komponentu, co je throw-away one-off.
- **Tech feasibility scorecard** per varianta: API needs, state complexity, perf rizika (virtualizace? streaming?), a11y blockers.
- **Token compliance report**: kolik % stylů je z design tokenů vs. hardcoded. Cíl pro „evolve" prototyp = >90 %.
- **Decision log: throw-away vs evolve vs reference-only.** Podepsaný FE leadem a EM. Bez tohoto se nehýbat.
- **Data contract draft** — jaké API endpointy / GraphQL queries prototyp předpokládá. Předáno backendu jako vstup, ne jako fait accompli.
- **A11y audit report** finálního prototypu (axe-core run + manuální keyboard test). Blockers = veto pro „final".
- **Repo + commit history** — ne ZIP. Git je paměť, code review začne den 1 po session 2.

## 4. Edge cases a rizika

1. **„Production by stealth"** — sponzor protlačí prototyp do prod přes management override. Mitigace: prototyp běží **jen na sandbox doméně**, robots noindex, watermark „PROTOTYPE — NOT PRODUCTION", session-locked auth.
2. **Design system drift** — AI generátor vyprodukuje vlastní `Button2`, `CardV3`, `useToast2`. Tři měsíce od session má app dva design systémy. Mitigace: token compliance check jako CI gate před merge.
3. **Hallucinated UI patterns** — Bolt/Lovable umí vymyslet komponenty, které ergonomicky neexistují (drag-drop tabs s nested modal). Nejde o vkus, jde o nemožnost otestovat. Mitigace: pattern allowlist v briefu.
4. **A11y regrese maskovaná „krásným" UI** — generated code má často `div role="button"`, chybí focus trap v modal, kontrast 3.5:1. Stakeholder řekne „vypadá hezky", ale je to lawsuit risk pro EAA. Mitigace: axe-core run na konci každé session, blocker = cannot ship.
5. **Lock-in na proprietární komponenty buildery** — v0 generuje shadcn, Lovable Supabase-coupled, Tempo React-only. Pokud máme Vue/Angular/legacy, prototyp je nepoužitelný jako reference. Mitigace: **vybrat builder podle našeho stacku, ne naopak.**

## 5. Konkrétní vylepšení metody

1. **Builder selection podle stacku, ne podle hype.** Next.js + shadcn → v0.app. Multi-framework legacy → Bolt.new. UI-only discovery → Google Stitch (5-screen canvas zdarma, side-by-side). Pokud máme custom design system → **Builder.io Fusion** s mapováním na naše komponenty (jediný tool, který to umí).
2. **„Vibe-brief" template** jako standardizovaný vstup pro AI: design tokens + component manifest + stack + conventions + anti-patterns + demo data shape + a11y baseline. Jeden markdown soubor, verzovaný v repo, načtený jako system prompt. Bez něj session 1 nestartovat.
3. **Cursor Composer 2 `/best-of-n` pro variantní generaci** místo paralelně otevřených tabů Boltu. Deterministicky 3 varianty ze stejného briefu, každá ve worktree, git history zachována. FE lead provede compare. Pro stakeholder share-out pak deploy do Vercel/Netlify preview URL.
4. **Throw-away kontrakt v charteru.** Defaultně každý prototyp = throw-away. „Evolve" status vyžaduje explicit rozhodnutí FE lead + EM po code review s token-compliance a a11y reportem. Nic mezi tím.
5. **A11y gate v session 2.** Před AI-led výkladem připomínek pustit axe-core + manuální keyboard test na top 2 varianty. Výsledek = jeden ze score axes závaznosti. Žádný „let's fix it later".

## 6. Konflikty s ostatními rolemi

- **UX / Designer (6)** — přetahování o ownership vizuálu. UX chce Figmu jako single source of truth, já chci tokeny v kódu jako single source. Řešení: Figma definuje, kód je SoT pro implementaci, oba mapujeme na stejné tokeny.
- **Zadavatel (1)** — chce prototyp do prod „protože to už funguje". Já to vetuji s odkazem na throw-away kontrakt. Tady FE lead potřebuje explicitní backing facilitátora a EM.
- **Backend / API lead (5)** — prototyp si vymyslí API shape, která neodpovídá realitě. Konflikt mezi „rychlost prototypu" a „nedělejme si fake API". Řešení: API contract draft jako výstup session 1, ne až 2.
- **Engineering Manager (9)** — pokud throw-away, musí akceptovat, že session = sunk cost discovery, ne delivery proti kapacitě. Pokud evolve, musí mi alokovat čas na refactor do produkce. Bez tohoto rozhodnutí neexistuje workshop.
- **Accessibility expert (11)** — spojenec, ale často přijde pozdě. Chci ho v session 1, ne až jako post-hoc audit.

## Memorabilia
Vibe-coding není nahrazení mého týmu. Je to nejlepší discovery nástroj posledních deseti let — pokud do něj nakrmím design tokeny a a11y baseline a pokud sponzor podepíše, že prototyp není produkt.
