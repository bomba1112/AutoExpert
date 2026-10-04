"""turbo.az listing -> CN catalogue configuration (battery first, power ±3 %, year ±1)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.core.config import get_settings
from app.services import cn_listing_match as cm
from app.services import listing_intake as intake
from app.services.cn_catalog_load import CnLoader, read_staging
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = ROOT / "data_work/cn/staging"
STAGING = read_staging(STAGING_DIR, ROOT / "data_work/cn/model_map.json")
BASE = "/api/v1/listings/intake"


@pytest.fixture
def cn_db(db_session):
    CnLoader(db_session, STAGING).load()
    db_session.commit()
    return db_session


@pytest.fixture
def flag():
    settings = get_settings()
    original = settings.cn_listing_match
    settings.cn_listing_match = True
    yield settings
    settings.cn_listing_match = original


def facts(make, model, year, engine, fuel=None, drive=None):
    claims = {
        name: intake._claim(name, value, f"test:{name}", 0.9)
        for name, value in (
            ("make", make),
            ("model", model),
            ("year", year),
            ("engine", engine),
            ("fuel", fuel),
            ("drivetrain", drive),
        )
        if value is not None
    }
    return cm.facts_from_claims(claims)


def test_engine_line_parsing():
    parsed = cm.parse_engine("1.5 L / 7.68 kWh / 197 a.g. / Plug-in Hibrid")
    assert parsed == {
        "displacement_l": Decimal("1.5"),
        "battery_kwh": Decimal("7.68"),
        "power_hp": Decimal("197"),
        "powertrain": "PHEV",
    }
    assert cm.parse_engine("69 kWh / 272 a.g. / Elektro") == {
        "battery_kwh": Decimal("69"),
        "power_hp": Decimal("272"),
        "powertrain": "BEV",
    }
    assert cm.parse_engine("1.5 L / 192 a.g. / Benzin")["powertrain"] == "ICE"


def test_tolerances():
    assert cm.battery_fits(Decimal("18.3"), Decimal("18.32"))
    assert cm.battery_fits(Decimal("15.9"), Decimal("15.87"))
    assert not cm.battery_fits(Decimal("18.6"), Decimal("18.32"))
    assert cm.battery_fits(Decimal("102"), Decimal("103"))  # 1 % of a large pack
    assert cm.power_fit(Decimal("197"), {"motors": Decimal("145")}) == "motors"
    assert cm.power_fit(Decimal("185"), {"engine": Decimal("141")}) is None  # 3.5 %
    assert cm.power_fit(Decimal("721"), {"engine_plus_motors": Decimal("530")})


def test_battery_decides_and_power_mismatch_is_reported(cn_db):
    result = cm.match(
        facts("BYD", "Qin Plus", 2025, "1.5 L / 7.68 kWh / 197 a.g. / Plug-in Hibrid"),
        cm.candidates(cn_db),
    )
    assert result["status"] == "EXACT_MATCH"
    assert result["candidates"][0]["configuration_key"] == "cn:byd_qin-plus_2025_dm-i-55km"
    assert result["conflicts"] == [
        {"field_name": "power", "claimed": "197 a.g.", "catalog_values": ["163 a.g. (120 kW)"]}
    ]


def test_unknown_battery_is_a_conflict(cn_db):
    result = cm.match(
        facts("BYD", "Qin Plus", 2025, "1.5 L / 12.0 kWh / 197 a.g. / Plug-in Hibrid"),
        cm.candidates(cn_db),
    )
    assert result["status"] == "CLAIM_CONFLICT"
    assert result["conflicts"][0]["field_name"] == "battery_kwh"


def test_year_window_and_ranking(cn_db):
    rows = cm.candidates(cn_db)
    # listed 2024: 2023, 2024 and 2025 年款 are possible, the 2024 one ranks first
    result = cm.match(
        facts("BYD", "Qin Plus", 2024, "1.5 L / 18.32 kWh / 197 a.g. / Plug-in Hibrid"), rows
    )
    keys = [c["configuration_key"] for c in result["candidates"]]
    assert result["status"] == "MULTIPLE_CANDIDATES"
    assert keys[0] == "cn:byd_qin-plus-dm-i_2024_18.32kwh-145kw"
    assert result["candidates"][0]["primary"] is True
    assert {"cn:byd_qin-plus-dm-i_2023_18.32kwh-145kw"} <= set(keys)
    assert all(abs(c["year"] - 2024) <= 1 for c in result["candidates"])
    # a seller year three years off: a year conflict naming the configuration, not "no match"
    far = cm.match(
        facts("Changan", "Qiyuan A06", 2023, "1.5 L / 28.39 kWh / 163 a.g. / Plug-in Hibrid"), rows
    )
    assert far["status"] == "CLAIM_CONFLICT"
    assert far["conflicts"][0] == {
        "field_name": "year",
        "claimed": "2023",
        "catalog_values": ["2026"],
    }


def test_aliases_and_exact_name_first(cn_db):
    rows = cm.candidates(cn_db)
    deepal = cm.match(
        facts("Deepal", "S07", 2025, "1.5 L / 31.73 kWh / 238 a.g. / Plug-in Hibrid"), rows
    )
    assert deepal["candidates"][0]["configuration_key"] == "cn:changan_deepal-s07_2025_erev-215"
    pro = cm.match(facts("Changan", "CS 75 Pro", 2025, "1.5 L / 192 a.g. / Benzin"), rows)
    assert pro["candidates"][0]["configuration_key"] == "cn:changan_cs75-pro_2025_1.5t-dct"
    zeekr = cm.match(facts("ZEEKR", "X", 2026, "69 kWh / 272 a.g. / Elektro"), rows)
    assert zeekr["status"] == "EXACT_MATCH"


def test_regression_on_the_catalogue_listings(cn_db):
    report = cm.regression(cn_db, STAGING_DIR / "listings/turbo_specs.json", STAGING_DIR)
    assert report["listings"] == 28
    assert report["summary"] == {"primary": 25, "candidate": 1, "closest_official_alternative": 2}
    by_outcome = {}
    for r in report["results"]:
        by_outcome.setdefault(r["outcome"], []).append(r)
    assert [r["status"] for r in by_outcome["candidate"]] == ["CLAIM_CONFLICT"]  # Qiyuan A06 2023
    for r in by_outcome["closest_official_alternative"]:
        # CS 75 Plus "185 a.g.": by the ±3 % rule only 2025 JL473ZQ7 (188 PS) fits; the
        # catalogue linked 2026 (192 PS) and names the 2025 version as the closest official one
        assert r["primary"] == "cn:changan_cs75-plus_2025_jl473zq7-8at"
        assert r["expected"] == ["cn:changan_cs75-plus_2026_1.5t-8at"]


def auth(client: TestClient) -> dict:
    response = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def manual(client, fields):
    return client.post(
        BASE,
        headers=auth(client),
        json={"input_type": "MANUAL", "language": "ru", "fields": fields},
    )


QIN_FIELDS = {
    "make": "BYD",
    "model": "Qin Plus",
    "year": 2025,
    "engine": "1.5 L / 7.68 kWh / 197 a.g. / Plug-in Hibrid",
    "fuel": "Plug-in Hibrid",
}


def test_listing_intake_uses_the_cn_catalogue(client, cn_db, flag, monkeypatch):
    monkeypatch.setattr(intake, "_consumer_rows", lambda db: [])
    body = manual(client, QIN_FIELDS).json()
    assert body["match"]["status"] == "EXACT_MATCH"
    candidate = body["match"]["candidates"][0]
    assert candidate["configuration_key"] == "cn:byd_qin-plus_2025_dm-i-55km"
    assert candidate["market"] == "CN" and candidate["battery_kwh"] == 7.68
    assert body["match"]["conflicts"][0]["field_name"] == "power"
    claims = {c["field_name"]: c for c in body["claims"]}
    assert claims["battery_kwh"]["normalized_value"] == 7.68
    assert claims["power_hp"]["normalized_value"] == 197


def test_listing_intake_without_the_flag_is_unchanged(client, cn_db, flag, monkeypatch):
    monkeypatch.setattr(intake, "_consumer_rows", lambda db: [])
    flag.cn_listing_match = False
    body = manual(client, QIN_FIELDS).json()
    assert body["match"]["status"] == "OUT_OF_PRODUCT_SCOPE"
    assert "battery_kwh" not in {c["field_name"] for c in body["claims"]}


def test_us_makes_never_reach_the_cn_matcher(cn_db, flag, monkeypatch):
    calls = []
    monkeypatch.setattr(cm, "candidates", lambda db: calls.append(1) or [])
    claims = {
        "make": SimpleNamespace(raw_value="Hyundai", normalized_value="Hyundai"),
        "model": SimpleNamespace(raw_value="Elantra", normalized_value="Elantra"),
    }
    us = {"status": "EXACT_MATCH", "candidates": [], "question": None, "conflicts": []}
    assert cm.try_match(cn_db, claims, "ru", us_result=us) is None
    assert calls == []


def test_shared_make_keeps_the_us_answer(cn_db, flag):
    claims = {
        name: intake._claim(name, value, "t", 0.9)
        for name, value in (
            ("make", "Toyota"),
            ("model", "Corolla Cross"),
            ("year", 2026),
            ("engine", "2.0 L / 197 a.g. / Hibrid"),
        )
    }
    us = {"status": "EXACT_MATCH", "candidates": [{}], "question": None, "conflicts": []}
    assert cm.try_match(cn_db, claims, "ru", us_result=us) is None
    us_none = {"status": "NO_MATCH", "candidates": [], "question": None, "conflicts": []}
    cn = cm.try_match(cn_db, claims, "ru", us_result=us_none)
    assert cn["candidates"][0]["configuration_key"] == "cn:toyota_corolla-cross_2026_2.0-hev"
    claims["market"] = intake._claim("market", "Çin", "t", 0.9)
    assert cm.try_match(cn_db, claims, "ru", us_result=us) is not None
