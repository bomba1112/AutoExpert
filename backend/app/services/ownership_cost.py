"""Decimal calendar/price calculations from published scoped evidence, never network calls."""

from __future__ import annotations

import calendar
import hashlib
import json
from datetime import date, timedelta
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from app.schemas.verified_ownership import EnergyPrice, MaintenanceOperation, OwnershipScenario
from app.services.ownership_evidence import available, view

RULE_VERSION = "az-ownership-1.0"
D = Decimal


def report_section(snapshot, language):
    from app.schemas.paid_report import PaidReportSection, ReportParagraph, ReportRow

    az = language == "az"
    section = PaidReportSection(
        key="ownership_evidence",
        title="İstifadə xərcləri · AZ" if az else "Стоимость владения · AZ",
        paragraphs=[
            ReportParagraph(
                text=(
                    "Hesab mənbələrin və ssenarinin saxlanmış nüsxəsinə əsaslanır. "
                    "Naməlum məbləğ sıfır deyil."
                    if az
                    else "Расчёт основан на сохранённом снимке источников и сценария. "
                    "Неизвестная сумма не равна нулю."
                )
            )
        ],
    )
    for key, ru, az_label in [
        ("energy", "Энергия", "Enerji"),
        ("scheduled_service", "Плановое ТО", "Planlı xidmət"),
        ("operating_total", "Эксплуатация", "İstismar"),
        ("operating_known_subtotal", "Известная часть", "Məlum hissə"),
        ("purchase_separate", "Покупка отдельно", "Alış ayrıca"),
        ("depreciation", "Потеря стоимости", "Dəyər itkisi"),
        ("repair_reserve_separate", "Резерв отдельно", "Ehtiyat ayrıca"),
        ("ownership_total", "Полная стоимость", "Tam xərc"),
    ]:
        section.rows.append(
            ReportRow(
                key=key,
                label=az_label if az else ru,
                value=(snapshot[key] + " AZN") if snapshot[key] is not None else "—",
            )
        )
    for source in snapshot["evidence"]:
        section.paragraphs.append(
            ReportParagraph(text=(source["source_url"] + " · " + source["locator"]))
        )
    if snapshot["missing"]:
        section.paragraphs.append(
            ReportParagraph(
                text=(
                    "Hesab qisməndir: xidmət, hissə, iş və digər məbləğlər üzrə boşluqlar var."
                    if az
                    else "Расчёт частичный: есть пробелы в обслуживании, деталях, "
                    "работе или других статьях."
                )
            )
        )
    return section


def money(value):
    return str(value.quantize(D("0.01"), rounding=ROUND_HALF_UP)) if value is not None else None


def add_months(day, count):
    month = day.year * 12 + day.month - 1 + count
    year, month = divmod(month, 12)
    return date(year, month + 1, min(day.day, calendar.monthrange(year, month + 1)[1]))


def household_bill(tariff: EnergyPrice, kwh):
    if not tariff.tiers:
        return kwh * tariff.unit_price
    total, consumed = D(0), D(0)
    for tier in tariff.tiers:
        amount = max(D(0), min(kwh, tier.up_to_kwh or kwh) - consumed)
        total += amount * tier.unit_price
        consumed += amount
    return total


def charge_cost(tariff, grid_kwh, *, household=None, dedicated=False):
    if tariff.channel == "SUPPLIER_TO_OPERATOR":
        raise ValueError("NOT_A_CONSUMER_CHARGING_PRICE")
    if tariff.channel == "HOME" and tariff.tiers:
        if household is None:
            return None
        cost = household_bill(tariff, household + grid_kwh) - household_bill(tariff, household)
    else:
        cost = household_bill(tariff, grid_kwh)
    return cost + (tariff.fixed_monthly if dedicated else D(0))


