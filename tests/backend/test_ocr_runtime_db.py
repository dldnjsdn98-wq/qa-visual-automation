"""Durable settlement facts; parent scheduling/deadline tests follow API freeze."""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select

from backend.app.models import OCRResult, VerificationResult
from backend.app.services.ocr_types import OutcomeUnknown
from backend.app.services.verification_jobs import VerificationJobService
from test_ocr_jobs import (
    database, pending_job, _complete_result_writer, _rows, _insert_run, _factory,
)


class _CommitBoundary:
    """Deterministic local-clock crossing after the real PostgreSQL commit.

    This probes settlement semantics, not the runner's deadline enforcement.
    """

    def __init__(self, *, lose_ack=False):
        self.local_time = 299.0
        self.lose_ack = lose_ack
        self.events = []

    def hit(self, phase, context):
        operation = context["operation"] if "operation" in context else None
        if operation != "finalize":
            return
        self.events.append((phase, self.local_time))
        if phase == "AFTER_COMMIT":
            self.local_time = 301.0
            if self.lose_ack:
                raise OSError("synthetic acknowledgement lost after committed finalize")


def _claimed_in_verify(pending_job):
    factory, project_id, run_id = pending_job
    jobs = VerificationJobService(factory)
    claim = jobs.claim()
    assert claim is not None
    assert claim.fence.run_id == run_id
    jobs.stage(claim.fence)
    return factory, project_id, run_id, claim


@pytest.mark.parametrize("lose_ack", [False, True])
def test_valid_commit_survives_late_ack_or_locked_recovery(
    pending_job, lose_ack, record_property
):
    factory, project_id, run_id, claim = _claimed_in_verify(pending_job)
    boundary = _CommitBoundary(lose_ack=lose_ack)
    writes = []

    def writer(session, run, output):
        result = _complete_result_writer(session, run, output)
        writes.append(result)
        return result

    guard_calls = []

    def guard(operation, retry_index):
        guard_calls.append((operation, retry_index, boundary.local_time))
        if boundary.local_time >= 300:
            raise RuntimeError("ENGINE_TIMEOUT")

    jobs = VerificationJobService(
        factory, result_writer=writer, faults=boundary, mutation_guard=guard,
    )
    result = jobs.finalize(claim.fence, {})

    assert boundary.local_time > 300
    assert boundary.events == [("BEFORE_COMMIT", 299.0), ("AFTER_COMMIT", 299.0)]
    assert writes == [result]
    assert guard_calls
    assert all(operation == "finalize" and clock < 300
               for operation, _retry, clock in guard_calls)
    assert VerificationJobService(factory).recover_finalize(claim.fence) == result
    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.status == job.state == attempts[-1].outcome == "SUCCEEDED"
    assert run.ocr_result_id == result.ocr_result_id
    assert run.verification_result_id == result.verification_result_id
    assert len(attempts) == 1
    record_property("isolated_database_name", factory.kw["bind"].url.database)
    record_property("deadline_observation", "synthetic local clock; real DB commit")
    record_property("lost_commit_ack", lose_ack)
    record_property("result_writer_calls", len(writes))


def test_unresolved_ack_does_not_imply_rollback_or_compensating_failure(
    pending_job, monkeypatch, record_property
):
    factory, project_id, run_id, claim = _claimed_in_verify(pending_job)
    boundary = _CommitBoundary(lose_ack=True)
    jobs = VerificationJobService(
        factory, result_writer=_complete_result_writer, faults=boundary,
    )
    recovery_calls = []
    compensation_calls = []

    def unresolved(fence):
        recovery_calls.append(fence)
        raise OutcomeUnknown("synthetic primary recovery unavailable")

    monkeypatch.setattr(jobs, "recover_finalize", unresolved)
    monkeypatch.setattr(jobs, "fail", lambda *args: compensation_calls.append(args))
    with pytest.raises(OutcomeUnknown, match="primary recovery unavailable"):
        jobs.finalize(claim.fence, {})

    assert recovery_calls == [claim.fence]
    assert compensation_calls == []
    assert len([event for event in boundary.events if event[0] == "BEFORE_COMMIT"]) == 1
    # Observe through a fresh primary service: acknowledgement loss is not rollback.
    result = VerificationJobService(factory).recover_finalize(claim.fence)
    assert result is not None
    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.status == job.state == attempts[-1].outcome == "SUCCEEDED"
    with factory() as session:
        assert len(session.scalars(select(OCRResult).where(OCRResult.run_id == run_id)).all()) == 1
        assert len(session.scalars(select(VerificationResult).where(VerificationResult.run_id == run_id)).all()) == 1
    record_property("isolated_database_name", factory.kw["bind"].url.database)
    record_property("durable_result_after_uncertain_ack", "SUCCEEDED")
    record_property("compensating_fail_calls", len(compensation_calls))


