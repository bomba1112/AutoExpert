# ruff: noqa: E501
"""The Garage API (product phase, stage 2), behind the garage_v1 flag: on in the preview, off in
production. Every car belongs to the signed-in user."""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.models.garage import GarageFeedItem, GarageServiceRecord, GarageVehicle
from app.services import garage, garage_pdf, us_tech_facts

router = APIRouter(prefix="/garage", tags=["garage"])
Language = Literal["ru", "az", "en"]
Unit = Literal["km", "mi"]
Status = Literal["DONE", "UNKNOWN", "ONBOARD_RESET"]
Action = Literal["REPLACE", "INSPECT", "ROTATE", "ADJUST", "CLEAN"]


def _enabled() -> None:
    if not garage.enabled():
        raise HTTPException(404, "GARAGE_DISABLED")


class HistoryAnswer(BaseModel):
    job: str = Field(max_length=60)
    action: Action = "REPLACE"
    status: Status = "DONE"
    performed_on: date | None = None
    odometer: float | None = Field(default=None, ge=0, le=3_000_000)


class VehicleCreate(BaseModel):
    configuration_key: str = Field(max_length=200)
    vin: str | None = Field(default=None, max_length=17)
    nickname: str | None = Field(default=None, max_length=80)
    region: Literal["US", "AZ", "CIS"] | None = None
    odometer: float = Field(ge=0, le=3_000_000)
    unit: Unit = "km"
    read_on: date | None = None
    monthly: float | None = Field(default=None, ge=0, le=50_000)
    in_service_date: date | None = None
    history: list[HistoryAnswer] = Field(default_factory=list, max_length=40)


class VehicleUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=80)
    region: Literal["US", "AZ", "CIS"] | None = None
    conditions: Literal["NORMAL", "SEVERE"] | None = None
    monthly: float | None = Field(default=None, ge=0, le=50_000)
    oil_interval: float | None = Field(default=None, ge=0, le=100_000)
    oil_interval_months: int | None = Field(default=None, ge=0, le=60)
    in_service_date: date | None = None
    unit: Unit = "km"


class OdometerIn(BaseModel):
    value: float = Field(ge=0, le=3_000_000)
    unit: Unit = "km"
    read_on: date | None = None


class RecordIn(HistoryAnswer):
    unit: Unit = "km"
    note: str | None = Field(default=None, max_length=500)


def _vehicle(db, user, vehicle_id: str) -> GarageVehicle:
    vehicle = db.get(GarageVehicle, vehicle_id)
    if vehicle is None or vehicle.user_id != user.id:
        raise HTTPException(404, "VEHICLE_NOT_FOUND")
    return vehicle


