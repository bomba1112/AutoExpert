"""Cut-outs of every freely licensed car photo (photos/commons/*.webp -> photos/cut/*.webp, WebP
with transparency, 360 px wide) for the "VS" layouts (battle cards, the comparison head): two cars
facing each other over a background, as in the design reference. Background removal: rembg u2net
(~/.u2net). The licence and author stay those of the photo (CC BY-SA: an adapted version, credited
on the "Фото и лицензии" screen). Existing cut-outs are kept.

  uv run --no-project --with rembg --with onnxruntime --with pillow python scripts/design/make_cutouts.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from rembg import new_session, remove

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "apps" / "web_preview" / "photos" / "commons"
OUT = ROOT / "apps" / "web_preview" / "photos" / "cut"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    session = new_session("u2net")
    for src in sorted(SRC.glob("*.webp")):
        dst = OUT / src.name
        if dst.exists():
            continue
        cut = remove(Image.open(src).convert("RGB"), session=session)
        cut = cut.crop(cut.getbbox())
        cut = cut.resize((360, round(cut.height * 360 / cut.width)), Image.LANCZOS)
        for q in (80, 70, 60):
            cut.save(dst, "WEBP", quality=q, method=6)
            if dst.stat().st_size <= 40_000:
                break
        print(dst.name, dst.stat().st_size)


if __name__ == "__main__":
    main()
