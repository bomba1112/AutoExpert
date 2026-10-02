from __future__ import annotations

from app.models.enums import VariantResolutionStatus
from app.schemas.research import VehicleResearchRequest
from app.services.vehicle_identity import dimensions_equal, epa_powertrain, powertrain_type


class VehicleVariantResolver:
    """Resolves only fields present in provider evidence; user hints only filter."""

    def resolve(
        self,
        request: VehicleResearchRequest,
        identity_records: list[dict],
        variant_records: list[dict],
        *,
        selected_candidate_id: str | None = None,
    ) -> dict:
        record = identity_records[0]
        candidates = self._candidates(request, record, variant_records)
        notes: list[str] = []

        filtered = candidates
        if request.engine_hint:
            matches = [
                item
                for item in candidates
                if _contains_hint(item.get("engine"), request.engine_hint)
                or _contains_hint(item.get("label"), request.engine_hint)
            ]
            if matches:
                filtered = matches
                notes.append("Engine hint filtered provider-confirmed candidates")
            else:
                notes.append(
                    "Engine hint is user input and was not promoted because no provider "
                    "candidate confirmed it"
                )

        hint_mismatch = bool(
            request.engine_hint
            and filtered == candidates
            and not any(
                _contains_hint(c.get("engine"), request.engine_hint)
                or _contains_hint(c.get("label"), request.engine_hint)
                for c in candidates
            )
        )
        for field, hint in (
            ("powertrain_type", request.powertrain_hint),
            ("fuel", request.fuel_hint),
            ("transmission", request.transmission_hint),
            ("drivetrain", request.drivetrain_hint),
            ("trim", request.trim_hint),
        ):
            if hint:
                matches = [c for c in filtered if dimensions_equal(field, c.get(field), hint)]
                if matches:
                    filtered = matches
                else:
                    hint_mismatch = True
                    notes.append(
                        f"Requested {field} was not confirmed; choose an available configuration"
                    )
        selected = None
        if selected_candidate_id:
            selected = next(
                (item for item in candidates if item["id"] == selected_candidate_id), None
            )
            if selected is None:
                raise ValueError("Selected variant is not one of this research job's candidates")
            filtered = [selected]

        if len(filtered) == 1 and (not hint_mismatch or selected_candidate_id):
            status = VariantResolutionStatus.RESOLVED
            selected = filtered[0]
        elif filtered:
            status = VariantResolutionStatus.AMBIGUOUS
        else:
            status = VariantResolutionStatus.INSUFFICIENT_DATA

        engine_candidates = _unique(item.get("engine") for item in filtered)
        engine_code_candidates = _unique(item.get("engine_code") for item in filtered)
        transmission_candidates = _unique(item.get("transmission") for item in filtered)
        drivetrain_candidates = _unique(item.get("drivetrain") for item in filtered)
        generation_candidates = _unique(item.get("generation") for item in filtered)
        unresolved = []
        for field, values in (
            ("generation", generation_candidates),
            ("engine", engine_candidates),
            ("engine_code", engine_code_candidates),
            ("transmission", transmission_candidates),
            ("drivetrain", drivetrain_candidates),
        ):
            if len(values) != 1:
                unresolved.append(field)
        if not generation_candidates:
            notes.append("Generation was not returned by the selected official provider")

        return {
            "powertrain_type": powertrain_type(record),
            "fuel": record.get("fuel_type_primary"),
            "identity_state": "IDENTITY_INCOMPLETE",
            "make": str(record.get("make") or request.make or "UNRESOLVED").title(),
            "model": str(record.get("model") or request.model or "UNRESOLVED").title(),
            "year": int(record.get("model_year") or request.year),
            "market": request.market,
            "generation": generation_candidates[0] if len(generation_candidates) == 1 else None,
            "engine_candidates": engine_candidates,
            "engine_code_candidates": engine_code_candidates,
            "transmission_candidates": transmission_candidates,
            "drivetrain_candidates": drivetrain_candidates,
            "ambiguity": status != VariantResolutionStatus.RESOLVED,
            "needs_user_selection": status == VariantResolutionStatus.AMBIGUOUS,
            "unresolved_fields": unresolved,
            "notes": notes,
            "status": status.value,
            "candidates": filtered if status != VariantResolutionStatus.INSUFFICIENT_DATA else [],
            "selected_candidate_id": selected["id"] if selected else None,
        }

    @staticmethod
    def _candidates(
        request: VehicleResearchRequest,
        identity: dict,
        variant_records: list[dict],
    ) -> list[dict]:
        if request.vin:
            transmission = _transmission(identity)
            engine = _engine_description(identity)
            engine_code = _engine_code(identity.get("engine_model"))
            trim = identity.get("trim") or identity.get("series")
            label_bits = [
                str(identity.get("model_year") or request.year or ""),
                str(identity.get("make") or request.make or ""),
                str(identity.get("model") or request.model or ""),
                str(trim or ""),
                str(engine or ""),
                str(transmission or ""),
            ]
            return [
                {
                    "id": f"vpic-vin:{request.vin}",
                    "label": " ".join(item for item in label_bits if item),
                    "generation": None,
                    "production_year_start": identity.get("model_year") or request.year,
                    "production_year_end": identity.get("model_year") or request.year,
                    "market": request.market,
                    "trim": trim,
                    "powertrain_type": powertrain_type(identity),
                    "engine": engine,
                    "engine_code": engine_code,
                    "transmission": transmission,
                    "drivetrain": identity.get("drive_type"),
                    "body": identity.get("body_class"),
                    "evidence_ids": ["nhtsa-vpic:vin-decode"],
                    "confidence": "HIGH",
                }
            ]

        deduplicated: dict[str, dict] = {}
        for row in variant_records:
            identifier = str(row.get("candidate_id") or "").strip()
            label = str(row.get("label") or "").strip()
            if not identifier or not label:
                continue
            deduplicated[identifier] = {
                "id": identifier,
                "label": label,
                "generation": row.get("generation"),
                "production_year_start": row.get("production_year_start") or request.year,
                "production_year_end": row.get("production_year_end") or request.year,
                "market": request.market,
                "trim": row.get("trim"),
                "powertrain_type": row.get("powertrain_type", "UNKNOWN"),
                "fuel": row.get("fuel"),
                "engine": row.get("engine"),
                "engine_code": row.get("engine_code"),
                "transmission": row.get("transmission"),
                "drivetrain": row.get("drivetrain"),
                "body": row.get("body"),
                "evidence_ids": list(row.get("evidence_ids") or []),
                "confidence": str(row.get("confidence") or "MEDIUM"),
            }
        return list(deduplicated.values())