@router.get("/vin/{vin}")
def decode_vin(vin: str, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    return garage.decode_vin(db, vin, language)


@router.get("/catalog")
def catalog(db: DBSession, user: CurrentUser) -> list[dict]:
    _enabled()
    return us_tech_facts.facets(db)


@router.get("/catalog/configurations")
def catalog_configurations(db: DBSession, user: CurrentUser, make: str = Query(max_length=100),
                           model: str = Query(max_length=100), year: int = Query(ge=1990, le=2100),
                           language: Language = "ru") -> list[dict]:
    _enabled()
    return garage.candidates(db, make, model, year, None, language)


@router.get("/vehicles")
def vehicles(db: DBSession, user: CurrentUser, language: Language = "ru") -> list[dict]:
    _enabled()
    out = []
    for v in db.scalars(select(GarageVehicle).where(GarageVehicle.user_id == user.id).order_by(GarageVehicle.created_at)):
        view = garage.overview(db, v, language)
        urgent = [s for s in view["services"] if s["status"] in ("OVERDUE", "CHECK", "SOON")]
        out.append({"id": v.id, "title": view["title"], "nickname": v.nickname, "configuration": view["configuration"],
                    "mileage": view["mileage"]["text"], "urgent": len(urgent), "recalls": len(view["recalls"]),
                    "next": urgent[0]["label"] + " — " + urgent[0]["when"] if urgent else None})
    return out


@router.post("/vehicles", status_code=201)
def create_vehicle(value: VehicleCreate, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    names = garage.configuration_names(db, value.configuration_key)
    if names is None:
        raise HTTPException(422, "CONFIGURATION_NOT_FOUND")
    region = value.region or garage.default_region(user.country_code, language)
    vehicle = GarageVehicle(user_id=user.id, configuration_key=value.configuration_key, make=names[0], model=names[1],
                            year=names[2], nickname=value.nickname, region=region,
                            conditions=garage.default_conditions(region), conditions_by_owner=False,
                            in_service_date=value.in_service_date,
                            monthly_km=garage.to_km(value.monthly, value.unit) if value.monthly else None)
    if value.vin:
        decoded = garage.vpic_local.decode(value.vin)
        vehicle.vin = decoded["vin"] if len(decoded["vin"]) == 17 else None
        vehicle.vin_decode = {k: decoded.get(k) for k in ("make", "model", "model_year", "displacement_l", "drive", "transmission",
                                                          "engine_model", "trim", "series", "database")}
    db.add(vehicle)
    db.flush()
    today = value.read_on or date.today()
    garage.add_reading(db, vehicle, garage.to_km(value.odometer, value.unit), today)
    data = us_tech_facts.build(db, value.configuration_key, language) or {}
    schedule_jobs = {m.get("job_key") for m in data.get("maintenance") or []} | set(garage.OIL_JOBS)
    for answer in value.history:
        if answer.status == "UNKNOWN" and answer.job not in schedule_jobs:
            continue  # "не знаю" about a job this car's schedule does not have (a chain engine's timing belt)
        garage.add_record(db, vehicle, answer.job, answer.action, answer.status, answer.performed_on or (today if answer.status == "UNKNOWN" else None),
                          garage.to_km(answer.odometer, value.unit))
    db.flush()
    view = garage.overview(db, vehicle, language)
    garage.refresh_feed(db, vehicle, view)
    db.commit()
    return view


@router.get("/vehicles/{vehicle_id}")
def vehicle_view(vehicle_id: str, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    vehicle = _vehicle(db, user, vehicle_id)
    view = garage.overview(db, vehicle, language)
    if garage.refresh_feed(db, vehicle, view):
        db.commit()
    return view


@router.patch("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: str, value: VehicleUpdate, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    vehicle = _vehicle(db, user, vehicle_id)
    fields = value.model_fields_set
    if "nickname" in fields:
        vehicle.nickname = value.nickname
    if "region" in fields and value.region:
        vehicle.region = value.region
        if not vehicle.conditions_by_owner:
            vehicle.conditions = garage.default_conditions(value.region)
    if "conditions" in fields and value.conditions:
        vehicle.conditions, vehicle.conditions_by_owner = value.conditions, True
    if "monthly" in fields:
        vehicle.monthly_km = garage.to_km(value.monthly, value.unit) if value.monthly else None
    if "oil_interval" in fields:
        vehicle.oil_interval_km = garage.to_km(value.oil_interval, value.unit) if value.oil_interval else None
    if "oil_interval_months" in fields:
        vehicle.oil_interval_months = value.oil_interval_months or None
    if "in_service_date" in fields:
        vehicle.in_service_date = value.in_service_date
    db.flush()
    view = garage.overview(db, vehicle, language)
    garage.refresh_feed(db, vehicle, view)
    db.commit()
    return view


@router.delete("/vehicles/{vehicle_id}", status_code=204)
def delete_vehicle(vehicle_id: str, db: DBSession, user: CurrentUser) -> Response:
    _enabled()
    db.delete(_vehicle(db, user, vehicle_id))
    db.commit()
    return Response(status_code=204)


@router.post("/vehicles/{vehicle_id}/odometer")
def odometer(vehicle_id: str, value: OdometerIn, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    vehicle = _vehicle(db, user, vehicle_id)
    garage.add_reading(db, vehicle, garage.to_km(value.value, value.unit), value.read_on or date.today())
    db.flush()
    view = garage.overview(db, vehicle, language)
    garage.refresh_feed(db, vehicle, view)
    db.commit()
    return view


@router.post("/vehicles/{vehicle_id}/records", status_code=201)
def add_record(vehicle_id: str, value: RecordIn, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    vehicle = _vehicle(db, user, vehicle_id)
    on = value.performed_on or date.today()
    garage.add_record(db, vehicle, value.job, value.action, value.status, on, garage.to_km(value.odometer, value.unit), value.note)
    db.flush()
    view = garage.overview(db, vehicle, language)
    garage.refresh_feed(db, vehicle, view)
    db.commit()
    return view


@router.post("/vehicles/{vehicle_id}/onboard-reset", status_code=201)
def onboard_reset(vehicle_id: str, value: OdometerIn, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    """The car's onboard system asked for service (Oil-Life / CBS / Maintenance Minder) and the oil
    was changed: the count starts again."""
    _enabled()
    vehicle = _vehicle(db, user, vehicle_id)
    garage.add_record(db, vehicle, "engine_oil_and_filter", "REPLACE", "ONBOARD_RESET", value.read_on or date.today(),
                      garage.to_km(value.value, value.unit))
    db.flush()
    view = garage.overview(db, vehicle, language)
    garage.refresh_feed(db, vehicle, view)
    db.commit()
    return view


@router.delete("/vehicles/{vehicle_id}/records/{record_id}")
def delete_record(vehicle_id: str, record_id: str, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    vehicle = _vehicle(db, user, vehicle_id)
    record = db.get(GarageServiceRecord, record_id)
    if record is None or record.vehicle_id != vehicle.id:
        raise HTTPException(404, "RECORD_NOT_FOUND")
    vehicle.records.remove(record)
    db.delete(record)
    db.commit()
    return garage.overview(db, vehicle, language)


@router.get("/vehicles/{vehicle_id}/service-log.pdf")
def service_log_pdf(vehicle_id: str, db: DBSession, user: CurrentUser, language: Language = "ru") -> Response:
    _enabled()
    vehicle = _vehicle(db, user, vehicle_id)
    pdf = garage_pdf.render(garage.overview(db, vehicle, language), language)
    name = f"AutoExpert_service_log_{vehicle.make}_{vehicle.model}_{vehicle.year}.pdf".replace(" ", "_")
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/feed")
def feed(db: DBSession, user: CurrentUser, language: Language = "ru") -> list[dict]:
    _enabled()
    rows = db.execute(select(GarageFeedItem, GarageVehicle).join(GarageVehicle, GarageVehicle.id == GarageFeedItem.vehicle_id)
                      .where(GarageVehicle.user_id == user.id).order_by(GarageFeedItem.created_at.desc()).limit(200))
    return [garage.feed_text(item, vehicle, language, db) for item, vehicle in rows]


@router.post("/feed/{item_id}/read")
def feed_read(item_id: str, db: DBSession, user: CurrentUser) -> dict:
    _enabled()
    item = db.get(GarageFeedItem, item_id)
    if item is None or item.vehicle.user_id != user.id:
        raise HTTPException(404, "FEED_ITEM_NOT_FOUND")
    garage.mark_read(item)
    db.commit()
    return {"ok": True}
