"""Net price calculation: one door, and an order of several identical doors.

Money is an integer number of cents. No floats, no round().
"""

from __future__ import annotations

from doorcfg.models import DoorConfiguration, Violation
from doorcfg.rules import RuleSet, validate

MM2_PER_M2 = 1_000_000
PERCENT = 100


class InvalidConfigurationError(ValueError):
    """Raised when a price is requested for a configuration that breaks a rule."""

    def __init__(self, violations: list[Violation]) -> None:
        super().__init__(", ".join(violation.code for violation in violations))
        self.violations = violations


def divide_half_up(numerator: int, denominator: int) -> int:
    """Integer division that rounds half up (for non-negative numbers)."""
    return (2 * numerator + denominator) // (2 * denominator)


def panel_price_cents(config: DoorConfiguration, rules: RuleSet) -> int:
    area_mm2 = config.width_mm * config.height_mm
    return divide_half_up(area_mm2 * rules.surfaces[config.surface], MM2_PER_M2)


def insulation_price_cents(config: DoorConfiguration, rules: RuleSet) -> int:
    area_mm2 = config.width_mm * config.height_mm
    return divide_half_up(area_mm2 * rules.insulations[config.insulation], MM2_PER_M2)


def net_price_cents(config: DoorConfiguration, rules: RuleSet) -> int:
    """Net price of one door in cents, without quantity discount.

    Raises InvalidConfigurationError for invalid configurations.
    """
    violations = validate(config, rules)
    if violations:
        raise InvalidConfigurationError(violations)

    total = panel_price_cents(config, rules)
    total += insulation_price_cents(config, rules)
    total += rules.drives[config.drive].price_cents
    total += sum(rules.options[name].price_cents for name in config.options)
    return total


def discount_percent(quantity: int, rules: RuleSet) -> int:
    """Percent of the tier with the highest min_quantity the quantity reaches, else 0."""
    reached = [tier for tier in rules.quantity_discounts if quantity >= tier.min_quantity]
    if not reached:
        return 0
    return max(reached, key=lambda tier: tier.min_quantity).percent


def discount_cents(config: DoorConfiguration, rules: RuleSet) -> int:
    """Quantity discount on the whole order, rounded half up once."""
    undiscounted = net_price_cents(config, rules) * config.quantity
    return divide_half_up(undiscounted * discount_percent(config.quantity, rules), PERCENT)


def total_net_price_cents(config: DoorConfiguration, rules: RuleSet) -> int:
    """Net price of all doors of the order, after the quantity discount."""
    return net_price_cents(config, rules) * config.quantity - discount_cents(config, rules)
