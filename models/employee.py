"""Data model for an employee in the simulation."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class EmployeeRole(Enum):
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    SKILLED_WORKER = "skilled_worker"
    WORKER = "worker"
    INTERN = "intern"


class EmployeeStatus(Enum):
    APPLICANT = "applicant"     # In recruitment pipeline
    ONBOARDING = "onboarding"   # Hired, still ramping up
    ACTIVE = "active"           # Fully productive
    TRAINING = "training"       # Undergoing skill training
    TERMINATED = "terminated"   # Left or laid off


@dataclass
class Employee:
    """Represents a single employee."""

    name: str = "Unnamed Employee"
    role: EmployeeRole = EmployeeRole.WORKER
    skill_level: float = 50.0          # 0–100
    annual_salary: float = 40_000.0    # Base annual salary ($)
    benefits_cost_annual: float = 0.0  # Annual benefits cost ($)
    morale: float = 70.0               # 0–100
    tenure_weeks: int = 0              # Weeks employed at current business
    status: EmployeeStatus = EmployeeStatus.APPLICANT

    # Ramp-up: new hires are less productive until fully onboarded
    onboarding_weeks_remaining: int = 4

    # Training state
    training_weeks_remaining: int = 0
    training_skill_gain: float = 0.0   # Skill gain per week during training

    # Performance variability (daily noise around base productivity)
    performance_variance: float = 0.10  # ±10%

    # Unique identifier
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Business this employee is assigned to (None if unassigned)
    business_id: Optional[str] = None

    def __post_init__(self):
        if self.benefits_cost_annual == 0.0:
            from config.balancing import BENEFITS_COST_RATE
            self.benefits_cost_annual = self.annual_salary * BENEFITS_COST_RATE

    @property
    def monthly_salary(self) -> float:
        return self.annual_salary / 12

    @property
    def monthly_benefits(self) -> float:
        return self.benefits_cost_annual / 12

    @property
    def monthly_total_cost(self) -> float:
        return self.monthly_salary + self.monthly_benefits

    @property
    def effective_productivity(self) -> float:
        """0–100: productivity factoring in skill, morale, and onboarding ramp."""
        base = self.skill_level * (self.morale / 100)
        if self.status == EmployeeStatus.ONBOARDING:
            from config.balancing import ONBOARDING_RAMP_WEEKS
            ramp_fraction = 1 - (self.onboarding_weeks_remaining / max(ONBOARDING_RAMP_WEEKS, 1))
            base *= max(0.3, ramp_fraction)
        return min(100.0, max(0.0, base))

    def daily_tick(self) -> None:
        """Advance employee state by one day."""
        from config.balancing import MORALE_DECAY_RATE, DAYS_PER_MONTH

        # Morale slowly decays without intervention
        self.morale = max(0.0, self.morale - MORALE_DECAY_RATE)

        # Weekly updates (approximate as every 7th day via tenure)
        self.tenure_weeks += 1 / 7  # fractional weeks

        # Onboarding ramp
        if self.status == EmployeeStatus.ONBOARDING:
            self.onboarding_weeks_remaining = max(0, self.onboarding_weeks_remaining - 1 / 7)
            if self.onboarding_weeks_remaining <= 0:
                self.status = EmployeeStatus.ACTIVE

        # Training progression
        if self.status == EmployeeStatus.TRAINING:
            self.training_weeks_remaining = max(0, self.training_weeks_remaining - 1 / 7)
            self.skill_level = min(100.0, self.skill_level + self.training_skill_gain / 7)
            if self.training_weeks_remaining <= 0:
                self.status = EmployeeStatus.ACTIVE
                self.training_skill_gain = 0.0


# Resolve Optional hint without full typing import overhead
from typing import Optional
Employee.__annotations__["business_id"] = Optional[str]
