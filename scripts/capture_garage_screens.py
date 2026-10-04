# ruff: noqa: E501
"""Screenshots of the Garage for the owner's review of stage 2 (product phase): EN, RU, AZ for
Camry 2020, Sonata 2018 and BMW 3 Series 2016 — the garage list, each car, the "My car" feed and
adding a car by VIN. The preview must run with garage_v1 on (development default), e.g. on :8010.

The cars are added through the API under a fresh demo session per language with the same owner
inputs (odometer, log, oil interval) and deleted afterwards. The VINs are synthetic (serial
000000, a valid check digit): only their pattern is decoded from the local vPIC database.

  uv run --no-project --with playwright --with pillow python scripts/capture_garage_screens.py [base_url]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_work" / "product" / "screens" / "stage2"
HIDE = ".bottom-nav{display:none!important}.developer-drawer{display:none!important}"
CARS = [
    {"name": "camry_2020", "vin": "4T1B11HK6LU000000", "configuration_key": "toyota-camry-us-2020-2.5l-4cyl-ice-a-s8-fwd",
     "odometer": 87000, "monthly": 1500, "region": "AZ",
     "history": [{"job": "engine_oil_and_filter", "status": "DONE", "performed_on": "2026-06-15", "odometer": 82500},
                 {"job": "transmission_fluid", "status": "UNKNOWN"}, {"job": "spark_plugs", "status": "UNKNOWN"}],
     "patch": {"oil_interval": 7000, "oil_interval_months": 6}},
    {"name": "sonata_2018", "vin": "5NPE24AF0JH000000", "configuration_key": "hyundai-sonata-us-2018-2.4l-4cyl-ice-a-s6-fwd",
     "odometer": 112000, "monthly": 1800, "region": "CIS",
     "history": [{"job": "spark_plugs", "status": "DONE", "performed_on": "2025-03-10", "odometer": 96000},
                 {"job": "engine_oil_and_filter", "status": "UNKNOWN"}],
     "patch": None},
    {"name": "bmw_3_series_2016", "vin": "WBA8E9G59GNU00000", "configuration_key": "bmw-3-series-us-2016-2.0l-4cyl-turbo-ice-a-s8-rwd",
     "odometer": 103000, "monthly": 1200, "region": "US",
     "history": [{"job": "brake_fluid", "status": "UNKNOWN"}, {"job": "cabin_air_filter", "status": "DONE", "performed_on": "2025-11-02", "odometer": 95000}],
     "patch": None, "onboard_reset": {"value": 99500, "read_on": "2026-05-20"}},
]


def call(page, method: str, path: str, body=None):
    return page.evaluate(
        """async ([method, path, body]) => {
            const token = localStorage.getItem('autoexpert.demo.token');
            const r = await fetch('/api/v1' + path, {method, headers: {'Content-Type': 'application/json', Authorization: 'Bearer ' + token},
                                                    body: body ? JSON.stringify(body) : undefined});
            if (!r.ok) throw new Error(method + ' ' + path + ' ' + r.status + ' ' + await r.text());
            return r.status === 204 ? null : r.json();
        }""", [method, path, body])


def shoot(page, path: Path) -> None:
    page.add_style_tag(content=HIDE)
    page.wait_for_timeout(400)
    page.screenshot(path=str(path), full_page=True)


def main(base: str) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        for language in ("en", "ru", "az"):
            context = browser.new_context(viewport={"width": 412, "height": 915}, device_scale_factor=1,
                                          locale={"en": "en-US", "ru": "ru-RU", "az": "az-Latn-AZ"}[language])
            context.add_init_script(f"localStorage.setItem('autoexpert.ui.language', '{language}')")
            page = context.new_page()
            page.goto(f"{base}/preview/#/garage")
            page.wait_for_selector(".garage", timeout=120000)
            ids = []
            # several cars are a subscription right (stage 6): the demo user starts the trial first
            page.evaluate("""async () => { const t = localStorage.getItem('autoexpert.demo.token');
                await fetch('/api/v1/subscription/trial', {method: 'POST', headers: {Authorization: 'Bearer ' + t}}); }""")
            for car in CARS:
                body = {k: car[k] for k in ("configuration_key", "vin", "odometer", "monthly", "region", "history")} | {"unit": "km", "read_on": "2026-10-01"}
                view = call(page, "POST", f"/garage/vehicles?language={language}", body)
                if car.get("patch"):
                    call(page, "PATCH", f"/garage/vehicles/{view['id']}?language={language}", car["patch"] | {"unit": "km"})
                if car.get("onboard_reset"):
                    call(page, "POST", f"/garage/vehicles/{view['id']}/onboard-reset?language={language}", car["onboard_reset"] | {"unit": "km"})
                ids.append((car["name"], view["id"]))
            made[language] = ids
            page.goto("about:blank")
            page.goto(f"{base}/preview/#/garage")
            page.wait_for_selector(".garage-car-card", timeout=120000)
            shoot(page, OUT / f"garage_list_{language}.png")
            for name, vid in ids:
                page.goto("about:blank")
                page.goto(f"{base}/preview/#/garage-car/{vid}")
                page.wait_for_selector(".garage-summary", timeout=120000)
                shoot(page, OUT / f"{name}_{language}.png")
            page.goto("about:blank")
            page.goto(f"{base}/preview/#/garage-feed")
            page.wait_for_selector(".garage-feed", timeout=120000)
            shoot(page, OUT / f"feed_{language}.png")
            # adding a car by VIN: the decoded pattern and the configurations it narrows to
            page.goto("about:blank")
            page.goto(f"{base}/preview/#/garage-add")
            page.wait_for_selector("#garage-vin-form", timeout=120000)
            page.fill("#garage-vin", CARS[2]["vin"])
            page.click("#garage-vin-form button[type=submit]")
            page.wait_for_selector("#garage-add-form", timeout=120000)
            shoot(page, OUT / f"add_by_vin_{language}.png")
            for _name, vid in ids:
                call(page, "DELETE", f"/garage/vehicles/{vid}")
            context.close()
        browser.close()
    from PIL import Image

    for path in OUT.glob("*.png"):  # phone width, JPEG: small enough for git
        image = Image.open(path).convert("RGB")
        image.save(path.with_suffix(".jpg"), quality=72, optimize=True, progressive=True)
        path.unlink()
    print(json.dumps({k: [n for n, _ in v] for k, v in made.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"))
