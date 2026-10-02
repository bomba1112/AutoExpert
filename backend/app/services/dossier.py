# ruff: noqa: E501

from __future__ import annotations

from datetime import UTC, datetime

from app.core.abbreviations import AbbreviationExplainer
from app.models.enums import DataOrigin, EvidenceCategory, EvidenceStatus, Severity
from app.models.evidence import KnownIssue, TechnicalEvidence
from app.models.vehicle_knowledge import VehicleKnowledgeProfile
from app.schemas.vin import (
    DossierClaim,
    DossierKnownIssue,
    DossierSection,
    VehicleDossier,
    VehicleKnowledgeProfileDTO,
)
from app.services.dossier_synthesis import localized_component, synthesize_evidence_claims

SECTION_TITLES = {
    "ru": {
        "expert_verdict": "Экспертный вывод",
        "general_information": "Общая информация",
        "engine": "Двигатель",
        "transmission": "Коробка передач",
        "suspension": "Подвеска / передок",
        "steering": "Рулевое",
        "brakes": "Тормоза",
        "steering_brakes": "Рулевое / тормоза",
        "body": "Кузов",
        "electrical": "Электрика / электроника",
        "fuel_consumption": "Расход",
        "weak_points": "Слабые места",
        "owner_experience": "Опыт владельцев",
        "recalls_tsb": "Отзывные кампании / бюллетени производителя",
        "recommended_version": "Какую версию лучше брать",
        "pre_purchase_check": "Что проверить перед покупкой",
        "usa_vehicle": "Автомобиль из США",
        "sources": "Источники",
    },
    "az": {
        "expert_verdict": "Ekspert rəyi",
        "general_information": "Ümumi məlumat",
        "engine": "Mühərrik",
        "transmission": "Sürətlər qutusu",
        "suspension": "Asqı / ön hissə",
        "steering": "Sükan sistemi",
        "brakes": "Əyləclər",
        "steering_brakes": "Sükan / əyləclər",
        "body": "Kuzov",
        "electrical": "Elektrik / elektronika",
        "fuel_consumption": "Yanacaq sərfiyyatı",
        "weak_points": "Zəif nöqtələr",
        "owner_experience": "Sahib təcrübəsi",
        "recalls_tsb": "Geri çağırmalar / istehsalçı bülletenləri",
        "recommended_version": "Hansı versiyanı seçmək",
        "pre_purchase_check": "Almazdan əvvəl nəyi yoxlamaq",
        "usa_vehicle": "ABŞ-dan gətirilmiş avtomobil",
        "sources": "Mənbələr",
    },
    "en": {
        "expert_verdict": "Expert Verdict",
        "general_information": "General Information",
        "engine": "Engine",
        "transmission": "Transmission",
        "suspension": "Suspension / Front End",
        "steering": "Steering",
        "brakes": "Brakes",
        "steering_brakes": "Steering / Brakes",
        "body": "Body",
        "electrical": "Electrical / Electronics",
        "fuel_consumption": "Fuel Consumption",
        "weak_points": "Weak Points",
        "owner_experience": "Owner Experience",
        "recalls_tsb": "Recalls / Manufacturer Bulletins",
        "recommended_version": "Which Version to Choose",
        "pre_purchase_check": "Pre-purchase Checklist",
        "usa_vehicle": "USA Vehicle Section",
        "sources": "Sources",
    },
}

EMPTY_DATA = {
    "ru": "Данные пока не подтверждены.",
    "az": "Məlumat hələ təsdiqlənməyib.",
    "en": "The data has not yet been confirmed.",
}

INSPECTION_NOTICE = {
    "ru": "Состояние конкретного экземпляра требует физической проверки.",
    "az": "Konkret avtomobilin vəziyyəti fiziki yoxlama tələb edir.",
    "en": "The condition of the specific vehicle requires a physical inspection.",
}

DEMO_VERDICT = {
    "ru": "DEMO: автомобиль определён; вывод основан только на синтетическом наборе данных.",
    "az": "DEMO: avtomobil müəyyən edilib; nəticə yalnız sintetik məlumatlara əsaslanır.",
    "en": "DEMO: the vehicle is resolved; the verdict uses synthetic data only.",
}

