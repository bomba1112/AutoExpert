# ruff: noqa: E501
"""US technical facts for one configuration (next-stage prompt, stage C).

Assembles the scoped rows of the US technical database (technical_evidence, known_issues,
maintenance_schedule_items) whose applicability matches one configuration: line, generation,
model year, engine family, powertrain, drive, model designation, edition and body, trim. Rules:
- the most specific level wins: configuration -> engine family -> generation; within a level a
  row that names the configuration's model designation wins over a general one, and a FACT wins
  over a SECONDARY_NOTE stated for the same trim / designation;
- FACT is shown; SECONDARY_NOTE is shown marked "по данным справочников"; OWNER_REPORTS only in
  the weak points ("владельцы сообщают"); HIDDEN_CONFLICT never;
- metric units (conversions only through app.services.tech_units); every value keeps its source;
- an empty field or category is left out (no "no data" rows).
The database is only read. Served only while the show_us_tech_facts flag is on (preview/dev by
default, off in production).
"""

from __future__ import annotations

import hashlib
import re
import threading
import time
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.english import pick
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.evidence import KnownIssue, MaintenanceScheduleItem, SourceRecord, TechnicalEvidence
from app.models.translations import ContentTranslation
from app.services import fuel_advice, unit_display
from app.services.catalog_buyer import VALUE_LABELS
from app.services.tech_units import convert

LEVEL_RANK = {"CONFIGURATION": 0, "ENGINE": 1, "TRANSMISSION": 1, "GENERATION": 2}
DISPLAY_RANK = {"FACT": 0, "SECONDARY_NOTE": 1}
# fact keys that are not characteristics of the card (NHTSA communications, EPA mpg, internal keys)
NOT_LOADED = ("nhtsa_mfr_communication", "nhtsa_complaint_pattern", "carcomplaints_problem", "epa_city_mpg",
              "epa_highway_mpg", "epa_combined_mpg", "configuration")

# category -> (ru, az, fact keys in display order)
CATEGORIES = [
    ("engine", "Двигатель", "Mühərrik", [
        "engine_description", "hybrid_engine_description", "engine_code", "platform_code", "engine_layout",
        "engine_displacement_l", "engine_displacement_cc", "cylinders", "aspiration", "injection", "valvetrain",
        "timing_drive", "bore_stroke_mm", "bore_stroke_in", "compression_ratio", "power_hp", "power_rpm",
        "system_power_hp", "torque_lb_ft", "torque_rpm", "electric_motor", "traction_battery",
    ]),
    ("transmission", "Коробка", "Sürətlər qutusu", [
        "transmission_description", "transmission_description_epa", "transmission_code", "drivetrain",
    ]),
    ("fuel", "Топливо", "Yanacaq", [
        "powertrain", "fuel_type", "octane_aki", "octane_ron", "fuel_tank_l", "fuel_combined",
    ]),
    ("fluids", "Масла и жидкости", "Yağlar və mayelər", [
        "engine_oil_viscosity", "engine_oil_specification", "engine_oil_oem_approval", "engine_oil_alternatives",
        "engine_oil_capacity_l", "engine_oil_capacity_drain_refill_l", "engine_oil_capacity_without_filter_l",
        "engine_oil_topup_standards", "engine_oil_topup_limit_l", "engine_oil_consumption_max_l_per_1000km",
        "coolant", "coolant_description", "coolant_capacity_l", "inverter_coolant_capacity_l",
        "transmission_fluid", "transmission_fluid_capacity_l", "brake_fluid", "spark_plug",
    ]),
    ("body", "Кузов и размеры", "Kuzov və ölçülər", [
        "body", "length_mm", "width_mm", "height_mm", "wheelbase_mm", "track_front_mm", "track_rear_mm",
        "ground_clearance", "turning_circle_m", "curb_weight_kg", "weight_distribution_front_rear_pct", "towing_kg",
    ]),
    ("chassis", "Подвеска и тормоза", "Asqı və əyləclər", [
        "front_suspension", "rear_suspension", "steering", "front_brakes", "rear_brakes", "tires", "wheel_size_in",
        "tire_pressure_front_kpa", "tire_pressure_rear_kpa", "wheel_nut_torque_nm",
    ]),
    ("interior", "Салон и практичность", "Salon və praktiklik", [
        "seats", "passenger_volume_l", "cargo_l", "cargo_max_l",
    ]),
]
# a key shown only when its preferred twin has no value
FALLBACK_OF = {"bore_stroke_in": "bore_stroke_mm", "engine_displacement_cc": "engine_displacement_l",
               "coolant_description": "coolant", "transmission_description_epa": "transmission_description"}
LABELS = {
    "engine_description": ("Двигатель", "Mühərrik"), "hybrid_engine_description": ("Гибридная установка", "Hibrid qurğu"),
    "engine_code": ("Код двигателя", "Mühərrik kodu"), "platform_code": ("Код кузова / поколения", "Kuzov / nəsil kodu"),
    "engine_layout": ("Компоновка", "Düzülüş"), "engine_displacement_l": ("Рабочий объём", "İşçi həcm"),
    "engine_displacement_cc": ("Рабочий объём", "İşçi həcm"), "cylinders": ("Цилиндры", "Silindrlər"),
    "aspiration": ("Наддув", "Hava doldurma"), "injection": ("Впрыск", "Püskürtmə"), "valvetrain": ("Газораспределение", "Qazpaylama"),
    "timing_drive": ("Привод ГРМ", "Qazpaylama ötürücüsü"), "bore_stroke_mm": ("Диаметр × ход поршня", "Diametr × porşen gedişi"),
    "bore_stroke_in": ("Диаметр × ход поршня", "Diametr × porşen gedişi"), "compression_ratio": ("Степень сжатия", "Sıxılma dərəcəsi"),
    "power_hp": ("Мощность", "Güc"), "power_rpm": ("Обороты максимальной мощности", "Maksimal güc dövrləri"),
    "system_power_hp": ("Суммарная мощность системы", "Sistemin ümumi gücü"), "torque_lb_ft": ("Крутящий момент", "Fırlanma anı"),
    "torque_rpm": ("Обороты максимального момента", "Maksimal an dövrləri"), "electric_motor": ("Электромотор", "Elektrik mühərriki"),
    "traction_battery": ("Тяговая батарея", "Dartı batareyası"),
    "transmission_description": ("Коробка", "Sürətlər qutusu"), "transmission_description_epa": ("Коробка", "Sürətlər qutusu"),
    "transmission_code": ("Код коробки", "Qutunun kodu"), "drivetrain": ("Привод", "Ötürücü"),
    "powertrain": ("Силовая установка", "Güc qurğusu"), "fuel_type": ("Топливо", "Yanacaq"),
    "octane_aki": ("Октановое число AKI (США)", "AKI oktan ədədi (ABŞ)"), "octane_ron": ("Октановое число RON", "RON oktan ədədi"),
    "fuel_tank_l": ("Топливный бак", "Yanacaq çəni"), "fuel_combined": ("Расход, смешанный цикл EPA", "Sərfiyyat, EPA qarışıq dövrü"),
    "engine_oil_viscosity": ("Вязкость масла", "Yağın özlülüyü"), "engine_oil_specification": ("Класс масла", "Yağ sinfi"),
    "engine_oil_oem_approval": ("Допуск производителя", "İstehsalçı icazəsi"),
    "engine_oil_alternatives": ("Допустимая замена масла", "Yağın yolverilən əvəzi"),
    "engine_oil_capacity_l": ("Масло с фильтром", "Filtrlə yağ"),
    "engine_oil_capacity_drain_refill_l": ("Масло при замене", "Dəyişmə zamanı yağ"),
    "engine_oil_capacity_without_filter_l": ("Масло без фильтра", "Filtrsiz yağ"),
    "engine_oil_topup_standards": ("Масло для экстренного долива", "Təcili əlavə üçün yağ"),
    "engine_oil_topup_limit_l": ("Предел экстренного долива", "Təcili əlavə həddi"),
    "engine_oil_consumption_max_l_per_1000km": ("Допустимый расход масла", "Yolverilən yağ sərfi"),
    "coolant": ("Охлаждающая жидкость", "Soyuducu maye"), "coolant_description": ("Охлаждающая жидкость", "Soyuducu maye"),
    "coolant_capacity_l": ("Объём охлаждающей жидкости", "Soyuducu mayenin həcmi"),
    "inverter_coolant_capacity_l": ("Охлаждение инвертора", "İnvertorun soyudulması"),
    "transmission_fluid": ("Жидкость коробки", "Qutunun mayesi"), "transmission_fluid_capacity_l": ("Объём жидкости коробки", "Qutu mayesinin həcmi"),
    "brake_fluid": ("Тормозная жидкость", "Əyləc mayesi"), "spark_plug": ("Свечи зажигания", "Alışdırma şamları"),
    "body": ("Кузов", "Kuzov"), "length_mm": ("Длина", "Uzunluq"), "width_mm": ("Ширина", "En"), "height_mm": ("Высота", "Hündürlük"),
    "wheelbase_mm": ("Колёсная база", "Təkər bazası"), "track_front_mm": ("Колея спереди", "Ön iz"), "track_rear_mm": ("Колея сзади", "Arxa iz"),
    "ground_clearance": ("Клиренс", "Klirens"), "turning_circle_m": ("Диаметр разворота", "Dönmə diametri"),
    "curb_weight_kg": ("Снаряжённая масса", "Təchiz olunmuş kütlə"),
    "weight_distribution_front_rear_pct": ("Развесовка перед/зад", "Ön/arxa çəki paylanması"),
    "towing_kg": ("Масса буксируемого прицепа", "Yedək qoşqusunun kütləsi"),
    "front_suspension": ("Подвеска спереди", "Ön asqı"), "rear_suspension": ("Подвеска сзади", "Arxa asqı"), "steering": ("Рулевое управление", "Sükan idarəsi"),
    "front_brakes": ("Тормоза спереди", "Ön əyləclər"), "rear_brakes": ("Тормоза сзади", "Arxa əyləclər"), "tires": ("Шины", "Şinlər"),
    "wheel_size_in": ("Диаметр дисков", "Disklərin diametri"), "tire_pressure_front_kpa": ("Давление в шинах спереди", "Ön şin təzyiqi"),
    "tire_pressure_rear_kpa": ("Давление в шинах сзади", "Arxa şin təzyiqi"), "wheel_nut_torque_nm": ("Момент затяжки колёсных гаек", "Təkər qaykalarının bərkidilmə anı"),
    "seats": ("Мест", "Oturacaq sayı"), "passenger_volume_l": ("Объём салона", "Salonun həcmi"), "cargo_l": ("Багажник", "Baqaj"),
    "cargo_max_l": ("Багажник со сложенными сиденьями", "Qatlanmış oturacaqlarla baqaj"),
}
UNIT_WORDS = {"L": ("л", "l", "L"), "mm": ("мм", "mm", "mm"), "kg": ("кг", "kq", "kg"), "m": ("м", "m", "m"), "kPa": ("кПа", "kPa", "kPa"),
              "rpm": ("об/мин", "dövr/dəq", "rpm"), "kW": ("кВт", "kVt", "kW"), "N·m": ("Н·м", "N·m", "N·m"),
              "L/100km": ("л/100 км", "l/100 km", "L/100 km"), "cm3": ("см³", "sm³", "cc"), "%": ("%", "%", "%"),
              "L/1000km": ("л на 1000 км", "l / 1000 km", "L per 1,000 km")}
