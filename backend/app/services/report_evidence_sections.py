# ruff: noqa: E501
"""Localized factual presentation of history and owner samples (no damage inference)."""

from app.schemas.paid_report import PaidReportSection, ReportEvent, ReportParagraph, ReportRow


def tr(language, ru, az, en):
    return (ru, az, en)[{"ru": 0, "az": 1, "en": 2}[language]]


TOPIC_LABELS = {
    "ENGINE": ("Двигатель", "Mühərrik", "Engine"),
    "TRANSMISSION": ("Коробка", "Sürətlər qutusu", "Transmission"),
    "COOLING": ("Охлаждение", "Soyutma", "Cooling"),
    "ELECTRICAL": ("Электрика", "Elektrik", "Electrical"),
    "SUSPENSION": ("Подвеска", "Asqı", "Suspension"),
    "STEERING": ("Рулевое", "Sükan", "Steering"),
    "BRAKES": ("Тормоза", "Əyləclər", "Brakes"),
    "BODY": ("Кузов", "Kuzov", "Body"),
    "INTERIOR": ("Салон", "Salon", "Interior"),
    "INFOTAINMENT": ("Мультимедиа", "Multimedia", "Infotainment"),
    "FUEL_ECONOMY": ("Расход топлива", "Yanacaq sərfiyyatı", "Fuel economy"),
    "MAINTENANCE": ("Обслуживание", "Qulluq", "Maintenance"),
    "RELIABILITY_GENERAL": ("Надёжность в целом", "Ümumi etibarlılıq", "General reliability"),
}
ISSUE_LABELS = {
    "coolant_intrusion": (
        "Попадание антифриза в цилиндры",
        "Antifrizin silindrlərə keçməsi",
        "Coolant intrusion into cylinders",
    ),
    "transmission_failure": (
        "Отказ коробки передач",
        "Sürətlər qutusunun sıradan çıxması",
        "Transmission failure",
    ),
    "oil_consumption": ("Повышенный расход масла", "Yüksək yağ sərfiyyatı", "High oil consumption"),
}


def history_status_text(payload, language):
    research = payload.get("history_research", {})
    state = research.get("state")
    if state == "NO_RECORDS":
        main = tr(
            language,
            "В подключённых источниках история этого VIN не найдена.",
            "Qoşulmuş mənbələrdə bu VIN-in tarixçəsi tapılmayıb.",
            "No history for this VIN was found in the connected sources.",
        )
    elif payload.get("events"):
        main = tr(
            language,
            f"Найдено событий по этому VIN: {len(payload['events'])}.",
            f"Bu VIN üzrə tapılan hadisələr: {len(payload['events'])}.",
            f"Events found for this VIN: {len(payload['events'])}.",
        )
    elif research.get("successful_provider_count", 0):
        main = tr(
            language,
            "В проверенной части источников записи не найдены; часть источников недоступна. Поиск истории неполный.",
            "Yoxlanılan mənbələrdə qeyd tapılmayıb; bəzi mənbələr əlçatmazdır. Tarixçə axtarışı natamamdır.",
            "No records were found in the sources that responded; other sources were unavailable. History coverage is incomplete.",
        )
    elif research:
        main = tr(
            language,
            "Источники истории VIN сейчас недоступны. Наличие аукционов, ДТП и записей пробега не проверено.",
            "VIN tarixçəsi mənbələri hazırda əlçatmazdır. Hərrac, qəza və yürüş qeydləri yoxlanılmayıb.",
            "VIN history sources are currently unavailable. Auction, accident and mileage records have not been checked.",
        )
    else:
        main = tr(
            language,
            "История этого VIN ещё не проверена в источниках аукционов и продаж.",
            "Bu VIN-in tarixçəsi hərrac və satış mənbələrində hələ yoxlanılmayıb.",
            "This VIN has not yet been checked against auction and sale history sources.",
        )
    caution = tr(
        language,
        "Отсутствие записей не означает отсутствие ДТП или ремонта.",
        "Qeydlərin olmaması qəza və ya təmirin olmaması demək deyil.",
        "An absence of records does not mean an absence of accidents or repairs.",
    )
    return main, caution


