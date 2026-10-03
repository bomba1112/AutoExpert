# ruff: noqa: E501
"""US technical facts in the configuration card (next-stage prompt, stage C).

A small synthetic generation with two configurations (2.5 ICE FWD and 2.5 hybrid) checks the
assembly rules: level precedence, powertrain / engine / year filters, HIDDEN_CONFLICT and empty
values never shown, OWNER_REPORTS only among weak points, maintenance jobs matched to the
gearbox, and the show_us_tech_facts flag (off in production: routes answer 404 and the client
configuration is unchanged).
"""

from __future__ import annotations

from datetime import UTC, datetime
from itertools import count

import pytest
from app.core.config import get_settings
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel
from app.models.enums import EvidenceCategory
from app.models.evidence import KnownIssue, MaintenanceScheduleItem, SourceRecord, TechnicalEvidence
from app.services import us_tech_facts

ICE = "toyota-camry-us-2020-2.5l-4cyl-ice-a-s8-fwd"
HEV = "toyota-camry-us-2020-2.5l-4cyl-hev-a-av-s6-fwd"
_keys = count()


@pytest.fixture(autouse=True)
def fresh_cache():
    us_tech_facts.clear_cache()
    settings = get_settings()
    original = settings.show_us_tech_facts, settings.environment
    yield
    settings.show_us_tech_facts, settings.environment = original
    us_tech_facts.clear_cache()


@pytest.fixture
def generation(db_session):
    make = VehicleMake(name="Toyota", normalized_name="toyota")
    model = VehicleModel(make=make, name="Camry", normalized_name="camry")
    gen = VehicleGeneration(model=model, name="VIII", code="XV70", start_year=2018, end_year=2024)
    source = SourceRecord(title="2020 Camry Owner's Manual", publisher="Toyota", url="https://example.test/om.pdf",
                          source_type="OWNER_MANUAL", retrieved_at=datetime(2026, 1, 1, tzinfo=UTC), confidence="HIGH")
    db_session.add_all([make, model, gen, source])
    db_session.flush()
    return {"make": make, "gen": gen, "source": source, "db": db_session}


def fact(g, key, value, *, level="GENERATION", display="FACT", unit=None, years=(2018, 2024), config=None, engine=None,
         app=None, extra=None):
    row = TechnicalEvidence(
        source_id=g["source"].id, category=EvidenceCategory.ENGINE, title=key, statement=str(value), status="CONFIRMED", confidence="HIGH",
        scope_level=level, display_level=display, make_id=g["make"].id, generation_id=g["gen"].id, year_from=years[0],
        year_to=years[1], configuration_key=config, engine_family_key=engine, fact_key=key, value=value, unit=unit,
        locator="page 541", natural_key=f"k{next(_keys)}",
        conditions={"applicability": app or {}, "cites": [{"source": "om-2020", "pages": [541], "quote": f"q {key}"}], **(extra or {})})
    g["db"].add(row)
    return row


def configuration(g, key, powertrain, engine, transmission, labels):
    fact(g, "configuration", key, level="CONFIGURATION", config=key, engine=engine, years=(2020, 2020),
         extra={"identity": {"powertrain": powertrain, "drivetrain": "FWD", "engine_family_key": engine, "displacement_l": "2.5",
                             "cylinders": 4, "epa_transmission": transmission, "aspiration": "NATURALLY_ASPIRATED"}, "line": "Camry"})
    fact(g, "powertrain", powertrain, level="CONFIGURATION", config=key, engine=engine, years=(2020, 2020))
    for i, label in enumerate(labels):
        fact(g, "epa_combined_mpg", 32 + i, level="CONFIGURATION", config=key, engine=engine, unit="mpg", years=(2020, 2020),
             extra={"epa_model": label})
        fact(g, "fuel_combined", 7.4 - i / 10, level="CONFIGURATION", config=key, engine=engine, unit="L/100km", years=(2020, 2020),
             extra={"epa_model": label})


