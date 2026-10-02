from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.catalog import (
    CountryProfile,
    RegionProfile,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)
from app.models.enums import (
    ConfidenceLevel,
    DataOrigin,
    EvidenceCategory,
    EvidenceStatus,
    Sentiment,
    Severity,
    SourceTier,
    SourceUsageStatus,
)
from app.models.evidence import (
    KnownIssue,
    LocalCostItem,
    MarketListing,
    OwnerEvidence,
    SourceRecord,
    TechnicalEvidence,
)
from app.models.vehicle_knowledge import VehicleKnowledgeProfile

DEMO_MAKE = "Demo Motors"
DEMO_MODEL = "Atlas"


def seed_demo(session: Session) -> str:
    existing = session.scalar(select(VehicleMake).where(VehicleMake.name == DEMO_MAKE))
    if existing:
        variant = session.scalar(
            select(VehicleVariant)
            .join(VehicleGeneration)
            .join(VehicleModel)
            .where(VehicleModel.make_id == existing.id)
        )
        if variant is None:
            raise RuntimeError("Partial demo seed detected")
        seed_autoexpert2_demo(session)
        session.commit()
        return variant.id

    now = datetime(2026, 9, 1, tzinfo=UTC)
    source = SourceRecord(
        title="Auto Expert synthetic development fixture",
        publisher="Auto Expert Development",
        url="https://example.invalid/autoexpert/demo-fixture",
        source_type="DEMO_FIXTURE",
        source_tier=SourceTier.C,
        data_origin=DataOrigin.DEMO,
        market="AZ",
        language="en",
        retrieved_at=now,
        notes="Synthetic data for pipeline testing; never production evidence.",
        confidence=ConfidenceLevel.HIGH,
        usage_status=SourceUsageStatus.ACTIVE,
        is_demo=True,
    )
    session.add(source)
    session.flush()

    country = CountryProfile(
        country_code="AZ",
        name="Azerbaijan — demo profile",
        currency="AZN",
        default_language="az",
        road_context={"fixture": True},
        supply_context={"fixture": True},
        is_demo=True,
    )
    country.regions.append(
        RegionProfile(
            name="Baku demo",
            city="Baku",
            road_context={"fixture": True},
            climate_context={"fixture": True},
            service_context={"fixture": True},
            is_demo=True,
        )
    )
    make = VehicleMake(name=DEMO_MAKE, normalized_name="demomotors", is_demo=True)
    model = VehicleModel(name=DEMO_MODEL, normalized_name="atlas", is_demo=True)
    generation = VehicleGeneration(
        name="Demo Generation 1",
        code="D1",
        start_year=2020,
        end_year=2024,
        is_demo=True,
    )
    variant = VehicleVariant(
        market="AZ",
        name="1.8 Demo Automatic FWD",
        year_from=2020,
        year_to=2024,
        engine_code="DEMO-E18",
        engine="1.8 Demo Petrol",
        transmission_code="DEMO-A6",
        transmission="6-speed demo automatic",
        drivetrain="FWD",
        body="sedan",
        fuel="petrol",
        displacement_l=Decimal("1.80"),
        power_kw=Decimal("100.00"),
        ground_clearance_mm=170,
        specifications={"fixture": True},
        specification_source_id=source.id,
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    make.models.append(model)
    model.generations.append(generation)
    generation.variants.append(variant)
    session.add_all([country, make])
    session.flush()

    fuel_evidence = TechnicalEvidence(
        vehicle_variant_id=variant.id,
        source_id=source.id,
        category=EvidenceCategory.FUEL,
        title="Synthetic consumption range",
        statement="DEMO: synthetic real-use consumption range for pipeline verification.",
        status=EvidenceStatus.ESTIMATE,
        confidence=ConfidenceLevel.MEDIUM,
        market="AZ",
        conditions={
            "consumption_city_low": 8.5,
            "consumption_city_high": 10.5,
            "consumption_highway_low": 5.8,
            "consumption_highway_high": 7.2,
            "fit_metrics": {"economy": 68},
        },
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    engine_evidence = TechnicalEvidence(
        vehicle_variant_id=variant.id,
        source_id=source.id,
        category=EvidenceCategory.ENGINE,
        title="Synthetic engine evidence",
        statement="DEMO: engine statement used only to test evidence traceability.",
        status=EvidenceStatus.CONFIRMED,
        confidence=ConfidenceLevel.HIGH,
        market="AZ",
        conditions={
            "fit_metrics": {
                "reliability": 72,
                "maintenance_affordability": 65,
                "performance": 58,
                "resale_liquidity": 61,
                "comfort": 66,
                "passenger_space": 64,
                "cargo_space": 57,
            }
        },
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    transmission_evidence = TechnicalEvidence(
        vehicle_variant_id=variant.id,
        source_id=source.id,
        category=EvidenceCategory.TRANSMISSION,
        title="Synthetic transmission evidence",
        statement="DEMO: transmission statement used only to test report section routing.",
        status=EvidenceStatus.CONFIRMED,
        confidence=ConfidenceLevel.HIGH,
        market="AZ",
        conditions={},
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    session.add_all([fuel_evidence, engine_evidence, transmission_evidence])
    session.flush()
    session.add(
        KnownIssue(
            vehicle_variant_id=variant.id,
            component="suspension",
            description="DEMO: synthetic issue used to validate inspection guidance.",
            affected_variants={"variant_id": variant.id},
            conditions={"fixture": True},
            severity=Severity.MEDIUM,
            evidence_ids=[engine_evidence.id],
            confidence=ConfidenceLevel.MEDIUM,
            inspection_recommendation=(
                "DEMO: ask a workshop to inspect the front suspension; this does not certify "
                "the specific vehicle."
            ),
            status=EvidenceStatus.ESTIMATE,
            is_demo=True,
            data_origin=DataOrigin.DEMO,
        )
    )

    prices = [20500, 21200, 21800, 22100, 22750, 23500, 120000]
    for index, price in enumerate(prices, start=1):
        session.add(
            MarketListing(
                vehicle_variant_id=variant.id,
                source_id=source.id,
                external_key=f"demo-listing-{index}",
                country="AZ",
                city="Baku",
                make=DEMO_MAKE,
                model=DEMO_MODEL,
                generation="D1",
                year=2022 + index % 2,
                engine="1.8 Demo Petrol",
                displacement_l=Decimal("1.80"),
                transmission="6-speed demo automatic",
                drivetrain="FWD",
                mileage_km=70_000 + index * 3_000,
                price=Decimal(price),
                currency="AZN",
                url=f"https://example.invalid/listings/demo-{index}",
                observed_at=now - timedelta(days=index),
                is_demo=True,
                data_origin=DataOrigin.DEMO,
            )
        )

    session.add_all(
        [
            LocalCostItem(
                source_id=source.id,
                country="AZ",
                city="Baku",
                vehicle_variant_id=variant.id,
                applicability={"fuel": "petrol"},
                category="fuel",
                operation="DEMO petrol price per liter",
                part_price_low=Decimal("1.10"),
                part_price_high=Decimal("1.20"),
                currency="AZN",
                updated_at_source=now,
                is_demo=True,
                data_origin=DataOrigin.DEMO,
            ),
            LocalCostItem(
                source_id=source.id,
                country="AZ",
                city="Baku",
                vehicle_variant_id=variant.id,
                applicability={"include_in_starting_service": True},
                category="maintenance",
                operation="DEMO initial oil service",
                part_price_low=Decimal("70"),
                part_price_high=Decimal("100"),
                labor_price_low=Decimal("20"),
                labor_price_high=Decimal("35"),
                currency="AZN",
                updated_at_source=now,
                is_demo=True,
                data_origin=DataOrigin.DEMO,
            ),
        ]
    )

    topics = ["suspension", "comfort", "fuel", "electronics"]
    for index in range(12):
        topic = topics[index % len(topics)]
        material_key = f"demo-owner-material-{index + 1}"
        summary = f"DEMO owner observation {index + 1} about {topic}."
        dedupe = hashlib.sha256(
            f"{variant.id}|{material_key}|{topic}|{summary}".encode()
        ).hexdigest()
        session.add(
            OwnerEvidence(
                source_id=source.id,
                vehicle_variant_id=variant.id,
                owner_identity_key=f"demo-owner-{index + 1}",
                material_identity_key=material_key,
                dedupe_key=dedupe,
                mileage_km=60_000 + index * 5_000,
                component=topic,
                topic=topic,
                sentiment=Sentiment.NEGATIVE if topic == "suspension" else Sentiment.POSITIVE,
                issue_type="DEMO_FIXTURE" if topic == "suspension" else None,
                summary=summary,
                observed_at=now - timedelta(days=index),
                is_demo=True,
                data_origin=DataOrigin.DEMO,
            )
        )

    seed_autoexpert2_demo(session)
    session.commit()
    return variant.id


def seed_autoexpert2_demo(session: Session) -> str:
    existing = session.scalar(
        select(VehicleKnowledgeProfile).where(
            VehicleKnowledgeProfile.make == "Toyota",
            VehicleKnowledgeProfile.model == "Camry",
            VehicleKnowledgeProfile.year == 2019,
            VehicleKnowledgeProfile.market == "USA",
            VehicleKnowledgeProfile.is_demo.is_(True),
        )
    )
    if existing is not None:
        return existing.id

    now = datetime(2026, 9, 12, tzinfo=UTC)
    source = SourceRecord(
        title="Auto Expert 2.0 synthetic Camry/VIN fixture",
        publisher="Auto Expert Development",
        url="https://example.invalid/autoexpert/camry-vin-demo-fixture",
        source_type="DEMO_FIXTURE",
        source_tier=SourceTier.C,
        data_origin=DataOrigin.DEMO,
        market="US",
        language="en",
        retrieved_at=now,
        notes=(
            "Synthetic fixture for the accepted Camry dossier structure. "
            "It is not a real VIN-history source."
        ),
        confidence=ConfidenceLevel.HIGH,
        usage_status=SourceUsageStatus.ACTIVE,
        is_demo=True,
    )
    session.add(source)
    session.flush()

    make = session.scalar(select(VehicleMake).where(VehicleMake.normalized_name == "toyota"))
    if make is None:
        make = VehicleMake(name="Toyota", normalized_name="toyota", is_demo=True)
        session.add(make)
        session.flush()
    model = session.scalar(
        select(VehicleModel).where(
            VehicleModel.make_id == make.id,
            VehicleModel.normalized_name == "camry",
        )
    )
    if model is None:
        model = VehicleModel(
            make_id=make.id,
            name="Camry",
            normalized_name="camry",
            is_demo=True,
        )
        session.add(model)
        session.flush()
    generation = session.scalar(
        select(VehicleGeneration).where(
            VehicleGeneration.model_id == model.id,
            VehicleGeneration.code == "XV70",
            VehicleGeneration.start_year == 2017,
        )
    )
    if generation is None:
        generation = VehicleGeneration(
            model_id=model.id,
            name="XV70",
            code="XV70",
            start_year=2017,
            end_year=2024,
            is_demo=True,
        )
        session.add(generation)
        session.flush()
    variant = session.scalar(
        select(VehicleVariant).where(
            VehicleVariant.generation_id == generation.id,
            VehicleVariant.market == "US",
            VehicleVariant.engine_code == "A25A-FKS",
            VehicleVariant.year_from == 2019,
            VehicleVariant.year_to == 2019,
        )
    )
    if variant is None:
        variant = VehicleVariant(
            generation_id=generation.id,
            specification_source_id=source.id,
            market="US",
            name="2019 2.5 A25A-FKS 8AT FWD — DEMO",
            year_from=2019,
            year_to=2019,
            engine_code="A25A-FKS",
            engine="2.5 petrol",
            transmission_code="8AT",
            transmission="8AT",
            drivetrain="FWD",
            body="sedan",
            fuel="petrol",
            specifications={"fixture": True, "source_market": "USA"},
            is_demo=True,
            data_origin=DataOrigin.DEMO,
        )
        session.add(variant)
        session.flush()

    identity = TechnicalEvidence(
        vehicle_variant_id=variant.id,
        source_id=source.id,
        category=EvidenceCategory.OTHER,
        title="DEMO vehicle identity",
        statement="DEMO: Toyota Camry XV70 2019 USA profile identity fixture.",
        status=EvidenceStatus.CONFIRMED,
        confidence=ConfidenceLevel.HIGH,
        market="US",
        conditions={"fixture": True},
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    engine = TechnicalEvidence(
        vehicle_variant_id=variant.id,
        source_id=source.id,
        category=EvidenceCategory.ENGINE,
        title="DEMO A25A-FKS identity",
        statement="DEMO: A25A-FKS engine identity fixture.",
        status=EvidenceStatus.CONFIRMED,
        confidence=ConfidenceLevel.HIGH,
        market="US",
        conditions={"fixture": True},
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    transmission = TechnicalEvidence(
        vehicle_variant_id=variant.id,
        source_id=source.id,
        category=EvidenceCategory.TRANSMISSION,
        title="DEMO 8AT identity",
        statement="DEMO: 8AT transmission identity fixture.",
        status=EvidenceStatus.CONFIRMED,
        confidence=ConfidenceLevel.HIGH,
        market="US",
        conditions={"fixture": True},
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    session.add_all([identity, engine, transmission])
    session.flush()

    issue = KnownIssue(
        vehicle_variant_id=variant.id,
        component="demo_component",
        description="DEMO: synthetic weak-point entry for dossier layout validation.",
        affected_variants={"vehicle_variant_id": variant.id, "fixture": True},
        conditions={"fixture": True},
        symptoms=["DEMO: synthetic symptom"],
        consequences="DEMO: synthetic consequence; no real repair claim.",
        typical_mileage_min=None,
        typical_mileage_max=None,
        severity=Severity.MEDIUM,
        evidence_ids=[engine.id],
        confidence=ConfidenceLevel.MEDIUM,
        inspection_recommendation=(
            "DEMO: request a physical inspection; this fixture does not certify a vehicle."
        ),
        status=EvidenceStatus.ESTIMATE,
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    session.add(issue)

    profile = VehicleKnowledgeProfile(
        vehicle_variant_id=variant.id,
        make="Toyota",
        model="Camry",
        generation="XV70",
        production_year_start=2017,
        production_year_end=2024,
        market="USA",
        year=2019,
        engine="2.5 petrol",
        engine_code="A25A-FKS",
        transmission="8AT",
        drivetrain="FWD",
        body="sedan",
        fuel="petrol",
        profile_version="2.0.0-demo",
        freshness_at=now,
        dossier_seed={"fixture": True, "accepted_sample_structure": True},
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    profile.sources.append(source)
    profile.evidence.extend([identity, engine, transmission])
    session.add(profile)
    session.flush()
    return profile.id


def seed_autoexpert2_ford_demo(session: Session) -> str:
    """Create a Ford-compatible identity shell for the real example VIN.

    Only make/model/year/body are represented. Powertrain fields remain visibly
    unresolved because this synthetic VIN-history fixture is not technical evidence.
    """

    existing = session.scalar(
        select(VehicleKnowledgeProfile).where(
            VehicleKnowledgeProfile.make == "Ford",
            VehicleKnowledgeProfile.model == "Fusion",
            VehicleKnowledgeProfile.year == 2019,
            VehicleKnowledgeProfile.market == "USA",
            VehicleKnowledgeProfile.is_demo.is_(True),
        )
    )
    if existing is not None:
        return existing.id

    now = datetime(2026, 9, 17, tzinfo=UTC)
    source = SourceRecord(
        title="Auto Expert Ford Fusion VIN-history demo fixture",
        publisher="Auto Expert Development",
        url="https://example.invalid/autoexpert/ford-fusion-vin-demo-fixture",
        source_type="VIN_DEMO_FIXTURE",
        source_tier=SourceTier.C,
        data_origin=DataOrigin.DEMO,
        market="US",
        language="en",
        retrieved_at=now,
        notes=(
            "Synthetic history fixture attached to the Ford-compatible example VIN. "
            "It is not a real VIN-history source and contains no powertrain claim."
        ),
        confidence=ConfidenceLevel.HIGH,
        usage_status=SourceUsageStatus.ACTIVE,
        is_demo=True,
    )
    session.add(source)
    session.flush()

    make = session.scalar(select(VehicleMake).where(VehicleMake.normalized_name == "ford"))
    if make is None:
        make = VehicleMake(name="Ford", normalized_name="ford", is_demo=True)
        session.add(make)
        session.flush()
    model = session.scalar(
        select(VehicleModel).where(
            VehicleModel.make_id == make.id,
            VehicleModel.normalized_name == "fusion",
        )
    )
    if model is None:
        model = VehicleModel(
            make_id=make.id,
            name="Fusion",
            normalized_name="fusion",
            is_demo=True,
        )
        session.add(model)
        session.flush()
    generation = session.scalar(
        select(VehicleGeneration).where(
            VehicleGeneration.model_id == model.id,
            VehicleGeneration.code == "UNRESOLVED-DEMO-2019",
        )
    )
    if generation is None:
        generation = VehicleGeneration(
            model_id=model.id,
            name="Unresolved — demo identity only",
            code="UNRESOLVED-DEMO-2019",
            start_year=2019,
            end_year=2019,
            is_demo=True,
        )
        session.add(generation)
        session.flush()
    variant = VehicleVariant(
        generation_id=generation.id,
        specification_source_id=source.id,
        market="US",
        name="2019 Ford Fusion — DEMO identity shell",
        year_from=2019,
        year_to=2019,
        engine_code="UNRESOLVED",
        engine="UNRESOLVED — DEMO identity only",
        transmission_code=None,
        transmission="UNRESOLVED",
        drivetrain="UNRESOLVED",
        body="sedan",
        fuel="UNRESOLVED",
        specifications={"fixture": True, "powertrain_unresolved": True},
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    session.add(variant)
    session.flush()

    identity = TechnicalEvidence(
        vehicle_variant_id=variant.id,
        source_id=source.id,
        category=EvidenceCategory.OTHER,
        title="DEMO Ford-compatible VIN identity shell",
        statement=(
            "DEMO: Ford Fusion 2019 identity shell for UI validation; powertrain details "
            "are intentionally unresolved."
        ),
        status=EvidenceStatus.CONFIRMED,
        confidence=ConfidenceLevel.HIGH,
        market="US",
        conditions={"fixture": True, "powertrain_unresolved": True},
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    session.add(identity)
    session.flush()

    profile = VehicleKnowledgeProfile(
        vehicle_variant_id=variant.id,
        make="Ford",
        model="Fusion",
        generation="UNRESOLVED",
        production_year_start=2019,
        production_year_end=2019,
        market="USA",
        year=2019,
        engine="UNRESOLVED — DEMO identity only",
        engine_code="UNRESOLVED",
        transmission="UNRESOLVED",
        drivetrain="UNRESOLVED",
        body="sedan",
        fuel="UNRESOLVED",
        profile_version="2.0.0-demo-ford-identity",
        freshness_at=now,
        dossier_seed={"fixture": True, "powertrain_unresolved": True},
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    profile.sources.append(source)
    profile.evidence.append(identity)
    session.add(profile)
    session.flush()
    return profile.id


def main() -> None:
    with SessionLocal() as session:
        variant_id = seed_demo(session)
    print(f"Demo seed ready. Vehicle variant ID: {variant_id}")


if __name__ == "__main__":
    main()