UNIT_OF = {"engine_oil_consumption_max_l_per_1000km": "L/1000km", "engine_displacement_l": "L", "engine_oil_topup_limit_l": "L"}
EXTRA_WORDS = {"TURBOCHARGED": ("Турбонаддув", "Turbo"), "CHAIN": ("Цепь", "Zəncir"), "BELT": ("Ремень", "Kəmər"),
               "4WD": ("Полный 4WD", "Tam 4WD")}
JOBS = {
    "engine_oil_and_filter": ("Масло и масляный фильтр", "Yağ və yağ filtri"),
    "engine_oil": ("Моторное масло", "Mühərrik yağı"), "oil_filter": ("Масляный фильтр", "Yağ filtri"),
    "engine_air_filter": ("Воздушный фильтр двигателя", "Mühərrikin hava filtri"), "cabin_air_filter": ("Салонный фильтр", "Salon filtri"),
    "spark_plugs": ("Свечи зажигания", "Alışdırma şamları"), "brake_fluid": ("Тормозная жидкость", "Əyləc mayesi"),
    "engine_coolant": ("Охлаждающая жидкость", "Soyuducu maye"), "cooling_system": ("Система охлаждения", "Soyutma sistemi"),
    "transmission_fluid": ("Жидкость АКПП", "Avtomatik qutunun mayesi"), "dct_fluid": ("Жидкость робота DCT", "DCT robot qutusunun mayesi"),
    "dual_clutch_fluid": ("Жидкость робота DSG / S tronic", "DSG / S tronic qutusunun mayesi"),
    "manual_transmission_fluid": ("Масло МКПП", "Mexaniki qutunun yağı"), "transfer_case_fluid": ("Масло раздаточной коробки", "Paylayıcı qutunun yağı"),
    "differential_fluid": ("Масло дифференциала", "Diferensialın yağı"), "awd_coupling_fluid": ("Масло муфты полного привода", "Tam ötürücü muftasının yağı"),
    "timing_belt": ("Ремень ГРМ", "Qazpaylama kəməri"), "accessory_drive_belt": ("Приводной ремень", "Ötürücü kəmər"),
    "tire_rotation": ("Перестановка колёс", "Təkərlərin yerdəyişməsi"), "fuel_filter": ("Топливный фильтр", "Yanacaq filtri"),
    "brakes": ("Тормоза", "Əyləclər"), "battery": ("Аккумулятор", "Akkumulyator"), "battery_12v": ("Аккумулятор 12 В", "12 V akkumulyator"),
    "front_suspension": ("Подвеска", "Asqı"), "suspension": ("Подвеска", "Asqı"), "exhaust_system": ("Выхлопная система", "İşlənmiş qaz sistemi"),
    "wiper_blades": ("Щётки стеклоочистителя", "Şüşətəmizləyən fırçalar"), "ac_desiccant": ("Осушитель кондиционера", "Kondisioner qurudücüsü"),
    "diesel_exhaust_fluid": ("Жидкость AdBlue / DEF", "AdBlue / DEF mayesi"), "steering": ("Рулевое управление", "Sükan idarəsi"),
    "drive_shafts": ("Приводные валы и пыльники", "Ötürücü vallar və tozluqlar"), "valve_clearance": ("Зазоры клапанов", "Klapan araboşluqları"),
    "fuel_system": ("Топливная система", "Yanacaq sistemi"), "parking_brake": ("Стояночный тормоз", "Dayanacaq əyləci"),
    "brake_lines": ("Тормозные трубки и тросы", "Əyləc boruları və trosları"), "clutch_fluid": ("Жидкость сцепления", "Mufta mayesi"),
    "drive_shaft_boots": ("Пыльники приводных валов", "Ötürücü val tozluqları"), "propeller_shaft": ("Карданный вал", "Kardan valı"),
    "evap_system": ("Система улавливания паров топлива", "Yanacaq buxarlarının tutulma sistemi"),
    "evap_vapor_lines": ("Трубки улавливания паров топлива", "Yanacaq buxarı boruları"), "fuel_lines": ("Топливные трубки", "Yanacaq boruları"),
    "fluid_levels": ("Уровни жидкостей", "Maye səviyyələri"), "gas_struts": ("Газовые упоры", "Qaz dayaqları"),
    "idle_speed": ("Обороты холостого хода", "Boş gediş dövrləri"), "inverter_coolant": ("Охлаждающая жидкость инвертора", "İnvertorun soyuducu mayesi"),
    "key_fob_battery": ("Батарейка ключа", "Açar batareyası"), "steering_linkage": ("Рулевые тяги и шарниры", "Sükan çubuqları və oynaqları"),
}
ACTIONS = {"REPLACE": ("замена", "dəyişmə"), "INSPECT": ("проверка", "yoxlama"), "ROTATE": ("перестановка", "yerdəyişmə"),
           "ADJUST": ("регулировка", "tənzimləmə"), "CLEAN": ("очистка", "təmizləmə")}
SYSTEMS = {"OIL_LIFE_MONITOR": ("по бортовой системе ресурса масла", "yağ resursunun bort sisteminə görə"),
           "MAINTENANCE_MINDER": ("по Maintenance Minder", "Maintenance Minder üzrə"),
           "CBS": ("по бортовой системе CBS (по состоянию)", "CBS bort sisteminə görə (vəziyyətə görə)"),
           "SERVICE_A_B": ("Service A / Service B", "Service A / Service B")}
SEVERITY = {"LOW": ("низкая", "aşağı"), "MINOR": ("низкая", "aşağı"), "MEDIUM": ("средняя", "orta"), "HIGH": ("высокая", "yüksək"),
            "CRITICAL": ("критическая", "kritik")}
SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "MINOR": 3, "LOW": 3}
PROBABILITY = {"RARE": ("редко", "nadir"), "OCCASIONAL": ("иногда", "bəzən"), "COMMON": ("часто", "tez-tez")}

# --- applicability -------------------------------------------------------------------------------
BODY_FAMILY = [(re.compile(r"wagon|touring|avant|allroad|sportwagen|estate", re.I), "WAGON"),
               (re.compile(r"gran turismo|\bgt\b", re.I), "GT"),
               (re.compile(r"convertible|cabrio|roadster|spyder", re.I), "CONVERTIBLE"),
               (re.compile(r"coupe", re.I), "COUPE"),
               (re.compile(r"hatch|\b5dr\b|\b3dr\b", re.I), "HATCH"),
               (re.compile(r"sedan|\b4dr\b", re.I), "SEDAN")]
BODY_NAMES = {"WAGON": "wagon", "GT": "Gran Turismo", "CONVERTIBLE": "cabriolet", "COUPE": "coupe", "HATCH": "hatchback"}
BODY_WORDS = {"sedan", "sedans", "sports", "wagon", "touring", "coupe", "convertible", "gran", "turismo", "gt", "cabrio",
              "cabriolet", "hatchback", "hatch", "suv", "4dr", "2dr", "5dr", "3dr", "avant", "sportback", "van"}
DRIVE_WORDS = {"xdrive": "AWD", "4matic": "AWD", "quattro": "AWD", "4motion": "AWD", "awd": "AWD", "4wd": "AWD",
               "sdrive": "RWD", "fwd": "FWD", "rwd": "RWD"}
