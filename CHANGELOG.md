# Changelog

**Pflanzer Method | pflanzer.cz/method**

Formát: [Keep a Changelog](https://keepachangelog.com/cs/1.1.0/), verze metody
a toolu jsou společné.

## [0.5.0] — 2026-10-19

Malá skupina, celá cesta. Navenek `/pm` a 5 kroků, pod povrchem robustní tool.

### Metoda
- **6 kroků cesty, každý se jménem** (byznys, produkt, design, vývoj,
  bezpečnost & právo, provoz); krok bez jména = Kickoff se nesvolává (ADR-0021).
- **Jádro 3–4 lidé + okna** (Decider 15 min + Rozhodnutí, checkpointy
  bezpečnost & právo a provoz po 20 min), max 5 lidí naráz.
- Jeden průběh: Kickoff → Build (3 h) → Async (3–5 dní) → Rozhodnutí → Ship
  → handoff → retro; ~6–8 PD. Stupně Quick / Lean / Full pod povrchem
  (ADR-0017), default = Lean.
- Inspirace z trhu (ADR-0022): `CONSTITUTION.md` v target repu, připravenost
  repa, kdy metodu nepoužít, decision log v repu, kontroly během Buildu,
  rozšířený checkpoint bezpečnosti (egress, tokeny, prompt injection),
  měření pilotů. Srovnání: `docs/research/srovnani-metod-2026.md`.
- Audit-grade vrstva přesunuta do `docs/governance/`.
- Nové vstupní dokumenty: `docs/zacni.md` (první pilot), `docs/postup.md`
  (diagram průběhu, kde varianty fyzicky jsou).

### Tool
- Instalace jako Claude Code plugin (`install.sh` → `pflanzer@pflanzer-method`),
  CLI `pflanzer` funguje z libovolného repa.
- Nové příkazy: `pflanzer doctor` (připravenost repa), `pflanzer status`
  (fáze + jeden další krok), `pflanzer feedback add|list` (offline feedback),
  `pflanzer checkpoint` (podpis oken = triage pro Ship), `pflanzer hub`
  (web hub jedním příkazem, sdílí DB s CLI).
- Rozhodnutí: Go vyžaduje vítěze, otevřený critical na vítězi blokuje Go
  (resolve / override s důvodem), Iterate max 1×, decision log do
  `.pflanzer/decisions/<slug>.md` v target repu.
- Ship: gates jen na vítěze, stack-aware, skóre X/100, práh pilot 80 /
  production 85; adaptér `pflanzer.gates.yml`; triage hard gate.
- Handoff: metriky pilotu + „Změř po 30 dnech" napojené na `/pm retro`.
- Jedna datová složka `~/.pflanzer` (`PFLANZER_DATA`), timezone-aware hub.
- Sloučeno s auditem N1–N18: testy + CI, retro, role cards, AI provenance,
  AI náklady, více target repo, PdM konvence.

### Úklid
- ADR číslování jednoznačné: 0010 SHIP.md, 0016 mob mode, 0017 mezi-session okno.
- Případová studie a identifikující údaje pilotu odstraněny.

## [0.4] a starší

Viz git historie a ADR 0001–0020.
