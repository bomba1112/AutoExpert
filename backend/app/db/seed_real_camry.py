# ruff: noqa: E501

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.seed_demo import seed_autoexpert2_demo
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.enums import (
    ConfidenceLevel,
    DataOrigin,
    EvidenceCategory,
    EvidenceStatus,
    Sentiment,
    Severity,
    SourceTier,
    SourceUsageStatus,
)
from app.models.evidence import KnownIssue, OwnerEvidence, SourceRecord, TechnicalEvidence
from app.models.vehicle_knowledge import VehicleKnowledgeProfile

PILOT_SLUG = "toyota-camry-2019-25-usa"


def seed_real_camry(session: Session) -> str:
    """Seed a reviewed, source-linked real model dossier; never a real VIN history."""
    existing = session.scalar(
        select(VehicleKnowledgeProfile).where(
            VehicleKnowledgeProfile.make == "Toyota",
            VehicleKnowledgeProfile.model == "Camry",
            VehicleKnowledgeProfile.year == 2019,
            VehicleKnowledgeProfile.market == "USA",
            VehicleKnowledgeProfile.engine_code == "A25A-FKS",
            VehicleKnowledgeProfile.data_origin == DataOrigin.REAL,
        )
    )
    if existing is not None:
        return existing.id

    seed_autoexpert2_demo(session)
    session.flush()
    now = datetime(2026, 9, 14, tzinfo=UTC)
    sources = _sources(session, now)

    make = session.scalar(select(VehicleMake).where(VehicleMake.normalized_name == "toyota"))
    model = session.scalar(
        select(VehicleModel).where(
            VehicleModel.make_id == make.id,
            VehicleModel.normalized_name == "camry",
        )
    )
    generation = session.scalar(
        select(VehicleGeneration).where(
            VehicleGeneration.model_id == model.id,
            VehicleGeneration.code == "XV70",
        )
    )
    make.is_demo = False
    model.is_demo = False
    generation.is_demo = False

    variant = VehicleVariant(
        generation_id=generation.id,
        specification_source_id=sources["toyota_press"].id,
        market="US",
        name="2019 Camry 2.5 A25A-FKS Direct Shift 8AT FWD",
        year_from=2019,
        year_to=2019,
        engine_code="A25A-FKS",
        engine="2.5 L Dynamic Force gasoline inline-four",
        transmission_code="UB80E",
        transmission="8AT",
        drivetrain="FWD",
        body="sedan",
        fuel="gasoline",
        displacement_l=Decimal("2.49"),
        power_kw=Decimal("151.38"),
        specifications={
            "displacement_cc": 2487,
            "power_hp": {"standard_grades": 203, "xse": 206},
            "torque_lb_ft": {"standard_grades": 184, "xse": 186},
            "injection": "Toyota D-4S direct and port injection",
            "timing_drive": "chain",
            "transmission_model": "UB80E",
            "trim_dependent_values": True,
        },
        is_demo=False,
        data_origin=DataOrigin.REAL,
    )
    session.add(variant)
    session.flush()

    evidence = _evidence(session, variant, sources)
    issues = _known_issues(variant, evidence)
    session.add_all(issues)
    _owner_sample(session, variant, sources["nhtsa_complaints"])

    profile = VehicleKnowledgeProfile(
        vehicle_variant_id=variant.id,
        make="Toyota",
        model="Camry",
        generation="XV70",
        production_year_start=2018,
        production_year_end=2024,
        market="USA",
        year=2019,
        engine="2.5 L Dynamic Force gasoline inline-four",
        engine_code="A25A-FKS",
        transmission="8AT",
        drivetrain="FWD",
        body="sedan",
        fuel="gasoline",
        profile_version="3.0.0-pilot.1",
        freshness_at=now,
        dossier_seed={
            "slug": PILOT_SLUG,
            "review_scope": "model-level USA specification; exact trim and VIN require resolution",
            "recalls_count": 6,
            "manufacturer_communications_count": 1,
            "owner_materials_count": 10,
        },
        is_demo=False,
        data_origin=DataOrigin.REAL,
    )
    profile.sources.extend(sources.values())
    profile.evidence.extend(evidence.values())
    session.add(profile)
    session.commit()
    return profile.id


