---
description: Ship gate — quality gates + winner + SHIP.md; alias pro `/pm ship`
---

# /pflanzer-session-3 — Ship gate (dříve Session 3)

> **Branding:** Každý user-facing výstup tohoto commandu začíná brand line
> **`Pflanzer Method | pflanzer.cz/method`** (první řádek, pak prázdný řádek).

Argumenty: `$ARGUMENTS` = projekt slug.

Předpoklad: `projects.status = 'handoff'` (= Decider's Go v Session 2).

## Co tento command dělá

**Ship gate není meeting.** Je to pipeline, kterou po Decider's Go spustí
jeden člověk (typicky dev u klávesnice nebo facilitátor) a výsledek ukáže
Deciderovi. Název `/pflanzer-session-3` a `tool/cli/session_3.py` zůstávají
jen jako technické názvy; v dokumentaci a u stolu je to **Ship gate**
(`/pm ship`).

Default cesta metody: varianty staví 3× Claude Code ve **worktrees target
repa** (`python tool/cli/worktree.py setup --slug <slug>` →
`~/.pflanzer/targets/<slug>-{A,B,C}/`, branche `pflanzer/<slug>-{A,B,C}`).
Ship gate proto kód nikam nekopíruje a na GitHub URL se neptá:

1. **Autodetekce worktrees** — pro každou variantu najde její worktree,
   ověří `git remote get-url origin == projects.target_repo_url`
   (pre-flight, ADR-0009) a gates pouští **přímo ve worktree**
   (`extracted_code.extraction_method = 'worktree'`, `local_path` = worktree).
2. **Quality gates** na každé variantě (build / types / lint / tests /
   coverage / acceptance / security / a11y / observability) → `gate_score
   0-100` vs `production_readiness_target` z Charteru. Příkazy gates bere
   z adaptéru `pflanzer.gates.yml` **z base branche** target repa, ne
   z variant branche (integrita — agent ve worktree ho mohl „zjednodušit").
3. **Minimum gates pro verdikt** — `production_ready` jen když běžely
   (pass / warn / fail) aspoň 4 gates a mezi nimi `build` i `tests`. Jinak
   `blocked_by: ["gates:insufficient (3/9 run, missing: build, tests)"]`.
4. **Winner** = nejvyšší gate_score (tie-break = preference_score ze Session 1).
5. **Triage hard gate** — pro risk profil `pilot` / `production` musí mít
   všechny 4 triage tracky (discovery / security / legal / platform) status
   `ok`. Jinak `production_ready = false` bez ohledu na gate score
   a výstup nese `blocked_by: ["triage:security deferred", …]`.
6. Výstup: `data/production_reports/<slug>-readiness.md` a pak SHIP.md
   (`/pm handoff`).

Pořadí zdrojů kódu per varianta (`tool/cli/extract.py` `plan_extraction`):

| Priorita | Zdroj | Kdy |
|----------|-------|-----|
| 1 | `--method-overrides` | explicitní volba týmu |
| 2 | `worktree` | worktree varianty existuje (default cesta) |
| 3 | `git_clone` (`--repo-urls`) | hosted builder (Bolt / v0 / Lovable) u projektu s `--prefer-hosted` |
| 4 | `skeleton` | **jen risk profil `throwaway`** |

Pro `pilot` / `production` bez worktree a bez hosted URL Ship gate
**fail-loud** skončí hláškou „spusť `python tool/cli/worktree.py setup --slug
<slug>`" — skeleton by vyrobil greenfield kód, který do target repa nepůjde
(reuse ~0 %).

## Jak postupuj

### Krok 1 — Autodetekce worktrees (žádná otázka na GitHub URL)

Ověř, že worktrees existují a patří do target repa:

```bash
python tool/cli/worktree.py verify --slug $ARGUMENTS --cwd ~/.pflanzer/targets/$ARGUMENTS-A
# … totéž pro -B, -C (resp. -mob v mob mode)
```

- Všechny worktrees existují a `verify` vrací `ok` → pokračuj Krokem 2
  **bez otázek**.
- Worktree chybí a varianta vznikla v Claude Code / Codex CLI / Cursoru →
  nic se neptej; řekni týmu, ať spustí
  `python tool/cli/worktree.py setup --slug $ARGUMENTS` a variantu ve
  worktree postaví (resp. commitne na branch `pflanzer/<slug>-<X>`).
- Worktree chybí **a** projekt jel přes `--prefer-hosted` (builder varianty
  je `v0` / `bolt` / `lovable`) → teprve teď se zeptej:

```
AskUserQuestion: "Varianta {X} ({builder}) nemá worktree. Máš GitHub URL z buildru?"
options:
  - "Ano, vlož URL" [text input → https://github.com/<org>/<repo>]
  - "Ne — varianta do Ship gate nepůjde" (vyřaď ji ze shortlistu)
  - "Throwaway projekt — použij skeleton" (jen pokud risk profil = throwaway)
```

- Skeleton nikdy nenabízej pro `pilot` / `production`.

### Krok 2 — Spusť Ship gate

Default (worktrees):

```bash
python3 tool/cli/session_3.py --slug $ARGUMENTS
```

Jen pro hosted varianty bez worktree (`--prefer-hosted`):

```bash
python3 tool/cli/session_3.py --slug $ARGUMENTS \
  --repo-urls '{"B": "https://github.com/team/onboarding-b"}'
```

Pokud příkaz skončí `✖ Ship gate zastaven: …` (exit 2), ukaž hlášku týmu
doslova — typicky chybí worktree, nesedí `origin` vs `target_repo_url`, nebo
je požadovaný skeleton u pilot/production. Nic neobcházej přes
`--method-overrides skeleton`; pro pilot/production ho tool stejně odmítne.

### Krok 3 — Minimum gates + adaptér z base

Ship gate před gates načte `pflanzer.gates.yml` (resp. `.yaml` / `.json`)
z base branche target repa (`git -C <worktree> show origin/<target_branch>:pflanzer.gates.yml`,
fallback `<target_branch>:…`) a pustí gates s touto verzí. V base žádný
adaptér není → autodetekce stacku.

- V reportu (`Adaptér` sloupec + sekce „Gate adaptér — integrita") zkontroluj
  warning **„adapter modified in variant branch — ignored"**: varianta
  adaptér změnila, gates běžely s verzí z base. Změnu adaptéru řeš jako
  změnu CI configu — PR do base branche s review, ne ve variant branchi.
- Pokud `per_variant[].gates_sufficient = false` a winner nese
  `gates:insufficient (…)` v `blocked_by`: gates nemají dost důkazů pro
  verdikt (typicky Java / .NET / Go repo bez adaptéru, `build`/`tests`
  jako `unsupported`). Řekni týmu, ať doplní adaptér do **base branche**
  (`pflanzer init gates-template --path <repo>`, viz
  `tool/templates/README-gates.md`) a Ship gate spustí znovu. Tohle se
  neoverriduje — bez `build` a `tests` není co podepsat.

### Krok 4 — Triage gate

Ve stdout zkontroluj `blocked_by` a `triage.tracks`.

Pokud `blocked_by` není prázdné (typicky po in-room `/pflanzer`, který
triage záměrně odkládá jako `deferred`):

```
Pflanzer Method | pflanzer.cz/method

⛔ Blokováno: spusť `/pm triage <slug>`
   triage:security deferred, triage:legal deferred
   production_ready = false (gate score {N}/{target} na tom nic nemění)
```

Zeptej se Decidera:

```
AskUserQuestion: "Triage není podepsaný ({blocked_by}). Co teď?"
options:
  - "Spustit /pm triage teď, pak Ship gate znovu" (doporučeno)
  - "Pilot v sandboxu bez production launche, triage paralelně"
  - "Decider override (rationale do decision logu)"
```

Override jen explicitně a s rationale — zapíše řádek do `decisions`
(`type = 'triage'`) a do `audit_log`:

```bash
python3 tool/cli/session_3.py --slug $ARGUMENTS \
  --override-triage --rationale "Security podepsal ústně 2026-09-20, písemně do T+2d; pilot bez L3 dat."
```

Override pokrývá jen blokace, které existovaly v okamžiku override; nová
blokace (např. security přejde na `blocked`) Ship gate znovu zablokuje.

### Krok 5 — Vyhodnocení & Decider call

Stdout obsahuje:
- `production_ready`, `blocked_by`, `risk_profile`, `triage`
- `winner` s `gate_score`, `gate_ready`, `local_path` (= worktree), `next_step`
- `per_variant[]` s každou variantou + score + `method` + `gates_run` /
  `gates_sufficient` + `adapter` (zdroj + warnings)

Ukaž týmu na velký TV:

```
Pflanzer Method | pflanzer.cz/method

Variant A (claude-code) → gate score 85/100  🚀 ready     worktree
Variant C (claude-code) → gate score 72/100  ⚠ pilot-only worktree
Triage: discovery ok · security ok · legal ok · platform ok
```

Pokud `production_ready=true`:
```
✅ Winner: Variant A (branch pflanzer/<slug>-A). Většina kódu je použitelná.
   Next: /pm handoff $ARGUMENTS → SHIP.md + gh pr create.
```

Pokud `production_ready=false` kvůli gate score (triage i minimum gates OK):
- Ukaž failed gates (security/tests = blocker, lint/observability = warn).
- Zeptej se Decidera:

```
AskUserQuestion: "Score {N}/{target} pod targetem. Co teď?"
options:
  - "Pilot s 5 uživateli, paralelně fix gates" (žádný production launch)
  - "Pause — tým 1-2 sprinty harduje ve worktree, pak re-run Ship gate"
  - "Ship anyway (Decider override + rationale do decision logu)"
```

### Krok 6 — SHIP.md + PR

```bash
/pm handoff $ARGUMENTS
```

SHIP.md (`data/handoffs/$ARGUMENTS/SHIP.md`) obsahuje:
- blok **„Blokováno"** nahoře, pokud triage gate neprošel,
- winnera **ze Ship gate** (nejvyšší gate_score, tie-break preference_score)
  s řádkem „Vybrán podle"; preference_score jen jako fallback, když Ship
  gate ještě neběžel,
- počet spuštěných gates a warning, pokud se adaptér ve worktree liší od base,
- sekci **„Triage stav"** (per track ok / deferred / failed + signed_by),
- sekci **„AI provenance"** + read-only kontrolu trailerů na
  `base..pflanzer/<slug>-<W>` (chybějící trailery / AI `Co-Authored-By` /
  bot autor = warning, historie se nepřepisuje),
- sekci **„AI náklady (viditelnost)"** — tokeny Claude Code per varianta
  + celkem za cyklus ze session logů na tomto stroji (USD jen s ceníkem,
  `tool/templates/README-ai-usage.md`; bez limitu),
- copy-paste `git commit` s trailery `Pflanzer-Variant` /
  `Pflanzer-Session: ship` / `AI-Assisted` (autor = dev u klávesnice)
  a `gh pr create` s labely `pflanzer`, `ai-generated`, `pflanzer:<slug>`.

## Co NEDĚLAT

- **Neptej se na GitHub URL**, když worktrees existují — default cesta je
  Claude Code ve worktree target repa, URL je jen fallback pro `--prefer-hosted`.
- **Nenabízej skeleton** pro `pilot` / `production` — greenfield scaffold
  do target repa nepůjde. Skeleton je jen pro `throwaway`.
- **Neobcházej triage gate** — `production_ready` s `deferred` trackem jde
  jen přes `--override-triage --rationale "…"` (decision log, DORA / AI Act
  čl. 14). Ústní „security to ví" nestačí.
- **Neupravuj `pflanzer.gates.yml` ve variant branchi** — Ship gate ho
  stejně ignoruje a bere verzi z base branche.
- **Nepřeskakuj quality gates** kvůli rychlosti — gate fail = production
  bug. Decider override musí mít rationale do logu.
- **Nepřebíj winner** ručně — score je deterministicky weighted (security
  + tests = 2× váha). Pokud Decider nesouhlasí, řešit přes preference_score
  v Session 1, ne tady.
- **Nesvolávej meeting** — Ship gate je pipeline; lidi potřebuješ až na
  Decider call (Krok 4–5), a i ten může proběhnout async.
- **Nenastavuj AI jako autora commitu** ani `Co-Authored-By` s AI — AI
  asistenci značí jen trailery.

## Reference

- `tool/cli/session_3.py` (Ship gate orchestrator, triage hard gate, `--override-triage`)
- `tool/cli/extract.py` (`plan_extraction`: worktree > hosted URL > skeleton jen throwaway)
- `tool/cli/worktree.py` (`setup` / `verify`, cesty `~/.pflanzer/targets/<slug>-<X>/`)
- `tool/cli/quality_gates.py` (gates + scoring, adaptér `pflanzer.gates.yml`)
- `tool/templates/README-gates.md` (adaptér pro Java / .NET / Go / vlastní příkazy)
- `tool/cli/triage.py` (`ship_triage_gate`, `record_triage_override`)
- `tool/cli/handoff_pr.py` (SHIP.md, trailery, labely, AI provenance)
- `docs/methodology/07-handoff-do-vyvoje.md` § AI code provenance
- `docs/decisions/0009-worktree-in-target-repo.md`
- `data/production_reports/<slug>-readiness.md` (výstup)
