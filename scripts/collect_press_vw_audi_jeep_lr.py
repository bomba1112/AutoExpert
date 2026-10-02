"""Collect the US press "specifications" documents of the Volkswagen, Audi, Jeep and Land Rover lines.

Hosts (US newsrooms only, see data_work/_shared/press/FORMAT.md):
  media.vw.com          Volkswagen of America media site. Client-rendered Nuxt app; its pages load
                        JSON from https://media.vw.com/api (calls read from the site's JS bundle):
                        /api/models (model tree), /api/models/<slug> (model page: documents and
                        current press kit), /api/press-kits/<slug> (press kit: attached documents
                        and "siblingsAndSelf" = the press kits of all model years of that model).
                        Spec sheets are PDF documents titled "... Technical Specifications" /
                        "... Specifications" / "... Tech Specs" attached to the yearly press kits
                        (and, for line-years still missing, to press releases of the model page:
                        /api/models/<slug>/releases, /api/releases/<id>/sidebar-content).
                        Where a line-year has no spec-titled document, the press kit PDF of that
                        year is used (Audi 2014-2020 kits end with the technical specifications).
  media.audiusa.com     Audi of America media site, same platform and API as media.vw.com.
  media.stellantisnorthamerica.com
                        Stellantis (FCA US) media site. Its robots.txt disallows "/" for the AI
                        agents ClaudeBot, Claude-Web and anthropic-ai. This collector is run by an
                        Anthropic AI agent, so the host is not crawled: robots.txt is stored and
                        one manifest row with status=blocked records the reason.
  media.jlr.com         JLR media site (linked as the press office from jlr.com); its "North America
                        (English)" edition is the locale /en-us. The Land Rover lines are under the
                        brand sections /range-rover and /discovery: pages /<brand>/en-us/tech-specs
                        and /<brand>/en-us/press-kit list documents per vehicle and model year; each
                        download is a zip archive on the CDN media.production.jlrms.com holding the
                        PDF (2014/2015: Word .doc/.docx). Used: all US/North-America tech-spec items
                        and press kits titled as specs (every PDF/Word member), and from the other
                        in-scope press kits the members whose file name names spec/tech.
                        Canadian-only items are skipped.

For every line of make volkswagen/audi/jeep/land-rover in scripts/us_tech_lines.py and every
model year 2014-2026 within Line.years the collector lists the spec documents found, downloads
them and stores their page text. Line-years without a spec document get one row with
status=not_found whose url is the model page on the site with "#<year>".

Files (FORMAT.md):
  data_work/_shared/manifest_press/<host>.csv          manifest (resumable: ok URLs are reused)
  RAW_ROOT/press/<host>/<document>.pdf                  spec PDFs as published (zip members for JLR)
  RAW_ROOT/press/<host>/api/<name>.json.gz              API answers / listing pages used for discovery
  RAW_ROOT/press/<host>/robots.txt.gz                   robots.txt as fetched
  RAW_ROOT/pagetext/<sha256>.json.gz                    {"sha256","file","pages":[text per PDF page]}
Manifest doc_type: press_specifications (spec documents), press_index (discovery answers),
robots (robots.txt). For JLR the manifest url of a document is the zip URL; when one zip holds
several PDFs the member name is appended as "#<member>".

Run (pdfplumber is needed for the page text):
  uv run --no-project --with httpx --with beautifulsoup4 --with pdfplumber --with pypdfium2 --with olefile \
      python scripts/collect_press_vw_audi_jeep_lr.py [--host media.vw.com ...] [--refresh-index] [--dry-run]
"""

from __future__ import annotations

import argparse
import bisect
import gzip
import io
import json
import re
import struct
import sys
import urllib.robotparser
import zipfile
from xml.etree import ElementTree
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import (  # noqa: E402
    RAW_ROOT,
    WORK,
    Blocked,
    Fetcher,
    Manifest,
    now,
    read_maybe_gz,
    sha256,
    write_gz,
)
from us_tech_lines import LINES  # noqa: E402

FIELDS = [
    "make", "line", "year", "doc_type", "title", "url", "http_status", "bytes", "sha256",
    "retrieved_at", "path", "status", "note",
]
MANIFEST_DIR = WORK / "_shared" / "manifest_press"
YEARS = (2014, 2026)
# Product tokens of Anthropic agents; a robots.txt group that disallows one of them applies here.
AI_AGENT_TOKENS = ("ClaudeBot", "Claude-User", "Claude-Web", "anthropic-ai")

VW = "media.vw.com"
AUDI = "media.audiusa.com"
STLA = "media.stellantisnorthamerica.com"
JLR = "media.jlr.com"
JLR_CDN = "media.production.jlrms.com"
HOST_MAKE = {VW: "volkswagen", AUDI: "audi", STLA: "jeep", JLR: "land-rover"}
ALL_HOSTS = [VW, AUDI, STLA, JLR]

