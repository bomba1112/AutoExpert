"""Audit cached annual manufacturer documents once per document, without network I/O.

This deliberately does not change commercial rights or publish claims. The
machine checks are evidence for a document-group review, not a licence grant.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import logging
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from bs4 import BeautifulSoup  # noqa: E402
from pypdf import PdfReader  # noqa: E402

logging.getLogger("pypdf").setLevel(logging.CRITICAL)

REVIEW = (
    ROOT
    / "deliverables/VerifiedData/commercial-manufacturer-drivetrain-01"
    / "factory-agent-review-remaining.jsonl"
)
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-02/document-audit.json"
BRAND_TERMS = {
    "Mercedes-Benz": ("mercedes", "mbusa"),
    "BMW": ("bmw",),
    "Audi": ("audi",),
    "Volkswagen": ("volkswagen", "vw.com"),
    "Hyundai": ("hyundai",),
    "Kia": ("kia",),
    "Toyota": ("toyota",),
    "Nissan": ("nissan",),
    "Honda": ("honda",),
    "Land Rover": ("land rover", "landrover"),
    "Chevrolet": ("chevrolet",),
    "Lexus": ("lexus",),
    "Infiniti": ("infiniti",),
    "Jeep": ("jeep",),
    "Mitsubishi": ("mitsubishi",),
    "Cadillac": ("cadillac",),
    "Tesla": ("tesla",),
}
OFFICIAL_TERMS = {
    "Mercedes-Benz": ("mbusa.com", "mbusa", "mercedes-benz.com", "mercedes-benz usa"),
    "BMW": ("bmwusa.com", "bmw.com", "bmw of north america"),
    "Audi": ("audiusa.com", "audi of america", "audi.com"),
    "Volkswagen": ("vw.com", "volkswagen of america", "volkswagen.com"),
    "Hyundai": ("hyundaiusa.com", "hyundai motor america"),
    "Kia": ("kia.com", "kia motors america", "kia america"),
    "Toyota": ("toyota.com", "toyota motor sales"),
    "Nissan": ("nissanusa.com", "nissan north america"),
    "Honda": ("honda.com", "american honda"),
    "Land Rover": ("landroverusa.com", "jaguar land rover north america"),
    "Chevrolet": ("chevrolet.com", "general motors"),
    "Lexus": ("lexus.com", "toyota motor sales"),
    "Infiniti": ("infinitiusa.com", "nissan north america"),
    "Jeep": ("jeep.com", "fca us llc", "chrysler group llc"),
    "Mitsubishi": ("mitsubishicars.com", "mitsubishi motors north america"),
    "Cadillac": ("cadillac.com", "general motors"),
    "Tesla": ("tesla.com", "tesla motors"),
}


def clean(text: str) -> str:
    return " ".join(text.casefold().replace("\x00", " ").split())


def model_present(text: str, model: str) -> bool:
    word = clean(model).replace("-class", " class")
    options = {word, word.replace(" ", ""), word.replace(" series", "series")}
    if model.endswith("-Class"):
        code = model.split("-")[0].casefold()
        options.add(code + "-class")
        if re.search(rf"\b{re.escape(code)}[ -]?\d{{3}}\b", text):
            return True
    if re.fullmatch(r"[A-Za-z]\d", model) and re.search(
        rf"\b{re.escape(model[0].casefold())}\s?{model[1]}\b", text
    ):
        return True
    return any(term in text or term in text.replace(" ", "") for term in options)


def audit_document(path: Path, meta: dict) -> dict:
    result = {k: meta[k] for k in ("sha256", "url", "make", "model", "model_year")}
    result["row_count"] = meta["row_count"]
    result["host"] = urlparse(meta["url"]).hostname
    result["cache_exists"] = path.is_file()
    if not path.is_file():
        result["reason"] = "CACHE_MISSING"
        return result
    data = path.read_bytes()
    result["sha256_matches"] = hashlib.sha256(data).hexdigest() == meta["sha256"]
    if not result["sha256_matches"]:
        result["reason"] = "HASH_MISMATCH"
        return result
    try:
        if data.startswith(b"%PDF"):
            with contextlib.redirect_stderr(io.StringIO()):
                reader = PdfReader(io.BytesIO(data), strict=False)
                parts = [(page.extract_text() or "") for page in reader.pages]
            result["page_count"] = len(parts)
            text = clean(" ".join(parts))
            meta_text = clean(str(reader.metadata or ""))
            result["kind"] = "PDF"
        else:
            text = clean(
                BeautifulSoup(data.decode("utf-8", "replace"), "html.parser").get_text(
                    " ", strip=True
                )
            )
            meta_text = ""
            result["page_count"] = None
            result["kind"] = "HTML"
    except Exception as exc:
        result["reason"] = "EXTRACTION_FAILED:" + type(exc).__name__
        return result
    result["extracted_chars"] = len(text)
    result["brand_in_document"] = any(x in text for x in BRAND_TERMS.get(meta["make"], ()))
    metadata_names_model = bool(
        meta["model"].endswith("-Class")
        and re.search(rf"\b{re.escape(meta['model'].split('-')[0].casefold())}\b", meta_text)
        and any(term in meta_text for term in BRAND_TERMS.get(meta["make"], ()))
    )
    result["model_in_document"] = model_present(text, meta["model"]) or metadata_names_model
    result["year_in_document"] = (
        str(meta["model_year"]) in text or str(meta["model_year"]) in meta_text
    )
    brand = meta["make"].casefold()
    copyright_mark = bool(re.search(r"(?:©|copyright)\s*(?:\d{4}\s*)?" + re.escape(brand), text))
    result["manufacturer_mark_in_document"] = bool(
        any(x in text for x in OFFICIAL_TERMS.get(meta["make"], ()))
        or any(x in meta_text for x in BRAND_TERMS.get(meta["make"], ()))
        or copyright_mark
    )
    result["us_mark_in_document"] = any(
        x in text for x in ("united states", "u.s.", "usa", "america")
    )
    # Preserve only boolean checks; never copy brochure prose or tables.
    pdf_pass = bool(
        result["kind"] == "PDF"
        and result["page_count"] >= 3
        and result["extracted_chars"] >= 1000
        and result["brand_in_document"]
        and result["model_in_document"]
        and result["year_in_document"]
        and result["manufacturer_mark_in_document"]
    )
    result["manufacturer_issued_release"] = bool(
        result["kind"] == "HTML"
        and result["host"] == "www.prnewswire.com"
        and meta["make"] == "Hyundai"
        and "news provided by hyundai motor america" in text
        and "source hyundai motor america" in text
        and "model engine transmission drivetrain" in text
    )
    result["machine_authenticity_pass"] = bool(
        pdf_pass
        or (
            result["manufacturer_issued_release"]
            and result["brand_in_document"]
            and result["model_in_document"]
            and result["year_in_document"]
            and result["manufacturer_mark_in_document"]
        )
    )
    return result


def run(db_path: Path, out: Path, *, refresh_failed: bool = False) -> dict:
    review = [json.loads(x) for x in REVIEW.read_text(encoding="utf-8").splitlines() if x]
    keys = [row["catalog_key"] for row in review]
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    variants = {}
    keyset = set(keys)
    for key, specs in db.execute(
        "SELECT catalog_key,specifications FROM vehicle_variants "
        "WHERE published_revision_id IS NOT NULL AND is_demo=0"
    ):
        if key in keyset:
            variants[key] = json.loads(specs)["catalog"]
    groups = defaultdict(list)
    for row in review:
        key = row["catalog_key"]
        catalog = variants.get(key)
        if not catalog:
            continue
        refs = [
            (catalog.get("facts", {}).get(name) or {}).get("documentary_source") or {}
            for name in (
                "powertrain",
                "fuel",
                "engine_displacement",
                "engine_description",
                "transmission_description",
                "drivetrain",
            )
        ]
        if not all(ref.get("registry_id") == catalog.get("source_registry_id") for ref in refs):
            continue
        if len({(ref.get("sha256"), ref.get("url")) for ref in refs}) != 1:
            continue
        ref = refs[0]
        if not ref.get("sha256") or not ref.get("url"):
            continue
        group = (
            ref["sha256"],
            ref["url"],
            catalog["make"],
            catalog["model"],
            catalog["model_year"],
        )
        groups[group].append(key)
    previous = {}
    if refresh_failed and out.is_file():
        prior = json.loads(out.read_text(encoding="utf-8"))
        previous = {
            (d["sha256"], d["url"], d["make"], d["model"], d["model_year"]): d
            for d in prior["documents"]
            if d.get("machine_authenticity_pass")
        }
    audited = []
    for (sha, url, make, model, year), group_keys in sorted(groups.items()):
        meta = dict(
            sha256=sha, url=url, make=make, model=model, model_year=year, row_count=len(group_keys)
        )
        group_id = (sha, url, make, model, year)
        cached = previous.get(group_id)
        path = ROOT / ".localdata" / "raw" / sha
        if (
            cached
            and sorted(cached.get("catalog_keys", [])) == sorted(group_keys)
            and path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() == sha
        ):
            audit = cached
        else:
            audit = audit_document(path, meta)
        audit["catalog_keys"] = sorted(group_keys)
        audited.append(audit)
    report = {
        "document_groups": len(audited),
        "rows_audited": sum(x["row_count"] for x in audited),
        "machine_pass_rows": sum(
            x["row_count"] for x in audited if x.get("machine_authenticity_pass")
        ),
        "machine_fail_rows": sum(
            x["row_count"] for x in audited if not x.get("machine_authenticity_pass")
        ),
        "by_host": dict(Counter(x["host"] for x in audited)),
        "documents": audited,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        k: report[k]
        for k in (
            "document_groups",
            "rows_audited",
            "machine_pass_rows",
            "machine_fail_rows",
            "by_host",
        )
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--refresh-failed", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.db, args.out, refresh_failed=args.refresh_failed),
            ensure_ascii=False,
            indent=2,
        )
    )
