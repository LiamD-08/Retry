# Architecture Overview

This document describes the system design and data flows for the Business Turnaround Simulation Game.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        game.py                          │
│              (CLI entry point / UI loop)                │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               core/simulation.py (Simulation)           │
│  Owns: GameClock, Player, Marketplace, BusinessManager  │
└──┬──────────────────┬─────────────────┬─────────────────┘
   │                  │                 │
   ▼                  ▼                 ▼
GameClock         Player            BusinessManager
(core/clock.py)  (services/player)  (businesses/manager)
   │                  │                 │
   │ callbacks         │ Ledger          │ owns businesses
   ▼                  ▼                 ▼
Daily/Monthly    models/financial   models/business
ticks            (Ledger, Txns)     models/employee
```

## Module Responsibilities

### `core/`
| File | Responsibility |
|------|---------------|
| `clock.py` | In-game calendar. Tracks day/month/year. Fires daily/monthly callbacks. Provides `seasonal_multiplier`. |
| `simulation.py` | Central coordinator. Owns all top-level state. Exposes a simple API to the UI (tick, acquire, sell, queue_action). |

### `models/`
Pure data models with minimal logic. No cross-module imports.

| File | Responsibility |
|------|---------------|
| `business.py` | `Business` entity with `BusinessFinancials` and `BusinessKPIs`. All P&L properties computed as `@property`. |
| `employee.py` | `Employee` entity with `daily_tick()` for per-day state updates (morale decay, onboarding ramp, training progress). |
| `market.py` | `Marketplace` container and `MarketListing` wrapper. |
| `financial.py` | `Transaction` record and `Ledger` (running balance + monthly aggregates). |

### `economy/`
Financial calculation logic (no persistent state).

| File | Responsibility |
|------|---------------|
| `finance.py` | `update_business_financials()` — monthly P&L recalculation. `update_kpis()` — KPI drift and turnaround effects. `compute_valuation()`, `compute_sale_proceeds()`. |
| `pricing.py` | Price elasticity, marketing revenue lift, noise injection, effective revenue formula. |
| `debt.py` | Interest calculations, amortisation, restructuring fee. |

### `businesses/`

| File | Responsibility |
|------|---------------|
| `archetypes.py` | `BusinessArchetype` definitions for each sector (8 sectors). Provides revenue/cost ratios, seasonal profiles. |
| `marketplace.py` | `generate_business()` — creates a randomised failing business. `refresh_marketplace()` — populates marketplace with fresh listings. |
| `manager.py` | `BusinessManager` — acquisition (rent/buyout), daily/monthly tick orchestration, turnaround action queue, employee management, exit (sell). |

### `employees/`

| File | Responsibility |
|------|---------------|
| `performance.py` | Aggregate metrics: `team_productivity()`, `team_morale()`, `total_monthly_labor_cost()`. Turnover check. Training application. |
| `hr.py` | `daily_hr_tick()`, `monthly_hr_tick()`, termination (severance), raises, benefits update. |
| `recruiter.py` | `JobPosting`, `generate_applicant()`, `make_offer()`, `post_job()`. |

### `services/`

| File | Responsibility |
|------|---------------|
| `player.py` | `Player` — cash (via Ledger), portfolio tracking, net worth estimate. |
| `events.py` | `GameEvent` templates, `roll_event()` — probabilistic daily random events. |

### `ui/`
Presentation only. No game state mutation.

| File | Responsibility |
|------|---------------|
| `dashboard.py` | Portfolio overview, marketplace listing view. |
| `business_view.py` | Full business detail (P&L + KPIs + staff). |
| `employee_view.py` | Staff table, job postings. |
| `reports.py` | P&L report, KPI report, ledger summary. Utility `format_currency()`. |

### `config/`
| File | Responsibility |
|------|---------------|
| `balancing.py` | All tunable constants (capital, multiples, rates, thresholds). |

### `data/`
| File | Responsibility |
|------|---------------|
| `seeds.py` | Pre-built sample businesses for testing. |
| `business_names.json` | Name fragments used by the name generator. |

---

## Core Data Flows

### 1. Acquisition Flow
```
Player selects listing → Simulation.acquire_business(id, mode)
  → BusinessManager.acquire_rent() / acquire_buyout()
    → Ledger records debit (Transaction)
    → Business.status = OWNED
    → Player.add_to_portfolio(id)
  → Marketplace removes listing
```

### 2. Monthly Tick Flow
```
Simulation.advance_month()
  → GameClock.advance_days(30)
    → Each day: daily_callback → BusinessManager.daily_tick()
        → Employee.daily_tick() (morale decay, ramp, training)
        → HR turnover checks (daily_hr_tick)
        → Random event roll (roll_event)
        → Lease payment on day 1 (Ledger debit)
    → Last day: monthly_callback → BusinessManager.monthly_tick()
        → monthly_hr_tick (tenure milestones)
        → Resolve queued turnaround actions
        → update_business_financials() → new revenue/costs
        → update_kpis() → KPI drift
        → business.monthly_history.append(snapshot)
        → Ledger records net cashflow
```

### 3. Exit Flow
```
Simulation.sell_business(id)
  → BusinessManager.sell_business(id)
    → compute_sale_proceeds(business, acquisition_cost)
      → compute_valuation() → EBITDA × multiple + assets − debt
      → apply broker fee (3%) and capital gains tax (20%)
    → Ledger records net proceeds + costs
    → Business.status = SOLD, employees terminated
    → Player.remove_from_portfolio(id)
```

---

## Key Design Decisions

1. **Separation of models and logic**: `models/` contains pure data; `economy/` and `employees/` contain calculation logic. This makes testing easier and prevents circular imports.

2. **Ledger as single source of truth**: All cash movements go through `models/financial.Ledger`. Player cash = `ledger.balance()`.

3. **Action queue**: Turnaround actions are queued during the month and resolved atomically at month-end, preventing mid-month inconsistencies.

4. **KPI drift model**: KPIs move toward targets gradually each month (`_nudge()`), reflecting that real business improvements take time.

5. **Uncertainty injection**: All KPI and revenue calculations include `±UNCERTAINTY_FACTOR` noise to prevent perfect-play strategies.

6. **Clock callbacks**: `GameClock` uses registered callbacks so each system can react to time passing without tight coupling.
