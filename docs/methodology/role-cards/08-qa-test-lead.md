Pflanzer Method | pflanzer.cz/method

# Role card #8 — QA / Test lead

> Jakmile padne „produkce“ nebo „pilot“, hlídáš, že varianty mají testovatelné chování, ne jen UI.

Status v catalogu: **povinná při triggeru** · Kdy se zve: Jakákoli zmínka 'produkce' nebo 'pilot' v output?

## Přines do Session 1
- Test strategy a regression inventory
- Kritické flows, které se nesmí rozbít
- Contract test framework (Pact) a automation framework
- Seed akceptačních scénářů `tests/acceptance/<slug>.feature`

## Podepisuješ
- 3–5 BDD / Gherkin scénářů s ≥ 1 negative path per varianta
- P2P (prototype-to-prod) checklist, 9 položek
- Lidský review každého AI scénáře před CI

## Kdy jsi v místnosti
- Quick (60–90 min) — **async**: Gherkin seed a P2P checklist v mezi-session okně
- Lean (3 h) — **async**: scénáře připravíš před session, review v mezi-session okně
- Full (5–6 h) — **celá session**: ve wrap-upu Gherkin seed per varianta

## Hlasuješ o
Skóruješ všechny 4 dimenze; tvůj pohled: jde variantu otestovat a kolik to stojí.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **risk**, **effort**. K tomu commitment level 0–3 pro mezi-session práci.

## Okamžitě hlas
- Varianta nemá žádný negative path scénář
- Acceptance scénáře v diff walkthrough neprojely, a přesto se hlasuje
- AI testuje implementaci místo chování

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ AI generuje testy, každý scénář ale před CI reviewuje člověk. Sub-agent: `.claude/agents/qa-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 8 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
