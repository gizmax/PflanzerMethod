# Method Falsifiability — perspektiva Method Stewarda

> Autoresearch round 1, role: **Method Steward** (10 % FTE, interní operátor
> metody, vlastník T+6 / T+12 reportu, signatář návrhu Kill / Iterate před
> CPO / DoE).
>
> Vstupy: `method-charter.md` v0.2.1, ADR-0007, devil's advocate Útok 12,
> `00-tldr.md`.
>
> Audience: autor metody (Pflanzer) + budoucí Method Decider (CPO/DoE),
> kteří musí Charter podepsat **jako operační dokument**, ne jako manifest.

---

## Verdikt

Method-level Charter v0.2.1 je **správně postavený jako koncept**, ale jako
operační dokument je **non-functional**: ze čtyř success metrik je
1 reálně sběratelná po 1 pilotu, 1 po 3 pilotech, 2 jsou neměřitelné bez
infrastruktury, kterou Charter neuvádí. Tři kill criteria (3/6/10 pilotů)
jsou formulována tak, že **první trigger-able point je T+18 měsíců** —
což je hluboko za bodem, kdy by Method Steward o metodě řekl „funguje /
nefunguje". Charter chybí: (1) baseline collection playbook, (2) per-pilot
instrumentation spec (co konkrétně se zapisuje, kde, kdo, kdy), (3) leading
indicators v horizontu T+30 dní, ne T+6 měsíců, (4) Method Steward decision
checklist (kdy svolat method-level review mimo plánovaný T+6 cyklus).
Bez těchto dodatků je Method Steward role „person who writes the death
certificate after the patient has already left the hospital".

---

## Co Method Charter dělá dobře

1. **Existuje vůbec.** Většina interních frameworků v korporátu nemá
   own falsifying criterion. Tím, že Pflanzer si vynucuje vlastní XYZ
   hypotézu, mizí asymetrie *„zhasnu projekt, ale ne metodu, kterou jsem
   pro něj použil"*. To je epistemicky korektní a unikátní v segmentu.
2. **Hierarchie metrik je čistá.** Primary lagging (time-to-handoff)
   + leading (handoff acceptance) + guardrail (re-work) + sentiment (NPS).
   Žádná metrika není odvozená z jiné, žádná není proxy bez konkrétní
   target hodnoty. To umožňuje při Kill review jednoznačně říct, která
   metrika selhala.
3. **Kill criteria jsou **gradované** (3 / 6 / 10 pilotů).** Není to
   binární „after N pilots, decide". Každý threshold měří jiný failure
   mode: 3 = morální adoption signal (zhasínají sami), 6 = numerical
   efficacy (zlepšení < 25 %), 10 = sustainability bez vendor coache.
   To je jediná veřejná methodology, která ve své kill logice rozlišuje
   *efficacy failure* vs *adoption failure*.
4. **Audit-committee odpověď v Charteru explicitně formulovaná.**
   Sekce „Audit-committee odpověď" (řádky 73–79) je technika ze sales
   playbooku — definovat předem, jak zní odpověď na otázku, kterou
   dostaneš za 6 měsíců. Většina internal methods nemá ani draft této
   odpovědi.

---

## Co chybí pro reálnou operacionalizaci

### 1. Success thresholds jsou definované, ale nejsou **instrumentované**

Charter říká: *„Time-to-handoff ≤ 50 % baseline, měřeno per pilot,
agregováno T+6 mo."* To je **policy**, ne **měření**. Operacionální
dotazy, na které Charter neodpovídá:

