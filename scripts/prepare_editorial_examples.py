# ruff: noqa: E501
"""Prepare factual editorial comparisons from published source rows, never per view.

Local research edition only. This script does not approve photos or commercial rights.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.api.routes.knowledge import (
    PublicationInput,
    ReviewInput,
    publication_review,
    save_publication,
)
from app.db.session import SessionLocal
from app.models.user import User
from app.services.catalog_buyer import fact_value, records
from sqlalchemy import select

with SessionLocal() as db:
    reviewer = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
    if not reviewer:
        raise SystemExit("An existing local editorial reviewer is required")
    all_rows = records(db)
    prepared = []
    for make, model in [("Toyota", "Corolla"), ("Hyundai", "Elantra"), ("Honda", "Accord")]:
        variants = [
            (v, c)
            for v, c in all_rows
            if c["make"] == make and c["model"] == model and c["model_year"] == 2026
        ]
        chosen = []
        for powertrain in ("ICE", "HEV"):
            eligible = [
                (v, c)
                for v, c in variants
                if fact_value(c, "powertrain") == powertrain and fact_value(c, "fuel_combined")
            ]
            if not eligible:
                break
            chosen.append(
                min(eligible, key=lambda item: Decimal(str(fact_value(item[1], "fuel_combined"))))
            )
        if len(chosen) != 2:
            continue
        fuel = [fact_value(c, "fuel_combined") for _, c in chosen]
        quantity = [str(Decimal(str(f)) * 240) for f in fuel]
        evidence = [c["facts"]["fuel_combined"]["evidence_id"] for _, c in chosen]
        name = make + " " + model
        value = PublicationInput(
            slug=(make + "-" + model + "-2026-ice-hev").lower(),
            translations={
                "ru": {
                    "title": name + ": бензин или гибрид?",
                    "summary": "Две версии 2026 года. Расход по EPA и ваши условия.",
                    "paragraphs": [
                        f"У выбранной бензиновой версии расход по комбинированному циклу EPA — {fuel[0]} л/100 км; у выбранной HEV — {fuel[1]} л/100 км. Это характеристики конкретных конфигураций, не всех машин с этим названием.",
                        f"При 1000 км в месяц за 24 месяца сценарий составляет {quantity[0]} и {quantity[1]} л соответственно. Цены покупки, топлива, перепродажи и ремонта не заданы, поэтому полная стоимость и окупаемость неизвестны.",
                        "Миф: меньший официальный расход автоматически означает лучшую покупку. Для вывода нужны цена предложения, история обслуживания и диагностика конкретного автомобиля.",
                    ],
                    "limitations": "Локальная исследовательская публикация по рынку США. Поколения и точные коды агрегатов пока не подтверждены. Цикл EPA не обещает такой же расход в Баку. Надёжность, ликвидность и состояние батареи не оценивались. Фото моделей ожидают проверки прав и применимости.",
                },
                "az": {
                    "title": name + ": benzin, yoxsa hibrid?",
                    "summary": "2026-cı ilin iki versiyası. EPA sərfiyyatı və sizin şəraitiniz.",
                    "paragraphs": [
                        f"Seçilmiş benzin versiyası üçün EPA qarışıq dövr sərfiyyatı {fuel[0]} l/100 km, seçilmiş HEV üçün isə {fuel[1]} l/100 km-dir. Bunlar həmin adlı bütün avtomobillərin deyil, konkret konfiqurasiyaların göstəriciləridir.",
                        f"Ayda 1000 km və 24 ay üçün ssenari müvafiq olaraq {quantity[0]} və {quantity[1]} l edir. Alış, yanacaq, təkrar satış və təmir qiymətləri verilməyib; tam xərc və özünüödəmə məlum deyil.",
                        "Mif: aşağı rəsmi sərfiyyat avtomatik olaraq daha yaxşı alış deməkdir. Nəticə üçün təklif qiyməti, servis tarixçəsi və konkret avtomobilin diaqnostikası lazımdır.",
                    ],
                    "limitations": "ABŞ bazarı üzrə lokal tədqiqat nəşri. Nəsillər və dəqiq aqreqat kodları hələ təsdiqlənməyib. EPA dövrü Bakıda eyni sərfiyyata zəmanət vermir. Etibarlılıq, satış sürəti və batareya vəziyyəti qiymətləndirilməyib. Model şəkillərinin hüquq və uyğunluq yoxlaması gözlənilir.",
                },
            },
            variant_ids=[v.id for v, _ in chosen],
            asset_ids=[],
            topics=["cost", "HEV"],
            scenario={
                "months": 24,
                "monthly_km": 1000,
                "currency": "AZN",
                "price_inputs": None,
                "formula": "distance_km * source_l_per_100km / 100",
            },
            claims=[
                {
                    "kind": "OFFICIAL_CONSUMPTION_COMPARISON",
                    "evidence_ids": evidence,
                    "source_ids": list(
                        {c["facts"]["fuel_combined"]["source_id"] for _, c in chosen}
                    ),
                    "values": fuel,
                    "unit": "L/100km",
                    "cycle": "EPA",
                    "quantity_24_months_l": quantity,
                }
            ],
        )
        publication = save_publication(value, db, reviewer)
        publication_review(
            publication["id"],
            ReviewInput(
                action="publish",
                note="Reviewed official source values, Decimal scenario arithmetic and bilingual limitations. No image, reliability or commercial rights approval.",
            ),
            db,
            reviewer,
        )
        prepared.append(
            {
                "id": publication["id"],
                "slug": value.slug,
                "variant_ids": value.variant_ids,
                "vehicle_images": "IMAGE_QA",
            }
        )
    Path("deliverables/MasterLocal/editorial-publications.json").write_text(
        json.dumps(prepared, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"local_research_publications": len(prepared), "approved_vehicle_images": 0}))
