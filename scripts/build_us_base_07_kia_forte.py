"""Review official Kia US Forte 2021/22 matrices into the existing batch format."""

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
MANIFEST = ROOT / "data/manifests/us-base-catalog-07-root-kia-forte.json"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"

URLS = {
    "s21": "https://www.kiamedia.com/us/es/models/forte/2021/specifications",
    "f21": "https://www.kiamedia.com/us/en/models/forte/2021/features",
    "p21": "https://www.kiamedia.com/us/en/models/forte/2021/pricing",
    "o21": "https://www.kiamedia.com/us/es/media/documenttext/16504/2021-forte-overview",
    "s22": "https://www.kiamedia.com/us/en/media/specifications/20027/2022-kia-forte-specifications",
    "f22": "https://www.kiamedia.com/us/en/models/forte/2022/features",
    "p22": "https://www.kiamedia.com/us/en/models/forte/2022/pricing",
    "o22": "https://www.kiamedia.com/us/en/models/forte/2022",
}

# Every row below is a factory pricing-table line, not a product of engine/gearbox lists.
LINES = {
    2021: [
        ("Forte FE", "2.0L I4 - 6 M/T", "FE", "2.0", "MT", "Forte", "Manual 6-spd"),
        ("Forte FE", "2.0L I4 - IVT", "FE", "2.0", "IVT", "Forte FE", "Automatic (variable gear ratios)"),
        ("Forte LXS", "2.0L I4 - IVT", "LXS", "2.0", "IVT", "Forte", "Automatic (variable gear ratios)"),
        ("Forte GT-Line", "2.0L I4 - IVT", "GT Line", "2.0", "IVT", "Forte", "Automatic (variable gear ratios)"),
        ("Forte EX", "2.0L I4 - IVT", "EX", "2.0", "IVT", "Forte", "Automatic (variable gear ratios)"),
        ("Forte GT", "1.6L Turbo - DCT", "GT", "1.6", "DCT", "Forte", "Automatic (AM-S7)"),
        ("Forte GT", "1.6L Turbo - 6 M/T", "GT", "1.6", "MT", "Forte", "Manual 6-spd"),
    ],
    2022: [
        ("Forte FE", "2.0G - IVT", "FE", "2.0", "IVT", "Forte FE", "Automatic (variable gear ratios)"),
        ("Forte LXS", "2.0G - IVT", "LXS", "2.0", "IVT", "Forte", "Automatic (variable gear ratios)"),
        ("Forte GT Line", "2.0G - IVT", "GT Line", "2.0", "IVT", "Forte", "Automatic (variable gear ratios)"),
        ("Forte GT", "1.6T - DCT", "GT", "1.6", "DCT", "Forte", "Automatic (AM-S7)"),
        ("Forte GT MT", "1.6T - 6 M/T", "GT MT", "1.6", "MT", "Forte", "Manual 6-spd"),
    ],
}


def fact(value, document_key, unit=None):
    return {"value": value, "document_key": document_key, **({"unit": unit} if unit else {})}


def pricing_lines(raw):
    soup = BeautifulSoup(raw, "html.parser")
    return [
        tuple(c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])[:2])
        for tr in soup.find_all("tr")
        if tr.get_text(" ", strip=True).startswith("Forte ")
    ]


