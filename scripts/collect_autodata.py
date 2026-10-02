"""auto-data.net as a SECONDARY source for Mercedes-Benz oil and coolant capacities (prompt 5.9).

auto-data.net lists European versions (production years, metric power); it has no US listing.
A listing is used only when it matches a US configuration of the line by model designation
(e.g. "C 300", "AMG C 43"), displacement, number of cylinders, 4MATIC/AWD and years
(US model year within production start .. end + 1), and only for line-years that no US owner's
manual covers (build_manual_facts.py). The engine oil specification on the site is shown only
after a login and is not collected.

Navigation follows the site's own links: brand page -> model pages -> generation pages ->
modification pages. robots.txt allows general crawlers. One request at a time, 2-5 s pause.
Raw pages: RAW_ROOT/autodata/<id>.html.gz, manifest data_work/_shared/manifest_autodata.csv,
page text RAW_ROOT/pagetext/<sha256>.json.gz, documents data_work/<make>/extracted/autodata-<id>.json.

  .venv/Scripts/python.exe scripts/collect_autodata.py mercedes-benz
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, read_maybe_gz, sha256, write_gz  # noqa: E402
from us_tech_lines import lines_for  # noqa: E402

BASE = "https://www.auto-data.net"
BRAND = {"mercedes-benz": "/en/mercedes-benz-brand-138"}
# registry line -> auto-data model slugs (as linked from the brand page)
MODELS = {
    "mercedes-benz/c-class": ["c-class"], "mercedes-benz/e-class": ["e-class"], "mercedes-benz/s-class": ["s-class"],
    "mercedes-benz/gla": ["gla"], "mercedes-benz/glb": ["glb"], "mercedes-benz/glc": ["glc", "glk"],
    "mercedes-benz/gle": ["gle", "m-class"], "mercedes-benz/gls": ["gls", "gl"], "mercedes-benz/cla": ["cla"],
    "mercedes-benz/cls": ["cls"], "mercedes-benz/cle": ["cle"], "mercedes-benz/amg-gt-4-door": ["amg-gt-4-door-coupe"],
    "mercedes-benz/eqs": ["eqs"], "mercedes-benz/eqb": ["eqb"],
}
SKIP_BODY = re.compile(r"station wagon|estate|t-modell|all-terrain|long|china|pullman|van", re.I)
FIELDS = ["kind", "make", "line", "url", "http_status", "bytes", "sha256", "retrieved_at", "path", "status", "note"]
DESIGNATION = re.compile(r"\b(?:Mercedes-(?:AMG|Maybach)\s+|AMG\s+|Maybach\s+)?([A-Z]{1,3})\s?(\d{2,3})\s?(e|d|h)?\b")


def designation(text: str) -> str | None:
    """'AMG C 43 V6 (390 Hp) 4MATIC' -> 'AMGC43'; 'C 300 (258 Hp)' -> 'C300'; EPA 'AMG C43 4matic' -> 'AMGC43'."""
    t = text.replace("Mercedes-AMG", "AMG").replace("Mercedes-Maybach", "Maybach")
    m = DESIGNATION.search(t)
    if not m:
        return None
    prefix = "AMG" if re.search(r"\bAMG\b", t[: m.end()]) else "Maybach" if re.search(r"Maybach", t[: m.end()]) else ""
    return f"{prefix}{m.group(1)}{m.group(2)}{m.group(3) or ''}"


def get(fetcher, manifest, url, dest, meta):
    hit = manifest.ok(url)
    if hit and (RAW_ROOT / hit["path"]).exists():
        return read_maybe_gz(RAW_ROOT / hit["path"]).decode("utf-8", errors="replace")
    response = fetcher.get(url)
    row = {**meta, "url": url, "retrieved_at": now()}
    if response is None or response.status_code != 200:
        manifest.add({**row, "http_status": response.status_code if response is not None else "ERROR", "status": "error"})
        return None
    write_gz(dest, response.content)
    manifest.add({**row, "http_status": 200, "bytes": len(response.content), "sha256": sha256(response.content),
                  "path": dest.relative_to(RAW_ROOT).as_posix(), "status": "ok"})
    return response.text


def table(html: str) -> dict:
    """Label -> value of the specification rows (<div class="row"><div class="par">..</div><div class="val">..</div>);
    the secondary unit in <span class="val2"> (US qt, cu. in.) is left out of the value."""
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for row in soup.find_all("div", class_="row"):
        par, val = row.find("div", class_="par"), row.find("div", class_="val")
        if not par or not val:
            continue
        for extra in val.find_all("span", class_="val2"):
            extra.extract()
        out.setdefault(" ".join(par.get_text(" ", strip=True).split()), " ".join(val.get_text(" ", strip=True).split()))
    return out


def number(text: str | None) -> float | None:
    m = re.match(r"\s*(\d+(?:\.\d+)?)", text or "")
    return float(m.group(1)) if m else None


def us_configs(make: str, line_key: str) -> list[dict]:
    slug = line_key.split("/")[1]
    staging = json.loads((WORK / make / "staging" / slug / "staging.json").read_text(encoding="utf-8"))
    out = []
    for c in staging["configurations"]:
        for v in c.get("epa_vehicles", []):
            out.append({"year": c["year"], "designation": designation(v.get("epa_model", "")), "displacement": c.get("displacement_l"),
                        "cylinders": c.get("cylinders"), "awd": c.get("drivetrain") in ("AWD", "4WD"), "powertrain": c.get("powertrain"),
                        "epa_model": v.get("epa_model")})
    return out


def main(argv) -> int:
    make = argv[0]
    fetcher = Fetcher(pause=(2.0, 5.0), attempts=2, timeout=60)
    manifest = Manifest(WORK / "_shared" / "manifest_autodata.csv", FIELDS)
    out_dir = WORK / make / "extracted"
    written = 0
    try:
        brand_url = BASE + BRAND[make]
        brand = get(fetcher, manifest, brand_url, RAW_ROOT / "autodata" / "brand.html.gz", {"kind": "brand", "make": make})
        model_links = {re.sub(r"^/en/mercedes-benz-(.+)-model-\d+$", r"\1", h): urljoin(BASE, h)
                       for h in re.findall(r'href="(/en/mercedes-benz-[a-z0-9-]+-model-\d+)"', brand or "")}
        for line in lines_for(make):
            if line.key not in MODELS:
                continue
            configs = us_configs(make, line.key)
            wanted = {c["designation"] for c in configs if c["designation"]}
            for model_slug in MODELS[line.key]:
                model_url = model_links.get(model_slug)
                if not model_url:
                    print(line.key, model_slug, "not on site", flush=True)
                    continue
                html = get(fetcher, manifest, model_url, RAW_ROOT / "autodata" / f"model-{model_slug}.html.gz",
                           {"kind": "model", "make": make, "line": line.key})
                soup = BeautifulSoup(html or "", "html.parser")
                gens = {}
                for a in soup.find_all("a", href=True):
                    if re.search(r"-generation-\d+$", a["href"]):
                        url = urljoin(BASE, a["href"])
                        gens[url] = (gens.get(url, "") + " " + " ".join(a.get_text(" ", strip=True).split())).strip()
                for gen_url, gen_text in gens.items():
                    # "Mercedes-Benz C-class (W205) 2014 - 2018 Sedan Power: ..." : skip generations that
                    # ended before the 2014 model year and body styles never sold in the US line
                    span = re.search(r"\b((?:19|20)\d\d)\s*-\s*((?:19|20)\d\d)?", gen_text)
                    if span and span.group(2) and int(span.group(2)) < 2013:
                        continue
                    if SKIP_BODY.search(gen_text + " " + gen_url):
                        continue
                    gid = gen_url.rsplit("-", 1)[-1]
                    gen_html = get(fetcher, manifest, gen_url, RAW_ROOT / "autodata" / f"gen-{gid}.html.gz",
                                   {"kind": "generation", "make": make, "line": line.key})
                    gsoup = BeautifulSoup(gen_html or "", "html.parser")
                    mods = {}
                    for a in gsoup.find_all("a", href=True):
                        text = " ".join(a.get_text(" ", strip=True).split())
                        if re.search(r"-\d+$", a["href"]) and "generation" not in a["href"] and "model" not in a["href"] and "(" in text:
                            mods.setdefault(urljoin(BASE, a["href"]), text)
                    for mod_url, mod_text in mods.items():
                        if designation(mod_text) not in wanted:
                            continue
                        mid = mod_url.rsplit("-", 1)[-1]
                        target = out_dir / f"autodata-{mid}.json"
                        mod_html = get(fetcher, manifest, mod_url, RAW_ROOT / "autodata" / f"mod-{mid}.html.gz",
                                       {"kind": "modification", "make": make, "line": line.key})
                        if not mod_html:
                            continue
                        spec = table(mod_html)
                        start, end = number(spec.get("Start of production")), number(spec.get("End of production"))
                        displ = number(spec.get("Engine displacement"))
                        cyl = number(spec.get("Number of cylinders"))
                        awd = bool(re.search(r"4MATIC|all wheel", mod_text + " " + spec.get("Drive wheel", ""), re.I))
                        des = designation(mod_text)
                        if not start:
                            continue
                        last_my = (end or 2026) + 1
                        years_us = sorted({c["year"] for c in configs
                                           if c["designation"] == des and c["cylinders"] == cyl and c["awd"] == awd
                                           and displ and c["displacement"] and abs(float(c["displacement"]) - displ / 1000) < 0.06
                                           and start <= c["year"] <= last_my})
                        if not years_us:
                            continue
                        text = " ".join(BeautifulSoup(mod_html, "html.parser").get_text(" ", strip=True).split())
                        sha = sha256(mod_html.encode("utf-8"))
                        hit = manifest.ok(mod_url)
                        sha = hit.get("sha256") or sha
                        store = RAW_ROOT / "pagetext" / f"{sha}.json.gz"
                        with gzip.open(store, "wt", encoding="utf-8") as handle:
                            json.dump({"sha256": sha, "file": hit.get("path"), "pages": [text]}, handle)
                        engine_text = f"{des} {displ / 1000:.1f}L {int(cyl)}cyl" + (" 4MATIC" if awd else "")
                        facts = []
                        for label, key in (("Engine oil capacity", "engine_oil_capacity_l"), ("Coolant", "coolant_capacity_l")):
                            value = number(spec.get(label))
                            raw = spec.get(label, "")
                            quote = f"{label} {raw}"
                            if value is not None and quote in text:
                                facts.append({"key": key, "value": value, "unit": "L", "page": 1, "quote": quote, "row": f"{mod_text} | {label} | {raw} | engine code {spec.get('Engine Model/Code', '')}",
                                              "engine_text": engine_text, "original": raw})
                        doc = {
                            "key": f"autodata-{mid}", "make": make, "lines": [line.key], "years": years_us,
                            "doc_type": "secondary_specifications",
                            "title": f"auto-data.net: {mod_text} (European listing, production {int(start)}-{int(end) if end else ''})",
                            "path": str(RAW_ROOT / hit["path"]), "url": mod_url, "page_url": gen_url, "sha256": sha,
                            "retrieved_at": hit.get("retrieved_at"), "tier": "B", "source_type": "SECONDARY_SPEC_DATABASE",
                            "publisher": "auto-data.net (European listing; matched to the US model by designation, displacement, cylinders, drive and years)",
                            "authenticity": "SECONDARY",
                        }
                        result = {"doc": doc, "extractor": "autodata-1", "pages": 1, "edition_market": "EU_MATCHED_TO_US",
                                  "status": "ok", "engine_codes": [], "review": [], "facts": facts,
                                  "matched_us_configurations": sorted({c["epa_model"] for c in configs if c["year"] in years_us and c["designation"] == des})}
                        target.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
                        written += 1
                        print(line.key, mod_text[:60], years_us, [(f["key"], f["value"]) for f in facts], flush=True)
    except Blocked as exc:
        print("STOPPED:", exc, flush=True)
        return 3
    print("documents", written, "requests", fetcher.requests, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
