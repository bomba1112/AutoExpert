# ruff: noqa: E501
"""Consumer report projection. Internal evidence stays in developer diagnostics."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from app.schemas.paid_report import (
    PaidReportReadiness,
    PaidReportSection,
    PaidVehicleReport,
    ReportParagraph,
    ReportRow,
    VehiclePhotoSet,
)
from app.services.report_evidence_sections import (
    ISSUE_LABELS,
    history_section,
    history_status_text,
    owner_section,
)
from app.services.vehicle_identity import POWER_FIELDS, scope_label
from app.services.vehicle_identity import VERSION as IDENTITY_VERSION


def tr(language: str, ru: str, az: str, en: str) -> str:
    return (ru, az, en)[{"ru": 0, "az": 1, "en": 2}[language]]


LABELS = {
    "size_class": ("Размерный класс EPA", "EPA ölçü sinfi", "EPA size class"),
    "configuration": (
        "Конфигурация каталога EPA",
        "EPA kataloq konfiqurasiyası",
        "EPA catalogue configuration",
    ),
    "electric_kwh_100km": (
        "Электроэнергия EPA, кВт·ч/100 км",
        "EPA elektrik sərfiyyatı, kWh/100 km",
        "EPA electricity, kWh/100 km",
    ),
    "charge_240v_hours": (
        "Зарядка 240 В, ч (EPA)",
        "240 V şarj, saat (EPA)",
        "240 V charging, hours (EPA)",
    ),
    "cargo_cuft": (
        "Багажник EPA, куб. футы",
        "EPA baqaj həcmi, kub fut",
        "EPA luggage volume, cubic feet",
    ),
    "powertrain_type": ("Силовая установка", "Güc qurğusu", "Powertrain"),
    "engine_power_hp": (
        "Мощность ДВС, hp (SAE)",
        "Daxiliyanma mühərrikinin gücü, hp (SAE)",
        "Combustion engine power, SAE hp",
    ),
    "engine_power_kw": ("Мощность двигателя, кВт", "Mühərrik gücü, kW", "Engine power, kW"),
    "motor_power_hp": (
        "Мощность электромотора, hp (SAE)",
        "Elektrik mühərrikinin gücü, hp (SAE)",
        "Electric motor power, SAE hp",
    ),
    "motor_power_kw": (
        "Мощность электромотора, кВт",
        "Elektrik mühərrikinin gücü, kW",
        "Electric motor power, kW",
    ),
    "system_combined_power_hp": (
        "Суммарная мощность гибридной системы, hp (SAE)",
        "Hibrid sisteminin ümumi gücü, hp (SAE)",
        "Combined hybrid system power, SAE hp",
    ),
    "system_combined_power_kw": (
        "Суммарная мощность гибридной системы, кВт",
        "Hibrid sisteminin ümumi gücü, kW",
        "Combined hybrid system power, kW",
    ),
    "battery_capacity_kwh": (
        "Ёмкость тяговой батареи, кВт·ч",
        "Dartı batareyasının tutumu, kWh",
        "Traction battery capacity, kWh",
    ),
    "battery_type": ("Тип тяговой батареи", "Dartı batareyasının növü", "Traction battery type"),
    "hybrid_transmission_type": (
        "Трансмиссия гибридной системы",
        "Hibrid sistemin transmissiyası",
        "Hybrid transmission",
    ),
    "make": ("Марка", "Marka", "Make"),
    "model": ("Модель", "Model", "Model"),
    "year": ("Модельный год", "Model ili", "Model year"),
    "market": ("Рынок исследования", "Araşdırma bazarı", "Research market"),
    "body": ("Кузов", "Kuzov", "Body"),
    "trim": ("Комплектация", "Komplektasiya", "Trim"),
    "doors": ("Двери", "Qapılar", "Doors"),
    "seats": ("Места", "Oturacaqlar", "Seats"),
    "code": ("Код агрегата", "Aqreqat kodu", "Powertrain code"),
    "family": ("Семейство двигателя", "Mühərrik ailəsi", "Engine family"),
    "displacement": ("Рабочий объём", "İş həcmi", "Displacement"),
    "cylinders": ("Цилиндры", "Silindrlər", "Cylinders"),
    "power_hp": ("Мощность, л.с. (SAE)", "Güc, a.g. (SAE)", "Power, SAE hp"),
    "aspiration": ("Наддув", "Üfürmə", "Aspiration"),
    "injection": ("Впрыск", "Püskürtmə", "Injection"),
    "fuel": ("Топливо", "Yanacaq", "Fuel"),
    "fuel_grade": ("Категория топлива EPA", "EPA yanacaq kateqoriyası", "EPA fuel category"),
    "octane_aki": (
        "Минимум по шкале США (AKI)",
        "ABŞ şkalası üzrə minimum (AKI)",
        "Minimum US octane (AKI)",
    ),
    "timing": ("Привод ГРМ", "Qazpaylama ötürməsi", "Timing drive"),
    "oil": ("Моторное масло", "Mühərrik yağı", "Engine oil"),
    "oil_capacity_l": ("Масло с фильтром", "Filtrlə yağ həcmi", "Oil with filter"),
    "oil_interval": ("Регламент масла", "Yağ dəyişmə qaydası", "Oil service"),
    "type": ("Тип коробки", "Qutunun növü", "Transmission type"),
    "gears": ("Число передач", "Pillə sayı", "Gears"),
    "fluid": ("Жидкость коробки", "Qutu mayesi", "Transmission fluid"),
    "drivetrain": ("Привод", "Ötürücü", "Drivetrain"),
    "construction": ("Конструкция", "Quruluş", "Construction"),
    "architecture": ("Оборудование", "Avadanlıq", "Equipment"),
    "length_mm": ("Длина", "Uzunluq", "Length"),
    "width_mirrors_mm": ("Ширина с зеркалами", "Güzgülərlə en", "Width including mirrors"),
    "wheelbase_mm": ("Колёсная база", "Təkər bazası", "Wheelbase"),
    "official": ("Официальный расход EPA", "Rəsmi EPA sərfiyyatı", "Official EPA consumption"),
    "owner_reported": ("По записям владельцев", "Sahiblərin qeydləri üzrə", "Owner-reported"),
}
VALUES = {
    "ICE": (
        "ДВС (без гибридной системы)",
        "Daxili yanma mühərriki (hibridsiz)",
        "Internal combustion (non-hybrid)",
    ),
    "HEV": (
        "Гибрид HEV (без внешней зарядки)",
        "Hibrid HEV (xarici şarjsız)",
        "HEV hybrid (non-plug-in)",
    ),
    "PHEV": ("Подключаемый гибрид PHEV", "Şəbəkədən doldurulan hibrid PHEV", "Plug-in hybrid PHEV"),
    "MHEV": ("Мягкий гибрид MHEV", "Yumşaq hibrid MHEV", "Mild hybrid MHEV"),
    "BEV": ("Электромобиль BEV", "Elektromobil BEV", "Battery electric BEV"),
    "Lithium-Ion/Li-Ion": ("Литий-ионная", "Litium-ion", "Lithium-ion"),
    "4WD/4-Wheel Drive/4x4": (
        "Полный (категория vPIC AWD/4WD)",
        "Tam (vPIC AWD/4WD kateqoriyası)",
        "All driven wheels (vPIC AWD/4WD category)",
    ),
    "Sport Utility Vehicle [SUV]/Multipurpose Vehicle [MPV]": (
        "Кроссовер / SUV",
        "Krossover / SUV",
        "SUV / MPV",
    ),
    "USA": ("США", "ABŞ", "United States"),
    "Sedan/Saloon": ("Седан", "Sedan", "Sedan"),
    "Gasoline": ("Бензин", "Benzin", "Gasoline"),
    "Electricity": ("Электроэнергия", "Elektrik enerjisi", "Electricity"),
    "DIRECT_DRIVE": (
        "Одноступенчатый редуктор",
        "Birpilləli reduktor",
        "Single-speed reduction gear",
    ),
    "Compact Cars": (
        "Компактный автомобиль по классификации EPA",
        "EPA üzrə kompakt avtomobil",
        "EPA compact car class",
    ),
    "Midsize Cars": (
        "Средний класс по классификации EPA",
        "EPA üzrə orta sinif",
        "EPA midsize car class",
    ),
    "Large Cars": (
        "Большой автомобиль по классификации EPA",
        "EPA üzrə böyük avtomobil",
        "EPA large car class",
    ),
    "Small Sport Utility Vehicle 4WD": (
        "Компактный кроссовер по классификации EPA",
        "EPA üzrə kompakt krossover",
        "EPA small SUV class",
    ),
    "Small Sport Utility Vehicle 2WD": (
        "Компактный кроссовер по классификации EPA",
        "EPA üzrə kompakt krossover",
        "EPA small SUV class",
    ),
    "Diesel": ("Дизель", "Dizel", "Diesel"),
    "Regular Gasoline": (
        "Обычный бензин по классификации США",
        "ABŞ təsnifatına görə adi benzin",
        "Regular gasoline",
    ),
    "Premium Gasoline": (
        "Премиальный бензин по классификации США",
        "ABŞ təsnifatına görə premium benzin",
        "Premium gasoline",
    ),
    "TURBO": ("Турбонаддув", "Turbo", "Turbocharged"),
    "DIRECT_INJECTION": ("Непосредственный впрыск", "Birbaşa püskürtmə", "Direct injection"),
    "AUTOMATIC": ("Автоматическая", "Avtomatik", "Automatic"),
    "MANUAL": ("Механическая", "Mexaniki", "Manual"),
    "CVT": ("Вариатор", "Variator", "CVT"),
    "FWD": ("Передний", "Ön", "Front-wheel drive"),
    "RWD": ("Задний", "Arxa", "Rear-wheel drive"),
    "AWD": ("Полный", "Tam", "All-wheel drive"),
    "4WD": ("Полный", "Tam", "Four-wheel drive"),
    "TIMING_BELT": ("Зубчатый ремень", "Dişli kəmər", "Timing belt"),
    "MACPHERSON_INTEGRAL_LINK": (
        "Спереди — независимая MacPherson; сзади — независимая многорычажная Integral Link",
        "Öndə müstəqil MacPherson; arxada müstəqil çoxqollu Integral Link",
        "Independent MacPherson front; independent integral-link rear",
    ),
    "ELECTRIC_PARKING_BRAKE": (
        "Электрический стояночный тормоз",
        "Elektrik dayanacaq əyləci",
        "Electric parking brake",
    ),
    "ELECTRIC_POWER_STEERING": (
        "Электроусилитель руля",
        "Elektrik sükan gücləndiricisi",
        "Electric power steering",
    ),
    "TPMS": ("Контроль давления в шинах", "Təkər təzyiqinə nəzarət", "Tire pressure monitoring"),
}
TITLES = {
    "vehicle": ("Автомобиль", "Avtomobil", "Vehicle"),
    "engine": ("Двигатель", "Mühərrik", "Engine"),
    "transmission": ("Коробка и привод", "Sürətlər qutusu və ötürücü", "Transmission and drive"),
    "chassis": (
        "Подвеска, рулевое и тормоза",
        "Asqı, sükan və əyləclər",
        "Suspension, steering and brakes",
    ),
    "body": ("Кузов", "Kuzov", "Body"),
    "electrical": ("Электрика", "Elektrik sistemi", "Electrical systems"),
    "fuel": ("Расход и эксплуатация", "Sərfiyyat və istismar", "Consumption and running"),
    "weak_points": ("Слабые места", "Zəif nöqtələr", "Weak points"),
    "owner_reviews": ("Отзывы владельцев", "Sahiblərin rəyləri", "Owner reviews"),
    "recalls": (
        "Отзывные кампании и бюллетени",
        "Geri çağırmalar və bülletenlər",
        "Recalls and technical bulletins",
    ),
    "history": (
        "История VIN и фотографии",
        "VIN tarixçəsi və şəkillər",
        "VIN history and photographs",
    ),
    "expert_verdict": ("Экспертный вывод", "Ekspert rəyi", "Expert conclusion"),
}


def fact_display(finding: dict, language: str) -> tuple[str, str] | None:
    key, value = finding["subtopic"], finding.get("value")
    if value is None or finding.get("status") == "INSUFFICIENT_DATA" or key not in LABELS:
        return None
    label = tr(language, *LABELS[key])
    if key == "official":
        unit = tr(language, "л/100 км", "l/100 km", "L/100 km")
        text = tr(
            language,
            f"Город {value['city']} · трасса {value['highway']} · смешанный {value['combined']} {unit}",
            f"Şəhər {value['city']} · magistral {value['highway']} · qarışıq {value['combined']} {unit}",
            f"City {value['city']} · highway {value['highway']} · combined {value['combined']} {unit}",
        )
    elif key == "owner_reported":
        if not value.get("combined_l_100km"):
            return None
        text = tr(
            language,
            f"{value['combined_l_100km']} л/100 км · {value['sample_size']} добровольных записей",
            f"{value['combined_l_100km']} l/100 km · {value['sample_size']} könüllü qeyd",
            f"{value['combined_l_100km']} L/100 km · {value['sample_size']} voluntary records",
        )
    elif key == "oil_interval":
        text = tr(
            language,
            f"По индикатору ресурса; не реже {value['months']} месяцев или {value['km']:,} км при обычных условиях",
            f"Yağ resursu göstəricisinə görə; adi şəraitdə ən gec {value['months']} ay və ya {value['km']:,} km",
            f"Follow the oil-life monitor; at most {value['months']} months or {value['km']:,} km in normal service",
        )
    elif isinstance(value, (str, int, float)):
        text = tr(language, *VALUES[str(value)]) if str(value) in VALUES else str(value)
        if key == "power_hp":
            text = f"{float(value):g}"
        if key in {"displacement", "oil_capacity_l"}:
            text += tr(language, " л", " l", " L")
        if key.endswith("_mm"):
            text += tr(language, " мм", " mm", " mm")
        # Only codes, proper names, units and numeric values may pass through untranslated.
        if (
            language != "en"
            and key
            in {
                "body",
                "fuel",
                "type",
                "drivetrain",
                "construction",
                "architecture",
                "aspiration",
                "injection",
            }
            and str(value) not in VALUES
        ):
            return None
    else:
        return None
    return label, text


def paid_readiness(profile, history=None) -> PaidReportReadiness:  # noqa: ANN001
    depth = profile.dossier_seed.get("knowledge_depth", {})
    findings = [
        f
        for f in depth.get("findings", [])
        if f["status"] == "CONFIRMED" and f.get("value") is not None
    ]
    keys = {(f["topic"], f["subtopic"]) for f in findings}
    source_ids = {s.id for s in profile.sources}
    evidence_ids = {e.id for e in profile.evidence}
    checks = {
        "vehicle_identity": all(
            ("identity", key) in keys for key in ("make", "model", "year", "body")
        ),
        "market": bool(profile.market),
        "engine": ("engine", "displacement") in keys
        and len([f for f in findings if f["topic"] == "engine"]) >= 4,
        "transmission": ("transmission", "type") in keys
        and (
            ("transmission", "gears") in keys
            or any(
                f["topic"] == "transmission" and f["subtopic"] == "type" and f["value"] == "CVT"
                for f in findings
            )
        ),
        "useful_transmission": len([f for f in findings if f["topic"] == "transmission"]) >= 2,
        "drivetrain": ("identity", "drivetrain") in keys,
        "basic_chassis": ("suspension", "construction") in keys
        and any((topic, "construction") in keys for topic in ("steering", "brakes")),
        "fuel_if_available": not depth.get("epa_candidates")
        or ("fuel_consumption", "official") in keys,
        "recall_research": "recalls" in profile.dossier_seed.get("completed_capabilities", []),
        "provenance": bool(findings)
        and all(
            set(f["source_ids"]) <= source_ids
            and set(f["evidence_ids"]) <= evidence_ids
            and f["source_ids"]
            and f["evidence_ids"]
            for f in findings
        ),
        "no_critical_contradictions": not any(
            c["resolution"] == "UNRESOLVED" and c["topic"] in {"identity", "engine", "transmission"}
            for c in depth.get("contradictions", [])
        ),
    }
    integrity = profile.dossier_seed.get("identity_integrity", {})
    if integrity.get("version") == IDENTITY_VERSION:
        from app.services.vehicle_identity import integrity_from_findings

        integrity = integrity_from_findings(
            depth.get("target", {}), depth.get("findings", []), depth.get("contradictions", [])
        )
    fields = integrity.get("fields", {})
    checks["identity_integrity"] = (
        integrity.get("version") == IDENTITY_VERSION and integrity.get("state") == "RESOLVED"
    )
    checks["powertrain_type"] = fields.get("powertrain_type", {}).get("value") in {
        "ICE",
        "HEV",
        "PHEV",
        "BEV",
        "MHEV",
    }
    checks["fuel_resolved"] = fields.get("fuel", {}).get("status") == "CONFIRMED"
    research = (history or {}).get("history_research", {})
    attempts = research.get("attempts", [])
    checks["vin_history_checked"] = bool(attempts) and any(
        a.get("query_completed")
        and a.get("state") in {"NO_RECORDS", "AVAILABLE"}
        and a.get("query", {}).get("vin") == (history or {}).get("vin")
        and a.get("provenance")
        for a in attempts
    )
    missing = [key for key, passed in checks.items() if not passed]
    return PaidReportReadiness(
        identity_state=integrity.get("state", "IDENTITY_INCOMPLETE"),
        state="NOT_ENOUGH_DATA_FOR_PAID_REPORT" if missing else "READY",
        can_purchase=not missing,
        missing_requirements=missing,
        checks=checks,
    )


def relevant_recalls(profile):
    candidates = profile.dossier_seed.get("knowledge_depth", {}).get("epa_candidates", [])
    conventional = (
        len(candidates) == 1
        and not candidates[0].get("fuelType2")
        and "hybrid" not in str(candidates[0].get("atvType", "")).casefold()
    )
    result = []
    for evidence in profile.evidence:
        conditions = evidence.conditions
        if not conditions.get("campaign_number"):
            continue
        if conventional and re.search(
            re.escape(profile.model) + r"\s+(?:PHEV|plug-in hybrid|Hybrid)\s+vehicles",
            conditions.get("summary", ""),
            re.I,
        ):
            continue
        result.append(evidence)
    return result


def build_paid_report(check) -> PaidVehicleReport:  # noqa: ANN001
    profile, language = check.profile, check.language
    depth = profile.dossier_seed.get("knowledge_depth", {})
    integrity = profile.dossier_seed.get("identity_integrity", {})
    findings = depth.get("findings", [])
    # A pre-gate cache must not keep presenting unverified variant specifications.
    if integrity.get("version") != IDENTITY_VERSION:
        findings = [f for f in findings if f["topic"] not in {"engine", "transmission"}]
    readiness = paid_readiness(profile, check.full_history_payload)
    sections = {
        key: PaidReportSection(key=key, title=tr(language, *title)) for key, title in TITLES.items()
    }
    vehicle = sections["vehicle"]
    identity = next(
        (e for e in profile.evidence if e.conditions.get("consumer_kind") == "vehicle_identity"),
        None,
    )
    vehicle.rows.append(
        ReportRow(
            key="vin",
            label="VIN",
            value=check.normalized_vin,
            evidence_ids=[identity.id] if identity else [],
            source_ids=[identity.source_id] if identity else [],
        )
    )
    for finding in findings:
        if finding["topic"] in {"engine", "transmission"} and finding["status"] != "CONFIRMED":
            continue
        display = fact_display(finding, language)
        if not display:
            continue
        topic, key = finding["topic"], finding["subtopic"]
        row = ReportRow(
            key=f"{topic}.{key}",
            label=display[0],
            value=display[1],
            evidence_ids=finding["evidence_ids"],
            source_ids=finding["source_ids"],
        )
        destination = {
            "identity": "vehicle",
            "fuel_consumption": "fuel",
            "suspension": "chassis",
            "steering": "chassis",
            "brakes": "chassis",
        }.get(topic, topic)
        if destination in sections:
            if destination == "chassis":
                row.label = tr(
                    language,
                    *{
                        "suspension": ("Подвеска", "Asqı", "Suspension"),
                        "steering": ("Рулевое", "Sükan", "Steering"),
                        "brakes": ("Тормоза", "Əyləclər", "Brakes"),
                    }[topic],
                )
            sections[destination].rows.append(row)
        if topic in {"engine", "transmission", "body"} and key in {
            "family",
            "displacement",
            *POWER_FIELDS,
            "fuel",
            "type",
            "gears",
            "length_mm",
            "width_mirrors_mm",
            "wheelbase_mm",
        }:
            vehicle.rows.append(row)
        if topic == "identity" and key == "drivetrain":
            sections["transmission"].rows.append(row)
    dossier_sections = {item["key"]: item for item in check.dossier_snapshot.get("sections", [])}
    recalls = relevant_recalls(profile)
    recall_ids = {e.id for e in recalls}
    for claim in dossier_sections.get("recalls_tsb", {}).get("claims", []):
        if claim.get("kind") != "recall" or not set(claim.get("evidence_ids", [])) & recall_ids:
            continue
        evidence = next(e for e in recalls if e.id in claim["evidence_ids"])
        raw = evidence.conditions
        summary = raw.get("summary", "").casefold()
        detail = " ".join(
            part
            for part in [claim.get("heading"), claim.get("text"), claim.get("why_it_matters")]
            if part
        )
        detail = (
            tr(
                language,
                "Отзывная кампания для части автомобилей этого модельного года. ",
                "Bu model ilinin bəzi avtomobilləri üçün geri çağırma. ",
                "Recall campaign for some vehicles of this model year. ",
            )
            + detail
        )
        electrical_detail = None
        if "rearview camera" in summary:
            electrical_detail = tr(
                language,
                "Камера заднего вида: программная ошибка может давать пустое изображение или оставлять его на экране после выхода из заднего хода. Заводское решение — обновление программного обеспечения.",
                "Arxa görüntü kamerası: proqram xətası boş görüntü verə və ya geriyə hərəkət bitdikdən sonra görüntünü ekranda saxlaya bilər. Zavod həlli proqram təminatının yenilənməsidir.",
                "Rearview camera: a software error may cause a blank image or leave the image displayed after reversing ends. The factory remedy is a software update.",
            )
        elif "engine block heater" in summary:
            electrical_detail = tr(
                language,
                "Электрический подогреватель двигателя, если установлен: трещина и утечка антифриза могут вызвать короткое замыкание и пожар при подключении к сети. Производитель рекомендует не подключать его до устранения неисправности.",
                "Elektrik mühərrik qızdırıcısı quraşdırılıbsa: çat və antifriz sızması şəbəkəyə qoşulduqda qısaqapanma və yanğına səbəb ola bilər. İstehsalçı təmirədək onu şəbəkəyə qoşmamağı tövsiyə edir.",
                "Engine block heater, if fitted: a crack and coolant leak may cause a short circuit and fire when plugged in. The manufacturer advises against plugging it in until remedied.",
            )
        if electrical_detail:
            detail = f"{raw['campaign_number']} · {scope_label('MODEL_YEAR', language)}. {electrical_detail}"
            sections["electrical"].paragraphs.append(
                ReportParagraph(
                    text=detail, source_ids=claim["source_ids"], evidence_ids=claim["evidence_ids"]
                )
            )
        sections["recalls"].paragraphs.append(
            ReportParagraph(
                text=detail,
                source_ids=claim["source_ids"],
                evidence_ids=claim["evidence_ids"],
            )
        )
    if recalls:
        sections["recalls"].paragraphs.append(
            ReportParagraph(
                text=tr(
                    language,
                    "Кампании найдены для модели и года. Статус выполнения по этому VIN в подключённой базе отсутствует.",
                    "Kampaniyalar model və il üçün tapılıb. Bu VIN üzrə icra statusu qoşulmuş bazada yoxdur.",
                    "Campaigns match the model year. Completion status for this VIN is unavailable in the connected database.",
                ),
                source_ids=list({e.source_id for e in recalls}),
                evidence_ids=[e.id for e in recalls],
            )
        )
    owner_count = depth.get("fuel", {}).get("owner_reported", {}).get("sample_size", 0)
    if owner_count:
        owner_evidence = [
            e for e in profile.evidence if e.conditions.get("subtopic") == "owner_reported"
        ]
        sections["owner_reviews"].paragraphs.append(
            ReportParagraph(
                text=tr(
                    language,
                    f"В My MPG доступны {owner_count} записи владельцев о расходе для совпавшей конфигурации. Это добровольные замеры, а не отзывы о надёжности. Для типичного расхода выборка {'слишком мала' if owner_count < 5 else 'приведена отдельно в разделе расхода'}.",
                    f"Uyğun komplektasiya üçün My MPG-də sahiblərin {owner_count} sərfiyyat qeydi var. Bunlar könüllü ölçmələrdir, etibarlılıq rəyləri deyil. Sərfiyyat nümunəsi ayrıca qiymətləndirilir.",
                    f"My MPG contains {owner_count} owner fuel logs for the matched configuration. These voluntary measurements are not reliability reviews. {'The sample is too small to establish typical consumption.' if owner_count < 5 else 'Owner consumption is listed separately.'}",
                ),
                evidence_ids=[e.id for e in owner_evidence],
                source_ids=list({e.source_id for e in owner_evidence}),
            )
        )
    if sections["fuel"].rows:
        sections["fuel"].paragraphs.append(
            ReportParagraph(
                text=tr(
                    language,
                    "Официальные показатели рассчитаны по циклу EPA; л/100 км переведены из американских MPG. Они не являются прогнозом расхода в Баку.",
                    "Rəsmi göstəricilər EPA sınaq dövrünə aiddir; ABŞ MPG vahidi l/100 km-ə çevrilib. Bunlar Bakı üçün sərfiyyat proqnozu deyil.",
                    "Official values use the EPA test cycle, converted from US MPG to L/100 km. They are not a forecast for driving in Baku.",
                ),
                evidence_ids=[eid for r in sections["fuel"].rows for eid in r.evidence_ids],
                source_ids=list({sid for r in sections["fuel"].rows for sid in r.source_ids}),
            )
        )
    # Keep the empty state compact and make no claim that an empty sample proves reliability.
    sections["weak_points"].collapsed = True
    sections["weak_points"].paragraphs.append(
        ReportParagraph(
            text=tr(
                language,
                "Повторяющиеся неисправности пока не подтверждены независимыми источниками. Жалобы NHTSA не превращаются автоматически в список слабых мест.",
                "Təkrarlanan nasazlıqlar hələ müstəqil mənbələrlə təsdiqlənməyib. NHTSA şikayətləri avtomatik zəif nöqtəyə çevrilmir.",
                "Independent sources have not yet established recurring faults. NHTSA complaints are not automatically promoted to weak points.",
            )
        )
    )
    owner_reliability = check.full_history_payload.get("owner_reliability", {})
    aggregation = owner_reliability.get("issue_aggregation") or depth.get("issue_aggregation", {})
    issues = aggregation.get("known_issues", [])
    supported_issues = [item for item in issues if item.get("title") == "coolant_intrusion"]
    if supported_issues:
        sections["weak_points"].paragraphs = []
        sections["weak_points"].collapsed = False
        for issue in supported_issues:
            liters = issue["affected_variants"].get("displacement")
            program = ", ".join(issue.get("documents", []))
            detail = tr(
                language,
                f"Двигатель {liters} л: попадание охлаждающей жидкости в цилиндры. Симптомы — снижение уровня антифриза, дым из выхлопной трубы и пропуски зажигания. Проблема описана производителем и совпадает с несколькими отдельными жалобами. Применимость ограничена версиями и датами выпуска из заводского документа; это не диагноз этого VIN.",
                f"{liters} l mühərrik: soyuducu mayenin silindrlərə keçməsi. Əlamətlər — antifriz səviyyəsinin azalması, egzoz tüstüsü və alışma buraxmaları. Problem istehsalçı tərəfindən təsvir edilib və ayrı şikayətlərlə uyğun gəlir. Tətbiq zavod sənədindəki versiya və istehsal tarixləri ilə məhdudlaşır; bu VIN üçün diaqnoz deyil.",
                f"{liters} L engine: coolant intrusion into the cylinders. Symptoms include coolant loss, exhaust smoke and misfires. The manufacturer describes the concern and separate complaints corroborate it. Applicability is limited to the versions and build dates in the factory document; it is not a diagnosis of this VIN.",
            )
            sections["weak_points"].paragraphs.append(
                ReportParagraph(
                    text=detail, source_ids=issue["source_ids"], evidence_ids=issue["evidence_ids"]
                )
            )
            sections["weak_points"].paragraphs = []
            for suffix, label, value in (
                (
                    "system",
                    tr(language, "Система", "Sistem", "System"),
                    tr(
                        language,
                        f"Двигатель {liters} л",
                        f"{liters} l mühərrik",
                        f"{liters} L engine",
                    ),
                ),
                (
                    "problem",
                    tr(language, "Проблема", "Problem", "Problem"),
                    tr(
                        language,
                        "Попадание антифриза в цилиндры; возможен серьёзный ремонт двигателя.",
                        "Antifrizin silindrlərə keçməsi; ciddi mühərrik təmiri tələb oluna bilər.",
                        "Coolant intrusion into the cylinders; major engine repair may be needed.",
                    ),
                ),
                (
                    "scope",
                    tr(language, "Применимость", "Tətbiq", "Applicability"),
                    tr(
                        language,
                        f"{profile.year} {profile.make} {profile.model}, {liters} л. Ограничения по дате выпуска и заводскому списку VIN — в программе {program}.",
                        f"{profile.year} {profile.make} {profile.model}, {liters} l. İstehsal tarixi və zavod VIN siyahısı məhdudiyyətləri {program} proqramındadır.",
                        f"{profile.year} {profile.make} {profile.model}, {liters} L. Build-date and factory VIN-list limits are defined in program {program}.",
                    ),
                ),
                (
                    "symptoms",
                    tr(language, "Проявления", "Əlamətlər", "Symptoms"),
                    tr(
                        language,
                        "Потеря антифриза, дым из выхлопной трубы, пропуски зажигания.",
                        "Antifriz itkisi, egzoz tüstüsü, alışma buraxmaları.",
                        "Coolant loss, exhaust smoke and misfires.",
                    ),
                ),
                (
                    "basis",
                    tr(language, "Основание", "Əsas", "Basis"),
                    tr(
                        language,
                        "Заводской документ и несколько отдельных жалоб по совпавшему объёму двигателя. Частота поломок из этой выборки не рассчитывается.",
                        "Zavod sənədi və uyğun mühərrik həcmi üzrə ayrı şikayətlər. Bu nümunədən nasazlıq tezliyi hesablanmır.",
                        "A factory document and separate complaints matching engine displacement. This sample does not establish a failure rate.",
                    ),
                ),
            ):
                sections["weak_points"].rows.append(
                    ReportRow(
                        key=f"{issue['id']}.{suffix}",
                        label=label,
                        value=value,
                        source_ids=issue["source_ids"],
                        evidence_ids=issue["evidence_ids"],
                    )
                )
            sections["engine"].paragraphs.append(
                ReportParagraph(
                    text=tr(
                        language,
                        "Главный выявленный риск двигателя — попадание антифриза в цилиндры; подробности и применимость — в разделе «Слабые места».",
                        "Mühərrik üzrə əsas aşkar risk antifrizin silindrlərə keçməsidir; təfərrüat və tətbiq «Zəif nöqtələr» bölməsindədir.",
                        "The main identified engine concern is coolant intrusion; details and applicability are in Weak points.",
                    ),
                    source_ids=issue["source_ids"],
                    evidence_ids=issue["evidence_ids"],
                )
            )
            sections["recalls"].paragraphs.append(
                ReportParagraph(
                    text=tr(
                        language,
                        f"Заводская программа обслуживания {program} описывает риск проникновения антифриза и обновление управления охлаждением. Это исторический документ, не обещание действующей бесплатной кампании.",
                        f"Zavodun {program} servis proqramı antifrizin keçməsi riskini və soyutma idarəetməsinin yenilənməsini təsvir edir. Bu tarixi sənəddir, hazırda pulsuz kampaniya vədi deyil.",
                        f"Factory service program {program} describes coolant intrusion risk and a cooling-control update. This is a historical document, not a promise of current free coverage.",
                    ),
                    source_ids=issue["source_ids"],
                    evidence_ids=issue["evidence_ids"],
                )
            )
    real_history = check.full_history_payload if not check.is_demo else {}
    # Unknown issue keys do not disappear. The coolant-specific text above is a
    # translation template for an evidence key, never a Ford/VIN detection rule.
    for issue in issues:
        if issue in supported_issues:
            continue
        sections["weak_points"].collapsed = False
        sections["weak_points"].paragraphs.append(
            ReportParagraph(
                text=tr(
                    language,
                    *ISSUE_LABELS.get(
                        issue["title"],
                        (
                            "Сообщения о неисправности требуют проверки применимости",
                            "Nasazlıq məlumatlarının tətbiqi yoxlanmalıdır",
                            "Reported concern requires an applicability check",
                        ),
                    ),
                )
                + tr(
                    language,
                    ". Вывод основан на сопоставленных источниках, не на частоте поломок.",
                    ". Nəticə tutuşdurulmuş mənbələrə əsaslanır, nasazlıq tezliyinə deyil.",
                    ". This finding is based on corroborated sources, not a failure rate.",
                ),
                source_ids=issue["source_ids"],
                evidence_ids=issue["evidence_ids"],
            )
        )
    if owner_reliability:
        sections["owner_reviews"] = owner_section(owner_reliability, language)
    real_sources = {s.id for s in profile.sources} | {
        s["id"] for s in getattr(check, "source_snapshot", []) if not s.get("is_demo")
    }
    events = [
        e
        for e in real_history.get("timeline", [])
        if not e.get("is_demo") and e.get("source_ids") and set(e["source_ids"]) <= real_sources
    ]
    for item in events:
        if not item.get("is_demo"):
            sections["history"].paragraphs.append(
                ReportParagraph(
                    text=f"{item['date']} · {item['summary']}",
                    source_ids=item.get("source_ids", []),
                )
            )
    for key in ("auctions", "damage_details", "odometer_records"):
        for item in real_history.get(key, []):
            if (
                item.get("is_demo")
                or not item.get("source_ids")
                or not set(item["source_ids"]) <= real_sources
            ):
                continue
            if key == "auctions":
                text = (
                    f"{item['date']} · {item['sale_price']} {item['currency']} · {item['damage']}"
                )
            elif key == "damage_details":
                text = f"{item['area']} · {item['description']}"
            else:
                text = f"{item['date']} · {item['value']} {item['unit']}"
            sections["history"].paragraphs.append(
                ReportParagraph(text=text, source_ids=item["source_ids"])
            )
    photo_sets = [
        VehiclePhotoSet.model_validate(item) for item in real_history.get("photo_sets", [])
    ]
    if real_history.get("history_research"):
        sections["history"] = history_section(real_history, language)
    photo_sets = [
        item
        for item in photo_sets
        if item.vin == check.normalized_vin and item.source_id in real_sources and item.photos
    ]
    # A final, vehicle-specific conclusion derives only from displayed facts.
    by_key = {row.key: row.value for section in sections.values() for row in section.rows}
    bits = [
        by_key.get(key)
        for key in (
            "identity.body",
            "engine.family",
            "engine.displacement",
            "transmission.type",
            "identity.drivetrain",
        )
        if by_key.get(key)
    ]
    opening = f"{profile.year} {profile.make} {profile.model}: " + "; ".join(bits) + "."
    paragraphs = [opening]
    if (
        by_key.get("identity.seats") == "5"
        and by_key.get("identity.doors") == "4"
        and any(
            f["topic"] == "transmission" and f["subtopic"] == "type" and f["value"] == "AUTOMATIC"
            for f in findings
        )
        and by_key.get("suspension.construction")
    ):
        paragraphs.append(
            tr(
                language,
                "Практические плюсы конфигурации — пятиместный салон с четырьмя дверями, автоматическая коробка и независимая подвеска обеих осей.",
                "Komplektasiyanın praktik üstünlükləri — dörd qapılı beşyerlik salon, avtomatik qutu və hər iki oxda müstəqil asqıdır.",
                "Practical strengths of this configuration are its five-seat, four-door cabin, automatic transmission and independent suspension at both ends.",
            )
        )
    if supported_issues:
        paragraphs.append(
            tr(
                language,
                "Основной технический риск — система охлаждения двигателя: подтверждённая для части этой модификации проблема может привести к серьёзному ремонту. При продолжении выбора нужны диагностика потери антифриза и пропусков зажигания, а также документы о ранее выполненных работах по двигателю.",
                "Əsas texniki risk mühərrikin soyutma sistemidir: bu modifikasiyanın bir hissəsi üçün təsdiqlənmiş problem ciddi təmirə səbəb ola bilər. Seçim davam edərsə, antifriz itkisi və alışma buraxmaları üzrə diaqnostika, həmçinin əvvəlki mühərrik işlərinin sənədləri lazımdır.",
                "The main technical risk concerns engine cooling: the documented issue affecting some examples of this configuration can lead to major repair. Further consideration should include coolant-loss and misfire diagnostics and records of previous engine work.",
            )
        )
    if all(
        by_key.get(key) for key in ("engine.oil", "transmission.fluid", "fuel_consumption.official")
    ):
        paragraphs.append(
            tr(
                language,
                "Для обслуживания найдены заводские требования к маслу и жидкости коробки; расход можно сопоставить с официальным циклом EPA.",
                "Qulluq üçün zavodun yağ və qutu mayesi tələbləri tapılıb; sərfiyyatı rəsmi EPA dövrü ilə müqayisə etmək olar.",
                "Manufacturer oil and transmission-fluid requirements are available; consumption can be compared with the official EPA cycle.",
            )
        )
    if recalls:
        paragraphs.append(
            tr(
                language,
                f"Отзывные кампании уровня модели: {len(recalls)}. До решения о покупке нужны уточнение применимости и статус выполнения по VIN.",
                f"Əsas təsdiqlənmiş diqqət mövzusu model üzrə {len(recalls)} geri çağırma kampaniyasıdır. Alış qərarından əvvəl VIN üzrə icra statusu lazımdır.",
                f"Model-level recall campaigns: {len(recalls)}. VIN applicability and completion status are needed before a purchase decision.",
            )
        )
    has_history = bool(
        events or real_history.get("events") or real_history.get("auctions") or photo_sets
    )
    show_history_section = has_history or bool(real_history.get("history_research"))
    if has_history:
        history_summary = " ".join(p.text for p in sections["history"].paragraphs[:3])
        photo_count = sum(len(group.photos) for group in photo_sets)
        paragraphs.append(
            tr(
                language,
                f"По конкретному VIN: {history_summary} Фотографий из источников: {photo_count}.",
                f"Konkret VIN üzrə: {history_summary} Mənbələrdən şəkillər: {photo_count}.",
                f"For this VIN: {history_summary} Source photographs: {photo_count}.",
            )
        )
    if not has_history and not show_history_section:
        paragraphs.extend(history_status_text(real_history, language))
    paragraphs.append(
        tr(
            language,
            "Продолжить рассмотрение можно, если продавец предоставит историю обслуживания и выполнения указанных кампаний. Окончательное решение требует осмотра конкретного автомобиля.",
            "Satıcı qulluq tarixçəsini və göstərilən kampaniyaların icrasını təqdim edərsə, avtomobili nəzərdən keçirməyə davam etmək olar. Son qərar konkret avtomobilə baxış tələb edir.",
            "Further consideration is reasonable if the seller supplies maintenance history and evidence that the listed campaigns were completed. A final decision requires inspection of the specific vehicle.",
        )
    )
    all_eids = sorted(
        {eid for section in sections.values() for row in section.rows for eid in row.evidence_ids}
        | {eid for issue in supported_issues for eid in issue["evidence_ids"]}
        | {e.id for e in recalls}
    )
    all_sids = sorted(
        {sid for section in sections.values() for row in section.rows for sid in row.source_ids}
        | {sid for section in sections.values() for p in section.paragraphs for sid in p.source_ids}
        | {group.source_id for group in photo_sets}
        | {sid for issue in supported_issues for sid in issue["source_ids"]}
        | {e.source_id for e in recalls}
    )
    sections["expert_verdict"].paragraphs = [
        ReportParagraph(text=p, evidence_ids=all_eids, source_ids=all_sids) for p in paragraphs
    ]
    identity_notice = tr(
        language,
        "Точная модификация силовой установки не подтверждена.",
        "Güc qurğusunun dəqiq modifikasiyası təsdiqlənməyib.",
        "The exact powertrain configuration is not confirmed.",
    )
    if integrity.get("state") != "RESOLVED":
        sections["expert_verdict"].paragraphs.insert(0, ReportParagraph(text=identity_notice))
    for conflict in integrity.get("critical_conflicts", []):
        alternatives = "; ".join(str(a["value"]) for a in conflict["alternatives"])
        label = tr(language, *LABELS.get(conflict["subtopic"], (conflict["subtopic"],) * 3))
        message = tr(
            language,
            f"Противоречие источников — {label}: {alternatives}. Значение для VIN не подтверждено.",
            f"Mənbələr arasında ziddiyyət — {label}: {alternatives}. VIN üzrə dəyər təsdiqlənməyib.",
            f"Source conflict — {label}: {alternatives}. The value for this VIN is unconfirmed.",
        )
        destination = sections.get(conflict["topic"], vehicle)
        destination.paragraphs.append(
            ReportParagraph(
                text=message,
                evidence_ids=conflict["evidence_ids"],
                source_ids=sorted(
                    {sid for a in conflict["alternatives"] for sid in a["source_ids"]}
                ),
            )
        )
    ptype = integrity.get("fields", {}).get("powertrain_type", {}).get("value")
    if ptype in {"HEV", "PHEV", "MHEV"}:
        known = {f["subtopic"] for f in findings if f["status"] == "CONFIRMED"}
        for key in POWER_FIELDS:
            if key not in known:
                sections["engine"].rows.append(
                    ReportRow(
                        key="engine." + key,
                        label=tr(language, *LABELS[key]),
                        value=tr(language, "Не подтверждено", "Təsdiqlənməyib", "Not confirmed"),
                    )
                )
        sections["engine"].paragraphs.append(
            ReportParagraph(
                text=tr(
                    language,
                    "Мощность двигателя и суммарная мощность гибридной системы — разные величины. Мощности двигателя и электромотора нельзя просто складывать.",
                    "Mühərrik gücü və hibrid sistemin ümumi gücü fərqli göstəricilərdir; sadəcə toplanmır.",
                    "Engine power and combined hybrid system power are different values; engine and motor ratings must not simply be added.",
                ),
                evidence_ids=all_eids,
                source_ids=all_sids,
            )
        )
    for section in sections.values():
        if not section.rows and not section.paragraphs:
            section.collapsed = True
    order = {
        "vehicle": "vin identity.make identity.model identity.year identity.trim identity.market identity.body identity.doors identity.seats engine.family engine.displacement engine.power_hp transmission.type transmission.gears identity.drivetrain engine.fuel body.length_mm body.width_mirrors_mm body.wheelbase_mm",
        "engine": "engine.family engine.displacement engine.cylinders engine.aspiration engine.power_hp engine.fuel engine.octane_aki engine.injection engine.timing engine.oil engine.oil_capacity_l engine.oil_interval engine.fuel_grade",
        "transmission": "transmission.type transmission.gears identity.drivetrain transmission.fluid",
        "chassis": "suspension.construction steering.construction brakes.construction",
    }
    for key, fields in order.items():
        priorities = {field: i for i, field in enumerate(fields.split())}
        sections[key].rows.sort(key=lambda row: priorities.get(row.key, 100))
    included = [
        section for key, section in sections.items() if key != "history" or show_history_section
    ]
    return PaidVehicleReport(
        language=language,
        vin=check.normalized_vin,
        title=f"{profile.year} {profile.make} {profile.model}",
        subtitle=tr(language, "Отчёт об автомобиле", "Avtomobil hesabatı", "Vehicle report"),
        generated_at=datetime.now(UTC),
        readiness=readiness,
        notice=(identity_notice + " " if integrity.get("state") != "RESOLVED" else "")
        + tr(
            language,
            "Предварительный отчёт. Оплата недоступна.",
            "İlkin hesabat. Ödəniş mümkün deyil.",
            "Preliminary report. Payment unavailable.",
        )
        if not readiness.can_purchase
        else None,
        # Existing sections and source panels carry the correctness corrections.
        sections=included,
        photo_sets=photo_sets,
        source_ids=sorted(real_sources),
    )
