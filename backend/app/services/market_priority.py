"""AZ listing prevalence schedules research, never verifies vehicle identity."""

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.services.catalog_scope import in_active_scope, minimum_year
from app.services.knowledge_import import normalized

POLICY_PATH = Path(__file__).resolve().parents[3] / "data/manifests/az-market-priority-policy.json"


def policy():
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def normalize_market_claim(raw, sales_channel=None):
    """Country of assembly must not be passed here: this accepts the seller's market field only."""
    key = normalized(raw or "")
    channel = "OFFICIAL_DEALER" if normalized(sales_channel or "") == "resmi diler" else "UNKNOWN"
    if key == "resmi diler":
        return {"market": "UNKNOWN", "region": "UNKNOWN", "channel": "OFFICIAL_DEALER"}
    values = {
        "amerika": ("US", "US"),
        "abs": ("US", "US"),
        "usa": ("US", "US"),
        "koreya": ("KR", "KR"),
        "cin": ("CN", "CN"),
        "avropa": ("EU", "EU"),
        "almaniya": ("DE", "EU"),
        "fransa": ("FR", "EU"),
        "italiya": ("IT", "EU"),
        "cexiya": ("CZ", "EU"),
        "boyuk britaniya": ("UK", "EU"),
        "yaponiya": ("JP", "OTHER"),
        "kanada": ("CA", "OTHER"),
        "diger": ("OTHER", "OTHER"),
        "namelum": ("UNKNOWN", "UNKNOWN"),
        "": ("UNKNOWN", "UNKNOWN"),
    }
    market, region = values.get(key, ("OTHER", "OTHER"))
    return {"market": market, "region": region, "channel": channel}


def distribution(record):
    markets, regions, channels, raw_counts = Counter(), Counter(), Counter(), Counter()
    years = defaultdict(set)
    if record.get("market_counts"):
        values = [(r["market_raw"], None, r["count"], None) for r in record["market_counts"]]
    else:
        unique = {r["listing_id"]: r for r in record.get("listings", [])}
        values = [
            (r.get("market_raw"), r.get("sales_channel_raw"), 1, r.get("model_year"))
            for r in unique.values()
            if r["active"] and not r.get("order_only")
        ]
    for raw, sales, count, year in values:
        claim = normalize_market_claim(raw, sales)
        markets[claim["market"]] += count
        regions[claim["region"]] += count
        channels[claim["channel"]] += count
        raw_counts[raw or "(missing)"] += count
        if year is not None and count:
            years[claim["market"]].add(year)
    return {
        "markets": dict(markets),
        "regions": dict(regions),
        "sales_channels": dict(channels),
        "raw_market_field_counts": dict(raw_counts),
        "observed_local_listings": sum(markets.values()),
        "observed_model_years": {m: sorted(y) for m, y in years.items()},
        "scope": record["distribution_scope"],
        "channel_counts_overlap_market_counts": True,
    }


def canonical(make, model, rules):
    make = next(
        (v for k, v in rules["make_aliases"].items() if normalized(k) == normalized(make)), make
    )
    make = next((v for v in rules["primary_makes"] if normalized(v) == normalized(make)), make)
    for alias in rules.get("reviewed_model_aliases", []):
        if normalized(alias["make"]) == normalized(make) and normalized(
            alias["from"]
        ) == normalized(model):
            model = alias["to"]
    return make, model


