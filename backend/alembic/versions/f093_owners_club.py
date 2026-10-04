# ruff: noqa: E501
"""The owners club (product phase, stage 4): rooms, posts, comments, photos, "me too" marks,
reports, bans, the moderation log and the review queue. New tables only."""

import sqlalchemy as sa
from alembic import op

revision = "f093_owners_club"
down_revision = "f092_account_readiness"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "club_rooms",
        sa.Column("key", sa.String(80), nullable=False),
        sa.UniqueConstraint("key", name="uq_club_rooms_key"),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("make_id", sa.String(36), sa.ForeignKey("vehicle_makes.id", name="fk_club_rooms_make_id_vehicle_makes"), nullable=False),
        sa.Column("generation_id", sa.String(36), sa.ForeignKey("vehicle_generations.id", name="fk_club_rooms_generation_id_vehicle_generations")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("year_from", sa.Integer()),
        sa.Column("year_to", sa.Integer()),
        sa.Column("starters_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "club_posts",
        sa.Column("room_id", sa.String(36), sa.ForeignKey("club_rooms.id", ondelete="CASCADE", name="fk_club_posts_room_id_club_rooms"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_club_posts_user_id_users")),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("known_issue_id", sa.String(36), sa.ForeignKey("known_issues.id", ondelete="SET NULL", name="fk_club_posts_known_issue_id_known_issues")),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("same_count", sa.Integer(), nullable=False),
        sa.Column("report_count", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "club_comments",
        sa.Column("post_id", sa.String(36), sa.ForeignKey("club_posts.id", ondelete="CASCADE", name="fk_club_comments_post_id_club_posts"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_club_comments_user_id_users"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("report_count", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "club_photos",
        sa.Column("post_id", sa.String(36), sa.ForeignKey("club_posts.id", ondelete="CASCADE", name="fk_club_photos_post_id_club_posts"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_club_photos_user_id_users"), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "club_reactions",
        sa.Column("post_id", sa.String(36), sa.ForeignKey("club_posts.id", ondelete="CASCADE", name="fk_club_reactions_post_id_club_posts"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_club_reactions_user_id_users"), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("post_id", "user_id", name="uq_club_reactions_post_user"),
    )
    op.create_table(
        "club_reports",
        sa.Column("target_type", sa.String(10), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("reporter_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_club_reports_reporter_id_users"), nullable=False),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.Column("note", sa.String(300)),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("target_type", "target_id", "reporter_id", name="uq_club_reports_target_reporter"),
    )
    op.create_table(
        "club_bans",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_club_bans_user_id_users"), nullable=False),
        sa.Column("by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL", name="fk_club_bans_by_user_id_users")),
        sa.Column("reason", sa.String(300), nullable=False),
        sa.Column("until", sa.DateTime(timezone=True)),
        sa.Column("lifted_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "club_moderation_log",
        sa.Column("actor", sa.String(40), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("target_type", sa.String(10), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("reason", sa.String(300)),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "club_review_queue",
        sa.Column("post_id", sa.String(36), sa.ForeignKey("club_posts.id", ondelete="CASCADE", name="fk_club_review_queue_post_id_club_posts"), nullable=False),
        sa.UniqueConstraint("post_id", name="uq_club_review_queue_post_id"),
        sa.Column("room_id", sa.String(36), sa.ForeignKey("club_rooms.id", ondelete="CASCADE", name="fk_club_review_queue_room_id_club_rooms"), nullable=False),
        sa.Column("owners", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("reviewed_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL", name="fk_club_review_queue_reviewed_by_users")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("known_issue_id", sa.String(36), sa.ForeignKey("known_issues.id", ondelete="SET NULL", name="fk_club_review_queue_known_issue_id_known_issues")),
        sa.Column("note", sa.Text()),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_club_rooms_make_id", "club_rooms", ["make_id"])
    op.create_index("ix_club_rooms_generation_id", "club_rooms", ["generation_id"])
    op.create_index("ix_club_posts_room_id", "club_posts", ["room_id"])
    op.create_index("ix_club_posts_user_id", "club_posts", ["user_id"])
    op.create_index("ix_club_comments_post_id", "club_comments", ["post_id"])
    op.create_index("ix_club_comments_user_id", "club_comments", ["user_id"])
    op.create_index("ix_club_photos_post_id", "club_photos", ["post_id"])
    op.create_index("ix_club_reactions_post_id", "club_reactions", ["post_id"])
    op.create_index("ix_club_reports_target_id", "club_reports", ["target_id"])
    op.create_index("ix_club_bans_user_id", "club_bans", ["user_id"])
    op.create_index("ix_club_moderation_log_target_id", "club_moderation_log", ["target_id"])
    op.create_index("ix_club_review_queue_room_id", "club_review_queue", ["room_id"])


def downgrade():
    for table in ('club_review_queue', 'club_moderation_log', 'club_bans', 'club_reports', 'club_reactions', 'club_photos', 'club_comments', 'club_posts', 'club_rooms'):
        op.drop_table(table)
