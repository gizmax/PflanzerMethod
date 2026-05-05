# 02 — Key themes

> Synthesis output: co se napříč 15 perspektivami panelu opakuje, kde má
> metoda v0 strukturální díry, jaké artefakty panel požaduje, jak upravit
> role catalog, MoSCoW priority na vstupy a top 10 ostrých takeaways.

## 1. Co se opakuje (≥5 perspektiv)

1. **Metoda nemá Business / Product / Discovery layer před řešením.**
   Pflanzer v0 startuje generací mockupů, ne validací problému (perspektivy
   1, 2, 6, 12, 14). Bez business case, JTBD, OST a success metric vyrobí
   „nejlépe sladěnou black-box organizaci v korporátu" (12). Pojmenováno
   také v 8 a 13 (testovatelnost a support readiness se rozhoduje v session 1).

2. **Throw-away vs evolve kontrakt absentuje.** „Production by stealth"
   (4), „vibe-deployed prototype" (5), „shadow-IT" (15), „prototype do prod
   bez DPIA" (10), „happy-path-only deployed" (8), „prototype shipnutý
   bez gate" (7). 6 perspektiv žádá explicitní kontrakt v charteru.

3. **Sandbox jako produkt, ne výmluva.** Perspektivy 7, 10, 15 a podpořeno
   1, 5, 8 — pre-approved Terraform modul s VPC, throwaway DB, syntetický
   seeder, audit logging, 24h TTL, cost cap. Self-service z developer portal.

4. **Data classification a AI Act tier jako gate.** L1–L4 (7), DPIA trigger
   checklist (10), event taxonomy + privacy classification (12), persona
   inclusivity & disability data (11). 4 perspektivy žádají explicit
   classification před session 1.

5. **Score závaznosti potřebuje strukturu.** Pojmenováno v 1, 2, 7, 9, 10,
   11, 12. V0 popisuje „score závaznosti" bez škály. Panel žádá: 1–5 Likert
   s rationale field; weight per role (Security/Legal/A11y high-risk =
   blocker, ne weighted vote); AI-only feedback deflation max 0.5; uloženo
   do DB pro learning loop.

6. **Discovery Readiness Gate.** Perspektivy 2, 6, 12, 13, 14. Persona
   freshness ≤ 6 měsíců, JTBD, OST, voice-of-customer verbatim. Bez gate
   metoda generuje řešení k neexistujícímu problému.

7. **Contract-first / OpenAPI shadow agent.** Perspektivy 5, 4, 8, 12.
   OpenAPI vzniká paralelně s UI generátorem (BE shadow agent), ne post-hoc.
   Breaking-change registr s consumer ownery jako session 1 výstup.

8. **A11y povinná, ne volitelná (EAA 2025).** Perspektivy 6, 11 explicitně,
   podpořeno 4, 8, 13. EAA platí od 28. 6. 2025 — public-facing + B2B nad
   250 zaměstnanců spadá pod reasonable accommodation. Catalog v0 má A11y
   jako VOLITELNOU = regulatorně neudržitelné.

9. **Energy curve a 2 sessions vs 1 dlouhá.** Perspektiva 3 (a podpořeno
   8, 9). Kreativní špička 45–90 min, druhá vlna max 60 min. Session 1
   = 5–6 h ne 8 h, end v 16:00. Mezi-session 5–7 dní (ne 14). Session 2
   = 3 h rozhodovací, ne generativní.

10. **Decider model + accountability atribuce.** Perspektivy 1, 3, 7, 9, 10.
    V0 předpokládá konsensus, ale 8 lidí = paralýza nebo HiPPO maska. Decider
    s tie-breaker právem (informed dictatorship), zadavatel hlasuje POSLEDNÍ,
    decision log atribuuje člověka (DORA, AI Act čl. 14, GDPR čl. 22).

11. **Reinforcement / post-launch loop chybí.** Perspektivy 1 (ADKAR R),
    12 (T+30/60/90 readout, kill criteria), 13 (T+7 ticket check, T+30 retro,
    T+90 churn cohort), 14 (continuous discovery rhythm). Bez track-back
    metoda zhasne po 2 pilotech.