OWNER_EMPTY = {
    "ru": (
        "Подтверждённая выборка материалов владельцев для этого профиля не подключена. "
        "Процент неисправностей автомобилей не рассчитывается."
    ),
    "az": (
        "Bu profil üçün təsdiqlənmiş sahib materialları seçimi qoşulmayıb. "
        "Avtomobillərin nasazlıq faizi hesablanmır."
    ),
    "en": (
        "No confirmed owner-material sample is connected to this profile. "
        "No fleet-wide failure percentage is calculated."
    ),
}


def profile_dto(profile: VehicleKnowledgeProfile) -> VehicleKnowledgeProfileDTO:
    vin_identity = profile.dossier_seed.get("vin_identity", {})
    return VehicleKnowledgeProfileDTO(
        id=profile.id,
        make=profile.make,
        model=profile.model,
        generation=profile.generation,
        production_year_start=profile.production_year_start,
        production_year_end=profile.production_year_end,
        market=profile.market,
        year=profile.year,
        trim=vin_identity.get("trim") or vin_identity.get("series"),
        engine=profile.engine,
        engine_code=profile.engine_code,
        transmission=profile.transmission,
        drivetrain=profile.drivetrain,
        body=profile.body,
        fuel=profile.fuel,
        profile_version=profile.profile_version,
        freshness_at=profile.freshness_at,
        source_ids=[item.id for item in profile.sources],
        evidence_ids=[item.id for item in profile.evidence],
        is_demo=profile.is_demo,
        data_origin=profile.data_origin,
    )


