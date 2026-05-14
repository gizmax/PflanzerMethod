# Autoresearch — Mob Mode (vs paralelní dvojice)

> Status: research v1 · 2026-05-14 · branch `research/mob-mode`

## Otázka

Aktuální Pflanzer flow předpokládá **3 paralelní dvojice** v 3 worktrees,
každá staví jednu variantu (A/B/C). Tom navrhuje alternativu:

> **Všech 6 lidí sedí dohromady, dívají se na 1 monitor, společně vibe-codí
> CC instance a dělají několik návrhů sekvenčně.**

Otázka: kdy je tato "mob mode" varianta lepší než paralelní 3 dvojice?
Jak by měla vypadat v `/pflanzer` wizardu?

## Cíle (mechanické metriky)

- **Shared understanding**: % lidí v místnosti, kteří umí vysvětlit winning
  variantu hodinu po session (paralelní = ~33 %, mob ~80 %)
- **Decider preference dispersion**: standard deviation Decider preference
  scores per variant (paralelní = vysoká divergence, mob = nižší)
- **Wall-clock variants/session**: paralelní = 3, mob = 2-3 sequential v 90 min
- **Per-person engagement**: % session active vs passive observation
  (paralelní = 100 %, mob = ~16 % active driving / 84 % observing)
- **Knowledge transfer post-session**: count technical questions z týmu po session
  (paralelní = vysoký pro non-driving roles, mob = nízký)

## Anti-cíle (no-go)

- "Mob = consensus driven" → groupthink, tichý nesouhlas, HiPPO override
- "Senior staví, ostatní koukají" → 5 lidí = expensive observers
- 6 lidí 90 minut = 9 person-days, marginální output 1-2 varianty = bad ROI

## Scope

**V scope:**
- Mob protocol: driver/navigator rotation, time-boxing per varianta
- Wizard mode select v `/pflanzer` (paralelní vs mob)
- `worktree.py setup --mob` = 1 worktree místo 3, sequential variants
- Voting flow: mob nemá A/B/C voting jak ho známe (jiný formát)
- Cognitive limits: 6 lidí × 90 min na 1 obrazovce — co o tom víme

**Mimo scope:**
- Replace paralelní mode (existuje pořád, mob je opt-in)
- Hybrid mode (3 dvojice + sync revue) — možná v3
- Remote mob (rozdílné time zones) — tato research je in-room

## 4 expert perspektivy (paralelně, 1 wave)

1. **Mob-programming expert** — Woody Zuill / Llewellyn Falco lineage,
   10+ let mob practice, ví co funguje vs co bombing
2. **Facilitator-of-large-groups expert** — D&D dungeon master / improv
   teacher / coach pro 6+ lidí na live decision
3. **Cognitive load expert** — UX-research / education psychology, ví
   o pozornostní křivce 6 lidí × 90 min na 1 obrazovce
4. **Vibe-coding pragmatist** — real-world CC user, prošel s týmem oba
   módy, ví ROI per-osoba

## Output formát per perspektiva

Každý expert vrátí markdown v `docs/research/mob-mode/perspectives/<slug>.md`:

1. **TL;DR** (3 bullets)
2. **Kdy mob mode > paralelní** (decision criteria)
3. **Kdy paralelní > mob** (counter-criteria)
4. **Mob-specific pitfalls** (co se rozbije)
5. **Concrete protocol design** (timing, role rotation, breakpointy)
6. **Integration s Pflanzer** (jak by to vypadalo v wizardu)

## Synthesis

Po wave: `docs/research/mob-mode/synthesis.md`:
- Decision tree "kdy který mode"
- Concrete protocol pro mob (time-boxed driver rotation, breakpointy, voting)
- Wizard changes pro `/pflanzer` (mode select)
- Worktree.py changes (`--mob` flag → 1 worktree)
- Konflikty mezi perspektivami + resolution
- Punt list (pure-research perspektivy bez actionable změny)
