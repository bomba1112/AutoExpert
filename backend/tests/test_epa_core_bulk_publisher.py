"""CORE bulk publication keeps factory precedence and stable annual identities."""

import importlib.util
import json
from pathlib import Path

import pytest
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.knowledge_ops import CatalogRevision, SourceRegistry
from app.services.catalog_verification import (
    fingerprint,
    identity_verified,
    source_confirmed_core_ready,
)
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "publish_us_epa_core", ROOT / "scripts/publish_us_epa_core.py"
)
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)
SOURCE_SHA = "a" * 64
INDEX = {"source": {"zip_sha256": SOURCE_SHA}}


def candidate(vehicle_id="101", *, drive="Front-Wheel Drive", displ="2.0"):
    raw = {
        "id": vehicle_id,
        "make": "Toyota",
        "model": "Camry",
        "baseModel": "Camry",
        "year": "2020",
        "atvType": "",
        "displ": displ,
        "cylinders": "4",
        "trany": "Automatic 8-spd",
        "drive": drive,
        "fuelType1": "Regular Gasoline",
        "comb08": "29",
    }
    return {
        "epa_vehicle_id": vehicle_id,
        "make": "Toyota",
        "model": "Camry",
        "epa_model": "Camry",
        "model_year": 2020,
        "normalized_powertrain_key": "b" * 64,
        "epa_fields": raw,
    }


def source(db):
    db.add(
        SourceRegistry(
            id="epa",
            title="DOE / EPA FuelEconomy.gov",
            state="LOCAL_RESEARCH",
            config={"commercial_reuse": False, "rights": "NON_COMMERCIAL_RESEARCH"},
        )
    )
    db.commit()


def factory_variant(
    db,
    *,
    make_name="Toyota",
    model_name="Camry",
    values=None,
    generation_code="XV70",
    cited_epa_id=None,
):
    make = VehicleMake(name=make_name, normalized_name=make_name.casefold(), is_demo=False)
    db.add(make)
    db.flush()
    model = VehicleModel(
        make_id=make.id, name=model_name, normalized_name=model_name.casefold(), is_demo=False
    )
    db.add(model)
    db.flush()
    generation = VehicleGeneration(
        model_id=model.id,
        name=generation_code,
        code=generation_code,
        start_year=2018,
        is_demo=False,
    )
    db.add(generation)
    db.flush()
    values = values or {
        "powertrain": "ICE",
        "fuel": "GASOLINE",
        "engine_displacement": 2.0,
        "cylinders": 4,
        "transmission_description": "8-speed automatic",
        "transmission_family": "AT",
        "drivetrain": "FWD",
    }
    catalog = {
        "make": make_name,
        "model": model_name,
        "model_year": 2020,
        "original_market": "US",
        "generation": generation_code,
        "configuration": "2.0 / 8AT / FWD",
        "facts": {key: {"status": "CONFIRMED", "value": value} for key, value in values.items()},
        "source_registry_id": "factory-toyota-us",
    }
    if cited_epa_id:
        catalog["external_key"] = f"factory-{make_name.casefold()}-epa-{cited_epa_id}-us"
    catalog["verification_gate"] = {
        "state": "VERIFIED_SCOPED",
        "rule_version": "test",
        "fingerprint": fingerprint(catalog),
    }
    variant = VehicleVariant(
        catalog_key="factory:test-camry",
        published_revision_id="factory-revision",
        generation_id=generation.id,
        market="US",
        name="2.0 / 8AT / FWD",
        year_from=2020,
        year_to=2020,
        specifications={"catalog": catalog},
        is_demo=False,
    )
    db.add(variant)
    db.commit()
    return variant


def test_bulk_core_publishes_once_and_keeps_all_epa_ids(db_session):
    source(db_session)
    rows = [candidate("101"), candidate("102")]
    plan, summary = core.plan_groups([rows], INDEX, db_session)
    assert summary["counts"] == {"PUBLISH_CORE": 1}
    record = plan[0]["record"]
    assert not record["generation"] and "102" in record["revision_note"]
    assert core.publish_plan(db_session, plan, INDEX)["core_published"] == 1
    db_session.expire_all()
    variant = db_session.scalar(
        select(VehicleVariant).where(VehicleVariant.catalog_key.like("epa:core-v1-%"))
    )
    catalog = variant.specifications["catalog"]
    assert catalog["source_provenance"]["epa_vehicle_ids"] == ["101", "102"]
    assert source_confirmed_core_ready(catalog)
    assert not identity_verified(catalog)
    assert core.publish_plan(db_session, plan, INDEX)["already_core_on_rerun"] == 1
    second_plan, second_summary = core.plan_groups([rows], INDEX, db_session)
    assert second_summary["counts"] == {"ALREADY_CORE": 1}
    assert core.publish_plan(db_session, second_plan, INDEX) == {}
    assert db_session.scalar(select(func.count()).select_from(VehicleVariant)) == 1
    assert db_session.scalar(select(func.count()).select_from(CatalogRevision)) == 1


