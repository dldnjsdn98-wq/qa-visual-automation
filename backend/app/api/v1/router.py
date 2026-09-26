from fastapi import APIRouter
from backend.app.schemas.common import Error
from . import projects, builds, locales, categories, situations, string_keys, strings, screenshots, verification_runs

router = APIRouter(prefix="/api/v1", responses={status: {"model": Error} for status in (400, 404, 405, 409, 413, 415, 422, 500, 503)})
for module in (projects, builds, locales, categories, situations, string_keys, strings, screenshots):
    router.include_router(module.router)
router.include_router(verification_runs.router)
router.include_router(verification_runs.profile_router)
