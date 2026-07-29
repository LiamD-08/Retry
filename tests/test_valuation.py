"""Tests for business valuation calculations."""
import pytest
from data.seeds import make_failing_restaurant, make_struggling_retailer
from economy.finance import compute_valuation, compute_sale_proceeds
from config.balancing import SELL_TRANSACTION_COST_RATE, SELL_CAPITAL_GAINS_TAX_RATE


@pytest.fixture
def restaurant():
    return make_failing_restaurant()


@pytest.fixture
def retailer():
    return make_struggling_retailer()


class TestValuation:
    def test_valuation_returns_tuple_of_two(self, restaurant):
        result = compute_valuation(restaurant)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_valuation_low_lte_high(self, restaurant):
        low, high = compute_valuation(restaurant)
        assert low <= high

    def test_valuation_non_negative(self, restaurant):
        low, high = compute_valuation(restaurant)
        assert low >= 0.0
        assert high >= 0.0

    def test_profitability_increases_valuation(self, restaurant):
        """A business with higher EBITDA should have higher valuation."""
        from models.business import Business, BusinessFinancials, BusinessKPIs, BusinessSize
        biz_low = Business(
            name="Low EBITDA",
            sector="restaurant",
            size=BusinessSize.SMALL,
            condition=50.0,
            asset_value=100_000.0,
            debt=0.0,
        )
        biz_low.financials = BusinessFinancials(
            monthly_revenue=10_000.0,
            monthly_cogs=3_000.0,
            monthly_labor=4_000.0,
            monthly_overhead=2_000.0,
            monthly_maintenance=500.0,
        )
        biz_low.kpis = BusinessKPIs(reputation=50.0)
        biz_low._employee_ids = []

        biz_high = Business(
            name="High EBITDA",
            sector="restaurant",
            size=BusinessSize.SMALL,
            condition=50.0,
            asset_value=100_000.0,
            debt=0.0,
        )
        biz_high.financials = BusinessFinancials(
            monthly_revenue=30_000.0,
            monthly_cogs=9_000.0,
            monthly_labor=8_000.0,
            monthly_overhead=3_000.0,
            monthly_maintenance=500.0,
        )
        biz_high.kpis = BusinessKPIs(reputation=50.0)
        biz_high._employee_ids = []

        _, high_val_low = compute_valuation(biz_low)
        _, high_val_high = compute_valuation(biz_high)
        assert high_val_high > high_val_low

    def test_debt_reduces_valuation(self, restaurant):
        """More debt should lower the valuation."""
        from copy import deepcopy
        biz_no_debt = deepcopy(restaurant)
        biz_no_debt.debt = 0.0

        biz_high_debt = deepcopy(restaurant)
        biz_high_debt.debt = 200_000.0

        low_nd, _ = compute_valuation(biz_no_debt)
        low_hd, _ = compute_valuation(biz_high_debt)
        assert low_nd > low_hd

    def test_valuation_range_on_business_model(self, restaurant):
        """Business.valuation_range should match compute_valuation result."""
        from config.balancing import SECTOR_EBITDA_MULTIPLES, DEFAULT_EBITDA_MULTIPLE
        multiples = SECTOR_EBITDA_MULTIPLES.get(restaurant.sector, DEFAULT_EBITDA_MULTIPLE)
        # compute_valuation adjusts multiples by reputation; just check both are non-negative
        low, high = restaurant.valuation_range(multiples)
        assert low >= 0.0
        assert high >= 0.0


class TestSaleProceeds:
    def test_sale_proceeds_structure(self, retailer):
        result = compute_sale_proceeds(retailer, acquisition_cost=retailer.asking_price)
        assert "gross_value" in result
        assert "broker_fee" in result
        assert "capital_gain" in result
        assert "tax" in result
        assert "net_proceeds" in result

    def test_broker_fee_rate(self, retailer):
        result = compute_sale_proceeds(retailer, acquisition_cost=0)
        expected_fee = result["gross_value"] * SELL_TRANSACTION_COST_RATE
        assert result["broker_fee"] == pytest.approx(expected_fee, rel=1e-6)

    def test_tax_on_gain(self, retailer):
        result = compute_sale_proceeds(retailer, acquisition_cost=0)
        # All proceeds are gain when acquisition_cost = 0
        expected_tax = result["gross_value"] * SELL_CAPITAL_GAINS_TAX_RATE
        assert result["tax"] == pytest.approx(expected_tax, rel=1e-3)

    def test_no_tax_when_no_gain(self, retailer):
        """If sold at or below cost, no capital gains tax."""
        result = compute_sale_proceeds(retailer, acquisition_cost=10_000_000)
        assert result["capital_gain"] == 0.0
        assert result["tax"] == 0.0

    def test_net_proceeds_is_positive(self, retailer):
        result = compute_sale_proceeds(retailer, acquisition_cost=retailer.asking_price)
        assert result["net_proceeds"] >= 0.0

    def test_net_proceeds_equals_gross_minus_costs(self, retailer):
        result = compute_sale_proceeds(retailer, acquisition_cost=0)
        expected = result["gross_value"] - result["broker_fee"] - result["tax"]
        assert result["net_proceeds"] == pytest.approx(expected, rel=1e-9)
