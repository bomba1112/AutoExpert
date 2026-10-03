"""Collect the English buyer-facing texts to translate into Russian and Azerbaijani (owner
decision 2026-10-03: weak points - titles and symptoms, service campaigns - descriptions,
maintenance - job names; the original English is kept).

Reads the live database (read only) and the staging maintenance files; writes
  data_work/_shared/i18n/sources.json   one entry per distinct text: kind, sha256, text, rows
  data_work/_shared/i18n/terms.json     glossary candidates: NHTSA component segments, topics,
                                        maintenance service / condition labels, the terms the
                                        app already uses (seed for the single glossary)
Kinds:
  issue_title, issue_symptom, issue_inspection, issue_component      (known_issues)
  recall_summary, recall_component                                   (nhtsa_recall rows)
  maintenance_service, maintenance_condition, maintenance_qualifier  (applicability labels)

  .venv/Scripts/python.exe scripts/i18n_collect.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_work" / "_shared" / "i18n"
sys.path.insert(0, str(ROOT / "backend"))


def normalise(text: str) -> str:
    return " ".join(str(text or "").split())


def text_hash(text: str) -> str:
    return hashlib.sha256(normalise(text).encode("utf-8")).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect((ROOT / "autoexpert.db").resolve().as_uri() + "?mode=ro", uri=True)
    texts: dict[tuple[str, str], dict] = {}

    def add(kind: str, text) -> None:
        text = normalise(text)
        if not text:
            return
        key = (kind, text_hash(text))
        entry = texts.setdefault(key, {"kind": kind, "hash": key[1], "text": text, "rows": 0})
        entry["rows"] += 1

    for title, symptoms, inspection, component in db.execute(
            "select title, symptoms, inspection_recommendation, component from known_issues where scope_level is not null"):
        add("issue_title", title)
        add("issue_inspection", inspection)
        add("issue_component", component)
        for symptom in json.loads(symptoms or "[]"):
            add("issue_symptom", symptom)
    for (conditions,) in db.execute("select conditions from technical_evidence where fact_key='nhtsa_recall'"):
        cond = json.loads(conditions or "{}")
        add("recall_summary", cond.get("summary"))
        add("recall_component", cond.get("component"))
    for (applicability,) in db.execute("select applicability from maintenance_schedule_items"):
        app = json.loads(applicability or "{}")
        add("maintenance_service", app.get("service"))
        add("maintenance_condition", app.get("operating_condition"))
        for key in ("equipment", "oil_monitor", "brake_fluid_type", "schedule_table", "filter", "condition"):
            add("maintenance_qualifier", app.get(key))

    # glossary candidates
    terms = defaultdict(Counter)
    for (kind, _), entry in texts.items():
        text = entry["text"]
        if kind in ("issue_component", "recall_component"):
            for segment in text.split(":"):
                if segment.strip():
                    terms["nhtsa_component_segment"][segment.strip().upper()] += entry["rows"]
        elif kind == "issue_title":
            m = re.match(r"^(Manufacturer communication|Owners report(?: \(CarComplaints\.com\))?):\s*(.+)$", text)
            if m:
                terms["issue_topic"][m.group(2).strip()] += entry["rows"]
                for part in m.group(2).split(" / "):
                    terms["issue_topic_part"][part.strip()] += entry["rows"]
        elif kind == "issue_symptom":
            for part in text.split(" / "):
                terms["issue_topic_part"][part.strip()] += entry["rows"]
        elif kind.startswith("maintenance_"):
            terms[kind][text] += entry["rows"]
    from app.services import us_tech_facts as service  # the RU/AZ pairs the app already shows
    seed = {"maintenance_job": {k: list(v) for k, v in service.JOBS.items()},
            "maintenance_action": {k: list(v) for k, v in service.ACTIONS.items()},
            "severity": {k: list(v) for k, v in service.SEVERITY.items()},
            "probability": {k: list(v) for k, v in service.PROBABILITY.items()},
            "fact_label": {k: list(v) for k, v in service.LABELS.items()}}
    (OUT / "sources.json").write_text(json.dumps(sorted(texts.values(), key=lambda e: (e["kind"], -e["rows"], e["text"])),
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "terms.json").write_text(json.dumps({"candidates": {k: dict(v.most_common()) for k, v in terms.items()}, "app_seed": seed},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = Counter(e["kind"] for e in texts.values())
    chars = Counter()
    for e in texts.values():
        chars[e["kind"]] += len(e["text"])
    for k in sorted(kinds):
        print(f"{k}: {kinds[k]} texts, {chars[k]} chars")
    print({k: len(v) for k, v in terms.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
