---
description: Rozhodnutí (/pm decide, 60–90 min, Decider + jádro) — demo, top 3 spory, Go / Iterate (max 1×) / Kill, decision log do target repa.
---

# Rozhodnutí (`/pm decide`) — 60–90 min

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

> **Argumenty:** `<slug>` = **první slovo** z `$ARGUMENTS` (zbytek je kontext od uživatele —
> rozhodnutí, jména, poznámky). Bez slugu: `pflanzer status`. Do příkazů dosazuj jen `<slug>`.
> **Zápisy dělá výhradně tool** (`pflanzer …`) — decision log, checkpointy ani DB nikdy needituj ručně.


Kdo: **Decider + jádro**, max 5 lidí. Decider u stavby nebyl — začni
10min demem běžících variant na preview. Decider hlasuje **poslední**.
Zástupce bezpečnosti/provozu přizvi jen při otevřeném critical v jeho kroku.

## Krok 1 — Příprava

```bash
pflanzer session_2 prep --slug <slug>
```

Ukaž na TV: commitment index, top 3 spory (osa, hlasy per krok cesty,
návrh řešení), počet critical. Chybí feedback? Zpět na `/pm feedback`.

## Krok 2 — Critical

Každý otevřený `critical` projdi: opraveno / varianta ven / Decider
override (rationale povinné). **Dokud je critical na vítězi otevřený, Go
nejde zapsat** — tool to odmítne. Iterate je povolen (opraví ho).

## Krok 3 — Spory a hlasování

Top 3 spory: AI navrhuje řešení, nerozhoduje. Neznámý spor rozhodne
Decider s rationale.

**Rady pro silent voting:** každý napíše volbu sám a najednou (karty /
chat v jednom okamžiku), nikdo ji dřív neříká nahlas; důvod jednou větou;
jádro hlasuje o tom, co uvidí uživatel; **Decider odkryje svou volbu poslední**
a když se liší od většiny, řekne proč. Až potom diskuse.

## Krok 4 — Rozhodnutí

AskUserQuestion Decideru: **Go / Iterate / Kill** + rationale (1–2 věty,
povinné). Při Go vyber vítěze.

**Dobrý rationale má tři části:** (1) **proč** tahle varianta / rozhodnutí,
(2) **co vědomě nechceme** (co jsme z poražených variant nebo ze scope
odložili), (3) **kdo hlídá riziko** (jméno a co přesně sleduje). Má mu
rozumět někdo, kdo v místnosti nebyl. Špatně: „A je lepší.“ Dobře: „A, protože
splní metodu bez změny API; nechceme zatím B-ův report; riziko ceny hlídá
Petra přes týdenní dashboard.“

```bash
pflanzer session_2 decide --slug <slug> go --winner A --rationale "<1–2 věty>"   # u mob mode: --winner mob
pflanzer session_2 decide --slug <slug> go --winner A --rationale "…" --override-critical "<důvod>"
pflanzer session_2 decide --slug <slug> iterate --variants A,B --rationale "…" --iterate-focus "<co změnit>"   # max 1×
pflanzer session_2 decide --slug <slug> kill --rationale "…"
# critical vyřešen jinak než overridem (--by a --note jsou povinné):
pflanzer session_2 resolve --slug <slug> --feedback-id <id> --by "<kdo>" --note "<jak>"
# druhé rozhodnutí po Go jen výslovně:
pflanzer session_2 decide --slug <slug> go --winner B --rationale "…" --force
```

- **Mob mode** (jedna společná varianta `mob`): není co porovnávat, `prep` to řekne
  lidsky; Decider rozhoduje jen Go (`--winner mob`) / Iterate / Kill. `--winner`
  bere skutečné varianty projektu z Buildu, ne natvrdo A/B/C.
- **Iterate**: AskUserQuestion se vždy ptá, **které varianty jdou do druhého kola**
  (`--variants A,B`; tool ověří, že existují). Ostatní skončí; status i hub
  ukazují jen varianty ve hře, vypadlé jen jako informace. Bez `--variants`
  platí shortlist z hlasování Buildu.
- **Iterate** = jedno další Build kolo (max 1×). Druhý Iterate tool
  odmítne — problém je špatně zadaný, zpět na Kickoff.
- Decider nemůže rozhodnout → eskalace dle ADR-0001.
- Tool zapíše **decision log do target repa** `.pflanzer/decisions/<slug>.md`
  — **commitni ho** (kdo, kdy, co, proč zůstane v gitu).

## Krok 5 — Výstup a další krok

Ukaž lidský výstup toolu a předej jeho **Doporučení**. Rozhodnutí +
rationale, vítěz, počet critical, cesta k decision logu.

**Poděkuj poraženým variantám nahlas** (jméno autora a co dobrého přinesly);
jejich nápady jdou do parking lotu, ne do koše. Ať vývojáři nesmažou větve
dřív, než PR vítěze projde.

**Jeden** další krok:

- Go → `/pm ship <slug>` — vývojáři + provoz (checkpoint 20 min)
- Iterate → `/pm build <slug>` — jádro, jen to, co se mění
- Kill → tool vypíše i **úklid** (zastavit náhled s heslem
  `pflanzer preview down --slug <slug>`, smazat worktrees přes `git worktree remove`);
  projdi ho s vývojářem. Poděkuj týmu nahlas a veď k poučením:
  `pflanzer retro lesson --slug <slug> --text "<poučení>"` (1–3 poučení,
  jedna věta každé); pak hotovo

## Co NEDĚLAT

- Nepřebíjej Decidera; nezapomeň rationale (audit).
- Nedovol druhý Iterate; druhé `decide` po Go jen s `--force` a `--rationale`.
- Nezapomeň commitnout decision log.

## Reference

- `docs/methodology/06-session-2.md`, `docs/decisions/0001-decider-model.md`
