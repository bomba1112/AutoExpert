"""Screenshots of the US technical facts panel in the web preview (next-stage prompt, stage C.5).

The preview must run with the show_us_tech_facts flag on (development default), e.g. on :8010.
For each configuration: the technical tab with every category open, then every other tab the
configuration has (an empty tab is not shown and so not captured). Phone width, Russian labels.
Uses the system Microsoft Edge through Playwright (no browser download).

  uv run --no-project --with playwright python scripts/capture_us_tech_screens.py [base_url]
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_work" / "ui" / "screens"
TARGETS = [
    ("toyota_camry_2020_2.5", "toyota-camry-us-2020-2.5l-4cyl-ice-a-s8-fwd"),
    ("hyundai_sonata_2018_2.4", "hyundai-sonata-us-2018-2.4l-4cyl-ice-a-s6-fwd"),
    ("kia_optima_2016_2.4", "kia-optima-k5-us-2016-2.4l-4cyl-ice-a-s6-fwd"),
    ("mercedes_c300_2016", "mercedes-benz-c-class-us-2016-2.0l-4cyl-turbo-ice-a-7-spd-rwd"),
    ("bmw_530i_2018", "bmw-5-series-us-2018-2.0l-4cyl-turbo-ice-a-s8-rwd"),
    ("tesla_model3_2021_awd", "tesla-model-3-us-2021-ev-bev-a-a1-awd"),
]

# the fixed bottom navigation would cover the content in a full-page capture
HIDE_NAV = ".bottom-nav{display:none!important}"


def main(base: str) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        context = browser.new_context(viewport={"width": 412, "height": 915}, device_scale_factor=1.5)
        context.add_init_script("localStorage.setItem('autoexpert.ui.language', 'ru')")  # read when the app starts
        page = context.new_page()
        for name, key in TARGETS:
            page.goto("about:blank")
            page.goto(f"{base}/preview/#/us-tech/{key}")
            page.wait_for_selector(".us-tech, .us-tech-view .catalog-card", timeout=60000)
            page.wait_for_timeout(500)
            page.add_style_tag(content=HIDE_NAV)
            page.evaluate("document.querySelectorAll('details.us-tech-group').forEach(d => d.open = true)")
            page.screenshot(path=str(OUT / f"{name}_technical.png"), full_page=True)
            tabs = page.eval_on_selector_all("[data-ustech-tab]", "els => els.map(e => e.dataset.ustechTab)")
            for tab in tabs:
                if tab == "technical":
                    continue
                page.click(f"[data-ustech-tab='{tab}']")
                page.wait_for_timeout(300)
                page.screenshot(path=str(OUT / f"{name}_{tab}.png"), full_page=True)
            print(name, "tabs:", ", ".join(tabs))
        # the panel inside the existing vehicle card (a published variant linked to a configuration)
        page.goto("about:blank")
        page.goto(f"{base}/preview/#/catalog-car/d952470f-11f2-446d-a15f-78ba6f903d9f")
        page.wait_for_selector(".us-tech", timeout=120000)
        page.add_style_tag(content=HIDE_NAV)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "toyota_camry_2020_2.5_vehicle_card.png"), full_page=True)
        print("vehicle card captured")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"))
