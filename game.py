"""
Business Turnaround Simulation Game
====================================
Main entry point. Run with: python game.py
"""
from __future__ import annotations

import sys

from businesses.marketplace import refresh_marketplace
from core.simulation import Simulation
from employees.recruiter import post_job, make_offer
from models.employee import EmployeeRole
from ui.business_view import show_business_detail
from ui.dashboard import show_dashboard, show_marketplace
from ui.employee_view import show_employee_list, show_job_postings
from ui.reports import format_currency, print_pl_report, print_kpi_report


def _input(prompt: str) -> str:
    """Wrapper around input() so tests can patch it easily."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting game.")
        sys.exit(0)


def main_menu(sim: Simulation) -> str:
    print("\n" + "=" * 40)
    print("  MAIN MENU")
    print("=" * 40)
    print("  [1] Dashboard (portfolio overview)")
    print("  [2] Marketplace (browse & acquire)")
    print("  [3] Manage a business")
    print("  [4] Staffing")
    print("  [5] Advance time")
    print("  [6] Financial reports")
    print("  [0] Quit")
    print("=" * 40)
    return _input("Choice: ")


# ---------------------------------------------------------------------------
# Sub-menus
# ---------------------------------------------------------------------------

def menu_dashboard(sim: Simulation) -> None:
    businesses = sim.manager.all_businesses()
    show_dashboard(sim.clock, sim.player.ledger, businesses)


def menu_marketplace(sim: Simulation) -> None:
    while True:
        show_marketplace(sim.marketplace.listings)
        print("\n  [B] Buy (buyout)  [R] Rent/Lease  [X] Refresh  [Q] Back")
        choice = _input("Choice: ").upper()

        if choice == "Q":
            break

        if choice == "X":
            refresh_marketplace(sim.marketplace)
            print("  Marketplace refreshed.")
            continue

        if choice in ("B", "R"):
            idx = _input("  Enter listing number: ")
            try:
                idx = int(idx) - 1
                listing = sim.marketplace.listings[idx]
            except (ValueError, IndexError):
                print("  Invalid selection.")
                continue

            mode = "buyout" if choice == "B" else "rent"
            biz = listing.business
            show_business_detail(biz)
            confirm = _input(f"  Acquire '{biz.name}' via {mode}? [y/N]: ").lower()
            if confirm == "y":
                success, msg = sim.acquire_business(biz.id, mode)
                print(f"\n  {msg}")


def menu_manage_business(sim: Simulation) -> None:
    businesses = sim.manager.all_businesses()
    if not businesses:
        print("\n  You have no owned businesses.")
        return

    print("\n  Your businesses:")
    for i, b in enumerate(businesses, 1):
        print(f"  [{i}] {b.name} ({b.sector})")

    idx = _input("Select business number (or Q to go back): ").strip()
    if idx.upper() == "Q":
        return
    try:
        biz = businesses[int(idx) - 1]
    except (ValueError, IndexError):
        print("  Invalid selection.")
        return

    employees = sim.manager._get_employees(biz.id)
    show_business_detail(biz, employees)

    while True:
        print("\n  ACTIONS:")
        print("  [1] Queue maintenance upgrade")
        print("  [2] Queue marketing campaign")
        print("  [3] Queue staff training")
        print("  [4] Queue debt restructuring")
        print("  [5] Pay down debt")
        print("  [6] Sell business")
        print("  [Q] Back")
        action = _input("Choice: ").upper()

        if action == "Q":
            break

        elif action == "1":
            spend_str = _input(f"  Maintenance spend (default ${biz.asset_value * 0.05:,.0f}): $")
            try:
                spend = float(spend_str) if spend_str else biz.asset_value * 0.05
            except ValueError:
                spend = biz.asset_value * 0.05
            sim.queue_action(biz.id, "maintenance_upgrade", {"spend": spend})
            print(f"  Queued maintenance upgrade (${spend:,.0f}) — resolves at month-end.")

        elif action == "2":
            spend_str = _input(f"  Marketing budget (default ${biz.financials.monthly_revenue * 0.05:,.0f}): $")
            try:
                spend = float(spend_str) if spend_str else biz.financials.monthly_revenue * 0.05
            except ValueError:
                spend = biz.financials.monthly_revenue * 0.05
            sim.queue_action(biz.id, "marketing", {"spend": spend})
            print(f"  Queued marketing campaign (${spend:,.0f}) — resolves at month-end.")

        elif action == "3":
            weeks_str = _input("  Training weeks (default 4): ")
            try:
                weeks = int(weeks_str) if weeks_str else 4
            except ValueError:
                weeks = 4
            sim.queue_action(biz.id, "training", {"weeks": weeks, "spend": 500.0})
            print(f"  Queued {weeks}-week staff training — resolves at month-end.")

        elif action == "4":
            if biz.debt <= 0:
                print("  No debt to restructure.")
            else:
                confirm = _input(f"  Restructure ${biz.debt:,.0f} debt (fee: ${biz.debt * 0.02:,.0f})? [y/N]: ").lower()
                if confirm == "y":
                    sim.queue_action(biz.id, "debt_restructure", {})
                    print("  Debt restructuring queued — resolves at month-end.")

        elif action == "5":
            amount_str = _input(f"  Amount to pay off (max ${biz.debt:,.0f}): $")
            try:
                amount = float(amount_str)
            except ValueError:
                print("  Invalid amount.")
                continue
            if amount > sim.player.cash:
                print("  Insufficient cash.")
                continue
            sim.queue_action(biz.id, "pay_down_debt", {"amount": amount})
            print(f"  Queued debt paydown of ${amount:,.0f} — resolves at month-end.")

        elif action == "6":
            from economy.finance import compute_valuation
            low, high = compute_valuation(biz)
            print(f"\n  Estimated sale value: {format_currency(low)} – {format_currency(high)}")
            confirm = _input("  Confirm sale? [y/N]: ").lower()
            if confirm == "y":
                success, msg, details = sim.sell_business(biz.id)
                print(f"\n  {msg}")
                break


def menu_staffing(sim: Simulation) -> None:
    businesses = sim.manager.all_businesses()
    if not businesses:
        print("\n  No owned businesses.")
        return

    print("\n  Select business:")
    for i, b in enumerate(businesses, 1):
        print(f"  [{i}] {b.name}")
    idx = _input("Business number (or Q): ")
    if idx.upper() == "Q":
        return
    try:
        biz = businesses[int(idx) - 1]
    except (ValueError, IndexError):
        print("  Invalid selection.")
        return

    employees = sim.manager._get_employees(biz.id)
    show_employee_list(employees, biz.name)

    print("\n  [1] Hire employee  [2] Fire employee  [Q] Back")
    choice = _input("Choice: ").upper()

    if choice == "1":
        roles = list(EmployeeRole)
        print("  Roles:")
        for i, r in enumerate(roles, 1):
            print(f"    [{i}] {r.value}")
        role_idx = _input("  Select role: ")
        try:
            role = roles[int(role_idx) - 1]
        except (ValueError, IndexError):
            print("  Invalid role.")
            return

        from config.balancing import EMPLOYEE_SALARY_RANGES, DEFAULT_SALARY_RANGE
        salary_range = EMPLOYEE_SALARY_RANGES.get(role.value, DEFAULT_SALARY_RANGE)
        sal_str = _input(f"  Salary (${salary_range[0]:,.0f}–${salary_range[1]:,.0f}): $")
        try:
            salary = float(sal_str)
        except ValueError:
            salary = (salary_range[0] + salary_range[1]) / 2

        posting = post_job(biz.id, role, salary)
        # Immediately generate some applicants
        for _ in range(3):
            posting.age()

        if not posting.applicants:
            print("  No applicants found yet.")
            return

        print(f"\n  Applicants for {role.value}:")
        for i, app in enumerate(posting.applicants, 1):
            print(f"  [{i}] {app.name:<22} Skill: {app.skill_level:.0f}  Cost/mo: {format_currency(app.monthly_total_cost)}")

        pick = _input("  Select applicant to hire (or Q): ")
        if pick.upper() == "Q":
            return
        try:
            applicant = posting.applicants[int(pick) - 1]
        except (ValueError, IndexError):
            print("  Invalid selection.")
            return

        success = make_offer(applicant, biz.id)
        if success:
            sim.manager.hire_employee(biz.id, applicant)
            print(f"  {applicant.name} accepted the offer! They start onboarding.")
        else:
            print(f"  {applicant.name} declined the offer.")

    elif choice == "2":
        if not employees:
            print("  No employees to fire.")
            return
        print("  Select employee to fire:")
        for i, emp in enumerate(employees, 1):
            print(f"  [{i}] {emp.name} ({emp.role.value})")
        pick = _input("  Employee number (or Q): ")
        if pick.upper() == "Q":
            return
        try:
            emp = employees[int(pick) - 1]
        except (ValueError, IndexError):
            print("  Invalid selection.")
            return
        confirm = _input(f"  Fire {emp.name}? Severance: {format_currency((emp.annual_salary/52)*4)} [y/N]: ").lower()
        if confirm == "y":
            severance = sim.manager.fire_employee(biz.id, emp.id)
            print(f"  {emp.name} has been terminated. Severance paid: {format_currency(severance)}")


def menu_advance_time(sim: Simulation) -> None:
    print("\n  [1] Advance 1 day")
    print("  [2] Advance 1 week (7 days)")
    print("  [3] Advance 1 month (30 days)")
    print("  [4] Advance 3 months")
    print("  [Q] Back")
    choice = _input("Choice: ").upper()

    if choice == "1":
        days = 1
    elif choice == "2":
        days = 7
    elif choice == "3":
        days = 30
    elif choice == "4":
        days = 90
    else:
        return

    print(f"\n  Advancing {days} day(s)...")
    log = sim.tick(days)

    if log:
        print(f"\n  --- Events ---")
        for line in log[-20:]:  # show last 20 events
            print(f"  {line}")

    print(f"\n  Date is now: {sim.clock.date_string}")
    print(f"  Cash balance: {format_currency(sim.player.cash)}")


def menu_reports(sim: Simulation) -> None:
    businesses = sim.manager.all_businesses()
    if not businesses:
        print("\n  No owned businesses.")
        return

    for biz in businesses:
        print_pl_report(biz)
        print_kpi_report(biz)

    from ui.reports import print_ledger_summary
    print_ledger_summary(sim.player.ledger, sim.clock.month, sim.clock.year)


# ---------------------------------------------------------------------------
# Game entry point
# ---------------------------------------------------------------------------

def run_game() -> None:
    print("\n" + "=" * 60)
    print("  BUSINESS TURNAROUND SIMULATOR")
    print("  You are a turnaround specialist. Acquire failing businesses,")
    print("  fix them, and profit.")
    print("=" * 60)

    from config.balancing import INITIAL_CAPITAL
    sim = Simulation(starting_capital=INITIAL_CAPITAL)
    print(f"\n  Starting capital: {format_currency(sim.player.cash)}")
    print(f"  Date: {sim.clock.date_string}")
    print("  The marketplace has been populated with businesses for you to review.")

    while True:
        choice = main_menu(sim)

        if choice == "1":
            menu_dashboard(sim)
        elif choice == "2":
            menu_marketplace(sim)
        elif choice == "3":
            menu_manage_business(sim)
        elif choice == "4":
            menu_staffing(sim)
        elif choice == "5":
            menu_advance_time(sim)
        elif choice == "6":
            menu_reports(sim)
        elif choice == "0":
            print("\n  Thanks for playing. Goodbye!")
            break
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    run_game()
