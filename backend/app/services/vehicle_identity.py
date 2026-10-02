# ruff: noqa: E501
"""Variant boundaries and identity readiness, independent of report completeness.

No inference from 'gasoline' to ICE: HEVs also burn gasoline. Source assertions
remain auditable even when a conflicting assertion cannot be used in a report.
"""

from __future__ import annotations

import re

VERSION = "0.7.0"
POWERTRAIN_TYPES = {"ICE", "HEV", "PHEV", "BEV", "MHEV", "UNKNOWN"}
POWER_FIELDS = (
    "engine_power_hp",
    "engine_power_kw",
    "motor_power_hp",
    "motor_power_kw",
    "system_combined_power_hp",
    "system_combined_power_kw",
    "battery_capacity_kwh",
    "battery_type",
    "hybrid_transmission_type",
)
CRITICAL = {"powertrain_type", "engine", "transmission", "drivetrain", "fuel"}


def powertrain_type(record: dict) -> str:
    text = str(record.get("powertrain_type") or record.get("electrification_level") or "").upper()
    if text in POWERTRAIN_TYPES:
        return text
    if "PHEV" in text or "PLUG-IN" in text or "PLUG IN" in text:
        return "PHEV"
    if "MHEV" in text or "MILD" in text:
        return "MHEV"
    if "HEV" in text or "HYBRID" in text:
        return "HEV"
    if "BEV" in text or "BATTERY ELECTRIC" in text:
        return "BEV"
    if "NOT ELECTRIFIED" in text or "NOT APPLICABLE" in text:
        return "ICE"
    # Secondary electric fuel confirms electrification, not HEV vs PHEV.
    return "UNKNOWN"


def epa_powertrain(row: dict) -> str:
    text = str(row.get("atvType") or "").casefold()
    if "plug" in text or str(row.get("phevBlended")).lower() == "true":
        return "PHEV"
    if "hybrid" in text:
        return "HEV"
    if text in {"ev", "electric vehicle"} or row.get("fuelType1") == "Electricity":
        return "BEV"
    if row.get("fuelType2") == "Electricity":
        return "PHEV"
    if row.get("fuelType1") in {
        "Regular Gasoline",
        "Premium Gasoline",
        "Midgrade Gasoline",
        "Diesel",
    }:
        return "ICE"
    return "UNKNOWN"


def dimension(field: str, value: object) -> str:
    text = str(value or "").strip().casefold()
    if field in {"powertrain", "powertrain_type"}:
        return {"conventional": "ice", "hybrid": "hev"}.get(text, text)
    if field == "drivetrain":
        for names, result in (
            (("front-wheel", "front wheel", "fwd"), "fwd"),
            (("rear-wheel", "rear wheel", "rwd"), "rwd"),
            (("all-wheel", "all wheel", "awd"), "awd"),
        ):
            if any(n in text for n in names):
                return result
        if "4wd/4-wheel drive/4x4" in text:
            return "all_driven_wheels"  # vPIC's broad category includes AWD.
        if text in {"4wd", "4-wheel drive"}:
            return "4wd"
    if field == "fuel":
        if "gasoline" in text or text == "regular":
            return "gasoline"
        if text in {"electric", "electricity"}:
            return "electric"
    if field == "transmission":
        if "cvt" in text or "variable" in text or "(av" in text:
            return "cvt"
        if "automatic" in text:
            return "automatic"
        if "manual" in text:
            return "manual"
    return re.sub(r"[^a-z0-9.]", "", text)


def dimensions_equal(field: str, a: object, b: object) -> bool:
    left, right = dimension(field, a), dimension(field, b)
    if field == "drivetrain" and "all_driven_wheels" in {left, right}:
        return left in {"awd", "4wd", "all_driven_wheels"} and right in {
            "awd",
            "4wd",
            "all_driven_wheels",
        }
    return left == right


