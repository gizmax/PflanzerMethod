"""AI usage visibility (audit N16) — Claude Code token usage per variant.

Three Claude Code sessions run in parallel in the variant worktrees
(`worktree.py`: `<targets>/<slug>-<X>`, extra repos `<slug>-<X>-<role>`).
This module reads the session transcripts Claude Code keeps on this machine
and sums token usage per variant, so SHIP.md can say "the cycle cost X".
It is visibility only — there is no limit and nothing is blocked.

Transcript location (Claude Code):
    <claude_home>/projects/<escaped-cwd>/<session-id>.jsonl
    <claude_home>/projects/<escaped-cwd>/<session-id>/subagents/agent-*.jsonl
`<claude_home>` is `$CLAUDE_CONFIG_DIR` when set (Claude Code's documented
override of its config/data directory), else `~/.claude`. `<escaped-cwd>` is
the absolute working directory with every character outside `[A-Za-z0-9-]`
replaced by `-`.

Record shape used (everything else is ignored):
    {"type": "assistant", "timestamp": "...Z",
     "message": {"id": "msg_...", "model": "...",
                 "usage": {"input_tokens", "output_tokens",
                           "cache_creation_input_tokens",
                           "cache_read_input_tokens"}}}
One API response is streamed as several records sharing `message.id`;
usage is counted once per id (max per field). Unknown record types, missing
fields and corrupt JSON lines are skipped.

Price (optional): `$PFLANZER_AI_PRICES` or `<repo>/pflanzer.prices.json`
(`{model_prefix: {"input", "output", "cache_write", "cache_read"}}` in USD
per 1M tokens, longest prefix wins). Prices are never hardcoded — see
`tool/templates/README-ai-usage.md`.

Usage:
    python3 tool/cli/ai_usage.py --slug checkout            # table
    python3 tool/cli/ai_usage.py --slug checkout --json
    python3 tool/cli/ai_usage.py --slug checkout --record   # snapshot -> ai_usage table
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli import worktree  # noqa: E402
from tool.cli.db import audit, transaction  # noqa: E402

BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"
PRICES_ENV = "PFLANZER_AI_PRICES"
PRICES_FILE = REPO_ROOT / "pflanzer.prices.json"
PRICES_TEMPLATE = "tool/templates/pflanzer.prices.json.template"
CLAUDE_CONFIG_ENV = "CLAUDE_CONFIG_DIR"
# Claude Code shortens very long escaped directory names (prefix + hash);
# such directories are matched by prefix and verified via the records' `cwd`.
MAX_ESCAPED_LEN = 200
CWD_PROBE_LINES = 50

# Summary key -> usage field in the transcript.
TOKEN_FIELDS: dict[str, str] = {
    "input": "input_tokens",
    "output": "output_tokens",
    "cache_creation": "cache_creation_input_tokens",
    "cache_read": "cache_read_input_tokens",
}
# Summary key -> price list key (USD per 1M tokens).
PRICE_FIELDS: dict[str, str] = {
    "input": "input",
    "output": "output",
    "cache_creation": "cache_write",
    "cache_read": "cache_read",
}
# Claude Code writes locally generated (non-API) assistant messages under this model.
SYNTHETIC_MODELS = {"<synthetic>"}


# --------------------------------------------------------------------------
# Transcript discovery
# --------------------------------------------------------------------------


def escape_project_dir(path: str | Path) -> str:
    """Claude Code project directory name for a working directory."""
    return re.sub(r"[^A-Za-z0-9-]", "-", str(path))


def claude_home_dir(claude_home: Path | None = None) -> Path:
    if claude_home is not None:
        return Path(claude_home)
    env = os.environ.get(CLAUDE_CONFIG_ENV)
    if env:
        return Path(env).expanduser()
    return Path.home() / ".claude"


def _path_variants(worktree_path: Path) -> list[Path]:
    """The worktree as given (absolute) and symlink-resolved, de-duplicated."""
    out: list[Path] = []
    for p in (Path(os.path.abspath(worktree_path)), worktree_path.resolve()):
        if p not in out:
            out.append(p)
    return out


def _cwd_matches(transcript: Path, cwds: set[str]) -> bool:
    try:
        with transcript.open(encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= CWD_PROBE_LINES:
                    break
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict) and isinstance(rec.get("cwd"), str):
                    return rec["cwd"] in cwds
    except OSError:
        return False
    return False


def _glob_escape(text: str) -> str:
    return re.sub(r"([*?\[])", r"[\1]", text)


def _dir_transcripts(d: Path) -> list[Path]:
    return sorted(d.glob("*.jsonl")) + sorted(d.glob("*/subagents/*.jsonl"))


def find_transcripts(worktree: Path, claude_home: Path | None = None) -> list[Path]:
    """All Claude Code transcripts (sessions + their subagents) started in `worktree`.

    Sessions started in a subdirectory of the worktree are not included (their
    escaped name would also prefix-match sibling worktrees such as `<slug>-A-be`).
    """
    projects = claude_home_dir(claude_home) / "projects"
    if not projects.is_dir():
        return []
    paths = _path_variants(Path(worktree))
    found: list[Path] = []
    for p in paths:
        name = escape_project_dir(p)
        d = projects / name
        if d.is_dir():
            found.extend(_dir_transcripts(d))
        if len(name) > MAX_ESCAPED_LEN:
            cwds = {str(x) for x in paths}
            prefix = name[:MAX_ESCAPED_LEN]
            for cand in projects.glob(f"{_glob_escape(prefix)}*"):
                if cand.is_dir() and cand.name != name:
                    found.extend(t for t in _dir_transcripts(cand) if _cwd_matches(t, cwds))
    seen: set[Path] = set()
    return [t for t in found if not (t in seen or seen.add(t))]


# --------------------------------------------------------------------------
# Summarising
# --------------------------------------------------------------------------


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)) and value > 0:
        return int(value)
    return 0


def _empty_tokens() -> dict[str, int]:
    return {k: 0 for k in TOKEN_FIELDS}


def _session_key(transcript: Path) -> str:
    """Subagent transcripts belong to their parent session (<sid>/subagents/…)."""
    if transcript.parent.name == "subagents":
        return transcript.parent.parent.name
    return transcript.stem


def summarize_usage(paths: Iterable[Path], prices: dict[str, dict[str, float]] | None = None,
                    ) -> dict[str, Any]:
    """Token usage over transcripts: per model + totals + session count + time window.

    `sessions` counts distinct sessions (one top-level `.jsonl` each; subagent
    transcripts are attributed to their parent session).
    """
    messages: dict[str, dict[str, Any]] = {}
    sessions: set[str] = set()
    model_sessions: dict[str, set[str]] = {}
    first_ts: str | None = None
    last_ts: str | None = None
    files = 0
    skipped = 0
    for transcript in paths:
        transcript = Path(transcript)
        try:
            fh = transcript.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files += 1
        skey = _session_key(transcript)
        sessions.add(skey)
        with fh:
            for lineno, line in enumerate(fh):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    skipped += 1
                    continue
                if not isinstance(rec, dict):
                    continue
                ts = rec.get("timestamp")
                if isinstance(ts, str) and ts:
                    first_ts = ts if first_ts is None or ts < first_ts else first_ts
                    last_ts = ts if last_ts is None or ts > last_ts else last_ts
                if rec.get("type") != "assistant":
                    continue
                msg = rec.get("message")
                if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                    continue
                model = msg.get("model") if isinstance(msg.get("model"), str) else "unknown"
                if model in SYNTHETIC_MODELS:
                    continue
                usage = msg["usage"]
                tokens = {k: _int(usage.get(f)) for k, f in TOKEN_FIELDS.items()}
                mid = msg.get("id") or rec.get("requestId") or f"{transcript}:{lineno}"
                prev = messages.get(mid)
                if prev is None:
                    messages[mid] = {"model": model, **tokens}
                else:  # streamed blocks of one response: count once, keep max per field
                    for k, v in tokens.items():
                        prev[k] = max(prev[k], v)
                model_sessions.setdefault(model, set()).add(skey)

    models: dict[str, dict[str, Any]] = {}
    for m in messages.values():
        row = models.setdefault(m["model"], {"messages": 0, **_empty_tokens()})
        row["messages"] += 1
        for k in TOKEN_FIELDS:
            row[k] += m[k]
    for model, row in models.items():
        row["sessions"] = len(model_sessions.get(model, ()))

    totals = _empty_tokens()
    for row in models.values():
        for k in TOKEN_FIELDS:
            totals[k] += row[k]
    summary: dict[str, Any] = {
        "sessions": len(sessions),
        "files": files,
        "messages": len(messages),
        **totals,
        "models": dict(sorted(models.items())),
        "first_ts": first_ts,
        "last_ts": last_ts,
        "skipped_lines": skipped,
        "est_usd": None,
        "unpriced_models": [],
    }
    if prices:
        apply_prices(summary, prices)
    return summary


# --------------------------------------------------------------------------
# Optional pricing (never hardcoded)
# --------------------------------------------------------------------------


def load_prices() -> tuple[dict[str, dict[str, float]] | None, str | None]:
    """Price list from `$PFLANZER_AI_PRICES` or `<repo>/pflanzer.prices.json`.

    Returns (prices, source_path) or (None, None). Keys starting with `_` are
    comments; a model entry whose rates are all missing/null is ignored.
    """
    env = os.environ.get(PRICES_ENV)
    path = Path(env).expanduser() if env else PRICES_FILE
    if not path.is_file():
        if env:
            print(f"[ai_usage] warn: {PRICES_ENV}={env} neexistuje — cena se nevykazuje.",
                  file=sys.stderr)
        return None, None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[ai_usage] warn: ceník {path} nejde načíst ({exc}) — cena se nevykazuje.",
              file=sys.stderr)
        return None, None
    if not isinstance(raw, dict):
        return None, None
    prices: dict[str, dict[str, float]] = {}
    for prefix, rates in raw.items():
        if prefix.startswith("_") or not isinstance(rates, dict):
            continue
        clean = {k: float(v) for k, v in rates.items()
                 if k in PRICE_FIELDS.values() and isinstance(v, (int, float))
                 and not isinstance(v, bool) and v >= 0}
        if clean:
            prices[prefix] = clean
    return (prices or None), (str(path) if prices else None)


def price_for(model: str, prices: dict[str, dict[str, float]]) -> dict[str, float] | None:
    best = max((p for p in prices if model.startswith(p)), key=len, default=None)
    return prices[best] if best is not None else None


def _usd(row: dict[str, Any], rate: dict[str, float]) -> float:
    return sum(row[k] * rate.get(pk, 0.0) for k, pk in PRICE_FIELDS.items()) / 1_000_000


def apply_prices(summary: dict[str, Any], prices: dict[str, dict[str, float]]) -> dict[str, Any]:
    """Fill `est_usd` per model and in total; unmatched models go to `unpriced_models`."""
    total = 0.0
    priced = False
    unpriced: list[str] = []
    for model, row in summary["models"].items():
        rate = price_for(model, prices)
        if rate is None:
            row["est_usd"] = None
            unpriced.append(model)
            continue
        row["est_usd"] = round(_usd(row, rate), 6)
        total += row["est_usd"]
        priced = True
    summary["est_usd"] = round(total, 6) if priced else None
    summary["unpriced_models"] = unpriced
    return summary


# --------------------------------------------------------------------------
# Project level
# --------------------------------------------------------------------------


def usage_for_project(slug: str, claude_home: Path | None = None,
                      prices: dict[str, dict[str, float]] | None = None,
                      ) -> dict[str, dict[str, Any]]:
    """{variant: summary} over every worktree of every target repo of the project.

    Paths are computed (no existence check) so transcripts still count after a
    worktree was cleaned up. Variants without any transcript are omitted.
    `prices=None` loads the optional price list (see `load_prices`).
    """
    repos = worktree.load_target_repos(slug)
    if prices is None:
        prices, _ = load_prices()
    out: dict[str, dict[str, Any]] = {}
    for variant in worktree.PARALLEL_VARIANTS + worktree.MOB_VARIANTS:
        transcripts: list[Path] = []
        wts: list[str] = []
        for _repo, wt in worktree.variant_worktrees(slug, repos, variant):
            found = find_transcripts(wt, claude_home)
            if found:
                transcripts.extend(found)
                wts.append(str(wt))
        if transcripts:
            summary = summarize_usage(transcripts, prices)
            summary["worktrees"] = wts
            out[variant] = summary
    return out


def cycle_totals(usage: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tot: dict[str, Any] = {"sessions": 0, "messages": 0, **_empty_tokens(), "est_usd": None}
    for s in usage.values():
        for k in ("sessions", "messages", *TOKEN_FIELDS):
            tot[k] += int(s.get(k) or 0)
        if s.get("est_usd") is not None:
            tot["est_usd"] = round((tot["est_usd"] or 0.0) + float(s["est_usd"]), 6)
    return tot


def _source_label() -> str:
    return f"claude-code-jsonl@{socket.gethostname()}"


def record_snapshot(slug: str, usage: dict[str, dict[str, Any]] | None = None,
                    ) -> dict[str, Any]:
    """Write one row per (variant, model); replaces the previous snapshot of that key."""
    usage = usage_for_project(slug) if usage is None else usage
    measured_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    source = _source_label()
    rows = 0
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(f"Projekt '{slug}' neexistuje.")
        pid = int(proj[0])
        for variant, s in usage.items():
            for model, m in s["models"].items():
                conn.execute(
                    """
                    INSERT INTO ai_usage (project_id, variant, model, sessions, messages,
                        input_tokens, output_tokens, cache_creation_tokens,
                        cache_read_tokens, est_usd, measured_at, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, variant, model) DO UPDATE SET
                        sessions = excluded.sessions, messages = excluded.messages,
                        input_tokens = excluded.input_tokens,
                        output_tokens = excluded.output_tokens,
                        cache_creation_tokens = excluded.cache_creation_tokens,
                        cache_read_tokens = excluded.cache_read_tokens,
                        est_usd = excluded.est_usd, measured_at = excluded.measured_at,
                        source = excluded.source
                    """,
                    (pid, variant, model, m["sessions"], m["messages"], m["input"],
                     m["output"], m["cache_creation"], m["cache_read"], m.get("est_usd"),
                     measured_at, source),
                )
                rows += 1
        audit(conn, action="ai_usage.record", target_type="project", target_id=pid,
              payload={"slug": slug, "rows": rows, "variants": sorted(usage),
                       "source": source})
    return {"slug": slug, "rows": rows, "measured_at": measured_at, "source": source}


def load_snapshot(slug: str) -> dict[str, dict[str, Any]]:
    """Last recorded snapshot in the same shape as `usage_for_project` (fallback)."""
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT a.variant, a.model, a.sessions, a.messages, a.input_tokens,
                   a.output_tokens, a.cache_creation_tokens, a.cache_read_tokens,
                   a.est_usd, a.measured_at, a.source
            FROM ai_usage a JOIN projects p ON p.id = a.project_id
            WHERE p.slug = ? ORDER BY a.variant, a.model
            """, (slug,),
        ).fetchall()
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        s = out.setdefault(r[0], {
            "sessions": 0, "messages": 0, **_empty_tokens(), "models": {},
            "est_usd": None, "unpriced_models": [], "measured_at": r[9], "source": r[10],
        })
        m = {"sessions": r[2], "messages": r[3], "input": r[4], "output": r[5],
             "cache_creation": r[6], "cache_read": r[7], "est_usd": r[8]}
        s["models"][r[1]] = m
        # Per-model session counts may overlap; the variant shows the max.
        s["sessions"] = max(s["sessions"], int(r[2] or 0))
        s["messages"] += int(r[3] or 0)
        for k in TOKEN_FIELDS:
            s[k] += int(m[k] or 0)
        if r[8] is None:
            s["unpriced_models"].append(r[1])
        else:
            s["est_usd"] = round((s["est_usd"] or 0.0) + float(r[8]), 6)
        s["measured_at"] = max(s["measured_at"] or "", r[9] or "") or None
    return out


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _n(value: Any) -> str:
    return f"{int(value or 0):,}".replace(",", " ")


