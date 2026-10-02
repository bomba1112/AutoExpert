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
        raw_file = raw_path_of(item)
        body = None
        if not raw_file.is_dir():  # mycarusermanual sections: a folder, checked through the page text store
            data = raw_file.read_bytes()
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
            pages = json.loads(gzip.decompress((RAW_ROOT / "pagetext" / f"{item['sha256']}.json.gz").read_bytes()))
            texts = [" ".join(pages["pages"][p - 1].split()) for p in cite["pages"] or []]
            quote = " ".join(cite["quote"].split())
            if not any(quote in t or norm_text(quote) in norm_text(t) for t in texts):
                problems.append(f"{cite['source']}: quote not on page {cite['pages']}")
                continue
            # PDF rows are rebuilt again from the word positions (label/value pairing re-checked);
            # a ruled capacity table is read again cell by cell; HTML pages: quote check only
            # press pages: `row` is the table label of the press parser (its own --verify checks the
            # pairing), so only the quote is re-checked here
            if (cite.get("row") and ROWS is not None and raw_file.suffix.lower() == ".pdf"
                    and item.get("source_type") != "PRESS_RELEASE"):
                import pdfplumber

                with pdfplumber.open(raw_file) as pdf:
                    page = pdf.pages[cite["pages"][0] - 1]
                    rebuilt = [r["text"] for col in ROWS(page) for r in col]
                    found = cite["row"] in rebuilt or any(cite["row"][:200] in r for r in rebuilt) \
                        or any(cite["row"][:120] in t or MNORM(cite["row"])[:120] in MNORM(t) for t in texts)
                    if not found and TABLES is not None:
                        again = [f for table in TABLES[0](page) for f in TABLES[1](cite["pages"][0], table, pages["pages"][cite["pages"][0] - 1])[0]]
                        found = any(f["row"] == cite["row"] for f in again)
                if not found:
                    problems.append(f"{cite['source']}: row not rebuilt on page {cite['pages'][0]}: {cite['row'][:80]}")
    return problems


def norm_text(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


try:  # geometric re-check needs pdfplumber (run through uv); without it only quotes are checked
    from extract_manual_facts import rows_of as ROWS
    from extract_manual_facts import norm as MNORM
    from extract_manual_facts import ruled_tables, table_facts

    TABLES = (ruled_tables, table_facts)
except Exception:  # noqa: BLE001
    ROWS = None
    TABLES = None


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
        for item in sample(staging.get("maintenance", [])):
            problems = []
            for cite in item["cites"]:
                source = staging["sources"][cite["source"]]
                body = source_bytes(source)
                if source.get("sha256") and hashlib.sha256(body).hexdigest() != source["sha256"]:
                    problems.append(f"{cite['source']}: sha256 differs from manifest")
                elif source["kind"] == "pdf_pages":
                    # schedule tables: the item text is found again on the cited page
                    pages = json.loads(gzip.decompress((RAW_ROOT / "pagetext" / f"{source['sha256']}.json.gz").read_bytes()))
                    if not any(norm_text(cite["quote"]) in norm_text(pages["pages"][p - 1]) for p in cite.get("pages") or []):
                        problems.append(f"{cite['source']}: schedule text not found on page {cite.get('pages')}")
                elif cite["quote"].split(" ", 6)[-1][:60] not in body.decode("utf-8", errors="ignore"):
                    problems.append(f"{cite['source']}: service text not found again")
            results.append({"kind": "maintenance", "id": item["id"], "problems": problems})
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
