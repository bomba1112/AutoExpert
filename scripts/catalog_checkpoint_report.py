"""Read-only, configuration-level checkpoint tables from the actual published catalogue."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

from app.services.catalog_verification import catalog_excluded

REPORT_FORMAT = "vehicle-lists-first-v1"
START = "<!-- BEGIN VEHICLE CATALOG TABLES -->"
END = "<!-- END VEHICLE CATALOG TABLES -->"


def fact(c, name):
    return c.get("facts", {}).get(name, {}).get("value")


def year_ranges(years):
    """Compress only adjacent model years, never manufacture a gap year."""
    runs = []
    for year in sorted(set(years)):
        if runs and year == runs[-1][-1] + 1:
            runs[-1].append(year)
        else:
            runs.append([year])
    return ", ".join(str(r[0]) if len(r) == 1 else f"{r[0]}–{r[-1]}" for r in runs)


def scalar_changes(previous, current):
    changes = []
    for name in ("make", "model", "generation", "generation_code", "facelift", "original_market"):
        if previous.get(name) != current.get(name):
            changes.append(name)
    old_facts, new_facts = previous.get("facts", {}), current.get("facts", {})
    for name in sorted(old_facts.keys() | new_facts.keys()):
        old = {k: old_facts.get(name, {}).get(k) for k in ("value", "unit", "status")}
        new = {k: new_facts.get(name, {}).get(k) for k in ("value", "unit", "status")}
        if old != new:
            changes.append(name)
    return changes


def record_entry(variant, c, status, changes=()):
    engine = str(fact(c, "engine_description") or "UNKNOWN")
    for name in ("engine_code", "engine_family", "powertrain", "fuel", "power_hp", "trim"):
        f = c.get("facts", {}).get(name, {})
        if f.get("status") == "CONFIRMED" and f.get("value") not in (None, "", "UNKNOWN"):
            engine += f"; {name}={f['value']}"
    transmission = str(fact(c, "transmission_description") or "UNKNOWN")
    if c.get("facts", {}).get("transmission_code", {}).get("status") == "CONFIRMED" and fact(
        c, "transmission_code"
    ):
        transmission += f"; code={fact(c, 'transmission_code')}"
    generation = str(c.get("generation") or c.get("generation_code") or "UNKNOWN")
    code = c.get("generation_code")
    if code and code not in generation:
        generation += f" ({code})"
    if c.get("facelift"):
        generation += "; " + c["facelift"]
    seats = c.get("facts", {}).get("seats", {})
    confirmed_seats = seats.get("value") if seats.get("status") == "CONFIRMED" else None
    return {
        "make": c["make"],
        "model": c["model"],
        "generation": generation,
        "market": c["original_market"],
        "model_year": c["model_year"],
        "engine": engine,
        "transmission": transmission,
        "drivetrain": fact(c, "drivetrain") or "UNKNOWN",
        "body": fact(c, "body") or "UNKNOWN",
        "seats": confirmed_seats,
        "status": status,
        "changed_fields": list(changes),
        "catalog_key": variant.catalog_key,
        "variant_id": variant.id,
    }


def group_entries(entries, make_order):
    groups = {}
    for row in entries:
        fields = {
            k: v for k, v in row.items() if k not in {"model_year", "catalog_key", "variant_id"}
        }
        signature = json.dumps(fields, sort_keys=True, ensure_ascii=False)
        group = groups.setdefault(signature, {**fields, "members": []})
        group["members"].append({k: row[k] for k in ("model_year", "catalog_key", "variant_id")})
    result = []
    for group in groups.values():
        group["members"].sort(key=lambda x: (x["model_year"], x["catalog_key"]))
        group["model_years"] = sorted({r["model_year"] for r in group["members"]})
        group["configuration_count"] = len(group["members"])
        group["counts_by_model_year"] = dict(
            sorted(Counter(r["model_year"] for r in group["members"]).items())
        )
        result.append(group)
    result.sort(
        key=lambda r: (
            make_order.index(r["make"]) if r["make"] in make_order else len(make_order),
            r["make"],
            r["model"],
            r["generation"],
            r["engine"],
            r["transmission"],
            r["drivetrain"],
            r["body"],
            str(r["seats"]),
            r["status"],
            r["model_years"],
        )
    )
    return result


def build_report(
    targets, variants, strict_rows, baseline, make_order, base_rows=None, enrichment_keys=()
):
    # Select only catalogue fields; never export users, accounts, sessions or reviewer metadata.
    with sqlite3.connect(Path(baseline).resolve().as_uri() + "?mode=ro", uri=True) as before:
        previous = {
            key: json.loads(spec).get("catalog", {})
            for key, spec in before.execute(
                "SELECT catalog_key, specifications FROM vehicle_variants "
                "WHERE catalog_key IS NOT NULL"
            )
        }
    strict_keys = {v.catalog_key for v, _ in strict_rows}
    from app.services.catalog_verification import us_catalog_with_confirmed_seating as us_catalog_ready

    enrichment_keys = set(enrichment_keys)
    delta_keys = list(targets) + sorted(enrichment_keys - set(targets))
    delta = []
    for key in delta_keys:
        v = variants[key]
        c = v.specifications["catalog"]
        prior = previous.get(key)
        changes = scalar_changes(prior, c) if prior else []
        action = "ADDED" if prior is None else "CHANGED" if changes else "EVIDENCE_REFRESH"
        if catalog_excluded(c):
            availability = "EXCLUDED"
        elif key in strict_keys:
            availability = (
                "ENTERED_STRICT_SCOPED"
                if prior and not us_catalog_ready(prior)
                else "STRICT_SCOPED"
            )
        else:
            availability = "NOT_IN_STRICT_OUTPUT"
        delta.append(record_entry(v, c, action + " / " + availability, changes))
    cumulative = [record_entry(v, c, "AVAILABLE_SCOPED") for v, c in strict_rows]
    grouped_delta = group_entries(delta, make_order)
    grouped_strict = group_entries(cumulative, make_order)
    for grouped, expected in ((grouped_delta, set(delta_keys)), (grouped_strict, strict_keys)):
        members = [r["catalog_key"] for group in grouped for r in group["members"]]
        assert len(members) == len(set(members)) and set(members) == expected
    report = {
        "format": REPORT_FORMAT,
        "delta_from_previous_batch": grouped_delta,
        "cumulative_strict_output_catalog": grouped_strict,
        "reconciliation": {
            "status": "PASS",
            "delta_configuration_count": len(delta),
            "new_batch_target_configuration_count": len(targets),
            "existing_configuration_enrichment_count": len(enrichment_keys - set(targets)),
            "strict_output_configuration_count": len(cumulative),
            "delta_covers_every_batch_target_once": True,
            "delta_covers_every_enrichment_target_once": True,
            "cumulative_equals_active_us_rows": True,
        },
    }
    if base_rows is not None:
        conditional = [
            record_entry(v, c, "AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN")
            for v, c in base_rows
            if v.catalog_key not in strict_keys
        ]
        report["cumulative_conditional_output_catalog"] = group_entries(conditional, make_order)
        report["reconciliation"].update(
            conditional_configuration_count=len(conditional),
            ordinary_search_base_configuration_count=len(base_rows),
            base_equals_strict_plus_conditional=(
                len(base_rows) == len(cumulative) + len(conditional)
            ),
        )
        assert report["reconciliation"]["base_equals_strict_plus_conditional"]
    return report


def cell(value):
    return str(value if value is not None else "UNKNOWN").replace("|", "\\|").replace("\n", " ")


def table(rows):
    lines = [
        "| Make | Model | Generation | USA market | Model years | Engine | Transmission "
        "| Drivetrain | Body | Seats | Configuration count | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---:|---|",
    ]
    for row in rows:
        status = row["status"]
        if row["changed_fields"]:
            status += "; changed: " + ", ".join(row["changed_fields"])
        count = str(row["configuration_count"])
        if any(n > 1 for n in row["counts_by_model_year"].values()):
            count += (
                " (" + ", ".join(f"{y}: {n}" for y, n in row["counts_by_model_year"].items()) + ")"
            )
        values = [
            row["make"],
            row["model"],
            row["generation"],
            "USA" if row["market"] == "US" else row["market"],
            year_ranges(row["model_years"]),
            row["engine"],
            row["transmission"],
            row["drivetrain"],
            row["body"],
            row["seats"],
            count,
            status,
        ]
        lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    return "\n".join(lines)


def markdown(report, batch_id):
    conditional = ""
    if "cumulative_conditional_output_catalog" in report:
        conditional = "\n## Cumulative conditional-output catalog — места не подтверждены\n\n"
        conditional += (
            "Доступны в обычном поиске `US_CONFIRMED_2000`, если число мест не ограничено "
            "и все другие жёсткие условия подтверждены. UNKNOWN не проходит требование мест, "
            "бюджета или другого неизвестного поля: только отдельная группа «Требует уточнения», "
            "без первого предложения. Это доступность, а не новая верификация.\n\n"
        )
        conditional += table(report["cumulative_conditional_output_catalog"]) + "\n"
    return f"""{START}
