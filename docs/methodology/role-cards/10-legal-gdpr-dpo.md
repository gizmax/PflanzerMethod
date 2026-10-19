Pflanzer Method | pflanzer.cz/method

# Role card #10 — Legal / GDPR / DPO

> Za 20 minut potvrdíš, že varianty nezpracují osobní údaje bez právního důvodu a že tvrzení v UI jdou doložit. Podpis: `pflanzer checkpoint --slug <slug> bezpecnost --by <jméno> --note …`.

**Krok cesty:** Bezpečnost & právo · **Kde jsi:** okno — checkpoint 20 min v posledních 30 min Buildu (stačí Legal / DPO nebo Security)

Status v catalogu: **doporučená** · Kdy se zve: Osobní data, marketing, novel AI use case (≥ Limited risk-tier), nebo regulovaný produkt (PSD2/MiFID)?

## Přines do svého okna
- Jaké osobní údaje varianty zpracují a na jakém základě
- Zda je ve hře AI Act vyššího rizika nebo zvláštní kategorie dat
- Tvrzení v UI (marketing), která musí jít doložit
- Pro hlubší kontrolu (stupeň Full): RoPA, DPIA trigger checklist (GDPR čl. 35), DPA + SCC per dodavatel, AI Act risk-tier

## Podepisuješ
- Checkpoint bezpečnost & právo: `pflanzer checkpoint --slug <slug> bezpecnost --by <jméno> --note …` (blokace: přidej `--blocked`)
- Veto při vysokém riziku AI Act nebo zvláštních kategoriích dat
- Pro hlubší kontrolu (stupeň Full): DPIA podepsaná DPO a právní základ per funkce

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
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Jen jako předkontrola** (ADR-0023): `--ai --agent legal-gdpr-expert` zapíše návrh; u pilotu a produkce podepíše člověk do 48 h. Vysoké riziko AI Act a zvláštní kategorie vždy člověk. Sub-agent: `.claude/agents/legal-gdpr-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 10 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
