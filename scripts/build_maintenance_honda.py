"""Honda maintenance items (Maintenance Minder) from the official US owner's manuals
(techinfo.honda.com, manifest data_work/_shared/manifest_official/techinfo.honda.com.csv).

Honda prints no mileage schedule for these lines: the owner's manual's "Maintenance Minder"
chapter lists what each Minder code stands for ("CODE Maintenance Main Items": A, B; "CODE
Maintenance Sub Items": 1-7). Every job of a code becomes one MAINTENANCE_MINDER item with
applicability {"minder_code": ..., "edition": ...}; the "Inspect these items:" sub-bullets of B
are INSPECT items of code B. No interval is invented: an item carries a maximum only where the
manual states one in its footnote ("*1: If a Maintenance Minder message does not appear more
than 12 months after the display is reset, change the engine oil every year" -> max 12 months;
"*5: ... change the brake fluid every 3 years" -> max 36 months). Fixed intervals that the manual
states outside the Minder are FIXED_INTERVAL items: "Independent of the Maintenance Minder
information, replace the brake fluid every 3 years", "Inspect idle speed every 160,000 miles",
and the severe-use footnotes (dusty conditions: air cleaner element every 15,000 miles; soot:
dust and pollen filter; mountainous driving / towing: transmission fluid) as condition SEVERE.
Only the "U.S. models" table is used when a manual prints a Canadian one too (codes 0/9).

The warranty basebooks (owners.honda.com) were checked: they refer to the Maintenance Minder
and print no schedule.

Output: data_work/honda/staging/<line>/maintenance_minder.json (maintenance_common.write).

  .venv/Scripts/python.exe scripts/build_maintenance_honda.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_maintenance_nissan import jobs_of as nissan_jobs  # noqa: E402
from maintenance_common import (  # noqa: E402
    gen_for,
    generations_of,
    item,
    merge_years,
    miles_to_km,
    norm,
    our_lines,
    page_text,
    pdf_source,
    write,
)
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MAKE = "honda"
NAME = "minder"
REGISTRY = "factory-honda-us"
MANIFEST = WORK / "_shared" / "manifest_official" / "techinfo.honda.com.csv"
HONDA_JOBS = [  # tried before the shared vocabulary
    ("engine_oil", r"replace engine oil(?!.*filter)"),
    ("parking_brake", r"parking brake"),
    ("idle_speed", r"idle speed"),
]
VERB = re.compile(r"(?:Replace|Inspect|Rotate|Check|Service|Adjust|Clean)\b")
FOOTNOTE = re.compile(r"\*(\d):\s*(.*?)(?=\s\*\d:\s|\s#\s*:|\sCODE Maintenance|\s[AB0-9]\s*●|\s\d+\s+uuMaintenance|$)")


def jobs_of(text: str) -> list[str]:
    clean = re.sub(r"\*\d*|#", " ", text)
    for job, pattern in HONDA_JOBS:
        if re.search(pattern, clean, re.I):
            return [job]
    return nissan_jobs(clean)


def action_of(text: str, default: str | None) -> str | None:
    t = text.strip().lower()
    for verb, action in (("rotate", "ROTATE"), ("replace", "REPLACE"), ("change", "REPLACE"), ("inspect", "INSPECT"),
                         ("check", "INSPECT"), ("adjust", "ADJUST"), ("clean", "CLEAN")):
        if t.startswith(verb):
            return action
    return default


def documents() -> list[dict]:
    lines = our_lines(MAKE)
    docs = []
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["status"] != "ok" or row["doc_type"] != "owners_manual" or not row["path"].startswith("official/honda/"):
                continue
            title = row["title"]
            edition = re.sub(r"\(.*?\)", " ", title)
            edition = re.sub(r"^\d{4}\s+|\s+Owner's Manual.*$", "", " ".join(edition.split()))
            docs.append({"key": "official-" + hashlib.sha1(row["url"].encode()).hexdigest()[:12],
                         "lines": [ln for ln in row["lines"].split(";") if ln in lines],
                         "years": [int(y) for y in row["years"].split(";") if y], "title": title, "url": row["url"],
                         "path": RAW_ROOT / row["path"], "sha256": row["sha256"], "retrieved_at": row["retrieved_at"],
                         "edition": edition.lower()})
    return docs


def interval_text(text: str) -> dict | None:
    """'every 15,000 miles (24,000 km)', 'every 2 years or 30,000 miles (48,000 km), whichever comes first'."""
    m = re.search(r"every (?:(?P<y>\d+) years? or )?(?P<mi>[\d,]+) miles \((?P<km>[\d,]+) km\)", text)
    if m:
        miles = int(m.group("mi").replace(",", ""))
        months = int(m.group("y")) * 12 if m.group("y") else None
        return {"interval_km": int(m.group("km").replace(",", "")), "interval_miles_original": miles, "interval_months": months,
                "rule": "WHICHEVER_FIRST" if months else None, "matched": m.group(0)}
    m = re.search(r"every (?P<y>\d+) years", text)
    if m:
        return {"interval_km": None, "interval_miles_original": None, "interval_months": int(m.group("y")) * 12, "rule": None,
                "matched": m.group(0)}
    return None


def us_section(text: str) -> str | None:
    """The U.S. part of a Maintenance Service Items page (None for a Canadian-only page)."""
    if "Canadian models" in text and "U.S. models" not in text:
        return None
    if "U.S. models" in text and "Canadian models" in text:
        return text[text.index("U.S. models"): text.index("Canadian models")]
    return text


class Builder:
    def __init__(self):
        self.lines = our_lines(MAKE)
        self.entries = defaultdict(list)  # line -> entries
        self.gaps = defaultdict(list)
        self.docs, self.texts, self.pages = {}, {}, defaultdict(set)

    def years_of(self, doc, line):
        lo, hi = self.lines[line].years
        return [y for y in doc["years"] if lo <= y <= hi]

    def gap(self, doc, field, reason):
        for line in doc["lines"]:
            ys = self.years_of(doc, line)
            if ys:
                self.gaps[line].append({"scope": f"{MAKE}/{line} MY{ys[0]}" + (f"-{ys[-1]}" if len(ys) > 1 else "") + f" ({doc['key']})",
                                        "field": f"maintenance:{field}", "reason": reason})

    def add(self, doc, page, job, action, quote, locator, *, system="MAINTENANCE_MINDER", condition="NORMAL", iv=None,
            max_iv=None, applicability=None, note=None):
        if norm(quote) not in norm(self.texts[doc["key"]][page - 1]):
            raise SystemExit(f"quote not on page {doc['key']} p.{page}: {quote}")
        self.pages[doc["key"]].add(page)
        for line in doc["lines"]:
            self.entries[line].append({"doc": doc, "page": page, "job": job, "action": action, "quote": norm(quote),
                                       "locator": locator, "system": system, "condition": condition, "iv": iv,
                                       "max_iv": max_iv, "app": applicability or {}, "note": note})

    def doc(self, doc):
        texts = page_text(doc["sha256"])
        self.texts[doc["key"]], self.docs[doc["key"]] = texts, doc
        pages = [i for i, t in enumerate(texts) if re.search(r"CODE\s+Maintenance\s+(?:Main|Sub)\s+Items", t)]
        if not pages:
            self.gap(doc, "schedule", "no Maintenance Minder service-item table found in the owner's manual")
            return
        seen = set()
        fixed_seen = set()
        for index in pages:
            text = texts[index]
            section = us_section(text)
            if section is None:
                continue
            flat = norm(section)
            notes = {int(m.group(1)): m.group(2).strip() for m in FOOTNOTE.finditer(flat)}
            code, bullet, in_codes, sub_mode = None, None, False, False
            found = []
            for raw in section.splitlines():
                ln = raw.strip()
                if not ln:
                    continue
                if re.match(r"^\*\d:|^#\s*:|^\*\s+Not available|.*\.book\s|^Adjust the valves", ln) or re.match(r"^CODE\s+Maintenance", ln):
                    bullet, sub_mode = None, False
                    if ln.startswith("CODE"):
                        code, in_codes = None, True
                    elif not ln.startswith("Adjust"):
                        code = None
                    continue
                # 'B ● Replace ...' (2014-2025 layout) or 'A Replace engine oil*1' / a code alone on its line (2026)
                m = re.match(r"^([AB]|[0-9])(?:\s*●\s*|\s+|$)(.*)$", ln)
                if in_codes and m and ("●" in ln[:4] or not m.group(2) or re.match(VERB, m.group(2))):
                    code, sub_mode = m.group(1), False
                    bullet = {"code": code, "text": m.group(2).strip(), "sub": False} if m.group(2).strip() else None
                    if bullet:
                        found.append(bullet)
                        sub_mode = bool(re.match(r"Inspect these items", bullet["text"]))
                    continue
                if code is None:
                    continue
                if ln.startswith("●") or re.match(VERB, ln):
                    bullet = {"code": code, "text": ln.lstrip("● ").strip(), "sub": False}
                    found.append(bullet)
                    sub_mode = bool(re.match(r"Inspect these items", bullet["text"]))
                    continue
                if ln.startswith("•") or (sub_mode and re.match(r"^[A-Z]", ln)):
                    bullet = {"code": code, "text": ln.lstrip("• ").strip(), "sub": True}
                    found.append(bullet)
                    continue
                if bullet is not None and re.match(r"^[a-z(]", ln):
                    bullet["text"] += " " + ln
            for b in found:
                text_b = re.split(r"\s\*\d:\s", b["text"])[0].strip()
                if re.match(r"^Inspect these items:?$", text_b, re.I):
                    continue
                action = action_of(text_b, "INSPECT" if b["sub"] else None)
                jobs = jobs_of(text_b)
                if not jobs or action is None:
                    continue
                if re.search(r"during services|if they are noisy", text_b, re.I):
                    continue  # conditional adjustment, not a Minder job
                refs = [int(n) for n in re.findall(r"\*(\d)", text_b)]
                max_iv, extra_note, severe = None, None, []
                for n in refs:
                    note_text = notes.get(n, "")
                    if re.search(r"does not appear more than \d+ months", note_text):
                        iv = interval_text(note_text) or ({"interval_months": 12, "matched": "every year"}
                                                          if re.search(r"every year", note_text) else None)
                        if iv:
                            max_iv = {"interval_km": None, "interval_months": iv["interval_months"]}
                            extra_note = f"maximum as printed: {note_text}"
                    elif interval_text(note_text):
                        severe.append((n, note_text))
                for job in jobs:
                    key = (b["code"], job, action)
                    if key in seen:
                        continue
                    seen.add(key)
                    self.add(doc, index + 1, job, action, text_b,
                             f"p.{index + 1} Maintenance Minder code {b['code']}: {text_b}"[:480],
                             max_iv=max_iv, applicability={"minder_code": b["code"], "edition": doc["edition"]},
                             note=extra_note)
                    for n, note_text in severe:
                        iv = interval_text(note_text)
                        fkey = ("severe", job, n, iv["interval_km"], iv["interval_months"])
                        if fkey in fixed_seen:
                            continue
                        fixed_seen.add(fkey)
                        q = next((norm(m.group(0)) for m in [re.search(r"[^.]*" + re.escape(iv["matched"]) + r"[^.]*\.?", note_text)] if m), note_text)
                        if norm(q) not in flat:
                            q = iv["matched"]
                        self.add(doc, index + 1, job, "REPLACE", q, f"p.{index + 1} footnote *{n} of Minder code {b['code']}",
                                 system="FIXED_INTERVAL", condition="SEVERE", iv=iv,
                                 applicability={"edition": doc["edition"]}, note=f"condition as printed: {note_text}"[:400])
            # stated outside the Minder (side column of the same page)
            for pattern, job, action in ((r"Independent of the Maintenance Minder information, replace the brake fluid every \d+ years\.?",
                                          "brake_fluid", "REPLACE"),
                                         (r"Inspect idle speed every [\d,]+ miles \([\d,]+ km\)\.?", "idle_speed", "INSPECT")):
                m = re.search(pattern, flat)
                if m and (job, "fixed") not in fixed_seen:
                    fixed_seen.add((job, "fixed"))
                    self.add(doc, index + 1, job, action, m.group(0), f"p.{index + 1} Maintenance Service Items (side note)",
                             system="FIXED_INTERVAL", iv=interval_text(m.group(0)), applicability={"edition": doc["edition"]})

    def finish(self) -> None:
        for slug in sorted(self.lines):
            gens = generations_of(MAKE, slug)
            by_scope = defaultdict(list)
            for e in self.entries.get(slug, []):
                for year in self.years_of(e["doc"], slug):
                    gen = gen_for(gens, year)
                    if gen is None:
                        continue
                    key = (year, gen, e["job"], e["action"], e["condition"], e["system"], json.dumps(e["app"], sort_keys=True))
                    by_scope[key].append(e)
            items = []
            for key, es in by_scope.items():
                year, gen = key[0], key[1]
                variants = {json.dumps([e["iv"] and (e["iv"]["interval_km"], e["iv"]["interval_months"]),
                                        e["max_iv"] and e["max_iv"]["interval_months"]]) for e in es}
                if len(variants) > 1:
                    self.gaps[slug].append({"scope": f"{MAKE}/{slug} MY{year}", "field": f"maintenance:{key[2]}",
                                            "reason": f"{key[3]} {key[4]} {key[6]}: the manuals give different values {sorted(variants)}; not written"})
                    continue
                e0 = es[0]
                iv = {k: v for k, v in (e0["iv"] or {}).items() if k != "matched"}
                it = item(slug, gen, year, e0["job"], e0["action"], condition=e0["condition"], system=e0["system"], interval=iv,
                          applicability=e0["app"], note=e0["note"], max_interval=e0["max_iv"], source=e0["doc"]["key"],
                          quote=e0["quote"], page=e0["page"], locator=e0["locator"])
                for e in es[1:]:
                    cite = {"source": e["doc"]["key"], "quote": e["quote"], "pages": [e["page"]], "locator": e["locator"]}
                    if cite not in it["cites"] and len(it["cites"]) < 4:
                        it["cites"].append(cite)
                items.append(it)
            merged = merge_years(items)
            used = {c["source"] for it in merged for c in it["cites"]}
            sources = {}
            for key in used:
                doc = self.docs[key]
                pages = {p for it in merged for c in it["cites"] if c["source"] == key for p in c["pages"]}
                sources[key] = pdf_source(key, doc["path"], doc["sha256"], doc["url"], doc["title"],
                                          "honda (manufacturer domain techinfo.honda.com)", REGISTRY, doc["years"], pages,
                                          doc["retrieved_at"], source_type="OWNER_MANUAL_OFFICIAL")
            gaps = list({json.dumps(g, sort_keys=True): g for g in self.gaps.get(slug, [])}.values())
            out = write(MAKE, slug, NAME, sources, merged, gaps)
            years = sorted({y for it in merged for y in range(it["years"][0], it["years"][1] + 1)})
            print(f"{MAKE}/{slug}: items {len(merged)}, years {years[0] if years else '-'}-{years[-1] if years else '-'} "
                  f"({len(years)}), sources {len(sources)}, gaps {len(gaps)} -> {out.relative_to(WORK.parent)}", flush=True)


def self_check() -> tuple[int, int]:
    checked = problems = 0
    for path in sorted((WORK / MAKE / "staging").glob(f"*/maintenance_{NAME}.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cache = {}
        for it in data["items"]:
            assert it["schedule_system"] in ("FIXED_INTERVAL", "MAINTENANCE_MINDER")
            assert it["action"] in ("REPLACE", "INSPECT", "ROTATE", "ADJUST", "CLEAN")
            if it["schedule_system"] == "FIXED_INTERVAL" and not (it["interval_km"] or it["interval_months"]):
                problems += 1
                print("PROBLEM no interval", it["id"])
            if it["interval_km"] is not None and not (1000 <= it["interval_km"] <= 400000):
                problems += 1
                print("PROBLEM interval_km", it["id"])
            for c in it["cites"]:
                src = data["sources"][c["source"]]
                if src["sha256"] not in cache:
                    cache[src["sha256"]] = page_text(src["sha256"])
                for p in c["pages"]:
                    checked += 1
                    if norm(c["quote"]) not in norm(cache[src["sha256"]][p - 1]):
                        problems += 1
                        print("PROBLEM", path.parent.name, it["id"], c["source"], p, c["quote"][:80])
    return checked, problems


def main() -> int:
    builder = Builder()
    for doc in documents():
        if doc["lines"]:
            builder.doc(doc)
    builder.finish()
    checked, problems = self_check()
    print(f"checked {checked}, problems {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
