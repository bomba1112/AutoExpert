from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from app.core.vin import VINValidationError, normalize_vin, validate_vin
from app.models.enums import VehicleIdentifierType

NON_NA_VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
LOCAL_IDENTIFIER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9-]{4,29}$")


def normalize_market(value: str) -> str:
    normalized = "".join(value.strip().upper().split())
    aliases = {
        "US": "USA",
        "UNITEDSTATES": "USA",
        "CA": "CANADA",
        "CAN": "CANADA",
        "KR": "KOREA",
        "KOR": "KOREA",
        "SOUTHKOREA": "KOREA",
        "JP": "JAPAN",
        "JPN": "JAPAN",
        "EU": "EUROPE",
        "CN": "CHINA",
        "CHN": "CHINA",
    }
    return aliases.get(normalized, normalized)


@dataclass(frozen=True)
class IdentifierValidationResult:
    value: str
    identifier_type: VehicleIdentifierType
    market: str
    strategy: str
    check_digit_applied: bool


class IdentifierValidationStrategy(Protocol):
    id: str

    def validate(
        self, value: str, identifier_type: VehicleIdentifierType, market: str
    ) -> IdentifierValidationResult: ...


class NorthAmericanIdentifierStrategy:
    id = "NORTH_AMERICA_VIN"

    def validate(
        self, value: str, identifier_type: VehicleIdentifierType, market: str
    ) -> IdentifierValidationResult:
        if identifier_type != VehicleIdentifierType.VIN:
            raise VINValidationError("USA and Canada research currently require a VIN")
        return IdentifierValidationResult(
            value=validate_vin(value),
            identifier_type=identifier_type,
            market=market,
            strategy=self.id,
            check_digit_applied=True,
        )


class InternationalVINStrategy:
    id = "INTERNATIONAL_VIN"

    def validate(
        self, value: str, identifier_type: VehicleIdentifierType, market: str
    ) -> IdentifierValidationResult:
        if identifier_type != VehicleIdentifierType.VIN:
            raise VINValidationError(f"{market} strategy expects a VIN")
        normalized = normalize_vin(value)
        if len(normalized) != 17:
            raise VINValidationError("VIN must contain exactly 17 characters")
        if not NON_NA_VIN_PATTERN.fullmatch(normalized):
            raise VINValidationError("VIN contains unsupported characters or I, O, Q")
        return IdentifierValidationResult(
            value=normalized,
            identifier_type=identifier_type,
            market=market,
            strategy=self.id,
            check_digit_applied=False,
        )


class JapaneseIdentifierStrategy:
    id = "JAPAN_VIN_OR_FRAME"

    def validate(
        self, value: str, identifier_type: VehicleIdentifierType, market: str
    ) -> IdentifierValidationResult:
        if identifier_type == VehicleIdentifierType.VIN:
            return InternationalVINStrategy().validate(value, identifier_type, market)
        normalized = normalize_vin(value)
        if not LOCAL_IDENTIFIER_PATTERN.fullmatch(normalized):
            raise VINValidationError(
                "Japanese chassis/frame number must be 5-30 letters, digits, or hyphens"
            )
        return IdentifierValidationResult(
            value=normalized,
            identifier_type=identifier_type,
            market=market,
            strategy=self.id,
            check_digit_applied=False,
        )


class VehicleIdentifierValidator:
    """Chooses identifier validation rules by market instead of assuming US rules."""

    def __init__(self) -> None:
        self._north_america = NorthAmericanIdentifierStrategy()
        self._international = InternationalVINStrategy()
        self._japan = JapaneseIdentifierStrategy()

    def validate(
        self,
        value: str,
        *,
        market: str,
        identifier_type: VehicleIdentifierType = VehicleIdentifierType.VIN,
    ) -> IdentifierValidationResult:
        normalized_market = normalize_market(market)
        if normalized_market in {"USA", "CANADA"}:
            strategy: IdentifierValidationStrategy = self._north_america
        elif normalized_market == "JAPAN":
            strategy = self._japan
        else:
            strategy = self._international
        return strategy.validate(value, identifier_type, normalized_market)


__all__ = [
    "IdentifierValidationResult",
    "VehicleIdentifierValidator",
    "VehicleIdentifierType",
    "normalize_market",
]
