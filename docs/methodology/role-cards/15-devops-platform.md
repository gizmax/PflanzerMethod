Pflanzer Method | pflanzer.cz/method

# Role card #15 — DevOps / Platform

> Zastupuješ krok provoz: sandbox, cestu do produkce, deploy footprint, SLO a observability.

**Krok cesty:** Provoz · **Kde jsi:** okno — checkpoint provozu 20 min u Shipu (stačí DevOps nebo EM)

Status v catalogu: **doporučená** · Kdy se zve: Změny v infra / deploy / runtime / sandbox? (téměř vždy)

## Přines do svého okna
- Sandbox spec (Terraform modul, 24h TTL)
- Approved runtime list a secret policy (Vault + OIDC)
- Šablonu footprint estimate
- Observability contract (OTel, structured logs, tracing)

## Podepisuješ
- Checkpoint provozu: `pflanzer checkpoint --slug <slug> provoz --by JMÉNO --note …` (blokace: přidej `--blocked`)
- SLO baseline a Promote-to-prod gate checklist
- Deploy footprint TCO vítězné varianty

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
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ Jen pro typické vzory; custom infra řeší člověk. Sub-agent: `.claude/agents/devops-platform-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 15 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
