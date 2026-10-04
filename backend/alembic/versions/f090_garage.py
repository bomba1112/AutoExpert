# ruff: noqa: E501
"""The Garage (product phase, stage 2): the owner's cars, odometer readings, service log, the
"My car" feed and the recall notices of the daily NHTSA check. New tables only; nothing existing
changes.
"""

import sqlalchemy as sa
from alembic import op

revision = "f090_garage"
down_revision = "f089_content_translations_en"
branch_labels = depends_on = None


def _stamps():
    return [sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.create_table(
        "garage_vehicles", *_stamps(),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE",
                                                         name="fk_garage_vehicles_user_id_users"), nullable=False),
        sa.Column("configuration_key", sa.String(200)),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("vin", sa.String(17)),
        sa.Column("vin_decode", sa.JSON()),
        sa.Column("nickname", sa.String(80)),
        sa.Column("region", sa.String(8), nullable=False),
        sa.Column("conditions", sa.String(10), nullable=False),
        sa.Column("conditions_by_owner", sa.Boolean(), nullable=False),
        sa.Column("in_service_date", sa.Date()),
        sa.Column("monthly_km", sa.Integer()),
        sa.Column("oil_interval_km", sa.Integer()),
        sa.Column("oil_interval_months", sa.Integer()),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_garage_vehicles_user_id", "garage_vehicles", ["user_id"])
    op.create_index("ix_garage_vehicles_configuration_key", "garage_vehicles", ["configuration_key"])
    op.create_table(
        "garage_odometer_readings", *_stamps(),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("garage_vehicles.id", ondelete="CASCADE",
                                                            name="fk_garage_odometer_readings_vehicle_id_garage_vehicles"), nullable=False),
        sa.Column("km", sa.Integer(), nullable=False),
        sa.Column("read_on", sa.Date(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
    )
    op.create_index("ix_garage_odometer_readings_vehicle_id", "garage_odometer_readings", ["vehicle_id"])
    op.create_table(
        "garage_service_records", *_stamps(),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("garage_vehicles.id", ondelete="CASCADE",
                                                            name="fk_garage_service_records_vehicle_id_garage_vehicles"), nullable=False),
        sa.Column("job", sa.String(60), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("performed_on", sa.Date()),
        sa.Column("odometer_km", sa.Integer()),
        sa.Column("note", sa.Text()),
    )
    op.create_index("ix_garage_service_records_vehicle_id", "garage_service_records", ["vehicle_id"])
    op.create_table(
        "garage_feed_items", *_stamps(),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("garage_vehicles.id", ondelete="CASCADE",
                                                            name="fk_garage_feed_items_vehicle_id_garage_vehicles"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("pushed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("vehicle_id", "key", name="uq_garage_feed_items_vehicle_key"),
    )
    op.create_index("ix_garage_feed_items_vehicle_id", "garage_feed_items", ["vehicle_id"])
    op.create_table(
        "garage_recall_notices", *_stamps(),
        sa.Column("campaign_number", sa.String(40), nullable=False),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("component", sa.Text()),
        sa.Column("summary", sa.Text()),
        sa.Column("remedy", sa.Text()),
        sa.Column("report_date", sa.String(20)),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("campaign_number", "make", "model", "year", name="uq_garage_recall_notices_campaign"),
    )


def downgrade():
    for table in ("garage_recall_notices", "garage_feed_items", "garage_service_records", "garage_odometer_readings",
                  "garage_vehicles"):
        op.drop_table(table)
