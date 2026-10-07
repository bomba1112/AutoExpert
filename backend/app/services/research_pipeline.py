from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.enums import (
    ConfidenceLevel,
    DataOrigin,
    EvidenceCategory,
    EvidenceStatus,
    ResearchJobStatus,
    Sentiment,
    SourceTier,
    SourceUsageStatus,
)
from app.models.evidence import KnownIssue, OwnerEvidence, SourceRecord, TechnicalEvidence
from app.models.research import ResearchJob
from app.models.vehicle_knowledge import VehicleKnowledgeProfile
from app.providers.database import DatabaseOwnerReviewProvider
from app.review_engine.engine import OwnerFeedbackEngine
from app.schemas.research import ProviderResult, ResearchJobCreate, VehicleResearchRequest
from app.schemas.reviews import OwnerObservation
from app.services.catalog_names import existing_name
from app.services.dossier import build_vehicle_dossier
from app.services.dossier_synthesis import localized_component
from app.services.knowledge_coverage import DEPTH_VERSION, coverage, research_plan
from app.services.knowledge_depth import enrich_profile, selected_epa
from app.services.provider_registry import ProviderRegistry
from app.services.provider_router import ProviderRouter
from app.services.real_data_quality import RealDataQualityError, validate_real_profile
from app.services.research_rights import (
    permitted_research_registry,
    profile_uses_restricted_epa,
)
from app.services.variant_resolver import VehicleVariantResolver, epa_candidates
from app.services.vehicle_identity import (
    VERSION as IDENTITY_VERSION,
)
from app.services.vehicle_identity import (
    filter_results,
    identity_target,
    powertrain_type,
)

ENRICHMENT_CAPABILITIES = [
    "vehicle_variants",
    "recalls",
    "owner_complaints",
    "manufacturer_communications",
]
AUTOMATIC_BUILD_METHOD = "AUTOMATIC_RESEARCH"


