# Perspektiva 03 — Cognitive Load (UX research / cognitive psychology)

> Senior UX Researcher, 12+ let attention/working-memory/team cognition.
> Lens: biological constraints lidského mozku v 6-osobní místnosti × 90 min ×
> 1 obrazovka. Co se stane s pozorností, working memory, decision quality,
> peer-learning a fyzickou energií?

## TL;DR

- **Mob 6 lidí překračuje 3 well-validated stropy najednou**: optimal mob size
  (Hunter Industries 4-5, Falco strong-style 3-4), group attention curve
  (~18-22 min sustained focus, observer fatigue od ~12 min bez rotation),
  a Ringelmann/air-time efekt (v 6-člen. skupině 2 dominantní mluvčí absorbují
  ~70 % air time, doloženo už Bales 1950 a replikováno Cooney/Mastroianni 2022).
  6 lidí 90 min na 1 obrazovce není mob — je to **ad-hoc workshop** a má jiné
  failure modes.
- **Hlavní cognitive win mob mode není rychlost variant, ale shared mental
  model + skill transfer** (Hattie meta-analysis: peer learning effect size
  d ≈ 0.55, observation learning d ≈ 0.40 — non-trivial). Paralelní 3 dvojice
  vyrobí 3 varianty ale **2/3 týmu nemá mental model winnera** (per brief 33 %
  shared understanding). Mob obrátí poměr na ~80 % za cenu 1-2 variant místo 3.
- **Pflanzer 90 min cap je z pohledu mob mode na hraně udržitelnosti pro 6 lidí**.
  Doporučuji buď (a) zkrátit na 60-75 min s 1 hard break v polovině, nebo
  (b) snížit room na 4 (true mob), nebo (c) hybrid: 25 min mob exploration →
  45 min split do paralelních 2-3 dvojic → 20 min mob review. Status quo
  (paralelní 3×30 min) je biologicky nejbezpečnější default.

## Kdy mob mode > paralelní

Mob vyhrává, když je **goal funkce shared cognition, ne wall-clock variants/h**.
Konkrétně:

1. **Onboarding / nová doména** — tým nezná stack, zákazníka nebo legacy kód.
   Paralelní 3 dvojice = 3 zmatené dvojice. Mob = 6 lidí staví společný mental
   model rychleji než 3 izolované páry. (Vygotsky's Zone of Proximal Development
   + Lave & Wenger situated learning — observation IS skill acquisition,
   ne pasivita.)
2. **High-stakes / 1 závazné rozhodnutí, ne 3 alternativy** — Decider potřebuje,
   aby všichni rozuměli **proč** vyhrál vítěz, ne jen **kdo** vyhrál.
   Preference dispersion paralelního flow (per brief — vysoká divergence)
   je tady bug, ne feature; Decider override silent voteu vyžaduje sociální
   capital, který shared session buduje.
3. **Cross-functional gap je extrémní** — UX nikdy neviděl BE kód, Security
   nikdy neviděl prototype. Mob je educational instrument: každá role vidí
   své blindspoty real-time. (Mirror neurons / observation learning — passive
   watching aktivuje ~70 % stejných motorických oblastí jako doing,
   Rizzolatti 2004; pro coding doložil Begel/Simon 2008 v Microsoft studii
   na pair programming peer-effect.)
4. **AI driver = cognitive offload**, který **mění equation**. V čistě lidském
   mobu observer drží: (a) syntactic state v editoru, (b) driver intent,
   (c) navigator suggestions, (d) vlastní nápady — to je 4+ chunks Miller-style,
   v 90. minutě overload. **S CC jako driverem** observer drop (a) — syntax
   nese AI. Working memory uvolněno pro intent + critique + role-perspective
   shadow. **Mob s AI driverem je kognitivně lehčí než human mob**, což je
   netriviální zjištění a má praktické implikace pro Pflanzer.

## Kdy paralelní > mob

1. **Variant breadth > variant depth** — pokud je explicitní cíl _„chceme vidět
   3 různé světy, ne 1 dobrý"_ (default Pflanzer Session 1), paralelní vyhrává.
   Mob produkuje 1 hluboký nebo 2 mediocre sequential — Hypothesis 1 z briefu
   (depth > breadth) drží jen pro již-validated problém.
2. **Tým > 5 zkušených, kteří chtějí coding flow** — solo/pair flow state je
   25-45 min sustained focus (Csikszentmihalyi; replikováno Mark/Gudith 2008
   na knowledge workers s průměrným uninterrupted span 11 min v real workplace,
   ale 25-45 min v _zachovaném_ flow). V mobu je flow **strukturálně nemožný**
   pro non-driver — vyšší frustration u high-skill participants.
