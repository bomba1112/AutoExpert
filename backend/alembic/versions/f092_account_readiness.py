# ruff: noqa: E501
"""Account readiness for the owners club (product phase, stage 4): email confirmation, password
reset, login attempts and the outbox. Three nullable user columns and three new tables; nothing
existing changes."""

import sqlalchemy as sa
from alembic import op

revision = "f092_account_readiness"
down_revision = "f091_ai_mechanic"
branch_labels = depends_on = None


def _stamps():
    return [sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("email_verified_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("password_changed_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("display_name", sa.String(40)))
    op.create_table(
        "auth_tokens", *_stamps(),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_auth_tokens_user_id_users"), nullable=False),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("token_hash", name="uq_auth_tokens_token_hash"),
    )
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])
    op.create_table(
        "login_attempts", *_stamps(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("ip", sa.String(64)),
        sa.Column("success", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_login_attempts_email", "login_attempts", ["email"])
    op.create_index("ix_login_attempts_ip", "login_attempts", ["ip"])
    op.create_table(
        "outbox_messages", *_stamps(),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_outbox_messages_user_id_users")),
        sa.Column("channel", sa.String(10), nullable=False),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("recipient", sa.String(320), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_outbox_messages_user_id", "outbox_messages", ["user_id"])


def downgrade():
    for table in ("outbox_messages", "login_attempts", "auth_tokens"):
        op.drop_table(table)
    with op.batch_alter_table("users") as batch:
        for column in ("display_name", "password_changed_at", "email_verified_at"):
            batch.drop_column(column)
