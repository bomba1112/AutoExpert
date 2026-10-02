from __future__ import annotations

import pytest
from app.models.enums import ConfidenceLevel, EvidenceStatus, FitRating
from app.schemas.analysis import (
    EvidenceBundle,
    GeneratedReport,
    GeneratedSection,
    GroundedClaim,
    VehicleSnapshot,
)
from app.schemas.common import EvidenceItem, MoneyRange
from app.schemas.fit import FitAnalysis, UsageProfileInput
from app.schemas.market import MarketAnalysis
from app.schemas.ownership import OwnershipCostResult
from app.schemas.reviews import OwnerFeedbackAggregation
from app.services.evidence_validation import UngroundedReportError, validate_generated_report
from pydantic import ValidationError


def _bundle() -> EvidenceBundle:
    return EvidenceBundle(
        vehicle=VehicleSnapshot(
            variant_id="variant",
            make="Demo",
            model="Demo",
            generation="D1",
            variant="V1",
            market="AZ",
            year=2022,
            is_demo=True,
        ),
        user_profile=UsageProfileInput(monthly_mileage_km=1000, city_share=0.5),
        technical_evidence=[
            EvidenceItem(
                id="estimate-1",
                category="engine",
                title="Estimate",
                statement="An estimate",
                status=EvidenceStatus.ESTIMATE,
                confidence=ConfidenceLevel.LOW,
                source_ids=["source-1"],
                is_demo=True,
            )
        ],
        known_issues=[],
        market_analysis=MarketAnalysis(
            status=EvidenceStatus.INSUFFICIENT_DATA,
            confidence=ConfidenceLevel.LOW,
            currency="AZN",
        ),
        local_costs=[],
        owner_feedback=OwnerFeedbackAggregation(
            unique_material_count=0,
            unique_observation_count=0,
            duplicate_count=0,
            topics=[],
            positive_topics=[],
            negative_topics=[],
            mixed_topics=[],
        ),
        ownership_calculation=OwnershipCostResult(
            status=EvidenceStatus.INSUFFICIENT_DATA,
            planned_maintenance=MoneyRange(low=0, high=0, currency="AZN"),
        ),
        fit_analysis=FitAnalysis(
            rating=FitRating.COMPROMISE,
            score=50,
            confidence=ConfidenceLevel.LOW,
            reasons=[],
            missing_facts=[],
        ),
        sources=[],
    )


def test_confirmed_evidence_requires_source() -> None:
    with pytest.raises(ValidationError):
        EvidenceItem(
            id="fact",
            category="engine",
            title="Fact",
            statement="Statement",
            status=EvidenceStatus.CONFIRMED,
            confidence=ConfidenceLevel.HIGH,
        )


def test_generator_cannot_upgrade_estimate_to_confirmed() -> None:
    generated = GeneratedReport(
        language="en",
        verdict=FitRating.COMPROMISE,
        verdict_summary="Grounded",
        inspection_notice="Inspection required",
        sections=[
            GeneratedSection(
                key="engine",
                title="Engine",
                summary="Invalid upgrade",
                claims=[
                    GroundedClaim(
                        text="Invalid upgrade",
                        status=EvidenceStatus.CONFIRMED,
                        evidence_ids=["estimate-1"],
                    )
                ],
            )
        ],
    )
    with pytest.raises(UngroundedReportError, match="upgraded"):
        validate_generated_report(_bundle(), generated)
