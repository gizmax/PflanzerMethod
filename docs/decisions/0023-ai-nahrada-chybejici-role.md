# ADR-0023 — AI náhrada chybějícího zástupce kroku cesty

**Pflanzer Method | pflanzer.cz/method**

**Status:** Accepted · 2026-10-19
**Související:** ADR-0021 (malá skupina, celá cesta), `02-role-catalog.md`
§ AI proxy vs lidský zástupce, ADR-0001 (Decider), ADR-0020 (Track P)

## Kontext

ADR-0021 říká: krok cesty bez jména = Kickoff se nesvolává. V praxi firma
často nemá designéra, security je přetížená a provoz odpoví za dva týdny.
Striktní pravidlo pak metodu zablokuje dřív, než začne; volné pravidlo
(„AI to zastoupí") vrací přesně tu mezeru, kterou v0.5 zavírala: rychlý kód,
který nikdo nepodepsal.

Role catalog už má princip **„AI nikdy není podpis"** a 3 režimy AI proxy.
Chybí převod na kroky cesty a na podpis oken.

## Rozhodnutí

Krok cesty smí mít místo jména **`AI`** — ale jen podle tabulky. AI
**připraví** (perspektivu, kontrolu, draft checkpointu), **člověk podepisuje**.

| Krok cesty | AI náhrada | Kdo podepíše místo chybějícího člověka |
|------------|-----------|-----------------------------------------|
| Byznys (Decider) | **nikdy** | — bez Decidera se Kickoff nesvolává |
| Vývoj | **nikdy** | — u klávesnice sedí vývojář (Track P) |
| Produkt | jen stupeň Quick / throwaway | Decider (scope) |
| Design | ano (UX expert + a11y gates) | PdM; u production customer-facing je potřeba člověk |
| Bezpečnost & právo | jen **AI pre-check** | throwaway: stačí AI; pilot/production: člověk do 48 h, jinak Ship blokuje |
| Provoz | jen **AI pre-check** | throwaway: AI; pilot: vývojář z jádra (vývoj + provoz); production: člověk z provozu |

Pravidla:

1. **AI náhrada je vidět.** Charter, `pflanzer status`, decision log a SHIP.md
   ji uvádí výslovně („Design: AI (ux-expert), podepisuje PdM").
2. **AI checkpoint = draft.** `pflanzer checkpoint … --ai` zapíše návrh;
   pro pilot/production zůstává okno „čeká na podpis člověka" a Ship
   blokuje, dokud ho člověk nepotvrdí (`--by <jméno>`), nebo Decider vědomě
   nepřebije (`--override-triage --rationale`).
3. **AI feedback má váhu max 0,5** (beze změny) a AI nikdy nehlasuje.
4. **Jen na chvíli.** AI náhrada je pro pilot; pro další projekt téhož týmu
   `status` připomene sehnat člověka.

## Důsledky

- Metoda nezamrzne na chybějícím designérovi nebo vytížené security, ale
  produkční riziko dál podepisuje člověk.
- Stejný mechanismus jako checkpointy (ADR-0021) — žádný nový proces.
- Riziko: tým začne AI náhradu používat jako výchozí. Mitigace: viditelnost
  (bod 1) a připomínka (bod 4); metrika „podíl kroků s AI náhradou" v retru.
