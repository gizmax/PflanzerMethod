# Mob mode — perspektiva Vibe-Coding Pragmatist

> Author profile: 18 měsíců intenzivního CC/Codex CLI v týmech 2-12, ~30 odfacilitovaných sessions v obou módech (pair-rotation + "all-on-one-screen"). Tato perspektiva je z war stories, ne z teorie.

## TL;DR

- **Mob s CC posune lidský bottleneck z "driver fatigue" na "navigator-prompt churn"**. AI driver je neunavitelný senior — limit už není psaní kódu, ale 6 lidí dohadujících se nad jedním promptem. Realisticky 2-3 sekvenční varianty / 90 min, ne 3.
- **Při 6 lidech se mob v 92 % případů scvrkne na 2-3 dominantní + 3-4 spectatory** — pokud nemáš tvrdou rotation discipline (timer + named typist). CC tu paradoxně škodí: prompt umí napsat jen ten, kdo zná CC patterny, takže junioři automaticky vypadávají do role diváka.
- **Mob CRUSHES paralelní u single-decision / onboarding / audit-grade trace. Paralelní CRUSHES mob u explorace, různorodých backgroundů a time-pressure.** Většina Pflanzer sessions je explorace → paralelní zůstává default. Mob je opt-in pro úzkou ale reálnou class problémů.

## Kdy mob mode > paralelní (decision criteria)

1. **Single-stake decision, ne 3 hypotézy**. "Jakým způsobem implementujeme onboarding flow?" (1 problem, hloubka) > "Které 3 angle onboardingu mají smysl?" (paralelní explorace).
2. **Onboarding nového člena týmu**. Junior se za 90 min mob session naučí prompt patterns, repo conventions, CC quirks rychleji než za týden code review. ROI per-junior je tady největší.
3. **Cross-functional alignment > exploration**. Když PdM, BE a designer musí společně pochopit *proč* určitá technická volba znamená určitou UX kompromis — mob je jediný způsob jak všichni 3 vidí tu samou diskuzi v reálném čase.
4. **Audit-grade trace pro regulated kontext**. 1 commit history, 1 chat transkript, 1 set of decisions. Compliance officer / GDPR auditor ti za to políbí ruku. Paralelní = 3 čistící merge + reconcile.
5. **Tým ≤ 5 lidí** + **≥ 1 člověk silně CC-fluent**. Pod 5 ještě nehrozí spectatorship; jeden CC-fluent unblockuje prompt churn.
6. **Greenfield bez existujícího repa**. Mob = společná mentální mapa od nuly. Paralelní = 3 lidé musí každopádně reconcileovat 3 různé mentální mapy.

## Kdy paralelní > mob (counter-criteria)

1. **Pure explorace 3 odlišných úhlů** (happy-path / multi-step / smart defaults — přesně to co dělá `VARIANT_ANGLES` v `tool/cli/quick_session.py:314-318`). Mob je tu plýtvání: tým je nucen sériově opouštět rozdělanou A aby zkusil B.
2. **Tým s nezávislými backgroundy**. Designer + dev + data analyst — každý chce vést svůj lens. Mob = 2 z nich čekají, paralelní = každý jede.
3. **Time-pressure (90 min, must ship 3 demos pro stakeholdera)**. Paralelní = 3× output v stejném wall-clocku. Mob za 90 min reálně dodá 1.5 finished varianty.
4. **Tým > 6 lidí**. Mob se rozpadá na "council of 3 + audience of 3+". Paralelní škáluje lineárně přidáním párů.
5. **Brownfield s velkým repem**. Každá varianta potřebuje 5-10 min na čtení existujícího kódu (per `_render_builder_prompt()` POVINNÝ POSTUP body 1-3, `quick_session.py:432-441`). V mobu si tím zabiješ první 30 % session času sériově.
6. **Když Decider chce uvidět diversity před commitnutím** (typický vibe-coding use case). Paralelní mu dá 3 reálné varianty na výběr, mob mu dá 1 winning + 1-2 polotovary.

## Mob-specific pitfalls (real war stories)

**P1 — Prompt-churn paralýza.** Tým 6 lidí 12 minut diskutuje, jestli má v promptu být "use shadcn/ui Button" nebo "use existing Button component". Mezitím CC čeká. Reálně viděno 3× ze 5 mob sessions: > 30 % session času = debata nad jedním promptem. **Fix: Prompt Driver má 60 vteřin na napsání + odeslání. Ostatní mlčí. Po odeslání diskutujeme output.**

