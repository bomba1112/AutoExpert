"""Fail-closed joins: an EPA similarity never becomes verified evidence."""

import importlib.util
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "us_catalog_universe_join", ROOT / "scripts/us_catalog_universe_join.py"
)
join = importlib.util.module_from_spec(spec)
spec.loader.exec_module(join)


def candidate(**values):
    return {
        "epa_vehicle_id": "101",
        "make": "Kia",
        "model": "Forte",
        "epa_model": "Forte",
        "model_year": 2017,
        "normalized_powertrain_key": "one",
        "normalized_powertrain": {
            "displ": "2",
            "drive": "front-wheel drive",
            "trany": "manual 6-spd",
            "eng_dscr": "",
            "tCharger": "",
            "sCharger": "",
        },
        **values,
    }


def verified(**values):
    return {
        "variant_id": "published-1",
        "make": "Kia",
        "model": "Forte",
        "model_year": 2017,
        "displacement_l": 2.0,
        "transmission": "6-speed manual",
        "transmission_gears": 6,
        "transmission_family": "MANUAL",
        "drivetrain": "FWD",
        "aspiration": "NATURALLY_ASPIRATED",
        "injection": "MPI",
        "aliases": ["Forte"],
        **values,
    }


def test_exact_verified_epa_id_is_reused_but_identity_conflicts_fail_closed():
    record = verified()
    by_id = defaultdict(list, {"101": [record]})
    exact = join.classify(candidate(), by_id, {}, {})
    conflict = join.classify(
        candidate(
            normalized_powertrain={
                **candidate()["normalized_powertrain"],
                "drive": "rear-wheel drive",
            }
        ),
        by_id,
        {},
        {},
    )
    assert exact["classification"] == "ALREADY_VERIFIED"
    assert conflict["classification"] == "CONFLICT"
    assert conflict["reason"] == "DRIVETRAIN"


def test_factory_tuple_similarity_is_review_only_and_body_aliases_do_not_spread():
    record = verified()
    key = ("kia", "forte", 2017)
    by_model = defaultdict(list, {key: [record]})
    probable = join.classify(candidate(epa_vehicle_id="102"), {}, by_model, {})
    coupe = join.classify(candidate(epa_vehicle_id="103", epa_model="Forte Koup"), {}, by_model, {})
    assert probable["classification"] == "POSSIBLE_ALIAS"
    assert probable["matched_variant_id"] == "published-1"
    assert coupe["classification"] == "CANDIDATE_NEW"
