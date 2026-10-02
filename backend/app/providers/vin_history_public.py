"""Public/archive history adapters with explicit coverage and access provenance.

Default sources currently restrict lookup access. Their recorded audits remain
unavailable, never NO_RECORDS. The normalized adapter supports an authorized
free/public or future PAYG response without provider-specific report branches.
"""

from collections.abc import Callable
from datetime import UTC, datetime

from app.schemas.research_evidence import (
    EvidenceProviderMetadata,
    ProviderAttempt,
    ResearchState,
    VinHistoryResult,
)

CAPABILITIES = [
    "VIN_EVENT_DISCOVERY",
    "AUCTION",
    "SALE",
    "TITLE",
    "ODOMETER",
    "PRIMARY_DAMAGE",
    "SECONDARY_DAMAGE",
    "LOSS_TYPE",
    "SALE_DATE",
    "AUCTION_COMPANY",
    "LOT_ID",
    "SALE_PRICE",
    "SELLER_TYPE",
    "LOCATION",
    "PHOTO_AVAILABILITY",
    "PHOTO_METADATA",
]

# This is an access-policy audit, not a vehicle-history dataset. Dates are the
# actual audit dates; an attempted lookup never pretends to have refreshed them.
ACCESS_AUDITS = [
    (
        "statvin_public",
        "Stat.vin",
        "https://stat.vin/terms-of-service",
        "TERMS_PROHIBIT_AUTOMATED_ACCESS",
        None,
    ),
    (
        "bidcars_public",
        "Bid.cars",
        "https://bid.cars/robots.txt",
        "ROBOTS_DISALLOW_ARCHIVE_SEARCH",
        200,
    ),
    ("bidfax_public", "Bidfax", "https://bidfax.info/robots.txt", "ACCESS_CHALLENGE", 403),
    ("vinfax_public", "Vinfax", "https://www.vinfax.net/vin/check", "HTTP_ACCESS_DENIED", 403),
    (
        "finalbid_public",
        "FinalBid",
        "https://finalbid.vin/en/terms",
        "TERMS_PROHIBIT_AUTOMATED_COLLECTION",
        None,
    ),
]


class AuditedRestrictedHistoryProvider:
    def __init__(self, audit):
        identifier, name, url, reason, status = audit
        self.metadata = EvidenceProviderMetadata(
            id=identifier,
            name=name,
            capabilities=CAPABILITIES,
            commercial_usage_status="RESTRICTED",
            policy_url=url,
        )
        self.reason, self.http_status = reason, status

    def lookup(self, vin: str) -> VinHistoryResult:
        return VinHistoryResult(
            vin=vin,
            attempt=ProviderAttempt(
                provider=self.metadata,
                state=ResearchState.PROVIDER_UNAVAILABLE,
                checked_at=datetime(2026, 9, 18, tzinfo=UTC),
                query={"vin": vin},
                scope="US auction archive; source access audit only, VIN query not completed",
                query_completed=False,
                reason=self.reason,
                http_status=self.http_status,
                provenance={
                    "policy_url": str(self.metadata.policy_url),
                    "audit_date": "2026-09-18",
                    "access_not_bypassed": True,
                    "audit_kind": "SOURCE_ACCESS_NOT_VIN_LOOKUP",
                },
            ),
        )

    def photo_assets(self, result):
        return {}


class AuthorizedHistoryAdapter:
    """Injected authorized connection; no subscriptions, credentials or charges created.

    The callback maps a provider's documented response into VinHistoryResult.
    PAYG activation and its budget must be supplied explicitly by the operator.
    Asset callbacks must enforce the provider's licence and allowed hosts.
    """

    def __init__(
        self,
        metadata: EvidenceProviderMetadata,
        lookup: Callable,
        assets: Callable | None = None,
        *,
        spending_authorized=False,
    ):
        if metadata.cost_type != "FREE_PUBLIC" and not spending_authorized:
            raise ValueError("Paid provider activation requires explicit spending authorization")
        self.metadata, self.fetch, self.assets = metadata, lookup, assets

    def lookup(self, vin):
        result = VinHistoryResult.model_validate(self.fetch(vin))
        if result.vin != vin or result.attempt.provider.id != self.metadata.id:
            raise ValueError("Provider returned a different VIN or provider identity")
        return result

    def photo_assets(self, result):
        if result.photo_sets and self.metadata.commercial_usage_status != "ALLOWED":
            raise ValueError("Photo caching/publication requires provider permission")
        return self.assets(result) if self.assets else {}


def default_history_providers():
    return [AuditedRestrictedHistoryProvider(audit) for audit in ACCESS_AUDITS]
