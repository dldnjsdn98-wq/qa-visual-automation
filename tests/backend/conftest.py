from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from backend.app.config import get_settings
from backend.app.main import app
from backend.app.api.dependencies import get_session, get_storage
from backend.app.storage.local import LocalStorage

ROOT = Path(__file__).resolve().parents[2]


def migrate(engine, revision="head", downgrade=False):
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend/migrations"))
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        (command.downgrade if downgrade else command.upgrade)(config, revision)


@pytest.fixture(scope="session")
def database():
    name = "qa_backend_test_" + uuid4().hex
    url = get_settings().database_url
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    # This database is uniquely allocated by this test run; no user DB is reset.
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    engine = create_engine(url.set(database=name), isolation_level="REPEATABLE READ", connect_args={"client_encoding": "utf8", "connect_timeout": 5})
    try:
        migrate(engine)
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


@pytest.fixture
def client(database, tmp_path):
    factory = sessionmaker(database, expire_on_commit=False)
    def sessions():
        with factory() as session:
            yield session
    storage = LocalStorage(tmp_path / "storage")
    app.dependency_overrides[get_session] = sessions
    app.dependency_overrides[get_storage] = lambda: storage
    with TestClient(app) as result:
        result.storage = storage
        result.factory = factory
        yield result
    app.dependency_overrides.clear()


def created(client, path, body):
    response = client.post(path, json=body)
    assert response.status_code == 201, response.text
    assert response.headers["location"].endswith(response.json()["id"])
    return response.json()


@pytest.fixture
def catalog(client):
    project = created(client, "/api/v1/projects", {"slug": "p-" + uuid4().hex, "name": "QA"})
    p = "/api/v1/projects/" + project["id"]
    build = created(client, p + "/builds", {"label": "1.0"})
    locale = created(client, p + "/locales", {"code": "JA-jp", "name": "日本語"})
    category = created(client, p + "/categories", {"slug": "tutorial", "name": "Tutorial"})
    situation = created(client, p + "/situations", {"category_id": category["id"], "slug": "welcome", "name": "Welcome"})
    return dict(p=p, project=project, build=build, locale=locale, category=category, situation=situation)
