"""Hub (pilot 26): tiché hlasování bez předvybrané volby, radia s hodnotou a label,
heslo k náhledu skryté za tlačítkem."""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "tool" / "web" / "frontend" / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_vote_has_no_default_choice() -> None:
    s = _read("components/SilentVote.tsx")
    assert 'useState<VoteChoice | "">("")' in s
    assert 'setChoice("go")' not in s
    assert "Vyberte Go, Iterate nebo Kill" in s
    # validace volby je dřív než kontrola vítěze
    assert s.index("setErr(\"Vyberte Go, Iterate nebo Kill.\")") < s.index(
        "setWinnerErr(\"Vyberte vítěznou variantu\")")
    # vítěz nemá výchozí hodnotu
    assert 'useState("")' in s and '<option value="">' in s


def test_vote_radios_have_value_id_and_label() -> None:
    s = _read("components/SilentVote.tsx")
    m = re.search(
        r'<label key=\{c\} htmlFor=\{`\$\{idp\}-vote-\$\{c\}`\}.*?<input.*?/>', s, re.S)
    assert m, "radio hlasování musí mít label for + input"
    tag = m.group(0)
    assert 'id={`${idp}-vote-${c}`}' in tag
    assert 'name="vote"' in tag and "value={c}" in tag
    assert 'value="on"' not in s


def test_feedback_severity_radios_have_values() -> None:
    s = _read("pages/FeedbackForm.tsx")
    assert 'useState<Feedback["severity"] | "">("")' in s
    assert 'id={`sev-${s}`} type="radio" name="severity" value={s}' in s
    assert "htmlFor={`sev-${s}`}" in s


def test_all_radios_have_value() -> None:
    for p in SRC.rglob("*.tsx"):
        for tag in re.findall(r'<input\b[^\n]*?type="radio"[^\n]*', p.read_text(encoding="utf-8")):
            assert "value=" in tag, f"{p.name}: radio bez value"


def test_preview_password_hidden_behind_button() -> None:
    c = _read("components/PreviewLogin.tsx")
    assert "Zobrazit heslo" in c and "Skrýt heslo" in c
    assert "Heslo k náhledům — neposílejte ho dál mimo tým." in c
    assert "useState(false)" in c
    # heslo se vykreslí jen při shown
    assert re.search(r"shown \? \(\s*<p>Heslo:", c)
    for page in ("pages/ProjectPage.tsx", "pages/CompareVariants.tsx"):
        s = _read(page)
        assert "<PreviewLogin" in s
        assert "previewLoginText" not in s
