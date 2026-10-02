"""Allowlisted source/deployment and public QA archives; no live data or credentials."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData"
EXCLUDED = {
    "__pycache__",
    ".venv",
    ".git",
    ".runtime",
    ".backups",
    ".localdata",
    ".signing",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    ".dart_tool",
    "build",
    "dist",
}
SUFFIXES = {".pyc", ".db", ".sqlite3", ".jks", ".keystore", ".p12", ".pem"}
ROOT_FILES = {
    ".gitignore",
    ".dockerignore",
    ".env.example",
    "pyproject.toml",
    "uv.lock",
    "uv.toml",
    "README.md",
    "Start-Local.ps1",
    "run-preview.ps1",
}
SOURCE_DIRS = {"backend", "apps", "data", "docs", "scripts", "deploy", "docker"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(path):
    parts = path.relative_to(ROOT).parts
    return (
        not path.is_symlink()
        and not EXCLUDED.intersection(parts)
        and path.suffix.lower() not in SUFFIXES
        and (not path.name.startswith(".env") or path.name == ".env.example")
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    policy = json.loads(
        (ROOT / "data/manifests/az-market-priority-policy.json").read_text(encoding="utf-8")
    )
    active_path = policy["active_catalog_manifest"]
    active = json.loads((ROOT / active_path).read_text(encoding="utf-8"))
    if policy.get("checkpoint_reporting", {}).get("format") == "vehicle-lists-first-v1":
        folder = OUT / active["batch_id"]
        tables = json.loads((folder / "catalog-tables.json").read_text(encoding="utf-8"))
        coverage = json.loads((folder / "coverage.json").read_text(encoding="utf-8"))
        expected = coverage["cumulative_us_with_seating_counts"]["model_year_configurations"]
        if (
            tables["batch_id"] != active["batch_id"]
            or sum(row["configuration_count"] for row in tables["cumulative_strict_output_catalog"])
            != expected
        ):
            raise SystemExit("Checkpoint catalogue lists do not match active coverage")
        if "cumulative_conditional_output_catalog" in tables:
            conditional = tables["cumulative_conditional_output_catalog"]
            base_expected = coverage["cumulative_basic_counts"]["model_year_configurations"]
            keys = [
                m["catalog_key"]
                for group in tables["cumulative_strict_output_catalog"] + conditional
                for m in group["members"]
            ]
            if expected + sum(
                g["configuration_count"] for g in conditional
            ) != base_expected or len(set(keys)) != len(keys):
                raise SystemExit("Conditional catalogue does not reconcile with basic coverage")
        start, end = "<!-- BEGIN VEHICLE CATALOG TABLES -->", "<!-- END VEHICLE CATALOG TABLES -->"
        rendered = (folder / "catalog-tables.md").read_text(encoding="utf-8")
        required_block = start + rendered.split(start, 1)[1].split(end, 1)[0] + end
        checkpoint = (ROOT / "docs/CHECKPOINT_US_BASE_CATALOG.md").read_text(encoding="utf-8")
        if required_block not in checkpoint:
            raise SystemExit("Checkpoint must contain complete delta and cumulative tables")
    mass_checkpoint = ROOT / "docs/CHECKPOINT_US_BASE_CATALOG_07_MASS.md"
    mass_summary = None
    if mass_checkpoint.exists():
        mass_folder = OUT / "us-base-catalog-07"
        mass_summary = json.loads(
            (mass_folder / "mass-scale-summary.json").read_text(encoding="utf-8")
        )
        mass_delta = json.loads((mass_folder / "mass-scale-delta.json").read_text(encoding="utf-8"))
        mass_cumulative = json.loads(
            (mass_folder / "mass-scale-cumulative.json").read_text(encoding="utf-8")
        )
        if (
            sum(g["configuration_count"] for g in mass_delta) != mass_summary["new_base_ready"]
            or sum(g["configuration_count"] for g in mass_cumulative)
            != mass_summary["after"]["model_year_configurations"]
            or mass_summary["removed_from_base_ready"]
            or "## Cumulative active US BASE_READY catalogue"
            not in mass_checkpoint.read_text(encoding="utf-8")
        ):
            raise SystemExit("Mass-scale checkpoint does not reconcile with named catalogues")
    # Values never leave memory or appear in output. Only exact secret matches are checked.
    values = dotenv_values(ROOT / ".env")
    secrets = [
        value.encode()
        for key, value in values.items()
        if value and len(value) >= 12 and re.search(r"KEY|TOKEN|PASSWORD|SECRET", key)
    ]
    source_files = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and safe(path)
        and (
            path.relative_to(ROOT).parts[0] in SOURCE_DIRS
            or path.relative_to(ROOT).as_posix() in ROOT_FILES
        )
    )
    qa_files = sorted(
        path
        for path in OUT.rglob("*")
        if path.is_file()
        and path.suffix in {".json", ".md", ".txt", ".png", ".html", ".webp", ".csv"}
        and path.name not in {"SHA256SUMS.txt", "package-manifest.json"}
    )
    for path in source_files + qa_files:
        content = path.read_bytes()
        if any(secret in content for secret in secrets):
            raise SystemExit("Secret gate blocked packaging: " + path.relative_to(ROOT).as_posix())
    archives = []
    for name, paths in [
        ("AutoExpert_0.8.1_VerifiedData_Source_Deployment.zip", source_files),
        ("AutoExpert_0.8.1_VerifiedData_QA.zip", qa_files),
    ]:
        archive = OUT / name
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for path in paths:
                z.write(path, path.relative_to(ROOT).as_posix())
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:
                raise SystemExit("Archive integrity failed")
        archives.append({"file": name, "files": len(paths), "bytes": archive.stat().st_size})
    manifest = {
        "version": "0.8.1",
        "secret_gate": "PASS",
        "live_database_included": False,
        "account_session_metadata_included": False,
        "latest_checkpoint": (
            "docs/CHECKPOINT_US_BASE_CATALOG_07_MASS.md"
            if mass_summary
            else "docs/CHECKPOINT_US_BASE_CATALOG.md"
        ),
        "mass_scale_current_batch": "us-base-catalog-07-mass" if mass_summary else None,
        "mass_scale_base_ready_annual_configurations": (
            mass_summary["after"]["model_year_configurations"] if mass_summary else None
        ),
        "active_catalog_batch": active["batch_id"],
        "active_catalog_manifest": active_path,
        "checkpoint_reporting_format": policy.get("checkpoint_reporting", {}).get("format"),
        "apk_rebuilt_for_this_batch": False,
        "documentary_corrections_portable": False,
        "documentary_restore_note": (
            "The base-catalog batch is published in the existing local database. Replay "
            "there is idempotent. A fresh database requires source acquisition, remapping "
            "RawDocument IDs, baseline revisions and a new editorial review. Neither the "
            "live database nor private document cache is distributed in these archives. "
            "The portable public fact bundle remains the preceding research baseline."
        ),
        "source_files": len(source_files),
        "archives": archives,
        "source_inventory": [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in source_files
        ],
    }
    (OUT / "package-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    targets = [ROOT / "deliverables/AutoExpert_2_0_Alpha_0.8.1.apk", *sorted(OUT.glob("*.zip"))]
    targets += sorted(OUT.glob("*.json"))
    (OUT / "SHA256SUMS.txt").write_text(
        "\n".join(f"{sha(p)}  {p.relative_to(ROOT).as_posix()}" for p in targets) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"secret_gate": "PASS", "archives": archives}))


if __name__ == "__main__":
    main()
