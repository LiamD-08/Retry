"""Financial transaction record model."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class TransactionType(Enum):
    ACQUISITION = "acquisition"
    LEASE_PAYMENT = "lease_payment"
    REVENUE = "revenue"
    COGS = "cogs"
    LABOR = "labor"
    OVERHEAD = "overhead"
    MAINTENANCE = "maintenance"
    DEBT_SERVICE = "debt_service"
    TRAINING = "training"
    MARKETING = "marketing"
    EQUIPMENT = "equipment"
    HIRING = "hiring"
    SEVERANCE = "severance"
    SALE_PROCEEDS = "sale_proceeds"
    SALE_COSTS = "sale_costs"
    TAX = "tax"
    OTHER = "other"


@dataclass
class Transaction:
    """A single financial transaction."""

    amount: float                          # Positive = inflow, negative = outflow
    type: TransactionType = TransactionType.OTHER
    description: str = ""
    business_id: str = ""
    day: int = 0
    month: int = 0
    year: int = 1
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def is_income(self) -> bool:
        return self.amount > 0

    @property
    def is_expense(self) -> bool:
        return self.amount < 0


@dataclass
class Ledger:
    """Tracks all transactions and running balance for a player."""

    transactions: list[Transaction] = field(default_factory=list)
    opening_balance: float = 0.0

    def record(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)

    def balance(self) -> float:
        return self.opening_balance + sum(t.amount for t in self.transactions)

    def transactions_for_business(self, business_id: str) -> list[Transaction]:
        return [t for t in self.transactions if t.business_id == business_id]

    def income_this_month(self, month: int, year: int) -> float:
        return sum(
            t.amount for t in self.transactions
            if t.month == month and t.year == year and t.amount > 0
        )

    def expenses_this_month(self, month: int, year: int) -> float:
        return sum(
            t.amount for t in self.transactions
            if t.month == month and t.year == year and t.amount < 0
        )

    def net_this_month(self, month: int, year: int) -> float:
        return sum(
            t.amount for t in self.transactions
            if t.month == month and t.year == year
        )
