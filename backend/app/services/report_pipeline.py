from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.report_pricing import configured_report_price
from app.llm.deterministic import DeterministicLLMProvider
from app.market_engine import MarketEngine
from app.models.analysis import AnalysisRequest, Report
from app.models.catalog import VehicleVariant
from app.models.enums import EvidenceStatus, ReportStatus
from app.models.evidence import LocalCostItem, SourceRecord, TechnicalEvidence
from app.models.user import User
from app.pricing import OwnershipCostEngine
from app.providers.analytics import DatabaseAnalyticsProvider
from app.providers.database import (
    DatabaseLocalCostProvider,
    DatabaseMarketDataProvider,
    DatabaseOwnerReviewProvider,
    DatabaseTechnicalDataProvider,
)
from app.report_engine import FitEngine
from app.repositories.vehicles import VehicleRepository
from app.review_engine import OwnerFeedbackEngine
from app.schemas.analysis import (
    AnalysisCreate,
    EvidenceBundle,
    KnownIssueSnapshot,
    LocalCostSnapshot,
    PreviewResponse,
    VehicleSnapshot,
)
from app.schemas.common import EvidenceItem, SourceSnapshot
from app.schemas.fit import GroundedMetric, VehicleFitFacts
from app.schemas.market import MarketListingInput, MarketVehicle
from app.schemas.ownership import ConsumptionRange, OwnershipCostInput, PlannedCost
from app.schemas.reviews import OwnerObservation
from app.services.evidence_validation import validate_generated_report


