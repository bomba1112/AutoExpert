# ruff: noqa: E501
"""Convert the NHTSA standalone vPIC database (PostgreSQL plain dump, vpic.nhtsa.dot.gov/downloads,
"vPICList_lite_YYYY_MM.plain.zip") into a local SQLite file for VIN decoding in the Garage
(product phase, stage 2): the app decodes a VIN from this file only, with no external requests.

Only the tables the decoder needs are copied: WMI, schemas, patterns, elements and the lookup
tables the elements name. The big per-year valid-character cache and the vehicle-spec tables are
left out. The output never goes into git (C:\\AutoExpertData\\vpic\\vpic_lite.sqlite by default).

    python scripts/vpic_standalone_import.py <dump.sql> [<out.sqlite>]
"""

from __future__ import annotations

import re
import sqlite3
import sys
import time
from pathlib import Path

DEFAULT_OUT = Path(r"C:\AutoExpertData\vpic\vpic_lite.sqlite")
SKIP = {"wmiyearvalidchars", "wmiyearvalidchars_cacheexceptions", "vehiclespecpattern", "vehiclespecschema",
        "vehiclespecschema_model", "vehiclespecschema_year", "vspecschemapattern", "defs_body", "defs_make",
        "defs_model", "decodingoutput", "vindescriptor", "vinexception", "manufacturer_make"}
COPY = re.compile(r"^COPY vpic\.(\w+) \(([^)]*)\) FROM stdin;$")
ESCAPES = {"\\t": "\t", "\\n": "\n", "\\r": "\r", "\\\\": "\\"}
INDEXES = ["CREATE INDEX ix_wmi_wmi ON wmi (wmi)", "CREATE INDEX ix_wvs_wmi ON wmi_vinschema (wmiid)",
           "CREATE INDEX ix_pattern_schema ON pattern (vinschemaid)", "CREATE INDEX ix_wmi_make ON wmi_make (wmiid)",
           "CREATE INDEX ix_make_model ON make_model (modelid)", "CREATE INDEX ix_emp ON enginemodelpattern (enginemodelid)"]


def unescape(field: str):
    if field == "\\N":
        return None
    return re.sub(r"\\[tnr\\]", lambda m: ESCAPES[m.group(0)], field) if "\\" in field else field


def main(dump: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    db = sqlite3.connect(tmp)
    db.execute("PRAGMA journal_mode=OFF")
    db.execute("PRAGMA synchronous=OFF")
    counts, table, columns, batch = {}, None, [], []
    started = time.time()
    with dump.open(encoding="utf-8") as handle:
        for line in handle:
            if table is None:
                m = COPY.match(line.rstrip("\n"))
                if m and m.group(1) not in SKIP:
                    table, columns = m.group(1), [c.strip().strip('"') for c in m.group(2).split(",")]
                    db.execute(f'CREATE TABLE {table} ({", ".join(columns)})')
                    batch = []
                continue
            if line.startswith("\\."):
                insert = f'INSERT INTO {table} VALUES ({", ".join("?" * len(columns))})'
                db.executemany(insert, batch)
                counts[table] = len(batch)
                table = None
                continue
            batch.append([unescape(f) for f in line.rstrip("\n").split("\t")])
    for statement in INDEXES:
        db.execute(statement)
    db.execute("CREATE TABLE meta (key, value)")
    db.executemany("INSERT INTO meta VALUES (?, ?)", [("source", dump.name), ("origin", "https://vpic.nhtsa.dot.gov/downloads/"),
                                                       ("imported_at", time.strftime("%Y-%m-%d %H:%M:%S"))])
    db.commit()
    db.close()
    tmp.replace(out)
    print(f"{out} — {len(counts)} tables, pattern rows {counts.get('pattern')}, {time.time() - started:.0f} s")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT)
