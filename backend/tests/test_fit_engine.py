from __future__ import annotations

from app.models.enums import ConfidenceLevel, EvidenceStatus, FitRating
from app.report_engine import FitEngine
from app.schemas.fit import GroundedMetric, UsageProfileInput, VehicleFitFacts


def _profile() -> UsageProfileInput:
    return UsageProfileInput(
        monthly_mileage_km=1800,
        city_share=0.65,
        poor_roads=True,
        mountains=True,
        passengers=5,
        cargo_need="high",
        economy_priority=5,
        reliability_priority=5,
        comfort_priority=4,
        performance_priority=2,
        maintenance_cost_priority=5,
        resale_priority=4,
    )


def _metric(value: float) -> GroundedMetric:
    return GroundedMetric(
        value=value,
        status=EvidenceStatus.CONFIRMED,
        evidence_ids=[f"evidence-{value}"],
    )


def test_fit_uses_grounded_metrics_and_user_conditions() -> None:
    facts = VehicleFitFacts(
        ground_clearance_mm=190,
        ground_clearance_status=EvidenceStatus.CONFIRMED,
        drivetrain="AWD",
        drivetrain_status=EvidenceStatus.CONFIRMED,
        economy=_metric(80),
        reliability=_metric(84),
        comfort=_metric(75),
        performance=_metric(68),
        maintenance_affordability=_metric(78),
        resale_liquidity=_metric(76),
        passenger_space=_metric(72),
        cargo_space=_metric(70),
    )
    result = FitEngine().analyze(_profile(), facts)
    assert result.rating == FitRating.STRONG_FIT
    assert result.confidence == ConfidenceLevel.HIGH
    assert any(reason.code == "conditions.road_clearance" for reason in result.reasons)
    assert any(reason.code == "conditions.mountain_drivetrain" for reason in result.reasons)


def test_missing_facts_reduce_confidence_instead_of_being_invented() -> None:
    result = FitEngine().analyze(_profile(), VehicleFitFacts())
    assert result.rating == FitRating.COMPROMISE
    assert result.confidence == ConfidenceLevel.LOW
    assert "reliability" in result.missing_facts
    assert "ground_clearance_mm" in result.missing_facts
