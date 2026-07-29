"""Main dashboard: portfolio overview and player status."""
from __future__ import annotations

from core.clock import GameClock
from models.business import Business, BusinessStatus
from models.financial import Ledger
from ui.reports import format_currency


def show_dashboard(
    clock: GameClock,
    ledger: Ledger,
    businesses: list[Business],
) -> None:
    """Print the main portfolio dashboard."""
    balance = ledger.balance()
    monthly_cashflow = sum(b.financials.cashflow for b in businesses if b.status == BusinessStatus.OWNED)
    profitable_count = sum(
        1 for b in businesses
        if b.status == BusinessStatus.OWNED and b.financials.net_income >= 0
    )
    owned = [b for b in businesses if b.status == BusinessStatus.OWNED]

    print(f"\n{'═' * 60}")
    print(f"  BUSINESS TURNAROUND SIMULATOR")
    print(f"  Date: {clock.date_string}")
    print(f"{'═' * 60}")
    print(f"  Cash Balance:         {format_currency(balance):>14}")
    print(f"  Monthly Portfolio CF: {format_currency(monthly_cashflow):>14}")
    print(f"  Businesses Owned:     {len(owned):>14}")
    print(f"  Profitable:           {profitable_count:>14} / {len(owned)}")
    print(f"{'─' * 60}")

    if not owned:
        print("  No businesses in portfolio. Visit the marketplace to acquire one.")
    else:
        print(f"  {'#':<3} {'Name':<25} {'Sector':<12} {'Net Income':>12} {'Cashflow':>12}")
        print(f"  {'─' * 56}")
        for i, biz in enumerate(owned, 1):
            ni = biz.financials.net_income
            cf = biz.financials.cashflow
            ni_str = format_currency(ni)
            cf_str = format_currency(cf)
            flag = "✓" if ni >= 0 else "✗"
            print(f"  {flag}{i:<3} {biz.name:<25} {biz.sector:<12} {ni_str:>12} {cf_str:>12}")

    print(f"{'═' * 60}")


def show_marketplace(listings) -> None:
    """Print available businesses on the marketplace."""
    print(f"\n{'─' * 65}")
    print("  MARKETPLACE — Available Businesses")
    print(f"{'─' * 65}")
    if not listings:
        print("  No businesses available. Advance time to refresh.")
    else:
        print(f"  {'#':<3} {'Name':<25} {'Sector':<12} {'Asking Price':>13} {'Monthly Lease':>14}")
        print(f"  {'─' * 60}")
        for i, listing in enumerate(listings, 1):
            b = listing.business
            print(
                f"  {i:<3} {b.name:<25} {b.sector:<12} "
                f"{format_currency(b.asking_price):>13} "
                f"{format_currency(b.monthly_lease):>14}/mo"
            )
            if listing.notes:
                print(f"       {listing.notes}")
    print(f"{'─' * 65}")
