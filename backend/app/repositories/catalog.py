from sqlalchemy import select, func
from backend.app.errors import not_found
from backend.app.models import Project


def get(session, model, identity, project_id=None, lock=False):
    statement = select(model).where(model.id == identity)
    if project_id is not None:
        statement = statement.where(model.project_id == project_id)
    if lock:
        statement = statement.with_for_update()
    row = session.scalar(statement)
    if row is None:
        raise not_found()
    return row


def project(session, identity):
    return get(session, Project, identity)


def page(session, model, predicates, limit, offset, recent=False):
    statement = select(model).where(*predicates)
    # The engine uses REPEATABLE READ: count and page share one snapshot,
    # including the case where offset is beyond the final row.
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    order = (model.uploaded_at.desc(), model.id.desc()) if recent else (model.created_at, model.id)
    return list(session.scalars(statement.order_by(*order).limit(limit).offset(offset))), total


def insert(session, model, values):
    row = model(**values)
    session.add(row)
    session.flush()
    return row
