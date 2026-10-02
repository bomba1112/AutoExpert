"""Shared plumbing for the batch US tech-database collectors.

Bulky raw files (PDF manuals, crawled HTML, API responses) live outside OneDrive under
RAW_ROOT (default C:\\AutoExpertData\\raw, override with AUTOEXPERT_RAW_ROOT). Manifests
with URL, HTTP status, size, sha256 and retrieval time are tracked in git under
data_work/, so every raw file can be re-identified and re-downloaded.

Politeness: one Fetcher per host, one request at a time, a random pause between
requests, up to 3 retries with growing pauses on timeouts and 5xx, and a stop after
repeated 403/429 answers.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import os
import random
import ssl
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data_work"
RAW_ROOT = Path(os.environ.get("AUTOEXPERT_RAW_ROOT", r"C:\AutoExpertData\raw"))
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_ref(path: Path) -> str:
    """Portable reference stored in evidence: rawstore:<path relative to RAW_ROOT>."""
    return "rawstore:" + path.relative_to(RAW_ROOT).as_posix()


def raw_path(ref: str) -> Path:
    if ref.startswith("rawstore:"):
        return RAW_ROOT / ref[len("rawstore:") :]
    return ROOT / ref


def write_gz(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as handle:
        handle.write(data)


def read_maybe_gz(path: Path) -> bytes:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as handle:
            return handle.read()
    return path.read_bytes()


class Manifest:
    """Append-only CSV manifest; rows are keyed by URL."""

    def __init__(self, path: Path, fields: list[str]):
        self.path, self.fields = path, fields
        self.rows: dict[str, dict] = {}
        if path.exists():
            with path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    self.rows[row["url"]] = row

    def ok(self, url: str) -> dict | None:
        row = self.rows.get(url)
        return row if row and row.get("status") == "ok" else None

    def add(self, row: dict) -> None:
        self.rows[row["url"]] = row
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists()
        for attempt in range(6):  # OneDrive sync can briefly lock the file
            try:
                with self.path.open("a", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=self.fields)
                    if new:
                        writer.writeheader()
                    writer.writerow({k: row.get(k, "") for k in self.fields})
                return
            except PermissionError:
                time.sleep(2 * (attempt + 1))
        raise PermissionError(f"manifest locked: {self.path}")


class Blocked(RuntimeError):
    pass


class Fetcher:
    """One host, one request at a time, polite pauses, bounded retries."""

    def __init__(self, pause=(2.0, 5.0), timeout=90, max_blocks=3, headers=None, attempts=4):
        self.client = httpx.Client(
            headers={"User-Agent": UA, **(headers or {})},
            timeout=timeout,
            follow_redirects=True,
            verify=ssl.create_default_context(),  # system roots, as backend providers do
        )
        self.pause = pause
        self.attempts = attempts
        self.max_blocks = max_blocks
        self.blocks = 0
        self.requests = 0

    def get(self, url: str, params=None, headers=None) -> httpx.Response | None:
        extra = 0.0
        for attempt in range(self.attempts):
            time.sleep(random.uniform(*self.pause) + extra)
            self.requests += 1
            try:
                response = self.client.get(url, params=params, headers=headers)
            except httpx.HTTPError:
                extra = 5.0 * (attempt + 1)
                continue
            if response.status_code in (403, 429):
                self.blocks += 1
                if self.blocks >= self.max_blocks:
                    raise Blocked(f"{response.status_code} on {url}")
                self.pause = (self.pause[0] * 2, self.pause[1] * 2)
                extra = 15.0 * (attempt + 1)
                continue
            self.blocks = 0
            if response.status_code >= 500:
                extra = 5.0 * (attempt + 1)
                continue
            return response
        return None
