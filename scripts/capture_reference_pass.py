# ruff: noqa: E501
"""Screenshot pairs "reference / our screen" for the UI-by-reference pass (prompt section 5):
home, selection, matching cars, car card, technical categories, engine -> oils and fluids, compare,
the Auto Expert opinion on the Turbo.az Stinger link and on a manual input
and the garage, in RU (region AZ) and EN (region US).

The preview must run with the development flags (expert_opinion_v1, us tech facts, garage). Each
listing page is fetched once by the server and kept a day (provider cache), so RU and EN share it.
The garage car made for the picture is deleted afterwards.

  uv run --no-project --with playwright --with pillow python scripts/capture_reference_pass.py [base_url]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_work" / "ui" / "screens" / "reference_pass"
REF = ROOT / "design" / "reference"
HIDE = ".developer-drawer{display:none!important}"
# owner 2026-10-06: the opinion by link is checked on the Stinger link only
LISTINGS = {"stinger": "https://turbo.az/autos/10556520-kia-stinger"}
CARD_QUERY = {"makes": ["Hyundai"], "models": ["Sonata"], "year": 2017}
OILS_QUERY = {"makes": ["Toyota"], "models": ["Camry"], "year": 2017, "fluids": True}
GARAGE_CAR = "toyota-camry-us-2020-2.5l-4cyl-ice-a-s8-fwd"
# phone crops of the reference images: (file, box)
PHONES = {
    "home": ("01_approved_home_podbor_results.png", (14, 0, 504, 1024)),
    "selection": ("01_approved_home_podbor_results.png", (522, 0, 1012, 1024)),
    "results": ("01_approved_home_podbor_results.png", (1028, 0, 1522, 1024)),
    "results_list": ("04_found_cars_list.png", None),
    "card": ("02_car_card_tech_oil.png", (52, 0, 530, 941)),
    "card_technical": ("02_car_card_tech_oil.png", (586, 0, 1084, 941)),
    "oils_fluids": ("02_car_card_tech_oil.png", (1140, 0, 1626, 941)),
    "compare": ("03_compare_verdict_podbor.png", (522, 0, 1012, 1024)),
    "check": ("03_compare_verdict_podbor.png", (12, 0, 504, 1024)),
}
FILTERS = {"catalog_scope": "US_BASE_2000", "catalog_ready_only": True, "market_preference": "SELECTED", "markets": ["US"], "year_min": 2017,
           "year_max": 2017, "body": [], "engine": "GASOLINE_NA", "transmission": "AT", "makes": [], "models": [], "roads": [], "priorities": [],
           "monthly_km": 1000, "ownership_months": 24, "city": "", "charging": "UNKNOWN", "sort": "recommended", "origin": "KR"}


def call(page, method, path, body=None):
    return page.evaluate(
        """async ([method, path, body]) => {
            const token = localStorage.getItem('autoexpert.demo.token');
            const r = await fetch('/api/v1' + path, {method, headers: {'Content-Type': 'application/json', 'X-AutoExpert-Token': token || ''},
                                                    body: body ? JSON.stringify(body) : undefined});
            if (!r.ok) throw new Error(method + ' ' + path + ' ' + r.status + ' ' + await r.text());
            return r.status === 204 ? null : r.json();
        }""", [method, path, body])


def first_variant(page, query, lang):
    body = {**FILTERS, "engine": "ANY", "transmission": "ANY", "origin": None, "makes": query["makes"], "models": query["models"],
            "year_min": query["year"], "year_max": query["year"], "limit": 30}
    body.pop("origin")
    data = call(page, "POST", f"/knowledge/search?language={lang}", body)
    matches = sorted(data["matches"], key=lambda v: (bool(v.get("preview")), float((v.get("facts", {}).get("engine_displacement") or {}).get("value") or 99)))
    if not query.get("fluids"):
        return matches[0]["id"]
    for v in matches:  # the first version whose technical card has oils and fluids
        try:
            tech = call(page, "GET", f"/catalog/variants/{v['id']}/us-tech?language={lang}")
        except Exception:
            continue
        if any(c["key"] == "fluids" for c in tech.get("categories", [])):
            return v["id"]
    raise SystemExit("no version with oils and fluids")


def go(page, base, route, selector, timeout=180000):
    page.goto(f"{base}/preview/#/{route}")
    page.wait_for_selector(selector, timeout=timeout)
    page.add_style_tag(content=HIDE)
    page.wait_for_timeout(500)


def shoot(page, name, lang, full=False):
    path = OUT / f"ours_{name}_{lang}.png"
    if full:  # the fixed bottom menu would cover the middle of a long page
        page.add_style_tag(content=".bottom-nav{position:static!important}.catalog-sticky{position:static!important}")
        page.wait_for_timeout(200)
    page.screenshot(path=str(path), full_page=full)
    return path


def pair(name, lang, ours: Path):
    jpg = OUT / f"ours_{name}_{lang}.jpg"
    ours_img = Image.open(ours).convert("RGB")
    ours_img.save(jpg, quality=85)
    ours.unlink()
    if name not in PHONES:
        return
    file, box = PHONES[name]
    ref = Image.open(REF / file).convert("RGB")
    if box:
        ref = ref.crop(box)
    height = 1000
    left = ref.resize((round(ref.width * height / ref.height), height))
    view = ours_img.crop((0, 0, ours_img.width, min(ours_img.height, round(ours_img.width * 2.2))))
    right = view.resize((round(view.width * height / view.height), height))
    canvas = Image.new("RGB", (left.width + right.width + 30, height), "white")
    canvas.paste(left, (0, 0))
    canvas.paste(right, (left.width + 30, 0))
    canvas.save(OUT / f"pair_{name}_{lang}.jpg", quality=85)


def main(base: str) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        for lang in ("ru", "en"):
            context = browser.new_context(viewport={"width": 412, "height": 900}, device_scale_factor=2,
                                          locale={"en": "en-US", "ru": "ru-RU"}[lang])
            context.add_init_script(f"localStorage.setItem('autoexpert.ui.language', '{lang}'); localStorage.removeItem('autoexpert.ui.region');")
            page = context.new_page()
            go(page, base, "home", ".home-battles .battle-card")
            pair("home", lang, shoot(page, "home", lang))
            pair("home_full", lang, shoot(page, "home_full", lang, full=True))
            # selection, with a few choices made
            page.evaluate("""f => localStorage.setItem('autoexpert.catalog.buyer.v1', JSON.stringify({filters: f, basket: []}))""",
                          {**FILTERS, "body": ["SEDAN"], "year_min": 2017, "year_max": 2020, **({"budget_max_minor": 2000000} if lang == "ru" else {"budget_usd": 20000})})
            go(page, base, "pick", "#catalog-wizard")
            pair("selection", lang, shoot(page, "selection", lang))
            pair("selection_full", lang, shoot(page, "selection_full", lang, full=True))
            # matching cars
            page.evaluate("""f => localStorage.setItem('autoexpert.catalog.buyer.v1', JSON.stringify({filters: f, basket: []}))""", FILTERS)
            go(page, base, "catalog-results", ".model-card")
            pair("results", lang, shoot(page, "results", lang))
            pair("results_list", lang, shoot(page, "results_list", lang, full=True))
            # the car card, its technical categories, engine -> oils and fluids
            card = first_variant(page, CARD_QUERY, lang)
            go(page, base, f"catalog-car/{card}", ".car-tabs")
            pair("card", lang, shoot(page, "card", lang))
            page.evaluate("document.querySelector('.car-tabs').scrollIntoView({block: 'start'})")
            page.wait_for_timeout(300)
            pair("card_technical", lang, shoot(page, "card_technical", lang))
            oils = first_variant(page, OILS_QUERY, lang)
            go(page, base, f"catalog-car/{oils}/fluids", ".fluid-block")
            pair("oils_fluids", lang, shoot(page, "oils_fluids", lang))
            # compare: the first curated battle
            go(page, base, "home", ".home-battles .battle-card")
            page.click("[data-k=battle-compare]")
            page.wait_for_selector(".vs-head", timeout=240000)
            page.add_style_tag(content=HIDE)
            pair("compare", lang, shoot(page, "compare", lang))
            pair("compare_full", lang, shoot(page, "compare_full", lang, full=True))
            # the check screen, the opinion on the Stinger link and on a manual input (an OK opinion)
            go(page, base, "check", "#expert-check")
            pair("check", lang, shoot(page, "check", lang))
            for key, url in LISTINGS.items():
                page.evaluate("""b => sessionStorage.setItem('autoexpert.expert.request', JSON.stringify(b))""", {"query": url})
                page.goto(f"{base}/preview/#/home")
                page.goto(f"{base}/preview/#/opinion")
                page.wait_for_selector(".ae-verdict, .ae-warn-card, .ae-error-card", timeout=240000)
                page.add_style_tag(content=HIDE)
                page.wait_for_timeout(500)
                pair(f"opinion_{key}", lang, shoot(page, f"opinion_{key}", lang, full=True))
            page.evaluate("""b => sessionStorage.setItem('autoexpert.expert.request', JSON.stringify(b))""",
                          {"manual": {"make": "Honda", "model": "Accord", "year": 2019, "engine": "1.5", "fuel": "Benzin", "transmission": "Variator", "mileage_km": 87000}})
            page.goto(f"{base}/preview/#/home")
            page.goto(f"{base}/preview/#/opinion")
            page.wait_for_selector(".ae-verdict", timeout=240000)
            page.add_style_tag(content=HIDE)
            page.wait_for_timeout(500)
            pair("opinion_manual", lang, shoot(page, "opinion_manual", lang, full=True))
            # the garage
            car = call(page, "POST", f"/garage/vehicles?language={lang}", {"configuration_key": GARAGE_CAR, "odometer": 87000, "monthly": 1200,
                                                                           "region": "AZ" if lang == "ru" else "US"})
            try:
                go(page, base, f"garage-car/{car['id']}", ".garage-summary")
                pair("garage", lang, shoot(page, "garage", lang, full=True))
            finally:
                call(page, "DELETE", f"/garage/vehicles/{car['id']}")
            context.close()
        browser.close()
    print(json.dumps(sorted(p.name for p in OUT.glob("*.jpg")), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8020"))