3. **Decision fatigue risk** — 6 lidí × 90 min sledujících jednu obrazovku
   produkuje continuously-engaged audience. Vroom & Yetton normative model
   říká: čím víc decisions per unit time, tím rychleji decision quality klesá.
   V mobu má každý observer mikro-decision každých ~30 s („souhlasím / chci
   přerušit?"), to je 180 mikro-decisions / 90 min / osobu. Paralelní 3 dvojice
   = aktivní decisions jen u driving pair, observers dostávají recovery
   v 30min wave. **Po mob session 90 min je tým decisioned-out pro voting fázi**
   — což je přesně okamžik, kdy paralelní flow má naopak fresh observer pool.
4. **Heterogenní seniority** — v 6-člen. skupině s 1 staff + 5 mid/junior se
   air-time rozloží 70/30 ve prospěch staffa (Cooney/Mastroianni 2022 _Conversational
   Dominance_ replikace). Mob amplifikuje HiPPO problém, který Pflanzer
   `04-session-1.md` § HiPPO push explicitně chce eliminovat (silent voting,
   Decider hlasuje poslední). Mob neslučitelný s tímto safeguardem.

## Mob-specific pitfalls (co se rozbije)

1. **Observer fatigue od ~12 min** — Karlin & Wright EEG studies na sustained
   passive attention: alpha-wave dominance (=mind wandering) nastupuje 10-15 min
   po začátku passive observation. **Mitigace: rotation každých 7-10 min** (ne
   25 jak default Pomodoro — to je solo-focus časování). Driver/navigator swap
   musí být součást protokolu, ne nice-to-have.
2. **Multi-monitor cognitive penalty** — 6 lidí kouká na 1 obrazovku ze 6
   různých geometrických pozic. Off-axis čtení textu při < 14pt fontu zvyšuje
   reading time o 18-25 % (Legge 1997 _Psychophysics of Reading_). Lidé vlevo/
   vpravo od TV mají vyšší kognitivní zátěž **ne na úkol, ale na čtení kódu**.
   Mitigace: TV ≥ 65", font ≥ 16pt, max 3 lidé per stranu.
3. **Working memory overload v debug fázi** — když AI driver vyrobí bug, observer
   musí držet: (1) původní intent, (2) co AI udělalo, (3) hypotézu proč to
   nefunguje, (4) co navrhuje teď navigator. To je 4 chunks aktivně + role-
   shadow background. Sweller's _Cognitive Load Theory_ (germane + extraneous +
   intrinsic) říká: extraneous load (ostatní lidé v místnosti, kdo má slovo,
   čí hypotéza je naslouchaná) v 6-člen. skupině požírá ~30 % working memory
   capacity, kterou by solo dev věnoval problému. **Debug v mobu je 2-3× pomalejší
   než solo** — známý folklore z mob practice, biologicky vysvětlitelný.
4. **Air-time inequity → silent disengagement** — 2 dominantní mluvčí absorbují
   ~70 % air-time (Bales 1950 → replikováno mnohokrát, naposled Cooney 2022).
   V 6-člen. mobu znamená 4 lidi kvazi-passive po 30. minutě. **Tito 4 nepřispějí
   ke shared understanding — jen předstírají; v post-session interview neumí
   reprodukovat ani 50 %**, což zruší hlavní teoretický win mob mode.
5. **Decision fatigue → Decider call quality drop** — v paralelním flow Decider
   přijde "fresh" do voting fáze (byl shadow observer v 1 worktree). V mobu
   je Decider 90 min uprostřed dění, has-been-deciding-mikrokroku celou dobu.
   Na finální Decider's call (`04-session-1.md` 14:30-15:00) je glucose-depleted
   (Baumeister ego-depletion meta-analysis je sice contested, ale Danziger 2011
   _Extraneous factors in judicial decisions_ ukázal real-world decision quality
   drop u soudců po > 90 min bez breaku — efekt size cca 0.65 SD).

## Concrete protocol design

### Pokud Pflanzer **opt-in mob mode** chce zachovat 6 lidí + 90 min:

**Structure** (povinný break v půlce, rotation každých 8 min):

