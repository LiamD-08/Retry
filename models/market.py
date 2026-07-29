"""Data model for the business marketplace."""
from __future__ import annotations

from dataclasses import dataclass, field
from models.business import Business


@dataclass
class MarketListing:
    """A business available for acquisition on the marketplace."""

    business: Business
    days_on_market: int = 0
    negotiable: bool = True
    notes: str = ""

    def age_listing(self) -> None:
        self.days_on_market += 1

    @property
    def urgency(self) -> str:
        if self.days_on_market >= 60:
            return "desperate"
        if self.days_on_market >= 30:
            return "motivated"
        return "standard"


@dataclass
class Marketplace:
    """Holds the current set of available business listings."""

    listings: list[MarketListing] = field(default_factory=list)

    def add_listing(self, business: Business, notes: str = "") -> MarketListing:
        listing = MarketListing(business=business, notes=notes)
        self.listings.append(listing)
        return listing

    def remove_listing(self, business_id: str) -> None:
        self.listings = [l for l in self.listings if l.business.id != business_id]

    def get_listing(self, business_id: str) -> MarketListing | None:
        for listing in self.listings:
            if listing.business.id == business_id:
                return listing
        return None

    def daily_tick(self) -> None:
        for listing in self.listings:
            listing.age_listing()

    def count(self) -> int:
        return len(self.listings)
