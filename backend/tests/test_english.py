"""English, the third language (product phase, stage 1): no untranslated server text in English,
US units with the metric value in brackets, the manufacturer's octane as printed, and the APIs
accepting en."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest
from app.core.english import english, pick, table
from app.services import catalog_buyer as buyer
from app.services import fuel_advice, unit_display
from app.services import us_tech_facts

APP = Path(__file__).resolve().parents[1] / "app"
CYR = re.compile(r"[А-Яа-яЁё]")
MODULES = ["services/catalog_buyer.py", "services/us_tech_facts.py", "services/fuel_advice.py", "services/buyer_experience.py",
           "services/history_flow.py", "services/listing_intake.py", "services/ownership_cost.py", "services/vehicle_identity.py",
           "services/nrcan_catalog.py", "api/routes/knowledge.py", "api/routes/buyer.py", "api/routes/vin.py", "api/routes/catalog.py",
           "core/abbreviations.py", "providers/listings.py", "services/chat_context.py", "services/report_pdf.py", "api/routes/chat.py"]


def russian_constants():
    for rel in MODULES:
        tree = ast.parse((APP / rel).read_text(encoding="utf-8"))
        inside_f = {id(v) for node in ast.walk(tree) if isinstance(node, ast.JoinedStr) for v in node.values}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and CYR.search(node.value) and id(node) not in inside_f:
                yield rel, node.lineno, node.value


def walk_text(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            if k not in ("source", "original", "quote", "locator", "source_url"):
                yield from walk_text(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from walk_text(v)


def test_every_russian_server_text_has_english():
    missing = [f"{rel}:{line}: {text[:60]!r}" for rel, line, text in russian_constants() if text not in table()]
    assert not missing, missing[:20]
    assert not any(CYR.search(v) for v in table().values())


def test_pick_and_fallback():
    assert pick("ru", "Двигатель", "Mühərrik") == "Двигатель"
    assert pick("az", "Двигатель", "Mühərrik") == "Mühərrik"
    assert pick("en", "Двигатель", "Mühərrik") == english("Двигатель") and not CYR.search(english("Двигатель"))
    assert pick("en", "Двигатель", "Mühərrik", "Engine block") == "Engine block"


@pytest.mark.parametrize(("value", "unit", "key", "expected"), [
    (4702, "mm", "length_mm", "185.1 in (4,702 mm)"), (55, "L", "fuel_tank_l", "14.5 gal (55 L)"),
    (5.5, "L", "engine_oil_capacity_l", "5.8 qt (5.5 L)"), (250, "kPa", "tire_pressure_front_kpa", "36 psi (250 kPa)"),
    (1470, "kg", "curb_weight_kg", "3,241 lb (1,470 kg)"), (7.4, "L/100km", "fuel_combined", "32 mpg (7.4 L/100km)"),
    (90, "°C", "coolant_temperature", "194 °F (90 °C)")])
def test_us_units_with_metric_in_brackets(value, unit, key, expected):
    assert unit_display.show(value, unit, "en", key) == expected
    assert unit_display.show(value, unit, "ru", key) is None and unit_display.show(value, unit, "az", key) is None


def test_maintenance_distance_by_language():
    assert unit_display.distance(24140, 15000, "en") == "15,000 mi (24,140 km)"
    assert unit_display.distance(24000, None, "en") == "14,913 mi (24,000 km)"
    assert unit_display.distance(24000, None, "ru") == "24,000 km"
    assert us_tech_facts._interval(16000, 12, "WHICHEVER_FIRST", "en", 10000) == "10,000 mi (16,000 km) or 1 year, whichever comes first"


def test_fuel_in_english_is_the_manufacturer_octane_as_printed():
    facts = {"fuel": {"value": "GASOLINE", "status": "CONFIRMED", "locator": "EPA vehicle 1: fuelType1"},
             "aspiration": {"value": "TURBO", "status": "CONFIRMED", "locator": "EPA vehicle 1: tCharger"}}
    lines = fuel_advice.rows(fuel_advice.traits_from_facts(facts, [], [91]), "en")
    assert [x["value"] for x in lines] == ["AKI 91 (US pump octane)"] and lines[0]["kind"] == "manufacturer"
    assert fuel_advice.rows(fuel_advice.traits_from_facts(facts, [], []), "en") == []  # no AI recommendation in English
    ru = fuel_advice.rows(fuel_advice.traits_from_facts(facts, [], [91]), "ru")
    assert any(x["kind"] == "recommendation" for x in ru)


def test_vehicle_profile_in_english_has_no_russian():
    epa = lambda v, f="fuelType1": {"value": v, "status": "CONFIRMED", "locator": f"EPA vehicle 1: {f}"}  # noqa: E731
    catalog = {"facts": {"fuel": epa("GASOLINE"), "powertrain": epa("ICE", "atvType"), "aspiration": epa("TURBO", "tCharger"),
                         "drivetrain": epa("FWD", "drive"), "transmission_family": epa("AT", "trany"),
                         "length_mm": {"value": 4702, "unit": "mm", "status": "CONFIRMED"},
                         "octane_aki": {"value": 91, "status": "CONFIRMED"}},
               "source_url": "https://www.fueleconomy.gov/", "original_market": "US", "model_year": 2020}
    profile = buyer.vehicle_profile(catalog, "en")
    russian = [t for t in walk_text(profile) if CYR.search(t)]
    assert not russian, russian[:10]
    rows = {r["key"]: r for g in profile["technical"] for r in g["rows"]}
    assert rows["length_mm"]["value"] == "185.1 in (4,702 mm)"
    assert rows["fuel_octane_maker"]["value"] == "AKI 91 (US pump octane)" and "fuel_recommendation" not in rows


def test_us_tech_panel_in_english_has_no_russian(db_session):
    from tests.test_us_tech_facts import ICE, configuration, fact

    from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel
    from app.models.evidence import SourceRecord
    from datetime import UTC, datetime

    us_tech_facts.clear_cache()
    make = VehicleMake(name="Toyota", normalized_name="toyota")
    model = VehicleModel(make=make, name="Camry", normalized_name="camry")
    gen = VehicleGeneration(model=model, name="VIII", code="XV70", start_year=2018, end_year=2024)
    source = SourceRecord(title="2020 Camry Owner's Manual", publisher="Toyota", url="https://example.test/om.pdf",
                          source_type="OWNER_MANUAL", retrieved_at=datetime(2026, 1, 1, tzinfo=UTC), confidence="HIGH")
    db_session.add_all([make, model, gen, source])
    db_session.flush()
    g = {"make": make, "gen": gen, "source": source, "db": db_session}
    configuration(g, ICE, "ICE", "A25A-FKS", "Automatic (S8)", ["Camry LE/SE"])
    fact(g, "fuel_tank_l", 60.6, unit="L")
    fact(g, "tire_pressure_front_kpa", 240, unit="kPa")
    fact(g, "engine_oil_capacity_l", 4.5, level="ENGINE", engine="A25A-FKS", unit="L")
    fact(g, "octane_aki", 87)
    db_session.commit()
    data = us_tech_facts.build(db_session, ICE, "en")
    russian = [t for t in walk_text(data) if CYR.search(t)]
    assert not russian, russian[:10]
    rows = {r["key"]: r for c in data["categories"] for r in c["rows"]}
    assert rows["fuel_tank_l"]["values"][0]["value"] == "16 gal (60.6 L)"
    assert rows["tire_pressure_front_kpa"]["values"][0]["value"] == "35 psi (240 kPa)"
    assert rows["engine_oil_capacity_l"]["values"][0]["value"] == "4.8 qt (4.5 L)"
    assert rows["octane_aki"]["values"][0]["value"] == "AKI 87 (US pump octane)"
    us_tech_facts.clear_cache()


def test_apis_accept_english(client):
    assert client.get("/api/v1/meta/client-config").status_code == 200
    assert client.get("/api/v1/catalog/us-tech/configurations", params={"language": "en"}).status_code != 422
    response = client.post("/api/v1/knowledge/search?language=en", json={})
    assert response.status_code != 422


def test_translations_have_english_text():
    path = Path(__file__).resolve().parents[2] / "data_work" / "_shared" / "i18n" / "translations.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert rows and all(r.get("en") and not CYR.search(r["en"]) for r in rows)
    upper = [r for r in rows if r["kind"] == "recall_component" and r["en"].isupper()]
    assert not upper  # NHTSA component paths are shown in sentence case
