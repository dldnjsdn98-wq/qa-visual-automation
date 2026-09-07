from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Request, Response, Query, Depends
from pydantic import AwareDatetime, model_validator, ValidationError
from starlette.concurrency import run_in_threadpool
from backend.app.api.dependencies import DB, get_storage
from backend.app.schemas.screenshots import Screenshot, ScreenshotUpload
from backend.app.schemas.strings import ExpectedStrings
from backend.app.schemas.common import Page
from backend.app.models import Screenshot as Model
from backend.app.repositories import catalog as repo
from backend.app.services import screenshots as service, expected_strings
from backend.app.services.catalog import validate_references
from backend.app.validation.multipart import parse_upload
from backend.app.errors import DomainError
from .catalog_routes import Pagination, query_guard


class ScreenshotFilter(Pagination):
    build_id: UUID | None = None
    locale_id: UUID | None = None
    category_id: UUID | None = None
    situation_id: UUID | None = None
    source: Literal["manual"] | None = None
    uploaded_from: AwareDatetime | None = None
    uploaded_to: AwareDatetime | None = None

    @model_validator(mode="after")
    def range_order(self):
        if self.uploaded_from and self.uploaded_to and self.uploaded_from >= self.uploaded_to:
            raise DomainError(field="query.uploaded_from", reason="from must be earlier than to")
        return self


router = APIRouter(prefix="/projects/{project_id}/screenshots", tags=["screenshots"])
upload_schema = {"requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"type": "object", "additionalProperties": False, "required": ["file", "metadata"], "properties": {"file": {"type": "string", "format": "binary", "description": "One original PNG/JPEG, <=20 MiB"}, "metadata": {"type": "string", "description": "JSON-serialized ScreenshotUpload; browser sets multipart boundary", "contentMediaType": "application/json"}}}}}}}


@router.post("", response_model=Screenshot, status_code=201, dependencies=[query_guard()], openapi_extra=upload_schema)
async def upload(project_id: UUID, request: Request, response: Response, session: DB, storage=Depends(get_storage)):
    if "idempotency-key" in request.headers:
        raise DomainError(field="body", reason="Idempotency-Key is not supported in Phase 1")
    values, stream, filename, media_type = await run_in_threadpool(parse_upload, request.headers.get("content-type", ""), await request.body())
    try:
        metadata = ScreenshotUpload.model_validate(values)
    except ValidationError as exc:
        from backend.app.api.middleware import validation_error
        raise validation_error(exc, "metadata") from None
    result = await run_in_threadpool(service.upload, session, storage, project_id, metadata, stream, filename, media_type)
    response.headers["Location"] = f"/api/v1/projects/{project_id}/screenshots/{result['id']}"
    return result


@router.get("", response_model=Page[Screenshot], dependencies=[query_guard(*ScreenshotFilter.model_fields)])
def list_screenshots(project_id: UUID, query: Annotated[ScreenshotFilter, Query()], session: DB):
    values = query.model_dump(exclude_none=True)
    validate_references(session, project_id, values)
    predicates = [Model.project_id == project_id]
    for key, value in values.items():
        if key == "uploaded_from":
            predicates.append(Model.uploaded_at >= value)
        elif key == "uploaded_to":
            predicates.append(Model.uploaded_at < value)
        elif key not in ("limit", "offset"):
            predicates.append(getattr(Model, key) == value)
    rows, total = repo.page(session, Model, predicates, query.limit, query.offset, recent=True)
    return dict(items=[service.serialize(row) for row in rows], total=total, limit=query.limit, offset=query.offset)


def lookup(session, project_id, screenshot_id):
    repo.project(session, project_id)
    return repo.get(session, Model, screenshot_id, project_id)


@router.get("/{screenshot_id}", response_model=Screenshot, dependencies=[query_guard()])
def detail(project_id: UUID, screenshot_id: UUID, session: DB):
    return service.serialize(lookup(session, project_id, screenshot_id))


@router.get("/{screenshot_id}/expected-strings", response_model=ExpectedStrings, dependencies=[query_guard()])
def expected(project_id: UUID, screenshot_id: UUID, session: DB):
    row = lookup(session, project_id, screenshot_id)
    return expected_strings.resolve(session, project_id, row.build_id, row.locale_id, row.situation_id)


@router.get("/{screenshot_id}/content", dependencies=[query_guard()], response_class=Response, responses={200: {"content": {"image/png": {}, "image/jpeg": {}}}})
def content(project_id: UUID, screenshot_id: UUID, session: DB, storage=Depends(get_storage)):
    row = lookup(session, project_id, screenshot_id)
    data = service.read_content(storage, row)
    ext = "png" if row.media_type == "image/png" else "jpg"
    return Response(data, media_type=row.media_type, headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private,max-age=3600", "Content-Disposition": f'inline; filename="{row.id}.{ext}"'})
