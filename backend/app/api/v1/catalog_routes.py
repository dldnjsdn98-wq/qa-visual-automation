from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Query, Path, Request, Response, Depends
from pydantic import Field
from backend.app.schemas.common import Closed, Page, StringId
from backend.app.api.dependencies import DB
from backend.app.repositories import catalog as repo
from backend.app.repositories.strings import key_by_string_id
from backend.app.services import catalog as service
from backend.app.errors import DomainError


class Pagination(Closed):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SituationFilter(Pagination):
    category_id: UUID | None = None


class StringKeyFilter(Pagination):
    string_id: StringId | None = None


class StringFilter(StringKeyFilter):
    build_id: UUID | None = None
    locale_id: UUID | None = None


def query_guard(*allowed):
    def guard(request: Request):
        for key in request.query_params:
            if key not in allowed or len(request.query_params.getlist(key)) != 1:
                raise DomainError(field=f"query.{key}", reason="unknown or repeated query parameter")
    return Depends(guard)


def scoped_router(collection, identity_name, model, create_schema, patch_schema, response_schema, filters=Pagination):
    router = APIRouter(prefix=f"/projects/{{project_id}}/{collection}", tags=[collection])
    item_path = "/{" + identity_name + "}"

    def list_items(project_id: UUID, query: Annotated[filters, Query()], session: DB):
        values = query.model_dump(exclude_none=True)
        service.validate_references(session, project_id, values, field_prefix="query")
        predicates = [model.project_id == project_id]
        for key, value in values.items():
            if key in ("limit", "offset"):
                continue
            if key == "string_id":
                found = key_by_string_id(session, project_id, value)
                predicates.append(model.string_key_id == found.id if collection == "strings" else model.string_id == value)
            else:
                predicates.append(getattr(model, key) == value)
        rows, total = repo.page(session, model, predicates, query.limit, query.offset)
        return dict(items=[service.serialize(session, row) for row in rows], total=total, limit=query.limit, offset=query.offset)

    def create_item(project_id: UUID, body: create_schema, response: Response, session: DB):
        result = service.create(session, model, body.model_dump(), project_id)
        response.headers["Location"] = f"/api/v1/projects/{project_id}/{collection}/{result['id']}"
        return result

    def get_item(project_id: UUID, identity: Annotated[UUID, Path(alias=identity_name)], session: DB):
        repo.project(session, project_id)
        return service.serialize(session, repo.get(session, model, identity, project_id))

    def patch_item(project_id: UUID, identity: Annotated[UUID, Path(alias=identity_name)], body: patch_schema, session: DB):
        return service.patch(session, model, identity, body.model_dump(exclude_unset=True), project_id)

    def delete_item(project_id: UUID, identity: Annotated[UUID, Path(alias=identity_name)], session: DB):
        service.delete(session, model, identity, project_id)
        return Response(status_code=204)

    for endpoint, path, method, schema, status, allowed in (
        (list_items, "", "GET", Page[response_schema], 200, tuple(filters.model_fields)),
        (create_item, "", "POST", response_schema, 201, ()),
        (get_item, item_path, "GET", response_schema, 200, ()),
        (patch_item, item_path, "PATCH", response_schema, 200, ()),
        (delete_item, item_path, "DELETE", None, 204, ()),
    ):
        endpoint.__name__ = f"{method.lower()}_{collection.replace('-', '_')}_{'item' if path else 'collection'}"
        router.add_api_route(path, endpoint, methods=[method], response_model=schema, status_code=status, dependencies=[query_guard(*allowed)])
    return router
