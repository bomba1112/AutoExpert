"""Read-only cache, provenance and prior-fact guards for factory batch mapping."""

import hashlib
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import scripts.factory_bulk_table_enrich as factory_bulk

SHEET = (
    b'<table class="specifications-table">'
    b'<tr class="specifications-table__header"><th></th><th>Base</th><th>Sport</th></tr>'
    b'<tr><td colspan="3">Exterior Dimensions</td></tr>'
    b'<tr><td>Length (in.)</td><td colspan="2">172.6 in.</td></tr>'
    b"</table>"
)


def test_cache_cold_warm_and_corruption_reparse(monkeypatch, tmp_path: Path):
    source = tmp_path / ".localdata/verified-source-documents"
    source.mkdir(parents=True)
    digest = hashlib.sha256(SHEET).hexdigest()
    (source / digest).write_bytes(SHEET)
    monkeypatch.setattr(factory_bulk, "ROOT", tmp_path)
    monkeypatch.setattr(factory_bulk, "CACHE", tmp_path / ".localdata/factory-bulk-cache")
    doc = SimpleNamespace(sha256=digest)
    counts = Counter()
    cold = factory_bulk._load_table(doc, counts)
    assert counts["documents_parsed"] == 1
    assert factory_bulk._load_table(doc, counts) == cold
    assert counts["cache_hits"] == 1
    cache = next(factory_bulk.CACHE.glob("*.json"))
    cache.write_text(cache.read_text().replace("172.6", "999.9"), encoding="utf-8")
    assert factory_bulk._load_table(doc, counts) == cold
    assert counts["cache_invalidated"] == 1
    assert counts["documents_parsed"] == 2


def test_existing_equivalent_alias_is_not_a_new_fact():
    assert factory_bulk._alias_evidence(
        {"facts": {"factory_length": {"status": "CONFIRMED", "value": "172.6 in."}}},
        "length_in",
        172.6,
    ) == "SAME"
    assert factory_bulk._alias_evidence(
        {"facts": {"fuel_tank_l": {"status": "CONFIRMED", "value": 45}}},
        "fuel_tank_us_gal",
        11.9,
    ) == "SAME"
    assert factory_bulk._alias_evidence(
        {"facts": {"factory_length": {"status": "CONFIRMED", "value": "179.5 in."}}},
        "length_in",
        172.6,
    ) == "CONFLICT"


def test_source_scope_is_only_known_annual_us_specification_path():
    assert factory_bulk._URL.fullmatch(
        "https://www.kiamedia.com/us/en/models/forte/2017/specifications"
    )
    assert not factory_bulk._URL.fullmatch(
        "https://www.kiamedia.com/ca/en/models/forte/2017/specifications"
    )
    assert not factory_bulk._URL.fullmatch(
        "https://www.kiamedia.com/us/en/models/forte/2017/specifications?model=2020"
    )

