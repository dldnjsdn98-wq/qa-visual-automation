"""Verify the hash lock in a newly created local Python 3.12 environment."""
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def main():
    target = ROOT / ".pytest_cache" / ("clean-python-" + uuid4().hex[:12])
    subprocess.run([sys.executable, "-m", "venv", str(target)], check=True)
    python = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    for args in (["-m", "pip", "install", "--require-hashes", "-r", "backend/requirements.lock"], ["-m", "pip", "install", "--no-deps", "--no-build-isolation", "."], ["-m", "pip", "check"], ["-c", "from backend.app.main import app; assert len(app.openapi()['paths']) == 22; print('Clean installation and application import PASS')"]):
        subprocess.run([str(python), *args], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
