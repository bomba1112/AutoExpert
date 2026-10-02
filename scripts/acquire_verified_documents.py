"""Bounded, explicit-URL public acquisition; no credentials, response headers or account data."""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import time
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]


def acquire(manifest):
    cache = ROOT / ".localdata/verified-source-documents"
    cache.mkdir(parents=True, exist_ok=True)
    receipt = ROOT / "deliverables/VerifiedData/acquisition-ledger.json"
    ledger = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else []
    results = []
    if len(manifest["documents"]) > 50:
        raise ValueError("DOCUMENT_BUDGET")
    with httpx.Client(
        timeout=25, follow_redirects=False, verify=ssl.create_default_context()
    ) as client:
        for doc in manifest["documents"]:
            url = doc["url"]
            if doc["cost"] != "FREE" or doc["storage"] not in {"PUBLIC_FACTS", "OPEN_LICENSE"}:
                results.append({"url": url, "status": "NEEDS_PERMISSION"})
                continue
            parsed = urlparse(url)
            if (
                parsed.scheme != "https"
                or parsed.username
                or parsed.password
                or parsed.hostname not in manifest["allowed_hosts"]
            ):
                raise ValueError("URL_NOT_AUTHORIZED")
            old = next(
                (
                    r
                    for r in reversed(ledger)
                    if r["url"] == url
                    and r.get("http_status") == 200
                    and r.get("sha256")
                    and not r.get("error")
                ),
                None,
            )
            if old and (cache / old["sha256"]).exists():
                results.append(old)
                continue
            for attempt in range(2):
                start = time.monotonic()
                record = {
                    "url": url,
                    "observed_at": datetime.now(UTC).isoformat(),
                    "attempt": attempt + 1,
                    "cost_usd": "0.00",
                }
                try:
                    with ExitStack() as stack:
                        response = stack.enter_context(client.stream("GET", url))
                        for _hop in range(2):
                            if not response.is_redirect:
                                break
                            destination = response.headers.get("location", "")
                            dest = urlparse(destination)
                            record.setdefault("redirects", []).append(
                                {
                                    "http_status": response.status_code,
                                    "host": dest.hostname,
                                    "path": dest.path,
                                }
                            )
                            if (
                                dest.scheme != "https"
                                or dest.username
                                or dest.password
                                or dest.hostname not in manifest.get("redirect_hosts", [])
                            ):
                                break
                            # Short-lived publisher-issued signed CDN URL stays in memory only.
                            response.close()
                            response = stack.enter_context(client.stream("GET", destination))
                        record["http_status"] = response.status_code
                        record["media_type"] = response.headers.get("content-type", "").split(";")[
                            0
                        ]
                        content = bytearray()
                        for chunk in response.iter_bytes():
                            if time.monotonic() - start > 90:
                                raise TimeoutError("RESPONSE_TOTAL_TIME_BUDGET")
                            content.extend(chunk)
                            if len(content) > 20_000_000:
                                raise ValueError("RESPONSE_BYTE_BUDGET")
                        if response.status_code == 200:
                            if parsed.path.lower().endswith(".pdf") and not content.startswith(
                                b"%PDF-"
                            ):
                                raise ValueError("PDF_CONTENT_MISMATCH")
                            digest = hashlib.sha256(content).hexdigest()
                            (cache / digest).write_bytes(content)
                            record.update(sha256=digest, byte_size=len(content))
                        elif response.is_redirect:
                            # Record a public destination, do not automatically traverse hosts.
                            destination = response.headers.get("location", "")
                            if "?" not in destination and "@" not in destination:
                                record["redirect"] = destination
                except Exception as exc:
                    record["error"] = type(exc).__name__
                record["latency_ms"] = round((time.monotonic() - start) * 1000)
                ledger.append(record)
                receipt.write_text(
                    json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                if record.get("http_status", 0) < 500 and record.get("http_status") or attempt == 1:
                    break
                time.sleep(1)
            results.append(record)
            print(
                json.dumps(
                    {k: record[k] for k in ("url", "http_status", "error", "sha256") if k in record}
                ),
                flush=True,
            )
            time.sleep(0.5)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args()
    acquire(json.loads(Path(args.manifest).read_text(encoding="utf-8")))
