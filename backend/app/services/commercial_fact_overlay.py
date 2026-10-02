"""Field-scoped commercial facts over an unchanged internal EPA candidate.

The EPA row is used to locate an annual candidate and detect disagreements. It
is never itself evidence for a value returned by this production projection.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from sqlalchemy import select

from app.models.knowledge_ops import CommercialFactClaim

REUSE_STATUSES = frozenset({"COMMERCIAL_OK", "INTERNAL_RESEARCH", "NEEDS_REVIEW"})
RIGHTS_BASES = frozenset({"CC0_DATASET", "US_FEDERAL_DATASET", "FACTUAL_EXTRACTION"})
FACT_RIGHTS_REFERENCES = frozenset(
    {
        "https://www.copyright.gov/help/faq/faq-protect.html",
        "https://www.copyright.gov/register/tx-databases.html",
    }
)
AZ_FACT_RIGHTS_REFERENCES = frozenset(
    {
        "https://www.wipo.int/wipolex/en/legislation/details/22657",
        "https://www.copat.gov.az/docs/Qanunvericilik/Qanunlar/English/Law-Database.pdf",
    }
)
IDENTITY_FIELDS = frozenset(
    {"make", "model", "model_year", "original_market", "generation", "generation_code"}
)
MECHANICAL_FIELDS = frozenset(
    {
        "powertrain",
        "fuel",
        "engine_displacement",
        "engine_description",
        "engine_code",
        "motor_description",
        "transmission_description",
        "transmission_family",
        "drivetrain",
        "cylinders",
        "aspiration",
    }
)
OPTIONAL_FACT_FIELDS = frozenset(
    {
        "body",
        "trim",
        "seats",
        "gears",
        "power_kw",
        "power_hp",
        "size_class",
        "ground_clearance",
        "length",
        "length_mm",
        "width",
        "width_mm",
        "height",
        "height_mm",
        "wheelbase",
        "wheelbase_mm",
        "fuel_combined",
        "fuel_grade",
        "electricity_combined",
        "motor_description",
        "cargo_l",
        "octane_aki",
        "octane_ron",
    }
)
CLAIM_FIELDS = IDENTITY_FIELDS | MECHANICAL_FIELDS | OPTIONAL_FACT_FIELDS
FACTORY_DOMAINS = {
    "audi": ("audi.com", "audiusa.com", "audi-mediacenter.com"),
    "bmw": ("bmwgroup.com", "bmwusa.com", "bmw.com"),
    "cadillac": ("cadillac.com", "gm.com"),
    "chevrolet": ("chevrolet.com", "gm.com"),
    "honda": ("honda.com", "hondainfocenter.com"),
    "hyundai": ("hyundaiusa.com", "hyundainews.com"),
    "infiniti": ("infinitiusa.com", "nissannews.com"),
    "jeep": ("jeep.com", "stellantisfleet.com", "stellantisnorthamerica.com"),
    "kia": ("kia.com", "kiamedia.com"),
    "land-rover": ("landrover.com", "landroverusa.com", "jaguarlandrover.com"),
    "lexus": ("lexus.com",),
    "mercedes": ("mbusa.com", "mercedes-benz.com", "daimler.com"),
    "mitsubishi": ("mitsubishicars.com",),
    "nissan": ("nissanusa.com", "nissannews.com"),
    "tesla": ("tesla.com",),
    "toyota": ("toyota.com",),
    "volkswagen": ("vw.com", "volkswagen.com", "vwnews.com"),
    "vw": ("vw.com", "volkswagen.com", "vwnews.com"),
}


def _host(url):
    parsed = urlparse(url or "")
    try:
        if (
            parsed.scheme != "https"
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
        ):
            return None
    except ValueError:
        return None
    return parsed.hostname


def _host_in(host, domains):
    return bool(host and any(host == domain or host.endswith("." + domain) for domain in domains))


def _scalar(value):
    return (
        value is not None
        and not isinstance(value, (dict, list, bool))
        and (not isinstance(value, str) or (bool(value.strip()) and len(value) <= 120))
    )


def _same(a, b):
    if a is None or b is None:
        return a is b
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except (InvalidOperation, TypeError, ValueError):
        return " ".join(str(a).casefold().split()) == " ".join(str(b).casefold().split())


def candidate_value(catalog, name):
    if name in IDENTITY_FIELDS:
        return catalog.get(name)
    fact = catalog.get("facts", {}).get(name) or {}
    return fact.get("value") if fact.get("status") == "CONFIRMED" else None


def _rights_ok(claim, source):
    if (
        claim.reuse_status != "COMMERCIAL_OK"
        or claim.source_id == "epa"
        or source is None
        or source.paused
        or not _scalar(claim.value)
        or claim.fact_name not in CLAIM_FIELDS
        or claim.rights_basis not in RIGHTS_BASES
        or not _host(claim.source_url)
        or not _host(claim.rights_reference)
        or not claim.locator
    ):
        return False
    try:
        date.fromisoformat(claim.rights_checked_at or "")
    except ValueError:
        return False
    if claim.rights_basis == "CC0_DATASET":
        rights = source.config or {}
        return bool(
            claim.source_id == "wikidata-structured-cc0"
            and source.id == "wikidata-structured-cc0"
            and source.state == "APPROVED"
            and rights.get("commercial_reuse") is True
            and "creativecommons.org/publicdomain/zero/1.0" in (rights.get("rights_url") or "")
            and "creativecommons.org/publicdomain/zero/1.0" in claim.rights_reference
            and _host_in(_host(claim.source_url), ("wikidata.org", "wikimedia.org"))
        )
    if claim.rights_basis == "US_FEDERAL_DATASET":
        rights = source.config or {}
        return bool(
            source.state == "APPROVED"
            and rights.get("commercial_reuse") is True
            and rights.get("dataset_url")
            and rights.get("rights_url")
            and rights.get("checked_at")
            and claim.rights_reference == rights["rights_url"]
            and claim.source_id != "epa"
        )
    # A narrow use of a factual statement does not promote its creative
    # document or registry. Mirrored brochures need an explicit human review.
    brand = claim.source_id.removeprefix("factory-").removesuffix("-us")
    official = _host_in(_host(claim.source_url), FACTORY_DOMAINS.get(brand, ()))
    scope = claim.evidence_scope or {}
    return bool(
        claim.source_id.startswith("factory-")
        and source.state in {"APPROVED", "LOCAL_RESEARCH"}
        and (source.config or {}).get("factory_identity_evidence")
        and claim.fact_name in CLAIM_FIELDS
        and claim.rights_reference in FACT_RIGHTS_REFERENCES
        and scope.get("az_rights_reference") in AZ_FACT_RIGHTS_REFERENCES
        and scope.get("extraction_scope") == "ISOLATED_FACT"
        and scope.get("source_document_kind")
        in {"BROCHURE", "SPEC_SHEET", "OWNER_MANUAL", "PRESS_KIT"}
        and scope.get("source_authenticity")
        == ("OFFICIAL_PUBLISHER" if official else "REVIEWED_MIRROR")
        and (official or (scope.get("reviewer") and scope.get("authenticity_review_note")))
    )


def claim_valid_for_candidate(claim, catalog, source):
    if not _rights_ok(claim, source):
        return False
    scope = claim.evidence_scope or {}
    if not scope.get("source_record_id"):
        return False
    for key in ("make", "model", "model_year", "original_market"):
        if not _same(scope.get(key), catalog.get(key)):
            return False
    if scope.get("original_market") != "US":
        return False
    reference_value = candidate_value(catalog, claim.fact_name)
    if claim.fact_name in {"generation", "generation_code"} and str(
        reference_value or ""
    ).casefold() in {"", "unknown", "unresolved", "unverified", "generation unverified"}:
        reference_value = claim.value
    if not _same(claim.value, reference_value):
        # EPA disagreement is a review case, never an automatic correction.
        return False
    if claim.fact_name in MECHANICAL_FIELDS:
        if scope.get("granularity") != "EXACT_CONFIGURATION":
            return False
        keys = scope.get("configuration_keys") or {}
        for name in ("engine_displacement", "transmission_description", "drivetrain"):
            if name not in keys or not _same(keys[name], candidate_value(catalog, name)):
                return False
        engine_key = next(
            (
                name
                for name in ("engine_description", "engine_code", "motor_description")
                if candidate_value(catalog, name) is not None
            ),
            None,
        )
        if engine_key is None or not _same(
            keys.get(engine_key), candidate_value(catalog, engine_key)
        ):
            return False
    elif scope.get("granularity") not in {"MODEL_YEAR", "EXACT_CONFIGURATION", "YEAR_RANGE"}:
        return False
    if scope.get("granularity") == "YEAR_RANGE":
        try:
            if (
                not int(scope["model_year_from"])
                <= catalog["model_year"]
                <= int(scope["model_year_to"])
            ):
                return False
        except (KeyError, TypeError, ValueError):
            return False
    return True


def upsert_claim(
    db,
    *,
    variant_id,
    fact_name,
    value,
    source_id,
    evidence_scope,
    reuse_status,
    source_url,
    locator,
    rights_basis=None,
    rights_reference=None,
    rights_checked_at=None,
    unit=None,
):
    """Store source assertion; runtime independently rechecks commercial eligibility."""
    if reuse_status not in REUSE_STATUSES or fact_name not in CLAIM_FIELDS:
        raise ValueError("INVALID_FACT_CLAIM")
    if not locator or not _host(source_url) or not _scalar(value):
        raise ValueError("FACT_EVIDENCE_REQUIRED")
    if not isinstance(evidence_scope, dict):
        raise ValueError("FACT_SCOPE_REQUIRED")
    if reuse_status == "COMMERCIAL_OK" and (
        rights_basis not in RIGHTS_BASES or not rights_reference or not rights_checked_at
    ):
        raise ValueError("FACT_RIGHTS_EVIDENCE_REQUIRED")
    claim = db.scalar(
        select(CommercialFactClaim).where(
            CommercialFactClaim.variant_id == variant_id,
            CommercialFactClaim.fact_name == fact_name,
            CommercialFactClaim.source_id == source_id,
            CommercialFactClaim.locator == locator,
        )
    )
    if claim is None:
        claim = CommercialFactClaim(
            variant_id=variant_id,
            fact_name=fact_name,
            source_id=source_id,
            locator=locator,
        )
        db.add(claim)
    claim.value = value
    claim.evidence_scope = evidence_scope
    claim.reuse_status = reuse_status
    claim.source_url = source_url
    claim.rights_basis = rights_basis
    claim.rights_reference = rights_reference
    claim.rights_checked_at = rights_checked_at
    claim.unit = unit
    db.flush()
    return claim


def claims_for_variants(db, variant_ids):
    if not variant_ids:
        return {}
    grouped = defaultdict(list)
    for claim in db.scalars(
        select(CommercialFactClaim).where(
            CommercialFactClaim.variant_id.in_(variant_ids),
            CommercialFactClaim.reuse_status == "COMMERCIAL_OK",
        )
    ):
        grouped[claim.variant_id].append(claim)
    return grouped


def commercial_overlay_core_ready(catalog):
    if catalog.get("commercial_fact_overlay") is not True:
        return False
    facts = catalog.get("facts") or {}

    def has(name):
        return bool(
            (fact := facts.get(name))
            and fact.get("status") == "CONFIRMED"
            and fact.get("reuse_status") == "COMMERCIAL_OK"
            and _scalar(fact.get("value"))
            and str(fact["value"]).strip().upper() not in {"UNKNOWN", "UNRESOLVED"}
        )

    if not all(catalog.get(k) for k in ("make", "model", "model_year")):
        return False
    if (
        catalog.get("original_market") != "US"
        or not isinstance(catalog["model_year"], int)
        or isinstance(catalog["model_year"], bool)
        or catalog["model_year"] < 2000
    ):
        return False
    if not all(has(k) for k in ("powertrain", "transmission_description", "drivetrain")):
        return False
    powertrain = facts["powertrain"]["value"]
    if powertrain not in {"ICE", "HEV", "PHEV", "MHEV", "EREV", "BEV", "FCEV"}:
        return False
    if facts["drivetrain"]["value"] not in {"FWD", "RWD", "AWD", "4WD", "PART_TIME_4WD"}:
        return False
    if powertrain in {"BEV", "FCEV"}:
        return has("motor_description") or has("engine_description")
    try:
        displacement = Decimal(str(facts["engine_displacement"]["value"]))
    except (KeyError, InvalidOperation, TypeError, ValueError):
        return False
    return displacement.is_finite() and displacement > 0 and (
        has("fuel")
        and has("engine_displacement")
        and (has("engine_description") or has("engine_code"))
    )


def project_commercial_catalog(catalog, claims, sources):
    """Build a consumer-safe catalogue solely from independently cleared claims."""
    accepted = defaultdict(list)
    for claim in claims:
        if claim_valid_for_candidate(claim, catalog, sources.get(claim.source_id)):
            accepted[claim.fact_name].append(claim)
    chosen = {}
    for name, options in accepted.items():
        # Two accepted sources that disagree require review; never pick one.
        if any(not _same(options[0].value, item.value) for item in options[1:]):
            continue
        chosen[name] = sorted(options, key=lambda item: (item.source_id, item.locator))[0]
    if not all(key in chosen for key in ("make", "model", "model_year", "original_market")):
        return None
    facts = {
        name: {
            "value": claim.value,
            "unit": claim.unit,
            "status": "CONFIRMED",
            "reuse_status": "COMMERCIAL_OK",
            "source_id": claim.source_id,
            "evidence_id": claim.id,
            "source_url": claim.source_url,
        }
        for name, claim in chosen.items()
        if name not in IDENTITY_FIELDS
    }
    fingerprint_input = [
        {
            "id": item.id,
            "value": item.value,
            "source_id": item.source_id,
            "scope": item.evidence_scope,
            "status": item.reuse_status,
            "source_url": item.source_url,
            "rights_reference": item.rights_reference,
            "rights_checked_at": item.rights_checked_at,
        }
        for item in sorted(chosen.values(), key=lambda item: (item.fact_name, item.id))
    ]
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_input, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:24]
    primary = chosen["make"]
    projected = {
        "make": chosen["make"].value,
        "model": chosen["model"].value,
        "model_year": chosen["model_year"].value,
        "original_market": chosen["original_market"].value,
        "generation": chosen["generation"].value if "generation" in chosen else None,
        "generation_code": chosen["generation_code"].value if "generation_code" in chosen else None,
        "configuration": "",  # Never copy the research candidate's editorial label.
        "facts": facts,
        "source_registry_id": "commercial-fact-overlay",
        "source_url": primary.source_url,
        "source_date": None,
        "revision_id": "overlay-" + fingerprint,
        "publication_scope": "COMMERCIAL",
        "published_at": max(item.updated_at.isoformat() for item in chosen.values()),
        "commercial_fact_overlay": True,
        "documentary_sections": [],
    }
    if not commercial_overlay_core_ready(projected):
        return None
    # Construct a compact label from cleared facts only.
    mechanics = [
        facts[k]["value"]
        for k in (
            "engine_description",
            "engine_code",
            "engine_displacement",
            "transmission_description",
            "drivetrain",
        )
        if k in facts
    ]
    projected["configuration"] = " · ".join(str(value) for value in mechanics)
    return projected


def project_existing_commercial_catalog(catalog, sources):
    """Preserve licensed legacy rows while filtering their mixed-source fields.

    Legacy records predate the claims table. Their registry's documented
    dataset licence is the fallback reuse decision for its own facts only; a
    research-only documentary reference is removed field by field.
    """
    primary = sources.get(catalog.get("source_registry_id"))
    if not _source_has_dataset_rights(primary):
        return None
    c = copy.deepcopy(catalog)
    facts = {}
    for name, fact in (c.get("facts") or {}).items():
        ref = fact.get("documentary_source") or {}
        source_id = ref.get("registry_id") or c["source_registry_id"]
        if not _source_has_dataset_rights(sources.get(source_id)):
            continue
        facts[name] = {**fact, "reuse_status": "COMMERCIAL_OK"}
    c["facts"] = facts

    def references_safe(references):
        return all(
            _source_has_dataset_rights(sources.get(ref.get("registry_id"))) for ref in references
        )

    c["documentary_sections"] = [
        section
        for section in c.get("documentary_sections", [])
        if references_safe(section.get("references") or [])
    ]
    verification = c.get("identity_verification") or {}
    if not all(
        references_safe(refs) for refs in (verification.get("field_evidence") or {}).values()
    ):
        c["identity_verification"] = None
        c["verification_gate"] = None
        c["generation"] = None
        c["generation_code"] = None
    c["configuration"] = " · ".join(
        str(facts[name]["value"])
        for name in (
            "engine_description",
            "engine_displacement",
            "transmission_description",
            "drivetrain",
        )
        if name in facts and facts[name].get("status") == "CONFIRMED"
    )
    return c


def _source_has_dataset_rights(source):
    rights = (source.config or {}) if source else {}
    return bool(
        source
        and source.state == "APPROVED"
        and not source.paused
        and rights.get("commercial_reuse") is True
        and rights.get("rights_url")
        and rights.get("checked_at")
    )
