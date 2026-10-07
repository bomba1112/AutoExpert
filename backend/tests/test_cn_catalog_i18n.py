"""CN catalogue texts RU -> AZ / EN: loaded into content_translations, shown by the card."""

from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest
from app.models.translations import ContentTranslation
from app.services import cn_catalog
from app.services.cn_catalog_load import CnLoader, read_staging, text_key, validate
from app.services.us_tech_facts import text_hash
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[2]
STAGING = read_staging(ROOT / "data_work/cn/staging", ROOT / "data_work/cn/model_map.json")
QIN = "cn:byd_qin-plus-dm-i_2023_18.32kwh-145kw"
CYRILLIC = re.compile(r"[А-Яа-яЁё]")


@pytest.fixture
def cn_db(db_session):
    CnLoader(db_session, STAGING).load()
    db_session.commit()
    return db_session


def test_snapshot_carries_both_languages_with_the_app_key():
    az, en = STAGING.translations["az"], STAGING.translations["en"]
    assert len(az) == len(en) == 510
    assert set(az) == set(en)
    for key, entry in az.items():
        assert key == text_key(entry["ru"]) == text_hash(entry["ru"])
        assert entry["status"] == "ok" and entry["kind"].startswith("cn_")
    assert STAGING.glossary["version"].startswith("cn-")
    assert validate(STAGING) == []


def test_validate_refuses_a_key_that_does_not_match_its_text():
    broken = copy.copy(STAGING)
    entries = dict(STAGING.translations["az"])
    key = next(iter(entries))
    entries[key] = {**entries[key], "ru": entries[key]["ru"] + " (изменено)"}
    broken.translations = {**STAGING.translations, "az": entries}
    assert any("does not match" in e for e in validate(broken))


def test_load_writes_one_row_per_text_and_is_idempotent(cn_db):
    rows = cn_db.scalars(
        select(ContentTranslation).where(ContentTranslation.kind.like("cn_%"))
    ).all()
    assert len(rows) == 510
    for row in rows:
        assert row.source_text == row.text_ru  # the Russian original
        assert row.text_az and row.text_en and not CYRILLIC.search(row.text_en)
        assert row.method == "llm" and row.status == "CHECKED"
        assert row.glossary_version == STAGING.glossary["version"]
    report = CnLoader(cn_db, STAGING).load()
    assert report.counts["translations_unchanged"] == 510
    assert not report.counts.get("translations_new") and not report.counts.get(
        "translations_updated"
    )


def test_card_in_azerbaijani_and_english(cn_db):
    ru = cn_catalog.build(cn_db, QIN, "ru")
    az = cn_catalog.build(cn_db, QIN, "az")
    en = cn_catalog.build(cn_db, QIN, "en")
    # Russian card unchanged: the catalogue's own texts
    assert [w["title"] for w in ru["weak_points"]] == [
        i["text"]
        for i in STAGING.records["byd_qin-plus-dm-i_2023_18.32kwh-145kw"]["known_issues_resolved"]
    ]
    assert ru["weak_points"][0]["origin"].startswith("гибридная система")
    for card, lang in ((az, "az"), (en, "en")):
        for w in card["weak_points"]:
            assert not CYRILLIC.search(w["title"]) and not CYRILLIC.search(w["origin"])
            assert w["original_language"] == lang
        assert not any(CYRILLIC.search(c["name"]) for c in card["components"])
        assert not CYRILLIC.search(card["status_china"] or "")
        assert not CYRILLIC.search(card["generation_label"] or "")
    assert en["weak_points"][0]["origin"].startswith("hybrid system BYD DM-i (4th-generation DM")
    assert "review of BYD Song PLUS DM-i" in en["weak_points"][0]["origin"]
    assert "üzrə rəy" in az["weak_points"][0]["origin"]
    fuel = next(r for c in en["categories"] for r in c["rows"] if r["key"] == "fuel_l_100km_cn")
    assert fuel["values"][0]["qualifier"] == "MIIT combined (including electric driving)"
    fuel_az = next(r for c in az["categories"] for r in c["rows"] if r["key"] == "fuel_l_100km_cn")
    assert fuel_az["values"][0]["qualifier"].startswith("MIIT, qarışıq dövr")
    assert en["labels"]["buyer_checks"] == "What to check when buying"


def test_buyer_checks_and_hybrid_system_translated(cn_db):
    slug, record = next((s, r) for s, r in STAGING.records.items() if r.get("buyer_checks"))
    key = f"cn:{slug}"
    en = cn_catalog.build(cn_db, key, "en")
    az = cn_catalog.build(cn_db, key, "az")
    assert len(en["buyer_checks"]) == len(record["buyer_checks"]) > 0
    assert not any(CYRILLIC.search(t) for t in en["buyer_checks"] + az["buyer_checks"])
    zeekr = cn_catalog.build(cn_db, "cn:zeekr_8x_2026_55kwh", "en")
    hybrid = next(
        r for c in zeekr["categories"] for r in c["rows"] if r["key"] == "hybrid_system_name"
    )
    assert not CYRILLIC.search(hybrid["values"][0]["value"])


def test_missing_translation_falls_back_to_the_russian_original(cn_db):
    text = STAGING.records["byd_qin-plus-dm-i_2023_18.32kwh-145kw"]["known_issues_resolved"][0][
        "text"
    ]
    row = cn_db.scalar(
        select(ContentTranslation).where(
            ContentTranslation.kind == "cn_issue", ContentTranslation.source_hash == text_hash(text)
        )
    )
    cn_db.delete(row)
    cn_db.commit()
    en = cn_catalog.build(cn_db, QIN, "en")
    first = en["weak_points"][0]
    assert first["title"] == text and first["original_language"] == "ru"
    count = cn_db.scalar(
        select(func.count())
        .select_from(ContentTranslation)
        .where(ContentTranslation.kind.like("cn_%"))
    )
    assert count == 509
