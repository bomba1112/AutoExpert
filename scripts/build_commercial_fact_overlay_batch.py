"""Dry-run fact-level commercial corroboration over the existing US catalogue.

The EPA CORE catalogue is a read-only candidate/QA universe.  This program
extracts short factual claims only from already-published, annual factory
records with per-fact documentary provenance.  A mirrored PDF, an EPA URL, a
vPIC model-year name, or a merely similar EPA mechanical tuple is never enough
to promote a mechanical fact.  The output is a reviewable JSONL import plan;
this command never writes to the application database.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "deliverables/VerifiedData/us-catalog-universe/index.json"
DEFAULT_DB = ROOT / "autoexpert.db"
DEFAULT_OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-01"
RIGHTS_REFERENCE = "https://www.copyright.gov/help/faq/faq-protect.html"
AZ_RIGHTS_REFERENCE = (
    "https://www.copat.gov.az/docs/Qanunvericilik/Qanunlar/English/Law-Database.pdf"
)
RIGHTS_DATE = "2026-09-28"

# This is deliberately a publisher-host allowlist, not a general PDF allowlist.
# It controls automatic *fact extraction* only; no document text/image licence
# or wholesale permission is inferred.  A new host must be reviewed explicitly.
PUBLISHER_HOSTS = {
    "factory-audi-us": ("audiusa.com", "audi.com"),
    "factory-bmw-us": ("bmwgroup.com", "bmwusa.com"),
    "factory-cadillac-us": ("cadillac.com", "gm.com"),
    "factory-chevrolet-us": ("chevrolet.com", "gm.com"),
    "factory-honda-us": ("honda.com", "hondainfocenter.com"),
    "factory-hyundai-us": ("hyundaiusa.com", "hyundainews.com"),
    "factory-infiniti-us": ("infinitiusa.com", "infinitinews.com"),
    "factory-jeep-us": ("jeep.com", "stellantisfleet.com", "stellantisnorthamerica.com"),
    "factory-kia-us": ("kia.com", "kiamedia.com"),
    "factory-land-rover-us": ("landroverusa.com", "jaguarlandrover.com"),
    "factory-lexus-us": ("lexus.com",),
    "factory-mercedes-us": ("mbusa.com", "mercedes-benz.com"),
    "factory-mitsubishi-us": ("mitsubishicars.com",),
    "factory-nissan-us": ("nissanusa.com", "nissannews.com"),
    "factory-tesla-us": ("tesla.com",),
    "factory-toyota-us": ("toyota.com",),
    "factory-volkswagen-us": ("vw.com", "volkswagen.com"),
    "factory-vw-us": ("vw.com", "volkswagen.com"),
}

MECHANICAL_FACTS = (
    "powertrain",
    "fuel",
    "engine_displacement",
    "engine_description",
    "engine_code",
    "cylinders",
    "aspiration",
    "motor_description",
    "transmission_description",
    "transmission_family",
    "drivetrain",
)
IDENTITY_FACTS = ("make", "model", "model_year", "original_market")


def compact(value: object) -> str:
    return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())


def fact(catalog: dict, key: str) -> dict:
    entry = (catalog.get("facts") or {}).get(key) or {}
    if entry.get("status") != "CONFIRMED" or entry.get("value") in (None, "", "UNKNOWN"):
        return {}
    return entry


def number(value: object) -> Decimal | None:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (TypeError, InvalidOperation):
        return None


def publisher_host(source_id: str, url: str) -> bool:
    parts = urlparse(url)
    if parts.scheme != "https" or parts.username or parts.password:
        return False
    host = (parts.hostname or "").lower().rstrip(".")
    return any(
        host == suffix or host.endswith("." + suffix)
        for suffix in PUBLISHER_HOSTS.get(source_id, ())
    )


def document_kind(url: str) -> str | None:
    path = urlparse(url).path.lower()
    host = (urlparse(url).hostname or "").lower()
    if "service.tesla.com" in host or "owners-manual" in path or "owners_manual" in path:
        return "OWNER_MANUAL"
    if (
        "specification" in path
        or "facts-guide" in path
        or "trimwalk" in path
        or "/feature-guide/features-by-trim/" in path
    ):
        return "SPEC_SHEET"
    if path.endswith(".pdf") or path.endswith(".ashx"):
        return "BROCHURE"
    if any(token in host for token in ("press", "media", "news")):
        return "PRESS_KIT"
    return None


def scoped_reference(catalog: dict, entry: dict) -> tuple[dict, str]:
    ref = entry.get("documentary_source") or {}
    source_id = catalog.get("source_registry_id") or ""
    year = catalog.get("model_year")
    if ref.get("registry_id") != source_id or not source_id.startswith("factory-"):
        return ref, "NONFACTORY_DOCUMENTARY_SOURCE"
    if ref.get("make") != catalog.get("make") or ref.get("model") != catalog.get("model"):
        return ref, "DOCUMENT_IDENTITY_MISMATCH"
    if ref.get("market") != "US" or catalog.get("original_market") != "US":
        return ref, "DOCUMENT_MARKET_MISMATCH"
    exact_year = ref.get("model_year") == year
    year_range = (
        isinstance(ref.get("model_year_from"), int)
        and isinstance(ref.get("model_year_to"), int)
        and ref["model_year_from"] <= year <= ref["model_year_to"]
    )
    if not (exact_year or year_range):
        return ref, "DOCUMENT_YEAR_UNRESOLVED"
    if not entry.get("source_id") or not ref.get("url") or not ref.get("document_id"):
        return ref, "DOCUMENT_PROVENANCE_MISSING"
    if not publisher_host(source_id, ref["url"]):
        return ref, "NON_PUBLISHER_HOST"
    if not document_kind(ref["url"]):
        return ref, "DOCUMENT_KIND_UNRESOLVED"
    return ref, "OFFICIAL_PUBLISHER"


def factual_value_ok(value: object) -> bool:
    if isinstance(value, (int, float)):
        return True
    if not isinstance(value, str):
        return False
    return bool(value.strip()) and len(value) <= 120 and not any(c in value for c in "\n\r\t")


def configuration_keys(catalog: dict) -> dict:
    required = ("engine_displacement", "transmission_description", "drivetrain")
    keys = {key: fact(catalog, key).get("value") for key in required}
    if fact(catalog, "powertrain").get("value") in {"BEV", "FCEV"}:
        # An explicit absent displacement is part of the source-scoped BEV key.
        keys["motor_description"] = fact(catalog, "motor_description").get("value")
    elif fact(catalog, "engine_description"):
        keys["engine_description"] = fact(catalog, "engine_description").get("value")
    else:
        keys["engine_code"] = fact(catalog, "engine_code").get("value")
    return keys


def factory_claims(variant: dict) -> tuple[list[dict], list[str]]:
    catalog = variant["catalog"]
    config = configuration_keys(catalog)
    reasons = []
    required_key_names = ("transmission_description", "drivetrain")
    if fact(catalog, "powertrain").get("value") in {"BEV", "FCEV"}:
        required_key_names += ("motor_description",)
    else:
        required_key_names += ("engine_displacement",)
    if any(config.get(key) in (None, "") for key in required_key_names):
        reasons.append("UNRESOLVED_ENGINE_TRANSMISSION_OR_DRIVETRAIN")
    configuration_complete = not reasons
    source_claims = []
    for name in MECHANICAL_FACTS:
        entry = fact(catalog, name)
        if not entry:
            continue
        ref, source_state = scoped_reference(catalog, entry)
        if not factual_value_ok(entry["value"]):
            source_state = "NON_PRIMITIVE_VALUE"
        # Optional fields can remain unknown/needs-review without suppressing
        # an otherwise complete base configuration.
        source_claims.append((name, entry, ref, source_state))

    # Identity is tied to the same annual manufacturer document as the
    # configuration.  Never copy an EPA make/model/year into these claims.
    anchor = next(
        (
            (entry, ref)
            for name, entry, ref, state in source_claims
            if name in {"powertrain", "engine_description", "transmission_description"}
            and state == "OFFICIAL_PUBLISHER"
        ),
        None,
    )
    if anchor is None:
        reasons.append("NO_DIRECT_MANUFACTURER_IDENTITY_ANCHOR")

    claims = []
    for name, entry, ref, state in source_claims:
        scoped_state = state if configuration_complete else "UNRESOLVED_CONFIGURATION_KEY"
        claims.append(_claim(variant, name, entry["value"], entry, ref, scoped_state, config))
    if anchor is not None:
        entry, ref = anchor
        for name in IDENTITY_FACTS:
            claims.append(
                _claim(
                    variant,
                    name,
                    catalog[name],
                    entry,
                    ref,
                    "OFFICIAL_PUBLISHER",
                    config,
                )
            )
    return claims, sorted(set(reasons))


def _claim(
    variant: dict, name: str, value: object, entry: dict, ref: dict, state: str, config: dict
) -> dict:
    catalog = variant["catalog"]
    source_id = catalog["source_registry_id"]
    scope = {
        "make": catalog["make"],
        "model": catalog["model"],
        "model_year": catalog["model_year"],
        "original_market": "US",
        "granularity": "EXACT_CONFIGURATION",
        "configuration_keys": config,
        "source_record_id": entry.get("source_id"),
        "source_authenticity": "OFFICIAL_PUBLISHER"
        if state == "OFFICIAL_PUBLISHER"
        else "UNREVIEWED_HOST",
        "extraction_scope": "ISOLATED_FACT" if state == "OFFICIAL_PUBLISHER" else "UNREVIEWED",
        "source_document_kind": document_kind(ref.get("url") or ""),
        "az_rights_reference": AZ_RIGHTS_REFERENCE,
    }
    return {
        "variant_id": variant["id"],
        "catalog_key": variant["catalog_key"],
        "fact_name": name,
        "value": value,
        "source_id": source_id,
        "evidence_scope": scope,
        "reuse_status": "COMMERCIAL_OK" if state == "OFFICIAL_PUBLISHER" else "NEEDS_REVIEW",
        "source_url": ref.get("url") or catalog.get("source_url"),
        # A short locator points at a structured, previously reviewed field;
        # the source document's creative wording is never copied to output.
        "locator": f"catalog-fact:{name};document:{ref.get('document_id') or 'unknown'}",
        "rights_basis": "FACTUAL_EXTRACTION" if state == "OFFICIAL_PUBLISHER" else None,
        "rights_reference": RIGHTS_REFERENCE if state == "OFFICIAL_PUBLISHER" else None,
        "rights_checked_at": RIGHTS_DATE if state == "OFFICIAL_PUBLISHER" else None,
        "unit": entry.get("unit"),
    }


def _published_us_variants(db_path: Path):
    uri = db_path.resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    try:
        for variant_id, key, specs in db.execute(
            "SELECT id,catalog_key,specifications FROM vehicle_variants "
            "WHERE published_revision_id IS NOT NULL AND is_demo=0 "
            "AND json_extract(specifications,'$.catalog.original_market')='US'"
        ):
            catalog = (json.loads(specs or "{}")).get("catalog") or {}
            if catalog:
                yield {"id": variant_id, "catalog_key": key, "catalog": catalog}
    finally:
        db.close()


def _transmission(catalog: dict) -> tuple[str | None, int | None]:
    description = str(fact(catalog, "transmission_description").get("value") or "").lower()
    family = str(fact(catalog, "transmission_family").get("value") or "").upper()
    gears = re.search(r"(?:^|\D)(\d{1,2})\s*(?:[- ]?speed|[- ]?spd|at\b|mt\b|dct\b)", description)
    if not gears:
        gears = re.search(r"\b(?:a|am|av)(\d{1,2})\b", description)
    count = int(gears[1]) if gears else None
    if family == "MANUAL" or "manual" in description and "automated" not in description:
        return "MANUAL", count
    if (
        family in {"CVT", "ECVT", "VARIABLE_UNSPECIFIED"}
        or "variable" in description
        or "cvt" in description
    ):
        return "VARIABLE", None
    if family == "SINGLE_SPEED" or "single-speed" in description or "single speed" in description:
        return "SINGLE_SPEED", None
    if (
        family in {"AT", "DCT", "AMT", "AUTOMATIC_UNSPECIFIED", "AMT_UNSPECIFIED"}
        or "automatic" in description
        or "dct" in description
    ):
        return "AUTOMATIC", count
    return None, count


def _mechanical_key(catalog: dict) -> tuple:
    return (
        compact(catalog.get("make")),
        compact(catalog.get("model")),
        catalog.get("model_year"),
        fact(catalog, "powertrain").get("value"),
        fact(catalog, "fuel").get("value"),
        number(fact(catalog, "engine_displacement").get("value")),
        _transmission(catalog),
        str(fact(catalog, "drivetrain").get("value") or "").upper(),
    )


def _qa_matches(epa: dict, factory_index: dict[tuple, list[dict]]) -> list[dict]:
    # This is a QA comparison, never a commercial fact claim.  A coarse EPA
    # tuple cannot independently establish factory engine/gearbox identity.
    key = _mechanical_key(epa["catalog"])
    return factory_index.get(key, [])


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def run(db_path: Path = DEFAULT_DB, out: Path = DEFAULT_OUT) -> dict:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    sha = index["source"]["zip_sha256"]
    variants = list(_published_us_variants(db_path))
    factory = [
        v for v in variants if v["catalog"].get("source_registry_id", "").startswith("factory-")
    ]
    epa = [
        v
        for v in variants
        if v["catalog"].get("source_registry_id") == "epa"
        and v["catalog"].get("source_provenance", {}).get("dataset_sha256") == sha
    ]
    claims = []
    exceptions = []
    production_ready = []
    factory_index = defaultdict(list)
    for variant in factory:
        factory_index[_mechanical_key(variant["catalog"])].append(variant)
        row_claims, reasons = factory_claims(variant)
        claims.extend(row_claims)
        status_by_name = {claim["fact_name"]: claim["reuse_status"] for claim in row_claims}
        required = set(IDENTITY_FACTS) | {
            "powertrain",
            "fuel",
            "transmission_description",
            "drivetrain",
        }
        if fact(variant["catalog"], "powertrain").get("value") in {"BEV", "FCEV"}:
            required.add("motor_description")
        else:
            required.add("engine_displacement")
            if not (
                fact(variant["catalog"], "engine_description")
                or fact(variant["catalog"], "engine_code")
            ):
                reasons.append("ENGINE_IDENTITY_NOT_DISAMBIGUATED")
            else:
                required.add(
                    "engine_description"
                    if fact(variant["catalog"], "engine_description")
                    else "engine_code"
                )
        if all(status_by_name.get(name) == "COMMERCIAL_OK" for name in required) and not reasons:
            production_ready.append(variant)
        else:
            exceptions.append(
                {
                    "catalog_key": variant["catalog_key"],
                    "make": variant["catalog"].get("make"),
                    "model": variant["catalog"].get("model"),
                    "model_year": variant["catalog"].get("model_year"),
                    "reason_codes": sorted(
                        set(reasons)
                        | {
                            f"MISSING_SAFE_{name.upper()}"
                            for name in required
                            if status_by_name.get(name) != "COMMERCIAL_OK"
                        }
                    ),
                }
            )
    qa = []
    qa_counts = Counter()
    for variant in epa:
        matches = _qa_matches(variant, factory_index)
        status = "UNMATCHED_RESEARCH_ONLY"
        if len(matches) == 1:
            status = "POSSIBLE_FACTORY_EQUIVALENT_SUPPRESS_EPA"
        elif len(matches) > 1:
            status = "AMBIGUOUS_FACTORY_EQUIVALENT_REVIEW"
        qa_counts[status] += 1
        qa.append(
            {
                "epa_catalog_key": variant["catalog_key"],
                "make": variant["catalog"].get("make"),
                "model": variant["catalog"].get("model"),
                "model_year": variant["catalog"].get("model_year"),
                "qa_status": status,
                "factory_catalog_keys": [v["catalog_key"] for v in matches],
            }
        )

    out.mkdir(parents=True, exist_ok=True)
    _jsonl(out / "factory-fact-claims-dry-run.jsonl", claims)
    _jsonl(out / "factory-agent-review.jsonl", exceptions)
    _jsonl(out / "epa-core-factory-qa.jsonl", qa)
    ready_named = sorted({(v["catalog"]["make"], v["catalog"]["model"]) for v in production_ready})
    review_reasons = Counter(reason for row in exceptions for reason in row["reason_codes"])
    summary = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "writes_to_application_database": False,
        "epa_source_sha256": sha,
        "epa_exact_zip_rows_qa_only": len(epa),
        "factory_rows_considered": len(factory),
        "factory_claims_emitted": len(claims),
        "factory_commercial_ok_claims": sum(c["reuse_status"] == "COMMERCIAL_OK" for c in claims),
        "factory_needs_review_claims": sum(c["reuse_status"] == "NEEDS_REVIEW" for c in claims),
        "factory_rows_with_complete_safe_claims": len(production_ready),
        "factory_models_with_complete_safe_claims": len(ready_named),
        "factory_ready_model_names": [f"{make} {model}" for make, model in ready_named],
        "factory_rows_needing_review": len(exceptions),
        "factory_review_reason_counts": dict(sorted(review_reasons.items())),
        "epa_qa_status": dict(sorted(qa_counts.items())),
        "vpic_limitation": (
            "GetModelsForMakeYear corroborates only make/model/model-year, "
            "never engine/transmission/drivetrain"
        ),
        "publication_note": (
            "The dry-run plan does not make a row production-visible; "
            "apply through commercial_fact_overlay after review."
        ),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(run(args.db, args.out), ensure_ascii=False, indent=2))
