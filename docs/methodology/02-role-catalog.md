# Role catalog — knihovna perspektiv pro Pflanzerovu metodu

> **Status:** DRAFT v0.1 (před expertním panelem). Finalizace po fázi 1.4 syntézy.

## Proč role catalog

Klasické workshop metodiky (Design Sprint, LDJ, …) předpokládají fixní okruh
účastníků („Decider, Facilitator, 4–7 expertů"). Pflanzerova metoda jde dál:
**každý projekt má jiný relevantní mix rolí.**

Role catalog řeší dvě věci:
1. **Pre-flight check** — než svolám session, vím, koho potřebuji v místnosti
   a koho ne. Nezvu zbytečně, ale ani nezapomínám.
2. **AI panel mapping** — pro každou vybranou roli umí tool spustit
   odpovídajícího sub-agenta, který se k materiálům vyjadřuje *z té perspektivy*.

## Jak číst tabulku

- **Povinná** = bez této role session 1 nemá smysl spouštět.
- **Doporučená** = standardně přidat, pokud nemáš důvod nepřidat.
- **Volitelná (trigger)** = přidat, **jen když** platí trigger. Jinak overhead.
- **AI proxy** = co dělat, když lidský zástupce není k dispozici (AI jen
  reprezentuje jeho perspektivu, finální slovo má pak člověk asynchronně).

---

## Katalog (15 rolí)

### 1. Zadavatel / Business owner — POVINNÁ
- **Vlastní nápad a budget.** Bez něj není projekt.
- **Vstup:** business cíl, success metric, konstrainty.
- **Výstup ze session:** preferovaná varianta, go/no-go signály.
- **AI proxy:** ❌ Nelze. Bez něj sessionu 1 odložit.

### 2. Produkt manažer — POVINNÁ
- **Překlad business → produktové požadavky**, prioritizace.
- **Vstup:** persona, user journey, konkurence, OKR vazba.
- **Výstup:** preference matrix, scope rozhodnutí.
- **AI proxy:** ⚠️ Krátkodobě (s předem připraveným briefem).

### 3. Facilitátor (lidský + AI) — POVINNÁ
- **Vede session**, hlídá agendu a čas, deeskaluje konflikty.
- AI co-pilot ho doplňuje (panel expertů, generování mockupů, sumarizace).
- **AI proxy:** ❌ Lidský facilitátor nutný — AI samotná
  konflikt mezi rolemi neureší.

### 4. Frontend / Vibe-coding lead — DOPORUČENÁ pro UI fíčury
- **Trigger pro povinnost:** projekt mění UI nebo přidává nový view.
- **Vstup:** existující design system, preferovaný stack (React/Vue/...),
  code conventions, accessibility minimum.
- **Výstup:** preference UI varianty, technický feasibility check.
- **AI proxy:** ⚠️ Pro greenfield jde, pro brownfield ne (zná kontext).

### 5. Backend / API lead — DOPORUČENÁ pro data/API změny
- **Trigger:** nové API, změny datového modelu, integrace.
- **Vstup:** existující API contracts, datový model, performance constraints.
- **Výstup:** odhad effort, API skica, identifikace breaking changes.
- **AI proxy:** ⚠️ Jen pro velmi greenfield části.

### 6. UX / Designer — DOPORUČENÁ pro nové flow
- **Trigger pro povinnost:** nový user flow, přepracování core experience.
- **Volitelná:** drobná change v existujícím flow (PM + FE-dev to ošetří).
- **Vstup:** brand guidelines, design system, persony, research insights.
- **Výstup:** preference UX varianty, identifikace usability rizik.
- **AI proxy:** ✅ Možný, pokud existuje silný design system jako kontext.

### 7. Security / Compliance — POVINNÁ pro projekty s daty uživatelů
- **Trigger pro povinnost:** auth, osobní data, externí integrace, payment.
- **Volitelná:** interní tooling bez user dat.
- **Vstup:** threat model, compliance requirements (DORA/NIS2/PCI), data classification.
- **Výstup:** **veto právo na varianty s critical risk**, mitigation návrhy.
- **AI proxy:** ❌ Veto musí podepsat člověk; AI připraví podklad.

### 8. QA / Test lead — DOPORUČENÁ pro release-grade fíčury
- **Trigger pro povinnost:** výstup míří do produkce v <1 měsíci.
- **Volitelná:** explorační prototyp bez plánu produkce.
- **Vstup:** test strategy, automation framework, kritické flows.
- **Výstup:** testability assessment, návrh akcept. kritérií.
- **AI proxy:** ✅ Pro generování testů a checklistů jde.

### 9. Engineering manager — DOPORUČENÁ pro scope > 2 sprinty
- **Trigger pro povinnost:** odhad práce > 2 sprinty / 1 PI.
- **Volitelná:** quick win < 1 sprint.
- **Vstup:** týmová kapacita, roadmap, dependencies na ostatní týmy.
- **Výstup:** **realističnost timelinu**, konflikt s ostatní roadmapou.
- **AI proxy:** ❌ Kapacita & roadmap jsou citlivé, vyžadují člověka.

### 10. Legal / GDPR — VOLITELNÁ (trigger)
- **Trigger:** osobní data, marketing communication, smluvní vztahy,
  novel AI use case (EU AI Act).
- **Vstup:** stávající DPA, ToS, marketing compliance rules.
- **Výstup:** flagy nepoužitelných variant, doporučení pro privacy.
- **AI proxy:** ✅ Krátkodobě s předem připraveným briefem, finální opt v.

### 11. Accessibility expert — VOLITELNÁ (trigger)
- **Trigger:** public-facing, sektor s WCAG povinností (EU EAA), vládní/EU.
- **Volitelná:** interní tooling pro malou skupinu.
- **Vstup:** WCAG 2.2 AA / EAA požadavky, target audience.
- **Výstup:** kontrolní seznam pro mockupy, identifikace blockerů.
- **AI proxy:** ✅ Audit mockupů AI zvládne, lidský expert review na final.

### 12. Data / Analytics — VOLITELNÁ (trigger)
- **Trigger:** projekt definuje nový metric, A/B test, nebo touchne
  existující analytics events.
- **Vstup:** event taxonomy, stávající dashboardy, hypotézy k testování.
- **Výstup:** návrh measurement plan, definice success metric.
- **AI proxy:** ✅ AI navrhne event schema, člověk schválí.

### 13. Customer support proxy — VOLITELNÁ (trigger)
- **Trigger:** post-launch impact (změna ve flow, kterou uživatelé volají).
- **Volitelná:** greenfield interní bez customer base.
- **Vstup:** top 10 support tickets, frikční místa v current flow.
- **Výstup:** flagy variant, které zhorší support load.
- **AI proxy:** ⚠️ Pokud má AI přístup k ticket history, jde.

### 14. End-user proxy / User research — VOLITELNÁ (trigger)
- **Trigger:** nejasné persony, novel use case, nový segment.
- **Volitelná:** persona je dobře známá z předchozí research.
- **Vstup:** dostupné persony, research insights, JTBD framing.
- **Výstup:** flag variant, které neřeší job-to-be-done.
- **AI proxy:** ✅ Může simulovat persony na základě brief.

### 15. DevOps / Platform — VOLITELNÁ (trigger)
- **Trigger:** nový deploy footprint, nové runtime, change v infra,
  významný datový tok.
- **Volitelná:** stejný stack jako existující systém.
- **Vstup:** současná infra, deploy pipeline, observability stack.
- **Výstup:** odhad infra effort, blokující dependencies.
- **AI proxy:** ⚠️ Jen pro typické vzory, custom infra ne.

---

## Decision tree — koho pozvat?

> Použij kaskádově. Každá otázka přidá další roli, pokud je odpověď ano.

1. **Vždy:** Zadavatel (1) + PM (2) + Facilitátor (3) → core 3.
2. **Mění se UI nebo vzniká nový view?** → +Frontend (4) + UX (6).
3. **Mění se data nebo API?** → +Backend (5).
4. **Pracujeme s daty uživatelů, auth, integracemi nebo platbami?** → +Security (7) [POVINNĚ].
5. **Půjde to do produkce do měsíce?** → +QA (8).
6. **Bude to déle než 2 sprinty / je to prioritní pro PI?** → +Eng manager (9).
7. **Osobní data, marketing, AI use case?** → +Legal/GDPR (10).
8. **Public-facing nebo regulovaný (EAA)?** → +Accessibility (11).
9. **Definujeme metriku nebo A/B test?** → +Data (12).
10. **Existujicí customer base a změna ve user-facing flow?** → +Customer support (13).
11. **Persona je nejasná nebo nový segment?** → +User research (14).
12. **Mění se infra, deploy, runtime?** → +DevOps (15).

**Sanity check:** Pokud je v místnosti **>10 lidí**, je něco špatně —
buď zúžit scope, nebo udělat dvě paralelní sessions po menších buňkách.

## Kdy AI proxy vs lidský zástupce

- **Vetovací role** (Security, Eng-manager kapacita, Legal final): **vždy člověk**, AI připraví podklady.
- **Konzultativní role** (UX, Data, Accessibility, User research): **AI proxy OK**
  s human-in-the-loop review na výstup.
- **Vlastnické role** (Zadavatel, PM): **vždy člověk**, AI dělá briefing a sumarizaci.

## Otevřené otázky → expertní panel

- Chybí nějaká role? (Procurement? Marketing? Solution architect?)
- Není 15 rolí příliš/málo?
- Měla by být role **„AI strategist / vibe-coding architect"** zvlášť, nebo je to facilitator?
- Jak řešit konflikt rolí v session 1 (security veto vs zadavatel push)?
- Decision tree — chybí pravidla pro typické projektové archetypy
  (B2B SaaS, internal tool, customer-facing mobile, …)?

> Tyto otázky řeší expertní panel ve fázi 1.3.
