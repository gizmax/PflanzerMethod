# 07 — Security / Compliance perspektiva

## Kdo jsem

Senior Security Architect z CISO Office v EU/CEE bance (s druhou nohou v telco
světě). 15+ let v secopsu a AppSec, spolupodepisuji DORA reporting, NIS2
kompetenční mapu, PCI-DSS scope, GDPR DPIA a nově AI Act risk classification.
Můj denní pohled: vibe-coding workshop = nový attack surface (data exposure,
IP leak, credential exfil v promptu, supply-chain vektor v generovaných
dependencies, shadow-IT prototyp shipnutý do produ bez review). Mám veto
právo, ale **nechci být přírodní bariéra** — chci pre-approved sandbox a
shift-left guardrails, aby tým nemusel chodit „kolem“ bezpečnosti.

## 1. Posouzení Pflanzerovy metody

Metoda **mě v základu těší**: Security je v role katalogu jako povinná pro
projekty s daty uživatelů a má veto. Klíčový posun proti Design Sprintu —
nejsem tam až po prototypu, kdy je drahé něco škrtat. Co mě **znervózňuje**:

1. **Datová třída neřešena.** Zdrojový popis mluví o „demo datech“, ale
   neříká, jestli synthetic, masked, nebo prod snapshot. To je rozdíl mezi
   no-review a plnou DPIA per GDPR čl. 35.
2. **AI tool jako black box.** Bolt/Lovable/v0/Stitch posílají prompt včetně
   příloh do US providerů. Bez Approved AI Tool Listu padá metoda na první
   compliance audit (DORA čl. 28 — ICT third-party risk, NIS2 čl. 21
   supply chain).
3. **Prompt jako exfil kanál.** „Vibekódovat live“ = stakeholder copy-pastne
   reálný customer e-mail nebo IBAN do promptu. Logováno, retained, mimo EU.
4. **Generovaný kód = supply chain.** AI builder vytáhne `npm i` 200 balíků
   včetně tří typosquattů. Žádný SBOM, žádný license check.
5. **Handoff do vývoje** je v metodě popsán jako „hladký“. Bez gate je to
   přesně ta cesta, jak prototyp s hardcoded API klíčem skončí v prod repu.
6. **Audit trail session 2** — AI vede výklad připomínek, ale rozhodnutí
   musí být atributovatelné člověku (DORA accountability, AI Act čl. 14
   human oversight pro high-risk use case).

Verdikt: metoda je **schválitelná pod podmínkou**, že nad ní postavíme
sandbox spec, data classification gate a Approved Tool list. Bez nich
veto na první session, kde někdo zmíní „pojďme to napojit na prod API“.

## 2. Must-have vstupy (do charteru, před session 1)

- **Data Classification Statement.** Jeden ze čtyř levelů, podepsaný DPO:
  - L1 Public (marketing copy) — žádný gate.
  - L2 Internal synthetic (faker, GPT-generated) — light review.
  - L3 Anonymizovaný snapshot (k-anonymity ≥ 5, žádné quasi-identifiers)
    — DPIA lite + sandbox-only.
  - L4 Real PII / payment / health — **session se nekoná** v této metodě,
    jde do plného SDLC s threat modelem.
- **Threat model lite** (STRIDE one-pager) — co chráníme, před kým, jaký
  blast radius prototypu.
- **Approved AI Tool list.** Schválené: Claude Enterprise (zero-retention DPA),
  Cursor Business (privacy mode), v0 Team s SSO + DPA, Bolt Pro s opt-out
  trainingu. **Neschválené pro session:** free tiery, osobní účty, Replit
  Starter, GitHub Spark Tech preview (právní vakuum).
- **Sandbox spec** — viz výstupy.
- **Identity & access** — všichni v session loggovaní jednotným SSO,
  guest přístupy s expirací 24 h, MFA povinné.
- **DORA checklist pro third-party** pokud session generuje produkční
  závislost (SaaS provider zaregistrovaný do ICT registru, DPA, exit plán).
- **Async legal/compliance pre-read** charteru 48 h předem (pattern
  z baseline 03 — legal nepřijde na celý den, ale podepíše scope).

## 3. Must-have výstupy (z každé session)

- **Audit log** — každý prompt, každá AI odpověď, attribuce na user @ SSO,
  retention 7 let pro regulované projekty (DORA čl. 12 logy, NIS2 incident
  forensics). Nikoli „chat history v Bolt účtu“.
- **SBOM prototypu** — `cyclonedx` / `syft` na výstupní repo, license scan
  (žádné GPL v bankovním kontextu bez schválení), CVE scan (Trivy/Snyk).
- **Secret scan** výstupu (gitleaks, trufflehog) — hardcoded klíče
  v generovaném kódu jsou běžné, gate před handoffem to musí chytit.
