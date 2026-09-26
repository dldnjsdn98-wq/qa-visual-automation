"""Synthetic authority checks; run with --noconftest and plugin autoload disabled.

Run runner_reexport separately: it intentionally loads application dependencies.
No test in this module launches an OCR child or requests native containment.
"""
import os
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def synthetic_environment(monkeypatch):
    # Replace the mapping, never copy/read/retain the operator's ambient values.
    values = {
        "PGPASSWORD": "synthetic-secret",
        "DATABASE_URL": "synthetic-db-url",
        "POSTGRES_PASSWORD": "synthetic-secret",
        "AWS_SECRET_ACCESS_KEY": "synthetic-secret",
        "PYTHONPATH": "synthetic-pythonpath",
        "PATH": "synthetic-path",
        "HOME": "synthetic-home",
        "USERPROFILE": "synthetic-userprofile",
        "UNLISTED_SENTINEL": "synthetic-unlisted",
        "SystemRoot": "synthetic-system-root",
        "WINDIR": "synthetic-windows-directory",
    }
    monkeypatch.setattr(os, "environ", values)
    return values


def test_child_environment_authority_and_fixed_values(synthetic_environment):
    from backend.app.workers.ocr_child_environment import child_environment

    result = child_environment("synthetic-scratch")
    assert result == {
        "SystemRoot": "synthetic-system-root",
        "WINDIR": "synthetic-windows-directory",
        "TEMP": "synthetic-scratch", "TMP": "synthetic-scratch",
        "HOME": "synthetic-scratch", "USERPROFILE": "synthetic-scratch",
        "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "True",
    }
    assert synthetic_environment["HOME"] == "synthetic-home"
    assert result is not synthetic_environment


def test_child_environment_absent_optional_keys(synthetic_environment):
    from backend.app.workers.ocr_child_environment import child_environment

    synthetic_environment.clear()
    result = child_environment("synthetic-scratch")
    assert not {"SystemRoot", "WINDIR", "QA_OCR_MODEL_ROOT", "PADDLE_HOME",
                "PADDLE_PDX_CACHE_HOME"} & result.keys()


@pytest.mark.parametrize("key", ["QA_OCR_MODEL_ROOT", "PADDLE_HOME", "PADDLE_PDX_CACHE_HOME"])
@pytest.mark.parametrize("absolute", [False, True])
def test_child_environment_optional_normalized_paths(
    synthetic_environment, monkeypatch, tmp_path, key, absolute,
):
    from backend.app.workers.ocr_child_environment import child_environment

    monkeypatch.chdir(tmp_path)
    relative = os.path.join("synthetic-models", "..", "synthetic-cache")
    synthetic_environment[key] = os.path.join(str(tmp_path), relative) if absolute else relative
    result = child_environment("synthetic-scratch")
    assert result[key] == os.path.join(str(tmp_path), "synthetic-cache")
    assert os.path.isabs(result[key])


def test_runner_reexport_separate_process(monkeypatch, record_property):
    """Parent selects ONLY this node in a separate inspected non-native process."""
    assert "backend.app.workers.ocr" not in sys.modules, "requires fresh interpreter"
    import psycopg
    from backend.app import config

    calls = []

    def deny_connect(*args, **kwargs):
        calls.append("connect")  # Never retain arguments, URLs or credentials.
        raise AssertionError("DB connection forbidden in re-export check")

    monkeypatch.setattr(psycopg, "connect", deny_connect)
    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace(
        database_url="postgresql+psycopg://synthetic:synthetic@127.0.0.1:1/synthetic",
        storage_root="synthetic-storage",
    ))
    from backend.app.workers.ocr_child_environment import child_environment
    from backend.app.workers import ocr

    assert ocr.child_environment is child_environment
    assert calls == []
    record_property("db_connect_calls", len(calls))
