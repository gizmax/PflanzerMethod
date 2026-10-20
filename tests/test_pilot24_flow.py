"""Pilot 24: pořadí record -> share, libovolné jméno v preview proxy, okno Zadání, Design za AI."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import pytest

from tests.test_pilot23_share import env  # noqa: F401
from tool.cli import checkpoint, preview, share, status

ROOT = Path(__file__).resolve().parents[1]


def _basic(user: str, pw: str) -> str:
    return "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()


def _authorized(header: str | None, pw: str = "tajne:heslo") -> bool:
    handler_cls = preview._make_handler(1, pw, "A")
    h = handler_cls.__new__(handler_cls)
    h.headers = {"Authorization": header} if header is not None else {}  # type: ignore[assignment]
    return bool(h._authorized())  # type: ignore[attr-defined]


def test_preview_accepts_any_username_with_right_password() -> None:
    assert _authorized(_basic("pflanzer", "tajne:heslo"))
    assert _authorized(_basic("tomas", "tajne:heslo"))
    assert _authorized(_basic("", "tajne:heslo"))


def test_preview_rejects_wrong_password_or_malformed() -> None:
    assert not _authorized(_basic("pflanzer", "spatne"))
    assert not _authorized(_basic("tomas", "tajne"))
    assert not _authorized(None)
    assert not _authorized("Basic " + base64.b64encode(b"tajne:heslo-bez-jmena").decode())
    assert not _authorized("Basic %%%")


def test_preview_compare_is_constant_time() -> None:
    src = (ROOT / "tool/cli/preview.py").read_text(encoding="utf-8")
    assert "hmac.compare_digest(given_pw, expected_pw)" in src


def test_share_warns_when_build_not_recorded(env: dict[str, Any],  # noqa: F811
                                             monkeypatch: pytest.MonkeyPatch,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(status, "_last_build", lambda slug: {})
    share.main(["--slug", "demo", "--tunnel", "none", "--password", "pw1"])
    out = capsys.readouterr().out
    assert "Build ještě není zapsaný — hub zatím varianty neukáže" in out
    assert "pflanzer record --spec" in out
    assert "NEODESÍLAT" in out
    assert "Zpráva pro kolegy (přeposlat):" not in out


def test_share_normal_after_record(env: dict[str, Any],  # noqa: F811
                                   monkeypatch: pytest.MonkeyPatch,
                                   capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(status, "_last_build", lambda slug: {"slug": slug})
    share.main(["--slug", "demo", "--tunnel", "none", "--password", "pw1"])
    out = capsys.readouterr().out
    assert "Zpráva pro kolegy (přeposlat):" in out
    assert "NEODESÍLAT" not in out and "Build ještě není zapsaný" not in out


def test_status_after_record_points_to_share() -> None:
    phase, nxt = status._phase("session_1", "none", 0, 0)
    assert nxt == "pflanzer share --slug <slug>"


def test_order_record_before_share_in_docs_and_help() -> None:
    zacni = (ROOT / "docs/zacni.md").read_text(encoding="utf-8")
    assert zacni.index("pflanzer record --spec soubor.json") < zacni.index(
        "pflanzer share --slug S` | builder")
    assert len(zacni.splitlines()) <= 170
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.index("`record` → `share`") > 0
    helptxt = (ROOT / "tool/bin/pflanzer").read_text(encoding="utf-8")
    assert helptxt.index("# 3. zápis hodnocení Buildu") < helptxt.index("# 4. sdílení")


OWNERS = {"byznys": "Dana Nováková", "produkt": "Petr Produkt", "design": "AI",
          "vyvoj": "Tomáš Vývoj", "bezpecnost": "Jana Bezpečná", "provoz": "Karel Provoz"}


def test_zadani_signed_at_kickoff_and_visible_in_status(tmp_db: Path, bare_repo: Path) -> None:
    from tests.conftest import bootstrap_project, file_url
    out = bootstrap_project(slug="z24", target_repo_url=file_url(bare_repo),
                            metric="10 z 15 lidí otevře přehled",
                            kill_criteria="po 4 týdnech bez liftu", path_owners=OWNERS)
    slug = out["slug"]
    cps = {c["window"]: c for c in checkpoint.list_checkpoints(slug)}
    assert cps["zadani"]["state"] == "ok"
    d = status.project_detail(slug)
    lines = "\n".join(status.detail_lines(d))
    assert "Zadání (Kickoff)" in lines


def test_zadani_by_role_word_explains_name(tmp_db: Path, bare_repo: Path) -> None:
    from tests.conftest import bootstrap_project, file_url
    out = bootstrap_project(slug="z24b", target_repo_url=file_url(bare_repo), path_owners=OWNERS)
    with pytest.raises(ValueError) as ei:
        checkpoint.sign(out["slug"], "zadani", by="Decider", note="x")
    assert "jméno Decidera" in str(ei.value)


def test_docs_describe_zadani_and_design() -> None:
    zacni = (ROOT / "docs/zacni.md").read_text(encoding="utf-8")
    assert "Zadání se\npodepíše samo při Kickoffu" in zacni
    assert '--by "Decider"' not in zacni
    assert "design --by" in zacni and "jen, když AI návrh vzniká až dodatečně" in zacni
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "lockfile" in readme
