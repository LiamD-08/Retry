"""Debt calculations: interest accrual and restructuring."""
from __future__ import annotations

from config.balancing import (
    DEBT_INTEREST_RATE_MIN, DEBT_INTEREST_RATE_MAX,
    DEBT_RESTRUCTURE_COST_RATE, DAYS_PER_YEAR,
)


def daily_interest(principal: float, annual_rate: float) -> float:
    """Return the interest accrued on *principal* for one day."""
    return principal * annual_rate / DAYS_PER_YEAR


def monthly_interest(principal: float, annual_rate: float) -> float:
    """Return the interest component of a monthly debt service payment."""
    return principal * annual_rate / 12


def monthly_principal_payment(
    principal: float,
    annual_rate: float,
    term_months: int,
) -> float:
    """Amortising monthly payment (principal portion only)."""
    if term_months <= 0:
        return 0.0
    return principal / term_months


def monthly_debt_service(
    principal: float,
    annual_rate: float,
    term_months: int,
) -> float:
    """Total monthly payment = interest + principal amortisation."""
    return monthly_interest(principal, annual_rate) + monthly_principal_payment(
        principal, annual_rate, term_months
    )


def restructure_debt(
    principal: float,
    current_rate: float,
    new_rate: float | None = None,
    extend_months: int = 24,
) -> tuple[float, float, float]:
    """
    Restructure debt: extend term and optionally lower rate.

    Returns (new_principal, new_rate, restructuring_fee).
    The fee is a one-time cost charged to player cashflow.
    """
    fee = principal * DEBT_RESTRUCTURE_COST_RATE
    if new_rate is None:
        new_rate = max(DEBT_INTEREST_RATE_MIN, current_rate - 0.02)
    return principal, new_rate, fee


def debt_payoff_cost(principal: float) -> float:
    """Early payoff penalty (1% of outstanding principal)."""
    return principal * 0.01
