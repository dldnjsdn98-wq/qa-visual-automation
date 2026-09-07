from datetime import datetime
from typing import Annotated, Generic, TypeVar
from uuid import UUID
from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator
from backend.app.validation.unicode import validate_unicode
from backend.app.errors import DomainError

Slug = Annotated[str, StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Description = Annotated[str, StringConstraints(max_length=2000)] | None
StringId = Annotated[str, StringConstraints(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
Text = Annotated[str, StringConstraints(max_length=10000)]


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def unicode_boundary(cls, value):
        return validate_unicode(value)


class Patch(Closed):
    @model_validator(mode="before")
    @classmethod
    def patch_presence(cls, value):
        if isinstance(value, dict):
            if not value:
                raise DomainError(field="body", reason="at least one field is required")
            for key, item in value.items():
                if item is None and key != "description":
                    raise DomainError(field=f"body.{key}", reason="null is not allowed")
        return value


class Audit(Closed):
    id: UUID
    created_at: datetime
    updated_at: datetime


T = TypeVar("T")
class Page(Closed, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorDetail(Closed):
    field: str | None
    reason: str


class ErrorBody(Closed):
    code: str
    message: str
    details: list[ErrorDetail]
    request_id: UUID


class Error(Closed):
    error: ErrorBody
