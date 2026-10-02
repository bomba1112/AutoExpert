"""Data-quality gates for the US technical database (prompt section 9), shared by all makes.

The staging sets in data_work/<make>/staging/<line>/staging.json are tracked in git and are
exactly what scripts/load_us_tech_facts.py writes, so the gates run without the live DB.
The loader itself is exercised on an in-memory database with a tiny synthetic staging set.
"""

from __future__ import annotations

import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel
from app.models.enums import ScopeLevel
from app.models.evidence import KnownIssue, TechnicalEvidence
from app.models.knowledge_ops import SourceRegistry
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[2]
STAGING = sorted(ROOT.glob("data_work/*/staging/*/staging.json"))
YEARS = range(2014, 2027)
DISPLAY = {"FACT", "SECONDARY_NOTE", "OWNER_REPORTS", "HIDDEN_CONFLICT"}


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = _load_module("build_us_tech_staging", ROOT / "scripts" / "build_us_tech_staging.py")
loader = _load_module("load_us_tech_facts", ROOT / "scripts" / "load_us_tech_facts.py")


def _staging():
    if not STAGING:
        pytest.skip("no staging sets yet")
    return [json.loads(p.read_text(encoding="utf-8")) for p in STAGING]


def test_staging_has_no_validation_errors():
    for staging in _staging():
        assert staging["errors"] == [], staging["line"]


def test_every_technical_fact_has_evidence():
    for staging in _staging():
        for fact in staging["facts"]:
            assert fact["cites"], fact["id"]
            for cite in fact["cites"]:
                assert cite["source"] in staging["sources"] and cite["quote"].strip(), fact["id"]
            assert fact["display_level"] in DISPLAY
        for issue in staging["issues"]:
            assert any(
                issue["evidence"].get(k) for k in ("recalls", "tsbs", "complaint_patterns")
            ), issue["id"]


def test_every_configuration_has_engine_transmission_and_drive():
    for staging in _staging():
        gap_scopes = {g["scope"] for g in staging["gaps"] if g["field"] == "engine_family_key"}
        for cfg in staging["configurations"]:
            assert cfg["drivetrain"] in {"FWD", "RWD", "AWD", "4WD"}, cfg["configuration_key"]
            assert cfg["epa_trany"], cfg["configuration_key"]
            assert Decimal(cfg["displacement_l"]) > 0 and cfg["cylinders"] > 0
            # Engine code only when a source confirms it; otherwise an explicit gap entry.
            assert cfg["engine_family_key"] or cfg["configuration_key"] in gap_scopes


def test_generation_years_cover_scope_without_gaps():
    for staging in _staging():
        covered = set()
        for gen in staging["generations"]:
            covered.update(range(gen["start_year"], gen["end_year"] + 1))
        assert set(YEARS) <= covered, staging["line"]
        for cfg in staging["configurations"]:
            assert cfg["generation"], cfg["configuration_key"]


def test_only_us_market_records():
    for staging in _staging():
        assert staging["market"] == "US"
        for item in staging["sources"].values():
            if item["source_type"] == "OWNER_MANUAL_COPY":
                assert item.get("edition") == "US", item["key"]


def test_numeric_values_within_validator_ranges():
    for staging in _staging():
        for fact in staging["facts"]:
            if fact["key"] in builder.RANGES and isinstance(fact["value"], (int, float)):
                low, high = builder.RANGES[fact["key"]]
                assert low <= fact["value"] <= high, (fact["id"], fact["value"])


def test_issue_probability_follows_the_rule():
    for staging in _staging():
        for issue in staging["issues"]:
            pattern = any(
                n >= builder.COMPLAINT_PATTERN_THRESHOLD for n in issue["complaints_in_years"] or []
            )
            tsb = bool(issue["evidence"].get("tsbs"))
            expected = "COMMON" if pattern and tsb else "OCCASIONAL" if pattern or tsb else "RARE"
            assert issue["probability"] == expected, issue["id"]
            assert issue["severity"] in {"LOW", "MEDIUM", "HIGH"}


