"""Read-only HTTP checks for the active US catalogue; no account/session metadata."""

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    checks = []
    policy = json.loads(
        (ROOT / "data/manifests/az-market-priority-policy.json").read_text(encoding="utf-8")
    )
    manifest = json.loads((ROOT / policy["active_catalog_manifest"]).read_text(encoding="utf-8"))
    coverage = json.loads(
        (ROOT / "deliverables/VerifiedData" / manifest["batch_id"] / "coverage.json").read_text(
            encoding="utf-8"
        )
    )
    with httpx.Client(base_url="http://127.0.0.1:8000/api/v1/knowledge", timeout=60) as client:

        def request(name, path, payload=None):
            response = client.get(path) if payload is None else client.post(path, json=payload)
            checks.append({"name": name, "http_status": response.status_code})
            response.raise_for_status()
            return response.json()

        facets = request("US facets", "/facets?catalog_scope=US_BASE_2000")
        assert facets["markets"] == ["US"]
        assert min(facets["years"]) >= 2000
        base = {"catalog_scope": "US_BASE_2000", "year_min": 2000, "limit": 100}
        for language in ("ru", "az"):
            found = request(
                f"Unbranded sedan gasoline AT / {language}",
                f"/search?language={language}",
                {**base, "body": ["SEDAN"], "engine": "GASOLINE", "transmission": "AT"},
            )
            top = found["recommendation"]["top"]
            assert top and top["market"] == "US"
            models = {(top["make"], top["model"])}
            for alternative in found["recommendation"]["competitors"]:
                pair = (alternative["make"], alternative["model"])
                assert pair not in models
                models.add(pair)
            checks[-1].update(models=found["matched_models"], versions=found["matched_versions"])
            profile = request(f"Profile / {language}", f"/vehicles/{top['id']}?language={language}")
            assert len(profile["profile"]["categories"]) == 4
            assert len(profile["profile"]["technical"]) == 11
            comparison = request(
                f"Compare top and competitor / {language}",
                "/compare",
                {
                    "variant_ids": [top["id"], found["recommendation"]["competitors"][0]["id"]],
                    "language": language,
                },
            )
            assert len(comparison["members"]) == 2
        seven = request("Seven seats", "/search", {**base, "min_seats": 7})
        assert seven["matches"] and all(x["facts"]["seats"]["value"] >= 7 for x in seven["matches"])
        for seats in (5, 7):
            resolved = request(
                f"Tiguan AWD {seats} seats",
                "/resolve",
                {
                    "catalog_scope": "US_BASE_2000",
                    "make": "Volkswagen",
                    "model": "Tiguan",
                    "market": "US",
                    "year": 2019,
                    "drivetrain": "AWD",
                    "seats": seats,
                },
            )
            assert resolved["candidates"]
            assert all(x["facts"]["seats"]["value"] == seats for x in resolved["candidates"])
        unknown_budget = request(
            "Unknown budget does not rank as affordable",
            "/search",
            {**base, "budget_max_minor": 2000000},
        )
        assert unknown_budget["recommendation"]["top"] is None
        for name, params in [
            ("Skoda excluded", {"makes": ["Skoda"]}),
            ("CA excluded", {"market_preference": "SELECTED", "markets": ["CA"]}),
        ]:
            assert not request(name, "/search", {**base, **params})["matches"]
        for brand in coverage["priority_make_coverage"]:
            for language in ("ru", "az"):
                result = request(
                    f"Strict published scope / {brand['make']} / {language}",
                    f"/search?language={language}",
                    {**base, "makes": [brand["make"]]},
                )
                assert (
                    result["matched_versions"]
                    == brand["us_with_seating"]["model_year_configurations"]
                ), brand["make"]
                assert result["matched_models"] == brand["us_with_seating"]["models"], brand["make"]
                assert all(
                    x["make"] == brand["make"] and x["facts"]["seats"]["status"] == "CONFIRMED"
                    for x in result["matches"]
                )
                checks[-1].update(
                    models=result["matched_models"], configurations=result["matched_versions"]
                )
    output = ROOT / "deliverables/VerifiedData" / manifest["batch_id"] / "live-http.json"
    output.write_text(
        json.dumps(
            {"status": "PASS", "read_only": True, "checks": checks}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "checks": len(checks)}))


if __name__ == "__main__":
    main()
