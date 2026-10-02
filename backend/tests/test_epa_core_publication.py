"""An actual EPA-style publication reaches CORE without acquiring factory status."""

# ruff: noqa: F811

from app.models.knowledge_ops import SourceRegistry
from app.schemas.knowledge import BuyerFilters, ImportManifest
from app.services import catalog_buyer as buyer
from app.services.catalog_verification import (
    base_catalog_ready,
    identity_verified,
    source_confirmed_core_ready,
)
from app.services.knowledge_import import (
    enqueue,
    epa_record,
    process_job,
    publish_job,
    review_job,
)
from test_published_knowledge import editorial  # noqa: F401


def test_epa_annual_core_is_visible_without_generation_body_or_seats(db_session, editorial):
    _, actor = editorial
    db_session.add(
        SourceRegistry(
            id="epa",
            title="Isolated EPA source fixture",
            state="APPROVED",
            config={"commercial_reuse": True, "cost_model": "FREE"},
        )
    )
    db_session.commit()
    record = epa_record(
        {
            "id": "999999",
            "make": "Test make",
            "baseModel": "Test model",
            "model": "Test model",
            "year": "2020",
            "fuelType1": "Regular Gasoline",
            "displ": "2.0",
            "trany": "Automatic (S6)",
            "drive": "Front-Wheel Drive",
            "VClass": "Compact Cars",
        }
    )
    job = enqueue(
        db_session,
        ImportManifest(
            source_id="epa",
            parser="manifest-json-v1",
            records=[record],
            selection_basis="Isolated EPA CORE publication test only",
        ),
    )
    process_job(db_session, job.id)
    review_job(db_session, job, actor, note="Reviewed isolated CORE fixture", approve=True)
    publish_job(db_session, job, actor, note="Publish isolated CORE fixture")

    variant, catalog = next(
        (variant, catalog)
        for variant, catalog in buyer.records(db_session)
        if catalog["source_registry_id"] == "epa"
    )
    assert source_confirmed_core_ready(catalog)
    assert not base_catalog_ready(catalog) and not identity_verified(catalog)
    assert catalog["generation"] is None
    assert "body" not in catalog["facts"] and "seats" not in catalog["facts"]
    assert "engine_description" not in catalog["facts"]

    for lang in ("az", "ru"):
        base = buyer.search(db_session, BuyerFilters(catalog_scope="US_BASE_2000"), lang)
        assert [item["id"] for item in base["matches"]] == [variant.id]
        assert base["matches"][0]["generation"] is None
        assert base["matches"][0]["source_confirmed_core"]
        assert not buyer.search(
            db_session, BuyerFilters(catalog_scope="US_CONFIRMED_2000"), lang
        )["matches"]
        assert buyer.search(
            db_session,
            BuyerFilters(catalog_scope="US_BASE_2000", transmission="AUTOMATIC_UNSPECIFIED"),
            lang,
        )["matches"]
        for exact in ("AT", "CVT", "DCT"):
            assert not buyer.search(
                db_session, BuyerFilters(catalog_scope="US_BASE_2000", transmission=exact), lang
            )["matches"]
        assert not buyer.search(
            db_session, BuyerFilters(catalog_scope="US_BASE_2000", body=["SEDAN"]), lang
        )["matches"]
    resolved = buyer.resolve(
        db_session,
        {"catalog_scope": "US_BASE_2000", "make": "Test make", "model": "Test model", "year": 2020},
    )
    assert [candidate["id"] for candidate in resolved["candidates"]] == [variant.id]
    assert not buyer.resolve(
        db_session,
        {"catalog_scope": "US_CONFIRMED_2000", "make": "Test make", "year": 2020},
    )["candidates"]
