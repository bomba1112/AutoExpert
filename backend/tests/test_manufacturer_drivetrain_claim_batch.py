"""The reviewed drive matrix, not the EPA candidate, determines each claim."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_manufacturer_drivetrain_claim_batch import reviewed_drive_value  # noqa: E402


def assertion(key: str, drive: str) -> dict:
    return {
        "catalog_key": key,
        "official_variant": f"Model {key}",
        "official_drive_term": drive,
        "drivetrain": drive,
        "locator": f"Official matrix, Model {key} column, drive row",
    }


def test_per_key_manufacturer_drive_rejects_swapped_values_with_same_group_counts():
    reviewed = {"front": assertion("front", "FWD"), "all": assertion("all", "AWD")}
    candidates = {"front": "FWD", "all": "AWD"}
    assert [reviewed_drive_value(reviewed[key], candidates[key]) for key in reviewed] == [
        "FWD",
        "AWD",
    ]

    # A cohort-level count would still see one FWD and one AWD. The exact
    # per-key comparison must reject both mislabeled factory assertions.
    reviewed["front"]["drivetrain"] = "AWD"
    reviewed["all"]["drivetrain"] = "FWD"
    for key in reviewed:
        with pytest.raises(ValueError, match="EPA_CANDIDATE_CONFLICTS_WITH_MANUFACTURER"):
            reviewed_drive_value(reviewed[key], candidates[key])


def test_incomplete_or_unknown_official_assertion_is_not_promoted():
    row = assertion("front", "FWD")
    row["locator"] = ""
    with pytest.raises(ValueError, match="INCOMPLETE_MANUFACTURER_ASSERTION"):
        reviewed_drive_value(row, "FWD")
    row["locator"] = "Official matrix, front column"
    row["drivetrain"] = "UNKNOWN"
    with pytest.raises(ValueError, match="INVALID_MANUFACTURER_DRIVE"):
        reviewed_drive_value(row, "UNKNOWN")
