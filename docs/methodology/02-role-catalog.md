# Role catalog — knihovna zástupců kroků cesty

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: říká, **kdo může zastoupit který krok cesty**.
> Je to knihovna, ne seznam pozvánek (ADR-0021). Zástupce dostane jen svou
> jednostránkovou [role card](role-cards/README.md) (co přinést, co
> podepisuje, kdy být u toho, na co hlasuje); pro konkrétní projekt se
> jmény: `pflanzer roles cards --slug <slug>`. Historie změn katalogu:
> ADR-0003.

## 6 kroků cesty → kdo je může zastoupit

| # | Krok cesty | Typický zástupce (catalog) | Účast |
|---|------------|-----------------------------|-------|
| 1 | Byznys | Zadavatel / sponzor = **Decider** (#1) | okna: Kickoff 15 min + Rozhodnutí 60–90 min |
| 2 | Produkt | PdM (#2), často i facilitátor (#3) | jádro |
| 3 | Design | UX / Designer (#6) | jádro (u interního toolu může krýt PdM) |
| 4 | Vývoj | FE / Vibe-coding lead (#4), BE / API lead (#5) | jádro (1–2 buildeři) |
| 5 | Bezpečnost & právo | Security (#7) nebo Legal / DPO (#10) — jeden stačí | okno: checkpoint 20 min |
| 6 | Provoz | DevOps / Platform (#15), případně EM (#9) | okno: checkpoint 20 min u Ship |

Pravidla:

- **Žádný krok bez jména.** Krok bez zástupce = nesvolávat.
- **Jeden člověk smí krýt víc kroků** (vývojář = vývoj + provoz, PdM =
  produkt + design u interního toolu).
- **Jádro** 3–4 lidé celou dobu (PdM, 1–2 vývojáři, designér);
  **okno** = konkrétní čas nad konkrétním artefaktem. **Max 5 lidí naráz.**
- **Zástupce má mandát.** Kdo nemůže v okně rozhodnout, není zástupce
  (vetovací role: senior delegát, ne junior bez mandátu).
- **Ostatní role** (QA, A11y, Data, CS proxy, End-user, …) jsou v default
  profilu **AI expert sub-agenti** (`.claude/agents/`): perspektiva
  nepřítomné role jako vstup, ne hlas. Lidského zástupce přidávej jen
  v rozšířené sestavě stupně Full. Sub-agenty spouštěj ve vlnách po 3–4.
- **U klávesnice sedí vývojář**, nikdy facilitátor ani „AI proxy" za
  vývojový tým (ADR-0020, Track P).

## Jak číst katalog

- **Status** = povinná · povinná při triggeru · doporučená (default-on =
  vypíná se jen s důvodem) · volitelná (trigger).
- **AI proxy:** Režim 1 = vždy člověk · Režim 2 = AI draft + podpis
  člověka · Režim 3 = AI vede samo (viz níže).
- Čísla rolí se používají napříč tool/agenty (`§ N`) — neměň je.

## Katalog (18 rolí)

### 1. Zadavatel / Business owner — povinná
Vlastní problém a budget; **Decider** s mandátem říct Go i Kill (ADR-0001).
Přináší zadání na 1 stránku (problém, metrika, kill kritérium). Okna:
Kickoff, Rozhodnutí; hlasuje poslední. AI proxy: ne (Režim 1).

### 2. Produkt manažer (PdM) — povinná
Překlad byznysu do produktových požadavků a priorit; vlastní scope
(tie-breaker na scope, UX na flow) a parking lot. Přináší JTBD, metriku,
OST; zajišťuje, že problém je ověřený. AI proxy: draft ano, finální slovo
člověk (Režim 1).

### 3. Facilitátor (lidský + AI) — povinná
Hlídá čas, energii a parking lot, deeskaluje konflikty, drží silent
voting a pořadí hlasování. Často PdM. Při audit-grade/high-stakes
projektu navíc druhý facilitátor z jiné jednotky nebo externí coach
(ADR-0006). AI proxy: ne (Režim 1).

### 4. Frontend / Vibe-coding lead — doporučená (v Track P povinná)
Builder u klávesnice: řídí AI při stavbě variant, drží konvence repa,
token compliance a přístupnost základů. Přináší `INTEGRATION_GUIDE`,
design tokeny, component manifest. AI proxy: greenfield částečně,
brownfield jen s human review (Režim 2).

### 5. Backend / API lead — doporučená (v Track P povinná při změně API/dat)
Builder pro API a datový model: contract-first (OpenAPI), breaking-change
registr, migrace. Přináší OpenAPI, ERD, NFR baseline, ADR archiv.
AI proxy: jen velmi greenfield části (Režim 2).

### 6. UX / Designer — doporučená
Flow a konzistence s design systémem; u nového flow je v jádru.
Přináší persony, journey, tokeny, seznam odchylek od DS. AI proxy:
audit design systému ano, integrita flow s podpisem (Režim 2).

### 7. Security / Compliance — povinná při triggeru
Trigger: auth, osobní data, integrace, platby, nový AI use case. Zastupuje
krok Bezpečnost & právo na checkpointu: **veto na varianty s Kritickou připomínkou (`critical`)
rizikem** (veto je veto, ne hlas), data classification, threat model,
SBOM/secret scan. Podpis: `pflanzer checkpoint … bezpecnost`. AI proxy:
STRIDE draft a scany ano, veto podepisuje člověk (Režim 1).

### 8. QA / Test lead — povinná při triggeru
Trigger: jakákoli zmínka „produkce" nebo „pilot". Acceptance scénáře
(Gherkin, aspoň 1 negativní), test pyramida, kontrola, že AI testy
testují chování, ne zrcadlí implementaci. AI proxy: generování testů ano,
review každého scénáře člověkem před CI (Režim 2).

### 9. Engineering manager — doporučená
Trigger: scope nad ~2 sprinty. Kapacita, závislosti, T-shirt odhad (ne
story pointy), strop nákladů; u kroku Provoz může krýt checkpoint.
AI proxy: ne — kapacita je citlivá (Režim 1).

### 10. Legal / GDPR / DPO — doporučená
Trigger: osobní data, marketingová tvrzení, AI Act ≥ Limited. Zastupuje
krok Bezpečnost & právo (spolu s #7, stačí jeden). DPIA trigger, AI Act
tier, DPA/SCC dodavatelů. Lidský DPO povinně u High-risk, zvláštních
kategorií a profilování. AI proxy: jen L1/L2 data a minimal/limited risk
(Režim 2).

### 11. Accessibility expert — doporučená (default-on pro customer-facing)
WCAG 2.2 AA quickscan, axe-core; Critical/Serious na veřejném rozhraní
blokuje „final". Opt-out jen pro interní admin tool s doloženým důvodem.
AI proxy: statické audity ano, pre-launch review člověkem (EAA se nedá
atestovat AI) (Režim 2).

### 12. Data / Analytics — doporučená
Trigger: release intent, nové metriky. Measurement plan (lagging +
leading + guardrail), event schema, instrumentace nejpozději 2 dny před
Shipem. AI proxy: návrh schématu ano, plán schvaluje člověk (Režim 2).

### 13. Customer support proxy — doporučená
Trigger: uživatelská základna řádu tisíců + změna viditelná uživatelům.
Predikce ticketů per varianta, podpůrné materiály před launchem.
AI proxy: jen s přístupem k historii ticketů (Režim 2).

### 14. End-user proxy / User research — doporučená (default-on)
Hlas uživatele: čerstvost persony, JTBD, audit discovery debtu (skóre
0–10; ≥ 7 = STOP). AI je vstup (kontrola archetypu), ne výstup — nový
poznatek, okrajové případy a say-do gap nezvládne. AI-only feedback má
váhu max 0,5 (Režim 2).

### 15. DevOps / Platform — doporučená
Zastupuje krok Provoz: preview prostředí pro 3 branche, deploy plán,
monitoring, on-call, rollback, strop nákladů. Podpis:
`pflanzer checkpoint … provoz`. AI proxy: typické vzory ano, custom infra
ne (Režim 2).

### 16. UX writer / Content designer — volitelná (trigger)
Trigger: texty v UI, chybové stavy, marketingová tvrzení, plain language.
Marketingová a právní tvrzení vždy z firemní šablony, nikdy generovaná.
AI proxy: draft + lidský review (Režim 2).

### 17. Champion / Pilot lead — volitelná (trigger)
Trigger: druhý a další pilot v jednotce, škálování. Vlastní retro, měření
T+7/30/60/90 a předávání zkušeností mezi piloty; u prvních pilotů
bootstrap (ADR-0006). AI proxy: ne (Režim 1).

### 18. Solution / Domain architect — volitelná (trigger)
Trigger: zadání přes 3+ týmy, komplexní doména, regulovaný SDLC. Integration
map, breaking-change registr, ADR drafty. AI proxy: jen typické vzory
(Režim 2).

## Výběr zástupců — rychlý strom

1. **Vždy:** Decider (#1), PdM (#2), vývojář (#4 a/nebo #5), designér
   (#6; u interního toolu může krýt PdM).
2. **Bezpečnost & právo:** Security (#7) při datech/auth/integracích/
   platbách; Legal/DPO (#10) při osobních datech, marketingu, AI Act ≥
   Limited. Stačí jeden člověk, který unese obě témata.
3. **Provoz:** DevOps/Platform (#15), jinak EM (#9) nebo vývojář s přístupem
   k pipeline.
4. **Další perspektivy** (QA #8, A11y #11, Data #12, CS #13, End-user #14,
   UX writer #16, Architect #18) jako AI sub-agenti; člověka jen v rozšířené
   sestavě (Full) nebo když trigger výslovně vyžaduje (A11y u
   customer-facing: lidský review před launchem).
5. **Sanity check:** naráz **max 5 lidí**. Víc = scope je příliš široký —
   zúžit, nebo rozdělit na paralelní buňky (u 3+ týmů federovaný model, viz
   [`08`](08-edge-cases-a-rizika.md) § 7). Pro jádro > 4 zváž, kdo může
   přejít na okno.

Před výběrem roles ověř **Krok 0** (ověřený problém) a u Full i triage
tracky — [`03`](03-pre-session-priprava.md).

## AI proxy vs lidský zástupce — 3 režimy

| Režim | Pravidlo | Příklady |
|-------|----------|----------|
| **1 — Vlastnické a vetovací** | vždy člověk | Decider, PdM (finál), facilitátor, Security (veto), EM (kapacita), DPO u High-risk, Champion |
| **2 — Konzultativní** | AI připraví draft, člověk podepíše do 24–48 h | UX audit DS, QA scénáře, Data schéma, CS predikce, UX writer, End-user archetypy |
| **3 — Execution-heavy** | AI vede, výsledek jde do decision logu | generování variant, shrnutí, clustering feedbacku, agregace skóre, OpenAPI shadow, SBOM/CVE, axe-core, STRIDE draft |

Cross-cutting:

- **AI-only feedback má váhu max 0,5** z 1,0 (heuristika, ne kalibrovaný
  parametr; kalibrace přes měření pilotů).
- **Decision log vždy atribuuje člověka**, nikdy „AI navrhla"
  (AI Act čl. 14, GDPR čl. 22).
- **AI nikdy není podpis**: pre-launch review přístupnosti a veto
  bezpečnosti jsou nedelegovatelné.

## AI náhrada chybějícího zástupce

> ADR-0023. Krok cesty smí mít místo jména `AI` (v zadání `AI` nebo
> `AI:<agent>`, např. `AI:ux-expert`) — ale jen podle tabulky. AI **připraví**,
> **člověk podepisuje**. Tří režimy výše se to týká takto:

| Krok cesty | Režim | AI náhrada | Kdo podepíše |
|------------|-------|-----------|--------------|
| Byznys (Decider) | 1 | **nikdy** | bez Decidera se Kickoff nesvolává |
| Vývoj | 1 | **nikdy** | u klávesnice sedí vývojář |
| Produkt | 1→2 | jen stupeň Quick / throwaway | Decider (zadání) |
| Design | 2 | ano (UX expert + kontroly přístupnosti) | PdM; u zákaznického produktu v produkci člověk |
| Bezpečnost & právo | 1 | jen **předkontrola** (`pflanzer checkpoint … --ai --agent security-expert`) | throwaway: stačí AI; pilot/production: člověk do 48 h, jinak Ship blokuje |
| Provoz | 1 | jen **předkontrola** (`--ai --agent devops-platform-expert`) | throwaway: AI; pilot: vývojář z jádra; production: člověk z provozu |

Pravidla (zkráceně):

1. AI náhrada je **vidět**: v zadání, `pflanzer status`, decision logu a `SHIP.md`.
2. AI checkpoint je **draft**. Pro pilot/production zůstává „čeká na podpis
   člověka" (`--by <jméno>`), dokud ho někdo nepotvrdí; Ship do té doby
   blokuje, nebo Decider vědomě přebije (`--override-triage --rationale`).
3. AI feedback má váhu max 0,5 a AI nikdy nehlasuje.
4. AI náhrada je **na chvíli** (pilot). Pro další projekt téhož týmu `status`
   připomene sehnat člověka; retro měří podíl kroků s AI náhradou.

Ostatní role katalogu (QA, přístupnost, data, support, uživatelé…) nejsou kroky
cesty: jejich perspektivu dodávají AI expert sub-agenti jako vstup bez hlasu.
