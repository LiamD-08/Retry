"""Business type (archetype) definitions.

Each archetype describes the *starting* characteristics of a class of
failing business, including P&L structure and KPI baselines.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from models.business import BusinessSize


@dataclass
class BusinessArchetype:
    sector: str
    display_name: str
    size_range: tuple[BusinessSize, BusinessSize]  # (min, max)

    # Revenue drivers
    base_monthly_revenue_range: tuple[float, float]  # ($, $)
    cogs_ratio_range: tuple[float, float]             # fraction of revenue
    labor_ratio_range: tuple[float, float]            # fraction of revenue
    overhead_monthly_range: tuple[float, float]       # ($, $)

    # Asset profile
    asset_value_range: tuple[float, float]            # ($, $)
    depreciation_rate: float = 0.10                   # Annual depreciation of assets

    # Condition of failing business at acquisition
    condition_range: tuple[float, float] = (20.0, 50.0)

    # Starting KPIs for a failing business
    satisfaction_range: tuple[float, float] = (25.0, 50.0)
    utilization_range: tuple[float, float] = (30.0, 55.0)
    quality_range: tuple[float, float] = (30.0, 55.0)
    reputation_range: tuple[float, float] = (20.0, 45.0)
    churn_range: tuple[float, float] = (0.10, 0.25)

    # Debt profile (fraction of asset value)
    debt_ratio_range: tuple[float, float] = (0.3, 0.8)

    # Seasonal demand shape (multiplier per month, index 0=Jan)
    seasonal_profile: list[float] = field(default_factory=lambda: [1.0] * 12)

    # Description shown in marketplace
    description: str = ""


ARCHETYPES: dict[str, BusinessArchetype] = {
    "restaurant": BusinessArchetype(
        sector="restaurant",
        display_name="Restaurant",
        size_range=(BusinessSize.MICRO, BusinessSize.MEDIUM),
        base_monthly_revenue_range=(15_000, 80_000),
        cogs_ratio_range=(0.28, 0.38),
        labor_ratio_range=(0.28, 0.40),
        overhead_monthly_range=(4_000, 15_000),
        asset_value_range=(80_000, 400_000),
        depreciation_rate=0.10,
        condition_range=(15.0, 45.0),
        seasonal_profile=[0.85, 0.82, 0.90, 0.95, 1.02, 1.08,
                          1.15, 1.12, 1.00, 0.95, 0.90, 1.20],
        description="Struggling eatery with declining customer base.",
    ),
    "retail": BusinessArchetype(
        sector="retail",
        display_name="Retail Store",
        size_range=(BusinessSize.MICRO, BusinessSize.MEDIUM),
        base_monthly_revenue_range=(20_000, 120_000),
        cogs_ratio_range=(0.45, 0.60),
        labor_ratio_range=(0.15, 0.25),
        overhead_monthly_range=(5_000, 20_000),
        asset_value_range=(60_000, 350_000),
        depreciation_rate=0.08,
        condition_range=(20.0, 50.0),
        seasonal_profile=[0.80, 0.75, 0.85, 0.90, 0.95, 1.00,
                          1.05, 1.00, 0.95, 0.95, 1.10, 1.60],
        description="Brick-and-mortar shop losing ground to online competitors.",
    ),
    "manufacturing": BusinessArchetype(
        sector="manufacturing",
        display_name="Small Manufacturer",
        size_range=(BusinessSize.SMALL, BusinessSize.LARGE),
        base_monthly_revenue_range=(50_000, 300_000),
        cogs_ratio_range=(0.50, 0.65),
        labor_ratio_range=(0.20, 0.30),
        overhead_monthly_range=(8_000, 40_000),
        asset_value_range=(200_000, 1_500_000),
        depreciation_rate=0.12,
        condition_range=(15.0, 40.0),
        seasonal_profile=[0.90, 0.92, 0.98, 1.02, 1.05, 1.05,
                          1.00, 1.00, 1.02, 1.02, 0.98, 0.92],
        description="Aging factory with outdated equipment and cost overruns.",
    ),
    "services": BusinessArchetype(
        sector="services",
        display_name="Service Business",
        size_range=(BusinessSize.MICRO, BusinessSize.MEDIUM),
        base_monthly_revenue_range=(10_000, 100_000),
        cogs_ratio_range=(0.10, 0.25),
        labor_ratio_range=(0.40, 0.60),
        overhead_monthly_range=(2_000, 12_000),
        asset_value_range=(30_000, 250_000),
        depreciation_rate=0.07,
        condition_range=(25.0, 55.0),
        description="Professional or trade services firm with retention problems.",
    ),
    "technology": BusinessArchetype(
        sector="technology",
        display_name="Tech Company",
        size_range=(BusinessSize.MICRO, BusinessSize.MEDIUM),
        base_monthly_revenue_range=(20_000, 200_000),
        cogs_ratio_range=(0.10, 0.20),
        labor_ratio_range=(0.45, 0.65),
        overhead_monthly_range=(3_000, 20_000),
        asset_value_range=(50_000, 500_000),
        depreciation_rate=0.25,
        condition_range=(30.0, 60.0),
        description="Software/tech startup burning cash with low retention.",
    ),
    "healthcare": BusinessArchetype(
        sector="healthcare",
        display_name="Healthcare Practice",
        size_range=(BusinessSize.MICRO, BusinessSize.MEDIUM),
        base_monthly_revenue_range=(30_000, 180_000),
        cogs_ratio_range=(0.25, 0.40),
        labor_ratio_range=(0.35, 0.50),
        overhead_monthly_range=(5_000, 25_000),
        asset_value_range=(100_000, 800_000),
        depreciation_rate=0.09,
        condition_range=(25.0, 50.0),
        description="Medical or dental practice struggling with billing and staffing.",
    ),
    "logistics": BusinessArchetype(
        sector="logistics",
        display_name="Logistics / Delivery",
        size_range=(BusinessSize.SMALL, BusinessSize.LARGE),
        base_monthly_revenue_range=(40_000, 250_000),
        cogs_ratio_range=(0.45, 0.60),
        labor_ratio_range=(0.20, 0.35),
        overhead_monthly_range=(6_000, 30_000),
        asset_value_range=(150_000, 1_000_000),
        depreciation_rate=0.15,
        condition_range=(15.0, 40.0),
        description="Delivery fleet with high fuel costs and driver turnover.",
    ),
    "hospitality": BusinessArchetype(
        sector="hospitality",
        display_name="Hotel / B&B",
        size_range=(BusinessSize.SMALL, BusinessSize.LARGE),
        base_monthly_revenue_range=(25_000, 200_000),
        cogs_ratio_range=(0.20, 0.35),
        labor_ratio_range=(0.30, 0.45),
        overhead_monthly_range=(8_000, 35_000),
        asset_value_range=(300_000, 2_000_000),
        depreciation_rate=0.07,
        condition_range=(15.0, 45.0),
        seasonal_profile=[0.60, 0.55, 0.70, 0.85, 1.10, 1.25,
                          1.30, 1.30, 1.10, 0.90, 0.70, 0.90],
        description="Hotel or guesthouse with dated facilities and poor reviews.",
    ),
}


def get_archetype(sector: str) -> BusinessArchetype:
    return ARCHETYPES.get(sector, ARCHETYPES["services"])


def list_sectors() -> list[str]:
    return list(ARCHETYPES.keys())