@pytest.mark.parametrize("operation", ["claim", "renew", "stage", "finalize", "fail"])
def test_expired_mutation_is_rejected_before_opening_database(operation):
    opened = []

    def sessions():
        opened.append(True)
        pytest.fail("expired mutation opened a database session")

    def expired(_operation, _retry):
        raise RuntimeError("ENGINE_TIMEOUT")

    jobs = VerificationJobService(sessions, mutation_guard=expired, result_writer=lambda *_: None)
    args = {"claim": (), "renew": (None,), "stage": (None,),
            "finalize": (None, {}), "fail": (None, "ENGINE_TIMEOUT")}
    with pytest.raises(RuntimeError, match="ENGINE_TIMEOUT"):
        getattr(jobs, operation)(*args[operation])
    assert opened == []


def test_deadline_crossed_during_begin_prevents_stage_mutation(pending_job, monkeypatch):
    from backend.app.repositories.verification_runs import VerificationRunRepository

    factory, project_id, run_id = pending_job
    claim = VerificationJobService(factory).claim()
    expired = False
    begin = VerificationRunRepository.begin

    def begin_crossing_deadline(repo):
        nonlocal expired
        begin(repo)
        expired = True

    def guard(_operation, _retry):
        if expired:
            raise RuntimeError("ENGINE_TIMEOUT")

    with monkeypatch.context() as patch:
        patch.setattr(VerificationRunRepository, "begin", begin_crossing_deadline)
        with pytest.raises(RuntimeError, match="ENGINE_TIMEOUT"):
            VerificationJobService(factory, mutation_guard=guard).stage(claim.fence)

    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.stage == job.stage == "OCR"
    assert run.status == job.state == "RUNNING"
    assert attempts[-1].outcome == "STARTED"


def test_proven_finalize_rollback_after_deadline_forbids_second_finalize(
    pending_job, record_property
):
    factory, project_id, run_id, claim = _claimed_in_verify(pending_job)
    expired = False
    injected = False
    writer_calls = []
    guard_calls = []

    def sessions():
        session = factory()
        original_commit = session.commit

        def commit():
            nonlocal expired, injected
            if not injected:
                # Actual PostgreSQL rollback, then lost acknowledgement at the
                # service COMMIT boundary. Recovery must inspect the primary.
                session.rollback()
                injected = expired = True
                raise OSError("synthetic commit transport loss after rollback")
            original_commit()

        session.commit = commit
        return session

    def guard(operation, retry_index):
        guard_calls.append((operation, retry_index, expired))
        if expired:
            raise RuntimeError("ENGINE_TIMEOUT")

    def writer(session, run, output):
        writer_calls.append(run["id"])
        return _complete_result_writer(session, run, output)

    jobs = VerificationJobService(sessions, result_writer=writer, mutation_guard=guard)
    with pytest.raises(RuntimeError, match="ENGINE_TIMEOUT"):
        jobs.finalize(claim.fence, {})

    assert injected
    assert writer_calls == [run_id]
    assert guard_calls[-1] == ("finalize", 0, True)
    # Fresh primary recovery proves absence only in this injected rollback case.
    assert VerificationJobService(factory).recover_finalize(claim.fence) is None
    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.status == job.state == "RUNNING"
    assert run.stage == job.stage == "VERIFY"
    assert attempts[-1].outcome == "STARTED"
    assert run.ocr_result_id is run.verification_result_id is None
    with factory() as session:
        assert session.scalar(select(OCRResult).where(OCRResult.run_id == run_id)) is None
        assert session.scalar(select(VerificationResult).where(VerificationResult.run_id == run_id)) is None
    record_property("isolated_database_name", factory.kw["bind"].url.database)
    record_property("result_writer_calls", len(writer_calls))
    record_property("post_deadline_finalize_blocked", True)