- **Decision log session 2** s lidskou atribucí — kdo schválil kterou
  variantu, ne „AI navrhla“. Pro AI Act čl. 14 a DORA accountability.
- **Veto registr** — pokud security flagovala variantu jako critical
  risk, je to podepsaný artefakt, ne ústní poznámka.
- **Sandbox-to-prod gate checklist** — než cokoli z prototypu opustí
  sandbox, projde: threat model full, pen test (pokud L3+), DPIA, change
  approval, ICT third-party registrace.

## 4. Edge cases

- **Stakeholder copy-pastne reálné PII do promptu** uprostřed session.
  Mitigace: DLP plugin v prohlížeči (Nightfall, Microsoft Purview), prompt
  pre-filter, „pii-redactor“ middleware před AI providerem. Incident
  response playbook + 72h GDPR notification clock.
- **Prototyp obsahuje halucinovaný legal text** (ToS, GDPR notice). Nikdy
  nepoužít bez legal review — flag v metodě.
- **AI provider má outage během session** — fallback Approved Tool #2,
  nikdy ne „rychle to dáme do ChatGPT z osobního účtu“.
- **Session na regulovaném produktu (PSD2 SCA, MiFID)** — security veto
  na vibe-coding metodu samotnou, jde standardním SDLC.
- **Prototype shipnutý do produ bez gate** (klasický shadow-IT failure).
  Technická pojistka: sandbox má vlastní VPC, žádný route do prod sítě,
  žádné prod credentials v secret store.
- **Champion ze session 2 odejde z firmy** s knowhow. NDA + IP assignment
  v charteru, code v firemním repu od minuty 1, ne na osobním GitHubu.

## 5. Vylepšení metody

1. **Přidat krok 0: „Security & Data Triage“** (15 min, async, před session 1).
   DPO + sec architect klasifikuje data, schválí tool, podepíše charter.
   Bez podpisu se session 1 nespouští. Toto je guardrail, ne bariéra —
   máme pre-approved templates, takže 80 % případů projde za den.
2. **Pre-approved sandbox jako produkt CISO Office.** Terraform modul:
   isolated VPC, throwaway DB, syntetický seeder, audit logging do SIEM,
   24h TTL. Tým si „objedná sandbox“ a má ho do hodiny. Místo aby každý
   workshop vyjednával infra ad hoc.
3. **„Security AI proxy" v session 1.** Sub-agent s threat-model promptem
   běží paralelně, generuje STRIDE komentáře k mockupům. Lidský sec architect
   review-uje async po session, ale tým má feedback live. Šetří mou kapacitu.
4. **Bind AI Act risk tier do score závaznosti.** Pokud session 2 syntetizuje
   feedback a Security flagne „high-risk AI system“ (čl. 6), score = blocker,
   ne weighted vote. Veto, ne hlas mezi hlasy.
5. **Champion v každé BU má security buddy** — innersource pattern z baseline
   03, ale spárovaný. Champion ví, koho zavolat, sec architect ví, kdo
   workshopy reálně dělá. Snižuje friction o řád.

## 6. Konflikty s ostatními rolemi

- **vs Zadavatel / PdM:** „Chceme to rychle, security to zdrží.“ Můj
  protiargument: pre-approved sandbox a tool list **zrychlují**, protože
  eliminují late-stage review. Veto používám jen na L4 data nebo
  unapproved tooly.
- **vs Frontend / Backend lead:** „Tenhle balík už používáme jinde, neskenuj
  to znovu.“ SBOM gate nediskutuju — DORA čl. 8 ICT asset inventory
  je vyžaduje per artefakt.
- **vs Eng manager (timeline):** Pokud handoff do produ znamená přeskok
  threat modelu, blokuju. Návrh: paralelní threat model track během
  prototypingu, ne sériově po něm.
- **vs Legal/GDPR:** typicky souhlas, edge je AI Act interpretace —
  kdo definuje „high-risk“ use case? Doporučuju společný triage protokol.
- **vs DevOps:** sdílená agenda, konflikt jen u „rychle to deployneme
  na náš shared cluster“ — ne, sandbox VPC nebo nic.

## Memorabilia

- **„Sandbox je produkt, ne výmluva."** Když má CISO Office hotový
  pre-approved sandbox, security přestává být bottleneck a stává se
  enabler. To je rozdíl mezi „blocker“ a „guardrail“.
- **„Prompt je log, ne konverzace."** Cokoli, co napíšeš do AI nástroje
  v korporátu, je retained, replicable a může skončit u regulátora.
  Workshop musí mít DLP a Approved Tool list, jinak je to GDPR breach
  čekající na kalendář.
- **„Veto, které nepoužiješ proaktivně, použiješ retroaktivně —
  a to už bolí všechny."** Šift-left znamená: být v místnosti od minuty
  0, ne podepisovat odmítnutí v týdnu 6.
