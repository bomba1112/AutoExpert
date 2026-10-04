# ruff: noqa: E501
"""VIN decoding from the local standalone vPIC database (product phase, stage 2: the Garage adds a
car by VIN with no external request).

The database is NHTSA's standalone vPIC (vpic.nhtsa.dot.gov/downloads), converted to SQLite by
scripts/vpic_standalone_import.py; its path is settings.vpic_database_path. The decoding follows
NHTSA's own stored procedure (vpic.spvindecode / spvindecode_core in the dump):
- WMI = positions 1-3 (+ 12-14 when position 3 is "9");
- model year from position 10, the 30-year cycle told by position 7 for cars / MPV / light trucks;
- keys = positions 4-8 + "|" + positions 10-17, matched against the patterns of the vehicle schemas
  the WMI has for that year ("*" any character, [..] a class, a prefix match);
- per element the best pattern wins: schema year (later first), change date (later first), fewer
  fixed characters, keys, id;
- the make comes from the decoded model (Make_Model), else from the WMI when it has one make;
- the engine model adds its EngineModelPattern elements; displacement in L from cc / ci.
Only the vehicle identity is used (make, model, year, engine, drive, gearbox, fuel, body, trim);
the result is a hint for choosing our configuration, never a fact of the car card.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from datetime import date
from pathlib import Path

from app.core.config import get_settings

TRANSLITERATION = {**{c: i + 1 for i, c in enumerate("ABCDEFGH")}, **{c: i + 1 for i, c in enumerate("JKLMN")},
                   "P": 7, "R": 9, **{c: i + 2 for i, c in enumerate("STUVWXYZ")}, **{str(d): d for d in range(10)}}
WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
MULTI = {"121", "129", "150", "154", "155", "114", "169", "186"}  # elements that keep every value
SKIP_ELEMENTS = {"26", "27", "29", "39"}
WANTED = {"26": "make", "28": "model", "13": "displacement_l", "9": "cylinders", "15": "drive", "37": "transmission",
          "63": "transmission_speeds", "24": "fuel", "66": "fuel_secondary", "38": "trim", "109": "trim2", "34": "series",
          "5": "body", "18": "engine_model", "135": "turbo", "126": "electrification", "14": "doors", "64": "engine_configuration",
          "71": "engine_hp", "75": "plant_country", "39": "vehicle_type", "27": "manufacturer"}

_LOCK = threading.Lock()
_ELEMENTS: dict | None = None


def database_path() -> Path:
    return Path(get_settings().vpic_database_path)


def available() -> bool:
    return database_path().is_file()


def normalize(vin: str) -> str:
    return re.sub(r"[\s-]", "", str(vin or "")).upper()


def check_digit(vin: str) -> str | None:
    """The North American check digit (position 9) the VIN should carry."""
    if not VIN_RE.match(vin):
        return None
    total = sum(TRANSLITERATION[c] * w for c, w in zip(vin, WEIGHTS, strict=True))
    rest = total % 11
    return "X" if rest == 10 else str(rest)


def wmi_of(vin: str) -> str:
    wmi = vin[:3]
    return wmi + vin[11:14] if wmi[2] == "9" and len(vin) >= 14 else wmi


def _year_from_position_10(c: str) -> int | None:
    if "A" <= c <= "H":
        return 2010 + ord(c) - ord("A")
    if "J" <= c <= "N":
        return 2010 + ord(c) - ord("A") - 1
    if c == "P":
        return 2023
    if "R" <= c <= "T":
        return 2010 + ord(c) - ord("A") - 3
    if "V" <= c <= "Y":
        return 2010 + ord(c) - ord("A") - 4
    if "1" <= c <= "9":
        return 2031 + ord(c) - ord("1")
    return None


def model_years(vin: str, vehicle_type: str | None, truck_type: str | None, today: date | None = None) -> list[int]:
    """Candidate model years, the most likely first (vpic.fVinModelYear2)."""
    year = _year_from_position_10(vin[9])
    if year is None:
        return []
    limit = (today or date.today()).year + 2
    car_lt = vehicle_type in ("2", "7") or (vehicle_type == "3" and truck_type == "1")
    if car_lt and vin[6].isdigit():
        return [year - 30]
    if car_lt and vin[6].isalpha():
        return [year]
    if year > limit:
        return [year - 30]
    return [year, year - 30]


def _regex(keys: str) -> re.Pattern:
    out = []
    for ch in keys:
        out.append("." if ch == "*" else ch if ch in "[]" else re.escape(ch))
    text = "".join(out)
    if "[" in keys:
        text = text.replace("1-A", "1A")
    return re.compile("^" + text)


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{database_path()}?mode=ro", uri=True, check_same_thread=False)


def _elements(db: sqlite3.Connection) -> dict:
    global _ELEMENTS
    with _LOCK:
        if _ELEMENTS is None:
            _ELEMENTS = {r[0]: {"name": r[1], "code": r[2], "lookup": r[3], "datatype": r[4], "decode": r[5], "private": r[6]}
                         for r in db.execute("SELECT id, name, code, lookuptable, datatype, decode, isprivate FROM element")}
        return _ELEMENTS


def _lookup(db: sqlite3.Connection, element: dict, attribute: str) -> str:
    table = element.get("lookup")
    if element.get("datatype") != "lookup" or not table or not re.fullmatch(r"\w+", table):
        return attribute
    row = db.execute(f"SELECT name FROM {table} WHERE id = ?", (attribute,)).fetchone()
    return row[0] if row else attribute


def _items(db: sqlite3.Connection, vin: str, year: int, wmi_row) -> list[dict]:
    wmi_id = wmi_row[0]
    keys = vin[3:8] + "|" + vin[9:17]
    elements = _elements(db)
    items = []
    rows = db.execute(
        "SELECT p.id, p.keys, p.elementid, p.attributeid, coalesce(p.updatedon, p.createdon), wvs.yearfrom, p.vinschemaid "
        "FROM wmi_vinschema wvs JOIN pattern p ON p.vinschemaid = wvs.vinschemaid "
        "LEFT JOIN vinschema vs ON vs.id = wvs.vinschemaid "
        "WHERE wvs.wmiid = ? AND CAST(wvs.yearfrom AS INTEGER) <= ? AND (wvs.yearto IS NULL OR CAST(wvs.yearto AS INTEGER) >= ?) "
        "AND coalesce(vs.tobeqced, 'f') = 'f'", (wmi_id, year, year))
    for pid, pkeys, element_id, attribute, changed, year_from, _schema in rows:
        element = elements.get(element_id) or {}
        if element_id in SKIP_ELEMENTS or not element.get("decode") or element.get("private") == "t":
            continue
        if "#" in pkeys or not _regex(pkeys.upper()).match(keys):
            continue
        items.append({"element": element_id, "attribute": attribute, "priority": int(year_from), "changed": changed or "",
                      "keys": pkeys.upper(), "id": int(pid), "source": "pattern"})
    engine = _best(items, "18")
    if engine:
        for element_id, attribute in db.execute(
                "SELECT p.elementid, p.attributeid FROM enginemodel em JOIN enginemodelpattern p ON p.enginemodelid = em.id "
                "WHERE lower(trim(em.name)) = lower(trim(?))", (engine["attribute"],)):
            items.append({"element": element_id, "attribute": attribute, "priority": 50, "changed": "", "keys": engine["keys"],
                          "id": 0, "source": "engine model"})
    return items


def _rank(item: dict) -> tuple:
    keys = item["keys"] or ""
    return (-item["priority"], _desc(item["changed"]), len(keys.replace("*", "")), keys.replace("[", "").replace("]", ""), item["id"])


def _desc(text: str) -> tuple:
    return tuple(-ord(c) for c in text) + (1,)


def _best(items: list[dict], element_id: str) -> dict | None:
    found = [i for i in items if i["element"] == element_id]
    return min(found, key=_rank) if found else None


def decode(vin: str) -> dict:
    """Decode a VIN from the local database. Never raises for a bad VIN: the result says why."""
    vin = normalize(vin)
    result: dict = {"vin": vin, "valid": False, "errors": [], "source": "NHTSA vPIC standalone (local)"}
    if not VIN_RE.match(vin):
        result["errors"].append("FORMAT")  # 17 characters, no I / O / Q
        return result
    result["check_digit_ok"] = check_digit(vin) == vin[8]
    if not available():
        result["errors"].append("DATABASE_UNAVAILABLE")
        return result
    with _connect() as db:
        wmi = wmi_of(vin)
        wmi_row = db.execute("SELECT id, vehicletypeid, trucktypeid, manufacturerid FROM wmi WHERE wmi = ?", (wmi,)).fetchone()
        if not wmi_row:
            result["errors"].append("UNKNOWN_WMI")
            return result
        best, best_year = [], None
        for year in model_years(vin, wmi_row[1], wmi_row[2]):
            items = _items(db, vin, year, wmi_row)
            if len({i["element"] for i in items}) > len({i["element"] for i in best}) or best_year is None:
                best, best_year = items, year
        values: dict = {}
        elements = _elements(db)
        for element_id in sorted({i["element"] for i in best}):
            chosen = [i for i in best if i["element"] == element_id]
            chosen = chosen if element_id in MULTI else [min(chosen, key=_rank)]
            text = "; ".join(_lookup(db, elements.get(element_id, {}), i["attribute"]) for i in chosen)
            values[element_id] = text
        model_item = _best(best, "28")
        make = None
        if model_item:
            row = db.execute("SELECT mk.name FROM make_model mm JOIN make mk ON mk.id = mm.makeid WHERE mm.modelid = ?",
                             (model_item["attribute"],)).fetchone()
            make = row[0] if row else None
        if make is None:
            makes = db.execute("SELECT mk.name FROM wmi_make wm JOIN make mk ON mk.id = wm.makeid WHERE wm.wmiid = ?",
                               (wmi_row[0],)).fetchall()
            make = makes[0][0] if len(makes) == 1 else None
        if make:
            values["26"] = make
        if "13" not in values:
            if "11" in values and _number(values["11"]) is not None:
                values["13"] = f"{_number(values['11']) / 1000:.1f}"
            elif "12" in values and _number(values["12"]) is not None:
                values["13"] = f"{_number(values['12']) * 0.016387064:.1f}"
        manufacturer = db.execute("SELECT name FROM manufacturer WHERE id = ?", (wmi_row[3],)).fetchone()
        vehicle_type = db.execute("SELECT name FROM vehicletype WHERE id = ?", (wmi_row[1],)).fetchone()
        values["27"] = manufacturer[0] if manufacturer else None
        values["39"] = vehicle_type[0] if vehicle_type else None
        meta = dict(db.execute("SELECT key, value FROM meta").fetchall())
    for element_id, name in WANTED.items():
        value = values.get(element_id)
        if value not in (None, "", "Not Applicable"):
            result[name] = value
    result.update({"valid": bool(result.get("make")), "model_year": best_year, "wmi": wmi, "database": meta.get("source")})
    if not result.get("model"):
        result["errors"].append("MODEL_NOT_DECODED")
    if not result["check_digit_ok"]:
        result["errors"].append("CHECK_DIGIT")  # North American VINs only; shown as a warning
    return result


def _number(text):
    try:
        return float(str(text).split(";")[0])
    except ValueError:
        return None
