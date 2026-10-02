"""Read-only baseline of Toyota rows in the live DB for the US tech database work.

Usage: .venv/Scripts/python.exe scripts/toyota_us_baseline.py [MAKE] > data_work/<make>/BASELINE.json
Opens the SQLite file through a read-only URI; never writes.
"""

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAKE = sys.argv[1] if len(sys.argv) > 1 else "Toyota"
LINES = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Prius"],
}
RELATED = {
    "Toyota": [
        "Prius Prime",
        "Prius c",
        "Prius v",
        "RAV4 Prime",
        "Corolla Cross",
        "Corolla Hatchback",
        "Corolla iM",
        "Camry Hybrid",
        "Highlander Hybrid",
        "RAV4 Hybrid",
        "Grand Highlander",
    ],
}


def main():
    con = sqlite3.connect(f"file:{(ROOT / 'autoexpert.db').as_posix()}?mode=ro", uri=True)
    con.execute("pragma query_only=on")
    q = lambda s, *a: con.execute(s, a).fetchall()
    make_id = q("select id from vehicle_makes where name=?", MAKE)[0][0]
    models = dict(q("select name, id from vehicle_models where make_id=?", make_id))
    out = {
        "make": MAKE,
        "lines": {},
        "related_models_present": [m for m in RELATED.get(MAKE, []) if m in models],
    }
    all_variant_ids = q(
        """select v.id from vehicle_variants v join vehicle_generations g on g.id=v.generation_id
        join vehicle_models m on m.id=g.model_id where m.make_id=?""",
        make_id,
    )
    out["make_totals"] = {
        "models": len(models),
        "generations": q(
            "select count(*) from vehicle_generations g join vehicle_models m on m.id=g.model_id where m.make_id=?",
            make_id,
        )[0][0],
        "variants": len(all_variant_ids),
    }
    for line in LINES.get(MAKE, []) + out["related_models_present"]:
        mid = models.get(line)
        if not mid:
            out["lines"][line] = None
            continue
        gens = []
        for gid, name, code, sy, ey, demo in q(
            "select id,name,code,start_year,end_year,is_demo from vehicle_generations where model_id=? order by start_year",
            mid,
        ):
            vs = q(
                "select id, year_from, market, data_origin, published_revision_id is not null, specifications from vehicle_variants where generation_id=?",
                gid,
            )
            src = Counter()
            years = [v[1] for v in vs if v[1]]
            for v in vs:
                c = json.loads(v[5] or "{}").get("catalog", {})
                src[
                    f"{c.get('source_registry_id')}|{v[2]}|{v[3]}|{'pub' if v[4] else 'unpub'}"
                ] += 1
            gens.append(
                {
                    "name": name,
                    "code": code,
                    "start_year": sy,
                    "end_year": ey,
                    "is_demo": bool(demo),
                    "variants": len(vs),
                    "variant_years": [min(years), max(years)] if years else None,
                    "by_source_market_origin": dict(src),
                }
            )
        vids = [
            r[0]
            for r in q(
                """select v.id from vehicle_variants v join vehicle_generations g on g.id=v.generation_id where g.model_id=?""",
                mid,
            )
        ]
        ph = ",".join("?" * len(vids)) or "''"
        in_range = q(
            f"select count(*) from vehicle_variants where id in ({ph}) and market='US' and year_from between 2014 and 2026",
            *vids,
        )[0][0]
        facts = Counter()
        for (spec,) in q(
            f"select specifications from vehicle_variants where id in ({ph}) and market='US' and year_from between 2014 and 2026",
            *vids,
        ):
            for k in json.loads(spec or "{}").get("catalog", {}).get("facts") or {}:
                facts[k] += 1
        out["lines"][line] = {
            "generations": gens,
            "us_variants_my2014_2026": in_range,
            "fact_keys_us_my2014_2026": dict(facts.most_common()),
            "technical_evidence_by_category": dict(
                q(
                    f"select category, count(*) from technical_evidence where vehicle_variant_id in ({ph}) group by 1",
                    *vids,
                )
            ),
            "recall_evidence": q(
                f"select count(*) from technical_evidence where vehicle_variant_id in ({ph}) and json_extract(conditions,'$.campaign_number') is not null",
                *vids,
            )[0][0],
            "commercial_fact_claims_by_status": dict(
                q(
                    f"select reuse_status, count(*) from commercial_fact_claims where variant_id in ({ph}) group by 1",
                    *vids,
                )
            ),
            "commercial_ok_fact_names": dict(
                q(
                    f"select fact_name, count(*) from commercial_fact_claims where variant_id in ({ph}) and reuse_status='COMMERCIAL_OK' group by 1",
                    *vids,
                )
            ),
            "known_issues": q(
                f"select count(*) from known_issues where vehicle_variant_id in ({ph})", *vids
            )[0][0],
            "owner_evidence": q(
                f"select count(*) from owner_evidence where vehicle_variant_id in ({ph})", *vids
            )[0][0],
            "documentary_sections": q(
                f"select count(*) from vehicle_variants where id in ({ph}) and json_array_length(json_extract(specifications,'$.catalog.documentary_sections'))>0",
                *vids,
            )[0][0],
        }
    out["raw_documents_factory_source"] = q(
        "select count(*) from raw_documents where source_id=?", f"factory-{MAKE.lower()}-us"
    )[0][0]
    out["table_totals"] = {
        t: q(f"select count(*) from {t}")[0][0]
        for t in (
            "vehicle_generations",
            "vehicle_variants",
            "technical_evidence",
            "commercial_fact_claims",
            "known_issues",
            "source_records",
            "raw_documents",
            "catalog_revisions",
            "knowledge_import_jobs",
        )
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
