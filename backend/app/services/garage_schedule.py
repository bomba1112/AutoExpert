# ruff: noqa: E501
"""Next service of each job for a car in the Garage (product phase, stage 2). Pure functions: the
inputs are the configuration's published schedule (us_tech_facts.maintenance, FACT and
SECONDARY_NOTE rows only), the owner's log and odometer; nothing is read from the database here.

Rules:
- conditions: the schedule of the car's conditions (SEVERE / NORMAL) when the manual states one for
  that job, else the normal one;
- an interval is km and / or months; WHICHEVER_FIRST (or no rule) -> due at whichever comes first;
- first / subsequent: the first replacement at the "first" interval, the next ones at the
  "subsequent" interval; "every" repeats;
- a job done (log) -> next = done + interval;
- "не знаю" / no record -> by the schedule from the current mileage: the next milestone of the
  schedule's grid after the current mileage (months from the in-service date when known, else from
  the date the owner answered), marked "по регламенту, не подтверждено"; the timing belt with an
  unknown history -> "check now";
- onboard systems (Oil-Life, CBS, Maintenance Minder): service when the car asks, reminder at the
  manual's maximum interval; "the car asks for service" resets the count (ONBOARD_RESET);
- engine oil: the owner's interval; the manual's values are only hints.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date

SOON_KM = 1500
SOON_DAYS = 30
DAYS_PER_MONTH = 30.44
OIL_JOBS = ("engine_oil_and_filter", "engine_oil", "oil_filter")
ONBOARD = ("OIL_LIFE_MONITOR", "CBS", "MAINTENANCE_MINDER")
CHECK_WHEN_UNKNOWN = ("timing_belt",)


@dataclass
class Reading:
    km: int
    on: date


@dataclass
class Record:
    job: str
    action: str = "REPLACE"
    status: str = "DONE"  # DONE / UNKNOWN / ONBOARD_RESET
    on: date | None = None
    km: int | None = None


@dataclass
class Interval:
    km: int | None = None
    months: int | None = None
    rule: str | None = None
    max_km: int | None = None
    max_months: int | None = None
    system: str | None = None
    item: dict | None = None

    @property
    def empty(self) -> bool:
        return not self.km and not self.months


@dataclass
class Plan:
    job: str
    action: str
    every: Interval | None = None
    first: Interval | None = None
    subsequent: Interval | None = None
    severe: bool = False
    owner_set: bool = False
    hints: list[dict] = field(default_factory=list)

    @property
    def onboard(self) -> str | None:
        for interval in (self.every, self.first, self.subsequent):
            if interval and interval.system in ONBOARD:
                return interval.system
        return None


def add_months(day: date, months: int) -> date:
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def months_between(a: date, b: date) -> float:
    return (b - a).days / DAYS_PER_MONTH


def average_monthly(readings: list[Reading]) -> int | None:
    """km per month from the first and the last reading at least 30 days apart."""
    ordered = sorted(readings, key=lambda r: (r.on, r.km))
    if len(ordered) < 2:
        return None
    first, last = ordered[0], ordered[-1]
    if (last.on - first.on).days < 30 or last.km < first.km:
        return None
    return round((last.km - first.km) / months_between(first.on, last.on))


def estimate_km(readings: list[Reading], monthly_km: int | None, today: date) -> dict:
    """The current mileage: the last reading plus the monthly average since. The owner's average
    wins over the computed one. ask: the app should ask the owner to confirm (30 days or 2 000 km
    of estimate)."""
    if not readings:
        return {"km": None, "estimated": False, "monthly_km": monthly_km, "last": None, "ask": True}
    last = max(readings, key=lambda r: (r.on, r.km))
    monthly = monthly_km or average_monthly(readings)
    days = max((today - last.on).days, 0)
    added = round((monthly or 0) * days / DAYS_PER_MONTH)
    return {"km": last.km + added, "estimated": added > 0, "monthly_km": monthly, "last": {"km": last.km, "on": last.on},
            "ask": days >= 30 or added >= 2000}


def _interval(item: dict) -> Interval:
    return Interval(km=item.get("km"), months=item.get("months"), rule=item.get("rule"), max_km=item.get("max_km"),
                    max_months=item.get("max_months"), system=item.get("system_code"), item=item)


def _tighter(a: Interval | None, b: Interval) -> Interval:
    """Of two statements of the same interval (several services / qualifiers) the more frequent."""
    if a is None:
        return b
    key = lambda i: (i.km or 10**9, i.months or 10**6)  # noqa: E731
    return b if key(b) < key(a) else a


def plans(schedule: list[dict], conditions: str) -> dict[tuple[str, str], Plan]:
    """One plan per (job, action) for the car's conditions."""
    severe = conditions == "SEVERE"
    grouped: dict[tuple[str, str], list[dict]] = {}
    for item in schedule:
        grouped.setdefault((item.get("job_key"), item.get("action_code") or "REPLACE"), []).append(item)
    out = {}
    for (job, action), items in grouped.items():
        severe_items = [i for i in items if i.get("severe")]
        chosen = severe_items if severe and severe_items else [i for i in items if not i.get("severe")] or items
        plan = Plan(job=job, action=action, severe=bool(severe and severe_items))
        for item in chosen:
            slot = {"FIRST": "first", "SUBSEQUENT": "subsequent"}.get(item.get("occurrence_code"), "every")
            setattr(plan, slot, _tighter(getattr(plan, slot), _interval(item)))
        out[(job, action)] = plan
    return out