def history_section(payload, language):
    section = PaidReportSection(
        key="history",
        title=tr(
            language,
            "История автомобиля в США",
            "Avtomobilin ABŞ tarixçəsi",
            "Vehicle history in the USA",
        ),
    )
    main, caution = history_status_text(payload, language)
    section.paragraphs = [ReportParagraph(text=main), ReportParagraph(text=caution)]
    types = {
        "AUCTION": ("Аукцион", "Hərrac", "Auction"),
        "SALE": ("Продажа", "Satış", "Sale"),
        "TITLE": ("Статус документов", "Sənəd statusu", "Title record"),
        "ODOMETER": ("Запись пробега", "Yürüş qeydi", "Odometer record"),
        "DAMAGE": ("Запись повреждения", "Zədə qeydi", "Damage record"),
        "OTHER": ("Событие", "Hadisə", "Event"),
    }
    fields = {
        "auction": ("Аукцион / компания", "Hərrac / şirkət", "Auction / company"),
        "lot_id": ("Номер лота", "Lot nömrəsi", "Lot ID"),
        "location": ("Место", "Yer", "Location"),
        "odometer": ("Пробег по источнику", "Mənbədəki yürüş", "Source-reported odometer"),
        "odometer_status": ("Статус пробега", "Yürüş statusu", "Odometer status"),
        "title": ("Документ / статус", "Sənəd / status", "Title / status"),
        "primary_damage": (
            "Основное повреждение по источнику",
            "Mənbədəki əsas zədə",
            "Source-reported primary damage",
        ),
        "secondary_damage": ("Дополнительное повреждение", "Əlavə zədə", "Secondary damage"),
        "loss_type": (
            "Тип убытка по источнику",
            "Mənbədəki itki növü",
            "Source-reported loss type",
        ),
        "sale_price": ("Цена продажи", "Satış qiyməti", "Sale price"),
        "seller_type": ("Тип продавца", "Satıcı növü", "Seller type"),
    }
    for event in payload.get("events", []):
        rows = []
        for key, labels in fields.items():
            value = event.get(key)
            if value is None or key in event.get("conflicts", {}):
                continue
            if key == "odometer":
                value = f"{value} {event.get('odometer_unit', '')}"
            if key == "sale_price":
                value = f"{value} {event.get('currency', '')}"
            rows.append(
                ReportRow(
                    key=f"{event['id']}.{key}",
                    label=tr(language, *labels),
                    value=str(value),
                    source_ids=event["source_ids"],
                    evidence_ids=[event["id"]],
                )
            )
        if event.get("conflicts"):
            rows.append(
                ReportRow(
                    key=f"{event['id']}.conflict",
                    label=tr(language, "Расхождения", "Uyğunsuzluqlar", "Conflicting records"),
                    value=tr(
                        language,
                        "Источники расходятся в деталях; спорные значения не показаны.",
                        "Mənbələrin detalları fərqlənir; mübahisəli dəyərlər göstərilmir.",
                        "Sources disagree on details; disputed values are not displayed.",
                    ),
                    source_ids=event["source_ids"],
                    evidence_ids=[event["id"]],
                )
            )
        section.events.append(
            ReportEvent(
                id=event["id"],
                title=tr(language, *types[event["event_type"]])
                + (f" · {event['event_date']}" if event.get("event_date") else ""),
                rows=rows,
                source_ids=event["source_ids"],
            )
        )
    return section


