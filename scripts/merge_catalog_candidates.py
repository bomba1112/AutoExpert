"""Single-writer adoption of reviewed per-agent manifests and hash-checked receipts."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from catalog_writer_lock import catalog_writer_lock

ROOT = Path(__file__).resolve().parents[1]


def walk(value):
    if isinstance(value, dict):
        if (
            value.get("url")
            and value.get("sha256")
            and value.get("http_status") == 200
            and not value.get("error")
        ):
            yield value
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--batch", required=True)
    p.add_argument("--manifest", action="append", required=True)
    p.add_argument("--receipt", action="append", default=[])
    a = p.parse_args()
    target = ROOT / f"data/manifests/{a.batch}.json"
    if (ROOT / f"deliverables/VerifiedData/{a.batch}/prepared.json").exists():
        raise ValueError("PREPARED_BATCH_IS_IMMUTABLE")
    merged = dict(
        version="basic-catalog-ai-source-1",
        batch_id=a.batch,
        selection_status="OWNER_MASTER_LIST_REVIEWED_SOURCE_TUPLES",
        epa_document_id=None,
        documents={},
        families=[],
    )
    for path in a.manifest:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
        if value.get("provenance") == "AI_DRAFT":
            raise ValueError("AI_IS_NOT_SOURCE")
        if merged["epa_document_id"] not in (None, value["epa_document_id"]):
            raise ValueError("EPA_SOURCE_MISMATCH")
        merged["epa_document_id"] = value["epa_document_id"]
        if set(merged["documents"]) & set(value["documents"]):
            raise ValueError("DOCUMENT_KEY_COLLISION")
        merged["documents"].update(value["documents"])
        merged["families"].extend(value["families"])
    ids = [f["id"] for f in merged["families"]]
    if len(ids) != len(set(ids)):
        raise ValueError("FAMILY_COLLISION")
    ledgerpath = ROOT / "deliverables/VerifiedData/base-catalog-acquisition.json"
    with catalog_writer_lock():
        ledger = json.loads(ledgerpath.read_text(encoding="utf-8"))
        receipts = {r["url"]: r for r in walk(ledger)}
        for path in a.receipt:
            for r in walk(json.loads((ROOT / path).read_text(encoding="utf-8"))):
                receipts[r["url"]] = r
        adopted = []
        cache = ROOT / ".localdata/verified-source-documents"
        for spec in merged["documents"].values():
            r = receipts.get(spec["url"])
            if not r:
                raise ValueError("MISSING_RECEIPT:" + spec["url"])
            dst = cache / r["sha256"]
            path = dst if dst.exists() else ROOT / r["path"]
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != r["sha256"]:
                raise ValueError("HASH_MISMATCH")
            if spec.get("format") == "pdf" and not raw.startswith(b"%PDF-"):
                raise ValueError("PDF_EXPECTED")
            if not dst.exists():
                dst.write_bytes(raw)
            clean = dict(
                url=r["url"],
                sha256=r["sha256"],
                http_status=200,
                media_type="application/pdf" if raw.startswith(b"%PDF-") else "text/html",
                byte_size=len(raw),
                observed_at=r.get("observed_at") or "2026-09-26",
                latency_ms=r.get("latency_ms", round(r.get("seconds", 0) * 1000)),
                cost_usd="0.00",
            )
            if not any(x.get("url") == r["url"] and x.get("sha256") == r["sha256"] for x in ledger):
                ledger.append(clean)
            adopted.append(clean)
        ledgerpath.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
        target.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        out = ROOT / f"deliverables/VerifiedData/{a.batch}"
        out.mkdir(exist_ok=True)
        (out / "source-adoption.json").write_text(
            json.dumps(
                dict(at=datetime.now(UTC).isoformat(), manifests=a.manifest, documents=adopted),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    print(json.dumps(dict(families=len(ids), documents=len(adopted), manifest=str(target))))


if __name__ == "__main__":
    main()
