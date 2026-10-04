from __future__ import annotations

from decimal import Decimal

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataOrigin


class CountryProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "country_profiles"

    country_code: Mapped[str] = mapped_column(String(2), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    currency: Mapped[str] = mapped_column(String(3))
    default_language: Mapped[str] = mapped_column(String(5))
    road_context: Mapped[dict] = mapped_column(JSON, default=dict)
    supply_context: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    regions: Mapped[list[RegionProfile]] = relationship(
        back_populates="country", cascade="all, delete-orphan"
    )


class RegionProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "region_profiles"
    __table_args__ = (UniqueConstraint("country_id", "name"),)

    country_id: Mapped[str] = mapped_column(ForeignKey("country_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    road_context: Mapped[dict] = mapped_column(JSON, default=dict)
    climate_context: Mapped[dict] = mapped_column(JSON, default=dict)
    service_context: Mapped[dict] = mapped_column(JSON, default=dict)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    country: Mapped[CountryProfile] = relationship(back_populates="regions")


class VehicleMake(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_makes"

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    normalized_name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    models: Mapped[list[VehicleModel]] = relationship(
        back_populates="make", cascade="all, delete-orphan"
    )


class VehicleModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_models"
    __table_args__ = (UniqueConstraint("make_id", "normalized_name"),)

    make_id: Mapped[str] = mapped_column(ForeignKey("vehicle_makes.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    normalized_name: Mapped[str] = mapped_column(String(120), index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    make: Mapped[VehicleMake] = relationship(back_populates="models")
    generations: Mapped[list[VehicleGeneration]] = relationship(
        back_populates="model", cascade="all, delete-orphan"
    )


class VehicleGeneration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_generations"
    __table_args__ = (UniqueConstraint("model_id", "code", "start_year"),)

    model_id: Mapped[str] = mapped_column(ForeignKey("vehicle_models.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str | None] = mapped_column(String(80))
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    model: Mapped[VehicleModel] = relationship(back_populates="generations")
    variants: Mapped[list[VehicleVariant]] = relationship(
        back_populates="generation", cascade="all, delete-orphan"
    )


class VehicleVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_variants"

    catalog_key: Mapped[str | None] = mapped_column(String(180), unique=True, index=True)
    published_revision_id: Mapped[str | None] = mapped_column(String(36), index=True)
    editorial_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    generation_id: Mapped[str] = mapped_column(ForeignKey("vehicle_generations.id"), index=True)
    specification_source_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_records.id"), index=True
    )
    market: Mapped[str] = mapped_column(String(24), index=True)
    name: Mapped[str] = mapped_column(String(180))
    year_from: Mapped[int | None] = mapped_column(Integer)
    year_to: Mapped[int | None] = mapped_column(Integer)
    engine_code: Mapped[str | None] = mapped_column(String(80))
    engine: Mapped[str | None] = mapped_column(String(160))
    transmission_code: Mapped[str | None] = mapped_column(String(80))
    transmission: Mapped[str | None] = mapped_column(String(120))
    drivetrain: Mapped[str | None] = mapped_column(String(40))
    body: Mapped[str | None] = mapped_column(String(60))
    fuel: Mapped[str | None] = mapped_column(String(40))
    displacement_l: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    power_kw: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    ground_clearance_mm: Mapped[int | None] = mapped_column(Integer)
    official_fuel_city_l_100km: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    official_fuel_highway_l_100km: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    # f090 (CN catalogue): ICE / HEV / PHEV / EREV / BEV and the official traction battery,
    # the main fingerprint of a Chinese configuration. NULL for every US/CA variant.
    powertrain_type: Mapped[str | None] = mapped_column(String(16), index=True)
    battery_kwh: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), index=True)
    specifications: Mapped[dict] = mapped_column(JSON, default=dict)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        Enum(DataOrigin, name="vehicle_variant_data_origin", native_enum=False),
        default=DataOrigin.REAL,
        index=True,
    )

    generation: Mapped[VehicleGeneration] = relationship(back_populates="variants")
    specification_source: Mapped[SourceRecord | None] = relationship()
    technical_evidence: Mapped[list[TechnicalEvidence]] = relationship(
        back_populates="vehicle_variant"
    )
    known_issues: Mapped[list[KnownIssue]] = relationship(back_populates="vehicle_variant")


from app.models.evidence import KnownIssue, SourceRecord, TechnicalEvidence  # noqa: E402
