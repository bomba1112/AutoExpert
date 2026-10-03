"""Deterministic buyer queries over published catalogue revisions; no provider calls."""

# ruff: noqa: E501
from __future__ import annotations

import hashlib
import re
from datetime import timedelta
from decimal import Decimal
from difflib import SequenceMatcher

from sqlalchemy import select

from app.core.config import get_settings
from app.models.catalog import VehicleVariant
from app.models.enums import DataOrigin, SourceUsageStatus
from app.models.evidence import MarketListing, SourceRecord
from app.models.knowledge_ops import SourceRegistry, VehicleAsset
from app.schemas.knowledge import BuyerFilters, CostScenario
from app.schemas.paid_report import (
    PaidReportReadiness,
    PaidReportSection,
    PaidVehicleReport,
    ReportParagraph,
    ReportRow,
)
from app.services.buyer_experience import persist_report
from app.services.catalog_scope import catalog_in_active_scope, scope_policy
from app.services.catalog_verification import (
    base_catalog_counts,
    base_catalog_ready,
    catalog_excluded,
    documentary_sources_allowed,
    dossier_full,
    identity_verified,
    source_confirmed_core_ready,
    us_catalog_ready,
)
from app.services.commercial_fact_overlay import (
    claims_for_variants,
    commercial_overlay_core_ready,
    project_commercial_catalog,
    project_existing_commercial_catalog,
)
from app.services.knowledge_import import catalog_identity_hash, normalized
from app.services.knowledge_registry import utcnow

RANK_VERSION = "buyer-evidenced-fit-2.0"
LABELS = {
    "powertrain": ("Силовая установка", "Güc qurğusu"),
    "fuel": ("Топливо", "Yanacaq"),
    "fuel_grade": ("Топливо по источнику", "Mənbədəki yanacaq"),
    "engine_displacement": ("Объём двигателя", "Mühərrikin həcmi"),
    "cylinders": ("Цилиндры", "Silindrlər"),
    "engine_description": ("Двигатель по источнику", "Mənbədəki mühərrik"),
    "aspiration": ("Наддув", "Hava doldurma"),
    "transmission_description": ("Коробка по источнику", "Mənbədəki sürətlər qutusu"),
    "transmission_family": ("Тип коробки", "Qutu növü"),
    "gears": ("Число передач", "Ötürmə sayı"),
    "drivetrain": ("Привод", "Ötürücü"),
    "size_class": ("Размерный класс источника", "Mənbənin ölçü sinfi"),
    "body": ("Кузов", "Kuzov"),
    "fuel_combined": ("Расход · цикл EPA", "Sərfiyyat · EPA dövrü"),
    "electricity_combined": ("Электроэнергия · цикл EPA", "Elektrik sərfiyyatı · EPA dövrü"),
    "motor_description": ("Электромотор по источнику", "Mənbədəki elektrik mühərriki"),
    "charge_ac_240v_hours": ("Зарядка AC 240 V", "AC 240 V şarj"),
    "epa_range_miles": ("Запас хода EPA", "EPA gediş ehtiyatı"),
    "hatch_cargo": ("Багажник хетчбэка", "Hetçbek baqajı"),
    "four_door_cargo": ("Багажник · 4 двери", "Baqaj · 4 qapı"),
    "two_door_cargo": ("Багажник · 2 двери", "Baqaj · 2 qapı"),
    "seats": ("Места", "Oturacaq sayı"),
    "ground_clearance": ("Клиренс", "Klirens"),
    "trim": ("Комплектация", "Komplektasiya"),
    "power_kw": ("Мощность", "Güc"),
}
VALUE_LABELS = {
    "SEDAN": ("Седан", "Sedan"),
    "CROSSOVER": ("Кроссовер", "Krossover"),
    "HATCHBACK": ("Хетчбэк", "Hetçbek"),
    "COUPE": ("Купе", "Kupe"),
    "AT": ("Обычный автомат AT", "Klassik avtomat AT"),
    "CVT": ("Вариатор CVT / IVT", "Variator CVT / IVT"),
    "DCT": ("Робот DCT / DSG", "Robot DCT / DSG"),
    "Regular Gasoline": (
        "Бензин Regular · классификация источника",
        "Regular benzin · mənbənin təsnifatı",
    ),
    "Premium Gasoline": (
        "Бензин Premium · классификация источника",
        "Premium benzin · mənbənin təsnifatı",
    ),
    "Midgrade Gasoline": (
        "Бензин Midgrade · классификация источника",
        "Midgrade benzin · mənbənin təsnifatı",
    ),
    "Diesel": ("Дизель", "Dizel"),
    "Electricity": ("Электроэнергия", "Elektrik"),
    "Hydrogen": ("Водород", "Hidrogen"),
    "Compact Cars": ("Компактный класс EPA", "EPA kompakt sinfi"),
    "Compact": ("Компактный класс NRCan", "NRCan kompakt sinfi"),
    "Mid-size": ("Средний класс NRCan", "NRCan orta sinfi"),
    "Full-size": ("Большой класс NRCan", "NRCan böyük sinfi"),
    "Subcompact": ("Малый класс NRCan", "NRCan kiçik sinfi"),
    "Minicompact": ("Мини-компактный класс NRCan", "NRCan mini-kompakt sinfi"),
    "Two-seater": ("Двухместный класс NRCan", "NRCan iki yerli sinfi"),
    "Sport utility vehicle: Small": ("Малый SUV · NRCan", "Kiçik SUV · NRCan"),
    "Sport utility vehicle: Standard": ("Стандартный SUV · NRCan", "Standart SUV · NRCan"),
    "Station wagon: Small": ("Малый универсал · NRCan", "Kiçik universal · NRCan"),
    "Station wagon: Mid-size": ("Средний универсал · NRCan", "Orta universal · NRCan"),
    "Pickup truck: Small": ("Малый пикап · NRCan", "Kiçik pikap · NRCan"),
    "Pickup truck: Standard": ("Стандартный пикап · NRCan", "Standart pikap · NRCan"),
    "Minivan": ("Минивэн · NRCan", "Miniven · NRCan"),
    "Midsize Cars": ("Средний класс EPA", "EPA orta sinfi"),
    "Large Cars": ("Большой класс EPA", "EPA böyük sinfi"),
    "Subcompact Cars": ("Малый класс EPA", "EPA kiçik sinfi"),
    "Minicompact Cars": ("Мини-компактный класс EPA", "EPA mini-kompakt sinfi"),
    "Two Seaters": ("Двухместный класс EPA", "EPA iki yerli sinfi"),
    "COMBUSTION_UNSPECIFIED": (
        "ДВС/гибрид · архитектура не уточнена",
        "DYM/hibrid · quruluş dəqiqləşdirilməyib",
    ),
    "MHEV": ("Мягкий гибрид", "Yumşaq hibrid"),
    "EREV": (
        "Электропривод с увеличителем запаса хода",
        "Gediş ehtiyatı artırıcılı elektrik ötürücüsü",
    ),
    "FCEV": ("Водородные топливные элементы", "Hidrogen yanacaq elementləri"),
    "NATURALLY_ASPIRATED": ("Без наддува", "Turbosuz"),
    "SINGLE_SPEED": ("Одноступенчатый редуктор", "Birpilləli reduktor"),
    "ECVT": ("Электромеханическая e-CVT", "Elektromexaniki e-CVT"),
    "CONFIRMED": ("Подтверждено", "Təsdiqlənib"),
    "ESTIMATE": ("Оценка", "Təxmini"),
    "NEEDS_INSPECTION": ("Нужен осмотр", "Baxış tələb olunur"),
    "INSUFFICIENT_DATA": ("Недостаточно данных", "Məlumat yetərli deyil"),
    "BEV": ("Электромобиль", "Elektromobil"),
    "ICE": ("ДВС", "Daxiliyanma mühərriki"),
    "HEV": ("Гибрид без зарядки", "Şarjsız hibrid"),
    "PHEV": ("Заряжаемый гибрид", "Şarj olunan hibrid"),
    "GASOLINE": ("Бензин", "Benzin"),
    "DIESEL": ("Дизель", "Dizel"),
    "ELECTRICITY": ("Электроэнергия", "Elektrik"),
    "FWD": ("Передний", "Ön"),
    "RWD": ("Задний", "Arxa"),
    "AWD": ("Полный AWD", "Tam AWD"),
    "AUTOMATIC_UNSPECIFIED": (
        "Автоматическая · конструкция не уточнена",
        "Avtomatik · quruluş dəqiqləşdirilməyib",
    ),
    "VARIABLE_UNSPECIFIED": (
        "Бесступенчатая · конструкция не уточнена",
        "Pilləsiz · quruluş dəqiqləşdirilməyib",
    ),
    "AMT_UNSPECIFIED": (
        "Автоматизированная · сцепление не уточнено",
        "Avtomatlaşdırılmış · mufta dəqiqləşdirilməyib",
    ),
    "MANUAL": ("Механика", "Mexaniki"),
    "TURBO": ("Турбо", "Turbo"),
    "SUPERCHARGED": ("Механический нагнетатель", "Mexaniki kompressor"),
    "SUV": ("SUV", "SUV"),
    "WAGON": ("Универсал", "Universal"),
    "PICKUP": ("Пикап", "Pikap"),
    "MINIVAN": ("Минивэн", "Miniven"),
}


def tr(language, ru, az):
    return az if language == "az" else ru


