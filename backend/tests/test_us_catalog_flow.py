"""US scope, transparent recommendations and profile facts on isolated fixtures."""

# ruff: noqa: F811
import copy
from unittest.mock import patch

import pytest
from app.schemas.knowledge import BuyerFilters
from app.services import catalog_buyer as buyer
from app.services.catalog_verification import us_catalog_ready, us_catalog_with_confirmed_seating
from test_base_catalog_batch import basic
from test_factory_verification import apply, proof  # noqa: F401
from test_published_knowledge import editorial  # noqa: F401


def seated(value):
    value = basic(value)
    value["facts"]["seats"] = dict(
        value=5,
        locator="Synthetic seating table",
        documentary_source=value["facts"]["body"]["documentary_source"],
    )
    return value


def test_seating_contract_and_old_catalog_remain_independent(db_session, proof):
    actor, base, value = proof
    apply(db_session, actor, basic(value))
    assert us_catalog_ready(base.specifications["catalog"])
    assert not us_catalog_with_confirmed_seating(base.specifications["catalog"])
    value = seated(value)
    value["identity_verification"]["previous_revision_id"] = base.published_revision_id
    apply(db_session, actor, value)
    assert us_catalog_ready(base.specifications["catalog"])
    assert us_catalog_with_confirmed_seating(base.specifications["catalog"])


def test_us_query_filters_facets_resolver_and_budget_uncertainty(db_session, proof):
    actor, base, value = proof
    apply(db_session, actor, seated(value))
    with patch(
        "app.services.market_priority.policy", return_value={"primary_makes": ["Test make"]}
    ):
        params = dict(
            catalog_scope="US_BASE_2000",
            year_min=2000,
            engine="GASOLINE",
            transmission="AT",
            body=["SEDAN"],
        )
        result = buyer.search(db_session, BuyerFilters(**params))
        assert result["recommendation"]["top"]["id"] == base.id
        assert result["matched_models"] == 1
        assert buyer.facets(db_session, "US_BASE_2000")["markets"] == ["US"]
        budget = buyer.search(db_session, BuyerFilters(**params, budget_max_minor=2000000))
        assert budget["recommendation"]["top"] is None
        assert budget["needs_confirmation"][0]["missing"] == ["budget"]
        resolved = buyer.resolve(
            db_session,
            dict(
                catalog_scope="US_BASE_2000",
                make="Test make",
                model="Test model",
                year=2020,
                market="US",
                language="az",
            ),
        )
        assert resolved["candidates"][0]["facts"]["seats"]["label"] == "Oturacaq sayı"
    from app.services.catalog_scope import scope_policy
    with patch("app.services.catalog_buyer.scope_policy", return_value=scope_policy()):
        assert not buyer.search(db_session, BuyerFilters(catalog_scope="US_BASE_2000"))["matches"]
    # The generic API retains historical/non-priority records.
    assert buyer.search(db_session, BuyerFilters())["matches"]


def ranked(hp, seats=5, cycle="EPA", fuel=7):
    return dict(
        base_catalog_ready=True,
        market="US",
        test_cycle=cycle,
        ranking={},
        facts={
            "power_hp": dict(value=hp, status="CONFIRMED"),
            "seats": dict(value=seats, status="CONFIRMED"),
            "powertrain": dict(value="ICE", status="CONFIRMED"),
            "fuel_combined": dict(value=fuel, status="CONFIRMED", unit="L/100km"),
        },
    )


def test_ranking_uses_only_requested_measurable_preferences():
    items = [ranked(150), ranked(250)]
    buyer.apply_fit_ranking(items, BuyerFilters(priorities=["performance", "reliability"]), "ru")
    assert items[1]["ranking"]["score"] > items[0]["ranking"]["score"]
    assert items[1]["ranking"]["unsupported_priorities"] == ["reliability"]
    items[0]["facts"].pop("power_hp")
    buyer.apply_fit_ranking(items, BuyerFilters(priorities=["performance"]), "az")
    assert items[1]["ranking"]["score"] == items[0]["ranking"]["score"]
    assert items[1]["ranking"]["unsupported_priorities"] == ["performance"]


def test_ranking_never_compares_different_consumption_cycles():
    items = [ranked(150, cycle="EPA", fuel=6), ranked(150, cycle="WLTP", fuel=8)]
    buyer.apply_fit_ranking(items, BuyerFilters(priorities=["cost"]), "ru")
    assert items[0]["ranking"]["score"] == items[1]["ranking"]["score"]
    assert not items[0]["ranking"]["supported_priorities"]


@pytest.mark.parametrize("language", ["ru", "az"])
def test_profile_categories_keep_fact_provenance_without_invented_octane_or_acceleration(
    db_session, proof, language
):
    actor, base, value = proof
    apply(db_session, actor, seated(value))
    c = copy.deepcopy(base.specifications["catalog"])
    c["facts"]["acceleration_0_60_mph_s"] = {"value": 6.5, "status": "CONFIRMED"}
    c["facts"]["fuel_grade"] = {"value": "Regular Gasoline", "status": "CONFIRMED"}
    p = buyer.vehicle_profile(c, language)
    assert [x["key"] for x in p["categories"]] == [
        "technical",
        "weak_points",
        "campaigns",
        "inspection",
    ]
    assert len(p["technical"]) == 10
    assert "fluids" not in {group["key"] for group in p["technical"]}
    summary = {r["key"]: r for r in p["summary"]}
    assert "acceleration_0_100_s" not in summary
    assert not {"octane_ron", "octane_aki"} & summary.keys()
    assert summary["seats"]["source_url"] == "https://example.test/factory"
    assert not p["categories"][1]["entries"]
