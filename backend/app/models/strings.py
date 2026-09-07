from uuid import UUID
from sqlalchemy import String, Text, Integer, UniqueConstraint, CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from backend.app.db import Base
from .catalog import Identity, Audit, Scoped, scope_fk


class StringKey(Identity, Audit, Scoped, Base):
    __tablename__ = "string_keys"
    __table_args__ = (UniqueConstraint("project_id", "string_id"), UniqueConstraint("project_id", "id"))
    string_id: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)


class StringEntry(Identity, Audit, Scoped, Base):
    __tablename__ = "string_entries"
    __table_args__ = (
        UniqueConstraint("project_id", "build_id", "string_key_id", "locale_id"),
        scope_fk("build_id", "builds"), scope_fk("locale_id", "locales"), scope_fk("string_key_id", "string_keys"),
        CheckConstraint("char_length(text) <= 10000", name="ck_entry_text_length"),
        Index("ix_entries_catalog", "project_id", "build_id", "locale_id", "string_key_id"),
        Index("ix_entries_key", "project_id", "string_key_id"), Index("ix_entries_locale", "project_id", "locale_id"),
    )
    build_id: Mapped[UUID] = mapped_column(PGUUID)
    locale_id: Mapped[UUID] = mapped_column(PGUUID)
    string_key_id: Mapped[UUID] = mapped_column(PGUUID)
    text: Mapped[str] = mapped_column(Text)


class SituationExpectedString(Scoped, Base):
    __tablename__ = "situation_expected_strings"
    __table_args__ = (
        UniqueConstraint("project_id", "build_id", "situation_id", "position"),
        scope_fk("build_id", "builds"), scope_fk("situation_id", "situations"), scope_fk("string_key_id", "string_keys"),
        CheckConstraint("position >= 0", name="ck_expected_position"),
        Index("ix_expected_key", "project_id", "string_key_id"), Index("ix_expected_situation", "project_id", "situation_id"),
    )
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), primary_key=True, index=True)
    build_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)
    situation_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)
    string_key_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)
    position: Mapped[int] = mapped_column(Integer)