def owner_section(data, language):
    section = PaidReportSection(
        key="owner_reviews",
        title=tr(language, "Отзывы владельцев", "Sahiblərin rəyləri", "Owner reviews"),
    )
    sample = data.get("sample", {})
    materials = sample.get("materials", [])
    eids = [eid for m in materials for eid in m["evidence_ids"]]
    sids = sorted({sid for m in materials for sid in m["source_ids"]})
    count = sample.get("unique_materials", 0)

    def add(text):
        section.paragraphs.append(ReportParagraph(text=text, source_ids=sids, evidence_ids=eids))

    add(
        tr(
            language,
            f"Уникальных материалов по известной конфигурации: {count}.",
            f"Məlum komplektasiyaya uyğun {count} unikal material araşdırılıb.",
            f"Unique materials reviewed for the known configuration: {count}.",
        )
    )
    quality = sample.get("sample_quality", "VERY_SMALL")
    quality_text = {
        "VERY_SMALL": (
            "Выборка очень мала. Вывод о надёжности по ней не делается.",
            "Nümunə çox kiçikdir. Etibarlılıq barədə nəticə çıxarılmır.",
            "The sample is very small. No reliability conclusion can be drawn.",
        ),
        "SMALL": (
            "Выборка мала: это ограниченные наблюдения владельцев.",
            "Nümunə kiçikdir: bunlar sahiblərin məhdud müşahidələridir.",
            "The sample is small: these are limited owner observations.",
        ),
        "USEFUL": (
            "Выборка позволяет сравнить темы обсуждений, но не частоту поломок автомобилей.",
            "Nümunə mövzuları müqayisə etməyə imkan verir, avtomobil nasazlıqlarının tezliyini deyil.",
            "The sample supports topic comparisons, not vehicle failure rates.",
        ),
        "STRONG": (
            "Собран значительный массив материалов; он всё равно не является случайной выборкой автомобилей.",
            "Çoxlu material toplanıb; bu yenə də avtomobillərin təsadüfi nümunəsi deyil.",
            "A substantial material sample is available; it is still not a random vehicle sample.",
        ),
    }
    add(tr(language, *quality_text[quality]))
    if count:
        for topic, n in sorted(
            sample["topic_mentions"].items(), key=lambda pair: (-pair[1], pair[0])
        ):
            section.rows.append(
                ReportRow(
                    key="owner_topic." + topic,
                    label=tr(language, *TOPIC_LABELS[topic]),
                    value=tr(
                        language,
                        f"Материалов с упоминанием: {n} из {count}",
                        f"{count} materialdan {n}-də qeyd olunur",
                        f"Mentioned in {n} of {count} materials",
                    ),
                    source_ids=sids,
                    evidence_ids=eids,
                )
            )
        issues = {}
        for m in materials:
            if m.get("issue_key") in ISSUE_LABELS:
                issues[m["issue_key"]] = issues.get(m["issue_key"], 0) + 1
        for key, n in issues.items():
            add(
                tr(language, *ISSUE_LABELS[key])
                + tr(
                    language,
                    f": {n} из {count} материалов. Это сообщения владельцев, а не диагноз этого VIN.",
                    f": {count} materialdan {n}. Bunlar sahiblərin məlumatlarıdır, bu VIN-in diaqnozu deyil.",
                    f": {n} of {count} materials. These are owner accounts, not a diagnosis of this VIN.",
                )
            )
        if sample.get("positive_topics"):
            for topic, n in sorted(sample["positive_topics"].items()):
                add(
                    tr(
                        language,
                        "Положительные оценки — ",
                        "Müsbət rəylər — ",
                        "Positive observations — ",
                    )
                    + tr(language, *TOPIC_LABELS[topic])
                    + tr(
                        language,
                        f": {n} из {count}.",
                        f": {count} materialdan {n}.",
                        f": {n} of {count}.",
                    )
                )
        else:
            add(
                tr(
                    language,
                    "Положительные стороны в этой выборке не оценивались: изученные страницы посвящены проблемам.",
                    "Bu nümunədə müsbət cəhətlər qiymətləndirilməyib: araşdırılan səhifələr problemlərə həsr olunub.",
                    "Positive qualities were not assessed in this sample: the reviewed pages focus on problems.",
                )
            )
        add(
            tr(
                language,
                "Материалы сопоставлены по указанному двигателю и коробке; неизвестные характеристики не додумываются. Жалобы NHTSA и замеры My MPG в это число не входят. Доля неисправных автомобилей не рассчитывается.",
                "Materiallar göstərilən mühərrik və qutu üzrə uyğunlaşdırılıb; naməlum xüsusiyyətlər təxmin edilmir. NHTSA şikayətləri və My MPG ölçmələri bu saya daxil deyil. Nasaz avtomobillərin payı hesablanmır.",
                "Materials are matched using the stated engine and transmission; unknown attributes are not inferred. NHTSA complaints and My MPG measurements are excluded. No vehicle failure percentage is calculated.",
            )
        )
    else:
        add(
            tr(
                language,
                "Доступных отзывов с достаточными сведениями о модификации пока нет. Часть источников ограничивает доступ.",
                "Modifikasiya barədə kifayət qədər məlumatı olan əlçatan rəy hələ yoxdur. Bəzi mənbələr girişi məhdudlaşdırır.",
                "No accessible reviews with sufficient variant details are available yet. Some sources restrict access.",
            )
        )
    return section
