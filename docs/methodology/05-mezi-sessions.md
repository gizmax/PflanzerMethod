# 05 — Mezi sessions

> Status: v1.0. Scoring window mezi Session 1 a Session 2: prototype hub
> s 1–3 variantami, strukturovaný feedback per oddělení, async triage update,
> Discovery Debt Detector audit. Délka **5–7 pracovních dní** [perspektiva 03].

## Cíl mezi-sessions okna

Zhmotnit Session 1 shortlist do **klikacího prototypu v 1–3 variantách** se
sdíleným rozcestníkem, sebrat **score-based feedback per role × per
varianta**, aktualizovat triage stanoviska a doručit Session 2 rozhodovací
materiál — ne pokračovat v generaci.

## Délka okna

**5–7 pracovních dní** [perspektiva 03]:

- **Den 1–2**: deploy prototypů do sandboxu (max 48 h od konce Session 1).
- **Den 3–5**: scoring window (3 prac. dny pro role).
- **Den 6**: AI syntéza a clustering feedbacku.
- **Den 7**: Decider review a Session 2 prep pack distribuce 24 h předem.

Delší než 7 dní = ztráta kontextu a momentum. Kratší než 5 = role nezvládnou
ohodnotit, zejména async stakeholdeři (Legal, Security, Engineering manager).

## Prototype hub spec

Rozcestník na sdílené URL (sandbox doména + watermark + noindex), bez
accountu, bez prod credentials.

**Povinný obsah:**

- **Hero rozcestník** s 1–3 variantami, každá karta:
  - Embed link (sandbox URL).
  - **Version diff popis** vůči ostatním variantám: 3–5 odrážek
    (UX flow, datový model, performance trade-off, A11y stav, security stance).
  - OST tag + JTBD card mapping [perspektiva 14].
  - T-shirt size od EM + draft effort estimate.
  - Throw-away/evolve flag (default = throw-away).
- **Sandbox URL** s 24h TTL refreshovaným do konce scoring windowu;
  audit logging do SIEM, žádný route do prod sítě [perspektiva 07].
- **OpenAPI 3.1 draft** per varianta + breaking-change registr.
- **Token compliance report** + DS deviation list.
- **A11y quickscan report** (axe-core) + Critical/Serious flag.
- **Ticket prediction worksheet** per varianta.
- **Deploy footprint estimate** (TCO sheet).
- **Risk register** + veto registr ze Session 1.
- **AI Act Fáze B — Interim review** (dvoufázový protokol v0.3, Útok 4):
  DPO znovu klasifikuje risk-tier proti **konkrétnímu** variantu (data flow,
  downstream decision, intended user) — ne proti Charteru. Output:
  ratified tier + delta vs Fáze A. Pokud upgrade (např. Limited → High-risk),
  Session 2 dostává **mandatory Conflict bod** pro Decider's call.
  Fáze C (final) se podepisuje až v Session 2 / handoff.
- **Decision log Session 1** s lidskou atribucí.
- **Acceptance criteria seed** (Gherkin, ≥ 1 negative scenario per varianta).
- **Feedback formulář link** (viz níže).

**Sandbox guardrails** [perspektiva 07]:
- Vlastní VPC, default-deny network, watermark + noindex.
- Žádné prod credentials, žádný route do prod sítě.
- 24h TTL refresh, audit log retention 7 let pro regulované projekty.
- Approved AI tool only (Claude Enterprise / Cursor Business / v0 Team
  / Bolt Pro s DPA).

## Feedback formulář — scoring schema

Strukturovaný formulář, ne free-text mailem. Generuje se per varianta
× per role; AI co-pilot agreguje a klasifikuje.

### Povinná pole

| Pole | Typ | Pravidla |
|------|-----|----------|
| Role | enum | Z role catalogu (1–17) |
| Hodnotitel | SSO ID | Auditovatelná atribuce, ne anonym |
| Varianta | enum | A / B / C |
| Severity | enum | **Critical** (blocker) / **Serious** (high) / **Yellow flag** (warning) / **Nit** (low) |
| Department | enum | Z role taxonomie |
| Kategorie | enum | UX / A11y / Security / Legal / Performance / Data / Effort / Other |
| **Score závaznosti** | **0–1 float** | 0 = ignorovat / 0.25 / 0.5 / 0.75 / 1 = blocker. **AI-only persona feedback max 0.5** [synthesis 02] |
| **Rationale** | text | **Povinný field**. Bez rationale score neplatí [perspektiva 02] |
| Mitigation návrh | text | Volitelný; pokud Critical, povinný |
| AI-assisted? | bool | Označit, pokud feedback generoval AI proxy |
| Evidence link | URL | Volitelné: ticket ID, transcript citace, persona note, axe-core run |

### Severity × department × kategorie matrix

[baseline 03 + perspektivy 11, 10]:

- **Security STRIDE Critical** → blocker, session pivotuje.
- **Legal AI Act high-risk + bez DPIA** → blocker.
- **A11y WCAG Critical / Serious na public-facing** → blocker [perspektiva 11].
- **EM capacity overrun** → blocker s eskalací.
- **BE breaking change bez consumer alignment** → blocker s registrem.
- **UX usability debt** → Yellow flag (warning, ne veto).
- **QA testability concern** → Yellow flag.
- **CS load increase** → Yellow flag, požaduje predikci ticket volume.

