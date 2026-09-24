# 01 — Conflict matrix

> Synthesis output. Mapuje reálné konflikty mezi rolemi pojmenované v sekci 6
> jednotlivých perspektiv. Cílem je pojmenovat osy, ne všechny dvojice.

## Tabulka konfliktů

| Role A | Role B | O co konflikt | Co chce A | Co chce B | Návrh resolution |
|--------|--------|---------------|-----------|-----------|------------------|
| Zadavatel (1) | Security (7) | Datová třída sandboxu | Live integrace pro „realistický test", rychlost | Synthetic / L1–L2 data, sandbox-only scope | Pre-charter Data Classification Statement podepsaný DPO před session 1; L4 = session se nekoná. |
| Zadavatel (1) | Eng manager (9) | Kapacita Q3, business urgency vs roadmap | Ship za 2 sprinty, P&L push | Capacity buffer 25 %, default into IP iteraci, veto na overcommit | Capacity pre-sign-off jako vstup; pokud kapacita zmizí, aktivuje se champion v jiné BU. |
| Zadavatel (1) | Frontend lead (4) | Prototyp do prod | „To už funguje, jen to nasaďte" | Throw-away kontrakt, sandbox watermark, 24h TTL | Throw-away default v charteru; „evolve" jen po code review s podpisem FE + EM + Security. |
| Zadavatel (1) | Backend lead (5) | Timeline kontra migrace | Vibe-coding speed timeline | Migrace 200M řádků trvá kvartál bez ohledu na rychlost UI | Score závaznosti BE = „schválím contract", ne „líbí se mi UI"; T-shirt sizing v session, SP po spiku. |
| Zadavatel (1) | UX (6) | Speed vs research rigor | Ship to learn | Persona research a JTBD lock před první variantou | XYZ hypotéza jako falsifikovatelný marker; persona ownership shared (PdM + UX podpisují). |
| Zadavatel (1) | Customer support (13) | Ticket impact a support cost | „Support to vyřeší" | Forecast + readiness D-2 jako blocker launchu | Support cost line item v business case; D-2 readiness checklist jako merge-blocker. |
| Zadavatel (1) | Data/Analytics (12) | Dashboard a measurement | „Dashboard zítra", bez consent / sample size | Measurement plan, instrumentation deadline | Measurement plan jako součást DoD; bez něj není ship. Consent + power analysis pre-read. |
| PdM (2) | UX (6) | Persona ownership | Prioritization + scope tie-breaker | Persona validation a research ownership | Shared artefakt; PdM tie-breaker na scope, UX na flow. Persona doc podepsaný oběma před session. |
| PdM (2) | Security (7) | Veto-late vs feature scope | Pre-read charteru, on-call slot | Veto na critical risk, žádné late-stage surprises | Pre-charter triage 80 % pokrývá; on-call slot v session; eskalace pro 20 %. |
| PdM (2) | Backend lead (5) | „Pole navíc v UI" | „Malá změna" | Schema migration + backfill + contract bump | Breaking-change registr s explicitním ownership; každá UI změna kontrola proti consumer ownerům. |
| PdM (2) | Customer support (13) | Interpretace pain | Vlastní view zákazníka | Verbatim z ticketů, top-10 kategorií | VoC ritual prvních 30 min Session 1; ticket data jako vstup, ne názor jako rozhodnutí. |
| PdM (2) | Data/Analytics (12) | Outcome vs output | Ship rychle | Měřitelný ship, leading + lagging | Measurement v DoD; PdM + Analytics interlock — PdM definuje outcome, Analytics měřitelný proxy. |
| PdM (2) | End-user proxy (14) | Discovery vs delivery | Mockup driven scope | Discovery readiness gate, fresh persona | Discovery Readiness Gate povinný; <6 měsíců staré persona, 5+ rozhovorů, OST. |
| Frontend lead (4) | Backend lead (5) | Rychlost vs contract | Flexibilní JSON, rapid UI | OpenAPI vzniká současně, typed schema | Contract-first: BE shadow agent generuje OpenAPI paralelně s UI generátorem (side-by-side). |
| Frontend lead (4) | UX (6) | Komponentní rozhodování | shadcn defaults, implementační pohodlí | Design system steward, deviation = ticket | DS steward s veto na nové komponenty; tokens jako MCP context do builderu, every deviation logována. |
| Frontend lead (4) | Accessibility (11) | A11y stav generovaného kódu | Rychlost vibe-codingu | Sémantický HTML, focus management, contrast | A11y quickscan + axe-core jako Session 1 gate; expert v místnosti od minuty 0, ne post-hoc. |
| Backend lead (5) | DevOps (15) | Ownership SLO/SLA | Application-level performance | Platform-level SLO baseline, runbook | SLO Quick-Set library a sdílený footprint estimate; SLO = sdílený artefakt, ne overlap. |
| Security (7) | Legal/GDPR (10) | „High-risk AI Act" interpretace | STRIDE, sandbox guardrails | DPIA trigger, AI Act tier classification | Společný triage protokol (Krok 0 — Security & Legal Triage) s pre-approved templates; oba podepisují charter. |
| Security (7) | DevOps (15) | „Deploy na shared cluster" | Sandbox VPC, network default-deny | Self-service paved-road sandbox modul | Sandbox spec jako sdílený Terraform modul (Security guardrails + Platform lifecycle). |
| Eng manager (9) | UX (6) | Kapacita vs UX kvalita | „Vezmeme jednodušší variantu" | Yellow flag pro known usability debt | UX dostává viditelný warning v rozhodovací matici (ne veto, ale signal vs „rychlejší = lepší"). |
| Eng manager (9) | Backend lead (5) | Effort estimate v rapid contextu | T-shirt z místnosti pro PI commit | „M = 3 týdny, ne 3 dny", spike před hard estimate | Dvoufázový estimate: T-shirt v session, story-point až po 2-day capped spike. |
| Customer support (13) | UX (6) | Happy path vs unhappy path | Predikované error/recovery scénáře | Čistý core flow | Top-3 predikované tickety = P1 v acceptance criteria; error states povinné v každé variantě. |
| Data/Analytics (12) | Security (7), Legal (10) | PII v event taxonomy | Trackable behavior signals | Hashing, pseudonymizace, consent | Privacy classification dat jako vstup; PII NIKDY v event name/property; server-side pro essential. |
| End-user proxy (14) | PdM (2) + Zadavatel (1) | AI persona jako náhrada research | Rychlost, archetype check | Real evidence, novel insight, edge cases | Score deflation: AI-only persona feedback max 0.5 z 1.0; AI persona = vstup do session, ne výstup. |

