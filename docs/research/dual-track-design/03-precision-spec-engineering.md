# 03 — Precision Spec Engineering (Pflanzer Track S fallback)

> **Cílový čtenář:** metodolog, EM/PM, sales engineer, který musí obhájit
> Track S spec proti námitce *„vždyť to dělá Spec Kit / Kiro / BMAD a generuje
> 2 577 ř. MD pro 689 ř. kódu."*
>
> **Datum:** 2026-05-28
> **Scope:** Track S = fallback Pflanzer mode, kdy dev tým **NENÍ v room**
> a Session 2 winner musí jít k nim jako spec, ne jako commit do target repa.
> **Pozice:** Track S **NENÍ preferovaná cesta** (default = Track A artefakt =
> running production code per `glossary.md`). Track S existuje pro 3 use casy:
> (1) vendor build, (2) regulatorně-mandated separate impl, (3) capacity-bound
> dev tým s vlastním sprint cadencem nesladitelným s 14-day Pflanzer cyklem.
>
> **Předchozí context:**
> - `docs/research/spec-driven-vs-pflanzer/01-sdd-mechanika.md`
>   (SDD failure modes, 9.8-42.1 % drift, 2 577 / 689 ratio)
> - `docs/research/spec-driven-vs-pflanzer/02-friction-quantification.md`
>   (cost data, 20-40 PD SDD vs 10 PD Pflanzer)
> - `docs/methodology/glossary.md` (artefakt = produkt; deprecated terms)
> - `docs/methodology/07-handoff-do-vyvoje.md` (sign-off package existující struktura)

---

## TLDR (5 řádků)

1. **Track S precision spec není 2 577-řádkový PRD.** Kombinuje 5 sekcí
   (Functional / Technical / Quality / Implementation / Sign-off)
   **napojených na běžící reference prototype z Session 1** — spec popisuje
   to, co stakeholder right now klikne na sandbox URL.
2. **Hlavní anti-drift mechanism = combined source of truth.**
   Spec ≠ source of truth alone. **Spec + Reference Prototype + Decision Log +
   Executable Acceptance Tests = SoT.** Re-implementation gap (Yan et al. 2025
   9.8-42.1 %) klesne, protože dev tým má 4 nezávislé anchory.
3. **Sign-off je cross-fn paralelní** (PM, FE, BE, Security, Legal, DPO,
   A11y, QA, EM) s explicitními veto rights per role + quality gate score
   ≥ 80/100 pro spec samotnou (ne až pro impl).
4. **Hand-off ritual má 5 stages:** Spec Walkthrough (90 min) → Q&A window
   (5 prac. dní) → Amendment protocol → First Milestone Review → Embedded
   Reviewer T+30. Bez 5/5 spec expires po 30 dní (proti spec staleness
   per Augment Code 2026).
5. **Honest:** Track S má re-implementation gap risk — Pflanzer ho **redukuje**
   díky reference prototype, ne **eliminuje**. Default mode (artefakt =
   produkt) ho **eliminuje úplně** (kód jde sám dál). Track S = degradovaný
   default, ne první volba.

---

## 1. Anatomy precision specu — 5 sekcí

### Princip: spec je **navigation layer**, ne re-implementation contract

Spec Kit / Kiro / OpenSpec selhávají, protože dělají *„LLM přečte spec,
vygeneruje impl"* — dvě LLM volání = compound hallucination (9.8-42.1 %
mismatch per Yan et al. 2025 × 2 ≈ 18-66 % effective drift).

Pflanzer Track S spec dělá *„dev čte spec + kliká reference prototype +
spouští executable acceptance testy + čte decision log"*. **Spec navádí
k 3 dalším anchorům**, není sám zdrojem pravdy. Tím Track S obchází
Berry & Kamsties (2004) NL-requirements ambiguity — ambiguita prose se
disambiguuje kódem, ne dalším prose.

### A. Functional spec

**Cíl:** stakeholder + dev tým rozumí *co* systém dělá a *proč*. Žádný
„jak" (to je sekce B).

#### A.1 User stories — INVEST format s edge case mandatorností