12. **AI-human dělba práce nedefinovaná.** Perspektivy 3, 7, 10, 11, 14.
    „AI vede výklad" v session 2 = nedostatečně specifikované. Tří-režimová
    matice: vlastnické/vetovací role = člověk; konzultativní = AI proxy +
    human sign-off; execution-heavy = AI vede.

## 2. Strukturální díry v metodě v0

- **Business Charter** — chybí ROI artefakt, success threshold, kill-switch,
  decider mandate (1).
- **Discovery layer / OST / JTBD** — metoda startuje řešením, ne problémem
  (2, 6, 14).
- **Data Classification Statement** — synthetic / anonymized / live není
  rozlišeno (7, 10).
- **Approved AI Tool list + DPA / SCC** — vibe-coding tools jako processors
  bez schválení = GDPR breach (7, 10).
- **Sandbox spec** — runtime prototypu nedefinovaný (15, 7, 5).
- **Contract-first / OpenAPI / breaking-change registr** (5, 4, 8).
- **A11y baseline + WCAG 2.2 AA** jako acceptance kritérium (4, 6, 11).
- **Event taxonomy + measurement plan + A/B test design** (12).
- **Support readiness D-2 + ticket prediction worksheet** (13).
- **P2P (Prototype-to-Prod) checklist** — single biggest gap (8, 15, 7).
- **SLO baseline + observability hooks + runbook** (15, 8, 5).
- **Energy curve / time-box / break protokol** (3).
- **AI-human dělba práce + human override** (3, 7, 10, 14).
- **Veto-handling playbook + escalation protokol** (1, 3, 7, 9).
- **Reinforcement track 30/60/90** (1, 12, 13).
- **MoSCoW na vstupy** (3) — 30+ povinných vstupů paralyzuje session.
- **Multi-team / dependency map** (9).
- **IP iteration mounting v SAFe** (1, 9).
- **Persona expiry policy + Discovery Debt Detector** (14).
- **UX writer / content design slot** (6).

## 3. Must-have nové artefakty (souhrn napříč panelem)

**Pre-flight (před session 1):**
- Business Charter (problém, segment, ARR impact, success metric, XYZ
  hypotéza, constraints, decider mandate, throw-away/evolve flag).
- Data Classification Statement (L1–L4, podepsaný DPO).
- AI Act risk-tier classification (Unacceptable / High-risk / Limited /
  Minimal).
- DPIA trigger checklist + RoPA záznam.
- Approved AI Tool list (s DPA/SCC) + ToS-snapshot.
- Threat model lite (STRIDE one-pager).
- Sandbox spec (Terraform modul, VPC, TTL, cost cap).
- Discovery Readiness Gate (persona ≤6 mo, JTBD, OST v0).
- Capacity pre-sign-off od Eng managera.
- Backend Context Pack (OpenAPI URL, ERD výřez, NFR čísla, ADR archiv).
- Vibe-brief (design tokens, component manifest, tech stack, conventions,
  anti-patterns, demo data shape, a11y baseline).
- Event taxonomy + naming convention + baseline metriky pre-read.
- Top-10 ticket kategorií + 20 verbatim citací (CS proxy).
- Persona disability set (low vision, motor, cognitive — alespoň 2).

**Session 1 výstupy:**
- 1–3 anotované mockupy s OST tag a JTBD card mapping.
- Draft OpenAPI 3.1 per varianta (BE shadow agent).
- Breaking-change registr + ERD diff + effort heat-map.
- Token compliance report + komponentový mapping (reuse / new / one-off).
- A11y quickscan (8–10 položek) + axe-core run.
- Gherkin akceptace (≥1 negative scenario per varianta).
- Ticket prediction worksheet per varianta.
- Deploy footprint estimate (TCO sheet) per varianta.
- Sandbox URL + IaC commit hash + 4 golden signals dashboard.
- Risk register + veto log + score závaznosti per role.
- Decision log s lidskou atribucí.

