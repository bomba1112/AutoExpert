"""Fuel shown in the app (owner rule 2026-10-04): the manufacturer's AKI as our AI grade by a
fixed table, and a separate Auto Expert recommendation derived in code — never a fact of the
database and never labelled as the manufacturer's requirement."""

from __future__ import annotations

from itertools import product

import pytest
from app.services import catalog_buyer as buyer
from app.services import fuel_advice
from app.services import us_tech_facts

MAKER_WORDS = ("по требованию производителя", "istehsalçının tələbi ilə")


def epa(value, field="fuelType1"):
    return {"value": value, "status": "CONFIRMED", "locator": f"EPA vehicle 1: {field}"}


def gasoline(**facts):
    return {"fuel": epa("GASOLINE"), "fuel_grade": epa("Regular Gasoline"), "powertrain": epa("ICE", "atvType"), **facts}


def rec(facts, aki=(), language="ru", texts=()):
    lines = fuel_advice.rows(fuel_advice.traits_from_facts(facts, list(texts), list(aki)), language)
    return [x for x in lines if x["kind"] == "recommendation"], [x for x in lines if x["kind"] == "manufacturer"]


@pytest.mark.parametrize(("aki", "ru", "az"), [(87, "АИ-92", "AI-92"), (89, "АИ-93/95", "AI-93/95"),
                                               (91, "АИ-95", "AI-95"), (93, "АИ-98", "AI-98")])
def test_fixed_aki_table(aki, ru, az):
    assert fuel_advice.maker_value(aki, "ru") == f"{ru} (AKI {aki} по шкале США)"
    assert fuel_advice.maker_value(aki, "az") == f"{az} (AKI {aki} ABŞ şkalası ilə)"
    _, maker = rec(gasoline(), [aki])
    assert maker[0]["label"] == "Бензин по требованию производителя" and maker[0]["basis"] == "по требованию производителя"


def test_aki_outside_the_table_is_not_converted():
    assert fuel_advice.maker_value(90, "ru") == "AKI 90 (по шкале США)"


def test_direct_injection_from_epa_sidi_and_from_the_source_text():
    sidi = gasoline(engine_description=epa("SIDI; FFS", "eng_dscr"))
    (line,), _ = rec(sidi)
    assert line["value"] == "не ниже АИ-95, рекомендация для АЗ/СНГ" and "SIDI" in line["reason"]
    named = gasoline(injection={"value": "Gasoline Direct Injection (GDI)", "status": "CONFIRMED", "locator": "Kia Media"})
    assert rec(named)[0][0]["grade"] == 95
    assert rec(gasoline(), texts=["2.0L direct injection DOHC"])[0][0]["grade"] == 95


@pytest.mark.parametrize("boost", ["TURBO", "SUPERCHARGED"])
def test_turbo_and_supercharger_from_epa(boost):
    (line,), _ = rec(gasoline(aspiration=epa(boost, "tCharger")))
    assert line["grade"] == 95 and line["value"].startswith("не ниже АИ-95")


def test_port_injected_engine_without_boost_and_an_unknown_engine():
    assert rec(gasoline(engine_description=epa("FFS", "eng_dscr")))[0][0]["grade"] == 92
    assert rec(gasoline())[0][0]["grade"] == 92  # an EPA record without SIDI: no direct injection
    unknown = {"fuel": {"value": "GASOLINE", "status": "CONFIRMED", "locator": "press"}}
    (line,), _ = rec(unknown)
    assert line["grade"] == 95 and "не подтверждён" in line["reason"]


def test_recommendation_never_below_the_manufacturer():
    (line,), (maker,) = rec(gasoline(engine_description=epa("SIDI", "eng_dscr")), [93])
    assert maker["value"].startswith("АИ-98") and line["value"] == "не ниже АИ-98, рекомендация для АЗ/СНГ"
    (line,), (maker,) = rec(gasoline(), [89])
    assert maker["value"].startswith("АИ-93/95") and line["grade"] == 95
    (line,), _ = rec(gasoline(fuel_grade=epa("Premium Gasoline")))
    assert line["grade"] == 95  # never lower than the EPA premium fuel shown next to it


