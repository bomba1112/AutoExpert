# ruff: noqa: F811
"""Synthetic isolated fixtures: never publish fixture prices to the local catalogue."""

from datetime import UTC, date, datetime
from decimal import Decimal as D
from types import SimpleNamespace

import pytest
from app.schemas.knowledge import ImportManifest
from app.schemas.verified_ownership import (
    EnergyPrice,
    MaintenanceOperation,
    OwnershipRecord,
    OwnershipScenario,
)
from app.services.knowledge_import import (
    enqueue,
    process_job,
    publish_job,
    review_job,
    store_document,
)
from app.services.ownership_cost import (
    calculate,
    charge_cost,
    comparable_prices,
    maintenance_calendar,
    package_cost,
)
from app.services.ownership_evidence import available
from test_published_knowledge import editorial, published, synthetic_consumer_rows  # noqa: F401


def scenario(**kw):
    return OwnershipScenario(start_date=date(2026, 1, 1), current_odometer_km=0, **kw)


def op(**kw):
    return MaintenanceOperation(
        operation="oil",
        action="REPLACE",
        schedule="NORMAL",
        interval_km=10000,
        interval_months=12,
        original_interval="Test fixture",
        labels={"az": "Test", "ru": "Тест"},
        **kw,
    )


def energy(key="fuel", **kw):
    data = {
        "energy": "AI92",
        "channel": "RETAIL",
        "provider": "Test",
        "unit": "L",
        "unit_price": "1.00",
        "regulated": True,
    }
    data.update(kw.pop("data", {}))
    fields = dict(
        external_key=key,
        kind="ENERGY_PRICE",
        source_url="https://example.test/tariff",
        locator="Fixture",
        observed_at=datetime(2025, 12, 1, tzinfo=UTC),
        effective_from=date(2026, 1, 1),
        verification="CONFIRMED",
        limitations={"az": "Test", "ru": "Тест"},
        data=data,
    )
    fields.update(kw)
    return OwnershipRecord(**fields)


def publish_evidence(db, user, records):
    manifest = ImportManifest(
        source_id="test-source",
        parser="ownership-json-v1",
        ownership_records=records,
        selection_basis="Isolated ownership test fixture",
    )
    job = enqueue(db, manifest)
    while job.state in {"QUEUED", "RUNNING"}:
        process_job(db, job.id, batch_size=1)
    review_job(db, job, user, approve=True, note="Reviewed test ownership evidence")
    publish_job(db, job, user, note="Publish isolated test evidence")
    return job, manifest


def test_review_history_idempotency_and_lock(db_session, editorial):
    _, user = editorial
    job, manifest = publish_evidence(db_session, user, [energy()])
    assert enqueue(db_session, manifest).id == job.id
    first = available(db_session)[0]
    publish_evidence(db_session, user, [energy(data={"unit_price": "1.20"})])
    second = available(db_session)[0]
    assert second.previous_revision_id == first.id and first.state == "SUPERSEDED"
    assert first.payload["data"]["unit_price"] == "1.00"
    second.editorial_locked = True
    db_session.commit()
    with pytest.raises(ValueError, match="EDITORIAL_OVERRIDE_PROTECTED"):
        publish_evidence(db_session, user, [energy(data={"unit_price": "1.30"})])
    assert available(db_session)[0].id == second.id


def test_bad_raw_quarantines_no_publication(db_session, editorial):
    _, user = editorial
    doc = store_document(db_session, "test-source", b'[{"kind":"ENERGY_PRICE","unexpected":true}]')
    job = enqueue(
        db_session,
        ImportManifest(
            source_id="test-source",
            parser="ownership-json-v1",
            document_id=doc.id,
            selection_basis="Schema drift isolated fixture",
        ),
    )
    process_job(db_session, job.id)
    assert job.errors and not available(db_session)
    with pytest.raises(ValueError):
        review_job(db_session, job, user, approve=True, note="Do not approve drift")


