from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import CHAR, JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


HASH_CHECK = "{column} ~ '^[0-9a-f]{{64}}$'"
UUID4_CHECK = (
    "substring({column}::text from 15 for 1) = '4' "
    "AND substring({column}::text from 20 for 1) IN ('8','9','a','b')"
)
ERROR_CODE_CHECK = "{column} IS NULL OR {column} ~ '^[A-Z][A-Z0-9_]{{0,63}}$'"


class OCRProfile(Base):
    __tablename__ = "ocr_profiles"
    __table_args__ = (
        CheckConstraint("char_length(profile_id) BETWEEN 1 AND 128", name="ck_ocr_profile_id_length"),
        CheckConstraint(HASH_CHECK.format(column="profile_digest"), name="ck_ocr_profile_digest"),
        CheckConstraint("octet_length(canonical_manifest) BETWEEN 2 AND 8388608", name="ck_ocr_profile_manifest_size"),
        CheckConstraint("char_length(engine_name) BETWEEN 1 AND 128", name="ck_ocr_profile_engine_name"),
        CheckConstraint("char_length(engine_version) BETWEEN 1 AND 128", name="ck_ocr_profile_engine_version"),
        CheckConstraint("jsonb_typeof(model_ids) = 'array'", name="ck_ocr_profile_model_ids"),
        CheckConstraint("jsonb_typeof(language_tags) = 'array'", name="ck_ocr_profile_language_tags"),
        CheckConstraint("coordinate_space = 'original-raster-v1'", name="ck_ocr_profile_coordinate_space"),
    )

    profile_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_digest: Mapped[str] = mapped_column(CHAR(64), unique=True)
    canonical_manifest: Mapped[bytes] = mapped_column(LargeBinary)
    engine_name: Mapped[str] = mapped_column(String(128))
    engine_version: Mapped[str] = mapped_column(String(128))
    model_ids: Mapped[list] = mapped_column(JSONB)
    language_tags: Mapped[list] = mapped_column(JSONB)
    coordinate_space: Mapped[str] = mapped_column(String(32))
    normalization_version: Mapped[str] = mapped_column(String(64))
    matching_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())


