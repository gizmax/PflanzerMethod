---
description: Live in-room session pro tým — společný vibe-coding od problému k handoff za 60-90 min, bez koleček iterací mezi sessions.
---

# /pflanzer — In-room session (single entry point)

**Argumenty (volitelné)**: `$ARGUMENTS` = problem statement (1 věta).
Pokud chybí, zeptáš se v kroku 1.

## Pro koho

Tým 4-6 lidí v zasedačce, jeden notebook připojený k velkému TV.
Cíl: do 60-90 min mít **shortlist + akční handoff** (kdo / co / do kdy),
bez čekání na pre-sessions a 4 separátních wizardů.

Pod kapotou tento command volá Charter + Roles + Triage (deferred) +
Builder Decision + Session 1 persistenci. Sofistikovanost zachována,
UX zjednodušeno.

## Workflow (5 kroků = 5 AskUserQuestion bloků + 1 generativní)

### KROK 1 — HOOK (co dnes řešíte)

Pokud `$ARGUMENTS` chybí, zeptej se přes `AskUserQuestion`:

> **Co konkrétně chcete dnes vyřešit?** (1-2 věty, akční formulace)

Zachovej odpověď jako `hook` (ne validovat moc — krátké je fajn).

### KROK 2 — DECIDER + ROOM (kdo má hlas)

Zeptej se 2 otázkami v jedné AskUserQuestion zprávě (paralelně):

**A) Kdo má dnes finální slovo (Decider)?** [text input]
- Default: nejstarší v místnosti / line manager / sponsor.

