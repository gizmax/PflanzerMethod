# Synthesis — Mob Mode vs Paralelní (default)

> Status: synthesis v1 · 2026-05-14 · branch `research/mob-mode`
> Inputs: `00-brief.md`, `perspectives/01-mob-coach.md`, `02-facilitator.md`,
> `03-cognitive-load.md`, `04-vibe-coding-pragmatist.md`
> Author angle: Senior Tech Lead / Synthesis Editor — cross-perspective
> reconciliation s důrazem na actionable Pflanzer changes.

## TL;DR (5 bullets)

1. **Mob je opt-in, ne replacement.** Všechny 4 perspektivy se shodují, že
   paralelní default zůstává správný pro 70-80 % corporate use cases (pilot,
   production, brownfield, tight acceptance criteria, time-pressure, tým > 5).
   Mob je sniper rifle pro úzkou class problémů (greenfield, onboarding,
   single-stake decision, audit-grade trace, cross-functional alignment).
2. **Cognitive ceiling pro mob = 4-5 lidí.** Mob-coach (Hunter Industries
   sweet spot 4-5), Cognitive load (Falco strong-style 3-4, air-time inequity
   ~70/30 v 6+ skupině), Facilitator (rotation overhead exponenciální nad 5)
   a Pragmatist (92 % šestičlenných mobs degraduje na 3 dominantní + 3
   spectatory) konvergují. Pro 6 lidí: buď split na 2 mini-mobs po 3, nebo
   přepnout na hybrid, nebo držet paralelní.
3. **AI driver mění equation, ale nezachrání špatný setup.** CC jako
   permanent silent helper sníží cognitive load observerů (syntax nese AI,
   working memory zůstává pro intent + critique), zároveň ale vytváří nový
   bottleneck: **prompt-churn paralýza** (6 lidí 12 minut diskutuje 1 prompt)
   a **scroll-back drift** (CC vyplivne 200 LOC za 8 s, 4 lidi missnou
   polovinu). Vyžaduje strong-style + named typist + diff-summary nahlas.
4. **Realistický variant count = 1 deep nebo 2 sequential, ne 3.** Mob-coach
   "1 deep + 1 rushed", Facilitator "spolehlivě 2 / ambiciózně 3 degraded",
   Cognitive "1-2 reálně", Pragmatist "1.5 finished varianty". Pflanzer
   builder-prompts se musí přizpůsobit (iteration roadmap, ne A/B/C angles).
