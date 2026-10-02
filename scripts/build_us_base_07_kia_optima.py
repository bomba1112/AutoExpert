"""Review Kia's US 2014/15 Optima pricing and trim matrices as annual tuples."""

# ruff: noqa: E501

from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import RawDocument  # noqa: E402
from app.services.factory_bulk_tables import parse_factory_table  # noqa: E402
from app.services.knowledge_import import document_text, private_path  # noqa: E402
from app.services.market_priority import base_catalog_batch  # noqa: E402

OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07"
MANIFEST = ROOT / "data/manifests/us-base-catalog-07-root-kia-optima.json"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"
URLS = {
    "s14": "https://www.kiamedia.com/us/en/models/optima/2014/specifications",
    "f14": "https://www.kiamedia.com/us/en/models/optima/2014/features",
    "p14": "https://www.kiamedia.com/us/en/models/optima/2014/pricing",
    "o14": "https://www.kiamedia.com/us/en/models/optima/2014",
    "s15": "https://www.kiamedia.com/us/en/media/specifications/20416/2015-kia-optima-specifications",
    "f15": "https://www.kiamedia.com/us/en/models/optima/2015/features",
    "p15": "https://www.kiamedia.com/us/en/models/optima/2015/pricing",
    "o15": "https://www.kiamedia.com/us/en/models/optima/2015",
}

# Exact factory pricing rows, reviewed against the source at runtime. No Cartesian pairing.
LINES = (
    ("Optima LX", "2.4L GDI I-4 - 6 A/T", "LX", "2.4"),
    ("Optima EX", "2.4L GDI I-4 - 6 A/T", "EX", "2.4"),
    ("Optima SX", "2.4L GDI I-4 - 6 A/T", "SX", "2.4"),
    ("Optima SX Turbo", "2.0L T-GDI I-4 - 6 A/T", "SX Turbo", "2.0"),
    ("Optima SXL Turbo", "2.0L T-GDI I-4 - 6 A/T", "SXL Turbo", "2.0"),
)


def fact(value, key, unit=None):
    return {"value": value, "document_key": key, **({"unit": unit} if unit else {})}


def pricing_lines(raw):
    soup = BeautifulSoup(raw, "html.parser")
    return [
        tuple(c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])[:2])
        for tr in soup.find_all("tr")
        if tr.get_text(" ", strip=True).startswith("Optima ")
        and " - 6 A/T" in tr.get_text(" ", strip=True)
    ]


def feature(table, trim, prefix):
    row = next(r for r in table.rows if r.group == "Mechanical" and r.label.startswith(prefix))
    return row.values[table.trims.index(trim)]


def spec_value(table, trim, group, label):
    idx = table.trims.index(trim)
    return next(r.values[idx] for r in table.rows if r.group == group and r.label == label)


