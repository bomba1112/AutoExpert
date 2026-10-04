"""CN catalogue load (data_work/cn/staging) into an empty database."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.enums import DisplayLevel, ScopeLevel
from app.models.evidence import KnownIssue, TechnicalEvidence
from app.services import cn_catalog
from app.services.cn_catalog_load import CnLoader, read_staging, validate
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "data_work" / "cn" / "staging"
MODEL_MAP = ROOT / "data_work" / "cn" / "model_map.json"


@pytest.fixture(scope="module")
def staging():
    return read_staging(STAGING, MODEL_MAP)


@pytest.fixture
def loaded(db_session, staging):
    # an existing US Toyota Corolla Cross: the CN records must reuse the make and model
    toyota = VehicleMake(name="Toyota", normalized_name="toyota", is_demo=False)
    db_session.add(toyota)
    db_session.flush()
    cross = VehicleModel(make_id=toyota.id, name="Corolla Cross", normalized_name="corolla cross")
    db_session.add(cross)
    db_session.flush()
    us_generation = VehicleGeneration(model_id=cross.id, name="US", code="UNRESOLVED")
    db_session.add(us_generation)
    db_session.flush()
    report = CnLoader(db_session, staging).load()
    db_session.flush()
    return report, us_generation


def count(db, model, *where):
    return db.scalar(select(func.count()).select_from(model).where(*where))


def test_snapshot_is_valid(staging):
    assert validate(staging) == []
    assert len(staging.records) == staging.manifest["counts"]["configurations"] == 157
    assert len(staging.components) == staging.manifest["counts"]["components"] == 54
    assert len(staging.manifest["samr_commit"]) == 40


def test_load_writes_every_configuration_once(db_session, loaded, staging):
    report, _ = loaded
    assert report.conflicts == []
    assert report.warnings == []
    assert report.counts["variants_new"] == 157
    assert count(db_session, VehicleVariant, VehicleVariant.market == "CN") == 157
    assert (
        count(db_session, TechnicalEvidence, TechnicalEvidence.fact_key == "configuration") == 157
    )
    issues = sum(len(r.get("known_issues") or []) for r in staging.records.values())
    component_issues = sum(len(c.get("known_issues") or []) for c in staging.components.values())
    loaded_issues = count(db_session, KnownIssue, KnownIssue.market == "CN")
    assert loaded_issues == issues + component_issues - report.counts["issues_duplicate_in_staging"]


def test_second_load_changes_nothing(db_session, loaded, staging):
    before = count(db_session, TechnicalEvidence), count(db_session, KnownIssue)
    report = CnLoader(db_session, staging).load()
    db_session.flush()
    assert report.conflicts == []
    assert report.stale == []
    assert report.counts["variants_unchanged"] == 157
    assert not any(k.endswith("_new") for k in report.counts)
    assert (count(db_session, TechnicalEvidence), count(db_session, KnownIssue)) == before


def test_names_follow_turbo_az_and_reuse_existing_toyota(db_session, loaded):
    _, us_generation = loaded
    makes = set(db_session.scalars(select(VehicleMake.name)))
    assert makes == {"Toyota", "BYD", "Changan", "Zeekr", "Lynk & Co"}
    deepal = db_session.scalar(
        select(VehicleVariant)
        .where(VehicleVariant.catalog_key.like("cn:changan_deepal-s07%"))
        .limit(1)
    )
    assert deepal.generation.model.name == "Deepal S07"
    assert deepal.generation.model.make.name == "Changan"
    assert deepal.specifications["cn"]["sub_brand"] == "Deepal"
    cross = db_session.scalars(
        select(VehicleVariant).where(VehicleVariant.catalog_key.like("cn:toyota_corolla-cross%"))
    ).all()
    assert cross and {v.generation.model.name for v in cross} == {"Corolla Cross"}
    assert {v.generation.code for v in cross} == {"CN"}
    assert all(v.generation_id != us_generation.id for v in cross)
    assert count(db_session, VehicleModel, VehicleModel.name == "Corolla Cross") == 1


def test_fingerprint_columns(db_session, loaded, staging):
    for slug, record in staging.records.items():
        variant = db_session.scalar(
            select(VehicleVariant).where(VehicleVariant.catalog_key == f"cn:{slug}")
        )
        battery = (record.get("battery") or {}).get("kwh")
        assert variant.battery_kwh == (
            None if battery is None else Decimal(str(battery)).quantize(Decimal("0.01"))
        )
        assert variant.powertrain_type in {"ICE", "HEV", "PHEV", "EREV", "BEV"}
        assert variant.power_kw is not None, slug
        assert variant.published_revision_id is None
        assert "catalog" not in variant.specifications
    qin = db_session.scalar(
        select(VehicleVariant).where(
            VehicleVariant.catalog_key == "cn:byd_qin-plus-dm-i_2023_18.32kwh-145kw"
        )
    )
    assert (qin.powertrain_type, qin.battery_kwh, qin.power_kw) == (
        "PHEV",
        Decimal("18.32"),
        Decimal("145.00"),
    )
    lynk = db_session.scalar(
        select(VehicleVariant).where(VehicleVariant.catalog_key == "cn:lynk-co_900_2026_1.5t-phev")
    )
    assert lynk.specifications["cn"]["power_basis"] == "engine_plus_motors"


def test_listing_values_never_become_facts(db_session, loaded):
    qin = db_session.scalar(
        select(VehicleVariant).where(VehicleVariant.catalog_key == "cn:byd_qin-plus_2025_dm-i-55km")
    )
    listing = qin.specifications["cn"]["listing"]
    assert listing["listing_values"]["hp"] == 197
    assert qin.specifications["cn"]["verification"] == "mismatch"
    facts = db_session.scalars(
        select(TechnicalEvidence).where(
            TechnicalEvidence.configuration_key == "cn:byd_qin-plus_2025_dm-i-55km"
        )
    ).all()
    assert all("turbo.az" not in str(f.value) for f in facts)
    assert {f.value for f in facts if f.fact_key == "motor_power_kw"} == {120}


def test_display_level_by_source_host(db_session, loaded):
    facts = db_session.scalars(
        select(TechnicalEvidence).where(TechnicalEvidence.market == "CN")
    ).all()
    for fact in facts:
        host = fact.source.url
        if "auto.sohu.com" in host:
            assert fact.display_level == DisplayLevel.FACT, (fact.fact_key, host)
        elif fact.fact_key != "configuration":
            assert fact.display_level == DisplayLevel.SECONDARY_NOTE, (fact.fact_key, host)
    ranges = [
        f
        for f in facts
        if f.fact_key == "ev_range_km" and f.configuration_key == "cn:byd_qin-plus_2025_dm-i-55km"
    ]
    assert {(f.conditions["cycle"], f.value, f.display_level) for f in ranges} == {
        ("WLTC", 43, DisplayLevel.SECONDARY_NOTE),
        ("CLTC", 55, DisplayLevel.SECONDARY_NOTE),
    }


def test_owner_reports_have_no_severity_and_component_scope(db_session, loaded):
    issues = db_session.scalars(select(KnownIssue).where(KnownIssue.market == "CN")).all()
    assert issues
    assert all(i.severity is None for i in issues)
    assert all(i.display_level == DisplayLevel.OWNER_REPORTS for i in issues)
    hybrid = [i for i in issues if i.scope_level == ScopeLevel.HYBRID_SYSTEM]
    assert hybrid and all(i.hybrid_system_key and i.vehicle_variant_id is None for i in hybrid)
    own = [i for i in issues if i.scope_level == ScopeLevel.CONFIGURATION]
    assert all(i.vehicle_variant_id and not i.engine_family_key for i in own)


def test_resolved_issues_equal_the_catalogue(db_session, loaded, staging):
    """known_issues_resolved is not stored: joined at read time, identical to the JSON."""

    def projection(items):
        return [
            (
                i["text"],
                i["source"],
                i["scope"],
                i["origin"],
                i.get("component"),
                tuple(i.get("more_sources") or ()),
                i.get("review_car") if not i.get("component") else None,
                i.get("scope_note") if not i.get("component") else None,
            )
            for i in items
        ]

    for slug, record in staging.records.items():
        variant = db_session.scalar(
            select(VehicleVariant).where(VehicleVariant.catalog_key == f"cn:{slug}")
        )
        expected = projection(record.get("known_issues_resolved") or [])
        assert projection(cn_catalog.resolved_issues(db_session, variant)) == expected, slug


def test_replace_own_reloads_only_cn_rows(db_session, loaded, staging):
    us = VehicleVariant(
        generation_id=loaded[1].id, market="US", name="US Corolla Cross", specifications={}
    )
    db_session.add(us)
    db_session.flush()
    report = CnLoader(db_session, staging).load(replace_own=True)
    db_session.flush()
    assert report.counts["removed_vehicle_variants"] == 157
    assert report.counts["variants_new"] == 157
    assert db_session.get(VehicleVariant, us.id) is not None