# Newspress (VW/Audi) model-page slugs (from /api/models) -> registry line.
NEWSPRESS_SLUGS = {
    VW: {
        "jetta": "volkswagen/jetta", "jetta-gli": "volkswagen/jetta", "jetta-sportwagen": "volkswagen/jetta",
        "passat": "volkswagen/passat",
        "tiguan": "volkswagen/tiguan", "tiguan-limited": "volkswagen/tiguan",
        "atlas": "volkswagen/atlas",
        "arteon": "volkswagen/arteon",
        "touareg": "volkswagen/touareg",
    },
    AUDI: {
        "A3": "audi/a3", "a3s3-sedan": "audi/a3", "A3-Sedan": "audi/a3", "S3-Sedan": "audi/a3",
        "a3-cabriolet": "audi/a3", "rs-3": "audi/a3",
        "A4": "audi/a4", "a4s4": "audi/a4", "a-4": "audi/a4", "s4": "audi/a4", "A4-allroad": "audi/a4",
        "A5": "audi/a5", "a5s5": "audi/a5", "a5-sedan": "audi/a5", "s5-sedan": "audi/a5",
        "a5-previous-models": "audi/a5", "a5-s5-coupe": "audi/a5", "A5-Coupe": "audi/a5",
        "S5-Coupe": "audi/a5", "a5s5-sportback": "audi/a5", "A5-Sportback": "audi/a5",
        "S5-Sportback": "audi/a5", "a5s5-cabriolet": "audi/a5", "A5-Cabriolet": "audi/a5",
        "S5-Cabriolet": "audi/a5", "rs-5-coupe": "audi/a5", "rs-5-sportback": "audi/a5",
        "A6-main": "audi/a6", "A6": "audi/a6", "a6-allroad": "audi/a6", "rs-6-avant": "audi/a6", "s6": "audi/a6",
        "q3-main": "audi/q3", "q3": "audi/q3",
        "q5-main": "audi/q5", "q5sq5": "audi/q5", "q5": "audi/q5", "SQ5": "audi/q5",
        "q5sq5-sportback": "audi/q5", "q5-sportback": "audi/q5", "sq5-sportback": "audi/q5",
        "q7-main": "audi/q7", "q7-sq7": "audi/q7", "q7": "audi/q7", "sq7": "audi/q7",
    },
}
# Model names in document titles -> registry line (a title naming one of these belongs to it).
TITLE_LINES = {
    VW: [
        ("volkswagen/jetta", r"\b(Jetta|GLI)\b"),
        ("volkswagen/passat", r"\bPassat\b"),
        ("volkswagen/tiguan", r"\bTiguan\b"),
        ("volkswagen/atlas", r"\bAtlas\b(?!\s*Cross)"),
        ("volkswagen/arteon", r"\bArteon\b"),
        ("volkswagen/touareg", r"\bTouareg\b"),
    ],
    AUDI: [
        ("audi/a3", r"\b(A3|S3|RS ?3)\b"),
        ("audi/a4", r"\b(A4|S4)\b|^(?!.*\bA6\b).*\ballroad\b"),
        ("audi/a5", r"\b(A5|S5|RS ?5)\b"),
        ("audi/a6", r"\b(A6|S6|RS ?6)\b"),
        ("audi/q3", r"\bQ3\b"),
        ("audi/q5", r"\bS?Q5\b"),
        ("audi/q7", r"\bS?Q7\b"),
    ],
}
# Titles of models that share a page tree with a line but are not that line.
TITLE_EXCLUDE = {
    VW: r"(?i)\bCross Sport\b|\bGolf\b|\bID\.",
    AUDI: r"(?i)\be-tron\b",
}
SPEC_TITLE = re.compile(r"(?i)\b(tech(nical)?\s*spec\w*|spec(s|ifications?|\s*sheet)|technical\s+data)\b")
NOT_SPEC_TITLE = re.compile(r"(?i)\b(pricing|price list|at[- ]a[- ]glance)\b")
# press kit PDFs (Audi 2014-2020 publish no separate spec sheet; the kit ends with the technical
# specifications) are used only for line-years without a spec-titled document
PRESS_KIT_TITLE = re.compile(r"(?i)\b(press|media)\s*kit\b")

# media.jlr.com: listing pages (North America edition) and title -> line rules.
JLR_PAGES = [
    ("/range-rover/en-us/tech-specs", "tech-specs"),
    ("/discovery/en-us/tech-specs", "tech-specs"),
    ("/range-rover/en-us/press-kit", "press-kit"),
    ("/discovery/en-us/press-kit", "press-kit"),
]
JLR_TITLE_LINES = [
    ("land-rover/discovery-sport", r"(?i)\bDiscovery Sport\b|\bLR2\b"),
    ("land-rover/range-rover-evoque", r"(?i)\bEvoque\b"),
    ("land-rover/range-rover-sport", r"(?i)\bRange Rover Sport\b"),
    ("land-rover/range-rover", r"(?i)\bRange Rover\b(?!\s+(Sport|Evoque|Velar))"),
]
JLR_SECTION_LINES = {
    "Range Rover (2012-2021)": "land-rover/range-rover",
    "Range Rover": "land-rover/range-rover",
    "Range Rover Sport (2013-2022)": "land-rover/range-rover-sport",
    "Range Rover Sport": "land-rover/range-rover-sport",
    "Range Rover Evoque": "land-rover/range-rover-evoque",
    "Range Rover Evoque (2010-2018)": "land-rover/range-rover-evoque",
    "Discovery Sport": "land-rover/discovery-sport",
}
# press kits whose title names specs ("(US Specs)", "TECHNICAL PRESS KIT") are used whole; other
# press-kit zips only for PDF/Word members whose file name names specifications / technical data
JLR_TITLE_SPEC = re.compile(r"(?i)\bspecs?\b|\btechnical\b")
JLR_MEMBER_SPEC = re.compile(r"(?i)spec|tech")
JLR_CANADA_ONLY = re.compile(r"(?i)\bcanad(a|ian)\b")
JLR_US = re.compile(r"(?i)\bUS\b")
# model pages used as the "not found" anchor per line
JLR_LINE_PAGES = {
    "land-rover/range-rover": "/range-rover/en-us/vehicle/range-rover",
    "land-rover/range-rover-sport": "/range-rover/en-us/vehicle/range-rover-sport",
    "land-rover/range-rover-evoque": "/range-rover/en-us/vehicle/range-rover-evoque",
    "land-rover/discovery-sport": "/discovery/en-us/vehicle/discovery-sport",
}


def log(message: str) -> None:
    print(message, flush=True)


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")


def title_year(text: str) -> int | None:
    match = re.search(r"\b(20[0-3]\d)\b", text or "")
    if match:
        return int(match.group(1))
    match = re.search(r"(?i)\bMY ?(\d{2})\b", text or "")
    return 2000 + int(match.group(1)) if match else None


