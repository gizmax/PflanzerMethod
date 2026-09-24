# Perspektiva: Backend / API lead

## Kdo jsem
Principal BE engineer v korporátu, 15+ let. Java monolity, Go microservices, DDD, event-driven. Můj rozpočet na blbost je nulový — jakmile se prototyp dostane do prod bez review, platím to dva roky migracemi a hotfixy. Vibe-coding mě neděsí; děsí mě, když ho někdo zaměňuje za delivery.

## 1. Posouzení metody z mé role

**Co mi pomáhá**
- Jsem v místnosti od minuty 0 — můžu zarazit nesmyslné datové modely dřív, než se na ně postaví UI a stanou se "realitou".
- Score závaznosti dává BE veto na variantách, které porušují existující contracty, aniž by se musel dohadovat politicky.
- Mockup mezi sessions je tangible — můžu z něj reverse-inženýrovat OpenAPI a mám konkrétní artefakt pro architecture review.

**Co mi chybí**
- Metoda mlčí o **datovém modelu jako prvotřídním artefaktu**. Vibe-coder vygeneruje JSON z hlavy, FE to zkonzumuje, a najednou máme `userId` jako string vedle existujícího UUID v `core-users`.
- **Žádný contract-first krok.** OpenAPI/AsyncAPI/protobuf se nikde nezmiňuje. To je v korporátu kde má každá BU svoje API gateway a každý consumer svoje SLA strategická chyba.
- **Žádné gating na breaking changes.** Pflanzer předpokládá greenfield, ale 80 % korporátní práce je integrace s existujícím.
- Idempotence, retry semantika, eventual consistency, transakční hranice — nikde. Mockup ukáže happy path, FE myslí že je hotovo.

**Co mě v ní ohrožuje**
- "Programátoři jsou u tvorby prototypu → handoff bude hladký" je nebezpečný předpoklad. Hladký handoff znamená *commitment*, ne vibe. Bez ADR a contractu commitment není.
- AI v session 2 "navrhuje, jak to zapracovat" — pokud nemá kontext na existující domain model, navrhne věci, které lokálně dávají smysl a globálně rozbijí bounded context.
- Scope creep skrz UI: PdM přidá pole do mockupu, BE má v ten moment "schváleno" něco, co znamená migraci 200M řádků.

## 2. Must-have vstupy do Session 1

1. **Existující OpenAPI/AsyncAPI specifikace** dotčených služeb (raw YAML, ne PDF export). Pokud neexistují → flag, vytvoř před session.
2. **ERD + data dictionary** dotčených bounded contextů: PK/FK, kardinality, owner služba, retention policy, klasifikace dat (PII/PCI).
3. **Integration map**: kdo je consumer našich API (interní + externí), jejich SLA, contract version pinning, deprecation policy.
4. **Non-functional baseline**: p95 latence, throughput peak, error budget, current SLO. Bez čísel se nedá designovat.
5. **Auth/authz model**: OAuth scopes, session lifecycle, mTLS hranice, service-to-service identity (SPIFFE/JWT claims).
6. **ADR archiv** (Architecture Decision Records) za posledních 12 měsíců — co už bylo rozhodnuto a proč. Zabraňuje re-litigaci.
7. **Event taxonomy + schema registry stav** (pokud jedeme event-driven): existující eventy, jejich verze, kompatibilita, dead-letter strategie.
8. **Coding & API conventions**: error format (RFC 7807?), pagination styl, časové zóny, ID formát (UUIDv7?), naming (snake/camel), versioning strategie (URI vs header).

Bez 1, 2, 3, 5 se Session 1 z mé role **nespouští**. Je to pre-flight, ne nice-to-have.

## 3. Must-have výstupy ze Session 1 a 2

**Session 1**
- **Draft OpenAPI 3.1** pro každou variantu mockupu — vygenerovaný "shadow agentem" paralelně s UI. Stub, ne final, ale strukturovaný.
- **Domain delta**: které entity přibývají, které se mění, které jsou breaking. Diff proti current ERD.
- **Breaking-change registr**: explicitní seznam (URL change, removed field, type change, semantics change) per varianta — vstup do score závaznosti.
- **Effort heat-map** per varianta: S/M/L/XL na BE, s jednou větou proč (typicky migration cost, ne dev cost).

**Session 2**
- **Akceptovaný OpenAPI** finální varianty, lintovaný (Spectral), s examples.
- **3–5 ADR draftů**: API versioning, idempotency strategie, transakční hranice, error model, eventy vs sync.
- **Contract test skeleton** (Pact/Schemathesis) — minimálně názvy testů, ne implementace.
- **Migration plan stub**: backfill strategy, dual-write window, rollback plán, feature flag.
- **Observability checklist**: jaké metriky/traces/logs nově vznikají, kdo vlastní dashboardy, alert thresholds.

