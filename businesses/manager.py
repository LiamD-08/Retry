"""Business lifecycle management: acquisition, operations, and exit."""
from __future__ import annotations

from config.balancing import (
    RENT_MARKUP_MIN, RENT_MARKUP_MAX, DAYS_PER_MONTH,
)
from economy.finance import (
    update_business_financials, update_kpis, compute_sale_proceeds,
)
from employees.hr import daily_hr_tick, monthly_hr_tick, employee_summary
from employees.performance import (
    team_productivity, team_quality_contribution, total_monthly_labor_cost,
    apply_productivity_to_capacity,
)
from models.business import Business, AcquisitionType, BusinessStatus
from models.employee import Employee
from models.financial import Ledger, Transaction, TransactionType
from services.events import roll_event


class BusinessManager:
    """Manages all owned businesses for the player."""

    def __init__(self, ledger: Ledger, clock) -> None:
        self._ledger = ledger
        self._clock = clock
        self._businesses: dict[str, Business] = {}
        self._employees: dict[str, Employee] = {}  # global employee registry
        self._event_log: list[str] = []

    # ------------------------------------------------------------------
    # Acquisition
    # ------------------------------------------------------------------

    def acquire_rent(self, business: Business) -> bool:
        """
        Acquire business via rent/lease.
        Deducts first month's lease payment from player cash.
        Returns False if insufficient funds.
        """
        cost = business.monthly_lease
        if self._ledger.balance() < cost:
            return False

        business.status = BusinessStatus.OWNED
        business.acquisition_type = AcquisitionType.RENT
        business.acquisition_cost_paid = cost
        business._employee_ids = []

        self._ledger.record(Transaction(
            amount=-cost,
            type=TransactionType.ACQUISITION,
            description=f"First lease payment: {business.name}",
            business_id=business.id,
            day=self._clock.day,
            month=self._clock.month,
            year=self._clock.year,
        ))
        self._businesses[business.id] = business
        return True

    def acquire_buyout(self, business: Business) -> bool:
        """
        Acquire business via full buyout.
        Deducts asking price from player cash.
        """
        cost = business.asking_price
        if self._ledger.balance() < cost:
            return False

        business.status = BusinessStatus.OWNED
        business.acquisition_type = AcquisitionType.BUYOUT
        business.acquisition_cost_paid = cost
        business._employee_ids = []

        self._ledger.record(Transaction(
            amount=-cost,
            type=TransactionType.ACQUISITION,
            description=f"Buyout: {business.name}",
            business_id=business.id,
            day=self._clock.day,
            month=self._clock.month,
            year=self._clock.year,
        ))
        self._businesses[business.id] = business
        return True

    # ------------------------------------------------------------------
    # Daily / Monthly ticks
    # ------------------------------------------------------------------

    def daily_tick(self) -> list[str]:
        """Process all businesses for one day. Returns event log lines."""
        log: list[str] = []
        portfolio_size = len(self._businesses)

        for biz in list(self._businesses.values()):
            if biz.status != BusinessStatus.OWNED:
                continue

            biz.days_owned += 1

            # HR daily tick
            employees = self._get_employees(biz.id)
            hr_events = daily_hr_tick(employees)
            for event_type, emp in hr_events:
                if event_type == "quit":
                    biz._employee_ids.remove(emp.id)
                    log.append(f"{biz.name}: {emp.name} ({emp.role.value}) quit.")

            # Random events
            event = roll_event(biz.id, portfolio_size)
            if event:
                event_log = event.apply(biz, employees)
                log.extend(event_log)

            # Collect lease payment at month start (day 1)
            if self._clock.day == 1 and biz.acquisition_type == AcquisitionType.RENT:
                self._ledger.record(Transaction(
                    amount=-biz.monthly_lease,
                    type=TransactionType.LEASE_PAYMENT,
                    description=f"Monthly lease: {biz.name}",
                    business_id=biz.id,
                    day=self._clock.day,
                    month=self._clock.month,
                    year=self._clock.year,
                ))

        return log

    def monthly_tick(self) -> list[str]:
        """
        Process all businesses at month-end: P&L update, KPI refresh,
        record revenue and expenses in ledger.
        Returns event log lines.
        """
        log: list[str] = []

        for biz in list(self._businesses.values()):
            if biz.status != BusinessStatus.OWNED:
                continue

            employees = self._get_employees(biz.id)

            # HR monthly
            hr_log = monthly_hr_tick(employees)
            log.extend(hr_log)

            # Update labor cost from actual employees
            labor_cost = total_monthly_labor_cost(employees)
            productivity = team_productivity(employees)

            # Update KPIs from productivity influence
            biz.kpis.utilization = apply_productivity_to_capacity(
                biz.kpis.utilization, productivity
            )

            # Collect actions for KPI update
            actions = [a["type"] for a in biz.pending_actions]
            self._resolve_actions(biz, employees)

            # Update P&L
            update_business_financials(
                biz,
                seasonal_multiplier=self._clock.seasonal_multiplier,
                employee_total_cost=labor_cost if employees else None,
            )
            update_kpis(biz, actions)

            # Save monthly snapshot
            biz.monthly_history.append(biz.snapshot())

            # Record net cashflow in ledger
            cashflow = biz.financials.cashflow
            self._ledger.record(Transaction(
                amount=cashflow,
                type=TransactionType.REVENUE if cashflow > 0 else TransactionType.OVERHEAD,
                description=f"Monthly P&L: {biz.name}",
                business_id=biz.id,
                day=self._clock.day,
                month=self._clock.month,
                year=self._clock.year,
            ))

            profitable = biz.financials.net_income >= 0
            status_str = "✓ Profitable" if profitable else "✗ Loss"
            log.append(
                f"{biz.name}: Revenue ${biz.financials.monthly_revenue:,.0f} | "
                f"Net Income ${biz.financials.net_income:+,.0f} ({status_str})"
            )

        return log

    # ------------------------------------------------------------------
    # Turnaround actions
    # ------------------------------------------------------------------

    def queue_action(self, business_id: str, action_type: str, params: dict | None = None) -> bool:
        """Queue a turnaround action to be resolved at month-end."""
        biz = self._businesses.get(business_id)
        if biz is None:
            return False
        biz.pending_actions.append({"type": action_type, "params": params or {}})
        return True

    def _resolve_actions(self, biz: Business, employees: list[Employee]) -> None:
        """Apply queued actions and clear the queue."""
        for action in biz.pending_actions:
            action_type = action["type"]
            params = action["params"]

            if action_type == "maintenance_upgrade":
                cost = params.get("spend", biz.asset_value * 0.05)
                self._ledger.record(Transaction(
                    amount=-cost,
                    type=TransactionType.MAINTENANCE,
                    description=f"Maintenance upgrade: {biz.name}",
                    business_id=biz.id,
                    day=self._clock.day,
                    month=self._clock.month,
                    year=self._clock.year,
                ))

            elif action_type == "marketing":
                cost = params.get("spend", biz.financials.monthly_revenue * 0.05)
                self._ledger.record(Transaction(
                    amount=-cost,
                    type=TransactionType.MARKETING,
                    description=f"Marketing spend: {biz.name}",
                    business_id=biz.id,
                    day=self._clock.day,
                    month=self._clock.month,
                    year=self._clock.year,
                ))

            elif action_type == "training":
                cost = params.get("spend", 500.0) * len(employees)
                self._ledger.record(Transaction(
                    amount=-cost,
                    type=TransactionType.TRAINING,
                    description=f"Staff training: {biz.name}",
                    business_id=biz.id,
                    day=self._clock.day,
                    month=self._clock.month,
                    year=self._clock.year,
                ))
                for emp in employees:
                    from employees.performance import apply_training
                    apply_training(emp, weeks=params.get("weeks", 4))

            elif action_type == "debt_restructure":
                from economy.debt import restructure_debt
                biz.debt, biz.debt_interest_rate, fee = restructure_debt(
                    biz.debt, biz.debt_interest_rate
                )
                self._ledger.record(Transaction(
                    amount=-fee,
                    type=TransactionType.DEBT_SERVICE,
                    description=f"Debt restructuring fee: {biz.name}",
                    business_id=biz.id,
                    day=self._clock.day,
                    month=self._clock.month,
                    year=self._clock.year,
                ))

            elif action_type == "pay_down_debt":
                amount = min(params.get("amount", 10_000.0), biz.debt)
                biz.debt -= amount
                self._ledger.record(Transaction(
                    amount=-amount,
                    type=TransactionType.DEBT_SERVICE,
                    description=f"Debt paydown: {biz.name}",
                    business_id=biz.id,
                    day=self._clock.day,
                    month=self._clock.month,
                    year=self._clock.year,
                ))

        biz.pending_actions.clear()

    # ------------------------------------------------------------------
    # Exit
    # ------------------------------------------------------------------

    def sell_business(self, business_id: str) -> dict | None:
        """
        Sell a business. Records proceeds in ledger.
        Returns sale details dict or None if business not found.
        """
        biz = self._businesses.get(business_id)
        if biz is None or biz.status != BusinessStatus.OWNED:
            return None

        result = compute_sale_proceeds(biz, biz.acquisition_cost_paid)
        net = result["net_proceeds"]

        self._ledger.record(Transaction(
            amount=net,
            type=TransactionType.SALE_PROCEEDS,
            description=f"Sale proceeds: {biz.name}",
            business_id=biz.id,
            day=self._clock.day,
            month=self._clock.month,
            year=self._clock.year,
        ))
        self._ledger.record(Transaction(
            amount=-(result["broker_fee"] + result["tax"]),
            type=TransactionType.SALE_COSTS,
            description=f"Sale costs (fees+tax): {biz.name}",
            business_id=biz.id,
            day=self._clock.day,
            month=self._clock.month,
            year=self._clock.year,
        ))

        biz.status = BusinessStatus.SOLD

        # Terminate employees
        employees = self._get_employees(biz.id)
        for emp in employees:
            emp.status = __import__("models.employee", fromlist=["EmployeeStatus"]).EmployeeStatus.TERMINATED

        del self._businesses[business_id]
        return result

    # ------------------------------------------------------------------
    # Employee management
    # ------------------------------------------------------------------

    def hire_employee(self, business_id: str, employee: Employee) -> bool:
        """Add an employee to a business roster."""
        biz = self._businesses.get(business_id)
        if biz is None:
            return False
        employee.business_id = business_id
        self._employees[employee.id] = employee
        biz._employee_ids.append(employee.id)
        return True

    def fire_employee(self, business_id: str, employee_id: str) -> float:
        """Lay off an employee. Returns severance cost."""
        from employees.hr import terminate_employee
        emp = self._employees.get(employee_id)
        if emp is None:
            return 0.0
        severance = terminate_employee(emp)
        biz = self._businesses.get(business_id)
        if biz and employee_id in biz._employee_ids:
            biz._employee_ids.remove(employee_id)
        self._ledger.record(Transaction(
            amount=-severance,
            type=TransactionType.SEVERANCE,
            description=f"Severance: {emp.name}",
            business_id=business_id,
            day=self._clock.day,
            month=self._clock.month,
            year=self._clock.year,
        ))
        return severance

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_employees(self, business_id: str) -> list[Employee]:
        biz = self._businesses.get(business_id)
        if biz is None:
            return []
        return [self._employees[eid] for eid in biz._employee_ids if eid in self._employees]

    def get_business(self, business_id: str) -> Business | None:
        return self._businesses.get(business_id)

    def all_businesses(self) -> list[Business]:
        return list(self._businesses.values())

    def portfolio_cashflow(self) -> float:
        """Sum of monthly cashflow across all owned businesses."""
        return sum(b.financials.cashflow for b in self._businesses.values())
