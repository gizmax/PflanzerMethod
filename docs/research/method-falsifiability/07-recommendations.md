# Method Falsifiability — Recommendations & Priorities

> Konkrétní action items pro v0.3 Method Charter update. Priority P0-P3, owner,
> effort estimate, ADR mapping.

## Priority P0 (PR-blocking pro v0.3) — Charter structural changes

| # | Action | Where | Effort | New ADR |
|---|--------|-------|--------|---------|
| P0-1 | **Practitioner/Academic track split** — Charter explicit označí which claims jsou business-decision vs publication-grade. Practitioner timeline T+18 mo, academic 3-5y opt-in side track. | `method-charter.md` § Status + new § „Scope of validity claims" | 2 h | (existing ADR-0007 addendum) |
| P0-2 | **Time-bounded kill criteria + Default Sunset** — N=8 informational, **N=12 decision-grade NEBO T+18 mo default Sunset (whichever first)**. Steward early-kill veto explicit. | `method-charter.md` § Kill criteria | 1 h | ADR-0011 (Method Decider profile + Sunset default) |
| P0-3 | **Method Decider redefined** — VP Eng Effectiveness (2 levels under CTO), tenure 4-7y, JD includes sunset authority. NE CPO. | `method-charter.md` § Status + ADR-0007 addendum | 1 h | ADR-0011 |
| P0-4 | **Method Steward FTE redefined** — 0.5-0.7 FTE dedikovaný Senior PdM, €100-150k OPEX, Engineering Excellence CoE. NE „EM ve volném čase". | `method-charter.md` § Status + new § „Method Steward operational scope" | 2 h | ADR-0012 |
| P0-5 | **Pre-registration discipline** — fit criteria + statistical test signed pre-pilot, Charter version pinned. | `method-charter.md` new § „Pre-registration protocol" | 2 h | ADR-0013 |
| P0-6 | **Compliance Score** — 12 must-have prvků per pilot, ex-post Steward audit. Score < 10/12 = pilot disqualified z method-level metrics. | `method-charter.md` new § „Pflanzer Compliance Score" | 3 h | ADR-0013 (joint) |
| P0-7 | **Causal model (Theory of Why)** explicit v Charteru — 5 interventions → 5 mediátorů → 4 outcomes + moderators. | `method-charter.md` new § „Causal model" | 2 h | (Akademik kauzální diagram, ADR-0007 addendum) |
| P0-8 | **Success threshold tabulka rozšířena o instrumentation** — sloupce „Definice (start → end)", „Data source", „Cadence". | `method-charter.md` § Success threshold (rewrite) | 1 h | — |

**P0 total effort:** ~14 hodin Charter rewrite + 4 nové ADR drafty.

## Priority P1 (v0.3 SHOULD, ne PR-blocking) — Measurement infrastructure

| # | Action | Where | Effort | New ADR |
|---|--------|-------|--------|---------|
| P1-1 | ✅ **DONE (2026-05-17)** — Composite PflanzerIndex formula + edge cases v **ADR-0014** + reference v `method-charter.md` § Success threshold. | ADR-0014, method-charter | done | ADR-0014 |
| P1-2 | **Blind external EM acceptance panel** — 3 EMs z jiných BU, average Likert + numerical, ~12 h/pilot. | new file `docs/methodology/acceptance-review-protocol.md` | 8 h | ADR-0014 (joint) |
| P1-3 | **Baseline collection playbook** — full population mining (Jira/Azure), survival analysis (censored), propensity matching design. | new file `docs/methodology/baseline-collection-playbook.md` | 16 h (~2 days) | — |
| P1-4 | **Per-pilot instrumentation spec** — 7-row artefakt tabulka, form templates (T+30 acceptance survey, T+90 NPS form). | new file `docs/methodology/per-pilot-instrumentation.md` | 8 h | — |
| P1-5 | **Project Class Taxonomy A/B/C/D** s explicit definicemi, baseline collected per class. | new section v `01-filozofie-a-kdy-pouzit.md` nebo new file | 4 h | — |
| P1-6 | ✅ **DONE (2026-05-17)** — Leading indicators dashboard (LI-1 až LI-5) + threshold + veto trigger workflow v `docs/methodology/leading-indicators.md`. Reference z method-charter.md § Validační loop. | `docs/methodology/leading-indicators.md` | done | — |
| P1-7 | **Method Dashboard template** — Confluence / Notion table spec (10 polí), query examples. | new file `docs/methodology/method-dashboard-template.md` | 3 h | — |
| P1-8 | **Re-work shadow ledger** — Jira labels schema, audited quarterly. | included v P1-4 (instrumentation spec) | — | — |

