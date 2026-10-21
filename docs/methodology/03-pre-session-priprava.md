# 03 — Příprava před Kickoffem

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: co musí být hotové, než začne Kickoff. Pro
> default profil (Lean) je to krátké — `pflanzer doctor`, jména, okna,
> preview. Pro stupeň **Full** (regulované) k tomu přibývá plný triage;
> ten je tu stručně a audit-grade detail je ve vrstvě
> [`governance/`](../governance/README.md). Stupně: [`00-lean-pflanzer.md`](00-lean-pflanzer.md)
> § Tři stupně. Postup krok za krokem pro první pilot: [`zacni.md`](../zacni.md).

## Příprava v Lean (default)

Bez těchto pěti věcí Kickoff nesvolávej.

1. **Ověřený problém** (Krok 0 níže) — metoda discovery nenahrazuje.
2. **Repo je připravené:** `pflanzer init` commitnutý a pushnutý,
   vyplněný `docs/INTEGRATION_GUIDE.md` (auth, API klient, state, logger,
   feature flags, struktura, test runner) a `.pflanzer/CONSTITUTION.md`
   (krátká nepřekročitelná pravidla pro AI — držet na jedné obrazovce),
   testy, lint, build, CI a **preview deploy větví**. Ověř
   `pflanzer doctor` → „připraveno ke Kickoffu: ano". Při „ne" nezačínej,
   pokud chybějící věc vědomě nepřijmeš jako riziko (ADR-0022).
3. **Jména ke všem 6 krokům cesty** (byznys/Decider, produkt, design,
   vývoj, bezpečnost & právo, provoz). Kdo může který krok zastoupit:
   [`02-role-catalog.md`](02-role-catalog.md). Krok bez jména = nesvolávat.
4. **Okna v kalendáři najednou, ne ad hoc:** Kickoff 15 min · Build 3 h ·
   checkpoint bezpečnost & právo 20 min · Rozhodnutí 60–90 min · checkpoint
   provozu 20 min. Délky podle stupně: kanonická tabulka v 00-lean.
5. **Preview prostředí domluvené s provozem** — to, co firma už má
   (Vercel/Netlify preview, review apps, preview namespace), bez
   produkčních dat a bez přístupu do produkční sítě. Bez URL nemá Sběr feedbacku (Async) na
   co klikat.

Pak **Kickoff** (`/pm start`, 15 min, Decider + jádro): zadání na 1
stránku (problém v 1 větě, jedna metrika úspěchu, kill kritérium), jména,
stupeň a risk profil (`throwaway | pilot | production`).

### Zadání na 1 stránku (Kickoff)

| Pole | Obsah |
|------|-------|
| Problém | 1 věta; evidence z Kroku 0 |
| Metrika úspěchu | jedna; leading i lagging, je-li možné |
| Kill kritérium | konkrétní podmínka „kdy to zabalíme" |
| Decider + mandát | jméno, mandát říct Go i Kill, eskalační kontakt (ADR-0001) |
| Jména 6 kroků | jádro vs okno, termíny oken |
| Stupeň, risk profil | Quick/Lean/Full · throwaway/pilot/production |
| Výjimka throw-away | jen s důvodem (ADR-0005): discovery-only pilot, důkaz oddělený od produkce, certifikovaná regulovaná produkce. Jinak vítěz jde do produkce |
| Rozpočet | odhad PD jádra a oken; default profil ~6–8 PD |

Zadání je povinný vstup Buildu (ADR-0004). Tool ho zakládá jedinou cestou
(`pflanzer start`, v Claude Code `/pm start`; bez Claude Code
`pflanzer start --spec kickoff.json`). Kickoff se ptá jednou otázkou
**„Jak vážné to je?“** (demo / pilot / ostré + osobní údaje) a z odpovědi
odvodí stupeň, okna a prahy; krátký slug vypíše sám. **Zastavovací
pravidla:** data L4 (reálné PII, platby, zdraví) nebo AI Act „unacceptable"
→ projekt se nezačíná, patří do plného SDLC; zapiš do decision logu.

### Krok 1a — Rozpočet (True Cost)

Dřívější rozsáhlý worksheet per role × fáze je v default profilu zbytečný.
Stačí **odhad PD**: jádro 3–4 lidé × ~1,5 dne + okna + Ship; typicky
**~6–8 PD** a ~8 dní kalendářně. Měř ho u každého pilotu (počet lidí,
trvání, počet zásahů v oknech, gate score). U Full odhad sepíše EM
s ohledem na triage, delší Build a Async; podrobný worksheet a
reinforcement rozpočet viz [`governance/method-charter.md`](../governance/method-charter.md).

## Krok 0 — Discovery Readiness Gate

Metoda řeší alignment, ne discovery. Bez ověřeného problému vznikne
„nejhladší feature factory". PdM doloží:

1. **Persona** nejvýš 6 měsíců stará (B2B 9, interní nástroj 12 s nutným
   re-shadowingem), aspoň 5 nedávných rozhovorů nebo ekvivalent (shadowing,
   review ticketů, nahrávky prodejních hovorů). Po pivotu/reorganizaci
   expiruje.
2. **JTBD** „When [situace], I want to [job], so I can [výsledek]",
   podepsané PdM (a designérem, je-li v jádru).
3. **OST v0** (desired outcome → 2–3 opportunities → uvažovaná řešení),
   vyplněný zhruba z 60 %.

Chybí-li cokoli, předřaď 2týdenní discovery sprint; Kickoff odlož.
**Discovery Debt Detector** (sub-agent `discovery-debt-detector`) spočítá
podíl tvrzení o uživateli bez zdroje: skóre 0–10, **≥ 7 = STOP**,
3–6 = varování (výstupy jen exploratory), ≤ 2 = OK. V Lean ho stačí
pustit při `/pm feedback` ([`05`](05-mezi-sessions.md)); ve Full už před
Kickoffem.

