from __future__ import annotations

from collections import Counter, defaultdict

from app.models.enums import Sentiment
from app.schemas.reviews import (
    OwnerFeedbackAggregation,
    OwnerObservation,
    TopicAggregation,
)


class OwnerFeedbackEngine:
    minimum_sample_for_percentage = 10

    def aggregate(self, observations: list[OwnerObservation]) -> OwnerFeedbackAggregation:
        mirrored_story_identity: dict[tuple[str, str], str] = {}
        deduplicated: dict[tuple[str, str], tuple[str, OwnerObservation]] = {}
        for item in observations:
            normalized_summary = " ".join(item.summary.casefold().split())
            canonical_material = item.material_identity_key
            if item.owner_identity_key:
                mirror_key = (item.owner_identity_key.casefold(), normalized_summary)
                canonical_material = mirrored_story_identity.setdefault(
                    mirror_key, item.material_identity_key
                )
            # One material contributes at most one vote to a topic, even if its
            # narrative is repeated, split into keywords, or normalized twice.
            key = (canonical_material, item.topic.strip().casefold())
            deduplicated.setdefault(key, (canonical_material, item))

        unique = list(deduplicated.values())
        material_ids = {canonical_material for canonical_material, _ in unique}
        topic_materials: dict[str, set[str]] = defaultdict(set)
        topic_sentiments: dict[str, Counter[Sentiment]] = defaultdict(Counter)
        for canonical_material, item in unique:
            topic = item.topic.strip().casefold()
            topic_materials[topic].add(canonical_material)
            topic_sentiments[topic][item.sentiment] += 1

        sample_size = len(material_ids)
        topics: list[TopicAggregation] = []
        positive: list[str] = []
        negative: list[str] = []
        mixed: list[str] = []
        for topic, materials in topic_materials.items():
            sentiment = self._classify_sentiment(topic_sentiments[topic])
            if sentiment == Sentiment.POSITIVE:
                positive.append(topic)
            elif sentiment == Sentiment.NEGATIVE:
                negative.append(topic)
            elif sentiment == Sentiment.MIXED:
                mixed.append(topic)
            topics.append(
                TopicAggregation(
                    topic=topic,
                    material_mentions=len(materials),
                    sample_size=sample_size,
                    mention_share=round(len(materials) / sample_size, 4) if sample_size else 0,
                    show_percentage=sample_size >= self.minimum_sample_for_percentage,
                    sentiment=sentiment,
                )
            )
        topics.sort(key=lambda value: (-value.material_mentions, value.topic))
        return OwnerFeedbackAggregation(
            unique_material_count=sample_size,
            unique_observation_count=len(unique),
            duplicate_count=len(observations) - len(unique),
            topics=topics,
            positive_topics=sorted(positive),
            negative_topics=sorted(negative),
            mixed_topics=sorted(mixed),
        )

    @staticmethod
    def _classify_sentiment(counts: Counter[Sentiment]) -> Sentiment:
        positive = counts[Sentiment.POSITIVE]
        negative = counts[Sentiment.NEGATIVE]
        explicitly_mixed = counts[Sentiment.MIXED]
        if explicitly_mixed or (positive and negative):
            return Sentiment.MIXED
        if negative:
            return Sentiment.NEGATIVE
        if positive:
            return Sentiment.POSITIVE
        return Sentiment.NEUTRAL
