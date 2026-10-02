"""Source-only BMW USA G30 candidate; no shared ledger or database writes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/bmw-g30-source-work"
CACHE = ROOT / ".localdata/us-base-catalog-07-bmw-g30-documents"
RECEIPT = WORK / "acquisition-receipts.json"
MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-bmw-g30.json"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"

URLS = {
    "bmw-g30-us-2017-launch": "https://www.press.bmwgroup.com/usa/article/detail/T0264802EN_US/the-all-new-2017-bmw-5-series%3A-performance-redefined",
    "bmw-g30-us-2017-technical": "https://www.press.bmwgroup.com/usa/article/attachment/T0264802EN_US/402275",
    "bmw-g30-us-2017-pricing": "https://www.press.bmwgroup.com/usa/article/detail/T0266788EN_US/bmw-announces-price-for-the-all-new-2017-bmw-5-series",
    "bmw-g30-us-2018-technical": "https://www.press.bmwgroup.com/usa/article/attachment/T0264802EN_US/402277",
    "bmw-g30-us-2018-update": "https://www.press.bmwgroup.com/usa/article/detail/T0271729EN_US/model-year-2018-update-information",
    "bmw-g30-us-generation-code": "https://www.press.bmwgroup.com/usa/article/attachment/T0266788EN_US/391871",
    "bmw-g30-us-2019-brochure": "https://www.auto-brochures.com/makes/BMW/5%20Series/BMW_US%205Series_2019.pdf",
    "bmw-g30-us-2019-pricing-530": "https://www.bimmerpost.com/goodiesforyou/priceguides/2019/2019%20BMW%20530i_30e%20%28G30%29%20Rel%202018-05-29%20-%20PricingGuide_Retail.pdf",
    "bmw-g30-us-2019-pricing-540": "https://www.bimmerpost.com/goodiesforyou/priceguides/2019/2019%20BMW%20540i_40d_M50i%20%28G30%29%20Rel%202018-06-04%20-%20PricingGuide_Retail.pdf",
    "bmw-g30-us-2020-update": "https://www.press.bmwgroup.com/usa/article/detail/T0299940EN_US/bmw-model-year-2020-update-information",
}


def acquire() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    receipts = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.exists() else []
    for name, url in URLS.items():
        if any(
            r.get("url") == url and r.get("sha256") and (ROOT / r["path"]).exists()
            for r in receipts
        ):
            continue
        tmp = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".tmp")
        start = time.monotonic()
        proc = subprocess.run(
            [
                "curl.exe",
                "--silent",
                "--show-error",
                "--max-time",
                "65",
                "--max-filesize",
                "70000000",
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
            "name": name,
            "url": url,
            "observed_at": datetime.now(UTC).isoformat(),
            "http_status": int(proc.stdout or 0),
            "latency_ms": round((time.monotonic() - start) * 1000),
            "cost_usd": "0.00",
        }
        if proc.returncode or rec["http_status"] != 200:
            rec["error"] = f"FETCH_FAILED_{proc.returncode}"
        elif (
            name.endswith("brochure")
            or name.endswith("pricing")
            and name != "bmw-g30-us-2017-pricing"
        ) and not raw.startswith(b"%PDF-"):
            rec["error"] = "PDF_CONTENT_MISMATCH"
        else:
            digest = hashlib.sha256(raw).hexdigest()
            dest = CACHE / digest
            dest.write_bytes(raw)
            rec.update(
                sha256=digest,
                path=str(dest.relative_to(ROOT)).replace("\\", "/"),
                byte_size=len(raw),
                media_type="application/pdf" if raw.startswith(b"%PDF-") else "text/html",
            )
        tmp.unlink(missing_ok=True)
        receipts.append(rec)
        RECEIPT.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
        print(json.dumps(rec), flush=True)


def fact(value, document_key=None, unit=None):
    return {
        "value": value,
        **({"document_key": document_key} if document_key else {}),
        **({"unit": unit} if unit else {}),
    }


def build() -> None:
    """Emit only annual factory table rows independently matched to EPA complete tuples."""
    started = time.perf_counter()
    sys.path.insert(0, str(ROOT / "backend"))
    from app.db.session import SessionLocal
    from app.models.knowledge_ops import RawDocument
    from app.services.knowledge_import import document_text, private_path
    from app.services.market_priority import base_catalog_batch
    from pypdf import PdfReader

    receipts = {
        r["name"]: r
        for r in json.loads(RECEIPT.read_text(encoding="utf-8"))
        if r.get("sha256") and r.get("http_status") == 200 and not r.get("error")
    }
    required = [
        "bmw-g30-us-2017-launch",
        "bmw-g30-us-2017-technical",
        "bmw-g30-us-2017-pricing",
        "bmw-g30-us-2018-technical",
        "bmw-g30-us-generation-code",
    ]
    assert all(name in receipts for name in required)
    for name in required:
        r = receipts[name]
        raw = (ROOT / r["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == r["sha256"]

    def pdf_text(name):
        raw = (ROOT / receipts[name]["path"]).read_bytes()
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)

    t17 = pdf_text("bmw-g30-us-2017-technical")
    t18 = pdf_text("bmw-g30-us-2018-technical")
    assert all(
        x in t17
        for x in [
            "Preliminary Technical Specifications",
            "B46B20O0",
            "B58B30M0",
            "8HP50",
            "RWD AWD RWD AWD",
        ]
    )
    assert all(
        x in t18
        for x in [
            "2018 BMW 5 Series Sedan",
            "B46B20O0",
            "B58B30M0",
            "N63B44O2",
            "8P75H",
            "RWD AWD RWD AWD AWD RWD AWD",
        ]
    )
    with SessionLocal() as db:
        epa_doc = db.get(RawDocument, EPA_DOC)
        epa = list(
            csv.DictReader(
                document_text(private_path(epa_doc.storage_key).read_bytes()).splitlines()
            )
        )

    docs = {
        "launch17": {
            "url": URLS["bmw-g30-us-2017-launch"],
            "source_id": "factory-bmw-us",
            "publisher": "BMW of North America PressClub USA",
            "market": "US",
            "year_from": 2017,
            "year_to": 2018,
            "locator": (
                "MY2017 US G30 launch: seventh-generation sedan identity, "
                "530i/540i engines and 8-speed automatic. Annual PDF governs tuples."
            ),
            "format": "html",
        },
        "tech17": {
            "url": URLS["bmw-g30-us-2017-technical"],
            "source_id": "factory-bmw-us",
            "publisher": "BMW of North America technical data",
            "market": "US",
            "year_from": 2017,
            "year_to": 2017,
            "locator": (
                "PDF pp18–20: four MY2017 US sedan columns, drive, "
                "B46/B58 engine, 8HP50 automatic, dimensions, seats, fuel/oil."
            ),
            "format": "pdf",
        },
        "price17": {
            "url": URLS["bmw-g30-us-2017-pricing"],
            "source_id": "factory-bmw-us",
            "publisher": "BMW of North America PressClub USA",
            "market": "US",
            "year_from": 2017,
            "year_to": 2017,
            "locator": (
                "MY2017 US launch-price announcement names 530i/xDrive "
                "and 540i/xDrive sedan offerings."
            ),
            "format": "html",
        },
        "tech18": {
            "url": URLS["bmw-g30-us-2018-technical"],
            "source_id": "factory-bmw-us",
            "publisher": "BMW of North America technical data",
            "market": "US",
            "year_from": 2018,
            "year_to": 2018,
            "locator": (
                "PDF pp1–2: seven MY2018 US sedan columns; exact drive, "
                "engine, 8HP50/8HP75/8P75H automatic, fuel, dimensions and seats."
            ),
            "format": "pdf",
        },
        "gen": {
            "url": URLS["bmw-g30-us-generation-code"],
            "source_id": "factory-bmw-us",
            "publisher": "BMW of North America MY2018 pricing guide",
            "market": "US",
            "year_from": 2017,
            "year_to": 2018,
            "locator": (
                "BMW North America pricing PDF names 5 Series Sedan (G30); "
                "manufacturer launch article identifies seventh generation."
            ),
            "format": "pdf",
        },
    }

    variants = [
        (
            2017,
            "530i",
            "RWD",
            "2.0",
            "B46B20O0",
            4,
            248,
            258,
            "8HP50",
            194.6,
            58.2,
            18.0,
            5.25,
            "ICE",
        ),
        (
            2017,
            "530i xDrive",
            "AWD",
            "2.0",
            "B46B20O0",
            4,
            248,
            258,
            "8HP50",
            194.6,
            58.2,
            18.0,
            5.25,
            "ICE",
        ),
        (
            2017,
            "540i",
            "RWD",
            "3.0",
            "B58B30M0",
            6,
            335,
            332,
            "8HP50",
            194.6,
            58.2,
            18.0,
            6.5,
            "ICE",
        ),
        (
            2017,
            "540i xDrive",
            "AWD",
            "3.0",
            "B58B30M0",
            6,
            335,
            332,
            "8HP50",
            194.6,
            58.2,
            18.0,
            6.5,
            "ICE",
        ),
        (
            2018,
            "530i",
            "RWD",
            "2.0",
            "B46B20O0",
            4,
            248,
            258,
            "8HP50",
            194.6,
            58.2,
            18.0,
            5.25,
            "ICE",
        ),
        (
            2018,
            "530i xDrive",
            "AWD",
            "2.0",
            "B46B20O0",
            4,
            248,
            258,
            "8HP50",
            194.6,
            58.2,
            18.0,
            5.25,
            "ICE",
        ),
        (
            2018,
            "540i",
            "RWD",
            "3.0",
            "B58B30M0",
            6,
            335,
            332,
            "8HP50",
            194.6,
            58.2,
            18.0,
            6.5,
            "ICE",
        ),
        (
            2018,
            "540i xDrive",
            "AWD",
            "3.0",
            "B58B30M0",
            6,
            335,
            332,
            "8HP50",
            194.6,
            58.2,
            18.0,
            6.5,
            "ICE",
        ),
        (
            2018,
            "M550i xDrive",
            "AWD",
            "4.4",
            "N63B44O2",
            8,
            456,
            480,
            "8HP75",
            195.4,
            57.8,
            18.0,
            10.0,
            "ICE",
        ),
        (
            2018,
            "530e",
            "RWD",
            "2.0",
            "B46B20O0",
            4,
            248,
            310,
            "8P75H",
            194.6,
            58.4,
            12.1,
            5.25,
            "PHEV",
        ),
        (
            2018,
            "530e xDrive",
            "AWD",
            "2.0",
            "B46B20O0",
            4,
            248,
            310,
            "8P75H",
            194.6,
            58.4,
            12.1,
            5.25,
            "PHEV",
        ),
    ]
    groups = []
    for (
        year,
        name,
        drive,
        disp,
        code,
        cylinders,
        hp,
        torque,
        txcode,
        length,
        height,
        tank,
        oil,
        powertrain,
    ) in variants:
        r = [
            row
            for row in epa
            if row["year"] == str(year)
            and row["make"] == "BMW"
            and row["model"] == name
            and row["displ"] == disp
            and row["trany"] == "Automatic (S8)"
            and row["drive"] == {"RWD": "Rear-Wheel Drive", "AWD": "All-Wheel Drive"}[drive]
        ]
        assert len(r) == 1, (year, name, len(r))
        tech = "tech17" if year == 2017 else "tech18"
        engine = (
            f"{name} {disp}L turbo inline-{cylinders}"
            if cylinders != 8
            else f"{name} {disp}L twin-turbo V8"
        )
        if powertrain == "PHEV":
            engine += " + plug-in electric motor"
        groups.append(
            {
                "id": f"{year}-{name.lower().replace(' ', '-')}-{drive.lower()}-8at",
                "year_from": year,
                "year_to": year,
                "configuration": f"{name} {disp}L / 8-speed Steptronic automatic / {drive}",
                "allowed_drives": [drive],
                "factory_combinations": [{"drivetrain": drive}],
                "epa_drive_match": {"model": [name], "displ": [disp], "trany": ["Automatic (S8)"]},
                "locator": (
                    f"BMW NA MY{year} technical PDF {name} column: {code}, "
                    f"{hp} hp, {txcode} 8AT, {drive}. EPA ID {r[0]['id']} confirms drive."
                ),
                "facts": {
                    "body": fact("SEDAN", tech),
                    "seats": fact(5, tech),
                    "powertrain": fact(powertrain, tech),
                    "fuel": fact("GASOLINE", tech),
                    "engine_description": fact(engine, tech),
                    "engine_displacement": fact(float(disp), tech, "L"),
                    "engine_code": fact(code, tech),
                    "cylinders": fact(cylinders, tech),
                    "aspiration": fact("TURBO", tech),
                    "power_hp": fact(hp, tech, "hp"),
                    "torque_lb_ft": fact(torque, tech, "lb-ft"),
                    "transmission_family": fact("AT", tech),
                    "transmission_description": fact("8-speed Steptronic automatic", tech),
                    "transmission_code": fact(txcode, tech),
                    "gears": fact(8, tech),
                    "trim": fact(name, tech),
                    "octane_aki": fact(91, tech, "AKI"),
                    "fuel_tank_us_gal": fact(tank, tech, "US gal"),
                    "engine_oil_capacity_l": fact(oil, tech, "L"),
                    "engine_oil_capacity_note": fact(
                        "Factory engine-oil filling quantity; service refill may differ", tech
                    ),
                    "length_in": fact(length, tech, "in"),
                    "width_in": fact(73.5, tech, "in"),
                    "height_in": fact(height, tech, "in"),
                    "wheelbase_in": fact(117.1, tech, "in"),
                },
            }
        )
    manifest = {
        "version": "basic-catalog-07-independent-source-candidate-bmw-g30",
        "batch_id": "us-base-catalog-07-source-bmw-g30",
        "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
        "selection_status": "OWNER_MASTER_LIST_INDEPENDENT_BMW_US_ANNUAL_TABLES",
        "epa_document_id": EPA_DOC,
        "documents": docs,
        "families": [
            {
                "id": "bmw-5series-g30-us-2017-2018-source07",
                "make": "BMW",
                "model": "5 Series",
                "generation": "G30 sedan (seventh generation)",
                "generation_code": "G30",
                "market": "US",
                "year_from": 2017,
                "year_to": 2018,
                "local_relevance_tier": 1,
                "local_generation_year_priority": 1,
                "source_availability_rank": 1,
                "annual_documents": {"2017": ["tech17", "price17"], "2018": ["tech18"]},
                "generation_documents": ["launch17", "gen"],
                "scope_note": (
                    "BMW USA G30 5 Series sedan only. Each annual engine, "
                    "8AT and drive tuple is in its own BMW technical column and "
                    "independently drive-matched to EPA."
                ),
                "exclude": [
                    "Other years or markets",
                    "G31 Touring, Gran Turismo, F90 M5",
                    "Unlisted diesel and 2017 PHEV/M550i without annual complete tuple",
                    "MY2019–2020 pending US gearbox source",
                ],
                "groups": groups,
            }
        ],
    }
    assert (
        base_catalog_batch(manifest=manifest)["families"][0]["id"] == manifest["families"][0]["id"]
    )
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (WORK / "review.json").write_text(
        json.dumps(
            {
                "at": datetime.now(UTC).isoformat(),
                "rows": len(groups),
                "years": {"2017": 4, "2018": 7},
                "epa_match_count": len(groups),
                "documents": {
                    k: receipts[name]["sha256"]
                    for k, name in {
                        "launch17": required[0],
                        "tech17": required[1],
                        "price17": required[2],
                        "tech18": required[3],
                        "gen": required[4],
                    }.items()
                },
                "holds": [
                    "MY2017 M550i/530e: absent from current EPA full tuple cache",
                    "MY2019 US brochure acquired; gearbox guide HTTP403/timeout; held",
                    "MY2020 US update lacks full annual engine×gearbox matrix; held",
                ],
                "seconds_review_builder": round(time.perf_counter() - started, 3),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "manifest": str(MANIFEST.relative_to(ROOT)),
                "families": 1,
                "rows": len(groups),
                "seconds": round(time.perf_counter() - started, 3),
            }
        )
    )


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--build", action="store_true")
    opts = args.parse_args()
    build() if opts.build else acquire()