---

## Top 5 cross-cutting konfliktů (řeší se napříč ≥3 perspektivami)

### A. Prototyp do prod / sandbox-only kontrakt
*Pojmenováno v perspektivách 1, 4, 5, 7, 8, 10, 15.* Sponzor uvidí běžící Bolt
instanci a chce „nasadit". FE lead trvá na throw-away. Security odmítá deploy
mimo sandbox VPC. Legal nepodepíše bez DPIA. DevOps odmítá shared cluster.
QA blokuje bez P2P checklistu.

**Resolution:** Throw-away je default v Business Charteru. „Evolve" status
vyžaduje současně: (a) FE lead + EM podpis na token-compliance + a11y report,
(b) Security sign-off na threat model + SBOM + secret scan, (c) DPO sign-off
na DPIA + AI Act tier, (d) DevOps schválený footprint + SLO + runbook,
(e) QA P2P checklist (Gherkin scénáře, contract testy, regression analysis).
Sandbox technicky enforcuje hranici — vlastní VPC, watermark, noindex, 24h
TTL, žádný route do prod sítě. Bez kompletního paketu prototyp neopustí
sandbox. Tím se odzbrojí politický tlak „management override".

### B. Pre-flight gating: Security + Legal + Discovery + Platform triage
*Pojmenováno v perspektivách 1, 7, 10, 14, 15 (a implicitně 2, 8, 12).*
Pflanzer v0 startuje řešením, ne problémem. Security/Legal nemají checkpoint
před kódem; Discovery debt je default; Platform footprint vyplave v týdnu 6.

**Resolution:** „Krok 0" jako paralelní async triage 48 h před session 1,
s pre-approved templates pro 80 % případů: (1) Data Classification + AI Act
tier (Security + DPO), (2) Discovery Readiness Gate (persona freshness ≤6 mo,
JTBD, OST v0), (3) Platform Triage (sandbox modul, footprint estimate v0,
runtime approval). Bez podepsaného charteru a všech tří triage signoffů
session 1 neodstartuje. Tím odpadají late-stage veta a metoda ztrácí
charakter „rychlé cesty kolem governance".