DRIVES = {"fwd": "FWD", "front wheel drive": "FWD", "front-wheel drive": "FWD", "rwd": "RWD", "rear wheel drive": "RWD",
          "rear-wheel drive": "RWD", "awd": "AWD", "all wheel drive": "AWD", "all-wheel drive": "AWD", "4wd": "AWD",
          "4x4": "AWD", "2wd": "2WD"}
MODEL_TOKEN = re.compile(r"^(?:m?\d{3}[a-z]{0,2}\+?|m\d{1,3}[a-z]?|x\d|z\d|i\d|(?:a|s|rs|q|sq)\d|[a-z]{1,3}\d{2,3}[a-z]{0,2}\+?)$")
NOT_MODEL = re.compile(r"^my\d{2}$")
FILLER = {"with", "and", "the", "all", "models", "model", "line", "if", "equipped", "tech", "sheet", "product", "info", "new",
          "all-new", "first-ever", "-", "us", "key", "dimensions", "preliminary", "options", "data", "edition", "series",
          "canadian", "vehicle", "activity", "stands", "apart"}
POWER_WORDS = re.compile(r"^(?:hybrid|plug-in|phev|hev|energi|diesel|tdi|bluetec|electric|ev|e-tron|bev|tfsi|\d\.\dl?|l)$")


def text_hash(text: str) -> str:
    """The key of a translation: sha256 of the English text with whitespace collapsed
    (the same as scripts/i18n_collect.py)."""
    return hashlib.sha256(" ".join(str(text or "").split()).encode("utf-8")).hexdigest()


class Translator:
    """Russian / Azerbaijani text of an English original from content_translations (owner
    decision 2026-10-03: the original stays, the translation is in separate fields). A text
    without a translation is shown as it is."""

    def __init__(self, db, language: str):
        self.db = db
        self.column = {"az": ContentTranslation.text_az, "en": ContentTranslation.text_en}.get(language, ContentTranslation.text_ru)
        self.cache: dict = {}

    def __call__(self, kind: str, original):
        if not original or not str(original).strip():
            return original
        key = (kind, text_hash(original))
        if key not in self.cache:
            self.cache[key] = self.db.scalar(select(self.column).where(
                ContentTranslation.kind == kind, ContentTranslation.source_hash == key[1]))
        return self.cache[key] or original


def _enum(value) -> str | None:
    return None if value is None else str(getattr(value, "value", value))


def tr(language: str, pair) -> str:
    return pick(language, pair[0], pair[1], pair[2] if len(pair) > 2 else None)


def norm_text(text) -> str:
    """Lower case, parentheses dropped; a model letter group and its number joined ("c 300" ->
    "c300", "rs 5" -> "rs5", "es 300h" -> "es300h")."""
    text = str(text or "").lower().replace("®", "").replace("™", "")
    text = re.sub(r"\([^)]*\)", " ", text)
    return re.sub(r"\b(a|s|rs|q|sq|c|e|g|gl|glc|gle|gla|glb|gls|cla|cls|cle|sl|slk|ml|es|is|gs|ls|nx|rx|gx|lx|ux|rc|lc)"
                  r"\s(\d{1,3}[a-z]{0,2}\+?)(?=\s|$|[,/;])", r"\1\2", text)


def tokens(text) -> set[str]:
    return {t for t in re.split(r"[\s/,;]+", norm_text(text)) if t}


def body_family(text) -> str | None:
    return next((b for p, b in BODY_FAMILY if p.search(str(text or ""))), None)


def number(value):
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def displacements(text) -> set[Decimal]:
    """Displacements a label names: "2.5L", "G1.6 T-GDi", "sonata 2 0t"."""
    text = str(text or "")
    found = {Decimal(m.group(1)) for m in re.finditer(r"(?<![\d.])(\d\.\d)(?!\d)", text)}
    found |= {Decimal(f"{m.group(1)}.{m.group(2)}") for m in re.finditer(r"\b(\d) (\d)t?\b", norm_text(text))}
    return found


def powertrains_named(text) -> set[str] | None:
    """Powertrains a label names; None when it names none."""
    t = norm_text(text)
    if re.search(r"plug-in|\bphev\b|energi", t):
        rest = t.replace("plug-in hybrid", "")
        return {"PHEV"} | ({"HEV"} if re.search(r"\bhybrid\b", rest) else set())
    if re.search(r"\bhybrid\b|\bhev\b", t):
        return {"HEV"}
    if re.search(r"\bdiesel\b|\btdi\b|bluetec", t):
        return {"DIESEL"}
    if re.search(r"e-tron", t):
        return {"BEV", "PHEV"}
    if re.search(r"\belectric\b|\bev\b|\bbev\b", t):
        return {"BEV"}
    return None


def model_tokens_of(text, ignore: set[str]) -> set[str]:
    return {t for t in tokens(text) if MODEL_TOKEN.match(t) and not NOT_MODEL.match(t)} - ignore


