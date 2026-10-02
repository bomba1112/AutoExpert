"""Compare AI hypotheses to independently reviewed source tuples; never publish AI fields."""

import argparse
import copy
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.catalog_scope import in_active_scope  # noqa: E402

VERSION = "source-tuple-ai-comparison-2"
FIELD_MAP = {
    "body": "body",
    "displacement_l": "engine_displacement",
    "cylinders": "cylinders",
    "powertrain": "powertrain",
    "fuel_type": "fuel",
    "aspiration": "aspiration",
    "injection": "injection",
    "transmission_type": "transmission_family",
    "transmission_gears": "gears",
    "drivetrain": "drivetrain",
    "trim": "trim",
    "seats": "seats",
    "engine_label": "engine_description",
    "engine_code": "engine_code",
    "engine_family": "engine_family",
    "transmission_label": "transmission_description",
    "transmission_code": "transmission_code",
    "engine_oil_viscosity": "engine_oil_viscosity",
    "engine_oil_approval": "engine_oil_approval",
    "engine_oil_fill_with_filter_l": "engine_oil_service_capacity_l",
    "transmission_fluid_specification": "transmission_fluid_specification",
    "transmission_fluid_service_volume_l": "transmission_fluid_service_capacity_l",
    "battery_capacity_kwh": "battery_capacity_kwh",
    "electric_motor_code": "electric_motor_code",
}
JOINT = (
    "body",
    "displacement_l",
    "powertrain",
    "fuel_type",
    "aspiration",
    "transmission_type",
    "transmission_gears",
    "drivetrain",
    "trim",
)
NUMERIC = {"displacement_l", "cylinders", "transmission_gears", "seats", "battery_capacity_kwh"}
DESCRIPTIVE = {"generation", "engine_label", "transmission_label", "injection"}


def equal(name, a, b):
    if name == "transmission_type":
        # Comparator-only spelling normalization; publication still uses existing gates.
        a = "MANUAL" if str(a).upper() == "MT" else a
        b = "MANUAL" if str(b).upper() == "MT" else b
    if name in NUMERIC:
        try:
            return Decimal(str(a)) == Decimal(str(b))
        except InvalidOperation:
            return False
    return " ".join(str(a).casefold().split()) == " ".join(str(b).casefold().split())


def observations(manifest, manifest_path=None):
    """Only source-authored manifest values; AI candidates are not accepted as this input."""
    if manifest.get("provenance") == "AI_DRAFT" or "families" not in manifest:
        raise ValueError("INDEPENDENT_SOURCE_MANIFEST_REQUIRED")
    result = []
    for family_index, family in enumerate(manifest["families"]):
        for group_index, group in enumerate(family["groups"]):
            if not group.get("factory_combinations"):
                raise ValueError("EXPLICIT_SOURCE_TUPLE_REQUIRED")
            for year in range(group["year_from"], group["year_to"] + 1):
                for combination in group["factory_combinations"]:
                    raw_values = {
                        **family.get("facts", {}),
                        **group["facts"],
                        **group.get("annual_facts", {}).get(str(year), {}),
                        "drivetrain": combination["drivetrain"],
                    }
                    values = {
                        k: (v.get("value") if isinstance(v, dict) else v)
                        for k, v in raw_values.items()
                    }
                    annual = family["annual_documents"][str(year)]
                    result.append(
                        {
                            "id": (
                                f"{family['id']}:{group['id']}:{combination['drivetrain']}:{year}"
                            ),
                            "make": family["make"],
                            "model": family["model"],
                            "market": family["market"],
                            "model_year": year,
                            "generation": family.get("generation_code") or family["generation"],
                            "facts": values,
                            "provenance": "FACTORY_DOCUMENT_OBSERVATION",
                            "manifest_path": manifest_path,
                            "batch_id": manifest.get("batch_id"),
                            "source_state": manifest.get("state", "REVIEWED_MANIFEST"),
                            "field_observations": {
                                k: {
                                    "normalized_value": values[k],
                                    "source_value": values[k],
                                    "source_unit": v.get("unit") if isinstance(v, dict) else None,
                                    "document_key": v.get("document_key", annual[0])
                                    if isinstance(v, dict)
                                    else annual[0],
                                    "locator": group["locator"],
                                    "applicability": {
                                        "make": family["make"],
                                        "model": family["model"],
                                        "market": family["market"],
                                        "model_year": year,
                                        "configuration": group["configuration"],
                                        "drivetrain": combination["drivetrain"],
                                    },
                                }
                                for k, v in raw_values.items()
                            },
                            "references": [
                                {
                                    "document_key": key,
                                    **manifest["documents"][key],
                                    "table_locator": group["locator"],
                                }
                                for key in annual
                            ],
                            "generation_references": [
                                {"document_key": key, **manifest["documents"][key]}
                                for key in family.get("generation_documents", [])
                            ],
                            "joint_applicability": group["configuration"],
                        }
                    )
                    entry = result[-1]
                    for field, observed in entry["field_observations"].items():
                        normalize_observation(
                            observed,
                            field,
                            raw_values,
                            manifest,
                            family,
                            group,
                            family_index,
                            group_index,
                            year,
                        )
    return result