def build_queue(observations, catalogue, rules, *, us_sources_available, now=None):
    now = now or datetime.now(UTC)
    technical = defaultdict(list)
    for c in catalogue:
        make, model = canonical(c["make"], c["model"], rules)
        technical[(normalized(make), normalized(model))].append(c)
    latest = {}
    conflicts = []
    for r in observations:
        make, model = canonical(r["make"], r["model"], rules)
        key = (normalized(make), normalized(model))
        if key in latest and r["observed_at"] == latest[key]["observed_at"]:
            conflicts.append({"make": make, "model": model, "code": "CONCURRENT_MARKET_SNAPSHOTS"})
        if key not in latest or r["observed_at"] > latest[key]["observed_at"]:
            latest[key] = r
    rows, queues = [], {k: [] for k in rules["queue_order"]}
    for key, r in latest.items():
        make, model = canonical(r["make"], r["model"], rules)
        d = distribution(r)
        elapsed = now - datetime.fromisoformat(r["observed_at"].replace("Z", "+00:00"))
        fresh = 0 <= elapsed.total_seconds() <= rules["freshness_days"] * 86400
        catalog = technical.get(key, [])
        coverage = dict(Counter(c["original_market"] for c in catalog))
        us_count = d["markets"].get("US", 0)
        observed = d["observed_local_listings"]
        # Do not multiply a partial sample share by the entire model's listing count.
        prevalence = r["listing_count"] if d["scope"] == "COMPLETE" else observed
        relevance = Decimal(us_count) / Decimal(prevalence) if prevalence else Decimal(0)
        availability = Decimal(1 if us_sources_available else 0)
        score = Decimal(prevalence or 0) * availability * relevance
        conflict = any(
            normalized(c["make"]) == key[0] and normalized(c["model"]) == key[1] for c in conflicts
        )
        row = {
            "make": make,
            "model": model,
            "source_make": r["make"],
            "source_model": r["model"],
            "listing_count": r["listing_count"],
            "count_method": r["count_method"],
            "inventory_scope": r["inventory_scope"],
            "observed_at": r["observed_at"],
            "source_url": r["source_url"],
            "locator": r["locator"],
            "market_distribution": d,
            "us_variant_present": "SELLER_CLAIM"
            if us_count
            else "NOT_OBSERVED_IN_COMPLETE_SNAPSHOT"
            if d["scope"] == "COMPLETE"
            else "UNKNOWN",
            "us_listing_count_or_sample_lower_bound": us_count
            if d["scope"] != "NOT_OBSERVED"
            else None,
            "verification_status": "DISCOVERY_CONFLICT"
            if conflict
            else "SELLER_CLAIM_NOT_TECHNICALLY_VERIFIED",
            "technical_source_coverage": {
                "source_rows_by_market": coverage,
                "exact_model_name_match_only": True,
                "full_market_variants": 0,
                "free_us_adapter_available": us_sources_available,
            },
            "dossier_status": "BASIC_FACTS_PARTIAL" if catalog else "NOT_RESEARCHED",
            "priority": {
                "local_prevalence": prevalence,
                "basis": d["scope"],
                "source_availability": str(availability),
                "market_relevance": str(relevance),
                "score": str(score.quantize(Decimal("0.0001"))),
            },
            "fresh": fresh,
            "batch_status": "WAITING_LOCAL_OR_MARKET_EVIDENCE",
            "revision_id": r.get("revision_id"),
            "source_id": r.get("source_id"),
        }
        local_present = r["inventory_scope"] == "ACTIVE_LOCAL" and (r["listing_count"] or observed)
        primary = make in rules["primary_makes"]
        if fresh and local_present and not conflict:
            if us_count > 0:
                name = "PRIMARY_US_MARKET_QUEUE" if primary else "SECONDARY_US_MARKET_QUEUE"
                row["batch_status"] = (
                    "READY_FOR_US_DISCOVERY" if us_sources_available else "SOURCE_UNAVAILABLE"
                )
                if name in queues:
                    queues[name].append({**row, "target_markets": ["US"]})
            if (
                primary
                and "PRIMARY_OTHER_MARKET_QUEUE" in queues
                and (not us_count or observed > us_count)
            ):
                other = [m for m, count in d["markets"].items() if m != "US" and count]
                queues["PRIMARY_OTHER_MARKET_QUEUE"].append(
                    {
                        **row,
                        "target_markets": other,
                        "batch_status": "OTHER_MARKET_RESEARCH"
                        if other and other != ["UNKNOWN"]
                        else "WAITING_MARKET_VERIFICATION",
                    }
                )
        elif not fresh:
            row["batch_status"] = "STALE_DISCOVERY_REFRESH_REQUIRED"
        rows.append(row)
    owner_basis = (
        rules.get("primary_basis") == "OWNER_PRIORITY_WITH_OFFICIAL_US_SOURCE_CONFIGURATIONS"
    )
    if owner_basis:
        add_owner_priorities(rows, queues, technical, rules, us_sources_available)
    for members in queues.values():
        members.sort(
            key=lambda r: (
                r.get("editorial_round", -1),
                r.get("owner_make_rank", -1),
                -Decimal(r["priority"]["score"] or "0"),
                -(r["listing_count"] or r["market_distribution"]["observed_local_listings"]),
                r["make"],
                r["model"],
            )
        )
        for index, row in enumerate(members, 1):
            row["queue_rank"] = index
    brands = []
    for make in rules["primary_makes"]:
        members = [r for r in rows if r["make"] == make]
        brands.append(
            {
                "make": make,
                "observed_models": sum(r.get("source_id") is not None for r in members),
                "technical_candidate_models": len(members),
                "model_inventory_status": "OPTIONAL_MANUAL_INPUT_NOT_COLLECTED"
                if owner_basis
                else "OBSERVED_SUBSET_COMPLETENESS_NOT_ESTABLISHED"
                if members
                else "AWAITING_PERMITTED_EXPORT",
                "listing_count": None,
                "market_distribution": None,
                "us_variant_present": "SELLER_CLAIM"
                if any(r["us_variant_present"] == "SELLER_CLAIM" for r in members)
                else "OFFICIAL_US_SOURCE_CONFIGURATION"
                if any(
                    r["us_variant_present"] == "OFFICIAL_US_SOURCE_CONFIGURATION" for r in members
                )
                else "UNKNOWN",
                "status": "OWNER_PRIORITY_ACTIVE"
                if owner_basis
                else "PARTIAL"
                if members
                else "NO_OBSERVATIONS",
            }
        )
    return {
        "policy_version": rules["version"],
        "generated_at": now.isoformat(),
        "brands": brands,
        "models": rows,
        **queues,
        "conflicts": conflicts,
        "uniform_catalog_expansion": "DISABLED",
        "paid_calls": 0,
        "discovery_records": len(observations),
        "overall": "PARTIAL" if rows else "NO_PRIORITY_EVIDENCE",
    }


