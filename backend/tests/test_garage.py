# ruff: noqa: E501
"""The Garage (product phase, stage 2): the next service of every interval variant, "не знаю",
conditions, onboard systems, the owner's oil interval, recalls by configuration and the daily NHTSA
check, unconfirmed (hidden) maintenance never used, the API behind the garage_v1 flag, the service
log PDF and the local VIN decoding."""

from __future__ import annotations

from datetime import date
from itertools import count

import pytest
from app.core.config import get_settings
from app.models.evidence import MaintenanceScheduleItem
from app.models.garage import GarageRecallNotice, GarageVehicle
from app.services import garage, garage_push, garage_recalls, us_tech_facts, vpic_local
from app.services.garage_schedule import (
    Interval,
    Plan,
    Reading,
    Record,
    add_months,
    due,
    estimate_km,
    oil_plan,
    plans,
)
from tests.test_us_tech_facts import ICE, configuration, fact, generation  # noqa: F401

TODAY = date(2026, 10, 5)
_keys = count()


def item(job, km=None, months=None, *, action="REPLACE", occurrence="EVERY", severe=False, system="FIXED_INTERVAL", max_km=None, max_months=None):
    rule = "WHICHEVER_FIRST" if km and months else None
    return {"job_key": job, "job": job, "action_code": action, "action": action.lower(), "occurrence_code": occurrence,
            "occurrence": {"FIRST": "first", "SUBSEQUENT": "subsequent"}.get(occurrence), "rule": rule, "km": km, "months": months,
            "severe": severe, "system_code": system, "system": None, "max_km": max_km, "max_months": max_months,
            "interval": f"{km} km / {months} mo", "secondary": False, "source": {"title": "manual"}}


def plan_of(job, *items, conditions="NORMAL", action="REPLACE"):
    return plans(list(items), conditions)[(job, action)]


# --- every interval variant ----------------------------------------------------------------------
def test_km_and_months_whichever_first_from_the_log():
    p = plan_of("spark_plugs", item("spark_plugs", 10000, 12))
    log = [Record("spark_plugs", on=date(2026, 1, 1), km=80000)]
    r = due(p, log, 85000, TODAY)
    assert (r["next_km"], r["next_date"], r["remaining_km"], r["status"], r["confirmed"]) == (90000, date(2027, 1, 1), 5000, "OK", True)
    assert due(p, log, 89000, TODAY)["status"] == "SOON"           # 1 000 km left
    assert due(p, log, 85000, date(2026, 12, 20))["status"] == "SOON"  # 12 days left
    assert due(p, log, 85000, date(2027, 1, 2))["status"] == "OVERDUE"  # the months came first
    assert due(p, log, 91000, TODAY)["status"] == "OVERDUE"            # the km came first


def test_km_only_and_months_only():
    km_only = due(plan_of("engine_air_filter", item("engine_air_filter", 30000)), [Record("engine_air_filter", on=date(2026, 1, 1), km=60000)], 70000, TODAY)
    assert km_only["next_km"] == 90000 and km_only["next_date"] is None and km_only["status"] == "OK"
    months_only = due(plan_of("brake_fluid", item("brake_fluid", None, 24)), [Record("brake_fluid", on=date(2025, 1, 15), km=50000)], 70000, TODAY)
    assert months_only["next_km"] is None and months_only["next_date"] == date(2027, 1, 15) and months_only["remaining_km"] is None


def test_first_and_subsequent_replacements():
    p = plan_of("engine_coolant", item("engine_coolant", 160000, 120, occurrence="FIRST"), item("engine_coolant", 80000, 60, occurrence="SUBSEQUENT"))
    assert p.first.km == 160000 and p.subsequent.km == 80000
    before = due(p, [], 100000, TODAY, in_service=date(2019, 10, 1))
    assert before["next_km"] == 160000 and before["next_date"] == date(2029, 10, 1) and not before["confirmed"]
    after = due(p, [], 170000, TODAY, in_service=date(2016, 1, 1))
    assert after["next_km"] == 240000 and after["next_date"] == date(2031, 1, 1)  # 120 + 60 months
    done = due(p, [Record("engine_coolant", on=date(2026, 3, 1), km=165000)], 170000, TODAY)
    assert done["next_km"] == 245000 and done["next_date"] == date(2031, 3, 1) and done["confirmed"]


def test_only_a_first_occurrence():
    p = plan_of("ac_desiccant", item("ac_desiccant", 100000, occurrence="FIRST"))
    assert due(p, [Record("ac_desiccant", on=date(2025, 5, 1), km=101000)], 120000, TODAY)["status"] == "DONE"
    passed = due(p, [], 120000, TODAY)
    assert passed["status"] == "CHECK" and passed["basis"] == "FIRST_PASSED_UNKNOWN"