def normalize_observation(observed, field, raw, manifest, family, group, fi, gi, year):
    """Preserve recorded pre-conversion values; never reverse-calculate a source claim."""
    paths = {
        f"/families/{fi}/facts",
        f"/families/{fi}/groups/{gi}/facts",
        f"/families/{fi}/groups/{gi}/annual_facts/{year}",
    }
    matches = [
        n
        for n in manifest.get("source_unit_normalizations", [])
        if n.get("field") == field
        and n.get("value") == observed["normalized_value"]
        and (
            (n.get("family") == family["id"] and n.get("group") == group["id"])
            or n.get("path") in paths
        )
    ]
    if matches:
        n = matches[-1]
        observed.update(
            source_value=n["raw_value"],
            source_unit=n["raw_unit"],
            normalized_unit=n["unit"],
            conversion=n["conversion"],
            normalization_basis="RECORDED_SOURCE_UNIT_NORMALIZATION",
        )
        return
    raw_key = {"ground_clearance": "ground_clearance_in", "fuel_combined": "epa_combined_mpg"}.get(
        field
    )
    if raw_key and raw_key in raw:
        original = raw[raw_key]
        original_value = original.get("value") if isinstance(original, dict) else original
        original_unit = original.get("unit") if isinstance(original, dict) else None
        # Units must have been recorded, not inferred from a number alone.
        if original_unit:
            observed.update(
                source_value=original_value,
                source_unit=original_unit,
                raw_source_field=raw_key,
                normalized_unit=observed["source_unit"],
                normalization_basis="RETAINED_RAW_SOURCE_FIELD",
            )
            return
    if field in {"ground_clearance", "fuel_combined"}:
        observed.update(
            normalized_unit=observed["source_unit"],
            source_value=None,
            source_unit=None,
            source_original_status="NOT_SEPARATELY_RECORDED; normalized manifest value retained",
        )


def merge_observations(manifests):
    """Repeated stable tuple IDs are explicit later revisions, not extra vehicles."""
    merged = {}
    for path, manifest in manifests:
        for row in observations(manifest, path):
            old = merged.get(row["id"])
            if old:
                identity = ("make", "model", "market", "model_year")
                if any(old[k] != row[k] for k in identity):
                    raise ValueError("CORRECTION_TUPLE_SCOPE_MISMATCH")
                history = old.get("superseded_observations", []) + [
                    {k: v for k, v in old.items() if k != "superseded_observations"}
                ]
                row["superseded_observations"] = history
                row["supersession_reason"] = "LATER_EXPLICIT_SOURCE_MANIFEST_SAME_TUPLE_ID"
                row["changed_source_fields"] = sorted(
                    k
                    for k in row["facts"].keys() | old["facts"].keys()
                    if row["facts"].get(k) != old["facts"].get(k)
                )
            merged[row["id"]] = row
    return list(merged.values())