def _sources(session: Session, now: datetime) -> dict[str, SourceRecord]:
    definitions = {
        "toyota_press": dict(
            title="2019 Toyota Camry Builds on Exciting Style, Sport Performance and Innovative Safety Tech",
            publisher="Toyota Motor Sales, U.S.A.",
            url="https://pressroom.toyota.com/2019-toyota-camry-builds-exciting-style-sport-perfor-innovative-safety-tech-standard-equipment/",
            source_type="MANUFACTURER_PRODUCT_DOCUMENTATION",
            source_tier=SourceTier.A,
            published_at=datetime(2019, 3, 5, tzinfo=UTC),
            confidence=ConfidenceLevel.HIGH,
        ),
        "toyota_maintenance": dict(
            title="2019 Camry Warranty & Maintenance Guide (T-MMS-19Camry)",
            publisher="Toyota Motor Sales, U.S.A.",
            url="https://assets.sia.toyota.com/publications/en/omms-s/T-MMS-19Camry/pdf/T-MMS-19Camry.pdf",
            source_type="MANUFACTURER_MAINTENANCE_GUIDE",
            source_tier=SourceTier.A,
            published_at=None,
            confidence=ConfidenceLevel.HIGH,
        ),
        "nhtsa_recalls": dict(
            title="NHTSA Recalls by Vehicle: 2019 Toyota Camry",
            publisher="National Highway Traffic Safety Administration",
            url="https://api.nhtsa.gov/recalls/recallsByVehicle?make=TOYOTA&model=CAMRY&modelYear=2019",
            source_type="GOVERNMENT_RECALL_API",
            source_tier=SourceTier.A,
            published_at=None,
            confidence=ConfidenceLevel.HIGH,
        ),
        "nhtsa_tsb": dict(
            title="T-SB-0152-19: Hesitation on Acceleration From a Slow Roll or Rolling Stop",
            publisher="Toyota Motor Sales, U.S.A. / NHTSA document repository",
            url="https://static.nhtsa.gov/odi/tsbs/2019/MC-10169403-9999.pdf",
            source_type="MANUFACTURER_COMMUNICATION",
            source_tier=SourceTier.A,
            published_at=datetime(2019, 11, 1, tzinfo=UTC),
            confidence=ConfidenceLevel.HIGH,
        ),
        "nhtsa_complaints": dict(
            title="NHTSA Consumer Complaints: 2019 Toyota Camry (pilot sample)",
            publisher="National Highway Traffic Safety Administration",
            url="https://api.nhtsa.gov/complaints/complaintsByVehicle?make=TOYOTA&model=CAMRY&modelYear=2019",
            source_type="OWNER_SUBMISSIONS_GOVERNMENT_REPOSITORY",
            source_tier=SourceTier.C,
            published_at=None,
            confidence=ConfidenceLevel.MEDIUM,
        ),
        "epa_fuel": dict(
            title="FuelEconomy.gov vehicle data: 2019 Toyota Camry",
            publisher="U.S. Department of Energy / U.S. Environmental Protection Agency",
            url="https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year=2019&make=Toyota&model=Camry",
            source_type="GOVERNMENT_FUEL_ECONOMY_DATA",
            source_tier=SourceTier.A,
            published_at=None,
            confidence=ConfidenceLevel.HIGH,
        ),
        "vpic": dict(
            title="vPIC Vehicle Product Information Catalog API",
            publisher="National Highway Traffic Safety Administration",
            url="https://vpic.nhtsa.dot.gov/api/",
            source_type="GOVERNMENT_VIN_DECODE_DOCUMENTATION",
            source_tier=SourceTier.A,
            published_at=None,
            confidence=ConfidenceLevel.HIGH,
        ),
        "engine_reference": dict(
            title="Toyota A25 Dynamic Force engine technical overview",
            publisher="Toyota-Club.Net technical reference",
            url="https://toyota-club.net/files/faq/18-03-20_faq_df_r4_eng.htm",
            source_type="INDEPENDENT_TECHNICAL_REFERENCE",
            source_tier=SourceTier.B,
            published_at=None,
            confidence=ConfidenceLevel.MEDIUM,
        ),
        "transmission_reference": dict(
            title="Inside Toyota's UA/UB80E/F torque converter",
            publisher="Transmission Digest",
            url="https://www.transmissiondigest.com/inside-toyotas-ua-ub80e-f-torque-converter/",
            source_type="AUTOMOTIVE_TRADE_TECHNICAL_REFERENCE",
            source_tier=SourceTier.B,
            published_at=datetime(2023, 11, 15, tzinfo=UTC),
            confidence=ConfidenceLevel.MEDIUM,
        ),
    }
    result = {}
    for key, values in definitions.items():
        record = SourceRecord(
            **values,
            market="US",
            language="en",
            retrieved_at=now,
            notes=(
                "Model-level evidence. Recall applicability and completion must be checked "
                "against the specific VIN. Owner complaints are allegations, not failure rates."
            ),
            usage_status=SourceUsageStatus.ACTIVE,
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        session.add(record)
        session.flush()
        result[key] = record
    return result


def _evidence(
    session: Session,
    variant: VehicleVariant,
    sources: dict[str, SourceRecord],
) -> dict[str, TechnicalEvidence]:
    rows = [
        (
            "verdict",
            "toyota_press",
            EvidenceCategory.OTHER,
            "expert_verdict",
            EvidenceStatus.ESTIMATE,
            "The 2.5-liter USA Camry has a well-documented powertrain, but model documentation cannot establish the condition of a specific used car.",
            "У версии 2.5 для рынка США хорошо документирована силовая установка, но данные модели не подтверждают состояние конкретного автомобиля.",
            "ABŞ bazarı üçün 2.5 versiyasının güc aqreqatı yaxşı sənədləşdirilib, lakin model məlumatı konkret avtomobilin vəziyyətini təsdiqləmir.",
        ),
        (
            "identity",
            "toyota_press",
            EvidenceCategory.OTHER,
            "general_information",
            EvidenceStatus.CONFIRMED,
            "2019 USA Toyota Camry, XV70 generation, gasoline 2.5-liter four-cylinder with front-wheel drive.",
            "Toyota Camry 2019 для рынка США, поколение XV70: бензиновый 2,5-литровый четырёхцилиндровый двигатель и передний привод.",
            "ABŞ bazarı üçün 2019 Toyota Camry, XV70 nəsli: 2.5 litrlik dörd silindrli benzin mühərriki və ön ötürücü.",
        ),
        (
            "engine_design",
            "toyota_press",
            EvidenceCategory.ENGINE,
            "engine",
            EvidenceStatus.CONFIRMED,
            "A25A-FKS is Toyota's 2,487 cc Dynamic Force inline-four with D-4S direct and port injection, 13.0:1 compression, VVT-iE intake timing and VVT-i exhaust timing.",
            "A25A-FKS — заводской код рядного четырёхцилиндрового двигателя Toyota Dynamic Force объёмом 2487 см³: комбинированный прямой и распределённый впрыск D-4S, степень сжатия 13,0:1, VVT-iE на впуске и VVT-i на выпуске.",
            "A25A-FKS — Toyota Dynamic Force 2487 sm³ sıralı dörd silindrli mühərrikin zavod kodudur: D-4S birbaşa və paylanmış püskürtmə, 13,0:1 sıxılma, girişdə VVT-iE və çıxışda VVT-i.",
        ),
        (
            "engine_timing",
            "engine_reference",
            EvidenceCategory.ENGINE,
            "engine",
            EvidenceStatus.CONFIRMED,
            "The A25A-FKS camshafts use a timing chain; this independent technical confirmation is medium-confidence and is not a service-life claim.",
            "В приводе газораспределительного механизма A25A-FKS используется цепь; это независимое техническое подтверждение средней достоверности, а не заявление о ресурсе.",
            "A25A-FKS qazpaylama mexanizminin ötürməsində zəncir istifadə olunur; bu, orta etibarlı müstəqil texniki təsdiqdir və resurs iddiası deyil.",
        ),
        (
            "engine_output",
            "toyota_press",
            EvidenceCategory.ENGINE,
            "engine",
            EvidenceStatus.CONFIRMED,
            "USA output is trim-dependent: 203 hp and 184 lb-ft for standard 2.5 grades; XSE is listed at 206 hp and 186 lb-ft.",
            "Мощность зависит от комплектации: 203 л.с. и 184 lb-ft у обычных версий 2.5; для XSE указаны 206 л.с. и 186 lb-ft.",
            "Güc komplektasiyadan asılıdır: standart 2.5 versiyalarında 203 a.g. və 184 lb-ft, XSE-də 206 a.g. və 186 lb-ft göstərilir.",
        ),
        (
            "transmission",
            "transmission_reference",
            EvidenceCategory.TRANSMISSION,
            "transmission",
            EvidenceStatus.CONFIRMED,
            "Toyota documents 8AT — 8-speed Direct Shift automatic transmission; the independent trade-technical reference identifies UB80E as the four-cylinder front-drive family.",
            "Toyota указывает 8AT — 8-ступенчатую автоматическую коробку Direct Shift; независимый отраслевой технический источник определяет UB80E как семейство для четырёхцилиндровых переднеприводных версий.",
            "Toyota 8AT — 8 pilləli Direct Shift avtomatik sürətlər qutusunu göstərir; müstəqil sahəvi texniki mənbə UB80E-ni dörd silindrli ön ötürücülü versiyalar üçün ailə kimi müəyyən edir.",
        ),
        (
            "tsb_hesitation",
            "nhtsa_tsb",
            EvidenceCategory.TRANSMISSION,
            "recalls_tsb",
            EvidenceStatus.CONFIRMED,
            "Toyota T-SB-0152-19 covers some 2019 Camry vehicles that may hesitate at 6 mph or below after a 3-to-1 downshift with under 40% accelerator; the procedure updates ECM calibration.",
            "TSB — технический бюллетень производителя T-SB-0152-19 относится к некоторым Camry 2019: возможна задержка отклика на скорости до 6 mph после переключения 3→1 при нажатии газа менее 40%; процедура предусматривает обновление калибровки ECM.",
            "TSB — istehsalçının texniki bülleteni T-SB-0152-19 bəzi 2019 Camry avtomobillərində 6 mph və aşağı sürətdə 3→1 keçidindən sonra, qaz pedalı 40%-dən az basıldıqda gecikməni təsvir edir; prosedur ECM kalibrlənməsini yeniləyir.",
        ),
        (
            "suspension",
            "toyota_press",
            EvidenceCategory.SUSPENSION,
            "suspension",
            EvidenceStatus.CONFIRMED,
            "Toyota documents a rear multi-link suspension for the XV70 Camry; component condition and alignment still require inspection.",
            "Toyota указывает для Camry XV70 заднюю многорычажную подвеску; состояние деталей и углы установки колёс требуют осмотра.",
            "Toyota Camry XV70 üçün arxa çoxqollu asqını göstərir; hissələrin vəziyyəti və təkər bucaqları baxış tələb edir.",
        ),
        (
            "body_safety",
            "toyota_press",
            EvidenceCategory.BODY,
            "body",
            EvidenceStatus.CONFIRMED,
            "The 2019 USA Camry is a TNGA-K sedan with Toyota Safety Sense P driver-assistance equipment documented as standard.",
            "Camry 2019 для США — седан на платформе TNGA-K; комплекс помощи водителю Toyota Safety Sense P указан как стандартный.",
            "ABŞ üçün 2019 Camry TNGA-K platformalı sedandır; Toyota Safety Sense P sürücüyə yardım kompleksi standart kimi göstərilib.",
        ),
        (
            "electronics",
            "toyota_press",
            EvidenceCategory.ELECTRICAL,
            "electrical",
            EvidenceStatus.CONFIRMED,
            "Toyota documents Entune 3.0 multimedia and Toyota Safety Sense P; operation of the fitted systems must be checked on the individual car.",
            "Toyota документирует мультимедиа Entune 3.0 и Toyota Safety Sense P; работу установленных систем нужно проверять на конкретной машине.",
            "Toyota Entune 3.0 multimedia və Toyota Safety Sense P sistemlərini sənədləşdirir; quraşdırılmış sistemlərin işi konkret avtomobildə yoxlanmalıdır.",
        ),
        (
            "maintenance",
            "toyota_maintenance",
            EvidenceCategory.MAINTENANCE,
            "engine",
            EvidenceStatus.CONFIRMED,
            "Toyota's USA maintenance guide uses scheduled 5,000-mile/6-month service points and condition-dependent maintenance; use the exact log and operating-condition notes rather than a universal interval.",
            "Руководство Toyota для США содержит сервисные точки через 5 000 миль/6 месяцев и операции, зависящие от условий; нужно сверять точный журнал, а не применять один универсальный интервал.",
            "Toyota-nın ABŞ təlimatında 5 000 mil/6 ay servis nöqtələri və şəraitdən asılı əməliyyatlar var; vahid interval əvəzinə dəqiq jurnal yoxlanmalıdır.",
        ),
        (
            "fuel",
            "epa_fuel",
            EvidenceCategory.FUEL,
            "fuel_consumption",
            EvidenceStatus.CONFIRMED,
            "EPA ratings for the gasoline 2.5 vary by trim: 28–29 mpg city, 39–41 mpg highway and 32–34 mpg combined; these are test-cycle values, not a promise of real consumption.",
            "Оценки EPA для бензинового 2.5 зависят от комплектации: 28–29 mpg город, 39–41 mpg трасса и 32–34 mpg смешанный цикл; это тестовые значения, а не обещание реального расхода.",
            "EPA göstəriciləri 2.5 benzin versiyasında komplektasiyaya görə dəyişir: şəhər 28–29 mpg, magistral 39–41 mpg, qarışıq 32–34 mpg; bunlar test göstəriciləridir, real sərfiyyat zəmanəti deyil.",
        ),
        (
            "usa_scope",
            "vpic",
            EvidenceCategory.SAFETY,
            "usa_vehicle",
            EvidenceStatus.CONFIRMED,
            "vPIC decodes manufacturer-submitted VIN attributes; model-year recall results do not prove that a specific VIN is affected or that a remedy is complete.",
            "vPIC расшифровывает переданные производителем атрибуты VIN; результаты recall по модели и году не доказывают применимость к конкретному VIN или выполнение ремонта.",
            "vPIC istehsalçının təqdim etdiyi VIN atributlarını açır; model və il üzrə recall nəticəsi konkret VIN-ə tətbiqi və təmirin tamamlandığını sübut etmir.",
        ),
    ]
    result = {}
    for key, source_key, category, section_key, status, en, ru, az in rows:
        item = TechnicalEvidence(
            vehicle_variant_id=variant.id,
            source_id=sources[source_key].id,
            category=category,
            title=key.replace("_", " ").title(),
            statement=en,
            status=status,
            confidence=(
                ConfidenceLevel.MEDIUM if source_key == "engine_reference" else ConfidenceLevel.HIGH
            ),
            market="US",
            conditions={
                "section_key": section_key,
                "translations": {"en": en, "ru": ru, "az": az},
            },
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        session.add(item)
        session.flush()
        result[key] = item

    recalls = [
        (
            "20V682000",
            "fuel pump",
            "The in-tank low-pressure fuel pump may fail and the engine may stall while driving.",
            "Насос низкого давления в баке может отказать, что может привести к остановке двигателя в движении.",
            "Çəndəki aşağı təzyiqli yanacaq nasosu sıradan çıxa və mühərrik hərəkətdə dayana bilər.",
        ),
        (
            "20V012000",
            "fuel pump",
            "Initial fuel-pump campaign later expanded by 20V682000; verify the current VIN-specific campaign record.",
            "Первоначальная кампания по топливному насосу позднее была расширена 20V682000; нужно проверить актуальную запись по VIN.",
            "İlkin yanacaq nasosu kampaniyası sonradan 20V682000 ilə genişləndirilib; cari VIN qeydi yoxlanmalıdır.",
        ),
        (
            "21V890000",
            "brake vacuum pump",
            "A vacuum-pump vane cap may break, reducing brake assist and increasing stopping effort.",
            "Крышка лопасти вакуумного насоса может разрушиться, уменьшив усиление тормозов и увеличив усилие на педали.",
            "Vakuum nasosunun qanad qapağı qırıla, əyləc gücləndirməsini azalda və pedal qüvvəsini artıra bilər.",
        ),
        (
            "19V567000",
            "occupant classification",
            "Incorrect occupant-classification calibration may prevent the front passenger and knee airbags from deploying as intended.",
            "Неверная калибровка системы классификации пассажира может помешать штатному срабатыванию передней пассажирской и коленной подушек.",
            "Sərnişin təsnifatı sisteminin səhv kalibrlənməsi ön sərnişin və diz hava yastıqlarının nəzərdə tutulduğu kimi açılmasına mane ola bilər.",
        ),
        (
            "19V503000",
            "load label",
            "Certain distributor-applied load-capacity labels may state an incorrect carrying capacity.",
            "На части автомобилей дилерская наклейка грузоподъёмности могла содержать неверное значение.",
            "Bəzi avtomobillərdə distribyutorun yük tutumu etiketi səhv dəyər göstərə bilər.",
        ),
        (
            "19V244000",
            "load label legibility",
            "Certain distributor-applied load labels may become illegible; VIN applicability must be checked.",
            "На части автомобилей маркировка грузоподъёмности могла стать нечитаемой; применимость нужно проверить по VIN.",
            "Bəzi avtomobillərdə yük etiketi oxunmaz ola bilər; tətbiq VIN üzrə yoxlanmalıdır.",
        ),
    ]
    for campaign, component, en, ru, az in recalls:
        item = TechnicalEvidence(
            vehicle_variant_id=variant.id,
            source_id=sources["nhtsa_recalls"].id,
            category=EvidenceCategory.SAFETY,
            title=f"NHTSA recall {campaign}: {component}",
            statement=en,
            status=EvidenceStatus.CONFIRMED,
            confidence=ConfidenceLevel.HIGH,
            market="US",
            conditions={
                "section_key": "recalls_tsb",
                "campaign_number": campaign,
                "model_level_only": True,
                "translations": {"en": en, "ru": ru, "az": az},
            },
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        session.add(item)
        session.flush()
        result[f"recall_{campaign}"] = item
    return result


def _known_issues(
    variant: VehicleVariant,
    evidence: dict[str, TechnicalEvidence],
) -> list[KnownIssue]:
    definitions = [
        (
            "Fuel pump",
            ["recall_20V012000", "recall_20V682000"],
            Severity.CRITICAL,
            "Official recalls cover a possible low-pressure fuel-pump failure on affected vehicles.",
            ["stalling", "rough running", "warning lamps"],
            "Verify campaign applicability and completion by VIN; confirm stable operation during a road test.",
        ),
        (
            "Brake vacuum pump",
            ["recall_21V890000"],
            Severity.CRITICAL,
            "An official recall covers possible loss of power-brake assist on affected vehicles.",
            ["hard brake pedal", "reduced brake assist"],
            "Verify recall completion by VIN and test brake-pedal assist before purchase.",
        ),
        (
            "Passenger airbag occupant classification",
            ["recall_19V567000"],
            Severity.CRITICAL,
            "An official recall covers incorrect occupant-classification calibration on affected vehicles.",
            ["airbag warning indicator", "passenger-airbag status inconsistency"],
            "Verify recall completion by VIN and scan the supplemental-restraint system for faults.",
        ),
        (
            "Low-speed acceleration hesitation",
            ["tsb_hesitation"],
            Severity.MEDIUM,
            "Toyota T-SB-0152-19 documents a specific low-speed hesitation condition on some vehicles.",
            ["hesitation after a rolling stop", "hesitation following a 3-to-1 downshift"],
            "Road-test below 6 mph from a rolling stop and verify ECM calibration applicability with Toyota service information.",
        ),
    ]
    return [
        KnownIssue(
            vehicle_variant_id=variant.id,
            component=component,
            description=description,
            affected_variants={
                "make": "Toyota",
                "model": "Camry",
                "year": 2019,
                "market": "US",
                "vin_applicability_required": True,
            },
            conditions={"translations": {}},
            symptoms=symptoms,
            consequences=None,
            typical_mileage_min=None,
            typical_mileage_max=None,
            severity=severity,
            evidence_ids=[evidence[key].id for key in keys],
            source_count=len({evidence[key].source_id for key in keys}),
            confidence=ConfidenceLevel.HIGH,
            inspection_recommendation=recommendation,
            status=EvidenceStatus.CONFIRMED,
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        for component, keys, severity, description, symptoms, recommendation in definitions
    ]


def _owner_sample(session: Session, variant: VehicleVariant, source: SourceRecord) -> None:
    rows = [
        (
            "11762892",
            "suspension",
            "strut_attachment",
            "Owner alleged simultaneous front strut separation while reversing.",
            None,
        ),
        (
            "11761489",
            "electrical",
            "door_lock_actuator",
            "Owner alleged repeated door-lock actuator failures; the report says no Toyota inspection confirmed it.",
            None,
        ),
        (
            "11758768",
            "engine",
            "coolant_pump",
            "Owner reported a dealer-diagnosed coolant-pump fault and overheating at about 47,000 miles.",
            75639,
        ),
        (
            "11756907",
            "engine",
            "stalling",
            "Owner alleged a stall with multiple warning lamps; the report says the vehicle was not diagnosed.",
            160934,
        ),
        (
            "11756617",
            "body",
            "windshield_cracking",
            "Owner alleged repeated large windshield cracks after small road-debris impacts.",
            None,
        ),
        (
            "11753170",
            "transmission",
            "transmission_noise",
            "Owner reported a dealer-confirmed transmission concern with a speed-related whine at about 65,000 miles.",
            104607,
        ),
        (
            "11689172",
            "electrical",
            "aftermarket_wiring",
            "Owner alleged faults associated with dealer-installed aftermarket anti-theft wiring; this is not treated as a factory defect.",
            None,
        ),
        (
            "11612627",
            "body",
            "bumper_attachment",
            "Owner alleged rear-bumper attachment failure; the submission does not establish a model-wide defect.",
            None,
        ),
        (
            "11589835",
            "fuel",
            "fuel_leak",
            "Owner alleged fuel leaking during refueling at about 58,000 miles; cause was not determined in the submission.",
            93342,
        ),
        (
            "11752091",
            "transmission",
            "transmission_noise",
            "Owner alleged a progressively worsening transmission whine; no diagnosis is included in the submission.",
            None,
        ),
    ]
    for odi, component, topic, summary, mileage_km in rows:
        material_key = f"nhtsa-odi-{odi}"
        dedupe = hashlib.sha256(
            f"{variant.id}|{material_key}|{topic}|{' '.join(summary.casefold().split())}".encode()
        ).hexdigest()
        session.add(
            OwnerEvidence(
                source_id=source.id,
                vehicle_variant_id=variant.id,
                owner_identity_key=None,
                material_identity_key=material_key,
                dedupe_key=dedupe,
                mileage_km=mileage_km,
                component=component,
                topic=topic,
                sentiment=Sentiment.NEGATIVE,
                issue_type="OWNER_ALLEGATION",
                excerpt=None,
                summary=summary,
                observed_at=None,
                is_demo=False,
                data_origin=DataOrigin.REAL,
            )
        )
