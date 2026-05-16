# Method Falsifiability — Key Themes

> Společné motivy napříč 4 perspektivami (01 Steward, 02 Data, 03 VP, 04 Akademik).
> Theme = pattern, který zazněl alespoň ve 3 ze 4 perspektiv.

## Theme A — „Charter v0.2.1 = audit-grade vocabulary on top of operationally hollow spec"

**Kdo říká:** všichni 4.

**Detail:** Method Charter má správný **slovník** (XYZ hypothesis, threshold, kill
criteria, baseline, reinforcement). Má správný **intent** (self-applied discipline,
audit committee defensibility). Chybí **operational stack** — instrumentation,
data sources, pre-registration, statistical power, comparison fairness, drift
detection, post-mortem disclosure.

**Symptomy:**
- Method Steward: *„Bez instrumentation specu Steward T+6 nedodá report — dodá esej."*
- Data analyst: *„7/50 statistical-rigor scorecard. Audit-grade fail."*
- Skeptický VP: *„Charter naplňuje 9 z 10 graveyard patternů."*
- Akademik: *„Major revision, borderline reject. Vocabulary bez evidence chain."*

**Implication:** v0.3 NESMÍ být kosmetický refactor (přepsat 3 odstavce). MUSÍ
být **structural rewrite** — sekce, ADR-y, nové dokumenty, nové role contracty.

## Theme B — „Practitioner authority vs Academic authority je hybridované — vyber si"

**Kdo říká:** Akademik explicit, Skeptický VP a Data analyst implicit.

**Detail:** Current Charter má hybrid framing — *„kill po 6 pilotech"* (business
decision) + *„≥ 50 % time reduction"* (quasi-scientific claim). Žádné z toho
nelze obhájit současně — N=6 nedostane statistical power pro -50 % claim,
ale stačí na business decision *„this isn't going anywhere"*.

**Resolution:** Charter v0.3 explicitně rozliší:
- **Practitioner track** (business decision, ~T+18 mo timeline, N=8-12 + time-bound,
  internal governance) → Method Charter primary scope.
- **Academic track** (publication validation, ~3-5 let timeline, N=12-20 multi-org,
  external research program) → opt-in side track pokud org má academic partner.

Akademik explicit: *„Vyberte si nebo rozdělte. Charter dnes hybriduje."*

## Theme C — „Method survival cost = byrokratický cost, ne metodický cost"

**Kdo říká:** Skeptický VP explicit, Method Steward implicit (Steward operating
model section), Data analyst implicit (~20 PD + 12 h/pilot blind review).

**Detail:** Pflanzer hodnotová proposice je *„rychlost a alignment"*. Aby
metoda **přežila 18+ měsíců**, potřebuje byrokratický overhead, který hodnotovou
proposici **explicitně ředí**. Tohle je trade-off, který autorům není pohodlný.

**Konkrétně:**
- **Method Steward**: 0.5-0.7 FTE = €100-150k OPEX ročně.
- **External blind acceptance review**: 36 h × interní rate per pilot.
- **External red team (consortium)**: legal contracts, peer org agreements.
- **Project Class Taxonomy + baseline mining**: 5-10 PD setup + ongoing maintenance.
- **Pre-registration audit trail**: signed document per pilot.
- **Compliance Score audit**: ex-post per pilot, ~2-4 h Steward.

**Implication:** Charter v0.3 obsahuje **CFO-readable cost section** s explicit
budget lines. Bez toho je Pflanzer v rozpočtovém procesu *budget vapor*.

## Theme D — „Pre-registration je univerzální blind spot"

**Kdo říká:** Data analyst (M4 pre-registered decision rule), Akademik (Gap 1
ad-hoc rescue), Method Steward (instrumentation tabulka před pilotem),
Skeptický VP (Charter version pinning).

**Detail:** Current Charter má fit criteria + threshold, ale není pre-registered
před pilot 1. To znamená:
- **Garden of forking paths** (Gelman & Loken 2014): post-hoc redefinice fit
  criteria pro „úspěšný" vs „neúspěšný" pilot.
- **Drift detection nemožný**: bez signed baseline „takhle metoda vypadá v0.X"
  není jak detect, že po 18 měsících je to *„Pflanzer-inspired"*.

