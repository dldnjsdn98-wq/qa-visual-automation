from sqlalchemy import select, func
from backend.app.errors import not_found
from backend.app.models import Project


def get(session, model, identity, project_id=None, lock=False, key_share=False):
    if lock and key_share:
        raise ValueError("choose one catalog row lock mode")
    statement = select(model).where(model.id == identity)
    if project_id is not None:
        statement = statement.where(model.project_id == project_id)
    if key_share:
        # FOR KEY SHARE prevents DELETE/key changes while allowing unrelated
        # non-key updates. Receipt transactions set a five-second lock timeout.
        statement = statement.with_for_update(read=True, key_share=True)
    elif lock:
        statement = statement.with_for_update()
    row = session.scalar(statement)
    if row is None:
        raise not_found()
    return row


def project(session, identity, lock=False, key_share=False):
    return get(session, Project, identity, lock=lock, key_share=key_share)


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
