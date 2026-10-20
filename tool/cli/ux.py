"""Human-facing output for every `pflanzer` command.

One shape everywhere: brand line → what happened (1–6 lines) → ONE next step
→ 1–3 recommendations for the people doing it. JSON stays available via
`--json` for Claude Code commands and scripts.

    from tool.cli.ux import emit, tips_for
    emit(out, title="Kickoff hotový", lines=[...], next_step="/pm build <slug>",
         tips=tips_for("kickoff", ctx), as_json=args.json)
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any, NoReturn

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

# Doporučení pro lidi podle fáze. Krátké, praktické, bez žargonu.
# Klíč = fáze; hodnota = seznam (podmínka, text). Podmínka je klíč v ctx,
# který musí být truthy (None = vždy).
TIPS: dict[str, list[tuple[str | None, str]]] = {
    "init": [
        (None, "INTEGRATION_GUIDE nemusíte psát ručně: vývojář v Claude Code napíše "
               "„vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“ a výsledek zkontroluje (5 min)."),
        (None, "Commitněte a pushněte vše najednou, než spustíte Kickoff (worktrees se klonují "
               "z originu)."),
    ],
    # Doctor: ⚠ řádky tabulky už říkají, co chybí (CI, preview) — tip to nesmí opakovat.
    "doctor": [],
    "kickoff": [
        ("metric_weak", "Metrika zatím nemá číslo nebo termín. Dobrá: „10 z 15 obchodníků otevře "
                        "přehled aspoň 3× týdně do 30 dnů“. „Budou to používat“ nestačí."),
        ("kill_weak", "Kill kritérium potřebuje číslo: „po 4 týdnech otevře přehled méně než 5 "
                      "z 15 lidí → končíme“. Bez čísla se Kill nikdy neřekne."),
        ("ai_design", "Bez designéra: AI připraví návrh a kontrolu přístupnosti, ale vzhled "
                      "potvrdí PdM před Rozhodnutím (`pflanzer checkpoint … design`; u pilotu Ship "
                      "neblokuje, u production ano) — domluvte, "
                      "kdo se na varianty podívá."),
        ("ai_stand_ins", "Kroky s AI náhradou podepisuje člověk (ADR-0023) — "
                         "domluvte, kdo to bude, ještě dnes."),
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
    ],
    "after_setup": [
        (None, "Každá varianta má jiný úhel — nemíchejte je."),
    ],
    "after_vote": [
        ("multi_variants", "Pošlete zástupcům odkazy na všechny varianty a termín Asyncu, ne víc."),
        ("single_variant", "Pošlete zástupcům odkaz na společnou variantu a termín Asyncu, ne víc."),
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
    "checkpoint_design": [
        (None, "Design za AI potvrzuje člověk, který varianty viděl: projděte hlavní tok "
               "a kontrasty a napište do poznámky, co jste skutečně zkontrolovali."),
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
    ],
    "after_go": [
        (None, "Rationale ukažte týmu do hodiny; critical na poražených zapište do parking "
               "lotu nebo vědomě zavřete."),
        (None, "Poraženým variantám poděkujte nahlas — jejich nápady jdou do parking lotu, "
               "ne do koše."),
    ],
    "after_critical": [
        (None, "Autor + vývojář: oprav ve vítězné variantě, pak `pflanzer session_2 resolve …`; "
               "nebo Decider vědomě přebije `--override-critical`."),
    ],
    "after_resolve": [
        (None, "Na vítězi žádný critical nezbývá → decide go."),
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
    ],
    "after_ship": [
        (None, "PR nech zkontrolovat člověkem, který u Buildu nebyl."),
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
    ],
    "after_kill": [
        (None, "Kill je dobrý výsledek — ušetřil Ship. Zapište 1–3 poučení (co jsme se "
               "dozvěděli o problému, o uživatelích, o zadání)."),
        (None, "Poděkujte týmu nahlas; varianty si nechte jako reference."),
        (None, "Další pilot: vezměte poučení do zadání nového Kickoffu."),
    ],
    "retro": [
        (None, "Retro do 30 minut: co bychom příště udělali jinak, a jedno rozhodnutí pro další pilot."),
    ],
}


def plural(n: int, one: str, few: str, many: str) -> str:
    """Czech noun agreement including the number: `plural(3, "den", "dny", "dnů")` -> "3 dny".

    1 -> `one`, 2-4 -> `few`, 0 and 5+ -> `many` (fractions/negatives use `many`).
    """
    try:
        k = int(n)
    except (TypeError, ValueError):
        return f"{n} {many}"
    if k != n:
        return f"{n} {many}"
    a = abs(k)
    form = one if a == 1 else few if 2 <= a <= 4 else many
    return f"{k} {form}"


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
                             "Zapiš JSON do souboru (nástrojem Write, např. "
                             ".pflanzer/specs/<slug>-kickoff.json) a zadej jeho cestu: --spec cesta.json")
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


def did_you_mean(word: str, choices: Any) -> str | None:
    """Closest match of `word` among `choices` (typo help), or None."""
    opts = [str(c) for c in choices]
    hit = difflib.get_close_matches(str(word), opts, n=1, cutoff=0.6)
    return hit[0] if hit else None


def project_not_found_message(slug: str) -> str:
    """Czech "no such project" sentence with did-you-mean and existing slugs."""
    slugs: list[str] = []
    try:
        from tool.cli.db import transaction
        with transaction() as conn:
            slugs = [r[0] for r in conn.execute("SELECT slug FROM projects ORDER BY slug").fetchall()]
    except Exception:  # noqa: BLE001 — advisory only
        pass
    msg = f"Projekt „{slug}“ neexistuje."
    near = did_you_mean(slug, slugs) if slugs else None
    if near:
        msg += f" Myslel jste „{near}“?"
    msg += (" Existující projekty: " + ", ".join(slugs) + "." if slugs
            else " Zatím žádný projekt nemáte — založíte ho přes /pm start.")
    return msg + " Přehled: pflanzer status"


ASYNC_FULL = "3–5 dní"
ASYNC_AFTER_ITERATE = "1–2 dny"


def async_days(slug: str) -> str:
    """Okno Asyncu: po Iterate (druhé kolo opravuje jen konkrétní věci) kratší než poprvé."""
    try:
        from tool.cli.db import transaction
        with transaction() as conn:
            row = conn.execute(
                "SELECT 1 FROM sessions s JOIN projects p ON p.id = s.project_id "
                "WHERE p.slug = ? AND s.type = 3 LIMIT 1", (slug,)).fetchone()
        return ASYNC_AFTER_ITERATE if row else ASYNC_FULL
    except Exception:  # noqa: BLE001 — advisory only
        return ASYNC_FULL


def project_not_found(slug: str) -> NoReturn:
    """Czech "no such project" error with existing slugs; exit 2."""
    die(project_not_found_message(slug))
    raise SystemExit(2)  # pragma: no cover — die() already exits


class CzechArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with Czech, human error messages (exit 2, brand line)."""

    def error(self, message: str) -> NoReturn:  # type: ignore[override]
        prog = self.prog
        m = re.match(r"the following arguments are required: (.+)", message)
        if m:
            names = [n.strip() for n in m.group(1).split(",")]
            first = names[0]
            extra = f" (a dále {', '.join(names[1:])})" if len(names) > 1 else ""
            hint = f"Příklad a všechny parametry: {prog} --help"
            self._fail(f"Chybí povinný parametr {first}{extra}. {hint}")
        m = re.match(r"argument ([^:]+): invalid choice: '([^']*)' \(choose from (.+)\)", message)
        if m:
            bad = m.group(2)
            choices = [c.strip().strip("'") for c in m.group(3).split(",")]
            near = did_you_mean(bad, choices)
            txt = f"Neznámý příkaz ‚{bad}‘."
            if near:
                txt += f" Myslel jste ‚{near}‘?"
            txt += f" Možnosti: {', '.join(choices)}."
            self._fail(txt)
        m = re.match(r"unrecognized arguments: (.+)", message)
        if m:
            self._fail(f"Neznámý parametr: {m.group(1)}. Přehled: {prog} --help")
        m = re.match(r"argument ([^:]+): expected one argument", message)
        if m:
            self._fail(f"Parametr {m.group(1)} potřebuje hodnotu. Přehled: {prog} --help")
        m = re.match(r"argument ([^:]+): invalid (\w+) value: '([^']*)'", message)
        if m:
            self._fail(f"Parametr {m.group(1)} má neplatnou hodnotu ‚{m.group(3)}‘. "
                       f"Přehled: {prog} --help")
        m = re.match(r"argument ([^:]+): not allowed with argument (.+)", message)
        if m:
            self._fail(f"Parametry {m.group(1)} a {m.group(2)} nejdou použít spolu.")
        self._fail(f"{message}. Přehled: {prog} --help")

    def _fail(self, text: str) -> NoReturn:
        sys.stderr.write(f"{BRAND_LINE}\n\nCHYBA: {text}\n")
        sys.exit(2)


