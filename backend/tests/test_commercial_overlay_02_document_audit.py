"""The group audit must reject unattributed third-party HTML releases."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_manufacturer_cache_02 import audit_document  # noqa: E402


def _release(tmp_path: Path, *, issuer: bool) -> dict:
    article = (
        "2019 Hyundai Kona. Hyundai Motor America. "
        "Model Engine Transmission Drivetrain. "
        "Kona SE 2.0L 6-Speed Automatic FWD."
    )
    if issuer:
        article += " News provided by Hyundai Motor America. SOURCE Hyundai Motor America."
    data = ("<html><body>" + article + "</body></html>").encode()
    path = tmp_path / "release.html"
    path.write_bytes(data)
    meta = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "url": "https://www.prnewswire.com/news-releases/hyundai-kona.html",
        "make": "Hyundai",
        "model": "Kona",
        "model_year": 2019,
        "row_count": 1,
    }
    return audit_document(path, meta)


def test_manufacturer_issued_release_passes_group_identity_checks(tmp_path: Path):
    result = _release(tmp_path, issuer=True)
    assert result["manufacturer_issued_release"] is True
    assert result["machine_authenticity_pass"] is True


def test_syndicated_page_without_manufacturer_issuer_stays_in_review(tmp_path: Path):
    result = _release(tmp_path, issuer=False)
    assert result["manufacturer_issued_release"] is False
    assert result["machine_authenticity_pass"] is False
