# 09 — Srovnání s existujícími metodami

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: pomůže obhájit volbu metody proti alternativě
> a ukáže, co Pflanzer Method převzala a co přidává. Aktuální srovnání
> s metodami AI-asistovaného vývoje 2025–2026 (AI-DLC, Spec Kit, Kiro,
> BMAD, Atlassian, Uber a další) je v
> [`../research/srovnani-metod-2026.md`](../research/srovnani-metod-2026.md);
> doporučení, co z trhu převzít, rozhodl ADR-0022. Starší detailní rešerše:
> `docs/research/competitive/`.
>
> **Brand:** „AI Design Sprint" je značka Design Sprint Academy — v dokumentaci
> ani marketingu ji nepoužívat.

## Workshopové metody (stručně)

| Metoda | Cíl a výstup | Kde selhává v korporátu | Co si Pflanzer vzala |
|--------|--------------|-------------------------|----------------------|
| **Design Sprint** (GV) | Validace otázky přes prototyp testovaný s 5 uživateli, 4–5 dní | týden seniorů nereálný; bezpečnost/provoz mimo místnost | Decider s tie-breakerem, time-boxing, „together alone" |
| **Lightning Decision Jam** | Prioritizace problémů s vlastníky, 30–60 min | mělká hloubka; HiPPO přebije hlasování; akce nikdo nerozjede | dot voting, silent ideation |
| **Lean Inception** | MVP Canvas, alignment týmu | týden bez přerušení; canvas není kód | alignment jako cíl, MVP myšlení |
| **Event Storming** | Mapa domény, bounded contexts | neřeší rozhodnutí ani produkci | stejní lidé nad stejným artefaktem, sdílený doménový jazyk |
| **Pretotyping** | Test tržní hypotézy nejmenším experimentem | tržní test, ne interní alignment | XYZ hypotéza jako falsifikovatelná metrika |
| **Liberating Structures** | 1-2-4-All, TRIZ pre-mortem | sada technik, ne metoda | silent first, pre-mortem |
| **Pflanzer Method** | 3 běžící varianty na reálném repu → rozhodnutí → PR přes gates | chybí-li ověřený problém, Decider, nebo vývojář | — |

## AI-asistované metody (stručně)

- **AWS AI-DLC** (mob elaboration/construction): nejbližší příbuzný —
  princip „AI navrhuje, lidé validují". Je homogenně inženýrský, bez
  soutěžních variant, bez formálního rozhodnutí a bez audit trail.
- **Spec Kit, Kiro, BMAD, OpenSpec:** disciplína specifikace a orchestrace
  agentů; řeší jeden kus (jak řídit agenta), ne alignment skupiny ani
  cestu do produkce. Doplňují se: Pflanzer může jejich výstupy používat
  jako vstup do Buildu.
- **Atlassian, Uber, Shopify:** adopce a prototypování uvnitř firem; cesta
  prototyp → produkce zůstává otevřená otázka. Pflanzer je nejsilnější
  právě tam.
- **Konzultantské rámce** (strategie, operating model): jiná vrstva —
  řídí portfolio, ne jednotlivý pilot. Pflanzer je opakovatelná jednotka
  pilotu, ne strategie.

## Rozhodovací strom

Použij kaskádově, první „ano" je doporučená metoda.

1. Do hodiny jen seřadit problémy s vlastníky? → **LDJ**.
2. Mapuješ komplexní doménu (legacy, bounded contexts)? → **Event
   Storming**; Pflanzer může následovat.
3. Testuješ tržní hypotézu před investicí? → **Pretotyping**.
4. Chybí strategické rámování problému? → **Foundation Sprint** (Knapp,
   Zeratsky) jako pre-krok před zadáním.
5. Nový problémový prostor bez ověřené persony, pět dní seniorů je k
   dispozici? → **Design Sprint** s předřazeným discovery.
6. Greenfield MVP s ověřeným segmentem a canvas alignmentem? → **Lean
   Inception**.
7. Čistě technický tým, žádný netechnický stakeholder, žádná compliance?
   → **AI-DLC** nebo vlastní mob.
8. Regulované (AI Act High-risk, DORA, PSD2 SCA)? → standardní SDLC, nebo
   Pflanzer s vrstvou [`governance/`](../governance/README.md).
9. Rozhodnutí blokuje víc oddělení, funkční varianta je k rozhodnutí
   potřeba, je repo, Decider s mandátem a vývojář v jádru? → **Pflanzer
   Method**.
10. Jedna drobnost na sprint? → backlog, žádný workshop.

## Co Pflanzer přidává

Žádný z jednotlivých prvků není unikát; **spojení celého cyklu** ano:

1. **Celá cesta v malé skupině** (ADR-0021): jádro 3–4 + okna zástupců
   6 kroků, max 5 naráz — místo velké místnosti nebo samotného týmu
   vývojářů.
2. **3 soutěžní varianty** téhož zadání paralelně na reálném repu
   (worktrees, ADR-0009) — rozhoduje se mezi možnostmi, ne o jedné.
3. **Rozhodnutí s anti-HiPPO protokolem:** silent voting, Decider poslední,
   Go jen s vítězem, critical na vítězi blokuje Go, Iterate max 1×,
   decision log v repu.
4. **Cesta do produkce přes automat:** gates jen na vítěze, skóre X/100,
   checkpointy, PR s AI provenance (§ AI code provenance v [`07`](07-handoff-do-vyvoje.md)).
5. **Měření outcome** (`/pm retro`): % LOC vítěze v produkci, days-to-prod,
   T+7/30/60/90. Důkazy o účinnosti metody dnes nemá nikdo, Pflanzer
   včetně; tool je začíná sbírat.
6. **Governance jako volitelná vrstva** (AI Act, DORA, Track S) bez změny
   modelu účasti.

Dříve silné argumenty — „AI viditelně generuje kód před stakeholdery",
„funkční kód místo Figmy", „AI syntéza feedbacku" — jsou dnes běžné
a diferenciací nejsou.

## Čeho se vyvarovat

Těžká specifikace před každou změnou, certifikace a role navíc, kulturní
mandáty přes hodnocení zaměstnanců (ADR-0022).