| Metrika | Otevřené operacionální otázky |
|---|---|
| Time-to-handoff | Kde začíná měření? První Charter session? Anebo Discovery Readiness Gate sign-off? Kde končí? `git tag handoff-vN`? Anebo developer „accept" v Jira? Kdo zapisuje timestampy? Pflanzer tool? Method Steward ručně? Jaký field v jakém systému? |
| Handoff acceptance | „≥ 80 % artefaktů použito v T+30." Co je *artefakt* (Charter, OpenAPI spec, ADR, Gherkin scenarios — řekněme 5–7 položek)? Kdo certifikuje *použito*? EM dev týmu (Charter to tvrdí), ale podle jakého důkazu — git diff? Jira link na ticket s reference na artefakt? Self-declared? |
| Re-work % T+90 | „≤ baseline current state." Re-work jako co? Reopen rate ticketů? PRs s revert? Hotfixes do 90 dní? Definice **re-worku** chybí. V InvestmentBotu jsem to já a další tým definovali 4 různými způsoby. |
| Stakeholder NPS | „≥ +20, post-pilot survey." Survey kdy přesně? T+7 (čerstvé, ale ovlivněné session euforií)? T+30 (poctivější, ale low response rate)? Vzorek = jen účastníci sessions, nebo i dev tým, který artefakty převzal? |

**Bez instrumentation specu Method Steward T+6 nedodá report** — dodá
manuální esej s odhady.

### 2. Sběratelnost per pilot vs per N pilotů — Charter to nemíchá, ale neoddělené

Realita sběru dat napříč piloty:

- **Po 1 pilotu sběratelné:** time-to-handoff (1 datapoint, bez agregace),
  handoff acceptance v T+30 (5–7 artefaktů × 1 pilot), NPS (1 survey).
  Kvalitativní retro (Champion).
- **Po 3 pilotech sběratelné:** median time-to-handoff, distribuce
  acceptance %, dispersion NPS, *„zhasnul / pokračuje" rate* (Kill criterion
  po 3 pilotech).
- **Po 6 pilotech sběratelné:** re-work % T+90 (jen pro piloty
  > 90 dní staré, takže reálně jen 3 ze 6 prvních pilotů), trend
  time-to-handoff (zlepšuje se s tím, jak tým zraje?), late-stage veto
  count.
- **Po 10 pilotech sběratelné:** organic Champion pipeline metric
  (kolik z 10 pilotů produkovalo nového Champion-trained kandidáta?
  Charter to neměří — měl by).

**Co Charter chybí:** explicitní tabulka *„po jakém N pilotů kterou metriku
poprvé reálně máš"*. Bez ní Method Steward T+3 piloty publikuje report,
v kterém 2 ze 4 metrik chybí, a CPO si pomyslí *„metoda zatím nemá data"*
— špatný retention signal.

### 3. „Baseline 3 měsíce před prvním pilotem" je **operačně nesplnitelný** bez exec mandate

ADR-0007 říká: *„Baseline metric collection 3 měsíce před prvním pilotem.
Light: 5–10 reprezentativních projektů, manuální estimace nebo project
tracker analysis."*

To je hezky napsané a v praxi to znamená:

