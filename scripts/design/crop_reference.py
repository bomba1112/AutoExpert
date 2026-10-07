"""Cut the owner's design reference into one file per screen, scaled to the 390 px mobile width
(visual-match prompt, step 1). Boxes are the phone screens inside the bezels (found by scanning
the dark bezel columns of each picture)."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "design" / "reference"
OUT = REF / "crops"
WIDTH = 390
CROPS = {
    "home": ("01_approved_home_podbor_results.png", (33, 18, 487, 999)),
    "podbor": ("01_approved_home_podbor_results.png", (542, 18, 994, 999)),
    "results": ("01_approved_home_podbor_results.png", (1045, 18, 1503, 999)),
    "car_card": ("02_car_card_tech_oil.png", (70, 18, 513, 925)),
    "tech_categories": ("02_car_card_tech_oil.png", (604, 18, 1066, 925)),
    "oil_fluids": ("02_car_card_tech_oil.png", (1158, 18, 1604, 925)),
    "compare": ("03_compare_verdict_podbor.png", (540, 27, 997, 1013)),
    "found_list": ("04_found_cars_list.png", (68, 17, 512, 925)),
    "home_dark": ("03_compare_verdict_podbor.png", (37, 27, 497, 1013)),
    "podbor_4steps": ("03_compare_verdict_podbor.png", (1050, 27, 1509, 1013)),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (file, box) in CROPS.items():
        im = Image.open(REF / file).convert("RGB").crop(box)
        im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        im.save(OUT / f"{name}.png", optimize=True)
        print(name, im.size)


if __name__ == "__main__":
    main()
