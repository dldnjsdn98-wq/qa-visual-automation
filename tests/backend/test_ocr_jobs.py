"""PostgreSQL concurrency and recovery tests for P3-OCR-v1 durable jobs."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from hashlib import sha256
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from backend.app.models import (
    OCRResult,
    VerificationAttempt,
    VerificationJob,
    VerificationResult,
    VerificationRun,
)
from backend.app.config import get_settings
from backend.app.services.ocr_types import FinalizedResults, JobFence, LostFence
from backend.app.services.verification_jobs import VerificationJobService
from conftest import migrate


CANONICAL = b"{}"
CANONICAL_SHA256 = sha256(CANONICAL).hexdigest()
SOURCE_SHA256 = "b" * 64


@pytest.fixture(scope="module")
def database():
    """Keep global queue claims isolated from pending API fixtures in the full suite."""
    name = "qa_backend_test_" + uuid4().hex
    url = get_settings().database_url
    admin = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 5},
    )
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    engine = create_engine(
        url.set(database=name), isolation_level="REPEATABLE READ",
        connect_args={"client_encoding": "utf8", "connect_timeout": 5},
    )
    try:
        migrate(engine)
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


def _factory(database):
    return sessionmaker(database, expire_on_commit=False)


def _insert_screenshot(connection, catalog):
    screenshot_id = uuid4()
    project_id = catalog["project"]["id"]
    connection.execute(text("""
        INSERT INTO screenshots
          (id, project_id, build_id, locale_id, category_id, situation_id, source,
           original_filename, storage_key, file_hash, media_type, size_bytes, width,
           height, metadata_version, metadata, client_upload_id)
        VALUES
          (:id, :project_id, :build_id, :locale_id, :category_id, :situation_id,
           'manual', 'ocr-job.png', :storage_key, :file_hash, 'image/png', 10,
           4, 3, 1, '{}'::jsonb, NULL)
    """), {
        "id": screenshot_id,
        "project_id": project_id,
        "build_id": catalog["build"]["id"],
        "locale_id": catalog["locale"]["id"],
        "category_id": catalog["category"]["id"],
        "situation_id": catalog["situation"]["id"],
        "storage_key": f"objects/{project_id}/{screenshot_id}.png",
        "file_hash": SOURCE_SHA256,
    })
    return screenshot_id


def _insert_profile(connection):
    profile_id = "ocr-job-fixture-" + uuid4().hex
    canonical = ('{"profile_id":"' + profile_id + '"}').encode("ascii")
    digest = sha256(canonical).hexdigest()
    connection.execute(text("""
        INSERT INTO ocr_profiles
          (profile_id, profile_digest, canonical_manifest, engine_name, engine_version,
           model_ids, language_tags, coordinate_space, normalization_version,
           matching_version)
        VALUES
          (:profile_id, :digest, :canonical, 'fixture-engine', '1',
           '["fixture-model"]'::jsonb, '["ja-JP"]'::jsonb,
           'original-raster-v1', 'norm-v1', 'one-to-one-levenshtein-v1')
    """), {
        "profile_id": profile_id,
        "digest": digest,
        "canonical": canonical,
    })
    return profile_id, canonical, digest


def _insert_run(connection, catalog, *, state="PENDING", attempts=0):
    """Insert a contract-complete run/job, optionally expired at one DB timestamp."""
    screenshot_id = _insert_screenshot(connection, catalog)
    profile_id, profile_canonical, profile_digest = _insert_profile(connection)
    run_id = uuid4()
    project_id = catalog["project"]["id"]
    anchor = connection.scalar(text("SELECT clock_timestamp()"))
    running = state == "RUNNING"
    stage = "OCR" if running else "QUEUED"
    started = anchor - timedelta(seconds=1) if running else None
    connection.execute(text("""
        INSERT INTO verification_runs
          (id, project_id, screenshot_id, client_run_id, protocol_version,
           fingerprint_version, request_fingerprint, canonical_request, profile_id,
           profile_digest, profile_canonical, snapshot_version, snapshot_canonical,
           snapshot_sha256, captured_at, source_mode, configuration_canonical,
           configuration_sha256, normalization_version, matching_version,
           pass_threshold, review_threshold, locale_code, ocr_language,
           screenshot_storage_key, screenshot_file_hash, screenshot_size_bytes,
           screenshot_media_type, screenshot_width, screenshot_height,
           screenshot_build_id, screenshot_locale_id, screenshot_category_id,
           screenshot_situation_id, screenshot_metadata_version, screenshot_metadata,
           build_label, locale_name, category_slug, category_name, situation_slug,
           situation_name, situation_description, snapshot_item_count,
           snapshot_missing_count, status, stage, attempt_count, created_at,
           updated_at, started_at)
        VALUES
          (:id, :project_id, :screenshot_id, :client_run_id, 1, 1,
           :request_hash, :canonical, :profile_id, :profile_digest,
           :profile_canonical, 1, :canonical, :canonical_digest, :anchor,
           'run_creation', :canonical, :canonical_digest,
           'norm-v1', 'one-to-one-levenshtein-v1', 95, 85, 'JA-jp', 'ja',
           :storage_key, :source_hash, 10, 'image/png', 4, 3, :build_id,
           :locale_id, :category_id, :situation_id, 1, '{}'::jsonb, 'build',
           'locale', 'category', 'Category', 'situation', 'Situation', NULL,
           0, 0, :state, :stage, :attempts, :created, :anchor, :started)
    """), {
        "id": run_id,
        "project_id": project_id,
        "screenshot_id": screenshot_id,
        "client_run_id": uuid4(),
        "request_hash": "a" * 64,
        "canonical": CANONICAL,
        "profile_id": profile_id,
        "profile_digest": profile_digest,
        "profile_canonical": profile_canonical,
        "canonical_digest": CANONICAL_SHA256,
        "anchor": anchor,
        "storage_key": f"objects/{project_id}/{screenshot_id}.png",
        "source_hash": SOURCE_SHA256,
        "build_id": catalog["build"]["id"],
        "locale_id": catalog["locale"]["id"],
        "category_id": catalog["category"]["id"],
        "situation_id": catalog["situation"]["id"],
        "state": state,
        "stage": stage,
        "attempts": attempts,
        "created": anchor - timedelta(seconds=2),
        "started": started,
    })

    token = uuid4() if running else None
    connection.execute(text("""
        INSERT INTO verification_jobs
          (run_id, project_id, state, stage, attempt_count, generation,
           attempt_token, lease_expires_at, available_at, next_attempt_at,
           created_at, updated_at, started_at)
        VALUES
          (:run_id, :project_id, :state, :stage, :attempts, :attempts,
           :token, :lease, :available, NULL, :created, :anchor, :started)
    """), {
        "run_id": run_id,
        "project_id": project_id,
        "state": state,
        "stage": stage,
        "attempts": attempts,
        "token": token,
        "lease": anchor if running else None,
        "available": None if running else anchor,
        "created": anchor - timedelta(seconds=2),
        "anchor": anchor,
        "started": started,
    })

    if running:
        for generation in range(1, attempts + 1):
            current = generation == attempts
            attempt_token = token if current else uuid4()
            connection.execute(text("""
                INSERT INTO verification_attempts
                  (project_id, run_id, generation, claim_request_id, attempt_token,
                   correlation_id, claimed_at, lease_at_claim, outcome, error_code,
                   error_stage, error_retryable, error_message, closed_at)
                VALUES
                  (:project_id, :run_id, :generation, :claim, :token, :correlation,
                   :claimed, :attempt_lease, :outcome, :error_code, :error_stage,
                   :error_retryable, :error_message, :closed)
            """), {
                "project_id": project_id,
                "run_id": run_id,
                "generation": generation,
                "claim": uuid4(),
                "token": attempt_token,
                "correlation": uuid4(),
                "claimed": anchor - timedelta(seconds=2),
                "attempt_lease": anchor + timedelta(seconds=1),
                "outcome": "STARTED" if current else "EXPIRED",
                "error_code": None if current else "LEASE_EXPIRED",
                "error_stage": None if current else "OCR",
                "error_retryable": None if current else False,
                "error_message": None if current else "OCR verification processing could not be completed.",
                "closed": None if current else anchor - timedelta(seconds=1),
            })
    return UUID(project_id), run_id, anchor, token


@pytest.fixture
def pending_job(database, catalog):
    with database.begin() as connection:
        project_id, run_id, _, _ = _insert_run(connection, catalog)
    return _factory(database), project_id, run_id


def _rows(factory, project_id, run_id):
    with factory() as session:
        run = session.get(VerificationRun, run_id)
        job = session.get(VerificationJob, run_id)
        attempts = session.scalars(
            select(VerificationAttempt)
            .where(VerificationAttempt.project_id == project_id,
                   VerificationAttempt.run_id == run_id)
            .order_by(VerificationAttempt.generation)
        ).all()
        return run, job, attempts


def _make_retry_due(factory, project_id, run_id):
    with factory() as session:
        now = session.scalar(text("SELECT clock_timestamp()"))
        session.execute(text("""
            UPDATE verification_jobs
            SET available_at=:now, next_attempt_at=:now, updated_at=:now
            WHERE project_id=:project_id AND run_id=:run_id AND state='RETRY_WAIT'
        """), {"now": now, "project_id": project_id, "run_id": run_id})
        session.execute(text("""
            UPDATE verification_runs SET next_attempt_at=:now, updated_at=:now
            WHERE project_id=:project_id AND id=:run_id AND status='RETRY_WAIT'
        """), {"now": now, "project_id": project_id, "run_id": run_id})
        session.commit()


def _complete_result_writer(session, run, _output):
    ocr_id, verification_id = uuid4(), uuid4()
    session.add(OCRResult(
        id=ocr_id,
        project_id=run["project_id"],
        run_id=run["id"],
        screenshot_id=run["screenshot_id"],
        coordinate_space="original-raster-v1",
        width=run["screenshot_width"],
        height=run["screenshot_height"],
        region_count=0,
        no_text=True,
        profile_id=run["profile_id"],
        profile_digest=run["profile_digest"],
        engine_name="fixture-engine",
        engine_version="1",
        ocr_language=run["ocr_language"],
        source_sha256=run["screenshot_file_hash"],
        pixel_sha256="c" * 64,
        runtime_manifest={},
        preprocessing={},
        raw_audit={},
        raw_audit_sha256="d" * 64,
        timings_ms={},
        output_sha256="e" * 64,
    ))
    session.flush()
    session.add(VerificationResult(
        id=verification_id,
        project_id=run["project_id"],
        run_id=run["id"],
        screenshot_id=run["screenshot_id"],
        ocr_result_id=ocr_id,
        snapshot_sha256=run["snapshot_sha256"],
        configuration_sha256=run["configuration_sha256"],
        matching_version=run["matching_version"],
        normalization_version=run["normalization_version"],
        verification_status="UNVERIFIED",
        evaluation_reason="NO_EXPECTATIONS",
        incomplete=False,
        total_count=0,
        evaluated_count=0,
        unverified_count=0,
        pass_count=0,
        review_count=0,
        fail_count=0,
        unmatched_region_count=0,
        pass_threshold=run["pass_threshold"],
        review_threshold=run["review_threshold"],
    ))
    session.flush()
    return FinalizedResults(
        ocr_result_id=ocr_id,
        verification_result_id=verification_id,
        verification_status="UNVERIFIED",
        snapshot_sha256=run["snapshot_sha256"],
        configuration_sha256=run["configuration_sha256"],
        profile_digest=run["profile_digest"],
    )


class LoseAckOnce:
    def __init__(self, operation):
        self.operation = operation
        self.fired = False

    def hit(self, phase, context):
        if phase == "AFTER_COMMIT" and context["operation"] == self.operation and not self.fired:
            self.fired = True
            raise OSError("synthetic lost commit acknowledgement")


class FailBeforeCommitOnce:
    def __init__(self, operation):
        self.operation = operation
        self.fired = False

    def hit(self, phase, context):
        if phase == "BEFORE_COMMIT" and context["operation"] == self.operation and not self.fired:
            self.fired = True
            raise RuntimeError("synthetic pre-commit failure")


def test_due_claim_records_db_clock_lease_and_attempt_evidence(pending_job):
    factory, project_id, run_id = pending_job
    claim = VerificationJobService(factory).claim()

    assert claim is not None
    assert claim.fence.project_id == project_id
    assert claim.fence.run_id == run_id
    assert claim.attempt_count == 1
    run, job, attempts = _rows(factory, project_id, run_id)
    assert (run.status, job.state, run.stage, job.stage) == ("RUNNING", "RUNNING", "OCR", "OCR")
    assert run.attempt_count == job.attempt_count == job.generation == 1
    assert job.attempt_token == claim.fence.attempt_token
    assert attempts[0].outcome == "STARTED"
    assert attempts[0].claim_request_id == claim.fence.claim_request_id
    assert attempts[0].attempt_token == claim.fence.attempt_token
    assert attempts[0].correlation_id == claim.correlation_id
    assert attempts[0].lease_at_claim == claim.lease_expires_at
    assert claim.lease_expires_at - attempts[0].claimed_at == timedelta(seconds=60)


def test_two_concurrent_claimants_have_exactly_one_owner(pending_job):
    factory, project_id, run_id = pending_job
    barrier = Barrier(2)

    def claim():
        barrier.wait()
        return VerificationJobService(factory).claim()

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: claim(), range(2)))

    owned = [claim for claim in claims if claim is not None]
    assert len(owned) == 1
    _, job, attempts = _rows(factory, project_id, run_id)
    assert job.attempt_count == job.generation == 1
    assert job.attempt_token == owned[0].fence.attempt_token
    assert len(attempts) == 1


def test_db_clock_expiry_equality_is_taken_over_and_stale_owner_is_denied(database, catalog):
    with database.begin() as connection:
        project_id, run_id, equality, old_token = _insert_run(
            connection, catalog, state="RUNNING", attempts=1
        )
    factory = _factory(database)
    stale = JobFence(project_id, run_id, 1, old_token, uuid4())

    replacement = VerificationJobService(factory).claim()

    assert replacement is not None
    assert replacement.fence.run_id == run_id
    assert replacement.fence.generation == 2
    with pytest.raises(LostFence):
        VerificationJobService(factory).renew(stale)
    with pytest.raises(LostFence):
        VerificationJobService(factory).stage(stale)
    _, job, attempts = _rows(factory, project_id, run_id)
    assert attempts[0].outcome == "EXPIRED"
    assert attempts[0].closed_at >= equality
    assert attempts[1].outcome == "STARTED"
    assert job.attempt_token == replacement.fence.attempt_token


def test_renew_extends_from_fresh_db_clock_and_wrong_token_is_denied(pending_job):
    factory, project_id, run_id = pending_job
    service = VerificationJobService(factory)
    claim = service.claim()
    original = claim.lease_expires_at

    renewed = service.renew(claim.fence)

    assert renewed > original
    with factory() as session:
        job = session.get(VerificationJob, run_id)
        assert job.lease_expires_at == renewed
        assert renewed - job.updated_at == timedelta(seconds=60)
    wrong = JobFence(project_id, run_id, claim.fence.generation, uuid4(), claim.fence.claim_request_id)
    with pytest.raises(LostFence):
        service.renew(wrong)


def test_retry_backoff_is_five_then_ten_seconds_and_third_failure_exhausts(pending_job):
    factory, project_id, run_id = pending_job
    service = VerificationJobService(factory)

    first = service.claim()
    assert service.fail(first.fence, "ENGINE_TIMEOUT") == "RETRY_WAIT"
    run, job, attempts = _rows(factory, project_id, run_id)
    assert job.next_attempt_at - job.updated_at == timedelta(seconds=5)
    assert run.next_attempt_at == job.next_attempt_at
    assert attempts[0].outcome == "RETRY_WAIT"
    assert attempts[0].error_code == "ENGINE_TIMEOUT"

    _make_retry_due(factory, project_id, run_id)
    second = service.claim()
    assert second.attempt_count == 2
    assert service.fail(second.fence, "ENGINE_PROCESS_CRASH") == "RETRY_WAIT"
    _, job, attempts = _rows(factory, project_id, run_id)
    assert job.next_attempt_at - job.updated_at == timedelta(seconds=10)
    assert [row.outcome for row in attempts] == ["RETRY_WAIT", "RETRY_WAIT"]

    _make_retry_due(factory, project_id, run_id)
    third = service.claim()
    assert third.attempt_count == 3
    assert service.fail(third.fence, "INPUT_STORAGE_UNAVAILABLE") == "FAILED"
    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.status == job.state == "FAILED"
    assert run.error_code == job.last_error_code == "RETRY_EXHAUSTED"
    assert run.error_cause_code == job.last_error_cause_code == "INPUT_STORAGE_UNAVAILABLE"
    assert run.error_retryable is job.last_error_retryable is False
    assert run.error_attempt == job.last_error_attempt == 3
    assert attempts[-1].outcome == "FAILED"
    assert attempts[-1].error_code == "RETRY_EXHAUSTED"
    assert service.claim() is None


def test_expired_third_attempt_is_reaped_without_a_fourth_claim(database, catalog):
    with database.begin() as connection:
        project_id, run_id, _, _ = _insert_run(
            connection, catalog, state="RUNNING", attempts=3
        )
    factory = _factory(database)

    assert VerificationJobService(factory).claim() is None

    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.status == job.state == "FAILED"
    assert job.generation == job.attempt_count == 3
    assert job.last_error_code == "RETRY_EXHAUSTED"
    assert job.last_error_cause_code == "LEASE_EXPIRED"
    assert len(attempts) == 3
    assert attempts[-1].outcome == "EXPIRED"


def test_stage_and_finalize_are_atomic_and_partial_writer_rolls_back(pending_job):
    factory, project_id, run_id = pending_job
    service = VerificationJobService(factory)
    claim = service.claim()

    stage_fault = FailBeforeCommitOnce("stage")
    with pytest.raises(RuntimeError, match="synthetic pre-commit failure"):
        VerificationJobService(factory, faults=stage_fault).stage(claim.fence)
    run, job, attempts = _rows(factory, project_id, run_id)
    assert stage_fault.fired
    assert run.stage == job.stage == "OCR"
    assert attempts[0].outcome == "STARTED"

    assert service.stage(claim.fence) == "VERIFY"

    def partial_writer(session, run, output):
        _complete_result_writer(session, run, output)
        raise RuntimeError("synthetic validation failure")

    with pytest.raises(RuntimeError, match="synthetic validation failure"):
        VerificationJobService(factory, result_writer=partial_writer).finalize(claim.fence, {})

    with factory() as session:
        assert session.scalar(select(OCRResult).where(OCRResult.run_id == run_id)) is None
        assert session.scalar(select(VerificationResult).where(VerificationResult.run_id == run_id)) is None
        assert session.get(VerificationJob, run_id).state == "RUNNING"
        assert session.get(VerificationRun, run_id).stage == "VERIFY"

    result = VerificationJobService(
        factory, result_writer=_complete_result_writer
    ).finalize(claim.fence, {})
    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.status == job.state == "SUCCEEDED"
    assert run.stage == job.stage == "COMPLETE"
    assert run.ocr_result_id == result.ocr_result_id
    assert run.verification_result_id == result.verification_result_id
    assert run.verification_status == "UNVERIFIED"
    assert attempts[0].outcome == "SUCCEEDED"


def test_lost_claim_and_finalize_ack_recover_exact_committed_identity(pending_job):
    factory, project_id, run_id = pending_job
    claim_fault = LoseAckOnce("claim")
    claim = VerificationJobService(factory, faults=claim_fault).claim()
    assert claim_fault.fired

    recovered = VerificationJobService(factory).recover_claim(claim.fence)
    assert recovered == claim
    _, job, attempts = _rows(factory, project_id, run_id)
    assert job.attempt_count == 1
    assert len(attempts) == 1

    VerificationJobService(factory).stage(claim.fence)
    finalize_fault = LoseAckOnce("finalize")
    result = VerificationJobService(
        factory, result_writer=_complete_result_writer, faults=finalize_fault
    ).finalize(claim.fence, {})
    assert finalize_fault.fired
    recovered_result = VerificationJobService(factory).recover_finalize(claim.fence)
    assert recovered_result == result
    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.status == job.state == "SUCCEEDED"
    assert len(attempts) == 1
    assert attempts[0].outcome == "SUCCEEDED"
