from datetime import datetime
from uuid import UUID
from typing import Annotated, Literal, Any
from pydantic import Field, UUID4, field_validator, model_validator
from pydantic.json_schema import SkipJsonSchema
from .common import Closed
from backend.app.validation.metadata import validate_metadata


class ScreenshotUpload(Closed):
    build_id: UUID
    locale_id: UUID
    category_id: UUID
    situation_id: UUID
    source: Literal["manual"]
    metadata_version: Literal[1] = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata_version", mode="before")
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError("metadata_version must be integer 1")
        return value

    @field_validator("metadata")
    @classmethod
    def bounded_metadata(cls, value):
        return validate_metadata(value)


class AgentScreenshotUpload(Closed):
    upload_protocol_version: Literal[1]
    client_upload_id: UUID4
    build_id: UUID
    locale_id: UUID
    category_id: UUID
    situation_id: UUID
    source: Literal["agent", "automation"]
    metadata_version: Literal[1] = 1
    metadata: dict[str, Any] = Field(default_factory=dict)
    expected_file_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | SkipJsonSchema[None] = Field(default=None, json_schema_extra=lambda schema: schema.pop("default", None))

    @field_validator("expected_file_hash", mode="before")
    @classmethod
    def supplied_hash_is_not_null(cls, value):
        if value is None:
            raise ValueError("expected_file_hash must be omitted or a lowercase SHA-256 hex string")
        return value

    @field_validator("upload_protocol_version", "metadata_version", mode="before")
    @classmethod
    def integer_versions(cls, value):
        if type(value) is not int:
            raise ValueError("version must be integer 1")
        return value

    @field_validator("metadata")
    @classmethod
    def bounded_metadata(cls, value):
        return validate_metadata(value)


class Screenshot(Closed):
    id: UUID
    project_id: UUID
    build_id: UUID
    locale_id: UUID
    category_id: UUID
    situation_id: UUID
    source: Literal["manual", "agent", "automation"]
    original_filename: str
    uploaded_at: datetime
    file_hash: str
    media_type: Literal["image/png", "image/jpeg"]
    size_bytes: int
    width: int
    height: int
    metadata_version: Literal[1]
    metadata: dict[str, Any]
    client_upload_id: UUID | None
    content_url: str

    @model_validator(mode="after")
    def source_identity_pair(self):
        if (self.source == "manual") != (self.client_upload_id is None):
            raise ValueError("source and client_upload_id do not form a valid pair")
        return self
