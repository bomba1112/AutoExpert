# ruff: noqa: E501
"""Persisted enrichment of the existing profile, with field-level provenance."""

from __future__ import annotations

import re

from app.models.enums import ConfidenceLevel, DataOrigin, EvidenceCategory, EvidenceStatus
from app.models.evidence import TechnicalEvidence
from app.services.knowledge_coverage import DEPTH_VERSION, coverage, synthesize_facts
from app.services.owner_experience import aggregate_issues, fuel_layers, owner_sample
from app.services.vehicle_identity import (
    applicability_class,
    identity_target,
    integrity_from_findings,
    powertrain_type,
)

IDENTITY_FIELDS = {
    "vin": ("identity", "vin"),
    "make": ("identity", "make"),
    "model": ("identity", "model"),
    "model_year": ("identity", "year"),
    "body_class": ("identity", "body"),
    "trim": ("identity", "trim"),
    "doors": ("identity", "doors"),
    "seats": ("identity", "seats"),
    "engine_model": ("engine", "code"),
    "displacement_l": ("engine", "displacement"),
    "engine_cylinders": ("engine", "cylinders"),
    "engine_hp": ("engine", "engine_power_hp"),
    "engine_kw": ("engine", "engine_power_kw"),
    "battery_type": ("engine", "battery_type"),
    "battery_kwh": ("engine", "battery_capacity_kwh"),
    "drive_type": ("identity", "drivetrain"),
    "fuel_type_primary": ("engine", "fuel"),
}


def scope_for(request) -> dict:  # noqa: ANN001
    return {
        "make": request.make,
        "model": request.model,
        "year": request.year,
        "market": request.market,
    }


def selected_epa(result, identity: dict) -> dict | None:  # noqa: ANN001
    from app.providers.knowledge_public import _matches_identity

    if not result or result.error:
        return None
    if identity.get("selected_epa_id"):
        return next(
            (r for r in result.records if str(r.get("id")) == str(identity["selected_epa_id"])),
            None,
        )
    if len(result.records) != 1:
        return None
    row = result.records[0]
    # A model name alone never resolves a VIN configuration.
    if not identity.get("displacement_l") or not identity.get("engine_cylinders"):
        return None
    return row if _matches_identity(row, identity) else None


