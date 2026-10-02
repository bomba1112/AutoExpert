"""Fail-closed verification: source-backed scope, review, immutable document hashes."""

from app.core.config import get_settings
from app.models.knowledge_ops import RawDocument
from app.services.knowledge_registry import require_source

IDENTITY_FIELDS = {
    "generation",
    "market",
    "model_year",
    "engine_description",
    "transmission_description",
    "drivetrain",
    "applicability",
}
FULL_SECTIONS = {
    "conclusion",
    "engine",
    "transmission",
    "fuel",
    "body",
    "chassis",
    "safety",
    "electrical",
    "service",
    "market",
    "owners",
    "recalls",
    "communications",
    "known_issues",
    "applicability",
}


def reference_years(ref):
    return (
        {ref.model_year}
        if ref.model_year is not None
        else set(range(ref.model_year_from, ref.model_year_to + 1))
    )


def _document_checksum(path, cache):
    """Reuse identical bytes only within one validation, with a file-change guard."""
    from app.services.knowledge_import import checksum

    def signature():
        stat = path.stat()
        return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns

    before = signature()
    key = (path, before)
    if key not in cache:
        digest = checksum(path.read_bytes())
        if signature() != before:
            raise ValueError("VERIFICATION_DOCUMENT_MISMATCH")
        cache[key] = digest
    return cache[key]


def check_reference(
    db, ref, record, *, identity=False, field=None, target_year=None, _document_hashes=None
):
    from app.services.knowledge_import import normalized, private_path

    source = require_source(db, ref.registry_id)
    doc = db.get(RawDocument, ref.document_id)
    if (
        not doc
        or doc.source_id != ref.registry_id
        or doc.sha256 != ref.sha256
        or doc.locator != ref.url
        or _document_checksum(
            private_path(doc.storage_key),
            _document_hashes if _document_hashes is not None else {},
        )
        != ref.sha256
    ):
        raise ValueError("VERIFICATION_DOCUMENT_MISMATCH")
    if (
        normalized(ref.make) != normalized(record.make)
        or normalized(ref.model) != normalized(record.model)
        or ref.market != record.original_market
        or (record.model_year if target_year is None else target_year) not in reference_years(ref)
    ):
        raise ValueError("VERIFICATION_APPLICABILITY_MISMATCH")
    if (
        identity
        and not source.config.get("factory_identity_evidence")
        and field not in source.config.get("identity_evidence_fields", [])
    ):
        raise ValueError("FACTORY_IDENTITY_SOURCE_REQUIRED")
    return source


def validate_publication(db, record, previous):
    """Called inside the ordinary atomic publication; a supplied status flag is never trusted."""
    # A new cache per record: never reuse validation across records, jobs or transactions.
    document_hashes = {}
    refs = [f.documentary_source for f in record.facts.values() if f.documentary_source]
    refs += [r for s in record.documentary_sections for r in s.references]
    for ref in refs:
        check_reference(db, ref, record, _document_hashes=document_hashes)
    if len({s.key for s in record.documentary_sections}) != len(record.documentary_sections):
        raise ValueError("DUPLICATE_DOSSIER_SECTION")
    v = record.identity_verification
    if not v:
        return None
    if not previous or previous.published_revision_id != v.previous_revision_id:
        raise ValueError("VERIFICATION_BASE_REVISION_CHANGED")
    if v.unresolved_conflicts:
        raise ValueError("UNRESOLVED_IDENTITY_CONFLICT")
    if not record.generation or IDENTITY_FIELDS - v.field_evidence.keys():
        raise ValueError("IDENTITY_EVIDENCE_INCOMPLETE")
    required_years = {record.model_year}
    if v.range_scope:
        required_years = set(range(v.range_scope.model_year_from, v.range_scope.model_year_to + 1))
        if record.model_year not in required_years:
            raise ValueError("RECORD_OUTSIDE_IDENTITY_RANGE")
    for key in IDENTITY_FIELDS:
        if not v.field_evidence[key]:
            raise ValueError("IDENTITY_EVIDENCE_INCOMPLETE")
        covered_years = set()
        for ref in v.field_evidence[key]:
            overlap = reference_years(ref) & required_years
            if not overlap:
                raise ValueError("IDENTITY_REFERENCE_OUTSIDE_RANGE")
            check_reference(
                db,
                ref,
                record,
                identity=True,
                field=key,
                target_year=min(overlap),
                _document_hashes=document_hashes,
            )
            covered_years |= overlap
        if covered_years != required_years:
            raise ValueError("IDENTITY_RANGE_EVIDENCE_GAP")
    for key in ("engine_description", "transmission_description", "drivetrain"):
        fact = record.facts.get(key)
        if not fact or fact.status != "CONFIRMED" or not fact.documentary_source:
            raise ValueError("CONFIRMED_FACTORY_AGGREGATES_REQUIRED")
    family = record.facts.get("transmission_family")
    if not family or family.value in {"AUTOMATIC_UNSPECIFIED", "VARIABLE_UNSPECIFIED", "UNKNOWN"}:
        raise ValueError("TRANSMISSION_CONSTRUCTION_UNRESOLVED")
    return {"state": "VERIFIED_SCOPED", "rule_version": "factory-identity-range-2"}