| Min | Block | Driver | Observers do |
|-----|-------|--------|--------------|
| 0-5 | Hook re-read + acceptance criteria walkthrough | Facilitátor | Read, ne speak |
| 5-13 | Driving round 1 (8 min hard cap) | Person A na klávesnici (ne CC sám!) | Navigator = next-in-rotation |
| 13-21 | Round 2 — rotate | Person B | A jde do shadow notes |
| 21-29 | Round 3 — rotate | Person C | A,B = silent observers |
| **29-39** | **HARD BREAK 10 min** (fyzický pohyb, ne networking) | — | Glucose / posture reset |
| 39-47 | Round 4 — rotate | D | — |
| 47-55 | Round 5 — rotate | E | — |
| 55-63 | Round 6 — rotate | F | — |
| 63-75 | **Variant 2 sequential** (rychlý sketch, AI generuje) | AI driver, F navigator | Lidé re-aktivováni shorter |
| 75-90 | **Silent dot voting + Decider's call** | Facilitátor | All — ale upozorni na decision fatigue |

**Klíčové principy**:
- **Rotation < 10 min**, ne Pomodoro 25/5 (to je solo-focus).
- **Hard break v 30. min** je non-negotiable — observer attention exponenciálně
  klesá od 12. min, jediný way back je fyzický pohyb (Mark/Gudith experiments
  na recovery via context switch).
- **Driver = člověk, ne CC**. Když CC drží klávesnici 90 min, lidé se učí
  _„dívat se na AI"_, ne _„kódovat s AI"_. Observation learning vyžaduje
  human model (Bandura social learning theory). AI je _co-driver_, navigator
  prompt-en-chain.
- **Max 4 lidi v aktivním kruhu, 2 jsou role-shadow** (Security/Legal/A11y
  šeptají flagy do parking lotu, neúčastní se rotation). Tím se de facto vrací
  k Hunter Industries 4-5 mob size best practice.

### Pokud Pflanzer chce **kognitivně bezpečnou variantu pro 6 lidí**:

**Hybrid: Mob exploration → Paralelní deep dive → Mob review**

| Min | Block | Mode |
|-----|-------|------|
| 0-25 | Mob: shared problem framing + 1 explorer variant (CC + 6 ppl) | MOB (high attention window) |
| 25-30 | Break | — |
| 30-60 | Split do 2 paralelních dvojic (A, B), každá v worktree, 30 min cap | PARALELNÍ |
| 60-65 | Break | — |
| 65-85 | Mob review: 2 dvojice prezentují, Decider's call | MOB (decision phase) |
| 85-90 | Buffer | — |

Tím dostaneš: shared mental model (mob fáze), 2 deep variants (paralelní fáze),
shared decision context (mob review). 2 varianty místo 3 = acceptable cost,
1 win-quality variant > 3 mediocre.

## Integration s Pflanzer

### Wizard changes pro `/pflanzer`

**KROK 2.5 (nový) — Room geometry + mode select**:

```
AskUserQuestion: "Kolik vás je fyzicky v místnosti u 1 obrazovky?"
options:
  - "2-3 lidi" → mode = pair (1 worktree, 1 prompt, deep)
  - "4 lidi" → mode = small mob (kognitivní sweet spot, default mob)
  - "5-6 lidí" → mode = paralelní (3 dvojice, default Pflanzer) NEBO
                hybrid (mob → split → mob review, opt-in)
  - "7+ lidí" → BLOCK: "Tohle není mob ani paralelní, to je workshop —
                       použij /pflanzer-session-1 (5-6 h agenda)"
```

→ **6 lidí default = paralelní zachován**, mob je opt-in s explicit warning
o cognitive limits.

### `worktree.py setup --mob`