class Target:
    """The configuration as the database's configuration row describes it."""

    def __init__(self, row: TechnicalEvidence, facts: dict, designations: list[str], generation_labels: list[str],
                 model_name: str):
        cond = row.conditions or {}
        ident = cond.get("identity") or {}
        self.row = row
        self.key = row.configuration_key
        self.make_id, self.generation_id = row.make_id, row.generation_id
        self.year = row.year_from
        self.engine = ident.get("engine_family_key") or row.engine_family_key
        self.drivetrain = DRIVES.get(str(ident.get("drivetrain") or facts.get("drivetrain") or "").lower())
        self.displacement = number(ident.get("displacement_l") or facts.get("engine_displacement_l"))
        self.transmission = str(ident.get("epa_transmission") or facts.get("transmission_description_epa") or "")
        self.cylinders = number(ident.get("cylinders") or facts.get("cylinders"))
        power = str(facts.get("powertrain") or ident.get("powertrain") or "").upper()
        self.diesel = power == "DIESEL" or "-diesel-" in (self.key or "")
        self.powertrain = "DIESEL" if self.diesel else power
        self.line = str(cond.get("line") or model_name)
        self.ignore = tokens(self.line) | tokens(model_name) | tokens(self.line.replace("-", " "))
        self.designations = designations
        self.design_tokens = [tokens(d) - self.ignore for d in designations]
        self.all_tokens = set().union(*self.design_tokens) if self.design_tokens else set()
        self.model_tokens = {t for d in self.design_tokens for t in d if MODEL_TOKEN.match(t) and not NOT_MODEL.match(t)}
        self.bodies = {body_family(d) or "DEFAULT" for d in designations} or {"DEFAULT"}
        self.generation_bodies = {body_family(d) or "DEFAULT" for d in generation_labels}
        # words that tell one configuration of the generation from another ("GLI", "Si", "Type R", "Eco")
        self.generation_words = set().union(*(tokens(d) - self.ignore for d in generation_labels)) if generation_labels else set()
        self.generation_design_tokens = [tokens(d) - self.ignore for d in generation_labels]
        self.aspiration = str(ident.get("aspiration") or facts.get("aspiration") or "").upper()
        self.trims: set[str] | None = None

    def powertrain_ok(self, allowed, diesel_named: bool = False) -> bool:
        allowed = {str(a).upper() for a in allowed}
        if not self.powertrain or self.powertrain in allowed:
            return True
        # a diesel takes rows filed as combustion ("ICE") only when they name the diesel
        return self.powertrain == "DIESEL" and "ICE" in allowed and diesel_named

    def drive_ok(self, drive) -> bool:
        wanted = DRIVES.get(str(drive).strip().lower())
        if not wanted or not self.drivetrain:
            return True
        if wanted == "2WD":
            return self.drivetrain in ("FWD", "RWD")
        return wanted == self.drivetrain

    def displacement_ok(self, values: set[Decimal]) -> bool:
        return not values or self.displacement is None or any(abs(v - self.displacement) <= Decimal("0.06") for v in values)

    def body_ok(self, body: str | None) -> bool:
        if body is None:
            return True
        if body == "SEDAN":
            return bool(self.bodies & {"DEFAULT", "SEDAN"})
        # a body word no configuration of the generation names describes the whole line ("CLA coupe")
        return body in self.bodies or body not in self.generation_bodies

    def strict_designation(self, label) -> str | None:
        """The configuration designation the label names with nothing but body words or the model
        name added ("330i xDrive" fits "330i xDrive Sports Wagon"; "330i" does not fit "330i xDrive")."""
        extra = BODY_WORDS | self.ignore
        for alt in re.split(r",|/|;|\band\b", norm_text(label)):
            b = tokens(alt) - extra
            for design, a in zip(self.designations, self.design_tokens, strict=True):
                a = a - BODY_WORDS
                if a and b and a == b:
                    return design
        return None

    def distinguishing(self, words: set[str]) -> bool:
        """The label carries a word that names another configuration of the generation."""
        return bool((words & self.generation_words) - self.all_tokens)

    def trim_label_fits(self, label) -> bool:
        """A trim label ("SE / Sport", "LONG RANGE AWD", "COROLLA 4DR SEDAN L/LE") fits when one of
        its alternatives either uses no word of the generation's EPA designations or uses only
        words of this configuration's designations ("MID RANGE" is not the "Long Range AWD")."""
        for alt in re.split(r"/|,|;", norm_text(label)):
            words = {w for w in tokens(alt) - self.ignore - BODY_WORDS - FILLER if not POWER_WORDS.match(w)}
            if not words & self.generation_words or words <= self.all_tokens:
                return True
        return False

    def transmission_ok(self, text) -> bool:
        t, mine = str(text).lower(), self.transmission.lower()
        if not mine:
            return True
        if "manual" in t and "automatic" not in t:
            return mine.startswith("manual")
        if "semi-automatic" in t:
            return "(am" in mine
        if "cvt" in t or "variable" in t:
            return "variable" in mine or "(av" in mine
        if "automatic" in t and mine.startswith("manual"):
            return False
        gears = re.search(r"(\d+)[ -]speed", t)
        mine_gears = re.findall(r"(\d+)", mine)
        return not (gears and mine_gears and gears.group(1) != mine_gears[-1])

    @property
    def automated_manual(self) -> bool:
        return "(am" in self.transmission.lower()

    @property
    def manual(self) -> bool:
        return self.transmission.lower().startswith("manual")

    def transmission_value_ok(self, text) -> bool:
        """A gearbox description agrees with the configuration's EPA gearbox: type (dual clutch,
        continuously variable, manual) and number of gears."""
        t, mine = str(text).lower(), self.transmission.lower()
        if not mine:
            return True
        variable = "variable" in mine or "(av" in mine
        if re.search(r"dual[- ]clutch|\bdct\b|\bdsg\b|s tronic", t):
            return self.automated_manual
        if re.search(r"continuously variable|\bcvt\b|\bivt\b", t):
            return variable
        if re.search(r"\bmanual\b", t) and not re.search(r"automatic|manual shift|manual mode|manumatic", t):
            return self.manual
        gears = re.search(r"(\d+)[ -]speed", t)
        mine_gears = re.findall(r"(\d+)", mine)
        if gears and mine_gears and not variable:
            return gears.group(1) == mine_gears[-1]
        return True

    def engine_ok(self, label) -> tuple[bool, str | None]:
        """(fits, designation) for an applicability "engine": a displacement ("2.5L", "Smartstream
        G1.6 T-GDi"), a model designation ("530i"), a factory engine code ("A25A-FKS") or a word."""
        text = str(label).strip()
        if self.engine and text.upper() == str(self.engine).upper():
            return True, None
        named = powertrains_named(text)
        if named == {"DIESEL"}:
            if not self.diesel:
                return False, None
        elif named and not self.powertrain_ok(named):
            return False, None
        disp = displacements(text)
        if disp:
            if not self.displacement_ok(disp):
                return False, None
            model = model_tokens_of(text, self.ignore)
            if not model:
                return True, None
            # "C300 2.0L 4cyl 4MATIC": the designation and its drive word must fit as well
            if not model & self.model_tokens or not self.drive_words_ok(text, model):
                return False, None
            return True, next((d for d, toks in zip(self.designations, self.design_tokens, strict=True) if model & toks), None)
        if model_tokens_of(text, self.ignore):
            design = self.strict_designation(text)
            return design is not None, design
        if re.fullmatch(r"[A-Z0-9]{2,}(?:-[A-Z0-9]+)*", text) and re.search(r"\d", text):
            engine = str(self.engine or "").upper()
            return bool(engine) and (engine.startswith(text.upper()) or text.upper().startswith(engine)), None
        return True, None

    def drive_words_ok(self, text, model: set[str]) -> bool:
        """A label with a drive word ("4MATIC", "xDrive") fits only that drive; a label without one
        is the plain version when the generation also has the plain designation of that model."""
        words = tokens(text)
        drive = next((DRIVE_WORDS[w] for w in words if w in DRIVE_WORDS), None)
        if drive:
            return not self.drivetrain or drive == self.drivetrain or (drive == "AWD" and self.drivetrain == "4WD")
        plain_exists = any(model & d and not d & set(DRIVE_WORDS) for d in self.generation_design_tokens)
        mine = [d for d in self.design_tokens if model & d]
        return not (plain_exists and mine and all(d & set(DRIVE_WORDS) for d in mine))

    def loose_alternative_fits(self, alt: str) -> bool:
        """One entry of a maintenance-card model list ("A3 with AWD", "A3 2.0l TDI", "RS 3", "Jetta GLI")."""
        if not self.displacement_ok(displacements(alt)):
            return False
        named = powertrains_named(alt)
        if named == {"DIESEL"} and not self.diesel:
            return False
        if named and named != {"DIESEL"} and not self.powertrain_ok(named):
            return False
        words = tokens(alt)
        drive = next((DRIVE_WORDS[w] for w in words if w in DRIVE_WORDS), None)
        if drive and self.drivetrain and drive != self.drivetrain:
            return False
        rest = {w for w in words - self.ignore - BODY_WORDS - FILLER - set(DRIVE_WORDS) if not POWER_WORDS.match(w)}
        return not rest or rest <= self.all_tokens

    def edition_fits(self, edition: str) -> tuple[bool, bool]:
        """(fits, names a designation). An edition fits when one of its alternatives fits: its
        model designations, powertrain words, displacement, distinguishing words and body."""
        text = norm_text(edition)
        line = norm_text(self.line)
        parts = [text]
        if line and len(re.findall(r"\b" + re.escape(line) + r"\b", text)) > 1:
            parts = [p.strip() for p in re.split(r"\b" + re.escape(line) + r"\b", text)][1:]
        alternatives = []
        for part in parts:
            pieces = [p.strip() for p in re.split(r"\band\b|/|,", part)]
            alternatives += [p for p in pieces if p] or [""]
        named_any = False
        for alt in alternatives:
            named = model_tokens_of(alt, self.ignore)
            named_any |= bool(named)
            if named and not named & self.model_tokens:
                continue
            words = powertrains_named(alt)
            if words == {"DIESEL"} and not self.diesel:
                continue
            if words and words != {"DIESEL"} and not self.powertrain_ok(words):
                continue
            if not self.displacement_ok(displacements(alt)):
                continue
            rest = tokens(alt) - self.ignore - BODY_WORDS - FILLER - set(DRIVE_WORDS)
            if not named and self.distinguishing({w for w in rest if not POWER_WORDS.match(w)}):
                continue
            if not self.body_ok(body_family(alt)):
                continue
            return True, bool(named)
        return False, named_any


DISPLAY_ONLY = "\x00"  # marks a qualifier part that labels a value without making it a separate version


def _app(row) -> dict:
    """A row's applicability (NHTSA recall rows carry a sentence instead of a mapping)."""
    app = (row.conditions or {}).get("applicability")
    return app if isinstance(app, dict) else {}


def _list(value) -> list:
    return value if isinstance(value, list) else [value]


def applies(app: dict, t: Target, translate=None) -> tuple[bool, int, list[str]]:
    """(applies, specificity, qualifier parts). Specificity 0: the row names the configuration's
    model designation; 1: general. Qualifiers name the trim, designation, tire or condition a
    value is stated for when it is narrower than the configuration."""
    specific, qual = 1, []
    if not app:
        return True, 1, qual
    labels = " ".join(str(app.get(k) or "") for k in ("edition", "variant", "engine", "models", "engine_note"))
    diesel_named = powertrains_named(labels) == {"DIESEL"}
    power = app.get("powertrain")
    if power:
        allowed = set(str(power).upper().split("/"))
        if allowed <= {"ICE", "HEV", "PHEV", "BEV", "DIESEL", "FCEV", "MHEV"}:
            if not t.powertrain_ok(allowed, diesel_named):
                return False, 1, qual
        elif not any(str(power).lower() in d.lower() for d in t.designations):
            return False, 1, qual  # a sub-system name ("eAssist") the configuration's designations do not carry
    if app.get("powertrains") and not t.powertrain_ok(_list(app["powertrains"]), True):
        return False, 1, qual
    if app.get("powertrain_except") and any(str(app["powertrain_except"]).lower() in d.lower() for d in t.designations):
        return False, 1, qual
    for key in ("drive", "drivetrain"):
        if app.get(key) and not t.drive_ok(app[key]):
            return False, 1, qual
    if app.get("displacement_l") and not t.displacement_ok({number(app["displacement_l"])} - {None}):
        return False, 1, qual
    if app.get("engine"):
        ok, design = t.engine_ok(app["engine"])
        if not ok:
            return False, 1, qual
        if design:
            specific = 0
            qual.append(design)
    if app.get("engine_except"):
        disp, named = displacements(app["engine_except"]), powertrains_named(app["engine_except"])
        hit_disp = bool(disp) and t.displacement is not None and t.displacement_ok(disp)
        hit_named = bool(named) and (t.powertrain in named or (named == {"DIESEL"} and t.diesel))
        if (disp or named) and (hit_disp or not disp) and (hit_named or not named):
            return False, 1, qual
    if app.get("engine_note"):
        named = powertrains_named(app["engine_note"])
        if named and not t.powertrain_ok(named, True):
            return False, 1, qual
    if app.get("engine_code"):
        code, engine = str(app["engine_code"]).upper(), str(t.engine or "").upper()
        if not engine or not (engine.startswith(code) or code.startswith(engine)):
            return False, 1, qual
    for key in ("variant", "vpic_ca_model"):
        label = app.get(key)
        if not label:
            continue
        if model_tokens_of(label, t.ignore):
            design = t.strict_designation(label)
            if design is None:
                return False, 1, qual
            specific = 0
            if design not in qual:
                qual.append(design)
            continue
        # a trim name ("SE / Sport", "Hybrid Limited", "COROLLA 4DR SEDAN L/LE")
        named = powertrains_named(label)
        if named == {"DIESEL"} and not t.diesel or named and named != {"DIESEL"} and not t.powertrain_ok(named):
            return False, 1, qual
        if not t.body_ok(body_family(label)):
            return False, 1, qual
        if not t.trim_label_fits(label):
            return False, 1, qual
        trim = " ".join(w for w in re.split(r"\s+", str(label)) if w.lower() not in t.ignore | BODY_WORDS).strip(" -")
        if t.trims and trim:
            names = {x.strip().upper() for x in re.split(r"/|,", trim) if x.strip()}
            if names and not names & {x.upper() for x in t.trims}:
                return False, 1, qual
        if trim and key == "vpic_ca_model":
            # a Canadian trim name is not a US version: the value competes with the general US
            # value (a FACT wins) and keeps the trim only as a label
            qual.append(DISPLAY_ONLY + trim + " (CA)")
        elif trim:
            qual.append(trim)
    if app.get("models"):
        alternatives = [a for a in re.split(r";|,", str(app["models"])) if a.strip()]
        if not any(t.loose_alternative_fits(a) for a in alternatives):
            return False, 1, qual
    if app.get("except"):
        named = model_tokens_of(app["except"], t.ignore)
        if named & t.model_tokens or (not named and t.strict_designation(app["except"])):
            return False, 1, qual
    if app.get("edition"):
        ok, named = t.edition_fits(app["edition"])
        if not ok:
            return False, 1, qual
        if named:
            specific = 0
    body = body_family(" ".join(str(app.get(k) or "") for k in ("edition", "variant", "models")))
    if body in BODY_NAMES and len(t.bodies) > 1:
        qual.append(BODY_NAMES[body])
    if app.get("transmission") and not t.transmission_ok(app["transmission"]):
        return False, 1, qual
    trims = app.get("trims") or app.get("trims_from_pi")
    if trims:
        trims = [str(x) for x in _list(trims)]
        if t.trims:
            trims = [x for x in trims if x in t.trims]
            if not trims:
                return False, 1, qual
        qual.append("/".join(trims))
    if app.get("except_trims") and t.trims and t.trims <= {str(x) for x in _list(app["except_trims"])}:
        return False, 1, qual
    if app.get("tires"):
        qual.append(", ".join(str(x) for x in _list(app["tires"])))
    if app.get("minder_code"):
        qual.append(f"Maintenance Minder: {app['minder_code']}")
    for key in ("condition", "emissions", "wheel", "equipment", "oil_monitor", "brake_fluid_type", "schedule_table", "filter"):
        if app.get(key):
            qual.append(translate("maintenance_qualifier", str(app[key])) if translate else str(app[key]))
    return True, specific, qual


