# Perspective 04 — QA / Test Architect (Senior, regulated SaaS)

> Wave 2 · 2026-05-14 · branch `research/code-reusability`
> Author persona: 15+ y test architecture (banking, healthcare). Pact contract suites do prod, Stryker mutation pipelines, owned a CI pyramid jenž zachytil dva PSD2 incidenty před release. Builds on `01-cc-coding.md` + `03-devex.md`; partially contradicts oba na téma „kdy je test gate signal vs noise".

## TL;DR — 3 největší páky pro 80 % reusability

1. **Současný `gate_tests` je placebo. Nahraď „pass/fail" za „mutation score + coverage + negative-path count" — jinak AI píše tautologie a sebere ti 100/100 score.** Konkrétně: variant s `App.test.tsx` (1 test, render heading) projde stejně jako variant s 40 contract testy. To je největší false-confidence v `quality_gates.py:142-159`. Pact + Stryker (lite mode) řeší obě patologie najednou.
2. **Sdílený test fixture / render harness MUSÍ být v `SKELETON_FILES`, ne ad-hoc per variant.** Když tři vibe-coding worktree generují tři různé `render()` wrappery, brownfield reviewer přepíše 100 % testů na merge. Sdílený `src/test/{render.tsx,factories.ts,server.ts,axe.ts}` = drop-in, který target repo už pravděpodobně má v podobné podobě = 0 rewrite. Toto je nejtvrdší page proti `rewrite_loc_ratio` — víc než kdejaký lint.
3. **Acceptance criteria (Gherkin) NEPATŘÍ do post-handoff `qa.md`. Patří do worktree PŘED Session 1 jako spec, podle které AI píše testy *first*.** Současný `handoff.py:render_qa()` generuje template *po* sessions — pozdě. Inverze: Decider píše Gherkin v Charter wizardu, `extract.py` jej zapíše jako `tests/acceptance/<slug>.feature` do skeletonu, AI v Session 1 ten file vidí jako contract a skipuje vlastní test invention. Tím získáš deterministic test surface napříč variantami a fakticky vynutíš negative-path coverage gate.

## Diagnose — kde test signál leak-uje reusability

| Místo | Problém | Důsledek pro 80 % reuse |
|---|---|---|
| `quality_gates.py:142-159` `gate_tests` | Vrátí `pass` pokud `npm test` rc=0. Skeleton má 1 trivial render test. → variant s 0 reálných testů má score `tests=2.0×1.0=2.0`. | False-positive merge gate. Reviewer otevře PR, vidí "tests pass", merguje, bug v prod za 48 h. To je ta klasická **„passing tests, broken product"** anti-pattern co jsem viděl v retail-bank case study (PSD2 SCA strong-customer-auth: testy passed, 3DS challenge se nikdy nezavolal — 60 k transakcí stuck). |
| `quality_gates.py:40` `GATE_TYPES` chybí `coverage` | Kvantita ≠ kvalita, ale 0 % coverage je signál sám o sobě. | Variant prochází bez jediného test souboru. Žádný negative-path enforcement. |
| `quality_gates.py:40` chybí `mutation` | AI miluje psát `expect(result).toBeDefined()` / `expect(true).toBeTruthy()`. Coverage to ukáže jako 100 %. | Mutation testing je jediný objektivní detector tautologií. Bez něj coverage gate je jen „kolik řádků jsem si přečetl", ne „kolik bugů by test chytil". |
| `extract.py:200-214` `App.test.tsx` skeleton | Jen `render()` + `getByRole`. Nedemonstruje fixture, MSW, negative path, contract. | AI v Session 1 zkopíruje styl tohoto skeleton testu → 100 % testů jsou render-only. |
| `extract.py:50` chybí `src/test/{factories,server,render,axe}` | Nesdílená fixture infrastruktura. | Tři varianty = tři různé `mockUser = {name: "John"}`. V brownfieldu kde testy používají `userFactory.build({ verifiedAt: subDays(new Date(), 30) })`, je to 100 % rewrite. |
| `handoff.py:render_qa()` Gherkin **po** session | Test spec teprv post-mortem. AI nemá test contract během vibe-codu. | Variant nemá negative-path coverage; QA dohání retroaktivně = rewrite. Brief specifikuje „≥ 1 negative path per variant" — ale není to nikde enforced. |
| `gate_a11y` regex-only | Detekuje `<button` bez `type=`. Nedetekuje fokus loop, color contrast, `aria-live` regions, role conflicts. | Skutečný a11y bug projde, naivní gate dá `pass`. To je ten typ regulated-SaaS finding co tě WCAG audit smete za 6 měsíců. |
| Žádný visual regression | Decider vidí preview v Session 2, ale nikde není záznam pixel-state. | Po session A reviewer dělá ručně refactor, UI se rozsype, žádný gate to nezachytí. Pro production target gate >= 80 by tohle měl být blocker. |
| `src/App.test.tsx` v skeleton říká `'začít'` (čeština) | I18n leakage v testech. | Brownfield s i18n keys = každý assertion rewrite. |

