"""PostgreSQL migration checks for the Phase 3 verification schema.

Integration assumptions (P3-OCR-v1 rev. 1, sections 3 and 10.1): migration
``0004`` is additive to ``0003_phase2_upload_receipts`` and registers the
contract tables below in ``Base.metadata``.  The test deliberately uses a
populated 0003 database, rather than model inserts, so it catches accidental
rewrites of Phase 1/2 rows during the upgrade.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from backend.app.config import get_settings
from backend.app.db import Base
import backend.app.models  # noqa: F401 - registers every current ORM table.
from conftest import migrate


OCR_TABLES = {
    "ocr_profiles",
    "verification_runs",
    "verification_expected_items",
    "verification_jobs",
    "verification_attempts",
    "ocr_results",
    "ocr_regions",
    "verification_results",
    "verification_items",
}


def _temporary_database(prefix: str):
    name = prefix + uuid4().hex
    url = get_settings().database_url
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    return name, admin, create_engine(url.set(database=name), isolation_level="REPEATABLE READ")


def _insert_populated_0003_fixture(connection):
    """Insert enough Phase 1/2 data to detect an accidental table rewrite."""
    project_id, build_id, locale_id, category_id, situation_id, key_id = (uuid4() for _ in range(6))
    screenshot_id, client_upload_id, token = uuid4(), uuid4(), uuid4()
    uploaded_at = datetime(2025, 9, 25, 1, 2, 3, 456789, tzinfo=timezone.utc)
    metadata = '{"unicode":"e\\u0301 😀","empty":"","nested":{"null":null}}'
    values = {
        "project_id": project_id,
        "build_id": build_id,
        "locale_id": locale_id,
        "category_id": category_id,
        "situation_id": situation_id,
        "key_id": key_id,
        "entry_id": uuid4(),
        "screenshot_id": screenshot_id,
        "client_upload_id": client_upload_id,
        "token": token,
        "uploaded_at": uploaded_at,
        "metadata": metadata,
        "storage_key": f"objects/{project_id}/{screenshot_id}.png",
        "file_hash": hashlib.sha256(b"legacy-bytes").hexdigest(),
        "receipt_hash": "b" * 64,
    }
    statements = (
        ("INSERT INTO projects (id, slug, name) VALUES (:project_id, :slug, 'Legacy')", {**values, "slug": "legacy-" + uuid4().hex}),
        ("INSERT INTO builds (id, project_id, label) VALUES (:build_id, :project_id, 'legacy-build')", values),
        ("INSERT INTO locales (id, project_id, code, name) VALUES (:locale_id, :project_id, 'ko-KR', '한국어')", values),
        ("INSERT INTO categories (id, project_id, slug, name) VALUES (:category_id, :project_id, 'legacy', 'Legacy')", values),
        ("INSERT INTO situations (id, project_id, category_id, slug, name) VALUES (:situation_id, :project_id, :category_id, 'legacy', 'Legacy')", values),
        ("INSERT INTO string_keys (id, project_id, string_id) VALUES (:key_id, :project_id, 'legacy.key')", values),
        ("INSERT INTO string_entries (id, project_id, build_id, locale_id, string_key_id, text) VALUES (:entry_id, :project_id, :build_id, :locale_id, :key_id, '')", values),
        ("INSERT INTO situation_expected_strings (project_id, build_id, situation_id, string_key_id, position) VALUES (:project_id, :build_id, :situation_id, :key_id, 7)", values),
        ("""INSERT INTO screenshots (id, project_id, build_id, locale_id, category_id, situation_id, source, original_filename, uploaded_at, storage_key, file_hash, media_type, size_bytes, width, height, metadata_version, metadata, client_upload_id) VALUES (:screenshot_id, :project_id, :build_id, :locale_id, :category_id, :situation_id, 'agent', 'legacy-é-😀.png', :uploaded_at, :storage_key, :file_hash, 'image/png', 123, 12, 8, 1, CAST(:metadata AS jsonb), :client_upload_id)""", values),
        ("""INSERT INTO upload_receipts (project_id, client_upload_id, fingerprint_version, upload_protocol_version, request_fingerprint, canonical_request, state, attempt_generation, attempt_token, candidate_screenshot_id, candidate_storage_key, screenshot_id, lease_expires_at, last_error_code) VALUES (:project_id, :client_upload_id, 1, 1, :receipt_hash, CAST('{}' AS bytea), 'COMPLETED', 1, :token, :screenshot_id, :storage_key, :screenshot_id, NULL, NULL)""", values),
    )
    for statement, parameters in statements:
        connection.execute(text(statement), parameters)
    return project_id, screenshot_id, client_upload_id


def _json_row(connection, table: str, where: str, **params):
    return connection.execute(text(f"SELECT to_jsonb(row_value) FROM {table} AS row_value WHERE {where}"), params).scalar_one()


def test_0003_to_0004_preserves_populated_phase1_phase2_rows():
    name, admin, engine = _temporary_database("qa_ocr_0003_preservation_")
    try:
        migrate(engine, "0003_phase2_upload_receipts")
        with engine.begin() as connection:
            project_id, screenshot_id, client_upload_id = _insert_populated_0003_fixture(connection)
        with engine.connect() as connection:
            screenshot_before = _json_row(connection, "screenshots", "id = :id", id=screenshot_id)
            receipt_before = _json_row(
                connection,
                "upload_receipts",
                "project_id = :project_id AND client_upload_id = :client_upload_id",
                project_id=project_id,
                client_upload_id=client_upload_id,
            )

        migrate(engine, "head")

        with engine.connect() as connection:
            assert _json_row(connection, "screenshots", "id = :id", id=screenshot_id) == screenshot_before
            assert _json_row(
                connection,
                "upload_receipts",
                "project_id = :project_id AND client_upload_id = :client_upload_id",
                project_id=project_id,
                client_upload_id=client_upload_id,
            ) == receipt_before
            table_names = set(inspect(connection).get_table_names())
            assert OCR_TABLES <= table_names
            assert all(connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0 for table in OCR_TABLES)
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


def test_fresh_0004_head_has_contract_tables_and_orm_metadata_parity():
    name, admin, engine = _temporary_database("qa_ocr_head_")
    try:
        migrate(engine)
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            assert OCR_TABLES <= tables
            assert tables == set(Base.metadata.tables) | {"alembic_version"}
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


def test_0004_downgrades_to_0003_and_reapplies_cleanly():
    name, admin, engine = _temporary_database("qa_ocr_roundtrip_")
    try:
        migrate(engine)
        migrate(engine, "0003_phase2_upload_receipts", downgrade=True)
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            assert not (OCR_TABLES & tables)
            assert {"projects", "screenshots", "upload_receipts"} <= tables
        migrate(engine)
        with engine.connect() as connection:
            assert OCR_TABLES <= set(inspect(connection).get_table_names())
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()
