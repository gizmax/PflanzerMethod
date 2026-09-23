# Audit Pflanzer Method pro vibe-coding uvnitř firem — nálezy a návrhy zlepšení

> **Datum:** 2026-09-23 · **Rozsah:** `docs/methodology/`, `docs/decisions/`,
> `.claude/commands/`, `.claude/agents/`, `tool/cli/`, `tool/web/`, README,
> case study. **Metoda auditu:** čtení dokumentace a kódu, křížová kontrola
> claimů mezi marketingem, metodikou a toolem. Tool jsem nespouštěl proti
> reálnému target repu, pilotní data (e-shop 2026) nejsou doplněna, takže
> tvrzení o efektu metody jsem posuzoval jen podle konzistence a mechanismů,
> ne podle výsledků.

## TL;DR

Metoda má **silné jádro**, které v korporátním vibe-codingu skutečně chybí:
dev v místnosti od minuty 0 (Track P), anti-HiPPO hlasování, hierarchie
závaznosti místo binárního veta, pre-flight triage a worktree v target repu
(ADR-0009). To jsou správné páky.

Hlavní problém není v principu, ale v tom, že **repo dnes obsahuje tři různé
Pflanzery najednou** (90minutový in-room, 3hodinový lean, 5–6hodinový
audit-grade) a **tool pořád místy nese v0.2 logiku** (throw-away default,
Bolt/v0 extract), kterou v0.4 dokumentace už opustila. Druhý problém: metoda
slibuje „kód jde do produkce“, ale **nemá nástroj, který by to změřil**.
Bez měření zůstane e-shop case study s `_< doplnit >_` a marketing claim
neobhajitelný.

Navrhuji 6 P0 zásahů (konzistence + měření + gate), 8 P1 (metoda pro
korporátní realitu: Java/.NET stacky, více repozitářů, preview pro
non-tech, provenance AI kódu) a 4 P2 (adopce).

---

## 1. Co funguje (a co nerozbíjet)

| Prvek | Proč je to správně | Kde |
|-------|--------------------|-----|
| **Track P: dev v room = produkt, ne handoff** | Jediný způsob, jak z vibe-codingu nedostat „re-implementaci podle prototypu“. Správně gate-ovaný 4 hard triggers pro Track S. | ADR-0020, `07-handoff-do-vyvoje.md` |
| **Worktree v target repu, ne v meta-repu** | P0 fix, bez kterého je reuse 0 %. Cached clone + package manager autodetekce je pragmatické. | ADR-0009, `tool/cli/worktree.py` |
| **Acceptance criteria jako vstup do session** | Decider napíše Gherkin před vibe-codingem, AI píše kód, aby prošel. Dává apples-to-apples srovnání variant. | `pflanzer.md` KROK 3, `quality_gates.py` (gate `acceptance`, váha 2.5) |
| **Diversity přes 3 prompty, ne 3 buildery** | Odstraňuje migration overhead „3 weby na 3 builderech“, který case study sama pojmenovala jako problém. | README § Volba builderu |
| **Anti-HiPPO + rationale povinný + AI-only deflace 0.5** | Jediný differentiator, který je zároveň sociální mechanismus i auditní stopa. | `04-session-1.md`, `06-session-2.md` |
| **Hierarchie závaznosti (Critical / Yellow / Score)** | Dává Security a Legal strukturovanou cestu, ne veto-kladivo. | `05-mezi-sessions.md` |
| **Lean 1-pager + explicitní „co NEpotřebuješ“** | Vzácná poctivost: audit-grade overhead je označený jako overhead. | `00-lean-pflanzer.md` |
| **Devil's advocate a falsifiability kolo** | Metoda má vlastní kill criteria. Většina workshop metod nemá. | `docs/research/synthesis/05-*`, ADR-0011/13 |

---

## 2. Nálezy — seřazené podle dopadu

Formát: **Situace → Důkaz → Dopad → Návrh.**

### N1. Tři neslučitelné definice Session 1 (a „2 vs 3 sezení“) — P0

**Situace.** Čtenář se dozví tři různé délky a dva různé počty sezení podle
toho, který soubor otevře první.

