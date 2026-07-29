"""Sample businesses used for testing and as an initial marketplace seed."""
from __future__ import annotations

from models.business import Business, BusinessSize, BusinessStatus, AcquisitionType
from models.business import BusinessFinancials, BusinessKPIs


def make_failing_restaurant() -> Business:
    b = Business(
        name="Old Town Diner",
        sector="restaurant",
        size=BusinessSize.SMALL,
        condition=30.0,
        asset_value=180_000.0,
        debt=90_000.0,
        debt_interest_rate=0.09,
        location_quality=55.0,
        asking_price=95_000.0,
        monthly_lease=1_200.0,
    )
    b.financials = BusinessFinancials(
        monthly_revenue=18_000.0,
        monthly_cogs=6_300.0,
        monthly_labor=7_200.0,
        monthly_overhead=4_500.0,
        monthly_maintenance=1_800.0,
        monthly_debt_service=675.0,
        monthly_depreciation=150.0,
    )
    b.kpis = BusinessKPIs(
        customer_satisfaction=35.0,
        utilization=38.0,
        quality_score=32.0,
        churn_rate=0.18,
        reputation=28.0,
    )
    b._employee_ids = []
    return b


def make_struggling_retailer() -> Business:
    b = Business(
        name="Bennett Goods",
        sector="retail",
        size=BusinessSize.SMALL,
        condition=45.0,
        asset_value=120_000.0,
        debt=50_000.0,
        debt_interest_rate=0.07,
        location_quality=60.0,
        asking_price=75_000.0,
        monthly_lease=900.0,
    )
    b.financials = BusinessFinancials(
        monthly_revenue=32_000.0,
        monthly_cogs=17_600.0,
        monthly_labor=6_400.0,
        monthly_overhead=5_000.0,
        monthly_maintenance=800.0,
        monthly_debt_service=292.0,
        monthly_depreciation=80.0,
    )
    b.kpis = BusinessKPIs(
        customer_satisfaction=42.0,
        utilization=45.0,
        quality_score=44.0,
        churn_rate=0.14,
        reputation=38.0,
    )
    b._employee_ids = []
    return b


SEED_BUSINESSES = [make_failing_restaurant, make_struggling_retailer]
