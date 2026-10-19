---
description: Kickoff + Build v jednom (/pm live) — malé jádro se zástupci všech kroků cesty postaví 3 varianty a odejde s preview URL a jmény pro okna.
---

# `/pm live` — Kickoff + Build v jednom sezení

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

> **Argumenty:** `<slug>` = **první slovo** z `$ARGUMENTS` (zbytek je kontext od uživatele —
> rozhodnutí, jména, poznámky). Bez slugu: `pflanzer status`. Do příkazů dosazuj jen `<slug>`.
> **Zápisy dělá výhradně tool** (`pflanzer …`) — decision log, checkpointy ani DB nikdy needituj ručně.

Argumenty: `$ARGUMENTS` = problém v 1 větě (jinak se zeptej).

## Pro koho

Malý interní tool, kde Decider může být u Kickoffu prvních 15 min a pak
přijít až na Rozhodnutí. Jádro 3–4 lidé u jedné obrazovky, **nikdy víc než
5 naráz**. Pro větší nebo rizikovější věc dělej `/pm start` a `/pm build`
zvlášť (jiný den, Decider si vezme okno).

`/pm live` **není zkratka kolem pravidel** — jen spojuje dva command soubory.

## Postup

1. **Kickoff** — přečti `.claude/commands/pflanzer-charter.md` a proveď ho
   celý (doctor → sběr → spec zapsaný Write do
   `.pflanzer/specs/<slug>-kickoff.json` →
   `pflanzer quick_session bootstrap --spec .pflanzer/specs/<slug>-kickoff.json`;
   heredoc jen jako záloha; u každého chybějícího kroku nabídka [jméno] / [stejný
   člověk jako X] / [AI náhrada — jen kde ADR-0023 dovolí]). Krok bez jména
   a bez povolené AI náhrady = STOP. Decider je přítomen jen pro tuto část.
   Po Kickoffu rovnou napiš texty pozvánek pro okna (podle role cards) a jako další krok uveď právě jednu chybějící věc (jméno podepisujícího, zabookovaná okna, preview URL), jinak Build.
2. **Build** — přečti `.claude/commands/pflanzer-session-1.md` a proveď ho
   celý (`worktree setup` → `prompts` → 3× Claude Code → průběžné kontroly
   → checkpoint bezpečnost & právo (u AI náhrady `security-expert` +
   `pflanzer checkpoint … --ai --agent …`; u AI designu potvrdí PdM `pflanzer checkpoint --slug S design --by <PdM>`) → push → preview → zápis).
3. **Hlasování a zápis** — viz Build Krok 5; Decider ve `live` režimu
   nehlasuje (Rozhodnutí je samostatné okno).

## Časté otázky

- **Decider chce být na Buildu:** ne (anti-HiPPO, ADR-0021). Nabídni
  10min screencast z Buildu (jméno PdM) a pozvánku na Rozhodnutí s demem
  (jméno Decidera) — jména z `pflanzer status`.
- **Chybí preview URL:** navrhni konkrétního člověka (zástupce provozu
  z projektu) a termín.

## Výstup

Lidský výstup toolu a jeho Doporučení, zadání na 1 stránku, tabulka varianta /
branch / preview URL, jména (nebo AI náhrada s podepisujícím) a termíny oken.
Připomeň: bez pushe nejsou preview URL. Na konci **jeden** další krok:

> Další krok: `/pm feedback <slug>` — zástupci klikají na preview 3–5 dní.

## Co NEDĚLAT

- Nezakládej projekt jinak než přes `pflanzer quick_session bootstrap`.
- Nepřeskakuj `doctor` ani checkpoint bezpečnosti & práva.
- Žádné Sessions/Slices; terminologie Kickoff, Build, Async, Rozhodnutí, Ship.
