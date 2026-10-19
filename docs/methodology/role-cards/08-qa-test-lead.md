Pflanzer Method | pflanzer.cz/method

# Role card #8 — QA / Test lead

> Za 20 minut v Asyncu potvrdíš, že varianty mají testovatelné chování, ne jen UI, a které scénáře se nesmí rozbít.

**Krok cesty:** Vývoj (kvalita) · **Kde jsi:** jádro nebo okno — Build (scénáře) a Ship (gates)

Status v catalogu: **povinná při triggeru** · Kdy se zve: Jakákoli zmínka 'produkce' nebo 'pilot' v output?

## Přines do svého okna
- Kritické průchody, které se nesmí rozbít
- 3–5 akceptačních scénářů s aspoň jednou chybovou cestou na variantu
- Lidskou kontrolu každého scénáře, který napsala AI
- Pro hlubší kontrolu (stupeň Full): test strategy a regression inventory, contract test (Pact), P2P checklist o 9 položkách

## Podepisuješ
- 3–5 BDD / Gherkin scénářů s ≥ 1 negative path per varianta
- P2P (prototype-to-prod) checklist, 9 položek
- Lidský review každého AI scénáře před CI

## Kdy jsi u toho
- Quick (60–90 min) — **async**: Gherkin seed a P2P checklist v Async okně
- Lean (3 h) — **async**: scénáře připravíš před Buildem, review v Async okně
- Full (5–6 h) — **celý běh**: ve wrap-upu Buildu Gherkin seed per varianta

## Hlasuješ o
Skóruješ všechny 4 dimenze; tvůj pohled: jde variantu otestovat a kolik to stojí.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **risk**, **effort**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Varianta nemá žádný negative path scénář
- Acceptance scénáře v diff walkthrough neprojely, a přesto se hlasuje
- AI testuje implementaci místo chování

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Není to krok cesty** (ADR-0023); perspektivu dodá QA expert jako vstup a každý scénář zkontroluje člověk před CI. Sub-agent: `.claude/agents/qa-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 8 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