def test_factory_equivalent_wins_without_creating_core_duplicate(db_session):
    source(db_session)
    existing = factory_variant(db_session)
    rows = [candidate()]
    plan, summary = core.plan_groups([rows], INDEX, db_session)
    assert summary["counts"] == {"SUPPRESSED_VERIFIED": 1}
    assert core.publish_plan(db_session, plan, INDEX) == {}
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(VehicleVariant)) == 1
    assert (
        db_session.get(VehicleVariant, existing.id).specifications["catalog"]["generation"]
        == "XV70"
    )


def test_ambiguous_drive_stays_in_insufficient_core_queue(db_session):
    source(db_session)
    plan, summary = core.plan_groups(
        [[candidate(drive="4-Wheel or All-Wheel Drive")]], INDEX, db_session
    )
    assert summary["counts"] == {"INSUFFICIENT_CORE": 1}
    assert "record" not in plan[0]


def test_epa_a1_bev_is_equivalent_to_verified_single_speed(db_session):
    source(db_session)
    factory_variant(
        db_session,
        make_name="Tesla",
        model_name="Model 3",
        generation_code="Model 3 original",
        values={
            "powertrain": "BEV",
            "fuel": "ELECTRICITY",
            "transmission_description": "Single-speed fixed ratio",
            "transmission_family": "SINGLE_SPEED",
            "drivetrain": "RWD",
        },
        cited_epa_id="10101",
    )
    row = candidate("10101", drive="Rear-Wheel Drive", displ="")
    row.update(make="Tesla", model="Model 3", epa_model="Model 3")
    row["epa_fields"].update(
        make="Tesla",
        model="Model 3",
        baseModel="Model 3",
        displ="",
        atvType="EV",
        fuelType1="Electricity",
        evMotor="electric motor",
        trany="Automatic (A1)",
        drive="Rear-Wheel Drive",
        comb08="0",
        combE="28",
    )
    plan, summary = core.plan_groups([[row]], INDEX, db_session)
    assert summary["counts"] == {"SUPPRESSED_VERIFIED": 1}
    assert "record" not in plan[0]
    other_motor = candidate("10102", drive="Rear-Wheel Drive", displ="")
    other_motor.update(
        make="Tesla",
        model="Model 3",
        epa_model="Model 3",
        normalized_powertrain_key="c" * 64,
    )
    other_motor["epa_fields"] = {
        **row["epa_fields"],
        "id": "10102",
        "evMotor": "different electric motor",
    }
    other_plan, other_summary = core.plan_groups([[other_motor]], INDEX, db_session)
    assert other_summary["counts"] == {"PUBLISH_CORE": 1}
    assert other_plan[0]["epa_ids"] == ["10102"]


def test_same_displacement_drive_year_does_not_hide_turbo_variant(db_session):
    source(db_session)
    factory_variant(
        db_session,
        values={
            "powertrain": "ICE",
            "fuel": "GASOLINE",
            "engine_displacement": 2.0,
            "cylinders": 4,
            "aspiration": "NATURALLY_ASPIRATED",
            "transmission_description": "8-speed automatic",
            "transmission_family": "AT",
            "drivetrain": "FWD",
        },
    )
    naturally_aspirated = candidate("10101")
    plan, summary = core.plan_groups([[naturally_aspirated]], INDEX, db_session)
    assert summary["counts"] == {"SUPPRESSED_VERIFIED": 1}
    assert "record" not in plan[0]

    turbo = candidate("10102")
    turbo["normalized_powertrain_key"] = "c" * 64
    turbo["epa_fields"]["tCharger"] = "T"
    turbo_plan, turbo_summary = core.plan_groups([[turbo]], INDEX, db_session)
    assert turbo_summary["counts"] == {"PUBLISH_CORE": 1}
    assert turbo_plan[0]["epa_ids"] == ["10102"]


