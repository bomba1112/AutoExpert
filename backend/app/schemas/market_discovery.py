"""Minimal permitted market observations; seller fields never become technical facts."""

from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class DiscoveryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ListingMarketClaim(DiscoveryModel):
    listing_id: str = Field(min_length=1, max_length=100)
    source_url: str = Field(min_length=8, max_length=2000)
    market_raw: str | None = Field(default=None, max_length=100)
    sales_channel_raw: str | None = Field(default=None, max_length=100)
    active: bool
    order_only: bool = False
    model_year: int | None = Field(default=None, ge=1886, le=2100)
    # Only a checksum is exported. Exact identifiers stay in the existing private VIN workflow.
    identifier_reference: str | None = Field(default=None, max_length=100)


class MarketCount(DiscoveryModel):
    market_raw: str | None = Field(default=None, max_length=100)
    count: int = Field(ge=0, le=10000000)
    source_url: str = Field(min_length=8, max_length=2000)
    locator: str = Field(min_length=1, max_length=500)


class MarketDiscoveryRecord(DiscoveryModel):
    external_key: str = Field(min_length=1, max_length=160)
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    observed_at: AwareDatetime
    source_url: str = Field(min_length=8, max_length=2000)
    locator: str = Field(min_length=1, max_length=500)
    listing_count: int | None = Field(default=None, ge=0, le=10000000)
    count_method: Literal["FILTER_TOTAL", "COMPLETE_EXPORT", "UNKNOWN"] = "UNKNOWN"
    inventory_scope: Literal["ACTIVE_LOCAL", "MIXED_LOCAL_AND_ORDER", "UNKNOWN"] = "UNKNOWN"
    distribution_scope: Literal["COMPLETE", "SAMPLE", "NOT_OBSERVED"] = "NOT_OBSERVED"
    listings: list[ListingMarketClaim] = Field(default_factory=list, max_length=10000)
    market_counts: list[MarketCount] = Field(default_factory=list, max_length=100)
    selection_method: str = Field(min_length=10, max_length=1000)
    limitations: dict[Literal["az", "ru"], str]

    @model_validator(mode="after")
    def coherent_observation(self):
        if self.observed_at > datetime.now(UTC):
            raise ValueError("FUTURE_MARKET_DISCOVERY")
        if (self.listing_count is None) != (self.count_method == "UNKNOWN"):
            raise ValueError("COUNT_METHOD_REQUIRED")
        if self.listings and self.market_counts:
            raise ValueError("DO_NOT_MIX_SAMPLE_AND_AGGREGATES")
        if set(self.limitations) != {"az", "ru"}:
            raise ValueError("AZ_RU_LIMITATIONS_REQUIRED")
        ids = {}
        for row in self.listings:
            value = row.model_dump(mode="json")
            if row.listing_id in ids and ids[row.listing_id] != value:
                raise ValueError("DUPLICATE_LISTING_CONFLICT")
            ids[row.listing_id] = value
        # Repeated promotions count once. Sold and order-only ads are not local stock.
        self.listings = [ListingMarketClaim(**v) for v in ids.values()]
        active = sum(r.active and not r.order_only for r in self.listings)
        if (
            self.inventory_scope == "ACTIVE_LOCAL"
            and self.listing_count is not None
            and active > self.listing_count
        ):
            raise ValueError("SAMPLE_EXCEEDS_TOTAL")
        if self.distribution_scope == "COMPLETE":
            if self.inventory_scope != "ACTIVE_LOCAL" or self.listing_count is None:
                raise ValueError("COMPLETE_DISTRIBUTION_REQUIRES_LOCAL_TOTAL")
            total = sum(r.count for r in self.market_counts) if self.market_counts else active
            if total != self.listing_count:
                raise ValueError("DISTRIBUTION_TOTAL_MISMATCH")
        if self.distribution_scope == "NOT_OBSERVED" and (self.listings or self.market_counts):
            raise ValueError("DISTRIBUTION_SCOPE_REQUIRED")
        if self.market_counts and self.distribution_scope != "COMPLETE":
            raise ValueError("FILTER_COUNTS_REQUIRE_COMPLETE_NON_OVERLAPPING_PARTITION")
        raw = [r.market_raw for r in self.market_counts]
        if len(set(raw)) != len(raw):
            raise ValueError("DUPLICATE_MARKET_BUCKET")
        for url in [
            self.source_url,
            *[r.source_url for r in self.listings],
            *[r.source_url for r in self.market_counts],
        ]:
            p = urlsplit(url)
            if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment:
                raise ValueError("PUBLIC_HTTPS_LOCATOR_REQUIRED")
        return self
