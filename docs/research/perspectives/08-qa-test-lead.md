# 08 — QA Lead / Test Engineering Manager

## Kdo jsem

QA Lead v korporátu, tým 8 (5 manual / 3 automation), 10+ let. Žiju test
pyramidou (70/20/10), Pactem a exploratory chartery místo skriptovaných
regresí. AI-generated kód poznám podle toho, že happy path běží a první
null/timeout ho rozsype. Pflanzer mě láká — stakeholdeři v jedné
místnosti je sen — i děsí: prototype-to-prod bez QA gate je vzor, který
v produkci hoří.

## 1. Kde metoda funguje

- **„Together alone" sníží defekt rate v zadání.** 70 % bugů není kód,
  ale špatně pochopený požadavek. Security + backend v místnosti od
  minuty 0 = akceptační kritéria hned testovatelná, ne přepisovaná
  v sprint reviewu.
- **Funkční mockup > Figma fasáda** pro testovatelnost. Reálné flows
  a BDD scénáře nad nimi hned, ne po dev handoffu.
- **Score závaznosti per oddělení** = elegantní vstup pro risk-based
  test prioritization.
- **AI-mediovaná syntéza v session 2** odstraňuje politiku z
  post-mortemu připomínek. Bez moderace je to HiPPO show.

## 2. Co metoda láme

- **„Happy path only" vibe-coding.** Bolt, Lovable, v0 default produkují
  šťastnou cestu. Empty states, error handling, network failure, race
  conditions — v session 1 nevznikne. Stakeholder odejde s pocitem, že
  „to funguje", protože klikal demo data.
- **Testovatelnost jako afterthought.** Katalog má QA „doporučenou pro
  release-grade fíčury". Špatně — testovatelnost (architektura, SoC,
  deterministická data, observability hooks) se rozhoduje v session 1.
- **Prototype-to-prod transition nedefinovaná.** Metoda končí
  „handoffem". To je bod, kde prototypy umírají — vibe-kód nemá testy,
  contracts ani observability. Kdo to píše, z jakého rozpočtu?
- **Regrese skrytá pod novou fíčurou.** Pro brownfield projekt session
  1 ignoruje impact na současné flows. Bez regression inventory tým
  slíbí věc, která rozbije 3 jiné.
- **AI blind spots.** Kód s closures přes private state, magic strings,
  globální state — netestovatelný. Bez code-level reviewu v session 1
  to nikdo nezachytí.

## 3. Co přidat / vylepšit

### 3.1 QA do session 1 jako povinná pro vše s release intentem

Trigger „<1 měsíc do produkce" je pozdě. Reálný trigger: **kdokoliv
v místnosti řekl `produkce` nebo `pilot s reálnými uživateli`**. Pak
QA povinná. Pro pure exploration (throwaway sandbox) volitelná.

### 3.2 BDD/Gherkin akceptace jako session 1 výstup

Vedle 1–3 mockupů povinně **3–5 Gherkin scénářů per preferovaná
varianta**:

```gherkin
Feature: <capability>
  Scenario: <happy path>
    Given <stav + data> When <akce> Then <observable outcome>
  Scenario: <empty state>
  Scenario: <error / timeout / 4xx / 5xx>
  Scenario: <permission / auth boundary>
```

**Min. 1 ne-happy scénář per varianta**, jinak session 1 nekončí.
Největší dluh AI-prototypů, neudělá se sám.

### 3.3 Test pyramide split rozhodnut v session 1

| Vrstva | Cíl | Kdo | Kdy |
|---|---|---|---|
| Unit | 70 % branch | dev | 1. sprint |
| Integration + Pact | klíč. endpointy | dev + QA | 1. sprint |
| E2E | 3–5 happy + 2–3 neg. | QA auto | 2. sprint |
| Exploratory | per release | QA manual | průběžně |

Bez splitu metoda generuje technický dluh maskovaný jako MVP.

### 3.4 Contract testing input z session 1

Pokud prototyp volá nebo definuje API, **OpenAPI/GraphQL draft** je
session 1 artefakt vedle mockupů. QA z toho generuje Pact konzumentské
testy. Bez contractu je integration handoff hádanka pro 3 týdny.

### 3.5 Exploratory charter pro mezi-session období

Mezi session 1 a 2 vedle klikacího prototypu i QA charter (90 min):

```
CHARTER
Mission: Explore <variant X> with <persona Y>
         to discover <risk class Z> using <dataset W>.
Areas: empty states, error paths, perf, a11y, auth bypass.
Out-of-scope: <explicitly>
Deliverable: bug list + risk notes + testability findings
```

Session 2 pak má **risk findings s vlastním score** (blocker / major /
minor / info).

### 3.6 Prototype-to-prod gate (P2P checklist)

Mezi „final" a „handoff" povinný gate:

- [ ] Gherkin akceptace (≥1 negative per scénář)
- [ ] Pyramide split + vlastník per vrstva
- [ ] API contract + Pact testy zadané
- [ ] Regression impact analysis
- [ ] Observability v DoD
- [ ] Synthetic data sada
- [ ] Security sign-off (role 7)
- [ ] A11y baseline (public-facing)
- [ ] DoD schválená QA + dev + PdM

Bez checklistu není handoff. Single biggest gap metody.

### 3.7 AI proxy QA — risky default

LLM generuje testy, které **testují implementaci, ne chování** (mock
všeho, test projde i když produkční kód padá). AI proxy ano, ale
**lidský review na každý generovaný scénář je povinný** před CI. Jinak
500 testů, false sense of safety, žádná reálná pojistka.

## 4. Korporátní reálie

- **DORA čl. 24** — TLPT a ICT testing povinné. Happy-path-only
  prototyp compliance neprojde.
- **WCAG 2.2 AA / EAA** — public-facing = legal requirement. Patří do
  P2P gate.
- **Audit trail 3–5 let** pro každou scored připomínku. Otter/Read
  transkript je vstup, ne dostatečný artefakt.

## 5. Doporučení pro pilot

1. **Sanity pilot:** 1 projekt s nízkým release rizikem (interní
   tooling), QA u stolu od session 1, P2P checklist enforcován.
2. **Měřit:** defect leakage vs baseline, coverage po 2 sprintech,
   time-to-first-Pact-test.
3. **Risk gate:** pokud defect leakage > baseline, QA veto pro
   production-bound projekty, dokud P2P checklist nedoladíme.
4. **Champion v QA komunitě.** Senior QA jako spoluautor — jinak
   metoda regaluje ke „QA picks up the mess" anti-patternu.

## 6. Adjacent praxe

- **Atlassian Pre-Mortem** v session 1 (15 min): „za 3 měsíce hořelo —
  proč?" Generuje negative test cases, které vibe-coding ignoruje.
- **TRIZ** jako QA pre-mortem — „co uděláme, aby produkce hořela",
  pak inverze. Lepší než risk register.
- **Continuous Discovery OST (Torres)** pro testabilitu: outcome
  v produkci → measurement plan v P2P checklistu.

## Memorabilia

**Vibe-prototyp je testovatelný právě tehdy, když u něj v session 1
seděl QA a na konci dne odchází s 3–5 Gherkin scénáři, drafted API
contractem a exploratory charterem. Bez toho je to demo, ne MVP — a
demo nepatří do produkce, ať si to v session 2 odsouhlasí kdokoliv.**

Pflanzer zrychlí discovery. Bez P2P checklistu zrychlí i defect
leakage — to není zrychlení, to je dluh s úrokem.