- Method Steward dostane mandate sbírat metriky z 5–10 *cizích* projektů.
- Cizí PM-ové nemají důvod spolupracovat („proč moje data?").
- Project tracker analysis (Jira / Asana / Confluence) je notoricky
  šumavá — issue je často založen 2 týdny po skutečném startu „nápadu",
  closure neoznačuje skutečné dokončení handoffu.
- 3 měsíce = 1 kvartál. Korporátní orgs reorganizují v průměru každých
  18 měsíců (zdroj: Gartner). Pravděpodobnost, že baseline ownership přežije
  start prvního pilotu, je < 70 %.

**Co Charter potřebuje:** baseline collection **playbook** —
ne policy. Konkrétně:

- **Vzorek 5–10 projektů — kterých?** Definice: projekty
  cross-functional (3+ oddělení) s velikostí 8–40 person-days,
  uzavřené v posledních 12 měsících. Method Steward žádá od EM
  každého participating BU 2 takové projekty.
- **Data points per projekt:** start date (Jira issue created),
  handoff date (PR merged or feature-flag enabled), re-work proxy
  (count of post-merge hotfixes do T+90), survey 5 otázek post-hoc
  Likertem od 3 účastníků projektu.
- **Time budget per projekt:** 2 hodiny analýzy + 30 minut interview.
  10 projektů = 25 hodin = 3 práce dny Method Stewarda.
- **Sign-off:** baseline report podepsán Method Decider PŘED tím, než
  start prvního pilotu. Bez sign-off pilot neběží.

### 4. Kill criteria po 3 / 6 / 10 pilotech jsou **trigger-not-triggerable** v korporátu

Realistická timeline v cílové organizaci (předpoklad: 1 pilot = 6–9 týdnů
+ T+90 lag pro re-work metric = ~5 měsíců total cycle):

- Pilot 1 startuje T+0.
- Pilot 1 dokončen handoff T+2 mo.
- Pilot 1 plně měřitelný (T+90 done) T+5 mo.
- Piloty 2, 3 mohou běžet paralelně, ale pouze pokud máš 3 Champions
  trained. Realistická assumption v early-stage adoption: 1 Champion,
  serial piloty.
- → 3 piloty plně měřitelné: **T+15 mo**.
- → 6 pilotů: **T+30 mo**.
- → 10 pilotů: **T+50 mo**.

Devil's advocate Útok 12 to říká: *„audit committee otázka první minuty:
kolik pilotů prošlo"*. Po T+18 mo má Method Steward
v nejlepším případě **3 piloty s kompletními daty**. Kill rozhodnutí
po 3 pilotech tedy přichází T+15–18 mo. Kill po 6 pilotech přichází T+30 mo.

**V tom okně se metodu už nikdo neopováží killnout:**
politický cost je sunk (Champion-of-Champions má reputaci postavenou
na adopci), CPO se rotuje (avg tenure CPO v scale-upu = 24 mo, zdroj:
Sequoia 2024). Trigger-ability je v praxi **0**.

**Co Charter potřebuje:** kill criteria **per pilot count + per time
elapsed**, pokud čas elapse rychleji. Příklad reformulace:

| Trigger | Reformulace |
|---|---|
| Po 3 pilotech > 50 % zhasne | **Po 3 pilotech NEBO T+12 mo (whichever first), pokud retention < 50 %** |
| Po 6 pilotech zlepšení < 25 % | **Po 6 pilotech NEBO T+18 mo, pokud zlepšení trend < 25 %** |
| Po 10 pilotech < 3 self-sustaining BU | **Po 10 pilotech NEBO T+30 mo, pokud Champion pipeline < 2 nových** |

Bez time-bounded variant je „po N pilotech" silně manipulovatelné:
Method Steward (nebo jeho šéf) může artificially delay další pilot,
aby zabránil triggeru.

### 5. Leading indicators v horizontu T+30 — **chybí úplně**

Charter má:
- Leading metric: handoff acceptance T+30 (per pilot, 1 datapoint).
- Lagging: re-work T+90.
- Method-level agregace T+6 mo.

Co chybí: **leading indicators na method-level v horizontu T+30 dní**,
které Method Steward sleduje na dashboardu *ráno*. Konkrétní návrhy:

| Indicator | Měřeno | Trigger |
|---|---|---|
| Pre-flight gate rejection rate | % charterů, které neprošly Discovery Readiness Gate | > 40 % → metoda se aplikuje na špatné projekty → review fit criteria |
| Session 1 → Session 2 churn | % pilotů, kde S2 nestartuje do 14 dní po S1 | > 30 % → ztráta momenta, alignment problem |
| Champion-of-Champions overload | průměrný počet open pilotů per Champion | > 3 → scaling bottleneck, nevíme, jestli to trénuje nebo brzdí |
| Decider tie-breaker frequency | % decisions, kde Decider musel rozhodnout (vs konsensus) | > 50 % → metoda nedoručuje alignment, jen formalizuje veto |
| Throwaway → evolve gate slippage | % pilotů, kde throwaway artefakt nakonec evolved | > 20 % → governance leak (ADR-0005) |

Tyto indikátory **nezdvojují** Charter primary metrics — jsou to
*early-warning signals*. Bez nich Method Steward zjistí, že metoda
nefunguje, až po 5 měsících. S nimi to může říct po 4 týdnech.

### 6. Method Steward role — minimum viable scope **není definován**

ADR-0007 říká: *„Method Steward — sleduje metrics across pilots, publikuje
T+6/T+12 reporty, agreguje retros do role catalog updatů."*

To je popis výstupu, ne popis práce. 10 % FTE = 4 hodiny týdně.
Co se v tom okně dělá konkrétně?

**Můj návrh MVP scope Method Stewarda (cca 4 h/týden):**

| Cadence | Aktivita | Time |
|---|---|---|
| Per pilot (jednorázové) | Sign-off Charter (XYZ + kill criteria), zkontrolovat baseline assignment | 1 h |
| Týdně | Update method dashboard (5 leading indicators above), zaznamenat anomálie | 1 h |
| Měsíčně | 30-min sync s Champions napříč piloty (cross-pollination retros), update role catalog ADR pokud frikce | 2 h |
| T+30 per pilot | Sběr handoff acceptance dat od EM, zápis do tracker | 1 h |
| T+90 per pilot | Sběr re-work dat, NPS readout, per-pilot mini-report | 2 h |
| T+6 mo | Method-level agregátní report → CoP | 8 h (jednorázový spike) |
| T+12 mo | Method-level review session s Method Decider | 4 h |

**Co je nice-to-have (NE-MUST):**
- Aktualizace metodiky dokumentace per learning.
- Externí publikace (blog, talks).
- Trénink nových Champions (to je Champion-of-Champions, ne Steward).

**Co MUSÍ Method Steward dělat, i kdyby měl jen 4 h/týden:**
1. Vlastnit baseline collection a sign-off (jinak XYZ hypotéza
   nemá ground truth).
2. Vlastnit per-pilot metric collection ownership (i kdyby delegoval).
3. Být **eskalační autorita pro Kill trigger** — pokud žádný indikátor
   neprůjde, MUSÍ svolat Method Decider review do 30 dní.

**Co Charter musí přidat:** Method Steward operational checklist + RACI
matrice (kdo zapisuje data, kdo agreguje, kdo rozhoduje).

### 7. Dashboard, který odpoví na ranní otázku „funguje metoda?"

Charter zmiňuje *„Method Steward publikuje report do CoP / Confluence"*.
To je outbound. Co chybí: **inbound** — Method Steward potřebuje **vlastní
dashboard**, na který se ráno dívá. Pokud ho nemá, T+6 report je
sestavovaný retro z paměti a interview.

**Minimum dashboard fields (Confluence table / Notion DB stačí):**

| Field | Per pilot | Source |
|---|---|---|
| Pilot ID, Champion, BU, start date | text | Charter sign-off |
| Pre-flight gate sign-off date | date | Discovery Readiness Gate artefakt |
| S1 date, S2 date | date | Session calendar |
| Handoff date | date | git tag / PR merge link |
| Time-to-handoff (days) | calc | (handoff - charter sign-off) |
| Handoff acceptance T+30 (% artefaktů used) | %, 0–100 | EM sign-off form |
| Re-work T+90 (count hotfixes / reopens) | int | Jira query |
| NPS score | -100..+100 | survey form |
| Verdict | go/iterate/kill/throwaway/evolve | Decider session output |
| Status | active / done / killed | manual |

10 řádků = 10 pilotů. Method Steward se na to dívá ráno, vidí trendy,
ví, kdy svolat review. Bez tohoto je „validating loop" jen ritualizovaný
T+6 spike, který se neudělá včas.

### 8. Falsifikace v opačném směru — chybí „what would prove the method works?"

Charter má kill criteria (negativní falsifikace) — co prokáže, že
nefunguje. Chybí **success criteria as discrete events** (pozitivní
falsifikace) — co prokáže, že funguje, nezávisle na měření trendu:

- **Strong success signal:** po pilotu N, BU které pilot nehostovala,
  požádá o pilot **z vlastní iniciativy** (= organic pull, ne push).
  Counter = 0 po 6 pilotech → adoption broken.
- **Strong success signal:** Decider z pilotu N **opakuje** Pflanzer
  metodu na druhý projekt do 6 měsíců. Counter = 0 po 6 pilotech → not
  sticky.
- **Strong success signal:** dev tým, který přebral handoff, **odmítl**
  re-work z důvodu *„v charteru bylo jasno"* (= alignment held). Aspoň
  1× po 3 pilotech.

Toto jsou **lagging adoption indicators**, které doplňují re-work %
T+90. Bez nich Charter měří jen *efficacy* (zrychlení), ne *stickiness*
(používá se to dál).

---

## Konkrétní navrhované úpravy `method-charter.md`

### Sekce „Success threshold" — rozšířit tabulku o instrumentation column

Aktuálně 4 sloupce. Navrhuji 6:

```diff
- | Metric | Cíl | Měřeno | Vlastník |
+ | Metric | Cíl | Definice (start → end) | Data source | Cadence | Vlastník |
```

S příkladem:

```
| Time-to-handoff | ≤ 50 % baseline | Od Discovery Readiness Gate
  sign-off (timestamp ve Charter dokumentu) do `git tag handoff-v1`
  v target repo NEBO PR merged s label `pflanzer-handoff` | Pflanzer
  tool DB (preferred) NEBO Confluence Charter page + Git API | Per
  pilot completion | Method Steward |
```

Bez sloupce „Definice (start → end)" každý pilot zaznamená time-to-handoff
po svém. Bez sloupce „Data source" Method Steward nemá kde data hledat.

### Nová sekce „Baseline collection playbook" (vložit za „Comparison baseline")

Obsah viz bod 3 výše: vzorek 5–10 projektů s konkrétními
kvalifikačními kritérii, data points per projekt, time budget,
sign-off requirement.

### Nová sekce „Per-pilot instrumentation" (vložit za „Baseline collection playbook")

Tabulka s artefakty, které pilot MUSÍ vyprodukovat, aby byl
měřitelný. Bez nich Method Steward pilot nezapočítá:

| Artefakt | Kdy | Kdo | Format |
|---|---|---|---|
| Charter sign-off s timestamp | T-0 | Champion | Pflanzer tool / Confluence |
| Pre-flight gate sign-off | T-7d (před S1) | Champion + Security + Platform | Pflanzer tool |
| Session 1 closeout artefakty | T-end-of-S1 | Champion | scoped epic, OpenAPI, varianty |
| Handoff completion marker | T+handoff | EM dev tým | git tag / PR label |
| T+30 acceptance survey | T+30 | EM dev tým | 5-field form (linked artefakty + % used) |
| T+90 re-work count | T+90 | Method Steward (Jira query) | int |
| T+90 NPS | T+90 | Method Steward | -100..+100 |

### Nová sekce „Leading indicators (method-level dashboard)" (vložit za „Per-pilot instrumentation")

5 metrik z bodu 5 výše, s threshold a action.

### Sekce „Kill criteria" — přidat time-bounded varianty

Reformulace per bod 4 výše. Změnit jednoduchou tabulku na:

```diff
- | Po N pilotech | Kill trigger |
+ | Trigger (whichever first) | Kill condition |
+ | 3 piloty NEBO T+12 mo | > 50 % zhasnutí after S2 |
+ | 6 pilotů NEBO T+18 mo | Avg time-to-handoff ≥ baseline × 0.75 |
+ | 10 pilotů NEBO T+30 mo | < 3 self-sustaining BU; nebo Champion pipeline = 0 |
```

A přidat **early-kill veto** (Method Steward authority):

> Method Steward má pravomoc kdykoli mezi T+0 a T+12 mo svolat
> **emergency method-level review** s Method Decider, pokud 2+ leading
> indicators porušují threshold po dobu > 60 dní. Tím se eliminuje
> *„we need more pilots to know"* lock-in.

### Nová sekce „Method Steward operational scope" (vložit za „Validační loop & sunset")

RACI + cadence z bodu 6 výše. Explicitně oddělit MUST aktivity od
nice-to-have. Plus jasné: minimum **0.1 FTE = 4 h/týden + 8 h spike
T+6 / T+12**.

### Nová sekce „Method dashboard" (vložit za „Method Steward operational scope")

Specifikace tabulky z bodu 7 výše. Reference, kde dashboard žije
(Confluence template? Pflanzer tool view? Notion DB?). Method Steward
**MUSÍ** dashboard aktualizovat týdně. Bez dashboard žije Charter jako
PDF, ne jako proces.

### Sekce „Audit-committee odpověď" — rozšířit o failure scenario

Aktuálně 1 odpověď (success path). Přidat 2. odpověď (failure path):

> Otázka: *„Metoda nefunguje, proč ji ještě používáte?"*
>
> Odpověď: *„X pilotů prošlo, time-to-handoff je W % zlepšení (pod
> threshold). T+12 mo Method Steward review (link) doporučuje
> [Iterate / Kill] s konkrétními změnami v role catalog / fit criteria.
> Decision: [datum] s Method Deciderem."*

To je odpověď, která ukáže, že Method Steward role je funkční i v failure
mode — což je hlavní test methodology integrity.

---

## Otevřené otázky, kde Method Steward bez exec mandate selže

Tyto otázky **nejsou** v Method Steward kompetenci, protože Method Steward
je 10 % FTE interní operátor, ne mocensky figurka. Patří na stůl Method
Decider (CPO/DoE) a v širších otázkách autora metody samotného.

1. **Kdo má pravomoc forcovat baseline collection napříč BU, jejichž PM-ové
   nemají incentive spolupracovat?** Bez exec mandate Method Steward
   dostane 3 z 10 projektů a Charter XYZ je defeato unfalsifiable. CPO
   musí v org-wide announcementu Pflanzer baseline collection vyhlásit
   jako *required*, ne *requested*.

2. **Jaká je politika, když Champion-of-Champions a Method Steward
   nesouhlasí o Kill triggeru?** Champion má adoption incentive (žije
   z aplikace metody), Method Steward má integrity incentive (žije z
   poctivé hodnocení). Konflikt zájmů. Charter neuvádí, jak se řeší —
   v praxi Champion vyhraje, protože má víc politické energie. Method
   Decider musí mít **direct line k Method Stewardovi**, ne přes Champion.

3. **Co když Method Steward sám nevěří v metodu?** 10 % FTE může být
   přidělené někomu, kdo metodu vnímá jako *yet another framework*.
   Charter nemá selekční kritéria pro Method Stewarda. Návrh: Method
   Steward MUSÍ být absolvent aspoň 1 pilotu jako Champion nebo Decider
   (= zná metodu z first-hand), a MUSÍ podepsat conflict-of-interest
   disclosure (žádný osobní stake na adopci).

4. **Co bude s daty po sunset?** Charter říká *„sunset není failure, je to
   methodology hygiene"*. Ale po sunset zbývá DB s 10 piloty, 50+ Charterů,
   role catalog. Kdo to archivuje? Kdo to zveřejní jako post-mortem?
   Korporátní organisations nikdy dobrovolně nepublikují methodology
   post-mortems (= reputační cost > learning value). Bez explicit
   commitmentu „post-mortem se zveřejní externě po N pilotech bez ohledu
   na výsledek" Method Steward selže reciprocity argument — proč by mu
   ostatní pomáhali se sběrem dat, když pozitivní výsledky jdou ven jako
   marketing, ale negativní zůstanou v interní DB?

5. **Měření „baseline current state" má politický náboj.** Current state
   je sériový handoff, který *někdo* vlastní (typicky head of project
   management, head of product ops). Měření jeho baseline =
   demonstrating že existing process je pomalý. Method Steward bez exec
   krytí dostane pushback od owners current state. Návrh: baseline
   collection MUSÍ být formulován jako *„we measure org-wide
   time-to-handoff"*, ne *„we measure how slow your process is"*. To
   je nuance, kterou Charter dnes neřeší.

6. **AI-generated handoff acceptance bias.** Charter neuvádí, jak se měří
   *kvalita* handoff package u Pflanzer pilotů vs baseline. Pokud
   Pflanzer handoff má lepší OpenAPI spec než baseline (protože BE
   shadow agent ho generuje), je to fair comparison? Možná ne —
   srovnáváme apples to oranges. Návrh: comparison MUSÍ zahrnovat
   *„handoff package completeness rubric"* (např. 10-item checklist
   completeness %) jako covariate. Bez toho audit committee řekne
   *„Pflanzer je rychlejší, ale handoff je jiný, srovnání není fair"*.

