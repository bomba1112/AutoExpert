from app.models.enums import EvidenceStatus
from app.schemas.analysis import EvidenceBundle, GeneratedReport


class UngroundedReportError(ValueError):
    pass


def validate_generated_report(bundle: EvidenceBundle, report: GeneratedReport) -> None:
    status_by_id: dict[str, EvidenceStatus] = {
        item.id: item.status for item in bundle.technical_evidence
    }
    status_by_id.update({item.id: item.status for item in bundle.known_issues})
    status_by_id.update(
        {
            "market_analysis": bundle.market_analysis.status,
            "ownership_calculation": bundle.ownership_calculation.status,
            "owner_feedback": EvidenceStatus.ESTIMATE,
            "fit_analysis": EvidenceStatus.ESTIMATE,
        }
    )
    for section in report.sections:
        for claim in section.claims:
            if not claim.evidence_ids and claim.status not in {
                EvidenceStatus.NEEDS_INSPECTION,
                EvidenceStatus.INSUFFICIENT_DATA,
            }:
                raise UngroundedReportError(
                    f"Claim in section {section.key!r} has no evidence reference"
                )
            for evidence_id in claim.evidence_ids:
                if evidence_id not in status_by_id:
                    raise UngroundedReportError(f"Unknown evidence reference: {evidence_id}")
                source_status = status_by_id[evidence_id]
                if (
                    claim.status == EvidenceStatus.CONFIRMED
                    and source_status != EvidenceStatus.CONFIRMED
                ):
                    raise UngroundedReportError(
                        f"Claim upgraded {source_status.value} evidence to CONFIRMED"
                    )
