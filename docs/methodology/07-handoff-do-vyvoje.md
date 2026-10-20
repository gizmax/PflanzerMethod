# 07 — Ship, handoff a retro

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: co se děje po Go — Ship (`/pm ship`), handoff
> (`/pm handoff`) a měření outcome (`/pm retro`). Obsahuje i pravidla
> značení AI kódu (§ AI code provenance), na která odkazuje tool. Ship není
> setkání, ale pipeline a práce vývojářů; vítěz byl od začátku v target repu,
> takže se **nic nepřepisuje** (ADR-0005, ADR-0009).

## Ship (1–2 dny, vývojáři + provoz)

Předpoklad: Rozhodnutí skončilo Go s vítězem a krok Provoz má jméno.

1. **Ověř worktree** vítěze v target repu (`pflanzer worktree verify`).
2. **Quality gates jen na vítěze** (`pflanzer session_3 --slug <slug>`):
   lint, typy, testy, security, a11y, build, observability → **skóre X/100**.
   Práh **pilot 80 / production 85** (podle risk profilu ze zadání);
   security a testy mají dvojnásobnou váhu. Poražené varianty se nehodnotí.
   - Příkazy gates bere **adaptér `pflanzer.gates.yml` z base branche**
     target repa — varianta ho nepřepíše (report to hlásí). Bez adaptéru
     autodetekce stacku.
   - Verdikt „připraveno" vyžaduje aspoň build a testy a celkem 4 gates;
     jinak `blocked_by: gates:insufficient`. Neoverriduje se.
   - U `pilot`/`production` (a vždy u Full) musí být všechny triage tracky
     `ok`; jinak blokace. Override jen Decider s rationale
     (`--override-triage`).
3. **Pod prahem:** seznam, co dopravit (security/testy = blocker, lint/
   observability = varování). Decider volí: pilot s malou skupinou a
   paralelní oprava · pauza · Ship i přesto (override s rationale do
   decision logu).
4. **Checkpoint provozu** (20 min): deploy plán, monitoring, on-call,
   rollback, strop nákladů. Podpis:
   `pflanzer checkpoint --slug <slug> provoz --by "<jméno>" --note "…"`
   (`--list` ukáže stav oken). Bez podpisu Ship neprojde.
5. **PR vítěze do `main` target repa** přes běžnou pipeline a review;
   poražené větve se smažou.

### Checklist před prvním produkčním deployem

Sjednocuje výstupy gates a oken; vlastní ho vývoj s provozem.

```
[ ] build, testy a lint zelené; skóre ≥ práh (80 / 85)
[ ] secret scan a SBOM/licence scan clean (žádné Critical/High CVE)
[ ] acceptance scénáře (Gherkin, aspoň 1 negativní) projíždějí
[ ] AI provenance: trailery a PR labely přítomné, autor = člověk u klávesnice
[ ] observability: logy, metriky, traces; dashboard se 4 golden signals
[ ] SLO baseline a runbook; on-call a alerty nastavené
[ ] rollback otestovaný; feature flag default OFF, postupný rollout
[ ] checkpointy bezpečnost & právo a provoz podepsané
[ ] přístupnost: automat zelený; u veřejného rozhraní lidský review
[ ] měření: eventy/instrumentace nasazené, dashboard metriky ze zadání
[ ] podpora připravená (KB, makra) — je-li změna viditelná uživatelům
[ ] change advisory podle firemního procesu
```

Regulované (Full) navíc: DPIA a AI Act Fáze C podepsané DPO, Annex IV
kostra, vendor DPA/SCC, audit trail s retencí
([`governance/`](../governance/README.md)).

## Handoff (`/pm handoff`)

Název příkazu je stabilní rozhraní, význam je **předání vítěze do běžného
vývojového procesu přes PR**, ne re-implementace (ADR-0010). Generuje:

- **`SHIP.md`** — primární výstup, **1 stránka**: vítěz (větev + SHA),
  skóre X/100 vs práh, odpovědnosti (Decider, vlastník větve), příkaz
  `gh pr create`, checkpoint provozu, sekce „Změř po 30 dnech",
  viditelnost AI nákladů a kontrola trailerů.
- **Balíček per role** (doplněk pro audit, *sign-off package*): každý
  zástupce dostane jen svůj soubor.

| Krok cesty | Co v balíčku |
|------------|--------------|
| Vývoj | OpenAPI + breaking-change registr (pole · změna · konzument · vlastník · okno), migration plan stub, contract test skeleton, component manifest (reuse / nové / jednorázové), diff tokenů, ADR drafty |
| Provoz | SLO archetyp, runbook stub, odhad provozní stopy, rollback, on-call |
| Bezpečnost & právo | výsledek checkpointu, veto registr, SBOM/scan, u Full DPIA/RoPA/AI Act Fáze C |
| QA / test | 3–5 Gherkin scénářů per flow (aspoň 1 negativní), test pyramida, exploratory charter; kontrola, že AI testy testují chování, ne zrcadlí implementaci |
| Data / podpora | event taxonomie (`object_action`), measurement plan (lagging + leading + guardrail), predikce ticketů, termíny podpůrných materiálů |
| Rozhodnutí | decision log s lidskou atribucí, parking lot, zadání |

Placeholdery `TODO` v balíčcích jsou záměr — doplní tým podle kontextu.
Do balíčku nepiš osobní údaje.

