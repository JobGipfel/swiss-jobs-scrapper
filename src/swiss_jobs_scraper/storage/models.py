"""
SQLAlchemy ORM models for job storage.

These models define the database schema for persisting job listings.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):  # type: ignore
    """SQLAlchemy declarative base."""

    pass


class StoredJob(Base):
    """
    Database model for persisted job listings.

    Stores both the original job data and AI-processed enrichments.
    The content_hash is used to detect changes for upsert logic.
    """

    __tablename__ = "jobs"

    # === Core Identifiers ===
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    source_platform: Mapped[str] = mapped_column(String(100), nullable=False)

    # === Original Content ===
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    external_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # === Timestamps ===
    date_added: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    date_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # === AI-Processed Fields (Separate Columns) ===
    title_de: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title_fr: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title_it: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_it: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_languages: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_experience_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    years_experience_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    education: Mapped[str | None] = mapped_column(String(500), nullable=True)
    semantic_keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )

    # === Raw Data ===
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<StoredJob(id={self.id}, title={self.title[:30] if self.title else ''}...)>"