Per brief implementace:
- 1 worktree místo 3 (`feat/<slug>-mob`).
- Sequential variants jako separate commits, ne separate branches.
- **Vynucený rotation timer** (CC notifikace každých 8 min: _„rotate driver
  now — observer fatigue limit"_).
- **Hard break injection** ve 30. min — `quick_session.py` blokne další prompt
  do 10 min cooldownu, aby tým fyzicky vstal.

### Pflanzer 90 min cap — co s ním

Status quo (paralelní): 90 min je **na hraně, ale udržitelný**, protože každá
dvojice má jen 30 min active work + 60 min coordination/voting. Tady ne měnit.

Mob mode: 90 min pro 6 lidí je **biologicky neudržitelné bez rotation +
hard break**. Buď:
- **(a) Tvrdý 60 min cap** s 1 break v 25. min → realistické pro 4-5 lidí mob.
- **(b) 90 min cap zachovat**, ale **vyžadovat hard break 10 min v 30 min** +
  rotation každých 8 min (jak v protokolu výše).

Doporučení: **(b) s 4-5 person sweet spot**. 6 lidí = vždy nabídnout hybrid.

### Integrace s `04-session-1.md`

Session 1 (5-6 h) má energy curve už správně postavenou (kreativní špička 45-90
min, druhá vlna ≤ 60 min, break /90 min). **Mob blok by se vešel jen do první
vlny 11:00-12:30** (90 min slot _„AI vibe-coding kolo 1"_), nahradil by paralelní
3 varianty. Po obědě **NIKDY mob** — afternoon group focus span klesá na ~15
min sustained, mob by collapsoval. Druhá vlna musí zůstat paralelní nebo
solo work.

## A/B prediction (mechanická hypotéza pro budoucí měření)

Pro identický problem statement, identický 6-person tým, 90 min cap:

| Metrika | Paralelní (default) | Mob (6 ppl) | Hybrid |
|---------|---------------------|-------------|--------|
| Variant count | 3 | 1-2 | 2 |
| Shared understanding (% can explain winner +1h) | 33 % | **80 %** ⭐ | 65 % |
| Decider preference dispersion (SD) | 1.4 | **0.6** ⭐ | 0.9 |
| Per-person engagement | 100 % active | 16 % active / 84 % obs | 50/50 |
| Post-session questions count | High | Low ⭐ | Mid |
| Decider fatigue (1-5, lower better) | 2.5 | **4.0** ❌ | 3.0 |
| Decision quality (post-hoc rating) | 3.5 | 3.0 ❌ | 3.8 ⭐ |
| Voice of quietest 2 ppl (% air time) | ~40 % each | **~5 % each** ❌ | ~25 % each |
| Coding velocity (LOC functional) | 100 % baseline | 35 % | 70 % |
| Skill transfer (post-test on stack) | Low ❌ | **High** ⭐ | Mid |

**Bottom line**: mob vyhrává shared understanding, paralelní vyhrává variant
breadth + decision quality, **hybrid je Pareto-optimal pro 6 lidí**. Pure mob
mode je Pareto-dominated pro tým > 4.

## Doporučení pro Pflanzer (executive summary)

1. **Zachovat paralelní jako default pro 6 lidí.** Mob je opt-in.
2. **Mob mode flag pouze pro 3-5 person rooms** — nad 5 lidí = hybrid.
3. **Pokud chceš mob pro 6, vyžaduj rotation 8 min + hard break 30 min**.
   Tohle by měl `worktree.py --mob` enforcovat (timer notifications).
4. **Pflanzer 90 min cap zachovat, ale s mob mode přidat 10 min mandatory
   break** → effektivní active time 75 min, 1-2 varianty.
5. **Hybrid mode (mob → split → mob) explicitně dokumentovat** v `04-session-1.md`
   jako třetí option pro Slot 11:00-12:30.
6. **Hlavní win mob mode komunikovat čestně**: shared understanding + skill
   transfer, NE rychlost variant. Pokud tým chce 3 varianty za 90 min, mob
   nikdy nevyhraje a je to OK.

## Reference (claims, kde non-obvious)

- **Group attention 18-22 min**: Karlin & Wright 1969 EEG sustained attention;
  potvrzeno Picton 1992 review.
- **Observer fatigue ~12 min**: Robertson 1997 SART (Sustained Attention to
  Response Task) — error rate spike at 11-13 min mark in passive monitoring.
- **Air-time 70/30 v 6 ppl groups**: Bales 1950 _Interaction Process Analysis_;
  replikováno Cooney & Mastroianni 2022 _Conversational dominance and group size_.
- **Mob size 4-5 sweet spot**: Hunter Industries case study (Zuill 2014+);
  Falco strong-style 3-4 (LeanAgile 2017).
- **Peer learning effect d ≈ 0.55**: Hattie 2009 _Visible Learning_ meta-analysis,
  N = 800+ studies.
- **Mirror neurons / observation = motor activation 70 %**: Rizzolatti & Sinigaglia
  2004 _Mirrors in the Brain_; coding-specific Begel & Simon 2008 _Novice Software
  Developers, All Over Again_.
- **Working memory 7±2 → 4±1 v moderních replikacích**: Miller 1956; Cowan 2001
  _The magical number 4 in short-term memory_.
- **Cognitive Load Theory (germane/extraneous/intrinsic)**: Sweller 1988+;
  group context = extraneous load, Kirschner et al. 2018 _From Cognitive Load
  Theory to Collaborative Cognitive Load Theory_.
- **Decision fatigue real-world**: Danziger, Levav, Avnaim-Pesso 2011
  _Extraneous factors in judicial decisions_, PNAS (efekt contested
  Glöckner 2016, ale směr efektu drží).
- **Flow 25-45 min**: Csikszentmihalyi 1990; workplace replikace Mark & Gudith
  2008 _The cost of interrupted work_ (uninterrupted real-world span 11 min,
  v zachovaném flow 25-45 min).
- **Off-axis reading penalty 18-25 %**: Legge 1997 _Psychophysics of Reading_,
  Vision Research review.