def pdf_pages(body: bytes) -> list[str]:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(body)) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def store_pagetext(digest: str, file: str, pages: list[str], extra: dict | None = None) -> None:
    target = RAW_ROOT / "pagetext" / f"{digest}.json.gz"
    if target.exists():
        with gzip.open(target, "rt", encoding="utf-8") as handle:
            existing = json.load(handle)
        if existing.get("file") != file:
            log(f"  pagetext {digest[:12]} already stored for {existing.get('file')}; kept")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(target, "wt", encoding="utf-8") as handle:
        json.dump({"sha256": digest, "file": file, "pages": pages, **(extra or {})}, handle)


def member_wanted(name: str, member_filter: re.Pattern | None) -> bool:
    """Zip member to keep: a PDF or Word document (matching the filter for press kits)."""
    if name.startswith("__MACOSX") or not name.lower().endswith((".pdf", ".doc", ".docx")):
        return False
    return member_filter is None or bool(member_filter.search(Path(name).name))


# ---- Word documents (JLR zips of 2015 hold .doc/.docx spec sheets) -------------------------------
_SPRM_SIZE = {0: 1, 1: 1, 2: 2, 3: 4, 4: 2, 5: 2, 7: 3}


def _prls(grpprl: bytes) -> dict[int, bytes]:
    out: dict[int, bytes] = {}
    pos = 0
    while pos + 2 <= len(grpprl):
        sprm = struct.unpack_from("<H", grpprl, pos)[0]
        pos += 2
        spra = sprm >> 13
        if spra == 6:
            if sprm == 0xD608:  # sprmTDefTable: 2-byte size
                size = struct.unpack_from("<H", grpprl, pos)[0] - 1
                pos += 2
            elif sprm == 0xC615 and pos < len(grpprl) and grpprl[pos] == 255:  # sprmPChgTabs, long form
                del_count = grpprl[pos + 1]
                add_count = grpprl[pos + 2 + 4 * del_count]
                size = 1 + 1 + 4 * del_count + 1 + 3 * add_count
                out[sprm] = grpprl[pos:pos + size]
                pos += size
                continue
            else:
                size = grpprl[pos] if pos < len(grpprl) else 0
                pos += 1
        else:
            size = _SPRM_SIZE[spra]
        out[sprm] = grpprl[pos:pos + size]
        pos += size
    return out


def doc_rows(data: bytes) -> list[list[str]]:
    import olefile

    ole = olefile.OleFileIO(io.BytesIO(data))
    word = ole.openstream("WordDocument").read()
    flags = struct.unpack_from("<H", word, 0x000A)[0]
    table = ole.openstream("1Table" if flags & 0x0200 else "0Table").read()

    # piece table -> text and the stream offset (FC) of every character
    fc_clx, lcb_clx = struct.unpack_from("<II", word, 0x01A2)
    clx = table[fc_clx:fc_clx + lcb_clx]
    pos = 0
    while pos < len(clx) and clx[pos] == 0x01:
        pos += 3 + struct.unpack_from("<H", clx, pos + 1)[0]
    if pos >= len(clx) or clx[pos] != 0x02:
        raise ValueError("no piece table")
    lcb = struct.unpack_from("<I", clx, pos + 1)[0]
    plc = clx[pos + 5:pos + 5 + lcb]
    n = (lcb - 4) // 12
    cps = struct.unpack_from(f"<{n + 1}I", plc, 0)
    chars: list[str] = []
    fcs: list[int] = []
    for i in range(n):
        fc = struct.unpack_from("<I", plc, 4 * (n + 1) + 8 * i + 2)[0]
        count = cps[i + 1] - cps[i]
        if fc & 0x40000000:
            start = (fc & ~0x40000000) // 2
            text = word[start:start + count].decode("cp1252", errors="replace")
            fcs.extend(start + k for k in range(len(text)))
        else:
            text = word[fc:fc + 2 * count].decode("utf-16-le", errors="replace")
            fcs.extend(fc + 2 * k for k in range(len(text)))
        chars.extend(text)

    # paragraph properties: FC ranges -> (in table, table-row end)
    fc_bte, lcb_bte = struct.unpack_from("<II", word, 0x0102)
    bte = table[fc_bte:fc_bte + lcb_bte]
    nb = (lcb_bte - 4) // 8
    runs: list[tuple[int, int, bool, bool]] = []
    for i in range(nb):
        pn = struct.unpack_from("<I", bte, 4 * (nb + 1) + 4 * i)[0] & 0x3FFFFF
        fkp = word[pn * 512:(pn + 1) * 512]
        crun = fkp[511]
        rgfc = struct.unpack_from(f"<{crun + 1}I", fkp, 0)
        for j in range(crun):
            b_offset = fkp[4 * (crun + 1) + 13 * j]
            in_table = ttp = False
            if b_offset:
                at = 2 * b_offset
                cb = fkp[at]
                if cb == 0:
                    cb2 = fkp[at + 1]
                    grp = fkp[at + 2:at + 2 + 2 * cb2]
                else:
                    grp = fkp[at + 1:at + 1 + 2 * cb - 1]
                props = _prls(grp[2:])
                in_table = bool(props.get(0x2416, b"\x00")[:1] != b"\x00") or bool(
                    props.get(0x6649, b"\x00\x00\x00\x00") != b"\x00\x00\x00\x00")
                ttp = bool(props.get(0x2417, b"\x00")[:1] != b"\x00") or bool(
                    props.get(0x244C, b"\x00")[:1] != b"\x00")
            runs.append((rgfc[j], rgfc[j + 1], in_table, ttp))
    runs.sort()
    starts = [r[0] for r in runs]

    def props_at(fc: int) -> tuple[bool, bool]:
        k = bisect.bisect_right(starts, fc) - 1
        if 0 <= k < len(runs) and runs[k][0] <= fc < runs[k][1]:
            return runs[k][2], runs[k][3]
        return False, False

    text = "".join(chars)
    # drop field codes (\x13 code \x14 result \x15 -> result)
    keep = [True] * len(text)
    depth_code = []
    for k, ch in enumerate(text):
        if ch == "\x13":
            depth_code.append(True)
            keep[k] = False
        elif ch == "\x14":
            if depth_code:
                depth_code[-1] = False
            keep[k] = False
        elif ch == "\x15":
            if depth_code:
                depth_code.pop()
            keep[k] = False
        elif depth_code and depth_code[-1]:
            keep[k] = False

    rows: list[list[str]] = []
    cells: list[str] = []
    cell_paras: list[str] = []
    para: list[str] = []
    for k, ch in enumerate(text):
        if not keep[k]:
            continue
        if ch in "\r\x07":
            in_table, ttp = props_at(fcs[k])
            line = _clean("".join(para))
            para = []
            if ch == "\x07" and ttp:
                rows.append(cells)
                cells, cell_paras = [], []
            elif ch == "\x07":
                cell_paras.append(line)
                cells.append("\n".join(p for p in cell_paras if p))
                cell_paras = []
            elif in_table:
                cell_paras.append(line)
            elif line:
                rows.append([line])
            continue
        para.append(ch)
    if cells:
        rows.append(cells)
    return rows