### WCAG dimenze

WCAG Critical / Serious (axe-core severity) = blokující váha 1.0 v score
závaznosti, bez ohledu na ostatní hodnocení. Public-facing + B2B nad
250 zaměstnanců default-on, EAA platí od 28. 6. 2025 [perspektiva 11].

### AI Act risk tier dimenze

[perspektiva 10]:
- **Unacceptable** → varianta vyřazena, ne hlasování.
- **High-risk** → DPIA povinný + Annex IV tech doc + human oversight per
  čl. 14. Score nemůže být > 0.5 bez kompletního paketu.
- **Limited risk** → transparency povinnosti, score normální.
- **Minimal** → score normální.

### Anti-pattern: politické skóre

Pokud oddělení dá nízký score, aby se zbavilo práce, AI co-pilot flaguje
**pattern „chronický blocker"** [perspektiva 02]. Facilitátor tento pattern
prezentuje v Session 2 jako samostatný bod.

## Async triage update

Tři triage tracks z Kroku 0a (`03-pre-session-priprava.md`) **aktualizují
stanovisko** v scoring window:

### Security & Data Triage update

- Re-classify data flow per varianta (pokud se změnil).
- STRIDE one-pager update + nové mitigation needs.
- SBOM scan, license scan, CVE scan, secret scan na každém prototypu.
- Approved AI tool list compliance check (žádný shadow tool nepoužit).
- Veto registr finalizace.

### Legal & Privacy Triage update

- AI Act tier potvrzení per varianta.
- DPIA lite finalizace (pokud trigger).
- Privacy Notice draft per varianta.
- Vendor risk register update.
- Marketing claim review (UCPD + ePrivacy).

### Platform Triage update

- Deploy footprint estimate finalize per varianta.
- SLO baseline draft + runbook stub.
- Observability contract check (OTel + structured logs + tracing).
- P2P (Prototype-to-Prod) gate checklist update.

**Termín**: triage updates do hub repo nejpozději **Den 5** scoring windowu.
Bez nich se Session 2 nesvolá.

## Discovery debt detector — průběžný audit

AI co-pilot skill běží **na každém feedback batch** [perspektiva 14]:

- Kolik tvrzení o uživateli ve feedbacku má zdroj (research artefakt, citace
  transcriptu, ticket ID) vs. assumption-stated-as-fact?
- Kolik feedback bodů je AI-only (bez human sign-off)?
- Existuje OST node pro každý feedback bod?
- Skóre 0–10 s rozhraním:
  - **≤ 2** = OK, Session 2 pokračuje.
  - **3–6** = WARNING, závaznost session 2 výstupů omezena na *exploratory*;
    no full handoff bez additional discovery.
  - **≥ 7** = STOP, předřaď discovery sprint, Session 2 odložena.

## Eskalační protokol

### Kdy svolat Session 2 dřív (před plánovaným D7)

- Všichni účastníci dali score do D3 (kapacita využita).
- Decider potřebuje go-decision pro PI planning gate (kalendářní hard
  deadline).
- **Zero Critical** ve veto registru a **≥ 80 % role coverage** ve scoring.

### Kdy odložit Session 2

- **Kterákoli role flagne Critical** bez mitigation návrhu — session 2
  posunuta o 3–5 dní pro mitigation work [synthesis 01].
- **Triage update** přinesl nový high-risk finding (Security STRIDE
  Critical, Legal AI Act high-risk bez DPIA, A11y WCAG Critical).
- **Discovery Debt Detector ≥ 7** — discovery sprint se předřazuje.
- **Decider nedostupný** — session se posunuje, ne probíhá bez něj
  [perspektiva 01].
- **EM kapacita zmizela** — aktivuje se champion alternativa v jiné BU
  [synthesis 01], nebo se projekt přesouvá do IP iteration.

### Kdy ukončit projekt mezi sessions (kill bez Session 2)

- **L4 data leak** v sandboxu (incident response playbook, ne Session 2).
- **Discovery Debt Detector ≥ 7 + Decider odmítá discovery sprint**
  (problem-fit chybí, alignment je theatre).
- **Capacity buffer < 0** napříč celým PI a žádný champion není dostupný.
- **Kill criteria z Charteru splněny** (např. NPS shift threshold prolomen).

## Výstupy mezi-sessions (vstup do Session 2)

Doručené Decider + všem rolím **24 h před Session 2**:

- **Score-based feedback aggregate** per role × per varianta + commitment
  level mapping.
- **Triage updates** (Security, Legal, Platform) finalizované.
- **Discovery Debt Detector** report.
- **Veto registr** finalizovaný.
- **Top 3 sporné body** připravené pro conflict-resolution playbook
  v Session 2.
- **Decider's pre-read shortlist** — který směr Decider preferuje vs.
  co říká panel.
- **Updated risk register** + mitigation deadlines.
- **P2P gate checklist** stav per varianta (kompletní / blocker / N/A).
