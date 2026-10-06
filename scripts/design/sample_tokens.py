"""Colour tokens picked from the owner's design reference (visual-match prompt, step 2).

Fills are the median of a 5x5 patch at a point of the cropped screens (design/reference/crops,
390 px wide); text colours are the median of the darkest / most saturated pixels inside the box
of a word. The result goes to design/tokens.json — every colour of the web app comes from there
(scripts/design/build_tokens_css.py turns it into apps/web_preview/tokens.css).

  .venv/Scripts/python.exe scripts/design/sample_tokens.py
"""
from __future__ import annotations

import colorsys
import json
from pathlib import Path
from statistics import median

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CROPS = ROOT / "design" / "reference" / "crops"
OUT = ROOT / "design" / "tokens.json"

# name: (crop, point) for fills; (crop, box, "dark" | "sat") for text and thin strokes
FILLS = {
    "bg": ("podbor", (370, 150)),
    "card": ("podbor", (330, 238)),
    "primary": ("podbor", (40, 731)),
    "step_inactive": ("podbor", (195, 88)),
    "navy_card": ("home", (16, 500)),
    "buy_card": ("home", (20, 230)),
    "chip_home": ("home", (25, 357)),
    "chip": ("podbor", (20, 338)),
    "chip_selected": ("podbor", (70, 302)),
    "badge_blue_bg": ("results", (290, 351)),
    "warning_bg": ("results", (376, 668)),
    "warning_icon": ("results", (32, 677)),
    "verdict_bg": ("compare", (360, 245)),
    "vs_circle": ("compare", (196, 128)),
    "cta_dark": ("compare", (330, 752)),
    "nav_active": ("home", (47, 797)),
    "tower": ("home", (343, 130)),
    "tower_light": ("home", (373, 147)),
}
TEXT = {
    "heading": ("podbor", (14, 135, 280, 160), "dark5"),
    "badge_green_bg": ("results", (303, 183, 376, 212), "mode"),
    "badge_yellow_bg": ("results", (289, 502, 376, 531), "mode"),
    "dot_green": ("compare", (128, 438, 142, 452), "sat"),
    "dot_yellow": ("compare", (128, 514, 142, 528), "sat"),
    "text": ("podbor", (14, 166, 330, 192), "dark"),
    "muted": ("podbor", (150, 104, 240, 117), "dark"),
    "link": ("podbor", (320, 45, 385, 60), "sat"),
    "brand_blue": ("home", (85, 42, 128, 60), "sat"),
    "buy_title": ("home", (28, 205, 210, 245), "sat"),
    "chip_selected_border": ("podbor", (54, 290, 60, 315), "sat"),
    "badge_green_text": ("results", (285, 183, 375, 205), "dark"),
    "badge_blue_text": ("results", (285, 345, 375, 358), "dark"),
    "badge_yellow_text": ("results", (285, 503, 375, 528), "dark"),
    "nav_inactive": ("home", (125, 785, 160, 808), "dark"),
    "on_dark": ("home", (24, 398, 250, 440), "light"),
    "on_dark_muted": ("home", (24, 460, 210, 474), "light8"),
    "chip_text": ("home", (40, 350, 75, 364), "dark"),
    "avatar": ("home", (348, 45, 372, 70), "mode"),
    "flag_blue": ("home", (299, 166, 315, 169), "sat"),
    "flag_red": ("home", (299, 171, 315, 173), "sat"),
    "flag_green": ("home", (299, 175, 315, 178), "sat"),
    "script": ("home", (250, 123, 323, 173), "dark"),
}


def hexed(rgb) -> str:
    return "#%02x%02x%02x" % tuple(round(c) for c in rgb)


def patch(im, x, y, r=2):
    px = [im.getpixel((i, j)) for i in range(x - r, x + r + 1) for j in range(y - r, y + r + 1)]
    return tuple(median(p[k] for p in px) for k in range(3))


def text_colour(im, box, mode):
    px = [im.getpixel((i, j)) for i in range(box[0], box[2]) for j in range(box[1], box[3])]
    if mode == "mode":  # the most frequent colour (quantised): the fill of a badge behind its text
        counts = {}
        for p in px:
            q = tuple(c // 6 * 6 for c in p)
            counts[q] = counts.get(q, 0) + 1
        best = max(counts, key=counts.get)
        pick = [p for p in px if tuple(c // 6 * 6 for c in p) == best]
    elif mode in ("dark", "dark5"):
        px.sort(key=lambda p: sum(p))
        pick = px[: max(8, len(px) // (5 if mode == "dark5" else 12))]
    elif mode in ("light", "light8"):
        px.sort(key=lambda p: -sum(p))
        pick = px[: max(8, len(px) // (8 if mode == "light" else 30))] if mode == "light" else [p for p in px if 120 < sum(p) / 3 < 235] or px[:8]
    else:
        px.sort(key=lambda p: -colorsys.rgb_to_hsv(*(c / 255 for c in p))[1] * (1 - abs(sum(p) / 765 - 0.45)))
        pick = px[: max(8, len(px) // 15)]
    return tuple(median(p[k] for p in pick) for k in range(3))


def main() -> None:
    images = {p.stem: Image.open(p).convert("RGB") for p in CROPS.glob("*.png")}
    tokens = {name: hexed(patch(images[crop], *point)) for name, (crop, point) in FILLS.items()}
    tokens.update({name: hexed(text_colour(images[crop], box, mode)) for name, (crop, box, mode) in TEXT.items()})
    doc = {"_source": "picked from design/reference/crops by scripts/design/sample_tokens.py", "color": tokens}
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    for k, v in tokens.items():
        print(f"{k:22} {v}")


if __name__ == "__main__":
    main()
