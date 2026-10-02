"""Bulk Wikidata/vPIC identity joins for the existing US research universe.

Wikidata structured statements are CC0, but a global car-model entity is not
evidence for a particular US model year or powertrain.  vPIC's cached
GetModelsForMakeYear response can support a model-year name only; its dataset
reuse metadata remains under review.  Neither source creates mechanical
COMMERCIAL_OK claims here or changes the application database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "autoexpert.db"
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-01"
CACHE = ROOT / ".localdata/wikidata-model-cache"
VPIC_CROSSCHECK = ROOT / "deliverables/VerifiedData/us-catalog-universe/vpic-crosscheck.jsonl"
ACTIVE_CATALOG = ROOT / "deliverables/VerifiedData/us-catalog-universe/core-catalog-after.json"
WDQS = "https://query.wikidata.org/sparql"
CC0 = "https://www.wikidata.org/wiki/Wikidata:Licensing"


def compact(value: object) -> str:
    return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())


def model_labels(db_path: Path) -> list[tuple[str, str]]:
    active = json.loads(ACTIVE_CATALOG.read_text(encoding="utf-8"))
    active_models = {
        tuple(compact(part) for part in name.split(" | ", 1))
        for name in active["us_base_2000"]["models"]
    }
    connection = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT DISTINCT json_extract(specifications,'$.catalog.make'), "
            "json_extract(specifications,'$.catalog.model') "
            "FROM vehicle_variants WHERE published_revision_id IS NOT NULL "
            "AND is_demo=0 AND json_extract(specifications,'$.catalog.original_market')='US' "
            "ORDER BY 1,2"
        ).fetchall()
    finally:
        connection.close()
    result = []
    seen = set()
    for make, model in rows:
        key = compact(make), compact(model)
        if key in active_models and key not in seen:
            seen.add(key)
            result.append((make, model))
    return result


def query_for(labels: list[str]) -> str:
    quoted = " ".join(json.dumps(label, ensure_ascii=False) + "@en" for label in labels)
    return (
        "SELECT ?requested ?item ?maker ?makerLabel ?inception ?end WHERE { "
        f"VALUES ?requested {{ {quoted} }} "
        "?item rdfs:label ?requested . "
        "OPTIONAL { ?item wdt:P176 ?maker . } "
        "OPTIONAL { ?item wdt:P571 ?inception . } "
        "OPTIONAL { ?item wdt:P576 ?end . } "
        'SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . } '
        "} LIMIT 500"
    )


def fetch_or_cache(labels: list[str], cache: Path, *, network: bool) -> tuple[list[dict], str]:
    query = query_for(labels)
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
    path = cache / f"{digest}.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload["bindings"], "CACHE"
    if not network:
        return [], "NOT_CACHED"
    url = WDQS + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AutoExpert/0.8 (Wikidata CC0 model identity research)",
            "Accept": "application/sparql-results+json",
        },
    )
    error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP_{response.status}")
                payload = json.load(response)
            bindings = payload["results"]["bindings"]
            if not isinstance(bindings, list):
                raise ValueError("INVALID_SPARQL_RESPONSE")
            cache.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "query_sha256": digest,
                        "source_url": WDQS,
                        "retrieved_at_utc": datetime.now(UTC).isoformat(),
                        "bindings": bindings,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            return bindings, "NETWORK"
        except urllib.error.HTTPError as exc:
            # WDQS announced an active-outage cap of one request per minute.
            # Do not hammer the service or turn a 429 into a false no-match.
            if exc.code == 429:
                return [], "UPSTREAM_RATE_LIMIT_429"
            error = f"HTTP_{exc.code}"
            time.sleep(1.5 * (attempt + 1))
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            error = str(exc)[:160]
            time.sleep(1.5 * (attempt + 1))
    return [], "ERROR:" + (error or "unknown")


def _value(binding: dict, name: str) -> str | None:
    return (binding.get(name) or {}).get("value")


def _qid(uri: str | None) -> str | None:
    if not uri or "/entity/Q" not in uri:
        return None
    return uri.rsplit("/", 1)[-1]


def wikidata_join(
    models: list[tuple[str, str]],
    cache: Path,
    *,
    network: bool,
    upstream_limited: bool = False,
    chunk_size: int = 25,
) -> tuple[list[dict], dict]:
    label_to_model = {f"{make} {model}": (make, model) for make, model in models}
    labels = sorted(label_to_model)
    candidates: dict[tuple[str, str], list[dict]] = defaultdict(list)
    request_counts = Counter()
    model_counts = Counter()
    unqueried = set(labels)
    for offset in range(0, len(labels), chunk_size):
        chunk = labels[offset : offset + chunk_size]
        bindings, origin = fetch_or_cache(chunk, cache, network=network)
        request_counts[origin] += 1
        if origin == "UPSTREAM_RATE_LIMIT_429":
            upstream_limited = True
            break
        if origin in {"NETWORK", "CACHE"}:
            unqueried.difference_update(chunk)
        for binding in bindings:
            label = _value(binding, "requested")
            key = label_to_model.get(label)
            qid = _qid(_value(binding, "item"))
            if not key or not qid:
                continue
            make, model = key
            maker = _value(binding, "makerLabel")
            candidates[key].append(
                {
                    "wikidata_item": qid,
                    "wikidata_item_url": f"https://www.wikidata.org/wiki/{qid}",
                    "manufacturer_label": maker,
                    "manufacturer_item": _qid(_value(binding, "maker")),
                    "manufacturer_name_matches": compact(maker) == compact(make),
                    "global_inception": _value(binding, "inception"),
                    "global_end": _value(binding, "end"),
                }
            )
        print(f"Wikidata labels {min(offset + chunk_size, len(labels))}/{len(labels)}", flush=True)

    rows = []
    for make, model in models:
        entries = list({e["wikidata_item"]: e for e in candidates[(make, model)]}.values())
        matched = [e for e in entries if e["manufacturer_name_matches"]]
        if f"{make} {model}" in unqueried:
            status = "UPSTREAM_UNQUERIED_RATE_LIMIT" if upstream_limited else "NOT_CACHED"
        else:
            status = (
                "MODEL_IDENTITY_CC0_CANDIDATE"
                if len(matched) == 1
                else (
                    "AMBIGUOUS_MODEL_ENTITY" if len(matched) > 1 else "NO_UNAMBIGUOUS_MODEL_ENTITY"
                )
            )
        rows.append(
            {
                "make": make,
                "model": model,
                "status": status,
                "entities": entries,
                "candidate_source_id": "wikidata-structured-cc0",
                "reuse_status": "COMMERCIAL_OK"
                if status == "MODEL_IDENTITY_CC0_CANDIDATE"
                else "NEEDS_REVIEW",
                "rights_basis": "CC0_DATASET",
                "rights_reference": CC0,
                "rights_checked_at": "2026-09-28",
                "applicability_limit": (
                    "Global model identity only; no US model-year, "
                    "generation or mechanical claim"
                ),
            }
        )
        model_counts[status] += 1
    return rows, {
        "requests": dict(sorted(request_counts.items())),
        "model_statuses": dict(sorted(model_counts.items())),
    }


def vpic_join(path: Path) -> tuple[list[dict], dict]:
    rows = []
    counts = Counter()
    with path.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            status = row["status"]
            counts[status] += 1
            rows.append(
                {
                    "make": row["make"],
                    "model": row["model"],
                    "model_year": row["model_year"],
                    "status": status,
                    "candidate_source_id": "nhtsa_vpic_getmodelsformakeyear",
                    "source_url": row["vpic_response_url"],
                    "reuse_status": "NEEDS_REVIEW",
                    "rights_reason": (
                        "Data.gov Access & Use metadata says unknown-license; "
                        "commercial reuse unconfirmed"
                    ),
                    "applicability_limit": (
                        "Model-year name only; no mechanical configuration evidence"
                    ),
                }
            )
    return rows, dict(sorted(counts.items()))


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def run(
    db_path: Path = DB,
    out: Path = OUT,
    cache: Path = CACHE,
    *,
    network: bool = True,
    upstream_limited: bool = False,
) -> dict:
    models = model_labels(db_path)
    wikidata, wd_counts = wikidata_join(
        models, cache, network=network, upstream_limited=upstream_limited
    )
    vpic, vpic_counts = vpic_join(VPIC_CROSSCHECK)
    out.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out / "wikidata-model-identity.jsonl", wikidata)
    _write_jsonl(out / "vpic-model-year-rights-review.jsonl", vpic)
    summary = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "wikidata_models_considered": len(models),
        "wikidata_counts": wd_counts,
        "wikidata_rights": CC0,
        "wikidata_upstream_limitation": (
            "WDQS returned HTTP 429, active-outage rate limit one request per minute"
            if upstream_limited
            else None
        ),
        "vpic_model_year_pairs_considered": len(vpic),
        "vpic_counts": vpic_counts,
        "claims_written_to_application_db": 0,
        "mechanical_claims_from_wikidata_or_vpic": 0,
    }
    (out / "identity-join-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--upstream-limited", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.db,
                args.out,
                args.cache,
                network=not args.no_network,
                upstream_limited=args.upstream_limited,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
