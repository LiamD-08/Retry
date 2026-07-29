"""Business detail view: shows full info for a single business."""
from __future__ import annotations

from models.business import Business, AcquisitionType
from economy.finance import compute_valuation
from ui.reports import format_currency, print_pl_report, print_kpi_report


def show_business_detail(business: Business, employees: list | None = None) -> None:
    """Print a detailed overview of a single business."""
    acq = "Rented" if business.acquisition_type == AcquisitionType.RENT else (
        "Owned (Buyout)" if business.acquisition_type == AcquisitionType.BUYOUT else "Available"
    )
    low, high = compute_valuation(business)

    header = [
        f"\n{'#' * 55}",
        f"  {business.name.upper()}",
        f"  Sector: {business.sector.title()}  |  Size: {business.size.value.title()}",
        f"  Status: {acq}  |  Days Owned: {business.days_owned}",
        f"  Asking Price: {format_currency(business.asking_price)}  |  Monthly Lease: {format_currency(business.monthly_lease)}",
        f"  Asset Value: {format_currency(business.asset_value)}  |  Outstanding Debt: {format_currency(business.debt)}",
        f"  Estimated Value: {format_currency(low)} – {format_currency(high)}",
        f"{'#' * 55}",
    ]
    print("\n".join(header))

    print_pl_report(business)
    print_kpi_report(business)

    if employees:
        print(f"\n  Employees ({len(employees)}):")
        for emp in employees:
            print(
                f"    • {emp.name:<20} {emp.role.value:<15} "
                f"Skill: {emp.skill_level:.0f}  Morale: {emp.morale:.0f}  "
                f"Cost/mo: {format_currency(emp.monthly_total_cost)}"
            )
