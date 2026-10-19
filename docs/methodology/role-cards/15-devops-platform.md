Pflanzer Method | pflanzer.cz/method

# Role card #15 — DevOps / Platform

> Zajišťuješ sandbox a cestu do produkce — deploy footprint, SLO a observability.

Status v catalogu: **doporučená** · Kdy se zve: Změny v infra / deploy / runtime / sandbox? (téměř vždy)

## Přines do Session 1
- Sandbox spec (Terraform modul, 24h TTL)
- Approved runtime list a secret policy (Vault + OIDC)
- Šablonu footprint estimate
- Observability contract (OTel, structured logs, tracing)

## Podepisuješ
- Platform triage (sandbox provisioning, runtime approval)
- SLO baseline a Promote-to-prod gate checklist
- Deploy footprint TCO per varianta

## Kdy jsi v místnosti
- Quick (60–90 min) — **async**: triage je deferred; sandbox a worktrees připravíš předem
- Lean (3 h) — **async**: sandbox připravíš předem, footprint review mezi sessions
- Full (5–6 h) — **celá session**: sandbox a footprint per varianta

## Hlasuješ o
Skóruješ všechny 4 dimenze; effort a risk za tebe = provoz v produkci.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **effort**, **risk**. K tomu commitment level 0–3 pro mezi-session práci.

## Okamžitě hlas
- Varianta potřebuje runtime mimo approved list
- Secret v kódu nebo v promptu
- Chybí observability — výpadek v produkci nepoznáme

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ Jen pro typické vzory; custom infra řeší člověk. Sub-agent: `.claude/agents/devops-platform-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 15 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