7. **Self-sustaining BU metrika (kill po 10 pilotech) — definice
   „self-sustaining"?** Charter říká *„organic Champion pipeline"*.
   Operacionální dotaz: BU má self-sustaining, pokud (a) zaškolila
   vlastního Champion, (b) provedla 2+ piloty bez Champion-of-Champions
   help, (c) udržela kvalitu dle metrik. Vše tři? Jen (a) + (b)? Bez
   přesné definice je kill criterion neměřitelné a tedy nevynutitelné.

---

## Závěrečná instrumentation TODO list (priority pro v0.3 Charter)

Pokud bych měl jako Method Steward operacionalizovat současný Charter
zítra, potřeboval bych před prvním pilotem těchto **9 artefaktů**, které
v repo zatím neexistují:

1. `docs/methodology/baseline-collection-playbook.md` — vzorek
   kritéria, 5-field interview script, time budget, sign-off template.
2. `docs/methodology/per-pilot-instrumentation.md` — 7-row artefakt
   tabulka + form templates (T+30 acceptance survey, T+90 NPS form).
3. `docs/methodology/method-dashboard-template.md` — Confluence /
   Notion table spec (10 polí, query examples pro re-work).
4. `docs/methodology/method-steward-raci.md` — operační scope
   + cadence + selekční kritéria pro Method Steward osobu.
