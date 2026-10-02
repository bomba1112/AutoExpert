"""Synthetic proof documents stay in isolated fixtures; no provider requests."""
# ruff: noqa: F811

import copy

import pytest
from app.models.knowledge_ops import SourceRegistry
from app.schemas.knowledge import CatalogRecord, ImportManifest
from app.services.catalog_buyer import coverage, projection, records, save_dossier
from app.services.catalog_verification import IDENTITY_FIELDS, dossier_full, identity_verified
from app.services.knowledge_import import (
    enqueue,
    process_job,
    publish_job,
    review_job,
    store_document,
)
from test_published_knowledge import editorial, published  # noqa: F401


@pytest.fixture
def proof(db_session, editorial, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "knowledge_data_dir", str(tmp_path))
    _, actor = editorial
    base = published(db_session, actor)[0]
    factory = SourceRegistry(
        id="factory-test",
        title="Synthetic official source",
        state="LOCAL_RESEARCH",
        config={"factory_identity_evidence": True, "commercial_reuse": False, "cost_model": "FREE"},
    )
    db_session.add(factory)
    db_session.flush()
    url = "https://example.test/factory"
    doc = store_document(db_session, factory.id, b"Synthetic factory evidence only", locator=url)
    reference = dict(
        registry_id=factory.id,
        document_id=doc.id,
        sha256=doc.sha256,
        url=url,
        locator="Isolated specifications table",
        make="Test make",
        model="Test model",
        market="US",
        model_year=2020,
    )
    c = base.specifications["catalog"]
    value = {k: v for k, v in c.items() if k in CatalogRecord.model_fields}
    value["facts"] = {
        k: {
            a: b
            for a, b in f.items()
            if a
            in {
                "value",
                "unit",
                "status",
                "locator",
                "labels",
                "titles",
                "source_date",
                "documentary_source",
            }
        }
        for k, f in c["facts"].items()
    }
    value.update(
        generation="Synthetic generation",
        identity_verification={
            "previous_revision_id": base.published_revision_id,
            "applicability": "Only this synthetic 2020 US fixture configuration.",
            "field_evidence": {k: [reference] for k in IDENTITY_FIELDS},
            "review_note": "Reviewed isolated factory document with exact fixture applicability.",
        },
    )
    for k, v in {
        "engine_description": "Synthetic 1.6 engine",
        "transmission_description": "6-speed AT",
        "transmission_family": "AT",
        "drivetrain": "FWD",
    }.items():
        value["facts"][k] = dict(value=v, locator="Isolated table", documentary_source=reference)
    value["documentary_sections"] = [
        {
            "key": "engine",
            "status": "EVIDENCED",
            "references": [reference],
            "text": {
                "ru": "Синтетический двигатель 1.6 для проверки связи с документом.",
                "az": "Sənədlə əlaqəni yoxlamaq üçün sintetik 1.6 mühərrik.",
            },
        }
    ]
    return actor, base, value


def apply(db, actor, value):
    job = enqueue(
        db,
        ImportManifest(
            source_id="test-source",
            parser="manifest-json-v1",
            records=[value],
            selection_basis="Synthetic verification only",
        ),
    )
    process_job(db, job.id)
    review_job(db, job, actor, note="Reviewed isolated proof", approve=True)
    publish_job(db, job, actor, note="Publish isolated proof")
    return job


def test_scoped_verification_keeps_sources_and_does_not_make_full(db_session, proof):
    actor, base, value = proof
    old_id = base.published_revision_id
    apply(db_session, actor, value)
    c = base.specifications["catalog"]
    assert identity_verified(c) and not dossier_full(c)
    assert c["verification_gate"]["state"] == "VERIFIED_SCOPED"
    assert base.published_revision_id != old_id
    assert c["facts"]["engine_description"]["source_id"] != c["facts"]["fuel_combined"]["source_id"]
    assert coverage(db_session)["verified_scoped_versions"] == 1
    assert coverage(db_session)["fully_supported_dossiers"] == 0
    for language in ("az", "ru"):
        section = next(s for s in projection(c, language).sections if s.key == "engine")
        assert section.paragraphs[0].evidence_ids and "1.6" in section.paragraphs[0].text
    altered = copy.deepcopy(c)
    altered["facts"]["drivetrain"]["value"] = "AWD"
    assert not identity_verified(altered)


