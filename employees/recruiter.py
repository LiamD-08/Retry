"""Recruitment system: posting jobs, reviewing applicants, making offers."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from config.balancing import (
    EMPLOYEE_SALARY_RANGES, DEFAULT_SALARY_RANGE,
    HIRING_SUCCESS_RATE_MIN, HIRING_SUCCESS_RATE_MAX,
    ONBOARDING_RAMP_WEEKS, BENEFITS_COST_RATE,
)
from models.employee import Employee, EmployeeRole, EmployeeStatus

# First names and last names used to generate candidate names
_FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie",
    "Quinn", "Avery", "Peyton", "Drew", "Blake", "Cameron", "Dana",
    "Evan", "Frankie", "Harper", "Jesse", "Kai", "Lee",
]
_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Wilson", "Moore", "Anderson", "Thomas",
    "Jackson", "White", "Harris", "Martin", "Thompson", "Young",
]


def _random_name() -> str:
    return f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"


@dataclass
class JobPosting:
    """A job opening posted by the player."""

    business_id: str
    role: EmployeeRole
    offered_salary: float
    days_open: int = 0
    applicants: list[Employee] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(random.randint(10000, 99999)))

    def age(self) -> None:
        self.days_open += 1
        # New applicants trickle in daily (probabilistic)
        if random.random() < 0.3:
            self.applicants.append(generate_applicant(self.role, self.offered_salary))


def generate_applicant(role: EmployeeRole, offered_salary: float) -> Employee:
    """Create a randomised job applicant for the given role."""
    salary_range = EMPLOYEE_SALARY_RANGES.get(role.value, DEFAULT_SALARY_RANGE)
    # Skill level roughly correlates with expected salary
    mid_salary = (salary_range[0] + salary_range[1]) / 2
    salary_ratio = offered_salary / max(mid_salary, 1)
    # Better pay → higher average applicant quality
    skill = random.gauss(40 + salary_ratio * 20, 15)
    skill = max(5.0, min(100.0, skill))

    emp = Employee(
        name=_random_name(),
        role=role,
        skill_level=skill,
        annual_salary=offered_salary,
        morale=random.uniform(60.0, 90.0),
        status=EmployeeStatus.APPLICANT,
        onboarding_weeks_remaining=ONBOARDING_RAMP_WEEKS,
    )
    emp.benefits_cost_annual = offered_salary * BENEFITS_COST_RATE
    return emp


def make_offer(applicant: Employee, business_id: str) -> bool:
    """
    Attempt to hire *applicant*. Returns True if they accept.
    Probability of acceptance depends on salary competitiveness.
    """
    acceptance_rate = random.uniform(HIRING_SUCCESS_RATE_MIN, HIRING_SUCCESS_RATE_MAX)
    if random.random() < acceptance_rate:
        applicant.status = EmployeeStatus.ONBOARDING
        applicant.business_id = business_id
        applicant.onboarding_weeks_remaining = ONBOARDING_RAMP_WEEKS
        return True
    return False


def post_job(
    business_id: str,
    role: EmployeeRole,
    offered_salary: float | None = None,
) -> JobPosting:
    """Create a new job posting for *business_id*."""
    salary_range = EMPLOYEE_SALARY_RANGES.get(role.value, DEFAULT_SALARY_RANGE)
    if offered_salary is None:
        offered_salary = (salary_range[0] + salary_range[1]) / 2
    return JobPosting(
        business_id=business_id,
        role=role,
        offered_salary=offered_salary,
    )
