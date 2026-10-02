from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DataOrigin, EvidenceStatus
from app.models.research import ProviderCacheEntry
from app.schemas.research import ProviderResult, VehicleResearchRequest
from app.services.provider_registry import ProviderRegistry


class ProviderRouter:
    """Selects one lowest-cost active provider per capability and persists successes."""

    def __init__(
        self,
        db: Session,
        registry: ProviderRegistry,
        *,
        cache_ttl: timedelta = timedelta(hours=24),
    ) -> None:
        self.db = db
        self.registry = registry
        self.cache_ttl = cache_ttl

    def fetch(
        self,
        request: VehicleResearchRequest,
        capabilities: list[str],
        *,
        context: dict | None = None,
    ) -> list[ProviderResult]:
        results: list[ProviderResult] = []
        for capability in dict.fromkeys(capabilities):
            candidates = self.registry.for_capability(
                market=request.market,
                capability=capability,
            )
            if not candidates:
                results.append(
                    ProviderResult(
                        provider_id="none",
                        capability=capability,
                        status=EvidenceStatus.INSUFFICIENT_DATA,
                        source_url="urn:autoexpert:provider-registry",
                        retrieved_at=datetime.now(UTC),
                        error=f"No active provider for {request.market}/{capability}",
                    )
                )
                continue
            for selected in candidates:
                version = getattr(selected.provider, "normalization_version", None)
                cache_context = (
                    {**(context or {}), "normalization_version": version} if version else context
                )
                cache_key = self._cache_key(request, cache_context)
                cached = self._cached(selected.definition.id, capability, cache_key)
                if cached is not None:
                    metadata = cached.raw_payload if isinstance(cached.raw_payload, dict) else {}
                    result = ProviderResult(
                        provider_id=cached.provider_id,
                        capability=cached.capability,
                        status=cached.status,
                        records=cached.normalized_payload,
                        raw_payload=cached.raw_payload,
                        source_url=cached.source_url,
                        retrieved_at=cached.retrieved_at.replace(tzinfo=UTC)
                        if cached.retrieved_at.tzinfo is None
                        else cached.retrieved_at,
                        from_cache=True,
                        api_requests=0,
                        duration_ms=0,
                        error=metadata.get("_cached_error"),
                        http_status=metadata.get("_cached_http_status", 200),
                        data_origin=cached.data_origin,
                    )
                else:
                    if context is not None and hasattr(selected.provider, "fetch_context"):
                        result = selected.provider.fetch_context(request, context)
                    else:
                        result = selected.provider.fetch(request)
                    if context is not None or result.error is None:
                        self._save_cache(result, cache_key)
                results.append(result)
                if result.error is None and result.status == EvidenceStatus.CONFIRMED:
                    break
        return results

    def _cached(
        self,
        provider_id: str,
        capability: str,
        cache_key: str,
    ) -> ProviderCacheEntry | None:
        now = datetime.now(UTC)
        entry = self.db.scalar(
            select(ProviderCacheEntry).where(
                ProviderCacheEntry.provider_id == provider_id,
                ProviderCacheEntry.capability == capability,
                ProviderCacheEntry.cache_key == cache_key,
            )
        )
        if entry is None:
            return None
        expires_at = entry.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return entry if expires_at > now else None

    def _save_cache(self, result: ProviderResult, cache_key: str) -> None:
        ttl = self.cache_ttl if result.status == EvidenceStatus.CONFIRMED else timedelta(minutes=15)
        raw = result.raw_payload
        if result.error:
            raw = {
                "_cached_error": result.error,
                "_cached_http_status": result.http_status,
                "payload": raw,
            }
        entry = self.db.scalar(
            select(ProviderCacheEntry).where(
                ProviderCacheEntry.provider_id == result.provider_id,
                ProviderCacheEntry.capability == result.capability,
                ProviderCacheEntry.cache_key == cache_key,
            )
        )
        if entry is None:
            entry = ProviderCacheEntry(
                provider_id=result.provider_id,
                capability=result.capability,
                cache_key=cache_key,
                status=result.status,
                source_url=result.source_url,
                normalized_payload=result.records,
                raw_payload=raw,
                retrieved_at=result.retrieved_at,
                expires_at=result.retrieved_at + ttl,
                data_origin=DataOrigin.REAL,
            )
            self.db.add(entry)
        else:
            entry.status = result.status
            entry.source_url = result.source_url
            entry.normalized_payload = result.records
            entry.raw_payload = raw
            entry.retrieved_at = result.retrieved_at
            entry.expires_at = result.retrieved_at + ttl
            entry.data_origin = DataOrigin.REAL
        self.db.flush()

    @staticmethod
    def _cache_key(request: VehicleResearchRequest, context: dict | None = None) -> str:
        canonical = request.model_dump(mode="json", exclude_none=True)
        if context is not None:
            canonical["knowledge_context"] = context
        encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()