def comparison_conclusion(language):
    return tr(
        language,
        "Выбор зависит от ваших условий. Данных о надёжности и локальных расходах пока недостаточно, чтобы назвать общего победителя.",
        "Seçim şəraitinizdən asılıdır. Etibarlılıq və yerli xərclər barədə məlumat ümumi qalibi müəyyən etmək üçün yetərli deyil.",
    )


def fact_value(catalog, key):
    f = catalog.get("facts", {}).get(key, {})
    return f.get("value") if f.get("status") == "CONFIRMED" else None


def _consumer_generation(catalog):
    """An internal unresolved-generation bucket is not a vehicle generation."""
    for value in (catalog.get("generation_code"), catalog.get("generation")):
        if normalized(str(value or "")) not in {
            "",
            "unknown",
            "unresolved",
            "unverified",
            "generation unverified",
        }:
            return value
    return None


_AUTOMATIC_FAMILIES = frozenset(
    {
        "AT", "CVT", "ECVT", "DCT", "AMT",
        "AUTOMATIC_UNSPECIFIED", "VARIABLE_UNSPECIFIED", "AMT_UNSPECIFIED",
    }
)


def _transmission_fit(actual, requested):
    """Return MATCH, UNKNOWN or CONFLICT without guessing EPA gearbox construction."""
    if actual is None:
        return "UNKNOWN"
    if requested == "AUTOMATIC_UNSPECIFIED":
        return "MATCH" if actual in _AUTOMATIC_FAMILIES else "CONFLICT"
    if actual == requested:
        return "MATCH"
    if actual == "AUTOMATIC_UNSPECIFIED" and requested in _AUTOMATIC_FAMILIES:
        return "UNKNOWN"
    if actual == "VARIABLE_UNSPECIFIED" and requested in {"CVT", "ECVT"}:
        return "UNKNOWN"
    if actual == "AMT_UNSPECIFIED" and requested in {"AMT", "DCT"}:
        return "UNKNOWN"
    return "CONFLICT"


def _ready_for_scope(catalog, scope):
    return (
        (source_confirmed_core_ready(catalog) or commercial_overlay_core_ready(catalog))
        if scope == "US_BASE_2000"
        else base_catalog_ready(catalog)
    )


def fact_display(fact, language):
    raw = str(fact["value"])
    value = fact.get("labels", {}).get(language) or tr(language, *VALUE_LABELS.get(raw, (raw, raw)))
    if value == raw:
        if raw.startswith("Automatic"):
            value = raw.replace("Automatic", tr(language, "Автоматическая", "Avtomatik"), 1)
        elif raw.startswith("Manual"):
            value = raw.replace("Manual", tr(language, "Механика", "Mexaniki"), 1)
        value = re.sub(r"(\d+)-spd", lambda m: m[1] + tr(language, " передач", " pillə"), value)
        for source, ru, az in [
            ("Standard Sport Utility Vehicle", "Стандартный SUV", "Standart SUV"),
            ("Small Sport Utility Vehicle", "Компактный SUV", "Kompakt SUV"),
            ("Sport Utility Vehicle", "SUV", "SUV"),
            ("Small Station Wagons", "Малый универсал", "Kiçik universal"),
            ("Midsize Station Wagons", "Средний универсал", "Orta universal"),
            ("Standard Pickup Trucks", "Стандартный пикап", "Standart pikap"),
            ("Small Pickup Trucks", "Малый пикап", "Kiçik pikap"),
            ("Minivans", "Минивэн", "Miniven"),
            ("Vans, Cargo Type", "Грузовой фургон", "Yük furqonu"),
            ("Vans, Passenger Type", "Пассажирский фургон", "Sərnişin furqonu"),
            ("Special Purpose Vehicles", "Специальный класс EPA", "EPA xüsusi sinfi"),
        ]:
            value = value.replace(source, tr(language, ru, az))
    if fact.get("status") != "CONFIRMED":
        status = fact.get("status", "INSUFFICIENT_DATA")
        value += " · " + tr(language, *VALUE_LABELS.get(status, (status, status)))
    return value


def configuration_display(c, language):
    if base_catalog_ready(c):
        # Render the selected complete configuration, not its source group of drives.
        return " · ".join(
            fact_display(c["facts"][key], language)
            for key in ("engine_description", "transmission_description", "drivetrain")
        )
    if source_confirmed_core_ready(c) or commercial_overlay_core_ready(c):
        # EPA's raw configuration label can contain editorial/unverified names.
        # Show only source-supported mechanical facts, leaving missing optional facts out.
        engine = c.get("facts", {}).get("engine_description")
        displacement = c.get("facts", {}).get("engine_displacement")
        powertrain = c.get("facts", {}).get("powertrain")
        parts = []
        if engine and engine.get("status") == "CONFIRMED" and engine.get("value"):
            parts.append(fact_display(engine, language))
        elif displacement and displacement.get("status") == "CONFIRMED" and displacement.get("value"):
            parts.append(f"{fact_display(displacement, language)} {displacement.get('unit') or 'L'}")
        elif powertrain and powertrain.get("status") == "CONFIRMED":
            parts.append(fact_display(powertrain, language))
        parts.extend(
            fact_display(c["facts"][key], language)
            for key in ("transmission_description", "drivetrain")
        )
        return " · ".join(parts)
    if c.get("source_registry_id") != "epa":
        return c["configuration"]
    parts = [c["configuration"].split(" · ")[0]]
    for key in ("engine_displacement", "transmission_description", "drivetrain"):
        fact = c["facts"].get(key)
        if fact:
            parts.append(
                fact_display(fact, language) + (" " + fact["unit"] if fact.get("unit") else "")
            )
    return " · ".join(parts)


def records(db, *, active_scope=True, production_safe=False, variant_ids=None):
    """variant_ids: only these variants (the preview layer); None keeps every published one."""
    sources = {s.id: s for s in db.scalars(select(SourceRegistry))}
    rules = scope_policy() if active_scope else None
    result = []
    variants = list(db.scalars(
        select(VehicleVariant).where(
            VehicleVariant.published_revision_id.is_not(None), VehicleVariant.is_demo.is_(False),
            *([VehicleVariant.id.in_(list(variant_ids))] if variant_ids is not None else []),
        )
    ))
    # Listing intake must use the same rights-cleared consumer projection even
    # when the local preview itself is running in development mode.
    production = get_settings().environment == "production" or production_safe
    claims = claims_for_variants(db, [v.id for v in variants]) if production else {}
    for v in variants:
        c = v.specifications.get("catalog", {})
        if active_scope and not catalog_in_active_scope(c, rules):
            continue
        if catalog_excluded(c):
            continue
        source = sources.get(c.get("source_registry_id"))
        if production:
            if source and source.config.get("commercial_reuse") and c.get("publication_scope") == "COMMERCIAL":
                c = project_existing_commercial_catalog(c, sources)
            else:
                # Candidate source rights/state do not flow into independent
                # claims. A research registry may be paused without hiding
                # separately corroborated values.
                c = project_commercial_catalog(c, claims.get(v.id, []), sources)
            if c is None:
                continue
        else:
            if not source or source.state not in {"APPROVED", "LOCAL_RESEARCH"}:
                continue
            if not documentary_sources_allowed(db, c):
                continue
        result.append((v, c))
    if production:
        # The same approved facts can corroborate a factory row and its EPA
        # candidate. Prefer the factory publication rather than showing twins.
        def duplicate_key(c):
            if not c.get("commercial_fact_overlay"):
                return None
            facts = c.get("facts") or {}
            def value(name):
                return normalized(str((facts.get(name) or {}).get("value") or ""))
            return (
                normalized(c["make"]), normalized(c["model"]), c["model_year"],
                value("powertrain"), value("engine_displacement"),
                value("engine_description") or value("engine_code"),
                value("transmission_description"), value("drivetrain"),
            )
        best = {}
        for v, c in result:
            key = duplicate_key(c)
            if key is None:
                best[("existing", v.id)] = (v, c)
            else:
                current = best.get(key)
                original = (v.specifications.get("catalog") or {}).get("source_registry_id", "")
                priority = (original == "epa", v.id)
                if current is None or priority < current[0]:
                    best[key] = (priority, (v, c))
        result = [entry if key[0] == "existing" else entry[1] for key, entry in best.items()]
    return result


def version(records_):
    return hashlib.sha256(
        "|".join(sorted(c.get("revision_id") or v.published_revision_id for v, c in records_)).encode()
    ).hexdigest()[:16]


def asset_for(db, variant_id, assets=None):
    if assets is None:
        assets = db.scalars(select(VehicleAsset).where(VehicleAsset.state == "APPROVED"))
    for asset in assets:
        if variant_id in asset.applicability.get("variant_ids", []) and asset.rights.get(
            "commercial_reuse"
        ):
            return {
                "id": asset.id,
                "url": f"/api/v1/knowledge/assets/{asset.id}/card",
                "state": "APPROVED",
                "version": asset.version,
                "attribution": asset.rights.get("reference"),
                "source_url": asset.provenance.get("source_url"),
            }
    return {"state": "IMAGE_QA", "url": None}