**Session 2 výstupy:**
- Go / iterate / kill rozhodnutí s explicit kritériem.
- Updated business case + exec one-pager.
- Handoff package: scoped epic, akceptační kritéria, dependency map,
  tech debt flagy.
- Akceptovaný OpenAPI lintovaný (Spectral) + 3–5 ADR.
- Contract test skeleton (Pact / Schemathesis).
- DPIA artefakt + AI Act tech doc skeleton (Annex IV) pokud high-risk.
- Privacy Notice draft + Legal basis statement per feature.
- Measurement plan (primary, leading, guardrail) + A/B test design + kill
  criteria + dashboard mockup.
- Support readiness checklist (KB D-7, makra D-2, training, escalation).
- SLO baseline + runbook stub + on-call assignment.
- P2P (Prototype-to-Prod) checklist (SBOM, secret scan, IaC v monorepu,
  observability, SLO, runbook, change advisory, DPIA, A11y human review).
- Audit log + decision atribuce + veto registr.

**Post-handoff (reinforcement):**
- T+7 ticket category check vs prediction.
- T+30 build progress vs estimate + leading metric readout.
- T+60 retro + verbatim sample.
- T+90 lagging metric vs success criterion + churn cohort + learning
  loop do role catalogu.

## 4. Návrhy úprav role catalogu

