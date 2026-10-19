"""Human-facing output for every `pflanzer` command.

One shape everywhere: brand line → what happened (1–6 lines) → ONE next step
→ 1–3 recommendations for the people doing it. JSON stays available via
`--json` for Claude Code commands and scripts.

    from tool.cli.ux import emit, tips_for
    emit(out, title="Kickoff hotový", lines=[...], next_step="/pm build <slug>",
         tips=tips_for("kickoff", ctx), as_json=args.json)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

# Doporučení pro lidi podle fáze. Krátké, praktické, bez žargonu.
# Klíč = fáze; hodnota = seznam (podmínka, text). Podmínka je klíč v ctx,
# který musí být truthy (None = vždy).
TIPS: dict[str, list[tuple[str | None, str]]] = {
    "init": [
        (None, "INTEGRATION_GUIDE nemusíte psát ručně: vývojář v Claude Code napíše "
               "„vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“ a výsledek zkontroluje (5 min)."),
        (None, "Commitněte a pushněte vše najednou: `git add -A docs .pflanzer tests .gitignore`."),
    ],
    "doctor": [
        ("no_preview", "Bez preview URL zástupci v Asyncu nemají na co klikat — domluvte "
                       "s provozem sdílení dřív než Kickoff (viz docs/postup.md)."),
        ("no_ci", "Bez CI půjde PR ze Ship bez automatických kontrol; stačí lint + test + build."),
    ],
    "kickoff": [
        ("metric_weak", "Metrika zatím nemá číslo nebo termín. Dobrá: „10 z 15 obchodníků otevře "
                        "přehled aspoň 3× týdně do 30 dnů“. „Budou to používat“ nestačí."),
        ("kill_weak", "Kill kritérium potřebuje číslo: „po 4 týdnech otevře přehled méně než 5 "
                      "z 15 lidí → končíme“. Bez čísla se Kill nikdy neřekne."),
        ("ai_design", "Bez designéra: AI připraví návrh a kontrolu přístupnosti, ale vzhled "
                      "před Ship potvrdí PdM — domluvte, kdo se na varianty podívá."),
        ("ai_stand_ins", "Kroky s AI náhradou podepisuje člověk (ADR-0023) — "
                         "domluvte, kdo to bude, ještě dnes."),
        (None, "Dobrá metrika = číslo + termín: „10 z 15 obchodníků otevře přehled aspoň "
               "3× týdně do 30 dnů“. „Budou to používat“ nestačí."),
        (None, "Decider musí umět říct i Kill. Kdo nemůže zastavit, není Decider."),
        (None, "Zabookujte všechna okna teď (Build, checkpointy, Rozhodnutí) — "
               "ad hoc termíny pilot zabijí."),
    ],
    "build": [
        (None, "U klávesnice sedí vývojář, ostatní navigují. Max 5 lidí u obrazovky."),
        (None, "Pošlete bezpečnosti předem 3 věty: co aplikace čte, kam píše, "
               "jestli vidí reálná data. Checkpoint pak trvá 20 minut, ne hodinu."),
        ("ai_design", "Design dělá AI: nechte ji zkontrolovat kontrasty a ovládání z klávesnice "
                      "a výsledek ukažte PdM ještě před Rozhodnutím."),
        (None, "Hlasujte za to, co uvidí uživatel, ne za kód. Důvod jednou větou."),
    ],
    "async": [
        (None, "Dobrý feedback: co jsem zkoušel → co se stalo → co jsem čekal → co navrhuji. "
               "Jeden feedback = jeden problém."),
        (None, "Critical jen pro to, co se nesmí nasadit (právo, bezpečnost, data, rozbitý "
               "hlavní tok) — vždy s důvodem."),
        ("silent_reps", "Kdo z oken ještě nic nenapsal, dostane připomínku: mlčení "
                        "nevetovací role po termínu = souhlas, u bezpečnosti ne."),
    ],
    "veto": [
        (None, "Veto = jedna věta: co přesně nejde nasadit a co ho zruší („Nejde, dokud "
               "export neanonymizuje e-maily. Zrušíme, když to ukážete v demu.“)."),
    ],
    "checkpoint_bezpecnost": [
        (None, "Předávání bezpečnosti ve 3 větách: co aplikace čte, kam zapisuje, jestli "
               "vidí reálná data. Víc nepotřebuje — zbytek se doptá v okně."),
        ("blocked", "Blokace je dobrá zpráva, pokud je konkrétní. Napište, co přesně se má "
                    "změnit — kdo odblokuje, uvidí přesný příkaz v dalším kroku."),
    ],
    "checkpoint_provoz": [
        (None, "Provoz si vezme 4 věci: jak se vrátit zpět (rollback), kdo má on-call, co "
               "kontrolovat první hodinu po nasazení a jak funkci vypnout (feature flag)."),
        ("blocked", "Doplňte chybějící z těch čtyř věcí (rollback, on-call, první hodina, "
                    "flag) a okno podepište znovu — zabere to 10 minut."),
    ],
    "ai_stand_in": [
        (None, "AI připraví podklad, podepisuje člověk. Domluvte jméno teď, ne až Ship "
               "stojí: bez podpisu člověka pilot nepůjde."),
        (None, "AI náhrada je dočasná — pro další projekt tým sežene člověka (ADR-0023)."),
    ],
    "decide": [
        (None, "Začněte 10min demem běžících variant — Decider je viděl jen v Asyncu."),
        (None, "Tiché hlasování: všichni napíší volbu najednou, Decider odkryje svou poslední."),
        ("veto", "Veto zapište jednou větou: co přesně nejde nasadit a co ho zruší."),
        ("open_critical", "Critical na jiné variantě než vítězné Go neblokuje — řešte jen ty "
                          "na vítězi (opravit, nebo vědomě přebít s důvodem)."),
        (None, "Rationale pište tak, aby mu za půl roku rozuměl někdo, kdo nebyl v místnosti."),
    ],
    "iterate": [
        (None, "Iterate = jedno kolo navíc a jen na to, co se mění. Druhé Iterate není — "
               "pak je problém špatně zadaný."),
    ],
    "ship": [
        ("missing_signatures", "Před Ship chybí podpisy oken — bez nich pilot nepůjde. "
                               "Každé okno je 20 minut, domluvte je dnes."),
        (None, "Checkpoint provozu: rollback, on-call, první hodina po nasazení a feature "
               "flag. 20 minut."),
        ("below_threshold", "Pod prahem: nejdřív opravte tests/build; Ship i přesto jen "
                            "vědomě s `--override-threshold` a důvodem od Decidera."),
        (None, "Poraženým variantám poděkujte nahlas — jejich nápady jdou do parking lotu, ne do koše."),
    ],
    "handoff": [
        (None, "Za 30 dní `/pm retro`: kolik kódu vítěze přežilo, metrika vs. cíl, incidenty."),
        (None, "Sdílejte SHIP.md s celým týmem — je to jedna stránka, ne audit."),
    ],
    "status": [
        ("blocked", "Blokace nikdo nevyřeší sám od sebe: napište konkrétnímu člověku "
                    "z kroku cesty ještě dnes."),
        ("ai_pending", "AI draft není podpis. Člověk ho přečte, upraví a podepíše "
                       "(20 minut), jinak Ship zůstane zablokovaný."),
        ("open_critical", "Critical = nesmí se nasadit. Buď se opraví, nebo ho Decider "
                          "vědomě přebije s důvodem."),
        (None, "Stav projektu zkontrolujte vždy před schůzkou: `pflanzer status`."),
    ],
    "retro": [
        (None, "Retro do 30 minut: co bychom příště udělali jinak, a jedno rozhodnutí pro další pilot."),
    ],
}


# ---------------------------------------------------------------------------
# Závažnost: uživatel píše critical|major|minor (aliasy high/medium/low),
# DB drží critical|high|medium|low, zobrazuje se česky.
# ---------------------------------------------------------------------------

SEVERITY_LABELS = {"critical": "Kritické", "high": "Vysoké", "medium": "Střední", "low": "Nízké"}
_SEVERITY_ALIASES = {"critical": "critical", "major": "high", "high": "high",
                     "medium": "medium", "minor": "low", "low": "low"}


def normalize_severity(value: str) -> str:
    """User input (critical|major|minor|high|medium|low) → DB value."""
    key = (value or "").strip().lower()
    if key not in _SEVERITY_ALIASES:
        raise ValueError(
            f"Neznámá závažnost „{value}“. Použij critical, major nebo minor "
            "(případně high, medium, low)."
        )
    return _SEVERITY_ALIASES[key]


def severity_label(db_value: str) -> str:
    """DB value → česky (Kritické / Vysoké / Střední / Nízké)."""
    return SEVERITY_LABELS.get(db_value, db_value)


# ---------------------------------------------------------------------------
# Vstup a chyby
# ---------------------------------------------------------------------------


def read_spec(arg: str | Path, *, example: str = "") -> dict[str, Any]:
    """Read a JSON spec from a file, or from stdin when `arg` is `-`.

    Raises ValueError with a human sentence (and `example`) on bad input.
    """
    if str(arg) == "-":
        raw = sys.stdin.read()
        origin = "ze standardního vstupu"
    else:
        path = Path(arg)
        if not path.is_file():
            raise ValueError(f"Soubor se specem {path} neexistuje. "
                             "Spec můžeš poslat i přes stdin: --spec - <<'EOF' … EOF")
        raw = path.read_text(encoding="utf-8")
        origin = f"ze souboru {path}"
    if not raw.strip():
        raise ValueError(f"Spec {origin} je prázdný." + (f"\nPříklad:\n{example}" if example else ""))
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Spec {origin} není platný JSON ({exc.msg}, řádek {exc.lineno}, "
                         f"sloupec {exc.colno})." + (f"\nPříklad:\n{example}" if example else "")) from exc
    if not isinstance(data, dict):
        raise ValueError(f"Spec {origin} musí být JSON objekt {{…}}."
                         + (f"\nPříklad:\n{example}" if example else ""))
    return data


def die(message: str, example: str = "") -> None:
    """Human error to stderr + exit 2 (never a traceback)."""
    sys.stderr.write(f"{BRAND_LINE}\n\nCHYBA: {message}\n")
    if example and example not in message:
        sys.stderr.write(f"\nPříklad správného použití:\n{example}\n")
    sys.exit(2)


def tips_for(phase: str, ctx: dict[str, Any] | None = None, limit: int = 3) -> list[str]:
    """Recommendations for `phase`, filtered by truthy keys in `ctx`."""
    ctx = ctx or {}
    picked = [text for cond, text in TIPS.get(phase, []) if cond is None or ctx.get(cond)]
    # Conditional tips are more specific → put them first.
    conditional = [t for c, t in TIPS.get(phase, []) if c and ctx.get(c)]
    ordered = conditional + [t for t in picked if t not in conditional]
    return ordered[:limit]


def render(title: str, lines: list[str] | None = None, next_step: str | None = None,
           tips: list[str] | None = None, warnings: list[str] | None = None) -> str:
    out = [BRAND_LINE, "", f"## {title}", ""]
    for line in lines or []:
        out.append(f"- {line}")
    if warnings:
        out += ["", *[f"⚠ {w}" for w in warnings]]
    if next_step:
        out += ["", f"**Další krok:** {next_step}"]
    if tips:
        out += ["", "**Doporučení:**", *[f"- {t}" for t in tips]]
    return "\n".join(out) + "\n"


def emit(data: Any, *, title: str, lines: list[str] | None = None,
         next_step: str | None = None, tips: list[str] | None = None,
         warnings: list[str] | None = None, as_json: bool = False) -> None:
    """Print JSON (for tools) or the human view (default)."""
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        return
    sys.stdout.write(render(title, lines, next_step, tips, warnings))