def build_vehicle_dossier(
    profile: VehicleKnowledgeProfile,
    *,
    language: str,
    known_issues: list[KnownIssue],
    owner_feedback=None,  # noqa: ANN001
    owner_source_ids: list[str] | None = None,
    official_complaints_feedback=None,  # noqa: ANN001
    official_complaint_source_ids: list[str] | None = None,
) -> VehicleDossier:
    language = language if language in SECTION_TITLES else "ru"
    if profile.data_origin == DataOrigin.REAL:
        return _build_real_dossier(
            profile,
            language=language,
            known_issues=known_issues,
            owner_feedback=owner_feedback,
            owner_source_ids=owner_source_ids or [],
            official_complaints_feedback=official_complaints_feedback,
            official_complaint_source_ids=official_complaint_source_ids or [],
        )
    titles = SECTION_TITLES[language]
    glossary = AbbreviationExplainer(language)
    sources = [item.id for item in profile.sources]
    evidence_by_category: dict[EvidenceCategory, TechnicalEvidence] = {}
    for item in profile.evidence:
        evidence_by_category.setdefault(item.category, item)

    general_text = _general_claim(profile, language, glossary)
    identity_evidence = next(iter(profile.evidence), None)
    identity_evidence_ids = [identity_evidence.id] if identity_evidence else []
    identity_source_ids = [identity_evidence.source_id] if identity_evidence else sources
    identity_status = (
        identity_evidence.status if identity_evidence else EvidenceStatus.INSUFFICIENT_DATA
    )

    sections: list[DossierSection] = [
        DossierSection(
            key="expert_verdict",
            title=titles["expert_verdict"],
            summary=DEMO_VERDICT[language],
            claims=[
                DossierClaim(
                    text=DEMO_VERDICT[language],
                    status=EvidenceStatus.ESTIMATE,
                    source_ids=identity_source_ids,
                    evidence_ids=identity_evidence_ids,
                )
            ],
        ),
        DossierSection(
            key="general_information",
            title=titles["general_information"],
            summary=general_text,
            claims=[
                DossierClaim(
                    text=general_text,
                    status=identity_status,
                    source_ids=identity_source_ids,
                    evidence_ids=identity_evidence_ids,
                )
            ],
        ),
    ]

    sections.extend(
        [
            _technical_section(
                "engine",
                titles,
                evidence_by_category.get(EvidenceCategory.ENGINE),
                _engine_claim(profile, language, glossary),
                language,
            ),
            _technical_section(
                "transmission",
                titles,
                evidence_by_category.get(EvidenceCategory.TRANSMISSION),
                _transmission_claim(profile, language, glossary),
                language,
            ),
            _technical_section(
                "suspension",
                titles,
                evidence_by_category.get(EvidenceCategory.SUSPENSION),
                None,
                language,
            ),
            _technical_section(
                "steering",
                titles,
                evidence_by_category.get(EvidenceCategory.STEERING),
                None,
                language,
            ),
            _technical_section(
                "brakes",
                titles,
                evidence_by_category.get(EvidenceCategory.BRAKES),
                None,
                language,
            ),
            _technical_section(
                "body",
                titles,
                evidence_by_category.get(EvidenceCategory.BODY),
                None,
                language,
            ),
            _technical_section(
                "electrical",
                titles,
                evidence_by_category.get(EvidenceCategory.ELECTRICAL),
                None,
                language,
            ),
            _technical_section(
                "fuel_consumption",
                titles,
                evidence_by_category.get(EvidenceCategory.FUEL),
                None,
                language,
            ),
        ]
    )

    sections.append(
        DossierSection(
            key="weak_points",
            title=titles["weak_points"],
            summary=(EMPTY_DATA[language] if not known_issues else DEMO_VERDICT[language]),
            known_issues=[
                _issue_snapshot(issue, profile.evidence, language) for issue in known_issues
            ],
        )
    )
    sections.append(
        DossierSection(
            key="owner_experience",
            title=titles["owner_experience"],
            summary=OWNER_EMPTY[language],
            claims=[
                DossierClaim(
                    text=OWNER_EMPTY[language],
                    status=EvidenceStatus.INSUFFICIENT_DATA,
                )
            ],
        )
    )
    tsb = glossary.render("TSB")
    closing_sections = [
        DossierSection(
            key="recalls_tsb",
            title=titles["recalls_tsb"],
            summary=f"{tsb}. {EMPTY_DATA[language]}",
            claims=[
                DossierClaim(
                    text=EMPTY_DATA[language],
                    status=EvidenceStatus.INSUFFICIENT_DATA,
                )
            ],
        ),
        DossierSection(
            key="recommended_version",
            title=titles["recommended_version"],
            summary=EMPTY_DATA[language],
            claims=[
                DossierClaim(
                    text=EMPTY_DATA[language],
                    status=EvidenceStatus.INSUFFICIENT_DATA,
                )
            ],
        ),
        DossierSection(
            key="pre_purchase_check",
            title=titles["pre_purchase_check"],
            summary=INSPECTION_NOTICE[language],
            claims=[
                DossierClaim(
                    text=INSPECTION_NOTICE[language],
                    status=EvidenceStatus.NEEDS_INSPECTION,
                )
            ],
        ),
    ]
    if profile.market.upper() in {"US", "USA"}:
        closing_sections.append(
            DossierSection(
                key="usa_vehicle",
                title=titles["usa_vehicle"],
                summary=INSPECTION_NOTICE[language],
                claims=[
                    DossierClaim(
                        text=INSPECTION_NOTICE[language],
                        status=EvidenceStatus.NEEDS_INSPECTION,
                    )
                ],
            )
        )
    closing_sections.append(
        DossierSection(
            key="sources",
            title=titles["sources"],
            summary=_source_summary(len(sources), language),
        )
    )
    sections.extend(closing_sections)

    return VehicleDossier(
        language=language,
        vehicle=profile_dto(profile),
        expert_verdict=DEMO_VERDICT[language],
        inspection_notice=INSPECTION_NOTICE[language],
        sections=sections,
        source_ids=sources,
        generated_at=datetime.now(UTC),
        is_demo=profile.is_demo,
    )


def _technical_section(
    key: str,
    titles: dict[str, str],
    evidence: TechnicalEvidence | None,
    claim_text: str | None,
    language: str,
) -> DossierSection:
    if evidence is None:
        return DossierSection(
            key=key,
            title=titles[key],
            summary=EMPTY_DATA[language],
            claims=[
                DossierClaim(
                    text=EMPTY_DATA[language],
                    status=EvidenceStatus.INSUFFICIENT_DATA,
                )
            ],
        )
    text = claim_text or evidence.statement
    return DossierSection(
        key=key,
        title=titles[key],
        summary=text,
        claims=[
            DossierClaim(
                text=text,
                status=evidence.status,
                source_ids=[evidence.source_id],
                evidence_ids=[evidence.id],
            )
        ],
    )