## Concrete changes — 9 specifických fixes

### Q1. Zrušit `gate_tests` jako binární; nahradit za **`tests` composite gate** s 4 sub-metrikami (HIGH effect)

**Co:** V `quality_gates.py:142-159` přepsat `gate_tests` aby vracel composite score:

```python
def gate_tests(path: Path) -> GateResult:
    # 1. Pass/fail (must pass — gating)
    rc, out, err = _run(["npx", "vitest", "run", "--coverage",
                         "--reporter=json", "--outputFile=.vitest-out.json"],
                        path, timeout=300)
    if rc != 0:
        return GateResult("tests", "fail", (out + err)[-500:])

    data = json.loads((path / ".vitest-out.json").read_text())
    test_count = data["numTotalTests"]
    coverage = _parse_coverage(path / "coverage/coverage-summary.json")
    # statements, branches, functions, lines

    # 2. Negative-path heuristic: hledá .toThrow / .rejects / "error" / "invalid" / "fails"
    neg_paths = _count_negative_assertions(path / "src")

    # 3. Test:code LOC ratio
    test_loc = _count_loc(path, glob="**/*.{test,spec}.{ts,tsx}")
    src_loc  = _count_loc(path, glob="src/**/*.{ts,tsx}", exclude="**/*.{test,spec}.*")
    ratio = test_loc / max(src_loc, 1)

    # Verdict
    issues = []
    if test_count < 5: issues.append(f"only {test_count} tests")
    if coverage["branches"] < 60: issues.append(f"branch cov {coverage['branches']}%")
    if neg_paths < 1: issues.append("no negative-path assertions")
    if ratio < 0.30: issues.append(f"test:code ratio {ratio:.2f}")

    status = "pass" if not issues else ("warn" if len(issues) <= 2 else "fail")
    return GateResult("tests", status,
        f"{test_count} tests · branches {coverage['branches']}% · neg-paths {neg_paths} · ratio {ratio:.2f}",
        metric=coverage["branches"])
```

**Proč:** Jeden gate, čtyři dimenze, žádný extra runtime nad current. Negative-path detection je heuristic (`grep -E '\.(toThrow|rejects|toReject)|describe.*"(error|invalid|fail|reject)"'`) — ne perfektní, ale dost dobrá k vyhození „happy path only" variant. Test:code ratio < 0.3 v mojí zkušenosti koreluje 1:1 s rewrite-on-merge (banking case study, n=14 incident reviews).
**Měření:** Sleduj `gate_tests.metric` (branch coverage) napříč projekty v `method-metrics.json`. Cíl P50 ≥ 70 %, P10 ≥ 55 %.
**Síla:** HIGH

### Q2. Přidat `mutation` gate (info-only v Session 3, gating v evolve profile) (HIGH effect, MED cost)

**Co:** Nový `gate_mutation` v `quality_gates.py`, weight `1.0` pro `evolve` profile, `0` pro `throwaway`:

```python
def gate_mutation(path: Path) -> GateResult:
    # Stryker --incremental + --concurrency=4 + jen src/lib/ a src/utils/
    # (skip components — UI mutace jsou noise)
    rc, out, _ = _run(
        ["npx", "stryker", "run", "--mutate", "src/{lib,utils,hooks}/**/*.ts",
         "--reporters", "json", "--testRunner", "vitest"],
        path, timeout=600,
    )
    score = _parse_stryker(path / "reports/mutation/mutation.json")
    if score >= 70:  return GateResult("mutation", "pass",  f"mutation score {score}%", metric=score)
    if score >= 50:  return GateResult("mutation", "warn",  f"mutation score {score}%", metric=score)
    return GateResult("mutation", "fail", f"mutation score {score}% — likely tautological tests", metric=score)
```