def card(db, variant, c, language="ru", assets=None):
    generation = c.get("generation")
    generation_code = c.get("generation_code")
    unknown_generation = {"", "unknown", "unresolved", "unverified", "generation unverified"}
    result = {
        "id": variant.id,
        "make": c["make"],
        "model": c["model"],
        "year": c["model_year"],
        "configuration": configuration_display(c, language),
        "source_configuration": c["configuration"],
        "market": c["original_market"],
        "generation": generation
        if normalized(str(generation or "")) not in unknown_generation else None,
        "generation_code": generation_code
        if normalized(str(generation_code or "")) not in unknown_generation else None,
        "base_catalog_ready": base_catalog_ready(c),
        "us_catalog_ready": us_catalog_ready(c),
        "source_confirmed_core": source_confirmed_core_ready(c) or commercial_overlay_core_ready(c),
        "verified_scoped": identity_verified(c),
        "facelift": c.get("facelift"),
        "revision_id": c["revision_id"],
        "scope": c["publication_scope"],
        "attribution": "Contains information licensed under the Open Government Licence – Canada."
        if c.get("source_registry_id") == "nrcan"
        else None,
        "test_cycle": c["facts"].get("source_cycle", {}).get("value")
        or c.get("source_registry_id"),
        "facts": {
            k: {
                **f,
                "label": f.get("titles", {}).get(language) or tr(language, *LABELS.get(k, (k, k))),
                "display": fact_display(f, language),
            }
            for k, f in c["facts"].items()
            if f.get("status") == "CONFIRMED"
            and f.get("value") not in (None, "", "UNKNOWN", "UNRESOLVED")
        },
        "asset": {"state": "IMAGE_QA", "url": None}
        if c.get("commercial_fact_overlay") else asset_for(db, variant.id, assets),
    }
    if c.get("preview_only"):  # preview layer (catalog_preview): production cards stay as they are
        result["preview"] = True
        result["us_configuration_key"] = c.get("us_configuration_key")
    return result


def facets(db, catalog_scope="ALL", *, rows=None):
    rows = records(db) if rows is None else rows
    if catalog_scope == "US_BASE_2000":
        rows = active_us_rows(rows)
    elif catalog_scope == "US_CONFIRMED_2000":
        rows = active_us_base_rows(rows)
    make_models = {}
    for _, c in rows:
        entry = make_models.setdefault(normalized(c["make"]), {"name": c["make"], "models": {}})
        entry["models"].setdefault(normalized(c["model"]), c["model"])
    return {
        "version": version(rows),
        "makes": [
            {"name": item["name"], "models": sorted(item["models"].values())}
            for _, item in sorted(make_models.items())
        ],
        "markets": sorted({c["original_market"] for _, c in rows}),
        "years": sorted({c["model_year"] for _, c in rows}, reverse=True),
        "counts": coverage(db, rows),
        "ranking_version": RANK_VERSION,
    }


def coverage(db, rows=None):
    rows = records(db) if rows is None else rows
    fields = [
        "body",
        "engine_displacement",
        "transmission_family",
        "drivetrain",
        "fuel_combined",
        "electricity_combined",
        "ground_clearance",
        "seats",
    ]
    return {
        "base_catalog": base_catalog_counts(rows),
        "makes": len({normalized(c["make"]) for _, c in rows}),
        "models": len({(normalized(c["make"]), normalized(c["model"])) for _, c in rows}),
        "verified_generations": len(
            {
                (c["make"], c["model"], c["generation"], c["original_market"])
                for _, c in rows
                if identity_verified(c)
            }
        ),
        "published_versions": len(rows),
        "fully_supported_dossiers": sum(dossier_full(c) for _, c in rows),
        "verified_scoped_versions": sum(identity_verified(c) for _, c in rows),
        "fields": {key: sum(fact_value(c, key) is not None for _, c in rows) for key in fields},
        "markets": {
            m: sum(c["original_market"] == m for _, c in rows)
            for m in sorted({c["original_market"] for _, c in rows})
        },
        "commercial_versions": sum(c["publication_scope"] == "COMMERCIAL" for _, c in rows),
        "approved_assets": len(
            list(db.scalars(select(VehicleAsset.id).where(VehicleAsset.state == "APPROVED")))
        ),
    }


def active_us_rows(rows):
    rules = scope_policy()
    return [
        (v, c)
        for v, c in rows
        if catalog_in_active_scope(c, rules)
        and (source_confirmed_core_ready(c) or commercial_overlay_core_ready(c))
        and not catalog_excluded(c)
    ]


def active_us_base_rows(rows):
    """Ordinary search scope; request-specific missing facts are checked by search/resolve."""
    rules = scope_policy()
    return [
        (v, c)
        for v, c in rows
        if catalog_in_active_scope(c, rules) and base_catalog_ready(c) and not catalog_excluded(c)
    ]


def apply_fit_ranking(items, filters, language):
    """Rank only hard matches and observable preferences, with an auditable explanation."""

    def numeric(item, key):
        f = item["facts"].get(key, {})
        if f.get("status") != "CONFIRMED":
            return None
        try:
            return float(f["value"])
        except (TypeError, ValueError, KeyError):
            return None

    measures = []
    if "performance" in filters.priorities:
        measures.append(
            (
                "performance",
                "power_hp",
                1,
                "Подтверждённая мощность по источнику",
                "Mənbəyə görə təsdiqlənmiş güc",
            )
        )
    if "space" in filters.priorities or filters.family_use:
        measures.append(
            ("space", "seats", 1, "Подтверждённое число мест", "Təsdiqlənmiş oturacaq sayı")
        )
    if "cost" in filters.priorities and items:
        bases = {
            (
                i.get("test_cycle"),
                i["market"],
                i["facts"].get("fuel_combined", {}).get("unit"),
                i["facts"].get("powertrain", {}).get("value"),
            )
            for i in items
        }
        if len(bases) == 1 and all(numeric(i, "fuel_combined") is not None for i in items):
            measures.append(
                (
                    "fuel_only",
                    "fuel_combined",
                    -1,
                    "Меньший расход в одном тестовом цикле; это не стоимость владения",
                    "Eyni sınaq dövründə daha az sərfiyyat; bu, istifadə xərci deyil",
                )
            )
    for item in items:
        item["ranking"].update(
            score=100 + (10 if item.get("base_catalog_ready") else 0),
            basis="hard_constraints_then_evidenced_preferences",
            reasons=[
                tr(
                    language,
                    "Соответствует подтверждённым условиям запроса",
                    "Sorğunun təsdiqlənmiş şərtlərinə uyğundur",
                )
            ],
            supported_priorities=[],
        )
        if item.get("base_catalog_ready"):
            item["ranking"]["reasons"].append(
                tr(
                    language,
                    "Поколение и сочетание агрегатов подтверждены",
                    "Nəsil və aqreqat uyğunluğu təsdiqlənib",
                )
            )
    for preference, key, direction, ru, az in measures:
        values = [numeric(i, key) for i in items]
        # Missing data is not a zero score for the vehicle: omit this comparison
        # for the whole candidate cohort when its coverage is incomplete.
        if not values or any(v is None for v in values):
            continue
        low, high = min(values), max(values)
        for item, value in zip(items, values, strict=True):
            relative = (
                ((value - low) if direction > 0 else (high - value)) / (high - low)
                if high > low
                else 0
            )
            item["ranking"]["score"] += round(10 * relative, 4)
            item["ranking"]["reasons"].append(f"{tr(language, ru, az)}: {value:g}")
            item["ranking"]["supported_priorities"].append(preference)
    for item in items:
        item["ranking"]["unsupported_priorities"] = [
            p for p in filters.priorities if p not in item["ranking"]["supported_priorities"]
        ]


