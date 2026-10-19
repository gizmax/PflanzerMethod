Pflanzer Method | pflanzer.cz/method

# AI náklady — viditelnost tokenů Claude Code (`ai_usage.py`)

**Co se měří.** Claude Code ukládá transkript každé session do `~/.claude/projects/<cesta-worktree>/*.jsonl` (subagenti v `<session>/subagents/`; `CLAUDE_CONFIG_DIR` přesměruje `~/.claude`). `tool/cli/ai_usage.py` projde worktrees všech variant a repozitářů projektu (`<targets>/<slug>-<X>`, `<slug>-<X>-<role>`) a sečte `usage` z odpovědí modelu: input, output, cache write, cache read — per varianta a model, jednou za `message.id`.

**Jen viditelnost.** Žádný limit ani gate. Počítá se jen tento stroj — jiné notebooky, CI a hosted buildery (v0, Lovable, Bolt …) v číslech nejsou. Session spuštěná v podadresáři worktree se nezapočítá.

```bash
python3 tool/cli/ai_usage.py --slug <slug>            # tabulka varianty × tokeny
python3 tool/cli/ai_usage.py --slug <slug> --json
python3 tool/cli/ai_usage.py --slug <slug> --record   # snapshot do DB tabulky ai_usage
```

`--record` přepíše předchozí snapshot stejné varianty a modelu. SHIP.md (`handoff_pr.py`) měří živě; když na stroji logy nejsou, použije poslední snapshot z DB.

**Cena (volitelně).** Ceny se mění, proto nejsou v kódu. Zkopíruj `tool/templates/pflanzer.prices.json.template` do kořene PflanzerMethod repa jako `pflanzer.prices.json` (je v `.gitignore`), nebo nastav `PFLANZER_AI_PRICES=<cesta>`. Vyplň USD za 1M tokenů (`input`, `output`, `cache_write`, `cache_read`) podle aktuálního ceníku nebo vaší smlouvy. Klíč je prefix model ID (nejdelší prefix vyhrává). Hodnota `null` = model bez ceny. Bez ceníku SHIP.md ukáže jen tokeny.

Odhad je orientační: nepočítá slevy, batch ani rozdílné ceny 5min/1h cache zápisu.
