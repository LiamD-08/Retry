"""Dynamic pricing logic: adjusts revenue based on pricing decisions."""
from __future__ import annotations

from config.balancing import UNCERTAINTY_FACTOR


def price_elasticity_factor(price_change_pct: float, elasticity: float = -1.5) -> float:
    """
    Estimate demand change from a price change.

    price_change_pct: positive = price increase (e.g. 0.10 = +10%)
    elasticity:       price elasticity of demand (negative = normal good)

    Returns a multiplier for demand (e.g. 0.85 means 15% fewer customers).
    """
    demand_change = elasticity * price_change_pct
    return max(0.1, 1.0 + demand_change)


def marketing_revenue_lift(
    spend_monthly: float,
    current_revenue: float,
    reputation: float,
) -> float:
    """
    Estimate the revenue increase from marketing spend.

    Returns fractional lift (e.g. 0.05 = 5% more revenue).
    Diminishing returns above 5% of revenue.
    """
    if current_revenue <= 0:
        return 0.0
    spend_fraction = spend_monthly / current_revenue
    # Logarithmic return, moderated by reputation (higher rep = better conversion)
    rep_factor = 0.5 + (reputation / 100) * 1.0
    lift = rep_factor * 0.08 * min(spend_fraction / 0.05, 1.0)
    return min(lift, 0.15)  # cap at 15% lift per month


def apply_noise(value: float, factor: float = UNCERTAINTY_FACTOR) -> float:
    """Apply random multiplicative noise to a value."""
    import random
    noise = random.uniform(-factor, factor)
    return value * (1.0 + noise)


def compute_effective_revenue(
    base_revenue: float,
    price_multiplier: float,
    demand_multiplier: float,
    seasonal_multiplier: float,
    utilization: float,
) -> float:
    """
    Combine all revenue drivers into a final monthly revenue figure.

    utilization is 0–100; at 100 the business is running at capacity.
    """
    util_factor = utilization / 100.0
    revenue = base_revenue * price_multiplier * demand_multiplier * seasonal_multiplier * util_factor
    return apply_noise(max(0.0, revenue))