def add_owner_priorities(rows, queues, technical, rules, us_available):
    """Owner brand instruction is enough to begin; no invented Turbo observations."""
    existing = {
        (normalized(r["make"]), normalized(r["model"])) for r in queues["PRIMARY_US_MARKET_QUEUE"]
    }
    for rank, make in enumerate(rules["primary_makes"]):
        model_order = rules.get("first_wave_model_order", {}).get(make, [])
        families = {key: values for key, values in technical.items() if key[0] == normalized(make)}
        for key, values in families.items():
            us = [
                c
                for c in values
                if in_active_scope(c["make"], c["original_market"], c["model_year"], rules)
            ]
            if not us or key in existing:
                continue
            model = us[0]["model"]
            if rules.get("active_layer", "").startswith("US_BASE_CATALOG") and normalized(
                model
            ) not in {normalized(m) for m in model_order}:
                continue
            row = {
                "make": make,
                "model": model,
                "source_make": make,
                "source_model": model,
                "listing_count": None,
                "count_method": "NOT_COLLECTED",
                "inventory_scope": "NOT_COLLECTED",
                "observed_at": None,
                "source_url": None,
                "locator": "Owner priority instruction",
                "market_distribution": {
                    "scope": "NOT_OBSERVED",
                    "markets": {},
                    "sales_channels": {},
                    "observed_local_listings": 0,
                    "observed_model_years": {},
                },
                "us_variant_present": "OFFICIAL_US_SOURCE_CONFIGURATION",
                "us_listing_count_or_sample_lower_bound": None,
                "verification_status": "SOURCE_CONFIGURATIONS_NOT_FULL_FACTORY_IDENTITY",
                "technical_source_coverage": {
                    "source_rows_by_market": dict(Counter(c["original_market"] for c in values)),
                    "source_ids": sorted({c.get("source_registry_id", "epa") for c in us}),
                    "source_urls": sorted({c["source_url"] for c in us}),
                    "free_us_adapter_available": us_available,
                    "full_market_variants": 0,
                },
                "dossier_status": "BASIC_FACTS_PARTIAL",
                "priority": {
                    "local_prevalence": None,
                    "market_relevance": "OWNER_SELECTED_MAKE",
                    "source_availability": str(int(us_available)),
                    "score": None,
                    "basis": "OWNER_BRANDS_EDITORIAL_MODEL_ORDER_NO_MEASURED_POPULARITY",
                },
                "owner_make_rank": rank,
                "editorial_round": model_order.index(model)
                if model in model_order
                else len(model_order) + 1,
                "batch_status": "READY_FOR_US_DISCOVERY" if us_available else "SOURCE_UNAVAILABLE",
                "research_model_years": sorted({c["model_year"] for c in us}),
                "research_year_basis": "PUBLISHED_OFFICIAL_US_DATA_NOT_TURBO",
                "target_markets": ["US"],
                "revision_id": None,
                "source_id": None,
            }
            rows.append(row)
            queues["PRIMARY_US_MARKET_QUEUE"].append(row)
        if "PRIMARY_OTHER_MARKET_QUEUE" in queues and not any(
            r["make"] == make for r in queues["PRIMARY_US_MARKET_QUEUE"]
        ):
            for model in model_order:
                row = {
                    "make": make,
                    "model": model,
                    "listing_count": None,
                    "market_distribution": {"scope": "NOT_OBSERVED", "observed_local_listings": 0},
                    "us_variant_present": "NOT_ESTABLISHED",
                    "verification_status": "MARKET_SPECIFIC_DOCUMENT_REQUIRED",
                    "dossier_status": "NOT_RESEARCHED",
                    "technical_source_coverage": {"source_rows_by_market": {}},
                    "priority": {"score": None, "basis": "OWNER_BRAND_DRAFT_MODEL_CANDIDATE"},
                    "target_markets": [],
                    "batch_status": "NON_US_FACTORY_DISCOVERY_REQUIRED",
                    "editorial_round": model_order.index(model),
                    "owner_make_rank": rank,
                }
                rows.append(row)
                queues["PRIMARY_OTHER_MARKET_QUEUE"].append(row)