**Metriky pilotu** (tool je zapíše, slouží k vylepšení metody): čas
dny od Go do merge · gate score vítěze · počet kol Iterate · kolik kódu vítěze
přežije 30 dní v `main` · AI náklady.

## AI code provenance

Decision log řeší atribuci **rozhodnutí**; tato sekce **kódu**: kdo je
autor AI-generovaného commitu, jak se značí, jak se reviewuje.

1. **Autor commitu = vývojář u klávesnice** (git author i committer).
   Ručí za kód jako za vlastní. **AI není autor ani spoluautor** — žádný
   `Co-Authored-By` s AI; automatickou atribuci builderu vypni. V mob
   režimu (ADR-0016) je autorem aktuální driver; commituje se před předáním
   klávesnice.
2. **Trailery** zapisuje tool automaticky (`worktree.py` při založení variant,
   `handoff_pr.py` je přepne na `ship` a ověří před PR):

   | Trailer | Hodnota |
   |---------|---------|
   | `Pflanzer-Variant` | `<slug>-A` / `-B` / `-C` / `-mob` |
   | `Pflanzer-Session` | fáze vzniku commitu: `1` Build, `2` Iterate/Rozhodnutí, `ship` |
   | `AI-Assisted` | builder (`claude-code`, `codex-cli`, `cursor`, …); u `manual` se vynechává |

   Jsou strojově čitelné (`git log --format='%(trailers:key=AI-Assisted)'`).
3. **PR labely** `pflanzer`, `ai-generated`, `pflanzer:<slug>` a sekce
   **„AI provenance"** v PR body (builder, rodina modelu, 3 varianty / vítěz,
   kdo seděl u klávesnice, odkaz na decision log / SHIP.md).
4. **Review AI kódu = stejná review jako lidského** (stejní reviewers,
   CODEOWNERS, CI); approve dává člověk mimo autora. Reviewer navíc
   odpoví na tři otázky: (a) použila varianta existující komponenty repa,
   nebo vytvořila paralelní? (b) jsou v kódu mocky, stuby, hardcoded data
   nebo TODO, které musí pryč, a mají vlastníka? (c) ověřil člověk, že AI
   testy testují skutečné chování?
5. **IP a licence:** kód podléhá firemní licenční politice; secret a licence
   scan před mergem; do promptů **nikdy produkční data** ani cizí
   licencovaný kód; builder má podepsané DPA.
6. **Retence:** default profil — git history (autor + trailery) a PR stačí.
   Regulované: navíc prompt history a audit log s retencí podle regulace
   (DORA 7 let).

**Kdo podepisuje co:** vývojář kód (commit + PR) · Decider rozhodnutí
(decision log) · bezpečnost scany a checkpoint · provoz checkpoint provozu ·
EM kapacitu na hardening.

### AI náklady

SHIP.md ukazuje tokeny (input/output/cache) per varianta a za cyklus ze
session logů Claude Code na stroji, kde běžel Build (`tool/cli/ai_usage.py`;
USD jen s lokálním ceníkem `pflanzer.prices.json`). Je to viditelnost pro
EM, ne limit ani gate. Strop nákladů hlídá checkpoint bezpečnost & právo.

## Retro (`/pm retro`)

Pod povrchem, mimo pět kroků hlavní cesty. Spouští ho ten, kdo vlastní měření
(zástupce Produktu nebo Provozu), po mergi vítěze:

- `measure` — z target repa spočítá % LOC vítěze v produkci beze změny
  (cíl ≥ 80 %) a days-to-prod (cíl ≤ 14); při nesplnění FLAG.
- `reminders` — nastaví readouty od Go: **T+7** bugy a hotfixy ·
  **T+30** leading metrika, přijetí handoffu vývojem · **T+60** podíl
  přepsaných LOC (rework) · **T+90** lagging metrika vs kritérium ze zadání
  a verdikt Go/Iterate/Kill pro další vývoj.
- `record` / `report` — ruční readouty a souhrn `data/retro/<slug>-retro.md`.

T+90 je vstup pro zlepšení samotné metody (kalibrace váhy AI-only feedbacku,
velikosti jádra, délky oken). Bez readoutů se metoda zlepšovat nedá.

## Adopce a další piloty

Druhý a další pilot v jednotce vede **Champion** (#17,
[`02`](02-role-catalog.md)): drží retro a měření, předává zkušenosti,
určuje zástupce (buddy), který ho zastoupí při odchodu (viz
[`08`](08-edge-cases-a-rizika.md) § 10). Vrstva pro víc pilotů
(Method Steward, pre-registrace, PflanzerIndex): [`governance/`](../governance/README.md).

## Track S (jen výjimečně)

Když vývojář není k dispozici a platí jeden ze čtyř triggerů, výstupem
není kód, ale **precision spec ≥ 80/100** s pětistupňovým předáním vývoji
(walkthrough, Q&A okno, amendment protokol, první milestone, embedded
reviewer) a pravidly proti driftu. Je to mimo hlavní cestu: ADR-0020
a [`governance/`](../governance/README.md). Platí pro něj stejná AI
provenance.

## Co handoff NENÍ

ZIP s prototypem hozený přes plot · ticket „implementuj podle Figmy" ·
„vibe-deployed" instance s produkčními credentials · stránka bez atribuce
rozhodnutí · předání bez gates a checklistu.