def docx_rows(data: bytes) -> list[list[str]]:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    root = ElementTree.fromstring(zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml"))
    body = root.find("w:body", ns)
    rows: list[list[str]] = []

    def para_text(p) -> str:
        parts = []
        for node in p.iter():
            tag = node.tag.split("}")[1]
            if tag == "t" and node.text:
                parts.append(node.text)
            elif tag in ("tab",):
                parts.append(" ")
            elif tag in ("br", "cr"):
                parts.append("\n")
        return _clean("".join(parts))

    def walk(node) -> None:
        for child in node:
            tag = child.tag.split("}")[1]
            if tag == "p":
                line = para_text(child)
                if line:
                    rows.append([line])
            elif tag == "tbl":
                for tr in child.findall("w:tr", ns):
                    cells = []
                    for tc in tr.findall("w:tc", ns):
                        cells.append("\n".join(t for t in (para_text(p) for p in tc.iter(
                            "{%s}p" % ns["w"])) if t))
                    rows.append(cells)
            elif tag == "sdt":
                content = child.find("w:sdtContent", ns)
                if content is not None:
                    walk(content)

    walk(body)
    return rows


def _clean(text: str) -> str:
    text = text.replace("\x0b", "\n").replace("\x0c", "\n").replace("\xa0", " ").replace("\x1e", "-")
    text = re.sub(r"[\x00-\x08\x0e-\x1f]", "", text)
    return "\n".join(re.sub(r"[ \t]+", " ", part).strip() for part in text.split("\n")).strip()


def rows_text(rows: list[list[str]]) -> str:
    """Plain text of the rows: cells separated by a tab, cell-internal line breaks as spaces."""
    return "\n".join("\t".join(cell.replace("\n", " ") for cell in row) for row in rows)


class Robots:
    """robots.txt of one host (RFC 9309: a 4xx answer means no rules)."""

    def __init__(self, fetcher: Fetcher, base: str):
        self.base = base
        self.parser = urllib.robotparser.RobotFileParser()
        self.status: int | str = ""
        self.body = b""
        try:
            response = fetcher.get(f"{base}/robots.txt")
        except Blocked as exc:
            response = None
            self.status = f"blocked: {exc}"
        if response is not None:
            self.status = response.status_code
            self.body = response.content
            lines = self.body.decode("utf-8", errors="replace").splitlines() if response.status_code == 200 else []
            self.parser.parse(lines)
        else:
            self.parser.parse([])

    def denied_agents(self) -> list[str]:
        return [token for token in AI_AGENT_TOKENS if not self.parser.can_fetch(token, f"{self.base}/")]

    def allowed(self, url: str, ua: str) -> bool:
        return self.parser.can_fetch(ua, url) and all(
            self.parser.can_fetch(token, url) for token in AI_AGENT_TOKENS
        )


class Host:
    def __init__(self, host: str, refresh_index: bool):
        self.host = host
        self.make = HOST_MAKE[host]
        self.base = f"https://{host}"
        self.manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)
        self.fetcher = Fetcher()
        self.refresh_index = refresh_index
        self.lines = {line.key: line for line in LINES if line.make == self.make}
        self.robots: Robots | None = None
        self.cdn: dict[str, tuple[Fetcher, Robots]] = {}
        self.downloaded = 0
        self.failed = 0
        self.dry_run = False

    # ---- robots -----------------------------------------------------------------------------
    def check_robots(self) -> str | None:
        """Fetch robots.txt (always), store it, return a block reason or None."""
        robots = Robots(self.fetcher, self.base)
        self.robots = robots
        rel = Path("press") / self.host / "robots.txt.gz"
        if robots.body:
            write_gz(RAW_ROOT / rel, robots.body)
        denied = robots.denied_agents()
        reason = None
        if denied:
            reason = ("robots.txt disallows / for " + ", ".join(denied)
                      + " (Anthropic AI agents); host not crawled")
        self.manifest.add({
            "make": self.make, "doc_type": "robots", "title": "robots.txt", "url": f"{self.base}/robots.txt",
            "http_status": robots.status, "bytes": len(robots.body),
            "sha256": sha256(robots.body) if robots.body else "", "retrieved_at": now(),
            "path": rel.as_posix() if robots.body else "", "status": "blocked" if reason else "ok",
            "note": reason or "no rule against the pages used",
        })
        return reason

    def allowed(self, url: str) -> bool:
        ua = self.fetcher.client.headers["User-Agent"]
        host = urlsplit(url).netloc
        if host == self.host:
            return self.robots is None or self.robots.allowed(url, ua)
        return self.cdn_fetcher(host)[1].allowed(url, ua)

    def cdn_fetcher(self, host: str) -> tuple[Fetcher, Robots]:
        if host not in self.cdn:
            fetcher = Fetcher()
            robots = Robots(fetcher, f"https://{host}")
            rel = Path("press") / self.host / f"robots.{host}.txt.gz"
            if robots.body:
                write_gz(RAW_ROOT / rel, robots.body)
            self.manifest.add({
                "make": self.make, "doc_type": "robots", "title": f"robots.txt of {host}",
                "url": f"https://{host}/robots.txt", "http_status": robots.status, "bytes": len(robots.body),
                "sha256": sha256(robots.body) if robots.body else "", "retrieved_at": now(),
                "path": rel.as_posix() if robots.body else "",
                "status": "blocked" if robots.denied_agents() else "ok",
                "note": ("4xx answer = no robots rules (RFC 9309 2.3.1.3)"
                         if isinstance(robots.status, int) and 400 <= robots.status < 500
                         else "no rule against the files used"),
            })
            self.cdn[host] = (fetcher, robots)
        return self.cdn[host]

    def fetcher_for(self, url: str) -> Fetcher:
        host = urlsplit(url).netloc
        return self.fetcher if host == self.host else self.cdn_fetcher(host)[0]

    # ---- discovery answers ------------------------------------------------------------------
    def index(self, url: str, name: str, kind: str, line: str = "", year: str = "", title: str = "") -> bytes | None:
        """GET a discovery answer (API JSON or listing page); cached via the manifest."""
        rel = Path("press") / self.host / "api" / (safe_name(name) + (".json.gz" if kind == "json" else ".html.gz"))
        row = self.manifest.ok(url)
        if row and not self.refresh_index and row.get("path") and (RAW_ROOT / row["path"]).exists():
            return read_maybe_gz(RAW_ROOT / row["path"])
        if not self.allowed(url):
            self.manifest.add({"make": self.make, "line": line, "year": year, "doc_type": "press_index",
                               "title": title, "url": url, "status": "robots_disallowed", "retrieved_at": now()})
            return None
        headers = {"accept": "application/json"} if kind == "json" else None
        response = self.fetcher.get(url, headers=headers)
        status = response.status_code if response is not None else ""
        body = response.content if response is not None else b""
        ctype = response.headers.get("content-type", "") if response is not None else ""
        ok = status == 200 and (("json" in ctype) if kind == "json" else ("html" in ctype))
        if ok:
            write_gz(RAW_ROOT / rel, body)
        self.manifest.add({
            "make": self.make, "line": line, "year": year, "doc_type": "press_index", "title": title,
            "url": url, "http_status": status, "bytes": len(body), "sha256": sha256(body) if body else "",
            "retrieved_at": now(), "path": rel.as_posix() if ok else "",
            "status": "ok" if ok else ("not_found" if status == 404 else "error"),
            "note": "" if ok else clean(body[:200].decode("utf-8", errors="replace")),
        })
        return body if ok else None

    def api(self, path: str, **kw) -> dict | None:
        body = self.index(f"{self.base}/api{path}", "api_" + path.strip("/"), "json", **kw)
        return json.loads(body) if body else None

    # ---- documents ----------------------------------------------------------------------------
    def save_pdf(self, rel: Path, body: bytes) -> int:
        target = RAW_ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        pages = pdf_pages(body)
        store_pagetext(sha256(body), rel.as_posix(), pages)
        return len(pages)

    def save_word(self, rel: Path, body: bytes) -> list[list[str]]:
        """Word member (.doc/.docx): stored as published; page text = the table rows as text
        (cells separated by a tab), the rows themselves are kept under "rows"."""
        target = RAW_ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        rows = doc_rows(body) if rel.suffix.lower() == ".doc" else docx_rows(body)
        store_pagetext(sha256(body), rel.as_posix(), [rows_text(rows)], {"rows": rows})
        return rows

    def download_pdf(self, url: str, line: str, year: int, title: str, note: str) -> dict:
        row = self.manifest.ok(url)
        if row and row.get("path") and (RAW_ROOT / row["path"]).exists():
            return row
        base = {"make": self.make, "line": line, "year": year, "doc_type": "press_specifications",
                "title": title, "url": url}
        if not self.allowed(url):
            row = {**base, "status": "robots_disallowed", "retrieved_at": now(), "note": note}
            self.manifest.add(row)
            return row
        response = self.fetcher_for(url).get(url)
        status = response.status_code if response is not None else ""
        body = response.content if response is not None else b""
        name = unquote(Path(urlsplit(url).path).name)
        ok = status == 200 and body[:5] == b"%PDF-"
        rel = Path("press") / self.host / safe_name(name if name.lower().endswith(".pdf") else name + ".pdf")
        if ok:
            pages = self.save_pdf(rel, body)
            note = f"{note}; {pages} PDF pages"
            self.downloaded += 1
        else:
            self.failed += 1
            ctype = response.headers.get("content-type", "") if response is not None else ""
            note = f"{note}; not a PDF ({ctype})" if status == 200 else note
        row = {**base, "http_status": status, "bytes": len(body), "sha256": sha256(body) if ok else "",
               "retrieved_at": now(), "path": rel.as_posix() if ok else "",
               "status": "ok" if ok else ("not_found" if status == 404 else "error"), "note": note}
        self.manifest.add(row)
        return row

    def download_zip(self, url: str, line: str, year: int, title: str, note: str,
                     member_filter: re.Pattern | None = None) -> list[dict]:
        """JLR: zip archive holding the spec PDF(s); every PDF member is one manifest row.

        member_filter: keep only PDF members whose file name matches (press kits hold releases,
        fact sheets and spec sheets); a zip without a matching member gets one row with
        status=no_spec_member listing its members."""
        known = [r for u, r in self.manifest.rows.items()
                 if (u == url or u.startswith(url + "#")) and r.get("status") == "ok"
                 and r.get("path") and (RAW_ROOT / r["path"]).exists()]
        if known:
            return known
        previous = self.manifest.rows.get(url, {})
        if previous.get("status") == "no_spec_member":
            listed = previous.get("note", "").split("zip members: ", 1)[-1].split("; ")
            if not any(member_wanted(name, member_filter) for name in listed):
                return [previous]
        base = {"make": self.make, "line": line, "year": year, "doc_type": "press_specifications", "title": title}
        if not self.allowed(url):
            row = {**base, "url": url, "status": "robots_disallowed", "retrieved_at": now(), "note": note}
            self.manifest.add(row)
            return [row]
        response = self.fetcher_for(url).get(url)
        status = response.status_code if response is not None else ""
        body = response.content if response is not None else b""
        members: list[tuple[str, bytes]] = []
        names: list[str] = []
        if status == 200 and body[:2] == b"PK":
            archive = zipfile.ZipFile(io.BytesIO(body))
            names = [info.filename for info in archive.infolist() if not info.filename.endswith("/")]
            members = [(info.filename, archive.read(info)) for info in archive.infolist()
                       if member_wanted(info.filename, member_filter)]
        if names and not members:
            row = {**base, "url": url, "http_status": status, "bytes": len(body), "sha256": sha256(body),
                   "retrieved_at": now(), "status": "no_spec_member",
                   "note": f"{note}; zip members: " + "; ".join(names)[:600]}
            self.manifest.add(row)
            return [row]
        if not members:
            self.failed += 1
            row = {**base, "url": url, "http_status": status, "bytes": len(body), "retrieved_at": now(),
                   "status": "not_found" if status == 404 else "error",
                   "note": f"{note}; zip without PDF/Word member" if status == 200 else note}
            self.manifest.add(row)
            return [row]
        stem = safe_name(Path(urlsplit(url).path).parent.name)[:8] + "_" + safe_name(Path(urlsplit(url).path).stem)
        rows = []
        for member, data in members:
            member_url = url if len(members) == 1 else f"{url}#{quote(member)}"
            rel = Path("press") / self.host / f"{stem}__{safe_name(Path(member).name)}"
            if member.lower().endswith(".pdf"):
                pages = self.save_pdf(rel, data)
                kind = f"PDF '{member}'"
                extent = f"{pages} PDF pages"
            else:
                rows_ = self.save_word(rel, data)
                kind = f"Word document '{member}'"
                extent = f"{len(rows_)} table rows/paragraphs, page text = one page"
            self.downloaded += 1
            row = {**base, "url": member_url, "http_status": status, "bytes": len(data), "sha256": sha256(data),
                   "retrieved_at": now(), "path": rel.as_posix(), "status": "ok",
                   "note": f"{note}; {kind} from zip ({len(body)} bytes, sha256 {sha256(body)[:16]}); {extent}"}
            self.manifest.add(row)
            rows.append(row)
        return rows

    def not_found(self, line: str, year: int, url: str, note: str) -> None:
        row = self.manifest.rows.get(url)
        if row and row.get("status") == "not_found" and row.get("note") == note:
            return
        self.manifest.add({"make": self.make, "line": line, "year": year, "doc_type": "press_specifications",
                           "title": "", "url": url, "retrieved_at": now(), "status": "not_found", "note": note})


