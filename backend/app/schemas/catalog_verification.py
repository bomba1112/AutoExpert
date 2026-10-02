"""Scoped documentary evidence on the existing CatalogRecord / ImportJob path."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DocumentaryReference(Strict):
    registry_id: str
    document_id: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    url: str = Field(pattern=r"^https://", max_length=2000)
    locator: str = Field(min_length=3, max_length=1000)
    make: str
    model: str
    market: str
    model_year: int | None = Field(default=None, ge=1886, le=2100)
    model_year_from: int | None = Field(default=None, ge=1886, le=2100)
    model_year_to: int | None = Field(default=None, ge=1886, le=2100)

    @model_validator(mode="after")
    def exact_year_or_documented_range(self):
        if self.model_year is not None:
            if self.model_year_from is not None or self.model_year_to is not None:
                raise ValueError("ONE_DOCUMENT_YEAR_SCOPE_REQUIRED")
        elif self.model_year_from is None or self.model_year_to is None:
            raise ValueError("DOCUMENT_YEAR_SCOPE_REQUIRED")
        elif self.model_year_to < self.model_year_from:
            raise ValueError("DOCUMENT_YEAR_RANGE_REVERSED")
        return self


class IdentityRange(Strict):
    family_scope_id: str = Field(min_length=3, max_length=160)
    configuration_group: str = Field(min_length=10, max_length=400)
    model_year_from: int = Field(ge=1886, le=2100)
    model_year_to: int = Field(ge=1886, le=2100)
    exclusions: list[str] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def coherent_range(self):
        if not 1 <= self.model_year_to - self.model_year_from <= 40:
            raise ValueError("MULTI_YEAR_RANGE_REQUIRED")
        return self


class IdentityVerification(Strict):
    previous_revision_id: str
    # Each record stays configuration-specific; an optional range requires evidence for every year.
    applicability: str = Field(min_length=20, max_length=1500)
    field_evidence: dict[str, list[DocumentaryReference]]
    unresolved_conflicts: list[str] = Field(default_factory=list)
    review_note: str = Field(min_length=20, max_length=2000)
    range_scope: IdentityRange | None = None


class DocumentarySection(Strict):
    key: str
    status: Literal["EVIDENCED", "PARTIAL", "NOT_APPLICABLE"]
    text: dict[str, str]
    references: list[DocumentaryReference] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def bilingual(self):
        if set(self.text) != {"az", "ru"} or any(len(s) < 30 for s in self.text.values()):
            raise ValueError("SUBSTANTIVE_AZ_RU_TEXT_REQUIRED")
        if self.key not in {
            "conclusion",
            "engine",
            "transmission",
            "fuel",
            "body",
            "chassis",
            "safety",
            "electrical",
            "service",
            "market",
            "owners",
            "recalls",
            "communications",
            "known_issues",
            "applicability",
        }:
            raise ValueError("EXISTING_DOSSIER_SECTION_REQUIRED")
        return self
