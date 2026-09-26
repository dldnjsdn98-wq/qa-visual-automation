"""phase3 OCR verification persistence

Revision ID: 0004_phase3_ocr_verification
Revises: 0003_phase2_upload_receipts
"""

from alembic import op


revision = "0004_phase3_ocr_verification"
down_revision = "0003_phase2_upload_receipts"
branch_labels = None
depends_on = None


DDL = r"""
CREATE FUNCTION phase3_valid_polygon(value jsonb, image_width integer, image_height integer)
RETURNS boolean
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    point jsonb;
    x numeric;
    y numeric;
BEGIN
    IF jsonb_typeof(value) <> 'array' OR jsonb_array_length(value) NOT BETWEEN 3 AND 8
       OR image_width <= 0 OR image_height <= 0 THEN
        RETURN false;
    END IF;
    FOR point IN SELECT elem FROM jsonb_array_elements(value) AS elements(elem) LOOP
        IF jsonb_typeof(point) <> 'array' OR jsonb_array_length(point) <> 2
           OR jsonb_typeof(point->0) <> 'number' OR jsonb_typeof(point->1) <> 'number' THEN
            RETURN false;
        END IF;
        x := (point->>0)::numeric;
        y := (point->>1)::numeric;
        IF x < 0 OR x > image_width OR y < 0 OR y > image_height
           OR scale(x) > 6 OR scale(y) > 6 THEN
            RETURN false;
        END IF;
    END LOOP;
    RETURN true;
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END
$$;

CREATE TABLE ocr_profiles (
    profile_id varchar(128) PRIMARY KEY,
    profile_digest char(64) NOT NULL UNIQUE,
    canonical_manifest bytea NOT NULL,
    engine_name varchar(128) NOT NULL,
    engine_version varchar(128) NOT NULL,
    model_ids jsonb NOT NULL,
    language_tags jsonb NOT NULL,
    coordinate_space varchar(32) NOT NULL,
    normalization_version varchar(64) NOT NULL,
    matching_version varchar(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT ck_ocr_profile_id_length CHECK (char_length(profile_id) BETWEEN 1 AND 128),
    CONSTRAINT ck_ocr_profile_digest CHECK (profile_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_ocr_profile_manifest_size CHECK (octet_length(canonical_manifest) BETWEEN 2 AND 8388608),
    CONSTRAINT ck_ocr_profile_engine_name CHECK (char_length(engine_name) BETWEEN 1 AND 128),
    CONSTRAINT ck_ocr_profile_engine_version CHECK (char_length(engine_version) BETWEEN 1 AND 128),
    CONSTRAINT ck_ocr_profile_model_ids CHECK (jsonb_typeof(model_ids) = 'array'),
    CONSTRAINT ck_ocr_profile_language_tags CHECK (jsonb_typeof(language_tags) = 'array'),
    CONSTRAINT ck_ocr_profile_coordinate_space CHECK (coordinate_space = 'original-raster-v1')
);

CREATE TABLE verification_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    screenshot_id uuid NOT NULL,
    client_run_id uuid NOT NULL,
    protocol_version integer NOT NULL,
    fingerprint_version integer NOT NULL,
    request_fingerprint char(64) NOT NULL,
    canonical_request bytea NOT NULL,
    profile_id varchar(128) NOT NULL REFERENCES ocr_profiles(profile_id) ON DELETE RESTRICT,
    profile_digest char(64) NOT NULL,
    profile_canonical bytea NOT NULL,
    snapshot_version integer NOT NULL,
    snapshot_canonical bytea NOT NULL,
    snapshot_sha256 char(64) NOT NULL,
    captured_at timestamptz NOT NULL,
    source_mode varchar(32) NOT NULL,
    configuration_canonical bytea NOT NULL,
    configuration_sha256 char(64) NOT NULL,
    normalization_version varchar(64) NOT NULL,
    matching_version varchar(64) NOT NULL,
    pass_threshold numeric(5,2) NOT NULL,
    review_threshold numeric(5,2) NOT NULL,
    locale_code varchar(63) NOT NULL,
    ocr_language varchar(63) NOT NULL,
    screenshot_storage_key text NOT NULL,
    screenshot_file_hash char(64) NOT NULL,
    screenshot_size_bytes bigint NOT NULL,
    screenshot_media_type varchar(32) NOT NULL,
    screenshot_width integer NOT NULL,
    screenshot_height integer NOT NULL,
    screenshot_build_id uuid NOT NULL,
    screenshot_locale_id uuid NOT NULL,
    screenshot_category_id uuid NOT NULL,
    screenshot_situation_id uuid NOT NULL,
    screenshot_metadata_version integer NOT NULL,
    screenshot_metadata jsonb NOT NULL,
    build_label varchar(120) NOT NULL,
    locale_name varchar(120) NOT NULL,
    category_slug varchar(64) NOT NULL,
    category_name varchar(120) NOT NULL,
    situation_slug varchar(64) NOT NULL,
    situation_name varchar(120) NOT NULL,
    situation_description text,
    snapshot_item_count integer NOT NULL,
    snapshot_missing_count integer NOT NULL,
    status varchar(16) NOT NULL,
    stage varchar(16) NOT NULL,
    attempt_count integer NOT NULL,
    next_attempt_at timestamptz,
    verification_status varchar(16),
    ocr_result_id uuid,
    verification_result_id uuid,
    error_code varchar(64),
    error_correlation_id uuid,
    error_cause_code varchar(64),
    error_stage varchar(16),
    error_retryable boolean,
    error_message varchar(255),
    error_attempt integer,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    started_at timestamptz,
    completed_at timestamptz,
    CONSTRAINT uq_verification_runs_project_client UNIQUE (project_id, client_run_id),
    CONSTRAINT uq_verification_runs_project_id UNIQUE (project_id, id),
    CONSTRAINT fk_verification_runs_screenshot FOREIGN KEY (project_id, screenshot_id) REFERENCES screenshots(project_id,id) ON DELETE RESTRICT,
    CONSTRAINT ck_verification_run_versions CHECK (protocol_version = 1 AND fingerprint_version = 1),
    CONSTRAINT ck_verification_run_client_uuid4 CHECK (substring(client_run_id::text from 15 for 1) = '4' AND substring(client_run_id::text from 20 for 1) IN ('8','9','a','b')),
    CONSTRAINT ck_verification_run_fingerprint CHECK (request_fingerprint ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_verification_run_request_size CHECK (octet_length(canonical_request) BETWEEN 2 AND 65536),
    CONSTRAINT ck_verification_run_snapshot_version CHECK (snapshot_version = 1 AND source_mode = 'run_creation'),
    CONSTRAINT ck_verification_run_snapshot_hash CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_verification_run_snapshot_size CHECK (octet_length(snapshot_canonical) BETWEEN 2 AND 8388608),
    CONSTRAINT ck_verification_run_config_hash CHECK (configuration_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_verification_run_config_size CHECK (octet_length(configuration_canonical) BETWEEN 2 AND 8388608),
    CONSTRAINT ck_verification_run_profile_hash CHECK (profile_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_verification_run_profile_size CHECK (octet_length(profile_canonical) BETWEEN 2 AND 8388608),
    CONSTRAINT ck_verification_run_source_hash CHECK (screenshot_file_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_verification_run_source_size CHECK (screenshot_size_bytes > 0 AND screenshot_width > 0 AND screenshot_height > 0),
    CONSTRAINT ck_verification_run_metadata CHECK (screenshot_metadata_version = 1 AND jsonb_typeof(screenshot_metadata) = 'object'),
    CONSTRAINT ck_verification_run_snapshot_counts CHECK (snapshot_item_count BETWEEN 0 AND 1000 AND snapshot_missing_count BETWEEN 0 AND snapshot_item_count),
    CONSTRAINT ck_verification_run_thresholds CHECK (pass_threshold BETWEEN 0 AND 100 AND review_threshold BETWEEN 0 AND 100 AND review_threshold < pass_threshold),
    CONSTRAINT ck_verification_run_status CHECK (status IN ('PENDING','RUNNING','RETRY_WAIT','SUCCEEDED','FAILED')),
    CONSTRAINT ck_verification_run_stage CHECK (stage IN ('QUEUED','OCR','VERIFY','COMPLETE')),
    CONSTRAINT ck_verification_run_quality CHECK (verification_status IS NULL OR verification_status IN ('PASS','REVIEW','FAIL','UNVERIFIED')),
    CONSTRAINT ck_verification_run_attempt_count CHECK (attempt_count BETWEEN 0 AND 3),
    CONSTRAINT ck_verification_run_error_code CHECK (error_code IS NULL OR error_code ~ '^[A-Z][A-Z0-9_]{0,63}$'),
    CONSTRAINT ck_verification_run_cause_code CHECK (error_cause_code IS NULL OR error_cause_code ~ '^[A-Z][A-Z0-9_]{0,63}$'),
    CONSTRAINT ck_verification_run_error_stage CHECK (error_stage IS NULL OR error_stage IN ('QUEUED','OCR','VERIFY')),
    CONSTRAINT ck_verification_run_error_attempt CHECK (error_attempt IS NULL OR error_attempt BETWEEN 0 AND 3),
    CONSTRAINT ck_verification_run_error_shape CHECK (
        (error_code IS NULL AND error_correlation_id IS NULL AND error_cause_code IS NULL AND error_stage IS NULL AND error_retryable IS NULL AND error_message IS NULL AND error_attempt IS NULL)
        OR (error_code IS NOT NULL AND error_correlation_id IS NOT NULL AND error_stage IS NOT NULL AND error_retryable IS NOT NULL AND error_message IS NOT NULL AND error_attempt IS NOT NULL)
    ),
    CONSTRAINT ck_verification_run_lifecycle CHECK (
        (status='PENDING' AND stage='QUEUED' AND attempt_count=0 AND started_at IS NULL AND completed_at IS NULL AND next_attempt_at IS NULL AND verification_status IS NULL AND ocr_result_id IS NULL AND verification_result_id IS NULL AND error_code IS NULL)
        OR (status='RUNNING' AND stage IN ('OCR','VERIFY') AND attempt_count BETWEEN 1 AND 3 AND started_at IS NOT NULL AND completed_at IS NULL AND next_attempt_at IS NULL AND verification_status IS NULL AND ocr_result_id IS NULL AND verification_result_id IS NULL AND error_code IS NULL)
        OR (status='RETRY_WAIT' AND stage IN ('OCR','VERIFY') AND attempt_count BETWEEN 1 AND 2 AND started_at IS NOT NULL AND completed_at IS NULL AND next_attempt_at IS NOT NULL AND verification_status IS NULL AND ocr_result_id IS NULL AND verification_result_id IS NULL AND error_code IS NOT NULL AND error_retryable IS TRUE)
        OR (status='SUCCEEDED' AND stage='COMPLETE' AND attempt_count BETWEEN 1 AND 3 AND started_at IS NOT NULL AND completed_at IS NOT NULL AND next_attempt_at IS NULL AND verification_status IS NOT NULL AND ocr_result_id IS NOT NULL AND verification_result_id IS NOT NULL AND error_code IS NULL)
        OR (status='FAILED' AND stage IN ('QUEUED','OCR','VERIFY') AND attempt_count BETWEEN 0 AND 3 AND completed_at IS NOT NULL AND next_attempt_at IS NULL AND verification_status IS NULL AND ocr_result_id IS NULL AND verification_result_id IS NULL AND error_code IS NOT NULL AND error_retryable IS FALSE)
    ),
    CONSTRAINT ck_verification_run_timestamps CHECK (updated_at >= created_at AND (started_at IS NULL OR started_at >= created_at) AND (completed_at IS NULL OR completed_at >= started_at))
);
CREATE INDEX ix_verification_runs_history ON verification_runs (project_id, screenshot_id, created_at DESC, id DESC);

CREATE TABLE verification_expected_items (
    project_id uuid NOT NULL,
    run_id uuid NOT NULL,
    position integer NOT NULL,
    string_key_id uuid NOT NULL,
    string_id varchar(128) NOT NULL,
    entry_id uuid,
    expected_text text,
    translation_status varchar(16) NOT NULL,
    PRIMARY KEY (run_id, position),
    CONSTRAINT uq_verification_expected_scope_position UNIQUE (project_id,run_id,position),
    CONSTRAINT uq_verification_expected_run_key UNIQUE (run_id,string_key_id),
    CONSTRAINT fk_verification_expected_run FOREIGN KEY (project_id,run_id) REFERENCES verification_runs(project_id,id) ON DELETE RESTRICT,
    CONSTRAINT ck_verification_expected_position CHECK (position >= 0),
    CONSTRAINT ck_verification_expected_string_id CHECK (char_length(string_id) BETWEEN 1 AND 128),
    CONSTRAINT ck_verification_expected_text CHECK (expected_text IS NULL OR char_length(expected_text) <= 10000),
    CONSTRAINT ck_verification_expected_translation CHECK ((translation_status='missing' AND entry_id IS NULL AND expected_text IS NULL) OR (translation_status='present' AND entry_id IS NOT NULL AND expected_text IS NOT NULL))
);

CREATE TABLE verification_jobs (
    run_id uuid PRIMARY KEY,
    project_id uuid NOT NULL,
    state varchar(16) NOT NULL,
    stage varchar(16) NOT NULL,
    attempt_count integer NOT NULL,
    generation bigint NOT NULL,
    attempt_token uuid,
    lease_expires_at timestamptz,
    available_at timestamptz,
    next_attempt_at timestamptz,
    last_error_code varchar(64),
    last_error_correlation_id uuid,
    last_error_cause_code varchar(64),
    last_error_stage varchar(16),
    last_error_retryable boolean,
    last_error_message varchar(255),
    last_error_attempt integer,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    started_at timestamptz,
    completed_at timestamptz,
    CONSTRAINT uq_verification_jobs_scope UNIQUE (project_id,run_id),
    CONSTRAINT fk_verification_jobs_run FOREIGN KEY (project_id,run_id) REFERENCES verification_runs(project_id,id) ON DELETE RESTRICT,
    CONSTRAINT ck_verification_job_state CHECK (state IN ('PENDING','RUNNING','RETRY_WAIT','SUCCEEDED','FAILED')),
    CONSTRAINT ck_verification_job_stage CHECK (stage IN ('QUEUED','OCR','VERIFY','COMPLETE')),
    CONSTRAINT ck_verification_job_counters CHECK (attempt_count BETWEEN 0 AND 3 AND generation BETWEEN 0 AND 9223372036854775807),
    CONSTRAINT ck_verification_job_error_code CHECK (last_error_code IS NULL OR last_error_code ~ '^[A-Z][A-Z0-9_]{0,63}$'),
    CONSTRAINT ck_verification_job_cause_code CHECK (last_error_cause_code IS NULL OR last_error_cause_code ~ '^[A-Z][A-Z0-9_]{0,63}$'),
    CONSTRAINT ck_verification_job_error_stage CHECK (last_error_stage IS NULL OR last_error_stage IN ('QUEUED','OCR','VERIFY')),
    CONSTRAINT ck_verification_job_error_attempt CHECK (last_error_attempt IS NULL OR last_error_attempt BETWEEN 0 AND 3),
    CONSTRAINT ck_verification_job_error_shape CHECK ((last_error_code IS NULL AND last_error_correlation_id IS NULL AND last_error_cause_code IS NULL AND last_error_stage IS NULL AND last_error_retryable IS NULL AND last_error_message IS NULL AND last_error_attempt IS NULL) OR (last_error_code IS NOT NULL AND last_error_correlation_id IS NOT NULL AND last_error_stage IS NOT NULL AND last_error_retryable IS NOT NULL AND last_error_message IS NOT NULL AND last_error_attempt IS NOT NULL)),
    CONSTRAINT ck_verification_job_lifecycle CHECK (
        (state='PENDING' AND stage='QUEUED' AND attempt_count=0 AND generation=0 AND attempt_token IS NULL AND lease_expires_at IS NULL AND available_at IS NOT NULL AND started_at IS NULL AND completed_at IS NULL AND next_attempt_at IS NULL AND last_error_code IS NULL)
        OR (state='RUNNING' AND stage IN ('OCR','VERIFY') AND attempt_count BETWEEN 1 AND 3 AND generation=attempt_count AND attempt_token IS NOT NULL AND lease_expires_at IS NOT NULL AND available_at IS NULL AND started_at IS NOT NULL AND completed_at IS NULL AND next_attempt_at IS NULL AND last_error_code IS NULL)
        OR (state='RETRY_WAIT' AND stage IN ('OCR','VERIFY') AND attempt_count BETWEEN 1 AND 2 AND generation=attempt_count AND attempt_token IS NULL AND lease_expires_at IS NULL AND available_at=next_attempt_at AND next_attempt_at IS NOT NULL AND started_at IS NOT NULL AND completed_at IS NULL AND last_error_code IS NOT NULL AND last_error_retryable IS TRUE)
        OR (state='SUCCEEDED' AND stage='COMPLETE' AND attempt_count BETWEEN 1 AND 3 AND generation=attempt_count AND attempt_token IS NULL AND lease_expires_at IS NULL AND available_at IS NULL AND next_attempt_at IS NULL AND started_at IS NOT NULL AND completed_at IS NOT NULL AND last_error_code IS NULL)
        OR (state='FAILED' AND stage IN ('QUEUED','OCR','VERIFY') AND attempt_count BETWEEN 0 AND 3 AND generation=attempt_count AND attempt_token IS NULL AND lease_expires_at IS NULL AND available_at IS NULL AND next_attempt_at IS NULL AND completed_at IS NOT NULL AND last_error_code IS NOT NULL AND last_error_retryable IS FALSE)
    )
);
CREATE INDEX ix_verification_jobs_due ON verification_jobs (state,available_at);
CREATE INDEX ix_verification_jobs_running_lease ON verification_jobs (lease_expires_at) WHERE state='RUNNING';

CREATE TABLE verification_attempts (
    project_id uuid NOT NULL,
    run_id uuid NOT NULL,
    generation bigint NOT NULL,
    claim_request_id uuid NOT NULL,
    attempt_token uuid NOT NULL,
    correlation_id uuid NOT NULL,
    claimed_at timestamptz NOT NULL,
    lease_at_claim timestamptz NOT NULL,
    outcome varchar(16) NOT NULL,
    error_code varchar(64),
    error_cause_code varchar(64),
    error_stage varchar(16),
    error_retryable boolean,
    error_message varchar(255),
    closed_at timestamptz,
    PRIMARY KEY (project_id,run_id,generation),
    CONSTRAINT uq_verification_attempt_claim UNIQUE (claim_request_id),
    CONSTRAINT uq_verification_attempt_token UNIQUE (attempt_token),
    CONSTRAINT fk_verification_attempt_job FOREIGN KEY (project_id,run_id) REFERENCES verification_jobs(project_id,run_id) ON DELETE RESTRICT,
    CONSTRAINT ck_verification_attempt_generation CHECK (generation BETWEEN 1 AND 3),
    CONSTRAINT ck_verification_attempt_claim_uuid4 CHECK (substring(claim_request_id::text from 15 for 1)='4' AND substring(claim_request_id::text from 20 for 1) IN ('8','9','a','b')),
    CONSTRAINT ck_verification_attempt_token_uuid4 CHECK (substring(attempt_token::text from 15 for 1)='4' AND substring(attempt_token::text from 20 for 1) IN ('8','9','a','b')),
    CONSTRAINT ck_verification_attempt_outcome CHECK (outcome IN ('STARTED','SUCCEEDED','RETRY_WAIT','FAILED','EXPIRED')),
    CONSTRAINT ck_verification_attempt_error_code CHECK (error_code IS NULL OR error_code ~ '^[A-Z][A-Z0-9_]{0,63}$'),
    CONSTRAINT ck_verification_attempt_cause_code CHECK (error_cause_code IS NULL OR error_cause_code ~ '^[A-Z][A-Z0-9_]{0,63}$'),
    CONSTRAINT ck_verification_attempt_error_stage CHECK (error_stage IS NULL OR error_stage IN ('QUEUED','OCR','VERIFY')),
    CONSTRAINT ck_verification_attempt_error_shape CHECK ((outcome IN ('STARTED','SUCCEEDED') AND error_code IS NULL AND error_cause_code IS NULL AND error_stage IS NULL AND error_retryable IS NULL AND error_message IS NULL) OR (outcome IN ('RETRY_WAIT','FAILED','EXPIRED') AND error_code IS NOT NULL AND error_stage IS NOT NULL AND error_retryable IS NOT NULL AND error_message IS NOT NULL)),
    CONSTRAINT ck_verification_attempt_closed CHECK ((outcome='STARTED' AND closed_at IS NULL) OR (outcome<>'STARTED' AND closed_at IS NOT NULL)),
    CONSTRAINT ck_verification_attempt_timestamps CHECK (lease_at_claim > claimed_at AND (closed_at IS NULL OR closed_at >= claimed_at))
);

CREATE TABLE ocr_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL, run_id uuid NOT NULL, screenshot_id uuid NOT NULL,
    coordinate_space varchar(32) NOT NULL, width integer NOT NULL, height integer NOT NULL, region_count integer NOT NULL, no_text boolean NOT NULL,
    profile_id varchar(128) NOT NULL, profile_digest char(64) NOT NULL, engine_name varchar(128) NOT NULL, engine_version varchar(128) NOT NULL,
    ocr_language varchar(63) NOT NULL, source_sha256 char(64) NOT NULL, pixel_sha256 char(64) NOT NULL,
    runtime_manifest jsonb NOT NULL, preprocessing jsonb NOT NULL, raw_audit jsonb NOT NULL, raw_audit_sha256 char(64) NOT NULL,
    timings_ms jsonb NOT NULL, output_sha256 char(64) NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_ocr_results_scope_run UNIQUE(project_id,run_id), CONSTRAINT uq_ocr_results_scope_id UNIQUE(project_id,run_id,id),
    CONSTRAINT fk_ocr_results_run FOREIGN KEY(project_id,run_id) REFERENCES verification_runs(project_id,id) ON DELETE RESTRICT,
    CONSTRAINT ck_ocr_result_coordinate_space CHECK(coordinate_space='original-raster-v1'),
    CONSTRAINT ck_ocr_result_dimensions CHECK(width>0 AND height>0), CONSTRAINT ck_ocr_result_region_count CHECK(region_count BETWEEN 0 AND 1000),
    CONSTRAINT ck_ocr_result_profile_hash CHECK(profile_digest ~ '^[0-9a-f]{64}$'), CONSTRAINT ck_ocr_result_source_hash CHECK(source_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_ocr_result_pixel_hash CHECK(pixel_sha256 ~ '^[0-9a-f]{64}$'), CONSTRAINT ck_ocr_result_output_hash CHECK(output_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_ocr_result_audit_hash CHECK(raw_audit_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_ocr_result_json_objects CHECK(jsonb_typeof(runtime_manifest)='object' AND jsonb_typeof(preprocessing)='object' AND jsonb_typeof(raw_audit)='object' AND jsonb_typeof(timings_ms)='object'),
    CONSTRAINT ck_ocr_result_audit_size CHECK(octet_length(raw_audit::text)<=8388608)
);

CREATE TABLE ocr_regions (
    project_id uuid NOT NULL, run_id uuid NOT NULL, result_id uuid NOT NULL, region_index integer NOT NULL, engine_region_index integer NOT NULL,
    raw_text text NOT NULL, confidence double precision NOT NULL, confidence_semantics varchar(32) NOT NULL,
    detection_confidence double precision, detection_confidence_unavailable_reason varchar(64), polygon jsonb NOT NULL,
    bbox_x double precision NOT NULL, bbox_y double precision NOT NULL, bbox_width double precision NOT NULL, bbox_height double precision NOT NULL,
    source_width integer NOT NULL, source_height integer NOT NULL, clipped boolean NOT NULL,
    PRIMARY KEY(result_id,region_index), CONSTRAINT uq_ocr_regions_scope_index UNIQUE(project_id,run_id,result_id,region_index),
    CONSTRAINT fk_ocr_regions_result FOREIGN KEY(project_id,run_id,result_id) REFERENCES ocr_results(project_id,run_id,id) ON DELETE RESTRICT,
    CONSTRAINT ck_ocr_region_indices CHECK(region_index>=0 AND engine_region_index>=0), CONSTRAINT ck_ocr_region_text CHECK(char_length(raw_text)<=10000),
    CONSTRAINT ck_ocr_region_confidence CHECK(confidence>=0.0 AND confidence<=1.0),
    CONSTRAINT ck_ocr_region_detection_confidence CHECK(detection_confidence IS NULL OR (detection_confidence>=0.0 AND detection_confidence<=1.0)),
    CONSTRAINT ck_ocr_region_confidence_semantics CHECK(confidence_semantics='recognition'),
    CONSTRAINT ck_ocr_region_detection_shape CHECK((detection_confidence IS NULL AND detection_confidence_unavailable_reason='NOT_EXPOSED_BY_PROFILE') OR (detection_confidence IS NOT NULL AND detection_confidence_unavailable_reason IS NULL)),
    CONSTRAINT ck_ocr_region_bbox CHECK(bbox_x>=0 AND bbox_y>=0 AND bbox_width>0 AND bbox_height>0 AND bbox_x+bbox_width<=source_width AND bbox_y+bbox_height<=source_height),
    CONSTRAINT ck_ocr_region_polygon CHECK(phase3_valid_polygon(polygon,source_width,source_height))
);

CREATE TABLE verification_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL, run_id uuid NOT NULL, screenshot_id uuid NOT NULL, ocr_result_id uuid NOT NULL,
    snapshot_sha256 char(64) NOT NULL, configuration_sha256 char(64) NOT NULL, matching_version varchar(64) NOT NULL, normalization_version varchar(64) NOT NULL,
    verification_status varchar(16) NOT NULL, evaluation_reason varchar(32) NOT NULL, incomplete boolean NOT NULL,
    total_count integer NOT NULL, evaluated_count integer NOT NULL, unverified_count integer NOT NULL, pass_count integer NOT NULL, review_count integer NOT NULL, fail_count integer NOT NULL, unmatched_region_count integer NOT NULL,
    pass_threshold numeric(5,2) NOT NULL, review_threshold numeric(5,2) NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_verification_results_scope_run UNIQUE(project_id,run_id), CONSTRAINT uq_verification_results_scope_id UNIQUE(project_id,run_id,id),
    CONSTRAINT fk_verification_results_run FOREIGN KEY(project_id,run_id) REFERENCES verification_runs(project_id,id) ON DELETE RESTRICT,
    CONSTRAINT fk_verification_results_ocr FOREIGN KEY(project_id,run_id,ocr_result_id) REFERENCES ocr_results(project_id,run_id,id) ON DELETE RESTRICT,
    CONSTRAINT ck_verification_result_snapshot_hash CHECK(snapshot_sha256 ~ '^[0-9a-f]{64}$'), CONSTRAINT ck_verification_result_config_hash CHECK(configuration_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_verification_result_status CHECK(verification_status IN ('PASS','REVIEW','FAIL','UNVERIFIED')),
    CONSTRAINT ck_verification_result_reason CHECK(evaluation_reason IN ('EVALUATED','PARTIAL_UNVERIFIED','NO_EVALUABLE_EXPECTATIONS','NO_EXPECTATIONS')),
    CONSTRAINT ck_verification_result_thresholds CHECK(pass_threshold BETWEEN 0 AND 100 AND review_threshold BETWEEN 0 AND 100 AND review_threshold<pass_threshold),
    CONSTRAINT ck_verification_result_nonnegative CHECK(total_count>=0 AND evaluated_count>=0 AND unverified_count>=0 AND pass_count>=0 AND review_count>=0 AND fail_count>=0 AND unmatched_region_count>=0),
    CONSTRAINT ck_verification_result_count_totals CHECK(evaluated_count=pass_count+review_count+fail_count AND total_count=evaluated_count+unverified_count),
    CONSTRAINT ck_verification_result_incomplete CHECK(incomplete=(unverified_count>0)),
    CONSTRAINT ck_verification_result_evaluation CHECK((evaluation_reason='EVALUATED' AND total_count>0 AND unverified_count=0) OR (evaluation_reason='PARTIAL_UNVERIFIED' AND evaluated_count>0 AND unverified_count>0) OR (evaluation_reason='NO_EVALUABLE_EXPECTATIONS' AND total_count>0 AND evaluated_count=0) OR (evaluation_reason='NO_EXPECTATIONS' AND total_count=0)),
    CONSTRAINT ck_verification_result_aggregate CHECK((verification_status='FAIL' AND fail_count>0) OR (verification_status='REVIEW' AND fail_count=0 AND review_count>0) OR (verification_status='PASS' AND fail_count=0 AND review_count=0 AND unverified_count=0 AND evaluated_count>0) OR (verification_status='UNVERIFIED' AND fail_count=0 AND review_count=0 AND (unverified_count>0 OR evaluated_count=0)))
);

CREATE TABLE verification_items (
    project_id uuid NOT NULL, run_id uuid NOT NULL, verification_result_id uuid NOT NULL, ocr_result_id uuid NOT NULL, expected_position integer NOT NULL,
    string_key_id uuid NOT NULL, string_id varchar(128) NOT NULL, entry_id uuid, expected_text text, normalized_expected text, translation_status varchar(16) NOT NULL,
    region_index integer, observed_text text, normalized_observed text, match_method varchar(16), match_score numeric(12,6), score_numerator bigint, score_denominator bigint,
    verification_status varchar(16) NOT NULL, reason varchar(32) NOT NULL,
    PRIMARY KEY(verification_result_id,expected_position), CONSTRAINT uq_verification_items_scope_position UNIQUE(project_id,run_id,verification_result_id,expected_position),
    CONSTRAINT fk_verification_items_result FOREIGN KEY(project_id,run_id,verification_result_id) REFERENCES verification_results(project_id,run_id,id) ON DELETE RESTRICT,
    CONSTRAINT fk_verification_items_expected FOREIGN KEY(project_id,run_id,expected_position) REFERENCES verification_expected_items(project_id,run_id,position) ON DELETE RESTRICT,
    CONSTRAINT fk_verification_items_region FOREIGN KEY(project_id,run_id,ocr_result_id,region_index) REFERENCES ocr_regions(project_id,run_id,result_id,region_index) ON DELETE RESTRICT,
    CONSTRAINT ck_verification_item_method CHECK(match_method IS NULL OR match_method IN ('EXACT','NORMALIZED','FUZZY','NONE')),
    CONSTRAINT ck_verification_item_status CHECK(verification_status IN ('PASS','REVIEW','FAIL','UNVERIFIED')),
    CONSTRAINT ck_verification_item_reason CHECK(reason IN ('MATCHED','NO_MATCH','MISSING_TRANSLATION','EMPTY_EXPECTED','NORMALIZED_EMPTY_EXPECTED')),
    CONSTRAINT ck_verification_item_score CHECK(match_score IS NULL OR (match_score>=0 AND match_score<=100)), CONSTRAINT ck_verification_item_denominator CHECK(score_denominator IS NULL OR score_denominator>0),
    CONSTRAINT ck_verification_item_numerator CHECK(score_numerator IS NULL OR (score_numerator>=0 AND score_numerator<=100*score_denominator)),
    CONSTRAINT ck_verification_item_shape CHECK((verification_status='UNVERIFIED' AND reason IN ('MISSING_TRANSLATION','EMPTY_EXPECTED','NORMALIZED_EMPTY_EXPECTED') AND region_index IS NULL AND observed_text IS NULL AND normalized_observed IS NULL AND match_method IS NULL AND match_score IS NULL AND score_numerator IS NULL AND score_denominator IS NULL) OR (verification_status='FAIL' AND reason='NO_MATCH' AND region_index IS NULL AND observed_text IS NULL AND normalized_observed IS NULL AND match_method='NONE' AND match_score=0 AND score_numerator=0 AND score_denominator=1) OR (verification_status IN ('PASS','REVIEW') AND reason='MATCHED' AND region_index IS NOT NULL AND observed_text IS NOT NULL AND normalized_observed IS NOT NULL AND match_method IN ('EXACT','NORMALIZED','FUZZY') AND match_score IS NOT NULL AND score_numerator IS NOT NULL AND score_denominator IS NOT NULL)),
    CONSTRAINT ck_verification_item_exact_score CHECK((match_method IN ('EXACT','NORMALIZED') AND verification_status='PASS' AND match_score=100 AND score_numerator=100 AND score_denominator=1) OR match_method NOT IN ('EXACT','NORMALIZED') OR match_method IS NULL)
);
CREATE UNIQUE INDEX uq_verification_items_assigned_region ON verification_items(verification_result_id,region_index) WHERE region_index IS NOT NULL;

ALTER TABLE verification_runs ADD CONSTRAINT fk_verification_runs_ocr_result FOREIGN KEY(project_id,id,ocr_result_id) REFERENCES ocr_results(project_id,run_id,id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE verification_runs ADD CONSTRAINT fk_verification_runs_verification_result FOREIGN KEY(project_id,id,verification_result_id) REFERENCES verification_results(project_id,run_id,id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;

CREATE FUNCTION phase3_reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION USING ERRCODE='23000', MESSAGE=TG_TABLE_NAME || ' is append-only';
END
$$;

CREATE FUNCTION phase3_guard_run() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE old_fixed jsonb; new_fixed jsonb;
BEGIN
    IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification_runs are retained'; END IF;
    old_fixed := to_jsonb(OLD) - ARRAY['status','stage','attempt_count','next_attempt_at','verification_status','ocr_result_id','verification_result_id','error_code','error_correlation_id','error_cause_code','error_stage','error_retryable','error_message','error_attempt','updated_at','started_at','completed_at']::text[];
    new_fixed := to_jsonb(NEW) - ARRAY['status','stage','attempt_count','next_attempt_at','verification_status','ocr_result_id','verification_result_id','error_code','error_correlation_id','error_cause_code','error_stage','error_retryable','error_message','error_attempt','updated_at','started_at','completed_at']::text[];
    IF old_fixed IS DISTINCT FROM new_fixed THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification run immutable input changed'; END IF;
    IF OLD.status IN ('SUCCEEDED','FAILED') THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='terminal verification run is immutable'; END IF;
    IF NOT ((OLD.status='PENDING' AND NEW.status IN ('PENDING','RUNNING')) OR (OLD.status='RUNNING' AND NEW.status IN ('RUNNING','RETRY_WAIT','SUCCEEDED','FAILED')) OR (OLD.status='RETRY_WAIT' AND NEW.status IN ('RETRY_WAIT','RUNNING'))) THEN
        RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='invalid verification run transition';
    END IF;
    IF NEW.attempt_count < OLD.attempt_count OR (OLD.started_at IS NOT NULL AND NEW.started_at IS DISTINCT FROM OLD.started_at) OR NEW.updated_at < OLD.updated_at THEN
        RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification run lifecycle regressed';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION phase3_guard_job() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE now_db timestamptz := clock_timestamp(); old_fixed jsonb; new_fixed jsonb;
BEGIN
    IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification_jobs are retained'; END IF;
    old_fixed := to_jsonb(OLD) - ARRAY['state','stage','attempt_count','generation','attempt_token','lease_expires_at','available_at','next_attempt_at','last_error_code','last_error_correlation_id','last_error_cause_code','last_error_stage','last_error_retryable','last_error_message','last_error_attempt','updated_at','started_at','completed_at']::text[];
    new_fixed := to_jsonb(NEW) - ARRAY['state','stage','attempt_count','generation','attempt_token','lease_expires_at','available_at','next_attempt_at','last_error_code','last_error_correlation_id','last_error_cause_code','last_error_stage','last_error_retryable','last_error_message','last_error_attempt','updated_at','started_at','completed_at']::text[];
    IF old_fixed IS DISTINCT FROM new_fixed THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification job identity changed'; END IF;
    IF OLD.state IN ('SUCCEEDED','FAILED') THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='terminal verification job is immutable'; END IF;
    IF NEW.updated_at < OLD.updated_at OR NEW.generation < OLD.generation OR NEW.attempt_count < OLD.attempt_count THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification job lifecycle regressed'; END IF;
    IF OLD.state IN ('PENDING','RETRY_WAIT') AND NEW.state='RUNNING' THEN
        IF NEW.generation<>OLD.generation+1 OR NEW.attempt_count<>OLD.attempt_count+1 OR NEW.lease_expires_at<=now_db THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='invalid verification job claim'; END IF;
    ELSIF OLD.state='RUNNING' AND NEW.state='RUNNING' AND NEW.generation=OLD.generation THEN
        IF OLD.lease_expires_at<=now_db OR NEW.attempt_token IS DISTINCT FROM OLD.attempt_token OR NEW.attempt_count<>OLD.attempt_count OR NEW.lease_expires_at<OLD.lease_expires_at THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='stale verification job mutation'; END IF;
    ELSIF OLD.state='RUNNING' AND NEW.state='RUNNING' AND NEW.generation=OLD.generation+1 THEN
        IF OLD.lease_expires_at>now_db OR OLD.attempt_count>=3 OR NEW.attempt_count<>OLD.attempt_count+1 OR NEW.lease_expires_at<=now_db THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='invalid expired job takeover'; END IF;
    ELSIF OLD.state='RUNNING' AND NEW.state IN ('RETRY_WAIT','SUCCEEDED') THEN
        IF OLD.lease_expires_at<=now_db OR NEW.generation<>OLD.generation OR NEW.attempt_count<>OLD.attempt_count THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='stale verification job completion'; END IF;
    ELSIF OLD.state='RUNNING' AND NEW.state='FAILED' THEN
        IF NEW.generation<>OLD.generation OR NEW.attempt_count<>OLD.attempt_count OR NOT ((OLD.lease_expires_at>now_db) OR (OLD.lease_expires_at<=now_db AND OLD.attempt_count=3 AND NEW.last_error_code='RETRY_EXHAUSTED')) THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='invalid verification job failure'; END IF;
    ELSIF NEW.state=OLD.state AND OLD.state IN ('PENDING','RETRY_WAIT') THEN
        NULL;
    ELSE RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='invalid verification job transition';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION phase3_guard_attempt() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification attempts are retained'; END IF;
    IF OLD.outcome<>'STARTED' THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='completed verification attempt is immutable'; END IF;
    IF NEW.outcome='STARTED' OR ROW(NEW.project_id,NEW.run_id,NEW.generation,NEW.claim_request_id,NEW.attempt_token,NEW.correlation_id,NEW.claimed_at,NEW.lease_at_claim) IS DISTINCT FROM ROW(OLD.project_id,OLD.run_id,OLD.generation,OLD.claim_request_id,OLD.attempt_token,OLD.correlation_id,OLD.claimed_at,OLD.lease_at_claim) THEN
        RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='invalid verification attempt closure';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION phase3_round_half_even_6(value numeric) RETURNS numeric
LANGUAGE SQL IMMUTABLE STRICT AS $$
    SELECT CASE
        WHEN value * 1000000 - trunc(value * 1000000) = 0.5 THEN
            (CASE WHEN mod(trunc(value * 1000000), 2) = 0
                  THEN trunc(value * 1000000)
                  ELSE trunc(value * 1000000) + 1 END) / 1000000
        ELSE round(value, 6)
    END
$$;

CREATE FUNCTION phase3_guard_item_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected verification_expected_items%ROWTYPE; result verification_results%ROWTYPE; rounded numeric(12,6);
BEGIN
    SELECT * INTO STRICT expected FROM verification_expected_items WHERE project_id=NEW.project_id AND run_id=NEW.run_id AND position=NEW.expected_position;
    SELECT * INTO STRICT result FROM verification_results WHERE project_id=NEW.project_id AND run_id=NEW.run_id AND id=NEW.verification_result_id;
    IF ROW(NEW.string_key_id,NEW.string_id,NEW.entry_id,NEW.expected_text,NEW.translation_status) IS DISTINCT FROM ROW(expected.string_key_id,expected.string_id,expected.entry_id,expected.expected_text,expected.translation_status) OR NEW.ocr_result_id<>result.ocr_result_id THEN
        RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification item provenance mismatch';
    END IF;
    IF NEW.score_numerator IS NOT NULL THEN
        rounded := phase3_round_half_even_6(NEW.score_numerator::numeric / NEW.score_denominator::numeric);
        IF NEW.match_score IS DISTINCT FROM rounded THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification item rational score mismatch'; END IF;
    END IF;
    IF NEW.match_method='FUZZY' AND NOT ((NEW.verification_status='PASS' AND NEW.score_numerator>=result.pass_threshold*NEW.score_denominator) OR (NEW.verification_status='REVIEW' AND NEW.score_numerator>=result.review_threshold*NEW.score_denominator AND NEW.score_numerator<result.pass_threshold*NEW.score_denominator)) THEN
        RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification item threshold classification mismatch';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION phase3_check_lifecycle() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p uuid; r_id uuid; new_json jsonb := to_jsonb(NEW); old_json jsonb := to_jsonb(OLD); run_row verification_runs%ROWTYPE; job_row verification_jobs%ROWTYPE; ocr_row ocr_results%ROWTYPE; verification_row verification_results%ROWTYPE; n integer; latest_outcome varchar(16); latest_token uuid;
BEGIN
    p := COALESCE((new_json->>'project_id')::uuid,(old_json->>'project_id')::uuid);
    r_id := COALESCE((new_json->>'run_id')::uuid,(old_json->>'run_id')::uuid,(new_json->>'id')::uuid,(old_json->>'id')::uuid);
    SELECT * INTO run_row FROM verification_runs WHERE project_id=p AND id=r_id;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification lifecycle lost its run'; END IF;
    SELECT * INTO STRICT job_row FROM verification_jobs WHERE project_id=p AND run_id=r_id;
    IF ROW(run_row.status,run_row.stage,run_row.attempt_count,run_row.next_attempt_at,run_row.started_at,run_row.completed_at,run_row.error_code,run_row.error_correlation_id,run_row.error_cause_code,run_row.error_stage,run_row.error_retryable,run_row.error_message,run_row.error_attempt)
       IS DISTINCT FROM ROW(job_row.state,job_row.stage,job_row.attempt_count,job_row.next_attempt_at,job_row.started_at,job_row.completed_at,job_row.last_error_code,job_row.last_error_correlation_id,job_row.last_error_cause_code,job_row.last_error_stage,job_row.last_error_retryable,job_row.last_error_message,job_row.last_error_attempt) THEN
        RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification run and job lifecycle disagree';
    END IF;
    SELECT count(*) INTO n FROM verification_expected_items WHERE project_id=p AND run_id=r_id;
    IF n<>run_row.snapshot_item_count THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification expected snapshot count mismatch'; END IF;
    SELECT count(*) INTO n FROM verification_expected_items WHERE project_id=p AND run_id=r_id AND translation_status='missing';
    IF n<>run_row.snapshot_missing_count THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification expected missing count mismatch'; END IF;
    SELECT count(*) INTO n FROM verification_attempts WHERE project_id=p AND run_id=r_id;
    IF n<>job_row.attempt_count THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification attempt count mismatch'; END IF;
    IF job_row.attempt_count>0 THEN
        SELECT outcome,attempt_token INTO STRICT latest_outcome,latest_token FROM verification_attempts WHERE project_id=p AND run_id=r_id AND generation=job_row.generation;
        IF (job_row.state='RUNNING' AND (latest_outcome<>'STARTED' OR latest_token<>job_row.attempt_token))
           OR (job_row.state='RETRY_WAIT' AND latest_outcome<>'RETRY_WAIT')
           OR (job_row.state='SUCCEEDED' AND latest_outcome<>'SUCCEEDED')
           OR (job_row.state='FAILED' AND latest_outcome NOT IN ('FAILED','EXPIRED')) THEN
            RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification current attempt outcome mismatch';
        END IF;
    END IF;
    IF run_row.status='SUCCEEDED' THEN
        SELECT * INTO STRICT ocr_row FROM ocr_results WHERE project_id=p AND run_id=r_id;
        SELECT * INTO STRICT verification_row FROM verification_results WHERE project_id=p AND run_id=r_id;
        IF run_row.ocr_result_id<>ocr_row.id OR run_row.verification_result_id<>verification_row.id OR run_row.verification_status<>verification_row.verification_status OR ocr_row.screenshot_id<>run_row.screenshot_id OR verification_row.screenshot_id<>run_row.screenshot_id OR ocr_row.profile_id<>run_row.profile_id OR ocr_row.profile_digest<>run_row.profile_digest OR ocr_row.source_sha256<>run_row.screenshot_file_hash OR ocr_row.width<>run_row.screenshot_width OR ocr_row.height<>run_row.screenshot_height OR verification_row.ocr_result_id<>ocr_row.id OR verification_row.snapshot_sha256<>run_row.snapshot_sha256 OR verification_row.configuration_sha256<>run_row.configuration_sha256 OR verification_row.matching_version<>run_row.matching_version OR verification_row.normalization_version<>run_row.normalization_version OR verification_row.pass_threshold<>run_row.pass_threshold OR verification_row.review_threshold<>run_row.review_threshold OR verification_row.total_count<>run_row.snapshot_item_count THEN
            RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification completed result provenance mismatch';
        END IF;
        SELECT count(*) INTO n FROM ocr_regions WHERE project_id=p AND run_id=r_id AND result_id=ocr_row.id;
        IF n<>ocr_row.region_count THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='OCR region count mismatch'; END IF;
        SELECT count(*) INTO n FROM verification_items WHERE project_id=p AND run_id=r_id AND verification_result_id=verification_row.id;
        IF n<>verification_row.total_count THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='verification item count mismatch'; END IF;
    ELSE
        IF EXISTS(SELECT 1 FROM ocr_results WHERE project_id=p AND run_id=r_id) OR EXISTS(SELECT 1 FROM verification_results WHERE project_id=p AND run_id=r_id) THEN RAISE EXCEPTION USING ERRCODE='23000', MESSAGE='non-successful run has public results'; END IF;
    END IF;
    RETURN NULL;
END
$$;

CREATE TRIGGER trg_phase3_profiles_immutable BEFORE UPDATE OR DELETE ON ocr_profiles FOR EACH ROW EXECUTE FUNCTION phase3_reject_mutation();
CREATE TRIGGER trg_phase3_runs_guard BEFORE UPDATE OR DELETE ON verification_runs FOR EACH ROW EXECUTE FUNCTION phase3_guard_run();
CREATE TRIGGER trg_phase3_expected_immutable BEFORE UPDATE OR DELETE ON verification_expected_items FOR EACH ROW EXECUTE FUNCTION phase3_reject_mutation();
CREATE TRIGGER trg_phase3_jobs_guard BEFORE UPDATE OR DELETE ON verification_jobs FOR EACH ROW EXECUTE FUNCTION phase3_guard_job();
CREATE TRIGGER trg_phase3_attempts_guard BEFORE UPDATE OR DELETE ON verification_attempts FOR EACH ROW EXECUTE FUNCTION phase3_guard_attempt();
CREATE TRIGGER trg_phase3_ocr_results_immutable BEFORE UPDATE OR DELETE ON ocr_results FOR EACH ROW EXECUTE FUNCTION phase3_reject_mutation();
CREATE TRIGGER trg_phase3_regions_immutable BEFORE UPDATE OR DELETE ON ocr_regions FOR EACH ROW EXECUTE FUNCTION phase3_reject_mutation();
CREATE TRIGGER trg_phase3_verification_results_immutable BEFORE UPDATE OR DELETE ON verification_results FOR EACH ROW EXECUTE FUNCTION phase3_reject_mutation();
CREATE TRIGGER trg_phase3_items_immutable BEFORE UPDATE OR DELETE ON verification_items FOR EACH ROW EXECUTE FUNCTION phase3_reject_mutation();
CREATE TRIGGER trg_phase3_items_insert BEFORE INSERT ON verification_items FOR EACH ROW EXECUTE FUNCTION phase3_guard_item_insert();

CREATE CONSTRAINT TRIGGER ctr_phase3_runs AFTER INSERT OR UPDATE ON verification_runs DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION phase3_check_lifecycle();
CREATE CONSTRAINT TRIGGER ctr_phase3_expected AFTER INSERT ON verification_expected_items DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION phase3_check_lifecycle();
CREATE CONSTRAINT TRIGGER ctr_phase3_jobs AFTER INSERT OR UPDATE ON verification_jobs DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION phase3_check_lifecycle();
CREATE CONSTRAINT TRIGGER ctr_phase3_attempts AFTER INSERT OR UPDATE ON verification_attempts DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION phase3_check_lifecycle();
CREATE CONSTRAINT TRIGGER ctr_phase3_ocr_results AFTER INSERT ON ocr_results DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION phase3_check_lifecycle();
CREATE CONSTRAINT TRIGGER ctr_phase3_regions AFTER INSERT ON ocr_regions DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION phase3_check_lifecycle();
CREATE CONSTRAINT TRIGGER ctr_phase3_verification_results AFTER INSERT ON verification_results DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION phase3_check_lifecycle();
CREATE CONSTRAINT TRIGGER ctr_phase3_items AFTER INSERT ON verification_items DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION phase3_check_lifecycle();
"""


def upgrade():
    op.execute(DDL)


def downgrade():
    op.execute(
        """
        ALTER TABLE verification_runs DROP CONSTRAINT fk_verification_runs_verification_result;
        ALTER TABLE verification_runs DROP CONSTRAINT fk_verification_runs_ocr_result;
        DROP TABLE verification_items;
        DROP TABLE verification_results;
        DROP TABLE ocr_regions;
        DROP TABLE ocr_results;
        DROP TABLE verification_attempts;
        DROP TABLE verification_jobs;
        DROP TABLE verification_expected_items;
        DROP TABLE verification_runs;
        DROP TABLE ocr_profiles;
        DROP FUNCTION phase3_check_lifecycle();
        DROP FUNCTION phase3_guard_item_insert();
        DROP FUNCTION phase3_round_half_even_6(numeric);
        DROP FUNCTION phase3_guard_attempt();
        DROP FUNCTION phase3_guard_job();
        DROP FUNCTION phase3_guard_run();
        DROP FUNCTION phase3_reject_mutation();
        DROP FUNCTION phase3_valid_polygon(jsonb,integer,integer);
        """
    )
