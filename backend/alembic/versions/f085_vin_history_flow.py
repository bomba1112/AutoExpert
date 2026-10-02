"""Provider-agnostic, separately entitled VIN history checkout."""

import sqlalchemy as sa
from alembic import op

revision = "f085_vin_history_flow"
down_revision = "f084_commercial_fact_claims"
branch_labels = depends_on = None


def _identity():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "vin_check_requests",
        *_identity(),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vin", sa.String(17), nullable=False),
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column("product", sa.String(80), nullable=False),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("vehicle_identity", sa.JSON(), nullable=False),
        sa.Column("preview", sa.JSON(), nullable=False),
        sa.Column("quote", sa.JSON(), nullable=False),
        sa.Column("failure_code", sa.String(80)),
        sa.Column("is_mock", sa.Boolean(), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "vin",
            "provider_id",
            "product",
            name="uq_vin_history_owner_vin_provider_product",
        ),
    )
    for column in ("user_id", "vin", "status"):
        op.create_index(f"ix_vin_check_requests_{column}", "vin_check_requests", [column])
    op.create_table(
        "provider_capability_snapshots",
        *_identity(),
        sa.Column(
            "request_id", sa.String(36), sa.ForeignKey("vin_check_requests.id"), nullable=False
        ),
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.UniqueConstraint("request_id", name="uq_provider_capability_request"),
    )
    op.create_index(
        "ix_provider_capability_snapshots_request_id",
        "provider_capability_snapshots",
        ["request_id"],
    )
    op.create_table(
        "provider_transactions",
        *_identity(),
        sa.Column(
            "request_id", sa.String(36), sa.ForeignKey("vin_check_requests.id"), nullable=False
        ),
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("external_id", sa.String(200)),
        sa.Column("raw_payload", sa.JSON()),
        sa.Column("failure_code", sa.String(80)),
        sa.UniqueConstraint("request_id", "kind", name="uq_provider_transaction_request_kind"),
        sa.UniqueConstraint("idempotency_key", name="uq_provider_transaction_idempotency"),
    )
    op.create_index("ix_provider_transactions_request_id", "provider_transactions", ["request_id"])
    op.create_table(
        "vehicle_history_reports",
        *_identity(),
        sa.Column(
            "request_id", sa.String(36), sa.ForeignKey("vin_check_requests.id"), nullable=False
        ),
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column("provider_report_id", sa.String(200)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("vehicle_identity", sa.JSON(), nullable=False),
        sa.Column("normalized_snapshot", sa.JSON(), nullable=False),
        sa.Column("source_snapshot", sa.JSON(), nullable=False),
        sa.UniqueConstraint("request_id", name="uq_vehicle_history_report_request"),
    )
    op.create_index(
        "ix_vehicle_history_reports_request_id", "vehicle_history_reports", ["request_id"]
    )
    op.create_table(
        "history_events",
        *_identity(),
        sa.Column(
            "report_id", sa.String(36), sa.ForeignKey("vehicle_history_reports.id"), nullable=False
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("event_date", sa.String(10)),
        sa.Column("country", sa.String(3)),
        sa.Column("state", sa.String(60)),
        sa.Column("mileage", sa.Integer()),
        sa.Column("mileage_unit", sa.String(5)),
        sa.Column("source_provider", sa.String(80), nullable=False),
        sa.Column("source_record_id", sa.String(160), nullable=False),
        sa.Column("normalized_summary", sa.JSON(), nullable=False),
        sa.Column("raw_locator", sa.String(300), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.UniqueConstraint(
            "report_id", "source_record_id", "event_type", name="uq_history_event_source_type"
        ),
    )
    op.create_index("ix_history_events_report_id", "history_events", ["report_id"])
    op.create_index("ix_history_events_event_type", "history_events", ["event_type"])
    for table in (
        "odometer_events",
        "damage_events",
        "auction_events",
        "title_events",
        "registration_events",
        "theft_events",
    ):
        op.create_table(
            table,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "history_event_id",
                sa.String(36),
                sa.ForeignKey("history_events.id"),
                unique=True,
                nullable=False,
            ),
            sa.Column("details", sa.JSON(), nullable=False),
        )
    op.create_table(
        "history_assets",
        *_identity(),
        sa.Column(
            "report_id", sa.String(36), sa.ForeignKey("vehicle_history_reports.id"), nullable=False
        ),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("history_events.id")),
        sa.Column("source_record_id", sa.String(160), nullable=False),
        sa.Column("media_type", sa.String(80), nullable=False),
        sa.Column("photo_type", sa.String(32), nullable=False),
        sa.Column("display_rights_confirmed", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.LargeBinary()),
        sa.Column("caption", sa.JSON(), nullable=False),
        sa.UniqueConstraint("report_id", "source_record_id", name="uq_history_asset_source"),
    )
    op.create_index("ix_history_assets_report_id", "history_assets", ["report_id"])
    op.create_table(
        "history_report_entitlements",
        *_identity(),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "request_id", sa.String(36), sa.ForeignKey("vin_check_requests.id"), nullable=False
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "payment_transaction_id",
            sa.String(36),
            sa.ForeignKey("provider_transactions.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "request_id", name="uq_history_entitlement_owner_request"),
    )
    for column in ("user_id", "request_id"):
        op.create_index(
            f"ix_history_report_entitlements_{column}", "history_report_entitlements", [column]
        )
    op.create_table(
        "history_cost_ledger",
        *_identity(),
        sa.Column(
            "request_id", sa.String(36), sa.ForeignKey("vin_check_requests.id"), nullable=False
        ),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(14, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("is_mock", sa.Boolean(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.UniqueConstraint("request_id", "kind", name="uq_history_cost_request_kind"),
    )
    op.create_index("ix_history_cost_ledger_request_id", "history_cost_ledger", ["request_id"])


def downgrade():
    for table in (
        "history_cost_ledger",
        "history_report_entitlements",
        "history_assets",
        "theft_events",
        "registration_events",
        "title_events",
        "auction_events",
        "damage_events",
        "odometer_events",
        "history_events",
        "vehicle_history_reports",
        "provider_transactions",
        "provider_capability_snapshots",
        "vin_check_requests",
    ):
        op.drop_table(table)
