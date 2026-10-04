"""Chinese configuration catalogue: read side (rows written by cn_catalog_load)."""

from __future__ import annotations

from sqlalchemy import select

from app.models.catalog import VehicleVariant
from app.models.evidence import KnownIssue

MARKET = "CN"
KIND_COLUMN = {
    "engine": KnownIssue.engine_family_key,
    "transmission": KnownIssue.transmission_key,
    "hybrid_system": KnownIssue.hybrid_system_key,
}
KIND_RU = {"engine": "двигатель", "transmission": "коробка", "hybrid_system": "гибридная система"}


def _issue_view(issue: KnownIssue, origin: str, component: str | None = None) -> dict:
    conditions = issue.conditions or {}
    view = {
        "text": issue.description,
        "source": conditions.get("source"),
        "scope": issue.component,
        "origin": origin,
    }
    if conditions.get("more_sources"):
        view["more_sources"] = conditions["more_sources"]
    if component:
        # inherited reports carry the component, not the review car of another model
        view["component"] = component
        return view
    if conditions.get("review_car"):
        view["review_car"] = conditions["review_car"]
    if conditions.get("scope_note"):
        view["scope_note"] = conditions["scope_note"]
    return view


def _order(issue: KnownIssue) -> int:
    return int((issue.conditions or {}).get("order", 0))


def resolved_issues(db, variant: VehicleVariant) -> list[dict]:
    """The model's own owner reports, then the reports of its components (engine, transmission,
    hybrid system, in the record's order), each (source, text) once — the rule of
    samr/tools/resolve_issues.py. Inherited reports name their origin."""
    cn = (variant.specifications or {}).get("cn") or {}
    own = sorted(
        db.scalars(
            select(KnownIssue).where(
                KnownIssue.vehicle_variant_id == variant.id, KnownIssue.market == MARKET
            )
        ),
        key=_order,
    )
    result = [_issue_view(issue, "модель") for issue in own]
    seen = {(i["source"], i["text"]) for i in result}
    for kind, cid in (cn.get("components") or {}).items():
        if not cid or kind not in KIND_COLUMN:
            continue
        rows = sorted(
            db.scalars(
                select(KnownIssue).where(
                    KnownIssue.market == MARKET,
                    KnownIssue.vehicle_variant_id.is_(None),
                    KIND_COLUMN[kind] == cid,
                )
            ),
            key=_order,
        )
        for issue in rows:
            conditions = issue.conditions or {}
            key = (conditions.get("source"), issue.description)
            if key in seen:
                continue
            seen.add(key)
            models = conditions.get("reported_in") or []
            own_model = cn.get("catalogue_model") in models
            origin = (
                f"{KIND_RU[kind]} {conditions.get('component_label', cid)}, "
                f"отзыв по {', '.join(models) or 'неизвестно'}"
                + (" (эта модель)" if own_model else "")
            )
            result.append(_issue_view(issue, origin, cid))
    return result