def maintenance_calendar(operation: MaintenanceOperation, scenario: OwnershipScenario):
    """Day-level scenario; distance is uniform inside each actual calendar month."""
    if operation.schedule != scenario.schedule:
        return {"events": [], "status": "NOT_APPLICABLE"}
    if operation.schedule == "SEVERE" and not set(operation.condition_codes) & set(
        scenario.severe_conditions
    ):
        return {"events": [], "status": "NOT_APPLICABLE"}
    if operation.action in {"CONDITION", "SCENARIO_REPAIR"} or operation.rule == "CONDITION_ONLY":
        return {"events": [], "status": "NEEDS_INSPECTION"}
    history = next((h for h in scenario.history if h.operation == operation.operation), None)
    first = bool(history and history.never_serviced)
    unknown = (
        not history
        or (operation.interval_km and history.last_odometer_km is None)
        or (operation.interval_months and history.last_date is None)
    )
    if first:
        unknown = bool(operation.interval_months and not scenario.first_registration)
    events = []
    if unknown:
        if not scenario.initial_service_assumption:
            return {"events": [], "status": "HISTORY_REQUIRED"}
        last_day, last_km = scenario.start_date, scenario.current_odometer_km
        events.append(
            {
                "date": last_day.isoformat(),
                "odometer_km": str(last_km),
                "action": operation.action,
                "basis": "INITIAL_SERVICE_ASSUMPTION",
            }
        )
    elif first:
        last_day, last_km = scenario.first_registration, D(0)
    else:
        last_day, last_km = history.last_date, history.last_odometer_km
    odometer = scenario.current_odometer_km

    def due(day):
        km = (operation.first_km or operation.interval_km) if first else operation.interval_km
        months = (
            (operation.first_months or operation.interval_months)
            if first
            else operation.interval_months
        )
        return (months and day >= add_months(last_day, months)) or (
            km and odometer + D("0.00001") >= last_km + km
        )

    if not unknown and due(scenario.start_date):
        events.append(
            {
                "date": scenario.start_date.isoformat(),
                "odometer_km": str(odometer),
                "action": operation.action,
                "basis": "OVERDUE_AT_START",
            }
        )
        last_day, last_km, first = scenario.start_date, odometer, False
    for month in range(scenario.months):
        begin = add_months(scenario.start_date, month)
        end = add_months(scenario.start_date, month + 1)
        daily = scenario.monthly_km / D((end - begin).days)
        for offset in range(1, (end - begin).days + 1):
            day = begin + timedelta(days=offset)
            odometer += daily
            if due(day):
                events.append(
                    {
                        "date": day.isoformat(),
                        "odometer_km": str(odometer.quantize(D("0.1"))),
                        "action": operation.action,
                        "basis": "ASSUMED_INITIAL_HISTORY" if unknown else "PUBLISHED_SCHEDULE",
                    }
                )
                last_day, last_km, first = day, odometer, False
    return {"events": events, "status": "ESTIMATE" if unknown else "CONFIRMED_SCHEDULE_SCENARIO"}


def package_cost(required_quantity, package_quantity, package_price, additional_cost):
    if additional_cost is None:
        return None
    packages = (required_quantity / package_quantity).to_integral_value(rounding=ROUND_CEILING)
    return packages * package_price + additional_cost