def epa_candidates(records: list[dict]) -> list[dict]:
    """EPA configurations, not trim or exact-VIN claims."""
    return [
        {
            "candidate_id": f"epa:{r['id']}",
            "label": " · ".join(
                str(v)
                for v in (
                    r.get("model"),
                    epa_powertrain(r),
                    f"{r['displ']} L" if r.get("displ") else None,
                    r.get("trany"),
                    r.get("drive"),
                )
                if v
            ),
            "engine": f"{r.get('displ')} L · {r.get('cylinders')} cyl · {r.get('fuelType1')}"
            if r.get("displ")
            else r.get("fuelType1"),
            "powertrain_type": epa_powertrain(r),
            "fuel": r.get("fuelType1"),
            "transmission": r.get("trany"),
            "drivetrain": r.get("drive"),
            "body": r.get("VClass"),
            "evidence_ids": [f"epa:{r['id']}"],
            "confidence": "HIGH",
        }
        for r in records
    ]


def _contains_hint(value: object, hint: str) -> bool:
    return _normalized(hint) in _normalized(value) if value else False


def _normalized(value: object) -> str:
    return "".join(character for character in str(value or "").casefold() if character.isalnum())


def _unique(values):  # noqa: ANN001, ANN201
    return list(dict.fromkeys(str(item) for item in values if item not in {None, ""}))


def _transmission(record: dict) -> str | None:
    style = str(record.get("transmission_style") or "").strip()
    speeds = str(record.get("transmission_speeds") or "").strip()
    if style and speeds:
        return f"{speeds}-speed {style}"
    return style or (f"{speeds}-speed" if speeds else None)


def _engine_description(record: dict) -> str | None:
    values: list[str] = []
    displacement = str(record.get("displacement_l") or "").strip()
    if displacement:
        values.append(f"{displacement}L")
    cylinders = str(record.get("engine_cylinders") or "").strip()
    if cylinders:
        values.append(f"{cylinders}-cylinder")
    configuration = str(record.get("engine_configuration") or "").strip()
    if configuration and configuration.casefold() not in {item.casefold() for item in values}:
        values.append(configuration)
    fuel = str(record.get("fuel_type_primary") or "").strip()
    if fuel:
        values.append(fuel)
    model = _engine_code(record.get("engine_model"))
    if model:
        values.append(model)
    return " ".join(values) or None


def _engine_code(value: object) -> str | None:
    text = " ".join(str(value or "").split())
    if not text or text.casefold() in {
        "n/a",
        "na",
        "not applicable",
        "not available",
        "unknown",
    }:
        return None
    return text
