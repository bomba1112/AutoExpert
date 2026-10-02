"""Bounded extraction of selected LEMON HTML tables into *review candidates*.

The module has no network access and never assigns a row to a vehicle version.
The source URL, page hash, table/row locator, original cells and explicit spans
are kept so the existing publication review can assess applicability later.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

PARSER_VERSION = "lemon-selective-html-v1"
MAX_HTML_BYTES = 4_000_000
MAX_TABLES = 40
MAX_ROWS_PER_TABLE = 1000
MAX_COLUMNS = 32
ALLOWED_HOST = "lemon-manuals.la"

TARGET_TERMS = (
    "fluids",
    "common specs",
    "tire fitment",
    "specifications",
)
SKIP_TERMS = (
    "labor times",
    "trouble codes",
    "wiring diagram",
    "bundle",
    "download",
    "single page",
)
FLUID_HEADER_ALIASES = {
    "fluid type": "component",
    "fluid": "component",
    "application": "application",
    "operation": "operation",
    "standard": "standard",
    "metric": "metric",
    "fluid spec": "specification",
    "fluid specification": "specification",
    "note": "note",
    "s/h": "source_marker",
}
FLUID_COMPONENTS = {
    "engine oil": "ENGINE_OIL",
    "automatic transmission fluid": "AUTOMATIC_TRANSMISSION_FLUID",
    "manual transmission fluid": "MANUAL_TRANSMISSION_FLUID",
    "engine coolant": "ENGINE_COOLANT",
    "brake fluid": "BRAKE_FLUID",
    "fuel tank": "FUEL_TANK",
}


def _clean(value: str) -> str:
    return " ".join(value.split())


def _source_url_allowed(url: str) -> bool:
    parts = urlsplit(url)
    try:
        port = parts.port
    except ValueError:
        return False
    path = unquote(parts.path).casefold()
    return (
        parts.scheme == "https"
        and parts.hostname == ALLOWED_HOST
        and port is None
        and not parts.username
        and not parts.password
        and not parts.query
        and not parts.fragment
        and parts.path.startswith("/")
        and ".." not in path
        and "\\" not in path
    )


def _safe_span(value: object) -> int:
    try:
        number = int(str(value or "1"))
    except ValueError as exc:
        raise ValueError("INVALID_TABLE_SPAN") from exc
    if not 1 <= number <= MAX_COLUMNS:
        raise ValueError("TABLE_SPAN_LIMIT")
    return number


@dataclass(frozen=True)
class GridCell:
    text: str
    origin_row: int
    origin_col: int
    header: bool
    explicit_span: bool

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "origin_row": self.origin_row,
            "origin_col": self.origin_col,
            "header": self.header,
            "explicit_span": self.explicit_span,
        }


def _table_rows(table: Tag) -> list[Tag]:
    return [tr for tr in table.find_all("tr") if tr.find_parent("table") is table]


def expand_table(table: Tag) -> list[list[GridCell | None]]:
    """Expand explicit HTML row/column spans; never fill genuinely empty cells."""
    rows = _table_rows(table)
    if len(rows) > MAX_ROWS_PER_TABLE:
        raise ValueError("TABLE_ROW_LIMIT")
    grid: list[list[GridCell | None]] = []
    # Column -> (remaining rows, source cell). A carry is an explicit rowspan.
    carried: dict[int, tuple[int, GridCell]] = {}
    for row_index, tr in enumerate(rows):
        row: list[GridCell | None] = [None] * MAX_COLUMNS
        for column, (remaining, cell) in list(carried.items()):
            row[column] = cell
            if remaining <= 1:
                del carried[column]
            else:
                carried[column] = (remaining - 1, cell)
        column = 0
        for td in tr.find_all(["td", "th"], recursive=False):
            while column < MAX_COLUMNS and row[column] is not None:
                column += 1
            width, height = _safe_span(td.get("colspan")), _safe_span(td.get("rowspan"))
            if column + width > MAX_COLUMNS:
                raise ValueError("TABLE_COLUMN_LIMIT")
            if any(row[col] is not None for col in range(column, column + width)):
                raise ValueError("OVERLAPPING_TABLE_SPAN")
            cell = GridCell(
                text=_clean(td.get_text(" ", strip=True)),
                origin_row=row_index,
                origin_col=column,
                header=td.name == "th",
                explicit_span=width > 1 or height > 1,
            )
            for col in range(column, column + width):
                row[col] = cell
                if height > 1:
                    carried[col] = (height - 1, cell)
            column += width
        occupied = [i for i, value in enumerate(row) if value is not None]
        grid.append(row[: max(occupied) + 1] if occupied else [])
    width = max(map(len, grid), default=0)
    return [row + [None] * (width - len(row)) for row in grid]


def _section_path(table: Tag) -> list[str]:
    headings = []
    for node in table.find_all_previous(["h1", "h2", "h3"], limit=6):
        text = _clean(node.get_text(" ", strip=True))
        if text and text not in headings:
            headings.append(text)
    return list(reversed(headings))


def _notes(table: Tag) -> list[str]:
    notes = []
    tfoot = table.find("tfoot")
    if tfoot:
        notes.append(_clean(tfoot.get_text(" ", strip=True)))
    for next_node in table.find_next_siblings(limit=3):
        if next_node.name in {"table", "h1", "h2", "h3"}:
            break
        if next_node.name in {"p", "ul", "ol", "div"}:
            text = _clean(next_node.get_text(" ", strip=True))
            if text and re.search(r"(?i)^(?:notes?|\*|†|‡|important)\b|^[*†‡]", text):
                notes.append(text[:1000])
    return notes


def _manual_relationship(soup: BeautifulSoup) -> dict | None:
    """Keep site-declared sharing and exceptions without expanding applicability."""
    for node in soup.find_all(["p", "div"]):
        own_text = _clean(node.get_text(" ", strip=True))
        if "manual is identical to the manual for" not in own_text.casefold():
            continue
        variants = []
        list_node = node.find_next_sibling(["ul", "ol"])
        if list_node:
            variants = [_clean(li.get_text(" ", strip=True)) for li in list_node.find_all("li")]
        exceptions = []
        for field in ("labor times", "fluids", "tire fitment"):
            if field in own_text.casefold():
                exceptions.append(field)
        return {
            "source_statement": own_text[:1000],
            "variants_named": variants[:100],
            "exception_sections": exceptions,
            "application": "REVIEW_REQUIRED",
        }
    return None


def _capacity(value: str | None) -> dict | None:
    if not value:
        return None
    match = re.fullmatch(
        r"(?i)\s*(\d+(?:\.\d+)?)\s*(US\s*QTS?\.?|QTS?\.?|L|LITERS?|US\s*GALS?\.?|GALS?\.?)\s*",
        value,
    )
    if not match:
        return None
    token = match.group(2).casefold().replace(" ", "").rstrip(".")
    unit = {
        "usqt": "US_QUART",
        "usqts": "US_QUART",
        "qt": "QUART_UNSPECIFIED",
        "qts": "QUART_UNSPECIFIED",
        "l": "LITRE",
        "liter": "LITRE",
        "liters": "LITRE",
        "usgal": "US_GALLON",
        "usgals": "US_GALLON",
        "gal": "GALLON_UNSPECIFIED",
        "gals": "GALLON_UNSPECIFIED",
    }[token]
    return {"value": match.group(1), "unit": unit, "original": value}


def _fluid_normalized(values: dict) -> dict:
    operation = (values.get("operation") or "").casefold()
    if "drain" in operation and "refill" in operation and "filter" in operation:
        capacity_type = "SERVICE_WITH_FILTER"
    elif "dry" in operation and "fill" in operation:
        capacity_type = "DRY_FILL"
    else:
        capacity_type = "UNSPECIFIED"
    return {
        "component": FLUID_COMPONENTS.get((values.get("component") or "").casefold()),
        "standard_capacity": _capacity(values.get("standard")),
        "metric_capacity": _capacity(values.get("metric")),
        "capacity_type": capacity_type,
        "specification_text": values.get("specification"),
    }


def _fluid_candidates(grid: list[list[GridCell | None]], locator: str) -> list[dict]:
    candidates = []
    for header_index, row in enumerate(grid[: min(5, len(grid))]):
        fields = [
            FLUID_HEADER_ALIASES.get((cell.text if cell else "").strip().casefold()) for cell in row
        ]
        if "component" not in fields or "specification" not in fields:
            continue
        for row_index in range(header_index + 1, len(grid)):
            current = grid[row_index]
            if all(cell is None or not cell.text for cell in current):
                continue
            if all(cell is not None and cell.header for cell in current):
                continue
            values = {}
            for col, name in enumerate(fields):
                if name and col < len(current):
                    cell = current[col]
                    values[name] = cell.text if cell else None
            component = values.get("component")
            if not component:
                # No silent carry into an empty component cell.
                continue
            candidates.append(
                {
                    "kind": "FLUID_ROW_CANDIDATE",
                    "locator": f"{locator}:row-{row_index + 1}",
                    "raw_fields": values,
                    "normalized": _fluid_normalized(values),
                    "explicit_conditions": [
                        value
                        for key in ("application", "operation", "note")
                        if (value := values.get(key))
                    ],
                    "applicability": "UNRESOLVED",
                    "publication": "REVIEW_REQUIRED",
                }
            )
        break
    return candidates


def parse_page(content: bytes, *, source_url: str, retrieved_at: str) -> dict:
    """Parse one selected page; returns source-specific rows, never published facts."""
    if not content or len(content) > MAX_HTML_BYTES:
        raise ValueError("HTML_SIZE_LIMIT")
    if not _source_url_allowed(source_url):
        raise ValueError("LEMON_SOURCE_URL_REQUIRED")
    soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
    if not soup.find("html"):
        raise ValueError("HTML_DOCUMENT_REQUIRED")
    text_start = _clean(soup.get_text(" ", strip=True)[:3000]).casefold()
    if any(token in text_start for token in ("verify you are human", "captcha", "cf-chl-")):
        raise ValueError("ACCESS_CHALLENGE")
    tables = soup.find_all("table")
    if len(tables) > MAX_TABLES:
        raise ValueError("TABLE_COUNT_LIMIT")
    digest = hashlib.sha256(content).hexdigest()
    result = {
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "sha256": digest,
        "parser_version": PARSER_VERSION,
        "title": _clean(soup.title.get_text(" ", strip=True)) if soup.title else None,
        "headings": [_clean(h.get_text(" ", strip=True)) for h in soup.find_all(["h1", "h2"])][:20],
        "manual_relationship": _manual_relationship(soup),
        "tables": [],
        "candidates": [],
        "publication": "REVIEW_REQUIRED",
    }
    for index, table in enumerate(tables, start=1):
        locator = f"table-{index}"
        grid = expand_table(table)
        section = _section_path(table)
        record = {
            "locator": locator,
            "section_path": section,
            "caption": _clean(table.caption.get_text(" ", strip=True)) if table.caption else None,
            "notes": _notes(table),
            "grid": [[cell.as_dict() if cell else None for cell in row] for row in grid],
        }
        result["tables"].append(record)
        if "fluid" in " ".join(section + [record["caption"] or ""]).casefold():
            result["candidates"].extend(_fluid_candidates(grid, locator))
    return result


def discover_child_links(content: bytes, *, page_url: str, max_links: int = 100) -> list[dict]:
    """Extract actual same-host child links; this function never follows them."""
    if not 0 < max_links <= 500 or len(content) > MAX_HTML_BYTES:
        raise ValueError("LINK_DISCOVERY_LIMIT")
    if not _source_url_allowed(page_url):
        raise ValueError("LEMON_SOURCE_URL_REQUIRED")
    base = urlsplit(page_url)
    soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
    result, seen = [], set()
    for a in soup.find_all("a", href=True):
        url = urljoin(page_url, a["href"])
        target = urlsplit(url)
        path = unquote(target.path).casefold()
        if (
            not _source_url_allowed(url)
            or not target.path.startswith(base.path)
            or url == page_url
            or any(token in path for token in SKIP_TERMS)
            or any(path.endswith(ext) for ext in (".zip", ".torrent", ".pdf", ".png", ".jpg"))
        ):
            continue
        if url in seen:
            continue
        seen.add(url)
        result.append({"url": url, "source_label": _clean(a.get_text(" ", strip=True))})
        if len(result) == max_links:
            break
    return result


def is_target_section(url: str) -> bool:
    """Restrict fetch candidates to technical subsections actually discovered."""
    parts = urlsplit(url)
    path = unquote(parts.path).casefold()
    return (
        _source_url_allowed(url)
        and "/repair and diagnosis/" in path
        and any(term in path for term in TARGET_TERMS)
        and not any(term in path for term in SKIP_TERMS)
    )