def apply_fact_corrections(source_rows, corrections):
    """Apply reviewed same-key facts; legacy key spelling never becomes actual drive evidence."""
    from app.schemas.knowledge import ImportManifest

    rows = copy.deepcopy(source_rows)
    keyed = defaultdict(list)
    for row in rows:
        parts = row["id"].split(":")
        if len(parts) != 4:
            raise ValueError("SOURCE_TUPLE_ID_SHAPE_REQUIRED")
        keyed["-".join(parts)].append(row)
    conflicts = []
    for path, payload in corrections:
        manifest = ImportManifest.model_validate(payload)
        if manifest.parser != "manifest-json-v1":
            raise ValueError("REVIEWED_FACT_CORRECTION_MANIFEST_REQUIRED")
        seen = set()
        for record in manifest.records:
            if record.external_key in seen:
                raise ValueError("DUPLICATE_FACT_CORRECTION_KEY")
            seen.add(record.external_key)
            candidates = keyed.get(record.external_key, [])
            if len(candidates) != 1:
                raise ValueError("EXISTING_UNAMBIGUOUS_SOURCE_TUPLE_REQUIRED")
            row = candidates[0]
            if (row["make"], row["model"], row["market"], row["model_year"]) != (
                record.make,
                record.model,
                record.original_market,
                record.model_year,
            ):
                raise ValueError("FACT_CORRECTION_SCOPE_MISMATCH")
            changes = []
            for field, fact in record.facts.items():
                if fact.value == row["facts"].get(field):
                    continue
                ref = fact.documentary_source
                if fact.status != "CONFIRMED" or ref is None:
                    raise ValueError("FACT_CORRECTION_REQUIRES_CONFIRMED_DOCUMENT")
                years = (
                    {ref.model_year}
                    if ref.model_year is not None
                    else set(range(ref.model_year_from, ref.model_year_to + 1))
                )
                if (ref.make, ref.model, ref.market) != (
                    record.make,
                    record.model,
                    record.original_market,
                ) or record.model_year not in years:
                    raise ValueError("FACT_CORRECTION_DOCUMENT_SCOPE_MISMATCH")
                changes.append((field, fact, ref.model_dump(mode="json")))
            if not changes:
                continue
            previous = {
                k: copy.deepcopy(v) for k, v in row.items() if k != "superseded_observations"
            }
            row.setdefault("superseded_observations", []).append(previous)
            row["supersession_reason"] = "REVIEWED_SAME_KEY_FACT_CORRECTION"
            row["fact_correction_manifest"] = path
            row["external_key"] = record.external_key
            row["id_encoding_note"] = (
                "Stable historical observation ID and external key retained; "
                "actual drivetrain is the current sourced fact, not the key suffix."
            )
            row["joint_applicability"] = record.configuration
            row["changed_source_fields"] = [field for field, _, _ in changes]
            # Current tuple applicability must follow its reviewed fact, including
            # unchanged engine fields. The previous AWD context remains in history.
            actual_drive = record.facts.get("drivetrain")
            actual_drive = actual_drive.value if actual_drive else row["facts"].get("drivetrain")
            for observed in row["field_observations"].values():
                observed["applicability"].update(
                    configuration=record.configuration, drivetrain=actual_drive
                )
            for field, fact, ref in changes:
                old_value = row["facts"].get(field)
                row["facts"][field] = fact.value
                row["field_observations"][field] = {
                    "normalized_value": fact.value,
                    "source_value": fact.value,
                    "source_unit": fact.unit,
                    "document_key": ref["document_id"],
                    "documentary_source": ref,
                    "locator": fact.locator,
                    "applicability": {
                        "make": record.make,
                        "model": record.model,
                        "market": record.original_market,
                        "model_year": record.model_year,
                        "configuration": record.configuration,
                        "drivetrain": actual_drive,
                    },
                }
                reference = {
                    **ref,
                    "document_key": ref["document_id"],
                    "table_locator": fact.locator,
                }
                if reference not in row["references"]:
                    row["references"].append(reference)
                conflicts.append(
                    {
                        "source_observation_id": row["id"],
                        "external_key": record.external_key,
                        "manifest": path,
                        "field": field,
                        "old_value": old_value,
                        "corrected_value": fact.value,
                        "documentary_source": ref,
                        "resolution": "SOURCE_BACKED_FACT_CORRECTION_SAME_KEY",
                        "reason": (
                            "Unsupported AWD normalization corrected to factory 4WD; "
                            "original value retained in superseded history"
                        )
                        if field == "drivetrain" and old_value == "AWD" and fact.value == "4WD"
                        else record.revision_note,
                        "new_configuration": False,
                    }
                )
    assert len(rows) == len(source_rows)
    return rows, conflicts