def test_known_schedule_time_and_distance_independent():
    s = scenario(
        monthly_km=0,
        history=[{"operation": "oil", "last_date": "2025-06-01", "last_odometer_km": 0}],
    )
    events = maintenance_calendar(op(), s)["events"]
    assert [e["date"] for e in events] == ["2026-06-01", "2027-06-01"]
    s = scenario(
        monthly_km=10000,
        months=1,
        history=[{"operation": "oil", "last_date": "2026-01-01", "last_odometer_km": 0}],
    )
    assert maintenance_calendar(op(), s)["events"][0]["date"] == "2026-02-01"


def test_unknown_history_and_explicit_initial_service():
    assert maintenance_calendar(op(), scenario())["status"] == "HISTORY_REQUIRED"
    events = maintenance_calendar(op(), scenario(initial_service_assumption=True))["events"]
    assert events[0]["basis"] == "INITIAL_SERVICE_ASSUMPTION"
    assert events[0]["date"] == "2026-01-01"


def test_first_interval_and_overdue():
    s = scenario(
        monthly_km=1000,
        first_registration=date(2025, 1, 1),
        history=[{"operation": "oil", "never_serviced": True}],
    )
    events = maintenance_calendar(op(first_months=18, first_km=90000), s)["events"]
    assert [e["date"] for e in events] == ["2026-07-01", "2027-05-01"]
    s = scenario(
        monthly_km=0,
        history=[{"operation": "oil", "last_date": "2024-01-01", "last_odometer_km": 0}],
    )
    assert maintenance_calendar(op(), s)["events"][0]["basis"] == "OVERDUE_AT_START"


def test_severe_not_inferred_from_country_and_inspection_not_replacement():
    with pytest.raises(ValueError, match="SEVERE_CONDITIONS_REQUIRED"):
        scenario(schedule="SEVERE")
    severe = op().model_copy(update={"schedule": "SEVERE", "condition_codes": ["DUST"]})
    assert maintenance_calendar(severe, scenario())["status"] == "NOT_APPLICABLE"
    inspect = op().model_copy(update={"action": "INSPECT"})
    assert all(
        e["action"] == "INSPECT"
        for e in maintenance_calendar(inspect, scenario(initial_service_assumption=True))["events"]
    )


def test_packaging_and_unknown_extra():
    assert package_cost(D("5.4"), D("4"), D("80"), D(0)) == 160
    assert package_cost(D("5.4"), D("4"), D("80"), None) is None


def test_home_tiers_incremental_fixed_and_operator_tariff():
    home = EnergyPrice(
        energy="ELECTRICITY",
        channel="HOME",
        provider="Test",
        unit="kWh",
        regulated=True,
        tiers=[
            {"up_to_kwh": 200, "unit_price": "0.084"},
            {"up_to_kwh": 300, "unit_price": "0.10"},
            {"unit_price": "0.15"},
        ],
        fixed_monthly=1,
    )
    assert charge_cost(home, D(200), household=D(150)) == D("21.70")
    assert charge_cost(home, D(200), household=D(150), dedicated=True) == D("22.70")
    assert charge_cost(home, D(200)) is None
    with pytest.raises(ValueError, match="NOT_A_CONSUMER"):
        charge_cost(home.model_copy(update={"channel": "SUPPLIER_TO_OPERATOR"}), D(100))


def test_fuel_date_change_decimal_partial_and_snapshot(db_session, editorial):
    _, user = editorial
    variant = published(db_session, user)[0]
    publish_evidence(
        db_session,
        user,
        [
            energy(),
            energy("fuel-new", effective_from=date(2026, 1, 16), data={"unit_price": "2.00"}),
        ],
    )
    c = variant.specifications["catalog"]
    s = scenario(
        monthly_km=3100,
        months=1,
        fuel_energy="AI92",
        purchase="10000",
        resale="9000",
        repair_reserve="1000",
        other="0",
    )
    result = calculate(db_session, variant, c, s)
    # 100 km/day * 6.25 L/100km * (15*1 + 16*2)
    assert result["energy"] == "293.75"
    assert result["operating_total"] is None and result["scheduled_service"] is None
    assert result["depreciation"] == "1000.00"
    assert len(result["evidence"]) == 2
    from app.services.catalog_buyer import save_dossier

    saved = save_dossier(db_session, user, variant, c, "ru", {}, ownership=result)
    assert saved.evidence_bundle["ownership_snapshot"]["energy"] == "293.75"
    sections = saved.generated_sections["translations"]
    ru = next(x for x in sections["ru"]["sections"] if x["key"] == "ownership_evidence")
    az = next(x for x in sections["az"]["sections"] if x["key"] == "ownership_evidence")
    assert [r["value"] for r in ru["rows"]] == [r["value"] for r in az["rows"]]
    publish_evidence(
        db_session,
        user,
        [energy("fuel-new", effective_from=date(2026, 1, 16), data={"unit_price": "3.00"})],
    )
    db_session.refresh(saved)
    assert saved.evidence_bundle["ownership_snapshot"]["energy"] == "293.75"


