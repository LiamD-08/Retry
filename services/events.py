"""Game event system: random events that affect businesses."""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class EventSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


@dataclass
class GameEvent:
    title: str
    description: str
    severity: EventSeverity
    business_id: str
    effects: dict          # Keys: "revenue_pct", "condition", "satisfaction", "morale", "cost"

    def apply(self, business, employees: list | None = None) -> list[str]:
        """Apply effects to business (and optionally employees). Returns log lines."""
        log = [f"[EVENT] {self.title} — {self.description}"]

        if "revenue_pct" in self.effects:
            delta = business.financials.monthly_revenue * self.effects["revenue_pct"]
            business.financials.monthly_revenue = max(0.0, business.financials.monthly_revenue + delta)
            log.append(f"  Revenue change: {delta:+,.0f}")

        if "condition" in self.effects:
            business.condition = max(0.0, min(100.0, business.condition + self.effects["condition"]))
            log.append(f"  Condition change: {self.effects['condition']:+.1f}")

        if "satisfaction" in self.effects:
            business.kpis.customer_satisfaction = max(
                0.0, min(100.0, business.kpis.customer_satisfaction + self.effects["satisfaction"])
            )
            log.append(f"  Satisfaction change: {self.effects['satisfaction']:+.1f}")

        if "morale" in self.effects and employees:
            for emp in employees:
                emp.morale = max(0.0, min(100.0, emp.morale + self.effects["morale"]))
            log.append(f"  Employee morale change: {self.effects['morale']:+.1f}")

        return log


# ---------------------------------------------------------------------------
# Event templates
# ---------------------------------------------------------------------------

_EVENT_TEMPLATES = [
    # Minor positive
    {
        "title": "Local Press Feature",
        "description": "A local newspaper wrote a positive piece about the business.",
        "severity": EventSeverity.MINOR,
        "effects": {"satisfaction": 5.0, "revenue_pct": 0.05},
    },
    {
        "title": "Employee Recognition",
        "description": "A long-serving employee received public recognition.",
        "severity": EventSeverity.MINOR,
        "effects": {"morale": 8.0},
    },
    # Minor negative
    {
        "title": "Minor Equipment Fault",
        "description": "A minor equipment fault requires routine repair.",
        "severity": EventSeverity.MINOR,
        "effects": {"condition": -3.0, "cost": 500.0},
    },
    {
        "title": "Poor Online Review",
        "description": "A customer left a scathing online review.",
        "severity": EventSeverity.MINOR,
        "effects": {"satisfaction": -4.0},
    },
    # Moderate negative
    {
        "title": "Key Employee Departure",
        "description": "A key team member resigned unexpectedly.",
        "severity": EventSeverity.MODERATE,
        "effects": {"morale": -12.0, "revenue_pct": -0.05},
    },
    {
        "title": "Supply Chain Disruption",
        "description": "A supplier raised prices or caused a shortage.",
        "severity": EventSeverity.MODERATE,
        "effects": {"revenue_pct": -0.08, "satisfaction": -5.0},
    },
    {
        "title": "Equipment Breakdown",
        "description": "Key equipment broke down and needs repair.",
        "severity": EventSeverity.MODERATE,
        "effects": {"condition": -8.0, "revenue_pct": -0.10},
    },
    # Major negative
    {
        "title": "Health & Safety Violation",
        "description": "A regulatory inspection found a serious violation.",
        "severity": EventSeverity.MAJOR,
        "effects": {"satisfaction": -15.0, "revenue_pct": -0.20, "condition": -5.0},
    },
    {
        "title": "Competitor Opens Nearby",
        "description": "A well-funded competitor opened near your location.",
        "severity": EventSeverity.MAJOR,
        "effects": {"revenue_pct": -0.12, "satisfaction": -8.0},
    },
]


def roll_event(
    business_id: str,
    portfolio_size: int = 1,
) -> GameEvent | None:
    """
    Roll to see if a random event fires for a business this day.
    Returns a GameEvent or None.
    """
    from config.balancing import RANDOM_EVENT_DAILY_PROBABILITY, EVENT_CHAOS_SCALE_PER_BUSINESS
    base_prob = RANDOM_EVENT_DAILY_PROBABILITY
    chaos = base_prob + EVENT_CHAOS_SCALE_PER_BUSINESS * (portfolio_size - 1)
    if random.random() > chaos:
        return None

    template = random.choice(_EVENT_TEMPLATES)
    return GameEvent(
        title=template["title"],
        description=template["description"],
        severity=template["severity"],
        business_id=business_id,
        effects=dict(template["effects"]),
    )
