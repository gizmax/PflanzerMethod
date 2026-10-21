# Changelog

**Pflanzer Method | pflanzer.cz/method**

Formát: [Keep a Changelog](https://keepachangelog.com/cs/1.1.0/), verze metody
a toolu jsou společné.

## [0.6.0] — 2026-10-21

Kickoff jednou otázkou a cesta, kterou jde projít celou z terminálu.
Zpřesněno na sérii pilotů (PR #27–#38).

### Metoda
- **„Jak vážné to je?“** — jediná otázka Kickoffu (demo / pilot / ostré
  + osobní údaje). Z odpovědi se odvodí stupeň Quick / Lean / Full, okna
  a prahy; `personal_data: true` = třída dat aspoň L3, `false` = L2.
- **Okna podle vážnosti:** demo žádná; pilot bez osobních dat Zadání + jedno
  sloučené okno **Bezpečnost a provoz**; s osobními daty Zadání, Bezpečnost
  & právo, Provoz; Právo (DPIA) samostatně jen u Full, když triage DPIA
  odloží. Zadání podepisuje Decider (v Kickoffu s metrikou a kill kritériem
  samo); AI návrh nikdy nepřepíše podpis člověka (ADR-0023).
- **Závažnost** Kritické / Důležité / Drobné; prahy Shipu a závaznosti
  zdůvodněny v ADR-0024.
- **Skóre jako věta:** „Skóre X ze 100 z N automatických kontrol“, částečné,
  když část kontrol neproběhla; neměří splnění zadání.
- Retro měří **dny od Go do merge**.
- Dokumentace sjednocena: `00-tldr.md`, `00-lean-pflanzer.md` a `zacni.md`
  popisují stejnou cestu; „Async“ se jmenuje Sběr feedbacku (Async).

### Tool
- Cesta: `start` → `build` → `record` (dřív `vote`) → `share` → sběr
  feedbacku → `decide` → `ship` → `retro measure` → `report`.
- `pflanzer start --spec` — Kickoff bez Claude Code; krátký automatický slug.
- `pflanzer share` — preview variant i hub na jedné adrese, heslo zvlášť,
  hotová zpráva kolegům s termínem (`--deadline`); `share down` vše ukončí.
- `pflanzer feedback add --by`, `feedback_pull` (souhrn + kdo ještě mlčí),
  `decide prep|resolve`, `build --builder manual|claude-code|…`.
- `pflanzer ship` sám vyrobí `SHIP.md` a text PR a vypíše `gh pr create`;
  `retro measure` bere `--pr-url` nebo `--merge-commit`.
- `pflanzer report summary` (stránka pro vedení) a `report portfolio`
  (tabulka přes projekty, `--csv`).
- Okno `checkpoint … bezpecnost-provoz` (aliasy `bezpecnost`, `provoz`).

### Výstupy
- Lidský výstup všech příkazů s „Doporučením“ a jedním dalším krokem;
  závažnost a skóre ve stejných větách v CLI, hubu, PR i `SHIP.md`.
- Opravy z řady pilotů na různých stacích (Vite SPA, Express, Go, FastAPI,
  Next.js, multi-repo, mob).

### Hub
- Pohled podle role (co má kdo posoudit), kdo ještě chybí, okna s hotovým
  příkazem k podpisu, tiché hlasování (informativní), termín feedbacku.

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