5. **Voting flow se MUSÍ změnit.** Per-variant dot voting v mobu nefunguje
   — všichni stavěli vše, attachment je rovnocenný. Konsenzus napříč
   perspektivami: structured retrospective ("co WORKS / co DOESN'T per
   element", "fit na acceptance", "commitment 0-3 ship-tomorrow"), Decider's
   call s veřejnou rationale. `role_preferences` schema lze re-použít, ale
   `user_value` per-element místo per-variant.

## Decision tree — kdy mob vs paralelní vs hybrid

Auto-recommend logic v `/pflanzer` wizardu (Charter signals → mode):

```python
def recommend_mode(charter: Charter, room: Room) -> tuple[str, str]:
    """Return (mode, rationale_for_decider)."""

    # Hard blocks (production)
    if charter.production_readiness_target >= 70:
        return "parallel", "Production target >= 70 — paralelní pro % LOC reuse a audit trail per varianta."
    if charter.risk_profile == "production":
        return "parallel", "Risk profile production — 3 varianty dají Decideri real choice; mob = sunk-cost commitment."

    # Hard blocks (room geometry)
    if room.size > 6:
        return "parallel", "Tým > 6 — mob se rozpadá na council + audience; paralelní škáluje lineárně."
    if room.size > 5:
        return "hybrid_or_parallel", "Tým 6 = za hranou mob ceiling (4-5). Default paralelní, hybrid opt-in."

    # Veto roles
    if charter.has_veto_role(["Security", "Legal", "EM"]):
        return "parallel", "Vetovací role povinná — shadow agents v paralelním flagují real-time; mob = 70min ticho + 75min veto."

    # Mob wins
    if charter.is_greenfield and charter.cross_functional_disagreement_on_framing:
        return "mob", "Greenfield + framing disagreement — mob donutí společný mental model PŘED kódem."
    if charter.onboarding_new_member or charter.is_new_team:
        return "mob", "Onboarding / nový tým — mob = delivery + skill transfer najednou (peer learning d≈0.55)."
    if charter.single_high_stakes_decision and not charter.needs_breadth:
        return "mob", "Single-stake hluboká decision — paralelní 3 variant je over-engineering."
    if charter.audit_grade_trace_required:
        return "mob", "Audit-grade — 1 commit history, 1 chat transkript, 1 set of decisions; compliance friendly."
    if room.size <= 5 and charter.has_strong_domain_holder:
        return "mob", "Tým <= 5 + 1 senior s domain knowledge — mob = permanent navigator + observer learning."

    # Default
    return "parallel", "Default — most sessions = explorace, paralelní vždy vyhrává na ROI a variant breadth."
```

**Decider explicit confirm pro non-default**: pokud auto-recommend řekne mob a
Decider potvrdí, ale jakákoliv hard-block podmínka existuje (např. production
target ≥ 70 PLUS team manuálně chce mob), wizard musí zobrazit warning a
force re-confirm s textem rationale.

## Mob protocol design — konsenzuální verze

Sjednocený protokol napříč 4 perspektivami. Tam, kde experti divergovali,
volím **medián / safest** s rationale.

### Pre-session (15 min, mandatory)
- Decider napíše 1 odstavec "co bych chtěl vidět ve výsledku" → in-room TV
- Acceptance criteria z Charteru permanent on second screen (read-only sticky)
- Decider podepíše **mute kontrakt** (no verbal navigation during build phase)

### Session structure (90 min)

| Block | Time | Aktivita | Mode |
|-------|------|----------|------|
| Open + Frame | 0-15 | VoC ritual, 1-2-4-All framing (silent write 2 min → 2 dvojice → all → public reveal). Pokud >2 výrazně rozdílné framings → kill switch, fallback paralelní. | Facilitátor vede |
| Pre-mortem TRIZ | 15-20 | "Za 6 měsíců iter 1 selhala, proč?" silent na sticky | Facilitátor |
| **Iterace 1** | 20-50 | Strong-style mob, **6-min driver / 8-min rotation** (medián 4-min Falco / 5-min Pragmatist / 8-min Coach+Facilitator). Hard checkpoint v 35. min: máme working preview? Pokud ne, kill switch. | Mob |
| **HARD BREAK** | 50-55 | Non-negotiable. Fyzický pohyb, ne networking. Monitor fatigue real (Cognitive ref Karlin/Wright EEG). | — |
| Mid-checkpoint | 55-60 | Decider thumb up/down + 1-věta rationale. **Refine vs pivot**? Default refine. Pivot pouze pokud Decider explicit "iter 1 dead end". | Facilitátor + Decider |
| **Iterace 2** | 60-80 | Refinement (default) OR pivot (opt-in). Reset rule: bývalý driver → observer queue. Pre-mortem TRIZ 3 min před start. | Mob |
| Voting + Decider call | 80-90 | Structured retrospective (viz § Voting flow). | Facilitátor + Decider |

**Total: 90 min, realisticky 1 deep + 1 refined iter (= 2 "varianty"). 3rd
iteration je optional/skip default.**

### Role rotation cadence (8-min cyklus)

Konsenzuální cadence: **6 min driver active + 2 min handoff/checkpoint = 8 min
total**. Důvod volby: 4-min Falco je human-mob optimal, ale s CC jako
permanent silent helper potřebuje navigator čas vyložit context (Mob-coach).
8-min Falco norm je facilitator standard. 5-min Pragmatist je middle ground.
**Volím 6+2** jako synthesis: dostatečně dlouhé pro non-trivial CC interakci,
dostatečně krátké aby observer fatigue nezačala.

### Role assignments (rotující)

- **Driver** (1) — drží klávesnici, posílá prompt do CC. **Mlčí během CC outputu.**
- **Navigator** (1) — myslí 1-2 kroky dopředu, instruuje driver. Po CC outputu
  POVINNĚ čte diff summary nahlas (2 věty). Anti scroll-back drift.
- **Observers s explicit task** (2-3):
  - **Timekeeper**: hlásí 1 min do rotace
  - **Tester / Acceptance guardian**: ověřuje proti Gherkin scénářům
  - **Risk-watcher / Skeptic**: forced devil's advocate, sticky každý smell
  - **Researcher**: paralelně grepuje repo, hledá podobné komponenty
  - **Scribe**: decision log v real-time
- **Decider** (1) — **fyzicky mimo stůl** (observer chair, 1.5 m za týmem),
  **mute** během build phase, parking-lot otázky pouze po iter-end, hlasuje
  poslední, rationale POVINNÝ při override.

### Voting flow — structured retrospective (NE per-variant dot voting)

Konsenzuální schema napříč Mob-coach + Pragmatist + Facilitator:

```
AskUserQuestion (per role, 1× per iteration):
  "Co z iterace {N} FUNGUJE? Vyber 1-2 prvky." [multiSelect]
  "Co z iterace {N} NEFUNGUJE? Vyber 1-2 prvky." [multiSelect]
  "Která iterace nejlépe odpovídá Acceptance criteria?" [single: iter1/iter2/combined]
  "Pokud bys měl(a) tohle shippnout zítra do produkce, commitment 0-3?" [single]

AskUserQuestion (Decider, last):
  "Final ship — iter1, iter2, combined merge, nebo Iterate/Kill?" + rationale (POVINNÉ)
```

Persist do `role_preferences` tabulky: `user_value` per-element parsed
("WORKS: X,Y / DOESNT: Z"), `commitment_level` per-iteration, `rationale`
text. Decider call do `audit` log s `decider_mute_audit: bool`.

### Breakpointy / kill switches

- **35. min** (15 min do prvního break): pokud nemáme working preview iter 1
  → kill switch, rozpadnout na 2 mini-mobs po 3 nebo přejít na 2 dvojice
- **Frame disagreement >2** (po 1-2-4-All v 15. min): kill switch, fallback paralelní
- **Decider verbal navigation breach** (audit log): warning, ne kill, ale do retrospective
- **AI dead-end loop** (CC se zacyklí 3× za sebou): commit checkpoint na separátní
  branch, restart prompt s explicit alternative approach

### CC-specific rules (Pragmatist + Coach konsenzus)

- **Prompt Driver má 60 s na napsání + odeslání**, jinak diskutujeme až output
  (anti prompt-churn paralýza)
- **Žádný "let's see what CC thinks"** bez explicit human navigator hypothesis
- **Commit checkpoint každých 15 min** na separátní branch
  `pflanzer/<slug>-mob-cp-<N>` — anti single-thread context loss
- **Driver MUSÍ koukat na TV, ne na vlastní laptop** (zoom 150 % v terminálu,
  bezdrátová klávesnice na stůl) — anti TV-vs-laptop ergonomic split

## Konflikty + resolution

### Konflikt 1 — Variant count realism

| Perspektiva | Pozice |
|---|---|
| Brief | "2-3 sequential v 90 min" |
| Mob-coach | "1 deep + 1 rushed" — brief je optimistic |
| Facilitator | "spolehlivě 2 / ambiciózně 3 degraded" |
| Cognitive | "1-2 reálně" |
| Pragmatist | "1.5 finished varianty" |

**Resolution**: dokumentovat jako **1 deep iteration + 1 refinement iteration =
2 sloty default**. 3rd iteration je opt-in s explicit warning v wizardu
("ambiciózně, riziko degraded quality"). `MOB_ITERATION_ANGLES` v
`quick_session.py` má 2 entries default, 3rd s `optional=True` flag.

### Konflikt 2 — Decider physical location

| Perspektiva | Pozice |
|---|---|
| Mob-coach | "Decider u stolu OK, jen mute, hlasuje poslední" |
| Facilitator | "**Fyzicky mimo stůl** (observer chair 1.5 m), mute kontrakt POVINNÝ" |
| Cognitive | "Decider 90 min v dění = decision fatigue, glucose-depleted v voting fázi" |
| Pragmatist | "Mute kromě mid-checkpoints; Decider zapojený = HiPPO" |

**Resolution**: konsenzus 3:1 — **Decider fyzicky mimo stůl, observer chair
1.5 m za týmem, mute kontrakt POVINNÝ**, parking-lot otázky pouze po iter-end.
Implementace: `mute_contract_signed: bool` field v session metadata, audit log
zaznamenává každý verbal navigation breach.

### Konflikt 3 — Rotation cadence

| Perspektiva | Pozice |
|---|---|
| Mob-coach | "6-min driver / 2-min ask CC / rotace 8 min" |
| Facilitator | "8-min hard cap (Falco norm)" |
| Cognitive | "Rotation < 10 min, optimum 7-10" |
| Pragmatist | "5-min cycle" |

**Resolution**: **6 min driver active + 2 min handoff/checkpoint = 8 min total
cycle**. Důvod: synthesis mediánu, dostatečně dlouhé pro CC interakci,
dostatečně krátké aby observer fatigue (12 min onset) nezasáhla.
`worktree.py --mode mob` injectne timer notifikaci každých 8 min.

### Konflikt 4 — Mob size cap

| Perspektiva | Pozice |
|---|---|
| Mob-coach | "≤ 5 hard, 6 = odpoj 1-2 do scribe/observer" |
| Facilitator | "Sweet spot 4, max 5; 6 = rozdíl na 2 mini-mobs" |
| Cognitive | "4 ideal, 5 max; 6 = vždy hybrid" |
| Pragmatist | "≤ 5 lidí + ≥ 1 CC-fluent; nad 5 council+audience" |

**Resolution**: **mob hard cap = 5 lidí**. Pro 6+ wizard auto-recommends
hybrid (Sprint 6) nebo paralelní. Implementace: `room.size > 5` v
`recommend_mode()` vrátí `hybrid_or_parallel`, ne `mob`.

### Konflikt 5 — Hybrid mode viability

| Perspektiva | Pozice |
|---|---|
| Mob-coach | "Mob → 2 mini-mobs split — viable v iterace 2" |
| Facilitator | "Hybrid v3, defer (komplexita facilitace)" |
| Cognitive | "**Hybrid je Pareto-optimal pro 6 lidí**" (mob explore → split → mob review) |
| Pragmatist | "Hybrid v3 — TBD, disabled" |

**Resolution**: **hybrid je teoreticky nejlepší pro 6 lidí, ale punt do
Sprint 6** (komplexita facilitace + worktree management). V wizardu zobrazit
jako disabled option s tooltipem "v3 — coming". Pro Sprint 4 dostačí mob ≤ 5
+ paralelní default.

## Pflanzer integration — concrete file changes

### 1. `/pflanzer` wizard (`.claude/commands/pflanzer.md`)

**Přidat KROK 2.5 — MODE SELECT** (mezi KROK 2 Decider+Room a KROK 3 Risk Profile):

```markdown
## KROK 2.5 — Mode select

Před bootstrap zeptat se týmu na working mode. Auto-recommend z Charteru
signálů (viz `recommend_mode()` v `tool/cli/quick_session.py`).

AskUserQuestion:
  question: "Jak budete dnes pracovat?"
  description: "{auto_recommend_rationale}"
  options:
    - "Paralelně (3 dvojice, 3 worktrees, A/B/C angles)" [default pokud not mob]
    - "Mob (1 obrazovka, sequential iterations, ≤ 5 lidí)" [default pokud mob]
    - "Hybrid v3 — coming Sprint 6" [disabled]

Pokud user vybere mob a hard-block existuje (production target ≥ 70, team > 5,
veto role povinná), force re-confirm s warning.
```

### 2. `tool/cli/worktree.py`

Přidat `--mode parallel|mob|hybrid` flag (default `parallel`) do `setup` subcommand.

V `_create_worktrees()` (current `worktree.py:121-155`):

```python
def _create_worktrees(slug: str, mode: Literal["parallel", "mob"] = "parallel"):
    if mode == "mob":
        variants = ("mob",)
        # 1 worktree, 1 branch pflanzer/<slug>-mob, 1× npm install
    else:
        variants = ("A", "B", "C")
        # 3 worktrees, branches pflanzer/<slug>-{A,B,C}
    for variant in variants:
        ...
```

CLI:
```bash
python tool/cli/worktree.py setup --slug X --mode mob
# → 1 worktree místo 3 (3× rychlejší setup, 1 npm install)
```

### 3. `tool/cli/quick_session.py`

**Nové konstanty** (po current `VARIANT_ANGLES` na :314-318):

```python
MOB_ITERATION_ANGLES = (
    ("iter1", "first stab", "Rough first stab implementace, happy-path. "
     "Tým společně exploruje řešení, AI je permanent silent helper. "
     "Cíl: working preview do 35. min."),
    ("iter2", "refinement", "Refinement iter1 NEBO pivot pokud Decider call. "
     "Default refine: polish UX, edge cases, acceptance pass. "
     "Pivot pouze pokud iter1 dead-end."),
    # iter3 optional, opt-in v wizardu s warning
)
```

**`builder_prompts(mode="parallel")` parameter**:

```python
def builder_prompts(slug, hook, *, mode: Literal["parallel", "mob"] = "parallel", n=3):
    if mode == "mob":
        return [_render_builder_prompt_mob(slug, hook, iter_idx=i)
                for i in range(min(n, len(MOB_ITERATION_ANGLES)))]
    return [_render_builder_prompt(slug, hook, variant=v) for v in VARIANT_ANGLES[:n]]
```

**`_render_builder_prompt_mob()`** — nová funkce, vychází z current
`_render_builder_prompt()` (`quick_session.py:411-460`):

- `{variant}` → `{iteration}` v textu (sémantika "verze v čase")
- "Tvoje dvojice" framing → "Tvoje session (mob, ≤ 5 lidí u 1 TV)"
- Iteration history: "Toto je iterace {N}. Předchozí iterace: {summary iter N-1}.
  Co měníme: {diff_intent}."
- **Scroll-back guard**: "Po každém change vypiš 2-větný diff summary nahoře
  v odpovědi. Tým to čte nahlas před dalším promptem."
- **Single branch**: `pflanzer/{slug}-mob` (iterations = git commits, ne branches)
- **Acceptance .feature gate per iteration**: CC po každé iteraci spustí
  `.feature` runner a vypíše pass/fail
- **Rotation reminder**: "Driver rotuje každých 8 min, ne task-based"
- **Commit checkpoint**: "Každých 15 min commit na `pflanzer/{slug}-mob-cp-{N}`"

**`record_voting()` adapted**:

- Per-iteration retrospective vs per-variant scoring
- New schema: `works_elements: list[str]`, `doesnt_work_elements: list[str]`,
  `acceptance_fit: enum(iter1|iter2|combined)`, `commitment: int 0-3`
- Persist do existující `role_preferences` table, `rationale` field obsahuje
  parsed elements ("WORKS: X, Y / DOESNT: Z")

### 4. `tool/cli/handoff_pr.py` + `handoff.py`

**SHIP.md mob mode**:

- Section "Varianty" → "Iterations" (1 winning iteration + history of pivots)
- New section "Retrospective summary" — aggregated WORKS/DOESN'T elements per role
- Audit log: 1 commit history (linear) vs 3-merge (paralelní)
- `decider_mute_audit: bool` field shown in handoff metadata

**`render_handoff()` (current `quick_session.py:572-715`)** detect mode z
session metadata, dispatch:

- `mode == "parallel"`: existující path
- `mode == "mob"`: render mob-specific SHIP.md s "Iteration timeline" místo
  "Variant comparison"

### 5. New docs

- **`docs/methodology/04-session-1.md`** — přidat sekci "Mob variant of agenda"
  (cca 200 řádků): kdy použít, mob protocol detail, pre-session checklist,
  voting flow změna. Reference na `docs/decisions/0011-mob-mode-opt-in.md`.

- **`docs/decisions/0011-mob-mode-opt-in.md`** — ADR:
  - Kontext: brief otázka mob vs paralelní
  - Varianty: (a) mob default, (b) paralelní default + mob opt-in,
    (c) hybrid default
  - Rozhodnutí: **(b) paralelní default, mob opt-in s hard-block guards**
  - Důsledky: wizard mode select, worktree.py --mode flag,
    quick_session.py builder_prompts mode param, voting schema dispatch,
    handoff dispatch. Sprint 5: auto-recommend signals + handoff.
    Sprint 6: hybrid mode + measurement loop.

## Punt list

Things 1-2 perspectives mentioned but not making top changes:

- **Hybrid mode** (mob 25-30 min framing → split paralelní 30-45 min →
  mob review 20-30 min) — Cognitive ref jako Pareto-optimal pro 6 lidí,
  ale Facilitator + Pragmatist označili "v3 defer" kvůli komplexitě
  facilitace + worktree state management. **Punt → Sprint 6.**

- **T+24h shared-understanding quiz** (Mob-coach navrhuje auto-generated quiz
  3 otázky po handoffu, self-score 0-3 do `audit` jako `mob.knowledge_check`).
  Karpathyho autoresearch metric loop pro empirické měření mob vs paralelní.
  **Punt → Sprint 6** jako measurement instrumentation.

- **Remote mob** (různé time zones, async mob) — explicitně out-of-scope brief,
  ale Pragmatist krátce zmínil. **Punt → out of v1-3 scope.**

- **Mob mode pro Session 1 odpolední slot** — Cognitive explicitně varuje
  "po obědě NIKDY mob, group focus span klesá na ~15 min". Zachovat jako
  pravidlo v `04-session-1.md` rozšíření, ale není top change.

- **TV size + font requirements** (Cognitive ref Legge 1997: TV ≥ 65", font
  ≥ 16pt, max 3 lidé per stranu). Patří do `docs/methodology/03-room-setup.md`
  pre-session checklist, ne do toolu.

- **Decision fatigue mitigation** (Decider glucose-depleted v 90. min voting
  fázi). Cognitive navrhuje 5 min mandatory snack break před voting.
  Nice-to-have, ne top change.

- **Lens assignment per varianta** (Facilitator: "varianta A optimalizováno
  pro UX lens, B pro BE, C pro QA" jako anti-groupthink). Sofistikovaná, ale
  v 2-iteration mob mode marginal. Punt do v3.

## Implementation order

### Sprint 4 (this commit) — MVP mob mode opt-in
1. **`/pflanzer` wizard**: KROK 2.5 mode select s default paralelní + mob opt-in
2. **`worktree.py`**: `--mode parallel|mob` flag, 1 worktree pro mob
3. **`quick_session.py`**: `builder_prompts(mode=...)` parameter,
   `MOB_ITERATION_ANGLES` constant, `_render_builder_prompt_mob()` function
4. **`docs/decisions/0011-mob-mode-opt-in.md`**: ADR schválena
5. **Hard-block guards**: production target ≥ 70 + team > 5 + veto role →
   force re-confirm warning

### Sprint 5 (next)
1. **`handoff.py`**: SHIP.md mob-aware (Iterations section, retrospective summary)
2. **`record_voting()`**: structured retrospective schema (WORKS/DOESN'T per
   element, acceptance fit, commitment)
3. **`recommend_mode()`**: auto-recommend logic z Charteru signálů
4. **`docs/methodology/04-session-1.md`**: mob variant of agenda
5. **Decider mute audit**: `mute_contract_signed: bool`, breach logging

### Sprint 6 (later)
1. **Hybrid mode** (mob → split → mob review): wizard option, worktree
   state management, handoff merger
2. **T+24h knowledge-check quiz**: auto-generated 3 otázky, self-score,
   `audit.mob.knowledge_check`
3. **Measurement instrumentation**: shared understanding %, Decider
   preference dispersion SD, per-person engagement % — empirické
   srovnání mob vs paralelní po 5-10 sessions
4. **Lens assignment per iteration** (anti-groupthink sofistikace)

---

## Reference (cross-perspective claims)

- Hunter Industries mob sweet spot 4-5 (Mob-coach, Cognitive)
- Falco strong-style 3-4, mob-timer 8 min (Mob-coach, Facilitator)
- Group attention 18-22 min, observer fatigue ~12 min (Cognitive ref
  Karlin/Wright EEG, Robertson SART)
- Air-time inequity 70/30 v 6+ skupině (Cognitive, Facilitator ref Bales/Cooney)
- Working memory 4±1 (Cognitive ref Cowan), Cognitive Load Theory (Sweller,
  Kirschner Collaborative CLT)
- Peer learning d ≈ 0.55, observation learning d ≈ 0.40 (Cognitive ref Hattie)
- Asch conformity replikováno code review kontextu (Facilitator ref Bavota 2015)
- Anchoring bias design context (Facilitator ref Hallihan/Shu 2012)

---

*Synthesis end. Implementation starts Sprint 4 commit.*
