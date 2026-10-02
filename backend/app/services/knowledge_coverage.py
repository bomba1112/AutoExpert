# ruff: noqa: E501
"""Language-independent coverage, applicability, contradictions and research planning.

Scores describe evidence coverage, never reliability or a vehicle's condition.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict

DEPTH_VERSION = "0.7.0-buyer2"
TOPICS = {
    "identity": ["make", "model", "year", "market", "body", "trim", "drivetrain", "generation"],
    "engine": [
        "identity",
        "code",
        "displacement",
        "cylinders",
        "aspiration",
        "injection",
        "timing",
        "fuel",
        "oil",
        "cooling",
        "known_issues",
        "maintenance",
        "symptoms",
        "inspection",
    ],
    "transmission": [
        "type",
        "code",
        "gears",
        "service",
        "fluid",
        "known_issues",
        "symptoms",
        "inspection",
    ],
    "suspension": ["construction", "weak_areas", "conditions", "symptoms", "inspection"],
    "steering": ["construction", "weak_areas", "conditions", "symptoms", "inspection"],
    "brakes": ["construction", "weak_areas", "conditions", "symptoms", "inspection"],
    "body": ["construction", "corrosion", "inspection"],
    "electrical": ["architecture", "weak_areas", "inspection"],
    "fuel_consumption": ["official", "owner_reported", "user_estimate"],
    "owner_experience": ["sample", "topics", "applicability"],
    "maintenance": ["schedule", "fluids", "conditions"],
}
CAPABILITY_TOPICS = {
    "technical_bulletins": {"engine", "transmission", "electrical"},
    "maintenance_specs": {"engine", "transmission", "steering", "maintenance"},
    "technical_specs": {
        "engine",
        "transmission",
        "suspension",
        "steering",
        "brakes",
        "body",
        "electrical",
        "maintenance",
    },
    "fuel_economy": {"engine", "transmission", "fuel_consumption"},
    "owner_experience": {"owner_experience", "fuel_consumption"},
}
ALIASES = {
    "power train": "transmission",
    "powertrain": "transmission",
    "gearbox": "transmission",
    "service brakes": "brakes",
    "service brakes, hydraulic": "brakes",
    "electrical system": "electrical",
    "structure": "body",
    "fuel economy": "fuel_consumption",
    "engine and engine cooling": "engine",
}


def normalize_topic(value: str) -> str:
    key = " ".join(value.casefold().replace("_", " ").split())
    return ALIASES.get(key, key.replace(" ", "_"))


def stable_id(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:24]


def normalize_value(value: object) -> str:
    return re.sub(r"[^a-z0-9.]", "", str(value).casefold())


def applicability(target: dict, scope: dict) -> str:
    """Unknown discriminators never establish an exact match. Mismatches are rejected."""
    from app.services.vehicle_identity import dimensions_equal

    target = {
        **target,
        "powertrain_type": target.get("powertrain_type") or target.get("powertrain"),
    }
    scope = {**scope, "powertrain_type": scope.get("powertrain_type") or scope.get("powertrain")}
    matched = True
    for field in (
        "make",
        "model",
        "year",
        "market",
        "generation",
        "engine_code",
        "engine",
        "transmission",
        "displacement",
        "cylinders",
        "drivetrain",
        "fuel",
        "powertrain_type",
        "trim",
        "vin",
    ):
        expected = scope.get(field)
        if expected in ("UNKNOWN", "UNRESOLVED"):
            matched = False
            continue
        if expected in (None, ""):
            continue
        actual = target.get(field)
        if actual in (None, "", "UNRESOLVED", "UNKNOWN"):
            matched = False
        elif field == "displacement":
            if abs(float(actual) - float(expected)) > 0.06:
                return "MISMATCH"
        elif not dimensions_equal(field, actual, expected):
            return "MISMATCH"
    if scope.get("years") and target.get("year") not in scope["years"]:
        return "MISMATCH" if target.get("year") else "UNRESOLVED"
    if not all(scope.get(key) for key in ("make", "model", "market")):
        matched = False
    return "MATCH" if matched else "UNRESOLVED"


def synthesize_facts(facts: list[dict], target: dict) -> tuple[list[dict], list[dict]]:
    from app.services.vehicle_identity import applicability_class

    grouped = defaultdict(list)
    for fact in facts:
        if applicability(target, fact.get("applicability", {})) == "MISMATCH":
            continue
        fact = dict(fact)
        fact.setdefault(
            "applicability_class",
            applicability_class(fact.get("applicability", {}), exact=fact.get("exact_vin", False)),
        )
        if not fact.get("evidence_ids") or not fact.get("source_ids"):
            continue
        if (
            applicability(target, fact.get("applicability", {})) == "UNRESOLVED"
            and fact.get("status") == "CONFIRMED"
        ):
            fact["status"] = "ESTIMATE"
        grouped[(normalize_topic(fact["topic"]), fact["subtopic"])].append(fact)
    findings, contradictions = [], []
    for (topic, subtopic), items in sorted(grouped.items()):
        by_value = defaultdict(list)
        for item in items:
            from app.services.vehicle_identity import dimensions_equal

            value_key = normalize_value(item["value"])
            if subtopic in {"drivetrain", "fuel"}:
                value_key = next(
                    (
                        key
                        for key, values in by_value.items()
                        if dimensions_equal(subtopic, values[0]["value"], item["value"])
                    ),
                    value_key,
                )
            by_value[value_key].append(item)
        conflict = len(by_value) > 1
        exact = [
            item for item in items if item.get("exact_vin") and item.get("authority") in {"A", "B"}
        ]
        exact_values = {normalize_value(item["value"]) for item in exact}
        # A decoder disagreement with an explicitly matched configuration is a
        # critical conflict, not permission to silently select the decoder value.
        variant_disagreement = any(i.get("applicability_class") == "EXACT_VARIANT" for i in items)
        critical = topic in {"identity", "engine", "transmission"}
        oem = [i for i in items if i.get("authority") == "OEM_VIN"]
        resolved = conflict and (
            len({normalize_value(i["value"]) for i in oem}) == 1
            or (len(exact_values) == 1 and not (critical and variant_disagreement))
        )
        chosen = oem if resolved and oem else exact if resolved else items
        status = (
            "INSUFFICIENT_DATA"
            if conflict and not resolved
            else (
                "CONFIRMED"
                if any(item.get("status") == "CONFIRMED" for item in chosen)
                else "ESTIMATE"
                if any(item.get("status") == "ESTIMATE" for item in chosen)
                else "NEEDS_INSPECTION"
                if any(item.get("status") == "NEEDS_INSPECTION" for item in chosen)
                else "INSUFFICIENT_DATA"
            )
        )
        evidence_ids = sorted({eid for item in items for eid in item["evidence_ids"]})
        chosen_eids = sorted({eid for item in chosen for eid in item["evidence_ids"]})
        finding = {
            "id": stable_id([topic, subtopic, evidence_ids]),
            "topic": topic,
            "subtopic": subtopic,
            "value": chosen[0]["value"] if status != "INSUFFICIENT_DATA" else None,
            "status": status,
            "evidence_ids": chosen_eids,
            "source_ids": sorted({sid for item in chosen for sid in item["source_ids"]}),
            "applicability": chosen[0].get("applicability", {}),
            "scope": chosen[0].get("scope", "MODEL_CONFIGURATION"),
            "applicability_class": chosen[0]["applicability_class"],
        }
        findings.append(finding)
        if conflict:
            contradictions.append(
                {
                    "finding_id": finding["id"],
                    "topic": topic,
                    "subtopic": subtopic,
                    "alternatives": [
                        {
                            "value": item["value"],
                            "evidence_ids": item["evidence_ids"],
                            "source_ids": item["source_ids"],
                        }
                        for item in items
                    ],
                    "resolution": "OEM_VIN_AUTHORITY"
                    if resolved and oem
                    else "EXACT_VIN_AUTHORITY"
                    if resolved
                    else "UNRESOLVED",
                    "evidence_ids": evidence_ids,
                }
            )
    return findings, contradictions


def coverage(findings: list[dict]) -> dict:
    values = {(item["topic"], item["subtopic"]): item for item in findings}
    result = {}
    weights = {"CONFIRMED": 1, "ESTIMATE": 0.5, "NEEDS_INSPECTION": 0.25, "INSUFFICIENT_DATA": 0}
    for topic, subtopics in TOPICS.items():
        states = {
            sub: values.get((topic, sub), {}).get("status", "INSUFFICIENT_DATA")
            for sub in subtopics
        }
        score = sum(weights[status] for status in states.values()) / len(states)
        result[topic] = {
            "subtopics": states,
            "coverage": round(score, 3),
            "status": "CONFIRMED" if score == 1 else "ESTIMATE" if score else "INSUFFICIENT_DATA",
        }
    return result


def research_plan(
    state: dict, registry, market: str, completed: set[str] | None = None
) -> list[dict]:
    steps = []
    for capability, topics in CAPABILITY_TOPICS.items():
        missing = [
            f"{topic}.{sub}"
            for topic in sorted(topics)
            for sub, status in state[topic]["subtopics"].items()
            if status == "INSUFFICIENT_DATA"
        ]
        if not missing or capability in (completed or set()):
            continue
        candidates = registry.for_capability(market=market, capability=capability)
        steps.append(
            {
                "capability": capability,
                "missing_topics": missing,
                "candidate_sources": [item.definition.id for item in candidates],
                "status": "PLANNED" if candidates else "UNAVAILABLE",
                "stages": [
                    "retrieval",
                    "normalization",
                    "deduplication",
                    "applicability",
                    "contradiction_check",
                    "synthesis",
                ],
            }
        )
    return steps
