"""Employee / staffing view."""
from __future__ import annotations

from models.employee import Employee, EmployeeStatus


def show_employee_list(employees: list[Employee], business_name: str = "") -> None:
    """Print a table of all employees for a business (HR metrics only).
    Financial cost data is shown in the financial reports view.
    """
    title = f"STAFF — {business_name}" if business_name else "STAFF"
    print(f"\n{'─' * 65}")
    print(f"  {title}")
    print(f"{'─' * 65}")
    print(f"  {'Name':<22} {'Role':<16} {'Status':<12} {'Skill':>5} {'Morale':>6}")
    print(f"  {'─' * 61}")
    for emp in employees:
        if emp.status == EmployeeStatus.TERMINATED:
            continue
        print(
            f"  {emp.name:<22} {emp.role.value:<16} {emp.status.value:<12} "
            f"{emp.skill_level:>5.0f} {emp.morale:>6.0f}"
        )
    active = [e for e in employees if e.status != EmployeeStatus.TERMINATED]
    headcount = len(active)
    avg_morale = (sum(e.morale for e in active) / headcount) if headcount else 0.0
    avg_skill = (sum(e.skill_level for e in active) / headcount) if headcount else 0.0
    print(f"  {'─' * 61}")
    print(
        f"  Total: {headcount} employees  |  "
        f"Avg Morale: {avg_morale:.0f}  |  "
        f"Avg Skill: {avg_skill:.0f}"
    )
    print(f"{'─' * 65}")


def show_job_postings(postings: list) -> None:
    """Print open job postings (role and applicant count only)."""
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
            f"Applicants: {applicant_count}  "
            f"Days open: {posting.days_open}"
        )
    print(f"{'─' * 55}")

