"""Quantity discount: written from docs/specs/quantity-discount.md, before the implementation.

The numbers are the examples of the spec. "AC n" names the acceptance criterion a test checks.
"""

import json
from dataclasses import replace

import pytest

from doorcfg.cli import main
from doorcfg.evaluate import evaluate
from doorcfg.messages import available_languages, load_messages
from doorcfg.models import DoorConfiguration
from doorcfg.pricing import (
    discount_cents,
    discount_percent,
    net_price_cents,
    total_net_price_cents,
)
from doorcfg.rules import RuleSet, validate
from doorcfg.web import handle, parse_config

VALID = "width=2500&height=2125&surface=smooth&drive=standard"
BASE_DOOR = 94_400


def test_tiers_and_limits_come_from_the_rule_set(rules: RuleSet) -> None:
    """AC 1"""
    assert (rules.quantity.min, rules.quantity.max) == (1, 50)
    assert [(tier.min_quantity, tier.percent) for tier in rules.quantity_discounts] == [
        (5, 5),
        (10, 8),
    ]


def test_one_door_costs_what_it_costs_today(base_config: DoorConfiguration, rules: RuleSet) -> None:
    """AC 2"""
    assert base_config.quantity == 1
    assert discount_cents(base_config, rules) == 0
    assert total_net_price_cents(base_config, rules) == BASE_DOOR


@pytest.mark.parametrize(
    ("quantity", "percent", "discount", "total"),
    [
        (4, 0, 0, 377_600),
        (5, 5, 23_600, 448_400),
        (9, 5, 42_480, 807_120),
        (10, 8, 75_520, 868_480),
        (50, 8, 377_600, 4_342_400),
    ],
)
def test_the_highest_tier_reached_applies_to_the_whole_order(
    base_config: DoorConfiguration,
    rules: RuleSet,
    quantity: int,
    percent: int,
    discount: int,
    total: int,
) -> None:
    """AC 3"""
    order = replace(base_config, quantity=quantity)
    assert discount_percent(quantity, rules) == percent
    assert discount_cents(order, rules) == discount
    assert total_net_price_cents(order, rules) == total


def test_the_price_of_one_door_does_not_depend_on_the_quantity(
    base_config: DoorConfiguration, rules: RuleSet
) -> None:
    """AC 6"""
    assert net_price_cents(replace(base_config, quantity=10), rules) == BASE_DOOR


def test_the_discount_is_rounded_half_up_to_whole_cents(
    base_config: DoorConfiguration, rules: RuleSet
) -> None:
    """AC 4"""
    # 5 x 1,039.63 EUR = 5,198.15 EUR, 5 % = 259.9075 EUR -> 259.91 EUR
    double = replace(base_config, insulation="double", quantity=5)
    assert discount_cents(double, rules) == 25_991
    assert total_net_price_cents(double, rules) == 493_824
    # 5 x 552.50 EUR = 2,762.50 EUR, 5 % = 138.125 EUR -> 138.13 EUR (exactly half a cent)
    ribbed = replace(base_config, surface="ribbed", drive="manual", quantity=5)
    assert discount_cents(ribbed, rules) == 13_813
    assert total_net_price_cents(ribbed, rules) == 262_437


def test_quantity_limits_are_inclusive(base_config: DoorConfiguration, rules: RuleSet) -> None:
    """AC 5"""
    for allowed in (1, 50):
        assert validate(replace(base_config, quantity=allowed), rules) == []
    for refused in (0, 51, -3):
        violations = validate(replace(base_config, quantity=refused), rules)
        assert [violation.code for violation in violations] == ["QUANTITY_OUT_OF_RANGE"]


def test_the_quantity_is_checked_after_the_existing_rules(
    base_config: DoorConfiguration, rules: RuleSet
) -> None:
    """Spec, "Violation": the order of the existing violations does not change."""
    order = replace(base_config, surface="glass", options=frozenset({"sunroof"}), quantity=0)
    assert [violation.code for violation in validate(order, rules)] == [
        "UNKNOWN_SURFACE",
        "UNKNOWN_OPTION",
        "QUANTITY_OUT_OF_RANGE",
    ]