def _issue_snapshot(
    issue: KnownIssue,
    evidence: list[TechnicalEvidence],
    language: str = "en",
) -> DossierKnownIssue:
    evidence_map = {item.id: item for item in evidence}
    source_ids = list(
        dict.fromkeys(
            evidence_map[evidence_id].source_id
            for evidence_id in issue.evidence_ids
            if evidence_id in evidence_map
        )
    )
    severity = issue.severity.value
    if issue.severity == Severity.LOW:
        severity = Severity.MINOR.value
    elif issue.severity == Severity.HIGH:
        severity = Severity.CRITICAL.value
    mileage = None
    if issue.typical_mileage_min is not None and issue.typical_mileage_max is not None:
        mileage = [issue.typical_mileage_min, issue.typical_mileage_max]
    localized = next(
        (
            _localized_statement(evidence_map[evidence_id], language)
            for evidence_id in issue.evidence_ids
            if evidence_id in evidence_map
        ),
        issue.description,
    )
    return DossierKnownIssue(
        component=issue.component,
        description=localized if language != "en" else issue.description,
        affected_variant=issue.affected_variants,
        symptoms=issue.symptoms,
        mileage_range=mileage,
        consequences=issue.consequences,
        inspection_recommendation=issue.inspection_recommendation,
        severity=severity,
        confidence=issue.confidence,
        status=issue.status,
        source_ids=source_ids,
        evidence_ids=issue.evidence_ids,
        source_count=issue.source_count,
    )