# --- values --------------------------------------------------------------------------------------
def fmt(n: Decimal) -> str:
    text = f"{n.normalize():f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def word(value: str, language: str) -> str | None:
    raw = value.strip()
    for table in (VALUE_LABELS, EXTRA_WORDS):
        for candidate in (raw, raw.upper()):
            if candidate in table:
                return tr(language, table[candidate])
    return None


def rpm_text(value) -> str:
    text = str(value).replace(",", "").replace("–", "-").replace(" ", "")
    m = re.fullmatch(r"(\d+)-(\d+)", text)
    if m:
        return m.group(1) if m.group(1) == m.group(2) else f"{m.group(1)}–{m.group(2)}"
    return text


def transmission_text(raw: str, language: str) -> str:
    value = raw
    if raw.startswith("Automatic"):
        value = raw.replace("Automatic", tr(language, ("Автомат", "Avtomat")), 1)
    elif raw.startswith("Manual"):
        value = raw.replace("Manual", tr(language, ("Механика", "Mexaniki")), 1)
    value = value.replace("variable gear ratios", tr(language, ("вариатор", "variator")))
    return re.sub(r"(\d+)-spd", lambda m: m[1] + tr(language, (" передач", " pillə")), value)


def show(key: str, value, unit: str | None, app: dict, language: str) -> str:
    def u(name):
        return tr(language, UNIT_WORDS[name])

    unit = UNIT_OF.get(key) or unit
    if value is None or value == [] or (isinstance(value, str) and not value.strip()):
        return ""  # an empty value is left out, never shown as a dash
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    if isinstance(value, str):
        raw = value.strip()
        named = word(raw, language)
        if named:
            return named
        if key in ("power_rpm", "torque_rpm"):
            return f"{rpm_text(raw)} {u('rpm')}"
        if key == "bore_stroke_mm":
            return re.sub(r"\s*[x×]\s*", " × ", raw) + f" {u('mm')}"
        if key == "bore_stroke_in":
            parts = [number(p) for p in re.split(r"\s*[x×]\s*", raw)]
            if len(parts) == 2 and all(p is not None for p in parts):
                mm = [fmt(convert(p, "in", "mm")) for p in parts]
                return f"{mm[0]} × {mm[1]} {u('mm')} ({raw} in)"
            return raw
        if key in ("transmission_description_epa",):
            return transmission_text(raw, language)
        if key == "weight_distribution_front_rear_pct":
            return f"{raw} %"
        if not re.fullmatch(r"\d+(?:\.\d+)?", raw):
            return raw
    n = number(value)
    if n is None:
        return str(value)
    if language == "en" and key not in ("power_hp", "system_power_hp", "torque_lb_ft", "power_rpm", "torque_rpm",
                                        "wheel_size_in", "engine_displacement_l", "engine_displacement_cc"):
        # product phase, stage 1: US units with the metric value in brackets
        us = unit_display.show(n, unit, language, key)
        if us:
            return us
        if unit == "L/1000km":
            miles = unit_display.to_us(1000, "km")[0]
            return f"{fmt(n)} L per {fmt(miles)} mi (1,000 km)"
    if key in ("power_hp", "system_power_hp"):
        text = f"{fmt(n)} hp ({fmt(convert(n, 'hp', 'kW'))} {u('kW')})"
    elif key == "torque_lb_ft":
        text = f"{fmt(n)} lb-ft ({fmt(convert(n, 'lb_ft', 'N·m'))} {u('N·m')})"
    elif key == "wheel_size_in":
        text = f"{fmt(n)}″"
    elif key in ("power_rpm", "torque_rpm"):
        text = f"{fmt(n)} {u('rpm')}"
    elif key == "engine_displacement_l":
        text = f"{n:.1f} {u('L')}"
    elif unit in UNIT_WORDS:
        text = f"{fmt(n)} {u(unit)}"
    else:
        text = fmt(n)
    if app.get("rpm") and key in ("power_hp", "torque_lb_ft", "system_power_hp"):
        text += tr(language, (" при ", ", ")) + f"{rpm_text(app['rpm'])} {u('rpm')}"
    return text


# --- assembly ------------------------------------------------------------------------------------
def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.show_us_tech_facts is not None:
        return bool(settings.show_us_tech_facts)
    return settings.environment != "production"


def _configuration_row(db, configuration_key: str) -> TechnicalEvidence | None:
    return db.scalar(select(TechnicalEvidence).where(TechnicalEvidence.fact_key == "configuration",
                                                     TechnicalEvidence.configuration_key == configuration_key).limit(1))


def _gearbox(text: str) -> tuple[str | None, int | None]:
    """(family, gears) of an EPA or catalogue gearbox: AT, CVT, DCT, MANUAL."""
    t = str(text or "").lower()
    gears = re.findall(r"(\d+)", t)
    count = int(gears[-1]) if gears else None
    if t.startswith("manual") or t == "manual":
        return "MANUAL", count
    if "(av" in t or "variable" in t or "cvt" in t or "ivt" in t:
        return "CVT", None
    if "(am" in t or "dual-clutch" in t or "dct" in t or "dsg" in t:
        return "DCT", count
    return ("AT", count) if t else (None, None)


def configuration_for_variant(db, variant_id: str) -> str | None:
    """The configuration a catalogue variant is linked to. The loader links by displacement,
    drive and powertrain only, so a variant can carry several configurations (2.0 IVT and 2.0T
    DCT of one Elantra year): the one whose gearbox and aspiration agree with the variant wins;
    equivalent EPA codings of the same car (AV-S7 / variable gear ratios) are told apart by the
    amount of data; nothing compatible -> no configuration."""
    rows = list(db.execute(select(TechnicalEvidence.configuration_key, TechnicalEvidence.conditions).where(
        TechnicalEvidence.fact_key == "configuration", TechnicalEvidence.vehicle_variant_id == variant_id)))
    if not rows:
        from app.services import catalog_preview  # a variant of the preview layer (2021-2026)

        return catalog_preview.configuration_key(db, variant_id)
    if len(rows) == 1:
        return rows[0][0]
    from app.models.catalog import VehicleVariant

    variant = db.get(VehicleVariant, variant_id)
    facts = ((variant.specifications or {}).get("catalog") or {}).get("facts") or {} if variant else {}
    fact = lambda k: (facts.get(k) or {}).get("value") if isinstance(facts.get(k), dict) else facts.get(k)  # noqa: E731
    family = str(fact("transmission_family") or "").upper() or _gearbox(fact("transmission_description") or (variant.transmission if variant else ""))[0]
    family = {"AMT": "DCT", "ECVT": "CVT", "VARIABLE_UNSPECIFIED": "CVT"}.get(family, family)
    gears = fact("gears")
    aspiration = str(fact("aspiration") or "").upper()
    turbo = None if not aspiration else aspiration in ("TURBO", "TURBOCHARGED", "SUPERCHARGED")
    fitting = []
    for key, cond in rows:
        ident = (cond or {}).get("identity") or {}
        cfg_family, cfg_gears = _gearbox(ident.get("epa_transmission"))
        if family in ("AT", "CVT", "DCT", "MANUAL") and cfg_family and cfg_family != family:
            continue
        if gears and cfg_gears and int(gears) != cfg_gears:
            continue
        cfg_turbo = str(ident.get("aspiration") or "").upper() in ("TURBOCHARGED", "SUPERCHARGED")
        if turbo is not None and ident.get("aspiration") and cfg_turbo != turbo:
            continue
        fitting.append(key)
    if not fitting:
        return None
    if len(fitting) == 1:
        return fitting[0]
    counts = dict(db.execute(select(TechnicalEvidence.configuration_key, func.count()).where(
        TechnicalEvidence.configuration_key.in_(fitting)).group_by(TechnicalEvidence.configuration_key)).all())
    return sorted(fitting, key=lambda k: (-counts.get(k, 0), k))[0]


