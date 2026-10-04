"""Chinese configuration catalogue: read side (rows written by cn_catalog_load).

The configuration card has the shape of the US technical card (categories -> rows -> values
with source and display level) plus battery, range and charging. Values are metric in every
language (Chinese-market cars). Owner reports keep their Russian original until the
translation step; severity is never shown (owner reviews state none). Behind the
show_cn_catalog flag: on in development/test (preview), off in production.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.english import pick
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.evidence import KnownIssue, SourceRecord, TechnicalEvidence
from app.services.catalog_buyer import VALUE_LABELS

MARKET = "CN"
HP_PER_KW = Decimal("1.36")
KIND_COLUMN = {
    "engine": KnownIssue.engine_family_key,
    "transmission": KnownIssue.transmission_key,
    "hybrid_system": KnownIssue.hybrid_system_key,
}
KIND_RU = {"engine": "двигатель", "transmission": "коробка", "hybrid_system": "гибридная система"}


def _issue_view(issue: KnownIssue, origin: str, component: str | None = None) -> dict:
    conditions = issue.conditions or {}
    view = {
        "text": issue.description,
        "source": conditions.get("source"),
        "scope": issue.component,
        "origin": origin,
    }
    if conditions.get("more_sources"):
        view["more_sources"] = conditions["more_sources"]
    if component:
        # inherited reports carry the component, not the review car of another model
        view["component"] = component
        return view
    if conditions.get("review_car"):
        view["review_car"] = conditions["review_car"]
    if conditions.get("scope_note"):
        view["scope_note"] = conditions["scope_note"]
    return view


def _order(issue: KnownIssue) -> int:
    return int((issue.conditions or {}).get("order", 0))


def resolved_issues(db, variant: VehicleVariant) -> list[dict]:
    """The model's own owner reports, then the reports of its components (engine, transmission,
    hybrid system, in the record's order), each (source, text) once — the rule of
    samr/tools/resolve_issues.py. Inherited reports name their origin."""
    cn = (variant.specifications or {}).get("cn") or {}
    own = sorted(
        db.scalars(
            select(KnownIssue).where(
                KnownIssue.vehicle_variant_id == variant.id, KnownIssue.market == MARKET
            )
        ),
        key=_order,
    )
    result = [_issue_view(issue, "модель") for issue in own]
    seen = {(i["source"], i["text"]) for i in result}
    for kind, cid in (cn.get("components") or {}).items():
        if not cid or kind not in KIND_COLUMN:
            continue
        rows = sorted(
            db.scalars(
                select(KnownIssue).where(
                    KnownIssue.market == MARKET,
                    KnownIssue.vehicle_variant_id.is_(None),
                    KIND_COLUMN[kind] == cid,
                )
            ),
            key=_order,
        )
        for issue in rows:
            conditions = issue.conditions or {}
            key = (conditions.get("source"), issue.description)
            if key in seen:
                continue
            seen.add(key)
            models = conditions.get("reported_in") or []
            own_model = cn.get("catalogue_model") in models
            origin = (
                f"{KIND_RU[kind]} {conditions.get('component_label', cid)}, "
                f"отзыв по {', '.join(models) or 'неизвестно'}"
                + (" (эта модель)" if own_model else "")
            )
            result.append(_issue_view(issue, origin, cid))
    return result


# ---- configuration card -----------------------------------------------------------------

# category -> ((ru, az, en), fact keys in display order)
CATEGORIES = [
    (
        "powertrain",
        ("Силовая установка", "Güc qurğusu", "Powertrain"),
        [
            "powertrain",
            "hybrid_system_name",
            "platform",
            "system_power_hp",
            "transmission_description",
            "drivetrain",
        ],
    ),
    (
        "engine",
        ("Двигатель", "Mühərrik", "Engine"),
        [
            "engine_code",
            "engine_displacement_cc",
            "aspiration",
            "compression_ratio",
            "engine_power_kw",
            "engine_torque_nm",
        ],
    ),
    (
        "motors",
        ("Электромоторы", "Elektrik mühərrikləri", "Electric motors"),
        [
            "motor_type",
            "motor_count",
            "motor_axle",
            "motor_power_kw",
            "motor_front_kw",
            "motor_rear_kw",
            "motor_torque_nm",
        ],
    ),
    (
        "battery",
        ("Батарея и запас хода", "Batareya və yürüş ehtiyatı", "Battery and range"),
        [
            "battery_kwh",
            "battery_chemistry",
            "battery_brand",
            "battery_supplier",
            "battery_cooling",
            "battery_voltage_v",
            "ev_range_km",
            "consumption_kwh_100km",
            "fuel_l_100km_cn",
        ],
    ),
    (
        "charging",
        ("Зарядка", "Şarj", "Charging"),
        [
            "charging_connector",
            "dc_supported",
            "dc_max_kw",
            "dc_charge_time_h",
            "ac_max_kw",
            "ac_full_h",
        ],
    ),
    ("performance", ("Динамика", "Dinamika", "Performance"), ["accel_0_100_s", "top_speed_kmh"]),
    (
        "body",
        ("Кузов и размеры", "Kuzov və ölçülər", "Body and dimensions"),
        ["length_mm", "width_mm", "height_mm", "wheelbase_mm", "curb_weight_kg"],
    ),
]
LABELS = {
    "powertrain": ("Тип силовой установки", "Güc qurğusunun növü", "Powertrain type"),
    "hybrid_system_name": ("Гибридная система", "Hibrid sistem", "Hybrid system"),
    "platform": ("Платформа", "Platforma", "Platform"),
    "system_power_hp": ("Суммарная мощность системы", "Sistemin ümumi gücü", "System power"),
    "transmission_description": ("Коробка", "Sürətlər qutusu", "Transmission"),
    "drivetrain": ("Привод", "Ötürücü", "Drive"),
    "engine_code": ("Код двигателя", "Mühərrik kodu", "Engine code"),
    "engine_displacement_cc": ("Рабочий объём", "İşçi həcm", "Displacement"),
    "aspiration": ("Наддув", "Hava doldurma", "Aspiration"),
    "compression_ratio": ("Степень сжатия", "Sıxılma dərəcəsi", "Compression ratio"),
    "engine_power_kw": ("Мощность двигателя", "Mühərrikin gücü", "Engine power"),
    "engine_torque_nm": ("Крутящий момент двигателя", "Mühərrikin fırlanma anı", "Engine torque"),
    "motor_type": ("Тип электромотора", "Elektrik mühərrikinin növü", "Motor type"),
    "motor_count": ("Число электромоторов", "Elektrik mühərriklərinin sayı", "Number of motors"),
    "motor_axle": ("Ось электромотора", "Elektrik mühərrikinin oxu", "Motor axle"),
    "motor_power_kw": ("Мощность электромоторов", "Elektrik mühərriklərinin gücü", "Motor power"),
    "motor_front_kw": ("Передний мотор", "Ön mühərrik", "Front motor"),
    "motor_rear_kw": ("Задний мотор", "Arxa mühərrik", "Rear motor"),
    "motor_torque_nm": ("Момент электромоторов", "Elektrik mühərriklərinin anı", "Motor torque"),
    "battery_kwh": ("Ёмкость тяговой батареи", "Dartı batareyasının tutumu", "Traction battery"),
    "battery_chemistry": ("Химия батареи", "Batareyanın kimyası", "Battery chemistry"),
    "battery_brand": ("Марка батареи", "Batareyanın markası", "Battery brand"),
    "battery_supplier": ("Поставщик батареи", "Batareya tədarükçüsü", "Battery supplier"),
    "battery_cooling": ("Охлаждение батареи", "Batareyanın soyudulması", "Battery cooling"),
    "battery_voltage_v": ("Напряжение батареи", "Batareyanın gərginliyi", "Battery voltage"),
    "ev_range_km": ("Запас хода на электричестве", "Elektriklə yürüş ehtiyatı", "Electric range"),
    "consumption_kwh_100km": ("Расход электроэнергии", "Elektrik sərfiyyatı", "Energy use"),
    "fuel_l_100km_cn": ("Расход топлива", "Yanacaq sərfiyyatı", "Fuel consumption"),
    "charging_connector": ("Разъём зарядки", "Şarj yuvası", "Charging connector"),
    "dc_supported": ("Быстрая зарядка DC", "Sürətli DC şarj", "DC fast charging"),
    "dc_max_kw": ("Мощность DC", "DC gücü", "DC power"),
    "dc_charge_time_h": ("Время быстрой зарядки", "Sürətli şarj müddəti", "DC charging time"),
    "ac_max_kw": ("Мощность AC", "AC gücü", "AC power"),
    "ac_full_h": ("Полная зарядка AC", "AC ilə tam şarj", "Full AC charge"),
    "accel_0_100_s": ("Разгон 0–100 км/ч", "0–100 km/saat sürətlənmə", "0–100 km/h"),
    "top_speed_kmh": ("Максимальная скорость", "Maksimal sürət", "Top speed"),
    "length_mm": ("Длина", "Uzunluq", "Length"),
    "width_mm": ("Ширина", "En", "Width"),
    "height_mm": ("Высота", "Hündürlük", "Height"),
    "wheelbase_mm": ("Колёсная база", "Təkər bazası", "Wheelbase"),
    "curb_weight_kg": ("Снаряжённая масса", "Təchiz olunmuş kütlə", "Curb weight"),
}
UNITS = {
    "kW": ("кВт", "kVt", "kW"),
    "PS": ("л.с.", "a.g.", "hp"),
    "N·m": ("Н·м", "N·m", "N·m"),
    "kWh": ("кВт·ч", "kVt·saat", "kWh"),
    "km": ("км", "km", "km"),
    "mm": ("мм", "mm", "mm"),
    "kg": ("кг", "kq", "kg"),
    "s": ("с", "san", "s"),
    "km/h": ("км/ч", "km/saat", "km/h"),
    "h": ("ч", "saat", "h"),
    "V": ("В", "V", "V"),
    "cc": ("см³", "sm³", "cc"),
    "kWh/100km": ("кВт·ч/100 км", "kVt·saat/100 km", "kWh/100 km"),
    "L/100km": ("л/100 км", "l/100 km", "L/100 km"),
}
WORDS = {
    "ICE": ("ДВС", "Daxili yanma mühərriki", "Combustion engine"),
    "HEV": ("Гибрид (HEV)", "Hibrid (HEV)", "Hybrid (HEV)"),
    "PHEV": ("Подключаемый гибрид (PHEV)", "Plug-in hibrid (PHEV)", "Plug-in hybrid (PHEV)"),
    "EREV": (
        "Электромобиль с ДВС-генератором (EREV)",
        "Generatorlu elektromobil (EREV)",
        "Range-extended EV (EREV)",
    ),
    "BEV": ("Электромобиль (BEV)", "Elektromobil (BEV)", "Battery electric (BEV)"),
    "NA": ("Атмосферный", "Atmosfer", "Naturally aspirated"),
    "T": ("Турбонаддув", "Turbo", "Turbocharged"),
    "PMSM": (
        "Синхронный с постоянными магнитами",
        "Daimi maqnitli sinxron",
        "Permanent-magnet synchronous",
    ),
    "front": ("Передняя", "Ön", "Front"),
    "rear": ("Задняя", "Arxa", "Rear"),
    "front+rear": ("Обе оси", "Hər iki ox", "Both axles"),
    "True": ("Есть", "Var", "Yes"),
    "False": ("Нет", "Yoxdur", "No"),
    "Редуктор 1 ст.": ("Редуктор, 1 ступень", "Reduktor, 1 pilləli", "Single-speed reduction gear"),
    "3-ступ. DHT": ("DHT, 3 ступени", "DHT, 3 pilləli", "3-speed DHT"),
    "1-ступ. DHT": ("DHT, 1 ступень", "DHT, 1 pilləli", "Single-speed DHT"),
    "7DCT (сухое/мокрое сцепление — не указано)": (
        "7DCT (тип сцепления не указан)",
        "7DCT (mufta növü göstərilməyib)",
        "7DCT (clutch type not stated)",
    ),
}
SCOPES = {
    "engine": ("двигатель", "mühərrik", "engine"),
    "transmission": ("коробка", "sürətlər qutusu", "transmission"),
    "hybrid_system": ("гибридная система", "hibrid sistem", "hybrid system"),
    "battery": ("батарея", "batareya", "battery"),
    "body": ("кузов", "kuzov", "body"),
    "suspension": ("подвеска", "asqı", "suspension"),
    "interior": ("салон", "salon", "interior"),
    "software": ("электроника и ПО", "elektronika və proqram", "electronics and software"),
    "electrical": ("электрика", "elektrik", "electrical"),
}
COMPONENT_KINDS = {
    "engine": ("Двигатель", "Mühərrik", "Engine"),
    "transmission": ("Коробка", "Sürətlər qutusu", "Transmission"),
    "hybrid_system": ("Гибридная система", "Hibrid sistem", "Hybrid system"),
}
COMPONENT_COLUMN = {
    "engine": TechnicalEvidence.engine_family_key,
    "transmission": TechnicalEvidence.transmission_key,
    "hybrid_system": TechnicalEvidence.hybrid_system_key,
}
OWNERS_REPORT = ("владельцы сообщают", "sahiblər bildirir", "owners report")


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.show_cn_catalog is not None:
        return bool(settings.show_cn_catalog)
    return settings.environment != "production"


def tr(language: str, triple) -> str:
    return pick(language, triple[0], triple[1], triple[2])


def _fmt(n) -> str:
    text = f"{Decimal(str(n)).normalize():f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def show(key: str, value, unit: str | None, language: str) -> str:
    if value is None or value == "" or value == []:
        return ""
    if isinstance(value, dict) and set(value) <= {"min", "max"}:
        text = f"{_fmt(value['min'])}–{_fmt(value['max'])}"
        return f"{text} {tr(language, UNITS[unit])}" if unit in UNITS else text
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    raw = str(value)
    if raw in WORDS:
        return tr(language, WORDS[raw])
    if isinstance(value, str):
        labels = VALUE_LABELS.get(raw) or VALUE_LABELS.get(raw.upper())
        return pick(language, labels[0], labels[1]) if labels else raw
    text = f"{_fmt(value)} {tr(language, UNITS[unit])}" if unit in UNITS else _fmt(value)
    if unit == "kW" and key != "dc_max_kw" and key != "ac_max_kw":
        # power: the catalogue's and turbo.az's horsepower is metric (PS)
        ps = (Decimal(str(value)) * HP_PER_KW).quantize(Decimal("1"))
        text += f" ({ps} {tr(language, UNITS['PS'])})"
    return text


def _qualifier(row: TechnicalEvidence) -> str | None:
    conditions = row.conditions or {}
    if conditions.get("cycle"):
        return str(conditions["cycle"])
    if conditions.get("window_pct"):
        window = str(conditions["window_pct"])
        return window if "%" in window else f"{window} %"
    return None


def _source_view(source: SourceRecord | None, row: TechnicalEvidence) -> dict:
    return {
        "title": source.title if source else None,
        "publisher": source.publisher if source else None,
        "url": source.url if source else None,
        "tier": str(source.source_tier.value) if source else None,
        "locator": row.locator,
    }


def _configuration_row(db, key: str) -> TechnicalEvidence | None:
    return db.scalar(
        select(TechnicalEvidence).where(
            TechnicalEvidence.fact_key == "configuration",
            TechnicalEvidence.market == MARKET,
            TechnicalEvidence.configuration_key == key,
        )
    )


def _components(db, variant: VehicleVariant, language: str) -> list[dict]:
    cn = (variant.specifications or {}).get("cn") or {}
    out = []
    for kind, cid in (cn.get("components") or {}).items():
        if not cid or kind not in COMPONENT_COLUMN:
            continue
        rows = db.scalars(
            select(TechnicalEvidence).where(
                TechnicalEvidence.market == MARKET,
                TechnicalEvidence.configuration_key.is_(None),
                COMPONENT_COLUMN[kind] == cid,
            )
        ).all()
        facts = {r.fact_key: r for r in rows}
        name = facts.get("component_marketing_name") or facts.get("component_name")

        def value(fact_key, facts=facts):
            return facts[fact_key].value if fact_key in facts else None

        out.append(
            {
                "kind": kind,
                "kind_label": tr(language, COMPONENT_KINDS[kind]),
                "key": cid,
                "name": name.value if name else cid,
                "codes": value("component_codes") or [],
                "supplier": value("component_supplier"),
                "generation": value("component_generation"),
                "secondary": bool(name and name.display_level.value == "SECONDARY_NOTE"),
            }
        )
    return out


def weak_points(db, variant: VehicleVariant, language: str) -> list[dict]:
    """Owner reports (own model and inherited through components); never a severity."""
    out = []
    for issue in resolved_issues(db, variant):
        scope = issue.get("scope")
        sources = [issue["source"], *(issue.get("more_sources") or [])]
        out.append(
            {
                "title": issue["text"],
                "component": tr(language, SCOPES[scope]) if scope in SCOPES else scope,
                "inherited": bool(issue.get("component")),
                "origin": issue["origin"],
                "owner_reports": True,
                "note": tr(language, OWNERS_REPORT),
                "sources": [s for s in sources if s],
                "original_language": "ru",
            }
        )
    return out


def summary(variant: VehicleVariant, language: str) -> str:
    parts = []
    if variant.powertrain_type:
        parts.append(tr(language, WORDS[variant.powertrain_type]))
    if variant.battery_kwh is not None:
        parts.append(f"{_fmt(variant.battery_kwh)} {tr(language, UNITS['kWh'])}")
    if variant.power_kw is not None:
        parts.append(show("power", variant.power_kw, "kW", language))
    if variant.engine:
        parts.append(variant.engine)
    if variant.drivetrain:
        parts.append(show("drivetrain", variant.drivetrain, None, language))
    return " · ".join(parts)


def build(db, key: str, language: str = "ru") -> dict | None:
    row = _configuration_row(db, key)
    if row is None:
        return None
    variant = db.get(VehicleVariant, row.vehicle_variant_id)
    cn = (variant.specifications or {}).get("cn") or {}
    facts = db.scalars(
        select(TechnicalEvidence).where(
            TechnicalEvidence.market == MARKET,
            TechnicalEvidence.configuration_key == key,
            TechnicalEvidence.fact_key != "configuration",
            TechnicalEvidence.display_level.in_(("FACT", "SECONDARY_NOTE")),
            TechnicalEvidence.is_demo.is_(False),
        )
    ).all()
    by_key = defaultdict(list)
    for fact in facts:
        by_key[fact.fact_key].append(fact)
    source_ids = {f.source_id for f in facts}
    sources = (
        {s.id: s for s in db.scalars(select(SourceRecord).where(SourceRecord.id.in_(source_ids)))}
        if source_ids
        else {}
    )
    categories = []
    for category, title, keys in CATEGORIES:
        rows = []
        for fact_key in keys:
            values = []
            for fact in sorted(by_key.get(fact_key, []), key=lambda f: str(_qualifier(f))):
                shown = show(fact_key, fact.value, fact.unit, language)
                if not shown:
                    continue
                values.append(
                    {
                        "value": shown,
                        "qualifier": _qualifier(fact),
                        "secondary": fact.display_level.value == "SECONDARY_NOTE",
                        "level": fact.scope_level.value,
                        "source": _source_view(sources.get(fact.source_id), fact),
                    }
                )
            if values:
                label = tr(language, LABELS[fact_key])
                rows.append({"key": fact_key, "label": label, "values": values})
        if rows:
            categories.append({"key": category, "title": tr(language, title), "rows": rows})
    model = variant.generation.model
    notices = []
    listing = cn.get("listing") or {}
    if listing.get("listing_copy"):
        notices.append(
            {
                "kind": "listing_copy",
                "text": tr(
                    language,
                    (
                        "Название модели взято из объявления; характеристики — от модели-близнеца",
                        "Modelin adı elandan götürülüb; xüsusiyyətlər oxşar modelə aiddir",
                        "Model name taken from the listing; specifications are those of its twin",
                    ),
                ),
                "copy_of": listing.get("copy_of"),
            }
        )
    return {
        "configuration_key": key,
        "market": MARKET,
        "year": variant.year_from,
        "variant_id": variant.id,
        "title": f"{model.make.name} {model.name} {variant.year_from}",
        "sub_brand": cn.get("sub_brand"),
        "trim": cn.get("trim_key"),
        "trims": cn.get("trims") or [],
        "summary": summary(variant, language),
        "powertrain_type": variant.powertrain_type,
        "battery_kwh": float(variant.battery_kwh) if variant.battery_kwh is not None else None,
        "categories": categories,
        "components": _components(db, variant, language),
        "weak_points": weak_points(db, variant, language),
        "notices": notices,
        "labels": {
            "secondary": tr(
                language,
                ("по данным справочников", "məlumat kitabçalarına görə", "per reference sources"),
            ),
            "owner_reports": tr(language, OWNERS_REPORT),
            "sources": tr(language, ("Источники", "Mənbələr", "Sources")),
            "model_year": tr(
                language, ("Модельный год (年款)", "Model ili (年款)", "Model year (年款)")
            ),
        },
    }


def _catalog_query():
    return (
        select(TechnicalEvidence, VehicleVariant, VehicleMake.name, VehicleModel.name)
        .join(VehicleVariant, VehicleVariant.id == TechnicalEvidence.vehicle_variant_id)
        .join(VehicleGeneration, VehicleGeneration.id == VehicleVariant.generation_id)
        .join(VehicleModel, VehicleModel.id == VehicleGeneration.model_id)
        .join(VehicleMake, VehicleMake.id == VehicleModel.make_id)
        .where(TechnicalEvidence.fact_key == "configuration", TechnicalEvidence.market == MARKET)
    )


def configurations(db, make=None, model=None, year=None, language="ru", limit=200) -> list[dict]:
    """Configurations of the CN catalogue (preview navigation; nothing is published)."""
    query = _catalog_query()
    if make:
        query = query.where(func.lower(VehicleMake.name) == make.lower())
    if model:
        query = query.where(func.lower(VehicleModel.name) == model.lower())
    if year:
        query = query.where(VehicleVariant.year_from == year)
    query = query.order_by(
        VehicleMake.name,
        VehicleModel.name,
        VehicleVariant.year_from,
        TechnicalEvidence.configuration_key,
    )
    return [
        {
            "configuration_key": row.configuration_key,
            "make": make_name,
            "model": model_name,
            "year": variant.year_from,
            "label": summary(variant, language),
            "variant_id": variant.id,
        }
        for row, variant, make_name, model_name in db.execute(query.limit(limit))
    ]


def facets(db) -> list[dict]:
    """Make / model / model years of the CN catalogue (preview navigation)."""
    years = defaultdict(set)
    for _row, variant, make, model in db.execute(_catalog_query()):
        years[(make, model)].add(variant.year_from)
    return [
        {"make": make, "model": model, "years": sorted(ys)}
        for (make, model), ys in sorted(years.items())
    ]
