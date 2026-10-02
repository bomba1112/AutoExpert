# ruff: noqa: E501
"""Buyer projections on the existing Report/AnalysisRequest persistence and dossier engine."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from app.models.analysis import AnalysisRequest, Report
from app.models.enums import DataOrigin, EvidenceStatus, OdometerRisk, ReportStatus
from app.schemas.paid_report import PaidReportSection, PaidVehicleReport, ReportParagraph, ReportRow
from app.schemas.vin import DossierClaim, DossierSection, VINHistoryPayload
from app.services.chat_context import build_chat_context_snapshot
from app.services.paid_report import build_paid_report, tr
from app.services.report_evidence import ensure_report_evidence
from app.services.research_pipeline import ResearchPipeline

VERSION = "0.8.1"


def source_snapshot(source):
    return {
        "id": source.id,
        "title": source.title,
        "publisher": source.publisher,
        "url": source.url,
        "source_type": source.source_type,
        "source_tier": source.source_tier.value,
        "data_origin": source.data_origin.value,
        "market": source.market,
        "language": source.language,
        "retrieved_at": source.retrieved_at.isoformat(),
        "confidence": source.confidence.value,
        "usage_status": source.usage_status.value,
        "is_demo": source.is_demo,
    }


def context_for(job):
    vin = job.requested_vehicle.get("vin") or ""
    return SimpleNamespace(
        profile=job.profile,
        language=job.language,
        normalized_vin=vin,
        is_demo=False,
        data_origin=DataOrigin.REAL,
        found=False,
        records_count=0,
        photos_count=0,
        auctions_count=0,
        has_salvage_title=False,
        odometer_risk=OdometerRisk.UNKNOWN,
        full_history_payload=VINHistoryPayload(
            vin=vin,
            timeline=[],
            auctions=[],
            photos=[],
            damage_details=[],
            odometer_records=[],
            is_demo=False,
            data_origin=DataOrigin.REAL,
        ).model_dump(mode="json"),
        dossier_snapshot=job.dossier_snapshot,
        source_snapshot=[source_snapshot(s) for s in job.profile.sources],
    )


def persist_report(db, user_id, language, input_snapshot, projections, evidence, analysis=None):
    if analysis is None:
        analysis = AnalysisRequest(
            user_id=user_id,
            country="AZ",
            language=language,
            vehicle_input=input_snapshot,
            usage_profile=input_snapshot.get("preferences", {}),
        )
        db.add(analysis)
        db.flush()
    report = Report(
        user_id=user_id,
        analysis_request_id=analysis.id,
        language=language,
        status=ReportStatus.FULL,
        report_version=VERSION,
        is_unlocked=False,
        is_demo=False,
        input_snapshot=input_snapshot,
        evidence_bundle=evidence,
        calculated_data={},
        generated_sections={"buyer": projections[language], "translations": projections},
        methodology_version="buyer-v1",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def create_dossier(db, user_id, job, *, language, listing=None, preferences=None, parent_id=None):
    check = context_for(job)
    # Model dossiers do not submit an empty/fake VIN to history providers.
    ensure_report_evidence(check, history_providers=None if check.normalized_vin else [])
    if listing:
        check.source_snapshot.append(
            {
                "id": "listing:" + listing["id"],
                "title": "Listing · "
                + (listing.get("data", {}).get("title") or listing["source_url"]),
                "url": listing["source_url"],
                "source_type": "SELLER_LISTING",
                "retrieved_at": listing.get("retrieved_at") or datetime.now(UTC).isoformat(),
                "publisher": "Seller",
                "source_tier": "C",
                "confidence": "LOW",
                "data_origin": "REAL",
                "usage_status": "ACTIVE",
                "is_demo": False,
            }
        )
    projections, contexts = {}, {}
    for lang in ("ru", "az", "en"):
        check.language = lang
        check.dossier_snapshot = (
            ResearchPipeline(db, None)._dossier(check.profile, lang).model_dump(mode="json")
        )
        projection = build_paid_report(check)
        projection = buyer_projection(projection, check, listing, preferences or {})
        projections[lang] = projection.model_dump(mode="json")
        context = build_chat_context_snapshot(
            db, check, history_unlocked=bool(check.normalized_vin)
        )
        if listing:
            section = next(s for s in projection.sections if s.key == "offer")
            claims = [
                DossierClaim(
                    text=f"{r.label}: {r.value}",
                    status="ESTIMATE",
                    source_ids=r.source_ids,
                    evidence_ids=["listing:" + listing["id"] + "." + r.key],
                )
                for r in section.rows
            ]
            context.dossier_sections.append(
                DossierSection(
                    key="offer", title=section.title, summary="Seller claims", claims=claims
                )
            )
            context.evidence_statuses.update(
                {eid: EvidenceStatus.ESTIMATE for c in claims for eid in c.evidence_ids}
            )
        contexts[lang] = context.model_dump(mode="json")
    snapshot = {
        "kind": "LISTING" if listing else "VIN" if check.normalized_vin else "MODEL",
        "job_id": job.id,
        "profile_id": job.profile.id,
        "vin": check.normalized_vin or None,
        "vehicle": {"make": job.profile.make, "model": job.profile.model, "year": job.profile.year},
        "listing": listing,
        "preferences": preferences or {},
        "parent_report_id": parent_id,
    }
    return persist_report(
        db,
        user_id,
        language,
        snapshot,
        projections,
        {
            "sources": check.source_snapshot,
            "contexts": contexts,
            "history": check.full_history_payload,
        },
    )


def buyer_projection(report, check, listing, preferences):
    lang = report.language
    report.version = VERSION
    report.subtitle = tr(lang, "Разбор для покупателя", "Alıcı üçün təhlil", "Buyer's analysis")
    report.notice = tr(
        lang,
        "Покрытие источников неполное; существенные пробелы отмечены ниже.",
        "Mənbə əhatəsi tam deyil; mühüm boşluqlar aşağıda göstərilib.",
        "Source coverage is incomplete; material gaps are identified below.",
    )
    # History is a separate product. Its absence does not withhold a model analysis.
    report.readiness.checks.pop("vin_history_checked", None)
    report.readiness.missing_requirements = [k for k, v in report.readiness.checks.items() if not v]
    report.readiness.can_purchase = not report.readiness.missing_requirements
    report.readiness.state = (
        "READY" if report.readiness.can_purchase else "NOT_ENOUGH_DATA_FOR_PAID_REPORT"
    )
    sections = {s.key: s for s in report.sections}
    original = preferences.get("original_market")
    if original and original != check.profile.market:
        sections["vehicle"].paragraphs.append(
            ReportParagraph(
                text=tr(
                    lang,
                    "Исходный рынок не подтверждён. Выбрана справочная модификация США; её характеристики не подтверждают комплектацию конкретного объявления.",
                    "İlkin bazar təsdiqlənməyib. ABŞ istinad versiyası seçilib; xüsusiyyətləri konkret elanın komplektasiyasını təsdiqləmir.",
                    "Original market is unconfirmed. A US reference configuration was selected; its specifications do not confirm the individual listing's equipment.",
                )
            )
        )
    sections["vehicle"].rows = [r for r in sections["vehicle"].rows if r.key != "vin" or report.vin]
    if not report.vin:
        sections.pop("history", None)
    findings = check.profile.dossier_seed.get("knowledge_depth", {}).get("findings", [])
    known = {
        (f["topic"], f["subtopic"]): f
        for f in findings
        if f["status"] == "CONFIRMED" and f.get("value") is not None
    }
    ptype = known.get(("identity", "powertrain_type"), {}).get("value")
    configuration = known.get(("identity", "configuration"), {}).get("value")
    if configuration and not report.vin:
        report.title = f"{check.profile.year} {check.profile.make} {configuration}"
    if sections["fuel"].rows:
        sections["fuel"].paragraphs = [
            ReportParagraph(
                text=tr(
                    lang,
                    "EPA — Агентство по охране окружающей среды США. Здесь приведён официальный цикл; реальный результат зависит от скорости, температуры и маршрута. Электроэнергия и бензин указаны в разных единицах и не сравниваются напрямую. Регламент масла и жидкостей применяется только при наличии документа для выбранной версии.",
                    "EPA ABŞ Ətraf Mühitin Mühafizəsi Agentliyidir. Burada rəsmi sınaq dövrü göstərilir; real nəticə sürət, temperatur və marşrutdan asılıdır. Elektrik və benzin fərqli vahidlərdə verilir və birbaşa müqayisə olunmur. Yağ və maye cədvəli yalnız seçilmiş versiyaya uyğun sənəd olduqda tətbiq edilir.",
                    "EPA is the US Environmental Protection Agency. These are official test-cycle figures; actual results depend on speed, temperature and route. Electricity and gasoline use different units and are not compared directly. Oil and fluid schedules are used only where documentation matches the selected configuration.",
                ),
                source_ids=sorted({s for r in sections["fuel"].rows for s in r.source_ids}),
                evidence_ids=sorted({e for r in sections["fuel"].rows for e in r.evidence_ids}),
            )
        ]
    if sections["recalls"].paragraphs:
        sections["recalls"].paragraphs.insert(
            0,
            ReportParagraph(
                text=tr(
                    lang,
                    "NHTSA — Национальное управление безопасности дорожного движения США. Это кампании для модели и года; принадлежность конкретного автомобиля к кампании и её выполнение проверяются отдельно.",
                    "NHTSA ABŞ Yol Hərəkəti Təhlükəsizliyi Milli İdarəsidir. Bunlar model və il üzrə kampaniyalardır; konkret avtomobilə aidiyyət və icra ayrıca yoxlanır.",
                    "NHTSA is the US National Highway Traffic Safety Administration. These campaigns concern the model year; individual applicability and completion require a separate check.",
                )
            ),
        )
    sections["weak_points"].title = tr(
        lang,
        "Сильные стороны и ограничения",
        "Üstünlüklər və məhdudiyyətlər",
        "Strengths and limitations",
    )
    if ptype == "HEV":
        sections["weak_points"].paragraphs.insert(
            0,
            ReportParagraph(
                text=tr(
                    lang,
                    "Эта конфигурация даёт электрическую помощь без необходимости подключать машину к зарядной станции. Такой формат стоит рассматривать, когда нужен гибрид, а регулярная внешняя зарядка неудобна. Компромисс — наличие тяговой батареи и силовой электроники, состояние которых не определяется общими характеристиками модели.",
                    "Bu konfiqurasiya avtomobili şarj stansiyasına qoşmadan elektrik dəstəyi verir. Hibrid lazım olduğu, lakin müntəzəm xarici şarjın əlverişsiz olduğu halda bu formatı nəzərdən keçirmək olar. Kompromis dartı batareyası və güc elektronikasının olmasıdır; onların vəziyyəti ümumi model xüsusiyyətlərindən müəyyən edilmir.",
                    "This configuration provides electric assistance without requiring a charging station. It is worth considering when a hybrid is desired but regular external charging is inconvenient. The tradeoff is a traction battery and power electronics whose individual condition cannot be established from model specifications.",
                )
            ),
        )
    # Collapse many unknown hybrid component rows into one meaningful gap.
    sections["engine"].rows = [r for r in sections["engine"].rows if r.evidence_ids]
    facts = "; ".join(f"{r.label}: {r.value}" for r in sections["engine"].rows[:5])
    texts = []
    if facts:
        texts.append(facts + ".")
    if ptype == "HEV":
        texts.append(
            tr(
                lang,
                "Это гибрид без внешней зарядки: двигатель и электромотор работают совместно, а батарея получает энергию при движении и торможении. Для сравнения расходов используйте показатели именно этой гибридной модификации. Паспортные мощности двигателя, электромотора и всей системы не взаимозаменяемы. Найденные данные не определяют остаточный ресурс тяговой батареи конкретного автомобиля; для предложения важны сервисные записи и диагностика гибридной системы.",
                "Bu, xaricdən doldurulmayan hibriddir: mühərrik və elektrik motoru birgə işləyir, batareya hərəkət və əyləcləmə zamanı enerji alır. Xərcləri müqayisə edərkən məhz bu hibrid versiyanın göstəricilərindən istifadə edin. Mühərrik, elektrik motoru və sistem gücləri eyni deyil. Tapılan məlumat konkret avtomobilin batareya ömrünü müəyyən etmir; təklif üçün servis qeydləri və hibrid sistemin diaqnostikası vacibdir.",
                "This is a hybrid without external charging: the engine and electric motor work together and the battery recovers energy during driving and braking. Compare consumption using this hybrid configuration's figures. Engine, motor and combined system ratings are not interchangeable. The available specifications do not establish remaining battery life for an individual vehicle; maintenance records and hybrid-system diagnostics matter when assessing an offer.",
            )
        )
    elif ptype == "BEV":
        texts.append(
            tr(
                lang,
                "Это электромобиль. Перед выбором сопоставьте подтверждённый запас хода с ежедневным маршрутом и возможностью регулярной зарядки. Расход электроэнергии нельзя читать как расход бензина. Ёмкость новой батареи, её остаточная ёмкость и мощность зарядки — разные показатели; отсутствующие данные не подменяются характеристиками похожей версии.",
                "Bu elektromobildir. Seçimdən əvvəl təsdiqlənmiş yürüş məsafəsini gündəlik marşrut və müntəzəm şarj imkanı ilə müqayisə edin. Elektrik sərfiyyatı benzin sərfiyyatı deyil. Yeni batareyanın tutumu, qalıq tutum və şarj gücü fərqli göstəricilərdir; çatışmayan məlumat oxşar versiyadan götürülmür.",
                "This is a battery electric vehicle. Compare its confirmed range with daily routes and dependable charging access. Electricity consumption is not gasoline consumption. New battery capacity, remaining capacity and charging power describe different things; missing values are not borrowed from a similar version.",
            )
        )
    elif facts:
        texts.append(
            tr(
                lang,
                "Эти характеристики относятся к выбранной конфигурации. При оценке расходов особенно важны топливо, регламент обслуживания и режим поездок. Официальный расход помогает сравнивать автомобили на единой основе, но не обещает такой же результат в пробках или зимой. Без заводского регламента точные допуски масла и интервалы обслуживания не назначаются. Сведения о надёжности ниже отделены от паспортных данных двигателя.",
                "Bu xüsusiyyətlər seçilmiş konfiqurasiyaya aiddir. Xərclərin qiymətləndirilməsində yanacaq, qulluq cədvəli və istifadə rejimi vacibdir. Rəsmi sərfiyyat vahid əsasda müqayisəyə kömək edir, lakin tıxacda və qışda eyni nəticəyə zəmanət vermir. Zavod cədvəli olmadan dəqiq yağ tələbləri və qulluq intervalları təyin edilmir. Etibarlılıq məlumatı mühərrik xüsusiyyətlərindən ayrıca verilir.",
                "These specifications describe the selected configuration. Fuel, maintenance requirements and journey patterns are central to running costs. Official consumption supports like-for-like comparison but does not promise the same result in traffic or winter. Exact oil approvals and service intervals are not prescribed without manufacturer documentation. Reliability evidence below is kept separate from engine specifications.",
            )
        )
    if texts:
        sections["engine"].paragraphs.insert(
            0,
            ReportParagraph(
                text=" ".join(texts),
                source_ids=sorted({s for r in sections["engine"].rows for s in r.source_ids}),
                evidence_ids=sorted({e for r in sections["engine"].rows for e in r.evidence_ids}),
            ),
        )
    trans = sections["transmission"]
    if trans.rows:
        trans.paragraphs.insert(
            0,
            ReportParagraph(
                text=tr(
                    lang,
                    "Коробка и привод определяют характер движения и требования к обслуживанию. Показанные значения относятся к выбранной конфигурации, а перечень кампаний ниже может охватывать более широкий набор версий. Наличие автоматической коробки само по себе не доказывает ни высокую надёжность, ни неисправность. Для конкретного предложения полезны записи о замене жидкости, выполненных ремонтах и проявлениях при переключении; отсутствие найденных жалоб не заменяет эти сведения.",
                    "Sürətlər qutusu və ötürücü hərəkət xüsusiyyətlərini və qulluq tələblərini müəyyən edir. Göstərilən dəyərlər seçilmiş konfiqurasiyaya aiddir; aşağıdakı kampaniyalar daha geniş versiyaları əhatə edə bilər. Avtomatik qutunun olması nə yüksək etibarlılığı, nə də nasazlığı sübut edir. Konkret təklif üçün maye dəyişməsi, təmir və keçid davranışı barədə qeydlər faydalıdır; şikayət tapılmaması bu məlumatları əvəz etmir.",
                    "Transmission and drivetrain shape driving behaviour and maintenance requirements. The values shown apply to the selected configuration; recall campaigns below may cover a broader range of versions. An automatic transmission alone proves neither reliability nor a fault. For a specific offer, useful evidence includes fluid-change records, previous repairs and shifting symptoms. An absence of discovered complaints cannot replace those records.",
                ),
                source_ids=sorted({s for r in trans.rows for s in r.source_ids}),
                evidence_ids=sorted({e for r in trans.rows for e in r.evidence_ids}),
            ),
        )
    if listing:
        data, sid = listing.get("data", {}), "listing:" + listing["id"]
        labels = {
            "price": ("Цена", "Qiymət", "Price"),
            "mileage_km": (
                "Заявленный пробег, км",
                "Elan edilən yürüş, km",
                "Advertised mileage, km",
            ),
            "city": ("Город", "Şəhər", "City"),
            "color": ("Цвет продавца", "Satıcının rəng məlumatı", "Seller-stated colour"),
            "engine": ("Двигатель продавца", "Satıcının mühərrik məlumatı", "Seller-stated engine"),
            "transmission": (
                "Коробка продавца",
                "Satıcının qutu məlumatı",
                "Seller-stated transmission",
            ),
            "condition_claim": (
                "Состояние со слов продавца",
                "Satıcının vəziyyət iddiası",
                "Seller's condition claim",
            ),
            "market_claim": (
                "Рынок со слов продавца",
                "Satıcının bazar məlumatı",
                "Seller-stated market",
            ),
        }
        rows = [
            ReportRow(
                key="listing." + k,
                label=tr(lang, *v),
                value=str(data[k])
                + (" " + str(data.get("currency") or "") if k == "price" else ""),
                source_ids=[sid],
            )
            for k, v in labels.items()
            if data.get(k) is not None
        ]
        rows.append(
            ReportRow(
                key="listing.url",
                label=tr(lang, "Источник", "Mənbə", "Source"),
                value=listing["source_url"],
                source_ids=[sid],
            )
        )
        sections["offer"] = PaidReportSection(
            key="offer",
            title=tr(
                lang, "Указано продавцом", "Satıcının məlumatı", "As advertised by the seller"
            ),
            rows=rows,
            paragraphs=[
                ReportParagraph(
                    text=tr(
                        lang,
                        "Цена, пробег и состояние — заявления продавца, не подтверждённая история. Фото объявления не являются свидетельством ДТП. Исходный рынок объявления может отличаться от рынка выбранной справочной версии.",
                        "Qiymət, yürüş və vəziyyət satıcının iddialarıdır, təsdiqlənmiş tarixçə deyil. Elan şəkilləri qəza sübutu deyil. Elanın ilkin bazarı seçilmiş istinad versiyasının bazarından fərqlənə bilər.",
                        "Price, mileage and condition are seller claims, not verified history. Listing photos are not accident evidence. The listing's original market may differ from the selected reference configuration.",
                    ),
                    source_ids=[sid],
                )
            ],
        )
        if data.get("description"):
            sections["offer"].paragraphs.append(
                ReportParagraph(text=data["description"], source_ids=[sid])
            )
        report.source_ids.append(sid)
    verdict = sections.pop("expert_verdict")
    if not report.vin:
        verdict.paragraphs = verdict.paragraphs[:1]
    fuel = known.get(("fuel_consumption", "official"), {}).get("value", {})
    if fuel.get("combined"):
        value = fuel["combined"]
        verdict.paragraphs.append(
            ReportParagraph(
                text=tr(
                    lang,
                    f"Эту версию стоит включить в выбор для повседневных поездок, если подходят её привод и трансмиссия. Официальный смешанный расход — {value} л/100 км; он даёт основу для сравнения бюджета поездок. Это не прогноз расхода на вашем маршруте. Доказательств превосходства по ресурсу, комфорту и ликвидности пока недостаточно: низкий расход не заменяет этих критериев.",
                    f"Ötürücü və qutu tələblərinizə uyğundursa, bu versiyanı gündəlik istifadə üçün seçimə daxil etmək olar. Rəsmi qarışıq sərfiyyat {value} l/100 km-dir; səfər büdcəsini müqayisə etməyə əsas verir. Bu, sizin marşrut üçün proqnoz deyil. Resurs, komfort və likvidlik üstünlüyü hələ sübut edilməyib: az sərfiyyat bu meyarları əvəz etmir.",
                    f"Include this configuration in a daily-driving shortlist if its drivetrain and transmission meet your needs. Official combined consumption is {value} L/100 km, providing a basis for comparing travel budgets. It is not a forecast for your route. Evidence of superior longevity, comfort or resale is insufficient; low consumption does not replace those criteria.",
                ),
                source_ids=known[("fuel_consumption", "official")]["source_ids"],
                evidence_ids=known[("fuel_consumption", "official")]["evidence_ids"],
            )
        )
    verdict.paragraphs.append(
        ReportParagraph(
            text=tr(
                lang,
                "Следующий шаг до оплаты автомобиля — получить документы об обслуживании и выполнении подходящих отзывных кампаний. Для дистанционной покупки запросите эти материалы у продавца; независимая проверка выбранного экземпляра остаётся отдельным этапом. Этот разбор объясняет конфигурацию и доступные риски, но не подтверждает нынешнее состояние машины.",
                "Avtomobilə ödənişdən əvvəl növbəti addım qulluq və uyğun geri çağırmaların icra sənədlərini almaqdır. Uzaqdan alış zamanı bunları satıcıdan istəyin; seçilmiş avtomobilin müstəqil yoxlanması ayrıca mərhələdir. Bu təhlil konfiqurasiyanı və mövcud riskləri izah edir, cari vəziyyəti təsdiqləmir.",
                "Before paying for a vehicle, obtain maintenance records and completion evidence for applicable recalls. For a remote purchase, request these from the seller; independent inspection of the selected vehicle is a separate step. This analysis explains the configuration and available risks but does not establish its present condition.",
            )
        )
    )
    if listing:
        verdict.paragraphs.append(
            ReportParagraph(
                text=tr(
                    lang,
                    "Предложение имеет смысл обсуждать после сопоставления заявленной версии с документами и сервисной историей. Указанная цена — цена одного продавца; без сопоставимых актуальных предложений её нельзя назвать рыночной или выгодной.",
                    "Təklifi elan edilmiş versiya sənədlər və servis tarixçəsi ilə tutuşdurulduqdan sonra müzakirə etmək məqsədəuyğundur. Qiymət bir satıcının təklifidir; aktual müqayisələr olmadan onu bazar və ya sərfəli qiymət adlandırmaq olmaz.",
                    "Discuss this offer after reconciling the advertised configuration with documents and service records. Its price is one seller's asking price; without current comparable offers it cannot be called market value or a bargain.",
                )
            )
        )
    report.sections = [verdict, *sections.values()]
    return report


def comparison_projection(members, lang, preferences):
    reports = [
        PaidVehicleReport.model_validate(r.generated_sections["translations"][lang])
        for r in members
    ]
    labels = [r.title + (" · " + str(i + 1)) for i, r in enumerate(reports)]
    sections = []
    keys = (
        "engine",
        "transmission",
        "fuel",
        "chassis",
        "body",
        "weak_points",
        "owner_reviews",
        "offer",
    )
    for key in keys:
        selected = [next((s for s in r.sections if s.key == key), None) for r in reports]
        if not any(selected):
            continue
        title = next(s.title for s in selected if s)
        rows, paragraphs = [], []
        for label, section, vehicle_report in zip(labels, selected, reports, strict=True):
            facts = list(section.rows) if section else []
            if key == "engine":
                facts = [
                    row
                    for item in vehicle_report.sections
                    if item.key == "vehicle"
                    for row in item.rows
                    if row.key == "identity.powertrain_type"
                ] + facts
            summary = " · ".join(f"{r.label}: {r.value}" for r in facts)
            if not summary and section and section.paragraphs:
                summary = section.paragraphs[0].text
            rows.append(
                ReportRow(
                    key=f"{key}.{len(rows)}",
                    label=label,
                    value=summary
                    or tr(
                        lang,
                        "Сопоставимых данных нет",
                        "Müqayisə olunan məlumat yoxdur",
                        "Comparable data unavailable",
                    ),
                    source_ids=sorted(
                        {s for r in facts for s in r.source_ids}
                        | {s for p in (section.paragraphs if section else []) for s in p.source_ids}
                    ),
                    evidence_ids=sorted(
                        {e for r in facts for e in r.evidence_ids}
                        | {
                            e
                            for p in (section.paragraphs if section else [])
                            for e in p.evidence_ids
                        }
                    ),
                )
            )
        sections.append(PaidReportSection(key=key, title=title, rows=rows, paragraphs=paragraphs))
    fuels = []
    for member in members:
        # Use stored normalized official facts, never parse localized rounded prose.
        value = member.evidence_bundle.get("official_consumption")
        fuels.append(value)
    verdict = [
        tr(
            lang,
            "Сравнение не присваивает баллы надёжности по количеству жалоб. Условия эксплуатации и обслуживание могут изменить выбор. Риски конкретного объявления относятся только к этому предложению.",
            "Müqayisə şikayət sayına görə etibarlılıq balı vermir. İstifadə şəraiti və qulluq seçimi dəyişə bilər. Konkret elanın riskləri yalnız həmin təklifə aiddir.",
            "Complaint counts are not reliability scores. Use conditions and maintenance can change the choice. Risks from a specific listing apply only to that offer.",
        )
    ]
    if all(isinstance(x, (float, int)) and x > 0 for x in fuels):
        index = min(range(len(fuels)), key=fuels.__getitem__)
        km = preferences.get("monthly_km") or 1000
        quantities = "; ".join(
            f"{labels[i]}: {float(f) * km / 100:g} L" for i, f in enumerate(fuels)
        )
        verdict.insert(
            0,
            tr(
                lang,
                f"Если главный приоритет — расход топлива, по единому официальному циклу предпочтителен {labels[index]}. При {km} км/месяц расчёт: {quantities}. Это сценарный расчёт, а не прогноз реального расхода. Для выбора по комфорту, ресурсу и перепродаже сопоставимых данных недостаточно; такая рекомендация может измениться после их получения.",
                f"Əsas prioritet yanacaq sərfiyyatıdırsa, eyni rəsmi dövrə görə {labels[index]} üstün görünür. Ayda {km} km üçün hesablama: {quantities}. Bu ssenari hesablamasıdır, real sərfiyyat proqnozu deyil. Komfort, resurs və təkrar satış üçün müqayisə edilən məlumat kifayət deyil; həmin məlumat seçimi dəyişə bilər.",
                f"If fuel consumption is the main priority, {labels[index]} is preferable on the same official test cycle. At {km} km/month: {quantities}. This is a scenario calculation, not a real-world forecast. Comparable comfort, longevity and resale evidence is insufficient; obtaining it could change the recommendation.",
            ),
        )
    else:
        verdict.insert(
            0,
            tr(
                lang,
                "Единый победитель не обоснован: сравнимых данных по выбранным приоритетам недостаточно. Сначала исключите версии, которые не подходят по приводу, трансмиссии или зарядке, затем сопоставьте условия конкретных предложений и обслуживание.",
                "Vahid qalib əsaslandırılmır: seçilmiş prioritetlər üzrə müqayisə olunan məlumat kifayət deyil. Əvvəlcə ötürücü, qutu və ya şarj baxımından uyğun olmayan versiyaları çıxarın, sonra təkliflərin şərtlərini və qulluğunu müqayisə edin.",
                "A single winner is not supported by comparable evidence for the selected priorities. First eliminate configurations that do not fit drivetrain, transmission or charging needs, then compare individual offers and maintenance records.",
            ),
        )
    sections.append(
        PaidReportSection(
            key="expert_verdict",
            title=tr(
                lang, "Что выбрать и почему", "Nəyi və niyə seçmək", "Which to choose and why"
            ),
            paragraphs=[ReportParagraph(text=t) for t in verdict],
        )
    )
    return PaidVehicleReport(
        version=VERSION,
        language=lang,
        vin="",
        title=tr(lang, "Сравнение автомобилей", "Avtomobillərin müqayisəsi", "Vehicle comparison"),
        subtitle=" / ".join(labels),
        generated_at=datetime.now(UTC),
        readiness=reports[0].readiness,
        sections=[sections[-1], *sections[:-1]],
        source_ids=sorted({sid for r in reports for sid in r.source_ids}),
    )
