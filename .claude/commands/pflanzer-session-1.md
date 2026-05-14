---
description: Spustí Session 1 orchestrator — facilitátor + role expert sub-agents → 1-3 varianty + preference matrix per role. Slice 5.
---

# /pflanzer-session-1 — Session 1 (generativní)

Argumenty: `$ARGUMENTS` = projekt slug.

Předpoklady (povinné):
- `projects.status = 'triage'` (proběhl `/pflanzer-triage`)
- ≥ 1 row v `roles` (proběhl `/pflanzer-roles`)
- Všechny 4 triage tracks mají status `ok` nebo `deferred`

## Co tento command dělá

Aplikuje **canonical agendu Session 1** z `docs/methodology/04-session-1.md`:

1. **Builder decision** — `tool/cli/builder_decision.py` doporučí 1-3 builders.
2. **Variant manifest** — facilitator agent navrhne 1-3 varianty (different
   builders, different aesthetic biases).
3. **Vibe-coding** — uživatel je vyzván k manuálnímu spuštění builderu
   (v0 / Bolt / Cursor / …) a vložení reálných prototype URLs.
4. **Preference matrix** — paralelní expert sub-agents (per role v DB)
   ohodnotí každou variantu na 4 dimenzích.
5. **Decider's call** — `AskUserQuestion` na shortlist 1-3 variant + rationale +
   veto registr + parking lot.
6. **Persist** — `tool/cli/session.py` zapíše DB (sessions, variants,
   role_preferences, decisions row), AI-only deflation aplikuje agregát,
   posune `projects.status = 'session_1'`.
7. **Web hub push** — POST variants do FastAPI hub pro mezi-session feedback.

## Jak postupuj

### Krok 1 — Validace

```python
import sqlite3
from pathlib import Path
db = sqlite3.connect("data/pflanzer.db")
db.row_factory = sqlite3.Row
proj = db.execute("SELECT id, status, name, throwaway_or_evolve FROM projects WHERE slug = ?", ("$ARGUMENTS",)).fetchone()
roles = db.execute("SELECT catalog_idx, catalog_label, status, ai_proxy_mode, human_owner FROM roles WHERE project_id = ?", (proj["id"],)).fetchall()
triage = db.execute("SELECT track, status FROM triage WHERE project_id = ?", (proj["id"],)).fetchall()
```

Pokud cokoli chybí → instruuj uživatele co spustit:
- chybí projekt → `/pflanzer-charter`
- status≠'triage' → `/pflanzer-triage $ARGUMENTS`
- žádné role → `/pflanzer-roles $ARGUMENTS`

### Krok 2 — Builder shortlist

```bash
python3 tool/cli/builder_decision.py --slug $ARGUMENTS
```

Zobraz uživateli ranked shortlist + diversity hint. **Volitelně** se zeptej
přes `AskUserQuestion`, jestli chce override (např. „máme licenci jen na Cursor").

### Krok 3 — Spusť facilitátora + role experts

Spusť **facilitator** agent (orchestrator), který si paralelně zavolá
role-experts ve vlnách po 3-4 (ne všechny najednou — context budget).

```
Agent(subagent_type="facilitator", prompt="""
Run Session 1 facilitator for slug=$ARGUMENTS.
- Read data/charters/$ARGUMENTS.md, data/triage/$ARGUMENTS/_summary.md.
- Use builder shortlist from `tool/cli/builder_decision.py --slug $ARGUMENTS`.
- For each role row in DB (catalog_idx, expert_agent slug), spawn the
  matching <expert>-expert sub-agent in waves of 3-4 (parallel within wave,
  sequential between waves).
- Aggregate role preferences into the spec format.
- Return ONLY the JSON spec (no commentary).
""")
```

### Krok 4 — Real prototype URLs

Facilitator vrací varianty s `prototype_url = sandbox.invalid/...` placeholders.
Vyzvi uživatele přes `AskUserQuestion` per variant:

> **Variant A** (`v0`) — popis: `<description>`
> Spusť builder, naclickej prototyp, vlož preview URL:
> [Other → vlož URL]

Update spec JSON in-memory (nahraď placeholder URL skutečnou).

### Krok 5 — Decider's call (interactively)

```
AskUserQuestion: "Které varianty jdou do mezi-session prototype hubu?"
options: ["A", "B", "C", "A+B", "A+C", "B+C", "A+B+C"]
```

```
AskUserQuestion: "Decider's rationale (1-2 věty, povinné pro decision log):"
```

Pokud Security/A11y/Legal vrátili veto flag → uveď do summary + zeptej se,
jestli Decider override (musí mít rationale do decision logu).

Doplň `decider_call.shortlist`, `rationale`, `veto_register`, `parking_lot`
do spec JSON.

### Krok 6 — Persist

Zapiš JSON do `/tmp/<slug>-session-1-spec.json` a spusť:

```bash
python3 tool/cli/session.py --spec /tmp/$ARGUMENTS-session-1-spec.json
```

Ověř, že stdout obsahuje `summary_path` a žádný error.

### Krok 7 — Web hub push (best-effort)

Pro každou variantu z DB:

```bash
curl -X POST http://localhost:8000/api/projects/$ARGUMENTS/variants \
  -H "Content-Type: application/json" \
  -d '{"name":"A","builder":"v0","prototype_url":"...","description_md":"..."}'
```

Pokud web hub neběží — neselhej, jen logni warning a doporuč
`docker compose up -d` v `tool/web/`.

### Krok 8 — Souhrn pro uživatele

- Tabulka variant × score × shortlist flag.
- Veto registr (pokud nějaký).
- Path k `data/sessions/<slug>/_summary.md`.
- Next: `/pflanzer-feedback-pull <slug>` (Slice 6) za 5-7 pracovních dní.

## Co NEDĚLAT

- **Neagreguj score sám** — to dělá `tool/cli/session.py` (deterministic,
  auditable, AI-only deflation).
- **Negeneruj > 3 varianty** — Decider's tax (synthesis 02).
- **Nepřeskoč Decider's call** — commitment je sociální akt
  (`04-session-1.md`); pokud chybí, decision row se nezapíše a status
  zůstane `triage`.
- **Nepřepiš veto** — Security/Legal/A11y veto bez explicit Decider override
  rationale = session se odkládá.
- **Nepust > 4 expert agents paralelně** — context window. Vlny po 3-4.
- **Nezakázej manual builder** — pokud žádný approved builder není OK
  (L4 data, unapproved tooling), `manual` je legitimní fallback.

## Reference

- `docs/methodology/04-session-1.md` (canonical agenda)
- `docs/methodology/02-role-catalog.md` (decision tree pro výběr expert agents)
- `docs/decisions/0008-tool-form-factor.md` (Hybrid: CLI + web hub mirror)
- `tool/cli/session.py` (persistence + aggregate score logic)
- `tool/cli/builder_decision.py` (builder shortlist heuristic)
- `.claude/agents/facilitator.md` (orchestrator)
- `.claude/agents/<role>-expert.md` × 17 (role-specific lens)