@pytest.mark.parametrize("wait_at", ["due", "run"])
@pytest.mark.parametrize("policy_change", ["expired", "suspended"])
@pytest.mark.parametrize("initial", ["pending", "takeover", "reaper"])
def test_claim_selection_wait_cannot_mutate_after_policy_change(
    database, catalog, monkeypatch, wait_at, policy_change, initial, record_property
):
    from backend.app.repositories.verification_runs import VerificationRunRepository
    from backend.app.workers.ocr_runtime import DeadlinePolicy

    with database.begin() as connection:
        project_id, run_id, _, _ = _insert_run(
            connection, catalog,
            state="PENDING" if initial == "pending" else "RUNNING",
            attempts={"pending": 0, "takeover": 1, "reaper": 3}[initial],
        )
    factory = _factory(database)
    before_run, before_job, before_attempts = _rows(factory, project_id, run_id)
    entered, release = threading.Event(), threading.Event()
    policy = DeadlinePolicy(time.monotonic() + 60)
    original_run = VerificationRunRepository.run
    mutation_calls = []

    def pause():
        entered.set()
        if not release.wait(5):
            raise AssertionError("test did not release selection boundary")

    def selected_due(repo):
        # Select and lock this test's real durable job, excluding other cases'
        # deliberately unclaimed rows. The wait is an injected repository seam,
        # not a claim that PostgreSQL SKIP LOCKED blocks on a locked job.
        job = repo.lock(project_id, run_id)
        if wait_at == "due":
            pause()
        return job

    def selected_run(repo, p, r):
        row = original_run(repo, p, r)
        if wait_at == "run":
            pause()
        return row

    monkeypatch.setattr(VerificationRunRepository, "due", selected_due)
    monkeypatch.setattr(VerificationRunRepository, "run", selected_run)
    for name in ("start", "close_attempt", "transition"):
        original = getattr(VerificationRunRepository, name)
        def observe(repo, *args, _name=name, _original=original, **kwargs):
            mutation_calls.append(_name)
            return _original(repo, *args, **kwargs)
        monkeypatch.setattr(VerificationRunRepository, name, observe)

    jobs = VerificationJobService(factory, mutation_guard=policy.guard)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(jobs.claim)
        try:
            assert entered.wait(3), "claim must actually enter the selected wait"
            if policy_change == "expired":
                policy.deadline = time.monotonic() - 1
            else:
                policy.suspended = True
        finally:
            release.set()
        expected = RuntimeError if policy_change == "expired" else OutcomeUnknown
        with pytest.raises(expected, match="ENGINE_TIMEOUT|quarantined"):
            future.result(timeout=3)

    assert mutation_calls == [], "no claim/reaper/takeover write may start after policy loss"
    run, job, attempts = _rows(factory, project_id, run_id)
    assert (run.status, run.stage, run.attempt_count) == (
        before_run.status, before_run.stage, before_run.attempt_count,
    )
    assert (job.state, job.generation, job.attempt_token, job.lease_expires_at) == (
        before_job.state, before_job.generation, before_job.attempt_token, before_job.lease_expires_at,
    )
    assert [(a.generation, a.outcome, a.closed_at) for a in attempts] == [
        (a.generation, a.outcome, a.closed_at) for a in before_attempts
    ]
    assert run.ocr_result_id is run.verification_result_id is None
    record_property("isolated_database_name", factory.kw["bind"].url.database)
    record_property("claim_wait_boundary", wait_at)
    record_property("policy_change_while_waiting", policy_change)
    record_property("durable_claim_transition", initial)
    record_property("post_policy_mutation_calls", len(mutation_calls))


@pytest.mark.parametrize("reason", ["revoked", "digest_mismatch"])
def test_queued_profile_admission_loss_fails_fenced_without_child(
    pending_job, monkeypatch, reason, record_property
):
    from backend.app.models import VerificationRun
    from backend.app.repositories.verification_runs import VerificationRunRepository
    from backend.app.workers import ocr_admission
    from backend.app.workers.ocr import OCRRunner

    factory, project_id, run_id = pending_job
    with factory() as session:
        row = session.get(VerificationRun, run_id)
        expected = (row.profile_id, row.profile_digest)
    observed = []
    # Model a queued run whose deployment assertion has changed since admission.
    admitted_profiles = {expected[0]: expected[1]}
    assert admitted_profiles.get(expected[0]) == expected[1]
    if reason == "revoked":
        admitted_profiles.clear()
    else:
        admitted_profiles[expected[0]] = "0" * 64

    def admitted(profile_id, profile_digest):
        observed.append((profile_id, profile_digest))
        return admitted_profiles.get(profile_id) == profile_digest

    monkeypatch.setattr(ocr_admission, "admitted", admitted)
    monkeypatch.setattr(VerificationRunRepository, "due", lambda repo: repo.lock(project_id, run_id))
    runner = OCRRunner(session_factory=factory)
    runner._storage_root = lambda: "unused-no-source-access"
    runner._launch = lambda *_: pytest.fail("unadmitted queued profile launched child")
    assert runner.run_once()
    assert observed == [expected]
    assert runner.last_process is None
    assert runner.child_stopped
    assert not runner.quarantined
    run, job, attempts = _rows(factory, project_id, run_id)
    assert run.status == job.state == attempts[-1].outcome == "FAILED"
    assert run.error_code == job.last_error_code == attempts[-1].error_code == "ENGINE_UNAVAILABLE"
    assert run.error_retryable is False
    assert run.ocr_result_id is run.verification_result_id is None
    with factory() as session:
        assert session.scalar(select(OCRResult).where(OCRResult.run_id == run_id)) is None
        assert session.scalar(select(VerificationResult).where(VerificationResult.run_id == run_id)) is None
    record_property("isolated_database_name", factory.kw["bind"].url.database)
    record_property("runner_admission_identity", repr(expected))
    record_property("admission_change", reason)


