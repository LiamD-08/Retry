"""Financial reports view."""
from __future__ import annotations

from models.business import Business
from models.financial import Ledger


def format_currency(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def print_pl_report(business: Business) -> None:
    """Print a formatted P&L statement for a business."""
    f = business.financials
    lines = [
        f"\n{'=' * 50}",
        f"  P&L REPORT — {business.name}",
        f"{'=' * 50}",
        f"  Revenue:              {format_currency(f.monthly_revenue):>14}",
        f"  COGS:                 {format_currency(-f.monthly_cogs):>14}",
        f"  {'─' * 34}",
        f"  Gross Profit:         {format_currency(f.gross_profit):>14}  ({f.gross_margin:.1%})",
        f"",
        f"  Labor:                {format_currency(-f.monthly_labor):>14}",
        f"  Overhead:             {format_currency(-f.monthly_overhead):>14}",
        f"  Maintenance:          {format_currency(-f.monthly_maintenance):>14}",
        f"  Depreciation:         {format_currency(-f.monthly_depreciation):>14}",
        f"  {'─' * 34}",
        f"  EBITDA:               {format_currency(f.ebitda):>14}",
        f"  Operating Income:     {format_currency(f.operating_income):>14}  ({f.operating_margin:.1%})",
        f"",
        f"  Debt Service:         {format_currency(-f.monthly_debt_service):>14}",
        f"  {'─' * 34}",
        f"  Net Income:           {format_currency(f.net_income):>14}",
        f"  Cashflow:             {format_currency(f.cashflow):>14}",
        f"{'=' * 50}",
    ]
    print("\n".join(lines))


def print_kpi_report(business: Business) -> None:
    """Print a KPI summary for a business."""
    k = business.kpis
    lines = [
        f"\n{'─' * 50}",
        f"  KPIs — {business.name}",
        f"{'─' * 50}",
        f"  Customer Satisfaction:  {k.customer_satisfaction:>5.1f} / 100",
        f"  Utilization:            {k.utilization:>5.1f} / 100",
        f"  Quality Score:          {k.quality_score:>5.1f} / 100",
        f"  Reputation:             {k.reputation:>5.1f} / 100",
        f"  Monthly Churn:          {k.churn_rate:>6.1%}",
        f"  Asset Condition:        {business.condition:>5.1f} / 100",
        f"{'─' * 50}",
    ]
    print("\n".join(lines))


def print_ledger_summary(ledger: Ledger, month: int, year: int) -> None:
    """Print a summary of ledger activity for the current month."""
    income = ledger.income_this_month(month, year)
    expenses = ledger.expenses_this_month(month, year)
    net = ledger.net_this_month(month, year)
    balance = ledger.balance()

    lines = [
        f"\n{'─' * 50}",
        f"  CASHFLOW SUMMARY (Month {month}, Year {year})",
        f"{'─' * 50}",
        f"  Income:               {format_currency(income):>14}",
        f"  Expenses:             {format_currency(expenses):>14}",
        f"  Net:                  {format_currency(net):>14}",
        f"  Cash Balance:         {format_currency(balance):>14}",
        f"{'─' * 50}",
    ]
    print("\n".join(lines))
