# ruff: noqa: E501
"""The "crooked letters" check (visual-match prompt, step 2): every glyph of the app is drawn by
the local Inter (or Caveat for the handwritten line), never by a fallback font.

1. A test page with the RU, AZ and EN alphabets in the app's font -> data_work/ui/visual_match/font_test.png.
2. Chrome DevTools (CSS.getPlatformFontsForNode) lists the fonts that really drew each text node of
   the test page and of the main screens in RU, AZ and EN; any other family is reported.

  uv run --no-project --with playwright --with pillow python scripts/design/font_check.py [base_url]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data_work" / "ui" / "visual_match"
ALLOWED = {"Inter", "Caveat"}
TEXT = {
    "RU": "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "AZ": "ABCÇDEƏFGĞHXIİJKQLMNOÖPRSŞTUÜVYZ abcçdeəfgğhxıijkqlmnoöprsştuüvyz",
    "EN": "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789 ₼ $ € № « » — – · %",
}
ROUTES = ["home", "pick", "catalog-results", "check", "compare", "profile"]


def fonts_used(page) -> dict[str, int]:
    cdp = page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("CSS.enable")
    root = cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})["root"]
    used: dict[str, int] = {}

    def walk(node):
        if node.get("nodeType") == 1 and node.get("localName") not in ("script", "style", "svg", "path", "head", "title", "meta", "link"):
            if any(c.get("nodeType") == 3 and c.get("nodeValue", "").strip() for c in node.get("children", [])):
                try:
                    for f in cdp.send("CSS.getPlatformFontsForNode", {"nodeId": node["nodeId"]})["fonts"]:
                        used[f["familyName"]] = used.get(f["familyName"], 0) + f["glyphCount"]
                except Exception:
                    pass
        for c in node.get("children", []) or []:
            walk(c)

    walk(root)
    return used


def main(base: str) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report, bad = {}, False
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        ctx.add_init_script("if (!localStorage.getItem('autoexpert.ui.language')) localStorage.setItem('autoexpert.ui.language', 'ru');")
        page = ctx.new_page()
        page.goto(f"{base}/preview/#/home")
        page.wait_for_selector(".ae-intro")
        page.evaluate("""t => { document.body.innerHTML = '<main style="padding:16px;font-family:Inter;background:#fff">' +
            Object.entries(t).map(([k, v]) => `<h2 style="font:800 18px Inter;margin:14px 0 4px">${k}</h2><p style="font:400 15px/1.5 Inter;margin:0">${v}</p><p style="font:700 15px/1.5 Inter;margin:0">${v}</p>`).join('') +
            '<h2 style="font:800 18px Inter;margin:14px 0 4px">Caveat</h2><p style="font:600 18px Caveat">Лучшие машины для твоих дорог · Yolların üçün ən yaxşı maşınlar</p></main>'; }""", TEXT)
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "font_test.png"), full_page=True)
        report["font_test"] = fonts_used(page)
        for lang in ("ru", "az", "en"):
            page.evaluate(f"localStorage.setItem('autoexpert.ui.language', '{lang}')")
            for route in ROUTES:
                page.goto(f"{base}/preview/#/{route}")
                page.reload()
                page.wait_for_timeout(2500)
                page.evaluate("document.fonts.ready")
                report[f"{lang}:{route}"] = fonts_used(page)
        browser.close()
    for key, used in report.items():
        other = {k: v for k, v in used.items() if k not in ALLOWED}
        bad |= bool(other)
        print(f"{key:22} {json.dumps(used, ensure_ascii=False)}{'   <-- FALLBACK' if other else ''}")
    (OUT / "font_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FALLBACK FONTS FOUND" if bad else "only Inter / Caveat drew the text")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8020"))
