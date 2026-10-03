"""Full (not sampled) re-check of every fact cited from a Teoalida database: the workbook's sha256
is the one cited, and the quote is found again in the cited sheet row (page text of the sheet).

  .venv/Scripts/python.exe scripts/recheck_teoalida.py bmw [toyota …]
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402


def norm(text: str) -> str:
    return " ".join(str(text).replace(" ", " ").split())


def main(makes: list[str]) -> int:
    checked = bad = 0
    sha_ok: dict[str, bool] = {}
    pages_cache: dict[str, list] = {}
    for make in makes:
        for path in sorted((WORK / make / "staging").glob("*/staging.json")):
            st = json.loads(path.read_text(encoding="utf-8"))
            for fact in st.get("facts", []):
                for cite in fact["cites"]:
                    src = st["sources"][cite["source"]]
                    if src.get("registry") != "teoalida":
                        continue
                    checked += 1
                    raw = RAW_ROOT / src["path"][len("rawstore:"):]
                    if src["sha256"] not in sha_ok:
                        sha_ok[src["sha256"]] = hashlib.sha256(raw.read_bytes()).hexdigest() == src["sha256"]
                    if not sha_ok[src["sha256"]]:
                        bad += 1
                        print("SHA", path.parent.name, fact["id"])
                        continue
                    if src["sha256"] not in pages_cache:
                        with gzip.open(RAW_ROOT / "pagetext" / f"{src['sha256']}.json.gz", "rt", encoding="utf-8") as h:
                            pages_cache[src["sha256"]] = json.load(h)["pages"]
                    pages = pages_cache[src["sha256"]]
                    if not any(norm(cite["quote"]) in norm(pages[p - 1]) for p in cite.get("pages") or []):
                        bad += 1
                        print("QUOTE", path.parent.name, fact["id"], cite["quote"][:100])
    print(f"teoalida citations checked {checked}, problems {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
