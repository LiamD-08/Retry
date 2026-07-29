"""Business marketplace: generates failing businesses for the player to acquire."""
from __future__ import annotations

import json
import os
import random

from businesses.archetypes import get_archetype, list_sectors, ARCHETYPES
from config.balancing import (
    MARKET_BUSINESS_COUNT_MIN, MARKET_BUSINESS_COUNT_MAX,
    RENT_MARKUP_MIN, RENT_MARKUP_MAX,
    DEBT_INTEREST_RATE_MIN, DEBT_INTEREST_RATE_MAX,
)
from models.business import Business, BusinessSize, BusinessStatus, AcquisitionType
from models.market import Marketplace, MarketListing


# ---------------------------------------------------------------------------
# Name generation
# ---------------------------------------------------------------------------

_NAMES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "business_names.json")

def _load_names() -> dict:
    with open(_NAMES_PATH, "r") as fh:
        return json.load(fh)


def generate_business_name(sector: str, names_data: dict) -> str:
    generic = names_data.get("generic_names", ["Unnamed"])
    sector_suffixes = names_data.get(sector, names_data.get("services", ["Co."]))
    prefixes = names_data.get("prefixes", [""])

    use_prefix = random.random() < 0.4
    owner_name = random.choice(generic)
    suffix = random.choice(sector_suffixes)

    if use_prefix:
        prefix = random.choice(prefixes)
        return f"{prefix} {owner_name} {suffix}"
    return f"{owner_name} {suffix}"


# ---------------------------------------------------------------------------
# Business generation
# ---------------------------------------------------------------------------

_SIZE_EMPLOYEE_COUNTS = {
    BusinessSize.MICRO: (1, 5),
    BusinessSize.SMALL: (6, 20),
    BusinessSize.MEDIUM: (21, 50),
    BusinessSize.LARGE: (51, 150),
}


def _pick_size(archetype) -> BusinessSize:
    sizes = [BusinessSize.MICRO, BusinessSize.SMALL, BusinessSize.MEDIUM, BusinessSize.LARGE]
    min_idx = sizes.index(archetype.size_range[0])
    max_idx = sizes.index(archetype.size_range[1])
    return random.choice(sizes[min_idx: max_idx + 1])


def generate_business(sector: str | None = None, names_data: dict | None = None) -> Business:
    """Generate a randomised failing business for the marketplace."""
    if names_data is None:
        names_data = _load_names()

    if sector is None:
        sector = random.choice(list_sectors())

    archetype = get_archetype(sector)
    size = _pick_size(archetype)

    # --- Core financials ---
    monthly_revenue = random.uniform(*archetype.base_monthly_revenue_range)
    # Failing business: revenue is suppressed
    revenue_suppression = random.uniform(0.40, 0.75)
    monthly_revenue *= revenue_suppression

    cogs_ratio = random.uniform(*archetype.cogs_ratio_range)
    labor_ratio = random.uniform(*archetype.labor_ratio_range)
    overhead = random.uniform(*archetype.overhead_monthly_range)

    # Asset value and debt
    asset_value = random.uniform(*archetype.asset_value_range)
    debt_ratio = random.uniform(*archetype.debt_ratio_range)
    debt = asset_value * debt_ratio
    interest_rate = random.uniform(DEBT_INTEREST_RATE_MIN, DEBT_INTEREST_RATE_MAX)

    # Monthly debt service (interest-only for simplicity initially)
    monthly_debt_service = debt * interest_rate / 12

    # Depreciation
    monthly_depreciation = asset_value * archetype.depreciation_rate / 12

    # Condition and KPIs
    condition = random.uniform(*archetype.condition_range)
    maintenance_cost = _maintenance_cost(condition, asset_value)

    # Asking price: asset value adjusted for condition, minus some discount
    condition_factor = 0.4 + (condition / 100) * 0.8  # 0.4–1.2
    asking_price = asset_value * condition_factor * random.uniform(0.85, 1.15)

    # Monthly lease (if player rents instead of buying)
    annual_lease_rate = random.uniform(RENT_MARKUP_MIN, RENT_MARKUP_MAX)
    monthly_lease = asking_price * annual_lease_rate / 12

    # Build the business object
    b = Business(
        name=generate_business_name(sector, names_data),
        sector=sector,
        size=size,
        condition=condition,
        asset_value=asset_value,
        debt=debt,
        debt_interest_rate=interest_rate,
        location_quality=random.uniform(30.0, 80.0),
        status=BusinessStatus.AVAILABLE,
        acquisition_type=AcquisitionType.NONE,
        asking_price=round(asking_price, -2),   # round to nearest $100
        monthly_lease=round(monthly_lease, -1),
    )
    b._employee_ids = []

    # Set financials
    b.financials.monthly_revenue = round(monthly_revenue, 2)
    b.financials.monthly_cogs = round(monthly_revenue * cogs_ratio, 2)
    b.financials.monthly_labor = round(monthly_revenue * labor_ratio, 2)
    b.financials.monthly_overhead = round(overhead, 2)
    b.financials.monthly_maintenance = round(maintenance_cost, 2)
    b.financials.monthly_debt_service = round(monthly_debt_service, 2)
    b.financials.monthly_depreciation = round(monthly_depreciation, 2)

    # Set KPIs
    b.kpis.customer_satisfaction = random.uniform(*archetype.satisfaction_range)
    b.kpis.utilization = random.uniform(*archetype.utilization_range)
    b.kpis.quality_score = random.uniform(*archetype.quality_range)
    b.kpis.reputation = random.uniform(*archetype.reputation_range)
    b.kpis.churn_rate = random.uniform(*archetype.churn_range)

    return b


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
# Marketplace refresh
# ---------------------------------------------------------------------------

def refresh_marketplace(marketplace: Marketplace, names_data: dict | None = None) -> list[Business]:
    """Generate a new batch of listings and add them to the marketplace."""
    if names_data is None:
        names_data = _load_names()

    count = random.randint(MARKET_BUSINESS_COUNT_MIN, MARKET_BUSINESS_COUNT_MAX)
    new_businesses: list[Business] = []

    # Vary sectors each refresh
    sectors = random.sample(list_sectors(), min(count, len(list_sectors())))
    if count > len(sectors):
        sectors += random.choices(list_sectors(), k=count - len(sectors))

    for sector in sectors[:count]:
        b = generate_business(sector, names_data)
        archetype = ARCHETYPES.get(sector)
        notes = archetype.description if archetype else ""
        marketplace.add_listing(b, notes=notes)
        new_businesses.append(b)

    return new_businesses
