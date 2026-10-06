"""Merge the provenance of the car photos (apps/web_preview/photos/**/provenance_*.json) into
photos/provenance.json and write apps/web_preview/photos.js — the manifest the app reads to show a
photo of a model whose generation covers the car's year, with its author and licence (shown on
large photos and on the "Фото и лицензии" screen).

Only photos whose licence allows use in a commercial app are taken (CC0 / public domain / CC BY /
CC BY-SA from Wikimedia Commons). Manufacturer press photos are editorial-only and are not used
(owner decision pending; they wait outside the project). Hero cut-outs for the home cards come
from photos/hero/hero.json (scripts/design/make_hero.py).

  .venv/Scripts/python.exe scripts/design/build_photos.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "apps" / "web_preview" / "photos"
OUT_JS = ROOT / "apps" / "web_preview" / "photos.js"
FREE = re.compile(r"^(cc0|public domain|pd|cc by(-sa)?( \d\.\d)?)", re.I)


def main() -> None:
    items, hero_dark, skipped = [], None, []
    for part in sorted(DIR.rglob("provenance_*.json")):
        for row in json.loads(part.read_text(encoding="utf-8")):
            f = DIR / row["file"]
            licence = str(row.get("license") or "")
            if not f.exists():
                skipped.append((row["file"], "missing file"))
                continue
            if not FREE.match(licence) or re.search(r"\bNC\b|\bND\b", licence):
                skipped.append((row["file"], f"licence not free for an app: {licence or 'none'}"))
                continue
            row["bytes"] = f.stat().st_size
            if row.get("role") == "hero-dark":
                hero_dark = row
                continue
            items.append(row)
    items.sort(key=lambda r: (r["make"], r["model"], r["years"][0]))
    (DIR / "provenance.json").write_text(json.dumps(items + ([hero_dark] if hero_dark else []), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hero = {"buy": [], "dark": None, "credits": []}
    meta = DIR / "hero" / "hero.json"
    if meta.exists():
        hero.update(json.loads(meta.read_text(encoding="utf-8")))
    if hero_dark and not hero.get("dark"):
        cut = DIR / "cut" / Path(hero_dark["file"]).name  # the dark car without its background
        hero["dark"] = f"cut/{cut.name}" if cut.exists() else hero_dark["file"]
        hero["credits"].append({"file": hero_dark["file"], "author": hero_dark.get("author"), "license": hero_dark.get("license"),
                                "license_url": hero_dark.get("license_url"), "source_page": hero_dark.get("source_page")})
    keep = ("file", "make", "model", "generation", "years", "author", "license", "license_url", "source_page")
    photos = [{k: r.get(k) for k in keep} for r in items]
    facing = json.loads((DIR / "facing.json").read_text(encoding="utf-8")) if (DIR / "facing.json").exists() else {}
    for p in photos:
        if p["file"] in facing:  # where the front points: the VS layouts mirror only when needed
            p["facing"] = facing[p["file"]]
    for p in photos:  # the cut-out of the photo for the "VS" layouts (scripts/design/make_cutouts.py)
        cut = DIR / "cut" / Path(p["file"]).name
        if cut.exists():
            p["cut"] = f"cut/{cut.name}"
    OUT_JS.write_text(
        "// written by scripts/design/build_photos.py from photos/**/provenance_*.json — freely licensed car photos\n"
        f"export const PHOTOS = {json.dumps(photos, ensure_ascii=False)};\n"
        f"export const HERO = {json.dumps(hero, ensure_ascii=False)};\n",
        encoding="utf-8", newline="\n",
    )
    print(len(photos), "photos;", "hero:", {k: v for k, v in hero.items() if k != "credits"})
    for s in skipped:
        print("skipped", *s)


if __name__ == "__main__":
    main()
