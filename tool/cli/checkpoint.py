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
    pflanzer checkpoint --slug S bezpecnost --by "Lucie" --note "OK s podmínkami" \\
        --conditions "CSRF; rate limit; DPA s dodavatelem"
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
    # Plný triage (stupeň Full): právo (DPIA) se podepisuje zvlášť, když ho triage odložil.
    "pravo": {"label": "Právo (DPIA)", "tracks": ("legal",)},
    # Jen AI náhrada designu: žádný triage track (CHECK má 4 hodnoty), podpis je v audit logu.
    "design": {"label": "Design (AI)", "tracks": ()},
}
# Pilot (Lean) bez osobních dat a bez AI Act triggeru: bezpečnost a provoz jsou JEDNO okno
# (20 min, jeden podpis). Právo se otevře jen při osobních datech / AI Act high.
MERGED = "bezpecnost-provoz"
MERGED_MINUTES = 20
WINDOWS[MERGED] = {"label": "Bezpečnost a provoz", "tracks": ("security", "legal", "platform")}
ALIASES = {"kickoff": "zadani", "discovery": "zadani", "security": "bezpecnost",
           "legal": "pravo", "dpia": "pravo", "platform": "provoz",
           "ops": "provoz", "ux": "design", "bezpecnost_provoz": MERGED,
           "bezpecnost-a-provoz": MERGED, "security-ops": MERGED}
# Okna, která u sloučeného projektu přebírá MERGED (staré návody `bezpecnost` / `provoz` fungují).
MERGED_ABSORBS = ("bezpecnost", "provoz")
SECURITY_WINDOWS = ("bezpecnost", MERGED)


# Okno -> krok cesty, jehož zástupce ho podepisuje.
WINDOW_STEP = {"zadani": "byznys", "bezpecnost": "bezpecnost", "provoz": "provoz",
               "design": "design", "pravo": "bezpecnost", MERGED: "bezpecnost"}
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
                         + " Okna: zadani | bezpecnost | pravo | provoz | design "
                         "(u pilotu bez osobních dat: bezpecnost-provoz).")
    return key


def is_merged_profile(risk: str | None, tier: str | None, data_class: str | None,
                      ai_act_tier: str | None) -> bool:
    """Pilot + Lean + bez osobních dat (třída < L3) + bez AI Act high = jedno okno Bezpečnost a provoz."""
    return (risk == "pilot" and tier == "lean"
            and str(data_class or "").upper() not in ("L3", "L4")
            and str(ai_act_tier or "").lower() not in ("high", "unacceptable"))


def merged_applies(conn: Any, pid: int, risk: str | None = None) -> bool:
    """Má projekt jedno okno Bezpečnost a provoz? Starší projekt s už podepsaným dílčím oknem
    nebo s plným triage zůstává u oddělených oken (podpisy se nepřepisují)."""
    from tool.cli.tier import infer_tier
    from tool.cli.triage import load_risk_profile
    try:
        risk = risk or load_risk_profile(conn, pid)
        if risk != "pilot":
            return False
        cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()}
        sel = "data_class, ai_act_tier, capacity_profile" + (", tier" if "tier" in cols else "")
        row = conn.execute(f"SELECT {sel} FROM projects WHERE id = ?", (pid,)).fetchone()
        if not row:
            return False
        tier = row[3] if len(row) > 3 and row[3] else infer_tier(conn, pid, row[2])
        if not is_merged_profile(risk, tier, row[0], row[1]):
            return False
        if any(a in _last_audit(conn, pid) for a in ("bezpecnost", "provoz", "pravo")):
            return False
        for r in conn.execute("SELECT artefact_md FROM triage WHERE project_id = ? AND track "
                              "IN ('security','legal','platform')", (pid,)).fetchall():
            if "Kickoff" not in (r[0] or "")[:80]:
                return False        # proběhl plný triage: okna zůstávají oddělená
        return True
    except Exception:  # noqa: BLE001 — poradní rozhodnutí, starší DB bez sloupců
        return False


