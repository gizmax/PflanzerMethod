"""Role cards (audit N15): catalog `card` data, generator, static cards in docs."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tool.cli import roles

BRAND = "Pflanzer Method | pflanzer.cz/method"
STANDALONE_ABBREV = re.compile(r"(?<![/\w])PM(?!\w)")
STATIC_DIR = roles.REPO_ROOT / "docs" / "methodology" / "role-cards"


def _card_files(out_dir: Path) -> list[Path]:
    return sorted(p for p in out_dir.glob("*.md") if p.name != "README.md")


def test_every_role_has_complete_card() -> None:
    catalog = roles.load_catalog()
    assert len(catalog["roles"]) == 18
    presences = set(catalog["card_presence"])
    for role in catalog["roles"]:
        card = role.get("card")
        assert card, f"role #{role['idx']} has no card"
        for field in roles.CARD_FIELDS:
            assert card.get(field), f"role #{role['idx']}: empty card.{field}"
        assert 2 <= len(card["bring"]) <= 4, role["idx"]
        assert 2 <= len(card["red_flags"]) <= 3, role["idx"]
        assert card["sign_off"], role["idx"]
        for tier in roles.TIERS:
            slot = card["when_in_room"][tier]
            assert slot["presence"] in presences, (role["idx"], tier)
            assert slot["note"].strip(), (role["idx"], tier)
        vote = card["vote_on"]
        assert vote["note"].strip(), role["idx"]
        assert set(vote["dimensions"]) <= {"user_value", "effort", "risk", "strategic_fit"}
        assert set(vote["focus"]) <= set(vote["dimensions"]), role["idx"]
        assert roles.missing_card_fields(role) == []


def test_cards_all_renders_18_branded_one_pagers(tmp_path: Path) -> None:
    out = tmp_path / "cards"
    roles.main(["cards", "--all", "--out", str(out)])
    files = _card_files(out)
    assert len(files) == 18
    assert (out / "README.md").is_file()
    for path in [*files, out / "README.md"]:
        text = path.read_text(encoding="utf-8")
        assert text.splitlines()[0] == BRAND, path.name
        assert not STANDALONE_ABBREV.search(text), f"{path.name}: standalone abbreviation"
    for path in files:
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 60, path.name
    readme = (out / "README.md").read_text(encoding="utf-8")
    for path in files:
        assert f"]({path.name})" in readme


def test_cards_tier_highlights_one_row(tmp_path: Path) -> None:
    out = roles.generate_cards(out=tmp_path / "c", tier="lean")
    text = Path(out["cards"][6]).read_text(encoding="utf-8")  # #7 Security
    marked = [ln for ln in text.splitlines() if "tvůj stupeň" in ln]
    assert len(marked) == 1 and "Lean" in marked[0]
    with pytest.raises(ValueError, match="tier"):
        roles.generate_cards(out=tmp_path / "x", tier="huge")


def test_cards_for_project_only_selected_roles(project: dict[str, Any], tmp_path: Path) -> None:
    out = tmp_path / "project-cards"
    result = roles.generate_cards(slug=project["slug"], out=out)
    names = [p.name for p in _card_files(out)]
    # conftest bootstrap: room [1, 2, 3, 4, 6]
    assert [n[:2] for n in names] == ["01", "02", "03", "04", "06"]
    assert result["cards_count"] == 5
    assert result["tier"] == "quick"  # /pm live bootstrap with the default profile

    fe = (out / "04-frontend-vibe-coding-lead.md").read_text(encoding="utf-8")
    assert fe.splitlines()[0] == BRAND
    assert "Petr Frontend" in fe
    assert "Dana Deciderová" in fe
    assert project["slug"] in fe
    assert "▶ Quick" in fe
    assert not STANDALONE_ABBREV.search(fe)
    ux = (out / "06-ux-designer.md").read_text(encoding="utf-8")
    assert "doplň jméno" in ux  # no human_owner for UX in the fixture
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "Petr Frontend" in readme and "05-" not in readme

    # Explicit tier wins over the DB guess; default out dir is data/role-cards/<slug>.
    again = roles.generate_cards(slug=project["slug"], tier="full")
    assert again["tier"] == "full"
    assert Path(again["out_dir"]).name == project["slug"]
    assert "▶ Full" in Path(again["cards"][0]).read_text(encoding="utf-8")


def test_cards_cli_errors(tmp_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        roles.main(["cards", "--slug", "does-not-exist"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert err.startswith(BRAND) and "does-not-exist" in err
    with pytest.raises(SystemExit):
        roles.main([])  # legacy mode still needs --spec


def test_static_cards_are_up_to_date(tmp_path: Path) -> None:
    fresh = tmp_path / "fresh"
    result = roles.generate_cards(out=fresh)
    assert result["cards_count"] == 18
    expected = {p.name: p.read_text(encoding="utf-8") for p in fresh.glob("*.md")}
    actual = {p.name: p.read_text(encoding="utf-8") for p in STATIC_DIR.glob("*.md")}
    assert sorted(actual) == sorted(expected), (
        "docs/methodology/role-cards/ is out of sync — run "
        "`python3 tool/cli/roles.py cards --all`"
    )
    stale = [name for name in expected if actual[name] != expected[name]]
    assert not stale, f"Regenerate static role cards (`roles.py cards --all`): {stale}"


def test_catalog_readers_unaffected() -> None:
    """The additive `card` section keeps the fields legacy readers use."""
    raw = json.loads(roles.CATALOG_PATH.read_text(encoding="utf-8"))
    for role in raw["roles"]:
        for key in ("idx", "label", "default_status", "ai_proxy_mode", "trigger", "expert_agent"):
            assert key in role
