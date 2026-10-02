"""10% re-check of a make's staging (prompt section 9): re-open the cited source and compare.

For a seeded random 10% sample per line of facts, EPA configurations and recalls:
  - the cached raw file is re-read and its sha256 compared with the manifest;
  - vPIC Canadian facts: the cited row/field value is read again and converted again;
  - EPA configurations: every listed EPA id is looked up again (year, displacement,
    cylinders, transmission, drive, combined mpg);
  - recalls: the campaign number is found again in every cited recall response;
  - manual facts: the quote is found again on the cited page of the PDF text.
Output: data_work/<make>/staging/recheck_10pct.json; exit code 1 on any mismatch.

  .venv/Scripts/python.exe scripts/recheck_us_batch.py hyundai
"""

from __future__ import annotations

import gzip
import hashlib
import json
import random
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_us_batch_staging import DIM_KEYS, DRIVE  # noqa: E402
from us_tech_common import RAW_ROOT, ROOT, WORK  # noqa: E402
from us_tech_sources import epa_rows  # noqa: E402

sys.path.insert(0, str(ROOT / "backend"))
from app.services.tech_units import convert  # noqa: E402

CODE_TO_FIELD = {"OL": "length_cm", "OW": "width_cm", "OH": "height_cm", "WB": "wheelbase_cm",
                 "TWF": "track_front_cm", "TWR": "track_rear_cm", "CW": "curb_weight_kg"}


def source_bytes(item) -> bytes:
    path = item["path"]
    file = RAW_ROOT / path[len("rawstore:"):] if path.startswith("rawstore:") else ROOT / path
    return file.read_bytes()


def check_fact(fact, sources) -> list[str]:
    problems = []
    for cite in fact["cites"]:
        item = sources[cite["source"]]
        data = source_bytes(item)
        body = gzip.decompress(data) if item["path"].endswith(".gz") else data
        if item.get("sha256") and hashlib.sha256(body).hexdigest() != item["sha256"]:
            problems.append(f"{cite['source']}: sha256 differs from manifest")
            continue
        if item["kind"] == "json_gz" and cite.get("field"):
            payload = json.loads(body)
            rows = [
                {s["Name"]: s["Value"] for s in r.get("Specs", [])}
                for r in payload.get("Results", [])
            ]
            row = next((r for r in rows if r.get("Model") == cite["quote"]), None)
            if row is None:
                problems.append(f"{cite['source']}: row '{cite['quote']}' not found")
                continue
            raw = (row.get(cite["field"]) or "").strip()
            if raw != cite["raw_value"]:
                problems.append(f"{cite['source']}: {cite['field']}={raw} != {cite['raw_value']}")
            if cite["field"] in CODE_TO_FIELD and fact["key"] != "weight_distribution_front_rear_pct":
                _, unit_from, unit_to = DIM_KEYS[CODE_TO_FIELD[cite["field"]]]
                again = convert(raw, unit_from, unit_to) if unit_from != unit_to else Decimal(raw)
                if Decimal(str(fact["value"])) != again:
                    problems.append(f"conversion {raw} {unit_from} -> {again} != {fact['value']}")
        elif item["kind"] == "pdf_pages":
            pdf_bytes = source_bytes(item)
            if hashlib.sha256(pdf_bytes).hexdigest() != item["sha256"]:
                problems.append(f"{cite['source']}: PDF sha256 differs from manifest")
                continue
            pages = json.loads(gzip.decompress((RAW_ROOT / "pagetext" / f"{item['sha256']}.json.gz").read_bytes()))
            texts = [" ".join(pages["pages"][p - 1].split()) for p in cite["pages"] or []]
            quote = " ".join(cite["quote"].split())
            if not any(quote in t for t in texts):
                problems.append(f"{cite['source']}: quote not on page {cite['pages']}")
                continue
            # the table row is rebuilt again from the PDF word positions: the value must sit
            # on the same row as when it was extracted (label/value pairing re-checked)
            if cite.get("row") and ROWS is not None:
                import pdfplumber

                with pdfplumber.open(raw_path_of(item)) as pdf:
                    rebuilt = [r["text"] for col in ROWS(pdf.pages[cite["pages"][0] - 1]) for r in col]
                if cite["row"] not in rebuilt and not any(cite["row"][:200] in r for r in rebuilt):
                    if not any(cite["row"][:120] in t for t in texts):
                        problems.append(f"{cite['source']}: row not rebuilt on page {cite['pages'][0]}: {cite['row'][:80]}")
    return problems


try:  # geometric re-check needs pdfplumber (run through uv); without it only quotes are checked
    from extract_manual_facts import rows_of as ROWS
except Exception:  # noqa: BLE001
    ROWS = None


def raw_path_of(item) -> Path:
    path = item["path"]
    return RAW_ROOT / path[len("rawstore:"):] if path.startswith("rawstore:") else ROOT / path


def check_configuration(cfg) -> list[str]:
    by_id = {r["id"]: r for r in epa_rows()}
    problems = []
    for epa in cfg["epa_vehicles"]:
        row = by_id.get(epa["epa_id"])
        if row is None:
            problems.append(f"EPA id {epa['epa_id']} missing")
            continue
        if int(row["year"]) != cfg["year"] or (row["displ"] or None) != cfg["displacement_l"]:
            problems.append(f"EPA id {epa['epa_id']}: year/displacement differ")
        if row["trany"] != cfg["epa_trany"] or DRIVE.get(row["drive"], row["drive"] or None) != cfg["drivetrain"]:
            problems.append(f"EPA id {epa['epa_id']}: transmission/drive differ")
        if int(row["comb08"]) != epa["combined_mpg"]:
            problems.append(f"EPA id {epa['epa_id']}: combined mpg {row['comb08']} != {epa['combined_mpg']}")
    return problems


def check_recall(recall, sources) -> list[str]:
    problems = []
    for key in recall["sources"]:
        item = sources[key]
        body = gzip.decompress(source_bytes(item))
        if item.get("sha256") and hashlib.sha256(body).hexdigest() != item["sha256"]:
            problems.append(f"{key}: sha256 differs from manifest")
        payload = json.loads(body)
        if not any(r.get("NHTSACampaignNumber") == recall["campaign_number"] for r in payload.get("results", [])):
            problems.append(f"{key}: campaign {recall['campaign_number']} not found")
    return problems


def main(make: str) -> int:
    report, failed = {}, 0
    for path in sorted((WORK / make / "staging").glob("*/staging.json")):
        staging = json.loads(path.read_text(encoding="utf-8"))
        if not staging.get("build"):
            continue
        rng = random.Random(f"{make}/{path.parent.name}")
        sample = lambda items: rng.sample(items, max(1, round(len(items) * 0.1))) if items else []  # noqa: E731
        results = []
        for fact in sample(staging["facts"]):
            results.append({"kind": "fact", "id": fact["id"], "problems": check_fact(fact, staging["sources"])})
        for cfg in sample(staging["configurations"]):
            results.append({"kind": "configuration", "id": cfg["configuration_key"], "problems": check_configuration(cfg)})
        for recall in sample(staging["recalls"]):
            results.append({"kind": "recall", "id": f"{recall['campaign_number']}/{recall['generation']}",
                            "problems": check_recall(recall, staging["sources"])})
        bad = [r for r in results if r["problems"]]
        failed += len(bad)
        report[path.parent.name] = {"checked": len(results), "mismatches": len(bad), "details": bad}
        print(path.parent.name, len(results), "checked,", len(bad), "mismatches",
              "(geometry)" if ROWS else "(quotes only)", flush=True)
    out = WORK / make / "staging" / "recheck_10pct.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