def identity_target(request, identity: dict, epa: dict | None = None) -> dict:
    ptype = powertrain_type(identity)
    if ptype == "UNKNOWN" and epa and not identity.get("fuel_type_secondary"):
        ptype = epa_powertrain(epa)
    return {
        "vin": request.vin,
        "make": request.make,
        "model": request.model,
        "year": request.year,
        "market": request.market,
        "generation": None,
        "trim": identity.get("trim") or identity.get("series"),
        "body": identity.get("body_class"),
        "displacement": identity.get("displacement_l") or (epa or {}).get("displ"),
        "cylinders": identity.get("engine_cylinders") or (epa or {}).get("cylinders"),
        "engine": identity.get("engine_model"),
        "engine_code": identity.get("engine_model"),
        "powertrain_type": ptype,
        "fuel": identity.get("fuel_type_primary") or (epa or {}).get("fuelType1"),
        "transmission": identity.get("transmission_style") or (epa or {}).get("trany"),
        "drivetrain": identity.get("drive_type") or (epa or {}).get("drive"),
    }


def applicability_class(scope: dict, *, exact: bool = False) -> str:
    if exact and scope.get("vin"):
        return "EXACT_VIN"
    if scope.get("powertrain_type") not in (None, "", "UNKNOWN") and (
        scope.get("displacement")
        or scope.get("engine_code")
        or scope.get("powertrain_type") == "BEV"
    ):
        return "EXACT_VARIANT"
    if scope.get("generation"):
        return "GENERATION"
    if scope.get("year") or scope.get("years"):
        return "MODEL_YEAR"
    if scope.get("model"):
        return "MODEL_WIDE"
    return "UNKNOWN"


def narrative_scope(text: str, base: dict) -> dict:
    """Only explicit, unambiguous constraints; broad narratives stay model-wide."""
    scope = dict(base)
    text = text.casefold()
    liters = set(re.findall(r"\b(\d\.\d)\s*(?:l(?:iter|itre)?s?)\b", text))
    if len(liters) == 1:
        scope["displacement"] = float(next(iter(liters)))
    phev = bool(re.search(r"\bphev\b|plug[- ]in (?:hybrid|hev)", text))
    hev = bool(re.search(r"(?<!in )\bhev\b|(?<!in )\bhybrid\b", text))
    ice = bool(re.search(r"non[- ]hybrid|gasoline[- ]only|\bice\b", text))
    mixed_base_model = bool(
        base.get("model")
        and re.search(re.escape(str(base["model"]).casefold()) + r"\s*(?:,|and\b|vehicles\b)", text)
    )
    if phev and not hev and not mixed_base_model:
        scope["powertrain_type"] = "PHEV"
    elif ice and not phev:
        scope["powertrain_type"] = "ICE"
    elif hev and not phev and not ice and not mixed_base_model:
        scope["powertrain_type"] = "HEV"
    drives = {x.upper() for x in re.findall(r"\b(fwd|awd|rwd|4wd)\b", text)}
    if len(drives) == 1:
        scope["drivetrain"] = drives.pop()
    return scope


def filter_results(results: list, target: dict) -> tuple[list, list[dict]]:
    from app.services.knowledge_coverage import applicability

    filtered, rejected = [], []
    base = {k: target.get(k) for k in ("make", "model", "year", "market")}
    for result in results:
        rows = []
        for row in result.records:
            if result.capability in {"vehicle_identity", "vehicle_variants", "fuel_economy"}:
                rows.append(row)
                continue
            text = " ".join(
                str(row.get(k) or "") for k in ("summary", "normalized_summary", "text")
            )
            scope = narrative_scope(text, row.get("applicability") or base)
            match = applicability(target, scope)
            classification = row.get("applicability_class") or applicability_class(scope)
            if result.capability in {"recalls", "owner_complaints", "manufacturer_communications"}:
                classification = "MODEL_YEAR"
            if match == "MISMATCH":
                rejected.append(
                    {
                        "provider_id": result.provider_id,
                        "capability": result.capability,
                        "record_id": row.get("campaign_number")
                        or row.get("odi_number")
                        or row.get("document_id")
                        or row.get("material_id")
                        or f"{row.get('topic')}.{row.get('subtopic')}",
                        "reason": "INCOMPATIBLE_VARIANT",
                        "applicability": scope,
                        "applicability_class": classification,
                        "source_url": result.source_url,
                    }
                )
                continue
            rows.append({**row, "applicability": scope, "applicability_class": classification})
        updates = {"records": rows}
        if len(rows) != len(result.records):
            updates["raw_payload"] = {
                "variant_rejected_count": len(result.records) - len(rows),
                "original": result.raw_payload,
            }
        filtered.append(result.model_copy(update=updates))
    return filtered, rejected


