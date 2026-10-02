from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel


class AnalyticsEventCreate(APIModel):
    event_name: str = Field(min_length=1, max_length=80)
    properties: dict = Field(default_factory=dict)
