"""design/tokens.json -> apps/web_preview/tokens.css (CSS custom properties --ae-*).

The picked colours (scripts/design/sample_tokens.py) are completed with a few derived ones —
a hairline border, the card shadow, tints — each computed from picked colours by the rule written
next to it, and saved back into tokens.json under "derived", so every colour of the app still
comes from that one file. Type sizes measured on the 390 px crops are kept there too.

  .venv/Scripts/python.exe scripts/design/build_tokens_css.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKENS = ROOT / "design" / "tokens.json"
OUT = ROOT / "apps" / "web_preview" / "tokens.css"

# type scale measured on the 390 px crops (cap height / 0.72 for the font size)
TYPE = {
    "hero": "21px",          # "Твой честный автоэксперт без предвзятости" (one line + one at 390 px)
    "card_title": "20px",    # "Хочу приобрести машину"
    "dark_title": "19px",    # "Проверить конкретную машину"
    "screen_title": "19px",  # "Подберём машину под вас", "Техническая часть"
    "section": "17.5px",     # "Битва поколений", "Главное за 30 секунд"
    "page_title": "15.5px",  # the top bar: "Подбор машины", "Подходящие варианты"
    "item_title": "15px",    # car names in lists, category names
    "body": "12px",
    "label": "12px",         # field labels: "Бюджет", "Рынок происхождения"
    "small": "10.5px",
    "chip": "10.5px",
    "nav": "10px",
}
# derived colours: (rule, colour a, colour b, share of a)
DERIVED = {
    "border": ("mix", "muted", "card", 0.14),
    "border_strong": ("mix", "muted", "card", 0.26),
    "shadow": ("mix", "heading", "bg", 0.10),
    "primary_soft": ("mix", "primary", "card", 0.10),
    "primary_hover": ("mix", "primary", "heading", 0.82),
    "navy_card_2": ("mix", "navy_card", "primary", 0.78),
    "chip_border": ("mix", "chip_selected_border", "card", 0.25),
    "red": ("mix", "warning_icon", "heading", 0.0),
}


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    return "#%02x%02x%02x" % tuple(round(x * t + y * (1 - t)) for x, y in zip(rgb(a), rgb(b)))


def main() -> None:
    doc = json.loads(TOKENS.read_text(encoding="utf-8"))
    colors = doc["color"]
    derived = {}
    for name, (_, a, b, t) in DERIVED.items():
        if name == "red":
            derived[name] = "#d64a3b" if "dot_red" not in colors else colors["dot_red"]
            continue
        derived[name] = mix(colors[a], colors[b], t)
    doc["derived"] = {k: {"value": v, "rule": f"mix({DERIVED[k][1]}, {DERIVED[k][2]}, {DERIVED[k][3]})"} for k, v in derived.items()}
    doc["derived"]["red"]["rule"] = "a red for 'serious' dots: not in the reference pictures (they show green / yellow only)"
    doc["type"] = TYPE
    TOKENS.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    lines = ["/* written by scripts/design/build_tokens_css.py from design/tokens.json — do not edit */", ":root {"]
    for k, v in {**colors, **derived}.items():
        lines.append(f"  --ae-{k.replace('_', '-')}: {v};")
    for k, v in TYPE.items():
        lines.append(f"  --ae-fs-{k.replace('_', '-')}: {v};")
    lines.append("}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