# ---- media.vw.com / media.audiusa.com ----------------------------------------------------------
def doc_url(host: Host, doc: dict) -> str:
    return urljoin(host.base + "/", doc["url"].lstrip("/"))


def title_lines(host: str, title: str) -> list[str]:
    return [key for key, pattern in TITLE_LINES[host] if re.search(pattern, title)]


def collect_newspress(host: Host) -> dict:
    slugs = NEWSPRESS_SLUGS[host.host]
    tree = host.api("/models", title="model tree")
    known = set()

    def walk(node: dict) -> None:
        known.add(node.get("slug"))
        for child in node.get("children") or []:
            walk(child)

    for node in (tree or {}).get("data", []):
        walk(node)
    missing = [slug for slug in slugs if slug not in known]
    if missing:
        log(f"  slugs not in the model tree: {missing}")

    # url -> {"title", "published", "contexts": [(kind "model"|"kit", line of the model page, context title)]}
    docs: dict[str, dict] = {}
    kit_line: dict[str, str] = {}
    kit_title: dict[str, str] = {}
    exclude = re.compile(TITLE_EXCLUDE[host.host])

    def add_doc(doc: dict, kind: str, line: str, context: str) -> None:
        if doc.get("media_type") != "document" and not str(doc.get("url", "")).lower().endswith(".pdf"):
            return
        url = doc_url(host, doc)
        entry = docs.setdefault(url, {"title": clean(doc.get("title")), "published": doc.get("published"),
                                      "contexts": []})
        entry["contexts"].append((kind, line, context))

    for slug, line in slugs.items():
        if slug not in known:
            continue
        data = host.api(f"/models/{quote(slug)}", line=line, title=f"model page {slug}")
        if not data:
            continue
        model = data["data"]
        for doc in model.get("documents") or []:
            add_doc(doc, "model", line, f"model page {slug}")
        for kit in model.get("pressKits") or []:
            kit_line.setdefault(kit["slug"], line)
            kit_title.setdefault(kit["slug"], clean(kit.get("title")))

    queue = list(kit_line)
    seen = set()
    while queue:
        slug = queue.pop(0)
        if slug in seen:
            continue
        seen.add(slug)
        line = kit_line[slug]
        data = host.api(f"/press-kits/{quote(slug)}", line=line, title=f"press kit {slug}")
        if not data:
            continue
        kit = data["data"]
        kit_title[slug] = clean(kit.get("title"))
        for doc in kit.get("documents") or []:
            add_doc(doc, "kit", line, kit_title[slug])
        for sibling in kit.get("siblingsAndSelf") or []:
            # the siblings are all press kits under the same parent node, which can be a broad
            # group (e.g. archived kits of many models): follow only kits naming a line of this host
            sibling_title = clean(sibling.get("title"))
            if not title_lines(host.host, sibling_title) or exclude.search(sibling_title):
                continue
            if sibling.get("slug") and sibling["slug"] not in seen:
                kit_line.setdefault(sibling["slug"], line)
                kit_title.setdefault(sibling["slug"], clean(sibling.get("title")))
                queue.append(sibling["slug"])

    def select() -> list[tuple[str, str, int, str, str]]:
        """Spec documents in scope: (url, line, year, title, note)."""
        picked = []
        kit_picked = []
        for url, entry in sorted(docs.items()):
            title = entry["title"]
            is_spec = bool(SPEC_TITLE.search(title)) and not NOT_SPEC_TITLE.search(title)
            is_kit = bool(PRESS_KIT_TITLE.search(title)) and not is_spec
            if not (is_spec or is_kit):
                continue
            if exclude.search(title):
                continue
            named = title_lines(host.host, title)
            kit_named = sorted({key for kind, _, context in entry["contexts"] if kind in ("kit", "release")
                                for key in title_lines(host.host, context)})
            page_lines = sorted({line for kind, line, _ in entry["contexts"] if kind == "model"})
            if named:
                lines, how = named, "line named in the document title"
            elif kit_named:
                lines, how = kit_named, "line named in the press kit / release title"
            elif page_lines:
                lines, how = page_lines, "line of the model page listing the document"
            else:
                continue
            year = title_year(title)
            year_how = "year from the title"
            if year is None:
                for _, _, context in entry["contexts"]:
                    year = title_year(context)
                    if year:
                        year_how = f"year from '{context}'"
                        break
            if year is None:
                continue
            name_year = re.search(r"(?i)(20\d\d) ?my|my ?(20\d\d)", unquote(urlsplit(url).path))
            file_note = ""
            if name_year and int(name_year.group(1) or name_year.group(2)) != year:
                file_note = f"; file name says MY{name_year.group(1) or name_year.group(2)}"
            for line in lines:
                reg = host.lines.get(line)
                if reg is None or not (max(YEARS[0], reg.years[0]) <= year <= min(YEARS[1], reg.years[1])):
                    continue
                contexts = "; ".join(sorted({c for _, _, c in entry["contexts"]}))[:300]
                (picked if is_spec else kit_picked).append((
                    url, line, year, title,
                    ("" if is_spec else "press kit PDF (no spec-titled document for this line-year); ")
                    + f"{how}; {year_how}{file_note}; published {entry['published']}; found on: {contexts}"
                    + (f"; also lines {','.join(x for x in lines if x != line)}" if len(lines) > 1 else "")))
        spec_years = {(line, year) for _, line, year, _, _ in picked}
        return picked + [k for k in kit_picked if (k[1], k[2]) not in spec_years]

    # press releases of the model pages, for line-years without a spec document in the press kits:
    # /api/models/<slug>/releases?page=N (5 per page) and /api/releases/<id>/sidebar-content
    # (documents attached to a release); only releases with documents whose title names a
    # model year that is still missing for the line.
    covered = {(line, year) for _, line, year, _, _ in select()}
    for slug, line in slugs.items():
        reg = host.lines[line]
        missing = {y for y in range(max(YEARS[0], reg.years[0]), min(YEARS[1], reg.years[1]) + 1)
                   if (line, y) not in covered}
        if not missing or slug not in known:
            continue
        page, last = 1, 1
        while page <= last:
            data = host.api(f"/models/{quote(slug)}/releases?page={page}", line=line,
                            title=f"releases of {slug} page {page}")
            if not data:
                break
            last = int((data.get("meta") or {}).get("last_page") or 1)
            for release in data.get("data") or []:
                rtitle = clean(release.get("title"))
                years_named = {int(y) for y in re.findall(r"\b(20[12]\d)\b", rtitle)}
                years_named |= {2000 + int(y) for y in re.findall(r"(?i)\bMY ?(\d{2})\b", rtitle)}
                if not release.get("documents_count") or not (years_named & missing):
                    continue
                side = host.api(f"/releases/{release['id']}/sidebar-content", line=line,
                                title=f"release {release['id']} documents: {rtitle[:80]}")
                for doc in ((side or {}).get("data") or {}).get("documents") or []:
                    add_doc(doc, "release", line, rtitle)
            page += 1

    found: dict[tuple[str, int], list[str]] = {}
    selected = select()
    log(f"  {len(docs)} documents listed, {len(selected)} spec documents in scope")
    if host.dry_run:
        for url, entry in sorted(docs.items(), key=lambda kv: kv[1]["title"]):
            mark = "*" if any(s[0] == url for s in selected) else " "
            log(f"   {mark} {entry['title']} | {url} | {sorted({c for _, _, c in entry['contexts']})[:2]}")
        return {}
    for url, line, year, title, note in selected:
        row = host.download_pdf(url, line, year, title, note)
        if row.get("status") == "ok":
            found.setdefault((line, year), []).append(url)
        log(f"  {row.get('status'):>9} {line} {year} {title}")

    # line-years without a spec document
    kits_by_line_year: dict[tuple[str, int], list[str]] = {}
    for slug, line in kit_line.items():
        year = title_year(kit_title.get(slug, ""))
        if year:
            for key in title_lines(host.host, kit_title.get(slug, "")) or [line]:
                kits_by_line_year.setdefault((key, year), []).append(kit_title[slug])
    first_slug = {}
    for slug, line in slugs.items():
        first_slug.setdefault(line, slug)
    for key, reg in host.lines.items():
        for year in range(max(YEARS[0], reg.years[0]), min(YEARS[1], reg.years[1]) + 1):
            if (key, year) in found:
                continue
            kits = kits_by_line_year.get((key, year), [])
            note = ("press kits of that year without a spec document: " + "; ".join(sorted(set(kits)))
                    if kits else "no press kit of that model year listed")
            note += ("; checked: model pages " + ", ".join(s for s, k in slugs.items() if k == key)
                     + ", their press kits (all years) and the releases naming that year")
            host.not_found(key, year, f"{host.base}/models/{first_slug.get(key, '')}#{year}", note)
    return found