### C. AI proxy hranice — kdy AI nahradí člověka a kdy ne
*Pojmenováno v perspektivách 3, 7, 8, 10, 11, 14 (částečně 6, 12).* Catalog
v0 dává AI proxy ✅ příliš snadno. End-user proxy = archetype interpolation,
neumí novel insight. Accessibility AI proxy nezvládne screen reader UX.
Security/Legal vetují AI bez human override. QA AI proxy generuje testy,
které testují implementaci místo chování.

**Resolution:** Tří-režimová matice (z perspektivy 3 a podpořená ostatními):
(1) **Vlastnické a vetovací role** (Zadavatel, PdM, Security final, Legal
final, EM kapacita, Accessibility final pre-launch, End-user pro novel
insight) — vždy člověk, AI dělá briefing/sumarizaci. (2) **Konzultativní
role** s AI proxy + human-in-the-loop async sign-off do 24–48 h (UX, Data,
QA test generation, Customer support analytics). (3) **Execution-heavy
context-light tasks** — AI vede (mockup generation, sumarizace transcriptu,
clustering, score agregace, SBOM scan, axe-core audit). **Score deflation**
pro AI-only persona/feedback (max 0.5 z 1.0). **Decision log atribuuje
člověka**, ne „AI navrhla" (AI Act čl. 14, GDPR čl. 22, DORA accountability).

### D. Veto handling: Security + Legal + Eng kapacita + UX + A11y
*Pojmenováno v perspektivách 1, 3, 7, 8, 9, 10, 11.* Veto-rights v catalogu
v0 jsou nerovnoměrné: Security/EM mají, UX/A11y/QA nemají. Zadavatel se bojí,
že veto v místnosti zničí jeho preferenci politicky.

**Resolution:** Strukturovaná hierarchie závaznosti místo binárního veta:
(1) **Critical risk = blocker** (Security STRIDE Critical, Legal AI Act
high-risk + bez DPIA, A11y WCAG Critical/Serious na public-facing, EM
capacity overrun, BE breaking change bez consumer alignment). Session
pivotuje na alt. variantu, nepokračuje v zablokované. (2) **Yellow flag =
viditelný warning v decision matrici** bez veta (UX usability debt, QA
testability concern, Customer support load increase). (3) **Score
závaznosti** (1–5 Likert s rationale field) se zveřejňuje **až po
hlasování**, zadavatel hlasuje **poslední** (anti-HiPPO). Konflikt v 5.
minutě výskytu, ne ke konci. Pre-charter triage pokrývá 80 % případů
ex-ante, takže veto v místnosti je vzácné.

### E. Discovery debt vs alignment-driven feature factory
*Pojmenováno v perspektivách 2, 6, 12, 13, 14.* Pflanzer staví stakeholdery
do místnosti a vyrobí mockup — ale na nejasném problému. Persona je
PowerPoint z roku 2024. JTBD chybí. AI persona dělá archetype check, ne
research. Vibe-coding bez fresh evidence = sofistikovaný monolog.

**Resolution:** **Discovery Readiness Gate** povinný před session 1
(perspektiva 14): persona freshness ≤6 měsíců (5+ rozhovorů), JTBD statement
podepsaný PdM, OST v0 (desired outcome → opportunities → solutions). Mockupy
v session 1 musí mapovat na konkrétní node OST. Pokud chybí, předřazuje se
2-week Discovery Sprint (15 rozhovorů). **Voice of Customer ritual** prvních
30 min Session 1 (perspektiva 13): 5 verbatim citací, 1 audio recording,
1 anekdota „nejhorší týden support". **Pre-mortem TRIZ ve 30. minutě**
(perspektiva 8): „za 6 měsíců to selhalo, proč?" Generuje rizika dřív, než
tým zamiluje variantu. **Discovery Debt Detector** jako AI co-pilot skill —
audit, kolik tvrzení v briefu má zdroj vs. assumption-stated-as-fact, skóre
0–10. ≥7 = STOP, předřaď discovery sprint.
