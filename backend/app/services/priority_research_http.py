"""Shared official dataset cache for an explicit local batch with request accounting."""

import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlsplit

from app.core.config import get_settings
from app.providers.official_nhtsa import OfficialProviderUnavailable
from app.services.catalog_research import BudgetHTTP
from app.services.knowledge_registry import utcnow


class PriorityHTTP(BudgetHTTP):
    def __init__(self, cancelled=lambda: False):
        super().__init__(cancelled=cancelled)
        self.max_response_bytes = 32 * 1024 * 1024
        self.min_interval_seconds = 0.5
        self.cache_hits = 0
        self.receipts = []
        self.last_status = None
        self.actual_requests = 0
        self.client.event_hooks["response"].append(self._response_status)
        self.client.event_hooks["request"].append(self._count_request)

    def _response_status(self, response):
        self.last_status = response.status_code

    def _count_request(self, request):
        self.actual_requests += 1

    def _request(self, url, *, headers=None):
        p = urlsplit(url)
        shared = (p.hostname == "static.nhtsa.gov" and p.path.startswith("/odi/ffdd/tsbs/")) or (
            p.hostname == "vpic.nhtsa.dot.gov" and "/GetModelsForMakeYear/" in p.path
        )
        root = Path(get_settings().knowledge_data_dir) / "priority-official-cache"
        key = hashlib.sha256(url.encode()).hexdigest()
        body_path, meta_path = root / (key + ".bin"), root / (key + ".json")
        if shared and body_path.is_file() and meta_path.is_file():
            meta = json.loads(meta_path.read_text())
            if meta["url"] == url and time.time() - meta["timestamp"] < 86400:
                body = body_path.read_bytes()
                if hashlib.sha256(body).hexdigest() != meta["sha256"]:
                    raise OfficialProviderUnavailable(
                        "SHARED_CACHE_CHECKSUM_FAILED", api_requests=0
                    )
                self.cache_hits += 1
                self.receipts.append({**meta, "cache_hit": True, "network_calls": 0})
                return body, 0
        before = time.monotonic()
        self.last_status = None
        requests_before = self.actual_requests
        try:
            body, calls = super()._request(url, headers=headers)
        except OfficialProviderUnavailable:
            self.receipts.append(
                {
                    "url": url,
                    "status": "UNAVAILABLE",
                    "http_status": self.last_status,
                    "network_calls": self.actual_requests - requests_before,
                    "latency_ms": round((time.monotonic() - before) * 1000),
                    "observed_at": utcnow().isoformat(),
                    "cache_hit": False,
                }
            )
            raise
        meta = {
            "url": url,
            "timestamp": time.time(),
            "observed_at": utcnow().isoformat(),
            "http_status": self.last_status,
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
            "latency_ms": round((time.monotonic() - before) * 1000),
        }
        if shared:
            root.mkdir(parents=True, exist_ok=True)
            body_path.write_bytes(body)
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
        self.receipts.append({**meta, "cache_hit": False, "network_calls": calls})
        return body, calls
