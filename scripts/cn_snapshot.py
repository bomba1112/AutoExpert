"""Snapshot of the Chinese configuration catalogue (samr/catalog) into data_work/cn/staging.

Copies the configuration records (*.json), the component files (components/*/*.json),
index.csv, REPORT.md and the translations (i18n/glossary.json, i18n/az.json, i18n/en.json;
the phrase book they are built from stays in samr). Build scripts (_build) and review dumps
(_issues) stay in samr.
MANIFEST.json records the samr commit the snapshot was taken from and the sha256 of every
copied file; the snapshot is refused when samr/catalog has uncommitted changes, so the commit
hash always describes the copied bytes.

  .venv/Scripts/python.exe scripts/cn_snapshot.py [--samr C:/Users/jalil/samr]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "data_work" / "cn" / "staging"


def git(samr: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(samr), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samr", default=r"C:\Users\jalil\samr")
    args = parser.parse_args(argv)
    samr = Path(args.samr)
    catalog = samr / "catalog"
    dirty = git(samr, "status", "--porcelain", "--", "catalog", "turbo_specs.json")
    if dirty:
        print("samr has uncommitted changes in the catalogue; commit them first:\n" + dirty)
        return 1
    files = sorted(catalog.glob("*.json")) + sorted(catalog.glob("components/*/*.json"))
    files += [catalog / "index.csv", catalog / "REPORT.md"]
    files += [catalog / "i18n" / name for name in ("glossary.json", "az.json", "en.json")]
    target = STAGING / "catalog"
    if target.exists():
        shutil.rmtree(target)
    hashes = {}
    for path in files:
        relative = path.relative_to(catalog).as_posix()
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    # the turbo.az listings the catalogue was built from: the matcher's regression set
    listings = STAGING / "listings"
    listings.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(samr / "turbo_specs.json", listings / "turbo_specs.json")
    listing_hashes = {
        "turbo_specs.json": hashlib.sha256((samr / "turbo_specs.json").read_bytes()).hexdigest()
    }
    manifest = {
        "source": str(catalog),
        "samr_commit": git(samr, "rev-parse", "HEAD"),
        "samr_branch": git(samr, "rev-parse", "--abbrev-ref", "HEAD"),
        "samr_commit_subject": git(samr, "log", "-1", "--format=%s"),
        "snapshot_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "counts": {
            "configurations": sum(1 for k in hashes if "/" not in k and k.endswith(".json")),
            "components": sum(1 for k in hashes if k.startswith("components/")),
        },
        "files": hashes,
        "listing_files": listing_hashes,
    }
    (STAGING / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        "snapshot",
        manifest["samr_commit"][:10],
        manifest["counts"],
        "->",
        target.relative_to(ROOT),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
