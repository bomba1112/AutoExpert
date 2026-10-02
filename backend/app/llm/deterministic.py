from __future__ import annotations

from app.models.enums import EvidenceStatus
from app.schemas.analysis import (
    EvidenceBundle,
    GeneratedReport,
    GeneratedSection,
    GroundedClaim,
)

_COPY = {
    "ru": {
        "verdict": "Итог для ваших условий: {rating} ({score}/100).",
        "inspection": "Состояние конкретного экземпляра требует физической проверки.",
        "insufficient": "Недостаточно подтверждённых данных.",
        "market": (
            "В изученной выборке из {count} сопоставимых объявлений "
            "медиана составляет {median} {currency}."
        ),
        "owners": (
            "Проанализировано уникальных материалов владельцев: {count}. "
            "Доля упоминаний относится только к изученной выборке."
        ),
        "fuel": (
            "Оценочный годовой расход на топливо: {low}–{high} {currency} при указанных допущениях."
        ),
    },
    "az": {
        "verdict": "Şəraitiniz üçün nəticə: {rating} ({score}/100).",
        "inspection": "Konkret avtomobilin vəziyyəti fiziki yoxlama tələb edir.",
        "insufficient": "Təsdiqlənmiş məlumat kifayət deyil.",
        "market": (
            "Araşdırılmış {count} müqayisə edilə bilən elanda median qiymət "
            "{median} {currency} təşkil edir."
        ),
        "owners": (
            "Unikal sahib materialları təhlil edilib: {count}. "
            "Qeyd faizləri yalnız araşdırılmış nümunəyə aiddir."
        ),
        "fuel": (
            "Göstərilən fərziyyələrə əsasən illik yanacaq xərci təxminən "
            "{low}–{high} {currency} təşkil edir."
        ),
    },
    "en": {
        "verdict": "Fit for your conditions: {rating} ({score}/100).",
        "inspection": "The condition of this specific vehicle requires a physical inspection.",
        "insufficient": "Insufficient confirmed data.",
        "market": (
            "Across {count} comparable listings in the reviewed sample, "
            "the median asking price is {median} {currency}."
        ),
        "owners": (
            "Unique owner materials reviewed: {count}. "
            "Mention shares apply only to the reviewed sample."
        ),
        "fuel": (
            "Estimated annual fuel cost is {low}–{high} {currency} under the stated assumptions."
        ),
    },
}

_TITLES = {
    "ru": [
        "Экспертный вывод",
        "Автомобиль",
        "Двигатель",
        "Коробка передач",
        "Подвеска / передок",
        "Рулевое управление / тормоза",
        "Кузов / электроника",
        "Расход топлива",
        "Пригодность",
        "Местный рынок",
        "Расходы владения",
        "Опыт владельцев",
        "Проверка перед покупкой",
        "Альтернативы",
        "Источники",
    ],
    "az": [
        "Ekspert rəyi",
        "Avtomobil",
        "Mühərrik",
        "Sürətlər qutusu",
        "Asqı / ön hissə",
        "Sükan / əyləclər",
        "Kuzov / elektronika",
        "Yanacaq sərfiyyatı",
        "Uyğunluq",
        "Yerli bazar",
        "Sahiblik xərcləri",
        "Sahib təcrübəsi",
        "Alışdan əvvəl yoxlama",
        "Alternativlər",
        "Mənbələr",
    ],
    "en": [
        "Expert Verdict",
        "Vehicle",
        "Engine",
        "Transmission",
        "Suspension / Front End",
        "Steering / Brakes",
        "Body / Electronics",
        "Fuel Consumption",
        "Suitability",
        "Local Market",
        "Ownership Costs",
        "Owner Feedback",
        "Pre-purchase Inspection",
        "Alternatives",
        "Sources",
    ],
}

_KEYS = [
    "expert_verdict",
    "vehicle",
    "engine",
    "transmission",
    "suspension",
    "steering_brakes",
    "body_electronics",
    "fuel_consumption",
    "suitability",
    "local_market",
    "ownership_costs",
    "owner_feedback",
    "inspection",
    "alternatives",
    "sources",
]