def selected_feature(table, label, trim):
    row = next(r for r in table.rows if r.group == "Mechanical" and r.label == label)
    return row.values[table.trims.index(trim)]


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
    features = {year: parse_factory_table(raw[f"f{str(year)[-2:]}"]) for year in LINES}
    for year, lines in LINES.items():
        actual = pricing_lines(raw[f"p{str(year)[-2:]}"])
        assert Counter(actual) == Counter((line[0], line[1]) for line in lines)
        table = features[year]
        for _, _, trim, displacement, transmission, _, _ in lines:
            assert trim in table.trims
            engine_label = (
                "2.0L 4-cylinder multi-port injection (MPI) engine"
                if displacement == "2.0"
                else "1.6L 4-cylinder turbo gasoline-direct injection (GDI) engine"
            )
            gear_label = {
                "MT": "6-Speed Manual Transmission",
                "DCT": "7-speed Dual Clutch Transmission",
                "IVT": "Intelligent Variable Transmission (i-IVT)"
                if year == 2021
                else "Intelligent Variable Transmission (IVT)",
            }[transmission]
            assert selected_feature(table, engine_label, trim) == "S"
            assert selected_feature(table, gear_label, trim) in {"S", "O"}
    with SessionLocal() as db:
        epa_doc = db.get(RawDocument, EPA_DOC)
        epa = list(
            csv.DictReader(document_text(private_path(epa_doc.storage_key).read_bytes()).splitlines())
        )
    for year, lines in LINES.items():
        for _, _, _, displacement, _, model, trany in lines:
            found = [
                row
                for row in epa
                if row["year"] == str(year)
                and row["make"] == "Kia"
                and row["model"] == model
                and row["displ"] == displacement
                and row["trany"] == trany
            ]
            assert len(found) == 1 and found[0]["drive"] == "Front-Wheel Drive"

    docs = {}
    for key, url in URLS.items():
        year = 2021 if key.endswith("21") else 2022
        docs[key] = {
            "url": url,
            "source_id": "factory-kia-us",
            "publisher": "Kia America manufacturer US specifications and model material",
            "market": "US",
            "year_from": year,
            "year_to": year,
            "locator": {
                "s": "US Forte manufacturer specifications, trim columns and technical table",
                "f": "US Forte features matrix, Mechanical trim columns",
                "p": "US Forte MSRP matrix, exact trim, engine and transmission line; prices not imported",
                "o": "US Forte annual overview, body, generation continuity and engine scope",
            }[key[0]],
            "format": "html",
        }
    groups = []
    for year, lines in LINES.items():
        yy = str(year)[-2:]
        for listed, label, trim, displacement, transmission, epa_model, epa_trany in lines:
            engine = "2.0L MPI Atkinson-cycle inline-4" if displacement == "2.0" else "1.6L turbo GDI inline-4"
            family, gear = {"IVT": ("CVT", "Intelligent Variable Transmission (IVT)"),
                            "MT": ("MANUAL", "6-speed manual"),
                            "DCT": ("DCT", "7-speed dual-clutch")}[transmission]
            engine_source = f"s{yy}" if year == 2021 else f"o{yy}"
            facts = {
                "body": fact("SEDAN", f"o{yy}"),
                "powertrain": fact("ICE", f"o{yy}"),
                "fuel": fact("GASOLINE", f"s{yy}" if year == 2021 else f"f{yy}"),
                "engine_description": fact(engine, engine_source),
                "engine_displacement": fact(float(displacement), engine_source, "L"),
                "cylinders": fact(4, engine_source),
                "injection": fact("MPI" if displacement == "2.0" else "GDI", f"f{yy}"),
                "power_hp": fact(147 if displacement == "2.0" else 201, engine_source, "hp"),
                "torque_lb_ft": fact(132 if displacement == "2.0" else 195, engine_source, "lb-ft"),
                "transmission_family": fact(family, f"f{yy}"),
                "transmission_description": fact(gear, f"f{yy}"),
                "trim": fact(listed, f"p{yy}"),
                "wheelbase_in": fact(106.3, f"s{yy}", "in"),
            }
            if transmission != "IVT":
                facts["gears"] = fact(6 if transmission == "MT" else 7, f"f{yy}")
            if year == 2021:
                facts.update(
                    octane_aki=fact(87, "s21", "AKI"),
                    fuel_tank_us_gal=fact(14.0, "s21", "US gal"),
                    engine_oil_capacity_l=fact(4.0 if displacement == "2.0" else 4.5, "s21", "L"),
                    engine_oil_capacity_note=fact("With oil filter; factory table capacity", "s21"),
                )
            else:
                facts["seats"] = fact(5, "o22")
            groups.append(
                {
                    "id": f"{year}-{trim.lower().replace(' ', '-')}-{displacement}-{transmission.lower()}",
                    "year_from": year,
                    "year_to": year,
                    "configuration": f"{listed} · {displacement}L · {gear}",
                    "allowed_drives": ["FWD"],
                    "factory_combinations": [{"drivetrain": "FWD"}],
                    "epa_drive_match": {"model": [epa_model], "displ": [displacement], "trany": [epa_trany]},
                    "locator": f"Kia US MY{year} pricing line {listed}: {label}; Features Mechanical columns "
                    f"{trim} engine+gear; EPA exact tuple confirms FWD; no adjacent MY extrapolation",
                    "facts": facts,
                }
            )
    manifest = {
        "version": "basic-catalog-ai-source-1",
        "batch_id": "us-base-catalog-07-kia-forte",
        "selection_status": "OWNER_MASTER_LIST_REVIEWED_SOURCE_TUPLES",
        "epa_document_id": EPA_DOC,
        "documents": docs,
        "families": [
            {
                "id": "kia-forte-bd-us-2021-2022-07",
                "make": "Kia",
                "model": "Forte",
                "generation": "BD / BDm sedan",
                "generation_code": "BD",
                "market": "US",
                "year_from": 2021,
                "year_to": 2022,
                "facelift_from": 2022,
                "local_relevance_tier": 1,
                "local_generation_year_priority": 1,
                "source_availability_rank": 1,
                "annual_documents": {"2021": ["s21", "f21", "p21", "o21"], "2022": ["s22", "f22", "p22", "o22"]},
                "generation_documents": [],
                "scope_note": "US Forte 2021/22 sedan, only factory pricing and Mechanical matrix listed trim/engine/gear pairs; EPA exact matching tuple confirms FWD.",
                "exclude": ["Other MY, body styles, market versions and unavailable trim/gear pairings"],
                "facts": {},
                "groups": groups,
            }
        ],
    }
    base_catalog_batch(manifest=manifest)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "source_documents_reused_or_acquired": len(docs),
        "factory_pricing_lines_matched": len(groups),
        "epa_exact_drive_pairs": len(groups),
        "candidate_annual_configurations": len(groups),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (OUT / "kia-forte-source-review.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