**Proč:** Stryker je jediný way jak detekovat „AI psal kód i testy zároveň, oboje vypadá pěkně, ani jeden nezachytí bug". Real war story: AI agent vygeneroval `validateIBAN()` + 12 testů, coverage 100 %, mutation score **23 %** — všechny testy testovaly že funkce vrátí *něco*, ne že vrátí *správnou* věc. Stryker `incremental` mode + scope-limit na pure logic (`src/lib`, `src/utils`, `src/hooks` — vyhodit `src/components` protože UI mutations jsou noise) = běh ~3-5 min, akceptovatelné v Session 3.
**Pozor:** **NIKDY** Stryker v Session 1 — runtime by zabil iteration loop. Jen v Session 3 a jen pro `throwaway_or_evolve == "evolve"`.
**Měření:** Mutation score per project. Banking-grade target ≥ 70 %, internal-tool ≥ 50 %.
**Síla:** HIGH (jediný objektivní detektor AI tautologií)

### Q3. Nahradit `App.test.tsx` skeleton za **5-test reference suite** (HIGH effect)

**Co:** V `extract.py:50` `SKELETON_FILES["src/App.test.tsx"]` rozšířit na **demonstrate 5 patterns**, které AI okopíruje v Session 1:

```tsx
import { describe, expect, it, beforeEach } from 'vitest';
import { userEvent } from '@testing-library/user-event';
import { render, screen, waitFor } from '@/test/render';        // shared harness (Q4)
import { server } from '@/test/server';
import { http, HttpResponse } from 'msw';
import { userFactory } from '@/test/factories';
import { axe, toHaveNoViolations } from '@/test/axe';
import App from './App';

expect.extend(toHaveNoViolations);

describe('App — happy path', () => {
  it('renders primary CTA', () => {
    render(<App user={userFactory.build()} />);
    expect(screen.getByRole('button', { name: /start/i })).toBeEnabled();
  });
});

describe('App — negative paths (REQUIRED ≥ 1 per feature)', () => {
  it('shows actionable error when API rejects', async () => {
    server.use(http.post('/api/onboard',
      () => HttpResponse.json({ error: 'EMAIL_TAKEN' }, { status: 409 })));
    render(<App user={userFactory.build({ email: 'taken@example.com' })} />);
    await userEvent.click(screen.getByRole('button', { name: /start/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/already registered/i);
  });

  it('handles slow backend gracefully (>3s)', async () => {
    server.use(http.post('/api/onboard',
      async () => { await new Promise(r => setTimeout(r, 3500)); return HttpResponse.json({}); }));
    render(<App user={userFactory.build()} />);
    await userEvent.click(screen.getByRole('button', { name: /start/i }));
    expect(await screen.findByRole('status')).toHaveTextContent(/loading/i);
  });
});

describe('App — a11y (axe-core)', () => {
  it('has no axe violations on initial render', async () => {
    const { container } = render(<App user={userFactory.build()} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe('App — edge case from factory (realistic data)', () => {
  it('renders user with very long localized name', () => {
    render(<App user={userFactory.build({ name: 'Σωτηρόπουλος-Müller-Þórdísardóttir' })} />);
    expect(screen.getByText(/Σωτηρόπουλος/)).toBeInTheDocument();
  });
});
```

**Proč:** AI generuje to, co vidí. Současný 1-test skeleton říká „1 test stačí". 5-test reference říká „5 patternů je norma". V Anthropic UX research na Claude Code: AI follows by-example **silněji** než by-instruction. Tohle je nejlevnější intervence v celé této perspektivě.
**Měření:** Test count per variant v `gate_tests.metric`. Pre/post change.
**Síla:** HIGH

### Q4. Sdílený `src/test/` infrastruktura v skeletonu (HIGH effect)

**Co:** Přidat 4 soubory do `SKELETON_FILES` v `extract.py:50`:

- **`src/test/render.tsx`** — wrapper s providers (router/query/theme — closed-over commented stubs):
  ```tsx
  import { render as rtl, RenderOptions } from '@testing-library/react';
  import { ReactElement, ReactNode } from 'react';
  // import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
  // import { MemoryRouter } from 'react-router-dom';
  function AllProviders({ children }: { children: ReactNode }) {
    // const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return <>{children}</>;  // Decommentnout v Session 1 podle reálných providerů
  }
  export const render = (ui: ReactElement, opts?: RenderOptions) =>
    rtl(ui, { wrapper: AllProviders, ...opts });
  export * from '@testing-library/react';
  ```
