# ruff: noqa: E501

from __future__ import annotations

import re
from collections.abc import Iterable

from app.models.evidence import TechnicalEvidence
from app.schemas.vin import DossierClaim

_COPY = {
    "ru": {
        "identity_heading": "Автомобиль по VIN",
        "identity_why": "VIN-декодирование уточняет заводскую конфигурацию, но не подтверждает состояние автомобиля.",
        "identity_check": "Сверьте VIN на кузове, табличках и в документах.",
        "verdict": "Автомобиль определён по официальным данным. Неподтверждённые поля оставлены без догадок; состояние экземпляра требует осмотра.",
        "usa_scope": "Для автомобиля проверены доступные официальные базы США. Выполнение кампаний и состояние конкретного экземпляра подтверждаются отдельно по VIN.",
        "engine_heading": "Подтверждённая конфигурация двигателя",
        "engine_why": "Это идентифицирует версию силового агрегата, но не говорит о его текущем состоянии.",
        "engine_check": "Сверьте маркировку и комплектацию с документами и результатом диагностики.",
        "transmission_heading": "Подтверждённая коробка передач",
        "transmission_why": "Тип коробки определяет применимые процедуры проверки и обслуживания.",
        "transmission_check": "Проверьте работу на холодную и после прогрева, ошибки и историю обслуживания.",
        "body_heading": "Тип кузова по VIN",
        "body_why": "Декодер подтверждает заводской тип автомобиля, но не историю кузовного ремонта.",
        "body_check": "Осмотрите силовые элементы, геометрию и качество предыдущего ремонта.",
        "recall_heading": "Отзывная кампания NHTSA {campaign}",
        "recall_generic": "Официальная кампания относится к системе «{component}» и описывает дефект, требующий проверки применимости по VIN.",
        "recall_stop": "В системе «{component}» компонент может перестать работать.",
        "recall_leak": "В системе «{component}» возможна утечка.",
        "recall_break": "Компонент системы «{component}» может разрушиться или сломаться.",
        "recall_detach": "Компонент системы «{component}» может отсоединиться.",
        "recall_short": "В системе «{component}» возможно короткое замыкание.",
        "recall_software": "Ошибка программного обеспечения может нарушить работу системы «{component}».",
        "risk_fire": "В официальной записи указана опасность возгорания.",
        "risk_stall": "Возможна остановка двигателя, что повышает риск ДТП.",
        "risk_crash": "Неисправность может повысить риск ДТП.",
        "risk_injury": "Неисправность может повысить риск травм.",
        "risk_generic": "Официальная запись указывает на потенциальный риск безопасности; исходное описание доступно у источника.",
        "recall_action": "Проверьте применимость кампании именно к этому VIN и запросите подтверждение выполненного бесплатного ремонта.",
        "recall_applicability": "Кампания найдена для {year} {make} {model}; совпадение модели и года ещё не доказывает применимость к конкретному VIN.",
        "recall_none": "На дату запроса модельный поиск NHTSA не вернул кампаний. Это не доказывает отсутствие открытых кампаний у конкретного VIN.",
        "comm_heading": "TSB — технический бюллетень производителя {document}",
        "comm_text": "Документ производителя относится к системе «{component}» и описывает сервисную ситуацию: {summary}",
        "comm_why": "Бюллетень помогает диагностике и ремонту, но не является отзывной кампанией и не доказывает дефект этого автомобиля.",
        "comm_action": "Уточните у профильного сервиса применимость документа по VIN и наличие описанных симптомов.",
        "generic_localized": "Подтверждённая запись сохранена в источниках. Детали пока не переведены для пользовательского отчёта.",
    },
    "az": {
        "identity_heading": "VIN üzrə avtomobil",
        "identity_why": "VIN dekodlaşdırılması zavod konfiqurasiyasını dəqiqləşdirir, lakin avtomobilin vəziyyətini təsdiqləmir.",
        "identity_check": "Kuzovdakı, lövhələrdəki və sənədlərdəki VIN-i tutuşdurun.",
        "verdict": "Avtomobil rəsmi məlumatlarla müəyyən edilib. Təsdiqlənməyən sahələr ehtimalla doldurulmayıb; konkret avtomobil baxış tələb edir.",
        "usa_scope": "Avtomobil üçün ABŞ-ın mövcud rəsmi bazaları yoxlanılıb. Kampaniyaların icrası və konkret avtomobilin vəziyyəti VIN üzrə ayrıca təsdiqlənir.",
        "engine_heading": "Təsdiqlənmiş mühərrik konfiqurasiyası",
        "engine_why": "Bu, güc aqreqatının versiyasını müəyyən edir, lakin hazırkı vəziyyətini göstərmir.",
        "engine_check": "Markalanmanı və komplektasiyanı sənədlər və diaqnostika nəticəsi ilə tutuşdurun.",
        "transmission_heading": "Təsdiqlənmiş sürətlər qutusu",
        "transmission_why": "Qutunun növü tətbiq olunan yoxlama və qulluq prosedurlarını müəyyən edir.",
        "transmission_check": "Soyuq və isti halda işləməni, xətaları və qulluq tarixçəsini yoxlayın.",
        "body_heading": "VIN üzrə kuzov növü",
        "body_why": "Dekoder zavod kuzov növünü təsdiqləyir, lakin kuzov təmiri tarixçəsini göstərmir.",
        "body_check": "Daşıyıcı elementləri, geometriyanı və əvvəlki təmirin keyfiyyətini yoxlayın.",
        "recall_heading": "NHTSA geri çağırma kampaniyası {campaign}",
        "recall_generic": "Rəsmi kampaniya «{component}» sisteminə aiddir və VIN üzrə tətbiqi yoxlanmalı olan qüsuru təsvir edir.",
        "recall_stop": "«{component}» sistemində komponent işləməyi dayandıra bilər.",
        "recall_leak": "«{component}» sistemində sızma mümkündür.",
        "recall_break": "«{component}» sisteminin komponenti qırıla və ya dağıla bilər.",
        "recall_detach": "«{component}» sisteminin komponenti ayrıla bilər.",
        "recall_short": "«{component}» sistemində qısaqapanma mümkündür.",
        "recall_software": "Proqram təminatı xətası «{component}» sisteminin işini poza bilər.",
        "risk_fire": "Rəsmi qeyddə yanğın riski göstərilir.",
        "risk_stall": "Mühərrik dayana bilər və bu, qəza riskini artırır.",
        "risk_crash": "Nasazlıq qəza riskini artıra bilər.",
        "risk_injury": "Nasazlıq xəsarət riskini artıra bilər.",
        "risk_generic": "Rəsmi qeyd potensial təhlükəsizlik riskini göstərir; ilkin təsvir mənbədə mövcuddur.",
        "recall_action": "Kampaniyanın məhz bu VIN-ə aid olduğunu yoxlayın və pulsuz təmirin icrasını təsdiqləyən sənəd istəyin.",
        "recall_applicability": "Kampaniya {year} {make} {model} üçün tapılıb; model və ilin uyğunluğu konkret VIN-ə tətbiqi hələ təsdiqləmir.",
        "recall_none": "Sorğu tarixində NHTSA model axtarışı kampaniya qaytarmayıb. Bu, konkret VIN üçün açıq kampaniyanın olmadığını sübut etmir.",
        "comm_heading": "TSB — istehsalçının texniki bülleteni {document}",
        "comm_text": "İstehsalçı sənədi «{component}» sisteminə aiddir və servis halını təsvir edir: {summary}",
        "comm_why": "Bülleten diaqnostika və təmirə kömək edir, lakin geri çağırma deyil və bu avtomobildə qüsuru sübut etmir.",
        "comm_action": "Sənədin VIN üzrə tətbiqini və göstərilən əlamətləri ixtisaslaşmış servisdə dəqiqləşdirin.",
        "generic_localized": "Təsdiqlənmiş qeyd mənbələrdə saxlanılıb. Detallar istifadəçi hesabatı üçün hələ tərcümə edilməyib.",
    },
    "en": {
        "identity_heading": "Vehicle identified by VIN",
        "identity_why": "VIN decoding refines the factory configuration; it does not confirm the vehicle's condition.",
        "identity_check": "Match the VIN on the body and labels to the vehicle documents.",
        "verdict": "Official data identifies the vehicle. Unsupported fields remain unresolved, and the specific vehicle still requires inspection.",
        "usa_scope": "Available official US databases were checked. Campaign completion and the condition of the specific vehicle require separate VIN verification.",
        "engine_heading": "Confirmed engine configuration",
        "engine_why": "This identifies the powertrain version but does not establish its current condition.",
        "engine_check": "Match the markings and configuration to the documents and diagnostic results.",
        "transmission_heading": "Confirmed transmission",
        "transmission_why": "The transmission type determines the relevant inspection and maintenance procedures.",
        "transmission_check": "Check operation cold and fully warm, stored faults, and maintenance history.",
        "body_heading": "VIN-decoded body type",
        "body_why": "The decoder confirms the factory body type, not the history of body repairs.",
        "body_check": "Inspect structural members, geometry, and the quality of previous repairs.",
        "recall_heading": "NHTSA recall campaign {campaign}",
        "recall_generic": "The official campaign concerns the {component} system and describes a defect whose VIN applicability must be checked.",
        "recall_stop": "A component in the {component} system may stop operating.",
        "recall_leak": "A leak may occur in the {component} system.",
        "recall_break": "A component in the {component} system may fracture or break.",
        "recall_detach": "A component in the {component} system may detach.",
        "recall_short": "A short circuit may occur in the {component} system.",
        "recall_software": "A software error may disrupt the {component} system.",
        "risk_fire": "The official record identifies a fire risk.",
        "risk_stall": "The engine may stall, increasing crash risk.",
        "risk_crash": "The defect may increase crash risk.",
        "risk_injury": "The defect may increase injury risk.",
        "risk_generic": "The official record identifies a potential safety risk; the original description remains available from the source.",
        "recall_action": "Check whether the campaign applies to this VIN and request proof that the free remedy was completed.",
        "recall_applicability": "The campaign was found for the {year} {make} {model}; a model-year match alone does not establish applicability to this VIN.",
        "recall_none": "At retrieval time, the NHTSA model search returned no campaigns. This does not prove that a specific VIN has no open campaign.",
        "comm_heading": "TSB — manufacturer technical service bulletin {document}",
        "comm_text": "The manufacturer document concerns the {component} system and describes this service condition: {summary}",
        "comm_why": "A bulletin supports diagnosis and repair; it is not a recall and does not prove a defect in this vehicle.",
        "comm_action": "Ask a qualified service center to check VIN applicability and the described symptoms.",
        "generic_localized": "A confirmed record is retained in the sources. Its details are not yet adapted for the consumer report.",
    },
}


