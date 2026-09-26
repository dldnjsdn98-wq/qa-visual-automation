"""Static checks for the Phase 2 backend packaging contract."""

from pathlib import Path
import json
import platform
import re
import tomllib

from backend.app.main import app
from worker.ocr.profiles import iter_profile_documents
from worker.ocr.schemas import SCHEMA_NAMES, load_schema, schema_sha256, validate_schema_instance


ROOT = Path(__file__).resolve().parents[2]
APPROVED_RFC8785_WHEEL_HASH = (
    "520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48"
)
APPROVED_RAPIDFUZZ_HASHES = {
    "0debb5f43662ea84d2f0228a0c7407ff647f9c3d13f3b692efff0cde46eebce0",  # CPython 3.12 manylinux x86_64
    "cfca36e4612208875e08611a779164b6cb8900ab8bbd3d82d4cfdfae9efbfac9",  # CPython 3.12 Windows x86_64
    "e13a8160d017b499ec7a2fa9d0ce1ae2e7377080815785819f966fb235d4eb60",  # sdist fallback
    "f9b0a501f37fb852c54469375baa25874246b3bbc8b6e21fb4cd186a32335868",  # CPython 3.12 musllinux x86_64
}


def _project_config():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _lock_records(path):
    text = path.read_text(encoding="utf-8")
    logical_lines = re.sub(r"\\\r?\n\s*", " ", text).splitlines()
    records = {}
    for line in logical_lines:
        match = re.match(r"^([A-Za-z0-9_.-]+(?:\[[^]]+\])?)==([^\s;]+)", line)
        if match is None:
            continue
        name = match.group(1).split("[", 1)[0].lower().replace("_", "-")
        records[name] = {
            "version": match.group(2),
            "hashes": set(re.findall(r"sha256:([0-9a-f]{64})", line)),
            "line": line,
        }
    return records


def test_qualified_ocr_runtime_dependencies_are_exact_direct_pins():
    dependencies = _project_config()["project"]["dependencies"]

    assert {
        "paddleocr==3.7.0",
        "paddlepaddle==3.3.1",
        "paddlex[ocr-core]==3.7.2",
        "opencv-contrib-python==4.10.0.84",
        "RapidFuzz==3.14.6",
        "rfc8785==0.1.4",
    } <= set(dependencies)


def test_agent_extra_and_package_discovery_include_runtime_code():
    config = _project_config()

    assert config["project"]["optional-dependencies"]["agent"] == ["httpx>=0.28,<1"]
    assert config["tool"]["setuptools"]["packages"]["find"]["include"] == [
        "backend*",
        "agent*",
        "worker*",
    ]
    assert config["tool"]["setuptools"]["package-data"] == {
        "worker.ocr.schemas": ["v1/*.json"],
        "worker.ocr.profiles": ["registered/*.json", "fixtures/*.json"],
    }


def test_worker_v1_schemas_are_packaged_loadable_closed_resources():
    assert SCHEMA_NAMES == {
        "source-facts",
        "profile-manifest",
        "ocr-adapter-output",
        "expected-snapshot",
        "canonical-regions",
        "verification-config",
        "verification-adapter-output",
    }
    for name in SCHEMA_NAMES:
        schema = load_schema(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"] == f"urn:qa-visual-automation:ocr:{name}:v1"
        assert len(schema_sha256(name)) == 64


def test_existing_base_dev_and_pytest_scopes_are_preserved():
    project = _project_config()["project"]
    dependencies = set(project["dependencies"])
    extras = project["optional-dependencies"]
    pytest_config = _project_config()["tool"]["pytest"]["ini_options"]

    assert {
        "fastapi>=0.115,<1",
        "uvicorn[standard]>=0.34,<1",
        "sqlalchemy>=2.0,<2.1",
        "alembic>=1.14,<2",
        "pydantic-settings>=2.7,<3",
        "psycopg[binary]>=3.2,<4",
        "Pillow>=12.3,<13",
        "python-multipart>=0.0.32,<1",
        "RapidFuzz==3.14.6",
    } <= dependencies
    assert {"pytest>=8,<10", "httpx>=0.28,<1", "pyyaml>=6,<7"} <= set(extras["dev"])
    assert pytest_config["testpaths"] == ["tests/backend", "tests/integration", "tests/ocr"]


def test_backend_lock_pins_rfc8785_to_the_approved_wheel_hash():
    lock_text = (ROOT / "backend" / "requirements.lock").read_text(encoding="utf-8")
    match = re.search(
        r"(?m)^rfc8785==(?P<version>[^\s\\]+)\s+\\\s*\r?\n"
        r"\s+--hash=sha256:(?P<hash>[0-9a-f]{64})\s*$",
        lock_text,
    )

    assert match is not None, "rfc8785 must have one pinned, hashed lock entry"
    assert match.group("version") == "0.1.4"
    assert match.group("hash") == APPROVED_RFC8785_WHEEL_HASH


def test_backend_lock_pins_rapidfuzz_for_windows_and_linux():
    lock_text = (ROOT / "backend" / "requirements.lock").read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^rapidfuzz==(?P<version>[^\s\\]+)\s+\\\s*\r?\n"
        r"(?P<hashes>(?:\s+--hash=sha256:[0-9a-f]{64}(?:\s+\\)?\s*\r?\n)+)",
        lock_text,
    )

    assert match is not None, "rapidfuzz must have a pinned, hashed lock entry"
    assert match.group("version") == "3.14.6"
    assert set(re.findall(r"sha256:([0-9a-f]{64})", match.group("hashes"))) == APPROVED_RAPIDFUZZ_HASHES