def adjudicated(rule, draft, year, field, claim, value, source):
    return bool(
        rule.get("draft_id") == draft["id"]
        and rule.get("model_year") == year
        and rule.get("field") == field
        and rule.get("draft_value") == claim
        and rule.get("source_value") == value
        and source["id"] in rule.get("source_observation_ids", [])
        and rule.get("decision") == "ACCEPT_SCOPED_SOURCE_LABEL"
        and rule.get("references")
        and rule.get("reason")
    )


def compare(drafts, source_rows, adjudications=()):
    results = []
    matched = set()
    for draft in drafts:
        if draft.get("provenance") != "AI_DRAFT" or draft.get("publication_eligible") is not False:
            raise ValueError("UNVERIFIED_DRAFT_REQUIRED")
        if any(
            f.get("verification_status") != "UNVERIFIED" or f.get("source") is not None
            for f in draft["fields"].values()
        ):
            raise ValueError("DRAFT_CANNOT_SELF_VERIFY")
        claims = {k: v["value"] for k, v in draft["fields"].items()}
        for year in claims["model_years"]:
            item = {
                "draft_id": draft["id"],
                "model_year": year,
                "publication_from_draft": False,
                "fields": {},
            }
            if not in_active_scope(claims["make"], claims["market"], year):
                results.append(
                    {**item, "status": "OUTSIDE_ACTIVE_SCOPE", "source_observation_ids": []}
                )
                continue
            possible = [
                s
                for s in source_rows
                if (s["make"], s["model"], s["market"], s["model_year"])
                == (claims["make"], claims["model"], claims["market"], year)
            ]

            def differences(s, claims=claims, draft=draft, year=year):
                return [
                    k
                    for k in JOINT
                    if claims.get(k) is not None
                    and s["facts"].get(FIELD_MAP[k]) is not None
                    and not equal(k, claims[k], s["facts"][FIELD_MAP[k]])
                    and not any(
                        adjudicated(r, draft, year, k, claims[k], s["facts"][FIELD_MAP[k]], s)
                        for r in adjudications
                    )
                ]

            exact = [s for s in possible if not differences(s)]
            # Unique one-field disagreement is an exception to review, never a silent join.
            near = [s for s in possible if len(differences(s)) == 1] if not exact else []
            chosen = exact or (near if len(near) == 1 else [])
            item["source_observation_ids"] = [s["id"] for s in chosen]
            if not chosen:
                item["status"] = "INSUFFICIENT_DATA"
                item["reason"] = "NO_UNAMBIGUOUS_SOURCE_TUPLE; absence does not prove nonexistence"
            else:
                for field, claim in claims.items():
                    if field == "model_years":
                        continue
                    values = [
                        s.get(field)
                        if field in {"make", "model", "market", "generation"}
                        else s["facts"].get(FIELD_MAP.get(field, field))
                        for s in chosen
                    ]
                    value = values[0] if values and all(v == values[0] for v in values) else None
                    status = (
                        "INSUFFICIENT_DATA"
                        if value is None or claim is None
                        else "CONFIRMED"
                        if equal(field, claim, value)
                        else "NEEDS_LABEL_REVIEW"
                        if field in DESCRIPTIVE
                        else "CONTRADICTION"
                    )
                    raw_status = status
                    scoped_review = (
                        claim is not None
                        and value is not None
                        and all(
                            any(
                                adjudicated(r, draft, year, field, claim, value, s)
                                for r in adjudications
                            )
                            for s in chosen
                        )
                    )
                    if status == "CONTRADICTION" and scoped_review:
                        status = "SOURCE_LABEL_ADJUDICATED"
                    item["fields"][field] = {
                        "draft_value": claim,
                        "source_value": value,
                        "status": status,
                        "unadjudicated_status": raw_status,
                    }
                item["status"] = (
                    "CONTRADICTION"
                    if any(f["status"] == "CONTRADICTION" for f in item["fields"].values())
                    else "MATCHED_SOURCE_TUPLE_WITH_ADJUDICATION"
                    if any(
                        f["status"] == "SOURCE_LABEL_ADJUDICATED" for f in item["fields"].values()
                    )
                    else "MATCHED_SOURCE_TUPLE"
                )
                if exact:
                    matched.update(s["id"] for s in exact)
            results.append(item)
    return {
        "parser_version": VERSION,
        "draft_annual_results": results,
        "source_discovered_observation_ids": [
            s["id"] for s in source_rows if s["id"] not in matched
        ],
        "counts": dict(Counter(r["status"] for r in results)),
        "drafts_unchanged": True,
        "publication_input": "INDEPENDENT_REVIEWED_FACTORY_MANIFEST_ONLY",
    }


