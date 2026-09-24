import logging
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from backend.app.models import Screenshot
from backend.app.repositories import catalog as repo
from backend.app.services.catalog import validate_references
from backend.app.errors import DomainError, database_error

log = logging.getLogger(__name__)


def serialize(row):
    result = {column.key: getattr(row, column.key) for column in row.__mapper__.column_attrs if column.key != "storage_key"}
    result["metadata"] = result.pop("capture_metadata")
    result["content_url"] = f"/api/v1/projects/{row.project_id}/screenshots/{row.id}/content"
    return result


def cleanup(storage, key):
    try:
        storage.delete(key)
    except OSError:
        log.error("Compensation failed; retain for maintenance: %s", key)


def upload(session, storage, project_id, metadata, stream, filename, media_type):
    values = metadata.model_dump()
    validate_references(session, project_id, values, field_prefix="metadata")
    session.rollback()  # End read snapshot before decoding/storage I/O.
    staged = None
    try:
        staged = storage.stage(stream, 20_971_520)
        facts = storage.inspect(staged, media_type)
        if "resolution" in values["metadata"] and values["metadata"]["resolution"] != {"width": facts.width, "height": facts.height}:
            raise DomainError(field="metadata.metadata.resolution", reason="resolution must match decoded image")
        identity = uuid4()
        key = f"objects/{project_id}/{identity}.{facts.extension}"
        storage.publish(staged, key)
        # From here, only a known rollback authorizes compensation.
        try:
            session.connection(execution_options={"isolation_level": "READ COMMITTED"})
            validate_references(session, project_id, values, field_prefix="metadata")
            values["capture_metadata"] = values.pop("metadata")
            row = repo.insert(session, Screenshot, dict(values, id=identity, project_id=project_id, original_filename=filename, storage_key=key, file_hash=staged.sha256, media_type=facts.media_type, size_bytes=staged.byte_count, width=facts.width, height=facts.height))
            result = serialize(row)
        except BaseException:
            try:
                session.rollback()
            finally:
                cleanup(storage, key)
            raise
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            cleanup(storage, key)
            raise database_error(exc) from None
        except SQLAlchemyError:
            # Commit may have reached primary; never delete on uncertainty.
            session.invalidate()
            try:
                with Session(session.get_bind()) as recovery:
                    committed = recovery.get(Screenshot, identity)
                    if committed is not None:
                        return serialize(committed)
            except SQLAlchemyError:
                pass
            log.error("Ambiguous upload commit; retained object %s", key)
            raise DomainError(503, "DATABASE_UNAVAILABLE", "Upload outcome is uncertain; inspect screenshot list") from None
        return result
    except SQLAlchemyError as exc:
        raise database_error(exc) from None
    except OSError:
        raise DomainError(503, "STORAGE_UNAVAILABLE", "Storage unavailable") from None
    finally:
        if staged:
            try:
                storage.discard_stage(staged.token)
            except OSError:
                log.error("Staging cleanup failed: %s", staged.token)


def read_content(storage, row):
    try:
        stream, size = storage.open_read(row.storage_key)
        try:
            content = stream.read(row.size_bytes + 1)
        finally:
            stream.close()
        if size != row.size_bytes or len(content) != row.size_bytes:
            raise OSError()
        return content
    except OSError:
        log.error("Referenced screenshot object unavailable: %s", row.id)
        raise DomainError(503, "STORAGE_UNAVAILABLE", "Screenshot content unavailable") from None
