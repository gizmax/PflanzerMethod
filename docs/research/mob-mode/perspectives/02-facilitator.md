# 02 — Facilitator / Group Dynamics Perspective

> Autor: Senior Facilitator (Liberating Structures, Design Sprint GV, LDJ,
> Open Space, Fishbowl, 15+ let cross-functional). Branch
> `research/mob-mode`, wave 1.

## TL;DR

- **Mob mode v 6 lidech × 90 min je facilitační hard mode**, ne snadnější
  varianta paralelního flow. Bez explicitních turn-taking rituálů,
  rotation cadence < 8 min a Decider-mute pravidla degraduje na „1 senior
  kóduje, 5 přitakává" do 25. minuty.
- **Diversity ≠ groupthink je řešitelné jen sekvenční single-thread
  variantou s povinným pivot reset** (nový driver + nový navigator + reset
  prompt) mezi variantami. Pokud se mob „doplní" na variantu předchozí
  místo restartu, vyrobíš 1 monolit + 2 patche, ne 3 varianty.
- **Decider v místnosti při mob = HiPPO šum amplifikován 6×**. Pflanzer
  silent-vote-poslední pattern z `04-session-1.md` § HiPPO push v mobu
  nelze 1:1 použít — Decider vidí každý keystroke. Potřebujeme
  **„Decider as observer, not navigator"** kontrakt + verbal silence
  protocol.

## Kdy mob mode > paralelní

1. **Shared mental model je primární cíl**, ne počet variant. Když tým
   po session musí **společně udržovat** kód (žádný owner per varianta,
   všichni babysittují winner), mob > paralelní. Knowledge transfer
   v mobu je side-effect, v paralelním vyžaduje 30-min revue + reading
   cizího kódu.
2. **Nový tým / nová doména** (první session v BU, nově složený squad,
   nová tech stack). Mob = onboarding + delivery najednou. Paralelní
   předpokládá, že každá dvojice ví, co dělá.
3. **High-stakes single decision** (např. „jeden API endpoint, pojď ho
   nadesignovat"). Když je problém **úzký a hluboký**, paralelní 3
   variant je over-engineering — všichni stejně budou chtít jednu.
4. **Decider explicitně chce „cítit" implementaci** (ne jen reviewovat
   3 prototypy). Mob dává Deciderovi reálný kontakt s effort × tradeoff.
   Tady ale platí pitfall #2 níže.
5. **Tým < 5 lidí**. Pflanzer min je 4 (Charter + PdM + Facilitátor +
   Decider). Při 4 lidech paralelní = 2 dvojice = 2 varianty, ROI
   marginální. Mob s 4 = ideální velikost (níže § Concrete protocol).

## Kdy paralelní > mob

1. **Diversity je primární cíl** (Charter má XYZ hypotézu se širokým
   solution space). 3 paralelní = 3 nezávislé framings; mob
   sekvenční = první framing se anchoruje a další 2 jsou jeho deriváty
   (anchoring bias literatura: Tversky/Kahneman, Hallihan/Shu 2012 pro
   design context).
2. **Cross-functional s vetovacími rolemi** (Security/Legal/EM povinně
   senior). 6 lidí v mobu, kde Security expert sedí 70 minut tiše a pak
   v 75. zařve „veto" je facilitační noční můra. Paralelní = každá veto
   role má kanál (shadow agent) a flagne v reálném čase.
3. **Timeline je deadline-driven** (3 varianty MUSÍ existovat na konci).
   Mob v 90 min spolehlivě dodá 2, ambiciózně 3 s degradovanou kvalitou.
   Paralelní spolehlivě 3.
4. **Politika je toxická** (Decider má historii overridů, juniors se
   bojí mluvit). Paralelní + silent dot voting = anonymizace. Mob = 6
   lidí čte řeč těla Decidera každých 30 sekund.
5. **Per-person engagement matters pro retention** (junioři, kteří se
   v mobu 80 % session koukají, odcházejí frustrovaní). Vibe-product
   metric „% session active" = 16 % v mobu vs 100 % v paralelním
   (per `00-brief.md`).

## Mob-specific pitfalls (co se rozbije)