_COMPONENTS = {
    "airbag": ("Подушки безопасности", "Təhlükəsizlik yastıqları", "Air bags"),
    "fuel": ("Топливная система", "Yanacaq sistemi", "Fuel system"),
    "powertrain": ("Силовой агрегат", "Güc aqreqatı", "Powertrain"),
    "electrical": ("Электрика", "Elektrik sistemi", "Electrical system"),
    "brakes": ("Тормозная система", "Əyləc sistemi", "Brake system"),
    "steering": ("Рулевое управление", "Sükan sistemi", "Steering"),
    "engine": ("Двигатель", "Mühərrik", "Engine"),
    "seatbelts": ("Ремни безопасности", "Təhlükəsizlik kəmərləri", "Seat belts"),
    "structure": ("Кузов и силовая структура", "Kuzov və daşıyıcı struktur", "Body structure"),
    "visibility": ("Обзорность", "Görünüş", "Visibility"),
    "tires": ("Шины", "Şinlər", "Tires"),
    "suspension": ("Подвеска", "Asqı", "Suspension"),
    "lights": ("Наружное освещение", "Xarici işıqlandırma", "Exterior lighting"),
    "speed_control": ("Управление скоростью", "Sürətin idarə edilməsi", "Speed control"),
    "other": ("Другой узел", "Digər sistem", "Other component"),
}