@pytest.mark.parametrize("failure", ["safe_prelaunch", "cleaned_after_start", "unproven", "memory_error", "runtime_error"])
def test_admitted_run_containment_launch_failure_settles_only_when_safe(
    client, catalog, monkeypatch, failure, record_property
):
    from uuid import UUID
    from test_ocr_api import disposable_profile_registry, _upload, _run_path, _run_body
    from backend.app.repositories.verification_runs import VerificationRunRepository
    from backend.app.workers import ocr_admission, ocr_containment
    from backend.app.workers.ocr import OCRRunner

    # Reuse the synthetic registry builder locally, not its autouse fixture.
    state = disposable_profile_registry.__wrapped__(monkeypatch)
    identity = (state.document.profile_id, state.document.sha256)
    observed = []
    def admitted(profile_id, digest):
        observed.append((profile_id, digest))
        return (profile_id, digest) == identity
    monkeypatch.setattr(ocr_admission, "admitted", admitted)
    screenshot, _ = _upload(client, catalog)
    created = client.post(_run_path(screenshot), json=_run_body(identity[0]))
    assert created.status_code == 202, created.text
    run_id, project_id = UUID(created.json()["id"]), UUID(catalog["project"]["id"])
    monkeypatch.setattr(VerificationRunRepository, "due", lambda repo: repo.lock(project_id, run_id))
    launches = []
    cleanup_confirmed = failure in {"safe_prelaunch", "cleaned_after_start"}
    workload_started = failure not in {"safe_prelaunch", "unproven"}
    def unavailable(*args, **kwargs):
        launches.append(True)
        if failure == "memory_error":
            raise MemoryError("synthetic unknown launch ownership")
        if failure == "runtime_error":
            raise RuntimeError("synthetic unknown launch ownership")
        raise ocr_containment.ContainmentUnavailable(
            "synthetic launch failure; no subprocess created", cleanup_confirmed=cleanup_confirmed,
            workload_started=workload_started,
        )
    monkeypatch.setattr(ocr_containment, "launch_contained", unavailable)
    runner = OCRRunner(session_factory=client.factory, storage=client.storage)
    try:
        assert runner.run_once()
        assert launches == [True]
        assert observed == [identity]
        assert runner.last_process is None
        run, job, attempts = _rows(client.factory, project_id, run_id)
        if failure == "safe_prelaunch":
            assert run.status == job.state == attempts[-1].outcome == "FAILED"
            assert run.error_code == job.last_error_code == "ENGINE_UNAVAILABLE"
            assert not runner.quarantined
            assert runner._scratch is None
        else:
            assert run.status == job.state == "RUNNING"
            assert attempts[-1].outcome == "STARTED"
            assert run.error_code is job.last_error_code is None
            assert runner.quarantined
            # Proven cleanup after started work may dispose scratch, but never
            # authorizes a fresh durable unavailable mutation.
            if not cleanup_confirmed:
                assert runner._scratch is not None
                from pathlib import Path
                assert Path(runner._scratch.name).is_dir(), "unknown launch ownership lost scratch"
            with pytest.raises(OutcomeUnknown):
                runner.run_once()
        assert run.ocr_result_id is run.verification_result_id is None
        record_property("isolated_database_name", client.factory.kw["bind"].url.database)
        record_property("synthetic_cleanup_confirmed", cleanup_confirmed)
        record_property("synthetic_workload_started", workload_started)
        record_property("launch_failure_case", failure)
        record_property("durable_state", run.status)
    finally:
        # Fixture injected no OS workload; explicitly dispose only its scratch.
        # This is not a product stop retry or proof of native cleanup.
        if runner._scratch is not None:
            runner._scratch.cleanup()


def test_metadata_admission_observes_frozen_identity_after_session_close(pending_job, monkeypatch):
    from contextlib import contextmanager
    from backend.app.models import VerificationRun
    from backend.app.workers import ocr_admission
    from backend.app.workers.ocr_runtime import load_metadata
    from types import SimpleNamespace

    factory, project_id, run_id = pending_job
    with factory() as session:
        row = session.get(VerificationRun, run_id)
        expected = (row.profile_id, row.profile_digest)
    closed = []
    observed = []

    @contextmanager
    def sessions():
        with factory() as session:
            yield session
        closed.append(True)

    def admitted(profile_id, profile_digest):
        assert closed == [True]
        observed.append((profile_id, profile_digest))
        return False

    monkeypatch.setattr(ocr_admission, "admitted", admitted)
    claim = SimpleNamespace(fence=SimpleNamespace(project_id=project_id, run_id=run_id))
    with pytest.raises(RuntimeError, match="ENGINE_UNAVAILABLE"):
        load_metadata(sessions, "unused", claim)
    assert observed == [expected]