def search(db, filters: BuyerFilters, language="ru", *, rows=None):
    all_rows = records(db) if rows is None else rows
    if filters.catalog_scope == "US_BASE_2000":
        all_rows = active_us_rows(all_rows)
    elif filters.catalog_scope == "US_CONFIRMED_2000":
        all_rows = active_us_base_rows(all_rows)
    assets = list(db.scalars(select(VehicleAsset).where(VehicleAsset.state == "APPROVED")))
    confirmed, uncertain = [], []
    rejected = {}
    # Asking prices are observations, never sale prices or evidence of liquidity.
    listings = list(
        db.scalars(
            select(MarketListing)
            .join(SourceRecord, MarketListing.source_id == SourceRecord.id)
            .where(
                SourceRecord.usage_status == SourceUsageStatus.ACTIVE,
                SourceRecord.is_demo.is_(False),
                MarketListing.data_origin == DataOrigin.REAL,
                MarketListing.country == filters.country,
                MarketListing.currency == "AZN",
                MarketListing.is_demo.is_(False),
                MarketListing.observed_at >= utcnow() - timedelta(days=30),
                MarketListing.observed_at <= utcnow(),
            )
        )
    )
    source_policies = {s.id: s for s in db.scalars(select(SourceRegistry))}
    scopes = {v.id: catalog_identity_hash(c) for v, c in all_rows}

    def permitted_listing(row):
        if row.source.source_type != "KNOWLEDGE_MARKET_OBSERVATION":
            return True
        source_id = (row.source.notes or "").split(";", 1)[0].removeprefix("registry=")
        if not scopes.get(
            row.vehicle_variant_id
        ) or f"scope={scopes[row.vehicle_variant_id]}" not in (row.source.notes or ""):
            return False
        policy = source_policies.get(source_id)
        return bool(
            policy
            and policy.state in {"APPROVED", "LOCAL_RESEARCH"}
            and (
                get_settings().environment != "production" or policy.config.get("commercial_reuse")
            )
        )

    listings = [row for row in listings if permitted_listing(row)]
    for variant, c in all_rows:
        if filters.catalog_ready_only and not _ready_for_scope(c, filters.catalog_scope):
            continue
        missing, failed, reasons = [], [], []

        def check(key, actual, predicate, missing=missing, failed=failed, reasons=reasons):
            if actual is None:
                missing.append(key)
            elif not predicate(actual):
                failed.append(key)
            else:
                reasons.append(key)

        if filters.makes:
            check(
                "make", c["make"], lambda x: normalized(x) in {normalized(m) for m in filters.makes}
            )
        if filters.models:
            check(
                "model",
                c["model"],
                lambda x: normalized(x) in {normalized(m) for m in filters.models},
            )
        if filters.generations:
            check(
                "generation",
                _consumer_generation(c),
                lambda x: normalized(x) in {normalized(g) for g in filters.generations},
            )
        if filters.query and normalized(filters.query) not in normalized(
            " ".join([c["make"], c["model"], *c.get("aliases", [])])
        ):
            failed.append("query")
        if filters.year_min:
            check("year_min", c["model_year"], lambda x: x >= filters.year_min)
        if filters.year_max:
            check("year_max", c["model_year"], lambda x: x <= filters.year_max)
        if filters.market_preference == "SELECTED":
            check("market", c["original_market"], lambda x: x in filters.markets)
        if filters.body:
            body = fact_value(c, "body")
            if (
                body == "SUV"
                and c.get("source_registry_id") == "epa"
                and "CROSSOVER" in filters.body
                and "SUV" not in filters.body
            ):
                missing.append("body_subtype")
            else:
                check("body", body, lambda x: x in filters.body)
        if filters.supply_channel:
            check("supply_channel", c.get("supply_channel"), lambda x: x == filters.supply_channel)
        if filters.engine not in {"ANY", "UNKNOWN"}:
            engine = filters.engine
            if engine in {"BEV", "PHEV", "HEV", "MHEV", "EREV", "FCEV"}:
                check("engine", fact_value(c, "powertrain"), lambda x, engine=engine: x == engine)
            else:
                check(
                    "fuel",
                    fact_value(c, "fuel"),
                    lambda x, engine=engine: x == ("DIESEL" if engine == "DIESEL" else "GASOLINE"),
                )
                if engine.startswith("GASOLINE"):
                    check("powertrain", fact_value(c, "powertrain"), lambda x: x == "ICE")
                if engine in {"GASOLINE_NA", "GASOLINE_TURBO"}:
                    check(
                        "aspiration",
                        fact_value(c, "aspiration"),
                        lambda x, engine=engine: (
                            x == ("TURBO" if engine.endswith("TURBO") else "NATURALLY_ASPIRATED")
                        ),
                    )
        if filters.transmission not in {"ANY", "UNKNOWN"}:
            actual = fact_value(c, "transmission_family")
            fit = _transmission_fit(actual, filters.transmission)
            if fit == "MATCH":
                reasons.append("transmission")
            elif fit == "CONFLICT":
                failed.append("transmission")
            elif actual is not None:
                missing.append("transmission_construction")
            else:
                missing.append("transmission")
        if filters.drivetrain:
            check("drivetrain", fact_value(c, "drivetrain"), lambda x: x == filters.drivetrain)
        for param, key in [
            (filters.min_seats, "seats"),
            (filters.min_clearance_mm, "ground_clearance"),
        ]:
            if param:
                check(key, fact_value(c, key), lambda x, p=param: Decimal(str(x)) >= p)
        if filters.displacement_max_l is not None:
            check(
                "displacement",
                fact_value(c, "engine_displacement"),
                lambda x: Decimal(str(x)) <= filters.displacement_max_l,
            )
        if filters.large_boot:
            check("cargo_l", fact_value(c, "cargo_l"), lambda x: Decimal(str(x)) >= 450)
        budget_rows = [
            r
            for r in listings
            if r.vehicle_variant_id == variant.id
            and (not filters.city or normalized(r.city or "") == normalized(filters.city))
        ]
        if filters.budget_max_minor is not None or filters.budget_min_minor is not None:
            prices = [int(r.price * 100) for r in budget_rows]
            if filters.initial_service_included:
                missing.append("initial_service_budget")
            check(
                "budget",
                prices or None,
                lambda xs: any(
                    (filters.budget_max_minor is None or x <= filters.budget_max_minor)
                    and (filters.budget_min_minor is None or x >= filters.budget_min_minor)
                    for x in xs
                ),
            )
        if failed:
            for reason in failed:
                rejected[reason] = rejected.get(reason, 0) + 1
            continue
        item = card(db, variant, c, language, assets)
        tradeoffs = []
        if fact_value(c, "powertrain") in {"BEV", "PHEV"} and filters.charging != "YES":
            tradeoffs.append("CHARGING_NOT_CONFIRMED")
        if filters.market_preference == "UNKNOWN":
            tradeoffs.append("MARKET_NOT_CHOSEN")
        if filters.engine == "UNKNOWN" or filters.transmission == "UNKNOWN":
            tradeoffs.append("CONFIGURATION_PREFERENCE_UNRESOLVED")
        item.update(
            {
                "match": "NEEDS_CONFIRMATION" if missing else "MATCH",
                "matched_conditions": reasons,
                "missing": missing,
                "tradeoffs": tradeoffs,
                "asking_prices": [
                    {
                        "price_minor": int(r.price * 100),
                        "observed_at": r.observed_at.isoformat(),
                        "source_id": r.source_id,
                        "url": r.url,
                    }
                    for r in budget_rows
                ],
                "ranking": {
                    "version": RANK_VERSION,
                    "score": len(reasons),
                    "basis": "confirmed_constraint_count",
                    "unsupported_priorities": list(filters.priorities),
                },
            }
        )
        (uncertain if missing else confirmed).append(item)

    apply_fit_ranking(confirmed, filters, language)

    def recommended_order(item):
        return (-item["ranking"]["score"], -item["year"], item["make"], item["model"], item["id"])

    recommended = sorted(confirmed, key=recommended_order)
    top = recommended[0] if recommended else None

    def order(item):
        if filters.sort == "make":
            return (item["make"], item["model"], -item["year"], item["id"])
        if filters.sort == "consumption":
            # Partition liquid/electric units; never rank kWh against litres as a shared score.
            fact = item["facts"].get("fuel_combined") or item["facts"].get("electricity_combined")
            return (
                item["test_cycle"],
                (fact or {}).get("unit", "~"),
                Decimal(str(fact["value"])) if fact else Decimal("9999"),
                item["id"],
            )
        return (
            -item["ranking"]["score"] if filters.sort == "recommended" else 0,
            -item["year"],
            item["make"],
            item["model"],
            item["id"],
        )

    confirmed.sort(key=order)
    uncertain.sort(key=order)

    # One strongest configuration per model makes competitors visible; all matching
    # configurations remain available through the existing matches/resolver contract.
    leaders = {}
    for item in recommended:
        leaders.setdefault((normalized(item["make"]), normalized(item["model"])), item)
    competitors = sorted(
        [item for item in leaders.values() if top is None or item["id"] != top["id"]],
        key=order,
    )

    def group_count(items):
        return len({(normalized(i["make"]), normalized(i["model"])) for i in items})

    return {
        "catalog_version": version(all_rows),
        "ranking_version": RANK_VERSION,
        "recommendation": {
            "top": top,
            "competitors": competitors[filters.offset : filters.offset + filters.limit],
            "competitor_models": len(competitors),
            "tied_on_evidence": bool(
                top
                and sum(i["ranking"]["score"] == top["ranking"]["score"] for i in leaders.values())
                > 1
            ),
            "tie_break": "model_year_then_name",
            "scope": "CONFIRMED_REQUEST_FIT_NOT_OVERALL_RELIABILITY_OR_VALUE",
        },
        "filters": filters.model_dump(mode="json"),
        "matches": confirmed[filters.offset : filters.offset + filters.limit],
        "needs_confirmation": uncertain[filters.offset : filters.offset + filters.limit],
        "matched_models": group_count(confirmed),
        "matched_versions": len(confirmed),
        "uncertain_models": group_count(uncertain),
        "uncertain_versions": len(uncertain),
        "rejections": rejected,
        "suggested_relaxation": max(rejected, key=rejected.get)
        if rejected and not confirmed
        else None,
        "constraints_relaxed": False,
    }


