"""Cache one official vPIC make/year response for every new EPA model-year pair.

vPIC confirms a reported model name in a model year. It does not verify an EPA
engine, transmission, drivetrain, trim, or generation. Missing vPIC matches stay
unresolved, never become a negative vehicle-existence claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-catalog-universe"
CACHE = ROOT / ".localdata/vpic-model-year-cache"
DOCS = "https://vpic.nhtsa.dot.gov/api/"
URL = "https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/{make}/modelyear/{year}?format=json"


def compact(value: object) -> str:
    return "".join(c for c in str(value or "").casefold() if c.isalnum())


def query_url(make: str, year: int) -> str:
    if year < 1996 or year > datetime.now(UTC).year + 2:
        raise ValueError("VPIC_YEAR_OUT_OF_RANGE")
    return URL.format(make=urllib.parse.quote(make, safe=""), year=year)


def fetch(make: str, year: int, *, timeout: int = 30) -> dict:
    url = query_url(make, year)
    request = urllib.request.Request(url, headers={"User-Agent": "AutoExpert/0.8 local-research"})
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        status = response.status
    parsed = json.loads(raw)
    if status != 200 or not isinstance(parsed.get("Results"), list):
        raise ValueError("VPIC_INVALID_RESPONSE")
    models = sorted(
        {str(item["Model_Name"]).strip() for item in parsed["Results"] if item.get("Model_Name")}
    )
    return {
        "source_url": url,
        "http_status": status,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "latency_ms": round((time.perf_counter() - started) * 1000),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "make": make,
        "model_year": year,
        "models": models,
    }


def cached_response(
    make: str, year: int, cache: Path, *, min_interval: float, timer: dict
) -> tuple[dict, bool]:
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (compact(make) + "-" + str(year) + ".json")
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved.get("source_url") == query_url(make, year) and saved.get("http_status") == 200:
            return saved, True
    delay = min_interval - (time.monotonic() - timer.get("last_call", 0))
    if delay > 0:
        time.sleep(delay)
    error = None
    for attempt in range(3):
        timer["last_call"] = time.monotonic()
        try:
            result = fetch(make, year)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
            )
            tmp.replace(path)
            return result, False
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            error = str(exc)[:160]
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    return {
        "source_url": query_url(make, year),
        "http_status": None,
        "make": make,
        "model_year": year,
        "models": [],
        "error": error,
    }, False


def model_status(row: dict, response: dict, epa_models: set[str]) -> str:
    if response.get("http_status") != 200:
        return "VPIC_UNAVAILABLE"
    names = {compact(x) for x in response["models"]}
    if compact(row["model"]) in names:
        return "VPIC_EXACT_BASE_MODEL"
    if any(compact(model) in names for model in epa_models):
        return "VPIC_EXACT_EPA_MODEL"
    return "VPIC_NAME_UNRESOLVED"


def run(
    candidates: Path, joined: Path, out: Path, cache: Path, *, min_interval: float = 0.4
) -> dict:
    joined_rows = {
        json.loads(x)["epa_vehicle_id"]: json.loads(x) for x in joined.open(encoding="utf-8")
    }
    pairs: dict[tuple[str, str, int], dict] = {}
    epa_models: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    for line in candidates.open(encoding="utf-8"):
        row = json.loads(line)
        status = joined_rows[row["epa_vehicle_id"]]["classification"]
        if status == "ALREADY_VERIFIED":
            continue
        key = (row["make"], row["model"], row["model_year"])
        pairs.setdefault(key, row)
        epa_models[key].add(row["epa_model"])
    make_years = sorted({(make, year) for make, _, year in pairs})
    responses = {}
    counts = Counter()
    timer = {}
    for index, (make, year) in enumerate(make_years, 1):
        result, hit = cached_response(make, year, cache, min_interval=min_interval, timer=timer)
        responses[(make, year)] = result
        counts["cache_hits" if hit else "network_calls"] += 1
        if result.get("http_status") != 200:
            counts["failed_make_year_requests"] += 1
        if index % 25 == 0 or index == len(make_years):
            print(
                f"vPIC make-years {index}/{len(make_years)} "
                f"· network {counts['network_calls']} · cache {counts['cache_hits']}",
                flush=True,
            )
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for (make, model, year), row in sorted(pairs.items()):
        response = responses[(make, year)]
        status = model_status(row, response, epa_models[(make, model, year)])
        counts[status] += 1
        rows.append(
            {
                "make": make,
                "model": model,
                "model_year": year,
                "epa_model_example": row["epa_model"],
                "status": status,
                "vpic_response_url": response["source_url"],
                "vpic_http_status": response.get("http_status"),
                "vpic_error": response.get("error"),
            }
        )
    (out / "vpic-crosscheck.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows),
        encoding="utf-8",
    )
    summary = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "official_documentation": DOCS,
        "endpoint_template": URL,
        "requested_make_years": len(make_years),
        "new_model_year_pairs": len(rows),
        "counts": dict(sorted(counts.items())),
        "self_imposed_min_interval_seconds": min_interval,
        "published_powertrain_configs": 0,
        "limitation": "vPIC model existence is not powertrain, generation or trim verification",
    }
    (out / "vpic-crosscheck-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=OUT / "candidates.jsonl")
    parser.add_argument("--join", type=Path, default=OUT / "candidate-join.jsonl")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--min-interval", type=float, default=0.4)
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.candidates, args.join, args.out, args.cache, min_interval=args.min_interval),
            ensure_ascii=False,
        )
    )