## 4. Edge cases a rizika

1. **"Vibe-deployed prototype"** — někdo z workshopu ukáže běžící Bolt/Lovable instanci sponzorovi, ten řekne "tak to nasaďte". Schema vygenerované AI končí v prod DB. Mitigace: charter explicitně zakazuje deploy mimo sandbox; production deployment vyžaduje samostatný architecture review gate.
2. **Idempotence ignored.** Mockup nemá retry, prototype nemá `Idempotency-Key`. FE pak v prod při timeoutu duplikuje objednávky. Mitigace: idempotency je default v API conventions, ne opt-in.
3. **Breaking change pro existing consumers** schovaná v UI změně. Field rename v mockupu = field rename v API = rozbité 4 mobilní apps v marketu. Mitigace: BE shadow agent fl aguje každou změnu signatury proti registrovaným consumerům.
4. **Datový model navržený UI-first.** Denormalizace pro pohodlí FE, která rozbije source-of-truth. "User má addressLine kombinovaný" — a najednou nemůžeš dělat fakturační reporty. Mitigace: ERD-first warm-up s Event Stormingem na komplexní domény (per baseline 01).
5. **Eventual consistency lež.** Mockup ukáže "okamžitě se zobrazí v dashboardu", ale reálná architektura má 2 s propagaci přes Kafku. PdM commitne UX, který nelze postavit. Mitigace: každý mockup screen má anotaci "data freshness: realtime / <Xs / async".

## 5. Konkrétní vylepšení metody

1. **Contract-first vstup pre-session.** Před Session 1 vznikne *Backend Context Pack* (1–2 strany): seznam dotčených services, jejich OpenAPI URL, ERD výřez, top 3 NFR čísla, top 5 ADR. Generuje BE lead, schvaluje v briefingu. Bez tohoto packu Session 1 s "data/API změnou" trigger se nespouští.
2. **BE Shadow Agent paralelně s UI generátorem.** Zatímco Bolt/Lovable/Stitch generuje UI varianty, druhý agent (Cursor `/best-of-n` nebo Claude Code se `senior-fullstack` skillem) generuje **OpenAPI spec a ERD diff** z téhož briefu. Side-by-side se promítá: mockup vlevo, kontrakt vpravo. Stakeholder vidí oba v reálném čase.
3. **Hand-off rules jako blocker, ne checklist.** Z workshopu se nevychází bez: (a) lintovaného OpenAPI, (b) breaking-change registru s podpisem všech consumer ownerů, (c) min. 3 ADR draftů, (d) sandbox-only flagu na deploymentu. Score závaznosti pro BE = "schválím contract", ne "líbí se mi UI".
4. **Pre-mortem pro datový model v Session 1.** 15 min TRIZ (per baseline 01): "jak bychom tento model zaručeně rozbili za 18 měsíců?" Generuje seznam migration risks dřív, než se commitne. Levné, vysoký payoff.
5. **API observability budget per varianta.** Každá varianta v mockupu má anotaci: nové endpointy, odhad RPS, p95 cíl, cardinality nových metrik (pozor na Prometheus blow-up). BE shadow agent to počítá automaticky. Bez čísel = "varianta nehodnocena".

## 6. Konflikty s ostatními rolemi

- **Frontend / Vibe-coding lead**: chce rychlost a flexibilní JSON; já chci stabilní contract a typed schema. Řešení: contract-first (OpenAPI vzniká **současně** s UI, ne po něm), generated TS clients pro FE.
- **Zadavatel**: vidí běžící prototype a očekává timeline odpovídající vibe-codingu. Já mu musím říct, že migrace 200M řádků trvá kvartál bez ohledu na to, jak rychle Bolt vygeneruje UI. Score závaznosti mi v tom musí krýt záda.
- **Produkt manažer**: chce pole "navíc" v UI ("je to malá změna"). Pro mě je to schema migration + backfill + contract bump. Konflikt řeší breaking-change registr s explicitním ownership.
- **Security**: typicky spojenec, ale občas konflikt o "kolik dat může jít do sandbox prototypu". Řeší charter s data classification.
- **DevOps / Platform**: spojenec — oba tlačíme na boring infra, observability, stabilní contracty. Pravděpodobnost konfliktu o ownership SLO/SLA.
- **Engineering manager**: konflikt o effort estimaty. Vibe-coding zkresluje, kolik práce je hotovo. Mé "M" znamená 3 týdny, ne 3 dny. EM mi musí věřit, ne čísla z prototypu.

## Memorabilia
Vibe-coding generuje UI v hodinách, contract žije roky. Pokud z workshopu nevyjde podepsaný kontrakt, byl to hezký den — ne metoda.
