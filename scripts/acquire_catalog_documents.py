"""Fetch an explicit, reviewed list of public factory documents with bounded curl requests.

Separate receipts avoid overwriting the older acquisition ledger. No crawl, credentials,
headers, cookies or redirects; downloads remain private, never vehicle image assets.
"""

import argparse
import hashlib
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def acquire(manifest):
    cache = ROOT / ".localdata/verified-source-documents"
    cache.mkdir(parents=True, exist_ok=True)
    receipt = ROOT / "deliverables/VerifiedData/base-catalog-acquisition.json"
    ledger = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else []
    previous = ROOT / "deliverables/VerifiedData/acquisition-ledger.json"
    old = json.loads(previous.read_text(encoding="utf-8")) if previous.exists() else []
    if len(manifest["documents"]) > 60:
        raise ValueError("DOCUMENT_BUDGET")
    for doc in manifest["documents"]:
        url = doc["url"]
        p = urlparse(url)
        if (
            p.scheme != "https"
            or p.hostname not in manifest["allowed_hosts"]
            or p.username
            or p.password
            or p.query
        ):
            raise ValueError("PUBLIC_DOCUMENT_URL_REQUIRED")
        if doc["cost"] != "FREE" or doc["storage"] != "PUBLIC_FACTS":
            raise ValueError("PUBLIC_FREE_DOCUMENT_REQUIRED")
        prior = next(
            (
                r
                for r in reversed(old + ledger)
                if r["url"] == url and r.get("sha256") and not r.get("error")
            ),
            None,
        )
        if prior and (cache / prior["sha256"]).exists():
            continue
        tmp = cache / (hashlib.sha256(url.encode()).hexdigest() + ".download")
        started = time.monotonic()
        run = subprocess.run(
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
        record = {
            "url": url,
            "observed_at": datetime.now(UTC).isoformat(),
            "http_status": int(run.stdout or 0),
            "cost_usd": "0.00",
            "latency_ms": round((time.monotonic() - started) * 1000),
        }
        content = tmp.read_bytes() if tmp.exists() else b""
        if run.returncode:
            record["error"] = "CURL_EXIT_" + str(run.returncode)
        elif record["http_status"] == 200:
            if doc.get("format") == "pdf" and not content.startswith(b"%PDF-"):
                record["error"] = "PDF_CONTENT_MISMATCH"
            else:
                digest = hashlib.sha256(content).hexdigest()
                (cache / digest).write_bytes(content)
                record.update(
                    sha256=digest,
                    byte_size=len(content),
                    media_type="application/pdf" if content.startswith(b"%PDF-") else "text/html",
                )
        tmp.unlink(missing_ok=True)
        ledger.append(record)
        receipt.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        print(json.dumps(record), flush=True)
    return ledger


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    args = parser.parse_args()
    acquire(json.loads(Path(args.manifest).read_text(encoding="utf-8")))
