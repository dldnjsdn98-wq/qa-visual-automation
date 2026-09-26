"""P3-OCR-v1 short primary transactions, independent of UploadReceipt.

Integration column contract (SQL, no ORM class dependency): verification_runs has
status/stage/error_* columns, attempt_count, next_attempt_at, timestamps, result IDs/quality,
snapshot_canonical/snapshot_sha256, configuration_canonical/configuration_sha256,
profile_digest. Jobs use contract state/last_error_*/available_at/lease fields.
Attempts additionally store correlation_id, closed_at and error_* columns; their contract
identity and outcome fields have the exact names used below. Migration owner
must supply the scoped FKs, immutable triggers and claim_request_id uniqueness.
All methods run inside the caller's single short transaction; none commits.
"""
from datetime import timedelta
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.services.ocr_types import JobFence, JobInvariantError, LostFence

MAX_GENERATION = 2**63 - 1
ERROR_KEYS = ('code', 'correlation_id', 'cause_code', 'stage', 'retryable', 'message', 'attempt')


def error_params(error):
    return {"e_" + key: (error or {}).get(key) for key in ERROR_KEYS}


def error_set(prefix):
    return ', '.join(prefix + key + '=:e_' + key for key in ERROR_KEYS)


class VerificationRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def begin(self):
        self.session.connection(execution_options={"isolation_level": "READ COMMITTED"})
        self.session.execute(text("SET LOCAL lock_timeout = '5s'"))
        self.session.execute(text("SET LOCAL statement_timeout = '10s'"))
        self.session.execute(text("SET LOCAL idle_in_transaction_session_timeout = '10s'"))
        primary = self.session.execute(text(
            "SELECT NOT pg_is_in_recovery() AND current_setting('transaction_read_only') = 'off'"
        )).scalar_one()
        if not primary:
            raise JobInvariantError("OCR jobs require a writable primary")

    def now(self):
        return self.session.execute(text("SELECT clock_timestamp()")).scalar_one()

    def lock(self, project_id: UUID, run_id: UUID):
        return self.session.execute(text(
            "SELECT * FROM verification_jobs WHERE project_id=:p AND run_id=:r FOR UPDATE"
        ), {"p": project_id, "r": run_id}).mappings().one_or_none()

    def due(self):
        return self.session.execute(text("""
            SELECT * FROM verification_jobs
            WHERE (state IN ('PENDING','RETRY_WAIT') AND available_at <= clock_timestamp())
               OR (state='RUNNING' AND lease_expires_at <= clock_timestamp())
            ORDER BY available_at, run_id FOR UPDATE SKIP LOCKED LIMIT 1
        """)).mappings().one_or_none()

    def run(self, project_id, run_id):
        row = self.session.execute(text(
            "SELECT * FROM verification_runs WHERE project_id=:p AND id=:r"
        ), {"p": project_id, "r": run_id}).mappings().one_or_none()
        if row is None:
            raise JobInvariantError("Job is missing its scoped run")
        return row

    def attempt(self, fence: JobFence):
        return self.session.execute(text("""
            SELECT * FROM verification_attempts
            WHERE project_id=:p AND run_id=:r AND generation=:g
              AND attempt_token=:t AND claim_request_id=:c
        """), self.params(fence)).mappings().one_or_none()

    def current_attempt(self, job):
        return self.session.execute(text("""
            SELECT * FROM verification_attempts
            WHERE project_id=:p AND run_id=:r AND generation=:g AND attempt_token=:t
        """), {"p": job["project_id"], "r": job["run_id"],
                 "g": job["generation"], "t": job["attempt_token"]}).mappings().one_or_none()

    @staticmethod
    def params(fence):
        return {"p": fence.project_id, "r": fence.run_id, "g": fence.generation,
                "t": fence.attempt_token, "c": fence.claim_request_id}

    @staticmethod
    def owns(job, fence, now):
        return bool(job is not None and job["state"] == "RUNNING"
                    and job["generation"] == fence.generation
                    and job["attempt_token"] == fence.attempt_token
                    and job["lease_expires_at"] is not None
                    and job["lease_expires_at"] > now)

    def fenced(self, fence):
        job = self.lock(fence.project_id, fence.run_id)
        now = self.now()  # Deliberately AFTER acquiring the row lock.
        if not self.owns(job, fence, now):
            raise LostFence("OCR attempt no longer owns a live lease")
        attempt = self.attempt(fence)
        if attempt is None or attempt["outcome"] != "STARTED":
            raise JobInvariantError("Live job has no matching open attempt")
        run = self.run(fence.project_id, fence.run_id)
        if (run["status"] != job["state"] or run["attempt_count"] != job["attempt_count"]
                or run["stage"] != job["stage"]):
            raise JobInvariantError("Run/job lifecycle mismatch")
        return job, run, attempt, now

    def close_attempt(self, job, outcome, error=None):
        result = self.session.execute(text("""
            UPDATE verification_attempts SET outcome=:outcome, closed_at=clock_timestamp(),
              error_code=:e_code,error_cause_code=:e_cause_code,error_stage=:e_stage,
              error_retryable=:e_retryable,error_message=:e_message
            WHERE project_id=:p AND run_id=:r AND generation=:g
              AND attempt_token=:t AND outcome='STARTED'
        """), {"p": job["project_id"], "r": job["run_id"], "g": job["generation"],
                 "t": job["attempt_token"], "outcome": outcome,
                 **error_params(error)})
        if result.rowcount != 1:
            raise JobInvariantError("Attempt can only be closed once")

    def transition(self, job, *, state, stage, now, error=None, available_at=None,
                   result=None):
        """Caller MUST hold job lock and have checked worker/reaper fence."""
        terminal = state in {"SUCCEEDED", "FAILED"}
        params = {"p": job["project_id"], "r": job["run_id"], "state": state,
                  "stage": stage, "now": now, "completed": now if terminal else None,
                  **error_params(error),
                  "available": available_at,
                  "next": available_at if state == "RETRY_WAIT" else None,
                  "ocr": result.ocr_result_id if result else None,
                  "verification": result.verification_result_id if result else None,
                  "quality": result.verification_status if result else None}
        self.session.execute(text("""
            UPDATE verification_jobs SET state=:state, stage=:stage, attempt_token=NULL,
              lease_expires_at=NULL, available_at=:available, next_attempt_at=:next,
              updated_at=:now,completed_at=:completed,
        """ + error_set('last_error_') + """
            WHERE project_id=:p AND run_id=:r
        """), params)
        self.session.execute(text("""
            UPDATE verification_runs SET status=:state, stage=:stage, updated_at=:now,
              completed_at=:completed, next_attempt_at=:next,
        """ + error_set('error_') + """,
              ocr_result_id=:ocr, verification_result_id=:verification, verification_status=:quality
            WHERE project_id=:p AND id=:r
        """), params)

    def start(self, job, request_id, token, correlation_id, now):
        generation = job["generation"] + 1
        count = job["attempt_count"] + 1
        if generation > MAX_GENERATION or count > 3:
            raise JobInvariantError("Claim bounds must be checked under lock")
        lease = now + timedelta(seconds=60)
        params = {"p": job["project_id"], "r": job["run_id"], "g": generation,
                  "count": count, "token": token, "claim": request_id,
                  "correlation": correlation_id, "now": now, "lease": lease}
        self.session.execute(text("""
            INSERT INTO verification_attempts
              (project_id,run_id,generation,claim_request_id,attempt_token,
               claimed_at,lease_at_claim,outcome,correlation_id)
            VALUES (:p,:r,:g,:claim,:token,:now,:lease,'STARTED',:correlation)
        """), params)
        self.session.execute(text("""
            UPDATE verification_jobs SET state='RUNNING',stage='OCR',attempt_count=:count,
              generation=:g,attempt_token=:token,lease_expires_at=:lease,
              available_at=NULL,next_attempt_at=NULL,started_at=COALESCE(started_at,:now),updated_at=:now,
        """ + ','.join('last_error_' + key + '=NULL' for key in ERROR_KEYS) + """
            WHERE project_id=:p AND run_id=:r
        """), params)
        self.session.execute(text("""
            UPDATE verification_runs SET status='RUNNING',stage='OCR',attempt_count=:count,
              started_at=COALESCE(started_at,:now),updated_at=:now,next_attempt_at=NULL,
        """ + ','.join('error_' + key + '=NULL' for key in ERROR_KEYS) + """
            WHERE project_id=:p AND id=:r
        """), params)
        return JobFence(job["project_id"], job["run_id"], generation, token, request_id), lease

    def renew(self, fence, now):
        lease = now + timedelta(seconds=60)
        params = {**self.params(fence), "lease": lease, "now": now}
        self.session.execute(text("""
            UPDATE verification_jobs SET lease_expires_at=:lease,updated_at=:now WHERE project_id=:p AND run_id=:r
        """), params)
        self.session.execute(text("""
            UPDATE verification_runs SET updated_at=:now WHERE project_id=:p AND id=:r
        """), params)
        return lease

    def stage(self, fence, now):
        self.session.execute(text("""
            UPDATE verification_jobs SET stage='VERIFY',updated_at=:now WHERE project_id=:p AND run_id=:r
        """), {**self.params(fence), "now": now})
        self.session.execute(text("""
            UPDATE verification_runs SET stage='VERIFY',updated_at=:now WHERE project_id=:p AND id=:r
        """), {**self.params(fence), "now": now})

    def result_pair(self, project_id, run_id):
        return self.session.execute(text("""
            SELECT o.id AS ocr_result_id,v.id AS verification_result_id,
                   v.verification_status, v.snapshot_sha256, v.configuration_sha256,
                   o.profile_digest
            FROM ocr_results o JOIN verification_results v
              ON v.project_id=o.project_id AND v.run_id=o.run_id AND v.ocr_result_id=o.id
            WHERE o.project_id=:p AND o.run_id=:r
        """), {"p": project_id, "r": run_id}).mappings().one_or_none()

    def any_results(self, project_id, run_id):
        return self.session.execute(text("""
            SELECT EXISTS(SELECT 1 FROM ocr_results WHERE project_id=:p AND run_id=:r)
                OR EXISTS(SELECT 1 FROM verification_results WHERE project_id=:p AND run_id=:r)
        """), {"p": project_id, "r": run_id}).scalar_one()
