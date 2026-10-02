"""Allowlisted source/deployment and public QA archives; no live data or credentials."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/MasterLocal"
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
        and path.suffix in {".json", ".md", ".txt", ".png"}
        and path.name not in {"SHA256SUMS.txt", "package-manifest.json"}
    )
    for path in source_files + qa_files:
        content = path.read_bytes()
        if any(secret in content for secret in secrets):
            raise SystemExit("Secret gate blocked packaging: " + path.relative_to(ROOT).as_posix())
    archives = []
    for name, paths in [
        ("AutoExpert_0.8.0_MasterLocal_Source_Deployment.zip", source_files),
        ("AutoExpert_0.8.0_MasterLocal_QA.zip", qa_files),
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
        "version": "0.8.0",
        "secret_gate": "PASS",
        "live_database_included": False,
        "account_session_metadata_included": False,
        "source_files": len(source_files),
        "archives": archives,
        "source_inventory": [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in source_files
        ],
    }
    (OUT / "package-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    targets = [ROOT / "deliverables/AutoExpert_2_0_Alpha_0.8.0.apk", *sorted(OUT.glob("*.zip"))]
    targets += sorted(OUT.glob("*.json"))
    (OUT / "SHA256SUMS.txt").write_text(
        "\n".join(f"{sha(p)}  {p.relative_to(ROOT).as_posix()}" for p in targets) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"secret_gate": "PASS", "archives": archives}))


if __name__ == "__main__":
    main()
