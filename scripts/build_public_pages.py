# ruff: noqa: E501
"""Generate the public car pages (product phase, stage 5): a static site from the database, one
page per line -> generation -> engine in EN, RU, AZ, with indexes, sitemap.xml and robots.txt.
The output folder is what goes to the web server (never into git).

    python scripts/build_public_pages.py [--out C:/AutoExpertData/public_site] [--base https://...]
                                         [--makes toyota,honda] [--workers 8]

Runs only while the public_car_pages flag is on (preview / development by default). The database
is only read.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services import public_pages, us_tech_facts  # noqa: E402


def build_groups(groups: list[dict]) -> list[tuple[dict, dict]]:
    out = []
    with SessionLocal() as db:
        for group in groups:
            by_language = {}
            for language in public_pages.LANGUAGES:
                cards = {c["key"]: us_tech_facts.build(db, c["key"], language) for c in group["configs"]}
                by_language[language] = public_pages.merge(group, {k: v for k, v in cards.items() if v})
            out.append((group, by_language))
            us_tech_facts.clear_cache()
    return out


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=settings.public_site_dir)
    parser.add_argument("--base", default=settings.public_site_base_url)
    parser.add_argument("--app", default=settings.public_app_url)
    parser.add_argument("--makes", default="")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if not public_pages.enabled(settings):
        print("public_car_pages is off: nothing generated")
        return 1
    started = time.time()
    with SessionLocal() as db:
        groups = public_pages.groups(db, {m.strip().lower() for m in args.makes.split(",") if m.strip()} or None)
    chunks = [groups[i::args.workers] for i in range(args.workers)]
    pages = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(build_groups, [c for c in chunks if c]):
            pages.extend(result)
    pages.sort(key=lambda p: p[0]["path"])
    stats = public_pages.write_site(Path(args.out), pages, args.base, args.app)
    print(json.dumps({**stats, "groups": len(groups), "out": args.out, "seconds": round(time.time() - started)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