def synthesize_evidence_claims(
    items: Iterable[TechnicalEvidence], language: str
) -> list[DossierClaim]:
    language = language if language in _COPY else "ru"
    claims: list[DossierClaim] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        claim = _claim(item, language)
        if claim is None:
            continue
        dedupe_key = (claim.kind, (claim.heading or claim.text).casefold())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        claims.append(claim)
    return claims


def localized_component(value: object, language: str) -> str:
    normalized = str(value or "").upper()
    if "AIR BAG" in normalized:
        key = "airbag"
    elif "FUEL" in normalized:
        key = "fuel"
    elif "POWER TRAIN" in normalized or "POWERTRAIN" in normalized or "TRANSMISSION" in normalized:
        key = "powertrain"
    elif "ELECTR" in normalized:
        key = "electrical"
    elif "BRAKE" in normalized:
        key = "brakes"
    elif "STEER" in normalized:
        key = "steering"
    elif "ENGINE" in normalized:
        key = "engine"
    elif "SEAT BELT" in normalized:
        key = "seatbelts"
    elif "STRUCTURE" in normalized or "BODY" in normalized:
        key = "structure"
    elif any(
        term in normalized for term in ("VISIBILITY", "WINDOW", "WINDSHIELD", "BACK OVER", "CAMERA")
    ):
        key = "visibility"
    elif "SPEED CONTROL" in normalized:
        key = "speed_control"
    elif "TIRE" in normalized or "WHEEL" in normalized:
        key = "tires"
    elif "SUSPENSION" in normalized:
        key = "suspension"
    elif "LIGHT" in normalized:
        key = "lights"
    else:
        key = "other"
    return _COMPONENTS[key][{"ru": 0, "az": 1, "en": 2}.get(language, 0)]