def resolve(db, query, *, rows=None):
    rows = records(db) if rows is None else rows
    if query.get("catalog_scope") == "US_BASE_2000":
        rows = active_us_rows(rows)
    elif query.get("catalog_scope") == "US_CONFIRMED_2000":
        rows = active_us_base_rows(rows)
    q = {k: v for k, v in query.items() if v is not None and v != ""}
    candidates = []
    for v, c in rows:
        if q.get("catalog_ready_only") and not _ready_for_scope(c, q.get("catalog_scope")):
            continue
        if q.get("make") and normalized(q["make"]) != normalized(c["make"]):
            continue
        names = {normalized(c["model"]), *[normalized(a) for a in c.get("aliases", [])]}
        if q.get("model") and normalized(q["model"]) not in names:
            continue
        if q.get("year") and int(q["year"]) != c["model_year"]:
            continue
        candidates.append((v, c))
    named = list(candidates)
    if q.get("market") and q["market"] not in {"UNKNOWN", "ANY"}:
        candidates = [(v, c) for v, c in candidates if c["original_market"] == q["market"]]
        if not candidates and named:
            # Establish market coverage before checking mechanical compatibility.
            return {
                "status": "UNSUPPORTED",
                "candidates": [],
                "missing": ["market_coverage"],
                "conflicts": [],
                "suggestions": [],
            }
    conflicts, missing = set(), set()
    for key, fact in [
        ("generation", "generation"),
        ("engine", "engine_displacement"),
        ("transmission", "transmission_family"),
        ("drivetrain", "drivetrain"),
        ("trim", "trim"),
        ("body", "body"),
        ("seats", "seats"),
    ]:
        if key not in q:
            continue
        remaining = []
        for v, c in candidates:
            actual = (
                _consumer_generation(c)
                if key == "generation"
                else fact_value(c, fact)
            )
            fit = _transmission_fit(actual, q[key]) if key == "transmission" else None
            if actual is None or fit == "UNKNOWN":
                missing.add(key)
                remaining.append((v, c))
            elif fit == "MATCH" or (key == "engine" and _same_decimal(actual, q[key])) or (
                key != "engine" and normalized(str(actual)) == normalized(str(q[key]))
            ):
                remaining.append((v, c))
        if not remaining and candidates:
            conflicts.add(key)
        candidates = remaining
    uncertain = []
    if query.get("catalog_scope") == "US_CONFIRMED_2000":
        fields = {
            "engine": "engine_displacement",
            "transmission": "transmission_family",
            "drivetrain": "drivetrain",
            "trim": "trim",
            "body": "body",
            "seats": "seats",
        }
        exact = []
        for v, c in candidates:
            gaps = [k for k, f in fields.items() if k in q and fact_value(c, f) is None]
            if gaps:
                item = card(db, v, c, query.get("language", "ru"))
                item.update(match="NEEDS_CONFIRMATION", missing=gaps)
                uncertain.append(item)
            else:
                exact.append((v, c))
        candidates = exact
        missing = {k for item in uncertain for k in item["missing"]} if not exact else set()
    suggestions = []
    if not named and q.get("model"):
        names = sorted({(c["make"], c["model"]) for _, c in rows})
        suggestions = [
            {"make": m, "model": n}
            for m, n in sorted(
                names,
                key=lambda x: (
                    -SequenceMatcher(None, normalized(q["model"]), normalized(x[1])).ratio()
                ),
            )[:5]
            if SequenceMatcher(None, normalized(q["model"]), normalized(n)).ratio() >= 0.6
        ]
    status = (
        "CONTRADICTION"
        if conflicts
        else "NEEDS_CONFIRMATION"
        if not candidates and uncertain
        else "NOT_IN_CATALOG"
        if not candidates
        else "EXACT"
        if len(candidates) == 1 and not missing
        else "MULTIPLE"
    )
    return {
        "status": status,
        "candidates": [card(db, v, c, query.get("language", "ru")) for v, c in candidates[:50]],
        "candidate_count": len(candidates),
        "needs_confirmation": uncertain,
        "missing": sorted(missing),
        "conflicts": sorted(conflicts),
        "suggestions": suggestions,
    }


def _same_decimal(left, right):
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except Exception:
        return False


def costs(catalog, scenario: CostScenario):
    s = scenario
    distance = Decimal(s.monthly_km * s.months)
    fuel, electric = (
        fact_value(catalog, "fuel_combined"),
        fact_value(catalog, "electricity_combined"),
    )
    powertrain = fact_value(catalog, "powertrain")
    energy = None
    if powertrain == "BEV" and electric is not None and s.electricity_price is not None:
        energy = distance / 100 * Decimal(str(electric)) * s.electricity_price
    elif powertrain in {"ICE", "HEV"} and fuel is not None and s.fuel_price is not None:
        energy = distance / 100 * Decimal(str(fuel)) * s.fuel_price
    depreciation = (
        s.purchase_price - s.resale_price
        if s.purchase_price is not None and s.resale_price is not None
        else None
    )
    components = {
        "depreciation": depreciation,
        "energy": energy,
        "maintenance": s.maintenance,
        "repair_reserve": s.repair_reserve,
        "other": s.other_costs,
    }
    complete = all(v is not None for v in components.values()) and bool(
        s.price_date and s.price_source
    )

    def money(v):
        return str(v.quantize(Decimal("0.01"))) if v is not None else None

    return {
        "version": "ownership-decimal-1.0",
        "currency": "AZN",
        "months": s.months,
        "distance_km": str(distance),
        "purchase_separate": money(s.purchase_price),
        "components": {k: money(v) for k, v in components.items()},
        "known_subtotal": money(sum((v for v in components.values() if v is not None), Decimal(0)))
        if any(v is not None for v in components.values())
        else None,
        "total": money(sum(components.values())) if complete else None,
        "status": "SCENARIO" if complete else "INSUFFICIENT_DATA",
        "assumptions": s.model_dump(mode="json"),
        "missing": [k for k, v in components.items() if v is None]
        + ([] if s.price_date and s.price_source else ["price_date_and_source"]),
        "consumption_basis": "SOURCE_TEST_CYCLE_NOT_AZ_REAL_WORLD",
        "price_basis": "USER_SCENARIO_NOT_VERIFIED_MARKET",
    }