### P1 — Driver capture (1 senior kóduje, 5 koukají)
Bez **strict timer-based rotation < 8 min** se nejrychlejší typer stane
de facto perma-driverem. Coding pace asymetrie v 6-osobním týmu je
typicky 3-4×. Fix: **8-min rotace timer-driven, ne task-driven** (žádné
„dokódím tuhle funkci"). Llewellyn Falco's mob-timer norm.

### P2 — Decider implementation pre-bias
V paralelním Decider hlasuje poslední, silent. V mobu Decider vidí každý
keystroke a tichá řeč těla (povzdech, „hmm") implementaci ovlivní dřív,
než bude vůbec k hlasování. Vibe-coding s Deciderem v místnosti =
vibe-coding pro Decidera, ne pro problém. Fix: **Decider sedí mimo stůl
(observer chair), nemá hlas v navigaci, smí pouze parking-lot otázky
po skončení varianty**. „Decider mute" kontrakt podepsaný v Charteru.

### P3 — Observer fatigue + Slack drift
Po 18-22 min observation engagement koleje k nule (group attention
research, Bligh 2000). 4 lidi v 90 min mobu = každý je observer ~70 min
= telefon out v 35. minutě. Fix: **rotace driver+navigator+observer každých
8 min**, observers mají **explicit task** (timekeeper, tester, scribe,
risk-watcher), ne „koukat na obrazovku".

### P4 — Groupthink amplification
6 lidí staví 1 řešení = 6× confirmation bias. Když navigátor #2 řekne
„jo to funguje", 4 observers přitakají i kdyby to nefungovalo. Asch
conformity (1956) replikováno v code review kontextu (Bavota 2015).
Fix: **povinný Pre-mortem TRIZ mezi variantami** (5 min, každý 1
failure scenario na sticky note silent), ne pouze na začátku session
jako v `04-session-1.md`.

### P5 — Cross-functional cognitive overload
6 distinct lenses (PdM/FE/BE/UX/QA/Decider) force-fed serially na 1
obrazovku = každý observer parsuje kód přes **vlastní lens** + kontext
švih každých 8 min při rotaci. Working memory limit (Cowan 4±1) je
po 30 minutách prázdný. Fix: **lens assignment per varianta**, ne per
session (varianta A = optimalizováno pro UX lens; varianta B = pro BE;
varianta C = pro QA). Paradoxně **mob + lens-rotation = strukturovaná
diverzita**, nikoli groupthink.

### P6 — Vote-flow break
Pflanzer voting flow (`/pflanzer` step 5) hlasuje per varianta × per
role = 6 rolí × 3 varianty = 18 hlasovacích bodů. V mobu, kde celý tým
postavil všech 6/3 dohromady, hlasy jsou vzájemně závislé (každý hlasuje
pro „svou" rotaci). Fix: viz § Integration s Pflanzer níže.

## Concrete protocol design — Mob 90 min

### Timing tabulka (4-6 lidí, 1 monitor, 2-3 sequential variants)

| Čas | Blok | Aktivita | LS struktura | Driver / Nav / Obs |
|-----|------|----------|--------------|--------------------|
| 00:00–00:08 | Open | VoC ritual (3 citace, 1 audio) + Decider-mute kontrakt podpis | **Impromptu Networking** krátce | Facilitátor vede |
| 00:08–00:18 | Frame | JTBD lock + 3 hypotézy (1 per varianta) na sticky | **1-2-4-All** (1 min sami → 2 dvojice → 4 → all) | Facilitátor + PdM |
| 00:18–00:23 | Pre-mortem | „Za 6 měsíců 1. varianta selhala, proč?" silent na sticky | **TRIZ** | Facilitátor |
| **00:23–00:48** | **Variant A — mob build (25 min)** | Hypotéza A, prompt napíše navigator, driver kóduje | **Mob timer 8 min**, 3 rotace | A1: D=FE, N=PdM, Obs=UX/BE/QA<br>A2: D=PdM, N=UX, Obs=...<br>A3: D=UX, N=BE, Obs=... |
| 00:48–00:53 | Reset + Pre-mortem B | Driver clears screen, **fresh git branch**, sticky pre-mortem variant B | **TRIZ** | Facilitátor |
| **00:53–01:18** | **Variant B — mob build (25 min)** | Hypotéza B, **jiný framing**, NE pokračování A | **Mob timer 8 min**, 3 rotace | rotace pokračuje, nikdo z A nedělá driver v B první rotaci |
| 01:18–01:23 | Break | Fyzický reset, telefon povolen, Decider mute pokračuje | — | — |
| **01:23–01:38** | **Variant C — mob build (15 min, optional)** | Pokud time-box dovolí; jinak skip | **Mob timer 5 min** | další rotace |
| 01:38–01:48 | Silent vote + Decider's call | Per varianta × per role 4 dimenze, **Decider hlasuje poslední** | **1-2-4-All voting**, Mentimeter / fyzické dot stickers | Facilitátor + Decider |
| 01:48–01:30 | Wrap | Commitment 0-3, parking lot, handoff link | — | Facilitátor |

> **Total: 90 min, 2-3 variants, 0% Decider-driven, 100% rotated driver/nav.**

### Role rotation cadence

- **8 min driver** (Falco norm), žádné výjimky
- **Driver advance rule**: nový driver = bývalý navigator. Bývalý driver →
  observer queue. Žádný „skip mě" — kdo neumí stack, **smí napsat
  pseudo-code, navigator přepíše**. Strong-style mob (Falco): „for an idea
  to go from your head into the computer, it MUST go through someone
  else's hands".
- **Observer task assignment** (na začátku každé varianty):
  - **Timekeeper**: hlásí 1 min do rotace
  - **Tester**: píše acceptance check (Gherkin) souběžně s kódem
  - **Risk-watcher**: sticky každý smell (security/a11y/perf)
  - **Scribe**: decision log v reálném čase

### Decider protocol (kritický)

- Decider **fyzicky mimo stůl** (observer chair, 1.5 m za týmem)
- Decider **mute** během build phase (pouze parking-lot otázky po varianta-end)
- Decider **hlasuje poslední** (per `04-session-1.md` § HiPPO push)
- Decider **rationale POVINNÝ** pokud override jakékoli silent vote
- Pokud Decider chce vyzkoušet driver = **break model**, přepiš na paralelní

## Variants v mobu — kolik a jak diverse

**Realistická čísla** (z LDJ + mob practice):
- 4 lidé, 90 min: spolehlivě 2 varianty, ambiciózně 3
- 6 lidí, 90 min: spolehlivě 2 (víc rotation overhead)
- 6 lidí, 120 min: spolehlivě 3 (ale `04-session-1.md` cap je 90 min
  pro `/pflanzer` quick mode → drž se 2)

**Diversity guarantee** (povinné rituály):
1. **Reset mezi variantami** (fresh git branch, blank screen, žádný copy-paste)
2. **Driver ban per varianta** (kdo dělal driver v A 1. rotaci, nesmí v B 1. rotaci)
3. **Pre-mortem TRIZ per varianta** (ne jen na začátku)
4. **Different framing prompt** (A = happy-path, B = guided, C = smart-defaults
   per `quick_session.py prompts --n 3`)

Bez těchto 4 rituálů mob inherentně produkuje 1 řešení × 2 varianty
= patch series, ne 3 nezávislé varianty.

## Integration s Pflanzer

### Wizard mode select (`/pflanzer`, step 2.5)

Mezi krokem 2 (Decider + Room) a krokem 3 (Risk Profile) přidat:

```
AskUserQuestion: "Jak budete dnes pracovat?"
options:
  - "Paralelně — 3 dvojice, 3 worktrees" (default; max diversity, 3 variants)
  - "Mob — 1 monitor, sequential variants" (shared understanding > diversity, 2-3 variants)
  - "Hybrid — 2 paralelní + mob revue" (v3, defer)
```

### Auto-recommend na základě signálů (Charteru)

| Charter signál | Doporuč mob | Doporuč paralelní |
|----------------|-------------|--------------------|
| Tým < 5 lidí | ✓ | |
| Nový tým / nová BU | ✓ (onboarding) | |
| Vetovací role povinná (Sec/Legal/EM) | | ✓ (shadow agents) |
| Risk profile = production | | ✓ (audit trail per varianta) |
| Decider chce „feel" implementaci | ✓ + mute kontrakt | |
| XYZ hypotéza wide solution space | | ✓ (anchoring risk) |
| Customer-facing + A11y | | ✓ (axe-core paralelně) |

### `worktree.py setup --mob`
1 worktree místo 3, branche `feat/<slug>-mob-A`, `feat/<slug>-mob-B`,
`feat/<slug>-mob-C` (sequential, ne paralelní). Rotation log v
`docs/decisions/<slug>-mob-rotation.log` (auditovatelný driver per timestamp).

### Voting flow změna (kritická)

V mobu **nemůžeš hlasovat per varianta × per role** klasicky — všichni
stavěli vše. Místo toho:

1. **Per varianta × 4 dimenze** (user_value, effort, risk, strategic_fit) =
   silent dot voting **per osoba** (ne per role), Mentimeter / fyzické
   dot stickers, 1-2-4-All adapted (1 min sami → 2 dvojice → all).
2. **Role-lens reflection** (5 min): každý zapíše „v které variantě moje
   role nejvíc utrpěla, proč" (rationale POVINNÝ). To je proxy za
   per-role preference.
3. **Decider's call** = identický s paralelním (`/pflanzer` step 6),
   ale s mute-kontrakt audit (zda Decider držel mute → log).
4. **Commitment level 0-3 per persona** = stejný jako paralelní.

### Facilitator agent prompt změny

V `.claude/agents/facilitator.md` přidat sekci:

```
## Mob mode (--mode=mob)
- variants: max 2 (spolehlivě), 3 (ambiciózně, time-boxed warning)
- role_preferences: collected per-osoba, ne per-role; lens reflection
  field POVINNÝ
- driver_rotation_log: required artefact (per-timestamp who-typed)
- decider_mute_audit: bool (true = Decider neudal verbal direction
  během build phase)
- pre_mortem_count: musí být >= variant_count (1 pre-mortem per varianta)
```

## Reference

- `docs/methodology/04-session-1.md` § HiPPO push, § Energy curve
- `.claude/commands/pflanzer.md` § KROK 4 (builder prompts), § KROK 5 (voting)
- `.claude/agents/facilitator.md` § Output formát
- Liberating Structures: 1-2-4-All, TRIZ, Impromptu Networking
- Falco/Zuill: strong-style mob, mob-timer norm (8 min)
- Asch (1956), Cowan (2001), Bligh (2000), Hallihan/Shu (2012)