5. `docs/methodology/leading-indicators.md` — 5 leading indicators
   + threshold + action playbook.
6. ADR-0008 — *Method Steward early-kill veto authority* (kdy
   Method Steward smí svolat emergency review nad rámec T+6/T+12).
7. ADR-0009 — *Comparison baseline rubric* (jak srovnávat Pflanzer
   handoff vs baseline handoff fair — completeness rubric, covariate
   adjustment).
8. ADR-0010 — *Method post-mortem disclosure commitment* (sunset
   data zveřejněna do N dní bez ohledu na výsledek).
9. `tooling/baseline-collection.sql` (případně Jira JQL templates) —
   queries pro re-work count, late-stage veto count, time-to-handoff
   z existujících tracker systémů.

Bez těchto 9 položek je Method Charter v0.2.1 *spec*, ne *operace*.
Po jejich doplnění Method Steward může ráno otevřít dashboard, podívat
se na 5 leading indicators, a říct *„metoda nezavadla / zaspala /
prostě nefunguje"* — což je primární output role, kterou Charter zakládá.

---

*Sepsáno: 2026-05-16. Role: Method Steward (interní pragmatik). Round:
method-falsifiability autoresearch #1. Další perspektivy: CPO/Decider,
Champion-of-Champions, External skeptik (audit committee proxy).*
