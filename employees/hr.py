"""HR system: compensation management, morale, and turnover handling."""
from __future__ import annotations

from config.balancing import (
    LAYOFF_COST_WEEKS, MORALE_DECAY_RATE, BENEFITS_COST_RATE,
)
from models.employee import Employee, EmployeeStatus
from employees.performance import check_turnover, boost_morale


def monthly_hr_tick(employees: list[Employee]) -> list[str]:
    """
    Process monthly HR events for a list of employees.
    Returns a list of event messages.
    """
    events: list[str] = []

    for emp in employees:
        if emp.status == EmployeeStatus.TERMINATED:
            continue

        # Tenure milestone morale boosts (every 12 weeks ≈ 3 months)
        if int(emp.tenure_weeks) % 12 == 0 and int(emp.tenure_weeks) > 0:
            boost_morale(emp, 5.0)

    return events


def daily_hr_tick(employees: list[Employee]) -> list[tuple[str, Employee]]:
    """
    Process daily HR events. Returns list of (event_type, employee) tuples.
    event_type: "quit"
    """
    events = []
    for emp in list(employees):
        emp.daily_tick()
        if check_turnover(emp):
            emp.status = EmployeeStatus.TERMINATED
            events.append(("quit", emp))
    return events


def terminate_employee(employee: Employee, annual_salary: float | None = None) -> float:
    """
    Lay off an employee. Returns the severance cost ($).
    """
    employee.status = EmployeeStatus.TERMINATED
    salary = annual_salary if annual_salary is not None else employee.annual_salary
    severance = (salary / 52) * LAYOFF_COST_WEEKS
    return severance


def give_raise(employee: Employee, raise_pct: float) -> float:
    """
    Give an employee a salary raise. Returns the annual increase ($).
    raise_pct: fraction of current salary (e.g. 0.05 = 5%).
    """
    increase = employee.annual_salary * raise_pct
    employee.annual_salary += increase
    employee.benefits_cost_annual = employee.annual_salary * BENEFITS_COST_RATE
    boost_morale(employee, raise_pct * 200)  # e.g. 5% raise → +10 morale
    return increase


def update_benefits(employee: Employee) -> None:
    """Recalculate benefits cost based on current salary."""
    employee.benefits_cost_annual = employee.annual_salary * BENEFITS_COST_RATE


def employee_summary(employees: list[Employee]) -> dict:
    """Return a dict of aggregate stats for a list of employees."""
    active = [e for e in employees if e.status != EmployeeStatus.TERMINATED]
    if not active:
        return {
            "headcount": 0,
            "avg_morale": 0.0,
            "avg_skill": 0.0,
            "monthly_cost": 0.0,
        }
    return {
        "headcount": len(active),
        "avg_morale": sum(e.morale for e in active) / len(active),
        "avg_skill": sum(e.skill_level for e in active) / len(active),
        "monthly_cost": sum(e.monthly_total_cost for e in active),
    }