@pytest.mark.parametrize(
    "defect,code",
    [
        ("market", "APPLICABILITY_MISMATCH"),
        ("hash", "DOCUMENT_MISMATCH"),
        ("stale", "BASE_REVISION_CHANGED"),
        ("conflict", "UNRESOLVED_IDENTITY_CONFLICT"),
        ("generation", "IDENTITY_EVIDENCE_INCOMPLETE"),
        ("missing_reference", "IDENTITY_EVIDENCE_INCOMPLETE"),
        ("transmission", "TRANSMISSION_CONSTRUCTION_UNRESOLVED"),
    ],
)
def test_incomplete_or_mismatched_proof_never_publishes(db_session, proof, defect, code):
    actor, base, value = proof
    old = base.published_revision_id
    if defect == "market":
        value["facts"]["engine_description"]["documentary_source"]["market"] = "CA"
    if defect == "hash":
        value["facts"]["engine_description"]["documentary_source"]["sha256"] = "0" * 64
    if defect == "stale":
        value["identity_verification"]["previous_revision_id"] = "other"
    if defect == "conflict":
        value["identity_verification"]["unresolved_conflicts"] = ["Engine conflict"]
    if defect == "generation":
        value["generation"] = None
    if defect == "missing_reference":
        value["identity_verification"]["field_evidence"].pop("generation")
    if defect == "transmission":
        value["facts"]["transmission_family"]["value"] = "AUTOMATIC_UNSPECIFIED"
    with pytest.raises(ValueError, match=code):
        apply(db_session, actor, value)
    assert base.published_revision_id == old and not identity_verified(
        base.specifications["catalog"]
    )


def test_factory_source_revocation_hides_mixed_source_record(db_session, proof):
    actor, _, value = proof
    apply(db_session, actor, value)
    assert len(records(db_session)) == 1
    db_session.get(SourceRegistry, "factory-test").paused = True
    db_session.commit()
    assert not records(db_session)


def test_saved_bilingual_dossier_keeps_all_document_sources(db_session, proof):
    actor, base, value = proof
    value["facts"]["engine_code"] = {**value["facts"]["engine_description"], "value": "TEST-CODE"}
    value["documentary_sections"].append(
        {
            "key": "recalls",
            "status": "PARTIAL",
            "references": value["documentary_sections"][0]["references"],
            "text": {
                "ru": "Синтетическая кампания; применимость к VIN не установлена.",
                "az": "Sintetik kampaniya; VIN-ə uyğunluq hələ müəyyən edilməyib.",
            },
        }
    )
    apply(db_session, actor, value)
    assert base.engine_code == "TEST-CODE"
    c = base.specifications["catalog"]
    report = save_dossier(db_session, actor, base, c, "az", {})
    saved = {s["id"] for s in report.evidence_bundle["sources"]}
    for language in ("az", "ru"):
        p = projection(c, language)
        assert set(p.source_ids) <= saved
        assert "generation" not in p.readiness.missing_requirements
        section = next(s for s in p.sections if s.key == "safety")
        assert len(section.paragraphs) == 1 and section.paragraphs[0].source_ids
    assert len(saved) == 2


def test_identity_only_document_source_is_also_revocable(db_session, proof):
    actor, _, value = proof
    extra = SourceRegistry(
        id="generation-test",
        title="Synthetic generation source",
        state="LOCAL_RESEARCH",
        config={"factory_identity_evidence": True},
    )
    db_session.add(extra)
    db_session.flush()
    doc = store_document(
        db_session,
        extra.id,
        b"Synthetic generation scope",
        locator="https://example.test/generation",
    )
    ref = copy.deepcopy(value["identity_verification"]["field_evidence"]["generation"][0])
    ref.update(registry_id=extra.id, document_id=doc.id, sha256=doc.sha256, url=doc.locator)
    value["identity_verification"]["field_evidence"]["generation"] = [ref]
    apply(db_session, actor, value)
    assert len(records(db_session)) == 1
    extra.paused = True
    db_session.commit()
    assert not records(db_session)
