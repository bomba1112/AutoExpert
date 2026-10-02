"""Summarize measured bulk-work operations without inventing agent review time."""

# ruff: noqa: E501

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def timestamp(value: str):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def acquisition_receipts(since: datetime):
    unique = {}
    for path in OUT.rglob("*.json"):
        if "receipt" not in path.name and "acquisition" not in path.name:
            continue
        value = read(path)
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict) or item.get("http_status") != 200:
                continue
            digest = item.get("sha256")
            observed = item.get("observed_at")
            if (
                digest
                and observed
                and timestamp(observed) >= since
                and item.get("latency_ms") is not None
            ):
                unique.setdefault(digest, item)
    return list(unique.values())


def main():
    first = read(OUT / "ai-work/source-review-metrics.json")
    second = read(OUT / "ai-work/source-review-metrics-2.json")
    third = read(OUT / "ai-work/source-review-metrics-3.json")
    summary = read(OUT / "mass-scale-summary.json")
    elapsed = (
        timestamp(summary["observed_at"])
        - timestamp(summary["baseline_at"])
    ).total_seconds()
    receipts = acquisition_receipts(timestamp(summary["baseline_at"]))
    observations = OUT / "final-ops-measured.json"
    final_ops = read(observations) if observations.exists() else {}
    metrics = {
        "baseline_at": summary["baseline_at"],
        "observed_at": summary["observed_at"],
        "catalog_production_wall_seconds": round(elapsed, 3),
        "new_base_ready": summary["new_base_ready"],
        "new_base_ready_per_hour_catalog_production": round(
            summary["new_base_ready"] * 3600 / elapsed, 2
        ),
        "catalog_production_window_note": "Frozen baseline through final named live-DB catalogue snapshot; final audit, regression, backup and package are timed separately.",
        "ai_draft_serialization_seconds": first["programmatic"]["ai_draft_generation_seconds"],
        "ai_model_reasoning_seconds": None,
        "bulk_epa_index_and_db_read_seconds": first["programmatic"]["epa_index_and_db_read_seconds"],
        "bulk_scope_join_seconds": first["programmatic"]["epa_scope_join_seconds"],
        "ai_epa_comparison_seconds": first["programmatic"]["ai_epa_comparison_seconds"],
        "source_first_fetch_seconds_sum_three_ai_packets_known": round(
            first["source_acquisition"]["successful_used_document_first_fetch_seconds_sum_from_tool_results"]
            + second["programmatic"]["source_acquisition_first_fetch_sum_seconds"]
            + third["programmatic"]["source_acquisition_first_fetch_known_sum_seconds"],
            4,
        ),
        "third_ai_packet_successful_first_fetch_latencies_unavailable": third["programmatic"]["source_acquisition_first_fetch_latency_not_retained_count"],
        "successful_unique_receipts_with_latency": len(receipts),
        "source_fetch_latency_seconds_sum_unique_receipts": round(
            sum(item["latency_ms"] for item in receipts) / 1000, 4
        ),
        "source_fetch_latency_note": "Sum of measured request latencies, not critical-path wall time; parallel fetches and cache reads differ.",
        "first_ai_packet_text_extraction_seconds": first["programmatic"]["extraction_seconds_sum"],
        "second_ai_packet_text_extraction_seconds": second["programmatic"]["selected_factory_page_and_html_extraction_seconds"],
        "third_ai_packet_text_extraction_seconds": third["programmatic"]["source_payload_extraction_assertions_seconds"],
        "second_ai_packet_cached_epa_index_seconds": second["programmatic"]["cached_epa_index_seconds"],
        "second_ai_packet_69_exact_joins_seconds": second["programmatic"]["exact_factory_epa_join_and_receipt_check_seconds"],
        "first_ai_packet_manifest_validation_seconds": first["programmatic"]["manifest_build_and_hash_validation_seconds"],
        "second_ai_packet_manifest_validation_seconds": second["programmatic"]["manifest_hash_schema_validation_seconds"],
        "third_ai_packet_full_publication_preflight_seconds": third["programmatic"]["production_validate_publication_preflight_seconds"],
        "agent_factory_matrix_review_seconds": None,
        "agent_conflict_adjudication_seconds": None,
        "agent_review_note": "Factory matrix reading, source selection and exception decisions were not separately timed.",
        "final_operations": final_ops,
    }
    (OUT / "mass-scale-operation-timings.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "new_base_ready_per_hour_catalog_production": metrics[
                    "new_base_ready_per_hour_catalog_production"
                ],
                "successful_unique_receipts_with_latency": len(receipts),
                "catalog_production_wall_seconds": metrics["catalog_production_wall_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
