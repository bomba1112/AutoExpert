"""Translations of English content shown to buyers (owner decision 2026-10-03).

The English original stays where it is (known_issues, technical_evidence conditions,
maintenance applicability); this table holds the Russian and Azerbaijani text in separate
fields, keyed by the kind of text and the sha256 of the normalised English source, so one
translation serves every row that carries the same text. Technical terms follow one
glossary (data_work/_shared/i18n/glossary.json); glossary_version records which one.
"""

from __future__ import annotations

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ContentTranslation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_translations"
    __table_args__ = (UniqueConstraint("kind", "source_hash"),)

    # issue_title, issue_symptom, issue_inspection, issue_component, recall_summary,
    # recall_component, maintenance_service, maintenance_condition, ...
    kind: Mapped[str] = mapped_column(String(40), index=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_text: Mapped[str] = mapped_column(Text)
    text_ru: Mapped[str] = mapped_column(Text)
    text_az: Mapped[str] = mapped_column(Text)
    # template (script, glossary), glossary (term list), llm (agent, checked), manual
    method: Mapped[str] = mapped_column(String(20))
    glossary_version: Mapped[str] = mapped_column(String(20))
    # CHECKED (automatic checks passed), REVIEWED (an independent review agreed)
    status: Mapped[str] = mapped_column(String(20), default="CHECKED")
