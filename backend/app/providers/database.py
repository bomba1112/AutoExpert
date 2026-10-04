from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.catalog import VehicleVariant
from app.models.enums import SourceUsageStatus
from app.models.evidence import (
    KnownIssue,
    LocalCostItem,
    MarketListing,
    OwnerEvidence,
    SourceRecord,
    TechnicalEvidence,
)


class DatabaseTechnicalDataProvider:
    def __init__(self, session: Session):
        self.session = session

    def evidence_for(self, variant_id: str, market: str) -> list[TechnicalEvidence]:
        statement = (
            select(TechnicalEvidence)
            .join(SourceRecord, TechnicalEvidence.source_id == SourceRecord.id)
            .where(
                TechnicalEvidence.vehicle_variant_id == variant_id,
                or_(TechnicalEvidence.market.is_(None), TechnicalEvidence.market == market),
                SourceRecord.usage_status == SourceUsageStatus.ACTIVE,
            )
        )
        variant = self.session.get(VehicleVariant, variant_id)
        return [
            row
            for row in self.session.scalars(statement)
            if not row.conditions.get("revision_id")
            or (variant and row.conditions["revision_id"] == variant.published_revision_id)
        ]

    def issues_for(self, variant_id: str) -> list[KnownIssue]:
        return list(
            self.session.scalars(
                select(KnownIssue).where(
                    KnownIssue.vehicle_variant_id == variant_id,
                    # f093: CN owner-review issues carry no severity and stay out of
                    # the analysis reports.
                    KnownIssue.severity.is_not(None),
                )
            )
        )


class DatabaseMarketDataProvider:
    def __init__(self, session: Session):
        self.session = session

    def listings_for(self, *, country: str, make: str, model: str) -> list[MarketListing]:
        statement = (
            select(MarketListing)
            .join(SourceRecord, MarketListing.source_id == SourceRecord.id)
            .where(
                MarketListing.country == country,
                MarketListing.make.ilike(make),
                MarketListing.model.ilike(model),
                SourceRecord.usage_status == SourceUsageStatus.ACTIVE,
            )
        )
        return list(self.session.scalars(statement))


class DatabaseLocalCostProvider:
    def __init__(self, session: Session):
        self.session = session

    def costs_for(self, *, country: str, city: str | None, variant_id: str) -> list[LocalCostItem]:
        statement = (
            select(LocalCostItem)
            .join(SourceRecord, LocalCostItem.source_id == SourceRecord.id)
            .where(
                LocalCostItem.country == country,
                or_(LocalCostItem.city.is_(None), LocalCostItem.city == city),
                or_(
                    LocalCostItem.vehicle_variant_id.is_(None),
                    LocalCostItem.vehicle_variant_id == variant_id,
                ),
                SourceRecord.usage_status == SourceUsageStatus.ACTIVE,
            )
        )
        return list(self.session.scalars(statement))


class DatabaseOwnerReviewProvider:
    def __init__(self, session: Session):
        self.session = session

    def observations_for(self, variant_id: str) -> list[OwnerEvidence]:
        statement = (
            select(OwnerEvidence)
            .join(SourceRecord, OwnerEvidence.source_id == SourceRecord.id)
            .where(
                OwnerEvidence.vehicle_variant_id == variant_id,
                SourceRecord.usage_status == SourceUsageStatus.ACTIVE,
            )
        )
        return list(self.session.scalars(statement))
