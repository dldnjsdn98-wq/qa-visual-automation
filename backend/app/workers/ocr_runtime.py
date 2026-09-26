"""Parent-only metadata and single-operation DB execution boundary."""
import hashlib
import json
import threading
import time
from sqlalchemy import select
from backend.app.models import VerificationRun
from backend.app.services.ocr_types import OutcomeUnknown
from backend.app.workers import ocr_admission

MAX_SOURCE_BYTES = 20_971_520

class DeadlinePolicy:
    def __init__(self, deadline=float("inf")):
        self.deadline = deadline
        self.suspended = False
        self.timeout_failure = False

    def guard(self, operation, retry_index):
        if self.suspended:
            raise OutcomeUnknown("Runner is quarantined")
        if time.monotonic() >= self.deadline:
            if operation == "fail" and self.timeout_failure and retry_index == 0:
                return
            raise RuntimeError("ENGINE_TIMEOUT")

    def allow_timeout_failure(self):
        if self.suspended or self.timeout_failure:
            raise OutcomeUnknown("Timeout failure cannot be issued")
        self.timeout_failure = True


class OneOperation:
    """A hung parent driver never blocks supervision or permits a second operation."""
    def __init__(self):
        self.thread = None
        self.done = threading.Event()
        self.name = None
        self.value = None
        self.error = None

    @property
    def pending(self):
        return self.thread is not None and not self.done.is_set()

    @property
    def occupied(self):
        return self.thread is not None

    def start(self, name, action):
        if self.occupied:
            raise OutcomeUnknown("Another parent operation is unsettled")
        self.name, self.value, self.error = name, None, None
        self.done.clear()
        def execute():
            try:
                self.value = action()
            except BaseException as exc:
                self.error = exc
            finally:
                self.done.set()
        self.thread = threading.Thread(target=execute, name="ocr-parent-db", daemon=True)
        self.thread.start()

    def take(self):
        if not self.occupied or not self.done.is_set():
            raise OutcomeUnknown("Parent operation has not settled")
        self.thread.join(timeout=0.1)
        if self.thread.is_alive():
            raise OutcomeUnknown("Parent operation thread has not exited")
        self.thread = None
        if self.error is not None:
            raise self.error
        return self.value


def load_metadata(session_factory, storage_root, claim):
    with session_factory() as session:
        row = session.scalar(select(VerificationRun).where(
            VerificationRun.project_id == claim.fence.project_id,
            VerificationRun.id == claim.fence.run_id,
        ))
        if row is None:
            raise RuntimeError("SNAPSHOT_INTEGRITY_ERROR")
        values = {}
        for name, digest in (
            ("snapshot_canonical", row.snapshot_sha256),
            ("configuration_canonical", row.configuration_sha256),
            ("profile_canonical", row.profile_digest),
        ):
            raw = bytes(getattr(row, name))
            if len(raw) > 8 * 1024 * 1024:
                raise RuntimeError("SNAPSHOT_INTEGRITY_ERROR")
            if hashlib.sha256(raw).hexdigest() != digest:
                code = "SNAPSHOT_INTEGRITY_ERROR" if name == "snapshot_canonical" else "PROFILE_DIGEST_MISMATCH"
                raise RuntimeError(code)
            values[name] = json.loads(raw)
        storage_key = row.screenshot_storage_key
        expected_size = row.screenshot_size_bytes
        expected_hash = row.screenshot_file_hash
        facts = {
            "source_sha256": row.screenshot_file_hash, "size": row.screenshot_size_bytes,
            "mime_type": row.screenshot_media_type, "width": row.screenshot_width,
            "height": row.screenshot_height, "locale_code": row.locale_code,
            "ocr_language": row.ocr_language,
        }
        snapshot_sha256 = row.snapshot_sha256
        configuration_sha256 = row.configuration_sha256
        profile_id, profile_digest = row.profile_id, row.profile_digest
    # This is the same deployment admission provider used by the API. A run
    # admitted before a release/readiness change still settles durably as
    # unavailable; it must not be silently skipped or use an alternate profile.
    if not ocr_admission.admitted(profile_id, profile_digest):
        raise RuntimeError("ENGINE_UNAVAILABLE")
    snapshot = values["snapshot_canonical"]
    configuration = values["configuration_canonical"]
    expected_snapshot = {
        "snapshot_version": snapshot["snapshot_version"],
        "sha256": snapshot_sha256,
        "items": snapshot["expected_items"],
        "captured_at": snapshot["captured_at"],
        "source_mode": snapshot["source_mode"],
        "locale_code": facts["locale_code"],
        "ocr_language": snapshot["ocr_language"],
        "screenshot": snapshot["screenshot"],
        "item_count": snapshot["item_count"],
        "missing_count": snapshot["missing_count"],
    }
    verification_config = {
        "configuration_sha256": configuration_sha256,
        "pass_threshold": configuration["pass_threshold"],
        "review_threshold": configuration["review_threshold"],
        "normalization_version": configuration["normalization_version"],
        "matching_version": configuration["matching_version"],
    }
    if type(expected_size) is not int or not 1 <= expected_size <= MAX_SOURCE_BYTES:
        raise RuntimeError("SNAPSHOT_INTEGRITY_ERROR")
    return {"source": {"root": storage_root, "key": storage_key,
                       "size": expected_size, "sha256": expected_hash},
            "source_facts": facts, "profile_manifest": values["profile_canonical"],
            "expected_snapshot": expected_snapshot, "verification_config": verification_config}
