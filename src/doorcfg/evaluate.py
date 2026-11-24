"""One answer for every front end (CLI, web page, JSON API): can it be built, what does it cost?

Front ends only translate input and output. The decision lives here, in rules.py and pricing.py.
"""

from __future__ import annotations

from typing import TypedDict

from doorcfg.models import DoorConfiguration
from doorcfg.pricing import net_price_cents
from doorcfg.rules import RuleSet, validate


class ViolationDict(TypedDict):
    code: str
    message: str


class Evaluation(TypedDict):
    valid: bool
    violations: list[ViolationDict]
    net_price_cents: int | None


def evaluate(config: DoorConfiguration, rules: RuleSet) -> Evaluation:
    """Validates the configuration and prices it when it can be built."""
    violations = validate(config, rules)
    return {
        "valid": not violations,
        "violations": [{"code": v.code, "message": v.message} for v in violations],
        "net_price_cents": None if violations else net_price_cents(config, rules),
    }