def test_ev_grid_losses_and_phev_explicit_share(db_session, editorial):
    _, user = editorial
    variant = published(db_session, user)[0]
    publish_evidence(
        db_session,
        user,
        [
            energy(
                "ev",
                data={
                    "energy": "ELECTRICITY",
                    "channel": "HOME",
                    "unit": "kWh",
                    "unit_price": "0.15",
                },
            )
        ],
    )
    c = {
        "facts": {
            "powertrain": {"value": "BEV"},
            "electricity_combined": {"value": "20", "unit": "kWh/100km", "status": "CONFIRMED"},
        }
    }
    r = calculate(
        db_session,
        variant,
        c,
        scenario(months=1, consumption_side="GRID", charging_loss_fraction="0.2"),
    )
    assert r["energy"] == "30.00" and "GRID_CONSUMPTION_ALREADY_INCLUDES_LOSSES" in r["warnings"]
    r = calculate(
        db_session,
        variant,
        c,
        scenario(months=1, consumption_side="BATTERY", charging_loss_fraction="0.2"),
    )
    assert r["energy"] == "37.50"
    c["facts"]["powertrain"]["value"] = "PHEV"
    assert calculate(db_session, variant, c, scenario(months=1))["energy"] is None


def test_prices_deduplicate_seller_and_do_not_invent_median():
    def offer(seller, offer_id, price):
        return SimpleNamespace(
            payload={
                "verification": "CONFIRMED",
                "observed_at": "2026-01-01",
                "data": {
                    "part_number": "P",
                    "brand": "B",
                    "unit": "L",
                    "region": "Baku",
                    "condition": "NEW",
                    "available": True,
                    "offer_type": "EXACT",
                    "seller_id": seller,
                    "original_offer_id": offer_id,
                    "package_price": price,
                    "package_quantity": "4",
                },
            }
        )

    a = offer("a", "one", "80")
    kwargs = dict(part_number="P", brand="B", unit="L", region="Baku", at=date(2026, 1, 2))
    result = comparable_prices([a, a, a], **kwargs)
    assert result["observations"] == 1 and result["median"] is None
    assert (
        comparable_prices([a, offer("b", "two", "100"), offer("c", "three", "120")], **kwargs)[
            "median"
        ]
        == "25.00"
    )


def test_scope_change_hides_fitment(db_session, editorial):
    _, user = editorial
    variant = published(db_session, user)[0]
    payload = energy("fit").model_dump(mode="json")
    payload.update(
        kind="FITMENT",
        variant_ids=[variant.id],
        data={
            "part_number": "P",
            "brand": "B",
            "material_key": "oil",
            "relationship": "OEM",
            "identity_basis": "Isolated test exact variant",
        },
    )
    publish_evidence(db_session, user, [OwnershipRecord.model_validate(payload)])
    assert len(available(db_session, variant_id=variant.id)) == 1
    changed = dict(variant.specifications["catalog"])
    changed["original_market"] = "KR"
    variant.specifications = {"catalog": changed}
    db_session.commit()
    assert available(db_session, variant_id=variant.id) == []


