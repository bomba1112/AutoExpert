"""grounded auto expert chat

Revision ID: b74f2e6a91cd
Revises: 6f13b027d4aa
Create Date: 2026-09-14 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b74f2e6a91cd"
down_revision: str | None = "6f13b027d4aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auto_expert_chat_sessions",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("vin_check_id", sa.String(length=36), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("context_version", sa.String(length=30), nullable=False),
        sa.Column("context_snapshot", sa.JSON(), nullable=False),
        sa.Column("context_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "access_mode",
            sa.Enum(
                "INCLUDED_WITH_UNLOCKED_DOSSIER",
                "LIMITED_QUESTIONS",
                "PREMIUM_UNLIMITED",
                "SUBSCRIPTION",
                name="chat_access_mode",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("question_limit", sa.Integer(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auto_expert_chat_sessions_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["vin_check_id"],
            ["vin_checks.id"],
            name=op.f("fk_auto_expert_chat_sessions_vin_check_id_vin_checks"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auto_expert_chat_sessions")),
    )
    for column in ("user_id", "vin_check_id", "context_hash", "is_demo"):
        op.create_index(
            op.f(f"ix_auto_expert_chat_sessions_{column}"),
            "auto_expert_chat_sessions",
            [column],
            unique=False,
        )

    op.create_table(
        "auto_expert_chat_messages",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "role",
            sa.Enum("USER", "ASSISTANT", name="auto_expert_chat_role", native_enum=False),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "CONFIRMED",
                "ESTIMATE",
                "NEEDS_INSPECTION",
                "INSUFFICIENT_DATA",
                name="chat_evidence_status",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["auto_expert_chat_sessions.id"],
            name=op.f("fk_auto_expert_chat_messages_session_id_auto_expert_chat_sessions"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auto_expert_chat_messages_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auto_expert_chat_messages")),
        sa.UniqueConstraint(
            "session_id",
            "sequence",
            name=op.f("uq_auto_expert_chat_messages_session_id"),
        ),
    )
    for column in ("session_id", "user_id", "role"):
        op.create_index(
            op.f(f"ix_auto_expert_chat_messages_{column}"),
            "auto_expert_chat_messages",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in ("role", "user_id", "session_id"):
        op.drop_index(
            op.f(f"ix_auto_expert_chat_messages_{column}"),
            table_name="auto_expert_chat_messages",
        )
    op.drop_table("auto_expert_chat_messages")
    for column in ("is_demo", "context_hash", "vin_check_id", "user_id"):
        op.drop_index(
            op.f(f"ix_auto_expert_chat_sessions_{column}"),
            table_name="auto_expert_chat_sessions",
        )
    op.drop_table("auto_expert_chat_sessions")
