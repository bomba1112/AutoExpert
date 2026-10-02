from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.models.enums import OdometerRisk

TOYOTA_DEMO_VIN = "4T1B11HK8KU000000"
FORD_EXAMPLE_VIN = "3FA6P0HD0KR114795"

# Backwards-compatible name for the original Toyota regression fixture. New
# developer-review UI uses FORD_EXAMPLE_VIN explicitly.
DEMO_VIN = TOYOTA_DEMO_VIN


@dataclass(frozen=True)
class ResolvedVINVehicle:
    make: str
    model: str
    generation: str
    production_year_start: int
    production_year_end: int
    market: str
    year: int
    engine: str
    engine_code: str
    transmission: str
    drivetrain: str
    body: str
    fuel: str
    is_demo: bool


@dataclass(frozen=True)
class VINPrecheckData:
    found: bool
    records_count: int
    photos_count: int
    auctions_count: int
    has_salvage_title: bool
    odometer_risk: OdometerRisk
    is_demo: bool


class VINPrecheckProvider(Protocol):
    name: str

    def resolve_vehicle(self, vin: str) -> ResolvedVINVehicle | None: ...

    def precheck(self, vin: str) -> VINPrecheckData: ...

    def full_history(self, vin: str) -> dict: ...


class DeterministicDemoVINPrecheckProvider:
    name = "deterministic_demo_vin"

    def resolve_vehicle(self, vin: str) -> ResolvedVINVehicle | None:
        if vin == TOYOTA_DEMO_VIN:
            return ResolvedVINVehicle(
                make="Toyota",
                model="Camry",
                generation="XV70",
                production_year_start=2017,
                production_year_end=2024,
                market="USA",
                year=2019,
                engine="2.5 petrol",
                engine_code="A25A-FKS",
                transmission="8AT",
                drivetrain="FWD",
                body="sedan",
                fuel="petrol",
                is_demo=True,
            )
        if vin == FORD_EXAMPLE_VIN:
            return ResolvedVINVehicle(
                make="Ford",
                model="Fusion",
                generation="UNRESOLVED",
                production_year_start=2019,
                production_year_end=2019,
                market="USA",
                year=2019,
                engine="UNRESOLVED — DEMO identity only",
                engine_code="UNRESOLVED",
                transmission="UNRESOLVED",
                drivetrain="UNRESOLVED",
                body="sedan",
                fuel="UNRESOLVED",
                is_demo=True,
            )
        return None

    def precheck(self, vin: str) -> VINPrecheckData:
        found = vin in {TOYOTA_DEMO_VIN, FORD_EXAMPLE_VIN}
        return VINPrecheckData(
            found=found,
            records_count=3 if found else 0,
            photos_count=18 if found else 0,
            auctions_count=2 if found else 0,
            has_salvage_title=found,
            odometer_risk=OdometerRisk.HIGH if found else OdometerRisk.UNKNOWN,
            is_demo=True,
        )

    def full_history(self, vin: str) -> dict:
        if vin not in {TOYOTA_DEMO_VIN, FORD_EXAMPLE_VIN}:
            return {
                "vin": vin,
                "timeline": [],
                "auctions": [],
                "photos": [],
                "damage_details": [],
                "odometer_records": [],
                "is_demo": True,
                "data_origin": "DEMO",
            }
        return {
            "vin": vin,
            "timeline": [
                {
                    "date": "2019-06-10",
                    "event_type": "DEMO_REGISTRATION",
                    "summary": "DEMO: synthetic registration event.",
                    "status": "ESTIMATE",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                },
                {
                    "date": "2023-04-18",
                    "event_type": "DEMO_AUCTION",
                    "summary": "DEMO: synthetic auction event with damage notation.",
                    "status": "NEEDS_INSPECTION",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                },
                {
                    "date": "2023-05-02",
                    "event_type": "DEMO_AUCTION",
                    "summary": "DEMO: synthetic second auction listing.",
                    "status": "ESTIMATE",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                },
            ],
            "auctions": [
                {
                    "date": "2023-04-18",
                    "sale_price": 6200,
                    "currency": "USD",
                    "damage": "DEMO: synthetic front-area damage entry.",
                    "status": "ESTIMATE",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                },
                {
                    "date": "2023-05-02",
                    "sale_price": 7100,
                    "currency": "USD",
                    "damage": "DEMO: synthetic secondary auction entry.",
                    "status": "ESTIMATE",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                },
            ],
            "photos": [
                {
                    "id": f"demo-photo-{index:02d}",
                    "label": f"DEMO archive photo {index}",
                    "placeholder": True,
                    "status": "ESTIMATE",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                }
                for index in range(1, 19)
            ],
            "damage_details": [
                {
                    "area": "front",
                    "description": "DEMO: synthetic damage detail; not a real VIN record.",
                    "status": "NEEDS_INSPECTION",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                }
            ],
            "odometer_records": [
                {
                    "date": "2022-01-10",
                    "value": 41000,
                    "unit": "mi",
                    "status": "ESTIMATE",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                },
                {
                    "date": "2023-04-18",
                    "value": 81000,
                    "unit": "mi",
                    "status": "ESTIMATE",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                },
                {
                    "date": "2023-05-02",
                    "value": 54000,
                    "unit": "mi",
                    "status": "ESTIMATE",
                    "source_ids": ["vin-demo-source"],
                    "is_demo": True,
                },
            ],
            "is_demo": True,
            "data_origin": "DEMO",
        }