def main():
    started = time.perf_counter()
    receipts = {
        r["url"]: r
        for r in json.loads(
            (ROOT / "deliverables/VerifiedData/base-catalog-acquisition.json").read_text(
                encoding="utf-8"
            )
        )
        if r.get("http_status") == 200 and r.get("sha256") and not r.get("error")
    }
    raw = {
        key: (ROOT / ".localdata/verified-source-documents" / receipts[url]["sha256"]).read_bytes()
        for key, url in URLS.items()
    }
    with SessionLocal() as db:
        epa_doc = db.get(RawDocument, EPA_DOC)
        epa = list(
            csv.DictReader(
                document_text(private_path(epa_doc.storage_key).read_bytes()).splitlines()
            )
        )
    docs = {}
    groups = []
    for year in (2014, 2015):
        yy = str(year)[-2:]
        features = parse_factory_table(raw[f"f{yy}"])
        specs = parse_factory_table(raw[f"s{yy}"])
        assert features.trims == specs.trims == tuple(line[2] for line in LINES)
        assert Counter(pricing_lines(raw[f"p{yy}"])) == Counter(
            (line[0], line[1]) for line in LINES
        )
        transmission = "Automatic 6-spd" if year == 2014 else "Automatic (S6)"
        for listed, pricing_label, trim, displacement in LINES:
            assert (
                feature(
                    features,
                    trim,
                    "2.4L four-cylinder engine GDI"
                    if displacement == "2.4"
                    else "2.0L turbocharged four-cylinder GDI",
                )
                == "S"
            )
            assert feature(features, trim, "6-speed automatic transmission") == "S"

            def spec(group, label, table=specs, target_trim=trim):
                return spec_value(table, target_trim, group, label)

            assert spec("Engine", "Displacement (cc)").startswith(
                "2,359" if displacement == "2.4" else "1,998"
            )
            assert spec("Engine", "Horsepower").startswith(
                "ULEV-II: 192" if displacement == "2.4" else "274"
            )
            assert spec("Engine", "Torque").startswith(
                "ULEV-II: 181" if displacement == "2.4" else "269"
            )
            assert spec("Drivetrain", "Transmission") == "6-speed Sportmatic automatic"
            found = [
                r
                for r in epa
                if r["year"] == str(year)
                and r["make"] == "Kia"
                and r["model"] == "Optima"
                and r["displ"] == displacement
                and r["trany"] == transmission
            ]
            assert len(found) == 1 and found[0]["drive"] == "Front-Wheel Drive"
            facts = {
                "body": fact("SEDAN", f"o{yy}"),
                "powertrain": fact("ICE", f"o{yy}"),
                "fuel": fact("GASOLINE", f"s{yy}"),
                "engine_description": fact(
                    "2.4L GDI inline-4" if displacement == "2.4" else "2.0L turbo GDI inline-4",
                    f"s{yy}",
                ),
                "engine_displacement": fact(float(displacement), f"s{yy}", "L"),
                "cylinders": fact(4, f"s{yy}"),
                "injection": fact("GDI", f"s{yy}"),
                "power_hp": fact(192 if displacement == "2.4" else 274, f"s{yy}", "hp"),
                "torque_lb_ft": fact(181 if displacement == "2.4" else 269, f"s{yy}", "lb-ft"),
                "transmission_family": fact("AT", f"s{yy}"),
                "transmission_description": fact("6-speed Sportmatic automatic", f"s{yy}"),
                "gears": fact(6, f"s{yy}"),
                "trim": fact(listed, f"p{yy}"),
                "wheelbase_in": fact(110.0, f"s{yy}", "in"),
                "fuel_tank_us_gal": fact(18.5, f"s{yy}", "US gal"),
            }
            groups.append(
                {
                    "id": f"{year}-{trim.lower().replace(' ', '-')}-{displacement}",
                    "year_from": year,
                    "year_to": year,
                    "configuration": f"{listed} · {displacement}L · 6-speed Sportmatic automatic",
                    "allowed_drives": ["FWD"],
                    "factory_combinations": [{"drivetrain": "FWD"}],
                    "epa_drive_match": {
                        "model": ["Optima"],
                        "displ": [displacement],
                        "trany": [transmission],
                    },
                    "locator": f"Kia US MY{year} pricing line {listed}: {pricing_label}; Features Mechanical {trim} column; EPA annual exact tuple FWD",
                    "facts": facts,
                }
            )
        for prefix, label in (
            ("s", "technical specifications"),
            ("f", "Mechanical trim matrix"),
            ("p", "exact MSRP trim-engine-gear line, price not imported"),
            ("o", "US annual model overview"),
        ):
            key = f"{prefix}{yy}"
            docs[key] = {
                "url": URLS[key],
                "source_id": "factory-kia-us",
                "publisher": "Kia America manufacturer US model material",
                "market": "US",
                "year_from": year,
                "year_to": year,
                "locator": f"US Optima MY{year} {label}",
                "format": "html",
            }
    manifest = {
        "version": "basic-catalog-ai-source-1",
        "batch_id": "us-base-catalog-07-kia-optima-corrected",
        "selection_status": "OWNER_MASTER_LIST_REVIEWED_SOURCE_TUPLES",
        "epa_document_id": EPA_DOC,
        "documents": docs,
        "families": [
            {
                "id": "kia-optima-tfqf-us-2014-2015-07",
                "make": "Kia",
                "model": "Optima",
                "generation": "TF/QF",
                "generation_code": "TF/QF",
                "market": "US",
                "year_from": 2014,
                "year_to": 2015,
                "local_relevance_tier": 1,
                "local_generation_year_priority": 1,
                "source_availability_rank": 1,
                "annual_documents": {
                    "2014": ["s14", "f14", "p14", "o14"],
                    "2015": ["s15", "f15", "p15", "o15"],
                },
                "generation_documents": [],
                "scope_note": "US TF/QF sedan MY2014/15, only Kia pricing and Mechanical matrix trim/engine/gear lines; annual EPA exact tuple confirms FWD. No hybrid inference.",
                "exclude": ["Hybrid, other markets, other MY, and unlisted trim/gear pairs"],
                "facts": {},
                "groups": groups,
            }
        ],
    }
    base_catalog_batch(manifest=manifest)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "factory_pricing_lines_matched": len(groups),
        "epa_exact_drive_pairs": len(groups),
        "candidate_annual_configurations": len(groups),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (OUT / "kia-optima-source-review.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
