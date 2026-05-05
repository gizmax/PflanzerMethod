---
description: Vede tým interaktivním wizardem, vyplní Pflanzer Business Charter (ADR-0004) a persistne projekt do DB.
---

# /pflanzer-charter — Charter wizard (Slice 1)

Argumenty: `$ARGUMENTS` = projekt slug (kebab-case, např. `demo-widget`).
Pokud nezadáno, ptej se uživatele přes AskUserQuestion.

## Co tento command dělá

Vyplníš s uživatelem **Pflanzer Business Charter** podle ADR-0004 a persistneš
projektový záznam do `data/pflanzer.db` + Charter markdown do
`data/charters/<slug>.md`.

## Jak postupuj

1. **Pokud uživatel nezadal slug v `$ARGUMENTS`**, použij AskUserQuestion:
   `Question: Jaký je slug projektu? (kebab-case, např. demo-widget, 'investbot-forecast')`

2. **Zkontroluj DB** — pokud projekt s tímto slugem už existuje, zeptej se
   uživatele:
   - **Update** existující Charter (úprava)
   - **Smazat a začít znovu** (potvrď destruktivně)
   - **Zvolit jiný slug**

3. **Načti referenční dokumenty** (musíš znát strukturu):
   - `docs/decisions/0001-decider-model.md` (kanonický eskalační protokol)
   - `docs/decisions/0004-charter-as-mandatory-input.md` (Charter template)
   - `docs/decisions/0008-tool-form-factor.md` (capacity profil)

4. **Veď wizard přes AskUserQuestion** — v tomto pořadí:

   **A) Identifikace:**
   - Project name (lidsky čitelný název projektu)
   - XYZ hypotéza — formát: *„Věříme, že [persona] s [JTBD] potřebuje [řešení],
     což měříme růstem [metric] o [delta] během [time window]."*
     Pokud uživatel s formulací bojuje, **delegujt sub-agenta `zadavatel-helper`**
     pro pomoc s draftem.

   **B) Decider + eskalace (ADR-0001):**
   - Decider name (jméno + role)
   - Decider mandate from (kdo a kdy podepsal mandát; např. „CPO Anna Nováková, 2026-04-15")
   - CPO/sponzor eskalační kontakt
   - Sponsor name
   - Backup Decider (volitelné, automatická delegace při PTO)

   **C) Success threshold:**
   - Primary lagging metric (např. „MAU +15 % T+90")
   - Leading metric (proxy, měřitelné T+7 nebo T+30)
   - Guardrail metric (co nesmí regredovat)

   **D) Kill criteria:**
   - Multi-line text: kdy projekt zrušíme (např. „Pokud T+30 leading metric
     nedosáhne X, escalation. Pokud T+90 lagging < Y, kill.")

   **E) Kapacitní commit (ADR-0008 + devil's advocate Útok 1):**
   - Capacity profile: `default` | `regulated` | `audit-grade`
     - default = greenfield low-risk, ~10 PD per cyklus
     - regulated = data/integrace/AI Act limited, ~14 PD
     - audit-grade = high-risk AI Act, regulated SDLC, ~18–22 PD
   - Person-days commit (číslo) — připomeň reálný range pro vybraný profil

   **F) Risk profile:**
   - AI Act risk-tier: `minimal` | `limited` | `high` | `unacceptable`
     **Pozor**: označ jako *provisional, re-assessed v Session 2*
     (devil's advocate Útok 4).
   - Data class: `L1` | `L2` | `L3` | `L4` (per `docs/methodology/02-role-catalog.md`)
   - **Pokud `unacceptable` nebo `L4`** → **STOP**: session se nekoná.
     Zaznamenej do decision logu a nepokračuj.

   **G) Throw-away vs evolve (ADR-0005):**
   - Default: `throwaway`
   - Pokud uživatel chce `evolve`, ptej se na 6 podmínek z ADR-0005 a vyžaduj
     splnění všech:
       1. Tým, který bude v produkci, je v Session 1 přítomen v plné síle.
       2. Stack v session = stack v produkci.
       3. Code review aplikuje se i na vibe-generated code.
       4. Design system compliance ≥ 90 %.
       5. Test pyramide split předem stanoven.
       6. Promote-to-prod gate checklist projde.
     Ulož pole splněných podmínek do `evolve_conditions_met`.

   **H) Reinforcement track (ADR-0004 + devil's advocate Útok 11):**
   - T+7: kdo měří co
   - T+30: kdo měří co
   - T+60: kdo měří co
   - T+90: kdo měří co + Go/Iterate/Kill review
   - **Reinforcement budget commit (PD)**: musí být explicit číslo, ne 0.

5. **Sestav JSON spec** z odpovědí a předej do `tool/cli/charter.py`:

```bash
python3 tool/cli/charter.py --spec /tmp/<slug>-spec.json
```

Output bude JSON s `{ project_id, charter_path, slug }`.

6. **Verifikuj výstup**:
   - Otevři vygenerovaný Charter (`data/charters/<slug>.md`) přes Read.
   - Ujisti se, že žádné pole nezůstalo `_PENDING_` nepatřičně.
   - Zaznamenej audit log entry úspěchu.

7. **Souhrn pro uživatele**:
   - Slug + project_id
   - Path k Charter souboru
   - Status: `charter` (next krok = `/pflanzer-roles <slug>`).
   - Připomeň pre-flight checklist z `docs/methodology/03-pre-session-priprava.md`
     — Charter je krok 1; než se spouští Session 1, musí být hotové
     `/pflanzer-roles` + `/pflanzer-triage`.

## Co NEDĚLAT

- Nezačínej Session 1 work — to je jiný command (`/pflanzer-session-1`).
- Nepřeskakuj žádné z polí A-H (kompletní Charter je MUST per devil's advocate Útok 11).
- Nesplš `unacceptable` AI Act tier nebo `L4` data class — to je hard STOP.

## Reference

- `docs/decisions/0004-charter-as-mandatory-input.md`
- `docs/decisions/0001-decider-model.md`
- `docs/decisions/0005-throwaway-vs-evolve-prototype.md`
- `docs/decisions/0008-tool-form-factor.md`
- `docs/methodology/03-pre-session-priprava.md`
