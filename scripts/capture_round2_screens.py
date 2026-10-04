"""Screenshots for the owner's second round (2026-10-03): translated weak points, service
campaigns and maintenance (RU and AZ), and the 2021-2026 preview layer (badge, card with the
US technical panel). The preview must run with show_us_tech_facts and
preview_us_configurations enabled (development defaults), e.g. on :8010.

  uv run --no-project --with playwright --with pillow python scripts/capture_round2_screens.py [base_url]
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_work" / "ui" / "screens" / "round2"
HIDE_NAV = ".bottom-nav{display:none!important}"
PANELS = [
    # (file name, configuration key, language, tabs)
    ("camry_2020_2.5", "toyota-camry-us-2020-2.5l-4cyl-ice-a-s8-fwd", "az", ["weak_points", "campaigns"]),
    ("camry_2020_2.5", "toyota-camry-us-2020-2.5l-4cyl-ice-a-s8-fwd", "ru", ["weak_points", "campaigns"]),
    ("optima_2016_2.4", "kia-optima-k5-us-2016-2.4l-4cyl-ice-a-s6-fwd", "az", ["maintenance", "campaigns"]),
    ("c300_2016", "mercedes-benz-c-class-us-2016-2.0l-4cyl-turbo-ice-a-7-spd-rwd", "ru", ["maintenance", "weak_points"]),
    ("model3_2021_awd", "tesla-model-3-us-2021-ev-bev-a-a1-awd", "az", ["campaigns"]),
]
PREVIEW_CARDS = [("preview_camry_2023_2.5_fwd", "b3387f88-1a38-4abe-b611-769cf4040880", "ru"),
                 ("preview_bmw_530i_2022", "0d7674a8-902e-4beb-9db1-9e247c965bd8", "az")]


def shoot(page, path: Path) -> None:
    page.add_style_tag(content=HIDE_NAV)
    page.wait_for_timeout(300)
    page.screenshot(path=str(path), full_page=True)


def main(base: str) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        for language in ("ru", "az"):
            context = browser.new_context(viewport={"width": 412, "height": 915}, device_scale_factor=1)
            context.add_init_script(f"localStorage.setItem('autoexpert.ui.language', '{language}')")
            page = context.new_page()
            for name, key, lang, tabs in PANELS:
                if lang != language:
                    continue
                page.goto("about:blank")
                page.goto(f"{base}/preview/#/us-tech/{key}")
                page.wait_for_selector(".us-tech", timeout=120000)
                for tab in tabs:
                    if page.locator(f"[data-ustech-tab='{tab}']").count():
                        page.click(f"[data-ustech-tab='{tab}']")
                        shoot(page, OUT / f"{name}_{tab}_{language}.png")
                print(name, language, tabs)
            for name, variant, lang in PREVIEW_CARDS:
                if lang != language:
                    continue
                page.goto("about:blank")
                page.goto(f"{base}/preview/#/catalog-car/{variant}")
                page.wait_for_selector(".preview-notice", timeout=180000)
                page.wait_for_selector(".us-tech", timeout=120000)
                shoot(page, OUT / f"{name}_{language}.png")
                # the fuel section (owner rule 2026-10-04): manufacturer's octane and the Auto Expert line
                page.evaluate("document.querySelectorAll('details.technical-group').forEach(d => d.open = true)")
                fuel = page.locator("details.technical-group", has=page.locator("[data-fuel-kind]")).first
                if fuel.count():
                    fuel.screenshot(path=str(OUT / f"{name}_fuel_{language}.png"))
                print(name, language)
            context.close()
        browser.close()
    from PIL import Image

    for path in OUT.glob("*.png"):  # phone width, JPEG: small enough for git
        image = Image.open(path).convert("RGB")
        image.save(path.with_suffix(".jpg"), quality=70, optimize=True, progressive=True)
        path.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"))
