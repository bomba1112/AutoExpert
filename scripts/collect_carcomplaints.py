"""CarComplaints.com owner-complaint summaries per line and model year (prompt 5.9).

Navigation follows the site's own links (make page -> model page -> model-year pages); no
URL is guessed. robots.txt allows these pages for general crawlers. One request at a time,
3-6 s pause, raw HTML gzip-compressed under RAW_ROOT/carcomplaints, manifest
data_work/_shared/manifest_carcomplaints.csv.

Parsed per model year: complaints per category (the site's counts) and the "Worst <year>
<model> Problems" list with the site's average repair cost and average mileage.
Output: data_work/_shared/carcomplaints/<make>.json  (SECONDARY, owner reports).

  .venv/Scripts/python.exe scripts/collect_carcomplaints.py [--make hyundai]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, read_maybe_gz, sha256, write_gz  # noqa: E402
from us_tech_lines import MAKE_ORDER, MAKES, LINES  # noqa: E402

BASE = "https://www.carcomplaints.com"
FIELDS = ["kind", "make", "line", "year", "url", "http_status", "bytes", "sha256", "retrieved_at", "path", "status", "note"]
SITE_MAKE = {"mercedes-benz": "Mercedes-Benz", "land-rover": "Land_Rover", "volkswagen": "Volkswagen"}
# site model link text -> registry line (checked against the make page's own links)
LINE_TEXT = {
    "hyundai/sonata": r"^Sonata$", "hyundai/elantra": r"^Elantra$", "hyundai/tucson": r"^Tucson$",
    "hyundai/santa-fe": r"^Santa Fe$", "hyundai/santa-fe-sport": r"^Santa Fe Sport$", "hyundai/accent": r"^Accent$",
    "hyundai/kona": r"^Kona$", "kia/optima-k5": r"^(Optima|K5)$", "kia/forte": r"^Forte$", "kia/rio": r"^Rio$",
    "kia/sorento": r"^Sorento$", "kia/sportage": r"^Sportage$", "toyota/camry": r"^Camry$", "toyota/corolla": r"^Corolla$",
    "toyota/rav4": r"^RAV4$", "toyota/highlander": r"^Highlander$", "toyota/prius": r"^Prius$",
    "mercedes-benz/c-class": r"^C-Class$", "mercedes-benz/e-class": r"^E-Class$", "mercedes-benz/s-class": r"^S-Class$",
    "mercedes-benz/gla": r"^GLA(-Class)?$", "mercedes-benz/glb": r"^GLB(-Class)?$", "mercedes-benz/glc": r"^GL[CK](-Class)?$",
    "mercedes-benz/gle": r"^(GLE|ML|M)(-Class)?$", "mercedes-benz/gls": r"^(GLS|GL)(-Class)?$", "mercedes-benz/cla": r"^CLA(-Class)?$",
    "mercedes-benz/cls": r"^CLS(-Class)?$", "mercedes-benz/cle": r"^CLE(-Class)?$", "mercedes-benz/eqs": r"^EQS$",
    "mercedes-benz/eqb": r"^EQB$", "bmw/3-series": r"^3 Series$", "bmw/5-series": r"^5 Series$", "bmw/7-series": r"^7 Series$",
    "bmw/x5": r"^X5$", "bmw/x6": r"^X6$", "bmw/x7": r"^X7$", "bmw/m3": r"^M3$", "bmw/m5": r"^M5$",
    "chevrolet/malibu": r"^Malibu$", "chevrolet/cruze": r"^Cruze$", "chevrolet/equinox": r"^Equinox$", "chevrolet/trax": r"^Trax$",
    "ford/fusion": r"^Fusion$", "lexus/es": r"^ES(\s?\d{3}\w?)?$", "lexus/rx": r"^RX(\s?\d{3}\w?)?$", "lexus/nx": r"^NX(\s?\d{3}\w?)?$",
    "lexus/gx": r"^GX(\s?\d{3})?$", "honda/accord": r"^Accord$", "honda/civic": r"^Civic$", "honda/cr-v": r"^CR-V$",
    "nissan/altima": r"^Altima$", "nissan/sentra": r"^Sentra$", "nissan/rogue": r"^Rogue$", "nissan/pathfinder": r"^Pathfinder$",
    "land-rover/range-rover": r"^Range Rover$", "land-rover/range-rover-sport": r"^Range Rover Sport$",
    "land-rover/range-rover-evoque": r"^Range Rover Evoque$", "land-rover/discovery-sport": r"^(Discovery Sport|LR2)$",
    "infiniti/q50": r"^Q50$", "infiniti/qx60": r"^(QX60|JX)$", "infiniti/fx-qx70": r"^(QX70|FX)$",
    "cadillac/cts": r"^CTS$", "cadillac/srx": r"^SRX$", "cadillac/escalade": r"^Escalade$",
    "jeep/grand-cherokee": r"^Grand Cherokee$", "jeep/cherokee": r"^Cherokee$", "jeep/compass": r"^Compass$",
    "audi/a3": r"^A3$", "audi/a4": r"^A4$", "audi/a5": r"^A5$", "audi/a6": r"^A6$", "audi/q3": r"^Q3$", "audi/q5": r"^Q5$", "audi/q7": r"^Q7$",
    "volkswagen/jetta": r"^Jetta$", "volkswagen/passat": r"^Passat$", "volkswagen/tiguan": r"^Tiguan$", "volkswagen/atlas": r"^Atlas$",
    "volkswagen/arteon": r"^Arteon$", "volkswagen/touareg": r"^Touareg$", "mitsubishi/outlander": r"^Outlander$",
    "mitsubishi/outlander-sport": r"^Outlander Sport$", "tesla/model-3": r"^Model 3$", "tesla/model-y": r"^Model Y$",
    "tesla/model-s": r"^Model S$", "tesla/model-x": r"^Model X$",
}


def get(fetcher, manifest, url, dest, meta):
    hit = manifest.ok(url)
    if hit and (RAW_ROOT / hit["path"]).exists():
        return read_maybe_gz(RAW_ROOT / hit["path"]).decode("utf-8", errors="replace")
    response = fetcher.get(url)
    row = {**meta, "url": url, "retrieved_at": now()}
    if response is None or response.status_code != 200:
        manifest.add({**row, "http_status": response.status_code if response else "ERROR",
                      "status": "not_found" if response is not None and response.status_code == 404 else "error"})
        return None
    write_gz(dest, response.content)
    manifest.add({**row, "http_status": 200, "bytes": len(response.content), "sha256": sha256(response.content),
                  "path": dest.relative_to(RAW_ROOT).as_posix(), "status": "ok"})
    return response.text


def parse_year(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" | ", strip=True)
    categories = {}
    block = re.search(r"Problems by Category(.*?)(?:Loading|Stay Up to Date)", text)
    if block:
        for name, count in re.findall(r"\|\s*([a-zA-Z /]+?) problems\s*\|\s*([\d,]+)", block.group(1)):
            categories[name.strip()] = int(count.replace(",", ""))
    links = {}
    for a in soup.find_all("a", href=True):
        found = re.match(r"#(\d+):", a.get_text(" ", strip=True))
        if found and a["href"].endswith(".shtml"):
            links.setdefault(int(found.group(1)), urljoin(url, a["href"]))
    worst = []
    for rank, name, cost, miles in re.findall(
        r"#(\d+):\s*\|\s*([^|]+?)\s*\|\s*\d{4} [^|]+\|\s*Average Cost to Fix:\s*\|\s*([^|]+?)\s*\|\s*Average Mileage:\s*\|\s*([^|]+?)\s*\|", text
    ):
        href = links.get(int(rank), "")
        category = href.rstrip("/").split("/")[-2] if href else ""
        worst.append({"rank": int(rank), "problem": name.strip(), "category": category, "problem_url": href,
                      "avg_cost": cost.strip(), "avg_mileage": miles.strip(),
                      "quote": f"#{rank}: {name.strip()} Average Cost to Fix: {cost.strip()} Average Mileage: {miles.strip()}"})
    return {"url": url, "categories": categories, "worst": worst}


def reparse(manifest: Manifest, out_dir: Path) -> None:
    """Rebuild the per-make JSON from the stored pages (no requests) after a parser change."""
    for path in sorted(out_dir.glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        for entry in result.values():
            for by_year in entry.get("models", {}).values():
                for year, page in by_year.items():
                    hit = manifest.ok(page["url"])
                    if hit:
                        html = read_maybe_gz(RAW_ROOT / hit["path"]).decode("utf-8", errors="replace")
                        by_year[year] = parse_year(html, page["url"])
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print("reparsed", path.name, flush=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--make")
    parser.add_argument("--reparse", action="store_true", help="re-read stored pages only")
    args = parser.parse_args(argv)
    if args.reparse:
        reparse(Manifest(WORK / "_shared" / "manifest_carcomplaints.csv", FIELDS), WORK / "_shared" / "carcomplaints")
        return 0
    fetcher = Fetcher(pause=(3.0, 6.0))
    manifest = Manifest(WORK / "_shared" / "manifest_carcomplaints.csv", FIELDS)
    out_dir = WORK / "_shared" / "carcomplaints"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        for make in ([args.make] if args.make else MAKE_ORDER):
            site_make = SITE_MAKE.get(make, MAKES[make]["epa"])
            make_url = f"{BASE}/{site_make}/"
            html = get(fetcher, manifest, make_url, RAW_ROOT / "carcomplaints" / make / "_make.html.gz", {"kind": "make", "make": make})
            if html is None:
                print(make, "make page unavailable", flush=True)
                continue
            soup = BeautifulSoup(html, "html.parser")
            links = {}
            for a in soup.find_all("a", href=True):
                href = urljoin(make_url, a["href"])
                if re.fullmatch(rf"{re.escape(BASE)}/{re.escape(site_make)}/[^/]+/", href):
                    links.setdefault(a.get_text(" ", strip=True), href)
            result = {}
            for line in [ln for ln in LINES if ln.make == make]:
                pattern = LINE_TEXT.get(line.key)
                matched = [(t, u) for t, u in links.items() if pattern and re.match(pattern, t)]
                if not matched:
                    result[line.key] = {"status": "not_on_site"}
                    continue
                entry = {"status": "ok", "models": {}}
                for text, model_url in matched:
                    model_slug = model_url.rstrip("/").rsplit("/", 1)[-1]
                    model_html = get(fetcher, manifest, model_url, RAW_ROOT / "carcomplaints" / make / model_slug / "_model.html.gz",
                                     {"kind": "model", "make": make, "line": line.key})
                    if model_html is None:
                        continue
                    years = {}
                    for a in BeautifulSoup(model_html, "html.parser").find_all("a", href=True):
                        href = urljoin(model_url, a["href"])
                        found = re.fullmatch(rf"{re.escape(model_url)}(\d{{4}})/", href)
                        if found and line.years[0] <= int(found.group(1)) <= line.years[1]:
                            years[int(found.group(1))] = href
                    for year, year_url in sorted(years.items()):
                        page = get(fetcher, manifest, year_url, RAW_ROOT / "carcomplaints" / make / model_slug / f"{year}.html.gz",
                                   {"kind": "year", "make": make, "line": line.key, "year": year})
                        if page:
                            entry["models"].setdefault(text, {})[str(year)] = parse_year(page, year_url)
                    print(line.key, text, len(years), "years", flush=True)
                result[line.key] = entry
            (out_dir / f"{make}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    except Blocked as exc:
        print("STOPPED:", exc, flush=True)
        return 3
    print("requests", fetcher.requests, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
