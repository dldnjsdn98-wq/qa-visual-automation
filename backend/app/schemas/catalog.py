import re
from uuid import UUID
from pydantic import field_validator
from .common import Closed, Patch, Audit, Slug, Name, Description
from backend.app.errors import DomainError


class ProjectCreate(Closed):
    slug: Slug
    name: Name
    description: Description = None


class ProjectPatch(Patch):
    name: Name = None
    description: Description = None


class Project(ProjectCreate, Audit):
    description: Description


class BuildCreate(Closed):
    label: Name
    description: Description = None


class BuildPatch(Patch):
    description: Description


class Build(BuildCreate, Audit):
    project_id: UUID
    description: Description


class LocaleCreate(Closed):
    code: str
    name: Name

    @field_validator("code")
    @classmethod
    def canonical_code(cls, value):
        match = re.fullmatch(r"([A-Za-z]{2,3})(?:-([A-Za-z]{4}))?(?:-([A-Za-z]{2}|[0-9]{3}))?", value)
        if not match:
            raise DomainError(code="UNSUPPORTED_LOCALE_CODE", field="body.code", reason="unsupported locale code")
        language, script, region = match.groups()
        return "-".join(p for p in [language.lower(), script.title() if script else None, region.upper() if region else None] if p)


class LocalePatch(Patch):
    name: Name


class Locale(LocaleCreate, Audit):
    project_id: UUID


class CategoryCreate(Closed):
    slug: Slug
    name: Name


class CategoryPatch(Patch):
    name: Name


class Category(CategoryCreate, Audit):
    project_id: UUID


class SituationCreate(CategoryCreate):
    category_id: UUID
    description: Description = None


class SituationPatch(ProjectPatch):
    pass


class Situation(SituationCreate, Audit):
    project_id: UUID
    description: Description
