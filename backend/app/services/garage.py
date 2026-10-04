# ruff: noqa: E501
"""The Garage (product phase, stage 2): the owner's car under the expert's eye.

A car is bound to one configuration of the US technical database; everything the Garage says about
it comes from that configuration's published rows through us_tech_facts.build (FACT; SECONDARY_NOTE
marked; OWNER_REPORTS only as "владельцы сообщают"; HIDDEN_CONFLICT never; an empty field is left
out). The next service of each job is computed by app.services.garage_schedule from the owner's log
and odometer. Served only while enabled(): on in development / test (preview), off in production
unless AUTOEXPERT_GARAGE_V1 says otherwise.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.english import pick
from app.models.catalog import VehicleMake
from app.models.evidence import TechnicalEvidence
from app.models.garage import (
    GarageFeedItem,
    GarageOdometerReading,
    GarageRecallNotice,
    GarageServiceRecord,
    GarageVehicle,
)
from app.services import garage_push, garage_schedule, unit_display, us_tech_facts, vpic_local
from app.services.garage_schedule import OIL_JOBS, Reading, Record

MI = 1.609344
CIS = {"RU", "KZ", "BY", "UZ", "KG", "TJ", "AM", "GE", "MD", "TM", "UA"}
# the fluid and its capacity shown next to a job ("через 2 000 км ATF WS, 7,3 л")
FLUIDS = {
    "engine_oil_and_filter": (("engine_oil_viscosity", "engine_oil_specification", "engine_oil_oem_approval"), "engine_oil_capacity_l"),
    "transmission_fluid": (("transmission_fluid",), "transmission_fluid_capacity_l"),
    "engine_coolant": (("coolant", "coolant_description"), "coolant_capacity_l"),
    "brake_fluid": (("brake_fluid",), None),
    "spark_plugs": (("spark_plug",), None),
}
# jobs the app asks about when a car is added ("когда меняли?" / "не знаю")
MAIN_JOBS = ("engine_oil_and_filter", "spark_plugs", "transmission_fluid", "dct_fluid", "dual_clutch_fluid",
             "engine_coolant", "brake_fluid", "timing_belt", "engine_air_filter", "cabin_air_filter",
             "differential_fluid", "transfer_case_fluid")

T = {
    "oil": ("Моторное масло и фильтр", "Mühərrik yağı və filtr", "Engine oil and filter"),
    "unconfirmed": ("по регламенту, не подтверждено", "reqlamentə görə, təsdiqlənməyib", "per schedule, not confirmed"),
    "check_now": ("история неизвестна — рекомендуем проверить сейчас", "tarixçə məlum deyil — indi yoxlatmağı tövsiyə edirik",
                  "history unknown — we recommend a check now"),
    "timing_check": ("История ремня ГРМ неизвестна: проверьте его состояние и, если нет документов о замене, планируйте замену по регламенту.",
                     "Qazpaylama kəmərinin tarixçəsi məlum deyil: vəziyyətini yoxladın, dəyişmə sənədi yoxdursa, reqlamentə görə dəyişməni planlaşdırın.",
                     "The timing belt history is unknown: have it inspected and, without proof of replacement, plan a replacement per the schedule."),
    "set_oil": ("Задайте интервал замены масла", "Yağın dəyişmə intervalını təyin edin", "Set your oil change interval"),
    "on_signal": ("по сигналу бортовой системы", "bort sisteminin siqnalı ilə", "when the onboard system asks"),
    "no_later": ("не позже", "gec olmayaraq", "no later than"),
    "in": ("через", "sonra", "in"),
    "by": ("до", "qədər", "by"),
    "or": ("или", "və ya", "or"),
    "overdue": ("просрочено", "vaxtı keçib", "overdue"),
    "done_first": ("первая замена выполнена", "ilk dəyişmə edilib", "first replacement done"),
    "no_interval": ("интервал в руководстве не указан", "interval təlimatda göstərilməyib", "the manual states no interval"),
    "severe": ("тяжёлые условия", "ağır şərait", "severe conditions"),
    "normal": ("нормальные условия", "normal şərait", "normal conditions"),
    "severe_missing": ("в руководстве нет отдельного регламента для тяжёлых условий — показан обычный",
                       "təlimatda ağır şərait üçün ayrıca reqlament yoxdur — adi reqlament göstərilir",
                       "the manual has no separate severe schedule — the normal one is shown"),
    "no_schedule": ("Регламента ТО этой машины в нашей базе пока нет. Журнал работ и масло по вашему интервалу работают; остальные напоминания появятся вместе с регламентом.",
                    "Bu avtomobilin texniki xidmət reqlamenti hələ bazamızda yoxdur. İş jurnalı və sizin intervalınızla yağ işləyir; digər xatırlatmalar reqlamentlə birlikdə görünəcək.",
                    "We don't have this car's maintenance schedule yet. The service log and oil by your interval work; other reminders will appear with the schedule."),
    "recall_note": ("Бесплатный ремонт у дилера. Касается ли кампания именно вашей машины — проверяется по VIN.",
                    "Dilerdə pulsuz təmir. Kampaniyanın məhz sizin avtomobilə aid olub-olmadığı VIN üzrə yoxlanılır.",
                    "Free repair at a dealer. Whether the campaign covers your car is checked by VIN."),
    "recall_new": ("Новая кампания NHTSA", "Yeni NHTSA kampaniyası", "New NHTSA campaign"),
    "typical": ("обычно проявляется на пробеге", "adətən bu yürüşdə özünü göstərir", "usually shows up at"),
    "odometer_ask": ("Уточните пробег: мы оцениваем его по среднему за месяц", "Yürüşü dəqiqləşdirin: onu aylıq ortalamaya görə hesablayırıq",
                     "Please confirm the mileage: we estimate it from your monthly average"),
}
DUE_TITLE = {
    "OVERDUE": ("Пора: просрочено", "Vaxtıdır: gecikib", "Due now: overdue"),
    "SOON": ("Скоро", "Tezliklə", "Coming up"),
    "CHECK": ("Проверить", "Yoxlatmaq", "Check"),
}


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.garage_v1 is not None:
        return bool(settings.garage_v1)
    return settings.environment != "production"


def t(language: str, key: str) -> str:
    ru, az, en = T[key]
    return pick(language, ru, az, en)


# --- units and dates ---------------------------------------------------------------------------
def to_km(value: float | int | None, unit: str) -> int | None:
    if value is None:
        return None
    return round(float(value) * MI) if unit == "mi" else round(float(value))


def distance(km: int | None, language: str) -> str | None:
    if km is None:
        return None
    if language == "en":
        return unit_display.distance(km, None, language)
    return f"{km:,}".replace(",", " ") + (" km" if language == "az" else " км")


MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def day_text(day: date | None, language: str) -> str | None:
    if day is None:
        return None
    return f"{MONTHS_EN[day.month - 1]} {day.day}, {day.year}" if language == "en" else day.strftime("%d.%m.%Y")


# --- region and conditions ---------------------------------------------------------------------
def default_region(country: str | None, language: str) -> str:
    country = (country or "").upper()
    if country in ("US", "CA"):
        return "US"
    if country == "AZ":
        return "AZ"
    if country in CIS:
        return "CIS"
    return {"en": "US", "az": "AZ"}.get(language, "CIS")


def default_conditions(region: str) -> str:
    """AZ / CIS: severe by default (the owner can switch); US: normal."""
    return "NORMAL" if region == "US" else "SEVERE"


# --- binding to a configuration ----------------------------------------------------------------
def _norm(text) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def _drive(text) -> str | None:
    t_ = str(text or "").lower()
    if not t_:
        return None
    if "fwd" in t_ or "front" in t_:
        return "FWD"
    if "rwd" in t_ or "rear" in t_:
        return "RWD"
    if "awd" in t_ or "all" in t_ or "4wd" in t_ or "4x4" in t_ or "4-wheel" in t_:
        return "AWD"
    return None


def _power(decoded: dict) -> str | None:
    level = str(decoded.get("electrification") or "").lower()
    fuel = str(decoded.get("fuel") or "").lower()
    if "phev" in level or "plug-in" in level:
        return "PHEV"
    if "bev" in level or fuel == "electric":
        return "BEV"
    if "hev" in level or "hybrid" in level:
        return "HEV"
    if "diesel" in fuel:
        return "DIESEL"
    return "ICE" if fuel else None


def candidates(db, make: str, model: str | None, year: int, decoded: dict | None = None, language: str = "ru") -> list[dict]:
    """Configurations of our database for a make / model / year, narrowed by what the VIN says
    (displacement, drive, gearbox, powertrain, engine). A filter that would leave nothing is not
    applied: the owner then chooses."""
    rows = list(db.execute(us_tech_facts._catalog_query().where(
        func.lower(VehicleMake.name) == str(make).lower(), TechnicalEvidence.year_from <= year, TechnicalEvidence.year_to >= year)))
    names = {_norm(model)} | ({_norm(decoded.get("series")), _norm(decoded.get("model"))} if decoded else set())
    names.discard("")
    if names:
        exact = [r for r in rows if _norm(r[2]) in names]
        prefix = [r for r in rows if any(n.startswith(_norm(r[2])) for n in names)]
        rows = exact or prefix
    if decoded:
        def ident(row):
            return (row[0].conditions or {}).get("identity") or {}

        filters = []
        disp = vpic_local._number(decoded.get("displacement_l"))
        if disp:
            filters.append(lambda r: ident(r).get("displacement_l") is None or abs(float(ident(r)["displacement_l"]) - disp) <= 0.06)
        drive = _drive(decoded.get("drive"))
        if drive:
            filters.append(lambda r: _drive(ident(r).get("drivetrain")) in (None, drive))
        speeds = decoded.get("transmission_speeds")
        if speeds and str(speeds).isdigit():
            filters.append(lambda r: us_tech_facts._gearbox(ident(r).get("epa_transmission"))[1] in (None, int(speeds)))
        style = str(decoded.get("transmission") or "").lower()
        family = "CVT" if "continuously" in style or "cvt" in style else "DCT" if "dual" in style or "dct" in style else \
            "MANUAL" if "manual" in style and "automated" not in style else "AT" if "automatic" in style else None
        if family:
            filters.append(lambda r: us_tech_facts._gearbox(ident(r).get("epa_transmission"))[0] in (None, family))
        power = _power(decoded)
        if power:
            filters.append(lambda r: ("DIESEL" if "-diesel-" in (r[0].configuration_key or "") else str(ident(r).get("powertrain") or "").upper() or None) in (None, power))
        engine = _norm(decoded.get("engine_model"))
        if engine:
            filters.append(lambda r: not ident(r).get("engine_family_key") or _norm(ident(r)["engine_family_key"]) in engine or engine in _norm(ident(r)["engine_family_key"]))
        for keep in filters:
            narrowed = [r for r in rows if keep(r)]
            if narrowed:
                rows = narrowed
    return [{"configuration_key": row.configuration_key, "make": make_name, "model": model_name, "year": year,
             "label": us_tech_facts.configuration_label(row, language)} for row, make_name, model_name in rows]


def decode_vin(db, vin: str, language: str = "ru") -> dict:
    decoded = vpic_local.decode(vin)
    out = {"decode": decoded, "candidates": []}
    if decoded.get("make") and decoded.get("model_year"):
        out["candidates"] = candidates(db, decoded["make"], decoded.get("model"), decoded["model_year"], decoded, language)
    return out


# --- the car -----------------------------------------------------------------------------------
def readings_of(vehicle: GarageVehicle) -> list[Reading]:
    return [Reading(km=r.km, on=r.read_on) for r in vehicle.readings]


def records_of(vehicle: GarageVehicle) -> list[Record]:
    return [Record(job=r.job, action=r.action, status=r.status, on=r.performed_on, km=r.odometer_km) for r in vehicle.records]


def _fluid(categories: list[dict], job: str) -> dict | None:
    spec_keys, capacity_key = FLUIDS.get(job, ((), None))
    rows = {r["key"]: r for c in categories for r in c["rows"]}

    def first(key):
        row = rows.get(key)
        return row["values"][0] if row and row["values"] else None

    spec = next((first(k) for k in spec_keys if first(k)), None)
    capacity = first(capacity_key) if capacity_key else None
    if not spec and not capacity:
        return None
    return {"spec": spec["value"] if spec else None, "capacity": capacity["value"] if capacity else None,
            "secondary": bool((spec or {}).get("secondary") or (capacity or {}).get("secondary")),
            "sources": [v["source"] for v in (spec, capacity) if v and v.get("source")]}


def _when(item: dict, language: str) -> str:
    status = item["status"]
    if status == "SET_INTERVAL":
        return t(language, "set_oil")
    if status == "CHECK":
        return t(language, "check_now")
    if status == "DONE":
        return t(language, "done_first")
    if status == "NO_INTERVAL":
        return t(language, "no_interval")
    if status == "ON_SIGNAL":
        return t(language, "on_signal")
    if item.get("onboard"):
        limits = [x for x in (distance(item["next_km"], language) if item["next_km"] is not None else None,
                              day_text(date.fromisoformat(item["next_date"]) if isinstance(item["next_date"], str) else item["next_date"], language))
                  if x]
        overdue = f" ({t(language, 'overdue')})" if item["status"] == "OVERDUE" else ""
        return f"{t(language, 'on_signal')}; {t(language, 'no_later')} " + f" {t(language, 'or')} ".join(limits) + overdue
    parts = []
    if item["remaining_km"] is not None:
        left = item["remaining_km"]
        parts.append(f"{t(language, 'in')} {distance(left, language)}" if left > 0 else f"{t(language, 'overdue')} {distance(-left, language)}")
    if item["next_date"] is not None:
        parts.append(f"{t(language, 'by')} {day_text(item['next_date'], language)}")
    return f" {t(language, 'or')} ".join(parts)


def overview(db, vehicle: GarageVehicle, language: str, today: date | None = None) -> dict:
    today = today or date.today()
    data = us_tech_facts.build(db, vehicle.configuration_key, language) if vehicle.configuration_key else None
    schedule = (data or {}).get("maintenance") or []
    categories = (data or {}).get("categories") or []
    has_severe = any(m.get("severe") for m in schedule)
    plans = garage_schedule.plans([m for m in schedule if m.get("job_key") not in OIL_JOBS], vehicle.conditions)
    oil = garage_schedule.oil_plan(plans, vehicle.oil_interval_km, vehicle.oil_interval_months, schedule)
    mileage = garage_schedule.estimate_km(readings_of(vehicle), vehicle.monthly_km, today)
    records = records_of(vehicle)
    added_on = vehicle.created_at.date() if vehicle.created_at else today
    items = []
    for plan in [oil, *plans.values()]:
        result = garage_schedule.due(plan, records, mileage["km"], today, in_service=vehicle.in_service_date, added_on=added_on)
        source_item = (plan.every or plan.subsequent or plan.first)
        entry = (source_item.item if source_item else None) or (plan.hints[0] if plan.hints else {})
        label = t(language, "oil") if plan.job in OIL_JOBS or plan.job == "engine_oil_and_filter" else entry.get("job") or plan.job
        intervals = [i for i in (plan.first, plan.subsequent, plan.every) if i and i.item]
        result.update({
            "label": label, "action_label": entry.get("action") if plan.job not in OIL_JOBS else None,
            "when": _when(result, language),
            "interval": "; ".join(f"{i.item['occurrence'] + ': ' if i.item.get('occurrence') else ''}{i.item['interval']}"
                                  for i in intervals if i.item.get("interval")) or _owner_interval(plan, vehicle, language)
            or entry.get("system"),
            "unconfirmed_note": t(language, "unconfirmed") if not result["confirmed"]
            and result["status"] not in ("SET_INTERVAL", "ON_SIGNAL", "NO_INTERVAL") else None,
            "secondary": any(i.item.get("secondary") for i in intervals),
            "system": entry.get("system"),
            "fluid": _fluid(categories, "engine_oil_and_filter" if plan.job in OIL_JOBS else plan.job),
            "sources": [i.item["source"] for i in intervals if i.item.get("source")][:2],
            "next_date": result["next_date"].isoformat() if result["next_date"] else None,
            "last": {**result["last"], "on": result["last"]["on"].isoformat() if result["last"].get("on") else None} if result["last"] else None,
        })
        if plan.job == "timing_belt" and result["status"] == "CHECK":
            result["advice"] = t(language, "timing_check")
        if plan.job in OIL_JOBS or plan.job == "engine_oil_and_filter":
            result["owner_interval"] = {"km": vehicle.oil_interval_km, "months": vehicle.oil_interval_months}
            result["hints"] = [{"interval": h.get("interval"), "severe": h.get("severe"), "system": h.get("system"),
                                "max_interval": h.get("max_interval"), "secondary": h.get("secondary"), "source": h.get("source")}
                               for h in plan.hints if h.get("interval") or h.get("system")]
        items.append(result)
    items.sort(key=garage_schedule.order)
    recalls = _recalls(db, vehicle, data, language)
    weak = []
    for issue in (data or {}).get("weak_points") or []:
        typical = issue.get("typical_km")
        weak.append({**issue, "typical": (f"{t(language, 'typical')} {distance(typical[0], language)}"
                                          + (f"–{distance(typical[1], language)}" if typical[1] and typical[1] != typical[0] else ""))
                     if typical and typical[0] else None})
    return {
        "id": vehicle.id, "title": " ".join(str(x) for x in (vehicle.make, vehicle.model, vehicle.year)),
        "nickname": vehicle.nickname, "vin": vehicle.vin, "configuration_key": vehicle.configuration_key,
        "configuration": (data or {}).get("summary"), "generation": (data or {}).get("generation"),
        "region": vehicle.region,
        "conditions": {"value": vehicle.conditions, "by_owner": vehicle.conditions_by_owner, "severe_in_manual": has_severe,
                       "label": t(language, "severe" if vehicle.conditions == "SEVERE" else "normal"),
                       "note": t(language, "severe_missing") if vehicle.conditions == "SEVERE" and schedule and not has_severe else None},
        "mileage": {"km": mileage["km"], "text": distance(mileage["km"], language), "estimated": mileage["estimated"],
                    "monthly_km": mileage["monthly_km"], "ask": mileage["ask"],
                    "monthly_text": distance(mileage["monthly_km"], language) if mileage["monthly_km"] else None,
                    "last": {"km": mileage["last"]["km"], "on": mileage["last"]["on"].isoformat(),
                             "text": distance(mileage["last"]["km"], language)} if mileage["last"] else None},
        "in_service_date": vehicle.in_service_date.isoformat() if vehicle.in_service_date else None,
        "schedule_available": bool(schedule),
        "schedule_note": None if schedule else t(language, "no_schedule"),
        "services": items,
        "recalls": recalls,
        "weak_points": weak,
        "log": [{"id": r.id, "job": r.job, "label": _job_label(r.job, language), "action": r.action, "status": r.status,
                 "on": r.performed_on.isoformat() if r.performed_on else None, "km": r.odometer_km,
                 "km_text": distance(r.odometer_km, language), "note": r.note}
                for r in sorted(vehicle.records, key=lambda r: (r.performed_on or date.min, r.odometer_km or 0), reverse=True)],
        "main_jobs": main_jobs(schedule, language),
        "fluids": [{"job": job, "label": _job_label(job, language), **fluid} for job in FLUIDS
                   if (fluid := _fluid(categories, job))],
        "labels": (data or {}).get("labels"),
    }


def _owner_interval(plan, vehicle: GarageVehicle, language: str) -> str | None:
    if not plan.owner_set:
        return None
    text = us_tech_facts._interval(vehicle.oil_interval_km, vehicle.oil_interval_months, "WHICHEVER_FIRST", language)
    return f"{text} · {pick(language, 'ваш интервал', 'sizin intervalınız', 'your interval')}" if text else None


def _job_label(job: str, language: str) -> str:
    if job in OIL_JOBS:
        return t(language, "oil")
    pair = us_tech_facts.JOBS.get(job)
    return us_tech_facts.tr(language, pair) if pair else job.replace("_", " ")


def main_jobs(schedule: list[dict], language: str) -> list[dict]:
    """The main jobs of this car's schedule the app asks about ("когда меняли?"), oil first."""
    present = {m.get("job_key") for m in schedule if (m.get("action_code") or "REPLACE") == "REPLACE"}
    jobs = ["engine_oil_and_filter"] + [j for j in MAIN_JOBS[1:] if j in present]
    return [{"job": j, "label": _job_label(j, language)} for j in jobs]


