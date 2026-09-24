# Perspektiva 01 — Mob-programming coach

> Author angle: 12+ let mob practice (Woody Zuill / Llewellyn Falco / Hunter
> Industries lineage), 50+ teams coached. Optika: kdy je shared keyboard
> levnější než tři paralelní, a kdy je to drahé spectator sport.

## TL;DR

- **Mob mode má smysl jen když je samotná otázka víc cenná než kód** — tj. když
  tým neví, co staví, a 60 minut shared exploration vyhraje 3× 30 min izolované
  exekuce. To je v Pflanzer kontextu menšina sessions (greenfield discovery,
  cross-team alignment, nové domény). Default 3 dvojice paralelně **držet**.
- **6 lidí na 1 monitoru je za hranou všech mob research findings** (sweet spot
  4-5, viz Hunter Industries postmortems). Pro Pflanzer to znamená: pokud `/pflanzer`
  rozhodne mob, **odpoj 1-2 lidi do "scribe + observer roli"** (rotace, ne sezení) —
  jinak get diminishing returns + monitor fatigue do 35. minuty.
- **Claude Code jako "AI mob member" mění rotation cadence** — strong-style
  4-min driver/navigator nefunguje, když je AI vždy on a nikdy nečeká.
  Doporučuji **6-min driver / 2-min "ask CC" / rotace každých 8 min** s explicit
  voiceover ("co teď CC dělá a proč").

## Kdy mob mode > paralelní

Konkrétní decision criteria, na kterých bych v `/pflanzer` wizardu mob doporučil:

1. **Greenfield + cross-functional disagreement.** Tým nemá shodu na tom,
   *co* staví (ne *jak*). Příklad: PdM si představuje multi-step wizard,
   FE chce single-screen, UX chce conversational. Paralelní mode v této situaci
   prostě postaví všechny tři a hlasování ukáže preferenci — ale **týmu zbyde
   3× rozdílný mental model winning fíčury**. Mob mode je donutí se na společný
   model dohodnout *před* prvním řádkem kódu, a to je ten cenný artefakt.
2. **Brownfield s heavy domain knowledge u jednoho člověka.** Když 1 senior
   ví všechno o legacy systému a 5 ostatních ne, paralelní mode = 2 dvojice
   blokované na "co dělá X?". Mob = senior je permanent navigator, ostatní
   driveři se učí v reálném čase. **War story**: Hunter Industries stáhli
   onboarding ze 6 týdnů na 2 právě tímhle.
3. **High-stakes Decider v místnosti.** Pokud Decider je C-level a má **1 šanci
   za kvartál** být v session, mob ho udrží v loopu (vidí trade-offs in real-time,
   nemusí komparovat 3 hotové výstupy, kde už je bias na "ten poslední, co
   jsem viděl"). Mob přirozeně produkuje "Decider's gut check" každých
   8-10 minut.
4. **Production-readiness target je nízký** (`production_readiness_target ≤ 50`,
   tj. throwaway / interní demo). Mob produkuje 1 hloubkovou variantu — pokud
   stejně chcete jednu vyhodit a iterovat, nedělej tři.

## Kdy paralelní > mob (current Pflanzer default)

Counter-criteria — když držet status quo:

1. **Risk profile = pilot/production.** `production_readiness_target ≥ 70`
   znamená, že chceš `% LOC merged unmodified` co nejvyšší. Tři varianty dají
   Decider real choice — mob produkuje jednu variantu, do které je tým
   sociálně committed (sunk cost), a Decider má choice mezi "go" a "throw away
   90 minut týmu". To není choice. **Doporučuji: production = paralelní hard rule.**
2. **Tým > 5.** Každý další člověk nad 5 je v mobu **pure spectator** s 16-20%
   active driving time → ~$5k zbytečného času per session (corporate rates).
   Pflanzerův implicit upper bound je 6 (ROOM v `quick_session.py`); mob s 6 lidmi
   je už za hranou. Pokud tým fakt chce mob a je 6+, **rozděl na 2 mini-mobs po 3**.
3. **Junior-heavy tým + týž senior na vše.** Mob prostě zesílí seniority gradient —
   junior nikdy neřekne "stop, nevím, co děláš", protože před 5 dalšími to bolí víc
   než před 1. Paralelní mode dá juniorovi safe space (1 partner).
4. **Acceptance criteria už existují a jsou tight.** Pokud máš Gherkin scénáře
   z Charteru a tři varianty mají project totéž acceptance test, mob nepřináší
   žádnou exploration value. Tři dvojice jsou rychlejší.

## Mob-specific pitfalls (co vidíme bombing)

Failure modes specifické pro 6-osob mob v 90 min Pflanzer kontextu:

- **"Tichý junior, hlasitý senior" / HiPPO bypass.** Decider mluví → tým kóduje
  jeho intuici → vote po session je formalita. Pflanzer má tohle adresované
  v paralelním modu (silent dot voting, Decider hlasuje **poslední**), ale mob
  to defacto rozbíjí — názor je viditelný v real time, anonymity is dead.
  **Fix**: před každou major decision (architecture, framing) **forced silent
  write** 2 min: každý napíše svůj názor na Slack/sticky, pak public reveal.
  Llewellyn Falco tomuhle říká "1-2-4-all in mob" — Pflanzer to už zná
  z `/pflanzer` § 5 Speed mode, jen to tu vynutit jako default ne fallback.
- **AI single-thread context window bottleneck.** Jedna CC instance = jedna
  konverzace. Když mob řekne "počkej, zkus jiný approach", CC ztratí kontext
  původního approach. Paralelní 3× CC tohle problém nemá (každý worktree
  má vlastní context). **Fix**: explicit "branch a checkpoint" každých 15 min
  — mob řekne CC "commit current state on branch X-checkpoint-N, pak zkusíme
  alternativu". Jinak you lose hours of work na jednom "co kdyby".
- **Monitor fatigue ~35 min.** Empiricky: 6 lidí, 1 obrazovka, 1 voice (ten,
  kdo navigates) = pozornostní křivka spadne na 50% kolem 35. minuty. To
  v 90 min session znamená, že **mob může realisticky vyrobit 1 hloubkovou
  variantu, ne 2-3 sequential**. Brief slibuje "mob ~2-3 sequential" — to je
  optimistic; podle mé zkušenosti je to **1 deep + 1 rushed**, kde druhá je
  vždy worse než kdyby ji udělala 1 dvojice samotná.
- **"All-in" risk.** Pokud jediná vyrobená varianta hits dead-end ve 60. minutě
  (CC se zacyklí, framework nepodporuje X), tým přijde o **celou session**.
  Paralelní 3× má built-in resilience: jedna varianta failne, dvě zůstanou.
  Mob nemá. **Fix**: hard kill rule v 45. minutě — pokud nemáš working preview,
  rozpadáš se na 3 dvojice na zbytek sessionu.

## Concrete protocol design

Pokud `/pflanzer` rozhodne mob, navrhuji následující protokol:

**Pre-session (15 min, mandatory):**
- Decider napíše **1 odstavec "co bych chtěl vidět ve výsledku"** a pošle do
  místnosti **before** session start. Mob bez sdíleného north star = drift do
  hodiny.
- Acceptance criteria z Charter na velkém TV po celou dobu (read-only sticky).

**Session structure (90 min):**

| Block | Time | Aktivita |
|-------|------|----------|
| Framing | 0-10 min | Decider voiceover north star, tým 1-2-4-all napíše vlastní interpretaci, public reveal. Pokud >2 výrazně rozdílné → mob je špatný mode, fallback na paralelní. |
| Mob round 1 | 10-50 min | 6-min driver / 8-min rotace, **strong-style** (driver nepíše vlastní nápady, čeká na navigator). CC je permanent silent helper, navigator říká nahlas, co CC instruuje. **Hard checkpoint v 30. min**: máme working preview? Pokud ne, kill switch. |
| Break | 50-55 min | Povinný (monitor fatigue real). Bez tohoto break = 80% dropoff v engagement. |
| Mob round 2 NEBO split | 55-85 min | Dvě cesty: (a) tým chce hloubku → polish round 1 variantu. (b) tým chce alternativu → split na 2 mini-mobs po 3 lidech, 30 min, dvě divergent variants. |
| Voting + Decider call | 85-90 min | Decider volá Go/Iterate/Kill. **Důležité**: voting otázka je jiná než v paralelním modu — viz dále. |

**Rotace rolí během mob round (8-min cyklus):**

- **Driver** (1) — drží klávesnici, píše/promptuje CC. Nemá vlastní názor během
  driving (strong-style).
- **Navigator** (1) — myslí 1-2 kroky dopředu, instruuje driver i CC.
- **Observers / Voice of X** (3-4) — ne jen koukají, **každý zastupuje konkrétní
  perspektivu** (Decider, UX, Backend, Acceptance criteria guardian). Když
  navigator řekne "next step?", observer-of-perspektiva má přednostní právo
  promluvit za svou roli. Tohle je adaptace Liberating Structures "Conversation
  Café" pro mob — bez explicit role assignement get diminishing returns rychleji.
- **Scribe** (1) — píše decision log v real-time (ne facilitátor — facilitátor
  hlídá čas a rotace).

**CC-specific rules:**
- Žádný "let's see what CC thinks" bez explicit human navigator hypothesis.
  Jinak tým defacto outsourcuje thinking na model, který nemá kontext, co tým
  fakt chce.
- Každých 15 min commit checkpoint na separátní branch (`pflanzer/<slug>-mob-cp-<N>`),
  abychom mohli rollback bez ztráty session.

## Voting v mob kontextu (klíčový rozdíl)

Paralelní mode má dot voting "líbí se mi A / B / C" — tři artefakty, comparable
choice. **Mob má jen 1-2 artefakty**, takže voting otázka se musí změnit:

**Místo "Variant {X}: Líbí se mi / Spíš ne / Veto / Pass" zeptat:**

1. **"Co z té varianty FUNGUJE — vyber 1-2 prvky."** [multiSelect]
2. **"Co z té varianty NEFUNGUJE — vyber 1-2 prvky."** [multiSelect]
3. **"Pokud bys měl(a) tuhle variantu shippnout zítra do produkce, co je tvůj
   commitment level (0-3)?"** [single]
4. **(Decider only)**: "Go / Iterate (a co konkrétně) / Kill?"

Tohle dává Decideri kvalitativní "co chytnout / co vyhodit" místo numerical
score variant proti sobě. Pflanzer's `role_preferences` schema (user_value,
strategic_fit, commitment_level) lze re-použít, ale `user_value` per varianta
nedává smysl — místo toho **per-element score**.

