"""Find a bounded reviewed source queue from actual manufacturer-brochure index links."""

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".localdata/bulk08/indices"


def fetch_index(url, *, refresh):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "www.auto-brochures.com" or parsed.query:
        raise ValueError("INDEX_URL_NOT_ALLOWED")
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".html")
    if path.exists() and not refresh:
        return path.read_bytes(), True, None
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=CACHE, suffix=".download", delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        result = subprocess.run(
            [
                "curl.exe",
                "--silent",
                "--show-error",
                "--max-time",
                "30",
                "--max-filesize",
                "2000000",
                "--proto",
                "=https",
                "--user-agent",
                "AutoExpert-local-research/0.8",
                "--output",
                str(temporary),
                "--write-out",
                "%{http_code} %{content_type}",
                url,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        status, media_type = result.stdout.split(" ", 1)
        if result.returncode or status != "200":
            raise ValueError(
                "INDEX_FETCH_FAILED:" + status + ":CURL_EXIT_" + str(result.returncode)
            )
        if media_type.split(";", 1)[0] not in {"text/html", "application/xhtml+xml"}:
            raise ValueError("INDEX_CONTENT_TYPE")
        content = temporary.read_bytes()
        if len(content) > 2_000_000:
            raise ValueError("INDEX_TOO_LARGE")
        path.write_bytes(content)
        return content, False, int(status)
    finally:
        temporary.unlink(missing_ok=True)


def select_documents(html, index, make, model, years):
    candidates = {}
    for anchor in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        # The site puts the year/model label in the text immediately before the PDF link.
        label = " ".join(str(anchor.previous_sibling or "").split())
        match = re.fullmatch(
            rf"(20\d{{2}})\s+{re.escape(make)}\s+{re.escape(model)}(?:\s+v([12]))?\s+PDF\s+(?:Brochure|Factsheet)",
            label,
            flags=re.IGNORECASE,
        )
        if not match or int(match.group(1)) not in years:
            continue
        url = urljoin(index, anchor["href"])
        parsed = urlparse(url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname != "www.auto-brochures.com"
            or not parsed.path.startswith("/makes/")
            or not parsed.path.lower().endswith(".pdf")
            or parsed.query
            or parsed.username
            or parsed.password
        ):
            continue
        # Preserve the observed host/path, requiring TLS for the subsequent request.
        url = urlunparse(("https", parsed.netloc, quote(parsed.path, safe="/%-._~"), "", "", ""))
        year, version = int(match.group(1)), int(match.group(2) or 1)
        candidates.setdefault(year, []).append((version, url, label))
    found, missing = [], []
    for year in years:
        choices = sorted(candidates.get(year, []), reverse=True)
        if not choices:
            missing.append(year)
            continue
        version, url, label = choices[0]
        found.append(
            {
                "make": make,
                "model": model,
                "year": year,
                "version": version,
                "label": label,
                "url": url,
                "cost": "FREE",
                "storage": "PUBLIC_FACTS",
                "format": "pdf",
            }
        )
    return found, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/manifests/us-bulk-data-08-discovery.json")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    assert manifest["market"] == "US"
    assert all(min(t["years"]) >= 2000 for t in manifest["targets"])
    output = ROOT / "deliverables/VerifiedData" / manifest["batch_id"]
    output.mkdir(parents=True, exist_ok=True)
    documents, misses, receipts = [], [], []
    index_data = {}
    for target in manifest["targets"]:
        index = target["index"]
        if index not in index_data:
            html, hit, status = fetch_index(index, refresh=args.refresh)
            index_data[index] = html
            receipts.append(
                {
                    "index": index,
                    "http_status": status,
                    "cache_hit": hit,
                    "sha256": hashlib.sha256(html).hexdigest(),
                    "bytes": len(html),
                }
            )
        found, missing = select_documents(
            index_data[index], index, target["make"], target["model"], target["years"]
        )
        documents.extend(found)
        for year in missing:
            misses.append(
                {
                    "make": target["make"],
                    "model": target["model"],
                    "year": year,
                    "reason": "NO_MATCHING_LINK_IN_SOURCE_INDEX",
                }
            )
    docs = [{k: d[k] for k in ("url", "cost", "storage", "format")} for d in documents]
    acquisition = {"allowed_hosts": ["www.auto-brochures.com"], "documents": docs}
    (ROOT / "data/manifests" / (manifest["batch_id"] + "-acquisition.json")).write_text(
        json.dumps(acquisition, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    result = {
        "batch_id": manifest["batch_id"],
        "observed_at": datetime.now(UTC).isoformat(),
        "indices": receipts,
        "document_count": len(documents),
        "documents": documents,
        "unmatched": misses,
        "no_technical_claims": True,
    }
    (output / "factory-source-discovery.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "documents": len(documents),
                "unmatched": misses,
                "indices": len(receipts),
                "cache_hits": sum(r["cache_hit"] for r in receipts),
            }
        )
    )


if __name__ == "__main__":
    main()