# ---- media.jlr.com -------------------------------------------------------------------------------
def jlr_items(html: bytes, kind: str) -> list[dict]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    items = []
    for section in soup.find_all("h2"):
        name = clean(section.get_text())
        container = section.find_parent("div", class_="row")
        if container is None:
            continue
        # the section's blocks follow until the next h2
        node = container
        while node is not None:
            node = node.find_next_sibling()
            if node is None or node.find("h2"):
                break
            for block in node.select("div.press-kit-block"):
                for row in block.select("div.pk-row"):
                    head = row.find("h3")
                    anchors = [a for a in row.select("a.jlr-download-btn") if a.get("href")]
                    if head is None or not anchors:
                        continue
                    items.append({"section": name, "title": clean(head.get_text()),
                                  "links": [a["href"] for a in anchors],
                                  "labels": [clean(a.get_text()) for a in anchors],
                                  "tab": block.get("id"), "kind": kind})
    return items


def collect_jlr(host: Host) -> dict:
    found: dict[tuple[str, int], list[str]] = {}
    seen_urls = set()
    for path, kind in JLR_PAGES:
        url = host.base + path
        body = host.index(url, path.strip("/").replace("/", "_"), "html", title=f"{kind} listing {path}")
        if not body:
            continue
        items = jlr_items(body, kind)
        log(f"  {path}: {len(items)} items")
        for item in items:
            title = item["title"]
            year = title_year(title)
            named = [key for key, pattern in JLR_TITLE_LINES if re.search(pattern, title)]
            line = named[0] if named else JLR_SECTION_LINES.get(item["section"])
            if line is None or year is None:
                continue
            reg = host.lines[line]
            if not (max(YEARS[0], reg.years[0]) <= year <= min(YEARS[1], reg.years[1])):
                continue
            if JLR_CANADA_ONLY.search(title) and not JLR_US.search(title):
                continue
            region = ("US named in the title" if JLR_US.search(title)
                      else "no market named in the title; listed in the North America (en-us) edition")
            for link, label in zip(item["links"], item["labels"]):
                if JLR_CANADA_ONLY.search(label) and not JLR_US.search(label):
                    continue
                if link in seen_urls:
                    continue
                seen_urls.add(link)
                note = (f"{kind} item '{title}' in section '{item['section']}' of {path}; download '{label}'; "
                        f"{region}; line {'named in the title' if named else 'from the section'}")
                spec_item = kind == "tech-specs" or bool(JLR_TITLE_SPEC.search(title))
                rows = host.download_zip(link, line, year, title, note, None if spec_item else JLR_MEMBER_SPEC)
                for row in rows:
                    if row.get("status") == "ok":
                        found.setdefault((line, year), []).append(row["url"])
                    log(f"  {row.get('status'):>9} {line} {year} {title} {row.get('url', '')[-60:]}")
    for key, reg in host.lines.items():
        for year in range(max(YEARS[0], reg.years[0]), min(YEARS[1], reg.years[1]) + 1):
            if (key, year) not in found:
                host.not_found(key, year, f"{host.base}{JLR_LINE_PAGES[key]}#{year}",
                               "no US tech-spec item or spec press kit of that model year on the "
                               "/en-us tech-specs and press-kit pages")
    return found


