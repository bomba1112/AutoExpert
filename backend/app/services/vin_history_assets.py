"""Authorized provider import boundary and content-addressed original photo storage.

Adapters obtain assets through their own approved provider connection. This service
never fetches arbitrary URLs. Bytes are required before a gallery can be published.
"""

import hashlib
import io
import os
from pathlib import Path

from PIL import Image

from app.providers.vin_history import VINHistoryResearch


def asset_root() -> Path:
    return Path(os.environ.get("AUTOEXPERT_VIN_ASSETS_DIR", ".runtime/vin-assets"))


def validate_photo_assets(photo_sets, assets: dict[str, bytes]):
    validated = []
    for group in photo_sets:
        for photo in group.photos:
            content = assets.get(photo.id)
            if not content or len(content) > 8_000_000:
                raise ValueError("Each photograph requires an original asset within 8 MB")
            with Image.open(io.BytesIO(content)) as picture:
                if picture.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Unsupported vehicle photograph format")
                if picture.width * picture.height > 40_000_000:
                    raise ValueError("Photograph exceeds pixel budget")
                picture.verify()
            digest = hashlib.sha256(content).hexdigest()
            if photo.asset_sha256 and photo.asset_sha256 != digest:
                raise ValueError("Photograph checksum differs from provider provenance")
            photo.asset_sha256 = digest
            validated.append((digest, content))
    return validated


def attach_history(check, research: VINHistoryResearch, assets: dict[str, bytes]) -> None:
    if check.is_demo or check.normalized_vin != research.vin:
        raise ValueError("History must belong to the real VIN check")
    validated = validate_photo_assets(research.photo_sets, assets)
    folder = asset_root()
    if validated:
        folder.mkdir(parents=True, exist_ok=True)
    for digest, content in validated:
        (folder / digest).write_bytes(content)
    check.full_history_payload = {
        **research.history.model_dump(mode="json"),
        "photo_sets": [p.model_dump(mode="json") for p in research.photo_sets],
        "provider_id": research.provider_id,
    }
    sources = {s["id"]: s for s in check.source_snapshot}
    sources.update({s.id: s.model_dump(mode="json") for s in research.sources})
    check.source_snapshot = list(sources.values())
    check.photos_count = len(validated)
    check.auctions_count = len(research.history.auctions)
    check.records_count = sum(
        len(getattr(research.history, key))
        for key in ("timeline", "auctions", "damage_details", "odometer_records")
    )


def photo_bytes(photo) -> bytes:
    digest = photo.asset_sha256
    if not digest:
        raise ValueError("Photograph has not been imported")
    content = (asset_root() / digest).read_bytes()
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("Stored photograph checksum mismatch")
    return content