def test_a_replacement_also_counts_for_the_inspection():
    p = plan_of("engine_coolant", item("engine_coolant", 30000, action="INSPECT"), action="INSPECT")
    r = due(p, [Record("engine_coolant", action="REPLACE", on=date(2026, 6, 1), km=80000)], 85000, TODAY)
    assert r["next_km"] == 110000 and r["confirmed"]


# --- unknown history ("не знаю") -----------------------------------------------------------------
def test_unknown_history_counts_by_the_schedule_from_the_current_mileage():
    p = plan_of("spark_plugs", item("spark_plugs", 30000, 36))
    r = due(p, [Record("spark_plugs", status="UNKNOWN", on=date(2026, 9, 1))], 87000, TODAY)
    assert r["next_km"] == 90000          # the next milestone of the schedule after 87 000
    assert r["next_date"] == date(2029, 9, 1)  # 36 months from the answer
    assert r["confirmed"] is False and r["basis"] == "SCHEDULE_UNCONFIRMED"
    # no record at all is the same as "не знаю"
    assert due(p, [], 87000, TODAY)["next_km"] == 90000


def test_unknown_timing_belt_means_check_now():
    p = plan_of("timing_belt", item("timing_belt", 100000, 60))
    r = due(p, [Record("timing_belt", status="UNKNOWN", on=date(2026, 9, 1))], 87000, TODAY)
    assert r["status"] == "CHECK" and r["basis"] == "UNKNOWN_CHECK_NOW" and not r["confirmed"]
    # a known replacement counts normally
    assert due(p, [Record("timing_belt", on=date(2024, 1, 1), km=60000)], 87000, TODAY)["next_km"] == 160000


# --- conditions ----------------------------------------------------------------------------------
def test_severe_conditions_use_the_severe_schedule_when_the_manual_has_one():
    schedule = [item("engine_air_filter", 30000), item("engine_air_filter", 15000, severe=True), item("cabin_air_filter", 24000)]
    severe = plans(schedule, "SEVERE")
    assert severe[("engine_air_filter", "REPLACE")].every.km == 15000 and severe[("engine_air_filter", "REPLACE")].severe
    # a job without a severe line keeps the normal one
    assert severe[("cabin_air_filter", "REPLACE")].every.km == 24000 and not severe[("cabin_air_filter", "REPLACE")].severe
    assert plans(schedule, "NORMAL")[("engine_air_filter", "REPLACE")].every.km == 30000


def test_default_conditions_by_region():
    assert garage.default_conditions("US") == "NORMAL"
    assert garage.default_conditions("AZ") == garage.default_conditions("CIS") == "SEVERE"
    assert garage.default_region("AZ", "ru") == "AZ" and garage.default_region("RU", "en") == "CIS"
    assert garage.default_region("US", "ru") == "US" and garage.default_region(None, "en") == "US"
    assert garage.default_region(None, "az") == "AZ" and garage.default_region(None, "ru") == "CIS"


# --- onboard systems and engine oil ---------------------------------------------------------------
def test_onboard_system_without_a_maximum_is_on_signal():
    p = plan_of("spark_plugs", item("spark_plugs", system="MAINTENANCE_MINDER"))
    assert due(p, [], 87000, TODAY)["status"] == "ON_SIGNAL"


def test_onboard_system_reminds_at_the_manuals_maximum_and_resets():
    schedule = [item("engine_oil_and_filter", system="OIL_LIFE_MONITOR", max_months=12)]
    oil = oil_plan({}, None, None, schedule)
    assert oil.onboard == "OIL_LIFE_MONITOR" and not oil.owner_set
    reset = [Record("engine_oil_and_filter", status="ONBOARD_RESET", on=date(2026, 4, 1), km=80000)]
    r = due(oil, reset, 86000, TODAY)
    assert r["next_date"] == date(2027, 4, 1) and r["confirmed"] and r["onboard"] == "OIL_LIFE_MONITOR"
    assert due(oil, reset, 86000, date(2027, 4, 2))["status"] == "OVERDUE"