def is_low_information_communication(item: TechnicalEvidence) -> bool:
    if item.source.source_type != "MANUFACTURER_COMMUNICATION":
        return False
    conditions = item.conditions or {}
    component = str(conditions.get("component") or "").strip()
    summary = str(conditions.get("summary") or "").strip()
    quality = str(conditions.get("information_quality") or "").upper()
    return quality == "LOW" or not component or len(summary) < 20


def _claim(item: TechnicalEvidence, language: str) -> DossierClaim | None:
    conditions = item.conditions or {}
    if conditions.get("excluded_from_synthesis"):
        return None
    if conditions.get("consumer_kind") == "issue_signal":
        return None
    if conditions.get("consumer_kind") == "knowledge_fact":
        from app.services.paid_report import fact_display

        display = fact_display({**conditions, "status": item.status.value}, language)
        if not display:
            return None
        return _grounded(item, heading=display[0], text=display[1], kind="knowledge_fact")
    if conditions.get("campaign_number"):
        return _recall_claim(item, language)
    if item.source.source_type == "MANUFACTURER_COMMUNICATION":
        return _communication_claim(item, language)
    kind = str(conditions.get("consumer_kind") or "fact")
    if kind in {
        "vehicle_identity",
        "research_verdict",
        "usa_scope",
        "engine_identity",
        "transmission_identity",
        "body_identity",
    }:
        return _identity_claim(item, language, kind)
    if conditions.get("query_returned_zero") and item.source.source_type == "GOVERNMENT_RECALL_API":
        return DossierClaim(
            heading=_COPY[language]["recall_heading"].format(campaign="—"),
            text=_COPY[language]["recall_none"],
            status=item.status,
            kind="recall_query",
            source_ids=[item.source_id],
            evidence_ids=[item.id],
            original_available=True,
        )
    translations = conditions.get("translations") or {}
    if language == "en":
        text = str(translations.get("en") or item.statement)
    else:
        text = str(translations.get(language) or _COPY[language]["generic_localized"])
    return DossierClaim(
        text=text,
        status=item.status,
        kind="fact",
        source_ids=[item.source_id],
        evidence_ids=[item.id],
        original_available=True,
    )


def _identity_claim(item: TechnicalEvidence, language: str, kind: str) -> DossierClaim:
    values = item.conditions.get("consumer_values") or {}
    copy = _COPY[language]
    if kind == "research_verdict":
        return _grounded(item, text=copy["verdict"], kind=kind)
    if kind == "usa_scope":
        return _grounded(item, text=copy["usa_scope"], kind=kind)
    if kind == "vehicle_identity":
        identity = " ".join(
            str(value)
            for value in (
                values.get("year"),
                values.get("make"),
                values.get("model"),
                values.get("trim") or values.get("series"),
            )
            if value not in {None, ""}
        )
        details = _join_values(
            language,
            (
                (
                    "Привод",
                    "Ötürücü",
                    "Drivetrain",
                    _translate_drivetrain(values.get("drivetrain"), language),
                ),
                (
                    "Кузов",
                    "Kuzov",
                    "Body",
                    _translate_body(values.get("body"), language),
                ),
            ),
        )
        return _grounded(
            item,
            heading=copy["identity_heading"],
            text=" · ".join(value for value in (identity, details) if value),
            why=copy["identity_why"],
            action=copy["identity_check"],
            kind=kind,
        )
    if kind == "engine_identity":
        text = _engine_text(values, language)
        return _grounded(
            item,
            heading=copy["engine_heading"],
            text=text,
            why=copy["engine_why"],
            action=copy["engine_check"],
            kind=kind,
        )
    if kind == "transmission_identity":
        return _grounded(
            item,
            heading=copy["transmission_heading"],
            text=_translate_transmission(values.get("transmission"), language),
            why=copy["transmission_why"],
            action=copy["transmission_check"],
            kind=kind,
        )
    return _grounded(
        item,
        heading=copy["body_heading"],
        text=_translate_body(values.get("body"), language),
        why=copy["body_why"],
        action=copy["body_check"],
        kind=kind,
    )


