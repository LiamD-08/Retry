# Tunable game balance constants
# Adjust these values to fine-tune gameplay difficulty and pacing.

# --- Player Starting State ---
INITIAL_CAPITAL = 500_000          # Starting cash ($)
MAX_OWNED_BUSINESSES = 10          # Portfolio cap

# --- Marketplace ---
MARKET_BUSINESS_COUNT_MIN = 3      # Min new businesses offered per refresh
MARKET_BUSINESS_COUNT_MAX = 5      # Max new businesses offered per refresh
MARKET_REFRESH_DAYS = 30           # How often marketplace refreshes (days)

# --- Acquisition ---
# Rent/Lease: annual lease cost as fraction of asset value
RENT_MARKUP_MIN = 0.08             # 8% of purchase price per year
RENT_MARKUP_MAX = 0.12             # 12% of purchase price per year

# --- Valuation & Exit ---
# EBITDA multiples used when selling a business (sector → multiple range)
SECTOR_EBITDA_MULTIPLES = {
    "restaurant":       (3.0, 5.0),
    "retail":           (4.0, 6.0),
    "manufacturing":    (4.0, 7.0),
    "services":         (5.0, 8.0),
    "technology":       (6.0, 10.0),
    "healthcare":       (5.0, 9.0),
    "logistics":        (4.0, 6.0),
    "hospitality":      (3.0, 5.5),
}
DEFAULT_EBITDA_MULTIPLE = (4.0, 6.0)

# Transaction costs when selling (fraction of sale price)
SELL_TRANSACTION_COST_RATE = 0.03  # 3% broker / legal fees
SELL_CAPITAL_GAINS_TAX_RATE = 0.20 # 20% capital gains tax on profit

# --- Employee System ---
EMPLOYEE_SALARY_RANGES = {         # Annual salary ranges by role ($)
    "manager":          (60_000, 150_000),
    "supervisor":       (45_000, 80_000),
    "skilled_worker":   (40_000, 70_000),
    "worker":           (30_000, 50_000),
    "intern":           (25_000, 35_000),
}
DEFAULT_SALARY_RANGE = (35_000, 65_000)

BENEFITS_COST_RATE = 0.18          # Benefits as fraction of salary (18%)
HIRING_SUCCESS_RATE_MIN = 0.60     # Min probability offer is accepted
HIRING_SUCCESS_RATE_MAX = 0.80     # Max probability offer is accepted
TRAINING_PAYOFF_WEEKS_MIN = 4      # Weeks before training shows results
TRAINING_PAYOFF_WEEKS_MAX = 8

ONBOARDING_RAMP_WEEKS = 4          # Weeks for a new hire to reach full productivity
LAYOFF_COST_WEEKS = 4              # Weeks of salary paid as severance
MORALE_DECAY_RATE = 0.02           # Per-day morale loss if no actions taken (fraction)
TURNOVER_MORALE_THRESHOLD = 30     # Morale below this triggers voluntary turnover risk
TURNOVER_DAILY_PROBABILITY = 0.005 # Daily quit probability when morale is low

# --- Business Operations ---
UNCERTAINTY_FACTOR = 0.08          # ±8% random noise on KPI calculations
SEASONAL_AMPLITUDE = 0.15          # ±15% seasonal revenue swing

# Condition thresholds (0–100 scale)
CONDITION_CRITICAL = 20
CONDITION_POOR = 40
CONDITION_FAIR = 60
CONDITION_GOOD = 80

# Maintenance cost as fraction of asset value per year
MAINTENANCE_RATE_GOOD = 0.02
MAINTENANCE_RATE_FAIR = 0.04
MAINTENANCE_RATE_POOR = 0.07
MAINTENANCE_RATE_CRITICAL = 0.12

# Debt
DEBT_INTEREST_RATE_MIN = 0.05      # Annual interest (5%)
DEBT_INTEREST_RATE_MAX = 0.15      # Annual interest (15%)
DEBT_RESTRUCTURE_COST_RATE = 0.02  # 2% of outstanding debt as restructuring fee

# --- Time ---
DAYS_PER_MONTH = 30
DAYS_PER_YEAR = 360
TICKS_PER_DAY = 1                  # One simulation tick = one game day

# --- Random Events ---
RANDOM_EVENT_DAILY_PROBABILITY = 0.02  # 2% chance of a random event per day per business
EVENT_CHAOS_SCALE_PER_BUSINESS = 0.01  # Chaos multiplier grows with portfolio size
