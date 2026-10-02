from __future__ import annotations

import re

VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
VIN_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)
VIN_VALUES = {
    **{str(value): value for value in range(10)},
    **dict(zip("ABCDEFGH", range(1, 9), strict=True)),
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "P": 7,
    "R": 9,
    **dict(zip("STUVWXYZ", range(2, 10), strict=True)),
}


class VINValidationError(ValueError):
    pass


def normalize_vin(value: str) -> str:
    return value.strip().upper()


def expected_check_digit(vin: str) -> str:
    total = sum(VIN_VALUES[character] * VIN_WEIGHTS[index] for index, character in enumerate(vin))
    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


def validate_vin(value: str) -> str:
    vin = normalize_vin(value)
    if len(vin) != 17:
        raise VINValidationError("VIN must contain exactly 17 characters")
    forbidden = sorted(set(vin) & {"I", "O", "Q"})
    if forbidden:
        raise VINValidationError("VIN cannot contain I, O, or Q")
    if not VIN_PATTERN.fullmatch(vin):
        raise VINValidationError("VIN contains unsupported characters")
    if vin[8] != expected_check_digit(vin):
        raise VINValidationError("VIN checksum is invalid")
    return vin
