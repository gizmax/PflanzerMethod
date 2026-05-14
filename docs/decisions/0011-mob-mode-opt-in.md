# ADR-0011 — Mob mode jako opt-in alternativa k paralelním dvojicím

> Status: Accepted · 2026-05-14
> Autor: research/mob-mode autoresearch (4 perspektiv) → synthesis
> Související ADR: 0009 (Worktree v target repu), 0010 (SHIP.md primary handoff)

## Kontext

Aktuální Pflanzer flow předpokládá 3 paralelní dvojice v 3 worktrees, každá
staví variantu A/B/C nezávisle. Tom navrhl alternativu: **6 lidí dohromady
u 1 monitoru, mob style, sequential iterations**.

4-perspektivní autoresearch (mob-coach, facilitator, cognitive-load,
vibe-coding-pragmatist) prokázal:

- **Konsenzus**: mob = legitimní opt-in pro ~20-30 % případů, ne replacement
- **Konsenzus**: 6 lidí v mobu je ZA hranou (Hunter Industries 4-5 cap,
  cognitive 70/30 air-time inequity v 6+ skupinách)
- **Konsenzus**: voting flow (per-variant dot voting) v mobu nefunguje —
  všichni stavěli všechny iterations, identifikují se s každou
- **Konsenzus**: Decider physically off-table + mute kontrakt POVINNÝ
  (jinak HiPPO amplifikováno 6× vs paralelní silent-vote-last)

## Rozhodnutí

1. **Default mode = `parallel`** (3 dvojice, 3 worktrees, A/B/C). Mob =
   explicit opt-in přes `--mode mob` (worktree.py / quick_session.py / wizard).
2. **Auto-recommend** v `recommend_mode()`:
   - Hard blocky pro mob: `production_target ≥ 70`, `risk_profile = production`,
     `room_size > 5`, veto role povinná
   - Mob-positive signály: nový tým, onboarding member, single high-stakes decision
   - Default fallback: paralelní
3. **Mob protocol** (z synthesis):
   - 1 worktree `pflanzer/<slug>-mob`, single shared branch
   - Driver/navigator/observer rotation: 6 min driver active + 2 min handoff
     = 8 min cycle (medián synthesis: Falco 4 min, Woody open, Pragmatist 5 min)
   - Observer task assignment: Voice of Decider / UX / Acceptance / QA
     (fight 18-22 min observer fatigue)
   - Hard break 25 min (cognitive-load: continuous attention biological max)
   - Decider mute kromě mid-checkpoints (HiPPO mitigation)
   - 1 deep iteration + 1 refinement = default; 3rd opt-in s warning
4. **Voting flow change**: per-iteration retrospective ("co fungovalo /
   co ne / co bys do produkce") místo dot voting per variant. Decider's
   call: ship iter1 / refine to iter2 / pivot / kill.
5. **`projects.session_mode = 'parallel' | 'mob'`** schema field, defaults
   'parallel'. Persistne mode vybraný v wizardu pro audit + retrospective.

## Konsekvence

### Pozitivní
- Tým s nově nastoupeným členem dostává mob jako onboarding tool (Hattie
  d≈0.55 peer learning effect), Pflanzer není anti-juniors-friendly
- Single high-stakes decisions (např. "ship této week, jediná volba")
  fungují v mobu lépe než tří-volbová paralelní explorace
- Cross-functional alignment v 1 commit history = jednodušší audit
- Hard-block guards chrání proti mis-use (mob v production target)

### Negativní / cost
- Wizard složitější o KROK 2.5 (jedna další otázka + auto-recommend)
- 2 prompt templates (`_render_builder_prompt` + `_render_mob_iteration_prompt`)
  = víc kódu na maintenance
- `worktree.py setup` má 2 paths (1 worktree vs 3) — víc test surface
- Voting flow rozdělený mezi paralelní a mob — Sprint 5 práce na adapted
  `record_voting()`

### Riziko: tým vybere mob ze špatných důvodů
Mitigace: hard-block guards (production target ≥ 70, room > 5, veto role)
+ explicit Decider rationale do decision logu pro override.

## Alternativy zvážené

1. **Replace paralelní mobem** — odmítnut, autoresearch konsenzus říká mob
   = narrow case, paralelní pro majority.
2. **Hybrid mode (mob → split → mob review)** — odmítnut pro Sprint 4,
   punted to v3 (komplexita facilitace + 3 perspektivy ho označily jako
   "Pareto-optimal pro 6 lidí, ale ne pro MVP").
3. **Mob jako jediná možnost pro nový tým + paralelní pro zkušené** —
   odmítnut, autoresearch říká, že rozhodnutí má být situační (per Charter
   signály), ne osobnostní.
4. **Strong-style 4-min Falco rotace** — odmítnuta, 4 perspektivy doporučily
   6-8 min cycle pro 6-osobový mob (Falco optimální pro 3-4 person mob).

## Implementační rozsah Sprint 4

- `tool/cli/worktree.py setup --mode parallel|mob`
- `tool/cli/quick_session.py recommend_mode()` + `MOB_ITERATION_ANGLES` +
  `_render_mob_iteration_prompt()` + `builder_prompts(mode=...)`
- `.claude/commands/pflanzer.md` KROK 2.5 mode select
- DB schema additive column `projects.session_mode`
- Tato ADR

Sprint 5 (next): handoff_pr.py mob-aware SHIP.md, structured retrospective
voting schema, auto-recommend signal capture v wizardu.

Sprint 6 (later): hybrid mode + T+24h shared-understanding quiz.

## Související

- Autoresearch synthesis: `docs/research/mob-mode/synthesis.md`
- Perspektivy: `docs/research/mob-mode/perspectives/{01-mob-coach,02-facilitator,03-cognitive-load,04-vibe-coding-pragmatist}.md`
- ADR-0009 (Worktree v target repu) — předpoklad pro mob (mob = 1 worktree)
- `docs/methodology/04-session-1.md` — canonical Session 1 (Sprint 5 add mob agenda)
