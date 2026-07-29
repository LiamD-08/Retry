"""Game clock: tracks in-game date and provides calendar helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from config.balancing import DAYS_PER_MONTH, DAYS_PER_YEAR


MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Seasonal demand multiplier per month (index 0 = January).
# Values >1 = peak, <1 = trough. Averaged across all sectors;
# sector-specific modifiers are applied on top in archetypes.
SEASONAL_BASELINE = [
    0.90, 0.88, 0.95, 1.00, 1.05, 1.08,
    1.10, 1.08, 1.02, 0.97, 0.95, 1.12,
]


@dataclass
class GameClock:
    """Tracks the passage of in-game time (day → month → year)."""

    day: int = 1          # Day of current month (1–30)
    month: int = 1        # Month of current year (1–12)
    year: int = 1         # Game year (starts at 1)
    total_days: int = 0   # Total days elapsed since game start

    # Callbacks registered by other systems (called each tick)
    _daily_callbacks: list = field(default_factory=list, repr=False)
    _monthly_callbacks: list = field(default_factory=list, repr=False)

    def register_daily(self, callback) -> None:
        self._daily_callbacks.append(callback)

    def register_monthly(self, callback) -> None:
        self._monthly_callbacks.append(callback)

    def tick(self) -> dict:
        """Advance one day. Returns a dict describing what happened."""
        self.total_days += 1
        self.day += 1

        events = {"new_day": True, "new_month": False, "new_year": False}

        if self.day > DAYS_PER_MONTH:
            self.day = 1
            self.month += 1
            events["new_month"] = True

            for cb in self._monthly_callbacks:
                cb(self)

            if self.month > 12:
                self.month = 1
                self.year += 1
                events["new_year"] = True

        for cb in self._daily_callbacks:
            cb(self)

        return events

    def advance_days(self, n: int) -> list[dict]:
        """Advance *n* days and return a list of tick event dicts."""
        return [self.tick() for _ in range(n)]

    @property
    def month_name(self) -> str:
        return MONTH_NAMES[self.month - 1]

    @property
    def date_string(self) -> str:
        return f"Year {self.year}, {self.month_name} {self.day}"

    @property
    def seasonal_multiplier(self) -> float:
        """Baseline seasonal demand multiplier for the current month."""
        return SEASONAL_BASELINE[self.month - 1]

    def months_elapsed(self) -> int:
        """Total complete months since game start."""
        return (self.year - 1) * 12 + (self.month - 1)
