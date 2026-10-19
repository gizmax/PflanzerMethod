# ADR-0021 — Malá skupina, celá cesta (v0.5)

**Status:** Accepted (v0.5)
**Date:** 2026-10-18
**Context source:** Zkušenost z pilotů (Tom, 2026-10-18) + rešerše praxe
AI-asistovaného vývoje 2025–2026 + interní audit konzistence dokumentace.
**Supersedes (partial):** `00-lean-pflanzer.md` v0.4 (sestava 6–7 lidí,
všichni na všem), README Quick start (3 sessions), význam „Session 3".
**Nemění:** ADR-0001 (Decider, anti-HiPPO), ADR-0005 (evolve default),
ADR-0009 (worktree v target repu), ADR-0020 (Track P default).

## Kontext

1. **Zkušenost z praxe:** lépe funguje **menší skupina, ve které jsou
   zástupci všech kroků cesty** (od zadavatele po provoz), než velká
   místnost. Ne všichni musí být celou dobu.
2. **Rešerše** (detail níže v Evidence):
   - mob programming bez AI: nad 3–4 lidi zapojení klesá (lidé se sami
     vyřazují);
   - AI-asistovaný mob: odhad praktiků 4–5 lidí místo 8–9 (názor, ne data);
   - Amazon AI-DLC: celý tým validuje návrhy AI hned, cykly v hodinách až
     dnech; úzké hrdlo je rozhodování, ne psaní kódu;
   - security se v AI-native týmech zapojuje průběžně v kontrolních bodech,
     ne jako stálý účastník ani jako koncové schvalování;
   - DORA 2025: přínos AI určuje kvalita platformy a jasné politiky →
     automatické brány nahrazují lidi v místnosti.
3. **Audit dokumentace v0.4** našel rozpory, které tým nemá šanci vyřešit:
   Session 1 trvá 60–90 min / 3 h / 5–6 h; „Session 3" má tři významy
   (ship / iterate / zakázaná); cena 10 PD vs 32 PD; default evolve vs
   throw-away; `/pm` vs `/pflanzer-*`; 6 vs 7 vs 10 lidí.
4. **Mezera v bezpečnosti:** lean profil v0.4 vynechal Security i Legal
   z místnosti, ale zároveň slíbil „winner jde rovnou do produkce" —
   nikde nebylo řečeno, kdo a kdy produkční rizika podepíše.

## Varianty

| Varianta | Pro | Proti |
|----------|-----|-------|
| A — ponechat v0.4, jen sjednotit čísla | nejmenší změna | velká místnost zůstává; mezera v bezpečnosti zůstává |
| B — **malé jádro + okna pro zástupce kroků cesty** | sedí na praxi i rešerši; každý krok cesty má hlas; zavírá mezeru v bezpečnosti | Decider není u stavby → riziko „rozhodnutí bez kontextu" (mitigace: demo + async klikání) |
| C — jen jádro (PdM + vývojář), ostatní async | nejrychlejší | ztrácí cross-functional alignment = hlavní důvod metody |

## Rozhodnutí

**Varianta B.** Pflanzer Method v0.5 stojí na třech pravidlech:

### 1. Celá cesta je zastoupena — každý krok má jednoho pojmenovaného zástupce

Cesta nápadu do produkce má **6 kroků**:

| # | Krok cesty | Kdo typicky zastupuje (z role catalogu) |
|---|------------|------------------------------------------|
| 1 | Byznys | Zadavatel / sponzor = Decider (#1) |
| 2 | Produkt | PdM (#2) |
| 3 | Design | UX / Designer (#6) |
| 4 | Vývoj | FE / Vibe-coding lead (#4), BE / API lead (#5) |
| 5 | Bezpečnost & právo | Security (#7), Legal / DPO (#10) — jeden člověk stačí |
| 6 | Provoz | DevOps / Platform (#15), případně EM (#9) |

- Jeden člověk smí zastupovat víc kroků (např. vývojář = vývoj + provoz,
  PdM = produkt + design u interního toolu).
- **Žádný krok nesmí zůstat bez jména.** Krok bez zástupce = session se
  nesvolává (nahrazuje anti-pattern „Security/Legal vynecháno").
- Role catalog (18 pozic) zůstává jako **seznam, kdo může krok zastoupit**,
  ne jako seznam lidí v místnosti.

### 2. Jádro je malé a je tam celou dobu; ostatní přicházejí na okna

- **Jádro (3–4 lidé, celou dobu):** PdM (facilitátor, pokud není
  dedikovaný), 1–2 vývojáři jako buildeři, designér.
- **Okna (konkrétní čas nad konkrétním artefaktem):**

| Kdo | Okno | Délka | Nad čím |
|-----|------|-------|---------|
| Decider / sponzor | Kickoff | 15 min | zadání na 1 stránku: problém, metrika, kill kritérium |
| Decider / sponzor | Rozhodnutí | 60–90 min | běžící varianty + agregovaný feedback |
| Bezpečnost & právo | Checkpoint | 20 min | datový tok, data classification, diff winneru |
| Provoz | Checkpoint | 20 min | výsledek quality gates, deploy plán, monitoring |

- **Nikdy víc než 5 lidí naráz.** Více = scope je příliš široký, rozděl.
- Decider **není u stavby** (anti-HiPPO zesílené: nemůže tlačit variantu
  během vzniku) a **hlasuje poslední** (ADR-0001 beze změny).
- Zástupce v okně musí mít mandát. Kdo nemůže v okně rozhodnout, není
  zástupce.

### 3. Automatické brány místo lidí v místnosti

Co pokryje automat, nepotřebuje člověka v místnosti: sandbox (síť
default-deny, syntetická data), secret scan, závislosti/SBOM, lint, typy,
testy, a11y (axe), build. Lidé v oknech řeší jen to, co brány nepokryjí
(datový tok, právní riziko, provozní odpovědnost).

### Průběh v0.5 (jediná kanonická verze)

```
Den 0   Kickoff            15 min   Decider + jádro       zadání na 1 stránku + jména zástupců
Den 1–5 Build              3 h      jádro                 3 varianty paralelně (AI v 3 worktrees)
        Checkpoint B&P     20 min   bezpečnost & právo    v posledních 30 min Buildu nebo do 48 h
        Async              3–5 dní  všichni zástupci      klikají, komentují; builder zapracovává
Den ~7  Rozhodnutí         60–90 min Decider + jádro      Go / Iterate / Kill, Decider poslední
Den ~8  Ship               1–2 dny  vývojáři + provoz    quality gates ≥ 80/100, checkpoint provozu, PR
```

- Terminologie: **Kickoff → Build → Rozhodnutí → Ship.** Slova
  „Session 1 / Session 2" zůstávají jako synonyma pro Build / Rozhodnutí.
  **„Session 3" se nepoužívá** — Ship není session, je to práce vývojářů
  s branami. Iterate = další Build kolo (max 1×), ne třetí session.
- Effort default profilu: **~6–8 PD** (jádro 3–4 lidé × ~1,5 dne + okna
  + Ship). Čísla 10 PD / 32 PD z v0.4 jsou nahrazena.
- Uživatelský vstup: **jen `/pm`** (`/pm start`, `/pm live`, `/pm decide`,
  `/pm ship`, …). `/pflanzer-*` jsou implementace pod kapotou.

### Audit-grade vrstva → `docs/governance/`

Method Steward, Method Decider + sunset, pre-registrace, Compliance Score,
PflanzerIndex, leading indicators, AI Act Fáze A/B/C a Track S se
přesouvají z hlavní cesty do `docs/governance/` (index tam). ADR zůstávají
v `docs/decisions/` beze změny. Hlavní cesta na ně odkazuje jedním řádkem.

## Důsledky

**Pozitivní**
- Menší skupina = vyšší zapojení, rychlejší rozhodování, méně divadla.
- Každý krok cesty má hlas a jméno → zavírá mezeru „kdo podepíše produkci".
- Jedna kanonická verze průběhu a terminologie; nižší cena (~6–8 PD).

**Negativní / rizika**
- Decider vidí varianty až u Rozhodnutí → mitigace: async klikání na
  sandbox URL během Async fáze; Rozhodnutí začíná 10min demem.
- Okna vyžadují disciplínu v kalendáři → mitigace: okna se bookují na
  Kickoffu, ne ad hoc.
- Méně lidí = méně perspektiv u stavby → mitigace: AI expert sub-agenti
  (role catalog) dávají perspektivy nepřítomných rolí jako vstup, ne hlas
  (AI-only feedback deflation max 0,5 platí dál).

**Otevřené / k ověření na pilotech**
- Optimální velikost jádra (3 vs 4) a délka Buildu — měřit u každého
  pilotu: počet lidí, trvání, počet zásahů v oknech, gate score.
- Tool (`tool/cli`, DB) zatím nezná pojem „okno"; commandy ho řeší
  v promptech. Úprava schématu = samostatný krok.

## Evidence (rešerše 2026-10-18)

- Mob programming case study (3–4 lidé optimum): https://arxiv.org/pdf/1907.11352 (2019) — zkušenostní, 1 tým.
- AI mob 4–5 lidí (názor): https://blog.flurdy.com/2026/02/mob-together-when-ai-joins-the-team (2026-02).
- Amazon AI-DLC (mob elaboration/construction): https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle (2025-07).
- Velikost týmu v éře AI (LeadDev): https://leaddev.com/management/ai-has-us-asking-does-team-size-still-matter (2026-04).
- Jak týmy v Anthropicu používají Claude Code (security průběžně): https://claude.com/blog/how-anthropic-teams-use-claude-code (2025-07).
- DORA State of AI-assisted Software Development 2025: https://www.infoq.com/news/2025/09/dora-state-of-ai-in-dev-2025 (2025-09).

Tvrdá data k optimální velikosti skupiny ani k „drop-in" účasti
neexistují — model v0.5 je designové rozhodnutí podložené praxí,
ne vědecký výsledek. Proto měřit (viz Otevřené).
