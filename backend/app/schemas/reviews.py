from __future__ import annotations

from pydantic import Field, model_validator

from app.models.enums import Sentiment
from app.schemas.common import APIModel


class OwnerObservation(APIModel):
    id: str
    material_identity_key: str
    owner_identity_key: str | None = None
    topic: str
    component: str
    sentiment: Sentiment
    summary: str
    source_id: str | None = None
    mileage_km: int | None = None
    observed_at: str | None = None
    is_demo: bool = False


class TopicAggregation(APIModel):
    topic: str
    material_mentions: int = Field(ge=0)
    sample_size: int = Field(ge=0)
    mention_share: float = Field(ge=0, le=1)
    show_percentage: bool
    sentiment: Sentiment

    @model_validator(mode="after")
    def unique_material_bounds(self):
        if self.material_mentions > self.sample_size:
            raise ValueError("Topic unique materials cannot exceed the total unique sample")
        return self


class OwnerFeedbackAggregation(APIModel):
    unique_material_count: int
    unique_observation_count: int
    duplicate_count: int
    topics: list[TopicAggregation]
    positive_topics: list[str]
    negative_topics: list[str]
    mixed_topics: list[str]
    percentage_disclaimer_required: bool = True