def _merged_owner(owners: dict[str, str], signers: dict[str, str] | None = None) -> str | None:
    """Vlastník sloučeného okna: zástupce Bezpečnosti; když ho zastupuje AI bez určeného
    podepisujícího a provoz má člověka, tak zástupce Provozu."""
    sec, prov = owners.get("bezpecnost"), owners.get("provoz")
    if _human(sec):
        return sec
    if sec and _human((signers or {}).get("bezpecnost") or (signers or {}).get("provoz")):
        return sec                          # AI draft má určeného podepisujícího
    if _human(prov):
        return prov
    return sec or prov


def _merged_signers(signers: dict[str, str]) -> dict[str, str]:
    out = dict(signers)
    if not out.get("bezpecnost") and out.get("provoz"):
        out["bezpecnost"] = out["provoz"]
    return out


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
    if window in SECURITY_WINDOWS and _is_code_author(who, owners, core):
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


def _legal_signer(value: str | None) -> str | None:
    """Jméno, které plný triage určil k podpisu práva (DPO); „NOT SIGNED — navržený signer X“ → X."""
    v = (value or "").strip()
    m = re.search(r"(?i)navr[žz]en\w*\s+signer\s+(.+)$", v)
    if m:
        v = m.group(1)
    v = re.sub(r"\s*\(.*$", "", v).strip()
    if not v or not _human(v) or re.search(r"(?i)pending|agent|unsigned|not signed", v):
        return None
    return v


def guidance_core(window: str, owners: dict[str, str], risk: str) -> str:
    """Kdo smí podepsat okno, které zastupuje AI a nikdo není určen (bez názvu okna)."""
    if risk == "throwaway":
        return "u throwaway stačí AI pre-check (ADR-0023)"
    decider, pdm, dev = (_human(owners.get(k)) for k in ("byznys", "produkt", "vyvoj"))

    def named(role: str, who: str | None) -> str:
        return f"{role} ({who})" if who else role

    if risk == "production":
        if window == "pravo":
            who_can = f"{named('Decider', decider)} nebo DPO/právník"
        elif window == "provoz":
            who_can = f"{named('Decider', decider)} nebo člověk odpovědný za provoz"
        elif window == MERGED:
            who_can = (f"{named('Decider', decider)} nebo člověk odpovědný za bezpečnost "
                       "či provoz")
        elif window == "bezpecnost":
            who_can = f"{named('Decider', decider)} nebo člověk odpovědný za bezpečnost"
        else:
            who_can = named("Decider", decider)
        no_dev = f"; ne autor kódu{f' ({dev})' if dev else ''}"
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
                signers: dict[str, str] | None = None,
                core: list[str] | None = None) -> str | None:
    """Člověk, který je pro okno určen k podpisu (None = nikdo nebyl určen).

    U production nepodepisuje AI náhradu autor kódu (ADR-0023: podepisuje člověk odpovědný
    za oblast / Decider) — takový „určený“ se ignoruje.
    """
    if _human(owner):
        return owner
    named = _human((signers or {}).get(WINDOW_STEP[window]))
    if named and is_ai_owner(owner):
        if risk == "production" and window != "design" and _is_code_author(named, owners, core or []):
            return None
        return named          # tým výslovně určil, kdo AI draft podepíše (ai_signers)
    if window == "provoz" and risk == "pilot" and _human(owners.get("vyvoj")):
        return owners["vyvoj"]
    if window == "design":
        return _human(owners.get("produkt")) or _human(owners.get("byznys"))
    return None


def _agent_from_who(who: str | None) -> str | None:
    m = re.match(r"AI \((.+)\)", who or "")
    return m.group(1) if m else None


def parse_conditions(raw: Any) -> list[str]:
    """`--conditions` (opakovatelné, v jednom zápisu oddělené středníkem nebo novým řádkem)."""
    items = [raw] if isinstance(raw, str) else list(raw or [])
    out: list[str] = []
    for item in items:
        for part in re.split(r"[;\n]", str(item or "")):
            part = part.strip().lstrip("-•* ").strip()
            if part and part not in out:
                out.append(part)
    return out