## Krok 0a — Triage tracky (jen stupeň Full)

Ve Full běží **čtyři povinné tracky** (Discovery + Security + Legal +
Platform; sub-agenti přes `/pm triage`), async 48–72 h před Kickoffem, a
všechny musí být `ok`; jinak Ship neprojde (override jen Decider
s rationale). V Lean je jejich obsah nahrazen checkpointem bezpečnost &
právo v Buildu a gates v Shipu.

### Security & Data Triage

- **Data classification L1–L4:** L1 veřejná · L2 interní/syntetická ·
  L3 anonymizovaný snapshot (k-anonymita ≥ 5) → DPIA lite, jen sandbox ·
  **L4 reálné PII/platby/zdraví = nezačínat**, plné SDLC.
- **Threat model lite** (STRIDE one-pager): co chráníme, před kým, jaký
  dosah má preview. Worktree **není bezpečnostní izolace**.
- **Approved AI Tool list** s DPA/SCC; neschváleno: free tiery, osobní účty,
  dodavatel bez DPA.
- **Identity:** SSO + MFA, host s expirací; **egress limit** a strop
  tokenů/nákladů.
- **DORA scope:** prompt audit log (SIEM, vyhledávání dle uživatele
  a projektu), retence 7 let, registr třetích stran — bez toho je
  práce s AI v DORA scope nekompatibilní.

### Legal & Privacy Triage

- **AI Act tier ve třech fázích:** **A** provizorní (z Kickoff zadání,
  označená `provisional`; slouží jen jako brána — High-risk bez kapacity
  na DPIA = STOP) → **B** přehodnocení nad skutečnými variantami v Async
  (upgrade Limited → High-risk = povinný sporný bod Rozhodnutí) →
  **C** finální podpis DPO s data flow diagramem, intended use, human
  oversight (čl. 14) a Annex IV kostrou před Shipem. Bez Fáze C pilot není
  kompletní.
- **DPIA trigger checklist** (GDPR čl. 35/3): osobní data, profilování,
  automatizované rozhodování, zvláštní kategorie, velký rozsah, systematické
  sledování, zranitelné subjekty, přeshraniční přenos.
- RoPA záznam, vendor risk register, brief marketingových tvrzení (UCPD,
  ePrivacy).

### Platform Triage

- **Sandbox spec** (předschválený modul): izolovaná síť s default-deny,
  syntetická data, audit logging, TTL, watermark, noindex, žádná cesta do
  produkční sítě, strop nákladů.
- Odhad provozní stopy per varianta, schválené runtime, observability
  contract (OTel, strukturované logy, tracing), politika secretů.

### Track S (nouzová cesta bez vývojáře)

Jen při jednom ze čtyř triggerů (distribuovaný vývoj ≥ 3 časová pásma ·
AI Act High-risk + certifikovaná produkce · FDA/IEC 62304/DO-178C/PSD2 SCA ·
sponzorem požadovaná specifikace jako výstup) a se schválením Method
Decidera (ADR-0011). Bez triggeru projekt odlož, nepřepínej. Detail: ADR-0020,
[`governance/`](../governance/README.md).

## Vstupy podle důležitosti (MoSCoW)

- **MUST (Lean):** zadání na 1 stránku, ověřený problém, `doctor` zelený,
  jména 6 kroků, okna, preview prostředí, `INTEGRATION_GUIDE` +
  `CONSTITUTION`, syntetická data se správnou shape.
- **SHOULD (customer-facing, osobní data):** DPIA lite + RoPA, WCAG 2.2 AA
  baseline, event taxonomie a baseline metriky, top-10 ticketů, brand/voice
  guidelines, matice podporovaných prohlížečů.
- **COULD (audit-grade):** power analýza A/B, i18n, přeshraniční přenosy,
  schema registry, IaC konvence.
- **WON'T:** reálná produkční data (L4), generované ToS/Privacy Notice,
  produkční deploy artefakty mimo Ship, pen test (post-Ship).

## Volba builderu

Default je **Claude Code v repu firmy** — varianty vznikají jako větve
target repa (ADR-0009). Hosted builder (v0/Bolt/Lovable) jen jako opt-in
pro greenfield bez repa nebo throw-away; kód pak musí skončit jako větev
v target repu. Každý builder musí být na Approved AI Tool list
(zero-retention DPA, SSO, audit log, opt-out trénování). Regulované věci
(PSD2 SCA, MiFID, zdraví) se vibe-codingem nehrají — standardní SDLC.

## Checklist před Kickoffem

```
Lean
[ ] Problém ověřen (persona, JTBD, OST; debt skóre ≤ 6)
[ ] pflanzer doctor: připraveno ke Kickoffu = ano
[ ] Decider má mandát říct Go i Kill
[ ] Jména u všech 6 kroků cesty; nikdo nad 5 lidí naráz
[ ] Preview prostředí pro 3 branche domluvené s provozem
[ ] Všechna okna v kalendáři
[ ] /pm funguje v Claude Code

Navíc ve Full
[ ] 4 triage tracky ok (Discovery, Security, Legal, Platform); AI Act Fáze A
[ ] Approved AI Tool list + prompt audit log (DORA scope)
[ ] Senior delegáti u vetovacích rolí, EM kapacita potvrzena
[ ] Rozpočet PD odsouhlasen EM a sponzorem
```

Cokoli ✗ = Kickoff se odkládá, neimprovizuje se na místě. Vetovací role,
které pre-read zablokují, řeš před oknem, ne v něm.
