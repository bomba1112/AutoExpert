# ruff: noqa: E501
"""Screenshots of stages 3–6 of the product phase in EN, RU, AZ: the AI mechanic, the owners
club, a public car page, the subscription (free car with locked hints, the plans, the trial).
The preview must run on :8010 with the flags on (development defaults) and the public site
generated (scripts/build_public_pages.py).

Each language uses a fresh demo session; the car and the club post made for the pictures are
deleted afterwards (the demo user's trial stays, as any preview session's would).

  uv run --no-project --with playwright --with pillow python scripts/capture_product_screens.py [base_url]
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_work" / "product" / "screens" / "stages3-6"
HIDE = ".bottom-nav{display:none!important}.developer-drawer{display:none!important}"
CAMRY = "toyota-camry-us-2020-2.5l-4cyl-ice-a-s8-fwd"
PUBLIC = "toyota/camry/viii-2018-2024/2-5l-a25a-fks"
QUESTIONS = {"en": "How much refrigerant does the A/C take?", "ru": "Сколько фреона в кондиционере?", "az": "Kondisionerə nə qədər freon lazımdır?"}
POST = {"en": ("Oil top-up between changes", "Is it normal to add about half a litre between changes?"),
        "ru": ("Долив масла между заменами", "Нормально ли доливать около полулитра между заменами?"),
        "az": ("Dəyişmələr arasında yağ əlavəsi", "Dəyişmələr arasında yarım litr yağ əlavə etmək normaldırmı?")}
COMMENT = {"en": "Same here, I check the level every two weeks.", "ru": "У меня так же, проверяю уровень раз в две недели.",
           "az": "Məndə də belədir, səviyyəni iki həftədən bir yoxlayıram."}


def call(page, method, path, body=None):
    return page.evaluate(
        """async ([method, path, body]) => {
            const token = localStorage.getItem('autoexpert.demo.token');
            const r = await fetch('/api/v1' + path, {method, headers: {'Content-Type': 'application/json', Authorization: 'Bearer ' + token},
                                                    body: body ? JSON.stringify(body) : undefined});
            if (!r.ok) throw new Error(method + ' ' + path + ' ' + r.status + ' ' + await r.text());
            return r.status === 204 ? null : r.json();
        }""", [method, path, body])


def open_route(page, base, route, selector):
    page.goto("about:blank")
    page.goto(f"{base}/preview/#/{route}")
    page.wait_for_selector(selector, timeout=180000)
    page.add_style_tag(content=HIDE)
    page.wait_for_timeout(400)


def main(base: str) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        for lang in ("en", "ru", "az"):
            context = browser.new_context(viewport={"width": 412, "height": 915}, device_scale_factor=1,
                                          locale={"en": "en-US", "ru": "ru-RU", "az": "az-Latn-AZ"}[lang])
            context.add_init_script(f"localStorage.setItem('autoexpert.ui.language', '{lang}')")
            page = context.new_page()
            open_route(page, base, "garage", ".garage")
            car = call(page, "POST", f"/garage/vehicles?language={lang}",
                       {"configuration_key": CAMRY, "odometer": 87000, "monthly": 1500, "region": {"en": "US", "ru": "CIS", "az": "AZ"}[lang],
                        "history": [{"job": "engine_oil_and_filter", "status": "DONE", "performed_on": "2026-06-15", "odometer": 82500}]})
            call(page, "PATCH", f"/garage/vehicles/{car['id']}?language={lang}", {"oil_interval": 7000, "oil_interval_months": 6, "unit": "km"})
            # stage 6: a free car — personal hints locked
            open_route(page, base, f"garage-car/{car['id']}", ".garage-summary")
            page.screenshot(path=str(OUT / f"free_car_locked_{lang}.png"), full_page=True)
            open_route(page, base, "subscription", ".sub-plans")
            page.screenshot(path=str(OUT / f"subscription_free_{lang}.png"), full_page=True)
            page.click("[data-action=subscription-trial]")
            page.wait_for_selector(".sub-current", timeout=60000)
            page.screenshot(path=str(OUT / f"subscription_trial_{lang}.png"), full_page=True)
            # stage 3: the AI mechanic (no API key here: the data-only mode, then an honest refusal)
            open_route(page, base, f"garage-car/{car['id']}", "#garage-mechanic")
            page.click("[data-action=garage-mechanic-example]")
            page.wait_for_selector(".garage-qa", timeout=60000)
            page.fill("#garage-mechanic-form input[name=question]", QUESTIONS[lang])
            page.click("#garage-mechanic-form button[type=submit]")
            page.wait_for_function("document.querySelectorAll('.garage-qa').length >= 2", timeout=60000)
            page.add_style_tag(content=HIDE)
            page.locator("#garage-mechanic").screenshot(path=str(OUT / f"mechanic_{lang}.png"))
            # stage 4: the owners club
            rooms = call(page, "GET", f"/club/vehicles/{car['id']}/rooms?language={lang}")
            open_route(page, base, "club", ".club-rooms")
            page.screenshot(path=str(OUT / f"club_home_{lang}.png"), full_page=True)
            title, body = POST[lang]
            post = call(page, "POST", f"/club/rooms/{rooms[0]['id']}/posts?language={lang}", {"title": title, "body": body})
            call(page, "POST", f"/club/posts/{post['id']}/comments?language={lang}", {"body": COMMENT[lang]})
            open_route(page, base, f"club-room/{rooms[0]['id']}", ".club-posts")
            page.screenshot(path=str(OUT / f"club_room_{lang}.png"), full_page=True)
            open_route(page, base, f"club-post/{post['id']}", ".club-post")
            page.screenshot(path=str(OUT / f"club_post_{lang}.png"), full_page=True)
            starter = next((x for x in call(page, "GET", f"/club/rooms/{rooms[0]['id']}?language={lang}")["posts"] if x["kind"] == "STARTER"), None)
            if starter:
                open_route(page, base, f"club-post/{starter['id']}", ".club-post")
                page.screenshot(path=str(OUT / f"club_starter_topic_{lang}.png"), full_page=True)
            call(page, "DELETE", f"/club/posts/{post['id']}")
            # stage 5: the public page
            page.goto(f"{base}/cars/{lang}/{PUBLIC}/")
            page.wait_for_selector("h1", timeout=60000)
            page.screenshot(path=str(OUT / f"public_camry_{lang}.png"), full_page=True)
            call(page, "DELETE", f"/garage/vehicles/{car['id']}")
            context.close()
            print(lang)
        browser.close()
    from PIL import Image

    for path in OUT.glob("*.png"):  # JPEG, small enough for git
        Image.open(path).convert("RGB").save(path.with_suffix(".jpg"), quality=72, optimize=True, progressive=True)
        path.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"))