def _recalls(db, vehicle: GarageVehicle, data: dict | None, language: str) -> list[dict]:
    out = []
    known = set()
    for c in (data or {}).get("campaigns") or []:
        known.add(str(c["number"]))
        out.append({**c, "note": t(language, "recall_note"), "origin": "DATABASE"})
    for notice in db.scalars(select(GarageRecallNotice).where(
            func.lower(GarageRecallNotice.make) == vehicle.make.lower(), func.lower(GarageRecallNotice.model) == vehicle.model.lower(),
            GarageRecallNotice.year == vehicle.year)):
        if notice.campaign_number in known:
            continue
        out.append({"number": notice.campaign_number, "component": notice.component, "summary": notice.summary,
                    "remedy": notice.remedy, "years": [notice.year, notice.year], "note": t(language, "recall_note"),
                    "origin": "NHTSA_DAILY_CHECK", "source_url": notice.source_url, "report_date": notice.report_date,
                    "label": t(language, "recall_new")})
    out.sort(key=lambda c: str(c["number"]), reverse=True)
    return out


# --- feed --------------------------------------------------------------------------------------
def refresh_feed(db, vehicle: GarageVehicle, view: dict | None = None, today: date | None = None, sender=None) -> list[GarageFeedItem]:
    """Add the notices the car needs now (each once): due / overdue / check jobs, recalls, a request
    to confirm the mileage, the oil interval to set. New items go to the push sender."""
    view = view or overview(db, vehicle, "en", today)
    today = today or date.today()
    existing = {i.key for i in vehicle.feed}
    wanted = []
    for s in view["services"]:
        if s["status"] in ("OVERDUE", "SOON"):
            wanted.append(("SERVICE_DUE", f"due:{s['job']}:{s['action']}:{s['next_km']}:{s['next_date']}",
                           {"job": s["job"], "action": s["action"], "status": s["status"], "next_km": s["next_km"],
                            "next_date": s["next_date"], "confirmed": s["confirmed"]}))
        elif s["status"] == "CHECK":
            wanted.append(("SERVICE_CHECK", f"check:{s['job']}", {"job": s["job"], "action": s["action"]}))
        elif s["status"] == "SET_INTERVAL":
            wanted.append(("OIL_INTERVAL", "oil:set", {}))
    for r in view["recalls"]:
        wanted.append(("RECALL", f"recall:{r['number']}", {"number": r["number"], "component": (r.get("original") or {}).get("component") or r.get("component"),
                                                           "origin": r.get("origin")}))
    if view["mileage"]["ask"]:
        wanted.append(("ODOMETER_ASK", f"odometer:{today:%Y-%m}", {"estimate_km": view["mileage"]["km"]}))
    added = []
    for kind, key, payload in wanted:
        if key in existing:
            continue
        item = GarageFeedItem(vehicle_id=vehicle.id, kind=kind, key=key[:200], payload=payload)
        db.add(item)
        vehicle.feed.append(item)
        added.append(item)
    if added:
        db.flush()
        garage_push.deliver(db, vehicle, added, sender)
    return added


