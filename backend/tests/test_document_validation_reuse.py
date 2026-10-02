"""Integrity must survive reuse of a document across many applicable facts."""

import hashlib
import os
from unittest.mock import patch

import pytest
from app.services.catalog_verification import _document_checksum
from app.services.knowledge_import import checksum


def test_same_bytes_reused_only_in_supplied_validation_cache(tmp_path):
    path = tmp_path / "document.pdf"
    path.write_bytes(b"same immutable source")
    cache = {}
    with patch("app.services.knowledge_import.checksum", wraps=checksum) as hashed:
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        assert _document_checksum(path, cache) == expected
        assert _document_checksum(path, cache) == expected
        assert hashed.call_count == 1
        assert _document_checksum(path, {}) == expected
        assert hashed.call_count == 2


def test_changed_same_size_document_invalidates_cached_hash(tmp_path):
    path = tmp_path / "document.pdf"
    path.write_bytes(b"original")
    cache = {}
    original = _document_checksum(path, cache)
    stamp = path.stat().st_mtime_ns
    path.write_bytes(b"tampered")
    os.utime(path, ns=(stamp + 10_000_000, stamp + 10_000_000))
    assert _document_checksum(path, cache) != original


def test_document_changed_during_read_is_rejected(tmp_path):
    path = tmp_path / "document.pdf"
    path.write_bytes(b"original")
    stamp = path.stat().st_mtime_ns

    def changed(data):
        path.write_bytes(b"tampered")
        os.utime(path, ns=(stamp + 10_000_000, stamp + 10_000_000))
        return checksum(data)

    with (
        patch("app.services.knowledge_import.checksum", side_effect=changed),
        pytest.raises(ValueError, match="VERIFICATION_DOCUMENT_MISMATCH"),
    ):
        _document_checksum(path, {})