**Důkaz.**
- `README.md:36` — „Session 1: Explore (in-room, 60-90 min)“; `README.md:126` — „Session 1 orchestrator (5–6 h)“.
- `00-lean-pflanzer.md:37` — „Session 1 — vibe (3 h, in-room)“ a „2 setkání“.
- `04-session-1.md:5,22` — „Délka 5–6 h, konec 16:00“.
- `.claude/commands/pflanzer.md:13` — „do 60-90 min mít shortlist + akční handoff“.
- README nadpis „3 sezení = ship to production“ vs lean „2 setkání“ vs
  `07-handoff-do-vyvoje.md` (Track P: D11–14 polish, žádná Session 3).

**Dopad.** Facilitátor nemá jeden autoritativní recept. Sponzor slyší
„90 minut“ a EM plánuje kapacitu na „5–6 h“. Session 3 je v toolu
(`/pflanzer-session-3`), ale metodika ji pro Track P nepopisuje jako
setkání.

**Návrh.**
1. Pojmenovat explicitně **tři stupně jedné metody** a dát je do jedné
   tabulky v `00-lean-pflanzer.md` (a jen odkazovat odjinud):
   - **Quick** (`/pm live`, 90 min): 1 kolo 30 min build, silent vote,
     1-page handoff, triage deferred, jen `throwaway`/`pilot`.
   - **Lean** (3 h): 2 kola build (30 + 30 min) s mid-checkpointem, vote,
     Decider shortlist; default pro Track P.
   - **Full** (5–6 h): kompletní agenda z `04-session-1.md` (VoC, pre-mortem,
     Crazy 8s, shadow agenti); audit-grade / regulated.
2. **„Session 3“ přejmenovat na „Ship gate“**. Není to setkání, je to
   pipeline (`quality_gates.py` + SHIP.md), kterou pouští dev pár po Session 2.
   Tím se sjednotí „2 sezení“ v metodice s „3 kroky“ v toolu.

### N2. Tool i část metodiky stále nesou v0.2 „throw-away default“ — P0

**Situace.** ADR-0005 v0.4 invertoval default na `evolve`. Sweep nebyl
dokončen a **Charter wizard v toolu vede uživatele k opačnému defaultu**.

**Důkaz.**
- `.claude/commands/pflanzer-charter.md:73` — „Default: `throwaway`“ + 6 podmínek pro evolve (v0.2 logika).
- `03-pre-session-priprava.md:386` — „Throw-away/evolve flag explicit (default = throw-away)“.
- `06-session-2.md:87` — „Prototyp do prod: throw-away je default v Charteru.“
- `08-edge-cases-a-rizika.md` § 8 — „Throw-away je default v Charteru; evolve vyžaduje 5-podpisový balíček.“
- `.claude/agents/fe-vibe-coding-expert.md` — „Brownfield + AI builder = throw-away pouze.“ (expert sub-agent bude systematicky skórovat proti Track P.)

**Dopad.** Přímý rozpor s hlavním marketing claimem („kód jde do produkce“).
Tým, který projde plným wizardem, skončí s throw-away Charterem, a FE expert
agent bude penalizovat evolve u brownfieldu, což je 80 % korporátních případů.

**Návrh.** Jednorázový sweep: 5 míst výše + `tool/cli/charter.py` default
`evolve`. V `pflanzer-charter.md` nahradit „6 podmínek pro evolve“ opačnou
logikou: **throw-away vyžaduje rationale z 3 povolených use-casů** (ADR-0005
v0.4). FE expert lens přepsat na „brownfield + evolve = reuse existing
components; risk ↑ pokud varianta zakládá nové komponenty mimo DS“.

### N3. `/pflanzer-session-3` je napsaný pro Bolt/v0/Lovable, ale default je Claude Code ve worktree — P0

**Situace.** README a `/pflanzer` říkají „3× CC v 3 worktrees target repa“.
Ship command pořád začíná otázkou „máš GitHub URL z Boltu/v0/Lovable?“.

**Důkaz.** `.claude/commands/pflanzer-session-3.md` Krok 1 („Variant A — máš
GitHub URL z Boltu/v0/Lovable?“, možnost „skeleton“), `tool/cli/extract.py`
`SKELETON_FILES` generický Vite scaffold. `docs/research/code-reusability/synthesis.md`
T5 tuto větev označil jako fallback jen pro throwaway.

**Dopad.** Pro default cestu je „extract“ no-op, ale UX tým nutí odpovídat
na irelevantní otázky. Skeleton fallback pro `pilot`/`production` produkuje
greenfield kód, který do target repa nepůjde (reuse ~0 %).