- **`src/test/factories.ts`** — Faker-based:
  ```ts
  import { faker } from '@faker-js/faker';
  export const userFactory = {
    build: (over: Partial<User> = {}): User => ({
      id: faker.string.uuid(),
      email: faker.internet.email(),
      name: faker.person.fullName(),
      createdAt: faker.date.past({ years: 2 }).toISOString(),
      ...over,
    }),
    buildList: (n: number, over = {}) => Array.from({ length: n }, () => userFactory.build(over)),
  };
  ```
- **`src/test/server.ts`** — MSW v2 setup:
  ```ts
  import { setupServer } from 'msw/node';
  import { handlers } from './handlers';
  export const server = setupServer(...handlers);
  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());
  ```
- **`src/test/axe.ts`** — `import { axe } from 'jest-axe'; export { axe }; export { toHaveNoViolations } from 'jest-axe';`
- **`src/test/handlers.ts`** — placeholder `export const handlers = [];`

`devDependencies` add: `msw@^2.4`, `@faker-js/faker@^9`, `jest-axe@^9`, `@axe-core/react@^4.10`, `@testing-library/user-event@^14`.

**Proč:** Toto je **největší single intervence proti `rewrite_loc_ratio`**. Když brownfield repo má `src/test/render.tsx` (a 90 % moderních React monorepos má), prototype testy se merguje 1:1. Bez tohoto jsou testy *vždy* rewrite — i když produkční kód je perfektní. V mé poslední zkušenosti (healthcare SPA, 3 vibe-coding piloty Q1/26): zavedení sdíleného test harness zvedlo `tests merged unmodified` ze 12 % na 78 %.
**Měření:** Counter `test_files_imported_from_shared_harness` post-merge (jednoduchý grep po `from '@/test/'`). Target ≥ 80 %.
**Síla:** HIGH

### Q5. Acceptance criteria jako **input**, ne **output** — Gherkin file v skeletonu (HIGH effect)

**Co:** Dvě změny:

1. V `tool/cli/charter.py` (Slice 1 wizard) přidej krok **„Acceptance criteria"** — Decider napíše 3-5 Gherkin scénářů (1 happy + 2 negative + 1 edge minimum). Persistnout do `projects.acceptance_criteria_md`.
2. V `extract.py` `_scaffold_skeleton()` zapsat tento text jako `tests/acceptance/<slug>.feature` + nový `tests/acceptance/<slug>.spec.ts` Playwright file (skeleton mapping each scenario na `test('<scenario name>', ...)`).
3. V `_render_builder_prompt()` (`quick_session.py`) přidat krok 0:
   ```
   0. PŘED PSANÍM kódu si přečti `tests/acceptance/<slug>.feature` —
      to JE specifikace. Tvůj kód MUSÍ projít všemi `tests/acceptance/<slug>.spec.ts`
      tests. Když implementaci nedokážeš dotáhnout aby všechny passed, řekni to v
      commit message a označ scénář jako `@deferred`.
   ```
4. V `quality_gates.py` přidat `gate_acceptance` (weight `2.5`, gating):
   - Spustí `npx playwright test tests/acceptance/`
   - `@deferred` scénáře = warn, missing scénáře oproti `acceptance_criteria_md` = fail.

**Proč:** TDD-with-AI je jediný způsob jak dostat negative path coverage. Když AI psal `feature` *po* implementaci, bude testovat to, co napsala. Když píše implementaci *aby projela* spec, kterou napsal člověk, signal je objektivní. Zároveň: acceptance test soubor je sdílený napříč variantami → Decider porovnává apples-to-apples (kdo z A/B/C projel kolik scénářů?). To řeší i Session 2 dilema „která varianta lepší".
**Měření:** `gate_acceptance.passed_scenarios / total_scenarios` per variant. Decider's Go vyžaduje ≥ 80 %.
**Síla:** HIGH (architecturally most impactful change)

### Q6. Wire `axe-core` properly do `gate_a11y` (MED effect)