def test_field_is_never_empty_for_a_gasoline_car_and_absent_for_diesel_or_electric():
    lines, maker = rec(gasoline())
    assert len(lines) == 1 and not maker  # no manufacturer octane: the recommendation alone
    assert rec({"fuel": epa("DIESEL"), "powertrain": epa("ICE", "atvType")}) == ([], [])
    assert rec({"fuel": epa("ELECTRICITY"), "powertrain": epa("BEV", "atvType")}) == ([], [])


def test_recommendation_is_never_labelled_as_the_manufacturer_requirement():
    variants = [gasoline(), gasoline(engine_description=epa("SIDI", "eng_dscr")), gasoline(aspiration=epa("TURBO", "tCharger")),
                {"fuel": {"value": "GASOLINE", "status": "CONFIRMED"}}]
    for facts, aki, language in product(variants, [(), (87,), (89,), (91,), (93,), (90,)], ("ru", "az")):
        lines = fuel_advice.rows(fuel_advice.traits_from_facts(facts, [], list(aki)), language)
        for line in lines:
            text = " ".join(str(line.get(k) or "") for k in ("label", "value", "basis", "reason"))
            if line["kind"] == "recommendation":
                assert line["key"] == "fuel_recommendation"
                assert not any(w in text for w in MAKER_WORDS), text
                assert "Auto Expert" in line["label"]
            else:
                assert line["kind"] == "manufacturer" and line["key"] == "fuel_octane_maker"
                assert any(w in line["basis"] for w in MAKER_WORDS)
        assert sum(x["kind"] == "recommendation" for x in lines) == 1


def test_recommendation_is_not_a_database_fact():
    # the rule writes nothing: a profile built twice from the same record gives the same line,
    # and the record itself has no fuel_recommendation fact
    catalog = {"facts": gasoline(aspiration=epa("TURBO", "tCharger"), octane_aki={"value": 91, "status": "CONFIRMED"}),
               "source_url": "https://www.fueleconomy.gov/", "original_market": "US", "model_year": 2020}
    profile = buyer.vehicle_profile(catalog, "ru")
    fuel = next(g for g in profile["technical"] if g["key"] == "fuel")
    keys = [r["key"] for r in fuel["rows"]]
    assert "octane_aki" not in keys and keys.count("fuel_octane_maker") == 1 and keys.count("fuel_recommendation") == 1
    recommendation = next(r for r in fuel["rows"] if r["key"] == "fuel_recommendation")
    assert recommendation["kind"] == "recommendation" and recommendation["source_url"] is None
    assert not any(w in recommendation["label"] + recommendation["value"] for w in MAKER_WORDS)
    maker = next(r for r in fuel["rows"] if r["key"] == "fuel_octane_maker")
    assert maker["value"] == "АИ-95 (AKI 91 по шкале США)"
    assert "fuel_recommendation" not in catalog["facts"]
    assert any(r["key"] == "fuel_recommendation" for r in profile["summary"])


def test_us_tech_panel_converts_the_octane_and_adds_the_recommendation(db_session):
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
    fact(g, "octane_aki", 87)
    fact(g, "injection", "D-4S (direct and port injection)")
    db_session.commit()
    for language in ("ru", "az"):
        data = us_tech_facts.build(db_session, ICE, language)
        fuel = next(c for c in data["categories"] if c["key"] == "fuel")
        rows = {r["key"]: r for r in fuel["rows"]}
        assert rows["octane_aki"]["kind"] == "manufacturer"
        assert rows["octane_aki"]["values"][0]["value"].startswith("АИ-92" if language == "ru" else "AI-92")
        line = rows["fuel_recommendation"]
        assert line["kind"] == "recommendation" and line["values"][0]["source"] is None
        assert line["values"][0]["value"].startswith("не ниже АИ-95" if language == "ru" else "ən azı AI-95")
        assert not any(w in line["label"] + line["values"][0]["value"] for w in MAKER_WORDS)
    us_tech_facts.clear_cache()


def test_every_combustion_record_gets_a_line_flex_fuel_included():
    unspecified = {"fuel": epa("GASOLINE"), "powertrain": epa("COMBUSTION_UNSPECIFIED", "atvType")}
    assert rec(unspecified)[0][0]["grade"] == 92
    assert rec({"fuel": epa("E85"), "powertrain": epa("ICE", "atvType")})[0][0]["grade"] == 92
    for other in ("Hydrogen", "Natural Gas"):
        assert rec({"fuel": epa(other), "powertrain": epa("ICE", "atvType")}) == ([], [])
