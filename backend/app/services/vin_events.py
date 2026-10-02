"""Conservative deduplication: mirrored pages are not additional auction events."""

from app.schemas.research_evidence import VinEvent
from app.services.knowledge_coverage import normalize_value, stable_id


def same_event(a: VinEvent, b: VinEvent) -> bool:
    if a.vin != b.vin or a.event_type != b.event_type:
        return False
    if a.event_date != b.event_date:
        return False  # A relisted lot on a different day is a different event.
    if a.lot_id and b.lot_id and a.auction and b.auction:
        return (normalize_value(a.lot_id), normalize_value(a.auction)) == (
            normalize_value(b.lot_id),
            normalize_value(b.auction),
        )
    # No identity deduced merely from equal damage or equal dates.
    return bool(
        a.event_date
        and a.auction
        and a.location
        and a.odometer is not None
        and all(
            getattr(a, k) == getattr(b, k)
            for k in ("auction", "location", "odometer", "odometer_unit", "title")
        )
    )


def deduplicate_events(events: list[VinEvent]) -> tuple[list[VinEvent], dict[str, str]]:
    kept: list[VinEvent] = []
    aliases = {}
    for supplied in events:
        item = supplied.model_copy(deep=True)
        match = next((e for e in kept if same_event(e, item)), None)
        if match is None:
            item.id = "event-" + stable_id(
                [
                    item.vin,
                    item.event_type,
                    item.event_date,
                    item.auction,
                    item.lot_id,
                    item.location if not item.lot_id else None,
                    item.id if not (item.lot_id and item.auction) else None,
                ]
            )
            aliases[supplied.id] = item.id
            kept.append(item)
            continue
        aliases[supplied.id] = match.id
        match.source_ids = sorted(set(match.source_ids + item.source_ids))
        match.provenance.extend(p for p in item.provenance if p not in match.provenance)
        for field in (
            "location",
            "odometer",
            "odometer_unit",
            "odometer_status",
            "title",
            "primary_damage",
            "secondary_damage",
            "loss_type",
            "sale_price",
            "currency",
            "seller_type",
        ):
            a, b = getattr(match, field), getattr(item, field)
            if field in match.conflicts:
                if b is not None and b not in match.conflicts[field]:
                    match.conflicts[field].append(b)
            elif a is None:
                setattr(match, field, b)
            elif b is not None and a != b:
                match.conflicts[field] = [a, b]
                setattr(match, field, None)
        # Never display a number paired with a disputed unit or currency.
        for number, unit in (("odometer", "odometer_unit"), ("sale_price", "currency")):
            if unit in match.conflicts and getattr(match, number) is not None:
                match.conflicts.setdefault(number, [getattr(match, number)])
                setattr(match, number, None)
    return kept, aliases