def integrity_from_findings(target: dict, findings: list, conflicts: list) -> dict:
    confirmed = {
        (f["topic"], f["subtopic"]): f
        for f in findings
        if f["status"] == "CONFIRMED" and f.get("value") is not None
    }
    mapping = {
        "powertrain_type": ("identity", "powertrain_type"),
        "fuel": ("engine", "fuel"),
        "engine": ("engine", "displacement"),
        "transmission": ("transmission", "type"),
        "drivetrain": ("identity", "drivetrain"),
    }
    fields = {
        key: {
            "value": target.get(key),
            "status": "UNRESOLVED",
            "source_ids": [],
            "evidence_ids": [],
        }
        for key in (
            "vin",
            "make",
            "model",
            "year",
            "market",
            "generation",
            "trim",
            "body",
            *CRITICAL,
            *POWER_FIELDS,
        )
    }
    for key in fields:
        pair = mapping.get(key, ("engine", key) if key in POWER_FIELDS else ("identity", key))
        fact = confirmed.get(pair)
        if fact:
            fields[key] = {
                k: fact.get(k)
                for k in ("value", "status", "source_ids", "evidence_ids", "applicability_class")
            }
    missing = [
        key
        for key in sorted(CRITICAL)
        if fields[key]["status"] != "CONFIRMED" or fields[key]["value"] in (None, "", "UNKNOWN")
    ]
    if target.get("powertrain_type") == "BEV":
        missing = [key for key in missing if key != "engine"]
    if ("transmission", "gears") not in confirmed and confirmed.get(
        ("transmission", "type"), {}
    ).get("value") not in {"CVT", "DIRECT_DRIVE"}:
        missing = sorted(set([*missing, "transmission"]))
    critical_conflicts = [
        c
        for c in conflicts
        if c.get("resolution") == "UNRESOLVED"
        and c["topic"] in {"identity", "engine", "transmission"}
    ]
    state = (
        "VARIANT_CONFLICT"
        if critical_conflicts
        else "IDENTITY_INCOMPLETE"
        if missing
        else "RESOLVED"
    )
    return {
        "version": VERSION,
        "state": state,
        "fields": fields,
        "missing_fields": missing,
        "critical_conflicts": critical_conflicts,
        "conflicts": conflicts,
    }


def scope_label(classification: str, language: str) -> str:
    labels = {
        "EXACT_VIN": ("Точный VIN", "Dəqiq VIN", "Exact VIN"),
        "EXACT_VARIANT": ("Точная модификация", "Dəqiq modifikasiya", "Exact modification"),
        "GENERATION": ("Поколение модели", "Model nəsli", "Model generation"),
        "MODEL_YEAR": (
            "Модель и год; применимость к VIN не подтверждена",
            "Model və il; VIN üzrə uyğunluq təsdiqlənməyib",
            "Model year; VIN applicability unconfirmed",
        ),
        "MODEL_WIDE": ("Модель в целом", "Ümumi model", "Model-wide"),
        "UNKNOWN": (
            "Применимость не подтверждена",
            "Uyğunluq təsdiqlənməyib",
            "Applicability unconfirmed",
        ),
    }
    return labels.get(classification, labels["UNKNOWN"])[{"ru": 0, "az": 1, "en": 2}[language]]


def source_scopes(profile, snapshots: list[dict], language: str) -> list[dict]:
    by_source = {}
    for evidence in profile.evidence:
        if evidence.conditions.get("excluded_from_synthesis"):
            continue
        by_source.setdefault(evidence.source_id, set()).add(
            evidence.conditions.get("applicability_class", "UNKNOWN")
        )
    return [
        {
            **s,
            "applicability_summary": "; ".join(
                scope_label(c, language) for c in sorted(by_source.get(s["id"], {"UNKNOWN"}))
            ),
        }
        for s in snapshots
    ]


