# Method Falsifiability — Conflict Matrix

> Mapuje **konflikty mezi 4 perspektivami** (01 Method Steward, 02 Data analyst,
> 03 Skeptický VP, 04 Akademik). Konflikt = perspektivy si nárokují různá řešení
> téže otázky. Resolution je návrh syntézy s rationale.

## Top 7 konfliktů

### Konflikt #1 — Minimum N pro kill rozhodnutí

| Perspektiva | Pozice | Rationale |
|-------------|--------|-----------|
| Method Steward | „Po 3 pilotech NEBO T+12 mo" je správný směr s time-bounded variantou | Operacionálně: po N=3 jsou data prvně agregovatelná; time-bounded zabrání political stall. |
| Data analyst | **N=3 v binomické noise floor (CI [21 %, 94 %]).** N=8 floor pro „better-than-coin-flip", **N=12 floor pro current Charter claim (-50 %)**, N=16-20 decision-grade | Power analysis (binomial exact, α=0.10, MDE=0.5). Charter nepřímo požaduje N=12, ale defines kill při N=3 = **vnitřní rozpor**. |
| Skeptický VP | Realistický throughput = 4-6 pilotů/rok → N=10 = **T+24-30 mo**. CPO se 3× změní. → Default Sunset po T+18 mo místo kill-by-N | Tenure profile + sunk-cost asymmetry; bez time-bound metoda zombifikuje. |
| Akademik | Pro publication: Cohen's d=1.0 → N≈17 per group; pro „validated method" claim N=20+ napříč 5 orgs / 3 industries | Cohen 1988, Lee & Baskerville 2003 generalizability. |

**Resolution v0.3:**
- **Rozdělit dva tracky** — **Practitioner track** (business decision) vs **Academic track** (publication-grade).
- **Practitioner track:** N=3 = **informational** (warning lights, ne kill); N=8 = první „kill defensible at α=0.10"; **N=12 = decision-grade kill bod** *NEBO* **T+18 mo default Sunset (whichever first)**. To je akceptace všech 3 praktických hlasů.
- **Academic track:** ne-binding sub-program; běží paralelně, ale Method Charter ho nevyžaduje pro business rozhodnutí. ADR-0007 addendum to explicitly rozliší.

### Konflikt #2 — Method Steward FTE a profil

| Perspektiva | Pozice |
|-------------|--------|
| Method Steward | **0.1 FTE (4 h/týden + 8 h spike T+6/T+12)** je minimum viable; cokoli víc bez hire budget = nereálné |
| Skeptický VP | **0.7-1.0 FTE dedikovaný Senior PdM, €150-200k/rok**, financováno z Engineering Excellence CoE OPEX. *„10 % bez headcount = budget vapor"* |
| Akademik | Steward jako advocate má conflict-of-interest s rolí measurer → **external/blind rater** pro acceptance měření |

