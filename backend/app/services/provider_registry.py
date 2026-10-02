from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models.enums import ProviderCostModel
from app.providers.knowledge_public import (
    EPAConfigurationProvider,
    EPAOwnerLogProvider,
    ManufacturerManualProvider,
    ManufacturerSpecificationProvider,
    PublicTechnicalBulletinProvider,
)
from app.providers.official_nhtsa import (
    NHTSACommunicationProvider,
    NHTSAComplaintProvider,
    NHTSARecallProvider,
    NHTSAVariantProvider,
    OfficialHTTPClient,
    OfficialVehicleProvider,
    VPICVehicleProvider,
)
from app.schemas.research import ProviderDefinitionDTO


@dataclass(frozen=True)
class ProviderDefinition:
    id: str
    markets: frozenset[str]
    capabilities: frozenset[str]
    cost_model: ProviderCostModel
    precheck_cost: Decimal
    full_lookup_cost: Decimal
    requires_api_key: bool
    active: bool
    priority: int
    data_classes: frozenset[str]

    def public_dto(self) -> ProviderDefinitionDTO:
        return ProviderDefinitionDTO(
            id=self.id,
            markets=sorted(self.markets),
            capabilities=sorted(self.capabilities),
            cost_model=self.cost_model.value,
            precheck_cost=str(self.precheck_cost),
            full_lookup_cost=str(self.full_lookup_cost),
            requires_api_key=self.requires_api_key,
            active=self.active,
            priority=self.priority,
            data_classes=sorted(self.data_classes),
        )


@dataclass(frozen=True)
class RegisteredProvider:
    definition: ProviderDefinition
    provider: OfficialVehicleProvider


class ProviderRegistry:
    def __init__(self, providers: list[RegisteredProvider]) -> None:
        identifiers = [item.definition.id for item in providers]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Provider registry IDs must be unique")
        self._providers = tuple(providers)

    @property
    def providers(self) -> tuple[RegisteredProvider, ...]:
        return self._providers

    def for_capability(self, *, market: str, capability: str) -> list[RegisteredProvider]:
        normalized_market = "USA" if market.upper() in {"US", "USA"} else market.upper()
        matches = [
            item
            for item in self._providers
            if item.definition.active
            and normalized_market in item.definition.markets
            and capability in item.definition.capabilities
        ]
        return sorted(
            matches,
            key=lambda item: (
                item.definition.full_lookup_cost,
                item.definition.priority,
                item.definition.id,
            ),
        )


def default_provider_registry(
    *, http: OfficialHTTPClient | None = None, include_depth: bool = True
) -> ProviderRegistry:
    shared_http = http or OfficialHTTPClient()

    def register(
        provider: OfficialVehicleProvider,
        *,
        data_classes: set[str],
        priority: int,
    ) -> RegisteredProvider:
        return RegisteredProvider(
            definition=ProviderDefinition(
                id=provider.id,
                markets=frozenset({"USA"}),
                capabilities=frozenset({provider.capability}),
                cost_model=ProviderCostModel.FREE,
                precheck_cost=Decimal("0"),
                full_lookup_cost=Decimal("0"),
                requires_api_key=False,
                active=True,
                priority=priority,
                data_classes=frozenset(data_classes),
            ),
            provider=provider,
        )

    providers = [
        register(
            VPICVehicleProvider(shared_http),
            data_classes={"vehicle_identity", "vehicle_specifications"},
            priority=10,
        ),
        register(
            NHTSAVariantProvider(shared_http),
            data_classes={"vehicle_variants", "configuration_labels"},
            priority=15,
        ),
        register(
            NHTSARecallProvider(shared_http),
            data_classes={"recalls", "safety"},
            priority=20,
        ),
        register(
            NHTSAComplaintProvider(shared_http),
            data_classes={"official_complaint_database", "complaints"},
            priority=30,
        ),
        register(
            NHTSACommunicationProvider(shared_http),
            data_classes={"manufacturer_communications", "service_bulletins"},
            priority=40,
        ),
    ]
    if include_depth:
        providers.extend(
            [
                register(
                    PublicTechnicalBulletinProvider(shared_http),
                    data_classes={"manufacturer_communication"},
                    priority=2,
                ),
                register(
                    ManufacturerSpecificationProvider(shared_http),
                    data_classes={"manufacturer_specification"},
                    priority=1,
                ),
                register(
                    ManufacturerManualProvider(shared_http),
                    data_classes={"manufacturer_maintenance"},
                    priority=2,
                ),
                register(
                    EPAConfigurationProvider(shared_http),
                    data_classes={"official_consumption", "configuration_specification"},
                    priority=20,
                ),
                register(
                    EPAOwnerLogProvider(shared_http),
                    data_classes={"owner_experience", "public_owner_logs"},
                    priority=40,
                ),
            ]
        )
    return ProviderRegistry(providers)