def test_bulk_refuses_changed_cached_epa_zip(tmp_path):
    archive = tmp_path / "vehicles-current.zip"
    archive.write_bytes(b"changed source bytes")
    candidate_path = tmp_path / "candidates.jsonl"
    candidate_path.write_bytes(b"")
    index_path = tmp_path / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "source": {"url": core.EPA_URL, "zip_sha256": SOURCE_SHA},
                "candidate_jsonl_sha256": SOURCE_SHA,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="EPA_CACHED_ZIP_HASH_MISMATCH"):
        core.read_cached_groups(candidate_path, index_path, archive)


def test_grouped_core_omits_optional_facts_that_disagree_between_epa_rows():
    first, second = candidate("101"), candidate("102")
    first["epa_fields"].update(VClass="Small Station Wagons", lv4="12", range="30")
    second["epa_fields"].update(
        VClass="Small Sport Utility Vehicle 2WD", comb08="30", lv4="0", range="40"
    )
    record = core.make_record([first, second], SOURCE_SHA)
    assert {
        "powertrain", "fuel", "engine_displacement", "transmission_description", "drivetrain"
    } <= set(record.facts)
    assert not {
        "size_class", "body", "fuel_combined", "epa_range_miles", "four_door_cargo"
    } & set(record.facts)
    assert '"epa_ids":["101","102"]' in record.revision_note


def test_grouped_bev_does_not_claim_one_test_rows_range_or_economy():
    first, second = candidate("101"), candidate("102")
    for row in (first, second):
        row["epa_fields"].update(
            atvType="EV", displ="", fuelType1="Electricity", evMotor="same motor",
            trany="Automatic (A1)", comb08="0", VClass="Compact Cars"
        )
    first["epa_fields"].update(combE="31", range="317")
    second["epa_fields"].update(combE="27", range="374")
    record = core.make_record([first, second], SOURCE_SHA)
    assert record.facts["powertrain"].value == "BEV"
    assert record.facts["motor_description"].value == "same motor"
    assert "electricity_combined" not in record.facts
    assert "epa_range_miles" not in record.facts
    assert record.facts["size_class"].value == "Compact Cars"


def test_optional_fact_repair_creates_new_revision_on_existing_variant(db_session):
    source(db_session)
    first, second = candidate("101"), candidate("102")
    first["epa_fields"].update(VClass="Small Station Wagons", lv4="12")
    second["epa_fields"].update(VClass="Small Sport Utility Vehicle 2WD", comb08="30")
    old_plan, _ = core.plan_groups([[first]], INDEX, db_session)
    assert core.publish_plan(db_session, old_plan, INDEX)["core_published"] == 1
    variant = db_session.scalar(
        select(VehicleVariant).where(VehicleVariant.catalog_key.like("epa:core-v1-%"))
    )
    old_variant_id = variant.id
    old_revision_id = variant.published_revision_id
    assert "fuel_combined" in variant.specifications["catalog"]["facts"]
    corrections, summary = core.plan_optional_fact_corrections([[first, second]], INDEX, db_session)
    assert summary["correction_count"] == 1
    assert {"fuel_combined", "size_class", "body", "four_door_cargo"} <= set(
        corrections[0]["removed_facts"]
    )
    assert core.publish_optional_fact_corrections(db_session, corrections, INDEX) == {
        "corrected": 1
    }
    db_session.expire_all()
    variant = db_session.get(VehicleVariant, old_variant_id)
    assert variant.published_revision_id != old_revision_id
    catalog = variant.specifications["catalog"]
    assert catalog["source_provenance"]["epa_vehicle_ids"] == ["101", "102"]
    assert not {"fuel_combined", "size_class", "body", "four_door_cargo"} & set(
        catalog["facts"]
    )
    assert db_session.scalar(select(func.count()).select_from(VehicleVariant)) == 1
    assert db_session.scalar(select(func.count()).select_from(CatalogRevision)) == 2
    assert core.publish_optional_fact_corrections(db_session, corrections, INDEX) == {
        "already_safe_on_rerun": 1
    }
    repeat, repeat_summary = core.plan_optional_fact_corrections(
        [[first, second]], INDEX, db_session
    )
    assert repeat == []
    assert repeat_summary["correction_count"] == 0