def _target(db, row: TechnicalEvidence) -> tuple[Target, list[TechnicalEvidence]]:
    year = row.year_from
    rows = list(db.scalars(select(TechnicalEvidence).where(
        TechnicalEvidence.generation_id == row.generation_id, TechnicalEvidence.make_id == row.make_id,
        TechnicalEvidence.year_from <= year, TechnicalEvidence.year_to >= year, TechnicalEvidence.scope_level.is_not(None),
        TechnicalEvidence.fact_key.not_in(NOT_LOADED))))
    epa = db.execute(select(TechnicalEvidence.configuration_key, TechnicalEvidence.conditions).where(
        TechnicalEvidence.generation_id == row.generation_id, TechnicalEvidence.year_from <= year,
        TechnicalEvidence.year_to >= year, TechnicalEvidence.fact_key == "epa_combined_mpg")).all()
    designations, generation_labels = [], []
    for key, cond in epa:
        label = (cond or {}).get("epa_model")
        if not label:
            continue
        generation_labels.append(label)
        if key == row.configuration_key and label not in designations:
            designations.append(label)
    facts = {r.fact_key: r.value for r in rows if r.configuration_key == row.configuration_key
             and _enum(r.scope_level) == "CONFIGURATION"}
    model_name = db.scalar(select(VehicleModel.name).join(VehicleGeneration, VehicleGeneration.model_id == VehicleModel.id)
                           .where(VehicleGeneration.id == row.generation_id)) or ""
    target = Target(row, facts, designations, generation_labels, model_name)
    target.trims = _trims(rows, target)
    return target, rows


def _trims(rows: list[TechnicalEvidence], t: Target) -> set[str] | None:
    """The trims the sources state for this configuration: the union of the trims of rows pinned
    to its engine family (or to its electrified powertrain). None when no source pins one."""
    found, every = set(), set()
    for r in rows:
        app = _app(r)
        trims = app.get("trims") or app.get("trims_from_pi")
        if not trims:
            continue
        every |= {str(x) for x in _list(trims)}
        engine = str(t.engine or "").upper()
        pinned = bool(engine) and (str(r.engine_family_key or "").upper() == engine or str(app.get("engine") or "").upper() == engine)
        pinned = pinned or (t.powertrain not in ("", "ICE", "DIESEL") and str(app.get("powertrain") or "").upper() == t.powertrain)
        if not pinned:
            continue
        if app.get("drivetrain") and not t.drive_ok(app["drivetrain"]):
            continue
        if app.get("powertrain") and not t.powertrain_ok(str(app["powertrain"]).upper().split("/")):
            continue
        found |= {str(x) for x in _list(trims)}
    if found:
        # a trim the configuration's EPA designations name ("Camry TRD") belongs to it as well
        found |= {x for x in every if x.lower() in t.all_tokens}
    return found or None


def _source_view(source: SourceRecord | None, row) -> dict:
    cites = ((row.conditions or {}).get("cites") or []) if hasattr(row, "conditions") else []
    first = next((c for c in cites if c.get("quote")), {})
    return {"title": source.title if source else None, "publisher": source.publisher if source else None,
            "url": source.url if source else None, "tier": _enum(source.source_tier) if source else None,
            "locator": row.locator, "quote": first.get("quote"), "pages": first.get("pages"),
            "sources_agreeing": len({c.get("source") for c in cites}) or 1}


def _edition_conflicts(rows: list[TechnicalEvidence], t: Target) -> set[str]:
    """Editions (press releases, spec sheets) whose general rows contradict the configuration:
    another gearbox, displacement or number of cylinders ("sonata eco" with its 7-speed DCT is not
    the 2.4 with the 6-speed automatic). None of their rows applies to it."""
    bad = set()
    narrowing = ("engine", "variant", "displacement_l", "models", "trims", "trims_from_pi", "vpic_ca_model", "engine_code")
    for r in rows:
        app = _app(r)
        edition = app.get("edition")
        if not edition or edition in bad or any(app.get(k) for k in narrowing):
            continue
        value = number(r.value) if not isinstance(r.value, str) or re.fullmatch(r"\s*\d+(?:\.\d+)?\s*", r.value) else None
        litres = value / 1000 if r.fact_key == "engine_displacement_cc" and value is not None else value
        conflicts = (
            (r.fact_key == "transmission_description" and not t.transmission_value_ok(r.value))
            or (r.fact_key in ("engine_displacement_l", "engine_displacement_cc") and litres is not None
                and t.displacement is not None and abs(litres - t.displacement) > Decimal("0.06"))
            or (r.fact_key == "cylinders" and value is not None and t.cylinders is not None and value != t.cylinders)
        )
        if conflicts:
            bad.add(edition)
    return bad


def _choose(options: list[tuple]) -> list[tuple]:
    """options: (level, specific, display, group, label, row). The most specific level, then the
    rows naming the designation, then per version group the best display level."""
    best_level = min(o[0] for o in options)
    options = [o for o in options if o[0] == best_level]
    best_specific = min(o[1] for o in options)
    options = [o for o in options if o[1] == best_specific]
    groups = defaultdict(list)
    for o in options:
        groups[o[3]].append(o)
    chosen = []
    for group in groups.values():
        best = min(o[2] for o in group)
        chosen += [o for o in group if o[2] == best]
    return chosen


_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()
STAMP_SECONDS = 60


def _stamp(db) -> tuple:
    out = []
    for table in (TechnicalEvidence, KnownIssue, MaintenanceScheduleItem, ContentTranslation):
        count, newest = db.execute(select(func.count(table.id), func.max(table.updated_at))).one()
        out.append((count, str(newest)))
    return tuple(out)


def build(db, configuration_key: str, language: str = "ru") -> dict | None:
    """Facts for one configuration, cached per configuration and language; the cache is renewed
    when the scoped tables change (checked at most once a minute)."""
    key = (str(db.get_bind().url), configuration_key, language)
    now = time.monotonic()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
    if hit and now - hit[1] < STAMP_SECONDS:
        return hit[2]
    stamp = _stamp(db)
    if hit and hit[0] == stamp:
        with _CACHE_LOCK:
            _CACHE[key] = (stamp, now, hit[2])
        return hit[2]
    result = _build(db, configuration_key, language)
    with _CACHE_LOCK:
        if len(_CACHE) > 512:
            _CACHE.clear()
        _CACHE[key] = (stamp, now, result)
    return result


def clear_cache() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()