def test_engine_oil_interval_is_the_owners():
    schedule = [item("engine_oil_and_filter", 16000, 12), item("engine_oil_and_filter", 8000, 6, severe=True)]
    unset = oil_plan({}, None, None, schedule)
    assert due(unset, [], 87000, TODAY)["status"] == "SET_INTERVAL"
    assert {h["km"] for h in unset.hints} == {16000, 8000}  # the manual's normal and severe values are hints
    owner = oil_plan({}, 7000, 6, schedule)
    r = due(owner, [Record("engine_oil_and_filter", on=date(2026, 7, 1), km=84000)], 87000, TODAY)
    assert (r["next_km"], r["next_date"]) == (91000, date(2027, 1, 1))


# --- mileage ---------------------------------------------------------------------------------------
def test_mileage_estimate_from_the_monthly_average():
    readings = [Reading(80000, date(2026, 1, 5)), Reading(89000, date(2026, 7, 5))]
    est = estimate_km(readings, None, TODAY)
    assert est["monthly_km"] == round(9000 / ((date(2026, 7, 5) - date(2026, 1, 5)).days / 30.44))
    assert est["estimated"] and est["km"] > 89000 and est["ask"]  # three months since the last reading
    owner = estimate_km(readings, 1000, date(2026, 7, 20))
    assert owner["monthly_km"] == 1000 and owner["km"] == 89000 + round(1000 * 15 / 30.44) and not owner["ask"]
    assert estimate_km([], 1000, TODAY)["km"] is None


def test_add_months_keeps_the_end_of_month():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 11, 15), 14) == date(2028, 1, 15)


def test_interval_helpers():
    assert Interval().empty and not Interval(km=1).empty
    assert Plan("x", "REPLACE", every=Interval(system="CBS")).onboard == "CBS"


# --- the database: recalls by configuration, hidden maintenance, the daily check -----------------
@pytest.fixture
def car(generation, db_session):  # noqa: F811
    g = generation
    configuration(g, ICE, "ICE", "A25A-FKS", "Automatic (S8)", ["Camry LE/SE"])
    fact(g, "transmission_fluid", "Toyota Genuine ATF WS", level="ENGINE", engine="A25A-FKS")
    fact(g, "transmission_fluid_capacity_l", 7.3, level="ENGINE", engine="A25A-FKS", unit="L")
    fact(g, "nhtsa_recall", "20V682000", years=(2018, 2020),
         extra={"campaign_number": "20V682000", "component": "FUEL PUMP", "summary": "The fuel pump may fail.", "model_years": [2019, 2020]})
    fact(g, "nhtsa_recall", "18V000000", years=(2018, 2018),
         extra={"campaign_number": "18V000000", "component": "OTHER", "summary": "Another year.", "model_years": [2018]})

    def job(name, km, months, display="FACT", condition="NORMAL"):
        db_session.add(MaintenanceScheduleItem(
            market="US", make_id=g["make"].id, generation_id=g["gen"].id, year_from=2018, year_to=2022, applicability={},
            schedule_system="FIXED_INTERVAL", job=name, action="REPLACE", condition=condition, occurrence="EVERY", interval_km=km,
            interval_months=months, rule="WHICHEVER_FIRST" if km and months else None, source_id=g["source"].id,
            locator="page 600", confidence="HIGH", status="CONFIRMED", display_level=display, natural_key=f"g{next(_keys)}",
            notes="quote: Replace"))

    job("transmission_fluid", 96000, None)
    job("spark_plugs", 96000, None, display="HIDDEN_CONFLICT")  # never shown, never reminded
    job("engine_air_filter", 48000, None)
    job("engine_air_filter", 24000, None, condition="SEVERE")
    db_session.commit()
    us_tech_facts.clear_cache()
    yield g
    us_tech_facts.clear_cache()


def _vehicle(db, user_id, region="US", conditions="NORMAL"):
    v = GarageVehicle(user_id=user_id, configuration_key=ICE, make="Toyota", model="Camry", year=2020, region=region,
                      conditions=conditions, conditions_by_owner=False)
    db.add(v)
    db.flush()
    garage.add_reading(db, v, 87000, TODAY)
    db.flush()
    return v


@pytest.fixture
def user(db_session):
    from app.models.user import User

    u = User(email="garage@example.test", password_hash="x", preferred_language="ru")
    db_session.add(u)
    db_session.flush()
    return u


def test_recalls_by_configuration_and_hidden_maintenance(car, db_session, user):
    v = _vehicle(db_session, user.id)
    view = garage.overview(db_session, v, "ru", TODAY)
    assert [r["number"] for r in view["recalls"]] == ["20V682000"]  # the 2018-only campaign is not this car's
    jobs = {s["job"] for s in view["services"]}
    assert "spark_plugs" not in jobs  # HIDDEN_CONFLICT: never used
    atf = next(s for s in view["services"] if s["job"] == "transmission_fluid")
    assert atf["fluid"]["spec"] == "Toyota Genuine ATF WS" and atf["fluid"]["capacity"] == "7.3 л"
    assert atf["next_km"] == 96000 and atf["unconfirmed_note"] == "по регламенту, не подтверждено"
    assert any(f["job"] == "transmission_fluid" for f in view["fluids"])


