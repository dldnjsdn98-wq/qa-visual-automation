import hashlib
import io
import os
from uuid import uuid4, UUID
import pytest
from sqlalchemy import create_engine, inspect, insert
from sqlalchemy.exc import IntegrityError
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from backend.app.config import get_settings
from backend.app.db import Base
from backend.app.models import Project, Build, Locale, Category, Situation, StringKey, StringEntry
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
        assert len(inspect(engine).get_table_names()) == 10
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
