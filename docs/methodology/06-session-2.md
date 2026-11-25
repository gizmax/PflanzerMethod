# 06 — Rozhodnutí

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: jak vést Rozhodnutí (`/pm decide`) — agenda,
> top 3 spory, silent voting, rozhodnutí Decidera Go / Iterate / Kill a co
> když Decider nerozhodne. Je to rozhodovací setkání, ne generativní: žádné
> nové varianty. Délka je ve všech stupních stejná (60–90 min); Full smí
> využít širší agendu (viz konec). Stupně: [`00-lean-pflanzer.md`](00-lean-pflanzer.md).

## Cíl

Z agregovaného feedbacku, běžících variant a diffu udělat **jedno
rozhodnutí s rationale**: Go s vítězem, Iterate (max 1×), nebo Kill.
Zapíše se do decision logu v target repu (`.pflanzer/decisions/<slug>.md`,
**commitni**). Po Go následuje Ship, ne další setkání. Pokud skupina chce
další varianty, je to signál špatného zadání: vrať se ke Kickoffu.

## Kdo

**Decider + jádro**, max 5 lidí. Decider u Buildu nebyl, proto začíná
demo. Zástupce bezpečnosti & práva nebo provozu přizvi jen při otevřeném
Kritickém v jejich kroku. **Bez Decidera Rozhodnutí neprobíhá** (ADR-0001).

## Agenda (60–90 min)

