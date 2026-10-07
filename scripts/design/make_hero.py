"""Cut-outs for the home "Хочу приобрести машину" card: three cars of the freely licensed photos
(photos/commons, CC BY / CC BY-SA) with the background removed (rembg, model u2net in ~/.u2net),
saved as WebP with transparency in photos/hero/ and listed with their authors and licences in
photos/hero/hero.json (the credits screen shows them; "modified": background removed).

  uv run --no-project --with rembg --with onnxruntime --with pillow python scripts/design/make_hero.py [--mirror] <photo> [<photo> <photo>]
  One photo: a single car (owner 2026-10-06, until the owner's banner arrives), 690 px wide for
  sharp 3x screens; --mirror turns it to face the text.
  (photos as named in photos/commons/provenance_commons.json, e.g. commons/toyota-rav4-2019-2024.webp)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image
from rembg import new_session, remove

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "apps" / "web_preview" / "photos"
OUT = DIR / "hero"


def main(args: list[str]) -> int:
    mirror = "--mirror" in args
    files = [a for a in args if a != "--mirror"]
    width = 690 if len(files) == 1 else 420
    OUT.mkdir(parents=True, exist_ok=True)
    rows = {r["file"]: r for part in sorted((DIR / "commons").glob("provenance_commons*.json"))
            for r in json.loads(part.read_text(encoding="utf-8"))}
    session = new_session("u2net")
    meta = json.loads((OUT / "hero.json").read_text(encoding="utf-8")) if (OUT / "hero.json").exists() else {}
    buy, credits = [], [c for c in meta.get("credits", []) if c.get("role") != "buy"]
    for i, file in enumerate(files, 1):
        row = rows[file]
        cut = remove(Image.open(DIR / file).convert("RGB"), session=session)
        cut = cut.crop(cut.getbbox())
        cut = cut.resize((width, round(cut.height * width / cut.width)), Image.LANCZOS)
        if mirror:
            cut = cut.transpose(Image.FLIP_LEFT_RIGHT)
        # the source in the name: a new picture gets a new name, so no browser keeps the old one
        name = f"hero/buy-{i}-{Path(file).stem}{'-m' if mirror else ''}.webp"
        for q in (82, 74, 66, 58):
            cut.save(DIR / name, "WEBP", quality=q, method=6)
            if (DIR / name).stat().st_size <= 90_000:
                break
        buy.append(name)
        credits.append({"role": "buy", "file": name, "make": row["make"], "model": row["model"], "years": row["years"], "author": row["author"],
                        "license": row["license"], "license_url": row["license_url"], "source_page": row["source_page"],
                        "modified": "background removed, resized, WebP" + (", mirrored" if mirror else "")})
        print(name, (DIR / name).stat().st_size, "bytes from", file)
    meta.update({"buy": buy, "credits": credits})
    (OUT / "hero.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
