"""Conservative Kia US specification-table adapter; no catalog expansion or network."""

import re
from decimal import Decimal

from bs4 import BeautifulSoup


def clean(value):
    return re.sub(r"\s+", " ", value).strip()


def columns(content):
    soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
    table = soup.select_one("table.specifications-table")
    if table is None:
        raise ValueError("FACTORY_TABLE_NOT_FOUND")
    result, group = [], ""
    for row in table.select("tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        values = [clean(c.get_text(" ", strip=True)) for c in cells]
        if "specifications-table__header" in row.get("class", []):
            result = [{"trim": v, "rows": []} for v in values[1:]]
            continue
        if len(cells) == 1:
            group = values[0]
            continue
        if not result or not cells:
            continue
        expanded = []
        for cell in cells[1:]:
            expanded.extend([clean(cell.get_text(" ", strip=True))] * int(cell.get("colspan", 1)))
        if len(expanded) != len(result):
            raise ValueError("FACTORY_TABLE_COLUMN_DRIFT")
        for column, value in zip(result, expanded, strict=True):
            if value and value not in {"-", "--", "TBD", "N/A"}:
                column["rows"].append((group, values[0], value))
    if not result:
        raise ValueError("FACTORY_TABLE_EMPTY")
    return result


def engine_type(column):
    return next(
        (v for g, k, v in column["rows"] if g.lower() == "engine" and k.lower() == "type"), None
    )


def displacement(column):
    text = next((v for _, k, v in column["rows"] if "displacement" in k.lower()), None)
    if text:
        match = re.search(r"[\d,.]+", text)
        if match:
            return Decimal(match[0].replace(",", "")) / 1000
    return None


def transmission(column):
    found = set()
    for group, key, value in column["rows"]:
        if key.lower() in {"first", "1st"} and re.search(
            r"\d[ -]*speed.*transmission", group, re.I
        ):
            found.add(re.sub(r"^Transmission Gear Ratios:\s*", "", group, flags=re.I))
        if key.lower() == "transmission type":
            found.add(value)
    return next(iter(found)) if len(found) == 1 else None


def matched_columns(catalog, choices):
    facts = catalog["facts"]
    litre = facts.get("engine_displacement", {}).get("value")
    if litre is None:
        return []  # EV battery/motor variants need their own confirmed matching keys.
    aspiration = facts.get("aspiration", {}).get("value")
    result = []
    for col in choices:
        size = displacement(col)
        if size is None or size.quantize(Decimal("0.1")) != Decimal(str(litre)).quantize(
            Decimal("0.1")
        ):
            continue
        engine = engine_type(col) or ""
        turbo = "turbo" in engine.lower() or "t-gdi" in engine.lower()
        if aspiration == "TURBO" and not turbo:
            continue
        if aspiration == "NATURALLY_ASPIRATED" and turbo:
            continue
        result.append(col)
    return result


def common_facts(matches):
    """Ambiguous trim sets can contribute only facts identical across every candidate."""
    result = {}
    for key, getter in (
        ("engine_description", engine_type),
        ("transmission_description", transmission),
    ):
        values = {getter(col) for col in matches}
        if len(values) == 1 and None not in values:
            result[key] = next(iter(values))
    return result