def oil_plan(schedule_plans: dict, owner_km: int | None, owner_months: int | None, schedule: list[dict]) -> Plan:
    """The engine oil plan: the owner's interval; the manual's normal / severe values and the
    onboard system are hints."""
    hints = []
    onboard = None
    for item in schedule:
        if item.get("job_key") in OIL_JOBS and (item.get("action_code") or "REPLACE") == "REPLACE":
            hints.append(item)
            onboard = onboard or (item.get("system_code") if item.get("system_code") in ONBOARD else None)
    plan = Plan(job="engine_oil_and_filter", action="REPLACE", owner_set=bool(owner_km or owner_months), hints=hints)
    if plan.owner_set:
        maximum = next((h for h in hints if h.get("max_km") or h.get("max_months")), None)
        plan.every = Interval(km=owner_km, months=owner_months, rule="WHICHEVER_FIRST", system=onboard,
                              max_km=maximum.get("max_km") if maximum else None,
                              max_months=maximum.get("max_months") if maximum else None)
    elif onboard:
        maximum = next((h for h in hints if h.get("system_code") == onboard), {})
        plan.every = Interval(system=onboard, max_km=maximum.get("max_km"), max_months=maximum.get("max_months"))
    return plan


def _last(records: list[Record], job: str, action: str) -> Record | None:
    """The latest record of the job: a replacement also counts for an inspection of the same job."""
    fits = [r for r in records if r.job == job and (r.action == action or r.action == "REPLACE")]
    if job in OIL_JOBS:
        fits = [r for r in records if r.job in OIL_JOBS]
    done = [r for r in fits if r.status in ("DONE", "ONBOARD_RESET")]
    if done:
        return max(done, key=lambda r: (r.on or date.min, r.km or 0))
    unknown = [r for r in fits if r.status == "UNKNOWN"]
    return max(unknown, key=lambda r: (r.on or date.min)) if unknown else None


