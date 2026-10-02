"""Confirmed identity may be useful without seating; unknown hard constraints never match."""

# ruff: noqa: F811
from unittest.mock import patch

from app.schemas.knowledge import BuyerFilters
from app.services import catalog_buyer as buyer
from app.services.catalog_verification import base_catalog_counts, base_catalog_ready
from test_base_catalog_batch import basic
from test_factory_verification import apply, proof  # noqa: F401
from test_published_knowledge import editorial  # noqa: F401


def test_partial_admission_keeps_strict_counts_and_request_constraints(db_session, proof):
    actor, base, value = proof
    apply(db_session, actor, basic(value))
    with patch(
        "app.services.market_priority.policy", return_value={"primary_makes": ["Test make"]}
    ):
        before = base_catalog_counts(buyer.records(db_session), require_us_seating=True)
        params = dict(
            catalog_scope="US_CONFIRMED_2000", year_min=2000, engine="GASOLINE", transmission="AT"
        )
        for lang in ("az", "ru"):
            result = buyer.search(db_session, BuyerFilters(**params), lang)
            assert result["recommendation"]["top"]["id"] == base.id
            assert result["recommendation"]["top"]["us_catalog_ready"]
            profile = buyer.vehicle_profile(base.specifications["catalog"], lang)
            assert "seats" not in {row["key"] for row in profile["summary"]}
            for constraint in (
                {"min_seats": 7},
                {"budget_max_minor": 2000000},
                {"min_clearance_mm": 150},
            ):
                constrained = buyer.search(db_session, BuyerFilters(**params, **constraint), lang)
                assert not constrained["matches"] and constrained["recommendation"]["top"] is None
                assert constrained["needs_confirmation"][0]["id"] == base.id
        assert [x["id"] for x in buyer.search(
            db_session, BuyerFilters(catalog_scope="US_BASE_2000")
        )["matches"]] == [base.id]
        assert before == base_catalog_counts(buyer.records(db_session), require_us_seating=True)
        assert buyer.facets(db_session, "US_CONFIRMED_2000")["markets"] == ["US"]
        exact = buyer.resolve(
            db_session, dict(catalog_scope="US_CONFIRMED_2000", make="Test make", year=2020)
        )
        assert exact["status"] == "EXACT"
        pending = buyer.resolve(
            db_session,
            dict(catalog_scope="US_CONFIRMED_2000", make="Test make", year=2020, seats=7),
        )
        assert not pending["candidates"] and pending["status"] == "NEEDS_CONFIRMATION"
        assert pending["needs_confirmation"][0]["missing"] == ["seats"]


def test_optional_seats_do_not_override_powertrain_and_fuel_evidence(db_session, proof):
    actor, base, value = proof
    apply(db_session, actor, basic(value))
    import copy

    from app.services.catalog_verification import fingerprint

    original = base.specifications["catalog"]
    assert base_catalog_ready(original)
    for missing_key in ("powertrain", "fuel"):
        altered = copy.deepcopy(original)
        altered["facts"].pop(missing_key)
        altered["verification_gate"]["fingerprint"] = fingerprint(altered)
        assert not base_catalog_ready(altered)

    electric = copy.deepcopy(original)
    source = electric["facts"]["engine_description"]["documentary_source"]
    electric["facts"]["powertrain"].update(value="BEV", documentary_source=source)
    electric["facts"]["fuel"].update(value="ELECTRICITY", documentary_source=source)
    electric["facts"]["engine_description"].update(
        value="Source-backed electric motor variant", documentary_source=source
    )
    electric["facts"].pop("engine_displacement")
    electric["verification_gate"]["fingerprint"] = fingerprint(electric)
    assert base_catalog_ready(electric)


def test_partial_scope_does_not_promote_research_other_market_or_conflict(db_session, proof):
    actor, base, value = proof
    with patch(
        "app.services.market_priority.policy", return_value={"primary_makes": ["Test make"]}
    ):
        assert not buyer.search(db_session, BuyerFilters(catalog_scope="US_CONFIRMED_2000"))[
            "matches"
        ]
        apply(db_session, actor, basic(value))
        for filters in (
            {"market_preference": "SELECTED", "markets": ["CA"]},
            {"year_max": 1999},
            {"transmission": "CVT"},
        ):
            assert not buyer.search(
                db_session, BuyerFilters(catalog_scope="US_CONFIRMED_2000", **filters)
            )["matches"]
        c = base.specifications["catalog"]
        import copy

        c = copy.deepcopy(c)
        c["original_market"] = "CA"
        assert not buyer.active_us_base_rows([(base, c)])
        c["original_market"] = "US"
        c["facts"]["catalog_applicability"] = {
            "value": "EXCLUDED",
            "status": "CONFIRMED",
            "documentary_source": {"url": "https://example.test"},
        }
        assert not buyer.active_us_base_rows([(base, c)])
