"""Free-text translation batches for the translation agents, and the check of one batch.

  .venv/Scripts/python.exe scripts/i18n_batches.py split [N]     data_work/_shared/i18n/missing.json ->
                                                                 batches/batch_NN.json (texts still missing)
  .venv/Scripts/python.exe scripts/i18n_batches.py check NN      checks llm/batch_NN.json against its batch:
                                                                 every text present, the same checks as
                                                                 i18n_build.py, glossary terms used
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "data_work" / "_shared" / "i18n"
sys.path.insert(0, str(ROOT / "scripts"))


def split(size: int) -> int:
    missing = json.loads((I18N / "missing.json").read_text(encoding="utf-8"))
    done = set()
    for path in (I18N / "llm").glob("*.json"):
        done |= {(e["kind"], e["hash"]) for e in json.loads(path.read_text(encoding="utf-8"))}
    todo = [e for e in missing if (e["kind"], e["hash"]) not in done]
    out = I18N / "batches"
    out.mkdir(parents=True, exist_ok=True)
    start = len(list(out.glob("batch_*.json")))
    for i in range(0, len(todo), size):
        number = start + i // size + 1
        chunk = [{"kind": e["kind"], "hash": e["hash"], "text": e["text"]} for e in todo[i:i + size]]
        (out / f"batch_{number:02d}.json").write_text(json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(todo)} texts in {(len(todo) + size - 1) // size} batches from batch_{start + 1:02d}")
    return 0


def check(number: str) -> int:
    from i18n_build import check as check_text
    from i18n_build import glossary_warnings

    batch = json.loads((I18N / "batches" / f"batch_{number}.json").read_text(encoding="utf-8"))
    path = I18N / "llm" / f"batch_{number}.json"
    if not path.exists():
        print("missing output", path)
        return 1
    done = {(e["kind"], e["hash"]): e for e in json.loads(path.read_text(encoding="utf-8"))}
    general = json.loads((I18N / "glossary.json").read_text(encoding="utf-8"))["terms"].get("general", {})
    bad = 0
    for e in batch:
        t = done.get((e["kind"], e["hash"]))
        if t is None:
            print("NOT TRANSLATED", e["hash"][:12], e["text"][:80])
            bad += 1
            continue
        problems = check_text(e["text"], t.get("ru", ""), t.get("az", ""), general)
        warnings = glossary_warnings(e["text"], t.get("ru", ""), t.get("az", ""), general)
        if problems:
            bad += 1
            print("FAIL", e["hash"][:12], problems)
        for w in warnings:
            print("GLOSSARY", e["hash"][:12], w)
    print(f"batch {number}: {len(batch)} texts, {len(batch) - bad} pass, {bad} fail")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1] == "split":
        sys.exit(split(int(sys.argv[2]) if len(sys.argv) > 2 else 78))
    sys.exit(check(sys.argv[2]))
