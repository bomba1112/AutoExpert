"""Bounded, user-assisted Turbo.az listing intake contract."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import APIModel

InputType = Literal["URL_REFERENCE", "TEXT", "HTML_SNAPSHOT", "MANUAL"]
MatchStatus = Literal[
    "EXACT_MATCH", "MULTIPLE_CANDIDATES", "CLAIM_CONFLICT", "OUT_OF_PRODUCT_SCOPE", "NO_MATCH"
]
MANUAL_FIELDS = frozenset(
    {
        "make",
        "model",
        "year",
        "engine",
        "fuel",
        "transmission",
        "drivetrain",
        "body",
        "market",
        "price",
        "currency",
        "mileage",
        "mileage_unit",
        "vin",
        "city",
        "color",
        "seller_type",
        "owners",
        "condition",
        "description",
        "listing_id",
    }
)


class ListingIntakeCreate(APIModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    input_type: InputType
    source_url: str | None = Field(default=None, max_length=2000)
    text: str | None = None
    html: str | None = None
    fields: dict[str, str | int | float] | None = None
    language: Literal["ru", "az"] = "ru"

    @model_validator(mode="after")
    def exactly_one_allowed_payload(self) -> ListingIntakeCreate:
        if self.input_type == "URL_REFERENCE":
            if (
                not self.source_url
                or self.text is not None
                or self.html is not None
                or self.fields is not None
            ):
                raise ValueError("URL_REFERENCE requires only a Turbo.az URL")
        elif self.input_type == "TEXT":
            if not self.text or self.html is not None or self.fields is not None:
                raise ValueError("TEXT requires only pasted text")
            if len(self.text.encode("utf-8")) > 60_000:
                raise ValueError("Pasted text exceeds 60 KB")
        elif self.input_type == "HTML_SNAPSHOT":
            if not self.html or self.text is not None or self.fields is not None:
                raise ValueError("HTML_SNAPSHOT requires only supplied HTML")
            if len(self.html.encode("utf-8")) > 256_000:
                raise ValueError("HTML snapshot exceeds 256 KB")
        elif self.input_type == "MANUAL":
            if not self.fields or self.text is not None or self.html is not None:
                raise ValueError("MANUAL requires fields")
            if set(self.fields) - MANUAL_FIELDS:
                raise ValueError("Unsupported manual field")
            if len(self.fields) > 22 or any(
                isinstance(value, bool)
                or len(str(value).encode("utf-8")) > (4000 if key == "description" else 200)
                for key, value in self.fields.items()
            ):
                raise ValueError("Manual field exceeds limit")
            if len(str(self.fields).encode("utf-8")) > 8_000:
                raise ValueError("Manual input exceeds 8 KB")
        return self


class ListingSnapshotRead(APIModel):
    source_type: Literal["TURBO_AZ", "USER_PROVIDED"]
    source_url: str | None = None
    source_listing_id: str | None = None
    captured_at: datetime
    input_type: InputType
    content_hash: str
    raw_content_locator: str | None = None
    language: Literal["ru", "az"]
    parser_version: str


class ListingFieldClaimRead(APIModel):
    field_name: str
    raw_value: str
    normalized_value: Any
    unit: str | None = None
    claim_type: Literal["SELLER_CLAIM"] = "SELLER_CLAIM"
    source_locator: str
    confidence: float = Field(ge=0, le=1)


class ListingCandidateRead(APIModel):
    variant_id: str
    make: str
    model: str
    year: int
    configuration: str
    engine: str | None = None
    transmission: str | None = None
    drivetrain: str | None = None
    body: str | None = None
    fuel: str | None = None


class ListingConflictRead(APIModel):
    field_name: str
    claimed: str
    catalog_values: list[str]


class ListingMatchRead(APIModel):
    status: MatchStatus
    candidates: list[ListingCandidateRead] = Field(default_factory=list)
    question: str | None = None
    conflicts: list[ListingConflictRead] = Field(default_factory=list)


class ListingIntakeRead(APIModel):
    id: str
    snapshot: ListingSnapshotRead
    claims: list[ListingFieldClaimRead]
    match: ListingMatchRead
    next_step: Literal["PROVIDE_CONTENT", "VIEW_RESULT"]
