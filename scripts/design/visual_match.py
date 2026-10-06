# ruff: noqa: E501
"""Side-by-side "reference | our screen" for the visual-match pass: one PNG per screen in
data_work/ui/visual_match/<screen>.png (the reference crop on the left, our screen at the same
390 px width on the right), plus the full page of ours as <screen>_full.png.

The preview runs on :8020 (scripts/dev_server.py). Cars are popular models of our base (Toyota
Camry, Hyundai Sonata, Honda Accord, ...), not the Kia example of the owner's message.

  uv run --no-project --with playwright --with pillow python scripts/design/visual_match.py [base_url] [round]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
CROPS = ROOT / "design" / "reference" / "crops"
OUT = ROOT / "data_work" / "ui" / "visual_match"
W, H, SCALE = 390, 844, 2
FILTERS = {"catalog_scope": "US_BASE_2000", "catalog_ready_only": True, "market_preference": "SELECTED", "markets": ["US"], "year_min": 2017,
           "year_max": 2017, "body": [], "engine": "GASOLINE_NA", "transmission": "AT", "makes": [], "models": [], "roads": [], "priorities": [],
           "monthly_km": 1000, "ownership_months": 24, "city": "", "charging": "UNKNOWN", "sort": "recommended", "origin": "KR"}


def call(page, method, path, body=None):
    return page.evaluate(
        """async ([method, path, body]) => {
            const token = localStorage.getItem('autoexpert.demo.token');
            const r = await fetch('/api/v1' + path, {method, headers: {'Content-Type': 'application/json', 'X-AutoExpert-Token': token || ''},
                                                    body: body ? JSON.stringify(body) : undefined});
            if (!r.ok) throw new Error(method + ' ' + path + ' ' + r.status);
            return r.status === 204 ? null : r.json();
        }""", [method, path, body])


def variant(page, make, model, year, need=None):
    body = {k: v for k, v in FILTERS.items() if k != "origin"} | {"engine": "ANY", "transmission": "ANY", "makes": [make], "models": [model],
                                                                  "year_min": year, "year_max": year, "limit": 30}
    matches = call(page, "POST", "/knowledge/search?language=ru", body)["matches"]
    plain = lambda v: 0 if (v.get("facts", {}).get("fuel") or {}).get("value") == "GASOLINE" and (v.get("facts", {}).get("powertrain") or {}).get("value") == "ICE" else 1  # noqa: E731
    disp = lambda v: float(((v.get("facts") or {}).get("engine_displacement") or {}).get("value") or 99)  # noqa: E731
    matches.sort(key=lambda v: (bool(v.get("preview")), plain(v), disp(v)))
    for v in matches:
        if not need:
            return v["id"]
        try:
            tech = call(page, "GET", f"/catalog/variants/{v['id']}/us-tech?language=ru")
        except Exception:
            continue
        if any(c["key"] == need for c in tech.get("categories", [])):
            return v["id"]
    raise SystemExit(f"no {make} {model} {year} with {need}")


def go(page, base, route, selector, timeout=180000):
    page.goto(f"{base}/preview/#/{route}")
    page.reload()  # a hash change alone does not re-read the saved filters
    page.wait_for_selector(selector, timeout=timeout)
    page.wait_for_timeout(700)


def pair(name, ref_name, page, label):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f"_{name}.png"
    page.screenshot(path=str(tmp))
    page.screenshot(path=str(OUT / f"{name}_full.png"), full_page=True)
    ours = Image.open(tmp).convert("RGB")
    tmp.unlink()
    ref = Image.open(CROPS / f"{ref_name}.png").convert("RGB") if ref_name else None
    width = W * SCALE
    ours = ours.resize((width, round(ours.height * width / ours.width)))
    if ref:
        ref = ref.resize((width, round(ref.height * width / ref.width)), Image.LANCZOS)
    height = max(ours.height, ref.height if ref else 0) + 40
    canvas = Image.new("RGB", (width * (2 if ref else 1) + (24 if ref else 0), height), "white")
    d = ImageDraw.Draw(canvas)
    x = 0
    if ref:
        canvas.paste(ref, (0, 40))
        d.text((10, 12), f"REFERENCE: {ref_name}", fill=(0, 0, 0))
        x = width + 24
    canvas.paste(ours, (x, 40))
    d.text((x + 10, 12), f"OURS: {label}", fill=(0, 0, 0))
    canvas.save(OUT / f"{name}.png", optimize=True)


def main(base: str, rnd: str) -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=SCALE, locale="ru-RU")
        ctx.add_init_script("localStorage.setItem('autoexpert.ui.language', 'ru'); localStorage.removeItem('autoexpert.ui.region');")
        page = ctx.new_page()
        go(page, base, "home", ".ae-battle")
        pair("home", "home", page, f"home RU / AZ · round {rnd}")
        page.evaluate("""f => localStorage.setItem('autoexpert.catalog.buyer.v1', JSON.stringify({filters: f, basket: []}))""",
                      {**FILTERS, "body": ["SEDAN"], "year_min": 2018, "year_max": 2022, "budget_max_minor": 2000000})
        go(page, base, "pick", "#catalog-wizard")
        pair("podbor", "podbor", page, f"selection · round {rnd}")
        page.evaluate("""f => localStorage.setItem('autoexpert.catalog.buyer.v1', JSON.stringify({filters: f, basket: []}))""", FILTERS)
        go(page, base, "catalog-results", ".model-card")
        pair("results", "results", page, f"matching cars · round {rnd}")
        camry = variant(page, "Toyota", "Camry", 2019)
        go(page, base, f"catalog-car/{camry}", ".car-tabs")
        pair("car_card", "car_card", page, f"Toyota Camry 2019 · round {rnd}")
        page.evaluate("document.querySelector('.car-tabs').scrollIntoView({block: 'start'}); window.scrollBy(0, -60)")
        page.wait_for_timeout(300)
        pair("tech_categories", "tech_categories", page, f"technical part · round {rnd}")
        oils = variant(page, "Toyota", "Camry", 2017, need="fluids")
        go(page, base, f"catalog-car/{oils}/fluids", ".fluid-block")
        pair("oil_fluids", "oil_fluids", page, f"Camry 2017 oils and fluids · round {rnd}")
        go(page, base, "home", ".ae-battle")
        page.click(".ae-battle")
        page.wait_for_selector(".vs-head", timeout=240000)
        page.wait_for_timeout(700)
        pair("compare", "compare", page, f"Camry vs Accord · round {rnd}")
        go(page, base, "check", "#expert-check")
        pair("check", "home_dark", page, f"check screen · round {rnd}")
        page.evaluate("""b => sessionStorage.setItem('autoexpert.expert.request', JSON.stringify(b))""", {"query": "4T1B11HK5KU000000"})
        page.goto(f"{base}/preview/#/home")
        page.goto(f"{base}/preview/#/opinion")
        page.wait_for_selector(".ae-verdict, .ae-warn-card", timeout=240000)
        page.wait_for_timeout(700)
        pair("opinion", None, page, f"opinion by VIN (Camry 2019) · round {rnd}")
        ctx.close()
        # EN / region US home
        ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=SCALE, locale="en-US")
        ctx.add_init_script("localStorage.setItem('autoexpert.ui.language', 'en'); localStorage.removeItem('autoexpert.ui.region');")
        page = ctx.new_page()
        go(page, base, "home", ".ae-battle")
        pair("home_en", "home", page, f"home EN / US · round {rnd}")
        ctx.close()
        browser.close()
    print("written to", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8020", sys.argv[2] if len(sys.argv) > 2 else "1"))
