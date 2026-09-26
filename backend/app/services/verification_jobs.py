"""Durable OCR mutations and locked-primary lost-ack recovery (P3-OCR-v1).

Supply a NEW Session per operation/heartbeat. ResultWriter is mandatory for
finalization: the parent implements closed adapter validation/result insertion.
No engine call or source I/O belongs in these short transactions. A recovered
renewal permits continuation only under its returned lease, never an assumed
extra sixty seconds. OutcomeUnknown always means suspend/discard publication.
"""
import hashlib
from datetime import timedelta
from uuid import uuid4

from sqlalchemy.exc import DBAPIError

from backend.app.repositories.verification_runs import MAX_GENERATION, VerificationRunRepository
from backend.app.services.ocr_types import (
    Claim, FinalizedResults, JobInvariantError, LostFence, OutcomeUnknown,
)

RETRYABLE = frozenset({"INPUT_STORAGE_UNAVAILABLE", "ENGINE_TIMEOUT", "ENGINE_PROCESS_CRASH"})
TERMINAL = frozenset({
    "ENGINE_UNAVAILABLE", "MODEL_UNAVAILABLE", "ENGINE_OUTPUT_INVALID", "RESULT_LIMIT_EXCEEDED",
    "NORMALIZATION_ERROR", "SNAPSHOT_INTEGRITY_ERROR", "PROFILE_DIGEST_MISMATCH",
    "INPUT_HASH_MISMATCH", "ENGINE_INTERNAL_ERROR", "ENGINE_RESOURCE_LIMIT",
})


def _sqlstate(exc):
    return getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)


def _error(code, stage, attempt, correlation, *, cause=None, retryable=False):
    return {"code": code, "correlation_id": str(correlation), "cause_code": cause,
            "stage": stage, "retryable": retryable,
            "message": "OCR verification processing could not be completed.", "attempt": attempt}