class DeterministicLLMProvider:
    """Development provider that only formats facts already present in the bundle."""

    def generate_report(self, bundle: EvidenceBundle, language: str) -> GeneratedReport:
        language = language if language in _COPY else "en"
        copy = _COPY[language]
        sections = [
            GeneratedSection(key=key, title=title, summary=copy["insufficient"], claims=[])
            for key, title in zip(_KEYS, _TITLES[language], strict=True)
        ]
        by_key = {section.key: section for section in sections}

        verdict_text = copy["verdict"].format(
            rating=bundle.fit_analysis.rating.value,
            score=bundle.fit_analysis.score,
        )
        by_key["expert_verdict"].summary = verdict_text
        by_key["expert_verdict"].claims = [
            GroundedClaim(
                text=verdict_text,
                status=EvidenceStatus.ESTIMATE,
                evidence_ids=["fit_analysis"],
            )
        ]
        by_key["suitability"].summary = verdict_text
        by_key["suitability"].claims = list(by_key["expert_verdict"].claims)

        category_map = {
            "engine": "engine",
            "transmission": "transmission",
            "suspension": "suspension",
            "steering": "steering_brakes",
            "brakes": "steering_brakes",
            "body": "body_electronics",
            "electrical": "body_electronics",
            "fuel": "fuel_consumption",
        }
        for evidence in bundle.technical_evidence:
            section_key = category_map.get(evidence.category)
            if not section_key:
                continue
            section = by_key[section_key]
            section.claims.append(
                GroundedClaim(
                    text=evidence.statement,
                    status=evidence.status,
                    evidence_ids=[evidence.id],
                )
            )
            section.summary = section.claims[0].text

        market = bundle.market_analysis
        if market.status != EvidenceStatus.INSUFFICIENT_DATA and market.median is not None:
            market_text = copy["market"].format(
                count=market.used_count, median=market.median, currency=market.currency
            )
            by_key["local_market"].summary = market_text
            by_key["local_market"].claims = [
                GroundedClaim(
                    text=market_text,
                    status=EvidenceStatus.ESTIMATE,
                    evidence_ids=["market_analysis"],
                )
            ]

        ownership = bundle.ownership_calculation
        if ownership.yearly_fuel is not None:
            fuel_text = copy["fuel"].format(
                low=ownership.yearly_fuel.low,
                high=ownership.yearly_fuel.high,
                currency=ownership.yearly_fuel.currency,
            )
            by_key["ownership_costs"].summary = fuel_text
            by_key["ownership_costs"].claims = [
                GroundedClaim(
                    text=fuel_text,
                    status=EvidenceStatus.ESTIMATE,
                    evidence_ids=["ownership_calculation"],
                )
            ]

        owner_text = copy["owners"].format(count=bundle.owner_feedback.unique_material_count)
        by_key["owner_feedback"].summary = owner_text
        by_key["owner_feedback"].claims = [
            GroundedClaim(
                text=owner_text,
                status=EvidenceStatus.ESTIMATE,
                evidence_ids=["owner_feedback"],
            )
        ]

        inspection_claims = [
            GroundedClaim(
                text=issue.inspection_recommendation,
                status=EvidenceStatus.NEEDS_INSPECTION,
                evidence_ids=[issue.id],
            )
            for issue in bundle.known_issues
        ]
        by_key["inspection"].summary = copy["inspection"]
        by_key["inspection"].claims = inspection_claims
        by_key["sources"].summary = f"{len(bundle.sources)}"
        return GeneratedReport(
            language=language,
            verdict=bundle.fit_analysis.rating,
            verdict_summary=verdict_text,
            inspection_notice=copy["inspection"],
            sections=sections,
        )

    def answer_question(self, bundle: EvidenceBundle, question: str, language: str) -> str:
        language = language if language in _COPY else "en"
        normalized = question.casefold()
        if self._contains(
            normalized,
            ("цен", "скид", "уступ", "price", "discount", "qiymət", "endirim"),
        ):
            market = bundle.market_analysis
            if market.median is None:
                return _COPY[language]["insufficient"]
            values = {
                "median": market.median,
                "currency": market.currency,
                "selected": market.selected_price,
                "deviation": market.percentage_deviation,
                "count": market.used_count,
            }
            templates = {
                "ru": (
                    "По snapshot отчёта медиана {median} {currency}; цена выбранной машины — "
                    "{selected} {currency}, отклонение — {deviation}%. Расчёт основан на "
                    "{count} сопоставимых объявлениях после удаления выбросов. Это оценка "
                    "цен предложений, а не подтверждённая цена сделки."
                ),
                "az": (
                    "Hesabat snapshot-ına görə median {median} {currency}, seçilmiş avtomobilin "
                    "qiyməti {selected} {currency}, fərq {deviation}%-dir. Hesablamada kənar "
                    "qiymətlər çıxarıldıqdan sonra {count} müqayisə edilən elan istifadə olunub. "
                    "Bu, elan qiymətlərinin təxminidir, təsdiqlənmiş satış qiyməti deyil."
                ),
                "en": (
                    "The report snapshot shows a {median} {currency} median; the selected car is "
                    "{selected} {currency}, a {deviation}% deviation. The estimate uses {count} "
                    "comparable asking prices after outlier removal; it is not a confirmed "
                    "transaction price."
                ),
            }
            return templates[language].format(**values)

        if self._contains(
            normalized,
            ("гор", "шамах", "mountain", "şamax", "dağ", "район", "region"),
        ):
            vehicle = bundle.vehicle
            values = {
                "rating": bundle.fit_analysis.rating.value,
                "score": bundle.fit_analysis.score,
                "drivetrain": vehicle.drivetrain or "—",
                "clearance": vehicle.ground_clearance_mm or "—",
            }
            templates = {
                "ru": (
                    "Для указанных условий итог отчёта — {rating} ({score}/100). В snapshot "
                    "зафиксированы привод {drivetrain} и клиренс {clearance} мм. Конкретную машину "
                    "перед регулярными горными поездками всё равно нужно физически проверить."
                ),
                "az": (
                    "Göstərilən şərait üçün hesabat nəticəsi {rating} ({score}/100)-dır. "
                    "Snapshot-da ötürücü {drivetrain}, klirens {clearance} mm göstərilib. "
                    "Daimi dağ səfərlərindən "
                    "əvvəl konkret avtomobil yenə də fiziki yoxlanmalıdır."
                ),
                "en": (
                    "For the stated conditions the report result is {rating} ({score}/100). The "
                    "snapshot records {drivetrain} drivetrain and {clearance} mm clearance. The "
                    "specific car still requires physical inspection before regular mountain use."
                ),
            }
            return templates[language].format(**values)

        if self._contains(
            normalized,
            ("расход", "топлив", "fuel", "consumption", "yanacaq", "sərfiyyat", "xərc"),
        ):
            yearly = bundle.ownership_calculation.yearly_fuel
            if yearly is None:
                return _COPY[language]["insufficient"]
            return _COPY[language]["fuel"].format(
                low=yearly.low,
                high=yearly.high,
                currency=yearly.currency,
            )

        if self._contains(
            normalized,
            ("пробег", "провер", "inspection", "mileage", "yürüş", "yoxla"),
        ):
            recommendations = [issue.inspection_recommendation for issue in bundle.known_issues]
            if not recommendations:
                return _COPY[language]["inspection"]
            prefix = {
                "ru": "По данным snapshot перед покупкой: ",
                "az": "Snapshot məlumatına görə alışdan əvvəl: ",
                "en": "Based on the snapshot, before purchase: ",
            }[language]
            return prefix + " ".join(recommendations) + " " + _COPY[language]["inspection"]

        summary = {
            "ru": (
                "По сохранённому отчёту итог — {rating} ({score}/100). "
                "Я могу отвечать только по фактам этого snapshot. {inspection}"
            ),
            "az": (
                "Saxlanmış hesabatın nəticəsi {rating} ({score}/100)-dır. Mən yalnız bu "
                "snapshot-dakı faktlara əsasən cavab verə bilərəm. {inspection}"
            ),
            "en": (
                "The saved report result is {rating} ({score}/100). I can answer only from facts "
                "in this snapshot. {inspection}"
            ),
        }[language]
        return summary.format(
            rating=bundle.fit_analysis.rating.value,
            score=bundle.fit_analysis.score,
            inspection=_COPY[language]["inspection"],
        )

    @staticmethod
    def _contains(value: str, keywords: tuple[str, ...]) -> bool:
        return any(keyword in value for keyword in keywords)
