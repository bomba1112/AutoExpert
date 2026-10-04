"""Load the Chinese configuration catalogue snapshot (data_work/cn/staging) into the database.

One catalogue record (年款 + powertrain) becomes:
  - a vehicle_variants row: market CN, catalog_key "cn:<slug>", powertrain_type, battery_kwh,
    power_kw (the official power behind the record's fingerprint) and specifications.cn with
    everything that is not a technical fact (trims, sub-brand, aliases, fingerprints, listing
    values, verification, notes). No published_revision_id: nothing reaches the US buyer
    projection;
  - a technical_evidence "configuration" row (configuration_key "cn:<slug>") and one scoped
    CONFIGURATION fact per field, each with the source of its section and a display level by
    source host (sohu -> FACT; others -> SECONDARY_NOTE, owner decision 2026-10-04);
  - known_issues for the model's own owner reports (OWNER_REPORTS, no severity).
Components (engines / transmissions / hybrid systems) become scoped ENGINE / TRANSMISSION /
HYBRID_SYSTEM facts and issues keyed by engine_family_key / transmission_key /
hybrid_system_key. Inherited issues are not copied: cn_catalog.resolved_issues() joins them at
read time exactly like samr/tools/resolve_issues.py.

Idempotent: every row carries a natural_key (variants: catalog_key). An existing key with the
same content is skipped; a key whose content differs is reported as a conflict and left
unchanged unless replace_own is set (then every CN row of this loader is removed first).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import delete, func, select

from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.enums import (
    ConfidenceLevel,
    DataOrigin,
    DisplayLevel,
    EvidenceCategory,
    EvidenceStatus,
    ScopeLevel,
    SourceTier,
    SourceUsageStatus,
)
from app.models.evidence import KnownIssue, SourceRecord, TechnicalEvidence
from app.services.catalog_names import existing_name
from app.services.knowledge_import import normalized

LOAD_VERSION = "cn-catalog-load-1"
MARKET = "CN"
KEY_PREFIX = "cn:"
GENERATION_CODE = "CN"
HP_PER_KW = Decimal("1.36")  # metric horsepower (PS), the catalogue's and turbo.az's "a.g."
COMPONENT_KINDS = {
    "engine": ("engines", ScopeLevel.ENGINE, "engine_family_key"),
    "transmission": ("transmissions", ScopeLevel.TRANSMISSION, "transmission_key"),
    "hybrid_system": ("hybrid_systems", ScopeLevel.HYBRID_SYSTEM, "hybrid_system_key"),
}
POWERTRAIN = {"PHEV_series_parallel": "PHEV"}
# Owner-reported issue scope (the catalogue's category) -> nothing else: kept as component text.


def nkey(*parts) -> str:
    return hashlib.sha256(
        json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def plain(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def same(a, b) -> bool:
    numbers = (int, float, Decimal)
    if (
        isinstance(a, numbers)
        and isinstance(b, numbers)
        and not isinstance(a, bool)
        and not isinstance(b, bool)
    ):
        return Decimal(str(a)) == Decimal(str(b))
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def dec(value, places: str = "0.01") -> Decimal | None:
    return None if value is None else Decimal(str(value)).quantize(Decimal(places))


def span(value):
    """{min, max} -> scalar when equal; None when both empty."""
    if isinstance(value, dict) and set(value) <= {"min", "max"}:
        low, high = value.get("min"), value.get("max")
        if low is None and high is None:
            return None
        if low == high or high is None:
            return low
        if low is None:
            return high
        return {"min": low, "max": high}
    return value


# ---- staging ---------------------------------------------------------------------------


@dataclass
class Staging:
    root: Path
    manifest: dict
    model_map: dict
    records: dict[str, dict]  # slug -> record
    components: dict[tuple[str, str], dict]  # (kind, id) -> component


def read_staging(staging_dir: Path, model_map_path: Path) -> Staging:
    catalog = staging_dir / "catalog"
    records = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(catalog.glob("*.json"))
    }
    components = {}
    for kind, (folder, _, _) in COMPONENT_KINDS.items():
        for path in sorted((catalog / "components" / folder).glob("*.json")):
            component = json.loads(path.read_text(encoding="utf-8"))
            components[(kind, component["id"])] = component
    return Staging(
        root=staging_dir,
        manifest=json.loads((staging_dir / "MANIFEST.json").read_text(encoding="utf-8")),
        model_map=json.loads(model_map_path.read_text(encoding="utf-8")),
        records=records,
        components=components,
    )


def validate(staging: Staging) -> list[str]:
    """Problems that stop a load."""
    errors = []
    expected = staging.manifest["files"]
    catalog = staging.root / "catalog"
    for relative, digest in expected.items():
        path = catalog / relative
        if not path.exists():
            errors.append(f"missing {relative}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"sha256 differs from MANIFEST: {relative}")
    models = staging.model_map["models"]
    for slug, record in staging.records.items():
        if record["model"] not in models:
            errors.append(f"{slug}: model {record['model']!r} not in model_map")
        if record["powertrain_type"] not in {"ICE", "HEV", "PHEV_series_parallel", "EREV", "BEV"}:
            errors.append(f"{slug}: powertrain_type {record['powertrain_type']!r}")
        for kind, cid in (record.get("components") or {}).items():
            if cid and (kind, cid) not in staging.components:
                errors.append(f"{slug}: component {kind}/{cid} missing")
            if cid and len(cid) > 40:
                errors.append(f"{slug}: component key longer than 40: {cid}")
        if not isinstance(record.get("my"), int):
            errors.append(f"{slug}: model year {record.get('my')!r}")
    return errors


# ---- derived values --------------------------------------------------------------------


def fingerprints(record: dict) -> list[dict]:
    value = record.get("match_fingerprint")
    items = value if isinstance(value, list) else [value] if value else []
    out = []
    for item in items:
        hps = item.get("hp")
        for hp in hps if isinstance(hps, list) else [hps]:
            out.append({"battery_kwh": item.get("battery_kwh"), "hp": hp})
    return out


def power_options(record: dict) -> dict[str, Decimal]:
    """Official powers a seller's figure may stand for (kW): traction motors, engine, system,
    engine + motors. The fingerprint hp of the catalogue is one of them (checked 2026-10-04:
    motors for BEV/EREV/PHEV, engine for ICE, engine or system for HEV, engine+motors for
    Lynk 900)."""
    motor, engine = record.get("motor") or {}, record.get("engine") or {}
    motors = (motor.get("front_kw") or 0) + (motor.get("rear_kw") or 0) or motor.get("power_kw")
    options = {}
    if motors:
        options["motors"] = Decimal(str(motors))
    if engine.get("power_kw"):
        options["engine"] = Decimal(str(engine["power_kw"]))
    if record.get("system_power_hp"):
        options["system"] = (Decimal(str(record["system_power_hp"])) / HP_PER_KW).quantize(
            Decimal("0.1")
        )
    if motors and engine.get("power_kw"):
        options["engine_plus_motors"] = Decimal(str(motors)) + Decimal(str(engine["power_kw"]))
    return options


def fingerprint_power(record: dict) -> tuple[str | None, Decimal | None]:
    """The official power closest to the fingerprint hp (within 3 %)."""
    options = power_options(record)
    best = None
    for fp in fingerprints(record):
        if not fp["hp"]:
            continue
        kw = Decimal(str(fp["hp"])) / HP_PER_KW
        for name, value in options.items():
            gap = abs(kw - value) / value
            if gap <= Decimal("0.03") and (best is None or gap < best[0]):
                best = (gap, name, value)
    return (best[1], best[2]) if best else (None, None)


def engine_label(record: dict) -> str | None:
    engine = record.get("engine") or {}
    if not engine.get("code") and not engine.get("displacement_cc"):
        return None
    parts = []
    if engine.get("displacement_cc"):
        litres = (Decimal(engine["displacement_cc"]) / 1000).quantize(Decimal("0.1"))
        parts.append(f"{litres}{'T' if engine.get('aspiration') == 'T' else ''}")
    if engine.get("code"):
        parts.append(engine["code"])
    return " ".join(parts)


# ---- loader ----------------------------------------------------------------------------


@dataclass
class Report:
    counts: Counter = field(default_factory=Counter)
    conflicts: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    stale: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "counts": dict(sorted(self.counts.items())),
            "conflicts": self.conflicts,
            "warnings": self.warnings,
            "stale": self.stale,
        }


class CnLoader:
    def __init__(self, db, staging: Staging, *, retrieved_at: datetime | None = None):
        self.db = db
        self.s = staging
        self.report = Report()
        self.retrieved_at = retrieved_at or datetime.fromisoformat(staging.manifest["snapshot_at"])
        self.sources: dict[str, str] = {}
        self.makes: dict[str, VehicleMake] = {}
        self.generations: dict[str, VehicleGeneration] = {}
        self.variants: dict[str, VehicleVariant] = {}
        self.keys: set[str] = set()
        display = staging.model_map["source_display"]
        self.host_display = {
            host: level for level in ("FACT", "SECONDARY_NOTE") for host in display[level]
        }
        self.default_display = display["default"]

    # -- helpers ----------------------------------------------------------------------
    def display_for(self, url: str | None) -> DisplayLevel:
        host = urlparse(url or "").netloc
        return DisplayLevel(self.host_display.get(host, self.default_display))

    def source(self, url: str, section: str) -> str:
        if url in self.sources:
            return self.sources[url]
        host = urlparse(url).netloc
        marker = f"cn_source={hashlib.sha256(url.encode()).hexdigest()[:24]}"
        existing = self.db.scalar(
            select(SourceRecord).where(SourceRecord.notes.like(f"%{marker}%"))
        )
        if existing:
            self.sources[url] = existing.id
            return existing.id
        sohu = host.endswith("auto.sohu.com")
        if sohu:
            kind, tier, publisher = "CN_CONFIG_TABLE", SourceTier.B, "搜狐汽车 (sohu)"
        elif host.endswith("wikipedia.org"):
            kind, tier, publisher = "ENCYCLOPEDIA", SourceTier.C, "Wikipedia"
        elif host in ("www.xchuxing.com", "www.auto-data.net"):
            kind, tier, publisher = "SECONDARY_SPEC_DATABASE", SourceTier.B, host
        elif host == "www.samr.gov.cn":
            kind, tier, publisher = "REGULATOR", SourceTier.A, "SAMR (国家市场监督管理总局)"
        else:
            kind, tier, publisher = "AUTOMOTIVE_MEDIA", SourceTier.C, host
        record = SourceRecord(
            title=f"{publisher}: {section}"[:300],
            publisher=publisher[:200],
            url=url,
            source_type=kind,
            source_tier=tier,
            data_origin=DataOrigin.REAL,
            market=MARKET,
            language="zh"
            if host.endswith(".cn") or "sohu" in host or host.endswith("xchuxing.com")
            else "en",
            retrieved_at=self.retrieved_at,
            confidence=ConfidenceLevel.HIGH if sohu else ConfidenceLevel.MEDIUM,
            usage_status=SourceUsageStatus.ACTIVE,
            is_demo=False,
            notes=f"{marker}; samr_commit={self.s.manifest['samr_commit'][:12]}; "
            f"load={LOAD_VERSION}",
        )
        self.db.add(record)
        self.db.flush()
        self.sources[url] = record.id
        self.report.counts["source_records_new"] += 1
        return record.id

    def section_url(self, record: dict, *sections: str) -> str | None:
        sources = record.get("sources") or {}
        for section in (*sections, "config_table", "engine"):
            url = sources.get(section)
            if isinstance(url, list):
                url = url[0] if url else None
            if url and url.startswith("http"):
                return url
        return None

    # -- names ------------------------------------------------------------------------
    def make(self, name: str) -> VehicleMake:
        if name in self.makes:
            return self.makes[name]
        make = existing_name(self.db, name)
        if make is None:
            make = VehicleMake(name=name, normalized_name=normalized(name), is_demo=False)
            self.db.add(make)
            self.db.flush()
            self.report.counts["makes_new"] += 1
        self.makes[name] = make
        return make

    def generation(self, catalogue_model: str, years: list[int]) -> VehicleGeneration:
        if catalogue_model in self.generations:
            return self.generations[catalogue_model]
        target = self.s.model_map["models"][catalogue_model]
        make = self.make(target["make"])
        model = existing_name(self.db, target["model"], make_id=make.id)
        if model is None:
            model = VehicleModel(
                make_id=make.id,
                name=target["model"],
                normalized_name=normalized(target["model"]),
                is_demo=False,
            )
            self.db.add(model)
            self.db.flush()
            self.report.counts["models_new"] += 1
        generation = self.db.scalar(
            select(VehicleGeneration).where(
                VehicleGeneration.model_id == model.id, VehicleGeneration.code == GENERATION_CODE
            )
        )
        if generation is None:
            generation = VehicleGeneration(
                model_id=model.id,
                name="China market (年款)",
                code=GENERATION_CODE,
                start_year=min(years),
                end_year=max(years),
                is_demo=False,
            )
            self.db.add(generation)
            self.db.flush()
            self.report.counts["generations_new"] += 1
        else:
            # one CN generation per model spans every catalogue year of that model
            low, high = min(years), max(years)
            if generation.start_year is None or low < generation.start_year:
                generation.start_year = low
            if generation.end_year is None or high > generation.end_year:
                generation.end_year = high
        self.generations[catalogue_model] = generation
        return generation

    # -- rows -------------------------------------------------------------------------
    def add_fact(
        self,
        *,
        natural_key,
        fact_key,
        value,
        unit=None,
        url,
        category,
        scope,
        make_id,
        generation_id=None,
        configuration_key=None,
        years=(None, None),
        keys=None,
        conditions=None,
        variant_id=None,
        locator=None,
        statement=None,
        display=None,
    ):
        if value is None or value == "" or value == []:
            return
        if not url:
            self.report.warnings.append(
                f"{fact_key} {configuration_key or keys}: no source URL, not loaded"
            )
            return
        if natural_key in self.keys:
            self.report.counts["facts_duplicate_in_staging"] += 1
            return
        self.keys.add(natural_key)
        display = display or self.display_for(url)
        existing = self.db.scalar(
            select(TechnicalEvidence).where(TechnicalEvidence.natural_key == natural_key)
        )
        if existing:
            if same(existing.value, plain(value)) and existing.display_level == display:
                self.report.counts["facts_unchanged"] += 1
            else:
                self.report.conflicts.append(
                    {
                        "what": f"technical_evidence {fact_key} {configuration_key or keys}",
                        "natural_key": natural_key,
                        "existing": plain(existing.value),
                        "new": plain(value),
                        "existing_display": str(existing.display_level),
                        "new_display": str(display),
                    }
                )
            return
        secondary = display == DisplayLevel.SECONDARY_NOTE
        row = TechnicalEvidence(
            vehicle_variant_id=variant_id,
            source_id=self.source(url, fact_key),
            category=category,
            title=fact_key[:240],
            statement=(
                statement
                or f"{fact_key}: {json.dumps(plain(value), ensure_ascii=False)}"
                + (f" {unit}" if unit else "")
            ),
            status=EvidenceStatus.CONFIRMED,
            confidence=ConfidenceLevel.MEDIUM if secondary else ConfidenceLevel.HIGH,
            market=MARKET,
            conditions=conditions or {},
            is_demo=False,
            data_origin=DataOrigin.REAL,
            configuration_key=configuration_key,
            fact_key=fact_key,
            value=plain(value),
            unit=unit,
            locator=(locator or url)[:500],
            scope_level=scope,
            make_id=make_id,
            generation_id=generation_id,
            year_from=years[0],
            year_to=years[1],
            display_level=display,
            natural_key=natural_key,
            **(keys or {}),
        )
        self.db.add(row)
        self.report.counts["facts_new"] += 1

    def add_issue(
        self,
        *,
        natural_key,
        issue: dict,
        scope,
        make_id,
        generation_id=None,
        years=(None, None),
        keys=None,
        variant_id=None,
        extra=None,
    ):
        if natural_key in self.keys:  # the same review twice in one source file
            self.report.counts["issues_duplicate_in_staging"] += 1
            return
        self.keys.add(natural_key)
        conditions = {
            "source": issue["source"],
            "more_sources": issue.get("more_sources") or [],
            "review_car": issue.get("review_car"),
            "scope_note": issue.get("scope_note"),
            "reported_in": issue.get("reported_in"),
            "lang": "ru",
            "load": LOAD_VERSION,
            **(extra or {}),
        }
        conditions = {k: v for k, v in conditions.items() if v not in (None, [], "")}
        existing = self.db.scalar(select(KnownIssue).where(KnownIssue.natural_key == natural_key))
        if existing:
            if existing.description == issue["text"] and same(existing.conditions, conditions):
                self.report.counts["issues_unchanged"] += 1
            else:
                self.report.conflicts.append(
                    {
                        "what": f"known_issue {issue['text'][:60]}",
                        "natural_key": natural_key,
                        "existing": existing.conditions,
                        "new": conditions,
                    }
                )
            return
        self.db.add(
            KnownIssue(
                vehicle_variant_id=variant_id,
                component=(issue.get("scope") or "other")[:120],
                description=issue["text"],
                title=issue["text"][:240],
                affected_variants={},
                conditions=conditions,
                symptoms=[],
                severity=None,
                evidence_ids=[],
                source_count=1 + len(issue.get("more_sources") or []),
                confidence=ConfidenceLevel.LOW,
                inspection_recommendation="",
                status=EvidenceStatus.ESTIMATE,
                is_demo=False,
                data_origin=DataOrigin.REAL,
                market=MARKET,
                scope_level=scope,
                make_id=make_id,
                generation_id=generation_id,
                year_from=years[0],
                year_to=years[1],
                display_level=DisplayLevel.OWNER_REPORTS,
                natural_key=natural_key,
                **(keys or {}),
            )
        )
        self.report.counts["issues_new"] += 1

    # -- main -------------------------------------------------------------------------
    def remove_own(self) -> None:
        """Every row this loader writes (CN market, CN keys); sources, makes, models stay."""
        cn_variants = select(VehicleVariant.id).where(
            VehicleVariant.market == MARKET, VehicleVariant.catalog_key.like(f"{KEY_PREFIX}%")
        )
        removed = {
            "known_issues": self.db.execute(
                delete(KnownIssue).where(KnownIssue.market == MARKET)
            ).rowcount,
            "technical_evidence": self.db.execute(
                delete(TechnicalEvidence).where(TechnicalEvidence.market == MARKET)
            ).rowcount,
        }
        removed["vehicle_variants"] = self.db.execute(
            delete(VehicleVariant).where(VehicleVariant.id.in_(cn_variants))
        ).rowcount
        self.db.flush()
        for key, value in removed.items():
            self.report.counts[f"removed_{key}"] = value

    def load(self, *, replace_own: bool = False, prune_stale: bool = False) -> Report:
        if replace_own:
            self.remove_own()
        years_by_model = defaultdict(list)
        for record in self.s.records.values():
            years_by_model[record["model"]].append(record["my"])
        component_makes = self.component_makes()
        for slug, record in self.s.records.items():
            generation = self.generation(record["model"], years_by_model[record["model"]])
            self.load_record(slug, record, generation)
        for (kind, cid), component in self.s.components.items():
            self.load_component(kind, cid, component, component_makes.get((kind, cid)))
        self.find_stale(prune_stale)
        self.db.flush()
        return self.report

    def component_makes(self) -> dict:
        makes = defaultdict(set)
        for record in self.s.records.values():
            make = self.s.model_map["models"][record["model"]]["make"]
            for kind, cid in (record.get("components") or {}).items():
                if cid:
                    makes[(kind, cid)].add(make)
        return {key: next(iter(names)) for key, names in makes.items() if len(names) == 1}

    def load_record(self, slug: str, record: dict, generation: VehicleGeneration) -> None:
        target = self.s.model_map["models"][record["model"]]
        make = self.make(target["make"])
        key = KEY_PREFIX + slug
        powertrain = POWERTRAIN.get(record["powertrain_type"], record["powertrain_type"])
        components = record.get("components") or {}
        engine = record.get("engine") or {}
        battery = record.get("battery") or {}
        power_basis, power_kw = fingerprint_power(record)
        if power_kw is None:
            self.report.warnings.append(f"{slug}: no official power matches the fingerprint hp")
        keys = {
            "engine_family_key": engine.get("code") or None,
            "transmission_key": components.get("transmission"),
            "hybrid_system_key": components.get("hybrid_system"),
        }
        component_ids = {k: v for k, v in components.items() if v}
        listing = {
            k: record[k]
            for k in (
                "listing_values",
                "turbo_listings",
                "closest_official",
                "listing_copy",
                "copy_of",
            )
            if record.get(k) not in (None, [], False)
        }
        cn = {
            "slug": slug,
            "catalogue_model": record["model"],
            "model_cn": record.get("model_cn"),
            "sub_brand": target["sub_brand"],
            "aliases": sorted({*target["aliases"], *(record.get("aliases") or [])}),
            "twin_models": record.get("twin_models") or [],
            "model_year": record["my"],
            "trim_key": record["trim_key"],
            "trims": record.get("trims") or [],
            "generation_label": record.get("generation"),
            "status_china": record.get("status_china"),
            "powertrain_detail": record["powertrain_type"],
            "hybrid_system_name": record.get("hybrid_system"),
            "components": component_ids,
            "components_null_reason": record.get("components_null_reason"),
            "fingerprints": fingerprints(record),
            "power_basis": power_basis,
            "power_options_kw": {k: float(v) for k, v in power_options(record).items()},
            "listing": listing,
            "verification": record.get("verification"),
            "notes": record.get("notes"),
            "sohu_trim": record.get("sohu_trim"),
            "trim_page": (record.get("sources") or {}).get("trim_page"),
            "buyer_checks": record.get("buyer_checks") or [],
            "samr_commit": self.s.manifest["samr_commit"],
        }
        values = {
            "generation_id": generation.id,
            "specification_source_id": self.source(
                self.section_url(record, "config_table"), "config_table"
            ),
            "market": MARKET,
            "name": record["trim_key"][:180],
            "year_from": record["my"],
            "year_to": record["my"],
            "engine_code": engine.get("code"),
            "engine": engine_label(record),
            "transmission_code": None,
            "transmission": record.get("transmission"),
            "drivetrain": record.get("drive"),
            "body": None,
            "fuel": "ELECTRICITY" if powertrain == "BEV" else "GASOLINE",
            "displacement_l": dec(Decimal(engine["displacement_cc"]) / 1000)
            if engine.get("displacement_cc")
            else None,
            "power_kw": dec(power_kw),
            "powertrain_type": powertrain,
            "battery_kwh": dec(battery.get("kwh")),
            "specifications": {"cn": cn},
        }
        variant = self.db.scalar(select(VehicleVariant).where(VehicleVariant.catalog_key == key))
        if variant is None:
            variant = VehicleVariant(
                catalog_key=key,
                is_demo=False,
                data_origin=DataOrigin.REAL,
                editorial_locked=False,
                **values,
            )
            self.db.add(variant)
            self.db.flush()
            self.report.counts["variants_new"] += 1
        else:
            changed = {
                k: [plain(getattr(variant, k)), plain(v)]
                for k, v in values.items()
                if not same(plain(getattr(variant, k)), plain(v))
            }
            if changed:
                self.report.conflicts.append({"what": f"variant {key}", "changed": changed})
            else:
                self.report.counts["variants_unchanged"] += 1
        self.variants[slug] = variant
        years = (record["my"], record["my"])
        common = {
            "make_id": make.id,
            "generation_id": generation.id,
            "configuration_key": key,
            "years": years,
            "scope": ScopeLevel.CONFIGURATION,
            "locator": f"sohu trim {(record.get('sohu_trim') or {}).get('trim_id')}"
            if record.get("sohu_trim")
            else None,
        }
        identity = {
            "powertrain": powertrain,
            "powertrain_detail": record["powertrain_type"],
            "drivetrain": record.get("drive"),
            "battery_kwh": battery.get("kwh"),
            "power_kw": plain(power_kw),
            "power_basis": power_basis,
            "displacement_l": float(values["displacement_l"]) if values["displacement_l"] else None,
            "engine_family_key": keys["engine_family_key"],
            "transmission_key": keys["transmission_key"],
            "hybrid_system_key": keys["hybrid_system_key"],
            "fingerprints": fingerprints(record),
        }
        self.add_fact(
            natural_key=nkey("cn-cfg", slug),
            fact_key="configuration",
            value=key,
            url=self.section_url(record, "config_table"),
            category=EvidenceCategory.OTHER,
            variant_id=variant.id,
            conditions={"identity": identity, "load": LOAD_VERSION},
            keys={k: v for k, v in keys.items() if v},
            statement=f"{key}: {record['model']} {record['trim_key']}",
            display=DisplayLevel.FACT,
            **common,
        )
        for fact_key, value, unit, category, sections, extra in self.record_facts(
            record, powertrain
        ):
            self.add_fact(
                natural_key=nkey("cn-fact", slug, fact_key, extra.get("cycle")),
                fact_key=fact_key,
                value=value,
                unit=unit,
                url=self.section_url(record, *sections),
                category=category,
                conditions=extra,
                **common,
            )
        for order, issue in enumerate(record.get("known_issues") or []):
            self.add_issue(
                natural_key=nkey("cn-issue", slug, issue["source"], issue["text"]),
                issue=issue,
                scope=ScopeLevel.CONFIGURATION,
                make_id=make.id,
                generation_id=generation.id,
                years=years,
                variant_id=variant.id,
                extra={"configuration_key": key, "order": order},
            )

    @staticmethod
    def record_facts(record: dict, powertrain: str):
        """(fact_key, value, unit, category, source sections, conditions)."""
        E, T, L, F, B, X = (
            EvidenceCategory.ENGINE,
            EvidenceCategory.TRANSMISSION,
            EvidenceCategory.ELECTRICAL,
            EvidenceCategory.FUEL,
            EvidenceCategory.BODY,
            EvidenceCategory.OTHER,
        )
        engine, motor = record.get("engine") or {}, record.get("motor") or {}
        battery, charging = record.get("battery") or {}, record.get("charging") or {}
        motors = (motor.get("front_kw") or 0) + (motor.get("rear_kw") or 0) or motor.get("power_kw")
        motors_nm = (motor.get("front_nm") or 0) + (motor.get("rear_nm") or 0) or motor.get(
            "torque_nm"
        )
        fuel = record.get("fuel_l_100km") or {}
        dims = record.get("dimensions_mm") or {}
        rows = [
            ("powertrain", powertrain, None, E, ("config_table",), {}),
            ("hybrid_system_name", record.get("hybrid_system"), None, E, ("hybrid_system",), {}),
            ("platform", record.get("platform"), None, X, ("platform",), {}),
            ("engine_code", engine.get("code"), None, E, ("engine",), {}),
            ("engine_displacement_cc", engine.get("displacement_cc"), "cc", E, ("engine",), {}),
            ("aspiration", engine.get("aspiration"), None, E, ("engine",), {}),
            ("compression_ratio", engine.get("compression"), None, E, ("engine",), {}),
            ("engine_power_kw", engine.get("power_kw"), "kW", E, ("engine",), {}),
            ("engine_torque_nm", engine.get("torque_nm"), "N·m", E, ("engine",), {}),
            ("motor_type", motor.get("type"), None, L, ("motor",), {}),
            ("motor_count", motor.get("count"), None, L, ("motor",), {}),
            ("motor_axle", motor.get("axle"), None, L, ("motor",), {}),
            ("motor_power_kw", motors, "kW", L, ("motor",), {}),
            ("motor_front_kw", motor.get("front_kw"), "kW", L, ("motor",), {}),
            ("motor_rear_kw", motor.get("rear_kw"), "kW", L, ("motor",), {}),
            ("motor_torque_nm", motors_nm, "N·m", L, ("motor",), {}),
            ("system_power_hp", record.get("system_power_hp"), "PS", E, ("system_power",), {}),
            (
                "transmission_description",
                record.get("transmission"),
                None,
                T,
                ("config_table",),
                {},
            ),
            ("drivetrain", record.get("drive"), None, T, ("config_table",), {}),
            ("battery_kwh", battery.get("kwh"), "kWh", L, ("battery",), {}),
            ("battery_chemistry", battery.get("chemistry"), None, L, ("battery",), {}),
            ("battery_brand", battery.get("brand"), None, L, ("battery_supplier", "battery"), {}),
            (
                "battery_supplier",
                battery.get("supplier"),
                None,
                L,
                ("battery_supplier", "battery"),
                {},
            ),
            ("battery_cooling", battery.get("cooling"), None, L, ("battery",), {}),
            ("battery_voltage_v", battery.get("voltage_v"), "V", L, ("battery",), {}),
            (
                "consumption_kwh_100km",
                record.get("consumption_kwh_100km"),
                "kWh/100km",
                F,
                ("consumption",),
                {},
            ),
            (
                "fuel_l_100km_cn",
                fuel.get("value"),
                "L/100km",
                F,
                ("fuel",),
                {"cycle": fuel.get("cycle")} if fuel.get("cycle") else {},
            ),
            ("charging_connector", charging.get("connector"), None, L, ("charging",), {}),
            ("dc_supported", charging.get("dc_supported"), None, L, ("charging",), {}),
            ("dc_max_kw", charging.get("dc_kw"), "kW", L, ("charging",), {}),
            (
                "dc_charge_time_h",
                charging.get("dc_to_80_h"),
                "h",
                L,
                ("charging",),
                {"window_pct": charging.get("dc_window_pct")}
                if charging.get("dc_window_pct")
                else {},
            ),
            ("ac_max_kw", charging.get("ac_kw"), "kW", L, ("charging",), {}),
            ("ac_full_h", charging.get("ac_full_h"), "h", L, ("charging",), {}),
            ("accel_0_100_s", span(record.get("accel_0_100_s")), "s", X, ("performance",), {}),
            ("top_speed_kmh", record.get("top_speed_kmh"), "km/h", X, ("performance",), {}),
            ("curb_weight_kg", span(record.get("curb_weight_kg")), "kg", B, ("weight",), {}),
            ("length_mm", dims.get("length"), "mm", B, ("dimensions",), {}),
            ("width_mm", dims.get("width"), "mm", B, ("dimensions",), {}),
            ("height_mm", dims.get("height"), "mm", B, ("dimensions",), {}),
            ("wheelbase_mm", dims.get("wheelbase"), "mm", B, ("dimensions",), {}),
        ]
        if engine.get("compression") is None:
            rows = [r for r in rows if r[0] != "compression_ratio"]
        for cycle, value in (record.get("ev_range_km") or {}).items():
            if value is not None:
                # MIIT stays MIIT: it is not assumed to be CLTC (catalogue rule)
                rows.append(
                    (
                        "ev_range_km",
                        value,
                        "km",
                        L,
                        ("ev_range_km", "ev_range_km_2"),
                        {"cycle": cycle},
                    )
                )
        return rows

    def load_component(self, kind: str, cid: str, component: dict, make_name: str | None) -> None:
        _, scope, key_column = COMPONENT_KINDS[kind]
        make_id = self.make(make_name).id if make_name else None
        urls = [
            u
            for u in (component.get("sources") or {}).values()
            if isinstance(u, str) and u.startswith("http")
        ]
        # spec values are the union of the sohu tables of the configurations that use it
        sohu_url = next(
            (
                self.section_url(self.s.records[slug], kind if kind == "engine" else "config_table")
                for slug in component.get("used_in") or []
                if slug in self.s.records
            ),
            None,
        )
        common = {"scope": scope, "make_id": make_id, "keys": {key_column: cid}}
        identity_url = urls[0] if urls else sohu_url
        for fact_key, value in (
            ("component_name", component.get("name")),
            ("component_marketing_name", component.get("marketing_name")),
            ("component_codes", component.get("codes")),
            ("component_supplier", component.get("supplier")),
            ("component_generation", component.get("generation")),
        ):
            if fact_key == "component_name" or not urls:
                url = identity_url if fact_key == "component_name" and urls else sohu_url
            else:
                url = identity_url
            self.add_fact(
                natural_key=nkey("cn-comp", kind, cid, fact_key),
                fact_key=fact_key,
                value=value,
                url=url,
                category=EvidenceCategory.OTHER,
                conditions={"component_kind": kind, "note": component.get("note")}
                if component.get("note")
                else {"component_kind": kind},
                **common,
            )
        if component.get("specs"):
            self.add_fact(
                natural_key=nkey("cn-comp", kind, cid, "component_specs"),
                fact_key="component_specs",
                value=component["specs"],
                url=sohu_url or identity_url,
                category=EvidenceCategory.OTHER,
                conditions={"component_kind": kind},
                **common,
            )
        label = (
            (component.get("codes") or [cid])[0]
            if kind == "engine"
            else (component.get("marketing_name") or component.get("name") or cid)
        )
        for order, issue in enumerate(component.get("known_issues") or []):
            self.add_issue(
                natural_key=nkey("cn-comp-issue", kind, cid, issue["source"], issue["text"]),
                issue={**issue, "scope": issue.get("scope", kind)},
                scope=scope,
                make_id=make_id,
                keys={key_column: cid},
                extra={
                    "component_kind": kind,
                    "component": cid,
                    "component_label": label,
                    "order": order,
                },
            )
        self.report.counts[f"components_{kind}"] += 1

    def find_stale(self, prune: bool) -> None:
        rows = [
            *self.db.execute(
                select(
                    TechnicalEvidence.id, TechnicalEvidence.natural_key, TechnicalEvidence.fact_key
                ).where(TechnicalEvidence.market == MARKET)
            ).all(),
        ]
        issues = self.db.execute(
            select(KnownIssue.id, KnownIssue.natural_key, KnownIssue.description).where(
                KnownIssue.market == MARKET
            )
        ).all()
        variants = self.db.execute(
            select(VehicleVariant.id, VehicleVariant.catalog_key).where(
                VehicleVariant.market == MARKET, VehicleVariant.catalog_key.like(f"{KEY_PREFIX}%")
            )
        ).all()
        wanted_variants = {KEY_PREFIX + slug for slug in self.s.records}
        stale_facts = [r for r in rows if r.natural_key not in self.keys]
        stale_issues = [r for r in issues if r.natural_key not in self.keys]
        stale_variants = [r for r in variants if r.catalog_key not in wanted_variants]
        self.report.stale = (
            [
                {
                    "table": "technical_evidence",
                    "fact_key": r.fact_key,
                    "natural_key": r.natural_key,
                }
                for r in stale_facts
            ]
            + [
                {"table": "known_issues", "text": r.description[:80], "natural_key": r.natural_key}
                for r in stale_issues
            ]
            + [{"table": "vehicle_variants", "catalog_key": r.catalog_key} for r in stale_variants]
        )
        if prune and self.report.stale:
            self.db.execute(
                delete(TechnicalEvidence).where(
                    TechnicalEvidence.id.in_([r.id for r in stale_facts])
                )
            )
            self.db.execute(
                delete(KnownIssue).where(KnownIssue.id.in_([r.id for r in stale_issues]))
            )
            self.db.execute(
                delete(VehicleVariant).where(VehicleVariant.id.in_([r.id for r in stale_variants]))
            )
            self.report.counts["pruned"] = len(self.report.stale)


def db_counts(db) -> dict:
    """CN row counts, for the load report."""
    return {
        "variants": db.scalar(
            select(func.count()).select_from(VehicleVariant).where(VehicleVariant.market == MARKET)
        ),
        "technical_evidence": db.scalar(
            select(func.count())
            .select_from(TechnicalEvidence)
            .where(TechnicalEvidence.market == MARKET)
        ),
        "known_issues": db.scalar(
            select(func.count()).select_from(KnownIssue).where(KnownIssue.market == MARKET)
        ),
        "source_records": db.scalar(
            select(func.count()).select_from(SourceRecord).where(SourceRecord.market == MARKET)
        ),
    }
