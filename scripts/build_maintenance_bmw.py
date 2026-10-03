"""BMW maintenance: Condition Based Service (CBS) as the US owner's manuals describe it
(mycarusermanual.com copies of US editions; prompt stage B.2, on-board systems).

The manuals print no fixed intervals: "Condition Based Service CBS — Sensors and special
algorithms take into account the driving conditions … Condition Based Service recognizes the
maintenance requirements", and name the time-dependent work: "checking brake fluid and, if
needed, changing the engine oil and the microfilter/activated-charcoal filter". For US intervals
they refer to the Service and Warranty Information / Maintenance Booklet, which is not on disk.

Items: schedule_system CBS, one per job the manual names (engine oil and filter, cabin
microfilter: REPLACE; brake fluid: INSPECT), no interval (the system decides); a limit only if
the manual prints one (none found). Copies: tier B, SECONDARY_NOTE.

  .venv/Scripts/python.exe scripts/build_maintenance_bmw.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance_common import gen_for, generations_of, item, merge_years, norm, our_lines, page_text, write  # noqa: E402
from us_tech_common import WORK  # noqa: E402

CBS = re.compile(r"Condition Based Service(?: CBS)?", re.I)  # the system the manual names
# words broken by the layout ("proce‐ dures", "neces‐ sary", "mi‐ crofilter", "microfilter/ activated")
JOBS_SENTENCE = re.compile(r"time-dependent maintenance\s+pro[\S\s]{0,6}?dures, such as checking brake fluid and, if (?:needed|neces[\S\s]{0,4}?sary),"
                           r"\s+changing the engine oil and the\s+mi[\S\s]{0,4}?crofilter/\s*activated-charcoal filter", re.I)


def main() -> int:
    lines = our_lines("bmw")
    per_line, gaps, sources = defaultdict(list), defaultdict(list), {}
    for path in sorted((WORK / "bmw" / "extracted").glob("mcum-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        meta = doc["doc"]
        if doc.get("edition_market") != "US":
            continue
        pages = page_text(meta["sha256"])
        cbs = next(((i + 1, m.group(0)) for i, t in enumerate(pages) for m in [CBS.search(norm(t))] if m), None)
        jobs = next(((i + 1, m.group(0)) for i, t in enumerate(pages) for m in [JOBS_SENTENCE.search(norm(t))] if m), None)
        key = meta["key"]
        for line_key in meta["lines"]:
            slug = line_key.split("/")[1]
            if slug not in lines:
                continue
            years = [y for y in meta["years"] if lines[slug].years[0] <= y <= lines[slug].years[1]]
            if not cbs or not jobs:
                gaps[slug].append({"scope": f"bmw/{slug} MY{years[0] if years else ''}-{years[-1] if years else ''} ({key})",
                                   "field": "maintenance", "reason": "the manual copy does not describe the CBS jobs (or the page is missing)"})
                continue
            sources[key] = {"key": key, "kind": "pdf_pages", "path": "rawstore:" + Path(meta["path"]).as_posix().split("/raw/")[-1]
                            if "/raw/" in Path(meta["path"]).as_posix() else meta["path"],
                            "url": meta.get("url", ""), "page_url": meta.get("url", ""), "sha256": meta["sha256"],
                            "retrieved_at": meta["retrieved_at"], "tier": "B", "source_type": "OWNER_MANUAL_COPY",
                            "registry": "factory-bmw-us", "title": meta["title"], "publisher": meta["publisher"],
                            "authenticity": "REVIEWED_MIRROR", "edition": "US", "model_year": years[0] if years else None,
                            "extract": json.dumps({"pdf_sha256": meta["sha256"], "url": meta.get("url", ""),
                                                   "pages": {str(cbs[0]): pages[cbs[0] - 1], str(jobs[0]): pages[jobs[0] - 1]}},
                                                  ensure_ascii=False)}
            gens = generations_of("bmw", slug)
            for year in years:
                gen = gen_for(gens, year)
                if not gen:
                    continue
                for job, action in (("engine_oil_and_filter", "REPLACE"), ("cabin_air_filter", "REPLACE"), ("brake_fluid", "INSPECT")):
                    per_line[slug].append(item(slug, gen, year, job, action, system="CBS", source=key, quote=jobs[1], page=jobs[0],
                                               locator="Condition Based Service", display_level="SECONDARY_NOTE", confidence="MEDIUM",
                                               note="interval set by Condition Based Service (sensors and algorithms); the manual prints no fixed interval or limit"))
    for slug in lines:
        items = merge_years(per_line.get(slug, []))
        if items or gaps.get(slug):
            write("bmw", slug, "cbs", sources, items, gaps.get(slug, []))
            print("bmw", slug, "items", len(items), "gaps", len(gaps.get(slug, [])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
