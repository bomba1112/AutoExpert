"""Load the checked translations (data_work/_shared/i18n/translations.json) into
content_translations of a database (the rehearsal copy first, then live).

A new (kind, sha256) is inserted; an existing one with the same Russian and Azerbaijani text is
left alone; an existing one whose text changed (a glossary or translation correction) is
updated and the change is written to data_work/_shared/i18n/load_changes_<db>.json.
The English originals in their own tables are never touched.

  .venv/Scripts/python.exe scripts/i18n_load.py rehearsal|live
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "data_work" / "_shared" / "i18n"
TARGETS = {"live": ROOT / "autoexpert.db", "rehearsal": Path(r"C:\AutoExpertData\work\rehearsal_batch.db")}


def main(target: str) -> int:
    path = TARGETS[target]
    rows = json.loads((I18N / "translations.json").read_text(encoding="utf-8"))
    db = sqlite3.connect(path)
    if not db.execute("select name from sqlite_master where type='table' and name='content_translations'").fetchone():
        raise SystemExit("content_translations missing: run the f088 migration first")
    now = datetime.now(UTC).isoformat()
    existing = {(k, h): (ru, az) for k, h, ru, az in db.execute("select kind, source_hash, text_ru, text_az from content_translations")}
    inserted = same = 0
    changes = []
    for r in rows:
        key = (r["kind"], r["hash"])
        status = "REVIEWED" if r.get("reviewed") else "CHECKED"
        if key not in existing:
            db.execute("insert into content_translations (id, created_at, updated_at, kind, source_hash, source_text, text_ru, text_az, "
                       "method, glossary_version, status) values (?,?,?,?,?,?,?,?,?,?,?)",
                       (str(uuid4()), now, now, r["kind"], r["hash"], r["text"], r["ru"], r["az"], r["method"], r["glossary_version"], status))
            inserted += 1
        elif existing[key] == (r["ru"], r["az"]):
            same += 1
        else:
            db.execute("update content_translations set text_ru=?, text_az=?, method=?, glossary_version=?, status=?, updated_at=? "
                       "where kind=? and source_hash=?", (r["ru"], r["az"], r["method"], r["glossary_version"], status, now, *key))
            changes.append({"kind": r["kind"], "hash": r["hash"], "old": existing[key], "new": [r["ru"], r["az"]]})
    db.commit()
    total = db.execute("select count(*) from content_translations").fetchone()[0]
    check = db.execute("pragma quick_check").fetchone()[0]
    db.close()
    if changes:
        (I18N / f"load_changes_{target}.json").write_text(json.dumps({"at": now, "changes": changes}, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    print(f"{target}: inserted {inserted}, unchanged {same}, updated {len(changes)}, total {total}, quick_check {check}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