**B) Kdo z těchto rolí je v místnosti?** [multiSelect, default: PM, FE, UX]
- Zadavatel / Business owner (#1) — vždy zahrnuto
- PM (#2) — vždy zahrnuto
- Facilitátor (#3) — vždy zahrnuto (může to být ty / Claude)
- Frontend (#4) ✅ default
- Backend (#5)
- UX / Designer (#6) ✅ default
- Security (#7) — pokud osobní data / auth
- QA (#8) — pokud "produkce / pilot"
- Engineering manager (#9)
- Legal / GDPR (#10)
- Accessibility (#11)
- Data / Analytics (#12)
- Customer support (#13)
- User research (#14)
- DevOps (#15)
- UX writer (#16)

Volitelně (jen pokud je tým > 6 lidí, jinak skipni): **Kdo zastává jakou roli?**
(text per role, jméno).

### KROK 3 — RISK PROFILE (rozsah dopadu)

```
AskUserQuestion: "Co je dnešní cíl tohoto prototypu?"
options:
  - "Throwaway proto" — interní demo, žádná produkce, žádná real data
  - "Pilot s 5-20 reálnými uživateli" — limited AI Act, L2 data
  - "Production launch" — limited AI Act, L3 data, regulated profile
```

→ mapuje se na `RISK_PROFILES` v `tool/cli/quick_session.py`.

**Bootstrap call** (po krocích 1-3):

Vyrob JSON spec do `/tmp/quick-bootstrap-<slug>.json`:

```json
{
  "hook": "<z kroku 1>",
  "decider_name": "<z kroku 2A>",
  "room_role_idx": [1, 2, 3, 4, 6],
  "risk_profile": "throwaway|pilot|production",
  "role_owners": {"1": "Honza", "2": "Petra", ...}
}
```

Spusť:

```bash
python3 tool/cli/quick_session.py bootstrap --spec /tmp/quick-bootstrap-<slug>.json
```

→ vrátí `slug`, `project_id`, `defer_note`. Slug ukaž týmu (link
do web hubu: `http://localhost:8000/<slug>`).

### KROK 4 — BUILDER PROMPTS (paralelní vibe-coding)

```bash
python3 tool/cli/quick_session.py prompts --slug <slug> --hook "<hook>" --n 3
```

→ JSON s 2-3 prompts. **Vyhoď je týmu na velký TV** v tomto formátu:

```
🎨 Variant A (v0) — happy-path minimum
   Otevři: https://v0.app
   Prompt: ```
   <prompt_text>
   ```
   → po buildu vlož preview URL: [_____]

🎨 Variant B (bolt) — guided multi-step
   Otevři: https://bolt.new
   Prompt: ```...```
   → preview URL: [_____]

🎨 Variant C (cursor) — smart defaults
   Pair-program v repu / Cursor (pokud máš)
   Prompt: ```...```
   → preview URL: [_____]
```

Tým si **rozdělí 3 variants po dvojicích**, paralelně buildují **15-30 min**.
Facilitátor (ty) hlídá čas — 30 min cap, pak voting bez ohledu na hotovost.

Po skončení zeptej se přes `AskUserQuestion` per variant:

> **Variant A — vlož preview URL** [text]
> *(pokud nehotové, vlož `none` — varianta vyhnání z votingu)*

### KROK 5 — VOTING (silent dot voting)

Pro každého člena u stolu (jméno z kroku 2B/owners) projdi tento mini-loop:

```
For role v selected_roles:
  pro každou variantu (A, B, C):
    AskUserQuestion: "{role_label} ({owner}) — Variant {X}"
    options:
      - "Líbí se mi" (user_value=0.8, strategic_fit=0.7)
      - "Spíš ne" (user_value=0.4, strategic_fit=0.5)
      - "Veto / blocker" (risk=0.9, rationale povinný)
      - "Pass" (skip)
    + zeptej se 1× na rationale (povinný 1 věta).
    + zeptej se 1× na commitment level 0-3 PER PERSONA (ne per varianta).
```

> ⚠ **Speed mode**: pokud je týmu > 4, použij Liberating Structures **1-2-4-All**:
> 1 min sami, 2 min ve dvojici, 4 min v čtveřici, pak All. Hlasy SILENT,
> Decider hlasuje **poslední** (per `04-session-1.md` § HiPPO push).

Sestav `votes` array per variant:

```json
[
  {
    "name": "A", "builder": "v0", "description": "happy-path minimum",
    "role_preferences": [
      {"role_idx": 1, "user_value": 0.8, "effort": 0.3, "risk": 0.2,
       "strategic_fit": 0.85, "commitment_level": 3,
       "rationale": "matches XYZ", "is_ai_only": false},
      ...
    ]
  }
]
```

### KROK 6 — DECIDER'S CALL (sociální akt)

```
AskUserQuestion: "{Decider} — která varianta jde do mezi-session prototype hubu?"
options: ["A", "B", "C", "A+B", "A+C", "B+C", "A+B+C", "Žádná → re-frame problému"]
```

```
AskUserQuestion: "Decider rationale (1-2 věty, do decision logu):" [text]
```

Pokud někdo dal "Veto / blocker" v kroku 5 → uveď do `veto_register` array
+ spec`AskUserQuestion: "Decider — override veto?"` (pokud ano, rationale
povinný do decision logu).

Vyrob spec a persistuj:

```json
{
  "slug": "<slug>",
  "facilitator": "<your name z kroku 2A or 2B owners>",
  "decider_call": {
    "shortlist": ["A", "B"],
    "rationale": "<z předchozího>",
    "veto_register": [...],
    "parking_lot": []
  },
  "votes": [...]
}
```

```bash
python3 tool/cli/quick_session.py vote --spec /tmp/quick-vote-<slug>.json
```

### KROK 7 — HANDOFF (1-page MD)

```bash
python3 tool/cli/quick_session.py handoff --slug <slug>
```

→ zapíše `data/quick/<slug>-handoff.md`. **Vyhoď týmu na TV** v plném textu
(je 1 stránka, vejde se).

Klíčové sekce:
- Co děláme (XYZ)
- Decider + decision rationale
- Varianty + scores
- **Kdo / Owner / Commitment 0-3 / Rationale** (table)
- Kill criteria
- ⚠ Pre-production TODO (triage deferred — re-run před pilotem)
- Co dál (5 akčních bodů)

## Co tento command NEDĚLÁ

- **Negeneruje moc otázek** — 5-6 AskUserQuestion bloků MAX. Pokud potřebuješ
  všechny pole z plného Charter wizardu, použij `/pflanzer-charter`.
- **Nespouští reálnou triage** — všechny 4 tracky deferred (in-room mode
  nemá 48h pre-read). Pre-pilot/production MUSÍ tým pustit `/pflanzer-triage`.
- **Nespouští 17 expert sub-agentů** — voting je manuální od lidí v místnosti
  (commitment je sociální akt). AI běží jen na builder prompts + agregaci.
- **Nepushuje varianty do web hubu** — to je krok 7 (handoff). Web hub je
  pro async mezi-session feedback (Slice 6).

## Anti-patterns (block immediately)

- **HiPPO override silent vote bez rationale** → block. Decider override
  vyžaduje veřejný rationale do decision logu.
- **Žádná negative variant** (A+B+C all positive) → flagni "groupthink risk",
  navrhni Pre-mortem TRIZ ("za 6 měsíců to selhalo, proč?").
- **Decider zvolí > 3 varianty** → Decider's tax (synthesis 02). Force
  re-pick s max 3.
- **Žádné L3+ data v promptech** — pokud Charter má `data_class=L3`, prompt
  generator už zahrnul varování; opakuj ho ústně před vibe-codingem.

## Reference

- `tool/cli/quick_session.py` (single-entry orchestrator)
- `docs/methodology/04-session-1.md` (canonical Session 1 — co tento command zkracuje)
- `docs/decisions/0008-tool-form-factor.md` § Hybrid (CC + web hub)
- Plný flow (4 sessions): `/pflanzer-charter` → `/pflanzer-roles` →
  `/pflanzer-triage` → `/pflanzer-session-1` → mezi-session → `/pflanzer-session-2`
- Quick flow (1 session): `/pflanzer` → handoff → (optional) plný flow později.
