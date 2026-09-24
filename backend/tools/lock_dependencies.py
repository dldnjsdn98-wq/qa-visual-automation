"""Capture installed Python 3.12 versions and PyPI distribution hashes."""
import importlib.metadata
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def package(name, version=None):
    suffix = f"/{version}" if version else ""
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}{suffix}/json", timeout=30) as response:
        return json.load(response)


def main():
    versions = {dist.metadata["Name"].lower().replace("_", "-"): dist.version for dist in importlib.metadata.distributions()}
    for ignored in ("pip", "qa-visual-automation"):
        versions.pop(ignored, None)
    if "setuptools" not in versions:
        versions["setuptools"] = package("setuptools")["info"]["version"]
    versions["uvloop"] = package("uvloop")["info"]["version"]
    lines = ["# Python 3.12 Windows/Linux runtime + test dependencies.", "# Install with --require-hashes; regenerate only after dependency review.", ""]
    for name, version in sorted(versions.items()):
        data = package(name, version)
        hashes = sorted({entry["digests"]["sha256"] for entry in data["urls"]})
        if not hashes:
            raise RuntimeError(f"No distribution hashes for {name}")
        marker = ' ; sys_platform != "win32" and sys_platform != "cygwin" and platform_python_implementation == "CPython"' if name == "uvloop" else ""
        lines.append(f"{name}=={version}{marker} \\")
        lines.extend("    --hash=sha256:" + digest + (" \\" if i < len(hashes) - 1 else "") for i, digest in enumerate(hashes))
    (ROOT / "backend/requirements.lock").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Locked {len(versions)} exact versions with distribution SHA-256 hashes")


if __name__ == "__main__":
    main()
