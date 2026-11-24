"""Insulation: a new attribute of the door. Written before the implementation (red first)."""

import json
from dataclasses import replace

import pytest

from doorcfg.cli import main
from doorcfg.messages import available_languages, load_messages
from doorcfg.models import DoorConfiguration
from doorcfg.pricing import net_price_cents
from doorcfg.rules import RuleSet, validate
from doorcfg.web import handle, parse_config

VALID = "width=2500&height=2125&surface=smooth&drive=standard"


def test_rules_offer_three_insulations(rules: RuleSet) -> None:
    assert list(rules.insulations) == ["single", "double", "thermo"]


def test_a_door_is_single_skinned_unless_asked_otherwise(base_config: DoorConfiguration) -> None:
    assert base_config.insulation == "single"


def test_single_insulation_costs_nothing(base_config: DoorConfiguration, rules: RuleSet) -> None:
    assert net_price_cents(base_config, rules) == 59_500 + 34_900


def test_thermo_insulation_is_priced_per_square_metre(
    base_config: DoorConfiguration, rules: RuleSet
) -> None:
    # 5.3125 m2 x 32.00 EUR = 170.00 EUR
    config = replace(base_config, insulation="thermo")
    assert net_price_cents(config, rules) == 59_500 + 34_900 + 17_000


def test_insulation_price_is_rounded_half_up_to_whole_cents(
    base_config: DoorConfiguration, rules: RuleSet
) -> None:
    # 5.3125 m2 x 18.00 EUR = 95.625 EUR -> 95.63 EUR
    config = replace(base_config, insulation="double")
    assert net_price_cents(config, rules) == 59_500 + 34_900 + 9_563


def test_unknown_insulation_is_a_violation(base_config: DoorConfiguration, rules: RuleSet) -> None:
    violations = validate(replace(base_config, insulation="vacuum"), rules)
    assert [violation.code for violation in violations] == ["UNKNOWN_INSULATION"]


def test_cli_accepts_insulation(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["--width", "2500", "--height", "2125", "--surface", "smooth", "--insulation", "thermo"]
    )
    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["net_price_cents"] == 59_500 + 17_000


def test_api_reads_insulation_and_defaults_to_single(rules: RuleSet) -> None:
    config = parse_config({"width": ["2500"], "height": ["2125"], "surface": ["smooth"]})
    assert config.insulation == "single"
    response = handle(f"/api/quote?{VALID}&insulation=thermo", rules)
    assert json.loads(response.body)["net_price_cents"] == 59_500 + 34_900 + 17_000


def test_page_offers_every_insulation_and_keeps_the_choice(rules: RuleSet) -> None:
    response = handle(f"/?{VALID}&insulation=double", rules)
    for name in rules.insulations:
        assert f'<option value="{name}"' in response.body
    assert '<option value="double" selected>' in response.body


def test_every_language_names_the_new_field_and_the_new_violation() -> None:
    for language in available_languages():
        messages = load_messages(language)
        assert messages.t("insulation").strip()
        assert "UNKNOWN_INSULATION" in messages.violations
