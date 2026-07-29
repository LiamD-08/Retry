"""Player state and portfolio management."""
from __future__ import annotations

from config.balancing import INITIAL_CAPITAL, MAX_OWNED_BUSINESSES
from models.financial import Ledger


class Player:
    """Represents the player's state: capital, portfolio, and history."""

    def __init__(self, starting_capital: float = INITIAL_CAPITAL) -> None:
        self.name: str = "Player"
        self.ledger: Ledger = Ledger(opening_balance=starting_capital)
        self._portfolio_ids: list[str] = []

    @property
    def cash(self) -> float:
        return self.ledger.balance()

    @property
    def portfolio_size(self) -> int:
        return len(self._portfolio_ids)

    def can_acquire_more(self) -> bool:
        return self.portfolio_size < MAX_OWNED_BUSINESSES

    def add_to_portfolio(self, business_id: str) -> None:
        if business_id not in self._portfolio_ids:
            self._portfolio_ids.append(business_id)

    def remove_from_portfolio(self, business_id: str) -> None:
        if business_id in self._portfolio_ids:
            self._portfolio_ids.remove(business_id)

    def net_worth(self, businesses: list) -> float:
        """
        Estimate net worth = cash + estimated portfolio value.
        *businesses* is a list of Business objects.
        """
        from economy.finance import compute_valuation
        portfolio_value = sum(
            (compute_valuation(b)[0] + compute_valuation(b)[1]) / 2
            for b in businesses
        )
        return self.cash + portfolio_value

    def summary(self) -> dict:
        return {
            "cash": self.cash,
            "portfolio_size": self.portfolio_size,
        }