def _usd_str(value: Any) -> str:
    return "—" if value is None else f"${float(value):,.2f}"


def render_markdown(usage: dict[str, dict[str, Any]], *, origin: str = "live",
                    heading: str = "## AI náklady (viditelnost)") -> str:
    """SHIP.md section. `origin` = "live" (fresh measurement) or "snapshot" (DB)."""
    lines = [heading, ""]
    if not usage:
        lines.append("Žádné session logy Claude Code pro worktrees tohoto projektu na tomto stroji.")
        return "\n".join(lines) + "\n"
    priced = any(s.get("est_usd") is not None for s in usage.values())
    lines += [
        "Tokeny ze session logů Claude Code (`~/.claude/projects/…`) pro worktrees tohoto "
        "projektu **na tomto stroji** — jiné stroje ani hosted buildery (v0, Lovable, …) "
        "se nezapočítají. Jen viditelnost, žádný limit.",
        "",
    ]
    headers = ["Varianta", "Sessions", "Zprávy", "Input", "Output", "Cache write", "Cache read"]
    if priced:
        headers.append("USD (odhad)")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join("---" for _ in headers) + "|")

    def row(label: str, s: dict[str, Any]) -> str:
        cells = [label, _n(s["sessions"]), _n(s["messages"]), _n(s["input"]),
                 _n(s["output"]), _n(s["cache_creation"]), _n(s["cache_read"])]
        if priced:
            cells.append(_usd_str(s.get("est_usd")))
        return "| " + " | ".join(cells) + " |"

    for variant in sorted(usage):
        lines.append(row(f"`{variant}`", usage[variant]))
    tot = cycle_totals(usage)
    lines.append(row("**Celkem za cyklus**", tot))
    lines.append("")

    models = sorted({m for s in usage.values() for m in s.get("models", {})})
    if models:
        lines.append("- **Modely**: " + ", ".join(f"`{m}`" for m in models))
    firsts = [s["first_ts"] for s in usage.values() if s.get("first_ts")]
    lasts = [s["last_ts"] for s in usage.values() if s.get("last_ts")]
    if firsts and lasts:
        lines.append(f"- **Okno**: {min(firsts)} → {max(lasts)}")
    if origin == "snapshot":
        measured = max((s.get("measured_at") or "" for s in usage.values()), default="")
        sources = sorted({s.get("source") or "?" for s in usage.values()})
        lines.append(f"- **Zdroj**: poslední snapshot z DB (`ai_usage`, {measured} UTC, "
                     f"{', '.join(sources)}) — živé logy na tomto stroji nenalezeny")
    else:
        lines.append("- **Zdroj**: živé měření při renderu "
                     "(snapshot: `python3 tool/cli/ai_usage.py --slug <slug> --record`)")
    unpriced = sorted({m for s in usage.values() for m in s.get("unpriced_models", [])})
    if priced and unpriced:
        lines.append("- ⚠ Bez ceny v ceníku (v USD nezapočteno): "
                     + ", ".join(f"`{m}`" for m in unpriced))
    if not priced:
        lines.append(
            f"- Cena se nevykazuje (chybí ceník). Zapnutí: zkopíruj `{PRICES_TEMPLATE}` "
            "do `pflanzer.prices.json` v kořeni PflanzerMethod repa (nebo nastav "
            f"`{PRICES_ENV}=<cesta>`) a doplň USD za 1M tokenů — viz "
            "`tool/templates/README-ai-usage.md`."
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--record", action="store_true",
                   help="Write the snapshot into the ai_usage table (replaces the previous one)")
    p.add_argument("--claude-home", type=Path, default=None,
                   help="Claude Code data dir (default: $CLAUDE_CONFIG_DIR or ~/.claude)")
    args = p.parse_args(argv)

    try:
        usage = usage_for_project(args.slug, claude_home=args.claude_home)
        recorded = record_snapshot(args.slug, usage) if args.record else None
    except ValueError as exc:
        print(f"[ai_usage] chyba: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"slug": args.slug, "variants": usage,
                          "total": cycle_totals(usage), "recorded": recorded},
                         ensure_ascii=False, indent=2))
    else:
        print(BRAND_LINE)
        print()
        print(render_markdown(usage, heading=f"# AI náklady — {args.slug}"))
        if recorded:
            print(f"Snapshot zapsán do DB (`ai_usage`): {recorded['rows']} řádků, "
                  f"{recorded['measured_at']} UTC.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
