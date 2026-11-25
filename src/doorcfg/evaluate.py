"""One answer for every front end (CLI, web page, JSON API): can it be built, what does it cost?

Front ends only translate input and output. The decision lives here, in rules.py and pricing.py.
"""

from __future__ import annotations

from typing import TypedDict

from doorcfg.models import DoorConfiguration
from doorcfg.pricing import (
    discount_cents,
    discount_percent,
    net_price_cents,
    total_net_price_cents,
)
from doorcfg.rules import RuleSet, validate


class ViolationDict(TypedDict):
    code: str
    message: str


class Evaluation(TypedDict):
    valid: bool
    violations: list[ViolationDict]
    net_price_cents: int | None
    quantity: int
    discount_percent: int | None
    discount_cents: int | None
    total_net_price_cents: int | None


def evaluate(config: DoorConfiguration, rules: RuleSet) -> Evaluation:
    """Validates the configuration and prices it when it can be built.

    `net_price_cents` is the price of one door, `total_net_price_cents` the whole order.
    """
    violations = validate(config, rules)
    valid = not violations
    return {
        "valid": valid,
        "violations": [{"code": v.code, "message": v.message} for v in violations],
        "net_price_cents": net_price_cents(config, rules) if valid else None,
        "quantity": config.quantity,
        "discount_percent": discount_percent(config.quantity, rules) if valid else None,
        "discount_cents": discount_cents(config, rules) if valid else None,
        "total_net_price_cents": total_net_price_cents(config, rules) if valid else None,
    }
