"""Brand rule (CLAUDE.md): "PM" means Pflanzer Method and may appear only in the
`/pm` command name, never in text. Product manager is "PdM"."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STANDALONE_PM = re.compile(r"(?<![/\w-])PM(?![\w-])")
SCANNED = ["README.md", "docs", ".claude", "tool", "website"]
SUFFIXES = {".md", ".py", ".json", ".template", ".yml", ".yaml", ".ts", ".tsx", ".html", ".js"}
# Lines that state the rule itself.
ALLOWED = {
    ".claude/commands/pm.md": "zkratka je jen v názvu commandu",
    "docs/methodology/glossary.md": "„PM\"",
}


def _files() -> list[Path]:
    out: list[Path] = []
    for entry in SCANNED:
        p = REPO / entry
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out += [f for f in p.rglob("*") if f.is_file() and f.suffix in SUFFIXES
                    and "node_modules" not in f.parts]
    return out


def test_no_standalone_pm_in_text() -> None:
    offenders = []
    for f in _files():
        rel = f.relative_to(REPO).as_posix()
        for no, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if not STANDALONE_PM.search(line):
                continue
            allowed = ALLOWED.get(rel)
            if allowed and allowed in line:
                continue
            if rel == "docs/methodology/glossary.md" and line.startswith("### PM"):
                continue
            offenders.append(f"{rel}:{no}: {line.strip()[:100]}")
    hint = "Standalone 'PM' in text (use 'PdM' for produkt manažer):\n"
    assert not offenders, hint + "\n".join(offenders)