def verification_batch(rules=None, manifest=None, cohort=None):
    """Owner-scoped execution queue. Source convenience cannot outrank local relevance."""
    rules = rules or policy()
    root = POLICY_PATH.parents[2]
    if manifest is None:
        path = (root / rules["active_verification_manifest"]).resolve()
        if not path.is_relative_to((root / "data/manifests").resolve()):
            raise ValueError("VERIFICATION_MANIFEST_OUTSIDE_DATA")
        manifest = json.loads(path.read_text(encoding="utf-8"))
    if cohort is None:
        cohort = json.loads((root / rules["verification_cohort"]).read_text(encoding="utf-8"))
    allowed = {(normalized(r["make"]), normalized(r["model"])) for r in cohort["cohort"]}
    members = manifest["families"]
    ids = set()
    for r in members:
        if r["id"] in ids:
            raise ValueError("DUPLICATE_VERIFICATION_SCOPE")
        ids.add(r["id"])
        if (
            r["make"] not in rules["primary_makes"]
            or (normalized(r["make"]), normalized(r["model"])) not in allowed
        ):
            raise ValueError("OUTSIDE_FROZEN_OWNER_COHORT")
        if r["market"] != "US" or r["make"] == "Skoda":
            raise ValueError("NON_US_REQUIRES_SEPARATE_MANIFEST")
        if r["requested_model_year_from"] > r["requested_model_year_to"]:
            raise ValueError("REVERSED_VERIFICATION_RANGE")
        if not r.get("target_configuration") or not r.get("exclude"):
            raise ValueError("EXPLICIT_CONFIGURATION_SCOPE_REQUIRED")
    ordered = sorted(
        enumerate(members),
        key=lambda pair: (
            pair[1]["local_relevance_tier"],
            pair[1]["owner_make_priority"],
            pair[1].get("local_generation_year_priority", 1),
            -pair[1].get("source_availability_rank", 0),
            pair[0],
        ),
    )
    return {
        "batch_id": manifest["batch_id"],
        "selection_status": manifest["selection_status"],
        "priority_order": manifest["priority_order"],
        "families": [{**r, "queue_rank": i} for i, (_, r) in enumerate(ordered, 1)],
        "bmw_330i_my2025_role": "PIPELINE_PROOF_ONLY",
        "turbo_counts_required": False,
    }