def _build_real_dossier(
    profile: VehicleKnowledgeProfile,
    *,
    language: str,
    known_issues: list[KnownIssue],
    owner_feedback,  # noqa: ANN001
    owner_source_ids: list[str],
    official_complaints_feedback,  # noqa: ANN001
    official_complaint_source_ids: list[str],
) -> VehicleDossier:
    titles = SECTION_TITLES[language]
    grouped: dict[str, list[TechnicalEvidence]] = {}
    for item in profile.evidence:
        if item.data_origin != DataOrigin.REAL or item.source.data_origin != DataOrigin.REAL:
            raise ValueError("REAL VehicleKnowledgeProfile cannot contain DEMO evidence or sources")
        if item.conditions.get("excluded_from_synthesis"):
            continue
        key = str(item.conditions.get("section_key") or item.category.value)
        grouped.setdefault(key, []).append(item)

    def section(key: str) -> DossierSection:
        items = grouped.get(key, [])
        claims = synthesize_evidence_claims(items, language)
        if not claims:
            return DossierSection(
                key=key,
                title=titles[key],
                summary=EMPTY_DATA[language],
                is_empty=True,
            )
        return DossierSection(
            key=key,
            title=titles[key],
            summary=claims[0].heading or claims[0].text,
            claims=claims,
        )

    sections = [section("expert_verdict"), section("general_information")]
    sections.extend(section(key) for key in ("engine", "transmission", "suspension"))

    brake_issues = [
        item
        for item in known_issues
        if any(word in item.component.casefold() for word in ("brake", "steer"))
    ]
    steering_brake_claims = synthesize_evidence_claims(
        [*grouped.get("steering", []), *grouped.get("brakes", [])], language
    )
    steering_brake_summary = EMPTY_DATA[language]
    if steering_brake_claims:
        steering_brake_summary = steering_brake_claims[0].heading or steering_brake_claims[0].text
    elif brake_issues:
        linked = next(
            (item for item in profile.evidence if item.id in brake_issues[0].evidence_ids),
            None,
        )
        if linked is not None:
            steering_brake_summary = _localized_statement(linked, language)
    sections.append(
        DossierSection(
            key="steering_brakes",
            title=titles["steering_brakes"],
            summary=steering_brake_summary,
            claims=steering_brake_claims,
            known_issues=[
                _issue_snapshot(item, profile.evidence, language) for item in brake_issues
            ],
            is_empty=not steering_brake_claims and not brake_issues,
        )
    )
    sections.extend(section(key) for key in ("body", "electrical", "fuel_consumption"))
    sections.append(
        DossierSection(
            key="weak_points",
            title=titles["weak_points"],
            summary=_weak_points_summary(len(known_issues), language),
            known_issues=[
                _issue_snapshot(item, profile.evidence, language) for item in known_issues
            ],
            is_empty=not known_issues,
        )
    )
    sections.append(
        _real_owner_section(
            language,
            owner_feedback,
            owner_source_ids,
            official_complaints_feedback,
            official_complaint_source_ids,
        )
    )
    sections.append(section("recalls_tsb"))

    output = next((item for item in profile.evidence if item.title == "Engine Output"), None)
    fuel = next((item for item in profile.evidence if item.category == EvidenceCategory.FUEL), None)
    recommendation_sources = [item.source_id for item in (output, fuel) if item]
    recommendation_evidence = [item.id for item in (output, fuel) if item]
    recommendation = {
        "ru": "Единственную «лучшую» версию без приоритетов покупателя назвать нельзя. Сравнивайте только подтверждённые комплектации, мощность, расход и доступность обслуживания.",
        "az": "Alıcının prioritetləri olmadan yeganə «ən yaxşı» versiyanı seçmək olmaz. Yalnız təsdiqlənmiş komplektasiyanı, gücü, sərfiyyatı və servis əlçatanlığını müqayisə edin.",
        "en": "There is no single supported ‘best’ version without buyer priorities. Compare only confirmed grades, output, fuel economy, and service availability.",
    }[language]
    if recommendation_sources:
        recommendation_claim = DossierClaim(
            text=recommendation,
            status=EvidenceStatus.ESTIMATE,
            source_ids=recommendation_sources,
            evidence_ids=recommendation_evidence,
        )
    else:
        recommendation = EMPTY_DATA[language]
        recommendation_claim = None
    sections.append(
        DossierSection(
            key="recommended_version",
            title=titles["recommended_version"],
            summary=recommendation,
            claims=[recommendation_claim] if recommendation_claim else [],
            is_empty=recommendation_claim is None,
        )
    )
    checklist = _checklist_text(language)
    issue_source_ids = list(
        dict.fromkeys(
            source_id
            for issue in (
                _issue_snapshot(item, profile.evidence, language) for item in known_issues
            )
            for source_id in issue.source_ids
        )
    )
    issue_evidence_ids = list(
        dict.fromkeys(evidence_id for item in known_issues for evidence_id in item.evidence_ids)
    )
    sections.append(
        DossierSection(
            key="pre_purchase_check",
            title=titles["pre_purchase_check"],
            summary=checklist,
            claims=[
                DossierClaim(
                    text=INSPECTION_NOTICE[language],
                    status=EvidenceStatus.NEEDS_INSPECTION,
                    heading={
                        "ru": "Базовая проверка перед покупкой",
                        "az": "Alışdan əvvəl əsas yoxlama",
                        "en": "Core pre-purchase inspection",
                    }[language],
                    why_it_matters=INSPECTION_NOTICE[language],
                    what_to_check=checklist,
                    kind="inspection_checklist",
                    source_ids=issue_source_ids,
                    evidence_ids=issue_evidence_ids,
                )
            ],
        )
    )
    sections.append(section("usa_vehicle"))
    sources_summary = _source_summary_real(len(profile.sources), language)
    sections.append(DossierSection(key="sources", title=titles["sources"], summary=sources_summary))
    verdict = sections[0].summary
    return VehicleDossier(
        dossier_version="3.1.0-consumer.1",
        language=language,
        vehicle=profile_dto(profile),
        expert_verdict=verdict,
        inspection_notice=INSPECTION_NOTICE[language],
        sections=sections,
        source_ids=[item.id for item in profile.sources],
        generated_at=datetime.now(UTC),
        is_demo=False,
    )


def _localized_statement(item: TechnicalEvidence, language: str) -> str:
    translations = item.conditions.get("translations", {})
    return str(translations.get(language) or translations.get("en") or item.statement)


def _weak_points_summary(count: int, language: str) -> str:
    if count == 0:
        return {
            "ru": "Подтверждённых слабых мест пока нет. Одна жалоба не считается доказанным дефектом модели.",
            "az": "Hələ təsdiqlənmiş zəif nöqtə yoxdur. Tək şikayət model qüsurunu sübut etmir.",
            "en": "No weak point is confirmed yet. A single complaint is not treated as a proven model defect.",
        }[language]
    return {
        "ru": f"Подтверждённых слабых мест модели: {count}. Применимость к конкретной версии и состояние машины проверяются отдельно.",
        "az": f"Model üzrə təsdiqlənmiş zəif nöqtələr: {count}. Konkret versiyaya tətbiq və avtomobilin vəziyyəti ayrıca yoxlanılır.",
        "en": f"Confirmed model-level weak points: {count}. Applicability to the exact version and vehicle condition require separate checks.",
    }[language]