# ---- media.stellantisnorthamerica.com ----------------------------------------------------------
def collect_blocked(host: Host, reason: str) -> dict:
    for key, reg in host.lines.items():
        for year in range(max(YEARS[0], reg.years[0]), min(YEARS[1], reg.years[1]) + 1):
            url = f"{host.base}/#{key}/{year}"
            if host.manifest.rows.get(url, {}).get("status") != "blocked":
                host.manifest.add({"make": host.make, "line": key, "year": year,
                                   "doc_type": "press_specifications", "url": url, "retrieved_at": now(),
                                   "status": "blocked", "note": reason})
    return {}


def run_host(name: str, refresh_index: bool, dry_run: bool = False) -> None:
    host = Host(name, refresh_index)
    host.dry_run = dry_run
    log(f"== {name}")
    try:
        reason = host.check_robots()
        if reason:
            log(f"  {reason}")
            collect_blocked(host, reason)
            return
        if name in NEWSPRESS_SLUGS:
            found = collect_newspress(host)
        elif name == JLR:
            found = collect_jlr(host)
        else:
            raise ValueError(name)
    except Blocked as exc:
        host.manifest.add({"make": host.make, "doc_type": "press_index", "url": f"{host.base}/#blocked-{now()}",
                           "retrieved_at": now(), "status": "blocked",
                           "note": f"host stopped after repeated 403/429: {exc}"})
        log(f"  BLOCKED: {exc}")
        return
    years = sum(len(v) for v in found.values())
    log(f"  done {name}: {len(found)} line-years with spec documents ({years} documents); "
        f"downloaded now {host.downloaded}, failed {host.failed}; requests {host.fetcher.requests}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", action="append", choices=ALL_HOSTS, help="host(s) to run (default all)")
    parser.add_argument("--refresh-index", action="store_true", help="re-fetch the discovery answers")
    parser.add_argument("--dry-run", action="store_true", help="VW/Audi: list documents, download nothing")
    args = parser.parse_args(argv)
    for name in args.host or ALL_HOSTS:
        run_host(name, args.refresh_index, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