# U throwaway stačí AI pre-check (ADR-0023): tipy o podpisu člověkem se nezobrazují.
_HUMAN_SIGN_PHASES = frozenset({"ai_stand_in"})
_HUMAN_SIGN_CONDITIONS = frozenset({"ai_pending", "ai_stand_ins", "missing_signatures"})


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def tips_for(phase: str, ctx: dict[str, Any] | None = None, limit: int = 3,
             seen: set[str] | None = None) -> list[str]:
    """Recommendations for `phase`, filtered by truthy keys in `ctx`.

    With `seen` (a set of tip texts already shown for the project) tips in it are
    skipped and the returned ones are added to it, so the same tip never repeats.
    """
    ctx = ctx or {}
    throwaway = bool(ctx.get("throwaway"))
    if throwaway and phase in _HUMAN_SIGN_PHASES:
        return []
    items = TIPS.get(phase, [])
    conditional = [t for c, t in items if c and ctx.get(c)
                   and not (throwaway and c in _HUMAN_SIGN_CONDITIONS)]
    generic = [t for c, t in items if c is None]
    if ctx.get("mob"):   # jediná společná varianta: žádní poražení, nikomu se nepoděkuje „za poražené“
        generic = [t for t in generic if "Poraženým" not in t]
    ordered = conditional + [t for t in generic if t not in conditional]
    if seen is not None:
        shown = {_norm(t) for t in seen}
        ordered = [t for t in ordered if _norm(t) not in shown]
    picked = ordered[:limit]
    if seen is not None:
        seen.update(picked)
    return picked