def vehicle_profile(c, language):
    """A compact catalogue profile, independent of paid or full dossier readiness."""

    def t(ru, az):
        return tr(language, ru, az)

    groups = [
        (
            "engine",
            "Двигатель",
            "Mühərrik",
            [
                "engine_description",
                "engine_family",
                "engine_code",
                "engine_displacement",
                "engine_displacement_cc",
                "cylinders",
                "power_hp",
                "power_kw",
                "torque_lb_ft",
                "torque_nm",
                "compression_ratio",
                "timing_drive",
                "motor_description",
            ],
        ),
        (
            "transmission",
            "Коробка",
            "Sürətlər qutusu",
            [
                "transmission_description",
                "transmission_family",
                "transmission_code",
                "gears",
                "drivetrain",
                "drivetrain_system",
            ],
        ),
        (
            "fuel",
            "Топливо",
            "Yanacaq",
            [
                "fuel",
                "powertrain",
                "fuel_grade",
                "octane_aki",
                "octane_ron",
                "fuel_tank_l",
                "fuel_tank_gal",
                "fuel_tank_us_gal",
                "fuel_combined",
                "electricity_combined",
                "epa_range_miles",
                "epa_city_mpg",
                "epa_highway_mpg",
                "epa_combined_mpg",
                "acceleration_0_60_mph_s",
            ],
        ),
        ("induction", "Впрыск / наддув", "Püskürtmə / hava doldurma", ["injection", "aspiration"]),
        (
            "fluids",
            "Масла и жидкости",
            "Yağlar və mayelər",
            [
                "engine_oil_viscosity",
                "engine_oil_specification",
                "engine_oil_capacity_l",
                "engine_oil_alternatives",
                "transmission_fluid",
                "transfer_fluid",
                "front_differential_fluid",
                "rear_differential_fluid",
                "coolant",
                "coolant_capacity_note",
                "brake_fluid",
            ],
        ),
        (
            "dimensions",
            "Кузов и размеры",
            "Kuzov və ölçülər",
            [
                "body",
                "length",
                "width",
                "height",
                "wheelbase",
                "length_mm",
                "width_mm",
                "height_mm",
                "wheelbase_mm",
                "ground_clearance",
                "length_in",
                "width_in",
                "height_in",
                "wheelbase_in",
            ],
        ),
        (
            "suspension",
            "Подвеска",
            "Asqı",
            [
                "suspension",
                "front_suspension",
                "rear_suspension",
                "suspension_front",
                "suspension_rear",
            ],
        ),
        ("brakes", "Тормоза", "Əyləclər", ["brakes", "front_brakes", "rear_brakes"]),
        (
            "wheels",
            "Шины и диски",
            "Şinlər və disklər",
            ["tires", "wheels", "front_tires", "rear_tires"],
        ),
        (
            "interior",
            "Салон / места / багажник",
            "Salon / oturacaqlar / baqaj",
            [
                "seats",
                "seating_options",
                "cargo_l",
                "cargo_cu_ft",
                "hatch_cargo",
                "four_door_cargo",
                "two_door_cargo",
                "cargo_max_cu_ft",
                "cargo_volume_max_cu_ft",
                "curb_weight_lb",
            ],
        ),
        (
            "equipment",
            "Электрика / оснащение",
            "Elektrik / təchizat",
            ["equipment", "trim", "battery_kwh", "charge_ac_240v_hours"],
        ),
    ]
    labels = {
        "power_hp": ("Мощность, hp", "Güc, hp"),
        "torque_lb_ft": ("Крутящий момент, lb-ft", "Fırlanma anı, lb-ft"),
        "torque_nm": ("Крутящий момент, Н·м", "Fırlanma anı, N·m"),
        "engine_displacement_cc": ("Объём, см³", "Həcm, sm³"),
        "injection": ("Впрыск", "Püskürtmə"),
        "seating_options": (
            "Варианты мест; уточнить экземпляр",
            "Oturacaq variantları; avtomobildə dəqiqləşdirin",
        ),
        "acceleration_0_100_s": ("Разгон 0–100 км/ч", "0–100 km/saat sürətlənmə"),
        "octane_aki": ("Октановое число AKI (США)", "AKI oktan ədədi (ABŞ)"),
        "octane_ron": ("Октановое число RON", "RON oktan ədədi"),
        "engine_family": ("Семейство двигателя", "Mühərrik ailəsi"),
        "engine_code": ("Код двигателя", "Mühərrik kodu"),
        "transmission_code": ("Код коробки", "Sürətlər qutusunun kodu"),
        "drivetrain_system": ("Система привода", "Ötürmə sistemi"),
        "timing_drive": ("Привод ГРМ", "Qazpaylama mexanizminin ötürücüsü"),
        "engine_oil_viscosity": ("Вязкость масла", "Yağın özlülüyü"),
        "engine_oil_specification": ("Допуск масла", "Yağ spesifikasiyası"),
        "engine_oil_capacity_l": ("Объём масла при замене", "Dəyişmə zamanı yağ həcmi"),
        "transmission_fluid": ("Жидкость коробки", "Sürətlər qutusu mayesi"),
        "coolant": ("Охлаждающая жидкость", "Soyuducu maye"),
        "brake_fluid": ("Тормозная жидкость", "Əyləc mayesi"),
        "engine_oil_alternatives": (
            "Допустимые альтернативы масла",
            "Yağın icazə verilən alternativləri",
        ),
        "coolant_capacity_note": ("Объём системы охлаждения", "Soyutma sisteminin tutumu"),
        "transfer_fluid": ("Жидкость раздаточной коробки", "Paylayıcı qutunun mayesi"),
        "front_differential_fluid": ("Масло переднего дифференциала", "Ön diferensialın yağı"),
        "rear_differential_fluid": ("Масло заднего дифференциала", "Arxa diferensialın yağı"),
        "compression_ratio": ("Степень сжатия", "Sıxılma dərəcəsi"),
        "epa_city_mpg": ("Расход EPA, город (US mpg)", "EPA sərfiyyatı, şəhər (US mpg)"),
        "epa_highway_mpg": ("Расход EPA, трасса (US mpg)", "EPA sərfiyyatı, magistral (US mpg)"),
        "epa_combined_mpg": ("Расход EPA, смешанный (US mpg)", "EPA sərfiyyatı, qarışıq (US mpg)"),
        "acceleration_0_60_mph_s": ("Разгон 0–60 mph", "0–60 mph sürətlənmə"),
        "cargo_max_cu_ft": ("Багажник со сложенными сиденьями", "Oturacaqlar qatlandıqda baqaj"),
        "cargo_volume_max_cu_ft": (
            "Багажник со сложенными сиденьями",
            "Oturacaqlar qatlandıqda baqaj",
        ),
        "curb_weight_lb": ("Снаряжённая масса", "Təchiz olunmuş kütlə"),
        "equipment": ("Оснащение", "Təchizat"),
        "battery_kwh": ("Ёмкость батареи", "Batareya tutumu"),
    }
    for keys, ru, az in [
        (["length", "length_mm", "length_in"], "Длина", "Uzunluq"),
        (["width", "width_mm", "width_in"], "Ширина без зеркал", "Güzgülərsiz en"),
        (["height", "height_mm", "height_in"], "Высота", "Hündürlük"),
        (["wheelbase", "wheelbase_mm", "wheelbase_in"], "Колёсная база", "Təkər bazası"),
        (["fuel_tank_l", "fuel_tank_gal", "fuel_tank_us_gal"], "Топливный бак", "Yanacaq çəni"),
        (["cargo_l", "cargo_cu_ft"], "Багажник", "Baqaj"),
        (["suspension", "front_suspension", "suspension_front"], "Передняя подвеска", "Ön asqı"),
        (["rear_suspension", "suspension_rear"], "Задняя подвеска", "Arxa asqı"),
        (["brakes", "front_brakes"], "Передние тормоза", "Ön əyləclər"),
        (["rear_brakes"], "Задние тормоза", "Arxa əyləclər"),
        (["tires", "front_tires"], "Шины", "Şinlər"),
        (["rear_tires"], "Задние шины", "Arxa şinlər"),
        (["wheels"], "Диски", "Disklər"),
    ]:
        labels.update({key: (ru, az) for key in keys})

    def row(key):
        f = c["facts"].get(key, {})
        if f.get("status") != "CONFIRMED" or f.get("value") in (None, "", "UNKNOWN", "UNRESOLVED"):
            return None
        source = f.get("documentary_source") or {}
        return dict(
            key=key,
            label=f.get("titles", {}).get(language)
            or t(*labels.get(key, LABELS.get(key, (key, key)))),
            value=fact_display(f, language) + (" " + f["unit"] if f.get("unit") else ""),
            reuse_status=f.get("reuse_status"),
            source_url=source.get("url") or f.get("source_url") or c["source_url"],
            **({} if c.get("commercial_fact_overlay") else {
                "locator": source.get("locator") or f.get("locator")
            }),
        )

    technical = []
    for key, ru, az, keys in groups:
        rows = [r for k in keys if (r := row(k))]
        if key == "fluids" and not rows:
            # The UI component can be exercised with a local QA response
            # fixture; no empty oils category belongs in a consumer profile.
            continue
        technical.append(
            dict(
                key=key,
                title=t(ru, az),
                rows=rows,
                empty_text=t(
                    "Подтверждённых данных для этой версии пока нет.",
                    "Bu versiya üçün təsdiqlənmiş məlumat hələ yoxdur.",
                ),
            )
        )
    scope = (c.get("identity_verification") or {}).get("range_scope")
    summary = [
        dict(key="market", label=t("Исходный рынок", "İlkin bazar"), value=c["original_market"]),
        dict(
            key="model_year",
            label=t("Модельный год выбранной версии", "Seçilmiş versiyanın model ili"),
            value=str(c["model_year"]),
        ),
    ]
    if _consumer_generation(c):
        summary.append(
            dict(key="generation", label=t("Поколение", "Nəsil"), value=_consumer_generation(c))
        )
    if scope:
        summary.append(
            dict(
                key="years",
                label=t(
                    "Подтверждённый диапазон сочетания", "Aqreqat uyğunluğunun təsdiqlənmiş illəri"
                ),
                value=f"{scope['model_year_from']}–{scope['model_year_to']}",
            )
        )
    for key in [
        "body",
        "seats",
        "fuel",
        "engine_description",
        "transmission_description",
        "drivetrain",
        "acceleration_0_100_s",
        "octane_ron",
        "octane_aki",
    ]:
        value = row(key)
        if value:
            summary.append(value)
    documentary = c.get("documentary_sections", [])

    def evidence(keys):
        return [
            dict(
                text=s["text"]["az" if language == "az" else "ru"],
                status=s["status"],
                sources=s["references"],
            )
            for s in documentary
            if s["key"] in keys
        ]

    return dict(
        summary=summary,
        technical=technical,
        categories=[
            dict(key="technical", title=t("Техническая часть", "Texniki hissə")),
            dict(
                key="weak_points",
                title=t("Слабые места", "Zəif cəhətlər"),
                entries=evidence({"known_issues"}),
                empty_text=t(
                    "Применимые слабые места пока не подтверждены. Это не означает отсутствия неисправностей.",
                    "Tətbiq olunan zəif cəhətlər hələ təsdiqlənməyib. Bu, nasazlığın olmaması demək deyil.",
                ),
            ),
            dict(
                key="campaigns",
                title=t("Сервисные кампании", "Servis kampaniyaları"),
                entries=evidence({"recalls", "communications"}),
                empty_text=t(
                    "Подтверждённых кампаний в этом профиле пока нет. Применимость и выполнение проверяются по VIN.",
                    "Bu profildə təsdiqlənmiş kampaniya hələ yoxdur. Tətbiq və icra VIN üzrə yoxlanılır.",
                ),
            ),
            dict(
                key="inspection",
                title=t("Что проверить при покупке", "Alış zamanı nə yoxlanmalıdır"),
                entries=[],
                empty_text=t(
                    "Общий план осмотра: VIN и документы, комплектация, кузов и следы ремонта, холодный запуск, диагностика блоков, тест-драйв и сервисная история. Это рекомендации по осмотру, а не найденные дефекты.",
                    "Ümumi baxış planı: VIN və sənədlər, komplektasiya, kuzov və təmir izləri, soyuq işəsalma, blokların diaqnostikası, sınaq yürüşü və servis tarixçəsi. Bunlar aşkar edilmiş qüsurlar deyil, baxış tövsiyələridir.",
                ),
            ),
        ],
        fuel_note=t(
            "AKI и RON — разные шкалы. Regular/Premium из EPA не подтверждают AI-92 или AI-95 для этой версии.",
            "AKI və RON fərqli şkalalardır. EPA Regular/Premium təsnifatı bu versiya üçün AI-92 və ya AI-95-i təsdiqləmir.",
        ),
    )