def enrich_profile(db, profile, request, results, sources: dict, plan: list[dict]) -> int:  # noqa: ANN001
    identity = next(item for item in results if item.capability == "vehicle_identity").records[0]
    base_scope = scope_for(request)
    epa_result = next((r for r in results if r.capability == "fuel_economy" and not r.error), None)
    epa = selected_epa(epa_result, identity)
    target = identity_target(request, identity, epa)
    facts, provenance = [], {}

    def fact(
        topic, subtopic, value, capability, locator, *, scope=None, status="CONFIRMED", exact=False
    ):  # noqa: ANN001, ANN202
        if value in (None, "", "Not Applicable", "UNRESOLVED") or capability not in sources:
            return
        from app.services.knowledge_coverage import applicability

        scope = dict(scope or base_scope)
        if exact:
            scope = {**scope, "vin": request.vin}
        classification = applicability_class(scope, exact=exact)
        if applicability(target, scope) == "MISMATCH":
            return
        # Model-wide technical data is context, never proof of this powertrain.
        if topic in {"engine", "transmission"} and classification not in {
            "EXACT_VIN",
            "EXACT_VARIANT",
        }:
            status = "ESTIMATE" if status == "CONFIRMED" else status
        source = sources[capability]
        result = next(
            item for item in reversed(results) if item.capability == capability and not item.error
        )
        category = topic if topic in {e.value for e in EvidenceCategory} else "other"
        item = TechnicalEvidence(
            vehicle_variant_id=profile.vehicle_variant_id,
            source_id=source.id,
            category=EvidenceCategory(category),
            title=f"{topic}.{subtopic}",
            statement=str(value),
            status=EvidenceStatus(status),
            confidence=ConfidenceLevel.HIGH if status == "CONFIRMED" else ConfidenceLevel.MEDIUM,
            market="US",
            conditions={
                "section_key": topic,
                "consumer_kind": "knowledge_fact",
                "topic": topic,
                "subtopic": subtopic,
                "value": value,
                "locator": locator,
                "applicability": scope,
                "applicability_class": classification,
                "provider_id": result.provider_id,
            },
            data_origin=DataOrigin.REAL,
            is_demo=False,
        )
        db.add(item)
        db.flush()
        profile.evidence.append(item)
        atom = {
            "topic": topic,
            "subtopic": subtopic,
            "value": value,
            "status": status,
            "applicability": scope,
            "applicability_class": classification,
            "exact_vin": exact,
            "authority": "A" if capability == "technical_specs" else "B",
            "source_ids": [source.id],
            "evidence_ids": [item.id],
            "scope": "VIN" if exact else "MODEL_CONFIGURATION",
        }
        facts.append(atom)
        provenance[item.id] = {
            "source_id": source.id,
            "provider_id": result.provider_id,
            "retrieved_at": result.retrieved_at.isoformat(),
            "url": locator.get("url") or result.source_url,
            "locator": locator,
            "raw": result.raw_payload,
        }

    for key, (topic, subtopic) in IDENTITY_FIELDS.items():
        if request.vin or key in {"make", "model", "model_year"}:
            fact(
                topic,
                subtopic,
                identity.get(key),
                "vehicle_identity",
                {"field": key},
                exact=bool(request.vin),
            )
    ptype = powertrain_type(identity)
    if ptype != "UNKNOWN":
        fact(
            "identity",
            "powertrain_type",
            ptype,
            "vehicle_identity",
            {"field": "electrification_level"},
            exact=bool(request.vin),
        )
    motor = re.search(
        r"Motor:.*?(\d+(?:\.\d+)?)\s*kW", identity.get("other_engine_info") or "", re.I
    )
    if motor:
        fact(
            "engine",
            "motor_power_kw",
            float(motor[1]),
            "vehicle_identity",
            {"field": "other_engine_info"},
            exact=bool(request.vin),
        )
    # Market is the requested research scope, not proof of first registration.
    fact(
        "identity",
        "market",
        request.market,
        "vehicle_identity",
        {"field": "research_market", "origin": "USER_RESEARCH_SCOPE"},
        status="ESTIMATE",
    )
    if identity.get("turbo") == "Yes":
        fact("engine", "aspiration", "TURBO", "vehicle_identity", {"field": "turbo"}, exact=True)
    if identity.get("transmission_style"):
        text = identity["transmission_style"].casefold()
        value = (
            "CVT"
            if "continuously" in text
            else "AUTOMATIC"
            if "automatic" in text
            else "MANUAL"
            if "manual" in text
            else None
        )
        fact(
            "transmission",
            "type",
            value,
            "vehicle_identity",
            {"field": "transmission_style"},
            exact=True,
        )
    if identity.get("transmission_speeds"):
        fact(
            "transmission",
            "gears",
            int(identity["transmission_speeds"]),
            "vehicle_identity",
            {"field": "transmission_speeds"},
            exact=True,
        )
    official, owner_logs = [], []
    if epa:
        locator = {"url": epa["record_url"], "record_id": epa["id"]}
        variant_scope = {
            **base_scope,
            "displacement": epa.get("displ"),
            "cylinders": epa.get("cylinders"),
            "powertrain_type": target["powertrain_type"],
            "drivetrain": epa.get("drive"),
        }
        fact(
            "identity",
            "configuration",
            epa.get("model"),
            "fuel_economy",
            {**locator, "field": "model"},
            scope=variant_scope,
        )
        if ptype == "UNKNOWN" and target["powertrain_type"] != "UNKNOWN":
            fact(
                "identity",
                "powertrain_type",
                target["powertrain_type"],
                "fuel_economy",
                {**locator, "field": "atvType"},
                scope=variant_scope,
            )
        fact(
            "engine",
            "displacement",
            epa.get("displ"),
            "fuel_economy",
            {**locator, "field": "displ"},
            scope=variant_scope,
        )
        fact(
            "engine",
            "cylinders",
            epa.get("cylinders"),
            "fuel_economy",
            {**locator, "field": "cylinders"},
            scope=variant_scope,
        )
        if epa.get("tCharger") == "T":
            fact(
                "engine",
                "aspiration",
                "TURBO",
                "fuel_economy",
                {**locator, "field": "tCharger"},
                scope=variant_scope,
            )
        if "SIDI" in epa.get("eng_dscr", ""):
            fact(
                "engine",
                "injection",
                "DIRECT_INJECTION",
                "fuel_economy",
                {**locator, "field": "eng_dscr"},
                scope=variant_scope,
            )
        fact(
            "engine",
            "fuel_grade",
            epa.get("fuelType1"),
            "fuel_economy",
            {**locator, "field": "fuelType1"},
            scope=variant_scope,
        )
        if not request.vin:
            fact(
                "engine",
                "fuel",
                epa.get("fuelType1"),
                "fuel_economy",
                {**locator, "field": "fuelType1"},
                scope=variant_scope,
            )
            fact(
                "identity",
                "size_class",
                epa.get("VClass"),
                "fuel_economy",
                {**locator, "field": "VClass"},
                scope=variant_scope,
            )
        transmission = epa.get("trany", "")
        tr_type = (
            "DIRECT_DRIVE"
            if target["powertrain_type"] == "BEV"
            else "CVT"
            if "variable" in transmission.casefold() or "(AV" in transmission.upper()
            else "AUTOMATIC"
            if "automatic" in transmission.casefold()
            else "MANUAL"
            if "manual" in transmission.casefold()
            else "DIRECT_DRIVE"
            if target["powertrain_type"] == "BEV"
            else None
        )
        fact(
            "transmission",
            "type",
            tr_type,
            "fuel_economy",
            {**locator, "field": "trany"},
            scope=variant_scope,
        )
        gears = re.search(r"(?:S|AV|\s)(\d+)\)?$", transmission)
        if gears and tr_type != "CVT":
            fact(
                "transmission",
                "gears",
                int(gears[1]),
                "fuel_economy",
                {**locator, "field": "trany"},
                scope=variant_scope,
            )
        drive = {
            "Front-Wheel Drive": "FWD",
            "Rear-Wheel Drive": "RWD",
            "All-Wheel Drive": "AWD",
            "4-Wheel Drive": "4WD",
        }.get(epa.get("drive"))
        fact(
            "identity",
            "drivetrain",
            drive,
            "fuel_economy",
            {**locator, "field": "drive"},
            scope=variant_scope,
        )
        # MPG/MPGe are not interchangeable; no liquid-fuel conversion for electric/PHEV.
        if target["powertrain_type"] in {"BEV", "PHEV"}:
            energy = float(epa.get("combE") or 0)
            if energy > 0:
                fact(
                    "fuel_consumption",
                    "electric_kwh_100km",
                    round(energy / 1.609344, 2),
                    "fuel_economy",
                    {
                        **locator,
                        "field": "combE",
                        "original_unit": "kWh/100 miles",
                        "conversion": "divide by 1.609344",
                    },
                    scope=variant_scope,
                )
            charge = float(epa.get("charge240") or 0)
            if charge > 0:
                fact(
                    "engine",
                    "charge_240v_hours",
                    charge,
                    "fuel_economy",
                    {**locator, "field": "charge240"},
                    scope=variant_scope,
                )
        if target["powertrain_type"] in {"BEV", "HEV", "PHEV"}:
            motors = re.findall(r"(\d+(?:\.\d+)?)\s*kW\b", str(epa.get("evMotor") or ""), re.I)
            if len(motors) == 1:
                fact(
                    "engine",
                    "motor_power_kw",
                    float(motors[0]),
                    "fuel_economy",
                    {**locator, "field": "evMotor"},
                    scope=variant_scope,
                )
            capacity = re.search(
                r"\b(\d+(?:\.\d+)?)\s*(?:kW-hr|kWh)\s+battery", str(epa.get("model") or ""), re.I
            )
            if capacity:
                fact(
                    "engine",
                    "battery_capacity_kwh",
                    float(capacity[1]),
                    "fuel_economy",
                    {**locator, "field": "model", "origin": "EPA configuration label"},
                    scope=variant_scope,
                )
        cargo = [
            (key, float(epa.get(key) or 0))
            for key in ("lv2", "lv4", "hlv")
            if float(epa.get(key) or 0) > 0
        ]
        if len(cargo) == 1:
            field, volume = cargo[0]
            fact(
                "body",
                "cargo_cuft",
                volume,
                "fuel_economy",
                {**locator, "field": field, "original_unit": "cubic feet (EPA)"},
                scope=variant_scope,
            )
        if epa.get("fuelType1") in {
            "Regular Gasoline",
            "Premium Gasoline",
            "Midgrade Gasoline",
            "Diesel",
        } and not epa.get("fuelType2"):
            values = {
                key: round(235.214583 / float(epa[field]), 1)
                for key, field in (
                    ("city", "city08"),
                    ("highway", "highway08"),
                    ("combined", "comb08"),
                )
                if float(epa.get(field) or 0) > 0
            }
            if len(values) == 3:
                official = [
                    {
                        **values,
                        "unit": "l/100km",
                        "epa_id": epa["id"],
                        "source_url": epa["record_url"],
                        "method": "235.214583 / US MPG",
                    }
                ]
                fact(
                    "fuel_consumption",
                    "official",
                    official[0],
                    "fuel_economy",
                    locator,
                    scope=variant_scope,
                )
    for result in results:
        if result.capability in {"technical_specs", "maintenance_specs"} and not result.error:
            for row in result.records:
                fact(
                    row["topic"],
                    "engine_power_hp" if row["subtopic"] == "power_hp" else row["subtopic"],
                    row["value"],
                    result.capability,
                    {**row["locator"], "url": row["record_url"]},
                    scope=row["applicability"],
                )
        if result.capability == "owner_experience" and not result.error and epa:
            owner_logs = result.records
    fuels = fuel_layers(official, owner_logs)
    if owner_logs:
        fact(
            "fuel_consumption",
            "owner_reported",
            fuels["owner_reported"],
            "owner_experience",
            {"url": owner_logs[0]["record_url"]},
            status=fuels["owner_reported"]["status"],
        )
    # Unit conversions retain the original evidence/locator and are not a new source.
    for original in list(facts):
        sub = original["subtopic"]
        if sub.endswith(("_power_hp", "_power_kw")):
            suffix = "kw" if sub.endswith("hp") else "hp"
            converted = sub[:-2] + suffix
            if not any(f["subtopic"] == converted for f in facts):
                facts.append(
                    {
                        **original,
                        "subtopic": converted,
                        "value": round(
                            float(original["value"])
                            * (0.745699872 if suffix == "kw" else 1 / 0.745699872),
                            3,
                        ),
                        "conversion": "1 SAE hp = 0.745699872 kW",
                    }
                )
    findings, contradictions = synthesize_facts(facts, target)
    gate = integrity_from_findings(target, findings, contradictions)
    # Keep rejected/conflicting raw evidence in diagnostics, never in dossier/chat synthesis.
    accepted_eids = {
        eid for f in findings if f["status"] != "INSUFFICIENT_DATA" for eid in f["evidence_ids"]
    }
    for evidence in profile.evidence:
        if (
            evidence.conditions.get("consumer_kind") == "knowledge_fact"
            and evidence.id not in accepted_eids
        ):
            evidence.conditions = {**evidence.conditions, "excluded_from_synthesis": True}
        if (
            evidence.conditions.get("consumer_kind") == "transmission_identity"
            and "transmission" in gate["missing_fields"]
        ):
            evidence.conditions = {**evidence.conditions, "excluded_from_synthesis": True}
    material_rows = []

    def material_evidence(material, capability):
        source = sources[capability]
        evidence = TechnicalEvidence(
            vehicle_variant_id=profile.vehicle_variant_id,
            source_id=source.id,
            category=EvidenceCategory.ENGINE,
            title=material["issue_key"],
            statement=material["text"],
            status=EvidenceStatus.ESTIMATE,
            confidence=ConfidenceLevel.MEDIUM,
            market="US",
            conditions={
                "consumer_kind": "issue_signal",
                "section_key": "weak_points",
                "material": material,
                "applicability": material.get("applicability", {}),
                "applicability_class": applicability_class(material.get("applicability", {})),
            },
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        db.add(evidence)
        db.flush()
        profile.evidence.append(evidence)
        result = next(r for r in results if r.capability == capability)
        provenance[evidence.id] = {
            "source_id": source.id,
            "provider_id": result.provider_id,
            "url": material.get("record_url") or result.source_url,
            "material_id": material["material_id"],
            "retrieved_at": result.retrieved_at.isoformat(),
            "raw": material["text"],
        }
        material_rows.append({**material, "source_ids": [source.id], "evidence_ids": [evidence.id]})

    for result in results:
        if (
            result.capability == "technical_bulletins"
            and not result.error
            and result.capability in sources
        ):
            for row in result.records:
                material_evidence(row, result.capability)
    complaint_source = sources.get("owner_complaints")
    if complaint_source:
        complaint_result = next(r for r in results if r.capability == "owner_complaints")
        for row in complaint_result.records:
            narrative = row.get("normalized_summary") or ""
            liters = re.search(r"\b(\d\.\d)\s*(?:l|liter|litre)\b", narrative, re.I)
            if (
                liters
                and identity.get("displacement_l")
                and abs(float(liters[1]) - float(identity["displacement_l"])) < 0.06
                and "coolant" in narrative.casefold()
                and any(
                    term in narrative.casefold()
                    for term in (
                        "intrusion",
                        "cylinder",
                        "head gasket",
                        "engine replacement",
                        "engine replaced",
                    )
                )
            ):
                material_evidence(
                    {
                        "material_id": f"ODI-{row['odi_number']}",
                        "topic": "engine",
                        "issue_key": "coolant_intrusion",
                        "text": narrative,
                        "owner_id": None,
                        "publisher_group": "NHTSA-ODI",
                        "evidence_class": "OFFICIAL_COMPLAINT_DATABASE",
                        "applicability": {
                            **row.get("applicability", base_scope),
                            "displacement": float(liters[1]),
                        },
                    },
                    "owner_complaints",
                )
                continue
            material_rows.append(
                {
                    "material_id": f"ODI-{row['odi_number']}",
                    "topic": row.get("components") or "other",
                    "text": row.get("normalized_summary") or "",
                    "owner_id": None,
                    "publisher_group": "NHTSA-ODI",
                    "evidence_class": "OFFICIAL_COMPLAINT_DATABASE",
                    "applicability": row.get("applicability", base_scope),
                }
            )
    state = {
        "version": DEPTH_VERSION,
        "target": target,
        "facts": facts,
        "findings": findings,
        "contradictions": contradictions,
        "coverage": coverage(findings),
        "research_plan": plan,
        "provenance": provenance,
        "fuel": fuels,
        "owner_sample": owner_sample(material_rows, target),
        "issue_aggregation": aggregate_issues(material_rows, target),
        "epa_candidates": epa_result.records if epa_result else [],
        "provider_availability": [
            {
                "provider_id": r.provider_id,
                "capability": r.capability,
                "error": r.error,
                "records": len(r.records),
                "from_cache": r.from_cache,
                "reason": r.raw_payload.get("unavailable_reason")
                if isinstance(r.raw_payload, dict)
                else None,
            }
            for r in results
        ],
    }
    profile.dossier_seed = {
        **profile.dossier_seed,
        "knowledge_depth": state,
        "identity_integrity": gate,
    }
    profile.profile_version = DEPTH_VERSION + "-paid-report.1"
    resolved = {
        (f["topic"], f["subtopic"]): f["value"] for f in findings if f["status"] == "CONFIRMED"
    }
    tr = resolved.get(("transmission", "type"))
    gears = resolved.get(("transmission", "gears"))
    if tr:
        profile.transmission = f"{gears}-speed {tr.title()}" if gears else tr
    if "transmission" in gate["missing_fields"]:
        profile.transmission = None
    if resolved.get(("identity", "drivetrain")):
        profile.drivetrain = resolved[("identity", "drivetrain")]
    return len(facts)
