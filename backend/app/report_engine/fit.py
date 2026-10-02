from __future__ import annotations

from app.models.enums import ConfidenceLevel, EvidenceStatus, FitRating
from app.schemas.fit import (
    FitAnalysis,
    FitReason,
    GroundedMetric,
    UsageProfileInput,
    VehicleFitFacts,
)

_USABLE = {EvidenceStatus.CONFIRMED, EvidenceStatus.ESTIMATE}


class FitEngine:
    """Transparent rules operating only on supplied, status-tagged facts."""

    def analyze(self, profile: UsageProfileInput, facts: VehicleFitFacts) -> FitAnalysis:
        weighted_total = 0.0
        total_weight = 0.0
        reasons: list[FitReason] = []
        missing: list[str] = []

        metrics = [
            ("economy", profile.economy_priority, facts.economy),
            ("reliability", profile.reliability_priority, facts.reliability),
            ("comfort", profile.comfort_priority, facts.comfort),
            ("performance", profile.performance_priority, facts.performance),
            (
                "maintenance_affordability",
                profile.maintenance_cost_priority,
                facts.maintenance_affordability,
            ),
            ("resale_liquidity", profile.resale_priority, facts.resale_liquidity),
        ]
        for name, weight, metric in metrics:
            if self._usable_metric(metric):
                weighted_total += metric.value * weight
                total_weight += weight
                impact = round((metric.value - 50) * weight / 25)
                if abs(impact) >= 2:
                    reasons.append(
                        FitReason(
                            code=f"priority.{name}",
                            impact=impact,
                            evidence_status=metric.status,
                            parameters={"score": metric.value, "priority": weight},
                        )
                    )
            else:
                missing.append(name)

        base_score = weighted_total / total_weight if total_weight else 50.0
        adjustment = 0
        if profile.poor_roads or profile.unpaved_roads:
            if facts.ground_clearance_mm is not None and facts.ground_clearance_status in _USABLE:
                clearance = facts.ground_clearance_mm
                road_impact = (
                    8
                    if clearance >= 180
                    else 2
                    if clearance >= 165
                    else -8
                    if clearance >= 145
                    else -15
                )
                if profile.unpaved_roads:
                    road_impact += 2 if clearance >= 180 else -3
                adjustment += road_impact
                reasons.append(
                    FitReason(
                        code="conditions.road_clearance",
                        impact=road_impact,
                        evidence_status=facts.ground_clearance_status,
                        parameters={"ground_clearance_mm": clearance},
                    )
                )
            else:
                missing.append("ground_clearance_mm")

        if profile.mountains:
            if facts.drivetrain and facts.drivetrain_status in _USABLE:
                normalized = facts.drivetrain.casefold().replace("-", "")
                mountain_impact = 5 if normalized in {"awd", "4wd", "4x4"} else 0
                adjustment += mountain_impact
                reasons.append(
                    FitReason(
                        code="conditions.mountain_drivetrain",
                        impact=mountain_impact,
                        evidence_status=facts.drivetrain_status,
                        parameters={"drivetrain": facts.drivetrain},
                    )
                )
            else:
                missing.append("drivetrain")

        if profile.passengers >= 5:
            adjustment += self._space_adjustment(
                "passenger_space", facts.passenger_space, reasons, missing
            )
        if profile.cargo_need == "high":
            adjustment += self._space_adjustment("cargo_space", facts.cargo_space, reasons, missing)

        score = max(0, min(100, round(base_score + adjustment)))
        rating = (
            FitRating.STRONG_FIT
            if score >= 75
            else FitRating.GOOD_FIT_WITH_CONDITIONS
            if score >= 60
            else FitRating.COMPROMISE
            if score >= 45
            else FitRating.POOR_FIT
        )
        expected_facts = (
            6 + int(profile.poor_roads or profile.unpaved_roads) + int(profile.mountains)
        )
        coverage = max(0.0, 1 - len(set(missing)) / max(expected_facts, 1))
        confidence = (
            ConfidenceLevel.HIGH
            if coverage >= 0.85
            else ConfidenceLevel.MEDIUM
            if coverage >= 0.60
            else ConfidenceLevel.LOW
        )
        reasons.sort(key=lambda item: abs(item.impact), reverse=True)
        return FitAnalysis(
            rating=rating,
            score=score,
            confidence=confidence,
            reasons=reasons,
            missing_facts=sorted(set(missing)),
        )

    @staticmethod
    def _usable_metric(metric: GroundedMetric | None) -> bool:
        return metric is not None and metric.status in _USABLE

    @staticmethod
    def _space_adjustment(
        name: str,
        metric: GroundedMetric | None,
        reasons: list[FitReason],
        missing: list[str],
    ) -> int:
        if metric is None or metric.status not in _USABLE:
            missing.append(name)
            return 0
        impact = round((metric.value - 50) / 8)
        reasons.append(
            FitReason(
                code=f"conditions.{name}",
                impact=impact,
                evidence_status=metric.status,
                parameters={"score": metric.value},
            )
        )
        return impact
