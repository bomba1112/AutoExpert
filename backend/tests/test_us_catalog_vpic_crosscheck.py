"""vPIC only corroborates a model/year name; it cannot certify powertrain."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "crosscheck_us_universe_vpic", ROOT / "scripts/crosscheck_us_universe_vpic.py"
)
vpic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vpic)


def test_one_make_year_request_url_and_name_matching():
    assert vpic.query_url("Mercedes-Benz", 2015).endswith(
        "/make/Mercedes-Benz/modelyear/2015?format=json"
    )
    result = {"http_status": 200, "models": ["C-Class", "GL-Class"]}
    assert vpic.model_status({"model": "C-Class"}, result, {"C300"}) == "VPIC_EXACT_BASE_MODEL"
    assert vpic.model_status({"model": "C"}, result, {"GL-Class"}) == "VPIC_EXACT_EPA_MODEL"
    assert vpic.model_status({"model": "C"}, result, {"C300"}) == "VPIC_NAME_UNRESOLVED"
    assert (
        vpic.model_status({"model": "C-Class"}, {"http_status": None}, {"C300"})
        == "VPIC_UNAVAILABLE"
    )
