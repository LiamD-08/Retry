"""Main simulation loop: ties all systems together."""
from __future__ import annotations

from businesses.manager import BusinessManager
from businesses.marketplace import refresh_marketplace
from core.clock import GameClock
from models.market import Marketplace
from services.player import Player


class Simulation:
    """
    Central simulation coordinator.

    Owns the game clock, marketplace, player state, and business manager.
    External code (UI / game loop) calls `tick()` to advance time.
    """

    def __init__(self, starting_capital: float | None = None) -> None:
        from config.balancing import INITIAL_CAPITAL
        if starting_capital is None:
            starting_capital = INITIAL_CAPITAL

        self.clock = GameClock()
        self.player = Player(starting_capital)
        self.marketplace = Marketplace()
        self.manager = BusinessManager(self.player.ledger, self.clock)
        self.event_log: list[str] = []

        # Register clock callbacks
        self.clock.register_daily(self._daily_callback)
        self.clock.register_monthly(self._monthly_callback)

        # Initial marketplace population
        refresh_marketplace(self.marketplace)

    # ------------------------------------------------------------------
    # Clock callbacks
    # ------------------------------------------------------------------

    def _daily_callback(self, clock: GameClock) -> None:
        log = self.manager.daily_tick()
        self.event_log.extend(log)
        self.marketplace.daily_tick()

    def _monthly_callback(self, clock: GameClock) -> None:
        log = self.manager.monthly_tick()
        self.event_log.extend(log)

        # Refresh marketplace every MARKET_REFRESH_DAYS days
        from config.balancing import MARKET_REFRESH_DAYS, DAYS_PER_MONTH
        if clock.months_elapsed() % max(1, MARKET_REFRESH_DAYS // DAYS_PER_MONTH) == 0:
            # Add new listings without clearing old ones
            refresh_marketplace(self.marketplace)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tick(self, days: int = 1) -> list[str]:
        """Advance simulation by *days* days. Returns accumulated event log."""
        self.event_log.clear()
        self.clock.advance_days(days)
        return list(self.event_log)

    def advance_month(self) -> list[str]:
        """Advance exactly one month (30 days)."""
        from config.balancing import DAYS_PER_MONTH
        return self.tick(DAYS_PER_MONTH)

    def acquire_business(self, business_id: str, mode: str) -> tuple[bool, str]:
        """
        Acquire a marketplace listing.
        mode: "rent" or "buyout"
        Returns (success, message).
        """
        listing = self.marketplace.get_listing(business_id)
        if listing is None:
            return False, "Business not found in marketplace."

        if not self.player.can_acquire_more():
            return False, "Portfolio limit reached."

        biz = listing.business

        if mode == "rent":
            if self.player.cash < biz.monthly_lease:
                return False, f"Insufficient funds. Need {biz.monthly_lease:,.2f}."
            success = self.manager.acquire_rent(biz)
        elif mode == "buyout":
            if self.player.cash < biz.asking_price:
                return False, f"Insufficient funds. Need {biz.asking_price:,.2f}."
            success = self.manager.acquire_buyout(biz)
        else:
            return False, f"Unknown acquisition mode: {mode}"

        if success:
            self.marketplace.remove_listing(business_id)
            self.player.add_to_portfolio(business_id)
            return True, f"Successfully acquired {biz.name} via {mode}."
        return False, "Acquisition failed."

    def sell_business(self, business_id: str) -> tuple[bool, str, dict | None]:
        """
        Sell an owned business.
        Returns (success, message, sale_details).
        """
        result = self.manager.sell_business(business_id)
        if result is None:
            return False, "Business not found or not owned.", None

        self.player.remove_from_portfolio(business_id)
        msg = (
            f"Business sold!\n"
            f"  Gross Value:  ${result['gross_value']:,.2f}\n"
            f"  Broker Fee:   ${result['broker_fee']:,.2f}\n"
            f"  Capital Gains Tax: ${result['tax']:,.2f}\n"
            f"  Net Proceeds: ${result['net_proceeds']:,.2f}"
        )
        return True, msg, result

    def queue_action(self, business_id: str, action_type: str, params: dict | None = None) -> bool:
        return self.manager.queue_action(business_id, action_type, params)
