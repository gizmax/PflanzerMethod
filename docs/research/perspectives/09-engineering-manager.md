# 09 — Engineering Manager perspektiva

> Role: EM korporátního týmu 6–8 inženýrů, SAFe rytmus, PI planning + IP iterace.
> 12 let zkušeností, 7 v leadu. Vlastní kapacitu, dependencies a growth lidí.

---

## TL;DR

Pflanzerova metoda je pro mě **nástroj na zabití dvou nejdražších bolestí**:
estimate sliding (3 → 8 sprintů) a dependencies, které vyplavou až ve sprint 4.
Jenže mi taky bere 2–3 dny seniorních inženýrů z capacity, kterou nemám.
Verdict: **fits jen do IP iterace a jen pro scope, kde estimate uncertainty
přesahuje 1 PI.** Pro quick wins je to overkill. Bez explicitního capacity
buffer a dependency map jako deliverable to bude další "hezký workshop",
co se nedostane do velocity.

---

## Co se mi na metodě LÍBÍ (z pohledu kapacity a delivery)

1. **Dev je v místnosti od minuty 0.** Tohle řeší přesně tu situaci, kdy mi
   PM přijde s "hotovým" prototypem z Figmy, dev říká "to nejde za 2 sprinty,
   to je 6", a já jdu eskalovat změnu commitmentu. Pokud dev signs-off na
   variantu během session 1, slipping estimate klesne řádově.
2. **Score závaznosti per oddělení** je geniální. Konečně mám artefakt, který
   ukáže architektovi, že "security řekla yellow, ne green" a já nemusím být
   prostředník v ping-pongu mailů.
3. **Klikací prototyp místo Figmy** = end of "looked done, was 80% left".
   Funkční mockup s dummy daty mi dá realističtější basis pro story-point
   estimate než wireframe.
4. **Handoff není handoff** — když inženýr metodu spoluvytvářel, mizí
   "not-invented-here" odpor. To je tichý win pro morálku týmu.

---

## Co mě DĚSÍ (a musí se to vyřešit)

### Capacity math

2 sessions × 6 hodin × 4 lidé z mého týmu (FE lead, BE lead, QA, někdy DevOps)
= **48 person-hours, ~6 člověko-dnů**, plus prep (~4h FE + 4h BE + 2h QA) a
mezi-session prototype work (~2 dny seniorního FE). Reálný footprint
**8–10 person-days = ~1 sprint kapacity celého týmu na jeden discovery cyklus.**

V PI o 5 sprintech to znamená, že **víc než 2–3 Pflanzer cykly za PI mi
spotřebují 15–20 % kapacity**. Sales mi to v životě nepodepíše bez argumentu,
že to vrátí trojnásobek na zkráceném delivery.

### Estimate sliding přesouvá fázi, neřeší ho

Pflanzer ostří **scope**, ne **složitost implementace**. Pořád hrozí, že
inženýr v session 1 řekne "ok feasible" pod sociálním tlakem zadavatele a
bez seriózního spike. Metoda tu sociální pressure dokonce **zesiluje** —
všichni stakeholders v jedné místnosti, hodiny tikají.

### Dependency overhead chybí

Metoda implicitně předpokládá, že tým, co tam sedí, fíčuru postaví sám.
V korporátu polovina featur visí na platform tymu, identity tymu, data
tymu. Pokud nejsou v session a nedostanou explicitní deliverable, alignment
zůstane jen uvnitř buňky, která metodu používá.

### IP iteration squeeze

IP iterace má **už teď** hackathons, tech debt, PI planning prep, learning.
Pokud Pflanzer cykly nasadím tam, kde je SAFe definuje, vytlačím tech debt
a inovaci. Potřebuju pravidlo, které IP slot komu patří.

---

## Konkrétní vylepšení od EM

### 1. Capacity rule — povolit jen tam, kde to dává smysl

Default trigger pro pozvání EM (povinná role) z catalogu je >2 sprinty / 1 PI.
**Doplnit:** EM má **veto na sám workshop**, pokud:
- pre-session estimate < 1 sprint (overkill, použij LDJ),
- > 50 % nutných rolí je z jiných týmů, které nemají capacity confirm,
- aktuální PI je už nad 80 % committed a Pflanzer cyklus by natlačil tým přes
  red line (capacity buffer 20 % standard pro unknowns).

