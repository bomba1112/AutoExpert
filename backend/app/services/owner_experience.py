# ruff: noqa: E501
"""Owner materials and issue signals; never a population failure-rate estimator."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.schemas.research_evidence import OWNER_CLASSES as RELIABILITY_CLASSES
from app.services.knowledge_coverage import applicability, normalize_topic, stable_id

OWNER_CLASSES = RELIABILITY_CLASSES | {"FORUM", "MODEL_COMMUNITY", "PUBLIC_OWNER_LOG"}


@dataclass(frozen=True)
class SampleThresholds:
    small: int = 5
    useful: int = 20
    strong: int = 50

    def __post_init__(self):
        if not 0 < self.small < self.useful < self.strong:
            raise ValueError("Sample thresholds must increase")

    def quality(self, count):
        return (
            "VERY_SMALL"
            if count < self.small
            else "SMALL"
            if count < self.useful
            else "USEFUL"
            if count < self.strong
            else "STRONG"
        )


def canonical_material_url(url: str) -> str:
    p = urlsplit(str(url))
    host = p.netloc.casefold().removeprefix("www.").removeprefix("m.")
    query = [
        (k, v)
        for k, v in parse_qsl(p.query)
        if not k.startswith("utm_") and k not in {"page", "pagenum", "pagesize", "ref", "fbclid"}
    ]
    path = re.sub(r"/page-\d+/?$", "/", p.path)
    if host == "carcomplaints.com":
        path = re.sub(r"-\d+(?=\.shtml$)", "", path)
    return urlunsplit(("https", host, path.rstrip("/"), urlencode(sorted(query)), p.fragment))


def owner_applicability(target: dict, item: dict) -> str:
    scope = item.get("applicability", {})
    result = applicability(target, scope)
    if result != "MATCH":
        return result
    # New provider material cannot inherit an engine from its model-year page.
    if item.get("provenance", {}).get("method") and not scope.get("displacement"):
        return "UNRESOLVED"
    return "MATCH"


def deduplicate_materials(materials: list[dict], target: dict) -> list[dict]:
    """Merge reposts globally and repeat posts by the same identified owner/issue.

    Anonymous observations are never claimed to be verified distinct people.
    """
    kept, seen = [], set()
    for item in materials:
        if owner_applicability(target, item) != "MATCH":
            continue
        text = re.sub(r"\W+", " ", item.get("text", "").casefold()).strip()
        keys = {
            (
                "material",
                canonical_material_url(item["canonical_url"])
                if item.get("canonical_url")
                else item.get("material_id"),
            )
        }
        if item.get("content_hash"):
            keys.add(("content_hash", item["content_hash"]))
        if item.get("material_id"):
            keys.add(("material", item["material_id"]))
        if text:
            keys.add(("text", stable_id(text)))
        if item.get("repost_of"):
            reference = item["repost_of"]
            keys.add(
                (
                    "material",
                    canonical_material_url(reference)
                    if reference.startswith("http")
                    else reference,
                )
            )
        if item.get("owner_id"):
            keys.add(("owner_topic", item["owner_id"], item.get("issue_key") or item.get("topic")))
        keys.discard(("material", None))
        similar = False
        for previous in kept:
            a, b = set(previous.get("text_fingerprint", [])), set(item.get("text_fingerprint", []))
            if len(a) >= 10 and len(b) >= 10 and len(a & b) / min(len(a), len(b)) >= 0.88:
                similar = True
            old_text = re.sub(r"\W+", " ", previous.get("text", "").casefold()).strip()
            if (
                len(text) >= 100
                and len(old_text) >= 100
                and SequenceMatcher(None, text, old_text).ratio() >= 0.9
            ):
                similar = True
        if not keys or seen.intersection(keys) or similar:
            seen.update(keys)
            continue
        seen.update(keys)
        component = {
            "coolant_intrusion": "engine",
            "oil_consumption": "engine",
            "transmission_failure": "transmission",
        }.get(item.get("issue_key"))
        kept.append(
            {
                **item,
                "topic": component
                or normalize_topic(item.get("topic") or (item.get("topics") or ["other"])[0]),
            }
        )
    return kept


def owner_sample(
    materials: list[dict], target: dict, thresholds: SampleThresholds | None = None
) -> dict:
    rows = deduplicate_materials(
        [m for m in materials if m.get("evidence_class") in OWNER_CLASSES], target
    )
    topics = defaultdict(list)
    for row in rows:
        for topic in set(row.get("topics") or [row["topic"].upper()]):
            topics[topic].append(row)
    quality = (thresholds or SampleThresholds()).quality(len(rows))
    assert all(len(value) <= len(rows) for value in topics.values())
    return {
        "sample_size": len(rows),
        "unique_materials": len(rows),
        "known_unique_owners": len({row["owner_id"] for row in rows if row.get("owner_id")}),
        "owner_identity_complete": bool(rows) and all(row.get("owner_id") for row in rows),
        "source_count": len({row["publisher_group"] for row in rows}),
        "topic_mentions": {key: len(value) for key, value in topics.items()},
        "sample_quality": quality,
        "reliability_conclusion_allowed": quality != "VERY_SMALL",
        "show_share": False,
        "positive_topics": {
            key: sum(r.get("sentiment") == "POSITIVE" for r in value)
            for key, value in topics.items()
            if any(r.get("sentiment") == "POSITIVE" for r in value)
        },
        "negative_topics": {
            key: sum(r.get("sentiment") == "NEGATIVE" for r in value)
            for key, value in topics.items()
            if any(r.get("sentiment") == "NEGATIVE" for r in value)
        },
        "materials": rows,
        "limitations": ["SELF_SELECTED_SAMPLE", "NOT_FAILURE_RATE"]
        + (
            ["PROBLEM_SELECTED_SAMPLE"]
            if any(r.get("provenance", {}).get("selection_bias") for r in rows)
            else []
        ),
    }


def aggregate_issues(materials: list[dict], target: dict) -> dict:
    rows = deduplicate_materials(materials, target)
    groups = defaultdict(list)
    for row in rows:
        if row.get("issue_key"):
            groups[(row["topic"], row["issue_key"])].append(row)
    issues, signals = [], []
    for (component, key), reports in groups.items():
        official = [r for r in reports if r.get("evidence_class") == "MANUFACTURER_COMMUNICATION"]
        owners = [
            r
            for r in reports
            if r.get("evidence_class")
            in OWNER_CLASSES | {"OFFICIAL_COMPLAINT_DATABASE", "OFFICIAL_COMPLAINT"}
        ]
        publishers = {r["publisher_group"] for r in reports}
        owner_publishers = {r["publisher_group"] for r in owners}
        # An anonymous report or a repeated owner cannot establish independence.
        distinct_owners = {r["owner_id"] for r in owners if r.get("owner_id")}
        independent = len(owner_publishers) >= 2 and len(distinct_owners) >= 2
        supported = (
            bool(official) and (bool(distinct_owners) or len(owners) >= 2) and len(publishers) >= 2
        )
        if not (independent or supported):
            signals.append(
                {
                    "component": component,
                    "issue_key": key,
                    "strength": "WEAK_SIGNAL" if len(owners) > 1 else "SINGLE_REPORT",
                    "material_count": len(reports),
                    "promoted": False,
                    "source_count": len({sid for r in reports for sid in r.get("source_ids", [])}),
                    "independent_source_count": len(publishers),
                    "owner_material_count": sum(
                        r.get("evidence_class") in OWNER_CLASSES for r in reports
                    ),
                    "official_support": bool(official),
                    "applicability": [r["applicability"] for r in reports],
                }
            )
            continue
        evidence_ids = sorted({eid for r in reports for eid in r.get("evidence_ids", [])})
        if not evidence_ids or any(not r.get("evidence_ids") for r in reports):
            continue
        issues.append(
            {
                "id": stable_id([component, key, evidence_ids]),
                "component": component,
                "title": key,
                "documents": sorted({r["document_id"] for r in reports if r.get("document_id")}),
                "description": key,
                "affected_variants": reports[0]["applicability"],
                "affected_years": sorted(
                    {r["applicability"]["year"] for r in reports if r["applicability"].get("year")}
                ),
                "conditions": sorted(
                    {condition for r in reports for condition in r.get("conditions", [])}
                ),
                "typical_mileage_if_known": None,
                "symptoms": sorted({s for r in reports for s in r.get("symptoms", [])}),
                "severity": "MEDIUM",
                "evidence_ids": evidence_ids,
                "source_ids": sorted({sid for r in reports for sid in r.get("source_ids", [])}),
                "source_count": len({sid for r in reports for sid in r.get("source_ids", [])}),
                "independent_source_count": len(publishers),
                "owner_material_count": sum(
                    r.get("evidence_class") in OWNER_CLASSES for r in reports
                ),
                "official_complaint_count": sum(
                    r.get("evidence_class") in {"OFFICIAL_COMPLAINT", "OFFICIAL_COMPLAINT_DATABASE"}
                    for r in reports
                ),
                "official_support": bool(official),
                "applicability": [r["applicability"] for r in reports],
                # A single named anecdote cannot upgrade the previous qualified finding.
                "confidence": "HIGH" if supported and independent else "MEDIUM",
                "status": "CONFIRMED" if supported and independent else "ESTIMATE",
                "inspection_recommendation": component,
            }
        )
    return {"known_issues": issues, "signals": signals}


def fuel_layers(official: list[dict], owner_logs: list[dict], *, user: dict | None = None) -> dict:
    # Do not round US MPG before unit conversion. Explicitly exclude non-liquid fuels.
    unique = {stable_id(row): row for row in owner_logs}
    logs = [row for row in unique.values() if 0 < float(row.get("mpg") or 0) < 200]
    result = {
        "official": official,
        "owner_reported": {
            "sample_size": len(logs),
            "unique_materials": len(logs),
            "owner_identity_complete": False,
            "source_count": 1 if logs else 0,
            "status": "ESTIMATE" if len(logs) >= 5 else "INSUFFICIENT_DATA",
            "combined_l_100km": round(
                sum(235.214583 / float(row["mpg"]) for row in logs) / len(logs), 1
            )
            if len(logs) >= 5
            else None,
            "scope": "SELF_REPORTED_LOGS",
            "not_failure_rate": True,
        },
        "user_estimate": {"status": "INSUFFICIENT_DATA", "combined_l_100km": None},
    }
    if user and float(user.get("distance_km", 0)) > 0 and float(user.get("liters", 0)) > 0:
        result["user_estimate"] = {
            "status": "ESTIMATE",
            "combined_l_100km": round(100 * user["liters"] / user["distance_km"], 1),
            "inputs": user,
            "method": "100 * liters / distance_km",
        }
    return result
