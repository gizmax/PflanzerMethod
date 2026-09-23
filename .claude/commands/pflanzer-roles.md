---
description: Vede tým decision tree pro výběr rolí z 18-position role catalogu (Slice 2). Persistne role rows do DB + generuje summary.
---

# /pflanzer-roles — Role selection wizard (Slice 2)

Argumenty: `$ARGUMENTS` = projekt slug. Předpokládá, že už proběhl
`/pflanzer-charter <slug>` (status musí být `charter`).

## Co tento command dělá

Aplikuje decision tree z `docs/methodology/02-role-catalog.md` § Decision tree
(15 kroků) a vybere podmnožinu rolí pro daný projekt. Persistne `roles` rows
v DB a generuje `data/charters/<slug>-roles.md` summary.

## Jak postupuj

1. **Validuj slug** — pokud `$ARGUMENTS` chybí, použij AskUserQuestion.
   Ověř, že `projects.status = 'charter'` (= proběhl `/pflanzer-charter`).
   Pokud `draft` → instruuj uživatele spustit Charter wizard nejdřív.

2. **Načti referenční dokumenty:**
   - `docs/methodology/02-role-catalog.md` (decision tree, 18 rolí)
   - `tool/data/role_catalog.json` (machine-readable verze)
   - `docs/research/synthesis/03-role-catalog-updates.md` (povýšení / degradace)