**Návrh.** Ship gate autodetekuje `pflanzer/<slug>-{A,B,C}` branche
v `~/.pflanzer/targets/<repo>/` a pouští gates přímo ve worktree. Otázka na
GitHub URL jen při `--prefer-hosted`. Skeleton povolit pouze pro
`risk_profile = throwaway`; jinak fail-loud.

### N4. Klíčová metrika metody se nikde neměří — P0

**Situace.** Metoda stojí na claimu „většina kódu z vibe-session jde do
produkce“ (cíl ≥ 80 % LOC merged without modification, Track P deploy D11–14).
Tool tuto hodnotu **neumí zjistit**.

**Důkaz.**
- `tool/db/schema.sql` — tabulky `projects … prompts`; žádná tabulka pro
  outcome (PR URL, merge datum, diff stat winner branch vs merged, T+7 bugy).
- `grep reuse|merged|rework tool/` — jen komentáře, žádná instrumentace.
- `docs/case-studies/eshop-2026.md` § Ship to production — čtyři otázky
  s `_< Doplnit po skutečném deploy >_`, 4 měsíce po pilotu nedoplněné.
- Reinforcement track T+7/30/60/90 existuje jen jako text v Charteru a SHIP.md.

**Dopad.** Bez dat je ADR-0014 PflanzerIndex i method-charter falsifikace
neproveditelná. Marketing claim „14 dní k produktu“ zůstává anekdotou.
Toto je současně největší reputační riziko pro metodu, která sama
prodává falsifikovatelnost.

**Návrh.** Nový command **`/pm retro <slug>`** (a `tool/cli/retro.py`):
1. Najde winner branch a merged PR v target repu (`gh pr list --search`
   nebo ručně vložená PR URL).
2. Spočítá `loc_winner`, `loc_merged_unchanged` (git diff mezi winner
   commitem a merge commitem po cestách, které winner zavedl), `days_to_prod`
   (Session 2 → merge/deploy tag), `t7_bugs` (issues s labelem `pflanzer:<slug>`).
3. Zapíše do nové tabulky `outcomes(project_id, milestone, metric, value,
   evidence_url, recorded_by, recorded_at)`.
4. Připomínky T+7/30/90 generovat jako `.ics` nebo GitHub issue s due date
   při `handoff` (tool už zná ownery z Charteru).
5. Case study `eshop-2026.md` doplnit z těchto dat, ne ručně.

### N5. In-room `/pflanzer` pro `production` odkládá triage a ship path to nevynucuje — P0

**Situace.** `/pflanzer` (Quick) záměrně deferuje všechny 4 triage tracky.
To je pro 90minutový formát správně. Ale nic dál po cestě neblokuje
`production_ready = true` bez dokončeného triage.

**Důkaz.** `tool/cli/quick_session.py` `_set_triage_deferred()`;
`tool/cli/session_3.py` a `tool/cli/handoff_pr.py` neobsahují kontrolu
`triage.status` (`grep deferred` bez výsledku). `pflanzer.md` jen textově
říká „Pre-pilot/production MUSÍ tým pustit `/pflanzer-triage`“.

