from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass
from importlib.resources import files
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ProfileDocument:
    profile_id: str
    canonical_bytes: bytes
    sha256: str
    manifest: Mapping[str, Any]
    availability: str
    unavailable_code: str | None
    production_eligible: bool


def _load(resource_name: str, *, fixture: bool) -> ProfileDocument:
    base = files(__package__)
    if fixture:
        resource = base.joinpath("fixtures", resource_name)
    else:
        resource = base.joinpath("registered", resource_name)
    raw = resource.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("profile manifest root must be an object")
    try:
        import rfc8785
    except ImportError as error:
        raise RuntimeError("rfc8785 is required to load profile manifests") from error
    canonical = rfc8785.dumps(manifest)
    profile_id = manifest.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id:
        raise ValueError("profile_id is required")
    production_eligible = manifest.get("production_eligible") is True
    qualification = manifest.get("qualification")
    if not isinstance(qualification, dict):
        raise ValueError("qualification is required")
    status = qualification.get("status")
    engine_options = manifest.get("engine_options")
    profile_platform = None
    if isinstance(engine_options, list):
        for option in engine_options:
            if (
                isinstance(option, dict)
                and option.get("name") == "platform_system"
                and isinstance(option.get("value"), str)
            ):
                profile_platform = option["value"]
                break
    platform_matches = fixture or profile_platform == platform.system()
    if status == "QUALIFIED" and (production_eligible or fixture) and platform_matches:
        availability = "AVAILABLE"
        unavailable_code = None
    else:
        availability = "UNAVAILABLE"
        code = qualification.get("unavailable_code")
        if not platform_matches:
            unavailable_code = "UNQUALIFIED_RUNTIME"
        else:
            unavailable_code = code if isinstance(code, str) and code else "UNQUALIFIED_RUNTIME"
    return ProfileDocument(
        profile_id=profile_id,
        canonical_bytes=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
        manifest=MappingProxyType(manifest),
        availability=availability,
        unavailable_code=unavailable_code,
        production_eligible=production_eligible,
    )


def _names(directory: str) -> tuple[str, ...]:
    resource = files(__package__).joinpath(directory)
    return tuple(
        sorted(
            item.name
            for item in resource.iterdir()
            if item.is_file() and item.name.endswith(".profile.json")
        )
    )


def iter_profile_documents() -> tuple[ProfileDocument, ...]:
    return tuple(_load(name, fixture=False) for name in _names("registered"))


def load_profile_document(profile_id: str) -> ProfileDocument:
    for document in iter_profile_documents():
        if document.profile_id == profile_id:
            return document
    raise KeyError(profile_id)


def iter_fixture_profile_documents() -> tuple[ProfileDocument, ...]:
    return tuple(_load(name, fixture=True) for name in _names("fixtures"))


def load_fixture_profile_document(profile_id: str) -> ProfileDocument:
    for document in iter_fixture_profile_documents():
        if document.profile_id == profile_id:
            return document
    raise KeyError(profile_id)