def comparable_prices(rows, *, part_number, brand, unit, region, at, max_age_days=30):
    offers = {}
    for row in rows:
        p, data = row.payload, row.payload["data"]
        age = (at - date.fromisoformat(p["observed_at"][:10])).days
        if p["verification"] != "CONFIRMED" or not 0 <= age <= max_age_days:
            continue
        if (data["part_number"], data["brand"], data["unit"], data["region"]) != (
            part_number,
            brand,
            unit,
            region,
        ):
            continue
        if (
            data["condition"] != "NEW"
            or data["offer_type"] != "EXACT"
            or data["available"] is not True
        ):
            continue
        key = (data["seller_id"], data["original_offer_id"])
        offers[key] = row
    prices = sorted(
        D(r.payload["data"]["package_price"]) / D(r.payload["data"]["package_quantity"])
        for r in offers.values()
    )
    sellers = {r.payload["data"]["seller_id"] for r in offers.values()}
    # One equal-weight representative per seller prevents reposts skewing a market estimate.
    per_seller = {}
    for row in offers.values():
        d = row.payload["data"]
        per_seller.setdefault(d["seller_id"], []).append(
            D(d["package_price"]) / D(d["package_quantity"])
        )
    representatives = sorted(sum(p) / len(p) for p in per_seller.values())
    median = None
    if len(sellers) >= 3:
        n = len(representatives)
        median = (representatives[(n - 1) // 2] + representatives[n // 2]) / 2
    return {
        "observations": len(offers),
        "unique_sellers": len(sellers),
        "min": money(min(prices)) if prices else None,
        "max": money(max(prices)) if prices else None,
        "median": money(median),
        "status": "COMPARABLE_SAMPLE" if len(sellers) >= 3 else "SINGLE_OR_SMALL_SAMPLE",
        "method": (
            "same part/brand/new/unit/region; fresh available exact prices; "
            "seller mean then median; no hidden outlier deletion"
        ),
    }


def calculate(db, variant, catalog, scenario: OwnershipScenario, *, production_safe=False):
    rows = available(db, variant_id=variant.id, production_safe=production_safe)
    by_id = {r.id: r for r in rows}
    used = {}
    tariff_ids = {}
    energy_lines = {}
    missing = []
    warnings = [
        "CURRENT_PRICE_HELD_AFTER_LAST_KNOWN_EFFECTIVE_DATE",
        "SOURCE_CONSUMPTION_NOT_REAL_WORLD_GUARANTEE",
    ]
    facts = catalog["facts"]

    def fact(key, allow_zero=False):
        f = facts.get(key, {})
        unit = "L/100km" if key in {"fuel_combined", "electric_mode_fuel"} else "kWh/100km"
        if f.get("status") != "CONFIRMED" or f.get("unit") != unit:
            return None
        try:
            value = D(str(f["value"]))
            return value if value.is_finite() and (value > 0 or allow_zero and value == 0) else None
        except Exception:
            return None

    def price(energy, channel, day, selected_id=None):
        eligible = [
            r
            for r in rows
            if r.kind == "ENERGY_PRICE"
            and r.payload["verification"] == "CONFIRMED"
            and r.payload["data"]["energy"] == energy
            and r.payload["data"]["channel"] == channel
            and r.payload["data"]["region"] in {"AZ", scenario.region}
            and r.payload["effective_from"] <= day.isoformat()
            and (not r.payload.get("effective_to") or r.payload["effective_to"] >= day.isoformat())
            and (not selected_id or r.id == selected_id)
        ]
        if not eligible:
            return None
        newest = max(r.payload["effective_from"] for r in eligible)
        eligible = [r for r in eligible if r.payload["effective_from"] == newest]
        if len({json.dumps(r.payload["data"], sort_keys=True) for r in eligible}) > 1:
            missing.append("CONFLICTING_ENERGY_PRICES")
            return None
        row = eligible[0]
        used[row.id] = view(row)
        tariff = EnergyPrice.model_validate(row.payload["data"])
        tariff_ids[id(tariff)] = row.id
        return tariff

    def energy_line(tariff, quantity, amount, month, day):
        revision = tariff_ids[id(tariff)]
        key = (month, revision)
        line = energy_lines.setdefault(
            key,
            {
                "month": month,
                "source_revision_id": revision,
                "energy": tariff.energy,
                "channel": tariff.channel,
                "unit": tariff.unit,
                "unit_price": str(tariff.unit_price) if tariff.unit_price is not None else None,
                "tariff": tariff.model_dump(mode="json"),
                "quantity": D(0),
                "amount": D(0),
                "from": day.isoformat(),
                "to": day.isoformat(),
            },
        )
        line["quantity"] += quantity
        line["amount"] += amount
        line["to"] = day.isoformat()
        return amount

    powertrain = facts.get("powertrain", {}).get("value")
    electric_share = (
        D(1)
        if powertrain == "BEV"
        else D(0)
        if powertrain in {"ICE", "HEV", "MHEV", "COMBUSTION_UNSPECIFIED"}
        else None
    )
    if powertrain in {"PHEV", "EREV"}:
        electric_share = scenario.electric_distance_share
    fuel, electric = fact("fuel_combined"), fact("electricity_combined")
    energy_total = D(0)
    energy_known = False
    energy_complete = True
    monthly = []
    for month in range(scenario.months):
        day = add_months(scenario.start_date, month)
        end = add_months(scenario.start_date, month + 1)
        days = (end - day).days
        amount = D(0)
        month_known = False
        month_complete = True
        if electric_share is None:
            missing.append(
                "PHEV_MODE_SHARE_REQUIRED"
                if powertrain in {"PHEV", "EREV"}
                else "POWERTRAIN_COST_MODEL_UNSUPPORTED"
            )
            energy_complete = False
            monthly.append({"month": month + 1, "energy": None})
            continue
        if electric_share < 1:
            for offset in range(days):
                tariff = price(
                    scenario.fuel_energy,
                    "RETAIL",
                    day + timedelta(days=offset),
                    scenario.fuel_price_revision_id,
                )
                if fuel is None or tariff is None or tariff.unit_price is None:
                    missing.append("FUEL_GRADE_PRICE_OR_CONSUMPTION_REQUIRED")
                    energy_complete = month_complete = False
                else:
                    month_known = True
                    quantity = scenario.monthly_km / days * (1 - electric_share) * fuel / 100
                    amount += energy_line(
                        tariff,
                        quantity,
                        quantity * tariff.unit_price,
                        month + 1,
                        day + timedelta(days=offset),
                    )
        if electric_share > 0:
            if powertrain in {"PHEV", "EREV"}:
                blended = fact("electric_mode_fuel", allow_zero=True)
                if blended is None:
                    energy_complete = month_complete = False
                    missing.append("ELECTRIC_MODE_GASOLINE_COMPONENT_REQUIRED")
                elif blended > 0:
                    for offset in range(days):
                        tariff = price(
                            scenario.fuel_energy,
                            "RETAIL",
                            day + timedelta(days=offset),
                            scenario.fuel_price_revision_id,
                        )
                        if tariff is None or tariff.unit_price is None:
                            energy_complete = month_complete = False
                            missing.append("FUEL_GRADE_PRICE_OR_CONSUMPTION_REQUIRED")
                        else:
                            month_known = True
                            quantity = scenario.monthly_km / days * electric_share * blended / 100
                            amount += energy_line(
                                tariff,
                                quantity,
                                quantity * tariff.unit_price,
                                month + 1,
                                day + timedelta(days=offset),
                            )
            grid_quantity = (
                scenario.monthly_km * electric_share * electric / 100
                if electric is not None
                else None
            )
            if scenario.consumption_side == "BATTERY":
                if scenario.charging_loss_fraction is None:
                    grid_quantity = None
                elif grid_quantity is not None:
                    grid_quantity /= 1 - scenario.charging_loss_fraction
            elif scenario.consumption_side == "UNKNOWN":
                grid_quantity = None
            elif scenario.charging_loss_fraction:
                warnings.append("GRID_CONSUMPTION_ALREADY_INCLUDES_LOSSES")
            if grid_quantity is None:
                missing.append("ELECTRICITY_CONSUMPTION_SIDE_OR_LOSS_REQUIRED")
                energy_complete = month_complete = False
            else:
                for channel, share, selected in [
                    ("HOME", scenario.home_share, scenario.home_tariff_revision_id),
                    (
                        scenario.public_channel,
                        1 - scenario.home_share,
                        scenario.public_tariff_revision_id,
                    ),
                ]:
                    if share == 0:
                        continue
                    tariff = price("ELECTRICITY", channel, day, selected)
                    daily_tariffs = [
                        price("ELECTRICITY", channel, day + timedelta(days=i), selected)
                        for i in range(days)
                    ]
                    changed = any(t != tariff for t in daily_tariffs)
                    cost = (
                        charge_cost(
                            tariff,
                            grid_quantity * share,
                            household=scenario.household_monthly_kwh,
                            dedicated=scenario.new_dedicated_meter and channel == "HOME",
                        )
                        if tariff
                        else None
                    )
                    if changed and channel == "HOME":
                        cost = None
                        missing.append("HOME_TARIFF_CHANGE_BILLING_ALLOCATION_REQUIRED")
                    elif channel != "HOME":
                        cost = (
                            sum(charge_cost(t, grid_quantity * share / days) for t in daily_tariffs)
                            if all(daily_tariffs)
                            else None
                        )
                    if cost is None:
                        missing.append("CHARGING_TARIFF_OR_HOUSEHOLD_BASE_REQUIRED")
                        energy_complete = month_complete = False
                    else:
                        month_known = True
                        amount += cost
                        if channel == "HOME":
                            energy_line(tariff, grid_quantity * share, cost, month + 1, day)
                        else:
                            for offset, daily_tariff in enumerate(daily_tariffs):
                                quantity = grid_quantity * share / days
                                energy_line(
                                    daily_tariff,
                                    quantity,
                                    charge_cost(daily_tariff, quantity),
                                    month + 1,
                                    day + timedelta(days=offset),
                                )
        energy_total += amount
        energy_known = energy_known or month_known
        monthly.append(
            {
                "month": month + 1,
                "date": day.isoformat(),
                "energy_known": money(amount) if month_known or month_complete else None,
                "status": "ESTIMATE" if month_complete else "PARTIAL",
            }
        )

    operations, service_total, service_complete = [], D(0), True
    service_known = False
    paid_packages, paid_overlap = set(), set()
    schedules = [
        r
        for r in rows
        if r.kind == "MAINTENANCE"
        and r.payload["verification"] == "CONFIRMED"
        and r.payload["effective_from"] <= scenario.start_date.isoformat()
        and (
            not r.payload.get("effective_to")
            or r.payload["effective_to"] >= scenario.start_date.isoformat()
        )
    ]
    if not schedules:
        missing.append("MAINTENANCE_SCHEDULE_NOT_RESEARCHED")
        service_complete = False
    if (
        facts.get("maintenance_coverage", {}).get("value") != "COMPLETE"
        or facts.get("maintenance_coverage", {}).get("status") != "CONFIRMED"
    ):
        missing.append("MAINTENANCE_COVERAGE_INCOMPLETE")
        service_complete = False
    seen_operations = set()
    for row in schedules:
        op = MaintenanceOperation.model_validate(row.payload["data"])
        plan = maintenance_calendar(op, scenario)
        if plan["status"] == "NOT_APPLICABLE":
            continue
        if op.operation in seen_operations:
            missing.append("CONFLICTING_MAINTENANCE_SCHEDULE:" + op.operation)
            service_complete = False
            continue
        seen_operations.add(op.operation)
        used[row.id] = view(row)
        if plan["status"] in {"HISTORY_REQUIRED", "NEEDS_INSPECTION"}:
            service_complete = False
            missing.append(plan["status"] + ":" + op.operation)
        for event in plan["events"]:
            parts_total, labor_total = D(0), None
            material_lines = []
            parts_known = D(0)
            any_part_known = not op.materials
            selected_labor = [
                by_id[i]
                for i in scenario.selected_labor_quotes
                if i in by_id
                and by_id[i].kind == "LABOR"
                and op.operation
                in (
                    [by_id[i].payload["data"]["operation"]]
                    + by_id[i].payload["data"]["included_operations"]
                )
            ]
            quote = selected_labor[0] if len(selected_labor) == 1 else None
            covered_materials = []
            if quote:
                q = quote.payload["data"]
                age = (
                    scenario.start_date - date.fromisoformat(quote.payload["observed_at"][:10])
                ).days
                if (
                    q["region"] == scenario.region
                    and quote.payload["verification"] == "CONFIRMED"
                    and 0 <= age <= 30
                    and q["price_min"] == q["price_max"]
                    and (q["unit"] != "HOUR" or q.get("hours"))
                ):
                    labor_total = D(q["price_min"]) * (D(q["hours"]) if q["unit"] == "HOUR" else 1)
                    covered_materials = q["included_materials"]
                    used[quote.id] = view(quote)
                    package_key = (quote.id, event["date"])
                    overlap_key = (q.get("overlap_group"), event["date"])
                    if package_key in paid_packages:
                        labor_total = D(0)
                    elif q.get("overlap_group") and overlap_key in paid_overlap:
                        labor_total = None
                        missing.append("OVERLAPPING_LABOR_REQUIRES_COMBINED_QUOTE")
                    else:
                        paid_packages.add(package_key)
                        paid_overlap.add(overlap_key)
            for material in op.materials:
                if material.key in covered_materials:
                    any_part_known = True
                    continue
                fitments = [
                    r
                    for r in rows
                    if r.kind == "FITMENT"
                    and r.payload["verification"] == "CONFIRMED"
                    and r.payload["data"]["material_key"] == material.key
                    and r.payload["data"]["relationship"] != "SELLER_CLAIM"
                ]
                offers = []
                for fit in fitments:
                    f = fit.payload["data"]
                    # Additional production/aggregate constraints require explicit resolution.
                    if f.get("production_from") or f.get("production_to") or f.get("constraints"):
                        continue
                    for pid in scenario.selected_part_prices:
                        p = by_id.get(pid)
                        if not p or p.kind != "PART_PRICE":
                            continue
                        sample = comparable_prices(
                            [p],
                            part_number=f["part_number"],
                            brand=f["brand"],
                            unit=material.unit,
                            region=scenario.region,
                            at=scenario.start_date,
                        )
                        if sample["observations"]:
                            offers.append((fit, p))
                if len(offers) != 1:
                    parts_total = None
                    missing.append("EXACT_FITMENT_PRICE_REQUIRED:" + material.key)
                    continue
                fit, p = offers[0]
                d = p.payload["data"]
                cost = package_cost(
                    material.quantity,
                    D(d["package_quantity"]),
                    D(d["package_price"]),
                    D(d["additional_cost"]) if d.get("additional_cost") is not None else None,
                )
                if cost is not None:
                    parts_known += cost
                    any_part_known = True
                used[fit.id], used[p.id] = view(fit), view(p)
                material_lines.append(
                    {
                        "material": material.key,
                        "required_quantity": str(material.quantity),
                        "unit": material.unit,
                        "package_quantity": d["package_quantity"],
                        "packages": str(
                            (material.quantity / D(d["package_quantity"])).to_integral_value(
                                rounding=ROUND_CEILING
                            )
                        ),
                        "package_price": d["package_price"],
                        "additional_cost": d["additional_cost"],
                        "amount": money(cost),
                        "fitment_revision_id": fit.id,
                        "price_revision_id": p.id,
                    }
                )
                parts_total = (
                    parts_total + cost if parts_total is not None and cost is not None else None
                )
            if labor_total is None or parts_total is None:
                service_complete = False
            if labor_total is None:
                missing.append("LABOR_QUOTE_REQUIRED:" + op.operation)
            known = parts_known + (labor_total or D(0))
            service_known = service_known or any_part_known or labor_total is not None
            service_total += known
            operations.append(
                {
                    **event,
                    "operation": op.operation,
                    "labels": op.labels,
                    "parts": money(parts_total),
                    "labor": money(labor_total),
                    "known_subtotal": money(known)
                    if any_part_known or labor_total is not None
                    else None,
                    "source_revision_id": row.id,
                    "materials": material_lines,
                    "labor_revision_id": quote.id if quote and quote.id in used else None,
                }
            )
    depreciation = (
        scenario.purchase - scenario.resale
        if scenario.purchase is not None and scenario.resale is not None
        else None
    )
    if depreciation is None:
        missing.append("RESALE_OR_PURCHASE_ASSUMPTION_REQUIRED")
    if scenario.other is None:
        missing.append("OTHER_COST_SCOPE_UNSPECIFIED")
    operating = energy_total + service_total + (scenario.other or D(0))
    complete = energy_complete and service_complete and scenario.other is not None
    snapshot = {
        "rules_version": RULE_VERSION,
        "knowledge_revision": variant.published_revision_id,
        "vehicle": {
            k: catalog.get(k)
            for k in (
                "make",
                "model",
                "model_year",
                "original_market",
                "generation",
                "configuration",
                "source_url",
                "source_date",
                "source_registry_id",
            )
        },
        "catalog_facts": facts,
        "scenario": scenario.model_dump(mode="json"),
        "price_policy": "DATED_FUEL_DAILY; ELECTRICITY_BILLING_PERIOD; LAST_KNOWN_PRICE_FORECAST",
        "rounding": "Decimal ROUND_HALF_UP 0.01 AZN; round after summing unrounded values",
        "currency": "AZN",
        "status": "COMPLETE" if complete and depreciation is not None else "PARTIAL",
        "energy": money(energy_total) if energy_complete else None,
        "energy_known_subtotal": money(energy_total) if energy_known or energy_complete else None,
        "scheduled_service": money(service_total) if service_complete else None,
        "service_known_subtotal": money(service_total)
        if service_known or service_complete
        else None,
        "operating_total": money(operating) if complete else None,
        "operating_known_subtotal": money(operating)
        if energy_known or service_known or complete or scenario.other is not None
        else None,
        "purchase_separate": money(scenario.purchase),
        "depreciation": money(depreciation),
        "ownership_total": money(operating + depreciation)
        if complete and depreciation is not None
        else None,
        "repair_reserve_separate": money(scenario.repair_reserve),
        "operations": operations,
        "monthly": monthly,
        "energy_breakdown": [
            {
                **line,
                "quantity": str(line["quantity"]),
                "amount": money(line["amount"]),
                "unrounded_amount": str(line["amount"]),
            }
            for line in energy_lines.values()
        ],
        "evidence": [used[key] for key in sorted(used)],
        "missing": sorted(set(missing)),
        "warnings": sorted(set(warnings)),
    }
    snapshot["scenario_id"] = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    return snapshot
