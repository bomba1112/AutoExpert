from __future__ import annotations

from app.core.report_pricing import configured_report_price
from app.models.analysis import Report
from app.schemas.analysis import GroundedClaim, PreviewResponse

PIPELINE_STAGES = [
    "vehicle_resolution",
    "technical_evidence",
    "market_analysis",
    "ownership_calculation",
    "owner_feedback",
    "fit_analysis",
    "grounding_validation",
    "snapshot_saved",
]


def preview_from_report(report: Report) -> PreviewResponse:
    bundle = report.evidence_bundle
    generated = report.generated_sections
    vehicle_input = report.input_snapshot["vehicle"]
    claims = [
        claim for section in generated.get("sections", []) for claim in section.get("claims", [])
    ]
    market = bundle["market_analysis"]
    price, currency = configured_report_price(vehicle_input["country"])
    return PreviewResponse(
        report_id=report.id,
        vehicle=bundle["vehicle"],
        verdict=generated["verdict"],
        verdict_summary=generated["verdict_summary"],
        highlights=[GroundedClaim.model_validate(claim) for claim in claims[:3]],
        local_market_status=market["status"],
        available_sections=[section["key"] for section in generated.get("sections", [])],
        is_unlocked=report.is_unlocked,
        is_demo=report.is_demo,
        price=price,
        currency=currency,
        country=vehicle_input["country"],
        city=vehicle_input.get("city"),
        comparable_count=market["comparable_count"],
        used_comparable_count=market["used_count"],
        evidence_count=len(bundle["technical_evidence"]) + len(bundle["known_issues"]),
        source_count=len(bundle["sources"]),
        pipeline_stages=PIPELINE_STAGES,
    )
