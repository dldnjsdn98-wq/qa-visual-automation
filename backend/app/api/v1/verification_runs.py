from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response

from backend.app.api.dependencies import DB
from backend.app.errors import DomainError
from backend.app.schemas.common import Page
from backend.app.schemas.verification import (
    ExpectedItem,
    OcrRegion,
    OcrSummary,
    ProfileList,
    VerificationItem,
    VerificationRun,
    VerificationRunCreate,
    VerificationRunSummary,
    VerificationSummary,
)
from backend.app.services import verification_runs as service

from .catalog_routes import Pagination, query_guard


class RunHistoryQuery(Pagination):
    selection: Literal["all", "succeeded"] = "all"


router = APIRouter(
    prefix="/projects/{project_id}/screenshots/{screenshot_id}/verification-runs",
    tags=["verification-runs"],
)
profile_router = APIRouter(prefix="/projects/{project_id}/ocr-profiles", tags=["ocr-profiles"])


def _set_poll_header(response: Response, run: dict):
    if run["status"] in ("PENDING", "RUNNING", "RETRY_WAIT"):
        response.headers["Retry-After"] = "2"


@router.post(
    "",
    response_model=VerificationRun,
    status_code=202,
    responses={200: {"model": VerificationRun, "description": "Same client_run_id replay"}},
    dependencies=[query_guard()],
)
def create_run(
    project_id: UUID,
    screenshot_id: UUID,
    body: VerificationRunCreate,
    request: Request,
    response: Response,
    session: DB,
):
    if "idempotency-key" in request.headers:
        raise DomainError(field="header.Idempotency-Key", reason="Idempotency-Key is not supported; use client_run_id")
    outcome = service.create_or_replay(session, project_id, screenshot_id, body)
    response.status_code = 200 if outcome.replayed else 202
    response.headers["Location"] = (
        f"/api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs/{outcome.run['id']}"
    )
    response.headers["Idempotency-Replayed"] = str(outcome.replayed).lower()
    if not outcome.replayed:
        response.headers["Retry-After"] = "2"
    return outcome.run


@router.get("", response_model=Page[VerificationRunSummary], dependencies=[query_guard(*RunHistoryQuery.model_fields)])
def list_runs(
    project_id: UUID,
    screenshot_id: UUID,
    query: Annotated[RunHistoryQuery, Query()],
    session: DB,
):
    return service.list_runs(session, project_id, screenshot_id, query.selection, query.limit, query.offset)


@router.get("/{run_id}", response_model=VerificationRun, dependencies=[query_guard()])
def get_run(project_id: UUID, screenshot_id: UUID, run_id: UUID, response: Response, session: DB):
    run = service.get_run(session, project_id, screenshot_id, run_id)
    _set_poll_header(response, run)
    return run


@router.get("/{run_id}/expected", response_model=Page[ExpectedItem], dependencies=[query_guard(*Pagination.model_fields)])
def list_expected(
    project_id: UUID,
    screenshot_id: UUID,
    run_id: UUID,
    query: Annotated[Pagination, Query()],
    session: DB,
):
    return service.list_expected(session, project_id, screenshot_id, run_id, query.limit, query.offset)


@router.get("/{run_id}/ocr", response_model=OcrSummary, dependencies=[query_guard()])
def get_ocr(project_id: UUID, screenshot_id: UUID, run_id: UUID, session: DB):
    return service.get_ocr(session, project_id, screenshot_id, run_id)


@router.get("/{run_id}/ocr/regions", response_model=Page[OcrRegion], dependencies=[query_guard(*Pagination.model_fields)])
def list_regions(
    project_id: UUID,
    screenshot_id: UUID,
    run_id: UUID,
    query: Annotated[Pagination, Query()],
    session: DB,
):
    return service.list_regions(session, project_id, screenshot_id, run_id, query.limit, query.offset)


@router.get("/{run_id}/verification", response_model=VerificationSummary, dependencies=[query_guard()])
def get_verification(project_id: UUID, screenshot_id: UUID, run_id: UUID, session: DB):
    return service.get_verification(session, project_id, screenshot_id, run_id)


@router.get(
    "/{run_id}/verification/items",
    response_model=Page[VerificationItem],
    dependencies=[query_guard(*Pagination.model_fields)],
)
def list_verification_items(
    project_id: UUID,
    screenshot_id: UUID,
    run_id: UUID,
    query: Annotated[Pagination, Query()],
    session: DB,
):
    return service.list_verification_items(session, project_id, screenshot_id, run_id, query.limit, query.offset)


@profile_router.get("", response_model=ProfileList, dependencies=[query_guard()])
def list_profiles(project_id: UUID, session: DB):
    return service.list_profiles(session, project_id)