def _recall_claim(item: TechnicalEvidence, language: str) -> DossierClaim:
    conditions = item.conditions or {}
    campaign = str(conditions.get("campaign_number") or "—")
    component = localized_component(conditions.get("component"), language)
    summary = str(conditions.get("summary") or item.statement)
    consequence = str(conditions.get("consequence") or "")
    make = str(conditions.get("make") or "")
    model = str(conditions.get("model") or "")
    year = str(conditions.get("model_year") or "—")
    copy = _COPY[language]
    issue_key = _issue_key(summary)
    text = copy[issue_key].format(component=component)
    risk = copy[_risk_key(f"{summary} {consequence}")]
    return _grounded(
        item,
        heading=copy["recall_heading"].format(campaign=campaign),
        text=text,
        why=risk,
        action=copy["recall_action"],
        applicability=copy["recall_applicability"].format(
            year=year,
            make=make.title(),
            model=model.title(),
        ),
        kind="recall",
    )


def _communication_claim(item: TechnicalEvidence, language: str) -> DossierClaim | None:
    if is_low_information_communication(item):
        return None
    conditions = item.conditions or {}
    copy = _COPY[language]
    component = localized_component(conditions.get("component"), language)
    summary = _communication_summary(str(conditions.get("summary") or ""), language)
    document = str(conditions.get("document_id") or "—")
    return _grounded(
        item,
        heading=copy["comm_heading"].format(document=document),
        text=copy["comm_text"].format(component=component, summary=summary),
        why=copy["comm_why"],
        action=copy["comm_action"],
        kind="manufacturer_communication",
    )


def _grounded(
    item: TechnicalEvidence,
    *,
    text: str,
    kind: str,
    heading: str | None = None,
    why: str | None = None,
    action: str | None = None,
    applicability: str | None = None,
) -> DossierClaim:
    return DossierClaim(
        heading=heading,
        text=text,
        why_it_matters=why,
        what_to_check=action,
        applicability=applicability,
        kind=kind,
        status=item.status,
        source_ids=[item.source_id],
        evidence_ids=[item.id],
        original_available=True,
    )


def _issue_key(text: str) -> str:
    normalized = text.casefold()
    if "software" in normalized or "program" in normalized:
        return "recall_software"
    if "short circuit" in normalized:
        return "recall_short"
    if "leak" in normalized:
        return "recall_leak"
    if any(word in normalized for word in ("fracture", "break", "broken")):
        return "recall_break"
    if any(word in normalized for word in ("detach", "separate")):
        return "recall_detach"
    if any(phrase in normalized for phrase in ("stop operating", "may fail", "inoperative")):
        return "recall_stop"
    return "recall_generic"


def _risk_key(text: str) -> str:
    normalized = text.casefold()
    if "fire" in normalized:
        return "risk_fire"
    if re.search(r"\bstall(?:s|ed|ing)?\b", normalized):
        return "risk_stall"
    if "crash" in normalized or "collision" in normalized:
        return "risk_crash"
    if "injur" in normalized:
        return "risk_injury"
    return "risk_generic"


def _communication_summary(value: str, language: str) -> str:
    normalized = value.casefold()
    labels = {
        "ru": {
            "hesitation": "задержка реакции или рывки при движении",
            "vibration": "вибрация",
            "noise": "посторонний шум",
            "leak": "возможная утечка",
            "software": "обновление или ошибка программного обеспечения",
            "generic": "диагностика и сервисная процедура описаны в исходном документе",
        },
        "az": {
            "hesitation": "hərəkət zamanı gecikmə və ya təkan",
            "vibration": "vibrasiya",
            "noise": "kənar səs",
            "leak": "mümkün sızma",
            "software": "proqram yeniləməsi və ya xətası",
            "generic": "diaqnostika və servis proseduru ilkin sənəddə təsvir olunub",
        },
        "en": {
            "hesitation": "hesitation or harsh response while driving",
            "vibration": "vibration",
            "noise": "abnormal noise",
            "leak": "a possible leak",
            "software": "a software update or software fault",
            "generic": "the diagnostic and service procedure is described in the original document",
        },
    }[language]
    for key, words in (
        ("hesitation", ("hesitat", "harsh shift", "delay")),
        ("vibration", ("vibrat",)),
        ("noise", ("noise", "rattle", "squeak")),
        ("leak", ("leak",)),
        ("software", ("software", "reprogram", "update")),
    ):
        if any(word in normalized for word in words):
            return labels[key]
    return labels["generic"]


