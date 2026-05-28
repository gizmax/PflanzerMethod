# 04 — Session 1

> Status: v1.0. Generativní session: cross-functional alignment, 1–3 funkční
> mockupy, preference matrix, score závaznosti per role, Decider's go/no-go
> shortlist. Délka 5–6 h, konec **16:00** (ne 17:30) [perspektiva 03].

## Cíl Session 1

Vyrobit **1–3 funkční mockupy** anotované na konkrétní node v OST, doplněné
preference matrixem (4 dimenze × role) a Decider's go/no-go shortlistem
pro mezi-session iteraci. Varianty nejsou Figma fasáda — jsou
**runnable produkční-ready apps** na sandbox URL, reviewable celým týmem
včetně programátora (který je v room od minuty 0). Session produkuje
**3 paralelní produkční-ready varianty + alignovaný shortlist** pro
mezi-session scoring window.

## Energy curve a délka

Kreativní špička je 45–90 minut, druhá vlna po obědě max 60 minut, pak je
tým v Slacku [perspektiva 03]. Proto:

- **Délka 5–6 h**, ne 8 h. Konec v 16:00, tým musí mít rezervu.
- **Break každých 90 min nediskutuju**, pulsní check-in (1–5 prst) každé 2 h.
- **Mezi-session okno: 5–7 pracovních dní** (ne 14, ne 3).
- AI nese execution-heavy zátěž (mockup generation, transcript summary,
  clustering) v okamžicích, kdy lidská energie klesá.

Anti-pattern: *„uděláme to celé za 1 den"*. Den bez prototypu mezi
sessions = rozhodli o vibe, ne o realitě.

## Účastníci

Per Decision tree z `02-role-catalog.md` + tato pravidla:

- **Core 4 (vždy)**: Zadavatel/Decider (1), PM (2), Facilitátor (3), AI co-pilot.
- **Per project mix**: FE (4), BE (5), UX (6), Security (7), QA (8) povinně
  pokud release intent, EM (9) pokud > 2 sprinty, Legal (10) pokud osobní
  data nebo AI Act trigger, A11y (11) default-on pro customer-facing,
  Data (12), CS proxy (13), End-user (14) default-on pokud customer-facing,
  DevOps (15) pokud session má sandbox.