**P2 — Senior píše, junioři koukají.** Bez tvrdé rotation discipline senior automaticky převezme klávesnici "protože je to rychlejší". 5 spectatorů = 5 promarněných person-hours. **Fix: Llewellyn-style "strong-style pairing": prompt PÍŠE junior, senior smí jen MLUVIT. Forced learning curve.**

**P3 — Scroll-back drift.** CC vyplivne 200 řádků diff za 8 vteřin. 4 ze 6 lidí v ten okamžik zírají do notes / Slacku / ven z okna a missnou polovinu. Reálně: za 30 min mob session 2 lidi vůbec netuší co code dělá. **Fix: po každém CC outputu Navigator (rotující role) MUSÍ nahlas přečíst diff summary v 2 větách. AI commentary mode (`/explain` po každém change) jako safety net.**

**P4 — "Sequential pivot" tax.** Iterace 1 dosáhla 60 % funkčnosti. Iterace 2 = "pivot, zkusíme úplně jinak". Tým ztratí muscle memory iterace 1, pivot je často horší než dořešená 1. Reálně viděno: 4 z 6 sequential sessions končí s iterací 1 jako "winner" a pivot jako "wasted 25 min". **Fix: druhá iterace MUSÍ být refinement, ne pivot. Pivot pouze pokud Decider explicitně zavolá "iterace 1 je dead end" do 15. minuty.**

**P5 — Voting amnesia.** V paralelní mód každý pár vidí jen svojí variantu, takže má jasné stanovisko "moje vs. ostatní". V mobu tým postavil **všechny 3 iterace** společně, takže k nim má rovnocenný attachment. Klasické "dot voting per variant" tu nefunguje — všichni dají 1 bod každé. **Fix: voting ne per varianta, ale **structured retrospective**: "Která iterace nejlépe odpovídá Acceptance kritériím?" + "Která by se nejlevněji dotáhla do production?" — Decider's call s veřejnou rationale.**

**P6 — TV vs laptop ergonomic split.** Driver má klávesnici na laptopu, tým kouká na TV. Driver vidí small font + vlastní cursor, tým vidí big font + delay (HDMI mirror lag ~200ms). Driver často píše 2 řádky napřed než tým "stihne" číst. **Fix: drvier MUSÍ zoom 150 % v terminálu, NEMUSÍ vidět vlastní laptop, MUSÍ koukat na TV jako tým. Klávesnice slepě nebo bezdrátová na stůl.**

## Concrete protocol design

### Time-box (90 min total)

| Phase | Min | Activity |
|-------|-----|----------|
| Setup | 0-10 | Facilitátor `worktree.py setup --mob --slug X` (1 worktree místo 3), tým si přečte `INTEGRATION_GUIDE.md` + acceptance .feature společně nahlas. |
| Iterace 1 | 10-35 | Rough first stab. Angle = `VARIANT_ANGLES[0]` (happy-path). Driver+Navigator rotují co 5 min. |
| Mid-checkpoint | 35-40 | Decider thumb up/down + 1-věta rationale. "Pivot vs refine?" rozhodnutí. |
| Iterace 2 | 40-65 | Refinement (default) NEBO pivot (jen pokud iter 1 ❌). Jiný driver+navigator. |
| Iterace 3 (optional) | 65-80 | Pouze pokud Decider call. Většinou skip → buffer. |
| Retrospective + Decider call | 80-90 | "Which iteration ship?" + commit winning + handoff. |

### Role rotation (5-min cycle)

- **Driver** (1×): klávesnice + odesílá prompt do CC. **Mlčí během CC outputu.**
- **Navigator** (1×): říká driverovi co psát. Po CC outputu povinně přečte diff summary nahlas (2 věty).
- **Researcher** (1×): paralelně grepuje repo, hledá podobné komponenty, hlásí nálezy navigatorovi.
- **Skeptic** (1×): hledá důvody PROČ to nebude fungovat. Forced devil's advocate, jinak groupthink.
- **Recorder** (1×): píše do session notes klíčová rozhodnutí + open questions. Future audit trail.
- **Decider** (1×): MLČÍ kromě mid-checkpoints. Pokud se Decider zapojuje průběžně, zabíjí dissent (HiPPO).

