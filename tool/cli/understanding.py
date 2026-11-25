"""`pflanzer why` a `pflanzer explain-back` — porozumění vítězi před Shipem (ADR-0027).

Dva doporučené kroky, které Ship neblokují a nemění skóre:

    pflanzer why add --slug S --what "nová závislost X" --why "protože …" [--by JMÉNO]
    pflanzer why list --slug S

    pflanzer explain-back record --slug S --by JMÉNO --change "co jsem upravil ručně" \\
        --minutes 25 [--note "…"]
    pflanzer explain-back show --slug S

Věty „proč“ a záznam vysvětlení zpět se ukážou v `SHIP.md`. Když vysvětlení zpět
chybí, SHIP.md ho uvede jako otevřené riziko.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.ux import (  # noqa: E402
    CzechArgumentParser,
    die,
    emit,
    project_not_found_message,
)

__all__ = [
    "add_why", "list_why", "record_explain_back", "list_explain_back", "latest_explain_back",
    "known_authors", "render_why_md", "render_understanding_md", "main",
]


def _project_id(conn: Any, slug: str) -> int:
    row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
    if not row:
        raise ValueError(project_not_found_message(slug))
    return int(row[0])


def _clean(value: str | None, label: str) -> str:
    text = re.sub(r"\s+", " ", (value or "").strip())
    if not text:
        raise ValueError(f"Chybí {label}.")
    return text


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lstrip("@")).casefold()


# --------------------------------------------------------------------------
# Věty „proč“ (ADR-0027 bod 3)
# --------------------------------------------------------------------------


def add_why(slug: str, what: str, why: str, by: str | None = None) -> dict[str, Any]:
    """Zapíše jednu větu zdůvodnění k návrhovému rozhodnutí vítěze."""
    what_t = _clean(what, "popis rozhodnutí (--what)")
    why_t = _clean(why, "zdůvodnění (--why)")
    who = (by or "").strip() or current_actor()
    with transaction() as conn:
        pid = _project_id(conn, slug)
        cur = conn.execute(
            "INSERT INTO design_rationale (project_id, what, why, added_by) VALUES (?, ?, ?, ?)",
            (pid, what_t, why_t, who))
        audit(conn, action="understanding.why_add", target_type="project", target_id=pid,
              payload={"slug": slug, "what": what_t, "why": why_t, "by": who})
        rid = int(cur.lastrowid or 0)
    return {"id": rid, "slug": slug, "what": what_t, "why": why_t, "by": who}


def list_why(slug: str) -> list[dict[str, Any]]:
    """Věty „proč“ projektu v pořadí zápisu; neexistující projekt = ValueError."""
    with transaction() as conn:
        pid = _project_id(conn, slug)
        rows = conn.execute(
            "SELECT id, what, why, added_by, added_at FROM design_rationale "
            "WHERE project_id = ? ORDER BY id", (pid,)).fetchall()
    return [{"id": r[0], "what": r[1], "why": r[2], "by": r[3], "at": r[4]} for r in rows]


def render_why_md(slug: str) -> str:
    """Sekce SHIP.md „Proč je to navržené takhle“ (vždy; prázdná ukáže příkaz)."""
    items = list_why(slug)
    if not items:
        return ("## Proč je to navržené takhle\n"
                "Zdůvodnění návrhu zatím nikdo nezapsal (nová závislost, datový model, obejití "
                "existující komponenty). Jednu větu přidáte: "
                f'`pflanzer why add --slug {slug} --what "…" --why "…"`\n')
    lines = [f"- **{i['what']}**: {i['why']}" + (f" ({i['by']})" if i.get("by") else "")
             for i in items]
    return "## Proč je to navržené takhle\n" + "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Vysvětlení zpět (ADR-0027 body 1, 2, 5)
# --------------------------------------------------------------------------


def known_authors(slug: str) -> list[str]:
    """Kdo vítěze psal, pokud to nástroj ví (jen čtení): zástupce kroku Vývoj z Kickoffu
    a autoři commitů větve vítěze. Prázdný seznam = nevíme."""
    names: list[str] = []
    try:
        from tool.cli.quick_session import keyboard_owner
        owner = keyboard_owner(slug)
        if owner:
            names.append(owner)
    except Exception:  # noqa: BLE001 — jen doplňující informace
        pass
    try:
        from tool.cli import handoff_pr
        ctx = handoff_pr._fetch_ship_context(slug)
        w, e = ctx["winner"], ctx["extracted"]
        wt = handoff_pr._winner_worktree(slug, w[0], e) if (w and e) else None
        if wt is not None:
            base = ctx["project"][7] or "main"
            rc, out = handoff_pr._git(wt, "log", "--format=%an", f"{base}..HEAD")
            if rc == 0:
                names.extend(x.strip() for x in out.splitlines() if x.strip())
    except Exception:  # noqa: BLE001 — bez vítěze / worktree prostě nevíme
        pass
    return list(dict.fromkeys(names))


def record_explain_back(slug: str, by: str, change: str, minutes: int,
                        note: str = "") -> dict[str, Any]:
    """Zapíše vysvětlení vítěze zpět; vysvětlovat nesmí autor (u klávesnice) vítěze."""
    who = _clean(by, "jméno (--by)")
    change_t = _clean(change, "popis ruční změny (--change)")
    if int(minutes) <= 0:
        raise ValueError("Počet minut (--minutes) musí být kladné číslo.")
    authors = known_authors(slug)
    if _norm_name(who) in {_norm_name(a) for a in authors}:
        raise ValueError(
            f"Vysvětlit vítěze zpět musí někdo, kdo u jeho klávesnice neseděl; {who} je "
            "veden jako autor. Zapište jiného vývojáře (typicky reviewera) nebo zástupce Provozu.")
    with transaction() as conn:
        pid = _project_id(conn, slug)
        cur = conn.execute(
            "INSERT INTO explain_back (project_id, explained_by, change_md, minutes, note, "
            "recorded_by) VALUES (?, ?, ?, ?, ?, ?)",
            (pid, who, change_t, int(minutes), (note or "").strip() or None, current_actor()))
        audit(conn, action="understanding.explain_back", target_type="project", target_id=pid,
              payload={"slug": slug, "by": who, "change": change_t, "minutes": int(minutes),
                       "note": (note or "").strip() or None})
        rid = int(cur.lastrowid or 0)
    log_path = _write_decision_log(slug, who, change_t, int(minutes), (note or "").strip())
    return {"id": rid, "slug": slug, "by": who, "change": change_t, "minutes": int(minutes),
            "note": (note or "").strip() or None, "decision_log": log_path}


def _write_decision_log(slug: str, who: str, change: str, minutes: int, note: str) -> str | None:
    """Záznam do `.pflanzer/decisions/<slug>.md` (kdo, kdy, co změnil, jak dlouho); jen když
    cwd je target repo. Zdroj pravdy zůstává DB."""
    try:
        from tool.cli.session_2 import write_repo_decision_log
        body = (f"### Vysvětlení vítěze zpět\n\n- Kdo: {who}\n- Co změnil ručně: {change}\n"
                f"- Jak dlouho: {minutes} min\n" + (f"- Poznámka: {note}\n" if note else ""))
        return write_repo_decision_log(slug, body, label="Vysvětlení zpět")
    except Exception:  # noqa: BLE001 — decision log nesmí shodit zápis
        return None


def list_explain_back(slug: str) -> list[dict[str, Any]]:
    with transaction() as conn:
        pid = _project_id(conn, slug)
        rows = conn.execute(
            "SELECT id, explained_by, change_md, minutes, note, recorded_at FROM explain_back "
            "WHERE project_id = ? ORDER BY id", (pid,)).fetchall()
    return [{"id": r[0], "by": r[1], "change": r[2], "minutes": r[3], "note": r[4],
             "at": r[5]} for r in rows]


def latest_explain_back(slug: str) -> dict[str, Any] | None:
    rows = list_explain_back(slug)
    return rows[-1] if rows else None


def _explain_line(rec: dict[str, Any]) -> str:
    when = f", {str(rec['at'])[:10]}" if rec.get("at") else ""
    note = f" Poznámka: {rec['note']}" if rec.get("note") else ""
    return (f"{rec['by']} vítěze vysvětlil zpět a ručně změnil: {rec['change']} "
            f"({rec['minutes']} min{when}).{note}")


def render_understanding_md(slug: str) -> str:
    """Sekce SHIP.md k vysvětlení zpět: záznam, nebo otevřené riziko (Ship neblokuje)."""
    rec = latest_explain_back(slug)
    if rec:
        return "## Vysvětlení vítěze zpět\n" + _explain_line(rec) + "\n"
    return ("## Otevřená rizika\n"
            "- Vítěze zatím nikdo mimo autory neprošel a nevysvětlil zpět (ADR-0027). Je to "
            "doporučený krok, Ship neblokuje: "
            f'`pflanzer explain-back record --slug {slug} --by "<jméno>" --change "…" '
            "--minutes N`\n")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _cmd_why(args: Any) -> None:
    if args.action == "add":
        out = add_why(args.slug, args.what, args.why, args.by)
        emit(out, title=f"Věta „proč“ zapsána — {args.slug}",
             lines=[f"**{out['what']}**: {out['why']}"],
             next_step=f"`pflanzer why list --slug {args.slug}` · pak `pflanzer ship --slug {args.slug}`",
             as_json=args.json)
        return
    items = list_why(args.slug)
    lines = [f"**{i['what']}**: {i['why']}" + (f" ({i['by']})" if i.get("by") else "")
             for i in items] or ["Zatím nic: zdůvodnění návrhu nikdo nezapsal."]
    emit(items, title=f"Proč je to navržené takhle — {args.slug}", lines=lines,
         next_step=None if items else
         f'`pflanzer why add --slug {args.slug} --what "…" --why "…"`', as_json=args.json)


def _cmd_explain_back(args: Any) -> None:
    if args.action == "record":
        out = record_explain_back(args.slug, args.by, args.change, args.minutes, args.note)
        lines = [f"{out['by']} · {out['minutes']} min · {out['change']}"]
        if out.get("decision_log"):
            lines.append(f"Decision log: `{out['decision_log']}`")
        emit(out, title=f"Vysvětlení zpět zapsáno — {args.slug}", lines=lines,
             next_step=f"`pflanzer ship --slug {args.slug}`", as_json=args.json)
        return
    rows = list_explain_back(args.slug)
    lines = [_explain_line(r) for r in rows] or [
        "Zatím nikdo mimo autory vítěze nevysvětlil zpět (doporučený krok, Ship neblokuje)."]
    emit(rows, title=f"Vysvětlení zpět — {args.slug}", lines=lines,
         next_step=None if rows else
         f'`pflanzer explain-back record --slug {args.slug} --by "<jméno>" --change "…" --minutes N`',
         as_json=args.json)


def build_parser() -> CzechArgumentParser:
    p = CzechArgumentParser(prog="pflanzer", description=__doc__.split("\n")[0])
    top = p.add_subparsers(dest="group", required=True)

    why = top.add_parser("why", help="věty „proč“ k návrhu vítěze")
    why_sub = why.add_subparsers(dest="action", required=True)
    add = why_sub.add_parser("add", help="zapsat větu zdůvodnění")
    add.add_argument("--slug", required=True)
    add.add_argument("--what", required=True,
                     help="návrhové rozhodnutí (nová závislost, datový model, …)")
    add.add_argument("--why", required=True, help="jedna věta: proč")
    add.add_argument("--by", default=None, help="kdo zdůvodnění potvrzuje (výchozí: git user)")
    lst = why_sub.add_parser("list", help="vypsat věty „proč“")
    lst.add_argument("--slug", required=True)

    eb = top.add_parser("explain-back", help="vysvětlení vítěze zpět (ne autorem)")
    eb_sub = eb.add_subparsers(dest="action", required=True)
    rec = eb_sub.add_parser("record", help="zapsat vysvětlení a ruční změnu")
    rec.add_argument("--slug", required=True)
    rec.add_argument("--by", required=True, help="kdo vysvětloval (ne autor u klávesnice)")
    rec.add_argument("--change", required=True, help="co se ve vítězi změnilo ručně")
    rec.add_argument("--minutes", required=True, type=int, help="jak dlouho to trvalo")
    rec.add_argument("--note", default="", help="nepovinná poznámka")
    show = eb_sub.add_parser("show", help="ukázat záznamy")
    show.add_argument("--slug", required=True)

    for sub in (add, lst, rec, show):
        sub.add_argument("--json", action="store_true", help="Strojový výstup")
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.group == "why":
            _cmd_why(args)
        else:
            _cmd_explain_back(args)
    except ValueError as exc:
        die(str(exc))


if __name__ == "__main__":
    main()
