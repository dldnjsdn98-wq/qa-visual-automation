"""Verify the hash lock in a newly created local Python 3.12 environment."""
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def main():
    target = ROOT / ".pytest_cache" / ("clean-python-" + uuid4().hex[:12])
    subprocess.run([sys.executable, "-m", "venv", str(target)], check=True)
    python = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    required_paths = {
        "/health",
        "/ready",
        "/api/v1/projects",
        "/api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs",
        "/api/v1/projects/{project_id}/ocr-profiles",
    }
    import_check = (
        "assert sys.version_info[:2] == (3, 12); "
        "from backend.app.main import app; "
        f"assert {required_paths!r} <= set(app.openapi()['paths']); "
        "import backend.app.workers.ocr, worker.verification; "
        "from pathlib import Path; import backend, worker; "
        "assert Path(backend.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()); "
        "assert all(Path(path).resolve().is_relative_to(Path(sys.prefix).resolve()) "
        "for path in worker.__path__); "
        "from worker.ocr import AdapterError, load_fixture_profile_document, ocr_execute; "
        "from worker.ocr.profiles import iter_profile_documents; "
        "profiles = iter_profile_documents(); "
        "assert len(profiles) == 4; "
        "assert {p.sha256 for p in profiles} == {"
        "'f4daa25d626111e2ca975c50abceaa838e2a3f5d49bcec69fdeab5cea3723c16',"
        "'00300d2aebd8097cba3879f8f35cae888c3e7a6b0abd3f426b654e5d7201c679',"
        "'89d587ee744e52a53593eae177366efe9b72079d6c0eacecad91c0ec916221ed',"
        "'39917d5bf35cd7b538ecd38db6f5c26604cda8370faae0069aa1acc1d2bde916'}; "
        "assert sum(p.availability == 'AVAILABLE' for p in profiles) == 2; "
        "assert all(p.production_eligible for p in profiles); "
        "fixture = load_fixture_profile_document('fixture-contract-v1'); "
        "assert fixture.sha256 == '2736423a78ae37e992a0a6011c2dd9ac793f3b7b516f2c504b0d19a7df275d27'; "
        "assert fixture.production_eligible is False; "
        "assert fixture.manifest['profile_id'] == 'fixture-contract-v1'; "
        "print('Clean installation and application import PASS')"
    )
    with TemporaryDirectory(prefix="qa-ocr-clean-import-") as import_cwd:
        import_path = Path(import_cwd).resolve()
        assert not import_path.is_relative_to(ROOT)
        commands = (
            (["-m", "pip", "install", "--require-hashes", "-r", "backend/requirements.lock"], ROOT),
            (["-m", "pip", "install", "--no-deps", "--no-build-isolation", "."], ROOT),
            (["-m", "pip", "check"], import_path),
            (["-I", "-c", "import sys; " + import_check], import_path),
        )
        for args, cwd in commands:
            subprocess.run([str(python), *args], cwd=cwd, check=True)


if __name__ == "__main__":
    main()