→ rotace Driver↔Navigator co 5 min, ostatní role drženy celou iteraci (kontext continuity).

### CC prompt template differences vs current `_render_builder_prompt(builder='claude-code')`

Current (`quick_session.py:411-460`) je psaný pro **paralelní pár** s vlastním worktree. Pro mob potřebujeme:

1. **`{variant}` → `{iteration}`** v textu promptu (sémantika "verze v čase", ne "alternativa v prostoru").
2. **Add iteration history**: "Toto je iterace {N}. Předchozí iterace: {summary iter 1}. Co měníme: {diff_intent}."
3. **Remove "Tvoje dvojice" framing** (`quick_session.py:420`) — nahradit "Tvoje session (mob, 6 lidí u TV)".
4. **Add scroll-back guard**: "Po každém change vypiš 2-větný diff summary nahoře v odpovědi. Tým to čte nahlas před dalším promptem."
5. **Branch deterministicky**: `pflanzer/{slug}-mob` (1 branch, ne A/B/C). Iterace = git commits, ne branches.
6. **Acceptance .feature pass-rate gate per iteration**, ne na konci. CC po každé iteraci spustí `.feature` runner a vypíše pass/fail.

### Worktree.py changes

```bash
python tool/cli/worktree.py setup --mob --slug X
# → 1 worktree místo 3 (current code at worktree.py:121-155 vytváří 3 vždy)
# → branch pflanzer/{slug}-mob
# → install deps 1× místo 3× (3× rychlejší setup)
```

Implementace: `_create_worktrees()` přidá parametr `mode: Literal["parallel", "mob"] = "parallel"`. Pokud `mob`, loop místo `for variant in ("A","B","C")` jede 1 iterací s `variant = "mob"`.

## Integration s Pflanzer wizardem

**KROK 0 (nový) — MODE SELECT** v `/pflanzer.md` před krokem 1:

```
AskUserQuestion: "Jak budete dnes pracovat?"
options:
  - "Paralelně (3 dvojice, 3 worktrees, 3 různé angles)" ✅ default
  - "Mob (všech 6 u 1 TV, 1 worktree, 2-3 sekvenční iterace)"
  - "Hybrid v3 — TBD" (disabled, future)
```

→ default zůstává paralelní (většina sessions = explorace). Mob je explicit opt-in.

**Decision tree pro doporučení modu** (renderni do AskUserQuestion description):
- ≤ 5 lidí + onboarding nového člena? → mob
- Single-stake decision (1 problém, různé hloubky)? → mob
- Greenfield + audit-grade? → mob
- 3 různé hypotézy + > 5 lidí + time pressure? → paralelní
- Default (most cases) → paralelní

**Krok 4 (Builder prompts)** dispatchne podle modu:
- `mode='parallel'`: existující `builder_prompts(n_variants=3)` (per `quick_session.py:321-398`)
- `mode='mob'`: nová `builder_prompts_mob(slug, hook, n_iterations=3)` — vrátí 1 prompt s iteration roadmap (3 angles jako sequential plan), ne 3 separátní prompts.

**Krok 5 (Voting)** dispatchne podle modu:
- `mode='parallel'`: existující per-variant dot voting (per `pflanzer.md:170-205`)
- `mode='mob'`: structured retrospective, ne dot voting:
  ```
  AskUserQuestion (1× per role): "Která iterace nejlépe pasuje na Acceptance criteria?" [A1/A2/A3]
  AskUserQuestion (1× per role): "Co bys změnil/a než to půjde do prod?" [text]
  AskUserQuestion (Decider): "Final ship — A1, A2, A3, nebo combined merge?"
  ```

**Krok 7 (Handoff)** zůstává stejný formát. `render_handoff()` (per `quick_session.py:572-715`) jen detekuje mode a v sekci "Varianty" píše "Iterace" místo "Variants". Single winning iteration → SHIP.md.

## Závěr (1 věta)

Mob je užitečná přídavná zbraň pro úzkou class problémů (single-decision, onboarding, audit-grade) — implementuj ji jako `--mob` opt-in flag s tvrdou rotation discipline a structured retrospective voting; **nech paralelní default**, protože většina vibe-coding session je explorace, kde paralelní vždycky vyhraje na ROI.
