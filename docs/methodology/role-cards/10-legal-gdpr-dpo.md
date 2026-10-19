Pflanzer Method | pflanzer.cz/method

# Role card #10 — Legal / GDPR / DPO

> Zastupuješ krok bezpečnost & právo z právní strany: osobní data, marketing claims a AI Act risk-tier.

**Krok cesty:** Bezpečnost & právo · **Kde jsi:** okno — checkpoint 20 min v posledních 30 min Buildu (stačí Legal / DPO nebo Security)

Status v catalogu: **doporučená** · Kdy se zve: Osobní data, marketing, novel AI use case (≥ Limited risk-tier), nebo regulovaný produkt (PSD2/MiFID)?

## Přines do svého okna
- RoPA a DPIA trigger checklist (GDPR čl. 35/3)
- AI Act risk-tier klasifikaci use casu
- DPA + SCC per vendor (včetně AI builderu)
- Marketing compliance brief, pokud jsou ve hře claims

## Podepisuješ
- Checkpoint bezpečnost & právo: `pflanzer checkpoint --slug <slug> bezpecnost --by JMÉNO --note …` (blokace: přidej `--blocked`)
- Legal & privacy triage (≥ 2 DPIA triggery = Build odložen)
- DPIA podepsaná DPO a legal basis per feature; veto při high-risk AI Act nebo special category datech

## Kdy jsi u toho
- Quick (60–90 min) — **async**: checkpoint se odkládá — podepíšeš ho před pilotem
- Lean (3 h) — **async**: checkpoint 20 min + 1-page checklist místo účasti v Buildu
- Full (5–6 h) — **celý běh**: senior delegát; pre-read 48 h předem

## Hlasuješ o
Skóruješ 4 dimenze; právní blocker nepatří do skóre, ale do veto registru.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **risk**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Osobní data bez legal basis nebo s ≥ 2 DPIA triggery
- Marketing claim, který nejde doložit
- AI use case ≥ High risk-tier v Quick / Lean stupni

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ AI zvládne L1/L2 data a minimal / limited risk; high-risk AI Act, special categories a profiling podepisuje lidský DPO. Sub-agent: `.claude/agents/legal-gdpr-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 10 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
