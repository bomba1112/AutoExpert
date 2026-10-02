from enum import StrEnum


class EvidenceStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    ESTIMATE = "ESTIMATE"
    NEEDS_INSPECTION = "NEEDS_INSPECTION"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class DataOrigin(StrEnum):
    DEMO = "DEMO"
    REAL = "REAL"


class ResearchJobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ProviderCostModel(StrEnum):
    FREE = "FREE"
    PAYG = "PAYG"
    SUBSCRIPTION = "SUBSCRIPTION"


class VehicleIdentifierType(StrEnum):
    VIN = "VIN"
    CHASSIS_NUMBER = "CHASSIS_NUMBER"
    FRAME_NUMBER = "FRAME_NUMBER"


class VariantResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class SourceTier(StrEnum):
    A = "A"
    B = "B"
    C = "C"


class EvidenceCategory(StrEnum):
    ENGINE = "engine"
    TRANSMISSION = "transmission"
    SUSPENSION = "suspension"
    STEERING = "steering"
    BRAKES = "brakes"
    ELECTRICAL = "electrical"
    BODY = "body"
    MAINTENANCE = "maintenance"
    FUEL = "fuel"
    SAFETY = "safety"
    OTHER = "other"


class ConfidenceLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Severity(StrEnum):
    LOW = "LOW"
    MINOR = "MINOR"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EntitlementType(StrEnum):
    VIN_REPORT_UNLOCKED = "VIN_REPORT_UNLOCKED"


class EntitlementStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class OdometerRisk(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class ChatRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ChatAccessMode(StrEnum):
    INCLUDED_WITH_UNLOCKED_DOSSIER = "INCLUDED_WITH_UNLOCKED_DOSSIER"
    LIMITED_QUESTIONS = "LIMITED_QUESTIONS"
    PREMIUM_UNLIMITED = "PREMIUM_UNLIMITED"
    SUBSCRIPTION = "SUBSCRIPTION"


class FitRating(StrEnum):
    STRONG_FIT = "STRONG_FIT"
    GOOD_FIT_WITH_CONDITIONS = "GOOD_FIT_WITH_CONDITIONS"
    COMPROMISE = "COMPROMISE"
    POOR_FIT = "POOR_FIT"


class ReportStatus(StrEnum):
    PREVIEW = "PREVIEW"
    FULL = "FULL"
    FAILED = "FAILED"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    ADMIN_UNLOCKED = "ADMIN_UNLOCKED"


class SourceUsageStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DISABLED = "DISABLED"


class Sentiment(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    MIXED = "MIXED"
    NEUTRAL = "NEUTRAL"


class ScopeLevel(StrEnum):
    """Level at which a scoped technical fact is defined (f087)."""

    CONFIGURATION = "CONFIGURATION"
    GENERATION = "GENERATION"
    ENGINE = "ENGINE"
    TRANSMISSION = "TRANSMISSION"


class DisplayLevel(StrEnum):
    """How a scoped fact may be shown to a consumer.

    FACT: official source or two independent sources agree.
    SECONDARY_NOTE: a single secondary reference ("по данным справочников").
    OWNER_REPORTS: owner complaints only ("владельцы сообщают…").
    HIDDEN_CONFLICT: sources disagree and the conflict is unresolved; never shown.
    """

    FACT = "FACT"
    SECONDARY_NOTE = "SECONDARY_NOTE"
    OWNER_REPORTS = "OWNER_REPORTS"
    HIDDEN_CONFLICT = "HIDDEN_CONFLICT"


class IssueProbability(StrEnum):
    COMMON = "COMMON"
    OCCASIONAL = "OCCASIONAL"
    RARE = "RARE"


class MaintenanceSystem(StrEnum):
    FIXED_INTERVAL = "FIXED_INTERVAL"
    OIL_LIFE_MONITOR = "OIL_LIFE_MONITOR"
    MAINTENANCE_MINDER = "MAINTENANCE_MINDER"
    CBS = "CBS"
    SERVICE_A_B = "SERVICE_A_B"


class MaintenanceAction(StrEnum):
    REPLACE = "REPLACE"
    INSPECT = "INSPECT"
    ROTATE = "ROTATE"
    ADJUST = "ADJUST"
    CLEAN = "CLEAN"


class MaintenanceCondition(StrEnum):
    NORMAL = "NORMAL"
    SEVERE = "SEVERE"


class MaintenanceOccurrence(StrEnum):
    EVERY = "EVERY"
    FIRST = "FIRST"
    SUBSEQUENT = "SUBSEQUENT"
