from sqlalchemy.exc import SQLAlchemyError
from backend.app.models import Project, Build, Locale, Category, Situation, StringEntry
from backend.app.repositories import catalog as repo
from backend.app.repositories.strings import key_by_string_id
from backend.app.errors import database_error, DomainError


def validate_references(session, project_id, values, field_prefix="body"):
    repo.project(session, project_id)
    for field, model in (("build_id", Build), ("locale_id", Locale), ("category_id", Category), ("situation_id", Situation)):
        if values.get(field) is not None:
            row = repo.get(session, model, values[field], project_id)
            if field == "situation_id" and values.get("category_id") is not None and row.category_id != values["category_id"]:
                raise DomainError(code="RELATIONSHIP_MISMATCH", field=f"{field_prefix}.situation_id", reason="situation does not belong to category")


def serialize(session, row):
    values = {column.key: getattr(row, column.key) for column in row.__mapper__.column_attrs}
    if isinstance(row, StringEntry):
        from backend.app.models import StringKey
        values["string_id"] = repo.get(session, StringKey, row.string_key_id, row.project_id).string_id
    return values


def create(session, model, values, project_id=None):
    values = dict(values)
    try:
        session.connection(execution_options={"isolation_level": "READ COMMITTED"})
        if project_id is not None:
            validate_references(session, project_id, values)
            values["project_id"] = project_id
        if model is StringEntry:
            values["string_key_id"] = key_by_string_id(session, project_id, values.pop("string_id")).id
        row = repo.insert(session, model, values)
        result = serialize(session, row)
        session.commit()
        return result
    except SQLAlchemyError as exc:
        session.rollback()
        raise database_error(exc) from None


def patch(session, model, identity, values, project_id=None):
    try:
        session.connection(execution_options={"isolation_level": "READ COMMITTED"})
        if project_id is not None:
            repo.project(session, project_id)
        row = repo.get(session, model, identity, project_id)
        for key, value in values.items():
            setattr(row, key, value)
        session.flush()
        result = serialize(session, row)
        session.commit()
        return result
    except SQLAlchemyError as exc:
        session.rollback()
        raise database_error(exc) from None


def delete(session, model, identity, project_id=None):
    try:
        session.connection(execution_options={"isolation_level": "READ COMMITTED"})
        if project_id is not None:
            repo.project(session, project_id)
        row = repo.get(session, model, identity, project_id)
        session.delete(row)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise database_error(exc) from None
