"""Readers for the cached batch sources (EPA, vPIC Canada, NHTSA, MfrComms) per line.

Every reader returns plain dicts and the source key/manifest row it came from, so the
staging builder can cite it. Nothing here reaches the network.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import re
import zipfile
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from us_tech_common import RAW_ROOT, ROOT, WORK
from us_tech_lines import MAKES, Line, epa_line, nhtsa_line, vpic_ca_line

EPA_ZIP = WORK / "_shared" / "raw" / "epa" / "vehicles.csv.zip"
MFR_DIR = WORK / "_shared" / "raw" / "nhtsa_mfrcomms"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


# ---- EPA ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def epa_rows() -> list[dict]:
    archive = zipfile.ZipFile(EPA_ZIP)
    with archive.open(archive.namelist()[0]) as handle:
        return list(csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8")))


def epa_for_line(line: Line) -> list[dict]:
    make = MAKES[line.make]["epa"]
    out = []
    for row in epa_rows():
        if row["make"] != make or not (2014 <= int(row["year"]) <= 2026):
            continue
        hit = epa_line(make, row["baseModel"], row["model"])
        if hit is not None and hit.key == line.key:
            out.append(row)
    return out


# ---- vPIC Canadian specifications -----------------------------------------------------
VPIC_FIELDS = {
    "OL": "length_cm",
    "OW": "width_cm",
    "OH": "height_cm",
    "WB": "wheelbase_cm",
    "CW": "curb_weight_kg",
    "TWF": "track_front_cm",
    "TWR": "track_rear_cm",
    "WD": "weight_distribution",
}


@lru_cache(maxsize=None)
def vpic_manifest() -> dict:
    rows = read_csv(WORK / "_shared" / "manifest_vpic.csv")
    return {(r["kind"], r["make"], r["year"]): r for r in rows if r["status"] == "ok"}


def vpic_ca_for_line(line: Line) -> list[dict]:
    """One dict per Canadian specification row of the line: year, model text, metric values."""
    out = []
    for year in range(2014, 2027):
        row = vpic_manifest().get(("vpic_canada_specs", line.make, str(year)))
        if not row:
            continue
        data = load_json_gz(RAW_ROOT / row["path"])
        for item in data.get("Results", []):
            specs = {s["Name"]: s["Value"] for s in item.get("Specs", [])}
            model = specs.get("Model", "")
            hit = vpic_ca_line(line.make, model)
            if hit is None or hit.key != line.key:
                continue
            record = {"year": year, "model": model, "source": f"vpic-ca-{line.make}-{year}"}
            for code, name in VPIC_FIELDS.items():
                record[name] = specs.get(code)
            record["raw_specs"] = specs
            out.append(record)
    return out


# ---- NHTSA recalls / complaints ------------------------------------------------------
@lru_cache(maxsize=None)
def nhtsa_manifest() -> list[dict]:
    return [r for r in read_csv(WORK / "_shared" / "manifest_nhtsa.csv") if r["status"] == "ok"]


def nhtsa_for_line(line: Line, kind: str) -> list[dict]:
    """[{year, model, source, row, results}] for kind 'recalls' or 'complaints'."""
    out = []
    for row in nhtsa_manifest():
        if row["kind"] != kind or row["make"] != line.make:
            continue
        hit = nhtsa_line(line.make, row["model"])
        if hit is None or hit.key != line.key:
            continue
        data = load_json_gz(RAW_ROOT / row["path"])
        out.append(
            {
                "year": int(row["year"]),
                "model": row["model"],
                "source": f"nhtsa-{kind}-{slug(row['model'])}-{row['year']}",
                "row": row,
                "results": data.get("results", []) if isinstance(data, dict) else [],
            }
        )
    return out


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


# ---- NHTSA Manufacturer Communications -------------------------------------------------
@lru_cache(maxsize=1)
def mfrcomms_all() -> list[dict]:
    """Rows for the Appendix A makes, MY2014+; cached under RAW_ROOT keyed by the zip files."""
    zips = sorted(MFR_DIR.glob("MFR_COMMS_RECEIVED_*.zip"))
    stamp = "-".join(f"{p.stat().st_size}" for p in zips)
    cache = RAW_ROOT / "cache" / f"mfrcomms_{stamp}.json.gz"
    if cache.exists():
        return load_json_gz(cache)
    makes = {m["nhtsa"] for m in MAKES.values()}
    rows = [r for r in _mfrcomms_parse(zips) if r["make"] in makes]
    cache.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(cache, "wt", encoding="utf-8") as handle:
        json.dump(rows, handle)
    return rows


def _mfrcomms_parse(zips) -> list[dict]:
    rows = []
    for path in zips:
        archive = zipfile.ZipFile(path)
        member = [i.filename for i in archive.infolist() if i.filename.endswith(".csv")][0]
        with archive.open(member) as handle:
            for row in csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8", errors="replace")):
                years = sorted(
                    {int(y) for y in re.findall(r"\d{4}", row["Model Year"]) if y != "9999"}
                )
                if not any(2014 <= y <= 2026 for y in years):
                    continue
                rows.append(
                    {
                        "id": row["TSB/Document ID"].strip(),
                        "make": row["Make"].strip().upper(),
                        "model": row["Model"].strip().upper(),
                        "years": years,
                        "summary": row["Concise Summary"].strip(),
                        "component": (row.get("Component") or row.get("Components") or "").strip(),
                        "file": path.relative_to(ROOT).as_posix(),
                    }
                )
    return rows


def mfrcomms_for_line(line: Line) -> list[dict]:
    make = MAKES[line.make]["nhtsa"]
    out = []
    for row in mfrcomms_all():
        if row["make"] != make:
            continue
        hit = nhtsa_line(line.make, row["model"])
        if hit is not None and hit.key == line.key:
            out.append(row)
    return out


def mfrcomms_columns() -> list[str]:
    path = sorted(MFR_DIR.glob("MFR_COMMS_RECEIVED_*.zip"))[0]
    archive = zipfile.ZipFile(path)
    member = [i.filename for i in archive.infolist() if i.filename.endswith(".csv")][0]
    with archive.open(member) as handle:
        return next(csv.reader(io.TextIOWrapper(handle, encoding="utf-8", errors="replace")))


def group_by(rows, key):
    out = defaultdict(list)
    for row in rows:
        out[key(row)].append(row)
    return out