- **Champion** (#17 z synthesis 03) — pokud zavádíme metodu v nové BU
  nebo druhý+ pilot. Owner Coaching Kata loop.
- **UX writer** (#16) — pokud user-facing copy / error states.
- **Sanity check**: > 10 lidí v místnosti = scope příliš široký, zúžit
  nebo paralelní sessions [synthesis 02].
- **Senior delegate** povinně pro vetovací role (Security, Legal, EM); junior
  bez mandátu = session se odkládá [perspektiva 01].

## Detailní agenda

| Čas | Blok | Aktivita | Vede |
|-----|------|----------|------|
| 09:00–09:30 | **Voice of Customer ritual** | 5 verbatim citací z ticketů, 1 audio recording, 1 anekdota „nejhorší týden support" | CS proxy |
| 09:30–10:00 | **Charter alignment + JTBD warm-up** | Re-read Charteru 5 min; JTBD lock; OST review; success metric a XYZ hypotéza fixovány | PM + UX (shared) |
| 10:00–10:15 | **Pre-mortem TRIZ** | *„Je 6 měsíců po launchi, fíčura selhala, proč?"* — kondenzát 15 min, generuje rizika dřív, než tým zamiluje variantu [perspektiva 02] | Facilitátor + AI |
| 10:15–10:45 | **Crazy 8s / silent ideation** | 8 minut × 8 sketches per účastník, individuálně. Bez diskuse | Facilitátor |
| 10:45–11:00 | **Break** | Fyzický reset, ne networking [perspektiva 03] | — |
| 11:00–12:30 | **AI vibe-coding kolo 1 — 3 paralelní varianty** | AI builder generuje 3 varianty paralelně z merged Crazy 8s. FE/UX/BE/A11y shadow ve svých kanálech: token compliance, OpenAPI shadow, axe-core run | **AI vede, lidé direction** |
| 12:30–13:00 | **Oběd + parking lot review** | Async; AI klasifikuje parking lot items | — |
| 13:00–13:30 | **A11y quickscan + tech feasibility check** | 8–10 položek WCAG 2.2 AA, axe-core report. BE feasibility: breaking-change check proti existujícím consumer ownerům. EM T-shirt sizing | A11y + BE + EM |
| 13:30–14:00 | **Silent dot voting + preference matrix** | 1-2-4-All. Hlasy SILENT, score se zveřejňuje **až po hlasování**. Zadavatel hlasuje **poslední** [perspektiva 03] | Facilitátor + AI |
| 14:00–14:30 | **Score závaznosti per oddělení** | 1–5 Likert s **rationale field** (povinný). Severity × department × kategorie matrix. AI-only persona feedback **score deflation max 0.5** [synthesis 02] | Per role |
| 14:30–15:00 | **Decider's call: shortlist 1–3 variant** | Decider rozhoduje, které varianty jdou do prototype hubu. Tie-breaker právo, ne consensus. Veto registr přiložen | Decider |
| 15:00–15:30 | **Wrap-up + parking lot + commitments** | Per role: commit level 0–3 pro mezi-session work; akceptační kritéria seed (Gherkin ≥ 1 negative scenario per varianta); P2P (Prototype-to-Prod) gate items per varianta | Facilitátor |
| **15:30–16:00** | **Buffer / overflow** | **Konec v 16:00 nejpozději** | — |

## AI-human dělba aktivit

Tříreřežimová matice ze syntézy [synthesis 02 + perspektiva 03]:

| Aktivita | Vede | Proč |
|----------|------|------|
| Generování mockupů | **AI** | Lidi to neumí dost rychle, AI 3 varianty / 20 min |
| Sumarizace transcriptu | **AI** | Otter / Read v real-time |
| Clustering sticky notes / feedback | **AI** | Šetří 30 min |
| OpenAPI shadow (BE shadow agent) | **AI** | Generuje paralelně s UI generátorem |
| Axe-core a11y audit | **AI** | Static check, 8–10 položek |
| SBOM scan + secret scan + CVE | **AI** | Execution-heavy |
| Discovery Debt Detector audit | **AI** | Tvrzení vs evidence |
| Pre-mortem rizika (1. draft) | **AI**, člověk validuje | AI nemá context blindness |
| Score agregace + rationale extrakce | **AI** | Dataset, ne názor |
| **JTBD framing & persona lock** | **Člověk** (PM + UX) | AI nepozná persona drift |
| **Konflikt mezi rolemi** | **Člověk** (Facilitátor) | AI nemá political authority |
| **Dot voting interpretation** | **Člověk** | „8 hlasů pro A" může být HiPPO |
| **Veto handling** (Security/Legal) | **Člověk** | AI nemá podpis |
| **Commitment moment** | **Člověk** | Závaznost je sociální akt |
| **Energy management** | **Člověk** | AI nepozná unavený tým |
| **Decision log s atribucí** | **Oba** | AI píše, člověk podepisuje (DORA, AI Act čl. 14, GDPR čl. 22) |

**Pravidlo**: AI vede, když je úkol **execution-heavy a context-light**. Člověk
vede, když je **context-heavy a accountability-bearing**.

## Konfliktní situace — playbook

[synthesis 01]. Konflikt nadojmem v 5. minutě výskytu, ne ke konci.

### Security veto vs zadavatel push (#7 × #1)

Pre-charter Data Classification Statement zachytí 80 % case-ů. V místnosti:
silent ranking blockerů → AI agreguje severity (STRIDE Critical/High/
Medium/Low) → **Critical = session pivotuje na alt. variantu**, nepokračuje
v zablokované. **Veto je veto, ne hlas mezi hlasy.** L4 data v promptu
(reálné PII) = okamžité přerušení session, incident response playbook,
72h GDPR notification clock [perspektiva 07].

### HiPPO push (zadavatel přebíjí persony)

Liberating Structures default: **1-2-4-All před diskusí**, dot voting
**silent před verbálním**. Score se zveřejní **až po hlasování**. Zadavatel
hlasuje **poslední**. Pokud Decider chce override silent vote výsledku,
musí to udělat **veřejně s rationale do decision logu** [perspektiva 02].

### Scope creep („když už tu jsme, přidejme…")

Facilitátor + PM mají právo říct **„parking lot"** a vrátit do JTBD.
Časový budget na varianty fixní. Parking lot review pouze v obědním slotu;
items se v session nevrací. Nový item v parking lotu = kandidát pro
**další charter**, ne pro tento.

### EM kapacita vs business timeline (#9 × #1, #2)

T-shirt sizing v session, **NE story pointy** (SP deformuje sociální
tlak). T-shirt > L → **2-day capped spike mimo workshop**, ne odhad
pod tlakem. Přetrvávající konflikt = eskalace mimo místnost
[perspektiva 03, synthesis 01].

### FE rychlost vs BE contract (#4 × #5)

**Contract-first**: BE shadow agent generuje OpenAPI 3.1 paralelně
s UI generátorem, side-by-side. Konflikt se nestává, protože vznikají
současně [synthesis 02]. Breaking-change registr s explicit ownership;
každá UI změna kontrola proti consumer ownerům.

### Pivot gate v 90. minutě

Pokud > 50 % rolí indikuje misalignment problému, session přepíná
z generative na **re-framing** a Session 1.5 se plánuje [perspektiva 01].
Lepší zastavit po 90 minutách, než vyrobit 3 mockupy ke špatnému
problému.

## Výstupy ze Session 1 (do 24 h)

> **Track-aware (v0.4, per ADR-0020):** Výstupy se liší podle Charter track
> designation. Track P (preferred default ~80 %) produkuje **běžící
> produkční-ready varianty**; Track S (fallback ~20 %) produkuje **reference
> prototypy + draft precision specu**.

Artefakty se generují AI co-pilotem v reálném čase a finalizují se v hodinách
po session.

**Společné pro Track P i Track S:**

- **1–3 anotované varianty** s embed link (public preview URL bez accountu)
  + sandbox URL + IaC commit hash. Každá varianta má **OST tag** a **JTBD card
  mapping** [perspektiva 14].
  - **Track P:** varianty = **produkční-ready apps** v target repo, s real
    code (ESLint/Prettier pass, types, Vitest passing).
  - **Track S:** varianty = **reference prototypy** (lightweight, navigation
    aid pro spec authors, ne deployable).
- **Preference matrix** — varianty × dimenze (user value, effort, risk,
  strategic fit) × role. Hlasy per role + commitment level [perspektiva 02].
- **Score závaznosti per role** s rationale field; AI-only persona feedback
  deflated max 0.5 [synthesis 02].
- **Veto registr** — kdo co flagoval, severity, mitigation deadline; podepsaný
  artefakt, ne ústní poznámka [perspektiva 07].
- **Draft OpenAPI 3.1 per varianta** (BE shadow agent) + breaking-change
  registr + ERD diff + 3–5 ADR drafts.
- **Token compliance report** > 90 % + komponentový mapping (reuse / new /
  one-off) + DS deviation list s ownerem.
- **A11y quickscan** (8–10 položek) + axe-core run report. Critical/Serious
  = blocker pro „final" status [perspektiva 11].
- **Akceptační kritéria seed** v Gherkin formátu, ≥ 1 negative scenario
  per varianta + exploratory charter.
- **Ticket prediction worksheet** per varianta (volume/TTR/deflectable/
  VoC match) [synthesis 02].
- **Deploy footprint estimate** (TCO sheet) per varianta + 4 golden signals
  dashboard mockup [synthesis 02].
- **Risk register** — top 5 rizik s ownerem a mitigation deadline.
- **Parking lot** — items pro další charter / další session.
- **Decision log** s lidskou atribucí (DORA, AI Act čl. 14, GDPR čl. 22).
- **Audit log session** — každý prompt, každá AI odpověď, atribuce na
  user @ SSO, retention 7 let pro regulované projekty [perspektiva 07].
- **SBOM** prototypu (`cyclonedx` / `syft`), license scan, CVE scan
  (Trivy/Snyk), secret scan (gitleaks/trufflehog).
- **Throw-away vs evolve flag** explicit per varianta. **Default = evolve**
  per ADR-0005 v0.4 rewrite (Track × Output 2×2 matrix). Throw-away je
  explicit opt-in pro 3 valid use cases.
- **Commitment level 0–3** per role (0 = neúčastnit se mezi-session, 1 =
  read-only feedback, 2 = active scoring, 3 = co-creation varianty).

**Track S only (pokud Charter = Track S):**

- **Draft precision spec sekce A–C** (Functional / Technical / Quality)
  per `tool/templates/precision-spec-track-s.md.template`. Reference
  prototypy z bodu 1 slouží jako navigation aid pro spec authors —
  combined SoT pattern (Spec + Reference Prototype + Decision Log +
  Tests = 4 anchory proti drift, per ADR-0020 anti-drift mechanism #3).
- **5-stage handoff ritual plan** — kdy 90-min walkthrough, kdy 5-day Q&A
  window, kdo embedded reviewer T+30 (per 07-handoff-do-vyvoje.md).

## Failure modes a mitigace

[perspektiva 03]:

- **Captured by tool** (debug Boltu 40 % session) → AI co-pilot v sub-roli,
  fallback builder předem připravený.
- **Captured by HiPPO** → silent voting, decider hlasuje poslední,
  Charter dává facilitátorovi právo „zadavateli, podržte slovo".
- **Conflict avoidance** → konflikt nadojmem v 5. minutě výskytu.
- **Energy blindness** → break každých 90 min, pulsní check-in (1–5 prst)
  každé 2 h.
- **AI as authority** → každý AI insight má human override; decision log
  atribuuje **člověka**, ne „AI navrhla".
- **Charter creep** → MoSCoW na vstupy striktní; pokud chybí MUST, session
  se odkládá.
