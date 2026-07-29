"""Employee / staffing view."""
from __future__ import annotations

from models.employee import Employee, EmployeeStatus
from employees.hr import employee_summary
from ui.reports import format_currency


def show_employee_list(employees: list[Employee], business_name: str = "") -> None:
    """Print a table of all employees for a business."""
    title = f"STAFF — {business_name}" if business_name else "STAFF"
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")
    print(f"  {'Name':<22} {'Role':<16} {'Status':<12} {'Skill':>5} {'Morale':>6} {'Monthly Cost':>13}")
    print(f"  {'─' * 66}")
    for emp in employees:
        if emp.status == EmployeeStatus.TERMINATED:
            continue
        print(
            f"  {emp.name:<22} {emp.role.value:<16} {emp.status.value:<12} "
            f"{emp.skill_level:>5.0f} {emp.morale:>6.0f} "
            f"{format_currency(emp.monthly_total_cost):>13}"
        )
    summary = employee_summary(employees)
    print(f"  {'─' * 66}")
    print(f"  Total: {summary['headcount']} employees  |  "
          f"Avg Morale: {summary['avg_morale']:.0f}  |  "
          f"Avg Skill: {summary['avg_skill']:.0f}  |  "
          f"Total Cost: {format_currency(summary['monthly_cost'])}/mo")
    print(f"{'─' * 70}")


def show_job_postings(postings: list) -> None:
    """Print open job postings."""
    if not postings:
        print("\n  No open job postings.")
        return
    print(f"\n{'─' * 55}")
    print("  OPEN JOB POSTINGS")
    print(f"{'─' * 55}")
    for posting in postings:
        applicant_count = len(posting.applicants)
        print(
            f"  [{posting.id}] {posting.role.value:<16}  "
            f"Salary: {format_currency(posting.offered_salary)}/yr  "
            f"Applicants: {applicant_count}  "
            f"Days open: {posting.days_open}"
        )
    print(f"{'─' * 55}")
