"""Source-only Toyota USA RAV4 fifth-generation MY2019-2021 reviewed packet.

This script writes only a candidate manifest and local review/receipt artifacts. It
reads the existing EPA raw document, and it does not publish or mutate the live DB.
"""
# ruff: noqa: E501

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from app.db.session import SessionLocal
from app.models.knowledge_ops import RawDocument
from app.schemas.knowledge import CatalogRecord
from app.services.knowledge_import import document_text, epa_record, private_path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/rav4-source-work"
CACHE = ROOT / ".localdata/us-base-catalog-07-rav4-documents"
MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-toyota-rav4-v.json"
RECEIPTS = WORK / "acquisition-receipts.json"
REVIEW = WORK / "source-review.json"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"

URLS = {
    "rav4-v-2019-us-source07": "https://www.auto-brochures.com/makes/Toyota/RAV4/Toyota_US%20RAV4_2019-2.pdf",
    "rav4-v-2020-us-source07": "https://www.auto-brochures.com/makes/Toyota/RAV4/Toyota_US%20RAV4_2020.pdf",
    "rav4-v-2021-us-source07": "https://www.auto-brochures.com/makes/Toyota/RAV4/Toyota_US%20RAV4_2021.pdf",
    "rav4-v-generation-us-source07": "https://pressroom.toyota.com/vehicle/2020-toyota-rav4/",
}


def acquire() -> list[dict]:
    WORK.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    receipts = json.loads(RECEIPTS.read_text(encoding="utf-8")) if RECEIPTS.exists() else []
    for key, url in URLS.items():
        if any(
            row.get("url") == url
            and row.get("http_status") == 200
            and row.get("sha256")
            and (ROOT / row["path"]).exists()
            for row in receipts
        ):
            continue
        tmp = CACHE / f"{hashlib.sha256(url.encode()).hexdigest()}.tmp"
        began = time.monotonic()
        proc = subprocess.run(
            [
                "curl.exe",
                "--location",
                "--silent",
                "--show-error",
                "--max-time",
                "60",
                "--max-filesize",
                "30000000",
                "--proto",
                "=https",
                "--output",
                str(tmp),
                "--write-out",
                "%{http_code}",
                url,
            ],
            capture_output=True,
            text=True,
        )
        raw = tmp.read_bytes() if tmp.exists() else b""
        rec = {
            "key": key,
            "url": url,
            "http_status": int(proc.stdout or 0),
            "observed_at": datetime.now(UTC).isoformat(),
            "latency_ms": round((time.monotonic() - began) * 1000),
            "cost_usd": "0.00",
        }
        if proc.returncode or rec["http_status"] != 200:
            rec["error"] = f"FETCH_FAILED_{proc.returncode}: {proc.stderr[:200]}"
        elif key != "rav4-v-generation-us-source07" and not raw.startswith(b"%PDF-"):
            rec["error"] = "PDF_CONTENT_MISMATCH"
        elif key == "rav4-v-generation-us-source07" and b"fifth-generation" not in raw:
            rec["error"] = "GENERATION_TEXT_NOT_FOUND"
        else:
            sha = hashlib.sha256(raw).hexdigest()
            path = CACHE / sha
            path.write_bytes(raw)
            rec.update(sha256=sha, path=path.relative_to(ROOT).as_posix(), byte_size=len(raw))
        tmp.unlink(missing_ok=True)
        receipts.append(rec)
        RECEIPTS.write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding="utf-8")
        if rec.get("error"):
            raise RuntimeError(f"SOURCE_ACQUISITION_FAILED: {key}: {rec['error']}")
    return receipts


def fact(value, unit=None):
    return {"value": value, **({"unit": unit} if unit else {})}