**Resolution v0.3:**
- **0.5 FTE dedikovaný** (kompromis), placeno z Engineering Excellence OPEX, ne „EM ve volném čase". Pokud org nemá CoE, **Pflanzer pilot se nestartuje** (early Sunset trigger).
- **Acceptance measurement delegated** na external blind rater (peer EM z jiné BU, viz Konflikt #5). Steward agreguje a interpretuje, nepočítá score sám.
- Selekční kritérium: Steward MUSÍ být alumnus ≥ 1 pilotu jako Champion/Decider + signed conflict-of-interest disclosure (Method Steward bod 6 perspective).

### Konflikt #3 — Method Decider seniorita

| Perspektiva | Pozice |
|-------------|--------|
| Method Steward (implicit) | OK s ADR-0007: CPO / DoE s exec mandate |
| Skeptický VP | **NESMÍ být CPO** — politicky exponovaný, tenure 2.3y, sunk-cost trap. Musí být **VP Engineering Effectiveness / Head of Engineering Excellence** (2 levely pod CTO, tenure 4-7y, JD zahrnuje sunset rozhodnutí) |
| Akademik | Decider role neutrální vůči akademické otázce |

**Resolution v0.3:**
- **Decider = VP Engineering Effectiveness** (nebo equivalent: Head of Engineering Excellence, Head of Process Portfolio), pozice 2 úrovně pod CTO/CIO. JD explicitně zahrnuje process portfolio management + sunset authority. **Aktualizuje ADR-0007** + samostatné **ADR-0011** pro detail.
- Exec committee = Informed (1× ročně summary), ne Accountable.

### Konflikt #4 — Sunset default

| Perspektiva | Pozice |
|-------------|--------|
| Method Steward | „Method Steward má pravomoc navrhnout sunset" — ale default zůstává keep until decided |
| Skeptický VP | **Default = Sunset po T+18 mo** bez explicit Keep memo. Obrácení burden of proof. |
| Data analyst | „Stopping for harm" — kill immediately pokud > 25 % pilotů má handoff collapse, ne čekat na N |
| Akademik | Pre-registered stopping rules (interim analysis at N=6, futility check) |

**Resolution v0.3:**
- **Default Sunset po T+18 mo** (Skeptický VP win) — obrátí inertia od „zombifikace" k explicit decision.
- **Stopping for harm rule** (Data analyst): kill immediately pokud ≥ 25 % pilotů má 0 % artifact utilization v T+30 (handoff collapse).
- **Method Steward early-kill veto** (perspective 01): pravomoc svolat emergency review pokud 2+ leading indicators porušují threshold > 60 dní.
- **Interim analysis at N=6** s conditional power check (Data analyst preregistration spec).

### Konflikt #5 — Acceptance measurement bias

| Perspektiva | Pozice |
|-------------|--------|
| Method Steward | EM dev týmu certifikuje *„použito"* (per current Charter) — ale potřebuje explicit definici „artefakt" + audit trail |
| Data analyst | **Blind external EM panel** (3 EMs z jiných BU, strip metadata, average Likert + numerical estimate). 12 h/pilot. |
| Skeptický VP | **External red team / peer-org observer** v T+12 review (consortium model: 3 banky se vzájemně red-teamují) |
| Akademik | **Independent rater blind to outcome**, Cohen's κ ≥ 0.6 + Artifact Utilization Coding Scheme (12 artifact types × 0-3 ordinal) |

**Resolution v0.3:**
- **3-vrstvý acceptance review v0.3:**
  1. **EM dev týmu T+30** (current Charter) — operational signal, fast.
  2. **Blind external EM panel T+30** (Data analyst) — 3 EMs z jiných BU, average. Bias guardrail.
  3. **External red team T+12 review** (Skeptický VP) — peer-org observer, ne single-pilot scope.
- **Coding scheme** (Akademik): Artifact Utilization 12 types × 0-3 → reliability κ ≥ 0.6 jako requirement pro Method Steward report acceptance.
- Cost: ~12 h × 3 EM = 36 person-hours per pilot — započítáno do True Cost Worksheet (regulated profil přírůstek).

### Konflikt #6 — Baseline collection method

| Perspektiva | Pozice |
|-------------|--------|
| Method Steward | „Baseline collection je politicky citlivý, vyžaduje exec mandate" + apples-to-apples comparison rubric |
| Data analyst | **Full population mining** (Jira / Azure DevOps za 24 mo), all matching fit-criteria proxy, **survival analysis** (censored = include) |
| Skeptický VP | „6-9 měsíců baseline" je apples-to-oranges bez **project class taxonomy** (B/C/D). €40k bootstrap budget + dedikovaný Steward 3 měsíce před prvním pilotem |
| Akademik | Multi-rater coding, IRB review pokud akademický partner, Boudreau et al. 2001 validation steps |

**Resolution v0.3:**
- **Project Class Taxonomy** (Skeptický VP) — A/B/C/D s explicit definice; baseline collected per class. Comparison MUSÍ být class-matched.
- **Full population mining** + survival analysis (Data analyst) — nahrazuje „5-10 manual estimace" v současném Charteru.
- **Bootstrap rozpočet €40k + 3 měsíce Steward pre-pilot** (Skeptický VP) — explicit Charter sekce + ADR-0012.
- **Apples-to-apples rubric**: handoff package completeness checklist (10 položek) jako covariate (Method Steward bod 6 + Akademik Boudreau).

### Konflikt #7 — Theory of Why (mechanismus)

| Perspektiva | Pozice |
|-------------|--------|
| Method Steward | Implicit potřeba (leading indicators jako proxy pro mechanism) |
| Data analyst | Konfundery (Champion quality, AI tools, sponsorship) je nutno **identifikovat strategy**; bez toho metoda nemá identification |
| Skeptický VP | Drift detection (pilot compliance score) — bez toho je *„Pflanzer-inspired"* zaměnitelný s Pflanzer |
| Akademik | **Theory of Why** = core gap; bez kauzálního diagramu (5 interventions → 5 mediátorů → 4 outcomes) není theory, jen recipe. Gregor Type V design theory standard. |

**Resolution v0.3:**
- **Adoptovat akademikův kauzální model** jako sekci v `method-charter.md` *„Causal model"*. 5 interventions, 5 mediátorů (Akerlof, Berry & Kamsties, Reinig, Cannon-Bowers, RE traceability), 4 outcomes, moderators.
- **Compliance Score** (Skeptický VP) jako measurement of *„intervention fidelity"* — bez intervention fidelity nelze testovat mediator chain.
- **Leading indicators** (Method Steward) jsou mapovatelné na mediátory — measurement bridge mezi theory a operations.
- **Confounder inventory** (Data analyst) jako explicit Charter sekce.

## Kde se perspektivy překvapivě shodují

- **Pre-registration of fit criteria + decision rule před pilot 1** — všichni 4 mention (Data analyst nejhlasitěji, ostatní implicitně).
- **„Self-applied discipline" je správně, ale undelivered** — ADR-0007 koncepčně OK, implementace chybí. Všichni 4 dávají full credit za intent + plnou kritiku za execution.
- **Time-bounded kill criteria** — Method Steward + Skeptický VP shodně, Data analyst tichý souhlas (přes interim analysis).
- **„Methodology Cost je byrokratický cost"** — Skeptický VP explicit; Method Steward implicit (Method Steward MVP scope); Data analyst implicit (~20 PD + ongoing); Akademik implicit (instrument validation cost).

## Kde se perspektivy nepřekrývají (žádný konflikt, doplnění)

- **Method Steward** vlastní: instrumentation specifika (start/end events, data sources), 9-položkový artefakt TODO.
- **Data analyst** vlastní: composite PflanzerIndex formule, propensity matching design, falsifying acid test spec.
- **Skeptický VP** vlastní: methodology graveyard checklist (10 patternů, Pflanzer naplňuje 9), drift / fork governance, peer consortium model.
- **Akademik** vlastní: 8 methodological gaps s literature anchor, 3-letá research roadmap, theory contribution claim, kauzální diagram.

## Total recommendation count

- **Operational changes (Method Steward):** 9 artefaktů (baseline playbook, instrumentation spec, leading indicators, etc.).
- **Statistical changes (Data analyst):** 11 priorities (P0-P3, ~20 PD effort).
- **Governance changes (Skeptický VP):** 3 non-negotiable (Decider profile, Steward FTE, compliance score + red team).
- **Academic changes (Akademik):** 8 methodological revisions, ~3-letá publication track.

**Bez duplikací unikátních doporučení: ~24 distinct action items** pro v0.3 Charter.