class VerificationRun(Base):
    __tablename__ = "verification_runs"
    __table_args__ = (
        UniqueConstraint("project_id", "client_run_id", name="uq_verification_runs_project_client"),
        UniqueConstraint("project_id", "id", name="uq_verification_runs_project_id"),
        ForeignKeyConstraint(
            ["project_id", "screenshot_id"],
            ["screenshots.project_id", "screenshots.id"],
            ondelete="RESTRICT",
            name="fk_verification_runs_screenshot",
        ),
        ForeignKeyConstraint(
            ["project_id", "id", "ocr_result_id"],
            ["ocr_results.project_id", "ocr_results.run_id", "ocr_results.id"],
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
            name="fk_verification_runs_ocr_result",
        ),
        ForeignKeyConstraint(
            ["project_id", "id", "verification_result_id"],
            ["verification_results.project_id", "verification_results.run_id", "verification_results.id"],
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
            name="fk_verification_runs_verification_result",
        ),
        CheckConstraint("protocol_version = 1 AND fingerprint_version = 1", name="ck_verification_run_versions"),
        CheckConstraint(UUID4_CHECK.format(column="client_run_id"), name="ck_verification_run_client_uuid4"),
        CheckConstraint(HASH_CHECK.format(column="request_fingerprint"), name="ck_verification_run_fingerprint"),
        CheckConstraint("octet_length(canonical_request) BETWEEN 2 AND 65536", name="ck_verification_run_request_size"),
        CheckConstraint("snapshot_version = 1 AND source_mode = 'run_creation'", name="ck_verification_run_snapshot_version"),
        CheckConstraint(HASH_CHECK.format(column="snapshot_sha256"), name="ck_verification_run_snapshot_hash"),
        CheckConstraint("octet_length(snapshot_canonical) BETWEEN 2 AND 8388608", name="ck_verification_run_snapshot_size"),
        CheckConstraint(HASH_CHECK.format(column="configuration_sha256"), name="ck_verification_run_config_hash"),
        CheckConstraint("octet_length(configuration_canonical) BETWEEN 2 AND 8388608", name="ck_verification_run_config_size"),
        CheckConstraint(HASH_CHECK.format(column="profile_digest"), name="ck_verification_run_profile_hash"),
        CheckConstraint("octet_length(profile_canonical) BETWEEN 2 AND 8388608", name="ck_verification_run_profile_size"),
        CheckConstraint(HASH_CHECK.format(column="screenshot_file_hash"), name="ck_verification_run_source_hash"),
        CheckConstraint("screenshot_size_bytes > 0 AND screenshot_width > 0 AND screenshot_height > 0", name="ck_verification_run_source_size"),
        CheckConstraint("screenshot_metadata_version = 1 AND jsonb_typeof(screenshot_metadata) = 'object'", name="ck_verification_run_metadata"),
        CheckConstraint("snapshot_item_count BETWEEN 0 AND 1000 AND snapshot_missing_count BETWEEN 0 AND snapshot_item_count", name="ck_verification_run_snapshot_counts"),
        CheckConstraint("pass_threshold BETWEEN 0 AND 100 AND review_threshold BETWEEN 0 AND 100 AND review_threshold < pass_threshold", name="ck_verification_run_thresholds"),
        CheckConstraint("status IN ('PENDING','RUNNING','RETRY_WAIT','SUCCEEDED','FAILED')", name="ck_verification_run_status"),
        CheckConstraint("stage IN ('QUEUED','OCR','VERIFY','COMPLETE')", name="ck_verification_run_stage"),
        CheckConstraint("verification_status IS NULL OR verification_status IN ('PASS','REVIEW','FAIL','UNVERIFIED')", name="ck_verification_run_quality"),
        CheckConstraint("attempt_count BETWEEN 0 AND 3", name="ck_verification_run_attempt_count"),
        CheckConstraint(ERROR_CODE_CHECK.format(column="error_code"), name="ck_verification_run_error_code"),
        CheckConstraint("error_cause_code IS NULL OR error_cause_code ~ '^[A-Z][A-Z0-9_]{0,63}$'", name="ck_verification_run_cause_code"),
        CheckConstraint("error_stage IS NULL OR error_stage IN ('QUEUED','OCR','VERIFY')", name="ck_verification_run_error_stage"),
        CheckConstraint("error_attempt IS NULL OR error_attempt BETWEEN 0 AND 3", name="ck_verification_run_error_attempt"),
        CheckConstraint(
            "(status = 'PENDING' AND stage = 'QUEUED' AND attempt_count = 0 AND started_at IS NULL AND completed_at IS NULL AND next_attempt_at IS NULL AND verification_status IS NULL AND ocr_result_id IS NULL AND verification_result_id IS NULL AND error_code IS NULL) OR "
            "(status = 'RUNNING' AND stage IN ('OCR','VERIFY') AND attempt_count BETWEEN 1 AND 3 AND started_at IS NOT NULL AND completed_at IS NULL AND next_attempt_at IS NULL AND verification_status IS NULL AND ocr_result_id IS NULL AND verification_result_id IS NULL AND error_code IS NULL) OR "
            "(status = 'RETRY_WAIT' AND stage IN ('OCR','VERIFY') AND attempt_count BETWEEN 1 AND 2 AND started_at IS NOT NULL AND completed_at IS NULL AND next_attempt_at IS NOT NULL AND verification_status IS NULL AND ocr_result_id IS NULL AND verification_result_id IS NULL AND error_code IS NOT NULL AND error_retryable IS TRUE) OR "
            "(status = 'SUCCEEDED' AND stage = 'COMPLETE' AND attempt_count BETWEEN 1 AND 3 AND started_at IS NOT NULL AND completed_at IS NOT NULL AND next_attempt_at IS NULL AND verification_status IS NOT NULL AND ocr_result_id IS NOT NULL AND verification_result_id IS NOT NULL AND error_code IS NULL) OR "
            "(status = 'FAILED' AND stage IN ('QUEUED','OCR','VERIFY') AND attempt_count BETWEEN 0 AND 3 AND completed_at IS NOT NULL AND next_attempt_at IS NULL AND verification_status IS NULL AND ocr_result_id IS NULL AND verification_result_id IS NULL AND error_code IS NOT NULL AND error_retryable IS FALSE)",
            name="ck_verification_run_lifecycle",
        ),
        CheckConstraint(
            "(error_code IS NULL AND error_correlation_id IS NULL AND error_cause_code IS NULL AND error_stage IS NULL AND error_retryable IS NULL AND error_message IS NULL AND error_attempt IS NULL) OR "
            "(error_code IS NOT NULL AND error_correlation_id IS NOT NULL AND error_stage IS NOT NULL AND error_retryable IS NOT NULL AND error_message IS NOT NULL AND error_attempt IS NOT NULL)",
            name="ck_verification_run_error_shape",
        ),
        CheckConstraint("updated_at >= created_at AND (started_at IS NULL OR started_at >= created_at) AND (completed_at IS NULL OR completed_at >= started_at)", name="ck_verification_run_timestamps"),
        Index("ix_verification_runs_history", "project_id", "screenshot_id", text("created_at DESC"), text("id DESC")),
    )

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("projects.id", ondelete="RESTRICT"))
    screenshot_id: Mapped[UUID] = mapped_column(PGUUID)
    client_run_id: Mapped[UUID] = mapped_column(PGUUID)
    protocol_version: Mapped[int] = mapped_column(Integer)
    fingerprint_version: Mapped[int] = mapped_column(Integer)
    request_fingerprint: Mapped[str] = mapped_column(CHAR(64))
    canonical_request: Mapped[bytes] = mapped_column(LargeBinary)
    profile_id: Mapped[str] = mapped_column(String(128), ForeignKey("ocr_profiles.profile_id", ondelete="RESTRICT"))
    profile_digest: Mapped[str] = mapped_column(CHAR(64))
    profile_canonical: Mapped[bytes] = mapped_column(LargeBinary)
    snapshot_version: Mapped[int] = mapped_column(Integer)
    snapshot_canonical: Mapped[bytes] = mapped_column(LargeBinary)
    snapshot_sha256: Mapped[str] = mapped_column(CHAR(64))
    captured_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    source_mode: Mapped[str] = mapped_column(String(32))
    configuration_canonical: Mapped[bytes] = mapped_column(LargeBinary)
    configuration_sha256: Mapped[str] = mapped_column(CHAR(64))
    normalization_version: Mapped[str] = mapped_column(String(64))
    matching_version: Mapped[str] = mapped_column(String(64))
    pass_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    review_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    locale_code: Mapped[str] = mapped_column(String(63))
    ocr_language: Mapped[str] = mapped_column(String(63))
    screenshot_storage_key: Mapped[str] = mapped_column(Text)
    screenshot_file_hash: Mapped[str] = mapped_column(CHAR(64))
    screenshot_size_bytes: Mapped[int] = mapped_column(BigInteger)
    screenshot_media_type: Mapped[str] = mapped_column(String(32))
    screenshot_width: Mapped[int] = mapped_column(Integer)
    screenshot_height: Mapped[int] = mapped_column(Integer)
    screenshot_build_id: Mapped[UUID] = mapped_column(PGUUID)
    screenshot_locale_id: Mapped[UUID] = mapped_column(PGUUID)
    screenshot_category_id: Mapped[UUID] = mapped_column(PGUUID)
    screenshot_situation_id: Mapped[UUID] = mapped_column(PGUUID)
    screenshot_metadata_version: Mapped[int] = mapped_column(Integer)
    screenshot_metadata: Mapped[dict] = mapped_column(JSONB)
    build_label: Mapped[str] = mapped_column(String(120))
    locale_name: Mapped[str] = mapped_column(String(120))
    category_slug: Mapped[str] = mapped_column(String(64))
    category_name: Mapped[str] = mapped_column(String(120))
    situation_slug: Mapped[str] = mapped_column(String(64))
    situation_name: Mapped[str] = mapped_column(String(120))
    situation_description: Mapped[str | None] = mapped_column(Text)
    snapshot_item_count: Mapped[int] = mapped_column(Integer)
    snapshot_missing_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))
    stage: Mapped[str] = mapped_column(String(16))
    attempt_count: Mapped[int] = mapped_column(Integer)
    next_attempt_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    verification_status: Mapped[str | None] = mapped_column(String(16))
    ocr_result_id: Mapped[UUID | None] = mapped_column(PGUUID)
    verification_result_id: Mapped[UUID | None] = mapped_column(PGUUID)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_correlation_id: Mapped[UUID | None] = mapped_column(PGUUID)
    error_cause_code: Mapped[str | None] = mapped_column(String(64))
    error_stage: Mapped[str | None] = mapped_column(String(16))
    error_retryable: Mapped[bool | None] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(String(255))
    error_attempt: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))


