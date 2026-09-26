import hashlib
import logging
import threading
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from backend.app.models import Screenshot
from backend.app.repositories import catalog as repo
from backend.app.services.catalog import validate_references
from backend.app.services import upload_receipts
from backend.app.services.upload_types import NOOP_UPLOAD_FAULTS, ReservationState, UploadOutcome
from backend.app.validation.jcs import canonicalize_fingerprint
from backend.app.errors import DomainError, database_error
from backend.app.storage.base import ObjectExists

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


def upload_manual(session, storage, project_id, metadata, stream, filename, media_type):
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
                        return UploadOutcome(serialize(committed), 201, None)
            except SQLAlchemyError:
                pass
            log.error("Ambiguous upload commit; retained object %s", key)
            raise DomainError(503, "DATABASE_UNAVAILABLE", "Upload outcome is uncertain; inspect screenshot list") from None
        return UploadOutcome(result, 201, None)
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


class LeaseKeeper:
    def __init__(self, factory, fence, intent, faults):
        self.factory = factory
        self.fence = fence
        self.intent = intent
        self.faults = faults
        self.stop = threading.Event()
        self.failure = None
        self.outcome = None
        self.thread = threading.Thread(target=self._run, name="upload-lease-renewer", daemon=True)

    def start(self):
        self.thread.start()

    def _run(self):
        while not self.stop.wait(upload_receipts.RENEW_INTERVAL_SECONDS):
            try:
                if not upload_receipts.renew_attempt(self.factory, self.fence, faults=self.faults):
                    self.outcome = upload_receipts.recover_finalize_commit(
                        self.factory,
                        self.fence,
                        self.intent,
                    )
                    self.stop.set()
                    return
            except BaseException as exc:
                self.failure = exc
                self.stop.set()
                return

    def stop_and_join(self):
        self.stop.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise DomainError(503, "DATABASE_UNAVAILABLE", "Lease renewal did not stop", retry_after=5)
        if self.failure is not None:
            raise self.failure
        return self.outcome


def _agent_outcome(reservation):
    if reservation.state == ReservationState.REPLAY:
        return UploadOutcome(reservation.screenshot, 200, True)
    if reservation.state == ReservationState.CONFLICT:
        raise DomainError(409, "IDEMPOTENCY_CONFLICT", "Upload identity conflicts")
    if reservation.state == ReservationState.IN_PROGRESS:
        raise DomainError(409, "UPLOAD_IN_PROGRESS", "Upload in progress", retry_after=reservation.retry_after or 1)
    return None


def upload_agent(session, storage, project_id, metadata, stream, filename, media_type, *, faults=NOOP_UPLOAD_FAULTS):
    values = metadata.model_dump()
    staged = None
    published = False
    try:
        staged = storage.stage(stream, 20_971_520)
        facts = storage.inspect(staged, media_type)
        if values.get("expected_file_hash") is not None and values["expected_file_hash"] != staged.sha256:
            raise DomainError(field="metadata.expected_file_hash", reason="expected hash does not match received file")
        if "resolution" in values["metadata"] and values["metadata"]["resolution"] != {"width": facts.width, "height": facts.height}:
            raise DomainError(field="metadata.metadata.resolution", reason="resolution must match decoded image")
        faults.hit("AFTER_STAGE_BEFORE_RESERVE", None)

        # Only the path project is checked before receipt comparison. Scoped
        # context is checked transactionally for a new/takeover generation.
        repo.project(session, project_id)
        session.rollback()
        client_upload_id = values.pop("client_upload_id")
        expected_file_hash = values.pop("expected_file_hash", None)
        payload = {
            "fingerprint_version": 1,
            "upload_protocol_version": values.pop("upload_protocol_version"),
            "project_id": str(project_id),
            "build_id": str(values["build_id"]),
            "locale_id": str(values["locale_id"]),
            "category_id": str(values["category_id"]),
            "situation_id": str(values["situation_id"]),
            "source": values["source"],
            "original_filename": filename,
            "metadata_version": values["metadata_version"],
            "metadata": values["metadata"],
            "file_hash": staged.sha256,
            "media_type": facts.media_type,
            "size_bytes": staged.byte_count,
            "width": facts.width,
            "height": facts.height,
        }
        canonical, fingerprint = canonicalize_fingerprint(payload)
        intent = upload_receipts.UploadIntent(project_id, client_upload_id, canonical, fingerprint)
        factory = sessionmaker(session.get_bind(), expire_on_commit=False)
        reservation = upload_receipts.reserve_or_replay(factory, intent, faults=faults)
        terminal = _agent_outcome(reservation)
        if terminal is not None:
            return terminal

        fence = reservation.fence
        keeper = LeaseKeeper(factory, fence, intent, faults)
        keeper.start()
        fenced_outcome = None
        try:
            try:
                storage.publish(staged, fence.candidate_storage_key)
                published = True
            except ObjectExists:
                storage.verify_exact(
                    fence.candidate_storage_key,
                    sha256=staged.sha256,
                    byte_count=staged.byte_count,
                )
                published = True
            faults.hit("AFTER_PUBLISH_BEFORE_FINALIZE", {"fence": fence})
        finally:
            fenced_outcome = keeper.stop_and_join()
        if fenced_outcome is not None:
            return fenced_outcome
        return upload_receipts.finalize_attempt(factory, fence, intent, faults=faults)
    except SQLAlchemyError as exc:
        raise database_error(exc) from None
    except OSError:
        # Published agent objects are never request-worker compensation targets.
        raise DomainError(503, "STORAGE_UNAVAILABLE", "Storage unavailable", retry_after=5) from None
    finally:
        if staged:
            try:
                storage.discard_stage(staged.token)
            except OSError:
                log.error("Staging cleanup failed: %s", staged.token)


def upload(session, storage, project_id, metadata, stream, filename, media_type, *, faults=NOOP_UPLOAD_FAULTS):
    if metadata.source == "manual":
        return upload_manual(session, storage, project_id, metadata, stream, filename, media_type)
    return upload_agent(session, storage, project_id, metadata, stream, filename, media_type, faults=faults)


def read_content(storage, row):
    try:
        stream, size = storage.open_read(row.storage_key)
        try:
            content = stream.read(row.size_bytes + 1)
        finally:
            stream.close()
        if (
            size != row.size_bytes
            or len(content) != row.size_bytes
            or hashlib.sha256(content).hexdigest() != row.file_hash
        ):
            raise OSError()
        return content
    except OSError:
        log.error("Referenced screenshot object unavailable: %s", row.id)
        raise DomainError(503, "STORAGE_UNAVAILABLE", "Screenshot content unavailable") from None
