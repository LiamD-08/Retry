"""Tests for financial calculations: P&L, cashflow, and ledger."""
import pytest
from models.business import Business, BusinessFinancials, BusinessKPIs, BusinessSize
from models.financial import Ledger, Transaction, TransactionType
from economy.finance import (
    update_business_financials, compute_valuation, compute_sale_proceeds, compute_roi,
)
from core.clock import GameClock


@pytest.fixture
def simple_business():
    b = Business(
        name="Test Diner",
        sector="restaurant",
        size=BusinessSize.SMALL,
        condition=50.0,
        asset_value=200_000.0,
        debt=60_000.0,
        debt_interest_rate=0.09,
    )
    b.financials = BusinessFinancials(
        monthly_revenue=30_000.0,
        monthly_cogs=9_000.0,
        monthly_labor=10_000.0,
        monthly_overhead=5_000.0,
        monthly_maintenance=500.0,
        monthly_debt_service=450.0,
        monthly_depreciation=167.0,
    )
    b.kpis = BusinessKPIs(
        customer_satisfaction=60.0,
        utilization=60.0,
        quality_score=60.0,
        churn_rate=0.08,
        reputation=55.0,
    )
    b._employee_ids = []
    return b


class TestBusinessFinancials:
    def test_gross_profit(self, simple_business):
        f = simple_business.financials
        assert f.gross_profit == pytest.approx(21_000.0)

    def test_gross_margin(self, simple_business):
        f = simple_business.financials
        assert f.gross_margin == pytest.approx(0.70, abs=1e-6)

    def test_ebitda(self, simple_business):
        f = simple_business.financials
        expected = 21_000 - 10_000 - 5_000 - 500
        assert f.ebitda == pytest.approx(expected)

    def test_operating_income(self, simple_business):
        f = simple_business.financials
        assert f.operating_income == pytest.approx(f.ebitda - f.monthly_depreciation)

    def test_net_income(self, simple_business):
        f = simple_business.financials
        assert f.net_income == pytest.approx(f.operating_income - f.monthly_debt_service)

    def test_cashflow_adds_back_depreciation(self, simple_business):
        f = simple_business.financials
        assert f.cashflow == pytest.approx(f.net_income + f.monthly_depreciation)

    def test_operating_margin(self, simple_business):
        f = simple_business.financials
        expected = f.operating_income / f.monthly_revenue
        assert f.operating_margin == pytest.approx(expected)

    def test_zero_revenue_margins(self):
        f = BusinessFinancials()
        assert f.gross_margin == 0.0
        assert f.operating_margin == 0.0


class TestLedger:
    def test_initial_balance(self):
        ledger = Ledger(opening_balance=500_000)
        assert ledger.balance() == 500_000

    def test_record_expense(self):
        ledger = Ledger(opening_balance=100_000)
        ledger.record(Transaction(amount=-20_000, type=TransactionType.ACQUISITION))
        assert ledger.balance() == pytest.approx(80_000)

    def test_record_income(self):
        ledger = Ledger(opening_balance=0)
        ledger.record(Transaction(amount=5_000, type=TransactionType.REVENUE))
        assert ledger.balance() == pytest.approx(5_000)

    def test_monthly_aggregates(self):
        ledger = Ledger(opening_balance=0)
        ledger.record(Transaction(amount=10_000, month=1, year=1, type=TransactionType.REVENUE))
        ledger.record(Transaction(amount=-3_000, month=1, year=1, type=TransactionType.LABOR))
        ledger.record(Transaction(amount=5_000, month=2, year=1, type=TransactionType.REVENUE))

        assert ledger.income_this_month(1, 1) == 10_000
        assert ledger.expenses_this_month(1, 1) == -3_000
        assert ledger.net_this_month(1, 1) == 7_000
        assert ledger.net_this_month(2, 1) == 5_000

    def test_transactions_for_business(self):
        ledger = Ledger(opening_balance=0)
        ledger.record(Transaction(amount=1_000, business_id="abc", type=TransactionType.REVENUE))
        ledger.record(Transaction(amount=2_000, business_id="xyz", type=TransactionType.REVENUE))
        biz_txns = ledger.transactions_for_business("abc")
        assert len(biz_txns) == 1
        assert biz_txns[0].business_id == "abc"


class TestFinanceUpdate:
    def test_update_business_financials_runs(self, simple_business):
        """update_business_financials should not raise and produce non-negative revenue."""
        clock = GameClock()
        update_business_financials(simple_business, seasonal_multiplier=clock.seasonal_multiplier)
        assert simple_business.financials.monthly_revenue >= 0

    def test_update_with_employee_labor(self, simple_business):
        update_business_financials(
            simple_business,
            seasonal_multiplier=1.0,
            employee_total_cost=12_000.0,
        )
        assert simple_business.financials.monthly_labor == pytest.approx(12_000.0)


class TestROI:
    def test_positive_roi(self):
        roi = compute_roi(monthly_cashflow=5_000, acquisition_cost=100_000, months_held=12)
        assert roi == pytest.approx(0.60)

    def test_zero_months(self):
        roi = compute_roi(monthly_cashflow=5_000, acquisition_cost=100_000, months_held=0)
        assert roi == 0.0

    def test_zero_cost(self):
        roi = compute_roi(monthly_cashflow=5_000, acquisition_cost=0, months_held=6)
        assert roi == 0.0