def test_conditions_switch_the_schedule(car, db_session, user):
    v = _vehicle(db_session, user.id, region="AZ", conditions="SEVERE")
    air = next(s for s in garage.overview(db_session, v, "en", TODAY)["services"] if s["job"] == "engine_air_filter")
    assert air["severe"] and air["next_km"] == 96000  # 24 000 grid after 87 000
    v.conditions = "NORMAL"
    air = next(s for s in garage.overview(db_session, v, "en", TODAY)["services"] if s["job"] == "engine_air_filter")
    assert not air["severe"] and air["next_km"] == 96000  # 48 000 grid: 96 000 as well
    v.readings[0].km = 97000
    air = next(s for s in garage.overview(db_session, v, "en", TODAY)["services"] if s["job"] == "engine_air_filter")
    assert air["next_km"] == 144000


def test_daily_recall_check_adds_new_campaigns_to_the_feed(car, db_session, user):
    v = _vehicle(db_session, user.id)
    db_session.commit()
    sent = garage_push.LogOnlySender()
    garage_push.set_sender(sent)
    try:
        calls = []

        def fetch(make, model, year):
            calls.append((make, model, year))
            return [{"NHTSACampaignNumber": "20V682000", "Component": "FUEL PUMP"},  # already in the database
                    {"NHTSACampaignNumber": "26V999000", "Component": "STEERING", "Summary": "New.", "ReportReceivedDate": "01/10/2026"}]

        result = garage_recalls.run(db_session, fetch)
        assert calls == [("Toyota", "Camry", 2020)] and result["new_notices"] == 1
        notices = db_session.query(GarageRecallNotice).all()
        assert [n.campaign_number for n in notices] == ["26V999000"]
        view = garage.overview(db_session, v, "ru", TODAY)
        assert [r["number"] for r in view["recalls"]] == ["26V999000", "20V682000"]
        assert view["recalls"][0]["origin"] == "NHTSA_DAILY_CHECK"
        assert {i.key for i in v.feed} >= {"recall:26V999000", "recall:20V682000"}
        assert any(m["key"] == "recall:26V999000" for m in sent.sent)  # the push interface got it; nothing was sent
        assert garage_recalls.run(db_session, fetch)["new_notices"] == 0  # once only
    finally:
        garage_push.set_sender(garage_push.LogOnlySender())