def test_the_answer_names_quantity_discount_and_total(
    base_config: DoorConfiguration, rules: RuleSet
) -> None:
    """AC 6"""
    assert evaluate(replace(base_config, quantity=5), rules) == {
        "valid": True,
        "violations": [],
        "net_price_cents": BASE_DOOR,
        "quantity": 5,
        "discount_percent": 5,
        "discount_cents": 23_600,
        "total_net_price_cents": 448_400,
    }


def test_an_invalid_order_has_no_amounts(base_config: DoorConfiguration, rules: RuleSet) -> None:
    """AC 7"""
    answer = evaluate(replace(base_config, quantity=51), rules)
    assert answer["valid"] is False
    assert answer["quantity"] == 51
    assert answer["net_price_cents"] is None
    assert answer["discount_percent"] is None
    assert answer["discount_cents"] is None
    assert answer["total_net_price_cents"] is None


def test_cli_accepts_a_quantity(capsys: pytest.CaptureFixture[str]) -> None:
    """AC 8"""
    door = ["--width", "2500", "--height", "2125", "--surface", "smooth", "--drive", "standard"]
    assert main([*door, "--quantity", "10"]) == 0
    assert json.loads(capsys.readouterr().out)["total_net_price_cents"] == 868_480
    assert main(door) == 0
    assert json.loads(capsys.readouterr().out)["quantity"] == 1


def test_api_reads_the_quantity_and_defaults_to_one(rules: RuleSet) -> None:
    """AC 9"""
    config = parse_config({"width": ["2500"], "height": ["2125"], "surface": ["smooth"]})
    assert config.quantity == 1
    answer = json.loads(handle(f"/api/quote?{VALID}&quantity=5", rules).body)
    assert answer["total_net_price_cents"] == 448_400
    assert json.loads(handle(f"/api/quote?{VALID}&quantity=", rules).body)["quantity"] == 1


def test_api_refuses_a_quantity_that_is_not_a_whole_number(rules: RuleSet) -> None:
    """AC 9"""
    for raw in ("many", "2.5"):
        response = handle(f"/api/quote?{VALID}&quantity={raw}", rules)
        assert response.status == 400
        assert "quantity" in json.loads(response.body)["error"]


def test_page_has_the_field_and_keeps_the_quantity(rules: RuleSet) -> None:
    """AC 10"""
    assert '<input id="quantity" name="quantity" type="number"' in handle("/", rules).body
    assert 'name="quantity" type="number" required\n             value="5"' in (
        handle(f"/?{VALID}&quantity=5", rules).body
    )


def test_page_shows_total_price_per_door_and_discount_for_several_doors(rules: RuleSet) -> None:
    """AC 10"""
    body = handle(f"/?{VALID}&quantity=5", rules).body
    assert '<p class="price">4,484.00 EUR</p>' in body
    assert "net price for 5 doors" in body
    assert "944.00 EUR per door" in body
    assert "5 % quantity discount: -236.00 EUR" in body


def test_page_shows_no_discount_line_without_a_discount(rules: RuleSet) -> None:
    """AC 10"""
    one_door = handle(f"/?{VALID}", rules).body
    assert '<p class="price">944.00 EUR</p>' in one_door
    assert "per door" not in one_door
    assert "quantity discount" not in one_door
    four_doors = handle(f"/?{VALID}&quantity=4", rules).body
    assert '<p class="price">3,776.00 EUR</p>' in four_doors
    assert "944.00 EUR per door" in four_doors
    assert "quantity discount" not in four_doors


@pytest.mark.parametrize("language", available_languages())
def test_every_language_has_the_new_texts_with_their_placeholders(language: str) -> None:
    """AC 11"""
    messages = load_messages(language)
    assert messages.t("quantity").strip()
    assert "7" in messages.t("net_total", quantity=7)
    assert "9.00 EUR" in messages.t("per_door", price="9.00 EUR")
    discount = messages.t("discount", percent=5, amount="2.00 EUR")
    assert "5" in discount and "2.00 EUR" in discount
    assert "QUANTITY_OUT_OF_RANGE" in messages.violations
