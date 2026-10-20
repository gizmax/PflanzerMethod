"""Hub (pilot 28): jedna formulace přihlášení k náhledu, validace vítěze u hlasu Go,
termín sběru feedbacku ve „Vaší úloze“."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")
pytest.importorskip("httpx")

from tests.test_pilot22_hub import env  # noqa: E402,F401

SRC = Path(__file__).resolve().parents[1] / "tool" / "web" / "frontend" / "src"
LOGIN = "Při otevření náhledu zadejte libovolné jméno a heslo k náhledům."


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_single_login_text_everywhere() -> None:
    assert f'"{LOGIN}"' in _read("lib/task.ts")
    assert "PREVIEW_LOGIN_TEXT" in _read("components/PreviewLogin.tsx")
    for p in SRC.rglob("*.ts*"):
        t = p.read_text(encoding="utf-8")
        assert "uživatel <strong>" not in t, p.name
        assert "(uživatel ${" not in t and "uživatel ${l.user}" not in t, p.name
        assert "pflanzer“" not in t


def test_vote_winner_validated_with_visible_message() -> None:
    s = _read("components/SilentVote.tsx")
    assert "Vyberte vítěznou variantu" in s
    assert 'id="vote-winner-err"' in s and 'aria-describedby' in s
    assert "noValidate" in s
    assert "voteErrorText" in s and "Array.isArray(detail)" in s


def test_deadline_in_my_task_source() -> None:
    p = _read("pages/ProjectPage.tsx")
    assert "Feedback do:" in p and "data.feedback_deadline" in p
    assert "feedback_deadline" in _read("lib/types.ts")


def test_backend_reads_share_deadline(env: dict, monkeypatch, tmp_path) -> None:  # noqa: F811
    from tests.test_expert_hub import who
    monkeypatch.setenv("PFLANZER_DATA", str(tmp_path))
    c = env["client"]
    assert c.get("/api/projects/demo", headers=who("x")).json()["feedback_deadline"] is None
    d = tmp_path / "preview"
    d.mkdir()
    (d / "demo.share.json").write_text(json.dumps({"deadline": "pátek 17:00"}), encoding="utf-8")
    got = c.get("/api/projects/demo", headers=who("x")).json()["feedback_deadline"]
    assert got == "pátek 17:00"