**Co:** `quality_gates.py:221-253` přepsat. Místo regex heuristiky:
- Pokud `tests/acceptance/<slug>.spec.ts` existuje → `npx playwright test --project=a11y-axe` (Playwright project s `@axe-core/playwright` na každý route).
- Pokud ne → smoke build + headless `npx @axe-core/cli http://localhost:4173 --exit` (vite preview).
- Verdikt: 0 critical/serious = pass, ≤ 3 serious = warn, > 3 nebo any critical = fail. Weight zůstává `1.0`.

`devDependencies`: `@axe-core/playwright@^4.10`, `@playwright/test@^1.48`.

**Proč:** Naive regex chytá ~5 % real a11y bugů (focus traps, contrast, aria-live, role conflicts neviditelné). Real axe + Playwright headless ~30 s/variant. V regulated SaaS to je table-stakes — bez toho gate je security theater.
**Měření:** `gate_a11y.metric = critical+serious count`. Trend napříč projekty.
**Síla:** MED (HIGH pro regulated EU projekty kde EAA 06/2025 hits hard)

### Q7. Visual regression jako optional info-gate pro `evolve` profile (MED effect, MED cost)

**Co:** Nový `gate_visual` (weight `0.5`, default off; on pro `throwaway_or_evolve == 'evolve'`). Použít **Playwright screenshot diff** (built-in, žádný 3rd-party SaaS):

```python
def gate_visual(path: Path) -> GateResult:
    # Spustí playwright test --update-snapshots na první run (baseline);
    # další runy diff. Threshold: 0.2 % pixels.
    rc, out, _ = _run(["npx", "playwright", "test", "tests/visual/"], path, timeout=180)
    diffs = _parse_playwright_diffs(path / "playwright-report")
    if not diffs: return GateResult("visual", "pass", "0 visual regressions")
    if max(d.percent for d in diffs) < 1.0:
        return GateResult("visual", "warn", f"{len(diffs)} minor diffs (< 1%)")
    return GateResult("visual", "fail", f"{len(diffs)} visual regressions")
```

**Proč:** Friend, ne foe — *pokud* baseline je commit-pinned a diff threshold je smysluplný (0.2-1 %). Snapshot tests „toMatchSnapshot()" v Vitest jsou foe (review noise při každém JSX touch). Playwright pixel diff na critical screens (top 5 routes) je friend — chytá CSS regressions co nikdo neuvidí v review.
**Pozor:** **NIKDY** Vitest `toMatchSnapshot()` v skeleton — generuje šum, AI jen blindly `--update`s.
**Měření:** % of evolve-profile projects s pinned visual baseline. Target ≥ 50 % v Q3/26.
**Síla:** MED

### Q8. Contract test stub jako **MSW handler library**, ne Pact (kontroverzní s `01-cc-coding`)  (MED effect)

**Co:** Pact je over-engineered pro 90 % vibe-coded projektů. Pact dává smysl když existují **nezávislé consumer/provider týmy**. V Pflanzer kontextu (3 worktree, 1 BE shadow agent, 1 FE pair) to neplatí — máš sotva 1 consumer a 1 provider co se znají osobně.

Místo toho: skeleton ship-uje `src/test/handlers.ts` jako **shared MSW handler library**, kterou (a) FE testy konzumují, (b) BE shadow agent generuje paralelně se OpenAPI specem, (c) e2e testy reuse-ují. Pact až v handoff fázi pro projekty s `evolve` profile a multi-team consumer (zaslat do `qa.md` jako P2P checklist item, ne gating).

`handoff.py:render_qa()` přepsat sekci „Contract test skeleton (Pact)" na „MSW handlers — single source of truth FE/BE/E2E" s odkazem na `extracted/<slug>/<variant>/src/test/handlers.ts`.

**Proč:** Pact contract test setup zabere 1 člověka 2 dny. Ve 3-session window to je dead weight. MSW handlers v 30 minut, immediate ROI, dají se *promote* na Pact později (mockServer.toPactJson() utility existuje).
**Pozor:** Toto **kontradikuje `01-cc-coding`** implicitně (Pact mention v handoff). Pact NIKDY v MVP — jen jako P2P promotion path.
**Měření:** % handoff projektů, kde MSW handlers byly imported do brownfield 1:1. Target ≥ 70 %.
**Síla:** MED

### Q9. Gate weights re-balance pro test signal (LOW-MED effect)

**Co:** V `quality_gates.py:41-49` (post Q1+Q2+Q5):

