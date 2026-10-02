"""Selective LEMON fetch with existing public HTTP gate and private HTML cache.

Only explicitly supplied URLs are fetched. No whole-manual traversal, bundles,
archives, authentication, proxies, paid services, or automatic publication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

import httpx
from app.providers.public_evidence_http import PublicAccessError, PublicEvidenceHTTP

from scripts.lemon_selective import ALLOWED_HOST, MAX_HTML_BYTES, SKIP_TERMS, parse_page

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = ROOT / ".localdata/lemon-html"
DEFAULT_OUTPUT = ROOT / "deliverables/VerifiedData/us-bulk-data-08/lemon-adapter-receipt.json"


def validate_lemon_url(url: str) -> None:
    parsed = urlsplit(url)
    path = unquote(parsed.path).casefold()
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("LEMON_URL_NOT_ALLOWED") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or port is not None
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/")
        or ".." in path
        or "\\" in path
        or "//" in path
        or any(term in path for term in SKIP_TERMS)
        or any(path.endswith(ext) for ext in (".zip", ".torrent", ".pdf", ".png", ".jpg"))
    ):
        raise ValueError("LEMON_URL_NOT_ALLOWED")


class LemonSelectiveHTTP(PublicEvidenceHTTP):
    """Reuse robots, TLS, redirects, size limit and honest UA from project client."""

    def __init__(
        self,
        *,
        explicit_urls: set[str],
        transport=None,
        min_interval_seconds: float = 2,
        max_requests: int = 12,
        max_elapsed_seconds: float = 180,
    ):
        super().__init__(transport=transport)
        self.client.timeout = httpx.Timeout(connect=10, read=30, write=10, pool=10)
        self.explicit_urls = set(explicit_urls)
        self.explicit_urls.add(f"https://{ALLOWED_HOST}/robots.txt")
        for url in self.explicit_urls:
            validate_lemon_url(url)
        self.min_interval_seconds = min_interval_seconds
        self.max_requests = max_requests
        self.max_elapsed_seconds = max_elapsed_seconds
        self.started = time.monotonic()
        self.last_request_at: float | None = None
        self.requests = 0
        self.stopped = False

    def _request(self, url):
        # Every redirect is checked here too, before the next network request.
        validate_lemon_url(url)
        if url not in self.explicit_urls:
            raise ValueError("LEMON_UNDISCOVERED_REDIRECT_OR_PAGE")
        if self.stopped or self.requests >= self.max_requests:
            raise ValueError("LEMON_CIRCUIT_OR_REQUEST_BUDGET")
        if time.monotonic() - self.started >= self.max_elapsed_seconds:
            raise ValueError("LEMON_TIME_BUDGET")
        if self.last_request_at is not None:
            wait = self.min_interval_seconds - (time.monotonic() - self.last_request_at)
            if wait > 0:
                time.sleep(wait)
        self.last_request_at = time.monotonic()
        self.requests += 1
        try:
            return super()._request(url)
        except PublicAccessError as exc:
            if exc.http_status in {401, 403, 429} or exc.reason == "ACCESS_CHALLENGE":
                self.stopped = True
            raise


def fetch_explicit_page(
    http: LemonSelectiveHTTP,
    url: str,
    *,
    cache_root: Path = DEFAULT_CACHE,
    use_cache: bool = True,
) -> tuple[bytes, dict]:
    """Return private verified bytes and a safe receipt, without publishing data."""
    validate_lemon_url(url)
    if url not in http.explicit_urls:
        raise ValueError("LEMON_UNDISCOVERED_PAGE")
    key = hashlib.sha256(url.encode()).hexdigest()
    meta_path = cache_root / f"{key}.json"
    if use_cache and meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        path = cache_root / f"{meta['sha256']}.html"
        if meta.get("url") == url and path.is_file():
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() == meta["sha256"]:
                return content, {**meta, "cache_hit": True, "network_requests": 0}
    started = time.monotonic()
    request_count_before = http.requests
    try:
        response = http.get(url, allowed_hosts={ALLOWED_HOST})
    except PublicAccessError as exc:
        return b"", {
            "url": url,
            "status": exc.reason,
            "http_status": exc.http_status,
            "failed_request_url": exc.url,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "cache_hit": False,
            "network_requests": http.requests - request_count_before,
        }
    content_type = response.headers.get("content-type", "").split(";", 1)[0].casefold()
    if content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError("LEMON_NOT_HTML")
    if len(response.content) > MAX_HTML_BYTES:
        raise ValueError("HTML_SIZE_LIMIT")
    content = response.content
    digest = hashlib.sha256(content).hexdigest()
    cache_root.mkdir(parents=True, exist_ok=True)
    (cache_root / f"{digest}.html").write_bytes(content)
    meta = {
        "url": url,
        "status": "FETCHED_UNVERIFIED_APPLICABILITY",
        "http_status": response.status_code,
        "sha256": digest,
        "bytes": len(content),
        "retrieved_at": datetime.now(UTC).isoformat(),
        "elapsed_ms": round((time.monotonic() - started) * 1000),
        "cache_hit": False,
        "network_requests": http.requests - request_count_before,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return content, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="One explicitly discovered Lemon HTML URL")
    parser.add_argument("--receipt", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    validate_lemon_url(args.url)
    http = LemonSelectiveHTTP(explicit_urls={args.url})
    started = time.monotonic()
    try:
        try:
            content, receipt = fetch_explicit_page(http, args.url, use_cache=not args.no_cache)
        except ValueError as exc:
            content = b""
            receipt = {
                "url": args.url,
                "status": str(exc),
                "http_status": http.audit[-1]["http_status"] if http.audit else None,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "cache_hit": False,
                "network_requests": http.requests,
                "published_facts": 0,
            }
    finally:
        http.close()
    if content:
        try:
            result = parse_page(content, source_url=args.url, retrieved_at=receipt["retrieved_at"])
        except ValueError as exc:
            receipt.update(status=str(exc), tables=0, review_candidates=0, published_facts=0)
        else:
            stage_path = DEFAULT_CACHE / f"{receipt['sha256']}.parsed.json"
            stage_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            receipt.update(
                tables=len(result["tables"]),
                review_candidates=len(result["candidates"]),
                staging_path=str(stage_path),
                published_facts=0,
            )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