def range_verified(c):
    return identity_verified(c) and bool((c.get("identity_verification") or {}).get("range_scope"))


def base_catalog_ready(c):
    """Legacy strict factory-backed readiness for the VERIFIED_SCOPED scope."""
    if not identity_verified(c) or not c.get("original_market") or not c.get("model_year"):
        return False
    for key in (
        "body",
        "powertrain",
        "fuel",
        "engine_description",
        "transmission_description",
        "transmission_family",
        "drivetrain",
    ):
        fact = c.get("facts", {}).get(key, {})
        if fact.get("status") != "CONFIRMED" or fact.get("value") in (None, "", "UNKNOWN"):
            return False
        if not fact.get("documentary_source"):
            return False
    # Electric and fuel-cell vehicles have no combustion displacement. Their
    # documented motor/engine description remains mandatory above.
    if c["facts"]["powertrain"]["value"] not in {"BEV", "FCEV"}:
        displacement = c["facts"].get("engine_displacement", {})
        if (
            displacement.get("status") != "CONFIRMED"
            or displacement.get("value") in (None, "", "UNKNOWN")
            or not displacement.get("documentary_source")
        ):
            return False
    return c["facts"]["transmission_family"]["value"] in {
        "AT",
        "CVT",
        "DCT",
        "MANUAL",
        "ECVT",
        "SINGLE_SPEED",
    }


def source_confirmed_core_ready(c):
    """Readiness for the US source-backed base catalogue, not factory verification.

    EPA describes an annual vehicle/powertrain configuration, but does not
    necessarily establish its generation, body, trim or gearbox construction.
    Those optional claims must remain absent rather than becoming admission
    requirements or inferred factory facts. Publication and source-rights checks
    are performed separately by the importer and buyer query.
    """
    if (
        not c.get("make")
        or not c.get("model")
        or c.get("original_market") != "US"
        or not isinstance(c.get("model_year"), int)
        or isinstance(c.get("model_year"), bool)
        or c["model_year"] < 2000
    ):
        return False

    # A previously verified factory row is also eligible for the base scope;
    # its strict verification gate and fingerprint remain unchanged.
    if base_catalog_ready(c):
        return True

    from urllib.parse import urlparse

    # The first structured CORE publisher consumes official EPA vehicle rows.
    # Restricting the non-factory path prevents an AI/research draft with merely
    # plausible-looking locators from becoming a consumer configuration.
    url = urlparse(c.get("source_url") or "")
    if (
        c.get("source_registry_id") != "epa"
        or url.scheme != "https"
        or url.hostname not in {"fueleconomy.gov", "www.fueleconomy.gov"}
    ):
        return False

    facts = c.get("facts") or {}

    def confirmed_from_source(key):
        fact = facts.get(key) or {}
        value = fact.get("value")
        return bool(
            fact.get("status") == "CONFIRMED"
            and value is not None
            and not isinstance(value, bool)
            and str(value).strip()
            and str(value).strip().upper() != "UNKNOWN"
            and fact.get("locator")
            and (not c.get("revision_id") or fact.get("source_id"))
        )

    for key in ("powertrain", "transmission_description", "drivetrain"):
        if not confirmed_from_source(key):
            return False
    # EPA's "4-Wheel or All-Wheel Drive" does not identify either exact drive.
    # Keep those rows in the insufficient-evidence queue instead of claiming a
    # definite AWD/4WD configuration or matching an exact drive filter.
    if facts["drivetrain"]["value"] not in {
        "FWD", "RWD", "AWD", "4WD", "PART_TIME_4WD",
    }:
        return False
    powertrain = facts["powertrain"]["value"]
    if powertrain not in {"BEV", "FCEV"}:
        if not confirmed_from_source("fuel") or not confirmed_from_source("engine_displacement"):
            return False
        try:
            from decimal import Decimal

            displacement = Decimal(str(facts["engine_displacement"]["value"]))
            if not displacement.is_finite() or displacement <= 0:
                return False
        except (ArithmeticError, TypeError, ValueError):
            return False

    # Transmission family is not a CORE prerequisite. Where a family is
    # present, even the broad EPA-derived types remain eligible; exact AT/CVT/
    # DCT matching is resolved by the buyer filter, never by this admission.
    family = facts.get("transmission_family") or {}
    return not family or family.get("value") in {
        "AT",
        "CVT",
        "DCT",
        "MANUAL",
        "ECVT",
        "SINGLE_SPEED",
        "AMT",
        "AUTOMATIC_UNSPECIFIED",
        "VARIABLE_UNSPECIFIED",
        "AMT_UNSPECIFIED",
    }