def projection(c, language, *, generated_at=None, preferences=None):
    def t(ru, az):
        return tr(language, ru, az)

    sections = [
        PaidReportSection(
            key="conclusion",
            title=t("Главное перед покупкой", "Alışdan əvvəl əsas məqam"),
            paragraphs=[
                ReportParagraph(
                    text=t(
                        "Базовые характеристики этой версии опубликованы. Данных недостаточно для вывода о надёжности, состоянии конкретной машины или справедливой цене в AZ. Начните с проверки версии и осмотра.",
                        "Bu versiyanın əsas göstəriciləri dərc edilib. Etibarlılıq, konkret avtomobilin vəziyyəti və AZ üzrə ədalətli qiymət barədə nəticə üçün məlumat yetərli deyil. Versiyanı dəqiqləşdirin və baxış keçirin.",
                    )
                )
            ],
        )
    ]
    groups = {
        "vehicle": (
            t("Автомобиль и версия", "Avtomobil və versiya"),
            ["powertrain", "fuel", "body", "size_class", "drivetrain", "trim"],
        ),
        "engine": (
            t("Двигатель", "Mühərrik"),
            [
                "engine_displacement",
                "cylinders",
                "aspiration",
                "engine_description",
                "motor_description",
                "power_kw",
            ],
        ),
        "transmission": (
            t("Коробка передач", "Sürətlər qutusu"),
            ["transmission_family", "transmission_description", "gears"],
        ),
        "fuel": (
            t("Расход и зарядка", "Sərfiyyat və şarj"),
            [
                "fuel_combined",
                "electricity_combined",
                "fuel_grade",
                "charge_ac_240v_hours",
                "epa_range_miles",
            ],
        ),
        "body": (
            t("Кузов и вместимость", "Kuzov və tutum"),
            ["seats", "ground_clearance", "hatch_cargo", "four_door_cargo", "two_door_cargo"],
        ),
    }
    for key, (title, keys) in groups.items():
        section = PaidReportSection(key=key, title=title, collapsed=True)
        for field in keys:
            f = c["facts"].get(field)
            if f:
                section.rows.append(
                    ReportRow(
                        key=field,
                        label=f.get("titles", {}).get(language)
                        or t(*LABELS.get(field, (field, field))),
                        value=fact_display(f, language)
                        + (" " + f["unit"] if f.get("unit") else ""),
                        source_ids=[f["source_id"]],
                        evidence_ids=[f["evidence_id"]],
                    )
                )
        if not section.rows:
            section.paragraphs.append(
                ReportParagraph(
                    text=t("Проверенных данных пока нет.", "Təsdiqlənmiş məlumat hələ yoxdur.")
                )
            )
        sections.append(section)
    for key, ru, az, gap_ru, gap_az in [
        (
            "chassis",
            "Подвеска и рулевое",
            "Asqı və sükan",
            "Нет применимой схемы подвески и статистики ремонтов. На подъёмнике проверьте люфты, утечки и следы ударов; на тест-драйве — стуки и увод.",
            "Uyğun asqı sxemi və təmir statistikası yoxdur. Qaldırıcıda boşluqları, sızmaları və zərbə izlərini, sınaq yürüşündə səsləri və yana çəkməni yoxlayın.",
        ),
        (
            "safety",
            "Тормоза и безопасность",
            "Əyləclər və təhlükəsizlik",
            "Нет проверенных данных о тормозной системе, оснащении и применимом краш-тесте. Сверьте оснащение по документам, ошибки ABS/SRS и состояние ремней. Отзыв для модели не подтверждает его выполнение на экземпляре.",
            "Əyləc sistemi, təchizat və uyğun qəza sınağı barədə yoxlanmış məlumat yoxdur. Sənədləri, ABS/SRS xətalarını və kəmərləri yoxlayın. Model üzrə geri çağırma konkret avtomobildə işin görüldüyünü təsdiqləmir.",
        ),
        (
            "electrical",
            "Электрика и электроника",
            "Elektrik və elektronika",
            "Нет применимых сервисных бюллетеней по электронике. Проверьте работу оборудования и полную диагностику блоков; отсутствие лампы ошибки не заменяет диагностику.",
            "Elektronika üzrə uyğun servis bülletenləri yoxdur. Avadanlığı və bütün blokları diaqnostika edin; xəta lampasının sönük olması diaqnostikanı əvəz etmir.",
        ),
        (
            "service",
            "Обслуживание и ремонты",
            "Xidmət və təmir",
            "Не подтверждены регламент, спецификации жидкостей и местные цены работ. Запросите руководство для точного рынка и двигателя, сервисные документы и датированную смету. Резерв ремонта задаётся отдельно в сравнении.",
            "Xidmət cədvəli, maye spesifikasiyaları və yerli iş qiymətləri təsdiqlənməyib. Dəqiq bazar və mühərrik üçün təlimat, servis sənədləri və tarixli smeta istəyin. Təmir ehtiyatı müqayisədə ayrıca verilir.",
        ),
        (
            "market",
            "Цена и обслуживание в AZ",
            "AZ üzrə qiymət və xidmət",
            "Нет достаточной выборки свежих сопоставимых предложений в AZ. Сравнивайте одинаковые версии с учётом состояния; цена объявления не равна цене сделки и не доказывает ликвидность.",
            "AZ üzrə aktual və müqayisə edilə bilən elan nümunəsi yetərli deyil. Eyni versiyaları vəziyyəti nəzərə alaraq müqayisə edin; elan qiyməti satış qiyməti deyil və satılma sürətini sübut etmir.",
        ),
        (
            "owners",
            "Опыт владельцев",
            "Sahiblərin təcrübəsi",
            "Для этой версии нет проверенной независимой выборки отзывов (0 материалов). Надёжность и вероятность поломки по отсутствию отзывов не оцениваются.",
            "Bu versiya üzrə yoxlanmış müstəqil rəy nümunəsi yoxdur (0 material). Rəylərin olmaması ilə etibarlılıq və nasazlıq ehtimalı qiymətləndirilmir.",
        ),
    ]:
        sections.append(
            PaidReportSection(
                key=key,
                title=t(ru, az),
                collapsed=True,
                paragraphs=[ReportParagraph(text=t(gap_ru, gap_az))],
            )
        )
    used = {field for _, fields in groups.values() for field in fields}
    additional = [
        ReportRow(
            key=key,
            label=f.get("titles", {}).get(language) or t(*LABELS.get(key, (key, key))),
            value=fact_display(f, language) + (" " + f["unit"] if f.get("unit") else ""),
            source_ids=[f["source_id"]],
            evidence_ids=[f["evidence_id"]],
        )
        for key, f in c["facts"].items()
        if key not in used
    ]
    if additional:
        sections.append(
            PaidReportSection(
                key="additional_facts",
                title=t("Дополнительные сведения источника", "Mənbənin əlavə məlumatları"),
                rows=additional,
            )
        )
    if fact_value(c, "powertrain") in {"BEV", "HEV", "PHEV", "MHEV", "EREV", "FCEV"}:
        sections.append(
            PaidReportSection(
                key="battery",
                title=t("Батарея и электропривод", "Batareya və elektrik ötürücüsü"),
                paragraphs=[
                    ReportParagraph(
                        text=t(
                            "Каталожные данные не определяют остаточный ресурс батареи. До покупки нужны диагностика высоковольтной системы и подтверждение применимых условий гарантии. Для версии с внешней зарядкой проверьте разъём, мощность станции и возможность зарядки по вашему маршруту.",
                            "Kataloq məlumatları batareyanın qalıq resursunu göstərmir. Alışdan əvvəl yüksək gərginlikli sistemi diaqnostika edin və zəmanət şərtlərini yoxlayın. Xaricdən şarj olunan versiyada giriş növünü, stansiya gücünü və marşrut üzrə şarj imkanını yoxlayın.",
                        )
                    )
                ],
            )
        )
    sections.append(
        PaidReportSection(
            key="suitability",
            title=t("Под ваши условия", "Şəraitinizə uyğunluq"),
            paragraphs=[
                ReportParagraph(
                    text=t(
                        "Оценка пригодности ограничена подтверждёнными характеристиками. Для семьи проверьте реальные места и багаж, для плохих дорог — клиренс и состояние подвески. Приоритеты надёжности и перепродажи требуют дополнительных источников.",
                        "Uyğunluq təsdiqlənmiş göstəricilərlə məhdudlaşır. Ailə üçün oturacaqları və baqajı, pis yollar üçün klirensi və asqını yoxlayın. Etibarlılıq və təkrar satış prioritetləri əlavə mənbələr tələb edir.",
                    )
                )
            ],
        )
    )
    preferences = preferences or {}
    km = preferences.get("monthly_km")
    fuel = fact_value(c, "fuel_combined")
    if (
        km is not None
        and fuel is not None
        and fact_value(c, "powertrain") not in {"BEV", "PHEV", "EREV", "FCEV"}
    ):
        fact = c["facts"]["fuel_combined"]
        amount = (Decimal(str(km)) * Decimal(str(fuel)) / 100).quantize(Decimal("0.1"))
        sections[-1].paragraphs.append(
            ReportParagraph(
                text=t(
                    f"При {km} км в месяц расчёт по циклу источника составляет {amount} L. Это ориентир тестового цикла, а не прогноз реального расхода в AZ.",
                    f"Ayda {km} km üçün mənbənin sınaq dövrü üzrə hesab {amount} L təşkil edir. Bu, sınaq göstəricisidir, AZ üzrə real sərfiyyat proqnozu deyil.",
                ),
                source_ids=[fact["source_id"]],
                evidence_ids=[fact["evidence_id"]],
            )
        )
    sections.append(
        PaidReportSection(
            key="inspection",
            title=t("Что проверить на конкретной машине", "Konkret avtomobildə nə yoxlanmalıdır"),
            paragraphs=[
                ReportParagraph(
                    text=t(
                        "Общий план осмотра: документы и идентификатор, фактическая комплектация, кузов и следы ремонта, холодный запуск, диагностика систем, тест-драйв и сервисные документы. Это план действий, а не обнаруженные дефекты.",
                        "Ümumi baxış planı: sənədlər və identifikator, faktiki komplektasiya, kuzov və təmir izləri, soyuq işəsalma, sistem diaqnostikası, sınaq yürüşü və servis sənədləri. Bu, hərəkət planıdır, aşkar edilmiş qüsurlar deyil.",
                    )
                )
            ],
        )
    )
    sections.append(
        PaidReportSection(
            key="alternatives",
            title=t("Альтернативы и следующий шаг", "Alternativlər və növbəti addım"),
            paragraphs=[
                ReportParagraph(
                    text=t(
                        "Добавьте две-три опубликованные версии в сравнение. Сначала сопоставьте конструкцию и расход в одном цикле, затем внесите свой сценарий расходов. После выбора версии проверьте объявление и доступную историю конкретного экземпляра.",
                        "Dərc edilmiş iki-üç versiyanı müqayisəyə əlavə edin. Əvvəl quruluşu və eyni dövrdə sərfiyyatı, sonra öz xərc ssenarinizi müqayisə edin. Versiyanı seçdikdən sonra elanı və konkret avtomobilin əlçatan tarixçəsini yoxlayın.",
                    )
                )
            ],
        )
    )
    if c.get("source_registry_id") == "nrcan":
        sections.append(
            PaidReportSection(
                key="licence",
                title=t("Источник и лицензия", "Mənbə və lisenziya"),
                paragraphs=[
                    ReportParagraph(
                        text="Natural Resources Canada. Contains information licensed under the Open Government Licence – Canada. https://open.canada.ca/en/open-government-licence-canada"
                    )
                ],
            )
        )
    populated_documentary_targets = set()
    for documentary in c.get("documentary_sections", []):
        # Populate existing report sections without changing the approved client layout.
        target_key = {
            "recalls": "safety",
            "communications": "electrical",
            "known_issues": "service",
            "applicability": "conclusion",
        }.get(documentary["key"], documentary["key"])
        section = next((s for s in sections if s.key == target_key), None)
        if section is not None:
            refs = c.get("documentary_evidence", {}).get(documentary["key"], {})
            paragraph = ReportParagraph(
                text=documentary["text"]["az" if language == "az" else "ru"], **refs
            )
            if target_key not in populated_documentary_targets:
                section.paragraphs = [paragraph]
            else:
                section.paragraphs.append(paragraph)
            populated_documentary_targets.add(target_key)
    return PaidVehicleReport(
        version="0.8.1",
        language=language,
        vin="",
        title=f"{c['make']} {c['model']} · {c['model_year']}",
        subtitle=configuration_display(c, language),
        generated_at=generated_at or utcnow(),
        readiness=PaidReportReadiness(
            state="NOT_ENOUGH_DATA_FOR_PAID_REPORT",
            can_purchase=False,
            missing_requirements=(["generation"] if not identity_verified(c) else [])
            + [
                "technical_reliability",
                "local_market",
                "instance_history",
            ],
            checks={"catalog_published": True, "vin_history_checked": False},
        ),
        notice=t(
            "Справочный разбор модели. VIN и история конкретного автомобиля не проверялись.",
            "Model üzrə məlumat təhlili. Konkret avtomobilin VIN-i və tarixçəsi yoxlanılmayıb.",
        ),
        sections=sections,
        source_ids=list(
            {f["source_id"] for f in c["facts"].values()}
            | {
                sid
                for refs in c.get("documentary_evidence", {}).values()
                for sid in refs["source_ids"]
            }
        ),
    )