@pytest.fixture
def camry(generation):
    g = generation
    configuration(g, ICE, "ICE", "A25A-FKS", "Automatic (S8)", ["Camry LE/SE"])
    configuration(g, HEV, "HEV", "A25A-FXS", "Automatic (AV-S6)", ["Camry Hybrid LE"])
    # level precedence: the engine-family value wins over a generation value of the same field
    fact(g, "power_hp", 200, unit="hp")
    fact(g, "power_hp", 203, level="ENGINE", engine="A25A-FKS", unit="hp", app={"rpm": 6600})
    fact(g, "power_hp", 176, level="ENGINE", engine="A25A-FXS", unit="hp")
    fact(g, "engine_oil_capacity_l", 4.5, level="ENGINE", engine="A25A-FKS", unit="L")
    fact(g, "engine_oil_viscosity", "SAE 0W-16", level="ENGINE", engine="A25A-FKS", display="SECONDARY_NOTE")
    fact(g, "engine_oil_capacity_l", 5.4, level="ENGINE", engine="2GR-FKS", unit="L")
    # powertrain filter and a hidden conflict on the same field
    fact(g, "fuel_tank_l", 60.6, unit="L", app={"powertrain": "ICE"})
    fact(g, "fuel_tank_l", 59.8, unit="L", app={"powertrain": "ICE"}, display="HIDDEN_CONFLICT")
    fact(g, "fuel_tank_l", 50, unit="L", app={"powertrain": "HEV"})
    # year filter and empty values
    fact(g, "ground_clearance", 150, unit="mm", years=(2018, 2019))
    fact(g, "front_brakes", "")
    fact(g, "rear_brakes", None)
    # trims stated by the source become version labels
    fact(g, "curb_weight_kg", 1470, unit="kg", app={"trims": ["L"], "powertrain": "ICE", "engine": "A25A-FKS"})
    fact(g, "curb_weight_kg", 1495, unit="kg", app={"trims": ["LE"], "powertrain": "ICE", "engine": "A25A-FKS"})
    fact(g, "curb_weight_kg", 1430, unit="kg", app={"trims": ["TRD"], "powertrain": "ICE"})
    # a recall
    fact(g, "nhtsa_recall", "20V682000", years=(2018, 2020),
         extra={"campaign_number": "20V682000", "component": "FUEL PUMP", "summary": "The fuel pump may fail.", "model_years": [2018, 2019, 2020]})
    fact(g, "nhtsa_recall", "17V000000", years=(2018, 2018),
         extra={"campaign_number": "17V000000", "component": "OTHER", "summary": "Other year.", "model_years": [2018]})

    def issue(title, display, engines=(), powertrain=None, severity="HIGH"):
        g["db"].add(KnownIssue(
            component="engine", title=title, description=title, symptoms=["stall"], severity=severity, confidence="HIGH",
            inspection_recommendation="Check by VIN.", status="CONFIRMED", scope_level="GENERATION", display_level=display,
            make_id=g["make"].id, generation_id=g["gen"].id, year_from=2018, year_to=2022, natural_key=f"i{next(_keys)}",
            probability="OCCASIONAL", affected_variants={"engines": list(engines), "powertrain": powertrain}))

    issue("Fuel pump failure", "FACT")
    issue("Owners report a rattle", "OWNER_REPORTS", severity="MEDIUM")
    issue("Disputed issue", "HIDDEN_CONFLICT")
    issue("V6 only issue", "FACT", engines=["2GR-FKS"])
    issue("Hybrid inverter coolant pump", "FACT")

    def job(name, action, km, months, display="FACT", app=None, condition="NORMAL"):
        g["db"].add(MaintenanceScheduleItem(
            market="US", make_id=g["make"].id, generation_id=g["gen"].id, year_from=2018, year_to=2022, applicability=app or {},
            schedule_system="FIXED_INTERVAL", job=name, action=action, condition=condition, occurrence="EVERY", interval_km=km,
            interval_months=months, rule="WHICHEVER_FIRST" if km and months else None, source_id=g["source"].id,
            locator="page 600", confidence="HIGH", status="CONFIRMED", display_level=display, natural_key=f"m{next(_keys)}",
            notes="quote: Replace engine oil"))

    job("engine_oil_and_filter", "REPLACE", 16000, 12)
    job("dct_fluid", "REPLACE", 120000, None)
    job("cabin_air_filter", "REPLACE", 24000, None, display="SECONDARY_NOTE", app={"approx_in_source": True})
    job("spark_plugs", "REPLACE", 96000, None, display="HIDDEN_CONFLICT")
    g["db"].commit()
    return g


def rows_of(data):
    return {r["key"]: r for c in data["categories"] for r in c["rows"]}


