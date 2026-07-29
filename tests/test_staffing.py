"""Tests for the employee / staffing system."""
import pytest
from models.employee import Employee, EmployeeRole, EmployeeStatus
from employees.performance import (
    team_productivity, team_quality_contribution, team_morale,
    total_monthly_labor_cost, check_turnover, apply_training, boost_morale,
)
from employees.hr import (
    terminate_employee, give_raise, employee_summary, daily_hr_tick,
)
from employees.recruiter import generate_applicant, make_offer, post_job
from config.balancing import BENEFITS_COST_RATE, LAYOFF_COST_WEEKS


@pytest.fixture
def active_employee():
    emp = Employee(
        name="Alice Smith",
        role=EmployeeRole.WORKER,
        skill_level=70.0,
        annual_salary=40_000.0,
        morale=75.0,
        status=EmployeeStatus.ACTIVE,
    )
    emp.onboarding_weeks_remaining = 0
    return emp


@pytest.fixture
def onboarding_employee():
    return Employee(
        name="Bob Jones",
        role=EmployeeRole.WORKER,
        skill_level=60.0,
        annual_salary=38_000.0,
        morale=80.0,
        status=EmployeeStatus.ONBOARDING,
        onboarding_weeks_remaining=4,
    )


@pytest.fixture
def team(active_employee, onboarding_employee):
    return [active_employee, onboarding_employee]


class TestEmployeeModel:
    def test_monthly_salary(self, active_employee):
        assert active_employee.monthly_salary == pytest.approx(40_000 / 12)

    def test_benefits_cost(self, active_employee):
        expected = 40_000 * BENEFITS_COST_RATE
        assert active_employee.benefits_cost_annual == pytest.approx(expected)

    def test_monthly_total_cost(self, active_employee):
        expected = (40_000 + 40_000 * BENEFITS_COST_RATE) / 12
        assert active_employee.monthly_total_cost == pytest.approx(expected)

    def test_effective_productivity_active(self, active_employee):
        prod = active_employee.effective_productivity
        # Expected ≈ skill * morale/100 = 70 * 0.75 = 52.5
        assert prod == pytest.approx(52.5, abs=1e-6)

    def test_effective_productivity_onboarding_is_lower(self, onboarding_employee, active_employee):
        # Onboarding employee should have lower effective productivity
        assert onboarding_employee.effective_productivity < active_employee.effective_productivity


class TestTeamMetrics:
    def test_team_productivity_empty(self):
        assert team_productivity([]) == 0.0

    def test_team_productivity_single(self, active_employee):
        prod = team_productivity([active_employee])
        assert 0 <= prod <= 100

    def test_team_morale(self, team):
        morale = team_morale(team)
        assert 0 <= morale <= 100

    def test_total_monthly_labor_cost(self, active_employee):
        cost = total_monthly_labor_cost([active_employee])
        assert cost == pytest.approx(active_employee.monthly_total_cost)

    def test_terminated_excluded_from_labor_cost(self, active_employee):
        terminated = Employee(
            name="Old Worker",
            role=EmployeeRole.WORKER,
            annual_salary=50_000.0,
            status=EmployeeStatus.TERMINATED,
        )
        cost = total_monthly_labor_cost([active_employee, terminated])
        assert cost == pytest.approx(active_employee.monthly_total_cost)

    def test_team_quality_contribution(self, active_employee):
        quality = team_quality_contribution([active_employee])
        assert quality == pytest.approx(active_employee.skill_level)


class TestTurnover:
    def test_no_turnover_at_high_morale(self):
        emp = Employee(morale=100.0, status=EmployeeStatus.ACTIVE)
        results = [check_turnover(emp) for _ in range(1000)]
        assert not any(results)

    def test_turnover_possible_at_low_morale(self):
        emp = Employee(morale=10.0, status=EmployeeStatus.ACTIVE)
        results = [check_turnover(emp) for _ in range(2000)]
        assert any(results)

    def test_terminated_never_quits(self):
        emp = Employee(morale=0.0, status=EmployeeStatus.TERMINATED)
        results = [check_turnover(emp) for _ in range(100)]
        assert not any(results)


class TestHR:
    def test_terminate_employee(self, active_employee):
        severance = terminate_employee(active_employee)
        assert active_employee.status == EmployeeStatus.TERMINATED
        expected_severance = (40_000 / 52) * LAYOFF_COST_WEEKS
        assert severance == pytest.approx(expected_severance)

    def test_give_raise_increases_salary(self, active_employee):
        old_salary = active_employee.annual_salary
        give_raise(active_employee, 0.10)
        assert active_employee.annual_salary == pytest.approx(old_salary * 1.10)

    def test_give_raise_boosts_morale(self, active_employee):
        old_morale = active_employee.morale
        give_raise(active_employee, 0.05)
        assert active_employee.morale > old_morale

    def test_employee_summary_empty(self):
        summary = employee_summary([])
        assert summary["headcount"] == 0
        assert summary["avg_morale"] == 0.0

    def test_employee_summary_active(self, active_employee):
        summary = employee_summary([active_employee])
        assert summary["headcount"] == 1
        assert summary["avg_skill"] == pytest.approx(active_employee.skill_level)


class TestTraining:
    def test_apply_training_sets_status(self, active_employee):
        apply_training(active_employee, weeks=4)
        assert active_employee.status == EmployeeStatus.TRAINING
        assert active_employee.training_weeks_remaining == pytest.approx(4)

    def test_training_increases_skill_over_time(self, active_employee):
        apply_training(active_employee, weeks=4, skill_gain_per_week=5.0)
        initial_skill = active_employee.skill_level
        # Simulate 4 weeks of daily ticks (28 days)
        for _ in range(28):
            active_employee.daily_tick()
        assert active_employee.skill_level >= initial_skill

    def test_boost_morale_capped_at_100(self):
        emp = Employee(morale=95.0, status=EmployeeStatus.ACTIVE)
        boost_morale(emp, 20.0)
        assert emp.morale == pytest.approx(100.0)


class TestRecruitment:
    def test_generate_applicant_returns_employee(self):
        applicant = generate_applicant(EmployeeRole.WORKER, 40_000)
        assert isinstance(applicant, Employee)
        assert applicant.status == EmployeeStatus.APPLICANT
        assert 0 <= applicant.skill_level <= 100

    def test_post_job_creates_posting(self):
        posting = post_job("biz123", EmployeeRole.MANAGER, 80_000)
        assert posting.business_id == "biz123"
        assert posting.role == EmployeeRole.MANAGER
        assert posting.offered_salary == 80_000

    def test_make_offer_acceptance(self):
        """Test that make_offer can accept — run many trials."""
        applicant = generate_applicant(EmployeeRole.WORKER, 40_000)
        accepted = False
        for _ in range(50):
            emp = generate_applicant(EmployeeRole.WORKER, 40_000)
            if make_offer(emp, "biz123"):
                accepted = True
                assert emp.status == EmployeeStatus.ONBOARDING
                assert emp.business_id == "biz123"
                break
        assert accepted, "make_offer should accept at least once in 50 trials"
