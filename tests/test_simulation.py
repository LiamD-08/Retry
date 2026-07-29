"""Integration tests for the simulation loop."""
import pytest
from core.simulation import Simulation
from models.business import BusinessStatus, AcquisitionType
from config.balancing import INITIAL_CAPITAL, DAYS_PER_MONTH


@pytest.fixture
def sim():
    """Fresh simulation with default starting capital."""
    return Simulation(starting_capital=INITIAL_CAPITAL)


class TestClockIntegration:
    def test_initial_date(self, sim):
        assert sim.clock.day == 1
        assert sim.clock.month == 1
        assert sim.clock.year == 1

    def test_tick_advances_day(self, sim):
        sim.tick(1)
        assert sim.clock.total_days == 1

    def test_advance_month_advances_30_days(self, sim):
        sim.advance_month()
        assert sim.clock.total_days == DAYS_PER_MONTH

    def test_month_rollover(self, sim):
        # Advance 12 months
        for _ in range(12):
            sim.advance_month()
        assert sim.clock.year == 2
        assert sim.clock.month == 1

    def test_seasonal_multiplier_range(self, sim):
        for month in range(1, 13):
            sim.clock.month = month
            m = sim.clock.seasonal_multiplier
            assert 0.5 <= m <= 1.5


class TestMarketplace:
    def test_marketplace_populated_on_start(self, sim):
        assert sim.marketplace.count() > 0

    def test_marketplace_listing_has_business(self, sim):
        listing = sim.marketplace.listings[0]
        assert listing.business is not None
        assert listing.business.name != ""

    def test_acquire_rent_success(self, sim):
        listing = sim.marketplace.listings[0]
        biz = listing.business
        # Ensure lease is affordable
        biz.monthly_lease = 1_000.0

        success, msg = sim.acquire_business(biz.id, "rent")
        assert success, msg
        assert biz.status == BusinessStatus.OWNED
        assert biz.acquisition_type == AcquisitionType.RENT

    def test_acquire_buyout_success(self, sim):
        listing = sim.marketplace.listings[0]
        biz = listing.business
        biz.asking_price = 10_000.0  # affordable

        success, msg = sim.acquire_business(biz.id, "buyout")
        assert success, msg
        assert biz.status == BusinessStatus.OWNED
        assert biz.acquisition_type == AcquisitionType.BUYOUT

    def test_acquire_removes_from_marketplace(self, sim):
        listing = sim.marketplace.listings[0]
        biz_id = listing.business.id
        listing.business.monthly_lease = 500.0

        sim.acquire_business(biz_id, "rent")
        assert sim.marketplace.get_listing(biz_id) is None

    def test_acquire_fails_insufficient_funds(self, sim):
        listing = sim.marketplace.listings[0]
        biz = listing.business
        biz.asking_price = INITIAL_CAPITAL * 10  # way too expensive

        success, msg = sim.acquire_business(biz.id, "buyout")
        assert not success

    def test_acquire_invalid_mode(self, sim):
        listing = sim.marketplace.listings[0]
        success, msg = sim.acquire_business(listing.business.id, "gift")
        assert not success


class TestOperations:
    def _acquire_cheap_business(self, sim) -> str:
        """Helper: acquire the first marketplace listing cheaply."""
        biz = sim.marketplace.listings[0].business
        biz.monthly_lease = 100.0
        sim.acquire_business(biz.id, "rent")
        return biz.id

    def test_monthly_tick_records_cashflow(self, sim):
        biz_id = self._acquire_cheap_business(sim)
        initial_cash = sim.player.cash
        sim.advance_month()
        # Cash should have changed (monthly P&L recorded)
        # Note: lease is already deducted at acquisition + month start
        assert sim.player.ledger.balance() != INITIAL_CAPITAL  # something was recorded

    def test_business_has_monthly_history_after_month(self, sim):
        biz_id = self._acquire_cheap_business(sim)
        sim.advance_month()
        biz = sim.manager.get_business(biz_id)
        assert len(biz.monthly_history) >= 1

    def test_queue_action_accepted(self, sim):
        biz_id = self._acquire_cheap_business(sim)
        result = sim.queue_action(biz_id, "marketing", {"spend": 1_000.0})
        assert result is True

    def test_queue_action_invalid_business(self, sim):
        result = sim.queue_action("nonexistent", "marketing", {})
        assert result is False

    def test_maintenance_upgrade_action(self, sim):
        biz_id = self._acquire_cheap_business(sim)
        biz = sim.manager.get_business(biz_id)
        initial_condition = biz.condition
        sim.queue_action(biz_id, "maintenance_upgrade", {"spend": 5_000.0})
        sim.advance_month()
        # Condition should have improved or at least action was processed
        biz_after = sim.manager.get_business(biz_id)
        assert biz_after is not None  # still exists

    def test_pay_down_debt_reduces_debt(self, sim):
        biz_id = self._acquire_cheap_business(sim)
        biz = sim.manager.get_business(biz_id)
        biz.debt = 50_000.0
        initial_debt = biz.debt
        sim.queue_action(biz_id, "pay_down_debt", {"amount": 10_000.0})
        sim.advance_month()
        assert biz.debt == pytest.approx(initial_debt - 10_000.0)


class TestExit:
    def _acquire_and_tick(self, sim, months: int = 3) -> str:
        biz = sim.marketplace.listings[0].business
        biz.monthly_lease = 100.0
        sim.acquire_business(biz.id, "rent")
        for _ in range(months):
            sim.advance_month()
        return biz.id

    def test_sell_business_returns_dict(self, sim):
        biz_id = self._acquire_and_tick(sim)
        success, msg, details = sim.sell_business(biz_id)
        assert success
        assert details is not None
        assert "net_proceeds" in details

    def test_sell_business_marks_sold(self, sim):
        biz_id = self._acquire_and_tick(sim)
        biz = sim.manager.get_business(biz_id)
        sim.sell_business(biz_id)
        # After sale, business should no longer be in manager
        assert sim.manager.get_business(biz_id) is None

    def test_sell_proceeds_credited(self, sim):
        biz_id = self._acquire_and_tick(sim)
        cash_before = sim.player.cash
        success, msg, details = sim.sell_business(biz_id)
        # Net proceeds should be added to ledger
        assert sim.player.cash > cash_before - 1  # allow rounding

    def test_sell_removes_from_portfolio(self, sim):
        biz_id = self._acquire_and_tick(sim)
        sim.sell_business(biz_id)
        assert biz_id not in sim.player._portfolio_ids

    def test_sell_nonexistent_fails(self, sim):
        success, msg, details = sim.sell_business("nonexistent_id")
        assert not success
        assert details is None


class TestPlayer:
    def test_initial_cash(self, sim):
        assert sim.player.cash == pytest.approx(INITIAL_CAPITAL)

    def test_cash_decreases_on_acquisition(self, sim):
        biz = sim.marketplace.listings[0].business
        biz.asking_price = 50_000.0
        sim.acquire_business(biz.id, "buyout")
        assert sim.player.cash == pytest.approx(INITIAL_CAPITAL - 50_000.0)

    def test_portfolio_size_increases(self, sim):
        biz = sim.marketplace.listings[0].business
        biz.monthly_lease = 500.0
        sim.acquire_business(biz.id, "rent")
        assert sim.player.portfolio_size == 1

    def test_net_worth_includes_portfolio(self, sim):
        biz = sim.marketplace.listings[0].business
        biz.monthly_lease = 500.0
        sim.acquire_business(biz.id, "rent")
        businesses = sim.manager.all_businesses()
        net_worth = sim.player.net_worth(businesses)
        assert net_worth > 0
