"""Expertní panel (UX + nováček): zacni.md na jednu stránku, faq.md s kotvami, /pm od nuly."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OLD_NAMES = ("session_3", "session_2", "pflanzer vote", "quick_session bootstrap")


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _slug(heading: str) -> str:
    return re.sub(r"\s+", "-", re.sub(r"[`*?!,.:()/|&]", "", heading.strip().lower())
                  .replace("…", "")).strip("-")


def test_zacni_is_one_page_and_links_faq() -> None:
    text = _read("docs/zacni.md")
    assert len(text.splitlines()) <= 170
    assert "faq.md" in text
    for name in OLD_NAMES:
        assert name not in text, name
    for step in ("pflanzer share", "pflanzer record", "decide", "ship"):
        assert step in text


def test_faq_exists_with_anchors_and_no_old_names() -> None:
    faq = _read("docs/faq.md")
    for heading in ("## Co když nemáme…", "### …designéra", "## Když se něco zasekne",
                    "## Co měřit", "## Tunel, LAN a preview", "## Výjimky a přebití prahu"):
        assert heading in faq, heading
    for name in OLD_NAMES:
        assert name not in faq, name
    assert faq.lstrip().startswith("# FAQ")


def test_zacni_links_to_faq_resolve() -> None:
    faq = _read("docs/faq.md")
    heads = {_slug(m.group(1)) for m in re.finditer(r"^#{1,3} (.+)$", faq, re.M)}
    targets = set(re.findall(r"faq\.md#([^)\s]+)", _read("docs/zacni.md") + _read("README.md")
                             + _read("docs/postup.md")))
    assert targets
    missing = [t for t in targets if t not in heads]
    assert not missing, missing


def test_user_docs_use_unified_names() -> None:
    for rel in ("README.md", "docs/zacni.md", "docs/postup.md", "docs/pro-decidera.md",
                "docs/methodology/00-tldr.md", ".claude/commands/pm.md",
                ".claude/commands/pflanzer-charter.md", ".claude/commands/pflanzer.md"):
        text = _read(rel)
        for name in ("pflanzer vote", "pflanzer session_3", "pflanzer session_2",
                     "quick_session bootstrap", "quick_session prompts"):
            assert name not in text, (rel, name)


def test_every_doc_starts_with_audience_sentence() -> None:
    for rel in ("README.md", "docs/zacni.md", "docs/faq.md", "docs/postup.md",
                "docs/pro-decidera.md", "docs/methodology/00-tldr.md"):
        assert "Pro koho:" in "\n".join(_read(rel).splitlines()[:8]), rel


def test_async_introduced_as_feedback_collection() -> None:
    text = _read("docs/zacni.md")
    assert "Sběr feedbacku (Async)" in text
    assert text.count("Async") == 1


def test_pm_bootstraps_uninitialised_repo_and_asks_one_question() -> None:
    pm = _read(".claude/commands/pm.md")
    assert "pflanzer init" in pm and "pflanzer doctor" in pm
    assert "INTEGRATION_GUIDE" in pm and "Od nuly" in pm
    charter = _read(".claude/commands/pflanzer-charter.md")
    for text in (pm, charter):
        assert "Jak vážné" in text
    assert "demo" in charter and "pilot" in charter and "ostré" in charter
    assert "výjimka, ne" in charter and "mob" in charter


def test_feedback_severity_labels() -> None:
    cmd = _read(".claude/commands/pflanzer-feedback-pull.md")
    assert "Kritické" in cmd and "Důležité" in cmd and "Drobné" in cmd