def test_most_specific_level_and_engine_family_win(camry):
    data = us_tech_facts.build(camry["db"], ICE, "ru")
    rows = rows_of(data)
    assert [v["value"] for v in rows["power_hp"]["values"]] == ["203 hp (151.4 кВт) при 6600 об/мин"]
    assert [v["value"] for v in rows["engine_oil_capacity_l"]["values"]] == ["4.5 л"]
    viscosity = rows["engine_oil_viscosity"]["values"][0]
    assert viscosity["value"] == "SAE 0W-16" and viscosity["secondary"] is True
    assert viscosity["source"]["quote"] == "q engine_oil_viscosity" and viscosity["source"]["title"]


def test_powertrain_and_year_filters(camry):
    ice = rows_of(us_tech_facts.build(camry["db"], ICE, "ru"))
    hev = rows_of(us_tech_facts.build(camry["db"], HEV, "ru"))
    assert [v["value"] for v in ice["fuel_tank_l"]["values"]] == ["60.6 л"]
    assert [v["value"] for v in hev["fuel_tank_l"]["values"]] == ["50 л"]
    assert [v["value"] for v in hev["power_hp"]["values"]] == ["176 hp (131.2 кВт)"]
    assert "engine_oil_capacity_l" not in hev  # the A25A-FKS and 2GR-FKS volumes are other engines
    assert "ground_clearance" not in ice  # stated for 2018-2019 only


def test_hidden_conflict_and_empty_values_are_never_shown(camry):
    data = us_tech_facts.build(camry["db"], ICE, "ru")
    rows = rows_of(data)
    assert "59.8 л" not in str(data)
    assert "front_brakes" not in rows and "rear_brakes" not in rows
    assert all(c["rows"] for c in data["categories"])  # an empty category is left out
    assert "Disputed issue" not in str(data["weak_points"])
    assert all(m["job_key"] != "spark_plugs" for m in data["maintenance"])


def test_trims_label_values_and_unrelated_trims_drop(camry):
    rows = rows_of(us_tech_facts.build(camry["db"], ICE, "ru"))
    values = {v["qualifier"]: v["value"] for v in rows["curb_weight_kg"]["values"]}
    assert values == {"L": "1470 кг", "LE": "1495 кг"}  # TRD is not a trim of this engine


def test_weak_points_campaigns_and_maintenance(camry):
    data = us_tech_facts.build(camry["db"], ICE, "ru")
    titles = [w["title"] for w in data["weak_points"]]
    assert titles == ["Fuel pump failure", "Owners report a rattle"]  # facts first, owner reports last
    owner = data["weak_points"][1]
    assert owner["owner_reports"] is True and owner["note"] == "владельцы сообщают"
    assert [c["number"] for c in data["campaigns"]] == ["20V682000"]
    jobs = {m["job_key"]: m for m in data["maintenance"]}
    assert set(jobs) == {"engine_oil_and_filter", "cabin_air_filter"}  # no DCT fluid on an 8-speed automatic
    assert jobs["engine_oil_and_filter"]["interval"] == "16 000 км или 1 год, что наступит раньше"
    assert jobs["cabin_air_filter"]["approximate"] is True and jobs["cabin_air_filter"]["secondary"] is True
    hev = us_tech_facts.build(camry["db"], HEV, "az")
    assert "Hybrid inverter coolant pump" in str(hev["weak_points"]) and "Hybrid inverter" not in str(data["weak_points"])
    assert hev["labels"]["approximate"] == "təxmini"


def test_owner_reports_never_reach_the_technical_part(camry):
    g = camry
    fact(g, "seats", 7, display="OWNER_REPORTS")
    g["db"].commit()
    us_tech_facts.clear_cache()
    assert "seats" not in rows_of(us_tech_facts.build(g["db"], ICE, "ru"))


def test_routes_follow_the_flag(client, camry):
    settings = get_settings()
    settings.show_us_tech_facts = None
    settings.environment = "development"
    assert us_tech_facts.enabled() is True
    assert client.get(f"/api/v1/catalog/us-tech/configurations/{ICE}").status_code == 200
    listed = client.get("/api/v1/catalog/us-tech/configurations", params={"make": "Toyota", "year": 2020}).json()
    assert {c["configuration_key"] for c in listed} == {ICE, HEV}
    assert client.get("/api/v1/meta/client-config").json()["us_tech_facts"] == {"enabled": True}
    assert client.get("/api/v1/catalog/us-tech/configurations/unknown").status_code == 404

    settings.show_us_tech_facts = False
    assert client.get(f"/api/v1/catalog/us-tech/configurations/{ICE}").status_code == 404
    assert client.get("/api/v1/catalog/us-tech/facets").status_code == 404
    assert "us_tech_facts" not in client.get("/api/v1/meta/client-config").json()


