"""Report pro vedení: jednostránkový souhrn projektu a přehled přes všechny projekty.

Subcommands:
- `summary --slug S [--out soubor.md] [--json]` — jedna stránka (≤ 40 řádků) pro vedení:
  cíl, rozhodnutí, náklad, kvalita, rizika, podpisy, výsledek po nasazení, další krok.
- `portfolio [--csv soubor.csv] [--json]` — tabulka přes všechny projekty v DB.

Čísla (days-to-prod, % LOC, AI náklad, podíl AI zástupců) berou z `retro.leadership_numbers`,
takže jsou v retro reportu a tady stejná. Co není změřené, je „neměřeno“ / „—“, nic se neodhaduje.
Funguje v každé fázi: před Go ukáže stav a co chybí.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli import retro  # noqa: E402
from tool.cli._compat import (  # noqa: E402
    ProjectNotFound,
    _window_ai_evidence,
    checkpoint_rows,
    count,
    exit_if_project_missing,
    local_date,
    signature_conditions,
)
from tool.cli.db import transaction  # noqa: E402
from tool.cli.ux import BRAND_LINE, CzechArgumentParser, die, emit  # noqa: E402

MAX_LINES = 40
DASH = "—"
WINDOW_LABELS = {"zadani": "Zadání", "design": "Design", "bezpecnost": "Bezpečnost", "provoz": "Provoz",
                 "bezpecnost-provoz": "Bezpečnost a provoz", "pravo": "Právo", "data": "Data",
                 "podpora": "Podpora"}
DECISION_WORDS = {"go": "Go", "iterate": "Iterate", "kill": "Kill"}
_PLACEHOLDER = re.compile(r"doplnit|doplň|nezad[aá]n|<[^>]+>|\btbd\b|\bxxx\b", re.I)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _clean(text: Any) -> str:
    t = " ".join(str(text or "").replace("**", "").split())
    return "" if t.lower() in retro.EMPTY_MARKERS or _PLACEHOLDER.search(t) else t


def _sentence(text: Any, limit: int = 160) -> str:
    """První věta (nebo prvních `limit` znaků) bez zalomení."""
    t = _clean(text)
    if not t:
        return ""
    m = re.match(r"(.+?[.!?])(\s|$)", t)
    if m:
        t = m.group(1)
    return t if len(t) <= limit else t[: limit - 1].rsplit(" ", 1)[0] + "…"


def _more(items: list[str], n: int = 3) -> str:
    shown = ", ".join(items[:n])
    return shown + (f" a dalších {len(items) - n}" if len(items) > n else "")


def _date(value: Any) -> str:
    d = local_date(value)
    return d.isoformat() if d else DASH


def _decision_reason(conn: Any, pid: int) -> str:
    row = conn.execute(
        "SELECT body_md FROM decisions WHERE project_id = ? AND type IN ('handoff','kill','preference') "
        "ORDER BY id DESC LIMIT 1", (pid,)).fetchone()
    if not row:
        return ""
    m = re.search(r"### Důvod\s+(.*?)(?:\n###|\Z)", row[0] or "", re.S)
    if not m:
        return ""
    from tool.cli.session_2 import strip_reason
    return _sentence(strip_reason(m.group(1)))


def _gate_rows(conn: Any, pid: int, winner: str | None) -> list[dict[str, str]]:
    """Výsledky bran vítěze (před Go: poslední změřená varianta); prázdné = brány neběžely."""
    sql = ("SELECT e.id FROM extracted_code e JOIN variants v ON v.id = e.variant_id "
           "JOIN sessions s ON s.id = v.session_id WHERE s.project_id = ? "
           "AND EXISTS (SELECT 1 FROM quality_gates q WHERE q.extracted_id = e.id)")
    args: list[Any] = [pid]
    if winner:
        sql += " AND v.name = ?"
        args.append(winner)
    ext = conn.execute(sql + " ORDER BY e.id DESC LIMIT 1", args).fetchone()
    if not ext:
        return []
    return [{"gate": r[0], "status": r[1], "details": r[2] or ""} for r in conn.execute(
        "SELECT gate_type, status, details_md FROM quality_gates WHERE extracted_id = ? ORDER BY id",
        (ext[0],)).fetchall()]


def _gate_info(rows: list[dict[str, str]], target: int | None) -> dict[str, Any]:
    if not rows:
        return {"ran": False, "score": None, "target": target, "sentence": None, "unverified": []}
    from tool.cli.quality_gates import (
        aggregate_score,
        gate_label,
        gates_summary_line,
        unverified_gates,
    )
    score = int(aggregate_score(
        [SimpleNamespace(gate_type=r["gate"], status=r["status"]) for r in rows])["gate_score"])  # type: ignore[arg-type]
    unv = [gate_label(u["gate"]) for u in unverified_gates(rows)]
    return {"ran": True, "score": score, "target": target, "unverified": unv,
            "sentence": gates_summary_line(score, rows, target=target)}


def _signatures(slug: str) -> list[dict[str, str]]:
    out = []
    for r in checkpoint_rows(slug):
        label = WINDOW_LABELS.get(r.get("window") or "", (r.get("window") or "?").capitalize())
        who = (r.get("signed_by") or "").strip()
        kind = (r.get("signer_kind") or "").strip()
        agent = (r.get("ai_agent") or r.get("owner_ai") or "").strip()
        ai = _window_ai_evidence(r)
        state = r.get("state")
        if state == "blocked":
            text = f"{label}: BLOKOVÁNO" + (f" ({who})" if who else "")
        elif state == "ok" and who and kind != "AI draft":
            text = (f"{label}: AI návrh" + (f" ({agent})" if agent else "") + f" + potvrdil/a {who}"
                    if ai else f"{label}: {who}" + (f" ({kind})" if kind in ("zástup", "autor kódu") else ""))
        elif ai:
            text = f"{label}: AI návrh" + (f" ({agent})" if agent else "") + ", čeká na člověka"
        else:
            text = f"{label}: zatím nepodepsáno"
        out.append({"window": r.get("window") or "", "text": text, "state": str(state or "")})
    return out


# --------------------------------------------------------------------------
# collect
# --------------------------------------------------------------------------


def collect(slug: str) -> dict[str, Any]:
    """Všechna data jednostránkového reportu jako dict (základ pro markdown i --json)."""
    from tool.cli.session_2 import get_winner, open_criticals, open_remarks, overridden_criticals
    from tool.cli.status import project_detail

    detail = project_detail(slug)       # ValueError při neexistujícím projektu
    nums = retro.leadership_numbers(slug)
    with transaction() as conn:
        p = dict(conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone())
        pid = int(p["id"])
        sess = conn.execute(
            "SELECT decision, decision_atribuce, decision_ts FROM sessions "
            "WHERE project_id = ? AND type = 2 ORDER BY id DESC LIMIT 1", (pid,)).fetchone()
        decided = sess and sess[0] in DECISION_WORDS
        winner = get_winner(conn, pid) if decided and sess[0] == "go" else None
        reason = _decision_reason(conn, pid) if decided else ""
        crit = open_criticals(conn, pid)
        if winner:
            crit = [c for c in crit if c["variant"] == winner]
        high = [r for r in open_remarks(conn, pid, winner) if r["severity"] == "high"]
        overridden = overridden_criticals(conn, pid)
        gates = _gate_info(_gate_rows(conn, pid, winner), p.get("production_readiness_target"))
        n_people = p.get("capacity_person_days")
    conds = [c for c in signature_conditions(slug) if c.get("state") != "waived"]
    sigs = _signatures(slug)
    killed = p["status"] == "killed"
    lessons = retro.lessons(slug) if killed else []

    if decided:
        decision = {"decision": sess[0], "word": DECISION_WORDS[sess[0]], "winner": winner,
                    "decider": (sess[1] or p.get("decider_name") or "").strip() or None,
                    "when": _date(sess[2]), "reason": reason}
    else:
        waiting = [b["text"] for b in detail.get("blockers", [])][:1]
        decision = {"decision": None, "word": None, "winner": None, "decider": p.get("decider_name"),
                    "when": None, "reason": "", "phase": detail["phase"], "missing": waiting}

    risks: list[str] = []
    if crit:
        risks.append(f"Kritické otevřené: {len(crit)} ("
                     + _more([f"{c['department']}: {_sentence(c['rationale'], 60)}" for c in crit]) + ")")
    if high:
        risks.append(f"Důležité otevřené: {len(high)} ("
                     + _more([_sentence(r["rationale"], 60) for r in high]) + ")")
    for c in overridden[:2]:
        due = f", termín {c['deadline']}" if c.get("deadline") else ""
        risks.append(f"Vědomě přebito ({c['decider']}, {c['at']}): "
                     f"{_sentence(c['reason'], 80)}{due}")
    if conds:
        risks.append(f"Podmínky z podpisů: {len(conds)} ("
                     + _more([c["text"] for c in conds]) + ")")
    if gates["unverified"]:
        risks.append("Neověřené brány: " + _more(gates["unverified"], 4))
    if killed:
        risks = [r for r in risks if not r.startswith(("Kritické", "Důležité"))]

    goal = _sentence(p.get("xyz_hypothesis"))
    nxt = detail["next_step"]
    first = next((b for b in detail.get("blockers", []) if b.get("command") == nxt), None)
    if first:       # věta místo příkazu s <jméno>; příkaz zůstane v `pflanzer status`
        nxt = first["text"].rstrip(".") + ". Detail: `pflanzer status --slug %s`." % slug
    if nxt == DASH:
        nxt = ("zapsat poučení: `pflanzer retro lesson --slug %s --text \"…\"`" % slug
               if killed and not lessons else
               "vzít poučení do zadání dalšího Kickoffu (`/pm start`)" if killed else
               "nic dalšího se neočekává")
    return {
        "slug": slug, "name": p["name"], "status": p["status"], "phase": detail["phase"],
        "goal": goal, "decision": decision,
        "cost": {"person_days": n_people, "ai": nums["ai_cost"]},
        "quality": gates, "risks": risks,
        "risk_counts": {"critical": len(crit), "important": len(high), "overridden": len(overridden),
                        "conditions": len(conds), "unverified_gates": len(gates["unverified"])},
        "signatures": sigs, "outcome": nums, "lessons": [x["text"] for x in lessons],
        "next_step": nxt,
    }


# --------------------------------------------------------------------------
# render summary
# --------------------------------------------------------------------------


def render_summary_md(data: dict[str, Any]) -> str:
    d, c = data["decision"], data["cost"]
    out = [BRAND_LINE, "", f"# Report pro vedení — {data['name']}", ""]
    out.append("**Cíl:** " + (data["goal"] or "v zadání (Kickoff) není cíl popsaný jednou větou."))
    out += ["", "## Rozhodnutí"]
    if d["decision"]:
        win = f" (vítěz {d['winner']})" if d["winner"] else ""
        who = f" — {d['decider']} (Decider)" if d["decider"] else ""
        out.append(f"**{d['word']}**{win}{who}, {d['when']}. "
                   + (f"Proč: {d['reason']}" if d["reason"] else "Důvod není v decision logu."))
    else:
        miss = f" Chybí: {d['missing'][0]}" if d.get("missing") else ""
        out.append(f"Zatím nepadlo. Stav: {d['phase']}.{miss}")
    out += ["", "## Náklad"]
    out.append("- Lidé: " + (f"{count(int(c['person_days']), 'člověkoden', 'člověkodny', 'člověkodnů')} "
                             "(plán kapacity v Kickoffu)"
                             if c["person_days"] else "neměřeno"))
    out.append("- AI: " + retro.leadership_ai_cost_text(c["ai"]))
    out += ["", "## Kvalita"]
    q = data["quality"]
    out.append(q["sentence"] if q["ran"] else "Brány zatím neběžely (spustí je Ship).")
    out += ["", "## Rizika"]
    out += [f"- {r}" for r in data["risks"]] or ["- Žádné otevřené riziko."]
    out += ["", "## Kdo podepsal"]
    out.append(" · ".join(s["text"] for s in data["signatures"]) or "Okna zatím nikdo nepodepsal.")
    out += ["", "## Výsledek po nasazení"]
    o = data["outcome"]
    if data["status"] == "killed":
        out.append("Do produkce nic nešlo."
                   + (" Poučení: " + "; ".join(data["lessons"]) if data["lessons"]
                      else " Poučení zatím není zapsané."))
    elif o["throwaway"]:
        out.append("Throwaway demo nejde do produkce, přežití kódu se neměří.")
    elif o["measured"]:
        out += [f"- {x}" for x in retro.leadership_lines(o)]
    else:
        out.append("Ještě neměřeno, měří se T+30 (`pflanzer retro measure`, po mergi do produkce).")
    out += ["", "## Další krok", data["next_step"]]
    # Strop 40 řádků: nejdřív zkrátíme rizika (nejdelší sekce), ostatní sekce zůstanou.
    if len(out) > MAX_LINES and len(data["risks"]) > 3:
        return render_summary_md(dict(data, risks=data["risks"][:-1]))
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# portfolio
# --------------------------------------------------------------------------

PORTFOLIO_COLS = ("projekt", "stupeň", "risk profil", "fáze / rozhodnutí", "skóre bran",
                  "dny Go→merge", "% LOC přežívá", "AI náklad", "podíl AI zástupců")


def _num(v: Any, unit: str = "") -> str:
    if v is None:
        return DASH
    f = float(v)
    return (f"{int(f)}" if f.is_integer() else f"{f:.1f}") + unit


def portfolio_rows() -> list[dict[str, Any]]:
    from tool.cli.status import project_detail, tier_label
    with transaction() as conn:
        slugs = [r[0] for r in conn.execute(
            "SELECT slug FROM projects ORDER BY created_at DESC, id DESC").fetchall()]
    rows = []
    for slug in slugs:
        d = project_detail(slug)
        nums = retro.leadership_numbers(slug)
        with transaction() as conn:
            pid = int(conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0])
            gates = _gate_info(_gate_rows(conn, pid, d.get("winner") if isinstance(d.get("winner"), str)
                                          else None), d.get("gate_target"))
        killed = d["status"] == "killed"
        lessons = [x["text"] for x in retro.lessons(slug)] if killed else []
        ai = nums["ai_cost"]
        cost = DASH
        if ai["measured"]:
            cost = f"${ai['usd']:.2f}" if ai["usd"] is not None else retro._tokens_text(int(ai["tokens"] or 0))
            if ai["czk"] is not None:
                cost += f" ({ai['czk']} Kč)"
        share = nums["ai_share"]["pct"]
        phase = d["phase"] + (f" · {DECISION_WORDS[d['decision']]}"
                              if d.get("decision") in DECISION_WORDS and not killed
                              and DECISION_WORDS[d["decision"]] not in d["phase"] else "")
        rows.append({
            "slug": slug, "name": d["name"], "tier": d["tier"], "tier_label": tier_label(d["tier"]).split(" (")[0],
            "risk_profile": d["risk_profile"], "phase": phase, "status": d["status"],
            "gate_score": gates["score"], "days_to_prod": nums["days_to_prod"]["value"],
            "loc_survival_pct": nums["loc_survival_pct"]["value"], "ai_cost": ai, "ai_cost_text": cost,
            "ai_share_pct": share, "lessons": lessons,
        })
    return rows


def _cells(r: dict[str, Any]) -> list[str]:
    return [r["slug"], r["tier_label"] or DASH, r["risk_profile"] or DASH, r["phase"] or DASH,
            DASH if r["gate_score"] is None else f"{r['gate_score']}/100",
            _num(r["days_to_prod"]), _num(r["loc_survival_pct"], " %"), r["ai_cost_text"],
            DASH if r["ai_share_pct"] is None else f"{r['ai_share_pct']} %"]


def render_portfolio_md(rows: list[dict[str, Any]]) -> str:
    out = [BRAND_LINE, "", "# Portfolio projektů", ""]
    if not rows:
        return "\n".join(out + ["Zatím žádný projekt. Nový založíte přes `/pm start`.", ""])
    esc = lambda t: str(t).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    out.append("| " + " | ".join(PORTFOLIO_COLS) + " |")
    out.append("|" + "|".join("---" for _ in PORTFOLIO_COLS) + "|")
    out += ["| " + " | ".join(esc(c) for c in _cells(r)) + " |" for r in rows]
    killed = [r for r in rows if r["status"] == "killed"]
    if killed:
        out += ["", "## Poučení z killnutých projektů", ""]
        for r in killed:
            out.append(f"- `{r['slug']}`: " + ("; ".join(r["lessons"]) if r["lessons"]
                                               else "poučení zatím není zapsané"))
    out += ["", f"Projektů: {len(rows)}. Cíle: dny do produkce ≤ {retro.TARGET_DAYS_TO_PROD}, "
            f"přežití kódu ≥ {retro.TARGET_REUSE_PCT:.0f} %. „{DASH}“ = neměřeno.", ""]
    return "\n".join(out)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(PORTFOLIO_COLS + ("poučení",))
        for r in rows:
            w.writerow(_cells(r) + ["; ".join(r["lessons"])])


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    p = CzechArgumentParser(prog="pflanzer report", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=CzechArgumentParser)
    ps = sub.add_parser("summary", help="Jednostránkový report pro vedení (jeden projekt)")
    ps.add_argument("--slug", required=True)
    ps.add_argument("--out", help="Zapiš markdown do souboru (jinak na výstup)")
    ps.add_argument("--json", action="store_true", help="Strojový výstup")
    pp = sub.add_parser("portfolio", help="Tabulka přes všechny projekty")
    pp.add_argument("--csv", help="Zapiš tabulku jako CSV")
    pp.add_argument("--json", action="store_true", help="Strojový výstup")
    args = p.parse_args(argv)
    try:
        if args.cmd == "summary":
            data = collect(args.slug)
            md = render_summary_md(data)
            if args.out:
                path = Path(args.out).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(md, encoding="utf-8")
                data["report_path"] = retro._display(path)
            if args.json:
                emit(dict(data, markdown=md), title="Report pro vedení", as_json=True)
            elif args.out:
                emit(data, title=f"Report pro vedení: {args.slug}",
                     lines=[f"Zapsáno: {data['report_path']} ({len(md.splitlines())} řádků)"],
                     next_step=data["next_step"])
            else:
                sys.stdout.write(md)
        else:
            rows = portfolio_rows()
            if args.csv:
                write_csv(Path(args.csv).expanduser(), rows)
            if args.json:
                emit({"projects": rows, "csv": args.csv}, title="Portfolio", as_json=True)
            elif args.csv:
                emit({"projects": rows}, title="Portfolio",
                     lines=[f"CSV zapsáno: {retro._display(Path(args.csv))} ({count(len(rows), 'projekt', 'projekty', 'projektů')})"])
            else:
                sys.stdout.write(render_portfolio_md(rows))
    except ProjectNotFound as e:
        from tool.cli.ux import project_not_found
        project_not_found(e.slug)
    except ValueError as e:
        if "neexistuje" in str(e):
            die(str(e))
        raise
    except Exception as e:  # noqa: BLE001
        exit_if_project_missing(e)
        raise


if __name__ == "__main__":
    main()