def sign(slug: str, window: str, *, by: str = "", note: str, blocked: bool = False,
         ai: bool = False, agent: str | None = None,
         conditions: Any = None, waive: Any = None,
         rationale: str = "") -> dict[str, Any]:
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
    cond_list = parse_conditions(conditions)
    waive_ids = parse_conditions(waive)
    if waive_ids and not (rationale or "").strip():
        raise ValueError("--waive vyžaduje --rationale \"…\": proč se podmínka z triage odpouští "
                         "(zapisuje se do audit logu).\nPříklad:\n"
                         '  pflanzer checkpoint --slug <slug> bezpecnost --by "Jana" --note "…" '
                         '--waive K3 --rationale "řeší se v jiném projektu"')
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z").strip()
    warnings: list[str] = []
    countersigned = False
    with transaction() as conn:
        proj = conn.execute("SELECT id, status FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(project_not_found_message(slug))
        if proj[1] == "killed":
            raise ValueError(killed_message(slug))
        pid = int(proj[0])
        merged = merged_applies(conn, pid)
        if window in MERGED_ABSORBS and merged:
            window = MERGED
            warnings.append("U tohoto pilotu jsou bezpečnost a provoz jedno okno — podepsáno "
                            "okno Bezpečnost a provoz.")
        elif window == MERGED and not merged:
            raise ValueError(
                "Okno bezpecnost-provoz je jen pro pilot (Lean) bez osobních dat. Tento projekt "
                "má okna zvlášť: `bezpecnost` a `provoz` (případně `pravo`).")
        label = WINDOWS[window]["label"]
        step = WINDOW_STEP[window]
        owners = _load_owners(conn, pid)
        signers = _load_signers(conn, pid)
        core = _load_core(conn, pid)
        owner = owners.get(step)
        if window == MERGED:
            signers = _merged_signers(signers)
            owner = _merged_owner(owners, signers)
        if window == "pravo":
            leg = conn.execute("SELECT status, artefact_md FROM triage WHERE project_id = ? "
                               "AND track = 'legal'", (pid,)).fetchone()
            separate = bool(leg) and leg[0] in ("deferred", "blocked") \
                and "Kickoff" not in (leg[1] or "")[:80]
            if not separate and "pravo" not in _last_audit(conn, pid):
                raise ValueError(
                    "Právo se podepisuje spolu s bezpečností (plný triage ho neodložil): "
                    f'`pflanzer checkpoint --slug {slug} bezpecnost --by "<jméno>" '
                    '--note "co jste ověřili"`.')
            # Právo (DPIA) podepisuje ten, koho jmenoval plný triage (typicky DPO), ne vlastník
            # kroku Bezpečnost & právo.
            lg = conn.execute("SELECT signed_by FROM triage WHERE project_id = ? AND "
                              "track = 'legal'", (pid,)).fetchone()
            named = _legal_signer(lg[0] if lg else None)
            if named:
                owner = named
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
                if not _designated(window, owner, owners, risk, signers, core):
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
            if window == MERGED and any(
                    _human(owners.get(k)) and _same_person(who, owners.get(k))
                    for k in ("bezpecnost", "provoz")):
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
        if (not ai and not blocked and risk == "production" and window != "design"
                and (is_ai_owner(owner) or countersigned)
                and _is_code_author(who, owners, core)):
            raise ValueError(
                f"U production nesmí AI náhradu okna {label} potvrdit autor kódu ({who}) — "
                "podepisuje člověk odpovědný za oblast nebo Decider (ADR-0023). "
                f"{guidance_core(window, owners, risk).capitalize()}.\n"
                f'Příklad: pflanzer checkpoint --slug {slug} {window} --by "<jméno>" '
                '--note "co jsem ověřil"')
        kind = _signer_kind(window, who, owner, owners, core, ai=ai,
                            designated=_designated(window, owner, owners, risk, signers, core))
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
        if window in (*SECURITY_WINDOWS, "pravo") and not blocked:
            from tool.cli.session_2 import open_criticals, overridden_criticals
            sec_re = re.compile(r"(?i)bezpe|secur|pr[aá]v|legal|gdpr|compliance")
            risky = [c for c in overridden_criticals(conn, pid)
                     if sec_re.search(str(c.get("department") or ""))
                     and not _critical_resolved(conn, c["id"])]
            for c in risky:
                warnings.append(
                    f"⚠ Na vítězi je přebitý critical od {c.get('submitted_by') or 'neznámého autora'}: "
                    f"{_clip(c.get('rationale'))} — podepisujete i s ním? "
                    f"(Decider ho přebil: {_clip(c['reason'], 80)})")
            known = {c["id"] for c in risky}
            for c in open_criticals(conn, pid):
                if sec_re.search(str(c.get("department") or "")) and c["id"] not in known:
                    warnings.append(
                        f"⚠ Otevřený critical od {c.get('submitted_by') or 'neznámého autora'} "
                        f"({c['department']}): {_clip(c.get('rationale'))} — podepisujete i s ním?")
        tracks = list(WINDOWS[window]["tracks"])
        if window == "bezpecnost":
            legal = conn.execute(
                "SELECT status, artefact_md FROM triage WHERE project_id = ? AND track = 'legal'",
                (pid,)).fetchone()
            from_full_triage = bool(legal) and "Kickoff" not in (legal[1] or "")[:80]
            if legal and legal[0] in ("deferred", "blocked") and from_full_triage:
                # Triage právo vědomě odložil (např. DPIA) — podpis bezpečnosti ho nepřepíše.
                tracks = ["security"]
                warnings.append(
                    "Právo zůstává odložené z triage (např. DPIA) — podepisuje se zvlášť: "
                    f'`pflanzer checkpoint --slug {slug} pravo --by "<DPO>" --note "DPIA hotová"`.')
        if window == "bezpecnost" and "legal" in tracks and "pravo" in _last_audit(conn, pid):
            lg2 = conn.execute("SELECT status FROM triage WHERE project_id = ? AND track = 'legal'",
                               (pid,)).fetchone()
            if lg2 and lg2[0] in ("ok", "blocked"):
                tracks = [t for t in tracks if t != "legal"]   # DPIA podpis okna Právo zůstává
        # Podmínky: re-sign je SLUČUJE s dřívějšími (nikdy nepřepisuje); podmínky z triage
        # podpis převezme, nebo je vědomě odpustí (--waive ID --rationale …).
        from tool.cli.triage import triage_conditions
        prev_ok = (_last_audit(conn, pid).get(window) or {}).get("status") == "ok"
        prev_conds = conditions_by_window(conn, pid).get(window, [])
        seen_c = {_norm_cond(c) for c in prev_conds}
        added = [c for c in cond_list if _norm_cond(c) not in seen_c]
        all_conds = [*prev_conds, *added]
        resigned = prev_ok and not ai and not blocked
        tri = [c for c in triage_conditions(conn, pid) if c["track"] in tracks]
        waived: list[dict[str, Any]] = []
        for tok in waive_ids:
            hit = [c for c in tri if tok.lower() in (c["id"].lower(), c["key"].lower())]
            if not hit:
                have = ", ".join(c["key"] for c in tri) or "žádné"
                raise ValueError(f"Podmínka ‚{tok}‘ z triage v okně {label} není. Dostupné: {have}.")
            for c in hit:
                waived.append({"key": c["key"], "id": c["id"], "text": c["text"],
                               "rationale": rationale.strip()})
        waived_keys = {w["key"] for w in waived}
        taken = [c for c in tri if status == "ok" and c["key"] not in waived_keys
                 and c["state"] != "waived"] if not blocked else []
        artefact = f"**Checkpoint {label}** — {head} · {who} · {now}\n\n{note.strip()}\n"
        artefact += f"\n_signed_by_role: {kind}_" + (f" · _ai_agent: {agent_name}_" if agent_name else "") + "\n"
        if all_conds:
            artefact += "\n**Podmínky podpisu** (musí splnit PR):\n" + "".join(
                f"- {c}\n" for c in all_conds)
        if taken:
            artefact += "\n**Podmínky z triage** (potvrzeno podpisem):\n" + "".join(
                f"- [{c['id']}] {c['text']}\n" for c in taken)
        if waived:
            artefact += "\n**Odpuštěné podmínky z triage:**\n" + "".join(
                f"- [{w['id']}] {w['text']} — {w['rationale']}\n" for w in waived)
        if countersigned:
            artefact += f"\n_Potvrzuje AI draft ({prior[1]})._\n"
        for track in tracks:
            prev = conn.execute("SELECT artefact_md FROM triage WHERE project_id = ? AND track = ?",
                                (pid, track)).fetchone()
            merged = merge_artefact(prev[0] if prev else "", window, label, artefact)
            conn.execute(
                """
                INSERT INTO triage (project_id, track, status, artefact_md, signed_by, signed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, track) DO UPDATE SET
                  status = excluded.status, artefact_md = excluded.artefact_md,
                  signed_by = excluded.signed_by, signed_at = excluded.signed_at
                """,
                (pid, track, status, merged, who),
            )
        audit(conn, action=f"checkpoint.{window}", target_type="project", target_id=pid,
              actor=current_actor(),
              payload={"slug": slug, "by": who, "status": status, "note": note, "ai": ai,
                       "signed_by_role": kind, "ai_agent": agent_name,
                       "countersigned_ai_draft": countersigned,
                       "conditions": cond_list,
                       "taken_conditions": [c["key"] for c in taken],
                       "waived_conditions": waived,
                       "tracks": tracks})
    designated = _designated(window, owner, owners, risk, signers, core)
    log = _append_decision_log(slug, label, who, status, note, now, kind=kind,
                               agent=agent_name, signer=designated)
    charter_updated = _stamp_charter(slug, window, who, status)
    next_step = _next_step(slug, window, status, owner, owners, risk, by=who, signers=signers,
                           core=core)
    return {"slug": slug, "window": window, "label": label, "status": status,
            "tracks": tracks, "signed_by": who,
            "signed_by_role": kind, "ai_agent": agent_name,
            "ai_draft": status == "pending", "ai": ai,
            "countersigned_ai_draft": countersigned,
            "conditions": all_conds, "added_conditions": added, "resigned": resigned,
            "triage_conditions": [{"key": c["key"], "id": c["id"], "text": c["text"]}
                                  for c in taken],
            "waived_conditions": waived,
            "open_triage_conditions": [{"key": c["key"], "id": c["id"], "text": c["text"]}
                                       for c in tri if c["state"] == "open"
                                       and c["key"] not in waived_keys
                                       and c["key"] not in {t["key"] for t in taken}],
            "charter_updated": charter_updated,
            "decision_log_repo": log, "warnings": warnings, "next_step": next_step}


def merge_artefact(previous: str | None, window: str, label: str, block: str) -> str:
    """Poznámku okna PŘIPOJÍ k artefaktu stopy (jméno + datum jsou v bloku); nepřepisuje cizí text.

    Dřívější blok téhož okna (re-sign) se nahradí; artefakt triage a bloky jiných oken zůstanou.
    """
    marker = f"<!-- cp:{window} -->"
    prev = (previous or "").strip()
    if prev:
        prev = re.sub(re.escape(marker) + r".*?(?=<!-- cp:|\Z)", "", prev, flags=re.S).strip()
        if prev.startswith(f"**Checkpoint {label}**") and "<!-- cp:" not in prev:
            prev = ""        # starý jednoblokový zápis téhož okna
    body = f"{marker}\n{block.strip()}\n"
    return f"{prev}\n\n{body}" if prev else body


def _clip(text: str | None, n: int = 120) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[: n - 1].rsplit(" ", 1)[0] + "…"


def _critical_resolved(conn: Any, fid: int) -> bool:
    try:
        r = conn.execute("SELECT resolved_at FROM feedback WHERE id = ?", (fid,)).fetchone()
    except Exception:  # noqa: BLE001 — starší schéma bez resolved_at
        return False
    return bool(r and r[0])


def _signer_for(window: str, owner: str | None, owners: dict[str, str], risk: str,
                signers: dict[str, str] | None = None,
                core: list[str] | None = None) -> str:
    designated = _designated(window, owner, owners, risk, signers, core)
    if designated:
        return designated
    decider = owners.get("byznys")      # krok bez člověka: určí Decider
    return decider if decider and not is_ai_owner(decider) else "<jméno člověka>"


def _next_step(slug: str, window: str, status: str, owner: str | None,
               owners: dict[str, str], risk: str, by: str = "",
               signers: dict[str, str] | None = None,
               core: list[str] | None = None) -> str:
    signer = _signer_for(window, owner, owners, risk, signers, core)
    label = WINDOWS[window]["label"]
    if status == "blocked":
        return (f"{label} je zablokované — odblokuje {signer}. Až bude opraveno: "
                f'`pflanzer checkpoint --slug {slug} {window} --by "{signer}" --note "co je opraveno"`')
    if status == "pending":
        return (f"AI draft {label} musí potvrdit člověk — {signer}: "
                f'`pflanzer checkpoint --slug {slug} {window} --by "{signer}" --note "co jsem ověřil"`')
    from tool.cli.status import project_detail
    return str(project_detail(slug)["next_step"])


CHARTER_SIGN_LINES = {
    "zadani": "- Decider podpis (datum + jméno):",
    "bezpecnost": "- Checkpoint Bezpečnost & právo",
    "provoz": "- Checkpoint Provoz",
    MERGED: ("- Checkpoint Bezpečnost & právo", "- Checkpoint Provoz"),
}


def _stamp_charter(slug: str, window: str, who: str, status: str) -> bool:
    """Přepíše řádek okna v sekci Sign-off charteru (`PENDING` → jméno + datum).

    Jen pro okna, jejichž řádek charter má; ostatní text zůstane. Vrací True, když se soubor změnil.
    BLOKOVÁNO se do charteru nezapisuje jako podpis (řádek zůstane čekající).
    """
    prefix = CHARTER_SIGN_LINES.get(window)
    if not prefix or status == "blocked":
        return False
    prefixes = (prefix,) if isinstance(prefix, str) else tuple(prefix)
    from tool.cli import charter as _charter
    path = Path(_charter.CHARTER_DIR) / f"{slug}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    day = datetime.now().astimezone().strftime("%Y-%m-%d")
    mark = f"podepsáno: {who}, {day}" if status == "ok" else \
        f"AI draft ({who}, {day}) — čeká na podpis člověka"
    out, changed = [], False
    for line in text.split("\n"):
        if line.startswith(prefixes):
            head = line.split(":", 1)[0]
            new = f"{head}: {mark}"
            if new != line:
                line, changed = new, True
        out.append(line)
    if changed:
        path.write_text("\n".join(out), encoding="utf-8")
    return changed


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


def _norm_cond(text: str) -> str:
    return " ".join(str(text or "").casefold().split())


def conditions_by_window(conn: Any, pid: int) -> dict[str, list[str]]:
    """Podmínky z podpisů oken (audit `checkpoint.<okno>`, klíč `conditions`).

    Podmínky všech podpisů okna se SLUČUJÍ (dedupe, pořadí podle vzniku): re-sign podmínky
    nepřepisuje ani nemaže. Zablokovaný zápis podmínky nemění.
    """
    out: dict[str, list[str]] = {}
    for r in conn.execute(
            "SELECT action, payload_json FROM audit_log WHERE target_type = 'project' "
            "AND target_id = ? AND action LIKE 'checkpoint.%' ORDER BY id", (pid,)).fetchall():
        try:
            payload = json.loads(r[1] or "{}")
        except (ValueError, TypeError):
            continue
        conds = payload.get("conditions")
        if isinstance(conds, list) and conds and payload.get("status") != "blocked":
            have = out.setdefault(r[0].split(".", 1)[1], [])
            seen = {_norm_cond(c) for c in have}
            for c in conds:
                if str(c).strip() and _norm_cond(c) not in seen:
                    have.append(str(c))
                    seen.add(_norm_cond(c))
    return out


def signature_conditions(slug: str) -> list[dict[str, str]]:
    """Ploský seznam podmínek: {text, window, label, by, state, rationale}.

    `state`: signed (z `--conditions`) | taken (z triage, potvrzeno podpisem okna) |
    open (z triage, zatím nikdo nepotvrdil) | waived (z triage, odpuštěno s důvodem).
    """
    from tool.cli.triage import triage_conditions

    rows = checkpoint_summary(slug)
    labels = {r["window"]: r["label"] for r in rows}
    with transaction() as conn:
        found = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not found:
            return []
        conds = conditions_by_window(conn, int(found[0]))
        tri = triage_conditions(conn, int(found[0]))
    out: list[dict[str, str]] = []
    for r in rows:
        if r["state"] != "ok":
            continue
        for c in conds.get(r["window"], []):
            out.append({"text": c, "window": r["window"], "label": r["label"],
                        "by": str(r.get("signed_by") or ""), "state": "signed", "rationale": ""})
    for want in ("taken", "open", "waived"):
        for c in tri:
            if c["state"] != want:
                continue
            win = c["window"] or c["window_for"]
            if win in (*MERGED_ABSORBS, "pravo") and MERGED in labels:
                win = MERGED
            out.append({"text": f"[{c['id']}] {c['text']}", "window": win,
                        "label": labels.get(win) or WINDOWS.get(win, {}).get("label", win),
                        "by": str(c.get("by") or ""), "state": want,
                        "rationale": str(c.get("rationale") or "")})
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
        core = _load_core(conn, pid)
        risk = load_risk_profile(conn, pid)
        merged = merged_applies(conn, pid, risk)
        last = _last_audit(conn, pid)
        rows = {r[0]: r for r in conn.execute(
            "SELECT track, status, signed_by, signed_at FROM triage WHERE project_id = ?",
            (pid,)).fetchall()}
    lg0, sec0 = rows.get("legal"), rows.get("security")
    # Právo (DPIA) je samostatné okno, když se od bezpečnosti odpojilo (odložené v plném
    # triage) nebo už bylo samostatně podepsáno; pak se okno Bezpečnost posuzuje jen podle
    # vlastního tracku security (jinak by „podepsáno“ pořád svítilo jako „čeká“).
    pravo_split = "pravo" in last or not (
        not lg0 or (sec0 and lg0[1] == sec0[1] and lg0[2] == sec0[2]) or lg0[1] == "čeká")
    out = []
    if merged:
        signers = _merged_signers(signers)
    for key, w in WINDOWS.items():
        if key == MERGED and not merged:
            continue
        if merged and key in (*MERGED_ABSORBS, "pravo"):
            continue            # sloučené okno nahrazuje bezpečnost + provoz (+ právo)
        owner = owners.get(WINDOW_STEP[key])
        if key == MERGED:
            owner = _merged_owner(owners, signers)
        if key == "design":
            if not is_ai_owner(owner):
                continue            # design dělá člověk: okno není potřeba
            payload = last.get("design") or {}
            state = payload.get("status") if payload.get("status") in ("ok", "blocked") \
                else "pending"
            signer = payload.get("by")
        else:
            if key == "pravo":
                if not pravo_split:
                    continue
                named = _legal_signer(lg0[2] if lg0 else None)
                if named:
                    owner = named
            wtracks = ["security"] if (key == "bezpecnost" and pravo_split) else w["tracks"]
            tracks = [rows.get(t) for t in wtracks]
            statuses = {r[1] if r else "missing" for r in tracks}
            state = ("ok" if statuses == {"ok"} else
                     "blocked" if "blocked" in statuses else
                     "pending" if "pending" in statuses else "čeká")
            signer = next((r[2] for r in tracks if r and r[1] in ("ok", "blocked", "pending")),
                          None)
            if risk == "throwaway" and key != "zadani" and state == "čeká":
                continue        # demo: okna se nevyžadují (AI pre-check se ukáže, pokud je)
        out.append({"window": key, "label": w["label"], "state": state, "signed_by": signer,
                    "owner": owner_display(owner, WINDOW_STEP[key]) or None,
                    "signer": _signer_for(key, owner, owners, risk, signers, core),
                    "designated": _designated(key, owner, owners, risk, signers, core),
                    "ai_signer": (signers.get(WINDOW_STEP[key]) if is_ai_owner(owner) else None),
                    "minutes": MERGED_MINUTES if key == MERGED else None,
                    "signed_at": next((r[3] for r in tracks if r and r[1] == "ok"), None)
                    if key != "design" else None,
                    "note": (last.get(key) or {}).get("note") if state == "blocked" else None,
                    "ai_agent": ai_agent(owner, WINDOW_STEP[key]) if is_ai_owner(owner) else None,
                    "state_text": (DESIGN_PENDING if key == "design" and state == "pending"
                                   else AI_OK_TEXT if (state == "ok" and risk == "throwaway"
                                                       and str(signer or "").startswith("AI"))
                                   else STATE_LABELS[state])})
    by_key = {r["window"]: r for r in out}
    sec_row, law = by_key.get("bezpecnost"), by_key.get("pravo")
    if sec_row and law and sec_row["state"] == "ok" and law["state"] != "ok":
        from tool.cli._compat import local_date
        day = local_date(sec_row.get("signed_at"))
        stamp = ", ".join(x for x in (str(sec_row["signed_by"] or ""),
                                      day.strftime("%d. %m. %Y") if day else "") if x)
        who = law["owner"] or law["signer"] or "DPO"
        what = {"blocked": f"Právo (DPIA) BLOKOVÁNO — {who}",
                "pending": f"Právo (DPIA): AI draft čeká na podpis — {who}"}.get(
            law["state"], f"čeká Právo (DPIA) — {who}")
        sec_row["state_text"] = f"Bezpečnost podepsána ({stamp}) · {what}"
        sec_row["waiting_for"] = "pravo"
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
        conds = conditions_by_window(conn, pid)
    out = []
    for r in rows:
        payload = last.get(r["window"]) or {}
        signed = r["state"] in ("ok", "blocked", "pending") and bool(r["signed_by"])
        out.append({
            "window": r["window"], "label": r["label"], "state": r["state"],
            "signed_by": r["signed_by"],
            "signer_kind": payload.get("signed_by_role") if signed else None,
            "ai_agent": payload.get("ai_agent") if signed else None,
            "owner_ai": r.get("ai_agent"),   # krok zastupuje AI už v Kickoffu (path_owners „AI:…“)
            "note": payload.get("note") if signed else None,
            "designated_signer": r.get("designated") if r.get("ai_signer") else None,
            "conditions": conds.get(r["window"], []) if r["state"] == "ok" else [],
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
    p.add_argument("window", nargs="?", help="zadani | bezpecnost | pravo | provoz | design | bezpecnost-provoz (pilot bez osobních dat: "
                   "bezpecnost i provoz podepíšou toto jedno okno; pravo jen při odloženém právu z plného triage)")
    p.add_argument("--by", default="", help="Kdo za krok cesty podepisuje (jméno z Kickoffu)")
    p.add_argument("--note", default="", help="Co se ověřilo / co chybí (povinné)")
    p.add_argument("--conditions", action="append", default=[],
                   help='Podmínky podpisu, které musí splnit PR (opakovatelné nebo '
                        '"CSRF; rate limit; DPA"); jdou do SHIP.md, těla PR a compliance.md')
    p.add_argument("--waive", action="append", default=[], metavar="ID",
                   help="Vědomě odpustit podmínku z triage (např. K3 nebo security:K3; "
                        "opakovatelné); vyžaduje --rationale")
    p.add_argument("--rationale", default="", help="S --waive: proč se podmínka odpouští")
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
                who = f" · {r['signed_by']}" if r["signed_by"] and not r.get("waiting_for") else ""
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
                   ai=args.ai, agent=args.agent, conditions=args.conditions,
                   waive=args.waive, rationale=args.rationale)
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
    if out.get("resigned"):
        if out["added_conditions"]:
            lines.append("Okno už bylo podepsané; doplněné podmínky: "
                         + "; ".join(out["added_conditions"]) + f" (celkem {len(out['conditions'])}).")
        else:
            lines.append("Okno už bylo podepsané; podmínky zůstávají beze změny"
                         + (f" ({len(out['conditions'])})." if out["conditions"] else "."))
    elif out.get("conditions"):
        lines.append(f"Podmínky podpisu ({len(out['conditions'])}): " + "; ".join(out["conditions"])
                     + " — propíšou se do SHIP.md a těla PR.")
    if out.get("triage_conditions"):
        lines.append(f"Podmínky z triage převzaté podpisem ({len(out['triage_conditions'])}): "
                     + "; ".join(f"[{c['id']}] {c['text']}" for c in out["triage_conditions"])
                     + " — podpisem je potvrzujete; odpustit: "
                     "--waive ID --rationale \"…\".")
    if out.get("waived_conditions"):
        lines.append("Odpuštěno: " + "; ".join(f"[{w['id']}] ({w['rationale']})"
                                              for w in out["waived_conditions"]))
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
