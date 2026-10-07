"""Line icons for the web preview (visual-match prompt): Tabler Icons (MIT), the outline set and a
few filled ones for the active bottom menu. The SVG bodies are written into
apps/web_preview/icons.js once, so the app needs no icon font and no request per icon.

  .venv/Scripts/python.exe scripts/design/build_icons.py
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "apps" / "web_preview" / "icons.js"
BASE = "https://cdn.jsdelivr.net/npm/@tabler/icons@3.31.0/icons"
OUTLINE = [
    "bell", "user", "home", "scale", "search", "file-text", "garage", "arrow-right", "arrow-left", "chevron-right",
    "chevron-down", "x", "check", "plus", "info-circle", "alert-triangle", "bulb", "world", "calendar", "cash",
    "wallet", "engine", "manual-gearbox", "car", "car-suv", "car-4wd", "bus", "truck", "chart-bar", "car-crash",
    "gauge", "lock", "shield", "photo", "gas-station", "droplet", "leaf", "plug", "bolt", "help-circle", "circle-dot",
    "steering-wheel", "robot", "adjustments", "wind", "disc", "armchair", "stack-2", "flag", "users", "heart",
    "share", "trending-up", "settings", "tool", "currency-manat", "list-check", "file-search", "license",
    "circle-check", "car-garage", "route", "building-skyscraper", "map-pin", "badge", "certificate",
]
FILLED = ["home", "user", "scale", "search", "file-text", "circle-check", "info-circle", "alert-triangle"]


def body(svg: str) -> str:
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    inner = re.sub(r'<path stroke="none" d="M0 0h24v24H0z" fill="none"\s*/>', "", inner)
    return re.sub(r"\s+", " ", inner).strip()


def fetch(kind: str, name: str) -> str | None:
    try:
        with urllib.request.urlopen(f"{BASE}/{kind}/{name}.svg", timeout=20) as r:
            return body(r.read().decode("utf-8"))
    except Exception:
        return None


def main() -> None:
    outline, filled, missing = {}, {}, []
    for name in OUTLINE:
        svg = fetch("outline", name)
        if svg:
            outline[name] = svg
        else:
            missing.append(name)
    for name in FILLED:
        svg = fetch("filled", name)
        if svg:
            filled[name] = svg
        else:
            missing.append(f"filled/{name}")
    js = (
        "// Tabler Icons (MIT, https://tabler.io/icons), outline and a few filled, written by\n"
        "// scripts/design/build_icons.py. icon(name) gives an inline SVG that takes the text colour.\n"
        f"export const OUTLINE = {json.dumps(outline, indent=0)};\n"
        f"export const FILLED = {json.dumps(filled, indent=0)};\n"
        "export function icon(name, cls = '', {filled = false, size = null} = {}) {\n"
        "  const shape = (filled && FILLED[name]) || OUTLINE[name] || OUTLINE['circle-dot'];\n"
        "  const solid = filled && FILLED[name];\n"
        "  return `<svg class=\"ic ic-${name}${cls ? ' ' + cls : ''}\" viewBox=\"0 0 24 24\"${size ? ` width=\"${size}\" height=\"${size}\"` : ''} "
        "fill=\"${solid ? 'currentColor' : 'none'}\" stroke=\"${solid ? 'none' : 'currentColor'}\" stroke-width=\"1.8\" stroke-linecap=\"round\" "
        "stroke-linejoin=\"round\" aria-hidden=\"true\" focusable=\"false\">${shape}</svg>`;\n"
        "}\n"
    )
    OUT.write_text(js, encoding="utf-8")
    print(f"{len(outline)} outline, {len(filled)} filled; missing: {missing}")


if __name__ == "__main__":
    main()