class VerificationExpectedItem(Base):
    __tablename__ = "verification_expected_items"
    __table_args__ = (
        PrimaryKeyConstraint("run_id", "position"),
        UniqueConstraint("project_id", "run_id", "position", name="uq_verification_expected_scope_position"),
        UniqueConstraint("run_id", "string_key_id", name="uq_verification_expected_run_key"),
        ForeignKeyConstraint(["project_id", "run_id"], ["verification_runs.project_id", "verification_runs.id"], ondelete="RESTRICT", name="fk_verification_expected_run"),
        CheckConstraint("position >= 0", name="ck_verification_expected_position"),
        CheckConstraint("char_length(string_id) BETWEEN 1 AND 128", name="ck_verification_expected_string_id"),
        CheckConstraint("expected_text IS NULL OR char_length(expected_text) <= 10000", name="ck_verification_expected_text"),
        CheckConstraint("(translation_status = 'missing' AND entry_id IS NULL AND expected_text IS NULL) OR (translation_status = 'present' AND entry_id IS NOT NULL AND expected_text IS NOT NULL)", name="ck_verification_expected_translation"),
    )
    project_id: Mapped[UUID] = mapped_column(PGUUID)
    run_id: Mapped[UUID] = mapped_column(PGUUID)
    position: Mapped[int] = mapped_column(Integer)
    string_key_id: Mapped[UUID] = mapped_column(PGUUID)
    string_id: Mapped[str] = mapped_column(String(128))
    entry_id: Mapped[UUID | None] = mapped_column(PGUUID)
    expected_text: Mapped[str | None] = mapped_column(Text)
    translation_status: Mapped[str] = mapped_column(String(16))


