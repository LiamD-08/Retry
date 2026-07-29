"""Employee productivity and quality calculations."""
from __future__ import annotations

import random

from config.balancing import UNCERTAINTY_FACTOR
from models.employee import Employee, EmployeeStatus


def team_productivity(employees: list[Employee]) -> float:
    """
    Aggregate productivity of a list of employees (0–100).
    Returns 0 if no active employees.
    """
    active = [e for e in employees if e.status in (EmployeeStatus.ACTIVE, EmployeeStatus.TRAINING, EmployeeStatus.ONBOARDING)]
    if not active:
        return 0.0
    return sum(e.effective_productivity for e in active) / len(active)


def team_quality_contribution(employees: list[Employee]) -> float:
    """
    Average skill level of active employees as a quality contribution (0–100).
    """
    active = [e for e in employees if e.status in (EmployeeStatus.ACTIVE, EmployeeStatus.TRAINING)]
    if not active:
        return 0.0
    return sum(e.skill_level for e in active) / len(active)


def team_morale(employees: list[Employee]) -> float:
    """Average morale across all non-terminated employees."""
    active = [e for e in employees if e.status != EmployeeStatus.TERMINATED]
    if not active:
        return 0.0
    return sum(e.morale for e in active) / len(active)


def total_monthly_labor_cost(employees: list[Employee]) -> float:
    """Sum of monthly salary + benefits for all non-terminated employees."""
    return sum(
        e.monthly_total_cost for e in employees
        if e.status != EmployeeStatus.TERMINATED
    )


def apply_productivity_to_capacity(
    base_utilization: float,
    productivity: float,
) -> float:
    """
    Adjust utilization based on team productivity.
    High productivity → can serve more customers / run at higher capacity.
    """
    productivity_factor = productivity / 100
    adjustment = (productivity_factor - 0.5) * 10  # ±5 points at extremes
    return max(0.0, min(100.0, base_utilization + adjustment))


def check_turnover(
    employee: Employee,
) -> bool:
    """
    Return True if the employee voluntarily quits this tick (daily check).
    Probability increases as morale drops.
    """
    from config.balancing import TURNOVER_MORALE_THRESHOLD, TURNOVER_DAILY_PROBABILITY
    if employee.status in (EmployeeStatus.TERMINATED, EmployeeStatus.APPLICANT):
        return False
    if employee.morale < TURNOVER_MORALE_THRESHOLD:
        # Probability scales inversely with morale below threshold
        p = TURNOVER_DAILY_PROBABILITY * (1 + (TURNOVER_MORALE_THRESHOLD - employee.morale) / 10)
        return random.random() < p
    return False


def boost_morale(employee: Employee, amount: float) -> None:
    """Increase employee morale by *amount* (capped at 100)."""
    employee.morale = min(100.0, employee.morale + amount)


def apply_training(employee: Employee, weeks: int, skill_gain_per_week: float = 3.0) -> None:
    """
    Start a training programme for *employee*.
    Training takes *weeks* and improves skill by *skill_gain_per_week* per week.
    """
    employee.status = EmployeeStatus.TRAINING
    employee.training_weeks_remaining = weeks
    employee.training_skill_gain = skill_gain_per_week
