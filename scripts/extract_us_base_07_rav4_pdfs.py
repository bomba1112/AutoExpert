"""Extract locally cached RAV4 manufacturer brochure text for source review."""
# ruff: noqa: E501

import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ROOT / ".localdata/us-base-catalog-07-rav4-documents"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/rav4-source-work"
WORK.mkdir(parents=True, exist_ok=True)

for year in ("2019", "2019-2", "2020", "2021"):
    reader = PdfReader(DOCUMENTS / f"rav4-{year}.pdf")
    pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
    target = WORK / f"rav4-{year}-extracted.txt"
    target.write_text(
        "\n\n".join(f"=== PDF PAGE {index + 1} ===\n{text}" for index, text in enumerate(pages)),
        encoding="utf-8",
    )
    plain = [page.extract_text() or "" for page in reader.pages]
    (WORK / f"rav4-{year}-plain.txt").write_text(
        "\n\n".join(
            f"=== PDF PAGE {index + 1} ===\n"
            + re.sub(r"[ \t]+", " ", text)
            for index, text in enumerate(plain)
        ),
        encoding="utf-8",
    )
    print(f"{year}: {len(pages)} pages; {target}")
    for index, page in enumerate(pages):
        lower = page.lower()
        if any(
            token in lower
            for token in ("2.5-liter dynamic", "8-speed", "ecvt", "e-cvt", "mechanical", "specifications")
        ):
            print(f"  page {index + 1}: {page[:110].strip()!r}")