class VerificationJob(Base):
    __tablename__ = "verification_jobs"
    __table_args__ = (
        UniqueConstraint("project_id", "run_id", name="uq_verification_jobs_scope"),
        ForeignKeyConstraint(["project_id", "run_id"], ["verification_runs.project_id", "verification_runs.id"], ondelete="RESTRICT", name="fk_verification_jobs_run"),
        CheckConstraint("state IN ('PENDING','RUNNING','RETRY_WAIT','SUCCEEDED','FAILED')", name="ck_verification_job_state"),
        CheckConstraint("stage IN ('QUEUED','OCR','VERIFY','COMPLETE')", name="ck_verification_job_stage"),
        CheckConstraint("attempt_count BETWEEN 0 AND 3 AND generation BETWEEN 0 AND 9223372036854775807", name="ck_verification_job_counters"),
        CheckConstraint(ERROR_CODE_CHECK.format(column="last_error_code"), name="ck_verification_job_error_code"),
        CheckConstraint("last_error_cause_code IS NULL OR last_error_cause_code ~ '^[A-Z][A-Z0-9_]{0,63}$'", name="ck_verification_job_cause_code"),
        CheckConstraint("last_error_stage IS NULL OR last_error_stage IN ('QUEUED','OCR','VERIFY')", name="ck_verification_job_error_stage"),
        CheckConstraint("last_error_attempt IS NULL OR last_error_attempt BETWEEN 0 AND 3", name="ck_verification_job_error_attempt"),
        CheckConstraint(
            "(last_error_code IS NULL AND last_error_correlation_id IS NULL AND last_error_cause_code IS NULL AND last_error_stage IS NULL AND last_error_retryable IS NULL AND last_error_message IS NULL AND last_error_attempt IS NULL) OR "
            "(last_error_code IS NOT NULL AND last_error_correlation_id IS NOT NULL AND last_error_stage IS NOT NULL AND last_error_retryable IS NOT NULL AND last_error_message IS NOT NULL AND last_error_attempt IS NOT NULL)",
            name="ck_verification_job_error_shape",
        ),
        CheckConstraint(
            "(state = 'PENDING' AND stage = 'QUEUED' AND attempt_count = 0 AND generation = 0 AND attempt_token IS NULL AND lease_expires_at IS NULL AND available_at IS NOT NULL AND started_at IS NULL AND completed_at IS NULL AND next_attempt_at IS NULL AND last_error_code IS NULL) OR "
            "(state = 'RUNNING' AND stage IN ('OCR','VERIFY') AND attempt_count BETWEEN 1 AND 3 AND generation = attempt_count AND attempt_token IS NOT NULL AND lease_expires_at IS NOT NULL AND available_at IS NULL AND started_at IS NOT NULL AND completed_at IS NULL AND next_attempt_at IS NULL AND last_error_code IS NULL) OR "
            "(state = 'RETRY_WAIT' AND stage IN ('OCR','VERIFY') AND attempt_count BETWEEN 1 AND 2 AND generation = attempt_count AND attempt_token IS NULL AND lease_expires_at IS NULL AND available_at = next_attempt_at AND next_attempt_at IS NOT NULL AND started_at IS NOT NULL AND completed_at IS NULL AND last_error_code IS NOT NULL AND last_error_retryable IS TRUE) OR "
            "(state = 'SUCCEEDED' AND stage = 'COMPLETE' AND attempt_count BETWEEN 1 AND 3 AND generation = attempt_count AND attempt_token IS NULL AND lease_expires_at IS NULL AND available_at IS NULL AND next_attempt_at IS NULL AND started_at IS NOT NULL AND completed_at IS NOT NULL AND last_error_code IS NULL) OR "
            "(state = 'FAILED' AND stage IN ('QUEUED','OCR','VERIFY') AND attempt_count BETWEEN 0 AND 3 AND generation = attempt_count AND attempt_token IS NULL AND lease_expires_at IS NULL AND available_at IS NULL AND next_attempt_at IS NULL AND completed_at IS NOT NULL AND last_error_code IS NOT NULL AND last_error_retryable IS FALSE)",
            name="ck_verification_job_lifecycle",
        ),
        Index("ix_verification_jobs_due", "state", "available_at"),
        Index("ix_verification_jobs_running_lease", "lease_expires_at", postgresql_where=text("state = 'RUNNING'")),
    )
    run_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(PGUUID)
    state: Mapped[str] = mapped_column(String(16))
    stage: Mapped[str] = mapped_column(String(16))
    attempt_count: Mapped[int] = mapped_column(Integer)
    generation: Mapped[int] = mapped_column(BigInteger)
    attempt_token: Mapped[UUID | None] = mapped_column(PGUUID)
    lease_expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    available_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    next_attempt_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_correlation_id: Mapped[UUID | None] = mapped_column(PGUUID)
    last_error_cause_code: Mapped[str | None] = mapped_column(String(64))
    last_error_stage: Mapped[str | None] = mapped_column(String(16))
    last_error_retryable: Mapped[bool | None] = mapped_column(Boolean)
    last_error_message: Mapped[str | None] = mapped_column(String(255))
    last_error_attempt: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))


