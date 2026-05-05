# 10 — Legal / GDPR / DPO perspektiva

## Kdo jsem

Senior Legal Counsel a DPO v EU/CEE korporátu, 12+ let. GDPR (čl. 5, 6,
13, 28, 32, 35, 44), EU AI Act (GPAI 2/2025, high-risk 8/2026), DSA,
ePrivacy, DPA / SCC, IP assignment v rapid prototypingu. Pflanzerova
metoda mě **přitahuje** (zkracuje "pinkací smyčky", co končí na stole
6měsíční DPIA) i **děsí** (rapid = bez review = AI vendor v US bez DPA,
marketing copy halucinovaný modelem, IBAN v promptu).

## 1. Posouzení Pflanzerovy metody

Z Legal/DPO pohledu **podmíněně schvalitelná**, ale role catalog mě
podceňuje: Legal/GDPR vedeno jako "VOLITELNÁ (trigger)", AI proxy
"krátkodobě OK". V roce 2026 **regulatorně neudržitelné**:

1. **AI Act trigger je téměř vždy.** Jakmile session generuje systém,
   který profile-uje, scoruje, filtruje CV nebo rozhoduje o úvěru, jsme
   v Annex III high-risk. "Novel AI use case" musí být povinný pre-flight
   assessment.
2. **Vibe-coding tool = processor / sub-processor.** Bolt, Lovable, v0,
   Stitch jsou GDPR čl. 28 processors v okamžiku, kdy do promptu
   vstoupí jakákoli osobní data (i pseudonymizovaná). Bez podepsané
   DPA + SCC (Module 2, EU → US) je první session **GDPR breach**.
3. **Joint controllership riziko.** Pokud provider použije prompty na
   trénink, přechází do joint-controller (čl. 26). Free tiery to default
   umožňují.
4. **Marketing compliance.** Mockup landing s "přihlaste se" bez double
   opt-in, ePrivacy banneru a legal basis declaration je default v každém
   vibe-coding outputu. Halucinovaný ToS / Privacy Notice = žaloba.
5. **Audit trail rozhodnutí.** AI Act čl. 14 (human oversight) a GDPR
   čl. 22 (ADM) vyžadují lidskou atribuci. "AI vede výklad připomínek"
   v session 2 je OK jen když finál podepíše člověk — to v metodě chybí.

## 2. Must-have vstupy (do charteru, před session 1)

- **RoPA záznam (čl. 30) — workshop entry.** Účel = "rapid prototyping",
  legal basis = LI (čl. 6/1/f) pro syntetická data; controller, processors
  (každý AI tool zvlášť), kategorie subjektů, retention (24h sandbox TTL),
  recipients, transfers, TOMs (čl. 32). 15 min, archivuje DPO.
- **DPIA trigger checklist** (čl. 35/3 + EDPB):
  - Systematic profiling / scoring? → DPIA.
  - Velký rozsah special categories (čl. 9) / trestní (čl. 10)? → DPIA.
  - Systematic monitoring veřejných míst? → DPIA.
  - Inovativní tech + nezletilí / vulnerable? → DPIA.
  - ADM s legal/significant effect? → DPIA.
  - **≥ 2 = session odložena** do DPIA lite.
- **AI Act risk-tier classification** (před session 1):
  - **Unacceptable (čl. 5)** — sociální scoring, real-time biometrie,
    manipulativní techniky → session se nekoná.
  - **High-risk (čl. 6 + Annex III)** — HR screening, credit scoring,
    biometrie, kritická infra, education, law enforcement → pouze
    s plánem QMS (čl. 17), conformity assessment, FRIA.
  - **Limited risk (čl. 50)** — chatboti, deepfakes → AI disclosure
    v mockupu.
  - **Minimal risk** — interní tooling bez profilování → standardní flow.
- **DPA + SCC pro každý AI vendor** v Approved Tool listu: Anthropic
  Enterprise (zero-retention), OpenAI Enterprise (DPA + SCC), Vercel
  (US transfer + SCC), Bolt (DPA jen Pro+), Lovable (DPA u Workspace).
  **Free tiery = automatický red flag.**