@pytest.mark.parametrize("share,expected", [("0", "100.00"), ("0.5", "70.00"), ("1", "40.00")])
def test_phev_blended_fuel_and_energy_breakdown(db_session, editorial, share, expected):
    _, user = editorial
    variant = published(db_session, user)[0]
    publish_evidence(
        db_session,
        user,
        [
            energy(),
            energy(
                "home",
                data={
                    "energy": "ELECTRICITY",
                    "channel": "HOME",
                    "unit": "kWh",
                    "unit_price": "0.10",
                },
            ),
        ],
    )
    c = {
        "facts": {
            "powertrain": {"value": "PHEV"},
            "fuel_combined": {"value": "10", "unit": "L/100km", "status": "CONFIRMED"},
            "electricity_combined": {"value": "20", "unit": "kWh/100km", "status": "CONFIRMED"},
            "electric_mode_fuel": {"value": "2", "unit": "L/100km", "status": "CONFIRMED"},
        }
    }
    result = calculate(
        db_session,
        variant,
        c,
        scenario(
            months=1, fuel_energy="AI92", consumption_side="GRID", electric_distance_share=share
        ),
    )
    assert result["energy"] == expected
    assert sum(D(x["unrounded_amount"]) for x in result["energy_breakdown"]).quantize(
        D(".01")
    ) == D(expected)
    assert result["catalog_facts"] == c["facts"]


def test_known_zero_is_not_missing_and_foreign_region_is_excluded(db_session, editorial):
    _, user = editorial
    variant = published(db_session, user)[0]
    publish_evidence(db_session, user, [energy()])
    r = calculate(
        db_session,
        variant,
        variant.specifications["catalog"],
        scenario(months=1, monthly_km=0, fuel_energy="AI92"),
    )
    assert r["energy"] == r["energy_known_subtotal"] == r["operating_known_subtotal"] == "0.00"
    publish_evidence(db_session, user, [energy(data={"region": "Ganja"})])
    r = calculate(
        db_session,
        variant,
        variant.specifications["catalog"],
        scenario(months=1, fuel_energy="AI92"),
    )
    assert r["energy"] is None and r["energy_known_subtotal"] is None


def test_csv_upload_resume_and_schema_drift(db_session, editorial):
    import csv
    import io
    import json

    from app.services.ownership_evidence import parse_csv

    _, user = editorial
    items = [energy("a").model_dump(mode="json"), energy("b").model_dump(mode="json")]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(OwnershipRecord.model_fields))
    writer.writeheader()
    for item in items:
        writer.writerow(
            {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in item.items()}
        )
    assert parse_csv(output.getvalue()) == items
    with pytest.raises(ValueError, match="SCHEMA_DRIFT"):
        parse_csv(output.getvalue().replace("external_key", "unexpected"))
    doc = store_document(db_session, "test-source", output.getvalue().encode())
    job = enqueue(
        db_session,
        ImportManifest(
            source_id="test-source",
            parser="ownership-csv-v1",
            document_id=doc.id,
            selection_basis="Synthetic permitted CSV upload",
        ),
    )
    process_job(db_session, job.id, batch_size=1)
    assert job.cursor == 1 and not available(db_session)
    process_job(db_session, job.id, batch_size=1)
    review_job(db_session, job, user, approve=True, note="CSV fixture review")
    publish_job(db_session, job, user, note="CSV fixture publication")
    assert len(available(db_session)) == 2


def test_labor_package_once_inspection_never_replacement(db_session, editorial):
    _, user = editorial
    variant = published(db_session, user)[0]
    rows = []
    for name in ("brake-inspection", "suspension-inspection"):
        r = energy(name).model_dump(mode="json")
        r.update(
            kind="MAINTENANCE",
            variant_ids=[variant.id],
            data={
                "operation": name,
                "action": "INSPECT",
                "schedule": "NORMAL",
                "interval_months": 12,
                "original_interval": "Synthetic yearly inspection",
                "labels": {"az": "Test", "ru": "Тест"},
            },
        )
        rows.append(OwnershipRecord.model_validate(r))
    r = energy("package").model_dump(mode="json")
    r.update(
        kind="LABOR",
        variant_ids=[variant.id],
        observed_at="2026-01-01T00:00:00Z",
        data={
            "seller_id": "test",
            "original_offer_id": "one",
            "region": "Baku",
            "workshop_type": "TEST",
            "operation": "inspection-package",
            "unit": "PACKAGE",
            "price_min": "50",
            "price_max": "50",
            "included_operations": [x.data["operation"] for x in rows],
        },
    )
    rows.append(OwnershipRecord.model_validate(r))
    publish_evidence(db_session, user, rows)
    quote = next(x for x in available(db_session) if x.kind == "LABOR")
    result = calculate(
        db_session,
        variant,
        variant.specifications["catalog"],
        scenario(months=1, initial_service_assumption=True, selected_labor_quotes=[quote.id]),
    )
    assert result["service_known_subtotal"] == "50.00"
    assert {x["action"] for x in result["operations"]} == {"INSPECT"}
    assert sorted(x["labor"] for x in result["operations"]) == ["0.00", "50.00"]


