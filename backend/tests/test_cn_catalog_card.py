"""CN configuration card, routes behind show_cn_catalog, isolation from the US technical card."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.core.config import get_settings
from app.models.catalog import VehicleMake, VehicleVariant
from app.models.enums import (
    ConfidenceLevel,
    DisplayLevel,
    EvidenceCategory,
    EvidenceStatus,
    ScopeLevel,
    SourceTier,
)
from app.models.evidence import SourceRecord, TechnicalEvidence
from app.services import cn_catalog, us_tech_facts
from app.services.cn_catalog_load import CnLoader, read_staging
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[2]
STAGING = read_staging(ROOT / "data_work/cn/staging", ROOT / "data_work/cn/model_map.json")
QIN = "cn:byd_qin-plus-dm-i_2023_18.32kwh-145kw"


@pytest.fixture
def cn_db(db_session):
    CnLoader(db_session, STAGING).load()
    db_session.commit()
    return db_session


def rows_of(card: dict) -> dict:
    return {row["key"]: row for category in card["categories"] for row in category["rows"]}


def test_card_shows_battery_power_and_sources(cn_db):
    card = cn_catalog.build(cn_db, QIN, "ru")
    assert card["title"] == "BYD Qin Plus 2023"
    assert card["powertrain_type"] == "PHEV" and card["battery_kwh"] == 18.32
    rows = rows_of(card)
    assert rows["battery_kwh"]["values"][0]["value"] == "18.32 кВт·ч"
    assert rows["motor_power_kw"]["values"][0]["value"] == "145 кВт (197 л.с.)"
    assert rows["engine_power_kw"]["values"][0]["value"] == "81 кВт (110 л.с.)"
    assert rows["ev_range_km"]["values"][0]["qualifier"] == "MIIT"
    assert rows["powertrain"]["values"][0]["value"] == "Подключаемый гибрид (PHEV)"
    for row in rows.values():
        for value in row["values"]:
            assert "sohu" in value["source"]["url"] and value["secondary"] is False
    assert {(c["kind"], c["key"]) for c in card["components"]} == {
        ("engine", "byd_472zqa_1.5"),
        ("transmission", "byd_ehs_ecvt_dmi4"),
        ("hybrid_system", "byd_dmi_4.0"),
    }
    dmi = next(c for c in card["components"] if c["kind"] == "hybrid_system")
    assert dmi["name"].startswith("BYD DM-i") and dmi["secondary"] is True  # ithome / Wikipedia


def test_card_owner_reports_inherited_and_without_severity(cn_db):
    card = cn_catalog.build(cn_db, QIN, "ru")
    assert card["weak_points"], "Qin Plus 2023 inherits the DM-i 4.0 report"
    inherited = [w for w in card["weak_points"] if w["inherited"]]
    assert inherited and inherited[0]["origin"].startswith("гибридная система")
    assert all(
        w["owner_reports"] and w["note"] == "владельцы сообщают" for w in card["weak_points"]
    )
    assert "severity" not in json.dumps(card)


def test_card_languages(cn_db):
    az = cn_catalog.build(cn_db, QIN, "az")
    en = cn_catalog.build(cn_db, QIN, "en")
    assert rows_of(az)["battery_kwh"]["label"] == "Dartı batareyasının tutumu"
    assert rows_of(az)["motor_power_kw"]["values"][0]["value"] == "145 kVt (197 a.g.)"
    assert rows_of(en)["battery_kwh"]["values"][0]["value"] == "18.32 kWh"
    assert {c["title"] for c in en["categories"]} >= {"Battery and range", "Electric motors"}
    assert all(w["original_language"] == "ru" for w in en["weak_points"])


def test_bev_card_has_no_engine_and_secondary_is_marked(cn_db):
    key = cn_db.scalar(
        select(VehicleVariant.catalog_key).where(VehicleVariant.catalog_key.like("cn:zeekr_001%"))
    )
    card = cn_catalog.build(cn_db, key, "ru")
    assert "engine" not in {c["key"] for c in card["categories"]}
    assert card["powertrain_type"] == "BEV"
    qin55 = cn_catalog.build(cn_db, "cn:byd_qin-plus_2025_dm-i-55km", "ru")
    ranges = rows_of(qin55)["ev_range_km"]["values"]
    assert {v["qualifier"] for v in ranges} == {"CLTC", "WLTC"}
    assert all(v["secondary"] for v in ranges)  # xchuxing -> SECONDARY_NOTE


def test_listing_copy_notice(cn_db):
    card = cn_catalog.build(cn_db, "cn:changan_qiyuan-a06r_2025_erev-240", "ru")
    assert card["notices"] and card["notices"][0]["copy_of"] == "changan_qiyuan-a06_2026_erev-240"


def test_facets_and_configurations(cn_db):
    facets = cn_catalog.facets(cn_db)
    assert {"make": "Changan", "model": "Deepal S07", "years": [2023, 2024, 2025, 2026]} in facets
    listed = cn_catalog.configurations(cn_db, "BYD", "Qin Plus", 2023)
    assert [c["configuration_key"] for c in listed] == [
        "cn:byd_qin-plus-dm-i_2023_18.32kwh-145kw",
        "cn:byd_qin-plus-dm-i_2023_8.32kwh-132kw",
    ]


def test_us_technical_card_never_shows_cn_configurations(cn_db):
    toyota = cn_db.scalar(select(VehicleMake).where(VehicleMake.name == "Toyota"))
    cross = cn_db.scalar(
        select(VehicleVariant).where(VehicleVariant.catalog_key.like("cn:toyota_corolla-cross%"))
    )
    source = SourceRecord(
        title="EPA",
        publisher="EPA",
        url="https://fueleconomy.gov",
        source_type="EPA",
        source_tier=SourceTier.A,
        retrieved_at=cross.created_at,
        confidence=ConfidenceLevel.HIGH,
    )
    cn_db.add(source)
    cn_db.flush()
    # a US configuration of the same make/model without market (as the US fixtures write it)
    us_generation = cross.generation.model.generations
    cn_db.add(
        TechnicalEvidence(
            source_id=source.id,
            category=EvidenceCategory.OTHER,
            title="configuration",
            statement="us",
            status=EvidenceStatus.CONFIRMED,
            confidence=ConfidenceLevel.HIGH,
            fact_key="configuration",
            value="toyota-corolla-cross-2023-us",
            configuration_key="toyota-corolla-cross-2023-us",
            scope_level=ScopeLevel.CONFIGURATION,
            display_level=DisplayLevel.FACT,
            make_id=toyota.id,
            generation_id=us_generation[0].id,
            year_from=2023,
            year_to=2023,
            conditions={"identity": {}},
        )
    )
    cn_db.flush()
    keys = [
        c["configuration_key"] for c in us_tech_facts.configurations(cn_db, "Toyota", None, None)
    ]
    assert keys == ["toyota-corolla-cross-2023-us"]
    facets = us_tech_facts.facets(cn_db)
    assert {f["make"] for f in facets} == {"Toyota"}
    assert us_tech_facts.build(cn_db, QIN, "ru") is None
    assert us_tech_facts.configuration_for_variant(cn_db, cross.id) is not None  # its CN key
    assert (
        us_tech_facts.build(cn_db, us_tech_facts.configuration_for_variant(cn_db, cross.id)) is None
    )


def test_routes_follow_the_flag(client, cn_db):
    settings = get_settings()
    original = settings.show_cn_catalog
    try:
        settings.show_cn_catalog = True
        response = client.get(f"/api/v1/catalog/cn/configurations/{QIN}", params={"language": "az"})
        assert response.status_code == 200
        assert response.json()["configuration_key"] == QIN
        assert client.get("/api/v1/catalog/cn/configurations/cn:none").status_code == 404
        assert client.get("/api/v1/catalog/cn/facets").status_code == 200
        settings.show_cn_catalog = False
        assert client.get(f"/api/v1/catalog/cn/configurations/{QIN}").status_code == 404
        assert client.get("/api/v1/catalog/cn/facets").status_code == 404
    finally:
        settings.show_cn_catalog = original


def test_flag_default_is_off_in_production():
    settings = get_settings().model_copy(
        update={"show_cn_catalog": None, "environment": "production"}
    )
    assert cn_catalog.enabled(settings) is False
    preview = settings.model_copy(update={"environment": "development"})
    assert cn_catalog.enabled(preview) is True
