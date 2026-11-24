import json
from pathlib import Path

import pytest

from doorcfg.messages import (
    DEFAULT_LANGUAGE,
    MESSAGES_DIR,
    available_languages,
    load_messages,
)
from doorcfg.models import DoorConfiguration
from doorcfg.rules import RuleSet, validate

REFERENCE = load_messages(DEFAULT_LANGUAGE)


def test_english_comes_first() -> None:
    assert available_languages()[0] == DEFAULT_LANGUAGE


@pytest.mark.parametrize("language", available_languages())
def test_every_language_file_is_complete(language: str) -> None:
    """A new language must have every text English has."""
    with (MESSAGES_DIR / f"{language}.json").open(encoding="utf-8") as handle:
        raw = json.load(handle)
    assert raw["language_name"].strip()
    assert set(raw["text"]) == set(REFERENCE.text)
    assert set(raw["violations"]) == set(REFERENCE.violations)
    assert all(value.strip() for value in [*raw["text"].values(), *raw["violations"].values()])


@pytest.mark.parametrize("language", available_languages())
def test_placeholders_survive_translation(language: str) -> None:
    assert load_messages(language).t("range", min=1, max=2).count("1") == 1
    assert "2" in load_messages(language).t("range", min=1, max=2)


def test_every_violation_code_of_the_rules_has_a_text(rules: RuleSet) -> None:
    broken = DoorConfiguration(
        width_mm=rules.width_mm.max + 1,
        height_mm=rules.height_mm.max + 1,
        surface="no-such-surface",
        drive="no-such-drive",
        insulation="no-such-insulation",
        options=frozenset({"no-such-option"}),
    )
    codes = {violation.code for violation in validate(broken, rules)}
    assert codes <= set(REFERENCE.violations)


def test_unknown_language_gives_english() -> None:
    assert load_messages("xx").language == DEFAULT_LANGUAGE
    assert load_messages(None).language == DEFAULT_LANGUAGE


def test_missing_texts_fall_back_to_english(tmp_path: Path) -> None:
    for name in ("en", "de"):
        (tmp_path / f"{name}.json").write_text(
            (MESSAGES_DIR / f"{name}.json").read_text(encoding="utf-8"), encoding="utf-8"
        )
    (tmp_path / "la.json").write_text('{"text": {"title": "Configurator portarum"}}', "utf-8")
    latin = load_messages("la", tmp_path)
    assert latin.language_name == "la"
    assert latin.t("title") == "Configurator portarum"
    assert latin.t("submit") == REFERENCE.t("submit")
    assert latin.violation("DRIVE_TOO_WEAK", "x") == REFERENCE.violations["DRIVE_TOO_WEAK"]
    assert latin.violation("NEW_CODE", "technical text") == "technical text"