class ReportPipeline:
    def __init__(self, session: Session):
        self.session = session
        self.technical_provider = DatabaseTechnicalDataProvider(session)
        self.market_provider = DatabaseMarketDataProvider(session)
        self.cost_provider = DatabaseLocalCostProvider(session)
        self.owner_provider = DatabaseOwnerReviewProvider(session)
        self.llm_provider = DeterministicLLMProvider()
        self.analytics = DatabaseAnalyticsProvider(session)

    def create_preview(self, user: User, value: AnalysisCreate) -> PreviewResponse:
        variant = VehicleRepository(self.session).resolve(value)
        request = AnalysisRequest(
            user_id=user.id,
            vehicle_variant_id=variant.id,
            country=value.vehicle.country,
            city=value.vehicle.city,
            language=value.report_language,
            vehicle_input=value.vehicle.model_dump(mode="json"),
            usage_profile=value.usage_profile.model_dump(mode="json"),
            selected_price=value.vehicle.price,
            currency=value.vehicle.currency,
            mileage_km=value.vehicle.mileage_km,
        )
        self.session.add(request)
        self.session.flush()

        bundle = self._build_bundle(variant, value)
        generated = self.llm_provider.generate_report(bundle, value.report_language)
        validate_generated_report(bundle, generated)
        report = Report(
            user_id=user.id,
            analysis_request_id=request.id,
            status=ReportStatus.PREVIEW,
            language=value.report_language,
            is_unlocked=False,
            is_demo=variant.is_demo,
            input_snapshot=value.model_dump(mode="json"),
            evidence_bundle=bundle.model_dump(mode="json"),
            calculated_data={
                "market_analysis": bundle.market_analysis.model_dump(mode="json"),
                "owner_feedback": bundle.owner_feedback.model_dump(mode="json"),
                "ownership_calculation": bundle.ownership_calculation.model_dump(mode="json"),
                "fit_analysis": bundle.fit_analysis.model_dump(mode="json"),
            },
            generated_sections=generated.model_dump(mode="json"),
        )
        self.session.add(report)
        self.session.flush()
        self.analytics.track(
            "preview_generated",
            user_id=user.id,
            anonymous_id=None,
            properties={"report_id": report.id, "is_demo": report.is_demo},
        )
        self.session.commit()

        claims = [claim for section in generated.sections for claim in section.claims]
        price, currency = configured_report_price(value.vehicle.country)
        return PreviewResponse(
            report_id=report.id,
            vehicle=bundle.vehicle,
            verdict=generated.verdict,
            verdict_summary=generated.verdict_summary,
            highlights=claims[:3],
            local_market_status=bundle.market_analysis.status,
            available_sections=[section.key for section in generated.sections],
            is_unlocked=False,
            is_demo=report.is_demo,
            price=price,
            currency=currency,
            country=value.vehicle.country,
            city=value.vehicle.city,
            comparable_count=bundle.market_analysis.comparable_count,
            used_comparable_count=bundle.market_analysis.used_count,
            evidence_count=len(bundle.technical_evidence) + len(bundle.known_issues),
            source_count=len(bundle.sources),
            pipeline_stages=[
                "vehicle_resolution",
                "technical_evidence",
                "market_analysis",
                "ownership_calculation",
                "owner_feedback",
                "fit_analysis",
                "grounding_validation",
                "snapshot_saved",
            ],
        )

    def _build_bundle(self, variant: VehicleVariant, value: AnalysisCreate) -> EvidenceBundle:
        evidence_rows = self.technical_provider.evidence_for(variant.id, value.vehicle.country)
        issue_rows = self.technical_provider.issues_for(variant.id)
        listing_rows = self.market_provider.listings_for(
            country=value.vehicle.country,
            make=variant.generation.model.make.name,
            model=variant.generation.model.name,
        )
        cost_rows = self.cost_provider.costs_for(
            country=value.vehicle.country,
            city=value.vehicle.city,
            variant_id=variant.id,
        )
        owner_rows = self.owner_provider.observations_for(variant.id)

        evidence = [
            EvidenceItem(
                id=item.id,
                category=item.category.value,
                title=item.title,
                statement=item.statement,
                status=item.status,
                confidence=item.confidence,
                source_ids=[item.source_id],
                conditions=item.conditions,
                is_demo=item.is_demo,
            )
            for item in evidence_rows
        ]
        issues = [
            KnownIssueSnapshot(
                id=item.id,
                component=item.component,
                description=item.description,
                conditions=item.conditions,
                mileage_range=[
                    mileage
                    for mileage in (item.typical_mileage_min, item.typical_mileage_max)
                    if mileage is not None
                ]
                or None,
                severity=item.severity,
                evidence_ids=item.evidence_ids,
                confidence=item.confidence,
                inspection_recommendation=item.inspection_recommendation,
                status=item.status,
                is_demo=item.is_demo,
            )
            for item in issue_rows
        ]
        market_listings = [
            MarketListingInput(
                id=item.id,
                country=item.country,
                city=item.city,
                make=item.make,
                model=item.model,
                generation=item.generation,
                year=item.year,
                engine=item.engine,
                displacement_l=item.displacement_l,
                transmission=item.transmission,
                drivetrain=item.drivetrain,
                mileage_km=item.mileage_km,
                price=item.price,
                currency=item.currency,
                observed_at=item.observed_at.isoformat(),
                source_id=item.source_id,
                url=item.url,
                is_demo=item.is_demo,
            )
            for item in listing_rows
        ]
        market_analysis = MarketEngine().analyze(
            MarketVehicle(
                country=value.vehicle.country,
                city=value.vehicle.city,
                make=variant.generation.model.make.name,
                model=variant.generation.model.name,
                generation=variant.generation.code or variant.generation.name,
                year=value.vehicle.year,
                engine=variant.engine,
                displacement_l=variant.displacement_l,
                transmission=variant.transmission,
                drivetrain=variant.drivetrain,
                mileage_km=value.vehicle.mileage_km,
                selected_price=value.vehicle.price,
                currency=value.vehicle.currency,
            ),
            market_listings,
        )
        owner_evidence = [
            OwnerObservation(
                id=item.id,
                material_identity_key=item.material_identity_key,
                owner_identity_key=item.owner_identity_key,
                topic=item.topic,
                component=item.component,
                sentiment=item.sentiment,
                summary=item.summary,
                source_id=item.source_id,
                mileage_km=item.mileage_km,
                observed_at=item.observed_at.isoformat() if item.observed_at else None,
                is_demo=item.is_demo,
            )
            for item in owner_rows
        ]
        owner_feedback = OwnerFeedbackEngine().aggregate(owner_evidence)
        ownership = OwnershipCostEngine().calculate(
            self._ownership_input(value, evidence_rows, cost_rows)
        )
        fit = FitEngine().analyze(value.usage_profile, self._fit_facts(variant, evidence_rows))
        source_ids = {
            *(item.source_id for item in evidence_rows),
            *(item.source_id for item in listing_rows),
            *(item.source_id for item in cost_rows),
            *(item.source_id for item in owner_rows),
        }
        if variant.specification_source_id:
            source_ids.add(variant.specification_source_id)
        sources = (
            list(self.session.scalars(select(SourceRecord).where(SourceRecord.id.in_(source_ids))))
            if source_ids
            else []
        )
        return EvidenceBundle(
            vehicle=self._vehicle_snapshot(variant, value),
            user_profile=value.usage_profile,
            technical_evidence=evidence,
            known_issues=issues,
            market_listings=market_listings,
            market_analysis=market_analysis,
            local_costs=[self._cost_snapshot(item) for item in cost_rows],
            owner_evidence=owner_evidence,
            owner_feedback=owner_feedback,
            ownership_calculation=ownership,
            fit_analysis=fit,
            sources=[self._source_snapshot(item) for item in sources],
        )

    @staticmethod
    def _vehicle_snapshot(variant: VehicleVariant, value: AnalysisCreate) -> VehicleSnapshot:
        return VehicleSnapshot(
            variant_id=variant.id,
            make=variant.generation.model.make.name,
            model=variant.generation.model.name,
            generation=variant.generation.name,
            variant=variant.name,
            market=variant.market,
            year=value.vehicle.year,
            engine=variant.engine,
            transmission=variant.transmission,
            drivetrain=variant.drivetrain,
            body=variant.body,
            fuel=variant.fuel,
            displacement_l=variant.displacement_l,
            power_kw=variant.power_kw,
            ground_clearance_mm=variant.ground_clearance_mm,
            source_ids=[variant.specification_source_id] if variant.specification_source_id else [],
            is_demo=variant.is_demo,
        )

    @staticmethod
    def _source_snapshot(value: SourceRecord) -> SourceSnapshot:
        return SourceSnapshot(
            id=value.id,
            title=value.title,
            publisher=value.publisher,
            url=value.url,
            source_type=value.source_type,
            market=value.market,
            language=value.language,
            published_at=value.published_at.isoformat() if value.published_at else None,
            retrieved_at=value.retrieved_at.isoformat(),
            confidence=value.confidence,
            usage_status=value.usage_status,
            is_demo=value.is_demo,
        )

    @staticmethod
    def _cost_snapshot(value: LocalCostItem) -> LocalCostSnapshot:
        return LocalCostSnapshot(
            id=value.id,
            category=value.category,
            operation=value.operation,
            applicability=value.applicability,
            part_price_low=value.part_price_low,
            part_price_high=value.part_price_high,
            labor_price_low=value.labor_price_low,
            labor_price_high=value.labor_price_high,
            currency=value.currency,
            source_id=value.source_id,
            updated_at=value.updated_at_source.isoformat(),
            is_demo=value.is_demo,
        )

    @staticmethod
    def _ownership_input(
        value: AnalysisCreate,
        evidence: list[TechnicalEvidence],
        costs: list[LocalCostItem],
    ) -> OwnershipCostInput:
        consumption = None
        for item in evidence:
            fields = item.conditions
            required = {
                "consumption_city_low",
                "consumption_city_high",
                "consumption_highway_low",
                "consumption_highway_high",
            }
            if required <= fields.keys() and item.status in {
                EvidenceStatus.CONFIRMED,
                EvidenceStatus.ESTIMATE,
            }:
                consumption = ConsumptionRange(
                    city_low=Decimal(str(fields["consumption_city_low"])),
                    city_high=Decimal(str(fields["consumption_city_high"])),
                    highway_low=Decimal(str(fields["consumption_highway_low"])),
                    highway_high=Decimal(str(fields["consumption_highway_high"])),
                )
                break
        fuel = next((item for item in costs if item.category.casefold() == "fuel"), None)
        fuel_price = None
        fuel_date = None
        if fuel and fuel.part_price_low is not None:
            high = fuel.part_price_high or fuel.part_price_low
            fuel_price = (fuel.part_price_low + high) / 2
            fuel_date = fuel.updated_at_source.date().isoformat()

        planned: list[PlannedCost] = []
        starting: list[PlannedCost] = []
        for item in costs:
            if item.category.casefold() == "fuel":
                continue
            low = (item.part_price_low or Decimal(0)) + (item.labor_price_low or Decimal(0))
            high = (item.part_price_high or item.part_price_low or Decimal(0)) + (
                item.labor_price_high or item.labor_price_low or Decimal(0)
            )
            planned_cost = PlannedCost(
                name=item.operation,
                low=low,
                high=high,
                required_first_year=bool(item.applicability.get("required_first_year")),
                assumption=(
                    f"{item.operation}; local source updated "
                    f"{item.updated_at_source.date().isoformat()}."
                ),
            )
            if item.applicability.get("include_in_starting_service"):
                starting.append(planned_cost)
            elif item.applicability.get("include_in_planned_maintenance"):
                planned.append(planned_cost)
        return OwnershipCostInput(
            monthly_mileage_km=value.usage_profile.monthly_mileage_km,
            city_share=Decimal(str(value.usage_profile.city_share)),
            consumption=consumption,
            fuel_price_per_liter=fuel_price,
            currency=value.vehicle.currency,
            planned_costs=planned,
            starting_service_costs=starting,
            fuel_price_source_date=fuel_date,
        )

    @staticmethod
    def _fit_facts(variant: VehicleVariant, evidence: list[TechnicalEvidence]) -> VehicleFitFacts:
        catalog_status = (
            EvidenceStatus.CONFIRMED
            if variant.specification_source_id
            else EvidenceStatus.INSUFFICIENT_DATA
        )
        metrics: dict[str, GroundedMetric] = {}
        for item in evidence:
            for name, score in item.conditions.get("fit_metrics", {}).items():
                if name not in metrics and item.status in {
                    EvidenceStatus.CONFIRMED,
                    EvidenceStatus.ESTIMATE,
                }:
                    metrics[name] = GroundedMetric(
                        value=float(score), status=item.status, evidence_ids=[item.id]
                    )
        return VehicleFitFacts(
            ground_clearance_mm=variant.ground_clearance_mm,
            ground_clearance_status=catalog_status,
            drivetrain=variant.drivetrain,
            drivetrain_status=catalog_status,
            economy=metrics.get("economy"),
            reliability=metrics.get("reliability"),
            comfort=metrics.get("comfort"),
            performance=metrics.get("performance"),
            maintenance_affordability=metrics.get("maintenance_affordability"),
            resale_liquidity=metrics.get("resale_liquidity"),
            passenger_space=metrics.get("passenger_space"),
            cargo_space=metrics.get("cargo_space"),
        )