def test_compare_and_save_detect_changed_evidence(client, db_session, editorial, monkeypatch):
    from app.core.security import create_access_token

    synthetic_consumer_rows(monkeypatch)
    _, user = editorial
    from test_published_knowledge import record

    variants = published(db_session, user, [record("first"), record("second")])
    publish_evidence(db_session, user, [energy()])
    value = scenario(months=1, fuel_energy="AI92").model_dump(mode="json")
    path = f"/api/v1/knowledge/vehicles/{variants[0].id}/ownership"
    response = client.post(path, json=value)
    assert response.status_code == 200
    sid = response.json()["scenario_id"]
    body = {"language": "az", "scenario": value, "expected_scenario_id": sid}
    assert client.post(path + "/save", json=body).status_code == 401
    headers = {"Authorization": "Bearer " + create_access_token(user.id)}
    assert client.post(path + "/save", json=body, headers=headers).status_code == 200
    publish_evidence(db_session, user, [energy(data={"unit_price": "2.00"})])
    assert client.post(path + "/save", json=body, headers=headers).status_code == 409
    comparison = {
        "scenario": value,
        "members": [
            {"variant_id": v.id, "current_odometer_km": i * 10000, "fuel_energy": "AI92"}
            for i, v in enumerate(variants[:2])
        ],
    }
    r = client.post("/api/v1/knowledge/ownership/compare", json=comparison)
    assert r.status_code == 200 and r.json()["winner"] is None
    assert not r.json()["coverage_comparable"]
    comparison["scenario"]["first_registration"] = "2020-01-01"
    assert client.post("/api/v1/knowledge/ownership/compare", json=comparison).status_code == 422


def test_consumer_ownership_excludes_evidence_after_rights_revocation(
    client, db_session, editorial, monkeypatch
):
    source, user = editorial
    synthetic_consumer_rows(monkeypatch)
    variant = published(db_session, user)[0]
    publish_evidence(db_session, user, [energy()])
    value = scenario(months=1, fuel_energy="AI92").model_dump(mode="json")
    assert calculate(db_session, variant, variant.specifications["catalog"], scenario(
        months=1, fuel_energy="AI92"
    ))["energy"] is not None

    source.config = {**source.config, "commercial_reuse": False}
    db_session.flush()
    # Internal research can still inspect the published record.
    assert available(db_session)
    assert client.get("/api/v1/knowledge/ownership/evidence").json() == []
    assert client.get(
        "/api/v1/knowledge/ownership/evidence", params={"variant_id": variant.id}
    ).json() == []
    response = client.post(
        f"/api/v1/knowledge/vehicles/{variant.id}/ownership", json=value
    )
    assert response.status_code == 200
    assert response.json()["energy"] is None
    assert response.json()["evidence"] == []


def test_extended_identity_scope_preserves_absent_legacy_fields():
    from app.services.knowledge_import import catalog_identity_hash, checksum
    from test_published_knowledge import record

    c = record().model_dump(mode="json")
    legacy = checksum(
        {
            "identity": {
                k: c.get(k)
                for k in (
                    "make",
                    "model",
                    "model_year",
                    "original_market",
                    "generation",
                    "facelift",
                )
            },
            "facts": {
                k: {
                    "value": c["facts"].get(k, {}).get("value"),
                    "status": c["facts"].get(k, {}).get("status"),
                }
                for k in (
                    "engine_displacement",
                    "powertrain",
                    "transmission_family",
                    "drivetrain",
                    "trim",
                    "body",
                )
            },
        }
    )
    assert catalog_identity_hash(c) == legacy
    c["facts"]["engine_code"] = {"value": "SYNTHETIC_ENGINE", "status": "CONFIRMED"}
    assert catalog_identity_hash(c) != legacy