def test_backend_lock_contains_the_exact_worker_windows_and_linux_lock_union():
    backend = _lock_records(ROOT / "backend" / "requirements.lock")
    worker_records = [
        _lock_records(ROOT / "worker" / "ocr" / "requirements-windows.lock"),
        _lock_records(ROOT / "worker" / "ocr" / "requirements-linux.lock"),
    ]

    assert len(backend) == 96
    for worker in worker_records:
        for name, record in worker.items():
            assert name in backend
            assert backend[name]["version"] == record["version"]
            assert backend[name]["hashes"] >= record["hashes"]
    assert backend["idna"]["version"] == "3.20"
    assert backend["pyyaml"]["version"] == "6.0.2"
    assert backend["tzdata"]["version"] == "2026.4"
    assert 'sys_platform == "win32"' in backend["tzdata"]["line"]
    assert 'sys_platform == "win32"' in backend["colorama"]["line"]


def test_backend_test_image_installs_the_hash_locked_dependencies():
    dockerfile = (ROOT / "backend" / "Dockerfile.test").read_text(encoding="utf-8")
    normalized = " ".join(dockerfile.split())

    assert "COPY backend/requirements.lock /app/backend/requirements.lock" in normalized
    assert "pip install --no-cache-dir --require-hashes -r backend/requirements.lock" in normalized
    assert "pip install --no-deps --no-build-isolation ." in normalized
    assert "python -m pip check" in normalized


def test_backend_images_match_the_qualified_native_runtime_contract():
    for name in ("Dockerfile", "Dockerfile.test"):
        dockerfile = (ROOT / "backend" / name).read_text(encoding="utf-8")
        normalized = " ".join(dockerfile.split())

        assert normalized.startswith("FROM python:3.12.14-slim-trixie")
        assert "libgl1=1.7.0-1+b2" in normalized
        assert "libglib2.0-0=2.84.4-3~deb13u5" in normalized
        assert "libgomp1=14.2.0-19" in normalized
        assert "rm -rf /var/lib/apt/lists/*" in normalized
        assert "COPY worker ./worker" in normalized
        assert "QA_OCR_MODEL_ROOT=/models/ocr" in normalized
        assert "PADDLE_HOME=/var/cache/paddle" in normalized
        assert "PADDLE_PDX_CACHE_HOME=/var/cache/paddle" in normalized
        assert "python -m pip check" in normalized
    test_image = (ROOT / "backend" / "Dockerfile.test").read_text(encoding="utf-8")
    assert "COPY tests/ocr/fixtures/runtime ./tests/ocr/fixtures/runtime" in test_image


def test_backend_images_copy_only_declared_source_roots_without_model_binaries():
    expected = {
        "Dockerfile": {
            "COPY pyproject.toml ./",
            "COPY backend ./backend",
            "COPY worker ./worker",
            "COPY alembic.ini ./",
        },
        "Dockerfile.test": {
            "COPY backend/requirements.lock /app/backend/requirements.lock",
            "COPY pyproject.toml alembic.ini ./",
            "COPY backend ./backend",
            "COPY worker ./worker",
            "COPY tests/backend ./tests/backend",
            "COPY tests/ocr/fixtures/runtime ./tests/ocr/fixtures/runtime",
        },
    }
    for name, allowed_copies in expected.items():
        instructions = {
            line.strip()
            for line in (ROOT / "backend" / name).read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("COPY ", "ADD "))
        }
        assert instructions == allowed_copies

    model_suffixes = {".onnx", ".pdmodel", ".pdiparams", ".pdparams"}
    assert not [
        path
        for source_root in (ROOT / "backend", ROOT / "worker")
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix.lower() in model_suffixes
    ]


def test_registered_production_profiles_load_with_exact_digests_and_platform_availability():
    expected = {
        "paddleocr-korean-medium-linux-x86_64-debian13-glibc2.41-cpython312-v1":
            "f4daa25d626111e2ca975c50abceaa838e2a3f5d49bcec69fdeab5cea3723c16",
        "paddleocr-korean-medium-windows-amd64-cpython312-v1":
            "00300d2aebd8097cba3879f8f35cae888c3e7a6b0abd3f426b654e5d7201c679",
        "paddleocr-unified-medium-linux-x86_64-debian13-glibc2.41-cpython312-v1":
            "89d587ee744e52a53593eae177366efe9b72079d6c0eacecad91c0ec916221ed",
        "paddleocr-unified-medium-windows-amd64-cpython312-v1":
            "39917d5bf35cd7b538ecd38db6f5c26604cda8370faae0069aa1acc1d2bde916",
    }
    documents = iter_profile_documents()

    assert {document.profile_id: document.sha256 for document in documents} == expected
    assert all(document.production_eligible for document in documents)
    for document in documents:
        validate_schema_instance("profile-manifest", document.manifest, stage="OCR")
        options = {item["name"]: item["value"] for item in document.manifest["engine_options"]}
        expected_availability = "AVAILABLE" if options["platform_system"] == platform.system() else "UNAVAILABLE"
        assert document.availability == expected_availability
        assert (document.unavailable_code is None) == (expected_availability == "AVAILABLE")


def test_generated_openapi_matches_the_current_application():
    generated = json.loads((ROOT / "backend" / "openapi.json").read_text(encoding="utf-8"))
    assert generated == app.openapi()
