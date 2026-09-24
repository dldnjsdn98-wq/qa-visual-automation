from pathlib import Path
import pytest

from backend.app.storage import local as local_module
from backend.app.storage.local import LocalStorage


@pytest.mark.parametrize("working_directory", ["repository", "outside"])
def test_storage_root_is_repository_relative_and_preserves_absolute_paths(monkeypatch, tmp_path, working_directory):
    repository_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repository_root if working_directory == "repository" else tmp_path)
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)

    default_storage = LocalStorage("storage/local")
    absolute_root = tmp_path / "explicit-storage"
    absolute_storage = LocalStorage(absolute_root)

    assert local_module.ROOT == repository_root
    assert default_storage.root == repository_root / "storage/local"
    assert absolute_storage.root == absolute_root