def _real_owner_section(  # noqa: ANN001
    language: str,
    aggregation,
    source_ids: list[str],
    official_aggregation,
    official_source_ids: list[str],
) -> DossierSection:
    title = SECTION_TITLES[language]["owner_experience"]
    owner_count = aggregation.unique_material_count if aggregation is not None else 0
    official_count = (
        official_aggregation.unique_material_count if official_aggregation is not None else 0
    )
    if owner_count == 0 and official_count == 0:
        return DossierSection(
            key="owner_experience",
            title=title,
            summary=EMPTY_DATA[language],
            is_empty=True,
        )
    claims: list[DossierClaim] = []
    if owner_count:
        claims.extend(
            _feedback_claims(
                language,
                aggregation,
                source_ids,
                official=False,
            )
        )
    if official_count:
        claims.extend(
            _feedback_claims(
                language,
                official_aggregation,
                official_source_ids,
                official=True,
            )
        )
    summary_parts = []
    if owner_count:
        summary_parts.append(
            {
                "ru": f"Опыт владельцев: {owner_count} уникальных материалов.",
                "az": f"Sahib təcrübəsi: {owner_count} unikal material.",
                "en": f"Owner experience: {owner_count} unique materials.",
            }[language]
        )
    else:
        summary_parts.append(
            {
                "ru": "Независимая выборка опыта владельцев пока не подключена.",
                "az": "Müstəqil sahib təcrübəsi nümunəsi hələ qoşulmayıb.",
                "en": "No independent owner-experience sample is connected yet.",
            }[language]
        )
    if official_count:
        summary_parts.append(
            {
                "ru": f"Отдельно изучены {official_count} жалоб из официальной базы NHTSA.",
                "az": f"Ayrıca NHTSA rəsmi bazasından {official_count} şikayət öyrənilib.",
                "en": f"Separately, {official_count} complaints from the official NHTSA repository were reviewed.",
            }[language]
        )
    summary = " ".join(summary_parts)
    return DossierSection(key="owner_experience", title=title, summary=summary, claims=claims)


def _feedback_claims(  # noqa: ANN001
    language: str,
    aggregation,
    source_ids: list[str],
    *,
    official: bool,
) -> list[DossierClaim]:
    claims: list[DossierClaim] = []
    heading = {
        "ru": "Жалобы в официальной базе" if official else "Опыт владельцев",
        "az": "Rəsmi bazadakı şikayətlər" if official else "Sahib təcrübəsi",
        "en": "Complaints in the official repository" if official else "Owner experience",
    }[language]
    noun = {
        "ru": "жалоб" if official else "материалов",
        "az": "şikayətdən" if official else "materialdan",
        "en": "complaints" if official else "materials",
    }[language]
    for topic in aggregation.topics:
        topic_name = localized_component(topic.topic, language)
        share = round(topic.mention_share * 100)
        percentage = (
            {
                "ru": f" ({share}% изученной выборки)",
                "az": f" (öyrənilmiş nümunənin {share}%-i)",
                "en": f" ({share}% of the reviewed sample)",
            }[language]
            if topic.show_percentage
            else ""
        )
        text = {
            "ru": f"Тема «{topic_name}» упоминалась в {topic.material_mentions} из {topic.sample_size} изученных {noun}{percentage}. Это не вероятность поломки автомобилей.",
            "az": f"«{topic_name}» mövzusu öyrənilmiş {topic.sample_size} {noun} {topic.material_mentions}-də qeyd olunub{percentage}. Bu, avtomobillərin nasazlıq ehtimalı deyil.",
            "en": f"The topic “{topic_name}” appeared in {topic.material_mentions} of {topic.sample_size} reviewed {noun}{percentage}. This is not a vehicle failure probability.",
        }[language]
        claims.append(
            DossierClaim(
                heading=heading,
                text=text,
                status=EvidenceStatus.ESTIMATE,
                source_ids=source_ids,
                kind="official_complaint_sample" if official else "owner_experience_sample",
                why_it_matters={
                    "ru": "Это сигнал для проверки, а не подтверждённый дефект модели или этого автомобиля.",
                    "az": "Bu, yoxlama üçün siqnaldır, modelin və ya bu avtomobilin təsdiqlənmiş qüsuru deyil.",
                    "en": "This is a reason to inspect, not a confirmed defect in the model or this vehicle.",
                }[language],
                what_to_check={
                    "ru": "Сопоставьте сообщения с независимыми источниками, историей обслуживания и результатами диагностики этого узла.",
                    "az": "Məlumatları müstəqil mənbələr, qulluq tarixçəsi və bu sistemin diaqnostika nəticələri ilə tutuşdurun.",
                    "en": "Cross-check the reports against independent sources, service history and diagnostics of this system.",
                }[language],
                original_available=True,
            )
        )
    return claims


