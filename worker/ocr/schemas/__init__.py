from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from importlib.resources import files
from typing import Any, Mapping

from worker.ocr.errors import AdapterError


SCHEMA_VERSION = 1
SCHEMA_NAMES = frozenset(
    {
        "source-facts",
        "profile-manifest",
        "ocr-adapter-output",
        "expected-snapshot",
        "canonical-regions",
        "verification-config",
        "verification-adapter-output",
    }
)


def load_schema(name: str, version: int = SCHEMA_VERSION) -> dict[str, Any]:
    if version != SCHEMA_VERSION or name not in SCHEMA_NAMES:
        raise KeyError((name, version))
    resource = files(__package__).joinpath(
        f"v{version}",
        f"{name}.schema.json",
    )
    value = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("schema root must be an object")
    return value


def schema_sha256(name: str, version: int = SCHEMA_VERSION) -> str:
    resource = files(__package__).joinpath(
        f"v{version}",
        f"{name}.schema.json",
    )
    return hashlib.sha256(resource.read_bytes()).hexdigest()


def _closed_root(
    value: object,
    *,
    required: frozenset[str],
    stage: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdapterError("ENGINE_OUTPUT_INVALID", stage)  # type: ignore[arg-type]
    if set(value) != set(required):
        raise AdapterError("ENGINE_OUTPUT_INVALID", stage)  # type: ignore[arg-type]
    return value


def _resolve_ref(root: Mapping[str, Any], reference: str) -> Mapping[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported schema reference: {reference}")
    current: Any = root
    for part in reference[2:].split("/"):
        current = current[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(current, Mapping):
        raise ValueError(f"schema reference is not an object: {reference}")
    return current


def _matches_type(value: object, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return type(value) is bool
    if expected == "integer":
        return type(value) is int
    if expected == "number":
        return type(value) in (int, float) and math.isfinite(float(value))
    if expected == "string":
        return isinstance(value, str)
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        )
    return False


def _validate_instance(
    value: object,
    schema: Mapping[str, Any],
    *,
    root: Mapping[str, Any],
    path: str,
) -> None:
    if "$ref" in schema:
        _validate_instance(
            value,
            _resolve_ref(root, schema["$ref"]),
            root=root,
            path=path,
        )
        return
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path}: const mismatch")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: value is not in enum")
    expected_type = schema.get("type")
    if expected_type is not None:
        choices = [expected_type] if isinstance(expected_type, str) else expected_type
        if not isinstance(choices, list) or not any(
            _matches_type(value, choice) for choice in choices
        ):
            raise ValueError(f"{path}: invalid type")
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ValueError(f"{path}: object key is not a string")
        required = schema.get("required", [])
        if any(key not in value for key in required):
            raise ValueError(f"{path}: missing required property")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise ValueError(f"{path}: unexpected properties")
        for key, child in properties.items():
            if key in value:
                _validate_instance(
                    value[key],
                    child,
                    root=root,
                    path=f"{path}.{key}",
                )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValueError(f"{path}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValueError(f"{path}: too many items")
        if schema.get("uniqueItems"):
            serialized = [
                json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                for item in value
            ]
            if len(serialized) != len(set(serialized)):
                raise ValueError(f"{path}: duplicate items")
        prefix = schema.get("prefixItems", [])
        for index, child in enumerate(prefix):
            if index < len(value):
                _validate_instance(
                    value[index], child, root=root, path=f"{path}[{index}]"
                )
        items = schema.get("items")
        if items is False and len(value) > len(prefix):
            raise ValueError(f"{path}: unexpected trailing items")
        if isinstance(items, Mapping):
            start = len(prefix) if prefix else 0
            for index in range(start, len(value)):
                _validate_instance(
                    value[index], items, root=root, path=f"{path}[{index}]"
                )
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValueError(f"{path}: string is too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValueError(f"{path}: string is too long")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ValueError(f"{path}: pattern mismatch")
    if type(value) in (int, float):
        numeric = Decimal(str(value))
        if not numeric.is_finite():
            raise ValueError(f"{path}: nonfinite number")
        if "minimum" in schema and numeric < Decimal(str(schema["minimum"])):
            raise ValueError(f"{path}: below minimum")
        if "maximum" in schema and numeric > Decimal(str(schema["maximum"])):
            raise ValueError(f"{path}: above maximum")
        if "exclusiveMinimum" in schema and numeric <= Decimal(
            str(schema["exclusiveMinimum"])
        ):
            raise ValueError(f"{path}: below exclusive minimum")
        if "multipleOf" in schema:
            try:
                if numeric % Decimal(str(schema["multipleOf"])) != 0:
                    raise ValueError(f"{path}: not a multiple")
            except InvalidOperation as error:
                raise ValueError(f"{path}: invalid numeric value") from error


def validate_schema_instance(
    name: str,
    value: object,
    *,
    version: int = SCHEMA_VERSION,
    stage: str,
) -> Mapping[str, Any] | Sequence[Any]:
    schema = load_schema(name, version)
    try:
        _validate_instance(value, schema, root=schema, path="$")
    except (KeyError, TypeError, ValueError) as error:
        raise AdapterError("ENGINE_OUTPUT_INVALID", stage) from error  # type: ignore[arg-type]
    if not isinstance(value, (Mapping, Sequence)) or isinstance(
        value, (str, bytes, bytearray)
    ):
        raise AdapterError("ENGINE_OUTPUT_INVALID", stage)  # type: ignore[arg-type]
    return value


def validate_ocr_adapter_output(value: object) -> Mapping[str, Any]:
    output = _closed_root(
        value,
        required=frozenset(
            {
                "adapter_version",
                "source_sha256",
                "profile_sha256",
                "pixel_sha256",
                "runtime_manifest",
                "preprocessing",
                "regions",
                "raw_audit",
                "timings_ms",
            }
        ),
        stage="OCR",
    )
    if output["adapter_version"] != 1:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    return output


def validate_verification_adapter_output(value: object) -> Mapping[str, Any]:
    output = _closed_root(
        value,
        required=frozenset(
            {
                "adapter_version",
                "snapshot_sha256",
                "configuration_sha256",
                "matching_version",
                "normalization_version",
                "items",
                "summary",
            }
        ),
        stage="VERIFY",
    )
    if output["adapter_version"] != 1:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    return output


__all__ = [
    "SCHEMA_NAMES",
    "SCHEMA_VERSION",
    "load_schema",
    "schema_sha256",
    "validate_schema_instance",
    "validate_ocr_adapter_output",
    "validate_verification_adapter_output",
]
