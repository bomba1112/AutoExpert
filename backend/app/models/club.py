# ruff: noqa: E501
"""The owners club (product phase, stage 4): rooms by make and by generation, posts, comments,
photos, "me too" marks, reports, bans, the moderation log and the review queue that feeds owner
reports into the database (after a moderator's check, never automatically)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ClubRoom(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_rooms"

    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)  # make:<id> / generation:<id>
    kind: Mapped[str] = mapped_column(String(12), nullable=False)  # MAKE / GENERATION
    make_id: Mapped[str] = mapped_column(ForeignKey("vehicle_makes.id"), index=True, nullable=False)
    generation_id: Mapped[str | None] = mapped_column(ForeignKey("vehicle_generations.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    year_from: Mapped[int | None] = mapped_column(Integer)
    year_to: Mapped[int | None] = mapped_column(Integer)
    starters_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ClubPost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_posts"

    room_id: Mapped[str] = mapped_column(ForeignKey("club_rooms.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)  # None: Auto Expert
    kind: Mapped[str] = mapped_column(String(10), default="POST", nullable=False)  # POST / STARTER
    known_issue_id: Mapped[str | None] = mapped_column(ForeignKey("known_issues.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="VISIBLE", nullable=False)  # VISIBLE / HELD / HIDDEN / REMOVED
    same_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ClubComment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_comments"

    post_id: Mapped[str] = mapped_column(ForeignKey("club_posts.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="VISIBLE", nullable=False)
    report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ClubPhoto(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A photo re-encoded on upload (camera metadata and location removed)."""

    __tablename__ = "club_photos"

    post_id: Mapped[str] = mapped_column(ForeignKey("club_posts.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)


class ClubReaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """ "У меня то же самое" — one per user and post."""

    __tablename__ = "club_reactions"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_club_reactions_post_user"),)

    post_id: Mapped[str] = mapped_column(ForeignKey("club_posts.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class ClubReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_reports"
    __table_args__ = (UniqueConstraint("target_type", "target_id", "reporter_id", name="uq_club_reports_target_reporter"),)

    target_type: Mapped[str] = mapped_column(String(10), nullable=False)  # POST / COMMENT
    target_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    reporter_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(10), default="OPEN", nullable=False)  # OPEN / RESOLVED


class ClubBan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_bans"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # None: until lifted
    lifted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ClubModerationLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_moderation_log"

    actor: Mapped[str] = mapped_column(String(40), nullable=False)  # a moderator's user id / AUTOFILTER / AI / REPORTS
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    target_type: Mapped[str] = mapped_column(String(10), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(300))
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class ClubReviewItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Owners repeatedly report the same problem: waiting for a moderator's check before it goes to
    the database as OWNER_REPORTS ("владельцы сообщают")."""

    __tablename__ = "club_review_queue"

    post_id: Mapped[str] = mapped_column(ForeignKey("club_posts.id", ondelete="CASCADE"), unique=True, nullable=False)
    room_id: Mapped[str] = mapped_column(ForeignKey("club_rooms.id", ondelete="CASCADE"), index=True, nullable=False)
    owners: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="PENDING", nullable=False)  # PENDING / APPROVED / REJECTED
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    known_issue_id: Mapped[str | None] = mapped_column(ForeignKey("known_issues.id", ondelete="SET NULL"))
    note: Mapped[str | None] = mapped_column(Text)
