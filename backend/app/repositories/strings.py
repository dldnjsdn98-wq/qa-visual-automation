from sqlalchemy import select
from backend.app.models import StringKey
from backend.app.errors import not_found


def key_by_string_id(session, project_id, string_id):
    row = session.scalar(select(StringKey).where(StringKey.project_id == project_id, StringKey.string_id == string_id))
    if row is None:
        raise not_found()
    return row
