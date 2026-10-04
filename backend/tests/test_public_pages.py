# ruff: noqa: E501
"""Public car pages (product phase, stage 5): one page per generation and engine in EN / RU / AZ,
only displayable data (hidden conflicts never, secondary data marked), no quotations from manuals,
hreflang, schema.org Vehicle + FAQPage, sitemap, the garage link, and the flag."""

from __future__ import annotations

import json
import re

import pytest
from app.core.config import get_settings
from app.services import public_pages, us_tech_facts
from tests.test_us_tech_facts import ICE, camry, generation  # noqa: F401


@pytest.fixture
def site(camry, db_session, tmp_path):  # noqa: F811
    us_tech_facts.clear_cache()
    groups = public_pages.groups(db_session)
    pages = []
    for group in groups:
        by_language = {lang: public_pages.merge(group, {c["key"]: us_tech_facts.build(db_session, c["key"], lang) for c in group["configs"]})
                       for lang in public_pages.LANGUAGES}
        pages.append((group, by_language))
    stats = public_pages.write_site(tmp_path, pages, "https://autoexpert.example", "https://app.autoexpert.example/")
    us_tech_facts.clear_cache()
    return tmp_path, groups, stats


def _page(root, language, group):
    return (root / "cars" / language / group["path"] / "index.html").read_text(encoding="utf-8")


def test_one_page_per_generation_and_engine_in_three_languages(site):
    root, groups, stats = site
    assert [g["engine"] for g in groups] == ["2.5L A25A-FKS", "2.5L A25A-FXS Hybrid"]
    assert groups[0]["path"] == "toyota/camry/xv70-2020-2020/2-5l-a25a-fks"
    for language in public_pages.LANGUAGES:
        for group in groups:
            assert (root / "cars" / language / group["path"] / "index.html").exists()
        assert (root / "cars" / language / "toyota" / "camry" / "index.html").exists()
    assert stats["pages"] == 6


def test_only_displayable_data_and_no_quotations(site):
    root, groups, _ = site
    page = _page(root, "en", groups[0])
    assert "15.9 gal (60.6 L)" in page or "16 gal (60.6 L)" in page
    assert "59.8" not in page  # HIDDEN_CONFLICT never
    assert "per reference sources" in page  # the SECONDARY_NOTE oil viscosity is marked
    assert "q fuel_tank_l" not in page and "page 541" not in page  # values and the source's name only
    assert "2020 Camry Owner&#x27;s Manual" in page or "2020 Camry Owner's Manual" in page
    assert "Spark plugs" not in page.split('id="maintenance"')[-1].split("</section>")[0]  # the hidden maintenance row


def test_seo_markup(site):
    root, groups, _ = site
    for language in public_pages.LANGUAGES:
        page = _page(root, language, groups[0])
        assert f'<html lang="{language}">' in page
        assert set(re.findall(r'rel="alternate" hreflang="([^"]+)"', page)) == {"en", "ru", "az", "x-default"}
        assert f'<link rel="canonical" href="https://autoexpert.example/cars/{language}/{groups[0]["path"]}/">' in page
        blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
        assert [b["@type"] for b in blocks] == ["Vehicle", "FAQPage"]
        assert blocks[0]["brand"]["name"] == "Toyota" and blocks[0]["vehicleEngine"]["name"] == "2.5L A25A-FKS"
        assert re.search(r'<meta name="description" content="[^"]{40,}">', page)
        assert "https://app.autoexpert.example/#/garage-add" in page  # the garage block
    ru = _page(root, "ru", groups[0])
    assert "Известные проблемы" in ru and "Добавьте свою машину в гараж" in ru
    sitemap = (root / "cars" / "sitemap.xml").read_text(encoding="utf-8")
    assert f"https://autoexpert.example/cars/az/{groups[0]['path']}/" in sitemap and 'hreflang="ru"' in sitemap
    assert "Sitemap: https://autoexpert.example/cars/sitemap.xml" in (root / "robots.txt").read_text(encoding="utf-8")


def test_applicability_collapses_into_ranges():
    configs = [{"year": y, "drive": d, "transmission": "A8"} for y in (2018, 2019, 2020) for d in ("FWD", "AWD")]
    variants = [public_pages._variant(c, configs) for c in configs if c["drive"] == "FWD"]
    assert public_pages._applies(variants, {2018, 2019, 2020}) == "FWD"
    assert public_pages._applies([(2018, "FWD"), (2019, "FWD"), (2021, "FWD")], {2018, 2019, 2020, 2021}) == "2018–2019, 2021 · FWD"


def test_flag():
    settings = get_settings()
    original = settings.public_car_pages, settings.environment
    try:
        settings.public_car_pages, settings.environment = None, "production"
        assert not public_pages.enabled(settings)
        settings.environment = "development"
        assert public_pages.enabled(settings)
        settings.public_car_pages = False
        assert not public_pages.enabled(settings)
    finally:
        settings.public_car_pages, settings.environment = original


def test_no_page_without_data(db_session, tmp_path):
    group = {"make": "X", "model": "Y", "generation": "G", "generation_id": "g", "engine": "1.0L", "years": (2020, 2020),
             "path": "x/y/g-2020-2020/1-0l", "configs": []}
    empty = {"fluids": [], "maintenance": [], "issues": [], "recalls": [], "versions": [], "sources": [], "labels": {}}
    stats = public_pages.write_site(tmp_path, [(group, dict.fromkeys(public_pages.LANGUAGES, empty))], "https://x.example", "https://x.example/")
    assert stats["pages"] == 0 and not (tmp_path / "cars" / "en" / "x").exists()
