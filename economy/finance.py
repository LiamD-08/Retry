"""P&L calculation, cashflow management, and business valuation."""
from __future__ import annotations

import random

from config.balancing import (
    SECTOR_EBITDA_MULTIPLES, DEFAULT_EBITDA_MULTIPLE,
    SELL_TRANSACTION_COST_RATE, SELL_CAPITAL_GAINS_TAX_RATE,
    UNCERTAINTY_FACTOR, SEASONAL_AMPLITUDE,
)
from economy.pricing import compute_effective_revenue, marketing_revenue_lift
from models.business import Business, BusinessKPIs


# ---------------------------------------------------------------------------
# P&L update
# ---------------------------------------------------------------------------

def update_business_financials(
    business: Business,
    seasonal_multiplier: float,
    price_multiplier: float = 1.0,
    marketing_spend: float = 0.0,
    employee_total_cost: float | None = None,
) -> None:
    """
    Recalculate monthly P&L for *business* given current conditions.

    This should be called once per month (at month-end tick).
    """
    f = business.financials
    k = business.kpis

    # --- Revenue ---
    marketing_lift = marketing_revenue_lift(
        marketing_spend, f.monthly_revenue, k.reputation
    )
    demand_multiplier = _demand_from_kpis(k)

    f.monthly_revenue = compute_effective_revenue(
        base_revenue=f.monthly_revenue / max(0.01, demand_multiplier),  # decouple base
        price_multiplier=price_multiplier,
        demand_multiplier=demand_multiplier * (1 + marketing_lift),
        seasonal_multiplier=seasonal_multiplier,
        utilization=k.utilization,
    )

    # --- COGS scales roughly with revenue ---
    f.monthly_cogs = f.monthly_revenue * _cogs_ratio(business)

    # --- Labor ---
    if employee_total_cost is not None:
        f.monthly_labor = employee_total_cost
    # else: labor stays as-is (set externally)

    # --- Maintenance adjusts with condition ---
    f.monthly_maintenance = _maintenance_cost(business.condition, business.asset_value)

    # --- Debt service: interest-only on outstanding debt ---
    f.monthly_debt_service = business.debt * business.debt_interest_rate / 12

    # --- Depreciation ---
    from businesses.archetypes import get_archetype
    archetype = get_archetype(business.sector)
    f.monthly_depreciation = business.asset_value * archetype.depreciation_rate / 12


def _demand_from_kpis(kpis: BusinessKPIs) -> float:
    """Translate customer satisfaction and reputation into a demand multiplier."""
    sat = kpis.customer_satisfaction / 100
    rep = kpis.reputation / 100
    churn_drag = 1 - kpis.churn_rate * 0.5
    return max(0.1, (sat * 0.6 + rep * 0.4) * churn_drag)


def _cogs_ratio(business: Business) -> float:
    from businesses.archetypes import get_archetype
    archetype = get_archetype(business.sector)
    lo, hi = archetype.cogs_ratio_range
    return (lo + hi) / 2


def _maintenance_cost(condition: float, asset_value: float) -> float:
    from config.balancing import (
        MAINTENANCE_RATE_CRITICAL, MAINTENANCE_RATE_POOR,
        MAINTENANCE_RATE_FAIR, MAINTENANCE_RATE_GOOD,
        CONDITION_CRITICAL, CONDITION_POOR, CONDITION_FAIR,
    )
    if condition <= CONDITION_CRITICAL:
        rate = MAINTENANCE_RATE_CRITICAL
    elif condition <= CONDITION_POOR:
        rate = MAINTENANCE_RATE_POOR
    elif condition <= CONDITION_FAIR:
        rate = MAINTENANCE_RATE_FAIR
    else:
        rate = MAINTENANCE_RATE_GOOD
    return asset_value * rate / 12


# ---------------------------------------------------------------------------
# KPI update
# ---------------------------------------------------------------------------

