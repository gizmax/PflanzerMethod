---
description: Kickoff + Build v jednom (/pm live) — malé jádro se zástupci všech kroků cesty postaví 3 varianty a odejde s preview URL a jmény pro okna.
---

# `/pm live` — Kickoff + Build v jednom sezení

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

Argumenty: `$ARGUMENTS` = problém v 1 větě (jinak se zeptej).

## Pro koho

Malý interní tool, kde Decider může být u Kickoffu prvních 15 min a pak
přijít až na Rozhodnutí. Jádro 3–4 lidé u jedné obrazovky, **nikdy víc než
5 naráz**. Pro větší nebo rizikovější věc dělej `/pm start` a `/pm build`
zvlášť (jiný den, Decider si vezme okno).

`/pm live` **není zkratka kolem pravidel** — jen spojuje dva command soubory.

## Postup

1. **Kickoff** — přečti `.claude/commands/pflanzer-charter.md` a proveď ho
   celý (doctor → sběr → `pflanzer quick_session bootstrap --spec`). Krok
   bez jména = STOP. Decider je přítomen jen pro tuto část.
2. **Build** — přečti `.claude/commands/pflanzer-session-1.md` a proveď ho
   celý (`worktree setup` → `prompts` → 3× Claude Code → průběžné kontroly
   → checkpoint bezpečnost & právo → push → preview → zápis).
3. **Hlasování a zápis** — viz Build Krok 5; Decider ve `live` režimu
   nehlasuje (Rozhodnutí je samostatné okno).

## Výstup

Zadání na 1 stránku, tabulka varianta / branch / preview URL, jména a termíny
oken. Na konci **jeden** další krok:

> Další krok: `/pm feedback <slug>` — zástupci klikají na preview 3–5 dní.

## Co NEDĚLAT

- Nezakládej projekt jinak než přes `pflanzer quick_session bootstrap`.
- Nepřeskakuj `doctor` ani checkpoint bezpečnosti & práva.
- Žádné Sessions/Slices; terminologie Kickoff, Build, Async, Rozhodnutí, Ship.
