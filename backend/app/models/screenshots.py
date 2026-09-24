from datetime import datetime
from uuid import UUID
from sqlalchemy import String, CHAR, Text, Integer, BigInteger, CheckConstraint, UniqueConstraint, ForeignKeyConstraint, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, TIMESTAMP
from backend.app.db import Base
from .catalog import Identity, Scoped, scope_fk


class Screenshot(Identity, Scoped, Base):
    __tablename__ = "screenshots"
    __table_args__ = (
        UniqueConstraint("project_id", "id"), scope_fk("build_id", "builds"), scope_fk("locale_id", "locales"),
        ForeignKeyConstraint(["project_id", "category_id", "situation_id"], ["situations.project_id", "situations.category_id", "situations.id"], ondelete="RESTRICT"),
        CheckConstraint("size_bytes > 0 AND width > 0 AND height > 0", name="ck_screenshot_positive"),
        CheckConstraint("metadata_version = 1 AND jsonb_typeof(metadata) = 'object'", name="ck_screenshot_metadata"),
        CheckConstraint("source = 'manual' AND client_upload_id IS NULL", name="ck_screenshot_phase1"),
        CheckConstraint("file_hash ~ '^[0-9a-f]{64}$'", name="ck_screenshot_hash"),
        Index("ix_screenshots_recent", "project_id", text("uploaded_at DESC"), text("id DESC")),
        Index("ix_screenshots_filters", "project_id", "build_id", "locale_id", "situation_id", text("uploaded_at DESC"), text("id DESC")),
        Index("ix_screenshots_category", "project_id", "category_id"), Index("ix_screenshots_locale", "project_id", "locale_id"), Index("ix_screenshots_situation", "project_id", "situation_id"),
    )
    build_id: Mapped[UUID] = mapped_column(PGUUID)
    locale_id: Mapped[UUID] = mapped_column(PGUUID)
    category_id: Mapped[UUID] = mapped_column(PGUUID)
    situation_id: Mapped[UUID] = mapped_column(PGUUID)
    source: Mapped[str] = mapped_column(String(32))
    original_filename: Mapped[str] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    storage_key: Mapped[str] = mapped_column(Text, unique=True)
    file_hash: Mapped[str] = mapped_column(CHAR(64))
    media_type: Mapped[str] = mapped_column(String(32))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    metadata_version: Mapped[int] = mapped_column(Integer, server_default="1")
    capture_metadata: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"))
    client_upload_id: Mapped[UUID | None] = mapped_column(PGUUID)