def feed_text(item: GarageFeedItem, vehicle: GarageVehicle, language: str, db=None) -> dict:
    p = item.payload or {}
    if item.kind == "SERVICE_DUE":
        title = pick(language, *DUE_TITLE["OVERDUE" if p.get("status") == "OVERDUE" else "SOON"])
        parts = [x for x in (distance(p.get("next_km"), language),
                             day_text(date.fromisoformat(p["next_date"]), language) if p.get("next_date") else None) if x]
        body = f"{_job_label(p['job'], language)}: " + f" {t(language, 'or')} ".join(parts)
        if not p.get("confirmed"):
            body += f" ({t(language, 'unconfirmed')})"
    elif item.kind == "SERVICE_CHECK":
        title = pick(language, *DUE_TITLE["CHECK"])
        body = t(language, "timing_check") if p.get("job") == "timing_belt" else f"{_job_label(p['job'], language)}: {t(language, 'check_now')}"
    elif item.kind == "RECALL":
        title = f"Recall {p.get('number')}"
        component = p.get("component")
        if component and db is not None:
            component = us_tech_facts.Translator(db, language)("recall_component", component)
        body = (component or "") + (" — " if component else "") + t(language, "recall_note")
    elif item.kind == "ODOMETER_ASK":
        title = pick(language, "Пробег", "Yürüş", "Mileage")
        body = t(language, "odometer_ask")
    else:
        title = t(language, "set_oil")
        body = pick(language, "Подсказка — значение из руководства; решение за вами.", "İpucu — təlimatdakı dəyərdir; qərar sizindir.",
                    "The manual's value is a hint; the choice is yours.")
    return {"id": item.id, "kind": item.kind, "vehicle_id": vehicle.id, "vehicle": f"{vehicle.make} {vehicle.model} {vehicle.year}",
            "title": title, "body": body, "created_at": item.created_at.isoformat() if item.created_at else None,
            "read": item.read_at is not None}


def mark_read(item: GarageFeedItem) -> None:
    item.read_at = item.read_at or datetime.now(UTC)


# --- writing -----------------------------------------------------------------------------------
def add_reading(db, vehicle: GarageVehicle, km: int, on: date, source: str = "OWNER") -> None:
    reading = GarageOdometerReading(vehicle_id=vehicle.id, km=km, read_on=on, source=source)
    db.add(reading)
    vehicle.readings.append(reading)


def add_record(db, vehicle: GarageVehicle, job: str, action: str, status: str, on: date | None, km: int | None,
               note: str | None = None) -> GarageServiceRecord:
    record = GarageServiceRecord(vehicle_id=vehicle.id, job=job, action=action, status=status, performed_on=on,
                                 odometer_km=km, note=note)
    db.add(record)
    vehicle.records.append(record)
    if km is not None and on is not None and status != "UNKNOWN":
        add_reading(db, vehicle, km, on, "SERVICE_LOG")
    return record


def configuration_names(db, configuration_key: str) -> tuple[str, str, int] | None:
    row = db.execute(us_tech_facts._catalog_query().where(TechnicalEvidence.configuration_key == configuration_key).limit(1)).first()
    if not row:
        return None
    return row[1], row[2], row[0].year_from