def _synthetic_staging(tmp_path):
    raw = tmp_path / "raw.txt"
    raw.write_text("Overall length 189.2 in. (4805 mm)", encoding="utf-8")
    rel = raw.relative_to(tmp_path).as_posix()
    source = {
        "key": "om-2014",
        "kind": "txt",
        "path": rel,
        "url": "https://example.test/om.pdf",
        "sha256": "",
        "retrieved_at": "2026-10-02T00:00:00+00:00",
        "tier": "B",
        "source_type": "OWNER_MANUAL_COPY",
        "title": "test manual",
        "publisher": "test",
        "authenticity": "REVIEWED_MIRROR",
        "edition": "US",
    }
    return {
        "make": "Toyota",
        "line": "Camry",
        "market": "US",
        "errors": [],
        "sources": {"om-2014": source},
        "generations": [
            {"code": "VII", "start_year": 2012, "end_year": 2017, "open_ended": False},
            {
                "code": "IX",
                "name": "IX test",
                "start_year": 2025,
                "end_year": 2026,
                "open_ended": True,
            },
        ],
        "facts": [
            {
                "id": "camry-VII-0",
                "generation": "VII",
                "key": "length_mm",
                "level": "GENERATION",
                "engine": None,
                "gen_bound": True,
                "years": [2014, 2014],
                "value": 4805,
                "unit": "mm",
                "original": "189.2 in. (4805 mm)",
                "applicability": {},
                "note": None,
                "cites": [
                    {
                        "source": "om-2014",
                        "pages": [1],
                        "quote": "Overall length 189.2 in. (4805 mm)",
                        "tier": "B",
                        "publisher": "test",
                    }
                ],
                "display_level": "SECONDARY_NOTE",
                "confidence": "MEDIUM",
                "primary_source": "om-2014",
            }
        ],
        "configurations": [],
        "recalls": [],
        "tsbs": [],
        "symptom_patterns": {},
        "issues": [],
    }


def test_loader_writes_scoped_rows_once_and_never_overwrites(db_session, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(loader, "ROOT", tmp_path)
    monkeypatch.setattr(get_settings(), "knowledge_data_dir", str(tmp_path / "store"))
    make = VehicleMake(name="Toyota", normalized_name="toyota")
    db_session.add(make)
    db_session.flush()
    model = VehicleModel(make_id=make.id, name="Camry", normalized_name="camry")
    db_session.add(model)
    db_session.flush()
    db_session.add(VehicleGeneration(model_id=model.id, name="VII sedan", code="VII"))
    db_session.add(
        VehicleGeneration(
            model_id=model.id,
            name="demo",
            code="XV70",
            start_year=2017,
            end_year=2024,
            is_demo=True,
        )
    )
    db_session.add(
        SourceRegistry(id="factory-toyota-us", title="t", config={}, state="LOCAL_RESEARCH")
    )
    db_session.flush()
    staging = _synthetic_staging(tmp_path)

    for run in range(2):
        report = {"generations": [], "conflicts": [], "existing_vs_new": [], "stale": []}
        run_loader = loader.Loader(db_session, staging, "Camry", report)
        run_loader.load_sources()
        run_loader.load_generations()
        run_loader.load_facts()
        db_session.flush()
        if run == 0:
            assert run_loader.counts["te_new_GENERATION"] == 1
        else:
            assert run_loader.counts["te_existing"] == 1 and not report["conflicts"]

    gens = {g.code: g for g in db_session.scalars(select(VehicleGeneration))}
    assert (gens["VII"].start_year, gens["VII"].end_year) == (2012, 2017)
    assert gens["IX"].end_year is None and gens["IX"].start_year == 2025
    assert (gens["XV70"].start_year, gens["XV70"].end_year) == (2017, 2024)
    row = db_session.scalar(
        select(TechnicalEvidence).where(TechnicalEvidence.fact_key == "length_mm")
    )
    assert row.vehicle_variant_id is None and row.scope_level == ScopeLevel.GENERATION
    assert row.market == "US" and row.locator == "page 1" and row.source_id
    assert db_session.scalar(select(func.count()).select_from(KnownIssue)) == 0

    staging["facts"][0]["value"] = 4806  # a changed value must not overwrite the stored one
    report = {"generations": [], "conflicts": [], "existing_vs_new": [], "stale": []}
    changed = loader.Loader(db_session, staging, "Camry", report)
    changed.load_sources()
    changed.load_generations()
    changed.load_facts()
    assert (
        db_session.scalar(
            select(TechnicalEvidence.value).where(TechnicalEvidence.fact_key == "length_mm")
        )
        == 4805
    )