**Povýšení:**
- **Accessibility (#11)** — VOLITELNÁ → DOPORUČENÁ s default-on pro
  customer-facing + B2B nad 250 zaměstnanců. Trigger obrácený: A11y
  povinná, pokud projekt nepadá do úzké výjimky (interní tooling <10 lidí
  bez plánu externalizace, microenterprise). EAA 2025. (#11)
- **End-user proxy / User Research (#14)** — VOLITELNÁ → DOPORUČENÁ s
  default-on. Trigger: customer-facing flow nebo nový segment. Volitelná
  pouze pokud Discovery Readiness Gate prošel s persona freshness ≤3 měsíce.
- **Customer support proxy (#13)** — VOLITELNÁ → DOPORUČENÁ pro customer
  base > 1000 active users. Trigger: existing customer base + user-facing
  change.
- **Legal/GDPR (#10)** — VOLITELNÁ → DOPORUČENÁ pro projekty s daty
  uživatelů, marketing copy, AI use cases. AI Act trigger je téměř vždy.
- **Data/Analytics (#12)** — VOLITELNÁ → DOPORUČENÁ pro projekty s release
  intentem (jakákoli measurement powinnost po launchi).
- **QA / Test lead (#8)** — DOPORUČENÁ → POVINNÁ pro vše s release intentem
  (kdokoli v místnosti řekne „produkce" nebo „pilot s reálnými uživateli").
- **DevOps / Platform (#15)** — VOLITELNÁ → DOPORUČENÁ pokud session má
  sandbox (téměř vždy v Pflanzer). Trigger pro povinnost: deploy footprint
  > sandbox baseline, nový runtime, change v infra.

**Degradace AI proxy:**
- **Legal/GDPR (#10)** — AI proxy ✅ → ⚠️ s explicit hranicí. AI proxy
  jen pro L1/L2 data, minimal/limited risk, interní tooling. Lidský DPO
  povinně pro high-risk, special categories, profiling, ADM, marketing
  s claims, novel vendor.
- **End-user proxy (#14)** — AI proxy ✅ → ⚠️ s score deflation max 0.5.
  AI persona = vstup do session, ne výstup. Nikdy poslední slovo.
- **Accessibility (#11)** — AI proxy ✅ → ⚠️ pro mockup audit OK; pre-launch
  povinný human review.
- **QA (#8)** — AI proxy ✅ → ⚠️ pro test generation s povinným lidským
  reviewem každého scénáře před CI (testují implementaci, ne chování).

**Nové role:**
- **#16 UX writer / content designer** (perspektiva 6). Trigger: user-facing
  copy, error states, empty states, microcopy, marketing claims. Volitelná
  pro internal tooling. AI proxy ⚠️ s human review (UCPD + ePrivacy
  compliance).
- **#17 Champion / pilot lead** (implicitně 7, 9). Trigger: zavádění metody
  v nové BU, druhý+ pilot. Owner Coaching Kata loop, sdílení learnings
  v internal CoP. Lidský facilitator-in-training.
- **(Volitelně) #18 Architect / Solution architect** — pojmenováno v
  otevřených otázkách v0; relevantní pro multi-team scope (perspektiva 9
  „dependencies overhead").

**Decision tree změny:**
- Přidat krok 0: **Discovery Readiness Gate.** Pokud chybí persona ≤6 mo /
  JTBD / OST → 2-week Discovery Sprint, session 1 odložena.
- Přidat krok 0a: **Security & Data + Legal & Privacy + Platform Triage**
  (paralelně async, 48 h předem). Bez podpisů session 1 neodstartuje.
- Přidat krok 13: **Pokud projekt aspiruje na produkci do <3 měsíců →
  +QA (8) POVINNĚ a +DevOps (15) DOPORUČENĚ.**
- Přidat sanity check: **Pokud >10 lidí v místnosti → buď zúžit scope, nebo
  paralelní sessions po menších buňkách** (zachovat z v0, ale doplnit
  federovaný model pro multi-team scope: per-team mini-session + společná
  final).

**Per-role text patche:**
- Sekce „Kdy AI proxy vs lidský zástupce" — doplnit tří-režimovou matici z
  perspektivy 3 a score deflation pravidlo.
- Sekce „Sanity check" — doplnit MoSCoW na vstupy (Must / Should / Could)
  a kapacitní footprint (~8–10 person-days per cyklus).

## 5. MoSCoW gradace vstupů do Session 1

Z 30+ vstupů panelu odvodit minimum viable input a regulated maximum.
Default = MUST only; high-stakes / regulated = MUST + SHOULD; audit-grade
= vše.

**MUST (bez nich session 1 neodstartuje):**
- Business Charter (problém, success metric, XYZ hypotéza, constraints,
  decider mandate).
- Data Classification Statement + AI Act risk-tier (DPO + Security podpis).
- Approved AI Tool list (s DPA/SCC).
- Sandbox spec / runtime approval (Platform Triage).
- Discovery Readiness Gate (persona ≤6 mo, JTBD, OST v0).
- Capacity pre-sign-off od Eng managera.
- Tech stack + design tokens + component manifest (Vibe-brief).
- Backend Context Pack (existující OpenAPI, ERD, NFR baseline, ADR archiv).
- Threat model lite (STRIDE one-pager).
- Reálná demo data se správnou shape (synthetic L1/L2).

**SHOULD (regulated / customer-facing default-on):**
- DPIA lite + RoPA entry (pokud personal data).
- Privacy Notice template + Legal basis statement.
- WCAG 2.2 AA baseline + a11y disability persona set.
- Event taxonomy + naming convention + baseline metriky.
- Top-10 ticket kategorií + 20 verbatim citací (existující customer base).
- Brand guidelines + microcopy do/don't.
- Konkurenční snapshot deck (5–8 screenshotů).
- Anti-pattern list (UI patterns, API conventions, infra conventions).
- Browser/device support matrix.
- Persona disability set + JTBD karty.

**COULD (nice-to-have, audit-grade):**
- Existing analytics events + dashboard / KPI strom.
- A/B test power analysis pre-read.
- Multilingual / i18n requirements (top-3 jazyky).
- Cross-border / TIA dokumenty (non-adequacy země).
- Vendor risk register entries (DPA, SCC, exit clauses).
- Schema registry export (Avo / Iteratively).
- Innersource champion contact + CoP onboarding.
- Persona-specific painy (cohort-segmented).
- IaC / GitOps repo structure conventions.

**WON'T (out-of-scope pro session 1, ne pro metodu):**
- Live prod systém data (L4) → session se nekoná, jde do plného SDLC.
- Marketing copy s halucinovaným ToS / Privacy Notice — vždy z firemní
  template, ne generated.
- Production deployment artefakty — vyžadují samostatný architecture review
  gate po session 2.
- Pen test report / TLPT (DORA čl. 24) — post-handoff.

## 6. Top 10 ostrých takeaways

1. **„Sandbox je produkt, ne výmluva."** *(Security, perspektiva 7)*
   Když má CISO Office hotový pre-approved Terraform sandbox, security
   přestává být bottleneck a stává se enabler. Rozdíl mezi „blocker" a
   „guardrail".

2. **„Vibe-coding bez persony je krásná chyba v rekordním čase."** *(UX,
   perspektiva 6)* AI generátor je výtah pro design system, ne náhrada
   research. Bez persony, JTBD a accessibility v místnosti **dřív než první
   mockup** vznikne kosmetická fikce.

3. **„Pflanzer řeší alignment, ne discovery. Pokud mu nepředřadím JTBD
   a success metric, vyrobí mi nejhladší feature factory v korporátu —
   s AI uprostřed."** *(PM, perspektiva 2)* Kontext: metoda startuje
   řešením; bez OST/JTBD je cross-functional shoda na špatném problému.

4. **„AI je nejlepší co-pilot v místnosti — ale nikdo nepodepíše rozhodnutí,
   které udělala AI."** *(Facilitator META, perspektiva 3)* Facilitátor
   v Pflanzerovi není moderátor, je **architect of accountability**:
   rozhoduje, kdy AI mluví, kdy člověk mlčí, a kdy se konflikt eskaluje.

5. **„Vibe-coding generuje UI v hodinách, contract žije roky. Pokud
   z workshopu nevyjde podepsaný kontrakt, byl to hezký den — ne metoda."**
   *(Backend lead, perspektiva 5)* Kontext: 80 % korporátní práce je
   integrace s existujícím; UI-first datový model rozbije bounded context.

6. **„Prompt je log, ne konverzace. Cokoli, co napíšeš do AI nástroje
   v korporátu, je retained, replicable a může skončit u regulátora."**
   *(Security, perspektiva 7)* Workshop musí mít DLP a Approved Tool list,
   jinak je to GDPR breach čekající na kalendář.

7. **„GDPR breach se neposuzuje podle úmyslu, ale podle architektury
   rozhodnutí. Pflanzerova metoda buď tu architekturu má v charteru, nebo
   ji bude mít v incident reportu."** *(Legal/DPO, perspektiva 10)*
   Vibe-coding tool = processor v okamžiku, kdy do promptu vstoupí jakákoli
   osobní data.

8. **„A11y v session 1 stojí 5 minut. Post-launch 5 týdnů a soudní spor."**
   *(Accessibility, perspektiva 11)* Quickscan na konci session 1 zachytí
   70 % issue. EAA non-compliance v EU = pokuta až 20 000 EUR + nucené
   stažení produktu z trhu.

9. **„Feature without measurement = feature without learning. Pflanzer
   bez instrumentation deadline a measurement plan vyrobí nejlépe sladěnou
   black-box organizaci v korporátu — všichni se shodli, nikdo neví,
   jestli to funguje."** *(Data/Analytics, perspektiva 12)*

10. **„Buď prediktivní v Session 1, nebo reaktivní po launchi. Třetí
    možnost není."** *(Customer Support, perspektiva 13)* Feature shipne
    v úterý, ve středu v 9:00 mám 47 ticketů se stejným dotazem — protože
    nikdo v session 1 neřekl „takhle to uživatel pochopí špatně".

**Bonus** *(Engineering Manager, 9):* „**Šetří čas zítra cenou času dnes.**"
Capacity math (~8–10 person-days/cyklus) musí být na stole, ne pod kobercem.

**Bonus** *(End-user proxy, 14):* „AI persona je *archetype check* — neumí
ti říct, co tě překvapí." Score deflation max 0.5; AI persona = vstup, ne
výstup.
