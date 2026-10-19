"""`pflanzer checkpoint` — zapíše výsledek okna zástupce kroku cesty (ADR-0021).

v0.5 nahrazuje plný 48h triage krátkými okny. Každé okno podepisuje příslušné
triage tracky, takže Ship (odložený triage blokuje production_ready)
projde bez paralelní byrokracie:

    zadani      → discovery          (Kickoff: problém, metrika, kill kritérium)
    bezpecnost  → security + legal   (20 min, konec Buildu nebo do 48 h)
    provoz      → platform           (20 min, před Ship)
    design      → (jen AI náhrada designu; bez triage tracku — zapisuje se do audit logu)

Usage:
    pflanzer checkpoint --slug S bezpecnost --by "Lucie" --note "syntetická data, egress jen API X"
    pflanzer checkpoint --slug S provoz --by "Karel" --blocked --note "chybí monitoring"
    pflanzer checkpoint --slug S bezpecnost --ai [--agent security-expert] --note "AI pre-check"
    pflanzer checkpoint --slug S design --by "Pavla" --note "prošla hlavní tok a kontrasty"
    pflanzer checkpoint --slug S --list

AI náhrada (ADR-0023): `--ai` zapíše DRAFT. U throwaway je okno hned ok, u pilotu
a production zůstane „čeká na podpis člověka“ (Ship blokuje) a potvrdí ho až
`--by <jméno>`. U okna provoz pilotu smí podepsat i vývojář z jádra.

Okno bezpečnost pokrývá tracky security + legal. Podepíše-li ho autor kódu
(zástupce kroku Vývoj), zapíše se jako „potvrdil autor kódu“ s upozorněním, že
právní kontrolu (GDPR, smlouvy) to nenahrazuje. Každý podpis má atribut
`signed_by_role` (zástupce | zástup | autor kódu | AI draft); souhrn pro SHIP.md
vrací `checkpoint_summary(slug)`.

Okno design: u AI náhrady designu ho potvrzuje člověk (PdM). U pilotu Ship
neblokuje, u production ano (`design_gate`).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.cli.charter import ai_agent, is_ai_owner, owner_display  # noqa: E402
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.ux import (
    CzechArgumentParser,
    did_you_mean,
    die,
    emit,
    project_not_found_message,
    tips_for_project,
)  # noqa: E402

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

WINDOWS: dict[str, dict[str, Any]] = {
    "zadani": {"label": "Zadání (Kickoff)", "tracks": ("discovery",)},
    "bezpecnost": {"label": "Bezpečnost & právo", "tracks": ("security", "legal")},
    "provoz": {"label": "Provoz", "tracks": ("platform",)},
    # Jen AI náhrada designu: žádný triage track (CHECK má 4 hodnoty), podpis je v audit logu.
    "design": {"label": "Design (AI)", "tracks": ()},
}
ALIASES = {"kickoff": "zadani", "discovery": "zadani", "security": "bezpecnost",
           "legal": "bezpecnost", "pravo": "bezpecnost", "platform": "provoz",
           "ops": "provoz", "ux": "design"}


# Okno -> krok cesty, jehož zástupce ho podepisuje.
WINDOW_STEP = {"zadani": "byznys", "bezpecnost": "bezpecnost", "provoz": "provoz",
               "design": "design"}
SIGNER_KINDS = ("zástupce", "zástup", "autor kódu", "AI draft")
AI_DRAFT_MARK = "AI draft — čeká na podpis člověka"
USAGE = ('  pflanzer checkpoint --slug <slug> bezpecnost --by "Jana" --note "co se ověřilo"\n'
         '  pflanzer checkpoint --slug <slug> provoz --ai --note "AI pre-check"')


def killed_message(slug: str) -> str:
    return (f"Projekt „{slug}“ je ukončen (Kill) — checkpointy už nemají smysl. "
            f"Zapište poučení: pflanzer retro lesson --slug {slug} --text \"…\"")


def _window(name: str) -> str:
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in WINDOWS:
        near = did_you_mean(key, [*WINDOWS, *ALIASES])
        near = ALIASES.get(near, near) if near else None
        raise ValueError(f"Neznámé okno ‚{name}‘."
                         + (f" Myslel jste ‚{near}‘?" if near else "")
                         + " Okna: zadani | bezpecnost | provoz | design.")
    return key


def _same_person(a: str | None, b: str | None) -> bool:
    ta = set((a or "").casefold().split())
    tb = set((b or "").casefold().split())
    return bool(ta and tb and (ta <= tb or tb <= ta))


def _load_owners(conn: Any, pid: int) -> dict[str, str]:
    row = conn.execute("SELECT path_owners_json FROM projects WHERE id = ?", (pid,)).fetchone()
    return json.loads(row[0]) if row and row[0] else {}


def _load_signers(conn: Any, pid: int) -> dict[str, str]:
    """`ai_signers_json`: krok -> člověk, který podepíše AI náhradu (chybí sloupec = {})."""
    try:
        row = conn.execute("SELECT ai_signers_json FROM projects WHERE id = ?", (pid,)).fetchone()
        data = json.loads(row[0]) if row and row[0] else {}
    except Exception:  # starší DB bez sloupce / poškozený JSON
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def _load_core(conn: Any, pid: int) -> list[str]:
    row = conn.execute("SELECT core_json FROM projects WHERE id = ?", (pid,)).fetchone()
    try:
        return list(json.loads(row[0])) if row and row[0] else []
    except (ValueError, TypeError):
        return []


def _is_code_author(who: str, owners: dict[str, str], core: list[str]) -> bool:
    """Autor kódu = zástupce kroku Vývoj, nebo člen jádra označený jako vývoj/dev."""
    vyvoj = owners.get("vyvoj")
    if vyvoj and not is_ai_owner(vyvoj) and _same_person(who, vyvoj):
        return True
    for member in core:
        if re.search(r"(?i)\b(v[ýy]voj\w*|dev\w*|program[aá]tor\w*)\b", member or ""):
            name = re.sub(r"\(.*?\)|[-–,].*$", "", member).strip()
            if _same_person(who, name):
                return True
    return False


def _signer_kind(window: str, who: str, owner: str | None, owners: dict[str, str],
                 core: list[str], *, ai: bool, designated: str | None = None) -> str:
    if ai:
        return "AI draft"
    if window == "bezpecnost" and _is_code_author(who, owners, core):
        return "autor kódu"
    if designated and _same_person(who, designated):
        return "zástupce"  # určený podepisující (Kickoff / ai_signers)
    if owner and is_ai_owner(owner) and any(
            _same_person(who, owners.get(k)) for k in ("byznys", "produkt") if _human(owners.get(k))):
        return "zástupce"  # AI draft potvrzuje Decider nebo PdM (ADR-0023)
    if window == "design" and owner and is_ai_owner(owner):
        pdm = owners.get("produkt")
        if pdm and not is_ai_owner(pdm) and _same_person(who, pdm):
            return "zástupce"  # AI design potvrzuje PdM (ADR-0023)
    if owner and not is_ai_owner(owner) and _same_person(who, owner):
        return "zástupce"
    return "zástup"


def _human(name: str | None) -> str | None:
    return name if name and not is_ai_owner(name) else None


def guidance_core(window: str, owners: dict[str, str], risk: str) -> str:
    """Kdo smí podepsat okno, které zastupuje AI a nikdo není určen (bez názvu okna)."""
    if risk == "throwaway":
        return "u throwaway stačí AI pre-check (ADR-0023)"
    decider, pdm, dev = (_human(owners.get(k)) for k in ("byznys", "produkt", "vyvoj"))

    def named(role: str, who: str | None) -> str:
        return f"{role} ({who})" if who else role

    if risk == "production":
        who_can = f"{named('Decider', decider)} nebo DPO/právník"
    else:
        who_can = f"{named('Decider', decider)} nebo {named('PdM', pdm)}"
    no_dev = f"; ne autor kódu{f' ({dev})' if dev else ''}, pokud jde o osobní data"
    when = "u production" if risk == "production" else "u pilotu"
    return f"{when} může podepsat {who_can}{no_dev}"


def signer_guidance(window: str, owners: dict[str, str], risk: str) -> str:
    """Věta pro bootstrap/status: AI pre-check a nikdo není určen k podpisu (ADR-0023)."""
    return (f"{WINDOWS[window]['label']}: AI pre-check, nikdo zatím není určen k podpisu — "
            f"{guidance_core(window, owners, risk)}.")


def _designated(window: str, owner: str | None, owners: dict[str, str], risk: str,
                signers: dict[str, str] | None = None) -> str | None:
    """Člověk, který je pro okno určen k podpisu (None = nikdo nebyl určen)."""
    if _human(owner):
        return owner
    named = _human((signers or {}).get(WINDOW_STEP[window]))
    if named and is_ai_owner(owner):
        return named          # tým výslovně určil, kdo AI draft podepíše (ai_signers)
    if window == "provoz" and risk == "pilot" and _human(owners.get("vyvoj")):
        return owners["vyvoj"]
    if window == "design":
        return _human(owners.get("produkt")) or _human(owners.get("byznys"))
    return None


def _agent_from_who(who: str | None) -> str | None:
    m = re.match(r"AI \((.+)\)", who or "")
    return m.group(1) if m else None


def sign(slug: str, window: str, *, by: str = "", note: str, blocked: bool = False,
         ai: bool = False, agent: str | None = None) -> dict[str, Any]:
    """Sign (or block) the triage tracks covered by a checkpoint window.

    `ai=True` writes an AI draft (ADR-0023): ok for throwaway, otherwise
    `pending` until a human countersigns with `by=`. Window `design` has no
    triage tracks (AI design stand-in, confirmed by a human; audit log only).
    """
    from tool.cli.triage import load_risk_profile

    window = _window(window)
    if not ai and not by.strip():
        raise ValueError("--by je povinné: kdo za krok cesty podepisuje "
                         "(nebo --ai pro AI draft).\nPříklad:\n" + USAGE)
    if not note.strip():
        raise ValueError("--note je povinné: co se v okně ověřilo / co chybí.\nPříklad:\n" + USAGE)
    if ai and window == "zadani":
        raise ValueError("Zadání (Kickoff) AI nepodepíše — podepisuje Decider. Použij --by <jméno>.")
    if ai and window == "design":
        raise ValueError("Design za AI je zapsaný už v Kickoffu; okno design potvrzuje člověk "
                         '(PdM): --by "<jméno>" --note "co jste zkontrolovali".')
    label = WINDOWS[window]["label"]
    step = WINDOW_STEP[window]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    warnings: list[str] = []
    countersigned = False
    with transaction() as conn:
        proj = conn.execute("SELECT id, status FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(project_not_found_message(slug))
        if proj[1] == "killed":
            raise ValueError(killed_message(slug))
        pid = int(proj[0])
        owners = _load_owners(conn, pid)
        signers = _load_signers(conn, pid)
        core = _load_core(conn, pid)
        owner = owners.get(step)
        risk = load_risk_profile(conn, pid)
        if window == "design" and not is_ai_owner(owner):
            raise ValueError(
                f"Design zastupuje člověk ({owner or 'nikdo'}) — okno design se používá jen "
                "pro AI náhradu designu.")
        track0 = WINDOWS[window]["tracks"][:1]
        prior = conn.execute(
            "SELECT status, signed_by FROM triage WHERE project_id = ? AND track = ?",
            (pid, track0[0])).fetchone() if track0 else None

        agent_name: str | None = None
        if ai:
            agent_name = agent or ai_agent(owner, step)
            who = f"AI ({agent_name})"
            status = "blocked" if blocked else ("ok" if risk == "throwaway" else "pending")
            head = ("BLOKOVÁNO" if blocked else
                    "AI pre-check" if status == "ok" else AI_DRAFT_MARK)
            if status == "pending":
                warnings.append(f"{label}: AI draft není podpis — Ship dál blokuje, dokud ho "
                                "nepotvrdí člověk (`--by <jméno>`).")
                if not _designated(window, owner, owners, risk, signers):
                    warnings.append(signer_guidance(window, owners, risk))
        else:
            who = by.strip()
            status = "blocked" if blocked else "ok"
            head = "BLOKOVÁNO" if blocked else "OK"
            countersigned = bool(prior and prior[0] == "pending"
                                 and str(prior[1] or "").startswith("AI")) and not blocked
            if countersigned:
                agent_name = _agent_from_who(prior[1])
            owner_human = _human(owner)
            allowed = bool(owner_human and _same_person(who, owner))
            if (window == "provoz" and risk == "pilot"
                    and _same_person(who, owners.get("vyvoj"))):
                allowed = True
            if window == "design" and _same_person(who, owners.get("produkt")):
                allowed = True
            if owner_human and not allowed:
                warnings.append(
                    f"{who} není zástupce kroku {label} ({owner}) — podpis zapsán jako zástup.")
            named = _human(signers.get(step)) if is_ai_owner(owner) else None
            if named and not _same_person(who, named) and not allowed \
                    and not (window == "design" and _same_person(who, owners.get("produkt"))):
                warnings.append(
                    f"Za {label} (AI náhrada) je určený podepisující {named}, "
                    f"podepsal {who} — podpis zapsán jako zástup.")
        kind = _signer_kind(window, who, owner, owners, core, ai=ai,
                            designated=_designated(window, owner, owners, risk, signers))
        if kind == "autor kódu" and not blocked:
            head = "OK — potvrdil autor kódu"
            if risk == "production":
                warnings.append(
                    f"{who} je autor kódu — u production nechte bezpečnost podepsat někoho, "
                    "kdo kód nepsal (Decider nebo DPO); právní kontrolu (GDPR, smlouvy) "
                    "autor kódu nepokrývá.")
            else:
                warnings.append(
                    f"{who} je autor kódu — u pilotu dovoleno, zapíšu jako „potvrdil autor "
                    "kódu“; právní kontrolu (GDPR, smlouvy) tím nepokrývá — doporučeno nechat "
                    "přečíst Deciderem nebo DPO.")
        artefact = f"**Checkpoint {label}** — {head} · {who} · {now}\n\n{note.strip()}\n"
        artefact += f"\n_signed_by_role: {kind}_" + (f" · _ai_agent: {agent_name}_" if agent_name else "") + "\n"
        if countersigned:
            artefact += f"\n_Potvrzuje AI draft ({prior[1]})._\n"
        for track in WINDOWS[window]["tracks"]:
            conn.execute(
                """
                INSERT INTO triage (project_id, track, status, artefact_md, signed_by, signed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, track) DO UPDATE SET
                  status = excluded.status, artefact_md = excluded.artefact_md,
                  signed_by = excluded.signed_by, signed_at = excluded.signed_at
                """,
                (pid, track, status, artefact, who),
            )
        audit(conn, action=f"checkpoint.{window}", target_type="project", target_id=pid,
              actor=current_actor(),
              payload={"slug": slug, "by": who, "status": status, "note": note, "ai": ai,
                       "signed_by_role": kind, "ai_agent": agent_name,
                       "countersigned_ai_draft": countersigned,
                       "tracks": list(WINDOWS[window]["tracks"])})
    designated = _designated(window, owner, owners, risk, signers)
    log = _append_decision_log(slug, label, who, status, note, now, kind=kind,
                               agent=agent_name, signer=designated)
    next_step = _next_step(slug, window, status, owner, owners, risk, by=who, signers=signers)
    return {"slug": slug, "window": window, "label": label, "status": status,
            "tracks": list(WINDOWS[window]["tracks"]), "signed_by": who,
            "signed_by_role": kind, "ai_agent": agent_name,
            "ai_draft": status == "pending", "ai": ai,
            "countersigned_ai_draft": countersigned,
            "decision_log_repo": log, "warnings": warnings, "next_step": next_step}


def _signer_for(window: str, owner: str | None, owners: dict[str, str], risk: str,
                signers: dict[str, str] | None = None) -> str:
    designated = _designated(window, owner, owners, risk, signers)
    if designated:
        return designated
    decider = owners.get("byznys")      # krok bez člověka: určí Decider
    return decider if decider and not is_ai_owner(decider) else "<jméno člověka>"


def _next_step(slug: str, window: str, status: str, owner: str | None,
               owners: dict[str, str], risk: str, by: str = "",
               signers: dict[str, str] | None = None) -> str:
    signer = _signer_for(window, owner, owners, risk, signers)
    label = WINDOWS[window]["label"]
    if status == "blocked":
        return (f"{label} je zablokované — odblokuje {signer}. Až bude opraveno: "
                f'`pflanzer checkpoint --slug {slug} {window} --by "{signer}" --note "co je opraveno"`')
    if status == "pending":
        return (f"AI draft {label} musí potvrdit člověk — {signer}: "
                f'`pflanzer checkpoint --slug {slug} {window} --by "{signer}" --note "co jsem ověřil"`')
    from tool.cli.status import project_detail
    return str(project_detail(slug)["next_step"])


def _append_decision_log(slug: str, label: str, by: str, status: str, note: str,
                         now: str, *, kind: str = "", agent: str | None = None,
                         signer: str | None = None) -> str | None:
    """Append to `.pflanzer/decisions/<slug>.md` in the target repo (cwd), if present."""
    base = Path.cwd() / ".pflanzer"
    if not base.is_dir():
        return None
    path = base / "decisions" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"{BRAND_LINE}\n\n# Decision log — {slug}\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        if status == "pending":
            who = agent or _agent_from_who(by) or "AI"
            f.write(f"\n## Checkpoint — {label}\n\n"
                    f"- **Stav**: AI draft ({who}) — čeká na podpis: "
                    f"{signer or '„určete kdo“'} · {now}\n"
                    f"- **Poznámka**: {note.strip()}\n")
        else:
            role = f"- **Role podpisu**: {kind}\n" if kind else ""
            f.write(f"\n## Checkpoint — {label}\n\n- **Stav**: {status.upper()}\n"
                    f"- **Podepsal**: {by} · {now}\n{role}- **Poznámka**: {note.strip()}\n")
    return str(path.relative_to(Path.cwd()))


AI_OK_TEXT = "podepsáno AI — u throwaway stačí (ADR-0023)"
STATE_LABELS = {"ok": "podepsáno", "blocked": "BLOKOVÁNO",
                "pending": "AI draft čeká na podpis člověka", "čeká": "čeká"}
DESIGN_PENDING = "AI design čeká na potvrzení člověkem"


def _last_audit(conn: Any, pid: int) -> dict[str, dict[str, Any]]:
    """Latest `checkpoint.<window>` audit payload per window."""
    out: dict[str, dict[str, Any]] = {}
    for r in conn.execute(
            "SELECT action, payload_json FROM audit_log WHERE target_type = 'project' "
            "AND target_id = ? AND action LIKE 'checkpoint.%' ORDER BY id", (pid,)).fetchall():
        try:
            out[r[0].split(".", 1)[1]] = json.loads(r[1] or "{}")
        except (ValueError, TypeError):
            continue
    return out


def list_checkpoints(slug: str) -> list[dict[str, Any]]:
    from tool.cli.triage import load_risk_profile

    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(project_not_found_message(slug))
        pid = int(proj[0])
        owners = _load_owners(conn, pid)
        signers = _load_signers(conn, pid)
        risk = load_risk_profile(conn, pid)
        last = _last_audit(conn, pid)
        rows = {r[0]: r for r in conn.execute(
            "SELECT track, status, signed_by, signed_at FROM triage WHERE project_id = ?",
            (pid,)).fetchall()}
    out = []
    for key, w in WINDOWS.items():
        owner = owners.get(WINDOW_STEP[key])
        if key == "design":
            if not is_ai_owner(owner):
                continue            # design dělá člověk: okno není potřeba
            payload = last.get("design") or {}
            state = payload.get("status") if payload.get("status") in ("ok", "blocked") \
                else "pending"
            signer = payload.get("by")
        else:
            tracks = [rows.get(t) for t in w["tracks"]]
            statuses = {r[1] if r else "missing" for r in tracks}
            state = ("ok" if statuses == {"ok"} else
                     "blocked" if "blocked" in statuses else
                     "pending" if "pending" in statuses else "čeká")
            signer = next((r[2] for r in tracks if r and r[1] in ("ok", "blocked", "pending")),
                          None)
        out.append({"window": key, "label": w["label"], "state": state, "signed_by": signer,
                    "owner": owner_display(owner, WINDOW_STEP[key]) or None,
                    "signer": _signer_for(key, owner, owners, risk, signers),
                    "designated": _designated(key, owner, owners, risk, signers),
                    "ai_signer": (signers.get(WINDOW_STEP[key]) if is_ai_owner(owner) else None),
                    "note": (last.get(key) or {}).get("note") if state == "blocked" else None,
                    "ai_agent": ai_agent(owner, WINDOW_STEP[key]) if is_ai_owner(owner) else None,
                    "state_text": (DESIGN_PENDING if key == "design" and state == "pending"
                                   else AI_OK_TEXT if (state == "ok" and risk == "throwaway"
                                                       and str(signer or "").startswith("AI"))
                                   else STATE_LABELS[state])})
    return out


def checkpoint_summary(slug: str) -> list[dict[str, Any]]:
    """Podpisy oken pro SHIP.md / PR: window, state, signed_by, signer_kind, ai_agent, note.

    `signer_kind` = zástupce | zástup | autor kódu | AI draft (None = okno nepodepsané).
    U okna potvrzeného člověkem po AI draftu je `ai_agent` agent, který draft psal.
    Okno `design` je v seznamu jen při AI náhradě designu.
    """
    rows = list_checkpoints(slug)
    with transaction() as conn:
        pid = int(conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0])
        last = _last_audit(conn, pid)
    out = []
    for r in rows:
        payload = last.get(r["window"]) or {}
        signed = r["state"] in ("ok", "blocked", "pending") and bool(r["signed_by"])
        out.append({
            "window": r["window"], "label": r["label"], "state": r["state"],
            "signed_by": r["signed_by"],
            "signer_kind": payload.get("signed_by_role") if signed else None,
            "ai_agent": payload.get("ai_agent") if signed else None,
            "note": payload.get("note") if signed else None,
            "designated_signer": r.get("designated") if r.get("ai_signer") else None,
        })
    return out


def design_gate(slug: str) -> dict[str, Any]:
    """Blokuje potvrzení AI designu Ship? Pilot ne, production (customer-facing) ano."""
    from tool.cli.triage import load_risk_profile

    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(project_not_found_message(slug))
        risk = load_risk_profile(conn, int(proj[0]))
    row = next((r for r in list_checkpoints(slug) if r["window"] == "design"), None)
    if not row:
        return {"applies": False, "state": None, "blocks_ship": False, "message": ""}
    open_ = row["state"] != "ok"
    blocks = open_ and risk == "production"
    msg = ""
    if open_:
        msg = (f"Design: {row['owner']} — potvrdí {row['signer']} "
               f"(`pflanzer checkpoint --slug {slug} design --by \"{row['signer']}\" "
               "--note \"co jsem zkontroloval\"`)")
        if blocks:
            msg += " — u production blokuje Ship."
    return {"applies": True, "state": row["state"], "blocks_ship": blocks, "message": msg}


def main(argv: list[str] | None = None) -> None:
    p = CzechArgumentParser(prog="pflanzer checkpoint", description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("window", nargs="?", help="zadani | bezpecnost | provoz | design")
    p.add_argument("--by", default="", help="Kdo za krok cesty podepisuje (jméno z Kickoffu)")
    p.add_argument("--note", default="", help="Co se ověřilo / co chybí (povinné)")
    p.add_argument("--blocked", action="store_true", help="Okno neprošlo — blokuje Ship")
    p.add_argument("--ai", action="store_true",
                   help="AI draft (ADR-0023): pilot/production čeká na podpis člověka")
    p.add_argument("--agent", default=None, help="S --ai: který agent (např. security-expert)")
    p.add_argument("--list", action="store_true", help="Stav všech oken")
    p.add_argument("--json", action="store_true", help="Strojový výstup")
    args = p.parse_args(argv)
    try:
        if args.list or not args.window:
            with transaction() as conn:
                st = conn.execute("SELECT status FROM projects WHERE slug = ?",
                                  (args.slug,)).fetchone()
            if st and st[0] == "killed":
                raise ValueError(killed_message(args.slug))
            rows = list_checkpoints(args.slug)
            lines = []
            for r in rows:
                who = f" · {r['signed_by']}" if r["signed_by"] else ""
                owner = f" (zástupce: {r['owner']})" if r["owner"] else ""
                lines.append(f"{r['label']}: **{r['state_text']}**{who}{owner}")
            open_ = next((r for r in rows if r["state"] != "ok" and r["window"] != "zadani"), None)
            nxt = (f'`pflanzer checkpoint --slug {args.slug} {open_["window"]} '
                   f'--by "{open_["signer"]}" --note "…"`' if open_
                   else f"Všechna okna jsou podepsaná — `/pm ship {args.slug}`")
            phase = {"provoz": "checkpoint_provoz", "design": "checkpoint_design"}.get(
                open_["window"] if open_ else "", "checkpoint_bezpecnost")
            emit(rows, title=f"Checkpointy — {args.slug}", lines=lines, next_step=nxt,
                 tips=[] if args.json else tips_for_project(args.slug, phase, limit=2),
                 as_json=args.json)
            return
        out = sign(args.slug, args.window, by=args.by, note=args.note, blocked=args.blocked,
                   ai=args.ai, agent=args.agent)
    except ValueError as e:
        die(str(e))
        return
    state = {"ok": AI_OK_TEXT if out["ai"] else "podepsáno", "blocked": "BLOKOVÁNO",
             "pending": AI_DRAFT_MARK}[out["status"]]
    lines = [f"{out['label']}: **{state}** · {out['signed_by']}"
             + (f" ({out['signed_by_role']})" if out["signed_by_role"] not in ("zástupce",)
                and not out["ai"] else "")]
    if out["countersigned_ai_draft"]:
        lines.append("Člověk potvrdil AI draft — okno je podepsané.")
    if out["decision_log_repo"]:
        lines.append(f"Zapsáno do `{out['decision_log_repo']}`.")
    phase = {"provoz": "checkpoint_provoz", "design": "checkpoint_design"}.get(
        out["window"], "checkpoint_bezpecnost")
    ctx = {"blocked": out["status"] == "blocked"}
    tips = [] if args.json else tips_for_project(
        args.slug, "ai_stand_in" if out["ai"] else phase, ctx, limit=2)
    emit(out, title=f"Checkpoint {out['label']} zapsán", lines=lines,
         next_step=out["next_step"], tips=tips, warnings=out["warnings"], as_json=args.json)


if __name__ == "__main__":
    main()