class ResearchPipeline:
    """Builds a source-linked vehicle profile without fixture or seed dependencies."""

    def __init__(
        self,
        db: Session,
        registry: ProviderRegistry,
        *,
        profile_ttl: timedelta = timedelta(days=30),
    ) -> None:
        self.db = db
        self.registry = permitted_research_registry(db, registry) if registry else registry
        self.profile_ttl = profile_ttl

    def create_job(self, *, user_id: str, value: ResearchJobCreate) -> ResearchJob:
        job = ResearchJob(
            user_id=user_id,
            request_key=_request_key(value.vehicle),
            status=ResearchJobStatus.QUEUED,
            language=value.language,
            requested_vehicle=value.vehicle.model_dump(mode="json", exclude_none=True),
            provider_steps=[],
            completed_capabilities=[],
            errors=[],
            resolution_snapshot={},
            dossier_snapshot={},
            metrics={},
            cache_hit=False,
            is_demo=False,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def select_variant(self, job: ResearchJob, candidate_id: str) -> ResearchJob:
        resolution = dict(job.resolution_snapshot or {})
        if not resolution.get("needs_user_selection"):
            raise ValueError("Research job is not waiting for a variant selection")
        candidate_ids = {item.get("id") for item in resolution.get("candidates", [])}
        if candidate_id not in candidate_ids:
            raise ValueError("Selected variant is not one of this research job's candidates")
        resolution["selected_candidate_id"] = candidate_id
        # A user's selection must never poison the cache of an ambiguous base query.
        job.request_key = hashlib.sha256(
            (job.request_key + ":" + candidate_id).encode()
        ).hexdigest()
        job.resolution_snapshot = resolution
        job.status = ResearchJobStatus.QUEUED
        job.completed_at = None
        self.db.commit()
        self.db.refresh(job)
        return job

    def execute(self, job: ResearchJob) -> ResearchJob:
        if job.status == ResearchJobStatus.COMPLETE:
            return job
        if job.status == ResearchJobStatus.PARTIAL and not job.resolution_snapshot.get(
            "needs_user_selection"
        ):
            return job
        request = VehicleResearchRequest.model_validate(job.requested_vehicle)
        started_perf = time.perf_counter()
        job.status = ResearchJobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        self.db.commit()

        try:
            existing = self._fresh_profile(job.request_key)
            if existing is not None:
                dossier = self._dossier(existing, job.language)
                job.vehicle_profile_id = existing.id
                job.status = (
                    ResearchJobStatus.PARTIAL
                    if existing.dossier_seed.get("identity_integrity", {}).get("state")
                    in {"VARIANT_CONFLICT", "IDENTITY_INCOMPLETE"}
                    else ResearchJobStatus.COMPLETE
                )
                job.cache_hit = True
                job.completed_capabilities = list(
                    existing.dossier_seed.get("completed_capabilities", [])
                )
                job.resolution_snapshot = dict(existing.dossier_seed.get("resolution", {}))
                job.dossier_snapshot = dossier.model_dump(mode="json")
                job.metrics = {
                    "api_requests": 0,
                    "sources_created": 0,
                    "evidence_created": 0,
                    "profile_reused": True,
                    "research_time_seconds": round(time.perf_counter() - started_perf, 4),
                }
                job.completed_at = datetime.now(UTC)
                self.db.commit()
                self.db.refresh(job)
                return job

            router = ProviderRouter(self.db, self.registry)
            identity_results = router.fetch(request, ["vehicle_identity"])
            identity = identity_results[0]
            if identity.status != EvidenceStatus.CONFIRMED or not identity.records:
                job.provider_steps = [_step(result) for result in identity_results]
                job.errors = [
                    f"{result.provider_id}: {result.error}"
                    for result in identity_results
                    if result.error
                ]
                no_market_provider = identity.provider_id == "none" and request.identifier
                job.status = (
                    ResearchJobStatus.PARTIAL if no_market_provider else ResearchJobStatus.FAILED
                )
                if not job.errors:
                    job.errors = [
                        (
                            f"No official identity provider is active for {request.market}; "
                            "identifier was accepted but vehicle fields remain unresolved"
                            if no_market_provider
                            else "Official vehicle identity could not be confirmed"
                        )
                    ]
                job.resolution_snapshot = _insufficient_resolution(request)
                job.metrics = {
                    "api_requests": sum(item.api_requests for item in identity_results),
                    "sources_created": 0,
                    "evidence_created": 0,
                    "profile_reused": False,
                    "research_time_seconds": round(time.perf_counter() - started_perf, 4),
                }
                job.completed_at = datetime.now(UTC)
                self.db.commit()
                self.db.refresh(job)
                return job

            effective_request = _effective_request(request, identity.records[0])
            # Establish the VIN boundary before any technical/model synthesis.
            initial_target = identity_target(effective_request, identity.records[0])
            enrichment_results = router.fetch(effective_request, ENRICHMENT_CAPABILITIES)
            results = identity_results + enrichment_results
            job.provider_steps = [_step(result) for result in results]
            job.completed_capabilities = [
                result.capability
                for result in results
                if result.error is None and result.status == EvidenceStatus.CONFIRMED
            ]
            job.errors = [
                f"{result.provider_id}: {result.error}" for result in results if result.error
            ]
            variant_result = next(
                (result for result in results if result.capability == "vehicle_variants"),
                None,
            )
            selected_id = job.resolution_snapshot.get("selected_candidate_id")
            configuration_results = []
            variants = variant_result.records if variant_result else []
            if not effective_request.vin and any(
                p.definition.id == "epa_vehicle_configuration" for p in self.registry.providers
            ):
                configuration_results = router.fetch(
                    effective_request,
                    ["fuel_economy"],
                    context={"identity": identity.records[0], "depth_version": DEPTH_VERSION},
                )
                if configuration_results and configuration_results[0].records:
                    variants = epa_candidates(configuration_results[0].records)
                results.extend(configuration_results)
            resolution = VehicleVariantResolver().resolve(
                effective_request,
                identity.records,
                variants,
                selected_candidate_id=selected_id,
            )
            _validate_identity(effective_request, identity.records)
            if not request.vin and str(resolution.get("selected_candidate_id") or "").startswith(
                "epa:"
            ):
                identity = identity.model_copy(deep=True)
                identity.records[0]["selected_epa_id"] = resolution["selected_candidate_id"].split(
                    ":", 1
                )[1]
                results[0] = identity
            if resolution["needs_user_selection"]:
                job.resolution_snapshot = resolution
                job.status = ResearchJobStatus.PARTIAL
                job.metrics = {
                    "api_requests": sum(item.api_requests for item in results),
                    "sources_created": 0,
                    "evidence_created": 0,
                    "profile_reused": False,
                    "research_time_seconds": round(time.perf_counter() - started_perf, 4),
                }
                job.completed_at = datetime.now(UTC)
                self.db.commit()
                self.db.refresh(job)
                return job

            plan = []
            if any(
                item.definition.id == "epa_vehicle_configuration"
                for item in self.registry.providers
            ):
                plan = research_plan(coverage([]), self.registry, effective_request.market)
                context = {"identity": identity.records[0], "depth_version": DEPTH_VERSION}
                depth_results = configuration_results or router.fetch(
                    effective_request, ["fuel_economy"], context=context
                )
                epa = selected_epa(depth_results[-1], identity.records[0])
                context = {
                    **context,
                    "epa_vehicle": epa,
                    "identity_target": identity_target(effective_request, identity.records[0], epa),
                }
                depth_results.extend(
                    router.fetch(
                        effective_request,
                        [
                            "technical_specs",
                            "maintenance_specs",
                            "technical_bulletins",
                            "owner_experience",
                        ],
                        context=context,
                    )
                )
                results = [r for r in results if r.capability != "fuel_economy"] + depth_results
                job.provider_steps = [_step(result) for result in results]
                for step in plan:
                    fetched = [r for r in depth_results if r.capability == step["capability"]]
                    step["status"] = (
                        "COMPLETE"
                        if any(r.records and not r.error for r in fetched)
                        else "UNAVAILABLE"
                    )

            target = identity_target(effective_request, identity.records[0], epa if plan else None)
            results, rejected = filter_results(results, target)
            profile, sources_created, evidence_created = self._persist_profile(
                request=effective_request,
                request_key=job.request_key,
                resolution=resolution,
                results=results,
                plan=plan,
            )
            profile.dossier_seed = {
                **profile.dossier_seed,
                "variant_rejections": rejected,
                "initial_identity_target": initial_target,
            }
            integrity = profile.dossier_seed.get("identity_integrity", {})
            resolution["identity_state"] = integrity.get("state", "IDENTITY_INCOMPLETE")
            resolution["powertrain_type"] = target["powertrain_type"]
            resolution["fuel"] = target["fuel"]
            resolution["identity_conflicts"] = integrity.get("critical_conflicts", [])
            if integrity.get("state") != "RESOLVED":
                resolution["unresolved_fields"] = sorted(
                    set(resolution["unresolved_fields"] + integrity.get("missing_fields", []))
                )
            profile.dossier_seed = {**profile.dossier_seed, "resolution": resolution}
            dossier = self._dossier(profile, job.language)
            validate_real_profile(profile, dossier=dossier)
            job.vehicle_profile_id = profile.id
            job.resolution_snapshot = resolution
            job.dossier_snapshot = dossier.model_dump(mode="json")
            job.cache_hit = False
            job.status = (
                ResearchJobStatus.PARTIAL
                if job.errors or (plan and integrity.get("state") != "RESOLVED")
                else ResearchJobStatus.COMPLETE
            )
            job.metrics = {
                "api_requests": sum(item.api_requests for item in results),
                "sources_created": sources_created,
                "evidence_created": evidence_created,
                "profile_reused": False,
                "research_time_seconds": round(time.perf_counter() - started_perf, 4),
            }
            job.completed_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(job)
            return job
        except (RealDataQualityError, ValueError) as error:
            self.db.rollback()
            job = self.db.get(ResearchJob, job.id)
            if job is None:
                raise
            job.status = ResearchJobStatus.FAILED
            job.errors = [f"Quality gate: {error}"]
            job.completed_at = datetime.now(UTC)
            job.metrics = {
                "api_requests": 0,
                "sources_created": 0,
                "evidence_created": 0,
                "profile_reused": False,
                "research_time_seconds": round(time.perf_counter() - started_perf, 4),
            }
            self.db.commit()
            self.db.refresh(job)
            return job

    def _fresh_profile(self, request_key: str) -> VehicleKnowledgeProfile | None:
        threshold = datetime.now(UTC) - self.profile_ttl
        candidates = list(
            self.db.scalars(
                select(VehicleKnowledgeProfile)
                .where(VehicleKnowledgeProfile.data_origin == DataOrigin.REAL)
                .order_by(VehicleKnowledgeProfile.freshness_at.desc())
            )
        )
        for profile in candidates:
            if profile_uses_restricted_epa(self.db, profile):
                continue
            freshness = profile.freshness_at
            if freshness.tzinfo is None:
                freshness = freshness.replace(tzinfo=UTC)
            if (
                profile.dossier_seed.get("build_method") == AUTOMATIC_BUILD_METHOD
                and profile.dossier_seed.get("request_key") == request_key
                and (
                    not profile.dossier_seed.get("knowledge_depth")
                    or profile.dossier_seed.get("identity_integrity", {}).get("version")
                    == IDENTITY_VERSION
                )
                and freshness >= threshold
                and (
                    not any(
                        item.definition.id == "epa_vehicle_configuration"
                        for item in self.registry.providers
                    )
                    or profile.dossier_seed.get("knowledge_depth", {}).get("version")
                    == DEPTH_VERSION
                )
            ):
                return profile
        return None

    def _persist_profile(
        self,
        *,
        request: VehicleResearchRequest,
        request_key: str,
        resolution: dict,
        results: list[ProviderResult],
        plan: list[dict] | None = None,
    ) -> tuple[VehicleKnowledgeProfile, int, int]:
        result_by_capability = {item.capability: item for item in results}
        identity = result_by_capability["vehicle_identity"]
        sources: dict[str, SourceRecord] = {}
        for result in results:
            if result.error is not None or result.status != EvidenceStatus.CONFIRMED:
                continue
            if (
                result.capability
                in {
                    "technical_specs",
                    "maintenance_specs",
                    "technical_bulletins",
                    "fuel_economy",
                    "owner_experience",
                }
                and not result.records
            ):
                continue
            source = _source_from_result(request, result)
            self.db.add(source)
            self.db.flush()
            sources[result.capability] = source

        identity_source = sources.get("vehicle_identity")
        if identity_source is None:
            raise RealDataQualityError("Confirmed identity has no persisted source")

        decoded = identity.records[0]
        catalog_variant = self._catalog_variant(request, resolution, decoded, identity_source)
        evidence: list[TechnicalEvidence] = []
        evidence.extend(
            _identity_evidence(
                catalog_variant,
                request,
                resolution,
                decoded,
                identity_source,
            )
        )

        variant_result = result_by_capability.get("vehicle_variants")
        if variant_result and "vehicle_variants" in sources:
            evidence.extend(
                _variant_evidence(
                    catalog_variant,
                    resolution,
                    variant_result,
                    sources["vehicle_variants"],
                )
            )

        recall_result = result_by_capability.get("recalls")
        if recall_result and "recalls" in sources:
            evidence.extend(_recall_evidence(catalog_variant, recall_result, sources["recalls"]))
        communication_result = result_by_capability.get("manufacturer_communications")
        if communication_result and "manufacturer_communications" in sources:
            evidence.extend(
                _communication_evidence(
                    catalog_variant,
                    communication_result,
                    sources["manufacturer_communications"],
                )
            )
        self.db.add_all(evidence)
        self.db.flush()

        complaint_result = result_by_capability.get("owner_complaints")
        if complaint_result and "owner_complaints" in sources:
            self.db.add_all(
                _owner_evidence(catalog_variant, complaint_result, sources["owner_complaints"])
            )
            self.db.flush()

        profile = VehicleKnowledgeProfile(
            vehicle_variant_id=catalog_variant.id,
            make=resolution["make"],
            model=resolution["model"],
            generation=resolution.get("generation") or "UNRESOLVED",
            production_year_start=request.year,
            production_year_end=request.year,
            market=request.market,
            year=request.year,
            engine=resolution["engine_candidates"][0]
            if len(resolution["engine_candidates"]) == 1
            else None,
            engine_code=resolution["engine_code_candidates"][0]
            if len(resolution["engine_code_candidates"]) == 1
            else None,
            transmission=resolution["transmission_candidates"][0]
            if len(resolution["transmission_candidates"]) == 1
            else None,
            drivetrain=resolution["drivetrain_candidates"][0]
            if len(resolution["drivetrain_candidates"]) == 1
            else None,
            body=(resolution.get("candidates") or [{}])[0].get("body")
            or (decoded.get("body_class") if request.vin else None),
            fuel=decoded.get("fuel_type_primary") if request.vin else None,
            profile_version="6.1.0-consumer.1",
            freshness_at=max(item.retrieved_at for item in results if item.error is None),
            dossier_seed={
                "build_method": AUTOMATIC_BUILD_METHOD,
                "request_key": request_key,
                "resolution": resolution,
                "provider_ids": [item.provider_id for item in results],
                "completed_capabilities": [
                    item.capability
                    for item in results
                    if item.error is None and item.status == EvidenceStatus.CONFIRMED
                ],
                "records_by_capability": {item.capability: len(item.records) for item in results},
                "vin_identity": {
                    key: decoded.get(key)
                    for key in (
                        "vin",
                        "series",
                        "series2",
                        "trim",
                        "trim2",
                        "engine_model",
                        "displacement_l",
                        "engine_cylinders",
                        "engine_configuration",
                        "engine_hp",
                        "engine_kw",
                        "fuel_type_secondary",
                        "electrification_level",
                        "battery_type",
                        "battery_kwh",
                        "battery_info",
                        "other_engine_info",
                        "transmission_speeds",
                        "transmission_style",
                        "drive_type",
                        "body_class",
                        "fuel_type_primary",
                        "plant_country",
                    )
                    if decoded.get(key) not in {None, ""}
                },
                "manual_seed_used": False,
            },
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        profile.sources.extend(sources.values())
        base_scope = {
            "make": request.make,
            "model": request.model,
            "year": request.year,
            "market": request.market,
        }
        for item in evidence:
            exact = item.conditions.get("consumer_kind") in {
                "vehicle_identity",
                "engine_identity",
                "transmission_identity",
                "body_identity",
            } and bool(request.vin)
            item.conditions = {
                **item.conditions,
                "applicability": item.conditions.get("applicability")
                or {**base_scope, **({"vin": request.vin} if exact else {})},
                "applicability_class": "EXACT_VIN" if exact else "MODEL_YEAR",
            }
        profile.evidence.extend(evidence)
        self.db.add(profile)
        self.db.flush()
        extra_count = (
            enrich_profile(self.db, profile, request, results, sources, plan) if plan else 0
        )
        return profile, len(sources), len(evidence) + extra_count

    def _catalog_variant(
        self,
        request: VehicleResearchRequest,
        resolution: dict,
        decoded: dict,
        identity_source: SourceRecord,
    ) -> VehicleVariant:
        make_name = resolution["make"]
        model_name = resolution["model"]
        make_key = _normalized(make_name)
        model_key = _normalized(model_name)
        make = existing_name(self.db, make_name)
        if make is None:
            make = VehicleMake(name=make_name, normalized_name=make_key, is_demo=False)
            self.db.add(make)
            self.db.flush()
        model = existing_name(self.db, model_name, make_id=make.id)
        if model is None:
            model = VehicleModel(
                make_id=make.id,
                name=model_name,
                normalized_name=model_key,
                is_demo=False,
            )
            self.db.add(model)
            self.db.flush()
        generation_code = resolution.get("generation") or "UNRESOLVED"
        generation = self.db.scalar(
            select(VehicleGeneration).where(
                VehicleGeneration.model_id == model.id,
                VehicleGeneration.code == generation_code,
                VehicleGeneration.start_year == request.year,
            )
        )
        if generation is None:
            generation = VehicleGeneration(
                model_id=model.id,
                name=generation_code,
                code=generation_code,
                start_year=request.year,
                end_year=request.year,
                is_demo=False,
            )
            self.db.add(generation)
            self.db.flush()

        engine = (
            resolution["engine_candidates"][0]
            if len(resolution["engine_candidates"]) == 1
            else None
        )
        engine_code = (
            resolution["engine_code_candidates"][0]
            if len(resolution["engine_code_candidates"]) == 1
            else None
        )
        transmission = (
            resolution["transmission_candidates"][0]
            if len(resolution["transmission_candidates"]) == 1
            else None
        )
        drivetrain = (
            resolution["drivetrain_candidates"][0]
            if len(resolution["drivetrain_candidates"]) == 1
            else None
        )
        displacement = _decimal(decoded.get("displacement_l")) if request.vin else None
        variant = VehicleVariant(
            generation_id=generation.id,
            specification_source_id=identity_source.id,
            market="US" if request.market == "USA" else request.market[:2],
            name=f"{request.year} {make_name} {model_name} — automatically resolved",
            year_from=request.year,
            year_to=request.year,
            engine_code=engine_code,
            engine=engine,
            transmission=transmission,
            drivetrain=drivetrain,
            body=(resolution.get("candidates") or [{}])[0].get("body")
            or (decoded.get("body_class") if request.vin else None),
            fuel=decoded.get("fuel_type_primary") if request.vin else None,
            displacement_l=displacement,
            specifications={
                "resolution_status": "PARTIAL" if resolution["unresolved_fields"] else "COMPLETE",
                "user_engine_hint": request.engine_hint,
                "user_hint_confirmed": False if request.engine_hint and not request.vin else None,
                "source_provider": identity_source.publisher,
            },
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        self.db.add(variant)
        self.db.flush()
        return variant

    def _dossier(self, profile: VehicleKnowledgeProfile, language: str):  # noqa: ANN202
        issues = list(
            self.db.scalars(
                select(KnownIssue).where(
                    KnownIssue.vehicle_variant_id == profile.vehicle_variant_id,
                    KnownIssue.severity.is_not(None),
                )
            )
        )
        rows = DatabaseOwnerReviewProvider(self.db).observations_for(profile.vehicle_variant_id)
        official_rows = [
            item
            for item in rows
            if item.source.source_type == "OWNER_SUBMISSIONS_GOVERNMENT_REPOSITORY"
        ]
        owner_rows = [item for item in rows if item not in official_rows]
        return build_vehicle_dossier(
            profile,
            language=language,
            known_issues=issues,
            owner_feedback=OwnerFeedbackEngine().aggregate(_owner_observations(owner_rows)),
            owner_source_ids=list(dict.fromkeys(item.source_id for item in owner_rows)),
            official_complaints_feedback=OwnerFeedbackEngine().aggregate(
                _owner_observations(official_rows, normalize_components=True)
            ),
            official_complaint_source_ids=list(
                dict.fromkeys(item.source_id for item in official_rows)
            ),
        )


def _request_key(request: VehicleResearchRequest) -> str:
    canonical = {
        "make": _normalized(request.make),
        "model": _normalized(request.model),
        "year": request.year,
        "market": request.market,
        "engine_hint": _normalized(request.engine_hint),
        "identifier": request.identifier,
        "identifier_type": request.identifier_type.value,
    }
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _effective_request(request: VehicleResearchRequest, identity: dict) -> VehicleResearchRequest:
    make = identity.get("make") or request.make
    model = identity.get("model") or request.model
    year = identity.get("model_year") or request.year
    if not make or not model or not year:
        raise RealDataQualityError("Official identity did not resolve make, model, and year")
    return VehicleResearchRequest(
        make=str(make),
        model=str(model),
        year=int(year),
        market=request.market,
        engine_hint=request.engine_hint,
        powertrain_hint=request.powertrain_hint,
        fuel_hint=request.fuel_hint,
        transmission_hint=request.transmission_hint,
        drivetrain_hint=request.drivetrain_hint,
        trim_hint=request.trim_hint,
        identifier=request.identifier,
        identifier_type=request.identifier_type,
    )


def _insufficient_resolution(request: VehicleResearchRequest) -> dict:
    return {
        "make": request.make,
        "model": request.model,
        "year": request.year,
        "market": request.market,
        "generation": None,
        "engine_candidates": [],
        "engine_code_candidates": [],
        "transmission_candidates": [],
        "drivetrain_candidates": [],
        "ambiguity": True,
        "needs_user_selection": False,
        "unresolved_fields": [
            "make",
            "model",
            "year",
            "generation",
            "engine",
            "engine_code",
            "transmission",
            "drivetrain",
        ],
        "notes": ["No official provider is active for this market and identifier type"],
        "status": "INSUFFICIENT_DATA",
        "candidates": [],
        "selected_candidate_id": None,
    }


def _validate_identity(request: VehicleResearchRequest, records: list[dict]) -> None:
    identities = {
        (
            _normalized(item.get("make")),
            _normalized(item.get("model")),
            int(item.get("model_year") or request.year),
        )
        for item in records
    }
    expected = (_normalized(request.make), _normalized(request.model), request.year)
    if expected not in identities:
        raise RealDataQualityError("Official identity conflicts with the requested vehicle")
    if len(identities) != 1:
        raise RealDataQualityError("Official provider returned contradictory vehicle identities")


def _source_from_result(
    request: VehicleResearchRequest,
    result: ProviderResult,
) -> SourceRecord:
    definitions = {
        "technical_bulletins": (
            "Manufacturer technical communication",
            str(request.make),
            "MANUFACTURER_TECHNICAL_DOCUMENT",
            SourceTier.A,
        ),
        "maintenance_specs": (
            "Manufacturer owner manual",
            str(request.make),
            "MANUFACTURER_MANUAL",
            SourceTier.A,
        ),
        "technical_specs": (
            "Manufacturer specification document",
            "Ford Motor Company" if request.make == "Ford" else str(request.make),
            "MANUFACTURER_SPECIFICATION",
            SourceTier.A,
        ),
        "fuel_economy": (
            "EPA vehicle configuration and fuel economy",
            "US Department of Energy / EPA",
            "GOVERNMENT_FUEL_ECONOMY",
            SourceTier.A,
        ),
        "owner_experience": (
            "My MPG shared owner fuel logs",
            "FuelEconomy.gov My MPG contributors",
            "PUBLIC_OWNER_LOG",
            SourceTier.C,
        ),
        "vehicle_identity": (
            "vPIC vehicle identity lookup",
            "National Highway Traffic Safety Administration",
            "GOVERNMENT_VEHICLE_API",
            SourceTier.A,
        ),
        "vehicle_variants": (
            "NHTSA vehicle configuration labels",
            "National Highway Traffic Safety Administration",
            "GOVERNMENT_CONFIGURATION_API",
            SourceTier.A,
        ),
        "recalls": (
            "NHTSA recalls by vehicle",
            "National Highway Traffic Safety Administration",
            "GOVERNMENT_RECALL_API",
            SourceTier.A,
        ),
        "owner_complaints": (
            "NHTSA consumer complaints by vehicle",
            "National Highway Traffic Safety Administration",
            "OWNER_SUBMISSIONS_GOVERNMENT_REPOSITORY",
            SourceTier.C,
        ),
        "manufacturer_communications": (
            "NHTSA manufacturer communications bulk data",
            "National Highway Traffic Safety Administration",
            "MANUFACTURER_COMMUNICATION",
            SourceTier.A,
        ),
    }
    title, publisher, source_type, tier = definitions[result.capability]
    return SourceRecord(
        title=f"{title}: {request.year} {request.make} {request.model}",
        publisher=publisher,
        url=result.source_url,
        source_type=source_type,
        source_tier=tier,
        data_origin=DataOrigin.REAL,
        market="US" if request.market == "USA" else request.market[:2],
        language="en",
        published_at=None,
        retrieved_at=result.retrieved_at,
        notes=(
            f"Automatically retrieved by {result.provider_id}; normalized records: "
            f"{len(result.records)}. Empty model-year results do not prove a specific VIN is clear."
        ),
        confidence=ConfidenceLevel.HIGH if tier == SourceTier.A else ConfidenceLevel.MEDIUM,
        usage_status=SourceUsageStatus.ACTIVE,
        is_demo=False,
    )


def _identity_evidence(
    variant: VehicleVariant,
    request: VehicleResearchRequest,
    resolution: dict,
    decoded: dict,
    source: SourceRecord,
) -> list[TechnicalEvidence]:
    identity = f"vPIC matched {request.year} {resolution['make']} {resolution['model']}."
    identity_values = {
        "year": request.year,
        "make": resolution["make"],
        "model": resolution["model"],
        "trim": decoded.get("trim"),
        "series": decoded.get("series"),
        "drivetrain": decoded.get("drive_type"),
        "body": decoded.get("body_class"),
        "powertrain_type": powertrain_type(decoded),
    }
    evidence = [
        _evidence(
            variant,
            source,
            EvidenceCategory.OTHER,
            "Automatic Vehicle Identity",
            identity,
            EvidenceStatus.CONFIRMED,
            "general_information",
            extra={
                "consumer_kind": "vehicle_identity",
                "consumer_values": identity_values,
                "exact_vin_priority": bool(request.vin),
            },
        ),
        _evidence(
            variant,
            source,
            EvidenceCategory.OTHER,
            "Automatic Research Verdict",
            (
                "Official US databases identify the model and model year, but unresolved "
                "variant fields and the condition of a specific vehicle require further evidence."
            ),
            EvidenceStatus.ESTIMATE,
            "expert_verdict",
            extra={
                "consumer_kind": "research_verdict",
                "consumer_values": {
                    "unresolved_fields": resolution.get("unresolved_fields", []),
                },
            },
        ),
        _evidence(
            variant,
            source,
            EvidenceCategory.OTHER,
            "USA Official Data Scope",
            (
                "The profile uses US government model-year data. Recall completion and the "
                "condition of a specific vehicle must be checked by VIN and physical inspection."
            ),
            EvidenceStatus.CONFIRMED,
            "usa_vehicle",
            extra={"consumer_kind": "usa_scope"},
        ),
    ]
    engine_values = {
        "engine_model": decoded.get("engine_model"),
        "displacement_l": decoded.get("displacement_l"),
        "cylinders": decoded.get("engine_cylinders"),
        "configuration": decoded.get("engine_configuration"),
        "fuel": decoded.get("fuel_type_primary"),
        "engine_power_hp": decoded.get("engine_hp"),
        "powertrain_type": powertrain_type(decoded),
    }
    if request.vin and any(value not in {None, ""} for value in engine_values.values()):
        evidence.append(
            _evidence(
                variant,
                source,
                EvidenceCategory.ENGINE,
                "vPIC Decoded Engine Configuration",
                f"vPIC decoded engine fields: {engine_values}.",
                EvidenceStatus.CONFIRMED,
                "engine",
                extra={
                    "consumer_kind": "engine_identity",
                    "consumer_values": engine_values,
                },
            )
        )
    transmission = _transmission(decoded) if request.vin else None
    if transmission:
        evidence.append(
            _evidence(
                variant,
                source,
                EvidenceCategory.TRANSMISSION,
                "vPIC Decoded Transmission",
                f"vPIC decoded transmission: {transmission}.",
                EvidenceStatus.CONFIRMED,
                "transmission",
                extra={
                    "consumer_kind": "transmission_identity",
                    "consumer_values": {"transmission": transmission},
                },
            )
        )
    if request.vin and decoded.get("body_class"):
        evidence.append(
            _evidence(
                variant,
                source,
                EvidenceCategory.BODY,
                "vPIC Decoded Body Class",
                f"vPIC decoded body class: {decoded['body_class']}.",
                EvidenceStatus.CONFIRMED,
                "body",
                extra={
                    "consumer_kind": "body_identity",
                    "consumer_values": {"body": decoded["body_class"]},
                },
            )
        )
    return evidence


def _recall_evidence(
    variant: VehicleVariant,
    result: ProviderResult,
    source: SourceRecord,
) -> list[TechnicalEvidence]:
    if not result.records:
        if isinstance(result.raw_payload, dict) and result.raw_payload.get(
            "variant_rejected_count"
        ):
            return []
        return [
            _evidence(
                variant,
                source,
                EvidenceCategory.SAFETY,
                "NHTSA Recall Query Result",
                (
                    "The NHTSA model-year query returned no recall records at retrieval time. "
                    "This is not proof that a specific VIN has no open recall."
                ),
                EvidenceStatus.CONFIRMED,
                "recalls_tsb",
                extra={"query_returned_zero": True},
            )
        ]
    return [
        _evidence(
            variant,
            source,
            EvidenceCategory.SAFETY,
            f"Recall {record['campaign_number']}",
            (
                f"NHTSA campaign {record['campaign_number']} — {record['component']}: "
                f"{record['summary']}"
            ),
            EvidenceStatus.CONFIRMED,
            "recalls_tsb",
            extra={
                "campaign_number": record["campaign_number"],
                "component": record["component"],
                "summary": record.get("summary"),
                "consequence": record.get("consequence"),
                "remedy": record.get("remedy"),
                "make": record.get("make"),
                "model": record.get("model"),
                "model_year": record.get("model_year"),
                "consumer_kind": "recall",
                "applicability": record.get("applicability", {}),
            },
        )
        for record in result.records
    ]


def _variant_evidence(
    variant: VehicleVariant,
    resolution: dict,
    result: ProviderResult,
    source: SourceRecord,
) -> list[TechnicalEvidence]:
    selected_id = resolution.get("selected_candidate_id")
    selected = next(
        (item for item in result.records if item.get("candidate_id") == selected_id),
        None,
    )
    if selected is None:
        return []
    return [
        _evidence(
            variant,
            source,
            EvidenceCategory.OTHER,
            "Official Vehicle Configuration",
            f"NHTSA configuration label: {selected['label']}.",
            EvidenceStatus.CONFIRMED,
            "general_information",
            extra={
                "candidate_id": selected_id,
                "provider_evidence_ids": selected.get("evidence_ids", []),
            },
        )
    ]


def _communication_evidence(
    variant: VehicleVariant,
    result: ProviderResult,
    source: SourceRecord,
) -> list[TechnicalEvidence]:
    if not result.records:
        return [
            _evidence(
                variant,
                source,
                EvidenceCategory.MAINTENANCE,
                "Manufacturer Communication Query Result",
                (
                    "The official manufacturer-communication archive returned no matching "
                    "model-year records at retrieval time."
                ),
                EvidenceStatus.CONFIRMED,
                "recalls_tsb",
                extra={"query_returned_zero": True},
            )
        ]
    evidence: list[TechnicalEvidence] = []
    seen: set[tuple[str, str]] = set()
    for record in result.records:
        component = str(record.get("component") or "").strip()
        summary = str(record.get("summary") or "").strip()
        document_id = str(record.get("document_id") or "UNKNOWN")
        dedupe_key = (document_id.casefold(), " ".join(summary.casefold().split()))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        information_quality = "MEANINGFUL" if component and len(summary) >= 20 else "LOW"
        evidence.append(
            _evidence(
                variant,
                source,
                EvidenceCategory.MAINTENANCE,
                f"Manufacturer Communication {document_id}",
                (
                    f"Manufacturer communication {document_id} — "
                    f"{component or 'component not specified'}: "
                    f"{summary or 'summary not provided in the bulk record'}"
                ),
                EvidenceStatus.CONFIRMED,
                "recalls_tsb",
                extra={
                    "nhtsa_id": record.get("nhtsa_id"),
                    "document_id": document_id,
                    "component": component or None,
                    "summary": summary or None,
                    "communication_date": record.get("communication_date"),
                    "information_quality": information_quality,
                    "consumer_kind": "manufacturer_communication",
                    "applicability": record.get("applicability", {}),
                },
            )
        )
    return evidence


def _owner_evidence(
    variant: VehicleVariant,
    result: ProviderResult,
    source: SourceRecord,
) -> list[OwnerEvidence]:
    rows = []
    for record in result.records:
        material_key = f"NHTSA-ODI-{record['odi_number']}"
        component = str(record.get("components") or "other")
        summary = str(record.get("normalized_summary") or "").strip()
        dedupe_key = hashlib.sha256(
            f"{variant.id}|{material_key}|{component.casefold()}|{summary.casefold()}".encode()
        ).hexdigest()
        rows.append(
            OwnerEvidence(
                applicability=record.get("applicability", {}),
                applicability_class=record.get("applicability_class", "MODEL_YEAR"),
                source_id=source.id,
                vehicle_variant_id=variant.id,
                owner_identity_key=None,
                material_identity_key=material_key,
                dedupe_key=dedupe_key,
                mileage_km=None,
                component=component[:100],
                topic=_owner_topic(component),
                sentiment=Sentiment.NEGATIVE,
                issue_type="OWNER_ALLEGATION",
                excerpt=None,
                summary=summary or "NHTSA owner complaint; narrative was not supplied.",
                observed_at=None,
                is_demo=False,
                data_origin=DataOrigin.REAL,
            )
        )
    return rows


def _evidence(
    variant: VehicleVariant,
    source: SourceRecord,
    category: EvidenceCategory,
    title: str,
    statement: str,
    status: EvidenceStatus,
    section_key: str,
    *,
    extra: dict | None = None,
) -> TechnicalEvidence:
    conditions = {"section_key": section_key, "automatic_research": True}
    conditions.update(extra or {})
    return TechnicalEvidence(
        vehicle_variant_id=variant.id,
        source_id=source.id,
        category=category,
        title=title[:240],
        statement=statement,
        status=status,
        confidence=(
            ConfidenceLevel.HIGH if status == EvidenceStatus.CONFIRMED else ConfidenceLevel.MEDIUM
        ),
        market="US",
        conditions=conditions,
        is_demo=False,
        data_origin=DataOrigin.REAL,
    )


def _step(result: ProviderResult) -> dict:
    completed = result.retrieved_at
    started = completed - timedelta(milliseconds=result.duration_ms)
    return {
        "provider_id": result.provider_id,
        "capability": result.capability,
        "status": ("CACHE_HIT" if result.from_cache else "FAILED" if result.error else "COMPLETE"),
        "records_count": len(result.records),
        "source_url": result.source_url,
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "duration_ms": result.duration_ms,
        "from_cache": result.from_cache,
        "error": result.error,
        "http_status": result.http_status,
    }


def _transmission(record: dict) -> str | None:
    style = str(record.get("transmission_style") or "").strip()
    speeds = str(record.get("transmission_speeds") or "").strip()
    if style and speeds:
        return f"{speeds}-speed {style}"
    return style or (f"{speeds}-speed" if speeds else None)


def _normalized(value: object) -> str:
    return "".join(character for character in str(value or "").casefold() if character.isalnum())


def _decimal(value: object) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in {None, ""} else None
    except (InvalidOperation, ValueError):
        return None


def _owner_topic(components: str) -> str:
    first = components.split(",", 1)[0].strip().casefold()
    return first[:120] or "other"


def _owner_observations(
    rows: list[OwnerEvidence], *, normalize_components: bool = False
) -> list[OwnerObservation]:
    return [
        OwnerObservation(
            id=item.id,
            material_identity_key=item.material_identity_key,
            owner_identity_key=item.owner_identity_key,
            topic=localized_component(item.topic, "en") if normalize_components else item.topic,
            component=item.component,
            sentiment=item.sentiment,
            summary=item.summary,
            source_id=item.source_id,
            mileage_km=item.mileage_km,
            observed_at=item.observed_at.isoformat() if item.observed_at else None,
            is_demo=item.is_demo,
        )
        for item in rows
    ]
