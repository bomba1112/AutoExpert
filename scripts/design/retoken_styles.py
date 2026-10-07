"""Every colour of the app from design/tokens.json (visual-match prompt, step 2): the older
styles.css (garage, club, reports, VIN history...) still had its own literal colours. Each literal
is replaced by the nearest token (CIELAB distance); a translucent one becomes
color-mix(in srgb, var(--ae-x) NN%, transparent). The old theme variables get a token by role.
The replacements are listed in design/retoken_report.json.

  .venv/Scripts/python.exe scripts/design/retoken_styles.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "apps" / "web_preview" / "styles.css"
TOKENS = ROOT / "design" / "tokens.json"
REPORT = ROOT / "design" / "retoken_report.json"
ROLE = {  # the old :root variables -> the token with the same role in the reference
    "--bg": "bg", "--ink": "heading", "--muted": "muted", "--navy": "navy-card", "--navy-2": "navy-card-2", "--paper": "bg",
    "--card": "card", "--line": "border", "--gold": "primary", "--gold-soft": "primary-soft", "--green": "badge-green-text",
    "--green-soft": "badge-green-bg", "--blue": "link", "--blue-soft": "chip-selected", "--orange": "warning-icon",
    "--orange-soft": "warning-bg", "--red": "red", "--red-soft": "warning-bg",
}
# palette tokens a literal may map to (not the photo / flag / script colours)
SKIP = {"flag-blue", "flag-red", "flag-green", "tower", "tower-light", "script", "avatar", "cta-dark", "vs-circle", "dot-yellow", "dot-green",
        "badge-yellow-text", "nav-active", "brand-blue", "buy-title"}
LITERAL = re.compile(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b|rgba?\([^)]*\)")


def to_rgba(text: str):
    t = text.strip().lower()
    if t.startswith("#"):
        h = t[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return r, g, b, a
    nums = re.findall(r"[\d.]+%?", t)
    r, g, b = (float(n) for n in nums[:3])
    a = 1.0
    if len(nums) > 3:
        a = float(nums[3].rstrip("%")) / (100 if nums[3].endswith("%") else 1)
    return r, g, b, a


def lab(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116  # noqa: E731
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def main() -> None:
    doc = json.loads(TOKENS.read_text(encoding="utf-8"))
    palette = {k.replace("_", "-"): v for k, v in doc["color"].items()} | {k.replace("_", "-"): v["value"] for k, v in doc["derived"].items()}
    choices = {k: lab(to_rgba(v)[:3]) for k, v in palette.items() if k not in SKIP}
    css = CSS.read_text(encoding="utf-8")
    report: dict[str, str] = {}

    def nearest(rgb):
        p = lab(rgb)
        return min(choices, key=lambda k: sum((a - b) ** 2 for a, b in zip(p, choices[k])))

    def swap(m):
        r, g, b, a = to_rgba(m.group(0))
        name = nearest((r, g, b))
        out = f"var(--ae-{name})" if a >= 0.999 else f"color-mix(in srgb,var(--ae-{name}) {round(a * 100)}%,transparent)"
        report[m.group(0)] = out
        return out

    # the old theme variables by role, then every other literal by distance
    def root_var(m):
        out = f"{m.group(1)}: var(--ae-{ROLE[m.group(1)]});"
        report[m.group(0)] = out
        return out

    css = re.sub(r"(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8});", lambda m: root_var(m) if m.group(1) in ROLE else m.group(0), css)
    out_lines = []
    for line in css.split("\n"):
        out_lines.append(line if "mask" in line else LITERAL.sub(swap, line))
    CSS.write_text("\n".join(out_lines), encoding="utf-8", newline="\n")
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(len(report), "literals replaced")


if __name__ == "__main__":
    main()