class VerificationAttempt(Base):
    __tablename__ = "verification_attempts"
    __table_args__ = (
        PrimaryKeyConstraint("project_id", "run_id", "generation"),
        UniqueConstraint("claim_request_id", name="uq_verification_attempt_claim"),
        UniqueConstraint("attempt_token", name="uq_verification_attempt_token"),
        ForeignKeyConstraint(["project_id", "run_id"], ["verification_jobs.project_id", "verification_jobs.run_id"], ondelete="RESTRICT", name="fk_verification_attempt_job"),
        CheckConstraint("generation BETWEEN 1 AND 3", name="ck_verification_attempt_generation"),
        CheckConstraint(UUID4_CHECK.format(column="claim_request_id"), name="ck_verification_attempt_claim_uuid4"),
        CheckConstraint(UUID4_CHECK.format(column="attempt_token"), name="ck_verification_attempt_token_uuid4"),
        CheckConstraint("outcome IN ('STARTED','SUCCEEDED','RETRY_WAIT','FAILED','EXPIRED')", name="ck_verification_attempt_outcome"),
        CheckConstraint(ERROR_CODE_CHECK.format(column="error_code"), name="ck_verification_attempt_error_code"),
        CheckConstraint("error_cause_code IS NULL OR error_cause_code ~ '^[A-Z][A-Z0-9_]{0,63}$'", name="ck_verification_attempt_cause_code"),
        CheckConstraint("error_stage IS NULL OR error_stage IN ('QUEUED','OCR','VERIFY')", name="ck_verification_attempt_error_stage"),
        CheckConstraint(
            "(outcome IN ('STARTED','SUCCEEDED') AND error_code IS NULL AND error_cause_code IS NULL AND error_stage IS NULL AND error_retryable IS NULL AND error_message IS NULL) OR "
            "(outcome IN ('RETRY_WAIT','FAILED','EXPIRED') AND error_code IS NOT NULL AND error_stage IS NOT NULL AND error_retryable IS NOT NULL AND error_message IS NOT NULL)",
            name="ck_verification_attempt_error_shape",
        ),
        CheckConstraint("(outcome = 'STARTED' AND closed_at IS NULL) OR (outcome <> 'STARTED' AND closed_at IS NOT NULL)", name="ck_verification_attempt_closed"),
        CheckConstraint("lease_at_claim > claimed_at AND (closed_at IS NULL OR closed_at >= claimed_at)", name="ck_verification_attempt_timestamps"),
    )
    project_id: Mapped[UUID] = mapped_column(PGUUID)
    run_id: Mapped[UUID] = mapped_column(PGUUID)
    generation: Mapped[int] = mapped_column(BigInteger)
    claim_request_id: Mapped[UUID] = mapped_column(PGUUID)
    attempt_token: Mapped[UUID] = mapped_column(PGUUID)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID)
    claimed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    lease_at_claim: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    outcome: Mapped[str] = mapped_column(String(16))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_cause_code: Mapped[str | None] = mapped_column(String(64))
    error_stage: Mapped[str | None] = mapped_column(String(16))
    error_retryable: Mapped[bool | None] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(String(255))
    closed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))