def test_production_default_is_off():
    settings = get_settings()
    settings.show_us_tech_facts = None
    settings.environment = "production"
    assert us_tech_facts.enabled(settings) is False
    settings.show_us_tech_facts = True
    assert us_tech_facts.enabled(settings) is True


def test_designation_and_edition_rules():
    class Row:
        configuration_key = "bmw-5-series-us-2018-3.0l-6cyl-turbo-ice-a-s8-awd"
        engine_family_key = None
        make_id = generation_id = None
        year_from = 2018
        conditions = {"identity": {"powertrain": "ICE", "drivetrain": "AWD", "displacement_l": "3.0", "epa_transmission": "Automatic (S8)"},
                      "line": "5 Series"}

    t = us_tech_facts.Target(Row(), {}, ["540i xDrive"], ["530i", "530i xDrive", "540i", "540i xDrive", "M550i xDrive", "530e", "540i xDrive Gran Turismo"], "5 Series")
    assert us_tech_facts.applies({"variant": "540i xDrive"}, t)[:2] == (True, 0)
    assert us_tech_facts.applies({"variant": "540i"}, t)[0] is False  # the rear-drive car
    assert us_tech_facts.applies({"edition": "530e and 530e xdrive phev sedans"}, t)[0] is False
    assert us_tech_facts.applies({"edition": "my18 5 series sedan tech"}, t)[0] is True
    assert us_tech_facts.applies({"edition": "5 series diesel tech sheet"}, t)[0] is False
    assert us_tech_facts.applies({"edition": "5 series gran turismo"}, t)[0] is False
    assert us_tech_facts.applies({"vpic_ca_model": "5 SERIES 540i xDRIVE 4DR SEDAN"}, t)[:2] == (True, 0)
    assert us_tech_facts.applies({"models": "A3 with AWD; S3"}, t)[0] is False


def test_web_preview_serves_the_panel_behind_the_flag(client):
    script = client.get("/preview/us-tech-views.js")
    assert script.status_code == 200
    assert "state.meta?.us_tech_facts?.enabled === true" in script.text
    assert "/catalog/us-tech/configurations/" in script.text
    app_v2 = client.get("/preview/app-v2.js").text
    assert "usTechViews.route(name, id)" in app_v2
    catalog = client.get("/preview/catalog-views.js").text
    assert "usTech?.enabled()" in catalog  # the vehicle card mounts the panel only with the flag


def test_translations_follow_the_language_and_keep_the_original(camry):
    from app.models.translations import ContentTranslation

    g = camry

    def translation(kind, text, ru, az):
        g["db"].add(ContentTranslation(kind=kind, source_hash=us_tech_facts.text_hash(text), source_text=text, text_ru=ru,
                                       text_az=az, method="manual", glossary_version="test", status="CHECKED"))

    translation("issue_title", "Fuel pump failure", "Отказ топливного насоса", "Yanacaq nasosunun nasazlığı")
    translation("issue_symptom", "stall", "двигатель глохнет", "mühərrik söndürülür")
    translation("recall_summary", "The fuel pump may fail.", "Топливный насос может отказать.", "Yanacaq nasosu sıradan çıxa bilər.")
    g["db"].commit()
    us_tech_facts.clear_cache()
    ru = us_tech_facts.build(g["db"], ICE, "ru")
    fact = next(w for w in ru["weak_points"] if w["original"]["title"] == "Fuel pump failure")
    assert fact["title"] == "Отказ топливного насоса" and fact["symptoms"] == ["двигатель глохнет"]
    assert fact["original"]["symptoms"] == ["stall"]
    assert ru["campaigns"][0]["summary"] == "Топливный насос может отказать."
    assert ru["campaigns"][0]["original"]["summary"] == "The fuel pump may fail."
    az = us_tech_facts.build(g["db"], ICE, "az")
    assert next(w for w in az["weak_points"] if w["original"]["title"] == "Fuel pump failure")["title"] == "Yanacaq nasosunun nasazlığı"
    # a text without a translation is shown as it is
    assert any(w["title"] == "Owners report a rattle" for w in az["weak_points"])