def _grid_next(current: float, first: int | None, step: int | None) -> int | None:
    """The next milestone of the schedule after the current value: first, first + step, ..."""
    start = first or step
    if not start:
        return None
    if current < start:
        return start
    if not step:
        return None  # only a first occurrence, already passed
    return start + (int((current - start) // step) + 1) * step


def due(plan: Plan, records: list[Record], current_km: int | None, today: date, *,
        in_service: date | None = None, added_on: date | None = None) -> dict:
    """The next service of one plan: next_km / next_date, what remains, status and why.
    status: OVERDUE, SOON, OK, CHECK (unknown history of a job to inspect now), ON_SIGNAL (the
    onboard system decides, no maximum), SET_INTERVAL (oil without the owner's interval), DONE (only
    a first occurrence, already done), NO_INTERVAL (the schedule states no km / months)."""
    last = _last(records, plan.job, plan.action)
    out: dict = {"job": plan.job, "action": plan.action, "severe": plan.severe, "confirmed": True, "basis": None,
                 "next_km": None, "next_date": None, "remaining_km": None, "remaining_days": None,
                 "onboard": plan.onboard, "last": None}
    if plan.job in OIL_JOBS and not plan.owner_set and not plan.onboard:
        return out | {"status": "SET_INTERVAL", "basis": "OWNER_INTERVAL_MISSING"}
    if last and last.status in ("DONE", "ONBOARD_RESET"):
        out["last"] = {"on": last.on, "km": last.km, "status": last.status}
        interval = plan.subsequent or plan.every
        if interval is None and plan.first and not plan.every:
            return out | {"status": "DONE", "basis": "FIRST_DONE"}
        if interval is None:
            return out | {"status": "NO_INTERVAL", "basis": "NO_INTERVAL"}
        km_step, month_step = _steps(interval)
        out["basis"] = "LOG"
        out["next_km"] = last.km + km_step if km_step and last.km is not None else None
        out["next_date"] = add_months(last.on, month_step) if month_step and last.on else None
    else:
        # no record or "не знаю": by the schedule from the current mileage, not confirmed
        out["confirmed"] = False
        out["basis"] = "SCHEDULE_UNCONFIRMED"
        out["last"] = {"status": "UNKNOWN"} if last else None
        if plan.job in CHECK_WHEN_UNKNOWN:
            return out | {"status": "CHECK", "basis": "UNKNOWN_CHECK_NOW"}
        first, step = plan.first or plan.every, plan.subsequent or plan.every
        if first is None and step is None:
            return out | {"status": "NO_INTERVAL", "basis": "NO_INTERVAL"}
        first_km, first_months = _steps(first) if first else (None, None)
        step_km, step_months = _steps(step) if step else (None, None)
        if current_km is not None and (first_km or step_km):
            out["next_km"] = _grid_next(current_km, first_km, step_km)
        if first_months or step_months:
            if in_service:
                elapsed = months_between(in_service, today)
                milestone = _grid_next(elapsed, first_months, step_months)
                out["next_date"] = add_months(in_service, milestone) if milestone is not None else None
            else:
                base = (last.on if last and last.on else None) or added_on or today
                out["next_date"] = add_months(base, step_months or first_months)
        if out["next_km"] is None and out["next_date"] is None:
            if plan.onboard:
                return out | {"status": "ON_SIGNAL"}  # the onboard system decides; no maximum stated
            return out | {"status": "CHECK", "basis": "FIRST_PASSED_UNKNOWN"}
    if out["next_km"] is None and out["next_date"] is None:
        status = "ON_SIGNAL" if plan.onboard else "NO_INTERVAL"
        return out | {"status": status}
    if current_km is not None and out["next_km"] is not None:
        out["remaining_km"] = out["next_km"] - current_km
    if out["next_date"] is not None:
        out["remaining_days"] = (out["next_date"] - today).days
    km_left, days_left = out["remaining_km"], out["remaining_days"]
    if (km_left is not None and km_left <= 0) or (days_left is not None and days_left <= 0):
        out["status"] = "OVERDUE"
    elif (km_left is not None and km_left <= SOON_KM) or (days_left is not None and days_left <= SOON_DAYS):
        out["status"] = "SOON"
    else:
        out["status"] = "OK"
    return out


def _steps(interval: Interval) -> tuple[int | None, int | None]:
    """km and months of an interval; an onboard system without a fixed interval counts by its
    maximum ("no later than")."""
    if interval.empty and interval.system in ONBOARD:
        return interval.max_km, interval.max_months
    return interval.km, interval.months


STATUS_ORDER = {"OVERDUE": 0, "CHECK": 1, "SOON": 2, "SET_INTERVAL": 3, "OK": 4, "ON_SIGNAL": 5, "NO_INTERVAL": 6, "DONE": 7}


def order(item: dict) -> tuple:
    km = item.get("remaining_km")
    days = item.get("remaining_days")
    soonest = min(x for x in (km / 50 if km is not None else None, days, 10**9) if x is not None)
    return STATUS_ORDER.get(item["status"], 9), soonest, item["job"]