3. **Veď wizard přes AskUserQuestion** — 16 otázek v decision tree:

   **MoSCoW profil** (jako první, ovlivňuje strict/permissive resolution):
   - `default` (greenfield, low-risk) | `regulated` (data/integrace/AI Act limited)
   - | `audit-grade` (high-risk AI Act, regulated SDLC)
   - Pro `audit-grade` připomeň, že **co-facilitator SHOULD** (devil's advocate
     Útok 10) — bude se ptát na owner Facilitátora #3 ve vlastnictví fázi.

   **Trigger questions** (ano/ne pro každou):

   1. **ui_changes**: Mění se UI nebo přidává se nový view? *(role #4 FE, #6 UX)*
   2. **data_or_api**: Mění se data nebo API? *(#5 BE)*
   3. **new_flow**: Vzniká nový user flow nebo přepracování core experience? *(#6 UX)*
   4. **data_auth_integration**: Pracujeme s daty uživatelů, auth, integracemi
      nebo platbami? *(#7 Security — povinně, pokud ano)*
   5. **release_intent**: Jakákoli zmínka „produkce" nebo „pilot" v output?
      *(#8 QA — povinně, pokud ano)*
   6. **scope_2plus_sprints**: Bude scope déle než 2 sprinty / je to PI priority?
      *(#9 Engineering manager)*
   7. **personal_data_marketing_ai_act**: Osobní data, marketing, novel AI use
      case (≥ Limited risk-tier), nebo regulovaný produkt (PSD2/MiFID)? *(#10 Legal)*
   8. **customer_facing_or_b2b_250**: Customer-facing nebo B2B nad 250
      zaměstnanců? *(#11 A11y default-on, opt-out s justifikací)*
   9. **release_intent_or_metrics**: Release intent (= ship plánován) nebo
      nové metriky / A/B test? *(#12 Data)*
   10. **customer_base_1000**: Customer base > 1000 active users + user-facing
       change? *(#13 CS proxy)*
   11. **customer_facing_or_new_segment**: Customer-facing flow nebo nový segment?
       *(#14 User research default-on, opt-out s justifikací)*
   12. **infra_changes**: Změny v infra / deploy / runtime / sandbox? *(#15 DevOps)*
   13. **user_facing_copy**: User-facing copy / marketing claims / error
       microcopy / B1-B2 plain language? *(#16 UX writer)*
   14. **second_plus_pilot**: Druhý+ pilot v BU, nebo scaling Pflanzeru
       ve společnosti? *(#17 Champion)*
   15. **multi_team_or_complex_domain**: Multi-team scope (≥ 3 týmy) nebo
       komplexní doména (vyžaduje Event Storming) nebo regulovaný SDLC?
       *(#18 Solution architect)*

   **Opt-out flagy** (jen pokud trigger je 'true'):
   - Pokud `customer_facing_or_b2b_250` = true → zeptej se, jestli chce
     **opt-out z A11y** (#11). Pokud ano, **vyžaduj justifikaci** (text důvodu —
     např. „pure internal admin tool < 50 zam, žádný WCAG závazek").
   - Pokud `customer_facing_or_new_segment` = true → zeptej se na opt-out
     z User research (#14). Justifikace: fresh persona ≤ 3 mo + JTBD podpis PM.

4. **Vlastnictví rolí** — pro každou vybranou roli zeptej se na human_owner
   (jméno + role v org). Pokud uživatel nezná jméno, můžeš nechat prázdné —
   doplní se před Session 1.

5. **Edge case: First pilot v BU** — pokud `second_plus_pilot` = false
   (= je to první pilot v této BU), připomeň ADR-0006:
   - Champion (#17) musí být v Bootstrap režimu (externí coach / rotace
     z první BU / tandem). Pokud uživatel nemá řešení, **flagni** to v summary.
   - Champion buddy POVINNÝ ve všech režimech.

6. **Sestav JSON spec** a předej do `tool/cli/roles.py`:

```bash
python3 tool/cli/roles.py --spec /tmp/<slug>-roles-spec.json
```

JSON spec format:
```json
{
  "slug": "demo-widget",
  "profile": "default",
  "ui_changes": true,
  "data_or_api": true,
  "new_flow": false,
  "data_auth_integration": false,
  "release_intent": true,
  "scope_2plus_sprints": false,
  "personal_data_marketing_ai_act": false,
  "customer_facing_or_b2b_250": true,
  "release_intent_or_metrics": true,
  "customer_base_1000": false,
  "customer_facing_or_new_segment": true,
  "infra_changes": true,
  "user_facing_copy": true,
  "second_plus_pilot": false,
  "multi_team_or_complex_domain": false,
  "a11y_optout": false,
  "a11y_optout_reason": "",
  "user_research_optout": false,
  "user_research_optout_reason": "",
  "owners": {"1": "Tom Pflanzer", "2": "Lucie Veselá"}
}
```

7. **Verifikuj výstup**:
   - Read `data/charters/<slug>-roles.md`.
   - Pokud sanity warning > 10 lidí, navrhni zúžit scope.
   - Pokud audit-grade profil, připomeň co-facilitator SHOULD.

8. **Vygeneruj role cards a rozešli je lidem** (audit N15) — 1 strana per
   vybraná role se jménem člověka, Deciderem, termíny Session 1/2 a stupněm:

```bash
python3 tool/cli/roles.py cards --slug <slug> [--tier quick|lean|full]
```

   - Výstup: `data/role-cards/<slug>/<NN>-<role>.md` + `README.md` (tabulka
     role → člověk → karta). Stupeň se odvodí z DB; když nesedí, předej `--tier`.
   - Řekni uživateli, ať **každému pošle jen jeho kartu** (s pozvánkou na
     Session 1) — sponzor ani Security nemusí číst `04-session-1.md`.
   - Karty bez jména (`— doplň jméno`) = chybí `human_owner`; doplň a přegeneruj.
   - Obecné karty bez projektu: `docs/methodology/role-cards/`.

9. **Souhrn pro uživatele**:
   - Počet vybraných rolí + jejich seznam s AI proxy režimem.
   - Path k summary a ke kartám (`data/role-cards/<slug>/README.md`).
   - Status: `charter` (zůstává — status='triage' nastaví slice 3).
   - Next krok: `/pflanzer-triage <slug>`.

## Co NEDĚLAT

- Nepřeskakuj decision tree otázky — chceme deterministické pokrytí.
- Neignoruj sanity warnings (> 10 lidí, audit-grade bez co-facilitator).
- Nezapomeň na Champion bootstrap (ADR-0006), pokud first pilot.

## Reference

- `docs/methodology/02-role-catalog.md` (decision tree)
- `docs/research/synthesis/03-role-catalog-updates.md` (proms / degradace)
- `docs/decisions/0003-role-catalog-promotions.md` (ADR)
- `docs/decisions/0006-champion-bootstrap.md` (Champion provisioning)
