from uuid import UUID
from typing import Literal
from pydantic import Field, field_validator
from .common import Closed, Patch, Audit, StringId, Description, Text


class StringKeyCreate(Closed):
    string_id: StringId
    description: Description = None


class StringKeyPatch(Patch):
    description: Description


class StringKey(StringKeyCreate, Audit):
    project_id: UUID
    description: Description


class StringEntryCreate(Closed):
    build_id: UUID
    locale_id: UUID
    string_id: StringId
    text: Text


class StringEntryPatch(Patch):
    text: Text


class StringEntry(StringEntryCreate, Audit):
    project_id: UUID
    string_key_id: UUID


class ExpectedMappingReplace(Closed):
    string_ids: list[StringId] = Field(max_length=1000)

    @field_validator("string_ids")
    @classmethod
    def unique(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("duplicate string_id")
        return value


class ExpectedKey(Closed):
    string_key_id: UUID
    string_id: StringId
    position: int


class ExpectedMapping(Closed):
    project_id: UUID
    build_id: UUID
    situation_id: UUID
    items: list[ExpectedKey]


class ExpectedString(ExpectedKey):
    entry_id: UUID | None
    text: Text | None
    translation_status: Literal["present", "missing"]


class ExpectedStrings(Closed):
    project_id: UUID
    build_id: UUID
    locale_id: UUID
    situation_id: UUID
    catalog_mode: Literal["current"]
    items: list[ExpectedString]
    total: int
    missing_count: int