class VerificationJobService:
    def __init__(self, session_factory, *, result_writer=None, faults=None, mutation_guard=None):
        self.session_factory = session_factory
        self.result_writer = result_writer
        self.faults = faults
        self.mutation_guard = mutation_guard

    def _hit(self, phase, context):
        if self.faults is not None:
            self.faults.hit(phase, context)

    def _transaction(self, operation, action, recover=None):
        for number in range(3):
            # Recovery operations only observe previously issued transactions.
            # Guard every mutation attempt, including serialization retries.
            mutating = operation in {"claim", "renew", "stage", "finalize", "fail"}
            if mutating and self.mutation_guard is not None:
                self.mutation_guard(operation, number)
            session = self.session_factory()
            committing = False
            try:
                repo = VerificationRunRepository(session)
                repo.begin()
                if mutating and self.mutation_guard is not None:
                    self.mutation_guard(operation, number)
                answer = action(repo)
                self._hit("BEFORE_COMMIT", {"operation": operation})
                committing = True
                session.commit()
                self._hit("AFTER_COMMIT", {"operation": operation})
                return answer
            except DBAPIError as exc:
                state = _sqlstate(exc)
                if state in {"40001", "40P01"}:
                    # PostgreSQL explicitly proves this transaction aborted.
                    session.rollback()
                    if number < 2:
                        continue
                    raise OutcomeUnknown("Database rollback retry budget exhausted") from exc
                if not committing:
                    session.rollback()
                    raise
                # Do not trust a connection that may have lost COMMIT's reply.
                session.invalidate()
                session.close()
                if recover is not None:
                    return recover()
                raise OutcomeUnknown("Database outcome cannot be resolved") from exc
            except Exception as exc:
                if committing:
                    # Includes deterministic AFTER_COMMIT fault injection.
                    session.invalidate()
                    session.close()
                    if recover is not None:
                        return recover()
                    raise OutcomeUnknown("Commit acknowledgement unavailable") from exc
                session.rollback()
                raise
            finally:
                session.close()

    def claim(self):
        request_id, token, correlation = uuid4(), uuid4(), uuid4()
        candidate = {}

        def action(repo):
            job = repo.due()
            if job is None:
                return None  # SKIP LOCKED is not a claim that the queue is empty.
            now = repo.now()
            if job["state"] == "RUNNING":
                if job["lease_expires_at"] > now:
                    return None
            elif job["available_at"] > now:
                return None
            run = repo.run(job["project_id"], job["run_id"])
            if run["status"] != job["state"] or run["attempt_count"] != job["attempt_count"]:
                raise JobInvariantError("Run/job lifecycle mismatch")
            candidate.update(project_id=job["project_id"], run_id=job["run_id"],
                             generation=job["generation"] + 1)
            failure_correlation = correlation
            if job["state"] == "RUNNING":
                predecessor = repo.current_attempt(job)
                if predecessor is None or predecessor["outcome"] != "STARTED":
                    raise JobInvariantError("Expired job has no matching open attempt")
                failure_correlation = predecessor["correlation_id"]
                if self.mutation_guard is not None:
                    self.mutation_guard("claim", 0)
                repo.close_attempt(job, "EXPIRED", _error(
                    "LEASE_EXPIRED", run["stage"], job["attempt_count"], failure_correlation))
            code = ("RETRY_EXHAUSTED" if job["attempt_count"] >= 3 else
                    "JOB_GENERATION_EXHAUSTED" if job["generation"] >= MAX_GENERATION else None)
            if code:
                cause = "LEASE_EXPIRED" if job["state"] == "RUNNING" else None
                if self.mutation_guard is not None:
                    self.mutation_guard("claim", 0)
                repo.transition(job, state="FAILED", stage=run["stage"], now=now,
                                error=_error(code, run["stage"], job["attempt_count"],
                                             failure_correlation, cause=cause))
                return None
            if self.mutation_guard is not None:
                self.mutation_guard("claim", 0)
            fence, lease = repo.start(job, request_id, token, correlation, now)
            candidate["fence"] = fence
            self._hit("AFTER_CLAIM", {"fence": fence})
            return Claim(fence, job["attempt_count"] + 1, lease, correlation)

        def recover():
            if "fence" not in candidate:
                # Could be a reaper COMMIT or a failed selection. Never pretend
                # a new identity is a replay of that unresolved operation.
                raise OutcomeUnknown("Claim did not produce a recoverable assignment")
            return self.recover_claim(candidate["fence"])

        return self._transaction("claim", action, recover)

    def recover_claim(self, fence):
        def action(repo):
            job = repo.lock(fence.project_id, fence.run_id)
            now = repo.now()
            if job is None:
                raise JobInvariantError("Durable job disappeared")
            attempt = repo.attempt(fence)
            if attempt is None:
                # This locked primary read waited for the original UPDATE to
                # resolve. No local inference may run on this absent claim.
                return None
            if not repo.owns(job, fence, now) or attempt["outcome"] != "STARTED":
                raise LostFence("Claim acknowledgement recovered after ownership ended")
            return Claim(fence, job["attempt_count"], job["lease_expires_at"],
                         attempt["correlation_id"])
        return self._transaction("recover_claim", action)

    def renew(self, fence):
        def action(repo):
            _, _, _, now = repo.fenced(fence)
            if self.mutation_guard is not None:
                self.mutation_guard("renew", 0)
            return repo.renew(fence, now)

        def recover():
            claim = self.recover_claim(fence)
            if claim is None:
                raise LostFence("Renewal has no committed claim")
            return claim.lease_expires_at
        return self._transaction("renew", action, recover)

    def stage(self, fence):
        def action(repo):
            _, run, _, now = repo.fenced(fence)
            if run["stage"] not in {"OCR", "VERIFY"}:
                raise JobInvariantError("Invalid live stage")
            if self.mutation_guard is not None:
                self.mutation_guard("stage", 0)
            repo.stage(fence, now)
            return "VERIFY"

        def recover():
            def read(repo):
                _, run, _, _ = repo.fenced(fence)
                if run["stage"] == "VERIFY":
                    return "VERIFY"
                raise OutcomeUnknown("Stage did not commit; caller must explicitly retry")
            return self._transaction("recover_stage", read)
        return self._transaction("stage", action, recover)

    def fail(self, fence, code):
        """Retry policy is a fixed Backend allowlist, never adapter-provided bool."""
        if code not in RETRYABLE | TERMINAL:
            code = "ENGINE_INTERNAL_ERROR"

        def action(repo):
            job, run, attempt, now = repo.fenced(fence)
            retryable = code in RETRYABLE and job["attempt_count"] < 3
            exhausted = code in RETRYABLE and not retryable
            error = _error("RETRY_EXHAUSTED" if exhausted else code, run["stage"],
                           job["attempt_count"], attempt["correlation_id"],
                           cause=code if exhausted else None, retryable=retryable)
            state = "RETRY_WAIT" if retryable else "FAILED"
            if self.mutation_guard is not None:
                self.mutation_guard("fail", 0)
            repo.close_attempt(job, state, error)
            repo.transition(job, state=state, stage=run["stage"], now=now, error=error,
                            available_at=now + timedelta(seconds=5 * job["attempt_count"])
                            if retryable else None)
            return state

        def recover():
            def read(repo):
                job = repo.lock(fence.project_id, fence.run_id)
                attempt = repo.attempt(fence)
                if attempt and attempt["outcome"] in {"RETRY_WAIT", "FAILED"}:
                    return attempt["outcome"]
                if not repo.owns(job, fence, repo.now()):
                    raise LostFence("Failure acknowledgement recovered after ownership ended")
                raise OutcomeUnknown("Failure did not commit; caller must explicitly retry")
            return self._transaction("recover_fail", read)
        return self._transaction("fail", action, recover)

    retry = fail

    @staticmethod
    def _validate_inputs(run):
        for canonical, digest in (("snapshot_canonical", "snapshot_sha256"),
                                  ("configuration_canonical", "configuration_sha256"),
                                  ("profile_canonical", "profile_digest")):
            value = run[canonical]
            if not isinstance(value, (bytes, memoryview)):
                raise JobInvariantError("Immutable input must be canonical bytes")
            if hashlib.sha256(bytes(value)).hexdigest() != run[digest]:
                raise JobInvariantError("Immutable input digest mismatch")

    @staticmethod
    def _validate_result(run, result):
        if (result.verification_status not in {"PASS", "REVIEW", "FAIL", "UNVERIFIED"}
                or result.snapshot_sha256 != run["snapshot_sha256"]
                or result.configuration_sha256 != run["configuration_sha256"]
                or result.profile_digest != run["profile_digest"]):
            raise JobInvariantError("Result does not identify the frozen inputs")

    def finalize(self, fence, output):
        if self.result_writer is None:
            raise JobInvariantError("Complete adapter validator/result writer is required")

        def action(repo):
            job, run, _, now = repo.fenced(fence)
            self._validate_inputs(run)
            if repo.any_results(fence.project_id, fence.run_id):
                raise JobInvariantError("Nonterminal job already has result rows")
            self._hit("BEFORE_RESULT_APPEND", {"fence": fence})
            if self.mutation_guard is not None:
                self.mutation_guard("finalize", 0)
            result = self.result_writer(repo.session, run, output)
            self._validate_result(run, result)
            pair = repo.result_pair(fence.project_id, fence.run_id)
            if pair is None or FinalizedResults(**pair) != result:
                raise JobInvariantError("Result writer did not insert a complete scoped result pair")
            # Result validation/insertion may consume lease time: check again
            # immediately before publishing the final state, still under lock.
            job, run, _, now = repo.fenced(fence)
            repo.close_attempt(job, "SUCCEEDED")
            repo.transition(job, state="SUCCEEDED", stage="COMPLETE", now=now, result=result)
            return result

        def recover():
            return self.recover_finalize(fence)
        for _ in range(2):
            result = self._transaction("finalize", action, recover)
            if result is not None:
                return result
        raise OutcomeUnknown("Finalize rollback was proven but bounded retry did not commit")

    def recover_finalize(self, fence):
        """Return committed results, or None for proven rollback + live fence.

        None permits an explicit bounded caller retry with the SAME output and
        fence; it never permits FAILED or a fresh claim on uncertain outcome.
        """
        def action(repo):
            job = repo.lock(fence.project_id, fence.run_id)
            now = repo.now()
            if job is None:
                raise JobInvariantError("Durable job disappeared")
            run = repo.run(fence.project_id, fence.run_id)
            attempt = repo.attempt(fence)
            pair = repo.result_pair(fence.project_id, fence.run_id)
            if job["state"] == "SUCCEEDED":
                if (run["status"] != "SUCCEEDED" or pair is None or attempt is None
                        or attempt["outcome"] != "SUCCEEDED"
                        or run["ocr_result_id"] != pair["ocr_result_id"]
                        or run["verification_result_id"] != pair["verification_result_id"]):
                    raise LostFence("Success does not belong to this complete attempt")
                result = FinalizedResults(**pair)
                self._validate_result(run, result)
                return result
            if not repo.owns(job, fence, now):
                raise LostFence("Finalize acknowledgement recovered after ownership ended")
            if repo.any_results(fence.project_id, fence.run_id):
                raise JobInvariantError("Partial results on a live job")
            return None
        return self._transaction("recover_finalize", action)
