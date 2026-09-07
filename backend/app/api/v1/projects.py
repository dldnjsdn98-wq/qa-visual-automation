from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Query, Response
from backend.app.models import Project as Model
from backend.app.schemas.catalog import Project, ProjectCreate, ProjectPatch
from backend.app.schemas.common import Page
from backend.app.api.dependencies import DB
from backend.app.repositories import catalog as repo
from backend.app.services import catalog as service
from .catalog_routes import Pagination, query_guard

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=Page[Project], dependencies=[query_guard("limit", "offset")])
def list_projects(query: Annotated[Pagination, Query()], session: DB):
    rows, total = repo.page(session, Model, [], query.limit, query.offset)
    return dict(items=rows, total=total, limit=query.limit, offset=query.offset)


@router.post("", response_model=Project, status_code=201, dependencies=[query_guard()])
def create_project(body: ProjectCreate, response: Response, session: DB):
    result = service.create(session, Model, body.model_dump())
    response.headers["Location"] = f"/api/v1/projects/{result['id']}"
    return result


@router.get("/{project_id}", response_model=Project, dependencies=[query_guard()])
def get_project(project_id: UUID, session: DB):
    return repo.project(session, project_id)


@router.patch("/{project_id}", response_model=Project, dependencies=[query_guard()])
def patch_project(project_id: UUID, body: ProjectPatch, session: DB):
    return service.patch(session, Model, project_id, body.model_dump(exclude_unset=True))


@router.delete("/{project_id}", status_code=204, dependencies=[query_guard()])
def delete_project(project_id: UUID, session: DB):
    service.delete(session, Model, project_id)
    return Response(status_code=204)
