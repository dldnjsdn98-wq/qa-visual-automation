import hashlib
import io
import os
from datetime import datetime, timezone
from uuid import uuid4, UUID
import pytest
from sqlalchemy import create_engine, inspect, insert, select
from sqlalchemy.exc import IntegrityError
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from backend.app.config import get_settings
from backend.app.db import Base
from backend.app.models import Project, Build, Locale, Category, Situation, Screenshot, StringKey, StringEntry
from backend.app.storage.local import LocalStorage
from backend.app.storage.base import ObjectExists, StorageError
from backend.app.maintenance.reconcile_storage import reconcile
from conftest import migrate
from test_screenshots import upload, image_bytes


def test_fresh_migration_roundtrip_and_metadata():
    name = "qa_migration_test_" + uuid4().hex
    url = get_settings().database_url
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    engine = create_engine(url.set(database=name))
    try:
        migrate(engine)
        assert set(inspect(engine).get_table_names()) == set(Base.metadata.tables) | {"alembic_version"}
        with engine.connect() as connection:
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        migrate(engine, "0001_bootstrap", downgrade=True)
        assert inspect(engine).get_table_names() == ["alembic_version"]
        migrate(engine)
        assert set(inspect(engine).get_table_names()) == set(Base.metadata.tables) | {"alembic_version"}
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


def test_0002_data_is_preserved_by_additive_0003_migration(tmp_path):
    name = "qa_migration_preservation_" + uuid4().hex
    url = get_settings().database_url
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    engine = create_engine(url.set(database=name))
    project_id, build_id, locale_id, category_id, situation_id, screenshot_id = (uuid4() for _ in range(6))
    original = image_bytes()
    storage = LocalStorage(tmp_path / "migration-originals")
    storage_key = f"objects/{project_id}/{screenshot_id}.png"
    storage.publish(storage.stage(io.BytesIO(original), len(original)), storage_key)
    uploaded_at = datetime(2025, 7, 8, 9, 10, 11, 123456, tzinfo=timezone.utc)
    capture_metadata = {
        "device": "기기 😀",
        "nested": {
            "日本語": ["한글", {"combining": "e\u0301", "empty": "", "null": None}],
        },
    }

    def screenshot_snapshot(connection):
        return dict(connection.execute(
            select(
                Screenshot.id,
                Screenshot.project_id,
                Screenshot.build_id,
                Screenshot.locale_id,
                Screenshot.category_id,
                Screenshot.situation_id,
                Screenshot.source,
                Screenshot.original_filename,
                Screenshot.uploaded_at,
                Screenshot.storage_key,
                Screenshot.file_hash,
                Screenshot.media_type,
                Screenshot.size_bytes,
                Screenshot.width,
                Screenshot.height,
                Screenshot.metadata_version,
                Screenshot.capture_metadata.label("capture_metadata"),
                Screenshot.client_upload_id,
            ).where(Screenshot.id == screenshot_id)
        ).mappings().one())

    def stored_bytes():
        stream, size = storage.open_read(storage_key)
        with stream:
            data = stream.read()
        assert size == len(data)
        return data

    try:
        migrate(engine, "0002_phase1_domain")
        with engine.begin() as connection:
            connection.execute(insert(Project).values(id=project_id, slug="legacy", name="Legacy"))
            connection.execute(insert(Build).values(id=build_id, project_id=project_id, label="1.0"))
            connection.execute(insert(Locale).values(id=locale_id, project_id=project_id, code="ko-KR", name="Korean"))
            connection.execute(insert(Category).values(id=category_id, project_id=project_id, slug="legacy", name="Legacy"))
            connection.execute(insert(Situation).values(id=situation_id, project_id=project_id, category_id=category_id, slug="legacy", name="Legacy"))
            connection.execute(insert(Screenshot).values(
                id=screenshot_id,
                project_id=project_id,
                build_id=build_id,
                locale_id=locale_id,
                category_id=category_id,
                situation_id=situation_id,
                source="manual",
                original_filename="기존-e\u0301-😀.png",
                uploaded_at=uploaded_at,
                storage_key=storage_key,
                file_hash=hashlib.sha256(original).hexdigest(),
                media_type="image/png",
                size_bytes=len(original),
                width=12,
                height=8,
                metadata_version=1,
                capture_metadata=capture_metadata,
                client_upload_id=None,
            ))
        with engine.connect() as connection:
            before = screenshot_snapshot(connection)
        original_before = stored_bytes()
        migrate(engine)
        with engine.connect() as connection:
            after = screenshot_snapshot(connection)
            assert after == before
            assert after["capture_metadata"] == capture_metadata
            assert after["uploaded_at"] == uploaded_at
            assert "upload_receipts" in inspect(connection).get_table_names()
            assert connection.exec_driver_sql("SELECT count(*) FROM upload_receipts").scalar_one() == 0
        assert stored_bytes() == original_before == original
        with engine.connect() as connection:
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


