"""Attach Stage 6.3 evidence without reworking the technical vehicle profile."""

from datetime import UTC, datetime, timedelta

from app.providers.owner_reviews import CarComplaintsOwnerProvider
from app.schemas.research_evidence import OwnerReviewResult, ProviderAttempt, ResearchState
from app.services.history_research import research_history
from app.services.owner_experience import aggregate_issues, owner_applicability, owner_sample

VERSION = "6.3.0"
RESTRICTED_OWNER_SOURCES = [
    {
        "provider_id": "reddit",
        "url": "https://www.reddit.com/robots.txt",
        "reason": "ROBOTS_DISALLOW",
        "state": "PROVIDER_UNAVAILABLE",
    },
    {
        "provider_id": "toyotanation",
        "url": "https://www.toyotanation.com/robots.txt",
        "reason": "ROBOTS_DISALLOW_ASSISTANT",
        "state": "PROVIDER_UNAVAILABLE",
    },
    {
        "provider_id": "hyundai_forums",
        "url": "https://www.hyundai-forums.com/robots.txt",
        "reason": "ROBOTS_DISALLOW_ASSISTANT",
        "state": "PROVIDER_UNAVAILABLE",
    },
    {
        "provider_id": "cars_com",
        "url": "https://www.cars.com/about/terms/",
        "reason": "TERMS_PROHIBIT_AUTOMATION_AND_HTTP_403",
        "state": "PROVIDER_UNAVAILABLE",
    },
    {
        "provider_id": "edmunds",
        "url": "https://www.edmunds.com/robots.txt",
        "reason": "AI_CRAWLER_RESTRICTED_NOT_IMPORTED",
        "state": "PROVIDER_UNAVAILABLE",
    },
    {
        "provider_id": "carsurvey",
        "url": "https://www.carsurvey.org/robots.txt",
        "reason": "ROBOTS_TIMEOUT",
        "state": "PROVIDER_UNAVAILABLE",
    },
]


def target_for_profile(profile):
    depth = profile.dossier_seed.get("knowledge_depth", {})
    target = {
        **depth.get("target", {}),
        "make": profile.make,
        "model": profile.model,
        "year": profile.year,
        "market": profile.market,
    }
    for fact in depth.get("findings", []):
        if fact["status"] != "CONFIRMED":
            continue
        if (fact["topic"], fact["subtopic"]) in {
            ("engine", "displacement"),
            ("engine", "cylinders"),
            ("engine", "fuel"),
            ("identity", "drivetrain"),
        }:
            target[fact["subtopic"]] = fact["value"]
        if (fact["topic"], fact["subtopic"]) == ("transmission", "type"):
            target["transmission"] = fact["value"]
    candidates = depth.get("epa_candidates", [])
    if len(candidates) == 1:
        epa = candidates[0]
        target["powertrain"] = (
            "PHEV"
            if epa.get("fuelType2")
            else "HYBRID"
            if "hybrid" in str(epa.get("atvType", "")).casefold()
            else "CONVENTIONAL"
        )
    if target.get("powertrain_type") not in {None, "UNKNOWN"}:
        target["powertrain"] = target["powertrain_type"]
    return target


def research_owners(profile, providers=None):
    providers = [CarComplaintsOwnerProvider()] if providers is None else providers
    target = target_for_profile(profile)
    results = []
    for provider in providers:
        try:
            results.append(provider.lookup(target))
        except Exception as error:
            results.append(
                OwnerReviewResult(
                    attempt=ProviderAttempt(
                        provider=provider.metadata,
                        state=ResearchState.ERROR,
                        query=target,
                        scope="Owner reliability",
                        reason=type(error).__name__,
                        provenance={"failure": str(error)[:180]},
                    )
                )
            )
        finally:
            if getattr(provider, "http", None):
                provider.http.close()
    materials = [m.model_dump(mode="json") for r in results for m in r.materials]
    sample = owner_sample(materials, target)
    excluded = [
        *[
            {
                "material_id": m["material_id"],
                "reason": owner_applicability(target, m),
                "applicability": m["applicability"],
            }
            for m in materials
            if owner_applicability(target, m) != "MATCH"
        ],
        *[m for r in results for m in r.excluded],
    ]
    factory_and_complaints = []
    for evidence in profile.evidence:
        material = evidence.conditions.get("material")
        if material and evidence.conditions.get("consumer_kind") == "issue_signal":
            factory_and_complaints.append(
                {
                    **material,
                    "evidence_ids": [evidence.id],
                    "source_ids": [evidence.source_id],
                }
            )
    return {
        "version": VERSION,
        "researched_at": datetime.now(UTC).isoformat(),
        "target": target,
        "sample": sample,
        "excluded": excluded,
        "attempts": [r.attempt.model_dump(mode="json") for r in results],
        "restricted_sources": [
            {**r, "checked_at": "2026-09-18", "query_completed": False}
            for r in RESTRICTED_OWNER_SOURCES
        ],
        "sources": [s.model_dump(mode="json") for r in results for s in r.sources],
        "issue_aggregation": aggregate_issues(
            [*factory_and_complaints, *sample["materials"]], target
        ),
    }


def ensure_report_evidence(check, *, owner_providers=None, history_providers=None):
    if check.is_demo or not check.profile or not check.profile.dossier_seed.get("knowledge_depth"):
        return
    history = check.full_history_payload or {}
    if history.get("history_research", {}).get("version") != VERSION:
        research_history(check, history_providers)
    owners = check.profile.dossier_seed.get("owner_reliability", {})
    fresh = False
    if owners.get("version") == VERSION and owners.get("researched_at"):
        fresh = datetime.fromisoformat(owners["researched_at"]) > datetime.now(UTC) - timedelta(
            days=1
        )
    if not fresh:
        owners = research_owners(check.profile, owner_providers)
        check.profile.dossier_seed = {**check.profile.dossier_seed, "owner_reliability": owners}
    check.full_history_payload = {**check.full_history_payload, "owner_reliability": owners}
    sources = {s["id"]: s for s in check.source_snapshot}
    sources.update({s["id"]: s for s in owners.get("sources", [])})
    check.source_snapshot = list(sources.values())