**Resolution v0.3 — pre-registration discipline:**
1. **Fit criteria signed pre-pilot** (OSF-style preregistration).
2. **Statistical test pre-registered** (α, power, MDE, test type, multiplicity correction).
3. **Charter version pinned per pilot** (e.g. „pinned: v0.3.2, deviations: [list]").
4. **Compliance Score requirements** (Skeptický VP) jako fidelity check.

## Theme E — „Acceptance / success je open-by-default Goodhart-loop"

**Kdo říká:** Data analyst (Flaw 6 Goodhart na self-reported acceptance),
Skeptický VP (NPS bez infrastruktury, response bias), Akademik (Gap 8
Reflexivity / Steward jako advocate-measurer), Method Steward (bod 6
self-declared acceptance je political).

**Detail:** Current Charter měří success interními metrikami od stran, které
mají incentive na pozitivní výsledek (EM dev týmu, post-pilot NPS, Method
Steward agregace). Žádný blind step, žádný external check, žádný negative
incentive na truthful reporting.

**Resolution v0.3:**
- **Blind external EM panel** pro acceptance (3 EMs z jiných BU, average).
- **External red team** v T+12 review (peer-org observer).
- **Re-work shadow ledger** (Jira labels, audited quarterly, ne self-report).
- **Replication audit** po N=6 pilotech (external auditor replikuje 2 pilots).

## Theme F — „Time-bounded kill je nezbytný; čistý N-based threshold v korpu nikdy nespustí"

**Kdo říká:** Method Steward (kill criteria time-bounded variants), Skeptický
VP (Útok 2 — T+24-30 mo throughput problem), Data analyst (interim analysis
at N=6).

**Detail:** *„Po 10 pilotech"* v reálné bance = T+30 mo = 3× CPO change + 2×
reorg + Method Steward turnover. Pure N-based kill criteria nikdy nedosáhne
trigger conditions — místo toho metoda *zombifikuje*.

**Resolution v0.3:**
- **Time-bounded triggers** ve formě „N pilotů NEBO T+X mo (whichever first)".
- **Early-kill veto** pro Method Steward (Skeptický VP × Method Steward shoda).
- **Default Sunset po T+18 mo** bez explicit Keep memo.
- **Interim analysis at N=6** s futility check (Data analyst formal mechanism).

## Theme G — „Steward jako advocate-measurer je conflict of interest"

**Kdo říká:** Method Steward (otevřená otázka #2 a #3), Skeptický VP (Útok 3
budget vapor + selekční kritéria), Akademik (Gap 8 positionality).

**Detail:** Method Steward je *„person who proposes the method continues"*
**a zároveň** *„person who measures whether it works"*. Conflict of interest
na úrovni, kterou akademická literatura standardně řeší externí raterem.

**Resolution v0.3:**
- **Steward NEPOČÍTÁ acceptance score** — to delegate na blind external EM panel.
- **Steward selekční kritéria**: alumnus ≥ 1 pilotu (zná metodu) + signed
  conflict-of-interest disclosure (žádný osobní stake na adopci).
- **Method Decider má direct line k Stewardovi**, ne přes Champion (Method
  Steward bod #2 perspective).
- **T+12 review obsahuje external red team observer** (Skeptický VP) — explicit
  outside check na Steward interpretation.

## Theme H — „Generalization claim není ex-ante kvalifikován"

**Kdo říká:** Akademik (Gap 6 over-claimed generalizability), Skeptický VP
(Project Class Taxonomy missing), Data analyst (propensity matching missing).

**Detail:** Charter implicitně cílí *„velké korporace s AI vibe-coding"*, ale
realisticky první piloty budou v jedné organizaci, jedné industry, podobném
size bracketu. Type EE generalization (Lee & Baskerville) napříč organizace
vyžaduje **explicit replication logic** + multi-context replication.

**Resolution v0.3:**
- **Charter sekce „Scope of validity claims"** explicitně mapuje N pilotů → defensible claim.
- **Project Class Taxonomy** (A/B/C/D) + minimum N per class před cross-class claim.
- **Pre-registered moderators** (Decider authority, AI tooling maturity,
  Champion presence, regulatory load, org size) — Akademik kauzální model
  je incorporated.

## Co se z key themes překlápí do v0.3 action items

Z 8 themes vznikají **6 strukturálních změn**:

1. **Method Charter v0.3 structural rewrite** (Theme A + B) — practitioner /
   academic track split, explicit operational stack.
2. **Pre-registration discipline + Compliance Score** (Theme D + G) — signed
   pre-pilot, Charter version pinning, fidelity check.
3. **Multi-vrstvý acceptance measurement** (Theme E + G) — blind EM panel,
   external red team, re-work shadow ledger.
4. **Time-bounded kill criteria + Default Sunset** (Theme F) — N=8-12 + T+18 mo,
   default Sunset, Steward early-kill veto.
5. **Budgetary realism** (Theme C) — Method Steward 0.5-0.7 FTE €100-150k,
   bootstrap budget €40k, CFO-readable cost section.
6. **Generalization explicit** (Theme H) — scope of validity claims tabulka,
   Project Class Taxonomy, moderators identification.

Ne všech 6 changes je P0 pro v0.3 PR. Viz `07-recommendations.md` pro priority.