**P1 total effort:** ~49 hodin = 6-7 person-days. Out-of-scope pro tento PR; track jako follow-up.

## Priority P2 (v0.3+ NICE) — Governance & external validity

| # | Action | Where | Effort |
|---|--------|-------|--------|
| P2-1 | **External red team / peer consortium model** v T+12 review. | new section + sample legal MOU | 8 h + legal review |
| P2-2 | **Bootstrap budget €40k spec** — 3 měsíce pre-pilot Steward + 2× konzultantský workshop + Jira data extraction tooling. | `method-charter.md` § new „Bootstrap" | 2 h |
| P2-3 | **Method post-mortem disclosure commitment** — sunset data zveřejněna po N dní bez ohledu na výsledek. | ADR-0010 | 4 h |
| P2-4 | **Synthetic control / DiD design** pro N=12+ pilots. | research design doc | 16 h (1 statistician PD ekvivalent) |
| P2-5 | **Fork governance ADR** — variant fork povolen jen s Method Decider sign-off + dedicated ADR + vlastní XYZ. | ADR-0015 | 3 h |
| P2-6 | **Self-sustaining BU definice** — operational kritéria (a Champion-trained kandidát, b 2+ piloty bez Steward, c quality threshold). | `method-charter.md` § Kill criteria | 1 h |

## Priority P3 (post-v0.3) — Academic track

| # | Action | Effort |
|---|--------|--------|
| P3-1 | **Instrument validation pilot** — think-aloud test, Cronbach α, Cohen's κ reliability. | 5 PD |
| P3-2 | **3-letá publication research roadmap** dle Akademika — Year 1 instrument, Year 2 multi-case, Year 3 multi-org. | ongoing |
| P3-3 | **IRB / ethics review** pokud academic partner. | 8 h |
| P3-4 | **Pre-registration on OSF** per pilot. | 1 h/pilot |
| P3-5 | **Replication package** (handbook + instruments) post N=6. | 5 PD |

## Recommended PR scope (v0.3 first delivery)

**In scope for this PR (research/method-falsifiability branch):**
- All P0 items (Charter rewrite + 4 ADR drafty: 0011, 0012, 0013, 0014).
- Update `05-devils-advocate-resolution.md` — Útok 12 → FULL FIX v0.3.
- New synthesis files: `05-conflict-matrix.md`, `06-key-themes.md`, `07-recommendations.md` (done).
- Per-perspective files (01-04, done).

**Out of scope for this PR (P1-P3 follow-ups):**
- P1 measurement infrastructure (separate PR per file).
- P2 governance ADRs.
- P3 academic track.

**Rationale:** P0 changes redefinují Charter foundations — bez nich jsou P1-P3
implementations postavené na nestabilním základě. P0 musí jít první.

## Risk: co se stane pokud P0 nedoručíme

- **Method Steward role** zůstává „EM ve volném čase" → budget vapor → role
  neobsazena → Method Charter v0.3 bez vlastníka.
- **Pre-registration discipline** chybí → garden of forking paths → každý pilot
  data jsou retrospektivně racionalizovatelná.
- **Kill criteria** zůstávají N-only → metoda zombifikuje (Spotify pattern).
- **Method Decider = CPO** → sunk-cost trap → metoda nezhasne ani po skutečném
  selhání.

Tj. bez P0 je v0.3 stejně non-functional jako v0.2.1, jen s víc dokumentací.

## Co P0 doručit nemůže (akceptované limitations)

- **N=12 minimum statistical power claim** vyžaduje 18+ měsíců real-world pilots.
  P0 to nezrychlí; pouze nastaví thresholdy korektně.
- **External red team consortium** vyžaduje peer org buy-in. P0 jen nadefinuje
  protokol; reálné MOU = P2.
- **Academic publication** = 3-5 let. P3 explicit out-of-scope.

Tyto limitations jsou v Charteru v0.3 explicitně formulované — *„audit dotaz
po 2 letech zní X, po 5 letech Y; nepředstírame, že jsou stejné."*