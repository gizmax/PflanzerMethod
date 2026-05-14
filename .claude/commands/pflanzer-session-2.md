---
description: Session 2 (decisional, ~3 h) — agreguje feedback by dept, navrhne resolution top 3 sporů, Decider's Go/Iterate/Kill call. Slice 7.
---

# /pflanzer-session-2 — Decisional session

Argumenty: `$ARGUMENTS` = projekt slug.

Předpoklady:
- `projects.status` IN ('session_1', 'session_2')
- `/pflanzer-feedback-pull <slug>` byl spuštěn (= summary + debt audit existují)

## Co tento command dělá

Aplikuje **canonical agendu Session 2** z `docs/methodology/06-session-2.md`
(3 h decisional, end 12:00, ne víc — energy curve):

1. **Pre-flow check** — feedback summary, debt audit, conflict matrix loaded.
2. **Aggregate by department** (mirror role label) — visualizace divergence.
3. **Top 3 conflicts** + suggested resolutions z `synthesis/01-conflict-matrix.md`.
4. **Commitment index** vs threshold z Charteru (default 0.6).
5. **Decider's call** přes `AskUserQuestion` → Go / Iterate / Kill.
6. **Iterate guard** — max 1× další session 1 (žádný infinite loop).
7. **Status update** → 'handoff' / 'session_2' / 'killed'.
8. **Eskalační protokol** per ADR-0001 pokud Decider neumí rozhodnout.

## Jak postupuj

### Krok 1 — Pre-Session 2 prep

```bash
python3 tool/cli/session_2.py prep --slug $ARGUMENTS
```

Výstup obsahuje: commitment_index, ready_for_decision flag, top 3 conflicts
s resolution návrhy, critical_flags count, next_action hint.

Ukaž týmu na velký TV jako **opening slide** Session 2.

### Krok 2 — Critical flags resolve (pokud nějaké)

Pokud `critical_flags > 0`:
- Pro každý critical: ukaž rationale + submitted_by, zeptej se Decider:

```
AskUserQuestion: "Critical: '{rationale}'. Co s tím?"
options:
  - "Resolved — popis fix" [text input]
  - "Defer to handoff (s mitigation deadline)"
  - "Block — varianta vyhozena ze shortlist"
  - "Reject critical (Decider override + rationale do decision logu)"
```

### Krok 3 — Top 3 conflicts review

Pro každý z `top_conflicts[:3]`:
- Ukaž `axis`, score per role, navrhované resolution.
- Pokud `resolution = null` → unmapped, **vyžaduje human review**:
  - Decider rozhodne ad-hoc, rationale povinný
  - Volitelně: navrhni přidat dvojici do `conflict_resolver.CONFLICT_RESOLUTIONS`.

### Krok 4 — Decider's call (sociální akt)

```
AskUserQuestion: "{Decider} — Go / Iterate / Kill?"
options:
  - "GO — handoff package, pilot/production"
  - "ITERATE — 1 další Session 1 round (max 1×)"
  - "KILL — projekt zastaven, retros volitelný"
```

```
AskUserQuestion: "Decider rationale (POVINNÉ pro DORA / AI Act čl. 14):" [text]
```

Pokud `iterate`:
```
AskUserQuestion: "Iterate focus (1-2 věty — co se mění oproti původní hypotéze):" [text]
```

### Krok 5 — Eskalační protokol (pokud potřeba)

Pokud Decider nemůže rozhodnout (read: tříhodinová debata bez resolution),
aplikuj **ADR-0001 (Decider escalation)**:
- Scenario A: Decider absent → backup_decider z Charteru.
- Scenario B: Decider conflicted → escalate na CPO (cpo_escalation_contact).
- Scenario C: Cross-functional gridlock → CPO + Decider joint sign-off.

Notify uživatele a zapiš `decision` row type='escalation' s rationale.

### Krok 6 — Persist

```bash
python3 tool/cli/session_2.py decide \
  --slug $ARGUMENTS \
  --decision <go|iterate|kill> \
  --rationale "<text z kroku 4>" \
  --iterate-focus "<jen pokud iterate>" \
  --decider "<jméno Decidera, pokud override>"
```

Výstup: `new_status`, `summary_path`, `next_step`.

### Krok 7 — Souhrn

- Tabulka top 3 conflicts × resolution.
- Decision + rationale (text pro decision log).
- Commitment index vs threshold.
- Path k `_session_2_summary.md`.
- Next step:
  - **Go** → `/pflanzer-handoff $ARGUMENTS`
  - **Iterate** → `/pflanzer-session-1 $ARGUMENTS` (single new variant) → znovu pull → znovu session 2
  - **Kill** → optional retro v `data/sessions/$ARGUMENTS/_kill-retro.md`

## Co NEDĚLAT

- **Nepřebíjet Decider** — AI navrhuje resolution, **ne** rozhoduje. Decider má final.
- **Nepřeskočit critical flags** — block Decider call dokud nejsou resolved nebo overridden.
- **Nedovolit > 1× iterate** — guard v `session_2.py`. Druhý iterate = re-Charter.
- **Nezapomenout audit_log** — každé rozhodnutí má atribuci na člověka
  (DORA 7-letá retence, AI Act čl. 14).

## Reference

- `docs/methodology/06-session-2.md` (canonical agenda)
- `docs/decisions/0001-decider-model.md` (eskalační protokol)
- `tool/cli/session_2.py` (prep + decide)
- `tool/cli/conflict_resolver.py` (top 3 sporů detection)
- `docs/research/synthesis/01-conflict-matrix.md` (suggested resolutions)
