from datetime import datetime
from uuid import UUID
from typing import Literal, Any
from pydantic import Field, field_validator
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
    source: Literal["manual"]
    original_filename: str
    uploaded_at: datetime
    file_hash: str
    media_type: Literal["image/png", "image/jpeg"]
    size_bytes: int
    width: int
    height: int
    metadata_version: Literal[1]
    metadata: dict[str, Any]
    client_upload_id: None
    content_url: str