def _checklist_text(language: str) -> str:
    return {
        "ru": "Сверьте VIN и документы; проверьте открытые отзывные кампании и подтверждение их выполнения; проведите холодный и прогретый тест-драйв; выполните компьютерную диагностику двигателя, коробки, антиблокировочной системы тормозов (ABS), подушек и преднатяжителей ремней безопасности (SRS); осмотрите силовые элементы кузова и качество ремонта.",
        "az": "VIN və sənədləri tutuşdurun; açıq geri çağırmaları və onların icrasını yoxlayın; soyuq və isti test sürüşü edin; mühərrik, sürətlər qutusu, təkərlərin bloklanmasının qarşısını alan əyləc sistemini (ABS), təhlükəsizlik yastıqlarını və kəmər dartıcılarını (SRS) kompüterlə yoxlayın; kuzovun daşıyıcı elementlərini və təmir keyfiyyətini nəzərdən keçirin.",
        "en": "Match the VIN and documents; check open recalls and proof of completion; road-test from cold and fully warm; scan the engine, transmission, anti-lock braking system (ABS), airbags and seat-belt pretensioners (SRS); inspect structural body members and repair quality.",
    }[language]


def _source_summary_real(count: int, language: str) -> str:
    return {
        "ru": f"В отчёте использовано источников: {count}. Для каждого важного вывода сохранены источник и дата получения.",
        "az": f"Hesabatda {count} mənbədən istifadə olunub. Hər vacib nəticə üçün mənbə və alınma tarixi saxlanılıb.",
        "en": f"Sources used in this report: {count}. Each important conclusion retains its source and retrieval date.",
    }[language]


def _general_claim(
    profile: VehicleKnowledgeProfile,
    language: str,
    glossary: AbbreviationExplainer,
) -> str:
    vin = glossary.render("VIN")
    engine = glossary.render(profile.engine_code) if profile.engine_code else profile.engine
    transmission = glossary.render(profile.transmission) if profile.transmission else "—"
    drivetrain = glossary.render(profile.drivetrain) if profile.drivetrain else "—"
    if language == "az":
        return (
            f"{profile.year} {profile.make} {profile.model} {profile.generation}, "
            f"bazar: {profile.market}. {engine}; {transmission}; {drivetrain}. {vin}."
        )
    if language == "en":
        return (
            f"{profile.year} {profile.make} {profile.model} {profile.generation}, "
            f"market: {profile.market}. {engine}; {transmission}; {drivetrain}. {vin}."
        )
    return (
        f"{profile.year} {profile.make} {profile.model} {profile.generation}, "
        f"рынок: {profile.market}. {engine}; {transmission}; {drivetrain}. {vin}."
    )


def _engine_claim(
    profile: VehicleKnowledgeProfile,
    language: str,
    glossary: AbbreviationExplainer,
) -> str:
    code = glossary.render(profile.engine_code) if profile.engine_code else profile.engine or "—"
    prefix = {"ru": "Двигатель", "az": "Mühərrik", "en": "Engine"}[language]
    return f"{prefix}: {code}. DEMO DATA."


def _transmission_claim(
    profile: VehicleKnowledgeProfile,
    language: str,
    glossary: AbbreviationExplainer,
) -> str:
    value = glossary.render(profile.transmission) if profile.transmission else "—"
    prefix = {"ru": "Коробка", "az": "Sürətlər qutusu", "en": "Transmission"}[language]
    return f"{prefix}: {value}. DEMO DATA."


def _source_summary(count: int, language: str) -> str:
    if language == "az":
        return f"Profil snapshot-ında {count} DEMO mənbə saxlanılıb."
    if language == "en":
        return f"The profile snapshot contains {count} DEMO source(s)."
    return f"В snapshot профиля сохранено DEMO-источников: {count}."