class OCRResult(Base):
    __tablename__ = "ocr_results"
    __table_args__ = (
        UniqueConstraint("project_id", "run_id", name="uq_ocr_results_scope_run"),
        UniqueConstraint("project_id", "run_id", "id", name="uq_ocr_results_scope_id"),
        ForeignKeyConstraint(["project_id", "run_id"], ["verification_runs.project_id", "verification_runs.id"], ondelete="RESTRICT", name="fk_ocr_results_run"),
        CheckConstraint("coordinate_space = 'original-raster-v1'", name="ck_ocr_result_coordinate_space"),
        CheckConstraint("width > 0 AND height > 0", name="ck_ocr_result_dimensions"),
        CheckConstraint("region_count BETWEEN 0 AND 1000", name="ck_ocr_result_region_count"),
        CheckConstraint(HASH_CHECK.format(column="profile_digest"), name="ck_ocr_result_profile_hash"),
        CheckConstraint(HASH_CHECK.format(column="source_sha256"), name="ck_ocr_result_source_hash"),
        CheckConstraint(HASH_CHECK.format(column="pixel_sha256"), name="ck_ocr_result_pixel_hash"),
        CheckConstraint(HASH_CHECK.format(column="output_sha256"), name="ck_ocr_result_output_hash"),
        CheckConstraint(HASH_CHECK.format(column="raw_audit_sha256"), name="ck_ocr_result_audit_hash"),
        CheckConstraint("jsonb_typeof(runtime_manifest) = 'object' AND jsonb_typeof(preprocessing) = 'object' AND jsonb_typeof(raw_audit) = 'object' AND jsonb_typeof(timings_ms) = 'object'", name="ck_ocr_result_json_objects"),
        CheckConstraint("octet_length(raw_audit::text) <= 8388608", name="ck_ocr_result_audit_size"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id: Mapped[UUID] = mapped_column(PGUUID)
    run_id: Mapped[UUID] = mapped_column(PGUUID)
    screenshot_id: Mapped[UUID] = mapped_column(PGUUID)
    coordinate_space: Mapped[str] = mapped_column(String(32))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    region_count: Mapped[int] = mapped_column(Integer)
    no_text: Mapped[bool] = mapped_column(Boolean)
    profile_id: Mapped[str] = mapped_column(String(128))
    profile_digest: Mapped[str] = mapped_column(CHAR(64))
    engine_name: Mapped[str] = mapped_column(String(128))
    engine_version: Mapped[str] = mapped_column(String(128))
    ocr_language: Mapped[str] = mapped_column(String(63))
    source_sha256: Mapped[str] = mapped_column(CHAR(64))
    pixel_sha256: Mapped[str] = mapped_column(CHAR(64))
    runtime_manifest: Mapped[dict] = mapped_column(JSONB)
    preprocessing: Mapped[dict] = mapped_column(JSONB)
    raw_audit: Mapped[dict] = mapped_column(JSONB)
    raw_audit_sha256: Mapped[str] = mapped_column(CHAR(64))
    timings_ms: Mapped[dict] = mapped_column(JSONB)
    output_sha256: Mapped[str] = mapped_column(CHAR(64))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())


class OCRRegion(Base):
    __tablename__ = "ocr_regions"
    __table_args__ = (
        PrimaryKeyConstraint("result_id", "region_index"),
        UniqueConstraint("project_id", "run_id", "result_id", "region_index", name="uq_ocr_regions_scope_index"),
        ForeignKeyConstraint(["project_id", "run_id", "result_id"], ["ocr_results.project_id", "ocr_results.run_id", "ocr_results.id"], ondelete="RESTRICT", name="fk_ocr_regions_result"),
        CheckConstraint("region_index >= 0 AND engine_region_index >= 0", name="ck_ocr_region_indices"),
        CheckConstraint("char_length(raw_text) <= 10000", name="ck_ocr_region_text"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_ocr_region_confidence"),
        CheckConstraint("detection_confidence IS NULL OR (detection_confidence >= 0.0 AND detection_confidence <= 1.0)", name="ck_ocr_region_detection_confidence"),
        CheckConstraint("confidence_semantics = 'recognition'", name="ck_ocr_region_confidence_semantics"),
        CheckConstraint("(detection_confidence IS NULL AND detection_confidence_unavailable_reason = 'NOT_EXPOSED_BY_PROFILE') OR (detection_confidence IS NOT NULL AND detection_confidence_unavailable_reason IS NULL)", name="ck_ocr_region_detection_shape"),
        CheckConstraint("bbox_x >= 0 AND bbox_y >= 0 AND bbox_width > 0 AND bbox_height > 0 AND bbox_x + bbox_width <= source_width AND bbox_y + bbox_height <= source_height", name="ck_ocr_region_bbox"),
        CheckConstraint("phase3_valid_polygon(polygon, source_width, source_height)", name="ck_ocr_region_polygon"),
    )
    project_id: Mapped[UUID] = mapped_column(PGUUID)
    run_id: Mapped[UUID] = mapped_column(PGUUID)
    result_id: Mapped[UUID] = mapped_column(PGUUID)
    region_index: Mapped[int] = mapped_column(Integer)
    engine_region_index: Mapped[int] = mapped_column(Integer)
    raw_text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float(53))
    confidence_semantics: Mapped[str] = mapped_column(String(32))
    detection_confidence: Mapped[float | None] = mapped_column(Float(53))
    detection_confidence_unavailable_reason: Mapped[str | None] = mapped_column(String(64))
    polygon: Mapped[list] = mapped_column(JSONB)
    bbox_x: Mapped[float] = mapped_column(Float(53))
    bbox_y: Mapped[float] = mapped_column(Float(53))
    bbox_width: Mapped[float] = mapped_column(Float(53))
    bbox_height: Mapped[float] = mapped_column(Float(53))
    source_width: Mapped[int] = mapped_column(Integer)
    source_height: Mapped[int] = mapped_column(Integer)
    clipped: Mapped[bool] = mapped_column(Boolean)


class VerificationResult(Base):
    __tablename__ = "verification_results"
    __table_args__ = (
        UniqueConstraint("project_id", "run_id", name="uq_verification_results_scope_run"),
        UniqueConstraint("project_id", "run_id", "id", name="uq_verification_results_scope_id"),
        ForeignKeyConstraint(["project_id", "run_id"], ["verification_runs.project_id", "verification_runs.id"], ondelete="RESTRICT", name="fk_verification_results_run"),
        ForeignKeyConstraint(["project_id", "run_id", "ocr_result_id"], ["ocr_results.project_id", "ocr_results.run_id", "ocr_results.id"], ondelete="RESTRICT", name="fk_verification_results_ocr"),
        CheckConstraint(HASH_CHECK.format(column="snapshot_sha256"), name="ck_verification_result_snapshot_hash"),
        CheckConstraint(HASH_CHECK.format(column="configuration_sha256"), name="ck_verification_result_config_hash"),
        CheckConstraint("verification_status IN ('PASS','REVIEW','FAIL','UNVERIFIED')", name="ck_verification_result_status"),
        CheckConstraint("evaluation_reason IN ('EVALUATED','PARTIAL_UNVERIFIED','NO_EVALUABLE_EXPECTATIONS','NO_EXPECTATIONS')", name="ck_verification_result_reason"),
        CheckConstraint("pass_threshold BETWEEN 0 AND 100 AND review_threshold BETWEEN 0 AND 100 AND review_threshold < pass_threshold", name="ck_verification_result_thresholds"),
        CheckConstraint("total_count >= 0 AND evaluated_count >= 0 AND unverified_count >= 0 AND pass_count >= 0 AND review_count >= 0 AND fail_count >= 0 AND unmatched_region_count >= 0", name="ck_verification_result_nonnegative"),
        CheckConstraint("evaluated_count = pass_count + review_count + fail_count AND total_count = evaluated_count + unverified_count", name="ck_verification_result_count_totals"),
        CheckConstraint("incomplete = (unverified_count > 0)", name="ck_verification_result_incomplete"),
        CheckConstraint(
            "(evaluation_reason = 'EVALUATED' AND total_count > 0 AND unverified_count = 0) OR "
            "(evaluation_reason = 'PARTIAL_UNVERIFIED' AND evaluated_count > 0 AND unverified_count > 0) OR "
            "(evaluation_reason = 'NO_EVALUABLE_EXPECTATIONS' AND total_count > 0 AND evaluated_count = 0) OR "
            "(evaluation_reason = 'NO_EXPECTATIONS' AND total_count = 0)",
            name="ck_verification_result_evaluation",
        ),
        CheckConstraint(
            "(verification_status = 'FAIL' AND fail_count > 0) OR "
            "(verification_status = 'REVIEW' AND fail_count = 0 AND review_count > 0) OR "
            "(verification_status = 'PASS' AND fail_count = 0 AND review_count = 0 AND unverified_count = 0 AND evaluated_count > 0) OR "
            "(verification_status = 'UNVERIFIED' AND fail_count = 0 AND review_count = 0 AND (unverified_count > 0 OR evaluated_count = 0))",
            name="ck_verification_result_aggregate",
        ),
    )
    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id: Mapped[UUID] = mapped_column(PGUUID)
    run_id: Mapped[UUID] = mapped_column(PGUUID)
    screenshot_id: Mapped[UUID] = mapped_column(PGUUID)
    ocr_result_id: Mapped[UUID] = mapped_column(PGUUID)
    snapshot_sha256: Mapped[str] = mapped_column(CHAR(64))
    configuration_sha256: Mapped[str] = mapped_column(CHAR(64))
    matching_version: Mapped[str] = mapped_column(String(64))
    normalization_version: Mapped[str] = mapped_column(String(64))
    verification_status: Mapped[str] = mapped_column(String(16))
    evaluation_reason: Mapped[str] = mapped_column(String(32))
    incomplete: Mapped[bool] = mapped_column(Boolean)
    total_count: Mapped[int] = mapped_column(Integer)
    evaluated_count: Mapped[int] = mapped_column(Integer)
    unverified_count: Mapped[int] = mapped_column(Integer)
    pass_count: Mapped[int] = mapped_column(Integer)
    review_count: Mapped[int] = mapped_column(Integer)
    fail_count: Mapped[int] = mapped_column(Integer)
    unmatched_region_count: Mapped[int] = mapped_column(Integer)
    pass_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    review_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())


