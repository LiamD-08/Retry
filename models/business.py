"""Data model for a business in the simulation."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AcquisitionType(Enum):
    NONE = "none"
    RENT = "rent"
    BUYOUT = "buyout"


class BusinessStatus(Enum):
    AVAILABLE = "available"   # on the marketplace
    OWNED = "owned"           # player owns it
    SOLD = "sold"             # player has exited


class BusinessSize(Enum):
    MICRO = "micro"           # 1–5 employees
    SMALL = "small"           # 6–20 employees
    MEDIUM = "medium"         # 21–50 employees
    LARGE = "large"           # 51–150 employees


@dataclass
class BusinessFinancials:
    """Monthly P&L snapshot (all values in $)."""

    monthly_revenue: float = 0.0
    monthly_cogs: float = 0.0          # Cost of goods sold
    monthly_labor: float = 0.0         # Total wages + benefits
    monthly_overhead: float = 0.0      # Rent, utilities, insurance
    monthly_maintenance: float = 0.0   # Equipment upkeep
    monthly_debt_service: float = 0.0  # Principal + interest payments
    monthly_depreciation: float = 0.0  # Non-cash asset depreciation

    @property
    def gross_profit(self) -> float:
        return self.monthly_revenue - self.monthly_cogs

    @property
    def gross_margin(self) -> float:
        if self.monthly_revenue == 0:
            return 0.0
        return self.gross_profit / self.monthly_revenue

    @property
    def operating_expenses(self) -> float:
        return (
            self.monthly_labor
            + self.monthly_overhead
            + self.monthly_maintenance
            + self.monthly_depreciation
        )

    @property
    def ebitda(self) -> float:
        return self.gross_profit - self.monthly_labor - self.monthly_overhead - self.monthly_maintenance

    @property
    def operating_income(self) -> float:
        return self.ebitda - self.monthly_depreciation

    @property
    def net_income(self) -> float:
        return self.operating_income - self.monthly_debt_service

    @property
    def operating_margin(self) -> float:
        if self.monthly_revenue == 0:
            return 0.0
        return self.operating_income / self.monthly_revenue

    @property
    def cashflow(self) -> float:
        """Actual cash movement (adds back depreciation, subtracts debt service)."""
        return self.net_income + self.monthly_depreciation


@dataclass
class BusinessKPIs:
    """Key performance indicators (0–100 scale unless noted)."""

    customer_satisfaction: float = 50.0   # 0–100
    utilization: float = 50.0             # 0–100 (% of capacity used)
    quality_score: float = 50.0           # 0–100
    churn_rate: float = 0.10              # Monthly fraction of customers lost
    reputation: float = 50.0             # 0–100 (affects new customer acquisition)


@dataclass
class Business:
    """Full business entity."""

    name: str = "Unnamed Business"
    sector: str = "services"
    size: BusinessSize = BusinessSize.SMALL
    condition: float = 50.0               # Physical condition of assets (0–100)
    asset_value: float = 100_000.0        # Fair market value of tangible assets ($)
    debt: float = 0.0                     # Outstanding debt ($)
    debt_interest_rate: float = 0.08      # Annual interest rate on debt
    location_quality: float = 50.0        # 0–100

    # Acquisition details
    status: BusinessStatus = BusinessStatus.AVAILABLE
    acquisition_type: AcquisitionType = AcquisitionType.NONE
    asking_price: float = 0.0             # Purchase price for buyout
    monthly_lease: float = 0.0           # Monthly cost if rented
    acquisition_cost_paid: float = 0.0   # Actual amount spent at acquisition
    days_owned: int = 0

    # Financial state
    financials: BusinessFinancials = field(default_factory=BusinessFinancials)
    kpis: BusinessKPIs = field(default_factory=BusinessKPIs)

    # History (monthly snapshots for trend analysis)
    monthly_history: list = field(default_factory=list, repr=False)

    # Unique identifier
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Pending turnaround actions (resolved each tick)
    pending_actions: list = field(default_factory=list, repr=False)

    def __post_init__(self):
        if self.asking_price == 0.0:
            self.asking_price = self.asset_value * 1.2  # default: 20% premium

    def snapshot(self) -> dict:
        """Return a dict snapshot of key metrics for history tracking."""
        f = self.financials
        k = self.kpis
        return {
            "revenue": f.monthly_revenue,
            "net_income": f.net_income,
            "ebitda": f.ebitda,
            "cashflow": f.cashflow,
            "customer_satisfaction": k.customer_satisfaction,
            "utilization": k.utilization,
            "quality_score": k.quality_score,
            "condition": self.condition,
        }

    def annualised_ebitda(self) -> float:
        return self.financials.ebitda * 12

    def valuation_range(self, multiples: tuple[float, float]) -> tuple[float, float]:
        """Return (low, high) valuation based on EBITDA multiples minus debt."""
        annual_ebitda = self.annualised_ebitda()
        low = annual_ebitda * multiples[0] + self.asset_value * 0.5 - self.debt
        high = annual_ebitda * multiples[1] + self.asset_value * 0.5 - self.debt
        # Clamp to zero floor
        return (max(0.0, low), max(0.0, high))

    @property
    def employee_ids(self) -> list[str]:
        """IDs of employees currently assigned to this business."""
        if not hasattr(self, "_employee_ids"):
            self._employee_ids: list[str] = []
        return self._employee_ids

    @employee_ids.setter
    def employee_ids(self, value: list[str]) -> None:
        self._employee_ids = value
