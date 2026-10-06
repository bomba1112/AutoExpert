"""Chinese configuration catalogue (samr/catalog): powertrain, battery, hybrid system.

Only nullable additions, no new tables:
- vehicle_variants.powertrain_type (ICE / HEV / PHEV / EREV / BEV) and battery_kwh, the main
  fingerprint of a Chinese configuration; NULL for every existing US/CA variant;
- hybrid_system_key on technical_evidence and known_issues: the hybrid-system component a fact
  or an owner-reported issue belongs to (scope_level HYBRID_SYSTEM), next to the existing
  engine_family_key / transmission_key;
- known_issues.severity becomes nullable: owner reviews state no severity and none is invented;
  an issue without severity is hidden from severity displays. Existing rows keep their value.

Downgrade is refused while CN rows exist (they cannot be represented in the previous schema);
remove them explicitly first instead of losing them silently.
"""

import sqlalchemy as sa
from alembic import op

revision = "f095_cn_catalog"
down_revision = "f094_subscriptions"
branch_labels = depends_on = None


def upgrade():
    with op.batch_alter_table("vehicle_variants") as batch:
        batch.add_column(sa.Column("powertrain_type", sa.String(16)))
        batch.add_column(sa.Column("battery_kwh", sa.Numeric(6, 2)))
        batch.create_index("ix_vehicle_variants_powertrain_type", ["powertrain_type"])
        batch.create_index("ix_vehicle_variants_battery_kwh", ["battery_kwh"])

    with op.batch_alter_table("technical_evidence") as batch:
        batch.add_column(sa.Column("hybrid_system_key", sa.String(40)))
        batch.create_index("ix_technical_evidence_hybrid_system_key", ["hybrid_system_key"])

    with op.batch_alter_table("known_issues") as batch:
        batch.add_column(sa.Column("hybrid_system_key", sa.String(40)))
        batch.create_index("ix_known_issues_hybrid_system_key", ["hybrid_system_key"])
        batch.alter_column("severity", existing_type=sa.String(8), nullable=True)


def downgrade():
    bind = op.get_bind()
    counts = {
        "CN variants": "SELECT COUNT(*) FROM vehicle_variants WHERE market = 'CN'",
        "known issues without severity": "SELECT COUNT(*) FROM known_issues WHERE severity IS NULL",
        "hybrid-system facts": "SELECT COUNT(*) FROM technical_evidence"
        " WHERE hybrid_system_key IS NOT NULL",
        "hybrid-system issues": "SELECT COUNT(*) FROM known_issues"
        " WHERE hybrid_system_key IS NOT NULL",
    }
    found = {name: bind.execute(sa.text(sql)).scalar() for name, sql in counts.items()}
    if any(found.values()):
        raise RuntimeError(
            f"f095 downgrade refused: {found}. Export and delete the CN rows explicitly first."
        )

    with op.batch_alter_table("known_issues") as batch:
        batch.alter_column("severity", existing_type=sa.String(8), nullable=False)
        batch.drop_index("ix_known_issues_hybrid_system_key")
        batch.drop_column("hybrid_system_key")

    with op.batch_alter_table("technical_evidence") as batch:
        batch.drop_index("ix_technical_evidence_hybrid_system_key")
        batch.drop_column("hybrid_system_key")

    with op.batch_alter_table("vehicle_variants") as batch:
        batch.drop_index("ix_vehicle_variants_battery_kwh")
        batch.drop_index("ix_vehicle_variants_powertrain_type")
        batch.drop_column("battery_kwh")
        batch.drop_column("powertrain_type")
