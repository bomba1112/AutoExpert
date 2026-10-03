"""OCR of mycarusermanual.com editions whose manual pages are images (no text layer), e.g.
Audi Q7 2016-2025, Q3/Q5 2020 (owner's amendment, 2026-10-03).

Only the sections that can hold oil, fluid, tank, tire and service information are read. Each
embedded page image is read with RapidOCR (ONNX models bundled in the package; deterministic for
the same image); text lines are put back in reading order per column (manual pages have two
columns). Written next to the section in the raw store:
  <section>.ocr.json   pages: [{"image_sha256", "lines": [{"text", "box"}], "text"}]
  <section>.ocr.txt    the pages' text (with spaces put back between digits and letters so the
                       edition-market markers of classify_mcum.py can be counted)
Idempotent: a section whose .ocr.json carries the same html sha256 is skipped.

  uv run --no-project --with rapidocr-onnxruntime python scripts/ocr_mcum_images.py audi/q7/suv_2016-2025 ...
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT  # noqa: E402

# the site misspells some section names ("checking-and-fulling--engine", "--fules")
SECTIONS = re.compile(r"oil|fuel|fules|refuel|technical-data|service|mainten|tire|wheel|capacit|fluid|coolant|brake|checking-and-f[iu]lling", re.I)
IMAGE = re.compile(r"data:image/png;base64,([A-Za-z0-9+/=]+)")


def reading_order(result, width: float) -> list[dict]:
    """Lines sorted by column (left half, then right half) and top; a line spanning most of the
    page (a heading) stays where its top puts it in the left column."""
    lines = []
    for box, text, score in result or []:
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        lines.append({"text": text, "box": [min(xs), min(ys), max(xs), max(ys)], "score": round(float(score), 3)})
    def column(line):
        x0, _, x1, _ = line["box"]
        return 0 if (x1 - x0) > 0.6 * width or (x0 + x1) / 2 < width / 2 else 1
    return sorted(lines, key=lambda l: (column(l), l["box"][1], l["box"][0]))


def spaced(text: str) -> str:
    text = re.sub(r"(?<=\d)(?=[A-Za-z])|(?<=[A-Za-z])(?=\d)", " ", text)
    return re.sub(r"([()/])", r" \1 ", text)


def main(folders: list[str]) -> int:
    from rapidocr_onnxruntime import RapidOCR
    import cv2
    import numpy as np

    ocr = RapidOCR()
    for rel in folders:
        folder = RAW_ROOT / "_mcum" / rel
        for html_path in sorted(folder.glob("*.html.gz")):
            name = html_path.name[: -len(".html.gz")]
            if not SECTIONS.search(name):
                continue
            raw = html_path.read_bytes()
            html_sha = hashlib.sha256(gzip.decompress(raw)).hexdigest()
            out_json = folder / f"{name}.ocr.json"
            if out_json.exists() and json.loads(out_json.read_text(encoding="utf-8")).get("html_sha256") == html_sha:
                continue
            html = gzip.decompress(raw).decode("utf-8", errors="replace")
            pages = []
            t0 = time.time()
            for b64 in IMAGE.findall(html):
                data = base64.b64decode(b64)
                image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                if image is None or image.shape[0] < 400:
                    continue  # icons and logos are not manual pages
                result, _ = ocr(image)
                lines = reading_order(result, image.shape[1])
                pages.append({"image_sha256": hashlib.sha256(data).hexdigest(), "lines": lines,
                              "text": " ".join(l["text"] for l in lines)})
            out_json.write_text(json.dumps({"html_sha256": html_sha, "engine": "rapidocr-onnxruntime", "pages": pages},
                                           ensure_ascii=False), encoding="utf-8")
            (folder / f"{name}.ocr.txt").write_text("\n".join(spaced(p["text"]) for p in pages), encoding="utf-8")
            print(rel, name, "pages", len(pages), f"{time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
