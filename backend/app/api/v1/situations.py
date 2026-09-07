from uuid import UUID
from backend.app.models import Situation
from backend.app.schemas import catalog as schema
from backend.app.schemas.strings import ExpectedMappingReplace, ExpectedMapping, ExpectedStrings
from backend.app.services import expected_strings
from backend.app.api.dependencies import DB
from .catalog_routes import scoped_router, SituationFilter, query_guard

router = scoped_router("situations", "situation_id", Situation, schema.SituationCreate, schema.SituationPatch, schema.Situation, SituationFilter)


@router.get("/{situation_id}/expected-string-keys", response_model=ExpectedMapping, dependencies=[query_guard("build_id")])
def get_mapping(project_id: UUID, situation_id: UUID, build_id: UUID, session: DB):
    return expected_strings.mapping(session, project_id, build_id, situation_id)


@router.put("/{situation_id}/expected-string-keys", response_model=ExpectedMapping, dependencies=[query_guard("build_id")])
def replace_mapping(project_id: UUID, situation_id: UUID, build_id: UUID, body: ExpectedMappingReplace, session: DB):
    return expected_strings.replace(session, project_id, build_id, situation_id, body.string_ids)


@router.get("/{situation_id}/expected-strings", response_model=ExpectedStrings, dependencies=[query_guard("build_id", "locale_id")])
def get_expected(project_id: UUID, situation_id: UUID, build_id: UUID, locale_id: UUID, session: DB):
    return expected_strings.resolve(session, project_id, build_id, locale_id, situation_id)