def _engine_text(values: dict, language: str) -> str:
    pieces: list[str] = []
    displacement = values.get("displacement_l")
    if displacement:
        pieces.append(
            {
                "ru": f"объём {displacement} л",
                "az": f"həcm {displacement} l",
                "en": f"{displacement} L displacement",
            }[language]
        )
    cylinders = values.get("cylinders")
    if cylinders:
        pieces.append(
            {
                "ru": f"{cylinders} цилиндра",
                "az": f"{cylinders} silindr",
                "en": f"{cylinders} cylinders",
            }[language]
        )
    fuel = values.get("fuel")
    if fuel:
        pieces.append(_translate_fuel(fuel, language))
    code = values.get("engine_model")
    if code:
        pieces.append(
            {"ru": f"код/модель {code}", "az": f"kod/model {code}", "en": f"model/code {code}"}[
                language
            ]
        )
    power = values.get("engine_power_hp")
    if power:
        pieces.append(
            {
                "ru": f"Мощность бензинового двигателя: {power} hp (SAE)",
                "az": f"Benzin mühərrikinin gücü: {power} hp (SAE)",
                "en": f"Combustion engine power: {power} SAE hp",
            }[language]
        )
    if values.get("powertrain_type") not in {None, "UNKNOWN"}:
        from app.services.paid_report import VALUES, tr

        pieces.append(tr(language, *VALUES[values["powertrain_type"]]))
    return " · ".join(pieces)


def _translate_fuel(value: object, language: str) -> str:
    normalized = str(value or "").casefold()
    if "gas" in normalized or "petrol" in normalized:
        return {"ru": "бензин", "az": "benzin", "en": "gasoline"}[language]
    if "diesel" in normalized:
        return {"ru": "дизель", "az": "dizel", "en": "diesel"}[language]
    if "electric" in normalized:
        return {"ru": "электрический", "az": "elektrik", "en": "electric"}[language]
    return str(value)


def _translate_transmission(value: object, language: str) -> str:
    text = str(value or "")
    normalized = text.casefold()
    speeds = "".join(character for character in text if character.isdigit())
    if "automatic" in normalized:
        return {
            "ru": f"{speeds + '-ступенчатая ' if speeds else ''}автоматическая коробка передач",
            "az": f"{speeds + ' pilləli ' if speeds else ''}avtomatik sürətlər qutusu",
            "en": f"{speeds + '-speed ' if speeds else ''}automatic transmission",
        }[language]
    if "manual" in normalized:
        return {
            "ru": f"{speeds + '-ступенчатая ' if speeds else ''}механическая коробка передач",
            "az": f"{speeds + ' pilləli ' if speeds else ''}mexaniki sürətlər qutusu",
            "en": f"{speeds + '-speed ' if speeds else ''}manual transmission",
        }[language]
    return text


def _translate_body(value: object, language: str) -> str:
    text = str(value or "")
    normalized = text.casefold()
    for token, labels in (
        ("sedan", ("Седан", "Sedan", "Sedan")),
        ("hatchback", ("Хэтчбек", "Hetçbek", "Hatchback")),
        ("sport utility", ("Кроссовер / SUV", "Krossover / SUV", "SUV")),
        ("wagon", ("Универсал", "Universal", "Wagon")),
        ("coupe", ("Купе", "Kupe", "Coupe")),
    ):
        if token in normalized:
            return labels[{"ru": 0, "az": 1, "en": 2}[language]]
    return text


def _translate_drivetrain(value: object, language: str) -> str:
    text = str(value or "")
    normalized = text.casefold()
    if "fwd" in normalized or "front-wheel" in normalized:
        return {
            "ru": "передний привод",
            "az": "ön ötürücü",
            "en": "front-wheel drive",
        }[language]
    if "awd" in normalized or "all-wheel" in normalized:
        return {
            "ru": "полный привод",
            "az": "tam ötürücü",
            "en": "all-wheel drive",
        }[language]
    if "rwd" in normalized or "rear-wheel" in normalized:
        return {
            "ru": "задний привод",
            "az": "arxa ötürücü",
            "en": "rear-wheel drive",
        }[language]
    return text


def _join_values(language: str, values: Iterable[tuple[str, str, str, object]]) -> str:
    index = {"ru": 0, "az": 1, "en": 2}[language]
    return " · ".join(
        f"{labels[index]}: {value}" for *labels, value in values if value not in {None, ""}
    )