### 2. PI fit-window — IP iterace jako default slot

V SAFe rytmu je **IP iterace** (sprint 5 z 5, 1–2 týdny) jediný slot, kde
Pflanzer neporušuje sprint commitment. Doporučení:
- **Pflanzer cykly default do IP iterace** — sponzor argumentuje SAFe
  definicí ("structured window for free investigation"), ne novým procesem.
- **Mid-PI Pflanzer** povolit jen pokud sponzor uvolní commit features
  ekvivalentní 8–10 person-days (tradeoff explicit).
- **Pre-PI Pflanzer** (před PI planning) je nejcennější — výstupem je
  **realistický estimate pro PI commitment**, ne discovery sám o sobě.

### 3. Dependency Map jako deliverable

K mockupu a score listu **přidat povinný artefakt: Dependency Map**.
Tabulka: feature komponenta → external team → typ dependency (API contract /
infra / approval / data) → required by date → owner contact.

Bez něj session končí mockupem, který tým samostatně neimplementuje.
Tohle je **největší doplněk metody za sebe**. Ideálně Dependency Map review
dělá platform/architecture guild týden před PI planning.

### 4. Estimate dvoufázově: T-shirt v sessionu, story-point po spiku

V session 1: **T-shirt sizing** (S/M/L/XL) per varianta, ne story pointy.
Pod tlakem místnosti je SP estimate vždy příliš optimistický.

Po session 1 dostává tým **2-day capped spike** (mimo workshop) na verifikaci
předpokladů — perf, integration risk, data volume. Teprve pak SP estimate
do PI commitmentu. Bez spiku **žádný hard estimate nedávat**.

### 5. Capacity buffer 25 % na Pflanzer-discovery-driven features

Features, které prošly Pflanzer cyklem, dostanou **25 % buffer** v PI
commitmentu (vs. 15 % standard). Ne proto, že metoda je nepřesná, ale proto,
že odhaluje větší part of unknown unknowns dřív — a tým si dovolí být
ambicióznější ve scope.

### 6. Champion model + Coaching Kata pro adopci v týmu

Pflanzer **netlačit jako mandate** (Kotter top-down recipe na fail).
- 2–3 dobrovolníci ze seniorů mého týmu jdou na 1. cyklus jako pilot.
- Učím se s nimi v Coaching Kata módu (target → obstacle → next experiment).
- Po 2–3 pilotech vznikne playbook a cyklus se nabízí ostatním.

To je zároveň **growth opportunity** pro seniory, co míří na lead role —
facilitace cross-functional sessionu je ideální stretch.

### 7. Eskalační protokol při dev-PM-security konfliktu

Catalog uvádí, že security má veto. Co když dev v session 1 řekne
"nevejde se to do PI" a sponzor tlačí? **EM má povinný callout** s rétorikou:
"Pokud commitneme, slip = opak Pflanzer cíle." Bez tohoto protokolu se
sociální pressure převálcuje engineering judgement.

---

## Memorabilia — jak metodu obhájit před exec a před týmem současně

**Před execem:** "Pflanzer mi v IP iteraci zachrání **ten** PI commitment,
co bychom jinak slipli. 8–10 person-days investovaných v sprint 5
předchozího PI = 2–3 sprinty ušetřené v dalším PI tím, že nemáme rework
a discovery v boji."

**Před týmem:** "Místo 4 sprintů rework po nesprávně pochopeném zadání
strávíte 2 dny v místnosti, kde **vy** ten zadání spoluformulujete —
a security, PM i sales podepíší výstup ve stejnou hodinu. Žádný ping-pong
mailů, žádné 'oni si představovali jiný'."

Stejná věta, jiný úhel: **šetří čas zítra cenou času dnes.** Pokud to v obou
publikách neříkám se stejnou vážností, jedna z nich přijde o důvěru.

---

## Otevřené otázky

- **Multi-team scope:** Pflanzer pro fíčuru přes 3 týmy = 3× session?
  Federovaný model (per-team mini-session + společná final)?
- **Allocation vůči standard PI ceremonies:** Pflanzer × backlog refinement
  × system demo × IP — kdo má prioritu, když koliduje?
- **Karierní cesta facilitátora** uvnitř engineering org: senior dev → tech
  lead → EM → ? Pflanzer facilitátor je **nový role pattern**, ale jak ho
  positioning na kariérní matrix?
