# ruff: noqa: E501
"""Daily check of new NHTSA recall campaigns for the cars in the garages (product phase, stage 2).

Once a day (scripts/garage_recall_job.py, or the in-process scheduler when garage_recall_job is on)
every make / model / year present in a garage is asked from NHTSA's public recalls API
(api.nhtsa.gov/recalls/recallsByVehicle). A campaign the US technical database does not have yet is
kept in garage_recall_notices as NHTSA states it (not a database fact) and goes to the feed of the
cars of that make / model / year. The database rows themselves are not changed.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import func, select

from app.models.garage import GarageRecallNotice, GarageVehicle
from app.services import garage, us_tech_facts

log = logging.getLogger("autoexpert.garage.recalls")
API = "https://api.nhtsa.gov/recalls/recallsByVehicle"
Fetch = Callable[[str, str, int], list[dict]]


def fetch_nhtsa(make: str, model: str, year: int) -> list[dict]:
    import httpx

    response = httpx.get(API, params={"make": make, "model": model, "modelYear": year}, timeout=30)
    response.raise_for_status()
    return response.json().get("results") or []


def _known_numbers(db, vehicles) -> dict[tuple, set[str]]:
    """Campaigns the database already shows for each make / model / year in the garages."""
    known: dict[tuple, set[str]] = {}
    for v in vehicles:
        data = us_tech_facts.build(db, v.configuration_key, "en") if v.configuration_key else None
        known.setdefault((v.make.lower(), v.model.lower(), v.year), set()).update(
            str(c["number"]) for c in (data or {}).get("campaigns") or [])
    return known


def run(db, fetch: Fetch = fetch_nhtsa, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    vehicles = list(db.scalars(select(GarageVehicle).where(GarageVehicle.is_demo.is_(False))))
    # our model name, and NHTSA's own name from the VIN when it differs ("3 Series" / "328i")
    targets = sorted({(v.make, name, v.year, v.model) for v in vehicles
                      for name in {v.model, ((v.vin_decode or {}).get("decode") or v.vin_decode or {}).get("model") or v.model}})
    known = _known_numbers(db, vehicles)
    found = errors = 0
    seen: set = set()
    for make, asked, year, model in targets:
        try:
            results = fetch(make, asked, year)
        except Exception as exc:  # noqa: BLE001 - one model failing must not stop the others
            log.warning("NHTSA recalls %s %s %s: %s", make, asked, year, exc)
            errors += 1
            continue
        for r in results:
            number = str(r.get("NHTSACampaignNumber") or "").strip()
            if not number or number in known.get((make.lower(), model.lower(), year), set()):
                continue
            key = (number, make.lower(), model.lower(), year)
            if key in seen:
                continue
            seen.add(key)
            exists = db.scalar(select(GarageRecallNotice).where(
                GarageRecallNotice.campaign_number == number, func.lower(GarageRecallNotice.make) == make.lower(),
                func.lower(GarageRecallNotice.model) == model.lower(), GarageRecallNotice.year == year))
            if exists:
                exists.checked_at = now
                continue
            db.add(GarageRecallNotice(campaign_number=number, make=make, model=model, year=year,
                                      component=r.get("Component"), summary=r.get("Summary"), remedy=r.get("Remedy"),
                                      report_date=r.get("ReportReceivedDate"),
                                      source_url=f"{API}?make={make}&model={asked}&modelYear={year}", checked_at=now))
            found += 1
    db.flush()
    for vehicle in vehicles:
        garage.refresh_feed(db, vehicle)
    db.commit()
    return {"models": len(targets), "new_notices": found, "errors": errors}


def start_daily(session_factory, interval_seconds: int = 86400) -> threading.Thread:
    """The in-process daily scheduler (settings.garage_recall_job)."""

    def loop():
        while True:
            try:
                with session_factory() as db:
                    log.info("garage recall check: %s", run(db))
            except Exception:  # noqa: BLE001
                log.exception("garage recall check failed")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=loop, name="garage-recalls", daemon=True)
    thread.start()
    return thread