def tips_for_project(slug: str, phase: str, ctx: dict[str, Any] | None = None,
                     limit: int = 3) -> list[str]:
    """Like `tips_for`, but never repeats a tip within one project.

    Shown tips are stored in the audit log (action `tip.shown`, target = project),
    so no schema change is needed. Unknown project or unreadable DB -> plain `tips_for`.
    """
    try:
        from tool.cli.db import audit, transaction
        with transaction() as conn:
            row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
            if not row:
                return tips_for(phase, ctx, limit)
            pid = int(row[0])
            try:
                from tool.cli.triage import load_risk_profile
                if load_risk_profile(conn, pid) == "throwaway":
                    ctx = {**(ctx or {}), "throwaway": True}
            except Exception:  # noqa: BLE001 — advisory
                pass
            try:
                mode = conn.execute("SELECT session_mode FROM projects WHERE id = ?",
                                    (pid,)).fetchone()
                if mode and mode[0] == "mob":
                    ctx = {**(ctx or {}), "mob": True}
            except Exception:  # noqa: BLE001 — starší DB bez sloupce
                pass
            seen: set[str] = set()
            for r in conn.execute(
                    "SELECT payload_json FROM audit_log WHERE action = 'tip.shown' "
                    "AND target_type = 'project' AND target_id = ?", (pid,)).fetchall():
                try:
                    seen.update(json.loads(r[0] or "{}").get("tips", []))
                except (ValueError, TypeError):
                    continue
            before = set(seen)
            tips = tips_for(phase, ctx, limit, seen=seen)
            new = [t for t in tips if t not in before]
            if new:
                audit(conn, action="tip.shown", target_type="project", target_id=pid,
                      payload={"phase": phase, "tips": new})
            return tips
    except Exception:  # noqa: BLE001 — tips are advisory, never break a command
        return tips_for(phase, ctx, limit)


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
