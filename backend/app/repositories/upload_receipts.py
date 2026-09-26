"""Locked receipt persistence. Transaction ownership belongs to the service."""
from datetime import timedelta

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

from backend.app.models import Screenshot, UploadReceipt

LEASE_SECONDS = 60
RENEW_INTERVAL_SECONDS = 20
MAX_GENERATION = 2**63 - 1


def begin_primary(session):
    # Must be the first connection acquisition on a fresh Session.
    session.connection(execution_options={"isolation_level": "READ COMMITTED"})
    session.execute(text("SET LOCAL lock_timeout = '5s'"))
    session.execute(text("SET LOCAL statement_timeout = '10s'"))
    session.execute(text("SET LOCAL idle_in_transaction_session_timeout = '10s'"))
    if session.scalar(text("SELECT pg_is_in_recovery()")):
        raise RuntimeError("Receipt operations require the primary")
    # PostgreSQL 17+ bounds the whole transaction too. Older supported servers
    # retain statement/lock/idle bounds; no external work belongs in this scope.
    if int(session.scalar(text("SHOW server_version_num"))) >= 170000:
        session.execute(text("SET LOCAL transaction_timeout = '15s'"))


def sample_db_clock(session):
    return session.scalar(select(func.clock_timestamp()))


def lock_receipt(session, project_id, client_upload_id):
    return session.scalar(select(UploadReceipt).where(
        UploadReceipt.project_id == project_id,
        UploadReceipt.client_upload_id == client_upload_id,
    ).with_for_update().execution_options(populate_existing=True))


def insert_first_attempt(session, intent, fence):
    """Unique-index arbitration also waits for an invisible competing INSERT."""
    result = session.execute(insert(UploadReceipt).values(
        project_id=intent.project_id, client_upload_id=intent.client_upload_id,
        fingerprint_version=1, upload_protocol_version=1,
        request_fingerprint=intent.request_fingerprint,
        canonical_request=intent.canonical_request, state="PROCESSING",
        attempt_generation=fence.attempt_generation, attempt_token=fence.attempt_token,
        candidate_screenshot_id=fence.candidate_screenshot_id,
        candidate_storage_key=fence.candidate_storage_key,
        lease_expires_at=fence.lease_expires_at,
        created_at=func.clock_timestamp(), updated_at=func.clock_timestamp(),
    ).on_conflict_do_nothing(index_elements=["project_id", "client_upload_id"])
      .returning(UploadReceipt.client_upload_id))
    return result.scalar_one_or_none() is not None


def owns(row, fence):
    return (row is not None and row.state == "PROCESSING"
            and row.project_id == fence.project_id
            and row.client_upload_id == fence.client_upload_id
            and row.request_fingerprint == fence.request_fingerprint
            and row.attempt_generation == fence.attempt_generation
            and row.attempt_token == fence.attempt_token
            and row.candidate_screenshot_id == fence.candidate_screenshot_id
            and row.candidate_storage_key == fence.candidate_storage_key)


def take_over_locked(session, row, now, fence):
    if not (row.state == "FAILED" or (
        row.state == "PROCESSING" and row.lease_expires_at <= now
    )):
        raise ValueError("Receipt is not eligible for takeover")
    if row.attempt_generation >= MAX_GENERATION:
        raise OverflowError("Receipt generation exhausted")
    if fence.attempt_generation != row.attempt_generation + 1:
        raise ValueError("Takeover must advance exactly one generation")
    row.state = "PROCESSING"
    row.attempt_generation = fence.attempt_generation
    row.attempt_token = fence.attempt_token
    row.candidate_screenshot_id = fence.candidate_screenshot_id
    row.candidate_storage_key = fence.candidate_storage_key
    row.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
    row.last_error_code = None
    row.updated_at = now
    session.flush()


def renew_locked(session, row, fence, now):
    if not owns(row, fence) or row.lease_expires_at <= now:
        return False
    row.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
    row.updated_at = now
    session.flush()
    return True


def mark_failed_locked(session, row, fence, now, error_code):
    if not owns(row, fence):
        return False
    row.state = "FAILED"
    row.lease_expires_at = None
    row.last_error_code = error_code
    row.updated_at = now
    session.flush()
    return True


def insert_screenshot(session, values):
    row = Screenshot(**values)
    session.add(row)
    session.flush()
    return row


def complete_locked(session, row, fence, screenshot, now):
    if not owns(row, fence) or row.lease_expires_at <= now:
        raise ValueError("Completion requires a live locked fence")
    row.state = "COMPLETED"
    row.screenshot_id = screenshot.id
    row.lease_expires_at = None
    row.last_error_code = None
    row.updated_at = now
    session.flush()


def load_completed_screenshot(session, row):
    screenshot = session.get(Screenshot, row.screenshot_id)
    if (screenshot is None or screenshot.project_id != row.project_id
            or screenshot.client_upload_id != row.client_upload_id
            or screenshot.id != row.candidate_screenshot_id
            or screenshot.storage_key != row.candidate_storage_key):
        raise RuntimeError("Completed receipt identity is inconsistent")
    return screenshot