def catalog_cursor(queue, drafts, comparison):
    """Read current public scope, without mutating DB, draft, or original queue."""
    from app.db.session import SessionLocal
    from app.services.catalog_buyer import active_us_base_rows, records
    from app.services.catalog_verification import us_catalog_with_confirmed_seating

    started = time.perf_counter()
    with SessionLocal() as db:
        db.autoflush = False
        ready = active_us_base_rows(records(db))
        published = defaultdict(list)
        for _, c in ready:
            published[(c["make"], c["model"])].append(c)
    summaries = []
    for (make, model), configs in sorted(published.items()):
        scopes = defaultdict(list)
        for c in configs:
            f = c["facts"]
            key = (
                c["generation"],
                f["body"]["value"],
                f["engine_description"]["value"],
                f["transmission_description"]["value"],
                f["drivetrain"]["value"],
            )
            scopes[key].append(c)
        summaries.append(
            {
                "make": make,
                "model": model,
                "market": "US",
                "exact_published_model_years": sorted({c["model_year"] for c in configs}),
                "configuration_count": len(configs),
                "with_confirmed_seats": sum(us_catalog_with_confirmed_seating(c) for c in configs),
                "scopes": [
                    {
                        "generation": k[0],
                        "body": k[1],
                        "engine": k[2],
                        "transmission": k[3],
                        "drivetrain": k[4],
                        "model_years": sorted({c["model_year"] for c in values}),
                        "configuration_count": len(values),
                    }
                    for k, values in sorted(scopes.items())
                ],
            }
        )
    remaining = []
    for q in queue["queue"]:
        years = {c["model_year"] for c in published.get((q["make"], q["model"]), [])}
        missing = sorted(set(q["target_model_years"]) - years)
        remaining.append(
            {
                "queue_id": q["queue_id"],
                "make": q["make"],
                "model": q["model"],
                "generation_target_hypothesis": q["generation_candidate"],
                "market": q["market"],
                "target_model_years": q["target_model_years"],
                "current_published_years_for_model": sorted(years),
                "missing_target_model_years": missing,
                "state": "WAITING_SOURCE"
                if missing
                else "YEAR_OVERLAP_REQUIRES_GENERATION_SCOPE_REVIEW",
                "note": (
                    "Year overlap is not proof of complete generation/trim coverage; "
                    "exact published scopes are listed separately."
                ),
            }
        )
    master = sorted({(q["make"], q["model"]) for q in queue["queue"]})
    unresolved = [
        {"draft_id": r["draft_id"], "model_year": r["model_year"], "status": r["status"]}
        for r in comparison["draft_annual_results"]
        if r["status"] in {"INSUFFICIENT_DATA", "CONTRADICTION"}
    ]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "db_writes": 0,
        "scope_validation": "PASS"
        if all(in_active_scope(c["make"], c["original_market"], c["model_year"]) for _, c in ready)
        else "FAIL",
        "public_readiness_function": "active_us_base_rows(records(db)); unchanged app contract",
        "published_models": summaries,
        "named_remaining_queue": remaining,
        "models_with_no_public_configuration": [
            {"make": m, "model": n} for m, n in master if (m, n) not in published
        ],
        "unresolved_draft_annual_targets": unresolved,
        "counts": {
            "published_makes": len({c["make"] for _, c in ready}),
            "published_models": len(published),
            "published_configurations": len(ready),
            "strict_configurations_with_confirmed_seats": sum(
                us_catalog_with_confirmed_seating(c) for _, c in ready
            ),
            "strict_models_with_confirmed_seats": len(
                {(c["make"], c["model"]) for _, c in ready if us_catalog_with_confirmed_seating(c)}
            ),
            "remaining_named_queue_entries": sum(
                bool(q["missing_target_model_years"]) for q in remaining
            ),
            "original_queue_entries": len(remaining),
        },
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", action="append", required=True)
    p.add_argument("--adjudication")
    p.add_argument("--fact-correction", action="append", default=[])
    p.add_argument("--cursor", action="store_true")
    p.add_argument("--source-backlog", action="append", default=[])
    p.add_argument("--queue", default="data/manifests/us-ai-verify-09-queue.json")
    p.add_argument("--drafts", default="deliverables/VerifiedData/us-ai-verify-09/ai-drafts.jsonl")
    p.add_argument("--output", default="deliverables/VerifiedData/us-ai-verify-09")
    a = p.parse_args()
    started = time.perf_counter()
    raw = (ROOT / a.drafts).read_bytes()
    drafts = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    manifests = [
        (name, json.loads((ROOT / name).read_text(encoding="utf-8"))) for name in a.manifest
    ]
    source = merge_observations(manifests)
    source, corrections = apply_fact_corrections(
        source,
        [
            (name, json.loads((ROOT / name).read_text(encoding="utf-8")))
            for name in a.fact_correction
        ],
    )
    adjudications = (
        json.loads((ROOT / a.adjudication).read_text(encoding="utf-8"))["decisions"]
        if a.adjudication
        else []
    )
    result = compare(drafts, source, adjudications)
    # Enrich provenance from the immutable acquisition receipt, never from the draft.
    receipts = {}
    for name in ("acquisition-ledger.json", "base-catalog-acquisition.json"):
        for row in json.loads(
            (ROOT / "deliverables/VerifiedData" / name).read_text(encoding="utf-8")
        ):
            if row.get("http_status") == 200 and row.get("sha256") and not row.get("error"):
                receipts[row["url"]] = row
    for row in source:
        for version in [row, *row.get("superseded_observations", [])]:
            for ref in version["references"] + version["generation_references"]:
                receipt = receipts.get(ref["url"])
                if receipt:
                    ref.update(sha256=receipt["sha256"], retrieved_at=receipt.get("observed_at"))
                else:
                    ref["receipt_status"] = "NOT_IN_SHARED_ACQUISITION_LEDGER"
    result.update(
        draft_sha256=hashlib.sha256(raw).hexdigest(),
        source_tuples=len(source),
        input_manifests=a.manifest,
        fact_correction_manifests=a.fact_correction,
        fact_correction_sha256={
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in a.fact_correction
        },
        corrected_existing_source_tuples=len({r["source_observation_id"] for r in corrections}),
        corrected_fact_cells=len(corrections),
        input_manifest_sha256={
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in a.manifest
        },
        superseded_tuples=sum(bool(s.get("superseded_observations")) for s in source),
        superseded_versions=sum(len(s.get("superseded_observations", [])) for s in source),
        normalized_observation_fields=sum(
            bool(f.get("normalization_basis"))
            for s in source
            for f in s["field_observations"].values()
        ),
        elapsed_seconds=round(time.perf_counter() - started, 4),
    )
    out = ROOT / a.output
    out.mkdir(parents=True, exist_ok=True)
    for name, value in (("source-observations.json", source), ("draft-comparison.json", result)):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    (out / "source-fact-corrections.json").write_text(
        json.dumps(
            {"new_source_tuples": 0, "corrections": corrections}, ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    if a.cursor:
        cursor = catalog_cursor(
            json.loads((ROOT / a.queue).read_text(encoding="utf-8")), drafts, result
        )
        cursor["source_review_backlogs"] = []
        for name in a.source_backlog:
            content = (ROOT / name).read_bytes()
            backlog = json.loads(content)
            cursor["source_review_backlogs"].append(
                {
                    "path": name,
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "state": backlog["state"],
                    "remaining": backlog["remaining"],
                    "counting_note": (
                        "Supplemental source-review scopes may overlap master queue; "
                        "not added to its count."
                    ),
                }
            )
        (out / "verification-cursor.json").write_text(
            json.dumps(cursor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    assert hashlib.sha256((ROOT / a.drafts).read_bytes()).hexdigest() == result["draft_sha256"]
    print(json.dumps({k: result[k] for k in ("counts", "source_tuples", "elapsed_seconds")}))


if __name__ == "__main__":
    main()
