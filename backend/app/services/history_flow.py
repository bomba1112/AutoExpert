"""VIN-history checkout orchestration; no real provider or payment is enabled."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.catalog import VehicleVariant
from app.models.history_flow import (
    AuctionEvent,
    CostLedgerEntry,
    DamageEvent,
    HistoryAsset,
    HistoryEvent,
    OdometerEvent,
    ProviderCapabilitySnapshot,
    ProviderTransaction,
    RegistrationEvent,
    ReportEntitlement,
    TheftEvent,
    TitleEvent,
    VehicleHistoryReport,
    VinCheckRequest,
)
from app.models.knowledge_ops import SourceRegistry
from app.providers.history_fixture import HistoryProviderError
from app.schemas.history_flow import (
    HistoryCheckRead,
    HistoryPreview,
    HistoryQuote,
    HistoryReportAsset,
    HistoryReportItem,
    HistoryReportRead,
    HistoryReportSection,
)
from app.services.commercial_fact_overlay import (
    claims_for_variants,
    project_commercial_catalog,
    project_existing_commercial_catalog,
)
from app.services.vin_unit_economics import evaluate

TYPED_EVENTS = {
    "ODOMETER": OdometerEvent,
    "DAMAGE": DamageEvent,
    "AUCTION": AuctionEvent,
    "TITLE": TitleEvent,
    "SALVAGE": TitleEvent,
    "TOTAL_LOSS": TitleEvent,
    "LIEN": TitleEvent,
    "REGISTRATION": RegistrationEvent,
    "THEFT": TheftEvent,
}
EVENT_SECTION = {
    "AUCTION": "auction",
    "SALE": "auction",
    "DAMAGE": "damage",
    "ODOMETER": "odometer",
    "TITLE": "title",
    "SALVAGE": "title",
    "TOTAL_LOSS": "title",
    "LIEN": "title",
    "THEFT": "theft",
    "REGISTRATION": "registration",
    "INSURANCE": "registration",
    "RECALL": "recall",
}
SECTION_TITLES = {
    "ru": {
        "vehicle": "Автомобиль и VIN",
        "summary": "Краткий итог",
        "timeline": "Хронология",
        "auction": "Аукционы и фотографии",
        "damage": "Повреждения",
        "odometer": "История пробега",
        "title": "Title, salvage и total loss",
        "theft": "Угон и иные статусы",
        "registration": "Регистрация и страхование",
        "recall": "Отзывные кампании",
        "technical": "Данные Auto Expert о модели",
        "inspection": "Что проверить физически",
        "sources": "Источники и ограничения",
    },
    "az": {
        "vehicle": "Avtomobil və VIN",
        "summary": "Qısa nəticə",
        "timeline": "Xronologiya",
        "auction": "Hərraclar və fotolar",
        "damage": "Zədələr",
        "odometer": "Yürüş tarixçəsi",
        "title": "Title, salvage və total loss",
        "theft": "Oğurluq və digər statuslar",
        "registration": "Qeydiyyat və sığorta",
        "recall": "Geri çağırmalar",
        "technical": "Auto Expert model məlumatları",
        "inspection": "Yerində nəyi yoxlamalı",
        "sources": "Mənbələr və məhdudiyyətlər",
    },
}
EVENT_TEXT = {
    "ru": {
        "AUCTION": "Аукционная запись",
        "SALE": "Запись о продаже",
        "DAMAGE": "Сообщение о повреждении",
        "ODOMETER": "Показание пробега",
        "TITLE": "Событие title",
        "SALVAGE": "Статус salvage",
        "TOTAL_LOSS": "Событие total loss",
        "LIEN": "Сообщение о залоге",
        "THEFT": "Сообщение об угоне",
        "REGISTRATION": "Регистрационное событие",
        "INSURANCE": "Страховое событие",
        "RECALL": "Отзывная кампания",
    },
    "az": {
        "AUCTION": "Hərrac qeydi",
        "SALE": "Satış qeydi",
        "DAMAGE": "Zədə barədə qeyd",
        "ODOMETER": "Yürüş göstəricisi",
        "TITLE": "Title qeydi",
        "SALVAGE": "Salvage statusu",
        "TOTAL_LOSS": "Total loss qeydi",
        "LIEN": "Girov qeydi",
        "THEFT": "Oğurluq qeydi",
        "REGISTRATION": "Qeydiyyat qeydi",
        "INSURANCE": "Sığorta qeydi",
        "RECALL": "Geri çağırma",
    },
}
PHOTO_TYPE_TEXT = {
    "ru": {
        "RETAIL_PHOTO": "фото объявления",
        "WHOLESALE_PHOTO": "аукционное фото",
        "HISTORICAL_PHOTO": "историческое фото",
    },
    "az": {
        "RETAIL_PHOTO": "elan fotosu",
        "WHOLESALE_PHOTO": "hərrac fotosu",
        "HISTORICAL_PHOTO": "tarixi foto",
    },
}


def owned_check(
    db: Session, user_id: str, check_id: str, *, lock: bool = False
) -> VinCheckRequest | None:
    query = select(VinCheckRequest).where(
        VinCheckRequest.id == check_id, VinCheckRequest.user_id == user_id
    )
    return db.scalar(query.with_for_update() if lock else query)


def entitlement(db: Session, check: VinCheckRequest, user_id: str) -> ReportEntitlement | None:
    return db.scalar(
        select(ReportEntitlement).where(
            ReportEntitlement.request_id == check.id,
            ReportEntitlement.user_id == user_id,
            ReportEntitlement.status == "ACTIVE",
        )
    )


def check_read(db: Session, check: VinCheckRequest, user_id: str) -> HistoryCheckRead:
    return HistoryCheckRead(
        check_id=check.id,
        vin=check.vin,
        status=check.status,
        vehicle_identity=check.vehicle_identity or {},
        preview=HistoryPreview.model_validate(
            {
                key: value
                for key, value in (check.preview or {}).items()
                if key in HistoryPreview.model_fields
            }
        ),
        quote=HistoryQuote.model_validate(check.quote or {}),
        is_unlocked=entitlement(db, check, user_id) is not None,
        is_mock=check.is_mock,
    )


def create_check(
    db: Session, *, user_id: str, vin: str, language: str, provider
) -> VinCheckRequest:
    existing = db.scalar(
        select(VinCheckRequest).where(
            VinCheckRequest.user_id == user_id,
            VinCheckRequest.vin == vin,
            VinCheckRequest.provider_id == provider.id,
            VinCheckRequest.product == "VIN_HISTORY",
        )
    )
    if existing is not None and not (
        existing.status == "FAILED_RETRYABLE" and entitlement(db, existing, user_id) is None
    ):
        return existing
    if existing is None:
        check = VinCheckRequest(
            user_id=user_id,
            vin=vin,
            provider_id=provider.id,
            product="VIN_HISTORY",
            language=language,
            status="CREATED",
            vehicle_identity={},
            preview={},
            quote={},
            is_mock=provider.is_mock,
        )
        db.add(check)
        db.flush()
    else:
        check = existing
        check.status = "CREATED"
        check.failure_code = None
    try:
        provider.validate_vin(vin)
        identity = provider.decode_vin(vin)
        preflight = provider.preflight(vin)
        provider_quote = provider.quote(vin, "VIN_HISTORY")
    except HistoryProviderError as error:
        check.status = "FAILED_RETRYABLE" if error.retryable else "FAILED_FINAL"
        check.failure_code = error.code
        check.quote = {"reason": error.code}
        db.commit()
        return check
    check.vehicle_identity = {
        k: identity[k]
        for k in (
            "make",
            "model",
            "model_year",
            "market",
            "engine_description",
            "transmission_description",
            "drivetrain",
        )
        if identity.get(k) is not None
    }
    check.preview = preflight
    capability = db.scalar(
        select(ProviderCapabilitySnapshot).where(ProviderCapabilitySnapshot.request_id == check.id)
    )
    if capability is None:
        db.add(
            ProviderCapabilitySnapshot(
                request_id=check.id,
                provider_id=provider.id,
                capabilities=dict(provider.capabilities),
            )
        )
    assessment = evaluate(
        provider_cost_usd=provider_quote.get("provider_cost_usd"),
        provider_cost_azn=provider_quote.get("provider_cost_azn"),
        retail_price_azn=provider_quote.get("retail_price_azn"),
        fx_rate_azn_per_usd=provider_quote.get("fx_azn_per_usd"),
        payment_fee_azn=provider_quote.get("payment_fee_azn", "0"),
        payment_fee_rate=provider_quote.get("payment_fee_rate", "0"),
        tax_fee_azn=provider_quote.get("tax_fee_azn", "0"),
        tax_fee_rate=provider_quote.get("tax_fee_rate", "0"),
        retry_cost_azn=provider_quote.get("retry_cost_azn", "0"),
        minimum_margin_azn=get_settings().vin_history_minimum_margin_azn,
    )
    mock_only = bool(provider_quote.get("mock_only")) and provider.is_mock
    can_offer = bool(preflight.get("history_available")) and assessment.sellable and mock_only
    check.quote = {
        "retail_price_azn": str(provider_quote["retail_price_azn"]) if can_offer else None,
        "currency": "AZN",
        "sellable": can_offer,
        "reason": None
        if can_offer
        else (
            "NO_HISTORY" if preflight.get("history_available") is False else assessment.status.value
        ),
        "is_mock_scenario": mock_only,
    }
    check.status = "AWAITING_PAYMENT" if can_offer else "PREFLIGHT_COMPLETE"
    db.commit()
    return check


def mock_payment(
    db: Session, check: VinCheckRequest, *, user_id: str, provider, simulate_failure: bool = False
) -> VinCheckRequest:
    if entitlement(db, check, user_id) is not None:
        return check
    if check.status != "AWAITING_PAYMENT" or not (check.quote or {}).get("sellable"):
        raise ValueError("REPORT_NOT_SELLABLE")
    payment = db.scalar(
        select(ProviderTransaction).where(
            ProviderTransaction.request_id == check.id, ProviderTransaction.kind == "MOCK_PAYMENT"
        )
    )
    if payment is None:
        payment = ProviderTransaction(
            request_id=check.id,
            provider_id="mock",
            kind="MOCK_PAYMENT",
            status="FAILED" if simulate_failure else "SUCCEEDED",
            idempotency_key=f"mock-payment:{check.id}",
            external_id=None if simulate_failure else f"mock:{check.id}",
            raw_payload={"sandbox": True},
        )
        db.add(payment)
        db.flush()
    elif payment.status == "FAILED" and not simulate_failure:
        # A failed *mock* attempt can be retried using the same stable payment
        # record. No second successful charge or entitlement is created.
        payment.status = "SUCCEEDED"
        payment.external_id = f"mock:{check.id}"
    if simulate_failure or payment.status != "SUCCEEDED":
        db.commit()
        return check
    db.add(
        ReportEntitlement(
            user_id=user_id, request_id=check.id, status="ACTIVE", payment_transaction_id=payment.id
        )
    )
    db.add(
        CostLedgerEntry(
            request_id=check.id,
            kind="MOCK_RETAIL",
            amount=Decimal(check.quote["retail_price_azn"]),
            currency="AZN",
            is_mock=True,
            snapshot={"sandbox": True},
        )
    )
    mock_quote = provider.quote(check.vin, check.product)
    cost_currency = "USD" if mock_quote.get("provider_cost_usd") is not None else "AZN"
    db.add(
        CostLedgerEntry(
            request_id=check.id,
            kind="MOCK_PROVIDER_COST",
            amount=Decimal(
                str(mock_quote.get("provider_cost_usd") or mock_quote.get("provider_cost_azn"))
            ),
            currency=cost_currency,
            is_mock=True,
            snapshot={"sandbox": True},
        )
    )
    check.status = "PAID"
    db.commit()  # durable entitlement before any provider call
    return fetch_report(db, check, provider=provider)


def fetch_report(db: Session, check: VinCheckRequest, *, provider) -> VinCheckRequest:
    if db.scalar(select(VehicleHistoryReport).where(VehicleHistoryReport.request_id == check.id)):
        return check
    txn = db.scalar(
        select(ProviderTransaction).where(
            ProviderTransaction.request_id == check.id, ProviderTransaction.kind == "REPORT"
        )
    )
    if txn is None:
        txn = ProviderTransaction(
            request_id=check.id,
            provider_id=provider.id,
            kind="REPORT",
            status="REQUESTED",
            idempotency_key=f"history-report:{check.id}",
        )
        db.add(txn)
    check.status = "PROVIDER_REQUESTED"
    db.commit()  # crash recovery repeats the same provider idempotency key
    try:
        raw = provider.purchase_or_fetch(check.vin, check.product, txn.idempotency_key)
        normalized = provider.normalize(raw)
        if normalized.get("vin") != check.vin:
            raise HistoryProviderError("VIN_MISMATCH")
        assets = provider.get_assets(normalized["provider_report_id"])
        publish_normalized(db, check, txn, normalized, raw=raw, asset_bytes=assets)
    except HistoryProviderError as error:
        txn.status = "FAILED_RETRYABLE" if error.retryable else "FAILED_FINAL"
        txn.failure_code = error.code
        check.status = txn.status if error.retryable else "REFUND_REQUIRED"
        check.failure_code = error.code
        db.commit()
    except (OSError, TimeoutError):
        txn.status = "FAILED_RETRYABLE"
        txn.failure_code = "PROVIDER_UNAVAILABLE"
        check.status = txn.status
        check.failure_code = txn.failure_code
        db.commit()
    return check


def publish_normalized(
    db: Session,
    check: VinCheckRequest,
    txn: ProviderTransaction,
    normalized: dict,
    *,
    raw: dict,
    asset_bytes: dict[str, bytes],
) -> VehicleHistoryReport:
    existing = db.scalar(
        select(VehicleHistoryReport).where(VehicleHistoryReport.request_id == check.id)
    )
    if existing is not None:
        return existing
    if normalized.get("vin") != check.vin:
        raise HistoryProviderError("VIN_MISMATCH")
    report = VehicleHistoryReport(
        request_id=check.id,
        provider_id=check.provider_id,
        provider_report_id=normalized.get("provider_report_id"),
        status="REPORT_READY",
        vehicle_identity=check.vehicle_identity,
        normalized_snapshot={"event_count": len(normalized.get("events", []))},
        source_snapshot=normalized.get("source", {}),
    )
    db.add(report)
    db.flush()
    event_ids: dict[str, str] = {}
    for position, item in enumerate(normalized.get("events", [])):
        event_type = item["event_type"]
        source_id = item["source_record_id"]
        event = HistoryEvent(
            report_id=report.id,
            event_type=event_type,
            event_date=item.get("event_date"),
            country=item.get("country"),
            state=item.get("state"),
            mileage=item.get("mileage"),
            mileage_unit=item.get("mileage_unit"),
            source_provider=check.provider_id,
            source_record_id=source_id,
            normalized_summary=item.get("normalized_summary", {}),
            raw_locator=f"provider_transactions/{txn.id}/events/{position}",
            confidence=item.get("confidence", "SOURCE_REPORTED"),
            status=item.get("status", "REPORTED"),
        )
        db.add(event)
        db.flush()
        event_ids[source_id] = event.id
        typed = TYPED_EVENTS.get(event_type)
        if typed is not None:
            db.add(
                typed(id=str(uuid4()), history_event_id=event.id, details=item.get("details", {}))
            )
    for item in normalized.get("assets", []):
        # Rights must be explicit. No provider URLs ever enter the public response.
        source_id = item["id"]
        if not item.get("display_rights_confirmed") or source_id not in asset_bytes:
            continue
        db.add(
            HistoryAsset(
                report_id=report.id,
                event_id=event_ids.get(item.get("event_id")),
                source_record_id=source_id,
                media_type=item["media_type"],
                photo_type=item.get("photo_type", "UNKNOWN_PHOTO_TYPE"),
                display_rights_confirmed=True,
                payload=asset_bytes[source_id],
                caption=item.get("caption", {}),
            )
        )
    txn.raw_payload = raw  # private source response, separate from report projection
    txn.external_id = normalized.get("provider_report_id")
    txn.status = "COMPLETE"
    check.status = "REPORT_READY" if normalized.get("events") else "PARTIAL"
    check.failure_code = None
    db.commit()
    return report


def report_read(db: Session, check: VinCheckRequest, *, language: str) -> HistoryReportRead:
    report = db.scalar(
        select(VehicleHistoryReport).where(VehicleHistoryReport.request_id == check.id)
    )
    if report is None:
        raise ValueError("REPORT_NOT_READY")
    events = list(
        db.scalars(
            select(HistoryEvent)
            .where(HistoryEvent.report_id == report.id)
            .order_by(HistoryEvent.event_date, HistoryEvent.id)
        )
    )
    assets = list(
        db.scalars(
            select(HistoryAsset).where(
                HistoryAsset.report_id == report.id, HistoryAsset.display_rights_confirmed.is_(True)
            )
        )
    )
    event_by_id = {event.id: event for event in events}
    title_details = {
        row.history_event_id: row.details
        for row in db.scalars(
            select(TitleEvent).where(
                TitleEvent.history_event_id.in_(
                    [
                        e.id
                        for e in events
                        if e.event_type in {"TITLE", "SALVAGE", "TOTAL_LOSS", "LIEN"}
                    ]
                )
            )
        )
    }
    buckets: dict[str, list[HistoryReportItem]] = {key: [] for key in SECTION_TITLES[language]}
    odometer_points = []
    for event in events:
        facts = [
            EVENT_TEXT[language].get(
                event.event_type,
                "Другое событие" if language == "ru" else "Digər hadisə",
            )
        ]
        if event.event_type == "ODOMETER" and event.mileage is not None and event.mileage_unit:
            facts.append(f"{event.mileage:,} {event.mileage_unit}")
        title_type = title_details.get(event.id, {}).get("title_type")
        if title_type:
            facts.append(str(title_type))
        if event.state or event.country:
            facts.append("/".join(v for v in (event.country, event.state) if v))
        facts.append(("источник" if language == "ru" else "mənbə") + f" {event.source_provider}")
        item = HistoryReportItem(event_id=event.id, date=event.event_date, text=" · ".join(facts))
        buckets["timeline"].append(item)
        section = EVENT_SECTION.get(event.event_type)
        if section:
            buckets[section].append(item)
        if (
            event.event_type == "ODOMETER"
            and event.event_date
            and event.mileage is not None
            and event.mileage_unit in {"mi", "km"}
        ):
            odometer_points.append(
                {
                    "date": event.event_date,
                    "mileage_km": round(
                        event.mileage * (1.609344 if event.mileage_unit == "mi" else 1)
                    ),
                    "original_value": event.mileage,
                    "original_unit": event.mileage_unit,
                }
            )
    odometer_points.sort(key=lambda row: row["date"])
    anomaly = any(
        a["mileage_km"] > b["mileage_km"]
        for a, b in zip(odometer_points, odometer_points[1:], strict=False)
    )
    buckets["vehicle"].append(
        HistoryReportItem(
            text=(
                f"{check.vehicle_identity.get('model_year', '')} "
                f"{check.vehicle_identity.get('make', '')} "
                f"{check.vehicle_identity.get('model', '')} · {check.vin}"
            )
        )
    )
    buckets["summary"].append(
        HistoryReportItem(
            text=(
                f"{len(events)} записей из учебного источника."
                if check.is_mock and language == "ru"
                else f"Nümunə mənbədə {len(events)} qeyd."
                if check.is_mock
                else f"Поставщик истории сообщил {len(events)} событий."
                if language == "ru"
                else f"Tarixçə provayderi {len(events)} hadisə bildirdi."
            )
        )
    )
    if anomaly:
        buckets["odometer"].append(
            HistoryReportItem(
                text=(
                    "Обнаружена аномалия последовательности пробега"
                    if language == "ru"
                    else "Yürüş qeydlərinin ardıcıllığında uyğunsuzluq aşkarlandı"
                )
            )
        )
    for asset in assets:
        caption = (asset.caption or {}).get(language)
        photo_label = PHOTO_TYPE_TEXT[language].get(
            asset.photo_type, "Foto" if language == "az" else "Фото"
        )
        buckets["auction"].append(
            HistoryReportItem(
                event_id=asset.event_id,
                text=photo_label + (f" · {caption}" if caption else ""),
            )
        )
    if buckets["damage"] or buckets["title"]:
        buckets["inspection"].append(
            HistoryReportItem(
                text=(
                    "Проверьте кузов, документы и состояние автомобиля при осмотре."
                    if language == "ru"
                    else "Baxış zamanı kuzovu, sənədləri və avtomobilin vəziyyətini yoxlayın."
                )
            )
        )
    technical_card = production_technical_card(db, check.vehicle_identity)
    if technical_card is not None:
        buckets["technical"].append(
            HistoryReportItem(
                text=(
                    "Модель и год присутствуют в опубликованном техническом каталоге Auto Expert."
                    if language == "ru"
                    else "Model və il Auto Expert-in dərc olunmuş texniki kataloqunda var."
                )
            )
        )
        exact = technical_card.get("exact_variant")
        if exact:
            labels = {
                "ru": ("Двигатель", "Коробка", "Привод"),
                "az": ("Mühərrik", "Qutu", "Ötürücü"),
            }[language]
            for label, value in zip(labels, exact, strict=True):
                buckets["technical"].append(HistoryReportItem(text=f"{label}: {value}"))
        else:
            buckets["technical"].append(
                HistoryReportItem(
                    text=(
                        "Точный вариант двигателя и коробки по этому VIN не установлен."
                        if language == "ru"
                        else "Bu VIN üzrə dəqiq mühərrik və qutu variantı müəyyən edilməyib."
                    )
                )
            )
    buckets["sources"].append(
        HistoryReportItem(
            text=(
                "Синтетический локальный источник для проверки интерфейса; "
                "не является историей реального VIN."
                if check.is_mock and language == "ru"
                else "İnterfeys yoxlaması üçün sintetik yerli mənbə; real VIN tarixçəsi deyil."
                if check.is_mock
                else "Данные предоставлены указанным поставщиком истории."
                if language == "ru"
                else "Məlumatlar göstərilən tarixçə provayderindən alınıb."
            )
        )
    )
    buckets["sources"].append(
        HistoryReportItem(text=(f"{check.provider_id} · {report.created_at.date().isoformat()}"))
    )
    if check.is_mock:
        buckets["sources"].append(
            HistoryReportItem(
                text=(
                    "Покрытие: только синтетические записи, без проверки внешнего поставщика."
                    if language == "ru"
                    else "Əhatə: yalnız sintetik qeydlər; xarici provayder yoxlanmayıb."
                )
            )
        )
    sections = [
        HistoryReportSection(key=key, title=title, items=buckets[key])
        for key, title in SECTION_TITLES[language].items()
        if buckets[key]
    ]
    return HistoryReportRead(
        check_id=check.id,
        vin=check.vin,
        language=language,
        status=check.status,
        vehicle_identity=check.vehicle_identity,
        sections=sections,
        mileage_anomaly=anomaly,
        odometer_points=odometer_points,
        asset_ids=[asset.id for asset in assets],
        assets=[
            HistoryReportAsset(
                id=asset.id,
                caption=(asset.caption or {}).get(language),
                event_date=event_by_id[asset.event_id].event_date
                if asset.event_id in event_by_id
                else None,
                source=event_by_id[asset.event_id].source_provider
                if asset.event_id in event_by_id
                else report.provider_id,
                photo_type=asset.photo_type
                if asset.photo_type in PHOTO_TYPE_TEXT[language]
                else None,
            )
            for asset in assets
        ],
        is_mock=check.is_mock,
    )


def production_technical_card(db: Session, identity: dict) -> dict | None:
    """Read-only rights-safe model/year join; never admit internal EPA facts.

    An exact variant needs independent engine/transmission/drive identification,
    which a make/model/year-only VIN decoder does not provide.
    """
    make, model, year = (identity.get(key) for key in ("make", "model", "model_year"))
    if not make or not model or not isinstance(year, int):
        return None
    candidates = list(
        db.scalars(
            select(VehicleVariant).where(
                VehicleVariant.published_revision_id.is_not(None),
                VehicleVariant.is_demo.is_(False),
                VehicleVariant.specifications["catalog"]["make"].as_string() == make,
                VehicleVariant.specifications["catalog"]["model"].as_string() == model,
                VehicleVariant.specifications["catalog"]["model_year"].as_integer() == year,
            )
        )
    )
    if not candidates:
        return None
    sources = {s.id: s for s in db.scalars(select(SourceRegistry))}
    claims = claims_for_variants(db, [v.id for v in candidates])
    eligible = []
    for variant in candidates:
        catalog = variant.specifications.get("catalog") or {}
        if catalog.get("original_market") not in {"US", "USA"}:
            continue
        source = sources.get(catalog.get("source_registry_id"))
        if (
            source
            and (source.config or {}).get("commercial_reuse")
            and catalog.get("publication_scope") == "COMMERCIAL"
        ):
            safe = project_existing_commercial_catalog(catalog, sources)
        else:
            safe = project_commercial_catalog(catalog, claims.get(variant.id, []), sources)
        if safe is not None:
            eligible.append(safe)
    if not eligible:
        return None
    keys = ("engine_description", "transmission_description", "drivetrain")
    if not all(identity.get(key) for key in keys):
        return {"model_year_present": True}

    def normalized(value: object) -> str:
        return " ".join(str(value).casefold().split())

    requested = tuple(normalized(identity[key]) for key in keys)
    matches = []
    for safe in eligible:
        facts = safe.get("facts") or {}
        values = tuple((facts.get(key) or {}).get("value") for key in keys)
        if (
            all(isinstance(value, str) for value in values)
            and tuple(normalized(value) for value in values) == requested
        ):
            matches.append(values)
    return (
        {"model_year_present": True, "exact_variant": matches[0]}
        if len(matches) == 1
        else {"model_year_present": True}
    )


def production_model_year_exists(db: Session, identity: dict) -> bool:
    return production_technical_card(db, identity) is not None