Každá user story musí splňovat INVEST kritéria (Bill Wake, viz
[Wikipedia](https://en.wikipedia.org/wiki/INVEST_(mnemonic))):

- **I**ndependent (nemůže být dependent na jiné story v batchi)
- **N**egotiable (popis je springboard pro konverzaci, ne literal contract)
- **V**aluable (dodává hodnotu komu — explicit persona link)
- **E**stimable (dev tým může odhadnout effort)
- **S**mall (vejde se do 1-3 sprint days nebo split na sub-stories)
- **T**estable (acceptance criteria executable, viz A.3)

**Pflanzer Track S delta vs vanilla INVEST:** přidává **2 mandatory
extensions**:

- **R** — **Referenced** (story linkuje na reference prototype URL /
  Figma frame / Session 1 transcript timestamp). Tím se zabraňuje
  Spec Kit anti-pattern *„user story bez ground truth artefaktu"*.
- **A** — **Attributed** (kdo z room v Session 1+2 story navrhl,
  kdo schválil — per AI Act čl. 14 human attribution requirement).

Final mnemonic: **INVEST-RA** (Pflanzer Track S extension).

**Template:**

```markdown
### US-NNN: <verb-first title>
Role: <Persona ID + link to persona doc>
Want: <concrete outcome, not feature noun>
So that: <business value, measurable if possible>

Referenced: <sandbox URL + timestamp || Figma frame ID || S1 transcript line>
Attributed: <proposer name> | <approver name (Decider)> | <date>

INVEST self-check:
- [ ] Independent (žádná dependency mimo batch)
- [ ] Negotiable (open for refinement)
- [ ] Valuable (link to OKR / metric)
- [ ] Estimable (T-shirt: XS/S/M/L)
- [ ] Small (≤ 3 dev days; jinak split)
- [ ] Testable (acceptance criteria below jsou executable)
```

#### A.2 Use case diagrams — Mermaid + ASCII fallback

**Formát volby:** **Mermaid** primary, **PlantUML** acceptable, **ASCII art**
allowed pro standalone snippet v ADR. Důvod Mermaid: native GitHub render,
LLM-friendly, version-control diffable jako text.

C4 model je acceptable, ale Mermaid C4 syntax je k 05/2026 stále
experimental (per [Mermaid docs](https://mermaid.js.org/syntax/c4.html))
— **default Track S = Mermaid sequence / flowchart**, C4 jen pro Context
+ Container úroveň, ne Component+.

**Antipattern:** PDF screenshoty diagramů. Žádný diagram, který nelze
diffnout v PR review, nepatří do Track S spec.

#### A.3 Acceptance criteria — Gherkin executable BDD

**Format:** Given/When/Then v Cucumber-compatible syntaxi. Per
[Automation Panda Gherkin guidelines for AI](https://automationpanda.com/2026/04/27/bdd-gherkin-guidelines-for-ai-coding-and-testing/)
(04/2026), AI-generated Gherkin drifts do *„vague Then steps, UI-heavy
scripts, multi-behavior scenarios, placeholder examples"*. Track S
spec proto vyžaduje:

- **Single behavior per scenario** (žádné *„And then user also sees..."*)
- **Concrete Then assertions** (`Then user receives HTTP 401 with body
  '{"error": "invalid_token"}'`, ne `Then login fails`)
- **No UI implementation detail v Given/When** (`Given user is authenticated`,
  ne `Given user clicked button id=login-submit`)
- **≥ 1 negative scenario per feature** (mandatory — bez negative scenario
  spec není sign-off ready)
- **3-5 scenarios per user story** (happy path + 2-4 edge cases)

**Příklad:**

```gherkin
Feature: Token refresh during long session

  Background:
    Given OAuth provider returns 60-min access tokens
    And refresh tokens valid for 30 days

  Scenario: Happy path — silent token refresh at 55-min mark
    Given user has active session with token issued 55 minutes ago
    When user triggers any authenticated API call
    Then system refreshes token transparently
    And user sees no interruption
    And new access_token expires 60 min from refresh moment

  Scenario: Refresh token expired (negative — MANDATORY)
    Given user has refresh_token issued 31 days ago
    When system attempts silent refresh
    Then system returns HTTP 401 with error_code=REFRESH_EXPIRED
    And user is redirected to login flow
    And session storage is cleared

  Scenario: Refresh during network partition
    Given user has valid refresh_token
    And OAuth provider returns 503 for 60 seconds
    When system attempts refresh
    Then system retries with exponential backoff (1s, 2s, 4s, 8s)
    And after 4 retries fails to login with error_code=AUTH_PROVIDER_DOWN
    And cached read-only data remains accessible per offline mode
```

**Anti-drift mechanism:** Gherkin scénáře musí být **executable** v target
repo (Cucumber.js / behave / pytest-bdd), ne prose-only. Per
[Augment Code SDD guide](https://www.augmentcode.com/guides/what-is-spec-driven-development):
*„SDD transforms BDD scenarios into executable validation gates."*
**Track S enforcement:** acceptance criteria CI job musí být zelený před
spec sign-off — žádná spec nepředaná dev týmu obsahuje pending Gherkin
scénáře.

#### A.4 Happy path + 3-5 edge cases per feature (mandatorní)

Per `02-friction-quantification.md` § Round 5, defects nezachycené v spec
costí **50-200×** víc per Boehm 1981. Track S anti-drift = explicit
edge case enumeration **PŘED** impl:

| Edge case typ | Minimum per feature |
|---|---|
| **Validation failure** (input boundary, malformed) | 1 |
| **Network/dependency failure** (timeout, 503, partition) | 1 |
| **Concurrent access** (race, deadlock proxy) | 1 — pokud aplikabilní |
| **Permission denied** (unauthenticated, wrong role) | 1 |
| **Capacity/scale degradation** (rate limit, quota) | 1 — pokud aplikabilní |

Pro feature *„OAuth login"*: minimum **4 edge cases** (validation, network,
permission, scale). Spec autoři vyjmenovávají + Gherkin scenario per edge
case (sekce A.3).

#### A.5 Out-of-scope sekce — explicit boundaries

Per [Scott Logic Spec Kit critique](https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html)
(11/2025), Spec Kit *„generates lengthy spec files"* — scope creep během
spec generation. Track S anti-pattern: **explicit out-of-scope list**
v každé spec sekci.

**Template:**

```markdown
## Explicitly NOT in scope (v1.0)

- ❌ SAML SSO — out (Track A jen OIDC pro v1.0; SAML do v2.0 backlog)
- ❌ Multi-factor authentication — out (separate spec SP-NNN)
- ❌ Cross-device session sync — out (mobile spec deferred)
- ❌ Account recovery flow — out (existující flow zůstává)

Rationale: scope locked v Session 2 (winner varianta byla without these).
Re-opening scope = signed amendment per § 5 Handoff ritual.
```

### B. Technical spec

**Cíl:** dev tým rozumí *jak* postavit; žádné guesswork, žádné implicit
contracts.

#### B.1 OpenAPI 3.1 contracts — complete, lint-clean, ne draft

Per `07-handoff-do-vyvoje.md` BE sekce: **Lintovaný OpenAPI 3.1**
(Spectral clean, examples per endpoint, RFC 7807 errors,
idempotency-key konvence). Track S delta: **OpenAPI je v `tool/templates/`
git-versioned, ne PDF**. Generován ze Session 1 backend shadow agenta,
finalized v Session 2.

**CI enforcement** (per
[apitect 2026 schema drift article](https://apitect.com/blogs/stopping-schema-drift-how-to-keep-your-openapi-spec-and-code-in-sync-automatically)):

```yaml
# .github/workflows/spec-lint.yml
- name: Lint OpenAPI
  run: spectral lint api/openapi.yaml --ruleset .spectral.yaml --fail-severity=warn

- name: Breaking-change check
  run: oasdiff breaking previous-openapi.yaml api/openapi.yaml --fail-on ERR

- name: Schemathesis property tests
  run: schemathesis run api/openapi.yaml --checks all --hypothesis-database=none

- name: Pact contract verification (consumer-driven)
  run: pact-broker can-i-deploy --pacticipant <service> --version $GIT_SHA
```

**Bez 4/4 zelených bodů spec není sign-off ready.**

#### B.2 Data model — ERD + JSON schemas + sample payloads

- **ERD**: Mermaid `erDiagram` v repu (text-diffable; PR review-able).
- **JSON Schema 2020-12** per entity (uložené v `schemas/*.schema.json`,
  pulled into OpenAPI components).
- **Sample payloads**: 3-5 reálných příkladů per endpoint v `examples/`
  (happy + 2 negative + 1 boundary), validované proti schema v CI.

**Anti-drift:** Schemathesis (per
[Pactflow contract testing guide](https://pactflow.io/blog/contract-testing-using-json-schemas-and-open-api-part-3/))
generuje stovky property tests z OpenAPI; falsifikuje spec, pokud impl
runtime nevyhoví.

#### B.3 Component architecture diagram — Mermaid

C4 Level 2 (Container) MUST. C4 Level 3 (Component) MAY pokud feature
spans 5+ services. Diagram MUSÍ:

- pojmenovat všechny existing components, které feature touches (proti
  Böckeler / Martin Fowler anti-pattern *„AI agent ignored existing
  classes, generated duplicates"*)
- explicit ownership boundaries (jaký tým vlastní jakou box)
- data flow direction (sync / async / event)
- trust boundaries (mandatory pro STRIDE sekce — viz C.4)

#### B.4 Tech stack constraints — explicit allow/deny list

Spec Kit anti-pattern: spec říká *„use modern web framework"* → dev tým
si vybere → 6 týmů v org má 6 stacků → fragmentace.

**Track S enforcement:**

```markdown
### Tech stack — MUST / MAY / MUST NOT

#### MUST
- Frontend: **Next.js 15.x** (per platform paved-road `customer-portal`
  cookiecutter)
- Backend: **FastAPI 0.115+** with **Pydantic v2**
- DB: **PostgreSQL 16** (existing prod cluster `prod-eu-1`)
- Auth: **OIDC via existing Keycloak realm `b2b`** (NE custom JWT)
- Observability: **OpenTelemetry** + existing **Grafana stack**

#### MAY
- Caching: Redis MAY (pokud justified v ADR), default no-cache
- Testing: pytest preferred, vitest if FE-only

#### MUST NOT
- ❌ MongoDB / non-relational primary store (org standard = Postgres)
- ❌ Custom auth implementation (bezpečnostní policy)
- ❌ AWS Lambda (org runs k8s; serverless = separate ADR)
- ❌ Bleeding-edge libraries < 6mo since stable release (per platform
  paved-road policy)
```

#### B.5 Integration points — external systems

Tabulka per integration:

| System | Direction | Auth | SLA | Owner | Fallback |
|---|---|---|---|---|---|
| Keycloak (existing) | OAuth provider | client_credentials | 99.95 % | Platform | Cached refresh tokens 15 min |
| Stripe (existing) | Payment webhook | HMAC signature | best-effort | Billing team | Async queue + replay |
| <KYC vendor> | Inbound REST | mTLS + API key | 99.9 % per SLA | Compliance vendor | Manual override flow |

#### B.6 Performance NFRs — concrete numbers

Per `07-handoff-do-vyvoje.md` Platform sekce, target SLO archetype:

```markdown
### Performance NFRs (v1.0)

| Metric | Target | Measurement | Validation |
|---|---|---|---|
| p95 latency (read) | < 300 ms | OpenTelemetry traces | k6 load test in CI |
| p95 latency (write) | < 800 ms | OpenTelemetry traces | k6 load test in CI |
| Availability | 99.9 % / 30d | SLO panel Grafana | Error-budget burn alert |
| Error budget | 0.1 % / 30d | error_rate / total_req | PagerDuty if 25 % consumed in 24h |
| Throughput | 1 000 RPS sustained | Load test | k6 ramp-up scenario |
| Cold start | < 2 s | First-request trace | E2E playwright test |
```

### C. Quality spec

**Cíl:** QA + Security + A11y + Compliance mají audit-grade evidence
že systém je `done` per definition before sign-off.

#### C.1 Test scenarios — BDD per layer

Per `07-handoff-do-vyvoje.md` QA sekce + AI Act čl. 14 audit trail
requirement (viz `02-friction-quantification.md` § 4.3):

```markdown
### Test pyramid split

| Layer | % effort | Owner | Tool |
|---|---|---|---|
| Unit | 70 % | Dev | pytest / vitest |
| Integration | 20 % | Dev + QA | pytest + testcontainers |
| E2E | 10 % | QA | Playwright |
| Contract | overlay | Dev + QA | Pact + Schemathesis |
| Property | overlay | Dev | Hypothesis (python) / fast-check (JS) |
```

#### C.2 Unit test prerequisites

**Mandatorní coverage:** každá veřejná funkce/class implementující
acceptance criterion MUSÍ mít unit test pojmenovaný per scenario ID
z Gherkin sekce A.3 (e.g., `test_token_refresh_happy_path_silent`).

**Coverage gate:** > 80 % branch coverage pro spec-derived modules
(ne celý repo — jen kód odpovídající na user stories této specifikace).

#### C.3 E2E test scenarios — Playwright pseudo-code

Per Gherkin scenario v A.3, MUSÍ existovat Playwright skeleton:

```typescript
// tests/e2e/oauth-refresh.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Token refresh during long session', () => {
  test('happy path — silent token refresh at 55-min mark', async ({ page }) => {
    // Setup: token issued 55 min ago (uses test-only API)
    await page.goto('/api/test/seed-session?token_age=3300');
    await page.goto('/dashboard');

    // Trigger authenticated API call
    await page.click('[data-testid=refresh-data]');

    // Assertion: data loaded, no login redirect
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('[data-testid=data-loaded]')).toBeVisible();

    // Assertion: new token in storage with expected expiry
    const tokenExpiry = await page.evaluate(() =>
      JSON.parse(localStorage.getItem('access_token')).exp
    );
    expect(tokenExpiry).toBeGreaterThan(Date.now() / 1000 + 3500);
  });

  test('refresh token expired — redirect to login', async ({ page }) => {
    // ... per Gherkin scenario A.3
  });
});
```

#### C.4 Security threat model — STRIDE one-pager

Per [Stellar STRIDE template](https://developers.stellar.org/docs/build/security-docs/threat-modeling/STRIDE-template)
+ `07-handoff-do-vyvoje.md` § Compliance handoff:

```markdown
### STRIDE one-pager — feature: OAuth login + refresh

#### What are we building?
[Mermaid dataflow diagram with trust boundaries]

#### Threats identified

| ID | STRIDE category | Threat | Severity | Mitigation ID |
|---|---|---|---|---|
| S.1 | Spoofing | Stolen refresh token replayed by attacker | High | S.1.R.1 |
| T.1 | Tampering | JWT signature bypass via algorithm confusion | Critical | T.1.R.1 |
| R.1 | Repudiation | User claims they never logged in | Medium | R.1.R.1 |
| I.1 | Information Disclosure | Tokens leaked in browser history | High | I.1.R.1 |
| D.1 | Denial of Service | Refresh endpoint hammered | High | D.1.R.1 |
| E.1 | Elevation of Privilege | Role injection via JWT claims | Critical | E.1.R.1 |

#### Mitigations

| ID | Mitigation |
|---|---|
| S.1.R.1 | Refresh token rotation on each use; old token invalidated |
| T.1.R.1 | Explicit `alg=RS256` enforcement; reject `none`, `HS256` from external |
| R.1.R.1 | Decision log v Pflanzer tool DB per AI Act čl. 14 |
| I.1.R.1 | httpOnly + Secure cookies; never localStorage for tokens |
| D.1.R.1 | Rate limit 10 refresh / min per user; 1 000 / min per IP |
| E.1.R.1 | Claims validation against allow-list; signed by trusted issuer |

#### Did we do a good job?
- [ ] Pentest scheduled for v1.0 launch -7d
- [ ] DAST scan in CI passes
- [ ] SBOM (cyclonedx) clean of Critical/High CVE
- [ ] Secret scan (gitleaks) clean
```

**Anti-drift:** STRIDE one-pager je v repu jako `docs/security/<feature>-stride.md`,
ne v PDF / Confluence. Reviewed Security lead + Decider, version-controlled.

#### C.5 A11y baseline — WCAG 2.2 AA checklist

Per [WCAG 2.2 + EAA compliance guide](https://www.levelaccess.com/compliance-overview/european-accessibility-act-eaa/)
(EAA enforcement 06/2025): **WCAG 2.2 Level AA = baseline pro EU consumer
products**. Track S spec MUSÍ obsahovat:

```markdown
### A11y baseline — WCAG 2.2 AA

#### Mandatory checks per feature (axe-core + manual)
- [ ] **1.4.11 Non-text Contrast** (≥ 3:1 for UI components, focus indicators)
- [ ] **2.1.1 Keyboard** (all interactive reachable + operable via keyboard)
- [ ] **2.4.7 Focus Visible** (custom focus ring visible per design tokens)
- [ ] **2.4.11 Focus Not Obscured (Minimum)** [NEW WCAG 2.2] (focused element
      partially visible)
- [ ] **2.5.8 Target Size (Minimum)** [NEW WCAG 2.2] (≥ 24×24 CSS px touch targets)
- [ ] **3.2.6 Consistent Help** [NEW WCAG 2.2] (help link in same location)
- [ ] **3.3.7 Redundant Entry** [NEW WCAG 2.2] (don't re-ask info user provided)
- [ ] **3.3.8 Accessible Authentication (Minimum)** [NEW WCAG 2.2] (no cognitive
      function test in login)
- [ ] **4.1.3 Status Messages** (ARIA live region for refresh status)

#### Validation
- axe-core CI run on every PR (zero Critical/Serious)
- Manual keyboard test top 3 user flows (per A11y reviewer)
- Screen reader test (NVDA + VoiceOver) — AI proxy NESTAČÍ pro EAA per
  `07-handoff-do-vyvoje.md` § Compliance handoff
```

#### C.6 Compliance — AI Act tier + DPIA trigger + DORA scope

Per `07-handoff-do-vyvoje.md` § Compliance handoff + per
[AI Act Article 14 implementation guide](https://www.knowlee.ai/blog/ai-audit-trail-implementation-guide):

```markdown
### Compliance classification

#### AI Act risk tier (Fáze C final, per ADR-0013)
- **Tier:** Limited Risk (deployer obligations only, ne High-risk system)
- **Rationale:** OAuth není ML model, není automated decision-making per
  čl. 22 GDPR (autorizace ano/ne není „rozhodnutí s legal effect")
- **Annex IV tech doc:** N/A (Limited Risk nemá Annex IV mandate)
- **Signed:** DPO @datum

#### DPIA trigger (GDPR čl. 35)
- **Trigger evaluation:** per
  [IAPP DPIA triggers](https://iapp.org/resources/article/what-triggers-a-dpia-under-the-gdpr)
  + national DPA Muss-Liste
  - [ ] Large-scale special category data — NE (OAuth není special category)
  - [ ] Systematic monitoring — NE
  - [ ] Automated decision making with legal effect — NE
  - [ ] Innovative use of new technologies — NE (standard OIDC)
  - [ ] Vulnerable subjects (children) — NE (B2B SaaS, adults only)
- **Verdict:** DPIA **NEPOTŘEBA** pro v1.0 OAuth feature
- **Signed:** DPO @datum

#### DORA scope (Article 28)
- **Vendor classification:** Keycloak = managed in-house (NE ICT third party)
- **Register entry:** N/A (no external ICT contract)
- **Resilience SLA:** per § B.6 Performance NFRs (99.9 % / 30d)
- **Signed:** Risk officer @datum

#### Audit trail (AI Act čl. 14 + DORA 7-year retention)
- Decision log: Pflanzer tool DB (`decisions/<pilot-id>.yaml`)
- Retention: 7 let (DORA), backed up to immutable storage
- Per-decision: rozhodnutí | navrhovatel | schvalovatel | datum | rationale
```

### D. Implementation guidance

**Cíl:** dev tým neztrácí kalendárové dny na bikeshedding setup; zero
ambiguity pro „naming convention", „lint config", „file structure".

#### D.1 File structure proposal

```
target-repo/
├── apps/
│   └── auth-service/
│       ├── src/
│       │   ├── routes/        # FastAPI routers (1 per resource)
│       │   ├── services/      # business logic
│       │   ├── models/        # Pydantic + SQLAlchemy
│       │   ├── adapters/      # external integrations (Keycloak)
│       │   └── tests/
│       │       ├── unit/
│       │       ├── integration/
│       │       └── e2e/
│       ├── api/
│       │   └── openapi.yaml   # spec-versioned with code
│       ├── docs/
│       │   ├── security/
│       │   │   └── stride.md
│       │   └── adr/
│       └── pyproject.toml
└── packages/
    └── auth-client/           # generated from OpenAPI
```

**Anti-drift:** OpenAPI v `apps/<svc>/api/openapi.yaml` je **single source**
pro server stubs (FastAPI route gen) i client SDK (`packages/auth-client/`).
Spec change = client regenerate = CI catch dříve než runtime.

#### D.2 Naming conventions

```markdown
### Naming conventions

#### Python (BE)
- ESLint/Prettier? **NE — Ruff + Black** (per platform paved-road)
- File names: `snake_case.py`
- Class names: `PascalCase`
- Function names: `snake_case`
- Constants: `SCREAMING_SNAKE_CASE`

#### TypeScript (FE)
- File names: `PascalCase.tsx` for components, `camelCase.ts` for utils
- Component names: `PascalCase`
- Hook names: `useCamelCase`
- Constants: `SCREAMING_SNAKE_CASE`

#### Database
- Table names: `snake_case`, plural (`users`, `refresh_tokens`)
- Column names: `snake_case`
- FK: `<referenced_table>_id`

#### API endpoints
- URL: `/v1/<resource>/<id>` (RESTful)
- Methods: standard HTTP verbs
- Errors: RFC 7807 Problem Details
```

#### D.3 Recommended libraries — pinned versions

Per platform paved-road template (per `07-handoff-do-vyvoje.md` § 5):

```markdown
### Libraries (v1.0, pinned)

#### BE
- fastapi==0.115.4
- pydantic==2.9.2
- sqlalchemy==2.0.36
- psycopg[binary]==3.2.3
- authlib==1.3.2  # OIDC client
- httpx==0.27.2
- pytest==8.3.3
- pytest-asyncio==0.24.0
- schemathesis==3.39.5

#### FE
- next@15.0.3
- react@19.0.0
- @tanstack/react-query@5.59.0
- zod@3.23.8
- playwright@1.49.0
- vitest@2.1.5
```

#### D.4 Anti-patterns — project-specific

```markdown
### Anti-patterns (MUST NOT)

- ❌ `localStorage` for tokens (per STRIDE I.1.R.1 — use httpOnly cookies)
- ❌ Synchronous external API calls in request hot path (use async + circuit
  breaker per Resilience4j / aiobreaker)
- ❌ ORM N+1 queries (use `selectinload` for related collections)
- ❌ Untyped function signatures (mypy strict mode required)
- ❌ Magic numbers (constants module mandatory)
- ❌ Print debugging (use OpenTelemetry spans + structured logs)
- ❌ Commit secrets (pre-commit hook with gitleaks)
```

#### D.5 Code review checklist

```markdown
### PR review checklist (auto-injected in PR template)

- [ ] All Gherkin acceptance scenarios pass in CI
- [ ] Branch coverage ≥ 80 % for changed modules
- [ ] OpenAPI spec updated if endpoint changed
- [ ] Pact contract validated against new spec version
- [ ] STRIDE one-pager updated if new trust boundary
- [ ] axe-core CI passes (Critical/Serious = 0)
- [ ] No new Critical/High CVE in SBOM
- [ ] ADR linked if architectural decision made
- [ ] Decision log entry if cross-fn decision
```

### E. Sign-off requirements

**Cíl:** žádný late-stage veto („security found this in week 4"). Cross-fn
parallel sign-off **before** spec leaves Pflanzer hub.

#### E.1 Who must approve

Per `07-handoff-do-vyvoje.md` § 8 + per AI Act čl. 14 attribution:

| Role | Section approval | Veto right |
|---|---|---|
| **Decider** (sponsor / VP) | Overall scope + commercial | YES — final |
| **PM** | A. Functional spec | YES if user story not valuable |
| **EM** (engineering manager) | B. Technical spec + D. Implementation | YES if not implementable in committed capacity |
| **FE lead** | B.3, B.4, D.1-D.5 (FE parts) | YES if FE infeasible |
| **BE lead** | B.1, B.2, B.5, B.6 | YES if BE infeasible |
| **Security lead** | C.4 STRIDE + B.5 integrations | YES on Critical/High threat unmitigated |
| **DPO** | C.6 AI Act + DPIA + GDPR | YES if Privacy by Design missing |
| **Legal counsel** | C.6 DORA + contract clauses | YES if regulatory blocker |
| **A11y reviewer** | C.5 WCAG 2.2 AA | YES if Critical/Serious axe issues |
| **QA lead** | C.1-C.3 test scenarios | YES if scenarios untestable |
| **CS proxy** | Ticket prediction + support docs plan | NO veto (informed only) |
| **Data lead** | Event taxonomy + measurement plan | NO veto (informed; veto via metric ownership) |

**Decider mandate per ADR-0001:** Decider votes **last** (anti-HiPPO).
Veto rights are **scope-locked** per role — security cannot veto pricing
copy, PM cannot veto STRIDE mitigation.

#### E.2 Approval order — parallel with veto callout

**NE sequential.** Sequential = 4-week calendar delay per
`02-friction-quantification.md` § Round 3.

**Parallel sign-off (5 prac. dní windowed):**

```
Day 1: Spec authors publish v1.0 RC to Pflanzer hub
Day 1-3: Each role reviews their owned sections in parallel
Day 3: Cross-functional callout (90 min meeting):
        - any veto raised? rationale heard, addressed or amendment opened
        - blocking concerns become amendment proposals
Day 4-5: Amendments incorporated by spec authors
Day 5 EOD: All roles sign — spec moves to v1.0 final
Day 6+: Spec hand-off ritual starts (§ 5 below)
```

#### E.3 Veto rights per role

Per § E.1 tabulka. **Veto = scope-locked**. Out-of-scope veto
(e.g., FE lead veto for security threat) = escalation to Decider, who
adjudicates (anti-HiPPO: Decider votes last, but adjudicates territorial
disputes immediately).

#### E.4 Quality gate score pro spec samotnou

**Spec quality gate ≥ 80/100 PŘED spec leaves hub.**

| Dimension | Weight | Self-check |
|---|---|---|
| **A.1 INVEST-RA user stories** | 10 | All stories meet 8/8 checklist? |
| **A.3 Gherkin executable** | 15 | All scenarios runnable in CI? ≥ 1 negative per feature? |
| **A.4 Edge cases enumerated** | 10 | ≥ 4 edge cases per feature (validation, network, permission, scale)? |
| **B.1 OpenAPI lint-clean** | 10 | Spectral 0 errors? |
| **B.2 ERD + JSON Schema** | 5 | Schema validates sample payloads? |
| **B.4 Tech stack explicit** | 5 | MUST/MAY/MUST NOT lists complete? |
| **B.6 Performance NFRs** | 5 | Numbers, ne adjectives? |
| **C.4 STRIDE one-pager** | 10 | All 6 categories addressed + mitigations? |
| **C.5 WCAG 2.2 AA checklist** | 5 | New 2.2 criteria addressed (2.4.11, 2.5.8, 3.2.6, 3.3.7, 3.3.8)? |
| **C.6 AI Act + DPIA + DORA** | 10 | Tier classification signed? DPIA trigger eval done? |
| **D.1-D.5 Implementation guidance** | 10 | File structure + libraries pinned + anti-patterns explicit? |
| **E. Sign-off complete** | 5 | All 11 roles signed (or noted N/A with rationale)? |
| **TOTAL** | 100 | ≥ 80 = hand-off ritual go |

**Score < 80 = spec re-work, ne hand-off.** Avoid replicating Spec Kit
*„sign off and pray"* anti-pattern (per Böckeler 11/2025).

---

## 2. Anti-drift mechanisms — 6 patterns

### 2.1 Spec + Reference Prototype + Decision Log + Tests = combined SoT

**Hlavní Track S anti-drift.** Žádný single dokument není sole source
of truth. Dev tým má 4 nezávislé anchory:

1. **Spec** (markdown, A-E sekce) — *„co a proč"*
2. **Reference prototype** (running on sandbox URL z Session 1) —
   *„jak má vypadat ve fungování"*
3. **Decision log** (rationale per AI Act čl. 14) — *„proč ne jinak"*
4. **Executable acceptance tests** (Gherkin + Pact + Schemathesis) —
   *„jak ověřit"*

Konflikt 2 zdrojů = amendment (§ 5.3 Amendment protocol). Konflikt 3+
zdrojů = spec re-issue. **Tím Pflanzer Track S obchází SDD failure mode
*„spec drift = spec drifts from code"*** — pro Track S spec drifts from
4 anchorů; každý disagreement je detekován.

Per [Augment Code „Living Specs"](https://www.augmentcode.com/guides/living-specs-for-ai-agent-development):
*„Static specs face four documented failure modes: expensive to maintain,
cannot capture all implicit context, drift over time, do not account
for iteration."* **Pflanzer Track S addresses all four:**

| Failure mode | Track S mitigation |
|---|---|
| Expensive to maintain | Spec autoři = Session 1+2 team, ne separate spec team. Maintenance = amendment, ne re-write. |
| Cannot capture implicit context | Reference prototype zachycuje implicit (klikatelný, observable). |
| Drift over time | CI breaks if spec ↔ impl ↔ tests diverge. |
| Doesn't account for iteration | Amendment protocol je first-class (§ 5.3). |

### 2.2 Spec versioning + change log + ADR cross-link

Per [MADR conventions](https://github.com/adr/madr):

- Spec versioning: **SemVer 2.0.0** (MAJOR.MINOR.PATCH)
- MAJOR = breaking scope change (e.g., feature removal, schema break)
- MINOR = new scope (additional user story)
- PATCH = clarification (no semantic change)
- **CHANGELOG.md** per spec, Keep a Changelog 1.0.0 format
- **ADR cross-link:** každý spec change MAJOR/MINOR má linked ADR
  („Supersedes ADR-NNNN", „Refines ADR-NNNN")

**Charter version pinned:** spec frontmatter linkuje na Charter SHA
(per `method-charter.md` Pre-registration protocol). Bez Charter pin
= spec není auditovatelný.

### 2.3 Bidirectional sync — dev team can request amendment, sponzor approves

Per § 5.3 Amendment protocol (níže). **Tessl-style** (per
`01-sdd-mechanika.md` § 1.5), ale ne *„spec as source"* — *„spec
as navigation, dev má amendment proposal right, sponzor adjudikuje"*.

**Anti-drift triggery z dev týmu:**
- *„This Gherkin scenario unimplementable v current stack"* → amendment B.4
- *„STRIDE missed X threat we discovered"* → amendment C.4
- *„Performance NFR unachievable"* → amendment B.6 + sponzor scope cut

### 2.4 Reference implementation (Session 1 mini-prototype) jako combined SoT

**Tohle je hlavní Pflanzer differentiation vs SDD.** Spec Kit / Kiro /
OpenSpec dělají *„spec → impl"* (one direction). Pflanzer Track S dělá
*„spec + reference prototype z S1 → impl"* (two anchory).

Per `01-sdd-mechanika.md` § 6.2 *„Funkční prototyp od minuty 1 vs 2 577
řádků markdownu"*:

> *„3 paralelní funkční weby z Session 1 (3h). Stakeholder kliká na real
> URL, ne čte PRD."*

Track S využívá **winner varianta z S2** (production-ready code z S1
+ S2 polish) jako reference prototype. Sandbox URL TTL extended z 24h
default na **30 dní pro Track S** (per `08-edge-cases-a-rizika.md`
forthcoming addendum — flag, NE merge tady, sponsor signs prodloužení).

**Dev tým:**
1. Čte spec markdown
2. Kliká reference prototype (vidí UX intent)
3. Spouští Gherkin acceptance tests v sandbox repo
4. Implementuje v target repo
5. Run Gherkin tests proti target repo — pass = done

**Anti-drift compound:** mismatch mezi sandbox a target = test fails;
dev tým ví, že drift se nedá ignorovat (ne *„yeah looks similar"* per
OpenSpec Attempt 1 — 2h + zero change).

### 2.5 Acceptance criteria as executable (Gherkin BDD)

Per `01-sdd-mechanika.md` § 4.4 *„AI hallucinations v spec → AI
hallucinations v impl (compound)"*. Track S mitigation: acceptance
criteria nejsou prose, jsou executable Gherkin → spustitelný v Cucumber/
behave/pytest-bdd → CI red/green binary signal.

**Per [Automation Panda 2026](https://automationpanda.com/2026/04/27/bdd-gherkin-guidelines-for-ai-coding-and-testing/):**
spec authors v Session 2 explicitně dělají *„spec autoři vlastní Gherkin,
QA lead validates that scenarios run before sign-off"*. CI gate.

### 2.6 Continuous spec ↔ impl monitoring (linter / checker)

Per [apitect 2026 schema drift article](https://apitect.com/blogs/stopping-schema-drift-how-to-keep-your-openapi-spec-and-code-in-sync-automatically):

```yaml
# In target dev repo .github/workflows/spec-sync.yml
- name: Verify spec sync
  run: |
    # Pull latest spec from Pflanzer hub
    git submodule update --remote specs/
    # Run Schemathesis: does impl match spec?
    schemathesis run specs/openapi.yaml --base-url $STAGING_URL --checks all
    # Run Pact: do consumer contracts hold?
    pact-broker can-i-deploy --pacticipant $SERVICE_NAME --version $GIT_SHA
    # If any check fails → block merge → file amendment proposal
```

**Schedule:** every PR + nightly cron. Cron failure = automatic
amendment proposal opened (auto-Slack to spec authors + dev team lead).

### 2.7 Mandatory spec review by dev team within 30 days

Per [Augment Code 2026](https://www.augmentcode.com/guides/what-is-spec-driven-development):
*„Most spec-driven tools produce static documents that drift from
implementation within hours."*

Track S enforcement: **spec expires po 30 dní bez handoff ritual start**.
Pokud dev tým neudělá Q&A + Walkthrough do 30 dní od sign-off, spec is
**flagged stale** v Pflanzer hub. Re-issue = re-sign-off cyklus.

**Důvod:** scope context decays fast (per Augment Code) — 30 dní je
honest upper bound před tím, než spec autoři ztratí mental model
z Session 2.

---

## 3. Markdown template — odkaz na separate file

Plnou markdown template viz:

**`/Users/gizmax/Documents/PflanzerMethod/tool/templates/precision-spec-track-s.md.template`**

Template obsahuje:
- YAML frontmatter (project, version, charter ref, signers, dates)
- Sekce A. Functional spec (user stories INVEST-RA, Mermaid diagrams,
  Gherkin acceptance, edge cases, out-of-scope)
- Sekce B. Technical spec (OpenAPI, ERD, architecture diagram, stack,
  integrations, NFRs)
- Sekce C. Quality spec (test pyramid, unit/E2E, STRIDE, A11y, AI Act/DPIA/DORA)
- Sekce D. Implementation guidance (file structure, naming, libs, anti-patterns, PR checklist)
- Sekce E. Sign-off matrix + quality gate score sheet
- Acceptance gate (≥ 80/100, hand-off ritual entry condition)

---

## 4. Comparison table — Pflanzer Track S vs SDD frameworks

| Dimension | **Pflanzer Track S** | Spec Kit | Kiro | OpenSpec | BMAD-METHOD |
|---|---|---|---|---|---|
| **Spec format** | Markdown + Gherkin + OpenAPI 3.1 + STRIDE + WCAG 2.2 AA + ADR cross-link | Markdown PRD + plan + tasks | EARS notation + design + tasks | Markdown proposal + specs + design + tasks | Multi-agent PRDs + architecture + stories |
| **Length (MD lines per feature)** | **~300-500** (terse, prototype-referenced) | **2 577** (Scott Logic Feature 1) | **excessive** (4 stories + 16 ACs single-line bug) | **high** (Attempt 2: more tasks than code) | **high** (12+ agents generating) |
| **Markdown : code ratio** | **target 0.5-1.0 : 1** (because reference prototype carries weight) | **3.74-7.54 : 1** | unclear, high | high | high |
| **Acceptance criteria format** | **Executable Gherkin** (CI gate) | Prose + sometimes Given/When/Then | EARS notation (prose with structure) | Prose + checklists | Prose user stories |
| **Negative scenarios mandatory** | **YES — ≥ 1 per feature** | No mandate | No mandate | No mandate | No mandate |
| **Sign-off process** | **Parallel 5-day window, 11 roles + Decider, veto-scoped** | Single dev + AI review | IDE-based, single user | Single proposer + AI | Multi-agent (no humans) |
| **Bidirectional sync** | **YES — amendment protocol + CI sync monitor** | **NO** (one-way spec → code) | **NO** | **NO** | **NO** |
| **Reference prototype** | **YES — Session 1 winner on sandbox URL (extended 30d TTL)** | **NO** (spec is sole SoT) | NO (some Hooks but not prototype) | **NO** | NO (agent simulations) |
| **Quality gate for spec itself** | **YES — ≥ 80/100 score before hand-off** | NO | NO | NO | NO |
| **Audit trail (decision log)** | **YES — AI Act čl. 14 + DORA 7y native** | NO | partial (tasks tracked) | partial (archive) | NO |
| **AI Act compliance** | **YES — Fáze C signed by DPO** | NO | NO | NO | NO |
| **DORA compliance** | **YES — Article 28 register entry + retention** | NO | NO | NO | NO |
| **WCAG 2.2 AA mandatory** | **YES — checklist + axe-core CI** | NO | NO | NO | NO |
| **STRIDE threat model** | **YES — one-pager + CI security checks** | NO | NO | NO | NO |
| **Anti-drift CI checks** | Spectral + Schemathesis + Pact + oasdiff + nightly sync | optional `/analyze` (Spec Kit) | optional Hooks | optional | unclear |
| **Spec expiry / freshness** | **30-day spec expiry without dev hand-off start** | NO mechanism | NO | NO | NO |
| **Hand-off ritual** | **5-stage (walkthrough + Q&A + amendment + milestone + T+30 embedded reviewer)** | NO ritual | NO ritual | NO ritual | NO ritual |
| **Combined source of truth** | **YES — Spec + Prototype + Decision log + Tests = 4 anchors** | spec only | spec only | spec only | spec only |
| **Re-implementation gap risk** | **medium** (better than SDD but exists) | **high** (9.8-42.1 %) | **high** | **high** | **high** |
| **Time-to-ship vs Pflanzer default** | **+50-100 %** (still 2× faster than SDD) | **10× slower than iterative prompting (Scott Logic)** | unclear | slower than Instructions.md (Incomplete Developer) | unclear |

**Note:** *Track S is the degraded Pflanzer mode.* Pflanzer default (Track A
artefakt = produkt) eliminates re-impl gap completely (kód jde do prod sám,
dev tým byl v room). Track S re-introduces a smaller gap because spec is
intermediary.

---

## 5. Track S hand-off ritual — 5 stages

Per user requirement: *„dev tým není v room, ale specka jde k nim — jaký
je ritual aby spec neztroskotala v rumu emailů?"*

### 5.1 Stage 1 — Spec walkthrough meeting (90 min, sync)

**Kdo:** PM + Decider + Spec authors (Session 1+2 team representatives:
1 BE, 1 FE, 1 PM, Security/DPO if compliance-heavy) + Dev team lead +
Dev team 2-3 senior engineers + EM of dev team.

**Agenda (90 min):**

```
00:00-00:10  Welcome + context (PM)
              - Why Pflanzer was used
              - Why Track S (dev tým wasn't in room — explicit reason)
              - Charter version + sign-off package overview
00:10-00:30  Walkthrough sekce A (Functional spec) — PM leads
              - 3-5 key user stories, including the negative scenarios
              - Reference prototype demo on sandbox URL (live click-through)
00:30-00:50  Walkthrough sekce B (Technical) — BE+FE leads
              - OpenAPI top endpoints
              - Architecture diagram (Mermaid)
              - Tech stack constraints (MUST/MAY/MUST NOT)
00:50-01:05  Walkthrough sekce C (Quality) — Security + QA + A11y
              - STRIDE one-pager
              - Acceptance Gherkin overview
              - WCAG 2.2 AA mandatory criteria
01:05-01:20  Dev tým Q&A (no answers yet — questions captured)
01:20-01:30  Next steps:
              - Q&A window opens (5 prac. dní, async)
              - Amendment protocol explained
              - First milestone date locked
```

**Output:** zápis (Pflanzer hub artifact), recording, FAQ inbox open.

### 5.2 Stage 2 — Q&A window (5 prac. dní async)

**Kdo:** Dev team (everyone, NE jen lead) klade otázky; Spec authors
(rotující per role) odpovídají do 24h max.

**Channel:**
- Pflanzer hub Q&A thread (NE Slack, NE email — auditable, version-controlled)
- Each question → answer → potentially → amendment proposal

**Throughput SLA:**
- Otázka raised → spec author response ≤ 24h
- If question = clarification → answer goes into spec patch (PATCH version bump)
- If question = scope dispute → escalation to Decider, who adjudicates ≤ 48h

**Anti-drift:** Q&A thread becomes **part of spec** (frontmatter `q_a_log`
linked). Future dev / auditor reads spec + Q&A log = same context as
original Session 2 team.

### 5.3 Stage 3 — Amendment protocol

**Trigger:** Dev tým objevuje, že spec is wrong, infeasible, or missing.

**Process:**

```
1. Dev tým opens amendment proposal v Pflanzer hub:
   - Title: AMENDMENT-NNN
   - Section affected: A.1 / B.3 / C.4 / ...
   - Proposed change: <diff>
   - Rationale: <why current spec doesn't work>
   - Impact: <scope / timeline / cost>

2. Spec authors review (within 3 prac. dní):
   - Approve: merge into spec, bump MINOR version, propagate to CI
   - Reject: rationale why; if dev tým disagrees, escalate to Decider
   - Need-Decider: cross-fn change (e.g., adding scope) → Decider adjudicates

3. Decider call (within 48h of escalation):
   - Approve: spec MAJOR version bump, all 11 roles re-sign affected sections
   - Reject: dev tým proceeds per original spec
   - Defer: amendment becomes ADR „Decision-NNNN-deferred-to-v2"

4. Amendment ledger:
   - All amendments logged in spec frontmatter `amendments` array
   - Per AI Act čl. 14: who proposed, who approved, when, why
```

**SLA:** From proposal to decision **≤ 5 prac. dní**. If breached
(Decider unavailable), amendment auto-escalates to Decider deputy
(per `method-charter.md` Decider Sunset). **No silent ignores.**

### 5.4 Stage 4 — First implementation milestone review

**Trigger:** Dev tým ships first slice (1-2 user stories, e.g., happy
path login without refresh logic) to staging.

**Format:**
- Dev tým demos first slice (30 min)
- Spec authors verify against:
  - Gherkin scenarios pass v staging CI
  - Reference prototype UX matches (side-by-side click-through)
  - OpenAPI conforms (Schemathesis pass on staging)
  - STRIDE mitigations implemented (security spot-check)

**Verdict:**
- ✅ **Aligned:** dev tým proceeds; lock first milestone
- ⚠️ **Drift detected:** open amendment OR dev tým re-implements affected
  slice OR spec patch issued
- ❌ **Misaligned:** escalate to Decider; potentially Spec re-issue +
  re-sign-off

**Anti-drift mechanism:** **First milestone review IS the early-warning
system** against drift compounding. Per `01-sdd-mechanika.md` § 2 lost-
context cost table — Round 2 drift is 10-30 %, Round 4+ is 35-60 %.
First milestone catches drift at ≤ 15 % (Round 1) — recoverable.

### 5.5 Stage 5 — Continuous embedded reviewer (T+30 shadow sprint)

**Trigger:** Dev tým enters mid-implementation (week 3-4 of typical
6-week build).

**Format:**
- 1 spec author (rotating) shadows dev tým sprint at T+30 mark
  (1-2 days, sit in stand-ups, observe code reviews, attend sprint
  planning)
- **Mandate:** detect drift early, not police compliance
- Reports back to spec authors team:
  - What's working
  - What's drifting (with proposed amendments)
  - What's been informally amended already (formalize via § 5.3)

**Deliverable:** T+30 shadow report (1-2 page markdown, in Pflanzer
hub), with optional Decider escalation if material drift.

**Anti-drift:** Embedded reviewer is **NOT** auditor, NOT spec police.
Role = continuous knowledge bridge. Without it, T+30 → T+60 is when
spec ↔ code gap balloons to 35 %+ per Round 4 lost-context table.

---

## 6. Quality gates pro spec samotnou

Per § 1.E.4 outlined. **Repeated here as final acceptance gate:**

| Phase | Quality gate | Score required | Action if failed |
|---|---|---|---|
| **Spec draft** (in Session 2) | Self-check ≥ 60 | Spec authors continue, but flag for Day 1 review |
| **RC v1.0** (sign-off start, Day 1) | Score ≥ 70 | Open known-issue tickets per role |
| **v1.0 final** (sign-off complete, Day 5 EOD) | Score ≥ 80 | **Hand-off ritual go** |
| **Post-hand-off** (Stage 1-5) | Continuous (amendments) | Each MAJOR amendment re-validates score ≥ 80 |

**Below 80 = re-work** (specific sections per dim with < threshold).
Spec leaving hub with score 65 = setup for SDD-style failure mode.

---

## 7. Honest assessment — Track S re-implementation gap risk

**Per user clarification: „Pflanzer Track S MUSÍ být dramatically lepší
než Spec Kit / Kiro / OpenSpec / BMAD."**

Track S **redukuje** re-impl gap (compared to SDD), but **does not
eliminate** it. Honest framing:

| Mode | Re-impl gap | Mechanism |
|---|---|---|
| Pflanzer default (Track A) | **~0 %** | Kód z room jde do prod. Dev tým byl v Session 1+2. |
| **Pflanzer Track S** | **~5-15 %** | Spec + reference prototype + executable tests redukuje, ne eliminuje. |
| SDD Spec Kit | 9.8-42.1 % (Yan et al. 2025) | Spec → impl one-way; spec drift inherent. |
| SDD Kiro | similar range | Same one-way flow + EARS overhead. |
| SDD OpenSpec | similar range | Lightweight = less validation = same drift. |
| SDD BMAD | unclear | Multi-agent; no human gate. |

**Why Track S is dramatically better than SDD:**

1. **Reference prototype** as concrete SoT (no other framework has this)
2. **Executable Gherkin** as CI gate (Spec Kit aspirational, Track S
   mandatory)
3. **Cross-fn sign-off** with veto rights (no other has 11-role gate)
4. **AI Act/DORA native** (no other framework)
5. **Amendment protocol** with SLA (Tessl only addresses, private beta)
6. **5-stage handoff ritual** (no other framework)
7. **Spec expiry** (Augment Code identifies problem, no other solves)
8. **Quality gate ≥ 80** for spec itself (no other framework)

**Why Track S is not Pflanzer default:**

Per `glossary.md`: *„Pflanzer artefakt JE running production code."*
Track S re-introduces spec as intermediary; that's why it's fallback,
not default. **Track S = degradovaný default, ne první volba.**

When users ask *„what if dev team can't be in room?"* — first answer:
*„Try harder to put them in room — that's the actual differentiation.
If impossible, Track S exists, but you're trading 5-15 % re-impl gap
for that organizational convenience."*

---

## 8. Reference (URLs + datum přístupu 2026-05-28)

### SDD failure mode primary sources

- **Scott Logic — Putting Spec Kit Through Its Paces** (26/11/2025) —
  [blog.scottlogic.com](https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html)
- **Martin Fowler / Birgitta Böckeler — Understanding SDD** (11/2025) —
  [martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- **Incomplete Developer — OpenSpec Failed My Experiment** (2026) —
  [dev.to](https://dev.to/incomplete_developer/openspec-spec-driven-development-failed-my-experiment-instructionsmd-was-simpler-and-faster-3a5d)
- **Augment Code — What Is SDD?** (2026) —
  [augmentcode.com](https://www.augmentcode.com/guides/what-is-spec-driven-development)
- **Augment Code — Living Specs** (2026) —
  [augmentcode.com](https://www.augmentcode.com/guides/living-specs-for-ai-agent-development)
- **Augment Code — 2026 EU AI Act and AI-Generated Code** —
  [augmentcode.com](https://www.augmentcode.com/guides/eu-ai-act-2026)

### Anti-drift mechanisms primary sources

- **apitect — Stopping Schema Drift** (2026) —
  [apitect.com](https://apitect.com/blogs/stopping-schema-drift-how-to-keep-your-openapi-spec-and-code-in-sync-automatically)
- **Pactflow — Schema-Based Contract Testing** —
  [pactflow.io](https://pactflow.io/blog/contract-testing-using-json-schemas-and-open-api-part-3/)
- **InstaTunnel — Automated Contract Testing: Detect API Drift Before Production** (04/2026) —
  [medium.com](https://medium.com/@instatunnel/automated-contract-testing-how-to-detect-api-drift-before-it-reaches-production-6c2a77baa2a3)
- **flarecanary — API Schema Drift Detection Tools Compared** (2026) —
  [dev.to](https://dev.to/flarecanary/api-schema-drift-detection-tools-compared-2026-1ib4)
- **totalshiftleft — What Is API Contract Testing?** (2026) —
  [totalshiftleft.ai](https://totalshiftleft.ai/blog/what-is-api-contract-testing)
- **Schemathesis docs** (2026) —
  [schemathesis.readthedocs.io](https://schemathesis.readthedocs.io/)

### Gherkin / BDD primary sources

- **Automation Panda — BDD Gherkin Guidelines for AI Coding and Testing** (04/2026) —
  [automationpanda.com](https://automationpanda.com/2026/04/27/bdd-gherkin-guidelines-for-ai-coding-and-testing/)
- **TestQuality — Mastering Gherkin BDD Tools** —
  [testquality.com](https://testquality.com/mastering-gherkin-bdd-tools-a-complete-guide-to-behavior-driven-development-testing/)
- **TestQuality — Complete Guide to Gherkin Syntax** —
  [testquality.com](https://testquality.com/complete-guide-to-gherkin-syntax-for-bdd-testing/)
- **Apidog — Gherkin Guide for BDD and API Testing** —
  [apidog.com](https://apidog.com/blog/gherkin-guide-bdd-api-testing/)

### INVEST / User stories primary sources

- **Wikipedia — INVEST (mnemonic)** —
  [en.wikipedia.org](https://en.wikipedia.org/wiki/INVEST_(mnemonic))
- **leanwisdom — INVEST Criteria for User Stories in SAFe** (2026) —
  [leanwisdom.com](https://www.leanwisdom.com/blog/crafting-high-quality-user-stories-with-the-invest-criteria-in-safe/)
- **Lucassen et al. (2016) — Quality User Story Framework** —
  [Springer](https://link.springer.com/article/10.1007/s00766-016-0250-x)

### STRIDE threat modeling

- **Stellar Docs — STRIDE Threat Model Template** —
  [developers.stellar.org](https://developers.stellar.org/docs/build/security-docs/threat-modeling/STRIDE-template)
- **Jit — STRIDE Threat Model Complete Guide** —
  [jit.io](https://www.jit.io/resources/app-security/stride-threat-model-a-complete-guide)
- **AquilaX — Threat Modeling with STRIDE: Developer Guide** —
  [aquilax.ai](https://aquilax.ai/blog/threat-modeling-stride-guide)

### WCAG 2.2 / EAA / Accessibility

- **Level Access — WCAG 2.2 Checklist 2026** —
  [levelaccess.com](https://www.levelaccess.com/blog/wcag-2-2-aa-summary-and-checklist-for-website-owners/)
- **Level Access — European Accessibility Act (EAA) Compliance Guide** —
  [levelaccess.com](https://www.levelaccess.com/compliance-overview/european-accessibility-act-eaa/)
- **inclly — WCAG 2.2 AA Checklist Complete 50-Criteria Guide 2026** —
  [inclly.com](https://inclly.com/resources/wcag-22-checklist)
- **W3C — WCAG 2 Overview** —
  [w3.org](https://www.w3.org/WAI/standards-guidelines/wcag/)

### AI Act / DPIA / DORA

- **McKenna Consultants — EU AI Act High-Risk Compliance Technical Readiness** —
  [mckennaconsultants.com](https://www.mckennaconsultants.com/eu-ai-act-high-risk-compliance-a-technical-readiness-guide-for-august-2026/)
- **Knowlee — AI Audit Trail Implementation Guide for Article 12** —
  [knowlee.ai](https://www.knowlee.ai/blog/ai-audit-trail-implementation-guide)
- **GDPR.eu — DPIA Template** —
  [gdpr.eu](https://gdpr.eu/data-protection-impact-assessment-template/)
- **TrustArc — GDPR Article 35 DPIA Cheat Sheet** —
  [trustarc.com](https://trustarc.com/resource/data-protection-impact-assessment-article35/)
- **IAPP — What triggers a DPIA under the GDPR** —
  [iapp.org](https://iapp.org/resources/article/what-triggers-a-dpia-under-the-gdpr)
- **agentmodeai — AI DPIA template (GDPR Art. 35 + EU AI Act Art. 26)** —
  [agentmodeai.com](https://agentmodeai.com/resources/ai-dpia-template/)
- **DORA Article 28** —
  [digital-operational-resilience-act.com](https://www.digital-operational-resilience-act.com/Article_28.html)
- **Springlex — DORA ITS RoI Article 3** —
  [springlex.eu](https://www.springlex.eu/en/packages/dora/its-roi-regulation/article-3/)

### ADR / Spec versioning

- **MADR — Markdown Architectural Decision Records** —
  [github.com/adr/madr](https://github.com/adr/madr)
- **adr.github.io — Architectural Decision Records** —
  [adr.github.io](https://adr.github.io/)
- **Microsoft Azure Well-Architected — ADR** —
  [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record)
- **AWS Prescriptive — ADR process** —
  [docs.aws.amazon.com](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html)
- **Joel Parker Henderson — ADR examples repo** —
  [github.com/joelparkerhenderson/architecture-decision-record](https://github.com/joelparkerhenderson/architecture-decision-record)

### Mermaid / C4

- **Mermaid — C4 Diagrams syntax** —
  [mermaid.js.org](https://mermaid.js.org/syntax/c4.html)
- **Mermaid Studio — C4 Diagram support** —
  [mermaidstudio.dev](https://mermaidstudio.dev/docs/diagram-types/c4/)
- **softaworks — C4 Architecture skill** —
  [github.com/softaworks/agent-toolkit](https://github.com/softaworks/agent-toolkit/blob/main/skills/c4-architecture/README.md)

### Specification grounding

- **Unstract — Specification Grounding: The Missing Link in Vibe Coding** —
  [unstract.com](https://unstract.com/blog/specification-grounding-vibe-coding/)
- **Spec Kit Agents (arXiv 2604.05278)** —
  [arxiv.org](https://arxiv.org/html/2604.05278v1)
- **Evaluation-Driven Development of LLM Agents (arXiv 2411.13768)** —
  [arxiv.org](https://arxiv.org/pdf/2411.13768)

### Pflanzer internal cross-refs

- `docs/methodology/00-tldr.md` (management 1-pager, ne re-implementation)
- `docs/methodology/07-handoff-do-vyvoje.md` (sign-off package — Track S
  staví na téhle existující struktuře)
- `docs/methodology/glossary.md` (artefakt = produkt; deprecated terms)
- `docs/methodology/method-charter.md` (Charter version pin, AI Act Fáze
  C signature)
- `docs/research/spec-driven-vs-pflanzer/01-sdd-mechanika.md` (SDD failure
  modes, anti-pattern catalog)
- `docs/research/spec-driven-vs-pflanzer/02-friction-quantification.md`
  (PD comparison, Boehm cost-of-defect)
- `tool/templates/precision-spec-track-s.md.template` (markdown template)

---

## 9. Open questions / decision flags

| Topic | Status | Owner | Due |
|---|---|---|---|
| Sandbox URL TTL extension to 30 days for Track S | Proposed (§ 2.4) | Platform + Security | Pre-pilot ADR |
| Q&A window 5 prac. dní — too short for global teams? | Open (§ 5.2) | EM Pflanzer + Champion | Test in 2 piloty |
| Embedded reviewer T+30 capacity commit (1-2 days) — who pays? | Open (§ 5.5) | EM source team | Pre-Charter signature |
| Spec quality gate 80/100 — calibration in 3 piloty | Open (§ 6) | Method Steward | T+6 mo method report |
| Amendment protocol SLA 5 prac. dní — vs Pflanzer 14-day cyklus | Open (§ 5.3) | Decider + Method Steward | First Track S pilot |
| Track S re-impl gap empirical measurement | Open (§ 7) | Method Steward + Data | After N=3 Track S piloty |

---

**Spec engineering is a discipline. Track S spec is dramatically lepší
than SDD by design — but Pflanzer default (artefakt = produkt) is even
better. Choose Track S only when room composition fails, not as
preference.**
