"""Database-only Phase 3 invariant tests.

These tests are intentionally contract-facing.  They expect the approved
``verification_*`` / ``ocr_*`` names from P3-OCR-v1 rev. 1 and exercise the
additive migration directly, rather than trusting API validation.  The
implementation supplies the small SQL fixture builder by keeping the column
names in the contract; any deliberate naming deviation must update this test
and be reviewed as a contract integration change.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from conftest import created


def _insert_screenshot(database, catalog, *, screenshot_id=None):
    screenshot_id = screenshot_id or uuid4()
    project_id = catalog["project"]["id"]
    with database.begin() as connection:
        connection.execute(text("""
            INSERT INTO screenshots
              (id, project_id, build_id, locale_id, category_id, situation_id, source,
               original_filename, storage_key, file_hash, media_type, size_bytes, width,
               height, metadata_version, metadata, client_upload_id)
            VALUES
              (:id, :project_id, :build_id, :locale_id, :category_id, :situation_id, 'manual',
               'ocr-contract.png', :storage_key, :hash, 'image/png', 10, 1, 1, 1, '{}'::jsonb, NULL)
        """), {
            "id": screenshot_id,
            "project_id": project_id,
            "build_id": catalog["build"]["id"],
            "locale_id": catalog["locale"]["id"],
            "category_id": catalog["category"]["id"],
            "situation_id": catalog["situation"]["id"],
            "storage_key": f"objects/{project_id}/{screenshot_id}.png",
            "hash": "a" * 64,
        })
    return screenshot_id


def _insert_profile(connection, *, profile_id=None):
    profile_id = profile_id or "test-profile-" + uuid4().hex
    profile_digest = hashlib.sha256(profile_id.encode("utf-8")).hexdigest()
    connection.execute(text("""
        INSERT INTO ocr_profiles
          (profile_id, profile_digest, canonical_manifest, engine_name, engine_version,
           model_ids, language_tags, coordinate_space, normalization_version, matching_version)
        VALUES
          (:profile_id, :profile_digest, :manifest, 'test-engine', '1',
           '["test-model"]'::jsonb, '["ko-KR"]'::jsonb, 'original-raster-v1', 'norm-v1',
           'one-to-one-levenshtein-v1')
    """), {
        "profile_id": profile_id,
        "profile_digest": profile_digest,
        "manifest": b"{}",
    })
    return profile_id


def _pending_run_values(catalog, screenshot_id, profile_id, *, project_id=None):
    project_id = project_id or catalog["project"]["id"]
    return {
        "id": uuid4(),
        "project_id": project_id,
        "screenshot_id": screenshot_id,
        "client_run_id": uuid4(),
        "request_fingerprint": "a" * 64,
        "profile_id": profile_id,
        "profile_digest": hashlib.sha256(profile_id.encode("utf-8")).hexdigest(),
        "locale_code": "JA-jp",
        "ocr_language": "ja",
        "storage_key": f"objects/{project_id}/{screenshot_id}.png",
        "source_hash": "b" * 64,
        "build_id": uuid4(),
        "locale_id": uuid4(),
        "category_id": uuid4(),
        "situation_id": uuid4(),
    }


def _insert_pending_run(connection, catalog, screenshot_id, profile_id, *, project_id=None):
    values = _pending_run_values(catalog, screenshot_id, profile_id, project_id=project_id)
    connection.execute(text("""
        INSERT INTO verification_runs
          (id, project_id, screenshot_id, client_run_id, protocol_version, fingerprint_version,
           request_fingerprint, canonical_request, profile_id, profile_digest, profile_canonical,
           snapshot_version, snapshot_canonical, snapshot_sha256, captured_at, source_mode,
           configuration_canonical, configuration_sha256, normalization_version, matching_version,
           pass_threshold, review_threshold, locale_code, ocr_language, screenshot_storage_key,
           screenshot_file_hash, screenshot_size_bytes, screenshot_media_type, screenshot_width,
           screenshot_height, screenshot_build_id, screenshot_locale_id, screenshot_category_id,
           screenshot_situation_id, screenshot_metadata_version, screenshot_metadata, build_label,
           locale_name, category_slug, category_name, situation_slug, situation_name,
           situation_description, snapshot_item_count, snapshot_missing_count, status, stage,
           attempt_count)
        VALUES
          (:id, :project_id, :screenshot_id, :client_run_id, 1, 1, :request_fingerprint, :json,
           :profile_id, :profile_digest, :json, 1, :json, :source_hash, clock_timestamp(),
           'run_creation', :json, :source_hash, 'norm-v1', 'one-to-one-levenshtein-v1', 95, 85,
           :locale_code, :ocr_language, :storage_key, :source_hash, 10, 'image/png', 1, 1,
           :build_id, :locale_id, :category_id, :situation_id, 1, '{}'::jsonb, 'build',
           'locale', 'category', 'Category', 'situation', 'Situation', NULL, 0, 0, 'PENDING',
           'QUEUED', 0)
    """), {**values, "json": b"{}"})
    return values["id"]


def _constraint_definitions(connection, table):
    rows = connection.execute(text(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conrelid = CAST(:table AS regclass) ORDER BY conname",
    ), {"table": table}).scalars()
    return "\n".join(definition for definition in rows if definition)


def _trigger_definitions(connection, table):
    rows = connection.execute(text(
        "SELECT pg_get_triggerdef(t.oid) FROM pg_trigger t "
        "WHERE t.tgrelid = CAST(:table AS regclass) AND NOT t.tgisinternal ORDER BY t.tgname",
    ), {"table": table}).scalars()
    return "\n".join(rows)


def test_contract_tables_declare_composite_project_scope_and_range_checks(database):
    """Scope and finite/range enforcement must reside in PostgreSQL, not routes."""
    expected = {
        "verification_runs": ("project_id", "screenshot_id"),
        "verification_expected_items": ("project_id", "run_id"),
        "verification_jobs": ("project_id", "run_id"),
        "verification_attempts": ("project_id", "run_id"),
        "ocr_results": ("project_id", "run_id"),
        "ocr_regions": ("project_id", "run_id", "result_id"),
        "verification_results": ("project_id", "run_id", "ocr_result_id"),
        "verification_items": ("project_id", "run_id", "result_id"),
    }
    with database.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        assert set(expected) <= tables
        for table, identifiers in expected.items():
            checks = _constraint_definitions(connection, table).lower()
            # The precise constraint names are implementation details.  The
            # columns must nevertheless occur in an FK/check declaration.
            for identifier in identifiers:
                assert identifier in checks, f"{table} lacks database enforcement mentioning {identifier}"

        regions = _constraint_definitions(connection, "ocr_regions").lower()
        items = _constraint_definitions(connection, "verification_items").lower()
        jobs = _constraint_definitions(connection, "verification_jobs").lower()
        runs = _constraint_definitions(connection, "verification_runs").lower()
        for token in ("confidence", "<=", "0", "1"):
            assert token in regions
        for token in ("score", "<=", "100"):
            assert token in items
        for token in ("attempt_count", "3", "generation"):
            assert token in jobs
        for token in ("pending", "running", "retry_wait", "succeeded", "failed", "completed_at"):
            assert token in runs


def test_immutable_tables_have_database_append_only_triggers(database):
    """A trigger is required because API-only immutability is insufficient."""
    immutable = {
        "ocr_profiles",
        "verification_expected_items",
        "verification_attempts",
        "ocr_results",
        "ocr_regions",
        "verification_results",
        "verification_items",
    }
    with database.connect() as connection:
        for table in immutable:
            definition = _trigger_definitions(connection, table).lower()
            assert "before" in definition
            assert "update" in definition or "delete" in definition


def test_append_only_profile_trigger_rejects_direct_sql_update_and_delete(database):
    """Direct SQL must not alter the pinned manifest retained by a run.

    ``ocr_profiles`` is the smallest immutable contract row that can be
    created independently of a worker result.  This verifies the trigger's
    behaviour, instead of merely checking that a trigger was declared.
    """
    with database.begin() as connection:
        profile_id = _insert_profile(connection, profile_id="test-immutable-profile-" + uuid4().hex)

    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            connection.execute(text("""
                UPDATE ocr_profiles
                SET canonical_manifest = :manifest
                WHERE profile_id = :profile_id
            """), {"profile_id": profile_id, "manifest": b'{"profile_id":"rewritten"}'})

    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            connection.execute(text("DELETE FROM ocr_profiles WHERE profile_id = :profile_id"), {"profile_id": profile_id})


def test_run_references_prevent_cross_project_screenshot_links(database, client, catalog):
    """The run FK must reject a screenshot from a different project.

    This intentionally tests DDL shape before the API fixture is available:
    a composite run/screenshot FK is the only acceptable cross-project guard.
    """
    screenshot_id = _insert_screenshot(database, catalog)
    with database.connect() as connection:
        foreign_keys = inspect(connection).get_foreign_keys("verification_runs")
    assert any(
        fk["referred_table"] == "screenshots"
        and {"project_id", "screenshot_id"} <= set(fk["constrained_columns"])
        and {"project_id", "id"} <= set(fk["referred_columns"])
        for fk in foreign_keys
    ), "verification_runs must use the restrictive composite project/screenshot FK"

    with database.begin() as connection:
        profile_id = _insert_profile(connection)
    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            _insert_pending_run(connection, catalog, screenshot_id, profile_id, project_id=uuid4())


def test_phase2_screenshot_and_upload_receipt_constraints_remain_present(database):
    """0004 must not relax Phase 2's original/receipt identity safeguards."""
    with database.connect() as connection:
        screenshot_checks = _constraint_definitions(connection, "screenshots").lower()
        receipt_checks = _constraint_definitions(connection, "upload_receipts").lower()
        receipt_fks = inspect(connection).get_foreign_keys("upload_receipts")
    assert "client_upload_id" in screenshot_checks and "source" in screenshot_checks
    assert "processing" in receipt_checks and "completed" in receipt_checks and "failed" in receipt_checks
    assert any(fk["referred_table"] == "screenshots" for fk in receipt_fks)


def test_match_score_database_rounding_is_half_even_at_six_places(database):
    with database.connect() as connection:
        assert connection.scalar(
            text("SELECT phase3_round_half_even_6(100::numeric / 512::numeric)")
        ) == Decimal("0.195312")
        assert connection.scalar(
            text("SELECT phase3_round_half_even_6(101::numeric / 512::numeric)")
        ) == Decimal("0.197266")
