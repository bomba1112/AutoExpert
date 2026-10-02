"""Review-bound BMW dossier/service batch over the frozen cohort; cached official sources only."""
# ruff: noqa: E402, E501

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal
from app.models.knowledge_ops import SourceRegistry
from app.models.research import ProviderCacheEntry
from app.models.user import User
from app.schemas.knowledge import ImportManifest
from app.services.catalog_buyer import records
from app.services.catalog_verification import identity_verified
from app.services.knowledge_import import (
    enqueue,
    process_job,
    publish_job,
    review_job,
    store_document,
)
from prepare_factory_51 import MAINTENANCE, public_record
from sqlalchemy import select

OUT = ROOT / "deliverables/VerifiedData/verification-51"
CATALOG = ROOT / "data/manifests/us-51-bmw-dossier-reviewed.json"
SERVICE = ROOT / "data/manifests/us-51-bmw-service-reviewed.json"
RECALLS = "https://api.nhtsa.gov/recalls/recallsByVehicle?make=BMW&model=330i&modelYear=2025"
COMMS = "https://static.nhtsa.gov/odi/ffdd/tsbs/MFR_COMMS_RECEIVED_2025-2026.zip"


def prepare(db):
    safety = db.get(SourceRegistry, "nhtsa-safety-batch")
    if safety is None or safety.paused:
        raise ValueError("EXISTING_SAFETY_REGISTRY_REQUIRED")
    safety.state = "LOCAL_RESEARCH"
    safety.config = {
        **safety.config,
        "cost_model": "FREE",
        "commercial_reuse": False,
        "documentation_url": "https://www.nhtsa.gov/nhtsa-datasets-and-apis",
        "checked_at": "2026-09-20",
        "storage_rights": "LOCAL_PUBLIC_FACT_RESEARCH",
        "display_rights": "LOCAL_RESEARCH_ONLY",
        "data_types": ["recall", "manufacturer_communication"],
        "review_note": "Owner-authorized local analysis of official public recall API and downloadable manufacturer communications. No commercial reuse claim for manufacturer documents.",
    }
    db.flush()
    cohort = json.loads((ROOT / "data/manifests/us-51-verification-cohort.json").read_text())
    ids = next(
        r["target_variant_ids"]
        for r in cohort["cohort"]
        if r["make"] == "BMW" and r["model"] == "3 Series"
    )
    selected = [(v, c) for v, c in records(db) if v.id in ids and identity_verified(c)]
    if len(selected) != 2:
        raise ValueError("VERIFIED_BMW_SCOPE_REQUIRED")
    ledger = json.loads((ROOT / "deliverables/VerifiedData/acquisition-ledger.json").read_text())
    receipt = next(r for r in ledger if r["url"] == MAINTENANCE and r.get("http_status") == 200)
    maint = store_document(
        db,
        "factory-bmw-us",
        (ROOT / ".localdata/verified-source-documents" / receipt["sha256"]).read_bytes(),
        locator=MAINTENANCE,
        media_type="application/pdf",
    )
    cached = db.scalar(select(ProviderCacheEntry).where(ProviderCacheEntry.source_url == RECALLS))
    campaigns = [
        {
            k: r[k]
            for k in (
                "campaign_number",
                "component",
                "summary",
                "consequence",
                "make",
                "model",
                "model_year",
            )
        }
        for r in cached.normalized_payload
        if r["campaign_number"] == "25V202000"
    ]
    if len(campaigns) != 1 or "330i xDrive" not in campaigns[0]["summary"]:
        raise ValueError("RECALL_SCOPE_REVIEW_REQUIRED")
    recall = store_document(
        db, safety.id, json.dumps(campaigns, sort_keys=True).encode(), locator=RECALLS
    )
    archive = (
        ROOT
        / ".localdata/priority-official-cache"
        / (hashlib.sha256(COMMS.encode()).hexdigest() + ".bin")
    ).read_bytes()
    comms = store_document(db, safety.id, archive, locator=COMMS, media_type="application/zip")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        rows = list(
            csv.DictReader(
                io.StringIO(z.read("MFR_COMMS_RECEIVED_2025-2026.csv").decode("utf-8-sig"))
            )
        )
    grouped = {
        model: [
            r
            for r in rows
            if r["Make"] == "BMW" and r["Model"] == model and r["Model Year"] == "2025"
        ]
        for model in ("330I", "330I XDRIVE")
    }
    if {k: len(v) for k, v in grouped.items()} != {"330I": 27, "330I XDRIVE": 1}:
        raise ValueError("COMMUNICATIONS_SNAPSHOT_REVIEW_REQUIRED")

    def ref(c, doc, locator):
        return dict(
            registry_id=doc.source_id,
            document_id=doc.id,
            sha256=doc.sha256,
            url=doc.locator,
            locator=locator,
            make=c["make"],
            model=c["model"],
            market="US",
            model_year=2025,
        )

    revised = []
    for variant, c in selected:
        value = public_record(c)
        value["identity_verification"]["previous_revision_id"] = variant.published_revision_id
        r = ref(
            c,
            recall,
            "25V202000; certain MY2025 330i / 330i xDrive; selected fields from cached official response",
        )
        m = ref(
            c,
            maint,
            "US MY2025 Maintenance booklet: printed pages 1-3, 11-13 (PDF 4-6, 14-16); 3 Series columns",
        )
        awd = c["external_key"] == "48164"
        doc_id = "11030312" if awd else "11013062"
        model = "330I XDRIVE" if awd else "330I"
        if not any(row["TSB/Document ID"] == doc_id for row in grouped[model]):
            raise ValueError("COMMUNICATION_NOT_FOUND")
        b = ref(
            c,
            comms,
            f"MFR_COMMS_RECEIVED_2025-2026.csv; BMW / {model} / 2025; document {doc_id}; concise summary only",
        )
        sections = [
            {
                "key": "recalls",
                "status": "PARTIAL",
                "references": [r],
                "text": {
                    "ru": "В сохранённом ответе NHTSA от 20.09.2026 найдена кампания 25V202000 для части BMW 330i и 330i xDrive 2025 года: соединение стартера-генератора с батареей может ослабнуть, что связано с риском остановки двигателя и перегрева проводки. Применимость к конкретному VIN и выполнение ремонта не проверены. Это не доказательство дефекта данного экземпляра.",
                    "az": "NHTSA-nın 20.09.2026 tarixində saxlanmış cavabında bəzi 2025 BMW 330i və 330i xDrive avtomobilləri üçün 25V202000 kampaniyası var: starter-generator ilə batareya arasındakı birləşmə boşala bilər; mühərrikin dayanması və naqillərin qızması riski göstərilir. Konkret VIN-ə uyğunluq və təmirin icrası yoxlanılmayıb. Bu, həmin avtomobildə qüsurun sübutu deyil.",
                },
            },
            {
                "key": "service",
                "status": "PARTIAL",
                "references": [m],
                "text": {
                    "ru": "Заводской регламент BMW США MY2025 использует CBS: масло с фильтром и тормозная жидкость обслуживаются по показаниям системы. Салонный микрофильтр заменяется при каждой второй замене масла, свечи — при каждой шестой для этой 3 Series. Приблизительный пробег в таблице не превращён в фиксированный интервал. Для календаря нужны CBS и история обслуживания; допуски, объёмы жидкостей, воздушный фильтр и цены AZ ещё не подтверждены.",
                    "az": "BMW ABŞ MY2025 zavod qaydası CBS sistemindən istifadə edir: yağ və filtr, həmçinin əyləc mayesi sistemin göstərişinə əsasən dəyişdirilir. Bu 3 Series üçün salon mikrofiltri hər ikinci, şamlar hər altıncı yağ dəyişməsində yenilənir. Cədvəldəki təxmini yürüş sabit interval kimi götürülməyib. Təqvim üçün CBS və xidmət tarixçəsi lazımdır; maye tələbləri, həcmlər, hava filtri və AZ qiymətləri hələ təsdiqlənməyib.",
                },
            },
        ]
        if awd:
            ru = "В архиве сообщений производителей NHTSA есть одна строка BMW 330i xDrive MY2025: документ 11030312 сообщает о неработающих сохранённых точках активации Automate My Habits после обновления ПО 25-07-5XX. Доступна аннотация, а не полный бюллетень; наличие функции, версия ПО, границы выпуска и процедура устранения требуют проверки. Это не оценка частоты отказов."
            az = "NHTSA istehsalçı məlumatları arxivində BMW 330i xDrive MY2025 üçün bir sətir var: 11030312 sənədi 25-07-5XX proqram yeniləməsindən sonra Automate My Habits funksiyasının saxlanmış aktivləşmə nöqtələrinin işləmədiyini bildirir. Yalnız xülasə mövcuddur; funksiyanın olması, proqram versiyası, istehsal sərhədləri və həll proseduru yoxlanılmalıdır. Bu, nasazlıq tezliyinin qiymətləndirilməsi deyil."
        else:
            ru = "В архиве сообщений производителей NHTSA найдены 27 строк BMW 330i MY2025. Например, аннотация документа 11013062 описывает возврат HUD к стандартному виду после повторного включения вместо Navigation View. Это не 27 подтверждённых неисправностей: среди записей есть административные запросы деталей. Полные бюллетени и применимость к оснащению требуют проверки; число строк нельзя переносить на xDrive."
            az = "NHTSA istehsalçı məlumatları arxivində BMW 330i MY2025 üçün 27 sətir tapılıb. Məsələn, 11013062 sənədinin xülasəsi yenidən aktivləşdikdə HUD-un Navigation View əvəzinə standart görünüşə qayıtmasını təsvir edir. Bu, 27 təsdiqlənmiş nasazlıq demək deyil: inzibati hissə sorğuları da var. Tam bülletenlər və təchizata uyğunluq yoxlanılmalıdır; sətir sayını xDrive-a aid etmək olmaz."
        sections.append(
            {
                "key": "communications",
                "status": "PARTIAL",
                "references": [b],
                "text": {"ru": ru, "az": az},
            }
        )
        sections.append(
            {
                "key": "known_issues",
                "status": "PARTIAL",
                "references": [b],
                "text": {
                    "ru": f"Документ {doc_id} даёт условный повод проверить соответствующую функцию на осмотре. До проверки полного бюллетеня и оснащения это кандидат для анализа, а не подтверждённая массовая неисправность семейства. Частота, типичный пробег, стоимость ремонта и окончательная причина не установлены.",
                    "az": f"{doc_id} sənədi baxış zamanı uyğun funksiyanı yoxlamaq üçün şərti əsas verir. Tam bülleten və təchizat yoxlanılana qədər bu, təhlil namizədidir, ailənin təsdiqlənmiş kütləvi nasazlığı deyil. Tezlik, tipik yürüş, təmir xərci və yekun səbəb müəyyən edilməyib.",
                },
            }
        )
        value["documentary_sections"] += sections
        value["revision_note"] = (
            "Reviewed BMW US MY2025 CBS schedule and cached NHTSA recall/communication scopes. Abstract-only issue candidates remain PARTIAL; no VIN history, defect prevalence, or AZ cost inferred."
        )
        revised.append(value)
    db.commit()
    manifest = ImportManifest(
        source_id="epa",
        parser="manifest-json-v1",
        records=revised,
        selection_basis="Enrich only two identity-verified frozen BMW US MY2025 configurations from cached official source evidence",
    )
    CATALOG.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    # CBS conditions cannot be converted into invented kilometre/month due dates.
    operations = [
        (
            "engine_oil_filter",
            "BMW_CBS_ENGINE_OIL_DUE",
            "CBS engine oil service",
            "Масло и фильтр · по CBS",
            "Yağ və filtr · CBS göstərişi ilə",
        ),
        (
            "cabin_microfilter",
            "EVERY_2ND_ENGINE_OIL_SERVICE",
            "Every 2nd engine oil service",
            "Салонный фильтр · каждая вторая замена масла",
            "Salon filtri · hər ikinci yağ dəyişməsində",
        ),
        (
            "spark_plugs",
            "EVERY_6TH_ENGINE_OIL_SERVICE",
            "Every 6th engine oil service",
            "Свечи · каждая шестая замена масла",
            "Şamlar · hər altıncı yağ dəyişməsində",
        ),
        (
            "brake_fluid",
            "BMW_CBS_BRAKE_FLUID_DUE",
            "CBS brake fluid due date",
            "Тормозная жидкость · по CBS",
            "Əyləc mayesi · CBS göstərişi ilə",
        ),
    ]
    ownership = []
    for op, condition, original, ru, az in operations:
        ownership.append(
            dict(
                external_key="bmw-us-my2025-330i-" + op,
                kind="MAINTENANCE",
                variant_ids=ids,
                source_url=MAINTENANCE,
                locator=f"US MY2025 Maintenance booklet, printed pp. 1-3 and 11-13; 3 Series column; sha256:{maint.sha256}",
                observed_at=receipt["observed_at"],
                effective_from="2026-09-20",
                verification="CONFIRMED",
                limitations={
                    "ru": "Только проверенные US MY2025 330i/330i xDrive. CBS и счётчик замен масла требуют истории автомобиля. Фиксированные интервалы, материалы и цены не установлены; тяжёлые условия отдельно не подтверждены.",
                    "az": "Yalnız yoxlanmış US MY2025 330i/330i xDrive. CBS və yağ dəyişmə sayı üçün avtomobilin tarixçəsi lazımdır. Sabit intervallar, materiallar və qiymətlər müəyyən edilməyib; ağır şərait ayrıca təsdiqlənməyib.",
                },
                data=dict(
                    operation=op,
                    action="REPLACE",
                    schedule="NORMAL",
                    condition_codes=[condition],
                    rule="CONDITION_ONLY",
                    original_interval=original,
                    materials=[],
                    labels={"ru": ru, "az": az},
                ),
            )
        )
    service = ImportManifest(
        source_id="factory-bmw-us",
        parser="ownership-json-v1",
        ownership_records=ownership,
        selection_basis="Reviewed US MY2025 BMW maintenance; exact verified configurations; conditional CBS/service-count rules only",
    )
    SERVICE.write_text(service.model_dump_json(indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-reviewed", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        if not CATALOG.exists() or not SERVICE.exists():
            if CATALOG.exists() != SERVICE.exists():
                raise ValueError("INCOMPLETE_PREPARATION_REVIEW_REQUIRED")
            prepare(db)
        if not args.publish_reviewed:
            print(
                json.dumps(
                    {
                        "status": "REVIEW_MANIFEST_READY",
                        "catalog_records": 2,
                        "maintenance_operations": 4,
                    }
                )
            )
            return
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        if actor is None:
            raise ValueError("EXISTING_REVIEW_ACTOR_REQUIRED")
        results = []
        for path in (CATALOG, SERVICE):
            manifest = ImportManifest.model_validate_json(path.read_text(encoding="utf-8"))
            job = enqueue(db, manifest)
            if job.state != "PUBLISHED":
                while job.state in {"QUEUED", "RUNNING"}:
                    process_job(db, job.id, batch_size=10)
                if job.state == "STAGED":
                    review_job(
                        db,
                        job,
                        actor,
                        approve=True,
                        note="Reviewed official PDF 3 Series columns and exact NHTSA model-year rows; no fixed CBS intervals, VIN applicability or generalized defects",
                    )
                publish_job(
                    db,
                    job,
                    actor,
                    note="Publish reviewed partial AZ/RU dossier and conditional maintenance; retain old snapshots",
                )
            results.append(
                {
                    "manifest": path.name,
                    "state": job.state,
                    "job_id": job.id,
                    "records": len(manifest.records) + len(manifest.ownership_records),
                }
            )
        (OUT / "enrichment-publication.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )
        print(json.dumps(results))


if __name__ == "__main__":
    main()
