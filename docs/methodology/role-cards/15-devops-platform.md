Pflanzer Method | pflanzer.cz/method

# Role card #15 — DevOps / Platform

> Za 20 minut potvrdíš tři věci: (1) jak se vrátíme zpět (rollback), (2) kdo je první týden na telefonu, (3) co sledujeme první hodinu po nasazení. Podpis: `pflanzer checkpoint --slug <slug> provoz --by <jméno> --note …`.

**Krok cesty:** Provoz · **Kde jsi:** okno — checkpoint provozu 20 min u Shipu (stačí DevOps nebo EM)

Status v catalogu: **doporučená** · Kdy se zve: Změny v infra / deploy / runtime / sandbox? (téměř vždy)

## Přines do svého okna
- Rollback: jak a za jak dlouho se vrátíme (vypnutí flagu, revert)
- On-call: kdo má první týden telefon a jak ho zastihnout
- První hodina: co se sleduje (chyby, latence, metrika z Kickoffu) a kdo se dívá
- Pro hlubší kontrolu (stupeň Full): sandbox spec, approved runtime list, SLO baseline, observability contract (OTel), deploy footprint

## Podepisuješ
- Checkpoint provozu: `pflanzer checkpoint --slug <slug> provoz --by <jméno> --note …` (blokace: přidej `--blocked`)
- Promote-to-prod checklist: monitoring, strop nákladů, feature flag

## Kdy jsi u toho
- Quick (60–90 min) — **async**: triage se odkládá; sandbox a worktrees připravíš předem
- Lean (3 h) — **async**: sandbox připravíš předem, okno 20 min u Shipu
- Full (5–6 h) — **celý běh**: sandbox a footprint per varianta v Buildu

## Hlasuješ o
Skóruješ všechny 4 dimenze; effort a risk za tebe = provoz v produkci.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **effort**, **risk**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Varianta potřebuje runtime mimo approved list
- Secret v kódu nebo v promptu
- Chybí observability — výpadek v produkci nepoznáme

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Jen jako předkontrola** (ADR-0023): `--ai --agent devops-platform-expert` zapíše návrh. Throwaway stačí AI, pilot podepíše vývojář z jádra, production člověk z provozu. Sub-agent: `.claude/agents/devops-platform-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 15 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