## Delta from previous batch — {batch_id}

Полный список новых, изменённых и повторно опубликованных версий batch.
`ADDED` — новая запись; `CHANGED` — изменились факты (поля указаны в Status);
`EVIDENCE_REFRESH` — обновление ревизии/provenance без изменения значений.
`ENTERED_STRICT_SCOPED` — существующая версия впервые прошла строгий gate.
`NOT_IN_STRICT_OUTPUT` — сохранена в базовом каталоге, но недоступна в текущей строгой выдаче.
`EXCLUDED` — исключена из выдачи. Область любого статуса ограничена указанными годами и связкой.

{table(report["delta_from_previous_batch"])}

## Cumulative strict-output catalog — прежний строгий критерий с местами

Полный список из того же `active_us_rows`, который использует приложение для `US_BASE_2000`.
`AVAILABLE_SCOPED` означает доступность только указанных годов, двигателя, коробки,
привода, кузова и мест. Статус не распространяется на остальные версии модели.
Объединены только одинаково описанные версии с одинаковым статусом; перечисление лет
сохраняет разрывы. Configuration count — число опубликованных годовых записей внутри
строки, а не число машин в объявлениях. Если в одном году несколько исходных записей,
приведено распределение по годам; их точные catalog_key сохранены в catalog-tables.json.
Body и Seats добавлены, чтобы варианты кузова и 5/7 мест не смешивались.

{table(report["cumulative_strict_output_catalog"])}
{conditional}
{END}
"""


def write_tables(out, report, batch_id, checkpoint=None):
    out = Path(out)
    payload = {"batch_id": batch_id, **report}
    dump = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (out / "catalog-tables.json").write_text(dump, encoding="utf-8")
    block = markdown(report, batch_id)
    (out / "catalog-tables.md").write_text(
        f"# {batch_id}: полный состав каталога\n\n" + block,
        encoding="utf-8",
    )
    if checkpoint:
        path = Path(checkpoint)
        existing = path.read_text(encoding="utf-8")
        if START in existing:
            head, rest = existing.split(START, 1)
            _, tail = rest.split(END, 1)
            existing = head.rstrip() + "\n\n" + block + tail
        else:
            # Keep every preceding checkpoint paragraph, but place all totals after both lists.
            title, rest = existing.split("\n", 1)
            existing = title + "\n\n" + block + "\n" + rest.lstrip()
        path.write_text(existing, encoding="utf-8")
