from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from statistics import median, quantiles

from app.models.enums import ConfidenceLevel, EvidenceStatus
from app.schemas.market import MarketAnalysis, MarketListingInput, MarketVehicle

_MONEY = Decimal("0.01")


def _normalize(value: str | None) -> str | None:
    if not value:
        return None
    return "".join(character for character in value.casefold() if character.isalnum())


def _qmoney(value: Decimal | float) -> Decimal:
    return Decimal(str(value)).quantize(_MONEY, rounding=ROUND_HALF_UP)


class MarketEngine:
    """Deterministic comparable selection and robust price statistics."""

    minimum_comparables = 3
    minimum_similarity = 0.58

    def analyze(self, vehicle: MarketVehicle, listings: list[MarketListingInput]) -> MarketAnalysis:
        same_currency_country = [
            item
            for item in listings
            if item.country == vehicle.country and item.currency == vehicle.currency
        ]
        scored: list[tuple[MarketListingInput, float]] = []
        for item in same_currency_country:
            score = self.similarity(vehicle, item)
            if score >= self.minimum_similarity:
                scored.append((item, score))

        base = {
            "currency": vehicle.currency,
            "sample_count": len(listings),
            "comparable_count": len(scored),
            "selected_price": vehicle.selected_price,
        }
        if len(scored) < self.minimum_comparables:
            return MarketAnalysis(
                **base,
                status=EvidenceStatus.INSUFFICIENT_DATA,
                confidence=ConfidenceLevel.LOW,
                assumptions=["Fewer than three sufficiently similar listings were available."],
            )

        inliers, excluded = self._remove_price_outliers([pair[0] for pair in scored])
        if len(inliers) < self.minimum_comparables:
            return MarketAnalysis(
                **base,
                status=EvidenceStatus.INSUFFICIENT_DATA,
                confidence=ConfidenceLevel.LOW,
                excluded_outlier_count=excluded,
                assumptions=["Too few comparable listings remained after outlier removal."],
            )

        prices = sorted(item.price for item in inliers)
        price_median = _qmoney(Decimal(str(median(prices))))
        if len(prices) >= 4:
            quartiles = quantiles(prices, n=4, method="inclusive")
            low, high = _qmoney(quartiles[0]), _qmoney(quartiles[2])
        else:
            low, high = _qmoney(prices[0]), _qmoney(prices[-1])

        absolute_deviation = None
        percentage_deviation = None
        if vehicle.selected_price is not None:
            absolute_deviation = _qmoney(vehicle.selected_price - price_median)
            if price_median:
                percentage_deviation = _qmoney(
                    (vehicle.selected_price - price_median) / price_median * Decimal(100)
                )

        mean_similarity = sum(
            score for item, score in scored if item.id in {value.id for value in inliers}
        ) / len(inliers)
        confidence = self._confidence(len(inliers), mean_similarity)
        return MarketAnalysis(
            **base,
            status=EvidenceStatus.ESTIMATE,
            confidence=confidence,
            used_count=len(inliers),
            excluded_outlier_count=excluded,
            median=price_median,
            market_range_low=low,
            market_range_high=high,
            absolute_deviation=absolute_deviation,
            percentage_deviation=percentage_deviation,
            assumptions=[
                "Range is the interquartile range of comparable asking prices.",
                "Asking prices are not confirmed transaction prices.",
                "Outliers are removed with the 1.5×IQR rule when at least four prices exist.",
            ],
            matched_listing_ids=[item.id for item in inliers],
        )

    def similarity(self, vehicle: MarketVehicle, listing: MarketListingInput) -> float:
        if _normalize(vehicle.make) != _normalize(listing.make):
            return 0.0
        if _normalize(vehicle.model) != _normalize(listing.model):
            return 0.0
        if (
            vehicle.generation
            and listing.generation
            and _normalize(vehicle.generation) != _normalize(listing.generation)
        ):
            return 0.0

        earned = 4.0  # exact make/model and same country/currency were prerequisites
        possible = 4.0

        earned, possible = self._categorical(
            vehicle.generation, listing.generation, 2.5, earned, possible
        )
        year_delta = abs(vehicle.year - listing.year)
        possible += 2.0
        earned += (
            2.0 if year_delta <= 1 else 1.4 if year_delta <= 2 else 0.6 if year_delta <= 4 else 0
        )

        earned, possible = self._categorical(vehicle.engine, listing.engine, 1.5, earned, possible)
        if vehicle.displacement_l is not None and listing.displacement_l is not None:
            possible += 1.0
            displacement_delta = abs(vehicle.displacement_l - listing.displacement_l)
            earned += (
                1.0
                if displacement_delta <= Decimal("0.1")
                else 0.4
                if displacement_delta <= Decimal("0.3")
                else 0
            )
        earned, possible = self._categorical(
            vehicle.transmission, listing.transmission, 1.5, earned, possible
        )
        earned, possible = self._categorical(
            vehicle.drivetrain, listing.drivetrain, 1.0, earned, possible
        )
        if vehicle.mileage_km is not None and listing.mileage_km is not None:
            possible += 1.0
            delta = abs(vehicle.mileage_km - listing.mileage_km)
            earned += (
                1.0
                if delta <= 20_000
                else 0.6
                if delta <= 50_000
                else 0.2
                if delta <= 100_000
                else 0
            )
        if vehicle.city and listing.city:
            possible += 0.25
            earned += 0.25 if _normalize(vehicle.city) == _normalize(listing.city) else 0
        return round(earned / possible, 4)

    @staticmethod
    def _categorical(
        left: str | None,
        right: str | None,
        weight: float,
        earned: float,
        possible: float,
    ) -> tuple[float, float]:
        if left is None or right is None:
            return earned, possible
        possible += weight
        if _normalize(left) == _normalize(right):
            earned += weight
        return earned, possible

    @staticmethod
    def _remove_price_outliers(
        listings: list[MarketListingInput],
    ) -> tuple[list[MarketListingInput], int]:
        if len(listings) < 4:
            return listings, 0
        prices = sorted(item.price for item in listings)
        q1, _, q3 = quantiles(prices, n=4, method="inclusive")
        iqr = q3 - q1
        if iqr == 0:
            inliers = [item for item in listings if item.price == q1]
        else:
            lower = q1 - Decimal("1.5") * iqr
            upper = q3 + Decimal("1.5") * iqr
            inliers = [item for item in listings if lower <= item.price <= upper]
        return inliers, len(listings) - len(inliers)

    @staticmethod
    def _confidence(count: int, mean_similarity: float) -> ConfidenceLevel:
        if count >= 10 and mean_similarity >= 0.78:
            return ConfidenceLevel.HIGH
        if count >= 5 and mean_similarity >= 0.65:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW
