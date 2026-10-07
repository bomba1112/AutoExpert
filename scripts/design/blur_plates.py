"""Blur readable licence plates on the car photos (privacy; the photos are public on Wikimedia
Commons, but the app need not show other people's plate numbers). Boxes were found by eye on a
grid overlay of each 960 px file; the photo's provenance gets "licence plate blurred" in its
"modified" note. Run once after new photos arrive; a photo already marked is skipped.

  .venv/Scripts/python.exe scripts/design/blur_plates.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "apps" / "web_preview" / "photos"
BOXES = {
    "commons/mercedes-benz-e-class-2014-2016.webp": [(670, 378, 834, 442)],
    "commons/hero-dark-mercedes-benz-c-class.webp": [(774, 306, 888, 361), (730, 118, 796, 138)],
    "commons/lexus-rx-2016-2022.webp": [(68, 318, 184, 370)],
}
NOTE = "licence plate blurred"


def main() -> None:
    for part in DIR.rglob("provenance_*.json"):
        rows = json.loads(part.read_text(encoding="utf-8"))
        changed = False
        for row in rows:
            boxes = BOXES.get(row["file"])
            if not boxes or NOTE in str(row.get("modified", "")):
                continue
            path = DIR / row["file"]
            im = Image.open(path).convert("RGB")
            for box in boxes:
                region = im.crop(box)
                small = region.resize((max(1, region.width // 10), max(1, region.height // 10)), Image.BILINEAR)
                im.paste(small.resize(region.size, Image.NEAREST).filter(ImageFilter.GaussianBlur(3)), box)
            for q in (86, 80, 72, 64):
                im.save(path, "WEBP", quality=q, method=6)
                if path.stat().st_size <= 150_000:
                    break
            row["modified"] = f"{row.get('modified') or 'resized and converted to WebP'}; {NOTE}"
            changed = True
            print("blurred", row["file"])
        if changed:
            part.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