def catalog_excluded(c):
    fact = c.get("facts", {}).get("catalog_applicability", {})
    return (
        fact.get("status") == "CONFIRMED"
        and fact.get("value") == "EXCLUDED"
        and bool(fact.get("documentary_source"))
    )


def us_catalog_ready(c):
    """Strict US factory-scoped readiness, without an optional seating gate."""
    return bool(
        base_catalog_ready(c)
        and c.get("original_market") == "US"
        and c.get("model_year", 0) >= 2000
    )


def us_catalog_with_confirmed_seating(c):
    """Separate coverage measure retained for seating-filter and cohort audits."""
    seats = c.get("facts", {}).get("seats", {})
    return bool(
        us_catalog_ready(c)
        and seats.get("status") == "CONFIRMED"
        and isinstance(seats.get("value"), (int, float))
        and not isinstance(seats.get("value"), bool)
        and 1 <= seats["value"] <= 30
        and seats.get("documentary_source")
    )


def base_catalog_counts(rows, *, require_us_seating=False):
    """Counts use confirmed scope, not raw catalogue rows or future product coverage."""
    check = us_catalog_with_confirmed_seating if require_us_seating else base_catalog_ready
    ready = [c for _, c in rows if check(c) and not catalog_excluded(c)]

    def scope(c):
        return c["make"], c["model"], c.get("generation_code") or c["generation"]

    def engine(c):
        return (*scope(c), c["original_market"], c["facts"]["engine_description"]["value"])

    def trans(c):
        return (*scope(c), c["original_market"], c["facts"]["transmission_description"]["value"])

    return {
        "makes": len({c["make"] for c in ready}),
        "models": len({(c["make"], c["model"]) for c in ready}),
        "generations": len({scope(c) for c in ready}),
        "market_variants": len({(*scope(c), c["original_market"]) for c in ready}),
        "engine_variants": len({engine(c) for c in ready}),
        "transmission_variants": len({trans(c) for c in ready}),
        "engine_transmission_combinations": len({(*engine(c), trans(c)[-1]) for c in ready}),
        "drivetrain_combinations": len(
            {
                (
                    *engine(c),
                    trans(c)[-1],
                    c["facts"]["drivetrain"]["value"],
                    c["facts"]["body"]["value"],
                )
                for c in ready
            }
        ),
        "model_year_configurations": len(ready),
        "models_with_ready_scope": len({(c["make"], c["model"]) for c in ready}),
        "scope_note": (
            "Confirmed published subsets only; not every engine, year or market of a model. "
            "Counts deduplicate annual rows and trim/fuel-economy groups."
        ),
    }


def fingerprint(c):
    from app.services.knowledge_import import checksum

    return checksum(
        {
            "scope": {
                k: c.get(k)
                for k in (
                    "make",
                    "model",
                    "model_year",
                    "original_market",
                    "configuration",
                    "generation",
                    "generation_code",
                    "facelift",
                )
            },
            "facts": {
                k: {f: v.get(f) for f in ("value", "status", "documentary_source")}
                for k, v in c.get("facts", {}).items()
            },
            "identity_verification": c.get("identity_verification"),
            "documentary_sections": c.get("documentary_sections", []),
        }
    )


def identity_verified(c):
    gate = c.get("verification_gate") or {}
    return gate.get("state") == "VERIFIED_SCOPED" and gate.get("fingerprint") == fingerprint(c)


def dossier_full(c):
    # Paragraph count cannot turn generic fallbacks into covered sections.
    covered = {
        s["key"]
        for s in c.get("documentary_sections", [])
        if s["status"] in {"EVIDENCED", "NOT_APPLICABLE"} and s.get("references")
    }
    return identity_verified(c) and not (FULL_SECTIONS - covered)


def documentary_sources_allowed(db, c):
    """A mixed-source record keeps the most restrictive publication rights."""
    from app.models.knowledge_ops import SourceRegistry

    refs = [
        f["documentary_source"] for f in c.get("facts", {}).values() if f.get("documentary_source")
    ]
    refs += [r for s in c.get("documentary_sections", []) for r in s["references"]]
    refs += [
        ref
        for references in (c.get("identity_verification") or {}).get("field_evidence", {}).values()
        for ref in references
    ]
    for ref in refs:
        source = db.get(SourceRegistry, ref["registry_id"])
        if not source or source.paused or source.state not in {"APPROVED", "LOCAL_RESEARCH"}:
            return False
        if get_settings().environment == "production" and not source.config.get("commercial_reuse"):
            return False
    return True