def make_group(year: int, grade: str, kind: str, drives: tuple[str, ...]) -> dict:
    is_hybrid = kind == "hybrid"
    label = f"RAV4 Hybrid {grade}" if is_hybrid else f"RAV4 {grade}"
    model = ["RAV4 Hybrid  AWD", "RAV4 Hybrid AWD"] if is_hybrid else ["RAV4", "RAV4 AWD"]
    if not is_hybrid and grade == "LE" and year >= 2020:
        model = ["RAV4", "RAV4 AWD LE"]
    if not is_hybrid and grade == "TRD Off-Road":
        model = ["RAV4 AWD TRD OFFROAD"]
    elif not is_hybrid and drives == ("AWD",):
        model = ["RAV4 AWD"]
    description = (
        "2.5L Dynamic Force 4-cylinder gasoline and hybrid electric motors; "
        "219 hp combined net system"
        if is_hybrid
        else "2.5L Dynamic Force 4-cylinder gasoline"
    )
    transmission = (
        "Electronically Controlled Continuously Variable Transmission (ECVT)"
        if is_hybrid
        else "Direct Shift 8-speed automatic (ECT-i)"
    )
    facts = {
        "trim": grade if not is_hybrid else f"Hybrid {grade}",
        "powertrain": "HEV" if is_hybrid else "ICE",
        "engine_description": description,
        "engine_displacement": fact(2.5, "L"),
        "transmission_family": "ECVT" if is_hybrid else "AT",
        "transmission_description": transmission,
    }
    if not is_hybrid:
        facts.update(power_hp=203, torque_lb_ft=fact(184, "lb-ft"), gears=8)
    page = "39-40" if year < 2021 else "24-26"
    drive_description = "/".join(drives)
    return {
        "id": f"{year}-{kind}-{grade.lower().replace(' ', '-').replace('/', '-')}",
        "year_from": year,
        "year_to": year,
        "configuration": f"{label} 2.5L / {transmission}",
        "allowed_drives": list(drives),
        "factory_combinations": [{"drivetrain": drive} for drive in drives],
        "epa_drive_match": {
            "model": model,
            "displ": ["2.5"],
            "trany": ["Automatic (AV-S6)" if is_hybrid else "Automatic (S8)"],
        },
        "locator": (
            f"Toyota USA MY{year} RAV4 manufacturer brochure PDF pp{page}: annual "
            f"{label} 2.5L {'HEV/ECVT' if is_hybrid else '203 hp/8AT'} "
            f"grade column with {drive_description} applicability. EPA vehicles.csv exact "
            "annual 2.5L transmission/drive tuple corroborates drive only; EPA's "
            "AV-S6 label is not treated as a conventional six-speed gearbox."
        ),
        "facts": facts,
    }


def manifest() -> dict:
    documents = {}
    for year in (2019, 2020, 2021):
        key = f"rav4-v-{year}-us-source07"
        documents[key] = {
            "url": URLS[key],
            "source_id": "factory-toyota-us",
            "publisher": "Toyota USA manufacturer-authored brochure (archived mirror)",
            "market": "US",
            "year_from": year,
            "year_to": year,
            "locator": (
                f"MY{year} US RAV4 brochure: annual grade model pages and specification "
                f"matrix PDF pp{'39-40' if year < 2021 else '24-26'}; "
                "gas/HEV engine, transmission and drive columns."
            ),
            "format": "pdf",
        }
    documents["rav4-v-generation-us-source07"] = {
        "url": URLS["rav4-v-generation-us-source07"],
        "source_id": "factory-toyota-us",
        "publisher": "Toyota USA Newsroom",
        "market": "US",
        "year_from": 2019,
        "year_to": 2021,
        "locator": (
            "Toyota USA 2020 RAV4 Newsroom product page: fifth-generation RAV4 "
            "introduced in 2019. Generation lineage only; annual powertrains from brochures."
        ),
        "format": "html",
    }
    groups = []
    gas_by_year = {
        2019: ("LE", "XLE", "XLE Premium", "Adventure", "Limited"),
        2020: ("LE", "XLE", "XLE Premium", "Adventure", "TRD Off-Road", "Limited"),
        2021: ("LE", "XLE", "XLE Premium", "Adventure", "TRD Off-Road", "Limited"),
    }
    hybrid_by_year = {
        2019: ("LE", "XLE", "XSE", "Limited"),
        2020: ("LE", "XLE", "XSE", "Limited"),
        2021: ("LE", "XLE", "XLE Premium", "XSE", "Limited"),
    }
    for year in (2019, 2020, 2021):
        for grade in gas_by_year[year]:
            drives = ("AWD",) if grade in {"Adventure", "TRD Off-Road"} else ("FWD", "AWD")
            groups.append(make_group(year, grade, "gas", drives))
        for grade in hybrid_by_year[year]:
            groups.append(make_group(year, grade, "hybrid", ("AWD",)))
    return {
        "version": "basic-catalog-07-independent-source-candidate-rav4-v-1",
        "batch_id": "us-base-catalog-07-source-toyota-rav4-v",
        "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
        "selection_status": "OWNER_MASTER_LIST_TOYOTA_US_ANNUAL_BROCHURES",
        "epa_document_id": EPA_DOC,
        "documents": documents,
        "families": [
            {
                "id": "toyota-rav4-v-us-2019-2021-source07",
                "make": "Toyota",
                "model": "RAV4",
                "generation": "V (2019 redesign, TNGA)",
                "generation_code": None,
                "market": "US",
                "year_from": 2019,
                "year_to": 2021,
                "local_relevance_tier": 1,
                "local_generation_year_priority": 1,
                "source_availability_rank": 1,
                "annual_documents": {
                    str(year): [f"rav4-v-{year}-us-source07"] for year in (2019, 2020, 2021)
                },
                "generation_documents": ["rav4-v-generation-us-source07"],
                "scope_note": (
                    "US RAV4 fifth-generation gasoline and non-plug-in hybrid grade tuples "
                    "MY2019-2021 only. Each model year uses its own Toyota-authored US grade matrix; "
                    "EPA drive confirms only exact annual 2.5L transmission/drive tuple."
                ),
                "exclude": [
                    "2019 earlier RAV4 generation and other model years/markets",
                    "MY2021 RAV4 Prime PHEV SE/XSE; separate plug-in construction",
                    "Unlisted options, trim-drive pairs, exact VIN claims and factory engine code XA50",
                    "EPA AV-S6 simulated-ratio label as evidence for a stepped six-speed gearbox",
                    "Other technical fields not explicitly reviewed in annual factory tables",
                ],
                "facts": {
                    "body": "SUV",
                    "fuel": "GASOLINE",
                    "cylinders": 4,
                    "seats": 5,
                    "wheelbase_in": fact(105.9, "in"),
                },
                "groups": groups,
            }
        ],
    }


