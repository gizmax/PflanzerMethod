---
description: Stáhne mezi-session feedback z web hubu, agreguje per dept/severity/varianta, spustí discovery-debt-detector audit. Slice 6.
---

# /pflanzer-feedback-pull — Mezi-session feedback intake

Argumenty: `$ARGUMENTS` = projekt slug.

Předpoklad: web hub byl spuštěn (`tool/web/`) a tým posbíral feedback přes
ScoringForm (`/<slug>/feedback/<variant_id>`) v mezi-session okně (Quick 3 / Lean 3–5 / Full 5–7 pracovních dní, ADR-0021).

## Co tento command dělá

1. Spustí `tool/cli/feedback_pull.py --slug $ARGUMENTS` → aggregate + summary MD.
2. Pokud feedback_count > 0, spustí `discovery-debt-detector` agent na summary.
3. Pokud Critical flags > 0 nebo debt verdict in (critical|high), notifikuje
   Decider přes `AskUserQuestion` (eskalační protokol per ADR-0001).
4. Vrátí summary + next step (Session 2 nebo Discovery Sprint).

## Jak postupuj

### Krok 1 — Pull + aggregate

```bash
python3 tool/cli/feedback_pull.py --slug $ARGUMENTS
```

Stdout vrátí JSON s `summary_path`, `feedback_count`, `critical_flags`,
`ai_only_ratio`. Read & ukaž týmu.

Pokud `feedback_count == 0`:
- Pravděpodobně tým ještě nesbírá. Připomeň URL web hubu
  (`http://localhost:8000/$ARGUMENTS/compare`).
- Stop tady, nepouštěj debt detector na prázdná data.

### Krok 2 — Discovery debt audit

Spusť sub-agent (read-only audit, neměl by nic zapisovat do DB):

```
Agent(subagent_type="discovery-debt-detector", prompt="""
Audit feedback summary pro slug=$ARGUMENTS.
- Read data/feedback/$ARGUMENTS-summary.md (just generated).
- Read data/charters/$ARGUMENTS.md.
- Read data/sessions/$ARGUMENTS/_summary.md (pro OST node mapping).
- Apply 5-dimension framework (assumption ratio / user contact / OST coverage
  / AI-only sanity / persona freshness). Score 0-2 each, total 0-10.
- Return ONLY JSON per agent definition.
""")
```

Persistuj JSON output do `data/feedback/$ARGUMENTS-debt.json`.

### Krok 3 — Eskalace (pokud potřeba)

```python
verdict = debt_json["verdict"]  # critical|high|manageable|healthy
if verdict in ("critical", "high") or critical_flags > 0:
    # Notifikuj Decider. Eskalační protokol per ADR-0001.
```

```
AskUserQuestion: "Discovery debt verdict = {verdict}, critical flags = {N}.
Co teď?"
options:
  - "Pokračovat do Session 2 přes všechno (Decider override + rationale)"
  - "Stop — vyřešit blockers, re-pull za 2-3 dny"
  - "Discovery Sprint (2 týdny) — Session 2 odložena"
```

Pokud Decider override → zapiš jako `decision` row type='escalation' s rationale.

### Krok 4 — Souhrn + next step

Print týmu:
- Tabulka debt scores (5 dimenzí + total).
- Critical flags (pokud nějaké) s kdo to flagnul + rationale.
- Path k summary + debt.json.
- Next: `/pflanzer-session-2 $ARGUMENTS` (pokud verdict ≥ manageable + 0 unresolved
  criticals).

## Co NEDĚLAT

- **Nezakrývat critical flags** — eskaluj k Decider, neagreguj je do score.
- **Nepřebíjet debt detector** — audit je read-only insight, neoznačuj automaticky
  feedback jako neplatný.
- **Nepouštět audit s feedback_count = 0** — vrátí healthy false positive.
- **Nezapisovat debt.json do hlavní DB** — je to ephemeral audit artefakt
  (per session). Hlavní zápis je summary.md + audit_log row z feedback_pull.py.

## Reference

- `docs/methodology/05-mezi-sessions.md` (mezi-session ritual)
- `tool/cli/feedback_pull.py` (aggregate logic + summary MD)
- `.claude/agents/discovery-debt-detector.md` (5-dim audit framework)
- `docs/decisions/0001-decider-model.md` (eskalační protokol)
