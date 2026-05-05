---
description: Spustí 4 paralelní pre-flight triage sub-agents (Discovery + Security + Legal + Platform) a aggregeguje gate decision. Slice 3.
---

# /pflanzer-triage — Pre-flight Triage (Slice 3)

Argumenty: `$ARGUMENTS` = projekt slug. Předpokládá `projects.status='charter'`
(= proběhl `/pflanzer-charter`) a alespoň 1 row v `roles` (= proběhl
`/pflanzer-roles`).

## Co tento command dělá

Aplikuje **Krok 0 + 0a** z `docs/methodology/03-pre-session-priprava.md`:
1. **Krok 0** — Discovery Readiness Gate (sub-agent `discovery-readiness`).
2. **Krok 0a** — 3 paralelní triage tracks (Security / Legal / Platform).

Pokud kterýkoliv track = `blocked` → Session 1 nestartuje, vrátí důvod.
Pokud všechny `ok` nebo `deferred` → status projektu posune na `triage`.

## Jak postupuj

1. **Validuj**: slug + projekt existuje + status='charter' + roles count > 0.
   Pokud chybí, instruuj uživatele co spustit nejdřív.

2. **Spusť 4 paralelní sub-agents** v JEDNÉ zprávě s 4 Agent tool calls:

```
Agent(subagent_type="discovery-readiness", prompt="Run Discovery Readiness Gate for slug=$ARGUMENTS. Read data/charters/$ARGUMENTS.md. Return JSON per agent definition.")
Agent(subagent_type="security-triage", prompt="Run Security & Data Triage for slug=$ARGUMENTS. Return JSON.")
Agent(subagent_type="legal-triage", prompt="Run Legal & Privacy Triage for slug=$ARGUMENTS. Return JSON.")
Agent(subagent_type="platform-triage", prompt="Run Platform Triage for slug=$ARGUMENTS. Return JSON.")
```

   Každý sub-agent vrátí JSON s polem `track`, `status`, `artefact_md`,
   `signed_by`, `rationale` + track-specific fields.

3. **Sestav JSON spec** s 4 výsledky a předej do `tool/cli/triage.py`:

```bash
python3 tool/cli/triage.py --spec /tmp/<slug>-triage-spec.json
```

JSON spec format:
```json
{
  "slug": "demo-widget",
  "results": [
    {"track": "discovery", "status": "ok", "artefact_md": "...", "signed_by": "...", "rationale": "..."},
    {"track": "security", "status": "ok", "data_class": "L2", "ai_act_tier": "minimal", ...},
    {"track": "legal", "status": "ok", "ai_act_tier": "minimal", "dpia_required": false, ...},
    {"track": "platform", "status": "ok", "sandbox_url": "...", ...}
  ]
}
```

4. **Verifikuj output**:
   - Read `data/triage/<slug>/_summary.md`.
   - Pokud overall='blocked', shrň důvody uživateli a navrhni nápravu.
   - Pokud overall='ok', připomeň pre-flight checklist
     (`docs/methodology/03-pre-session-priprava.md` § Pre-flight checklist).

5. **Sjednoť AI Act tier + Data class** s Charterem:
   - Security a Legal triage vrátí AI Act tier — pokud se liší od Charteru,
     update projects.ai_act_tier (Legal má precedence).
   - Security vrátí data_class — pokud se liší od Charteru (z slice 1),
     update projects.data_class (Security má precedence).

6. **Souhrn pro uživatele**:
   - Tabulka 4 tracks × status.
   - Blockers + warnings.
   - Next krok: `/pflanzer-session-1 <slug>` (jen pokud ok).

## Co NEDĚLAT

- Nepřeskakuj žádný ze 4 tracks — všechny POVINNÉ.
- Pokud Discovery debt skóre ≥ 7 → návrh 2-week Discovery Sprint, neforce
  pokračování.
- Pokud Legal DPIA ≥ 2 triggery → block, ne deferred.
- Pokud Security data_class = L4 → block (session se nekoná).

## Reference

- `docs/decisions/0002-pre-flight-triage-tracks.md`
- `docs/methodology/03-pre-session-priprava.md` § Krok 0 + Krok 0a
- `.claude/agents/{discovery-readiness,security-triage,legal-triage,platform-triage}.md`
