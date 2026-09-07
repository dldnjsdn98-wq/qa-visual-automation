from sqlalchemy import select, delete, and_
from sqlalchemy.exc import SQLAlchemyError
from backend.app.models import Build, Locale, Situation, StringKey, StringEntry, SituationExpectedString as Mapping
from backend.app.repositories import catalog as repo
from backend.app.repositories.strings import key_by_string_id
from backend.app.errors import database_error


def validate(session, project_id, build_id, situation_id, locale_id=None, lock=False):
    repo.project(session, project_id)
    repo.get(session, Build, build_id, project_id, lock=lock)
    repo.get(session, Situation, situation_id, project_id)
    if locale_id is not None:
        repo.get(session, Locale, locale_id, project_id)


def mapping(session, project_id, build_id, situation_id):
    validate(session, project_id, build_id, situation_id)
    rows = session.execute(select(Mapping, StringKey).join(StringKey, and_(StringKey.project_id == Mapping.project_id, StringKey.id == Mapping.string_key_id)).where(Mapping.project_id == project_id, Mapping.build_id == build_id, Mapping.situation_id == situation_id).order_by(Mapping.position))
    return dict(project_id=project_id, build_id=build_id, situation_id=situation_id, items=[dict(string_key_id=k.id, string_id=k.string_id, position=m.position) for m, k in rows])


def replace(session, project_id, build_id, situation_id, string_ids):
    try:
        validate(session, project_id, build_id, situation_id, lock=True)
        keys = [key_by_string_id(session, project_id, value) for value in string_ids]
        session.execute(delete(Mapping).where(Mapping.project_id == project_id, Mapping.build_id == build_id, Mapping.situation_id == situation_id))
        session.add_all([Mapping(project_id=project_id, build_id=build_id, situation_id=situation_id, string_key_id=key.id, position=i) for i, key in enumerate(keys)])
        session.flush()
        result = mapping(session, project_id, build_id, situation_id)
        session.commit()
        return result
    except SQLAlchemyError as exc:
        session.rollback()
        raise database_error(exc) from None


def resolve(session, project_id, build_id, locale_id, situation_id):
    validate(session, project_id, build_id, situation_id, locale_id)
    rows = session.execute(select(Mapping, StringKey, StringEntry).join(StringKey, and_(StringKey.project_id == Mapping.project_id, StringKey.id == Mapping.string_key_id)).outerjoin(StringEntry, and_(StringEntry.project_id == Mapping.project_id, StringEntry.build_id == Mapping.build_id, StringEntry.locale_id == locale_id, StringEntry.string_key_id == Mapping.string_key_id)).where(Mapping.project_id == project_id, Mapping.build_id == build_id, Mapping.situation_id == situation_id).order_by(Mapping.position))
    items = [dict(string_key_id=k.id, string_id=k.string_id, position=m.position, entry_id=e.id if e else None, text=e.text if e else None, translation_status="present" if e else "missing") for m, k, e in rows]
    return dict(project_id=project_id, build_id=build_id, locale_id=locale_id, situation_id=situation_id, catalog_mode="current", items=items, total=len(items), missing_count=sum(i["translation_status"] == "missing" for i in items))