def save_dossier(db, user, variant, catalog, language, preferences, *, ownership=None):
    generated_at = utcnow()
    projections = {
        lang: projection(
            catalog, lang, generated_at=generated_at, preferences=preferences
        ).model_dump(mode="json")
        for lang in ("ru", "az", "en")
    }
    if ownership:
        from app.services.ownership_cost import report_section

        for lang, p in projections.items():
            p["sections"].insert(1, report_section(ownership, lang).model_dump(mode="json"))
    source_ids = {sid for p in projections.values() for sid in p["source_ids"]}
    if catalog.get("commercial_fact_overlay"):
        registries = {
            s.id: s for s in db.scalars(select(SourceRegistry).where(SourceRegistry.id.in_(source_ids)))
        }
        sources = [
            {
                "id": source_id,
                "title": registries[source_id].title,
                "publisher": registries[source_id].title,
                "url": next(
                    f["source_url"] for f in catalog["facts"].values()
                    if f["source_id"] == source_id
                ),
                "retrieved_at": catalog["published_at"],
                "source_type": "COMMERCIAL_FACT_CLAIM",
                "is_demo": False,
            }
            for source_id in sorted(source_ids)
            if source_id in registries
        ]
    else:
        source_ids.add(variant.specification_source_id)
        source_records = db.scalars(select(SourceRecord).where(SourceRecord.id.in_(source_ids)))
        sources = [
            {
                "id": source.id,
                "title": source.title,
                "publisher": source.publisher,
                "url": source.url,
                "retrieved_at": source.retrieved_at.isoformat(),
                "source_type": source.source_type,
                "is_demo": False,
            }
            for source in source_records
        ]
    if ownership:
        for evidence in ownership["evidence"]:
            sources.append(
                {
                    "id": evidence["id"],
                    "title": evidence["kind"],
                    "publisher": evidence["source_id"],
                    "url": evidence["source_url"],
                    "retrieved_at": evidence["observed_at"],
                    "source_type": "OWNERSHIP_EVIDENCE",
                    "is_demo": False,
                    "locator": evidence["locator"],
                }
            )
        for p in projections.values():
            p["source_ids"] = list(
                dict.fromkeys(p["source_ids"] + [e["id"] for e in ownership["evidence"]])
            )
    report = persist_report(
        db,
        user.id,
        language,
        {
            "kind": "MODEL",
            "catalog_variant_id": variant.id,
            "catalog_revision_id": catalog["revision_id"]
            if catalog.get("commercial_fact_overlay") else variant.published_revision_id,
            "vehicle": {
                "make": catalog["make"],
                "model": catalog["model"],
                "year": catalog["model_year"],
                "market": catalog["original_market"],
            },
            "preferences": preferences,
            "vin": None,
            **({"ownership_scenario": ownership["scenario"]} if ownership else {}),
        },
        projections,
        {
            "sources": sources,
            "catalog_snapshot": catalog,
            "official_consumption": fact_value(catalog, "fuel_combined"),
            "official_electricity": fact_value(catalog, "electricity_combined"),
            "catalog_methodology": RANK_VERSION,
            **({"ownership_snapshot": ownership} if ownership else {}),
        },
    )
    return report


def answer_catalog_question(report, question, language):
    """Use the immutable saved facts only. No invented provider/LLM response."""
    import re

    snapshot = report.evidence_bundle["catalog_snapshot"]
    query = normalized(question)
    topics = {
        "engine": ["двиг", "мотор", "muherrik", "motor", "engine"],
        "transmission": ["короб", "qutu", "transmission"],
        "fuel": ["расход", "месяц", "yanacaq", "serf", "ay", "consumption", "month"],
        "body": ["багаж", "кузов", "baqaj", "kuzov", "cargo"],
    }
    keys = [key for key, terms in topics.items() if any(term in query for term in terms)]
    projection_ = report.generated_sections["translations"][language]
    rows = [
        row
        for section in projection_["sections"]
        if section["key"] in keys
        for row in section["rows"]
    ]
    text = "\n".join(row["label"] + ": " + row["value"] for row in rows)
    grounding = {
        "source_ids": sorted({sid for row in rows for sid in row["source_ids"]}),
        "evidence_ids": sorted({eid for row in rows for eid in row["evidence_ids"]}),
        "mode": "FACTUAL_TEMPLATE",
    }
    monthly = re.search(r"(?<!\d)(\d[\d ]{0,5})\s*(?:км|km)", question, re.I)
    if monthly and re.search(r"месяц|month|ayda|aylıq", question, re.I):
        distance = int(monthly[1].replace(" ", ""))
        key = (
            "electricity_combined"
            if fact_value(snapshot, "powertrain") == "BEV"
            else "fuel_combined"
        )
        fact = snapshot["facts"].get(key)
        if fact and distance <= 30000:
            quantity = (Decimal(str(fact["value"])) * distance / 100).quantize(Decimal("0.1"))
            unit = "kWh" if key == "electricity_combined" else "L"
            text += "\n" + tr(
                language,
                f"Сценарий: {distance} км × {fact['value']} / 100 = {quantity} {unit} в месяц. Цена энергии не задана.",
                f"Ssenari: {distance} km × {fact['value']} / 100 = ayda {quantity} {unit}. Enerji qiyməti verilməyib.",
            )
            grounding["calculation"] = {
                "monthly_km": distance,
                "quantity": str(quantity),
                "unit": unit,
            }
            grounding["source_ids"] = sorted(set(grounding["source_ids"] + [fact["source_id"]]))
            grounding["evidence_ids"] = sorted(
                set(grounding["evidence_ids"] + [fact["evidence_id"]])
            )
    limit = tr(
        language,
        "Ответ по сохранённым фактам. Для оценки надёжности, ремонта или состояния конкретной машины данных недостаточно.",
        "Cavab saxlanmış faktlara əsaslanır. Etibarlılıq, təmir və konkret avtomobilin vəziyyətini qiymətləndirmək üçün məlumat yetərli deyil.",
    )
    return (text + "\n\n" if text else "") + limit, grounding