| Čas | Blok | Poznámka |
|-----|------|----------|
| 0–10 | **Demo** běžících variant na preview | Decider je vidí poprvé „naostro"; vývojářský pár řekne reuse/nové/mock |
| 10–20 | **Tiché hlasování jádra** | nad vlastní zkušeností z Asyncu, **dřív než kdokoli uvidí AI souhrn**; výsledek se zatím nezveřejní (ADR-0026) |
| 20–35 | **Agregovaný feedback** | `pflanzer decide prep`: ke každé variantě nejsilnější argument pro a proti ve stejném rozsahu, v pořadí A, B, C; commitment index, počet Kritických, verdikt debtu, mlčící role (zapsané jako „no objection"). **AI nedoporučuje vítěze a varianty neřadí** |
| 35–50 | **Kritické** | každé otevřené Kritické: opraveno / varianta ven / Decider override s rationale |
| 50–75 | **Top 3 spory** | 5 min kontext → 5 min návrh řešení → 5 min hlasování → zápis nebo eskalace; kdo po sporech mění hlas, řekne to nahlas a zapíše se to |
| 75–90 | **Rozhodnutí Decidera** | zveřejní se výsledek hlasování, **Decider hlasuje poslední**: Go / Iterate / Kill + rationale (1–2 věty, povinné) a jedna věta k AI vstupu |

Proč hlasování před souhrnem: odborníci jdou za sklonem AI, aniž si toho
všimnou ([`../research/vylepseni-2026-11.md`](../research/vylepseni-2026-11.md) § 2).
Tiché hlasování chrání před vlivem nejvýše postaveného člověka, pořadí
bloků před vlivem AI. **Druhé tiché kolo po sporech má jen stupeň Full.**

Příkazy:

```bash
pflanzer decide prep --slug <slug>
pflanzer decide --slug <slug> go --winner A --rationale "…" \
    --ai-deviation "kde se Decider od AI vstupu odchýlil, nebo proč souhlasí"
pflanzer decide --slug <slug> iterate --rationale "…" --iterate-focus "…"
pflanzer decide --slug <slug> kill --rationale "…"
pflanzer decide resolve --slug <slug> --feedback-id <id> --by "<jméno>" --note "<jak>"
```

## Pravidla rozhodnutí

- **Go vyžaduje vítěze** (`--winner`). Poražené varianty se smažou po
  mergi.
- **Otevřené Kritické (`critical`) na vítězi blokuje Go** — tool jej odmítne zapsat.
  Cesty: vyřešit (`resolve`), nebo Decider override s rationale
  (`--override-critical`). Iterate je povolen (opraví ho).
- **Iterate = jedno další kolo Buildu, max 1×** s úzce definovaným
  zaměřením (`--iterate-focus`). Druhý Iterate tool odmítne: třetí kolo
  znamená špatně zadaný problém, zpět ke Kickoffu.
- **Kill** má rationale a stručné retro do decision logu.
- **Decider hlasuje poslední.** Přebije-li výsledek tiché hlasování, dělá to
  **veřejně s rationale do decision logu** (ADR-0001). Kritické od
  bezpečnosti/práva se hlasem přebít nedá, jen mitigací nebo pivotem.
- **AI vstup v decision logu** (ADR-0026): zápis uvádí, co do Rozhodnutí
  dodala AI (souhrn, draft konvergence, zastoupená role), a jednou větou,
  kde se Decider odchýlil nebo proč souhlasí. AI není podpis ani
  doporučení (ADR-0023).
- **Mlčení:** nevetovací role = „no objection"; vetovací role bez
  vyjádření = Rozhodnutí je jen review (ADR-0017).

## Top 3 spory

`decide prep` vybere tři nejostřejší osy (typicky mezi kroky cesty).
AI navrhuje řešení, nerozhoduje; neznámý spor rozhodne Decider
s rationale. Opakující se vzorce:

| Spor | Vzorec řešení |
|------|---------------|
| bezpečnost/právo vs tlak byznysu | critical = pivot nebo mitigace; reálná PII = okamžitý stop |
| vývoj/provoz vs termín | T-shirt odhad, ne story pointy; > L = 2denní spike mimo setkání; přetrvávající spor eskalovat mimo místnost |
| PdM vs design | scope rozhoduje PdM, flow design; persona je sdílený artefakt |
| FE vs BE kontrakt | contract-first, OpenAPI diff, breaking-change registr s vlastníkem |
| „už to skoro běží, pošleme to zákazníkovi" | vítěz jde do produkce **přes Ship**; sdílení preview před gates je incident ([`08`](08-edge-cases-a-rizika.md) § 8) |

**Hierarchie závaznosti:** Kritické = blocker (STRIDE Critical, AI Act
High-risk bez DPIA, WCAG Critical/Serious na veřejném rozhraní, breaking
change bez konzumentů) · varianta s varováním = viditelné v decision logu,
bez veta · skóre = váha pro zbytek (AI-only max 0,5).

## Když Decider nerozhodne

Autoritativní zdroj je **ADR-0001** (kanonický eskalační protokol); sem se
text nekopíruje. Pro orientaci:

- **Decider chybí:** Rozhodnutí se odkládá (max 5 pracovních dní), pak
  eskalace na sponzora; mlčení sponzora = Kill.
- **„Potřebuji víc času":** písemné rozhodnutí do decision logu do 48 h,
  pak eskalace; mlčení vede k Iterate, ne k tichému úmrtí.
- **Iterate vyčerpán:** další Rozhodnutí musí skončit Go nebo Kill, jinak
  automaticky Kill.

Eskalační kontakt a případný záložní Decider se zapisují v Kickoffu.

## Výstup

- Rozhodnutí + rationale, vítěz, počet a stav Kritických, decision log
  v repu (commit).
- Go → `/pm ship <slug>` ([`07`](07-handoff-do-vyvoje.md)) — vývojáři +
  provoz; Iterate → `/pm build <slug>` (jen to, co se mění); Kill → hotovo.

## Full — širší agenda

Ve stupni Full může Rozhodnutí využít až 3 h: delší agregace per role
(heatmapa skóre, severity), konvergence na vítěze s návrhy zapracování
(AI první draft vzniká až po prvním tichém hlasování; panel reaguje,
nepřekresluje; pak druhé tiché kolo, rozdíl kol je vidět v zápisu), a nakonec **podpis DPO
(AI Act Fáze C)** s data flow diagramem, intended use, human oversight
a Annex IV kostrou ([`03`](03-pre-session-priprava.md) § Legal & Privacy
Triage). Go-kritéria navíc: commitment index nad prahem zadání, nula
critical, debt ≤ 6, WCAG Critical/Serious zmírněné, kapacita potvrzená EM.
Každá kritická role potvrzuje commitment aspoň 2 ze 3 (0 nesouhlas ·
1 čtu · 2 reviewuji · 3 spolutvořím); 0 = automaticky Iterate. Eskalační
cesty: kapacita → sponzor + vedení vývoje, bezpečnost/právo → CISO + DPO,
spor mezi jednotkami → vedení.
