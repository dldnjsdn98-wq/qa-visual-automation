from datetime import datetime
from uuid import UUID
from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from backend.app.db import Base


class Identity:
    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, server_default=func.gen_random_uuid())


class Audit:
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Scoped:
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), index=True)


def scope_fk(column, table):
    return ForeignKeyConstraint(["project_id", column], [f"{table}.project_id", f"{table}.id"], ondelete="RESTRICT")


class Project(Identity, Audit, Base):
    __tablename__ = "projects"
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)


class Build(Identity, Audit, Scoped, Base):
    __tablename__ = "builds"
    __table_args__ = (UniqueConstraint("project_id", "label"), UniqueConstraint("project_id", "id"))
    label: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)


class Locale(Identity, Audit, Scoped, Base):
    __tablename__ = "locales"
    __table_args__ = (UniqueConstraint("project_id", "code"), UniqueConstraint("project_id", "id"))
    code: Mapped[str] = mapped_column(String(63))
    name: Mapped[str] = mapped_column(String(120))


class Category(Identity, Audit, Scoped, Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("project_id", "slug"), UniqueConstraint("project_id", "id"))
    slug: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(120))


class Situation(Identity, Audit, Scoped, Base):
    __tablename__ = "situations"
    __table_args__ = (UniqueConstraint("project_id", "category_id", "slug"), UniqueConstraint("project_id", "id"), UniqueConstraint("project_id", "category_id", "id"), scope_fk("category_id", "categories"))
    category_id: Mapped[UUID] = mapped_column(PGUUID)
    slug: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