class VerificationItem(Base):
    __tablename__ = "verification_items"
    __table_args__ = (
        PrimaryKeyConstraint("verification_result_id", "expected_position"),
        UniqueConstraint("project_id", "run_id", "verification_result_id", "expected_position", name="uq_verification_items_scope_position"),
        ForeignKeyConstraint(["project_id", "run_id", "verification_result_id"], ["verification_results.project_id", "verification_results.run_id", "verification_results.id"], ondelete="RESTRICT", name="fk_verification_items_result"),
        ForeignKeyConstraint(["project_id", "run_id", "expected_position"], ["verification_expected_items.project_id", "verification_expected_items.run_id", "verification_expected_items.position"], ondelete="RESTRICT", name="fk_verification_items_expected"),
        ForeignKeyConstraint(["project_id", "run_id", "ocr_result_id", "region_index"], ["ocr_regions.project_id", "ocr_regions.run_id", "ocr_regions.result_id", "ocr_regions.region_index"], ondelete="RESTRICT", name="fk_verification_items_region"),
        CheckConstraint("match_method IS NULL OR match_method IN ('EXACT','NORMALIZED','FUZZY','NONE')", name="ck_verification_item_method"),
        CheckConstraint("verification_status IN ('PASS','REVIEW','FAIL','UNVERIFIED')", name="ck_verification_item_status"),
        CheckConstraint("reason IN ('MATCHED','NO_MATCH','MISSING_TRANSLATION','EMPTY_EXPECTED','NORMALIZED_EMPTY_EXPECTED')", name="ck_verification_item_reason"),
        CheckConstraint("match_score IS NULL OR (match_score >= 0 AND match_score <= 100)", name="ck_verification_item_score"),
        CheckConstraint("score_denominator IS NULL OR score_denominator > 0", name="ck_verification_item_denominator"),
        CheckConstraint("score_numerator IS NULL OR (score_numerator >= 0 AND score_numerator <= 100 * score_denominator)", name="ck_verification_item_numerator"),
        CheckConstraint(
            "(verification_status = 'UNVERIFIED' AND reason IN ('MISSING_TRANSLATION','EMPTY_EXPECTED','NORMALIZED_EMPTY_EXPECTED') AND region_index IS NULL AND observed_text IS NULL AND normalized_observed IS NULL AND match_method IS NULL AND match_score IS NULL AND score_numerator IS NULL AND score_denominator IS NULL) OR "
            "(verification_status = 'FAIL' AND reason = 'NO_MATCH' AND region_index IS NULL AND observed_text IS NULL AND normalized_observed IS NULL AND match_method = 'NONE' AND match_score = 0 AND score_numerator = 0 AND score_denominator = 1) OR "
            "(verification_status IN ('PASS','REVIEW') AND reason = 'MATCHED' AND region_index IS NOT NULL AND observed_text IS NOT NULL AND normalized_observed IS NOT NULL AND match_method IN ('EXACT','NORMALIZED','FUZZY') AND match_score IS NOT NULL AND score_numerator IS NOT NULL AND score_denominator IS NOT NULL)",
            name="ck_verification_item_shape",
        ),
        CheckConstraint("(match_method IN ('EXACT','NORMALIZED') AND verification_status = 'PASS' AND match_score = 100 AND score_numerator = 100 AND score_denominator = 1) OR match_method NOT IN ('EXACT','NORMALIZED') OR match_method IS NULL", name="ck_verification_item_exact_score"),
        Index("uq_verification_items_assigned_region", "verification_result_id", "region_index", unique=True, postgresql_where=text("region_index IS NOT NULL")),
    )
    project_id: Mapped[UUID] = mapped_column(PGUUID)
    run_id: Mapped[UUID] = mapped_column(PGUUID)
    verification_result_id: Mapped[UUID] = mapped_column(PGUUID)
    ocr_result_id: Mapped[UUID] = mapped_column(PGUUID)
    expected_position: Mapped[int] = mapped_column(Integer)
    string_key_id: Mapped[UUID] = mapped_column(PGUUID)
    string_id: Mapped[str] = mapped_column(String(128))
    entry_id: Mapped[UUID | None] = mapped_column(PGUUID)
    expected_text: Mapped[str | None] = mapped_column(Text)
    normalized_expected: Mapped[str | None] = mapped_column(Text)
    translation_status: Mapped[str] = mapped_column(String(16))
    region_index: Mapped[int | None] = mapped_column(Integer)
    observed_text: Mapped[str | None] = mapped_column(Text)
    normalized_observed: Mapped[str | None] = mapped_column(Text)
    match_method: Mapped[str | None] = mapped_column(String(16))
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    score_numerator: Mapped[int | None] = mapped_column(BigInteger)
    score_denominator: Mapped[int | None] = mapped_column(BigInteger)
    verification_status: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(String(32))