Pokud session vyrobila **2 mini-mob variants**, vrať se k paralelnímu A/B
voting, jen s n=2.

## Integration s Pflanzer

Konkrétní změny do existujících files:

**`/Users/gizmax/Documents/PflanzerMethod/.claude/commands/pflanzer.md`** —
přidat **KROK 3.5 — MODE SELECT** (před bootstrap):

```
AskUserQuestion: "Jak budete varianty stavět?"
options:
  - "Paralelní 3 dvojice (default)" — 3 worktrees, A/B/C, 30 min cap.
    Doporučeno pro pilot/production a tým 6.
  - "Mob mode (1 obrazovka, sequential)" — 1 worktree, tým spolu.
    Doporučeno jen pokud: greenfield, throwaway, tým ≤ 5, cross-functional
    disagreement na framingu.
  - "Hybrid (mob 30 min framing, pak split na 2-3 dvojice)" — experimentální.
```

**Hard rule v wizardu**: pokud `risk_profile == "production"` AND user vybral
mob, zobraz warning a force re-confirm ("production = doporučuji paralelní pro
% LOC reuse — opravdu chceš mob?").

**`/Users/gizmax/Documents/PflanzerMethod/tool/cli/worktree.py`** — přidat
`--mob` flag do `setup` subcommand:

```python
p_setup.add_argument("--mob", action="store_true",
                     help="Mob mode: vytvoř 1 worktree místo 3 (slug-mob)")
```

V `_create_worktrees()` if mob: variants = ("mob",), branch = `pflanzer/<slug>-mob`.
Žádný A/B/C suffix, žádná diversity skrz angle.

**`/Users/gizmax/Documents/PflanzerMethod/tool/cli/quick_session.py`**:

- `VARIANT_ANGLES` — přidat single mob angle:
  ```python
  MOB_ANGLE = ("mob", "shared exploration",
               "Tým společně exploruje řešení v real-time, AI je permanent silent helper. "
               "Žádné pre-baked angle — direction emerges z mob discussion.")
  ```
- `builder_prompts(..., mode="parallel"|"mob")` — pokud mob, vrať 1 prompt
  místo 3, a do prompt textu zahrň mob protocol (rotation rules, checkpoint
  cadence, kill switch).
- `record_voting()` — accept nový spec format pro mob (per-element scores
  místo per-variant), persist do `role_preferences` s `rationale` polem
  obsahujícím parsed elements ("WORKS: X, Y / DOESNT: Z").

**Post-session knowledge transfer (Pflanzer's biggest mob win):**

Brief tipuje "shared understanding ~80% v mob vs ~33% paralelní". Doporučuji
to **měřit** přes auto-generated quiz po handoffu:

- Po `render_handoff()`, vyrob `data/quick/<slug>-quiz.md` se 3 otázkami
  ("co dělá winning varianta?", "proč jsme nevybrali alternativu?", "jaké je
  hlavní risk?"). Pošli linkem do týmu T+24h.
- Self-score 0-3, persist do `audit` log jako `mob.knowledge_check`.
- Po 5 sessions máš **empirickou metriku** mob vs paralelní shared understanding,
  ne jen anecdoty. To je classic Karpathyho autoresearch metric loop.

## Závěr — mob je opt-in, ne replacement

Pflanzer's paralelní default je správně pro 70-80% corporate use cases (pilot,
production, brownfield, tight acceptance criteria). Mob mode přidat jako
**explicit opt-in s warnings**, primárně pro greenfield throwaway exploration
a high-disagreement framing. Hard guardrails: tým ≤ 5, kill switch v 45. min,
forced silent write před každou major decision, separátní voting otázky.

Co bych **nenavrhoval**: dělat mob default. Většina týmů, co o tom mluví,
chce mob, protože je to social — ne protože je to optimal pro jejich problém.
Coach's job is to ask "co konkrétně řešíš?", ne "líbí se ti to?".