def identity_chat_sections(profile, language: str) -> list:
    from app.schemas.vin import DossierClaim, DossierSection
    from app.services.paid_report import LABELS, VALUES, tr

    gate = profile.dossier_seed.get("identity_integrity", {})
    fields = gate.get("fields", {})

    def claim(text, field=None, status=None):
        item = fields.get(field, {})
        return DossierClaim(
            text=text,
            status=status
            or item.get("status", "INSUFFICIENT_DATA").replace("UNRESOLVED", "INSUFFICIENT_DATA"),
            evidence_ids=item.get("evidence_ids", []),
            source_ids=item.get("source_ids", []),
        )

    ptype = fields.get("powertrain_type", {}).get("value") or "UNKNOWN"
    identity_text = (
        tr(language, *VALUES[ptype])
        if ptype in VALUES
        else tr(
            language,
            "Тип силовой установки не подтверждён.",
            "Güc qurğusunun növü təsdiqlənməyib.",
            "Powertrain type is unconfirmed.",
        )
    )
    identities = [claim(identity_text, "powertrain_type")]
    if gate.get("state") != "RESOLVED":
        identities.append(
            claim(
                tr(
                    language,
                    "Точная модификация силовой установки не подтверждена: есть неполные или противоречивые данные.",
                    "Güc qurğusunun dəqiq modifikasiyası təsdiqlənməyib: natamam və ya ziddiyyətli məlumat var.",
                    "The exact powertrain configuration is not confirmed: some data is incomplete or conflicting.",
                )
            )
        )
    powers = []
    for key in ("engine_power_hp", "system_combined_power_hp"):
        value = (
            fields.get(key, {}).get("value")
            if fields.get(key, {}).get("status") == "CONFIRMED"
            else None
        )
        text = (
            str(value)
            if value is not None
            else tr(language, "не подтверждена", "təsdiqlənməyib", "not confirmed")
        )
        powers.append(claim(tr(language, *LABELS[key]) + ": " + text + ".", key))
    powers.append(
        claim(
            tr(
                language,
                "Это разные величины. Мощность бензинового двигателя не является суммарной мощностью гибридной системы; мощности двигателя и электромотора нельзя просто складывать.",
                "Bunlar fərqli göstəricilərdir. Benzin mühərrikinin gücü hibrid sistemin ümumi gücü deyil; mühərrik gücləri sadəcə toplanmır.",
                "These are different quantities. Combustion engine power is not combined hybrid system power; engine and motor ratings must not simply be added.",
            ),
            "powertrain_type",
        )
    )
    model_evidence = [
        e
        for e in profile.evidence
        if e.conditions.get("applicability_class") in {"MODEL_YEAR", "MODEL_WIDE", "GENERATION"}
        and not e.conditions.get("excluded_from_synthesis")
    ]

    def scope_claim(text):
        return DossierClaim(
            text=text,
            status="ESTIMATE" if model_evidence else "INSUFFICIENT_DATA",
            evidence_ids=[e.id for e in model_evidence],
            source_ids=sorted({e.source_id for e in model_evidence}),
        )

    applies = scope_claim(
        tr(
            language,
            "Для записи уровня модели или года применимость именно к вашей версии не подтверждена. Совпадение модели не доказывает дефект вашего VIN. Точный VIN и точная модификация обозначаются отдельно; явно несовместимые записи исключены.",
            "Model və ya il səviyyəli qeydin məhz sizin versiyaya uyğunluğu təsdiqlənməyib. Model uyğunluğu VIN-də nasazlığı sübut etmir; uyğunsuz qeydlər çıxarılıb.",
            "A model-year record is not confirmed for your exact version. A model match does not establish a defect in your VIN. Exact VIN and modification evidence are distinguished; incompatible records are excluded.",
        )
    )
    recall = scope_claim(
        tr(
            language,
            "Отзывная кампания показана для части автомобилей этого модельного года. Это повод проверить включение VIN и выполнение ремонта у производителя; участие и неисправность вашего автомобиля не подтверждены.",
            "Geri çağırma bu model ilinin bəzi avtomobilləri üçün göstərilir. VIN-in daxil olmasını və təmirin icrasını istehsalçı ilə yoxlayın; sizin avtomobildə nasazlıq təsdiqlənməyib.",
            "The recall concerns some vehicles of this model year. Verify VIN inclusion and repair completion with the manufacturer; this does not confirm a defect in your car.",
        )
    )
    return [
        DossierSection(key=k, title=k, summary="", claims=c)
        for k, c in (
            ("variant_identity", identities),
            ("variant_power", powers),
            ("variant_applicability", [applies]),
            ("variant_recall", [recall]),
        )
    ]
