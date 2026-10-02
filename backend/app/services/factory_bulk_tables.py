"""Conservative whole-table facts from cached US factory specification sheets.

The table is parsed once per immutable document. A fact is common only when every
factory trim column contains the same unqualified value. Engine-, drive-, body-
and option-dependent rows stay outside this pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from bs4 import BeautifulSoup

PARSER_VERSION = "factory-common-v2"
_SPACE = re.compile(r"\s+")
_QUALIFIER = re.compile(
    r"\b(?:estimated|est\.|approx\.?|optional|available|opt\.?|except|"
    r"depending|varies|with(?:out)? roof|fwd|awd|rwd)\b|[†‡*]",
    re.I,
)
_NUMBER = r"(?P<number>\d{1,5}(?:\.\d+)?)"
_INCH = re.compile(rf"^{_NUMBER}\s*(?:in\.?|inches?)$", re.I)
_MIXED_MM_INCH = re.compile(rf"^\d[\d,]*\s*mm\s*\({_NUMBER}\s*in\.\)$", re.I)
_GALLON = re.compile(rf"^{_NUMBER}\s*(?:gal\.?|gallons?)$", re.I)
_SEATS = re.compile(r"^(?P<number>[1-9]|[12]\d)\s*(?:passengers?|persons?)?$", re.I)
_OCTANE_MIN = re.compile(r"\b(?P<number>8[7-9]|9[0-3])\b.{0,20}\bor higher\b", re.I)


def clean(value: str) -> str:
    return _SPACE.sub(" ", value).strip()


@dataclass(frozen=True)
class TableRow:
    group: str
    label: str
    values: tuple[str, ...]
    footnoted: bool = False
    inherited: bool = False


@dataclass(frozen=True)
class FactoryTable:
    trims: tuple[str, ...]
    rows: tuple[TableRow, ...]


def _expanded_rows(table):
    """Expand actual HTML spans; an unfilled cell is never forward-filled."""
    spanning = {}
    for tr in table.select("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells:
            continue
        result = []
        footnotes = []
        inherited_used = False
        position = 0

        def inherited(result=result, footnotes=footnotes):
            nonlocal position, inherited_used
            while position in spanning:
                inherited_used = True
                remaining, value, note = spanning[position]
                result.append(value)
                footnotes.append(note)
                if remaining == 1:
                    del spanning[position]
                else:
                    spanning[position] = (remaining - 1, value, note)
                position += 1

        inherited()
        for cell in cells:
            inherited()
            value = clean(cell.get_text(" ", strip=True))
            note = bool(cell.find("sup"))
            try:
                colspan = int(cell.get("colspan", 1))
                rowspan = int(cell.get("rowspan", 1))
            except (TypeError, ValueError) as exc:
                raise ValueError("FACTORY_TABLE_INVALID_SPAN") from exc
            if not 1 <= colspan <= 100 or not 1 <= rowspan <= 100:
                raise ValueError("FACTORY_TABLE_INVALID_SPAN")
            for _ in range(colspan):
                result.append(value)
                footnotes.append(note)
                if rowspan > 1:
                    spanning[position] = (rowspan - 1, value, note)
                position += 1
        inherited()
        yield tr, cells, tuple(result), any(footnotes), inherited_used
    if spanning:
        raise ValueError("FACTORY_TABLE_DANGLING_ROWSPAN")


def parse_factory_table(content: bytes) -> FactoryTable:
    soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
    table = soup.select_one("table.specifications-table")
    if table is None:
        raise ValueError("FACTORY_TABLE_NOT_FOUND")
    trims = ()
    group = ""
    rows = []
    for tr, cells, values, footnoted, inherited in _expanded_rows(table):
        if "specifications-table__header" in tr.get("class", []):
            if len(values) < 2 or not all(values[1:]):
                raise ValueError("FACTORY_TABLE_INVALID_HEADER")
            trims = values[1:]
            continue
        if len(cells) == 1 and cells[0].get("colspan") is not None:
            group = values[0]
            continue
        if not trims:
            continue
        if len(values) != len(trims) + 1:
            raise ValueError("FACTORY_TABLE_COLUMN_DRIFT")
        if not values[0]:
            raise ValueError("FACTORY_TABLE_EMPTY_LABEL")
        rows.append(TableRow(group, values[0], values[1:], footnoted, inherited))
    if not trims or not rows:
        raise ValueError("FACTORY_TABLE_EMPTY")
    return FactoryTable(tuple(trims), tuple(rows))


def _field_for_row(row: TableRow):
    group, label = row.group.casefold(), row.label.casefold()
    if group == "engine" and label == "fuel tank capacity (gal.)":
        return "fuel_tank_us_gal", "US gal", _GALLON
    if group == "exterior dimensions":
        names = {
            "length (in.)": "length_in",
            "overall length (in.)": "length_in",
            "overall length mm/(in.)": "length_in",
            "width (in.)": "width_in",
            "overall width (in.)": "width_in",
            "overall width mm/(in.)": "width_in",
            "wheelbase (in.)": "wheelbase_in",
            "wheelbase mm/(in.)": "wheelbase_in",
            "overall height (in.)": "height_in",
            "height (in.)": "height_in",
        }
        if label in names:
            pattern = _MIXED_MM_INCH if "mm/(in.)" in label else _INCH
            return names[label], "in", pattern
    if group in {"interior dimensions", "general"} and label in {
        "seating capacity",
        "passenger seating capacity",
        "passenger capacity",
    }:
        return "seats", None, _SEATS
    return None


def _text_field_for_row(row: TableRow):
    group, label = row.group.casefold(), row.label.casefold()
    if group == "engine" and label in {
        "fuel injection",
        "fuel injection system",
        "fuel system",
    }:
        return "injection"
    if group in {"suspension", "chassis/suspension"}:
        if label in {"front suspension", "front"}:
            return "front_suspension"
        if label in {"rear suspension", "rear"}:
            return "rear_suspension"
    if group == "brakes":
        if label in {"front mm/(in.)", "front brakes"}:
            return "front_brakes"
        if label in {"rear mm/(in.)", "rear brakes"}:
            return "rear_brakes"
    if group in {"tires & wheels", "wheels/tires"}:
        if label in {"tire size", "tires"}:
            return "tires"
        if label in {"wheel size (in.)", "wheels"}:
            return "wheels"
    return None


def common_table_facts(table: FactoryTable):
    """Return only single-source, all-column invariants; conflicts are quarantined."""
    candidates = {}
    quarantined = []
    for row in table.rows:
        field = _field_for_row(row)
        if field is None:
            continue
        key, unit, pattern = field
        if row.footnoted or row.inherited or _QUALIFIER.search(row.label):
            quarantined.append({"field": key, "reason": "QUALIFIED_ROW", "row": row.label})
            continue
        parsed = []
        for raw in row.values:
            if not raw or _QUALIFIER.search(raw):
                break
            match = pattern.fullmatch(raw)
            if not match:
                break
            parsed.append(Decimal(match.group("number")))
        if len(parsed) != len(table.trims) or len(set(parsed)) != 1:
            quarantined.append(
                {
                    "field": key,
                    "reason": "MISSING_DIFFERENT_OR_CONDITIONAL_COLUMN",
                    "row": row.label,
                }
            )
            continue
        value = int(parsed[0]) if key == "seats" else float(parsed[0])
        previous = candidates.get(key)
        if previous and previous["value"] != value:
            quarantined.append(
                {"field": key, "reason": "CONFLICTING_DUPLICATE_ROW", "row": row.label}
            )
            candidates[key] = None
            continue
        if key not in candidates:
            candidates[key] = {
                "value": value,
                "unit": unit,
                "group": row.group,
                "row": row.label,
                "raw": row.values[0],
                "trims": table.trims,
            }
    for row in table.rows:
        key = _text_field_for_row(row)
        if not key:
            continue
        if row.footnoted or row.inherited or _QUALIFIER.search(row.label):
            quarantined.append({"field": key, "reason": "QUALIFIED_ROW", "row": row.label})
            continue
        values = [clean(v) for v in row.values]
        if (
            not all(values)
            or len(set(values)) != 1
            or any(_QUALIFIER.search(v) or " / " in v for v in values)
        ):
            quarantined.append(
                {
                    "field": key,
                    "reason": "MISSING_DIFFERENT_OR_CONDITIONAL_COLUMN",
                    "row": row.label,
                }
            )
            continue
        value = values[0]
        previous = candidates.get(key)
        if previous and previous["value"] != value:
            quarantined.append(
                {"field": key, "reason": "CONFLICTING_DUPLICATE_ROW", "row": row.label}
            )
            candidates[key] = None
            continue
        if key not in candidates:
            candidates[key] = {
                "value": value,
                "unit": None,
                "group": row.group,
                "row": row.label,
                "raw": value,
                "trims": table.trims,
            }
    for row in table.rows:
        if row.group.casefold() != "engine" or row.label.casefold() not in {
            "fuel requirement",
            "required fuel",
        }:
            continue
        key = "octane_aki"
        if row.footnoted or row.inherited or any(_QUALIFIER.search(v) for v in row.values):
            quarantined.append({"field": key, "reason": "QUALIFIED_ROW", "row": row.label})
            continue
        values = [_OCTANE_MIN.search(v) for v in row.values]
        if not all(values) or len({v.group("number") for v in values}) != 1:
            quarantined.append({"field": key, "reason": "OCTANE_MIN_UNCLEAR", "row": row.label})
            continue
        value = int(values[0].group("number"))
        previous = candidates.get(key)
        if previous and previous["value"] != value:
            quarantined.append(
                {"field": key, "reason": "CONFLICTING_DUPLICATE_ROW", "row": row.label}
            )
            candidates[key] = None
            continue
        if key not in candidates:
            candidates[key] = {
                "value": value,
                "unit": "AKI minimum",
                "group": row.group,
                "row": row.label,
                "raw": row.values[0],
                "trims": table.trims,
            }
    return {key: value for key, value in candidates.items() if value}, quarantined


common_numeric_facts = common_table_facts