**Dopad.** Metodika prodává pre-flight triage jako governance moat
(`09-srovnani` USP #3), ale tool umožňuje shipnout s `production` profilem
bez Security/Legal podpisu. Přesně scénář „production by stealth“ z
`08-edge-cases` § 8.

**Návrh.** Hard gate v ship gate: pokud `risk_profile ∈ {pilot, production}`
a kterýkoli track má `deferred`, pak `production_ready = false` s důvodem
„triage deferred: security, legal“ a SHIP.md dostane blok „Blokováno:
spusť `/pm triage <slug>`“. Decider override jen s rationale do
`decisions` (stejně jako u gate score).

### N6. Tool nemá testy ani CI — P0 (reputační)

**Důkaz.** `tool/cli/` má 17 modulů, žádný `test_*.py`, žádný `.github/`.
Jediné výskyty `pytest`/`vitest` jsou detekce nástrojů v `quality_gates.py`.

**Dopad.** Metoda prodává „7 quality gates ≥ 80/100“ a sama nemá gate 0.
První korporátní security review toolu to najde během minuty.

**Návrh.** `tests/` s pytest smoke pro `quick_session.bootstrap/prompts`,
`quality_gates` (fixture s minimálním Vite projektem), `worktree.setup`
(dry-run na lokálním bare repu), `charter.py`. GitHub Actions: ruff + mypy
+ pytest + `npm run build` frontendu. Použít vlastní `quality_gates.py`
na vlastní repo je dobrý dogfooding argument.

### N7. Quality gates a worktree podporují jen Node a Python — P1

**Situace.** Cílový segment audit-grade (banky, pojišťovny, telco) je
převážně Java/Kotlin/.NET. Gates fungují jen pro `package.json` a
`ruff/mypy/pytest`; `worktree.py` instaluje jen JS package managery.

**Důkaz.** `quality_gates.py` (`_is_node_project`, ruff/mypy/pytest větve,
žádný mvn/gradle/dotnet/go), `worktree.py` (`packageManager` detekce).

**Návrh.** Gate adaptér přes soubor v target repu
`pflanzer.gates.yml` (příkaz per gate + parser exit code/výstupu), který
`pflanzer init-target` předvyplní autodetekcí (`pom.xml`, `build.gradle`,
`*.sln`, `go.mod`). Bez adaptéru gate `unsupported`, ne `fail`. Tím metoda
přestane být implicitně „React only“.

### N8. Jeden `target_repo_url` nestačí na korporátní feature (FE + BE + API) — P1

**Situace.** Typická firemní fíčura žije ve 2–3 repozitářích. Metoda počítá
s „BE shadow agent generuje OpenAPI paralelně“, ale tool má jeden target.

**Důkaz.** `worktree.py` čte jediný `projects.target_repo_url`;
`04-session-1.md` popisuje BE shadow, ale žádný command ho nespouští v BE repu.

**Návrh.** `projects.target_repos` jako JSON `[{role: "fe", url}, {role: "be", url}]`,
worktree per repo per varianta (`pflanzer/<slug>-A` v obou), BE prompt
angle „contract-first: nejdřív OpenAPI diff, pak implementace“. Monorepo:
`--workspace apps/<app>` flag (ADR-0009 to už zmiňuje jako budoucí práci).

### N9. Non-tech stakeholder nemá jak varianty vidět mezi sessions v CC defaultu — P1

**Situace.** Default cesta (CC ve worktree) nemá hosted preview. Web hub
sbírá feedback, ale odkud vezme `prototype_url`? Metodika slibuje „3 funkční
weby, stakeholdeři je vidí ve svém prohlížeči“.

**Důkaz.** README tabulka: „Preview URL: `npm run dev` + ngrok“. `pflanzer.md`
KROK 4: „Žádná AskUserQuestion za URL — branch je deterministický“. Web hub
`variants.prototype_url` tedy zůstane prázdný nebo ruční.

**Návrh.** Dvě levné možnosti, obě do `worktree.py` / `handoff`:
1. Pokud target repo má PR preview environment (Vercel/Netlify/vlastní
   „preview per branch“), otevřít draft PR per varianta hned po Session 1;
   preview URL se zapíše do `variants`.
2. Fallback: Playwright záznam (video + screenshoty klíčových kroků z
   acceptance `.feature`) per varianta, nahraný do web hubu. Stakeholder
   hodnotí průchod scénáři, ne živou aplikaci, ale hodnotí to samé, co
   Decider zadal.

### N10. Session 1 nemá „diff walkthrough“ — stakeholdeři hlasují o UI, ne o kódu — P1

**Situace.** Track P tvrdí, že winner kód jde do prod. V agendě ale mezi
„AI vibe-coding kolo“ a „silent dot voting“ není žádný krok, kde by dev
řekl, co AI napsalo. Case study: „1 builder na 3 paralelní weby v 90 min
byl tight.“

**Návrh.** Do Lean i Full agendy povinný blok **„Diff walkthrough“ 5 min
per varianta** (dev pár ukáže `git diff --stat`, kde sáhl do existujících
komponent, co je nové, co je mock). Vote má pak dimenzi `effort` a `risk`
podloženou realitou, ne pocitem z UI. Zároveň hard rule: **builder = dev
pár, nikdy facilitátor** (ADR-0020 to říká, `/pflanzer` KROK 4 to
nevynucuje).

### N11. Chybí pravidla pro provenance AI kódu — P1

**Situace.** Korporátní governance (a AI Act čl. 14 argument metody) chce
vědět: kdo je autor AI-generovaného commitu, jak se reviewuje, jak se značí.

**Důkaz.** Metodika řeší atribuci **rozhodnutí** (decision log), ne atribuci
**kódu**. `handoff_pr.py` generuje `gh pr create`, ale žádný label/trailer.

**Návrh.** Sekce „AI code provenance“ v `07-handoff-do-vyvoje.md` + tool:
- commit trailer `Pflanzer-Variant: <slug>-A` a `AI-Assisted: claude-code`,
- PR label `ai-generated` + `pflanzer:<slug>`,
- pravidlo: **autor commitu = dev, který seděl u klávesnice**, ručí jako
  za vlastní kód; AI nikdy jako autor,
- v `INTEGRATION_GUIDE.md` řádek „licence a IP: vygenerovaný kód podléhá
  stejné code review jako lidský“.

### N12. Web hub identita je `X-User` header — P1

**Důkaz.** `tool/web/backend/main.py:31` — „v0: trust X-User header (dev only)“.
Feedback formulář v metodice vyžaduje „Hodnotitel: SSO ID, auditovatelná
atribuce, ne anonym“.

**Návrh.** `oauth2-proxy` (OIDC) před FastAPI v `tool/web/nginx/pflanzer.conf`;
backend čte `X-Forwarded-Email` a v non-dev módu bez něj vrací 401.
Jeden odstavec v README „Deploy hubu ve firmě“.

### N13. Data leakage guard je jen ústní — P1

**Situace.** L3 varování v promptu a „opakuj ho ústně“. Pre-commit secret
scan existuje v gates, ale nic nebrání vložení prod dat do CC session
(fixtures, `.env`, exporty z DB).

**Návrh.** `pflanzer init-target` zapíše do target repa `CLAUDE.md` sekci
„Pflanzer session rules: žádná prod data, syntetický seeder v
`src/test/factories.ts`, `.env*` ignorovány“ a `worktree.py setup` spustí
`gitleaks detect` + kontrolu, že `.env` není trackovaný, před tím, než tým
sedne ke klávesnici.

### N14. Repo se neučí mezi piloty — P1

**Situace.** INTEGRATION_GUIDE, prompty a acceptance kritéria vznikají per
pilot. Nic z toho se nevrací do target repa jako trvalá „AI-readiness“.

**Návrh.** První PR každého pilotu = `docs/INTEGRATION_GUIDE.md` +
`CLAUDE.md` do target repa (ne do PflanzerMethod). Druhý pilot na stejném
repu startuje z hotového kontextu. To je zároveň nejlevnější měřitelný
přínos, který sponzor vidí i když pilot skončí Kill.

### N15. Dokumentační objem brzdí adopci — P2

**Důkaz.** ~7 500 řádků metodiky + 16 ADR + 70+ research souborů. Lean
1-pager sám odkazuje na 5 dalších dokumentů.

**Návrh.** Generovat z `tool/data/role_catalog.json` **role cards** (1 strana
per roli: co přinést, co podepsat, kdy být v místnosti, na co hlasovat).
`/pm roles` je rozešle. Sponzor a Security nikdy neotevřou `04-session-1.md`,
ale kartu ano.

### N16. Cost governance CC sessions — P2

**Situace.** 3× CC paralelně bez limitu; tabulka `prompts` existuje, ale
cost se nereportuje. Korporátní EM chce vidět „session stála X“.

**Návrh.** `worktree.py` per varianta zapíše token usage z CC session logu
(pokud dostupný) do `prompts`; SHIP.md dostane řádek „AI cost“. Bez tvrdého
limitu, jen viditelnost.

### N17. Zastaralý tech stack v CLAUDE.md — P2

**Důkaz.** `CLAUDE.md:59` uvádí model `claude-sonnet-4-20250514`.

**Návrh.** Aktualizovat na aktuální Claude 5 rodinu a odkázat na
`claude-api` skill místo hardcodu.

### N18. Mezi-session okno 5–7 dní vs 48–72 h — P2 (otevřený spor)

`docs/research/code-reusability/synthesis.md` K2 zachytil konflikt
(vibe-product perspektiva: 5–7 dní = ztráta momentum). Lean recept má
„Den 6–9 async“, tj. 4 dny. Doporučuji uzavřít ADR: **Quick/Lean = 3
pracovní dny, Full = 5–7** a přestat to psát jinak v každém souboru.

---

## 3. Prioritizovaný backlog

| # | Zásah | Priorita | Effort | Kde |
|---|-------|----------|--------|-----|
| N2 | Sweep throw-away → evolve (5 míst + charter.py + FE expert lens) | P0 | 2 h | docs, commands, agents, tool |
| N1 | Tabulka „3 stupně jedné metody“, Session 3 → „Ship gate“ | P0 | 4 h | `00-lean-pflanzer.md`, README, `pm.md` |
| N3 | Ship gate autodetekuje worktree branche; skeleton jen pro throwaway | P0 | 1 PD | `pflanzer-session-3.md`, `session_3.py`, `extract.py` |
| N5 | Hard gate: deferred triage blokuje `production_ready` | P0 | 0.5 PD | `session_3.py`, `handoff_pr.py` |
| N4 | `/pm retro` + tabulka `outcomes` + doplnění case study z dat | P0 | 2 PD | nový `retro.py`, `schema.sql`, `eshop-2026.md` |
| N6 | pytest smoke + GitHub Actions | P0 | 1 PD | `tests/`, `.github/workflows/` |
| N10 | Diff walkthrough blok + builder = dev pár (hard rule) | P1 | 2 h | `04-session-1.md`, `pflanzer.md` |
| N7 | `pflanzer.gates.yml` adaptér (Java/.NET/Go) | P1 | 2 PD | `quality_gates.py`, `init.py` |
| N8 | Více target repozitářů + monorepo workspace | P1 | 2 PD | `worktree.py`, schema |
| N9 | Preview per varianta (draft PR preview / Playwright záznam) | P1 | 2 PD | `worktree.py`, web hub |
| N11 | AI code provenance (trailer, label, autor = dev) | P1 | 3 h | `07-handoff`, `handoff_pr.py` |
| N13 | Pre-session secret/prod-data scan + CLAUDE.md pravidla v target repu | P1 | 0.5 PD | `worktree.py`, `init.py` |
| N14 | První PR pilotu = INTEGRATION_GUIDE + CLAUDE.md do target repa | P1 | 0.5 PD | `init.py`, `handoff_pr.py` |
| N12 | OIDC před web hubem | P1 | 0.5 PD | `nginx/pflanzer.conf`, `main.py` |
| N15 | Role cards generované z catalogu | P2 | 1 PD | `roles.py` |
| N16 | AI cost řádek v SHIP.md | P2 | 3 h | `handoff_pr.py` |
| N18 | ADR: délka mezi-session okna per stupeň | P2 | 1 h | `docs/decisions/` |
| N17 | Model v CLAUDE.md | P2 | 5 min | `CLAUDE.md` |

**Doporučené pořadí:** N2 → N1 → N3 → N5 (konzistence, ~2 PD, bez toho
tool odporuje metodice) → N4 + N6 (měření a důvěryhodnost, ~3 PD) → P1
podle toho, jaký je další pilot (Java shop → N7 první; FE+BE repo → N8
první; non-tech sponzor → N9 první).

---

## 4. Co jsem nekontroloval a co by mělo jít do dalšího kola

- **Reálný běh toolu** proti target repu (worktree setup, gates na
  brownfield projektu). Nálezy N3/N5/N7 jsou z čtení kódu, ne z běhu.
- **Website copy** (`website/`) mimo kontrolu claimu „14 dní“; marketing
  audit už existuje v `docs/research/marketing-audit/`.
- **Track S precision spec** (`precision-spec-track-s.md.template`, 735 ř.)
  jsem nehodnotil do hloubky; Track S je deklarovaný fallback a pro otázku
  „vibe-coding uvnitř firem“ je okrajový.
- **Pilotní data.** Jediný pilot nemá doplněné výsledky. Dokud N4
  neexistuje, další kolo review bude opět jen o konzistenci.

## Reference

- `docs/methodology/00-lean-pflanzer.md`, `04-session-1.md`, `06-session-2.md`, `07-handoff-do-vyvoje.md`, `08-edge-cases-a-rizika.md`
- ADR-0005 v0.4, ADR-0009, ADR-0011 (mob), ADR-0020
- `docs/research/code-reusability/synthesis.md` (T1–T10, K2)
- `docs/research/output-consistency/03-synthesis.md` (D4, D7 — částečně neimplementované)
- `docs/case-studies/eshop-2026.md`
- `tool/cli/quick_session.py`, `quality_gates.py`, `worktree.py`, `session_3.py`, `handoff_pr.py`, `tool/db/schema.sql`, `tool/web/backend/main.py`
