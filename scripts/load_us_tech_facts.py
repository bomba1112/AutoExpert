"""Load a validated staging set (scripts/build_us_tech_staging.py) into the database.

Writes only through the ORM in ONE transaction:
  - raw_documents (via knowledge_import.store_document) and source_records per source file;
  - fills NULL start/end years of existing generations and creates missing ones
    (never renames or changes existing values; DEMO and UNRESOLVED generations untouched);
  - f087 scoped technical_evidence rows: facts, research-layer configurations, recalls,
    used manufacturer communications and complaint symptom patterns;
  - f087 scoped known_issues;
  - nothing in vehicle_variants, catalog_revisions or commercial_fact_claims (no publication).
Idempotent: every row carries a natural_key; an existing key is skipped, a key whose stored
value differs is reported as a conflict and left unchanged.

  .venv/Scripts/python.exe scripts/load_us_tech_facts.py toyota camry --db <sqlite path> [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))
from us_tech_common import RAW_ROOT  # noqa: E402


def source_path(path: str) -> Path:
    """rawstore:<rel> lives in the raw store outside OneDrive; other paths are repo-relative."""
    if path.startswith("rawstore:"):
        return RAW_ROOT / path[len("rawstore:") :]
    return ROOT / path

LOAD_VERSION = "us-tech-load-1"
REGISTRY = {  # knowledge_sources registry id per staging source_type (existing rows only)
    "OWNER_MANUAL_COPY": "factory-toyota-us",
    "PRODUCT_INFORMATION": "factory-toyota-us",
    "PRESS_RELEASE": "factory-toyota-us",
    "MANUFACTURER_SUPPORT_ARTICLE": "factory-toyota-us",
    "US_FEDERAL_DATASET": None,  # resolved per key below (epa / nhtsa)
    "VPIC_CANADIAN_SPECIFICATIONS": "nhtsa-vpic-vehicle-api",
    "NHTSA_RECALLS_API": "nhtsa-safety-batch",
    "NHTSA_COMPLAINTS_API": "nhtsa-safety-batch",
}
CATEGORY = {
    "body": "BODY",
    "seats": "BODY",
    "length_mm": "BODY",
    "width_mm": "BODY",
    "height_mm": "BODY",
    "wheelbase_mm": "BODY",
    "track_front_mm": "BODY",
    "track_rear_mm": "BODY",
    "track_front_rear_in": "BODY",
    "ground_clearance": "BODY",
    "cargo_l": "BODY",
    "curb_weight_kg": "BODY",
    "factory_model_code": "OTHER",
    "fuel_tank_l": "FUEL",
    "fuel_type": "FUEL",
    "octane_aki": "FUEL",
    "octane_ron": "FUEL",
    "front_suspension": "SUSPENSION",
    "rear_suspension": "SUSPENSION",
    "steering": "STEERING",
    "front_brakes": "BRAKES",
    "rear_brakes": "BRAKES",
    "brake_fluid": "BRAKES",
    "tires": "OTHER",
    "tire_pressure_front_kpa": "OTHER",
    "tire_pressure_rear_kpa": "OTHER",
    "wheel_nut_torque_nm": "OTHER",
    "coolant": "MAINTENANCE",
    "coolant_capacity_l": "MAINTENANCE",
    "engine_oil_viscosity": "MAINTENANCE",
    "engine_oil_alternatives": "MAINTENANCE",
    "engine_oil_specification": "MAINTENANCE",
    "engine_oil_capacity_l": "MAINTENANCE",
    "engine_oil_capacity_without_filter_l": "MAINTENANCE",
    "spark_plug": "MAINTENANCE",
    "transmission_fluid": "TRANSMISSION",
    "transmission_fluid_capacity_l": "TRANSMISSION",
    "transmission_description": "TRANSMISSION",
    "transmission_code": "TRANSMISSION",
    "electric_motor": "ELECTRICAL",
    "traction_battery": "ELECTRICAL",
}
STATUS = {
    "FACT": "CONFIRMED",
    "SECONDARY_NOTE": "CONFIRMED",
    "OWNER_REPORTS": "ESTIMATE",
    "HIDDEN_CONFLICT": "NEEDS_INSPECTION",
}


def nkey(*parts) -> str:
    return hashlib.sha256(
        json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def as_json_scalar(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def same_value(a, b) -> bool:
    """Numeric-aware equality: SQLite JSON stores 4.0 as 4."""
    numbers = (int, float, Decimal)
    if (
        isinstance(a, numbers)
        and isinstance(b, numbers)
        and not isinstance(a, bool)
        and not isinstance(b, bool)
    ):
        return Decimal(str(a)) == Decimal(str(b))
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


class Loader:
    def __init__(self, db, staging, line_name, report):
        from app.models.catalog import VehicleMake, VehicleModel
        from sqlalchemy import select

        self.db, self.s, self.report = db, staging, report
        self.make = db.scalar(select(VehicleMake).where(VehicleMake.name == staging["make"]))
        names = staging.get("db_models") or [line_name]
        self.models = {name: self.model_row(name) for name in names}
        self.model = self.models[names[0]]
        self.source_ids, self.raw_ids, self.gen_ids = {}, {}, {}
        self.te_by_key = {}
        self.counts = Counter()

    def model_row(self, name):
        """Existing model of the make, or a new one for a line the catalog does not have yet."""
        from app.models.catalog import VehicleModel
        from sqlalchemy import select

        row = self.db.scalar(
            select(VehicleModel).where(
                VehicleModel.make_id == self.make.id, VehicleModel.name == name
            )
        )
        if row is None:
            row = VehicleModel(
                make_id=self.make.id, name=name, normalized_name=name.lower(), is_demo=False
            )
            self.db.add(row)
            self.db.flush()
            self.report.setdefault("models_created", []).append(name)
        return row

    # ---- sources -------------------------------------------------------------------
    def load_sources(self):
        from app.models.enums import ConfidenceLevel, DataOrigin, SourceTier, SourceUsageStatus
        from app.models.evidence import SourceRecord
        from app.services.knowledge_import import store_document
        from sqlalchemy import select

        for key, item in self.s["sources"].items():
            registry = item.get("registry") or REGISTRY.get(item["source_type"])
            if item["source_type"] == "US_FEDERAL_DATASET" and not item.get("registry"):
                registry = "epa" if key == "epa" else "nhtsa-safety-batch"
            paths = item.get("paths") or [item["path"]]
            raw_id = None
            for path in paths:
                # Batch PDF sources store only the cited pages (with the PDF sha256) as the raw
                # document; the full PDF stays in the raw store outside OneDrive.
                extract = item.get("extract")
                content = extract.encode("utf-8") if extract else source_path(path).read_bytes()
                media = (
                    "application/json"
                    if extract
                    else "application/gzip"
                    if path.endswith(".gz")
                    else "application/pdf"
                    if path.endswith(".pdf")
                    else "application/zip"
                    if path.endswith(".zip")
                    else "text/html"
                    if path.endswith(".html")
                    else "application/json"
                    if path.endswith(".json")
                    else "text/plain"
                )
                doc = store_document(
                    self.db, registry, content, locator=item.get("url") or path, media_type=media
                )
                raw_id = raw_id or doc.id
                self.counts["raw_documents_seen"] += 1
            self.raw_ids[key] = raw_id
            digest = (
                item.get("sha256") or hashlib.sha256(source_path(paths[0]).read_bytes()).hexdigest()
            )
            marker = f"us_tech_source={key}; sha256={digest}"
            existing = self.db.scalar(
                select(SourceRecord).where(SourceRecord.notes.like(f"%{marker}%"))
            )
            if existing:
                self.source_ids[key] = existing.id
                continue
            record = SourceRecord(
                title=item["title"][:300],
                publisher=item["publisher"][:200],
                url=item.get("url") or "",
                source_type=item["source_type"],
                source_tier=SourceTier(item["tier"]),
                data_origin=DataOrigin.REAL,
                market="US",
                language="en",
                retrieved_at=datetime.fromisoformat(item["retrieved_at"].replace("Z", "+00:00"))
                if "T" in item["retrieved_at"]
                else datetime.fromisoformat(item["retrieved_at"] + "T00:00:00+00:00"),
                confidence=ConfidenceLevel.HIGH if item["tier"] == "A" else ConfidenceLevel.MEDIUM,
                usage_status=SourceUsageStatus.ACTIVE,
                is_demo=False,
                notes=f"{marker}; registry={registry}; raw={','.join(paths)}; authenticity={item.get('authenticity')}; "
                f"edition={item.get('edition')}; page_url={item.get('page_url')}; load={LOAD_VERSION}",
            )
            self.db.add(record)
            self.db.flush()
            self.source_ids[key] = record.id
            self.counts["source_records_new"] += 1

    # ---- generations -----------------------------------------------------------------
    def load_generations(self):
        from app.models.catalog import VehicleGeneration
        from sqlalchemy import select

        for gen in self.s["generations"]:
            model = self.model
            if gen.get("db_model"):
                model = self.models.get(gen["db_model"]) or self.model_row(gen["db_model"])
            if gen.get("existing_id"):
                row = self.db.get(VehicleGeneration, gen["existing_id"])
            else:
                row = self.db.scalar(
                    select(VehicleGeneration).where(
                        VehicleGeneration.model_id == model.id,
                        VehicleGeneration.code == gen["code"],
                        VehicleGeneration.is_demo.is_(False),
                    )
                )
            # Batch staging marks which years a detected boundary backs; Camry staging has no
            # flags because both years come from its sources.
            start_year = gen["start_year"] if gen.get("start_known", True) else None
            end_year = (
                None
                if gen.get("open_ended") or not gen.get("end_known", True)
                else gen["end_year"]
            )
            if row is None:
                row = VehicleGeneration(
                    model_id=model.id,
                    name=gen.get("name") or f"{gen['code']} generation",
                    code=gen["code"],
                    start_year=start_year,
                    end_year=end_year,
                    is_demo=False,
                )
                self.db.add(row)
                self.db.flush()
                self.report["generations"].append(
                    {
                        "code": gen["code"],
                        "action": "created",
                        "start_year": start_year,
                        "end_year": end_year,
                    }
                )
            else:
                changes = {}
                if row.start_year is None and start_year is not None:
                    row.start_year, changes["start_year"] = start_year, start_year
                elif None not in (row.start_year, start_year) and row.start_year != start_year:
                    self.report["conflicts"].append(
                        {
                            "what": f"generation {gen['code']} start_year",
                            "existing": row.start_year,
                            "new": start_year,
                            "resolution": "existing kept",
                        }
                    )
                if row.end_year is None and end_year is not None:
                    row.end_year, changes["end_year"] = end_year, end_year
                elif None not in (row.end_year, end_year) and row.end_year != end_year:
                    self.report["conflicts"].append(
                        {
                            "what": f"generation {gen['code']} end_year",
                            "existing": row.end_year,
                            "new": end_year,
                            "resolution": "existing kept",
                        }
                    )
                self.report["generations"].append(
                    {"code": gen["code"], "action": "filled" if changes else "unchanged", **changes}
                )
            self.gen_ids[gen["code"]] = row.id

    # ---- technical evidence ------------------------------------------------------------
    def add_te(
        self,
        *,
        natural_key,
        category,
        title,
        statement,
        scope_level,
        fact_key,
        value,
        unit=None,
        generation=None,
        engine=None,
        transmission=None,
        configuration_key=None,
        years=None,
        display_level="FACT",
        confidence="HIGH",
        source_key,
        locator=None,
        conditions=None,
        variant_id=None,
    ):
        from app.models.enums import (
            ConfidenceLevel,
            DataOrigin,
            DisplayLevel,
            EvidenceCategory,
            EvidenceStatus,
            ScopeLevel,
        )
        from app.models.evidence import TechnicalEvidence
        from sqlalchemy import select

        existing = self.db.scalar(
            select(TechnicalEvidence).where(TechnicalEvidence.natural_key == natural_key)
        )
        if existing:
            if not same_value(existing.value, as_json_scalar(value)):
                self.report["conflicts"].append(
                    {
                        "what": f"technical_evidence {natural_key[:12]} {fact_key}",
                        "existing": existing.value,
                        "new": value,
                        "resolution": "existing kept",
                    }
                )
            self.counts["te_existing"] += 1
            self.te_by_key[natural_key] = existing.id
            return existing.id
        row = TechnicalEvidence(
            vehicle_variant_id=variant_id,
            source_id=self.source_ids[source_key],
            category=EvidenceCategory[category],
            title=title[:240],
            statement=statement,
            status=EvidenceStatus(STATUS[display_level]),
            confidence=ConfidenceLevel(confidence),
            market="US",
            conditions={**(conditions or {}), "load": LOAD_VERSION, "line": self.s["line"]},
            is_demo=False,
            data_origin=DataOrigin.REAL,
            scope_level=ScopeLevel(scope_level),
            make_id=self.make.id,
            generation_id=self.gen_ids.get(generation) if generation else None,
            engine_family_key=engine,
            transmission_key=transmission,
            configuration_key=configuration_key,
            year_from=years[0] if years else None,
            year_to=years[1] if years else None,
            fact_key=fact_key,
            value=as_json_scalar(value),
            unit=unit,
            raw_document_id=self.raw_ids.get(source_key),
            locator=(locator or "")[:500] or None,
            display_level=DisplayLevel(display_level),
            natural_key=natural_key,
        )
        self.db.add(row)
        self.db.flush()
        self.counts[f"te_new_{scope_level}"] += 1
        self.te_by_key[natural_key] = row.id
        return row.id

    def load_facts(self):
        for fact in self.s["facts"]:
            primary = next(c for c in fact["cites"] if c["source"] == fact["primary_source"])
            level = fact["level"]
            gen_bound = fact.get("gen_bound", True)
            unit = fact.get("unit")
            shown = f"{fact['value']}{' ' + unit if unit else ''}"
            # Semantic scope, never the value or the file position: a changed value for the same
            # scope is reported as a conflict instead of creating a second row.
            scope = (
                "fact",
                self.s["make"],
                self.s["line"],
                fact["generation"],
                level,
                fact.get("engine"),
                fact["key"],
                fact["years"],
                fact.get("applicability") or {},
                "conflict" if fact["display_level"] == "HIDDEN_CONFLICT" else "main",
            )
            self.add_te(
                natural_key=nkey(*scope),
                category=CATEGORY.get(
                    fact["key"],
                    "ENGINE"
                    if level == "ENGINE"
                    or fact["key"]
                    in {
                        "engine_layout",
                        "cylinders",
                        "engine_displacement_cc",
                        "bore_stroke_mm",
                        "bore_stroke_in",
                        "compression_ratio",
                        "valvetrain",
                        "injection",
                        "timing_drive",
                        "power_hp",
                        "torque_lb_ft",
                        "system_power_hp",
                        "engine_description",
                        "hybrid_engine_description",
                        "engine_code_applicability",
                    }
                    else "OTHER",
                ),
                title=fact["key"],
                statement=f"{shown} — {fact.get('original') or ''}".strip(" —"),
                scope_level=level,
                fact_key=fact["key"],
                value=fact["value"],
                unit=unit,
                generation=fact["generation"] if (level != "ENGINE" or gen_bound) else None,
                engine=fact.get("engine"),
                years=fact["years"],
                display_level=fact["display_level"],
                confidence=fact["confidence"],
                source_key=fact["primary_source"],
                locator=f"page {primary['pages'][0]}"
                if primary.get("pages")
                else primary["quote"][:200],
                conditions={
                    "applicability": fact.get("applicability") or {},
                    "original": fact.get("original"),
                    "note": fact.get("note"),
                    "staging_id": fact["id"],
                    "cites": [
                        {
                            "source": c["source"],
                            "pages": c.get("pages"),
                            "quote": c["quote"],
                            "tier": c["tier"],
                        }
                        for c in fact["cites"]
                    ],
                },
            )

    def factory_variant(self, year, cfg):
        """Existing published factory-toyota-us variant of the same year/engine/drive/powertrain."""
        from app.models.catalog import VehicleGeneration, VehicleVariant
        from sqlalchemy import select

        rows = self.db.scalars(
            select(VehicleVariant)
            .join(VehicleGeneration, VehicleGeneration.id == VehicleVariant.generation_id)
            .where(
                VehicleGeneration.model_id == self.model.id,
                VehicleVariant.year_from == year,
                VehicleVariant.market == "US",
                VehicleVariant.catalog_key.like(f"{self.factory_prefix()}:%"),
                VehicleVariant.is_demo.is_(False),
            )
        ).all()
        matches = []
        for v in rows:
            facts = (v.specifications or {}).get("catalog", {}).get("facts", {})
            value = lambda k: (facts.get(k) or {}).get("value")  # noqa: E731
            if (
                (
                    str(value("engine_displacement"))
                    == str(Decimal(cfg["displacement_l"]).normalize())
                    or Decimal(str(value("engine_displacement") or 0))
                    == Decimal(cfg["displacement_l"])
                )
                and value("drivetrain") == cfg["drivetrain"]
                and value("powertrain") == cfg["powertrain"]
            ):
                matches.append(v.id)
        return matches[0] if len(matches) == 1 else None

    def factory_prefix(self):
        return {
            "Mercedes-Benz": "factory-mercedes-us",
            "Land Rover": "factory-land-rover-us",
            "Volkswagen": "factory-vw-us",
        }.get(self.s["make"], f"factory-{self.s['make'].lower()}-us")

    def load_configurations(self):
        for cfg in self.s["configurations"]:
            key = cfg["configuration_key"]
            year = cfg["year"]
            linkable = (year <= 2020 or self.s.get("build")) and cfg.get("displacement_l")
            variant = self.factory_variant(year, cfg) if linkable else None
            base = {
                "configuration_key": key,
                "generation": cfg["generation"],
                "years": [year, year],
                "engine": cfg["engine_family_key"],
                "source_key": "epa",
                "variant_id": variant,
                "scope_level": "CONFIGURATION",
                "category": "OTHER",
            }
            identity = {
                "powertrain": cfg["powertrain"],
                "drivetrain": cfg["drivetrain"],
                "engine_family_key": cfg["engine_family_key"],
                "displacement_l": cfg["displacement_l"],
                "cylinders": cfg["cylinders"],
                "epa_transmission": cfg["epa_trany"],
                "aspiration": cfg["aspiration"],
                "epa_ids": [e["epa_id"] for e in cfg["epa_vehicles"]],
                "linked_factory_variant": variant,
                "research_layer_only": variant is None,
            }
            self.add_te(
                natural_key=nkey("cfg", key),
                title="configuration",
                fact_key="configuration",
                statement=f"{key}: {cfg['displacement_l']} L {cfg['cylinders']}-cyl {cfg['powertrain']}, {cfg['epa_trany']}, {cfg['drivetrain']}",
                value=key,
                locator=f"EPA ids {','.join(identity['epa_ids'])}",
                conditions={
                    "identity": identity,
                    "engine_rule_cites": cfg.get("engine_rule_cites"),
                },
                **base,
            )
            for fk, val, cat in (
                ("powertrain", cfg["powertrain"], "ENGINE"),
                ("drivetrain", cfg["drivetrain"], "TRANSMISSION"),
                ("transmission_description_epa", cfg["epa_trany"], "TRANSMISSION"),
                ("engine_displacement_l", cfg["displacement_l"], "ENGINE"),
                ("cylinders", cfg["cylinders"], "ENGINE"),
                ("aspiration", cfg["aspiration"], "ENGINE"),
            ):
                if val is None:
                    continue
                self.add_te(
                    natural_key=nkey("cfgfact", key, fk),
                    title=fk,
                    fact_key=fk,
                    statement=f"{val} (EPA)",
                    value=val,
                    locator=f"EPA ids {','.join(identity['epa_ids'])}",
                    conditions={"epa_ids": identity["epa_ids"]},
                    **{**base, "category": cat},
                )
            for epa in cfg["epa_vehicles"]:
                for fk, val, unit in (
                    ("epa_city_mpg", epa["city_mpg"], "mpg"),
                    ("epa_highway_mpg", epa["highway_mpg"], "mpg"),
                    ("epa_combined_mpg", epa["combined_mpg"], "mpg"),
                    ("fuel_combined", float(epa["combined_l_100km"]), "L/100km"),
                ):
                    self.add_te(
                        natural_key=nkey("cfgepa", key, epa["epa_id"], fk),
                        title=fk,
                        fact_key=fk,
                        statement=f"{val} {unit} (EPA {epa['epa_id']}, {epa['epa_model']})",
                        value=val,
                        unit=unit,
                        locator=f"EPA vehicle {epa['epa_id']}",
                        conditions={
                            "epa_id": epa["epa_id"],
                            "epa_model": epa["epa_model"],
                            "fuel_type": epa["fuel_type"],
                        },
                        **{**base, "category": "FUEL"},
                    )
            self.counts["configurations"] += 1
            self.counts["configurations_linked" if variant else "configurations_research_only"] += 1

    def load_recalls(self):
        for r in self.s["recalls"]:
            src = r.get("source") or f"nhtsa-recalls-{r['model_years'][0]}"
            self.add_te(
                natural_key=nkey("recall", self.s["line"], r["campaign_number"], r["generation"]),
                category="SAFETY",
                title=f"NHTSA recall {r['campaign_number']}",
                fact_key="nhtsa_recall",
                statement=f"{r['campaign_number']}: {r['component']}. {r['summary']}",
                scope_level="GENERATION",
                value=r["campaign_number"],
                generation=r["generation"],
                years=r["years"],
                source_key=src,
                locator=f"NHTSA campaign {r['campaign_number']}",
                conditions={
                    "campaign_number": r["campaign_number"],
                    "component": r["component"],
                    "summary": r["summary"],
                    "consequence": r["consequence"],
                    "remedy": r["remedy"],
                    "report_received_date": r["report_received_date"],
                    "model_years": r["model_years"],
                    "applicability": "model year match; VIN applicability must be checked",
                },
            )

    def load_tsbs(self, generations):
        for t in self.s["tsbs"]:
            in_scope = [y for y in t["years"] if 2014 <= y <= 2026]
            for gen in generations:
                years = [y for y in in_scope if gen["start_year"] <= y <= gen["end_year"]]
                if not years:
                    continue
                self.add_te(
                    natural_key=nkey("tsb", self.s["line"], t["id"], gen["code"]),
                    category="MAINTENANCE",
                    title=f"Manufacturer Communication {t['id']}",
                    fact_key="nhtsa_mfr_communication",
                    statement=t["summary"],
                    scope_level="GENERATION",
                    value=t["id"],
                    generation=gen["code"],
                    years=[min(years), max(years)],
                    source_key="nhtsa-mfrcomms",
                    locator=f"NHTSA MfrComms {t['id']} ({t['file']})",
                    conditions={
                        "document_id": t["id"],
                        "model": t["model"],
                        "model_years": t["years"],
                        "summary": t["summary"],
                    },
                )

    def load_symptom_patterns(self):
        for key, p in self.s["symptom_patterns"].items():
            gen, symptom = key.split("|", 1)
            years = sorted(int(y) for y in p["by_year"])
            first = p.get("source") or f"nhtsa-complaints-{years[0]}"
            self.add_te(
                natural_key=nkey("cmplpattern", self.s["line"], key),
                category="OTHER",
                title=f"NHTSA complaints: {symptom}",
                fact_key="nhtsa_complaint_pattern",
                statement=f"{p['count']} NHTSA complaints mention '{symptom}' for MY{years[0]}-{years[-1]} (by year {p['by_year']}); complaints are not engine-specific.",
                scope_level="GENERATION",
                value=p["count"],
                generation=gen,
                years=[years[0], years[-1]],
                display_level="OWNER_REPORTS",
                confidence="LOW",
                source_key=first,
                locator="NHTSA complaintsByVehicle narratives, keyword pattern",
                conditions={
                    "symptom": symptom,
                    "by_year": p["by_year"],
                    "sample_odi": p["sample_odi"],
                    "above_threshold": p["above_threshold"],
                    "engine_specific": False,
                },
            )

    def load_issues(self):
        from app.models.enums import (
            ConfidenceLevel,
            DataOrigin,
            DisplayLevel,
            EvidenceStatus,
            IssueProbability,
            ScopeLevel,
            Severity,
        )
        from app.models.evidence import KnownIssue
        from sqlalchemy import select

        recall_ids = {}
        for r in self.s["recalls"]:
            recall_ids.setdefault(r["campaign_number"], []).append(
                self.te_by_key[
                    nkey("recall", self.s["line"], r["campaign_number"], r["generation"])
                ]
            )
        for issue in self.s["issues"]:
            key = nkey("issue", self.s["line"], issue["id"])
            if self.db.scalar(select(KnownIssue).where(KnownIssue.natural_key == key)):
                self.counts["issues_existing"] += 1
                continue
            ev = issue["evidence"]
            evidence_ids = [i for n in ev.get("recalls", []) for i in recall_ids.get(n, [])]
            evidence_ids += [
                self.te_by_key[k]
                for t in ev.get("tsbs", [])
                for k in self.te_by_key
                if k == nkey("tsb", self.s["line"], t, issue["generation"])
            ]
            evidence_ids += [
                self.te_by_key[nkey("cmplpattern", self.s["line"], k)]
                for k in ev.get("complaint_patterns", [])
            ]
            manufacturer_backed = bool(ev.get("recalls") or ev.get("tsbs"))
            row = KnownIssue(
                vehicle_variant_id=None,
                component=issue["component"],
                description=issue["title"] + ". " + issue["cause"],
                affected_variants={
                    "generation": issue["generation"],
                    "years": issue["years"],
                    "engines": issue.get("engines")
                    or ([issue["engine"]] if issue.get("engine") else []),
                    "powertrain": issue.get("powertrain"),
                },
                conditions={
                    "note": issue.get("note"),
                    "complaints_in_years": issue.get("complaints_in_years"),
                    "evidence": ev,
                    "load": LOAD_VERSION,
                    "line": self.s["line"],
                    "staging_id": issue["id"],
                },
                symptoms=issue["symptoms"],
                consequences=issue["consequences"],
                severity=Severity(issue["severity"]),
                evidence_ids=evidence_ids,
                source_count=len(evidence_ids),
                confidence=ConfidenceLevel.HIGH if manufacturer_backed else ConfidenceLevel.LOW,
                inspection_recommendation=issue["inspection"],
                status=EvidenceStatus.CONFIRMED if manufacturer_backed else EvidenceStatus.ESTIMATE,
                is_demo=False,
                data_origin=DataOrigin.REAL,
                scope_level=ScopeLevel(issue["scope_level"]),
                make_id=self.make.id,
                generation_id=self.gen_ids[issue["generation"]],
                engine_family_key=issue.get("engine"),
                transmission_key=issue.get("transmission"),
                year_from=issue["years"][0],
                year_to=issue["years"][1],
                display_level=DisplayLevel.FACT
                if manufacturer_backed
                else DisplayLevel.OWNER_REPORTS,
                natural_key=key,
                market="US",
                title=issue["title"],
                cause=issue["cause"],
                typical_fix=issue["typical_fix"],
                probability=IssueProbability(issue["probability"]),
            )
            self.db.add(row)
            self.db.flush()
            self.counts["issues_new"] += 1

    def delete_own_line_rows(self):
        """--replace-own: remove the rows THIS pipeline wrote for this line (technical_evidence
        and known_issues tagged with this load version and exactly this line) so the line can be
        reloaded after a staging-rule change (e.g. moved generation boundaries). Anything else
        referencing those rows stops the run."""
        from app.models.evidence import KnownIssue, TechnicalEvidence
        from app.models.vehicle_knowledge import vehicle_profile_evidence
        from sqlalchemy import func, select

        own = lambda model: (  # noqa: E731
            model.make_id == self.make.id,
            func.json_extract(model.conditions, "$.load") == LOAD_VERSION,
            func.json_extract(model.conditions, "$.line") == self.s["line"],
        )
        te_ids = list(self.db.scalars(select(TechnicalEvidence.id).where(*own(TechnicalEvidence))))
        if te_ids:
            used = self.db.scalar(
                select(func.count()).select_from(vehicle_profile_evidence).where(
                    vehicle_profile_evidence.c.evidence_id.in_(te_ids)
                )
            )
            if used:
                raise SystemExit(f"--replace-own: {used} profile evidence rows reference this line's rows; stopped")
        issues = list(self.db.scalars(select(KnownIssue).where(*own(KnownIssue))))
        for issue in issues:
            self.db.delete(issue)
        self.db.flush()
        for row in self.db.scalars(select(TechnicalEvidence).where(TechnicalEvidence.id.in_(te_ids))):
            self.db.delete(row)
        self.db.flush()
        self.counts["replaced_own_te"] = len(te_ids)
        self.counts["replaced_own_issues"] = len(issues)

    def reconcile_own_generations(self, previous: dict | None):
        """Correct generation years and rows that THIS pipeline wrote in an earlier load when the
        staging rules have changed since. Provenance is the previous load_report.json: only a
        year it reports as filled/created (and still holding that value) is changed, and only a
        generation it reports as created, absent from the staging and referenced by nothing, is
        removed. Pre-existing generation data is never touched."""
        from app.models.catalog import VehicleGeneration, VehicleVariant
        from app.models.evidence import KnownIssue, MaintenanceScheduleItem, TechnicalEvidence
        from sqlalchemy import func, select

        if not previous:
            return
        written = {}
        for entry in previous.get("generations", []):
            if entry.get("action") in ("filled", "created"):
                written[entry["code"]] = entry
        current = {g["code"]: g for g in self.s["generations"]}
        model_ids = [m.id for m in self.models.values()]
        for code, entry in written.items():
            row = self.db.scalar(
                select(VehicleGeneration).where(
                    VehicleGeneration.model_id.in_(model_ids),
                    VehicleGeneration.code == code,
                    VehicleGeneration.is_demo.is_(False),
                )
            )
            if row is None:
                continue
            gen = current.get(code)
            if gen is None:
                if entry.get("action") != "created":
                    continue
                refs = sum(
                    self.db.scalar(select(func.count()).select_from(t).where(t.generation_id == row.id))
                    for t in (TechnicalEvidence, KnownIssue, MaintenanceScheduleItem, VehicleVariant)
                )
                if refs == 0:
                    self.db.delete(row)
                    self.report["generations"].append(
                        {"code": code, "action": "removed (created by an earlier load; no longer in staging; unreferenced)"}
                    )
                else:
                    self.report["generations"].append(
                        {"code": code, "action": f"kept (no longer in staging, still referenced by {refs} rows)"}
                    )
                continue
            start = gen["start_year"] if gen.get("start_known", True) else None
            end = None if gen.get("open_ended") or not gen.get("end_known", True) else gen["end_year"]
            for field, new in (("start_year", start), ("end_year", end)):
                if field not in entry or entry[field] is None:
                    continue
                if getattr(row, field) == entry[field] and new != entry[field]:
                    setattr(row, field, new)
                    self.report["generations"].append(
                        {"code": code, "action": f"corrected {field} {entry[field]} -> {new} (written by an earlier load of this pipeline)"}
                    )
        self.db.flush()

    def stale_rows(self, prune: bool):
        """Rows written by THIS loader for this make/line that the current staging no longer
        contains (e.g. a narrowed applicability). Pre-existing data is never touched; stale rows
        are reported and deleted only with --prune-stale and only when nothing references them."""
        from app.models.evidence import KnownIssue, TechnicalEvidence
        from sqlalchemy import func, select

        # Only rows tagged with exactly this line. Rows without a line tag (written before the
        # tag existed) can belong to any line of the make and are never pruned: on 2026-10-02 a
        # NULL-tolerant filter let a Corolla run delete untagged Camry rows.
        rows = self.db.scalars(
            select(TechnicalEvidence).where(
                TechnicalEvidence.make_id == self.make.id,
                func.json_extract(TechnicalEvidence.conditions, "$.load") == LOAD_VERSION,
                func.json_extract(TechnicalEvidence.conditions, "$.line") == self.s["line"],
            )
        ).all()
        referenced = {
            i
            for issue in self.db.scalars(
                select(KnownIssue).where(KnownIssue.make_id == self.make.id)
            )
            for i in (issue.evidence_ids or [])
        }
        for row in rows:
            if row.natural_key in self.te_by_key:
                continue
            entry = {
                "id": row.id,
                "fact_key": row.fact_key,
                "value": row.value,
                "years": [row.year_from, row.year_to],
                "scope_level": str(row.scope_level),
                "referenced_by_issue": row.id in referenced,
            }
            if prune and row.id not in referenced:
                self.db.delete(row)
                entry["action"] = "deleted (superseded by the current staging scope)"
                self.counts["te_stale_deleted"] += 1
            else:
                entry["action"] = "kept"
            self.report["stale"].append(entry)
        self.db.flush()

    def compare_existing_catalog(self):
        """Read-only: log disagreements between new scoped facts and existing factory variant facts."""
        from app.models.catalog import VehicleGeneration, VehicleVariant
        from app.services.tech_units import convert
        from sqlalchemy import select

        pairs = {
            "wheelbase_in": ("wheelbase_mm", "in", "mm"),
            "length_in": ("length_mm", "in", "mm"),
            "width_in": ("width_mm", "in", "mm"),
            "height_in": ("height_mm", "in", "mm"),
            "fuel_tank_us_gal": ("fuel_tank_l", "gal", "L"),
        }
        variants = self.db.scalars(
            select(VehicleVariant)
            .join(VehicleGeneration, VehicleGeneration.id == VehicleVariant.generation_id)
            .where(
                VehicleGeneration.model_id == self.model.id,
                VehicleVariant.market == "US",
                VehicleVariant.catalog_key.like(f"{self.factory_prefix()}:%"),
                VehicleVariant.year_from >= 2014,
            )
        ).all()
        for v in variants:
            facts = (v.specifications or {}).get("catalog", {}).get("facts", {})
            for old_key, (new_key, unit_from, unit_to) in pairs.items():
                old = (facts.get(old_key) or {}).get("value")
                if old is None:
                    continue
                try:
                    converted = convert(old, unit_from, unit_to)
                except (ArithmeticError, ValueError):
                    # Read-only comparison: a non-numeric catalog value is reported, not parsed.
                    self.report["existing_vs_new"].append(
                        {"variant": v.catalog_key, "existing": f"{old_key}={old!r}",
                         "resolution": "existing value is not numeric; not compared"}
                    )
                    continue
                candidates = [
                    f
                    for f in self.s["facts"]
                    if f["key"] == new_key
                    and f["years"][0] <= v.year_from <= f["years"][1]
                    and f["display_level"] != "HIDDEN_CONFLICT"
                ]
                if candidates and not any(
                    abs(Decimal(str(f["value"])) - converted)
                    <= Decimal("6" if unit_to == "mm" else "0.6")
                    for f in candidates
                ):
                    self.report["existing_vs_new"].append(
                        {
                            "variant": v.catalog_key,
                            "existing": f"{old_key}={old}",
                            "new_values": sorted({f["value"] for f in candidates}),
                            "resolution": "existing catalog fact kept; new scoped fact stored separately",
                        }
                    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("make")
    parser.add_argument("line")
    parser.add_argument("--db", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prune-stale", action="store_true")
    parser.add_argument(
        "--replace-own",
        action="store_true",
        help="delete this pipeline's rows for the line, then load (implies --prune-stale)",
    )
    args = parser.parse_args(argv)
    import os

    os.environ["AUTOEXPERT_DATABASE_URL"] = f"sqlite:///{Path(args.db).resolve().as_posix()}"
    from app import models  # noqa: F401
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    staging_path = ROOT / "data_work" / args.make / "staging" / args.line / "staging.json"
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    if staging["errors"]:
        raise SystemExit(f"staging has {len(staging['errors'])} validation errors; rebuild first")
    engine = create_engine(os.environ["AUTOEXPERT_DATABASE_URL"])
    report = {
        "generations": [],
        "conflicts": [],
        "existing_vs_new": [],
        "stale": [],
        "dry_run": args.dry_run,
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "db": str(Path(args.db).resolve()),
    }
    report_path = (
        ROOT / "data_work" / args.make / "staging" / args.line / "load_report.json"
    )
    previous = (
        json.loads(report_path.read_text(encoding="utf-8"))
        if report_path.exists() and staging.get("build")
        else None
    )
    if args.replace_own:
        args.prune_stale = True
    with Session(engine) as db:
        loader = Loader(db, staging, staging["line"], report)
        if args.replace_own:
            loader.delete_own_line_rows()
        if args.prune_stale:
            loader.reconcile_own_generations(previous)
        loader.load_sources()
        loader.load_generations()
        loader.load_facts()
        loader.load_configurations()
        loader.load_recalls()
        loader.load_tsbs(staging["generations"])
        loader.load_symptom_patterns()
        loader.load_issues()
        loader.stale_rows(args.prune_stale)
        if args.prune_stale:
            loader.reconcile_own_generations(previous)  # removes generations emptied by the prune
        loader.compare_existing_catalog()
        report["counts"] = dict(loader.counts)
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
    report["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    out = (
        ROOT
        / "data_work"
        / args.make
        / "staging"
        / args.line
        / (
            "load_report_dry_run.json"
            if args.dry_run
            else "load_report.json"
            if Path(args.db).resolve() == (ROOT / "autoexpert.db").resolve()
            # rehearsals on a copy must not replace the live load's provenance report
            else "load_report_rehearsal.json"
        )
    )
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "counts": report["counts"],
                "generations": report["generations"],
                "conflicts": len(report["conflicts"]),
                "existing_vs_new": len(report["existing_vs_new"]),
                "stale": report["stale"],
            },
            ensure_ascii=False,
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
