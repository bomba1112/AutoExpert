"""Preserve separate VIN/variant research revisions instead of a partial identity key."""

from alembic import op

revision = "e641c0f912ab"
down_revision = "d942f4c1a6e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("vehicle_knowledge_profiles") as batch:
        batch.drop_constraint("uq_vehicle_knowledge_profile_identity", type_="unique")


def downgrade() -> None:
    # SQLite/the database rejects duplicates rather than destroying revisions.
    with op.batch_alter_table("vehicle_knowledge_profiles") as batch:
        batch.create_unique_constraint(
            "uq_vehicle_knowledge_profile_identity",
            [
                "make",
                "model",
                "generation",
                "market",
                "year",
                "engine_code",
                "transmission",
                "data_origin",
            ],
        )