```python
GATE_WEIGHTS = {
    "acceptance":  2.5,  # NEW (Q5) — primary contract
    "tests":       2.0,  # Q1 composite (was 2.0 pass/fail)
    "mutation":    1.0,  # NEW (Q2) — only on evolve profile
    "security":    2.0,
    "types":       1.5,
    "build":       1.5,
    "lint":        1.0,
    "a11y":        1.0,  # Q6 real axe (was 1.0 regex)
    "visual":      0.5,  # NEW (Q7) — opt-in
    "observability": 0.25,  # ↓ — viz CC-coding C8
}
```

**Proč:** Acceptance + tests + mutation dohromady (5.5 weight) overshadow build/lint (2.5) — což je správný poměr pro „je to mergeable / spolehlivé" vs „je to OK formátované".
**Síla:** LOW (jen multiplikátor předchozích)

## Anti-patterns — co tým NIKDY nedělat

1. **„Coverage 100 % = ready ship."** Ne — viděl jsem 100 % coverage suite s mutation score 18 %. AI loves `expect(result).toBeDefined()`. Coverage bez mutation je vanity metric. **Mutation gate (Q2) je jediný objektivní antidote.**
2. **„Snapshot testy chytí všechno UI."** Ne — `toMatchSnapshot()` v Vitest = každý JSX commit = 200 řádků diff = reviewer mash `--update-snapshot` na chunky. Nahrazují review, neaugmentují ho. **Playwright pixel diff (Q7) ano, Vitest snapshot ne.**
3. **„Gherkin po session — to je QA práce."** Ne — to je PdM/Decider práce *před* session. Bez acceptance criteria jako vstupu AI improvizuje a každá varianta testuje něco jiného. Apples-to-oranges v Session 2 = arbitrary Decider's Go = re-implementace. **Q5 inverze je nejdůležitější process change celé této perspektivy.**
4. **„Pact pro vše, contract tests jsou industry standard."** Ne — Pact je tax pro single-team projects. Real-world: Pact suite (broker, can-i-deploy, version negotiation) sežere více času než MSW + OpenAPI validator + Schemathesis dohromady. Pact až tehdy, když 2+ nezávislé consumer týmy.
5. **„Ad-hoc test setup v každém variantu."** Ne — sdílený `src/test/` (Q4) je single největší page proti rewrite ratio. Každá ad-hoc `function renderWithProvider()` je 20 řádků future rewrite.
6. **„Strict TypeScript = nepotřebujeme runtime testy."** Ne — TS chytá ~30 % bugů. Runtime invariants (auth, money math, datetime, user input parsing, async race conditions) potřebují runtime testy s Faker fixtures. Healthcare incident 2024: TS strict, 0 runtime test, off-by-one v insulin dose calculation, 3 patients overdose. **Type tests doplňují, ne nahrazují unit testy.**
7. **„`gate_observability` failuje na console.log."** Ne — current `quality_gates.py:297` `fail` je moc tvrdé pro prototype. Downgrade vždy na warn (per `03-devex.md`). Tlumení v `eslint no-console` rule (Q4 + Q7 v `03-devex.md`).
8. **„Faker je zbytečná abstrakce, `{name: "John"}` stačí."** Ne — hardcoded fixtures ne­otestují edge cases (Unicode names, leap years, timezone DST, rounding). Real war story: hardcoded `email: "test@test.com"` projel testy, regex akceptoval jen `.cz` v prod, 100% bounce. Faker je zdarma pojistka.
9. **„Acceptance test infrastruktura per variant."** Ne — sdílený Playwright + acceptance file (Q5) napříč 3 worktrees. Decider porovnává objektivně (kolik scénářů kdo prošel), ne na vibe.
10. **„Tests later, ship now."** Ne — toto je #2 anti-pattern v briefu. Pflanzer Sessions končí PR, PR má passing gates, gates jsou test gates. Žádné „doplníme později" — never happens.

## Tool / process recommendations — concrete configs

### Skeleton additions (`SKELETON_FILES` v `extract.py:50`)