def _build(db, configuration_key: str, language: str) -> dict | None:
    row = _configuration_row(db, configuration_key)
    if row is None:
        return None
    t, rows = _target(db, row)
    excluded_editions = _edition_conflicts(rows, t)
    candidates = defaultdict(list)
    recalls = []
    for r in rows:
        if r.fact_key == "nhtsa_recall":
            recalls.append(r)
            continue
        level, display = _enum(r.scope_level), _enum(r.display_level)
        if display not in DISPLAY_RANK or r.is_demo:
            continue
        if level == "CONFIGURATION" and r.configuration_key != t.key:
            continue
        if level in ("ENGINE", "TRANSMISSION") and r.engine_family_key and r.engine_family_key != t.engine:
            continue
        app = _app(r)
        if app.get("edition") in excluded_editions:
            continue
        if r.fact_key == "transmission_description" and not t.transmission_value_ok(r.value):
            continue
        ok, specific, qual = applies(app, t)
        if not ok:
            continue
        epa_model = (r.conditions or {}).get("epa_model")
        if level == "CONFIGURATION" and epa_model and len(t.designations) > 1:
            qual = [epa_model, *qual]
        group = " · ".join(q for q in qual if not q.startswith(DISPLAY_ONLY))
        label = " · ".join(q.lstrip(DISPLAY_ONLY) for q in qual)
        candidates[r.fact_key].append((LEVEL_RANK.get(level, 3), specific, DISPLAY_RANK[display], group, label, r))
    source_ids = {o[-1].source_id for opts in candidates.values() for o in opts}
    sources = {s.id: s for s in db.scalars(select(SourceRecord).where(SourceRecord.id.in_(source_ids)))} if source_ids else {}
    others = tr(language, ("остальные версии", "digər versiyalar"))
    maker_aki: list[int] = []
    categories = []
    for cat, ru, az, keys in CATEGORIES:
        out_rows = []
        for key in keys:
            if key in FALLBACK_OF and candidates.get(FALLBACK_OF[key]):
                continue
            options = candidates.get(key)
            if not options:
                continue
            # values stated for another market (vPIC Canadian specifications) only fill a gap
            us = [o for o in options if (_app(o[-1]).get("market_of_data") or "US") == "US"]
            options = us or options
            values, seen = [], set()
            for _level, _specific, display, group, label, r in sorted(_choose(options), key=lambda o: (o[3] == "", o[4], o[2])):
                app = _app(r)
                shown = show(key, r.value, r.unit, app, language)
                if key == "octane_aki" and number(r.value) is not None:
                    # owner rule 2026-10-04: the manufacturer's AKI shown as our AI grade
                    maker_aki.append(int(number(r.value)))
                    shown = fuel_advice.maker_value(int(number(r.value)), language)
                if not shown or (label, shown) in seen:
                    continue
                seen.add((label, shown))
                values.append({"value": shown, "qualifier": label or None, "group": group, "secondary": display == 1,
                               "approximate": bool(app.get("approx_in_source")), "level": _enum(r.scope_level),
                               "source": _source_view(sources.get(r.source_id), r)})
            if len({v["value"] for v in values}) == 1:
                values = [{**values[0], "qualifier": None, "secondary": all(v["secondary"] for v in values)}]
            elif len({v["group"] for v in values}) > 1:
                values = [{**v, "qualifier": v["qualifier"] or others} for v in values]
            values = [{k: x for k, x in v.items() if k != "group"} for v in values]
            if values:
                label = fuel_advice.MAKER_LABEL if key == "octane_aki" else LABELS.get(key, (key, key))
                if key == "fuel_combined" and t.powertrain == "BEV":
                    # EPA states an electric car's consumption as MPGe: the litres are a gasoline equivalent
                    label = ("Расход EPA в бензиновом эквиваленте", "EPA sərfiyyatı benzin ekvivalentində")
                out_rows.append({"key": key, "label": tr(language, label), "values": values,
                                 **({"kind": "manufacturer", "basis": tr(language, fuel_advice.MAKER_BASIS)} if key == "octane_aki" else {})})
        if cat == "fuel":
            out_rows += _fuel_recommendation(db, row, t, candidates, maker_aki, language)
        if out_rows:
            categories.append({"key": cat, "title": tr(language, (ru, az)), "rows": out_rows})
    names = db.execute(select(VehicleMake.name, VehicleModel.name, VehicleGeneration.name, VehicleGeneration.code)
                       .join(VehicleModel, VehicleModel.make_id == VehicleMake.id)
                       .join(VehicleGeneration, VehicleGeneration.model_id == VehicleModel.id)
                       .where(VehicleGeneration.id == t.generation_id)).first()
    return {
        "configuration_key": t.key, "year": t.year, "variant_id": row.vehicle_variant_id,
        "title": " ".join(str(x) for x in (names[0], names[1], t.year) if x) if names else t.key,
        "generation": (names[3] or names[2]) if names else None,
        "summary": configuration_label(row, language),
        "designations": t.designations,
        "categories": categories,
        "weak_points": weak_points(db, t, language),
        "campaigns": campaigns(recalls, t, language, Translator(db, language)),
        "maintenance": maintenance(db, t, language, excluded_editions),
        "labels": {
            "secondary": tr(language, ("по данным справочников", "məlumat kitabçalarına görə")),
            "owner_reports": tr(language, ("владельцы сообщают", "sahiblər bildirir")),
            "approximate": tr(language, ("ориентировочно", "təxmini")),
            "sources": tr(language, ("Источники", "Mənbələr")),
        },
    }


def _fuel_recommendation(db, row: TechnicalEvidence, t: Target, candidates: dict, maker_aki: list[int],
                         language: str) -> list[dict]:
    """The Auto Expert fuel recommendation line (app.services.fuel_advice): a rule of the app,
    not a fact of the database, never labelled as the manufacturer's requirement. Engine traits:
    the EPA records of the configuration (eng_dscr "SIDI", fuelType1), the aspiration of its
    identity (EPA tCharger / sCharger) and the injection / engine texts of the sources."""
    ident = (row.conditions or {}).get("identity") or {}
    facts: dict = {}
    keys = [f"epa:{i}" for i in ident.get("epa_ids") or []]
    for variant in db.scalars(select(VehicleVariant).where(VehicleVariant.catalog_key.in_(keys))) if keys else []:
        catalog_facts = ((variant.specifications or {}).get("catalog") or {}).get("facts") or {}
        for key, fact in catalog_facts.items():
            # one engine per configuration: a direct-injection mark on any of its EPA records counts
            if key not in facts or (key == "engine_description" and "SIDI" in str((fact or {}).get("value"))):
                facts[key] = fact
    texts = [str(o[-1].value) for key in ("injection", "engine_description") for o in candidates.get(key, [])]
    traits = fuel_advice.traits_from_facts(facts, texts, maker_aki, aspiration=ident.get("aspiration"))
    if t.diesel:
        traits.fuel = "DIESEL"
    elif t.powertrain in ("BEV", "FCEV"):
        traits.fuel = "ELECTRICITY"
    elif traits.fuel is None and t.powertrain in fuel_advice.GASOLINE_POWERTRAINS:
        traits.fuel = "GASOLINE"
    out = []
    for line in fuel_advice.rows(traits, language):
        if line["kind"] != "recommendation":
            continue  # the manufacturer's octane is the octane row above, with its sources
        out.append({"key": line["key"], "kind": "recommendation", "label": line["label"], "basis": line["basis"],
                    "values": [{"value": line["value"], "qualifier": None, "reason": line["reason"], "secondary": False,
                                "approximate": False, "level": None, "source": None}]})
    return out


def configuration_label(row: TechnicalEvidence, language: str) -> str:
    ident = (row.conditions or {}).get("identity") or {}
    parts = []
    if ident.get("displacement_l"):
        parts.append(f"{ident['displacement_l']} {tr(language, UNIT_WORDS['L'])}")
    if ident.get("cylinders"):
        parts.append(f"{ident['cylinders']} {tr(language, ('цил.', 'sil.'))}")
    if ident.get("engine_family_key"):
        parts.append(str(ident["engine_family_key"]))
    power = "DIESEL" if "-diesel-" in (row.configuration_key or "") else ident.get("powertrain")
    if power:
        parts.append(word(str(power), language) or str(power))
    if ident.get("epa_transmission"):
        parts.append(transmission_text(str(ident["epa_transmission"]), language))
    if ident.get("drivetrain"):
        parts.append(word(str(ident["drivetrain"]), language) or str(ident["drivetrain"]))
    return " · ".join(parts)


def _catalog_query():
    return (select(TechnicalEvidence, VehicleMake.name, VehicleModel.name)
            .join(VehicleGeneration, VehicleGeneration.id == TechnicalEvidence.generation_id)
            .join(VehicleModel, VehicleModel.id == VehicleGeneration.model_id)
            .join(VehicleMake, VehicleMake.id == VehicleModel.make_id)
            .where(TechnicalEvidence.fact_key == "configuration"))


def configurations(db, make: str | None, model: str | None, year: int | None, language: str = "ru", limit: int = 200) -> list[dict]:
    """Configurations of the US technical database (preview navigation; nothing is published)."""
    query = _catalog_query()
    if make:
        query = query.where(func.lower(VehicleMake.name) == make.lower())
    if model:
        query = query.where(func.lower(VehicleModel.name) == model.lower())
    if year:
        query = query.where(TechnicalEvidence.year_from <= year, TechnicalEvidence.year_to >= year)
    query = query.order_by(VehicleMake.name, VehicleModel.name, TechnicalEvidence.year_from, TechnicalEvidence.configuration_key)
    return [{"configuration_key": row.configuration_key, "make": make_name, "model": model_name, "year": row.year_from,
             "label": configuration_label(row, language), "variant_id": row.vehicle_variant_id}
            for row, make_name, model_name in db.execute(query.limit(limit))]


def facets(db) -> list[dict]:
    """Make / model / model years present in the US technical database (preview navigation)."""
    rows = db.execute(select(VehicleMake.name, VehicleModel.name, TechnicalEvidence.year_from)
                      .join(VehicleGeneration, VehicleGeneration.id == TechnicalEvidence.generation_id)
                      .join(VehicleModel, VehicleModel.id == VehicleGeneration.model_id)
                      .join(VehicleMake, VehicleMake.id == VehicleModel.make_id)
                      .where(TechnicalEvidence.fact_key == "configuration")
                      .distinct()).all()
    years = defaultdict(set)
    for make, model, year in rows:
        years[(make, model)].add(year)
    return [{"make": make, "model": model, "years": sorted(ys)} for (make, model), ys in sorted(years.items())]


ISSUE_REQUIRES = [
    # a problem of a unit the configuration does not have is not its weak point (generation-wide
    # manufacturer communications name the unit: "hybrid / high-voltage system", "dual-clutch")
    (re.compile(r"hybrid|high[- ]voltage|\bhv\b|traction battery|inverter", re.I),
     lambda t: t.powertrain in ("", "HEV", "PHEV", "BEV", "MHEV", "FCEV")),
    (re.compile(r"dual[- ]clutch|\bdct\b|\bdsg\b", re.I), lambda t: not t.transmission or t.automated_manual),
    (re.compile(r"\bcvt\b|continuously variable", re.I), lambda t: not t.transmission or "variable" in t.transmission.lower() or "(av" in t.transmission.lower()),
    (re.compile(r"turbo", re.I), lambda t: not t.aspiration or t.aspiration == "TURBOCHARGED"),
    (re.compile(r"diesel|\bdef\b|adblue|\bdpf\b|particulate", re.I), lambda t: not t.powertrain or t.diesel),
    (re.compile(r"manual transmission|clutch pedal", re.I), lambda t: not t.transmission or t.manual),
    (re.compile(r"fuel pump|misfire|spark plug|oil consumption|timing chain|timing belt|exhaust|catalytic|engine oil|"
                r"fuel injector|transmission failure|shifting|stalling|engine stall", re.I), lambda t: t.powertrain != "BEV"),
]


