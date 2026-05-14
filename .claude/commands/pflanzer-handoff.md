---
description: Generate per-role handoff package (8 souborů) + method-metrics aggregate. Slice 8.
---

# /pflanzer-handoff — Handoff package generator

Argumenty: `$ARGUMENTS` = projekt slug.

Předpoklad: `projects.status = 'handoff'` (= Session 2 Decider's Go).

## Co tento command dělá

Per `docs/methodology/07-handoff-do-vyvoje.md` § Per-role handoff:

1. Pull all project context (Charter, roles, triage, sessions, variants, decisions, feedback).
2. Render 8 per-role artefaktů do `data/handoffs/<slug>/`:
   - `decision.md` — Charter snapshot + decision log + ADR drafty
   - `be.md` — OpenAPI 3.1 stub, ERD, breaking-change registr, contract test skeleton
   - `fe.md` — throw-away/evolve directive, component manifest delta, design tokens diff
   - `qa.md` — Gherkin scénáře (1 happy + ≥ 1 negative per varianta), P2P checklist (9 položek)
   - `platform.md` — Sandbox spec, paved-road, SLO baseline, promote-to-prod gate
   - `data.md` — measurement plan, event taxonomy delta, A/B test design, learning agenda
   - `support.md` — ticket prediction worksheet, support docs deadline (D-7/D-2/D+30)
   - `compliance.md` — audit trail dump, RoPA update, AI Act register, DPA flag list
3. Update `data/method-metrics.json` (time-to-handoff aggregate napříč projekty).
4. Audit log entry.

## Jak postupuj

### Krok 1 — Validace

Read project status z DB. Pokud ≠ 'handoff', instruuj uživatele spustit
`/pflanzer-session-2 $ARGUMENTS` nejdřív (Decider Go nutný).

### Krok 2 — Generate

```bash
python3 tool/cli/handoff.py --slug $ARGUMENTS
```

Stdout vrátí JSON s `out_dir`, `files[]`, `metrics`, `p2p_gate_checklist`.

### Krok 3 — Per-role assignment

Z `roles` table lookup human_owner per role. Pošli každému ownerovi jeho
package (souborový link nebo email; v0 jen log path):

| Role | Owner | Handoff file |
|------|-------|--------------|
| BE lead (#5) | <owner> | `data/handoffs/<slug>/be.md` |
| FE lead (#4) | <owner> | `data/handoffs/<slug>/fe.md` |
| QA (#8) | <owner> | `data/handoffs/<slug>/qa.md` |
| DevOps (#15) | <owner> | `data/handoffs/<slug>/platform.md` |
| Data (#12) | <owner> | `data/handoffs/<slug>/data.md` |
| CS proxy (#13) | <owner> | `data/handoffs/<slug>/support.md` |
| Security (#7) + Legal (#10) | <owner> | `data/handoffs/<slug>/compliance.md` |
| Decider (#1) | <owner> | `data/handoffs/<slug>/decision.md` |

### Krok 4 — Promote-to-prod gate readout

Přečti `qa.md` § P2P checklist (9 položek) + `platform.md` § Promote-to-prod
gate (7 položek). Sečti totální gate items, ukaž kolik je hotových (manuálně
checkuje QA + DevOps post-implementation).

### Krok 5 — Souhrn

- Path k `data/handoffs/<slug>/` (8 souborů).
- Method-metrics: time-to-handoff_days pro tento projekt.
- Aggregate metrics napříč projekty (avg / min / max time-to-handoff).
- Reminder: po deployi spusť reinforcement track per Charter (T+7 / T+30 / T+60 / T+90).

## Co NEDĚLAT

- **Negeneruj package pokud status ≠ 'handoff'** — vyžaduje Decider's Go.
- **Nepřebíjet template defaults** — TODO placeholders jsou záměr; tým je
  doplní per project context (BE openapi, FE component delta, atd.).
- **Nezapisovat real PII do souborů** — Charter / triage / decisions
  obsahují jen byly napsané týmem; pokud tým psal PII, fix v Charteru.
- **Nezapomenout method-metrics** — důležité pro reinforcement track
  (devil's advocate Útok 11): bez metrik tým nezjistí, jestli metoda
  funguje napříč pilotmi.

## Reference

- `docs/methodology/07-handoff-do-vyvoje.md` (canonical handoff specifikace)
- `tool/cli/handoff.py` (8 renderers + method-metrics)
- `data/method-metrics.json` (cross-project aggregate)