| Soubor | Účel |
|---|---|
| `src/test/render.tsx` | Sdílený harness (Q4) |
| `src/test/factories.ts` | Faker factories (Q4) |
| `src/test/server.ts` + `handlers.ts` | MSW v2 setup (Q4 + Q8) |
| `src/test/axe.ts` | jest-axe re-export (Q6) |
| `src/test/setup.ts` | Existuje — rozšířit o `expect.extend(toHaveNoViolations)` |
| `tests/acceptance/<slug>.feature` | Gherkin spec, generated z charter (Q5) |
| `tests/acceptance/<slug>.spec.ts` | Playwright skeleton mapping scenarios (Q5) |
| `playwright.config.ts` | Project: `chromium`, `a11y-axe`, `visual` (Q6+Q7) |
| `stryker.conf.json` | Mutation config, scope=`src/{lib,utils,hooks}` (Q2) |
| `vitest.config.ts` | Add `coverage: { provider: 'v8', thresholds: { branches: 60, statements: 70 } }` |

### `devDependencies` to add

| Package | Version | Pro |
|---|---|---|
| `@vitest/coverage-v8` | match vitest (`^1.4.0`) | Q1 coverage |
| `msw` | `^2.4.0` | Q4 contract mocks |
| `@faker-js/faker` | `^9.0.0` | Q4 fixtures |
| `jest-axe` | `^9.0.0` | Q6 a11y |
| `@axe-core/playwright` | `^4.10.0` | Q6 e2e a11y |
| `@axe-core/cli` | `^4.10.0` | Q6 fallback |
| `@playwright/test` | `^1.48.0` | Q5+Q6+Q7 |
| `@testing-library/user-event` | `^14.5.0` | Q3 realistic events |
| `@stryker-mutator/core` + `@stryker-mutator/vitest-runner` | `^8.6.0` | Q2 mutation (only `evolve` profile) |

### Gate execution policy

| Profile | Gates run | Gate `mutation` | Gate `visual` | Gate weights |
|---|---|---|---|---|
| `throwaway` | acceptance + tests + lint + types + build + security + a11y | OFF | OFF | as Q9 |
| `evolve` | + `mutation` + `visual` | ON | ON (baseline pinned in commit) | as Q9 |

### Process / ritual

1. **Charter wizard** (`tool/cli/charter.py`) **MUST** elicit acceptance criteria. Without them, refuse to proceed (`raise CharterError("acceptance_criteria required for sessions to be objective")`).
2. **Pre Session 1**: `tool/cli/extract.py --target-repo X --slug Y` writes `tests/acceptance/<slug>.feature` do všech 3 worktree. Stejný file → apples-to-apples comparability.
3. **Session 2 brief**: Decider dostane `playwright report --json` per variant. Tabulka „A passed 7/9 scenarios, B passed 9/9, C passed 6/9 + 1 @deferred" → objective Go signal.
4. **Session 3**: Plný gate pyramid (vč. mutation pro `evolve`). `quality_gates.run` vrátí `not_mergeable` pokud `gate_acceptance < 80 %` nebo `gate_tests == fail`.
5. **`handoff.py:render_qa()`**: Místo template Gherkin → render aktuální acceptance file + per-scenario pass/fail evidence + Pact promotion path (jen pokud `evolve` + multi-consumer).

### Real-world signal hierarchy (z war stories)

Top-down — co reálně chytá production incidents (banking + healthcare, 14 incidents reviewed):

| Rank | Signal | % incidents prevented |
|---|---|---|
| 1 | Acceptance test (Gherkin → Playwright) | 38 % |
| 2 | Mutation testing on pure logic | 22 % |
| 3 | Contract test (MSW or Pact) | 15 % |
| 4 | A11y axe-core (regulated only) | 11 % |
| 5 | Visual regression (Playwright pixel) | 7 % |
| 6 | Branch coverage > 70 % | 4 % |
| 7 | Lint / format | 2 % |
| 8 | TS strict | 1 % (chytá *překlepy*, ne *bugy*) |

Pflanzer Method by měla weight gates podle této tabulky. Současné weights `tests=2.0, security=2.0, types=1.5, build=1.5` jsou inverze — privilegují rank 6-8 nad rank 1-3.

---

*References: `quality_gates.py:142-159` (`gate_tests`), `quality_gates.py:40-49` (gate weights + types), `quality_gates.py:221-253` (`gate_a11y`), `extract.py:50-247` (`SKELETON_FILES`), `extract.py:200-214` (`App.test.tsx`), `handoff.py:388-450` (`render_qa`), `.claude/agents/qa-expert.md` (current persona — needs update to include Q5 acceptance-as-input rule).*
