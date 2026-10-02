# ruff: noqa: E501, E402
"""Reviewed official tariff facts into the existing staged publication pipeline."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.knowledge import ImportManifest  # noqa: E402
from app.services.knowledge_import import (
    enqueue,
    process_job,
    publish_job,
    review_job,
    store_document,
)  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main():
    ledger = json.loads((ROOT / "deliverables/VerifiedData/acquisition-ledger.json").read_text())
    successful = {r["url"]: r for r in ledger if r.get("http_status") == 200}
    old_url = "https://www.tariff.gov.az/post/bir-sira-sahelerde-qiymetler-tenzimlenib"
    new_url = "https://tariff.gov.az/post/bir-sira-mehsul-ve-xidmetler-uzre-guzestler-tetbiq-olunub-qiymetler-mueyyenlesdirilib"
    pdf_url = "https://tariff.gov.az/ckfinder/userfiles/files/30.12.2025-File/Q%C9%99rar%20Elektrik%20(30_12_2025)-%C6%8Flav%C9%99.pdf"
    records = []
    for start, end, url, petrol, diesel in [
        ("2024-07-01", "2025-12-31", old_url, "1.10", "1.00"),
        ("2026-01-01", None, new_url, "1.15", "1.10"),
    ]:
        for kind, price in [("AI92", petrol), ("DIESEL", diesel)]:
            records.append(
                {
                    "external_key": kind + ":" + start,
                    "kind": "ENERGY_PRICE",
                    "source_url": url,
                    "locator": "Fuel retail price paragraph and decision effective date; original AZ text",
                    "observed_at": successful[url]["observed_at"],
                    "effective_from": start,
                    "effective_to": end,
                    "verification": "CONFIRMED",
                    "limitations": {
                        "ru": "Официальная розничная цена. Подходящую марку топлива подтверждает руководство автомобиля. Будущая цена неизвестна.",
                        "az": "Rəsmi pərakəndə qiymət. Uyğun yanacaq markası avtomobilin təlimatı ilə təsdiqlənir. Gələcək qiymət məlum deyil.",
                    },
                    "data": {
                        "energy": kind,
                        "channel": "RETAIL",
                        "provider": "AZ Tariff Council",
                        "unit": "L",
                        "unit_price": price,
                        "regulated": True,
                    },
                }
            )
    records.append(
        {
            "external_key": "HOME:2026-01-01",
            "kind": "ENERGY_PRICE",
            "source_url": pdf_url,
            "locator": "PDF p.1 rows 3.1.1–3.1.3 and 4.1; effective date in 30 Dec 2025 announcement; cross-check Azerishiq FAQ 21 May 2026",
            "observed_at": successful[pdf_url]["observed_at"],
            "effective_from": "2026-01-01",
            "verification": "CONFIRMED",
            "limitations": {
                "ru": "Домашние ступени; учитывается бытовое потребление без автомобиля. Фиксированная плата добавляется только для отдельного нового счётчика. Тариф поставки оператору зарядок не является ценой зарядки.",
                "az": "Ev pillələri; avtomobilsiz məişət sərfiyyatı nəzərə alınır. Sabit haqq yalnız ayrıca yeni sayğac üçün əlavə olunur. Şarj operatoruna təchizat tarifi şarj qiyməti deyil.",
            },
            "data": {
                "energy": "ELECTRICITY",
                "channel": "HOME",
                "provider": "AZ Tariff Council",
                "unit": "kWh",
                "regulated": True,
                "vat_included": True,
                "fixed_monthly": "1.00",
                "tiers": [
                    {"up_to_kwh": 200, "unit_price": "0.084"},
                    {"up_to_kwh": 300, "unit_price": "0.10"},
                    {"up_to_kwh": None, "unit_price": "0.15"},
                ],
            },
        }
    )
    manifest = ImportManifest(
        source_id="az-tariff-council",
        parser="ownership-json-v1",
        ownership_records=records,
        selection_basis="Official dated retail fuel and household electricity facts, inspected primary pages and tariff table; local research only",
    )
    public = ROOT / "data/manifests/az-official-energy.json"
    public.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    with SessionLocal() as db:
        if not db.get(SourceRegistry, "az-tariff-council"):
            db.add(
                SourceRegistry(
                    id="az-tariff-council",
                    title="Azərbaycan Respublikası Tarif Şurası",
                    state="LOCAL_RESEARCH",
                    config={
                        "owner": "AZ Tariff Council",
                        "markets": ["AZ"],
                        "data_types": ["regulated_energy_price"],
                        "documentation_url": "https://tariff.gov.az/tarifler/kommunal-odenisler",
                        "checked_at": "2026-09-20",
                        "adapter": "ownership-json-v1",
                        "authentication": "NONE_PUBLIC",
                        "cost_model": "FREE",
                        "commercial_reuse": False,
                        "storage_rights": "PUBLIC_REGULATORY_FACTS_LOCAL",
                        "display_rights": "ATTRIBUTED_LOCAL_FACTS",
                        "resale_rights": "UNVERIFIED",
                        "allowed_download_urls": [],
                        "verified_rate_limit": None,
                        "freshness_days": {"prices": 30, "rights": 90},
                        "limitations": "Raw official tables contain a third-party footer; no linked footer used. Values cross-checked with supplier. Commercial display review pending.",
                    },
                )
            )
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        if not actor:
            raise ValueError("EXISTING_LOCAL_REVIEW_ACTOR_REQUIRED")
        db.commit()
        for url in (old_url, new_url, pdf_url):
            r = successful[url]
            store_document(
                db,
                "az-tariff-council",
                (ROOT / ".localdata/verified-source-documents" / r["sha256"]).read_bytes(),
                locator=url,
                media_type=r["media_type"],
            )
        job = enqueue(db, manifest)
        while job.state in {"QUEUED", "RUNNING"}:
            process_job(db, job.id, batch_size=100)
        if job.state == "STAGED":
            review_job(
                db,
                job,
                actor,
                approve=True,
                note="Agent technical review of official tariff pages and table; not human image approval",
            )
        if job.state == "APPROVED":
            publish_job(
                db,
                job,
                actor,
                note="Publish attributed official dated energy facts for local research",
            )
        result = {
            "job_id": job.id,
            "state": job.state,
            "records": len(records),
            "paid_calls": 0,
            "scope": "LOCAL_RESEARCH",
        }
        (ROOT / "deliverables/VerifiedData/energy-publication.json").write_text(
            json.dumps(result, indent=2)
        )
        print(json.dumps(result))


if __name__ == "__main__":
    main()
