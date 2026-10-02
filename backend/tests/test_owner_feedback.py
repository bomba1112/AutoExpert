from __future__ import annotations

from app.models.enums import Sentiment
from app.review_engine import OwnerFeedbackEngine
from app.schemas.reviews import OwnerObservation


def _observation(index: int, topic: str, sentiment: Sentiment) -> OwnerObservation:
    return OwnerObservation(
        id=f"obs-{index}",
        material_identity_key=f"material-{index}",
        owner_identity_key=f"owner-{index}",
        topic=topic,
        component=topic,
        sentiment=sentiment,
        summary=f"Unique summary {index}",
    )


def test_mentions_are_sample_statistics_and_duplicates_do_not_count() -> None:
    observations = [
        _observation(index, "suspension" if index < 3 else "comfort", Sentiment.NEGATIVE)
        for index in range(10)
    ]
    duplicate = observations[0].model_copy(update={"id": "duplicate-id"})
    result = OwnerFeedbackEngine().aggregate([*observations, duplicate])

    suspension = next(item for item in result.topics if item.topic == "suspension")
    assert result.unique_material_count == 10
    assert result.unique_observation_count == 10
    assert result.duplicate_count == 1
    assert suspension.material_mentions == 3
    assert suspension.mention_share == 0.3
    assert suspension.show_percentage is True
    assert result.percentage_disclaimer_required is True


def test_percentage_is_hidden_for_small_sample() -> None:
    result = OwnerFeedbackEngine().aggregate(
        [_observation(index, "engine", Sentiment.MIXED) for index in range(9)]
    )
    assert result.topics[0].show_percentage is False


def test_mirrored_story_from_same_owner_is_counted_once() -> None:
    original = _observation(1, "engine", Sentiment.NEGATIVE)
    mirror = original.model_copy(update={"id": "mirror", "material_identity_key": "mirrored-post"})
    result = OwnerFeedbackEngine().aggregate([original, mirror])
    assert result.unique_material_count == 1
    assert result.unique_observation_count == 1
    assert result.duplicate_count == 1