def validate_local(data: dict) -> dict:
    with SessionLocal() as db:
        doc = db.get(RawDocument, EPA_DOC)
        rows = list(csv.DictReader(document_text(private_path(doc.storage_key).read_bytes()).splitlines()))
    rows = [
        r for r in rows if r.get("make") == "Toyota" and r.get("year") in {"2019", "2020", "2021"}
    ]
    family = data["families"][0]
    confirmed = []
    for group in family["groups"]:
        year = group["year_from"]
        matching = [
            row
            for row in rows
            if int(row["year"]) == year
            and all(str(row.get(key)) in values for key, values in group["epa_drive_match"].items())
        ]
        available = {epa_record(row).facts["drivetrain"].value for row in matching}
        if available != set(group["allowed_drives"]):
            raise ValueError(
                f"EPA_DRIVE_GAP: {group['id']}: available={available} expected={group['allowed_drives']}"
            )
        for drive in group["allowed_drives"]:
            values = {**family["facts"], **group["facts"], "drivetrain": drive}
            source = data["documents"][family["annual_documents"][str(year)][0]]["url"]
            CatalogRecord.model_validate(
                {
                    "external_key": f"rav4-v-{year}-{group['id']}-{drive}",
                    "make": "Toyota",
                    "model": "RAV4",
                    "configuration": f"{group['configuration']} · {drive}",
                    "original_market": "US",
                    "model_year": year,
                    "generation": family["generation"],
                    "facts": {
                        key: {**(val if isinstance(val, dict) else {"value": val}), "locator": group["locator"]}
                        for key, val in values.items()
                    },
                    "source_url": source,
                }
            )
            confirmed.append(
                {
                    "year": year,
                    "grade": group["facts"]["trim"],
                    "engine": group["facts"]["engine_description"],
                    "transmission": group["facts"]["transmission_family"],
                    "drive": drive,
                    "epa_ids": sorted(
                        row["id"]
                        for row in matching
                        if epa_record(row).facts["drivetrain"].value == drive
                    ),
                }
            )
    return {
        "groups": len(family["groups"]),
        "annual_rows": len(confirmed),
        "rows_by_year": {str(y): sum(r["year"] == y for r in confirmed) for y in (2019, 2020, 2021)},
        "exact_annual_rows": confirmed,
    }


def main() -> None:
    receipts = acquire()
    data = manifest()
    review = validate_local(data)
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    REVIEW.write_text(
        json.dumps(
            {
                "review_status": "SOURCE_REVIEWED_NOT_PUBLISHED",
                "schema_validation": "CatalogRecord.model_validate PASS for each annual row; no DB writes",
                **review,
                "source_http_status": {r["key"]: r["http_status"] for r in receipts},
                "source_sha256": {r["key"]: r["sha256"] for r in receipts},
                "holds": [
                    "Toyota generation code XA50 not in reviewed Toyota USA material; fifth-generation identity confirmed, code left null.",
                    "MY2021 Prime PHEV excluded until separate factory engine/electric-drive row review.",
                    "219 hp hybrid is combined system net output, not gasoline-engine-only power; power_hp fact omitted.",
                    "EPA AV-S6 label represents certification vocabulary and is not imported as a stepped six-speed transmission.",
                    "EPA rows are used for annual drivetrain corroboration only; trim×drive applicability comes from the Toyota matrix.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"manifest": MANIFEST.relative_to(ROOT).as_posix(), "receipt": RECEIPTS.relative_to(ROOT).as_posix(), **{k: review[k] for k in ("groups", "annual_rows", "rows_by_year")}}))


if __name__ == "__main__":
    main()