def base_catalog_batch(rules=None, manifest=None):
    rules = rules or policy()
    root = POLICY_PATH.parents[2]
    if manifest is None:
        path = (root / rules["active_catalog_manifest"]).resolve()
        if not path.is_relative_to((root / "data/manifests").resolve()):
            raise ValueError("CATALOG_MANIFEST_OUTSIDE_DATA")
        manifest = json.loads(path.read_text(encoding="utf-8"))
    ids = set()
    for family in manifest["families"]:
        if family["id"] in ids or family["make"] not in rules["primary_makes"]:
            raise ValueError("OUTSIDE_OWNER_CATALOG_SCOPE")
        ids.add(family["id"])
        if rules.get("allowed_markets") and family["market"] not in rules["allowed_markets"]:
            raise ValueError("OUTSIDE_ACTIVE_CATALOG_MARKETS")
        if family["year_from"] < minimum_year(family["make"], rules):
            raise ValueError("OUTSIDE_ACTIVE_CATALOG_YEARS")
        if any(
            g["year_from"] < minimum_year(family["make"], rules)
            or g["year_from"] < family["year_from"]
            or g["year_to"] > family["year_to"]
            for g in family.get("groups", [])
        ):
            raise ValueError("GROUP_OUTSIDE_ACTIVE_CATALOG_YEARS")
        if family["make"] == "Skoda" and family["market"] == "US":
            raise ValueError("SKODA_REQUIRES_NON_US_SOURCES")
        if not family.get("groups") or not family.get("exclude"):
            raise ValueError("EXPLICIT_CATALOG_COMBINATIONS_REQUIRED")
    order = {m: i for i, m in enumerate(["US", "KR", "EU", "JP", "CN"])}
    members = sorted(
        manifest["families"],
        key=lambda f: (
            f["local_relevance_tier"],
            rules["primary_makes"].index(f["make"]),
            f.get("local_generation_year_priority", 1),
            order.get(f["market"], 5),
            -f.get("source_availability_rank", 0),
            f["id"],
        ),
    )
    return {
        "batch_id": manifest["batch_id"],
        "families": members,
        "selection_status": manifest["selection_status"],
        "turbo_counts_required": False,
        "readiness_gates": rules["basic_catalog_done_requires"],
        "deferred_workstreams": rules["deferred_workstreams"],
    }


def current_queue(db):
    from app.models.knowledge_ops import SourceRegistry
    from app.services.catalog_buyer import records
    from app.services.market_discovery import published

    source = db.get(SourceRegistry, "nhtsa")
    available = bool(
        source
        and not source.paused
        and source.state in {"APPROVED", "LOCAL_RESEARCH", "EXISTING_ADAPTER"}
    )
    result = build_queue(
        published(db), [c for _, c in records(db)], policy(), us_sources_available=available
    )
    if policy().get("work_mode") == "VERIFY_LOCAL_USABLE_FAMILIES":
        result["verification_batch"] = verification_batch()
        result["execution_mode"] = "VERIFY_LOCAL_USABLE_FAMILIES"
        # Discovery lists remain available as historical context, never as this stage's work order.
        for key in policy()["queue_order"]:
            for member in result[key]:
                member["batch_status"] = "RESEARCH_EXPANSION_FROZEN_USE_VERIFICATION_BATCH"
    if policy().get("work_mode") == "BUILD_BASE_CATALOG":
        result["catalog_batch"] = base_catalog_batch()
        result["execution_mode"] = "BUILD_BASE_CATALOG"
        for key in policy()["queue_order"]:
            for member in result[key]:
                member["batch_status"] = "USE_REVIEWED_BASE_CATALOG_MANIFEST"
    return result