def test_database_rejects_cross_project_fk(database, client, catalog):
    with database.begin() as connection:
        other = connection.execute(insert(Project).values(slug="other-" + uuid4().hex, name="Other").returning(Project.id)).scalar_one()
    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(insert(Situation).values(project_id=other, category_id=UUID(catalog["category"]["id"]), slug="invalid", name="Invalid"))
    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(insert(StringEntry).values(project_id=other, build_id=UUID(catalog["build"]["id"]), locale_id=UUID(catalog["locale"]["id"]), string_key_id=uuid4(), text="invalid"))


def test_storage_atomic_no_overwrite_and_traversal(tmp_path):
    storage = LocalStorage(tmp_path / "objects-root")
    data = image_bytes()
    staged = storage.stage(io.BytesIO(data), len(data))
    assert staged.sha256 == hashlib.sha256(data).hexdigest()
    facts = storage.inspect(staged, "image/png")
    assert (facts.width, facts.height) == (12, 8)
    key = f"objects/{uuid4()}/{uuid4()}.png"
    storage.publish(staged, key)
    second = storage.stage(io.BytesIO(b"different"), 100)
    with pytest.raises(ObjectExists):
        storage.publish(second, key)
    stream, size = storage.open_read(key)
    with stream:
        assert stream.read() == data
    for invalid in ("../outside", "/absolute", key + "/../other", "objects/not-a-uuid/file.png"):
        with pytest.raises(StorageError):
            storage.delete(invalid)
    storage.discard_stage(second.token)
    storage.delete(key)
    storage.delete(key)
    assert storage.list_objects() == []


def test_reconcile_dry_run_apply_and_missing(client, catalog):
    response = upload(client, catalog)
    assert response.status_code == 201
    storage = client.storage
    reference = storage.list_objects()[0]
    orphan = storage.stage(io.BytesIO(image_bytes()), 10000)
    key = f"objects/{uuid4()}/{uuid4()}.png"
    storage.publish(orphan, key)
    stage = storage.stage(io.BytesIO(b"staged"), 100)
    fresh = storage.stage(io.BytesIO(b"fresh"), 100)
    now = 2_000_000_000
    os.utime(storage.root / key, (now - 90000, now - 90000))
    os.utime(storage.root / "staging" / stage.token, (now - 90000, now - 90000))
    os.utime(storage.root / "staging" / fresh.token, (now, now))
    with pytest.raises(ValueError):
        reconcile(client.factory, storage, writers_stopped=False)
    report = reconcile(client.factory, storage, writers_stopped=True, now=now)
    assert report["orphans"] == [key] and report["deleted"] == []
    assert report["staging"] == [f"staging/{stage.token}"]
    report = reconcile(client.factory, storage, writers_stopped=True, apply=True, now=now)
    assert set(report["deleted"]) == {key, f"staging/{stage.token}"}
    assert storage.stat(reference.key)
    storage.delete(reference.key)
    report = reconcile(client.factory, storage, writers_stopped=True, now=now)
    assert reference.key in report["missing"]


def test_reconcile_database_failure_never_deletes(client, monkeypatch):
    def fail():
        raise RuntimeError("database unavailable")
    monkeypatch.setattr(client.storage, "delete", lambda *args: pytest.fail("deleted without primary"))
    with pytest.raises(RuntimeError):
        reconcile(fail, client.storage, writers_stopped=True, apply=True)