def update_kpis(business: Business, actions_taken: list[str] | None = None) -> None:
    """
    Update KPIs based on current business state and any turnaround actions.
    Called monthly.
    """
    if actions_taken is None:
        actions_taken = []

    k = business.kpis
    f = business.financials

    # Condition decay / improvement
    # Poor maintenance → condition drops
    if f.monthly_maintenance < _maintenance_cost(business.condition, business.asset_value) * 0.7:
        business.condition = max(0.0, business.condition - random.uniform(0.5, 2.0))
    elif "maintenance_upgrade" in actions_taken:
        business.condition = min(100.0, business.condition + random.uniform(2.0, 6.0))
    else:
        # Slow natural decay
        business.condition = max(0.0, business.condition - random.uniform(0.1, 0.5))

    # Quality score influenced by condition and staffing
    if business.condition > 60:
        quality_target = 70.0
    elif business.condition > 40:
        quality_target = 55.0
    else:
        quality_target = 35.0

    if "process_improvement" in actions_taken:
        quality_target = min(100.0, quality_target + 10.0)
    k.quality_score = _nudge(k.quality_score, quality_target, step=3.0)

    # Customer satisfaction influenced by quality and utilization (crowding)
    crowd_penalty = max(0.0, (k.utilization - 85) * 0.3) if k.utilization > 85 else 0.0
    sat_target = k.quality_score - crowd_penalty
    if "marketing" in actions_taken:
        sat_target = min(100.0, sat_target + 5.0)
    k.customer_satisfaction = _nudge(k.customer_satisfaction, sat_target, step=2.5)

    # Churn rate (high churn if satisfaction is low)
    churn_target = max(0.02, 0.25 - (k.customer_satisfaction / 100) * 0.22)
    k.churn_rate = _nudge(k.churn_rate, churn_target, step=0.005)

    # Reputation lags satisfaction
    k.reputation = _nudge(k.reputation, k.customer_satisfaction * 0.9, step=1.5)

    # Utilization: driven by reputation and seasonal demand (already in revenue)
    util_target = 20 + k.reputation * 0.65
    if "pricing_adjustment" in actions_taken:
        util_target = min(100.0, util_target + 5.0)
    k.utilization = _nudge(k.utilization, util_target, step=2.0)

    # Add noise to all KPIs
    noise = UNCERTAINTY_FACTOR
    k.customer_satisfaction = _clamp(k.customer_satisfaction * (1 + random.uniform(-noise, noise)))
    k.quality_score = _clamp(k.quality_score * (1 + random.uniform(-noise, noise)))
    k.utilization = _clamp(k.utilization * (1 + random.uniform(-noise, noise)))
    k.reputation = _clamp(k.reputation * (1 + random.uniform(-noise, noise)))


def _nudge(current: float, target: float, step: float) -> float:
    """Move *current* toward *target* by at most *step*."""
    diff = target - current
    move = min(abs(diff), step) * (1 if diff >= 0 else -1)
    return current + move


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

def compute_valuation(business: Business) -> tuple[float, float]:
    """
    Return (low_valuation, high_valuation) for the business.

    Uses EBITDA multiple × annualised EBITDA + asset value (50%) − debt.
    """
    multiples = SECTOR_EBITDA_MULTIPLES.get(business.sector, DEFAULT_EBITDA_MULTIPLE)

    # Adjust multiples by trend and reputation
    rep_bonus = (business.kpis.reputation - 50) / 100 * 0.5  # ±0.25x
    multiples = (multiples[0] + rep_bonus, multiples[1] + rep_bonus)

    return business.valuation_range(multiples)


def compute_sale_proceeds(
    business: Business,
    acquisition_cost: float,
) -> dict:
    """
    Calculate net proceeds from selling a business.

    Returns a dict with gross_value, broker_fee, tax, net_proceeds.
    """
    low, high = compute_valuation(business)
    gross_value = (low + high) / 2  # sell at midpoint

    broker_fee = gross_value * SELL_TRANSACTION_COST_RATE
    capital_gain = max(0.0, gross_value - acquisition_cost)
    tax = capital_gain * SELL_CAPITAL_GAINS_TAX_RATE
    net_proceeds = gross_value - broker_fee - tax

    return {
        "gross_value": gross_value,
        "broker_fee": broker_fee,
        "capital_gain": capital_gain,
        "tax": tax,
        "net_proceeds": net_proceeds,
        "valuation_low": low,
        "valuation_high": high,
    }


# ---------------------------------------------------------------------------
# ROI helper
# ---------------------------------------------------------------------------

def compute_roi(
    monthly_cashflow: float,
    acquisition_cost: float,
    months_held: int,
) -> float:
    """Annualised ROI on acquisition cost."""
    if acquisition_cost <= 0 or months_held <= 0:
        return 0.0
    total_return = monthly_cashflow * months_held
    annualised = (total_return / acquisition_cost) * (12 / months_held)
    return annualised