# --- the API ---------------------------------------------------------------------------------------
def _headers(client, language="ru"):
    token = client.post("/api/v1/auth/demo", json={"preferred_language": language}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_garage_api_flow(car, client):
    h = _headers(client)
    body = {"configuration_key": ICE, "odometer": 87000, "unit": "km", "monthly": 1500, "region": "AZ",
            "history": [{"job": "transmission_fluid", "status": "DONE", "performed_on": "2025-05-01", "odometer": 70000},
                        {"job": "engine_air_filter", "status": "UNKNOWN"}]}
    created = client.post("/api/v1/garage/vehicles?language=ru", json=body, headers=h)
    assert created.status_code == 201, created.text
    view = created.json()
    assert view["conditions"]["value"] == "SEVERE" and view["region"] == "AZ"
    atf = next(s for s in view["services"] if s["job"] == "transmission_fluid")
    assert atf["next_km"] == 166000 and atf["confirmed"]
    oil = next(s for s in view["services"] if s["job"] == "engine_oil_and_filter")
    assert oil["status"] == "SET_INTERVAL"
    vid = view["id"]
    updated = client.patch(f"/api/v1/garage/vehicles/{vid}?language=en", json={"oil_interval": 5000, "oil_interval_months": 6, "unit": "mi", "conditions": "NORMAL"}, headers=h).json()
    oil = next(s for s in updated["services"] if s["job"] == "engine_oil_and_filter")
    assert updated["conditions"] == {**updated["conditions"], "value": "NORMAL", "by_owner": True}
    assert oil["owner_interval"]["km"] == 8047 and "your interval" in oil["interval"]
    logged = client.post(f"/api/v1/garage/vehicles/{vid}/records?language=en",
                         json={"job": "engine_oil_and_filter", "performed_on": "2026-10-01", "odometer": 54100, "unit": "mi"}, headers=h).json()
    oil = next(s for s in logged["services"] if s["job"] == "engine_oil_and_filter")
    assert oil["status"] == "OK" and oil["next_km"] == round(54100 * 1.609344) + 8047
    assert client.post(f"/api/v1/garage/vehicles/{vid}/onboard-reset", json={"value": 88000}, headers=h).status_code == 201
    listing = client.get("/api/v1/garage/vehicles?language=ru", headers=h).json()
    assert listing[0]["id"] == vid
    feed = client.get("/api/v1/garage/feed?language=ru", headers=h).json()
    assert {f["kind"] for f in feed} >= {"RECALL"} and all(f["vehicle_id"] == vid for f in feed)
    assert client.post(f"/api/v1/garage/feed/{feed[0]['id']}/read", headers=h).json() == {"ok": True}
    pdf = client.get(f"/api/v1/garage/vehicles/{vid}/service-log.pdf?language=ru", headers=h)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    # another user sees nothing of this car
    other = _headers(client)
    assert client.get(f"/api/v1/garage/vehicles/{vid}", headers=other).status_code == 404
    assert client.get("/api/v1/garage/vehicles", headers=other).json() == []
    assert client.delete(f"/api/v1/garage/vehicles/{vid}", headers=h).status_code == 204


def test_unknown_configuration_is_refused(car, client):
    h = _headers(client)
    r = client.post("/api/v1/garage/vehicles", json={"configuration_key": "nope", "odometer": 1}, headers=h)
    assert r.status_code == 422


def test_garage_flag_off_in_production(client):
    settings = get_settings()
    original = settings.environment, settings.garage_v1
    h = _headers(client)
    try:
        settings.environment, settings.garage_v1 = "production", None
        assert not garage.enabled(settings)
        assert client.get("/api/v1/garage/vehicles", headers=h).status_code == 404
        settings.environment = "development"
        assert garage.enabled(settings) and client.get("/api/v1/garage/vehicles", headers=h).status_code == 200
        assert "garage_v1" in client.get("/api/v1/meta/client-config").json()
        settings.garage_v1 = False
        assert "garage_v1" not in client.get("/api/v1/meta/client-config").json()
    finally:
        settings.environment, settings.garage_v1 = original


def test_manual_choice_and_vin_candidates(car, db_session):
    found = garage.candidates(db_session, "toyota", "Camry", 2020)
    assert [c["configuration_key"] for c in found] == [ICE]
    decoded = {"make": "Toyota", "model": "Camry", "model_year": 2020, "displacement_l": "2.5", "transmission": "Automatic",
               "transmission_speeds": "8", "fuel": "Gasoline", "engine_model": "A25A-FKS", "drive": "4x2"}
    assert [c["configuration_key"] for c in garage.candidates(db_session, "Toyota", "Camry", 2020, decoded)] == [ICE]
    # a filter that would leave nothing is not applied: the owner chooses
    assert garage.candidates(db_session, "Toyota", "Camry", 2020, {**decoded, "displacement_l": "3.5"})


# --- local VIN decoding ------------------------------------------------------------------------------
def test_vin_check_digit_and_format():
    assert vpic_local.check_digit("1M8GDM9AXKP042788") == "X"
    assert vpic_local.check_digit("11111111111111111") == "1"
    bad = vpic_local.decode("1HGCM82633A00435")  # 16 characters
    assert bad["errors"] == ["FORMAT"] and not bad["valid"]
    assert vpic_local.decode("1HGCM82633A0O4352")["errors"] == ["FORMAT"]  # letter O


def test_model_year_cycle_by_position_7():
    assert vpic_local.model_years("4T1B11HK5KU000000", "2", None) == [2019]   # a letter at 7: 2010-2039
    assert vpic_local.model_years("1HGCM82633A004352", "2", None) == [2003]   # a digit at 7: 1980-2009
    assert vpic_local.model_years("1FTFW1E54PFA00000", "3", "2") == [2023, 1993]  # a heavy truck: both


@pytest.mark.skipif(not vpic_local.available(), reason="the local standalone vPIC database is not installed")
def test_vin_decoding_from_the_local_database():
    camry = vpic_local.decode("4T1B11HK5KU000000")
    assert (camry["make"], camry["model"], camry["model_year"], camry["engine_model"]) == ("Toyota", "Camry", 2019, "A25A-FKS")
    assert camry["database"].startswith("vPICList_lite")
    sonata = vpic_local.decode("5NPE24AF0JH000000")
    assert (sonata["make"], sonata["model"], sonata["model_year"], sonata["check_digit_ok"]) == ("Hyundai", "Sonata", 2018, True)