- **Marketing compliance brief** pro user-facing copy: cookie consent
  template, double opt-in, LI balancing test, unsubscribe, čl. 13 text.
- **IP assignment & confidentiality** v charteru — výstup patří firmě;
  AI-generated code IP (žádné AGPL kopie, license scan v gate).

## 3. Must-have výstupy (z každé session)

- **DPIA artefakt** (lite/plný) podepsaný DPO před handoffem. Šablona
  ICO / EDPB.
- **AI Act tech doc skeleton** (Annex IV) pokud high-risk: popis,
  intended purpose, training data lineage, accuracy, human oversight,
  foreseeable misuse.
- **Privacy Notice draft** (čl. 13/14) — nikdy halucinovaný, vždy
  z firemní template.
- **Legal basis statement per feature** — čl. 6/1/a–f explicitně,
  u marketingu opt-in s evidence trail.
- **Vendor risk register entry** pro každý AI tool (DPA, SCC version,
  sub-processors, transfer, exit clause).
- **Decision log s lidskou atribucí** — kdo schválil jménem; AI Act
  čl. 14 a GDPR čl. 22.

## 4. Edge cases

- **Reálný e-mail / IBAN v promptu.** GDPR breach, 72h clock (čl. 33).
  Mitigace: DLP pre-filter, redaction middleware, incident playbook.
- **Claim "AI-powered" bez podkladu** → UCPD, DSA čl. 25 dark patterns.
  Legal review claimů před share-out.
- **Prototype do produ bez DPIA** → osobní odpovědnost DPO. Sandbox-to-prod
  gate **nediskutovatelný**.
- **Vendor mění ToS uprostřed projektu** (Lovable, OpenAI čtvrtletně).
  Charter obsahuje ToS-snapshot v den session.
- **Produkt pro děti / vulnerable** → AI Act + GDPR čl. 8 + DSA čl. 28,
  ne vibe-coding metodou.
- **Cross-border tým** (DE+CZ+UA) — UA mimo adequacy, nutné SCC + TIA.

## 5. Vylepšení metody

1. **Krok 0a "Legal & Privacy Triage"** (30 min async, paralelně se
   Security). DPIA checklist + AI Act tier + RoPA entry. Pre-approved
   templates pro 80 % případů projdou za 30 min. Bez DPO podpisu se
   session 1 nespouští.
2. **Async pattern (baseline 03):** pre-read charteru 48 h předem (10 min
   DPO času), **on-call slot 30–45 min uprostřed session**, post-session
   sign-off před handoffem. DPO není fyzicky celý den, ale je ve smyčce.
3. **AI Act risk tier jako gating dimenze score závaznosti.** High-risk
   = Legal blocker, ne weighted vote. Limited risk = transparency jako
   akcept. kritérium.
4. **Privacy-by-Design template knihovna** v sandboxu — consent flow,
   DSAR endpoint, retention policy, audit log — aby vibe-coding
   negeneroval prototyp od nuly s halucinovaným ToS.
5. **Marketing compliance sub-agent** v AI co-pilotovi — review copy
   proti UCPD + ePrivacy + DSA před share-out.

## 6. Memorabilia — kdy AI proxy a kdy lidský DPO v session 2

- **AI proxy stačí:** L1/L2 data, minimal/limited risk, interní tooling,
  syntetická data, bez marketing copy navenek, bez ADM. AI proxy
  reportuje DPO async; sign-off do 24 h.
- **Lidský DPO povinně** (alespoň on-call 45 min): high-risk AI Act tier,
  special categories (čl. 9), profiling/scoring, cross-border do non-adequacy
  zemí, marketing s claims, jakýkoli ADM s legal/significant effect,
  novel vendor bez DPA. DPO podpis je osobní právní akt.

> "GDPR breach se neposuzuje podle úmyslu, ale podle architektury
> rozhodnutí. Pflanzerova metoda buď tu architekturu má v charteru,
> nebo ji bude mít v incident reportu."