def issue_fits(text: str, t: Target) -> bool:
    return all(check(t) for pattern, check in ISSUE_REQUIRES if pattern.search(text))


def weak_points(db, t: Target, language: str) -> list[dict]:
    translate = Translator(db, language)
    issues = db.scalars(select(KnownIssue).where(
        KnownIssue.make_id == t.make_id, KnownIssue.generation_id == t.generation_id, KnownIssue.year_from <= t.year,
        KnownIssue.year_to >= t.year, KnownIssue.scope_level.is_not(None), KnownIssue.is_demo.is_(False)))
    out = []
    for issue in issues:
        display = _enum(issue.display_level)
        if display not in ("FACT", "SECONDARY_NOTE", "OWNER_REPORTS"):
            continue
        affected = issue.affected_variants or {}
        engines = [str(e).upper() for e in affected.get("engines") or []]
        if issue.engine_family_key:
            engines.append(str(issue.engine_family_key).upper())
        if engines and (not t.engine or str(t.engine).upper() not in engines):
            continue
        if affected.get("powertrain") and not t.powertrain_ok(str(affected["powertrain"]).upper().split("/")):
            continue
        if not issue_fits(f"{issue.component} {issue.title or ''}", t):
            continue
        severity, probability = _enum(issue.severity), _enum(issue.probability)
        owner = display == "OWNER_REPORTS"
        note = None
        if owner:
            note = tr(language, ("владельцы сообщают", "sahiblər bildirir"))
        elif display == "SECONDARY_NOTE":
            note = tr(language, ("по данным справочников", "məlumat kitabçalarına görə"))
        title = issue.title or issue.component
        symptoms = [str(s) for s in issue.symptoms or [] if s]
        out.append({"title": translate("issue_title", title) if issue.title else translate("issue_component", title),
                    "component": translate("issue_component", issue.component),
                    "severity": tr(language, SEVERITY.get(severity, (severity, severity))), "severity_code": severity,
                    "probability": tr(language, PROBABILITY[probability]) if probability in PROBABILITY else None,
                    "symptoms": [translate("issue_symptom", s) for s in symptoms],
                    "how_to_check": translate("issue_inspection", issue.inspection_recommendation) or None,
                    "original": {"title": title, "symptoms": symptoms, "how_to_check": issue.inspection_recommendation or None},
                    "owner_reports": owner, "note": note, "years": [issue.year_from, issue.year_to]})
    out.sort(key=lambda i: (i["owner_reports"], SEVERITY_RANK.get(i["severity_code"], 9), i["title"] or ""))
    return out


def campaigns(rows: list[TechnicalEvidence], t: Target, language: str, translate=None) -> list[dict]:
    translate = translate or (lambda kind, text: text)
    out, seen = [], set()
    for r in rows:
        cond = r.conditions or {}
        number_ = cond.get("campaign_number") or str(r.value or "").strip('"')
        if not number_ or number_ in seen or _enum(r.display_level) == "HIDDEN_CONFLICT":
            continue
        years = [int(y) for y in cond.get("model_years") or [] if str(y).isdigit()]
        if years and t.year not in years:
            continue
        seen.add(number_)
        out.append({"number": number_, "component": translate("recall_component", cond.get("component")),
                    "summary": translate("recall_summary", cond.get("summary")),
                    "original": {"component": cond.get("component"), "summary": cond.get("summary")},
                    "years": [min(years), max(years)] if years else [r.year_from, r.year_to],
                    "note": tr(language, ("применимость к конкретному автомобилю проверяется по VIN",
                                          "konkret avtomobilə aidiyyəti VIN üzrə yoxlanılır"))})
    out.sort(key=lambda c: str(c["number"]), reverse=True)
    return out


def _years_word(years: int, language: str) -> str:
    if language == "az":
        return f"{years} il"
    if language == "en":
        return f"{years} year" if years == 1 else f"{years} years"
    if years % 10 == 1 and years % 100 != 11:
        return f"{years} год"
    if 2 <= years % 10 <= 4 and not 12 <= years % 100 <= 14:
        return f"{years} года"
    return f"{years} лет"


def _interval(km, months, rule, language: str, miles=None) -> str | None:
    parts = []
    if km and language == "en":
        parts.append(unit_display.distance(km, miles, language))
    elif km:
        parts.append(f"{km:,}".replace(",", " ") + " " + tr(language, ("км", "km")))
    if months:
        years, rest = divmod(months, 12)
        parts.append(_years_word(years, language) if not rest else f"{months} " + tr(language, ("мес.", "ay", "mo.")))
    if not parts:
        return None
    text = tr(language, (" или ", " və ya ", " or ")).join(parts)
    if len(parts) > 1 and rule == "WHICHEVER_FIRST":
        text += tr(language, (", что наступит раньше", ", hansı əvvəl çatarsa", ", whichever comes first"))
    return text


def job_fits(job: str, t: Target, jobs: set[str]) -> bool:
    """A job that belongs to one gearbox / drive / fuel applies only to configurations that have it
    (a schedule printed for the whole line lists the DCT fluid next to the automatic's ATF)."""
    if job in ("dct_fluid", "dual_clutch_fluid"):
        return not t.transmission or t.automated_manual
    if job == "manual_transmission_fluid":
        return not t.transmission or t.manual
    if job == "transmission_fluid":
        return not (t.manual or (t.automated_manual and jobs & {"dct_fluid", "dual_clutch_fluid"}))
    if job in ("transfer_case_fluid", "awd_coupling_fluid"):
        return t.drivetrain in (None, "AWD")
    if job == "diesel_exhaust_fluid":
        return t.diesel
    if job == "spark_plugs":
        return not t.diesel and t.powertrain != "BEV"
    return True


def maintenance(db, t: Target, language: str, excluded_editions: set[str] = frozenset()) -> list[dict]:
    items = [it for it in db.scalars(select(MaintenanceScheduleItem).where(
        MaintenanceScheduleItem.make_id == t.make_id, MaintenanceScheduleItem.generation_id == t.generation_id,
        MaintenanceScheduleItem.year_from <= t.year, MaintenanceScheduleItem.year_to >= t.year,
        MaintenanceScheduleItem.is_demo.is_(False)))
        if _enum(it.display_level) in DISPLAY_RANK and not (it.engine_family_key and it.engine_family_key != t.engine)
        and (it.applicability or {}).get("edition") not in excluded_editions]
    jobs = {it.job for it in items}
    translate = Translator(db, language)
    first, later = tr(language, ("первая", "ilk")), tr(language, ("последующие", "sonrakılar"))
    out, seen = [], set()
    for it in items:
        display = _enum(it.display_level)
        if not job_fits(it.job, t, jobs):
            continue
        app = it.applicability or {}
        ok, _, qual = applies(app, t, translate)
        if not ok:
            continue
        system, action = _enum(it.schedule_system), _enum(it.action)
        condition, occurrence = _enum(it.condition), _enum(it.occurrence)
        entry = {"job": tr(language, JOBS.get(it.job, (it.job.replace("_", " "),) * 2)), "job_key": it.job,
                 "action": tr(language, ACTIONS.get(action, (action, action))),
                 "interval": _interval(it.interval_km, it.interval_months, it.rule, language, it.interval_miles_original),
                 "max_interval": _interval(it.max_interval_km, it.max_interval_months, "WHICHEVER_FIRST", language),
                 "system": tr(language, SYSTEMS[system]) if system in SYSTEMS else None,
                 "severe": condition == "SEVERE",
                 "condition_detail": translate("maintenance_condition", app.get("operating_condition")),
                 "occurrence": {"FIRST": first, "SUBSEQUENT": later}.get(occurrence),
                 "service": translate("maintenance_service", app.get("service")),
                 "qualifier": " · ".join(q.lstrip(DISPLAY_ONLY) for q in qual if q) or None,
                 "approximate": bool(app.get("approx_in_source")),
                 "secondary": display == "SECONDARY_NOTE",
                 "km": it.interval_km, "months": it.interval_months,
                 "source": _source_view(it.source, it) | {"quote": _quote_of(it.notes)}}
        dedupe = tuple(entry[k] for k in ("job", "action", "interval", "max_interval", "severe", "occurrence", "service", "qualifier",
                                          "condition_detail"))
        if dedupe in seen:
            continue
        seen.add(dedupe)
        out.append(entry)
    order = {k: i for i, k in enumerate(JOBS)}
    out.sort(key=lambda m: (m["severe"], m["service"] or "", order.get(m["job_key"], 99),
                            {first: 0, None: 1}.get(m["occurrence"], 2), m["km"] or 0))
    return out


def _quote_of(notes: str | None) -> str | None:
    m = re.search(r"quote: (.+)$", notes or "")
    return m.group(1).strip() if m else None
